"""The task command that sets a red-base hold."""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.tasks import red_base
from lem.cli import place

if TYPE_CHECKING:
    from lem.records.task import Task


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task red-base`."""

    slug: str
    after: str


def run(call: Call) -> Task:
    """Set the task's hold."""
    return red_base.run(place.folder(), call.slug, call.after)


COMMAND = click.Command(
    "red-base",
    params=[
        click.Argument(["slug"]),
        click.Option(["--after"], required=True, help="the task that repairs the base"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Hold the landing for the red-base repair named by --after.",
)
