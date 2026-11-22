# Install, update, remove

## What you need

| Tool | Lem uses it for |
| --- | --- |
| [agterm](https://agterm.com) and its skill, from the agterm Help menu | a session for each task, panes and pages |
| [Claude Code](https://code.claude.com/docs) | the agents |
| git, and Python 3.11 or newer: `python3`, a `python3.N` on `PATH`, the Homebrew Python, or a Python that uv has | branches, worktrees, scripts |
| [revmux](https://github.com/umputun/revmux) and its skill | the review before each pull request |
| [cronn](https://cronn.umputun.dev) | the scheduled retro and night run |
| the mailbox chat, webrev and the backlog recipe, from the [agterm cookbook](https://github.com/umputun/agterm/tree/master/cookbook) | the wake-up of a task's session, agent messages, and pages to mark up |
| a remote on GitHub, and the [GitHub CLI](https://cli.github.com) `gh`, signed in | the pull requests, the one way a task lands |
| [Codex](https://github.com/openai/codex): highly recommended | a second model family for the review |
| agdoc, from the agterm cookbook: recommended | a page that you ask for, about an issue, a plan or a change |
| `JEV_API_KEY`, a key for the Jev decision model: optional | [the correction queue](#the-correction-queue) |

`/lem init` checks each tool and says how to install it.

## Install

Run these two commands at the root of your repository. `/lem init` commits `.claude/settings.json`
for your team.

```bash
claude plugin marketplace add pySilver/lem --scope project
claude plugin install lem@lem --scope project
```

## Set up the repository

1. Start Claude Code in agterm, at the root of the repository.
2. Type `/lem init`.
3. Answer three questions: the product and its users, who a change affects, and what must never go
   wrong.
4. Read the page of assumptions, for example who merges. Type `change land owner` to correct one.
5. Type `land`. Lem puts its settings on your base branch through a pull request on GitHub.
6. Type `/lem` and your first request.

Lem assumes auto mode in Claude Code and Codex. A permission prompt stops an agent.

> [!NOTE]
> On GitHub, Lem pushes each task and opens its pull request with no question. Your `land` approves
> this.

A task's worktree has no `.env` file or test database. Put the commands that make them in
[`checks.setup`](settings.md#checks).

## What Lem keeps

In git:

- `.lem/project.toml`: the [settings](settings.md).
- `.lem/profile.md`, `.lem/personas/`: the product, and the people that a change affects.
- `.lem/lessons.md`: your corrections of how an agent does a step in this repository.
- `docs/rulings.md`: your decisions about what the product does, which no agent reopens without
  asking you. The rulings are one file, with one bullet for each decision. A retro adds a bullet
  only after you approve the ruling, in a pull request.
- `docs/plans/`, `docs/backlog/`: the plans, and work for later. The [settings](settings.md#paths)
  can move the plans and the rulings.

Not in git:

- `.lem/project.local.toml`: the settings of this computer.
- `.lem/worktrees/`, `.lem/state/`: the worktrees, the tasks and the board.

For all repositories, in `~/.config/lem/` (or `$XDG_CONFIG_HOME/lem/`):

- `owner.jsonl`: your away status.
- `machine.toml`: the settings of this computer:
  - `[load]`: the load limit for the checks, 40 when you set none. `lem project load --start N`
    sets it, and `lem project load --start none` removes the limit;
  - `[handoff]`: the number of tokens where a session compacts, which `lem project handoff
    --tokens N` sets;
  - `[seats]`: the seats `merger` and `session`, which you write by hand;
  - `[serve]`: the board server's port, which `lem serve --port N` sets, and its door for your
    phone;
  - `[peers]`: the other computers of the board.
- `workspaces.json`, `serve.log`: the repositories that the board server shows, and its output.
- `push-key.pem`, `push.json`: the key and the devices of the notifications.

## The board on your phone

[The board](board.md#the-board-on-your-phone) gives the steps for Tailscale, the Home Screen and
the notifications.

## The correction queue

With this optional queue, a retro finds a correction that you gave more than one time. A hook sends
each message that you type, with the agent's message before it, to the Jev decision model.
Commands that start with `/` stay local.

`corrections.collect = true` turns it on for the repository. Each person then needs `JEV_API_KEY`
in the environment. The default provider is [OpenRouter](https://openrouter.ai); `JEV_API_URL`
names another. To say no for yourself, put `collect = false` under `[corrections]` in
`.lem/project.local.toml`.

## Update

Run these two commands, then start a new session, which also replaces the board server. Update
each repository: one board server serves them all. `lem doctor` shows each one you missed.

```bash
claude plugin marketplace update lem
claude plugin update lem@lem --scope project
```

## Remove

1. Merge or drop each open task.
2. Remove the cronn jobs of this repository.
3. If no other repository uses Lem, type `/lem serve tailscale off` and `/lem serve stop`.
4. Run `claude plugin uninstall lem@lem --scope project`.
5. Run `claude plugin marketplace remove lem --scope project`.
6. Remove Lem's allow rules from `.claude/settings.local.json`.
7. Run `git rm -r .lem`, and commit.
8. Delete the folder `.lem/`.
9. If no other repository uses Lem, delete `~/.config/lem/`, `~/.cache/lem-ask/` and
   `$TMPDIR/lem-ask/`.
