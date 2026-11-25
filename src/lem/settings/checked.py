"""The rules of a settings value that its type alone does not hold: a path stays inside the
checkout, a plan's file name holds its slug once, the base is not protected, the compaction
number is one Claude Code takes.
"""

import re
from pathlib import Path
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.settings.machine import Handoff
    from lem.settings.team import Branch, Paths

TOKENS = ("YYYY", "MM", "DD", "<slug>")
UNKNOWN_TOKEN = re.compile(r"<(?!slug>)[^>]*>")


def wrong(where: str, why: str, fix: str) -> Refusal:
    """The refusal of a value its type took and a rule does not."""
    return Refusal("settings", f"{where} {why}", fix)


def inside(checkout: Path, relative: str, where: str) -> Path:
    """The path `relative` names in `checkout`; refused when it is absolute, leaves the
    checkout or is its root, which would read the whole checkout as plans or rulings."""
    fix = "name a folder or a file inside the checkout, or leave the line out for Lem's"
    if Path(relative).is_absolute():
        raise wrong(where, f"= {relative!r} is absolute", fix)
    root = checkout.resolve()
    found = (root / relative).resolve()
    if not found.is_relative_to(root) or found == root:
        raise wrong(where, f"= {relative!r} leaves the checkout or is its root", fix)
    return found


def pattern_flaw(pattern: str) -> str | None:
    """What is wrong with a plan's file name, or None when Lem can use it."""
    if pattern.count("<slug>") != 1:
        return (
            "holds <slug> not once, and a plan of one task is told from another by it"
        )
    if "/" in pattern or "\\" in pattern:
        return "holds a folder; paths.plans names the folder"
    if not pattern.endswith(".md"):
        return "does not end with .md, and a plan is a markdown file"
    if UNKNOWN_TOKEN.search(pattern):
        return "holds a token Lem does not know; it knows YYYY, MM, DD and <slug>"
    twice = [token for token in TOKENS if pattern.count(token) > 1]
    return f"holds {twice[0]} twice" if twice else None


def paths(checkout: Path, given: Paths, name: str) -> None:
    """Refuse a path of `[paths]` Lem cannot use."""
    inside(checkout, given.plans, f"{name}: paths.plans")
    rulings = inside(checkout, given.rulings, f"{name}: paths.rulings")
    if not given.rulings.endswith(".md") or rulings.is_dir():
        raise wrong(
            f"{name}: paths.rulings",
            f"= {given.rulings!r} is no markdown file",
            'name the list file of the owner\'s rulings, as rulings = "docs/rulings.md"',
        )
    flaw = pattern_flaw(given.plan_file)
    if flaw:
        raise wrong(
            f"{name}: paths.plan_file = {given.plan_file!r}",
            flaw,
            'write a file name, as plan_file = "YYYY-MM-DD-<slug>.md"',
        )


def branch(given: Branch, name: str) -> None:
    """Refuse a base that is protected, which no task could land on."""
    if given.base in given.protected:
        raise Refusal(
            "protected",
            f"{name}: branch.base = {given.base!r} is in branch.protected, so no task could land",
            "take the base out of branch.protected",
        )


def handoff(given: Handoff, name: str, floor: int) -> None:
    """Refuse a compaction number under the floor Claude Code takes, but 0."""
    if 0 < given.tokens < floor:
        raise wrong(
            f"{name}: handoff.tokens = {given.tokens}",
            f"is under {floor}, which Claude Code refuses",
            f"write 0 for Claude Code's own trigger, or {floor} or more",
        )
