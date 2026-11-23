# Settings

Lem reads its settings from four files. An unknown key, a wrong value or a table in the wrong file
stops Lem, and the message names the fix.

## The four files

`~/.config/lem/` is `$XDG_CONFIG_HOME/lem/` when you set that variable.

| File | Whose | In git | What it holds |
| --- | --- | --- | --- |
| `.lem/settings.toml` | the team's, for this repository | yes | the rules that guard a change, and the team's seats. `/lem init` writes it |
| `.lem/settings.local.toml` | yours, for this repository | no | your seats, a no to the naps, and the days of the old files on this computer |
| `~/.config/lem/settings.toml` | yours, for every repository on this computer | no | your seats, and the look of the question page |
| `~/.config/lem/machine.toml` | this computer's | no | what is true for the whole computer: the load limit, the board server, the other computers, the compaction and the correction queue |

## Which file wins

A setting that more than one file can hold comes from the nearest file that holds it:

1. `.lem/settings.local.toml`
2. `.lem/settings.toml`
3. `~/.config/lem/settings.toml`
4. Lem's default

`lem project show` gives the file of each such value in `from`, or "Lem's default". No other file
overrides `~/.config/lem/machine.toml`.

Lem reads the rules that guard a change (the topics, the checks, who merges) from your main
checkout, so a task branch cannot change them. In the worktree of a task, Lem reads `[flow]`,
`[naps]` and `[state]` as your base branch has them. Lem reads `.lem/settings.local.toml` from your
main checkout, also for a task.

## Where each table is valid

Lem refuses a table in a file where it is not valid, and the message names the file where it is
valid.

| Table | `~/.config/lem/machine.toml` | `~/.config/lem/settings.toml` | `.lem/settings.toml` | `.lem/settings.local.toml` |
| --- | --- | --- | --- | --- |
| `[load]`, `[serve]`, `[peers]`, `[handoff]`, `[corrections]` | yes | no | no | no |
| `[seats]` | no | yes | yes | yes |
| `[ask]` | no | yes | no | no |
| `[flow]`, `[checks]`, `[branch]`, `[paths]`, `[tracker]`, `[jev]` | no | no | yes | no |
| `[naps]` | no | no | yes | only `on = false` |
| `[state]` | no | no | yes | yes |

## `.lem/settings.toml`

The settings of the team, in git. `/lem init` writes this file.

### `[paths]`

Paths are relative to the root of the repository.

| Setting | Default | Use |
| --- | --- | --- |
| `paths.plans` | `"docs/plans"` | the folder of the plans |
| `paths.plan_file` | `"YYYY-MM-DD-<slug>.md"` | the name of a plan file |
| `paths.rulings` | `"docs/rulings.md"` | the file of your rulings, one bullet for each: `- **The rule in one sentence.** (YYYY-MM-DD)` under the `##` heading of its group |

### `[branch]`

| Setting | Default | Use |
| --- | --- | --- |
| `branch.base` | `/lem init` writes the default branch | the branch that a task starts from and lands on |
| `branch.land` | `"agent"` | who merges. A merge agent reads each pull request first and writes its review. `"agent"`: the merge agent merges a green pull request that is not careful, and calls you for each other one. `"owner"`: you merge each pull request |
| `branch.history` | `"squash"` | what lands. `"squash"`: one commit. `"keep"`: the commits of the branch |
| `branch.protected` | `[]` | the branches where Lem lands nothing, pushes nothing and deletes nothing, also a task's own branch that you add here later |

### `[checks]`

During the build, each builder runs only the tests of its own change. Before the pull request, Lem
runs the commands below one time, in the worktree of the task. When you change `checks.commands` or
`checks.serial`, a task whose checks passed runs them again before its pull request and before its
merge.

| Setting | Default | Use |
| --- | --- | --- |
| `checks.commands` | `[]` | your tests, the whole suite. Add a linter only when no git hook runs it. With no command, only the task that adds one can land |
| `checks.serial` | `[]` | the tests that two tasks cannot run at the same time, for example an end-to-end suite with fixed ports. They run after `checks.commands`, one at a time for all tasks. Keep them out of `checks.commands` |
| `checks.setup` | `[]` | what a new worktree needs before its tests can run, for example `"uv sync"` or `"npm ci"` |

### `[flow]`

| Setting | Default | Use |
| --- | --- | --- |
| `flow.topics` | `[]` | the topics, one sentence each: `"a customer is charged the wrong amount"`. `/lem init` proposes them from your code, and you correct them. A change that can affect one is careful |

### `[seats]`

A seat is one string, `agent/model:effort`. Write all three parts for `seats.reviewer`,
`seats.planner`, `seats.fallback` and each of `seats.experts`: Lem stops at `"codex"` or
`"codex/gpt-6.2-sol"` there. In `seats.merger` and `seats.session`, a part that you do not write
takes the default of the agent. A persona names its own seats in the frontmatter of its file, in
the same form: `seats: ["claude/opus:high"]`. A persona file without it uses the seats of the panel.

Lem takes each seat, and `seats.fallback`, from the first of four places that names it:

1. `.lem/settings.local.toml`: you, for this repository;
2. `.lem/settings.toml`: the team;
3. `[seats]` in `~/.config/lem/settings.toml`: you, for all repositories;
4. the default of Lem, in the table below.

`lem project show` gives each seat and its place. `/lem set local NAME VALUE` writes a line of
`.lem/settings.local.toml`, and `/lem set global NAME VALUE` writes a line of
`~/.config/lem/settings.toml`. NAME is a seat or `fallback`. VALUE is a whole seat, one or two
whole seats with a comma between them for `experts`, `false` for `fallback`, or `default`, which
removes the line. The other lines and the comments of the file stay. No command writes
`.lem/settings.toml`.

When the agent of the reviewer, the planner or the merge agent gives an error, the fallback seat
starts in its place, and the task goes on. An error is a program that is not on this computer, no
login, no tokens, or a model that the agent does not know. A slow agent is not an error. The pull
request names the seat that stood in, the seat that failed and the error. This does not make it not green. With
`fallback = false`, or when the fallback cannot stand in, the task stops and waits for you. Type
"go on" in the session of the task, and Lem tries the seat again.

| Setting | Default | Use |
| --- | --- | --- |
| `seats.reviewer` | the seat in `~/.config/lem/settings.toml`, else `"claude/opus:high"`. `/lem init` writes `"codex/gpt-6.2-sol:high"`, or `"claude/opus:high"` without Codex | the reviewer of the plan talk |
| `seats.planner` | the seat in `~/.config/lem/settings.toml`, else `"claude/opus:high"` | the defender of the plan in the plan talk: only `claude` |
| `seats.merger` | the seat in `~/.config/lem/settings.toml`, else `"claude/opus:high"` | the merge agent: `claude` or `codex` |
| `seats.session` | the seat in `~/.config/lem/settings.toml`, else `"claude/opus:high"` | the agent of the session of each task: only `claude` |
| `seats.experts` | the list in `~/.config/lem/settings.toml`, else `["claude/fable:high", "codex/gpt-6.2-astra:high"]` | the experts of a decision in doubt. Without Codex, one answers alone |
| `seats.fallback` | the line in `~/.config/lem/settings.toml`, else `"claude/opus:high"` | the seat that Lem starts in place of the reviewer, the planner or the merge agent when its agent gives an error. Write all three parts. `false` turns the fallback off, and then the task waits for you |

### `[naps]`

An optional agent that reads the recent tasks and leaves a note for the retro.

| Setting | Default | Use |
| --- | --- | --- |
| `naps.on` | `false` | `true` turns the naps on |

### `[state]`

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
| `state.keep_days` | `30` | the days after which an old file goes. When nothing of a task that ended happened for this number of days, the task keeps only its small record, and its events become one summary event. Lem counts from the last event of the task, and from the last write of a folder. A dropped task whose events became a summary cannot be resumed. A whole number, `1` or more. A computer can set its own number in `.lem/settings.local.toml` |

### `[jev]`

Before a pull request, Lem asks the Jev decision model one question about each defect outside the
task that an agent calls under the bar: is this defect over the bar? The line of the defect in the
pull request shows the score. When the score is high, `lem land propose` stops one time, and the
agent looks at the defect again. Each question sends the place, the title and the text of the
defect to the provider of the model. Lem sends nothing when your computer has no `JEV_API_KEY`.

| Setting | Default | Use |
| --- | --- | --- |
| `jev.findings` | `true` | `false` sends no defect of this repository to the model. The line of the defect then says "Jev: not asked (off in the settings)" |

### `[tracker]`

Leave this table out with no tracker. [Connect Linear](linear.md) and
[Connect GitHub Issues](github-issues.md) tell you how to fill it.

| Setting | Default | Use |
| --- | --- | --- |
| `tracker.kind` | required | `"linear"` or `"github"`, the one key of the table. With `"github"`, Lem uses the issues of the repository that origin names |

## `.lem/settings.local.toml`

Git does not track this file. It holds your settings for this repository on this computer, and only
these.

| Table | What it can say |
| --- | --- |
| `[seats]` | a seat or `fallback` for this computer, in the same form. It replaces the line of the team. `/lem set local reviewer codex/gpt-6.2-sol:high` writes the reviewer, and `/lem set local reviewer default` removes it |
| `[naps]` | only `on = false` |
| `[state]` | only `keep_days`: the days for the old files of this computer. Lem uses this number on this computer, also when it is lower or higher than the number of the project |

## `~/.config/lem/settings.toml`

Your settings for every repository on this computer. `/lem set global NAME VALUE` writes a line
of `[seats]` and keeps the other lines. You write `[ask]` by hand. A repository file that names the
same seat wins.

| Setting | Default | Use |
| --- | --- | --- |
| `seats.reviewer`, `seats.planner`, `seats.merger`, `seats.session`, `seats.experts`, `seats.fallback` | as in [`[seats]`](#seats) | each seat and the fallback, in the form of [`[seats]`](#seats) |
| `ask.style` | `"refined"` | the look of the question page: `"refined"`, `"minimal"`, `"bold"` or `"terminal"` |
| `ask.size` | `"auto"` | the size of the question page: a percent of the pane, `"auto"` or `"full"` |
| `ask.review` | `"auto"` | the list of your answers before Lem gets them: `"auto"`, `"always"`, `"never"`, `true` or `false` |
| `ask.browser` | `false` | `true` opens the question page in your browser when you work outside agterm |
| `ask.status` | `{asking = ["blocked"], answered = ["active"]}` | the status of the session while a question waits, and after you answer it |

## `~/.config/lem/machine.toml`

The settings of this computer, for every repository on it. No other file overrides them. The
commands below write this file, and each one keeps the other tables.

| Setting | Default | Use |
| --- | --- | --- |
| `load.start` | `40` | the load average under which the checks of a landing start. `lem project load --start N` sets it, and `lem project load --start none` writes `0`, which removes the limit |
| `serve.port` | `4536` | the port of the board server. `lem serve --port N` sets it |
| `serve.tailscale` | `false` | `true` opens the door for your phone. `/lem serve tailscale` and `/lem serve tailscale off` set it |
| `serve.tailscale_port` | `4537` | the port of that door. `lem serve --tailscale-port N` sets it |
| `peers.HOST` | none | the port of the door of another computer of the board, with its Tailscale name as `HOST`. `/lem serve join HOST` and `/lem serve leave HOST` write it |
| `handoff.tokens` | `600000` | the number of tokens where the session of a task compacts. `0` lets Claude Code compact at its own limit. `lem project handoff --tokens N` sets it |
| `corrections.collect` | `false` | `true` turns on [the correction queue](install.md#the-correction-queue) in every repository on this computer. `lem corrections collect yes` and `lem corrections collect no` set it |
