"""The name of a task's plan file and of a ruling's file: the one place that builds it and finds it.

The settings' `paths.plan_file` and `paths.ruling_file` are patterns of the tokens `YYYY`, `MM`
and `DD`, the day the file was written, and `<slug>`, the task's or the ruling's (`project.py`
checks them). A plan an older Lem wrote is named `YYYYMMDD-<slug>.md` whatever the pattern, and is
found too; a ruling has no older name. `project.py` and `criteria.py` import this file; it reads
nothing and writes nothing.
"""

from __future__ import annotations

import re
from pathlib import Path

PLAN_FILE = "YYYY-MM-DD-<slug>.md"
# a ruling's file: the name the rulings folder had before it was a setting
RULING_FILE = "<slug>.md"
TOKENS = {"YYYY": r"(?P<Y>\d{4})", "MM": r"(?P<M>\d{2})", "DD": r"(?P<D>\d{2})"}
# the name an older Lem gave every plan; a later change may drop it once no task with such a plan is open
OLD_FILE = "YYYYMMDD-<slug>.md"


def regex(pattern: str, slug: str) -> re.Pattern[str]:
    """The names a pattern gives a task's plan, on any day: each token as what it stands for."""
    out, at = [], 0
    for found in re.finditer(r"YYYY|MM|DD|<slug>", pattern):
        out += [re.escape(pattern[at:found.start()]), re.escape(slug) if found.group() == "<slug>" else TOKENS[found.group()]]
        at = found.end()
    out.append(re.escape(pattern[at:]))
    return re.compile("".join(out))


def name(pattern: str, slug: str, day: str) -> str:
    """The name a task's plan takes when it is written on DAY (YYYY-MM-DD)."""
    year, month, date_ = day.split("-")
    return pattern.replace("<slug>", slug).replace("YYYY", year).replace("MM", month).replace("DD", date_)


def found(folder: Path, pattern: str, slug: str, older: bool = True) -> Path | None:
    """The task's plan in the plans folder: a file of the name the pattern gives, or, with `older`,
    of the name an older Lem gave every plan, `YYYYMMDD-<slug>.md`. Of several, the one of the
    newest day. A ruling is found with `older` false."""
    if not folder.is_dir():
        return None
    forms = [regex(pattern, slug), *([regex(OLD_FILE, slug)] if older else [])]
    hits = []
    for file in folder.iterdir():
        match = next((hit for form in forms if (hit := form.fullmatch(file.name))), None)
        if match and file.is_file():
            groups = match.groupdict()
            hits.append(((groups.get("Y") or "", groups.get("M") or "", groups.get("D") or ""), file.name, file))
    return max(hits)[2] if hits else None
