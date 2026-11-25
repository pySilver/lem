"""`lem land polish`: the polish pass, and its check when it is done.

    lem land polish SLUG [--done]

A stub until the step `land-checks` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land polish`."""

    slug: str
    done: bool = False


def run(call: Call) -> None:
    """Refuse until the step `land-checks` builds `lem land polish`."""
    raise not_built("land polish", "land-checks")


COMMAND = click.Command(
    "polish",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--done"],
            is_flag=True,
            help="after the polish builder: check what it committed",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The polish pass, and its check when it is done.",
)
