"""Check one expert's verbatim answer and record it once under a lock."""

import re
from typing import TYPE_CHECKING

import msgspec

from lem.addons.experts import folders
from lem.addons.experts.records import Answer, Record, Summary
from lem.kernel import clock, files, locks
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

PICK = re.compile(
    r"(?:pick:[ \t]*(?P<pick>\S[^\n]*?)|(?P<none>none fits))[ \t]*\n\s*why:[ \t]*(?P<why>\S.*)",
    re.IGNORECASE | re.DOTALL,
)
OPEN = re.compile(
    r"answer:[ \t]*(?P<answer>\S.*?)\n\s*why:[ \t]*(?P<why>\S.*)",
    re.IGNORECASE | re.DOTALL,
)


def read(path: Path, options: tuple[str, ...]) -> Answer:
    """The file stays verbatim. The record keeps the checked answer fields."""
    try:
        text = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as error:
        raise Refusal(
            "expert-answer",
            f"the answer in {path} does not read",
            "save the reply verbatim as UTF-8",
        ) from error
    found = (PICK if options else OPEN).fullmatch(text)
    if not found:
        raise Refusal(
            "expert-answer",
            "the reply does not follow the brief",
            "ask the expert once more with the same brief",
        )
    return parsed(found, options)


def parsed(found: re.Match[str], options: tuple[str, ...]) -> Answer:
    """Check the pick against the recorded options, word for word."""
    words = found.groupdict()
    pick = words.get("pick")
    if pick is not None and pick.strip() not in options:
        raise Refusal(
            "expert-pick",
            f"{pick!r} is not an option of the brief",
            "copy an option word for word",
        )
    return Answer(
        why=" ".join(found["why"].split()),
        at=clock.now(),
        pick=pick.strip() if pick else None,
        answer=plain(words.get("answer")),
        none=bool(words.get("none")),
    )


def plain(answer: str | None) -> str | None:
    """Collapse whitespace in the record and keep the source file verbatim."""
    return " ".join(answer.split()) if answer else None


def record(source: Path, name: str, expert: str) -> Summary:
    """Record the answer against the seats actually assigned in the brief."""
    folder = folders.existing(source, name)
    path = folder / "record.json"
    with locks.held(folder / ".lock"):
        drafted = msgspec.json.decode(path.read_bytes(), type=Record)
        checked = add(drafted, expert, folder)
        files.write_whole(path, msgspec.json.encode(checked))
    return summary(checked, folder)


def add(drafted: Record, expert: str, folder: Path) -> Record:
    """A second or unknown answer is a refusal."""
    if not any(seat.name == expert for seat in drafted.experts):
        raise Refusal(
            "expert-name",
            f"{expert!r} has no seat in this brief",
            "use a name the brief printed",
        )
    if expert in drafted.answers:
        raise Refusal(
            "expert-answered",
            f"{expert!r} answered already",
            "read the existing record",
        )
    picked = read(folder / f"{expert}.md", drafted.options)
    return msgspec.structs.replace(drafted, answers={**drafted.answers, expert: picked})


def summary(drafted: Record, folder: Path) -> Summary:
    """Show a shared pick only when at least two experts made that pick."""
    picks = {answer.pick for answer in drafted.answers.values()}
    shared = len(picks) == 1 and len(drafted.answers) > 1
    agree = next(iter(picks)) if shared else None
    waiting = tuple(
        seat.name for seat in drafted.experts if seat.name not in drafted.answers
    )
    return Summary(
        **msgspec.structs.asdict(drafted),
        folder=folder.name,
        dir=str(folder),
        agree=agree,
        waiting=waiting,
    )
