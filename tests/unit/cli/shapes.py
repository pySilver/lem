"""The shape of the command `lem` as plain data: for each noun and verb, the words it takes.

`tree.json` beside this file holds the shape the tree has; `test_tree.py` builds it again from
the commands as they are and compares, so a change of a noun, a verb, an argument or an option
fails until the file is written again on purpose:

    .venv/bin/python -I -B tests/unit/cli/shapes.py --write

For each command, at any depth:

    options       each option by its long flag: `aliases` (its other flags), `value`
                  (whether it takes a value), `required`, and where they hold `choices`,
                  `repeat` (it may be given more than once), `type` (int, float), `hidden`,
                  `default` (a value other than none) and `flag_value` (a switch: several
                  flags that set one word); `--help` is one of them
    positionals   in order, each with its `name` and `count`: 1, ? or *, + (one or more);
                  `choices` where it has them
    subcommands   each by its name, with `subcommand_required`
    default       the verb a first word that names none goes to (`lem ask SPEC`)
"""

import json
import sys
from pathlib import Path

import click

from lem.cli import lazy
from lem.cli.group import LazyGroup

FILE = Path(__file__).resolve().parent / "tree.json"
WRITE = ".venv/bin/python -I -B tests/unit/cli/shapes.py --write"
HELP = {"aliases": ["-h"], "value": False, "required": False}

type Shape = dict[str, object]


def count(param: click.Parameter) -> str:
    """An argument's count as the shape says it."""
    if param.nargs == -1:
        return "+" if param.required else "*"
    return "1" if param.required else "?"


def choices_of(param: click.Parameter) -> list[str] | None:
    if isinstance(param.type, click.Choice):
        return [str(choice) for choice in param.type.choices]
    return None


def kind_of(param: click.Parameter) -> str | None:
    if isinstance(param.type, click.types.IntParamType):
        return "int"
    if isinstance(param.type, click.types.FloatParamType):
        return "float"
    return None


def long_flag(option: click.Option) -> str:
    return next((flag for flag in option.opts if flag.startswith("--")), option.opts[0])


def option_shape(option: click.Option) -> Shape:
    main = long_flag(option)
    said: Shape = {
        "aliases": [flag for flag in option.opts if flag != main],
        "value": not option.is_flag,
        "required": option.required,
    }
    choices = choices_of(option)
    if choices is not None:
        said["choices"] = choices
    if option.multiple:
        said["repeat"] = True
    kind = kind_of(option)
    if kind is not None:
        said["type"] = kind
    if option.hidden:
        said["hidden"] = True
    if option.is_flag and not option.is_bool_flag:
        said["flag_value"] = option.flag_value
    default = option.default
    if default not in (None, False, (), click.core.UNSET):
        said["default"] = default
    return said


def shape_of(command: click.Command, ctx: click.Context) -> Shape:
    """The shape of COMMAND and of its subcommands, as plain data."""
    options: Shape = {"--help": HELP}
    positionals: list[Shape] = []
    for param in command.params:
        if isinstance(param, click.Option):
            options[long_flag(param)] = option_shape(param)
            continue
        positional: Shape = {"name": param.name, "count": count(param)}
        choices = choices_of(param)
        if choices is not None:
            positional["choices"] = choices
        positionals.append(positional)
    shape: Shape = {"options": options, "positionals": positionals}
    if isinstance(command, click.Group):
        children: Shape = {}
        for name in command.list_commands(ctx):
            child = command.get_command(ctx, name)
            assert child is not None, name
            with click.Context(child, info_name=name, parent=ctx) as inner:
                children[name] = shape_of(child, inner)
        shape["subcommands"] = children
        shape["subcommand_required"] = True
    if isinstance(command, LazyGroup) and command.default is not None:
        shape["default"] = command.default
    return shape


def tree() -> Shape:
    """The shape of `lem` and every command under it."""
    with click.Context(lazy.ROOT, info_name="lem") as ctx:
        shape = shape_of(lazy.ROOT, ctx)
    shape["subcommand_required"] = False
    return shape


def written() -> Shape:
    """The shape as `tree.json` holds it."""
    return json.loads(FILE.read_text(encoding="utf-8"))


def leaves(shape: Shape, path: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
    """The path of every command of SHAPE that has no subcommands."""
    children = shape.get("subcommands")
    if not isinstance(children, dict):
        return [path]
    return [
        found
        for name, child in children.items()
        for found in leaves(child, (*path, name))
    ]


if __name__ == "__main__":
    if sys.argv[1:] != ["--write"]:
        sys.exit(f"run it as {WRITE}")
    FILE.write_text(json.dumps(tree(), indent=2) + "\n", encoding="utf-8")
    print(f"{FILE}: {len(leaves(tree()))} commands")
