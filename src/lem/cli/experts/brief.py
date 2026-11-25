"""`lem experts brief`: the experts' brief of one question in words.

    lem experts brief --question Q [--context C] [--option O]... [--file F]... [--seat S]...

A stub until the step `addons-outside` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem experts brief`."""

    question: str
    context: str = ""
    options: tuple[str, ...] = ()
    files: tuple[str, ...] = ()
    seats: tuple[str, ...] = ()


def run(call: Call) -> None:
    """Refuse until the step `addons-outside` builds `lem experts brief`."""
    raise not_built("experts brief", "addons-outside")


COMMAND = click.Command(
    "brief",
    params=[
        click.Option(
            ["--question"],
            required=True,
            help="a question in words, which has a folder of its own",
        ),
        click.Option(
            ["--context"], default="", help="what is being decided, and why it came up"
        ),
        click.Option(
            ["--option", "options"],
            multiple=True,
            help="an option, word for word, once for each",
        ),
        click.Option(
            ["--file", "files"],
            multiple=True,
            help="a file that matters, once for each",
        ),
        click.Option(
            ["--seat", "seats"],
            multiple=True,
            help="an expert, once for each, in the place of seats.experts",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The experts' brief of one question in words.",
)
