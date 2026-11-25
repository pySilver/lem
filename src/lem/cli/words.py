"""What the leaves of the tree share in how they read their words."""

from typing import TypeAliasType, get_args

import click


def choice(alias: TypeAliasType) -> click.Choice:
    """Click's choice of the values of a `type X = Literal[...]` alias, in their order."""
    return click.Choice(get_args(alias.__value__))
