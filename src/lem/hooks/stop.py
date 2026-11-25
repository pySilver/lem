"""The `stop` hook, async: at the end of a turn, the mark of a card that still waits.

It reads no input: nothing in the Stop event is needed, and a pipe that stays open would keep
the read, and the hook, alive. A card's page and its mark are the step `ask`'s, with
`sessions`; until then the hook gives a turn's end no word.
"""

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Mapping


def answer(environ: Mapping[str, str], behind: str | None) -> str:
    """Say nothing: no card of Lem is open yet to mark."""
    return ""
