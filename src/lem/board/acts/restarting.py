"""A fresh session beside the one the guard stopped, on the owner's "Open a session" while the stop
stands: `lem session open SLUG --why stopped`, after the guard's one more look, which may open
nothing and say why (`serve.act_session` and `NOT_OPENED` on `main`).
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.app.sessions import guard_steps, here
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.board.acts.asked import Asked

# What the board says when the open beside a stopped session opened nothing, by the guard's
# reason (`serve.NOT_OPENED` on `main`).
NOT_OPENED = MappingProxyType(
    {
        "working": "Its session works again, so no session was opened.",
        "gone": (
            "Its session is gone from agterm, so no session was opened beside it: the "
            "board offers a fresh one in its place within a minute."
        ),
        "status": (
            "The task is no longer building, ready or landing, so no session was opened."
        ),
        "unread": (
            "The board cannot read whether its session works, and its stop no longer "
            "waits for you, so no session was opened beside it."
        ),
    }
)
GOES_ON = "Its agent reads the task’s state and goes on from there."


def beside(asked: Asked) -> str:
    """A fresh session beside the one the guard stopped, while the stop stands."""
    bound = here.bound(asked.checkout)
    acted = guard_steps.stepped(bound, asked.slug, "restart", None, asked.now)
    if not acted.acted:
        why = NOT_OPENED.get(acted.why or "", acted.say)
        raise Refusal("not-opened", why, "read the task's page again")
    slug = asked.slug
    return (
        f"A session of the task opened in agterm beside the one that stopped, which "
        f"agterm now names “{slug} · replaced”. {GOES_ON}"
    )
