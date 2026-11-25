"""Jev's read at a proposal (`model/landing/propose_jev.py`): each finding called under the bar
that Jev has not read is asked once through the `Judge` port, and its word kept at once in the
task's `jev.json`, so that no finding is sent twice, by this run or the next; a finding Jev
reads as over the bar stops the step once.

A machine where Jev has no adapter is a finding not asked, with that reason: Jev's read never
stops the landing for good.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.app import wiring
from lem.kernel import files
from lem.model.landing import propose_jev
from lem.ports import judge as jev
from lem.store import guard

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.landing.frame import Context

KEPT = "jev.json"
type Words = dict[str, propose_jev.Said]


def kept(folder: Path) -> Words:
    """Jev's words kept for the task, by finding."""
    path = folder / KEPT
    if not path.is_file():
        return {}
    return msgspec.json.decode(path.read_bytes(), type=Words)


def ask(judge: jev.Judge, finding: propose_jev.Asked) -> propose_jev.Said:
    """Jev's word on one finding."""
    if isinstance(judge, wiring.Unbound):
        return propose_jev.Said(why="Jev has no adapter on this machine")
    defect = jev.Defect(where=finding.where, title=finding.title, what=finding.what)
    said = judge.over_bar(defect)
    if isinstance(said, jev.NotAsked):
        return propose_jev.Said(why=said.why)
    return propose_jev.Said(score=said.score)


def read(context: Context, findings: tuple[propose_jev.Asked, ...]) -> Words:
    """Jev's word on each finding, asking only about those it has not read, kept before a
    refusal of the ones it reads as over the bar."""
    before = kept(context.folder)
    judge = context.ports.judge
    fresh = {
        finding.key: ask(judge, finding)
        for finding in findings
        if finding.key not in before
    }
    if fresh:
        guard.writable(context.workspace.state)
        words = msgspec.json.encode(before | fresh)
        files.write_whole(context.folder / KEPT, words)
    refused = propose_jev.refused(context.record.task.slug, fresh)
    if refused is not None:
        raise refused
    return before | fresh
