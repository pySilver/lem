"""Each framed journal writer reports a short append."""

import os
from typing import TYPE_CHECKING, Literal

import pytest

from fakes.records import MOMENT
from lem.app.sessions import acts, log
from lem.board.duties.merge_line import Waited, noted
from lem.records.sessions import SessionLine
from lem.store import sessions
from unit.owner.looked import TIP
from unit.sessions.world import SLUG, here_of, made

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("writer", ["merge", "act", "session"])
def test_a_short_journal_append_reports_the_io_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    writer: Literal["merge", "act", "session"],
) -> None:
    here = here_of(tmp_path)
    made(here)
    folder = here.folder(SLUG)
    writes: list[bytes] = []

    def short(fd: int, frame: bytes) -> int:
        writes.append(frame)
        return len(frame) - 1

    with monkeypatch.context() as patch:
        patch.setattr(os, "write", short)
        with pytest.raises(OSError):
            if writer == "merge":
                noted(
                    here.where.state,
                    Waited(
                        at=MOMENT,
                        task=SLUG,
                        tip=TIP,
                        by="merger",
                        waiting=0,
                        behind=(),
                    ),
                )
            elif writer == "act":
                log.append(folder, acts.Wake(at=MOMENT, session="one", why="queue"))
            else:
                sessions.append(
                    folder,
                    SessionLine(
                        at=MOMENT,
                        source="resume",
                        claude="one",
                        transcript="/transcripts/one.jsonl",
                        task=SLUG,
                    ),
                )

    (frame,) = writes
    assert frame.startswith(b"\n{")
    assert frame.endswith(b"}\n")
