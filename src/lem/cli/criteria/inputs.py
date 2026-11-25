"""`lem criteria inputs`: the inputs of the check of the criteria.

    lem criteria inputs SLUG

What a run of `lem criteria red` would depend on now, without the run: the tip, the base
commit, the plan file, and the settings' `checks.setup` and `checks.serial`; a task whose
criteria `red` could not read is refused in its words. The step `land-checks` owns it.
"""

import click
import msgspec

from lem.app.landing import checks_criteria
from lem.cli import place
from lem.records.red import Inputs
from lem.store import places, tasks


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria inputs`."""

    slug: str


class Shown(msgspec.Struct, frozen=True, kw_only=True):
    """What `lem criteria inputs` prints: the task, and the five inputs."""

    task: str
    inputs: Inputs


def run(call: Call) -> Shown:
    """Give the five inputs a run of the task's check would depend on now."""
    workspace = places.workspace(place.folder())
    record = tasks.read(workspace.state, call.slug)
    found = checks_criteria.inputs(workspace, record)
    return Shown(task=call.slug, inputs=found)


COMMAND = click.Command(
    "inputs",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The inputs of the check of the criteria.",
)
