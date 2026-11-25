"""The rules of a call that Click's parser does not hold by itself: exactly one of a set of
words, at most one, or at least one. Each is a wrong call (exit 2) before the leaf runs, and
gives the words back, so that a leaf's callback reads `run(msgspec.convert(check(...), Call))`.
"""

from collections.abc import Mapping

import click

type Given = Mapping[str, object]


def exactly_one(given: Given, *names: str) -> Given:
    """Refuse a call that gives none, or more than one, of the words `names`."""
    if counted(given, names) != 1:
        why = f"give exactly one of {listed(names)}"
        raise click.UsageError(why, click.get_current_context())
    return given


def at_most_one(given: Given, *names: str) -> Given:
    """Refuse a call that gives more than one of the words `names`."""
    if counted(given, names) > 1:
        why = f"give at most one of {listed(names)}"
        raise click.UsageError(why, click.get_current_context())
    return given


def at_least_one(given: Given, *names: str) -> Given:
    """Refuse a call that gives none of the words `names`."""
    if not counted(given, names):
        why = f"give at least one of {listed(names)}"
        raise click.UsageError(why, click.get_current_context())
    return given


def counted(given: Given, names: tuple[str, ...]) -> int:
    """How many of the words `names` the call gives."""
    return sum(is_given(given.get(name)) for name in names)


def is_given(word: object) -> bool:
    """A value (0 too), a flag that is on, or a repeated word given once at least."""
    return (
        word is not None
        and word is not False
        and not (isinstance(word, tuple) and not word)
    )


def listed(names: tuple[str, ...]) -> str:
    """The words `names` as the owner types them: each option's flag, each argument's name."""
    words = {word.name: word for word in click.get_current_context().command.params}
    return ", ".join(shown_name(words[name]) for name in names)


def shown_name(word: click.Parameter) -> str:
    """An option's long flag, or an argument's name in capitals."""
    if not isinstance(word, click.Option):
        return word.human_readable_name.upper()
    flags = [flag for flag in word.opts if flag.startswith("--")]
    return flags[0] if flags else word.opts[0]
