"""`lem criteria approve`: approve a task's criteria.

    lem criteria approve SLUG --file FILE [--shown DIGEST]
    lem criteria approve SLUG --small [--file FILE]
    lem criteria approve SLUG --read
    lem criteria approve SLUG --file FILE --alone

The owner's yes keeps FILE word for word, with no test lines; with `--shown`, the bytes his page
showed, and nothing when the file changed since. `--small`: Lem approves the one criterion of a
fast-track task in his name, as its first contract only, from `criteria.md` of the task's folder
unless FILE names another. `--read`: the lead freezes the plan's own criteria after a read that
nobody was confused by, as the first contract of a standard-track task from a complete request.
`--alone`: Lem or the lead approves FILE while the task runs without the owner. Neither `--read`
nor `--alone` is ever his yes.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.criteria import approve
from lem.cli import place
from lem.cli.checks import Given, at_most_one

if TYPE_CHECKING:
    from lem.records.approvals import Approval


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria approve`."""

    slug: str
    path: str | None = None
    small: bool = False
    read: bool = False
    alone: bool = False
    shown: str | None = None


def asked(call: Call) -> approve.Asked:
    """The approval the words ask for."""
    named = Path(call.path) if call.path else None
    if call.small:
        return approve.Asked(by="lem", path=named)
    if call.read:
        return approve.Asked(by="read")
    return approve.Asked(
        by="alone" if call.alone else "owner", path=named, shown=call.shown
    )


def run(call: Call) -> Approval:
    """Approve the task's criteria as the words ask."""
    return approve.approved(place.folder(), call.slug, asked(call))


def wrong(given: Given) -> str | None:
    """What is wrong with a call that gives `--read` with a file, an approval of the owner's
    or without him with no file, or `--shown` with no file of his; None when nothing is."""
    named = given["path"] is not None
    reading = bool(given["read"])
    if reading and named:
        return "--read freezes the plan's own criteria: no --file"
    if not (named or reading or given["small"]):
        return "approve needs --file: the criteria approved"
    shows = given["shown"] is not None
    if shows and (reading or given["small"] or not named):
        return "--shown goes with --file, the owner's own approval"
    return None


def fitted(given: Given) -> Given:
    """Refuse a call that names two approvers, or whose words do not fit its approver."""
    at_most_one(given, "small", "read", "alone")
    said = wrong(given)
    if said is not None:
        raise click.UsageError(said, click.get_current_context())
    return given


COMMAND = click.Command(
    "approve",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--file", "path"], help="the criteria approved, with no test lines"
        ),
        click.Option(
            ["--small"],
            is_flag=True,
            help="Lem approves the one criterion of a fast-track task",
        ),
        click.Option(
            ["--read"],
            is_flag=True,
            help="the lead freezes criteria a read found clear",
        ),
        click.Option(
            ["--alone"],
            is_flag=True,
            help="the criteria of a task that runs without the owner",
        ),
        click.Option(
            ["--shown"],
            help="with --file: the digest of the file as the owner's page showed it",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(fitted(given), Call)),
    help="Approve a task's criteria.",
)
