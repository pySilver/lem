"""The lines of the checks for the owner and the board: the end of a run, a run that goes on
too long, the end a session that did not start the run reads, and a run that waits (`land.
checks_say`, `overdue_say`, `resumed_line` and `wait_say` on `main`). None asks a question."""

from pathlib import Path
from types import MappingProxyType
from typing import Literal

from lem.kernel import clock
from lem.records.base import Frozen, Moment

type Ending = Literal["passed", "red", "refused", "stopped"]
type Behind = Literal["wanted", "longer", "first"]
# The checks are overdue when they run more than this many times as long as their last
# finished run: the owner's "three times longer than their last finished run" (criterion 5 of
# the plan 2026-11-19-landing-in-the-background).
OVERDUE_TIMES = 3
# And only after they ran for at least this many seconds: a last run of 0 or 1 second (a
# stand-in such as `true`, rounded under load) is no measure, and three times it passed while
# five Python steps started (the guards check under tests/all.sh, load-gate-default-forty,
# 2026-11-22). The minute is the criterion of the task overdue-race-after-one-second-run
# (2026-11-22), a guess that no real suite of the checks ends in under a minute, not a
# measurement.
OVERDUE_FLOOR = 60
# The words of a wait behind another run: the first in the line is one another task waits
# for and this run is not, its wait began earlier, or the two began at one moment.
BEHIND_WHY = MappingProxyType(
    {
        "wanted": "which another task waits for",
        "longer": "which waits longer",
        "first": "which is first in the line",
    }
)
NOTHING = "nothing for you"


class Wait(Frozen, frozen=True, kw_only=True):
    """Why a run waits at the load gate: the load and the start number, the run it waits a
    minute after, or the first in the line, its repository when not this one, and why it goes
    first; `unread` names each repository whose state did not read at this look."""

    load: float
    start: float
    after: str | None = None
    behind: str | None = None
    behind_repo: str | None = None
    why: Behind | None = None
    unread: tuple[str, ...] = ()


def ended(
    slug: str,
    outcome: Ending,
    failed: tuple[str, ...] = (),
    refused: str | None = None,
    *,
    review: bool = True,
) -> str:
    """The one line at the end of a run: the result and what comes next. `failed` names the red
    commands, `refused` what the checks refused, and `review` whether a review is due after a
    passed run."""
    if outcome == "passed" and not review:
        return (
            f"{slug}: the checks passed; no review is due, so it is proposed, {NOTHING}"
        )
    if outcome == "passed":
        return f"{slug}: the checks passed; the review runs, {NOTHING}"
    if outcome == "red":
        named = " and ".join(failed or ("a command",))
        return f"{slug}: the checks are red on {named}; a builder repairs it, {NOTHING}"
    if outcome == "refused":
        why = refused or "the step met an error"
        return f"{slug}: the checks refused the change: {why}; a builder repairs it, {NOTHING}"
    return f"{slug}: the checks were stopped; the landing waits for your word"


def duration(seconds: float) -> str:
    """Seconds in the words a person reads: `26 s`, `4 min 26 s`, `14 min`."""
    minutes, rest = divmod(int(seconds), 60)
    if not minutes:
        return f"{rest} s"
    if rest:
        return f"{minutes} min {rest} s"
    return f"{minutes} min"


def overdue(seconds: int | None, last: int | None) -> str | None:
    """The line of a run that has gone on for `seconds`, more than OVERDUE_TIMES as long as
    the last finished one and at least OVERDUE_FLOOR seconds; None while it is not overdue."""
    if seconds is None or last is None:
        return None
    if seconds < OVERDUE_FLOOR or seconds <= OVERDUE_TIMES * last:
        return None
    took, before = duration(seconds), duration(last)
    return (
        f"the checks run for {took}, more than three times their last run of {before}; "
        '"stop the checks" stops them'
    )


def resumed(slug: str, at: Moment, outcome: Ending) -> str:
    """The line for a session that did not start the run: its result, as past, and the next
    step as it is now. A stopped run waits for the owner's word; after any other, the landing
    goes on from its first step, as after a cut-off."""
    after = (
        "the landing waits for your word"
        if outcome == "stopped"
        else "the landing goes on from its first step, as after a cut-off"
    )
    when = clock.minute(at)
    return f"{slug}: its last run of the checks ended at {when}, {outcome}; {after}"


def waiting(slug: str, wait: Wait) -> str:
    """The one line of a run that waits, for the owner and the board."""
    start = f"{wait.start:g}"
    if wait.behind:
        other = wait.behind
        if wait.behind_repo:
            other = f"{wait.behind} of {Path(wait.behind_repo).name}"
        words = BEHIND_WHY[wait.why or "first"]
        said = (
            f"{slug}: the checks wait behind {other}, {words}; they start below {start}"
        )
    elif wait.after:
        said = (
            f"{slug}: the checks wait a minute after the checks of {wait.after} started, "
            f"so that the load shows them; then they start below {start}"
        )
    else:
        said = f"{slug}: the checks wait for the load: {wait.load:g}, they start below {start}"
    unread = (
        f"; the state of {Path(repo).name} does not read, so its landings count as wanted "
        "by no task"
        for repo in wait.unread
    )
    return said + "".join(unread)
