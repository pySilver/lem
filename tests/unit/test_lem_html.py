"""lem_html.py's one rule: text reaches a served page only escaped, in an element's text
and in an attribute's value, and only `Markup` passes as it is.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts")
)
lem_html = importlib.import_module("lem_html")
h, Markup = lem_html.h, lem_html.Markup

# a task's title as an attacker would write it
TITLE = '</a><script>alert("x")</script> & "quoted" \'single\''


class Escape(unittest.TestCase):
    def test_a_title_in_the_text_and_in_an_attribute_is_escaped(self) -> None:
        got = h("a", {"href": "/t", "title": TITLE}, TITLE)
        self.assertNotIn("<script>", got)
        self.assertNotIn('"quoted"', got)
        self.assertEqual(got.count("&lt;script&gt;"), 2)
        self.assertIn("&#x27;single&#x27;", got)

    def test_markup_nests_once_and_a_plain_string_never_passes_as_html(self) -> None:
        inner = h("b", None, "<i>")
        self.assertEqual(h("p", None, inner, "<i>"), "<p><b>&lt;i&gt;</b>&lt;i&gt;</p>")
        # a str added to Markup is escaped, so a slice or a join cannot let one through
        self.assertEqual(Markup("<br>") + "<i>", "<br>&lt;i&gt;")
        self.assertEqual("<i>" + Markup("<br>"), "&lt;i&gt;<br>")
        self.assertEqual(
            lem_html.join(["<i>", Markup("<br>")], " · "), "&lt;i&gt; · <br>"
        )

    def test_empty_children_and_false_attributes_are_left_out_and_true_is_bare(
        self,
    ) -> None:
        self.assertEqual(
            h(
                "div",
                {"hidden": True, "title": None, "open": False},
                None,
                False,
                "",
                [None, "a", ("b",)],
                0,
            ),
            "<div hidden>ab0</div>",
        )
        self.assertEqual(h("input", {"value": '"'}), '<input value="&quot;">')

    def test_a_name_that_would_break_the_tag_is_refused(self) -> None:
        for tag, attrs in (
            ("a onclick", None),
            ("a", {'x" onload="y': 1}),
            ("a", {"x y": 1}),
        ):
            with self.subTest(tag=tag, attrs=attrs), self.assertRaises(ValueError):
                h(tag, attrs)
        with self.assertRaises(ValueError):
            h("br", None, "text")

    def test_a_page_is_a_doctype_and_one_html_element(self) -> None:
        got = lem_html.page([h("title", None, TITLE)], h("body"))
        self.assertTrue(
            got.startswith('<!doctype html>\n<html lang="en"><head><title>&lt;/a&gt;')
        )
        self.assertTrue(got.endswith("<body></body></html>"))


if __name__ == "__main__":
    unittest.main()
