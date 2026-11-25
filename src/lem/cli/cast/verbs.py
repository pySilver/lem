"""The verbs of `lem cast`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (
    ("show", "lem.cli.cast.show"),
    ("init", "lem.cli.cast.init"),
    ("run-dir", "lem.cli.cast.run_dir"),
)

COMMAND = LazyGroup(
    "cast",
    "The persona panel's cast, and a panel's run folder.",
    VERBS,
    default="show",
)
