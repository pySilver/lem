"""The five parts of `handoff.md` under their headings, and the changed files its last part
names: each `PATH`: STATUS on a line of its own, the path bare or in backquotes, or `none`
(`templates/handoff.md`, `session.handoff_form` on `main`)."""

import itertools
import re

from lem.records.base import Frozen

# A line of `## Changed files`: a path, bare or in backquotes, a colon, and its status.
CHANGED = re.compile(
    r"[-*]\s+(?:`(?P<quoted>[^`]+)`|(?P<bare>[^\s:`]+)):\s*(?P<status>\S.*)"
)
NONE = re.compile(r"(?:[-*]\s+)?none\.?", re.IGNORECASE)
# The five parts of the form, each by its heading in lower case and as written.
PARTS = (
    ("settled", "Settled"),
    ("open", "Open"),
    ("next step", "Next step"),
    ("failed", "Failed"),
    ("changed files", "Changed files"),
)
CHANGED_FILES = "changed files"


type Lacking = tuple[list[str], tuple["Changed", ...]]


class Changed(Frozen, frozen=True, kw_only=True):
    """A changed file the handoff names, and its status."""

    path: str
    status: str


def lacking(parts: list[str]) -> Lacking:
    """The headings of the form with no words under them in `parts` (the titles and bodies of
    the headings in turn), with the lines of `## Changed files` that name no path and status;
    and the changed files."""
    bodies = bodies_of(parts)
    lacks = missing(bodies)
    wrong, changed = changed_of(bodies.get(CHANGED_FILES, ""))
    if wrong:
        lacks.append(
            "a path and a status on each line of ## Changed files, as `PATH`: STATUS, and "
            f"these lines have none: {wrong}"
        )
    return lacks, changed


def missing(bodies: dict[str, str]) -> list[str]:
    """The headings of the parts with no words under them."""
    return [f"## {title}" for key, title in PARTS if key not in bodies]


def bodies_of(parts: list[str]) -> dict[str, str]:
    """Each heading in lower case, and the words under it, for the headings with words."""
    pairs = itertools.batched(parts, 2, strict=True)
    return {key_of(title): body for title, body in pairs if body.strip()}


def key_of(title: str) -> str:
    """A heading in lower case, its words joined by one space."""
    return " ".join(title.lower().split())


def changed_of(body: str) -> tuple[str, tuple[Changed, ...]]:
    """The lines of `## Changed files` that name no path and status, joined, and the changed
    files; none for a part that says `none`."""
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if len(lines) == 1 and NONE.fullmatch(lines[0]):
        return "", ()
    read = tuple(map(changed_line, lines))
    wrong = "; ".join(one for one in read if isinstance(one, str))
    return wrong, tuple(one for one in read if isinstance(one, Changed))


def changed_line(line: str) -> Changed | str:
    """The changed file a line names, or the line as it is quoted for a refusal."""
    found = CHANGED.fullmatch(line)
    if found is None:
        return repr(line)
    path = found["quoted"] or found["bare"]
    return Changed(path=path, status=found["status"].strip())
