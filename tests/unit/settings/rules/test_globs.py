"""The picker's two rules over a glob, as calls of the functions that hold them: a glob's brace
groups as the globs they stand for (`braces`), and a glob of a rule file's `paths:` as patterns
over a path relative to the root (`glob_patterns`, `glob_regex`)."""

import re

import pytest

from lem.cli.rules.braces import braces
from lem.cli.rules.globs import glob_patterns, glob_regex


def matches(glob: str, path: str) -> bool:
    """Whether a glob of `paths:` covers the path, as the picker asks."""
    return any(pattern.fullmatch(path) for pattern in glob_patterns(glob))


def assert_covers(glob: str, covered: list[str], not_covered: list[str]) -> None:
    for path in covered:
        assert matches(glob, path), f"{glob} should cover {path}"
    for path in not_covered:
        assert not matches(glob, path), f"{glob} should not cover {path}"


def test_a_glob_with_no_brace_is_itself() -> None:
    assert braces("src/**/*.ts") == ("src/**/*.ts",)


def test_a_group_lists_its_endings() -> None:
    assert braces("src/**/*.{ts,tsx}") == ("src/**/*.ts", "src/**/*.tsx")


def test_two_groups_give_each_pair() -> None:
    assert braces("{a,b}/{c,d}.md") == ("a/c.md", "a/d.md", "b/c.md", "b/d.md")


def test_a_brace_inside_a_brace() -> None:
    assert braces("{a,{b,c}}.x") == ("a.x", "b.x", "c.x")
    assert braces("docs/{a,b{1,2}}/*.md") == (
        "docs/a/*.md",
        "docs/b1/*.md",
        "docs/b2/*.md",
    )


def test_an_empty_part_is_a_form_too() -> None:
    assert braces("app{,.min}.js") == ("app.js", "app.min.js")


def test_a_brace_with_no_comma_stays_as_written() -> None:
    assert braces("a{b}c") == ("a{b}c",)
    assert braces("a{b}{c,d}") == ("a{b}c", "a{b}d")


def test_a_brace_that_does_not_close_or_open_stays_as_written() -> None:
    assert braces("a{b") == ("a{b",)
    assert braces("c}") == ("c}",)
    assert braces("a{b{c,d}") == ("a{b{c,d}",)


def test_two_stars_as_a_whole_segment_cross_folders_none_too() -> None:
    assert_covers(
        "**/*.ts",
        ["x.ts", "src/x.ts", "src/api/v1/x.ts", "lib/a.ts", "tests/a.ts"],
        ["lib/a.tsx", "x.ts.bak", "README.md"],
    )
    assert_covers(
        "**/models.py",
        ["models.py", "app/models.py"],
        ["app/models.pyc", "app/my_models.py"],
    )
    assert_covers("**/*.sql", ["db/001.sql"], ["db/a#b.psql"])
    assert_covers("**/*.proto", ["api/v1.proto"], ["api/v1.protos"])


def test_two_stars_in_the_middle_are_any_number_of_folders() -> None:
    assert_covers(
        "src/**/*",
        ["src/x.ts", "src/components/a.tsx", "src/components/a.css", "src/a/b/c"],
        ["lib/src/x.ts", "x.ts"],
    )
    assert_covers(
        "src/**/*.{ts,tsx}",
        [
            "src/x.ts",
            "src/api/v1/x.ts",
            "src/components/a.tsx",
            "src/components/deep/a.tsx",
        ],
        ["src/components/a.css", "lib/a.ts"],
    )
    assert_covers(
        "lib/**/*.ts", ["lib/a.ts", "lib/x/y/a.ts"], ["lib/a.tsx", "src/lib/a.ts"]
    )
    assert_covers(
        "tests/**/*.test.ts",
        ["tests/unit/a.test.ts", "tests/a.test.ts"],
        ["tests/a.ts", "tests/unit/a.ts"],
    )


def test_two_stars_at_the_end_are_everything_under_the_folder() -> None:
    assert_covers(
        "**/models/**",
        ["app/models/user/x.py", "models/x.py"],
        ["app/models.py", "app/models"],
    )
    assert_covers("**", ["x", "a/b/c"], [])


def test_two_stars_inside_a_name_stay_in_one_segment() -> None:
    assert_covers(
        "d**e/*.x", ["dxe/f.x", "de/f.x", "dabce/f.x"], ["d/x/e/f.x", "dxe/g/f.x"]
    )
    assert_covers("**.ts", ["x.ts"], ["a/x.ts"])
    assert_covers("a**", ["a", "abc"], ["a/b"])


def test_two_stars_and_a_slash_at_the_end_cover_a_folder_and_no_file() -> None:
    assert_covers("src/**/", ["src/", "src/a/"], ["src/x.ts", "src/a/x.ts"])


def test_a_star_stays_in_one_folder() -> None:
    assert_covers("*.md", ["README.md", "notes.md"], ["docs/README.md", "README.mdx"])
    assert_covers(
        "src/components/*.tsx",
        ["src/components/a.tsx"],
        ["src/components/deep/a.tsx", "src/components/a.css", "src/a.tsx"],
    )
    assert_covers("src/*.ts", ["src/a.ts"], ["src/a/b.ts"])


def test_a_question_mark_is_one_character_of_one_segment() -> None:
    assert_covers("src/?.ts", ["src/a.ts"], ["src/ab.ts", "src/.ts", "src//.ts"])
    assert_covers("a?b", ["axb"], ["a/b", "ab"])


def test_a_name_that_starts_with_a_dot_is_matched() -> None:
    assert_covers(".revmux/**", [".revmux/lenses/a.md"], ["revmux/lenses/a.md"])
    assert_covers("*.md", [".notes.md"], [])
    assert_covers("**/*.yml", [".github/workflows/ci.yml"], [])


def test_a_path_with_no_pattern_is_that_file_only() -> None:
    assert_covers(
        "scripts/verify.sh",
        ["scripts/verify.sh"],
        ["scripts/other.sh", "scriptsXverify.sh", "a/scripts/verify.sh"],
    )
    assert_covers("**/*#*.psql", ["db/a#b.psql"], ["db/ab.psql"])


def test_a_leading_dot_slash_is_taken_off() -> None:
    assert_covers("./src/*.ts", ["src/a.ts"], ["./src/a.ts"])


def test_braces_list_folders_and_endings() -> None:
    assert_covers(
        "docs/{a,b}/*.md",
        ["docs/a/x.md", "docs/b/x.md"],
        ["docs/c/x.md", "docs/{a,b}/x.md"],
    )


def test_an_odd_glob_that_reads_matches_as_written() -> None:
    assert_covers("a{b", ["a{b"], ["ab"])
    assert_covers("c}", ["c}"], ["c"])
    assert_covers("[", ["["], ["a"])
    assert_covers("src/[ab.ts", ["src/[ab.ts"], ["src/a.ts"])


def test_a_class_in_brackets() -> None:
    assert_covers("src/[ab].ts", ["src/a.ts", "src/b.ts"], ["src/c.ts", "src/ab.ts"])
    assert_covers("v[0-9].md", ["v1.md"], ["vx.md"])
    assert_covers("x[]a]", ["x]", "xa"], ["xb"])
    assert_covers("a[\\]b", ["a\\b"], ["a]b"])


def test_a_class_with_its_bang_is_every_other_character() -> None:
    assert_covers("src/[!ab].ts", ["src/c.ts"], ["src/a.ts", "src/b.ts"])
    assert_covers("v[!0-9].md", ["vx.md"], ["v1.md"])


@pytest.mark.parametrize("glob", ["src/[z-a].ts", "src/[!].ts"])
def test_a_class_that_does_not_read_raises_a_regex_error(glob: str) -> None:
    # the picker turns this error into its refusal with the fix (test_picker.py)
    with pytest.raises(re.error):
        glob_regex(glob)
