"""The merge a drop must see under the step lock, even if the pull number was lost."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import changes, pull_identity
from lem.app.tasks import bases
from lem.records.landing import record as landing_record
from lem.store import tasks

if TYPE_CHECKING:
    from lem.app.wiring import Ports
    from lem.records.record import Record
    from lem.store.places import Workspace


def merged(
    given: Ports, place: Workspace, record: Record, landing: landing_record.Landing
) -> bool:
    """Verify the recorded PR or keep the identity of a recovered PR for `merged`."""
    forge = given.forge
    if landing.pull is not None:
        shown = pull_identity.checked(record, forge.pull(landing.pull.number))
        return shown.state == "merged" and shown.base == bases.chosen(
            given.git, place, record
        )
    if landing.started is None or landing.pushed is None:
        return False
    found = pull_identity.recovered(forge, landing.started, landing.pushed)
    if found is None:
        return False
    pull = landing_record.Pull(number=found.number, url=found.url, title=found.title)
    change = partial(changes.landing, pull=pull)
    tasks.update(place.state, record.task.slug, change, record.revision)
    return True
