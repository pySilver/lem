# Settings

Lem reads its settings from four files. An unknown key, a wrong value or a table in the wrong file
stops Lem, and the message names the fix.

## The four files

`~/.config/lem/` is `$XDG_CONFIG_HOME/lem/` when you set that variable.

| File | Whose | In git | What it holds |
| --- | --- | --- | --- |
| `.lem/settings.toml` | the team's, for this repository | yes | the rules that guard a change, and the team's seats. `/lem init` writes it |
| `.lem/settings.local.toml` | yours, for this repository | no | your seats, a no to the [naps](#naps), and the days of the old files on this computer |
| `~/.config/lem/settings.toml` | yours, for every repository on this computer | no | your seats, and the look of the question page |
| `~/.config/lem/machine.toml` | this computer's | no | what is true for the whole computer: the load limit, the board server, the other computers, the compaction and the correction queue |

## Which file wins

A setting that more than one file can hold comes from the nearest file that holds it:

1. `.lem/settings.local.toml`
2. `.lem/settings.toml`
3. `~/.config/lem/settings.toml`
4. Lem's default

This order holds for each seat, for `seats.fallback` and for `state.keep_days`. No other file
overrides `~/.config/lem/machine.toml`. `lem settings show` gives every value and, in `from`, the
file of each value, or "Lem's default".

For each task, Lem reads `.lem/settings.toml` and `.lem/settings.local.toml` from your main checkout.
A task branch cannot change the topics, the checks or who merges.
When your main checkout is on another branch than the base, Lem reads
`.lem/settings.toml` as the newest commit of your base branch has it.

## Change a setting

Edit and commit `.lem/settings.toml` yourself. For the other three files,
`lem settings set KEY VALUE --local`, `--home` or `--machine` writes one line of
`.lem/settings.local.toml`, `~/.config/lem/settings.toml` or `~/.config/lem/machine.toml`. KEY is
`TABLE.KEY`, as in the tables below, such as `load.start`. VALUE `default` removes the line. The
other lines and the comments of the file stay. Lem checks all the settings with the new line
before it writes it. A wrong value in any file stops the command, and the file stays as it was.

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
| `paths.rulings` | `"docs/rulings.md"` | the file of your rulings: `- **The rule in one sentence.** (YYYY-MM-DD)` under the `##` heading of its group |

### `[branch]`

| Setting | Default | Use |
| --- | --- | --- |
| `branch.base` | `/lem init` writes the default branch | the branch that a task starts from and lands on |
| `branch.land` | `"agent"` | who merges. With `"agent"`, Lem merges a [safe change](merge.md#the-merge-review). With `"owner"`, you merge every pull request |
| `branch.history` | `"squash"` | what lands. `"squash"`: one commit. `"keep"`: the commits of the branch |
| `branch.protected` | `[]` | the branches where Lem lands, pushes and deletes nothing, also a task's own branch that you add later |

### `[checks]`

During the build, each builder runs only the tests of its own change. Before the pull request, Lem
runs the commands below one time, in the worktree of the task. When you change `checks.commands` or
`checks.serial`, a task whose checks passed runs them again before its pull request and its merge.

| Setting | Default | Use |
| --- | --- | --- |
| `checks.commands` | `[]` | your tests, the whole suite. Add a linter only when no git hook runs it. With no command, only the task that adds one can land |
| `checks.serial` | `[]` | the tests that two tasks cannot run at the same time, such as an end-to-end suite with fixed ports. They run after `checks.commands`, one task at a time |
| `checks.setup` | `[]` | what a new worktree needs before its tests can run, such as `"uv sync"` or `"npm ci"` |

### `[flow]`

| Setting | Default | Use |
| --- | --- | --- |
| `flow.topics` | `[]` | what must never go wrong, one sentence each: `"a customer is charged the wrong amount"`. `/lem init` proposes them from your code. A change that can affect one is careful |

### `[seats]`

A seat is one string, `agent/model:effort`. `seats.reviewer`, `seats.merger`, `seats.fallback` and
each of `seats.experts` take `claude` or `codex`. `seats.planner` and `seats.session` take only
`claude`. Write all three parts, except in `seats.merger` and `seats.session`, where a part that
you leave out takes the default of the agent. A persona names its own seats in the frontmatter of
its file, in the same form: `seats: ["claude/opus:high"]`. A persona file without it uses the
seats of the panel.

The **plan talk** comes before the build of a careful plan, or of a plan with more than three
parts. The planner defends the plan, and the reviewer argues against it.

When the reviewer, the planner or the merge agent gives an error, `seats.fallback` starts in its
place, and the task goes on. An error is a missing program, login or model, no tokens, or a usage
limit. A slow agent is not an error. The pull request names the seat that stood in, the seat that
failed and the error, and green does not change. With `fallback = false`, or when the fallback
cannot stand in, the task waits for you. Type "go on" in its session, and Lem tries the seat again.

| Setting | Default | Use |
| --- | --- | --- |
| `seats.reviewer` | `"claude/opus:high"` | the reviewer of the plan talk. `/lem init` writes `"codex/gpt-6.2-sol:high"`, or `"claude/opus:high"` without Codex |
| `seats.planner` | `"claude/opus:high"` | the planner of the plan talk |
| `seats.merger` | `"claude/opus:high"` | the merge agent |
| `seats.session` | `"claude/opus:high"` | the agent of the session of each task |
| `seats.experts` | `["claude/fable:high", "codex/gpt-6.2-astra:high"]` | one or two experts for a decision in doubt. Without Codex, one answers alone |
| `seats.fallback` | `"claude/opus:high"` | the seat in place of a reviewer, planner or merge agent that gives an error. `false` turns it off |

### `[naps]`

A nap is an optional agent that reads the recent tasks, and leaves a note for the retro.

| Setting | Default | Use |
| --- | --- | --- |
| `naps.on` | `false` | `true` turns the naps on |

### `[state]`

Lem keeps the files of its work in `.lem/state/`, which git does not see. Each hour, the board
server removes the old files from it. An ended task with no new activity for `state.keep_days` days
keeps only a small record. The record holds its state, its request, its pull request, and the files
for its ticket and for `/lem resume`. Its events become one summary event. The board still shows the task in Done,
and its Overview tells you what stayed. A retro or a nap then finds no report and no decisions of
the task, and `/lem resume` cannot start a dropped task again. Type `/lem` and its request to start
a new task. The same limit applies to unused files of expert questions, persona panels, naps and
copies of personas. `lem prune --dry-run --days 7` shows what a number removes, and changes nothing.

| Setting | Default | Use |
| --- | --- | --- |
| `state.keep_days` | `30` | the days after the last event of a task, or the last write of a folder, after which its old files go. A whole number, `1` or more |

### `[jev]`

Before a pull request, Lem asks the Jev decision model about each defect outside the task that an
agent calls under the [bar](pull-request.md#what-lem-saw-outside-the-task). Jev gives a score for whether the defect is over the bar, and the line of
the defect in the pull request shows it. When the score is high, `lem land propose` stops one time,
and the agent looks at the defect again. Before an agent files a defect, Lem also asks which items
of the backlog can hold the same defect. Each question sends the place, the title and the text of
the defect to the provider of the model. The second question also sends the title, the place and
the first line of each item. Lem sends nothing when your computer has no `JEV_API_KEY`.

| Setting | Default | Use |
| --- | --- | --- |
| `jev.findings` | `true` | `false` sends no defect and no item of this repository to the model. The line of the defect then says "Jev: not asked (off in the settings)" |

### `[tracker]`

Leave this table out with no tracker. [Start from a ticket](tickets.md) tells you how to fill it.

| Setting | Default | Use |
| --- | --- | --- |
| `tracker.kind` | required | `"linear"` or `"github"`, the one key of the table |

## `.lem/settings.local.toml`

Git does not track this file. It holds your settings for this repository on this computer:
`[seats]`, `[naps]` with only `on = false`, and `[state]` with only `keep_days`. Each has the form
of its table above.

## `~/.config/lem/settings.toml`

Your settings for every repository on this computer.

| Setting | Default | Use |
| --- | --- | --- |
| `seats.reviewer`, `seats.planner`, `seats.merger`, `seats.session`, `seats.experts`, `seats.fallback` | as in [`[seats]`](#seats) | each seat and the fallback, in the form of [`[seats]`](#seats) |
| `ask.style` | `"refined"` | the look of the question page: `"refined"`, `"minimal"`, `"bold"` or `"terminal"` |
| `ask.size` | `"auto"` | the size of the question page: a percent of the pane, `"auto"` or `"full"` |
| `ask.review` | `"auto"` | the list of your answers before Lem gets them: `"auto"`, `"always"`, `"never"`, `true` or `false` |
| `ask.browser` | `false` | `true` opens the question page in your browser when you work outside agterm |
| `ask.status` | `{asking = ["blocked"], answered = ["active"]}` | the status of the session while a question waits, and after you answer it |

## `~/.config/lem/machine.toml`

The settings of this computer, for every repository on it.

| Setting | Default | Use |
| --- | --- | --- |
| `load.start` | `40` | the load average under which the checks of a landing start. `none` writes `0`, which removes the limit. `lem settings show` gives the load now |
| `serve.port` | `4536` | the port of the board server |
| `serve.tailscale` | `false` | `true` opens the door: a second port of the board server, which only your Tailscale login reaches. `lem serve door on` and `lem serve door off` set it |
| `serve.tailscale_port` | `4537` | the port of that door |
| `peers.HOST` | none | the door port of another computer of the board, by its Tailscale name. `lem serve join HOST` and `lem serve leave HOST` write it |
| `handoff.tokens` | `600000` | the tokens at which the session of a task compacts. `0` lets Claude Code compact at its own limit |
| `corrections.collect` | `false` | `true` turns on [the correction queue](install.md#the-correction-queue) in every repository on this computer |

## Other files of Lem

In git:

- `.lem/settings.toml`: the settings of your team.
- `.lem/profile.md`: the product. `.lem/personas/`: the people that a change affects.
- `.lem/lessons.md`: your corrections of how an agent does a step in this repository.
- `docs/rulings.md`: your decisions about what the product does, one bullet for each, which no
  agent reopens without asking you. A retro only proposes a ruling.
- `docs/plans/`, `docs/backlog/`: the plans, and work for later. [`[paths]`](#paths) can move the
  plans and the rulings.

Not in git:

- `.lem/settings.local.toml`: your settings for this repository on this computer.
- `.lem/worktrees/`: the worktrees of the tasks.
- `.lem/state/`: the tasks, the board and the reviewer's items, on this computer only. The board
  server removes what is older than [`state.keep_days`](#state). It removes no branch, no worktree
  and no pull request.

In `~/.config/lem/`, for all repositories:

- `owner.json`: whether you are away.
- `settings.toml` and `machine.toml`: the two files above.
- `workspaces.json`, `serve.json`, `serve.log`, `lem.log`: the repositories that the board server
  shows, the server, its output and the faults of Lem.
- `push-key.pem`, `push.json`: the key and the devices of the
  [notifications](phone.md#the-key-and-the-devices). The board server makes both. You supply no key.
