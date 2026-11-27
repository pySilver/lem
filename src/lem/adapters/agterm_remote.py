"""agterm's sessions of another Mac, through `agtermctl` on this Mac: the open windows and each
one's rows, the far Mac's list over ssh (`zmx tree HOST`), the attach of one session with its
companions (`zmx attach HOST SESSION --companions`), the select of a row in its window, and the
restore mode this launch of agterm runs (agterm's reference, "Remote sessions", be92bc63).

A call agterm refuses is `Refused` (`agterm_reply.py`); an answer that holds no list, no window
or no row id is `Unanswered`. A group attach that kept some rows is no refusal: its reply names
the rows and what failed.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.adapters.agterm_ctl import TOOL, ctl
from lem.adapters.agterm_group_forms import Reply, Windows
from lem.adapters.agterm_remote_forms import Listing, Moded
from lem.adapters.agterm_reply import asked, decoded, refused_by
from lem.adapters.agterm_tree import Node, nodes_of
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from collections.abc import Mapping

    type Environ = Mapping[str, str]

JSON = "--json"
WINDOW = "--window"


def windows(environ: Environ) -> tuple[str, ...]:
    """The ids of this Mac's open agterm windows."""
    printed = asked(environ, "window", "list", JSON, window=False)
    found = decoded(printed, Windows, "window list").found.windows
    return tuple(one.id for one in found if one.open)


def rows(environ: Environ, window: str) -> tuple[Node, ...]:
    """Every session of the window `window`, the ones attached from another Mac among them."""
    return nodes_of(asked(environ, "tree", JSON, WINDOW, window, window=False))


def listed(environ: Environ, host: str) -> tuple[str, ...]:
    """The ids of the sessions the Mac at the ssh destination `host` offers, as it lists them."""
    printed = asked(environ, "zmx", "tree", host, JSON, window=False)
    listing = decoded(printed, Listing, "zmx tree")
    return tuple(one.id for one in listing.found.remote.sessions)


def attach(environ: Environ, host: str, session: str) -> Reply:
    """Attach the session `session` of `host` here with its companions: agterm's reply, done or
    kept in part, which names the parent's row."""
    ran = ctl(environ, "zmx", "attach", host, session, "--companions", JSON)
    try:
        reply = msgspec.json.decode(ran.stdout or "{}", type=Reply)
    except msgspec.DecodeError:
        reply = Reply(ok=False)
    if reply.found is None or reply.found.id is None:
        if ran.returncode:
            raise refused_by(ran)
        raise Unanswered(TOOL, "zmx attach printed no row id")
    return reply


def select(environ: Environ, row: str, window: str | None) -> None:
    """Select the row `row`, in the window `window` when it is known: the owner's own act."""
    placed = (WINDOW, window) if window else ()
    asked(environ, "session", "select", "--target", row, *placed, window=not placed)


def restore_mode(environ: Environ) -> str | None:
    """The restore mode this launch of agterm runs, or None when its answer names none."""
    printed = asked(environ, "restore", "mode", JSON, window=False)
    return decoded(printed, Moded, "restore mode").found.restore.active
