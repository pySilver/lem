"""Which plugin Claude Code has for the repository, and whether its `hooks/run` finds the app's
`lem-hook`.

`hooks/run` reads no PATH, since a Claude Code that a GUI app started has `/usr/bin:/bin` alone
(seen 2026-11-24): it tries `$LEM_HOOK_BIN` when that is an absolute path, else Homebrew's
`opt/lem/libexec/bin/lem-hook` on Apple silicon, then on Intel, then uv's tool folder
`${XDG_BIN_HOME:-$HOME/.local/bin}`. The row looks in the same order.
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING

from lem.cli.doctor import plugins
from lem.cli.doctor.checkouts import main_checkout
from lem.cli.doctor.hook_modules import hook_modules_row
from lem.cli.doctor.row import REQUIRED, Row
from lem.hooks.other import same
from lem.kernel import paths

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look

HOOK = "lem-hook"
BREWED = Path("opt") / "lem" / "libexec" / "bin" / HOOK


def lem_for(
    project: str | None, found: tuple[plugins.Install, ...]
) -> plugins.Install | None:
    """The install of Lem the repository at the real path `project` gets: its own, else the
    user's (None: outside a repository, the user's only)."""
    lems = [one for one in found if one.name == "lem"]
    for wanted in (project, None):
        own = next((one for one in lems if one.project == wanted), None)
        if own is not None:
            return own
    return None


def plugin_folder(look: Look, root: Path | None) -> Path:
    """The plugin Claude Code has for the repository `root` (None: outside one): the folder of
    Lem's install for `root`, else for the user, when the settings leave it on and the folder
    is there; else the app's own files, which have the plugin's shape and which a task's
    session then loads."""
    real = str(root.resolve()) if root else None
    mine = lem_for(real, plugins.installs(look.home))
    if mine is None or not mine.folder:
        return paths.root()
    folder = Path(mine.folder or "")
    if plugins.enabled(mine.key, look.home, root) and folder.is_dir():
        return folder
    return paths.root()


def hooks_row(look: Look) -> Row:
    """The row of the hooks of the plugin Claude Code has for the main checkout of the call,
    and of the app's package."""
    plugin = plugin_folder(look, main_checkout(look.folder))
    return hook_modules_row(plugin, paths.PACKAGE)


def candidates(look: Look) -> tuple[Path, ...]:
    """The paths `hooks/run` tries, in its order."""
    named = look.environ.get("LEM_HOOK_BIN", "")
    if named:
        return (Path(named),) if named.startswith("/") else ()
    named_tools = look.environ.get("XDG_BIN_HOME")
    tools = Path(named_tools) if named_tools else look.home / ".local" / "bin"
    brewed = [brew / BREWED for brew in look.brews]
    return (*brewed, tools / HOOK)


def runnable(path: Path) -> bool:
    """Whether `hooks/run` would run `path`: a file this process may run."""
    return path.is_file() and os.access(path, os.X_OK)


def hook_said(look: Look) -> tuple[bool, str]:
    """Whether `hooks/run` finds a `lem-hook`, and which, against this app's."""
    tried = candidates(look)
    found = [path for path in tried if runnable(path)]
    if not found:
        listed = ", ".join(map(str, tried))
        return False, f"none of {listed}"
    own = look.executable.parent / HOOK
    first = found[0]
    if same(str(first), str(own)):
        return True, f"{first}, this app's"
    return True, f"{first}, not this app's {own}"


def lem_hook_row(look: Look) -> Row:
    """Whether `hooks/run` finds `lem-hook`, and whether it is this app's."""
    found, detail = hook_said(look)
    return Row(
        name="hooks/run finds lem-hook",
        need=REQUIRED,
        found=found,
        detail=detail,
        used_for=(
            "every hook of the plugin: Claude Code starts `hooks/run`, which starts the app's "
            "lem-hook from a fixed path, never from PATH"
        ),
        without_it=(
            "no hook runs and none says so; the owner installs Lem's app with Homebrew "
            "(`brew install pySilver/tap/lem`) or as a uv tool, or sets LEM_HOOK_BIN to "
            "the absolute path of a lem-hook in the environment Claude Code starts with"
        ),
    )
