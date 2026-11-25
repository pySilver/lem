"""The verbs of `lem settings`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (
    ("show", "lem.cli.settings.show"),
    ("set", "lem.cli.settings.set"),
)

COMMAND = LazyGroup(
    "settings",
    "Lem's settings, each value with the file it comes from, and their edits.",
    VERBS,
)
