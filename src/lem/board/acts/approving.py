"""His yes and his No to the criteria from the board (`serve.act_approve` and the criterion's
No of `act_answer` on `main`).

His yes is `lem criteria approve SLUG --shown DIGEST` in his name: the approval of the bytes his
page showed, or nothing, with his Yes written on the wait's question in the same write
(`model/criteria/yes.py`), so that of his yes on the board and his No typed in the session the
first counts. His No needs the same bytes: the page's mark is checked against the file's, and the
answer keeps it, so the session changes the text he read.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.criteria import approve, texts, where
from lem.board.acts import recording, telling
from lem.kernel.errors import Refusal
from lem.model.criteria import digest

if TYPE_CHECKING:
    from lem.board.acts.asked import Asked

NOTHING = "Nothing was recorded."
CHANGED = (
    "The criteria changed since the page showed them. Read them again, then answer. "
    f"{NOTHING}"
)


def shown_of(asked: Asked) -> str:
    """The mark of the criteria the page showed, when it is the mark of `criteria.md` now."""
    sheet = where.here_of(asked.checkout, asked.slug).sheet
    if not sheet.is_file():
        why = (
            "criteria.md is not in the task's folder yet: the task's session writes it. "
            f"{NOTHING}"
        )
        raise Refusal("no-criteria", why, "answer once the criteria wait for you")
    mark = digest.shown(texts.bytes_of(sheet, "the criteria"))
    if asked.given.digest != mark:
        raise Refusal("shown", CHANGED, "read the criteria again")
    return mark


def approved(asked: Asked) -> str:
    """His yes to the criteria the page showed: their approval in his name, and the word to
    the task's session."""
    shown = shown_of(asked)
    answer = partial(recording.answering, asked=asked, digest=shown, act="approve")
    approve.approved(
        asked.checkout,
        asked.slug,
        approve.Asked(by="owner", shown=shown, answer=answer),
    )
    told = telling.told(
        asked.checkout, asked.slug, asked.now, "it goes on to the build"
    )
    return f"Your yes to the criteria is on record. {told}"
