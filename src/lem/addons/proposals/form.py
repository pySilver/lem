"""The rules of a day's record that its types alone do not hold (`project.record_problem` on
`main`): its day and kind are its file's, its proposals go 1, 2, 3 with every text written, each
is added by one run, and each verdict names a proposal of the record once, never refuted and
passed at once, and a drop only of one that passed."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import datetime as dt

    from lem.addons.proposals.record import DayRecord, Kind, Proposal


def problem(record: DayRecord, kind: Kind, day: dt.date) -> str | None:
    """Why `record` is not the record of `kind`'s proposals of `day`, or None when it is."""
    found = (
        named_problem(record, kind, day),
        numbered_problem(record.proposals),
        runs_problem(record),
        verdicts_problem(record),
    )
    return next((said for said in found if said), None)


def named_problem(record: DayRecord, kind: Kind, day: dt.date) -> str | None:
    """Why its day or kind is not the one its file's name and folder say."""
    if record.date != day:
        return f"its date is {record.date}, and its name says {day}"
    if record.kind != kind:
        return f"its kind is {record.kind}, and its folder holds the {kind}'s"
    return None


def numbered_problem(proposals: tuple[Proposal, ...]) -> str | None:
    """Why the proposals do not go 1, 2, 3 in order with every text written."""
    for number, proposal in enumerate(proposals, 1):
        if proposal.number != number:
            return (
                f"its proposal {number} has the number {proposal.number}: the numbers "
                "go 1, 2, 3 in order"
            )
        texts = (proposal.move, proposal.body, proposal.source, proposal.where)
        if not all(text.strip() for text in texts):
            return f"proposal {number} has an empty move, body, source or where"
    return None


def runs_problem(record: DayRecord) -> str | None:
    """Why the runs do not add up to the proposals, each added by one run."""
    added = sorted(number for run in record.runs for number in run.proposals)
    if added != list(range(1, len(record.proposals) + 1)):
        return (
            "its runs do not add up to its proposals: each proposal is added by one run"
        )
    return None


def verdicts_problem(record: DayRecord) -> str | None:
    """Why a verdict or a drop names a proposal the record has not, or twice, or a proposal
    refuted and passed at once, or dropped with no pass."""
    known = frozenset(range(1, len(record.proposals) + 1))
    refuted = tuple(entry.number for entry in record.refuted)
    passed = tuple(entry.number for entry in record.passed)
    dropped = tuple(entry.number for entry in record.dropped)
    found = (
        entries_problem("refuted", refuted, known),
        entries_problem("passed", passed, known),
        entries_problem("dropped", dropped, known),
        exclusive_problem(set(refuted), set(passed), set(dropped)),
    )
    return next((said for said in found if said), None)


def entries_problem(
    key: str, numbers: tuple[int, ...], known: frozenset[int]
) -> str | None:
    """Why the list `key` names a proposal the record has not, or one twice."""
    unique = set(numbers)
    if len(unique) != len(numbers) or not unique <= known:
        return f"`{key}` names a proposal the record has not, or names one twice"
    return None


def exclusive_problem(
    refuted: set[int], passed: set[int], dropped: set[int]
) -> str | None:
    """Why a proposal is refuted and passed at once, or dropped with no pass."""
    if refuted & passed:
        return f"the proposal {min(refuted & passed)} is refuted and passed at once"
    if not dropped <= passed:
        return f"the proposal {min(dropped - passed)} is dropped, and it passed into no item"
    return None
