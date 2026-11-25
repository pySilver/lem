"""The verbs of `lem session`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (
    ("open", "lem.cli.session.open"),
    ("next", "lem.cli.session.next"),
    ("close", "lem.cli.session.close"),
    ("close-job", "lem.cli.session.close_job"),
    ("handoff", "lem.cli.session.handoff"),
    ("talk", "lem.cli.session.talk"),
    ("wake", "lem.cli.session.wake"),
    ("stopped", "lem.cli.session.stopped"),
    ("worked", "lem.cli.session.worked"),
    ("wait", "lem.cli.session.wait"),
    ("list", "lem.cli.session.list"),
    ("plugin-dir", "lem.cli.session.plugin_dir"),
)

COMMAND = LazyGroup(
    "session",
    "A task's own session in agterm: open, next, close, wake, wait and its handoff.",
    VERBS,
)
