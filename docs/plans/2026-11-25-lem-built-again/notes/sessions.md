# Notes of the step `sessions` for other steps

What the step `sessions` needs in files it does not own, the local stand-in it built until each
exists, and what other steps take from it.

## For `core` (`records/`): Lem's acts on a task's sessions in the journal

The slice's request stands, wider. `lem session open`, `close`, `wake`, `stopped`, `worked` and
the guard's restart put each act on record. The journal has no entry for them, so they are framed
lines of the task folder's `session-acts.jsonl` (`app/sessions/acts.py`: `Open {at, session, name,
phase, why, workspace}`, `Close {at, session, why}`, `Wake {at, session, why, head, unread}`,
`Stopped {at, session, unread}`, `Worked {at, session, turn}`; `app/sessions/log.py` reads and
writes them). Asked: the five as members of the journal's `Entry` union. Then `log.py` reads them
from `task.json` and appends under the record lock with `expect`; the guard's timeline
(`guard_look.timeline`) orders them with the work by the journal's own order instead of by the
second, which today keeps an act before work of the same second.

## For `core` (`ports/terminal.py`, `ports/harness.py`)

1. `Terminal.rename(session, name)`, a look at each session's main-pane program (`Pane.agent`,
   or `foregrounds() -> {id: argv | None}`), and a read of a pane's mailbox (`waiting(session,
   line) -> bool`). The agterm adapter has all three beside the port (`adapters/agterm_sessions.py`,
   `AgtermLooks`), and `app/sessions/beside.py` takes them through a runtime-checked Protocol that
   faults by name when a terminal lacks them. Once on the port, `beside.py` goes.
2. The caller's session: `app/sessions/here.py` reads `AGTERM_SESSION_ID` (or `AGT_SESSION_ID`)
   itself, the one agterm name in `app/`. A `Terminal.here() -> str | None` would hold it.
3. `Harness.plugin_folder(plugin_dir) -> Path | None`: the adapter has it beside the port, and
   `lem session plugin-dir` calls it on the Claude Code adapter directly.
4. A transcript's main-thread sign: a session's turn is the one of the transcript whose main
   thread wrote the newest turn, and `Signs.sign` counts the subagents too. The Claude Code
   adapter gives `main_sign(transcript)` beside the port (`ClaudeHarnessLooks`), taken through
   `beside.main_signs`. Asked: a `main` field on `Signs`.
5. `Signs.read: bool`: a transcript whose process is gone gives `Signs()`, which the app reads as
   "not read" (`app/sessions/signs.py: read`); a live session with no turn yet looks the same.
6. `pyproject.toml`: `psutil` is a dependency (commit `fcac0bc8`); `types-psutil` in the dev group
   would end pyrefly's untyped-import warning.

## For `settings`

- The seats: `app/sessions/seating.py` reads `[seats]` (reviewer, planner, merger, session,
  fallback) from `.lem/settings.local.toml`, `.lem/settings.toml` and the home's `settings.toml`,
  first file first, else Lem's `claude/opus:high`, with the form and the agents each seat takes.
  It is a stand-in: when `settings/` gives the seats with their source, `seating.seat_of` calls it.
- `[handoff] tokens` of the machine's file: `adapters/claude_launch.py` (`machine_of`) reads it with
  `tomllib` until the machine's struct exists. Its write is `lem settings set handoff.tokens N
  --machine` (rows `Tokens.*` and `Load.*` moved to you in `tests/ledger/moves/sessions.tsv`).

## For `task`

- The first line: `lem session wait SLUG --first-line` ends when the record has its read
  (`Shape`), and makes the line from the task, its type, the owner's words and the track
  (`app/sessions/first_line.py: line_of`). `main`'s opening line (`compose_opening_line`: careful,
  branch, the order, the queue, what comes after) belongs to `task read`. Asked: `task read` keeps
  the line it says on the record (a `say` of `Shape`, which is `core`'s), and `line_of` repeats it.
- `app/sessions/phase.py` reads the hold of a `Blocked` task by its status, and an `OwnerHold` on
  `plan` as the build's; `task`'s table of holds decides both.

## For `board-duties` and `board-acts`

- The guard of a stopped session is built here as a rule over the task's timeline
  (`app/sessions/guard_rule.py`, `guard_due.py: due`) and four steps that look once more in the
  task's lock (`guard_steps.stepped`: `status`, `restart`, `stopped`, `worked`). The duty asks
  `guard_due.due` over `guard_look.looked(here, slug, now)` and runs the step's command
  (`lem session wake SLUG --why status --session ID`, `lem session open SLUG --why stopped
  --session ID`, `lem session stopped SLUG --session ID`, `lem session worked SLUG --session ID`).
  The owner's "Open a session" on a stopped task is `lem session open SLUG --why stopped` with no
  `--session`. The `worked` step is taken (`main` held it back one release).
- `lem session open` does not put the workspace on `workspaces.json` (`project.register_checkout`
  on `main`): that file is `board-service`'s; the open could call its writer, or the board's
  start could list the workspace.

## For the plan: where the correction queue is

`main` keeps the queue in the project's state folder ("The queue is one file for one project:
`corrections.jsonl` in Lem's state folder", `corrections.py` docstring at `bf6d2836`), and so
does the hook; the design's part 3 lists "the correction queue" under the home folder. The
review of this step asked for the home. The step keeps `main`'s place, which `[corrections]
collect` of the machine's file (one yes for the machine) does not change; the orchestrator
decides, and `addons-flow`'s worker follows.

## For `ask` and `addons-flow`

The part `hooks` of this step left them these (its rows are in `moves/sessions.tsv`):

- `ask`: the Stop hook says nothing. The mark of an open card needs a card file the hook finds
  with `os` alone, its no-status choice, and the `[ask]` status words; `hooks/stop.py` is this
  step's file, so `ask` writes here what the hook reads and this step's owner applies it.
- `addons-flow`: the correction hook claims a message once and writes one `Correction` (msgspec's
  keys) to `.lem/state/corrections-waiting/NS-PID.json`, then starts `lem corrections worker PATH`
  detached. The worker reads it, removes the file, asks Jev, and appends to `corrections.jsonl`;
  `corrections.log` lines are `{at, session, note|error}`.
