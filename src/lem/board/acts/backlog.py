"""`POST /HOST/WORKSPACE/backlog/drop`: the owner's Drop of a reviewer's item, from the Backlog
view (`serve.act_drop` on `main`; `surfaces.md` B).

An item a task that did not end holds is refused with that task, and so is an item of the
backlog folder, which leaves that folder on a branch. Else `lem proposals drop PATH` removes the
file and keeps the drop in the day's record of each of its proposals, so that no later reviewer
proposes it again: the proposals are an add-on, whose command runs as a process of its own
(`child.py`). No task's journal gets the drop: no task is its.
"""

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

import msgspec
from starlette.concurrency import run_in_threadpool

from lem.app.tasks.opening import REVIEWER_ITEMS
from lem.board.acts import acting, back, child, slugs
from lem.board.acts.asked import Asked, refused
from lem.board.acts.notes import Note
from lem.kernel.errors import Refusal
from lem.store import tasks

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response


ACT = "drop"


class Dropped(msgspec.Struct, frozen=True, kw_only=True):
    """What `lem proposals drop` printed: the proposals whose record keeps the drop."""

    proposals: tuple[str, ...] = ()


def checked(asked: Asked) -> str:
    """The path of the item the drop names; refused for none, for an item of the backlog
    folder, and for one a task holds."""
    path = asked.given.path.strip()
    if not path:
        why = "The drop names no item: open the backlog again, and press Drop on the item."
        raise Refusal("item", why, "press Drop on the item")
    if str(PurePosixPath(path).parent) != REVIEWER_ITEMS:
        why = (
            f"{path} is an item of the backlog folder, which leaves it on a branch: "
            "nothing was dropped."
        )
        raise Refusal("item-folder", why, "remove it on a branch")
    holding = slugs.holder(path, tasks.every(asked.state))
    if holding is not None:
        why = f"This item has a task already: {holding.slug}, {holding.status}."
        raise Refusal("item-held", why, f"drop the task {holding.slug} first")
    return path


def names_of(outcome: msgspec.Raw | None) -> str:
    """The proposals whose record keeps the drop, as `lem proposals drop` printed them."""
    outcome = outcome or msgspec.Raw(b"{}")
    return ", ".join(msgspec.json.decode(outcome, type=Dropped).proposals)


def said_of(asked: Asked) -> str:
    """Drop the item, and say so."""
    path = checked(asked)
    printed = child.ran(asked.checkout, "proposals", "drop", path)
    if printed.refusal is not None:
        refused = printed.refusal
        raise Refusal(refused.code, refused.why, refused.fix)
    kept = names_of(printed.outcome) or "its proposals"
    return (
        f"Dropped: {path} is gone from the backlog, and the day's record keeps the drop "
        f"of {kept}, so no later reviewer proposes it again."
    )


def dropped(asked: Asked) -> Note:
    """Drop the reviewer's item, and the note."""
    try:
        said = said_of(asked)
    except Refusal as refusal:
        return refused(ACT, None, refusal)
    return Note(act=ACT, state="done", said=said)


async def endpoint(request: Request) -> Response:
    """Drop the item, then the Backlog view with the note."""
    asked = await acting.asked_of(request)
    if not isinstance(asked, Asked):
        return asked
    note = await run_in_threadpool(dropped, asked)
    return back.to_view(request, "backlog", note)
