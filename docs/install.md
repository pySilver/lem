# Install and remove

Lem comes in two forms: a Claude Code plugin, and a clone with links. Use one form in one
repository. This page gives what Lem needs, each form, what Lem writes, and how to remove all of
it.

## What Lem needs

Lem runs on macOS only, because agterm is a terminal for macOS. In Codex, `/lem` stops, and Codex
can only be a reviewer.

| Tool | Need | What Lem uses it for |
| --- | --- | --- |
| Python 3.11 or newer, as `python3` | required | each script of Lem. The `python3` that macOS brings can be older |
| git | required | worktrees, branches and the state of the tasks |
| Claude Code | required | the agent that runs `/lem` |
| [agterm](https://agterm.com) and the agterm skill | required | the pages, the panes and the companion of a plan talk. The Help menu of agterm installs the skill |
| the [mailbox chat](https://github.com/umputun/agterm/tree/master/cookbook/two-agent-mailbox-chat) and its skill | required | the messages between Lem and a lead, and between the defender and the reviewer. The recipe puts `mailbox-chat.py` on your `PATH` |
| [revmux](https://github.com/umputun/revmux) and the revmux skill | required | the review rounds before a pull request |
| the `lem-builder` agent | required | each builder. The plugin and the setup bring it |
| [webrev](https://github.com/umputun/agterm/tree/master/cookbook/annotate-document) | recommended | you mark a plan or a document as a page. `/lem annotate` uses it by default |
| [agdoc](https://github.com/umputun/agterm/tree/master/cookbook/html-doc-overlay) | recommended | a page about the issue, the plan or the change of the session |
| [plannotator-tui](https://github.com/umputun/agterm/tree/master/cookbook/annotate-in-plannotator-tui) | recommended | you mark the output of a pane, or the newest reply of an agent |
| Codex | optional | a reviewer of a second model family, and half of each persona panel |
| the Codex persona agent | optional | the second model family of a persona panel, in `~/.codex/agents/persona.toml` |
| cronn | optional | the scheduled retro and night plan |
| plannotator | optional | a different mark tool, if you name it in `tools.annotate` |
| an `OPENROUTER_API_KEY` | optional | the Jev decision model, for the correction queue, the sort of the backlog, and the check of a question card |

Lem brings no recommended tool. `/lem init` installs one only after your yes. Without webrev,
you read a file as it is and give your notes in the conversation. Without agdoc or
plannotator-tui, no step of Lem changes. Without an OpenRouter key, the three steps of Jev give
no result, and the correction hook logs each message as a failure.

The check of the computer gives one row for each tool, with what Lem cannot do without it:

```bash
python3 CLONE/skills/lem/scripts/doctor.py
```

`CLONE` is the folder of Lem. Run the check in the repository that uses Lem. `/lem init` and
the setup run it for you, so with the plugin you do not type it.

## The plugin

The plugin is the form for a repository that uses Lem. Run these commands in the root of the
repository:

```bash
claude plugin marketplace add pySilver/lem --scope project
claude plugin install lem@lem --scope project
```

- The repository `pySilver/lem` is private now. Your GitHub account needs read access to it.
- The two commands write two keys into `.claude/settings.json`: `extraKnownMarketplaces` and
  `enabledPlugins`. With `--scope local`, they write `.claude/settings.local.json`, which git does
  not track.
- Start Claude Code in the root of the repository. A session that starts in a subfolder does not
  get the plugin.
- `/lem` is the same command. The skill list shows the skills as `lem:lem`, `lem:lem-ask` and so
  on, and the builder as `lem:lem-builder`.
- The `lem-ask` and `jev` commands are on the `PATH` of the agent, in that repository only.
- The correction hook comes with the plugin. It sends nothing until the settings say
  `corrections.collect = true`. See "The correction hook" below.
- The plugin has no version number. Thus each commit of Lem is an update.

To update, run these two commands, and then start a new session:

```bash
claude plugin marketplace update lem
claude plugin update lem@lem
```

What is proven about the plugin:

- On 2026-11-15, Claude Code 2.1.325 loaded Lem as a plugin through `--plugin-dir` and through the
  settings of a project. The builder ran as `lem:lem-builder`, on the model of its file.
- On 2026-11-15, the hook of the plugin started on each message, in three sessions with nobody at
  the terminal.
- An install from GitHub, with the two commands above: not run yet.
- A task in the plugin form: not run yet.

## The clone and links

This form is for people who change Lem. The links point at the clone, so a change in the clone is
active in the next session of each linked repository.

1. Clone Lem: `git clone https://github.com/pySilver/lem`.
2. Link it into one repository: `python3 lem/scripts/setup.py --project ~/code/shop`.
3. Read the result. It lists each link, and then the rows of the check that are not found.
4. Install each required tool that the result shows as absent.
5. In agterm, go to `~/code/shop`, start `claude`, and type `/lem init`.

The setup does the check of the computer in that repository, after it makes the links. Do not run
the check in the clone before the setup: the builder is not linked yet, and the check says so.

All options of the setup script:

```bash
python3 scripts/setup.py                                          # link into your home directory, then check the computer
python3 scripts/setup.py --check                                  # change nothing; show the state of each link
python3 scripts/setup.py --remove                                 # remove the links, and the folders that they leave empty
python3 scripts/setup.py --project ~/code/shop                    # link into one repository only
python3 scripts/setup.py --project ~/code/shop --remove           # remove the links of that repository
python3 scripts/setup.py --corrections on --project ~/code/shop   # add the hook of the correction queue there
python3 scripts/setup.py --corrections off --project ~/code/shop  # remove that hook again
python3 scripts/setup.py --home DIR --bin DIR                     # a different home, or a different folder for the two commands
```

- Without `--project`, the script links each skill into `~/.claude/skills/`, the builder into
  `~/.claude/agents/`, and the `lem-ask` and `jev` commands into `~/.local/bin/`. Then each
  repository on the computer sees Lem, also a repository where a different flow runs.
- With `--project`, the links go into `.claude/skills/` and `.claude/agents/` of that repository.
  The script writes one `.gitignore` in each of the two folders, so that git does not see the
  links. It does not link the two commands, and Lem then starts its question page by its path.
- A folder that already has a `.gitignore` keeps it. If that file does not hide the links, the
  result names the folder.
- The script does not replace a file or a folder that is already there. It names the place, and
  it exits 1.
- If one link cannot be made, the script removes the links that it made in that run.
- A required tool that is absent makes the script exit 1 after it made the links.
- A project that wants a different builder keeps a file with the same name in its own
  `.claude/agents/`.
- The companion session of a plan talk starts in the permission mode that your Claude Code
  settings give a new session. The run from the Linear ticket used the auto mode (2026-11-15).

## The correction hook

The correction queue is optional. With it, `/lem retro` can find a correction that you gave two
times or more.

- The hook sends each message that you type, with the agent message before it, to the Jev
  decision model through OpenRouter. It does not send a command that starts with `/`.
- It sends only in a repository whose `.lem/project.toml` says `corrections.collect = true`. That
  line is in git, so it is a yes for each person who works there with the hook.
- The request uses the `OPENROUTER_API_KEY` of each person. A person without a key sends nothing.
- A person who does not want it puts `collect = false` under `[corrections]` into
  `.lem/project.local.toml`.
- With the plugin, the hook comes with the install. Do not add it a second time with the setup.
- With links, you add the hook yourself, on the day of the setup or later. An agent does not add
  it for you. Use `--project`: the hook then goes into `.claude/settings.local.json` of one
  repository.
- Without `--project`, the hook goes into `~/.claude/settings.json`, and it starts on each message
  in each repository. Use that form only if many of your repositories use Lem.
- A failure goes to `.git/lem/corrections.log`.

## What Lem writes, and how you undo it

| Where | What | How you undo it |
| --- | --- | --- |
| the repository | with the plugin: two keys in `.claude/settings.json`, or in `.claude/settings.local.json` with `--scope local` | `claude plugin uninstall lem@lem` and `claude plugin marketplace remove lem`, each with the same `--scope` |
| your home | with the plugin: the clone of the marketplace in `~/.claude/plugins/marketplaces/`, a copy of the plugin in `~/.claude/plugins/cache/`, and entries in `~/.claude/plugins/known_marketplaces.json` and `installed_plugins.json` | `claude plugin uninstall` and `claude plugin marketplace remove` |
| your home | with links: links in `~/.claude/skills/`, `~/.claude/agents/` and `~/.local/bin/` | `setup.py --remove` |
| the repository | with `setup.py --project`: links in `.claude/skills/` and `.claude/agents/`, and one `.gitignore` in each of the two folders | `setup.py --project DIR --remove` |
| the repository, or your home | the correction hook in `.claude/settings.local.json` of the repository, or in `~/.claude/settings.json`, only if you run `--corrections on` | `setup.py --corrections off`, with the same `--project` |
| the repository | `.lem/` and the starter set in `.revmux/`, on the branch `chore/lem-onboarding` | before "land": answer "drop". After it: the steps below |
| the repository | `.lem/.gitignore` and `.lem/worktrees/.gitignore`, so that git does not see the local settings and the worktrees | the steps below |
| the repository | one branch for each task, and its worktree in `.lem/worktrees/` | Lem removes them after the merge |
| the repository | the plan of each feature in `docs/plans/`, and the backlog items that a task filed in `docs/backlog/`, on the task branch | `git revert` after the merge |
| the git directory | `.git/lem/`, the state of Lem: see the list below this table | delete that folder |
| the repository | the commits of a task on the base branch, after the merge | `git revert` |
| the remote | the branch of each proposed task, and its pull request, on GitHub | close the pull request, and delete the branch |
| the remote | a merge of a pull request, or a push to the base branch on `origin`, on your word or with `branch.land = "agent"` | `git revert`, then a push |
| Linear | status changes and one comment on the ticket of a task, only with a `[tracker]` table | change the ticket in Linear |
| your home | scheduled jobs in cronn, only after your yes in `/lem init` | remove the job in cronn |
| your home | `~/.cache/lem-ask/mermaid-11.12.0.min.js`, which the question page gets on first use | delete that folder |
| your home | the pages of the question page in `$TMPDIR/lem-ask/`. Lem removes a page after a day | delete that folder |
| your home | before a Codex reviewer starts: Lem removes `~/.codex/agterm/SESSION-ID`, the file in which the agterm recipe for Codex keeps the conversation of the session | none: the next `codex` in that session writes a new file |

`.git/lem/` holds these files:

- `tasks/`, one folder for each task;
- `events.jsonl`, the event log;
- `decide-gate.jsonl`, the log of the question gate;
- `backlog-triage.json`, the verdicts of the backlog sort;
- `corrections.jsonl`, `corrections-reviews.jsonl` and `corrections.log`, the correction queue;
- `night/`, the night reports;
- the page of the board and its data files.

- The scripts of Lem do not edit your `.gitignore`. They write their own ignore files.
- The check of the computer runs `codex --version`. Codex can then write its own temporary folder
  in `~/.codex/tmp/`. That folder is Codex's, not Lem's.
- A task that you drop keeps its branch, because no other branch has its commits. You delete that
  branch.
- The plugin rows of the home come from the record of a different plugin of the same computer
  (revmux, 2026-11-17). Nobody installed Lem from GitHub yet.

## Remove Lem from a repository

1. Land or drop each open task.
2. Remove the scheduled jobs of this repository in cronn, if you accepted them.
3. For the plugin, run `claude plugin uninstall lem@lem --scope project` in the repository.
4. For the plugin, run `claude plugin marketplace remove lem --scope project`.
5. For the scope `project`, commit the change of `.claude/settings.json`.
6. For links, run `python3 scripts/setup.py --corrections off --project DIR`, if you added the
   hook there.
7. For links, run `python3 scripts/setup.py --project DIR --remove`.
8. Delete the folder `.git/lem/`.
9. Run `git rm -r .lem`, and commit that change.
10. Delete the folder `.lem/`. It still holds the local settings and the worktrees, which git
    does not track.
11. Delete `.revmux/` too, if you do not use the review tool for other work.
12. Delete the branch of each task that you dropped, and of each task that Lem answered.

To remove the home links, run `python3 scripts/setup.py --remove` in the clone. Then delete
`~/.cache/lem-ask/` and `$TMPDIR/lem-ask/`.

Steps 6 to 10 and the removal of the home links ran on 2026-11-17, in a new repository and a
new home folder. After them, the repository held only `.git` with no `lem/` folder, and the home
held no link. The plugin steps did not run.

## Checks, for people who change Lem

This command runs all the test suites at the same time. It shows one line for each suite.

```bash
bash tests/all.sh
```

`AGENTS.md`, "Checks", gives the command for each suite alone.
