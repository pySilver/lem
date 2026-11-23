# Lem as an app with dependencies, in a pythonic shape

> **Status: proposed**, for the owner to read. Nothing of it is built but step 0, which is the
> branch `chore/python-js-style`. The four questions at the end are his.

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
Step 1 comes first because nothing can depend on a library before the app installs with its
dependencies. Step 2 comes next because every later step leans on the tests, and they should be
in the form the new code's tests take.

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
