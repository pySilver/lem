"""What the board says when a joined machine's board does not name the task's session (the read
of `origin_read.py`): a board that does not answer, one that knows no such session, one that
cannot read a task's record (its own repair, passed on), one that refuses the owner's login, one
that fails, and one of a Lem too old to answer. Each refusal names its fix.
"""

from http import HTTPStatus

from lem.addons.peers import agterm_said
from lem.addons.peers.origin import GONE, Told
from lem.kernel.errors import Refusal


def unreachable(peer: str, said: str) -> Refusal:
    """The joined machine's board did not answer the read."""
    return Refusal(
        "peer-unreachable",
        f"the board of {peer} did not answer: {said}",
        f"the owner checks that the board of {peer} answers, with lem serve peers",
    )


def told_refusal(peer: str, session: str, told: Told) -> Refusal:
    """The refusal of the joined board's own word: no such session, or a record it cannot
    read, with that board's repair."""
    if told.code == GONE:
        return agterm_said.gone(peer, session)
    return Refusal(
        "peer-record",
        f"the board of {peer} cannot tell the task's session: {told.why}",
        f"on {peer}, {told.fix}",
    )


def status_refusal(peer: str, status: int) -> Refusal:
    """The refusal of an answer with no word of the joined board's own."""
    if status in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}:
        return Refusal(
            "peer-refused",
            f"the board of {peer} refused the read ({status})",
            f"the owner checks that {peer} and this Mac are on his own Tailscale login",
        )
    if status >= HTTPStatus.INTERNAL_SERVER_ERROR:
        return Refusal(
            "peer-fault",
            f"the board of {peer} failed on the read ({status})",
            f"the owner reads lem.log in Lem's home folder on {peer}",
        )
    return Refusal(
        "peer-old",
        f"the board of {peer} does not tell its agterm's sessions (it answered {status})",
        f"the owner updates Lem on {peer}",
    )
