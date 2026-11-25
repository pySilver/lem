"""`lem land file` as a step: under the task's step lock, where `file` is due, and with
`--again` where `propose` is due too, which refuses an item gone from the tip or an open item the
owner set to `worth: no` and names this word (`item-gone`, `item-refuted`)."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import filing, step
from lem.app.landing import next as next_step
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.kernel.envelope import Envelope
    from lem.model.landing.filing_flags import Flags
    from lem.model.landing.world import Verb


def due_step(folder: Path, slug: str) -> str:
    """The step due for the task now, as `lem land next` names it."""
    workspace = places.workspace(folder)
    return next_step.due_of(workspace, tasks.read(workspace.state, slug)).step


def run(folder: Path, slug: str, flags: Flags) -> Envelope:
    """`lem land file SLUG [--again] [--same RN.M=PATH]... [--new RN.M]...`."""
    verb: Verb = "file"
    if flags.again and due_step(folder, slug) == "propose":
        verb = "propose"
    return step.landed(folder, slug, verb, partial(filing.act, flags=flags))
