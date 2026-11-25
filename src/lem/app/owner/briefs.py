"""Each row of what waits as an entry of `lem waiting`, with the facts of its kind
(`project.cmd_waiting` on `main`): a task with no session says what it lacks, a stopped one the
command that opens a fresh session, a card its page and prompt, a task queued after a dropped one
the owner's two words, a block its line and fix, a merge review its why, and a pull request its
address, green or each reason it is not, the forge's conflict, the merge agent's read and a
refusal of its merge."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.owner.entries import Entry
from lem.model.landing import merge, merge_asked, merge_standing, mergeread
from lem.model.owner import verbs
from lem.records.holds import Blocked, OwnerHold, ReleaseHold
from lem.records.journal.task import StateNoted
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.owner.looks import Look, Row
    from lem.records.record import Record


def brief(record: Record) -> Entry:
    """The entry of a task, with no fact of a kind yet."""
    task = record.task
    return Entry(
        task=task.slug,
        ask=task.ask,
        since=task.since,
        night=task.night,
        line=line_of(record),
    )


def line_of(record: Record) -> str | None:
    """The task's line: its wait's own, else the newest state line of its journal."""
    hold = record.task.hold
    if isinstance(hold, OwnerHold):
        return hold.line
    if isinstance(hold, Blocked):
        return hold.why
    lines = [
        entry.line
        for entry in record.journal
        if isinstance(entry, StateNoted) and entry.line
    ]
    return lines[-1] if lines else None


def entry_of(row: Row, look: Look) -> Entry:
    """The entry of a row, with the facts of its kind."""
    record = look.record
    found = brief(record)
    slug = record.task.slug
    if row.kind == "session":
        return replace(found, need="deaf" if row.deaf else "gone")
    if row.kind == "stopped":
        command = f"lem session open {slug} --why stopped"
        return replace(found, open=command, unread=row.unread)
    if row.kind == "card":
        return replace(found, page=row.card, prompt=row.prompt)
    if row.kind == "review":
        return replace(found, why=row.why, tip=row.tip)
    return kept_entry(row, look, found)


def kept_entry(row: Row, look: Look, found: Entry) -> Entry:
    """The entry of a task queued after a dropped one, a block, or a merge."""
    record = look.record
    slug = record.task.slug
    if row.kind == "after_dropped":
        verb = verbs.verb(row, record.task, record.landing)
        start, drop = f"start {slug} now", f"/lem drop {slug}"
        return replace(
            found, since=row.since, after=row.after, start=start, drop=drop, verb=verb
        )
    if row.kind == "blocked":
        return blocked_entry(record, found)
    if row.kind == "merge":
        return pull_entry(record, found, conflict=row.conflict)
    return found


def blocked_entry(record: Record, found: Entry) -> Entry:
    """A block's entry: the release stop's message, or the block's line and its fix."""
    hold = record.task.hold
    if isinstance(hold, ReleaseHold):
        return replace(found, line=hold.say)
    if isinstance(hold, Blocked):
        return replace(found, fix=hold.fix)
    return found


def pull_entry(record: Record, found: Entry, *, conflict: bool) -> Entry:
    """A pull request's entry: its address, green or why not, the forge's conflict, the merge
    agent's newest read of the tip, and a refusal of its merge."""
    landing = record.landing or Landing()
    proposed = landing.proposed
    reasons = merge_standing.reasons_now(record) if proposed else None
    if proposed is not None and not reasons and merge_asked.contract_moved(record):
        reasons = (merge.MOVED,)
    refused = landing.refused
    if refused is not None and (proposed is None or refused.tip != proposed.tip):
        refused = None
    return replace(
        found,
        pull_request=landing.pull,
        green=not reasons if proposed else None,
        not_green=reasons,
        conflict=conflict,
        merge_review=mergeread.latest(landing),
        merge_refused=refused,
    )
