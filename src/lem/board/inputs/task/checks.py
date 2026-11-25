"""The tab Checks and review of a task, `/HOST/WORKSPACE/tasks/SLUG/checks`: each command of the
last run with its output, the rounds of the review, and the proposal."""

from lem.board.inputs.parts import Input, Link, Note, Row
from lem.board.inputs.task.overview import Went
from lem.board.inputs.text import Icon, Inline, Look, Plain
from lem.board.inputs.waits import Reasons


class Command(Input, frozen=True, kw_only=True):
    """A command of the last run: its id, its look and icon, its word (`green`, `exit 1`, or
    `runs` while it runs), the command, the link to its output, its last line, the commit it ran
    on, and when it ended."""

    id: Plain
    look: Look
    icon: Icon
    word: Plain
    command: Plain
    output: Link | None = None
    last: Plain | None = None
    tip: Plain | None = None
    time: Plain | None = None


class Proposal(Input, frozen=True, kw_only=True):
    """The proposal: its look and icon, its words (`Proposed: not green, for 4 reasons`), what
    green means or the reasons, and when."""

    look: Look
    icon: Icon
    said: Plain
    green: Inline | None = None
    reasons: Reasons | None = None
    time: Plain


class Checks(Input, frozen=True, kw_only=True):
    """The tab: the result of an act, the card of the checks (its line, its commands, the
    stopped or red end of a run with no command, or why there is none), the card of the review
    (its line, its rounds, the proposal, or why there is none), the words of a task that ended
    with neither, and what went with a pruned task's events."""

    note: Note | None = None
    commands_said: Plain | None = None
    commands: tuple[Command, ...] = ()
    ended_run: Row | None = None
    commands_empty: Plain | None = None
    rounds_said: Plain | None = None
    rounds: tuple[Row, ...] = ()
    proposal: Proposal | None = None
    rounds_empty: Plain | None = None
    ended: Plain | None = None
    went: Went | None = None
