"""Which listener a request came to, and whether an act of a page may go on there.

The door checked every request already (`board/door.py`), an act's origin too. On the main
listener an act of a page (the owner's acts on a task, the board's notifications, the jump to
a session) is taken only from a page of this board on this Mac: the request comes from the
loopback address, its `Host` is the listener's own with its port, its `Origin` is the board's
own origin, and a `Sec-Fetch-Site` it carries says same-origin (`serve.action_refusal` on
`main`). A page of another site that points a name of its own at this Mac carries that name.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.requests import HTTPConnection

LOOPBACK = ("127.0.0.1", "::1", "::ffff:127.0.0.1")


def at_door(request: HTTPConnection) -> bool:
    """Whether the request came through the tailnet door."""
    door = request.app.state.facts.door
    return door is not None and request.scope["server"][1] == door


def from_here(request: HTTPConnection) -> bool:
    """Whether the request came from a program on this Mac."""
    client = request.client
    return client is not None and client.host in LOOPBACK


def own_hosts(port: int) -> frozenset[str]:
    """The `Host` values of the main listener's own, with its port."""
    return frozenset((f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"))


def page_refusal(request: HTTPConnection) -> str | None:
    """None when the request comes from the board's own page on the main listener, else the
    line of its 403."""
    if not from_here(request):
        return "Only a page on this Mac acts through the board's main address."
    own = own_hosts(request.scope["server"][1])
    hosts = [word.strip().lower() for word in request.headers.getlist("host")]
    if len(hosts) != 1 or hosts[0] not in own:
        return "This address is not the board's own on this Mac."
    named = [word.strip().lower() for word in request.headers.getlist("origin")]
    origins = {f"http://{host}" for host in own}
    if len(named) != 1 or named[0] not in origins:
        return (
            "An act comes only from the board's own page, and this request names "
            "another origin or none."
        )
    fetch = request.headers.getlist("sec-fetch-site")
    if any(word.strip().lower() != "same-origin" for word in fetch):
        return (
            "An act comes only from the board's own page, "
            "and this request comes from another site."
        )
    return None


def act_refusal(request: HTTPConnection) -> str | None:
    """None when an act of a page may go on: through the door, which checked it, or from the
    board's own page on this Mac."""
    if at_door(request):
        return None
    return page_refusal(request)
