# Notes of the step `core` for other steps

## `board-service`: the silent server start before a command

`src/lem/__main__.py` (core's) checks the plugin's version and then runs `cli.lazy.main`. It
does not start the board server: that look (`__main__.look_for_server` on `main`: the pid in
Lem's home folder, signal 0, `lem serve ensure` detached with its output in the server's log,
`NO_LOOK = ("serve", "board", "doctor", "ask", "jev")`, off with `LEM_SERVE=off`) needs the
server's pid file and the replace rule, which are yours. Add the call in `__main__.main`, after
`refusal` and before `lazy.main`, as one function of `lem.board`; core agrees to that edit of
its file. Until then no `lem` of the rebuild starts a server, so no run touches the owner's.

## `sessions`: the version line has one place, `src/lem/hooks/versions.py`

`lem` before a command and the `session-start` hook say the same line when the plugin and the
app are two versions. Core wrote it once, with the standard library only, in
`src/lem/hooks/versions.py` (`behind(plugin, app)`), since `lem.hooks` may import nothing else
of Lem. The folder is yours from your step on; keep the function's name and its line, which
`tests/unit/core/test_entry.py` reads.

## `task`: the release stop

`Record.release` is the release a task began on. The store does not set the hold `release`:
the rule that stops a command two releases back, and its hold, are yours.

## `board-duties`: retention

`records/journal/task.py` has `Summary` and `Total`, the entry that a folded journal becomes;
the task's own fields (type, track, lead, careful, investigation, plan talk, night, opened)
stay on `Task`, so the summary keeps only what the journal held. Adjust its fields with a note
here if the prune needs another.

## Every step: what the core gives

- A command's output: `tests/fakes/command.py`, `lem(*args, cwd=...)` and `Ran.envelope()`,
  `Ran.result()`. `Envelope` cannot be decoded with a result (msgspec reads no `Raw` inside
  `Raw | None`), so read it untyped.
- Records for a test: `tests/fakes/records.py`, `record(slug, **task_fields)`, `MOMENT`.
- Ports of fakes: `tests/fakes/ports.py`, `fake_ports(git, forge, ...)`; the app's own:
  `lem.app.wiring.bound(place)`. An adapter module exposes `bind(place: Place)`, and
  `lem.ports.place.Place` is its argument.
- A real repository: `tests/fakes/repo.py`, `RealRepo.init(folder, files)`, with an origin and
  a teammate's clone; `LocalForge(remote=RealRepo or ModelGit)` merges through either.
- A port's contract: subclass the suite in `tests/contract/suites/` with your adapter, in your
  own test file (`tests/contract/test_git.py`, `test_forge.py`, `test_terminal.py`,
  `test_harness.py`).
- Snapshots: `.venv/bin/python -I -B tests --level unit --snapshots create PATHS` writes the
  values `snapshot()` lacks; then `ruff format`.
