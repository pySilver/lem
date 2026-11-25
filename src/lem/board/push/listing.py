"""The devices that get the board's notifications: a device's subscription taken or let go, what
`GET /api/server` says of them, and what the worker shows for the newest push (`push.subscribe`,
`push.unsubscribe`, `push.status` and `push.latest` on `main`).

A subscription is the browser's `PushSubscription.toJSON()`, with `workspaces`, a list of names,
for fewer than all: a new endpoint is added and a known one replaced, at most MOST push_file.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.adapters import notify_push_devices as push_file
from lem.adapters.notify_push_endpoint import device_of, refusal
from lem.kernel import clock
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

# How many devices the list keeps. A guess: one person's phones, tablets and computers.
MOST = 20
# What the worker shows when nothing was sent (`skills/lem/assets/sw.js` has the same words).
FIXED = push_file.Said(title="Lem", body="Something waits for you in Lem", url="/")
CODE = "push-device"


class Given(msgspec.Struct, frozen=True, kw_only=True):
    """A device's subscription as its page posts it."""

    endpoint: str
    keys: push_file.Keys = push_file.Keys()
    workspaces: tuple[str, ...] | None = None


class Switched(msgspec.Struct, frozen=True, kw_only=True, omit_defaults=True):
    """A device's notifications turned on or off: the device, whether one was removed, and
    how many devices get them now."""

    on: bool
    device: str | None = None
    removed: bool = False
    devices: int


def subscribed(home: Path, given: Given, agent: str) -> Switched:
    """Keep the device's subscription; refused for an endpoint at no push service."""
    said = refusal(given.endpoint)
    if said is not None:
        raise Refusal(CODE, said, "turn the notifications on from the board's own page")
    entry = push_file.Device(
        endpoint=given.endpoint,
        keys=given.keys,
        added=clock.now(),
        device=device_of(agent),
        workspaces=given.workspaces,
    )
    with push_file.changing(home) as held:
        others = held[-1].without(given.endpoint)
        if len(others) >= MOST:
            raise Refusal(
                CODE,
                f"{MOST} devices get the board's notifications already",
                "turn them off on one device first",
            )
        held.append(held[-1].holding((*others, entry)))
    return Switched(on=True, device=entry.device, devices=len(others) + 1)


def unsubscribed(home: Path, endpoint: str) -> Switched:
    """Let the device of `endpoint` go."""
    with push_file.changing(home) as held:
        before = held[-1]
        left = before.without(endpoint)
        held.append(before.holding(left))
    removed = len(left) != len(before.devices)
    return Switched(on=False, removed=removed, devices=len(left))


class Shown(msgspec.Struct, frozen=True, kw_only=True, omit_defaults=True):
    """What `GET /api/server` says of the notifications: each device's kind, when it was
    added and the workspaces it wants (never its endpoint), the last push, and a problem."""

    devices: tuple[push_file.Device, ...] = ()
    last: dict[str, object] | None = None
    problem: str | None = None


def status_of(home: Path) -> Shown:
    """The notifications as `GET /api/server` shows them."""
    try:
        found = push_file.read(home)
    except Refusal as refused:
        return Shown(problem=refused.why)
    shown = tuple(
        msgspec.structs.replace(one, endpoint="", keys=push_file.Keys())
        for one in found.devices
    )
    return Shown(devices=shown, last=found.last)


def latest_of(home: Path) -> push_file.Said:
    """What the worker shows for the newest push: the newest that was sent, or FIXED."""
    try:
        found = push_file.read(home).latest
    except Refusal:
        return FIXED
    return found or FIXED
