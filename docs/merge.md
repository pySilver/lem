# The merge

## The merge review

A fresh merge agent reads the [pull request](pull-request.md), task files, reviews and diff.
It writes `merge-review.md` and leaves the change as it is. The verdict is merge or call.
The review gives the work, purpose, results, decisions Lem took without you, time and tokens.

A safe small change gets the verdict and three sentences. A visual change gets before and after
pictures, or a line that says why they are missing. If the verdict is call, the last line tells
you how to try a visual change.

```mermaid
flowchart TD
    A["Lem opens the pull request"] --> B["A merge agent reads the task"]
    B --> C["It writes merge-review.md"]
    C --> D{"Is the change green and not careful?"}
    D -- "green, not careful" --> E{"Do the settings and verdict permit the merge?"}
    D -- "not green or careful" --> Y["You read the review, then merge or ask for a change"]
    E -- "settings permit, verdict is merge" --> M["Lem merges"]
    E -- "owner setting or call verdict" --> Y
```

When the merge agent calls you, "Waits for you" shows "Read the merge review" and "2 things".
The stack has a row for the review and one for the merge. The review is also the task's first card.

The board server merges a green change that is not careful when the verdict is merge and
[`branch.land`](settings.md#branch) is `"agent"`. Until the verdict, the task stays in "Checks
and review", with no row in "Waits for you" and no notification.

With `branch.land = "owner"`, the merge agent still writes its review. You merge the pull request.

## Merge it

Use **Merge** on GitHub, **Merge…** then **Approve** on the [board](board.md#act-from-the-board),
or `/lem land <task>`. While you are [away](away.md#answer-from-the-inbox), you can also answer
in the Inbox. Lem records your approval for the commit you see.

- GitHub applies the rules of your base branch. "Waits for you" shows a refusal from GitHub.
  If the pull request targets a different base branch, Lem refuses and gives the fix.
- Before an automatic merge, a fresh merge agent reads any change to the base tree since the checks. With
  `Base: safe.`, Lem can merge without a new run of the checks. After the merge, the pull request
  gives both bases and the reason. With `Base: another round.`, Lem rebases the task. It runs the
  checks again before it can merge.
- On a moved base, Lem rebases an approved task and runs the checks again. After a rebase or
  conflict, approval stands if a review covers the change and while the reasons for "not green"
  stay the same. The approved criteria must also stay the same. If your approval ends, the pull
  request says why. Approve the pull request again if your approval ends.
- If the checks fail after a rebase, the task leaves the line until a builder fixes it.
  It calls you only when the fix needs a criterion to change or a breaker applies.
- Lem merges one task at a time. A task whose checks ran on the current base merges first.
- For several tasks in one `/lem land` request, Lem merges them in the order you give. If you give
  no order, Lem starts with the oldest proposal.

Merge through the pull request. Afterward, the task removes its worktree and both copies of its
branch. It updates its ticket. Lem keeps a branch with an unmerged change and tells you what
changed and how to delete it.

On GitHub's button, you select the merge method. `branch.history` is for Lem's merge. With
`branch.history = "squash"`, the body of Lem's commit lists the task's decisions. It also gives
the note about a moved base when there is one. The last line is `Lem task: <task>`. The board
reads that line to show which task added a backlog item. See
[Fixed on the way](pull-request.md#what-lem-saw-outside-the-task) for the fixes.

The board server sees a merge or a close on GitHub within a few minutes.

## A conflict

The board server wakes each task whose pull request now conflicts. The task rebases the branch.
A builder resolves the conflict. The checks run again and one review reads the resolution.
Lem leaves every other open pull request as it is.

The merge review stays only if the merge agent gave a verdict before the conflict. A fresh merge
agent reads the pull request when:

- the merge agent did not give a verdict before the conflict;
- the read found a must-fix, a should or a nit, or did not answer two times;
- the change is careful;
- a commit came after the resolution;
- the review before the conflict left a must-fix.

The pull request says when the merge review carries.

## A commit of a teammate

Lem never pushes over a commit that it did not push. Such a commit stops Lem before its next push,
and Lem names the `git pull --rebase` that brings it in. Then the commit gets the checks and a read.

## Stop a task

Type `/lem drop <task>`, or close the pull request on GitHub with no merge. Lem removes the
worktree. A branch with commits of its own stays, and Lem tells you how to delete it. For new work,
make a new request.
