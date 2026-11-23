---
worth: later
where: skills/lem/harness/claude-code.md:mark-waiting
added: 2026-11-23
---
# A session's waiting mark in the sidebar goes back to active when its turn ends

`prompts/session.md` tells a task's session to mark itself as waiting for the owner (`mark-waiting`)
when it asks him something, and says that he sees it waits by that mark in agterm's sidebar. In
one-home-folder-for-lem on 2026-11-23, the session set agterm's status `blocked` at 11:49:52Z while
its second criteria page waited for him, and agterm's tree read `active` from 11:49:57Z, 5 seconds
later, at the end of the session's turn (tree `statusChangedAt` 1795434597.64). The page still waited.
So the sidebar showed a working session where one waited for the owner, and only the board's "Waits
for you" said otherwise.

The harness line of `mark-waiting` (`agtermctl session status blocked --blink --auto-reset`) still
says "Not run yet". Which part resets the status at the end of a turn (`--auto-reset`, or agterm's own
status from the agent's turn) was not read. Seen by the investigator of
waits-for-you-only-when-it-waits (its `outside.md`, 2026-11-23); the base commit has it.
