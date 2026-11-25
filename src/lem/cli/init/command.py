"""`lem init`: write the team's settings of this repository.

    lem init --base BRANCH [--codex yes|no]

A stub until the step `settings` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type Codex = Literal["yes", "no"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem init`."""

    base: str
    codex: Codex | None = None


def run(call: Call) -> None:
    """Refuse until the step `settings` builds `lem init`."""
    raise not_built("init", "settings")


COMMAND = click.Command(
    "init",
    params=[
        click.Option(["--base"], required=True, help="the branch tasks land on"),
        click.Option(
            ["--codex"],
            type=choice(Codex),
            help="whether the machine check found Codex; no puts Claude in the reviewer's seat",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Write the team's settings of this repository.",
)
