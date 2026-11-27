"""Every step that takes a task's step lock is named in its refusals by a command the tree of `lem`
takes (`store/step_refusals.command`): each call of `steps.step` and `steps.waited` in Lem's code
names its step by a verb of the landing or by a module's `STEP`, and the command of each step,
read against `tests/unit/cli/tree.json`, reaches a leaf with its flags and its arguments."""

import ast
import importlib
import json
import shlex
from pathlib import Path
from typing import get_args

import pytest

from lem.model.landing import world
from lem.store import step_refusals

SOURCE = Path(__file__).resolve().parents[3] / "src" / "lem"
TREE = Path(__file__).resolve().parents[1] / "cli" / "tree.json"
LOCKS = frozenset(("step", "waited"))


def module_of(path: Path) -> str:
    """The dotted name of the module at `path`."""
    return ".".join(("lem", *path.relative_to(SOURCE).with_suffix("").parts))


def named(call: ast.Call, path: Path) -> list[str]:
    """The step names one call of the step lock may take."""
    given = call.args[2]
    if isinstance(given, ast.Constant) and isinstance(given.value, str):
        return [given.value]
    if isinstance(given, ast.Name) and given.id == "STEP":
        return [importlib.import_module(module_of(path)).STEP]
    if isinstance(given, ast.Name) and given.id == "verb":
        return list(get_args(world.Verb.__value__))
    raise AssertionError(f"{path}: a step lock named by {ast.dump(given)}")


def steps_of() -> list[str]:
    """Every step name the code of Lem gives the step lock."""
    found: set[str] = set()
    for path in sorted(SOURCE.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call) or not isinstance(
                node.func, ast.Attribute
            ):
                continue
            target = node.func
            lock = isinstance(target.value, ast.Name) and target.value.id == "steps"
            if lock and target.attr in LOCKS:
                found.update(named(node, path))
    return sorted(found)


STEPS = steps_of()


def leaf_takes(words: list[str]) -> str | None:
    """Why the tree does not take `lem WORDS`, or None when it does."""
    node = json.loads(TREE.read_text(encoding="utf-8"))
    rest = list(words)
    while rest and rest[0] in node.get("subcommands", {}):
        node = node["subcommands"][rest.pop(0)]
    if node.get("subcommands"):
        return f"`{' '.join(words)}` stops at a group"
    flags = [word for word in rest if word.startswith("--")]
    values = [word for word in rest if not word.startswith("--")]
    options = node["options"]
    unknown = [flag for flag in flags if flag not in options or options[flag]["value"]]
    if unknown:
        return f"`{' '.join(words)}` gives {unknown}, which the leaf takes as no flag"
    needed = [one for one in node["positionals"] if one["count"] == "1"]
    if len(values) != len(needed):
        return f"`{' '.join(words)}` gives {len(values)} arguments for {len(needed)}"
    return None


def test_the_code_names_the_steps_it_locks() -> None:
    assert {"start", "checks", "task sync", "task red-base"} <= set(STEPS)
    assert "land checks --repair-limit" in STEPS
    assert "task move SLUG dropped" in STEPS


@pytest.mark.parametrize("step", STEPS)
def test_each_steps_refusal_names_a_command_the_tree_takes(step: str) -> None:
    shown = step_refusals.command(step, "gift-note")
    words = shlex.split(shown)
    assert words[0] == "lem"
    assert "gift-note" in words
    assert leaf_takes(words[1:]) is None
    refused = step_refusals.refusal("gift-note", step, None)
    assert refused.fix == f"wait for it to end, then run {shown} again"
