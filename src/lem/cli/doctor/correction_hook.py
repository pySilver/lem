"""The row of the correction hook registered in more than one place for this repository.

The hook comes with Lem's plugin. A second place is a settings file of Claude Code that names it
too, in any form added by hand: the plugin's line, whose core is `"$CLAUDE_PLUGIN_ROOT/hooks/run"
corrections`, or the app's entry itself, `lem-hook corrections`. No command of Lem's writes a
settings file, so the row names each entry to delete by hand; one in the repository's shared
settings is a change to commit too. The hook judges each message once however often it starts,
so the row is about telling the truth, not about a wrong queue: it never fails the check.
"""

from typing import TYPE_CHECKING

from lem.cli.doctor import plugins
from lem.cli.doctor.checkouts import roots
from lem.cli.doctor.hook_entries import Removal, removals
from lem.cli.doctor.row import PROJECT, Row

if TYPE_CHECKING:
    from pathlib import Path

    from lem.cli.doctor.look import Look

SEEN = (
    "The check reads the settings files of the home and of this repository and Claude "
    "Code's list of plugins; it does not see managed settings, a session's --settings, or a "
    "plugin loaded for one session by a flag"
)


def plugin_of(look: Look, root: Path | None) -> str | None:
    """`the plugin KEY` when Lem's plugin is installed for the user or for `root`, and the
    settings leave it on there."""
    real = str(root.resolve()) if root else None
    for install in plugins.installs(look.home):
        mine = install.project in {None, real} and install.name == "lem"
        if mine and plugins.enabled(install.key, look.home, root):
            return f"the plugin {install.key}"
    return None


def registered(look: Look) -> tuple[list[Removal], str | None]:
    """Each entry of the hook in a settings file for this repository with its removal, and
    Lem's plugin when it brings the hook here."""
    here = roots(look.folder)
    root = here[0] if here else None
    return removals(look, root), plugin_of(look, root)


def fixed(extra: list[Removal], plugin: str | None) -> str:
    """What the row says happens with the hook in more than one place, and the way out."""
    fix = "The plugin brings the hook, so remove each other place"
    if plugin is None:
        fix = "The hook comes with Lem's plugin: install it, and remove each of these"
    removed = "; ".join(": ".join(one) for one in extra)
    return (
        "Claude Code starts the hook once for each place. The first copy claims the "
        "message, so it is still judged once, and each other copy starts for nothing. "
        f"{fix}: {removed}. {SEEN}"
    )


def places_of(extra: list[Removal], plugin: str | None) -> list[str]:
    """Each place that registers the hook: the settings files, then the plugin."""
    places = [where for where, _ in extra]
    return [*places, plugin] if plugin else places


def correction_hook_rows(look: Look) -> tuple[Row, ...]:
    """A row when the correction hook is registered in more than one place for this
    repository; none otherwise."""
    extra, plugin = registered(look)
    places = places_of(extra, plugin)
    if len(places) <= 1:
        return ()
    count = len(places)
    named = ", ".join(places)
    return (
        Row(
            name="correction hook",
            need=PROJECT,
            found=False,
            detail=f"registered {count} times for this repository: {named}",
            used_for=(
                "the correction queue: one call of the Jev model and at most one entry for "
                "each message of the owner"
            ),
            without_it=fixed(extra, plugin),
        ),
    )
