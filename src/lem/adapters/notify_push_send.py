"""One push of the board's notifications to each device (RFC 8030,
https://www.rfc-editor.org/rfc/rfc8030.html), through pywebpush (`push.Pusher` on `main`).

A push is a POST with no body: the service worker asks `GET /api/push/latest` what to say, so
there is nothing to encrypt. It carries `TTL`, `Urgency: high`, which Apple names as the value
that delivers at once, and one `Topic` for every push, so that a service keeps only the newest
it has not delivered. 201 is taken; 404 and 410 mean the subscription is gone (7.3), and the
device leaves the list. What the worker shows is written before the push goes, since it asks as
soon as the push arrives.

`LEM_PUSH=record` writes each push into `push-record.jsonl` in Lem's home folder and answers 201
with no request; `LEM_PUSH=send` sends. Unset, a home folder of Lem that is not the owner's (a
test's, a trial's) records and his own sends, so that no test reaches a push service.
"""

import os
import pwd
from http import HTTPStatus
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

import msgspec

from lem.kernel import paths

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.adapters.notify_push_devices import Device

SWITCH = "LEM_PUSH"
RECORD = "push-record.jsonl"
# How long a push service keeps a push the device has not taken: six hours, a guess; the
# topic, eight characters, which Apple took where nine got 400 BadWebPushTopic (`push.TOPIC`
# on `main`, 2026-11-20); and how long one request may take, a guess.
TTL = 21_600
TOPIC = "lemwaits"
SEND_WAIT = 10.0
# How much of a service's answer is kept.
ANSWER_CHARS = 300
GONE = frozenset((HTTPStatus.NOT_FOUND, HTTPStatus.GONE))


class Reply(msgspec.Struct, frozen=True, kw_only=True, omit_defaults=True):
    """A push service's answer to one push: the device, the service, its status (None when
    no answer came), the start of what it said, and whether the device is gone."""

    device: str
    service: str | None = None
    status: int | None = None
    said: str = ""
    gone: bool = False


def recording(environ: Mapping[str, str]) -> bool:
    """Whether a push is recorded rather than sent."""
    named = environ.get(SWITCH, "")
    if named:
        return named == "record"
    real = pwd.getpwuid(os.getuid()).pw_dir
    return paths.home(environ) != paths.home({"HOME": real})


def recorded(home: Path, endpoint: str, header: str) -> Reply:
    """A push written into the record, with no request."""
    line = {
        "endpoint": endpoint,
        "ttl": TTL,
        "urgency": "high",
        "topic": TOPIC,
        "authorization": header,
    }
    with (home / RECORD).open("ab") as out:
        out.write(msgspec.json.encode(line))
        out.write(b"\n")
    return Reply(device="", status=HTTPStatus.CREATED, said="recorded, not sent")


def sent(endpoint: str, header: str) -> Reply:
    """A push sent, and the service's answer."""
    import pywebpush
    import requests

    headers = {"Urgency": "high", "Topic": TOPIC, "Authorization": header}
    pusher = pywebpush.WebPusher({"endpoint": endpoint})
    try:
        answer = pusher.send(None, headers, ttl=TTL, timeout=SEND_WAIT)
    except requests.RequestException as error:
        return Reply(device="", said=str(error)[:ANSWER_CHARS])
    if isinstance(answer, str):
        return Reply(device="", said=answer[:ANSWER_CHARS])
    status = answer.status_code
    told = answer.text[:ANSWER_CHARS]
    return Reply(device="", status=status, said=told, gone=status in GONE)


def pushed(
    device: Device, header: str, home: Path, environ: Mapping[str, str]
) -> Reply:
    """One push to `device`, recorded or sent, and its answer."""
    endpoint = device.endpoint
    reply = (
        recorded(home, endpoint, header)
        if recording(environ)
        else sent(endpoint, header)
    )
    service = urlsplit(endpoint).hostname
    return msgspec.structs.replace(reply, device=device.device, service=service)
