"""The tab Overview of a task (`board_task.overview_tab` on `main`): its cards in their order. A
task whose journal became one summary opens with that summary and draws no progress, whose
checks, review and decisions went with its events and would read as none."""

from typing import TYPE_CHECKING

from lem.board.inputs.task.overview import Overview
from lem.board.views.panel import asked, building, progress, pruned, review, verdict
from lem.board.views.panel.answered import answered
from lem.board.views.panel.breaker import breaker
from lem.board.views.panel.now import now

if TYPE_CHECKING:
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World
    from lem.model.owner.looks import Rows


def overview(
    world: World,
    seen: Seen,
    rows: Rows,
    standing: Standing,
    keep_days: int | None = None,
) -> Overview:
    """The Overview of the task of `seen`, with its rows of what waits for the owner and
    the days a pruned task's folder kept everything (`state.keep_days`, None while the
    settings do not read)."""
    summary = pruned.pruned(world, seen, standing, keep_days)
    shared = {
        "building": building.building(world, seen),
        "verdict": verdict.verdict(world, seen),
        "now": now(world, seen, rows, standing),
    }
    if summary is not None:
        return Overview(pruned=summary, **shared)
    cards = asked.cards(world, rows)
    return Overview(
        answered=answered(world, seen),
        cards=cards,
        cards_said=asked.cards_said(len(cards)),
        review=review.review(world, seen),
        parked=asked.parked(world, seen),
        breaker=breaker(world, seen, rows),
        phases=progress.progress(world, seen, standing),
        **shared,
    )
