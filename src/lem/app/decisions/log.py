"""`lem decisions log`: a decision, written with the number the record gives it
(`decisions.cmd_log` on `main`)."""

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.criteria import texts, where
from lem.app.decisions import experts
from lem.app.decisions.writing import Change, written
from lem.kernel import clock
from lem.model.decisions import chart, log

if TYPE_CHECKING:
    from lem.app.wiring import Ports
    from lem.records.decisions import Taken
    from lem.records.record import Record


def taking(asked: log.Logged, record: Record) -> tuple[Change, Taken]:
    """The decision `asked` for the record as it is."""
    now = clock.now()
    taken = log.taken_of(asked, len(record.task.decisions) + 1, now)
    return partial(log.logged, asked=asked, now=now), taken


def charted(path: str | None) -> str | None:
    """The chart of the file `path`, checked, or None with no file."""
    if path is None:
        return None
    named = Path(path)
    text = texts.text_of(texts.bytes_of(named, "one mermaid chart"), named)
    return chart.chart_of(text, path)


def logged(
    ports: Ports, folder: Path, slug: str, asked: log.Logged, chart_file: str | None
) -> Taken:
    """`lem decisions log SLUG ...`: the decision, its chart read from `chart_file`, and for
    `--by experts` the experts that answer here."""
    here = where.here_of(folder, slug)
    asked = replace(asked, chart=charted(chart_file))
    if asked.by == "experts":
        found = experts.here(ports.harness, here.workspace.checkout)
        asked = replace(asked, advisers=found)
    return written(here.workspace.state, slug, partial(taking, asked))
