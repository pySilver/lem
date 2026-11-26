"""The run of the checks as the record keeps it, and its end in the journal with the owner's
line (`land.checks_say` and the `gate.end` of `land.checks_run` on `main`)."""

import dataclasses
import time
from typing import TYPE_CHECKING

from lem.app.landing import changes, checks_record
from lem.model.criteria import contract
from lem.model.landing import checks_said, merge_recheck, phases
from lem.records.journal.landing import CheckEnd, CommandEnd
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.app.landing.checks_verdict import Verdict
    from lem.model.landing.world import World
    from lem.records.base import Moment
    from lem.records.record import Record


def timed(verdict: Verdict, ticked: float) -> Verdict:
    """The verdict with how long its run took since `ticked`, by the monotonic clock, which no
    change of the wall clock moves (`land.checks_run` on `main`)."""
    return dataclasses.replace(verdict, seconds=round(time.monotonic() - ticked))


def end_of(record: Record, world: World, verdict: Verdict, at: Moment) -> CheckEnd:
    """The run's end in the journal, with the owner's line: after a pass, whether the review
    runs or no review is due."""
    run = verdict.run
    failed = tuple(outcome.command for outcome in run.outcomes if not outcome.passed)
    after = phases.due(changes.landing(record, checked=run), world)
    said = checks_said.ended(
        record.task.slug,
        run.outcome,
        failed,
        verdict.refused,
        review=after.step == "read",
    )
    commands = tuple(
        CommandEnd(name=outcome.command, passed=outcome.passed, last=outcome.last)
        for outcome in run.outcomes
    )
    return CheckEnd(
        at=at,
        outcome=run.outcome,
        say=said,
        commands=commands,
        tip=run.tip,
        seconds=verdict.seconds,
        taken=next((one.taken_at for one in run.criteria if one.taken_at), None),
    )


def kept(record: Record, *, world: World, verdict: Verdict, at: Moment) -> Record:
    """The record with the run and its end; on the fast track, a lowered bar takes the task to
    the standard track. A passed run of a contract that moved since it began is refused, not
    written: it is no evidence of the contract of now."""
    if verdict.run.outcome == "passed":
        refused = contract.moved(record.task, verdict.contract)
        if refused is not None:
            raise refused
    end = end_of(record, world, verdict, at)
    changed = checks_record.checked(record, run=verdict.run, end=end)
    refused = merge_recheck.red(
        record.landing or Landing(),
        verdict.run,
        end,
        code=None if verdict.refusal is None else verdict.refusal.code,
    )
    if refused is not None:
        changed = changes.landing(changed, refused=refused)
    if not verdict.reshape:
        return changed
    slug = record.task.slug
    line = (
        f"{slug} lowers the bar, which a task on the fast track never does: it takes the "
        "standard track, and the interview comes first"
    )
    return checks_record.reshaped(changed, line=line, at=at)
