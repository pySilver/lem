# Install

## What you need

`/lem init` gives the install steps. `lem doctor` checks the tools.

### Required

- [agterm](https://agterm.com) for task sessions and pages.
- [agterm skill](https://agterm.com) from the agterm Help menu.
- [Claude Code](https://code.claude.com/docs) for the agents.
- [lem-builder agent](#install) from the Lem plugin for Claude Code.
- [git](https://git-scm.com) for branches and worktrees.
- [Python 3.14](https://www.python.org/downloads/) comes with the Lem app.
- [revmux](https://github.com/umputun/revmux) for review rounds.
- [revmux skill](https://github.com/umputun/revmux) for agents that run reviews.
- [mailbox-chat](https://github.com/umputun/agterm/tree/master/cookbook/two-agent-mailbox-chat#setup) for agent messages and session wake-ups.
- [mailbox-chat skill](https://github.com/umputun/agterm/tree/master/cookbook/two-agent-mailbox-chat#setup) from the same recipe.
- [webrev skill](https://github.com/umputun/agterm/tree/master/cookbook/annotate-document) to mark up documents.
- [backlog skill](https://github.com/umputun/agterm/tree/master/cookbook/backlog-picker) to add and open backlog items.
- [cronn](https://cronn.umputun.dev) for scheduled retro and night runs.

### Recommended

- [Codex](https://github.com/openai/codex) for a second model family in reviews.
- [agdoc skill](https://github.com/umputun/agterm/tree/master/cookbook/html-doc-overlay) for pages about issues, plans or changes.
- [plannotator-tui](https://github.com/umputun/agterm/tree/master/cookbook/annotate-in-plannotator-tui) to mark up pane text. [Plannotator](https://github.com/backnotprop/plannotator) shows plans and code reviews.

### Optional

- [GitHub CLI](https://cli.github.com) for pull requests. If your remote is on GitHub, install `gh` and sign in.
- [Plannotator Inbox](https://plannotator.ai/inbox/) for [what waits for you while you are away](away.md#answer-from-the-inbox).
- [`JEV_API_KEY`](settings.md#jev) for Jev. The [correction queue](#the-correction-queue) needs this key when it is on.
- [codex persona agent](https://github.com/pySilver/lem/tree/main/skills/lem-panel) for the second half of a persona panel.
- [task picker](board.md#open-it) to open a task board from a key in agterm. `lem doctor` gives the keymap line.

[Update and remove](update.md#remove) gives the steps to remove Lem and its `.lem/` folder.

## Install

Lem has two parts: the app, with the command `lem`, and the plugin for Claude Code.
Install the app once.

```bash
brew install pySilver/tap/lem
```

Install the plugin from the root of your repository.

```bash
claude plugin marketplace add pySilver/lem --scope project
claude plugin install lem@lem --scope project
```

`/lem init` commits `.claude/settings.json` only if git does not track it and it has only the two
Lem entries. They are `extraKnownMarketplaces` for `lem` and `enabledPlugins` for `lem@lem`.
Commit any other `.claude/settings.json` yourself. Each person installs Lem in their own clone
unless they already have it for every repository.

The first time a session reads a file of Lem, Claude Code asks for permission to read outside the
working directories. Answer it one time, or put the rule that `lem doctor` gives, such as
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

Run one command to set `collect` in `[corrections]` of `~/.config/lem/machine.toml`.
The other lines stay. A repository file cannot control the queue.

```bash
lem settings set corrections.collect no --machine
lem settings set corrections.collect yes --machine
```
