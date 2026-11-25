"""What `lem settings set` writes for the words it is given: `default` takes the line out, a
seat of the experts is one or two whole seats joined by a comma, a yes or a no is true or false,
`none` of the load gate is 0, a number is a number, and every other word is itself.

The file then says whether the value is of the key's form: a word is only turned into the value
its key takes, never checked here.
"""

import contextlib
import tomllib

from lem.kernel.errors import Refusal

DEFAULT = "default"
EXPERTS = "seats.experts"
# Words of a yes or a no, and what each writes.
YES_NO = (
    ("yes", True),
    ("true", True),
    ("on", True),
    ("no", False),
    ("false", False),
    ("off", False),
)
# A word that one key takes for a number: the load gate's `none` takes the gate away.
NUMBER_WORDS = (("load.start", "none", 0),)


type Typed = str | bool | int | float | list[str] | dict[str, object]


def number(word: str) -> int | float | None:
    """The number `word` is, or None."""
    for kind in (int, float):
        with contextlib.suppress(ValueError):
            return kind(word)
    return None


def yes_or_no(word: str) -> bool | None:
    """True or False for a word of a yes or a no, else None."""
    lowered = word.lower()
    return next((said for name, said in YES_NO if name == lowered), None)


def number_word(key: str, word: str) -> int | None:
    """The number a word of one key stands for (`load.start none`), else None."""
    asked = (key, word)
    return next(
        (said for name, one, said in NUMBER_WORDS if (name, one) == asked), None
    )


def typed(key: str, word: str) -> Typed | None:
    """What `word` writes for `key`; None for `default`, which takes the line out."""
    if word == DEFAULT:
        return None
    if word.startswith(("{", "[")):
        return toml_value(key, word)
    if key == EXPERTS:
        return [part.strip() for part in word.split(",")]
    for found in (yes_or_no(word), number_word(key, word), number(word)):
        if found is not None:
            return found
    return word


def toml_value(key: str, word: str) -> Typed:
    """A value written as TOML writes it, an inline table or a list (`ask.status`)."""
    try:
        return tomllib.loads(f"value = {word}")["value"]
    except tomllib.TOMLDecodeError as error:
        raise Refusal(
            "settings",
            f"{key} = {word} does not read as TOML: {error}",
            'write it as TOML writes it, as {asking = ["blocked"], answered = ["active"]}',
        ) from error


def table_key(key: str) -> tuple[str, str]:
    """The table and the key of `TABLE.KEY`; a key in another form is a refusal."""
    table, dot, name = key.partition(".")
    if not dot or not table or not name or "." in name:
        raise Refusal(
            "settings-key",
            f"{key!r} names no setting: a setting is TABLE.KEY",
            "name it as docs/settings.md does, as seats.reviewer or load.start",
        )
    return table, name
