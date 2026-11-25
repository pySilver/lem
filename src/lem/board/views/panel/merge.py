"""The merge's confirm step (`board_task.merge_step` and `board_model.merge_says` on `main`):
green or not green first, careful when it is, the reasons, the facts of what it merges, and one
button that carries the commit it shows, so that a branch proposed again since is not merged on
this look. A merge that stands, or that the board does not offer, says why instead."""

from typing import TYPE_CHECKING

from lem.board.inputs.parts import Chip
from lem.board.inputs.task.steps import Merge
from lem.board.views import marks
from lem.board.views.panel import confirm, merge_confirm, merge_facts, merge_said
from lem.board.views.panel.common import careful_of
from lem.board.views.reasons import reasons
from lem.model.landing import merge as landing_merge

if TYPE_CHECKING:
    from lem.board.inputs.task.steps import NotNow
    from lem.board.inputs.waits import Reasons
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World

NOTE = (
    "A merge cannot be undone from the board. Lem’s merge call reads the base branch "
    "first, and it can take a minute."
)
GREEN = f"{marks.GREEN}."
NOT_GREEN = "The pull request says why, and so do the rows below."


def merge(world: World, seen: Seen, standing: Standing) -> Merge | NotNow:
    """The merge's confirm step of the task of `seen`, or why there is nothing to do now."""
    said = merge_said.why_not(world, seen, standing)
    if said is not None:
        return confirm.not_now(world, seen.record.task.slug, said)
    landing = seen.record.landing
    green = bool(landing and landing.proposed and landing.proposed.green)
    why = reason_careful(seen)
    return Merge(
        confirm=merge_confirm.confirm_of(world, seen, green=green),
        green=green,
        word="Green" if green else "Not green",
        careful=None if why is None else careful_chip(why),
        sub=GREEN if green else NOT_GREEN,
        reasons=None if green else listed(world, seen),
        careful_why=None if why is None else careful_line(why),
        facts=merge_facts.facts(world, seen),
        note=NOTE,
    )


def listed(world: World, seen: Seen) -> Reasons | None:
    """The reasons the pull request is not green, under the step's list id."""
    return reasons(seen.record, "cf", world.viewer.view, world.viewer.base)


def reason_careful(seen: Seen) -> str | None:
    """The review's reason for a careful change, if it gave one."""
    if not landing_merge.careful(seen.record):
        return None
    careful = careful_of(seen.record)
    return careful.why if careful and careful.careful else ""


def careful_chip(why: str) -> Chip:
    """The careful mark, with why as its hover."""
    return Chip(
        label="careful", icon="shield-exclamation", look="bad", title=why or None
    )


def careful_line(why: str) -> str:
    """Why the change is careful, and who merges it."""
    said = f"{why} " if why else ""
    return f"**Careful:** {said}A careful change is merged by a person."
