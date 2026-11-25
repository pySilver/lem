"""Each reason a request is careful (`land.careful` on `main`): its shape's topics, the plan's
own call, an edit of Lem's own settings or of one machine's, and the newest review's call.

The shape, the plan and the review judge the change against the project's topics. An edit of
`.lem/settings.toml` is the one rule matched by this code, not by a judgment: the file says for
every later task what is careful, what the checks run, who merges and where a task lands (audit
A1, 2026-11-17: a branch that set `branch.land` to "agent" got one read and a green request). A
commit of `.lem/settings.local.toml`, one machine's own and untracked by design, is careful too
(audit N5, 2026-11-17).
"""

import tomllib
from typing import TYPE_CHECKING

from lem.records.base import Frozen
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.record import Record

SETTINGS_FILE = ".lem/settings.toml"
LOCAL_SETTINGS_FILE = ".lem/settings.local.toml"
GUARDS = (
    "Lem's own settings, which say for every later task what is careful, what the checks "
    "run, who merges and where a task lands"
)


class Seen(Frozen, frozen=True, kw_only=True):
    """One settings file as the change has it: whether the change touches it, and its text
    at the base and at the tip (None where the commit has no such file)."""

    touched: bool = False
    base: str | None = None
    tip: str | None = None


class Edits(Frozen, frozen=True, kw_only=True):
    """The change's edits of the team's settings file and of one machine's."""

    settings: Seen = Seen()
    local: Seen = Seen()


def tables_edited(base: str, tip: str) -> list[str] | None:
    """The tables whose values differ between two texts of the settings file, or None when
    one does not read as TOML."""
    try:
        both = (tomllib.loads(base), tomllib.loads(tip))
    except tomllib.TOMLDecodeError:
        return None
    before, after = both
    names = sorted(before.keys() | after.keys())
    return [name for name in names if before.get(name) != after.get(name)]


def settings_reason(seen: Seen) -> str | None:
    """Why the change is careful by its edit of `.lem/settings.toml`, naming each table
    whose values change; None when it leaves the file alone."""
    if not seen.touched:
        return None
    if seen.tip is None:
        return f"the change removes {SETTINGS_FILE}, {GUARDS}"
    edited = tables_edited(seen.base or "", seen.tip)
    if edited is None:
        return (
            f"the change leaves {SETTINGS_FILE} in a form that does not read as TOML, so "
            "what it says is careful cannot be told"
        )
    listed = " and ".join(f"[{name}]" for name in edited)
    what = f"{listed} of {SETTINGS_FILE}"
    if not edited:
        what = f"the text of {SETTINGS_FILE}, and no value in it"
    return f"the change edits {what}, {GUARDS}"


def local_reason(seen: Seen) -> str | None:
    """Why the change is careful by a commit of one machine's own settings; None when it
    leaves the file alone."""
    if not seen.touched:
        return None
    how = "changes"
    if seen.base is None:
        how = "adds"
    elif seen.tip is None:
        how = "removes"
    return (
        f"the change {how} {LOCAL_SETTINGS_FILE}, one machine's own settings, which git "
        "does not track: tracked, that machine's seats, naps and days the state keeps "
        "become every machine's"
    )


def review_reason(landing: Landing) -> tuple[str, ...]:
    """The careful call of the newest review that answered, when it says careful."""
    answered = [review for review in landing.reviews if review.answered]
    call = answered[-1] if answered else None
    if call is None or not call.careful:
        return ()
    why = call.careful_why
    return (f"the review says so: {why}",)


def reasons(record: Record, edits: Edits) -> tuple[str, ...]:
    """Each reason the request is careful, in `main`'s order; none when it is not."""
    task = record.task
    topics = task.shape.careful if task.shape else ()
    plan = task.plan.careful if task.plan else None
    edited = (settings_reason(edits.settings), local_reason(edits.local))
    return (
        *(f"the request is careful: {topic}" for topic in topics),
        *((f"the plan says so: {plan}",) if plan else ()),
        *(reason for reason in edited if reason),
        *review_reason(record.landing or Landing()),
    )
