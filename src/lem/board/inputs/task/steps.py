"""The steps of the owner's acts that ask first, each a page of the panel: the merge's confirm
(`/tasks/SLUG/merge`), a park with its one line of why, a drop with his note, a card of the
task's session; and the step that says why there is nothing to do now."""

from lem.board.inputs.forms import ActForm
from lem.board.inputs.parts import Chip, Input, Link
from lem.board.inputs.task.head import Fact
from lem.board.inputs.text import Href, Inline, Look, Plain
from lem.board.inputs.waits import Reasons


class NotNow(Input, frozen=True, kw_only=True):
    """A step with nothing to do now (`Lem merges it now`, `Nothing to park`): its id, what it
    says and the way back."""

    id: Plain
    said: Inline
    back: Link


class Confirm(Input, frozen=True, kw_only=True):
    """What every confirm step has: its look, its label and eyebrow (`Merge #44 · confirm`),
    the form of the act (none where the page may not act), the way back, the words in the
    form's place, and whether it is a sheet a phone reads to its end before its button."""

    look: Look
    label: Plain
    eyebrow: Plain
    form: ActForm | None = None
    back: Link | None = None
    words: Inline | None = None
    sheet: bool = False


class Merge(Input, frozen=True, kw_only=True):
    """The merge's confirm: green or not, its word, the careful mark, its line, the reasons,
    why the change is careful, its facts (the pull request, the commit, the branch, into, as),
    and the note under them."""

    confirm: Confirm
    green: bool
    word: Plain
    careful: Chip | None = None
    sub: Plain
    reasons: Reasons | None = None
    careful_why: Inline | None = None
    facts: tuple[Fact, ...] = ()
    note: Plain


class Park(Input, frozen=True, kw_only=True):
    """A park's confirm: what stopped the build and why, and what a park keeps."""

    confirm: Confirm
    what: Inline
    said: Inline


class Drop(Input, frozen=True, kw_only=True):
    """A drop's confirm: what the task waits for, and what a drop ends."""

    confirm: Confirm
    what: Inline
    said: Inline


class Card(Input, frozen=True, kw_only=True):
    """A card of the task's session on the board: the card's page in its frame, its title, and
    the id a refresh keeps it by."""

    confirm: Confirm
    frame: Href
    title: Plain
    keep: Plain
