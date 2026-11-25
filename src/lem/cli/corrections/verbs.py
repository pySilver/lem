"""The verbs of `lem corrections`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (
    ("list", "lem.cli.corrections.list"),
    ("lessons", "lem.cli.corrections.lessons"),
    ("worker", "lem.cli.corrections.worker"),
    ("show", "lem.cli.corrections.show"),
    ("record", "lem.cli.corrections.record"),
)

COMMAND = LazyGroup(
    "corrections", "The queue of the owner's corrections, for a retro.", VERBS
)
