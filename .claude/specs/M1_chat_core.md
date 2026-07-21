# Spec M1: Chat core

## User story
As a learner, I want to type a message into one chat box and get a helpful,
nicely formatted reply, so that I can study by talking to StudyPal and have the
conversation remembered for next time.

## Acceptance criteria
- [ ] A learner can type a message, press Send (or Enter), and see the reply
      appear as a left-aligned assistant bubble; their own message shows as a
      right-aligned user bubble.
- [ ] `POST /chat` calls OpenRouter using the single `OPENROUTER_MODEL` and
      returns HTTP 200 with a JSON `{ reply: "<non-empty string>" }`.
- [ ] Both the user message and the assistant reply are persisted to MongoDB
      `messages` as documents shaped `{ _id, role: "user"|"assistant", text, ts }`.
- [ ] Visual baseline: the page looks intentionally designed (system font,
      design tokens, centered ~720px column, sticky header, scrollable
      auto-scrolling message area, input bar pinned to bottom), not raw browser
      defaults. It supports light AND dark via `prefers-color-scheme`, has no
      horizontal scroll at 360px wide, disables input/button while a request is
      in flight, shows a "StudyPal is thinking…" indicator during the request,
      and renders the error line as a distinct (red-tinted) bubble.
- [ ] Markdown render: an assistant reply containing a heading, a numbered list,
      inline `code`, and a fenced code block renders as *formatted* output (real
      headings demoted to bubble size, indented list, code box) via
      `react-markdown` + `remark-gfm` — no literal `**`, `#`, or `---` visible.
      User turns stay plain text; raw-HTML passthrough is OFF (no `rehype-raw`).
- [ ] Backend fails loud-but-clean: a bad model slug or any OpenRouter 4xx/5xx /
      timeout returns an `HTTPException` (e.g. `502` with a JSON `detail`), never
      an unhandled `500`.
- [ ] Frontend fails loud-but-clean: the `POST /chat` call is wrapped in
      `try/catch` and any failure renders a visible error line in the chat, not a
      silent blank.

## Build plan (numbered, small steps)
1. **Backend deps.** Fill `backend/requirements.txt`: `fastapi`, `uvicorn[standard]`,
   `pymongo`, `certifi` (pinned), `httpx` (or `openai`) for the OpenRouter call,
   `python-dotenv`. Pin versions.
2. **backend/db.py.** Load `MONGODB_URI` / `MONGODB_DB` from env; create
   `MongoClient(MONGODB_URI, tlsCAFile=certifi.where())` (safe for local, required
   for Atlas). Expose the `messages` collection and a small
   `save_message(role, text)` helper writing `{ role, text, ts }` (server time).
3. **backend/openrouter.py.** One function `chat_completion(messages) -> str` that
   POSTs to OpenRouter `/chat/completions` with `OPENROUTER_API_KEY` and
   `OPENROUTER_MODEL`. On any upstream error (non-2xx, timeout, missing content)
   raise a clear exception the route converts to a 502.
4. **backend/main.py.** FastAPI app + CORS middleware (allow the Vite dev origin,
   `http://localhost:5173`). Route `POST /chat` taking `{ message: str }`:
   save the user message, build `[system, user]` context, call
   `chat_completion`, save the assistant reply, return `{ reply }`. Wrap the model
   call in try/except and raise `HTTPException(status_code=502, detail=...)` on
   failure. Add a `GET /health` returning `{ ok: true }`.
5. **Create the Vite React app** in `frontend/` (`npm create vite@latest . --
   --template react`), then add `react-markdown` and `remark-gfm` to
   `frontend/package.json`.
6. **frontend/src/App.jsx.** Single chat component: message list state, controlled
   input, submit handler that `try/catch`es `fetch('http://localhost:5173'…
   /chat)` (backend URL, e.g. `http://localhost:8000/chat`), appends user + reply,
   shows a "thinking" flag while awaiting, disables controls in flight, and pushes
   an error bubble on catch. Auto-scroll to newest.
7. **Markdown rendering.** Render assistant bubbles with `<ReactMarkdown
   remarkPlugins={[remarkGfm]}>` (no `rehype-raw`); render user bubbles as plain
   string.
8. **frontend/src/index.css (styling step).** Implement the visual baseline:
   `:root` design tokens (colors, spacing, radius, shadow, `--accent`), system
   font stack, dark-mode token swap via `@media (prefers-color-scheme: dark)`,
   centered column, sticky header, scrollable message area, sticky input bar,
   user/assistant bubbles, hover/focus-visible/disabled control states, thinking
   indicator, red-tinted error bubble, and scoped Markdown element styles under
   `.msg-assistant` (demoted headings, indented lists, inline/`pre` code boxes
   with `overflow-x:auto`, thin `hr`, scrollable table wrapper). Import once in
   `frontend/src/main.jsx`.

## Files to touch
- `backend/requirements.txt` (fill; `certifi` pinned)
- `backend/db.py` (new)
- `backend/openrouter.py` (new)
- `backend/main.py` (new — app, CORS, `/chat`, `/health`)
- `backend/.env.example` (already has the needed keys; leave as-is / confirm)
- `frontend/` (new Vite React scaffold: `package.json`, `index.html`,
  `vite.config.js`, `src/main.jsx`)
- `frontend/package.json` (add deps `react-markdown`, `remark-gfm`)
- `frontend/src/App.jsx` (new — chat component, try/catch, Markdown render)
- `frontend/src/index.css` (new — visual baseline + scoped Markdown styles)

## Test plan
- **AC1 (send/receive) + AC2 (200 non-empty):** REAL end-to-end smoke — start the
  backend against configured services and run a live `POST /chat` with a body like
  `{"message":"Explain recursion with a short numbered list and a code example"}`;
  assert HTTP 200 and a non-empty `reply` string. (Routing/tiers arrive in M2, so
  this uses the single `OPENROUTER_MODEL`.)
- **AC3 (persistence):** after the smoke, query MongoDB `messages` and assert two
  new docs exist with roles `user` and `assistant`, each with `text` and `ts`;
  verify the shape `{ _id, role, text, ts }`.
- **AC4 (visual baseline):** manual/browser check — load the app, confirm styled
  layout (sticky header, bottom input, bubbles), toggle OS dark mode to see token
  swap, resize to 360px for no horizontal scroll, and observe the disabled
  controls + "thinking…" indicator during a request. Grep `index.css` for
  `prefers-color-scheme`, `--accent`, and a system-font stack as a proxy check.
- **AC5 (Markdown):** send a reply with a heading, numbered list, inline `code`,
  and a fenced code block; confirm formatted output (real bullets/box) and NO
  literal `**`/`#`/`---`. Confirm user turns are plain text and `rehype-raw` is
  absent from the code.
- **AC6 (backend loud-but-clean):** temporarily set an invalid `OPENROUTER_MODEL`
  (or point at a bad slug) and `POST /chat`; assert the response is a `502`
  (not `500`) with a JSON `detail`.
- **AC7 (frontend loud-but-clean):** with the backend stopped (or forced error),
  send a message in the UI and confirm a visible error bubble appears rather than
  a silent blank chat.

## Out of scope
- Model routing / tiers (M2) — M1 uses the single `OPENROUTER_MODEL`.
- Loading learner profile / durable facts and the summarizer (M3, M5).
- Skills like `explain-simply` / `quiz-me` (M4) and evaluation (M6).
- Auth, multi-user, conversation history pagination, streaming responses.
