"""The persona panel's rules for a persona's file, as calls of cast.py's functions: the frontmatter
that names the seats a persona answers on, the seats when the file names none, a seat refused as the
settings refuse it, a seat whose agent is not on this machine, and the text a persona's agent reads
as who it is. Where the cast comes from (the checkout or the default branch) is a fact only git
shows, and tests/test-gate-panel.sh checks it in real repositories.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "skills" / "lem-panel" / "scripts")
)
cast = importlib.import_module("cast")

FILE = Path("/lem-unit/repo/.lem/personas/merchant.md")
BODY = "# A merchant\n\n## Who they are\n\nSells shoes in two shops.\n"


def everywhere(agent: str) -> bool:
    return True


def no_codex(agent: str) -> bool:
    return agent == "claude"


def seats(*lines: str, here=everywhere) -> dict:
    """The seats of a persona whose file opens with a frontmatter of these lines."""
    meta, _ = cast.frontmatter(
        "---\n" + "".join(f"{line}\n" for line in lines) + "---\n" + BODY, FILE
    )
    return cast.seats_of(meta, FILE, here)


class Refuses(unittest.TestCase):
    def refused(self, call, *args) -> str:
        with self.assertRaises(cast.CastError) as caught:
            call(*args)
        return str(caught.exception)


class Frontmatter(Refuses):
    """The frontmatter is read for the seats, and is not a part of the person."""

    def test_the_seats_are_read_and_the_text_after_it_is_the_person(self) -> None:
        meta, body = cast.frontmatter(
            '---\nseats: ["claude/opus:high", "codex/gpt-6.2-sol:high"]\n---\n\n'
            + BODY,
            FILE,
        )
        self.assertEqual(
            meta, {"seats": '["claude/opus:high", "codex/gpt-6.2-sol:high"]'}
        )
        self.assertEqual(body, BODY)
        self.assertNotIn("seats", body)

    def test_a_file_with_no_frontmatter_is_the_person_whole(self) -> None:
        self.assertEqual(cast.frontmatter(BODY, FILE), ({}, BODY))
        # a `---` further down is a rule of markdown, not a frontmatter
        text = BODY + "\n---\n\nMore.\n"
        self.assertEqual(cast.frontmatter(text, FILE), ({}, text))

    def test_a_blank_line_and_a_comment_are_skipped(self) -> None:
        meta, _ = cast.frontmatter(
            '---\n# chosen by the owner\n\nseats: ["claude/opus:high"]\n---\n' + BODY,
            FILE,
        )
        self.assertEqual(meta, {"seats": '["claude/opus:high"]'})

    def test_a_frontmatter_never_closed_another_key_and_a_line_twice_are_refused_with_the_file(
        self,
    ) -> None:
        for text, said in (
            ('---\nseats: ["claude/opus:high"]\n' + BODY, "no `---` line closes it"),
            ("---\nmodel: opus\n---\n" + BODY, "knows only `seats`, not 'model'"),
            (
                '---\nseats: ["claude/opus"]\nseats: ["codex"]\n---\n' + BODY,
                "`seats` is written twice",
            ),
            ("---\njust words\n---\n" + BODY, "is no `key: value` line"),
        ):
            with self.subTest(said=said):
                message = self.refused(cast.frontmatter, text, FILE)
                self.assertIn(str(FILE), message)
                self.assertIn(said, message)


class Seats(Refuses):
    """A persona answers once on each seat its file names, or on the panel's own two seats."""

    def test_a_file_names_its_seats_each_with_its_parts_and_its_name(self) -> None:
        found = seats('seats: ["claude/opus:high", "codex/gpt-6.2-sol:xhigh"]')
        self.assertEqual(found["seats_from"], "file")
        self.assertEqual(
            [
                (s["seat"], s["agent"], s["model"], s["effort"], s["name"], s["here"])
                for s in found["seats"]
            ],
            [
                ("claude/opus:high", "claude", "opus", "high", "opus", True),
                (
                    "codex/gpt-6.2-sol:xhigh",
                    "codex",
                    "gpt-6.2-sol",
                    "xhigh",
                    "sol",
                    True,
                ),
            ],
        )
        self.assertEqual(found["left_out"], [])
        # one seat is a persona that answers once
        self.assertEqual(
            [s["name"] for s in seats('seats: ["claude/fable:max"]')["seats"]],
            ["fable"],
        )

    def test_a_file_with_no_seats_answers_as_the_panel_always_did(self) -> None:
        found = cast.seats_of({}, FILE, everywhere)
        self.assertEqual(found["seats_from"], "default")
        self.assertEqual(
            [(s["agent"], s["model"], s["name"]) for s in found["seats"]],
            [("claude", "opus", "opus"), ("codex", None, "sol")],
        )
        self.assertEqual(seats("# no seats chosen yet"), found)

    def test_a_codex_seat_with_no_codex_is_left_out(self) -> None:
        found = seats(
            'seats: ["claude/opus:high", "codex/gpt-6.2-sol:high"]', here=no_codex
        )
        self.assertEqual([s["seat"] for s in found["seats"]], ["claude/opus:high"])
        self.assertEqual(
            [(s["seat"], s["here"]) for s in found["left_out"]],
            [("codex/gpt-6.2-sol:high", False)],
        )
        self.assertEqual(
            [s["name"] for s in cast.seats_of({}, FILE, no_codex)["left_out"]], ["sol"]
        )
        # a persona of codex seats only has none left on such a machine, and the panel names it
        self.assertEqual(
            seats('seats: ["codex/gpt-6.2-sol:high"]', here=no_codex)["seats"], []
        )

    def test_a_seat_the_settings_would_refuse_is_refused_with_the_file_and_the_line_to_write(
        self,
    ) -> None:
        for line, said in (
            (
                'seats: ["gemini/pro:high"]',
                "the agent 'gemini' must be claude or codex",
            ),
            ('seats: ["claude/opus:high:max"]', "holds 2 `:`"),
            ('seats: ["claude/"]', "names no model after the `/`"),
            ('seats: ["claude/opus high"]', "holds a space"),
            (
                "seats: claude/opus:high",
                "is not a list of one seat or more in double quotes",
            ),
            (
                "seats: ['claude/opus:high']",
                "is not a list of one seat or more in double quotes",
            ),
            ("seats: []", "is not a list of one seat or more in double quotes"),
            ("seats: [1]", "must be one string"),
        ):
            with self.subTest(line=line):
                message = self.refused(seats, line)
                self.assertIn(str(FILE), message)
                self.assertIn(said, message)
                self.assertIn(cast.SEATS_LINE, message)

    def test_two_seats_of_one_name_are_refused(self) -> None:
        message = self.refused(seats, 'seats: ["claude/opus:high", "claude/opus:max"]')
        self.assertIn("two seats are named opus", message)


class Person(unittest.TestCase):
    """What a persona's agent reads as who it is."""

    def test_a_file_with_no_frontmatter_is_read_where_it_is(self) -> None:
        with tempfile.TemporaryDirectory() as top:
            path = Path(top) / "merchant.md"
            path.write_text(BODY, encoding="utf-8")
            with mock.patch.object(cast, "state_file") as written:
                found = cast.persona(Path(top), path, everywhere)
            written.assert_not_called()
            self.assertEqual(
                (found["stem"], found["path"], found["person"], found["seats_from"]),
                ("merchant", str(path), str(path), "default"),
            )

    def test_a_file_with_a_frontmatter_is_read_without_it(self) -> None:
        with tempfile.TemporaryDirectory() as top:
            path = Path(top) / "merchant.md"
            path.write_text(
                '---\nseats: ["claude/opus:high"]\n---\n' + BODY, encoding="utf-8"
            )
            with mock.patch.object(
                cast, "state_file", return_value=Path(top) / "copy.md"
            ) as written:
                found = cast.persona(Path(top), path, everywhere)
            folder, name, body = written.call_args.args[1:]
            self.assertEqual((folder, body.decode("utf-8")), ("personas-person", BODY))
            self.assertTrue(name.startswith("merchant-") and name.endswith(".md"))
            self.assertEqual(
                (found["path"], found["person"]),
                (str(path), str(Path(top) / "copy.md")),
            )
            self.assertEqual([s["seat"] for s in found["seats"]], ["claude/opus:high"])

    def test_a_copy_read_again_takes_the_time_of_the_read(self) -> None:
        """`lem project prune` removes a copy by its last write, so a read writes its time on it."""
        import os
        import time

        with tempfile.TemporaryDirectory() as top:
            with mock.patch.object(cast, "cache", return_value=Path(top)):
                copy = cast.state_file(
                    Path(top), "personas-person", "merchant-1.md", b"body"
                )
                old = time.time() - 40 * 86400
                os.utime(copy, (old, old))
                self.assertEqual(
                    cast.state_file(
                        Path(top), "personas-person", "merchant-1.md", b"body"
                    ),
                    copy,
                )
            self.assertGreater(copy.stat().st_mtime, time.time() - 60)


if __name__ == "__main__":
    unittest.main()
