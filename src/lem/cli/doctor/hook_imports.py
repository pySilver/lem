"""What a module of `lem.hooks` imports at its top, and whether it reads and parses.

An import inside a function runs on that function's path only, so only the statements of a
module's body count.
"""

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

HOOKS = "lem.hooks"


def named(node: ast.stmt) -> list[str]:
    """The modules of Lem one statement at a module's top imports, by their dotted names."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names if alias.name.startswith("lem.")]
    if not isinstance(node, ast.ImportFrom) or node.level or not node.module:
        return []
    if node.module in {"lem", HOOKS}:
        return [f"{node.module}.{alias.name}" for alias in node.names]
    return [node.module] if node.module.startswith("lem.") else []


def shown(module: str) -> str:
    """A module of `lem.hooks` as its file: `hooks/main.py`."""
    stem = module.removeprefix("lem.").replace(".", "/")
    return f"{stem}.py"


def problem_of(package: Path, module: str) -> tuple[str | None, list[str]]:
    """What is wrong with `module` of the app's `package` (None when it is whole), and the
    modules of Lem it imports at its top."""
    name = shown(module)
    try:
        tree = ast.parse((package / name).read_bytes(), name)
    except FileNotFoundError:
        return f"{name} is missing", []
    except OSError as error:
        return f"{name} cannot be read ({error.strerror})", []
    except (SyntaxError, ValueError) as error:
        line = getattr(error, "lineno", None)
        at = "" if line is None else f" (line {line})"
        return f"{name} does not compile{at}", []
    return None, [found for node in tree.body for found in named(node)]
