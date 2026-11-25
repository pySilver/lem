"""What one run of retention tells: what went of each old task's folder, each journal folded
into its summary, the old folders, the totals, and what was skipped and failed."""

import msgspec

from lem.records.base import Frozen, Moment
from lem.store.retention.files import Failed, Skipped
from lem.store.retention.folders import Folder


class Kept(Frozen, frozen=True, kw_only=True):
    """An old ended task: its status, the files that went (or would go) and their bytes."""

    task: str
    status: str
    files: tuple[str, ...]
    bytes: int


class Folded(Frozen, frozen=True, kw_only=True):
    """A task whose journal became (or would become) its summary, and how many entries it
    folded."""

    task: str
    status: str
    entries: int


class Pruned(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """What one run did, or in a dry run would do: the days and where the number came from,
    the cutoff, each old task and what went of it, each journal folded and its entries, the old
    folders, the totals, how many tasks were open, young and old, and what was skipped and
    failed."""

    dry_run: bool
    keep_days: int
    source: str = msgspec.field(name="from")
    before: Moment
    state: str
    tasks: tuple[Kept, ...] = ()
    summarized: tuple[Folded, ...] = ()
    entries: int = 0
    folders: tuple[Folder, ...] = ()
    files: int = 0
    bytes: int = 0
    open: int = 0
    young: int = 0
    old: int = 0
    skipped: tuple[Skipped, ...] = ()
    failed: tuple[Failed, ...] = ()
