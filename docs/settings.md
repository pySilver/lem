# The settings

`.lem/project.toml` holds the settings of a project, and git tracks it. `/lem init` writes it,
and `lem project show` prints it with each value resolved.

- An unknown table or key, a wrong type, and a path outside the repository are errors. Lem names
  the error and the fix, and it stops.
- Lem reads the settings from your main checkout. An edit there counts at once, even before you
  commit it.
- If the main checkout is on another branch, Lem reads the settings from the newest commit of the
  base branch. It tells you so in one line.
- A task's branch cannot change the rules that guard it: the topics, the checks, who merges.
- A change that edits `.lem/project.toml` is careful, and a person merges it.

## `[paths]`

Each path is relative to the root of the checkout. It must name a folder or a file inside the
repository, not the root.

| Setting | Default | Meaning |
| --- | --- | --- |
| `paths.profile` | `.lem/profile.md` | what the project is |
| `paths.styleguide` | `.lem/styleguide`, or `.claude/rules` when that folder holds rules | the rule files for the code. If both folders hold rules, Lem reads both |
| `paths.personas` | `.lem/personas` | one file for each person that a change affects |
| `paths.review` | `.revmux` | the folder of the review tool |
| `paths.lessons` | `.lem/lessons.md` | the corrections that have no better place |
| `paths.rulings` | `docs/rulings` | your decisions that hold for later tasks |
| `paths.backlog` | `docs/backlog` | work for later |
| `paths.plans` | `docs/plans` | the plan of each full change |
| `paths.plan_file` | `"YYYY-MM-DD-<slug>.md"` | the name of a plan file. It takes the tokens `YYYY`, `MM`, `DD` and `<slug>`. Lem also finds a plan named `YYYYMMDD-<slug>.md` |
| `paths.worktrees` | `.lem/worktrees` | the worktrees of the tasks |

If a repository already keeps a profile, personas or worktrees for another tool, `/lem init`
gives you a choice. Lem links those folders, or it starts its own layout beside them. Lem moves no
file.

At its top, between two `---` lines, a rule file can name the files that it applies to:

```markdown
---
paths:
  - "app/**/*.py"
  - "tests/**/*.py"
---
```

A rule file with no `paths:` applies to all files. Each builder and each reviewer gets the rule
files for the files that it changes or reads.

## `[branch]`

| Setting | Default | Meaning |
| --- | --- | --- |
| `branch.base` | the default branch of `origin` | the branch that tasks start from and land on |
| `branch.land` | `"owner"` | who merges: `owner`, or `agent`. An agent merges only a pull request that is green and that the review called not careful |
| `branch.history` | `"keep"` | what lands: the commits of the branch (`keep`), or one commit (`squash`) |
| `branch.propose` | `"pull-request"` | how a task ends with a remote on GitHub: a pull request (`pull-request`), or a merge into the base branch with no pull request (`merge`). With another remote, or with none, a task always ends with the merge. With `pull-request`, Lem pushes the branch of each task and opens its pull request, and it does not ask you first: this value is your approval |
| `branch.protected` | `[]` | the branches where Lem lands nothing and pushes nothing |

The base branch must not be in `branch.protected`.

## `[checks]`

The checks are the commands that must pass before a pull request: your tests, and a linter or a
type checker if no git hook runs them.

| Setting | Default | Meaning |
| --- | --- | --- |
| `checks.commands` | `[]` | the whole suite, run one time before the pull request, at the root of the worktree of the task. With no command, Lem proposes no change. The one exception is the task that adds the commands |
| `checks.alone` | `[]` | the commands that must run alone on the computer, for example an end-to-end suite with fixed ports, one database or a browser. Lem runs each under one lock for the repository, after `checks.commands` pass |
| `checks.setup` | `[]` | the commands that a new worktree needs before its tests can start, for example an install of the packages |
| `checks.ignores` | `[]` | the paths that the checks do not read. If the base branch changes only in these paths after green checks, the result stays valid. A `*` also matches across folders |
| `checks.bar` | `[]` | extra regular expressions that find a mark of a lowered bar, for a language that Lem has no marks for |

An empty command is an error, because it passes and runs nothing. Lem has its own bar marks for
Python, JavaScript, TypeScript, Go, Rust, Java, Kotlin and shell.

A Python project with no git hooks:

```toml
[checks]
commands = [
  "uv run ruff check .",
  "uv run mypy src",
  "uv run pytest -q --ignore=tests/e2e",
]
alone = ["uv run pytest -q tests/e2e"]
setup = ["uv sync"]
ignores = ["docs/*"]
```

A JavaScript project where husky runs the linter and the type checker at each commit:

```toml
[checks]
commands = ["npm test"]
alone = ["npx playwright test"]
setup = ["npm ci"]
ignores = ["docs/*"]
```

## `[flow]`

| Setting | Default | Meaning |
| --- | --- | --- |
| `flow.topics` | `[]` | what must never go wrong, each as one sentence in your words, for example "a customer is charged the wrong amount" |
| `flow.max_tasks` | `4` | how many tasks build or land at one time. A task over the limit waits in the queue. Lower it when the tests share one database or use a browser |
| `flow.decision_wait` | `15` | how many minutes a decision of yours waits for your answer. Then the lead takes the option that both experts chose, or else the recommended option, and the pull request is not green because of it |
| `flow.watch_seconds` | `60` | how many seconds the watch of the open pull requests waits between two looks at GitHub |

## `[seats]`

A seat names the agent, the model and the effort for one role, as one string:
`agent/model:effort`.

| Setting | Default | Meaning |
| --- | --- | --- |
| `seats.reviewer` | none. `/lem init` writes `codex` when the machine check finds Codex, otherwise `claude`. With no seat, Lem asks you once | the reviewer of the plan talk: `claude` or `codex` |
| `seats.planner` | none: `claude`, with the model and the effort of the agent | the defender of the plan talk: only `claude` |
| `seats.experts` | `["claude/fable", "codex/gpt-6-astra:high"]` | the two experts, from two model families, that answer a question or a choice of yours |

```toml
[seats]
reviewer = "codex/gpt-6.1-sol:high"
planner = "claude/opus:high"
experts = ["claude/fable", "codex/gpt-6-astra:high"]
```

A seat can leave out the effort (`codex/gpt-6.1-sol`), or the model and the effort (`codex`). The
agent then uses its own default for that part. An empty seat, or a seat with a space, is an error.
The review before a pull request does not use the reviewer of this seat: it is a new agent with
the review tool.

## `[tools]`

| Setting | Default | Meaning |
| --- | --- | --- |
| `tools.annotate` | `"webrev"` | the tool that you use to mark up a plan or a draft. webrev does not come with Lem: it is a recommended tool |
| `tools.ask` | `"lem-ask"` | how a question comes to you: Lem's page, `terminal` for a list in the conversation, or your own skill or command |

## `[corrections]`

| Setting | Default | Meaning |
| --- | --- | --- |
| `corrections.collect` | `false` | `true` keeps a queue of your corrections for `/lem retro`, for each person who works in the repository |

The hook sends each message that a person types, with the agent's message before it, to the Jev
decision model through OpenRouter. It does not send a command that starts with `/`.
[install.md](install.md#the-correction-queue) gives the details.

## `[naps]`

| Setting | Default | Meaning |
| --- | --- | --- |
| `naps.on` | `false` | `true` lets Lem take a nap in the background when it ends a task or waits for you |
| `naps.keep_days` | `30` | how many days Lem keeps the folder of a nap |
| `naps.gap_hours` | `6` | how many hours must pass after the last nap before Lem takes a new one |

[inside.md](inside.md#naps) says what a nap does.

## `[tracker]`

The table is absent when the project has no tracker. Lem supports only Linear.

| Setting | Default | Meaning |
| --- | --- | --- |
| `tracker.kind` | required | `linear` |
| `tracker.server` | required | the name that the agent gives to the MCP server of the tracker |
| `tracker.workspace` | required | the workspace, as its address has it: `acme` for `linear.app/acme` |
| `tracker.team` | required | the key of the one team whose tickets this project takes |
| `tracker.moves` | required | who changes the status of a ticket: `lem`, or `tracker` when the automation of the tracker does it |
| `tracker.started` | required with `moves = "lem"` | the status of a ticket whose work started, as the team spells it |
| `tracker.landed` | required with `moves = "lem"` | the status of a ticket whose work landed. It must not be the same as `started` |

With `moves = "tracker"`, Lem moves no ticket, and `started` and `landed` must be absent.
[linear.md](linear.md) tells you how to connect a project to Linear.

## `.lem/project.local.toml`

This file is for one computer. Git does not track it, and Lem reads it from the main checkout. A
change that puts this file into git is careful, and a person merges it.

It can hold these tables, and no other:

| Table | What it can say |
| --- | --- |
| `[seats]` | a seat that replaces the seat of the project on this computer, in the same form: `reviewer = "codex/gpt-6.1-sol:high"`. `/lem reviewer` writes the reviewer seat, and `/lem reviewer default` removes it |
| `[tools]` | `annotate` and `ask`, as in `.lem/project.toml` |
| `[corrections]` | only `collect = false`. Then the hook sends no message from this computer |
| `[naps]` | only `on = false`. Then Lem takes no nap by itself on this computer. `/lem nap` still works |
| `[flow]` | only `max_tasks`: the limit of tasks for this computer |

The file can turn the correction queue and the naps off, but never on. The topics, the checks,
the protected branches and who merges are rules of the project, so this file cannot change them.
`lem project show` lists each setting that this file changes, under `local`.
