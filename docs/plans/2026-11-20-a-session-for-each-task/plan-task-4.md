# Task 4. A session for each task: the build plan

The contract is `shape-task-4.md`; builders read it first, and this plan reopens none of it.

## The trial (2026-11-21; agterm 0.41.1 serving, 0.43.0 installed; Claude Code 2.1.330)

No session of the owner's was touched or selected.

1. Open: `agtermctl session new --workspace CC105DA5-… --cwd /tmp/lem-trial-wake --name "lem trial · wake" --no-select --command "/opt/homebrew/bin/fish -l -c 'CLAUDE_CODE_AUTO_COMPACT_WINDOW=600000 claude \"…\"'" --json`: top level, not selected. `ps eww` showed the variable in the Claude process.
2. Claude Code showed its trust dialog for the new folder, **"No, exit" selected first**; I answered it with `agtermctl session type`.
3. The server's form: Python `subprocess.run`, environment `{HOME, PATH}` only, `agtermctl msg send TEXT --to ID:left --socket SOCKET --json`. The idle agent took a turn within 15 s. It got `[agterm mailbox, not a peer chat message] from outside agterm:` and the body, marked "NOT user input".
4. With **no `--socket`** it woke too: `agtermctl` finds the app's socket itself.
5. Five sends in two sessions woke the agent five times, two after about two minutes idle (00:31:00 to 00:33:49; 00:35:53 to 00:38:05). `ID:left` reached a session with no split.
6. The first session closed 1.3 s after the second send (`agtermctl recent list`, 00:33:50.36). No command of mine closed it, and the second session took the same send and stayed. Most likely a hand closed it after agterm posted "Claude is waiting for your input" (a `notify` event).
7. `agtermctl session move --to top` put the session first; the selection stayed.
8. `/exit` ended the agent, and the session left the tree at once: **a `--command` session leaves no shell; it leaves no session.**
9. A wake reaches an agent only through the mailbox chat's waiter, a hook of the owner's home settings (`mailbox-chat.py claude-hook`); waiters here had run 3 and 4 days (`ps`).

Untested: a compaction at the number; the two hooks; trust for a worktree in a trusted checkout; a wake after an hour idle; a relaunch in rerun mode.

**Result: a pane message from the server wakes an idle task session; the fallback is not needed.**

## 1. The forms

### `lem session` (`skills/lem/scripts/session.py`)

Each prints JSON and exits 1 with the fix.

- **`open SLUG [--focus] [--why new|handoff|dead|merged|conflict|queue|night|owner]`**
  - The phase comes from the state, never from an argument: no block, or `held` for the interview or criteria, is `shape`; `track: fast` is `fast`; `building`, `planned`, `blocked` and a breaker's `held` are `build`; `ready`, `landing`, `open` and a `landed` task not cleaned are `land`.
  - Under the task's lock (`session.lock`): when agterm's tree has the newest `session.open`'s session with an agent (`agent_runs`), it prints it with `already: true`.
  - Otherwise it writes `session.md` and runs `session new --workspace WS --cwd DIR --name SLUG --no-select --command "SHELL -l -c 'LEM_TASK=SLUG CLAUDE_CODE_AUTO_COMPACT_WINDOW=N claude \"Read TASK_DIR/session.md and follow it.\"'"`, then `session move --to top`, and with `--focus` `session select`. `DIR` is the worktree, else the main checkout. With tokens 0 the variable is left out.
  - It logs `session.open {session, name, phase, why, workspace}` and prints `{task, session, name, phase, already, say}`.
  - It refuses: no such task; ended and cleaned; `parked`; `queued` behind an open task; no agterm; no known workspace; an unquotable path.
- **`next SLUG [--same]`**, the change of phase: checks `handoff.md`; refuses while the state still gives the caller's phase, unless `--same` (his "hand off"); renames the caller `SLUG · handed off`; runs `open --why handoff`; prints the background line `lem session close SLUG --session OLD --why handoff --when-unselected`.
- **`close SLUG [--session ID] --why handoff|ended|owner [--when-unselected]`**: logs `session.close`, then `session close --target ID --undoable`. It refuses a selected session; `--when-unselected` looks every 5 s (a guess) and closes once he left it.
- **`handoff SLUG --check`**, and **`talk SLUG --from TEXT [--leave TEXT]`**, `companion.py`'s `talk` moved as it is.
- **`wake SLUG --why merged|conflict|queue`**: a live session gets `msg send "lem: SLUG WHY" --to ID:left`, logged `session.wake`; the agent reads the files, never the line. No live session: `open --why WHY`.
- **`wait SLUG --until STATE,… | --event NAME`** looks every 10 s (a guess); run in the background, its end wakes the caller.
- **`list`**: each task's newest session, `live`, `agent`, `selected`, `phase`, and `unanswered` (a wake still in the mailbox after 10 minutes, `msg read --as ID:left`, no ack).

### The record

The event log, which the board reads: `session.open`, `session.close`, `session.wake`. No state or brief line names a session; the plan talk's `session: ID` goes. `session.md`: `Read SKILL_DIR/prompts/session.md and follow it.`, then `task:`, `phase:`, `opened because:`, `task directory:`, `main checkout:`, `worktree:`.

### `[handoff] tokens`

- `~/.config/lem/machine.toml`, read by `lem_state.handoff_tokens()`: absent is 600000; 0 is None, and Lem sets nothing.
- It refuses a negative, a value under 100000, a bool and a float, with the fix.
- `lem project handoff --tokens N|default` writes it, as `load --start` does. `lem doctor` shows `handoff tokens: 600000 (default)`.

### The environment

`LEM_TASK=SLUG` and `CLAUDE_CODE_AUTO_COMPACT_WINDOW=N` in the launch line, since `session new` takes no environment (measured to reach the process). Builders inherit both.

### The hooks

`session_hook.py`, two entries in `hooks/hooks.json`; without `LEM_TASK` or a task directory, silent, exit 0. No hook reads a transcript.
- `PreCompact` (`auto|manual`) prints the summary's instructions: "This summary is the handoff of task SLUG, phase P, under five headings: Settled; Open; Next step; Failed; Changed files, each path with its status. Link a plan, a record or a commit by path or id; copy none of their text."
- `SessionStart` (`compact`) prints the newest state block word for word, then `handoff.md` with its time, under "the state is the truth; where the handoff is older, follow the state".

### `handoff.md`

A template, `templates/handoff.md`, checked as `templates/breaker.md` is: the line `task: SLUG · from PHASE · written: TIME`, the five headings, and a path and a status on each "Changed files" line. Why: three readers share the form (the next agent, `PreCompact`, `lem project resume`), and the changed files are the weakest part of every measured summary (`research-compaction.md`, part 2).

### A change of phase

1. The leaving agent writes the state block, then `handoff.md`, runs `lem session next SLUG`, says one line, starts the printed `close` in the background, and stops.
2. The new agent reads `session.md`, the state (`lem project tasks`), `handoff.md` where newer than the state, then its phase's text.
3. Only while no builder and no check runs: the agent waits for its own background work, since no script sees a subagent.
4. A dies before `next`, or B at its start: "no session", and one click opens from the state. A dies after `next`: nothing lost; `list` reads the newest session only.

### Each phase

- **First message**, always `Read TASK_DIR/session.md and follow it.` `prompts/session.md` sends `shape` to `stages/interview.md`, `build` to `brief.md` and `prompts/lead.md` (the lead is the session's own agent; builders are subagents), `land` to `stages/land.md` for this task, `fast` to "The fast track" of `stages/new.md`.
- **A new idea**, `/lem WORDS` anywhere: the caller picks the slug, runs `task-dir --ask`, `session talk`, `session open --why new --focus`, and says `say`. The new session reads the type and the track; on the fast track it stays one session. The board, the backlog and the night pass no `--focus`.
- **The shape** keeps the watch of the owner's mark, and sets agterm's attention mark while it waits for him.
- **The fast track**: one session to the merge; its builder is a subagent (`prompts/small.md`); landing, merge agent and cleanup run there.
- **The landing** runs task 3's merge agent, waits idle while `open`, takes step 8 after a merge (its agent's, or the server's wake), then `close --why ended --when-unselected`.
- **The plan talk**: the lead opens `SLUG · plan talk` under its own session (`open-task-session`), waits with `lem session wait SLUG --event plan.talk`, closes it and builds.
- **The night**, item by item: `task-dir --night`, `session open --why night`, `session wait SLUG --until open,held,blocked,landed,dropped,answered`.
- **Bare `/lem`** anywhere: `lem project waiting` and the board, plus the task's line in a task session. `park`, `drop`, `be-careful`, `standard-track` with no slug mean `LEM_TASK`.
- **"hand off"**: `handoff.md`, then `lem session next SLUG --same`.
- **The copied talk**: `talk.md` in the task directory, as today.

## 2. The server's duties

In `forge_loop`'s thread, under `SCRIPT_LOCK`; `session open`'s task lock keeps a click and a duty from opening two sessions.

1. **Merge**: after `lem land merged SLUG` writes `landed` or `dropped`, `lem session wake SLUG --why merged`.
2. **Conflict**: a pull request GitHub calls `CONFLICTING` gets `wake --why conflict`, once for each head (`session.wake` keeps the head).
3. **The queue**: each `queued` task whose `after:` task ended and that has no live session gets `session open --why queue`.
4. **No session**: a "Waits for you" row (`kind: session`) for a task not ended, parked or queued (or `landed`, not cleaned) whose newest session is gone from the tree or runs no agent, or that has none at 2 minutes old (a guess). A wake unanswered for 10 minutes gives the row as "does not answer". The click posts `agterm/open`, which runs `lem session open SLUG --why dead` (or `--why owner`, a new session). The row sends the push.
5. **The workspace**: the task's recorded one, else its `after:` task's, else the repository's newest; with none, the row says to type `/lem status SLUG`.

**Never**: type into a session (`session type` goes), select one without his click, close one, decide, or write a task file except through `land merged` and `lem session`.

**When it does not run**: the board does not load. `bin/lem` runs `serve.py --ensure` before any command but `serve`, as the `SessionStart` hook does. Every duty is read from the files at the next look, so a pause costs only time.

## 3. What goes

| Duty today | Where | After |
|---|---|---|
| take an ask | `new.md` | the caller names and opens; the new session reads type and track |
| interview, criteria | `companion.py`, `prompts/companion.md` | the shape session |
| start the lead | `companion due`, `start.md` | `session next` |
| a lead's stop | `stopped.md` | the build session itself |
| the landing | Lem's session | the land session |
| `land watch`, `land merged` | `SKILL.md` Status | the server |
| conflict repair | `land.md` 9 | server wakes, land session repairs |
| the queue | `start.md` | the server |
| breaker talk | `SLUG · breaker N` | the build session |
| owner watch | Lem's background | the shape session |
| `tell-coordinator` | briefs, harness | nobody: files and `session wait` |
| typed `/lem new`, `/lem status` | `serve.py`, `agterm.json` | `agterm/open`, `session open` |

Files that go: `companion.py` (`talk` moves), `prompts/companion.md`, `stages/open-interview.md`, `stages/stopped.md` (into `prompts/session.md`), `tests/lem-companion.sh`, `serve.py`'s `type` and `AGTERM_RECORD`, `board.py`'s `agterm.json`, the board model's companion events. `project.py` keeps `answered_holds`'s rule itself.

## 4. Stages

Each starts from `feat/parallel-landings` after task 3 is merged in, because `land.md` and `land.py` carry the merge agent. A, B and C run together in three worktrees, on the interfaces of section 1.

**A. The session scripts.** Outcome: `lem session`, the hooks, `[handoff] tokens`, the template; `companion.py` gone.
- Owns `session.py`, `session_hook.py`, `templates/handoff.md`, `tests/unit/test_session.py`, `tests/lem-session.sh`.
- Shared regions: `hooks/hooks.json` (two entries); `lem_state.py` `MACHINE_KEYS`, `MACHINE_FIX`, `handoff_tokens` (task 3 adds `[seats]` there); `project.py` `cmd_waiting` and a `handoff` subcommand; one `doctor.py` row; `bin/lem` (`companion` to `session`, `--ensure`); `tests/all.sh`, `tests/pick.py`.
- Tests: unit cases for the phase from the state, the handoff check, the tokens key (absent, 0, 99999, −1, `true`), and the hooks with and without `LEM_TASK`. `lem-session.sh`, with `lem-companion.sh`'s `agtermctl` stand-in: `open` twice is one `session new`; the line holds `--no-select` and both variables, then `move --to top`; `next` logs, renames and opens; `close` refuses a selected session.

**B. The server and the board.** Outcome: section 2.
- Owns the duties in `serve.py`; the `session` row and its click in `lem_board_model.py`, `lem_board_pages.py`, `board.html`; `board.py` without `agterm.json`.
- It calls only `session open|wake|list` and reads `session.*` events; a stub with the agreed JSON serves until A lands.
- Tests: unit cases for the no-session rule and for which duty fires (merged, conflicting, queued, a demo). One `lem-serve.sh` check: a merged pull request runs `land merged`, then `msg send` to the task's session.

**C. The texts: one stage, one builder.**
- `SKILL.md`: "One session for each task" replaces "Two levels"; Status loses the duties of each turn; bare `/lem`.
- Stages `new`, `interview`, `start`, `status`, `away`, `breaker`, `park`, `land`, `night`, `correct`; prompts `session.md` (new), `lead.md`, `small.md`, `defender.md`.
- Harness: `open-task-session` for a task session and the talk's companion; `tell-coordinator` goes; `claude-code.md` takes the trial's facts.
- Docs `flow.md`, `when-lem-needs-you.md`, `board.md`; a draft `agents-text-task-4.md` beside this plan, as task 2 did.
- No tests: a stage text's test is a real task.

**D. Integration**, by the coordinating session: merge A, B and C, run `tests/pick.py`'s suites, `tests/all.sh` once, then a real task in lem-scratch.

## 5. Risks, and what the first real task proves

1. **A deaf agent**: the wake rests on the owner's mailbox waiter; `list`'s `unanswered` shows a miss. The first task shows a GitHub merge waking its land session, which cleans.
2. **The trust dialog** stops a session in a folder never trusted. Check: one session on a new lem-scratch worktree, read with `agtermctl session text`. If it shows, open in the main checkout and work in the worktree by path.
3. **The number and the hooks**: `/compact` in a task session; the summary has the five headings, and the state comes back.
4. **Idle notifications**: each idle session posts "Claude is waiting for your input" (trial step 6). Count them on the first day, then decide.
5. **`--when-unselected`**: a handed-off session closes when he leaves it.
6. **A relaunch in rerun mode** starts each agent again with its first message, which the state-first rule makes safe. Check one with a task `open`.
7. **Cost**: a fresh session starts at about 84k tokens (Fable's median of 10 sessions); read each task's tokens from its transcript.
8. **An unexplained close** (trial step 6): a session gone with no `session.close` goes to the owner.

## 6. Open points, with the session's pick

1. **The record**: events only, since the board reads the log and one place cannot disagree with another.
2. **An old session he has selected** closes itself in the background once he leaves it.
3. **Focus**: only for `/lem WORDS` typed in a session, where he is talking about it.
4. **A land session waiting for his merge** stays idle: a reopen costs a fresh 84k start.
5. **A wake nobody takes**: a row for him, never an automatic replacement, which could end a live agent's long turn.
6. **The plan talk's end**: the lead waits on `plan.talk`, so `tell-coordinator` goes.
7. **The queue and the fast track**: the server alone starts a queued task; the fast track's change is a subagent's, so the session stays small.

## 7. The coordinating session's decisions on this plan (2026-11-21); where a line above differs, this holds

1. **Open points 1 to 7: taken as picked**, with the two changes below.
2. **"No session" is a row only when something is stuck.** A task that is `open` and waits only for the
   owner's merge or for the merge agent's call gets no row when its session is gone: at the merge the
   server's `wake` opens a session for the cleanup, so nothing is lost and nothing nags him. The row shows
   for a task in a phase that needs an agent to go on (the shape waiting for him counts: he cannot answer
   with no session), for a wake that nobody took after 10 minutes, and for a merged task whose cleanup
   session could not be opened. Every task with no live session has an "Open a session" button in its
   header on the board, row or no row. Criterion 8's wording ("a task that did not end") is the session's
   own, from Fable's opinion, so this narrows no word of the owner's.
3. **The server is started by a cheap look, never by a process for each call.** `bin/lem` reads the
   server's pid file and asks the kernel whether that process lives (no subprocess, no HTTP); only when it
   does not, it starts `serve.py --ensure` detached and goes on without a wait. The variable `LEM_SERVE=off`
   turns the look off, and `tests/lib.sh` sets it, so that no test starts a server it did not ask for.
   Measure the added time of a usual call and report it.
4. **The session's seat.** A task session is a top-level agent, so the builder agent's pinned model no
   longer covers the lead. One optional seat, `seats.session`, in the form `agent/model:effort`, with the
   three sources that task 3 gives `seats.merger` (the repository's settings, `[seats]` in
   `~/.config/lem/machine.toml`, else the agent's own default). The launch line names the model and the
   effort only when the seat does (read `claude --help` for the flags; where the command has no flag for
   the effort, the seat's effort is refused with one line that says so). Only `claude` for now. No model's
   name in Lem's code.
5. **The trust dialog.** `session open` never answers a dialog by typing. When the first real task shows
   the dialog for a worktree of a trusted checkout, the session opens in the main checkout and works in
   the worktree by path (risk 2); builders of stage A test which it is in lem-scratch before they choose
   `DIR`, and say what they saw.
6. **The mailbox waiter** is the owner's hook, and the mailbox chat is a required tool of Lem (his ruling).
   `lem doctor`'s row for it says that the wake-up of a task session rests on it.
7. **Stages A, B and C start after task 3 and the board's actions (stage S7) are both merged** into
   `feat/parallel-landings`: S7 changes `serve.py`'s POST routes and the board's pages.
