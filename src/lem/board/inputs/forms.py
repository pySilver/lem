"""The owner's acts as the page offers them: a form that posts one act, the answer to a
question with its note, and a line he could type in a session instead.

A view puts a form in an input only where the page may act (on this Mac, or through the tailnet
door for his login): a page that may not act has none, and the template prints what it is given.
"""

from typing import Literal

from lem.board.inputs.parts import Input, Link
from lem.board.inputs.text import Href, Icon, Inline, Plain, Press


class Field(Input, frozen=True, kw_only=True):
    """A hidden field the form posts: the question's id, the digest the page showed, the tip,
    the view under the panel."""

    name: Plain
    shown: Plain


class TextBox(Input, frozen=True, kw_only=True):
    """A box the owner types in: its name, its id (kept across a refresh), its label and
    placeholder, its rows (one line when 1), the most characters it takes, whether it must be
    filled, and the words already in it."""

    name: Plain
    id: Plain
    label: Plain | None = None
    placeholder: Plain | None = None
    rows: int = 1
    longest: int = 2000
    required: bool = False
    words: Plain = ""


class ActForm(Input, frozen=True, kw_only=True):
    """A form that posts one act (`Open a session`, `Start a task`, `Merge pull request #44`):
    where it posts, its button's words, icon and look, the words while it runs, its hidden
    fields, and the box the owner types in, when it has one."""

    action: Href
    label: Plain
    icon: Icon
    press: Press = "plain"
    busy: Plain
    fields: tuple[Field, ...] = ()
    box: TextBox | None = None


class Choice(Input, frozen=True, kw_only=True):
    """One option of an answer: its key and words, its icon and look. An option that asks
    first (park, drop) is a link to its confirm step, which takes the note typed so far."""

    option: Plain
    label: Plain
    icon: Icon
    press: Press = "plain"
    confirm: Href | None = None


class AnswerForm(Input, frozen=True, kw_only=True):
    """The answer to a question of the board (a breaker, a plan, the skip of a read, the
    criteria): its id, where it posts, the question, the hidden fields (the question's id, the
    digest shown, the tab, the view), the box of his note, and one choice for each option."""

    id: Plain
    action: Href
    question: Plain
    fields: tuple[Field, ...]
    note: TextBox
    choices: tuple[Choice, ...]


class Typed(Input, frozen=True, kw_only=True):
    """A line the owner can type in any session instead (`/lem park SLUG`), and what it does."""

    command: Plain
    does: Plain


class Way(Input, frozen=True, kw_only=True):
    """One line of where the owner answers, beside the task's session: its words, the agterm
    session a button jumps to (on this Mac only), a form (`Open a session`), a link (the
    Inbox's thread, `Park it…`), and the lines he could type."""

    said: Inline
    jump: Plain | None = None
    form: ActForm | None = None
    link: Link | None = None
    typed: tuple[Typed, ...] = ()
    kind: Literal["session", "inbox", "owner"] = "session"
