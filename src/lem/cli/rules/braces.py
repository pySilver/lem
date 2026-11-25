"""A glob's brace groups as the globs they stand for: `*.{ts,tsx}` is `*.ts` and `*.tsx`, a
group inside a group too. A brace with no comma, or one that does not close, stays as written.
"""

OPEN = "{"
CLOSE = "}"
COMMA = ","

# The text before a group, the text inside it, and the text after it.
type Group = tuple[str, str, str]


def braces(pattern: str) -> tuple[str, ...]:
    """Every glob `pattern` stands for, in the order its groups list them."""
    group = first_group(pattern)
    if group is None:
        return (pattern,)
    head, inner, tail = group
    parts = top_parts(inner)
    if len(parts) == 1:
        return kept(f"{head}{OPEN}{inner}{CLOSE}", tail)
    return spread(head, parts, tail)


def kept(written: str, tail: str) -> tuple[str, ...]:
    """A group with no comma as written, before each form of the text after it."""
    return tuple(written + rest for rest in braces(tail))


def spread(head: str, parts: list[str], tail: str) -> tuple[str, ...]:
    """Each part of a group in its place, and each form of what that makes."""
    forms = (f"{head}{part}{tail}" for part in parts)
    return tuple(done for form in forms for done in braces(form))


def first_group(pattern: str) -> Group | None:
    """The first brace group of `pattern` that closes, or None."""
    head, brace, rest = pattern.partition(OPEN)
    end = closing(rest) if brace else None
    if end is None:
        return None
    return head, rest[:end], rest[end + 1 :]


def closing(rest: str) -> int | None:
    """Where the group whose text starts `rest` closes, or None when it does not."""
    depth = 1
    for at, char in enumerate(rest):
        depth += (char == OPEN) - (char == CLOSE)
        if not depth:
            return at
    return None


def top_parts(inner: str) -> list[str]:
    """The text of a group cut at each comma outside an inner group."""
    parts, level, last = [], 0, 0
    for at, char in enumerate(inner):
        level += (char == OPEN) - (char == CLOSE)
        if char == COMMA and not level:
            parts.append(inner[last:at])
            last = at + 1
    parts.append(inner[last:])
    return parts
