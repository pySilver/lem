"""The stages of a task drawn behind every lane (`stage_of` and `band` of `time_of` on `main`):
the criteria, the plan, each task of the plan, the build after them, an investigation, the fast
track's change, the queue, the checks and the review, and the pull request. A held, blocked or
parked task stays in the stage it was in; criteria that wait come before any plan. Two stretches
of one stage in a row are one band.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.views import rule
from lem.board.views.timeline import plan_stages
from lem.board.views.timeline.blocks import Block, blocks_of
from lem.board.views.timeline.shapes import Stage

if TYPE_CHECKING:
    from collections.abc import Iterator

    from lem.board.views.timeline import frame
    from lem.records.record import Record

CRITERIA = ("criteria", "Acceptance criteria", "Criteria")
CHECKS = ("checks", "Checks and review", "Checks")
BY_STATUS = MappingProxyType(
    {
        "planned": plan_stages.PLAN,
        "queued": ("queued", "Queued", "Queued"),
        "ready": CHECKS,
        "landing": CHECKS,
        "open": ("pr", "Pull request", "PR"),
    }
)


def stages(record: Record, drawn: frame.Frame) -> list[Stage]:
    """The task's stages from its first moment, one band for two stretches of one stage in a
    row."""
    found: list[Stage] = []
    for stage in stretched(record, drawn):
        if found and joins(found[-1], stage):
            found[-1] = joined(found[-1], stage)
        else:
            found.append(stage)
    return found


def joined(last: Stage, stage: Stage) -> Stage:
    """The stage before, gone on to the end of `stage`."""
    return last._replace(end=stage.end, live=stage.live)


def joins(last: Stage, stage: Stage) -> bool:
    """Whether `stage` goes on the stage before it."""
    return last.key == stage.key and last.end == stage.start


def stretched(record: Record, drawn: frame.Frame) -> Iterator[Stage]:
    """Each state's stage, a build cut by the tasks of its plan."""
    blocks = blocks_of(record, drawn)
    if blocks and drawn.start < blocks[0].start:
        yield Stage(*CRITERIA, drawn.start, blocks[0].start)
    before = Stage(*CRITERIA, drawn.start, drawn.start)
    running = [each for each in blocks if each.noted.status not in rule.ENDED]
    for block in running:
        found = list(stages_of(record, block, before))
        yield from found
        before = found[-1] if found else before


def stages_of(record: Record, block: Block, before: Stage) -> Iterator[Stage]:
    """A state's stages: a build's, its status's, or for a held state the stage it was in."""
    status = block.noted.status
    held = block.noted.hold is not None
    if not held and status == "building":
        yield from plan_stages.building(record, block)
    elif not held and status in BY_STATUS:
        named = BY_STATUS[status]
        yield Stage(*named, block.start, block.end, live=block.live)
    else:
        yield before._replace(start=block.start, end=block.end, live=block.live)
