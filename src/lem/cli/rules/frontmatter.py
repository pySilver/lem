"""A rule file's frontmatter: the lines between its first two `---` lines."""

FENCE = "---"


def frontmatter(text: str) -> list[str]:
    """The lines of the frontmatter of `text`; none when it has no such block."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != FENCE:
        return []
    end = closing(lines)
    return [] if end is None else lines[1:end]


def closing(lines: list[str]) -> int | None:
    """The line of the `---` that closes the block the first line opens, or None."""
    rest = [line.strip() for line in lines[1:]]
    return rest.index(FENCE) + 1 if FENCE in rest else None
