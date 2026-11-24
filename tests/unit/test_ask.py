"""lem-ask's wait for a page's answer (ask.py), with a stand-in for agterm: what it
prints for a value the page submitted.

    python3 -B -m unittest discover -s tests/unit
"""

import contextlib
import io
import json
import sys
import tempfile
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

    def test_json_python_cannot_hold_is_kept_as_its_text(self) -> None:
        # a number of more than sys.get_int_max_str_digits() digits made json.loads
        # raise ValueError, and nesting deeper than the stack RecursionError, in the
        # decode or in the walk of `whole`: the wait ended with a traceback
        digits = "9" * (sys.get_int_max_str_digits() + 1)
        deep = '{"a":' * 600 + "1" + "}" * 600
        for value in (
            digits,
            f'{{"status": "answered", "n": {digits}}}',
            "[" * 100_000 + "]" * 100_000,
            deep,
        ):
            code, said = printed(value)
            self.assertEqual(code, 0)
            self.assertEqual(said["answers"]["answer"]["text"], value)


class LoadSpec(unittest.TestCase):
    def test_json_python_cannot_hold_in_a_spec_is_refused_with_a_message(self) -> None:
        # the same decode for a spec: a traceback where a spec that is no JSON is
        # refused with exit 1 and a message
        digits = "9" * (sys.get_int_max_str_digits() + 1)
        with tempfile.TemporaryDirectory() as folder:
            for text in (f'{{"title": {digits}}}', "[" * 100_000):
                path = Path(folder, "spec.json")
                path.write_text(text, encoding="utf-8")
                out = io.StringIO()
                with (
                    contextlib.redirect_stdout(out),
                    self.assertRaises(SystemExit) as stop,
                ):
                    ask.load_spec(str(path))
                self.assertEqual(stop.exception.code, 1)
                said = json.loads(out.getvalue())
                self.assertEqual(said["status"], "error")
                self.assertIn("spec", said["error"])


if __name__ == "__main__":
    unittest.main()
