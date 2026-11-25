"""`lem decisions criterion`: log the change of one criterion in the build.

    lem decisions criterion SLUG (--changed N|--added N|--removed N) --why WHY ...

N is the criterion's number in the criteria as they stand after every earlier change (`lem
decisions changes SLUG` gives them); `--was` and `--now` are its whole text, its sentence and the
steps of its case, word for word. `--decision` names the decision of the record that led to the
change; without one, `--by lead` is the lead's own change and `--by personas` the personas' clear
pick, with `--said`.
"""

from typing import Literal

import click
import msgspec

from lem.app.decisions import criterion
from lem.cli import place
from lem.cli.checks import exactly_one
from lem.cli.words import choice
from lem.model.decisions.criterion import Asked

type By = Literal["lead", "personas"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem decisions criterion`."""

    slug: str
    changed: int | None = None
    added: int | None = None
    removed: int | None = None
    was: str | None = None
    now: str | None = None
    why: str
    decision: int | None = None
    by: By | None = None
    said: str | None = None


def asked_of(call: Call) -> Asked:
    """The change the words give."""
    if call.changed is not None:
        how, number = "changed", call.changed
    elif call.added is not None:
        how, number = "added", call.added
    else:
        how, number = "removed", call.removed or 0
    return Asked(
        how=how,
        number=number,
        was=call.was,
        now=call.now,
        why=call.why,
        decision=call.decision,
        by=call.by,
        said=call.said,
    )


def run(call: Call) -> criterion.Criteria:
    """Write the change, and give the criteria as they stand after it."""
    return criterion.recorded(place.folder(), call.slug, asked_of(call))


COMMAND = click.Command(
    "criterion",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--changed"],
            type=click.INT,
            help="criterion N changed: --was before, --now after",
        ),
        click.Option(
            ["--added"],
            type=click.INT,
            help="a criterion added at number N, with --now its text",
        ),
        click.Option(
            ["--removed"],
            type=click.INT,
            help="criterion N leaves the criteria, with --was its text",
        ),
        click.Option(
            ["--was"], help="the criterion's text before the change, word for word"
        ),
        click.Option(
            ["--now"], help="the criterion's text after the change, word for word"
        ),
        click.Option(
            ["--why"], required=True, help="why the criterion changed, in one sentence"
        ),
        click.Option(
            ["--decision"],
            type=click.INT,
            help="the decision of the record that led to the change",
        ),
        click.Option(
            ["--by"], type=choice(By), help="who changed it, when no decision did"
        ),
        click.Option(
            ["--said"], help="with --by personas: who answered and what each picked"
        ),
    ],
    callback=lambda **given: run(
        msgspec.convert(exactly_one(given, "changed", "added", "removed"), Call)
    ),
    help="Log the change of one criterion in the build.",
)
