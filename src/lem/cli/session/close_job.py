"""`lem session close-job`: close the session of a scheduled job.

    lem session close-job [--session ID]

A stub until the step `sessions` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built

# seconds between two looks, unless the call says
EVERY = 5.0


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session close-job`."""

    session: str | None = None
    every: float = EVERY


def run(call: Call) -> None:
    """Refuse until the step `sessions` builds `lem session close-job`."""
    raise not_built("session close-job", "sessions")


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
