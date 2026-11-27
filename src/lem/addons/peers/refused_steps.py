"""Which refusal a failed step of the jump to a session of another Mac gets (`attaching.py`, and
the doctor's row of a joined machine): agtermctl's own parser refusing the words is an older
agterm on this Mac; agterm's reply is read for what failed, and on which Mac
(`agterm_said.py`). A session that ends between the list and the attach is gone ("no attachable
session", agterm be92bc63, `ControlServer+RemoteGroup.swift`).
"""

from typing import TYPE_CHECKING

from lem.adapters.agterm_reply import Refused
from lem.addons.peers import agterm_said

if TYPE_CHECKING:
    from lem.kernel.errors import Refusal
    from lem.ports.faults import Unanswered

LISTING = "list the sessions of another Mac"
COMPANIONS = "attach a session of another Mac with its companions"
HERE_OLD = ("too old for group attach", "--companions")
GONE_BETWEEN = "no attachable session"


def of_list(peer: str, host: str, failure: Unanswered) -> Refusal:
    """The refusal of a failed `zmx tree HOST`."""
    if not isinstance(failure, Refused):
        return agterm_said.unknown(peer, failure.said)
    if failure.usage:
        return agterm_said.here_old(LISTING, failure.said)
    return agterm_said.far(peer, host, failure.said, failure.code)


def of_attach(peer: str, host: str, session: str, failure: Unanswered) -> Refusal:
    """The refusal of a failed `zmx attach HOST SESSION --companions`."""
    if not isinstance(failure, Refused):
        return agterm_said.unknown(peer, failure.said)
    words = failure.said.lower()
    if failure.usage or any(word in words for word in HERE_OLD):
        return agterm_said.here_old(COMPANIONS, failure.said)
    if GONE_BETWEEN in words:
        return agterm_said.gone(peer, session)
    return agterm_said.far(peer, host, failure.said, failure.code)
