"""The kind of the workspace's tracker, `[tracker] kind` of `.lem/settings.toml`, or None.

A stand-in until the step `settings` gives the team's settings a `[tracker]` table
(`notes/task.md`): it reads the one key from the team's file, which `settings.load` already
checks for its form and its places.
"""

from typing import TYPE_CHECKING, Literal

import msgspec

from lem.kernel.errors import Refusal
from lem.settings import places
from lem.settings.load import tables

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.tickets import Tracker


class Table(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """`[tracker]`: the one key."""

    kind: Literal["linear", "github"]


def kind_of(checkout: Path) -> Tracker | None:
    """The tracker's kind in the team's file of `checkout`, or None when it names none."""
    path = checkout / places.TEAM
    found = tables(path).get("tracker") if path.is_file() else None
    if found is None:
        return None
    try:
        return msgspec.convert(found, Table).kind
    except msgspec.ValidationError as error:
        raise Refusal(
            "settings",
            f"{path}: [tracker] {error}",
            'write kind = "linear" or kind = "github" under [tracker], or remove the table',
        ) from error
