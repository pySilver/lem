"""`lem task resume`: bring back a parked task, or start again from a dropped one.

    lem task resume SLUG

A parked task comes back as it was; a dropped one goes on in a new task, from its breaker's
handoff or, when the release stop dropped it, as a new request (`app/tasks/resume.py`).
"""

import click
import msgspec

from lem.app.tasks import resume
from lem.cli import place
from lem.kernel.envelope import Envelope, Next


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task resume`."""

    slug: str


def run(call: Call) -> Envelope:
    """Resume the task, and name the session a new request opens."""
    resumed = resume.resumed(place.folder(), call.slug)
    outcome = msgspec.Raw(msgspec.json.encode(resumed))
    if resumed.resumed != "request":
        return Envelope(ok=True, outcome=outcome, say=resumed.says)
    command = f"lem session open {resumed.task} --why new"
    following = Next(act="run", command=command, why="its session takes its shape anew")
    return Envelope(ok=True, outcome=outcome, say=resumed.says, following=following)


COMMAND = click.Command(
    "resume",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Bring back a parked task, or start again from a dropped one.",
)
