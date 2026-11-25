"""The reviewer's verdicts as `lem proposals verdict --file` gives them, each checked against the
records before any is written (`project.cmd_proposals_verdict` on `main`).

A verdict names one proposal as the list gives it, `retro of DATE #N`, and either refutes it
with a reason or passes it with its area; `titles` gives each area that passed the title of its
item. A proposal with a verdict already keeps it.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.addons.proposals import days, names
from lem.addons.proposals.record import Area
from lem.kernel.errors import Refusal
from lem.records.base import Frozen

if TYPE_CHECKING:
    from pathlib import Path

    from lem.addons.proposals.record import DayRecord, Proposal

LIST = "lem proposals list gives the proposals with no verdict"
FORM = (
    '{"verdicts": [{"proposal": "retro of DATE #N", "refuted": REASON} or '
    '{"proposal": ..., "passed": AREA}, ...], "titles": {"AREA": "TITLE"}}'
)

type Records = dict[tuple[str, str], tuple[Path, DayRecord]]


class VerdictGiven(Frozen, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """One verdict: the proposal, and its reason or its area."""

    proposal: str
    refuted: str | None = None
    passed: Area | None = None


class VerdictsGiven(Frozen, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The verdicts, and the title of each area's item."""

    verdicts: tuple[VerdictGiven, ...]
    titles: dict[str, str] = msgspec.field(default_factory=dict)


def call_of(verdict: VerdictGiven) -> tuple[str, str]:
    """`refuted` and its reason, or `passed` and its area; refused for both, or neither, or
    an empty reason."""
    given = (("refuted", verdict.refuted), ("passed", verdict.passed))
    calls = [(word, said) for word, said in given if said is not None]
    written = all(said.strip() for _, said in calls)
    if len(calls) != 1 or not written:
        raise Refusal(
            "verdict-form",
            f"the verdict on {verdict.proposal!r} does not refute it with a reason or pass "
            "it with an area, one of the two",
            f"give {FORM}",
        )
    return calls[0]


def named_of(verdict: VerdictGiven, seen: set[names.Named]) -> names.Named:
    """The proposal the verdict names; refused for no such name, or a second verdict."""
    named = names.parsed(verdict.proposal)
    if named is None:
        raise Refusal(
            "verdict-name",
            f"a verdict names {verdict.proposal!r}, which is no proposal's name",
            f"name it as the list does, retro of DATE #N or night of DATE #N; {LIST}",
        )
    if named in seen:
        raise Refusal(
            "verdict-twice",
            f"{verdict.proposal} has two verdicts here",
            "give it one",
        )
    seen.add(named)
    return named


def record_of(state: Path, named: names.Named, records: Records) -> DayRecord:
    """The record of the proposal, read once for every verdict on its day; refused when there
    is none."""
    key = (named.kind, named.day.isoformat())
    if key not in records:
        path = days.path_of(state, named.kind, named.day)
        found = days.read(path, named.kind)
        if found is None:
            raise Refusal(
                "verdict-record",
                f"there is no record of the {named.kind} of {named.day} ({path})",
                LIST,
            )
        records[key] = (path, found)
    return records[key][1]


def proposal_of(named: names.Named, record: DayRecord) -> Proposal:
    """The proposal the name gives in its record; refused for a number past its proposals, or
    a proposal with a verdict already."""
    name = names.name_of(named.kind, named.day, named.number)
    if named.number > len(record.proposals):
        raise Refusal(
            "verdict-number",
            f"{name}: the record of its day has {len(record.proposals)} proposals",
            LIST,
        )
    judged = (entry.number for entry in (*record.refuted, *record.passed))
    if named.number in set(judged):
        raise Refusal(
            "verdict-again", f"{name} has a verdict already, which stays", LIST
        )
    return record.proposals[named.number - 1]
