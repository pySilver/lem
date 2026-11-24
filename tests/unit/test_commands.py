"""The shape of the command `lem`: for each name of the table (`lem.names`), and for
`lem-ask`, `lem-jev`, `lem help` and `lem version`, the words it takes, as plain data in
tests/unit/commands.json. A unit case builds the shape again from the parsers as they
are and compares it with the file, so a change of a name, a subcommand or an option
shows as a failure that names it.

    python3 -B -m unittest discover -s tests/unit
    python3 -B tests/unit/test_commands.py --write    the file again, after a meant change

The file holds no class or text of argparse: names, counts and booleans only, so that a
tree built from another command-line library can be compared with it. For each command
and each subcommand, at any depth:

    options       each option by its long flag: `aliases` (its other flags), `value`
                  (whether it takes a value), `required`, and where they hold,
                  `choices`, `count` (a value count other than one: ?, * or +),
                  `repeat` (it may be given more than once), `type` (int, float) and
                  `hidden` (no help shows it); `--help` is one of them
    positionals   in order, each with its `name` and `count`: 1, ?, *, +, a number, or
                  `rest` (every word after it, options too); `choices` where it has them
    exclusive     the groups of options of which at most one is given, with `required`
                  when one must be
    subcommands   each by its name, with `subcommand_required`
    default       the subcommand a first word that names none goes to (`lem-ask`)

Two modules read their own arguments without argparse: `cast` (`lem cast [init |
run-dir SLUG] [--repo DIR]`, --repo anywhere, and no --help) and `jev` (`lem-jev [check]
SPEC`). Their shapes are written here by hand from their `main`, and so are `help` and
`version`, the two words of `bin/lem` itself. `lem-ask`'s `default` is by hand too: its
`main` puts `ask` before any first word that is not a subcommand, before argparse reads
the line.

A parser is reached by its module's `main` with `ArgumentParser.parse_args` patched:
the patch keeps the parser and stops, before the command does anything.

The second table of the file, `exits`, is what a wrong call gives through `bin/lem`: the
exit status of `NAME --help`, of NAME with no argument, and of NAME with an option no
command has, for each name of the table and the two links. A name whose shape needs no
argument runs its command when it is called alone (`lem serve` serves, `lem doctor`
checks the machine, `lem-ask` reads a spec), so the table says `runs` for it and no case
calls it. tests/lem-command.sh checks the rest of a call through `bin/lem`: that each name
reaches its module with its arguments, that `--help` shows the usage in the name the
developer types, the words of one usage error, `lem`, `lem help`, `lem version` and an
unknown name. This case checks only the three exit statuses, for every name.
"""

import argparse
import importlib
import inspect
import json
import os
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import ModuleType
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from lem import names

FILE = Path(__file__).resolve().parent / "commands.json"
WRITE = "python3 -B tests/unit/test_commands.py --write"
# An option that no command of Lem takes, for the wrong call.
UNKNOWN = "--no-such-option"
# Every word of a call as one entry of `exits`.
CALLS = {"help": ["--help"], "bare": [], "unknown": [UNKNOWN]}
# What `exits` says of a call that is not made: the name alone runs its command.
RUNS = "runs"
# The seconds one call through bin/lem may take before the case calls it hung.
CALL_SECONDS = 60

HELP = {"aliases": ["-h"], "value": False, "required": False}
REPO = {"aliases": [], "value": True, "required": False}
# The shapes of what reads its arguments by hand: cast.main and jev.main, and bin/lem's
# own two words.
HAND: dict[str, dict] = {
    "cast": {
        "options": {"--repo": REPO},
        "positionals": [],
        "subcommands": {
            "init": {"options": {"--repo": REPO}, "positionals": []},
            "run-dir": {
                "options": {"--repo": REPO},
                "positionals": [{"name": "slug", "count": "1"}],
            },
        },
        "subcommand_required": False,
    },
    "lem-jev": {
        "options": {},
        "positionals": [{"name": "spec", "count": "1"}],
        "subcommands": {
            "check": {"options": {}, "positionals": [{"name": "spec", "count": "1"}]}
        },
        "subcommand_required": False,
    },
    "help": {"options": {}, "positionals": []},
    "version": {"options": {}, "positionals": []},
}
# lem-ask's main sends a line whose first word names no subcommand to this one.
ASK_DEFAULT = "ask"


class Captured(Exception):
    """Raised by the patched parse_args, with the parser it was called on."""

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        super().__init__("captured")
        self.parser = parser


def stop(
    self: argparse.ArgumentParser,
    args: object = None,
    namespace: object = None,
) -> None:
    raise Captured(self)


def parser_of(module: ModuleType) -> argparse.ArgumentParser:
    """The parser MODULE's main builds, taken at its call of parse_args."""
    main = module.main
    with (
        mock.patch.object(argparse.ArgumentParser, "parse_args", stop),
        mock.patch.object(argparse.ArgumentParser, "parse_known_args", stop),
        mock.patch.object(sys, "argv", [str(module.__file__)]),
    ):
        try:
            if inspect.signature(main).parameters:
                main([])
            else:
                main()
        except Captured as captured:
            return captured.parser
    raise AssertionError(
        f"{module.__name__}.main returned before it called parse_args; read how it "
        "parses its arguments"
    )


def count(nargs: object) -> str:
    """A positional's or an option's NARGS as the shape says it."""
    if nargs is None:
        return "1"
    if nargs == argparse.REMAINDER:
        return "rest"
    return str(nargs)


def main_flag(flags: list[str]) -> str:
    return next((flag for flag in flags if flag.startswith("--")), flags[-1])


def option(action: argparse.Action) -> dict:
    flags = list(action.option_strings)
    said: dict[str, object] = {
        "aliases": [flag for flag in flags if flag != main_flag(flags)],
        "value": action.nargs != 0,
        "required": action.required,
    }
    if action.choices is not None:
        said["choices"] = [str(choice) for choice in action.choices]
    if action.nargs not in (None, 0):
        said["count"] = count(action.nargs)
    if isinstance(action, argparse._AppendAction):  # noqa: SLF001 - argparse keeps a parser's words in its private names alone
        said["repeat"] = True
    if action.type is not None:
        said["type"] = getattr(action.type, "__name__", str(action.type))
    if action.help == argparse.SUPPRESS:
        said["hidden"] = True
    return said


def shape_of(parser: argparse.ArgumentParser) -> dict:
    """The shape of PARSER and of its subcommands, as plain data."""
    shape: dict[str, object] = {"options": {}, "positionals": []}
    options: dict[str, dict] = {}
    positionals: list[dict] = []
    for action in parser._actions:  # noqa: SLF001 - argparse keeps a parser's words in its private names alone
        if isinstance(action, argparse._SubParsersAction):  # noqa: SLF001 - argparse keeps a parser's words in its private names alone
            shape["subcommands"] = {
                name: shape_of(child) for name, child in action.choices.items()
            }
            shape["subcommand_required"] = action.required
        elif action.option_strings:
            options[main_flag(list(action.option_strings))] = option(action)
        else:
            positional: dict[str, object] = {
                "name": action.dest,
                "count": count(action.nargs),
            }
            if action.choices is not None:
                positional["choices"] = [str(choice) for choice in action.choices]
            positionals.append(positional)
    shape["options"] = options
    shape["positionals"] = positionals
    groups = [
        {
            "options": [
                main_flag(list(action.option_strings))
                for action in group._group_actions  # noqa: SLF001 - argparse keeps a parser's words in its private names alone
            ],
            "required": group.required,
        }
        for group in parser._mutually_exclusive_groups  # noqa: SLF001 - argparse keeps a parser's words in its private names alone
    ]
    if groups:
        shape["exclusive"] = groups
    return shape


def modules() -> dict[str, str]:
    """Each name of the table and each link, with the module it runs."""
    return {
        **{name: module for name, (module, _) in names.COMMANDS.items()},
        **names.ALIASES,
    }


def build() -> dict[str, dict]:
    """The shape of every name, from the parsers as they are and HAND."""
    shapes: dict[str, dict] = {}
    for name, module in modules().items():
        if name in HAND:
            shapes[name] = HAND[name]
            continue
        shapes[name] = shape_of(parser_of(importlib.import_module(f"lem.{module}")))
    shapes["lem-ask"]["default"] = ASK_DEFAULT
    shapes["help"] = HAND["help"]
    shapes["version"] = HAND["version"]
    return shapes


def needs_nothing(shape: dict) -> bool:
    """Whether a call of SHAPE's command with no word is one it takes."""
    if shape.get("subcommand_required"):
        return False
    return all(item["count"] in ("?", "*", "rest") for item in shape["positionals"])


def environment(home: Path) -> dict[str, str]:
    """A call's environment: no board server, and a home and a config folder of its
    own, with no agterm session to reach and no PYTHONPATH of the caller's."""
    kept = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("AGT", "XDG_", "LEM_", "PYTHON"))
    }
    return {
        **kept,
        "LEM_SERVE": "off",
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / "config"),
    }


def status(name: str, words: list[str], home: Path) -> int:
    """The exit status of `NAME WORDS` through bin/lem, run in a new repository with no
    commit: cast reads the checkout before its arguments, and there it reads them."""
    folder = home / "work"
    program = ROOT / "bin" / (name if name in names.ALIASES else "lem")
    line = [sys.executable, "-B", str(program)]
    line += [*([] if name in names.ALIASES else [name]), *words]
    ran = subprocess.run(
        line,
        cwd=folder,
        env=environment(home),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=CALL_SECONDS,
        check=False,
    )
    return ran.returncode


def exits(shapes: dict[str, dict]) -> dict[str, dict[str, int | str]]:
    """For each name of the table and each link, the exit status of each call of CALLS;
    RUNS for the bare call of a name that needs no word."""
    named = list(modules())
    with tempfile.TemporaryDirectory(prefix="lem-commands-") as folder:
        home = Path(folder)
        (home / "work").mkdir()
        (home / "config").mkdir()
        subprocess.run(
            ["git", "init", "-q", str(home / "work")],
            check=True,
            env=environment(home),
        )
        jobs = [
            (name, call)
            for name in named
            for call in CALLS
            if not (call == "bare" and needs_nothing(shapes[name]))
        ]
        with ThreadPoolExecutor(max_workers=8) as pool:
            codes = dict(
                zip(
                    jobs,
                    pool.map(lambda job: status(job[0], CALLS[job[1]], home), jobs),
                    strict=True,
                )
            )
    return {
        name: {call: codes.get((name, call), RUNS) for call in CALLS} for name in named
    }


def differences(was: object, now: object, path: str = "") -> Iterator[str]:
    """Each place where NOW differs from WAS, by its path of names."""
    if isinstance(was, dict) and isinstance(now, dict):
        for key in [*was, *(key for key in now if key not in was)]:
            where = f"{path} {key}".strip()
            if key not in now:
                yield f"{where}: gone"
            elif key not in was:
                yield f"{where}: new"
            else:
                yield from differences(was[key], now[key], where)
    elif was != now:
        yield f"{path}: {json.dumps(was)} is now {json.dumps(now)}"


def written() -> dict:
    if not FILE.is_file():
        raise AssertionError(f"{FILE} is not there; write it with `{WRITE}`")
    return json.loads(FILE.read_text(encoding="utf-8"))


def write() -> None:
    shapes = build()
    FILE.write_text(
        json.dumps({"commands": shapes, "exits": exits(shapes)}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {FILE}")


class Shape(unittest.TestCase):
    def test_the_file_holds_the_shape_the_parsers_have(self) -> None:
        found = list(differences(written()["commands"], build()))
        self.assertEqual(
            found,
            [],
            "the command's words differ from tests/unit/commands.json:\n  "
            + "\n  ".join(found)
            + f"\nwhen the change is meant, write the file again: `{WRITE}`",
        )

    def test_the_shape_names_every_name_of_the_table(self) -> None:
        self.assertEqual(
            set(build()), {*names.COMMANDS, *names.ALIASES, "help", "version"}
        )

    def test_a_parser_is_reached_without_running_its_command(self) -> None:
        # land's parser, reached through its main with parse_args patched: its words,
        # and nothing of the landing ran
        shape = shape_of(parser_of(importlib.import_module("lem.land")))
        self.assertEqual(shape["positionals"], [])
        self.assertTrue(shape["subcommand_required"])
        start = shape["subcommands"]["start"]
        self.assertEqual(start["positionals"], [{"name": "slug", "count": "1"}])
        self.assertEqual(
            start["options"]["--conflicting"],
            {"aliases": [], "value": False, "required": False},
        )
        self.assertEqual(
            shape["subcommands"]["merge"]["options"]["--by"]["choices"],
            ["owner", "merger"],
        )


class Exits(unittest.TestCase):
    def test_a_wrong_call_through_bin_lem_exits_as_the_file_says(self) -> None:
        found = list(differences(written()["exits"], exits(build())))
        self.assertEqual(
            found,
            [],
            "a wrong call exits otherwise than tests/unit/commands.json says:\n  "
            + "\n  ".join(found)
            + f"\nwhen the change is meant, write the file again: `{WRITE}`",
        )


if __name__ == "__main__":
    if sys.argv[1:] == ["--write"]:
        write()
    elif sys.argv[1:]:
        sys.exit(f"test_commands.py: {sys.argv[1:]!r}; the one argument is --write")
    else:
        unittest.main()
