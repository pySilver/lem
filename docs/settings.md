# Settings

`.lem/project.toml` holds the settings of a project, in git, and `/lem init` writes it. Lem reads
the rules that guard a change (the topics, the checks, who merges) from your main checkout, so a
task branch cannot change them. An unknown key or a wrong value stops Lem, and the message names
the fix.

## `[paths]`

Paths are relative to the root of the repository.

| Setting | Default | Use |
| --- | --- | --- |
| `paths.plans` | `"docs/plans"` | the folder of the plans |
| `paths.plan_file` | `"YYYY-MM-DD-<slug>.md"` | the name of a plan file |
| `paths.rulings` | `"docs/rulings.md"` | the file of your rulings, one bullet for each: `- **The rule in one sentence.** (YYYY-MM-DD)` under the `##` heading of its group |

## `[branch]`

| Setting | Default | Use |
| --- | --- | --- |
| `branch.base` | `/lem init` writes the default branch | the branch that a task starts from and lands on |
| `branch.land` | `"agent"` | who merges. A merge agent reads each pull request first and writes its review. `"agent"`: the merge agent merges a green pull request that is not careful, and calls you for each other one. `"owner"`: you merge each pull request |
| `branch.history` | `"squash"` | what lands. `"squash"`: one commit. `"keep"`: the commits of the branch |
| `branch.protected` | `[]` | the branches where Lem lands nothing, pushes nothing and deletes nothing, also a task's own branch that you add here later |

## `[checks]`

During the build, each builder runs only the tests of its own change. Before the pull request, Lem
runs the commands below one time, in the worktree of the task. When you change `checks.commands` or
`checks.serial`, a task whose checks passed runs them again before its pull request and before its
merge.

| Setting | Default | Use |
| --- | --- | --- |
| `checks.commands` | `[]` | your tests, the whole suite. Add a linter only when no git hook runs it. With no command, only the task that adds one can land |
| `checks.serial` | `[]` | the tests that two tasks cannot run at the same time, for example an end-to-end suite with fixed ports. They run after `checks.commands`, one at a time for all tasks. Keep them out of `checks.commands` |
| `checks.setup` | `[]` | what a new worktree needs before its tests can run, for example `"uv sync"` or `"npm ci"` |

## `[flow]`

| Setting | Default | Use |
| --- | --- | --- |
| `flow.topics` | `[]` | the topics, one sentence each: `"a customer is charged the wrong amount"`. `/lem init` proposes them from your code, and you correct them. A change that can affect one is careful |

## `[seats]`

A seat is one string, `agent/model:effort`. Write all three parts for `seats.reviewer`,
`seats.planner` and each of `seats.experts`: Lem stops at `"codex"` or `"codex/gpt-6.2-sol"` there.
In `seats.merger` and `seats.session`, a part that you do not write takes the default of the agent.
A persona names its own seats in the frontmatter of its file, in the same form:
`seats: ["claude/opus:high"]`. A persona file without it uses the seats of the panel.

| Setting | Default | Use |
| --- | --- | --- |
| `seats.reviewer` | `"codex/gpt-6.2-sol:high"`, or `"claude/opus:high"` without Codex | the reviewer of the plan talk |
| `seats.planner` | `"claude/opus:high"` | the defender of the plan in the plan talk: only `claude` |
| `seats.merger` | the seat in `~/.config/lem/machine.toml`, else `"claude/opus:high"` | the merge agent: `claude` or `codex`. Without a seat in the repository, Lem uses `merger` under `[seats]` in `~/.config/lem/machine.toml`, the file for all your repositories. Without that, Lem uses `"claude/opus:high"` |
| `seats.session` | the seat in `~/.config/lem/machine.toml`, else `"claude/opus:high"` | the agent of the session of each task: only `claude`. The sources and the default are the same as for `seats.merger` |
| `seats.experts` | `["claude/fable:high", "codex/gpt-6.2-astra:high"]` | the experts of a decision in doubt. Without Codex, one answers alone |

## `[corrections]`

| Setting | Default | Use |
| --- | --- | --- |
| `corrections.collect` | `false` | `true` turns on [the correction queue](install.md#the-correction-queue) for each person in the repository |

## `[naps]`

An optional agent that reads the recent tasks and leaves a note for the retro.

| Setting | Default | Use |
| --- | --- | --- |
| `naps.on` | `false` | `true` turns the naps on |

## `[state]`

Lem keeps the files of its work in `.lem/state/`, and git does not see this folder. The board
server removes the old files from it each hour. When nothing of a task that ended happened for
`state.keep_days` days, the server removes all the files of the task except a small record: its
state, its request, its pull request, and the files of its ticket and of a resume. After that, a
retro or a nap finds no report and no decisions of the task. In the event log, the server replaces
all the events of the task with one summary event, and the board shows the task in Done as before.
Its Overview tells you what stayed, and tabs 2 to 4 of its panel tell you that their details went
with the events. `/lem resume` cannot
start a dropped task again after this: type `/lem` and its request to start a new task. The server
also removes a question to the experts, the folder of a persona panel, a nap and a copy of the
personas that nobody used for that number of days. To see what a number removes, type
`lem project prune --dry-run --days 7`. This command removes and changes nothing.

| Setting | Default | Use |
| --- | --- | --- |
| `state.keep_days` | `30` | the days after which an old file goes. When nothing of a task that ended happened for this number of days, the task keeps only its small record, and its events become one summary event. Lem counts from the last event of the task, and from the last write of a folder. A dropped task whose events became a summary cannot be resumed. A whole number, `1` or more. A computer can set its own number in `.lem/project.local.toml` |

## `[tracker]`

Leave this table out with no tracker. [Connect Linear](linear.md) and
[Connect GitHub Issues](github-issues.md) tell you how to fill it.

| Setting | Default | Use |
| --- | --- | --- |
| `tracker.kind` | required | `"linear"` or `"github"`, the one key of the table. With `"github"`, Lem uses the issues of the repository that origin names |

## `.lem/project.local.toml`

Git does not track this file. It holds the settings of one computer, and only these.

| Table | What it can say |
| --- | --- |
| `[seats]` | a seat for this computer, in the same form. `/lem reviewer codex/gpt-6.2-sol:high` writes the reviewer, and `/lem reviewer default` removes it |
| `[corrections]` | only `collect = false` |
| `[naps]` | only `on = false` |
| `[state]` | only `keep_days`: the days for the old files of this computer. Lem uses this number on this computer, also when it is lower or higher than the number of the project |
