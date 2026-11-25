"""What `lem issue` prints: one issue as it was read, a task's step on its issue, and the line
for the owner beside either."""

import msgspec

from lem.adapters.tracker_gh_facts import Comment
from lem.kernel.envelope import Envelope
from lem.records.base import Frozen


class IssueRead(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """An issue of origin: its id and repository, its words, state, labels, author, assignees
    and comments apart from the text; `ask` is the text, or the title when the text is empty
    (`ask_is` says which); `task_open` is what `lem task open` takes for it."""

    id: str
    number: int
    repository: str
    url: str
    title: str
    text: str
    state: str
    state_reason: str | None
    labels: tuple[str, ...]
    author: str | None
    assignees: tuple[str, ...]
    comments: tuple[Comment, ...]
    ask: str
    ask_is: str
    task_open: tuple[str, ...]


class Stepped(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """A task's step on its issue: what gh did on the issue (`did`), the steps written down
    (`wrote`), and the issue's address, state and assignees after it, when it was read."""

    slug: str
    ticket: str
    repository: str
    step: str
    url: str | None = None
    state: str | None = None
    assignees: tuple[str, ...] | None = None
    did: tuple[str, ...] = ()
    wrote: tuple[str, ...] = ()


def enveloped(outcome: msgspec.Struct, say: str | None) -> Envelope | msgspec.Struct:
    """The outcome, with the line for the owner when there is one."""
    if say is None:
        return outcome
    encoded = msgspec.Raw(msgspec.json.encode(outcome))
    return Envelope(ok=True, outcome=encoded, say=say)
