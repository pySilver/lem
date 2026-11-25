"""`lem decisions log`: log one decision taken without the owner.

    lem decisions log SLUG --what W --chose C --why Y --by LEVEL ...

`--why` holds the gate's cite, `--said` what the personas answered. `--option` is each option the
decision had, "LABEL: what the person sees after it", `--vote` each persona's answer, "PERSONA,
FAMILY=OPTION", one for each model family, and `--level` what each level that ran answered,
"NAME=ANSWER". `--by personas` takes two votes or more, each for the option `--chose` names;
`--unsettled` goes with `--by lead`. `owner` is a word of the owner's: his help on breaker N
(`--breaker N`, which settles it, with his words in `--words`), a word nobody asked for, or his
yes to skip the personas' read; `lem` one that Lem took before the task had a lead. An important
decision, `--by dialectic`, `--by experts` or `--unsettled`, carries its story: `--case`,
`--case-was` and `--cause`, which any other decision may carry too. `--chart FILE` is one
mermaid chart, its flowchart texts in double quotes.
"""

from typing import TYPE_CHECKING, Literal

import click
import msgspec

from lem.app.decisions import bound
from lem.app.decisions import log as logging
from lem.cli import place
from lem.cli.words import choice
from lem.model.decisions.log import Logged
from lem.store import places

if TYPE_CHECKING:
    from lem.records.decisions import Taken

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


def logged_of(call: Call) -> Logged:
    """The decision the words give."""
    return Logged(
        what=call.what,
        chose=call.chose,
        why=call.why,
        by=call.by,
        said=call.said,
        undo=call.undo,
        options=call.options,
        votes=call.votes,
        levels=call.levels,
        unsettled=call.unsettled,
        story=(call.case, call.case_was, call.cause),
        breaker=call.breaker,
        words=call.words,
    )


def run(call: Call) -> Taken:
    """Write the decision, with the number the record gives it."""
    folder = place.folder()
    ports = bound.ports_of(places.workspace(folder).checkout)
    return logging.logged(ports, folder, call.slug, logged_of(call), call.chart)


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
