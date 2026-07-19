# Concept Map: the double helix

This is your best slide. Each row is one idea from the memory / harness video,
shown three ways: the concept, how Claude Code embodies it while we build, and
how StudyPal embodies it at runtime. Students learn every idea twice.

| Video concept | Build-time (Claude Code steering us) | Runtime (inside StudyPal) |
|---------------|--------------------------------------|---------------------------|
| System prompt / role | `CLAUDE.md` (how the agent behaves here) | the chatbot's system prompt |
| Procedural memory (skill.md) | `.claude/skills/` | `explain-simply`, `quiz-me` skills |
| Semantic memory (durable facts) | `context/PROJECT.md`, `DECISIONS.md` | learner `profile` in MongoDB |
| Episodic memory (dated events) | `context/WORKLOG.md` | `messages` collection |
| Working memory / context RAM | what the agent reads at session start | context built per `/chat` call |
| Subagent (summarizer) | `.claude/agents/` (summarizer, evaluator) | summarizer distills chats to facts |
| Harness / loop control | `CLAUDE.md` rules + specs + commands | model router + `/chat` flow |
| Eval (LLM as judge) | `/code-review`, tests, an evaluator agent | M6 scores answer quality |
| Consolidation gate | "update `context/` at session end" rule | summarize after N new messages |

## Say this to the class

> "The tool you are using to build the app is itself a memory-augmented agent
> harness. So while you learn to *drive* Claude Code, you are also looking at a
> live diagram of the exact system you are *building*."

## The two levels, kept separate on purpose

- **Build-time memory** helps *Claude* remember the project between coding
  sessions. It is `context/` + `CLAUDE.md`.
- **Runtime memory** helps *StudyPal* remember the *learner* between chats. It is
  MongoDB.

They rhyme, but they are different systems with different owners. Draw the line
clearly or students will conflate them.

## The build-time loop (LLM Ops, lightweight)

We will not stand up Langfuse in one hour. But we name the loop so students know
where it goes:

1. Build a module from its spec.
2. **Verify** it works (the `verify` habit, or a quick eval agent).
3. If it fails, diagnose and fix; if it passes, move to the next module.
4. Log the outcome in `context/WORKLOG.md`.

That is the trace -> eval -> diagnose -> gate -> release loop from the video,
shrunk to fit a classroom.
