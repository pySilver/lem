# Lem as an app with dependencies, in a pythonic shape

> **Status: accepted** by the owner on 2026-11-24, with his answers to its four questions ("His
> answers"). Three parts of it are built and on `main`: "Where the steps stand" names them, and
> "From here to the release" is the path that is left.

A draft by the maintaining session of 2026-11-23 and 24, from the owner's words of that night, an
inventory of the code and a research of how such a tool ships. Both reports are in the session's
scratch folder, `.claude/style-tools/reshape/` (`inventory.md`, `distribution.md`), outside git;
a number below names which of the two it is from, or the command that printed it.

## Why

He asked for a modern Python style: uv, `pyproject.toml`, ruff, pyrefly, with mybaze and
wemake-python-styleguide as the examples, and a popular convention for the JavaScript. Step 0 does
that for the code as it is. Then he read what the tools said of the code, and went further:

- "I think we will need to reshape the app to a pythonic state."
- "I don't want to have our own implementation of things that are well known and available in
  opensource for ages."
- "If `lem` needs to be an app that one has to setup in two steps (app + skills) so be it."
- "I also believe that we can afford different distribution (maybe a homebrew with uv?)."
- On "Opinionated and small": "I think its now just 'opionated'".

## Where Lem stands

- 52,708 lines of scripts in 1,619 functions, ten days after the first commit. Four files hold 51%
  of them: `land.py` 8,633, `project.py` 7,882, `lem_board_model.py` 5,843, `serve.py` 4,512. 72
  functions are over 100 lines, and `lem_board_model.time_of` is 820 (inventory, at `61fe428d`).
- `flake8 --select=WPS` reports 16,021 violations (run at `745d4993`): 5,452 lines too complex,
  2,410 repeated string literals, 1,511 names too short, 807 magic numbers.
- The scripts are libraries, commands and callees in one process at once: 22 `sys.path` inserts,
  29 `importlib` loads, and `lem_sibling`, which calls a script's `main` and captures what it
  prints (inventory).
- Lem writes by hand what a library does:

| Part | Today (inventory) | The usual library |
|---|---|---|
| HTTP server, routes, live stream, start and stop | a 900-line handler on `http.server`, 205 lines of stream, 311 of start and stop | Starlette and uvicorn |
| HTML | `h()`, called 840 times in two page modules | a template engine, or a typed builder |
| Web Push | 823 lines; the signature runs the `openssl` command | `cryptography` |
| HTTP clients and the peer proxy | `urllib` and `http.client`, 9 call sites | `httpx` |
| Command line | 13 `argparse` programs, 257 arguments, 4 programs parsed by hand | `cyclopts` |
| Settings | about 600 lines that read and check four TOML files, 250 that edit TOML and keep its comments | `pydantic-settings`, `tomlkit` |
| Records | 66 kinds, 18 read with no check; "write the whole file" written 17 times | `pydantic` models, one writer, `filelock` |
| Running `git`, `gh`, `agtermctl` | the `git` runner written 10 times | one module |
| Tests | a runner of its own for 1,254 unit cases; 478 checks in a shell framework of its own | `pytest` |

The library names are candidates, not choices: the inventory took them from knowledge, and each
step checks the current documentation before it takes one. Where mybaze already runs a library
for the job (`pydantic`, `pydantic-settings`, `cyclopts`, `structlog`, `psutil`, `uvicorn`,
`pytest`; its `pyproject.toml`, read 2026-11-23), that one is the first candidate.

## The target

One installed program, `lem`, which is a Python package with its dependencies, and the plugin
(skills, hooks, agents) that comes with it.

- **A package.** `src/lem/`, one module for one job, a domain in a folder: settings, records,
  tasks, landing, board, session, and a small kernel under them (processes, files and locks, the
  clock, errors). A script is no longer a library, a command and a callee at once: the command
  line calls functions, and so does the server.
- **Typed at the edges.** Each record and each settings table is a model that is checked when it
  is read. The 501 errors pyrefly found before step 0 came mostly from records passed around as
  `dict` and `object`.
- **The style is a gate.** ruff, pyrefly, and `flake8 --select=WPS` with wemake's own limits and
  ruff's line length of 88. The gate names the packages that pass it, and the list grows until it
  is `src/lem`. Then the reshape is done: 16,021 is 0, and so is the count of size marks that
  step 0 leaves.
- **What stays as it is.** Every command line an agent or he types (the plugin's texts name
  `lem NAME SUB` 476 times in 58 files); the form of each record, by the two-release rule; the
  board's addresses, which phone bookmarks hold; `push-key.pem`, or every device subscribes
  again; the meaning of each refusal and its fix; the skills' and the stages' texts; what each
  test proves.

## How it ships

From the research (`distribution.md`), which names what it tested and what it did not:

- **The app**: a Homebrew formula in a tap of his, built with uv from the `uv.lock` of the release
  tag. This is how he gets `agterm`, `revmux` and `cronn` today. On Linux, for CI:
  `uv tool install` from the tag. The installed command starts as fast as today's `bin/lem`
  (47 ms at the least for both, measured with a trivial tool).
- **The plugin**: from its marketplace, with its own update, as today (his answer of 2026-11-24).
  When the app and the plugin are of different versions, Lem stops with one line that names the
  one that is behind. On Linux, `uv tool install` does not read `uv.lock` (uv's maintainers, issue
  15361), so CI installs with `uv sync --frozen` from a checkout of the tag.
- **Later, by a trial**: Claude Code has a plugin source of type `command`, with which the app
  hands Claude Code its own plugin files, and `brew upgrade lem` would be the one update. Nobody
  tried it at project scope with the team's committed settings, after an upgrade, or in a session
  started from a GUI app. The app and its formula are built so that this source can replace the
  plugin's own release when a trial of those three cases passes.
- **Not this way**: one plugin that gets its libraries through `uv run`. Lem's hooks get 5 to 10
  seconds and stay silent on purpose, so after each update they would do nothing, with no word,
  until a command had downloaded the libraries; and a Lem command downloads nothing by itself.
- **The name.** `lem` is free in Homebrew. On PyPI it is another project's, so a wheel there needs
  another name. The Common Lisp editor Lem installs on a Mac as an app, with no command; a
  developer who built it from source can have its `lem` on his path. A plugin's `bin/` comes after
  the developer's own commands (Claude Code's documentation, and measured in this session:
  entries 27 to 30 of 30), so on such a machine Lem's skills call the editor. The name stays
  (his answer), and Lem says one line when another `lem` is first. The name is fixed for good on
  the day the formula is published.

## The steps, in order

Each step ends with `main` releasable, and what it changes for a developer is said in its row.

| | Step | What it does | A developer sees |
|---|---|---|---|
| 0 | Tools and conformance | uv, ruff, pyrefly, ESLint; the code formatted and clean under them, with no change of behavior | nothing |
| 1 | An app that installs | the scripts become the package `lem` with one entry point, moved and not rewritten; the formula in his tap; a check that the app and the plugin are of one version; `bin/lem`'s Python 3.9 launcher, `lem_python.py` and the `sys.path` inserts go | two install steps, two updates |
| 2 | pytest | the unit cases run under pytest as they are; the 80 shell checks that only call a script become unit cases; the journeys stay in shell | nothing |
| 3 | The kernel | one runner for `git`, `gh` and `agtermctl`, one writer and one lock, one clock, one error with its exit, logging for the server | nothing |
| 4 | Records | a model for each of the 66 records, checked on read; the defects the inventory read in the code are run, and the real ones fixed | a broken record is refused with its fix, where a traceback was |
| 5 | Settings | models over the four files, `tomlkit` for the edits; each refusal keeps its words | nothing |
| 6 | The command line | one command tree on a library, the same words and options; a command's help comes from its own function, and the 600-line module docstrings go | shorter `--help` |
| 7 | The board server | routes, forms, the stream and static files on a framework; pages from templates; Web Push with `cryptography`; the peers with `httpx` | nothing; the addresses stay |
| 8 | The large functions | `time_of`, the landing's steps, `project.py`'s commands, split under the wemake gate, a domain at a time | nothing |

Steps 3 to 7 each bring their package under the wemake gate when they end; step 8 brings the rest.

### Where the steps stand

Three parts were built in the night of 2026-11-24 with no dependency and no change of how Lem
installs, so that none of them waited for an answer of his. They are on `main` since that day:

- **Step 0**, the commits of `chore/python-js-style`.
- **The first half of step 1**, the commits of `refactor/package-layout`: the scripts are the
  package `src/lem/` with real imports and one entry, moved and not rewritten. Of the 22
  `sys.path` inserts one is left, in `bin/lem`; no module is loaded by its path. What is left of
  step 1 is stage 3 of "From here to the release": the formula in his tap, the check of the two
  versions, and the end of the Python 3.9 launcher, which is `src/lem/python.py` now.
- **A part of step 3**, the commits of `refactor/shared-helpers`: one writer of a whole file,
  one lock of a thread and a file, one clock, one stop of a process group, one `git` runner,
  each with the standard library. The `gh` and `agtermctl` runners, the one error and the
  logging are left.

Beside them, the fixes of `docs/backlog/` that needed no ruling.
Step 1 comes first because nothing can depend on a library before the app installs with its
dependencies. Step 2 comes next because every later step leans on the tests, and they should be
in the form the new code's tests take.

## From here to the release

The path from `main` on 2026-11-24 (`21a18e67`, installed release 0.3.1) to the release in which
the reshape is complete. A box is ticked in the commit that makes it true, so this list is the
state. The release is made on the owner's word.

### Stage 1: close the night's work

- [x] The style step, the shared helpers, the package `src/lem/` and the backlog fixes are on
  `main`, with every suite green (`bash tests/all.sh`, 28 suites).
- [x] The defects seen outside those changes are items of `docs/backlog/`.
- [x] The five items with `worth: yes` are fixed, each with its test, read by a reviewer, and on
  `main`: the bar's three suppression forms, the hook's traceback, a conflict's quoted file names,
  the "waits for" text of a task two releases back, `lem-ask`'s answer that is no object.
- [x] The owner's answers to the plan's questions are in "His answers", the two that change a
  ruling are in `docs/rulings/rulings.md`, and this plan's status is "accepted".
- [x] Each `worth: later` item of `docs/backlog/` has his ruling, or says what it waits for:
  eight got his answer on 2026-11-24, four had one correct behavior after all, and two wait for
  something that is no ruling (an add-on he chooses, a real Linear ticket).
- [x] His eight answers and the four fixes are built, each with its test, read by a reviewer, and
  on `main`.
- [x] What two outside reviews of that work found is repaired with it (Astra, 2026-11-24: the
  board and the sessions, the landing), and so are the defects they saw in older code that had
  one correct behavior. `lem land base` runs the plain rebase, and a review carries over it only
  where git's merge of the base and the tip before is clean and is the new tip's tree.

### Stage 2: the clean base, proved

Still a plugin with no install step and no dependency. No release: nobody uses Lem during the
migration.

- [x] One real task runs on `main`'s Lem in a scratch repository (`claude --plugin-dir`), from
  `/lem new` to a merged pull request: the hooks, the board server's start and a landing, on the
  new layout. The trial has a Lem home, a Claude configuration and a port of its own, as
  `tests/lib.sh` gives a suite, so that it cannot replace his board server; its report names the
  command that was resolved, its version and root, and the server's root and pid. A defect it
  shows is fixed before stage 3 starts.
- [x] The base lines that later stages are held to are recorded here: for each hook, and for one
  small command, the modules its process loads and its time (the least of 20 runs), on a prompt
  with the correction queue off, at a session's start and at a compaction.
- [x] The command lines of the skills' texts on `main` at the end of stage 1 are fixtures: what
  each name takes (its subcommands and options), and that each command line a text gives is one
  the command takes. `tests/unit/commands.json` holds the shape of 17 names, 88 subcommands and
  297 options in plain data, with no word of `argparse`, and what a wrong call exits with;
  `tests/unit/test_command_lines.py` reads 567 command lines from 84 texts against it. One line
  was wrong (`stages/investigate.md`, a `lem project state` with no text), and stage 3 corrects
  it.

#### The trial of 2026-11-24

Run by the maintaining session from a runbook that Astra wrote, on `main` at `3247d8fe`, in a
temporary folder with its own Lem home, Claude configuration (empty) and port, in the private
repository `pySilver/lem-scratch`.

- **Resolved.** In the request's session and in the task's session `command -v lem` gave the
  copy's `bin/lem`, and `lem version` gave version 0.3.1, commit `3247d8f` and the copy's folder as
  its root. The session listed the agent `lem:lem-builder`.
- **The board server.** No listener before the first session. The `SessionStart` hook started
  one: pid 79869, port 52849, its root the copy's folder and its home the trial's
  (`/api/server`). His own server kept its pid 3311, its start time and its two ports, read by
  `ps` and `lsof` before and after.
- **The task.** `/lem new Correct the typo "recieve" to "receive" in docs/word-list.txt.` went the
  fast track with no answer from a person: `session.open` at 20:09:48 UTC, one builder, the check
  `sh tests/words.sh`, one review read, pull request 19 proposed green at 20:14:00, the merge
  agent's verdict `merge` at 20:14:30, merged by the server at 20:14:52. The worktree and the
  branch were gone after it, here and on GitHub.
- **Seen, and not Lem's code.** A new Claude Code configuration (2.1.331) asks "Allow this read
  outside the working directories?" at the first read of a stage file in the plugin's folder: a
  new user meets it at the first task, so the install guide of stage 3 says it. The wake after
  the merge opened a second session, because the trial's wrapper of `claude` had another name
  and `session.agent_runs` saw no agent in the first: the next trial names its wrapper `claude`.

The base lines, on Python 3.15.2, with the board server running, each the least of 20 runs:

| Process | When | Least | Modules |
|---|---|---|---|
| `corrections hook` | a prompt, the queue off | 55.5 ms | 107 |
| `serve_hook` | a session's start | 50.8 ms | 82 |
| `session_hook` | a session's start | 47.8 ms | 83 |
| `session_hook` | before a compaction | 48.3 ms | 83 |
| `session_hook` | a start after a compaction | 48.5 ms | 83 |
| `ask hook-stop` | a turn's end, not waited for | 86.3 ms | 91 |
| `lem version` | a small command | 40.5 ms | 67 |

The modules of `lem` in a hook's process are `lem`, `lem.state` and `lem.paths` at most, beside
the hook's own module.

### Stage 3: Lem gets its libraries (the rest of step 1)

- [ ] The tap `pySilver/homebrew-tap`, made by the session, with a formula that builds Lem with
  uv from the lock file of a tag; `brew install` and `brew upgrade` tried from it.
- [ ] The app's command replaces the plugin's `bin/lem`; the hooks start the app by its full
  path; a check of the two versions stops with one line that names the one that is behind.
- [ ] An installed app knows where its files are. Today `paths.ROOT` is two folders above the
  package, which in an installed app is a folder of the interpreter: the skills' data, the
  plugin folder a task's session gets (`session.plugin_dir`) and the server's code stamp
  (`serve.code_stamp`, which is 0 for a folder with no source tree, so that an installed app
  would never replace an older server) each get their place from the installed package. Tried:
  a fresh install, an upgrade from one trial build to the next over that build's running
  server, and a second repository on another plugin version.
- [ ] The path a developer's keymap holds (`doctor.picker` writes the interpreter and the
  absolute `bin/lem` of the marketplace clone) still starts Lem after the change.
- [ ] The journeys of `tests/*.sh` run against the installed app too (`tests/lib.sh` starts
  `src/lem/__main__.py` of the checkout today, which passes where an installed app lacks a file).
- [ ] Python 3.14: the project file, the checkers' settings, the tests on Lem's own Python, CI.
- [ ] `lem doctor`, `docs/install.md` and the site describe the new install, and Lem says one
  line at the start of a session when another `lem` is first on the path.
- [ ] The scratch task of stage 2 runs again, on the installed app.

### Stages 4 to 10: the reshape, a step each

Each stage is one step of "The steps, in order", is done when its row there is true, and leaves
`main` releasable. Each ends with every suite green and with its package in the list of the style
gate (`flake8 --select=WPS`).

- [ ] Stage 4, step 2 (the tests): the unit cases run under pytest; the shell checks that only
  call a script are unit cases. `tests/all.sh`, `tests/pick.py` and `tests/suites.sh` change
  together and keep the count, the failures, the skips and the time limit; the case names before
  and after are compared, since an equal total can hide a missing case. A check that needs a
  real process (an exit status, a competing lock holder, the end of a process group) stays in
  shell.
- [ ] Stage 5, step 3 (the shared base): one runner for `gh` and `agtermctl`, one error with its
  exit, a log for the server. Each caller keeps its own policy (stdin, prompts, the socket and
  window, what is tried again). Wide.
- [ ] Stage 6, step 4 (the records): a model for each record, checked when it is read; the read
  defects of the inventory fixed, each in a commit of its own. Wide: it reaches 29 of the 41
  modules. The release reads no record of 0.3.1 ("No upgrade from 0.3.1" in "His answers"), so
  a record's form may change here in one step, with no reader of the old form beside it. Two
  rules, from the code: the reader and the writer of a record change in the same commit
  (`land.events_of` looks for the text `"task": "SLUG"` in a line before it parses it, so a
  writer with other bytes makes an event invisible to a reader that was left as it is); and one
  rule for all records says what becomes of a key the model does not know (`land.Task.keep`
  writes the whole record back today). No hook
  and no small command imports the model library: its import alone is about 40 ms for pydantic
  and 15 ms for msgspec (Astra's probe, Python 3.14.3, median of 7), against 33 to 58 ms for a
  whole hook today. Which library is measured on Lem's own records before it is chosen.
- [ ] Stage 7, step 5 (the settings): the settings as models over the data that `project.load`
  selects from its four files and from a committed blob; `tomlkit` for the edits. Not
  `pydantic-settings`: its sources (environment, dotenv, secrets) are not Lem's, and its import
  is about 84 ms (the same probe).
- [ ] Stage 8, step 6 (the command line): one command tree on a library, the same words and
  options. Wide: 13 modules. First the functions that the server and the landing call in
  process get direct callers (`sibling.in_form` finds `def main(argv` in a module's text, and
  starts a process when it is gone). The library is chosen by a measurement of Lem's own tree:
  in the probe, the dispatch of one argument took about 36 ms with cyclopts, 16 with argparse
  and 15 with Click, and `lem NAME` runs hundreds of times in a task.
- [ ] Stage 9, step 7 (the board server): the board server on a framework, the pages from
  templates, Web Push with `cryptography`, the peers with `httpx`. The server's duties (the
  machine, the push watcher, the Inbox watcher, the look at GitHub) keep one owner across its two
  listeners, and the door's rule stays with its listener. A run of `tests/lem-board-keys.sh` in
  which the phone's and the frames' checks execute, not skip, is required.
- [ ] Stage 10, step 8 (what is left of the large functions): each stage from 5 on splits the
  modules whose callers it changes, and brings them under the style gate; this stage splits what
  no stage touched. At its end the gate covers all of `src/lem`, and no size mark of step 0 is
  left.

A release between two stages is his call. None is planned: nobody uses Lem during the
migration, so a release before the end would run only its hooks and its board server in his
sessions.

### Stage 11: release 1.0.0

- [ ] `flake8 --select=WPS` over `src/lem` reports nothing, and `ruff`, `pyrefly` and ESLint
  report nothing.
- [ ] No `# noqa: ... over the limit before the limit was set` is left.
- [ ] Every suite is green on the release commit, and the scratch task of stage 2 ran on it.
- [ ] What Lem 0.3.1 left in his repositories and on his Mac is wiped, on his word and from a
  list of what goes (each repository's state folder and tasks' worktrees, Lem's home folder,
  the board server of 0.3.1); his Mac and mybaze start over on the release, and a week of real
  tasks there shows no defect that a fix release had to repair.
- [ ] The scheduled jobs `lem: night` and `lem: retro` are on again, on his word ("its not use
  until we complete refactoring", 2026-11-24).
- [ ] The five guides of `docs/` that run past the 800-word aim are cut (his answer of
  2026-11-24: at this release, since the stages before it write `install.md` again).
- [ ] One real nap reads the changed nap brief, and its dream is read (his answer of 2026-11-24:
  Lem changes the fewest words, and the next nap is the test).
- [ ] `AGENTS.md`, the guides and the site describe Lem as it is; this plan gets its status line
  with the commits.

### What each stage asks of him

| Stage | His part |
|---|---|
| 1 | A ruling on each `worth: later` item |
| 2 | Nothing |
| 3 | A try of `brew install pySilver/tap/lem` on his Mac, when he wants |
| 4 to 10 | A look at each stage's report |
| 11 | The word for 1.0.0 and for the scheduled jobs; a week of real use |

## An outside read, and what it changed

On 2026-11-24 a session of another model family (Astra, through Codex) read this plan against
`main`, read-only. Its report is `2026-11-24-lem-as-an-app/astra-read.md`, kept as an opinion.
The maintaining session found each line it quotes in the code, and took these points into the
stages above:

- Stage 2: the trial's own Lem home, Claude configuration and port; the base lines of the hooks.
- Stage 3: the root of an installed app, the keymap's path, the journeys on the installed app.
- Stage 6: the writer's bytes, the unknown keys, the cost of a model library in a hook.
- Stage 7: no `pydantic-settings`. Stage 8: direct callers first, and the library by measure.
- Stage 10: the split goes with each stage, not after all of them.

Its measured import times are in the stages where they decide something. Three defects it found
in today's code are items of `docs/backlog/`.

## How this work is done

- By the maintaining session, and not by Lem: "I will not use Lem anywhere during migration.
  That's why we disabled cronjobs to prevent Lem using itself" (the owner, 2026-11-24). Workers
  build each step, an independent reader reviews it, and `bash tests/all.sh` passes before `main`
  moves. Then the session merges the stage to `main`, pushes it and reports to him: he chose this
  over a question before each merge (2026-11-24).
- All work continues beside the reshape, with a stop while a wide step is open (his answer). The
  wide steps are the shared base, the records and the command line (stages 5, 6 and 8). Before
  one starts, the open work is finished; while it is open,
  nothing else starts or lands; then all work continues.
- No release is installed while nobody uses Lem: his Mac stays on 0.3.1 until the release at
  the end. That release reads no record of 0.3.1 and keeps no command line of it: his
  repositories start over ("No upgrade from 0.3.1" in "His answers"). So during the reshape a
  record, an event, a state, a settings key or a command line changes form in one step, and the
  skills' texts change with it in the same commit. The two-release rule of `AGENTS.md` holds
  again from the release at the end, which is the session's reading of his words.
- A step that changes how a thing is built changes no behavior with it. Where a defect is fixed
  (step 4), it is a commit of its own with its test.
- A task that moves a file is checked by what the tests prove, not by where they are: Lem's own
  bar counts a moved test file as a lowered bar, so the plan of such a task says which file went
  where.
- From the release at the end on, the command lines of the release before keep working for one
  release, as the records do: a session that runs while `brew upgrade lem` changes the app has
  the old skills and the new command.

## His rulings that this changes

In `docs/rulings/rulings.md`, in the same commit as this plan:

- "Opinionated and small" is "Opinionated".
- "Lem is a plugin, and nothing else" gives its place to "Lem may be an app and its skills, set up
  in two steps".
- New: "Lem uses the well-known open-source library for a job, and writes no copy of its own."
- New: "Lem's code has a modern style that tools hold."

In the commit that records his answers: "The app ships as a Homebrew program from his own tap"
is a bullet of its own, and "Python 3.11 stays" holds until Lem brings its own Python.

`AGENTS.md` still says that the scripts are standard-library Python. It says so until step 1
changes the code, since it describes the current state.

## His answers

Each question went through the question gate on 2026-11-24: a reader checked its brief against
the code, the people it affects answered where it affects more than one kind of person, and a
challenger argued against each card. The briefs, answers and cards are in `.personas/runs/` of
that day, outside git.

1. **How Lem ships**: a Homebrew program and the plugin, each with its own update. The first card
   recommended one plugin with its libraries through `uv`; a challenger showed what that does to
   the hooks, and three of four personas then left it.
2. **The tap**: the session makes `pySilver/homebrew-tap` when stage 3 starts.
3. **Which Python**: 3.14, from the release in which Lem brings its own Python. Until then 3.11.
4. **New work during the reshape**: all work continues, with a stop while a wide step is open.
   Both personas wanted features to wait; the record of the day before (12 features and 14 fixes
   beside one open step) and the plan's lack of an end date spoke against that.
5. **The name of the command**: `lem` stays, and Lem says one line when another `lem` is first.
   A ruling of its own, on his word.
6. **No upgrade from 0.3.1**, said by him the same evening and asked by nobody: "nobody uses Lem
   except me, so we don't need any 'clean upgrade' - we can wipe current usage of lem and start
   over in those repos". A ruling of its own. It took the readers of old forms out of stages 3,
   6 and 11.

## Out of scope

- A change of what Lem does: no command, stage, record or page is added or removed here.
- The skills' texts, the stages, the prompts and the harness files, except where a path of a
  script is named.
- The JavaScript beyond step 0: the board's kit stays as it is built today.
- A database, a second agent's harness, and anything `docs/backlog/` holds.
