"""A branch with no commit of its own (`landing.md` E, "Merge-only change"): a change that sat
only in a merge commit, which a rebase drops, or nothing to land (`land.cmd_base` on `main`).

The tip before the rebase is kept where a retry finds it: in `Based` once the rebase is on
record, and in git's `ORIG_HEAD` while a stop cut the step between the rebase and its record.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.base import Facts
    from lem.model.landing.world import World
    from lem.records.landing.start import Based
    from lem.records.record import Record


def merge_only(
    record: Record, world: World, change: str, before: str, where: str
) -> Refusal:
    """The refusal of a branch a rebase left with no commit of its own, while `change` sat at
    `before`, the tip before the rebase, which a reset puts back."""
    slug, onto = record.task.slug, world.rules.base
    return Refusal(
        "merge-only",
        f"the rebase onto origin/{onto} left the branch no commit of its own, and "
        f"{change} sat only in a merge commit, which a rebase drops. The branch was at "
        f"{before} before it",
        f"`git -C {where} reset --hard {before}` puts it back; the change goes into a "
        f"commit of its own, which a rebase keeps, then lem land base {slug} runs again. "
        f"When the work reached the base another way, lem task move {slug} dropped ends "
        "the task",
    )


def lost(
    record: Record, world: World, based: Based | None, where: str
) -> Refusal | None:
    """The refusal of a rebase on record that left the tip now no commit of its own while it
    could not show that it kept the change. None when no such rebase made the tip."""
    if based is None or based.tip != world.tip:
        return None
    if based.before == based.tip or not based.unshown_paths:
        return None
    paths = ", ".join(based.unshown_paths)
    return merge_only(record, world, f"the change in {paths}", based.before, where)


def nothing(record: Record) -> Refusal:
    """The refusal of a branch with no commit that origin's base lacks."""
    slug = record.task.slug
    return Refusal(
        "nothing-to-land",
        "the branch has no commit that origin's base lacks: there is nothing to land",
        f"when the work reached the base another way, or there is none, lem task move "
        f"{slug} dropped ends the task",
    )


def emptied(
    record: Record, world: World, based: Based, ahead: int, where: str
) -> Refusal | None:
    """The refusal of a rebase that left the branch no commit of its own; None when it left
    one."""
    if ahead:
        return None
    now = replace(world, tip=based.tip)
    return lost(record, now, based, where) or nothing(record)


def empty(record: Record, world: World, facts: Facts, where: str) -> Refusal:
    """The refusal of a branch with no commit of its own before any rebase: the loss of a
    rebase on record, or of one a stop cut before its record (`ORIG_HEAD` still holds the
    change), else nothing to land."""
    found = lost(record, world, (record.landing or Landing()).based, where)
    if found is not None:
        return found
    if facts.orig is not None:
        return merge_only(record, world, "the change", facts.orig, where)
    return nothing(record)
