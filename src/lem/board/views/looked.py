"""What the views read beside the records of the owner and the forge: the board server's last
look at the forge (`board_model.forge_look` on `main`: when it looked, and the tasks whose pull
request it called conflicting at the head Lem proposed last; a file that does not read is the
problem the status bar says), and whether each task runs without the owner now."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.owner import forge
from lem.board.views.world import Forge
from lem.model.owner import presence as presence_rule

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.views.world import Seen
    from lem.records.owner import Presence
    from lem.records.record import Record


def forge_of(state: Path, records: tuple[Record, ...]) -> Forge:
    """The look of the state folder `state` at the forge, over the workspace's records."""
    look = forge.read(state)
    conflicts = frozenset(
        record.task.slug for record in records if forge.conflicts(look, record)
    )
    return Forge(looked=look.looked, conflicts=conflicts, problem=look.said)


def alone(seen: Seen, presence: Presence) -> Seen:
    """The task, with whether it runs without the owner now: he is away, or the night opened
    it."""
    return replace(seen, alone=presence_rule.alone(seen.record.task, presence))
