"""What Claude Code installed as plugins: its list, `~/.claude/plugins/installed_plugins.json`,
and whether its settings leave a plugin on in a repository.

The list is the agent's own and may read any way: a list of another shape is no answer, and an
entry that names neither the user nor a project is skipped. An install for the user (or one
managed for him) counts in every repository, an install for a project only in that project.
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.cli.doctor.checkouts import files_of, table_of
from lem.kernel import folders

if TYPE_CHECKING:
    from collections.abc import Iterable

type Roots = tuple[Path, ...]
LISTED = Path(".claude") / "plugins" / "installed_plugins.json"
# The scopes of an install for the user, and of one for a project.
FOR_USER = frozenset(("user", "managed"))
FOR_PROJECT = frozenset(("project", "local"))


class Entry(msgspec.Struct, frozen=True, kw_only=True):
    """One install as Claude Code's list writes it."""

    scope: str | None = None
    project: str | None = msgspec.field(default=None, name="projectPath")
    folder: str | None = msgspec.field(default=None, name="installPath")
    version: str | None = None


class Listed(msgspec.Struct, frozen=True, kw_only=True):
    """Claude Code's list: each plugin's key and its installs."""

    plugins: dict[str, list[Entry]] = msgspec.field(default_factory=dict)


class Install(msgspec.Struct, frozen=True, kw_only=True):
    """One install: its key (`NAME@MARKETPLACE`), its scope, the real path of its project
    (None for the user), its folder and its version, as the list names them."""

    key: str
    scope: str
    project: str | None
    folder: str | None
    version: str | None

    def reaches(self, here: set[str]) -> bool:
        """Whether a repository of the real paths `here` gets this install."""
        return self.project is None or self.project in here

    @property
    def name(self) -> str:
        """The plugin's name, the key before its marketplace."""
        return self.key.split("@")[0]


def install_of(key: str, entry: Entry) -> Install | None:
    """The install `entry` of the plugin `key`; None for an entry of no known scope. Under the
    test entry, a folder outside the test's own is a fault before any row reads it."""
    if entry.scope in FOR_USER:
        project = None
    elif entry.scope in FOR_PROJECT and entry.project:
        project = os.path.realpath(entry.project)
    else:
        return None
    if entry.folder:
        folders.inside_test_root(Path(entry.folder))
    return Install(
        key=key,
        scope=entry.scope,
        project=project,
        folder=entry.folder,
        version=entry.version,
    )


def installs(home: Path) -> tuple[Install, ...]:
    """Every install in Claude Code's list in `home`; none when the list is absent or reads
    another way."""
    try:
        listed = msgspec.json.decode((home / LISTED).read_bytes(), type=Listed)
    except OSError, msgspec.DecodeError:
        return ()
    found = (
        install_of(key, entry)
        for key, entries in listed.plugins.items()
        for entry in entries
    )
    return tuple(one for one in found if one is not None)


def reaching(found: Iterable[Install], roots: Roots) -> tuple[Install, ...]:
    """The installs a repository of `roots` gets: each for the user, and each for one of
    them."""
    here = {str(root) for root in roots}
    return tuple(one for one in found if one.reaches(here))


def enabled(key: str, home: Path, root: Path | None) -> bool:
    """Whether Claude Code turns the plugin `key` on in the repository `root` (None: outside
    one). The repository's local settings say it first, then its shared ones, then the
    user's (code.claude.com/docs/en/settings-reference, `enabledPlugins`, read 2026-11-17).
    With no word the plugin is on: an install writes the word."""
    for path in files_of(home, root):
        said = table_of(path).get("enabledPlugins")
        word = said.get(key) if isinstance(said, dict) else None
        if isinstance(word, bool):
            return word
    return True
