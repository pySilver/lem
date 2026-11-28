"""The base commit and tree each open task's merge reads, and whether a part names the task (a
feature, which the owner merges)."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from lem.model.landing import destination
from lem.model.owner.looks import MergeBasis

if TYPE_CHECKING:
    from lem.app.sessions.here import Here
    from lem.records.record import Record
    from lem.settings.team import Branch

type Head = tuple[str | None, str | None]


@dataclass(frozen=True, kw_only=True, slots=True)
class Bases:
    """The last fetched commit and tree of each destination that open tasks need, and the
    tasks a part names."""

    settings: Branch | None = None
    refs: dict[str, Head] = field(default_factory=dict)
    features: frozenset[str] = frozenset()

    def for_task(self, record: Record) -> MergeBasis:
        """The recorded destination of this task, or the workspace default."""
        if self.settings is None:
            return MergeBasis()
        ref = destination.recorded(record.landing) or self.settings.base
        head, tree = self.refs.get(ref or "", (None, None))
        feature = record.task.slug in self.features
        return MergeBasis(
            base=head, tree=tree, land=self.settings.land, feature=feature
        )


def gathered(here: Here, branch: Branch | None, records: tuple[Record, ...]) -> Bases:
    """Read each needed destination once for merge reviews and standing approvals."""
    if branch is None:
        return Bases()
    refs = {
        destination.recorded(record.landing) or branch.base
        for record in records
        if needs_base(record)
    }
    named = {record.task.part_of for record in records}
    return Bases(
        settings=branch,
        refs={ref: read_base(here, ref) for ref in refs if ref},
        features=frozenset(slug for slug in named if slug is not None),
    )


def needs_base(record: Record) -> bool:
    """An open task with a merge review or an approval reads its destination."""
    landing = record.landing
    return bool(
        record.task.status == "open" and landing and (landing.reads or landing.standing)
    )


def read_base(here: Here, ref: str) -> Head:
    """Origin's last fetched commit and its tree."""
    checkout, git = here.where.checkout, here.ports.git
    head = git.remote_head(checkout, ref)
    return head, git.tree(checkout, head) if head else None
