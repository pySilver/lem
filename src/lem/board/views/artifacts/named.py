"""The files of a task's folder that the map knows by the form of their name: the merge agent's
brief of a tip on a base, a breaker's document, a builder's report (`reports/NN-TASK.md`,
`stages/build.md`), and a command's output of the checks."""

import re

from lem.board.views.artifacts.spots import BUILD, CHECKS, PR, Spot

BRIEF = re.compile(r"merge-brief-([0-9a-f]+)-([0-9a-f]+)(?:-\d+(?:-\d+)?)?\.md")
BREAKER = re.compile(r"breaker-(\d+)\.md")
REPORTS = "reports/"
# A command's output as the checks publish it (`app/landing/checks_run.py`): its round, its
# place in `checks.commands`, and the digest of its bytes.
OUTPUT = re.compile(r"checks/r(\d+)-(\d+)-[0-9a-f]+\.log")
# The short form of a commit in the brief's title.
SHORT = 9


def brief(path: str) -> Spot | None:
    """The merge agent's brief of one proposed tip on one base."""
    found = BRIEF.fullmatch(path)
    if found is None:
        return None
    tip = found[1][:SHORT]
    base = found[2][:SHORT]
    return Spot(group=PR, title=f"The merge agent's brief of {tip} on {base}")


def breaker(path: str) -> Spot | None:
    """The document of breaker N."""
    found = BREAKER.fullmatch(path)
    if found is None:
        return None
    return Spot(group=BUILD, title=f"What stopped the build: breaker {found[1]}")


def report(path: str) -> Spot | None:
    """A builder's report under `reports/`."""
    if not path.startswith(REPORTS) or not path.lower().endswith(".md"):
        return None
    name = path.removeprefix(REPORTS)[: -len(".md")]
    return Spot(group=BUILD, title=f"Report: {name}")


def check_output(path: str) -> Spot | None:
    """The whole output of a command of the checks, `checks/rROUND-PLACE-DIGEST.log`."""
    found = OUTPUT.fullmatch(path)
    if found is None:
        return None
    round_of, place = found[1], found[2]
    return Spot(group=CHECKS, title=f"Check {place} output, round {round_of}")
