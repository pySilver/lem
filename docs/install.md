# Install and remove

Lem is a Claude Code plugin. This page tells you what Lem needs, how to install and update it,
what Lem writes, and how to remove it.

## What Lem needs

Lem runs on macOS only, because agterm is a terminal for macOS.

| Tool | Need | What Lem uses it for |
| --- | --- | --- |
| Python 3.11 or newer, as `python3` | required | each script of Lem. The `python3` that comes with macOS can be older |
| git | required | worktrees and branches |
| [Claude Code](https://code.claude.com/docs) | required | the agent that runs `/lem` |
| [agterm](https://agterm.com) and the agterm skill | required | the pages, the panes and the companion session of a plan talk. The agterm Help menu installs the skill |
| the [mailbox chat](https://github.com/umputun/agterm/tree/master/cookbook/two-agent-mailbox-chat) and its skill | required | the messages between Lem and a lead, and between the defender and the reviewer. The recipe puts `mailbox-chat.py` on your `PATH` |
| [revmux](https://github.com/umputun/revmux) and the revmux skill | required | the review rounds before a pull request |
| the [GitHub CLI](https://cli.github.com) `gh`, signed in | required with a remote on GitHub | the pull requests, and the watch of the open pull requests |
| [webrev](https://github.com/umputun/agterm/tree/master/cookbook/annotate-document) | required | the markup of a plan or a document on a page |
| [agdoc](https://github.com/umputun/agterm/tree/master/cookbook/html-doc-overlay) | required | a page about the issue, the plan or the change of the session |
| the [backlog recipe](https://github.com/umputun/agterm/tree/master/cookbook/backlog-picker) | required | your own view of the items in `docs/backlog/`: its `backlog` skill and its picker. Install the skill for your user (`~/.claude/skills/backlog`) or for the repository (`.claude/skills/backlog`) |
| [plannotator-tui](https://github.com/umputun/agterm/tree/master/cookbook/annotate-in-plannotator-tui) | recommended | the markup of the output of a pane, or of the newest reply of an agent |
| [Codex](https://github.com/openai/codex) | optional, and highly recommended | a reviewer of a second model family, the second expert, and half of each persona panel. Without it, Claude reviews the work of Claude |
| the Codex persona agent | optional, with Codex | the second model family of a persona panel, in `~/.codex/agents/persona.toml` |
| [cronn](https://cronn.umputun.dev) | optional | the scheduled retro and night plan |
| an [OpenRouter](https://openrouter.ai) key, `OPENROUTER_API_KEY` | optional | the Jev decision model, for the correction queue and the check of a question card |

Lem does not include the recipes of the agterm cookbook. webrev, agdoc and the backlog recipe are
required: each row of the machine check gives the address of its guide. Lem does not include the
recommended tool either, and `/lem init` installs it only after your yes. Without plannotator-tui,
no step of Lem changes. Without Codex, the reviewer is a second Claude, one
expert does not answer, and a persona panel has one model family. Without an OpenRouter key, the
two uses of Jev give no result.

`/lem init` runs the machine check for you. The check shows one row for each tool, and says what
Lem cannot do without that tool. To run it yourself in Claude Code, ask the agent to run
`lem doctor`.

## The install

Run these two commands at the root of the repository:

```bash
claude plugin marketplace add pySilver/lem --scope project
claude plugin install lem@lem --scope project
```

- The two commands write two keys into `.claude/settings.json`: `extraKnownMarketplaces` and
  `enabledPlugins`. Commit that file, so that each person who works in the repository gets Lem.
- Start Claude Code at the root of the repository. A session that starts in a subfolder does not
  get the plugin.
- The skill list shows the skills as `lem:lem`, `lem:lem-ask` and so on, and the builder as
  `lem:lem-builder`. You still type `/lem`.
- The plugin puts the commands `lem`, `lem-ask` and `lem-jev` on the `PATH` of the agent, in that
  repository only.
- The correction hook comes with the plugin. It sends nothing until the settings say
  `corrections.collect = true`.
- The plugin has no version number. Each commit of Lem is an update.

Then type `/lem init` in a session at the root of the repository. The
[README](../README.md#install) gives its five steps.

## The update

Run these two commands, and then start a new session:

```bash
claude plugin marketplace update lem
claude plugin update lem@lem --scope project
```

To see which copy of Lem runs, ask the agent to run `lem version`. It prints the folder of the
plugin, and the commit when that folder is a git clone.

## The permissions that `/lem init` proposes

A builder runs in the background. In the `default` or the `acceptEdits` permission mode, a
command that needs a permission stops the builder. The permission question appears in Lem's
session, and at night nobody answers it. So `/lem init` proposes rules for the tracked
`.claude/settings.json`. The hand-over page at the end of `/lem init` shows them as an assumption
that you can change ("change allow none" removes them all).

Under `permissions.allow`:

- `Bash(lem *)`, `Bash(lem-ask *)` and `Bash(lem-jev *)`;
- `Bash(git worktree add *)`, `Bash(git add *)`, `Bash(git commit *)`, `Bash(git rm *)` and
  `Bash(git mv *)`;
- the `agtermctl` calls that Lem uses, for example `Bash(agtermctl msg send *)`;
- `Bash(mailbox-chat.py *)` and `Bash(revmux *)`;
- `Bash(codex exec *)`, for the experts;
- `Edit(/.lem/worktrees/**)`, the folder of the worktrees;
- one rule for each command of `checks.commands`, `checks.alone` and `checks.setup`. A command
  with `&&` gets one rule for each part.

The rules allow no `git push` and no command of the project other than its checks. Claude Code
shows no prompt when Lem merges. In a project with pull requests, Lem merges each one through
GitHub, so GitHub's rules for the base branch apply. With `branch.propose = "merge"`, Lem puts the branch on the
base branch directly. A push of a task branch goes only through `lem land`. The machine check
reads `permissions.defaultMode` and tells you what happens to a builder in that mode.

## GitHub

With a remote on GitHub, Lem pushes the branch of each task and opens its pull request. Turn on
the branch rule "Require branches to be up to date before merging" for the base branch. GitHub
then refuses to merge a pull request whose base is out of date.

## The correction queue

The correction queue is optional. With it, `/lem retro` can find a correction that you gave two
times or more.

- The hook sends each message that you type, with the agent's message before it, to the Jev
  decision model through OpenRouter. It does not send a command that starts with `/`.
- It sends only in a repository whose `.lem/project.toml` says `corrections.collect = true`. That
  line is in git, so it is a yes for each person who works in the repository.
- The hook of each person uses that person's own `OPENROUTER_API_KEY`. A person with no key sends
  nothing.
- A person who does not want it writes `collect = false` under `[corrections]` in
  `.lem/project.local.toml`.
- A message that may hold a lesson goes into the queue in `.lem/state/`. Git never sees it.
- A failure goes to `.lem/state/corrections.log`.

## What Lem writes, and how you undo it

| Where | What | How you undo it |
| --- | --- | --- |
| the repository | two keys in `.claude/settings.json` | `claude plugin uninstall` and `claude plugin marketplace remove`, each with `--scope project` |
| the repository | the allow list in `.claude/settings.json`, if you kept it at onboarding | remove the rules |
| your home | the clone of the marketplace in `~/.claude/plugins/marketplaces/lem/`, a copy of the plugin in `~/.claude/plugins/cache/lem/lem/`, and the entries `lem` and `lem@lem` in `~/.claude/plugins/known_marketplaces.json` and `installed_plugins.json` | `claude plugin uninstall` and `claude plugin marketplace remove` |
| the repository | `.lem/` and the starter set of the review tool in `.revmux/`, on the branch `chore/lem-onboarding` | before "land": answer "drop". After it: the steps below |
| the repository | `.lem/.gitignore` and `.lem/worktrees/.gitignore`, so that git does not see the local settings, the state and the worktrees | the steps below |
| the repository | in the commit of the onboarding: an ignore line for each kind of file that your check commands leave, for example `__pycache__/` | answer "change ignore none" before "land". After it: remove the lines |
| the repository | one branch for each task, and its worktree in `.lem/worktrees/` | Lem removes them after the merge |
| the repository | the plan of each full change in `docs/plans/`, and the backlog items of a task in `docs/backlog/`, on the task branch | `git revert` after the merge |
| the repository | `.lem/state/`, the state of Lem | delete that folder |
| the repository | the commits of a task on the base branch, after the merge | `git revert` |
| the remote | the branch of each proposed task, and its pull request, on GitHub | close the pull request, and delete the branch |
| the remote | a merge of a pull request, or a push to the base branch on `origin`, after your approval or with `branch.land = "agent"` | `git revert`, then a push |
| Linear | status changes and one comment on the ticket of a task, only with a `[tracker]` table | change the ticket in Linear |
| your home | scheduled jobs in cronn, only after your yes in `/lem init` | remove the job in cronn |
| your home | `~/.cache/lem-ask/mermaid-11.12.0.min.js`, which the question page gets on its first use | delete that folder |
| your home | the question pages in `$TMPDIR/lem-ask/`. Lem removes a page after a day | delete that folder |
| your home | before a Codex reviewer starts, Lem removes `~/.codex/agterm/SESSION-ID`, where the agterm recipe for Codex resume keeps the conversation of a session. So each reviewer starts with an empty context | none: the next `codex` in that session writes a new file |

- The scripts of Lem do not edit your `.gitignore`. Only the onboarding adds lines to it, in its
  own commit, and its page lists them.
- The checks remove each file that their own commands leave in the worktree of a task, and they
  name the files. They never remove a file that was there before the run.
- A task that you drop, or that Lem answers, loses its worktree. Its branch goes too, if it has no
  commit of its own. A branch with commits stays, and Lem tells you how to delete it.

## Remove Lem from a repository

1. Land or drop each open task.
2. Remove the scheduled jobs of this repository in cronn, if you accepted them.
3. Run `claude plugin uninstall lem@lem --scope project` at the root of the repository.
4. Run `claude plugin marketplace remove lem --scope project`.
5. Remove the allow rules of Lem from `.claude/settings.json`, if you kept them.
6. Commit the change of `.claude/settings.json`.
7. Run `git rm -r .lem`. Commit that change.
8. Delete the folder `.lem/`. It still holds the local settings, the state and the worktrees,
   which git does not track.
9. Delete the branch of each task that you dropped or that Lem answered, if the branch is still
   there.
10. Delete `~/.cache/lem-ask/` and `$TMPDIR/lem-ask/`, if no other repository uses Lem.
