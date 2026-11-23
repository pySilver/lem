# Claude Code: a task's own session

A part of `../claude-code.md`, read when a session opens one (`open-task-session`), copies a talk,
or meets a wake-up that did not arrive.

## open-task-session

Two kinds: a task's own session, and the plan talk's pair that a lead opens under it.

## A task's own session

`lem session open SLUG` opens it, never a line of this file, so that its name, its place and one
session for each task hold the same way each time: run twice, it opens one, and prints the one
that runs with `already: true`. It writes `session.md` into the task directory and runs, in
agterm's own words:

```bash
agtermctl session new --workspace WS --cwd DIR --name SLUG --no-select --command "LOGIN_SHELL -l -c 'LEM_TASK=SLUG CLAUDE_CODE_AUTO_COMPACT_WINDOW=N claude \"Read TASK_DIR/session.md and follow it.\"'"
```

then `agtermctl session move --to bottom`, and never `agtermctl session select`: the task's session
goes after the last session of its workspace, so the one the owner keeps first stays first, and it
never takes the focus, and only the owner's own act selects it. `DIR` is the
main checkout, also for a task with a worktree, which the session reaches by its path
(`owner-steps.md`, "A folder's trust"). A trial on 2026-11-21 (agterm 0.41.1 serving and 0.43.0
installed, Claude Code 2.1.330) showed:

- The session opened at the top level of the workspace and was not selected, and the selection
  stayed where it was.
- A probe on 2026-11-23 (agterm 0.41.1 serving) put `move --to bottom` after the workspace's last
  session and its companions, and `--to top` before the owner's first session. A companion,
  `session new --parent` or `session overlay open --companion` (`lem board`), went after the last
  companion of its session with no move.
- `session new` takes no environment, so the two variables are in the launch line, and `ps eww`
  showed the variable in the Claude process. A builder inherits both.
- `LOGIN_SHELL` is the owner's login shell by absolute path (`dscl . -read /Users/NAME UserShell`):
  agterm starts the command with its own `PATH`, and only the login shell finds `claude` the way
  the owner's terminal does. The line passes no flag that widens the session's permissions.
- Claude Code showed its trust dialog for a folder it had never trusted, with "No, exit" selected
  first. Nothing of Lem answers it ("What the owner does himself", `owner-steps.md`).
- A session opened with a command leaves no shell when its agent ends: after `/exit` the session
  left agterm's tree at once. A task whose agent ended has no session, and the board says so.
- Each idle session posts agterm's "Claude is waiting for your input". One of the trial's two
  sessions closed 1.3 s after such a notice with no command of the trial's, most likely by a hand.

`lem session open` puts the model and the effort of `seats.session` on the launch line
(`claude/opus:high` when no file names the seat); a part that a named seat leaves out is the
owner's default of Claude Code. When this Lem is not the installed plugin (its folder is
outside `~/.claude/plugins/`, or outside `plugins/` of `CLAUDE_CONFIG_DIR`), the line adds
`--plugin-dir` with that folder, so that the task's session runs the Lem that opened it. That holds
where no Lem is installed: with an older Lem installed for the project, the `lem` on such a session's
`PATH` is the installed one (lem-scratch, Claude Code 2.1.330, 2026-11-21), so a clone is tried with
the installed plugin switched off. A launch with `--model` and `--effort` ran (the same day). Not run yet: a relaunch of agterm in its
rerun mode, which starts each session's command again: the agent then starts from its first
message, and `prompts/session.md` reads the state before anything else, so it goes on or stops.

`lem session close SLUG [--session ID] --why ...` logs the close and then runs `agtermctl session
close --target ID --undoable`. An `ID` is refused unless a `session.open` of that task names it (an
older session of the task counts). It refuses a session the owner has selected; with
`--when-unselected` it looks every 5 seconds (a guess) and closes it once he left it, so it runs in
the background; a wake of that session meanwhile ends the wait with no close (`closed: false`,
`woken: true`). `lem session list` gives each task's newest session: whether it lives, runs an
agent and is selected, the phase its task is in now (`phase`) and the one it opened in
(`opened_in`), `unanswered`, a wake-up still in its mailbox after 10 minutes (never the guard's
status message), and for a live session its signs of work from Claude Code's own files
(`lem_signs.py`): `sign`, the time of the newest turn of its main thread or a subagent, `shell`,
whether a shell command of it runs, and `signs`, whether the two could be read.

## The context's number

`N` is `[handoff] tokens` of `~/.config/lem/machine.toml`, the owner's number for all his
repositories: 600,000 when the file has none, written with `lem project handoff --tokens N|default`
and shown by `lem doctor`. With 0 Lem sets nothing, and Claude Code compacts at its own trigger,
"at about 967K tokens by default" on a 1M window (Claude Code's model-config page, read
2026-11-21). Claude Code refuses a window under 100,000, and so does Lem. Past the number Claude
Code compacts the session by itself; background commands and background subagents keep running
through it (the context-window page, read 2026-11-21). The plugin brings two hooks for it, which
read no transcript and do nothing without `LEM_TASK`:

- `PreCompact` prints the summary's form, the five headings of `handoff.md`. Its output "becomes
  instructions for the compaction summary", 10,000 characters at most (the hooks reference, read
  2026-11-21).
- `SessionStart` with the source `compact` prints the task's newest state block and `handoff.md`
  with its time, under "the state is the truth; where the handoff is older, follow the state".

Both hooks ran in a compaction the owner's `/compact` started, in a landing session that waited for
a merge: the summary took the handoff's form, and the state came back after it (lem-scratch,
2026-11-21). Not run yet: a compaction at the number.

## A wake-up

Nothing of a task's session watches GitHub or another task. The board's server runs `lem session
wake SLUG --why merged|conflict|refused|queue|owner|inbox|status` (`owner` after his approval or his park on
the board, `inbox` after a question it sent to his Inbox or his reply in a thread whose session is gone,
`status` the guard's status message after 45 minutes with no sign of work, or with no event of the task when the signs do not read), which sends `agtermctl msg send "lem: SLUG WHY" --to
ID:left` to the task's live session, or opens one when none lives (never for `inbox` or `status`). `replaced`
is sent only by `lem session open SLUG --why stopped`, to the old session beside the fresh one. In the trial of 2026-11-21 the
idle agent took a turn within 15 s each time, five sends in two sessions, two of them after about
two minutes idle, with no `--socket` too (`agtermctl` finds the app's socket itself), and `ID:left`
reached a session with no split. The line arrived as `[agterm mailbox, not a peer chat message]
from outside agterm:` and its body, marked "NOT user input". So the session reads the files and
never the line. A wake reaches an agent only through the mailbox chat's waiter, a hook of the
owner's home settings (`mailbox-chat.py claude-hook`): the mailbox chat is a required tool of Lem,
and `lem doctor`'s row for it says so. A line reaches the agent only when its turn ends, since the
waiter keeps mail while a turn is busy (`mailbox-chat.py`, `Waiter.loop`, read 2026-11-22): a
`replaced` line ends no turn that runs, and the old pane closes itself when that turn ends. Mail is kept in memory only,
so a pane that was restarted has lost it; a wake nobody took shows on the board after 10 minutes,
except the status message, whose wait the guard itself ends. Not run yet: a wake after an hour idle.

## The session's transcript

`lem session talk SLUG --from TEXT [--leave TEXT ...]` copies the turns of the session it runs in,
the one where the owner typed the request, into the new task's `talk.md`, from the transcript
Claude Code keeps of it: the file `~/.claude/projects/*/ID.jsonl`, with `ID` from
`CLAUDE_CODE_SESSION_ID`, which Claude Code gives the Bash tool (`CLAUDE_CONFIG_DIR`, when it is
set, stands for `~/.claude`). Run it from that session, never from a builder's. The transcript
keeps the turns from before a compaction, so the copy is word for word after one too (495 owner
records before the first `compact_boundary` in one transcript of Lem's own repository, read
2026-11-19). One JSON record a line, read this way (40 transcripts of Lem's own repository,
Claude Code 2.1.328, 2026-11-19): an owner's turn is a `user` record whose `origin.kind` is
`human`, with no `isMeta` (the text a skill loads) and no `isCompactSummary`; a task's
notification, agterm's mail and a peer's message have another origin; a `/lem` line is a command
record (`<command-name>/lem:lem</command-name>` with its `<command-args>`), copied as `/lem ARGS`;
a record with a `tool_result` and one with `isSidechain` (a subagent's) are no turn; the agent's
turn is the text blocks of the `assistant` records between two prompts. A transcript in which no
prompt has an origin is refused, since the owner's turns cannot then be told from the rest.
Untested: whether `CLAUDE_CODE_SESSION_ID` follows a `/clear`.
