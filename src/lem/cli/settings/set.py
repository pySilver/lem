"""`lem settings set`: write one setting into the local, home or machine file.

    lem settings set KEY VALUE --local|--home|--machine

A stub until the step `settings` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built

type Scope = Literal["local", "home", "machine"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem settings set`."""

    key: str
    setting: str
    scope: Scope | None = None


def run(call: Call) -> None:
    """Refuse until the step `settings` builds `lem settings set`."""
    raise not_built("settings set", "settings")


COMMAND = click.Command(
    "set",
    params=[
        click.Argument(["key"]),
        click.Argument(["setting"]),
        click.Option(
            ["--local", "scope"],
            flag_value="local",
            help="this repository on this machine: .lem/settings.local.toml",
        ),
        click.Option(
            ["--home", "scope"],
            flag_value="home",
            help="every repository of the developer: Lem's home settings.toml",
        ),
        click.Option(
            ["--machine", "scope"],
            flag_value="machine",
            help="this machine: Lem's home machine.toml",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Write one setting into the local, home or machine file.",
)
