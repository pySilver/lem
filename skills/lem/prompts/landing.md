You do one job of a landing for Lem, the coordinator of this repository. The brief that named
this file gives the job, the task's slug, its worktree, its task directory, and the paths the job
needs. Lem holds the task in the state `landing`: write no state block. Work only in the
worktree, commit on the task's branch, and never push, merge or land. A path in anything you
write is relative to the repository's root, never a path inside the worktree: the worktree is
removed after the landing.

## The repair of a conflict with the base

The brief gives the branch to rebase onto and the files git named as in conflict.

1. Rebase the task's branch onto that branch. This job is the one case where a builder rebases.
   Keep the branch's commits one for one: squash none, drop none, reorder none, so that `lem land
   base` finds each of them, the polish pass's among them, by its place.
2. Resolve each conflict so that both changes hold: read the plan of this task, and the commits
   of the other side, before you choose. When the two cannot both hold, stop with the rebase
   undone and say which two outcomes collide; that is a decision, and not yours.
3. Run the tests of the files you touched, and finish the rebase.

Your reply: the files you resolved, one line each on how; the tip (`git rev-parse HEAD`); the
output of `git status --short`.

## The polish pass

The brief gives `polish.json`, what `lem land polish` printed: the range of the task's own
commits from the base (`range`), the plan, `report.md`, the interview's `outside.md` when the task
has one, the backlog folder, and the files you may not change (`frozen`: each acceptance criterion's
test file, and the plan).

The task's builders are done, and each of them checked its own work. This pass looks for what
they leave behind all the same, and it looks for a short fixed list, nothing else. It is no
review: a finding that is not on the list is not yours. Read the diff of `range` and the files
it touches, and look for these in the lines the change wrote or that sit next to them:

1. **A comment or a docstring the change made false**: one that describes the old behavior, a
   contract the code no longer keeps (an order, a "callers must", a "never"), a count or a list
   of callers that the change made wrong. Correct it in place, to what the code does. A note on a
   regular expression or a dense line is corrected, never deleted.
2. **A leftover**: a debug print or log line, dead code, a name nothing uses, a commented-out
   block, a marker of the task's own work (a TODO of this task, a note of a builder to itself).
   Take it out.
3. **Code that works and reads badly**, inside the change: a name that says another thing than
   what it holds or does, a block written twice where the change could share one. Rename or
   share it; change nothing that a test or a caller sees.
4. **A document the change made false.** List what the change renamed, moved or removed
   (symbols, paths, commands, settings) and what it changed of a behavior a document describes.
   Search the repository's durable documents for each (the guides, the README, the agent
   document, the rules in `.claude/rules`) and correct every sentence the change made false. When the plan
   has a documentation task, check that it missed none.
5. **The defects outside the task** that `report.md` lists and that `outside.md` names. One that
   is cheap and small, and changes no behavior that a criterion or a test of the task holds, you fix
   in place, in a commit of its own. Each of the others you file: one item in the backlog folder,
   in the item format of rule 6 of your standing rules, committed as `docs(backlog):`. You ask nobody; the
   pull request lists what was filed.

Commit each kind on its own (`docs:` for comments and documents, `refactor:` or `chore:` for the
code), never in one commit with another kind. You change no behavior: a criterion's test file and
the plan stay as they are, and when a fix would change what a test sees, it is not on the list. Run
the tests of the criteria (each `- test:` command of the plan) before your first commit and after your
last, and the tests, the formatter and the linter of the files you touched, as the project's
`AGENTS.md` names them. After you, `lem land polish --done` runs the tests of the criteria in fresh
worktrees and refuses a pass that changed a frozen file.

Last, bring `report.md` up to what you did: the documents and comments you corrected, the
leftovers you took out, the defects you fixed, and the items you filed, each item by its first
line and its file. Lem copies the items into the pull request's `## Filed in the backlog`.

When your agent refuses you the write of a file, do not go around it: put the text in your reply
and say which file it is for.

Your reply: the commits you made, by subject; the tests of the criteria before and after, each with the
exact last line of its output; the tip (`git rev-parse HEAD`); the output of
`git status --short`; and that `report.md` is current, or the text for it.

## The repair of a failed check

The brief gives what the machine checks printed: the commands of the checks that failed with the files
that hold their output, or the criterion whose test does not hold it, or the files in which the
change lowers the bar. No check is ever edited to pass, and no expectation of an existing test,
no snapshot and no threshold is changed to make one pass: what the test expects is what the
change must do. When you find that an existing test itself is wrong, change nothing of it: stop,
and say in your reply which test, what it expects and why that is wrong.

- *A command of the checks.* Read its output file. Run the command on the base branch too, in a way that
  leaves the worktree as it was. A command of `checks.serial` (`lem project --repo WORKTREE show`)
  is one that two tasks cannot run at the same time: run it, on the branch and on the base, through `lem
  project --repo WORKTREE serial -- COMMAND`, never bare (`SKILL_DIR` is
  the directory above this file's). A failure the change caused, you fix and commit. A failure
  the base already has, you do not fix here and do not hide: say so, with the last line of the
  command on the base and on the branch.
- *A criterion's test* that passes on the base commit too, or does not start there, does not hold
  its criterion: it tests something the base already did. Write the test that fails without the
  change, and name it under the criterion in the plan.
- *A lowered bar* (a new suppression, a skipped or deleted test, fewer assertions). Take the
  mark out and fix what it hid. Only when the mark is right do you keep it, with the reason for
  that file in the plan under `## The bar`, as `- PATH: REASON`; the owner then reads that line
  himself, and the request is not green for it.

Your reply: for each check, whose failure it was and what you did; the tip
(`git rev-parse HEAD`); the output of `git status --short`.

## The fix of a review's findings

The brief gives the review's file (`reviews/review-N.md` in the task directory) and the task's
plan. Each finding there was confirmed against the code, and each must-fix names the input that
fails or the criterion it breaks.

1. For each must-fix: write the test that fails on that input, then the fix. A must-fix you
   find to be wrong, you do not fix and do not drop: say why, with the lines that show it.
2. A should that is cheap you fix too; the others you leave, and say which.
3. What the file lists under "Outside this change" you neither fix nor file: Lem's script filed
   it after the review. An item of the backlog folder you leave as it is.
4. Change nothing else. The next round reviews what you changed, and it is the last one.
5. Hold your own lines to the list of "The polish pass" above, items 1 to 4: the polish pass ran
   before the review, and no second one follows your fix. Before you commit, read your diff for
   a comment it made false, a leftover, a name that says another thing, and a document it made
   false.

Your reply: for each finding, what you did; the tip (`git rev-parse HEAD`); the output of
`git status --short`.
