"""What a drop checks before it writes: the path names a reviewer's item, the item is there, no
open task started from it, and it names proposals that passed into it."""

from typing import TYPE_CHECKING

from lem.addons.proposals import heads, item_files
from lem.kernel.errors import Refusal
from lem.store import reviewer_items

if TYPE_CHECKING:
    from pathlib import Path

LIST = "read the backlog again: lem proposals list gives the proposals and their items"


def reviewer_path(checkout: Path, given: str) -> str:
    """The reviewer's item `given` names, as a path from the main checkout
    (`.lem/state/backlog/NAME.md`): given so, or whole under the main checkout; refused for
    any other path."""
    path = reviewer_items.relative(checkout, given)
    if path is not None:
        return path
    raise Refusal(
        "not-reviewer-item",
        f"{given!r} is not the path of a reviewer's item, "
        f"{reviewer_items.FROM_CHECKOUT}/NAME.md",
        "only the reviewer's items are dropped here; an item of the backlog folder leaves "
        "it on a branch",
    )


def droppable(state: Path, target: Path, path: str) -> tuple[str, ...]:
    """The proposals the item at `target` names, once every check of a drop holds."""
    text = present(target, path)
    not_held(state, path)
    return named(text, path)


def present(target: Path, path: str) -> str:
    """The item's text; refused when it is gone."""
    try:
        return target.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise Refusal(
            "item-gone",
            f"the item {path} is not there: it was dropped, or its task landed",
            LIST,
        ) from None


def not_held(state: Path, path: str) -> None:
    """Refuse the drop while a task that has not ended started from the item."""
    holding = (task for claimed, task in item_files.claims_of(state) if claimed == path)
    task = next(holding, None)
    if task is not None:
        raise Refusal(
            "item-held",
            f"the task {task.slug} ({task.status}) builds the item {path}, so it is not "
            "dropped: it leaves with that task's landing",
            f"drop the task {task.slug} first, or let it land",
        )


def named(text: str, path: str) -> tuple[str, ...]:
    """The proposals the item names; refused for an item decided against already, and for one
    that names none."""
    head = heads.head_of(text)
    if head.worth == "no":
        raise Refusal(
            "decided-against",
            f"the item {path} is decided against already (worth: no): the reviewer refuted "
            "its proposal, and the record keeps the reason, so there is nothing to drop",
            "leave it: it waits for nobody, and the backlog does not count it",
        )
    if not head.proposals:
        raise Refusal(
            "item-unnamed",
            f"the item {path} names no proposal in its head, so no record keeps its drop",
            "only lem proposals verdict writes the reviewer's items: remove a file it did "
            "not write by hand",
        )
    return head.proposals
