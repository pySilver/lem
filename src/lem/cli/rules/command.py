"""`lem rules`: the rule files that hold for FILES and a range's files.

    lem rules [FILES]... [--range RANGE]

A file is named relative to the checkout the call starts in, or by its absolute path; a range
adds each file its commits change, a moved file under its old name and its new one. The rules
are read from `.claude/rules` of that checkout, where the agent loads them by itself, in any
repository, with Lem set up there or not, as on `main`.
"""

import click
import msgspec

from lem.cli import place
from lem.cli.checks import at_least_one
from lem.cli.rules.named import checkout_of, named
from lem.cli.rules.picked import Picked, picked
from lem.cli.rules.ranged import range_names


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem rules`."""

    files: tuple[str, ...] = ()
    commits: str | None = None


def run(call: Call) -> Picked:
    """The rule files that hold for the files the call names and the range's files."""
    root = checkout_of(place.folder())
    given = tuple(named(root, word) for word in call.files)
    ranged = range_names(root, call.commits) if call.commits else ()
    return picked(root, tuple(sorted({*given, *ranged})))


COMMAND = click.Command(
    "rules",
    params=[
        click.Argument(["files"], nargs=-1),
        click.Option(
            ["--range", "commits"], help="also the files this range of commits changes"
        ),
    ],
    callback=lambda **given: run(
        msgspec.convert(at_least_one(given, "files", "commits"), Call)
    ),
    help="The rule files that hold for FILES and a range's files.",
)
