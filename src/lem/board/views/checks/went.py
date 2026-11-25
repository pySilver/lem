"""A tab of a pruned task (`board_task.went_tab` on `main`): what went with its journal into one
summary, and the way to its Artifacts. A task's journal is pruned once nothing of it happened for
`state.keep_days` days after its end."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs.parts import Link
from lem.board.inputs.task.overview import Went
from lem.board.views.artifacts.addresses import tab_href
from lem.records.journal.task import Summary

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World

# What went, by the tab.
WENT = MappingProxyType(
    {
        "criteria": (
            "Its acceptance criteria, their approval, the personas’ read and its decisions"
        ),
        "checks": "Its runs of the checks, its review rounds and the proposal’s reasons",
        "timeline": "Its timeline and its events",
    }
)
SAID = (
    "{went} went with its events: they became one summary, as nothing of the task "
    "happened for state.keep_days days after its end. The Overview shows what the summary "
    "keeps and what its folder holds, and Artifacts lists the files that are there."
)


def pruned(seen: Seen) -> bool:
    """Whether the task's journal became one summary."""
    return any(isinstance(entry, Summary) for entry in seen.record.journal)


def went(world: World, seen: Seen, tab: str) -> Went:
    """The tab `tab` of a pruned task."""
    artifacts = Link(
        href=tab_href(world, seen.record.task.slug),
        label="Artifacts",
        title="Open the tab Artifacts · key 5",
        icon="folder",
        frame=True,
    )
    said = SAID.format(went=WENT[tab])
    return Went(id=f"went-{tab}", said=said, artifacts=artifacts)
