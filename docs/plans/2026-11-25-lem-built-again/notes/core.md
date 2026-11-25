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

## `tree`: the five notes of `notes/tree.md`

1. The log of a fault: `lem.kernel.logs.logged(error, argv, environ) -> Failed`. It appends the
   moment, the command line and the traceback to `lem.log` in Lem's home folder, else writes
   the traceback to standard error and says why in `Failed.log`. It imports no `logging`
   (`tests/unit/core/test_kernel.py` holds that). `cli/faults.py` calls it, and the seam goes.
2. The root of Lem's files: `lem.kernel.paths.root()`, the same rule as `cli/version.py:root()`
   (`data` installed, else the checkout with `skills/lem/SKILL.md`, else a `Fault` that names
   both). `version.root` calls it.
3. `__main__.main` lets an empty `argv`, `help`, `version`, `-h` and `--help` through, and
   `doctor` too; every other command meets the version check. The server start is
   `board-service`'s (above).
4. `tests/unit/core/test_entry.py` no longer expects the stub: it compares `lem help` with
   what `lem.cli.lazy.main(["help"])` prints in the test's own process, so it holds with the
   stub and with the tree (checked against `rb/tree`'s `src/lem/cli/` on a copy: both 0 and
   `Usage: lem ...`).
5. The workspace of a call: `lem.store.places.workspace(folder) -> Workspace` (`checkout`,
   `lem`, `state`). Every leaf calls `places.workspace(place.folder())`. It reads the files git
   keeps (`.git`, `gitdir`, `commondir`), starts no git, and finds the main checkout from a
   task's worktree too; it refuses `no-repository` (fix: run it inside a checkout, or
   `lem --repo PATH`) and `no-lem` (fix: `lem init --base BRANCH`).

## `land-base`: the world of the Git port's contract

`tests/contract/suites/git.py` asks a world for `merge_in(where, ref, files)`: a merge commit
made in a worktree by hand (`git merge --no-ff --no-commit REF`, the files written, a commit),
so that the case "a rebase drops a merge commit and the edit only it made" runs on real git.
The refusal that follows from it (`land.cmd_base`, the merge-only change) is yours.

## For the plan: the folders of the Lem before

- **The rule.** The new Lem never writes into a repository's `.lem/state/` or into Lem's home
  folder when that folder holds the files of Lem 0.3, and reads nothing of such a state folder:
  it refuses `old-state`, with the fix that names the owner's cutover and `lem doctor` (his
  ruling: his repositories start over; the move of the old files is his act).
- **The marker.** `lem-state.json`, the bytes `{"form": 1}` and a line end, in either folder,
  published by a link (the first writer wins, the same bytes are no change) by the first write of
  the new Lem into the folder when it is absent or empty (a state folder may hold `.gitignore`).
  A folder with the marker is of this form; one with anything else and no marker is the Lem
  before's (`lem.kernel.folders.form`, one look).
- **`doctor` and the cutover.** `doctor` names each folder whose form is `old` (the home, and the
  state folder of each workspace) with the cutover's step; the cutover moves those files away,
  after which the first write of the new Lem marks the folder.

## Every step: the one way to write into the home or a state folder

- The home: `lem.kernel.folders.home_for_writing(environ)` gives the home's path for a write;
  `board/`, `settings/`, the add-ons and every other writer of `serve.json`, `workspaces.json`,
  `machine.toml`, `push.json` or a file of its own there call it, never `paths.home` (which is
  for reads). `store.owner.change` and `kernel.logs.logged` already do.
- A state folder: every function of `lem.store` passes `lem.store.guard` (`readable`,
  `writable`); a step that writes a file of its own into `.lem/state/` calls
  `guard.writable(state)` first.

## `sessions`: the hooks' look at the marker

The hooks import nothing of `lem` outside `lem.hooks`, never print and never fail; they do
nothing (no write, exit 0) in a folder of the Lem before. The few lines, for the state folder
(`allowed` = `{".gitignore"}`) and the home (`allowed` = empty):

```python
MARKER = "lem-state.json"
FORM = b'{"form": 1}\n'


def ours(folder, allowed):
    """Whether this Lem may write into folder; marks an absent or empty one."""
    if os.path.isfile(os.path.join(folder, MARKER)):
        return True
    try:
        if not set(os.listdir(folder)) <= allowed:
            return False  # the files of the Lem before: do nothing
    except FileNotFoundError:
        os.makedirs(folder, exist_ok=True)
    try:
        handle = os.open(os.path.join(folder, MARKER), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        return True  # another writer marked it first, with the same bytes
    os.write(handle, FORM)
    os.close(handle)
    return True
```

## Every step: no test reaches a real workspace

The entry starts every test in a folder of its own temporary root, in no repository, and sets
`LEM_TEST_ROOT` to that root; while it is set, the store and the home's writer fault on a
workspace, a state folder or a home outside it (`lem.kernel.folders.inside_test_root`). `tests/fakes/command.lem` runs in the test's own
folder when no `cwd` is named and refuses a `cwd` outside the root. The entry compares the
checkout's own `.lem/state/tasks` before and after a run and fails the run with the names of
what changed. A test that needs a workspace makes one (`tests/fakes/repo.py`).

## Every step: what the core gives

- A command's output: `tests/fakes/command.py`, `lem(*args, cwd=...)` and `Ran.envelope()`,
  `Ran.result()`. `Envelope` cannot be decoded with a result (msgspec reads no `Raw` inside
  `Raw | None`), so read it untyped.
- Records for a test: `tests/fakes/records.py`, `record(slug, **task_fields)`, `MOMENT`.
- Ports of fakes: `tests/fakes/ports.py`, `fake_ports(git, forge, ...)`; the app's own:
  `lem.app.wiring.bound(place)`. An adapter module exposes `bind(place: Place)`, and
  `lem.ports.place.Place` is its argument.
- A real repository: `tests/fakes/repo.py`, `RealRepo.init(folder, files)`, with an origin and
  a teammate's clone; `LocalForge(remote=RealRepo or ModelGit)` merges through either, by
  squash, merge or rebase, and reports the base each merge went onto.
- A write of a record of a newer form or release is refused by the store (`record-form`,
  `newer-release`); the stop of a task two releases back stays `task`'s.
- The ledger's cases are part of the `unit` level: `--level unit` runs `tests/unit` and
  `tests/ledger`, and a path in either is a path of `unit`.
- A port's contract: subclass the suite in `tests/contract/suites/` with your adapter, in your
  own test file (`tests/contract/test_git.py`, `test_forge.py`, `test_terminal.py`,
  `test_harness.py`).
- Snapshots: `.venv/bin/python -I -B tests --level unit --snapshots create PATHS` writes the
  values `snapshot()` lacks; then `ruff format`.
