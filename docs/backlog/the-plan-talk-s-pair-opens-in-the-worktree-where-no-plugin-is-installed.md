---
worth: later
where: skills/lem/harness/claude-code.md
added: 2026-11-21
---
# The plan talk's pair opens in the worktree, where no plugin is installed

"The plan talk's pair" in `skills/lem/harness/claude-code.md` opens the defender's session with
`agtermctl session new ... --cwd WORKTREE`. The same file, under "What the owner does himself",
says that a task's session opens in the main checkout because "a session started in the worktree
itself has no plugin installed for the project and none of the folder's own Claude Code settings"
(lem-scratch, Claude Code 2.1.330, 2026-11-21). The two texts disagree: by the second, a defender
started with the first line runs without Lem's plugin and without the repository's settings.

The lead of `owner-task-order-stays` (2026-11-21) met it and opened the pair in the main checkout
instead, as its decision 8 says (`lem decisions list owner-task-order-stays`). The launch line
should say where the pair opens, and how the defender then reaches the worktree (by its path, as
a task's session does), so that the next lead does not decide it again.
