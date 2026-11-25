"""One landing step: under the task's step lock, the record and the world read fresh, the step
refused unless it is the due one, its effects, and the due step after it (`landing.md` C and G).

A step's act writes its evidence through `store.tasks.update` with the revision it read, never
across an effect. A task that does not exist is refused before any lock or look.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import frame, say, step_release
from lem.app.landing.world import gather
from lem.kernel import clock
from lem.kernel.envelope import Envelope
from lem.model.landing import phases
from lem.store import places, steps, tasks

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from lem.model.landing import world
    from lem.records.base import Moment

type Act = Callable[[frame.Context], object]


def opened(
    workspace: places.Workspace,
    slug: str,
    now: Moment,
    *,
    verb: world.Verb | None = None,
) -> frame.Context:
    """The context of a step: the ports, the record and the world after a fetch."""
    record = step_release.at_step(workspace.state, slug, verb)
    ports = frame.bound(workspace)
    found = gather(ports, workspace, record, now, fetch=True)
    return frame.Context(ports=ports, workspace=workspace, record=record, world=found)


def allowed(context: frame.Context, verb: world.Verb) -> frame.Context:
    """The context, when `verb` is the due step; else its refusal."""
    due = phases.due(context.record, context.world)
    if due.step != verb:
        raise say.not_due(context.record.task.slug, verb, due)
    return context


def looked(context: frame.Context) -> world.Due:
    """The due step after the act, from the record and the world as they are now."""
    slug, now = context.record.task.slug, context.world.now
    record = tasks.read(context.workspace.state, slug)
    found = gather(context.ports, context.workspace, record, now, fetch=False)
    return phases.due(record, found)


def landed(folder: Path, slug: str, verb: world.Verb, act: Act) -> Envelope:
    """Run the step `verb` of the task `slug` with its act, and give its envelope."""
    workspace = places.workspace(folder)
    tasks.read(workspace.state, slug)
    now = clock.now()
    with steps.step(workspace.state, slug, verb, now):
        context = allowed(opened(workspace, slug, now), verb)
        outcome = msgspec.Raw(msgspec.json.encode(act(context)))
        following = say.following(slug, looked(context))
    return Envelope(ok=True, outcome=outcome, following=following)
