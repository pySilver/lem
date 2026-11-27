"""The backlog item a task starts from, as `lem task open` finds it: the one `--item` names, a
reviewer's item whose path is the ask alone, or the one tracked item the owner's words name, since
the board's "+" and a `/lem` line give the item's path alone or among his words, and the task
holds the item from its opening (`stages/new.md`, "Open the task")."""

import re
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing import polish
from lem.store import reviewer_items

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.tasks.opening import Asked
    from lem.store.places import Workspace

# A path of a markdown file among the owner's words.
NAMED = re.compile(r"[\w./-]+\.md\b")


def named_in(checkout: Path, words: str) -> str | None:
    """The one item of the backlog folder that git tracks whose path the owner's words name,
    alone or among other words, as the board's "+" and a `/lem` line give them; None when they
    name none, or more than one."""
    found = {
        named
        for named in NAMED.findall(words)
        if str(PurePosixPath(named).parent) == polish.BACKLOG
        and (checkout / named).is_file()
    }
    return found.pop() if len(found) == 1 else None


def item_of(workspace: Workspace, asked: Asked) -> str | None:
    """The backlog item the task starts from, a path in the main checkout: the one `--item`
    names, a reviewer's item whose path is the ask alone, or the one tracked item the words
    name; refused when it is gone (the owner dropped it in the meantime)."""
    given = asked.backlog_item
    if given:
        named = reviewer_items.checkout_path(workspace.checkout, given)
        if named is None:
            raise Refusal(
                "item-path",
                f"the backlog item {given!r} must name a file inside {workspace.checkout}; "
                "a tracked item cannot be a link",
                "give --item the path to the item itself, or omit --item",
            )
        path = reviewer_items.relative(workspace.checkout, given) or named.as_posix()
    else:
        checkout = workspace.checkout
        path = reviewer_items.relative(checkout, asked.ask) or named_in(
            checkout, asked.ask
        )
    if not path:
        return None
    reviewer_items.require(workspace.checkout, path)
    return path
