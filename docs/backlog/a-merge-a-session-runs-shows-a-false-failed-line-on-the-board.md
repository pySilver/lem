---
worth: later
where: skills/lem/scripts/serve.py:forge_once
added: 2026-11-22
---
# A merge a session runs shows a false failed line on the board

The board server's look at GitHub (`forge_once`) runs `lem land merged SLUG` for each pull request
GitHub calls merged. It skips a task whose merge the server itself runs (`NOTES.running`), since that
merge's process holds the task's step lock and `merged` would be refused. A merge that a task's
session runs with `lem land merge`, in a process of its own, is not in `NOTES.running`. When the
look comes between GitHub's merge and the end of that step, `merged` meets the held step lock, fails,
and the status bar shows "`lem land merged SLUG` failed after GitHub called pull request N merged"
until the next try, a few minutes later (`DUTY_RETRY`). Read in the code, not run; seen by the lead
of `merge-leaves-board-lock` (2026-11-22). A fix may skip a task whose step lock another process
holds, which needs a way to ask the lock without taking it.
