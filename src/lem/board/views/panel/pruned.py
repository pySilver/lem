"""A task whose journal became one summary (`board_task.summary_card`, `files_line` and
`went_tab` on `main`): the Overview's first card says so, what the summary keeps, what went with
the events and what the folder holds now; each tab whose detail went says so in one line."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs.names import plural, task_href
from lem.board.inputs.parts import Link
from lem.board.inputs.task.overview import Pruned, Went
from lem.board.views.panel.folder_line import files_line
from lem.board.views.panel.kept import kept
from lem.records.journal.task import Summary

if TYPE_CHECKING:
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World

# What went with the events of a summarized task, by the tab that showed it.
WENT = MappingProxyType(
    {
        "criteria": (
            "Its acceptance criteria, their approval, the personas’ read and its "
            "decisions"
        ),
        "checks": "Its runs of the checks, its review rounds and the proposal’s reasons",
        "timeline": "Its timeline and its events",
    }
)


def lowered(said: str) -> str:
    """A line with its first letter small, to stand in a sentence."""
    return said[:1].lower() + said[1:]


LOWERED = tuple(lowered(said) for said in WENT.values())
GONE = "; ".join(LOWERED)


def summary_of(seen: Seen) -> Summary | None:
    """The summary the task's journal became, or None."""
    return next((one for one in seen.record.journal if isinstance(one, Summary)), None)


def pruned(
    world: World, seen: Seen, standing: Standing, keep_days: int | None
) -> Pruned | None:
    """The Overview's first card of a summarized task, or None for any other."""
    summary = summary_of(seen)
    if summary is None:
        return None
    facts = "; ".join(kept(world, seen, standing))
    return Pruned(
        events=plural(summary.entries, "event"),
        kept=f"{facts}.",
        went=f"{GONE}.",
        files=files_line(seen, keep_days),
        artifacts=artifacts_link(world, seen.record.task.slug),
    )


def went(world: World, seen: Seen, tab: str) -> Went:
    """The one line of a tab of a summarized task whose detail went with its events."""
    said = (
        f"{WENT[tab]} went with its events: they became one summary, as nothing of the "
        "task happened for state.keep_days days after its end. The Overview shows what "
        "the summary keeps and what its folder holds, and Artifacts lists the files that "
        "are there."
    )
    link = artifacts_link(world, seen.record.task.slug)
    return Went(id=f"went-{tab}", said=said, artifacts=link)


def artifacts_link(world: World, slug: str) -> Link:
    """The link to the tab Artifacts."""
    return Link(
        href=task_href(world.viewer.base, slug, "artifacts", world.viewer.view),
        label="Artifacts",
        title="Open the tab Artifacts · key 5",
        icon="folder",
        frame=True,
    )
