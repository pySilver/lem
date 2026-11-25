"""The rows of what reaches the owner's phone: the door of the board server on his tailnet, and
the board's notifications.

The door's state is the machine's `[serve]` settings against the door the running server says it
opened in `serve.json`. The notifications are read from `push.json` in Lem's home folder: the
devices that turned them on and the last push with each push service's answer. The check sends
nothing.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.cli.doctor.board_rows import running
from lem.cli.doctor.machine_rows import settled
from lem.cli.doctor.row import OPTIONAL, Row
from lem.kernel import paths
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look

PUSH = "push.json"
DOOR_USED_FOR = (
    "the board on the owner's phone through his tailnet: his own login only, never the "
    "open internet"
)
PUSH_USED_FOR = (
    "a notification on the owner's phone or computer when something starts to wait for "
    'him; a device turns it on from the board\'s "Waits for you" (an iPhone from the board '
    "added to its Home Screen)"
)
PUSH_LINE = "lem serve push-test"


class Answer(msgspec.Struct, frozen=True, kw_only=True):
    """A device, and the push service's answer to the last push sent to it."""

    device: str | None = None
    status: int | str | None = None

    @property
    def said(self) -> str:
        """The device and its answer."""
        answer = self.status or "no answer"
        return f"{self.device}: {answer}"


class Last(msgspec.Struct, frozen=True, kw_only=True):
    """The last push: when, and each answer."""

    at: str | None = None
    answers: list[Answer] = msgspec.field(default_factory=list, name="results")


class Pushes(msgspec.Struct, frozen=True, kw_only=True):
    """What the check reads of `push.json`: the devices and the last push."""

    devices: list[Answer] = msgspec.field(default_factory=list)
    last: Last | None = None

    @property
    def named(self) -> str:
        """How many devices turned the notifications on, and their names."""
        names = [one.device or "?" for one in self.devices]
        counted = "device" if len(names) == 1 else "devices"
        listed = ", ".join(names)
        return f"{len(names)} {counted} ({listed})"


def door_row(look: Look) -> Row:
    """The door: off, on in the settings and open, or on and not opened by the server that
    runs. Optional: the board opens on this machine without it."""
    serve = settled(look).settings.serve
    if not serve.tailscale:
        return Row(
            name="board door",
            need=OPTIONAL,
            found=False,
            detail="the door is off: serve.tailscale is false on this machine",
            used_for=DOOR_USED_FOR,
            without_it="the board opens on this machine only; `lem serve door on` opens the "
            "door on the tailnet, one time",
            line="lem serve door on",
        )
    facts = running(look)
    opened = facts is not None and facts.door == serve.tailscale_port
    said = (
        "the server that runs opened it" if opened else "no server that runs opened it"
    )
    without = (
        "the phone reaches no board until `lem serve ensure` starts a server with the door, "
        "or `lem serve door off` closes it"
    )
    return Row(
        name="board door",
        need=OPTIONAL,
        found=opened,
        detail=f"the door is on, tailnet port {serve.tailscale_port}; {said}",
        used_for=DOOR_USED_FOR,
        without_it=None if opened else without,
        line="lem serve ensure",
    )


def pushes(look: Look) -> Pushes:
    """What `push.json` holds; nothing when it is not there."""
    path = paths.home(look.environ) / PUSH
    try:
        return msgspec.json.decode(path.read_bytes(), type=Pushes)
    except FileNotFoundError:
        return Pushes()
    except (OSError, msgspec.DecodeError) as error:
        raise Refusal(
            "push-file",
            f"{path} does not read: {error}",
            "no device gets a notification until the file reads",
        ) from error


def went(last: Last | None) -> str:
    """When the last push went, with each push service's answer."""
    if last is None or not last.at:
        return "no push has gone yet"
    said = [one.said for one in last.answers]
    listed = ", ".join(said)
    return f"the last push went at {last.at} ({listed})"


def notifications_row(look: Look) -> Row:
    """The board's notifications on the owner's devices. Optional: the board shows what waits
    without them."""
    found = pushes(look)
    if not found.devices:
        return Row(
            name="board notifications",
            need=OPTIONAL,
            found=False,
            detail="no device has turned them on",
            used_for=PUSH_USED_FOR,
            without_it="the owner learns what waits from the board or a task's session only",
            line=PUSH_LINE,
        )
    last = went(found.last)
    detail = f"{found.named}; {last}"
    return Row(
        name="board notifications",
        need=OPTIONAL,
        found=True,
        detail=detail,
        used_for=PUSH_USED_FOR,
        without_it=None,
        line=PUSH_LINE,
    )
