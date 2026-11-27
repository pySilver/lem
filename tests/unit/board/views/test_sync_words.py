"""The board's words for a feature's sync: the wake that the sync duty sends, and the session
it opens when none lives (`board/views/activity/tell_sessions.py`)."""

from fakes.records import MOMENT
from lem.app.sessions import acts
from lem.board.views.activity import tell_sessions

SAID = "the base moved: the feature takes it in by a merge"


def test_a_sync_wake_and_a_sync_open_have_their_words() -> None:
    woken = acts.Wake(at=MOMENT, session="S-1", why="sync", head="a" * 40)
    opened = acts.Open(
        at=MOMENT, session="S-1", name="save-items", phase="shape", why="sync"
    )
    assert tell_sessions.woken(woken).text == SAID
    assert tell_sessions.opened(opened).sub == f"the shape phase · {SAID}"
