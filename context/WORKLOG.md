# WORKLOG.md

Dated log of what got done each session, one line each. Newest at the bottom.

- 2026-07-19: Session start. `project_overview/` populated; seeded `context/`
  files (PROJECT, CURRENT_TASK, WORKLOG). Began Feature Loop for M1 (Chat core).
- 2026-07-19: M1 (Chat core) DONE. Spec `.claude/specs/M1_chat_core.md`. Built
  backend (`main.py`, `db.py`, `openrouter.py`, `requirements.txt`) and frontend
  (Vite React: `App.jsx`, `index.css` visual baseline, react-markdown +
  remark-gfm for assistant turns). All static QA checks passed; user ran the live
  end-to-end `POST /chat` smoke + frontend eyeball and approved at CHECKPOINT 2.
- 2026-07-21: M2 (Model routing) DONE. Spec `.claude/specs/M2_model_routing.md`.
  Added `backend/router.py` (keyword/length `route()` -> cheap/mid/strong,
  `TIER_MODELS` from `MODEL_CHEAP`/`MODEL_MID`/`MODEL_STRONG` env, `model_for()`);
  `chat_completion` now takes the model slug; `/chat` returns `{reply, tier, model}`
  and 502s on bad slug/upstream failure; frontend shows a muted theme-aware
  `[tier · model]` tag on assistant bubbles. Tester: all ACs PASS incl. a real live
  smoke routing to the strong tier (`anthropic/claude-sonnet-4.5`, 200 + non-empty)
  and a 502-not-500 bad-slug check. User approved at CHECKPOINT 2. Built on branch
  `feature/model-routing`.
