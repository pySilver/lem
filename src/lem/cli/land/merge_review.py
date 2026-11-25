"""`lem land merge-review`: the merge agent's brief, or its reply written down.

    lem land merge-review SLUG [--file FILE|--no-answer] [--tip TIP] [--base BASE]

A stub until the step `land-merge` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land merge-review`."""

    slug: str
    reply: str | None = None
    no_answer: bool = False
    tip: str | None = None
    base: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `land-merge` builds `lem land merge-review`."""
    raise not_built("land merge-review", "land-merge")


COMMAND = click.Command(
    "merge-review",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--file", "reply"],
            help="the merge agent's reply, its verdict on its first line",
        ),
        click.Option(
            ["--no-answer"],
            is_flag=True,
            help="the merge agent of the brief ended with no answer",
        ),
        click.Option(
            ["--tip"], help="the tip the step printed with the brief the agent read"
        ),
        click.Option(
            ["--base"], help="the base the step printed with the brief the agent read"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The merge agent's brief, or its reply written down.",
)
