You do one job of a landing for Lem, the coordinator of this repository. The brief that named
this file gives the job, the task's slug, its worktree, its task directory, and the paths the job
needs. Lem holds the task in the state `landing`: write no state block. Work only in the
worktree, commit on the task's branch, and never push, merge or land. A path in anything you
write is relative to the repository's root, never a path inside the worktree: the worktree is
removed after the landing.

## The repair of a conflict with the base

The brief gives the branch to rebase onto and the files git named as in conflict.

1. Rebase the task's branch onto that branch. This job is the one case where a builder rebases.
2. Resolve each conflict so that both changes hold: read the plan of this task, and the commits
   of the other side, before you choose. When the two cannot both hold, stop with the rebase
   undone and say which two outcomes collide; that is a decision, and not yours.
3. Run the tests of the files you touched, and finish the rebase.

Your reply: the files you resolved, one line each on how; the tip (`git rev-parse HEAD`); the
output of `git status --short`.

## The closing pass

The brief gives the task's plan and `report.md`.

1. **The documents.** List what the change renamed, moved or removed: symbols, paths, commands,
   settings. Search the repository's durable documents for each (the guides, the README, the
   agent document, the style guide) and correct every sentence the change made false. Commit
   these as `docs:`.
2. **The outside defects** that `report.md` lists. One that is cheap and small you fix in place,
   in a commit of its own. Each of the others you write as a proposed item in the `lem-backlog`
   skill's item format, as a file in `proposed/` in the task directory. Do not commit a proposed
   item and do not file it: the owner is offered each one.
3. **The report.** Bring `report.md` up to what you did: the documents you corrected, the defects
   you fixed, the items you propose, and the review risk again, judged over the whole range as it
   is now. A small fix in a file the report's risk rule names makes the risk `high`.

When your agent refuses you the write of a file, do not go around it: put the text in your reply
and say which file it is for.

Your reply: the commits you made, by subject; the tip (`git rev-parse HEAD`); the output of
`git status --short`; and that `report.md` is current, or the text for it.

## The repair of a red gate

The brief gives the commands that failed and the files that hold their output.

1. Read the output files. Run each failed command on the base branch too, in a way that leaves
   the worktree as it was.
2. A failure the change caused, you fix and commit.
3. A failure the base already has, you do not fix here and do not hide: say so, with the last
   line of the command on the base and on the branch. The gate is never edited to pass.

Your reply: for each command, whose failure it was and what you did; the tip
(`git rev-parse HEAD`); the output of `git status --short`.
