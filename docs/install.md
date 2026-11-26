# Install

## What you need

| Tool | Lem uses it for |
| --- | --- |
| [agterm](https://agterm.com) and its skill, from the agterm Help menu | a session for each task, panes and pages |
| [Claude Code](https://code.claude.com/docs) | the agents |
| git, and Python 3.14, which Lem's app brings with it | branches, worktrees, every command of Lem |
| [revmux](https://github.com/umputun/revmux) and its skill | the review before each pull request |
| [cronn](https://cronn.umputun.dev) | the scheduled retro and night run |
| the mailbox chat, webrev and the backlog recipe, from the [agterm cookbook](https://github.com/umputun/agterm/tree/master/cookbook) | the wake-up of a task's session, agent messages, and pages to mark up |
| a remote on GitHub, and the [GitHub CLI](https://cli.github.com) `gh`, signed in | the pull requests, the one way a task lands |
| [Codex](https://github.com/openai/codex): highly recommended | a second model family for the review |
| agdoc, from the agterm cookbook: recommended | a page that you ask for, about an issue, a plan or a change |
| [Plannotator](https://github.com/backnotprop/plannotator): recommended | the Inbox, where what waits for you goes while you are away, also on your phone |
| `JEV_API_KEY`, a key for the Jev decision model: optional | [the correction queue](#the-correction-queue), and a second look at each defect that an agent calls under the bar before a pull request ([`[jev]`](settings.md#jev)) |

`/lem init` checks each tool and says how to install it. `lem doctor` checks them again at any
time.

## Install

Lem has two parts: the app, with the command `lem`, and the plugin for Claude Code. Install the app
one time on your computer:

```bash
brew install pySilver/tap/lem
```

Then run these two commands at the root of your repository:

```bash
claude plugin marketplace add pySilver/lem --scope project
claude plugin install lem@lem --scope project
```

`/lem init` commits `.claude/settings.json` for your team. That file turns Lem on, but it installs
nothing: each person runs the commands in their own clone.

The first time a session reads a file of Lem, Claude Code asks "Allow this read outside the working
directories?". Answer it one time, or put the rule that `lem doctor` gives, such as
`Read(//opt/homebrew/Cellar/lem/**)`, under `permissions`, `allow` in `~/.claude/settings.json`.

## Set up the repository

1. Start Claude Code in agterm, at the root of the repository.
2. Type `/lem init`.
3. Answer three questions: the product and its users, who a change affects, and what must never go
   wrong.
4. Read the page of assumptions, for example who merges. Type `change land owner` to correct one.
5. Type `land`. Lem puts its settings on your base branch through a pull request on GitHub.
6. Type `/lem` and your first request.

Lem assumes auto mode in Claude Code and Codex. A permission prompt stops an agent. On GitHub, Lem
pushes each task and opens its pull request with no question. Your `land` approves this.

A task's worktree has no `.env` file or test database. Put the commands that make them in
[`checks.setup`](settings.md#checks).

## What Lem keeps

In git:

- `.lem/settings.toml`: the [settings](settings.md) of your team.
- `.lem/profile.md`, `.lem/personas/`: the product, and the people that a change affects.
- `.lem/lessons.md`: your corrections of how an agent does a step in this repository.
- `docs/rulings.md`: your decisions about what the product does, one bullet for each, which no
  agent reopens without asking you. A retro only proposes a ruling.
- `docs/plans/`, `docs/backlog/`: the plans, and work for later. The [settings](settings.md#paths)
  can move the plans and the rulings.

Not in git:

- `.lem/settings.local.toml`: your settings for this repository on this computer.
- `.lem/worktrees/`: the worktrees of the tasks.
- `.lem/state/`: the tasks and the board, on this computer only. The board server removes what is
  older than [`state.keep_days`](settings.md#state). It removes no branch, no worktree and no pull
  request.

For all repositories, in `~/.config/lem/` (or `$XDG_CONFIG_HOME/lem/`):

- `owner.json`: whether you are away.
- `settings.toml`: your settings for every repository: your seats, and the look of the question
  page.
- `machine.toml`: the settings of this computer: the load limit, the board server, the other
  computers, the compaction and the correction queue.
- `workspaces.json`, `serve.json`, `serve.log`, `lem.log`: the repositories that the board server
  shows, the server, its output and the faults of Lem.
- `push-key.pem`, `push.json`: the key and the devices of the notifications.

`lem settings show` gives each setting and the file that it comes from.

## The correction queue

With this optional queue, a retro finds a correction that you gave more than one time. A hook sends
each message that you type, with the agent's message before it, to the Jev decision model. Commands
that start with `/` stay local.

The queue is on or off for your computer, in every repository on it. `/lem init` asks you one time
for each computer. When the queue is on, it needs `JEV_API_KEY` in the environment. The default
provider is [OpenRouter](https://openrouter.ai); `JEV_API_URL` names another.

To turn the queue off or on, run one of these commands. Each writes `collect` under
`[corrections]` in `~/.config/lem/machine.toml`, and keeps the other lines of the file. A
repository file cannot turn the queue on or off.

```bash
lem settings set corrections.collect no --machine
lem settings set corrections.collect yes --machine
```
