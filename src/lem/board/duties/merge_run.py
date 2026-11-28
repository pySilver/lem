"""One merge the board server makes, in a thread of its own (`serve.merge_in_thread` on
`main`): a merge that waits for the merge lock, the base branch and the forge holds up no other
duty and no page.

The merge takes the task's step lock and the workspace's merge lock itself, as a session's
`lem land merge` does, so two merges of one workspace take turns. At the forge call, the count
of approved tasks that wait goes on record (`merge_line.py`). Its end is the line the task's
merge shows on the board (`Kept.said`) and in the server's log: merged, or why not. A refusal
the merge kept on record (a `Refused` of the tip) ends the duty for that tip; any other end
waits `memory.RETRY`.
"""

import threading
from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import merge, parts
from lem.board import merge_look
from lem.board.duties import merge_count, merge_said
from lem.kernel import clock, errors
from lem.model.landing import merge_asked

if TYPE_CHECKING:
    from lem.board.duties.context import Duty
    from lem.board.duties.memory import Key
    from lem.records import record as records
    from lem.records.landing.merge import Merger


def started(duty: Duty, record: records.Record, by: Merger, key: Key) -> bool:
    """Start the proposed tip's merge in a thread; a failure waits under `key`."""
    slug = record.task.slug
    proposed = record.landing.proposed if record.landing else None
    asked = merge_asked.Asked(
        by=by,
        via="server",
        tip=proposed.tip if proposed else None,
        standing=by == "owner",
        subject=subject_of(duty, record),
    )
    run = threading.Thread(
        target=ran, args=(duty, slug, asked, key), name=f"merge {slug}", daemon=True
    )
    return duty.kept.start_merge(slug, run)


def subject_of(duty: Duty, record: records.Record) -> str | None:
    """The one commit's subject where the history is squashed, and always for a feature: the
    pull request's title."""
    landing = record.landing
    pull = landing.pull if landing else None
    history = merge_look.branch_of(duty.here).history
    squash = history == "squash" or parts.named(duty.state, record.task.slug)
    return pull.title if squash and pull else None


def ran(duty: Duty, slug: str, asked: merge_asked.Asked, key: Key) -> None:
    """The merge, and its end as the board and the server's log say it."""
    duty.kept.said[slug] = f"Lem merges {slug}; the page shows the result when it ends."
    try:
        outcome = merge.run(
            duty.checkout,
            slug,
            asked,
            before_call=partial(merge_count.at_call, duty, slug),
        )
    except (errors.Refusal, errors.Fault) as error:
        duty.kept.ended(key, clock.now(), ran=False)
        duty.kept.said[slug] = merge_said.refused(duty.state, slug, error)
        duty.say(f"the server's merge of {slug} did not go: {error}")
        return
    duty.kept.ended(key, duty.now, ran=True)
    line = merge_said.completed(slug, outcome)
    duty.kept.said[slug] = line
    duty.say(line)
