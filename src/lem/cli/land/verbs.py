"""The verbs of `lem land`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (
    ("start", "lem.cli.land.start"),
    ("base", "lem.cli.land.base"),
    ("polish", "lem.cli.land.polish"),
    ("alike", "lem.cli.land.alike"),
    ("checks", "lem.cli.land.checks"),
    ("read", "lem.cli.land.read"),
    ("file", "lem.cli.land.file"),
    ("propose", "lem.cli.land.propose"),
    ("merge-review", "lem.cli.land.merge_review"),
    ("merge", "lem.cli.land.merge"),
    ("merged", "lem.cli.land.merged"),
    ("clean", "lem.cli.land.clean"),
    ("next", "lem.cli.land.next"),
)

COMMAND = LazyGroup(
    "land",
    "The landing, one step at a time, from the checks to the merge and the cleanup.",
    VERBS,
)
