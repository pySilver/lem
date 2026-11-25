"""`lem serve push-test`: send one push to every device that turned it on.

    lem serve push-test

Each device that turned the board's notifications on gets one test push, and the outcome is each
push service's answer (201: it took the push); a device the service no longer knows (404, 410)
leaves the list.
"""

import os
from http import HTTPStatus

import click
import msgspec

from lem.adapters.notify_push import PushNotifier
from lem.adapters.notify_push_send import Reply
from lem.kernel import folders


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve push-test`."""


class Tested(msgspec.Struct, frozen=True, kw_only=True):
    """How many devices got a test push, each one's answer, and a line for the owner."""

    devices: int
    replies: tuple[Reply, ...] = msgspec.field(name="results")
    said: str


def run(call: Call) -> Tested:
    """One test push to every device."""
    home = folders.home_for_writing(os.environ)
    replies = PushNotifier(home, os.environ).tested(None)
    took = sum(reply.status == HTTPStatus.CREATED for reply in replies)
    said = (
        f"{len(replies)} devices; the push services took {took}"
        if replies
        else "no device has turned the board's notifications on: open the board on the "
        "device, then turn them on from Waits for you"
    )
    return Tested(devices=len(replies), replies=replies, said=said)


COMMAND = click.Command(
    "push-test",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Send one push to every device that turned it on.",
)
