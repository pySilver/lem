"""`lem settings set`: write one setting into the local, home or machine file.

    lem settings set KEY VALUE --local|--home|--machine

Exactly one of the three files, by its switch; `default` takes the line out. No command writes
the team's file. The edit's library loads only when a setting is written (`settings/write.py`).
"""

import importlib
import os

import click
import msgspec

from lem.cli import place
from lem.cli.checks import exactly_one
from lem.settings.places import Scope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem settings set`."""

    key: str
    setting: str
    local: bool = False
    home: bool = False
    machine: bool = False


def run(call: Call) -> object:
    """Write the setting into the file the call's switch names."""
    scope = next(one for one in Scope if getattr(call, one.value, False))
    writer = importlib.import_module("lem.settings.write")
    asked = writer.Asked(
        key=call.key,
        word=call.setting,
        scope=scope,
        folder=place.folder(),
        environ=os.environ,
    )
    return writer.set_setting(asked)


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
