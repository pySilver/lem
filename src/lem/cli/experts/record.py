"""`lem experts record`: record one expert's answer.

lem experts record --folder DIR --expert NAME [--seat S]...
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.addons.experts import record
from lem.cli.place import folder

if TYPE_CHECKING:
    from lem.addons.experts.records import Summary


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem experts record`."""

    folder: str
    expert: str
    seats: tuple[str, ...] = ()


def run(call: Call) -> Summary:
    """Run the experts command in the active checkout."""
    return record.record(folder(), call.folder, call.expert)


COMMAND = click.Command(
    "record",
    params=[
        click.Option(
            ["--folder"],
            required=True,
            help="the folder of the question, as brief printed it",
        ),
        click.Option(["--expert"], required=True, help="the expert that answered"),
        click.Option(
            ["--seat", "seats"],
            multiple=True,
            help="an expert, once for each, in the place of seats.experts",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Record one expert's answer.",
)
