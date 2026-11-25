"""One glob of a rule file's `paths:` as patterns over a path relative to the root.

The forms Claude Code documents for `paths:` (its page on `.claude/rules`, read 2026-11-15):
`**/*.ts` is every such file in any directory, `src/**/*` every file under `src/`, `*.md` the
files of the root only, `src/components/*.tsx` the files of that one directory. So `*` and `?`
stay inside one path segment, and `**` as a whole segment is any number of directories, none
too. Not documented there, and matched here because a rule too many costs less than a rule
missed: a name that starts with a dot, and a character class in brackets.
"""

import re

from lem.cli.rules.braces import braces

SLASH = "/"
DEEP = "**"
# What each wildcard stands for.
ANY_FOLDERS = "(?:.*/)?"
ANYTHING = ".*"
IN_ONE_SEGMENT = (("*", "[^/]*"), ("?", "[^/]"))

type Piece = tuple[str, int]


def glob_patterns(glob: str) -> tuple[re.Pattern[str], ...]:
    """The patterns `glob` stands for, one for each of its brace forms, with a leading `./`
    taken off; a path is covered when one of them matches it whole."""
    return tuple(glob_regex(one) for one in braces(glob.removeprefix("./")))


def glob_regex(glob: str) -> re.Pattern[str]:
    """One glob with no brace group as a pattern; a class that does not read raises
    `re.error`."""
    pieces, at = [], 0
    while at < len(glob):
        piece, at = translated(glob, at)
        pieces.append(piece)
    return re.compile("".join(pieces))


def translated(glob: str, at: int) -> Piece:
    """The pattern of the glob's text at `at`, and where the next piece starts."""
    if whole_stars(glob, at):
        return stars(glob, at)
    char = glob[at]
    wildcard = dict(IN_ONE_SEGMENT).get(char)
    if wildcard is not None:
        return wildcard, at + 1
    if char == "[" and "]" in glob[at + 2 :]:
        return bracket(glob, at)
    return re.escape(char), at + 1


def whole_stars(glob: str, at: int) -> bool:
    """Whether `**` at `at` is a whole segment of the glob."""
    before = glob[at - 1 : at] if at else SLASH
    after = glob[at + 2 : at + 3] or SLASH
    opens, closes = before == SLASH, after == SLASH
    return glob.startswith(DEEP, at) and opens and closes


def stars(glob: str, at: int) -> Piece:
    """`**/` is any number of folders, none too; `**` at the end is everything below."""
    if at + 2 < len(glob):
        return ANY_FOLDERS, at + 3
    return ANYTHING, at + 2


def bracket(glob: str, at: int) -> Piece:
    """A class in brackets, `[!...]` every other character; its `]` may be its first."""
    end = glob.index("]", at + 2)
    inner = glob[at + 1 : end]
    if inner.startswith("!"):
        inner = "".join(("^", inner[1:]))
    escaped = inner.replace("\\", r"\\")
    return f"[{escaped}]", end + 1
