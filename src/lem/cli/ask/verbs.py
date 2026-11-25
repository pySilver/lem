"""The verbs of `lem ask`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (
    ("ask", "lem.cli.ask.ask"),
    ("q", "lem.cli.ask.quick"),
    ("wait", "lem.cli.ask.wait"),
    ("close", "lem.cli.ask.close"),
    ("demo", "lem.cli.ask.demo"),
    ("templates", "lem.cli.ask.templates"),
    ("render", "lem.cli.ask.render"),
)

COMMAND = LazyGroup(
    "ask",
    "The question page: one question to the owner as a page in agterm.",
    VERBS,
    default="ask",
)
