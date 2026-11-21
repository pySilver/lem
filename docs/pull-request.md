# The pull request

## What it says

The first line says green or not green, and each reason for "not green" comes next. Then come your
request, the acceptance criteria with their tests, the checks (your test commands), and each
decision with who took it and why.

A pull request is not green when one of these is true:

- your tests got less strict (the bar went down), even with a reason in the plan;
- the review left a must-fix after two rounds, or no reviewer answered;
- a criterion changed during the build;
- a decision went past the personas: the dialectic or the experts took it;
- Lem approved the criteria without you: while you were away, or in a night task;
- the personas did not answer, two times, when they read the criteria;
- the change brings the first checks into a project that had none;
- a task on the fast track turned out to be careful: it can affect what must never go wrong.

Smaller choices of an agent do not change green. The pull request lists the ones that matter.

## The merge review

Lem opens each pull request on GitHub, the one way a task lands. Then a fresh merge agent reads
the task: its files, its reviews and its diff. It changes nothing. It writes `merge-review.md` in
the folder of the task. The review starts with its verdict, merge or
call. Then it tells what Lem built and why, as a short story. Last come the results, each decision
that Lem took without you, and the time of the task. The review is shorter than the documents it
read. For a safe small change, it is the verdict and three sentences.

```mermaid
flowchart TD
    A["Lem opens the pull request"] --> B["A merge agent reads the task"]
    B --> C["It writes merge-review.md"]
    C --> D{"Careful, or not green?"}
    D -- "yes" --> W["It calls you"]
    D -- "no" --> E{"Did it find a problem?"}
    E -- "yes" --> W
    E -- "no" --> M["It merges"]
    W --> Y["You read the review, then merge or ask for a change"]
```

The merge agent calls you for each careful change and for each pull request that is not green.
It also calls you when it finds a problem. The board then shows "Read the merge review" in
"Waits for you", and the review is the first card of the task.

While the merge agent reads a pull request, nothing of it waits for you. After the verdict merge,
the board server merges it, and nothing waits for you then either. Until the merge, the task stays
in the column "Checks and review", with no row in "Waits for you" and no notification.

With `branch.land = "owner"`, the merge agent still writes its review, but it never merges
([Settings](settings.md#branch)).

## Merge it

There is one merge: the merge of the pull request on GitHub. You start it with the Merge button
on GitHub, with Merge on the [board](board.md), or with `/lem land <task>`. When the merge agent
gives the verdict merge, the board server starts the same merge.

- A merge goes through GitHub, under the rules of your base branch. When GitHub refuses it,
  "Waits for you" shows the line that GitHub gave.
- When the base branch moved, Lem first runs the checks again.
- With more than one task, `/lem land` merges them one at a time, in your order.

Do not merge the branch of a task by hand: Lem knows only a merge through the pull request. After
a merge, Lem removes the worktree and the branch, and updates the Linear ticket of the task.

On GitHub's button, you select the merge method. `branch.history` is for a merge by Lem.

The board server asks GitHub about the open pull requests every few minutes. When you merge or
close one on GitHub, the server records it and wakes the session of its task. That session
removes the worktree and the branch.

## A conflict

When a merge makes another open pull request conflict, the board server wakes the session of its
task. That session rebases the branch, and a builder resolves the conflict. The checks run again,
one read checks the resolution, and the merge agent reads the pull request again. The session tells
you in one line, for example:

> Rebased on main after the forge called it conflicting; one conflict in shop/dates.py, resolved by
> a builder; the checks passed again.

Lem leaves every other open pull request as it is.

## A commit of a teammate

Lem never pushes over a commit that it did not push. Such a commit stops Lem before its next push,
and Lem names the `git pull --rebase` that brings it in. Then the commit gets the checks and a read.

## Stop a task

Type `/lem drop <task>`, or close the pull request on GitHub with no merge. Lem removes the
worktree. A branch with commits of its own stays, and Lem tells you how to delete it. For new work,
make a new request.
