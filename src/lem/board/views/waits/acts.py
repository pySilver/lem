"""The owner's acts on a row of Waits for you (`board_pages.row_acts` on `main`), where the page
may act: the answer to a question the board takes with its own buttons (a breaker, a plan, the
skip of a read), the way to criteria that wait for his yes under their text, to a merge's confirm
step, to a card of the task's session, and "Open a session" for a task that lacks one."""

from typing import TYPE_CHECKING

from lem.app.sessions.phase import phase_or_none
from lem.board.inputs import names
from lem.board.inputs.forms import ActForm, Field
from lem.board.inputs.parts import Link
from lem.board.inputs.waits import Acts
from lem.board.views import answering, offers
from lem.board.views.waits import kinds

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
    if row.kind in ASKED:
        asked = offers.open_question(seen.record.task, row.kind)
        answer = answering.form(world, asked, "row", UNDER) if asked else None
        return Acts(answer=answer) if answer else None
    link = link_of(world, seen, row)
    if link is not None:
        return Acts(links=(link,))
    if row.kind in {"session", "stopped"} and opens_session(seen):
        return Acts(forms=(session_form(world, seen),))
    return None


def link_of(world: World, seen: Seen, row: Row) -> Link | None:
    """The way to the criteria's yes, a merge's confirm step, or a card of the session."""
    way = way_of(seen, row)
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


def way_of(seen: Seen, row: Row) -> Way | None:
    """The tab a row's link opens, its words, its icon and its look, or None."""
    if row.kind == "criteria" and offers.approvable(seen.record.task):
        return "criteria", "Read and approve…", "file-lines", GO
    if row.kind == MERGE and offers.merge_offered(seen):
        return MERGE, "Merge…", "code-pull-request", "risk"
    card = kinds.card_tab(row)
    if card is not None:
        return card, "Answer the card…", "user", GO
    return None


def opens_session(seen: Seen) -> bool:
    """Whether the task's phase gives it a session the board may open."""
    task = seen.record.task
    return phase_or_none(task, worktree=seen.worktree) is not None


def session_form(world: World, seen: Seen) -> ActForm:
    """`Open a session` for the task, from the row."""
    action = f"{names.task_href(world.viewer.base, seen.record.task.slug)}/session"
    return ActForm(
        action=action,
        label="Open a session",
        icon="play",
        press=GO,
        busy="Opening…",
        fields=(Field(name="in", shown=UNDER),),
    )
