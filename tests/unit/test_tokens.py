"""lem_tokens.py: the tokens of a task's Claude Code sessions, over small transcripts in the form Claude
Code writes them (one record a line; a reply's blocks share one `message.id` and its `usage`).

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
lem_tokens = importlib.import_module("lem_tokens")

SLUG = "gift-note"


def reply(message: str, given: int, said: int, read: int = 0, wrote: int = 0, side: bool = False) -> dict:
    return {"type": "assistant", "isSidechain": side, "message": {"id": message, "role": "assistant", "content": [{"type": "text", "text": "x"}],
            "usage": {"input_tokens": given, "output_tokens": said, "cache_read_input_tokens": read, "cache_creation_input_tokens": wrote,
                      "output_tokens_details": {"thinking_tokens": 1}, "service_tier": "standard"}}}


def write(file: Path, *records: object) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("".join((record if isinstance(record, str) else json.dumps(record)) + "\n" for record in records), encoding="utf-8")


class Tokens(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        root = Path(self.folder.name)
        self.state = root / "state"
        self.state.mkdir()
        self.projects = root / "projects" / "-shop"

    def log(self, *transcripts: tuple[str, str]) -> None:
        lines = [{"ts": "2026-11-21T10:00:00Z", "event": "session.open", "task": SLUG, "session": "S-1"}]
        lines += [{"ts": "2026-11-21T10:00:01Z", "event": "session.transcript", "task": task, "claude": Path(path).stem, "transcript": path, "source": "startup"}
                  for task, path in transcripts]
        write(self.state / "events.jsonl", *lines)

    def test_a_task_with_no_transcript_on_record_has_no_number(self):
        self.log()
        self.assertIsNone(lem_tokens.task_tokens(self.state, SLUG))

    def test_each_reply_counts_once_with_its_subagents_and_another_tasks_session_counts_for_none(self):
        first, second, other = (self.projects / f"{name}.jsonl" for name in ("aaa", "bbb", "ccc"))
        # one reply written as two records (two blocks), a user record, a line that does not read
        write(first, {"type": "user", "message": {"content": "go"}}, reply("m1", 3, 100, 1000, 50), reply("m1", 3, 100, 1000, 50), reply("m2", 2, 10), "{half")
        write(self.projects / "aaa" / "subagents" / "agent-a1.jsonl", reply("s1", 5, 20, 7, 9, side=True), reply("s1", 5, 20, 7, 9, side=True))
        (self.projects / "aaa" / "subagents" / "agent-a1.meta.json").write_text('{"agentType": "lem:lem-builder"}')
        write(second, reply("m3", 1, 1))
        write(other, reply("m9", 1000, 1000))
        self.log((SLUG, str(first)), (SLUG, str(second)), (SLUG, str(first)), ("another-task", str(other)))
        found = lem_tokens.task_tokens(self.state, SLUG)
        self.assertEqual({key: found[key] for key in ("input", "output", "cache_read", "cache_write", "sessions", "subagents", "missing", "unread")},
                         {"input": 11, "output": 131, "cache_read": 1007, "cache_write": 59, "sessions": 2, "subagents": 1, "missing": 0, "unread": 1})
        self.assertIn("(2) and their subagents (1)", found["covers"])
        self.assertIn("a Codex reviewer, an expert of another provider and a session on another machine are not in it", found["covers"])

    def test_a_transcript_that_is_gone_is_counted_and_said(self):
        kept = self.projects / "aaa.jsonl"
        write(kept, reply("m1", 1, 2))
        self.log((SLUG, str(kept)), (SLUG, str(self.projects / "gone.jsonl")))
        found = lem_tokens.task_tokens(self.state, SLUG)
        self.assertEqual((found["output"], found["sessions"], found["missing"]), (2, 1, 1))
        self.assertIn("1 transcript the log names is gone", found["covers"])


if __name__ == "__main__":
    unittest.main()
