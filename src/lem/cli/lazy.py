"""The command tree of `lem`, each command loaded only when it runs.

`lem NOUN VERB ARGS...`: the nouns are in `nouns.py`, each noun's verbs in its own `verbs.py`,
and each verb is a leaf module of its own. A leaf's outcome is printed as the envelope
(`output.py`): exit 0 done, 1 a refusal, 2 a wrong call (Click's own, on standard error), 3 a
fault, whose traceback goes to `lem.log`. `help` and `version` print text and JSON of their
own, with no envelope; `lem` alone is `lem help`.
"""

import logging

import click

from lem.cli import faults, nouns, output, usage, version
from lem.cli.group import LazyGroup
from lem.kernel.errors import Refusal

ROOT = LazyGroup(
    "lem",
    "Lem coordinates the agents that write code in one repository.",
    nouns.NOUNS,
    eager=(usage.COMMAND, version.COMMAND),
)


def main(argv: list[str]) -> int:
    """Run the command `argv` names, print its envelope, and give its exit code."""
    try:
        return clicked(argv or ["help"])
    except Refusal as refusal:
        return output.refused(refusal)
    except Exception as error:
        with faults.logged() as where:
            logging.getLogger(faults.LOGGER).exception("a fault of Lem")
            return output.failed(faults.line(error), where)


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
