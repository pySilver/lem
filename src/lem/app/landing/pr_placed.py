"""The lines under `## Filed in the backlog` and `## Filed as not worth it` (`main:land.placed`):
the notes' own lines, then the step's. A notes line that names an item the step lists takes the
place of the step's line, under the heading the item's `worth` gives, so no item is written
twice and none under the other heading."""

import re
from typing import TYPE_CHECKING

from lem.model.landing.propose_lines import FILED, NOT_WORTH

if TYPE_CHECKING:
    from lem.app.landing.pr_inputs import Lines

HEADINGS = (FILED, NOT_WORTH)
# The lines under each heading of the items: the step's, and the text's.
type Steps = dict[str, list[str]]
type Headed = dict[str, Lines]


def names_item(line: str, path: str) -> bool:
    """Whether a line names the item at `path`, and not another whose path starts the
    same."""
    return re.search(rf"(?<![\w./-]){re.escape(path)}(?![\w./-])", line) is not None


class Shelf:
    """The step's lines by heading, each item's place among them, and the notes' own lines
    put in their place."""

    __slots__ = ("kept", "lists", "spots", "taken")

    def __init__(self, steps: Steps) -> None:
        """The shelf of the step's lines, each item found by the path in its line."""
        self.lists = {heading: list(steps[heading]) for heading in HEADINGS}
        self.spots = {
            line.split("`")[1]: (heading, at)
            for heading in HEADINGS
            for at, line in enumerate(steps[heading])
        }
        self.kept: dict[str, list[str]] = {heading: [] for heading in HEADINGS}
        self.taken: set[str] = set()

    def put(self, heading: str, line: str) -> None:
        """Put a notes line in the place of the step's line of the item it names, after it
        when another took that place, else under its own heading."""
        path = next((path for path in self.spots if names_item(line, path)), None)
        if path is None:
            self.kept[heading].append(line)
            return
        where, at = self.spots[path]
        if path in self.taken:
            self.lists[where].append(line)
            return
        self.taken.add(path)
        self.lists[where][at] = line

    def placed(self) -> Headed:
        """Each heading's lines: the notes' own, then the step's."""
        return {heading: self.under(heading) for heading in HEADINGS}

    def under(self, heading: str) -> Lines:
        """One heading's lines: the notes' own, then the step's."""
        return (*self.kept[heading], *self.lists[heading])


def placed(own: Headed, steps: Steps) -> Headed:
    """The notes' own lines and the step's under the two headings of the items."""
    shelf = Shelf(steps)
    for heading in HEADINGS:
        for line in own[heading]:
            shelf.put(heading, line)
    return shelf.placed()
