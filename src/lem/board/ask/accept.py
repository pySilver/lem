"""Apply a card answer from the board and say what took effect."""

from collections.abc import Mapping
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.app.asking import ends, saved
from lem.board.acts.asker import Asker
from lem.board.ask import live_card, verify
from lem.kernel.errors import Refusal
from lem.records.questions import Answer, Question

if TYPE_CHECKING:
    from lem.app.asking.shape import Posted


class AtCard(msgspec.Struct, frozen=True, kw_only=True):
    """An answer to one saved question at one address."""

    folder: Path
    page: str
    shown: Question
    who: Asker
    environ: Mapping[str, str]


def accepted(at: AtCard, posted: Posted) -> tuple[HTTPStatus, str]:
    """Answer only the exact card the owner read, and only while it waits."""
    if at.shown.answer is not None:
        return taken(at.shown.answer)
    if posted.digest != at.shown.digest:
        return (
            HTTPStatus.CONFLICT,
            "The card differs from the page the owner read. Load it again.",
        )
    card = saved.metadata(at.folder, at.page)
    try:
        checked = verify.normalized(card.prompts, posted)
    except Refusal as error:
        return HTTPStatus.UNPROCESSABLE_ENTITY, f"{error.why} {error.fix}"
    live_card.check(at.folder, card, at.environ)
    return commit(at, checked)


def commit(at: AtCard, posted: Posted) -> tuple[HTTPStatus, str]:
    """Keep the answer in the task record and give the board its outcome."""
    proposed = Answer(
        option="answered",
        label=verify.label_of(posted),
        note=verify.note_of(posted),
        source="board",
        via=at.who.via,
        device=at.who.device,
        agent=at.who.agent or None,
        at=ends.time_of_answer(),
    )
    wire = msgspec.to_builtins(posted)
    for picked in wire["answers"].values():
        picked.setdefault("selected", [])
        picked.setdefault("labels", [])
    won, kept = ends.finish(at.folder, at.shown, proposed, wire)
    if not won:
        return taken(kept)
    return (
        HTTPStatus.OK,
        "The owner’s answer is on record. The task’s session will read it.",
    )


def taken(answer: Answer) -> tuple[HTTPStatus, str]:
    """The first answer still holds."""
    return HTTPStatus.CONFLICT, ends.description(answer)
