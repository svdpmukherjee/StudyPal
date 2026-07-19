# WORKLOG.md

Dated log of what got done each session, one line each. Newest at the bottom.

- 2026-07-19: Session start. `project_overview/` populated; seeded `context/`
  files (PROJECT, CURRENT_TASK, WORKLOG). Began Feature Loop for M1 (Chat core).
- 2026-07-19: M1 (Chat core) DONE. Spec `.claude/specs/M1_chat_core.md`. Built
  backend (`main.py`, `db.py`, `openrouter.py`, `requirements.txt`) and frontend
  (Vite React: `App.jsx`, `index.css` visual baseline, react-markdown +
  remark-gfm for assistant turns). All static QA checks passed; user ran the live
  end-to-end `POST /chat` smoke + frontend eyeball and approved at CHECKPOINT 2.
