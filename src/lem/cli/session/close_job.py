"""`lem session close-job`: close the session of a scheduled job.

    lem session close-job [--session ID]

It closes the caller's session, or the one named, once the owner has left it, when a scheduled
job started its agent (`app/sessions/closing_job.py`).
"""

import time

import click
import msgspec

from lem.app.sessions import closing_job, here
from lem.cli import place

# seconds between two looks, unless the call says
EVERY = 5.0


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session close-job`."""

    session: str | None = None
    every: float = EVERY


def run(call: Call) -> closing_job.JobClosed:
    """Close the job's session once the owner has left it."""
    bound = here.bound(place.folder())
    return closing_job.close_job(bound, call.session, call.every, time.sleep)


COMMAND = click.Command(
    "close-job",
    params=[
        click.Option(["--session"], help="the job's session (default: the caller's)"),
        click.Option(
            ["--every"],
            type=click.FLOAT,
            default=EVERY,
            hidden=True,
            help="seconds between two looks",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Close the session of a scheduled job.",
)
