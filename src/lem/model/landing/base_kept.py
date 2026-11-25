"""The record `base` writes: where the branch is on the base, a conflict a builder resolves,
and the polish pass carried through the rebase (`land.cmd_base` and `land.through_rebase` on
`main`)."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.records.landing.record import Landing
from lem.records.landing.start import Resolution

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.base import Sha
    from lem.records.landing.start import Based
    from lem.records.record import Record


def resolved(landing: Landing, based: Based) -> Resolution | None:
    """The resolution of a conflict this landing met, once a builder rebased the branch past
    it: the tip he made, on the base he made it on. One that waits keeps its tip before."""
    found = landing.resolution
    if found is None or found.after != found.before:
        return found
    if based.tip == found.before:
        return found
    return replace(found, after=based.tip, base=based.base)


def kept(record: Record, based: Based, polish: Sha | None) -> Record:
    """The record with the branch on the base, a waiting resolution resolved, and the polish
    pass's last commit by its name after the rebase (`polish`)."""
    landing = record.landing or Landing()
    polished = landing.polished
    if polished is not None and polish is not None:
        polished = replace(polished, after=polish)
    changed = replace(
        landing,
        based=based,
        resolution=resolved(landing, based),
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
