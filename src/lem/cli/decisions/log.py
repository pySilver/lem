"""`lem decisions log`: log one decision taken without the owner.

    lem decisions log SLUG --what W --chose C --why Y --by LEVEL ...

A stub until the step `criteria` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type By = Literal["lead", "gate", "personas", "dialectic", "experts", "owner", "lem"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem decisions log`."""

    slug: str
    what: str
    chose: str
    why: str
    by: By
    said: str | None = None
    undo: str | None = None
    options: tuple[str, ...] = ()
    votes: tuple[str, ...] = ()
    levels: tuple[str, ...] = ()
    unsettled: bool = False
    case: str | None = None
    case_was: str | None = None
    cause: str | None = None
    chart: str | None = None
    breaker: int | None = None
    words: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `criteria` builds `lem decisions log`."""
    raise not_built("decisions log", "criteria")


COMMAND = click.Command(
    "log",
    params=[
        click.Argument(["slug"]),
        click.Option(["--what"], required=True, help="what was decided"),
        click.Option(["--chose"], required=True, help="the option chosen"),
        click.Option(["--why"], required=True, help="why"),
        click.Option(
            ["--by"],
            required=True,
            type=choice(By),
            help="the level of the ladder that took it",
        ),
        click.Option(["--said"], help="what the personas answered: who, which option"),
        click.Option(["--undo"], help="what it would take to undo the decision"),
        click.Option(
            ["--option", "options"],
            multiple=True,
            help="an option, word for word, once for each",
        ),
        click.Option(
            ["--vote", "votes"],
            multiple=True,
            help="one persona's answer in one model family",
        ),
        click.Option(
            ["--level", "levels"],
            multiple=True,
            help="what one level of the ladder answered",
        ),
        click.Option(
            ["--unsettled"],
            is_flag=True,
            help="with --by lead: no level settled it, and the lead's pick stands",
        ),
        click.Option(
            ["--case"], help="one concrete run in numbered steps, one to a line"
        ),
        click.Option(["--case-was"], help="reproduced, or derived from the code"),
        click.Option(
            ["--cause"],
            help="why the case became possible, and how far the cause reaches",
        ),
        click.Option(
            ["--chart"], help="a file that holds one mermaid chart of the decision"
        ),
        click.Option(
            ["--breaker"], type=click.INT, help="with --by owner: his help on breaker N"
        ),
        click.Option(["--words"], help="with --by owner: his words as given"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Log one decision taken without the owner.",
)
