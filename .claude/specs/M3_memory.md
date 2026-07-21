# Spec M3: Memory

## User story
As a learner, I want StudyPal to remember durable facts about me (what I'm
studying, where I'm weak, how I like answers) across sessions, so that it greets
me as someone it already knows and can proactively revisit my weak spots instead
of starting from scratch every time.

## Acceptance criteria
- [ ] Durable facts live in the MongoDB `profile` collection as a single document
      shaped `{ _id, facts: ["studying algorithms", "weak on recursion", ...],
      updated_ts }`. `db.py` exposes helpers to read the facts list and to add a
      fact (de-duplicated, trimmed, no empty strings), always creating the client
      with `tlsCAFile=certifi.where()`.
- [ ] `GET /profile` returns HTTP 200 with `{ facts: [...] }` (empty list when the
      profile doc doesn't exist yet). `POST /profile` with `{ fact: "<non-empty>" }`
      appends a durable fact and returns the updated `{ facts: [...] }`; a blank or
      duplicate fact does not create a redundant entry.
- [ ] On every `POST /chat`, the backend loads the learner's profile facts and
      injects them into the model context (e.g. a "What you already know about this
      learner:" block in the system prompt), so a stored fact demonstrably steers
      the reply. `/chat` still returns `{ reply, tier, model }` (unchanged shape).
- [ ] The frontend loads the profile on mount (`GET /profile`) and shows a small,
      muted "StudyPal remembers" panel of fact chips under the header, and provides
      a labelled inline "remember this" input that `POST`s a new fact and updates
      the panel — all wrapped in `try/catch` so a failed profile call shows a
      visible error, never a silent blank.
- [ ] Visual baseline holds: the memory panel and chips use the existing design
      tokens (system font, `--accent`, spacing/radius), read correctly in light AND
      dark via `prefers-color-scheme`, cause no horizontal scroll at 360px wide, and
      the add-fact control has clear `:hover`/`:focus-visible`/`:disabled` states.
      Assistant replies still render as Markdown (heading/list/inline `code`/fenced
      block, no literal `**`/`#`/`---`); user turns stay plain text; `rehype-raw`
      stays OFF.
- [ ] Backend fails loud-but-clean: any OpenRouter or model error still returns an
      `HTTPException` (`502` with JSON `detail`), never an unhandled `500`; a Mongo
      read failure on `/profile` returns a clean error too, not a raw crash.

## Build plan (numbered, small steps)
1. **backend/db.py.** Add the `profile` collection alongside `messages`. Use a
   single well-known document (e.g. `{ "_id": "learner" }`). Add
   `get_profile_facts() -> list[str]` (returns `[]` when the doc is absent) and
   `add_profile_fact(fact: str) -> list[str]` that trims the fact, ignores
   empty/duplicate values (case-insensitive dedup), `$addToSet`s it into `facts`,
   sets `updated_ts`, and returns the full updated list. Keep the existing
   `certifi.where()` client — no second client.
2. **backend/main.py — profile routes.** Add `GET /profile` returning
   `{ "facts": get_profile_facts() }` and `POST /profile` taking
   `{ fact: str }` → `add_profile_fact(...)` → `{ "facts": [...] }`. Reject an
   empty `fact` with `HTTPException(400, ...)`. Wrap the Mongo calls so a store
   failure surfaces as a clean error (not an unhandled 500).
3. **backend/main.py — inject memory into /chat.** Before calling the model, load
   `facts = get_profile_facts()`. If non-empty, extend `SYSTEM_PROMPT` with a
   block like: "What you already know about this learner: <facts joined as a
   bullet list>. Use this to feel like you remember them and gently revisit weak
   spots." Build context as `[system(+memory), user]`, then route/call/save
   exactly as today. Response shape stays `{ reply, tier, model }`.
4. **frontend/src/App.jsx — load + display memory.** On mount (`useEffect`),
   `try/catch` `GET http://localhost:8000/profile`; store `facts` in state; render
   a "StudyPal remembers" panel of chips under the header (hidden when empty). On
   a profile fetch failure, show a visible inline error, not a blank panel.
5. **frontend/src/App.jsx — add a fact.** Add a small labelled input + "Remember"
   button; on submit, `try/catch` `POST /profile` with `{ fact }`, update the
   chips from the response, clear the input, and disable the control while the
   request is in flight. Leave the chat send flow, Markdown rendering, and
   `[tier · model]` tag untouched.
6. **frontend/src/index.css (styling step).** Style `.memory-panel` and
   `.memory-chip` (small, muted, `--accent`-tinted pill chips with radius/padding
   from tokens, wrapping with no 360px overflow) and the add-fact control
   (`:hover`/`:focus-visible`/`:disabled`), all theming via existing light/dark
   tokens — no new hardcoded colors. Keep it tasteful and minimal.

## Files to touch
- `backend/db.py` (add `profile` collection + `get_profile_facts` / `add_profile_fact`)
- `backend/main.py` (add `GET`/`POST /profile`; inject facts into `/chat` context)
- `frontend/src/App.jsx` (load profile on mount, chips panel, add-fact form)
- `frontend/src/index.css` (styling step — `.memory-panel`/`.memory-chip`, add-fact control, theme-aware)

## Test plan
- **AC1 (db helpers):** unit test against `mongomock` — `add_profile_fact("weak on
  recursion")` then `get_profile_facts()` returns it; adding the same fact (and a
  case variant) does not duplicate; a blank/whitespace fact is ignored;
  `get_profile_facts()` on an empty DB returns `[]`.
- **AC2 (profile routes):** with the backend up, `GET /profile` → 200 `{ facts }`;
  `POST /profile {"fact":"prefers short answers"}` → 200 with the fact present;
  `POST /profile {"fact":"  "}` → 400. Confirm no duplicate on re-post.
- **AC3 + AC6 (memory steers reply, live smoke):** REAL end-to-end smoke — seed a
  fact via `POST /profile {"fact":"weak on recursion"}`, then live `POST /chat`
  with a message that routes to **mid or strong**, e.g.
  `{"message":"Explain what I should study next based on what you know about me,
  with a short numbered list and one code example"}`. Assert HTTP 200, non-empty
  `reply`, `tier` in {mid, strong}, and that the reply text references the seeded
  weak spot (assert the reply mentions "recursion"), proving stored facts reached
  the model. Then set an invalid `MODEL_STRONG` (or force an upstream error) and
  confirm `/chat` returns `502` (not `500`) with a JSON `detail`.
- **AC4 + AC5 (frontend + visual):** manual/browser check — load the app; confirm
  the "StudyPal remembers" chips appear from `GET /profile`; add a fact via the
  form and see a new chip; send a chat message and confirm the assistant bubble
  still renders Markdown (real heading/list/code box, no literal `**`/`#`/`---`)
  and user turns stay plain text. Toggle OS dark mode (token swap), resize to
  360px (no horizontal scroll), and confirm the add-fact control shows
  focus/disabled states. Stop the backend and reload to confirm a visible profile
  error instead of a silent blank. Grep `index.css` for `.memory-chip` and confirm
  it uses theme tokens (`--accent`/`--text-muted`), not hardcoded colors.

## Out of scope
- **Automatic** distillation of chats into facts — the summarizer subagent that
  writes to `profile` is M5. M3 stores facts explicitly (seeded via `POST /profile`
  or the add-fact form) and only *loads + injects + recalls* them.
- Vector DB / embeddings / RAG — plain MongoDB documents only ("in production this
  line becomes a vector search").
- Per-learner profiles / auth / multi-user — a single shared `profile` doc.
- Editing or deleting individual facts, fact ranking, or trimming context to a
  token budget.
- Skills (M4) and evaluation (M6).
