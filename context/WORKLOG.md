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
- 2026-07-21: M3 (Memory) DONE. Spec `.claude/specs/M3_memory.md`. Added a
  `profile` collection (single `{_id:"learner", facts[], updated_ts}` doc) with
  `get_profile_facts`/`add_profile_fact` (trim + case-insensitive dedup,
  `$addToSet`) in `backend/db.py`, reusing the certifi-pinned client; `GET`/`POST
  /profile` routes in `backend/main.py` (400 on blank fact, Mongo failures wrapped
  clean); `/chat` injects the learner's facts into the system prompt (shape
  `{reply, tier, model}` unchanged). Frontend `App.jsx` loads the profile on mount,
  shows a "StudyPal remembers" chip panel + labelled add-fact form (try/catch,
  inline errors), theme-aware `.memory-*` styling in `index.css`; Markdown render
  + `[tier·model]` tag untouched. Tester: AC1 mongomock dedup 4/4, AC2 routes,
  AC3/AC6 real live smoke routing to mid (`google/gemini-2.5-flash`, 200, reply
  recalled the seeded "recursion" weak spot) + 502-not-500 bad-slug check; frontend
  static PASS. Purely visual items (browser eyeball, 360px, dark toggle) left to
  human per spec. User approved at CHECKPOINT 2.
- 2026-07-21: M4 (Skills) DONE. Spec `.claude/specs/M4_skills.md`. Added two
  runtime tutoring "moves" as skill prompt files (`backend/skills/explain-simply.md`,
  `quiz-me.md` — procedural memory, prompts only, ask for chat-friendly Markdown)
  loaded by a new allowlisted `backend/skills.py` (`ALLOWED_SKILLS =
  {explain-simply:mid, quiz-me:strong}`, `load_skill()` path-traversal-safe +
  `ValueError` on unknown names, `skill_tier()`). `/chat` gained an optional
  `skill` field: invalid -> clean 502-style `HTTPException(400)` (not 500), valid
  skill drives the tier (bypasses `route()`) and its prompt is injected AFTER the
  M3 memory block; no-skill path + `router.py` untouched; response echoes `skill`.
  Frontend `App.jsx` got "Explain simply"/"Quiz me" buttons (disabled while
  thinking/empty) + a "via <skill>" tag on the assistant bubble beside
  `[tier·model]`; theme-token `.skill-bar`/`.skill-btn`/`.msg-skill` in
  `index.css`; Markdown render (react-markdown + remark-gfm, rehype-raw OFF, user
  turns plain) unchanged. Tester: all ACs PASS incl. unit loader/traversal, invalid
  skill 400-not-500, and a REAL live smoke routing `quiz-me` to strong
  (`anthropic/claude-sonnet-4.5`, 200 non-empty, seeded "weak on recursion" surfaced
  in the quiz — M3 memory still applies) + a plain-vs-`explain-simply` diff proving
  the skill prompt reached the model. Note: a stale uvicorn (no `--reload`) faked an
  early pass; restart the server after a dev handoff. Visual items (dark toggle,
  360px, focus ring) left to human. User approved at CHECKPOINT 2.
