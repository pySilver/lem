# Notes of the step `slice-session` for other steps

What the walking skeleton of a task's session needs in files it does not own, the local stand-in
it built until each exists, and what the step `sessions` replaces.

## For `core` (`records/`): a session's open and close in the journal

`lem session open` and `lem session close` put each open and close on record: the agterm session,
its name, the phase it opened in, why, the workspace; for a close, the session and why (main's
`session.open` and `session.close` events). The journal has no entry for them. Asked: two entries
in `records/journal/task.py` and the `Entry` union, `SessionOpened {at, session, name, phase, why,
workspace}` and `SessionClosed {at, session, why: handoff|ended|owner}`.

Until then the slice keeps them in a file of its own, `tasks/SLUG/opened.jsonl`, framed lines as
`store.sessions` writes (`app/sessions/opened.py`, structs `Open` and `Close`). The step `sessions`
moves them into the journal (under the record lock, with `expect`) and removes the file.

## For `core` (`ports/terminal.py`)

1. **`Pane.agent: bool | None`**: whether an agent runs in the session's main pane, read from
   agterm's `foreground` (main's `session.agent_runs`), None while agterm has not drawn it. Main's
   `live` needs it: a session whose agent ended leaves a shell, which is no live session of the
   task. The slice counts every listed session as live.
2. **`Terminal.rename(session, name)`**: `session next` names the old session `SLUG · handed off`,
   and the guard's restart `SLUG · replaced` (`agtermctl session rename NAME --target ID`). The
   slice renames nothing.
3. **`Opening.command`**: the agterm adapter runs the words joined by spaces in the owner's login
   shell (`SHELL -l -c 'WORDS'`), so a harness's launch line is one word of it. The port's
   docstring could say so; nothing else changes.
4. **The caller's workspace**: with `Opening.workspace` None the adapter opens in the workspace of
   `AGTERM_SESSION_ID`, else lets agterm choose. Main refused a task "whose workspace nothing
   names"; the port cannot say "no caller" to the app. Either a `here() -> str | None` of the port,
   or the refusal in the adapter when there is no caller (the contract's "a terminal with no
   session yet" then needs a caller that is not listed).

## For `core` (`ports/harness.py`)

5. **`launch` has no environment for the task**: main's launch line carries `LEM_TASK=SLUG` (which
   the `session-start` hook reads) and `CLAUDE_CODE_AUTO_COMPACT_WINDOW=N` (`handoff.tokens` of the
   machine). The slice reads the slug from the brief's folder (`tasks/SLUG/session.md`) and leaves
   the compaction number out. Asked: `launch(seat, brief, cwd, plugin_dir, task: Slug, tokens: int |
   None)`, or one `Launch` struct.
6. **Whether Claude Code loads an installed plugin**: main gives `--plugin-dir` only when the
   project has no enabled install of `lem@lem` (`session.plugin_installed`). The slice always gives
   the app's root. Either the adapter drops `plugin_dir` by that rule, or a `Harness.loads_plugin(
   checkout) -> bool` for `lem session plugin-dir` too.

## For `tree` (`tests/unit/cli/test_tree.py`)

7. `test_each_stub_refuses_not_built_and_names_a_step_of_the_plan` runs every leaf and wants
   `not-built`; the four leaves this step built (`session open`, `next`, `close`, `list`) give
   their own refusal or their outcome, so the case fails for them (4 FAIL in the unit level of
   `rb/slice-session`). Asked: the case takes out the leaves a step built (a list, or a leaf
   whose module does not call `not_built` for its minimal call).
8. The same case runs each leaf in the test process's working folder: from a worktree of Lem that
   is the owner's main checkout `/Users/Silver/Projects/GitHub/lem`, whose `.lem/state` a built
   leaf reads (it writes nothing there). A built `session list` would ask agterm for its sessions
   if a task there had an open on record; the slice asks the terminal only then. Asked: the case
   runs a built leaf in a throwaway folder, or not at all.

## For `settings`

9. The launch line wants `seats.session` (model and effort) and `handoff.tokens`. The slice launches
   `Seat(agent="claude")` with neither (`app/sessions/opening.py`, `SEAT`).

## For `task`

10. Where a task's worktree is: the slice reads `.lem/worktrees/SLUG` with a `.git`
    (`app/sessions/here.py`, `WORKTREES`). `task worktree SLUG --path` is `task`'s.
11. `stages/new.md` (`slice-land`) may name `lem session wait SLUG --first-line` after `lem session
    open SLUG --why new`: the slice's `open` gives no `then`, since `session wait` is not built.

## For `sessions` (group 2): the slice's shortcuts, each by its file

- `app/sessions/opened.py`: the opens and closes in their own file (note above).
- `app/sessions/placing.py`: every listed session is live; the workspace order is the task's newest
  session's, then its `after` task's, then the caller's (main: the caller's before the `after`
  task's).
- `app/sessions/handing.py`: the phase that ends is the one the newest session opened in, never
  the record's run of states (`session.phase_left`); the old session is not renamed.
- `app/sessions/handoff.py`: the five parts are checked for words, not `## Changed files` for a
  path and a status on each line.
- `app/sessions/closing.py`: no wake ends a close that waits (`session wake` is not built).
- `app/sessions/listing.py`: no `agent`, `unanswered`, `unheard` or `shell`; the signs of the
  newest transcript of the session only.
- `cli/session/open.py`: `--why stopped` refuses `not-built`.
- `adapters/harness_claude.py`: `tokens` of a transcript refuses by name; signs read the
  transcript's last mebibyte (`claude_turns.TAIL`); `available` looks for `claude` on the PATH.
- `adapters/terminal_agterm.py`: `show` and `picker` refuse by name; no `--window`.
- `adapters/claude_transcript.py` and `adapters/claude_turns.py`: two modules of the Claude Code
  adapter beside `harness_claude.py`, which wemake's 7 members a module asked for.
- `hooks/corrections.py`: the gate only; no claim of a message, no worker, no queue.
- `hooks/stop.py`: says nothing; the mark of an open card is `ask`'s with `sessions`.
- `hooks/serve.py`: `lem serve ensure` with its output nowhere (main: the server's log).
