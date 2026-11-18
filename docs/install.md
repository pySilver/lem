# Install, update, remove

## What you need

| Tool | Lem uses it for |
| --- | --- |
| [agterm](https://agterm.com) and its skill, from the agterm Help menu | sessions, panes and pages |
| [Claude Code](https://code.claude.com/docs) | the agents |
| git, and Python 3.11 or newer as `python3` | branches, worktrees, scripts |
| [revmux](https://github.com/umputun/revmux) and its skill | the review before each pull request |
| [cronn](https://cronn.umputun.dev) | the scheduled retro and night run |
| the mailbox chat, webrev, agdoc and the backlog recipe, from the [agterm cookbook](https://github.com/umputun/agterm/tree/master/cookbook) | the messages between agents, and the pages that you read and mark up |
| the [GitHub CLI](https://cli.github.com) `gh`, signed in: only with a remote on GitHub | the pull requests on GitHub |
| [Codex](https://github.com/openai/codex): optional, highly recommended | a second model family. Without it, Claude reviews the work of Claude |
| a key for the Jev decision model, `JEV_API_KEY`: required when [the correction queue](#the-correction-queue) is on | the correction queue, and a check of each question card |

`/lem init` checks each tool, and tells you how to install one that is absent.

## Install

Run these two commands at the root of your repository, and commit `.claude/settings.json`. Then
each person who works in the repository gets Lem.

```bash
claude plugin marketplace add pySilver/lem --scope project
claude plugin install lem@lem --scope project
```

## Set up the repository

1. Start Claude Code in agterm, at the root of the repository.
2. Type `/lem init`.
3. Answer three questions: what the product is and who it is for, who a change affects, and what
   must never go wrong.
4. Read the page that Lem shows. It lists what Lem assumed, for example who merges. To correct an
   item, type `change` and the correction: `change land agent`.
5. Type `land`. Lem puts its settings on your base branch.
6. Type `/lem` and your first request, in one sentence.

Lem assumes that Claude Code and Codex run in auto mode: a builder works in the background, and
a permission prompt stops it until you answer.

> [!NOTE]
> With a remote on GitHub, Lem pushes the branch of each task and opens its pull request without
> a question. Your `land` at the end of `/lem init` approves this.

A worktree of a task has no `.env` file and no test database. If your tests need them, name a
script in `AGENTS.md` that prepares a worktree.

## What Lem keeps in your repository

| Path | In git | What it holds |
| --- | --- | --- |
| `.lem/project.toml` | yes | the [settings](settings.md) |
| `.lem/profile.md` | yes | what the product is |
| `.lem/personas/` | yes | the people that a change affects |
| `.lem/lessons.md` | yes | how agents work here. A line that starts with a stage name, such as `new:`, corrects that stage of Lem |
| `docs/plans/` | yes | the plan of each task on the standard track |
| `docs/backlog/` | yes | work for later |
| `docs/rulings/` | yes | your decisions about the product |
| `.claude/rules/` | yes | your rules for the code. Lem reads them, and writes none |
| `.revmux/` | yes | the folder of the review tool |
| `.lem/project.local.toml` | no | the settings of this computer |
| `.lem/worktrees/`, `.lem/state/` | no | the worktrees, the tasks and the board |

The [settings](settings.md#paths) can name another folder for the plans and for the rulings. Each
other path is fixed: if your repository keeps one in another folder, move it with `git mv`.

## The correction queue

With this optional queue, a retro finds a correction that you gave two times or more. A hook sends
each message that you type, with the agent's message before it, to the Jev decision model. It uses
the key of the person who typed it. Commands that start with `/` stay local.

`corrections.collect = true` turns it on for each person in the repository. Each person then puts
a key into the environment as `JEV_API_KEY`, and `/lem init` stops without one. The default
provider is [OpenRouter](https://openrouter.ai). For another provider, set `JEV_API_URL`. To say no for
yourself, put `collect = false` under `[corrections]` in `.lem/project.local.toml`.

## Update

Run these two commands, then start a new session.

```bash
claude plugin marketplace update lem
claude plugin update lem@lem --scope project
```

## Remove

1. Land or drop each open task.
2. Remove the scheduled jobs of this repository in cronn.
3. Run `claude plugin uninstall lem@lem --scope project`.
4. Run `claude plugin marketplace remove lem --scope project`.
5. Remove the allow rules of Lem from `.claude/settings.json`.
6. Run `git rm -r .lem`, and commit with the change of step 5.
7. Delete the folder `.lem/`, which still holds the files that git does not track.
8. If no other repository uses Lem, delete `~/.cache/lem-ask/` and `$TMPDIR/lem-ask/`.
