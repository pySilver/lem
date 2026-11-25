"""A markdown text of a task the browser renders (`board_pages.md_block` and `chart_block` on
`main`): its pull requests made links, under an id that a refresh keeps while its text stays,
`md-KEY-` and the first twelve of the SHA-256 of `KEY|TEXT`."""

import hashlib
from typing import TYPE_CHECKING

from lem.board.inputs.parts import Document
from lem.board.views.panel import pulls

if TYPE_CHECKING:
    from lem.records.record import Record

ID_LENGTH = 12


def document(
    key: str,
    text: str,
    forge: str | None = None,
    media: str | None = None,
    folder: str | None = None,
) -> Document:
    """The text under the key `key`, with the pictures of `media` and its links from
    `folder`."""
    linked = pulls.linked(text, forge)
    keyed = f"{key}|{linked}".encode()
    digest = hashlib.sha256(keyed).hexdigest()[:ID_LENGTH]
    named = f"md-{key}-{digest}"
    return Document(id=named, text=linked, media=media, folder=folder)


def chart(key: str, source: str) -> Document:
    """A mermaid chart of a record (a criterion's, a decision's), as a document's fenced
    block is drawn."""
    return document(key, f"```mermaid\n{source.strip()}\n```")


def forge_of(record: Record) -> str | None:
    """The forge's address of the repository of the task's pull request, which a bare `#N`
    of its texts links to; None with no pull request."""
    pull = record.landing.pull if record.landing else None
    return pulls.forge_of(pull.url if pull else None)
