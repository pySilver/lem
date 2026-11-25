"""`lem task build`: build a planned task, by its slug or its plan file.

    lem task build [SLUG|PLAN-FILE]

A plan file names its task by the plan the task has, else by the slug in its name; with no name
it lists the plans that wait for the owner (the ruling "`/lem build` takes a plan file too, and
lists the waiting plans when it gets no name"). A planned task goes to `building`.
"""

import click
import msgspec

from lem.app.tasks import building
from lem.cli import place
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task build`."""

    target: str | None = None


def run(call: Call) -> building.Built:
    """Start the build of a planned task, or list the plans that wait."""
    return building.built(places.workspace(place.folder()), call.target)


COMMAND = click.Command(
    "build",
    params=[
        click.Argument(["target"], required=False),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Build a planned task, by its slug or its plan file; list them with no name.",
)
