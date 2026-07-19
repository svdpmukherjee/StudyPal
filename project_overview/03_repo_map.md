# Repo Map: every folder and the concept it teaches

Two levels live in this repo, and keeping them apart is the key to not
overwhelming students:

- **Build-time layer** = files that steer the *coding agent* (Claude Code) while
  we build. These live in `.claude/` and `context/`.
- **Runtime layer** = the actual StudyPal app code. Lives in `backend/` and
  `frontend/`.

The magic of this project: the build-time concepts (memory, skills, agents) have
a twin at runtime inside the app. Students see each idea twice.

## The map

| Path | Layer | Holds | Concept it teaches | Filled when |
|------|-------|-------|--------------------|-------------|
| `project_overview/` | build | product intent (this folder) | product-owner handoff, specs-before-code | done (pre-class) |
| `CLAUDE.md` | build | the project constitution: how the agent must work here | steering the agent | Step 1 (live) |
| `context/` | build | session continuity files | picking up where you left off | Step 2 (live) |
| `.claude/specs/` | build | one spec per module, modular | spec-driven, modular planning | Step 3+ (live) |
| `.claude/skills/` | build | reusable coding moves for the agent | procedural memory (skills) | Step 5 (live) |
| `.claude/agents/` | build | subagent definitions (summarizer, evaluator) | subagent delegation | Step 6 (live) |
| `.claude/commands/` | build | slash commands for repeatable workflows | automating the pipeline | optional |
| `backend/` | runtime | FastAPI app, router, Mongo access | the app itself | Step 4+ (live) |
| `frontend/` | runtime | React chat UI | the app itself | Step 4+ (live) |

## Inside `context/` (the "pick up where I left off" folder)

This is the part most tutorials skip and the part that makes agentic work feel
professional. Four small files:

| File | Purpose | Who writes it |
|------|---------|---------------|
| `context/PROJECT.md` | the module list (M1..M6) with a status per module | agent, at session end |
| `context/CURRENT_TASK.md` | the one task in progress + its acceptance criteria | agent, when a task starts |
| `context/WORKLOG.md` | dated log: what got done each session, one line each | agent, at session end |
| `context/DECISIONS.md` | why we chose X over Y (a lightweight ADR) | agent, when a choice is made |

`CLAUDE.md` will instruct the agent to **read `context/` at the start of every
session and update it at the end.** That single rule is what lets a fresh
session continue smoothly, exactly like the episodic-memory handoff in the
video.

## What we deliberately do NOT create

- No vector DB, no Langfuse, no auth. Named as "the next layer" only.
- Empty folders stay empty until their step. That is the syllabus, not a gap.
