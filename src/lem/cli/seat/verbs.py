"""The verbs of `lem seat`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (
    ("show", "lem.cli.seat.show"),
    ("failed", "lem.cli.seat.failed"),
    ("again", "lem.cli.seat.again"),
)

COMMAND = LazyGroup(
    "seat",
    "The seat a task's role takes, the fallback that stands in, and the way back.",
    VERBS,
)
