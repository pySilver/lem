"""`lem experts record`: record one expert's answer.

    lem experts record --folder DIR --expert NAME [--seat S]...

A stub until the step `addons-outside` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem experts record`."""

    folder: str
    expert: str
    seats: tuple[str, ...] = ()


def run(call: Call) -> None:
    """Refuse until the step `addons-outside` builds `lem experts record`."""
    raise not_built("experts record", "addons-outside")


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
