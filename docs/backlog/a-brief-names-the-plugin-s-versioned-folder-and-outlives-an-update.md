---
worth: later
where: skills/lem/stages/new.md
added: 2026-11-21
---
# A brief names the plugin's versioned folder and outlives an update

A brief's first line is `Read SKILL_DIR/prompts/NAME.md and follow it.`, with `SKILL_DIR` written
out as an absolute path (`skills/lem/stages/new.md`, step 6; `skills/lem/stages/plan.md`, the
talk's brief). For an installed plugin that path holds its version.

In `owner-task-order-stays` (2026-11-21) the plugin went from 0.1.0 to 0.1.1 while the task ran.
The task's `session.md` now names `.../plugins/cache/lem/lem/0.1.1/skills/lem/prompts/session.md`,
while its `brief.md` and `talk-brief.md` still name `.../plugins/cache/lem/lem/0.1.0/...`. A lead
or a defender started from those briefs after the update reads the texts of 0.1.0, beside a
session and scripts of 0.1.1. Both folders were still in the plugin cache that day.

Whether a task should finish on the Lem it started with, or read the current one, is open; today
the answer depends on which file a fresh agent starts from.
