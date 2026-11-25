"""The verbs of `lem proposals`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (
    ("list", "lem.cli.proposals.list"),
    ("add", "lem.cli.proposals.add"),
    ("verdict", "lem.cli.proposals.verdict"),
    ("drop", "lem.cli.proposals.drop"),
)

COMMAND = LazyGroup(
    "proposals",
    "The night's and the retro's proposals, the reviewer's verdicts, his drop.",
    VERBS,
)
