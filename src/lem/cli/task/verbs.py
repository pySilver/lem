"""The verbs of `lem task`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (
    ("open", "lem.cli.task.open"),
    ("dir", "lem.cli.task.dir"),
    ("worktree", "lem.cli.task.worktree"),
    ("plan-file", "lem.cli.task.plan_file"),
    ("move", "lem.cli.task.move"),
    ("red-base", "lem.cli.task.red_base"),
    ("read", "lem.cli.task.read"),
    ("span", "lem.cli.task.span"),
    ("planned", "lem.cli.task.planned"),
    ("list", "lem.cli.task.list"),
    ("show", "lem.cli.task.show"),
    ("park", "lem.cli.task.park"),
    ("resume", "lem.cli.task.resume"),
    ("ticket", "lem.cli.task.ticket"),
    ("investigated", "lem.cli.task.investigated"),
    ("talked", "lem.cli.task.talked"),
    ("may-start", "lem.cli.task.may_start"),
    ("start", "lem.cli.task.start"),
    ("build", "lem.cli.task.build"),
    ("keep-item", "lem.cli.task.keep_item"),
)

COMMAND = LazyGroup(
    "task",
    "A task: its record, its state, its queue, its worktree and its ticket.",
    VERBS,
)
