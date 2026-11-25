"""Where the owner answers a row of what waits for him (`board_model.wait_say` on `main`, its
`where`): a session the task lacks or one that stopped, a card, a merge review, a refused or
conflicting merge; every other row is answered where the task says (`answer`).

Waits for you, the sidebar's hover, a task's header and its large card say the same words.
"""

import re
from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.app.sessions.guard_rule import ANSWER_SECONDS, QUIET_SECONDS
from lem.board.views import merge_state, words
from lem.board.views.panel.answer import answer as answer_of
from lem.records.landing.merge import MergeIntent

if TYPE_CHECKING:
    from lem.board.views.world import Seen
    from lem.model.owner.looks import Row
    from lem.records.landing.merge import Refused
    from lem.records.record import Record

QUIET = QUIET_SECONDS // 60
ANSWERED = ANSWER_SECONDS // 60
OPEN = "Open a session here or on the task’s header:"
# Where he answers a session the task lacks, by the task's status.
LACKS = MappingProxyType(
    {
        "dropped": (
            f"{OPEN} it gives a ticket what it is still owed, then removes the "
            "worktree; the branch keeps its commits."
        ),
        "landed": (
            f"{OPEN} it removes the worktree, and the branch when it holds nothing "
            "that was not merged, and updates the ticket."
        ),
    }
)
FRESH = f"{OPEN} a fresh agent reads the task’s state and goes on from there."
DEAF = (
    "A wake-up has waited in the task’s session for 10 minutes or more. "
    "Look at the session: its agent may wait for an answer, or run a long turn."
)
CARD = (
    "on the card, here or in the task’s session at the Mac. "
    "The board takes an answer with a note, never a conversation: "
    "a question back goes to the session at the Mac."
)
VERDICT = re.compile(r"^\s*Verdict:\s*(call|merge)\.\s*", re.IGNORECASE)
CONFLICT = (
    "Nothing to do now: the board’s server wakes the task’s session, which "
    "brings it onto the base, and then it waits for you again."
)


def where(seen: Seen, row: Row) -> str:
    """Where the owner answers `row` of the task of `seen`."""
    task = seen.record.task
    if row.kind in {"session", "stopped"}:
        return lacking(task.status, row)
    if row.kind == "card":
        return CARD
    if row.kind == "review":
        return f"The merge review is the first card of the task’s Overview. {why(row)}"
    if row.kind == "merge":
        return merge(seen.record, row)
    return answer_of(task, row.after)


def lacking(status: str, row: Row) -> str:
    """Where he answers a session the task lacks, or one the guard stopped."""
    if row.kind == "stopped":
        return stopped(row)
    return DEAF if row.deaf else LACKS.get(status, FRESH)


def stopped(row: Row) -> str:
    """Where he answers a session the guard stopped: a fresh one, opened here."""
    if row.unread:
        return (
            "Lem cannot read whether the task’s session works. It sent the session "
            f"the status message after {QUIET} minutes with no event of the task, and "
            f"saw no event of the task in the {ANSWERED} minutes after it. Lem opens no "
            f"second session by itself: {OPEN.lower()} and a fresh agent reads the "
            "task’s state and goes on from there. The old pane stays open in agterm."
        )
    if row.restarted:
        said = (
            f"The task’s session showed no sign of work for {QUIET} minutes, nor in "
            f"the {ANSWERED} minutes after Lem asked it for its status, and neither did "
            "the fresh session that took its place."
        )
    else:
        said = (
            f"The task’s session showed no sign of work in the {ANSWERED} minutes "
            "after Lem asked it for its status, and Lem opened no fresh session by "
            "itself, since the task already stopped once after its last work."
        )
    return (
        f"{said} {OPEN} a fresh agent reads the task’s state and goes on from there, "
        "and the old pane stays open in agterm."
    )


def why(row: Row) -> str:
    """The merge agent's one sentence of why it calls the owner, without the verdict the row
    says already (`board_model.review_why` on `main`)."""
    said = VERDICT.sub("", row.why or "").strip()
    said = words.capital(said or "the merge agent calls you")
    return said if said.endswith((".", "!", "?")) else f"{said}."


def merge(record: Record, row: Row) -> str:
    """Where he answers a merge: a refusal of the proposed tip, a conflict, or his merge."""
    pending = recovery(record)
    if pending is not None:
        return pending
    landing = record.landing
    proposed = landing.proposed if landing else None
    refused = landing.refused if landing else None
    if refused is not None and proposed is not None and refused.tip == proposed.tip:
        return refusal(refused)
    if row.conflict:
        return CONFLICT
    return answer_of(record.task)


def recovery(record: Record) -> str | None:
    """The owner's GitHub check while a merge call has no reply on record."""
    landing = record.landing
    if landing is None or not isinstance(merge_state.current(record), MergeIntent):
        return None
    pull = landing.pull
    named = f"[pull request #{pull.number}]({pull.url})" if pull else "the pull request"
    return (
        f"Check {named} on GitHub. The merge call has no reply on record. "
        "If the pull request is still open, tell the task’s session what GitHub shows."
    )


def refusal(refused: Refused) -> str:
    """Where he answers a merge Lem or GitHub refused: what it said, and what comes next."""
    line = refused.line or "nothing"
    if refused.source == "lem":
        return (
            f"Lem said: {line}. The board’s server woke the task’s session: it runs "
            "the steps the line names, or waits for you."
        )
    return (
        f"GitHub said: {line}. Act on GitHub, or ask the task’s session for a change."
    )
