"""The saved questions that belong to a task's live session."""

from typing import TYPE_CHECKING

import msgspec

from lem.app.asking import saved
from lem.app.sessions import log
from lem.kernel.errors import Fault, Refusal

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.owner.looks import Session
    from lem.records.record import Record


def in_session(folder: Path, record: Record, session: Session | None) -> Session | None:
    """Add the open card ids whose saved metadata names this session."""
    if session is None or not session.live or session.id is None:
        return session
    pending = (
        one.id
        for one in record.task.questions
        if one.topic == "card" and one.answer is None
    )
    return msgspec.structs.replace(
        session,
        cards=frozenset(key for key in pending if belongs(folder, key, session.id)),
    )


def belongs(folder: Path, key: str, session: str) -> bool:
    """An unreadable card stays in its overlay and has no row on the board."""
    if not key.startswith("card:"):
        return False
    page = key.rpartition(":")[2]
    try:
        card = saved.metadata(folder, page)
    except Fault, Refusal:
        return False
    return log.same(card.session, session)
