"""The command tree of `lem`, each command loaded only when it runs.

`lem NOUN VERB ARGS...`: the nouns are in `nouns.py`, each noun's verbs in its own `verbs.py`,
and each verb is a leaf module of its own. A leaf's outcome is printed as the envelope
(`output.py`): exit 0 done, 1 a refusal, 2 a wrong call (Click's own, on standard error), 3 a
fault, whose traceback goes to `lem.log` (`faults.py`, loaded only on a fault). `help` and
`version` print text and JSON of their own, with no envelope; `lem` alone is `lem help`.
"""

import importlib

import click

from lem.cli import nouns, output
from lem.cli.group import LazyGroup
from lem.kernel.errors import Fault, Refusal

# The two commands of `lem` itself, after the nouns, each loaded only when a call names it.
OWN = (
    ("help", "lem.cli.usage"),
    ("version", "lem.cli.version"),
)
ROOT = LazyGroup(
    "lem",
    "Lem coordinates the agents that write code in one repository.",
    (*nouns.NOUNS, *OWN),
)


def main(argv: list[str]) -> int:
    """Run the command `argv` names, print its envelope, and give its exit code."""
    try:
        return contained(argv or ["help"])
    except Fault as fault:
        logged = importlib.import_module("lem.cli.faults").logged(fault)
        return output.failed(*logged)


def contained(argv: list[str]) -> int:
    """Run the call: a refusal is printed, and any other failure becomes a `Fault`."""
    try:
        return clicked(argv)
    except Refusal as refusal:
        return output.refused(refusal)
    except Exception as error:
        kind = type(error).__name__
        said = " ".join(str(error).split())
        raise Fault(f"Lem failed: {kind}: {said}") from error


def clicked(argv: list[str]) -> int:
    """Parse `argv` and run its command; a wrong call or a help is Click's own."""
    try:
        with ROOT.make_context("lem", list(argv)) as ctx:
            outcome = ROOT.invoke(ctx)
    except click.exceptions.Exit as ended:
        return ended.exit_code
    except click.ClickException as wrong:
        wrong.show()
        return wrong.exit_code
    return output.done(outcome)
