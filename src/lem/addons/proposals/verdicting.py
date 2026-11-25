"""`lem proposals verdict`: the reviewer's verdict on each proposal written, under the records'
lock (`project.cmd_proposals_verdict` on `main`).

Every verdict is checked before any is written (`planning.py`). The items are written before
the records, so that a cut-off leaves a proposal with no verdict, which the next list gives
again, and never a verdict with no item; a refuted proposal's record entry keeps its form, since
its item names it.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.addons.proposals import days, drop_checks, item_files, planning
from lem.addons.proposals.judgment import Judgment
from lem.addons.proposals.record import DayRecord, Passed, Refuted
from lem.kernel import files
from lem.store import reviewer_items

if TYPE_CHECKING:
    import datetime as dt
    from pathlib import Path

    from lem.addons.proposals import verdicts
    from lem.addons.proposals.judging import Judged


def judged(state: Path, given: verdicts.VerdictsGiven, today: dt.date) -> Judgment:
    """Write the verdicts `given` on `today`: the items, then the records."""
    folder = state / reviewer_items.BACKLOG
    with reviewer_items.held(state):
        plan = planning.planned(folder, state, given, today)
        written(folder, plan)
        recorded(plan, today)
    refuted = (one.name for one in plan.judged if one.word == "refuted")
    return Judgment(
        day=today,
        refuted=tuple(refuted),
        items_made=tuple(made for made, _ in plan.made),
        decided_against=tuple(against for against, _ in plan.against),
    )


def removals(plan: planning.Plan) -> tuple[Path, ...]:
    """The refuted items that a verdict that passes their proposal removes."""
    passing = (one.name for one in plan.judged if one.word == "passed")
    return tuple(path for name in passing for path in plan.left.get(name, ()))


def changed_paths(plan: planning.Plan, leaving: tuple[Path, ...]) -> tuple[str, ...]:
    """The items the verdict can replace or remove, as paths from the checkout."""
    writes = (*plan.made, *plan.against)
    reused = (made.path for made, _ in writes)
    return (*reused, *(item_files.recorded(path.name) for path in leaving))


def written(folder: Path, plan: planning.Plan) -> None:
    """Write each item of the plan whole, then remove the refuted items of the proposals that
    pass now; refuse a change to a claimed item before the first write."""
    leaving = removals(plan)
    drop_checks.not_held(folder.parent, changed_paths(plan, leaving))
    folder.mkdir(parents=True, exist_ok=True)
    for made, text in (*plan.made, *plan.against):
        _, _, name = made.path.rpartition("/")
        files.write_whole(folder / name, text.encode())
    for path in leaving:
        path.unlink(missing_ok=True)


def recorded(plan: planning.Plan, today: dt.date) -> None:
    """Add each verdict to its day's record, and write each record whole."""
    paths = {made.area: made.path for made, _ in plan.made}
    for one in plan.judged:
        enter(plan.records, one, paths, today)
    for found in plan.records.values():
        days.write(*found)


def enter(
    records: verdicts.Records, one: Judged, paths: dict[str, str], today: dt.date
) -> None:
    """Put the record of the verdict `one`, with the verdict added, in `records`."""
    key = (one.named.kind, one.named.day.isoformat())
    path, record = records[key]
    records[key] = (path, entered(record, one, paths, today))


def entered(
    record: DayRecord, one: Judged, paths: dict[str, str], today: dt.date
) -> DayRecord:
    """The record with the verdict `one` added."""
    number = one.named.number
    if one.word == "refuted":
        entry = Refuted(number=number, reason=one.said, day=today)
        return msgspec.structs.replace(record, refuted=(*record.refuted, entry))
    item_path = paths[one.said]
    passed = Passed(number=number, area=one.said, item_path=item_path, day=today)
    return msgspec.structs.replace(record, passed=(*record.passed, passed))
