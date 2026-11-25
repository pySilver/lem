"""An item of the Backlog view (`board_pages.backlog_item` on `main`): its title and worth, its
tags, the place in the code it names, who added it, its text, and what the owner may do with
it."""

import hashlib
import re
from typing import TYPE_CHECKING

from lem.board.inputs.backlog import Entry
from lem.board.inputs.parts import Document
from lem.board.views.backlog import groups, holds, tags
from lem.board.views.backlog.added import added_of

if TYPE_CHECKING:
    from lem.board.views import backlog_read
    from lem.board.views.world import World
    from lem.records.record import Record

NOWHERE = "no place in the code named"
# A proposal's name (`retro of 2026-11-23 #7`), which an item's text shows as code, so that
# its number does not read as a pull request.
PROPOSAL = re.compile(r"(retro|night) of (\d{4}-\d{2}-\d{2}) #([1-9]\d*)")
# How many hex digits of the text's digest a document's id keeps.
DIGITS = 12


def entry_of(
    world: World, records: tuple[Record, ...], entry: backlog_read.Entry
) -> Entry:
    """The item `entry` of the read as the view shows it."""
    held = groups.holder(records, entry.path)
    clock = world.clock
    return Entry(
        key=entry.key,
        path=entry.path,
        title=entry.title,
        worth=groups.worth_of(entry),
        tags=tags.tags(entry, held, clock.now, clock.zone),
        where=entry.where or NOWHERE,
        where_problem=entry.where_problem if entry.where else None,
        new=tags.is_new(entry),
        added=added_of(world, records, entry),
        body=body_of(entry),
        holds=holds.holds_of(world.viewer, entry, held),
    )


def body_of(entry: backlog_read.Entry) -> Document | None:
    """The item's text as a document, or why it cannot be read; None with no text."""
    key = f"bl-{entry.key}"
    if entry.bad is not None:
        return document(key, f"This item cannot be read: {entry.bad}.")
    text = entry.text
    if entry.reviewer:
        text = PROPOSAL.sub(as_code, text)
    return document(key, text) if text else None


def as_code(found: re.Match[str]) -> str:
    """A proposal's name in backticks."""
    return f"`{found[0]}`"


def document(key: str, text: str) -> Document:
    """A markdown text under the id a refresh keeps while the text stays: `md-KEY-` and the
    first twelve of the SHA-256 of `KEY|TEXT` (`board_pages.md_block` on `main`)."""
    named = f"{key}|{text}".encode()
    digest = hashlib.sha256(named).hexdigest()[:DIGITS]
    return Document(id=f"md-{key}-{digest}", text=text)
