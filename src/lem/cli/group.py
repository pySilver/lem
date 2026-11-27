"""A group of `lem` whose commands are module paths, each imported only when a call names it.

Click's documented lazy pattern: the group knows its names and the module of each, and imports
a module when the parser reaches its name, so a call loads one leaf and the tables above it.
"""

import importlib
from pathlib import Path
from typing import TYPE_CHECKING

import click

from lem.cli import listing
from lem.kernel.errors import Fault, Refusal

if TYPE_CHECKING:
    from collections.abc import Sequence

# A table of the tree: each name with the dotted path of the module that holds its `COMMAND`.
type Table = tuple[tuple[str, str], ...]
# The package of the tree, `lem/cli`, where a module of a table has its file.
PACKAGE = Path(__file__).resolve().parent


class LazyGroup(click.Group):
    """A noun of `lem`, or `lem` itself: its names in a table, each module loaded on a call.

    `default` names the verb a call takes when its first word is no verb and no help option,
    as `lem ask SPEC` is `lem ask ask SPEC`.
    """

    def __init__(
        self,
        name: str,
        about: str,
        table: Table,
        *,
        default: str | None = None,
        options: Sequence[click.Parameter] = (),
    ) -> None:
        """Keep the table, the verb a call with no verb takes, and the group's own options."""
        super().__init__(
            name,
            params=list(options),
            help=about,
            context_settings={"help_option_names": ["-h", "--help"]},
        )
        self.table = table
        self.default = default

    def list_commands(self, ctx: click.Context) -> list[str]:
        """The names in the table's order."""
        return [name for name, _ in self.table]

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """The command `cmd_name` names, its module imported now; None for no command. A
        command that is no group puts its repository on the machine's list first
        (`listing.py`)."""
        path = dict(self.table).get(cmd_name)
        if path is None:
            return None
        command = loaded(path)
        if isinstance(command, click.Group):
            return command
        return listing.first(cmd_name, command)

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        """Put the default verb before a first word that is no verb and no help option."""
        first = args[0] if args else None
        known = first in dict(self.table) or first in ctx.help_option_names
        if self.default is not None and not known:
            return super().parse_args(ctx, [self.default, *args])
        return super().parse_args(ctx, args)


def loaded(path: str) -> click.Command:
    """The `COMMAND` of the module at `path`; a module without one is a fault of Lem, and a
    module the table names that is not there is a package to install again."""
    try:
        module = importlib.import_module(path)
    except ModuleNotFoundError as error:
        named = error.name or ""
        if path != named and not path.startswith(f"{named}."):
            raise
        raise not_whole(path) from error
    command = module.COMMAND
    if not isinstance(command, click.Command):
        raise Fault(f"{path}.COMMAND is no click.Command: Lem's package is not whole")
    return command


def not_whole(path: str) -> Refusal:
    """The refusal of a command whose module is not in the package: the file, and the repair."""
    parts = path.split(".")[2:]
    missing = PACKAGE.joinpath(*parts).with_suffix(".py")
    return Refusal(
        "not-whole",
        f"{missing} is not there: Lem's package {PACKAGE.parent} is not whole",
        "the owner installs Lem again",
    )
