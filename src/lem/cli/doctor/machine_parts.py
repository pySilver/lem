"""The parts of `lem doctor` that look at this machine's settings and board, at the repository
of the call, at the plugin's hooks and at Lem's own halves, in the order the owner reads them."""

from typing import TYPE_CHECKING

from lem.cli.doctor import (
    app_rows,
    board_rows,
    door_rows,
    hook_bin,
    machine_rows,
    project_rows,
)
from lem.cli.doctor.correction_hook import correction_hook_rows
from lem.cli.doctor.installed import installed_rows
from lem.cli.doctor.old_forms import old_forms_row
from lem.cli.doctor.reads import reads_row
from lem.cli.doctor.row import OPTIONAL, PROJECT, REQUIRED

if TYPE_CHECKING:
    from lem.cli.doctor.row import Part

MACHINE_PARTS: tuple[Part, ...] = (
    ("load gate", OPTIONAL, machine_rows.load_row),
    ("handoff tokens", OPTIONAL, machine_rows.handoff_row),
    ("board server", OPTIONAL, board_rows.server_row),
    ("installed Lem", OPTIONAL, installed_rows),
    ("board notifications", OPTIONAL, door_rows.notifications_row),
    ("board door", OPTIONAL, door_rows.door_row),
    ("project personas", PROJECT, project_rows.persona_rows),
    ("correction hook", PROJECT, correction_hook_rows),
    ("hook modules", REQUIRED, hook_bin.hooks_row),
    ("hooks/run finds lem-hook", REQUIRED, hook_bin.lem_hook_row),
    ("permission mode", PROJECT, project_rows.mode_rows),
    ("lem plugin scope", PROJECT, project_rows.scope_rows),
    ("Lem's versions", REQUIRED, app_rows.versions_row),
    ("lem on PATH", REQUIRED, app_rows.lem_row),
    ("reads of Lem's files", OPTIONAL, reads_row),
    ("folders of Lem 0.3", REQUIRED, old_forms_row),
)
