"""The machine's key of the board's notifications and its VAPID tokens (RFC 8292,
https://www.rfc-editor.org/rfc/rfc8292.html), through `py_vapid` (`push.machine_key` and
`push.token` on `main`).

The key pair is `push-key.pem` in Lem's home folder, made at first use under `push.lock` and
never printed; a page gets only the public key, the base64url of its uncompressed point, which
it gives `PushManager.subscribe` as `applicationServerKey`. A token names the push service's
origin (`aud`), ends TOKEN_LIFETIME after it was made (at most 24 hours, section 2) and names
SUBJECT (`sub`), and is used again for TOKEN_REUSE, since Apple asks for no new JWT more often
than once an hour.
"""

import threading
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid
from py_vapid.utils import b64urlencode

from lem.kernel import files, locks
from lem.kernel.errors import Fault

if TYPE_CHECKING:
    from pathlib import Path

KEY = "push-key.pem"
LOCK = "push.lock"
TOKEN_LIFETIME = 43_200
TOKEN_REUSE = 21_600
# The JWT's `sub`: a contact URI, which Apple requires as a `mailto:` or a URL. It names no
# person on purpose, and its domain is the one reserved for examples (RFC 2606): Apple answered
# 403 BadJwtToken to `localhost` or an `.invalid` domain and took example.com (`push.SUBJECT`
# on `main`, measured on 2026-11-20).
SUBJECT = "mailto:lem-board@example.com"


def key_of(home: Path) -> Vapid:
    """The machine's key pair, made at first use."""
    path = home / KEY
    if not path.is_file():
        with locks.held(home / LOCK):
            if not path.is_file():
                made = Vapid()
                made.generate_keys()
                files.write_whole(path, made.private_pem())
    return Vapid.from_file(str(path))


def public_of(key: Vapid) -> str:
    """The public key as a page gives it to `PushManager.subscribe`."""
    public = key.public_key
    if public is None:
        raise Fault("the key of the board's notifications holds no public key")
    point = public.public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    return b64urlencode(point)


def audience(endpoint: str) -> str:
    """The origin of the push service of `endpoint`."""
    parts = urlsplit(endpoint)
    return f"{parts.scheme}://{parts.netloc}"


class Tokens:
    """The header of each push service's token, made again only after TOKEN_REUSE."""

    def __init__(self, key: Vapid) -> None:
        """Keep the key, and no token yet."""
        self.key = key
        self.made: dict[str, tuple[float, str]] = {}
        self.lock = threading.Lock()

    def header(self, endpoint: str, now: float) -> str:
        """The `Authorization` header of a push to `endpoint` at the moment `now`."""
        aud = audience(endpoint)
        with self.lock:
            kept = self.made.get(aud)
            if kept is None or now - kept[0] >= TOKEN_REUSE:
                claims = {"aud": aud, "exp": int(now) + TOKEN_LIFETIME, "sub": SUBJECT}
                kept = (now, self.key.sign(claims)["Authorization"])
                self.made[aud] = kept
            return kept[1]
