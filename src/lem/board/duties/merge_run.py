"""One merge the board server makes, in a thread of its own (`serve.merge_in_thread` on
`main`): a merge that waits for the merge lock, the base branch and the forge holds up no other
duty and no page.

The merge takes the task's step lock and the workspace's merge lock itself, as a session's
`lem land merge` does, so two merges of one workspace take turns. Before it starts, the count
of approved tasks that wait goes on record (`merge_line.py`). Its end is the line the task's
merge shows on the board (`Kept.said`) and in the server's log: merged, or why not. A refusal
the merge kept on record (a `Refused` of the tip) ends the duty for that tip; any other end
waits `memory.RETRY`.
"""

import threading
from typing import TYPE_CHECKING

from lem.app.landing import merge
from lem.board.duties import merge_line
from lem.kernel.errors import Fault, Refusal
from lem.model.landing.merge_asked import Asked
from lem.settings.load import settings_of

if TYPE_CHECKING:
    from lem.board.duties.context import Duty
    from lem.board.duties.memory import Key
    from lem.records.landing.merge import Merger
    from lem.records.record import Record


def started(
    duty: Duty, record: Record, by: Merger, records: tuple[Record, ...], key: Key
) -> None:
    """Note how many approved tasks wait, then start the merge of the proposed tip in a thread
    of its own; a failed merge waits under `key`."""
    slug = record.task.slug
    waited = waited_of(duty, record, by, records)
    merge_line.noted(duty.state, waited)
    asked = Asked(
        by=by,
        via="server",
        tip=waited.tip,
        standing=by == "owner",
        subject=subject_of(duty, record),
    )
    run = threading.Thread(
        target=ran, args=(duty, slug, asked, key), name=f"merge {slug}", daemon=True
    )
    duty.kept.merging[slug] = run
    duty.kept.said[slug] = f"Lem merges {slug}; the page shows the result when it ends."
    run.start()
    duty.say(
        f"{command_of(slug, asked)} started, with {waited.waiting} other approved tasks waiting"
    )


def waited_of(
    duty: Duty, record: Record, by: Merger, records: tuple[Record, ...]
) -> merge_line.Waited:
    """The merge line's record of this merge: the approved tasks that wait besides it."""
    slug = record.task.slug
    proposed = record.landing.proposed if record.landing else None
    behind = merge_line.approved(records, slug)
    tip = proposed.tip if proposed else ""
    waiting = len(behind)
    return merge_line.Waited(
        at=duty.now, task=slug, tip=tip, by=by, waiting=waiting, behind=behind
    )


def command_of(slug: str, asked: Asked) -> str:
    """The merge as the command of its words, for the server's log."""
    standing = " --standing" if asked.standing else ""
    return f"`lem land merge {slug} --by {asked.by} --via server{standing}`"


def subject_of(duty: Duty, record: Record) -> str | None:
    """The one commit's subject where the history is squashed: the pull request's title."""
    landing = record.landing
    pull = landing.pull if landing else None
    history = settings_of(duty.checkout).settings.branch.history
    return pull.title if history == "squash" and pull else None


def ran(duty: Duty, slug: str, asked: Asked, key: Key) -> None:
    """The merge, and its end as the board and the server's log say it."""
    try:
        merge.run(duty.checkout, slug, asked)
    except (Refusal, Fault) as error:
        duty.kept.ended(key, duty.now, ran=False)
        duty.kept.said[slug] = f"The merge did not go: {error}"
        duty.say(f"the server's merge of {slug} did not go: {error}")
        return
    duty.kept.ended(key, duty.now, ran=True)
    duty.kept.said[slug] = (
        f"Merged: {slug} is on the base. Within a minute the board's server wakes the task's "
        "session, or opens one, which removes its worktree."
    )
    duty.say(f"the server merged {slug}")
