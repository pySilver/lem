"""The feed's words of a task's own entries: a move of its state, an act of the owner, and the
summary retention folded its journal into (`describe`, `acted_head` and `summary_said` on
`main`)."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs.names import plural
from lem.board.views import words
from lem.board.views.activity import states
from lem.board.views.activity.told import USER, YOU, Told

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.journal.task import OwnerAct, StateNoted, Summary
    from lem.records.task import Task

# Where the owner acted from, in words; a login is never named.
VIA = MappingProxyType(
    {
        "local": "the board, on this Mac",
        "door": "the board, through the tailnet door",
        "session": "the task’s session",
    }
)
# Each act of the board, in the feed's words.
ACTED = MappingProxyType(
    {
        "approve": "You approved the criteria from the board",
        "merge": "You merged it from the board",
        "park": "You parked the task from the board",
        "session": "You opened a session of the task from the board",
        "start": "You started the task from the board",
        "answer": "You answered a card of the task’s session from the board",
    }
)
SUMMARY_HEAD = "Its events became one summary"
SUMMARY_SAID = (
    "{events} in one event that keeps the task's status, its end and its pull request: "
    "nothing of the task happened for state.keep_days days after its end"
)


def state(entry: StateNoted, task: Task) -> Told:
    """A move of the task: its state's label, and the stage's line in the board's words."""
    said = states.said_of(states.key_of(entry.status, entry.hold))
    line = entry.line or ""
    shown = talked(task, entry.at)
    text = words.said(line, talked=shown) if line else ""
    return Told(said.look, said.icon, said.label, text)


def talked(task: Task, moment: datetime) -> bool:
    """Whether a plan talk of the task ended by `moment`."""
    talks = (span for span in task.spans if span.name == "plan-talk")
    ends = [span.end for span in talks if span.end]
    record = task.talk
    recorded = record is not None and record.at <= moment
    return recorded or any(end <= moment for end in ends)


def owner(entry: OwnerAct, task: Task) -> Told:
    """An act of the owner, with where he acted from."""
    if entry.act == "approve-carried" and task.resumed_from:
        return Told(
            YOU,
            USER,
            "You approved the criteria",
            sub=f"carried over from {task.resumed_from}",
        )
    where = VIA.get(entry.via or "", "")
    return Told(YOU, USER, acted(entry, task), where)


def acted(entry: OwnerAct, task: Task) -> str:
    """The head of his act: what he picked on which question, or the act's own words."""
    if entry.act != "answer" or entry.question is None:
        return ACTED.get(entry.act, f"You acted from the board: {entry.act}")
    asked = (one for one in task.questions if one.id == entry.question)
    question = next((one.question for one in asked), "a question of the task")
    label = words.capital(entry.option or "an option")
    where = "in the session" if entry.via == "session" else "from the board"
    return f"You picked {label} on “{question}” {where}"


def summary(entry: Summary) -> Told:
    """The one entry a pruned journal became: how many entries it stands for, and why."""
    last = entry.last_state
    key = states.key_of(last.status, last.hold) if last else ""
    said = states.said_of(key)
    events = plural(entry.entries, "event")
    text = SUMMARY_SAID.format(events=events)
    return Told(said.look, said.icon, SUMMARY_HEAD, text)
