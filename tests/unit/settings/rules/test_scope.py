"""What the picker reads from a rule file's frontmatter (`rule_scope`), and how it reads the
names of a range from the `Git` port's short form of a moved file (`unfolded`)."""

from typing import TYPE_CHECKING

import pytest

from lem.cli.rules.renames import unfolded
from lem.cli.rules.scope import rule_scope
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path


def scope_of(tmp_path: Path, text: str | bytes) -> tuple[str, ...] | None:
    """The scope of a rule file that holds `text`."""
    path = tmp_path / "rule.md"
    if isinstance(text, bytes):
        path.write_bytes(text)
    else:
        path.write_text(text, encoding="utf-8")
    return rule_scope(path, "rule.md")


@pytest.mark.parametrize(
    "text",
    [
        "# Conduct\nNever dig up a deleted document.\n",
        "---\ndescription: no scope in this one\n---\nSay what you did not verify.\n",
        "---\npaths:\n  - '*.md'\n",
        "",
    ],
    ids=["no-frontmatter", "no-paths", "no-closing-fence", "empty"],
)
def test_a_file_with_no_scope_covers_every_path(tmp_path: Path, text: str) -> None:
    assert scope_of(tmp_path, text) is None


@pytest.mark.parametrize(
    ("text", "globs"),
    [
        ('---\npaths:\n  - "**/*.ts"\n---\n', ("**/*.ts",)),
        ("---\npaths:\n  - 'src/components/*.tsx'\n---\n", ("src/components/*.tsx",)),
        (
            (
                '---\npaths:\n  # the three lines\n  - "src/**/*.{ts,tsx}"\n'
                '  - "lib/**/*.ts"\n\n  - tests/**/*.test.ts\ndescription: after\n---\n'
            ),
            ("src/**/*.{ts,tsx}", "lib/**/*.ts", "tests/**/*.test.ts"),
        ),
        (
            '---\npaths: ["**/models.py", "**/models/**", \'docs/{a,b}/*.md\']\n---\n',
            ("**/models.py", "**/models/**", "docs/{a,b}/*.md"),
        ),
        ("---\npaths: scripts/verify.sh\n---\n", ("scripts/verify.sh",)),
        (
            (
                '---\npaths: # the scope\n  - "**/*.sql" # every query\n'
                "  - '**/*#*.psql'\n---\n"
            ),
            ("**/*.sql", "**/*#*.psql"),
        ),
        ('---\npaths: ["a # b", "c"]  # a comment\n---\n', ("a # b", "c")),
        ("﻿---\npaths: ['**/*.proto']\n---\n".encode(), ("**/*.proto",)),
    ],
    ids=[
        "block",
        "single-quotes",
        "comments-and-a-key-after",
        "flow",
        "scalar",
        "comments-after-items",
        "hash-in-quotes",
        "byte-order-mark",
    ],
)
def test_the_scope_is_the_globs_of_paths_in_each_form(
    tmp_path: Path, text: str | bytes, globs: tuple[str, ...]
) -> None:
    assert scope_of(tmp_path, text) == globs


@pytest.mark.parametrize(
    ("text", "said"),
    [
        ("---\npaths:\n---\n", "rule.md: its `paths:` names no glob"),
        ("---\npaths: []\n---\n", "rule.md: its `paths:` names no glob"),
        ('---\npaths: ["a", ""]\n---\n', "rule.md: its `paths:` names no glob"),
        (
            '---\npaths:\n  glob: "src/**"\n---\n',
            "rule.md: a line under `paths:` is not a list item ('glob: \"src/**\"')",
        ),
    ],
    ids=["empty", "empty-flow", "empty-glob", "no-list"],
)
def test_a_paths_that_names_no_glob_or_is_no_list_is_refused_with_the_fix(
    tmp_path: Path, text: str, said: str
) -> None:
    with pytest.raises(Refusal) as refused:
        scope_of(tmp_path, text)
    assert refused.value.code == "rule-scope"
    assert refused.value.why == said
    assert '`  - "GLOB"`' in refused.value.fix


@pytest.mark.parametrize(
    ("shown", "names"),
    [
        ("src/x.ts", ("src/x.ts",)),
        ("{src => lib}/x.ts", ("src/x.ts", "lib/x.ts")),
        ("src/{a => b}/x.ts", ("src/a/x.ts", "src/b/x.ts")),
        ("src/{ => sub}/x.ts", ("src/x.ts", "src/sub/x.ts")),
        ("x.ts => sub/x.ts", ("x.ts", "sub/x.ts")),
        ('"docs/na\\303\\257ve.md"', ("docs/naïve.md",)),
        ('"a\\tb.md" => c.md', ("a\tb.md", "c.md")),
        ('c.md => "d\\"e.md"', ("c.md", 'd"e.md')),
    ],
    ids=[
        "one",
        "folder",
        "inner",
        "empty-side",
        "no-common",
        "quoted",
        "quoted-old",
        "quoted-new",
    ],
)
def test_a_moved_file_counts_under_both_names_and_a_quoted_name_as_itself(
    shown: str, names: tuple[str, ...]
) -> None:
    assert unfolded(shown) == names
