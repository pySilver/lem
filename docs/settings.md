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
| `paths.rulings` | `"docs/rulings"` | the folder of your rulings |
| `paths.ruling_file` | `"<slug>.md"` | the name of a ruling file |

## `[branch]`

| Setting | Default | Use |
| --- | --- | --- |
| `branch.base` | `/lem init` writes the default branch | the branch that a task starts from and lands on |
| `branch.land` | `"owner"` | who merges. `"owner"`: you. `"agent"`: Lem, only a green pull request that the review called not careful, and never while you are away |
| `branch.history` | `"squash"` | what lands. `"squash"`: one commit. `"keep"`: the commits of the branch |
| `branch.propose` | `"pull-request"` | how a task ends with a remote on GitHub. `"pull-request"`: Lem opens a pull request, with no question. `"merge"`: Lem merges into the base branch, with no pull request |
| `branch.protected` | `[]` | the branches where Lem lands nothing and pushes nothing |

## `[checks]`

During the build, each builder runs only the tests of its own change. Before the pull request, Lem
runs the commands below one time, in the worktree of the task.

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

A seat is one string, `agent/model:effort`. A part that you leave out takes the default of the agent.
A persona names its own seats in the frontmatter of its file, in the same form:
`seats: ["claude/opus:high"]`. A persona file without it uses the seats of the panel.

| Setting | Default | Use |
| --- | --- | --- |
| `seats.reviewer` | `"codex/gpt-6.2-sol:high"`, or `"claude/opus:high"` without Codex | the reviewer of the plan talk |
| `seats.planner` | `"claude/opus:high"` | the defender of the plan in the plan talk: only `claude` |
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

## `[tracker]`

Leave this table out with no tracker. [Connect Linear](linear.md) tells you how to fill it.

| Setting | Default | Use |
| --- | --- | --- |
| `tracker.kind` | required | `"linear"`, the one key of the table |

## `.lem/project.local.toml`

Git does not track this file. It holds the settings of one computer, and only these.

| Table | What it can say |
| --- | --- |
| `[seats]` | a seat for this computer. `/lem reviewer codex/gpt-6.2-sol:high` writes the reviewer, and `/lem reviewer default` removes it |
| `[corrections]` | only `collect = false` |
| `[naps]` | only `on = false` |
