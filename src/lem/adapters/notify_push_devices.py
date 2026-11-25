"""`push.json` in Lem's home folder: the devices that turned the board's notifications on, what
each workspace's list of what waits held at the last look, the newest thing that was sent, and
the last push's answers (`push.read_state` and `push.write_state` on `main`).

It is written whole under `push.lock`, by the server's watcher, a device's subscription and
`lem serve push-test` alike, with mode 0600 (a whole write's temporary file has it). A device's
entry holds its endpoint, its keys as the browser gave them, when it was added, its kind in short
(`iPhone · Safari`) and the workspaces it wants, all when it names none.
"""

from contextlib import contextmanager
from typing import TYPE_CHECKING

import msgspec

from lem.kernel import files, locks
from lem.kernel.errors import Refusal
from lem.records.base import Frozen, Moment

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

NAME = "push.json"
LOCK = "push.lock"


class Keys(Frozen, frozen=True, kw_only=True):
    """A subscription's keys, as the browser gives them."""

    p256dh: str = ""
    auth: str = ""


class Device(Frozen, frozen=True, kw_only=True):
    """A device that turned the notifications on."""

    endpoint: str
    keys: Keys = Keys()
    added: Moment
    device: str
    workspaces: tuple[str, ...] | None = None


class Said(Frozen, frozen=True, kw_only=True):
    """What the service worker shows for a push: its title, its line, the page it opens and
    its tag, which a newer push of one tag replaces."""

    title: str
    body: str
    url: str
    tag: str = "lem"
    at: Moment | None = None


class Memory(Frozen, frozen=True, kw_only=True):
    """A workspace's list at the last look: its rows' keys, and when each row that left it
    left, in seconds of the clock."""

    rows: tuple[str, ...] = ()
    gone: dict[str, float] = msgspec.field(default_factory=dict)


class Push(Frozen, frozen=True, kw_only=True):
    """The whole file."""

    devices: tuple[Device, ...] = ()
    seen: dict[str, Memory] = msgspec.field(default_factory=dict)
    latest: Said | None = None
    last: msgspec.Raw | None = None

    def holding(self, kept: tuple[Device, ...]) -> Push:
        """The file with the devices `kept`."""
        return msgspec.structs.replace(self, devices=kept)

    def without(self, endpoint: str) -> tuple[Device, ...]:
        """The devices but the one of `endpoint`."""
        return tuple(one for one in self.devices if one.endpoint != endpoint)


def read(home: Path) -> Push:
    """The file as it reads; empty when it is not there."""
    path = home / NAME
    try:
        return msgspec.json.decode(path.read_bytes(), type=Push)
    except FileNotFoundError:
        return Push()
    except (OSError, msgspec.DecodeError) as error:
        raise Refusal(
            "push-file",
            f"{path} does not read as the board's notifications ({error})",
            f"remove {path}, and turn the notifications on again on each device",
        ) from error


@contextmanager
def changing(home: Path) -> Generator[list[Push]]:
    """The file under its lock, as a list of one, whose last item is written whole at the
    end when it is another file than the one read."""
    with locks.held(home / LOCK):
        before = read(home)
        held = [before]
        yield held
        after = held[-1]
        if after != before:
            files.write_whole(home / NAME, msgspec.json.encode(after))
