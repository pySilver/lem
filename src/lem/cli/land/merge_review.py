"""`lem land merge-review`: the merge agent's brief, or its reply written down.

    lem land merge-review SLUG [--file FILE|--no-answer] [--tip TIP] [--base BASE] [--dispatch N]

The step `land-merge` owns it.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.landing import mergeread
from lem.cli import checks, place

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land merge-review`."""

    slug: str
    reply: str | None = None
    no_answer: bool = False
    tip: str | None = None
    base: str | None = None
    dispatch: int | None = None


def run(call: Call) -> Envelope:
    """Write the merge agent's brief, or its reply (or that it gave none) to the brief of
    `--tip` and `--base` that dispatch `--dispatch` started."""
    tip, base = call.tip, call.base
    brief = (tip, base, call.dispatch) if tip and base else None
    return mergeread.run(
        place.folder(), call.slug, call.reply, brief, no_answer=call.no_answer
    )


def given(words: checks.Given) -> checks.Given:
    """Refuse a call with both an answer and none, or with a tip, base or dispatch and
    neither: they go with the answer whose brief they name."""
    checks.at_most_one(words, "reply", "no_answer")
    answer = checks.counted(words, ("reply", "no_answer"))
    if not answer and checks.counted(words, ("tip", "base", "dispatch")):
        why = (
            "--tip, --base and --dispatch go with --file or --no-answer: the brief's tip "
            "and base, and the dispatch that started its agent"
        )
        raise click.UsageError(why, click.get_current_context())
    return words


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
        click.Option(
            ["--dispatch"],
            type=click.IntRange(min=1),
            help="the dispatch the step printed with the brief the agent read",
        ),
    ],
    callback=lambda **words: run(msgspec.convert(given(words), Call)),
    help="The merge agent's brief, or its reply written down.",
)
