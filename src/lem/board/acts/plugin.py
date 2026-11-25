"""The version check for the plugin a new task's session will load."""

import os
from pathlib import Path

from lem.adapters import claude_plugin
from lem.hooks import versions
from lem.kernel import folders, paths
from lem.kernel.errors import Refusal


def checked(checkout: Path) -> None:
    """Refuse a start whose session could not use the app with its installed plugin."""
    installed = claude_plugin.selected(checkout, os.environ)
    if installed is None:
        return
    fix = f"the owner runs `{versions.PLUGIN_UPDATE}` and starts the task again"
    if not isinstance(installed.folder, str) or not installed.folder:
        raise Refusal(
            "plugin-version", "Claude Code lists Lem's plugin without its path", fix
        )
    folders.inside_test_root(Path(installed.folder))
    behind = versions.behind(installed.folder, str(paths.root()))
    if behind is not None:
        raise Refusal("plugin-version", f"{behind}.", fix)
