---
worth: later
where: skills/lem/harness/claude-code/plan-talk.md
added: 2026-11-22
---
# The plan talk's session opens with no --plugin-dir, so a clone of Lem loaded only by --plugin-dir has no lem in it

With no Lem installed, lem session open gives the task's session --plugin-dir with the clone's folder (session.py:plugin_dir), but the lead opens the pair with claude --model "MODEL" --effort "EFFORT" "Read BRIEF and follow it." and no --plugin-dir; the defender's step 2, lem project --repo WORKTREE tasks (prompts/defender.md), finds no lem on that session's PATH on the base, and with this change the defender stops one step earlier, at the first line of talk-brief.md. Read in the harness text and session.py; no agterm session was started to show it.

Seen outside the change by review round 1 of task brief-reads-installed-lem (2026-11-22); the base commit has it.
