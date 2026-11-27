"""Connect the board's lifespan and task page to the owner's Inbox."""

from functools import partial
from typing import TYPE_CHECKING

from lem.addons.inbox import link, schedule
from lem.board.duties import runner
from lem.board.inputs.parts import Link
from lem.board.inputs.task.head import Fact
from lem.board.turns import Turn

if TYPE_CHECKING:
    from pathlib import Path

    from starlette.applications import Starlette

    from lem.board.facts import Facts


def targets(home: Path, facts: Facts) -> tuple[schedule.Target, ...]:
    """The local workspaces, each at the board's tailnet address when the door is open."""
    base = (facts.tailnet or facts.url).rstrip("/")
    found = []
    for name, space in runner.spaces(home, facts.host):
        url = f"{base}/{facts.host}/{name}/"
        found.append(schedule.Target(where=space, name=name, url=url))
    return tuple(found)


def reported(problems: dict[str, str], name: str, problem: str | None) -> None:
    """Keep the last failure for this workspace until a good look clears it."""
    if problem is None:
        problems.pop(name, None)
    else:
        problems[name] = problem


def thread(state: Path, slug: str, *, away: bool) -> Fact | None:
    """The task header's external link, or why the owner cannot open the Inbox."""
    found = link.shown(state, slug, away=away)
    if found.url:
        shown = Link(href=found.url, label="Open the thread", out=True)
        return Fact(key="inbox", term="Inbox", link=shown)
    return Fact(key="inbox", term="Inbox", text=found.why) if found.why else None


def bind(app: Starlette) -> None:
    """Give the server its Inbox callbacks before its lifespan starts."""
    state = app.state
    state.inbox_problems = {}
    state.inbox_turn = Turn(
        name="the look at the Inbox",
        every=schedule.INTERVAL,
        step=partial(
            schedule.cycle,
            partial(targets, state.home, state.facts),
            partial(reported, state.inbox_problems),
        ),
    )
    state.inbox_thread = thread
