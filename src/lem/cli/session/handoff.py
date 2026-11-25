"""`lem session handoff`: check the task's handoff.md against its template.

    lem session handoff SLUG --check

It reads the task's `handoff.md` and gives its first line's facts and its changed files, or
refuses with each part it lacks (`app/sessions/handoff.py`).
"""

import click
import msgspec

from lem.app.sessions import handoff, here
from lem.cli import place
from lem.cli.checks import exactly_one
from lem.kernel.errors import Refusal


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session handoff`."""

    slug: str
    check: bool = False


def run(call: Call) -> handoff.Form:
    """Check the task's handoff against its template."""
    folder = here.bound(place.folder()).folder(call.slug)
    path = folder / handoff.HANDOFF
    if not path.is_file():
        raise Refusal(
            "no-handoff",
            f"{path} is not there",
            "write it in the form of `templates/handoff.md`",
        )
    return handoff.form(path.read_text(encoding="utf-8"), call.slug)


COMMAND = click.Command(
    "handoff",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--check"],
            is_flag=True,
            help="check the handoff against templates/handoff.md",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(exactly_one(given, "check"), Call)),
    help="Check the task's handoff.md against its template.",
)
