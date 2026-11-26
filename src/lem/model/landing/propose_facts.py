"""What `propose` reads besides the record and the world: facts of the branch that only git
shows, and the notes the agent wrote. `app/landing/propose.py` gathers them; the rules of
`propose`, green and the pull request's text read them."""

from typing import TYPE_CHECKING

from lem.model.landing.items import BacklogItem
from lem.records.base import Frozen
from lem.records.landing.checks import Checked

if TYPE_CHECKING:
    from lem.records.record import Record

# The backlog folder, relative to the root of the repository: its one place.
BACKLOG = "docs/backlog"


class Filing(Frozen, frozen=True, kw_only=True):
    """An item the branch adds to the backlog folder: its path, its title (the first line
    after its head) and its `worth` as the tip's file says them."""

    path: str
    title: str | None = None
    worth: str | None = None


class Settings(Frozen, frozen=True, kw_only=True):
    """Lem's own settings files as the branch changes them: the team's file at the branch's
    merge base and at its tip (None where it is not), and whether one machine's own file is
    tracked at each."""

    before: str | None = None
    after: str | None = None
    local: tuple[bool, bool] = (False, False)


class Facts(Frozen, frozen=True, kw_only=True):
    """The facts of one proposal: the paths the branch changes against its merge base with
    the base, Lem's settings as it changes them, the items it adds to the backlog, which of
    the paths `propose` asked about the tip holds, the head of each of them that is an item, and
    the notes. The items under the bar carry their text and any reason."""

    changed: tuple[str, ...] = ()
    settings: Settings = Settings()
    added: tuple[Filing, ...] = ()
    under: tuple[BacklogItem, ...] = ()
    in_tip: frozenset[str] = frozenset()
    heads: tuple[Filing, ...] = ()
    notes: str = ""
    bar_read: Checked | None = None


def small(record: Record) -> bool:
    """Whether the task is on the fast track: its criteria's size, else its shape's track."""
    size = record.task.criteria.size
    if size is not None:
        return size == "small"
    shape = record.task.shape
    return shape is not None and shape.track == "small"
