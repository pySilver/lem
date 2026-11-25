"""The owner's approval of a merge, carried out after the page's answer: `lem land merge SLUG
--by owner --tip TIP` through the board, in a thread of its own, so that the page does not wait
for the base branch and the forge (`serve.merge_in_thread` on `main`).

The merge is the landing's (`app/landing/merge.py`), under the task's step lock and the
workspace's merge lock, so two merges of one repository take turns. His approval is his own word
for the tip he saw (`via` `board`): refused because the base moved, it stands, and the board's
server carries it out after passing checks on the rebased task. It stands
through a new landing after a conflict too, while the reasons he saw are the same
(`model/landing/merge_standing.py`). The note says what came of the act when the step ends.
"""

from typing import TYPE_CHECKING

from lem.app.landing import merge
from lem.board.acts import merge_duty, merge_status
from lem.board.acts.asked import line_of
from lem.board.acts.notes import NOTES, State
from lem.kernel.errors import Fault, Refusal
from lem.model.landing.merge_asked import Asked as Merging
from lem.settings.load import settings_of
from lem.store import tasks

if TYPE_CHECKING:
    from lem.board.acts.asked import Asked
    from lem.board.acts.notes import Merging as Key
    from lem.records.record import Record

type Said = tuple[State, str]

REFUSED: State = "refused"
# The hex digits of a commit in a line for the owner.
SHORT = 12

UNKNOWN = (
    "The merge ended with no word of what came of it: read the pull request on GitHub."
)


def what_of(record: Record) -> str:
    """The pull request by its number, or the task's branch."""
    pull = record.landing.pull if record.landing else None
    if pull is not None:
        return f"pull request #{pull.number}"
    branch = record.task.branch or record.task.slug
    return f"the branch {branch}"


def stands(record: Record) -> str:
    """The line of his approval that stands for the proposed tip."""
    found = merge_status.standing(record)
    tip = found.tip[:SHORT] if found else "the proposed tip"
    return (
        f"Your approval of {what_of(record)} at {tip} stands: the base moved after the "
        "checks ran. Lem checks the rebased task before it merges. If the checks fail, "
        "the task leaves the merge line. A builder repairs it. Your approval "
        "can carry to a new landing while the reasons you read are the same."
    )


def outcome(record: Record, base: str) -> Said:
    """What came of the merge, from the record after it."""
    landing = record.landing
    what = what_of(record)
    if landing is not None and landing.merged is not None:
        return "done", (
            f"Merged: {what} is on {base}. Within a minute the board’s server wakes the "
            "task’s session, or opens one, which removes its worktree, and its branch "
            "when it holds nothing that was not merged."
        )
    if landing is not None and landing.accepted is not None:
        queued = landing.accepted.queued
        return "done", f"GitHub took the merge of {what} and holds it: {queued}."
    return REFUSED, UNKNOWN


def asked_for(asked: Asked) -> Merging:
    """The merge as the landing takes it: the owner's, through the board, for the tip he saw,
    with the pull request's title as the one commit's subject of a squash."""
    record = tasks.read(asked.state, asked.slug)
    branch = settings_of(asked.checkout).settings.branch
    pull = record.landing.pull if record.landing else None
    subject = pull.title if pull is not None and branch.history == "squash" else None
    return Merging(by="owner", via="board", tip=asked.given.tip, subject=subject)


def said_of(asked: Asked) -> Said:
    """Run the merge, and say what came of it; a refusal that kept his approval says it
    stands."""
    base = settings_of(asked.checkout).settings.branch.base or "the base branch"
    try:
        merge.run(
            asked.checkout,
            asked.slug,
            asked_for(asked),
            before_call=merge_duty.counter(asked),
        )
    except Refusal as refusal:
        record = tasks.read(asked.state, asked.slug)
        if refusal.code == "intent":
            return "uncertain", line_of(refusal)
        if merge_status.standing(record) is not None:
            return "stands", stands(record)
        return REFUSED, line_of(refusal)
    return outcome(tasks.read(asked.state, asked.slug), base)


def merged(asked: Asked, token: str, key: Key) -> None:
    """The merge in its thread: the note of `token` says what came of it, and the task's
    merge is no longer running."""
    said: Said = (REFUSED, UNKNOWN)
    try:
        said = said_of(asked)
    except Fault as fault:
        pending = merge_status.uncertain(tasks.read(asked.state, asked.slug))
        if pending is None:
            said = (REFUSED, f"The merge failed: {fault}.")
        else:
            said = ("uncertain", pending)
    finally:
        NOTES.change(token, *said)
        NOTES.ended(key)
