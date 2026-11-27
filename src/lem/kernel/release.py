"""The release of this Lem, and whether another release is newer.

A record names the release its task began on. A write of a record of a newer release would drop
the keys this release does not know, so the store refuses it (`release.check` on `main` stops
every command for such a task, a drop too).
"""

import functools
from pathlib import Path

import msgspec

from lem.kernel import paths
from lem.kernel.errors import Fault

MANIFEST = Path(".claude-plugin") / "plugin.json"


class Manifest(msgspec.Struct, kw_only=True):
    """The one key of the plugin's manifest that a release is."""

    version: str


@functools.cache
def running() -> str:
    """This Lem's release: the version of its own plugin files' manifest, read once."""
    return named(paths.root())


def named(root: Path) -> str:
    """The release the manifest of the plugin's files in `root` names now."""
    path = root / MANIFEST
    try:
        return msgspec.json.decode(path.read_bytes(), type=Manifest).version
    except (OSError, msgspec.DecodeError) as error:
        raise Fault(f"{path} names no release: {error}") from error


def numbers(release: str) -> tuple[int, ...]:
    """`1.2.0` as (1, 2, 0); a release of another form is a fault."""
    parts = release.split(".")
    if not all(part.isdigit() for part in parts):
        raise Fault(f"{release!r} is no release: numbers joined by dots, as 1.2.0")
    return tuple(int(part) for part in parts)


def newer(release: str, than: str) -> bool:
    """Whether `release` is newer than `than`."""
    return numbers(release) > numbers(than)
