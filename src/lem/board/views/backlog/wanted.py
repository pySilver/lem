"""The backlog's filter as the address asks for it (`backlog_filter` and `filter_href` of
`board_pages` on `main`): words (`q`), one worth (`worth`), and one fact (`only`): a place that
no longer resolves, or an item git does not have committed. A value the filter does not know is
no filter, so a shared link shows the same list.
"""

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING
from urllib.parse import quote, urlencode

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from lem.board.inputs.text import Href

WORTH = "worth"
ONLY = "only"
WORDS = "q"
LONGEST = 200
WORTHS = frozenset(("yes", "later", "unset", "no"))
FACTS = frozenset(("stale", "new"))
# The keys of the address, in the order its query names them.
KEYS = (WORDS, WORTH, ONLY)


@dataclass(frozen=True, kw_only=True, slots=True)
class Wanted:
    """The filter the address asks for: its words (`q`), its worth, and its fact (`only`)."""

    words: str = ""
    worth: str = ""
    only: str = ""

    def value_of(self, key: str) -> str:
        """The value of the chip's `key`: the worth, or the fact."""
        return self.worth if key == WORTH else self.only

    def pressed(self, key: str, shown: str) -> Wanted:
        """This filter with its `key` set to `shown`: a value given again takes it off."""
        same = self.value_of(key) == shown
        return replace(self, **{key: "" if same else shown})

    def address(self, base: Href) -> Href:
        """The address of the backlog with this filter."""
        said = (self.words, self.worth, self.only)
        pairs = zip(KEYS, said, strict=True)
        query = urlencode(
            [pair for pair in pairs if pair[1]], safe="/", quote_via=quote
        )
        backlog = f"{base}/backlog"
        return f"{backlog}?{query}" if query else backlog


def wanted(query: Mapping[str, Sequence[str]]) -> Wanted:
    """The filter of the address's query, as `urllib.parse.parse_qs` reads it."""
    worth, only = first(query, WORTH), first(query, ONLY)
    return Wanted(
        words=first(query, WORDS)[:LONGEST],
        worth=worth if worth in WORTHS else "",
        only=only if only in FACTS else "",
    )


def first(query: Mapping[str, Sequence[str]], key: str) -> str:
    """The first value of `key` in the query, stripped; empty with none."""
    said = query.get(key) or ("",)
    return said[0].strip()
