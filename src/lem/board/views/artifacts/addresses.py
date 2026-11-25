"""The addresses of a task's files on the board (`board_pages.task_href` with a file, and the
server's `raw_href` and `media_href` on `main`): a file on the tab Artifacts, a page of the
folder on its own, and the folder of the task's pictures. Each part of a path is encoded, and an
address on the tab ends in a slash, so that none ends in an extension Turbo refuses to visit."""

from typing import TYPE_CHECKING
from urllib.parse import quote

from lem.board.inputs.names import task_href
from lem.board.inputs.parts import Link

if TYPE_CHECKING:
    from lem.board.inputs.text import Href
    from lem.board.views.world import World

ARTIFACTS = "artifacts"


def encoded(path: str) -> str:
    """Each part of `path` encoded, the slashes between them kept."""
    parts = (quote(part, safe="") for part in path.split("/"))
    return "/".join(parts)


def tab_href(world: World, slug: str, path: str | None = None) -> Href:
    """The tab Artifacts of task `slug`, with the file `path` shown, over the page's view."""
    tab = f"{ARTIFACTS}/{encoded(path)}/" if path else ARTIFACTS
    return task_href(world.viewer.base, slug, tab, world.viewer.view)


def raw_href(world: World, slug: str, path: str) -> Href:
    """A file of the task's folder as it is, for a frame or a tab of its own."""
    task = media_href(world, slug).removesuffix("media/")
    named = encoded(path)
    return f"{task}raw/{named}"


def media_href(world: World, slug: str) -> Href:
    """The folder of the task's pictures, which a document's pictures start from."""
    base, task = world.viewer.base, quote(slug)
    return f"{base}/tasks/{task}/media/"


def file_link(world: World, slug: str, path: str, label: str, title: str) -> Link:
    """A link that opens the file `path` on the tab Artifacts, in the task's panel."""
    href = tab_href(world, slug, path)
    return Link(href=href, label=label, title=title, frame=True)
