"""A group of `lem` whose commands are module paths, each imported only when a call names it.

Click's documented lazy pattern: the group knows its names and the module of each, and imports
a module when the parser reaches its name, so a call loads one leaf and the tables above it.
"""

import importlib
from typing import TYPE_CHECKING

import click

from lem.kernel.errors import Fault

if TYPE_CHECKING:
    from collections.abc import Sequence

# A table of the tree: each name with the dotted path of the module that holds its `COMMAND`.
type Table = tuple[tuple[str, str], ...]


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
        """The command `cmd_name` names, its module imported now; None for no command."""
        path = dict(self.table).get(cmd_name)
        return None if path is None else loaded(path)

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        """Put the default verb before a first word that is no verb and no help option."""
        first = args[0] if args else None
        known = first in dict(self.table) or first in ctx.help_option_names
        if self.default is not None and not known:
            return super().parse_args(ctx, [self.default, *args])
        return super().parse_args(ctx, args)


def loaded(path: str) -> click.Command:
    """The `COMMAND` of the module at `path`; a module without one is a fault of Lem."""
    command = importlib.import_module(path).COMMAND
    if not isinstance(command, click.Command):
        raise Fault(f"{path}.COMMAND is no click.Command: Lem's package is not whole")
    return command
