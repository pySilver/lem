"""Why a request is careful, and whether its plan called for a plan talk
(`main:land.careful`, `settings_edit`, `local_settings_edit`, `talk_due`).

The shape's topics, the plan's own call and the newest review's call are judgments against the
project's topics; an edit of Lem's own settings, or a commit of one machine's, is the one rule
matched here by itself: the file says for every later task what is careful, what the checks
run, who merges and where a task lands (audit A1 and N5 of 2026-11-17 on `main`).
"""

import tomllib
from typing import TYPE_CHECKING

from lem.model.landing.green_words import reason
from lem.model.landing.review import newest
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.propose_facts import Facts, Settings
    from lem.records.record import Record

type Tables = dict[str, object]

TEAM = ".lem/settings.toml"
LOCAL = ".lem/settings.local.toml"
GUARDS = (
    "Lem's own settings, which say for every later task what is careful, what the checks "
    "run, who merges and where a task lands"
)


def tables(text: str | None) -> Tables:
    """The tables of a settings file's text; none for a file that is not there."""
    return tomllib.loads(text) if text else {}


def edited(before: Tables, after: Tables) -> list[str]:
    """The names of the tables whose values differ between two forms of a file."""
    names = sorted({*before, *after})
    return [name for name in names if before.get(name) != after.get(name)]


def team_edit(settings: Settings) -> str:
    """Why an edit of the team's settings file is careful: the tables whose values change,
    or that only its text does, or that it is gone or no longer TOML."""
    if settings.after is None:
        return f"the change removes {TEAM}, {GUARDS}"
    try:
        names = edited(tables(settings.before), tables(settings.after))
    except tomllib.TOMLDecodeError:
        return (
            f"the change leaves {TEAM} in a form that does not read as TOML, so what "
            "it says is careful cannot be told"
        )
    listed = " and ".join(f"[{name}]" for name in names)
    what = f"the text of {TEAM}, and no value in it"
    if names:
        what = f"{listed} of {TEAM}"
    return f"the change edits {what}, {GUARDS}"


def local_edit(settings: Settings) -> str:
    """Why a commit of one machine's own settings is careful."""
    was, now = settings.local
    how = "changes"
    if now and not was:
        how = "adds"
    elif was and not now:
        how = "removes"
    return (
        f"the change {how} {LOCAL}, one machine's own settings, which git does not "
        "track: tracked, that machine's seats, naps and days the state keeps become "
        "every machine's"
    )


def edits(facts: Facts) -> tuple[str, ...]:
    """The reasons of the change's edits of Lem's own settings."""
    team = (team_edit(facts.settings),) if TEAM in facts.changed else ()
    local = (local_edit(facts.settings),) if LOCAL in facts.changed else ()
    return team + local


def why(record: Record, facts: Facts) -> tuple[str, ...]:
    """Each reason the request is careful; none when it is not: the shape's topics, the
    plan's call, an edit of Lem's settings, and the newest review's call."""
    task = record.task
    topics = task.shape.careful if task.shape else ()
    plan = ("the plan says so",) if task.plan and task.plan.careful else ()
    return topics + plan + edits(facts) + review_call(record)


def review_call(record: Record) -> tuple[str, ...]:
    """The newest answered review's careful call, with its reason, when it said yes."""
    last = newest(record.landing or Landing())
    if last is None or not last.careful:
        return ()
    said = reason(last.careful_why or "no reason given")
    return (f"the review says so: {said}",)
