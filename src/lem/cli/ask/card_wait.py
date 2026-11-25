"""An overlay waiter and the card's answer on the task record."""

import sys
from typing import TYPE_CHECKING

from lem.app.asking import ends, saved
from lem.app.asking.overlay_read import PageRefused
from lem.cli.ask import answer
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered
from lem.records.questions import Answer

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.asking.shape import End
    from lem.cli.ask.context import Context
    from lem.records.questions import Question

SAID = "said"


def recorded(here: Context, page: str) -> answer.Words | None:
    """The answer the board or an earlier waiter took, if one is there."""
    folder = here.task
    if folder is None:
        return None
    asked = saved.question(folder, page)
    if asked is None or asked.answer is None:
        return None
    return answer.on_record(folder, page, asked.answer)


def finished(here: Context, page: str, kind: End, raw: answer.Words) -> answer.Words:
    """Take this answer or read the answer that reached the record first."""
    if here.task is None:
        return answer.present(raw, page)
    asked = saved.question(here.task, page)
    if asked is None:
        return answer.present(raw, page)
    proposal = Answer(
        at=ends.time_of_answer(), option=kind, source="session", label=answer.label(raw)
    )
    return keep(here.task, asked, proposal, raw)


def keep(
    folder: Path, asked: Question, proposal: Answer, raw: answer.Words
) -> answer.Words:
    """The session result, with the first end from either surface."""
    page = asked.id.removeprefix("card:")
    try:
        won, kept = ends.finish(folder, asked, proposal, raw)
    except Refusal as refusal:
        return {"outcome": "refused", "pageID": page, SAID: refusal.why}
    return final_answer(folder, page, kept, None if won else proposal)


def final_answer(
    folder: Path, page: str, kept: Answer, later: Answer | None
) -> answer.Words:
    """Show the first answer and name a later act in the session when there is one."""
    printed = answer.on_record(folder, page, kept)
    if later is not None:
        race = later.label if later.option == "answered" else later.option
        printed.setdefault(SAID, ends.description(kept))
        name_later(printed, race)
    return printed


def after_board(here: Context, page: str, kept: answer.Words) -> None:
    """Read a later overlay pick before closing the board's answered card."""
    try:
        told = here.overlay.outcome(page)
    except OSError, Unanswered, PageRefused:
        told = None
    if told is not None and told.kind == "submitted":
        name_later(kept, answer.label(answer.submitted(told.payload)))
    close_board_answer(here, page)


def name_later(kept: answer.Words, race: str) -> None:
    """Name the later act alongside the one that counted."""
    said = kept[SAID]
    kept[SAID] = f"{said} The later act in the session was {race}."


def close_board_answer(here: Context, page: str) -> None:
    """Clear the displayed question after the board's answer reached the waiter."""
    try:
        here.overlay.close(page)
    except (OSError, Unanswered) as error:
        sys.stderr.write(
            f"lem ask kept the board's answer. The page could not close: {error}\n"
        )
