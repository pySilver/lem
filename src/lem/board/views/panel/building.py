"""What we are building, on a task's Overview (`board_task.building` and `board_model.
building_of` on `main`): the goal, the outcome of `task.md` as the markdown it was written in,
the before and after pictures its text does not show, the important decisions that wait for a
look, and the backlog items its branch filed."""

from typing import TYPE_CHECKING

from lem.board.inputs.names import plural, task_href
from lem.board.inputs.parts import Link
from lem.board.inputs.task.cards import Building
from lem.board.views import words
from lem.board.views.artifacts import addresses, documents
from lem.board.views.panel import common, important, shots, told

if TYPE_CHECKING:
    from lem.board.inputs.parts import Document
    from lem.board.views.facts import Filed
    from lem.board.views.world import Seen, World


def building(world: World, seen: Seen) -> Building | None:
    """What we are building of the task of `seen`, or None with nothing to say."""
    goal = goal_of(seen)
    outcome = told.outcome(seen.text("task.md") or "")
    count = len(important.important(seen.record))
    filed = filed_of(seen)
    if not (goal or outcome or count) and filed is None:
        return None
    slug = seen.record.task.slug
    return Building(
        goal=words.capital(goal),
        outcome=outcome_document(world, seen, outcome),
        shots=shots.shots(seen.files, outcome, addresses.media_href(world, slug)),
        important=important_link(world, slug, count),
        filed=filed_line(filed),
        on_branch=tuple((filed_title(one), one.path) for one in filed or ()),
    )


def goal_of(seen: Seen) -> str:
    """Why the request is of its type, the goal; "" before the shape."""
    shape = seen.record.task.shape
    return shape.why if shape else ""


def filed_of(seen: Seen) -> tuple[Filed, ...] | None:
    """The backlog items the branch filed; None when git cannot tell, and for a task that
    ended when it filed none."""
    filed = seen.filed
    if filed is not None and not filed and common.closed(seen.record.task):
        return None
    return filed


def outcome_document(world: World, seen: Seen, outcome: str) -> Document | None:
    """The outcome of `task.md`, with the task's pictures, or None."""
    if not outcome:
        return None
    slug = seen.record.task.slug
    media = addresses.media_href(world, slug)
    forge = documents.forge_of(seen.record)
    return documents.document(f"outcome-{slug}", outcome, forge, media=media)


def important_link(world: World, slug: str, count: int) -> Link | None:
    """The link to the important decisions on Criteria and decisions, or None."""
    if not count:
        return None
    waits = "waits" if count == 1 else "wait"
    return Link(
        href=task_href(world.viewer.base, slug, "criteria", world.viewer.view),
        label=f"{plural(count, 'important decision')} {waits} for a look",
        title="Open the tab Criteria and decisions · key 2",
        icon="triangle-exclamation",
        frame=True,
    )


def filed_line(filed: tuple[object, ...] | None) -> str | None:
    """How many backlog items the branch filed, or None when git cannot tell."""
    if filed is None:
        return None
    said = (
        f"{plural(len(filed), 'backlog item')} filed"
        if filed
        else "no backlog item filed"
    )
    return f"{said} · on the task’s branch"


def filed_title(filed: Filed) -> str:
    """The item's title with its problem, when its head does not read."""
    if filed.problem is None:
        return filed.title
    return f"{filed.title} · {filed.problem}"
