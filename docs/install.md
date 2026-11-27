# Install

## What you need

Lem lands each task through a pull request on GitHub, so the `origin` remote of your repository
must be on GitHub. Lem assumes auto mode in Claude Code and Codex. A permission prompt stops an
agent.

`/lem init` gives the install steps. `lem doctor` checks the tools.

### Required

- [agterm](https://agterm.com) for task sessions and pages.
- [agterm skill](https://agterm.com) from the agterm Help menu.
- [Claude Code](https://code.claude.com/docs) for the agents.
- [lem-builder agent](#install) from the Lem plugin for Claude Code.
- [git](https://git-scm.com) for branches and worktrees.
- [GitHub CLI](https://cli.github.com) for pull requests and issues. Install `gh` and sign in with
  `gh auth login`.
- [Python 3.14](https://www.python.org/downloads/) comes with the Lem app.
- [revmux](https://github.com/umputun/revmux) for review rounds.
- [revmux skill](https://github.com/umputun/revmux) for agents that run reviews.
- [mailbox-chat](https://github.com/umputun/agterm/tree/master/cookbook/two-agent-mailbox-chat#setup) for agent messages and session wake-ups.
- [mailbox-chat skill](https://github.com/umputun/agterm/tree/master/cookbook/two-agent-mailbox-chat#setup) from the same recipe.
- [webrev skill](https://github.com/umputun/agterm/tree/master/cookbook/annotate-document) to mark up documents.
- [backlog skill](https://github.com/umputun/agterm/tree/master/cookbook/backlog-picker) to add and open backlog items.
- [cronn](https://cronn.umputun.dev) for scheduled retro and night runs.

### Recommended

- [Codex](https://github.com/openai/codex) for a second model family. It reviews the larger
  changes and answers as a second expert. Codex is optional and highly recommended.
- [agdoc skill](https://github.com/umputun/agterm/tree/master/cookbook/html-doc-overlay) for pages about issues, plans or changes.
- [plannotator-tui](https://github.com/umputun/agterm/tree/master/cookbook/annotate-in-plannotator-tui) to mark up pane text. [Plannotator](https://github.com/backnotprop/plannotator) shows plans and code reviews.

### Optional

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

Lem pushes each task and opens its pull request on GitHub with no question. Your `land` approves
this.

A task's worktree has no `.env` file or test database. Put the commands that make them in
[`checks.setup`](settings.md#checks).

## What Lem keeps

[The files of Lem](settings.md#other-files-of-lem) lists what Lem keeps in git, outside git and in
`~/.config/lem/`. `lem settings show` gives each setting and the file that it comes from.

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
