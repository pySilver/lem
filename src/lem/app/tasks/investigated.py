"""`lem task investigated`: what the investigation of a bug or a question found, written after
Lem read the investigator's report; it ends the investigation's span, and a bug that was not
reproduced waits for one more fact from the owner."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.tasks import release
from lem.kernel import clock
from lem.model.task import investigation
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.work import Investigation

# The investigator's report in the task's folder.
REPORT = "investigation.md"


def investigated(
    state: Path, slug: str, given: investigation.Findings
) -> Investigation:
    """Write the findings `given` on the task `slug`, with its report when it is there."""
    record = release.checked(state, slug)
    report = REPORT if (places.task_folder(state, slug) / REPORT).is_file() else None
    now = clock.now()
    found = investigation.investigation(given, report=report, now=now)
    change = partial(investigation.investigated, found=found, now=now)
    tasks.update(state, slug, change, record.revision)
    return found
