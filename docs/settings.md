# Settings

`.lem/project.toml` holds the settings of a project, in git, and `/lem init` writes it. Lem reads
the rules that guard a change (the topics, the checks, who merges) from your main checkout, so a
task branch cannot change them. An unknown key or a wrong value stops Lem, and the message names
the fix.

## `[paths]`

Each path is relative to the root of the repository.

| Setting | Default | Use |
| --- | --- | --- |
| `paths.plans` | `"docs/plans"` | the folder of the plans |
| `paths.plan_file` | `"YYYY-MM-DD-<slug>.md"` | the name of a plan file |

## `[branch]`

| Setting | Default | Use |
| --- | --- | --- |
| `branch.base` | `/lem init` writes the default branch | the branch that a task starts from and lands on |
| `branch.land` | `"owner"` | who merges: `owner`, or `agent`, which merges only a green pull request that the review called not careful |
| `branch.history` | `"keep"` | what lands: the commits of the branch (`keep`), or one commit (`squash`) |
| `branch.propose` | `"pull-request"` | with a remote on GitHub: a pull request that Lem opens without a question, or `merge` into the base branch with no pull request |
| `branch.protected` | `[]` | the branches where Lem lands nothing and pushes nothing |

## `[checks]`

The checks must pass before a pull request. Put your tests here, and a linter only when no git hook
runs it.

| Setting | Default | Use |
| --- | --- | --- |
| `checks.commands` | `[]` | the whole suite, run one time before the pull request. With none, only the task that adds them can land |
| `checks.setup` | `[]` | what a fresh worktree needs before Lem runs the test of each criterion there, for example `"uv sync"` or `"npm ci"` |
| `checks.alone` | `[]` | the commands that need the computer to themselves, for example an end-to-end suite with fixed ports |

## `[flow]`

What must never go wrong, and how many tasks run.

| Setting | Default | Use |
| --- | --- | --- |
| `flow.topics` | `[]` | the topics, one sentence each: `"a customer is charged the wrong amount"`. A change that can affect one is careful |
| `flow.max_tasks` | `4` | how many tasks build or land at the same time. Lower it when tests share a database or a browser |

## `[seats]`

A seat is one string, `agent/model:effort`, and the model and the effort are optional.

| Setting | Default | Use |
| --- | --- | --- |
| `seats.reviewer` | `/lem init` writes `"codex"`, or `"claude"` without Codex | the reviewer of the plan talk: `claude` or `codex` |
| `seats.planner` | `claude`, with its own model and effort | the agent that defends the plan in the plan talk: only `claude` |
| `seats.experts` | `["claude/fable", "codex/gpt-6-astra:high"]` | the two experts of a decision in doubt |

## `[corrections]`

The optional queue of your corrections.

| Setting | Default | Use |
| --- | --- | --- |
| `corrections.collect` | `false` | `true` turns on [the queue](install.md#the-correction-queue) for each person in the repository |

## `[naps]`

An optional agent that reads the recent tasks now and then, and leaves a note for the retro.

| Setting | Default | Use |
| --- | --- | --- |
| `naps.on` | `false` | `true` turns the naps on |

## `[tracker]`

Leave this table out when the project has no tracker; [Connect Linear](linear.md) tells you how
to fill it.

| Setting | Default | Use |
| --- | --- | --- |
| `tracker.kind` | required | `"linear"` |
| `tracker.server` | required | the name of the Linear MCP server in Claude Code |
| `tracker.workspace` | required | the workspace, as in `linear.app/acme` |
| `tracker.team` | required | the key of the team whose tickets this project takes |
| `tracker.moves` | required | who moves a ticket: `lem`, or `tracker` when the automation of Linear does it |
| `tracker.started` | with `moves = "lem"` | the status of a ticket whose work started, as your team spells it |
| `tracker.landed` | with `moves = "lem"` | the status of a ticket whose work landed |

## `.lem/project.local.toml`

This file holds the settings of one computer, and git does not track it. It can hold only these.

| Table | What it can say |
| --- | --- |
| `[seats]` | a seat for this computer. `/lem reviewer codex/gpt-6.1-sol:high` writes the reviewer, and `/lem reviewer default` removes it |
| `[corrections]` | only `collect = false` |
| `[naps]` | only `on = false` |
| `[flow]` | only `max_tasks` |
