"""`lem criteria read`: the persona read of the criteria: its start, and what it found.

    lem criteria read SLUG start|done|silent --by lem|lead
    lem criteria read SLUG done --by lem --asked N --answered N [--family F]...
        [--silent "PERSONA, FAMILY: WHY"]... --criteria N --flagged N [--split] --digest D

`done` gives what `land` compares before the pull request credits the read (`main`'s
`project.read_form`): the personas asked and answered, each family that answered, each
silent persona and why, the criteria read and flagged, whether the families split, and the
digest of the criteria read (`lem criteria digest`); `start` and `silent` take none of it.
A stub until the step `criteria` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.checks import Given, is_given
from lem.cli.stub import not_built
from lem.cli.words import choice

type Moment = Literal["start", "done", "silent"]
type By = Literal["lem", "lead"]
# What `done` gives, and only `done`.
FOUND = ("asked", "answered", "criteria", "flagged", "digest")
EXTRA = ("families", "silent", "split")


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria read`."""

    slug: str
    moment: Moment
    by: By
    asked: int | None = None
    answered: int | None = None
    families: tuple[str, ...] = ()
    silent: tuple[str, ...] = ()
    criteria: int | None = None
    flagged: int | None = None
    split: bool = False
    digest: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `criteria` builds `lem criteria read`."""
    raise not_built("criteria read", "criteria")


def fitted(given: Given) -> Given:
    """Refuse `done` without what the read found, and `start` or `silent` with any of it."""
    done = given["moment"] == "done"
    named = FOUND if done else (*FOUND, *EXTRA)
    wrong = [name for name in named if is_given(given[name]) != done]
    if wrong:
        flags = ", --".join(wrong)
        rule = "done gives" if done else "only done takes"
        raise click.UsageError(f"{rule} --{flags}", click.get_current_context())
    return given


COMMAND = click.Command(
    "read",
    params=[
        click.Argument(["slug"]),
        click.Argument(["moment"], type=choice(Moment)),
        click.Option(
            ["--by"], required=True, type=choice(By), help="who runs the read"
        ),
        click.Option(["--asked"], type=click.IntRange(0), help="the personas asked"),
        click.Option(
            ["--answered"], type=click.IntRange(0), help="the personas that answered"
        ),
        click.Option(
            ["--family", "families"],
            multiple=True,
            help="a model family that answered, once for each",
        ),
        click.Option(
            ["--silent"],
            multiple=True,
            help='a persona that gave no answer, "PERSONA, FAMILY: WHY", once for each',
        ),
        click.Option(["--criteria"], type=click.IntRange(0), help="the criteria read"),
        click.Option(
            ["--flagged"], type=click.IntRange(0), help="the criteria flagged"
        ),
        click.Option(["--split"], is_flag=True, help="the model families split"),
        click.Option(["--digest"], help="the digest of the criteria read"),
    ],
    callback=lambda **given: run(msgspec.convert(fitted(given), Call)),
    help="The persona read of the criteria: its start, and what it found.",
)
