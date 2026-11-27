"""One-hop requests to boards, with an allowlist of relayed headers."""

from http.cookies import CookieError, SimpleCookie
from urllib.parse import unquote, urlsplit

from lem.addons.peers import rows

HOP = "Lem-Hop"
# The owner reads the relayed page on the Mac of the board that relays it, where his agterm runs:
# the joined board then draws the jump to a task's session, whose act is the relaying board's.
HERE = "Lem-Agterm"
# The most a board reads of a joined board's JSON reply, an error reply too (main, 2026-11-25).
JSON_CAP = 1_000_000
COOKIE = "lem_board"
FORWARDED = (
    "Accept",
    "Turbo-Frame",
    "User-Agent",
    "Last-Event-ID",
    "If-None-Match",
    "If-Modified-Since",
)
RETURNED = frozenset(
    (
        "content-type",
        "cache-control",
        "etag",
        "last-modified",
        "content-security-policy",
        "x-content-type-options",
        "referrer-policy",
        "allow",
        "vary",
        "x-accel-buffering",
    )
)


def location(given: str, peer: str, base: str) -> str | None:
    """A redirect may only stay on the entry board at the peer's path."""
    split = urlsplit(given)
    if split.netloc or split.scheme:
        own = urlsplit(base)
        if (split.scheme, split.netloc) != (own.scheme, own.netloc):
            return None
    path = split.path or "/"
    if unsafe(path):
        return None
    tail = f"?{split.query}" if split.query else ""
    prefix = f"/{peer}"
    if path in ("/", prefix) or path.startswith(f"{prefix}/"):
        return path + tail
    return f"/{peer}{path}{tail}"


def cookie(given: str) -> str | None:
    """Read only the board preference cookie."""
    try:
        jar = SimpleCookie(given)
    except CookieError:
        return None
    found = jar.get(COOKIE)
    if found is None:
        return None
    shown = found.coded_value
    return f"{COOKIE}={shown}"


def outgoing(
    incoming: dict[str, str],
    listed: tuple[rows.Row, ...],
    *,
    here: bool = False,
) -> dict[str, str]:
    """The given read headers, the preference cookie, the hop marker, and the mark of a page
    read on this Mac."""
    passed = {
        key: incoming[key.lower()] for key in FORWARDED if key.lower() in incoming
    }
    found = cookie(incoming.get("cookie", ""))
    if found:
        passed["Cookie"] = found
    spaces = rows.header(listed)
    if spaces:
        passed[rows.SPACES] = spaces
    passed[HOP] = "1"
    if here:
        passed[HERE] = "1"
    return passed


def returned(key: str, text: str, peer: str, base: str) -> str | None:
    """The one value a relayed response may send for this header."""
    lower = key.lower()
    if lower == "location":
        return location(text, peer, base)
    name = text.partition("=")[0].strip()
    if lower == "set-cookie" and name == COOKIE:
        return text
    return text if lower in RETURNED else None


def unsafe(path: str) -> bool:
    """A decoded path cannot leave the peer's namespace."""
    decoded = unquote(path)
    if unsafe_prefix(decoded):
        return True
    parts = decoded.split("/")
    return bool({".", ".."}.intersection(parts))


def unsafe_prefix(decoded: str) -> bool:
    """A local redirect has exactly one leading slash and no backslashes."""
    starts_local = decoded.startswith("/") and not decoded.startswith("//")
    return not starts_local or "\\" in decoded
