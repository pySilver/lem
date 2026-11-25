"""`lem proposals add`: add a run's proposals to the record of its day.

    lem proposals add --kind night|retro [--date DAY] --file FILE

The run is a JSON object, `{"read": WHAT IT READ, "proposals": [{"area", "move", "body",
"source", "where"}, ...]}`, from the file or from standard input; its proposals get the numbers
after those of the day's record (`addons/proposals/adding.py`).
"""

import datetime as dt
from typing import Literal

import click
import msgspec

from lem.addons.proposals import adding, given
from lem.cli import place
from lem.cli.words import choice
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.store import places

type Kind = Literal["night", "retro"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem proposals add`."""

    kind: Kind
    date: str | None = None
    path: str


RUN = '{"read": WHAT THE RUN READ, "proposals": [{"area", "move", "body", "source", "where"}]}'


def run(call: Call) -> adding.Added:
    """Add the run to the record of its day."""
    now = clock.now()
    day = day_of(call.date, now)
    state = places.state_of(places.workspace(place.folder()).checkout)
    told = given.read_given(call.path, given.RunGiven, RUN)
    return adding.added(state, call.kind, day, told, now)


def day_of(said: str | None, now: dt.datetime) -> dt.date:
    """The run's day: `--date`, else today in UTC; refused for a text that is no day."""
    if said is None:
        return now.date()
    try:
        return dt.date.fromisoformat(said)
    except ValueError:
        raise Refusal(
            "date", f"--date is the run's day, YYYY-MM-DD, not {said!r}", "give a day"
        ) from None


COMMAND = click.Command(
    "add",
    params=[
        click.Option(
            ["--kind"],
            required=True,
            type=choice(Kind),
            help="the run: the night or the retro",
        ),
        click.Option(["--date"], help="the run's day (default: today, in UTC)"),
        click.Option(
            ["--file", "path"], required=True, help="the run as JSON, or - for stdin"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Add a run's proposals to the record of its day.",
)
