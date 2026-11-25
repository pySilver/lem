"""The framed lines of `sessions.jsonl`, read past a torn, damaged or newer line, and the
owner's presence, written only when it changes."""

import json
import threading
from datetime import timedelta
from typing import TYPE_CHECKING

from fakes.records import MOMENT
from lem.records.owner import Change, Presence
from lem.records.sessions import SessionLine
from lem.store import owner, sessions

if TYPE_CHECKING:
    from pathlib import Path


def line(number: int) -> SessionLine:
    """The session `number` of a task."""
    return SessionLine(
        at=MOMENT,
        source="startup",
        claude=f"claude-{number}",
        transcript=f"/t/{number}.jsonl",
        pane=f"pane-{number}",
        task="fix-the-login",
    )


def test_a_framed_line_reads_back_and_carries_its_form(tmp_path: Path) -> None:
    sessions.append(tmp_path, line(1))
    written = (tmp_path / "sessions.jsonl").read_bytes()
    assert written.startswith(b'\n{"v":1,')
    assert written.endswith(b"}\n")
    assert sessions.read(tmp_path) == (line(1),)


def test_a_torn_line_a_damaged_one_and_a_newer_form_are_skipped(
    tmp_path: Path,
) -> None:
    sessions.append(tmp_path, line(1))
    newer = {"v": 2, "at": "2026-11-25T10:00:00Z", "pane": "the next form"}
    with (tmp_path / "sessions.jsonl").open("a") as stream:
        stream.write('\n{"v":1,"at":"2026-11-25T10:00:00Z","sour')  # a writer cut off
        stream.write("\nnot json at all\n")
        stream.write(f"\n{json.dumps(newer)}\n")
    sessions.append(tmp_path, line(2))
    assert sessions.read(tmp_path) == (line(1), line(2))


def test_writers_at_once_never_mix_their_lines(tmp_path: Path) -> None:
    threads = [
        threading.Thread(target=sessions.append, args=(tmp_path, line(number)))
        for number in range(40)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    read = sessions.read(tmp_path)
    assert sorted(found.claude for found in read) == sorted(
        f"claude-{number}" for number in range(40)
    )


def test_no_sessions_file_is_no_session(tmp_path: Path) -> None:
    assert sessions.read(tmp_path) == ()


def test_the_owner_is_there_until_he_says_he_is_away(tmp_path: Path) -> None:
    assert owner.read(tmp_path) == Presence()
    later = MOMENT + timedelta(hours=1)
    away = owner.change(tmp_path, "at the dentist", MOMENT, away=True)
    went = Change(away=True, at=MOMENT, words="at the dentist")
    assert away == Presence(
        away=True, since=MOMENT, words="at the dentist", seen=1, changes=(went,)
    )
    assert owner.change(tmp_path, "at the dentist", later, away=True) == away
    back = owner.change(tmp_path, None, later, away=False)
    came = Change(away=False, at=later)
    assert back == Presence(
        away=False, since=later, words=None, seen=2, changes=(went, came)
    )
    assert owner.change(tmp_path, None, later, away=False) == back
    assert owner.read(tmp_path) == back


def test_a_line_with_a_separator_python_splits_at_reads_back_whole(
    tmp_path: Path,
) -> None:
    odd = SessionLine(
        at=MOMENT,
        source="resume",
        claude="claude-\u2028x",
        transcript="/t/a\u2029b\u0085.jsonl",
        task="fix-the-login",
    )
    sessions.append(tmp_path, odd)
    sessions.append(tmp_path, line(2))
    assert sessions.read(tmp_path) == (odd, line(2))
