"""The two effects of `propose` (`landing.md` E, "Push recorded first"; H 3): the push of the
checked tip with a lease on Lem's last push, recorded before any call to the forge, and the
pull request, adopted, edited or opened.

A run cut off after the push finds it as its own; one cut off after the forge's call finds the
pull request with its head at the pushed commit, and edits it only when its words differ.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import changes
from lem.kernel.errors import Refusal
from lem.records.landing.record import Pull

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.model.landing.propose import Proposal
    from lem.model.landing.world import World
    from lem.records.record import Record


def checked_tip(context: Context) -> str:
    """The checked tip, while the task's branch is at it; refused once the branch moved."""
    world, slug = context.world, context.record.task.slug
    there = context.ports.git.tip(context.worktree, f"refs/heads/{world.branch}")
    if world.tip is None or there != world.tip:
        raise Refusal(
            "tip",
            f"{world.branch} moved after the step read it at {world.tip}",
            f"lem land next {slug}: the new tip's checks come first",
        )
    return world.tip


def sent(context: Context, last: str | None) -> str:
    """Push the checked tip to the task's branch with the lease of Lem's last push, when the
    branch is at it; give the commit git sent."""
    world, slug = context.world, context.record.task.slug
    tip = checked_tip(context)
    made = context.ports.git.push(context.worktree, world.branch, last, commit=tip)
    if not isinstance(made, str):
        raise Refusal(
            "git-refused",
            f"git refused the push of {world.branch}: {made.said}",
            f"lem land next {slug} names what origin holds now",
        )
    return made


def pushed(context: Context, *, push: bool) -> Record:
    """Push the tip when origin lacks it, and record the commit sent before any call to the
    forge; a commit that is not the checked tip is recorded, and refused."""
    record, world = context.record, context.world
    made = sent(context, lease(record, world)) if push else world.tip
    record = context.write(record, partial(recorded, made=made))
    slug = record.task.slug
    if made != world.tip:
        raise Refusal(
            "tip",
            f"the push sent {made}, not the checked {world.tip}: the branch moved",
            f"lem land next {slug}: the new tip's checks come first",
        )
    return record


def recorded(record: Record, *, made: str | None) -> Record:
    """The record with the push of `made`, Lem's last push, among the heads no proposal the
    forge confirmed holds yet."""
    landing = record.landing
    before = landing.unconfirmed if landing else ()
    if made is not None and made not in before:
        before = (*before, made)
    return changes.landing(record, pushed=made, unconfirmed=before)


def lease(record: Record, world: World) -> str | None:
    """The commit of origin's branch the push may replace: Lem's last push, or what origin
    holds when the checked tip holds it, a teammate's commit the builder brought in and the
    checks covered (`main:land.Task.own_remote`); none for a branch origin lacks."""
    if world.remote is None or world.remote_in_tip:
        return world.remote
    return record.landing.pushed if record.landing else None


def asked(context: Context, number: int | None, words: tuple[str, str]) -> Pull:
    """A new pull request with `words` (its title and text), or the edit of `number`."""
    forge, world = context.ports.forge, context.world
    title, text = words
    if number is None:
        made = forge.open_pull(world.branch, world.rules.base, title, text)
    else:
        made = forge.update_pull(number, title, text)
    return Pull(number=made.number, url=made.url, title=made.title)


def pulled(context: Context, proposal: Proposal, words: tuple[str, str]) -> Pull:
    """The forge's pull request with `words`: the task's own, edited when its words
    differ, else a new one."""
    found = proposal.adopt
    if found is not None and (found.title, found.body) == words:
        return Pull(number=found.number, url=found.url, title=found.title)
    return asked(context, found.number if found else None, words)
