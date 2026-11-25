"""The `Judge` port's first adapter: Jev, TypeSafe's decision model, over `httpx` (the design's
part 4; `land.ask_jev`, `land.ask_alike` and `jev.py` on `main`).

The key is `JEV_API_KEY` of the environment the command started with, the address
`JEV_API_URL`, OpenRouter's by default, and the model `JEV_MODEL`; with no key nothing is sent.
A request is given `SECONDS`; one that fails, times out or gets a reply that does not read is
"no answer", and the landing goes on as without Jev. The bar is rule 6 of the builder file the
project's builders read, from the main checkout (`model/landing/jev_bar.py`).
"""

from typing import TYPE_CHECKING

from lem.adapters import judge_jev_ask
from lem.kernel import paths
from lem.model.landing import jev_bar
from lem.ports.judge import Candidate, Defect, NotAsked, Score

if TYPE_CHECKING:
    from pathlib import Path

    import httpx

    from lem.ports.place import Place

URL = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.14"
KEY = "JEV_API_KEY"


class JevJudge:
    """Jev, asked through one `httpx` client, with the project's bar."""

    def __init__(
        self, asker: judge_jev_ask.Asker, rule: tuple[str | None, str]
    ) -> None:
        """Keep the asker and the bar's rule: its condition, or None, and its file's name."""
        self.asker = asker
        self.rule = rule

    def same_items(
        self, defect: Defect, candidates: tuple[Candidate, ...]
    ) -> tuple[Score, ...] | NotAsked:
        """Jev's score of each item as the same defect, by its path."""
        return self.asker.same(defect, candidates)

    def over_bar(self, defect: Defect) -> Score | NotAsked:
        """Jev's score of the defect as over the bar of rule 6."""
        rule, name = self.rule
        if rule is None:
            return NotAsked(why=f"no bar in {name}")
        return self.asker.over(defect, rule)


def bar_of(checkout: Path) -> tuple[str | None, str]:
    """The bar's condition, from the project's own builder file or Lem's, and its name."""
    own = (checkout / jev_bar.OWN).is_file()
    path = checkout / jev_bar.OWN if own else paths.root() / jev_bar.LEMS
    try:
        text = path.read_text(encoding="utf-8")
    except OSError, UnicodeDecodeError:
        return None, jev_bar.named(own=own)
    return jev_bar.condition(text), jev_bar.named(own=own)


def bind(place: Place, transport: httpx.BaseTransport | None = None) -> JevJudge:
    """The adapter for `place`: the key, address and model of its environment."""
    environ = place.environ
    asker = judge_jev_ask.Asker(
        key=environ.get(KEY) or None,
        url=environ.get("JEV_API_URL", "").strip() or URL,
        model=environ.get("JEV_MODEL", "").strip() or MODEL,
        transport=transport,
    )
    return JevJudge(asker, bar_of(place.checkout))
