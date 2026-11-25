"""The files of a task's folder that the map knows by the form of their name: the merge agent's
brief of a tip on a base, a breaker's document, a builder's report, a command's output of the
checks, and the record of the criteria's run on the base."""

import re

from lem.board.views.artifacts.spots import (
    BUILD,
    CHECKS,
    CRITERIA,
    CRITERIA_DOC,
    PR,
    Spot,
)

BRIEF = re.compile(r"merge-brief-([0-9a-f]+)-([0-9a-f]+)\.md")
BREAKER = re.compile(r"breaker-(\d+)\.md")
REPORTS = "reports/"
GATE = "gate/"
OUTPUT = re.compile(r"0*(\d+)\.log")
RED = re.compile(r"red(-.+)?\.json")
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


def gate(path: str) -> Spot | None:
    """The whole output of a command of the checks, `gate/NN.log`."""
    if not path.startswith(GATE):
        return None
    name = path.removeprefix(GATE)
    found = OUTPUT.fullmatch(name)
    title = f"Check {found[1]} output" if found else f"Check output: {name}"
    return Spot(group=CHECKS, title=title)


def red(path: str) -> Spot | None:
    """The record of the criteria's tests run on the base."""
    if RED.fullmatch(path) is None:
        return None
    return Spot(
        group=CRITERIA,
        title="Criteria fail on the base (record)",
        role="record",
        of=CRITERIA_DOC,
        label="red on the base",
        tab=CRITERIA,
    )
