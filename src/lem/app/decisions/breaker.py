"""`lem decisions breaker`: the circuit breaker, recorded with its cause and its document, and the
task held until the owner's help, park or drop (`decisions.cmd_breaker` on `main`).

The agent that stops commits what the task has, writes `handoff.md` and `breaker.md` in the task's
folder, and runs this. The document is kept under the breaker's number before the record cites
it, and `breaker.md` goes, so that a second breaker never writes over the first one's.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.criteria import texts, where
from lem.app.decisions import stopping
from lem.kernel import clock, files
from lem.model.decisions import breaker, document
from lem.records.decisions import Breaker
from lem.store import guard, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.decisions.writing import Change
    from lem.app.wiring import Ports
    from lem.records.record import Record


def made_of(record: Record, asked: stopping.Asked, path: Path) -> tuple[Breaker, bytes]:
    """The breaker the record keeps, numbered after the task's last decision, and the bytes of
    its document."""
    raw = texts.bytes_of(path, "the breaker's document")
    number = len(record.task.decisions) + 1
    title = document.title_of(texts.text_of(raw, path), str(path))
    made = Breaker(
        id=number,
        at=clock.now(),
        cause=asked.cause,
        what=title,
        document=breaker.kept_name(number),
        handoff=breaker.HANDOFF,
        irreversible=asked.kind,
    )
    return made, raw


def tripped(ports: Ports, folder: Path, slug: str, asked: stopping.Asked) -> Breaker:
    """Trip the breaker `asked` of the task `slug`: its document kept, then the record."""
    here = where.here_of(folder, slug)
    record = here.read()
    path = stopping.checked(ports, here, record, asked)
    made, raw = made_of(record, asked, path)
    guard.writable(here.workspace.state)
    files.publish(here.folder / made.document, raw)
    tasks.update(here.workspace.state, slug, holding(made, asked), record.revision)
    path.unlink()
    return made


def holding(made: Breaker, asked: stopping.Asked) -> Change:
    """The write of the breaker `made`, which holds the task with its line."""
    why = breaker.why_of(asked.cause, asked.kind)
    return partial(breaker.tripped, breaker=made, why=why, now=made.at)
