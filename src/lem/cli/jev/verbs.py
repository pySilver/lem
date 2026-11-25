"""The verbs of `lem jev`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (
    ("ask", "lem.cli.jev.ask"),
    ("check", "lem.cli.jev.check"),
)

COMMAND = LazyGroup(
    "jev",
    "The Jev model: choice and yes/no questions, answered as JSON.",
    VERBS,
    default="ask",
)
