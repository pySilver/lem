# Lem

Lem is the `lem` skill and the skills it ships, and the app `lem` they call: one flow for a unit of
work in any repository, with each project's settings kept in that project's repository. The site,
built from the pages of `docs/`, says what it does and how it works; `README.md` points to it; this
file says how to change it.

## Rules for a change here

- **The skill knows no project.** No repository, product, path or person of a real project appears
  in `skills/lem/SKILL.md`, the stage files, the harness files or the templates, except as the
  dated source of a measurement ("convertiser-server, 2026-11-14"). What a project needs to say,
  it says in its own `.lem/` folder or its own `AGENTS.md`.
- **A stage names a capability or a role, never a tool.** `spawn-builder`, `second-opinion`,
  `ask-owner`, `fan-out`, `show-page`, `load-skill`; the question gate, the persona panel, the
  review tool. `skills/lem/harness/README.md` is the contract. A tool's name belongs in the one
  harness file of its agent. A skill this repository ships is named by its name, which is the
  same in every agent: `lem-NAME`, which the owner calls as `/lem NAME`. Every skill, agent and
  command of the plugin carries Lem's name, so that none meets a developer's own.
- **A harness file exists only for an agent the contract was checked in.** Do not write one from
  another project's notes about an agent.
- **A number in a skill file carries its source and date.** A rule that rests on a measurement
  says so; a rule that rests on a guess says that instead.
- **One stage file per subcommand, read only when it runs, and a part that only one path reads
  is a file of its own.** `SKILL.md` holds what is true in every stage. A rule that one stage
  needs goes in that stage. A part of a stage that only one of its paths needs (the interview,
  an investigation, the polish pass) is a file beside it, and the step that chooses the path
  names that file in one line: a task on the fast track reads nothing that only the standard track needs.
- **A task's phases stay apart.** `plan` and `build` are the lead's, in the build phase. A step
  that reads a task's code or its diff goes to the lead, a builder or a fresh agent (the
  investigator, the review, the merge agent), never into the shape (`new`, `interview`) or the
  landing (`land`).
- **The app is Python 3.14 on the well-known library for each job, and its texts say "the
  owner".** Click for the command line, msgspec for every record and setting, tomlkit for a
  settings edit, Starlette, uvicorn and Jinja2 for the board, httpx and pywebpush beside them, and
  the standard library only in a hook. `lem help` prints text. `lem version` prints JSON with no
  envelope. Wrong command syntax is a Click error on standard error with exit 2. A dispatched
  command prints the JSON envelope of `src/lem/kernel/envelope.py`: exit 0 on completion, exit 1
  on a refusal with its code, why and fix, or exit 3 on a fault with its traceback in `lem.log`. No
  silent default for a choice that is the owner's (`lem init` with no base it can tell asks for
  `--base`). Every string the app prints or writes for a person, its `--help` too, says "the
  owner"; comments, docstrings and the stage files keep their voice. The gates hold the style with
  no `noqa`: ruff, pyrefly, wemake-python-styleguide and import-linter (the layers of
  `docs/plans/2026-11-25-lem-built-again.md`, part 2).
- **A change is measured by what it costs a developer on a small task** (the touches it asks of
  him, the waits, the agents it starts) as well as by what it guards.
- **Documentation describes the current state.** No changelog paragraphs, no "previously". The
  pages of `docs/` are the one source of the site, in ASD-STE100, each with one job and an aim of
  under 800 words; `README.md` holds only what a visitor of the repository needs before the site.
  A chart writes each node's and each edge's text in double quotes, and is drawn once on the built
  site before it is committed.
- **A maintainer's session with nobody at the terminal reads `docs/free-hour.md` first.** It changes
  no file that git tracks, makes no branch and no worktree, and never pushes ("A release"); a task's
  own session is not one. The scheduled `/lem night` of this repository takes its free hour as a
  search only, writes what it finds as proposals into the night's file of the day
  (`skills/lem/stages/night.md`), and opens no task here: asked on 2026-11-21 whether a night here
  may open pull requests, the owner answered "A3 no". The scheduled `/lem retro` of this repository
  takes no free hour: it is a retro only.
- **A change of the form of a record, an event or a state takes two releases.** It reads the form
  of `BEFORE` and writes one that `BEFORE` still reads: a new key goes beside the old one, and no
  key the old reader reads is renamed or removed; the next release may drop it. Its test reads a
  record of the old form, and finds each old key in one the new code writes.
- **A new ruling of the owner is one bullet of `docs/rulings/rulings.md`**, under the heading of
  its group: the rule in one sentence, in bold; only where the sentence alone could mislead, at most
  three lines more, with his words in quotes only where they are the rule or its limit; his day in
  parentheses at the end. No history in a bullet.
- **A ruling that replaces another takes its bullet's place**, and git keeps the old one. A ruling
  that changes a part of another changes that bullet's words. A bullet leaves the list only on the
  owner's word.
- **A rule that a test or one place now holds may move to `docs/rulings/history.md`, on his
  word**: a line of its first part with the test's name, which `tests/unit/guides/test_rulings.py`
  finds or fails, or a line of its second part with the place's path. A rule goes back to the list
  when its test or its place no longer holds it: the session that sees it moves it at once and
  tells him.
- **A new choice of the maintaining session is a bullet of the list's last part**, "Choices of the
  maintaining session", with `decided` before its day, **when no code, test or text can show it**;
  otherwise it is in the message of the commit that made it. The `decided` lines of
  `docs/rulings/history.md` are choices of the maintaining session that a test or one place holds.

## A release

A release is one commit on `main` and its tag, on the owner's word: `version` in
`.claude-plugin/plugin.json` and in the `lem` entry of `.claude-plugin/marketplace.json` is
`NUMBER`, the entry's `ref` is `vNUMBER`, and `BEFORE` in `src/lem/model/task/release.py` names the
release before. Commit it as `chore(release): Lem NUMBER`, tag it `vNUMBER`, and run
`git push --atomic origin main vNUMBER`. Then the formula of `pySilver/homebrew-tap` takes the tag,
built with uv from the release's `uv.lock`. An update installs that tag, so a merge to `main`
reaches no user. A release reads the records of `BEFORE` and none older. The owner's Mac takes each
release first, and a newer one repairs a bad one. The site is published apart, when the owner
starts `.github/workflows/pages.yml`.

## The owner's rulings

`docs/rulings/rulings.md` lists the owner's rulings in force under the twelve groups, and in its
last part the maintaining session's choices open to him. Read it whole once in a session, before a
change to Lem. A change that adds a part to Lem (a skill, a hook, a command, a key of the settings,
a tool it needs) reaches each bullet of "What Lem is, and who it is for". A ruling is reopened only
by asking him.

`docs/rulings/history.md` holds what left the list, still in force, each with the test or the one
place that holds it: read it when a change touches one.

## Checks

```bash
uv sync --locked                                     # .venv: Lem from this checkout, editable, and its tools
npm ci                                               # ESLint and neostandard, for the gate of the JavaScript
.venv/bin/python -I -B tests --level gates           # ruff, pyrefly, wemake, import-linter, ESLint
.venv/bin/python -I -B tests --level unit [PATHS]    # the unit level, or the files of it named
.venv/bin/zensical build --clean                     # the site into _site/, which git ignores
```

`tests/__main__.py` is the one entry, and `tests/levels.py` says what each level runs: `gates`,
`unit`, `model`, `histories`, `contract`, `journeys`, `hooks`, `browser`, and `full`, every level
at once. The entry sets its own home, `TMPDIR` and `LEM_SERVE=off`, so no test reaches the owner's
board server or Lem's home folder. A run counts only when its passed and skipped cases add up to
the cases it collected, and a selection that collects nothing fails. A level that reaches its
30-minute time limit fails. The test entry does not enforce that limit.

The loop: the unit level of the files a change touches after each edit; the levels of the folders
it touches once at its end; `--level full` once before `main` moves, one at a time on a machine
(the entry takes `/tmp/lem-full-run.lock`). Use the counts of the last full run as the baseline.
Run one journey for the path. Test its other inputs at a lower level.
A rule that takes facts and returns a result is a unit
case, a call of its function; a fact only git can show is a contract or journey case, in a
throwaway repository. A check that makes a dated name or reads the time keeps the value it made and
checks that value. Never make a timing assertion depend on a step that finishes in less than
one second.

`tests/unit/guides/` builds the site in a copy of the checkout and reads the built pages: no
request to another host, every `lem` line one the command tree takes, every link, `llms.txt` and
the Markdown copies, every chart drawn by Pele.

A change to the app comes with its test. A change to a stage file has no test: its test is a real
task, so say in the commit which task showed the need.

To run a clone of Lem in one session, load its folder as the plugin
(Claude Code 2.1.325, 2026-11-17: the session listed every `lem:` skill and `lem:lem-builder`):

```bash
claude --plugin-dir /path/to/lem   # for this session only
```

The `lem` on that session's `PATH` is still the installed app: put the checkout's `.venv/bin`
first on the `PATH` to try the app of the clone.

When the project has no enabled install of `lem@lem`, `lem session open` adds `--plugin-dir`
with the app's own data folder. For an editable install, that folder is the checkout.
The lead reads the folder for the plan talk's pair from `lem session plugin-dir`.
When the project loads the installed plugin, `lem session plugin-dir` returns `null` in `plugin_dir`.

## Layout

Each module's docstring says what it does and why; this list says where each thing is. Part 2 of
`docs/plans/2026-11-25-lem-built-again.md` gives the package tree and its layers.

- `skills/lem/SKILL.md`: the entry point, what holds in every stage, and "One session for each
  task".
- `skills/lem/stages/`: one file for each subcommand, read only when it runs. `new.md` opens a task
  in its own session; `interview.md` and `investigate.md` are the rest of the shape. `start.md`
  starts the build, `plan.md` and `build.md` are the lead's, `talk.md` the plan talk, `ladder.md` a
  decision in doubt and `breaker.md` the circuit breaker. `land.md` is the land phase, `polish.md`
  its step 3, and `conflict.md` what a conflicting pull request takes. The rest are the owner's
  other commands and the scheduled ones.
- `skills/lem/prompts/`: the standing briefs of each agent of a task, the merge agent, the
  reviewers, the night's proposals and the naps; `writing.md` says how a document for the owner is
  written.
- `skills/lem/templates/`: `profile.md` and `persona.md`, which onboarding fills; `handoff.md`, the
  hand-over between two agents of a task; `breaker.md`, the breaker's document.
- `skills/lem/harness/`: the capability contract, `README.md`, and one file for each agent, a core
  with its parts in a folder of the agent's name (`claude-code/`).
- `skills/lem/assets/`: what `lem serve` sends under `/assets/`. `lem.css` and `lem.js` are the
  look and the palette every page of Lem shares, and a new page for the owner links both and brings
  no style of its own; `board.css` is the board's. `vendor/` holds what `tools/board-kit` builds:
  `board-app.js`, `board-icons.json` and `pele.js`, the charts' renderer.
- `src/lem/`: the app. `__main__.py` is the command `lem`, and `hooks/main.py` is `lem-hook`, the
  entry of every hook, on the standard library only. The rows of its layers, from the top:
  `cli/` (a lazy group of Click commands, one leaf module for each), `board/` (the board server,
  its pages, acts and duties) and `addons/` (the night's proposals, corrections, Jev, experts, the
  cast, the Inbox, peers, naps, the picker), which the core never imports; `app/` (the use cases,
  each taking the ports that `app/wiring.py` builds); `adapters/` (git, `gh`, agterm, Claude Code,
  Web Push, Jev) and `settings/`; `ports/`; `model/` (the pure rules: the task, the criteria, the
  decisions, the owner, the landing); `store/` (each task's one record, written whole, and the
  locks); `records/` and `kernel/`.
- `.lem/`: Lem's settings, profile, cast and lessons. Its `state/`, which git ignores, holds each
  task's record and files, the night's and the retro's proposals, the reviewer's items and the
  board server's look at GitHub; `.lem/worktrees/` holds the tasks' worktrees. `.revmux/` is the
  review tool's configuration.
- Lem's home folder, `$XDG_CONFIG_HOME/lem` or `~/.config/lem`: the owner's presence, the machine's
  settings, the developer's own settings for every repository, the repositories the board server
  shows, and the server's files.
- `docs/`: the site's pages, each a guide in STE (`index.md` is the home page), and
  `settings.md`, the reference, one to one with the settings' structs (`tests/unit/settings/`).
  Beside them, off the site: `free-hour.md`, `rulings/`, `backlog/` (Lem's own deferred work) and
  `plans/`, the plans that built Lem, each finished one with a status line that names its commits
  and where later decisions changed it.
- `zensical.toml`, `overrides/` and `docs/assets/`: the site. Zensical, a dev dependency pinned in
  `uv.lock`, builds `docs/` into `_site/`; `overrides/` holds the home page's template and the page
  menu, and `docs/assets/` the site's style in the board's six hues and the chart script that draws
  each `mermaid` block with Pele. Its pictures and `pele.js` are links to the files of `assets/` and
  `skills/lem/assets/vendor/`. `.github/workflows/pages.yml`, started by hand only, builds and
  publishes it.
- `tests/`: the levels of "Checks". `fakes/` holds a stand-in for each port, `fixtures/` the board's
  afternoon of example tasks, and `ledger/` the behavior ledger of the Lem before, with the fate of
  each of its rows.
- `.claude-plugin/` and `hooks/`: what Claude Code reads to load this repository as the plugin
  `lem`. `pyproject.toml` builds the app, the package with these files under `lem/data`.
  `hooks/hooks.json` starts every hook through `hooks/run`, which finds `lem-hook`. Every text and
  message says `lem NAME`, so one permission rule, `Bash(lem *)`, covers them on every machine and
  after every update.
- `agents/lem-builder.md`: the builder, as a Claude Code agent definition; its body is the builder's
  standing rules, and `harness/claude-code.md` says how it is used and overridden.
- `assets/`: the logo (`lem.svg`, the animated scene with both skies), the figure alone
  (`lem-mark.svg`), the night file of each (`*-night.svg`), which `night.py` writes, and in
  `screens/` the board's pictures, light and dark.
- `skills/lem-ask/`, `skills/lem-interview-me/`, `skills/lem-dialectic/`, `skills/lem-root-cause/`,
  `skills/lem-gate/`, `skills/lem-panel/`, `skills/lem-linear/`, `skills/lem-github/`,
  `skills/lem-ask-expert/`: the skills Lem names and ships. `NOTICE` says where each came from.

## The shipped skills are copies, not yet under the rules above

Each was copied from where it worked and changed only as far as the new layout needed. Their text
still names Claude Code's tools. Bring one under the capability rule when a second agent has to run
it, not before.

The set is deliberately small. A tool with its own life (revmux, agterm, the mailbox chat, webrev,
agdoc, the backlog recipe, cronn, plannotator-tui, Plannotator, Codex) is checked for by
`lem doctor` and never copied in. The backlog's item format is the recipe's, and Lem's builders read
it in rule 6 of `agents/lem-builder.md`; no builder loads the recipe's skill, which is the owner's
own tool.
