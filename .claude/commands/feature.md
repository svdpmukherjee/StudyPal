---
description: Run the full Feature Development Loop for one module (plan -> approve -> build -> test -> approve -> close).
argument-hint: <feature-id, e.g. M3, or "next">
---

Run the **Feature Development Loop** defined in `CLAUDE.md` for feature: $ARGUMENTS

Follow it exactly, phase by phase:

1. **Orient** - read `context/` and the module intent. If the argument is
   "next", pick the first TODO module in `context/PROJECT.md`.
2. **Plan** - call the `planner` subagent to write the spec, then STOP at
   CHECKPOINT 1 and wait for my approval of the spec.
3. **Build** - after I approve, call the `developer` subagent to implement the
   spec.
4. **Test** - call the `tester` subagent. If it fails, route the failures back
   to the `developer` once, then re-test.
5. STOP at CHECKPOINT 2 and wait for my feature approval.
6. **Close** - after I approve, update `context/WORKLOG.md` and
   `context/PROJECT.md`, clear `context/CURRENT_TASK.md`, and remind me to open a
   new session for the next feature.

Do not pass either checkpoint without my explicit approval. Build only this one
feature in this session.
