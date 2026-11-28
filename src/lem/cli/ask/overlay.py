"""Show and close a question in the current agterm session."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.app.asking import keys, overlay_read, overlay_tree, page_close
from lem.cli.ask import temp_pages
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from pathlib import Path

TARGET = "--target"
BUSY = "overlay already open"


@dataclass(frozen=True, kw_only=True)
class Display:
    """The flags of a question overlay."""

    percent: str | None
    follow: bool
    chromeless: bool


@dataclass(frozen=True, kw_only=True)
class Opened:
    """The overlay agterm opened, or the question in its busy slot."""

    page: str | None = None
    busy: bool = False


@dataclass(frozen=True, kw_only=True)
class Overlay:
    """An operation in the agterm session that asked, never in another session."""

    environ: dict[str, str]
    session: str

    def opening(self, path: Path, display: Display) -> Opened:
        """Show the file with the agterm bridge."""
        told = overlay_read.reply(
            self.environ,
            "open",
            "--html",
            str(path),
            "--js",
            TARGET,
            self.session,
            *flags(display),
        )
        if told.error == BUSY:
            return Opened(page=self.shown(), busy=True)
        page = (told.answer.page or told.answer.id) if told.answer else None
        if not told.ok or not page:
            raise Unanswered("agtermctl", told.error or "no id for the question page")
        return Opened(page=keys.checked(page))

    def shown(self, page: str | None = None) -> str | None:
        """The owner has a question page in this session's overlay slot."""
        overlays = overlay_tree.read(self.environ, self.session)
        return temp_pages.ours(overlays, page)

    def close(self, page: str) -> bool:
        """Close this session's overlay while it still has this question."""
        return page_close.close(self.environ, self.session, page, shows=ours)

    def outcome(self, page: str) -> overlay_read.PageOutcome:
        """Read what the owner did in the overlay."""
        return overlay_read.outcome(self.environ, page)


def ours(overlays: tuple[overlay_tree.Overlay, ...], page: str) -> bool:
    """The session shows this page, and its file is one lem ask wrote."""
    return temp_pages.ours(overlays, page) is not None


def flags(display: Display) -> tuple[str, ...]:
    """The owner can ask for focus, a panel size or no title strip."""
    percent = ("--size-percent", display.percent) if display.percent else ()
    follow = ("--follow",) if display.follow else ()
    chromeless = ("--chromeless",) if display.chromeless else ()
    return (*percent, *follow, *chromeless)
