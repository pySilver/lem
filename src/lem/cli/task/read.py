"""`lem task read`: record the read of a request: type, track and what comes next.

    lem task read SLUG --type T --why W --track small|full ...

The plain form of the fast track, as the step `slice-land` built it; the step `task` owns it.
"""

from typing import Literal

import click
import msgspec

from lem.app.tasks import shape as shaping
from lem.cli import place
from lem.cli.stub import not_built
from lem.cli.words import choice
from lem.records.task import Shape

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


def run(call: Call) -> Shape:
    """Record the read of the request; a queue and a wait are the step `task`'s."""
    if call.order or call.after or call.wait:
        raise not_built("task read --order|--after|--wait", "task")
    shape = Shape(
        type=call.kind,
        why=call.why,
        track=call.track,
        careful=call.careful,
        then=call.then,
    )
    return shaping.shaped(place.folder(), call.slug, shape)


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
