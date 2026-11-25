"""The verbs of `lem criteria`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (
    ("approve", "lem.cli.criteria.approve"),
    ("approved", "lem.cli.criteria.approved"),
    ("change", "lem.cli.criteria.change"),
    ("digest", "lem.cli.criteria.digest"),
    ("show", "lem.cli.criteria.show"),
    ("record", "lem.cli.criteria.record"),
    ("red", "lem.cli.criteria.red"),
    ("inputs", "lem.cli.criteria.inputs"),
    ("read", "lem.cli.criteria.read"),
    ("skip", "lem.cli.criteria.skip"),
)

COMMAND = LazyGroup(
    "criteria",
    "A task's acceptance criteria: approve, change, show, and red on the base.",
    VERBS,
)
