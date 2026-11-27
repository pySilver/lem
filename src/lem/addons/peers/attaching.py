"""The steps in this Mac's agterm that show a task's session of a joined machine: select the row
already attached from that session, in whichever open window holds it, else attach it over ssh
with its companions and select the new row (agterm's reference, "Remote sessions": `window
list`, `tree --window`, `zmx tree HOST`, `zmx attach HOST SESSION --companions`).

A row is the session's when its `remoteHost` is the machine's ssh destination and its
`remoteSessionID` the session's id there. agterm writes that id from 0.42.0 on: a row attached
from the machine with no id cannot be told apart, and the steps stop rather than attach the
session twice. The attach takes the id as the far Mac lists it. Each step agterm refuses is a
refusal that names its fix (`agterm_said.py`). Only the owner's click on the board starts them.
"""

from typing import TYPE_CHECKING

from lem.adapters import agterm_remote
from lem.addons.peers import agterm_said, group_said, refused_steps
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lem.adapters.agterm_group_forms import Reply
    from lem.adapters.agterm_tree import Node

    type Environ = Mapping[str, str]

NO_ORIGIN = (
    "tell which session a row attached from another Mac shows (agterm 0.42.0 or newer)"
)


def from_session(row: Node, host: str, session: str) -> bool:
    """Whether `row` was attached from `session` of `host`; refused for a row from `host` that
    names no origin id. agterm prints ids in capitals, and ssh names a host in any case."""
    place = row.remote_host or ""
    if place.lower() != host.lower():
        return False
    if row.remote_session is None:
        said = f"the row {row.id} from {host} names no remoteSessionID"
        raise agterm_said.here_old(NO_ORIGIN, said)
    return row.remote_session.upper() == session.upper()


def row_in(rows: tuple[Node, ...], host: str, session: str) -> str | None:
    """The id of the row of `rows` attached from the session, or None."""
    found = (one.id for one in rows if from_session(one, host, session))
    return next(found, None)


def found_row(
    environ: Environ, peer: str, target: tuple[str, str]
) -> tuple[str, str] | None:
    """The window and the row of this Mac attached from the session `(host, session)`, or
    None."""
    try:
        for window in agterm_remote.windows(environ):
            row = row_in(agterm_remote.rows(environ, window), *target)
            if row is not None:
                return window, row
    except Unanswered as unanswered:
        raise agterm_said.unknown(peer, unanswered.said) from unanswered
    return None


def listed(environ: Environ, peer: str, host: str, session: str) -> str:
    """The session's id as the far Mac lists it; refused when it lists no such session."""
    try:
        offered = agterm_remote.listed(environ, host)
    except Unanswered as failure:
        raise refused_steps.of_list(peer, host, failure) from failure
    wanted = session.upper()
    exact = next((one for one in offered if one.upper() == wanted), None)
    if exact is None:
        raise agterm_said.gone(peer, session)
    return exact


def attach(environ: Environ, peer: str, host: str, session: str) -> Reply:
    """Attach the session with its companions: agterm's reply, done or kept in part."""
    try:
        return agterm_remote.attach(environ, host, session)
    except Unanswered as failure:
        raise refused_steps.of_attach(peer, host, session, failure) from failure


def select(environ: Environ, peer: str, row: str, window: str | None) -> None:
    """Select the row in its window; refused with what agterm said."""
    try:
        agterm_remote.select(environ, row, window)
    except Unanswered as unanswered:
        raise agterm_said.unknown(peer, unanswered.said) from unanswered


def shown(environ: Environ, peer: str, host: str, session: str) -> group_said.Shown:
    """Show the session `session` of `peer` here, by the ssh destination `host`: what the board
    says. A refusal names the step's fix."""
    found = found_row(environ, peer, (host, session))
    if found is not None:
        select(environ, peer, found[1], found[0])
        return group_said.Shown(said=group_said.SWITCHED)
    reply = attach(environ, peer, host, listed(environ, peer, host, session))
    parent = reply.found.id if reply.found else None
    select(environ, peer, parent or "", None)
    return group_said.opened(peer, reply)
