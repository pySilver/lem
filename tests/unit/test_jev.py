"""jev.py, Lem's client of the Jev decision model: build(), which checks a spec and
makes the request body of a choice and of a noul, and read(), which makes the printed
reply from Jev's. No case sends a request; the replies are in the form a real request
through OpenRouter gave on 2026-11-23 (`{"type": "noul", "noul": 0.98}` for a noul).

    python3 -B -m unittest discover -s tests/unit
"""

import json
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import jev  # noqa: E402 - after the line that puts src on sys.path

CHOICE = {
    "type": "choice",
    "instructions": "Is this a lesson?",
    "choices": {"lesson": "it teaches", "no_lesson": "it moves on"},
}
NOUL = {"type": "noul", "instructions": "Does the owner correct the agent?"}


def spec(*questions: dict, state: object = "the agent said; the owner said") -> dict:
    return {
        "state": state,
        "model": "typesafe/jev-1.14",
        "questions": {f"q{n}": q for n, q in enumerate(questions)},
    }


class Build(unittest.TestCase):
    def refused(self, given: dict) -> str:
        with self.assertRaises(jev.SpecError) as raised:
            jev.build(given)
        return str(raised.exception)

    def test_a_choice_is_sent_with_its_choices_as_criteria(self) -> None:
        body = jev.build(spec(CHOICE))
        self.assertEqual(
            body["questions"],
            {
                "q0": {
                    "type": "choice",
                    "instructions": "Is this a lesson?",
                    "criteria": {"lesson": "it teaches", "no_lesson": "it moves on"},
                }
            },
        )
        self.assertEqual(
            (body["model"], body["state"]),
            ("typesafe/jev-1.14", "the agent said; the owner said"),
        )

    def test_a_noul_without_yes_and_no_is_sent_without_criteria(self) -> None:
        self.assertEqual(
            jev.build(spec(NOUL))["questions"],
            {
                "q0": {
                    "type": "noul",
                    "instructions": "Does the owner correct the agent?",
                }
            },
        )

    def test_a_noul_with_yes_and_no_sends_them_as_criteria_true_and_false(self) -> None:
        body = jev.build(
            spec(
                {
                    **NOUL,
                    "yes": "the owner says the agent was wrong",
                    "no": "the owner only moves the work on",
                },
                CHOICE,
            )
        )
        self.assertEqual(
            body["questions"]["q0"],
            {
                "type": "noul",
                "instructions": "Does the owner correct the agent?",
                "criteria": {
                    "true": "the owner says the agent was wrong",
                    "false": "the owner only moves the work on",
                },
            },
        )
        self.assertEqual(body["questions"]["q1"]["type"], "choice")

    def test_a_question_with_no_type_or_another_type_is_refused_with_the_two_types(
        self,
    ) -> None:
        untyped = {key: value for key, value in CHOICE.items() if key != "type"}
        for question, said in (
            (untyped, "names no type"),
            ({**CHOICE, "type": "score"}, "has type 'score'"),
            ({**CHOICE, "type": None}, "names no type"),
        ):
            message = self.refused(spec(question))
            self.assertIn(f"question 'q0' {said}", message)
            self.assertIn('"type": "choice"', message)
            self.assertIn('"type": "noul"', message)
        self.assertIn(
            "names no type", self.refused({"state": "s", "questions": {"q0": "a text"}})
        )

    def test_a_noul_with_choices_and_a_choice_with_yes_or_no_are_refused(self) -> None:
        self.assertIn(
            (
                "is a noul and takes only type, instructions, yes and no; "
                "choices belong to a choice"
            ),
            self.refused(spec({**NOUL, "choices": CHOICE["choices"]})),
        )
        for extra in ({"yes": "y"}, {"no": "n"}, {"yes": "y", "no": "n"}):
            self.assertIn(
                (
                    "is a choice and takes only type, instructions and choices; "
                    "yes and no belong to a noul"
                ),
                self.refused(spec({**CHOICE, **extra})),
            )

    def test_a_noul_takes_both_yes_and_no_each_with_text_or_neither(self) -> None:
        for extra in (
            {"yes": "y"},
            {"no": "n"},
            {"yes": "y", "no": " "},
            {"yes": None, "no": "n"},
            {"yes": "y", "no": 1},
        ):
            self.assertIn(
                (
                    "needs both yes and no, each a text that says what that "
                    "answer means, or neither"
                ),
                self.refused(spec({**NOUL, **extra})),
            )

    def test_each_type_needs_instructions_and_a_choice_two_choices_with_a_meaning(
        self,
    ) -> None:
        for question in (
            {**NOUL, "instructions": " "},
            {"type": "noul"},
            {**CHOICE, "instructions": ""},
        ):
            self.assertIn(
                "question 'q0' needs instructions", self.refused(spec(question))
            )
        for choices in (
            {"a": "x"},
            {"a": "x", "b": ""},
            {"a": "x", "b": 2},
            ["a", "b"],
        ):
            self.assertIn(
                "needs at least two choices, each with a meaning",
                self.refused(spec({**CHOICE, "choices": choices})),
            )

    def test_a_state_is_a_non_empty_string_object_or_array(self) -> None:
        facts = {"agent": "I pushed it.", "owner": "you should have asked first"}
        self.assertEqual(jev.build(spec(NOUL, state=facts))["state"], facts)
        self.assertEqual(
            jev.build(spec(NOUL, state=["one fact", "another"]))["state"],
            ["one fact", "another"],
        )
        for state in ("", "  ", {}, [], None, 3, True):
            self.assertEqual(
                self.refused(spec(NOUL, state=state)),
                "state must be a non-empty string, or a non-empty JSON object or array",
            )

    def test_a_state_object_counts_the_bytes_of_its_json_text(self) -> None:
        questions = json.dumps(jev.build(spec(NOUL))["questions"]).encode()
        # the JSON text of {"facts": "ééé..."} is 13 bytes and the text's own: an é is
        # two bytes of UTF-8, not a six-byte escape
        room = jev.LIMIT_BYTES - len(questions) - len('{"facts": ""}')
        fits = {"facts": "é" * (room // 2)}
        self.assertEqual(
            len(json.dumps(fits, ensure_ascii=False).encode()) + len(questions),
            jev.LIMIT_BYTES - room % 2,
        )
        self.assertEqual(jev.build(spec(NOUL, state=fits))["state"], fits)
        with self.assertRaises(OverflowError) as raised:
            jev.build(spec(NOUL, state={"facts": "é" * (room // 2 + 1)}))
        self.assertIn(
            f"over the {jev.LIMIT_BYTES} past which OpenRouter runs Jev",
            str(raised.exception),
        )
        self.assertIn("never a cut-down copy", str(raised.exception))

    def test_a_string_state_counts_its_utf8_bytes(self) -> None:
        questions = len(json.dumps(jev.build(spec(NOUL))["questions"]).encode())
        jev.build(spec(NOUL, state="x" * (jev.LIMIT_BYTES - questions)))
        with self.assertRaises(OverflowError):
            jev.build(spec(NOUL, state="é" * ((jev.LIMIT_BYTES - questions) // 2 + 1)))


class Read(unittest.TestCase):
    QUESTIONS = {"lesson": {"type": "choice"}, "corrects": {"type": "noul"}}
    CHOSEN = {
        "type": "choice",
        "choice": "lesson",
        "confidence": 0.9,
        "probabilities": {"lesson": 0.9, "no_lesson": 0.1},
    }

    def failed(self, answers: object, questions: dict | None = None) -> str:
        with self.assertRaises(RuntimeError) as raised:
            jev.read({"model": "m", "answers": answers}, questions or self.QUESTIONS)
        return str(raised.exception)

    def test_each_answer_carries_its_type_and_what_its_type_has(self) -> None:
        reply = {
            "model": "typesafe/jev-1.14",
            "answers": {
                "lesson": self.CHOSEN,
                "corrects": {"type": "noul", "noul": 0.98},
            },
            "usage": {"cost": 0.0004, "tokens": 120},
        }
        self.assertEqual(
            jev.read(reply, self.QUESTIONS),
            {
                "model": "typesafe/jev-1.14",
                "answers": {
                    "lesson": self.CHOSEN,
                    "corrects": {"type": "noul", "noul": 0.98},
                },
                "cost": 0.0004,
            },
        )

    def test_a_noul_of_0_or_1_reads_and_a_reply_with_no_cost_reads_as_null(
        self,
    ) -> None:
        for noul in (0, 1, 0.5):
            read = jev.read(
                {"model": "m", "answers": {"q": {"type": "noul", "noul": noul}}},
                {"q": {"type": "noul"}},
            )
            self.assertEqual(
                (read["answers"]["q"], read["cost"]),
                ({"type": "noul", "noul": noul}, None),
            )
        self.assertIsNone(
            jev.read(
                {"answers": {"q": {"noul": 0.2}}, "usage": "free"},
                {"q": {"type": "noul"}},
            )["cost"]
        )

    def test_a_noul_with_no_number_is_a_failed_request_that_names_the_question(
        self,
    ) -> None:
        for given in (
            {"type": "noul"},
            {"type": "noul", "noul": None},
            {"type": "noul", "noul": "0.9"},
            {"type": "noul", "noul": 1.5},
            {"type": "noul", "noul": True},
            {"type": "choice", "noul": 0.9},
            None,
            0.9,
        ):
            message = self.failed({"lesson": self.CHOSEN, "corrects": given})
            self.assertIn(
                (
                    "the reply's answer to question 'corrects', a noul, lacks a noul, "
                    "a number from 0 to 1"
                ),
                message,
            )

    def test_a_choice_with_no_probabilities_is_a_failed_request_that_names_the_question(
        self,
    ) -> None:
        noul = {"type": "noul", "noul": 0.2}
        broken = (
            {
                key: value
                for key, value in self.CHOSEN.items()
                if key != "probabilities"
            },
            {**self.CHOSEN, "probabilities": {}},
            {**self.CHOSEN, "probabilities": {"lesson": None}},
            {**self.CHOSEN, "confidence": None},
            {key: value for key, value in self.CHOSEN.items() if key != "choice"},
            {"type": "noul", "noul": 0.9},
        )
        for given in broken:
            message = self.failed({"lesson": given, "corrects": noul})
            self.assertIn(
                (
                    "the reply's answer to question 'lesson', a choice, lacks a "
                    "choice, a confidence and probabilities"
                ),
                message,
            )

    def test_a_reply_that_misses_a_question_or_is_no_object_is_a_failed_request(
        self,
    ) -> None:
        self.assertIn(
            "the reply does not answer every question",
            self.failed({"lesson": self.CHOSEN}),
        )
        self.assertIn("the reply does not answer every question", self.failed(None))
        with self.assertRaises(RuntimeError):
            jev.read(["answers"], self.QUESTIONS)


if __name__ == "__main__":
    unittest.main()
