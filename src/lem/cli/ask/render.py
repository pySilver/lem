"""`lem ask render`: render a spec into an HTML file, attachments kept.

    lem ask render SPEC --out FILE

A stub until the step `ask` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem ask render`."""

    spec: str
    out: str


def run(call: Call) -> None:
    """Refuse until the step `ask` builds `lem ask render`."""
    raise not_built("ask render", "ask")


COMMAND = click.Command(
    "render",
    params=[
        click.Argument(["spec"]),
        click.Option(["--out", "-o"], required=True, help="the HTML file to write"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Render a spec into an HTML file, attachments kept.",
)
