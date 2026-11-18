"""The name of a task's plan file and of a ruling's file: the one place that builds it and finds it.

The settings' `paths.plan_file` and `paths.ruling_file` are patterns of the tokens `YYYY`, `MM`
and `DD`, the day the file was written, and `<slug>`, the task's or the ruling's (`project.py`
checks them). `project.py` and `criteria.py` import this file; it reads nothing and writes nothing.
"""

from __future__ import annotations

import re
from pathlib import Path

PLAN_FILE = "YYYY-MM-DD-<slug>.md"
# a ruling's file: its slug
RULING_FILE = "<slug>.md"
TOKENS = {"YYYY": r"(?P<Y>\d{4})", "MM": r"(?P<M>\d{2})", "DD": r"(?P<D>\d{2})"}


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


def found(folder: Path, pattern: str, slug: str) -> Path | None:
    """The task's plan in the plans folder, or a ruling in the rulings folder: a file of the name the
    pattern gives. Of several, the one of the newest day."""
    if not folder.is_dir():
        return None
    form = regex(pattern, slug)
    hits = []
    for file in folder.iterdir():
        match = form.fullmatch(file.name)
        if match and file.is_file():
            groups = match.groupdict()
            hits.append(((groups.get("Y") or "", groups.get("M") or "", groups.get("D") or ""), file.name, file))
    return max(hits)[2] if hits else None
