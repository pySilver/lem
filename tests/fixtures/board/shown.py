"""Makers of the values the afternoon's pages print, each written out: a time with the words it
shows, a task's address, a chip of the type of a request.

They spell a value; they make none of its words, so that the expected inputs read as the page
the owner sees, and a view's rule that gives other words fails its case.
"""

import hashlib
from zoneinfo import ZoneInfo

from fixtures.board.moments import BASE, NOW, ago
from lem.board.inputs.layout import Viewer
from lem.board.inputs.parts import Chip, Document, When

# The zone the afternoon's board shows its clock in.
ZONE = ZoneInfo("UTC")
# The owner on this Mac: a page that may act and jump to a session.
VIEWER = Viewer(host="studio", workspace="shop", base=BASE, local=True, may_act=True)
# The version of the state folder a page is drawn at, which a view takes as it is.
VERSION = "afternoon"
# Each request's type, as its chip says it, and its hover.
TYPE = "The type of the request, as Lem took it from the request: {kind}, because {why}"


def since(minutes: float, shown: str, title: str | None = None) -> When:
    """A length from `minutes` before now, which the browser's clock moves on."""
    return When(at=ago(minutes), shown=shown, title=title, ticks="since")


def gone(minutes: float, shown: str, title: str | None = None) -> When:
    """A time since `minutes` before now, which the browser's clock moves on."""
    return When(at=ago(minutes), shown=shown, title=title, ticks="ago")


def clock(minutes: float, shown: str, title: str | None = None) -> When:
    """A clock time, which stays as it is."""
    return When(at=ago(minutes), shown=shown, title=title)


def just_now() -> When:
    """The moment of the page."""
    return When(at=NOW, shown="just now", ticks="ago")


def task(slug: str, tab: str | None = None, under: str | None = None) -> str:
    """The address of a task, its tab, and the view under its panel."""
    path = f"{BASE}/tasks/{slug}" + (f"/{tab}" if tab else "")
    return f"{path}?in={under}" if under else path


def kind(name: str, why: str) -> Chip:
    """The chip of a request's type."""
    return Chip(label=name, icon="flag", title=TYPE.format(kind=name, why=why))


def document(
    key: str, text: str, media: str | None = None, folder: str | None = None
) -> Document:
    """A markdown text under the id a refresh keeps while the text stays: `md-KEY-` and the
    first twelve of the SHA-256 of `KEY|TEXT` (`main`'s `board_pages.md_block`)."""
    digest = hashlib.sha256(f"{key}|{text}".encode()).hexdigest()[:12]
    return Document(id=f"md-{key}-{digest}", text=text, media=media, folder=folder)
