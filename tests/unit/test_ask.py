"""lem-ask's wait for a page's answer (ask.py), with a stand-in for agterm: what it
prints for a value the page submitted.

    python3 -B -m unittest discover -s tests/unit
"""

import argparse
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


def past_the_limit() -> str:
    """A JSON object nested as deep as the interpreter's recursion limit, which Python
    cannot hold whatever one level costs: json.loads raises RecursionError on it
    under 3.11, and from 3.12 it decodes and the walk of `whole` raises (3.11 to 3.15,
    2026-11-24). A fixed depth of 600 passed the limit in the walk only while a
    comprehension was a frame of its own, under 3.11."""
    depth = sys.getrecursionlimit()
    return '{"a":' * depth + "1" + "}" * depth


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
        for value in (
            digits,
            f'{{"status": "answered", "n": {digits}}}',
            "[" * 100_000 + "]" * 100_000,
            past_the_limit(),
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
            for text in (f'{{"title": {digits}}}', past_the_limit()):
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
                self.assertIn("spec is JSON that Python cannot read", said["error"])


def page_of(spec: dict) -> str:
    """The text of the page `write_page` writes for SPEC, in a folder of its own."""
    with (
        tempfile.TemporaryDirectory() as folder,
        mock.patch.object(ask, "OUTDIR", folder),
    ):
        ask.check_spec(spec)
        path = ask.write_page(ask.build_html(spec, folder))
        return Path(path).read_bytes().decode("utf-8")


class HalfACharacterInASpec(unittest.TestCase):
    """A spec's text with one half of a UTF-16 pair alone, as JSON writes it
    ("\\ud83d") or as Python reads a byte of argv that is no UTF-8: write_page raised
    UnicodeEncodeError."""

    def test_a_spec_from_a_file_writes_its_page_as_valid_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "spec.json")
            path.write_text(
                '{"title": "ship \\ud83d", "questions": [{"id": "a", "prompt":'
                ' "go \\ud83d\\ude80 \\udc80now", "options": [{"id": "o1",'
                ' "label": "yes \\ud83d"}]}]}',
                encoding="utf-8",
            )
            spec = ask.load_spec(str(path))
        page = page_of(spec)
        self.assertIn("ship �", page)
        self.assertIn("go \U0001f680 �now", page)
        self.assertIn("yes �", page)
        self.assertEqual(spec["title"], "ship �")

    def test_a_quick_question_writes_its_page_as_valid_utf8(self) -> None:
        a = argparse.Namespace(
            prompt="go \udcff",
            options=["*yes \udcff|sub|why"],
            multi=False,
            context="the \ud83d",
            title=None,
        )
        page = page_of(ask.quick_spec(a))
        self.assertIn("go �", page)
        self.assertIn("yes �", page)
        self.assertIn("the �", page)


class WaitWord(unittest.TestCase):
    """The caller's last word on a page's status, which the Stop hook reads
    (`quiet_page`); test_python.AskStopHook plays the run through python.py."""

    def test_the_last_wait_holds_over_the_way_the_page_opened(self) -> None:
        with (
            tempfile.TemporaryDirectory() as folder,
            mock.patch.object(ask, "OUTDIR", folder),
        ):
            loud = {"id": "P1", "file": f"{folder}/x.html"}
            quiet = {"id": "P2", "file": f"{folder}/y{ask.QUIET_PAGE}"}
            self.assertEqual(
                (ask.quiet_page(loud), ask.quiet_page(quiet)), (False, True)
            )
            ask.keep_wait_word("P1", status=False)
            ask.keep_wait_word("P2", status=True)
            self.assertEqual(
                (ask.quiet_page(loud), ask.quiet_page(quiet)), (True, False)
            )
            ask.keep_wait_word("P1", status=True)
            self.assertFalse(ask.quiet_page(loud))
            # an id that is no plain file name keeps no word, and writes nowhere
            ask.keep_wait_word("../P3", status=False)
            self.assertFalse(ask.quiet_page({"id": "../P3", "file": "z.html"}))
            self.assertEqual(
                sorted(p.name for p in Path(folder).iterdir()),
                ["P1.wait.html", "P2.wait.html"],
            )


if __name__ == "__main__":
    unittest.main()
