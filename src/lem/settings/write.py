"""`lem settings set KEY VALUE --local|--home|--machine`: one setting written into one file.

`--local` writes the main checkout's `.lem/settings.local.toml`, from a task's worktree too; its
lock is in the state folder, which git never sees. `--home` and `--machine` write Lem's home
folder, through the one way a home is written (`folders.home_for_writing`), so that nothing is
written beside the files of the Lem before.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.kernel import folders, paths
from lem.kernel.errors import Refusal
from lem.settings import edit, places, reading, words
from lem.settings.answer import Set, answer
from lem.store import places as stores

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

LOCK = "settings.lock"


@dataclass(frozen=True, kw_only=True, slots=True)
class Asked:
    """The words of one `set`: the key, the word of its value, the file, the folder of the
    call, and its environment."""

    key: str
    word: str
    scope: places.Scope
    folder: Path
    environ: Mapping[str, str]


def checkout_of(folder: Path, scope: places.Scope) -> Path | None:
    """The main checkout of the workspace `folder` is in; None outside one for a file of the
    home folder, which needs none."""
    try:
        return stores.workspace(folder).checkout
    except Refusal:
        if scope in places.REPOSITORY:
            raise
        return None


def file_of(scope: places.Scope, where: reading.Where) -> tuple[Path, Path]:
    """The file of `scope` and its lock; a file of the home folder marks the home first."""
    if scope == places.Scope.local and where.checkout is not None:
        locks = stores.locks_folder(stores.state_of(where.checkout))
        return where.checkout / places.LOCAL, locks / LOCK
    home = folders.home_for_writing(where.environ)
    path = places.path_of(scope, home)
    return path, path.with_suffix(".lock")


def edit_for(asked: Asked, where: reading.Where) -> edit.Edit:
    """The edit `asked` names; a table its file may not hold is refused first."""
    table, name = words.table_key(asked.key)
    words.writable(table, asked.scope, where.named(asked.scope))
    path, lock = file_of(asked.scope, where)
    given = words.typed(asked.key, asked.word)
    return edit.Edit(
        scope=asked.scope, path=path, lock=lock, table=table, key=name, given=given
    )


def set_setting(asked: Asked) -> Set:
    """Write the setting `asked` names, checked first; `default` takes the line out."""
    checkout = checkout_of(asked.folder, asked.scope)
    home = paths.home(asked.environ)
    where = reading.Where(checkout=checkout, home=home, environ=asked.environ)
    change = edit_for(asked, where)
    edit.applied(change, where)
    return answer(change, asked.key, where)
