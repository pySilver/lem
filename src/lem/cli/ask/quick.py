"""`lem ask q`: one question to the owner, with its options, in one line.

    lem ask q PROMPT [OPTIONS]... [--multi] [--context TEXT] [--title TITLE] ...

A stub until the step `ask` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.ask.shown import Shown, options
from lem.cli.stub import not_built


class Call(Shown, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem ask q`."""

    prompt: str
    options: tuple[str, ...] = ()
    multi: bool = False
    context: str | None = None
    title: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `ask` builds `lem ask q`."""
    raise not_built("ask q", "ask")


COMMAND = click.Command(
    "q",
    params=[
        click.Argument(["prompt"]),
        click.Argument(["options"], nargs=-1),
        *options(),
        click.Option(
            ["--multi"], is_flag=True, help="the owner may pick more than one"
        ),
        click.Option(["--context"], help="what the question is about, above it"),
        click.Option(["--title"], help="the page's title"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Ask one question with its options, given on the command line.",
)
