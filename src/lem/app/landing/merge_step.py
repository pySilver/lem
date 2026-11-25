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
type Admits = Callable[[Due], bool]


class Hooks(msgspec.Struct, frozen=True, kw_only=True):
    """What a step adds to the run: its own line of what comes next (`told`), and a due step
    it is taken beside (`admits`: the owner's word while the merge agent's read is due)."""

    told: Told | None = None
    admits: Admits | None = None


NONE = Hooks()


def refused(workspace: places.Workspace, slug: str, verb: Verb) -> None:
    """Refuse the step `verb` when the record alone says another is due, with no look at git
    or the forge."""
    early = phases.settled(tasks.read(workspace.state, slug))
    if early is not None and early.step != verb:
        raise say.not_due(slug, verb, early)


def ran(
    workspace: places.Workspace, slug: str, verb: Verb, act: Act, admits: Admits | None
) -> tuple[Context, object, Due]:
    """Under the step lock: the step refused unless it is the due one, or one that `admits`
    takes beside it; its act, and the due step after it (from the record when it alone
    decides)."""
    now = clock.now()
    with steps.step(workspace.state, slug, verb, now):
        context = step.opened(workspace, slug, now)
        due = phases.due(context.record, context.world)
        if due.step != verb and not (admits is not None and admits(due)):
            raise say.not_due(slug, verb, due)
        outcome = act(context)
        after = phases.settled(tasks.read(workspace.state, slug))
        return context, outcome, after or step.looked(context)


def then_of(context: Context, outcome: object, due: Due, told: Told | None) -> Next:
    """What comes next: the act's own line, else the due step's command."""
    said = None if told is None else told(outcome)
    squash = context.world.rules.history == "squash"
    slug = context.record.task.slug
    return said or following.following(slug, due, squash=squash)


def landed(
    folder: Path, slug: str, verb: Verb, act: Act, hooks: Hooks = NONE
) -> Envelope:
    """Run the step `verb` of the task `slug` with its act, and give its envelope; `hooks`
    give the act's own line of what comes next, and the due step it is taken beside."""
    workspace = places.workspace(folder)
    refused(workspace, slug, verb)
    context, outcome, due = ran(workspace, slug, verb, act, hooks.admits)
    then = then_of(context, outcome, due, hooks.told)
    return Envelope(
        ok=True, outcome=msgspec.Raw(msgspec.json.encode(outcome)), following=then
    )
