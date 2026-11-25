"""`lem land merge`: merge the pull request, on the owner's word or the merger's.

    lem land merge SLUG --by owner|merger [--message M] [--via V] [--standing] [--tip TIP]
        [--checked MOMENT]

The step `land-merge` owns it.
"""

from typing import TYPE_CHECKING, Literal

import click
import msgspec

from lem.app.landing import merge
from lem.cli import checks, place
from lem.cli.words import choice
from lem.model.landing.merge_asked import Asked

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope

type By = Literal["owner", "merger"]
type Via = Literal["session", "server"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land merge`."""

    slug: str
    by: By
    message: str | None = None
    via: Via = "session"
    standing: bool = False
    tip: str | None = None
    checked: str | None = None


def run(call: Call) -> Envelope:
    """Merge the pull request, as asked."""
    asked = Asked(
        by=call.by,
        via=call.via,
        tip=call.tip,
        standing=call.standing,
        subject=call.message,
        checked=call.checked,
    )
    return merge.run(place.folder(), call.slug, asked)


def given(words: checks.Given) -> checks.Given:
    """Refuse `--standing` with the merge agent: it is the owner's merge that stood."""
    if words.get("standing") and words.get("by") != "owner":
        why = "--standing is the owner's merge that stood through a moved base: --by owner"
        raise click.UsageError(why, click.get_current_context())
    return words


COMMAND = click.Command(
    "merge",
    params=[
        click.Argument(["slug"]),
        click.Option(["--by"], required=True, type=choice(By), help="who merges"),
        click.Option(
            ["--message"],
            help="the subject of the one commit, when branch.history is squash",
        ),
        click.Option(
            ["--via"], type=choice(Via), default="session", help="who runs this call"
        ),
        click.Option(
            ["--standing"],
            is_flag=True,
            help="with --by owner: his merge that a moved base refused, still standing",
        ),
        click.Option(["--tip"], help="the whole commit the caller saw"),
        click.Option(
            ["--checked"],
            help=(
                "the moment of a merge call on record that the owner checked on GitHub: "
                "his word for a new call over it"
            ),
        ),
    ],
    callback=lambda **words: run(msgspec.convert(given(words), Call)),
    help="Merge the pull request, on the owner's word or the merger's.",
)
