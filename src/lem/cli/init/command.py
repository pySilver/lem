"""`lem init`: write the team's settings of this repository.

    lem init [--base BRANCH] [--codex yes|no]

An import takes the base from the old file when the owner gives none. A base already in the
team's file stays. With no base in either file or the call, use `origin/HEAD`.
"""

import os
from typing import Literal

import click
import msgspec

from lem.app.init.setup import Initialized, initialized
from lem.cli import place
from lem.cli.words import choice

type Codex = Literal["yes", "no"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem init`."""

    base: str | None = None
    codex: Codex = "yes"


def run(call: Call) -> Initialized:
    """Write the team's settings of the repository of the call."""
    return initialized(place.folder(), call.base, call.codex, os.environ)


COMMAND = click.Command(
    "init",
    params=[
        click.Option(
            ["--base"],
            help="the branch tasks land on (default: the saved base, then origin's default)",
        ),
        click.Option(
            ["--codex"],
            type=choice(Codex),
            default="yes",
            help="whether the machine check found Codex; no puts Claude in the reviewer's seat",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Write the team's settings of this repository.",
)
