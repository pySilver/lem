---
worth: later
where: skills/lem/scripts/session.py:brief_text
added: 2026-11-21
---
# A task's session.md names the folder of the Lem that opened it, also when that Lem is older than the installed one

`brief_text` writes the first line of `session.md` as `Read SKILL/prompts/session.md and follow it.`,
with `SKILL` the folder of the `session.py` that runs, so the folder is that of the `lem` on the
opening session's `PATH`, with its version in the path.

In the task `owner-order-open-defects` (2026-11-21), `lem session open` wrote `session.md` at 17:20
UTC naming `.../plugins/cache/lem/lem/0.1.1/skills/lem/prompts/session.md`, while the `lem` on the
new session's `PATH` was the folder `0.1.6` (`which -a lem`). The session that opened the task ran
the older Lem and wrote its own folder into the new session's first message. The two folders differ
in `prompts/session.md`, `SKILL.md` and most stage files (`diff -rq`); that task's session saw the
mismatch and followed the texts of `0.1.6`. A later change of phase rewrote `session.md` with `0.1.6`.

The item "A brief names the plugin's versioned folder and outlives an update" is the same path read
after an update; here the folder is old from the first message.
