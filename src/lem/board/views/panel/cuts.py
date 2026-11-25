"""Where a line of Lem's is cut (`board_model.cuts` and `split_top` on `main`): at a separator
that stands outside quotes, parentheses and code, so that a quoted choice or a path in
backticks stays whole."""

from itertools import accumulate
from types import MappingProxyType

# Outside every quote and parenthesis: the depth of parentheses and the open quote.
type State = tuple[int, str | None]
TOP: State = (0, None)
# A separator's place in a text, and the separator.
type Cut = tuple[int, str]
type Seps = tuple[str, ...]
# Each quote, and what closes it: a typographic quote closes on either of its two marks.
CLOSES = MappingProxyType({'"': '"', "`": "`", "“": "“”"})


def moved(state: State, char: str) -> State:
    """The state after `char`."""
    depth, quote = state
    if quote is not None:
        closes = CLOSES[quote]
        return (depth, None) if char in closes else state
    if char in CLOSES:
        return depth, char
    if char == "(":
        return depth + 1, None
    if char == ")":
        return max(0, depth - 1), None
    return state


def cuts(text: str, seps: Seps) -> list[Cut]:
    """Where each separator stands in `text` outside parentheses, quotes and code: its place
    and itself."""
    found: list[Cut] = []
    end = 0
    for index, state in enumerate(accumulate(text, moved, initial=TOP)):
        sep = starting(text, index, seps)
        if sep and index >= end and state == TOP:
            found.append((index, sep))
            end = index + len(sep)
    return found


def starting(text: str, index: int, seps: Seps) -> str:
    """The separator that starts at `index` of `text`, or ""."""
    return next((one for one in seps if text.startswith(one, index)), "")


def split_top(text: str, seps: Seps) -> list[str]:
    """`text` cut at each separator outside parentheses, quotes and code, each part
    stripped, the empty ones left out."""
    parts, start = [], 0
    for index, sep in cuts(text, seps):
        parts.append(text[start:index])
        start = index + len(sep)
    parts.append(text[start:])
    return [part.strip() for part in parts if part.strip()]
