"""`lem version`: the folder of Lem's files, its version and its commit, as JSON.

`root` is the package's `data` folder in an installed app, else the checkout the package is
part of; `version` is the manifest's; `commit` is the file `build-commit` a build wrote, else
git's HEAD when `root` is a checkout, else null. `root` is `lem.kernel.paths.root()`.
"""

import subprocess
from typing import TYPE_CHECKING

import click
import msgspec

from lem.kernel import paths

if TYPE_CHECKING:
    from pathlib import Path


class Manifest(msgspec.Struct, kw_only=True):
    """The one key of `.claude-plugin/plugin.json` that `lem version` reads."""

    version: str | None = None


class Version(msgspec.Struct, frozen=True, kw_only=True):
    """What `lem version` prints."""

    root: str
    version: str | None
    commit: str | None


def commit(folder: Path) -> str | None:
    """The commit a build wrote, else the checkout's HEAD, else None."""
    stamp = paths.PACKAGE / "build-commit"
    if stamp.is_file():
        return stamp.read_text(encoding="utf-8").strip() or None
    if not (folder / ".git").exists():
        return None
    ran = subprocess.run(
        ["git", "-C", str(folder), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return ran.stdout.strip() or None if ran.returncode == 0 else None


def shown() -> None:
    """Print the version as JSON, and end the call with no envelope."""
    folder = paths.root()
    found = Version(
        root=str(folder),
        version=manifest(folder).version,
        commit=commit(folder),
    )
    encoded = msgspec.json.encode(found)
    click.echo(msgspec.json.format(encoded, indent=2))
    raise click.exceptions.Exit(0)


def manifest(folder: Path) -> Manifest:
    """The plugin's manifest in `folder`; one that does not read gives no version."""
    path = folder / ".claude-plugin" / "plugin.json"
    try:
        return msgspec.json.decode(path.read_bytes(), type=Manifest)
    except OSError, msgspec.DecodeError:
        return Manifest()


COMMAND = click.Command(
    "version",
    callback=shown,
    help="Lem's version, the folder of its files and its commit, as JSON.",
)
