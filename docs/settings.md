# The settings

`.lem/project.toml` holds the rules of a project, in git. `/lem init` writes it, and
`python3 skills/lem/scripts/project.py show` prints it resolved. This page follows `TABLES`,
`PATHS` and `TEMPLATE` in `skills/lem/scripts/project.py`, one key for each row.

- An unknown table or key, a wrong type, and a path outside the repository are errors. Lem names
  the error and stops, because a stage that read half of the file would use defaults that nobody
  chose.
- Lem reads the `[flow]` table from the main checkout, also in the worktree of a task. Thus a
  branch cannot change the topics or the wait that guard it.
- The landing reads each setting from the main checkout.

## `[paths]`

Each path is relative to the root of the checkout. It must name a folder or a file inside the
repository, not the root.

| Setting | Default | Meaning |
| --- | --- | --- |
| `paths.profile` | `.lem/profile.md` | what the project is |
| `paths.styleguide` | `.lem/styleguide`; `/lem init` writes `.claude/rules` when that folder holds rules | the rule files for the code. If the two folders are there, Lem reads the two |
| `paths.personas` | `.lem/personas` | one file for each person that a change affects |
| `paths.review` | `.revmux` | the folder of the review tool |
| `paths.lessons` | `.lem/lessons.md` | the corrections that have no better place |
| `paths.rulings` | `docs/rulings` | your decisions that hold for later tasks |
| `paths.backlog` | `docs/backlog` | work for later |
| `paths.plans` | `docs/plans` | the plan of each feature |
| `paths.worktrees` | `.lem/worktrees` | the worktrees of the tasks |

A repository that already keeps a profile, personas or worktrees for a different tool gets a
choice at `/lem init`: `--existing link` names those folders, and `--existing new` starts the
layout of Lem. Lem moves no file.

A rule file can name the files that it applies to, at its top, between two `---` lines:

```markdown
---
paths:
  - "app/**/*.py"
  - "tests/**/*.py"
---
```

A rule file without `paths:` applies to all files. `project.py rules FILE ...` gives the rule
files for a change. Each builder and each reviewer gets them.

## `[branch]`

| Setting | Default | Meaning |
| --- | --- | --- |
| `branch.base` | the default branch of `origin`, which `/lem init` writes; `--base NAME` without one | the branch that tasks start from and land on |
| `branch.land` | `owner` | who merges: `owner`, or `agent`, which merges only a request that is green and that the review called not careful |
| `branch.history` | `keep` | what lands: the commits of the branch (`keep`), or one commit (`squash`) |
| `branch.propose` | `pull-request` | how a task ends with a remote on GitHub: a pull request (`pull-request`), or a merge into the base branch with no pull request (`merge`). With a different remote, or none, it is always the merge. With `pull-request`, Lem pushes the branch of each task and opens its pull request, and it does not ask you first: this value is your approval |
| `branch.protected` | `[]` | the branches that nothing lands on and nothing is pushed to |

The base branch must not be in `branch.protected`.

## `[gate]`

| Setting | Default | Meaning |
| --- | --- | --- |
| `gate.commands` | `[]` | the check commands, each run at the root of the task's worktree. With none, Lem proposes no change, except the task whose branch adds them |
| `gate.ignores` | `[]` | the paths that the gate does not read. If the base branch moves only by these files after a green gate, the result stays. A `*` crosses folders |
| `gate.setup` | `[]` | the commands that a new worktree needs before its tests can start, for example an install of the packages. The check of the stories runs them in its own worktree |
| `gate.bar` | `[]` | more regular expressions for a mark that lowers the bar, for a language that Lem has no marks for |

An empty command in `gate.commands` or `gate.setup` is an error, because it passes and runs
nothing. Lem has its own marks for Python, JavaScript, TypeScript, Go, Rust, Java, Kotlin and
shell.

## `[flow]`

| Setting | Default | Meaning |
| --- | --- | --- |
| `flow.topics` | `[]` | what must never go wrong, each as one sentence in your words, for example "a customer is charged the wrong amount" |
| `flow.max_tasks` | `4` | how many tasks build or land at one time. A task over the limit waits in a queue |
| `flow.decision_wait` | `15` | how many minutes a decision that is yours waits for your answer. Then the lead takes the option of the two experts, or the recommended option, and the pull request is not green for it |

- `flow.careful` is refused, with the sentence to write in `flow.topics` in its place.
  [flow.md](flow.md#careful) says why.
- Four to five tasks ran well on one Mac. Six gave a load average of 12 to 16 and unstable browser
  tests (convertiser-server, as its owner reported it on 2026-11-14). Lower `max_tasks` when the
  tests share one database or drive a browser.

## `[seats.reviewer]` and `[seats.planner]`

| Setting | Default | Meaning |
| --- | --- | --- |
| `seats.reviewer.agent` | the value of `/lem init --reviewer`: Codex when the check finds it | the reviewer of a plan talk: `claude` or `codex` |
| `seats.reviewer.model` | the default of the agent | the model of the reviewer |
| `seats.reviewer.plan_effort` | the default of the agent | the effort of the reviewer in a plan talk |
| `seats.planner.agent` | Claude Code | the defender of a plan talk: only `claude` |
| `seats.planner.model` | the default of the agent | the model of the defender |
| `seats.planner.effort` | the default of the agent | the effort of the defender |

- A seat that names a model or an effort must also name its agent.
- An old file with `seats.reviewer.effort` still reads, and Lem does not use that key.
- The review before a pull request is a new agent, not the reviewer of this seat.

## `[tools]`

| Setting | Default | Meaning |
| --- | --- | --- |
| `tools.annotate` | `webrev` | the tool with which you mark a plan or a draft. webrev is a recommended tool that you install |
| `tools.ask` | `lem-ask` | how a question comes to you: the page of Lem, `terminal` for a list in the conversation, or your own skill or command |

## `[corrections]`

| Setting | Default | Meaning |
| --- | --- | --- |
| `corrections.collect` | `false` | `true` keeps a queue of corrections for `/lem retro`, for each person who works in the repository with the hook |

The hook sends each message that a person types, with the agent message before it, to the Jev
decision model through OpenRouter. It does not send a command that starts with `/`. `true` in git
is a yes for each person who works in the repository with the hook. [install.md](install.md#the-correction-hook)
says how the hook gets there.

## `[tracker]`

The table is absent when the project has no tracker. Linear is the one tracker now.

| Setting | Default | Meaning |
| --- | --- | --- |
| `tracker.kind` | necessary | `linear` |
| `tracker.server` | necessary | the name of the MCP server of the tracker in the agent |
| `tracker.workspace` | necessary | the workspace, as in its address `linear.app/acme` |
| `tracker.team` | necessary | the key of the one team whose tickets this project takes |
| `tracker.moves` | necessary | who changes the status of a ticket: `lem`, or `tracker` for the automation of the tracker |
| `tracker.started` | necessary with `moves = "lem"` | the status of a ticket whose work started, as the team spells it |
| `tracker.landed` | necessary with `moves = "lem"` | the status of a ticket whose work landed. It must not be the same as `started` |

With `moves = "tracker"`, Lem moves no ticket, and `started` and `landed` must be absent.
[linear.md](linear.md) says how a project connects Linear.

## `.lem/project.local.toml`

This file is for one computer. Git does not track it, and Lem reads it from the main checkout.

- It can hold `[seats]`, `[tools]` and `[corrections]`, and no other table.
- A seat here replaces the seat of the project for this computer. `/lem reviewer` writes the
  reviewer seat, and `/lem reviewer default` removes it. You write the defender seat yourself,
  under `[seats.planner]`.
- `[corrections]` can say `collect = false`. Then the hook sends no message from this computer.
  The file cannot say `collect = true`.
- `project.py show` lists each setting that this file changes, under `local`.
