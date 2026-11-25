"""`lem decisions criterion`: log the change of one criterion in the build.

    lem decisions criterion SLUG (--changed N|--added N|--removed N) --why WHY ...

A stub until the step `criteria` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

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


def run(call: Call) -> None:
    """Refuse until the step `criteria` builds `lem decisions criterion`."""
    raise not_built("decisions criterion", "criteria")


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
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Log the change of one criterion in the build.",
)
