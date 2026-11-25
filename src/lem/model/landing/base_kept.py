"""The record `base` writes: where the branch is on the base, a conflict a builder resolves,
and the polish pass carried through the rebase (`land.cmd_base` and `land.through_rebase` on
`main`)."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.records.landing.record import Landing
from lem.records.landing.start import Based, Resolution

if TYPE_CHECKING:
    from lem.model.landing.rebased import Paths
    from lem.model.landing.world import World
    from lem.records.base import Sha
    from lem.records.landing.start import Polished
    from lem.records.record import Record


def resolved(
    landing: Landing, based: Based, files: tuple[str, ...]
) -> Resolution | None:
    """The resolution of a conflict this landing met, once a builder rebased the branch past
    it: the tip he made, on the base he made it on, with every file git's merge meets a
    conflict in (`files`). One that waits keeps its tip before."""
    found = landing.resolution
    if found is None or found.after != found.before:
        return found
    if based.tip == found.before:
        return found
    joined = tuple(sorted({*found.files, *files}))
    return replace(found, after=based.tip, base=based.base, files=joined)


def kept(
    record: Record, based: Based, polished: Polished | None, files: Paths = ()
) -> Record:
    """The record with the branch on the base, a waiting resolution resolved with `files`,
    and the polish pass carried through the rebase."""
    landing = record.landing or Landing()
    changed = replace(
        landing,
        based=based,
        resolution=resolved(landing, based, files),
        polished=polished,
    )
    return replace(record, landing=changed)


def conflicted(record: Record, world: World, files: tuple[str, ...]) -> Record:
    """The record of a conflict with the base: the files a builder resolves and the tip before
    it, which a conflict met before in this landing keeps."""
    landing = record.landing or Landing()
    found = landing.resolution
    tip = world.tip or world.base
    if found is not None and found.after == found.before:
        joined = tuple(sorted({*found.files, *files}))
        waiting = replace(found, files=joined, base=world.base)
    else:
        waiting = Resolution(files=files, before=tip, after=tip, base=world.base)
    return replace(record, landing=replace(landing, resolution=waiting))


def marked(record: Record, world: World, fork: Sha) -> Record:
    """The record before a rebase: the tip as it is, on the commit it forked from origin's
    base (`fork`), so that a stop between the rebase and its record still names the tip
    before it, which git's `ORIG_HEAD` confirms (`base_after.recovered`)."""
    landing = record.landing or Landing()
    tip, now = world.tip or fork, world.now
    mark = Based(tip=tip, base=fork, before=tip, carried=False, at=now)
    changed = replace(landing, based=mark)
    return replace(record, landing=changed)


def unmarked(record: Record, based: Based | None) -> Record:
    """The record with `based` as it was before the mark of a rebase that was undone."""
    landing = record.landing or Landing()
    return replace(record, landing=replace(landing, based=based))
