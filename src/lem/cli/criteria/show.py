"""`lem criteria show`: a task's criteria, with their state.

    lem criteria show SLUG

The criteria of the task's plan, or the `criteria.md` of a fast-track task, checked against
their approval and the recorded changes: `small` says which, and `plan` names the file. A plan
opens with them:

    ## Acceptance criteria

    Size: full, because the export gets a new column and two readers of it.

    1. A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has
       that text in its row.
       - test: `python3 -m unittest tests.test_export.GiftNote` in `tests/test_export.py`

`Size` is `full` (the standard track) or `small` (the fast track), with its reason. Under a
criterion come the steps of its case, its chart in a `mermaid` block, and then its tests or
`- no test: REASON`; a chart of several criteria goes under `## How it works`, after them.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.criteria import show
from lem.cli import place

if TYPE_CHECKING:
    from lem.model.criteria.standing import Shown


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria show`."""

    slug: str


def run(call: Call) -> Shown:
    """The task's criteria as they stand."""
    return show.shown(place.folder(), call.slug)


COMMAND = click.Command(
    "show",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="A task's criteria, with their state.",
)
