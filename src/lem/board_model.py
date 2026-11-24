"""The board's model: a repository's event log and Lem's files read into one object for
each task and one for the workspace, which the pages of `lem_board_pages` draw.

    model = derive(facts.events, facts.owner, now_ms(), meta=facts.meta)
    model.tasks                 every task with a state block or a session, in the order of its first event
    model.lane["you"]           the tasks of one column of the kanban
    waits_of(model)             one row for each thing the owner does
    wait_stacks(rows)           those rows grouped by task, as "Waits for you" draws and counts them
    wait_count(model)           how many tasks wait for the owner, in every place that says so
    card_line(task, lane)       what a card says
    now_head(task)              what the large card of a task says it does now
    time_of(task, end, meta)    where the time of one task went: its spans, marks and stages

The rules are pure functions over data: events in, model out, with the clock given
(`now`, in ms), so that a unit case calls them with a few events: which status a task is
in, who acts, which column it stands in, what waits for the owner and where he answers,
what a card says, green and its reasons, the phases; and for the board of one task, what
it waits for, the head of its large card, its criteria as they stand and the checks of
their tests, which decisions are important and why, a reason of not green in plain words
and each one cut into a row (`reason_parts`), its progress, and where its time went
(`time_of`). One rule says which words of a text are a pull request (`pull_refs`), and
one says when the server asks the forge itself (`forge_due`). A run of the checks ends
at its `gate.end`, and a landing whose run was stopped, red or refused is Lem's, with
the owner's next step in words after a stop (`checks_end`). A sentence here is Lem's own
and is said as it is.

The facts come in through the loaders at the end of this file (`Reader`), which read
each file only when its size or its change time moved, so that a page that renders after
a burst of events reads the log once: the event log (`events.jsonl`, read on from where
the last read stopped, and whole again when `lem project prune` put a new one in place),
the owner's mark (`project.owner_records`), and the settings, the backlog and the meta
facts through `board.py`'s functions, the board server's last look at the forge
(FORGE_LOOK, `Model.seen`), and its record of what it sent to the owner's Inbox while he
is away (INBOX_LOOK, `Model.inbox`, which `inbox_of` reads for a task's page), the open
`lem-ask` cards of each task's folder (`cards_look`, `Model.cards`, whose rows
`open_cards` gives), and what each task's folder says beside the log, the release it
began on and a change of its criteria that stopped in the middle (`task_files_look`, on
each Task). What does not read is a problem the page says, never an empty board.
"""  # noqa: E501 - the table of the model's names keeps its columns

import contextlib
import json
import math
import os
import re
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any, cast
from urllib.parse import quote

from lem import answers as lem_answers
from lem import cards as lem_cards
from lem import release as lem_release

# ---- the words of each status, and the lanes ----

# Who acts in each status, in the words of SKILL.md's table.
STATUS = {
    "queued": {
        "actor": "quiet",
        "who": "Lem",
        "label": "Queued",
        "icon": "clock",
        "live": False,
    },
    "building": {
        "actor": "lead",
        "who": "The agent",
        "label": "Building",
        "icon": "code",
        "live": True,
    },
    "planned": {
        "actor": "lem",
        "who": "Lem",
        "label": "Planned",
        "icon": "file",
        "live": False,
    },
    "held": {
        "actor": "you",
        "who": "You",
        "label": "Waits for you",
        "icon": "user",
        "live": True,
    },
    "blocked": {
        "actor": "bad",
        "who": "Lem",
        "label": "Blocked",
        "icon": "alert",
        "live": False,
    },
    "ready": {
        "actor": "gate",
        "who": "Lem",
        "label": "Ready for its checks",
        "icon": "flag",
        "live": False,
    },
    "landing": {
        "actor": "gate",
        "who": "The checks",
        "label": "Checks and review",
        "icon": "play",
        "live": True,
    },
    "open": {
        "actor": "you",
        "who": "You",
        "label": "Waits for the merge",
        "icon": "branch",
        "live": False,
    },
    "landed": {
        "actor": "done",
        "who": "Nobody",
        "label": "Landed",
        "icon": "check",
        "live": False,
    },
    "dropped": {
        "actor": "quiet",
        "who": "Nobody",
        "label": "Dropped",
        "icon": "x",
        "live": False,
    },
    "answered": {
        "actor": "done",
        "who": "Nobody",
        "label": "Answered",
        "icon": "file",
        "live": False,
    },
    "parked": {
        "actor": "quiet",
        "who": "Nobody",
        "label": "Parked",
        "icon": "park",
        "live": False,
    },
    # the board's own word for a task whose session opened and wrote no state block yet
    # (NEW): no stage writes it
    "new": {
        "actor": "lem",
        "who": "Its session",
        "label": "Starting",
        "icon": "play",
        "live": True,
    },
}
STATUS_ORDER = list(STATUS)
UNKNOWN = {
    "actor": "bad",
    "who": "Nobody",
    "label": "No status",
    "icon": "alert",
    "live": False,
}
# The status of a task with a `session.open` and no state block: its session reads the
# request, and the task is on the board from its first minute (`derive`). It is the
# board's word, never a state of project.py.
NEW = "new"
NEW_TEXT = "its session opened and reads the request; it wrote no state yet"
# The line with which a landing writes `blocked` while the base branch fails a check
# (stages/land.md step 4): the task's session waits for the task that repairs the base,
# and nothing waits for the owner.
BASE_RED = "the base is red"
# The fixed line of a block that a seat's error wrote (project.py FAILED_LINE,
# `lem project seat-failed`): the seat whose agent gave an error, and no fallback could
# stand in for it. A block of the merge agent's seat keeps its pull request, which the
# server's look at GitHub still watches (serve.py `open_prs`).
FAILED_SEAT = re.compile(r"the seat that failed: (reviewer|planner|merger)")
# each such seat as the records name it (lem_state.SEAT_NAMES)
SEAT_WORDS = {
    "reviewer": "the reviewer",
    "planner": "the planner",
    "merger": "the merge agent",
}
# The states a task does not leave (project.py ENDED): nobody acts, and nothing of
# it waits.
ENDED = ("landed", "dropped", "answered")
# The ended states whose task still gets a session while its worktree is there, as
# session.py's `phase_of` admits them: the session cleans up and pays what the ticket is
# still owed, after a merge or after a pull request closed on GitHub. An `answered`
# task, or one whose worktree is gone, gets none.
CLEANED_BY_SESSION = ("landed", "dropped")
# The state of a task the owner put aside (`/lem park`, project.py PARKED): nobody acts,
# and nothing of it waits for him, also when a breaker of it still does;
# `/lem resume SLUG` brings it back.
PARKED = "parked"
# The type of a request, from its state line `type: TYPE, because WHY` (stages/new.md).
TYPES = ("feat", "fix", "docs", "refactor", "perf", "test", "chore", "question")
# The records' own words for the fast track (SKILL.md), which the page says in the
# track's name.
FAST_BUILDER = re.compile(r"^small change: one builder$")
FAST_JOB = "the small change"
FAST_GREW = re.compile(r"\bthe small change is a full change$")
TRACKS = {"small": "fast", "full": "standard"}
# What the investigation of a fix or a question found (project.py `log investigation`).
CALLS = {
    "small": {
        "head": "The investigation found a plain cause: the fast track fixes it",
        "card": "The cause",
        "now": (
            "A plain cause, which one rule fixes: the task goes on by the fast track"
        ),
    },
    "full": {
        "head": "The investigation found a plain cause: the standard track",
        "card": "The cause",
        "now": "A plain cause, and the standard track: the interview starts from it",
    },
    "not-a-bug": {
        "head": "The investigation found no bug",
        "card": "No bug",
        "now": "No bug: the code does what it should",
    },
    "not-reproduced": {
        "head": "The investigation did not reproduce the bug",
        "card": "Not reproduced",
        "now": "Not reproduced: Lem asks you for one more fact",
    },
    "answer": {
        "head": "The investigation answered the question",
        "card": "The answer",
        "now": "The answer to the question",
    },
}
CRITERIA_WAIT = re.compile(r"\bcriteria wait\b")
# Who answers a wait for the owner's yes to the criteria: the owner, or `alone` for a
# task that runs without him.
APPROVERS = ("owner", "alone")
# The owner's word to skip the personas' read of the criteria (land.py READ_SKIP).
READ_SKIP = {
    "what": "the personas' read of the criteria",
    "chose": "no read: the criteria name only the developer",
}
# Who acts on a held task's criteria, from the events after its newest block
# (`turn_of`): the owner answers the interview's questions (`asks`), Lem writes the
# criteria once they ended (`writes`), the owner says whether to skip the personas' read
# (`skip`), the personas read them (`reads`), and the owner gives his yes once the read
# is in or he skipped it (`yes`). The three that are his:
OWNER_TURNS = ("asks", "skip", "yes")
# The statuses whose time counts from the block that named the wait, not from the first
# block of the status (`settle`): the interview's held block and the criteria's are two
# waits, and a block written again with the same first line is the same one.
WAIT_CLOCKS = ("held", "blocked")
# The words of Lem's turn and of the skip question, on the card and in the row of "Waits
# for you".
WRITES_SAYS = "Lem writes the criteria; then they come to you."
SKIP_SAYS = "Lem asks whether to skip the personas' read of the criteria"
# The first line of a held block whose request waits for the owner's one answer
# (`stages/new.md`, "The request").
ANSWER_WAIT = "the request waits for one answer"
# What Lem does for a held task's need while the task runs without the owner
# (`stages/away.md`): the need is the interview, the criteria, or the request's
# one answer.
GOES_ON = {
    "interview": (
        "Lem answers the interview with its own guesses, each in the task's decisions "
        "for the pull request, and approves the criteria without you"
    ),
    "criteria": (
        "Lem settles the criteria and approves them without you, each step in the "
        "task's decisions for the pull request"
    ),
    "answer": (
        "Lem takes the safer read of the request and goes on without you, the read in "
        "the task's decisions for the pull request"
    ),
}
# The lanes are who acts: the owner, a lead and its builders, the machine checks and
# the review.
LANES = [
    {
        "key": "you",
        "title": "Waits for you",
        "actor": "you",
        "empty": "Nothing waits for you",
    },
    {"key": "build", "title": "Building", "actor": "lead", "empty": "No task builds"},
    {
        "key": "checks",
        "title": "Checks and review",
        "actor": "gate",
        "empty": "No branch is checked or reviewed",
    },
    {"key": "done", "title": "Done", "actor": "done", "empty": "Nothing landed yet"},
]
LANE = {lane["key"]: lane for lane in LANES}
# The ended tasks Done draws as cards, the newest first: its head counts every ended
# task, and a page of the board lists the rest. An unmeasured estimate of a column that
# fits one screen of the large board (docs/plans/2026-11-21-done-column-shows-newest.md,
# 2026-11-21).
DONE_SHOWN = 20
# 'Proposed' is the pull request on GitHub.
PHASES = ["Criteria", "Plan", "Build", "Checks", "Review", "Proposed", "Landed"]
SMALL_PHASES = ["Change", "Checks", "Review", "Proposed", "Landed"]
# What waits for the owner, the most pressing first.
OWNER_ORDER = ["breaker", "held", "queued", "blocked", "planned", "open"]
BY_WHOM: dict[object, str] = {
    "lead": "the agent",
    "personas": "the personas",
    "owner": "you",
    "lem": "Lem",
    "experts": "the experts",
    "gate": "the question gate",
    "dialectic": "the dialectic",
}
# Who works on a task, from its state lines, in words a developer needs no glossary for.
LEAD = {
    "session": {
        "tag": "plan talk",
        "chip": "plan talk",
        "title": (
            "A companion session talks the plan through, with the reviewer in its "
            "other pane; an agent builds it after the talk"
        ),
        "head": "Its companion talks the plan through",
        "stat": (
            "a companion talks the plan through, with the reviewer in its other pane"
        ),
    },
    "talked": {
        "tag": "one agent",
        "chip": None,
        "title": "One agent builds it, after the plan talk in its companion",
        "head": "An agent builds it",
        "stat": "one agent builds the plan its companion talked through",
    },
    "builder": {
        "tag": "one agent",
        "chip": None,
        "title": (
            "One agent plans this task, and a fresh builder "
            "builds each task of its plan"
        ),
        "head": "An agent plans and builds it",
        "stat": "one agent plans it, and a fresh builder builds each task of the plan",
    },
    "small": {
        "tag": "one builder",
        "chip": "fast track",
        "title": (
            "The fast track: one builder makes it, with no lead and no plan, "
            "and the landing checks it"
        ),
        "head": "One builder makes the change",
        "stat": "one builder makes the change, with no lead and no plan",
    },
}
EXPERTS = {"fable": "Fable", "astra": "Astra"}
IRREVERSIBLE: dict[object, str] = {
    "data": "it destroys or rewrites data outside the worktree",
    "system": "it writes to a system outside the repository",
    "person": "it sends something to a person",
    "money": "it spends money",
}
# The two causes of the circuit breaker (decisions.py CAUSES), in the page's words.
BREAKS: dict[object, str] = {
    "irreversible": "the next step cannot be undone by a later “no”",
    "criteria": "no option keeps the criteria you approved",
}
# A held block's first line while a breaker holds the task (decisions.py BREAKER_WAIT).
BREAKER_WAIT = re.compile(r"breaker ([1-9]\d*) waits for the owner")
FAMILIES = {1: "one model family", 2: "two model families"}
# The events that cut a landing, the starts of its steps, and what a landing waits
# for (land.py).
CHECKS = (
    "polish",
    "gate",
    "task.red",
    "gate.end",
    "review",
    "review.filed",
    "proposed",
)
LANDING_STARTS = ("polish.start", "gate.start", "review.start", "builder.start")
WAITS = ("gate.wait", "merge.wait")
# The one event that stands for every event of an ended task that nothing happened in
# for `state.keep_days` days, which only `lem project prune` writes (project.py SUMMARY,
# `summary_of`), in the place of the task's newest event.
SUMMARY = "task.summary"
# The stop of a command for a task two releases back (lem_release.STOP): while it is
# newer than the task's newest state, the task is shown blocked with its message, and
# its status stays the one of its state.
RELEASE_STOP = "release.stop"
# What such a task does now, in words: its row's and its large card's head.
OLDER_RELEASE = "It began on an older release of Lem"
# How a run of the checks ended, by the `result` of its `gate.end` (land.py RESULTS).
CHECKS_END: dict[object, dict[str, str]] = {
    "passed": {
        "head": "The checks passed",
        "label": "Checks passed",
        "after": "Lem, between two steps of the landing",
    },
    "red": {
        "head": "The checks are red",
        "label": "Checks red",
        "after": "After the checks were red: Lem starts a builder that repairs it",
    },
    "refused": {
        "head": "The checks refused the change",
        "label": "Checks refused",
        "after": (
            "After the checks refused the change: Lem starts a builder that repairs it"
        ),
    },
    "stopped": {
        "head": "The checks were stopped",
        "label": "Checks stopped",
        "after": "The checks were stopped: the landing waits for your word",
    },
}
STEP_RUNS: dict[object, str] = {
    "polish.start": "The polish pass runs",
    "gate.start": "The checks run",
    "review.start": "The review runs",
}
# The three kinds of review, in the words of land.py.
KIND: dict[object, str] = {
    "read": "one read",
    "round": "a round with the profiles that fit",
    "full": "the project's full set",
}
# What green means, in the words of the first line of a green pull request (`GREEN`
# in land.py).
GREEN = (
    "The checks passed with the bar where it was, the review left no must-fix, no "
    "criterion changed, and no decision past the personas was taken without an answer"
)
PULL = re.compile(r"\bhttps?://\S+/pull/(\d+)\b")
# Why a task's session closed (`lem session close --why`), and why one opened or was
# woken, in words.
CLOSED = {
    "handoff": "a fresh session took its place",
    "ended": "the task ended",
    "owner": "you closed it",
}
OPENED = {
    "new": "for a new task",
    "handoff": "for the next phase",
    "dead": "in place of one that was gone",
    "merged": "after the merge, for the cleanup",
    "conflict": "to bring its pull request onto the base",
    "queue": "the task it waited for ended",
    "night": "for the night",
    "owner": "on your word",
    "stopped": (
        "beside the one that stopped, whose name in agterm now ends in “replaced”"
    ),
}
# How long a task may have no live session before the board says so: the time a session
# takes from its open to its agent (a guess, plan-task-4.md section 2, 2026-11-21).
GRACE_MS = 2 * 60 * 1000
# The merge review that calls the owner comes before the merge it is about.
WAIT_ORDER = {
    "breaker": 0,
    "session": 0,
    "stopped": 0,
    "criteria": 1,
    "held": 1,
    "card": 1,
    "after_dropped": 1,
    "blocked": 1,
    "plan": 2,
    "review": 3,
    "merge": 4,
}


# ---- formatting ----


def now_ms() -> int:
    return int(time.time() * 1000)


def at(ts: object) -> int | None:
    """An event's `ts` (ISO 8601, `Z` for UTC) in ms, or None when it does not read as
    a time."""
    if not isinstance(ts, str):
        return None
    try:
        moment = datetime.fromisoformat(ts)
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return int(moment.timestamp() * 1000)


# A span says its seconds under ten minutes, and its hours under two days (`span`); a
# time under five seconds ago is now (`ago`).
SECONDS_SHOWN_M = 10
HOURS_SHOWN_H = 48
JUST_NOW_MS = 5000


def span(ms: float) -> str:
    """A length of time as the board says it: 45s, 3m 07s, 25m, 2h 05m, 3d 4h."""
    s = max(0, round(ms / 1000))
    m, seconds = divmod(s, 60)
    if not m:
        return f"{s}s"
    if m < SECONDS_SHOWN_M:
        return f"{m}m {seconds:02d}s"
    hours, minutes = divmod(m, 60)
    if not hours:
        return f"{m}m"
    return (
        f"{hours}h {minutes:02d}m"
        if hours < HOURS_SHOWN_H
        else f"{hours // 24}d {hours % 24}h"
    )


def ago(ms: float) -> str:
    return "just now" if ms < JUST_NOW_MS else f"{span(ms)} ago"


def local(ms: float) -> datetime:
    return datetime.fromtimestamp(ms / 1000)  # noqa: DTZ006 - the board shows the clock of the machine it runs on


def hhmm(ms: float) -> str:
    return local(ms).strftime("%H:%M")


def day_label(ms: float) -> str:
    moment = local(ms)
    return f"{moment.strftime('%b')} {moment.day}"


def stamp(ms: float, now: float) -> str:
    """A clock time, with its date when it is not on the day of `now`: 00:10 and 23:50
    do not read as one evening."""
    return (
        "" if local(ms).date() == local(now).date() else f"{day_label(ms)} "
    ) + hhmm(ms)


def plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def criteria_count(n: int) -> str:
    return f"{n} {'criterion' if n == 1 else 'criteria'}"


def track_words(size: str | None) -> str:
    return f"{TRACKS.get(size, size)} track" if size else "criteria"


def cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def title_of(slug: object) -> str:
    """ "report-dates-stay-whole" -> "Report dates stay whole": the owner reads names,
    never codes."""
    words_ = re.sub(r"-+", " ", str(slug)).strip()
    return cap(words_) if words_ else "A task"


def flat(text: object) -> str:
    return " ".join(str(text).split())


def yours(s: str) -> str:
    """The stages write what waits for the developer in the third person; the page
    speaks to him."""
    s = re.sub(r"\b(waits?|waiting) for the owner['’]s\b", r"\1 for your", s)
    return re.sub(r"\b(waits?|waiting) for the owner\b", r"\1 for you", s)


def type_line(line: str) -> dict | None:
    found = re.match(r"^type: ([a-z]+), because (.+)$", line)
    return {"type": found[1], "why": found[2]} if found and found[1] in TYPES else None


def words(line: object, *, talked: bool = False) -> str | None:  # noqa: C901, PLR0911, PLR0912 - over the limit before the limit was set
    """A line of a state block as the page says it: a fixed line of the scripts in
    words, or left out (None) where the page says it elsewhere; any other line is the
    agent's own and stays as written."""
    s = str(line)
    if re.match(r"^lead: builder\b", s):
        return (
            "an agent builds the plan its companion talked through"
            if talked
            else "an agent plans and builds it"
        )
    if FAST_BUILDER.search(s):
        return "one builder makes the change"
    if FAST_GREW.search(s):
        return yours(FAST_GREW.sub("the task takes the standard track", s))
    if re.match(r"^lead: session\b", s):
        return "its companion talks the plan through"
    if re.fullmatch(r"investigation: (bug|question)", s):
        return None
    typed = type_line(s)
    if typed:
        return f"{typed['type']}, because {typed['why']}"
    plan = (
        re.search(r"\b(\d+) tasks?\b", s) if re.match(r"^plan committed\b", s) else None
    )
    if plan:
        return f"the plan is committed, with {plural(int(plan[1]), 'task')}"
    if re.match(r"^plan committed\b", s):
        return "the plan is committed"
    after = re.fullmatch(r"after: ([a-z0-9-]+)", s)
    if after:
        return f"it starts after “{title_of(after[1])}” ends"
    if BREAKER_WAIT.fullmatch(s):
        return "the build stopped, and its breaker waits for you"
    if s == CHANGED_CRITERIA:
        return "the criteria changed from your note, and wait for your yes again"
    if s == UNCHANGED_CRITERIA:
        return (
            "your note changed no criterion, and the criteria wait for your yes again"
        )
    resumed = re.fullmatch(r"resumed from ([a-z0-9-]+), which was dropped", s)
    if resumed:
        return f"it goes on from “{title_of(resumed[1])}”, which was dropped"
    if re.fullmatch(r"report: \S+", s):
        return None
    return yours(s)


def said_of(block: dict, *, talked: bool = False) -> list[str]:
    """A state block's lines as the page says them; `talked` when a plan talk ended
    before it."""
    return [
        said
        for said in (
            words(line, talked=talked)
            for line in [block.get("text", ""), *(block.get("lines") or [])]
        )
        if said
    ]


def held_need(line: object) -> dict | None:
    """What the task's session waits on the owner for, from the first line of a held
    block: the interview, the criteria, or the breaker by its number."""
    s = str(line or "")
    if s.startswith("the interview waits for the owner") or FAST_GREW.search(s):
        return {"need": "interview", "number": None}
    if s.startswith("the criteria wait for the owner"):
        return {"need": "criteria", "number": None}
    breaker = BREAKER_WAIT.fullmatch(s)
    return {"need": "breaker", "number": int(breaker[1])} if breaker else None


def lines_of(block: dict) -> list[str]:
    return [block.get("text", ""), *(block.get("lines") or [])]


def task_line(block: dict) -> re.Match[str] | None:
    return (
        re.search(r"\btask (\d+) of (\d+)\b", " ".join(lines_of(block)))
        if block["status"] == "building"
        else None
    )


def investigates(block: dict) -> bool:
    return block["status"] == "building" and any(
        line.startswith("investigation:") for line in lines_of(block)
    )


def small_block(block: dict) -> bool:
    return block["status"] == "building" and any(
        FAST_BUILDER.search(line) for line in lines_of(block)
    )


def waits_for_task(block: dict) -> bool:
    """Whether a state block has an `after: SLUG` line: a task it needs, or one the
    owner's words put it after."""
    return any(re.fullmatch(r"after: [a-z0-9-]+", line) for line in lines_of(block))


def checks_end(result: object) -> dict:
    return CHECKS_END.get(result) or {
        "head": f"The checks ended: {result or 'no result'}",
        "label": "Checks ended",
        "after": "Lem, after the checks",
    }


def say_of(end: dict) -> str:
    """The `say` of a `gate.end` without the task's name before it (land.py checks_say:
    "SLUG: ...")."""
    return re.sub(r"^[a-z0-9-]+: ", "", str(end.get("say") or ""))


def refused_of(end: dict) -> str:
    said = say_of(end)
    found = re.search(
        r"the checks refused the change: (.*?)(?:; a builder repairs it\b.*)?$", said
    )
    return found[1] if found else said


def expert_name(key: str) -> str:
    return EXPERTS.get(key, key)


def talk_counts(x: dict) -> str:
    """A plan talk's record in words: its questions and turns, how its questions ended,
    its repairs."""
    g = lambda k: x.get(k) or 0  # noqa: E731
    over = (
        f", over the bound of {x['bound']} for its {plural(g('questions'), 'question')}"
        if x.get("bound") is not None and g("turns") > x["bound"]
        else ""
    )
    design = (
        (
            f", {x['design']} of them "
            f"{'a design choice' if x['design'] == 1 else 'design choices'}"
        )
        if x.get("design")
        else ""
    )
    where = [
        *([f"{x['root']} at the cause"] if x.get("root") else []),
        *(
            [
                (
                    f"{x['layer']} {'a layer' if x['layer'] == 1 else 'layers'} over a "
                    "cited decision"
                )
            ]
            if x.get("layer")
            else []
        ),
    ]
    parts = [
        f"{plural(g('questions'), 'question')} in {plural(g('turns'), 'turn')}{over}",
        f"{x.get('settled')} settled, {x.get('open')} open{design}",
        f"{x.get('repaired')} repaired{': ' + ', '.join(where) if where else ''}",
    ]
    if x.get("shared"):
        parts.append(
            f"{x['shared']} {'decision' if x['shared'] == 1 else 'decisions'} two "
            "questions named"
        )
    if x.get("unargued"):
        parts.append(f"{x['unargued']} raised, not argued")
    return " · ".join(parts)


def review_line(r: dict) -> str:
    head = (
        "the conflict’s resolution"
        if r.get("of") == "resolution"
        else f"round {r.get('round')}"
    )
    verdict = (
        "not reviewed"
        if r.get("verdict") == "not reviewed"
        else (
            f"{r.get('verdict')}, {r.get('must_fix')} must-fix, {r.get('should')} "
            f"should, {r.get('nit')} nit"
        )
    )
    return f"{head}, {KIND.get(r.get('kind'), r.get('kind'))}: {verdict}"


# ---- the model ----


@dataclass
class Decision:
    id: object
    kind: str
    ts: int
    what: object = None
    chose: object = None
    why: object = None
    by: object = None
    said: object = None
    undo: object = None
    options: list = field(default_factory=list)
    # `taken` for a decision; for a breaker `waits`, or `helped` once a decision of the
    # owner's names it
    state: str = "taken"
    advisers: list | None = None
    levels: dict | None = None
    unsettled: bool = False
    # the owner's help on a breaker: the breaker's number, and his own words
    breaker: int | None = None
    words: object = None
    # a breaker (decisions.py `breaker`): its cause, the kind of a step no "no" undoes,
    # its document and handoff in the task directory, and the decision of the owner's
    # that helped it, with its time
    stop: object = None
    irreversible: object = None
    document: object = None
    handoff: object = None
    help: object = None
    helped: int | None = None
    # the dropped task a resumed task carried the record over from (project.py `resume`)
    copied: object = None
    # the decision's story, when its record has one (decisions.py `log` where it takes
    # them): the case as numbered steps, how the case is known, the cause, and a
    # mermaid chart
    case: list = field(default_factory=list)
    case_was: object = None
    cause: object = None
    chart: object = None


@dataclass
class Task:
    """One task as the board shows it: what its events said, folded in their order."""

    slug: str
    title: str
    ask: str | None = None
    blocks: list = field(default_factory=list)
    gates: list = field(default_factory=list)
    reviews: list = field(default_factory=list)
    proposal: dict | None = None
    criteria: dict | None = None
    red: dict | None = None
    lead: str | None = None
    session: str | None = None
    progress: dict | None = None
    commit: dict | None = None
    branch: str | None = None
    events: list = field(default_factory=list)
    decisions: dict = field(default_factory=dict)
    orphans: list = field(default_factory=list)
    changes: list = field(default_factory=list)
    approvals: list = field(default_factory=list)
    reads: list = field(default_factory=list)
    talks: list = field(default_factory=list)
    talk_start: dict | None = None
    filed: list = field(default_factory=list)
    missed: dict | None = None
    polish: dict | None = None
    type: dict | None = None
    investigation: dict | None = None
    # the task's first line to the owner, as `lem project state` composed it for the
    # block that names its path, while that block is the task's newest
    opening: str | None = None
    landing_step: dict | None = None
    checks_end: dict | None = None
    waits: dict | None = None
    # the task's agterm session, from the newest `session.open` (lem session): its id,
    # name, phase, why and time, when it was closed (`session.close` of that session),
    # and each wake-up (`session.wake`)
    opened: dict | None = None
    session_closed: int | None = None
    wakes: list = field(default_factory=list)
    # the merge agent's review of the newest proposal (`merge.review`), with its call on
    # a moved base (`base_call`, `safe` or `another round`), and the refusal of a merge
    # of it (`merge.refused`), GitHub's or Lem's own (`from`, and Lem's `kind`), until a
    # read that answers it (`answers_refusal`)
    merge_review: dict | None = None
    refused: dict | None = None
    # the tip of Lem's refusal of the owner's own merge because the base moved, once a
    # read answered it (`answers_refusal`): the board treats his merge as standing from
    # that read (`owner_stands`), before its `merge.stands` line, which the server's run
    # of his merge waits for (`stands_due` in serve.py); a new proposal clears it with
    # the refusal
    stood: str | None = None
    # set by `derive` once every event is read
    status: str = ""
    info: dict = field(default_factory=dict)
    text: str = ""
    shown: str = ""
    more: list = field(default_factory=list)
    last_ts: int = 0
    since: int = 0
    first: int = 0
    closed: bool = False
    # every decision and breaker of the record, by number; the breaker that waits while
    # the task is open (`stopped`, also when it is parked), and the one that waits for
    # the owner now (`breaker`)
    decided: list = field(default_factory=list)
    stopped: Decision | None = None
    breaker: Decision | None = None
    criteria_wait: bool = False
    need: dict | None = None
    approved: dict | None = None
    # the criteria wait for the owner's yes and it would count now: the need is the
    # criteria, or an interview whose criteria the personas read (or he skipped the
    # read) after its newest block
    approvable: bool = False
    # the personas' read of a held task's criteria that runs now (`turn_of`):
    # its `criteria.read.start`
    reading: dict | None = None
    # who acts on a held task's criteria now (`turn_of`, OWNER_TURNS), None for any
    # other task
    turn: str | None = None
    # the need of a held task that Lem settles without the owner, since the task runs
    # without him now (his mark says away, or a night's mark): `interview`, `criteria`
    # or `answer` (GOES_ON), else None
    goes_on: str | None = None
    helped: Decision | None = None
    waits_after: bool = False
    # the task a queued task waited for, which was dropped (`after_dropped`): it waits
    # for the owner's word
    dropped_after: str | None = None
    for_owner: bool = False
    # a held task of the owner's whose session's newest turn runs (`put_sessions`):
    # Lem's work until that turn ends; and what `settle` gave it (`for_owner`, `info`,
    # `shown`, `lane`), which it gets back then
    works: bool = False
    settled: dict | None = None
    # for an `open` task, who its merge waits for (`merge_wait`): "reads", "merges"
    # or "owner"
    merge_wait: str | None = None
    investigating: bool = False
    checks_stop: dict | None = None
    owner_rank: int = -1
    lane: str = "build"
    segments: list = field(default_factory=list)
    reached: str = ""
    investigated: bool = False
    plan_committed: bool = False
    gate_bad: int = 0
    # `blocked` while the base branch fails a check (BASE_RED): its session waits for
    # the repair, not for the owner
    base_red: bool = False
    # the seat a `blocked` task's newest block names as the one that failed
    # (FAILED_SEAT), or None
    failed_seat: str | None = None
    # each Claude Code session of the task, as the plugin's SessionStart hook logged it
    # (`session.transcript`): its id and the path of its transcript, which
    # lem_tokens reads
    transcripts: list = field(default_factory=list)
    # the task's summary (SUMMARY) as `lem project prune` wrote it, once its events
    # became that one event; the board of the task says so and shows what it
    # holds (board_task.py)
    summary: dict | None = None
    # the newest `release.stop` while no state came after it (RELEASE_STOP): `began`,
    # `running`, `branch`, `say`
    release_stop: dict | None = None
    # what the task's directory says beside the log (`task_files_look`), None while
    # nothing read it (a unit case): the release the task began on (lem_release),
    # whether that is older than the board's own (`behind`: no row the board answers
    # with its own buttons, since its session has no `board_answer`), and whether a
    # change of its criteria from the owner's note began under its newest state block
    # and did not end (`changing`: `criteria-before.json` names that block; no yes
    # counts until it ends)
    began: str | None = None
    behind: bool = False
    changing: bool = False
    # `approvable` as the log alone gives it (`settle`), which `task_files_look` narrows
    # by `changing`
    approvable_events: bool = False
    # each `lem-ask` card of the task's sessions with no `card.answered` or
    # `card.closed` in the log, by its page id: its first question's prompt and when it
    # went up. Whether it is open is its end file's to say (`Model.cards`, which the
    # Reader reads): the event after the end only tells the stream.
    cards: dict = field(default_factory=dict)


@dataclass
class Model:
    now: int
    tasks: list
    away: dict | None
    owners: list
    proposed: list
    building: list
    queued: list
    ready: list
    landing: list
    blocked: list
    parked: list
    for_owner: list
    landed_today: list
    unknown: list
    lane: dict
    by_slug: dict
    events: list
    meta: dict = field(default_factory=dict)
    # what the board server's last look at the forge said of each open task's pull
    # request, by its slug (`mergeable`, `head`): FORGE_LOOK of the state folder, which
    # serve.py writes at each look (`forge_once`) and the Reader reads; None while no
    # server has looked
    seen: dict | None = None
    # what the board server's last `lem session list` said of each task's session, by
    # its slug (`live`: the session is in agterm's tree; `agent`: an agent runs in its
    # pane; `unanswered`: a wake-up waits in it for 10 minutes; `sign`, `shell`, `signs`
    # and `turn`: the session's own signs of work, as lem_signs reads them; `worktree`:
    # the task's worktree is still there), which `put_sessions` puts here for serve.py,
    # `lem project waiting` and the guard; None while the server has not asked (a demo
    # workspace, or before its first look)
    sessions: dict | None = None
    # what the board server's Inbox thread last wrote of the owner's Inbox (`inbox_look`
    # of INBOX_LOOK): the door's last look and each thing it sent; None while no server
    # wrote it
    inbox: dict | None = None
    # the open `lem-ask` cards of each task, by its slug, as the files of its folder say
    # (`cards_look`): each card the log names with no end file, with its page, prompt,
    # time and the agterm session that put it up; None while nothing read the files (a
    # unit case), and then no card has a row
    cards: dict | None = None
    # the answers on record of each task's row that the board answers with its own
    # buttons (`answers_look`), by its slug, the record by the row's key (lem_answers);
    # None while nothing read the files, and then no row is hidden for an answer
    answers: dict | None = None


def decision_event(t: Task, e: dict, ts: int) -> None:
    """One line of decisions.py's record, as project.py logged it; `at` is the record's
    own time."""
    kind = str(e.get("event"))[len("decision.") :]
    if e.get("at"):
        ts = at(e["at"]) or ts
    if kind == "criterion":
        t.changes.append(
            {
                "ts": ts,
                "order": len(t.events),
                "change": e.get("change"),
                "how": e.get("how"),
                "criterion": e.get("criterion"),
                "was": e.get("was"),
                "now": e.get("now"),
                "why": e.get("why"),
                "decision": e.get("decision"),
                "by": e.get("by"),
                "said": e.get("said"),
                "approval": e.get("approval"),
            }
        )
        return
    if kind == "breaker":
        t.decisions[e.get("id")] = Decision(
            id=e.get("id"),
            kind=kind,
            ts=ts,
            what=e.get("what"),
            state="waits",
            stop=e.get("cause"),
            irreversible=e.get("irreversible"),
            document=e.get("document"),
            handoff=e.get("handoff"),
            copied=e.get("from"),
        )
        return
    if kind != "taken":
        return
    levels = e.get("levels") if isinstance(e.get("levels"), dict) else None
    d = t.decisions[e.get("id")] = Decision(
        id=e.get("id"),
        kind=kind,
        ts=ts,
        what=e.get("what"),
        chose=e.get("chose"),
        why=e.get("why"),
        by=e.get("by"),
        said=e.get("said"),
        undo=e.get("undo"),
        options=e.get("options") or [],
        advisers=e.get("advisers"),
        levels=levels,
        unsettled=e.get("unsettled") is True,
        breaker=e.get("breaker") if isinstance(e.get("breaker"), int) else None,
        words=e.get("words"),
        copied=e.get("from"),
        case=case_steps(e.get("case")),
        case_was=e.get("case_was"),
        cause=e.get("cause"),
        chart=e.get("chart") if isinstance(e.get("chart"), str) else None,
    )
    if d.breaker is None:
        return
    stopped = t.decisions.get(d.breaker)
    # the owner's help on a breaker the log does not hold is shown as such,
    # never dropped
    if stopped is None or stopped.kind != "breaker":
        t.orphans.append({"ts": ts, "id": d.id, "breaker": d.breaker, "chose": d.chose})
        return
    stopped.state, stopped.help, stopped.helped = "helped", d.id, ts


def case_steps(case: object) -> list[str]:
    """A record's case as its lines, as written: decisions.py keeps it as one text of
    numbered lines, a criterion as a list of lines; a line may be a label between two
    runs ("After:")."""
    lines = case if isinstance(case, list) else str(case or "").splitlines()
    return [str(line).strip() for line in lines if str(line).strip()]


# A step of a case, by its number, and a label between two runs of it
# ("Today:", "After:").
STEP = re.compile(r"^\d+[.)]\s+")
CASE_LABEL = re.compile(r"^[^.]{1,40}:$")


def case_runs(steps: list[str]) -> list[dict]:
    """A case's lines as its runs: each run's label ("" for none) and its steps without
    their numbers, so that "Today" and "After" read as two numbered lists."""
    runs: list[dict] = [{"label": "", "steps": []}]
    for line in steps:
        if CASE_LABEL.match(line) and not STEP.match(line):
            runs.append({"label": line[:-1], "steps": []})
        else:
            runs[-1]["steps"].append(STEP.sub("", line))
    return [r for r in runs if r["steps"] or r["label"]]


def same_tip(a: object, b: object) -> bool:
    """Whether two names of a commit are one commit: an event keeps a short id, a record
    the whole one."""
    return bool(a and b) and (str(a).startswith(str(b)) or str(b).startswith(str(a)))


def answers_refusal(
    refused: dict | None, before: dict | None, review: dict, proposed: object
) -> bool:
    """Whether a merge review (REVIEW) answers the refusal on record (REFUSED), as
    land.py's record of it clears `merge_refused` (`read_answers`): a read of the
    proposed tip (PROPOSED) with a verdict whose call on the moved base is `safe`, or
    that has no call on a move, answers Lem's refusal of that tip because the base moved
    (`kind: base`), unless the newest read of that tip before it (BEFORE) said `another
    round`, whose refusal only the new landing answers. land.py records a read with no
    call only when its brief named the checks' own base: main has their tree again,
    after a revert. A record with no verdict, which calls the owner, answers nothing,
    and no read answers any other refusal: GitHub's, a rule's, a tip's."""
    tip = review.get("tip")
    return bool(
        refused
        and review.get("verdict") in ("merge", "call")
        and review.get("base_call") in ("safe", None)
        and refused.get("from") == "lem"
        and refused.get("kind") == "base"
        and same_tip(refused.get("tip"), tip)
        and (not proposed or same_tip(proposed, tip))
        and not (
            before
            and same_tip(before.get("tip"), tip)
            and before.get("base_call") == "another round"
        )
    )


def fold(t: Task, e: dict, ts: int) -> None:  # noqa: C901, PLR0911, PLR0912, PLR0915 - over the limit before the limit was set
    """One event of a task into what the task holds."""
    event = str(e.get("event"))
    if event.startswith("decision."):
        decision_event(t, e, ts)
        return
    if event == SUMMARY:
        fold_summary(t, e, ts)
        return
    if event == "criteria.approved":
        t.approvals.append(
            {
                "ts": ts,
                "order": len(t.events),
                "number": e.get("number"),
                "by": e.get("by"),
                "size": e.get("size"),
                "why": e.get("why"),
                "digest": e.get("digest"),
                "criteria": e.get("criteria") or [],
                "replaces": e.get("replaces"),
            }
        )
        return
    if event == "criteria.read":
        t.reads.append(
            {
                "ts": ts,
                "order": len(t.events),
                "by": e.get("by"),
                "asked": e.get("asked"),
                "answered": e.get("answered"),
                "families": e.get("families") or [],
                "silent": e.get("silent") or [],
                "criteria": e.get("criteria"),
                "flagged": e.get("flagged"),
                "split": e.get("split") is True,
                "digest": e.get("digest"),
            }
        )
        return
    if event == "session.open":
        t.opened = {
            "session": e.get("session"),
            "name": e.get("name"),
            "phase": e.get("phase"),
            "why": e.get("why"),
            "ts": ts,
            "order": len(t.events),
        }
        t.session, t.session_closed = (
            (str(e["session"]) if e.get("session") else None),
            None,
        )
        return
    if event == "session.close":
        # the close of the newest session; one that names an older session, which a
        # handoff closes after it, changes nothing
        if t.opened and (
            not e.get("session") or e.get("session") == t.opened.get("session")
        ):
            t.session, t.session_closed = None, ts
        return
    if event == "session.wake":
        t.wakes.append(
            {
                "ts": ts,
                "order": len(t.events),
                "why": e.get("why"),
                "session": e.get("session"),
                "unread": e.get("unread") is True,
            }
        )
        return
    if event == RELEASE_STOP:
        t.release_stop = {
            "ts": ts,
            "began": e.get("began"),
            "running": e.get("running"),
            "branch": e.get("branch"),
            "say": str(e.get("say") or ""),
        }
        return
    if event == "session.stopped":
        # the guard's record of a stop (`stop_stands`), read from `t.events`: no step of
        # the task's own
        return
    if event == "card.asked":
        if e.get("page"):
            t.cards[str(e["page"])] = {
                "page": str(e["page"]),
                "prompt": str(e.get("prompt") or ""),
                "ts": ts,
            }
        return
    if event in ("card.answered", "card.closed"):
        t.cards.pop(str(e.get("page")), None)
        return
    if event == "session.transcript":
        t.transcripts.append(
            {
                "ts": ts,
                "claude": e.get("claude"),
                "transcript": e.get("transcript"),
                "source": e.get("source"),
            }
        )
        return
    if event == "plan.talk.start":
        t.talk_start = {"ts": ts, "reviewer": e.get("reviewer")}
        return
    if event == "plan.talk":
        t.talks.append(
            {
                "ts": ts,
                "start": t.talk_start["ts"] if t.talk_start else None,
                **{
                    k: e.get(k)
                    for k in (
                        "reviewer",
                        "turns",
                        "questions",
                        "settled",
                        "open",
                        "repaired",
                        "design",
                        "unargued",
                        "root",
                        "layer",
                        "shared",
                        "bound",
                    )
                },
            }
        )
        t.talk_start = None
        return
    if event == "merge.review":
        review = {
            "ts": ts,
            "verdict": e.get("verdict"),
            "calls": e.get("calls") is True,
            "why": e.get("why"),
            "by": e.get("by"),
            "tip": e.get("tip"),
            "base": e.get("base"),
            "base_call": e.get("base_call"),
            "base_why": e.get("base_why"),
        }
        refused = t.refused
        if refused is not None and answers_refusal(
            refused, t.merge_review, review, (t.proposal or {}).get("tip")
        ):
            if refused.get("by") == "owner":
                t.stood = refused.get("tip")
            t.refused = None
        t.merge_review = review
        return
    if event == "merge.refused":
        t.refused = {
            "ts": ts,
            "order": len(t.events),
            "said": e.get("said"),
            "by": e.get("by"),
            "tip": e.get("tip"),
            "from": e.get("from"),
            "kind": e.get("kind"),
        }
        return
    # a landing that waits: its checks for the machine's load or behind another landing,
    # or its merge call for another's merge
    if event in WAITS:
        t.waits = {
            "ts": ts,
            "event": event,
            **{
                k: e.get(k)
                for k in ("load", "start", "after", "behind", "behind_repo", "why")
            },
        }
        return
    t.waits = None
    # the newest step of the landing that started and has not ended yet
    if event in LANDING_STARTS:
        t.landing_step = e
    elif event != "task.state" and t.landing_step:
        t.landing_step = None
    # the newest end of a run of the checks, while the landing has not gone on since
    if event == "gate.end":
        t.checks_end = {"result": e.get("result"), "say": e.get("say")}
        return
    if event in LANDING_STARTS or event in CHECKS:
        t.checks_end = None
    if event == "review.filed":
        t.filed.append({"ts": ts, "items": e.get("items") or [], "tip": e.get("tip")})
        return
    if event == "careful.missed":
        t.missed = {"ts": ts, "round": e.get("round"), "why": e.get("why")}
        return
    if event == "polish":
        t.polish = {
            "ts": ts,
            "before": e.get("before"),
            "after": e.get("after"),
            "commits": e.get("commits"),
            "filed": e.get("filed") or [],
        }
        return
    if event == "investigation":
        t.investigation = {
            "ts": ts,
            "type": e.get("type"),
            "call": e.get("call"),
            "line": e.get("line"),
            "where": e.get("where"),
            "reproduced": e.get("reproduced"),
        }
        return
    if event == "task.criteria":
        t.criteria = {
            "order": len(t.events),
            "size": e.get("size"),
            "why": e.get("why"),
            "digest": e.get("digest"),
            "list": e.get("criteria") or [],
            "ts": ts,
        }
        return
    if event == "task.red":
        t.red = {
            "ok": e.get("ok"),
            "digest": e.get("digest"),
            "tests": e.get("tests") or [],
            "without": e.get("without_a_test") or [],
            "tip": e.get("tip"),
            "ts": ts,
        }
        return
    if event == "gate":
        # a result on another tip starts a new run, and a command's newer result
        # replaces its older one
        result = {
            "ts": ts,
            "command": e.get("command"),
            "exit": e.get("exit"),
            "last": e.get("last"),
            "tip": e.get("tip"),
        }
        if any(g["tip"] != result["tip"] for g in t.gates):
            t.gates = []
        t.gates = [g for g in t.gates if g["command"] != result["command"]] + [result]
        return
    if event == "review":
        # a review written down again after a cut-off run has the same attempt: it is
        # one review
        t.reviews = [
            r
            for r in t.reviews
            if r["attempt"] is None or r["attempt"] != e.get("attempt")
        ]
        t.reviews.append(
            {
                "ts": ts,
                **{
                    k: e.get(k)
                    for k in (
                        "attempt",
                        "round",
                        "of",
                        "kind",
                        "verdict",
                        "must_fix",
                        "should",
                        "nit",
                        "tip",
                    )
                },
                "answered": e.get("answered") or [],
                "silent": e.get("silent") or [],
                "ran": e.get("ran") or [],
                "left_out": e.get("left_out") or [],
                "careful": e.get("careful"),
                "careful_why": e.get("careful_why"),
            }
        )
        return
    if event == "proposed":
        t.proposal = {
            "ts": ts,
            "order": len(t.events),
            "green": e.get("green") is True,
            "reasons": e.get("not_green") or [],
            "tip": e.get("tip"),
        }
        # a new proposal is read again, and merged again
        t.merge_review, t.refused, t.stood = None, None, None
        return
    if event != "task.state":
        return
    t.landing_step = None
    # a state written after a release stop is the task's own work again, as a drop is
    t.release_stop = None
    status = e.get("status")
    if status != "landing":
        t.checks_end = None
    text = "" if e.get("text") is None else str(e.get("text"))
    lines = [str(line) for line in (e.get("lines") or [])]
    previous = t.blocks[-1]["status"] if t.blocks else None
    # a landing that starts is a new run of the gate; a task that comes back from the
    # build starts over
    if status == "landing" and previous != "landing":
        t.gates = []
    if status == "landing" and previous == "ready":
        t.reviews, t.proposal = [], None
    t.blocks.append(
        {
            "ts": ts,
            "order": len(t.events),
            "status": status,
            "text": text,
            "lines": lines,
        }
    )
    if e.get("ask"):
        t.ask = str(e["ask"])
    # the first line stands while its block is the task's newest: a later block is a
    # later moment of the task
    t.opening = str(e["say"]) if e.get("say") else None
    for line in [text, *lines]:
        lead = re.match(r"^lead: (builder|session)\b", line)
        if lead:
            t.lead = lead[1]
        if FAST_BUILDER.search(line):
            t.lead = "small"
        progress = (
            re.search(r"\btask (\d+) of (\d+)\b", line)
            if status == "building"
            else None
        )
        if progress:
            t.progress = {"n": int(progress[1]), "of": int(progress[2])}
        typed = type_line(line)
        if typed:
            t.type = typed
    joined = " ".join([text, *lines])
    planned = (
        re.search(r"\b(\d+) tasks?\b", joined)
        if status == "building" and re.search(r"\bplan committed\b", joined)
        else None
    )
    if planned:
        t.progress = {"n": 1, "of": int(planned[1])}
    if e.get("branch"):
        t.branch = e["branch"]
    if e.get("head") and e["head"] != (t.commit or {}).get("head"):
        t.commit = {"head": e["head"], "subject": e.get("subject") or "", "seen": ts}


def fold_summary(t: Task, e: dict, ts: int) -> None:
    """A task's summary (SUMMARY) as the task's whole past: one block, its newest, which
    also carries when the run of its status began (`since`), the task's first block
    (`first`), the pull request any of its blocks named (`pr`) and whether a plan talk
    ended before it (`talked`); and the facts its card reads from the other events: the
    ask, the branch, the type, the lead, the proposal and the investigation (the careful
    call and the criteria's size stay in `t.summary`, which `careful_of` and
    `criteria_size` read). Each is what this module read from the task's events, since
    project.py `summary_of` computes it with `derive`, so `settle`, the card, `pr_of`,
    `careful_of`, `after_ended` and `after_dropped` read a summarized task as before."""
    last = at(e.get("last")) or ts
    pr = e.get("pr") if isinstance(e.get("pr"), dict) and e["pr"].get("url") else None
    t.summary = e
    t.blocks = [
        {
            "ts": last,
            "order": len(t.events),
            "status": e.get("status"),
            "text": "" if e.get("text") is None else str(e["text"]),
            "lines": [str(line) for line in (e.get("lines") or [])],
            "since": at(e.get("since")) or last,
            "first": at(e.get("first")) or last,
            "pr": pr,
            "talked": e.get("talked") is True,
        }
    ]
    t.ask = str(e["ask"]) if e.get("ask") else None
    t.branch = str(e["branch"]) if e.get("branch") else None
    t.type = e["type"] if isinstance(e.get("type"), dict) else None
    t.lead = e["lead"] if e.get("lead") in LEAD else None
    p = e.get("proposal")
    t.proposal = (
        {
            "ts": at(p.get("ts")) or last,
            "order": len(t.events),
            "green": p.get("green") is True,
            "reasons": list(p.get("reasons") or []),
            "tip": p.get("tip"),
        }
        if isinstance(p, dict)
        else None
    )
    x = e.get("investigation")
    t.investigation = (
        {**x, "ts": at(x.get("ts")) or last} if isinstance(x, dict) else None
    )
    t.opening, t.landing_step, t.checks_end, t.waits, t.release_stop = (
        None,
        None,
        None,
        None,
        None,
    )


def lead_of(t: Task) -> str:
    return (
        "session"
        if t.lead == "session"
        else "small"
        if t.lead == "small"
        else "talked"
        if t.talks or t.lead == "talked"
        else "builder"
    )


def talked_before(t: Task, ms: int) -> bool:
    """Whether a plan talk ended by MS: one of the task's talks, or the summary's word
    for its past."""
    return any(x["ts"] <= ms for x in t.talks) or any(
        b.get("talked") and b["ts"] <= ms for b in t.blocks
    )


def skips_read(e: dict) -> bool:
    """Whether an event is the owner's word to skip the personas' read of the
    criteria (READ_SKIP)."""
    return (
        e.get("event") == "decision.taken"
        and e.get("by") == "owner"
        and e.get("what") == READ_SKIP["what"]
        and e.get("chose") == READ_SKIP["chose"]
    )


def turn_of(t: Task, last: dict) -> tuple[str, dict | None]:
    """Who acts on a held task's criteria now (OWNER_TURNS), folded over the events
    after its newest block, and the personas' read that runs now, its
    `criteria.read.start`, or None. The owner answers the interview's questions until
    they ended (`interview.end`), and the scout's read changes nothing of that; then Lem
    writes the criteria, until it asks him whether to skip the read (`read.skip.asked`)
    or the read starts; after the read (`criteria.read`) or his word to skip it, his yes
    is what is missing (stages/interview.md, steps 3 and 5). A held block with criteria
    and no interview has no end of questions, and only its read is not his. A read that
    started before the newest block is no read of what that block holds."""
    turn, read = "asks", None
    for e in t.events[last["order"] :]:
        event = e.get("event")
        if event == "interview.end":
            turn = "writes"
        elif event == "read.skip.asked":
            turn = "skip"
        elif event == "criteria.read.start":
            turn, read = "reads", e
        elif event == "criteria.read" or skips_read(e):
            turn, read = "yes", None
    return turn, read


def goes_on_of(t: Task, last: dict, *, away: bool) -> str | None:
    """The need of a held task that Lem settles without the owner now (GOES_ON), else
    None: the task runs without him while his mark says away (`away`), and from a
    night's own mark (`task.mode`) until it ends, as project.py `runs_without_owner`
    reads them. Its interview goes on with Lem's guesses, its criteria are approved
    without him, and its one question takes the safer read (stages/away.md). An order
    that names no task Lem can tell, an investigation's wait for one more fact and a
    breaker stay his."""
    if (
        t.status != "held"
        or t.breaker
        or not (away or any(e.get("event") == "task.mode" for e in t.events))
    ):
        return None
    if t.need and t.need["need"] in ("interview", "criteria"):
        return t.need["need"]
    return "answer" if last["text"].startswith(ANSWER_WAIT) else None


def settle(t: Task, now: int, *, away: bool = False) -> None:  # noqa: C901, PLR0912, PLR0915 - over the limit before the limit was set
    """What a task's events add up to, once every one is folded in; `away` when the
    owner's mark says that he is away."""
    last = t.blocks[-1]
    t.status = last["status"]
    t.info = dict(STATUS.get(t.status, UNKNOWN))
    t.text = last["text"]
    shown = said_of(last, talked=talked_before(t, last["ts"]))
    t.shown = shown[0] if shown else ""
    t.more = shown[1:]
    t.last_ts = last["ts"]
    # "since" is when the task entered the status it has now; a summary's block keeps
    # when its run began, and the task's first block. A wait of the owner's
    # (WAIT_CLOCKS) counts from the block that named it: an earlier block of the same
    # status counts only when it said the same first line, since another first line is
    # another wait
    i = len(t.blocks) - 1
    while (
        i > 0
        and t.blocks[i - 1]["status"] == t.status
        and (
            t.status not in WAIT_CLOCKS
            or t.blocks[i - 1]["text"].strip() == last["text"].strip()
        )
    ):
        i -= 1
    t.since = t.blocks[i].get("since", t.blocks[i]["ts"])
    t.first = t.blocks[0].get("first", t.blocks[0]["ts"])
    t.closed = t.status in ENDED
    # the breaker that holds the task: one at a time (decisions.py), and none once the
    # task ended; a parked task's breaker waits for nobody until `/lem resume` brings
    # it back
    t.decided = sorted(
        t.decisions.values(),
        key=lambda d: d.id if isinstance(d.id, (int, float)) else 0,
    )
    t.stopped = (
        None
        if t.closed
        else next(
            (
                d
                for d in reversed(t.decided)
                if d.kind == "breaker" and d.state == "waits"
            ),
            None,
        )
    )
    t.breaker = t.stopped if t.status != PARKED else None
    t.criteria_wait = t.status == "held" and bool(
        CRITERIA_WAIT.search(" ".join(lines_of(last)))
    )
    t.need = held_need(last["text"]) if t.status == "held" else None
    # criteria approved and no lead yet: an approval by the owner (or `alone`) after the
    # newest block, and for an interview after the newest read of its criteria since
    # then, or his word to skip it
    read_in = None
    if t.need and t.need["need"] == "interview":
        read_in = [r["ts"] for r in t.reads if r["order"] > last["order"]] + [
            d.ts
            for d in t.decisions.values()
            if d.kind == "taken"
            and d.by == "owner"
            and d.what == READ_SKIP["what"]
            and d.chose == READ_SKIP["chose"]
            and d.ts >= last["ts"]
        ]
    floor = (
        float("-inf") if read_in is None else max(read_in) if read_in else float("inf")
    )
    t.approved = None
    if t.need and t.need["need"] in ("criteria", "interview"):
        t.approved = next(
            (
                a
                for a in reversed(t.approvals)
                if a["by"] in APPROVERS
                and a["order"] > last["order"]
                and a["ts"] >= floor
            ),
            None,
        )
    t.approvable = bool(
        t.need
        and t.need["need"] in ("criteria", "interview")
        and not t.approved
        and (read_in is None or read_in)
    )
    if t.approved:
        t.criteria_wait = False
        t.shown = (
            "your yes to the criteria is on record: the task's session starts its build"
            if t.approved["by"] == "owner"
            else (
                "the criteria were approved without you, as the task runs alone: "
                "the task's session starts its build"
            )
        )
    # the owner's help on the breaker that holds the task is on record: it waits for
    # Lem's start of its lead
    held = (
        t.decisions.get(t.need["number"])
        if t.need and t.need["need"] == "breaker"
        else None
    )
    t.helped = (
        held
        if held
        and held.kind == "breaker"
        and held.state == "helped"
        and t.status == "held"
        else None
    )
    if t.helped:
        t.shown = (
            f"your help on breaker {t.helped.id} is on record: the task's session "
            "starts its build again"
        )
    t.waits_after = t.status == "queued" and waits_for_task(last)
    t.merge_wait = merge_wait(t)
    t.base_red = t.status == "blocked" and BASE_RED in [
        line.strip() for line in lines_of(last)
    ]
    t.failed_seat = (
        next(
            (
                found[1]
                for found in map(
                    FAILED_SEAT.fullmatch, (line.strip() for line in lines_of(last))
                )
                if found
            ),
            None,
        )
        if t.status == "blocked"
        else None
    )
    # who acts on a held task's criteria: while Lem writes them or the personas read
    # them, it waits for nothing of the owner's; and while it runs without him, Lem
    # settles its need without him
    t.turn, t.reading = (
        turn_of(t, last)
        if t.status == "held" and not t.approved and not t.helped and not t.breaker
        else (None, None)
    )
    t.goes_on = goes_on_of(t, last, away=away) if t.turn else None
    t.for_owner = (
        bool(t.breaker)
        or (t.turn in OWNER_TURNS and not t.goes_on)
        or t.merge_wait == "owner"
        or (t.status == "planned" and bool(re.search(r"\bowner\b", t.text)))
        or (t.status == "blocked" and not t.base_red)
    )
    interview = bool(t.need and t.need["need"] == "interview")
    if t.goes_on:
        t.info = {
            "actor": "lem",
            "who": "Lem",
            "label": "Lem goes on without you",
            "icon": "play",
            "live": True,
        }
        t.shown = GOES_ON[t.goes_on]
    elif t.reading:
        t.info = {
            "actor": "quiet",
            "who": "The agent" if t.reading.get("by") == "lead" else "Lem",
            "label": "The personas read the criteria",
            "icon": "users",
            "live": True,
        }
        t.shown = "nothing waits for you until their read is in"
    elif t.turn == "writes":
        t.info = {
            "actor": "lem",
            "who": "Lem",
            "label": "Lem writes the criteria",
            "icon": "file",
            "live": True,
        }
        t.shown = WRITES_SAYS
    elif t.turn == "skip" and interview:
        t.shown = SKIP_SAYS
    elif t.turn == "yes" and interview:
        t.shown = "the criteria wait for your yes"
    if t.merge_wait in MERGE_WAITS:
        t.info = dict(MERGE_WAITS[t.merge_wait])
    if t.approved and not t.for_owner:
        t.info = {
            "actor": "lem",
            "who": "Lem",
            "label": "Approved",
            "icon": "check",
            "live": False,
        }
    if t.helped and not t.for_owner:
        t.info = {
            "actor": "lem",
            "who": "Lem",
            "label": "Helped",
            "icon": "check",
            "live": False,
        }
    if t.for_owner and t.info["actor"] != "you":
        t.info = {**t.info, "actor": "you", "who": "You"}
    t.investigating = investigates(last)
    if t.investigating and not t.for_owner:
        t.info = {
            **t.info,
            "who": "The investigator",
            "label": "Investigating",
            "icon": "eye",
        }
    # a landing whose run of the checks was stopped, red or refused, and that has not
    # gone on since, is Lem's: it waits for the owner's word after a stop, and starts a
    # builder that repairs it after the others
    ended = (
        t.checks_end
        if t.status == "landing"
        and not t.for_owner
        and t.checks_end
        and t.checks_end.get("result") != "passed"
        else None
    )
    t.checks_stop = ended
    if ended:
        end = checks_end(ended.get("result"))
        stopped = ended.get("result") == "stopped"
        t.info = {
            "actor": "lem",
            "who": "Lem",
            "label": end["label"],
            "icon": "x" if stopped else "alert",
            "live": False,
        }
        said = say_of(ended) or (
            "the checks were stopped; the landing waits for your word"
            if stopped
            else f"{end['head'].lower()}; a builder repairs it, nothing for you"
        )
        t.shown = (
            (
                f"{said}. In the task's session, /lem land starts them again and /lem "
                f"drop {t.slug} drops the task"
            )
            if stopped
            else said
        )
    if t.release_stop and not t.closed:
        # a task two releases back: nothing of it goes on until the owner drops it, so
        # it is his, blocked, with the stop's message; its status stays the one of its
        # state, which open_prs and land.py read. A breaker of it waits for nobody: its
        # help, park or drop would stop in the guard (`t.stopped` keeps its document)
        t.for_owner, t.approvable, t.checks_stop, t.waits = True, False, None, None
        t.breaker = None
        t.info = {**STATUS["blocked"], "actor": "you", "who": "You"}
        t.shown, t.more = t.release_stop["say"], []
    t.approvable_events = t.approvable
    rank = (
        "blocked"
        if t.release_stop and not t.closed
        else "breaker"
        if t.breaker
        else t.status
    )
    t.owner_rank = OWNER_ORDER.index(rank) if rank in OWNER_ORDER else -1
    # a parked task stands in no column of who acts: nobody does, and it has a place of
    # its own; an open task whose merge agent reads it, or whose merge the server runs,
    # stands under the checks and review
    t.lane = (
        "you"
        if t.for_owner
        else "done"
        if t.closed
        else PARKED
        if t.status == PARKED
        else "checks"
        if t.status in ("ready", "landing", "open")
        else "build"
    )
    t.segments = []
    for k, b in enumerate(t.blocks):
        end_ = (
            t.blocks[k + 1]["ts"]
            if k + 1 < len(t.blocks)
            else (b["ts"] if t.closed else now)
        )
        prev = t.segments[-1] if t.segments else None
        if prev and prev["status"] == b["status"]:
            prev["end"] = end_
        else:
            t.segments.append(
                {
                    "status": b["status"],
                    "start": b.get("since", b["ts"]),
                    "end": end_,
                    "open": k == len(t.blocks) - 1 and not t.closed,
                }
            )
    # where the task got to: the newest status that is a step forward
    t.reached = next(
        (
            b["status"]
            for b in reversed(t.blocks)
            if b["status"] not in ("held", "blocked")
        ),
        t.status,
    )
    t.investigated = (
        any(investigates(b) for b in t.blocks) or t.investigation is not None
    )
    t.plan_committed = any(
        b["status"] == "planned"
        or re.search(r"\bplan committed\b", " ".join(lines_of(b)))
        for b in t.blocks
    )
    t.gate_bad = sum(1 for g in t.gates if g["exit"] != 0)


# What an `open` task shows while nothing of it waits for the owner (`merge_wait`).
MERGE_WAITS = {
    "reads": {
        "actor": "gate",
        "who": "The merge agent",
        "label": "The merge agent reads it",
        "icon": "eye",
        "live": True,
    },
    "merges": {
        "actor": "gate",
        "who": "Lem",
        "label": "Lem merges it",
        "icon": "branch",
        "live": True,
    },
    "relands": {
        "actor": "gate",
        "who": "Lem",
        "label": "Lem lands it again",
        "icon": "play",
        "live": True,
    },
}


def merge_wait(t: Task) -> str | None:  # noqa: PLR0911 - over the limit before the limit was set
    """Who the merge of an `open` task waits for, None for any other task. "reads": the
    merge agent, since no review of the tip Lem proposed last is written (a review of an
    older tip counts for none; one that `propose` carried onto this tip is its
    `merge.review` too), or since Lem refused the merge because the base moved
    (`merge.refused` with `kind: base`) and no read of that tip said `another round`:
    the task's session starts a fresh merge agent, which reads what moved. "merges": the
    board's server, since the review says `merge`, calls nobody and no merge of that tip
    was refused, or the owner's merge stands for that tip (`merge.stands`, or before
    that line the mark of the read that answered his refusal, `Task.stood`); a read
    whose call on the moved base is `safe`, or a read on the checks' own base after a
    revert, answers Lem's refusal (`answers_refusal`). "relands": the task's session,
    since a read of that tip said `another round` of the moved base, and the session
    lands it again, until the next proposal. "owner": the owner, for a review that
    calls him, any other refused merge, and an open task with no proposal on record.
    Only "owner" is a row of "Waits for you". The owner's own merge on the task's page
    is offered in "owner", and in "reads" and "merges" while no merge of his stands
    (`owner_stands`, `acts_of`): never in "relands", where a press meets the base
    refusal that only the new landing answers and is refused again."""
    if t.status != "open":
        return None
    if not t.proposal:
        return "owner"
    tip = t.proposal.get("tip")

    def same(of: object) -> bool:
        return same_tip(tip, of)

    # the events since the proposal, the newest last: a read of the moved base and a
    # merge of the owner's that stands are read there
    since = t.events[t.proposal["order"] :]
    again = any(
        e.get("event") == "merge.review"
        and e.get("base_call") == "another round"
        and same(e.get("tip"))
        for e in since
    )
    if t.refused:
        if t.refused.get("from") == "lem" and t.refused.get("kind") == "base":
            return "relands" if again else "reads"
        return "owner"
    r = t.merge_review
    if r and same(r.get("tip")) and r.get("base_call") == "another round":
        return "relands"
    # his merge stands by `merge.stands`, or, before that line, by the read that
    # answered his refusal (`Task.stood`), as `stands_span` reads it
    if same(t.stood) or any(
        e.get("event") == "merge.stands" and same(e.get("tip")) for e in since
    ):
        return "merges"
    if not r or (tip and r.get("tip") and not same(r.get("tip"))):
        return "reads"
    return "merges" if r.get("verdict") == "merge" and not r.get("calls") else "owner"


# What the note of the owner's merge says while it stands, by its span (`stands_span`):
# the merge agent reads the moved base, or the board's server runs his merge.
STANDS_SAID: dict[object, str] = {
    "reads": (
        "Your merge stands. It goes through when the merge agent’s read of "
        "the new base says safe."
    ),
    "merges": "Your merge stands. Lem merges it now.",
}


def stands_span(t: Task) -> str | None:
    """Where the owner's own merge of the tip Lem proposed last stands, None while it
    does not: "reads" while Lem's refusal of it because the base moved (`merge.refused`,
    `by: owner`, `from: lem`, `kind: base`) is the newest, for that tip, and no read of
    that tip said `another round`, so the merge agent reads what moved and his merge
    goes through on a read that says `safe`; "merges" while no refusal stands, the
    newest review of that tip does not say `another round`, and his merge stands for
    that tip, by `merge.stands` since the proposal (a safe read, or `propose` after a
    new landing) or by the read that answered his refusal (`Task.stood`, before its
    `merge.stands` line), and no merge of it started since (`merge.start`), so the
    board's server is about to run it. Once a try starts, the server's own merge guards
    a second press (`NOTES.merging` in serve.py), and a try that ends with no refusal on
    record offers his Merge again, with land.py's line on a press. A refusal of the
    merge agent's merge is no word of his, and GitHub's refusal of his standing merge
    waits for him: neither stands."""
    if t.status != "open" or not t.proposal:
        return None
    tip = t.proposal.get("tip")
    since = t.events[t.proposal["order"] :]
    again = any(
        e.get("event") == "merge.review"
        and e.get("base_call") == "another round"
        and same_tip(tip, e.get("tip"))
        for e in since
    )
    r = t.refused
    if r:
        his = (
            r.get("by") == "owner"
            and r.get("from") == "lem"
            and r.get("kind") == "base"
            and same_tip(tip, r.get("tip"))
        )
        return "reads" if his and not again else None
    review = t.merge_review
    if (
        review
        and same_tip(tip, review.get("tip"))
        and review.get("base_call") == "another round"
    ):
        return None
    if not (
        same_tip(tip, t.stood)
        or any(
            e.get("event") == "merge.stands" and same_tip(tip, e.get("tip"))
            for e in since
        )
    ):
        return None
    # the span ends at the first try of a merge (`merge.start`) after it began: after
    # the newest `merge.stands` of that tip, or, before that line, after the refusal the
    # read answered
    began = max(
        (
            i
            for i, e in enumerate(since)
            if e.get("event") == "merge.refused"
            or (e.get("event") == "merge.stands" and same_tip(tip, e.get("tip")))
        ),
        default=-1,
    )
    return (
        None
        if any(e.get("event") == "merge.start" for e in since[began + 1 :])
        else "merges"
    )


def owner_stands(t: Task, tip: object = None) -> bool:
    """Whether the owner's own merge stands (`stands_span`), and, given TIP, whether it
    stands for that commit, the one a note of his press was for: the one definition the
    board's Merge button, the note of his merge and the server's guard against a second
    press read."""
    span = stands_span(t)
    return span is not None and (
        tip is None or same_tip(tip, (t.proposal or {}).get("tip"))
    )


def stands_said(t: Task, tip: object = None, seen: dict | None = None) -> str | None:
    """The sentence of the owner's merge while it stands (`owner_stands`, for TIP when
    given), in the span that holds now (STANDS_SAID); None while it does not stand, and
    while the forge calls the pull request conflicting (`conflicts`, over SEEN, the
    board server's last look), where the conflict's own text says what comes next."""
    return (
        STANDS_SAID[stands_span(t)]
        if owner_stands(t, tip) and not conflicts(t, seen)
        else None
    )


def derive(  # noqa: C901 - over the limit before the limit was set
    events: list[dict], owner: list[dict], now: int, *, meta: dict | None = None
) -> Model:
    """The model of a workspace: each task from its events, in the order of its first
    event, and the lists every page reads. `owner` is the records of the owner's mark,
    oldest first; `meta` the repository's facts (`board.meta_of`)."""
    tasks: dict[str, Task] = {}
    said = owner[-1] if owner else None
    away = (
        {"since": at(said.get("ts")), "words": said.get("words") or ""}
        if said and said.get("away")
        else None
    )
    owners = [{"ts": at(o.get("ts")), "away": o.get("away") is True} for o in owner]
    for e in events:
        slug = e.get("task")
        if not slug:
            continue
        ts = at(e.get("ts"))
        if ts is None:
            continue
        t = tasks.get(slug)
        if t is None:
            t = tasks[slug] = Task(slug=slug, title=title_of(slug))
        t.events.append(e)
        fold(t, e, ts)
    for t in tasks.values():
        if not t.blocks and t.opened:
            # a task whose session opened and wrote no state yet is on the board from
            # its first minute, as NEW
            t.blocks.append(
                {
                    "ts": t.opened["ts"],
                    "order": t.opened["order"],
                    "status": NEW,
                    "text": NEW_TEXT,
                    "lines": [],
                }
            )
    listed = [t for t in tasks.values() if t.blocks]
    for t in listed:
        settle(t, now, away=away is not None)

    def by(status: str) -> list:
        return sorted((t for t in listed if t.status == status), key=lambda t: t.since)

    today = local(now).date()
    m = Model(
        now=now,
        tasks=listed,
        away=away,
        owners=owners,
        proposed=by("open"),
        building=by("building"),
        queued=by("queued"),
        ready=by("ready"),
        landing=by("landing"),
        parked=[t for t in by(PARKED) if is_parked(t)],
        for_owner=[],
        blocked=sorted(
            (
                t
                for t in listed
                if t.status == "blocked" or (t.release_stop and not t.closed)
            ),
            key=lambda t: t.since,
        ),
        landed_today=[
            t for t in listed if t.status == "landed" and local(t.since).date() == today
        ],
        unknown=[t for t in listed if t.status not in STATUS],
        lane={},
        by_slug=tasks,
        events=events,
        meta=meta or {},
    )
    # a task queued after a dropped task waits for his word, which only the other task's
    # status tells: it is his on every view, as its row of "Waits for you" says
    for t in listed:
        if after_dropped(t, m):
            t.dropped_after, t.for_owner, t.lane, t.owner_rank = (
                after_of(t),
                True,
                "you",
                OWNER_ORDER.index("queued"),
            )
            t.info = {**t.info, "actor": "you", "who": "You"}
    sort_lists(m)
    return m


def sort_lists(m: Model) -> None:
    """The lists of who acts, from each task's own `for_owner` and `lane`: the owner's,
    in the order of what presses most, and each column of the kanban."""
    m.for_owner = sorted(
        (t for t in m.tasks if t.for_owner), key=lambda t: (t.owner_rank, t.since)
    )
    m.lane = {
        lane["key"]: lanes_sorted(
            lane["key"], [t for t in m.tasks if t.lane == lane["key"]]
        )
        for lane in LANES
    }


# What a held task of the owner's shows while its session's newest turn runs
# (`put_sessions`): the session works on what he said, and nothing waits for him until
# that turn ends.
WORKS_INFO = {
    "actor": "lem",
    "who": "The task's session",
    "label": "Works on your answer",
    "icon": "play",
    "live": True,
}
WORKS_SAYS = "it waits for you again when the session's turn ends"


def works_of(t: Task, m: Model) -> bool:
    """Whether a held task of the owner's is Lem's work now: its session lives with an
    agent in its pane (`live_of`) and that session's newest turn runs (`turn` "runs",
    lem_signs). A task with no session facts, a session that is not live, and a turn
    that ended or that Lem cannot read stay the owner's. A breaker's held task follows
    the same rule: while its session works on his help, nothing of it waits. A held task
    two releases back (RELEASE_STOP) stays the owner's, blocked: every command of its
    session stops, so no turn of it works on his answer. A task that is Lem's work
    already (`t.works`) was the owner's in what `settle` gave it."""
    if (
        t.status != "held"
        or not (t.for_owner or t.works)
        or m.sessions is None
        or (t.release_stop and not t.closed)
    ):
        return False
    f = m.sessions.get(t.slug) or {}
    return f.get("live") is True and f.get("agent") is True and f.get("turn") == "runs"


# One put of the sessions at a time (`put_sessions`): the board server's request
# threads, its forge thread, its Inbox thread and its push watcher each put them on the
# one model the Reader keeps
SESSIONS_LOCK = threading.Lock()


def put_sessions(m: Model, sessions: dict | None) -> None:
    """Put what `lem session list` said of the task sessions (`sessions_of`, or None
    while nothing is known) on a model, and with it who acts on each held task: one
    whose session's turn runs (`works_of`) is Lem's work, with no row of "Waits for you"
    (`waits_of`), WORKS_INFO, and its card under Lem's work; one whose turn ended gets
    back what `settle` gave it. The board server sets the sessions again on a model it
    keeps (`Reader.current`), from more than one thread, so the puts take SESSIONS_LOCK
    in turn, and a task changes only when who acts on it changes: the same sessions give
    the same model however often they are put. Every place that sets `Model.sessions`
    calls it: serve.py, `lem project waiting` and the guard of a stopped session."""
    with SESSIONS_LOCK:
        m.sessions = sessions
        changed = False
        for t in m.tasks:
            works = works_of(t, m)
            if works == t.works:
                continue
            if works:
                t.settled = {
                    "for_owner": t.for_owner,
                    "info": dict(t.info),
                    "shown": t.shown,
                    "lane": t.lane,
                }
                t.for_owner, t.info, t.shown, t.lane = (
                    False,
                    dict(WORKS_INFO),
                    WORKS_SAYS,
                    "build",
                )
            elif t.settled is not None:
                t.for_owner, t.info, t.shown, t.lane = (
                    t.settled["for_owner"],
                    dict(t.settled["info"]),
                    t.settled["shown"],
                    t.settled["lane"],
                )
                t.settled = None
            t.works = works
            changed = True
        if changed:
            sort_lists(m)


def own_turn_unread(sessions: dict | None, caller: str | None) -> dict | None:
    """The task sessions as the session that asks for them reads them (CALLER, its own
    agterm session id, or None outside agterm): it asks inside its own turn, which then
    always runs, so the turn of its own entry is one Lem cannot tell (None), and the
    task it holds keeps its row (`works_of`). The wake of a breaker's session reads its
    row in `lem project waiting` to put up its card."""
    if not sessions or not caller:
        return sessions
    return {
        slug: {**f, "turn": None} if f.get("session") == caller else f
        for slug, f in sessions.items()
    }


def lanes_sorted(key: str, tasks: list) -> list:
    """A column's tasks in the board's order: the one that waited longest first, except
    where the newest is the news (Done); in "Waits for you" the most pressing first; a
    landing on top of the checks."""
    order = lambda t: STATUS_ORDER.index(t.status) if t.status in STATUS else -1  # noqa: E731
    if key == "done":
        return sorted(tasks, key=lambda t: -t.since)
    tasks = sorted(tasks, key=lambda t: (order(t), t.since))
    if key == "you":
        return sorted(tasks, key=lambda t: (t.owner_rank, t.since))
    if key == "checks":
        return sorted(
            tasks,
            key=lambda t: (
                t.status != "landing",
                0 if t.status == "landing" else t.since,
            ),
        )
    return tasks


def done_older(m: Model) -> list:
    """The ended tasks Done draws no card for: those after its newest `DONE_SHOWN`, the
    newest first."""
    return m.lane["done"][DONE_SHOWN:]


# ---- the backlog's items and the search over every card ----

# The backlog's groups, from each item's own `worth`: every item of the backlog folder,
# and the reviewer's items it decided against (`refuted`); its other items have a group
# of their own (`reviewer_items`).
BY_WORTH: list[dict[str, Any]] = [
    {"key": "yes", "name": "Worth doing", "actor": "gate"},
    {"key": "later", "name": "Later", "actor": "you"},
    {"key": "unset", "name": "No verdict in the item", "actor": "quiet"},
    {"key": "no", "name": "Decided against", "actor": "quiet", "recessive": True},
]
# The columns whose tasks have not ended, in the kanban's order: the search lists
# them first.
OPEN_LANES = ("you", "build", "checks")


def worth_of(it: dict) -> str:
    return it.get("worth") if it.get("worth") in ("yes", "later", "no") else "unset"


def refuted(it: dict) -> bool:
    """A reviewer's item that says `worth: no`: a proposal the reviewer decided against,
    kept so that no later night or retro raises it again. It waits for nobody, so the
    Backlog key does not count it."""
    return bool(it.get("reviewer")) and worth_of(it) == "no"


def worth_items(items: list[dict], key: str) -> list[dict]:
    """The items of a backlog's read in the group of BY_WORTH whose key is KEY, in the
    order of the read: the backlog folder's, and in "Decided against" the reviewer's
    refuted ones (`refuted`) too."""
    return [
        it
        for it in items
        if (not it.get("reviewer") or refuted(it)) and worth_of(it) == key
    ]


def search_rows(m: Model, backlog: dict | None) -> list[dict]:
    """One row for each card of the workspace, in the order the search lists them with
    nothing typed: the tasks of the columns that have not ended, each column in the
    kanban's order; the parked tasks; every ended task, the newest first, also those
    Done draws no card for; then the reviewer's items, the undecided ones first
    (`reviewer_items`); then the other backlog items by their worth, the reviewer's
    refuted ones among those of "Decided against" (`worth_items`). Each row has its
    title, whether it is a task that has not ended (`open`), the color of its place
    (`actor`), its chip: `COLUMN · STATUS`, `parked`, `STATUS DAY` for an ended task
    (the day it ended, on this machine's clock, as `stamp` reads it),
    `Backlog · undecided` or `Backlog · held by SLUG` for a reviewer's item that is not
    refuted, `Backlog · worth: WORTH` for the others; and an item's `slug` is its `key`.
    Only this model and this backlog come in, so no other workspace and no joined
    machine does."""

    def task_row(t: Task, *, open_: bool, actor: str, chip: str) -> dict:
        return {
            "kind": "task",
            "slug": t.slug,
            "title": t.title,
            "open": open_,
            "actor": actor,
            "chip": chip,
        }

    rows = []
    for key in OPEN_LANES:
        lane = LANE[key]
        rows += [
            task_row(
                t, open_=True, actor=lane["actor"], chip=f"{lane['title']} · {t.status}"
            )
            for t in m.lane[key]
        ]
    rows += [
        task_row(t, open_=True, actor=STATUS[PARKED]["actor"], chip=PARKED)
        for t in m.parked
    ]
    rows += [
        task_row(
            t,
            open_=False,
            actor=LANE["done"]["actor"],
            chip=f"{t.status} {local(t.since).date().isoformat()}",
        )
        for t in m.lane["done"]
    ]
    items = (backlog or {}).get("items") or []
    rows += [
        {
            "kind": "item",
            "slug": it["key"],
            "title": flat(it.get("title") or it["slug"]),
            "open": False,
            "actor": "lead" if it.get("held") else "you",
            "chip": f"Backlog · held by {it['held']['task']}"
            if it.get("held")
            else "Backlog · undecided",
        }
        for it in reviewer_items(items)
    ]
    for g in BY_WORTH:
        rows += [
            {
                "kind": "item",
                "slug": it["key"],
                "title": flat(it.get("title") or it["slug"]),
                "open": False,
                "actor": g["actor"],
                "chip": f"Backlog · worth: {g['key']}",
            }
            for it in worth_items(items, g["key"])
        ]
    return rows


def reviewer_items(items: list[dict]) -> list[dict]:
    """The reviewer's items of a backlog's read (`board.backlog`) that are not refuted
    (`refuted`), the undecided ones first, each part in the order of the read: a refuted
    one is in "Decided against"."""
    mine = [it for it in items if it.get("reviewer") and not refuted(it)]
    return [it for it in mine if not it.get("held")] + [
        it for it in mine if it.get("held")
    ]


def undecided(backlog: dict | None) -> int | None:
    """How many of the reviewer's items no task holds, the count on the "Backlog" key;
    None with no read. A refuted item (`worth: no`) waits for nobody and is
    never counted."""
    return (
        None
        if backlog is None
        else sum(
            1 for it in reviewer_items(backlog.get("items") or []) if not it.get("held")
        )
    )


# ---- what the views say ----

# Why the checks wait behind the first in the machine's line, by the `why` of its
# `gate.wait` (land.py).
BEHIND_WHY: dict[object, str] = {
    "wanted": "which another task waits for",
    "longer": "which waits longer",
    "first": "which is first in the line",
}


def behind_said(w: dict) -> str:
    """The landing that a run waits behind, and why that one goes first: "OTHER, which
    waits longer", with "of REPO" after OTHER when it is of another repository
    (`behind_repo`, the folder's name)."""
    repo = Path(str(w["behind_repo"])).name if w.get("behind_repo") else ""
    return (
        f"{w['behind']}{' of ' + repo if repo else ''}, "
        f"{BEHIND_WHY.get(w.get('why'), BEHIND_WHY['first'])}"
    )


def waits_say(w: dict) -> str:
    if w["event"] == "merge.wait":
        return f"Waits for the merge of {w.get('after') or 'another task'}"
    if w.get("behind"):
        return f"Its checks wait behind {behind_said(w)}"
    return (
        f"Its checks wait a minute after the checks of {w['after']} started"
        if w.get("after")
        else f"Waits for the load: {w.get('load')}, starts below {w.get('start')}"
    )


def waits_now(t: Task) -> dict | None:
    return t.waits if t.waits and t.status in ("landing", "open") else None


def card_line(t: Task, lane: dict) -> str:
    """The state line of a card, in words: the lane's title is not said again."""
    if waits := waits_now(t):
        return waits_say(waits)
    if t.status == "answered" and t.investigation:
        call = CALLS.get(t.investigation["call"], {}).get(
            "card", t.investigation["call"]
        )
        return f"{call}: {t.investigation['line']}"
    # a landing's step that started after its newest state block: the words of the head
    # of its page (`now_head`), since the state's own text ("the checks start") is older
    # than the step that runs
    if (
        t.status == "landing"
        and t.landing_step
        and not t.checks_stop
        and not t.release_stop
    ):
        return step_runs(t.landing_step)
    if not t.shown:
        return t.info["label"]
    said_ = PULL.sub(r"#\1", t.shown)
    # the label is not said again where the line says it first (WRITES_SAYS)
    label = (
        ""
        if t.info["label"] == lane["title"]
        or t.checks_stop
        or said_.lower().startswith(t.info["label"].lower())
        else t.info["label"]
    )
    return f"{label}: {said_}" if label else cap(said_)


def advisers_of(d: Decision) -> list:
    return d.advisers if d.advisers is not None else list(EXPERTS)


def stop_words(d: Decision) -> str:
    """Why a breaker stopped the build, in the page's words: its cause, and the kind of
    a step no "no" undoes."""
    said = BREAKS.get(d.stop, str(d.stop or "no cause on record"))
    return (
        f"{said}: {IRREVERSIBLE.get(d.irreversible, d.irreversible)}"
        if d.stop == "irreversible" and d.irreversible
        else said
    )


def is_parked(t: Task) -> bool:
    """Whether the task is parked and its park is its way on: never a task two releases
    back (RELEASE_STOP), whose way on is the stop's message and which `lem project
    resume` refuses to bring back, so that it stands in "Waits for you" alone."""
    return t.status == PARKED and t.release_stop is None


def parked_of(t: Task) -> dict | None:
    """A parked task: since when, why (the parked block's first line, in the owner's
    words), and the command that brings it back; None for a task that is not parked, or
    whose park is no way on (`is_parked`)."""
    if not is_parked(t):
        return None
    return {"since": t.since, "why": t.text, "resume": f"/lem resume {t.slug}"}


def board_yes_no(t: Task) -> str:
    """How the owner answers the standard track's criteria on the board: Yes, or No with
    his words, which changes them and asks again (`answer_row`); a task begun on an
    older release keeps the one Approve."""
    if t.behind:
        return "approve them there."
    return (
        "Yes, or No with your words, and Lem changes them and asks for your yes again."
    )


def answer_of(t: Task) -> str:  # noqa: C901, PLR0911, PLR0912 - over the limit before the limit was set
    """Where the owner answers what waits for him: in the task's own session, or on the
    board; for a task queued after a dropped task, which no session runs, in any
    Lem session; for a task two releases back, the stop's message, whatever its
    status: the board offers no act on it (`acts_of`)."""
    if t.release_stop and not t.closed:
        return t.release_stop["say"]
    if t.dropped_after:
        start, drop = f"start {t.slug} now", f"/lem drop {t.slug}"
        return (
            f"It waited for {t.dropped_after}, which was dropped, so the result it "
            f"waited for never came. Type “{start}” to start it without that result, "
            f"or {drop} to end it, in any Lem session of this repository."
        )
    if t.breaker is not None:
        return (
            "Read its document, first on the task’s Overview. Then help, park or drop "
            "the task on this board, or help in the task’s session. Or type /lem park "
            f"{t.slug} to put the task aside, or /lem drop {t.slug} to end it."
        )
    if t.status == "open":
        return "Merge the pull request on GitHub or on this board."
    if t.need and t.need["need"] == "interview" and t.turn == "skip":
        return (
            "Lem asks whether to skip the personas’ read of the criteria, since each "
            "names only you. Answer Yes or No on this board, "
            "or y or n in the task’s session."
        )
    if t.need and t.need["need"] == "interview" and t.turn == "yes":
        return (
            "The criteria wait for your yes in the task’s session. Approve or change "
            f"them there, or on this board: {board_yes_no(t)}"
        )
    if t.need and t.need["need"] == "interview":
        return (
            "The interview runs in the task’s session. Answer its questions there, and "
            "approve the criteria at its end."
        )
    if t.criteria_wait and t.text == FAST_CRITERION:
        return (
            "The one criterion of a request someone else wrote waits for your yes. "
            "Answer Yes or No under its text on this board, or y or n in the task’s "
            "session. No needs your words: what the criterion should say."
        )
    if t.criteria_wait and t.text == CHANGED_CRITERIA:
        return (
            "The criteria changed from your note, and wait for your yes again, each "
            "changed one with its text before beside it. Approve or change them in the "
            f"task’s session, or on this board: {board_yes_no(t)}"
        )
    if t.criteria_wait and t.reads and t.reads[-1]["answered"] == 0:
        return (
            "No persona answered the read of the acceptance criteria. "
            "Approve or change them in the task’s session, "
            f"or on this board: {board_yes_no(t)}"
        )
    if t.criteria_wait:
        return (
            "The acceptance criteria, with the personas’ read on top, wait in the "
            "task’s session. Approve or change them there, "
            f"or on this board: {board_yes_no(t)}"
        )
    if t.status == "held":
        return (
            f"It waits on what its state says: “{t.shown}”. "
            "The task’s session says what to do."
        )
    if t.status == "planned":
        return (
            "Read the plan, then build it or drop the task on this board, "
            "or tell the task’s session."
        )
    # a blocked task's session stopped and waits for his word, unless only the base's
    # repair is awaited
    return (
        blocked_where(t)
        if t.status == "blocked" and not t.base_red
        else (
            "Tell the task’s session to build it, "
            f"or type /lem drop {t.slug} to end it."
        )
    )


def blocked_where(t: Task) -> str:
    """Where the owner answers a task its session stopped with something it cannot
    settle alone (`blocked`): in that session, which waits for his word."""
    return (
        "The task’s session stopped on something it cannot settle alone: "
        f"“{t.shown or t.text}”. Tell it what to do in the task’s session, or "
        f"type /lem drop {t.slug} there to end the task."
    )


def after_of(t: Task) -> str | None:
    """The task a queued task waits for (its `after:` line), or None."""
    for line in lines_of(t.blocks[-1]):
        found = re.fullmatch(r"after: ([a-z0-9-]+)", line)
        if found:
            return found[1]
    return None


def after_ended(t: Task, m: Model) -> bool:
    """A queued task whose `after:` task landed or was answered: nothing holds it back
    any more. A dropped one is no such end (`after_dropped`): its result never came."""
    after = after_of(t)
    done = m.by_slug.get(after) if after else None
    return (
        t.status == "queued"
        and done is not None
        and bool(done.blocks)
        and done.status in ("landed", "answered")
    )


def after_dropped(t: Task, m: Model) -> bool:
    """A queued task whose `after:` task was dropped: it stays queued, and the owner
    says whether it starts without that task's result or is dropped too."""
    after = after_of(t)
    done = m.by_slug.get(after) if after else None
    return (
        t.status == "queued"
        and done is not None
        and bool(done.blocks)
        and done.status == "dropped"
    )


def session_entries(text: str) -> dict[str, dict]:
    """What `lem session list` printed, by task: a JSON list of entries, each with its
    `task` and the facts the board reads (`live`, `agent`, `unanswered`, `session`,
    `name`, and the signs of work `sign`, `shell`, `signs` and `turn`); a list under
    `sessions` or `tasks` is taken too. ValueError for anything else."""
    data = json.loads(text)
    if isinstance(data, dict):
        data = data.get("sessions", data.get("tasks"))
    if not isinstance(data, list):
        raise ValueError("`lem session list` printed no list of the tasks' sessions")
    return {
        str(e["task"]): {
            k: e.get(k)
            for k in (
                "live",
                "agent",
                "unanswered",
                "unheard",
                "session",
                "name",
                "sign",
                "shell",
                "signs",
                "turn",
            )
        }
        for e in data
        if isinstance(e, dict) and e.get("task")
    }


def sessions_of(entries: dict[str, dict], kept: set[str]) -> dict[str, dict]:
    """`Model.sessions` from what `lem session list` said (`session_entries`) and the
    tasks that ended and whose worktree is still there (KEPT): the one form the server
    and `lem project waiting` give the model."""
    return {
        slug: {**entries.get(slug, {}), "worktree": slug in kept}
        for slug in {*entries, *kept}
    }


# The board server's last look at the forge, in the state folder: `{"looked": ISO time,
# "seen": {SLUG: {"mergeable", "head"}}}`, which the server writes at each look
# (serve.py `forge_once`) and the board's model and `lem project waiting` read
# (`Model.seen`), so that a page and the terminal say the same.
FORGE_LOOK = "forge.json"


def forge_look(state: Path) -> dict | None:
    """The forge's last look as the server wrote it, or None when there is none or it
    does not read."""
    try:
        found = json.loads((state / FORGE_LOOK).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return (
        found
        if isinstance(found, dict) and isinstance(found.get("seen"), dict)
        else None
    )


# The board server's record of the owner's Inbox, in the state folder
# (`lem_inbox.RECORD`), which only its Inbox thread writes (`lem_inbox.Watcher`): the
# door's last look (`running`, `tailnet_url`, `why`), the last call that failed
# (`problem`), and each thing it sent (`sent`: the row's `key`, the `task`, its `kind`,
# `form` and `asks`, and once the Inbox answered, `message_id` and `thread_id`).
INBOX_LOOK = "inbox.json"
# Why no question went to the Inbox, in the page's words, for each `why` of the
# door (`lem_inbox.WHYS`).
INBOX_WHY = {
    "not installed": (
        "The Inbox is not installed on this Mac, so no question went there."
    ),
    "not running": "The Inbox does not run on this Mac, so no question went there.",
    "not answering": (
        "The Inbox on this Mac does not answer, so no question went there."
    ),
    "no tailnet address": (
        "The Inbox has no tailnet address, so the phone cannot open it."
    ),
    "failed": (
        "The board’s server could not ask the Inbox on this Mac, "
        "so no question went there."
    ),
}
# The same, for a task whose message went to the Inbox before its door closed: it is
# there, and the phone cannot reach it now.
INBOX_WHY_SENT = {
    "not installed": (
        "A message of this task went to the Inbox, but the Inbox is not installed on "
        "this Mac now, so the phone cannot open it."
    ),
    "not running": (
        "A message of this task went to the Inbox, but the Inbox does not run on this "
        "Mac now, so the phone cannot open it."
    ),
    "not answering": (
        "A message of this task went to the Inbox, but the Inbox on this Mac does not "
        "answer now, so the phone cannot open it."
    ),
    "no tailnet address": INBOX_WHY["no tailnet address"],
    "failed": (
        "A message of this task went to the Inbox, but the board’s server could not "
        "ask the Inbox on this Mac now, so the phone cannot open it."
    ),
}
# A thing the record keeps with no answer of the Inbox yet while a call failed: the next
# look sends it again.
INBOX_UNSENT = (
    "The board’s server could not send this to the Inbox yet; "
    "its next look tries again."
)


def inbox_look(state: Path) -> dict | None:
    """The record of the owner's Inbox as the server wrote it, with only the sent things
    that name a row; None when there is none or it does not read."""
    try:
        found = json.loads((state / INBOX_LOOK).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(found, dict):
        return None
    return {
        **found,
        "sent": [
            s
            for s in found.get("sent") or []
            if isinstance(s, dict) and isinstance(s.get("key"), str) and s["key"]
        ],
    }


def thread_link(tailnet: object, thread: object) -> str | None:
    """The address of a thread of the Inbox through its tailnet address,
    `TAILNET_URL#thread=ID` (the form `send_message` gave Lem's task sessions on
    2026-11-21); None unless the address is http or https."""
    if (
        not isinstance(tailnet, str)
        or not re.match(r"https?://[^\s/#?]+", tailnet)
        or not isinstance(thread, str)
        or not thread
    ):
        return None
    base = tailnet.split("#", 1)[0]
    base = base if re.match(r"https?://[^/]+/", base) else f"{base}/"
    return f"{base}#thread={quote(thread, safe='')}"


def inbox_of(t: Task, m: Model) -> dict | None:  # noqa: PLR0911 - over the limit before the limit was set
    """What a task's page says of the owner's Inbox, from the server's record
    (`Model.inbox`): None while his mark does not say away, while the task has no row of
    "Waits for you", and while nothing is known that changes today's line (no record, or
    nothing of the task sent yet). Else `thread`, the address of the task's thread at
    the Inbox's tailnet address, with `asks` when a question of the task went there (he
    answers in either place) or `gone` when only a note went, which no session can take
    a reply to (`lem_inbox.thing_of`: a task with no session, one whose session does not
    answer or stopped, one queued after a dropped task); or `why`, the line that says
    why there is no link. A thing counts only for a row the task has now: the merge
    review and the merge of a task are its merge's one thing."""
    if m.away is None:
        return None
    rows = [w for w in waits_of(m) if w["t"] is t]
    if not rows:
        return None
    record = m.inbox
    if not record:
        return None
    keys = {f"merge:{t.slug}" if w["kind"] == "review" else w["key"] for w in rows}
    sent = [
        s
        for s in record.get("sent") or []
        if s.get("task") == t.slug and s["key"] in keys
    ]
    door = record.get("running") is True and record.get("tailnet_url")
    there = [s for s in sent if s.get("message_id") and s.get("thread_id")]
    if not door:
        why = record.get("why")
        if not why:
            return None
        said = (
            (INBOX_WHY_SENT if there else INBOX_WHY).get(why)
            if isinstance(why, str)
            else None
        )
        went = (
            "A message of this task went to the Inbox, and"
            if there
            else "No question went to the Inbox:"
        )
        return {
            "thread": None,
            "asks": False,
            "gone": False,
            "why": said or f"{went} its last look said “{flat(why)}”.",
        }
    link = next(
        (thread_link(record["tailnet_url"], s["thread_id"]) for s in there), None
    )
    if link is None:
        unsent = any(not s.get("message_id") for s in sent) and record.get("problem")
        return (
            {"thread": None, "asks": False, "gone": False, "why": INBOX_UNSENT}
            if unsent
            else None
        )
    asks = any(s.get("form") == "question" for s in there)
    gone = not asks and any(
        s.get("kind") in ("session", "stopped", "after_dropped")
        or (s.get("asks") and s.get("form") == "note")
        for s in there
    )
    return {"thread": link, "asks": asks, "gone": gone, "why": None}


def live_of(t: Task, m: Model) -> dict | None:
    """What is known of the task's session now: `live` (its session is in agterm and an
    agent runs in it), `unanswered` (a wake-up waits in it for 10 minutes), `worktree`
    (the task's worktree is still there) and its `session`. From the server's
    `lem session list` (`Model.sessions`); in a demo workspace, which has no agterm to
    ask, from the log alone: live while its newest `session.open` has no close. None
    while nothing is known."""
    if m.sessions is not None:
        f = m.sessions.get(t.slug) or {}
        return {
            "live": f.get("live") is True and f.get("agent") is True,
            "unanswered": f.get("unanswered") is True,
            # which case of it (`lem session list`), or None from a list of the
            # release before
            "unheard": f.get("unheard") if isinstance(f.get("unheard"), dict) else None,
            "worktree": f.get("worktree") is True,
            "session": f.get("session") or t.session,
        }
    if m.meta.get("demo"):
        return {
            "live": t.session is not None,
            "unanswered": False,
            "worktree": False,
            "session": t.session,
        }
    return None


def session_need(t: Task, m: Model) -> str | None:
    """Whether the task is stuck for want of its session, so that a row of "Waits for
    you" says so: `gone` for a task whose phase needs an agent and that has no live
    session (2 minutes after its newest session opened, or after the task opened when it
    never had one), `deaf` for a live session that left a wake-up unanswered for 10
    minutes, None otherwise. An `open` task needs its session only while no merge review
    of its proposed tip is written, since the session runs the merge agent; one whose
    merge the server runs, or that waits for the owner's merge, has none: at the merge
    the server wakes or opens a session for the cleanup. A parked task has none, nor a
    queued one whose task has not ended. An ended task has one only when session.py's
    `phase_of` gives it a session (CLEANED_BY_SESSION: a merged task, or one whose pull
    request was closed, the drop GitHub's close wrote) and its worktree is still there,
    since its cleanup is what needs the session; a dropped task whose worktree is gone
    has none."""
    if t.status == PARKED:
        return None
    f = live_of(t, m)
    if f is None:
        return None
    if f["live"]:
        return "deaf" if f["unanswered"] else None
    if t.closed:
        if t.status not in CLEANED_BY_SESSION or not f["worktree"]:
            return None
        since = max(t.since, (t.opened or {}).get("ts") or 0)
    else:
        if (t.status == "open" and t.merge_wait != "reads") or (
            t.status == "queued" and not after_ended(t, m)
        ):
            return None
        since = max(t.first, (t.opened or {}).get("ts") or 0)
    return "gone" if m.now - since >= GRACE_MS else None


def opens_session(t: Task, m: Model) -> bool:
    """Whether the board offers "Open a session" for the task: nothing says that its
    session lives, or it lives and the guard of a stopped session logged its stop
    (`stopped_of`), and `lem session open` would take it, as session.py's `phase_of`
    says: not ended, except a merged or dropped task whose worktree stays
    (CLEANED_BY_SESSION); not parked; not queued behind a task that has not ended."""
    f = live_of(t, m)
    if (
        f is None
        or t.status == PARKED
        or (t.status == "queued" and not after_ended(t, m))
    ):
        return False
    if f["live"]:
        # a stop the guard logged: the session lives and does nothing, and the open goes
        # beside it
        return stopped_of(t, m) is not None
    return not t.closed or (t.status in CLEANED_BY_SESSION and f["worktree"])


# The guard of a stopped session (`stop_due`): the statuses whose session works with
# nobody at it, how long with no sign of work before Lem asks the session for its
# status, and how long it waits for an answer. The owner's words of 2026-11-22 (the task
# dead-tasks-woken-or-shown, its directions.md): "lets try 45min" and "I agree
# with 10min".
GUARDED = ("building", "ready", "landing")
QUIET_MS = 45 * 60 * 1000
ANSWER_MS = 10 * 60 * 1000
# The guard's record of a turn of a task's session that a look which read the session's
# signs saw after a status message that Lem sent while it could not read them
# (`stop_due`'s step `worked`): its `session`, and `turn`, the time of that turn.
WORKED = "session.worked"


def guarded(t: Task) -> bool:
    """Whether the guard of a stopped session watches the task: its status is in
    GUARDED, and no release stop holds it (RELEASE_STOP), whose session would wake every
    QUIET_MS into the same stop."""
    return t.status in GUARDED and t.release_stop is None


def work_event(e: dict) -> bool:
    """Whether an event of a task is work of its agent: any event but the sessions' own
    (`session.*`, the guard's steps and the hook's records among them) and `board.act`,
    the board's record of the owner's click, which `serve.py:asked_from` logs after the
    act it asked for."""
    event = str(e.get("event") or "")
    return not event.startswith("session.") and event != "board.act"


def stop_due(t: Task, m: Model) -> dict | None:  # noqa: PLR0911 - over the limit before the limit was set
    """The step of the guard of a stopped session that is due for the task now, or None:
    `{"step", "session", "from"}`, the step (`worked`, `status`, `restart` or
    `stopped`), the session it is for, and the time in ms it is due from. Only for a
    task the guard watches (`guarded`: in GUARDED, so not parked, held, queued,
    planned, blocked, open or ended, and with no release stop) whose session lives
    with an agent in its pane (`live_of`, `agent`) and in which no shell command runs
    (`shell`); never while the server has not asked (`Model.sessions` None) and never
    in a demo workspace.

    Its newest sign of work is the newest of the task's newest work event
    (`work_event`), its newest `session.open`, so that a fresh session's clock starts
    at its open, the turn of its newest WORKED record, and, when the session's signs
    read (`signs`), the session's own `sign` (its newest turn, or a subagent's). When
    they do not read, `sign` is not used, even when it holds a time: a turn with no
    live process to back it is no proof that the session works now. A WORKED record
    holds a turn that a look read while the signs read. Each of the two clocks counts
    only the status wake (`session.wake why=status`) that it sent, which `cmd_wake`
    marks `unread` when the signs do not read, so that a wake of one clock never starts
    the ANSWER_MS of the other; the wake before a stop that stands counts for both, so
    that a change of the signs gives a logged stop no second message and no second
    stop. Then:

    - `worked`, from the turn, when the signs read and show a turn at or after a status
      wake of the unread clock that the clock still counts (an unread stop after it
      stands, or the stop is still to come): the record of that turn, once, since the
      clock then counts from it. It ends the stop (`stop_stands`), so the row and the
      owner's refused "Open a session" go;
    - `status`, from that sign, QUIET_MS after it, when no status wake of its clock came
      after it;
    - with signs that read, `restart`, from that wake, ANSWER_MS after it, when no
      `session.open why=stopped` came after the task's newest work event, no stop of
      the task stands (`stop_stands`) and none stood since that event and the newest
      open (`stood_since`, a stop that a WORKED record ended): one restart for one
      stop, spent until the task's agent logs work again, and a logged stop waits for
      the owner's "Open a session";
    - `stopped`, from that wake, ANSWER_MS after it, when no `session.stopped` came
      after the wake, so that a stop is logged once: with signs that read once the
      restart is spent, a stop stands from before the wake or one stood since the
      task's newest work (an unread stop that a turn of the session passed, whose newer
      stop the owner's "Open a session" takes again), and with signs that do not read
      at once, since Lem never restarts by itself beside a session it cannot read.

    A wake in the same second as a sign counts as before it: the session that answers at
    once works."""
    if m.sessions is None or m.meta.get("demo") or not guarded(t):
        return None
    f = m.sessions.get(t.slug) or {}
    if (
        not (f.get("live") is True and f.get("agent") is True)
        or f.get("shell") is not False
    ):
        return None
    read = f.get("signs") is True
    work = next(
        (i for i in range(len(t.events) - 1, -1, -1) if work_event(t.events[i])), -1
    )
    times = [
        (t.opened or {}).get("ts") or 0,
        (at(t.events[work].get("ts")) or 0) if work >= 0 else 0,
        worked_turn(t),
    ]
    turn = (at(f.get("sign")) or 0) if read else 0
    since = max([*times, turn])
    session = f.get("session") or t.session
    # a turn read after a status message that the clock of signs that do not read still
    # counts: logged once, it ends that message's wait and the stop after it
    unread = next(
        (
            w
            for w in t.wakes
            if w.get("why") == "status" and w["unread"] and w["ts"] > max(times)
        ),
        None,
    )
    if unread is not None and turn >= unread["ts"]:
        return {"step": "worked", "session": session, "from": turn}
    stop = stop_stands(t)
    # the order of the status wake before the standing stop (`wake_before`, an index; an
    # order is index + 1)
    held = (
        wake_before(t, next(i for i, e in enumerate(t.events) if e is stop)) + 1
        if stop is not None
        else None
    )
    wake = next(
        (
            w
            for w in t.wakes
            if w.get("why") == "status"
            and w["ts"] > since
            and (w["unread"] is not read or w["order"] == held)
        ),
        None,
    )
    if wake is None:
        return (
            {"step": "status", "session": session, "from": since}
            if m.now - since >= QUIET_MS
            else None
        )
    if m.now - wake["ts"] < ANSWER_MS:
        return None
    if (
        read
        and stop is None
        and not any(
            e.get("event") == "session.open" and e.get("why") == "stopped"
            for e in t.events[work + 1 :]
        )
        and not stood_since(t, max(work + 1, (t.opened or {}).get("order") or 0))
    ):
        return {"step": "restart", "session": session, "from": wake["ts"]}
    # A stop that stands came before this wake, or is the one this wake was for: only
    # a newer wake (an unread stop that a turn of the session passed, so that the
    # readable clock sent its own message) logs one newer stop, whose open the owner's
    # click takes again (`session.guard_refusal`).
    if any(e.get("event") == "session.stopped" for e in t.events[wake["order"] :]):
        return None
    return {"step": "stopped", "session": session, "from": wake["ts"]}


def worked_turn(t: Task) -> int:
    """The time in ms of the turn that the task's newest WORKED record holds, or 0."""
    found = next((e for e in reversed(t.events) if e.get("event") == WORKED), None)
    return (at(found.get("turn")) or 0) if found else 0


def stood_since(t: Task, start: int) -> bool:
    """Whether a `session.stopped` that stood (not one a state block overtook,
    `stop_over_work`) is among the task's events from the place START on: in the run of
    work of the session that START begins, a stop of the task waited for the owner
    once, and the next one is his "Open a session" again, never a restart by itself."""
    return any(
        e.get("event") == "session.stopped" and not stop_over_work(t, e)
        for e in t.events[start:]
    )


def stop_stands(t: Task) -> dict | None:
    """The task's newest `session.stopped` while no work event (`work_event`) came after
    the newest status wake before it (`session.wake why=status`) and no `session.open`
    and no WORKED record came after it: the stop the guard logged, which waits for the
    owner's "Open a session"; else None. A work event between that wake and the stop is
    a state block the session appended in the moment the guard looked: the order of the
    log decides, and such a stop stands over nothing. A WORKED record is a turn that a
    look which read the session saw after the status message: the session answered."""
    found = next(
        (
            i
            for i in range(len(t.events) - 1, -1, -1)
            if t.events[i].get("event") == "session.stopped"
        ),
        None,
    )
    if found is None:
        return None
    wake = wake_before(t, found)
    if any(work_event(e) for e in t.events[wake + 1 :]) or any(
        e.get("event") in ("session.open", WORKED) for e in t.events[found + 1 :]
    ):
        return None
    return t.events[found]


def wake_before(t: Task, stop: int) -> int:
    """The place in `t.events` of the newest status wake (`session.wake why=status`)
    before the stop at STOP, or STOP itself when none came before it."""
    return next(
        (
            i
            for i in range(stop - 1, -1, -1)
            if t.events[i].get("event") == "session.wake"
            and t.events[i].get("why") == "status"
        ),
        stop,
    )


def stop_over_work(t: Task, e: dict) -> bool:
    """Whether the `session.stopped` record E of the task came after work of the task
    (`work_event`) that followed its status wake: the stop of a look that a state block
    overtook, which never stood (`stop_stands`), so that nothing waited for the owner
    when it was logged. E is found by identity, as `derive` keeps each record of the log
    in `t.events`; a record that is not there is no such stop."""
    stop = next((i for i, x in enumerate(t.events) if x is e), None)
    return stop is not None and any(
        work_event(x) for x in t.events[wake_before(t, stop) + 1 : stop]
    )


def restarted_before(t: Task, e: dict) -> bool:
    """Whether the guard opened a fresh session in the stopped one's place
    (`session.open why=stopped`) after the task's newest work event (`work_event`)
    before the `session.stopped` record E, found by identity as `stop_over_work` finds
    it. A readable stop comes once that restart is spent, or over a stop that already
    stood (`stop_due`), which no fresh session took the place of."""
    stop = next((i for i, x in enumerate(t.events) if x is e), None)
    for x in reversed(t.events[:stop] if stop is not None else []):
        if x.get("event") == "session.open" and x.get("why") == "stopped":
            return True
        if work_event(x):
            return False
    return False


def stopped_of(t: Task, m: Model) -> dict | None:
    """The stop that waits for the owner (`stop_stands`), while the guard watches the
    task (`guarded`) and its session still lives (`live_of`): the row `stopped` of
    "Waits for you", whose "Open a session" opens a fresh session beside it
    (`lem session open SLUG --why stopped`). None otherwise: a stopped session that is
    gone from agterm is `session_need`'s `gone`, whose open takes no stop, so the two
    rows never stand together."""
    if not guarded(t):
        return None
    f = live_of(t, m)
    if f is None or not f["live"]:
        return None
    return stop_stands(t)


def is_green(t: Task) -> bool:
    return t.proposal["green"] if t.proposal else "green" in t.blocks[-1]["lines"]


def not_green_why(t: Task) -> list:
    if t.proposal:
        return list(t.proposal["reasons"])
    return [
        re.sub(r"^not green:?\s*", "", line)
        for line in t.blocks[-1]["lines"]
        if re.match(r"^not green\b", line)
    ]


def verdict_of(t: Task) -> dict | None:
    """What the proposal said: green, or each reason it is not; None before
    a proposal."""
    if t.proposal:
        return {"green": t.proposal["green"], "reasons": list(t.proposal["reasons"])}
    lines = t.blocks[-1]["lines"]
    if not any(line == "green" or re.match(r"^not green\b", line) for line in lines):
        return None
    return {"green": is_green(t), "reasons": not_green_why(t)}


def pr_of(t: Task) -> dict | None:
    """The newest address of a pull request in the task's state lines, with its number
    and its repository; a summary's block gives the one its past named."""
    for b in reversed(t.blocks):
        if "pr" in b:
            if b["pr"]:
                return dict(b["pr"])
            continue
        for line in lines_of(b):
            found = PULL.search(line)
            if found:
                return {
                    "url": found[0],
                    "n": found[1],
                    "repo": "/".join(found[0].split("/")[3:5]),
                }
    return None


def careful_of(t: Task) -> dict | None:
    if t.missed:
        return {
            "yes": True,
            "why": t.missed["why"],
            "by": "the review called it careful, and the plan did not",
        }
    r = next((x for x in reversed(t.reviews) if isinstance(x["careful"], bool)), None)
    if r:
        return {
            "yes": r["careful"],
            "why": r["careful_why"] or "",
            "by": f"the review of round {r['round']}",
        }
    # a summarized task keeps the call its events made
    kept = (t.summary or {}).get("careful")
    return dict(kept) if isinstance(kept, dict) else None


def criteria_size(t: Task) -> str | None:
    """The size of the task's criteria, which `track_of` says as its track: from its
    newest criteria or approval, or from its summary (SUMMARY), which keeps the size its
    events gave."""
    if t.criteria and t.criteria.get("size"):
        return t.criteria["size"]
    if t.approvals:
        return t.approvals[-1].get("size")
    size = (t.summary or {}).get("size")
    return size if isinstance(size, str) and size else None


def conflicts(t: Task, seen: dict | None) -> bool:
    """The forge calls the pull request conflicting with the base, on the head Lem
    proposed last, at the board server's last look (`Model.seen`, by task)."""
    entry = (seen or {}).get(t.slug)
    entry = entry if isinstance(entry, dict) else None
    head, tip = (entry or {}).get("head"), (t.proposal or {}).get("tip")
    same = bool(head and tip) and (
        str(head).startswith(str(tip)) or str(tip).startswith(str(head))
    )
    return bool(entry) and entry.get("mergeable") == "CONFLICTING" and same


# ---- what the owner does from the board (serve.py's acts) ----

# Where the owner's word came from, as the `board.act` event keeps it (`via`): never
# his login.
VIA = {"local": "the board, on this Mac", "door": "the board, through the tailnet door"}
# Each act of the board, in the activity's words.
ACTED: dict[object, str] = {
    "approve": "You approved the criteria from the board",
    "merge": "You merged it from the board",
    "park": "You parked the task from the board",
    "session": "You opened a session of the task from the board",
    "start": "You started the task from the board",
    "answer": "You answered a card of the task’s session from the board",
}


def acts_of(t: Task, seen: dict | None) -> list[str]:
    """The acts the board offers on a task: `approve` while its criteria wait for the
    owner's yes and the yes would count (`Task.approvable`), `merge` while it is open,
    Lem does not land it again after a moved base (`merge_wait` "relands": until the
    next proposal, a merge of that tip is refused the same way), no merge of his stands
    (`owner_stands`: a second press adds nothing to the first, which goes through on the
    merge agent's safe read or that the server is about to run) and the forge does not
    call it conflicting (Lem brings that one onto the base first), and `park` while a
    breaker waits for him."""
    out: list[str] = []
    if t.release_stop and not t.closed:
        # every act of the board on a task two releases back stops in Lem's guard: the
        # drop is the way on
        return out
    if t.approvable:
        out.append("approve")
    if (
        t.status == "open"
        and t.merge_wait != "relands"
        and not owner_stands(t)
        and not conflicts(t, seen)
    ):
        out.append("merge")
    if t.breaker is not None:
        out.append("park")
    return out


# The first line of a held block of a small change that someone else asked for, whose
# one criterion waits for the owner's yes (project.py FAST_WAIT; stages/new.md, "The
# fast track", step 1).
FAST_CRITERION = (
    "the criteria wait for the owner: a small change that someone else asked for"
)
# The first line of the held block a change of the criteria from the owner's note writes
# (criteria.py CHANGED_WAIT, `lem criteria change`): the criteria wait for his yes
# again, with their text before the change kept in the task directory
# (criteria.py BEFORE).
CHANGED_CRITERIA = "the criteria wait for the owner: changed from the owner's note"
# The first line of the held block after his No whose note changes no criterion
# (criteria.py UNCHANGED_WAIT, `lem criteria change --unchanged`): the same criteria
# wait for his yes again, in a new row.
UNCHANGED_CRITERIA = (
    "the criteria wait for the owner: the owner's note changed no criterion"
)
CRITERIA_BEFORE = "criteria-before.json"
# What the board says once the owner's answer is on record, on the act's note and on the
# task's Overview.
ANSWER_ON_RECORD = "Your answer is on record: the task’s session takes it."
# What each row the board answers with its own buttons asks (lem_answers.OPTIONS), as
# the row and the record say it.
ANSWER_QUESTIONS = {
    "plan": "Build the plan, or drop the task?",
    "breaker": "Help, park or drop the task?",
    "skip": "Skip the persona read?",
    "criterion": "Approve this criterion?",
}
# What the note field of each such row asks for: Help, and No on the criterion, need the
# owner's words.
ANSWER_NOTES = {
    "plan": "A note for the task’s session, if you like",
    "breaker": "Help needs your words for the lead",
    "skip": "A note for the task’s session, if you like",
    "criterion": "No needs your words: what should the criterion say?",
}
# The criteria's row on the standard track: one kind with the fast track's (`criterion`,
# one key form and one record), its own words (criteria.py CRITERIA_QUESTION, which the
# owner's typed No records).
CRITERIA_QUESTION = "Approve the criteria?"
CRITERIA_NOTE = "No needs your words: what should the criteria say?"


def fast_criterion(t: Task) -> bool:
    """Whether the task's criteria are the fast track's one criterion of a request
    someone else wrote."""
    return t.text == FAST_CRITERION


def criterion_question(t: Task) -> str:
    """The question of the task's criteria row: "Approve this criterion?" on the fast
    track, "Approve the criteria?" else."""
    return ANSWER_QUESTIONS["criterion"] if fast_criterion(t) else CRITERIA_QUESTION


def answer_row(t: Task) -> dict | None:
    """The wait of the task that the board answers with its own buttons now
    (lem_answers), or None: a breaker that waits for the owner (Help, Park, Drop), a
    plan that waits for his read (Build, Drop), "Skip the persona read?" of an interview
    (Yes, No), and the criteria while his yes would count (`Task.approvable`, the turn
    his and nobody going on for him; Yes, No): "Approve this criterion?" of a small
    change that someone else asked for, "Approve the criteria?" on the standard track,
    after an interview's read or his skip of it, or in a held block of the criteria (a
    lead's doubt, a change from his note). Its key names the task's newest state block
    by its time to the second, so that a new block of the same wait is a new row, and an
    answer on record applies to its own block only (decision 9 of board-answers-a-card).
    A task begun on an older release than the board's (`Task.behind`) has no row of any
    kind: its session has no `board_answer` to read, so a recorded answer would hide the
    row and reach nobody; it keeps the board's other acts (criteria-change-asks-again,
    talk question 6). A task two releases back has none either: every answer of it
    would stop in Lem's guard (`acts_of`)."""
    if t.closed or not t.blocks or t.behind or t.release_stop:
        return None
    number = None
    if t.breaker is not None and isinstance(t.breaker.id, int):
        kind, number = "breaker", t.breaker.id
    elif t.status == "planned" and re.search(r"\bowner\b", t.text):
        kind = "plan"
    elif (
        t.turn == "skip" and not t.goes_on and t.need and t.need["need"] == "interview"
    ):
        kind = "skip"
    elif t.turn in OWNER_TURNS and not t.goes_on and t.approvable:
        kind = "criterion"
    else:
        return None
    question = (
        f"Breaker {number} of {t.slug}: help, park or drop the task?"
        if kind == "breaker"
        else criterion_question(t)
        if kind == "criterion"
        else ANSWER_QUESTIONS[kind]
    )
    note = (
        CRITERIA_NOTE
        if kind == "criterion" and not fast_criterion(t)
        else ANSWER_NOTES[kind]
    )
    return {
        "kind": kind,
        "key": lem_answers.key_of(kind, t.slug, t.blocks[-1]["ts"], number),
        "question": question,
        "options": dict(lem_answers.OPTIONS[kind]),
        "note": note,
    }


def answered_of(t: Task, m: Model) -> dict | None:
    """The owner's answer on record for the row of the task that the board answers with
    its own buttons (`answer_row`, `Model.answers`), or None: until the task's session
    writes its next state block, the row is hidden and the task's Overview says that his
    answer is on record."""
    row = answer_row(t)
    return (m.answers or {}).get(t.slug, {}).get(row["key"]) if row else None


def acted_head(e: dict[str, Any]) -> str:
    """The activity's words of a `board.act`: ACTED's, or for the answer of a row the
    board answers with its own buttons (its `key`, `option` and `question`, serve.py
    `act_answer`) what he picked and on which row. An event of an older form, with no
    `question`, is named by its row's kind."""
    if e.get("act") == "answer" and e.get("key"):
        try:
            kind = lem_answers.parse(e["key"])["kind"]
        except lem_answers.AnswerError:
            kind = ""  # no row's kind: each table below gives its default
        # the event's own value is the key, whatever a log changed by hand holds there
        options = cast("dict[object, str]", lem_answers.OPTIONS.get(kind, {}))
        label = options.get(e.get("option"), e.get("option") or "an option")
        question = (
            e.get("question")
            if isinstance(e.get("question"), str) and e.get("question")
            else ANSWER_QUESTIONS.get(kind, "a question of the task")
        )
        return f"You picked {label} on “{question}” from the board"
    return ACTED.get(e.get("act"), f"You acted from the board: {e.get('act')}")


def merge_says(t: Task) -> dict:
    """What the confirm step of a merge says first: green or not green, careful when it
    is, and the reasons it is not green."""
    v = verdict_of(t)
    careful = careful_of(t)
    return {
        "green": bool(v and v["green"]),
        "proposed": v is not None,
        "reasons": list(v["reasons"]) if v else [],
        "careful": bool(careful and careful["yes"]),
        "careful_why": (careful or {}).get("why") or "",
    }


def asked_of(t: Task, kinds: tuple, other: str) -> tuple[dict | None, str]:
    """The row of the task that the board answers with its own buttons (`answer_row`)
    when it is of one of KINDS, else None, and the key of the row of "Waits for you" it
    stands for: the answer row's own, which names the state block, else OTHER."""
    asks = answer_row(t)
    row = asks if asks and asks["kind"] in kinds else None
    return row, row["key"] if row else other


def held_row(t: Task) -> dict | None:
    """The row of "Waits for you" that a task's held block gives, or None, with the row
    the board answers with its own buttons as its `asks` (`asked_of`), whose key it
    takes. A breaker that waits is its own row, and the held block it wrote is not said
    again; a held task is his while its turn is (`turn_of`): not while Lem writes its
    criteria or the personas read them, nor while Lem settles its need without
    him (`goes_on_of`)."""
    if t.breaker:
        row, key = asked_of(t, ("breaker",), f"breaker:{t.slug}:{t.breaker.id}")
        return {
            "kind": "breaker",
            "key": key,
            "t": t,
            "c": t.breaker,
            "since": t.breaker.ts,
            "asks": row,
        }
    if t.turn in OWNER_TURNS and not t.goes_on:
        row, key = asked_of(t, ("skip", "criterion"), f"held:{t.slug}")
        return {
            "kind": "criteria" if t.criteria_wait else "held",
            "key": key,
            "t": t,
            "c": None,
            "since": t.since,
            "asks": row,
        }
    return None


def held_back(m: Model) -> set[str]:
    """The keys of the rows that a working session holds back (`put_sessions`): each
    would be a row of "Waits for you" once the session's turn ends, so the Inbox keeps
    what it sent for it (lem_inbox `plan`)."""
    return {
        row["key"]
        for t in m.tasks
        if t.works and not t.closed and (row := held_row(t)) is not None
    }


def waits_of(m: Model) -> list[dict]:  # noqa: C901 - over the limit before the limit was set
    """The rows of "Waits for you": one for each thing the owner does, as
    `lem project waiting` lists them (with the plans he reads), the most
    pressing first."""
    rows = []
    for t in m.tasks:
        if t.release_stop and not t.closed:
            # a task two releases back: its one row says the stop's message, and nothing
            # else of it is his until the drop
            rows.append(
                {
                    "kind": "blocked",
                    "key": f"blocked:{t.slug}",
                    "t": t,
                    "c": None,
                    "since": t.release_stop["ts"],
                    "say": t.release_stop["say"],
                }
            )
            continue
        # a task stuck for want of its session: the one row of a merged or dropped task
        # whose cleanup did not run
        need = session_need(t, m)
        stop = stopped_of(t, m)
        if stop is not None:
            # the guard's stop, whose fresh session also answers a wake-up that waits in
            # the stopped one; `unread` for a session whose signs of work Lem cannot
            # read, stopped after the status message alone
            rows.append(
                {
                    "kind": "stopped",
                    "key": f"stopped:{t.slug}",
                    "t": t,
                    "c": None,
                    "since": at(stop.get("ts")) or t.since,
                    "unread": stop.get("unread") is True,
                    # false for a stop that no fresh session took the place of
                    "restarted": restarted_before(t, stop),
                }
            )
        elif need:
            since = max(
                t.since if t.closed else t.first, (t.opened or {}).get("ts") or 0
            )
            rows.append(
                {
                    "kind": "session",
                    "key": f"{'deaf' if need == 'deaf' else 'session'}:{t.slug}",
                    "t": t,
                    "c": None,
                    "since": since,
                    "deaf": need == "deaf",
                    "unheard": (live_of(t, m) or {}).get("unheard")
                    if need == "deaf"
                    else None,
                }
            )
        if t.closed:
            continue
        # the row of a breaker or of a held task (`held_row`), held back while the
        # task's session works on his answer (`put_sessions`), and none while his answer
        # to it on the board is on record (`answered_of`): the task's session takes it
        answered = answered_of(t, m) is not None
        held = held_row(t)
        if held is not None and not t.works and not (held["asks"] and answered):
            rows.append(held)
        # a task queued after a task that was dropped: no session runs it, and only his
        # word starts it or ends it
        if after_dropped(t, m):
            done = m.by_slug[after_of(t)]
            rows.append(
                {
                    "kind": "after_dropped",
                    "key": f"after_dropped:{t.slug}",
                    "t": t,
                    "c": None,
                    "since": max(t.since, done.since),
                    "after": done.slug,
                }
            )
        # a task its session stopped with something it cannot settle alone; not one that
        # waits for the base's repair
        if t.status == "blocked" and not t.base_red:
            rows.append(
                {
                    "kind": "blocked",
                    "key": f"blocked:{t.slug}",
                    "t": t,
                    "c": None,
                    "since": t.since,
                }
            )
        # a card the task's live session put up and waits on: one row for each, answered
        # here or in the session
        rows.extend(
            {
                "kind": "card",
                "key": f"card:{t.slug}:{c['page']}",
                "t": t,
                "c": c,
                "since": c["since"],
            }
            for c in open_cards(t, m)
        )
        if t.status == "planned" and re.search(r"\bowner\b", t.text):
            row, key = asked_of(t, ("plan",), f"plan:{t.slug}")
            if not (row and answered):
                rows.append(
                    {
                        "kind": "plan",
                        "key": key,
                        "t": t,
                        "c": None,
                        "since": t.since,
                        "asks": row,
                    }
                )
        # an open task is his only when its merge waits for him (`merge_wait`): not
        # while the merge agent reads it, nor while the server merges it
        if t.merge_wait == "owner" and t.merge_review and t.merge_review["calls"]:
            rows.append(
                {
                    "kind": "review",
                    "key": f"review:{t.slug}",
                    "t": t,
                    "c": t.merge_review,
                    "since": t.merge_review["ts"],
                }
            )
        if t.merge_wait == "owner":
            rows.append(
                {
                    "kind": "merge",
                    "key": f"merge:{t.slug}",
                    "t": t,
                    "c": None,
                    "since": t.since,
                    "conflict": conflicts(t, m.seen),
                }
            )
    return sorted(rows, key=lambda w: (WAIT_ORDER[w["kind"]], w["since"]))


def wait_stacks(rows: list[dict]) -> list[dict]:
    """The rows of "Waits for you" (`waits_of`) grouped by task, as the view and its
    counts draw them: one group for each task, `{"t": task, "rows": [...]}`, in the
    place of its first row, its rows in their order. A group of one row is that row; a
    group of two or more is one stack that opens. The rows stay one for each thing: the
    pushes and the Inbox read them by their keys."""
    stacks: list[dict] = []
    by_slug: dict[str, dict] = {}
    for w in rows:
        stack = by_slug.get(w["t"].slug)
        if stack is None:
            stack = by_slug[w["t"].slug] = {"t": w["t"], "rows": []}
            stacks.append(stack)
        stack["rows"].append(w)
    return stacks


def wait_count(m: Model) -> int:
    """How many tasks wait for the owner: the tasks with a row of "Waits for you", one
    for each group of `wait_stacks`. Every place whose words say what waits for him
    counts this: the top line of the Tasks view (`summary_of`), the sidebar, the rail,
    the page's title, the phone's icon and the switcher's row of a workspace. The "You"
    column of the kanban holds the tasks whose next act is his (`for_owner`), which is
    not always the same set: a task that builds with no session has a row and stays in
    its column."""
    return len(wait_stacks(waits_of(m)))


def open_cards(t: Task, m: Model) -> list[dict]:
    """The `lem-ask` cards of the task that wait for the owner now, oldest first: open
    as its folder says (`Model.cards`), and put up by the session that is the task's
    live one (`live_of`). A card of an earlier session of the task, which a change of
    phase or a crash left with no waiter, has none, nor has any card while nothing says
    which session lives."""
    found = (m.cards or {}).get(t.slug) or []
    f = live_of(t, m) if found else None
    if not f or not f["live"] or not f["session"]:
        return []
    return [
        c
        for c in found
        if str(c.get("session") or "").upper() == str(f["session"]).upper()
    ]


def answered_in_session(w: dict, m: Model) -> bool:
    """Whether the owner answers a row of "Waits for you" in the task's own session
    rather than on the board: a held step with no answer of his on the board (the
    interview and the others; not criteria that wait for his approval there, nor a row
    with its own buttons, `asks`: "Skip the persona read?"), a task its session stopped,
    and a session that does not answer. Every other row (a merge, criteria, a breaker's
    document, a plan, a card of the task's session, a merge review, a task queued after
    a dropped one, a task with no session, a task whose stop the guard of a stopped
    session logged) he answers on the board or in another session."""
    kind = w["kind"]
    if kind == "held":
        return "approve" not in acts_of(w["t"], m.seen) and not w.get("asks")
    return kind == "blocked" or (kind == "session" and bool(w.get("deaf")))


def session_of_wait(w: dict, m: Model) -> str | None:
    """The session a click on a row's verb goes to: the task's session while it lives,
    for a row the owner answers there (`answered_in_session`); None otherwise, and the
    verb opens the task's panel."""
    if not answered_in_session(w, m):
        return None
    f = live_of(w["t"], m)
    return f["session"] if f and f["live"] and f["session"] else None


def dropped_head(after: str) -> str:
    """What a task queued after the dropped task AFTER waits for: the words of its row
    in "Waits for you" and of its Overview's headline."""
    return f"{after} was dropped: your word starts or ends this task"


def deaf_where(t: Task, unheard: dict | None) -> str:
    """Where the owner answers a session that does not answer, in the case `lem session
    list` names (UNHEARD): the wake's line still waits in its mailbox, or its pane took
    the line and took no turn (a parked Claude Code process), whose fresh session comes
    once he closes it (`session_need`'s `gone`). An entry with no case keeps the words
    of the line that waits."""
    if not unheard:
        return (
            "A wake-up has waited in the task’s session for 10 minutes or more. "
            "Look at the session: its agent may wait for an answer, "
            "or run a long turn."
        )
    line = f"“lem: {t.slug} {unheard.get('why')}”"
    if unheard.get("line") == "taken":
        return (
            f"The task’s session took the wake-up {line} 10 minutes ago or more, and "
            "took no turn after it: its agent does not run. Go to the session and "
            "tell it to go on, or close the session: then this row offers “Open a "
            "session”."
        )
    return (
        f"The wake-up {line} has waited in the task’s session for 10 minutes or "
        "more. Look at the session: its agent may wait for an answer, or run a long "
        "turn."
    )


def wait_say(w: dict) -> dict:  # noqa: C901, PLR0911, PLR0912 - over the limit before the limit was set
    """What a row of "Waits for you" says the owner does, its icon, the tab where he
    acts, and how its time reads."""
    t, kind = w["t"], w["kind"]
    if kind == "session" and w.get("deaf"):
        return {
            "verb": "Its session does not answer",
            "icon": "alert",
            "actor": "bad",
            "to": "overview",
            "note": "since its session opened",
            "where": deaf_where(t, w.get("unheard")),
        }
    if kind == "stopped" and w.get("unread"):
        return {
            "verb": "Its session stopped, and Lem cannot read it: open a fresh one",
            "icon": "alert",
            "actor": "bad",
            "to": "overview",
            "note": "since Lem logged the stop",
            "where": (
                "Lem cannot read whether the task’s session works. It sent the session "
                f"the status message after {QUIET_MS // 60000} minutes with no event "
                "of the task, and saw no event of the task in the "
                f"{ANSWER_MS // 60000} minutes after it. Lem opens no second session "
                "by itself: open a session here or on the task’s header, and a fresh "
                "agent reads the task’s state and goes on from there. "
                "The old pane stays open in agterm."
            ),
        }
    if kind == "stopped":
        return {
            "verb": "Its session stopped: open a fresh one",
            "icon": "alert",
            "actor": "bad",
            "to": "overview",
            "note": "since Lem logged the stop",
            "where": (
                (
                    "The task’s session showed no sign of work in the "
                    f"{ANSWER_MS // 60000} minutes after Lem asked it for its status, "
                    "and Lem opened no fresh session by itself, since the task "
                    "already stopped once after its last work."
                    if w.get("restarted") is False
                    else (
                        "The task’s session showed no sign of work for "
                        f"{QUIET_MS // 60000} minutes, nor in the {ANSWER_MS // 60000} "
                        "minutes after Lem asked it for its status, and neither did "
                        "the fresh session that took its place."
                    )
                )
                + " Open a session here or on the task’s header: "
                "a fresh agent reads the task’s state and goes on from there, and the "
                "old pane stays open in agterm."
            ),
        }
    if kind == "session" and t.closed and t.status == "dropped":
        return {
            "verb": "No session cleans the dropped task",
            "icon": "alert",
            "actor": "bad",
            "to": "overview",
            "note": "since it was dropped",
            "where": (
                "Open a session here or on the task’s header: it gives a ticket what "
                "it is still owed, then removes the worktree; "
                "the branch keeps its commits."
            ),
        }
    if kind == "session" and t.closed:
        return {
            "verb": "No session cleans the merged task",
            "icon": "alert",
            "actor": "bad",
            "to": "overview",
            "note": "since it was merged",
            "where": (
                "Open a session here or on the task’s header: it removes the worktree, "
                "and the branch when it holds nothing that was not merged, "
                "and updates the ticket."
            ),
        }
    if kind == "session":
        return {
            "verb": "No session runs this task",
            "icon": "alert",
            "actor": "bad",
            "to": "overview",
            "note": "since its last session opened" if t.opened else "since it opened",
            "where": (
                "Open a session here or on the task’s header: a fresh agent reads the "
                "task’s state and goes on from there."
            ),
        }
    if kind == "breaker":
        return {
            "verb": f"Read the breaker of {t.slug}",
            "icon": "alert",
            "to": "overview",
            "note": "since the build stopped",
        }
    if kind == "criteria":
        return {
            "verb": "Approve the criteria",
            "icon": "file",
            "to": "overview",
            "note": "in this state",
        }
    if kind == "held":
        return {
            "verb": cap(t.shown or t.info["label"]),
            "icon": "user",
            "to": "overview",
            "note": "in this state",
        }
    if kind == "after_dropped":
        # the two words he types, each with the task's name: no session runs this task,
        # so he types them in another one
        after, start, drop = w["after"], f"start {t.slug} now", f"/lem drop {t.slug}"
        return {
            "verb": dropped_head(after),
            "icon": "user",
            "to": "overview",
            "note": f"since {after} was dropped",
            "start": start,
            "drop": drop,
            "where": answer_of(t),
        }
    if kind == "blocked" and w.get("say"):
        return {
            "verb": OLDER_RELEASE,
            "icon": "alert",
            "actor": "bad",
            "to": "overview",
            "note": "since Lem stopped it",
            "where": w["say"],
        }
    if kind == "blocked":
        return {
            "verb": "Its session stopped: tell it what to do",
            "icon": "alert",
            "actor": "bad",
            "to": "overview",
            "note": "since it stopped",
            "where": blocked_where(t),
        }
    if kind == "plan":
        return {
            "verb": "Read the plan",
            "icon": "file",
            "to": "overview",
            "note": "in this state",
        }
    if kind == "card":
        return {
            "verb": cap(w["c"]["prompt"] or "The task’s session asks you"),
            "icon": "user",
            "to": f"card/{w['c']['page']}",
            "note": "since the session asked",
            "where": (
                "on the card, here or in the task’s session at the Mac. "
                "The board takes an answer with a note, never a conversation: "
                "a question back goes to the session at the Mac."
            ),
        }
    if kind == "review":
        return {
            "verb": "Read the merge review",
            "icon": "file",
            "to": "overview",
            "note": "since the merge agent wrote it",
            "where": (
                "The merge review is the first card of the "
                f"task’s Overview. {review_why(w['c'])}"
            ),
        }
    if t.refused and t.refused.get("from") == "lem":
        return {
            "verb": "The merge did not go through",
            "icon": "alert",
            "actor": "bad",
            "to": "overview",
            "note": "since it was proposed",
            "where": (
                f"Lem said: {t.refused.get('said') or 'nothing'}. The board’s server "
                "woke the task’s session: it runs the steps the line names, "
                "or waits for you."
            ),
        }
    if t.refused:
        return {
            "verb": "GitHub refused the merge",
            "icon": "alert",
            "actor": "bad",
            "to": "overview",
            "note": "since it was proposed",
            "where": (
                f"GitHub said: {t.refused.get('said') or 'nothing'}. Act on GitHub, or "
                "ask the task’s session for a change."
            ),
        }
    if w.get("conflict"):
        return {
            "verb": "It conflicts with the base",
            "icon": "alert",
            "actor": "bad",
            "to": "overview",
            "note": "since it was proposed",
            "where": (
                "Nothing to do now: the board’s server wakes the task’s session, which "
                "brings it onto the base, and then it waits for you again."
            ),
        }
    pr = pr_of(t)
    number = f" #{pr['n']}" if pr else ""
    verb = f"Merge the pull request{number}"
    return {
        "verb": verb,
        "icon": "branch",
        "to": "overview",
        "note": "since it was proposed",
    }


def review_why(review: dict) -> str:
    """The merge agent's one sentence of why it calls the owner, as land.py keeps it
    (the first line of its review, `Verdict: call.` and all), without the verdict that
    the row already says, as one sentence."""
    said = re.sub(
        r"^\s*Verdict:\s*(call|merge)\.\s*",
        "",
        str(review.get("why") or ""),
        flags=re.IGNORECASE,
    ).strip()
    said = cap(said or "the merge agent calls you")
    return said if said.endswith((".", "!", "?")) else f"{said}."


def phase_index(t: Task, lead: str | None = "") -> int:  # noqa: PLR0911 - over the limit before the limit was set
    """The step of the flow the task reached; a task that waits for the owner or is
    blocked stays where it got to."""
    lead = t.lead if lead == "" else lead
    reached = t.reached
    if reached == "answered":
        return -1
    if lead == "small":
        return (
            len(SMALL_PHASES)
            if reached == "landed"
            else max(0, phase_index(t, None) - 2)
        )
    if reached == "landed":
        return len(PHASES)
    if reached == "open":
        return 5
    if reached == "landing":
        return 4 if t.reviews else 3
    if reached == "ready":
        return 3
    if reached == "building":
        return 2 if t.plan_committed or t.progress else 1
    if reached == "planned":
        return 1
    return 0


def phases_of(t: Task) -> dict:
    """The phases of the task's progress card: their names, the current one (`at`) and
    how many are past."""
    lead = 1 if t.investigated else 0
    answered = t.status == "answered"
    base = SMALL_PHASES if t.lead == "small" else PHASES
    names = (
        [*(["Investigation"] if lead else []), "Answered"]
        if answered
        else ["Investigation", *base]
        if t.investigated
        else list(base)
    )
    step = 0 if t.investigating else -1 if answered else phase_index(t) + lead
    past = 0 if t.investigating else len(names) if answered else step
    return {"names": names, "at": step, "past": past}


# ---- the activity: each event in words ----


def investigation_sub(x: dict) -> str:
    parts = [
        x.get("where") or "",
        ("reproduced" if x.get("reproduced") else "not reproduced")
        if x.get("type") == "fix" and x.get("reproduced") is not None
        else "",
    ]
    return " · ".join(p for p in parts if p)


def job_of(e: dict) -> object:
    return "the change" if e.get("job") == FAST_JOB else e.get("job")


def gate_end_said(e: dict) -> dict:
    said = say_of(e)
    ran = f"after {span((e.get('seconds') or 0) * 1000)} on {e.get('tip') or '?'}" + (
        (
            f" · the tests of the criteria taken from the polish pass at {e['taken']}, "
            "not run again"
        )
        if e.get("taken")
        else ""
    )
    info = (
        {"actor": "done", "icon": "check"}
        if e.get("result") == "passed"
        else {"actor": "lem", "icon": "x"}
        if e.get("result") == "stopped"
        else {"actor": "bad", "icon": "alert"}
    )
    return {
        "info": info,
        "head": checks_end(e.get("result"))["head"],
        "text": said or ran,
        "sub": ran if said else "",
    }


SUMMARY_HEAD = "Its events became one summary"


def summary_said(e: dict) -> str:
    """What a task's summary stands for, in the words of the board: how many events,
    and why."""
    n = e.get("events") if isinstance(e.get("events"), int) else 0
    return (
        f"{plural(n, 'event')} in one event that keeps the task's status, its end and "
        "its pull request: nothing of the task happened for "
        "state.keep_days days after its end"
    )


# The start of the why of a merge review that is another round because the merge agent's
# answer could not be recorded twice on a moved base: Lem's words (`land.UNRECORDED`).
UNRECORDED = "the merge agent's answer could not be recorded twice"


def merge_review_said(e: dict) -> dict:
    """The merge agent's read in the feed: its verdict, and on a moved base its call
    (`base_call`) on the base it read, with that call's sentence of why (`base_why`)
    beside the verdict's."""
    call, calls = e.get("base_call"), e.get("calls")
    verdict = "it calls you" if calls else "it merges"
    sub = " · ".join(str(x) for x in (e.get("why"), e.get("base_why")) if x) or (
        f"by {e['by']}" if e.get("by") else ""
    )
    if call not in ("safe", "another round"):
        return {
            "info": {"actor": "you" if calls else "gate", "icon": "file"},
            "head": "The merge agent read the task",
            "text": verdict,
            "sub": sub,
        }
    base = f"the moved base {str(e['base'])[:9]}" if e.get("base") else "the moved base"
    if call == "safe":
        return {
            "info": {"actor": "you" if calls else "gate", "icon": "file"},
            "head": "The merge agent read the task and the moved base",
            "text": f"{base} is safe; {verdict}",
            "sub": sub,
        }
    if str(e.get("base_why") or "").startswith(UNRECORDED):
        # no read of the agent said it: Lem recorded another round in its place
        return {
            "info": {"actor": "gate", "icon": "file"},
            "head": "The merge agent's answer could not be recorded",
            "text": (
                f"{base} gets another round of the checks in doubt: Lem lands it again"
            ),
            "sub": e.get("base_why") or sub,
        }
    return {
        "info": {"actor": "gate", "icon": "file"},
        "head": "The merge agent read the task and the moved base",
        "text": f"{base} needs another round of the checks: Lem lands it again",
        "sub": e.get("base_why") or sub,
    }


def _approved_head(e: dict) -> str:
    heads: dict[object, str] = {
        "owner": "You approved the acceptance criteria",
        "lem": "Taken for the fast track in your name",
        "read": "The personas’ read froze the criteria",
    }
    return heads.get(e.get("by"), f"Criteria approved by {e.get('by')}")


def _flagged_words(flagged: object) -> str:
    """What a read of the criteria flagged: "2 flagged", or "nobody confused"."""
    return str(flagged) + " flagged" if flagged else "nobody confused"


def _criterion_head(e: dict) -> str:
    how = (
        "changed"
        if e.get("how") == "changed"
        else "was added"
        if e.get("how") == "added"
        else "was removed"
    )
    return f"Criterion {e.get('criterion')} {how}"


# What each event of the scripts says, in the feed's words; an event not named here is
# shown as its fields.
SAYS = {
    "task.criteria": lambda e: {
        "info": {"actor": "lead", "icon": "file"},
        "head": "Acceptance criteria recorded",
        "text": (
            f"{track_words(e.get('size'))}: "
            f"{criteria_count(len(e.get('criteria') or []))}"
        ),
    },
    "task.red": lambda e: {
        "info": {
            "actor": "done" if e.get("ok") else "bad",
            "icon": "check" if e.get("ok") else "alert",
        },
        "head": "The tests of the criteria hold"
        if e.get("ok")
        else "A test does not hold its criterion",
        "text": f"on {e.get('tip') or '?'}, against {e.get('base') or 'the base'}",
    },
    "criteria.approved": lambda e: {
        "info": {"actor": "you" if e.get("by") == "owner" else "lem", "icon": "check"},
        "head": _approved_head(e),
        "text": (
            f"{'approval ' + str(e['number']) + ' · ' if e.get('number') else ''}"
            f"{track_words(e.get('size'))}: "
            f"{criteria_count(len(e.get('criteria') or []))}"
        ),
    },
    "criteria.read": lambda e: (
        {
            "info": {"actor": "bad", "icon": "users"},
            "head": "Nobody answered the personas’ read of the criteria",
            "text": f"0 of {e.get('asked')} answered",
        }
        if not e.get("answered")
        else {
            "info": {
                "actor": "you" if e.get("split") or e.get("flagged") else "done",
                "icon": "users",
            },
            "head": "The personas read the criteria",
            "text": (
                f"{'the families split · ' if e.get('split') else ''}"
                f"{_flagged_words(e.get('flagged'))}"
                f" · {e.get('answered')} of {e.get('asked')} answered"
            ),
        }
    ),
    "review": lambda e: {
        "info": {
            "actor": "done" if e.get("verdict") == "clean" else "bad",
            "icon": "eye",
        },
        "head": "Review",
        "text": review_line(e),
    },
    "review.filed": lambda e: {
        "info": {"actor": "lem", "icon": "file"},
        "head": "Filed in the backlog",
        "text": plural(len(e.get("items") or []), "item"),
    },
    "proposed": lambda e: {
        "info": {
            "actor": "done" if e.get("green") else "you",
            "icon": "check" if e.get("green") else "alert",
        },
        "head": "Proposed: green" if e.get("green") else "Proposed: not green",
        "text": " · ".join(map(str, e.get("not_green") or [])),
    },
    "plan.talk.start": lambda e: {
        "info": {"actor": "gate", "icon": "split"},
        "head": "The plan talk started",
        "text": f"with {e.get('reviewer')}",
    },
    "plan.talk": lambda e: {
        "info": {"actor": "gate", "icon": "split"},
        "head": "The plan talk ended",
        "text": f"with {e.get('reviewer')}: {talk_counts(e)}",
    },
    # a seat's agent gave an error (`lem project seat-failed`): the fallback stood in,
    # or the task waits for your go on
    "seat.stand-in": lambda e: {
        "info": {"actor": "lem", "icon": "split"},
        "head": f"The fallback stood in for {SEAT_WORDS.get(e.get('seat'), 'a seat')}",
        "text": f"{e.get('took')} in place of {e.get('failed')}",
        "sub": e.get("said") or e.get("error") or "",
    },
    "seat.blocked": lambda e: {
        "info": {"actor": "you", "icon": "alert"},
        "head": (
            f"The seat of {SEAT_WORDS.get(e.get('seat'), 'a seat')} gave an error, "
            "and no fallback stood in"
        ),
        "text": e.get("say") or e.get("failed") or "",
        "sub": e.get("said") or "",
    },
    "seat.again": lambda e: {
        "info": {"actor": "you", "icon": "user"},
        "head": "Your go on: the seat is tried again",
        "text": e.get("say") or e.get("seat") or "",
    },
    "careful.missed": lambda e: {
        "info": {"actor": "bad", "icon": "alert"},
        "head": "Careful by the review, not by the plan",
        "text": f"round {e.get('round') or '?'}: {e.get('why')}",
    },
    "investigation": lambda e: {
        "info": {
            "actor": "you" if e.get("call") == "not-reproduced" else "done",
            "icon": "eye",
        },
        "head": CALLS.get(e.get("call"), {}).get(
            "head", f"The investigation: {e.get('call')}"
        ),
        "text": e.get("line"),
        "sub": investigation_sub(e),
    },
    "polish": lambda e: {
        "info": {"actor": "lead", "icon": "code"},
        "head": "The polish pass",
        "text": (
            f"{plural(e.get('commits') or 0, 'commit')}, "
            f"{plural(len(e['filed']), 'item') if e.get('filed') else 'no item'} filed "
            "in the backlog"
        ),
        "sub": " · ".join(
            [
                f"{e.get('before') or '?'} → {e.get('after') or '?'}",
                *map(str, e.get("filed") or []),
            ]
        ),
    },
    "interview.start": lambda e: {
        "info": {"actor": "you", "icon": "user"},
        "head": "The interview started",
        "text": "Lem asks you one question at a time",
    },
    "interview.end": lambda e: {
        "info": {"actor": "lem", "icon": "file"},
        "head": "The interview’s questions ended",
        "text": "Lem writes the criteria from the answers",
    },
    "read.skip.asked": lambda e: {
        "info": {"actor": "you", "icon": "users"},
        "head": "Lem asked whether to skip the personas’ read",
        "text": "the criteria name only you: your y or n",
    },
    "scout.start": lambda e: {
        "info": {"actor": "lead", "icon": "eye"},
        "head": "The scout started",
        "text": "it reads the code for the facts the criteria need",
    },
    "scout": lambda e: {
        "info": {"actor": "lead", "icon": "file"},
        "head": "The scout’s report is in",
        "text": "",
    },
    "criteria.read.start": lambda e: {
        "info": {"actor": "quiet", "icon": "users"},
        "head": "The personas’ read of the criteria started",
        "text": f"run by {'the agent' if e.get('by') == 'lead' else 'Lem'}",
    },
    "investigation.start": lambda e: {
        "info": {"actor": "lead", "icon": "eye"},
        "head": "The investigation started",
        "text": "an investigator reproduces the bug and finds its cause"
        if e.get("type") == "fix"
        else "an investigator finds the answer",
    },
    "builder.start": lambda e: {
        "info": {"actor": "lead", "icon": "code"},
        "head": "A builder started",
        "text": job_of(e),
    },
    "polish.start": lambda e: {
        "info": {"actor": "lead", "icon": "code"},
        "head": "The polish pass started",
        "text": f"on {e.get('before') or '?'}",
    },
    "gate.wait": lambda e: {
        "info": {"actor": "quiet", "icon": "clock"},
        "head": "The checks wait",
        "text": f"behind {behind_said(e)}"
        if e.get("behind")
        else f"a minute after the checks of {e['after']} started"
        if e.get("after")
        else f"for the load: {e.get('load')}, they start below {e.get('start')}",
    },
    "merge.wait": lambda e: {
        "info": {"actor": "quiet", "icon": "clock"},
        "head": "The merge call waits",
        "text": f"for the merge of {e.get('after') or 'another task'}",
    },
    "merge.start": lambda e: {
        "info": {"actor": "gate", "icon": "play"},
        "head": "Lem’s merge call started",
        "text": (
            "the merge agent’s merge, which the board’s server runs"
            if e.get("by") == "merger" and e.get("via") == "server"
            else "the merge agent’s merge"
            if e.get("by") == "merger"
            else "your merge"
            if e.get("by") == "owner"
            else ""
        )
        + ("; " if e.get("by") else "")
        + "it reads the base branch first",
    },
    "merge.review": merge_review_said,
    # land.py logs it after a safe read of the moved base, or a read on the checks' base
    # after a revert (`after`), or at a proposal that kept the change he merged
    "merge.stands": lambda e: {
        "info": {"actor": "gate", "icon": "play"},
        "head": "Your merge stands",
        "text": (
            "the merge agent read the moved base and said safe"
            if e.get("after") == "a read of the moved base"
            else (
                "the merge agent read it on the base the checks ran on, "
                "which main has again"
            )
            if e.get("after") == "a read of the base back on the checks' tree"
            else "the new landing kept the change you merged"
        )
        + ": the board’s server runs it, and nobody asks you again",
    },
    # land.py logs it when your standing merge ends: at `start` of a landing that starts
    # over, or at a proposal whose change or reasons for not green are not the ones you
    # merged (`why`)
    "merge.ended": lambda e: {
        "info": {"actor": "you", "icon": "alert"},
        "head": "Your merge ended",
        "text": f"{e.get('why') or 'no reason given'}: you merge it again",
    },
    "merge.refused": lambda e: {
        "info": {"actor": "bad", "icon": "alert"},
        "head": (
            "Lem refused your merge"
            if e.get("by") == "owner"
            else "Lem refused the merge agent’s merge"
        )
        if e.get("from") == "lem"
        else "GitHub refused the merge",
        "text": e.get("said") or "",
    },
    "gate.start": lambda e: {
        "info": {"actor": "gate", "icon": "play"},
        "head": "The checks started",
        "text": f"{plural(e.get('commands') or 0, 'command')} on {e.get('tip') or '?'}",
    },
    "gate.end": gate_end_said,
    "review.start": lambda e: {
        "info": {"actor": "gate", "icon": "eye"},
        "head": "The review started",
        "text": (
            f"attempt {e.get('attempt') or '?'} · "
            f"{KIND.get(e.get('floor'), e.get('floor'))}"
        ),
    },
    "session.open": lambda e: {
        "info": {"actor": "lem", "icon": "split"},
        "head": "A fresh session took the task over"
        if e.get("why") == "stopped"
        else "The task’s session opened",
        "text": e.get("name") or e.get("task") or "",
        "sub": " · ".join(
            x
            for x in (
                f"the {e['phase']} phase" if e.get("phase") else "",
                OPENED.get(e.get("why"), e.get("why") or ""),
            )
            if x
        ),
    },
    "session.close": lambda e: {
        "info": {"actor": "quiet", "icon": "split"},
        "head": "A session of the task closed",
        "text": CLOSED.get(e.get("why"), e.get("why") or ""),
    },
    "session.transcript": lambda e: {
        "info": {"actor": "quiet", "icon": "split"},
        "head": "Claude Code started in the task’s session",
        "text": {
            "startup": "a new conversation",
            "resume": "a resumed conversation",
            "clear": "after a clear",
            "compact": "after a compaction",
            "fork": "a forked conversation",
        }.get(e.get("source"), "a conversation"),
    },
    "session.wake": lambda e: (
        {
            "info": {"actor": "lem", "icon": "split"},
            "head": "The board’s server asked the task’s session for its status",
            "text": (
                (
                    f"no event of the task for {QUIET_MS // 60000} minutes, and Lem "
                    "cannot read its session"
                )
                if e.get("unread") is True
                else f"no sign of work for {QUIET_MS // 60000} minutes"
            )
            + ": it says where the task stands and goes on with its next step",
        }
        if e.get("why") == "status"
        else {
            "info": {"actor": "quiet", "icon": "split"},
            "head": (
                "The board’s server told the old session that a fresh one replaced it"
            ),
            "text": "it closes itself at the end of its turn",
        }
        if e.get("why") == "replaced"
        else {
            "info": {"actor": "lem", "icon": "split"},
            "head": "The board’s server woke the task’s session",
            "text": {
                "merged": "the pull request is merged: the session cleans up",
                "conflict": (
                    "GitHub calls the pull request conflicting: "
                    "the session brings it onto the base"
                ),
                "queue": "the task it waited for ended",
            }.get(e.get("why"), e.get("why") or ""),
        }
    ),
    WORKED: lambda e: {
        "info": {"actor": "lem", "icon": "split"},
        "head": "Lem read the task’s session again, and it worked",
        "text": (
            "a turn of the session came after the status message that Lem sent while "
            "it could not read it, so no stop waits for you"
        ),
    },
    "session.stopped": lambda e: {
        "info": {"actor": "bad", "icon": "alert"},
        "head": "The task’s session stopped",
        "text": (
            f"no event of the task in the {ANSWER_MS // 60000} minutes after the "
            "status message, and Lem cannot read its session: “Open a session” on the "
            "board starts a fresh one"
        )
        if e.get("unread") is True
        else (
            "no sign of work after the status message, nor in the fresh session: "
            "“Open a session” on the board starts another"
        ),
    },
    "decision.taken": lambda e: (
        {
            "info": {"actor": "you", "icon": "user"},
            "head": f"You helped on breaker {e['breaker']}",
            "text": e.get("chose"),
            "sub": f"“{e['words']}”" if e.get("words") else "",
        }
        if e.get("by") == "owner" and e.get("breaker") is not None
        else {
            "info": {"actor": "done", "icon": "check"},
            "head": (
                f"Decision {e.get('id')}, by {BY_WHOM.get(e.get('by'), e.get('by'))}"
            ),
            "text": f"{e.get('what')} → {e.get('chose')}",
        }
    ),
    "decision.breaker": lambda e: {
        "info": {"actor": "you", "icon": "alert"},
        "head": f"The build of {e.get('task')} stopped: {e.get('what')}",
        "text": stop_words(
            Decision(
                id=e.get("id"),
                kind="breaker",
                ts=0,
                stop=e.get("cause"),
                irreversible=e.get("irreversible"),
            )
        ),
        "sub": (
            f"breaker {e.get('id')} · {e.get('document') or 'breaker.md'} in the task "
            "directory"
        ),
    },
    "card.asked": lambda e: {
        "info": {"actor": "you", "icon": "user"},
        "head": "The task’s session asks you on a card",
        "text": e.get("prompt") or "",
    },
    "card.answered": lambda e: {
        "info": {"actor": "done", "icon": "check"},
        "head": "You answered the card on the board"
        if e.get("from") == "board"
        else "You answered the card in the session",
        "text": VIA.get(e.get("via"), "")
        + (f", from the {e['device']}" if e.get("device") else "")
        if e.get("from") == "board"
        else "",
    },
    "card.closed": lambda e: {
        "info": {"actor": "quiet", "icon": "dot"},
        "head": "The card was dismissed"
        if e.get("status") == "dismissed"
        else "The card was closed",
        "text": "on the board" if e.get("from") == "board" else "in the session",
    },
    "board.act": lambda e: {
        "info": {"actor": "you", "icon": "user"},
        "head": acted_head(e),
        "text": e.get("via") or "",
        "sub": e.get("why") or "",
    },
    "decision.criterion": lambda e: {
        "info": {"actor": "you", "icon": "alert"},
        "head": _criterion_head(e),
        "text": e.get("why"),
    },
    SUMMARY: lambda e: {
        "info": STATUS.get(e.get("status"), UNKNOWN),
        "head": SUMMARY_HEAD,
        "text": summary_said(e),
    },
}


def stop_over_work_said(_e: dict) -> dict:
    """The words of a `session.stopped` that never stood (`stop_over_work`), which
    `describe` gives in place of SAYS's."""
    return {
        "info": {"actor": "quiet", "icon": "split"},
        "head": "Lem logged a stop of the task’s session, but the task worked",
        "text": (
            "work of the task came after the status message and before the stop, so "
            "the stop does not stand and nothing waits for you"
        ),
    }


def stop_unrestarted_said(_e: dict) -> dict:
    """The words of a readable `session.stopped` that no fresh session took the place
    of (`restarted_before`), which `describe` gives in place of SAYS's."""
    return {
        "info": {"actor": "bad", "icon": "alert"},
        "head": "The task’s session stopped",
        "text": (
            "no sign of work after the status message, and Lem opened no fresh "
            "session by itself: “Open a session” on the board starts one"
        ),
    }


def describe(e: dict, m: Model) -> dict:
    """One event as the activity says it: an icon and its actor, a head, a text and a
    line under it."""
    title = title_of(e.get("task"))
    if e.get("event") == "task.state":
        info = STATUS.get(e.get("status", ""), UNKNOWN)
        t = m.by_slug.get(e.get("task"))
        block = {
            "text": "" if e.get("text") is None else str(e["text"]),
            "lines": [str(x) for x in e.get("lines") or []],
        }
        lines = said_of(
            block, talked=talked_before(t, at(e.get("ts")) or 0) if t else False
        )
        return {
            "info": info,
            "head": info["label"],
            "text": lines[0] if lines else "",
            "sub": " · ".join(lines[1:]),
            "title": title,
        }
    if e.get("event") == "gate":
        ok = e.get("exit") == 0
        return {
            "info": {
                "actor": "done" if ok else "bad",
                "icon": "check" if ok else "alert",
            },
            "head": "Check passed" if ok else f"Check failed, exit {e.get('exit')}",
            "text": e.get("command"),
            "sub": e.get("last") or "",
            "title": title,
            "mono": True,
        }
    say = SAYS.get(e.get("event"))
    if (
        e.get("event") == "session.stopped"
        and (t := m.by_slug.get(e.get("task")))
        and stop_over_work(t, e)
    ):
        # the stop of a look that a state block overtook: it never stood, and nothing
        # waited for the owner
        say = stop_over_work_said
    elif (
        e.get("event") == "session.stopped"
        and e.get("unread") is not True
        and (t := m.by_slug.get(e.get("task")))
        and not restarted_before(t, e)
    ):
        # a readable stop over one that already stood: no fresh session was opened
        say = stop_unrestarted_said
    if say:
        said: dict[str, Any] = {"title": title, "sub": "", **say(e)}
        if e.get("from") and e.get("was_at"):
            # a dropped task's event that its resumed task carried over (project.py
            # `resume`), at the time of the resume: it keeps its first time as `was_at`;
            # another event's `from` is its own field (`merge.refused`'s `lem` or
            # `github`, `merge.stands`'s old tip)
            said["sub"] = " · ".join(
                x
                for x in (said["sub"], f"carried over from “{title_of(e['from'])}”")
                if x
            )
        return said
    rest = " · ".join(
        f"{k} {v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)}"
        for k, v in e.items()
        if k not in ("ts", "event", "task")
    )
    return {
        "info": {"actor": "quiet", "icon": "dot"},
        "head": str(e.get("event")),
        "text": rest,
        "sub": "",
        "title": title,
    }


def feed(events: list[dict], newest: int = 200) -> list[tuple[int, dict]]:
    """The newest events, newest first: time sorts, and the order of the log breaks a
    tie, the later first."""
    timed = [
        (ts, i, e) for i, e in enumerate(events) if (ts := at(e.get("ts"))) is not None
    ]
    timed.sort(key=lambda x: (-x[0], -x[1]))
    return [(i, e) for _, i, e in timed[:newest]]


# ---- the board of one task ----

# The tabs of a task, in the order of their keys 1 to 5.
TASK_TABS = ("overview", "criteria", "checks", "timeline", "artifacts")
# The levels of the ladder a decision climbed (stages/ladder.md), in their order, as a
# record's `levels` names them; a level the record names that is not here comes after
# them, by its own name.
LADDER = [
    ("gate", "The question gate"),
    ("lead", "The agent"),
    ("personas", "The personas"),
    ("dialectic", "The dialectic"),
    ("experts", "The experts"),
]
# The levels past the personas: a decision one of them answered, or took, went past
# the personas.
PAST_PERSONAS = ("dialectic", "experts")
# The short label before a colon that a lead writes for an option it took ("D: the
# backlog is patched ...").
OPTION_LABEL = re.compile(r"^([A-Za-z0-9]{1,3}):\s")
# The rows of "Where the time went" of one task: who held the work. A row's color
# repeats a hue of lem.css and never stands alone: each row has its name, and each mark
# its hover.
ROWS = [
    {"key": "you", "label": "You", "fill": "var(--you)"},
    {"key": "lem", "label": "Lem", "fill": "var(--lem)"},
    {"key": "lead", "label": "The agent", "fill": "var(--lead)"},
    {
        "key": "builders",
        "label": "The builders",
        "fill": "color-mix(in srgb, var(--lead) 55%, var(--fg))",
    },
    {"key": "personas", "label": "The personas", "fill": "var(--quiet)"},
    {"key": "checks", "label": "The checks", "fill": "var(--gate)"},
    {
        "key": "review",
        "label": "The review",
        "fill": "color-mix(in srgb, var(--gate) 55%, var(--fg))",
    },
]
NICE_MINUTES = [
    1,
    2,
    5,
    10,
    15,
    20,
    30,
    45,
    60,
    90,
    120,
    180,
    240,
    360,
    480,
    720,
    1080,
    1440,
]


def nice_ceil(ms: float) -> int:
    """A length of an axis that reads well: the next of NICE_MINUTES, or whole days
    past them."""
    found = next((m for m in NICE_MINUTES if m * 60000 >= ms), None)
    return (found if found is not None else -(-int(ms) // 86400000) * 1440) * 60000


def hms(ms: float, now: float) -> str:
    """A clock time to the second, with its date when it is not on the day of `now`."""
    return (
        "" if local(ms).date() == local(now).date() else f"{day_label(ms)} "
    ) + local(ms).strftime("%H:%M:%S")


def tick_label(ms: float, whole: float, now: float) -> str:
    """The label of a tick of a time axis: to the second when the axis spans under six
    minutes, where six ticks of whole minutes would repeat one minute."""
    return hms(ms, now) if whole < 6 * 60000 else stamp(ms, now)


def track_of(t: Task) -> str | None:
    return (
        "fast track"
        if t.lead == "small"
        else track_words(criteria_size(t))
        if criteria_size(t)
        else None
    )


def waits_for(t: Task, waits: list) -> dict | None:
    """What the task waits for, in words: each thing the owner does in it, or what its
    landing waits for, or the task its queue waits for; None when it waits
    for nothing."""
    mine = [w for w in waits if w["t"] is t]
    if mine:
        # a task with a row "no session" is answered where that row says first, never
        # in the session that is gone; the words of its other row (a breaker, a held
        # state, a plan) follow, for the session he opens, and a task with no such row
        # keeps its own words
        gone = next(
            (
                w
                for w in mine
                if w["kind"] == "stopped"
                or (w["kind"] == "session" and not w.get("deaf"))
            ),
            None,
        )
        then = (
            f" {answer_of(t)}"
            if len(mine) > 1
            else ""
            if t.closed
            else f" Or type /lem drop {t.slug} to end it."
        )
        where = answer_of(t) if gone is None else wait_say(gone)["where"] + then
        return {
            "you": True,
            "text": "; ".join(wait_say(w)["verb"] for w in mine),
            "where": where,
        }
    if wait := waits_now(t):
        return {"you": False, "text": waits_say(wait), "where": None}
    after = (
        next(
            (
                line
                for line in said_of(t.blocks[-1])
                if line.startswith("it starts after")
            ),
            None,
        )
        if t.waits_after
        else None
    )
    return {"you": False, "text": cap(after), "where": None} if after else None


def starts_landing(t: Task) -> bool:
    """A landing starts with the rebase onto the base and, for a task that is not on the
    fast track, the polish pass; no event says which runs until the pass ends. A pass of
    an earlier landing still counts."""
    return (
        t.status == "landing"
        and not t.gates
        and not t.polish
        and not t.landing_step
        and not t.checks_end
        and criteria_size(t) != "small"
    )


def step_runs(e: dict) -> str:
    """What runs in a landing whose newest step started and has not ended."""
    return STEP_RUNS.get(e.get("event")) or f"A builder makes {job_of(e) or 'its job'}"


def now_head(t: Task) -> str:  # noqa: C901, PLR0911, PLR0912 - over the limit before the limit was set
    """The head of the large card of a task: what it does now, in words."""
    if t.release_stop and not t.closed:
        return OLDER_RELEASE
    s = t.status
    if s == "queued":
        if t.dropped_after:
            # the task it waited for was dropped, so it waits for his word: the headline
            # says what its row says
            return dropped_head(t.dropped_after)
        # "another task" holds for both reasons of a wait: the task needs its result, or
        # the owner's words put it after it
        return "Waits for another task" if t.waits_after else "Waits to start"
    if s == "building":
        return (
            "Its investigator examines it, before any criterion"
            if t.investigating
            else LEAD[lead_of(t)]["head"]
        )
    if s == "planned":
        return (
            "The plan waits for you"
            if t.for_owner
            else "The plan talk is done: the plan waits for the agent that builds it"
            if t.talks
            else "The plan waits for its plan talk"
        )
    if s == "held":
        return (
            "Approved: its lead has not started yet"
            if t.approved
            else "Helped: its lead has not started yet"
            if t.helped
            # its session's turn runs on what he said (`put_sessions`): a breaker's held
            # task too
            else "Its session works on your answer"
            if t.works
            else "The build stopped: its breaker waits for you"
            if t.breaker
            else "Lem goes on without you"
            if t.goes_on
            else "The personas read the criteria"
            if t.reading
            else "Lem writes the criteria"
            if t.turn == "writes"
            else "Lem asks you whether to skip the personas’ read"
            if t.turn == "skip" and t.need and t.need["need"] == "interview"
            # after the personas' read of an interview's criteria, or his word to skip
            # it, his yes is what waits
            else "The criteria wait for your yes"
            if t.approvable and t.need and t.need["need"] == "interview"
            else "The interview waits for you"
            if t.need and t.need["need"] == "interview"
            else "The criteria wait for your yes"
            if t.criteria_wait
            else "Waits for you"
        )
    if s == PARKED:
        return "Parked: nobody works on it until you bring it back"
    if s == "blocked":
        return (
            (
                "It waits for the base: a task of its own repairs the "
                "check that fails there"
            )
            if t.base_red
            else "Its session stopped: it waits for your word"
        )
    if s == NEW:
        return "Its session opened: it reads the request"
    if s == "ready":
        return "Waits for its checks"
    if s == "landing":
        if waits := waits_now(t):
            return waits_say(waits)
        if starts_landing(t):
            return (
                "It starts its landing: the rebase onto the base, then the polish "
                "pass, before the checks"
            )
        if t.checks_stop:
            return checks_end(t.checks_stop.get("result"))["head"]
        return (
            step_runs(t.landing_step)
            if t.landing_step
            else "The checks and the review run on it"
        )
    if s == "open":
        if waits := waits_now(t):
            return waits_say(waits)
        proposed: dict[str | None, str] = {
            "reads": "Proposed: the merge agent reads it",
            "merges": (
                "Proposed: the merge agent found nothing for you, and Lem merges it"
            ),
            "relands": "Proposed: Lem lands it again on the moved base",
        }
        return proposed.get(t.merge_wait, "Proposed: it waits for your merge")
    return {
        "landed": "Landed",
        "dropped": "Dropped",
        "answered": "Answered: it ended with a report and nothing to merge",
    }.get(s, f'Status "{s}"')


def who_acts(t: Task) -> str:
    """The eyebrow of the large card: who acts now."""
    who = t.info["who"]
    return (
        "You act"
        if who == "You"
        else "Nobody acts"
        if t.status == PARKED
        else "Closed"
        if who == "Nobody"
        else f"{who} acts"
    )


# ---- the criteria and the decisions of one task ----


def whole(criterion: object) -> str:
    """A criterion as the owner approved it, its sentence and the steps of its case:
    criteria.py's own `whole`, so that the board's "as they stand" agrees with what the
    landing calls changed. A recorded change names the same whole in its `was`
    and `now`."""
    criterion = criterion if isinstance(criterion, dict) else {}
    return CRITERIA().whole(
        {
            "text": str(criterion.get("text", "")),
            "case": [str(x) for x in criterion.get("case") or []],
        }
    )


_criteria: ModuleType | None = None


def CRITERIA() -> ModuleType:  # noqa: N802 - it stands for the module
    """criteria.py as a module, loaded once: the board reads a criterion as it does."""
    global _criteria  # noqa: PLW0603 - the module loads criteria.py once and keeps it
    if _criteria is None:
        from lem import criteria

        _criteria = criteria
    return _criteria


def standing(t: Task) -> dict | None:
    """The criteria as they stand: the newest approval's, each as its whole (`whole`:
    the sentence and the steps of its case), with each change recorded after it applied
    in order (decisions.py `changes`), and the digest criteria.py gives these texts when
    an approval holds the same ones (texts compare with each run of spaces as one); None
    before an approval."""
    if not t.approvals:
        return None
    a = t.approvals[-1]
    texts = [whole(st) for st in a["criteria"]]
    charts = [
        st.get("chart")
        if isinstance(st, dict) and isinstance(st.get("chart"), str)
        else None
        for st in a["criteria"]
    ]
    changes = [c for c in t.changes if c["approval"] == a["number"]]
    for c in changes:
        n = (c["criterion"] if isinstance(c["criterion"], int) else 0) - 1
        if c["how"] == "added":
            texts.insert(max(0, n), str(c["now"]))
            charts.insert(max(0, n), None)
        elif c["how"] == "changed":
            if 0 <= n < len(texts):
                texts[n] = str(c["now"])
        elif 0 <= n < len(texts):
            del texts[n]
            del charts[n]

    def same(x: dict) -> bool:
        return (
            x.get("size") == a.get("size")
            and len(x["criteria"]) == len(texts)
            and all(
                flat(whole(st)) == flat(texts[i]) for i, st in enumerate(x["criteria"])
            )
        )

    digest = (
        next((x["digest"] for x in reversed(t.approvals) if same(x)), None)
        if changes
        else a["digest"]
    )
    return {
        "approval": a,
        "texts": texts,
        "charts": charts,
        "changes": changes,
        "digest": digest,
    }


def criteria_sum(t: Task) -> str:
    """The line of the card of the criteria: their track and why."""
    approved = t.approvals[-1] if t.approvals else None
    if t.criteria and not (approved and approved["order"] > t.criteria["order"]):
        return f"{track_words(t.criteria['size'])}, because {t.criteria['why']}"
    return (
        f"{track_words(approved['size'])}, because {approved['why']}"
        if approved
        else ""
    )


def plan_criteria_stand(t: Task) -> bool:
    """Whether the plan's recorded criteria are the contract: criteria approved after
    the lead recorded the plan's (or before it wrote any) are the contract instead."""
    current = standing(t)
    return not (
        current
        and (not t.criteria or current["approval"]["order"] > t.criteria["order"])
    )


def criterion_checks(t: Task) -> list[dict]:
    """Each criterion of the plan with the tests that hold it and what the last check of
    them gave. A result counts only for the criteria and tests it ran on: a criterion or
    a test that changed since has no check yet. `state` is `done` (held by its tests),
    `bad` (a test does not hold it) or `quiet`."""
    red = t.red or {}
    # the board of a task draws these only for a task whose plan wrote its
    # criteria (board_task.py)
    criteria = cast("dict[str, Any]", t.criteria)
    current = bool(red and red.get("digest")) and red["digest"] == criteria["digest"]
    results = {
        (r.get("criterion"), r.get("command")): r
        for r in (red["tests"] if current else [])
        if isinstance(r, dict)
    }
    out = []
    for st in criteria["list"]:
        tests = [x for x in (st.get("tests") or []) if isinstance(x, dict)]
        checked = [results.get((st.get("n"), x.get("command"))) for x in tests]
        bad = any(r and r.get("problem") for r in checked)
        held = bool(tests) and all(r and not r.get("problem") for r in checked)
        said = []
        for x, r in zip(tests, checked, strict=True):
            if r and r.get("problem"):
                said.append((x.get("command"), str(r["problem"])))
            elif r:
                said.append(
                    (
                        x.get("command"),
                        "passes on the branch, fails on the base commit"
                        + (f" (checked on {red['tip']})" if red.get("tip") else ""),
                    )
                )
            else:
                said.append(
                    (
                        x.get("command"),
                        "no check of it is on record"
                        if t.closed
                        else "not checked yet",
                    )
                )
        out.append(
            {
                "n": st.get("n"),
                "text": st.get("text", ""),
                "state": "bad" if bad else "done" if held else "quiet",
                "tests": said,
                "no_test": st.get("no_test"),
                "label": "not held" if bad else "held by its tests" if held else "",
                "case": case_steps(st.get("case")),
                "chart": st.get("chart") if isinstance(st.get("chart"), str) else None,
            }
        )
    return out


def read_stale(t: Task, r: dict) -> str:
    """As land.py `unread` says it: the criteria as they stand are not the ones the read
    read, and what changed them, an approval of the owner's with other criteria or a
    change of the build; "" when they are."""
    st = standing(t)
    if not st:
        return ""
    read = next((x for x in t.approvals if x["digest"] == r["digest"]), None)
    if st["digest"]:
        differ = st["digest"] != r["digest"]
    else:
        differ = (
            not read
            or len(read["criteria"]) != len(st["texts"])
            or any(
                flat(whole(x)) != flat(st["texts"][i])
                for i, x in enumerate(read["criteria"])
            )
        )
    if not differ:
        return ""
    his = next(
        (
            x
            for x in reversed(t.approvals)
            if x["by"] == "owner"
            and x["order"] > r["order"]
            and x["digest"] != r["digest"]
        ),
        None,
    )
    changed = any(c["order"] > r["order"] for c in t.changes)
    parts = [
        p
        for p in (
            his and f" by your approval {his['number']}",
            changed and " by a change of the build",
        )
        if p
    ]
    return (
        f"The criteria changed after this read{' and'.join(parts)}, "
        "and the change was not read."
    )


def taken_over(t: Task, c: dict) -> int | float | None:
    """The number of an approval of the owner's after a change of the build, which made
    that change his (decisions.py `taken_over_by`): it is no cause of not green. None
    when there is none."""
    return next(
        (
            x["number"]
            for x in t.approvals
            if isinstance(x["number"], (int, float))
            and isinstance(c["approval"], (int, float))
            and x["number"] > c["approval"]
            and x["by"] == "owner"
        ),
        None,
    )


def importance(t: Task, d: Decision) -> str | None:
    """Why a decision is important, or None: a `decision N ` line of the newest proposal
    names it (it makes the pull request not green), it went past the personas (the
    dialectic or the experts took it, or answered at their level), no level of the
    ladder settled it (the agent's pick stands), or it is the owner's help on a breaker.
    A breaker is none: it stands on its own row."""
    if d.kind != "taken":
        return None
    named = any(
        str(line).startswith(f"decision {d.id} ")
        for line in (t.proposal or {}).get("reasons", [])
    )
    past = (
        d.by
        if d.by in PAST_PERSONAS
        else next(
            (lv for lv in PAST_PERSONAS if str((d.levels or {}).get(lv) or "").strip()),
            None,
        )
    )
    went = past and (
        f"it went past the personas: {BY_WHOM[d.by]} took it"
        if d.by in PAST_PERSONAS
        else f"it went past the personas: {BY_WHOM[past]} answered it"
    )
    parts = (
        named and "it makes the pull request not green",
        went,
        d.unsettled and "no level of the ladder settled it: the agent’s pick stands",
        d.by == "owner"
        and d.breaker is not None
        and f"it is your help on breaker {d.breaker}",
    )
    return ", and ".join(p for p in parts if p) or None


def important_of(t: Task) -> list:
    return [d for d in t.decided if importance(t, d)]


def chosen_at(d: Decision) -> int:
    """The option a decision took, by its place in its options, or -1: the same text, or
    the same short label before a colon when one option alone has it."""
    if d.chose is None:
        return -1
    if d.chose in d.options:
        return d.options.index(d.chose)
    found = OPTION_LABEL.match(str(d.chose))
    if not found:
        return -1
    hits = [
        i
        for i, option in enumerate(d.options)
        if (m := OPTION_LABEL.match(str(option))) and m[1] == found[1]
    ]
    return hits[0] if len(hits) == 1 else -1


def picked_word(d: Decision) -> str:
    return "the one expert picked it" if len(advisers_of(d)) == 1 else "both picked it"


def decision_says(t: Task, d: Decision) -> dict:
    """What the opened row of a decision says: how and why it was taken and by whom (the
    owner's help on a breaker with his own words), each level of the ladder it climbed,
    and why it is important."""
    if d.by == "owner" and d.breaker is not None:
        how = (
            f"your help on breaker {d.breaker}{f': “{d.words}”' if d.words else ''}, "
            f"because {d.why}"
        )
        who = f"by you, on breaker {d.breaker}"
    elif d.unsettled:
        how = f"the agent’s pick, which no level of the ladder settled, because {d.why}"
        who = "the agent’s pick, which no level settled"
    else:
        how = (
            f"taken by {BY_WHOM.get(d.by, d.by)}"
            f"{f', as {picked_word(d)}' if d.by == 'experts' else ''}"
            f", because {d.why}"
        )
        who = f"by {BY_WHOM.get(d.by, d.by)}"
    if d.copied:
        who = f"{who} · in “{title_of(d.copied)}”"
    known = dict(LADDER)
    levels = (
        (
            [(key, name, str(d.levels[key])) for key, name in LADDER if key in d.levels]
            + [
                (key, cap(key), str(d.levels[key]))
                for key in d.levels
                if key not in known
            ]
        )
        if d.levels
        else []
    )
    return {
        "how": how,
        "who": who,
        "levels": levels,
        "why": importance(t, d),
        "at": chosen_at(d),
    }


def breaker_says(t: Task, d: Decision) -> dict:
    """What the row of a breaker says: why it stopped the build, and where it stands
    now: it waits for the owner, for nobody while the task is parked, it was helped by a
    decision of his, or the task ended."""
    if d.state == "helped":
        now, actor = f"helped by your decision {d.help}", "done"
    elif t.closed:
        now, actor = f"the task is {t.status}: it no longer waits", "quiet"
    elif is_parked(t):
        now, actor = (
            f"the task is parked: it waits for nobody until /lem resume {t.slug}",
            "quiet",
        )
    else:
        now, actor = "it waits for you", "you"
    return {
        "why": stop_words(d),
        "now": now,
        "actor": actor,
        "copied": d.copied
        and f"carried over from “{title_of(d.copied)}”, which was dropped",
    }


def decisions_sum(t: Task) -> str:
    """The line of the card of the decisions: how many were taken, are important, and
    the breakers."""
    if not t.decided:
        return ""
    important = len(important_of(t))
    taken = sum(1 for d in t.decided if d.kind == "taken")
    breakers = sum(1 for d in t.decided if d.kind == "breaker")
    parts = [
        f"{taken} taken" if taken else "",
        f"{important} important" if important else "",
        plural(breakers, "breaker") if breakers else "",
    ]
    return " · ".join(p for p in parts if p)


# ---- the overview of one task ----


def building_of(t: Task, told: dict | None) -> dict | None:
    """ "What we are building": the goal (the reason of the type line), what the owner
    gets (the outcome of its task.md, `told`, as the markdown it was written in: a
    story, a list, a table or a chart reads only so), how many important decisions wait
    for a look, and the backlog items its branch filed. A task whose worktree is gone
    has no line of filed items (`filed` None), nor has a task that ended when git shows
    none. None when there is nothing to say."""
    goal = t.type["why"] if t.type else ""
    outcome = str((told or {}).get("outcome") or "").strip()
    important = len(important_of(t))
    filed = (told or {}).get("filed")
    filed = filed if isinstance(filed, list) and (filed or not t.closed) else None
    if not goal and not outcome and not important and filed is None:
        return None
    return {"goal": goal, "outcome": outcome, "important": important, "filed": filed}


# ---- the pull requests a text names, and the reasons of not green as rows ----

# A pull request a text of the board names: a forge's address of one, `OWNER/REPO#N`, or
# a bare `#N`.
PULL_REF = re.compile(
    r"(?P<url>https?://[^\s<>()\"'`]+?/pull/(?P<n1>\d+))(?![\w/])"
    r"|(?<![\w./-])(?P<repo>[A-Za-z0-9][\w.-]*/[\w.-]+)#(?P<n2>\d+)\b"
    r"|(?<![\w&#/])#(?P<n3>\d+)\b"
)
# The parts of a markdown text a link is never put into: a fenced block, code, a link or
# an autolink.
MD_KEEP = re.compile(
    r"```[\s\S]*?(?:```|\Z)|~~~[\s\S]*?(?:~~~|\Z)|`[^`\n]*`|!?\[[^\]\n]*\]\([^)\n]*\)|<[^>\n]*>"
)
GITHUB = "https://github.com"


def forge_of(m: "Model") -> str | None:
    """The forge's address of the workspace's repository,
    `https://github.com/OWNER/REPO`, from the newest pull request its tasks name; None
    while no task names one, and then a bare `#N` stays text."""
    found = max((t for t in m.tasks if pr_of(t)), key=lambda t: t.last_ts, default=None)
    if found is None:
        return None
    url = (pr_of(found) or {})["url"]
    return url[: url.index("/pull/")]


def pull_refs(text: object, forge: str | None) -> list:
    """A text in parts: each pull request it names as `{"text", "url"}`, every other
    part a str. The one rule of what is a link to a pull request on the board: an
    address of one as it is; `OWNER/REPO#N` on the forge's host (GitHub when none is
    known); a bare `#N` on the workspace's own repository (`forge`), and as text when
    that is not known."""
    text = str(text)
    out: list = []
    at = 0
    for found in PULL_REF.finditer(text):
        if found["url"]:
            url = found["url"]
        elif found["repo"]:
            host = forge[: forge.index("/", len("https://"))] if forge else GITHUB
            url = f"{host}/{found['repo']}/pull/{found['n2']}"
        elif forge:
            url = f"{forge}/pull/{found['n3']}"
        else:
            continue
        out += [text[at : found.start()], {"text": found[0], "url": url}]
        at = found.end()
    out.append(text[at:])
    return [part for part in out if part != ""]


def pull_links_md(text: str, forge: str | None) -> str:
    """A markdown text with each pull request it names as a markdown link (`pull_refs`),
    outside its code, its links and its fenced blocks; an address stays as it is, since
    the reader makes it a link itself."""
    out, at = [], 0

    def linked(part: str) -> str:
        return "".join(
            x
            if isinstance(x, str)
            else x["text"]
            if x["text"].startswith("http")
            else f"[{x['text']}]({x['url']})"
            for x in pull_refs(part, forge)
        )

    for kept in MD_KEEP.finditer(text):
        out += [linked(text[at : kept.start()]), kept[0]]
        at = kept.end()
    out.append(linked(text[at:]))
    return "".join(out)


# Where a reason of not green is cut: a separator of land.py's lines (`not_green`),
# outside quotes, parentheses and code.
OPENS, CLOSES = '(“"`', ')”"`'


def cuts(text: str, seps: tuple[str, ...]) -> list[tuple[int, str]]:
    """Where each separator stands in the text outside parentheses, quotes and code: its
    place and itself."""
    found, depth, quote, i = [], 0, None, 0
    while i < len(text):
        c = text[i]
        if quote:
            if c == quote or (quote == "“" and c == "”"):
                quote = None
        elif c in '"`“':
            quote = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth = max(0, depth - 1)
        elif depth == 0:
            sep = next((x for x in seps if text.startswith(x, i)), None)
            if sep:
                found.append((i, sep))
                i += len(sep)
                continue
        i += 1
    return found


def split_top(text: str, seps: tuple[str, ...]) -> list[str]:
    """The text cut at each separator that stands outside parentheses, quotes
    and code."""
    parts, start = [], 0
    for i, sep in cuts(text, seps):
        parts.append(text[start:i])
        start = i + len(sep)
    parts.append(text[start:])
    return [p.strip() for p in parts if p.strip()]


def reason_parts(line: object) -> dict:
    """One reason of not green as a row: its head, the leading clause of land.py's line
    up to its first `: ` or `. ` ("Decision 4 was taken without the owner"); `about`, a
    parenthesis that closes the head (what the decision was about, the bar's change);
    and `detail`, the rest cut at the line's own separators (`; ` and `. `) outside
    quotes, parentheses and code, each one sentence. `ref` names the decision or the
    breaker the line is about, for a link to it."""
    line = str(line).strip()
    first = cuts(line, (": ", ". "))
    head, rest = (
        (line[: first[0][0]], line[first[0][0] + len(first[0][1]) :])
        if first
        else (line, "")
    )
    about = ""
    depth, cut = 0, None
    for i, c in enumerate(head):
        if c == "(" and depth == 0:
            cut = i
        depth += (c == "(") - (c == ")")
    if cut is not None and cut > 0 and head.rstrip().endswith(")") and depth == 0:
        head, about = head[:cut].strip(), head.rstrip()[cut + 1 : -1].strip()
    detail = [p.rstrip(".") for p in split_top(rest.strip(), ("; ", ". "))]
    ref = re.match(r"^(decision|breaker) (\d+)\b", head)
    return {
        "head": cap(head.strip().rstrip(".:")),
        "about": about,
        "detail": detail,
        "ref": {"kind": ref[1], "id": int(ref[2])} if ref else None,
        "line": line,
    }


def reason_rows(reasons: list) -> list[dict]:
    """The reasons of not green as the board lists them, one row each
    (`reason_parts`)."""
    return [reason_parts(line) for line in reasons]


# ---- the server's look at the forge ----


def forge_due(
    open_prs: list[dict], looked_at: int | None, now: int, every_ms: int, *, forge: bool
) -> list[int]:
    """The pull requests the server asks the forge about now, by their numbers; none
    when no task is open with one, when the workspace has no forge to ask (`forge`
    false: a demo, or no GitHub remote), or when the server's last look (`looked_at`) is
    younger than `every_ms`."""
    if not forge or not open_prs:
        return []
    if looked_at is not None and now - looked_at < every_ms:
        return []
    return sorted({int(x["n"]) for x in open_prs})


def progress_of(t: Task) -> dict:
    """The progress card of a task: its phases with a line under each, the ring of the
    plan's tasks (finished, current, total), and the counts its stats say."""
    ph = phases_of(t)
    p = t.progress
    done = t.reached in ("landed", "ready", "landing", "open")
    total = p["of"] if p else 0
    finished = total if done else max(0, (p["n"] if p else 1) - 1)
    current = 1 if not done and p and t.status == "building" else 0
    review = t.reviews[-1] if t.reviews else None
    lead = 1 if t.investigated else 0
    small = t.lead == "small"

    def phase_sub(k: int) -> str:
        if k == PHASES.index("Build") and p:
            return f"task {p['of'] if done else p['n']} of {p['of']}"
        if k == PHASES.index("Checks") and t.gates:
            return f"{t.gate_bad} red" if t.gate_bad else f"{len(t.gates)} green"
        if k == PHASES.index("Review") and review:
            return str(review["verdict"])
        if k == PHASES.index("Proposed") and t.proposal:
            return "green" if t.proposal["green"] else "not green"
        return ""

    def sub(k: int) -> str:
        if k < lead:
            return (
                CALLS.get(t.investigation["call"], {}).get("card", "")
                if t.investigation
                else ""
            )
        return phase_sub(k - lead + (2 if small else 0))

    taken = sum(1 for d in t.decided if d.kind == "taken")
    past = sum(1 for d in t.decided if d.kind == "taken" and d.by in PAST_PERSONAS)
    breakers = sum(1 for d in t.decided if d.kind == "breaker")
    return {
        **ph,
        "subs": [sub(k) for k in range(len(ph["names"]))],
        "finished": finished,
        "current": current,
        "total": total,
        "review": review,
        "taken": taken,
        "past_personas": past,
        "breakers": breakers,
    }


# ---- where the time of one task went ----


def time_end(t: Task, now: int) -> int:
    """Where the drawing of a task's time stops: its last event when it is closed, a
    coarse clock (15 s) while it is open, so that the drawing holds still between
    two refreshes."""
    if t.closed:
        return max(t.last_ts, at(t.events[-1].get("ts")) or t.last_ts)
    return -(-now // 15000) * 15000


def time_of(t: Task, end: int, meta: dict | None = None) -> dict:  # noqa: C901, PLR0912, PLR0915 - over the limit before the limit was set
    """The spans of one task, each on the row of who held the work (ROWS), the marks of
    what logged only its end, and the bands of the stages behind them, up to `end`. A
    state block starts a span and the next one ends it; a stage whose start is logged
    (the interview, Lem's writing of the criteria after it, the scout, the personas'
    read, the investigation, a builder, the polish pass, the checks, the review:
    SKILL.md) runs from its start to the event that ends it; the criteria wait for the
    owner from the personas' read to his approval; a breaker holds the task for him in
    its held block, and a parked task holds nobody; a plan talk runs from its start to
    its record. A stage whose start is not in the log is a mark where it ended. A
    dropped task's events that a resumed task carried over (`from`) ran in the dropped
    task, so its time leaves them out. Nothing here is a guess at a time no event holds.
    `meta` gives how many commands one run of the checks has (`gates`) and how many
    are serial."""
    meta = meta or {}
    spans: list[dict] = []
    marks: list[dict] = []
    bands: list[dict] = []
    events = t.events
    first_ts = at(events[0].get("ts")) if events else None
    t0 = min(first_ts, t.first) if first_ts is not None else t.first

    def add(  # noqa: PLR0913 - over the limit before the limit was set
        row: str, frm: float, to: float, head: str, sub: str = "", *, live: bool = False
    ) -> None:
        if to > frm or live:
            spans.append(
                {
                    "row": row,
                    "from": frm,
                    "to": max(frm, to),
                    "head": head,
                    "sub": sub,
                    "live": live,
                }
            )

    # each event belongs to the state block it follows in the log, by its place in
    # the log
    block_of: dict[int, int] = {}
    current = -1
    for i, e in enumerate(events):
        if e.get("event") == "task.state":
            current += 1
        else:
            block_of[i] = current

    def block_status(i: int) -> str | None:
        k = block_of.get(i, -1)
        return t.blocks[k]["status"] if 0 <= k < len(t.blocks) else None

    explicit: list[dict] = []
    started_reads: set[int] = set()

    def read_sub(r: dict) -> str:
        families = r.get("families") or []
        return (
            f"{r.get('answered')} of {r.get('asked')} answered, "
            f"{FAMILIES.get(len(families), f'{len(families)} model families')} · "
            f"{_flagged_words(r.get('flagged'))}"
            f"{' · the families split' if r.get('split') else ''}"
        )

    def pair(  # noqa: PLR0913, PLR0917 - over the limit before the limit was set
        i: int,
        e: dict,
        row: str,
        head: str,
        sub: str | Callable[[dict], str],
        ends: Callable[[dict], bool],
    ) -> int | None:
        stop = next((j for j in range(i + 1, len(events)) if ends(events[j])), None)
        if stop is not None:
            explicit.append(
                {
                    "row": row,
                    "from": at(e.get("ts")),
                    "to": at(events[stop].get("ts")),
                    "head": head,
                    "sub": sub(events[stop]) if callable(sub) else sub,
                    "live": False,
                }
            )
        elif not t.closed:
            explicit.append(
                {
                    "row": row,
                    "from": at(e.get("ts")),
                    "to": end,
                    "head": head,
                    "sub": "it runs" if callable(sub) else sub,
                    "live": True,
                }
            )
        else:
            marks.append(
                {
                    "row": row,
                    "at": at(e.get("ts")),
                    "head": f"{head}: its start",
                    "sub": "no event of its end is logged",
                }
            )
        return stop

    for i, e in enumerate(events):
        ev = e.get("event")
        if e.get("from"):
            continue
        if ev == "interview.start":
            pair(
                i,
                e,
                "you",
                "The interview",
                "Lem asks you one question at a time",
                lambda x: x.get("event") == "interview.end",
            )
        elif ev == "interview.end":
            pair(
                i,
                e,
                "lem",
                "Lem writes the criteria",
                "from your answers and what the code says",
                lambda x: (
                    x.get("event")
                    in ("read.skip.asked", "criteria.read.start", "criteria.approved")
                ),
            )
        elif ev == "scout.start":
            pair(
                i,
                e,
                "builders",
                "The scout reads the code",
                "for the facts the criteria need",
                lambda x: x.get("event") == "scout",
            )
        elif ev == "criteria.read.start":
            stop = pair(
                i,
                e,
                "personas",
                "The personas’ read of the criteria",
                read_sub,
                lambda x: x.get("event") == "criteria.read",
            )
            if stop is not None:
                started_reads.add(stop)
        elif ev == "investigation.start":
            pair(
                i,
                e,
                "builders",
                "The investigation",
                "an investigator reproduces the bug and finds its cause"
                if e.get("type") == "fix"
                else "an investigator finds the answer",
                lambda x: x.get("event") == "investigation",
            )
        elif ev == "builder.start" and block_status(i) != "landing":
            pair(
                i,
                e,
                "builders",
                cap(str(job_of(e) or "a job")),
                "a fresh builder; its span ends at the next state block",
                lambda x: (
                    x.get("event") == "task.state"
                    or x.get("event") in LANDING_STARTS
                    or x.get("event") in CHECKS
                ),
            )
    spans.extend(explicit)

    def add_block(  # noqa: PLR0913 - over the limit before the limit was set
        row: str,
        frm: float,
        to: float,
        head: str,
        sub: str,
        *,
        open_: bool,
        coord: str | None = None,
    ) -> None:
        """A state block's span with the time of the stages above left out. When the
        block is a builder's work and a builder's start is logged in it, the rest of it
        is the coordinator's (`coord`: the agent of the task, or Lem): the brief before
        the builder starts, the report after it ends."""
        cover = sorted(
            [max(frm, x["from"]), min(to, x["to"])]
            for x in explicit
            if x["from"] < to and x["to"] > frm
        )
        if not cover:
            add(row, frm, to, head, sub, live=open_)
            return
        cur, pieces = frm, []
        for a0, b0 in cover:
            if a0 > cur:
                pieces.append((cur, a0))
            cur = max(cur, b0)
        if cur < to:
            pieces.append((cur, to))
        own = coord and any(
            x["row"] == "builders" and frm <= x["from"] < to for x in explicit
        )
        for a0, b0 in pieces:
            if not own or not coord:
                add(row, a0, b0, head, sub, live=open_ and b0 == to)
            else:
                before_ = a0 < cover[0][0]
                said = (
                    (
                        "It briefs the builder"
                        if coord == "lead"
                        else "Lem starts the builder"
                    )
                    if before_
                    else (
                        "It reads the builder’s report"
                        if coord == "lead"
                        else "Lem reads the report"
                    )
                )
                add(coord, a0, b0, said, sub, live=open_ and b0 == to)

    gates = (
        meta.get("gates")
        if isinstance(meta.get("gates"), int)
        and not isinstance(meta.get("gates"), bool)
        and meta.get("gates") > 0
        else None
    )
    serial_n = (
        meta.get("serial")
        if isinstance(meta.get("serial"), int)
        and not isinstance(meta.get("serial"), bool)
        else 0
    )

    def same_tip(a: object, b: object) -> bool:
        return bool(a and b) and (
            str(a).startswith(str(b)) or str(b).startswith(str(a))
        )

    def landing(k: int, frm: float, to: float, *, open_: bool) -> None:  # noqa: C901, PLR0912, PLR0915 - over the limit before the limit was set
        """The landing, cut by the events of its checks and its review: each piece
        belongs to the event that ends it. A step whose start is logged starts its piece
        there, and the time before it is Lem's: the rebase onto the base before the
        first step, and Lem between two steps after it. One run of the gate is its
        commands on one tip, in order: a repair shows only as a run on another tip after
        a failed run, a failed check of the criteria or a must-fix, or as a builder's
        start. A run of the checks ends at its `gate.end`, however it ended. A run that
        took the polish pass's result of the criteria's tests logs no `task.red`: its
        `gate.end` names the pass's commit (`taken`), and the span of the criteria's
        tests is drawn from it."""
        inside = [
            e
            for i, e in enumerate(events)
            if block_of.get(i) == k
            and (e.get("event") in CHECKS or e.get("event") in LANDING_STARTS)
        ]
        stepped = any(e.get("event") in LANDING_STARTS for e in inside)
        run: dict[str, Any] | None
        prev: float
        before: dict | None
        opened: dict | None
        checks: dict[str, Any] | None
        polished: dict | None
        run, owed, prev, before, opened, checks, polished = (
            None,
            False,
            frm,
            None,
            None,
            None,
            None,
        )

        def job(e: dict) -> str:
            return cap(str(job_of(e) or "a job"))

        for e in inside:
            # `derive` keeps only the events whose time reads
            x = cast("int", at(e.get("ts")))
            ev = e.get("event")
            if ev == "gate.start":
                checks = {
                    "total": e["commands"]
                    if isinstance(e.get("commands"), int)
                    else gates,
                    "done": 0,
                }
            if ev in LANDING_STARTS:
                if opened and opened.get("event") == "builder.start":
                    add(
                        "builders",
                        prev,
                        x,
                        job(opened),
                        "a builder of the landing; its span ends at the next step",
                    )
                elif not before:
                    add(
                        "lem",
                        prev,
                        x,
                        "The rebase onto the base",
                        "Lem rebases the branch before the first step of the landing",
                    )
                else:
                    add("lem", prev, x, "Lem, between two steps of the landing")
                opened, prev, before = e, x, e
                continue
            if opened and opened.get("event") == "builder.start":
                add(
                    "builders",
                    prev,
                    x,
                    job(opened),
                    "a builder of the landing; its span ends at the next step",
                )
                prev = x
            started = bool(before) and before.get("event") in LANDING_STARTS
            repairing = False
            if ev == "polish":
                add(
                    "builders",
                    prev,
                    x,
                    "The polish pass",
                    (
                        f"{e.get('before') or '?'} → {e.get('after') or '?'} · "
                        f"{plural(e.get('commits') or 0, 'commit')}"
                    ),
                )
                run, owed, prev, before, opened, polished = None, False, x, e, None, e
                continue
            if ev == "gate":
                if not run or run["done"] or not same_tip(run["tip"], e.get("tip")):
                    repairing = (
                        not started
                        and bool(run)
                        and not same_tip(run["tip"], e.get("tip"))
                        and (run["failed"] or owed)
                    )
                    if not run or not same_tip(run["tip"], e.get("tip")):
                        owed = False
                    run = {
                        "tip": e.get("tip"),
                        "count": 0,
                        "plain": 0,
                        "failed": False,
                        "done": False,
                    }
                run["count"] += 1
                if not e.get("serial"):
                    run["plain"] += 1
                run["failed"] = run["failed"] or e.get("exit") != 0
                run["done"] = gates is not None and (
                    run["count"] >= gates
                    or (
                        run["failed"]
                        and not e.get("serial")
                        and run["plain"] >= gates - serial_n
                    )
                )
                if checks:
                    checks["done"] += 1
            elif ev == "task.red":
                repairing = (
                    not started
                    and bool(owed or (run and run["failed"]))
                    and bool(run)
                    and not same_tip(run["tip"], e.get("tip"))
                )
                if not e.get("ok"):
                    owed = True
            elif ev == "review" and e.get("verdict") == "must-fix":
                owed = True
            if repairing:
                add(
                    "builders",
                    prev,
                    x,
                    "A repair, and the checks again",
                    "no event tells the repair from the checks",
                )
            elif ev == "gate":
                add(
                    "checks",
                    prev,
                    x,
                    f"The checks: {e.get('command') or 'a command'}",
                    f"green · {e.get('last') or ''}"
                    if e.get("exit") == 0
                    else f"exit {e.get('exit')} · {e.get('last') or ''}",
                )
            elif ev == "task.red":
                add(
                    "checks",
                    prev,
                    x,
                    "The tests of the criteria, on the branch and on the base commit",
                    "each test holds its criterion"
                    if e.get("ok")
                    else "a test does not hold its criterion",
                )
            elif ev == "gate.end":
                if e.get("taken"):
                    # drawn also with no width: it is the one place that says where the
                    # criteria's result came from
                    spans.append(
                        {
                            "row": "checks",
                            "from": prev,
                            "to": max(prev, x),
                            "live": False,
                            "head": (
                                "The tests of the criteria, taken from the "
                                f"polish pass at {e['taken']}"
                            ),
                            "sub": (
                                "not run again: the pass ran them on this commit, "
                                "with the same inputs"
                            ),
                        }
                    )
                    prev = max(prev, x)
                # drawn also with no width: a refusal often shares its second with the
                # event before it, and its head is the one place that says how the run
                # ended a run stopped while it waited for the load or its turn logs its
                # `gate.end` and no `gate.start`
                waited = checks is None and e.get("result") == "stopped"
                sub = [
                    refused_of(e) if e.get("result") == "refused" else "",
                    "stopped while they waited, before their first command"
                    if waited
                    else "",
                    f"{checks['done']} of {plural(checks['total'], 'command')} done"
                    if checks and checks["total"] is not None
                    else "",
                    span(e["seconds"] * 1000)
                    if isinstance(e.get("seconds"), (int, float))
                    and not isinstance(e.get("seconds"), bool)
                    and not waited
                    else "",
                ]
                spans.append(
                    {
                        "row": "checks",
                        "from": prev,
                        "to": max(prev, x),
                        "head": checks_end(e.get("result"))["head"],
                        "sub": " · ".join(s for s in sub if s),
                        "live": False,
                    }
                )
                checks = None
            elif ev == "review":
                head = (
                    "Review of the conflict’s resolution"
                    if e.get("of") == "resolution"
                    else f"Review round {e.get('round') or '?'}"
                )
                answered = e.get("answered") or []
                answered_say = (
                    " · answered: " + ", ".join(map(str, answered)) if answered else ""
                )
                add(
                    "review",
                    prev,
                    x,
                    f"{head}: {KIND.get(e.get('kind'), e.get('kind'))}",
                    f"{e.get('verdict')}{answered_say}",
                )
            elif ev == "review.filed":
                add(
                    "lem",
                    prev,
                    x,
                    "Lem files the defects outside the change",
                    plural(len(e.get("items") or []), "item"),
                )
            else:
                add(
                    "lem",
                    prev,
                    x,
                    "Lem writes the pull request",
                    "green" if e.get("green") else "not green",
                )
            prev, before, opened = x, e, None
        last = before.get("event") if before else None
        if open_:
            # the newest step, which every branch below that reads it has (`last`)
            step = before or {}
            after_failure = (
                "lem",
                "After a failed check: a repair or a stop, and no event says which yet",
            )
            between = ("lem", "Lem, between two steps of the landing")
            if last == "builder.start":
                row, head = "builders", job(step)
            elif last == "polish.start":
                row, head = "builders", "The polish pass runs"
            elif last == "gate.start":
                row, head = (
                    "checks",
                    f"The checks run: 0 of {gates} commands done"
                    if gates
                    else "The checks run",
                )
            elif last == "gate.end":
                row, head = "lem", checks_end(step.get("result"))["after"]
            elif last == "review.start":
                floor = KIND.get(step.get("floor"), step.get("floor") or "its floor")
                row, head = "review", f"The review runs: {floor}"
            elif not last:
                row, head = (
                    (
                        "lem",
                        (
                            "The landing starts: the rebase onto the base, then the "
                            "polish pass, and no event says which runs yet"
                        ),
                    )
                    if starts_landing(t)
                    else ("checks", "The checks run")
                )
            elif last == "polish":
                row, head = between if stepped else ("checks", "The checks run")
            elif last == "gate":
                # a gate event always starts or counts a run
                run = cast("dict[str, Any]", run)
                if run["failed"] and run["done"]:
                    row, head = after_failure
                elif run["failed"] and gates is None:
                    row, head = (
                        "lem",
                        (
                            "A command of this run failed: the next command, a repair "
                            "or a stop, and no event says which yet"
                        ),
                    )
                elif (
                    run["done"]
                    and polished
                    and polished.get("commits")
                    and same_tip(polished.get("after"), run["tip"])
                ):
                    # the checks take the pass's result when its run's inputs are still
                    # the same, and run the tests otherwise
                    row, head = (
                        "checks",
                        (
                            "The checks read the criteria again: the polish pass's "
                            f"result at {run['tip']} is taken, or the tests "
                            "run when an input changed"
                        ),
                    )
                elif run["done"]:
                    row, head = "checks", "The tests of the criteria run"
                else:
                    row, head = (
                        "checks",
                        (
                            f"The checks run: {run['count']} of {gates} commands "
                            f"done{', one failed' if run['failed'] else ''}"
                        )
                        if gates
                        else "The checks run",
                    )
            elif last == "task.red":
                row, head = (
                    (
                        between
                        if stepped
                        else (
                            "review",
                            "The review runs; its event comes when it is written down",
                        )
                    )
                    if step.get("ok")
                    else after_failure
                )
            elif last == "review" and step.get("verdict") == "must-fix":
                row, head = "builders", "A repair after the review’s must-fix"
            else:
                row, head = "lem", "Lem files and proposes"
            add(row, prev, end, head, "", live=True)
        elif opened and opened.get("event") == "builder.start":
            add(
                "builders",
                prev,
                to,
                job(opened),
                "a builder of the landing; its span ends at the next state block",
            )
        else:
            add(
                "lem",
                prev,
                to,
                "Lem, after the checks and the review"
                if last
                else "The landing, with no check on record",
            )

    saw_task = False
    stage: dict | None = None

    def stage_of(b: dict) -> dict:  # noqa: PLR0911 - over the limit before the limit was set
        nonlocal saw_task
        task = task_line(b)
        if task:
            saw_task = True
            return {
                "key": f"task-{task[1]}",
                "label": f"Task {task[1]}",
                "short": f"T{task[1]}",
                "sub": f"of {task[2]}",
            }
        if investigates(b):
            return {"key": "investigation", "label": "Investigation", "short": "Inv."}
        if small_block(b):
            return {"key": "change", "label": "The change", "short": "Change"}
        if b["status"] == "building":
            return (
                {"key": "build", "label": "Build", "short": "Build"}
                if saw_task
                else {"key": "plan", "label": "Plan", "short": "Plan"}
            )
        if b["status"] == "planned":
            return {"key": "plan", "label": "Plan", "short": "Plan"}
        if b["status"] == "queued":
            return {"key": "queued", "label": "Queued", "short": "Queued"}
        if b["status"] in ("ready", "landing"):
            return {"key": "checks", "label": "Checks and review", "short": "Checks"}
        if b["status"] == "open":
            return {"key": "pr", "label": "Pull request", "short": "PR"}
        # a held or blocked task stays in the stage it was in; criteria that wait come
        # before any plan
        return stage or {
            "key": "criteria",
            "label": "Acceptance criteria",
            "short": "Criteria",
        }

    def band(st: dict, frm: float, to: float, *, live: bool) -> None:
        prev = bands[-1] if bands else None
        if prev and prev["key"] == st["key"] and prev["to"] == frm:
            prev["to"], prev["live"] = to, live
        else:
            bands.append({**st, "from": frm, "to": to, "live": live})

    if t0 < t.first:
        band(
            {"key": "criteria", "label": "Acceptance criteria", "short": "Criteria"},
            t0,
            t.first,
            live=False,
        )

    for k, b in enumerate(t.blocks):
        nxt = t.blocks[k + 1]["ts"] if k + 1 < len(t.blocks) else None
        open_ = nxt is None and not t.closed
        frm = b["ts"]
        to = nxt if nxt is not None else (end if open_ else b["ts"])
        task = task_line(b)
        what = " · ".join(said_of(b, talked=talked_before(t, b["ts"])))
        s = b["status"]
        if s not in ENDED and s in STATUS:
            stage = stage_of(b)
            band(stage, frm, to, live=open_)
        if s == "queued":
            add_block(
                "lem",
                frm,
                to,
                "Queued: it waits for another task"
                if waits_for_task(b)
                else "Queued: it waits to start",
                what,
                open_=open_,
            )
        elif s == "building" and task:
            add_block(
                "builders",
                frm,
                to,
                f"Task {task[1]} of {task[2]}",
                what,
                open_=open_,
                coord="lead",
            )
        elif investigates(b):
            add_block(
                "builders", frm, to, "The investigation", what, open_=open_, coord="lem"
            )
        elif small_block(b):
            add_block(
                "builders",
                frm,
                to,
                "One builder makes the change",
                what,
                open_=open_,
                coord="lem",
            )
        elif s == "building":
            add_block("lead", frm, to, "It plans the task", what, open_=open_)
        elif s == "planned":
            owner = bool(re.search(r"\bowner\b", b["text"]))
            head = (
                "The plan waits for you"
                if owner
                else (
                    "The plan talk is done: the plan waits for the agent that builds it"
                )
                if any(x["ts"] <= b["ts"] for x in t.talks)
                else "The plan waits for its plan talk"
            )
            add_block("you" if owner else "lem", frm, to, head, what, open_=open_)
        elif s == "held":
            head = (
                "The criteria wait for your yes"
                if CRITERIA_WAIT.search(what)
                else "The build stopped: its breaker waits for you"
                if BREAKER_WAIT.fullmatch(b["text"])
                else "It waits for you"
            )
            add_block("you", frm, to, head, what, open_=open_)
        elif s == "blocked":
            red = BASE_RED in [line.strip() for line in lines_of(b)]
            add_block(
                "lem" if red else "you",
                frm,
                to,
                "Blocked: it waits for the base to be green again"
                if red
                else "Blocked: it waits for your word",
                what,
                open_=open_,
            )
        elif s == "ready":
            add_block(
                "lem", frm, to, "Ready: it waits for its checks", what, open_=open_
            )
        elif s == "landing":
            landing(k, frm, to, open_=open_)
        elif s == "open":
            add_block("you", frm, to, "It waits for your merge", what, open_=open_)

    # the criteria wait for his yes from the personas' read to his approval after it; a
    # yes he gave before the read was in, and a fast-track criterion Lem approved in his
    # name, cost him no wait
    since = float("-inf")
    for a in t.approvals:
        read = [r for r in t.reads if since < r["order"] < a["order"]]
        if a["by"] == "owner" and read:
            r = read[-1]
            add(
                "you",
                r["ts"],
                a["ts"],
                "The criteria waited for your yes",
                "from the personas’ read to your approval"
                f"{' · the read found a doubt' if r['flagged'] or r['split'] else ''}",
            )
        since = a["order"]
    for r in t.reads:
        if r["order"] - 1 in started_reads:
            continue
        families = r["families"]
        fam = FAMILIES.get(len(families), f"{len(families)} model families")
        sub = (
            f"nobody of {r['asked']} answered · its start is not logged"
            if not r["answered"]
            else (
                f"{r['answered']} of {r['asked']} answered, {fam} · "
                f"{_flagged_words(r['flagged'])}"
                f"{' · the families split' if r['split'] else ''}"
                " · its start is not logged"
            )
        )
        marks.append(
            {
                "row": "personas",
                "at": r["ts"],
                "head": "The personas’ read of the criteria ended",
                "sub": sub,
            }
        )
    # a plan talk is the review's from its start to its record; a record with no start
    # is a dot where it ended
    for talk in t.talks:
        sub = f"with {talk['reviewer']}: {talk_counts(talk)}"
        if talk["start"] is not None:
            add("review", talk["start"], talk["ts"], "The plan talk", sub)
        else:
            marks.append(
                {
                    "row": "review",
                    "at": talk["ts"],
                    "head": "The plan talk ended",
                    "sub": f"{sub} · its start is not logged",
                }
            )
    if t.talk_start and not t.closed:
        add(
            "review",
            t.talk_start["ts"],
            end,
            "The plan talk runs",
            f"with {t.talk_start['reviewer']}; its record comes when the talk ends",
            live=True,
        )
    elif t.talk_start:
        marks.append(
            {
                "row": "review",
                "at": t.talk_start["ts"],
                "head": "The plan talk started",
                "sub": (
                    f"with {t.talk_start['reviewer']}; no record of its end is logged"
                ),
            }
        )
    for i, e in enumerate(events):
        # the check the lead runs before the task is ready; the landing's own is a
        # span above
        if e.get("event") == "task.red" and block_status(i) != "landing":
            marks.append(
                {
                    "row": "checks",
                    "at": at(e.get("ts")),
                    "head": "The tests of the criteria, checked before the landing",
                    "sub": "each test holds its criterion"
                    if e.get("ok")
                    else "a test does not hold its criterion",
                }
            )

    # the total of each row is the time it held the work: two spans of one row that
    # overlap count once
    totals = {}
    for row in ROWS:
        parts = sorted(
            [max(t0, x["from"]), min(end, end if x["live"] else x["to"])]
            for x in spans
            if x["row"] == row["key"]
        )
        total, reach = 0, float("-inf")
        for a0, b0 in parts:
            if b0 > a0 and b0 > reach:
                total += b0 - max(a0, reach)
                reach = b0
        totals[row["key"]] = total
    return {
        "t0": t0,
        "end": end,
        "spans": spans,
        "marks": [x for x in marks if x["at"] is not None and t0 <= x["at"] <= end],
        "bands": bands,
        "totals": totals,
        "whole": max(1, end - t0),
    }


def time_rows(tm: dict) -> list[dict]:
    """The rows a task's time card draws: "You" always, and every other row that holds a
    span or a mark."""
    return [
        r
        for r in ROWS
        if r["key"] == "you"
        or any(x["row"] == r["key"] for x in tm["spans"])
        or any(x["row"] == r["key"] for x in tm["marks"])
    ]


# A row's share of a task's time is in percent of it (`time_shares`).
PERCENT = 100


def time_shares(tm: dict, rows: list[dict]) -> dict:
    """Each row's total and its share of the task's time, and whether the shares as
    shown add up past 100: two rows can hold the same minutes (a builder's span inside
    the agent's, the owner's wait for the criteria beside the personas' read), so
    rows overlap."""
    held = [r for r in rows if tm["totals"].get(r["key"], 0) > 0]
    share = {
        r["key"]: math.floor(PERCENT * tm["totals"][r["key"]] / tm["whole"] + 0.5)
        for r in held
    }
    raw = sum(tm["totals"][r["key"]] for r in held)
    shown = sum(share.values())
    return {
        "held": held,
        "share": share,
        "over": shown if raw > tm["whole"] * 1.005 and shown > PERCENT else None,
    }


# ---- the loaders: the files a workspace's model is made from ----


# The bad lines of the log that the page's status bar names before "and N
# more" (`Reader.read_log`).
BAD_LINES_SHOWN = 3


def log_version(inode: int, lines: int) -> str:
    """The version of the event log a page saw, as the stream's `id:` says it: the log's
    inode and its count of whole lines, in one id. `lem project prune` puts a new log in
    place (a new inode), so a page that saw the old one, whatever the count now, is told
    by the id that it is behind (serve.py `refreshes`)."""
    return f"{inode}-{lines}"


def cards_look(state: Path, m: Model) -> dict:
    """The open `lem-ask` cards of each task (`Model.cards`): each card the log names
    with no end in it (`Task.cards`) whose folder holds no end file,
    `cards/PAGEID.end.json` (lem_cards), with the agterm session its `cards/PAGEID.json`
    names. A card whose files do not read has no row: its session still waits for it at
    the Mac."""
    out: dict[str, list[dict]] = {}
    for t in m.tasks:
        if t.closed or not t.cards:
            continue
        folder = state / "tasks" / t.slug
        for page, c in sorted(t.cards.items(), key=lambda item: item[1]["ts"]):
            try:
                if lem_cards.end_file(folder, page).exists():
                    continue
                card = lem_cards.card(folder, page)
            except (lem_cards.CardError, OSError):
                continue
            if not isinstance(card, dict):
                continue
            questions = (
                card.get("questions") if isinstance(card.get("questions"), list) else []
            )
            first = questions[0] if questions and isinstance(questions[0], dict) else {}
            out.setdefault(t.slug, []).append(
                {
                    "page": page,
                    "prompt": str(first.get("prompt") or c["prompt"]),
                    "since": c["ts"],
                    "session": card.get("session"),
                    "chat": card.get("chat") is not False,
                }
            )
    return out


def task_files_look(state: Path, m: Model) -> None:
    """What each open task's directory says beside the log, put on its Task: the release
    it began on (`began`, lem_release's mark) and whether that is older than the board's
    own (`behind`), and whether a change of its criteria from the owner's note stopped
    in the middle (`changing`: `criteria-before.json` names the newest state block, as
    criteria.py `cmd_change` reads it), which makes no yes count (`approvable` false)
    until the change ends with its held block (logged decision 5 of
    criteria-change-asks-again). A release that cannot be told, the board's or the
    task's, counts as behind: the owner answers in the task's session, as on a task of
    an older release. Run at each look: `approvable` comes back from the log's own value
    each time."""
    try:
        running = lem_release.numbers(lem_release.running())
    except ValueError:
        running = None
    for t in m.tasks:
        if t.closed or not t.blocks:
            continue
        folder = state / "tasks" / t.slug
        try:
            t.began = lem_release.began_on(folder)
        except (ValueError, OSError):
            t.began = None
        began = lem_release.numbers(t.began) if t.began else None
        t.behind = running is None or began is None or began < running
        kept = None
        with contextlib.suppress(OSError, ValueError):
            kept = json.loads((folder / CRITERIA_BEFORE).read_text(encoding="utf-8"))
        t.changing = (
            t.status == "held"
            and isinstance(kept, dict)
            and at(kept.get("ts")) == t.blocks[-1]["ts"]
        )
        t.approvable = t.approvable_events and not t.changing


def change_of(t: Task, waiting: dict | None) -> dict | None:
    """The change of the task's criteria from the owner's note that waits for his yes
    now, as its card shows it, or None: while the newest held block is the change's
    (CHANGED_CRITERIA), the text before the change (WAITING's `before`, from
    `criteria-before.json`) and the one that waits (WAITING's `text`, the bytes of its
    digest), paired by criteria.py `change_of` (`before`, `after`, `pairs`). When they
    do not read, the pairs are none and `error` says why."""
    if (
        t.text != CHANGED_CRITERIA
        or not waiting
        or not isinstance(waiting.get("before"), str)
    ):
        return None
    try:
        return CRITERIA().change_of(waiting["before"], waiting["text"])
    except CRITERIA().CriteriaError as error:
        return {"before": [], "after": [], "pairs": [], "error": str(error)}


def answers_look(state: Path, m: Model) -> dict:
    """The answer on record of each task's row that the board answers with its own
    buttons (`Model.answers`): for each task with such a row now (`answer_row`), the
    record of its key in the task's folder, when there is one (lem_answers). A record
    that does not read hides nothing: the row stays his."""
    out: dict[str, dict] = {}
    for t in m.tasks:
        row = answer_row(t)
        if row is None:
            continue
        try:
            found = lem_answers.on_record(state / "tasks" / t.slug, row["key"])
        except (lem_answers.AnswerError, OSError):
            continue
        if isinstance(found, dict):
            out[t.slug] = {row["key"]: found}
    return out


class Reader:
    """The facts of one workspace, read again only where a file changed: the event log
    read on from where the last read stopped, the owner's mark, and the settings, the
    meta facts and the backlog at most once in `settle_seconds` (they ask git).
    `problems` holds what did not read, in words for the page's status bar."""

    def __init__(self, root: Path, state: Path, settle_seconds: float = 5.0) -> None:
        self.root, self.state = root, state
        self.settle_seconds = settle_seconds
        self.lock = threading.Lock()
        self.events: list[dict] = []
        self.log_at: tuple = (0, 0)
        self.log_bad: list[str] = []
        # the whole lines of the log read so far, blank and bad ones too: the count
        # of `log_version`
        self.log_lines = 0
        self.read_at = 0
        self.stamps: dict[str, object] = {}
        self.owner: list[dict] = []
        self.settings: dict | None = None
        self.settings_at = 0.0
        self.meta: dict = {}
        self.backlog: dict | None = None
        self.backlog_at = 0.0
        self.problems: dict[str, str] = {}
        self.model_key: tuple | None = None
        self.model: Model | None = None
        self.forge: dict | None = None
        self.inbox: dict | None = None

    # each loader keeps its last good read, and says what failed in `problems`

    def read_log(self) -> None:  # noqa: C901 - over the limit before the limit was set
        """The log read on from where the last read stopped, or from its start when it
        is another file (`lem project prune` puts a new one in place, with a new inode)
        or shrank. The inode and the size are the ones of the file this read holds open
        (`os.fstat`), so a replace between a look at the name and the open never reads
        the new file from the old one's offset."""
        file = self.state / "events.jsonl"
        try:
            handle = file.open("rb")
        except FileNotFoundError:
            self.events, self.log_at, self.log_bad, self.log_lines = [], (0, 0), [], 0
            self.problems.pop("events", None)
            return
        except OSError as error:
            self.problems["events"] = f"events.jsonl cannot be read ({error.strerror})"
            return
        with handle:
            try:
                facts = os.fstat(handle.fileno())
                same = (
                    self.log_at[0] == facts.st_ino and facts.st_size >= self.log_at[1]
                )
                start = self.log_at[1] if same else 0
                if start == facts.st_size and same:
                    return
                handle.seek(start)
                data = handle.read(facts.st_size - start)
            except OSError as error:
                self.problems["events"] = (
                    f"events.jsonl cannot be read ({error.strerror})"
                )
                return
        # only whole lines: a line that is being written is read at the next look
        whole = data.rfind(b"\n") + 1
        if not same:
            self.events, self.log_bad, self.log_lines = [], [], 0
        number = len(self.events) + len(self.log_bad)
        for raw in data[:whole].split(b"\n")[:-1]:
            number += 1
            if not raw.strip():
                continue
            try:
                record = json.loads(raw)
            except ValueError:
                self.log_bad.append(f"line {number}")
                continue
            if not isinstance(record, dict) or at(record.get("ts")) is None:
                self.log_bad.append(f"line {number}")
                continue
            self.events.append(record)
        self.log_lines += data[:whole].count(b"\n")
        self.log_at = (facts.st_ino, start + whole)
        self.read_at = now_ms()
        if self.log_bad:
            shown = ", ".join(self.log_bad[:BAD_LINES_SHOWN]) + (
                f" and {len(self.log_bad) - BAD_LINES_SHOWN} more"
                if len(self.log_bad) > BAD_LINES_SHOWN
                else ""
            )
            self.problems["events"] = (
                f"events.jsonl: {shown} {'is' if len(self.log_bad) == 1 else 'are'} no "
                "event with a time, and the board leaves "
                f"{'it' if len(self.log_bad) == 1 else 'them'} out"
            )
        else:
            self.problems.pop("events", None)

    def log_id(self) -> str:
        """The version of the log this reader read (`log_version`), which a page gives
        its stream."""
        return log_version(self.log_at[0], self.log_lines)

    def changed(self, key: str, path: Path) -> bool:
        try:
            facts = path.stat()
            stamp_ = (facts.st_ino, facts.st_size, facts.st_mtime_ns)
        except OSError:
            stamp_ = None
        if self.stamps.get(key, ()) == stamp_:
            return False
        self.stamps[key] = stamp_
        return True

    def read_owner(self, project: ModuleType) -> None:
        lem_state = project.lem_state
        try:
            mark = lem_state.owner_mark()
        except lem_state.StateError as error:
            self.problems["owner"] = str(error)
            return
        if not self.changed("owner", mark):
            return
        try:
            self.owner = project.owner_records()
            self.problems.pop("owner", None)
        except project.SettingsError as error:
            self.problems["owner"] = f"the owner's status does not read: {error}"

    def read_settings(self, board: ModuleType) -> None:
        if (
            self.settings is not None
            and time.monotonic() - self.settings_at < self.settle_seconds
        ):
            return
        try:
            self.settings = board.lem_project.load(self.root)
            self.meta = board.meta_of(self.settings, self.state)
            self.problems.pop("settings", None)
        except (
            board.lem_project.SettingsError,
            OSError,
            KeyError,
            ValueError,
        ) as error:
            self.problems["settings"] = f"the settings do not read: {error}"
        self.settings_at = time.monotonic()

    def read_backlog(self, board: ModuleType, *, fresh: bool = False) -> dict | None:
        """The backlog's items as `board.backlog` reads them, at most once in
        `settle_seconds`, or now with `fresh`, when a file of its folder or of the
        reviewer's folder changed (a name, a size or a time), or when the event log
        grew, since a task's start, landing or drop changes which reviewer's item a
        task holds."""
        with self.lock:
            self.read_settings(board)
            if self.settings is None:
                return self.backlog
            listing: list[object] | None
            try:
                folders = (
                    Path(self.settings["main"])
                    / Path(self.settings["places"]["backlog"]["path"]).relative_to(
                        self.settings["root"]
                    ),
                    board.reviewer_folder(self.settings),
                )
                listing = [
                    sorted(
                        (f.name, f.stat().st_size, f.stat().st_mtime_ns)
                        for f in folder.iterdir()
                    )
                    if folder.is_dir()
                    else []
                    for folder in folders
                ]
                listing.append(self.log_lines)
            except (KeyError, ValueError, OSError):
                listing = None
            moved = listing != self.stamps.get("backlog")
            self.stamps["backlog"] = listing
            if (
                fresh
                or moved
                or self.backlog is None
                or time.monotonic() - self.backlog_at >= self.settle_seconds
            ):
                try:
                    self.backlog = board.backlog(self.settings)
                    self.problems.pop("backlog", None)
                except (OSError, KeyError, ValueError) as error:
                    self.problems["backlog"] = f"the backlog does not read: {error}"
                self.backlog_at = time.monotonic()
            return self.backlog

    def current(self, board: ModuleType, now: int | None = None) -> Model:
        """The model as the files stand now, made again only when one of them changed,
        or once a minute for the times that move with the clock (a coarse clock keeps a
        page that is refreshed often from making it each time)."""
        with self.lock:
            self.read_log()
            self.read_owner(board.lem_project)
            self.read_settings(board)
            now = now if now is not None else now_ms()
            key = (
                len(self.events),
                self.log_at,
                self.stamps.get("owner"),
                json.dumps(self.meta, sort_keys=True),
                now // 60000,
            )
            if self.model is None or key != self.model_key:
                self.model = derive(self.events, self.owner, now, meta=self.meta)
                self.model_key = key
            else:
                self.model.now = now
            if self.changed("forge", self.state / FORGE_LOOK):
                self.forge = forge_look(self.state)
            self.model.seen = (self.forge or {}).get("seen")
            if self.changed("inbox", self.state / INBOX_LOOK):
                self.inbox = inbox_look(self.state)
            self.model.inbox = self.inbox
            task_files_look(self.state, self.model)
            self.model.cards = cards_look(self.state, self.model)
            self.model.answers = answers_look(self.state, self.model)
            return self.model
