"""The rule picker's two rules, as calls of the functions that hold them: a glob's brace
groups as the globs they stand for (`braces`), and a glob of a rule file's `paths:` as a
pattern over a path relative to the root (`glob_regex`). Which rule files the picker
finds (in a subfolder, through a link, not twice through a loop of links), what it reads
from their frontmatter, a file that moved in a range of commits, and the refusals of
`lem project rules` are facts only the file system, git and the real command show:
tests/lem-settings.sh runs one journey for them.

    python3 -B -m unittest discover -s tests/unit
"""

import re
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import project  # noqa: E402 - after the line that puts src on sys.path


def matches(glob: str, path: str) -> bool:
    """Whether a glob of `paths:` covers the path, through `glob_patterns`, which
    `cmd_rules` asks too."""
    return any(pattern.fullmatch(path) for pattern in project.glob_patterns(glob))


class Braces(unittest.TestCase):
    """`*.{ts,tsx}` stands for `*.ts` and `*.tsx`."""

    def test_a_glob_with_no_brace_is_itself(self) -> None:
        self.assertEqual(project.braces("src/**/*.ts"), ["src/**/*.ts"])

    def test_a_group_lists_its_endings(self) -> None:
        self.assertEqual(
            project.braces("src/**/*.{ts,tsx}"), ["src/**/*.ts", "src/**/*.tsx"]
        )

    def test_two_groups_give_each_pair(self) -> None:
        self.assertEqual(
            project.braces("{a,b}/{c,d}.md"), ["a/c.md", "a/d.md", "b/c.md", "b/d.md"]
        )

    def test_a_brace_inside_a_brace(self) -> None:
        self.assertEqual(project.braces("{a,{b,c}}.x"), ["a.x", "b.x", "c.x"])
        self.assertEqual(
            project.braces("docs/{a,b{1,2}}/*.md"),
            ["docs/a/*.md", "docs/b1/*.md", "docs/b2/*.md"],
        )

    def test_an_empty_part_is_a_form_too(self) -> None:
        self.assertEqual(project.braces("app{,.min}.js"), ["app.js", "app.min.js"])

    def test_a_brace_with_no_comma_stays_as_written(self) -> None:
        self.assertEqual(project.braces("a{b}c"), ["a{b}c"])
        self.assertEqual(project.braces("a{b}{c,d}"), ["a{b}c", "a{b}d"])

    def test_a_brace_that_does_not_close_or_open_stays_as_written(self) -> None:
        self.assertEqual(project.braces("a{b"), ["a{b"])
        self.assertEqual(project.braces("c}"), ["c}"])


class GlobRegex(unittest.TestCase):
    """The forms Claude Code documents for `paths:`, and the two it does
    not document."""

    def assert_covers(
        self, glob: str, covered: list[str], not_covered: list[str]
    ) -> None:
        for path in covered:
            self.assertTrue(matches(glob, path), f"{glob} should cover {path}")
        for path in not_covered:
            self.assertFalse(matches(glob, path), f"{glob} should not cover {path}")

    def test_two_stars_as_a_whole_segment_cross_folders_none_too(self) -> None:
        self.assert_covers(
            "**/*.ts",
            ["x.ts", "src/x.ts", "src/api/v1/x.ts", "lib/a.ts", "tests/a.ts"],
            ["lib/a.tsx", "x.ts.bak", "README.md"],
        )
        self.assert_covers(
            "**/models.py",
            ["models.py", "app/models.py"],
            ["app/models.pyc", "app/my_models.py"],
        )
        self.assert_covers("**/*.sql", ["db/001.sql"], ["db/a#b.psql"])
        self.assert_covers("**/*.proto", ["api/v1.proto"], ["api/v1.protos"])

    def test_two_stars_in_the_middle_are_any_number_of_folders(self) -> None:
        self.assert_covers(
            "src/**/*",
            ["src/x.ts", "src/components/a.tsx", "src/components/a.css", "src/a/b/c"],
            ["lib/src/x.ts", "x.ts"],
        )
        self.assert_covers(
            "src/**/*.{ts,tsx}",
            [
                "src/x.ts",
                "src/api/v1/x.ts",
                "src/components/a.tsx",
                "src/components/deep/a.tsx",
            ],
            ["src/components/a.css", "lib/a.ts"],
        )
        self.assert_covers(
            "lib/**/*.ts", ["lib/a.ts", "lib/x/y/a.ts"], ["lib/a.tsx", "src/lib/a.ts"]
        )
        self.assert_covers(
            "tests/**/*.test.ts",
            ["tests/unit/a.test.ts", "tests/a.test.ts"],
            ["tests/a.ts", "tests/unit/a.ts"],
        )

    def test_two_stars_at_the_end_are_everything_under_the_folder(self) -> None:
        self.assert_covers(
            "**/models/**",
            ["app/models/user/x.py", "models/x.py"],
            ["app/models.py", "app/models"],
        )
        self.assert_covers("**", ["x", "a/b/c"], [])

    def test_two_stars_inside_a_name_stay_in_one_segment(self) -> None:
        self.assert_covers(
            "d**e/*.x", ["dxe/f.x", "de/f.x", "dabce/f.x"], ["d/x/e/f.x", "dxe/g/f.x"]
        )
        self.assert_covers("**.ts", ["x.ts"], ["a/x.ts"])
        self.assert_covers("a**", ["a", "abc"], ["a/b"])

    def test_two_stars_and_a_slash_at_the_end_cover_a_folder_and_no_file(self) -> None:
        self.assert_covers("src/**/", ["src/", "src/a/"], ["src/x.ts", "src/a/x.ts"])

    def test_a_star_stays_in_one_folder(self) -> None:
        self.assert_covers(
            "*.md", ["README.md", "notes.md"], ["docs/README.md", "README.mdx"]
        )
        self.assert_covers(
            "src/components/*.tsx",
            ["src/components/a.tsx"],
            ["src/components/deep/a.tsx", "src/components/a.css", "src/a.tsx"],
        )
        self.assert_covers("src/*.ts", ["src/a.ts"], ["src/a/b.ts"])

    def test_a_question_mark_is_one_character_of_one_segment(self) -> None:
        self.assert_covers(
            "src/?.ts", ["src/a.ts"], ["src/ab.ts", "src/.ts", "src//.ts"]
        )
        self.assert_covers("a?b", ["axb"], ["a/b", "ab"])

    def test_a_name_that_starts_with_a_dot_is_matched(self) -> None:
        self.assert_covers(
            ".revmux/**", [".revmux/lenses/a.md"], ["revmux/lenses/a.md"]
        )
        self.assert_covers("*.md", [".notes.md"], [])
        self.assert_covers("**/*.yml", [".github/workflows/ci.yml"], [])

    def test_a_path_with_no_pattern_is_that_file_only(self) -> None:
        self.assert_covers(
            "scripts/verify.sh",
            ["scripts/verify.sh"],
            ["scripts/other.sh", "scriptsXverify.sh", "a/scripts/verify.sh"],
        )
        self.assert_covers("**/*#*.psql", ["db/a#b.psql"], ["db/ab.psql"])

    def test_braces_list_folders_and_endings(self) -> None:
        self.assert_covers(
            "docs/{a,b}/*.md",
            ["docs/a/x.md", "docs/b/x.md"],
            ["docs/c/x.md", "docs/{a,b}/x.md"],
        )

    def test_an_odd_glob_that_reads_matches_as_written(self) -> None:
        self.assert_covers("a{b", ["a{b"], ["ab"])
        self.assert_covers("c}", ["c}"], ["c"])
        self.assert_covers("[", ["["], ["a"])
        self.assert_covers("src/[ab.ts", ["src/[ab.ts"], ["src/a.ts"])

    def test_a_class_in_brackets(self) -> None:
        self.assert_covers(
            "src/[ab].ts", ["src/a.ts", "src/b.ts"], ["src/c.ts", "src/ab.ts"]
        )
        self.assert_covers("v[0-9].md", ["v1.md"], ["vx.md"])
        self.assert_covers("x[]a]", ["x]", "xa"], ["xb"])
        self.assert_covers("a[\\]b", ["a\\b"], ["a]b"])

    def test_a_class_with_its_bang_is_every_other_character(self) -> None:
        self.assert_covers("src/[!ab].ts", ["src/c.ts"], ["src/a.ts", "src/b.ts"])
        self.assert_covers("v[!0-9].md", ["vx.md"], ["v1.md"])

    def test_a_class_that_does_not_read_raises_a_regex_error(self) -> None:
        # cmd_rules turns this error into its refusal with the fix;
        # tests/lem-settings.sh runs that refusal once
        for glob in ("src/[z-a].ts", "src/[!].ts"):
            with self.subTest(glob=glob), self.assertRaises(re.error):
                project.glob_regex(glob)


if __name__ == "__main__":
    unittest.main()
