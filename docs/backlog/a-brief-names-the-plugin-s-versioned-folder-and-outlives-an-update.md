---
worth: yes
where: skills/lem/scripts/session.py:brief_text
added: 2026-11-21
---
# A brief and a task's session.md name the plugin's versioned folder

A brief's first line is `Read SKILL_DIR/prompts/NAME.md and follow it.`, with `SKILL_DIR` written
out as an absolute path (`skills/lem/stages/new.md`, the lead's brief and the fast track's brief;
`skills/lem/stages/plan.md`, the talk's brief). `brief_text` in `session.py` writes the first line of
`session.md` the same way, with `SKILL` the folder of the `session.py` that runs. For an installed
plugin that path holds its version, so a file written by one Lem sends a later agent to that Lem.

Two runs show it:

- In `owner-task-order-stays` (2026-11-21) the plugin went from 0.1.0 to 0.1.1 while the task ran.
  The task's `session.md` then named `.../plugins/cache/lem/lem/0.1.1/skills/lem/prompts/session.md`,
  while its `brief.md` and `talk-brief.md` still named `.../plugins/cache/lem/lem/0.1.0/...`. A lead
  or a defender started from those briefs after the update reads the texts of 0.1.0, beside a
  session and scripts of 0.1.1.
- In `owner-order-open-defects` (2026-11-21), `lem session open` wrote `session.md` at 17:20 UTC
  naming the folder `0.1.1`, while the `lem` on the new session's `PATH` was the folder `0.1.6`
  (`which -a lem`): the session that opened the task ran the older Lem. The two folders differ in
  `prompts/session.md`, `SKILL.md` and most stage files (`diff -rq`).

On 2026-11-22 the plugin cache held every version from 0.1.0 to 0.2.0, so the old texts were still
there to read; nothing says the cache keeps them.

Settled: a task reads the Lem that is installed now, never the one that wrote its files. The
owner's ruling "No word and no form of a Lem before is kept" covers it: asked whether "the reading
of an open task's older records" should go, he said "yes, remove". The outcome: no brief and no
`session.md` names a versioned folder of the plugin, and an agent started from either after an
update reads the texts of the installed Lem, beside its scripts. How the path is found (the `lem`
command on the agent's `PATH`, which the plugin puts there, or another way) is the lead's to choose.

Surfaced in the tasks `owner-task-order-stays` and `owner-order-open-defects` (2026-11-21); two
items joined on 2026-11-22.
