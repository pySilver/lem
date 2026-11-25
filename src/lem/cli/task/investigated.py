"""`lem task investigated`: what the investigation of a bug or a question found.

    lem task investigated SLUG --kind fix|question --call CALL --line TEXT
        [--result R] [--where PATH:SYMBOL] [--reproduced|--not-reproduced]

The form of `main`'s `project.investigation_form`: a fix's call is `small`, `full`,
`not-a-bug` or `not-reproduced`, a question's is `answer`, and only a fix says whether the bug
was reproduced. A fix needs `--reproduced` or `--not-reproduced`, a plain cause (`small`,
`full`) its `--where`, and `not-reproduced` waits for one more fact from the owner
(`model/task/investigation.py`).
"""

from typing import TYPE_CHECKING, Literal

import click
import msgspec

from lem.app.tasks import investigated
from lem.cli import place
from lem.cli.words import choice
from lem.model.task.investigation import Findings
from lem.store import places

if TYPE_CHECKING:
    from lem.cli.checks import Given
    from lem.records.work import Investigation

type Kind = Literal["fix", "question"]
type Found = Literal["bug", "none", "question", "unreproduced"]
type Track = Literal["small", "full", "not-a-bug", "not-reproduced", "answer"]
# The calls of a question; every other call is a fix's.
ANSWERS = ("answer",)


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task investigated`."""

    slug: str
    kind: Kind
    call: Track
    line: str
    found: Found | None = None
    where: str | None = None
    reproduced: bool | None = None


def run(call: Call) -> Investigation:
    """Write what the investigation found."""
    state = places.workspace(place.folder()).state
    given = Findings(
        kind=call.kind,
        call=call.call,
        line=call.line,
        found=call.found,
        where=call.where,
        reproduced=call.reproduced,
    )
    return investigated.investigated(state, call.slug, given)


def fitted(given: Given) -> Given:
    """Refuse a call that is not of its kind, and a question that says it reproduced."""
    question = given["kind"] == "question"
    if (given["call"] in ANSWERS) != question:
        why = "a fix's call is small, full, not-a-bug or not-reproduced; a question's is answer"
        raise click.UsageError(why, click.get_current_context())
    if question and given["reproduced"] is not None:
        why = "--reproduced and --not-reproduced are a fix's: a question reproduces nothing"
        raise click.UsageError(why, click.get_current_context())
    return given


COMMAND = click.Command(
    "investigated",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--kind"], required=True, type=choice(Kind), help="a fix or a question"
        ),
        click.Option(
            ["--call"],
            required=True,
            type=choice(Track),
            help="what comes next: a track for a fix, the answer for a question",
        ),
        click.Option(
            ["--line"],
            required=True,
            help="one line: the cause, the answer, or what was tried",
        ),
        click.Option(
            ["--result", "found"],
            type=choice(Found),
            help="what the investigation found",
        ),
        click.Option(["--where"], help="the cause's place, PATH:SYMBOL"),
        click.Option(
            ["--reproduced/--not-reproduced"],
            default=None,
            help="a fix: whether the bug was reproduced",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(fitted(given), Call)),
    help="What the investigation of a bug or a question found.",
)
