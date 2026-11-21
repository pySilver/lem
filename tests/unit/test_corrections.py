"""corrections.py's rules that read a file and return a result, each called in this process. The hook,
the queue and the review are facts of real runs, in tests/lem-machine.sh.

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


if __name__ == "__main__":
    unittest.main()
