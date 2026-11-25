"""`lem corrections worker`: judge one correction the hook wrote.

    lem corrections worker PAYLOAD

The correction hook starts it detached, with the file it wrote in `corrections-waiting/`; it
removes the file, asks Jev on the machine's yes, and queues a lesson
(`addons/corrections/worker.py`). Its output goes nowhere.
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING

import click
import msgspec

from lem.kernel import clock

if TYPE_CHECKING:
    from lem.addons.corrections.worker import Worked


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem corrections worker`."""

    payload: str


def run(call: Call) -> Worked:
    """Judge the correction, and queue it when it is a lesson. Jev's client loads here, and
    only for this command."""
    from lem.addons.corrections.worker import worked

    return worked(Path(call.payload), os.environ, clock.now())


COMMAND = click.Command(
    "worker",
    params=[
        click.Argument(["payload"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Judge one correction the hook wrote.",
)
