"""The verbs of `lem experts`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (
    ("brief", "lem.cli.experts.brief"),
    ("record", "lem.cli.experts.record"),
)

COMMAND = LazyGroup(
    "experts",
    "The experts' brief of one question, and the record of their answers.",
    VERBS,
)
