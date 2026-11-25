"""Where Lem's own files are: the plugin's files the app reads, and Lem's home folder.

An installed app holds the plugin's files in its package, under `lem/data`, at the names they
have in Lem's repository (pyproject.toml), and reads them there, never from the plugin Claude
Code loaded: the texts an agent reads are the texts of the `lem` it runs. A checkout (an
editable install) has no such folder, and its root is the checkout itself.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from lem.kernel.errors import Fault, Refusal

if TYPE_CHECKING:
    from collections.abc import Mapping

# This package's parent: src/lem of a checkout, or lem in an installed app's site-packages.
PACKAGE = Path(__file__).resolve().parents[1]


def root(package: Path = PACKAGE) -> Path:
    """The folder of the plugin's files: `lem/data` in an installed app, else the checkout
    that holds the skill `lem`."""
    installed = package / "data"
    if installed.is_dir():
        return installed
    checkout = package.parents[1]
    if (checkout / "skills" / "lem" / "SKILL.md").is_file():
        return checkout
    raise Fault(
        f"Lem's files are neither in {installed}, as in an installed Lem, nor in {checkout}, "
        "as in a checkout of Lem's repository: the owner installs Lem again"
    )


def home(environ: Mapping[str, str]) -> Path:
    """Lem's home folder: `$XDG_CONFIG_HOME/lem` when that is set, else `~/.config/lem`.
    Nothing here makes it."""
    named = environ.get("XDG_CONFIG_HOME", "")
    if not named:
        user = environ.get("HOME") or Path.home()
        return Path(user) / ".config" / "lem"
    if not Path(named).is_absolute():
        raise Refusal(
            "config-home",
            f"XDG_CONFIG_HOME is {named!r}, a relative path, which each folder would read "
            "as another place",
            "set XDG_CONFIG_HOME to an absolute path, or unset it for ~/.config",
        )
    return Path(named) / "lem"
