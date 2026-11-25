"""The plugin's version and the app's, and the one line that names the one behind.

The plugin a session loaded is named by `LEM_PLUGIN_ROOT`, which the `session-start` hook writes;
the app's own plugin files are its root (`kernel.paths.root`). Both `lem` before a command and the
hooks read this line, so it is written with the standard library only.
"""

import json
from pathlib import Path

MANIFEST = Path(".claude-plugin") / "plugin.json"
# The update command of each half, for the line that names the one that is behind.
APP_UPDATE = "brew upgrade pySilver/tap/lem"
PLUGIN_UPDATE = "claude plugin update lem@lem"


def version_of(folder: str) -> str:
    """The version in the manifest of `folder`; a manifest that does not read is named."""
    path = Path(folder) / MANIFEST
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return f"unreadable ({path}: {error})"
    version = manifest.get("version") if isinstance(manifest, dict) else None
    return str(version) if version else f"unreadable ({path}: no version)"


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
