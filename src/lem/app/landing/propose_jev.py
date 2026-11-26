"""Jev's read at a proposal (`model/landing/propose_jev.py`): ask once about a finding
called under the bar and keep the answer before refusing one Jev reads as over the bar."""

from typing import TYPE_CHECKING

from lem.app.landing import jev_reads
from lem.model.landing import propose_jev
from lem.ports import judge as jev
from lem.records.landing.review import JevRead

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.records.base import Moment
    from lem.records.record import Record

type Words = dict[str, propose_jev.Said]


def ask(judge: jev.Judge, finding: propose_jev.Asked) -> propose_jev.Said:
    """Jev's word on one finding."""
    defect = jev.Defect(where=finding.where, title=finding.title, what=finding.what)
    said = judge.over_bar(defect)
    if isinstance(said, jev.NotAsked):
        return propose_jev.Said(why=said.why)
    return propose_jev.Said(score=said.score)


def read(
    context: Context, findings: tuple[propose_jev.Asked, ...]
) -> tuple[Words, Record]:
    """Read each finding once and save its verdict before a refusal."""
    before = {
        one.key: propose_jev.Said(score=one.score, why=one.not_asked)
        for one in jev_reads.of(context.record)
        if one.path is None
    }
    fresh = {
        finding.key: ask(context.ports.judge, finding)
        for finding in findings
        if finding.key not in before
    }
    saved = jev_reads.kept(context, entries(fresh, context.world.now))
    refused = propose_jev.refused(context.record.task.slug, fresh)
    if refused is not None:
        raise refused
    return before | fresh, saved


def entries(words: Words, at: Moment) -> tuple[JevRead, ...]:
    """The bar verdicts the record keeps, without an item path."""
    return tuple(
        JevRead(key=key, score=said.score, not_asked=said.why, at=at)
        for key, said in words.items()
    )
