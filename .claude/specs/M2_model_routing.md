# Spec M2: Model routing

## User story
As a learner, I want StudyPal to pick a cheap, mid, or strong model based on how
hard my message is, and to show me which one answered, so that easy turns stay
fast/cheap and hard turns get a stronger model — and I can see the harness making
that choice.

## Acceptance criteria
- [ ] A router function `route(message) -> "cheap" | "mid" | "strong"` classifies
      an incoming message by a simple, honest rule (keyword and/or message-length
      based). Greetings/short recall → `cheap`; explain-a-concept → `mid`;
      quiz/generate/judge or long/complex asks → `strong`. The rule is readable
      and unit-tested for at least one message per tier.
- [ ] The three tier slugs come from env/config (`MODEL_CHEAP`, `MODEL_MID`,
      `MODEL_STRONG`) with sensible defaults, so a stale slug is swapped by editing
      `.env` — no code change. `chat_completion` accepts the chosen model as an
      argument (no longer reads a single `OPENROUTER_MODEL`).
- [ ] `POST /chat` returns HTTP 200 with JSON `{ reply, tier, model }` where `tier`
      is one of cheap/mid/strong and `model` is the exact slug used.
- [ ] The UI shows a small, muted `[tier · model]` tag on each assistant bubble
      (e.g. `mid · google/gemini-2.5-flash`), styled per the visual baseline
      (muted, not shouting), matching light/dark tokens; assistant Markdown still
      renders (no literal `**`/`#`/`---`) and user turns stay plain text.
- [ ] Backend fails loud-but-clean: a bad/retired slug or any OpenRouter
      4xx/5xx/timeout for the routed model returns an `HTTPException` (`502` with a
      JSON `detail`), never an unhandled `500`.
- [ ] A live `POST /chat` whose message routes to **mid or strong** returns HTTP
      200 with a non-empty `reply` and the matching `tier`/`model`, proving the
      non-cheap slug is valid.

## Build plan (numbered, small steps)
1. **backend/router.py (new).** Add `route(message: str) -> str` returning
   `"cheap" | "mid" | "strong"`. Simple honest rule: lowercase the message, check
   for strong keywords (`quiz`, `test me`, `generate`, `grade`, `evaluate`,
   `judge`, `problem set`) → `strong`; mid keywords (`explain`, `why`, `how`,
   `what is`, `walk me through`, `example`) or length over ~200 chars → `mid`;
   else `cheap`. Add a comment: "a real system would classify intent here."
   Expose a `TIER_MODELS` dict read from env with defaults matching
   `.env.example` (`MODEL_CHEAP` / `MODEL_MID` / `MODEL_STRONG`), and a helper
   `model_for(tier) -> slug`.
2. **backend/openrouter.py.** Change `chat_completion(messages, model)` to take
   the model slug as a parameter (default falls back to `MODEL_CHEAP` env or the
   old `OPENROUTER_MODEL` for safety). Keep the existing error handling: timeout,
   non-2xx, missing/empty content all raise `OpenRouterError` (→ 502). A rejected
   slug (404/400) already flows through the non-2xx branch — confirm it does.
3. **backend/main.py.** In `/chat`: after saving the user message, call
   `tier = route(req.message)` and `model = model_for(tier)`; build context;
   call `chat_completion(context, model)` inside the existing try/except; on
   `OpenRouterError` raise `HTTPException(502, detail=...)`. Extend
   `ChatResponse` to `{ reply: str, tier: str, model: str }` and return all three.
4. **backend/.env.example.** Confirm `MODEL_CHEAP` / `MODEL_MID` / `MODEL_STRONG`
   are present (they are). Note in a comment that slugs go stale — confirm live on
   openrouter.ai before relying on a tier.
5. **frontend/src/App.jsx.** Store `tier` and `model` on the assistant message
   object from the response; pass them to `Bubble`. Render a `<span className=
   "msg-tag">{tier} · {model}</span>` inside the assistant bubble (or its row),
   only for assistant turns. Leave user/error/thinking rendering unchanged.
6. **frontend/src/index.css (styling step).** Add a `.msg-tag` rule: small font
   (~0.72rem), `--text-muted` color, subtle letter-spacing, modest top margin so
   it sits under the rendered reply without shouting; must read correctly in both
   light and dark via existing tokens. No new colors outside the token set.

## Files to touch
- `backend/router.py` (new — `route()`, `TIER_MODELS`, `model_for()`)
- `backend/openrouter.py` (change `chat_completion` to take a `model` arg)
- `backend/main.py` (route → tier → model; return `{ reply, tier, model }`)
- `backend/.env.example` (confirm tier slug vars + stale-slug note)
- `frontend/src/App.jsx` (carry `tier`/`model`; render `[tier · model]` tag)
- `frontend/src/index.css` (new `.msg-tag` style, theme-aware)

## Test plan
- **AC1 (router rule):** unit test `route()` (pure function, no network/DB) with
  at least one message per tier — e.g. `"hi"` → `cheap`, `"explain recursion"` →
  `mid`, `"quiz me on binary trees"` → `strong`. Assert exact tier strings.
- **AC2 (config-sourced slugs):** unit test that `model_for("mid")` returns the
  `MODEL_MID` env value (set a temp env var to a sentinel and assert it flows
  through), proving slugs are swappable without code changes.
- **AC3 + AC6 (200 shape, live smoke):** REAL end-to-end smoke — start the backend
  against configured services and `POST /chat` with a message that routes to a
  **strong** tier, e.g. `{"message":"Quiz me on recursion with a short numbered
  list and one code example"}`; assert HTTP 200, non-empty `reply`, `tier` ==
  `"strong"`, and `model` == the configured `MODEL_STRONG` slug. This catches a
  broken non-cheap slug in QA. Optionally repeat with an `"explain …"` message and
  assert `tier` == `"mid"`.
- **AC4 (tag + Markdown, visual):** manual/browser check — send a message and
  confirm the assistant bubble shows a small muted `[tier · model]` tag and the
  Markdown renders (real heading/list/code box, no literal `**`/`#`/`---`); user
  turn stays plain text. Grep `index.css` for `.msg-tag` and confirm it uses
  `--text-muted` (theme token, not a hardcoded color).
- **AC5 (backend loud-but-clean):** set `MODEL_STRONG` to an invalid slug and
  `POST /chat` with a strong-routing message; assert the response is `502` (not
  `500`) with a JSON `detail`.

## Out of scope
- Learner profile / durable facts and the summarizer (M3, M5).
- Skills like `explain-simply` / `quiz-me` (M4) and evaluation (M6).
- ML/LLM-based intent classification — the demo router is deliberately a simple
  keyword/length rule.
- Streaming, cost accounting, per-user model preferences, ret/fallback across
  tiers on failure.
