"""The typed input of the pull request's template (`templates/pr.md.j2`): its blocks, each a
heading or none and its lines. The template only prints them."""

from lem.records.base import Frozen

# The lines of a part of the text, as the owner reads them.
type Lines = tuple[str, ...]


class Block(Frozen, frozen=True, kw_only=True):
    """One block of the text: its heading, and its lines as the owner reads them."""

    heading: str | None = None
    lines: Lines = ()


class Text(Frozen, frozen=True, kw_only=True):
    """The whole text, block by block, in the order the owner reads it."""

    blocks: tuple[Block, ...] = ()


def block(heading: str | None, lines: Lines) -> tuple[Block, ...]:
    """A block of `lines` under `heading`, or none when it has no line to show."""
    made = Block(heading=heading, lines=lines)
    return (made,) if lines else ()
