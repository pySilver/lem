"""A task's own session in agterm: one session carries one task, and each phase starts a
fresh agent.

    lem session open SLUG [--why new|handoff|dead|merged|conflict|refused|queue|night|owner|stopped] [--session ID]
                                 open the task's session for the phase its state gives, with no
                                 focus, or print the one that runs; `--why stopped` opens a fresh
                                 one beside a stopped live one
    lem session next SLUG [--same]
                                 the change of phase: check handoff.md, open the next session and
                                 name the old one `SLUG · handed off`; `--same` for the owner's
                                 "hand off" inside a phase
    lem session close SLUG [--session ID] --why handoff|ended|owner [--when-unselected]
                                 log the close, then close the session; never one the owner has selected,
                                 and with --session only one a `session.open` of SLUG names
    lem session close-job [--session ID]
                                 close the session of a scheduled night or retro, its own last step,
                                 once the owner has left it; never a task's session, and never one
                                 whose agent a job did not start with `/lem night`, `/lem night N`
                                 or `/lem retro`
    lem session handoff SLUG --check
                                 check handoff.md against `templates/handoff.md`
    lem session talk SLUG --from TEXT [--leave TEXT ...]
                                 copy the turns of this session about the ask into the task's talk.md
    lem session wake SLUG --why merged|conflict|refused|queue|owner|inbox|status [--head SHA] [--session ID]
                                 a pane message to the task's live session, or a new session;
                                 `--why status` only to a live one
    lem session stopped SLUG [--session ID]
                                 log that the task's session stopped after its status message and
                                 its restart, or after the message alone when Lem cannot read its
                                 signs, so that it waits for the owner
    lem session wait SLUG --until STATE,... | --event NAME | --first-line [--companion ID [--quiet FILE]]
                                 end when the task's state is one of these, or a new event is logged,
                                 or the task's first line is written, or when the task's session is
                                 gone (`"gone": true`), or with --companion when that companion of the
                                 waiting session is gone (`"gone": true, "companion": ID`), or with
                                 --quiet when FILE has not changed for 45 minutes since the later of
                                 its last change and the wait's start (`"quiet": true`)
    lem session list             each task's newest session: live, agent, selected, the phase the task is
                                 in now and the one the session opened in, unanswered, and its signs
                                 of work (sign, shell, signs, turn)
    lem session plugin-dir       the folder that `--plugin-dir` names on a launch line of this Lem, or
                                 null when this Lem is the installed plugin: the task's session and
                                 the plan talk's pair run the Lem that opened them

The phase comes from the task's state, never from an argument: no state block, or `held`
for the interview or the criteria (any hold but a breaker's), is `shape`; a task on the
fast track is `fast` from its request to its merge; `queued`, `building`, `planned`,
`blocked` (but by the merge agent's seat) and a breaker's `held` are `build`, but a
`queued` task that no lead started (no block of its state has a `lead:` line), which
goes on at step 8 of "The request", is `shape`; `ready`, `landing`, `open`, a `blocked`
task whose block names `the seat that failed: merger` (its pull request waits for the
owner's go on) and a `landed` task whose worktree is not removed yet are `land`. `open`
refuses a task that does not exist, one that ended (a landed one only once its worktree
is gone), a parked one, one queued `after:` a task that has not ended, a call with no
agterm, a workspace it cannot tell, and a path the launch line cannot carry.

`open` holds the task's lock (`session.lock` in its directory), so a click and a duty of
the board's server never open two. When agterm's tree has the newest `session.open`'s
session and an agent runs in it (`agent_runs`), `open` prints that one with
`already: true`. A session of the task that is still in the tree with no agent in it
(the shell the owner left after its agent ended) stays as it is: `open` opens the new
one beside it and closes nothing. Otherwise it writes `session.md` in the task
directory, the new agent's first read, and runs

    agtermctl session new --workspace WS --cwd DIR --name SLUG --no-select --command \\
      "SHELL -l -c 'LEM_TASK=SLUG CLAUDE_CODE_AUTO_COMPACT_WINDOW=N claude \\"Read TASK_DIR/session.md and follow it.\\"'"

then `session move --to bottom`: the new session goes after the last session of its
workspace, and the one the owner keeps first stays first. It never selects the session:
the owner's selection stays where it is, also when the task's session asks him a
question, and only his own act selects it. DIR is the main checkout in every phase, and
the agent works in the task's worktree by its path (`worktree:` of `session.md`): the
developer's Claude Code setup belongs to the main checkout's folder (a plugin installed
for the project, `.claude/settings.local.json`, the folder's trust), and a session
started in a worktree has none of it. In lem-scratch on 2026-11-21 a landing session
opened in its worktree found no `lem` command and no builder agent, and stopped as
`blocked`. N is `[handoff] tokens` of the machine (`lem project handoff`); with 0 the
variable is left out. `--model` and `--effort` follow only when `seats.session` names
them. `--plugin-dir ROOT` follows when this Lem is not the installed plugin, ROOT being
the folder of the plugin these scripts are in, so that the task's session runs the Lem
that opened it: a folder under Claude Code's plugin folders (`plugins/` of
`CLAUDE_CONFIG_DIR`, else of `~/.claude`) is the installed plugin and gets no flag; any
other is a clone loaded with `claude --plugin-dir`, or a branch before its release
(`plugin_dir`). `plugin-dir` prints that folder, or null, for the one launch line Lem
does not write itself: the plan talk's pair, which the lead opens under its session
(`harness/claude-code/plan-talk.md`). The workspace is the one the task's newest session
was in, else the caller's, else that of the task its `after:` line names, else the
repository's newest. It logs `session.open` with the session, its name, the phase, why
and the workspace.

`next` refuses while the state still gives the caller's phase (the leaving agent writes
its state block first), unless `--same`; it refuses a handoff.md that is not in the
form, not from the phase that ends, or older than the caller's session. The phase that
ends is the state's (`phase_left`): of the state blocks written after the task's newest
`session.open`, the newest before the ones that give the phase the task is in now, else
the phase that session opened in; so a session that led its task from the shape through
the build hands off from the build. With `--same` it is the phase the task is in. It
prints the line that closes the old session once the owner has left it, for
the background.

`open` puts the repository's main checkout into the machine's list of workspaces
(`lem project task-dir` does too), so that the board server shows it and runs its duties
from its first task. With `--why new`, a session it opens prints `then` too,
`lem session wait SLUG --first-line`: the line the session where the owner typed the
request runs in the background, to say the task's first line there (`stages/new.md`,
"Open the task", step 5).

`wait --first-line` ends when the task's log holds a `task.state` event with a `say`,
and prints `{"task": SLUG, "say": LINE, "gone": false}`, LINE being the event's
`say_named`: the line as a session other than the task's says it, with the task named
and in its commands. It ends with `"say": null` and `why`, one sentence, when a state
block comes that will never be followed by a line (a block with a type and no line, a
night's task among them, or a task parked or ended before it), when the task's session
is gone, and after FIRST_LINE_BOUND.

`wait` also ends when the task's newest session is gone from agterm's tree, or no agent
runs in it (`live`): then it prints `"gone": true` with the session's id, the task's
state, and a `say` that names `lem session open SLUG --why dead`. Its other ends print
`"gone": false`. An agterm that does not answer one look is asked again at the next.

`close --when-unselected` ends with no close (`closed: false`, `woken: true`) when the
session is woken while it waits (a new `session.wake` of that session in the log): the
session has work again, as a queued task's session does at `lem: SLUG queue`, and the
close of its next change of phase or of its end is the one that closes it.

`close-job` is the last step of a scheduled night or retro, whose session no task owns.
Its session is the caller's (`AGTERM_SESSION_ID`) or the one `--session` names. It
refuses the id that a `session.open` of a task names, with the line that closes it under
its task, and a session whose `foreground` in agterm's tree is not an agent's command
with the job's line as its last word (`job_line`): the cronn job's script starts the
agent with the prompt as its last argument, so a session where the owner typed
`/lem retro` into an agent he started himself is refused and stays his. Then it waits
while the owner has the session selected, as `close --when-unselected` does, and closes
it with agterm's undo. It logs no event: every record of the event log names its task
(`project.append_event`), and a job's session has none.

`wake` sends `lem: SLUG WHY` to the left pane of the task's live session and logs
`session.wake` (with `--head`, the head the pull request had, so that a conflict is
woken once for each head); the agent reads the files, never the line. With no live
session it opens one, as `open --why WHY`. The board's server sends `owner` after the
owner's act on the task from the board (his yes to the criteria, a park): a task that
gets no session then (a parked one) has nothing to wake, and that is no refusal. It
sends `inbox` when a thing of the task went to the owner's Inbox, or when his reply came
in a thread whose session no longer runs the task (`lem_inbox`): the live session reads
the thread itself, and with none live the wake opens nothing, since the reply waits in
the Inbox.

`list`'s `phase` is the phase the task's state gives now, null for a task that gets no
session (parked, or ended with its worktree gone), and `opened_in` the phase its newest
session opened in. Its `unanswered` is a wake older than UNANSWERED_AFTER whose line
still waits in the session's mailbox (`agtermctl msg read`, which removes nothing),
never the guard's status message, whose wait the guard itself ends.

Each entry whose session is live (`live`) says what Claude Code's own files say of its
work (`lem_signs`): `sign`, the time of the newest turn of the session's main thread or
of any of its subagents, or null; `shell`, true while a shell command of the session
runs; `signs`, false when neither could be read (no `session.transcript` record of that
agterm session, or no live process of it); and `turn`, `"runs"` while the newest turn of
the session's main thread runs, `"ended"` when it ended, or null when no record of it
tells or `signs` is false. A record of that session whose transcript's first prompt is
another task's launch line counts for none. A session that is not live has `sign` and
`turn` null and both others false.

The guard of a stopped session is the board server's (`serve.py`, `duties`; the rule is
`lem_board_model.stop_due`): 45 minutes with no sign of work in a task in `building`,
`ready` or `landing` give `wake --why status`, which sends `lem: SLUG status`; 10
minutes more give `open --why stopped`, a fresh session beside the old one, which it
renames `SLUG · replaced` and sends `lem: SLUG replaced` (logged as that session's
`session.wake`); once that restart is spent, `stopped` logs `session.stopped`. For a
session whose signs do not read, the clock is the task's events and its newest open
alone: 45 minutes with no event of the task give the status message, logged with
`unread: true`, and 10 minutes more with none give `stopped` at once, logged with
`unread: true`, since Lem opens no second session by itself beside a session it cannot
read. Each of the three looks once more in the task's lock before it acts
(`guard_check`): the task is still in one of those statuses, its newest session is the
one `--session` names and still lives with an agent in its pane, no shell command of it
runs, and the rule still gives that step, so that no sign of work came since the step
was due. Else it acts on nothing, exits 0 and prints `acted: false` with `why`
(`working`, `status`, `gone` or `unread`, a restart beside signs that do not read), and
the server's next look asks again. While a stop stands, no restart is due;
`open --why stopped` with no `--session` acts then, and when the signs read, only while
no sign of work came after the stop: the owner's "Open a session" on a stopped task. A
stop stands while no event of the task's work came after the status message before it,
so a state block logged in the moment of the stop leaves nothing waiting, and `stopped`
says so. The status message never opens a session: a gone pane is the board's "No
session runs this task".

`talk` copies the turns of this Claude Code session word for word: from the newest owner
turn whose text starts with TEXT to the newest turn, each with who said it and only its
text, less each owner turn that a `--leave` text starts (another topic) with the turns
of the agent that answer it. It copies only what the owner typed (a `/lem` line as he
typed it) and what the agent wrote; the skill's text that `/lem` loads, a task's
notification and agterm's mail are no turn of his.
"""

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not
    # a traceback
    sys.exit(
        "session.py: Lem needs Python 3.11 or newer, and this python3 is "
        f"{sys.version.split()[0]}; put a newer one first on PATH"
    )

import argparse
import contextlib
import fcntl
import importlib
import json
import os
import pwd
import re
import shlex
import shutil
import subprocess
import time
from collections.abc import Generator, Mapping
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    import lem_board_model

SCRIPTS = Path(__file__).resolve().parent
SKILL = SCRIPTS.parent
# the folder of the plugin these scripts are in: skills/lem/scripts is three levels
# under it
PLUGIN = SKILL.parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
project = importlib.import_module("project")
lem_state = importlib.import_module("lem_state")
lem_signs = importlib.import_module("lem_signs")
# the release a task began on, and the rule that stops a command for a task two
# releases back
lem_release = importlib.import_module("lem_release")

PHASES = ("shape", "build", "land", "fast")
WHYS = (
    "new",
    "handoff",
    "dead",
    "merged",
    "conflict",
    "refused",
    "queue",
    "night",
    "owner",
    "stopped",
)
# the whys of a `session.wake` record; `replaced` is sent only by `open --why stopped`,
# to the old pane
WAKES = (
    "merged",
    "conflict",
    "refused",
    "queue",
    "owner",
    "inbox",
    "status",
    "replaced",
)
CLOSES = ("handoff", "ended", "owner")
EVENTS = ("session.open", "session.close", "session.wake", "session.stopped")
# Why a step of the guard of a stopped session acted on nothing (`guard_refusal`), each
# with its words.
REFUSALS = {
    "working": (
        "its session showed a sign of work since the step was due, or a shell command "
        "of it runs, or the step was taken already"
    ),
    "status": "the task is no longer in building, ready or landing",
    "gone": (
        "the session the step was for is not the task's newest any more, or it no "
        "longer lives in agterm"
    ),
    "unread": (
        "its session's signs of work do not read (no transcript record of that "
        "session, or no live process of it), and Lem opens a fresh session beside such "
        'a session only on the owner\'s "Open a session" over its logged stop'
    ),
}
BRIEF = "session.md"
HANDOFF = "handoff.md"
LOCK = "session.lock"
TALK = "talk.md"
# The programs that count as the task's agent in the pane, by the name of their file.
AGENTS = ("claude", "codex")
# A shell's option that runs the next word as a command: `-c`, a cluster with it
# (`-lc`), or fish's `--command`.
SHELL_COMMAND = re.compile(r"-[a-zA-Z]*c[a-zA-Z]*|--command")
# The line a scheduled job starts its agent with, the last word of the agent's command:
# `/lem night`, `/lem night N` (`stages/night.md`) and `/lem retro` (`stages/init.md`,
# step 7).
JOB_LINE = re.compile(r"/lem (?:night(?: [1-9][0-9]*)?|retro)")
# A word of a command that sets a variable for it, `NAME=value`.
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*", re.DOTALL)
# A session opened this long ago counts as live while its agent starts: the login shell
# runs first, and a second `open` in that time must not open another. A guess.
STARTING = 60
# How often `close --when-unselected` looks whether the owner left the session. A guess
# (the plan).
CLOSE_EVERY = 5
# How often `wait` reads the task's state or the event log. A guess (the plan).
WAIT_EVERY = 10
# How long `wait --first-line` waits for the task's first line: 10 minutes, a guess
# (2026-11-21). In the real tasks of that day the first block came about a minute after
# the open; the fast track makes its worktree and runs `checks.setup` before it, and the
# interview may ask one question first.
FIRST_LINE_BOUND = 600
# How long `wait --quiet FILE` waits with no change of FILE (the plan talk's
# `talk-turns.md`) before it ends with `"quiet": true`, so that the lead reads the
# pair's screens for an agent that stopped at a limit and stays live in its pane: 45
# minutes, the guard's number for a session with no sign of work (the owner's,
# 2026-11-22), taken as a guess for a talk (plan seat-defaults-and-fallback,
# decision 10).
QUIET_SECONDS = 45 * 60
# After how long a wake whose line still waits in the mailbox is `unanswered`: 10
# minutes, a guess (the plan's "no session" row says "does not answer" after it).
UNANSWERED_AFTER = 600
# How long ps may take to list the machine's processes. A guess: it answers in well
# under a second.
PS_TIMEOUT = 10
# the characters that the launch line cannot carry inside its two levels of quotes to
# every login shell: fish reads `\` inside single quotes as an escape, where sh and zsh
# keep it
UNQUOTABLE = re.compile(r"[\\\n]")
# what sh, zsh or fish read inside double quotes, so that a word with one goes in
# single quotes
DOUBLE_QUOTED = re.compile(r"[\"$`\\]")
# how many words of a turn name it, in talk.md
FIRST_WORDS = 8
# The first line of handoff.md, and its five parts with what each holds
# (`templates/handoff.md`).
HANDOFF_LINE = re.compile(
    r"task:\s*(?P<task>[a-z0-9]+(?:-[a-z0-9]+)*)\s*·\s*from\s+(?P<phase>[a-z]+)\s*·\s*written:\s*(?P<written>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?Z)"
)
HANDOFF_PARTS = {
    "settled": "what is decided or done, each with its path, record or commit",
    "open": "what is not settled yet, or none",
    "next step": "the one step the next agent takes first",
    "failed": "what was tried and did not work, and why, or none",
    "changed files": "each changed file, `PATH`: STATUS on a line of its own, or none",
}
CHANGED = re.compile(
    r"[-*]\s+(?:`(?P<quoted>[^`]+)`|(?P<bare>[^\s:`]+)):\s*(?P<status>\S.*)"
)
NONE = re.compile(r"(?:[-*]\s+)?none\.?", re.IGNORECASE)


class SessionError(Exception):
    pass


# ---- the rules, over facts ----


def lead_started(state: str) -> bool:
    """Whether a lead ever ran for the task: a block of its whole STATE (state.md, every
    block) has a `lead:` line (`project.LEAD_LINE`), as its first line's text or a line
    under it."""
    for line in state.splitlines():
        found = project.STATE_LINE.fullmatch(line.strip())
        if project.LEAD_LINE.match(found["text"] if found else line.strip()):
            return True
    return False


def phase_of(
    slug: str,
    status: str | None,
    line: str | None,
    track: str | None,
    *,
    worktree: bool,
    state: str,
    lines: list[str] | None = None,
) -> str:
    """The phase of a task's session from its newest state block (STATUS and its first
    LINE), its track, whether its worktree is still there and its whole STATE; a
    SessionError with the fix for a task that gets no session. A `queued` task that no
    lead started was queued in the shape, at step 7 of "The request" (`stages/new.md`),
    and goes on there, at step 8; one that its lead queued goes on at the start of the
    build. A `landed` or `dropped` task whose worktree is still there is in the land
    phase: its session cleans it up and pays what its ticket is still owed, also for a
    pull request closed on GitHub while no session ran, which the board's server wakes
    as it wakes a merged one (`serve.py`, `duties`). A `blocked` task whose block names
    `the seat that failed: merger` is in the land phase too, as an `open` one: its pull
    request waits for the owner's go on; a block of the reviewer's or the planner's seat
    stays in the build. LINES are the block's lines under its first, the newest block of
    STATE when none are given."""
    if status is None:
        return "shape"
    if status == project.PARKED:
        raise SessionError(
            f"the task {slug!r} is parked: it gets no session until the owner's "
            f"`/lem resume {slug}` (`lem project resume {slug}`) brings it back"
        )
    if status in project.ENDED:
        if status in ("landed", "dropped") and worktree:
            return "fast" if track == "fast" else "land"
        if status == "landed":
            raise SessionError(
                f"the task {slug!r} is landed and cleaned: its worktree is gone, and "
                "an ended task gets no session; new work for it is a new ask"
            )
        raise SessionError(
            f"the task {slug!r} is {status}: an ended task gets no session, and new "
            "work for it is a new ask with a slug of its own"
        )
    if status == "held":
        # a breaker holds a build; every other hold waits for the owner, which the shape
        # session holds
        return (
            "build"
            if line and project.BREAKER_WAIT.fullmatch(line.strip())
            else "shape"
        )
    if track == "fast":
        return "fast"
    if status == "queued" and not lead_started(state):
        return "shape"
    if status == "blocked":
        if lines is None:
            newest = project.blocks_of(state)
            lines = newest[0]["lines"][1:] if newest else []
        return (
            "land" if project.failed_seat([line or "", *lines]) == "merger" else "build"
        )
    if status in ("queued", "building", "planned"):
        return "build"
    return "land"


def phase_left(
    slug: str,
    blocks: list[dict],
    track: str | None,
    now: str,
    start: str | None,
    state: str,
) -> str | None:
    """The phase a change of phase leaves: the phase of the newest state block before
    the run of blocks that gives NOW, the phase the task is in. BLOCKS are the
    `task.state` records the caller's session wrote, the ones after its `session.open`,
    oldest first, each with `status` and `text`; START is the phase that session opened
    in, which ends when none of its blocks gives another; STATE is the task's whole
    state, which tells a `queued` block of the shape from one its lead wrote
    (`phase_of`). A block that gives no phase (a park, an ended task's) is
    passed over."""
    for block in reversed(blocks):
        try:
            phase = phase_of(
                slug,
                block.get("status"),
                block.get("text"),
                track,
                worktree=True,
                state=state,
                lines=block.get("lines") or [],
            )
        except SessionError:
            continue
        if phase != now:
            return phase
    return start


def queued_behind(task: dict, tasks: list[dict]) -> str | None:
    """The task a `queued` task waits for (its `after:` line) while that one has not
    landed or been answered, else None. A dropped one holds it too, as `may-start` and
    the board's `after_ended` hold it: the result it waited for never came, and only the
    owner's word starts it or drops it."""
    if task["status"] != "queued" or not task["state"]:
        return None
    after = after_of(task)
    if not after:
        return None
    other = next((item["status"] for item in tasks if item["slug"] == after), None)
    return None if other in ("landed", "answered") else after


def behind_refusal(slug: str, behind: str, other: str | None) -> str:
    """The refusal of `open` for a task queued after BEHIND, whose status is OTHER."""
    if other == "dropped":
        return (
            f"the task {slug!r} is queued after {behind!r}, which was dropped: "
            "it waits for the owner's word, which starts it or drops it, and it gets "
            f'no session before that word. On his "start {slug} now", run the '
            f"commands `lem project may-start {slug}` prints, which remove the order, "
            f"and open its session again; on his `/lem drop {slug}`, drop it"
        )
    return (
        f"the task {slug!r} is queued after {behind!r}, which has not ended: "
        f"it gets its session when {behind} is landed or answered, and when {behind} "
        "is dropped it waits for the owner's word, which starts it or drops it"
    )


def after_of(task: dict) -> str | None:
    """The task that the `after:` line of the task's newest block names, read from each
    of its lines, its first too, as `may-start` and the board read it
    (`project.after_in`); None with no such line."""
    blocks = project.blocks_of(task["state"]) if task.get("state") else []
    return (
        project.after_in([line.strip() for line in blocks[0]["lines"]])
        if blocks
        else None
    )


def first_line(task: dict) -> str | None:
    found = (
        project.STATE_LINE.fullmatch(task["state"].splitlines()[0])
        if task.get("state")
        else None
    )
    return found["text"] if found else None


def first_line_end(slug: str, records: list[dict], *, night: bool) -> dict | None:
    """The end of `wait --first-line` from the task's `task.state` events, oldest first:
    its first line as another session says it, or None with the reason when a block came
    that no line will follow (a block with a type and no line, a task parked or ended
    first, or the hold of an order that named no task, whose line comes in the task's
    own session with the owner's answer); None while it waits."""
    for record in records:
        if record.get("say"):
            return {"task": slug, "say": record["say_named"], "gone": False}
        status = record.get("status")
        if status in project.ENDED or status == "parked":
            return {
                "task": slug,
                "say": None,
                "gone": False,
                "why": (
                    f"{slug} is {status} before its first line, "
                    "so there is no line to say"
                ),
            }
        if status == "held" and str(record.get("text", "")).strip().startswith(
            project.ORDER_WAIT
        ):
            return {
                "task": slug,
                "say": None,
                "gone": False,
                "why": (
                    f"{slug} is held: the order waits for the owner, since his words "
                    "name no open task Lem can tell. Its first line comes with his "
                    "answer, in its own session, and the list of what waits for "
                    "him shows it until then"
                ),
            }
        if project.type_of(
            "\n".join([str(record.get("text", "")), *map(str, record.get("lines", []))])
        ):
            why = (
                (
                    f"{slug} is a task of the night: it gets no first line, and the "
                    "night's report names it"
                )
                if night
                else (
                    f"the first state block of {slug} that names its type has no line, "
                    "so there is none to say; the board shows its state"
                )
            )
            return {"task": slug, "say": None, "gone": False, "why": why}
    return None


def command_agent(text: str) -> bool:
    """Whether a shell's `-c` string runs an agent: its first command word, after the
    `NAME=value` words that set its environment (the form `launch_line` builds), is an
    agent's file. A string that does not read as a shell's words counts when one plain
    word of it is an agent's file."""
    try:
        words = shlex.split(text)
    except ValueError:
        return any(Path(word).name in AGENTS for word in text.split())
    first = next((word for word in words if not ASSIGNMENT.fullmatch(word)), None)
    return first is not None and Path(first).name in AGENTS


def agent_runs(node: dict) -> bool | None:
    """Whether the program in the session's left pane is an agent (AGENTS), from
    agterm's tree. Its `foreground` is the argv of the pane's foreground process: an
    agent the owner started by hand (a word whose file is an agent's, `/…/bin/claude …`
    or `node /…/claude`), or the shell of the launch line, whose `-c` string runs the
    agent (`command_agent`). A shell with no command, or the null foreground of an idle
    shell, is no agent: a dead agent leaves one. None when agterm has not drawn the
    session yet and so does not know. The forms are the ones agterm's tree gave
    on 2026-11-21."""
    ground = node.get("foreground")
    if isinstance(ground, list) and ground:
        words = [str(word) for word in ground]
        for i, word in enumerate(words):
            if i and SHELL_COMMAND.fullmatch(words[i - 1]):
                if command_agent(word):
                    return True
            elif Path(word).name in AGENTS:
                return True
        return False
    return None if node.get("realized") is False else False


def job_line(node: dict) -> str | None:
    """The job's line of a session that a scheduled job started for one run, else None,
    from agterm's tree: its `foreground` is an agent's command (a word before the last
    whose file is an agent's, as `agent_runs` reads it) whose last word is the line
    (JOB_LINE). The cronn skill's job script ends in `exec ... "$JOB_AGENT" $JOB_ARGS
    "$JOB_PROMPT"` (`agent-session-job.sh`, read 2026-11-23), and agterm gives the argv
    of the pane's foreground process word by word (`agtermctl tree --json`, 2026-11-23),
    so the prompt is the last word. An agent the owner started with no prompt, where he
    typed `/lem retro`, has no such word; neither has a shell whose `-c` string holds
    the line."""
    ground = node.get("foreground")
    # an agent's command and the line after it
    if not isinstance(ground, list) or not ground[1:]:
        return None
    words = [str(word) for word in ground]
    line = " ".join(words[-1].split())
    if not JOB_LINE.fullmatch(line):
        return None
    return line if any(Path(word).name in AGENTS for word in words[:-1]) else None


def live(node: dict | None, opened: dict | None, now: datetime) -> bool:
    """Whether the session of a `session.open` record still carries its task: in the
    tree, and an agent runs in it, or agterm does not know yet, or it opened under
    STARTING seconds ago."""
    if node is None or opened is None:
        return False
    if agent_runs(node) is not False:
        return True
    return (now - stamp(opened["ts"])).total_seconds() < STARTING


def stamp(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def newest_opens(events: list[dict]) -> dict[str, dict]:
    """Each task's newest `session.open`."""
    found: dict[str, dict] = {}
    for record in events:
        if record.get("event") == "session.open":
            # project.append_event writes each record with its task's slug
            found[cast("str", record.get("task"))] = record
    return found


def handoff_form(text: str, slug: str) -> dict:
    """What handoff.md says of itself, after a check of its form
    (`templates/handoff.md`): its task, the phase it is from, its time and its changed
    files; a SessionError that names each part it lacks."""
    bare = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    lines = bare.splitlines()
    head = next((line.strip() for line in lines if line.strip()), "")
    found = HANDOFF_LINE.fullmatch(head)
    missing = []
    if not found:
        missing.append(
            f"a first line `task: {slug} · from PHASE · written: YYYY-MM-DDTHH:MMZ`, "
            f"with PHASE one of {', '.join(PHASES)}"
        )
    elif found["task"] != slug:
        missing.append(
            f"its first line names the task {found['task']!r}, and this is {slug!r}"
        )
    elif found["phase"] not in PHASES:
        missing.append(
            f"its first line says from {found['phase']!r}, "
            f"and a phase is one of {', '.join(PHASES)}"
        )
    parts: dict[str, list[str]] = {}
    current = None
    for line in lines:
        if line.startswith("## "):
            title = " ".join(line[3:].lower().split())
            current = title if title in HANDOFF_PARTS else None
            if current is not None:
                parts.setdefault(current, [])
        elif current is not None and line.strip():
            parts[current].append(line.strip())
    changed = []
    for part, holds in HANDOFF_PARTS.items():
        body = parts.get(part, [])
        if not body:
            missing.append(f"## {part[0].upper()}{part[1:]} ({holds})")
            continue
        if part == "changed files" and not (len(body) == 1 and NONE.fullmatch(body[0])):
            wrong = []
            for line in body:
                item = CHANGED.fullmatch(line)
                if item:
                    changed.append(
                        {
                            "path": item["quoted"] or item["bare"],
                            "status": item["status"].strip(),
                        }
                    )
                else:
                    wrong.append(line)
            if wrong:
                missing.append(
                    "a path and a status on each line of ## Changed files, as `PATH`: "
                    "STATUS, and these lines have none: "
                    f"{'; '.join(repr(line) for line in wrong)}"
                )
    # no first line in the form is one thing it lacks
    if missing or found is None:
        raise SessionError(
            (
                f"{HANDOFF} of {slug} is not in the form of `templates/handoff.md`: "
                "it lacks "
            )
            + "; ".join(missing)
        )
    return {
        "task": slug,
        "from": found["phase"],
        "written": found["written"],
        "changed": changed,
    }


def plugin_dir(root: Path, environ: Mapping[str, str]) -> str | None:
    """What `--plugin-dir` names on the launch line of a task's session and of the plan
    talk's pair (`lem session plugin-dir`): None when ROOT, this Lem's plugin folder, is
    under Claude Code's plugin folders (`plugins/` of CLAUDE_CONFIG_DIR, else of
    `~/.claude`), where the new session loads it as the installed plugin; else ROOT, so
    that the session runs this Lem and not the one that is installed."""
    home = Path(environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    plugins = (home / "plugins").resolve()
    found = root.resolve()
    return None if found == plugins or plugins in found.parents else str(found)


def launch_line(
    shell: str,
    slug: str,
    brief: Path,
    tokens: int | None,
    seat: dict,
    plugin: str | None = None,
) -> str:
    """The command of the task's session: the owner's login shell, so that his PATH
    finds claude, with the task and the compaction number in the environment, since
    `agtermctl session new` takes none, and with PLUGIN as `--plugin-dir` when this Lem
    is not the installed plugin (`plugin_dir`).

    Two levels read it: agterm's, which splits the line into words with their quotes,
    and the login shell's `-c`. Each word of the inner command is quoted for the login
    shell, and the whole inner command once more for agterm's level, so a model such as
    `opus[1m]` or a path with a space or an apostrophe reaches claude whole in bash, zsh
    and fish alike."""
    for what, value, fix in (
        ("the brief's path", str(brief), "move the checkout to a path without them"),
        (
            "the plugin's folder",
            plugin or "",
            "move Lem's folder to a path without them",
        ),
        ("the owner's login shell", shell, "set a login shell at a plain path"),
        ("the session's model", seat.get("model") or "", "write seats.session again"),
        ("the session's effort", seat.get("effort") or "", "write seats.session again"),
    ):
        if UNQUOTABLE.search(value):
            raise SessionError(
                f"{what} {value!r} holds a backslash or a line break, which the launch "
                "line cannot carry to every login shell (fish reads a backslash inside "
                f"quotes as an escape): {fix}"
            )
    words = (
        [f"LEM_TASK={slug}"]
        + ([f"CLAUDE_CODE_AUTO_COMPACT_WINDOW={tokens}"] if tokens is not None else [])
        + ["claude"]
    )
    words += [
        word
        for flag in ("model", "effort")
        if seat.get(flag)
        for word in (f"--{flag}", seat[flag])
    ]
    words += ["--plugin-dir", plugin] if plugin else []
    words.append(f"Read {brief} and follow it.")
    inner = " ".join(shell_word(word) for word in words)
    return f"{shlex.quote(shell)} -l -c {shlex.quote(inner)}"


def shell_word(word: str) -> str:
    """WORD as one word of sh, zsh and fish alike: bare when it needs no quote, in
    double quotes when it holds nothing those read inside them (`"`, `$`, a backquote, a
    backslash), else in single quotes, which keeps the usual launch line readable in
    agterm's tree."""
    if shlex.quote(word) == word:
        return word
    return f'"{word}"' if not DOUBLE_QUOTED.search(word) else shlex.quote(word)


def brief_text(
    slug: str, phase: str, why: str, directory: Path, main: Path, worktree: Path | None
) -> str:
    """The text of `session.md`. Its first line names `prompts/session.md` by its place
    in the plugin, found through `lem version`, and never by the folder of this Lem: the
    plugin's folder changes with each update, and a session started after one reads the
    texts of the Lem whose `lem` is on its PATH, the one whose scripts it runs."""
    return "\n".join(
        [
            "Read `skills/lem/prompts/session.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check.",  # noqa: E501 - tests/unit/test_session.py reads this line whole (BRIEF_LINE)
            "",
            f"task: {slug}",
            f"phase: {phase}",
            f"opened because: {why}",
            f"task directory: {directory}",
            f"main checkout: {main}",
            f"worktree: {worktree or 'none yet'}",
            "",
        ]
    )


# ---- agterm ----


def place() -> dict:
    """Where this command runs in agterm, from the variables agterm gives a session's
    commands; none for a process outside agterm (the board's server), whose `agtermctl`
    finds the app by itself."""

    def env(*names: str) -> str:
        return next((os.environ[name] for name in names if os.environ.get(name)), "")

    if not shutil.which("agtermctl"):
        raise SessionError(
            "agtermctl is not on the PATH: a task's session is a session of agterm, "
            "which Lem needs; install agterm's command line tool (Help > "
            "Install Command Line Tool)"
        )
    return {
        "session": env("AGTERM_SESSION_ID", "AGT_SESSION_ID"),
        "socket": env("AGTERM_SOCKET", "AGT_SOCKET"),
        "window": env("AGTERM_WINDOW_ID", "AGT_WINDOW_ID"),
    }


def ctl(where: dict, *args: str, window: bool = True) -> str:
    extra = ["--socket", where["socket"]] if where["socket"] else []
    if window and where["window"]:
        extra += ["--window", where["window"]]
    ran = subprocess.run(
        ["agtermctl", *args, *extra], capture_output=True, text=True, check=False
    )
    if ran.returncode != 0:
        raise SessionError(
            f"agtermctl {' '.join(args[:2])} failed: "
            f"{(ran.stderr or ran.stdout).strip() or f'exit {ran.returncode}'}"
        )
    return ran.stdout


def tree(where: dict) -> list[dict]:
    """Every session of agterm's tree, each with the id of its `workspace`."""
    try:
        found = json.loads(ctl(where, "tree", "--json"))["result"]["tree"]
    except (ValueError, KeyError, TypeError) as error:
        raise SessionError(f"agtermctl tree answered no tree ({error})") from error
    return [
        {**node, "workspace": str(workspace.get("id", ""))}
        for workspace in found.get("workspaces", [])
        for node in workspace.get("sessions", [])
    ]


def node_of(nodes: list[dict], session: object) -> dict | None:
    return next(
        (
            node
            for node in nodes
            if session and str(node.get("id", "")).upper() == str(session).upper()
        ),
        None,
    )


def left_pane(node: dict) -> str:
    """The id of the session's left pane, which a message reaches, else `left`."""
    return next(
        (
            str(surface["paneID"])
            for surface in node.get("surfaces", [])
            if isinstance(surface, dict)
            and surface.get("kind") == "left"
            and surface.get("paneID")
        ),
        "left",
    )


def login_shell() -> str:
    shell = pwd.getpwuid(os.getuid()).pw_shell
    if not shell or not Path(shell).is_absolute():
        raise SessionError(
            "the owner's login shell is not known to the system (no absolute path in "
            "the user database): agterm needs it to find claude"
        )
    return shell


# ---- the facts ----


def worktree_of(root: Path, settings: dict, slug: str) -> Path | None:
    path = (
        project.main_checkout(root)
        / Path(settings["places"]["worktrees"]["path"]).relative_to(root.resolve())
        / slug
    )
    return path if (path / ".git").exists() else None


@contextlib.contextmanager
def task_lock(directory: Path) -> Generator[None, None, None]:
    with (directory / LOCK).open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def facts_of(root: Path, slug: str) -> dict:
    directory = project.task_directory(root, slug)
    settings = project.load(root)
    tasks = project.read_tasks(root, settings)
    task = next(task for task in tasks if task["slug"] == slug)
    worktree = worktree_of(root, settings, slug)
    # the whole state, every block: whether a lead ever ran for a queued task is in an
    # older one
    written = (
        project.text_of(directory / "state.md")
        if (directory / "state.md").is_file()
        else ""
    )
    phase = phase_of(
        slug,
        task["status"],
        first_line(task),
        task["track"],
        worktree=worktree is not None,
        state=written,
    )
    return {
        "directory": directory,
        "settings": settings,
        "tasks": tasks,
        "task": task,
        "worktree": worktree,
        "phase": phase,
        "state": written,
    }


def workspace_for(
    slug: str, task: dict, opens: dict[str, dict], nodes: list[dict], caller: str
) -> str:
    """The workspace a new session of the task opens in: the one its newest session was
    in, else the caller's, else that of the task its `after:` line names, else the
    repository's newest."""
    known = {node["workspace"] for node in nodes}
    mine = node_of(nodes, caller)
    after = after_of(task)
    newest = max(opens.values(), key=lambda record: record["ts"], default=None)
    for found in (
        (opens.get(slug) or {}).get("workspace"),
        mine["workspace"] if mine else None,
        (opens.get(after) or {}).get("workspace") if after else None,
        (newest or {}).get("workspace"),
    ):
        if found and found in known:
            return found
    raise SessionError(
        f"no workspace of agterm is known for {slug}: no session of it or of this "
        "repository is on record, and this runs in no session of agterm. "
        f"Run `lem session open {slug}` from a session in the workspace it belongs in, "
        f"or type `/lem status {slug}` there"
    )


# ---- the guard of a stopped session ----


def guard_refusal(
    t: "lem_board_model.Task | None",
    m: "lem_board_model.Model",
    step: str,
    named: object,
) -> str | None:
    """Why the act of STEP (`status`, `restart` or `stopped`) of the guard of a stopped
    session acts on nothing, a key of REFUSALS, or None when it acts. T is the task in
    M, the board's model of the event log as it is now (None for a task with no state),
    whose `sessions` holds the one entry of T's newest session as read now in the task's
    lock; NAMED is the session the board server named, or None.

    It acts when the guard still watches the task (`guarded`), its newest session is the
    one named and still lives with an agent in its pane, no shell command of it runs,
    and the rule (`lem_board_model.stop_due`) still gives STEP over the new facts, so
    that no sign of work came since the time the step was due from; signs that do not
    read are facts of that rule, which gives them `status` and `stopped`. A `restart`
    that names no session acts while the task's stop stands (`stop_stands`) and, when
    the signs read, no sign of work came after it: the owner's "Open a session" on a
    stopped task. A `restart` that names one (the server's duty) never acts over a
    standing stop, and never when the signs do not read: Lem opens no second session by
    itself beside a session it cannot read."""
    bm = board_model()
    f = (m.sessions or {}).get(t.slug) if t is not None else None
    if t is None or not bm.guarded(t):
        return "status"
    if (
        not f
        or not (f.get("live") is True and f.get("agent") is True)
        or (named and str(named).upper() != str(f.get("session") or "").upper())
    ):
        return "gone"
    if f.get("shell") is not False:
        return "working"
    read = f.get("signs") is True
    if step == "restart":
        stood = bm.stop_stands(t)
        if stood is not None and not named:
            return (
                None
                if not read
                or (bm.at(f.get("sign")) or 0) <= (bm.at(stood.get("ts")) or 0)
                else "working"
            )
        if not read:
            return "unread"
    due = bm.stop_due(t, m)
    return None if due is not None and due["step"] == step else "working"


def board_model() -> ModuleType:
    return importlib.import_module("lem_board_model")


def model_now(root: Path) -> tuple["lem_board_model.Model", list[dict]]:
    """The board's model of the event log as it is now, and the log's records."""
    bm = board_model()
    state = project.state_root(root)
    reader = bm.Reader(project.main_checkout(root), state)
    reader.read_log()
    if "events" in reader.problems:
        raise SessionError(
            f"{state / 'events.jsonl'}: {reader.problems['events']}; "
            "the log is written by project.py, never by hand"
        )
    return bm.derive(reader.events, [], bm.now_ms()), reader.events


def guard_check(
    root: Path, slug: str, step: str, named: str | None, where: dict
) -> tuple[dict | None, str | None, bool]:
    """The look once more of the guard of a stopped session, run in the task's lock
    before its act: the board's model of the event log now, the task's newest session in
    agterm's tree (`agent` is true only for an agent agterm sees in its pane, as `list`
    gives it), and its signs of work read now. Its refusal, `acted: false` with its
    reason for the caller to print, or None; the session the act is for; and whether its
    signs read, for the record of the act."""
    bm = board_model()
    m, events = model_now(root)
    t = m.by_slug.get(slug)
    t = t if t is not None and t.blocks else None
    newest = newest_opens(events).get(slug)
    session = str(newest["session"]) if newest and newest.get("session") else None
    alive = agent = False
    signs = {"sign": None, "shell": False, "signs": False, "turn": None}
    if session is not None and t is not None and bm.guarded(t):
        node = node_of(tree(where), session)
        alive = live(node, newest, datetime.now(UTC))
        agent = node is not None and agent_runs(node) is True
        records = [
            record
            for record in events
            if record.get("event") == lem_signs.EVENT and record.get("task") == slug
        ]
        if alive and lem_signs.own_records(records, session):
            signs = lem_signs.signs_of(records, session, process_table(), slug)
    bm.put_sessions(
        m,
        {
            slug: {
                "live": alive,
                "agent": agent,
                "unanswered": False,
                "session": session,
                **signs,
            }
        },
    )
    reason = guard_refusal(t, m, step, named)
    read = signs.get("signs") is True
    if reason is None:
        return None, session, read
    return (
        {
            "task": slug,
            "session": session,
            "acted": False,
            "why": reason,
            "say": (
                f"Lem did nothing for {slug}: {REFUSALS[reason]}; "
                "the board server's next look asks again"
            ),
        },
        session,
        read,
    )


def tell_replaced(root: Path, where: dict, slug: str, old: str) -> dict:
    """After a restart, the old session's new name, `SLUG · replaced`, and the line
    `lem: SLUG replaced` to its left pane, logged as its `session.wake`, so that the
    owner sees which pane is old and the old agent closes itself at the end of its turn.
    What failed is said, never raised: the fresh session is open and on record
    by then."""
    try:
        ctl(where, "session", "rename", f"{slug} · replaced", "--target", old)
        ctl(
            where,
            "msg",
            "send",
            f"lem: {slug} replaced",
            "--to",
            f"{old}:left",
            window=False,
        )
    except SessionError as error:
        return {"old": old, "told": False, "problem": str(error)}
    project.append_event(
        root, "session.wake", slug, {"session": old, "why": "replaced"}
    )
    return {"old": old, "told": True}


def cmd_stopped(root: Path, slug: str, named: str | None) -> dict:
    where = place()
    directory = project.task_directory(root, slug)
    with task_lock(directory):
        refused, session, read = guard_check(root, slug, "stopped", named, where)
        if refused is not None:
            return refused
        project.append_event(
            root,
            "session.stopped",
            slug,
            {"session": session, **({} if read else {"unread": True})},
        )
        # a state block is appended under the log's lock, not the task's, so it may come
        # between the look and the stop
        t = model_now(root)[0].by_slug.get(slug)
        stands = t is not None and board_model().stop_stands(t) is not None
    if not stands:
        return {
            "task": slug,
            "session": session,
            "acted": True,
            "say": (
                f"the stop of {slug} is logged, but work of the task came before it, "
                "so the stop does not stand and nothing waits for the owner"
            ),
        }
    why = (
        (
            "Lem cannot read its session's signs of work, and no event of the task "
            f"came in the {board_model().ANSWER_MS // 60000} minutes "
            "after the status message"
        )
        if not read
        else (
            "its session showed no sign of work after the status "
            "message and after its restart"
        )
    )
    return {
        "task": slug,
        "session": session,
        "acted": True,
        "say": (
            f"the stop of {slug} is logged: {why}, so it waits for the owner, whose "
            f"`lem session open {slug} --why stopped` opens a fresh session"
        ),
    }


# ---- the commands ----


def cmd_open(
    root: Path,
    slug: str,
    why: str,
    replacing: str | None = None,
    named: str | None = None,
) -> dict:
    where = place()
    directory = project.task_directory(root, slug)
    # the board server shows the repository and runs its duties from its first
    # session on
    project.register_checkout(root)
    with task_lock(directory):
        if why == "stopped":
            # the restart of the guard, or the owner's open of a stopped task: beside
            # the live session it replaces
            refused, replacing, _ = guard_check(root, slug, "restart", named, where)
            if refused is not None:
                return refused
        facts = facts_of(root, slug)
        task, phase = facts["task"], facts["phase"]
        behind = queued_behind(task, facts["tasks"])
        if behind:
            raise SessionError(
                behind_refusal(
                    slug,
                    behind,
                    next(
                        (
                            item["status"]
                            for item in facts["tasks"]
                            if item["slug"] == behind
                        ),
                        None,
                    ),
                )
            )
        nodes = tree(where)
        opens = newest_opens(project.events_named(root, *EVENTS))
        newest = opens.get(slug)
        node = node_of(nodes, newest.get("session") if newest else None)
        if (
            newest
            and node is not None
            and live(node, newest, datetime.now(UTC))
            and str(newest["session"]).upper() != (replacing or "").upper()
        ):
            return {
                "task": slug,
                "session": newest["session"],
                "name": node.get("name") or newest.get("name"),
                "phase": phase,
                "already": True,
                "say": (
                    f"{slug} already runs in the session "
                    f"`{node.get('name') or newest.get('name')}`"
                ),
            }
        workspace = workspace_for(slug, task, opens, nodes, where["session"])
        try:
            tokens = lem_state.handoff_tokens()
        except lem_state.StateError as error:
            raise SessionError(str(error)) from error
        worktree = facts["worktree"]
        brief = directory / BRIEF
        line = launch_line(
            login_shell(),
            slug,
            brief,
            tokens,
            facts["settings"]["seats"]["session"],
            plugin_dir(PLUGIN, os.environ),
        )
        main = project.main_checkout(root)
        brief.write_text(
            brief_text(slug, phase, why, directory, main, worktree), encoding="utf-8"
        )
        made = ctl(
            where,
            "session",
            "new",
            "--workspace",
            workspace,
            "--cwd",
            str(main),
            "--name",
            slug,
            "--no-select",
            "--command",
            line,
            "--json",
        )
        try:
            session = str(json.loads(made)["result"]["id"])
        except (ValueError, KeyError, TypeError) as error:
            raise SessionError(
                "agtermctl session new answered no session "
                f"id ({error}): {made.strip()[:200]}"
            ) from error
        # the record first: the session exists now, whatever the next step does
        project.append_event(
            root,
            "session.open",
            slug,
            {
                "session": session,
                "name": slug,
                "phase": phase,
                "why": why,
                "workspace": workspace,
            },
        )
        ctl(where, "session", "move", "--to", "bottom", "--target", session)
    if why == "stopped":
        return {
            "task": slug,
            "session": session,
            "name": slug,
            "phase": phase,
            "already": False,
            "acted": True,
            **tell_replaced(root, where, slug, str(replacing)),
            "say": (
                f"{slug} goes on in a fresh session `{slug}`, phase {phase}, beside "
                f"the old one, which is named `{slug} · replaced`"
            ),
        }
    return {
        "task": slug,
        "session": session,
        "name": slug,
        "phase": phase,
        "already": False,
        "say": (
            f"{slug} is open in its own session `{slug}`, phase {phase}, "
            "at the end of the workspace"
        ),
        # the caller runs it in the background, and says the task's first line when
        # it ends
        **({"then": f"lem session wait {slug} --first-line"} if why == "new" else {}),
    }


def cmd_next(root: Path, slug: str, *, same: bool) -> dict:
    where = place()
    directory = project.task_directory(root, slug)
    opens = newest_opens(project.events_named(root, *EVENTS))
    newest = opens.get(slug)
    if newest is None:
        raise SessionError(
            f"no session of {slug} is on record, so there is no phase to hand off: "
            f"`lem session open {slug}` opens its first"
        )
    old = str(where["session"] or newest["session"])
    facts = facts_of(root, slug)
    phase = facts["phase"]
    # the phase that ends is the state's, never only the phase this session opened in: a
    # session that led its task on from the shape into the build hands off from the
    # build. Its blocks are the ones the log holds after the task's newest session.open.
    records = [
        record
        for record in project.events_named(root, "task.state", "session.open")
        if record.get("task") == slug
    ]
    last_open = max(
        (
            i
            for i, record in enumerate(records)
            if record.get("event") == "session.open"
        ),
        default=-1,
    )
    blocks = [
        record
        for record in records[last_open + 1 :]
        if record.get("event") == "task.state"
    ]
    was = (
        phase
        if same
        else phase_left(
            slug,
            blocks,
            facts["task"]["track"],
            phase,
            newest.get("phase"),
            facts["state"],
        )
    )
    if phase == was and not same:
        raise SessionError(
            f"the state of {slug} still gives the phase {was}: write the new state "
            f"block first (`lem project state {slug} ...`), then run this again; "
            'for the owner\'s "hand off" inside a phase, '
            f"`lem session next {slug} --same`"
        )
    file = directory / HANDOFF
    if not file.is_file():
        raise SessionError(
            f"{file} is not there: write the handoff in the form of "
            "`templates/handoff.md` first, after the state block"
        )
    form = handoff_form(file.read_text(encoding="utf-8"), slug)
    if form["from"] != was:
        raise SessionError(
            f"{HANDOFF} of {slug} says it is from {form['from']}, and the phase that "
            f"ends, by the task's state, is {was}: write it again "
            "for the phase that leaves"
        )
    if form["written"][:16] < newest["ts"][:16]:
        raise SessionError(
            f"{HANDOFF} of {slug} was written at {form['written']}, before this "
            f"session opened at {newest['ts']}: it is an older session's; "
            "write it again"
        )
    opened = cmd_open(root, slug, "handoff", replacing=old)
    if opened["already"]:
        raise SessionError(
            f"another session of {slug} runs already, `{opened['name']}` "
            f"({opened['session']}): it took over; this one closes with `lem session "
            f"close {slug} --session {old} --why handoff --when-unselected`"
        )
    ctl(where, "session", "rename", f"{slug} · handed off", "--target", old)
    close = f"lem session close {slug} --session {old} --why handoff --when-unselected"
    return {
        **opened,
        "old": old,
        "from": was,
        "close": close,
        "say": (
            f"{slug} goes on in a fresh session for the phase {opened['phase']}; "
            "this one closes once the owner has left it"
        ),
    }


def wakes_of(events: list[dict], session: str) -> int:
    """How many `session.wake` records the event log holds for SESSION: counted, not
    timed, since a record's time has whole seconds and a wake may come in the second the
    close started."""
    return sum(
        1
        for record in events
        if record.get("event") == "session.wake"
        and str(record.get("session", "")).upper() == session.upper()
    )


def own_session(events: list[dict], slug: str, session: str) -> None:
    """Refuse SESSION unless a `session.open` of SLUG names it. Any of the task's
    sessions counts, an older one too, since a handoff closes the one before it."""
    opened = [
        record
        for record in events
        if record.get("event") == "session.open"
        and str(record.get("session", "")).upper() == session.upper()
    ]
    if any(record.get("task") == slug for record in opened):
        return
    owners = sorted({str(record.get("task")) for record in opened})
    whose = (
        f"its `session.open` names {', '.join(owners)}"
        if owners
        else "no `session.open` names it"
    )
    raise SessionError(
        f"{session} is no session of {slug}: {whose}. `lem session list` gives each "
        "task's session; close a session under its own task, or leave out --session to "
        f"close {slug}'s newest"
    )


def cmd_close(
    root: Path,
    slug: str,
    session: str | None,
    why: str,
    *,
    when_unselected: bool,
    every: float,
) -> dict:
    where = place()
    project.task_directory(root, slug)
    events = project.events_named(root, *EVENTS)
    if session is None:
        newest = newest_opens(events).get(slug)
        if newest is None:
            raise SessionError(
                f"no session of {slug} is on record: there is nothing to close"
            )
        session = str(newest["session"])
    else:
        own_session(events, slug, session)
    logged = any(
        record.get("event") == "session.close"
        and str(record.get("session", "")).upper() == session.upper()
        for record in events
    )
    woken = wakes_of(events, session)
    while True:
        if (
            when_unselected
            and wakes_of(project.events_named(root, *EVENTS), session) > woken
        ):
            # woken after this close started (a queued task's turn, `lem: SLUG queue`):
            # the session has work again, and the close that its next change of phase or
            # its end runs is the one that counts
            return {
                "task": slug,
                "session": session,
                "why": why,
                "closed": False,
                "woken": True,
                "says": (
                    f"the session {session} was woken after this close started, so it "
                    "has work again and stays open; the close of its next change of "
                    "phase or of its end closes it"
                ),
            }
        node = node_of(tree(where), session)
        if node is None:
            if not logged:
                project.append_event(
                    root, "session.close", slug, {"session": session, "why": why}
                )
            return {
                "task": slug,
                "session": session,
                "why": why,
                "closed": False,
                "says": f"the session {session} is no longer in agterm's tree",
            }
        if not node.get("active"):
            break
        if not when_unselected:
            raise SessionError(
                f"the owner has the session `{node.get('name')}` selected, and Lem "
                f"never closes a session he looks at: `lem session close {slug} "
                f"--session {session} --why {why} --when-unselected` "
                "closes it once he left it"
            )
        time.sleep(every)
    # the log first: a session that closes itself ends with this command
    if not logged:
        project.append_event(
            root, "session.close", slug, {"session": session, "why": why}
        )
    ctl(where, "session", "close", "--target", session, "--undoable")
    return {"task": slug, "session": session, "why": why, "closed": True}


def cmd_close_job(root: Path, session: str | None, every: float) -> dict:
    where = place()
    session = session or where["session"]
    if not session:
        raise SessionError(
            "no session to close: run it in the job's own agterm session, which sets "
            "AGTERM_SESSION_ID, or name the session with --session ID"
        )
    opened = [
        record
        for record in project.events_named(root, "session.open")
        if str(record.get("session", "")).upper() == session.upper()
    ]
    if opened:
        slug = str(opened[-1].get("task"))
        raise SessionError(
            f"{session} is the session of the task {slug}, and a task's session closes "
            f"under its task: `lem session close {slug} --session {session} "
            "--why ended --when-unselected`"
        )
    node = node_of(tree(where), session)
    if node is None:
        return {
            "session": session,
            "closed": False,
            "says": f"the session {session} is no longer in agterm's tree",
        }
    line = job_line(node)
    if line is None:
        raise SessionError(
            f"the session `{node.get('name')}` is the owner's: no scheduled job "
            "started its agent for this run, since its command (agterm's foreground "
            f"{json.dumps(node.get('foreground'), ensure_ascii=False)}) does not end "
            "in `/lem night`, `/lem night N` or `/lem retro`; it stays open, and the "
            "owner closes it himself"
        )
    while node.get("active"):
        time.sleep(every)
        node = node_of(tree(where), session)
        if node is None:
            return {
                "session": session,
                "job": line,
                "closed": False,
                "says": f"the session {session} is no longer in agterm's tree",
            }
    ctl(where, "session", "close", "--target", session, "--undoable")
    return {"session": session, "job": line, "closed": True}


def cmd_handoff(root: Path, slug: str) -> dict:
    file = project.task_directory(root, slug) / HANDOFF
    if not file.is_file():
        raise SessionError(
            f"{file} is not there: write it in the form of `templates/handoff.md`"
        )
    return {**handoff_form(file.read_text(encoding="utf-8"), slug), "file": str(file)}


def cmd_wake(
    root: Path, slug: str, why: str, head: str | None, named: str | None = None
) -> dict:
    where = place()
    directory = project.task_directory(root, slug)
    if why == "status":
        # the guard's status message: to the live session it was due for, never a new
        # session in its place
        with task_lock(directory):
            refused, session, read = guard_check(root, slug, "status", named, where)
            if refused is not None:
                return refused
            ctl(
                where,
                "msg",
                "send",
                f"lem: {slug} status",
                "--to",
                f"{session}:left",
                window=False,
            )
            # a wake from the task's events alone says so, so that its words say which
            # clock sent it
            project.append_event(
                root,
                "session.wake",
                slug,
                {"session": session, "why": why, **({} if read else {"unread": True})},
            )
        return {
            "task": slug,
            "session": session,
            "why": why,
            "acted": True,
            "woke": True,
            "opened": False,
            "say": (
                f"the session of {slug} got `lem: {slug} status`, which asks where the "
                "task stands and to go on with its next step"
            ),
        }
    newest = newest_opens(project.events_named(root, *EVENTS)).get(slug)
    node = node_of(tree(where), newest.get("session") if newest else None)
    if newest and node is not None and live(node, newest, datetime.now(UTC)):
        session = str(newest["session"])
        ctl(
            where,
            "msg",
            "send",
            f"lem: {slug} {why}",
            "--to",
            f"{session}:left",
            window=False,
        )
        project.append_event(
            root,
            "session.wake",
            slug,
            {"session": session, "why": why, **({"head": head} if head else {})},
        )
        return {
            "task": slug,
            "session": session,
            "why": why,
            "woke": True,
            "opened": False,
            "say": (
                f"the session `{node.get('name')}` of {slug} got `lem: {slug} {why}`"
            ),
        }
    if why == "inbox":
        # the Inbox's word opens no session: the thing or the reply stays in the Inbox
        # for the session that comes
        return {
            "task": slug,
            "session": None,
            "why": why,
            "woke": False,
            "opened": False,
            "say": f"no session of {slug} runs: what came in the Inbox waits there",
        }
    if why == "owner":
        try:
            facts_of(root, slug)
        except SessionError as error:
            # his act ended the task's need of a session (a park): nothing waits for
            # the line
            return {
                "task": slug,
                "session": None,
                "why": why,
                "woke": False,
                "opened": False,
                "say": f"no session of {slug} runs, and it gets none: {error}",
            }
    opened = cmd_open(root, slug, why)
    if head:
        # the head is kept on the wake's record, so that a conflict is answered once for
        # each head
        project.append_event(
            root,
            "session.wake",
            slug,
            {"session": opened["session"], "why": why, "head": head},
        )
    return {**opened, "why": why, "woke": False, "opened": not opened["already"]}


def gone_session(root: Path, slug: str, where: dict) -> dict | None:
    """The task's newest session when it is gone: on record, and not live in agterm's
    tree (`live`); None while it lives, while none is on record, or when agterm did not
    answer, which the next look asks again."""
    newest = newest_opens(project.events_named(root, *EVENTS)).get(slug)
    if newest is None:
        return None
    try:
        node = node_of(tree(where), newest.get("session"))
    except SessionError:
        return None
    return None if live(node, newest, datetime.now(UTC)) else newest


def gone_companion(where: dict, companion: str, since: dict, now: datetime) -> bool:
    """Whether COMPANION, a session the waiting one opened under itself (the plan talk's
    pair), is gone: not in agterm's tree, or no agent runs in it once STARTING seconds
    passed since the wait began (SINCE, a record with its `ts`). False when agterm did
    not answer, which the next look asks again."""
    try:
        node = node_of(tree(where), companion)
    except SessionError:
        return False
    return not live(node, since, now)


def quiet_over(
    changed: float | None, began: float, now: float, after: float = QUIET_SECONDS
) -> bool:
    """Whether a wait with `--quiet FILE` ends as quiet at NOW: AFTER seconds passed
    since the later of FILE's last change (CHANGED, None while it is not there) and the
    wait's own start (BEGAN), so a wait that follows a quiet end with no error waits the
    whole time again over the same old file."""
    return now - max(began if changed is None else changed, began) >= after


def cmd_wait(
    root: Path,
    slug: str,
    until: list[str],
    event: str | None,
    every: float,
    companion: str | None = None,
    quiet: Path | None = None,
) -> dict:
    project.task_directory(root, slug)
    unknown = [state for state in until if state not in project.STATES]
    if unknown:
        raise SessionError(
            f"--until names {', '.join(unknown)}, and a state is "
            f"one of {', '.join(project.STATES)}"
        )
    where = place()
    began = {"ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}

    def mine() -> list[dict]:
        return [
            record
            for record in project.events_named(root, event)
            if record.get("task") == slug
        ]

    def task_now() -> dict:
        return next(task for task in project.read_tasks(root) if task["slug"] == slug)

    seen = len(mine()) if event else 0
    started = time.time()

    def changed() -> float | None:
        try:
            return quiet.stat().st_mtime if quiet else None
        except OSError:
            return None

    try:
        while True:
            if event:
                found = mine()
                if len(found) > seen:
                    return {"task": slug, "event": found[-1], "gone": False}
            else:
                task = task_now()
                if task["status"] in until:
                    return {
                        "task": slug,
                        "status": task["status"],
                        "line": first_line(task),
                        "since": task["since"],
                        "gone": False,
                    }
            if companion and gone_companion(where, companion, began, datetime.now(UTC)):
                task = task_now()
                return {
                    "task": slug,
                    "status": task["status"],
                    "line": first_line(task),
                    "since": task["since"],
                    "gone": True,
                    "companion": companion,
                    "say": (
                        f"the companion {companion} of {slug} is gone before the state "
                        "came, and the task is "
                        f"{task['status'] or 'with no state yet'}: read the plan's "
                        "`## Plan talk` and `talk` in `lem project tasks` before "
                        "anything else"
                    ),
                }
            if quiet and quiet_over(changed(), started, time.time()):
                task = task_now()
                return {
                    "task": slug,
                    "status": task["status"],
                    "line": first_line(task),
                    "since": task["since"],
                    "gone": False,
                    "quiet": True,
                    "file": str(quiet),
                    "say": (
                        f"{quiet.name} of {slug} has not changed for "
                        f"{QUIET_SECONDS // 60} minutes and no state came: "
                        "read the screen of each pane of the pair for one of the four "
                        "errors of a seat, and run the same wait again "
                        "when neither shows one"
                    ),
                }
            gone = gone_session(root, slug, where)
            if gone is not None:
                task = task_now()
                name = gone.get("name") or slug
                return {
                    "task": slug,
                    "status": task["status"],
                    "line": first_line(task),
                    "since": task["since"],
                    "gone": True,
                    "session": gone.get("session"),
                    "say": (
                        f"the session `{name}` of {slug} is gone, and the task is "
                        f"{task['status'] or 'with no state yet'}: nothing goes on "
                        f"with it until `lem session open {slug} --why dead` opens a "
                        "fresh one"
                    ),
                }
            time.sleep(every)
    except KeyboardInterrupt:
        raise SessionError(f"the wait for {slug} was stopped") from None


def cmd_first_line(root: Path, slug: str, every: float, bound: float) -> dict:
    project.task_directory(root, slug)
    where = place()
    end = time.monotonic() + bound
    try:
        while True:
            records = [
                record
                for record in project.events_named(root, "task.state")
                if record.get("task") == slug
            ]
            night = bool(
                project.nights(project.events_named(root, "task.mode")).get(slug)
            )
            found = first_line_end(slug, records, night=night)
            if found is not None:
                return found
            gone = gone_session(root, slug, where)
            if gone is not None:
                return {
                    "task": slug,
                    "say": None,
                    "gone": True,
                    "session": gone.get("session"),
                    "why": (
                        f"the session `{gone.get('name') or slug}` of {slug} is gone "
                        f"before its first line: `lem session open {slug} --why dead` "
                        "opens a fresh one"
                    ),
                }
            left = end - time.monotonic()
            if left <= 0:
                return {
                    "task": slug,
                    "say": None,
                    "gone": False,
                    "why": (
                        f"no first line of {slug} came in {bound / 60:g} minutes: "
                        "the board shows it when its session writes it"
                    ),
                }
            time.sleep(min(every, left))
    except KeyboardInterrupt:
        raise SessionError(
            f"the wait for the first line of {slug} was stopped"
        ) from None


def cmd_list(root: Path) -> list[dict]:
    where = place()
    nodes = tree(where)
    logged = project.events_named(root, *EVENTS, lem_signs.EVENT)
    events = [record for record in logged if record.get("event") in EVENTS]
    transcripts = [
        record for record in logged if record.get("event") == lem_signs.EVENT
    ]
    # the process table, read once and only when a live session has a record to read
    # it for
    table: list[str | None] = []
    settings = project.load(root)
    tasks = {task["slug"]: task for task in project.read_tasks(root, settings)}
    now = datetime.now(UTC)
    out = []
    for slug, opened in newest_opens(events).items():
        session = str(opened["session"])
        node = node_of(nodes, session)
        task = tasks.get(slug)
        # the whole state, every block: whether a lead ever ran for a queued task is in
        # an older one
        written = (
            project.text_of(project.task_directory(root, slug) / "state.md")
            if task and (project.task_directory(root, slug) / "state.md").is_file()
            else ""
        )
        try:
            phase = (
                phase_of(
                    slug,
                    task["status"],
                    first_line(task),
                    task["track"],
                    worktree=worktree_of(root, settings, slug) is not None,
                    state=written,
                )
                if task
                else None
            )
        except SessionError:
            # a parked task, or one that ended with its worktree gone, is in no phase
            phase = None
        after = [
            record
            for record in events
            if record.get("task") == slug
            and record["ts"] >= opened["ts"]
            and str(record.get("session", "")).upper() == session.upper()
        ]
        closed = next(
            (record for record in after if record.get("event") == "session.close"), None
        )
        wake = next(
            (
                record
                for record in reversed(after)
                if record.get("event") == "session.wake"
            ),
            None,
        )
        unanswered = False
        # the guard's own status message is no wait for the owner: the guard ends it at
        # 10 minutes, with the restart or the stop, so no row "does not answer" stands
        # beside its steps
        if (
            node is not None
            and wake is not None
            and wake.get("why") != "status"
            and (now - stamp(wake["ts"])).total_seconds() >= UNANSWERED_AFTER
        ):
            mailbox = ctl(
                where,
                "msg",
                "read",
                "--as",
                f"{session}:{left_pane(node)}",
                "--json",
                window=False,
            )
            unanswered = f"lem: {slug} {wake.get('why')}" in mailbox
        signs = {"sign": None, "shell": False, "signs": False, "turn": None}
        if live(node, opened, now):
            records = [record for record in transcripts if record.get("task") == slug]
            if lem_signs.own_records(records, session) and not table:
                table.append(process_table())
            signs = lem_signs.signs_of(
                records, session, table[0] if table else None, slug
            )
        out.append(
            {
                "task": slug,
                "session": session,
                "name": node.get("name") if node else opened.get("name"),
                "phase": phase,
                "opened_in": opened.get("phase"),
                "why": opened.get("why"),
                "since": opened["ts"],
                "workspace": opened.get("workspace"),
                "live": node is not None,
                "agent": agent_runs(node) if node else False,
                "selected": bool(node and node.get("active")),
                "closed": closed["why"] if closed else None,
                "unanswered": unanswered,
                **signs,
            }
        )
    return out


def process_table() -> str | None:
    """The machine's process table, `ps -A -o pid=,ppid=,command=`, or None when ps does
    not answer (lem_signs: with no table, no session's signs read). A byte that is not
    UTF-8 becomes one replacement character: one process of the machine, of any owner,
    can hold one in its command line."""
    try:
        ran = subprocess.run(
            ["ps", "-A", "-o", "pid=,ppid=,command="],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=PS_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return ran.stdout if ran.returncode == 0 else None


# ---- the transcript ----

COMMAND_NAME = re.compile(r"<command-name>(.*?)</command-name>", re.DOTALL)
COMMAND_ARGS = re.compile(r"<command-args>(.*?)</command-args>", re.DOTALL)


def typed_text(content: object) -> tuple[str, str | None]:
    """The text of a record the owner typed, and a slash command's arguments alone: a
    `/lem` line is kept as the command line he typed, `/lem ARGS` (Claude Code names a
    plugin's skill `/lem:lem`)."""
    if isinstance(content, list):
        text = "\n".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    else:
        text = content if isinstance(content, str) else ""
    text = text.strip()
    if text.startswith(("<command-message>", "<command-name>")) and (
        name := COMMAND_NAME.search(text)
    ):
        command = name[1].strip()
        plugin, colon, skill = command.lstrip("/").partition(":")
        if colon and plugin == skill:
            command = "/" + plugin
        args = (given[1] if (given := COMMAND_ARGS.search(text)) else "").strip()
        return (f"{command} {args}" if args else command), args
    return text, None


def transcript_turns(path: Path) -> list[dict]:
    """The turns of a Claude Code session's transcript, oldest first, each {"who":
    "owner" or "lem", "at": its first record's time, "text": its words}. The form is the
    harness's (`skills/lem/harness/claude-code.md`): one JSON record a line. The owner's
    turn is a `user` record whose `origin.kind` is `human`, with no `isMeta` (the text
    `/lem` loads) and no `isCompactSummary`; a task's notification, agterm's mail and a
    peer's message have another origin. The agent's turn is the text blocks of the
    `assistant` records between two prompts; a tool's call and its result are no words.
    A record of a subagent (`isSidechain`) is no turn of this session, and a
    `compact_boundary` ends nothing: the records before it are kept."""
    turns: list[dict] = []
    lem_open = False
    prompts = origins = 0
    for raw in path.read_bytes().splitlines():
        try:
            record = json.loads(raw.decode("utf-8", errors="replace"))
        except ValueError:
            continue
        if not isinstance(record, dict) or record.get("isSidechain"):
            continue
        kind = record.get("type")
        content = (
            (record.get("message") or {}).get("content")
            if isinstance(record.get("message"), dict)
            else None
        )
        if kind == "assistant":
            texts = (
                [
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                if isinstance(content, list)
                else []
            )
            words = "\n\n".join(text.strip() for text in texts if text.strip())
            if not words:
                continue
            if lem_open:
                turns[-1]["text"] += "\n\n" + words
            else:
                turns.append(
                    {"who": "lem", "at": record.get("timestamp"), "text": words}
                )
                lem_open = True
            continue
        if kind != "user":
            continue
        if isinstance(content, list) and any(
            isinstance(block, dict) and block.get("type") == "tool_result"
            for block in content
        ):
            continue
        # any other prompt ends the agent's turn: the owner's, a notification, a mail
        lem_open = False
        prompts += 1
        if "origin" in record:
            origins += 1
        origin = record.get("origin")
        if (
            record.get("isMeta")
            or record.get("isCompactSummary")
            or not (isinstance(origin, dict) and origin.get("kind") == "human")
        ):
            continue
        text, args = typed_text(content)
        if text:
            turns.append(
                {
                    "who": "owner",
                    "at": record.get("timestamp"),
                    "text": text,
                    "args": args,
                }
            )
    if prompts and not origins:
        raise SessionError(
            f"{path} names no prompt's origin, so the owner's turns cannot be told "
            "from the rest: this Claude Code writes its transcript in another form "
            "than harness/claude-code.md names; give the new session the talk by hand",
        )
    return turns


def flat(text: str) -> str:
    return " ".join(text.split())


def starts(turn: dict, start: str) -> bool:
    words = flat(start)
    return flat(turn["text"]).startswith(words) or (
        turn.get("args") is not None and flat(turn["args"]).startswith(words)
    )


def first_words(text: str) -> str:
    words = flat(text).split(" ")
    return " ".join(words[:FIRST_WORDS]) + (" …" if len(words) > FIRST_WORDS else "")


def talk_range(
    turns: list[dict], start: str, leave: list[str]
) -> tuple[list[dict], list[dict]]:
    """The turns from the newest owner turn that `start` starts to the newest turn, and
    what was left out: each owner turn that a text of `leave` starts (the newest one
    after the first turn), with the agent's turns after it until the next owner turn."""
    if not flat(start):
        raise SessionError(
            "--from is the first words of the owner's turn where the topic began, "
            "and it is empty"
        )
    begin = next(
        (
            index
            for index in range(len(turns) - 1, -1, -1)
            if turns[index]["who"] == "owner" and starts(turns[index], start)
        ),
        None,
    )
    if begin is None:
        raise SessionError(
            f"no turn of the owner starts with {start!r}: give the first words of his "
            "turn where the topic began, as he typed them"
        )
    kept = turns[begin:]
    out: set[int] = set()
    left: list[dict] = []
    for text in leave:
        if not flat(text):
            raise SessionError(
                "a --leave text is the first words of an owner turn to leave out, "
                "and it is empty"
            )
        at = next(
            (
                index
                for index in range(len(kept) - 1, 0, -1)
                if kept[index]["who"] == "owner" and starts(kept[index], text)
            ),
            None,
        )
        if at is None:
            raise SessionError(
                f"no turn of the owner after the first one starts with {text!r}: "
                "--leave names an owner turn of the copy, as he typed it"
            )
        if at in out:
            continue
        span = [at]
        while at + len(span) < len(kept) and kept[at + len(span)]["who"] == "lem":
            span.append(at + len(span))
        out.update(span)
        left.append(
            {
                "at": kept[at]["at"],
                "words": first_words(kept[at]["text"]),
                "lem_turns": len(span) - 1,
            }
        )
    return [turn for index, turn in enumerate(kept) if index not in out], sorted(
        left, key=lambda item: item["at"] or ""
    )


# the length of a time to its minute: `2026-11-19T14:17`
STAMP_TO_MINUTE = 16


def when(stamp_text: str | None) -> str:
    """`2026-11-19T14:17:34.495Z` as `2026-11-19 14:17 UTC`."""
    return (
        f"{stamp_text[:10]} {stamp_text[11:16]} UTC"
        if stamp_text and len(stamp_text) >= STAMP_TO_MINUTE
        else "an unknown time"
    )


def talk_text(slug: str, kept: list[dict], left: list[dict], source: Path) -> str:
    owners = sum(1 for turn in kept if turn["who"] == "owner")
    lines = [
        f"# The talk that led to the ask of {slug}",
        "",
        (
            "Copied word for word from the session where it was asked "
            f"({source.name}): {len(kept)} turns, {owners} of the owner and "
            f"{len(kept) - owners} of the agent, from the owner's turn of "
            f'{when(kept[0]["at"])} that starts "{first_words(kept[0]["text"])}" to '
            "the newest turn."
        ),
        "",
    ]
    if left:
        lines += ["Left out as another topic:", ""]
        lines += [
            (
                f"- the owner's turn of {when(item['at'])} that starts "
                f'"{item["words"]}", with {item["lem_turns"]} '
                f"turn{'s' if item['lem_turns'] != 1 else ''} of the agent after it"
            )
            for item in left
        ]
        lines.append("")
    for turn in kept:
        lines += [
            (
                f"## {'The owner' if turn['who'] == 'owner' else 'The agent'}, "
                f"{when(turn['at'])}"
            ),
            "",
            turn["text"],
            "",
        ]
    return "\n".join(lines)


def transcript_file() -> Path:
    """This session's transcript: `~/.claude/projects/*/ID.jsonl`, with ID the session's
    `CLAUDE_CODE_SESSION_ID`, which Claude Code gives the Bash tool
    (`harness/claude-code.md`). `CLAUDE_CONFIG_DIR`, when set, stands
    for `~/.claude`."""
    session = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    if not session:
        raise SessionError(
            "CLAUDE_CODE_SESSION_ID is not set: run `lem session talk` from the Claude "
            "Code session where the owner asked, whose Bash tool has it"
        )
    if not re.fullmatch(r"[A-Za-z0-9-]+", session):
        raise SessionError(
            f"CLAUDE_CODE_SESSION_ID {session!r} is no session id of Claude Code: "
            "run this from the session where the owner asked"
        )
    home = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    found = sorted((home / "projects").glob(f"*/{session}.jsonl"))
    if not found:
        raise SessionError(
            f"no transcript {session}.jsonl under {home / 'projects'}: "
            "run this from the Claude Code session where the owner asked, whose "
            "transcript Claude Code keeps there"
        )
    if len(found) > 1:
        raise SessionError(
            f"two transcripts carry the session {session}: "
            f"{', '.join(map(str, found))}; move the one that is "
            "not this session's aside"
        )
    return found[0]


def cmd_talk(root: Path, slug: str, start: str, leave: list[str]) -> dict:
    directory = project.task_directory(root, slug)
    source = transcript_file()
    kept, left = talk_range(transcript_turns(source), start, leave)
    file = directory / TALK
    file.write_text(talk_text(slug, kept, left, source), encoding="utf-8")
    owners = sum(1 for turn in kept if turn["who"] == "owner")
    return {
        "task": slug,
        "file": str(file),
        "transcript": str(source),
        "turns": len(kept),
        "owner_turns": owners,
        "lem_turns": len(kept) - owners,
        "first": {"at": kept[0]["at"], "words": first_words(kept[0]["text"])},
        "left_out": left,
    }


@lem_release.one_command
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="lem session",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="a directory inside the checkout (default: the current one)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    opened = commands.add_parser(
        "open",
        help=(
            "open the task's session for the phase its state gives, "
            "or print the one that runs"
        ),
    )
    opened.add_argument("slug")
    opened.add_argument(
        "--why",
        choices=WHYS,
        default="owner",
        help="why it opens, for the record (default: owner)",
    )
    opened.add_argument(
        "--session",
        metavar="ID",
        help=(
            "with --why stopped: the session the restart replaces, "
            "which must still be the task's newest"
        ),
    )
    following = commands.add_parser(
        "next",
        help=(
            "the change of phase: open the next session after the handoff, "
            "and name this one handed off"
        ),
    )
    following.add_argument("slug")
    following.add_argument(
        "--same",
        action="store_true",
        help='the owner\'s "hand off": a fresh session for the same phase',
    )
    closing = commands.add_parser(
        "close", help="log the close of a session, then close it"
    )
    closing.add_argument("slug")
    closing.add_argument(
        "--session",
        metavar="ID",
        help="the session to close (default: the task's newest)",
    )
    closing.add_argument("--why", required=True, choices=CLOSES)
    closing.add_argument(
        "--when-unselected",
        action="store_true",
        help=(
            "wait until the owner has left the session, then close it; "
            "a wake of the session meanwhile ends the wait with no close"
        ),
    )
    closing.add_argument(
        "--every", type=float, default=CLOSE_EVERY, help=argparse.SUPPRESS
    )
    job = commands.add_parser(
        "close-job",
        help=(
            "close this session of a scheduled night or retro once the owner has left "
            "it; a task's session, or one no job started, is refused"
        ),
    )
    job.add_argument(
        "--session",
        metavar="ID",
        help="the job's session (default: AGTERM_SESSION_ID, the caller's)",
    )
    job.add_argument("--every", type=float, default=CLOSE_EVERY, help=argparse.SUPPRESS)
    handoff = commands.add_parser(
        "handoff", help="check the task's handoff.md against templates/handoff.md"
    )
    handoff.add_argument("slug")
    handoff.add_argument("--check", action="store_true", required=True)
    talk = commands.add_parser(
        "talk",
        help="copy the turns of this session about the task's ask into its talk.md",
    )
    talk.add_argument("slug")
    talk.add_argument(
        "--from",
        dest="start",
        required=True,
        metavar="TEXT",
        help="the first words of the owner's turn where the topic began",
    )
    talk.add_argument(
        "--leave",
        action="append",
        default=[],
        metavar="TEXT",
        help=(
            "the first words of an owner turn of another topic, left out with the "
            "agent's turns after it"
        ),
    )
    waking = commands.add_parser(
        "wake", help="a pane message to the task's live session, or a new session"
    )
    waking.add_argument("slug")
    waking.add_argument(
        "--why", required=True, choices=[why for why in WAKES if why != "replaced"]
    )
    waking.add_argument(
        "--head",
        metavar="SHA",
        help="the pull request's head the wake is for, kept on its record",
    )
    waking.add_argument(
        "--session",
        metavar="ID",
        help=(
            "with --why status: the session the line is for, "
            "which must still be the task's newest"
        ),
    )
    stopping = commands.add_parser(
        "stopped",
        help=(
            "log that the task's session stopped after the status message and its "
            "restart, or after the message alone when Lem cannot read its signs, "
            "for the owner"
        ),
    )
    stopping.add_argument("slug")
    stopping.add_argument(
        "--session",
        metavar="ID",
        help="the session the stop is for, which must still be the task's newest",
    )
    waiting = commands.add_parser(
        "wait",
        help=(
            "end when the task's state is one of these, a new event of its own is "
            "logged, or its first line is written"
        ),
    )
    waiting.add_argument("slug")
    until = waiting.add_mutually_exclusive_group(required=True)
    until.add_argument(
        "--until",
        metavar="STATE,...",
        help="the states that end the wait, joined by commas",
    )
    until.add_argument(
        "--event",
        metavar="NAME",
        help=(
            "the event that ends the wait, the first one logged for "
            "the task after its start"
        ),
    )
    until.add_argument(
        "--first-line",
        action="store_true",
        help="end with the task's first line, as this session says it",
    )
    waiting.add_argument(
        "--companion",
        metavar="ID",
        help=(
            "with --until or --event: end too when this companion of the waiting "
            "session is gone (the plan talk's pair)"
        ),
    )
    waiting.add_argument(
        "--quiet",
        metavar="FILE",
        help=(
            'with --until and --companion: end too, with "quiet": true, when FILE has '
            f"not changed for {QUIET_SECONDS // 60} minutes since the later of its "
            "last change and the wait's start (the plan talk's talk-turns.md)"
        ),
    )
    waiting.add_argument(
        "--every", type=float, default=WAIT_EVERY, help=argparse.SUPPRESS
    )
    waiting.add_argument(
        "--bound", type=float, default=FIRST_LINE_BOUND, help=argparse.SUPPRESS
    )
    commands.add_parser("list", help="each task's newest session")
    commands.add_parser(
        "plugin-dir",
        help=(
            "the folder that --plugin-dir names on a launch line of this Lem, or null "
            "when this Lem is the installed plugin"
        ),
    )
    args = parser.parse_args(argv)
    if args.command == "plugin-dir":
        # no repository: the answer is this Lem's folder alone, which the plan talk's
        # pair takes too
        print(
            json.dumps(
                {"plugin_dir": plugin_dir(PLUGIN, os.environ)},
                indent=2,
                ensure_ascii=False,
            )
        )
        return
    try:
        root = project.repo_root(Path(args.repo))
        if (
            getattr(args, "session", None)
            and args.command in ("open", "wake")
            and args.why not in ("stopped", "status")
        ):
            raise SessionError(
                "--session goes with `open --why stopped` and `wake --why status`, the "
                "steps of the guard of a stopped session; "
                f"`{args.command} --why {args.why}` takes the task's newest session"
            )
        slug = getattr(args, "slug", None)
        if slug is not None and project.SLUG.fullmatch(slug):
            # the release rule (lem_release) for a command that names one task (`list`
            # and `close-job` name none): the close, and the wake and the open of a
            # session after a merge on GitHub, whose session cleans the task, pass
            ends = args.command == "close" or (
                args.command in ("open", "wake") and args.why == "merged"
            )
            stopped = lem_release.check(
                project.state_root(root) / "tasks" / slug, passes=ends
            )
            if stopped:
                raise SessionError(stopped)
        if args.command == "open":
            result: object = cmd_open(root, args.slug, args.why, named=args.session)
        elif args.command == "next":
            result = cmd_next(root, args.slug, same=args.same)
        elif args.command == "close":
            result = cmd_close(
                root,
                args.slug,
                args.session,
                args.why,
                when_unselected=args.when_unselected,
                every=max(0.01, args.every),
            )
        elif args.command == "close-job":
            result = cmd_close_job(root, args.session, max(0.01, args.every))
        elif args.command == "handoff":
            result = cmd_handoff(root, args.slug)
        elif args.command == "talk":
            result = cmd_talk(root, args.slug, args.start, args.leave)
        elif args.command == "wake":
            result = cmd_wake(root, args.slug, args.why, args.head, args.session)
        elif args.command == "stopped":
            result = cmd_stopped(root, args.slug, args.session)
        elif args.command == "wait" and args.first_line:
            if args.companion:
                raise SessionError(
                    "--companion goes with --until or --event: the first line comes "
                    "from the task's own session"
                )
            result = cmd_first_line(
                root, args.slug, max(0.01, args.every), max(0.0, args.bound)
            )
        elif args.command == "wait":
            states = [
                state.strip()
                for state in (args.until or "").split(",")
                if state.strip()
            ]
            if args.until is not None and not states:
                raise SessionError(
                    "--until names one state or more, joined by commas, "
                    "as --until open,held,landed"
                )
            if args.quiet and not (args.until and args.companion):
                raise SessionError(
                    "--quiet goes with --until and --companion: it wakes the lead of a "
                    "plan talk whose pair stopped writing its turns"
                )
            result = cmd_wait(
                root,
                args.slug,
                states,
                args.event,
                max(0.01, args.every),
                args.companion,
                Path(args.quiet).resolve() if args.quiet else None,
            )
        else:
            result = cmd_list(root)
    except (SessionError, project.SettingsError) as error:
        sys.exit(f"lem session: {error}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
