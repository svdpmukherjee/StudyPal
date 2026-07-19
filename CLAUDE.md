# CLAUDE.md - StudyPal

You are the **orchestrator** for this project. You do not write feature code
yourself. You read the current state, call the right subagent for each phase,
stop at checkpoints for human approval, and keep `context/` up to date so the
next session can continue.

## What this project is

StudyPal is a small React + FastAPI + MongoDB study-buddy chatbot (models via
OpenRouter). The full intent lives in `project_overview/`. Read it if you are
unsure what a module is for.

Pointers you will use constantly:

- `project_overview/` - product intent, architecture, module list.
- `.claude/specs/` - one spec per feature (the Planner writes these).
- `context/` - session memory. Read at start, update at end. Never skip this.

## Prime directive

> When the user names a feature (for example "build feature M3", "next feature",
> or `/feature M3`), run the **Feature Development Loop** below, one phase at a
> time, pausing at every CHECKPOINT.

One session builds **one** feature. When a feature is approved, tell the user to
open a **new session** for the next one.

## Roles

| Role                | Who                  | Job                                                    | Lives in                      |
| ------------------- | -------------------- | ------------------------------------------------------ | ----------------------------- |
| Orchestrator        | you (this session)   | sequence phases, manage checkpoints, update `context/` | CLAUDE.md                     |
| Planner (Architect) | `planner` subagent   | turn a module into a spec + step-by-step build plan    | `.claude/agents/planner.md`   |
| Developer (Builder) | `developer` subagent | implement the spec into `backend/`, `frontend/`        | `.claude/agents/developer.md` |
| Tester (QA)         | `tester` subagent    | verify the code against the spec, report pass/fail     | `.claude/agents/tester.md`    |

**Handoff rule:** agents never hand work to each other directly. They hand off
through **files**. The Planner writes a spec file; the Developer reads that spec;
the Tester reads the spec and the code. You pass the file paths between them.

## Feature Development Loop

Given a feature ID (for example `M3`):

**Phase 0 - Precondition (intent exists).** The Feature Loop plans against
`project_overview/`. If that folder is empty or still stub (no real
`01_product_brief.md` module list), **stop** and tell the user to run
`/interview-me` first, which interviews them and writes the five overview docs
plus seeds `context/PROJECT.md`. Do not invent the intent yourself. Once
`project_overview/` is populated, continue.

**Phase 1 - Orient.** Read `context/PROJECT.md`, `context/CURRENT_TASK.md`, and
the module row in `project_overview/01_product_brief.md`. If the user said "next
feature", pick the first module whose status is TODO in `context/PROJECT.md`.
Write the chosen feature into `context/CURRENT_TASK.md`.

**Phase 2 - Plan.** Call the `planner` subagent with the feature ID and the
paths above. It writes `.claude/specs/<ID>_<name>.md` containing: user story,
acceptance criteria, a numbered build plan, the exact files to touch, and a test
plan. Do not write code yet.

> **CHECKPOINT 1 (spec approval):** Show the user the spec path and a 3-line
> summary. Stop. Wait for "approved" before continuing. If they request changes,
> call the `planner` again with their notes.

**Phase 3 - Build.** Call the `developer` subagent with the approved spec path.
It implements the numbered build plan into `backend/` and `frontend/`, following
the spec's file list. It updates `context/CURRENT_TASK.md` with progress.

**Phase 4 - Test.** Call the `tester` subagent with the spec path. It runs the
spec's test plan (unit or smoke), reports pass/fail with details. If it fails,
call the `developer` once with the failure notes to fix, then re-test.

> **CHECKPOINT 2 (feature approval):** Report what was built and the test result.
> Stop. Wait for the user to review and say "approved".

**Phase 5 - Close.** After approval: append a dated line to `context/WORKLOG.md`,
set the module status to DONE in `context/PROJECT.md`, clear
`context/CURRENT_TASK.md`. Then tell the user: "Feature <ID> done. Open a new
session for the next feature."

## Session protocol

- **At session start:** read `context/PROJECT.md`, `context/CURRENT_TASK.md`,
  `context/WORKLOG.md` (last few lines). State in one line where we are.
- **At session end (or after each feature):** update those files as in Phase 5.
  This is how the next session picks up where this one left off.

## Guardrails

- One feature per session. Do not start a second feature; ask the user to open a
  new session.
- Never skip Phase 2. No code without an approved spec.
- Never pass CHECKPOINT gates on your own. A human approves.
- Keep it small. This is a teaching demo, not production. Prefer the simplest
  thing that satisfies the spec.
- If something is ambiguous, ask one question rather than guessing.

## Conventions

- Backend: FastAPI in `backend/`. Frontend: React (Vite) in `frontend/`. Store:
  MongoDB, collections `messages` and `profile`.
- Models via OpenRouter. Key in `backend/.env` (`OPENROUTER_API_KEY`), never
  committed. Document keys in `backend/.env.example`.
- Route model choice by task complexity (cheap / mid / strong), as in
  `project_overview/02_architecture.md`.
- OpenRouter model slugs go stale (models get renamed/retired). The slugs in
  `02_architecture.md` are **examples, not guarantees** - before wiring a tier,
  confirm each slug is currently valid (e.g. a live call, or `GET /models`). A
  slug OpenRouter rejects (404/400) must never reach the user as a raw crash;
  see the backend error convention below.
- MongoDB client always passes `tlsCAFile=certifi.where()` (pin `certifi`) so
  `mongodb+srv` (Atlas) TLS verifies on macOS; harmless on local Mongo. See
  "MongoDB: local or Atlas" in `project_overview/02_architecture.md`.
- The frontend `POST /chat` call must `try/catch` and show errors in the UI;
  never let a failed request render as a blank, silent chat.
- The frontend must apply the **visual baseline** ("Frontend look & feel" in
  `project_overview/02_architecture.md`): dependency-free CSS in
  `frontend/src/index.css` (design tokens, system font, message bubbles, sticky
  input bar, loading + error states, light/dark, responsive). Any spec that
  touches the UI (starting with M1) must include a styling step, list
  `frontend/src/index.css`, and carry a visual acceptance criterion. A page that
  renders as unstyled browser defaults is not "done".
- The frontend must **render assistant replies as Markdown**, not print the raw
  string. Assistant turns go through `react-markdown` + `remark-gfm` (the one
  allowed npm-dependency exception to the "dependency-free" CSS rule), styled per
  "Assistant messages are Markdown (render, don't dump)" in
  `project_overview/02_architecture.md`; **user** turns stay plain text and raw
  HTML passthrough stays **off**. Any UI-touching spec (starting M1, and every
  M4 skill) must include a Markdown-render step, list `react-markdown` +
  `remark-gfm` in the files/deps to touch, and carry an acceptance criterion that
  a reply with a heading, a list, and a code block renders as *formatted* output.
  A bubble showing literal `**`, `#`, or `---`, or lists with no indentation, is
  not "done".
- The backend must fail loud-but-clean too: `/chat` wraps the model call and, on
  an upstream error (bad slug, timeout, 4xx/5xx from OpenRouter), returns an
  `HTTPException` (e.g. `502` with a JSON `detail`), never an unhandled `500`. An
  unhandled `500` gets **no CORS headers**, so the browser blocks it and the UI
  shows only a generic "Failed to fetch" - the try/catch above can't surface a
  useful message. Return the clean status so the frontend can display the reason.
- Every feature's Test plan must include at least one **real** end-to-end smoke
  (live `POST /chat` -> HTTP 200 with a non-empty reply) against the configured
  services, not only mocked/`mongomock` checks. Once routing (M2) exists, the
  smoke must send a message that routes to a **mid or strong** tier (not just a
  trivial cheap-tier "hi"), so a broken non-cheap model slug is caught in QA
  rather than by the user.
