"""The verbs of `lem serve`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (
    ("ensure", "lem.cli.serve.ensure"),
    ("stop", "lem.cli.serve.stop"),
    ("run", "lem.cli.serve.run"),
    ("door", "lem.cli.serve.door"),
    ("add", "lem.cli.serve.add"),
    ("remove", "lem.cli.serve.remove"),
    ("list", "lem.cli.serve.list"),
    ("push-test", "lem.cli.serve.push_test"),
    ("join", "lem.cli.serve.join"),
    ("leave", "lem.cli.serve.leave"),
    ("peers", "lem.cli.serve.peers"),
)

COMMAND = LazyGroup(
    "serve",
    "The board server of this machine, its door, its workspaces and its peers.",
    VERBS,
)
