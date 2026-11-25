"""The names of files as the `git` adapter gives them: read as git wrote them (`-z`, bytes),
and shown so that a person reads each on one line and two paths never share a name.

A character that can break a line or reorder the text around it (a control, a format character
such as a right-to-left override, a line or paragraph separator) becomes its code point
(`<U+000A>`), a byte that is not UTF-8 its value (`<0xE9>`), and `<` itself `<U+003C>`, so that
every `<` of a shown name starts such a mark (`land.shown_name` on `main`).
"""

import unicodedata

# The categories of a character that is shown by its code point.
UNSHOWN = frozenset(("Cc", "Cf", "Zl", "Zp"))
# What `surrogateescape` decodes a byte 0x80 to 0xFF that is not UTF-8 to.
SURROGATE_LOW = 0xDC80
SURROGATE_HIGH = 0xDCFF
SURROGATE_BYTE = 0x80


def mark(char: str) -> str:
    """One character of a name as it is shown."""
    code = ord(char)
    if SURROGATE_LOW <= code <= SURROGATE_HIGH:
        byte = format(code - SURROGATE_LOW + SURROGATE_BYTE, "02X")
        return f"<0x{byte}>"
    if char == "<" or unicodedata.category(char) in UNSHOWN:
        point = format(code, "04X")
        return f"<U+{point}>"
    return char


def shown(raw: bytes) -> str:
    """A path as git wrote it, as a person reads it."""
    return "".join(mark(char) for char in raw.decode(errors="surrogateescape"))


def listed(output: bytes) -> tuple[str, ...]:
    """The names of a `-z` list, each shown, once each, in their order."""
    names = (shown(raw) for raw in output.split(b"\0") if raw)
    return tuple(dict.fromkeys(names))
