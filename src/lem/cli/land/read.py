"""`lem land read`: the review's read: what is due, or its record.

    lem land read SLUG [--record FILE]

A stub until the step `land-review` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land read`."""

    slug: str
    record: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `land-review` builds `lem land read`."""
    raise not_built("land read", "land-review")


COMMAND = click.Command(
    "read",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--record"], help="a JSON file that says what the review was and found"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The review's read: what is due, or its record.",
)
