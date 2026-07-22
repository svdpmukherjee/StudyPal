# CURRENT_TASK.md

**Feature in progress: M6 — Eval.**

Score answer quality with an LLM-as-judge (evaluation loop). The last TODO in
`context/PROJECT.md`.

Phase: Build complete (developer). Awaiting Phase 4 (tester) then CHECKPOINT 2
(feature approval).

## Build progress

Implemented per `.claude/specs/M6_eval.md`:

- `backend/db.py`: added `get_last_qa() -> dict | None` (most recent
  assistant reply paired with the preceding user question; `None` if no
  assistant turn or no user turn before it). Verified against mongomock
  (empty / normal / assistant-only cases).
- `backend/eval.py` (new): judge subagent — `JUDGE_PROMPT`,
  `evaluate_answer(question, answer)` (one call on `router.model_for("strong")`),
  `_parse_verdict(raw)` (strips fences, finds first `{...}`, `json.loads`,
  clamps `score`/`accuracy`/`clarity` to 1..5, safe defaults on any parse
  failure, never raises). `OpenRouterError` from `chat_completion`
  propagates. Verified: clean JSON, fenced+prose+out-of-range clamp, garbage
  -> safe default, and propagation of `OpenRouterError`.
- `backend/main.py`: added `EvaluateResponse` and `POST /evaluate` (no body):
  loads `get_last_qa()` (Mongo failure -> clean 502), returns
  `{evaluated:false, verdict:null, tier:null, model:null}` with no model call
  when there's nothing to judge, else calls `evaluator.evaluate_answer(...)`
  (imported as `import eval as evaluator` to avoid shadowing the `eval`
  builtin) inside try/except `OpenRouterError` -> 502, returns
  `{evaluated:true, verdict, tier:"strong", model: model_for("strong")}`.
  `/chat`, `/profile`, `/summarize` untouched.
- `frontend/src/App.jsx`: added `evaluating`/`verdict`/`hasEvaluated`/
  `evalError` state and `evaluateLastAnswer()` (try/catch POST
  `/evaluate`, empty body). "Evaluate last answer" button added next to
  "Summarize session", disabled while in flight. `.eval-panel` renders
  `score/5`, `accuracy`/`clarity` sub-scores, and the plain-text rationale,
  or a "Nothing to evaluate yet" note when there's no prior answer; a
  failure shows inline via `.memory-error`-styled text. Chat send, Markdown
  rendering, `[tier · model]` tag, skill buttons, summarize left untouched.
- `frontend/src/index.css`: added `.eval-btn`, `.eval-panel`, `.eval-score`,
  `.eval-subscores`, `.eval-rationale` using existing tokens (`--accent`,
  `--text-muted`, radius/spacing vars) with hover/focus-visible/disabled
  states and 360px-safe wrapping/padding. No new hardcoded colors, no new
  CSS/npm dependency.

Confirmed backend imports cleanly (`import main` succeeds, `/evaluate` route
registered) and frontend `vite build` succeeds with no errors.

## Left for tester

- Full smoke test plan from the spec (live `/chat` then live `/evaluate` on
  strong tier; empty-history 200 no-model-call case; bad `MODEL_STRONG` ->
  502; manual browser/visual check of `.eval-panel` in light+dark at 360px).
