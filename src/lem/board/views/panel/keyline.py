"""The one line a task's header keeps when it folds (`board_task.key_line` on `main`): the pull
request as a link with green or not green, else what the task waits for, else its newest state's
line."""

from typing import TYPE_CHECKING

from lem.board.inputs.names import pull_link
from lem.board.inputs.task.head import KeyLine
from lem.board.views import words
from lem.board.views.panel.common import pull_of
from lem.board.views.panel.shown import shown
from lem.board.views.panel.waiting import waits_for

if TYPE_CHECKING:
    from lem.board.views.world import Seen
    from lem.model.owner.looks import Rows
    from lem.records.landing.record import Landing, Pull

PULL = "code-pull-request"


def key_line(seen: Seen, rows: Rows) -> KeyLine | None:
    """The pull request with green or not green, else what the task waits for, else its
    newest state's line."""
    record = seen.record
    pull = pull_of(record)
    if pull is not None:
        return pulled(pull, record.landing)
    waiting = waits_for(seen, rows)
    if waiting is not None and waiting.yours:
        return KeyLine(look="you", icon="circle-question", text=waiting.text)
    if waiting is not None:
        return KeyLine(icon="clock", text=waiting.text)
    line = shown(record)
    return KeyLine(text=words.capital(line)) if line else None


def pulled(pull: Pull, landing: Landing | None) -> KeyLine:
    """The pull request's line, with green or not green once it is proposed."""
    proposed = landing.proposed if landing else None
    link = pull_link(pull, whole=True)
    if proposed is None:
        return KeyLine(link=link, icon=PULL)
    word = "green" if proposed.green else "not green"
    look = "ok" if proposed.green else "you"
    return KeyLine(link=link, word=word, look=look, icon=PULL)
