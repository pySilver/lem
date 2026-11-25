"""`lem criteria read`: the persona read of the criteria: its start, and what it found.

    lem criteria read SLUG start|done|silent --by lem|lead
    lem criteria read SLUG done --by lem --asked N --answered N [--family F]...
        [--silent "PERSONA, FAMILY: WHY"]... --criteria N --flagged N [--split] --digest D

`done` gives what `land` compares before the pull request credits the read (`main`'s
`project.read_form`): the personas asked and answered, each family that answered, each
silent persona and why, the criteria read and flagged, whether the families split, and the
digest of the criteria read (`lem criteria digest`); `start` and `silent` take none of it.
`silent` ends the read that started as one in which nobody answered, for a panel that gave
nothing to count.
"""

from typing import TYPE_CHECKING, Literal

import click
import msgspec

from lem.app.criteria import persona
from lem.cli import place
from lem.cli.checks import Given, is_given
from lem.cli.words import choice
from lem.model.criteria import reads

if TYPE_CHECKING:
    from lem.records.approvals import PersonaRead

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


def found_of(call: Call) -> reads.Found | None:
    """What a `done` read found, or None for its start and its silence."""
    if call.moment != "done" or call.digest is None:
        return None
    return reads.Found(
        asked=call.asked or 0,
        answered=call.answered or 0,
        families=call.families,
        silent=tuple(reads.silent_of(said) for said in call.silent),
        criteria=call.criteria or 0,
        flagged=call.flagged or 0,
        split=call.split,
        digest=call.digest,
    )


def run(call: Call) -> PersonaRead:
    """Write the read's start, what it found, or its silence."""
    return persona.noted(
        place.folder(), call.slug, (call.moment, call.by), found_of(call)
    )


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
