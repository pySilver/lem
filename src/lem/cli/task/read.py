"""`lem task read`: record the read of a request: type, track and what comes next.

    lem task read SLUG --type T --why W --track small|full ...

The read replaces the fixed lines of a request (`type:`, `then:`, `careful:`, `after:`, the
owner's order); `--fits` says the owner's words fit one open task, `--someone-else` that someone
else wrote the request (`model/task/read.py`). Its `say` is the task's first line.
"""

from typing import Literal

import click
import msgspec

from lem.app.tasks import shape as shaping
from lem.cli import place
from lem.cli.words import choice
from lem.kernel.envelope import Envelope
from lem.model.task.read import Queue, Wait
from lem.records.task import Shape

type Kind = Literal[
    "feat", "fix", "docs", "refactor", "perf", "test", "chore", "question"
]
type Track = Literal["small", "full"]
type Then = Literal["interview", "fast", "lead", "investigation"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task read`."""

    slug: str
    kind: Kind
    why: str
    track: Track
    careful: tuple[str, ...] = ()
    then: Then | None = None
    order: str | None = None
    after: tuple[str, ...] = ()
    wait: Wait | None = None
    fits: bool = False
    someone_else: bool = False


def run(call: Call) -> Envelope:
    """Record the read of the request, its queue and its wait; say the first line."""
    shape = Shape(
        type=call.kind,
        why=call.why,
        track=call.track,
        careful=call.careful,
        then=call.then,
        fits=call.fits,
        someone_else=call.someone_else,
    )
    queue = Queue(after=call.after, order=call.order, wait=call.wait)
    record = shaping.shaped(place.folder(), call.slug, shape, queue)
    outcome = msgspec.Raw(msgspec.json.encode(record.task.shape))
    say = shaping.said(place.folder(), record)
    return Envelope(ok=True, outcome=outcome, say=say)


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
        click.Option(
            ["--after"],
            multiple=True,
            help="a task this one waits for, once for each; it waits for all of them",
        ),
        click.Option(["--wait"], type=choice(Wait), help="what waits for the owner"),
        click.Option(
            ["--fits"],
            is_flag=True,
            help="the owner's words fit the one open task --after names",
        ),
        click.Option(
            ["--someone-else"],
            is_flag=True,
            help="someone else wrote the request: its criterion waits for his yes",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Record the read of a request: type, track and what comes next.",
)
