"""A row for each repository of the server's list whose installed Lem is another release than
the board server runs: a session there runs one Lem, and the server's duties over it another.

The install a repository gets is the one for its project, else the one for the user, from
Claude Code's list; its release is its folder's manifest, else the version the list names. No
server that runs, or a repository with no install, gives no row: the row `board server` says
the first.
"""

import os
import shlex
from pathlib import Path
from typing import TYPE_CHECKING

from lem.board.workspaces import listed
from lem.cli.doctor import plugins
from lem.cli.doctor.board_rows import running
from lem.cli.doctor.hook_bin import lem_for
from lem.cli.doctor.row import OPTIONAL, Row
from lem.hooks import versions
from lem.kernel import paths

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look

ENSURE = "lem serve ensure"


def release_of(found: plugins.Install) -> str:
    """The release of an install: its folder's manifest, else the list's version."""
    manifest = Path(found.folder or "") / versions.MANIFEST
    if found.folder and manifest.is_file():
        return versions.version_of(found.folder)
    return found.version or "an unknown version"


def which_older(theirs: str, server: str) -> str:
    """Which of the two releases is the older, when both are numbers."""
    mine, other = versions.numbers(theirs), versions.numbers(server)
    if mine is None or other is None:
        return "which is the newer is not known"
    return "the install is the older" if mine < other else "the server is the older"


def install_row(repository: str, found: plugins.Install, server: str) -> Row | None:
    """The row of one repository and the install it gets; None when it runs the server's
    release."""
    theirs = release_of(found)
    if theirs == server:
        return None
    scope = "user" if found.scope == "managed" else found.scope
    update = f"cd {shlex.quote(repository)} && claude plugin update {found.key} --scope {scope}"
    return Row(
        name=f"installed Lem: {Path(repository).name}",
        need=OPTIONAL,
        found=False,
        detail=f"{repository} has {theirs} of {found.key} installed for the {found.scope}, "
        f"and the board server runs {server}; {which_older(theirs, server)}",
        used_for=(
            "one Lem for a repository's task sessions and for the board server's duties "
            "over them"
        ),
        without_it=(
            "a task's session runs other code than the server that wakes it and merges for "
            "it: run the first line in a terminal and restart that repository's sessions, or "
            f"`{ENSURE}` from the newer Lem to replace the server"
        ),
        line=update,
        lines=(update, ENSURE),
    )


def installed_rows(look: Look) -> tuple[Row, ...]:
    """The rows of `install_row` for this machine's server, list and installs."""
    facts = running(look)
    if facts is None:
        return ()
    found = plugins.installs(look.home)
    rows = (
        install_row(repository, mine, facts.install.version)
        for repository in listed(paths.home(look.environ))
        if (mine := lem_for(os.path.realpath(repository), found)) is not None
    )
    return tuple(row for row in rows if row is not None)
