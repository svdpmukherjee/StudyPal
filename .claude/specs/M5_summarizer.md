# Spec M5: Summarizer agent

## User story
As a learner, I want StudyPal to look back over our recent chat and quietly
distill what it learned about me into durable memory, so that after a session I
don't have to hand-type facts — the next session already knows my topic and weak
spots because a focused summarizer subagent extracted them for me.

## Acceptance criteria
- [ ] A focused **summarizer subagent** lives in `backend/summarizer.py`: its only
      job is one LLM call whose prompt asks the model to read recent chat turns and
      return **candidate durable facts** about the learner (topic, weak spots,
      preferences). It requests a **machine-parseable** shape (e.g. a JSON array of
      short strings) and `summarize_messages(messages) -> list[str]` parses that
      into a clean list, tolerating a model that wraps JSON in prose or code fences
      (parse failure yields `[]`, never a crash). It uses a **non-cheap tier**
      (strong via `router.model_for("strong")`) — confirm the slug is live before
      wiring — and raises the existing `OpenRouterError` on upstream failure.
- [ ] `db.py` exposes `get_recent_messages(limit)` returning the last `limit`
      `messages` docs in chronological order (oldest→newest, `[]` when empty),
      reusing the single `certifi.where()` client — no second client.
- [ ] `POST /summarize` pulls the last N messages (default ~20), calls the
      summarizer, then stores each candidate via M3's `add_profile_fact` (reusing
      its trim + case-insensitive dedup), and returns `{ added: [...], facts: [...] }`
      — `added` = only the newly-stored facts (candidates that were duplicates or
      blank are **not** in `added`), `facts` = the full updated profile list. With
      no chat history it returns `{ added: [], facts: [...] }` and makes no model
      call.
- [ ] Backend fails loud-but-clean: an OpenRouter/model failure (bad slug, timeout,
      4xx/5xx) returns `HTTPException(502)` with a JSON `detail`, and a Mongo read
      failure returns a clean error — never an unhandled `500`. `/chat` and the
      `{ reply, tier, model, skill }` shape are **unchanged**.
- [ ] The frontend adds a clearly-labelled **"Summarize session"** control; tapping
      it `POST`s `/summarize`, then refreshes the M3 "StudyPal remembers" chip panel
      from the returned `facts` and shows which facts were just added (e.g. a short
      "Added N: …" line). It disables while the request is in flight and surfaces
      any failure via a visible inline error (never a silent blank) using the
      existing `try/catch` pattern.
- [ ] Visual + Markdown baseline holds: the summarize control and "added" feedback
      use existing design tokens (system font, `--accent`, spacing/radius), read
      correctly in light AND dark via `prefers-color-scheme`, cause no horizontal
      scroll at 360px, and have clear `:hover`/`:focus-visible`/`:disabled` states.
      Assistant chat replies still render as Markdown (heading/list/inline `code`/
      fenced block, no literal `**`/`#`/`---`); user turns stay plain text;
      `rehype-raw` stays OFF.

## Build plan (numbered, small steps)
1. **backend/db.py — read recent messages.** Add
   `get_recent_messages(limit: int = 20) -> list[dict]`: query `messages` sorted by
   `ts` descending, take `limit`, and return them **oldest→newest** (reverse) as
   `{role, text}` dicts. Return `[]` when empty. Reuse the existing client.
2. **backend/summarizer.py (new — the subagent).** Define a tight extractor prompt:
   "You are a summarizer. Read the conversation and extract at most ~5 short,
   durable facts about the *learner* (what they're studying, weak spots, stated
   preferences) — not facts about the world. Return ONLY a JSON array of short
   strings; return `[]` if nothing durable." Implement
   `summarize_messages(messages: list[dict]) -> list[str]`: build a compact context
   (system extractor prompt + a rendered transcript of the turns), call
   `chat_completion(context, router.model_for("strong"))`, then robustly parse the
   reply into a list — strip code fences, find the first `[...]`, `json.loads`, keep
   only non-empty trimmed strings; on any parse error return `[]`. Let
   `OpenRouterError` propagate to the caller. Keep it small and dependency-free
   (stdlib `json`, `re`).
3. **backend/main.py — `/summarize` route.** Add a `SummarizeResponse`
   (`added: list[str]`, `facts: list[str]`) and a `POST /summarize`. Load
   `msgs = get_recent_messages(20)` (wrap Mongo call → clean 502 on `PyMongoError`);
   if empty, return `{ added: [], facts: get_profile_facts() }` with **no** model
   call. Otherwise call `summarizer.summarize_messages(msgs)` inside a
   `try/except OpenRouterError` → `HTTPException(502, detail=...)`. For each returned
   candidate, call `add_profile_fact` and compare the returned list length (or
   membership) to detect which were actually newly added; collect those into
   `added`. Return `{ added, facts: <final list> }`. Do not touch `/chat`.
4. **frontend/src/App.jsx — summarize control.** Add a "Summarize session" button
   (near the memory panel or skill bar). Add `summarizing` state and a
   `summarizeSession()` that `try/catch`es `POST http://localhost:8000/summarize`,
   sets `facts` from `data.facts` (refreshing the M3 chip panel), and stores
   `data.added` to render a small "Added N: fact, fact" note (or "Nothing new to
   remember" when empty). Disable the button while `summarizing`; on failure set the
   existing `profileError` so it shows inline. Leave chat send, Markdown rendering,
   the `[tier · model]` tag, and skill buttons untouched.
5. **frontend/src/index.css (styling step).** Style `.summarize-btn` and a muted
   `.summarize-added` feedback line, reusing the existing light/dark tokens
   (`--accent`, `--text-muted`, token radius/spacing) with clear
   `:hover`/`:focus-visible`/`:disabled` states, wrapping with no 360px overflow —
   no new hardcoded colors, no new CSS dependency. Keep it tasteful and minimal.

## Files to touch
- `backend/summarizer.py` (new — the summarizer subagent: extractor prompt + `summarize_messages`, strong tier, robust JSON parse)
- `backend/db.py` (add `get_recent_messages`)
- `backend/main.py` (add `POST /summarize` reusing `add_profile_fact` dedup; clean 502 on model/Mongo failure; `/chat` untouched)
- `frontend/src/App.jsx` ("Summarize session" button, `summarizeSession()`, refresh chips + show added facts)
- `frontend/src/index.css` (styling step — `.summarize-btn`/`.summarize-added`, theme-aware)

## Test plan
- **AC2 (db read, unit):** with `mongomock`, insert a few `messages`, then
  `get_recent_messages(2)` returns the **last two** in oldest→newest order;
  `get_recent_messages()` on an empty collection returns `[]`.
- **AC1 (parser, unit):** call `summarize_messages` with `chat_completion`
  monkeypatched to return (a) a clean JSON array, (b) JSON wrapped in a ```` ```json ````
  fence + prose, and (c) non-JSON garbage. Assert (a)/(b) parse to the expected
  trimmed non-empty string list and (c) returns `[]` — no exception. (No live model
  in this unit test.)
- **AC3 (dedup lands in profile, integration):** with a seeded profile fact and a
  monkeypatched summarizer returning e.g. `["weak on recursion", "studying graphs"]`
  where one duplicates an existing fact, call the `/summarize` handler and assert
  the duplicate is **not** in `added`, the genuinely new fact **is**, and `facts`
  (via `get_profile_facts`) now contains both without duplication — proving reuse of
  M3's `add_profile_fact` dedup.
- **AC1/AC3/AC4 (REAL end-to-end smoke, non-cheap tier):** with the backend up and
  services configured, seed a chat: `POST /chat {"message":"I keep getting confused
  by recursion in binary trees"}`, then a **live** `POST /summarize`. Assert HTTP 200,
  that the summarizer's **strong** slug returned successfully (so a broken strong
  slug is caught here in QA, not by the user), that `added` ⊆ `facts`, and that the
  distilled facts plausibly reference the seeded topic (e.g. a fact mentioning
  "recursion"). Then confirm `GET /profile` now returns those facts — the round-trip
  from chat → subagent → durable memory works.
- **AC3 (empty history):** `POST /summarize` against an empty `messages` collection
  → 200 `{ added: [], facts: [...] }` with no model call (assert quick / no upstream
  error). Force an upstream failure (invalid `MODEL_STRONG`) with non-empty history
  → `/summarize` returns `502` (not `500`) with a JSON `detail`.
- **AC5/AC6 (frontend + visual, manual/browser):** hold a short chat, tap
  "Summarize session"; confirm the "StudyPal remembers" chips update with new facts
  and an "Added …" note appears (or "Nothing new"), the button disables while
  running, and a backend failure shows a visible inline error (not a blank). Confirm
  chat assistant bubbles still render Markdown (real heading/list/code box, no
  literal `**`/`#`/`---`) and user turns stay plain. Toggle OS dark mode (token
  swap), resize to 360px (no horizontal scroll), check `:focus-visible`/`:disabled`.
  Grep `index.css` for `.summarize-btn` and confirm it uses theme tokens (`--accent`),
  not hardcoded colors.

## Out of scope
- **Automatic** summarization on every turn / background scheduling — M5 is
  user-triggered via the button (the architecture's "sometimes asks the summarizer"
  step is kept explicit and manual for the demo).
- Editing, ranking, deleting, or trimming facts to a token budget; per-fact
  provenance (which turn produced which fact).
- Vector DB / embeddings / RAG — plain MongoDB documents only.
- Judging or scoring reply quality — that's the M6 eval loop.
- Any change to `/chat`, `router.py`'s tier logic, or the M4 skills.
