"""The reasons a pull request is not green, as the merge row, the Overview, Checks and review and
the merge step list them (`board_model.reason_parts` and `board_pages.reason_list` on `main`).

Each reason of `propose` is one line: its head up to its first `: ` or `. `, what it is about in
a parenthesis that closes the head, and the rest cut at its own `; ` and `. ` into one sentence
each. A reason about a decision or a breaker links to it on Criteria and decisions.
"""

import re
from typing import TYPE_CHECKING

from lem.board.inputs.names import task_href
from lem.board.inputs.parts import Link
from lem.board.inputs.waits import Reason, Reasons
from lem.board.views.panel import pulls
from lem.board.views.panel.cuts import cuts, split_top
from lem.board.views.words import capital

if TYPE_CHECKING:
    from lem.board.inputs.text import Href, View
    from lem.records.record import Record

REF = re.compile(r"^(decision|breaker) (\d+)\b")
# Where a reason's rest is cut into its sentences.
SENTENCES = ("; ", ". ")


def reasons(record: Record, key: str, under: View | None, base: Href) -> Reasons | None:
    """The reasons of the task's proposal under the list's id `key`, on a page over the view
    `under`; None while it has no proposal that is not green."""
    landing = record.landing
    proposed = landing.proposed if landing else None
    if proposed is None or proposed.green:
        return None
    forge = pulls.forge_of(landing.pull.url if landing and landing.pull else None)
    href = task_href(base, record.task.slug, "criteria", under or "tasks")
    rows = tuple(reason(line, href, forge) for line in proposed.reasons)
    return Reasons(id=key, rows=rows)


def reason(line: str, href: Href, forge: str | None) -> Reason:
    """One reason as a row; its decision or breaker links to `href`."""
    lead, rest = leading(line.strip())
    head, about = closing(lead)
    said = capital(head.strip().rstrip(".:"))
    return Reason(
        head=pulls.linked(said, forge),
        about=pulls.linked(about, forge) if about else None,
        detail=details(rest, forge),
        ref=ref_of(head, href),
    )


def leading(text: str) -> tuple[str, str]:
    """The leading clause of a line, up to its first `: ` or `. `, and the rest."""
    first = cuts(text, (": ", ". "))
    if not first:
        return text, ""
    index, sep = first[0]
    return text[:index], text[index + len(sep) :]


def details(rest: str, forge: str | None) -> tuple[str, ...]:
    """The rest of a line, one sentence each."""
    parts = split_top(rest.strip(), SENTENCES)
    return tuple(pulls.linked(sentence(part), forge) for part in parts)


def sentence(part: str) -> str:
    """One sentence of a reason, with its capital and no full stop."""
    return capital(part.rstrip("."))


def closing(head: str) -> tuple[str, str]:
    """The head and the parenthesis that closes it, or the head alone."""
    depth, cut = 0, None
    for index, char in enumerate(head):
        if char == "(" and not depth:
            cut = index
        depth += (char == "(") - (char == ")")
    if not cut or depth or not head.rstrip().endswith(")"):
        return head, ""
    about = head.rstrip()[cut + 1 : -1]
    return head[:cut].strip(), about.strip()


def ref_of(head: str, href: Href) -> Link | None:
    """The link to the decision or the breaker the reason names, or None."""
    found = REF.match(head)
    if found is None:
        return None
    named = f"{found[1]} {found[2]}"
    return Link(
        href=href,
        label=named,
        title=f"Open {named} on Criteria and decisions",
        icon="arrow-right",
        frame=True,
        anchor=f"dec-{found[2]}",
    )
