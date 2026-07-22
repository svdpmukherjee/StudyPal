# Spec M6: Eval

## User story
As a learner, I want to ask StudyPal to judge the quality of its own last answer
with an LLM-as-judge, so that I get a quick, structured read on how good that
explanation actually was (a 1–5 score, a couple of named criteria, and a short
reason) instead of having to trust it blindly — closing the harness's evaluation
loop.

## Acceptance criteria
- [ ] A focused **judge subagent** lives in `backend/eval.py`, mirroring the M5
      summarizer: it makes **one** LLM call on the **strong** tier via
      `router.model_for("strong")` (judging an answer is a "strong" task per the
      routing table). `evaluate_answer(question: str, answer: str) -> dict` sends a
      judge prompt asking for a **machine-parseable JSON verdict** and robustly
      parses the reply — stripping code fences/prose, finding the first `{...}`
      object, `json.loads` — into a normalized dict
      `{ "score": int(1..5), "accuracy": int(1..5), "clarity": int(1..5),
      "rationale": str }`. Any parse failure or out-of-range value yields a **safe
      default** (score clamped/defaulted, `rationale` a short fallback string) and
      **never crashes**; `OpenRouterError` from `chat_completion` **propagates** to
      the caller (uses only stdlib `json`, `re`).
- [ ] `db.py` exposes `get_last_qa() -> dict | None`: it finds the most recent
      `assistant` message and the `user` message immediately preceding it, returning
      `{ "question": <user text>, "answer": <assistant text> }`, or `None` when there
      is no such pair. It reuses the single `certifi.where()` client — no second
      client.
- [ ] `POST /evaluate` (no request body) pulls the last Q&A via `get_last_qa()`; if
      there is nothing to judge it returns `200 { "evaluated": false, "verdict": null }`
      and makes **no** model call. Otherwise it calls `eval.evaluate_answer(...)` and
      returns `200 { "evaluated": true, "verdict": { score, accuracy, clarity,
      rationale }, "tier": "strong", "model": <slug> }`. `/chat`, `/profile`, and
      `/summarize` and their response shapes are **unchanged**.
- [ ] Backend fails loud-but-clean: an OpenRouter/model failure (bad slug, timeout,
      4xx/5xx) returns `HTTPException(502)` with a JSON `detail`, and a Mongo read
      failure returns a clean `502` — never an unhandled `500` (so CORS headers are
      present and the UI can show the reason).
- [ ] The frontend adds a clearly-labelled **"Evaluate last answer"** control that
      `POST`s `/evaluate` (empty body), using the same `try/catch` + inline-error
      pattern as the M5 "Summarize session" button. On success it renders the verdict
      — the numeric **score /5**, the **accuracy** and **clarity** sub-scores, and the
      **rationale** — in an `.eval-*` panel. If no answer exists yet it shows a short
      "Nothing to evaluate yet" note. The button disables while the request is in
      flight; failures surface as a visible inline error (never a silent blank).
- [ ] Visual + Markdown baseline holds: the new eval control and verdict panel use
      existing design tokens (system font, `--accent`, `--text-muted`,
      spacing/radius) matching `.summarize-*`/`.memory-*`, read correctly in light AND
      dark via `prefers-color-scheme`, cause no horizontal scroll at 360px, and have
      clear `:hover`/`:focus-visible`/`:disabled` states. The rationale is a **short
      plain-text** line (kept plain by prompt), so no Markdown render is required; chat
      assistant bubbles still render Markdown and user turns stay plain text
      (`rehype-raw` stays OFF).

## Build plan (numbered, small steps)
1. **backend/db.py — read the last Q&A.** Add `get_last_qa() -> dict | None`: query
   `messages` sorted by `ts`/`_id` descending, walk to the most recent `assistant`
   doc and the nearest preceding `user` doc, and return
   `{ "question": user.text, "answer": assistant.text }`. Return `None` if there is
   no assistant turn (or no user turn before it). Reuse the existing client.
2. **backend/eval.py (new — the judge subagent).** Define a tight `JUDGE_PROMPT`:
   "You are a strict but fair grader. Judge the assistant's ANSWER to the student's
   QUESTION on a 1–5 scale for overall quality, plus accuracy and clarity (1–5
   each), and give a **one-sentence plain-text** rationale. Return ONLY a JSON
   object: `{\"score\":n,\"accuracy\":n,\"clarity\":n,\"rationale\":\"...\"}`."
   Implement `evaluate_answer(question, answer)`: build `context` (system judge
   prompt + a user message embedding QUESTION and ANSWER), call
   `chat_completion(context, model_for("strong"))`, then parse via a helper
   `_parse_verdict(raw)` that strips a ```` ``` ```` fence, finds the first `{...}`
   with `re`, `json.loads`, coerces each score to an int clamped to 1..5 (defaulting
   to `3` on missing/garbage), and takes a trimmed `rationale` string (fallback:
   "No rationale returned."). On any parse error return the safe default verdict —
   never raise. Let `OpenRouterError` propagate. Reuse M5's fence/JSON-parsing style
   (stdlib `json`, `re` only).
3. **backend/main.py — `/evaluate` route.** Add an `EvaluateResponse`
   (`evaluated: bool`, `verdict: dict | None`, `tier: str | None`,
   `model: str | None`) and a `POST /evaluate` (no body). Load `qa = get_last_qa()`
   (wrap the Mongo call → clean `502` on `PyMongoError`); if `None`, return
   `{ evaluated: False, verdict: None, tier: None, model: None }` with **no** model
   call. Otherwise call `eval.evaluate_answer(qa["question"], qa["answer"])` inside
   `try/except OpenRouterError` → `HTTPException(502, detail=...)`, and return
   `{ evaluated: True, verdict, tier: "strong", model: model_for("strong") }`. Do
   not touch `/chat`, `/profile`, `/summarize`. (Note: `eval` is a Python builtin —
   import the module as `import eval as evaluator` or name the file `evals.py`;
   Developer picks one and stays consistent.)
4. **frontend/src/App.jsx — evaluate control.** Add `evaluating`, `verdict`, and
   `hasEvaluated` state and an `evaluateLastAnswer()` that `try/catch`es
   `POST http://localhost:8000/evaluate` (empty body), stores `data.verdict` when
   `data.evaluated`, and clears/marks "nothing to evaluate" otherwise; on failure
   set the existing `profileError` (or a dedicated `evalError`) so it shows inline.
   Add an "Evaluate last answer" button near the summarize row, disabled while
   `evaluating`. Render a small `.eval-panel` showing `score/5`, `accuracy` and
   `clarity` sub-scores, and the plain-text `rationale`. Leave chat send, Markdown
   rendering, the `[tier · model]` tag, skill buttons, and summarize untouched.
5. **frontend/src/index.css (styling step).** Style `.eval-btn`, `.eval-panel`,
   `.eval-score`, and a muted `.eval-rationale`, reusing existing light/dark tokens
   (`--accent`, `--text-muted`, token radius/spacing) with clear
   `:hover`/`:focus-visible`/`:disabled` states, wrapping with no 360px overflow —
   no new hardcoded colors, no new CSS dependency. Keep it tasteful and minimal, in
   the visual language of `.summarize-*`/`.memory-*`.

## Files to touch
- `backend/eval.py` (new — judge subagent: `JUDGE_PROMPT`, `evaluate_answer`, `_parse_verdict`; strong tier; robust JSON parse; safe defaults)
- `backend/db.py` (add `get_last_qa`)
- `backend/main.py` (add `POST /evaluate` + `EvaluateResponse`; clean 502 on model/Mongo failure; `/chat`, `/profile`, `/summarize` untouched)
- `frontend/src/App.jsx` ("Evaluate last answer" button, `evaluateLastAnswer()`, verdict panel)
- `frontend/src/index.css` (styling step — `.eval-btn`/`.eval-panel`/`.eval-score`/`.eval-rationale`, theme-aware)

## Test plan
- **AC2 (db read, unit):** with `mongomock`, insert user/assistant turns; assert
  `get_last_qa()` returns the **most recent** assistant answer paired with the
  **user question just before it**; on an empty collection (or assistant-only)
  it returns `None`.
- **AC1 (parser, unit):** call `_parse_verdict` (or `evaluate_answer` with
  `chat_completion` monkeypatched) on (a) a clean JSON object, (b) JSON wrapped in a
  ```` ```json ```` fence + prose, and (c) non-JSON garbage. Assert (a)/(b) parse to
  the normalized verdict with `score`/`accuracy`/`clarity` ints in 1..5 and a
  non-empty `rationale`; assert (c) returns the **safe default** verdict with **no
  exception**. Also assert an out-of-range score (e.g. `9`) is clamped to `1..5`.
- **AC1 (propagation, unit):** with `chat_completion` monkeypatched to raise
  `OpenRouterError`, assert `evaluate_answer` **propagates** it (does not swallow).
- **AC3/AC4 (no-history, integration):** `POST /evaluate` against an empty `messages`
  collection → `200 { evaluated: false, verdict: null }` with **no** model call
  (assert quick / no upstream call made).
- **AC1/AC3/AC4 (REAL end-to-end smoke, strong tier):** with the backend up and
  services configured, seed a chat: `POST /chat {"message":"Explain how recursion
  unwinds on the call stack for factorial(3)"}` (routes mid/strong), then a **live**
  `POST /evaluate`. Assert HTTP 200, `evaluated == true`, `tier == "strong"`, that
  the **strong** slug returned successfully (so a broken strong slug is caught in QA,
  not by the user), and that `verdict.score`/`accuracy`/`clarity` are ints in 1..5
  with a non-empty `rationale`.
- **AC4 (REAL negative check, clean 502):** with a non-empty last Q&A, force an
  upstream failure by setting an invalid `MODEL_STRONG` slug and calling
  **live** `POST /evaluate`; assert it returns `502` (not `500`) with a JSON
  `detail` — mirroring M5's bad-slug check.
- **AC5/AC6 (frontend + visual, manual/browser):** send a chat message, tap
  "Evaluate last answer"; confirm the verdict panel shows `score/5`, accuracy,
  clarity, and a plain rationale line; with no prior answer it shows "Nothing to
  evaluate yet"; the button disables while running; a backend failure shows a
  visible inline error (not a blank). Toggle OS dark mode (token swap), resize to
  360px (no horizontal scroll), check `:focus-visible`/`:disabled`. Grep
  `index.css` for `.eval-btn`/`.eval-panel` and confirm they use theme tokens
  (`--accent`, `--text-muted`), not hardcoded colors. Confirm chat assistant bubbles
  still render Markdown and user turns stay plain.

## Out of scope
- **Batch/benchmark evaluation**, datasets, regression scoring, or a leaderboard —
  M6 judges exactly the **last** answer on demand, one call, for the demo.
- **Auto-evaluating every turn**, storing verdicts back to Mongo, or gating replies
  on a minimum score — the loop is user-triggered and read-only.
- Multi-judge ensembles, pairwise A/B comparison, or letting the user pick which
  past answer to grade (always the latest Q&A).
- Rendering the rationale as Markdown — it is deliberately a short plain-text line;
  chat Markdown rendering is unchanged.
- Any change to `/chat`, `/summarize`, `/profile`, `router.py`'s tier logic, or the
  M4 skills / M5 summarizer.
