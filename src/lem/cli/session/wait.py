"""`lem session wait`: wait for a state, an event or the task's first line.

    lem session wait SLUG (--until STATES|--event EVENT|--first-line) ...

It waits for one of the task's statuses, a new entry of a kind on its record, or its first line,
and ends too when its session or a companion is gone, or a quiet file stays quiet
(`app/sessions/waits.py`, `app/sessions/first_line.py`).
"""

import time
from typing import get_args

import click
import msgspec

from lem.app.sessions import first_line, here, waits
from lem.cli import place
from lem.cli.checks import exactly_one
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.records.task import Status

# seconds between two looks, unless the call says
EVERY = 10.0
# seconds the wait lasts at most, unless the call says
BOUND = 600.0


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session wait`."""

    slug: str
    until: str | None = None
    event: str | None = None
    first_line: bool = False
    companion: str | None = None
    quiet: str | None = None
    every: float = EVERY
    bound: float = BOUND


def run(call: Call) -> waits.waiting.Waited | first_line.FirstLine:
    """Wait for the state, the entry or the first line."""
    bound = here.bound(place.folder())
    if call.first_line:
        asked = (call.slug, call.every, call.bound)
        return first_line.first_line(bound, asked, clock.now, time.sleep)
    until = tuple(
        word.strip() for word in (call.until or "").split(",") if word.strip()
    )
    wanted = waits.Asked(
        slug=call.slug,
        until=until,
        event=call.event,
        companion=call.companion,
        quiet=call.quiet,
        every=call.every,
    )
    return waits.wait_for(bound, wanted, clock.now, time.sleep)


# The holds `--until` names beside the statuses, as `main`'s states named them.
HOLDS = ("held", "blocked", "parked", "release")


def statuses(words: str) -> tuple[str, ...]:
    """The statuses `--until` names; refused for a word that is no status."""
    stripped = map(str.strip, words.split(","))
    named = tuple(filter(None, stripped))
    known = (*get_args(Status.__value__), *HOLDS)
    unknown = " ".join(word for word in named if word not in known)
    if unknown:
        listed = " ".join(known)
        raise Refusal(
            "until",
            f"--until names {unknown}, which is no status or hold of a task",
            f"name statuses among {listed}, joined by commas",
        )
    return named


COMMAND = click.Command(
    "wait",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--until"], help="the states that end the wait, joined by commas"
        ),
        click.Option(["--event"], help="the event that ends the wait"),
        click.Option(
            ["--first-line"], is_flag=True, help="end with the task's first line"
        ),
        click.Option(
            ["--companion"], help="end too when this companion of the session is gone"
        ),
        click.Option(
            ["--quiet"], help="end too when FILE has not changed for 45 minutes"
        ),
        click.Option(
            ["--every"],
            type=click.FLOAT,
            default=EVERY,
            hidden=True,
            help="seconds between two looks",
        ),
        click.Option(
            ["--bound"],
            type=click.FLOAT,
            default=BOUND,
            hidden=True,
            help="seconds the wait lasts at most",
        ),
    ],
    callback=lambda **given: run(
        msgspec.convert(exactly_one(given, "until", "event", "first_line"), Call)
    ),
    help="Wait for a state, an event or the task's first line.",
)
