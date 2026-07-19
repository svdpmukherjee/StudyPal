# Project Overview

This folder is the **intent** of the project. It contains no code. It is what a
product owner hands to a development team before a single line is written.

In this class, the "development team" is a set of Claude agents steered by
`CLAUDE.md`. These documents are what those agents (and the students driving
them) read first to understand _what_ we are building and _why_, so they can
decide _how_.

## The one idea to teach

> You invest in the **context layer** (specs, memory, skills, agent
> instructions). The agent produces the **code**.

The app itself does not matter. The _way we build it_ is the lesson.

## Read in this order

1. `01_product_brief.md` - what StudyPal is, who it is for, the modules.
2. `02_architecture.md` - the moving parts and how a request flows.
3. `03_repo_map.md` - every folder, and which agentic concept it teaches.
4. `04_concept_map.md` - how the video's memory concepts map to Claude Code
   features map to StudyPal features (the "double helix").
5. `05_build_pipeline.md` - the step-by-step teaching order, folder by folder,
   so students are never overwhelmed.

## Golden rule for the class

Nothing outside `project_overview/` exists yet. We build it together, one folder
per step, in the order given by `05_build_pipeline.md`. Empty folders are not a
mistake. They are the syllabus.
