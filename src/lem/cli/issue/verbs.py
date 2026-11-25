"""The verbs of `lem issue`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (
    ("check", "lem.cli.issue.check"),
    ("read", "lem.cli.issue.read"),
    ("start", "lem.cli.issue.start"),
    ("land", "lem.cli.issue.land"),
    ("drop", "lem.cli.issue.drop"),
    ("answer", "lem.cli.issue.answer"),
)

COMMAND = LazyGroup(
    "issue",
    "The GitHub tracker: check, read an issue, and a task's steps on its issue.",
    VERBS,
)
