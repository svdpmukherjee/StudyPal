# Spec M4: Skills

## User story
As a learner, I want reusable tutoring "moves" I can trigger on a chat turn —
"Explain simply" and "Quiz me" — so that with one tap StudyPal switches into a
plain-language explainer or a short quiz-maker, instead of me having to hand-craft
the right prompt each time.

## Acceptance criteria
- [ ] Procedural memory is visible in the repo as **skill prompt files** under
      `backend/skills/`: `explain-simply.md` and `quiz-me.md`. Each is a small
      plain-text/Markdown prompt that instructs the tutor for that move and (per
      `02_architecture.md` line ~221) asks for **chat-friendly** Markdown (short
      paragraphs, modest heading levels, lists over walls of text). No code lives
      in these files — they are prompts.
- [ ] `backend/skills.py` loads a skill by name from `backend/skills/` against a
      fixed **allowlist** (`explain-simply`, `quiz-me`) so an unknown or path-like
      name (e.g. `../secrets`) can never read an arbitrary file: `load_skill(name)`
      returns the prompt text for an allowed name and raises/returns cleanly for
      anything else. It also exposes each skill's **suggested tier** (`explain-simply`
      → mid, `quiz-me` → strong).
- [ ] `POST /chat` accepts an optional `skill` field. With **no** `skill`, behavior
      is today's plain chat and the response is unchanged. With a valid `skill`, the
      backend prepends/injects that skill's prompt into the system prompt for that
      turn; an **invalid** `skill` returns `HTTPException(400)` (not a 500, not a
      silent ignore). Response stays backward-compatible `{ reply, tier, model }`
      plus an added `skill` field (echoing the applied skill, or `null`).
- [ ] M2 routing and M3 memory still work on a skill turn: the turn still routes to
      a tier (a `quiz-me` turn routes to **strong**, an `explain-simply` turn to
      **mid**) via the skill's suggested tier, and the learner's `profile` facts are
      still injected into the system prompt (memory block from M3 remains present).
      `router.py` model-routing logic is **not** modified.
- [ ] Frontend gives the user two clearly-labelled skill triggers ("Explain simply",
      "Quiz me") near the input bar; tapping one sends the current message text with
      that `skill`, disables while a request is in flight, and shows the applied
      skill on the resulting assistant bubble. Failures still surface via the
      existing `try/catch` error bubble (never a silent blank).
- [ ] Visual + Markdown baseline holds: the skill buttons use existing design tokens
      (system font, `--accent`, spacing/radius), read correctly in light AND dark via
      `prefers-color-scheme`, cause no horizontal scroll at 360px, and have clear
      `:hover`/`:focus-visible`/`:disabled` states. A skill reply containing a
      heading, a numbered list, inline `code`, and a fenced code block renders as
      **formatted** Markdown (real bullets, real code box) with no literal `**`/`#`/
      `---`; user turns stay plain text; `rehype-raw` stays OFF.

## Build plan (numbered, small steps)
1. **backend/skills/explain-simply.md (new).** A short prompt: "Re-explain the
   learner's topic in the simplest possible terms — short sentences, everyday
   analogies, no jargon (or define it). Use chat-friendly Markdown: short
   paragraphs, at most a small heading, a short bullet list if it helps. End with
   a one-line check-for-understanding question."
2. **backend/skills/quiz-me.md (new).** A short prompt: "Generate a short quiz (3–5
   questions) on the learner's topic, mixing recall and application; gently target
   their known weak spots if any are provided. Use chat-friendly Markdown: a small
   heading, a numbered list of questions, and put any answer key in a fenced code
   block or below a `---` divider so it's easy to skip."
3. **backend/skills.py (new).** Define `ALLOWED_SKILLS = {"explain-simply": "mid",
   "quiz-me": "strong"}`. `load_skill(name) -> str`: reject names not in the
   allowlist (raise `ValueError`), otherwise read `backend/skills/<name>.md` from a
   path built off this file's directory (no user-controlled path segments) and
   return its text. `skill_tier(name) -> str` returns the suggested tier. Keep it
   tiny and dependency-free (stdlib `pathlib`).
4. **backend/main.py — extend `/chat`.** Add `skill: str | None = None` to
   `ChatRequest` and `skill: str | None = None` to `ChatResponse`. In `chat()`:
   if `req.skill` is set, validate via `skills.ALLOWED_SKILLS` → `HTTPException(400)`
   on unknown; choose `tier = skills.skill_tier(req.skill)` (skill drives the tier)
   instead of `route(req.message)`; and after the existing M3 memory block, append
   the loaded skill prompt to `system_prompt` (e.g. a "For this reply, apply this
   tutoring move:\n<skill text>" block). With no skill, keep today's `route(...)`
   and plain system prompt exactly. Save/return as today, adding
   `"skill": req.skill` to the response. `router.py` is untouched.
5. **frontend/src/App.jsx — skill triggers.** Add two buttons ("Explain simply",
   "Quiz me") near the input bar. Refactor `sendMessage` to accept an optional
   `skill` argument and include it in the POST body when present; the plain Send
   button calls it with no skill. Carry the returned `skill` onto the assistant
   message object and show it on the bubble (e.g. a small "via explain-simply" tag
   next to the existing `[tier · model]`). Disable the skill buttons while
   `thinking` or when the input is empty. Keep Markdown rendering and the error
   bubble flow unchanged.
6. **frontend/src/index.css (styling step).** Style `.skill-bar` and
   `.skill-btn` (compact, `--accent`-outlined/tinted pill buttons using token
   radius/spacing, wrapping with no 360px overflow) with `:hover`/`:focus-visible`/
   `:disabled` states, and a muted `.msg-skill` tag on the assistant bubble — all
   theming via the existing light/dark tokens, no new hardcoded colors and no new
   CSS dependency.

## Files to touch
- `backend/skills/explain-simply.md` (new skill prompt file — procedural memory)
- `backend/skills/quiz-me.md` (new skill prompt file — procedural memory)
- `backend/skills.py` (new — allowlisted loader + suggested-tier lookup)
- `backend/main.py` (`ChatRequest`/`ChatResponse` `skill` field; validate + inject skill prompt; skill drives tier; keep M2 route + M3 memory)
- `frontend/src/App.jsx` (skill buttons, `sendMessage(skill)`, show applied skill on bubble)
- `frontend/src/index.css` (styling step — `.skill-bar`/`.skill-btn`/`.msg-skill`, theme-aware)

## Test plan
- **AC1/AC2 (skill loader, unit):** `load_skill("explain-simply")` and
  `load_skill("quiz-me")` return non-empty text; `skill_tier("quiz-me") == "strong"`
  and `skill_tier("explain-simply") == "mid"`; `load_skill("nope")` and
  `load_skill("../db")` raise `ValueError` (allowlist blocks unknown/path-like names).
- **AC3 (invalid skill route, smoke):** with the backend up, `POST /chat`
  `{"message":"photosynthesis","skill":"bogus"}` → HTTP 400 with a JSON `detail`
  (not 500, not a plain 200). `POST /chat` with no `skill` → 200 and response shape
  matches today plus `skill: null`.
- **AC3/AC4 (REAL end-to-end skill smoke, mid or strong):** seed a fact via
  `POST /profile {"fact":"weak on recursion"}`, then a **live** `POST /chat`
  `{"message":"binary search trees","skill":"quiz-me"}`. Assert HTTP 200, non-empty
  `reply`, `tier == "strong"` (skill drove routing to a non-cheap slug, so a broken
  strong slug is caught here in QA), and `skill == "quiz-me"`. This exercises the
  strong model end-to-end.
- **AC3/AC4 (skill output differs from plain):** live `POST /chat` for the same
  topic with **no** skill vs with `skill:"explain-simply"` (assert `tier=="mid"`),
  and confirm the two replies are materially different (e.g. the `explain-simply`
  reply is simpler/shorter or structured as an explanation), proving the skill
  prompt actually reached the model rather than being a no-op. Confirm the M3 memory
  block is still applied on a skill turn (the seeded weak spot can surface in a
  `quiz-me` reply).
- **AC5/AC6 (frontend + visual, manual/browser):** type a topic, tap "Quiz me" and
  "Explain simply"; confirm each sends the skill, the assistant bubble shows the
  applied-skill tag alongside `[tier · model]`, and a reply with heading + numbered
  list + inline `code` + fenced block renders as formatted Markdown (no literal
  `**`/`#`/`---`); user turns stay plain. Buttons disable while thinking and when
  input is empty. Toggle OS dark mode (token swap), resize to 360px (no horizontal
  scroll), check `:focus-visible`/`:disabled` states. Grep `index.css` for
  `.skill-btn` and confirm it uses theme tokens (`--accent`), not hardcoded colors.

## Out of scope
- **Automatic** skill selection (the backend/LLM deciding which move to apply) —
  M4 is user-triggered only; intent-based auto-routing to a skill is not built.
- New routing tiers or changes to `router.py`'s keyword/length logic — the skill
  merely *chooses* an existing tier for that turn.
- More skills beyond `explain-simply` and `quiz-me`; per-skill parameters; skill
  chaining or history of which skill produced which turn.
- Grading/scoring the learner's quiz answers — that's the M6 eval loop.
- Writing distilled facts back to `profile` from a skill turn — that's the M5
  summarizer subagent.
