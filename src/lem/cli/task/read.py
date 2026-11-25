"""`lem task read`: record the read of a request: type, track and what comes next.

    lem task read SLUG --type T --why W --track small|full ...

A stub until the step `slice-land` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type Kind = Literal[
    "feat", "fix", "docs", "refactor", "perf", "test", "chore", "question"
]
type Track = Literal["small", "full"]
type Then = Literal["interview", "fast", "lead", "investigation"]
type Wait = Literal["criteria", "interview"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task read`."""

    slug: str
    kind: Kind
    why: str
    track: Track
    careful: tuple[str, ...] = ()
    then: Then | None = None
    order: str | None = None
    after: str | None = None
    wait: Wait | None = None


def run(call: Call) -> None:
    """Refuse until the step `slice-land` builds `lem task read`."""
    raise not_built("task read", "slice-land")


COMMAND = click.Command(
    "read",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--type", "kind"],
            required=True,
            type=choice(Kind),
            help="the type of the change",
        ),
        click.Option(
            ["--why"], required=True, help="why it is of that type, in one line"
        ),
        click.Option(
            ["--track"],
            required=True,
            type=choice(Track),
            help="the fast track or the standard track",
        ),
        click.Option(
            ["--careful"], multiple=True, help="a topic that needs care, once for each"
        ),
        click.Option(["--then"], type=choice(Then), help="what comes next"),
        click.Option(["--order"], help="the owner's order, in his words"),
        click.Option(["--after"], help="the task this one waits for"),
        click.Option(["--wait"], type=choice(Wait), help="what waits for the owner"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Record the read of a request: type, track and what comes next.",
)
