---
worth: later
where: skills/lem/stages/start.md
added: 2026-11-16
---
# no long program of dependent branches on an integration branch

Every task of Lem starts from `branch.base` (`git worktree add -b BRANCH PATH BASE`,
`stages/start.md`) and ends as a pull request into it. A program of ten tasks in
which task 4 needs the code of task 3 therefore waits for task 3's pull request to merge before
task 4 can start. convertiser-server works another way today: a coordinator and about five
builders landed 67 branches in about 28 hours on an integration branch that is not the main
branch (`docs/plans/2026-11-15-three-touches/brief.md`, flow B, from that project's notes). The plan of the flow names this mode and leaves it out: "Not
built here, file it" (`docs/plans/2026-11-15-three-touches.md`, "What goes away").

What a reader would get wrong: `branch.base = "integration"` is not this mode. It points every
task at another branch, and each task still waits for the one before it to merge; nothing takes
the integration branch to the main branch through a review.

What it needs: a task that starts from another task's branch, and lands after it; the review of
the whole program before the integration branch reaches the main branch, since the owner ruled
that a review comes before the merge; and what happens to the later tasks when an earlier one is
dropped.

Unknown that settles the `later`: whether the owner wants the mode at all. In that project those
28 hours left 43 of 48 queued reviews open, and he called commits that reach the base branch
before a review "very dangerous in most cases" (2026-11-15). It is a `yes` when a project of his
needs a long program through Lem, and its review before the merge has a form he accepts.
