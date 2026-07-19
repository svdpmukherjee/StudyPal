---
description: Interview me one question at a time, then write the project_overview/ docs (product brief, architecture, repo map, concept map, build pipeline) for my review.
argument-hint: (optional) one line about the project, e.g. "a habit-tracker CLI"
---

# Interview me to build `project_overview/`

`project_overview/` is the **intent** of the project: what we are building and
why, written before any code, so the Feature Loop in `CLAUDE.md` has something to
plan against. This command fills it by **interviewing me**, then writing the
five docs from my answers. Use it when the folder is empty or stub, or when I
want to rewrite the intent from scratch.

Project (if I gave one on the command line): $ARGUMENTS

## How to run the interview (follow these exactly)

1. **One question at a time.** Ask a single question, wait for my answer, then
   ask the next. Never dump a list of questions at once; that is bewildering.
2. **Always recommend an answer.** With each question, give your own suggested
   answer and a one-line reason, so I can just say "yes" or correct you. I am
   often the person who does not yet know what to write, so lead, don't quiz.
3. **Look up facts, ask only decisions.** If something can be found by exploring
   the repo (existing files, stack already chosen, folder names, dependencies),
   look it up rather than asking me. Put only the genuine **decisions** to me.
4. **Walk the agenda in order** (below), resolving dependencies as you go: an
   answer that reshapes an earlier one, revisit it. Keep a running outline of
   what each of the five docs will contain.
5. **Do not write any file until CHECKPOINT.** Interview first, write second.
6. **No em-dashes** in anything you write. Use commas, colons, parentheses, or a
   new sentence.

## The agenda (this is the finish line)

The interview is **done when every slot below has an answer**, not when I run out
of patience. That is the explicit end that a generic grilling session lacks:
work the list, and when the last slot is filled you are finished. Skip a slot
only if I say it does not apply, and note that in the outline.

**Doc 1: `01_product_brief.md`** (what it is, for whom)
- One-sentence pitch.
- Who it is for (the one user, the one screen).
- The one job / the single moment that is the whole point.
- Non-goals (what we deliberately will not build).
- Module list: a table of buildable units (M1, M2, ...), each a one-line "what
  it does". These become the `/feature` IDs, so aim for 4 to 8 small modules
  built one at a time.

**Doc 2: `02_architecture.md`** (the moving parts)
- Tech stack (frontend, backend, store, external services / models).
- A moving-parts diagram: write it as a **Mermaid** `flowchart` from the answers.
- Request lifecycle: numbered steps for what happens on one core action.
- Data model, kept as small as honestly possible.
- Config and secrets (which keys, where they live, what is gitignored).
- Key conventions and gotchas: any "always do X" rules and known traps for this
  stack (error handling, TLS, CORS, and so on). Ask me for the ones I know; add
  the obvious ones for the stack.
- If there is a UI: carry over the **visual baseline** and the **"Assistant
  messages are Markdown (render, don't dump)"** section from this repo's current
  `02_architecture.md` if they apply, adapted to the new UI.

**Doc 3: `03_repo_map.md`** (every folder, what it holds)
- A table of top-level paths with: what lives there, and when it gets filled.
- If the project has a build-time layer (the `.claude/` + `context/` agent
  scaffolding) and a runtime layer (the app code), keep them clearly separated,
  as this repo's map does.

**Doc 4: `04_concept_map.md`** (the ideas this project teaches or leans on)
- Optional but recommended if the project is a teaching or portfolio artifact:
  a table mapping each core idea to where it shows up. If the project is purely
  practical with no teaching angle, ask me whether to skip this doc and record
  the choice.

**Doc 5: `05_build_pipeline.md`** (the build order)
- A step-by-step order for building the modules from Doc 1, one concept per step.
  Each step: Goal, Folder(s) touched, Do, and (if relevant) what it teaches.
- This is the spine the `/feature` loop follows, so the order must respect
  dependencies (nothing built before what it needs).

## CHECKPOINT (spec approval, human gate)

When every slot is filled, **stop** and show me a compact outline: the five doc
titles, each with its filled bullet points, plus the module list and the build
order. Ask for "approved". Do not write files until I approve. If I request
changes, adjust the outline and ask again. This mirrors the CHECKPOINT
discipline in `CLAUDE.md`: a human approves before anything is committed.

## Write (only after approval)

1. Write the five files into `project_overview/` using the exact names
   `01_product_brief.md` through `05_build_pipeline.md`, matching the structure
   and plain, concrete voice of this repo's existing docs.
2. Seed `context/PROJECT.md` with the module list from Doc 1, every module status
   set to `TODO`, so `/feature next` can pick the first one. Create
   `context/CURRENT_TASK.md` (empty template), `context/WORKLOG.md`, and
   `context/DECISIONS.md` if they do not exist.
3. Do **not** write any app code, specs, or skills. This command produces intent
   only. Building is the `/feature` loop's job.

## After writing

Tell me: the files written, a one-line summary of the product and the first
module, and the next step: "Review `project_overview/`. When it reads right, run
`/feature M1` (or `/feature next`) in a new session to start building."
