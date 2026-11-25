"""What a task the board starts is opened with (`serve.act_start` on `main`): the backlog item the
form names, by its path from the main checkout, or the owner's words, the first five plain words
of which name it.
"""

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from lem.app.tasks.opening import Asked as Opening
from lem.board.acts import slugs
from lem.kernel.errors import Refusal
from lem.model.task import claim

if TYPE_CHECKING:
    from lem.board.acts.asked import Asked
    from lem.records.record import Record

# The longest words of a new task, in characters (`serve.WORDS_CHARS` on `main`).
WORDS_CHARS = 2000
# The folders a task starts from: the backlog's and the reviewer's.
ITEM_FOLDERS = ("docs/backlog", ".lem/state/backlog")


def item_of(asked: Asked, every: tuple[Record, ...]) -> Opening:
    """The task of the backlog item the form names; refused for a path outside the backlog,
    one that is not there, and one a task holds."""
    path = asked.given.path.strip()
    parent = str(PurePosixPath(path).parent)
    if parent not in ITEM_FOLDERS or not path.endswith(".md"):
        why = f"{path} is no item of the backlog: nothing was started."
        raise Refusal("item", why, "read the backlog again")
    if not (asked.checkout / path).is_file():
        why = f"No item {path} is in the backlog now: nothing was started."
        raise Refusal("item-gone", why, "read the backlog again")
    holding = slugs.holder(path, every)
    if holding is not None:
        why = f"This item has a task already: {holding.slug}, {holding.status}."
        raise Refusal("item-held", why, f"go on with {holding.slug}")
    slug = slugs.item_slug(path, every)
    return Opening(slug=slug, ask=path, backlog_item=path)


def words_of(asked: Asked, every: tuple[Record, ...]) -> Opening:
    """The task of the owner's words; refused for no words, and for a slug a task runs."""
    words = " ".join(asked.given.words.split())[:WORDS_CHARS]
    slug = slugs.slug_of(words)
    if not slug:
        why = (
            "Type a few words that say what the task is, with a plain letter or digit "
            "(a to z, 0 to 9): they are its ask, and its first words its name."
        )
        raise Refusal("words", why, "begin with such a word")
    found = slugs.by_slug(every).get(slug)
    if found is not None and found.status not in claim.ENDED:
        why = f"{slug} is a task already, and it is {found.status}."
        raise Refusal("task-runs", why, "say the new one in other words")
    return Opening(slug=slug, ask=words)


def opening_of(asked: Asked, every: tuple[Record, ...]) -> Opening:
    """What the task opens with: the item the form names, else the owner's words."""
    if asked.given.path:
        return item_of(asked, every)
    return words_of(asked, every)
