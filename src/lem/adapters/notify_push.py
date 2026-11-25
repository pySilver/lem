"""The `Notifier` port on Web Push: a wait that began is one push to each device that wants its
workspace (the design's part 4; `push.py` on `main`).

What the worker shows is written into `push.json` first, then each device gets a push with no
body, under a token of its push service that is used again for a while
(`notify_push_key.Tokens`); a device its service no longer knows (404, 410) leaves the list, and
the last push's answers are kept for `GET /api/server` and `lem doctor`. A wait that ended sends
nothing: a push that was sent is not called back, and the worker shows the newest.
"""

import time
from typing import TYPE_CHECKING

import msgspec

from lem.adapters import notify_push_devices as devices
from lem.adapters import notify_push_key as keys
from lem.adapters import notify_push_send as send
from lem.kernel import clock
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

    from lem.ports.notifier import Wait
    from lem.ports.place import Place

type Replies = tuple[send.Reply, ...]


class Last(msgspec.Struct, frozen=True, kw_only=True):
    """The last push's moment and answers."""

    at: object
    replies: Replies = msgspec.field(name="results")


class PushNotifier:
    """Pushes from Lem's home folder `home` to the devices it lists."""

    def __init__(
        self,
        home: Path,
        environ: Mapping[str, str],
        now: Callable[[], float] = time.time,
    ) -> None:
        """Keep the home folder, the environment, the clock, and no token yet."""
        self.home = home
        self.environ = environ
        self.now = now
        self.tokens: keys.Tokens | None = None

    def started(self, wait: Wait) -> None:
        """One push of the wait to each device that wants its workspace."""
        title = wait.task.replace("-", " ").capitalize()
        said = devices.Said(
            title=wait.say,
            body=f"{title} · {wait.workspace}",
            url=wait.url,
            tag=f"lem-{wait.id}",
        )
        self.told(said, (wait.workspace,))

    def ended(self, wait_id: str) -> None:
        """Nothing: a push that was sent is not called back."""

    def told(self, said: devices.Said, workspaces: tuple[str, ...]) -> Replies:
        """One push of `said` to each device that wants one of the workspaces."""
        listed = devices.read(self.home).devices
        wanted = tuple(one for one in listed if wants(one, workspaces))
        return self.delivered(wanted, said)

    def tested(self, endpoint: str | None) -> Replies:
        """A test push to the device of `endpoint`, or to every device with None."""
        listed = devices.read(self.home).devices
        chosen = tuple(one for one in listed if endpoint in {None, one.endpoint})
        if endpoint is not None and not chosen:
            raise Refusal(
                "push-device",
                "this device is not on the list of the board's notifications",
                "turn the notifications off and on again on the device",
            )
        said = devices.Said(
            title="Lem",
            body="A test from the board: notifications reach this device.",
            url="/",
            tag="lem-test",
        )
        return self.delivered(chosen, said)

    def delivered(
        self, chosen: tuple[devices.Device, ...], said: devices.Said
    ) -> Replies:
        """`said` written for the worker, then one push to each device; the gone leave."""
        if not chosen:
            return ()
        moment = clock.now()
        with devices.changing(self.home) as held:
            stamped = msgspec.structs.replace(said, at=moment)
            held.append(msgspec.structs.replace(held[-1], latest=stamped))
        replies = tuple(self.pushed(one) for one in chosen)
        kept(self.home, chosen, replies, moment)
        return replies

    def pushed(self, device: devices.Device) -> send.Reply:
        """One push to `device`, under its service's token."""
        tokens = self.tokens or keys.Tokens(keys.key_of(self.home))
        self.tokens = tokens
        header = tokens.header(device.endpoint, self.now())
        return send.pushed(device, header, self.home, self.environ)


def kept(
    home: Path, chosen: tuple[devices.Device, ...], replies: Replies, moment: object
) -> None:
    """The answers kept as the last push's, and the devices whose service said gone taken
    off the list."""
    gone = gone_of(chosen, replies)
    last = msgspec.to_builtins(Last(at=moment, replies=replies))
    with devices.changing(home) as held:
        before = held[-1]
        left = tuple(one for one in before.devices if one.endpoint not in gone)
        held.append(msgspec.structs.replace(before, devices=left, last=last))


def gone_of(chosen: tuple[devices.Device, ...], replies: Replies) -> frozenset[str]:
    """The endpoints whose service said the device is gone."""
    pairs = zip(chosen, replies, strict=True)
    return frozenset(one.endpoint for one, reply in pairs if reply.gone)


def wants(device: devices.Device, workspaces: tuple[str, ...]) -> bool:
    """Whether the device wants a push of one of the workspaces: all, when it names none."""
    chosen = device.workspaces
    return chosen is None or any(name in chosen for name in workspaces)


def bind(place: Place) -> PushNotifier:
    """The pushes of the place's home folder."""
    return PushNotifier(place.home, place.environ)
