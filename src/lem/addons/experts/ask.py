"""Publish the brief and declare the answer file for each expert."""

from typing import TYPE_CHECKING

import msgspec

from lem.addons.cast import project, refs
from lem.addons.experts import audience, brief, folders, seats
from lem.addons.experts.records import Asked, Assigned, Brief, Record
from lem.kernel import clock, files
from lem.kernel.errors import Refusal
from lem.store.places import checkout_of, state_of

if TYPE_CHECKING:
    from pathlib import Path


def inputs(asked: Asked, worktree: Path, source: Path) -> Record:
    """Check the question and its choices before reading the audience."""
    if not asked.question.strip():
        raise Refusal(
            "expert-question", "--question is empty", "give the question in words"
        )
    options = asked.options
    distinct = set(options)
    if len(options) == 1 or len(distinct) != len(options):
        raise Refusal(
            "expert-options",
            "the options do not make a choice",
            "give distinct options or none",
        )
    return Record(
        question=asked.question.strip(),
        context=asked.context.strip(),
        files=tuple(evidence(worktree, name) for name in asked.files),
        options=asked.options,
        checkout=str(worktree),
        asked=clock.now(),
        experts=tuple(
            Assigned(**msgspec.structs.asdict(seat), answer="")
            for seat in seats.chosen(source, asked.seats)
        ),
        answers={},
    )


def evidence(worktree: Path, name: str) -> str:
    """Resolve a named file relative to the checkout the experts read."""
    path = (worktree / name).resolve()
    if not path.exists():
        raise Refusal(
            "expert-file",
            f"the owner's --file {path} is absent",
            "name an existing file",
        )
    return str(path)


def ask(source: Path, asked: Asked) -> Brief:
    """Prepare the files without contacting any expert."""
    drafted = inputs(asked, refs.checkout(source).path, source)
    people = audience.describe(project.resolve(source))
    folder = folders.make(
        state_of(checkout_of(source)), drafted.question, drafted.asked
    )
    return publish(folder, drafted, people)


def assigned(folder: Path, seat: Assigned) -> Assigned:
    """The answer goes to its own path under the question's folder."""
    answer = folder / f"{seat.name}.md"
    return msgspec.structs.replace(seat, answer=str(answer))


def publish(folder: Path, drafted: Record, people: str) -> Brief:
    """The harness reads the brief and the record after both files exist."""
    recorded = msgspec.structs.replace(
        drafted, experts=tuple(assigned(folder, seat) for seat in drafted.experts)
    )
    path = folder / "brief.md"
    files.publish(path, brief.render(recorded, people).encode())
    raw = msgspec.json.encode(recorded)
    files.publish(folder / "record.json", raw)
    return Brief(
        folder=folder.name,
        dir=str(folder),
        brief=str(path),
        worktree=recorded.checkout,
        experts=recorded.experts,
        answers={seat.name: seat.answer for seat in recorded.experts},
        ask=tuple(seat.name for seat in recorded.experts),
    )
