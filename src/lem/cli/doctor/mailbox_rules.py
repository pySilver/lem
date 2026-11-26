"""The two declarations the mailbox recipe needs in Codex's rules to send a reply."""

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

PROGRAM = "mailbox-chat.py"
SEND = (PROGRAM, "say", "--file")
type Declaration = tuple[str, dict[str, object]]


def declarations(path: Path) -> Iterator[Declaration]:
    """Read literal rule declarations without running the rule file."""
    try:
        nodes = ast.parse(path.read_text(encoding="utf-8")).body
    except OSError, SyntaxError, UnicodeError:
        return
    for node in nodes:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Name) and not call.args:
                yield call.func.id, arguments(call)


def arguments(call: ast.Call) -> dict[str, object]:
    """The literal keyword arguments of a rule declaration."""
    try:
        return {
            arg.arg: ast.literal_eval(arg.value) for arg in call.keywords if arg.arg
        }
    except ValueError, SyntaxError:
        return {}


def pins(words: dict[str, object], program: Path) -> bool:
    """The host executable names the copy found on PATH."""
    paths = words.get("paths")
    named = words.get("name") == PROGRAM
    return named and isinstance(paths, list) and str(program) in paths


def configured(folder: Path, program: Path) -> bool:
    """The recipe's executable pin and the allow rule for the file form of a send."""
    found = tuple(
        rule for path in folder.glob("*.rules") for rule in declarations(path)
    )
    pinned = (words for name, words in found if name == "host_executable")
    prefixes = (words for name, words in found if name == "prefix_rule")
    if not any(map(allows, prefixes)):
        return False
    return any(pins(words, program) for words in pinned)


def allows(words: dict[str, object]) -> bool:
    """This prefix rule allows the file form of a send."""
    pattern = words.get("pattern")
    return pattern == list(SEND) and words.get("decision") == "allow"
