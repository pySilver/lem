"""Push notifications from the board server to the owner's devices, when something starts to wait for him.

A device turns them on from the board (the `push` controller of `tools/board-kit`, on "Waits for you"
and in a phone's drawer): a tap subscribes it with the browser's Push API under this machine's key,
and the page posts the subscription to `lem serve` (`POST /api/push/subscribe`). The server's watcher
(`Watcher`, a thread of `lem serve`) looks at each workspace's list of what waits for the owner
(`lem_board_model.waits_of`) every LOOK_SECONDS, and when the list gains a row it sends one push to
each device that wants that workspace. The push carries no payload: the board's service worker
(`skills/lem/assets/sw.js`, served at `/sw.js`) asks `GET /api/push/latest` what to say, and shows a
fixed sentence when that fails.

What a push is, and the rules each part follows:

- A push is an HTTP POST with an empty body to the subscription's endpoint, with `TTL`, `Urgency` and
  `Topic` (RFC 8030, sections 5, 5.2, 5.3, 5.4: https://www.rfc-editor.org/rfc/rfc8030.html). TTL is
  TTL_SECONDS; Urgency is `high`, which Apple names as the value that delivers at once; one Topic for
  every push, so that an older push the service still holds is replaced by the newer one. The push
  service answers 201 when it takes the message; 404 or 410 means the subscription is gone (RFC 8030,
  7.3; Apple's table gives 410 for an expired token), and the device is removed from the list.
- With no payload there is nothing to encrypt, so RFC 8291 (aes128gcm, which needs ECDH and AES-GCM
  that Python's standard library does not have) is not used, and `Content-Encoding` is left out, as
  Apple allows for an empty payload
  (https://developer.apple.com/documentation/usernotifications/sending-web-push-notifications-in-web-apps-and-browsers).
  The worker's `push` event then has `event.data` null
  (https://developer.mozilla.org/en-US/docs/Web/API/PushEvent/data).
- VAPID (RFC 8292, https://www.rfc-editor.org/rfc/rfc8292.html): the header `Authorization: vapid
  t=JWT, k=KEY` (sections 2, 3.1, 3.2), the JWT signed with ECDSA on P-256 (ES256), its claims `aud`,
  the origin of the endpoint, `exp`, at most 24 hours ahead (section 2), and `sub`, a contact URI
  (section 2.1), which Apple refuses when it is not a `mailto:` or a URL, or names no real domain
  (`BadJwtToken`; SUBJECT says what was measured). KEY is the
  public key as the base64url of its uncompressed point, the same key the page gives
  `PushManager.subscribe` as `applicationServerKey`
  (https://developer.mozilla.org/en-US/docs/Web/API/PushManager/subscribe). A JWS signature is the
  64 bytes R||S (RFC 7518, 3.4), and openssl writes DER: `der_to_raw` converts it. A token lives
  TOKEN_LIFETIME and is used again for TOKEN_REUSE, since Apple asks for no new JWT more often than
  once an hour.
- Apple's push service takes HTTP/1.1 ("APNs supports both HTTP/1.1 and HTTP/2.0. The default protocol
  is HTTP/1.1", the page above), so `urllib` sends it.
- An endpoint is taken only on https, port 443, at a push service a browser hands out: Apple's
  `*.push.apple.com` (the page above), Google's `fcm.googleapis.com` (Chrome, Edge's Chromium
  builds on Android), Mozilla's `updates.push.services.mozilla.com` and Microsoft's
  `*.notify.windows.com` (https://blog.pushpad.xyz/2022/03/what-are-the-browser-push-services/). So no
  request to the server can make it POST to another address.

`openssl` is the one program outside the standard library that Lem's scripts run for this: ES256 needs
an elliptic-curve key and its signature, which the standard library does not make. It is found by its
absolute path (OPENSSL_PLACES; macOS ships `/usr/bin/openssl`), never on PATH, and a machine without
it is refused with one line. The key pair is the machine's: `push-key.pem` in Lem's home folder
(`lem_state.config()`), mode 0600, made at first use and never printed; the page gets only the public
key (`GET /api/push/key`). The devices, what each workspace's list held at the last look, the newest
thing that was sent and the last push's answers are `push.json` beside it, mode 0600, written whole
under `push.lock`. A device's entry holds its endpoint, its keys as the browser gave them, when it was
added, its kind in short (`iPhone · Safari`) and the workspaces it wants (all, by default).

What is new: the first look at a workspace this file has no memory of records its rows and sends
nothing; after that a row is new when it was not in the list at the last look, unless it left less
than FLAP_SECONDS ago (a row that leaves and comes back is not sent twice). A row is known by its key
(`lem_board_model.waits_of`: `breaker:SLUG:N`, `held:SLUG`, `blocked:SLUG`, `plan:SLUG`, `merge:SLUG`), so a second
breaker of one task is news of its own. The memory is in the file, so a restart of the server (each
update of the plugin replaces it) neither sends again what was sent nor misses what came while it was
down. A demo workspace sends nothing. The owner's away mark (`/lem im-away`) holds nothing back: no
build asks him anything, so the list gains only what cannot go on without him (a breaker, a pull
request to merge), and the phone is how he learns of it away from his computer.

A send is never on a request's path: the watcher runs in its own thread, each request with a timeout
of SEND_TIMEOUT, and a failure is one line in the server's log and `push` in `GET /api/server`. Only
`POST /api/push/test` (one push to the device that asks) and `lem serve --push-test` wait for the
answer, since the answer is what they show.

The environment variable LEM_PUSH=record makes the sender write what it would send into
`push-record.jsonl` in Lem's home folder and answer 201, with no request: every test suite sets it.
"""

import base64
import contextlib
import fcntl
import ipaddress
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lem_state  # noqa: E402  (beside this file)

# Where openssl is, by its absolute path: macOS's own first, then Homebrew's.
OPENSSL_PLACES = ("/usr/bin/openssl", "/opt/homebrew/bin/openssl", "/usr/local/bin/openssl")
# The files in Lem's home folder.
KEY_FILE = "push-key.pem"
STATE_FILE = "push.json"
LOCK_FILE = "push.lock"
RECORD_FILE = "push-record.jsonl"
# The switch of the test suites: the sender records and sends nothing.
SWITCH = ("LEM_PUSH", "record")
# How long a push service keeps a push the device has not taken. A guess: the owner looks at his phone
# within some hours, and an older "something waits" is no news (Apple keeps one up to 30 days).
TTL_SECONDS = 6 * 3600
URGENCY = "high"
# One topic for every push: the service keeps only the newest one it has not delivered (RFC 8030, 5.4:
# at most 32 characters of the URL-safe base64 alphabet). Apple also wants a length that base64 can
# have: "lem-waits", nine characters, got 400 BadWebPushTopic from web.push.apple.com on the owner's
# iPhone, and these eight got 201 (2026-11-20). That the length is the cause is an inference from the
# two answers, not a sentence of Apple's page.
TOPIC = "lemwaits"
# How long one request to a push service may take. A guess: a push service answers in well under a second.
SEND_TIMEOUT = 10
# A token's life (RFC 8292: at most 24 hours) and how long it is used again (Apple: no new JWT more
# often than once an hour). Picks inside both bounds.
TOKEN_LIFETIME = 12 * 3600
TOKEN_REUSE = 6 * 3600
# The JWT's `sub`: a contact URI, which Apple requires as a `mailto:` or a URL. It names no person on
# purpose, so the push services get no address of the owner, and its domain is example.com, the one
# reserved for examples (RFC 2606): Apple answered 403 BadJwtToken to the same token with `localhost`
# or an `.invalid` domain in it, and took it with example.com (2026-11-20, a request to an unknown
# device token, which then failed only on the token: 400 BadWebPushToken).
SUBJECT = "mailto:lem-board@example.com"
# A row that leaves the list and comes back within this time is not sent again. A guess: a task that
# moves from one state that waits to another in a few minutes is one thing for the owner.
FLAP_SECONDS = 300
# How often the watcher looks at each workspace's list. A guess: a phone needs no fresher news, and the
# model is read again only where a file changed (`lem_board_model.Reader`).
LOOK_SECONDS = 5
# How many devices the list keeps. A guess: one person's phones, tablets and computers.
MAX_DEVICES = 20
# What a device posts, at most.
MAX_BODY = 4096
# What the worker shows when it learns nothing more (sw.js has the same words).
FIXED = {"title": "Lem", "body": "Something waits for you in Lem", "url": "/"}
# The push services a browser hands out an endpoint of: exact hosts, and domains whose subdomains are.
PUSH_HOSTS = ("fcm.googleapis.com", "updates.push.services.mozilla.com")
PUSH_DOMAINS = (".push.apple.com", ".notify.windows.com")


class PushError(Exception):
    pass


# ---- the key and the token ----

def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def unb64url(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def der_to_raw(der: bytes) -> bytes:
    """An ECDSA signature on P-256 as openssl writes it (DER: a SEQUENCE of the INTEGERs r and s) as the
    64 bytes R||S a JWS carries (RFC 7518, 3.4), each number as 32 bytes, big-endian, padded on the left."""
    if len(der) < 8 or der[0] != 0x30 or der[1] != len(der) - 2:
        raise PushError("openssl's signature is no DER sequence of two integers")
    at, parts = 2, []
    for _ in range(2):
        if at + 2 > len(der) or der[at] != 0x02:
            raise PushError("openssl's signature is no DER sequence of two integers")
        size = der[at + 1]
        value = der[at + 2:at + 2 + size]
        if len(value) != size:
            raise PushError("openssl's signature is cut short")
        value = value.lstrip(b"\0")
        if len(value) > 32:
            raise PushError("openssl's signature has a number longer than P-256's")
        parts.append(value.rjust(32, b"\0"))
        at += 2 + size
    if at != len(der):
        raise PushError("openssl's signature has bytes after its two integers")
    return parts[0] + parts[1]


def raw_to_der(raw: bytes) -> bytes:
    """The 64 bytes R||S as DER, the form `openssl dgst -verify` reads: the way back of `der_to_raw`."""
    if len(raw) != 64:
        raise PushError("a P-256 signature is 64 bytes")

    def integer(value: bytes) -> bytes:
        value = value.lstrip(b"\0") or b"\0"
        if value[0] & 0x80:
            value = b"\0" + value
        return b"\x02" + bytes([len(value)]) + value

    body = integer(raw[:32]) + integer(raw[32:])
    return b"\x30" + bytes([len(body)]) + body


def openssl() -> str:
    """openssl by its absolute path, or a refusal that names the fix."""
    found = next((place for place in OPENSSL_PLACES if os.path.isfile(place) and os.access(place, os.X_OK)), None)
    if found is None:
        raise PushError(f"the board's notifications sign with openssl (ES256), and this machine has none at {', '.join(OPENSSL_PLACES)}: "
                        "install it (`brew install openssl@3`), then turn notifications on again")
    return found


def run_openssl(args: list[str], data: bytes | None = None) -> bytes:
    tool = openssl()
    try:
        ran = subprocess.run([tool, *args], input=data, capture_output=True, check=False, timeout=SEND_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise PushError(f"`openssl {args[0]}` did not run ({error})") from error
    if ran.returncode != 0:
        raise PushError(f"`openssl {args[0]}` failed: {ran.stderr.decode('utf-8', 'replace').strip() or f'exit {ran.returncode}'}")
    return ran.stdout


def home() -> Path:
    return lem_state.config()


def key_path() -> Path:
    return home() / KEY_FILE


# The public key of each key file, by its path and its change time: openssl is asked once.
_public: dict[tuple, str] = {}
_key_lock = threading.Lock()


def make_key(path: Path) -> None:
    """A new P-256 key pair in PATH, mode 0600 from its first byte: openssl writes into a file
    `mkstemp` made, which is renamed over PATH."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    os.close(handle)
    try:
        run_openssl(["ecparam", "-name", "prime256v1", "-genkey", "-noout", "-out", temporary])
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def public_key_of(path: Path) -> str:
    """The public key of the key file PATH as the base64url of its uncompressed point (65 bytes, 0x04 first)."""
    der = run_openssl(["ec", "-in", str(path), "-pubout", "-outform", "DER"])
    # a P-256 SubjectPublicKeyInfo is 91 bytes, and its last 65 are the point
    point = der[-65:]
    if len(der) != 91 or point[0] != 0x04:
        raise PushError(f"{path} holds no P-256 key: delete it, and the next turn-on makes a new one (each device then turns notifications on again)")
    return b64url(point)


def machine_key() -> tuple[Path, str]:
    """The machine's key file and its public key, the pair made at first use."""
    path = key_path()
    with _key_lock:
        if not path.is_file():
            with held():
                if not path.is_file():
                    make_key(path)
        stamp = (str(path), path.stat().st_mtime_ns)
        if stamp not in _public:
            _public[stamp] = public_key_of(path)
        return path, _public[stamp]


def sign(path: Path, data: bytes) -> bytes:
    """DATA signed with the key file PATH, ES256, as the 64 bytes a JWS carries."""
    return der_to_raw(run_openssl(["dgst", "-sha256", "-sign", str(path)], data))


def audience(endpoint: str) -> str:
    """The origin of an endpoint, the JWT's `aud` (RFC 8292, 2)."""
    parts = urlsplit(endpoint)
    return f"{parts.scheme}://{parts.netloc.lower()}"


def token(aud: str, now: float, path: Path, subject: str = SUBJECT, lifetime: int = TOKEN_LIFETIME) -> str:
    """A VAPID JWT for one push service, signed with the key file PATH."""
    head = b64url(json.dumps({"typ": "JWT", "alg": "ES256"}, separators=(",", ":")).encode("utf-8"))
    claims = b64url(json.dumps({"aud": aud, "exp": int(now) + lifetime, "sub": subject}, separators=(",", ":")).encode("utf-8"))
    signed = f"{head}.{claims}"
    return f"{signed}.{b64url(sign(path, signed.encode('ascii')))}"


def claims_of(jwt: str) -> dict:
    """The claims of a JWT, unchecked: what a test and the record read."""
    return json.loads(unb64url(jwt.split(".")[1]))


# ---- the endpoint ----

def refusal(endpoint) -> str | None:
    """Whether a device's endpoint is taken: None when it is, else the line that says why not. Only
    https, on its usual port, at a push service a browser hands out (PUSH_HOSTS, PUSH_DOMAINS)."""
    if not isinstance(endpoint, str) or not endpoint or len(endpoint) > 2048:
        return "The subscription has no endpoint of at most 2048 characters."
    try:
        parts = urlsplit(endpoint)
        port = parts.port
    except ValueError:
        return "The subscription's endpoint is no address."
    host = (parts.hostname or "").lower()
    if parts.scheme != "https" or parts.username or parts.password or port not in (None, 443):
        return "The subscription's endpoint is not https on its usual port, as every push service's is."
    with contextlib.suppress(ValueError):
        ipaddress.ip_address(host)
        return "The subscription's endpoint is an IP address, and a push service has a name."
    if host not in PUSH_HOSTS and not any(host.endswith(domain) and len(host) > len(domain) for domain in PUSH_DOMAINS):
        return (f"{host} is no push service a browser uses (Apple's *.push.apple.com, Google's fcm.googleapis.com, "
                "Mozilla's updates.push.services.mozilla.com, Microsoft's *.notify.windows.com).")
    return None


def device_of(agent: str) -> str:
    """A browser's user agent in short: the device and the browser, `iPhone · Safari`."""
    agent = agent or ""
    device = next((name for pattern, name in ((r"iPhone", "iPhone"), (r"iPad", "iPad"), (r"Android", "Android"), (r"Macintosh|Mac OS X", "Mac"),
                                              (r"Windows", "Windows"), (r"Linux|X11", "Linux")) if re.search(pattern, agent)), "a device")
    browser = next((name for pattern, name in ((r"Edg/", "Edge"), (r"Firefox/|FxiOS/", "Firefox"), (r"Chrome/|CriOS/", "Chrome"),
                                               (r"Safari/|AppleWebKit/", "Safari")) if re.search(pattern, agent)), "a browser")
    return f"{device} · {browser}"


# ---- the file ----

_file_lock = threading.Lock()


@contextlib.contextmanager
def held():
    """Hold `push.lock`: one writer of `push.json` at a time, the server's threads and `lem serve --push-test` alike."""
    folder = home()
    folder.mkdir(parents=True, exist_ok=True)
    with _file_lock, (folder / LOCK_FILE).open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def empty() -> dict:
    return {"devices": [], "seen": {}, "latest": None, "last": None}


def read_state() -> dict:
    """`push.json` as it reads; empty when it is not there. A file that does not read is refused with the fix."""
    file = home() / STATE_FILE
    try:
        text = file.read_text(encoding="utf-8")
    except FileNotFoundError:
        return empty()
    except OSError as error:
        raise PushError(f"{file} cannot be read ({error.strerror})") from error
    try:
        state = json.loads(text)
    except ValueError as error:
        raise PushError(f"{file} does not read as JSON ({error}): delete it, and turn notifications on again on each device") from error
    if not isinstance(state, dict) or not isinstance(state.get("devices", []), list) or not isinstance(state.get("seen", {}), dict):
        raise PushError(f"{file} is not the shape Lem writes: delete it, and turn notifications on again on each device")
    return {**empty(), **state}


def write_state(state: dict) -> None:
    """Write `push.json` whole, mode 0600: a temporary file beside it, then a rename over it."""
    file = home() / STATE_FILE
    file.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=file.parent, prefix=f".{file.name}.", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            out.write(json.dumps(state, indent=2) + "\n")
        os.replace(temporary, file)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def stamp(seconds: float | None = None) -> str:
    return datetime.fromtimestamp(time.time() if seconds is None else seconds, timezone.utc).isoformat(timespec="seconds")


def subscribe(given, agent: str) -> dict:
    """Keep a device's subscription (the browser's `PushSubscription.toJSON()`, and `workspaces`, a list
    of names, for fewer than all): a new endpoint is added, a known one is replaced."""
    if not isinstance(given, dict):
        raise PushError("The request carries no subscription: a JSON object with its endpoint.")
    endpoint = given.get("endpoint")
    said = refusal(endpoint)
    if said:
        raise PushError(said)
    keys = given.get("keys") if isinstance(given.get("keys"), dict) else {}
    keys = {name: value for name, value in keys.items() if name in ("p256dh", "auth") and isinstance(value, str) and len(value) <= 200}
    wanted = given.get("workspaces")
    if wanted is not None and not (isinstance(wanted, list) and all(isinstance(name, str) for name in wanted)):
        raise PushError("`workspaces` is a list of the workspaces' names, or absent for all of them.")
    entry = {"endpoint": endpoint, "keys": keys, "added": stamp(), "device": device_of(agent), "workspaces": wanted}
    with held():
        state = read_state()
        others = [d for d in state["devices"] if d.get("endpoint") != endpoint]
        if len(others) >= MAX_DEVICES:
            raise PushError(f"{MAX_DEVICES} devices get the board's notifications already: turn them off on one first.")
        state["devices"] = [*others, entry]
        write_state(state)
    return {"on": True, "device": entry["device"], "devices": len(state["devices"])}


def unsubscribe(endpoint) -> dict:
    with held():
        state = read_state()
        kept = [d for d in state["devices"] if d.get("endpoint") != endpoint]
        gone = len(kept) != len(state["devices"])
        if gone:
            state["devices"] = kept
            write_state(state)
    return {"on": False, "removed": gone, "devices": len(kept)}


def status() -> dict:
    """What `GET /api/server` and `lem doctor` say of the notifications: the devices (no endpoint), the last push and its answers."""
    try:
        state = read_state()
    except PushError as error:
        return {"devices": [], "last": None, "problem": str(error)}
    return {"devices": [{"device": d.get("device"), "added": d.get("added"), "workspaces": d.get("workspaces")} for d in state["devices"]],
            "last": state.get("last"), "key": key_path().is_file(), "problem": WATCH_PROBLEM.get("said")}


def latest() -> dict:
    """What the worker shows for the newest push: the newest thing that was sent, or the fixed sentence."""
    try:
        found = read_state().get("latest")
    except PushError:
        found = None
    return {**FIXED, **found} if isinstance(found, dict) else dict(FIXED)


# ---- the send ----

def post(endpoint: str, headers: dict) -> tuple[int | None, str]:
    """One push, an empty POST, and the push service's status and the start of its answer; None and why
    when no answer came. With LEM_PUSH=record, a line in `push-record.jsonl` and 201, with no request."""
    if os.environ.get(SWITCH[0]) == SWITCH[1]:
        auth = headers.get("Authorization", "")
        jwt = re.search(r"t=([^,\s]+)", auth)
        line = {"at": stamp(), "endpoint": endpoint, "TTL": headers.get("TTL"), "Urgency": headers.get("Urgency"), "Topic": headers.get("Topic"),
                "claims": claims_of(jwt[1]) if jwt else None}
        with (home() / RECORD_FILE).open("a", encoding="utf-8") as out:
            out.write(json.dumps(line) + "\n")
        return 201, "recorded, not sent (LEM_PUSH=record)"
    request = urllib.request.Request(endpoint, data=b"", method="POST", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=SEND_TIMEOUT) as reply:
            return reply.status, reply.read(300).decode("utf-8", "replace").strip()
    except urllib.error.HTTPError as error:
        return error.code, error.read(300).decode("utf-8", "replace").strip()
    except (urllib.error.URLError, OSError, ValueError) as error:
        return None, str(getattr(error, "reason", error))


class Pusher:
    """Sends a push to devices, with a token for each push service used again for TOKEN_REUSE; removes a
    device whose push service says it is gone (404, 410) and records the last push's answers."""

    def __init__(self, send=post, now=time.time) -> None:
        self.send_one = send
        self.now = now
        self.tokens: dict[str, tuple[float, str]] = {}
        self.lock = threading.Lock()

    def token(self, aud: str, path: Path) -> str:
        with self.lock:
            made = self.tokens.get(aud)
            if made is None or self.now() - made[0] >= TOKEN_REUSE:
                made = (self.now(), token(aud, self.now(), path))
                self.tokens[aud] = made
            return made[1]

    def send(self, devices: list[dict], said: dict | None = None) -> list[dict]:
        """One push to each device; SAID, what the worker then shows, is written first, since the
        worker asks for it as soon as the push arrives."""
        if not devices:
            return []
        if said is not None:
            with held():
                state = read_state()
                state["latest"] = {**said, "at": stamp(self.now())}
                write_state(state)
        path, public = machine_key()
        results = []
        for device in devices:
            endpoint = device.get("endpoint")
            refused = refusal(endpoint)
            if refused:
                results.append({"device": device.get("device"), "status": None, "said": refused, "gone": False})
                continue
            headers = {"TTL": str(TTL_SECONDS), "Urgency": URGENCY, "Topic": TOPIC, "Content-Length": "0",
                       "Authorization": f"vapid t={self.token(audience(endpoint), path)}, k={public}"}
            code, answer = self.send_one(endpoint, headers)
            results.append({"device": device.get("device"), "service": urlsplit(endpoint).hostname, "status": code, "said": answer[:300],
                            "gone": code in (404, 410), "endpoint": endpoint})
        gone = {r["endpoint"] for r in results if r.get("gone")}
        with held():
            state = read_state()
            if gone:
                state["devices"] = [d for d in state["devices"] if d.get("endpoint") not in gone]
            state["last"] = {"at": stamp(self.now()), "results": [{k: v for k, v in r.items() if k != "endpoint"} for r in results]}
            write_state(state)
        return [{k: v for k, v in r.items() if k != "endpoint"} for r in results]


def send_all(pusher: Pusher | None = None) -> list[dict]:
    """One push to every device, with a sentence that says it is a test: `lem serve --push-test`."""
    devices = read_state()["devices"]
    return (pusher or Pusher()).send(devices, {"title": "Lem", "body": "A test from lem serve: notifications reach this device.", "url": "/", "tag": "lem-test"})


def send_test(endpoint, pusher: Pusher | None = None) -> dict:
    """One push to the one device that asks for it from the board (`POST /api/push/test`)."""
    device = next((d for d in read_state()["devices"] if d.get("endpoint") == endpoint), None)
    if device is None:
        raise PushError("This device is not on the list: turn notifications off and on again.")
    said = {"title": "Lem", "body": "A test from the board: notifications reach this device.", "url": "/", "tag": "lem-test"}
    return (pusher or Pusher()).send([device], said)[0]


# ---- what is new, and the watcher ----

def gained(memory: dict | None, rows: list[str], now: float, flap: float = FLAP_SECONDS) -> tuple[list[str], dict]:
    """The rows of a workspace's list that are news, and the memory to keep, from the memory of the last
    look (None when there is none: everything is recorded and nothing is news). A row is news when the
    last look did not have it, unless it left less than FLAP seconds ago."""
    if not isinstance(memory, dict):
        return [], {"rows": sorted(set(rows)), "gone": {}}
    before = set(memory.get("rows") or [])
    gone = {key: at for key, at in (memory.get("gone") or {}).items() if isinstance(at, (int, float))}
    now_rows = set(rows)
    news = [key for key in dict.fromkeys(rows) if key not in before and not (key in gone and now - gone[key] < flap)]
    for key in before - now_rows:
        gone[key] = now
    gone = {key: at for key, at in gone.items() if key not in now_rows and now - at < flap}
    return news, {"rows": sorted(now_rows), "gone": gone}


# What the watcher last failed at, for `status()`; empty while it goes well.
WATCH_PROBLEM: dict = {}


def wants(device: dict, workspace: str) -> bool:
    chosen = device.get("workspaces")
    return chosen is None or workspace in chosen


class Watcher:
    """The thread of `lem serve` that sends a push when a workspace's list of what waits gains a row.
    `spaces()` gives each workspace as (name, path, a function that reads its model); `host` is the
    machine's name in the board's addresses."""

    def __init__(self, spaces, host: str, pusher: Pusher | None = None, log=None, now=time.time) -> None:
        self.spaces = spaces
        self.host = host
        self.pusher = pusher or Pusher(now=now)
        self.log = log or (lambda line: sys.stderr.write(f"serve.py: {line}\n"))
        self.now = now

    def say(self, problem: str | None) -> None:
        """One line in the log for each new problem, and none while it stays the same."""
        if problem and WATCH_PROBLEM.get("said") != problem:
            self.log(f"the board's notifications: {problem}")
        if problem:
            WATCH_PROBLEM.update(said=problem, at=stamp(self.now()))
        else:
            WATCH_PROBLEM.clear()

    def look(self) -> list[dict]:
        """One look at every workspace: the memory updated, and one push for the news to each device that
        wants its workspace. Returns what was sent."""
        import lem_board_model as bm  # here: a server that never looks loads no model for it

        now = self.now()
        # the models first, outside the file's lock: a subscription that comes meanwhile does not wait for them
        looked = []
        for name, path, model_of in self.spaces():
            try:
                model = model_of()
            except Exception as error:  # noqa: BLE001 - a workspace that does not read sends nothing, and the others still do
                self.log(f"the board's notifications skip {name}: {error}")
                continue
            if not model.meta.get("demo"):
                looked.append((name, path, model, bm.waits_of(model)))
        news = []
        with held():
            state = read_state()
            seen = state["seen"]
            changed = False
            for name, path, model, rows in looked:
                fresh, memory = gained(seen.get(path), [r["key"] for r in rows], now)
                if memory != seen.get(path):
                    seen[path] = memory
                    changed = True
                if fresh:
                    news += [(name, r) for r in rows if r["key"] in fresh]
            if changed:
                write_state(state)
            devices = state["devices"]
        if not news:
            return []
        name, row = news[0]
        say = bm.wait_say(row)
        t = row["t"]
        more = f" · and {len(news) - 1} more" if len(news) > 1 else ""
        tab = "" if say["to"] == "overview" else f"/{quote(say['to'], safe='')}"
        said = {"title": say["verb"], "body": f"{t.title} · {name}{more}", "url": f"/{quote(self.host)}/{quote(name)}/tasks/{quote(t.slug, safe='')}{tab}",
                "tag": f"lem-{row['key']}"}
        named = {space for space, _ in news}
        to = [d for d in devices if any(wants(d, space) for space in named)]
        sent = self.pusher.send(to, said)
        bad = [r for r in sent if r["status"] != 201]
        for r in bad:
            self.log(f"a push to {r['device']} got {r['status'] or 'no answer'}: {r['said'][:160]}{' (removed: the push service no longer knows it)' if r['gone'] else ''}")
        return sent

    def run(self, stopping: threading.Event) -> None:
        while not stopping.wait(LOOK_SECONDS):
            try:
                self.look()
            except PushError as error:
                self.say(str(error))
            except Exception as error:  # noqa: BLE001 - the watcher never stops the server; it says why and looks again
                self.say(repr(error))
            else:
                self.say(None)
