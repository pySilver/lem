"""A complete line of a shell block, parsed by Click itself.

`reading.py` judges a line against the shape of the tree and lets a required option that the
line leaves out pass, since prose names a command by what it is about. A line of a shell block
that has no mark of a synopsis (`[...]`, `(...)`, `|`, `...`) is a call an agent copies: here
each placeholder gets a stand-in its word takes (a choice's first value, a number, or `.`, a
folder that is there), and Click parses the root's options and the leaf's words, so that a
missing required option or a value Click refuses is an old line too. No command runs.
"""

import click

from lem.cli import lazy
from unit.cli import reading, shapes

type Shape = dict
type Split = tuple[list[str], list[str], list[str]]

TREE = shapes.tree()


def complete(line: reading.Line) -> bool:
    """Whether LINE is a whole call with no mark of a synopsis."""
    if line.span:
        return False
    marks = (reading.OPEN, reading.GROUP, reading.OR)
    if any(mark in reading.scanned(line.text) for mark in marks):
        return False
    words = [word.text for word in reading.words_of(line.text)]
    return not any("|" in word or reading.left_out(word) for word in words)


def stand_in(slot: dict | None) -> str:
    """A word that SLOT, an option's or a positional's shape, takes."""
    if slot is None:
        return "."
    if "choices" in slot:
        return slot["choices"][0]
    return {"int": "1", "float": "1.5"}.get(slot.get("type", ""), ".")


def word_for(slot: dict | None, text: str) -> str:
    return stand_in(slot) if reading.is_placeholder(text) else text


def option_words(level: Shape, texts: list[str], at: int) -> tuple[list[str], int]:
    """The option at AT of TEXTS with its value, each placeholder a stand-in; and the index
    after them."""
    flag, equal, attached = texts[at].partition("=")
    option = reading.option_of(level, flag)
    if equal:
        return [f"{flag}={word_for(option, attached)}"], at + 1
    if option is not None and option["value"] and at + 1 < len(texts):
        return [flag, word_for(option, texts[at + 1])], at + 2
    return [flag], at + 1


def split(texts: list[str]) -> Split | None:
    """The root's options, the path of nouns and verbs, and the leaf's words, each placeholder
    with its stand-in; None when a placeholder stands where a noun or a verb goes."""
    level: Shape = TREE
    parts: Split = ([], [], [])
    into, at, given = parts[0], 0, 0
    while at < len(texts):
        text = texts[at]
        if text == "--":
            into += ["--", *(word_for(None, word) for word in texts[at + 1 :])]
            break
        if reading.is_option(text):
            words, at = option_words(level, texts, at)
            into += words
            continue
        children = level.get("subcommands")
        if children:
            name = text if text in children else level.get("default")
            if name is None:
                return None
            at += name == text
            parts[1].append(name)
            level, into = children[name], parts[2]
            continue
        positionals = level["positionals"] or [None]
        into.append(word_for(positionals[min(given, len(positionals) - 1)], text))
        given, at = given + 1, at + 1
    if level.get("subcommands"):
        if "default" not in level:
            return None
        parts[1].append(level["default"])
    return parts


def clicks_word(line: reading.Line) -> str | None:
    """What Click says against the complete LINE, or None when it takes it."""
    parts = split([word.text for word in reading.words_of(line.text)])
    if parts is None:
        return None
    root, path, leaf = parts
    try:
        with lazy.ROOT.make_context("lem", [*root, *path, *leaf]) as ctx:
            command: click.Command = lazy.ROOT
            for name in path:
                assert isinstance(command, click.Group)
                found = command.get_command(ctx, name)
                assert found is not None
                command = found
            with command.make_context(path[-1], list(leaf), parent=ctx):
                return None
    except click.ClickException as error:
        return f"Click: {error.format_message()}"
