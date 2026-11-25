"""The names and addresses the board makes of a record's facts: a task's title from its slug,
the address of a task, its tab and its view, and the link of a pull request.

Every address of a workspace starts at its base, `/HOST/WORKSPACE`; a task opens in the panel
over the view in the address (`?in=waits`), which the kanban, the view of no `?in`, leaves out.
"""

import re
from typing import TYPE_CHECKING
from urllib.parse import quote

from lem.board.inputs.parts import Chip, Link

if TYPE_CHECKING:
    from lem.board.inputs.text import Href, Plain, View
    from lem.records.landing.record import Pull

# The hover of every link to a pull request on the forge.
FORGE = "Open the pull request on the forge: {url}"
REPOSITORY = re.compile(r"^https?://[^/]+/(?P<repo>[^/]+/[^/]+)/pull/\d+")


def title_of(slug: str) -> str:
    """`report-dates-stay-whole` as `Report dates stay whole`: the owner reads names, never
    codes."""
    words = " ".join(slug.split("-")).strip()
    if not words:
        return "A task"
    return words[:1].upper() + words[1:]


def task_href(
    base: Href,
    slug: str,
    tab: str | None = None,
    under: View = "tasks",
    *,
    artifact: str | None = None,
) -> Href:
    """The task's tab or artifact over the view `under`. Turbo needs the slash after a file."""
    named = quote(slug, safe="")
    path = f"{base}/tasks/{named}"
    if artifact and not tab:
        tab = "artifacts"
    if tab and (tab != "overview" or artifact):
        section = quote(tab)
        path = f"{path}/{section}"
    if artifact:
        encoded = quote(artifact)
        path = f"{path}/{encoded}/"
    return (
        f"{path}?in={under}"
        if under in {"waits", "backlog", "activity", "done"}
        else path
    )


def repository(pull: Pull) -> str | None:
    """`acme/shop` of a pull request's address, or None when the address names none."""
    found = REPOSITORY.match(pull.url)
    return found["repo"] if found else None


def pull_link(pull: Pull, *, whole: bool = False) -> Link:
    """The link to a pull request: `#44`, or `acme/shop#44` when `whole`."""
    named = repository(pull) if whole else None
    label = f"{named}#{pull.number}" if named else f"#{pull.number}"
    title = FORGE.format(url=pull.url)
    return Link(href=pull.url, label=label, title=title, out=True)


def pull_chip(pull: Pull, *, whole: bool = False) -> Chip:
    """The chip of a pull request, which links to it."""
    link = pull_link(pull, whole=whole)
    label, title = link.label, link.title
    return Chip(
        label=label, icon="code-pull-request", look="gate", title=title, link=link
    )


def plural(count: int, word: Plain) -> Plain:
    """`1 task`, `2 tasks`."""
    ending = "" if count == 1 else "s"
    return f"{count} {word}{ending}"
