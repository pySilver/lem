"""The verbs of `lem nap`, each with the leaf module that holds its command."""

from lem.cli.group import LazyGroup

VERBS = (("may", "lem.cli.nap.may"),)

COMMAND = LazyGroup("nap", "The naps: whether one may start now.", VERBS)
