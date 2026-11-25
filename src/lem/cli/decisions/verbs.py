"""The verbs of `lem decisions`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (
    ("log", "lem.cli.decisions.log"),
    ("criterion", "lem.cli.decisions.criterion"),
    ("changes", "lem.cli.decisions.changes"),
    ("breaker", "lem.cli.decisions.breaker"),
    ("pending", "lem.cli.decisions.pending"),
    ("list", "lem.cli.decisions.list"),
)

COMMAND = LazyGroup(
    "decisions",
    "A task's decisions, each taken without the owner, and its breakers.",
    VERBS,
)
