"""The kinds of value a board's input holds, each printed its own way by the page.

A template never parses a text: it prints each by its kind. A plain text is escaped as it is. An
inline text is one line of Lem's in markdown, with its code in backticks and each pull request it
names a link (`[#44](https://github.com/acme/shop/pull/44)`), which the page renders with
markdown-it's inline rule and every HTML escaped. A document is markdown rendered whole, and a
chart is the source of a mermaid flowchart.
"""

from typing import Annotated, Literal

import msgspec

type Plain = str
type Inline = Annotated[
    str,
    msgspec.Meta(
        description="one line in markdown: code in backticks, a pull request as a link"
    ),
]
type Markdown = Annotated[str, msgspec.Meta(description="a markdown document")]
type Chart = Annotated[str, msgspec.Meta(description="the source of a mermaid chart")]
# An address on the board (`/studio/shop/tasks/fix-the-login`) or outside it.
type Href = Annotated[str, msgspec.Meta(min_length=1)]
# A symbol of the board's icons (`board-icons.json`): `clock`, `pull`, `alert`.
type Icon = Annotated[str, msgspec.Meta(pattern="^[a-z0-9-]+$")]
# Who acts, as a column, a row or a card shows it (`a-you`, `c-ok`): the owner, a lead and its
# builders, the checks and the review, the end, nobody, Lem, a fault, a good result.
type Look = Literal["you", "lead", "gate", "done", "quiet", "lem", "bad", "ok"]
# The look of a button: the way on, a step that cannot be undone, or a plain one.
type Press = Literal["go", "risk", "plain"]
# A view of a workspace, under which a task's panel opens.
type View = Literal["tasks", "waits", "backlog", "activity", "done", "new"]
