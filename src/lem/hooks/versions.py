"""The plugin's version and the app's, and the one line that names the one behind.

The plugin a session loaded is named by `LEM_PLUGIN_ROOT`, which the `session-start` hook writes;
the app's own plugin files are its root (`kernel.paths.root`). Both `lem` before a command and the
hooks read this line, so it is written with the standard library only, and with no `pathlib`,
which a hook's start does not pay for.
"""

import json
import os

from lem.hooks import raw, where

MANIFEST = ".claude-plugin/plugin.json"
# The update command of each half, for the line that names the one that is behind.
APP_UPDATE = "brew upgrade pySilver/tap/lem"
PLUGIN_UPDATE = "claude plugin update lem@lem"
# What a manifest that does not read is called, and the fix of each half when its manifest is
# damaged (`hooks.version_line` on `main`): that half is installed again.
UNREADABLE = "unreadable"
AGAIN = (
    ("plugin", "installs Lem's plugin again"),
    ("app", "installs Lem again"),
)


def app_root() -> str | None:
    """The folder of the app's plugin files, by the rule of `kernel.paths.root`: `lem/data` in
    an installed app, else the checkout that holds the skill `lem`; None where that rule finds
    none."""
    package = where.parent(where.parent(os.path.realpath(__file__)))
    installed = f"{package}/data"
    if raw.is_folder(installed):
        return installed
    checkout = where.parent(where.parent(package))
    found = os.access(f"{checkout}/skills/lem/SKILL.md", os.F_OK)
    return checkout if found else None


def version_of(folder: str) -> str:
    """The version in the manifest of `folder`; a manifest that does not read is named."""
    path = f"{folder}/{MANIFEST}"
    try:
        manifest = json.loads(raw.read_bytes(path))
    except (OSError, ValueError) as error:
        return f"{UNREADABLE} ({path}: {error})"
    version = manifest.get("version") if isinstance(manifest, dict) else None
    return str(version) if version else f"{UNREADABLE} ({path}: no version)"


def numbers(version: str) -> tuple[int, ...] | None:
    """`1.2.0` as (1, 2, 0); None for anything else."""
    parts = version.split(".")
    if not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def behind(plugin: str, app: str) -> str | None:
    """The line for the plugin at `plugin` and the app at `app` when their versions differ,
    naming the one that is behind with its update command; None when they are one version."""
    theirs, mine = version_of(plugin), version_of(app)
    if theirs == mine:
        return None
    damage = damaged(theirs, mine)
    if damage is not None:
        return damage
    plugin_numbers, app_numbers = numbers(theirs), numbers(mine)
    if plugin_numbers is None or app_numbers is None:
        return (
            f"lem: Lem's plugin {theirs} ({plugin}) and Lem's app {mine} ({app}) are two "
            f"versions; the owner runs `{APP_UPDATE}` and `{PLUGIN_UPDATE}`, and starts the "
            "session again"
        )
    if plugin_numbers < app_numbers:
        return (
            f"lem: Lem's plugin {theirs} ({plugin}) is behind Lem's app {mine}; the owner "
            f"runs `{PLUGIN_UPDATE}` and starts the session again"
        )
    return (
        f"lem: Lem's app {mine} ({app}) is behind Lem's plugin {theirs}; the owner runs "
        f"`{APP_UPDATE}` and starts the session again"
    )


def damaged(theirs: str, mine: str) -> str | None:
    """The line for a half whose manifest does not read: it names the file and why, and the
    fix, to install that half again; None when both read."""
    for (half, fix), version in zip(AGAIN, (theirs, mine), strict=True):
        if version.startswith(UNREADABLE):
            return (
                f"lem: Lem's plugin and Lem's app may be two versions: the {half}'s manifest "
                f"is {version}; the owner {fix} and starts the session again"
            )
    return None
