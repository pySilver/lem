"""What git said of the backlog folder, once for the whole folder and never once for each item
(`board.backlog` on `main`): who added each item, and which items git has no commit of, or a
change since."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.board.views.backlog import ledger

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.views.backlog_read import AddedBy, Entry


@dataclass(frozen=True, kw_only=True, slots=True)
class Known:
    """Whether git told who added the items, the commit that added each, the paths it has no
    commit of, and those it has with a change since."""

    told: bool = False
    added: dict[str, AddedBy] = field(default_factory=dict)
    new: frozenset[str] = frozenset()
    edited: frozenset[str] = frozenset()

    def marked(self, entry: Entry) -> Entry:
        """The entry with what git says of its path."""
        path = entry.path
        tracked, changed = path not in self.new, path in self.edited
        added = self.added.get(path)
        return replace(entry, added=added, tracked=tracked, changed=changed)


def known_of(git: ledger.Ledger | None, checkout: Path, folder: str) -> Known:
    """What git says of the backlog folder `folder`; nothing while git is not asked or the
    folder is not there."""
    if git is None or not (checkout / folder).is_dir():
        return Known()
    adds = git.adds(checkout, folder)
    new, edited = ledger.changes(git.unsaved(checkout, folder) or ())
    if adds is None:
        return Known(new=new, edited=edited)
    added = ledger.added_by(adds, folder)
    return Known(told=True, added=added, new=new, edited=edited)
