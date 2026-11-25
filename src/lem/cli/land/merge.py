"""`lem land merge`: merge the pull request, on the owner's word or the merger's.

    lem land merge SLUG --by owner|merger [--message M] [--via V] [--standing] [--tip TIP]

A stub until the step `land-merge` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type By = Literal["owner", "merger"]
type Via = Literal["session", "server"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land merge`."""

    slug: str
    by: By
    message: str | None = None
    via: Via = "session"
    standing: bool = False
    tip: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `land-merge` builds `lem land merge`."""
    raise not_built("land merge", "land-merge")


COMMAND = click.Command(
    "merge",
    params=[
        click.Argument(["slug"]),
        click.Option(["--by"], required=True, type=choice(By), help="who merges"),
        click.Option(
            ["--message"],
            help="the subject of the one commit, when branch.history is squash",
        ),
        click.Option(
            ["--via"], type=choice(Via), default="session", help="who runs this call"
        ),
        click.Option(
            ["--standing"],
            is_flag=True,
            help="with --by owner: his merge that a moved base refused, still standing",
        ),
        click.Option(["--tip"], help="the whole commit the caller saw"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Merge the pull request, on the owner's word or the merger's.",
)
