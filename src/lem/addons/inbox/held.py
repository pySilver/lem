"""An open question stays while the session works on the owner's answer."""

from typing import TYPE_CHECKING

import msgspec

from lem.model.owner import held

if TYPE_CHECKING:
    from lem.app.owner.looking import Looked
    from lem.model.owner.looks import Look, Rows


def keys(seen: Looked) -> frozenset[str]:
    """Use the same row keys as the board, including a breaker's number."""
    rows = (restored(look, alone=seen.presence.away) for look in seen.looks)
    return frozenset(row.key for group in rows for row in group)


def restored(look: Look, *, alone: bool) -> Rows:
    """Read the held row as it will be when the live session ends its turn."""
    session = look.session
    if session is None or not session.live or not session.working:
        return ()
    quiet = msgspec.structs.replace(session, working=False)
    ready = msgspec.structs.replace(look, session=quiet)
    return held.hold_rows(ready, alone=alone or look.record.task.night is not None)
