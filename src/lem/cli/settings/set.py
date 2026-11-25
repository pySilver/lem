"""`lem settings set`: write one setting into the local, home or machine file.

    lem settings set KEY VALUE --local|--home|--machine

Exactly one of the three files, by its switch. A stub until the step `settings` builds it: it
refuses `not-built`.
"""

import click
import msgspec

from lem.cli.checks import exactly_one
from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem settings set`."""

    key: str
    setting: str
    local: bool = False
    home: bool = False
    machine: bool = False


def run(call: Call) -> None:
    """Refuse until the step `settings` builds `lem settings set`."""
    raise not_built("settings set", "settings")


COMMAND = click.Command(
    "set",
    params=[
        click.Argument(["key"]),
        click.Argument(["setting"]),
        click.Option(
            ["--local"],
            is_flag=True,
            help="this repository on this machine: .lem/settings.local.toml",
        ),
        click.Option(
            ["--home"],
            is_flag=True,
            help="every repository of the developer: Lem's home settings.toml",
        ),
        click.Option(
            ["--machine"], is_flag=True, help="this machine: Lem's home machine.toml"
        ),
    ],
    callback=lambda **given: run(
        msgspec.convert(exactly_one(given, "local", "home", "machine"), Call)
    ),
    help="Write one setting into the local, home or machine file.",
)
