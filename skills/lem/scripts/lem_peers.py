"""The other machines whose boards this machine's server shows under its one address.

    lem serve --join HOST[:PORT]   show the boards of the machine HOST of the tailnet here too, and exit
    lem serve --leave HOST         show them no more, and exit
    lem serve --peers              each machine joined, with whether it answers now, and exit

The owner runs `lem serve --tailscale` on each of his machines and `lem serve --join HOST` one time on
the one he opens from his phone, the entry. The entry's server then lists the other machine's
workspaces beside its own, in `/`, in `/api/workspaces` and in the switcher of each page, as
`HOST/WORKSPACE`, and passes that machine's pages through: a request for `/HOST/...` is fetched from
HOST at the same address, and its answer goes back as it came (`forward`). HOST is the first part of
every address of that machine's own board already, so its pages and links need no change. The joined
machines are `[peers]` in the machine's file (`lem_state`), each name with the port of its tailnet
door; the server reads the table at each look, so a join or a leave holds at once, with no restart.

A peer is reached at `https://HOST.SUFFIX:PORT/`, SUFFIX the tailnet's MagicDNS suffix from `tailscale
status --json`, over the tailnet and with the system's certificates (the tailnet's are public ones).
The request goes out from this Mac, so Tailscale puts the login of this Mac's user on it, and the
peer's door lets in the owner's login as it does for his phone. What a peer learns is that the
owner's login asked for one of its pages. Only GET and HEAD pass, and only the headers a page needs
(FORWARDED): `Accept`, `Turbo-Frame`, `User-Agent` (the native app's is read), `Last-Event-ID`, and of
the cookies only the board's own (`lem_board`, which the browser writes for the entry's origin, so a
peer's page reads the same folds and widths as the entry's). The answer keeps its status, its type,
its caching headers and a `Location`, which stays inside `/HOST/` (`kept_location`). A stream of
server-sent events passes chunk by chunk as it comes, comments too; it ends when the peer ends it, when
the client hangs up (a watch looks every WATCH_SECONDS), when the peer sends nothing for STREAM_SILENCE,
or when the server stops.

Every request to a peer carries `Lem-Hop: 1` (HOP). A server that gets one never forwards a request
and lists no peer, so two machines that joined each other never loop; it draws no agterm button, which
is for the Mac itself; and it reads `Lem-Spaces` (SPACES), the list of workspaces as the entry knows
it, so that the switcher on a peer's page lists every machine as the entry's own pages do.

The list asks each peer's `/api/workspaces` again when its answer is older than LIST_FRESH, in a thread
of its own. A page waits LIST_WAIT at most for that answer, and only while the peer answered at its
last look: a peer that sleeps is shown at once as "not reachable", with when it last answered and its
last known workspaces grayed, and it never slows a page.

Two environment variables are a test's switches, never settings. LEM_SERVE_NAME, read at the
server's start, is the machine's name in every address in place of its name on the tailnet, so that two
servers on one Mac are two machines. LEM_SERVE_PEERS, `NAME=ADDRESS,...`, gives a peer its address: a
whole base URL (`http://127.0.0.1:4621`, plain http on loopback) or a host name that stands for
`NAME.SUFFIX` (with the port of the join).
"""

import contextlib
import http.client
import http.cookies
import json
import os
import re
import socket
import ssl
import threading
import time
from urllib.parse import quote, unquote, urlsplit

import lem_state

# The header on every request to a peer, and its one value: a server that gets it forwards nothing.
HOP = "Lem-Hop"
# The header that carries the workspaces of every machine as the entry knows them, to a peer's page.
SPACES = "Lem-Spaces"
# The test's switches (above): this server's name, and the peers' addresses.
NAME_SWITCH = "LEM_SERVE_NAME"
ADDRESS_SWITCH = "LEM_SERVE_PEERS"
# A peer's list is asked again when it is older than this. A guess, the server's own REFRESH_SECONDS:
# a phone does not need fresher counts, and a page of the peer has its own stream.
LIST_FRESH = 5
# How long a page waits for a peer's list that is asked again. A guess: a tailnet's answer between two
# machines at home takes tens of milliseconds, and a page should not wait much longer than it renders.
LIST_WAIT = 0.6
# How long one look at a peer's list, or `--join`'s question, may take before the peer is not reachable.
LIST_TIMEOUT = 4
# How long a page's request may take to reach a peer, and then to get its answer. Guesses: a tailnet
# connection opens in well under a second when the machine is awake, and a page renders in under one.
CONNECT_TIMEOUT = 4
PAGE_TIMEOUT = 30
# How long a stream from a peer may stay silent before it is taken as gone: three of its pings (every
# 10 s, serve.PING_SECONDS) and a margin.
STREAM_SILENCE = 35
# How often a stream's watch looks whether its client hung up or the server stops.
WATCH_SECONDS = 0.5
# The request headers that pass to a peer, and the answer's headers that pass back.
FORWARDED = (
    "Accept",
    "Turbo-Frame",
    "User-Agent",
    "Last-Event-ID",
    "If-None-Match",
    "If-Modified-Since",
)
RETURNED = (
    "Content-Type",
    "Cache-Control",
    "ETag",
    "Last-Modified",
    "Location",
    "Content-Security-Policy",
    "X-Content-Type-Options",
    "Referrer-Policy",
    "Allow",
    "Vary",
    "X-Accel-Buffering",
)
# The board's one cookie (serve.PREFS_COOKIE), the only cookie that passes either way.
COOKIE = "lem_board"
# Over this size the list of workspaces does not go to a peer's page, whose switcher then lists its own.
# A guess with room: a workspace is about 150 bytes of it, and a server reads a header line of 64 KiB.
SPACES_CAP = 32_000


class PeerError(Exception):
    pass


def label(name: str) -> bool:
    return re.fullmatch(lem_state.PEER_NAME, name) is not None


def peer_name(given: str, suffix: str | None) -> str:
    """A machine's name on the tailnet from what the owner typed: one DNS label, in lower case. A full
    name is cut to its first label when the rest is this tailnet's suffix; of another tailnet it is refused."""
    name = given.strip().lower().rstrip(".")
    if "." in name:
        first, _, rest = name.partition(".")
        if not suffix or rest != suffix.lower().rstrip("."):
            where = (
                f"this tailnet's names end in .{suffix}"
                if suffix
                else "this Mac reads no tailnet now"
            )
            raise PeerError(
                f"{given} is no machine of this tailnet ({where}): give the machine's name, the first part of its address"
            )
        name = first
    if not label(name):
        raise PeerError(
            f"{given!r} is no machine's name on a tailnet: one word of letters, digits and hyphens, as `tailscale status` lists it"
        )
    return name


def parse_join(given: str, suffix: str | None) -> tuple[str, int | None]:
    """`HOST` or `HOST:PORT` of `--join`: the machine's name and its door's port, None when not given."""
    host, colon, port = given.rpartition(":") if ":" in given else (given, "", "")
    if colon and not (port.isdigit() and 0 < int(port) < 65536):
        raise PeerError(
            f"{port!r} in {given} is no port: give one from 1 to 65535, or none for this machine's own door port"
        )
    return peer_name(host, suffix), int(port) if colon else None


def test_name() -> str | None:
    """The machine's name a test gives this server (NAME_SWITCH), or None."""
    given = os.environ.get(NAME_SWITCH, "")
    if not given:
        return None
    if not label(given):
        raise PeerError(
            f"{NAME_SWITCH}={given!r} is no machine's name: one word of lower-case letters, digits and hyphens"
        )
    return given


def test_addresses() -> dict[str, str]:
    """The peers' addresses a test gives (ADDRESS_SWITCH), by name."""
    out = {}
    for part in os.environ.get(ADDRESS_SWITCH, "").split(","):
        name, eq, address = part.strip().partition("=")
        if eq and label(name) and address:
            out[name] = address.rstrip("/")
    return out


def tailnet_facts(status: dict) -> dict:
    """What `tailscale status --json` says that the peers need: the tailnet's suffix and the first label of
    each other machine's name."""
    suffix = str(status.get("MagicDNSSuffix") or "").rstrip(".")
    peers = status.get("Peer") if isinstance(status.get("Peer"), dict) else {}
    names = sorted(
        {
            str(p.get("DNSName") or "").split(".")[0].lower()
            for p in peers.values()
            if isinstance(p, dict) and p.get("DNSName")
        }
        - {""}
    )
    return {"suffix": suffix, "machines": names}


def base_of(name: str, port: int, suffix: str | None) -> str:
    """Where a peer is reached: the test's address when one names it, else `https://NAME.SUFFIX:PORT`."""
    switched = test_addresses().get(name)
    if switched:
        return switched if "://" in switched else f"https://{switched}:{port}"
    if not suffix:
        raise PeerError(
            "this Mac reads no tailnet now (`tailscale status --json` gave no MagicDNS suffix): open Tailscale and connect"
        )
    return f"https://{name}.{suffix}:{port}"


def hopped(headers) -> bool:
    """Whether a request came from another machine's server (HOP): then it is never forwarded."""
    return headers.get(HOP) is not None


def kept_location(location: str, peer: str, base: str) -> str | None:
    """A peer's redirect as an address of the entry: a path under `/PEER/` stays, `/` (the list of the
    workspaces) stays, any other path of the peer goes under `/PEER`; an address of the peer's own origin
    is read as its path; one of another origin is None, and the redirect does not pass."""
    split = urlsplit(location)
    if split.scheme or split.netloc:
        own = urlsplit(base)
        if (split.scheme, split.netloc) != (own.scheme, own.netloc):
            return None
    path = split.path or "/"
    if not path.startswith("/"):
        return None
    query = f"?{split.query}" if split.query else ""
    if path == "/" or path == f"/{peer}" or path.startswith(f"/{peer}/"):
        return path + query
    return f"/{peer}{path}{query}"


def request_headers(incoming, spaces: list | None = None) -> dict:
    """The headers of a request to a peer: the ones a page needs (FORWARDED), the board's own cookie and
    no other, HOP, and the list of the workspaces (SPACES) when it is given and not too long."""
    out = {
        name: incoming.get(name) for name in FORWARDED if incoming.get(name) is not None
    }
    cookie = incoming.get("Cookie")
    if cookie:
        try:
            jar = http.cookies.SimpleCookie(cookie)
        except http.cookies.CookieError:
            jar = {}
        if COOKIE in jar:
            out["Cookie"] = f"{COOKIE}={jar[COOKIE].coded_value}"
    out[HOP] = "1"
    if spaces:
        said = json.dumps(
            [
                {
                    key: row.get(key)
                    for key in (
                        "host",
                        "name",
                        "path",
                        "waits",
                        "building",
                        "checks",
                        "running",
                        "problem",
                        "reachable",
                        "answered",
                        "said",
                    )
                }
                for row in spaces
            ],
            separators=(",", ":"),
        )
        if len(said) <= SPACES_CAP:
            out[SPACES] = said
    return out


def reply_headers(
    headers: list[tuple[str, str]], peer: str, base: str
) -> list[tuple[str, str]]:
    """The headers of a peer's answer that go back (RETURNED), `Location` kept inside `/PEER/`, and of the
    cookies only the board's own."""
    out = []
    for key, value in headers:
        lower = key.lower()
        if lower == "location":
            kept = kept_location(value, peer, base)
            if kept is not None:
                out.append(("Location", kept))
        elif lower == "set-cookie":
            if value.split("=", 1)[0].strip() == COOKIE:
                out.append((key, value))
        elif lower in {name.lower() for name in RETURNED}:
            out.append((key, value))
    return out


def row_of(given: dict, host: str) -> dict | None:
    """One workspace of a peer's list, as the entry shows it: its address built here from its machine and
    its name, never taken from the answer; None when the entry is not a workspace."""
    if (
        not isinstance(given, dict)
        or not isinstance(given.get("name"), str)
        or not given["name"]
    ):
        return None
    row = {
        "host": host,
        "name": given["name"],
        "path": given.get("path") if isinstance(given.get("path"), str) else "",
        "url": f"/{quote(host)}/{quote(given['name'])}/",
    }
    for key in ("waits", "building", "checks", "running"):
        value = given.get(key)
        row[key] = (
            value if isinstance(value, int) and not isinstance(value, bool) else None
        )
    if isinstance(given.get("problem"), str):
        row["problem"] = given["problem"]
    for key, kind in (("reachable", bool), ("said", str)):
        if isinstance(given.get(key), kind):
            row[key] = given[key]
    if isinstance(given.get("answered"), int) and not isinstance(
        given.get("answered"), bool
    ):
        row["answered"] = given["answered"]
    return row


def gray(row: dict, answered: int | None, said: str) -> dict:
    """A workspace of a peer that does not answer: its name and place as last known, no counts."""
    return {
        **row,
        "waits": None,
        "building": None,
        "checks": None,
        "running": None,
        "reachable": False,
        "answered": answered,
        "said": said,
    }


def merged(own: list, me: str, states: list[dict]) -> list:
    """This machine's workspaces, then each peer's in the order of the table: a peer that answers with its
    rows, one that does not with its last known rows grayed (`gray`), or with one row of its machine
    alone when it never answered. A peer of this machine's own name is left out."""
    out = [{**row, "host": me} for row in own]
    for state in states:
        name = state["name"]
        if name == me:
            continue
        rows = [
            r
            for r in (row_of(given, name) for given in state.get("rows") or [])
            if r is not None
        ]
        said = state.get("said") or (
            "no answer yet" if state.get("reachable") is None else ""
        )
        if state.get("reachable"):
            out += rows
        elif rows:
            out += [gray(row, state.get("answered"), said) for row in rows]
        else:
            out.append(
                {
                    "host": name,
                    "name": "",
                    "path": "",
                    "url": "",
                    "waits": None,
                    "building": None,
                    "checks": None,
                    "running": None,
                    "reachable": False,
                    "answered": state.get("answered"),
                    "said": said,
                }
            )
    return out


def spaces_of(header: str | None) -> list:
    """The list of the workspaces an entry sent (SPACES), each row checked and its address built here; none
    when it does not read."""
    if not header:
        return []
    try:
        given = json.loads(header)
    except ValueError:
        return []
    if not isinstance(given, list):
        return []
    out = []
    for each in given:
        host = each.get("host") if isinstance(each, dict) else None
        if not isinstance(host, str) or not label(host):
            continue
        row = row_of(each, host)
        if row is not None:
            out.append(row)
        elif (
            isinstance(each.get("name"), str)
            and not each["name"]
            and each.get("reachable") is False
        ):
            out.append(
                {
                    "host": host,
                    "name": "",
                    "path": "",
                    "url": "",
                    "waits": None,
                    "building": None,
                    "checks": None,
                    "running": None,
                    "reachable": False,
                    "answered": each.get("answered")
                    if isinstance(each.get("answered"), int)
                    else None,
                    "said": each.get("said")
                    if isinstance(each.get("said"), str)
                    else "",
                }
            )
    return out


def with_own(given: list, own: list, me: str) -> list:
    """The list an entry sent, with this machine's rows in it replaced by its own fresh ones, at the place
    of its first; with nothing sent, this machine's rows alone."""
    mine = [{**row, "host": me} for row in own]
    others = [row for row in given if row.get("host") != me]
    at = next(
        (
            sum(1 for row in given[:index] if row.get("host") != me)
            for index, row in enumerate(given)
            if row.get("host") == me
        ),
        len(others),
    )
    return others[:at] + mine + others[at:]


def connect(
    base: str, timeout: float
) -> tuple[http.client.HTTPConnection, socket.socket]:
    """A connection to a peer's base address, open, and its socket. The system's certificates check an
    address of https."""
    split = urlsplit(base)
    if split.scheme not in ("http", "https") or not split.hostname:
        raise PeerError(f"{base} is no address of a peer")
    try:
        if split.scheme == "https":
            conn: http.client.HTTPConnection = http.client.HTTPSConnection(
                split.hostname,
                split.port or 443,
                timeout=timeout,
                context=ssl.create_default_context(),
            )
        else:
            conn = http.client.HTTPConnection(
                split.hostname, split.port or 80, timeout=timeout
            )
        conn.connect()
    except (OSError, http.client.HTTPException) as error:
        raise PeerError(
            f"{split.netloc} does not answer ({getattr(error, 'reason', None) or error})"
        ) from error
    return conn, conn.sock


def ask_json(base: str, path: str, timeout: float = LIST_TIMEOUT):
    """GET a peer's PATH with HOP, read as JSON."""
    conn, _ = connect(base, timeout)
    try:
        conn.request("GET", path, headers={HOP: "1", "Accept": "application/json"})
        reply = conn.getresponse()
        data = reply.read(1_000_000)
    except (OSError, http.client.HTTPException) as error:
        raise PeerError(
            f"{urlsplit(base).netloc} did not answer {path} ({error})"
        ) from error
    finally:
        conn.close()
    if reply.status != 200:
        line = data.decode("utf-8", "replace").strip().splitlines()
        raise PeerError(
            f"{urlsplit(base).netloc} answered {path} with {reply.status}{f': {line[0][:200]}' if line else ''}"
        )
    try:
        return json.loads(data)
    except ValueError as error:
        raise PeerError(
            f"{urlsplit(base).netloc} answered {path} with no JSON: is it a server of Lem?"
        ) from error


class Peer:
    """One machine joined: where it is, and what it last answered."""

    def __init__(self, name: str, port: int) -> None:
        self.name = name
        self.port = port
        self.lock = threading.Lock()
        self.rows: list = []
        self.answered: int | None = None  # epoch ms of its last answer
        self.reachable: bool | None = None  # None: not asked yet
        self.said = ""
        self.looked = float("-inf")  # monotonic time of the last look's end
        self.asking: threading.Event | None = None

    def state(self) -> dict:
        with self.lock:
            return {
                "name": self.name,
                "port": self.port,
                "rows": list(self.rows),
                "answered": self.answered,
                "reachable": self.reachable,
                "said": self.said,
            }

    def failed(self, said: str) -> None:
        with self.lock:
            self.reachable, self.said, self.looked = False, said, time.monotonic()

    def look(self, base) -> None:
        """Ask the peer's list once, and keep its answer or why there was none."""
        try:
            where = base()
            listed = ask_json(where, "/api/workspaces")
            if not isinstance(listed, list):
                raise PeerError(
                    f"{self.name} answered /api/workspaces with no list: is it a server of Lem?"
                )
            other = next(
                (
                    str(row.get("url"))
                    for row in listed
                    if isinstance(row, dict)
                    and isinstance(row.get("url"), str)
                    and not row["url"].startswith(f"/{self.name}/")
                ),
                None,
            )
            if other is not None:
                raise PeerError(
                    f"{self.name} shows its boards under another name ({other}): `lem serve --leave {self.name}` and "
                    f"`lem serve --join` with the name in that address"
                )
        except PeerError as error:
            self.failed(str(error))
            return
        with self.lock:
            self.rows, self.answered, self.reachable, self.said, self.looked = (
                listed,
                int(time.time() * 1000),
                True,
                "",
                time.monotonic(),
            )

    def fresh(self, base) -> bool:
        """Ask the list again, in a thread of its own, when it is older than LIST_FRESH and no question is
        out; say whether this call asked."""
        with self.lock:
            if time.monotonic() - self.looked < LIST_FRESH or (
                self.asking is not None and not self.asking.is_set()
            ):
                return False
            asking = self.asking = threading.Event()

        def run() -> None:
            try:
                self.look(base)
            finally:
                asking.set()

        threading.Thread(target=run, daemon=True, name=f"peer {self.name}").start()
        return True


class Peers:
    """The machines of the table `[peers]`, read at each look, each kept while the table names it."""

    def __init__(self, status) -> None:
        # status(): `tailscale status --json` as a dict, or an exception that says why not
        self.status = status
        self.lock = threading.Lock()
        self.known: dict[str, Peer] = {}
        self.suffix: str | None = None

    def table(self) -> dict[str, int]:
        try:
            return dict(lem_state.machine_table("peers"))
        except lem_state.StateError:
            return {}

    def tailnet_suffix(self) -> str | None:
        """This tailnet's suffix, read once when it reads."""
        if self.suffix is None:
            try:
                self.suffix = tailnet_facts(self.status())["suffix"] or None
            except Exception:  # noqa: BLE001 - no tailnet now: a peer is not reachable, and says why
                return None
        return self.suffix

    def all(self) -> list[Peer]:
        table = self.table()
        with self.lock:
            kept = {}
            for name, port in table.items():
                old = self.known.get(name)
                kept[name] = (
                    old if old is not None and old.port == port else Peer(name, port)
                )
            self.known = kept
            return list(kept.values())

    def get(self, name: str) -> Peer | None:
        return next((peer for peer in self.all() if peer.name == name), None)

    def base(self, peer: Peer) -> str:
        return base_of(
            peer.name,
            peer.port,
            None if peer.name in test_addresses() else self.tailnet_suffix(),
        )

    def states(self, wait: float = LIST_WAIT) -> list[dict]:
        """Each peer's last answer, asked again where it is old; all asked at once, so the wait is one wait."""
        peers = self.all()
        deadline = time.monotonic() + wait
        # only the look that asked waits, and only for a peer that answered at its last look or was never asked
        started = [
            peer for peer in peers if peer.fresh(lambda peer=peer: self.base(peer))
        ]
        for peer in started:
            with peer.lock:
                asking, hoping = peer.asking, peer.reachable is not False
            if hoping and asking is not None:
                asking.wait(max(0.0, deadline - time.monotonic()))
        return [peer.state() for peer in peers]


def probe(base: str) -> dict:
    """What a peer says of itself now (`/api/server`, `/api/workspaces`), for `--join` and `--peers`."""
    try:
        server = ask_json(base, "/api/server")
        listed = ask_json(base, "/api/workspaces")
    except PeerError as error:
        return {"reachable": False, "said": str(error)}
    if not isinstance(server, dict) or not isinstance(listed, list):
        return {"reachable": False, "said": "it answers, and not as a server of Lem"}
    return {
        "reachable": True,
        "host": server.get("host"),
        "version": server.get("version"),
        "workspaces": [row.get("name") for row in listed if isinstance(row, dict)],
    }


def join(given: str, me: str, reserved: tuple[str, ...], own_port: int, status) -> dict:
    """`--join HOST[:PORT]`: check the name, ask the machine once, and write it into `[peers]`. A machine
    that does not answer is joined all the same, since it may sleep; one that answers under another name
    is refused, since its pages would not pass."""
    addresses = test_addresses()
    facts: dict = {}
    trouble = None
    try:
        facts = tailnet_facts(status())
    except Exception as error:  # noqa: BLE001 - a test's address needs no tailnet; otherwise it is said below
        trouble = error
    name, port = parse_join(given, facts.get("suffix"))
    if name == me or name in reserved:
        raise PeerError(
            f"{name} is this machine's own name (or a word of the server's own): join another machine"
        )
    if name not in addresses:
        if trouble is not None:
            raise PeerError(
                f"the tailnet does not read on this Mac ({trouble}): the boards of another machine come over the tailnet"
            )
        if name not in facts["machines"]:
            raise PeerError(
                f"no machine of this tailnet is named {name}: `tailscale status` lists {', '.join(facts['machines']) or 'none'}"
            )
    port = port or own_port
    base = base_of(name, port, facts.get("suffix"))
    found = probe(base)
    if found["reachable"] and found.get("host") != name:
        raise PeerError(
            f"{base} answers as the machine {found.get('host')!r}, not {name}: join it by that name"
        )
    table = {key: value for key, value in Peers(status).table().items() if key != name}
    lem_state.write_machine("peers", {**table, name: port})
    if found["reachable"]:
        said = f"{name} answers ({found.get('version')}): its {len(found['workspaces'])} workspace(s) show on this machine's board, under /{name}/"
    else:
        said = (
            f"{name} is joined, and does not answer now: {found['said']}. It may sleep, or its server may not run (`lem serve --tailscale` "
            f"there opens its door); its workspaces show when it answers"
        )
    return {
        "joined": name,
        "port": port,
        "url": base,
        **{key: found.get(key) for key in ("reachable", "version", "workspaces")},
        "said": said,
        "file": str(lem_state.machine_file()),
        "server": "the running server reads the list at each look: nothing to restart",
    }


def leave(given: str) -> dict:
    """`--leave HOST`: take the machine out of `[peers]`."""
    name = given.strip().lower().rstrip(".").split(".")[0]
    table = Peers(dict).table()
    if name not in table:
        raise PeerError(
            f"{name} is not joined: `lem serve --peers` lists the machines that are"
        )
    rest = {key: value for key, value in table.items() if key != name}
    lem_state.write_machine("peers", rest or None)
    return {"left": name, "peers": sorted(rest), "file": str(lem_state.machine_file())}


def report(status) -> dict:
    """`--peers`: each machine joined, where it is reached, and what it says of itself now."""
    peers = Peers(status)
    out = []
    for peer in peers.all():
        try:
            base = peers.base(peer)
        except PeerError as error:
            out.append(
                {
                    "name": peer.name,
                    "port": peer.port,
                    "url": None,
                    "reachable": False,
                    "said": str(error),
                }
            )
            continue
        out.append({"name": peer.name, "port": peer.port, "url": base, **probe(base)})
    return {"peers": out, "file": str(lem_state.machine_file())}


def forward(
    handler, peer: Peer, base: str, stopping: threading.Event, spaces: list
) -> None:
    """Pass one request of the handler to the peer at the same address, and its answer back: a page, a
    file or a stream. PeerError, before anything was sent, says why the peer was not reached."""
    split = urlsplit(handler.path)
    target = (split.path or "/") + (f"?{split.query}" if split.query else "")
    try:
        conn, raw = connect(base, CONNECT_TIMEOUT)
        raw.settimeout(PAGE_TIMEOUT)
        conn.request(
            handler.command, target, headers=request_headers(handler.headers, spaces)
        )
        reply = conn.getresponse()
        stream = (reply.getheader("Content-Type") or "").startswith("text/event-stream")
        data = b"" if stream or handler.command == "HEAD" else reply.read()
    except PeerError as error:
        peer.failed(str(error))
        raise
    except (OSError, http.client.HTTPException) as error:
        said = f"{peer.name} did not answer {unquote(split.path)} ({error})"
        peer.failed(said)
        with contextlib.suppress(OSError):
            conn.close()
        raise PeerError(said) from error
    try:
        handler.send_response(reply.status)
        for key, value in reply_headers(reply.getheaders(), peer.name, base):
            handler.send_header(key, value)
        if stream:
            handler.send_header("Connection", "close")
            handler.close_connection = True
        else:
            handler.send_header(
                "Content-Length",
                reply.getheader("Content-Length")
                if handler.command == "HEAD" and reply.getheader("Content-Length")
                else str(len(data)),
            )
        handler.end_headers()
        if handler.command == "HEAD":
            return
        if stream:
            pipe(handler, reply, raw, stopping)
        else:
            handler.wfile.write(data)
    except (OSError, ValueError):
        return
    finally:
        with contextlib.suppress(OSError):
            reply.close()
        with contextlib.suppress(OSError):
            conn.close()


def pipe(handler, reply, raw: socket.socket, stopping: threading.Event) -> None:
    """A peer's stream to the client, chunk by chunk as it comes. A watch ends it from beside: when the
    client hung up or the server stops, it shuts the peer's socket, and the read ends."""
    done = threading.Event()

    def watch() -> None:
        while not done.wait(WATCH_SECONDS):
            if stopping.is_set() or handler.hung_up():
                with contextlib.suppress(OSError):
                    # the plain socket's own shutdown: an SSL socket's would drop its TLS state under the reading thread
                    socket.socket.shutdown(raw, socket.SHUT_RDWR)
                return

    threading.Thread(target=watch, daemon=True, name="peer stream watch").start()
    try:
        raw.settimeout(STREAM_SILENCE)
        while True:
            chunk = reply.read1(65536)
            if not chunk:
                return
            handler.wfile.write(chunk)
    except (OSError, ValueError, http.client.HTTPException):
        return
    finally:
        done.set()
