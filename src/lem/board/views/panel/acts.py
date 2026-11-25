"""The owner's acts in a task's header (`board_task.head_acts` on `main`): `Open a session` while
the board offers one, and the way to the merge's confirm step while it offers the merge."""

from typing import TYPE_CHECKING

from lem.board.inputs.names import task_href
from lem.board.inputs.parts import Link
from lem.board.inputs.task.head import HeadActs
from lem.board.views import offers
from lem.board.views.panel import opening
from lem.board.views.panel.common import pull_of

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World


def head_acts(world: World, seen: Seen) -> HeadActs | None:
    """`Open a session` while the board offers one, and the way to the merge's confirm step
    while it offers the merge; None on a page that may not act, or with neither."""
    if not world.viewer.may_act:
        return None
    session = opening.session_form(world, seen) if opening.opens(world, seen) else None
    offered = offers.merge_offered(seen, conflicts=world.forge.conflicts)
    merge = merge_link(world, seen) if offered else None
    if session is None and merge is None:
        return None
    return HeadActs(session=session, merge=merge)


def merge_link(world: World, seen: Seen) -> Link:
    """The link to the merge's confirm step, `Merge #44…`."""
    record = seen.record
    pull = pull_of(record)
    label = f"Merge #{pull.number}…" if pull else "Merge…"
    under = world.viewer.view
    href = f"{task_href(world.viewer.base, record.task.slug)}/merge"
    if under != "tasks":
        href = f"{href}?in={under}"
    return Link(
        href=href, label=label, icon="code-pull-request", press="risk", frame=True
    )
