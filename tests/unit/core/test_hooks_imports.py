"""`lem-hook` imports the standard library only (the design's part 2), since a hook's whole run
has a budget of about 50 ms (part 5). Read from the hooks' source, so an import on a path that no
test takes is found too."""

import ast
import sys
from pathlib import Path

import lem.hooks

HOOKS = Path(lem.hooks.__file__).resolve().parent
SRC = HOOKS.parents[1]


def outside(source: str, package: str) -> list[str]:
    """The modules that `source`, a module of `package`, imports from neither the standard
    library nor lem.hooks."""
    names: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = package.rsplit(".", node.level - 1)[0] if node.level else ""
            names.append(".".join(part for part in (base, node.module) if part))
    return [
        name
        for name in names
        if name.split(".")[0] not in sys.stdlib_module_names
        and name != "lem.hooks"
        and not name.startswith("lem.hooks.")
    ]


def test_every_module_of_the_hooks_imports_the_standard_library_only() -> None:
    modules = sorted(HOOKS.rglob("*.py"))
    assert modules
    for module in modules:
        package = ".".join(module.parent.relative_to(SRC).parts)
        assert outside(module.read_text(), package) == [], module


def test_the_check_finds_a_library_and_the_rest_of_lem() -> None:
    source = (
        "import json, msgspec\n"
        "from lem.kernel import errors\n"
        "from .. import store\n"
        "from . import serve\n"
        "from .session import start\n"
        "from lem.hooks import raw\n"
        "import os.path\n"
    )
    assert outside(source, "lem.hooks") == ["msgspec", "lem.kernel", "lem"]
