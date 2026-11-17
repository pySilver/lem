# The polish pass

Step 3 of `stages/land.md`, for a full change.

The task's own work is done, so this is the one moment for what it left around it, before the checks
and the review, so that the review reads the code as it will merge. Rules and reviews do not catch
what this pass catches: "Polishing step, sadly is unavoidable (most likely). I've tried many rules
etc but polishing step shows that there are some drifted comments, ugly code, leftovers and so on
always to be found" (the owner, 2026-11-16). `lem land polish SLUG` prints what the pass works on
and keeps the tip it starts at; keep its output as `polish.json` in the task directory.
`spawn-builder` with the brief at the end of `stages/land.md`, the job "the polish pass", and as its
path that file. The builder looks for a short fixed list and nothing else, inside the task's own
commits (`prompts/landing.md` has the list): a comment the change made false, a leftover, code that
works and reads badly, a document the change made false, and the defects outside the task that
`report.md` and the interview's `outside.md` name, each fixed in place when cheap or filed in the
backlog. It changes no behavior. Then `lem land polish SLUG --done` checks what it committed: it
refuses a worktree with changes nobody committed, a change of a criterion's test file or of the
plan, and tests of the criteria that no longer pass on the branch and fail on the base commit; a
refusal goes back to a builder with the same job and the step's message. Otherwise it logs the pass,
and the pull request's checks say how many commits it made and how many items it filed. The pass
runs once for a task, here, and never after each task of a plan; a builder of a later job of this
landing has the same list in its brief. So when the landing comes back here from a later step and
`lem land polish` prints `"done": true`, go on to step 4 of `stages/land.md`. `checks` refuses a
full change with no pass on the tip it checks. A rewrite of the branch after the pass, other than
the rebase of `base`, asks for the pass again: `checks` says so.

Read `report.md` again after the pass: its builder brought it up to what it did, the documents it
corrected, the defects it fixed and the items it filed. When its agent refused it the write, its
reply holds the report's text instead, and you write `report.md` from it word for word.
