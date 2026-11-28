"""A feature's parts as a read of its request sees them (`read.py`;
`docs/plans/2026-11-27-a-feature-in-parts.md`, "The order of the parts").

A feature carries no key of its own: its parts are the tasks its `after` names whose `part_of`
names it (`feature_parts.named_parts`, `read.parts_of`). A read keeps them in `after` whatever
`--after` says, since the feature's landing finds them there (`app/tasks/parts.py`), and the
feature waits for each part that has not landed nor been answered: only the ends of its parts, or
the owner's word, lift that wait.
"""

from lem.records.base import Frozen


class Parts(Frozen, frozen=True, kw_only=True):
    """A feature's parts, as the tasks its `after` names show them: each part in the order of
    `after`, and those it still waits for. A task with no parts has neither."""

    slugs: tuple[str, ...] = ()
    waits: tuple[str, ...] = ()

    def after(self, asked: tuple[str, ...]) -> tuple[str, ...]:
        """The task's `after` once read: its parts first, then the tasks the read asks for."""
        return tuple(dict.fromkeys((*self.slugs, *asked)))

    def waited(self, asked: tuple[str, ...]) -> tuple[str, ...]:
        """What the task waits for once read: the tasks the read asks for, then each part
        that has not ended."""
        return tuple(dict.fromkeys((*asked, *self.waits)))
