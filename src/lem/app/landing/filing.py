"""`lem land file`: each defect a review saw outside the change gets its place (`land.cmd_file`
on `main`).

In a clean worktree only: the places are decided (`model.landing.filing`), Jev is asked whether
a defect about to get a file of its own is one an item holds already, and nothing is written
when it names one. Then each item is written and committed (`app/landing/filing_commits.py`),
and the record names each place, and the checks moved to the new tip with the items in
`items_after`, which ask for no check and no review again. A run cut off after a commit finds
each item again by its defect.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import backlog, changes, filing_commits, judge_same
from lem.kernel.errors import Refusal
from lem.model.landing import filing, filing_flags
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.app.landing import frame
    from lem.records.landing.review import Filed
    from lem.records.record import Record


def clean_or_refused(context: frame.Context) -> None:
    """Refuse a worktree with a change nobody committed."""
    if context.world.clean:
        return
    slug = context.record.task.slug
    raise Refusal(
        "dirty",
        f"the worktree of {slug} has a change nobody committed",
        f"a builder commits it or removes it, then lem land file {slug} runs again",
    )


def filed(
    record: Record, *, places: tuple[Filed, ...], done: filing_commits.Committed
) -> Record:
    """The record with each place, a place given again replacing the one before, and the
    checks moved to the commit `file` made with the items in `items_after`."""
    landing = record.landing or Landing()
    named = {place.finding for place in places}
    kept = tuple(one for one in landing.filed if one.finding not in named)
    checked = landing.checked
    if done.written and checked is not None:
        after = (*checked.items_after, *done.written)
        checked = replace(checked, tip=done.tip, tree=done.tree, items_after=after)
    return changes.landing(record, filed=(*kept, *places), checked=checked)


def act(context: frame.Context, *, flags: filing_flags.Flags) -> tuple[Filed, ...]:
    """Give each waiting defect its place, write and commit its items, and record them."""
    clean_or_refused(context)
    tip = context.world.tip or ""
    shelf = backlog.shelf(context.ports.git, context.worktree, tip)
    placed = filing.decide(context.record, context.world, shelf, flags)
    if isinstance(placed, Refusal):
        raise placed
    refused = judge_same.checked(context, placed.asks, shelf)
    if refused is not None:
        raise refused
    done = filing_commits.committed(context, placed.writes)
    context.write(context.record, partial(filed, places=placed.filed, done=done))
    return placed.filed
