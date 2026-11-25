"""What the owner gets, from a task's `task.md` (`board.outcome` and `unwrapped` on `main`): its
`## Outcome` section, to the next heading of the same level or above, as the markdown it was
written in, with each line that only wraps a sentence joined to its paragraph, so that the
board's reader, which keeps a line break as one, shows a paragraph as one. A heading inside a
fenced block is no end of the section."""

import re

SECTION = re.compile(r"(?m)^##[ \t]+Outcome[ \t]*\n")
FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^#{1,2}[ \t]")
# A line that opens a block of its own: a list, a heading, a quote, a table, a fence, a rule.
BLOCK = re.compile(r"^\s*([-*+]\s|\d+[.)]\s|#|>|\||```|~~~|---|\*\*\*)")
# A line after which the next one never joins it.
APART = re.compile(r"^\s*(```|~~~|\||#)")


def outcome(text: str) -> str:
    """The `## Outcome` section of `text`, unwrapped; "" with none."""
    found = SECTION.search(text)
    if found is None:
        return ""
    kept: list[str] = []
    fence = ""
    for line in text[found.end() :].splitlines():
        if not fence and HEADING.match(line):
            break
        fence = fenced(fence, line)
        kept.append(line)
    return "\n".join(unwrapped(kept)).strip()


def fenced(fence: str, line: str) -> str:
    """The fence a line leaves open: one it opens, or none once it closes the open one."""
    mark = FENCE.match(line)
    if mark is None:
        return fence
    if not fence:
        return mark[1]
    return "" if line.strip().startswith(fence) else fence


def unwrapped(lines: list[str]) -> list[str]:
    """The lines with each one that only wraps a sentence joined to the line before it; a
    list, a table, a quote, a fence and a label stay as they were written."""
    out: list[str] = []
    fence = ""
    for line in lines:
        inside = bool(fence) or FENCE.match(line) is not None
        fence = fenced(fence, line)
        if not inside and out and joins(out[-1], line):
            out[-1] = joined(out[-1], line)
        else:
            out.append(line)
    return out


def joined(before: str, line: str) -> str:
    """The line before with `line` joined to its sentence."""
    head, tail = before.rstrip(), line.strip()
    return f"{head} {tail}"


def joins(before: str, line: str) -> bool:
    """Whether `line` only wraps the sentence of the line before it."""
    if not line.strip() or not before.strip() or BLOCK.match(line):
        return False
    labelled = before.rstrip().endswith(":") or before.endswith("  ")
    return not labelled and APART.match(before) is None
