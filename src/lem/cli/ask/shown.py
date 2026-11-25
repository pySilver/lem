"""The words every question page of `lem ask` takes: where it shows, how, and the wait.

`lem ask ask`, `q`, `wait` and `demo` each take them; their `Call` is a `Shown` with words of
its own.
"""

from typing import Literal

import click
import msgspec

from lem.cli.words import choice

type Style = Literal["refined", "minimal", "bold", "terminal"]
type Review = Literal["auto", "always", "never"]
# seconds the call waits for the owner's answer, unless it says
TIMEOUT = 570.0


class Shown(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """How a question page shows, and how long the call waits for its answer."""

    follow: bool = False
    size: int | None = None
    full: bool = False
    style: Style | None = None
    review: Review | None = None
    chromeless: bool = False
    timeout: float = TIMEOUT
    no_wait: bool = False
    no_status: bool = False
    browser: bool = False


def options() -> list[click.Parameter]:
    """The options of `Shown`, made new for each command that takes them."""
    return [
        click.Option(
            ["--follow"],
            is_flag=True,
            help="select this session, so the owner sees it now",
        ),
        click.Option(
            ["--size"], type=click.INT, help="a floating panel, percent of the session"
        ),
        click.Option(["--full"], is_flag=True, help="cover the whole session"),
        click.Option(["--style"], type=choice(Style), help="the page's look"),
        click.Option(
            ["--review"], type=choice(Review), help="show the answer before it goes"
        ),
        click.Option(
            ["--chromeless"], is_flag=True, help="hide the overlay's title strip"
        ),
        click.Option(
            ["--timeout"],
            type=click.FLOAT,
            default=TIMEOUT,
            help="seconds to wait for the answer",
        ),
        click.Option(
            ["--no-wait"],
            is_flag=True,
            help="open the page and print its id; lem ask wait reads it later",
        ),
        click.Option(
            ["--no-status"], is_flag=True, help="leave the sidebar's status glyph alone"
        ),
        click.Option(
            ["--browser"], is_flag=True, help="open the page in the local browser"
        ),
    ]
