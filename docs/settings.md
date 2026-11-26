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

`lem settings show` gives every value and, in `from`, the file of each value, or "Lem's default".
No other file overrides `~/.config/lem/machine.toml`.

For each task, Lem reads `.lem/settings.toml` and `.lem/settings.local.toml` from your main checkout.
A task branch cannot change the topics, the checks or who merges.
When your main checkout is on another branch than the base, Lem reads
`.lem/settings.toml` as the newest commit of your base branch has it.

`lem settings set KEY VALUE --local`, `--home` or `--machine` writes one line of
`.lem/settings.local.toml`, `~/.config/lem/settings.toml` or `~/.config/lem/machine.toml`. KEY is
`TABLE.KEY`, as in the tables below. VALUE `default` removes the line. The other lines and the
comments of the file stay. Lem checks all the settings with the new line before it writes it.
A wrong value in any file stops the command, and the file stays as it was.
Edit and commit `.lem/settings.toml` yourself.

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
| `branch.land` | `"agent"` | who merges. A merge agent reviews each pull request. With `"agent"`, Lem merges a green change that is not careful if the verdict is merge. With `"owner"`, you merge every pull request |
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

`lem settings show` gives each seat and its place. `lem settings set seats.NAME VALUE --local`
writes a line of `.lem/settings.local.toml`, and `lem settings set seats.NAME VALUE --home` writes
a line of `~/.config/lem/settings.toml`. NAME is a seat or `fallback`. VALUE is a whole seat, one or
two whole seats with a comma between them for `experts`, or `false` for `fallback`.
Use `default` to remove the line.

When the reviewer, planner or merge agent gives an error, the fallback seat starts in its place.
The task goes on. An error can come from a missing program, a missing login or an unknown model.
An agent also fails if it has no tokens or reaches a usage limit. A slow agent is not an error. The pull
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
server removes the old files from it each hour. If an ended task has no new activity for
`state.keep_days` days, the server keeps only a small record. It keeps the state, the request, the
pull request, and the files for the ticket and resume. After that, a retro or a nap finds no
report and no decisions of the task. The server replaces the task's events in the log with one
summary event. The board still shows the task in Done.
Its Overview tells you what stayed, and tabs 2 to 4 of its panel tell you that their details went
with the events. `/lem resume` cannot
start a dropped task again after this: type `/lem` and its request to start a new task. The same
limit applies to unused files of expert questions, persona panels, naps and copies of personas.
To see what a number removes, type
`lem prune --dry-run --days 7`. This command removes and changes nothing.

| Setting | Default | Use |
| --- | --- | --- |
| `state.keep_days` | `30` | the days after which an old file goes. After this many days with no new activity, an ended task keeps only its small record. Its events become one summary event. Lem counts from the last event of the task, and from the last write of a folder. A dropped task whose events became a summary cannot be resumed. A whole number, `1` or more. A computer can set its own number in `.lem/settings.local.toml` |

### `[jev]`

Before a pull request, Lem asks the Jev decision model about each defect outside the task that an
agent calls under the bar. Jev gives a score for whether the defect is over the bar. The line of
the defect in the pull request shows the score. When the score is high, `lem land propose` stops one time, and the
agent looks at the defect again. Before an agent files a defect, Lem also asks which items of the
backlog can hold the same defect. Each question sends the place, the title and the text of the
defect to the provider of the model. The second question also sends the title, the place and the
first line of each item. Lem sends nothing when your computer has no `JEV_API_KEY`.

| Setting | Default | Use |
| --- | --- | --- |
| `jev.findings` | `true` | `false` sends no defect and no item of this repository to the model. The line of the defect then says "Jev: not asked (off in the settings)" |

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
| `[seats]` | a seat or `fallback` for this computer, in the same form. It replaces the line of the team. `lem settings set seats.reviewer codex/gpt-6.2-sol:high --local` writes the reviewer, and `lem settings set seats.reviewer default --local` removes it |
| `[naps]` | only `on = false` |
| `[state]` | only `keep_days`: the days for the old files of this computer. Lem uses this number on this computer, also when it is lower or higher than the number of the project |

## `~/.config/lem/settings.toml`

Your settings for every repository on this computer. `lem settings set KEY VALUE --home` writes
a line of `[seats]` or `[ask]` and keeps the other lines. A repository file that names the same
seat wins.

| Setting | Default | Use |
| --- | --- | --- |
| `seats.reviewer`, `seats.planner`, `seats.merger`, `seats.session`, `seats.experts`, `seats.fallback` | as in [`[seats]`](#seats) | each seat and the fallback, in the form of [`[seats]`](#seats) |
| `ask.style` | `"refined"` | the look of the question page: `"refined"`, `"minimal"`, `"bold"` or `"terminal"` |
| `ask.size` | `"auto"` | the size of the question page: a percent of the pane, `"auto"` or `"full"` |
| `ask.review` | `"auto"` | the list of your answers before Lem gets them: `"auto"`, `"always"`, `"never"`, `true` or `false` |
| `ask.browser` | `false` | `true` opens the question page in your browser when you work outside agterm |
| `ask.status` | `{asking = ["blocked"], answered = ["active"]}` | the status of the session while a question waits, and after you answer it |

## `~/.config/lem/machine.toml`

The settings of this computer, for every repository on it. No other file overrides them.
`lem settings set KEY VALUE --machine` writes a line of this file. The other lines, the other
tables and the comments of the file stay, in any form of TOML.

| Setting | Default | Use |
| --- | --- | --- |
| `load.start` | `40` | the load average under which the checks of a landing start. `lem settings set load.start N --machine` sets it, and `lem settings set load.start none --machine` writes `0`, which removes the limit. `lem settings show` gives the load now and whether the checks wait |
| `serve.port` | `4536` | the port of the board server. `lem settings set serve.port N --machine` sets it |
| `serve.tailscale` | `false` | `true` opens the door for your phone. `lem serve door on` and `lem serve door off` set it |
| `serve.tailscale_port` | `4537` | the port of that door. `lem settings set serve.tailscale_port N --machine` sets it |
| `peers.HOST` | none | the port of the door of another computer of the board, with its Tailscale name as `HOST`. `lem serve join HOST` and `lem serve leave HOST` write it |
| `handoff.tokens` | `600000` | the number of tokens where the session of a task compacts. `0` lets Claude Code compact at its own limit. `lem settings set handoff.tokens N --machine` sets it, and `default` gives Lem's number back |
| `corrections.collect` | `false` | `true` turns on [the correction queue](install.md#the-correction-queue) in every repository on this computer. `lem settings set corrections.collect yes --machine` and `lem settings set corrections.collect no --machine` set it |
