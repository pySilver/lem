"""lem-ask's wait for a page's answer (ask.py), with a stand-in for agterm: what it
prints for a value the page submitted.

    python3 -B -m unittest discover -s tests/unit
"""

import contextlib
import io
import json
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import ask


def printed(value: str) -> tuple[int | None, dict]:
    """What `lem-ask wait` prints, through a UTF-8 output that refuses what UTF-8
    cannot hold, when the page submitted VALUE, and its exit status."""
    reply = json.dumps(
        {
            "ok": True,
            "result": {
                "pageOutcome": {"pageID": "P1", "outcome": "submitted", "value": value}
            },
        }
    )
    raw = io.BytesIO()
    out = io.TextIOWrapper(raw, encoding="utf-8", errors="strict")
    with (
        mock.patch.object(
            ask, "ctl", return_value=types.SimpleNamespace(stdout=reply, stderr="")
        ),
        mock.patch.object(ask, "defaults", return_value={}),
        contextlib.redirect_stdout(out),
    ):
        code = ask.wait_page("P1", 30, status=False)
        out.flush()
    return code, json.loads(raw.getvalue().decode("utf-8"))


class Submitted(unittest.TestCase):
    def test_a_lone_surrogate_prints_as_valid_utf8_and_the_answer_stays(self) -> None:
        # the review of 2026-11-24 on 8b84f438: a page's script sends
        # "🚀".slice(0, 1), one half of a pair, which JSON.stringify writes "\ud83d";
        # the wait raised UnicodeEncodeError where the release before printed it
        code, said = printed('"ship it \\ud83d"')
        self.assertEqual(code, 0)
        self.assertEqual(said["answers"]["answer"]["text"], "ship it �")
        code, said = printed(
            json.dumps(
                {
                    "status": "answered",
                    "answers": {"a": {"selected": [], "text": "go \ud83d now"}},
                }
            )
        )
        self.assertEqual(code, 0)
        self.assertEqual(said["answers"]["a"]["text"], "go � now")
        # a whole pair is the character it makes
        self.assertEqual(
            printed('"\\ud83d\\ude80"')[1]["answers"]["answer"]["text"], "\U0001f680"
        )


if __name__ == "__main__":
    unittest.main()
