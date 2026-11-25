"""List the specs Lem ships as question templates."""

import click
import msgspec

from lem.cli.ask import catalog


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem ask templates`."""


def run(call: Call) -> dict[str, object]:
    """Give the names and descriptions of the templates."""
    group = "templates"
    return {
        "outcome": "listed",
        group: catalog.listing(group),
        "directory": str(catalog.folder(group)),
    }


COMMAND = click.Command(
    "templates",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The question page's templates.",
)
