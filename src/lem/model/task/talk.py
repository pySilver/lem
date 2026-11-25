"""The plan talk's counts, which the landing reads and the pull request shows, in their one
form (`project.talk_form` on `main`): who argued the plan with its defender, its turns, the
questions of the reviewer's first list, how many it settled and left open, how many the lead
repaired, the open ones that are a design choice, the questions not argued, and Fable's three
counts of a layer of patches (2026-11-16). Its record ends the talk's span."""

from typing import TYPE_CHECKING

import msgspec
from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.task import spans

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.records.work import Talk

# The most turns a talk of N questions has by the rules of `stages/talk.md`: the reviewer's
# list, two answers of the defender and two of the reviewer on each question, and the close.
# Derived from those rules in a Fable second opinion (2026-11-16); no talk under them was
# measured. It is the defender's to keep, not a check of the record: a talk that ran longer is
# written as it ran, and its bound says that it went over.
TURNS_PER_QUESTION = 4
TURNS_AROUND = 2
FORM = (
    "lem task talked SLUG --reviewer AGENT --turns N --questions N --settled N --open N "
    "--repaired N --design N --unargued N --root N --layer N --shared N"
)


def counts(talk: Talk) -> list[int]:
    """The talk's counts."""
    fields = msgspec.structs.astuple(talk)
    return [count for count in fields if isinstance(count, int)]


def refusal(talk: Talk) -> str | None:
    """Why the talk's counts do not agree with each other, or None. A talk over its bound of
    turns, or one whose second question on a decision did not close as a design choice, is a
    fact and no refusal: a record refused for it would leave the request unproposed."""
    if not talk.reviewer.strip():
        return "reviewer names the agent that argued the plan with its defender"
    if min(counts(talk)) < 0:
        return "each N is a whole number, 0 or more"
    return turns(talk) or repairs(talk)


def turns(talk: Talk) -> str | None:
    """Why the talk's turns and questions do not agree, or None."""
    if talk.turns < TURNS_AROUND:
        return (
            "a talk has two turns at the least: the reviewer's list, which may be empty, "
            "and the close"
        )
    if not talk.questions and talk.unargued and talk.turns <= TURNS_AROUND:
        return (
            "a talk of no question and two turns has no turn after the list, so unargued "
            "is 0"
        )
    if talk.settled + talk.open != talk.questions:
        return (
            "each question of the reviewer's first list ends settled or left open, so "
            "settled and open add up to questions"
        )
    return None


def repairs(talk: Talk) -> str | None:
    """Why the talk's design choices and repairs do not agree with its questions, or None."""
    if talk.design > talk.open:
        return (
            "a design choice is a question left open because it held a second time, so "
            "design is at most open"
        )
    if talk.repaired > talk.questions:
        return (
            "repaired counts the questions whose answer changed the plan, so repaired is "
            "at most questions"
        )
    if talk.root + talk.layer > talk.repaired:
        return (
            "a repair either changed a decision of the plan (root) or put a mechanism "
            "over a decision with a cite (layer), or neither, so root and layer add up to "
            "at most repaired"
        )
    return None


def bound(talk: Talk) -> int:
    """The most turns the talk has by its rules; a talk over it went over."""
    return TURNS_PER_QUESTION * talk.questions + TURNS_AROUND


def talked(record: Record, *, talk: Talk) -> Record:
    """The record with the plan talk's counts, and its span ended when it is open; refused
    when the counts do not agree."""
    why = refusal(talk)
    if why is not None:
        raise Refusal(
            "talk",
            f"{FORM}: {why}",
            "count the talk again from its turns, and write the record in that form",
        )
    task = replace(record.task, talk=talk)
    return spans.ended_if_open(replace(record, task=task), "plan-talk", talk.at)
