"""Show a question from a JSON spec."""

import click
import msgspec

from lem.cli.ask import asking
from lem.cli.ask import spec as specs
from lem.cli.ask.shown import Shown, options


class Call(Shown, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem ask ask`."""

    spec: str | None = None


def run(call: Call) -> asking.Words:
    """Read the spec and show it on the requested surface."""
    spec, base = specs.load(call.spec)
    return asking.ask(spec, base, call)


COMMAND = click.Command(
    "ask",
    params=[
        click.Argument(["spec"], required=False),
        *options(),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Show the question of a spec (a file, or - for stdin) and wait for the answer.",
)
