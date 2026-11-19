---
worth: later
where: skills/lem/harness/claude-code.md:open-task-session
added: 2026-11-19
---
# a companion session stops at the folder trust prompt

`## open-task-session` opens a companion with `claude ... "Read BRIEF and follow it."` in a
folder, and names the permission mode a new session gets. It says nothing about the folder trust
prompt that Claude Code shows before the first prompt in a folder it does not trust yet.

The run: on 2026-11-19 at 17:52Z the builder of task 3 of
`docs/plans/2026-11-19-landing-in-the-background.md` started `claude --plugin-dir WORKTREE` in a
clone at `.lem/state/tasks/landing-in-the-background/run/lem`. That folder is inside the trusted
checkout of this repository, but it is a git repository of its own, and Claude Code asked whether
to trust it. The session waited there and read no brief; the builder closed it.

Whether a task's worktree (`.lem/worktrees/SLUG`, a git worktree and not a repository of its own)
gets the same prompt was not checked. What it needs: that check in a real plan talk, and, when
the prompt comes, one sentence in `open-task-session` on what Lem does (wait for the owner's
answer in the companion, and say so to him in one line) and a row or a line where the owner can
trust the folder once.
