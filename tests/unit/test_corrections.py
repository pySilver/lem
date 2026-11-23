"""corrections.py's rules that read a file and return a result, each called in this process. The hook,
the queue and the review are facts of real runs, in tests/lem-machine.sh.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
corrections = importlib.import_module("corrections")


def said(text: str) -> dict:
    return {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


class LastAgentText(unittest.TestCase):
    """The newest text an agent wrote, from a Claude Code transcript, one JSON record a line."""

    def test_a_text_that_holds_a_line_separator_is_the_newest_text(self):
        # Claude Code's JSON keeps U+2028 and U+2029 as they are inside a string
        newest = "first a\N{LINE SEPARATOR}b\N{PARAGRAPH SEPARATOR}c\x85d"
        with tempfile.TemporaryDirectory() as folder:
            transcript = Path(folder) / "session.jsonl"
            transcript.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in (said("older"), said(newest))), encoding="utf-8")
            self.assertEqual(corrections.last_agent_text(str(transcript)), newest)


class ProposedLesson(unittest.TestCase):
    """A retro changes no file: a lesson it finds goes into a proposal of its day, and its group is
    recorded `proposed`, with the file the proposal would change and the proposal's name, so that
    `lessons` gives it as a lesson in no file yet (stages/learn.md, "The correction queue")."""

    LESSON = "A night names the item it left out and why (retro of 2026-11-24 #3)."
    TARGET = "skills/lem/stages/night.md"

    def test_record_takes_the_verdict_proposed(self):
        args = corrections.arguments().parse_args(["record", "1a2b3c4d", "--decision", "lesson", "--verdict", "proposed",
                                                   "--target", self.TARGET, "--lesson", self.LESSON])
        self.assertEqual((args.verdict, args.target, args.lesson), ("proposed", self.TARGET, self.LESSON))

    def test_lessons_gives_a_proposed_lesson_with_its_verdict_and_its_target(self):
        owner = "you left out the item again and did not say why"
        with tempfile.TemporaryDirectory() as folder:
            where = Path(folder)
            (where / "corrections.jsonl").write_text(
                json.dumps({"ts": "2026-11-24T06:10:00Z", "session": "s-1", "owner": owner, "previous": "", "p_lesson": 0.8}) + "\n",
                encoding="utf-8")
            gid = corrections.group_id(owner)
            with mock.patch("sys.stdout", new=io.StringIO()):
                corrections.cmd_record(where, gid, "lesson", "proposed", self.TARGET, self.LESSON)
            with mock.patch("sys.stdout", new=io.StringIO()) as out:
                corrections.cmd_lessons(where)
            rows = json.loads(out.getvalue())
            self.assertEqual([(r["lesson"], r["target"], r["verdict"], r["days"]) for r in rows],
                             [(self.LESSON, self.TARGET, "proposed", ["2026-11-24"])])
            self.assertEqual(corrections.unreviewed(where), {})


if __name__ == "__main__":
    unittest.main()
