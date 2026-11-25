"""The notices at the top of the sidebar (`board_pages.notices` on `main`): demo data, the owner
away, and each blocked task with its line."""

from typing import TYPE_CHECKING

from lem.board.inputs import clock
from lem.board.inputs.names import task_href, title_of
from lem.board.inputs.sidebar import Notice
from lem.board.views import telling, words
from lem.records.holds import Blocked, ReleaseHold

if TYPE_CHECKING:
    from lem.board.views.frame.counted import Counted
    from lem.board.views.world import Seen, World

ALERT = "triangle-exclamation"
DEMO = "These tasks are examples and not real work. Nothing on this page waits for you."
BACK = "The tasks go on without you until you type /lem im-back."
DEMO_NOTICE = Notice(
    id="notice-demo", kind="demo", icon=ALERT, head="Demo data.", said=DEMO
)


def notices(world: World, counts: Counted) -> tuple[Notice, ...]:
    """Every notice of the page, in its order."""
    demo = DEMO_NOTICE if world.demo else None
    held = filter(stopped, (pair[0] for pair in counts.placed))
    first = tuple(filter(None, (demo, away(world))))
    return first + tuple(blocked(world, seen) for seen in held)


def away(world: World) -> Notice | None:
    """The notice of the owner's away, while he is away."""
    presence = world.presence
    if not presence.away or presence.since is None:
        return None
    stamp = clock.stamp(presence.since, world.clock.now, world.clock.zone)
    return Notice(
        id="notice-away",
        kind="away",
        look="you",
        icon="moon",
        head=f"You are away since {stamp}.",
        said=BACK,
    )


def stopped(seen: Seen) -> bool:
    """Whether a task that did not end is blocked, or began two releases back."""
    task = seen.record.task
    ended = task.status in {"landed", "answered", "dropped"}
    return not ended and isinstance(task.hold, Blocked | ReleaseHold)


def blocked(world: World, seen: Seen) -> Notice:
    """The notice of a blocked task, with its line."""
    task = seen.record.task
    hold = task.hold
    line = hold.say if isinstance(hold, ReleaseHold) else telling.said(seen.record)
    said = words.capital(line) if line else "No line is on record."
    return Notice(
        id=f"notice-blocked-{task.slug}",
        kind="blocked",
        look="bad",
        icon=ALERT,
        head="Blocked:",
        said=said,
        task=task_href(world.viewer.base, task.slug),
        task_title=title_of(task.slug),
    )
