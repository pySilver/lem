"""The merge a drop must see under the step lock, even if the pull number was lost."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import changes, pull_identity
from lem.model.landing import destination
from lem.records.landing import record as landing_record
from lem.settings import load as settings_load
from lem.store import tasks

if TYPE_CHECKING:
    from lem.ports.forge import Forge
    from lem.records.record import Record
    from lem.store.places import Workspace


def merged(
    forge: Forge, where: Workspace, record: Record, landing: landing_record.Landing
) -> bool:
    """Verify the recorded PR or keep the identity of a recovered PR for `merged`."""
    if landing.pull is not None:
        shown = pull_identity.checked(record, forge.pull(landing.pull.number))
        base = destination.recorded(landing) or settings_load.base_of(
            settings_load.team_of(where.checkout)
        )
        return shown.state == "merged" and shown.base == base
    if landing.started is None or landing.pushed is None:
        return False
    found = pull_identity.recovered(forge, landing.started, landing.pushed)
    if found is None:
        return False
    pull = landing_record.Pull(number=found.number, url=found.url, title=found.title)
    change = partial(changes.landing, pull=pull)
    tasks.update(where.state, record.task.slug, change, record.revision)
    return True
