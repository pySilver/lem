"""A path as the `Git` port's `diff_stat` gives it, as the files it names.

The port lists a range with `git diff --numstat`, which writes a moved file once, in git's own
short form, and quotes a name with an unusual character. The picker counts a moved file under
its old path and its new one, each with its rules, so each form is unfolded here:
`{src => lib}/x.ts` is `src/x.ts` and `lib/x.ts`, `a.ts => b.ts` is both names, and a quoted
name is the name git quoted.
"""

import re

ARROW = " => "
QUOTE = '"'
# The short form of a move with a folder or an ending in common (`pprint_rename` in git), which
# git writes only when neither name is quoted.
FOLDED = re.compile(r"(?P<head>[^{]*)\{(?P<old>.*) => (?P<new>.*)\}(?P<tail>.*)")
# A move where a name is quoted: each side whole, quoted or not.
SIDE = r'"(?:[^"\\]|\\.)*"|[^"]*'
MOVED = re.compile(rf"(?P<old>{SIDE}) => (?P<new>{SIDE})")


def unfolded(shown: str) -> tuple[str, ...]:
    """The one name of `shown`, or the old and the new name of a moved file."""
    if QUOTE in shown:
        return tuple(map(unquoted, quoted_sides(shown)))
    folded = FOLDED.fullmatch(shown)
    if folded is None:
        return tuple(shown.split(ARROW, 1))
    head, tail = folded["head"], folded["tail"]
    sides = (folded["old"], folded["new"])
    return tuple(joined(head, side, tail) for side in sides)


def quoted_sides(shown: str) -> tuple[str, ...]:
    """The sides of a move where a name is quoted, or the one name."""
    moved = MOVED.fullmatch(shown)
    return (shown,) if moved is None else (moved["old"], moved["new"])


def joined(head: str, side: str, tail: str) -> str:
    """One side of a folded move as a whole path; an empty side leaves one slash."""
    return f"{head}{side}{tail}".replace("//", "/")


def unquoted(side: str) -> str:
    """A name git quoted in C's way, its octal escapes the bytes of UTF-8, as the name."""
    if not side.startswith(QUOTE):
        return side
    escaped = side[1:-1].encode()
    return escaped.decode("unicode_escape").encode("latin-1").decode()
