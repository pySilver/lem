# Lem as an app with dependencies, in a pythonic shape

> **Status: proposed**, for the owner to read. Three parts of it are built and on `main`:
> "Where the steps stand" names them. The four questions at the end are his.

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
- **The plugin**: from the app. Claude Code has a plugin source of type `command`: the app prints
  the folder of its own plugin files, and Claude Code copies it once in each session. One update
  command, `brew upgrade lem`, and the skills match the app. A check of `lem version` in the
  plugin stays as the guard.
- **Not tested**: the `command` source at project scope with the team's committed settings, its
  run after an upgrade, and a session started from a GUI app. Step 1 begins with that trial in a
  scratch repository. If it fails, the plugin stays in its marketplace, the app and the plugin
  update apart, and the version check tells the developer which one is behind.
- **The name.** `lem` is free in Homebrew. On PyPI it is another project's, so a wheel there needs
  another name. A Common Lisp editor installs a command named `lem`, and a plugin's `bin/` comes
  last on `PATH` (measured in this session: entries 27 to 30 of 30), so on a Mac with that editor
  Lem's skills call the editor today.

## The steps, in order

Each step ends with `main` releasable, and what it changes for a developer is said in its row.

| | Step | What it does | A developer sees |
|---|---|---|---|
| 0 | Tools and conformance | uv, ruff, pyrefly, ESLint; the code formatted and clean under them, with no change of behavior | nothing |
| 1 | An app that installs | the scripts become the package `lem` with one entry point, moved and not rewritten; the formula; the plugin from the app; `bin/lem`'s Python 3.9 launcher, `lem_python.py` and the `sys.path` inserts go | two install steps, one update command |
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
  step 1 is the half that needs his answers: the formula, the plugin from the app, and the end
  of the Python 3.9 launcher, which is `src/lem/python.py` now.
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
state. The release numbers are proposals; each release is made on the owner's word.

### Stage 1: close the night's work

- [x] The style step, the shared helpers, the package `src/lem/` and the backlog fixes are on
  `main`, with every suite green (`bash tests/all.sh`, 28 suites).
- [x] The defects seen outside those changes are items of `docs/backlog/`.
- [ ] The five items with `worth: yes` are fixed, each with its test, read by a reviewer, and on
  `main`: the bar's three suppression forms, the hook's traceback, a conflict's quoted file names,
  the "waits for" text of a task two releases back, `lem-ask`'s answer that is no object.
- [ ] The owner's answers to the four questions of "Open with him" are bullets of
  `docs/rulings/rulings.md`, and this plan's status is "accepted".
- [ ] Each `worth: later` item of `docs/backlog/` has his ruling, or says what it waits for.

### Stage 2: release 0.4.0, the clean base

Still a plugin with no install step and no dependency. It brings the package layout and the
fixes to the machines that run Lem.

- [ ] One real task runs on `main`'s Lem in a scratch repository (`claude --plugin-dir`), from
  `/lem new` to a merged pull request: the hooks, the board server's start and a landing, on the
  new layout.
- [ ] `README.md`, `docs/install.md` and `site/index.html` say what 0.4.0 is.
- [ ] On his word: `version` 0.4.0, `BEFORE` 0.3.1, the tag, `git push --atomic origin main v0.4.0`.
- [ ] His Mac takes it first (`/plugin marketplace update lem`, `/reload-plugins`,
  `lem serve --ensure`), then mybaze. A defect it shows is fixed in 0.4.1 before stage 3 starts.

### Stage 3: Lem gets its libraries (the rest of step 1), release 0.5.0

What is built here follows his answer to "how Lem ships".

- [ ] A trial in a scratch repository of the way he chose, before any code: for a program from
  Homebrew that hands Claude Code its part, the three cases nobody tried (a repository whose
  committed settings switch Lem on, the session after an upgrade, a session started from an app's
  window); for one plugin with its libraries through `uv`, the first command with no network and
  the start time of a hook.
- [ ] The trial's result is written here, and the way that held is built: the formula in the tap
  (his repository, made by him or on his word), or the plugin's `uv` starter.
- [ ] The Python version he chose, with the checkers' settings, the tests on Lem's own Python and
  CI.
- [ ] `lem doctor`, `docs/install.md` and the site describe the new install; the command lines of
  0.4.0 still work for one release.
- [ ] On his word: release 0.5.0, the first with a dependency.

### Stages 4 to 10: the reshape, a step each

Each stage is one step of "The steps, in order", is done when its row there is true, and leaves
`main` releasable. Each ends with every suite green and with its package in the list of the style
gate (`flake8 --select=WPS`).

- [ ] Stage 4, step 2: the unit cases run under pytest; the shell checks that only call a script
  are unit cases.
- [ ] Stage 5, step 3: one runner for `gh` and `agtermctl`, one error with its exit, a log for the
  server.
- [ ] Stage 6, step 4: a model for each record, checked when it is read; the read defects of the
  inventory fixed, each in a commit of its own. Wide: it reaches 29 of the 41 modules.
- [ ] Stage 7, step 5: the settings as models; `tomlkit` for the edits.
- [ ] Stage 8, step 6: one command tree on a library, the same words and options. Wide: 13
  modules.
- [ ] Stage 9, step 7: the board server on a framework, the pages from templates, Web Push with
  `cryptography`, the peers with `httpx`.
- [ ] Stage 10, step 8: the large functions split; the style gate covers all of `src/lem`, and no
  size mark of step 0 is left.

A release between two stages is his call; the proposal is one after stage 6 and one after stage 9,
so that no release carries more than three steps.

### Stage 11: release 1.0.0

- [ ] `flake8 --select=WPS` over `src/lem` reports nothing, and `ruff`, `pyrefly` and ESLint
  report nothing.
- [ ] No `# noqa: ... over the limit before the limit was set` is left.
- [ ] Every suite is green on the release commit, and the release ran on his Mac and in mybaze
  for a week of real tasks with no defect that a fix release had to repair.
- [ ] The scheduled jobs `lem: night` and `lem: retro` are on again, on his word ("its not use
  until we complete refactoring", 2026-11-24).
- [ ] `AGENTS.md`, the guides and the site describe Lem as it is; this plan gets its status line
  with the commits.

### What each stage asks of him

| Stage | His part |
|---|---|
| 1 | The four answers; a ruling on each `worth: later` item |
| 2 | The word for 0.4.0; a look at the scratch task's pull request |
| 3 | The tap, if Homebrew; the word for 0.5.0 |
| 4 to 10 | The merge of each careful pull request; a release word where he wants one |
| 11 | The word for 1.0.0 and for the scheduled jobs |

## How this work is done

- By Lem itself: each step is one task or a few, on the standard track, careful where a topic of
  `.lem/settings.toml` is in reach (the landing, the records, the settings, the hook: most of
  them). Each ends as a pull request he merges.
- A step that changes how a thing is built changes no behavior with it. Where a defect is fixed
  (step 4), it is a commit of its own with its test.
- A task that moves a file is checked by what the tests prove, not by where they are: Lem's own
  bar counts a moved test file as a lowered bar, so the plan of such a task says which file went
  where.
- The command lines of the release before keep working for one release, as the records do: a
  session that runs while `brew upgrade lem` changes the app has the old skills and the new
  command.

## His rulings that this changes

In `docs/rulings/rulings.md`, in the same commit as this plan:

- "Opinionated and small" is "Opinionated".
- "Lem is a plugin, and nothing else" gives its place to "Lem may be an app and its skills, set up
  in two steps".
- New: "Lem uses the well-known open-source library for a job, and writes no copy of its own."
- New: "Lem's code has a modern style that tools hold."

`AGENTS.md` still says that the scripts are standard-library Python. It says so until step 1
changes the code, since it describes the current state.

## Open with him

1. **Which Python.** "Python 3.11 stays" was ruled when a script ran under the Mac's own
   `python3`. An app brings its own Python through uv. Stay on 3.11, or take 3.14 as mybaze has
   it? The session's pick: 3.14, since no developer installs it by hand and the two projects then
   share one style of code.
2. **New features during the reshape.** Go on beside it as tasks do today, or stop until step 4
   is in? The session's pick: go on. Each step is a set of small tasks, and a pause until the
   records are typed is about half of the reshape.
3. **The tap.** A repository `homebrew-tap` under his GitHub name. He makes it, or says that the
   session may.
4. **The name of the command.** Keep `lem`, and let `lem doctor` say when another `lem` stands
   before it on `PATH`; or give the command another name. The session's pick: keep it.

## Out of scope

- A change of what Lem does: no command, stage, record or page is added or removed here.
- The skills' texts, the stages, the prompts and the harness files, except where a path of a
  script is named.
- The JavaScript beyond step 0: the board's kit stays as it is built today.
- A database, a second agent's harness, and anything `docs/backlog/` holds.
