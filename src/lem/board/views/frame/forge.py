"""The top bar's chips (`board_pages.topbar` on `main`): the
base branch, the pull requests proposed and how many are not green, the board's look at GitHub,
and the tasks landed today."""

from datetime import timedelta
from typing import TYPE_CHECKING

from lem.board.inputs import clock
from lem.board.inputs.parts import Chip

if TYPE_CHECKING:
    from lem.board.views.world import World

# How long the board's own look at GitHub counts as fresh: a few of its looks, a guess
# (`BOARD_LOOK_FRESH` on `main`).
FRESH = timedelta(minutes=10)
ASKS = "The board asks GitHub itself"
DEMO = (
    "example tasks: no forge is asked",
    "A board of example tasks asks GitHub nothing",
)


def chips(world: World) -> tuple[Chip, ...]:
    """The top bar's chips."""
    branch = world.place.base
    base = Chip(label=f"tasks land on **{branch}**", icon="code-branch")
    found = (base, proposed_chip(world), look_chip(world), landed_chip(world))
    return tuple(chip for chip in found if chip is not None)


def proposed(world: World) -> list[bool]:
    """Whether each pull request proposed now is green."""
    open_tasks = (
        seen.record for seen in world.tasks if seen.record.task.status == "open"
    )
    landings = (record.landing for record in open_tasks if record.landing)
    return [landing.proposed.green for landing in landings if landing.proposed]


def proposed_chip(world: World) -> Chip | None:
    """`**1** proposed · 1 not green`, or `**2** proposed, green`."""
    greens = proposed(world)
    if not greens:
        return None
    bad = greens.count(False)
    said = f" · {bad} not green" if bad else ", green"
    return Chip(
        label=f"**{len(greens)}** proposed{said}",
        icon="code-pull-request",
        look="you" if bad else None,
    )


def look_chip(world: World) -> Chip | None:
    """Whether the board looked at GitHub lately, while a pull request is open; none on a
    board of example tasks."""
    count = len(proposed(world))
    if not count or world.demo:
        return None
    what = "the pull request" if count == 1 else f"the {count} pull requests"
    looked = fresh(world)
    if looked is not None:
        title = (
            f"The board asks GitHub about {what} a few minutes apart, records a merge or "
            "a close there at once, and wakes the task's session"
        )
        return Chip(label=f"checked {looked}", icon="eye", title=title)
    title = world.forge.problem or (
        f"The board's server has not asked GitHub about {what} lately: a merge or a close "
        "there shows here after its next look"
    )
    return Chip(label=f"nobody looks at {what}", icon="eye", look="you", title=title)


def fresh(world: World) -> str | None:
    """How long ago the board looked at GitHub, while the look is fresh and did not fail."""
    looked, now = world.forge.looked, world.clock.now
    failed = world.forge.problem is not None
    if looked is None or failed or now - looked > FRESH:
        return None
    return clock.ago((now - looked).total_seconds())


def landed_chip(world: World) -> Chip | None:
    """`**2** landed today`, on the clock of the page."""
    zone = world.clock.zone
    today = world.clock.now.astimezone(zone).date()
    landed = sum(
        1
        for seen in world.tasks
        if seen.record.task.status == "landed"
        and seen.record.task.since.astimezone(zone).date() == today
    )
    if not landed:
        return None
    return Chip(label=f"**{landed}** landed today", icon="check", look="ok")
