"""The verbs of `lem owner`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (
    ("away", "lem.cli.owner.away"),
    ("back", "lem.cli.owner.back"),
    ("watch", "lem.cli.owner.watch"),
)

COMMAND = LazyGroup(
    "owner", "The owner's presence: away, back, and the watch for his next word.", VERBS
)
