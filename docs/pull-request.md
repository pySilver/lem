# The pull request

## What it says

The first line says green or not green, and each reason for "not green" comes next. Then come your
request, the acceptance criteria with their tests, the checks (your test commands), and each
decision with who took it and why.

A pull request is not green when one of these is true:

- your tests got less strict (the bar went down), even with a reason in the plan;
- the review left a must-fix after two rounds, or no reviewer answered;
- a criterion changed during the build;
- Lem took a decision of yours while you were away;
- the personas did not answer, two times, when they read the criteria;
- the change brings the first checks into a project that had none;
- a task on the fast track turned out to be careful: it can affect what must never go wrong.

You can merge a green pull request without a read.

On the standard track, Lem also makes a page that tells what was built, why, and who took each decision.
Type `/lem status <task>` to open it.

## Merge it

Merge it on GitHub, as you do with any other: GitHub merges it as it is. Then Lem removes the worktree and the branch of the
task, and updates its Linear ticket if it has one. The next task that waits can start.

To let Lem merge, type `/lem land <task>`, or say "land it". Lem merges through GitHub, so the rules
of your base branch apply. If the base moved after the checks, the checks run again first.

| Setting | What changes |
| --- | --- |
| `branch.land = "agent"` | Lem merges a green pull request itself, if the review said not careful and the task does not run without you |
| `branch.history = "keep"` | the commits of the branch land, and not one commit for the task |
| `branch.propose = "merge"` | no pull request: "land it" merges the branch into the base branch |

While Lem's session is open, it looks at its pull requests one time each minute, with the GitHub
CLI `gh`. Each `/lem` also looks. When the board says "nobody watches", type `/lem`.

> [!TIP]
> On GitHub, turn on "Require branches to be up to date before merging" for the base branch.
> Then GitHub refuses a branch that is behind its base. For such a branch, type `/lem land
> <task>`: Lem rebases it and runs the checks again before the merge.

## A conflict

When a merge makes another open pull request conflict, Lem rebases its branch, and a builder
resolves the conflict. The checks run again, and one read checks the resolution. Then Lem updates
the pull request and tells you in one line, for example:

> Rebased on main after the forge called it conflicting; one conflict in shop/dates.py, resolved by
> a builder; the checks passed again.

Lem leaves every other open pull request as it is.

## A commit of a teammate

Lem never pushes over a commit that it did not push. Such a commit stops Lem before its next push,
and Lem names the `git pull --rebase` that brings it in. Then the commit gets the checks and a read.

## Stop a task

Type `/lem drop <task>`, or close the pull request on GitHub with no merge. Lem removes the worktree. A branch
with commits of its own stays, and Lem tells you how to delete it. A task that ended does not start
again: for new work, make a new request.
