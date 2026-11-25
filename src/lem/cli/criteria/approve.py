"""`lem criteria approve`: approve a task's criteria.

    lem criteria approve SLUG [--file FILE] [--small|--read|--alone] [--shown DIGEST]

The plain form of the fast track, as the step `slice-land` built it; the step `criteria` owns it.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.criteria import approve
from lem.cli import place
from lem.model.landing.world import later

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


def run(call: Call) -> Approval:
    """Approve the fast track's criterion in the owner's name; his own approval, the lead's
    and one without him are the step `criteria`'s."""
    others = (call.path, call.read, call.alone, call.shown)
    if not call.small or any(others):
        raise later("`lem criteria approve --file|--read|--alone|--shown`", "criteria")
    return approve.approved(place.folder(), call.slug)


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
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Approve a task's criteria.",
)
