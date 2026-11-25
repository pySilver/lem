"""His yes and his No to the criteria from the board (`serve.act_approve` and the criterion's
No of `act_answer` on `main`).

His yes is `lem criteria approve SLUG --shown DIGEST` in his name: the approval of the bytes his
page showed, or nothing, with his Yes written on the wait's question in the same write
(`model/criteria/yes.py`), so that of his yes on the board and his No typed in the session the
first counts. His No needs the same bytes: the page's mark is checked against the file's, and the
answer keeps it, so the session changes the text he read.
"""

from typing import TYPE_CHECKING

from lem.app.criteria import approve, texts, where
from lem.board.acts import asking, noting, telling
from lem.kernel.errors import Refusal
from lem.model.criteria import digest
from lem.store import tasks

if TYPE_CHECKING:
    from lem.board.acts.asked import Asked
    from lem.records.questions import Question

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


def approval_of(asked: Asked, question: Question) -> approve.Asked:
    """The approval in his name of the bytes his page showed, as his answer to `question`
    when the record holds it."""
    shown = shown_of(asked)
    task = tasks.read(asked.state, asked.slug).task
    named = question.id if asking.on_record(task, question) else None
    return approve.Asked(by="owner", shown=shown, question=named, via="board")


def approved(asked: Asked, question: Question) -> str:
    """His yes to the criteria the page showed: their approval in his name, and the word to
    the task's session."""
    approve.approved(asked.checkout, asked.slug, approval_of(asked, question))
    entry = noting.act_of(
        "approve", asked.asker, asked.now, question=question.id, option="yes"
    )
    noting.noted(asked.state, asked.slug, entry)
    told = telling.told(
        asked.checkout, asked.slug, asked.now, "it goes on to the build"
    )
    return f"Your yes to the criteria is on record. {told}"
