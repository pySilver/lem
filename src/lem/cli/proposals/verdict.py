"""`lem proposals verdict`: the reviewer's verdict on each proposal.

    lem proposals verdict --file FILE

The verdicts are a JSON object from the file or from standard input; each passed area becomes
one item of the state folder's backlog, and each refuted proposal a `worth: no` item
(`addons/proposals/verdicting.py`).
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.addons.proposals import given, verdicting, verdicts
from lem.cli import place
from lem.kernel import clock
from lem.store import places

if TYPE_CHECKING:
    from lem.addons.proposals.judgment import Judgment


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem proposals verdict`."""

    path: str


def run(call: Call) -> Judgment:
    """Write the reviewer's verdicts, the items first, then the records."""
    state = places.state_of(places.workspace(place.folder()).checkout)
    told = given.read_given(call.path, verdicts.VerdictsGiven, verdicts.FORM)
    return verdicting.judged(state, told, clock.now().date())


COMMAND = click.Command(
    "verdict",
    params=[
        click.Option(
            ["--file", "path"],
            required=True,
            help="the verdicts as JSON, or - for stdin",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The reviewer's verdict on each proposal.",
)
