"""One step of the merge's end of the landing (`merge-review`, `merge`, `merged`, `clean`): the
step lock, the record and the world read fresh, the step refused unless it is the due one, its
act, and what comes next (`app/landing/following.py`).

A step that the record alone refuses (a landing that ended, a task not ready) is refused before
any look at git or the forge, so it answers at once; a step that runs reads the world, since
what it does depends on it.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import following, say, step
from lem.kernel import clock
from lem.kernel.envelope import Envelope
from lem.model.landing import phases
from lem.store import places, steps, tasks

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from lem.app.landing.frame import Context
    from lem.kernel.envelope import Next
    from lem.model.landing.world import Due, Verb

type Act = Callable[[Context], object]
type Told = Callable[[object], Next | None]


def none_told(outcome: object) -> Next | None:
    """No line of the act's own: what comes next is the due step's."""
    return None


def refused(workspace: places.Workspace, slug: str, verb: Verb) -> None:
    """Refuse the step `verb` when the record alone says another is due, with no look at git
    or the forge."""
    early = phases.settled(tasks.read(workspace.state, slug))
    if early is not None and early.step != verb:
        raise say.not_due(slug, verb, early)


def ran(
    workspace: places.Workspace, slug: str, verb: Verb, act: Act
) -> tuple[Context, object, Due]:
    """Under the step lock: the step refused unless it is the due one, its act, and the due
    step after it (from the record when it alone decides)."""
    now = clock.now()
    with steps.step(workspace.state, slug, verb, now):
        context = step.allowed(step.opened(workspace, slug, now), verb)
        outcome = act(context)
        due = phases.settled(tasks.read(workspace.state, slug)) or step.looked(context)
    return context, outcome, due


def landed(
    folder: Path, slug: str, verb: Verb, act: Act, told: Told = none_told
) -> Envelope:
    """Run the step `verb` of the task `slug` with its act, and give its envelope; `told`
    gives the act's own line of what comes next, when it has one."""
    workspace = places.workspace(folder)
    refused(workspace, slug, verb)
    context, outcome, due = ran(workspace, slug, verb, act)
    squash = context.world.rules.history == "squash"
    then = told(outcome) or following.following(slug, due, squash=squash)
    encoded = msgspec.Raw(msgspec.json.encode(outcome))
    return Envelope(ok=True, outcome=encoded, following=then)
