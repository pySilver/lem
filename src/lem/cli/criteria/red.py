"""`lem criteria red`: whether each criterion's tests pass on the branch and fail on the base.

    lem criteria red SLUG

The run is written to the task's record and printed. A run that does not hold is refused in the
words of its first test with a problem, as `criteria.main` on `main` exits 1 for it. A term, an
interrupt or a hangup while it runs ends its tests and removes its worktrees, then refuses. The
step `land-checks` owns it.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.landing import checks_criteria, checks_group
from lem.cli import place
from lem.kernel import clock
from lem.model.landing import checks_red
from lem.store import places, tasks

if TYPE_CHECKING:
    from lem.records.red import Red


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria red`."""

    slug: str


def run(call: Call) -> Red:
    """Run the check of the task's criteria, write it on its record, and print it."""
    workspace = places.workspace(place.folder())
    record = tasks.read(workspace.state, call.slug)
    with checks_group.trapped():
        made = checks_criteria.red(workspace, record, clock.now())
    refusal = checks_red.failed(made)
    if refusal:
        raise refusal
    return made


COMMAND = click.Command(
    "red",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Whether each criterion's tests fail on the base.",
)
