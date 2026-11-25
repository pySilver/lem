"""Whether Claude Code loads Lem's installed plugin in a checkout, for the `Harness` port on
Claude Code (`harness_claude`).

It does when Claude Code's list of installed plugins (`plugins/installed_plugins.json`) has
`lem@lem` for the user, or for the checkout, and the settings leave it on: the checkout's local
settings say it first, then its shared ones, then the user's (code.claude.com/docs/en/
settings-reference, `enabledPlugins`, read 2026-11-17); with no word an install is on. Claude
Code's own folder is `CLAUDE_CONFIG_DIR`, else `~/.claude`, of the environment the command
started with. A file that is not there or does not read says nothing.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from collections.abc import Mapping

# The plugin a project installs from Lem's marketplace, by its key in both files.
PLUGIN = "lem@lem"
# The scopes of an install for every project, and of one for one project.
USER_SCOPES = ("user", "managed")
PROJECT_SCOPES = ("project", "local")


class Install(msgspec.Struct, frozen=True, kw_only=True):
    """One install of a plugin: its scope, and the project of a project's install."""

    scope: str | None = None
    project: str | None = msgspec.field(default=None, name="projectPath")

    def counts_for(self, checkout: Path) -> bool:
        """Whether Claude Code loads this install in `checkout`, a resolved path."""
        if self.scope in USER_SCOPES:
            return True
        if self.scope not in PROJECT_SCOPES or self.project is None:
            return False
        return Path(self.project).resolve() == checkout


class Installs(msgspec.Struct, frozen=True, kw_only=True):
    """Claude Code's list of installed plugins, by key."""

    plugins: dict[str, tuple[Install, ...]] = msgspec.field(default_factory=dict)

    def listed_for(self, checkout: Path) -> bool:
        """Whether an install of Lem's plugin counts for `checkout`."""
        here = checkout.resolve()
        installs = self.plugins.get(PLUGIN, ())
        return any(each.counts_for(here) for each in installs)


class Settings(msgspec.Struct, frozen=True, kw_only=True):
    """A settings file of Claude Code, by the one key read here."""

    enabled: dict[str, object] = msgspec.field(
        default_factory=dict, name="enabledPlugins"
    )

    def word(self) -> bool | None:
        """Whether the file turns Lem's plugin on or off; None when it says nothing."""
        said = self.enabled.get(PLUGIN)
        return said if isinstance(said, bool) else None


def claude_home(environ: Mapping[str, str]) -> Path:
    """Claude Code's own folder in `environ`."""
    named = environ.get("CLAUDE_CONFIG_DIR")
    if named:
        return Path(named)
    return Path(environ.get("HOME") or Path.home()) / ".claude"


def decoded[Form](path: Path, form: type[Form]) -> Form | None:
    """The JSON file at `path` as `form`; None when it is not there or does not read."""
    try:
        return msgspec.json.decode(path.read_bytes(), type=form)
    except OSError, msgspec.DecodeError:
        return None


def installed(checkout: Path, environ: Mapping[str, str]) -> bool:
    """Whether Claude Code loads Lem's installed plugin in `checkout`."""
    home = claude_home(environ)
    listed = decoded(home / "plugins" / "installed_plugins.json", Installs)
    if listed is None or not listed.listed_for(checkout):
        return False
    own = checkout / ".claude"
    return turned_on(
        (own / "settings.local.json", own / "settings.json", home / "settings.json")
    )


def turned_on(files: tuple[Path, ...]) -> bool:
    """The first word of `files` on Lem's plugin; on when none says one."""
    found = (decoded(path, Settings) for path in files)
    words = (settings.word() for settings in found if settings is not None)
    return next((word for word in words if word is not None), True)
