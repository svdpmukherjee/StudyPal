# StudyPal

A demo repo for **building an app with Claude Code, systematically**.

StudyPal is a small chat "study buddy" (React + FastAPI + MongoDB, models via
OpenRouter). But the app is only the excuse. The real lesson is the **workflow**:
how you drive Claude Code as an orchestrator that plans, builds, and tests one
feature at a time, with a human approving at every gate.

By the end you will have built a working app **and** learned a repeatable,
professional agentic-development loop you can reuse on any project.

---

## 1. What you need before you start

Create these two accounts and grab two values. Both have free tiers.

| You need                      | Where to get it                                                                   | What you get                                       |
| ----------------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------- |
| **OpenRouter API key**        | [openrouter.ai](https://openrouter.ai) → Keys                                     | `sk-or-...`, lets the app call LLMs                |
| **MongoDB connection string** | Local Mongo, **or** a free [MongoDB Atlas](https://www.mongodb.com/atlas) cluster | `mongodb://localhost:27017` or `mongodb+srv://...` |

Also install:

- **Claude Code** (the CLI or VS Code extension) and sign in.
- **Python 3.12+** and **Node.js 22+**.
- **MongoDB** running locally, _or_ an Atlas cluster (either works).

You will paste the two values into `backend/.env` later (Step 4). Never commit
that file; it is gitignored.

---

## 2. How Claude "sees" this repo

When you open a Claude Code session inside this folder, Claude **automatically
loads some files into its working memory** before you type anything:

- **`CLAUDE.md`** at the repo root. This is the project constitution: it tells
  Claude it is the _orchestrator_, that it builds one feature per session, and it
  defines the **Feature Development Loop** (plan → approve → build → test →
  approve → close). Read it once; it is the single most important file here.
- **Everything under `.claude/`**: your custom commands, your subagents, and
  your settings.

You do not have to point Claude at these. They are context it always has.

---

## 3. What the repo contains

Two layers live side by side. Keeping them apart is the whole trick.

### Build-time layer (steers the coding agent)

| Path                | What it holds                                                                        |
| ------------------- | ------------------------------------------------------------------------------------ |
| `CLAUDE.md`         | The rules Claude follows here (roles, the Feature Loop, guardrails).                 |
| `.claude/commands/` | **Custom slash commands** (see below).                                               |
| `.claude/agents/`   | **Subagents**: task-specific helpers Claude calls during a job.                      |
| `.claude/specs/`    | One spec file per feature. The Planner writes these; created live as you build.      |
| `context/`          | **Session memory** so a new session can continue where the last stopped (see below). |
| `project_overview/` | The **intent** of the app: what we are building and why, written before any code.    |

**`.claude/commands/`** holds custom slash commands, each for a definite purpose:

- **`/interview-me`** interviews you one question at a time, then writes the five
  `project_overview/` docs for you. Use it only if you cannot write the project
  intent yourself; it is optional.
- **`/feature`** runs the full build loop for one module, e.g. `/feature M1`.

**`.claude/agents/`** holds three subagents. They never talk to each other
directly; they hand off through **files**:

- **`planner.md`** (the Architect): turns one module into a written spec with a
  numbered build plan. Writes a spec, then stops.
- **`developer.md`** (the Builder): implements that approved spec into
  `backend/` and `frontend/` code.
- **`tester.md`** (QA): runs the spec's test plan and reports pass/fail.

### Runtime layer (the actual app)

| Path        | What it holds                                                                            |
| ----------- | ---------------------------------------------------------------------------------------- |
| `backend/`  | FastAPI app, model router, MongoDB access. `requirements.txt`, `.env.example` live here. |
| `frontend/` | React (Vite) chat UI.                                                                    |
| `database/` | Notes / helpers for the data store (kept minimal).                                       |

Empty folders (like `.claude/specs/`) stay empty until the step that fills them.
That is the syllabus, not a gap.

---

## 4. First-time setup

```bash
git clone <this-repo-url> StudyPal
cd StudyPal

# Backend: create your secrets file
cp backend/.env.example backend/.env
```

Open `backend/.env` and fill in your two values:

```ini
OPENROUTER_API_KEY=sk-or-...            # from openrouter.ai
MONGODB_URI=mongodb://localhost:27017   # or your Atlas mongodb+srv string
MONGODB_DB=studypal
```

---

## 5. The core workflow: one session per feature

The golden rule from `CLAUDE.md`: **one session builds one feature.**

### Step 1 - Make sure the intent exists

The Feature Loop plans against `project_overview/`. This repo already ships a
populated `project_overview/` (product brief, architecture, repo map, concept
map, build pipeline), with a module list:

| ID  | Module           | What it does                                                     |
| --- | ---------------- | ---------------------------------------------------------------- |
| M1  | Chat core        | React chat ↔ FastAPI `/chat` ↔ OpenRouter ↔ reply, save messages |
| M2  | Model routing    | Pick a cheap or strong model by task complexity                  |
| M3  | Memory           | Store durable facts about the learner, load them on start        |
| M4  | Skills           | Reusable moves: `explain-simply`, `quiz-me`                      |
| M5  | Summarizer agent | Distill recent chats into profile facts                          |
| M6  | Eval             | Score answer quality with an LLM-as-judge                        |

> If you were starting a _fresh_ project with an empty `project_overview/`, you
> would run **`/interview-me`** first and let Claude write these docs for you.

### Step 2 - Open a session and name it

In VS Code, open the built-in terminal **inside the StudyPal folder** and start
Claude Code:

```bash
cd StudyPal
claude
```

**Rename the session** to the feature you are about to build, for example
`M1-chat-core`. Naming keeps your history readable: one clearly-named session per
feature.

### Step 3 - Run the feature loop

```
/feature M1
```

(or `/feature next` to let Claude pick the first unbuilt module).

Claude now runs the **Feature Development Loop** from `CLAUDE.md`, one phase at a
time. First it makes sure the `context/` files exist. These are its session
memory:

| File                      | Purpose                                                          |
| ------------------------- | ---------------------------------------------------------------- |
| `context/PROJECT.md`      | The module list (M1..M6) with a status per module (TODO / DONE). |
| `context/CURRENT_TASK.md` | The one task in progress plus its acceptance criteria.           |
| `context/WORKLOG.md`      | A dated log: what got done each session, one line each.          |
| `context/DECISIONS.md`    | Why we chose X over Y (a lightweight decision record).           |

Then it walks the phases:

1. **Orient** - reads `context/` and the module's intent, states where we are.
2. **Plan** - calls the **planner** subagent, which writes a spec to
   `.claude/specs/M1_chat_core.md` (user story, acceptance criteria, numbered
   build plan, files to touch, test plan).
   → **CHECKPOINT 1:** Claude shows you the spec and **stops**. Read it. Reply
   **"approved"** (or ask for changes).
3. **Build** - calls the **developer** subagent to implement the approved spec
   into `backend/` and `frontend/`.
4. **Test** - calls the **tester** subagent to run the spec's test plan. If it
   fails, Claude routes the failures back to the developer once, then re-tests.
   → **CHECKPOINT 2:** Claude reports what was built and the test result, then
   **stops** for your feature approval.

**Before you approve at CHECKPOINT 2, run the app yourself** (Step 6).

### Step 4 - Close and move on

Once you approve, Claude appends a line to `context/WORKLOG.md`, marks the module
DONE in `context/PROJECT.md`, and clears `context/CURRENT_TASK.md`.

Then: **open a new session**, rename it (e.g. `M2-model-routing`), and run
`/feature M2`. Repeat down the module list.

---

## 6. Running the app (first time needs two terminals)

Open **two** terminals in VS Code.

**Terminal 1 - backend:**

```bash
cd backend
python -m venv venv          # first time only
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Terminal 2 - frontend:**

```bash
cd frontend
npm install                  # first time only
npm run dev
```

Now open **http://localhost:5173** in your browser and try the chat. If it
responds, the feature works. Go back to Claude and reply **"approved"** at
CHECKPOINT 2.

---

## 7. Quick reference

```
/interview-me      # (optional) build project_overview/ by interview
/feature M1        # build one module through the full loop
/feature next      # build the next TODO module

# run the app
cd backend  && source venv/bin/activate && uvicorn main:app --reload --port 8000
cd frontend && npm run dev
# open http://localhost:5173
```

**The rhythm:** new session → rename it → `/feature Mx` → approve the spec → let
it build and test → run the app → approve the feature → new session for the next
one.

That agentic loop, not the chatbot, is what the project is demoing.
