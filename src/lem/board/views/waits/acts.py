"""The owner's acts on a row of Waits for you (`board_pages.row_acts` on `main`), where the page
may act: the answer to a question the board takes with its own buttons (a breaker, a plan, the
skip of a read), the way to criteria that wait for his yes under their text, to a merge's confirm
step, to a card of the task's session, and "Open a session" for a task that lacks one."""

from typing import TYPE_CHECKING

from lem.app.sessions.phase import phase_or_none
from lem.board.inputs import names
from lem.board.inputs.parts import Link
from lem.board.inputs.waits import Acts
from lem.board.views import answering, offers
from lem.board.views.panel.opening import session_form
from lem.board.views.waits import kinds
from lem.records.holds import OwnerHold

if TYPE_CHECKING:
    from lem.board.inputs.text import Press
    from lem.board.views.world import Seen, World
    from lem.model.owner.looks import Row

    # The tab a link opens, its words, its icon and its look.
    type Way = tuple[str, str, str, Press]

UNDER = "waits"
# The rows the board answers with its own buttons, by the topic of their question.
ASKED = frozenset(("breaker", "plan", "skip"))
GO: Press = "go"
MERGE = "merge"


def acts(world: World, seen: Seen, row: Row) -> Acts | None:
    """The acts of `row`, or None where the page may not act or the row has none."""
    if not world.viewer.may_act:
        return None
    topic = topic_of(seen, row)
    if topic is not None:
        asked = offers.open_question(seen.record.task, topic)
        answer = answering.form(world, asked, "row", UNDER) if asked else None
        return Acts(answer=answer) if answer else None
    link = link_of(world, seen, row)
    if link is not None:
        return Acts(links=(link,))
    if (
        row.kind in {"session", "stopped"}
        and phase_or_none(seen.record.task, worktree=seen.worktree) is not None
    ):
        return Acts(forms=(session_form(world, seen, under=UNDER),))
    return None


def link_of(world: World, seen: Seen, row: Row) -> Link | None:
    """The way to the criteria's yes, a merge's confirm step, or a card of the session."""
    way = way_of(world, seen, row)
    return linked(world, seen.record.task.slug, way) if way else None


def linked(world: World, slug: str, way: Way) -> Link:
    """The link of a way: the tab it opens, its words, its icon and its look."""
    tab, label, icon, press = way
    href = href_of(world, slug, tab)
    return Link(href=href, label=label, icon=icon, press=press, frame=True)


def href_of(world: World, slug: str, tab: str) -> str:
    """The address of the task's tab under Waits for you; the merge's confirm step keeps the
    view in its query."""
    base = world.viewer.base
    if tab == MERGE:
        return f"{names.task_href(base, slug)}/{MERGE}?in={UNDER}"
    return names.task_href(base, slug, tab, UNDER)


def way_of(world: World, seen: Seen, row: Row) -> Way | None:
    """The tab a row's link opens, its words, its icon and its look, or None."""
    if row.kind == "criteria" and offers.approvable(seen.record.task):
        return "criteria", "Read and approve…", "file-lines", GO
    if row.kind == MERGE and offers.merge_offered(seen, world.forge.conflicts):
        return MERGE, "Merge…", "code-pull-request", "risk"
    card = kinds.card_tab(row)
    if card is not None:
        return card, "Answer the card…", "user", GO
    return None


def topic_of(seen: Seen, row: Row) -> str | None:
    """The topic of the question a row answers with the board's own buttons: a breaker, a
    plan, or the skip of the personas' read under his hold; None for any other row."""
    if row.kind in ASKED:
        return row.kind
    hold = seen.record.task.hold
    skips = (
        row.kind == "held" and isinstance(hold, OwnerHold) and hold.on == "skip-read"
    )
    return "skip" if skips else None
