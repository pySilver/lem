"""The text of a reviewer's item, in the backlog's item format (`agents/lem-builder.md`, rule 6;
`project.item_text` and `refuted_item_text` on `main`).

Its head (python-frontmatter writes it) holds `worth`, `where`, `added` and `proposals`, the
names of the proposals in it, by which a drop finds their records. The passed proposals of one
area are one item, `worth: later`; a refuted proposal is an item of its own, `worth: no`, whose
last line is `Decided against: REASON`, so that a later agent who meets the same change finds it
decided.
"""

from typing import TYPE_CHECKING

import frontmatter

from lem.addons.proposals import names

if TYPE_CHECKING:
    import datetime as dt

    from lem.addons.proposals.record import Proposal

type Entry = tuple[str, Proposal]
type Head = tuple[str, str, dt.date]


def origin(name: str, proposal: Proposal) -> list[str]:
    """Where the proposal came from, its source and place, and its body."""
    named = names.parsed(name)
    run = f"the {named.kind} of {named.day}" if named else "its run"
    place = f"Its source: {proposal.source}. Where: `{proposal.where}`."
    said = f"From {run}, proposal {proposal.number}. {place}"
    return [said, "", proposal.body]


def section(name: str, proposal: Proposal) -> list[str]:
    """One proposal of a passed area's item: its move as a heading, where it came from, its
    body."""
    heading = f"## {proposal.move}"
    return ["", heading, "", *origin(name, proposal)]


def joined(listed: list[str]) -> str:
    """`a`, `a and b`, `a, b and c`."""
    *earlier, last = listed
    if not earlier:
        return last
    first = ", ".join(earlier)
    return f"{first} and {last}"


def passed_line(area: str, today: dt.date, named: list[str]) -> str:
    """The first line of a passed area's item: how many proposals, about what, which."""
    count = "1 proposal" if len(named) == 1 else f"{len(named)} proposals"
    return f"The reviewer passed {count} about {area} on {today}: {joined(named)}."


def passed_text(title: str, area: str, today: dt.date, entries: list[Entry]) -> str:
    """The item of the proposals of `area` that passed on `today`, under `title`."""
    named = [name for name, _ in entries]
    lines = [f"# {title}", "", passed_line(area, today, named)]
    for name, proposal in entries:
        lines.extend(section(name, proposal))
    _, first = entries[0]
    return dumped(lines, ("later", first.where, today), named)


def refuted_text(name: str, proposal: Proposal, reason: str, today: dt.date) -> str:
    """The item of the refuted proposal `name`, with the reviewer's reason as its last line."""
    title = " ".join(proposal.move.split())
    told = " ".join(reason.split())
    lines = [f"# {title}", "", f"The reviewer refuted {name} on {today}.", ""]
    lines.extend((*origin(name, proposal), "", f"Decided against: {told}"))
    return dumped(lines, ("no", proposal.where, today), [name])


def dumped(lines: list[str], head: Head, named: list[str]) -> str:
    """The item: its head (worth, where, added) with the names of its proposals, then its
    lines."""
    worth, where, added = head
    body = "\n".join(lines)
    post = frontmatter.Post(
        body, worth=worth, where=where, added=added, proposals=named
    )
    return f"{frontmatter.dumps(post, sort_keys=False)}\n"
