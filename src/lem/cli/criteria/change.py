"""`lem criteria change`: the owner's change of a task's criteria.

    lem criteria change SLUG --typed --words NOTE
    lem criteria change SLUG --file FILE --words NOTE
    lem criteria change SLUG --pairs
    lem criteria change SLUG --unchanged

A change of the criteria from his note, on the standard track while they wait for his yes; it
approves nothing, and the criteria wait for his yes again. `--typed`: his No, typed in the task's
session, recorded as the answer to the wait before the new text is written; an answer of the
board that came first refuses it. `--file`: the text he answered kept, FILE written as the task's
`criteria.md`, and his yes asked again under a new question; it prints each changed criterion
before and after (`pairs`), and run again with the same file it ends a change that stopped in
the middle. `--pairs`: the pairs of the newest change again, while its wait stands.
`--unchanged`: after his No whose note changes no criterion (a direction, a question), the same
criteria wait for his yes again. Refused on the fast track, after an approval of the standard
track (a change is then `lem decisions criterion`), and after an approval since the wait began.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.criteria import change, typed
from lem.cli import place
from lem.cli.checks import Given, exactly_one

if TYPE_CHECKING:
    from lem.model.criteria.note import Shown


NEEDS = "--typed and --file need --words, his note"
TAKES = "only --typed and --file take --words"


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria change`."""

    slug: str
    path: str | None = None
    words: str | None = None
    typed: bool = False
    pairs: bool = False
    unchanged: bool = False


def run(call: Call) -> Shown | typed.Answered | typed.Again:
    """The change, his typed No, the pairs again, or a new wait of the same criteria."""
    folder, words = place.folder(), call.words or ""
    if call.typed:
        return typed.typed(folder, call.slug, words)
    if call.pairs:
        return change.again(folder, call.slug)
    if call.unchanged:
        return typed.unchanged(folder, call.slug)
    return change.changed(folder, call.slug, Path(call.path or ""), words)


def fitted(given: Given) -> Given:
    """Refuse a call that does not give one of its four forms, or whose note does not fit
    it: `--typed` and `--file` take `--words`, the other two take none."""
    exactly_one(given, "path", "typed", "pairs", "unchanged")
    noted = given["path"] is not None or bool(given["typed"])
    if noted != (given["words"] is not None):
        said = (
            "--typed and --file take --words"
            if noted
            else "only --typed and --file take --words"
        )
        raise click.UsageError(said, click.get_current_context())
    return given


COMMAND = click.Command(
    "change",
    params=[
        click.Argument(["slug"]),
        click.Option(["--file", "path"], help="the changed criteria"),
        click.Option(["--words"], help="the owner's note, in his words"),
        click.Option(
            ["--typed"],
            is_flag=True,
            help="record the owner's No typed in the task's session",
        ),
        click.Option(
            ["--pairs"], is_flag=True, help="print the pairs of the newest change again"
        ),
        click.Option(
            ["--unchanged"],
            is_flag=True,
            help="the owner's No changes no criterion: the same criteria wait",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(fitted(given), Call)),
    help="The owner's change of a task's criteria.",
)
