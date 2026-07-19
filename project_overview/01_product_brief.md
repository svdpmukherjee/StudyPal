# Product Brief: StudyPal

## The pitch (one sentence)

StudyPal is a chat study buddy that helps a student learn a topic and
**remembers what they struggle with**, so every session picks up where the last
one left off.

## Who it is for

One learner, one screen, one chat box. No login, no classes, no dashboards. A
student types what they are studying, asks questions, and StudyPal explains,
quizzes, and quietly tracks their weak spots.

## The one job

Make the learner feel *known*. On day two, StudyPal already knows they were
shaky on "recursion" and offers to revisit it. That single moment is the whole
demo, and it is the same "it remembers me" moment from the memory video.

## Non-goals (say these out loud in class)

- Not a full LMS. No grades, no accounts, no multi-user.
- No vector database. We store facts as plain MongoDB documents and *say* "in
  production this line becomes a vector search + RAG."
- Not production-hardened. It is a teaching artifact.

## Modules (each is one spec, built one at a time)

| ID | Module | What it does | Agentic concept it showcases |
|----|--------|--------------|------------------------------|
| M1 | Chat core | React chat <-> FastAPI `/chat` <-> OpenRouter <-> reply, save messages | spec-driven build, episodic memory |
| M2 | Model routing | Pick a cheap or strong OpenRouter model by task complexity | the "harness" controlling the LLM |
| M3 | Memory | Store durable facts about the learner, load them on start | semantic memory + recall |
| M4 | Skills | Reusable moves: `explain-simply`, `quiz-me` | procedural memory (skill files) |
| M5 | Summarizer agent | Distill recent chats into profile facts | subagent delegation |
| M6 | Eval | Score answer quality with an LLM-as-judge | evaluation loop |

## Demo scope (1 hour)

- **Pre-built before class:** M1 running (chat skeleton that echoes or does a
  single model call), plus this `project_overview/`. Removes all install pain.
- **Built live in class:** M3 (memory) as the hero slice, plus one skill (M4)
  and one subagent (M5). These touch spec, CLAUDE.md, skills, subagents, and
  memory in a single vertical.
- **Mention only / stretch:** M2 full routing and M6 eval, if time allows.

## Data StudyPal keeps (plain language)

- **Chat log** = every message with a timestamp (episodic memory).
- **Learner profile** = short list of durable facts, e.g. "studying algorithms",
  "weak on recursion", "prefers short answers" (semantic memory).
