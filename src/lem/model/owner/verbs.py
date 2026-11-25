"""What a row of what waits says the owner does, in the board's words (`board_model.wait_say` on
`main`, its `verb`): the terminal and the phone say the same.

The rest of the board's words for a row (where he acts, its icon, how its time reads) are the
board's views'.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.model.owner import merging
from lem.records.holds import OwnerHold
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.owner.looks import Row
    from lem.records.task import Task

OLDER_RELEASE = "It began on an older release of Lem"
# The verbs that follow from the kind alone.
PLAIN = MappingProxyType(
    {
        "criteria": "Approve the criteria",
        "plan": "Read the plan",
        "review": "Read the merge review",
        "blocked": "Its session stopped: tell it what to do",
    }
)
# The verb of an ended task whose cleanup lacks its session.
CLEANS = MappingProxyType(
    {
        "dropped": "No session cleans the dropped task",
        "landed": "No session cleans the merged task",
    }
)


def verb(row: Row, task: Task, landing: Landing | None) -> str:
    """The row's verb."""
    plain = PLAIN.get(row.kind)
    if row.say is not None:
        return OLDER_RELEASE
    if plain is not None:
        return plain
    if row.kind in {"session", "stopped"}:
        return session_verb(row, task)
    if row.kind == "merge":
        return merge_verb(row, landing or Landing())
    return asked_verb(row, task)


def asked_verb(row: Row, task: Task) -> str:
    """The verb of a breaker, a task queued after a dropped one, a card, or his wait."""
    if row.kind == "breaker":
        return f"Read the breaker of {task.slug}"
    if row.kind == "after_dropped":
        return f"{row.after} was dropped: your word starts or ends this task"
    if row.kind == "card":
        return capital(row.prompt or "the task's session asks you")
    return capital(held_line(task))


def session_verb(row: Row, task: Task) -> str:
    """The verb of a task that lacks its session or whose session stopped."""
    if row.kind == "stopped" and row.unread:
        return "Its session stopped, and Lem cannot read it: open a fresh one"
    if row.kind == "stopped":
        return "Its session stopped: open a fresh one"
    if row.deaf:
        return "Its session does not answer"
    return CLEANS.get(task.status, "No session runs this task")


def merge_verb(row: Row, landing: Landing) -> str:
    """The verb of a merge that waits for the owner: a refusal, a conflict, or his merge."""
    if landing.intent is not None:
        return "Check the pull request on GitHub"
    refused = refused_verb(row, landing)
    if refused is not None:
        return refused
    if row.conflict:
        return "It conflicts with the base"
    pull = landing.pull
    if pull is None:
        return "Merge the pull request"
    return f"Merge the pull request #{pull.number}"


def refused_verb(row: Row, landing: Landing) -> str | None:
    """The verb of a refused merge of the proposed tip, by Lem or by GitHub, or None."""
    proposed, refused = landing.proposed, landing.refused
    if refused is None or proposed is None or refused.tip != proposed.tip:
        return None
    if merging.calls_after_base_refusal(
        landing,
        refused,
        base_tree=row.base_tree,
        read_after_refusal=row.read_after_refusal,
    ):
        return None
    if refused.source == "lem":
        return "The merge did not go through"
    return "GitHub refused the merge"


def held_line(task: Task) -> str:
    """The line of the owner's wait, as the stage wrote it."""
    hold = task.hold
    if isinstance(hold, OwnerHold) and hold.line:
        return hold.line
    return "the task waits for you"


def capital(text: str) -> str:
    """The text with its first letter in capitals."""
    return text[:1].upper() + text[1:]
