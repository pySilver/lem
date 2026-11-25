"""`lem jev ask`: ask the Jev model the questions of a spec, and print its answers.

    lem jev [ask] SPEC

`lem jev SPEC` is this verb; `lem jev check SPEC` reads the spec and asks nothing. A stub
until the step `addons-outside` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem jev ask`."""

    spec: str


def run(call: Call) -> None:
    """Refuse until the step `addons-outside` builds `lem jev ask`."""
    raise not_built("jev ask", "addons-outside")


COMMAND = click.Command(
    "ask",
    params=[
        click.Argument(["spec"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Ask the Jev model the questions of a spec, and print its answers.",
)
