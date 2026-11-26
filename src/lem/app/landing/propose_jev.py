"""Jev's read at a proposal (`model/landing/propose_jev.py`): ask once about a finding
called under the bar and keep the answer before refusing one Jev reads as over the bar."""

from dataclasses import replace as with_record
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import jev_reads, judge_same
from lem.model.landing import propose_jev
from lem.ports import judge as jev
from lem.records.landing.review import JevRead

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.records.base import Moment
    from lem.records.record import Record

type Words = dict[str, JevRead]
type Findings = tuple[propose_jev.Asked, ...]


def ask(judge: jev.Judge | None, finding: propose_jev.Asked, at: Moment) -> JevRead:
    """Jev's word on one finding."""
    if judge is None:
        return JevRead(key=finding.key, at=at, not_asked="off in the settings")
    found = finding.defect
    defect = jev.Defect(where=found.where, title=found.title, what=found.what)
    said = judge.over_bar(defect)
    if isinstance(said, jev.NotAsked):
        return JevRead(key=finding.key, at=at, not_asked=said.why)
    return JevRead(key=finding.key, at=at, score=said.score)


def gathered(
    context: Context, findings: Findings, judge: jev.Judge | None
) -> tuple[Context, Words]:
    """Ask once about each finding and save each answer before the next call."""
    reads: Words = {}
    for known in jev_reads.of(context.record):
        if known.path is None:
            reads[known.key] = known
    for finding in findings:
        if finding.key in reads:
            continue
        said = ask(judge, finding, context.world.now)
        context = with_record(
            context,
            record=jev_reads.kept_all(context, (*jev_reads.of(context.record), said)),
        )
        reads[said.key] = said
    return context, reads


def stop(context: Context, over: dict[propose_jev.Asked, float]) -> None:
    """Keep which findings stopped the proposal before giving the refusal."""
    keys = {one.key for one in over}
    reads = []
    for one in jev_reads.of(context.record):
        if one.path is None and one.key in keys:
            reads.append(replace(one, refused=True))
        else:
            reads.append(one)
    jev_reads.kept_all(context, tuple(reads))
    raise propose_jev.refused(
        context.record.task.slug,
        {finding.label: score for finding, score in over.items()},
    )


def read(context: Context, findings: Findings) -> tuple[Words, Record]:
    """Check the saved verdicts against the findings as they stand on this proposal."""
    judge = (
        context.ports.judge
        if findings and judge_same.sends(context.workspace.checkout)
        else None
    )
    context, reads = gathered(context, findings, judge)
    over = {
        one: score
        for one in findings
        if (score := propose_jev.blocked(one, reads[one.key])) is not None
    }
    if over:
        stop(context, over)
    return {one.label: reads[one.key] for one in findings}, context.record
