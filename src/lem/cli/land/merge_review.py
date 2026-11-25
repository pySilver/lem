"""`lem land merge-review`: the merge agent's brief, or its reply written down.

    lem land merge-review SLUG [--file FILE|--no-answer] [--tip TIP] [--base BASE]

The plain path, as the step `slice-land` built it; the step `land-merge` owns it.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.landing import mergeread
from lem.cli import place
from lem.cli.stub import not_built

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land merge-review`."""

    slug: str
    reply: str | None = None
    no_answer: bool = False
    tip: str | None = None
    base: str | None = None


def run(call: Call) -> Envelope:
    """Write the merge agent's brief, or its reply; `--no-answer` is the step
    `land-merge`'s."""
    if call.no_answer:
        raise not_built("land merge-review --no-answer", "land-merge")
    brief = (call.tip, call.base) if call.tip and call.base else None
    return mergeread.run(place.folder(), call.slug, call.reply, brief)


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
