"""`lem ask ask`: one question to the owner as a page in agterm, from a spec.

    lem ask [ask] [SPEC] [--follow] [--size N] [--style S] [--timeout SECONDS] ...

`lem ask SPEC` is this verb: a first word that is no verb of `lem ask` is its spec. Every
outcome is exit 0, in `result.outcome`. A stub until the step `ask` builds it: it refuses
`not-built`.
"""

import click
import msgspec

from lem.cli.ask.shown import Shown, options
from lem.cli.stub import not_built


class Call(Shown, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem ask ask`."""

    spec: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `ask` builds `lem ask ask`."""
    raise not_built("ask ask", "ask")


COMMAND = click.Command(
    "ask",
    params=[
        click.Argument(["spec"], required=False),
        *options(),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Show the question of a spec (a file, or - for stdin) and wait for the answer.",
)
