---
worth: later
where: skills/lem/harness/claude-code.md:mark-waiting
added: 2026-11-23
---
# A session's waiting mark in the sidebar goes back to active when its turn ends

`prompts/session.md` tells a task's session to mark itself as waiting for the owner (`mark-waiting`)
when it asks him something. Status hooks outside Lem, the owner's and agterm's own adapter, set the
session `active` or `completed` at the end of its turn, so a session that asks its question in the
terminal (the first-line check, a fixed choice) shows a working session in agterm's sidebar while it
waits for him. Only the board's "Waits for you" and his Inbox say otherwise. Seen in
one-home-folder-for-lem on 2026-11-23: `blocked` at 11:49:52Z, `active` from the Stop hooks at
11:49:57Z.

The half of a question on a page of `lem-ask` was fixed on 2026-11-24: the plugin registers
`lem ask hook-stop`, which sets the mark again while the page is open.

What is left, for the terminal question: a `lem` command that sets the mark, notes the wait in the
task's folder and keeps the mark for any question until he answers; or the board server setting the
mark again for each task with a row in "Waits for you". How many waits are terminal questions was
not measured.
