# Build Pipeline: the step-by-step teaching order

One concept per step, one folder per step. Students never touch a folder before
its step. This is the spine of the class.

Each step lists: **Goal**, **Folder**, **Do**, **Students learn**, **Time**.

---

## Step 1 - Read the intent

- **Goal:** everyone understands what we are building and why.
- **Folder:** `project_overview/` (already done).
- **Do:** skim `01_product_brief.md` and the diagram in `02_architecture.md`.
- **Students learn:** real work starts from intent, not from code.

## Step 2 - Write the constitution

- **Goal:** give the agent its rules of engagement.
- **Folder:** `CLAUDE.md`.
- **Do:** write project summary, stack, conventions, and the key rule: _"At
  session start, read `context/`. At session end, update it."_ Point the agent
  at `project_overview/` and `.claude/specs/`.
- **Students learn:** `CLAUDE.md` is the steering wheel; every later step obeys
  it.

## Step 3 - Set up session memory

- **Goal:** make sessions resumable.
- **Folder:** `context/`.
- **Do:** create `PROJECT.md` (modules M1..M6 with status = TODO),
  `CURRENT_TASK.md` (empty template), `WORKLOG.md`, `DECISIONS.md`.
- **Students learn:** this is how Claude "picks up where it left off." Show the
  parallel to episodic memory.

## Step 4 - Write the first spec

- **Goal:** turn one module into a buildable spec.
- **Folder:** `.claude/specs/`.
- **Do:** write `M1_chat_core.md`: user story, acceptance criteria, the `/chat`
  contract, done-checklist. Keep it one page.
- **Students learn:** spec-driven, modular. One spec = one unit of work.

## Step 5 - Build Module 1 from its spec

- **Goal:** watch the agent turn a spec into working code.
- **Folder:** `backend/` + `frontend/`.
- **Do:** ask the agent to implement `M1_chat_core.md`. It writes the FastAPI
  route, Mongo save, and the React chat box. Run it. (If pre-built, re-derive
  one piece live so they see it happen.)
- **Students learn:** the agent implements _from the spec_, not from vibes.

## Step 6 - Add a skill

- **Goal:** capture a reusable move.
- **Folder:** `.claude/skills/`.
- **Do:** add a skill like `quiz-me` (how StudyPal should generate a short quiz).
  Invoke it.
- **Students learn:** skills = procedural memory. Reusable, not one-off prompts.

## Step 7 - Add a subagent

- **Goal:** delegate a specialized job.
- **Folder:** `.claude/agents/`.
- **Do:** define a `summarizer` subagent that reads recent `messages` and writes
  learner facts to `profile`. Run it.
- **Students learn:** subagents = focused workers with their own instructions.

## Step 8 - Add memory handling (the hero slice)

- **Goal:** StudyPal remembers the learner.
- **Folder:** `backend/` (uses spec `M3_memory.md`).
- **Do:** load `profile` into the system prompt on each `/chat`; after the turn,
  let the summarizer update it. Reload the page as a "new session" and show it
  recall the learner. **This is the wow moment.**
- **Students learn:** semantic memory + recall, end to end.

## Step 9 - Add an evaluation

- **Goal:** know if an answer was any good.
- **Folder:** `.claude/agents/` (an `evaluator`) or a `/eval` command.
- **Do:** score one answer with an LLM-as-judge rubric (clear? correct?
  on-level?). Log the score.
- **Students learn:** the eval / LLM Ops loop, shrunk to one call.

## Step 10 - Close the session, then reopen

- **Goal:** prove continuity.
- **Folder:** `context/`.
- **Do:** update `WORKLOG.md` and `PROJECT.md` (mark modules done). Start a fresh
  Claude session; show it read `context/` and know exactly what is next.
- **Students learn:** this is what makes agentic work sustainable across days.

---

## Two rules that keep it calm

1. **One folder at a time.** Never open the next folder until its step.
2. **Spec before code, log after code.** Every build step is bracketed by a spec
   (Step 3 pattern) and a worklog update (Step 9 pattern).
