"""The read of a joined machine's board that comes before the jump to a task's session there
(`jump.py`): the session's agterm id in that Mac's agterm and whether that agterm runs Live
sessions, as `origin.py` on that board answers. The reply must name the session the button
asked for, and is read to `JSON_CAP` at most, an error reply too. Each other answer is a refusal
that names its fix (`peer_said.py`).
"""

from http import HTTPStatus
from urllib.parse import quote

import httpx
import msgspec

from lem.addons.peers import look, peer_said, registry, requests
from lem.addons.peers.origin import Origin, Told
from lem.kernel.errors import Refusal

type Answer = tuple[int, bytes]


def named(peer: str, session: str, body: bytes) -> Origin:
    """The session of a 200 answer, when it is the one asked for; else the refusal."""
    try:
        found = msgspec.json.decode(body, type=Origin)
    except msgspec.DecodeError as error:
        raise peer_said.unreachable(peer, "its answer names no session") from error
    if found.session.upper() != session.upper():
        said = f"it named the session {found.session!r}, not {session}"
        raise peer_said.unreachable(peer, said)
    return found


def told_of(status: int, body: bytes) -> Told | None:
    """The joined board's own word of why it names no session, or None for an answer that
    holds none."""
    if status not in {HTTPStatus.NOT_FOUND, HTTPStatus.CONFLICT}:
        return None
    try:
        return msgspec.json.decode(body, type=Told)
    except msgspec.DecodeError:
        return None


def answered_origin(peer: str, session: str, answer: Answer) -> Origin:
    """The session the joined board named, when it is the one asked for; else the refusal."""
    status, body = answer
    if status == HTTPStatus.OK:
        return named(peer, session, body)
    told = told_of(status, body)
    if told is not None:
        raise peer_said.told_refusal(peer, session, told)
    raise peer_said.status_refusal(peer, status)


async def bounded(answer: httpx.Response) -> bytes:
    """The body of `answer`, read to `JSON_CAP` at most."""
    body = bytearray()
    async for chunk in answer.aiter_bytes():
        body.extend(chunk)
        if len(body) > requests.JSON_CAP:
            raise ValueError("its reply exceeds the board's JSON limit")
    return bytes(body)


async def got(joined: registry.Registry, peer: str, path: str) -> Answer:
    """The joined board's status and reply to a read of `path`."""
    machine = joined.known[peer]
    base = await joined.address(machine.name, machine.port)
    async with (
        joined.client(look.LIST_TIMEOUT) as client,
        client.stream("GET", base + path, headers={requests.HOP: "1"}) as answer,
    ):
        return answer.status_code, await bounded(answer)


def path_of(address: tuple[str, str, str]) -> str:
    """The address of the read on the joined board: `/PEER/WORKSPACE/agterm/SESSION`."""
    peer, workspace, session = address
    space = quote(workspace, safe="")
    named_session = quote(session, safe="")
    return f"/{peer}/{space}/agterm/{named_session}"


async def origin_of(joined: registry.Registry, address: tuple[str, str, str]) -> Origin:
    """Ask the joined board for the task's session in its agterm: a read."""
    peer, session = address[0], address[2]
    try:
        answer = await got(joined, peer, path_of(address))
    except Refusal as refusal:
        raise peer_said.unreachable(peer, refusal.why) from refusal
    except (httpx.HTTPError, ValueError) as error:
        raise peer_said.unreachable(peer, str(error) or type(error).__name__) from error
    return answered_origin(peer, session, answer)
