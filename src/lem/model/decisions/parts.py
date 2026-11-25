"""What each part of a breaker's document must hold (`decisions.BREAKER_PARTS` on `main`), as
`templates/breaker.md` has them: each a `## ` heading that opens with its words, in any case."""

import re
from types import MappingProxyType

# Each part by the words its heading opens with, and what its text must hold.
PARTS = MappingProxyType(
    {
        "today and after": "the run of Today and the run of After, each in numbered steps",
        "the case": (
            "the case that broke, in numbered steps, with its chart in a ```mermaid block"
        ),
        "the root cause": "why the case became possible, and how far the same cause reaches",
        "the options": "the options as this or that, in a table, with what each leads to",
        "the recommendation": "the option you would take, and why",
        "the assumptions": "what the document takes as true, one item each",
    }
)
STEP = re.compile(r"(?m)^\s*\d+[.)]\s+\S")
BULLET = re.compile(r"(?m)^\s*(?:[-*]|\d+[.)])\s+\S")
TODAY = re.compile(r"\btoday\b", re.IGNORECASE)
AFTER = re.compile(r"\bafter\b", re.IGNORECASE)
# The fewest numbered steps of a run, and the fewest rows of the options' table: its head, its
# rule and one option.
FEWEST_STEPS = 2
FEWEST_ROWS = 3


def steps(body: str) -> int:
    """How many numbered steps `body` holds."""
    return len(STEP.findall(body))


def runs(body: str) -> bool:
    """Today and after: two runs, each named, in numbered steps."""
    named = TODAY.search(body) and AFTER.search(body)
    return bool(named) and steps(body) >= FEWEST_STEPS


def holds(part: str, found: dict[str, list[str]]) -> bool:
    """Whether the lines `found` gives the part `part` hold what the part must; a part the
    document does not have holds nothing."""
    body = "\n".join(found.get(part, ()))
    if not body.strip():
        return False
    rows = [row for row in body.splitlines() if row.strip().startswith("|")]
    rules = {
        "today and after": runs(body),
        "the case": steps(body) >= FEWEST_STEPS and "```mermaid" in body,
        "the options": len(rows) >= FEWEST_ROWS,
        "the assumptions": bool(BULLET.search(body)),
    }
    return rules.get(part, True)
