"""The experts' rules for the part of a brief that says who the code is for, as calls of
experts.py's functions: each persona's first heading and its "Who they are", short, and
the profile's path, from what `lem cast` prints. The brief files the commands write, and
a project with no personas, are checked through the real command in
tests/test-ask-expert.sh.

    python3 -B -m unittest discover -s tests/unit
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import experts

MERCHANT = """# A merchant who sells shoes

<!-- a comment of the template -->
> A thin guess, written at the onboarding from little.

## Who they are

Sells shoes in two shops and online. Checks the orders each morning.

## What they want

Orders that are right.
"""

# a file of the built-in cast: no "Who they are", the person in its first paragraph
USER = """# A person who uses the product

You use this product to get something done. You came for a result.

**What you want.** The thing you came for.
"""


class WhoTheyAre(unittest.TestCase):
    def test_the_heading_and_the_who_they_are_part(self) -> None:
        self.assertEqual(
            experts.who_they_are(MERCHANT, "merchant"),
            (
                "A merchant who sells shoes",
                "Sells shoes in two shops and online. Checks the orders each morning.",
            ),
        )

    def test_a_file_with_no_such_part_gives_its_first_paragraph_and_no_quote(
        self,
    ) -> None:
        self.assertEqual(
            experts.who_they_are(USER, "user")[1],
            "You use this product to get something done. You came for a result.",
        )
        self.assertEqual(
            experts.who_they_are("> A guess.\n\nA cook at night.\n", "cook"),
            ("cook", "A cook at night."),
        )

    def test_a_long_part_is_cut_at_a_sentence_end_to_be_read_in_a_minute(self) -> None:
        long = (
            "# A clerk\n\n## Who they are\n\n"
            + " ".join(f"Sentence {n} has five words." for n in range(40))
            + "\n"
        )
        _, who = experts.who_they_are(long, "clerk")
        self.assertLessEqual(len(who.split()), experts.WHO_WORDS + 1)
        self.assertTrue(who.endswith("words. …"), who)
        self.assertTrue(who.startswith("Sentence 0 has five words."))


class Audience(unittest.TestCase):
    def test_the_part_names_the_profile_and_each_persona_by_its_path_and_says_how_to_weigh_them(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as top:
            merchant, user = Path(top) / "merchant.md", Path(top) / "user.md"
            # the file a persona's agent reads, without its frontmatter, is what the
            # part is taken from
            merchant.write_text(
                '---\nseats: ["claude/opus:high"]\n---\n' + MERCHANT, encoding="utf-8"
            )
            (Path(top) / "merchant.person.md").write_text(MERCHANT, encoding="utf-8")
            user.write_text(USER, encoding="utf-8")
            found = {
                "profile": {"path": "/repo/.lem/profile.md", "source": "checkout"},
                "personas": [
                    {
                        "stem": "merchant",
                        "path": str(merchant),
                        "person": str(Path(top) / "merchant.person.md"),
                    },
                    {"stem": "user", "path": str(user), "person": str(user)},
                ],
            }
            text = experts.audience_text(found)
        self.assertTrue(text.startswith("## Who the code is for\n"))
        self.assertIn(
            (
                "The project's profile, `/repo/.lem/profile.md`, says what the product "
                "is and who uses it: read it first."
            ),
            text,
        )
        self.assertIn(
            (
                f"- **A merchant who sells shoes** (`{merchant}`): "
                "Sells shoes in two shops and online."
            ),
            text,
        )
        self.assertIn(
            f"- **A person who uses the product** (`{user}`): You use this product",
            text,
        )
        self.assertIn(
            (
                "Weigh each option by what it does to these people. "
                "You still decide as an engineer"
            ),
            text,
        )
        self.assertIn("you answer as none of them", text)
        self.assertNotIn("seats", text)

    def test_a_project_with_no_profile_says_so(self) -> None:
        with tempfile.TemporaryDirectory() as top:
            user = Path(top) / "user.md"
            user.write_text(USER, encoding="utf-8")
            text = experts.audience_text(
                {
                    "profile": None,
                    "personas": [
                        {"stem": "user", "path": str(user), "person": str(user)}
                    ],
                }
            )
        self.assertIn("The project has no profile", text)

    def test_the_brief_holds_the_part_before_the_answer(self) -> None:
        part = "## Who the code is for\n\nPEOPLE\n"
        free = experts.free_brief_text(
            "Which store?", "", [], Path("/repo"), [], 2, part
        )
        self.assertLess(free.index(part), free.index("## Your answer"))


if __name__ == "__main__":
    unittest.main()
