"""The marks of a task that its card and its header share (`board_pages.card_chips` on `main`):
a session it lacks or that stopped, red checks, a review that left a must-fix before
any proposal, and green or not green."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs.parts import Chip
from lem.board.views import rounds

if TYPE_CHECKING:
    from lem.model.owner.looks import Row
    from lem.records.landing.checks import Outcome
    from lem.records.landing.record import Landing
    from lem.records.record import Record

# What green means, in the words of the first line of a green pull request.
GREEN = (
    "The checks passed with the bar where it was, the review left no must-fix, no "
    "criterion changed, and no decision past the personas was taken without an answer"
)
ALERT = "triangle-exclamation"
BAD = "bad"
# A session the task lacks, or that stopped, as its chip says it, and the chip's hover.
SESSIONS = MappingProxyType(
    {
        "deaf": (
            "session does not answer",
            "A wake-up has waited in the task’s session for 10 minutes or more",
        ),
        "stopped": (
            "session stopped",
            "The task’s session stopped: “Open a session” on its page starts a fresh one",
        ),
        "gone": (
            "no session",
            "No agent runs the task now: “Open a session” on its page starts a fresh one",
        ),
    }
)


def session(rows: tuple[Row, ...]) -> Chip | None:
    """A session the task lacks or that stopped, as its row in Waits for you says."""
    need = need_of(rows)
    if need is None:
        return None
    label, title = SESSIONS[need]
    return Chip(label=label, icon=ALERT, look=BAD, title=title)


def need_of(rows: tuple[Row, ...]) -> str | None:
    """What the task lacks of its session: `stopped`, `deaf`, `gone`, or None."""
    for row in rows:
        if row.kind == "stopped":
            return "stopped"
        if row.kind == "session":
            return "deaf" if row.deaf else "gone"
    return None


def checks(record: Record) -> Chip | None:
    """Red checks: how many of the last run's commands did not pass."""
    checked = record.landing.checked if record.landing else None
    outcomes = checked.outcomes if checked else ()
    bad = [one for one in outcomes if not one.passed]
    if not bad:
        return None
    title = "\n".join(command_line(one) for one in outcomes)
    label = f"checks red: {len(bad)} of {len(outcomes)}"
    return Chip(label=label, icon=ALERT, look=BAD, title=title)


def command_line(outcome: Outcome) -> str:
    """`green  make test  212 passed`, or `exit 1  ...`."""
    word = "green" if outcome.passed else f"exit {outcome.exit}"
    last = outcome.last or ""
    return f"{word}  {outcome.command}  {last}"


def review(record: Record) -> Chip | None:
    """A review that left a must-fix, while no proposal is on record."""
    landing = record.landing
    if landing is None or not landing.reviews or landing.proposed is not None:
        return None
    newest = landing.reviews[-1]
    must = rounds.counts(newest)[0]
    if not must:
        return None
    title = "\n".join(rounds.line(one) for one in landing.reviews)
    return Chip(label=f"{must} must-fix", icon="eye", look=BAD, title=title)


def verdict(record: Record) -> Chip | None:
    """Green or not green, with what green means or the reasons."""
    landing: Landing | None = record.landing
    proposed = landing.proposed if landing else None
    if proposed is None:
        return None
    if proposed.green:
        return Chip(label="green", icon="check", look="ok", title=GREEN)
    title = "\n".join(proposed.reasons)
    return Chip(label="not green", icon=ALERT, look="you", title=title)
