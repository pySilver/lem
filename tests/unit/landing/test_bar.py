"""Where a change lowers the bar, from the diff git gave (`model/landing/bar.py`), and the checks'
refusal of a bar lowered with no reason, on each track."""

import re
from typing import TYPE_CHECKING, cast

import pytest

from lem.kernel.errors import Refusal
from lem.model.landing.bar import (
    BarRead,
    Edited,
    Mark,
    bar_of,
    refusal,
    shebang_suffix,
)
from lem.model.landing.bar_marks import BAR_MARKS, marks_of

if TYPE_CHECKING:
    from collections.abc import Iterator

# The bar's marks of a Python file, each written in two pieces: the bar reads a .py
# file's marks, and this file adds none of the ones it feeds it.
NOQA = "#" + " noqa"
SKIP = "pytest.mark" + ".skip"
FLAKY = "pytest.mark" + ".flaky"
PYREFLY = "#" + " pyrefly: ignore"
TY = "#" + " ty: ignore"
RUFF = "#" + " ruff: noqa"
TYPE_IGNORE = "#" + " type: ignore"
H = "#"


def patch(
    path: str,
    minus: tuple[str, ...] = (),
    plus: tuple[str, ...] = (),
    *,
    was: str | None = None,
    new: bool = False,
    gone: bool = False,
) -> str:
    """One file's part of `git diff -U0 -M`: its header, then one hunk of the lines that
    went and came. `was` is the name before a move, `new` a file the base lacks, `gone`
    one the tip lacks."""
    before = was or path
    lines = [
        f"diff --git a/{before} b/{path}",
        "--- /dev/null" if new else f"--- a/{before}",
        "+++ /dev/null" if gone else f"+++ b/{path}",
    ]
    lines.append(f"@@ -1,{len(minus)} +1,{len(plus)} @@")
    return "\n".join(
        [*lines, *(f"-{line}" for line in minus), *(f"+{line}" for line in plus)]
    )


def bar(
    *patches: str,
    rows: tuple[str, ...] = (),
    plan: str = "",
    files: tuple[str, ...] = (),
) -> BarRead:
    """bar_of over the parts of a diff, the name-status rows, the plan and the changed
    files, none of them a file with no suffix."""
    return bar_of(
        "\n".join(patches),
        rows,
        plan,
        dict.fromkeys(files, ""),
        where="docs/plans/plan.md",
    )


def lowered(result: BarRead) -> list[tuple[str, str]]:
    """Each lowered bar of a result as its file and what lowers it, in order."""
    return sorted((mark.path, mark.what) for mark in result.lowered)


def test_a_removed_line_that_starts_with_two_dashes_is_no_header() -> None:
    # `-- ` removed is `--- ` in the diff: a SQL comment of a test, a line of a
    # Python string that only moved with the mark on it
    assert lowered(
        bar(
            patch(
                "tests/orders.sql",
                ("-- assert: every order has a customer", "SELECT 1;"),
                ("SELECT 1;",),
            )
        )
    ) == [("tests/orders.sql", "1 assertion(s) fewer")]
    moved = f"-- the total  {NOQA}: E501"
    assert lowered(bar(patch("calc.py", (moved, "x = 1"), ("x = 1", moved)))) == []


def test_an_added_line_that_starts_with_two_pluses_is_no_header() -> None:
    # `++ ` added is `+++ ` in the diff: a line of a string, a C++ comment; the
    # file after it keeps its name and the line keeps its mark
    added = f"++ the total  {NOQA}: E501"
    assert lowered(
        bar(patch("calc.py", plus=(added,)), patch("plug.py", plus=("x",)))
    ) == [("calc.py", NOQA)]
    assert lowered(bar(patch("calc.py", (added, "x = 1"), ("x = 1", added)))) == []
    # an assertion that only moved into a string's line keeps its count
    moved = patch(
        "tests/test_calc.py", ("assert total == 3",), ("++ assert total == 3",)
    )
    assert lowered(bar(moved)) == []


def test_a_new_suppression_lowers_the_bar() -> None:
    result = bar(patch("calc.py", plus=(f"import os  {NOQA}: F401",), new=True))
    assert result.lowered == (
        Mark(
            path="calc.py",
            what=NOQA,
            line=f"import os  {NOQA}: F401",
            reason=None,
        ),
    )


def test_a_suppression_that_only_got_a_space_is_none() -> None:
    result = bar(
        patch(
            "plug.py",
            minus=(f"import plugin {NOQA}: F401",),
            plus=(f"import plugin  {NOQA}: F401",),
        )
    )
    assert result.lowered == ()


def test_a_suppression_that_got_wider_is_a_new_one() -> None:
    result = bar(
        patch(
            "plug.py",
            minus=(f"import other  {NOQA}: E402",),
            plus=(f"import other  {NOQA}",),
        )
    )
    assert [mark.line for mark in result.lowered] == [f"import other  {NOQA}"]


def test_a_mark_put_beside_an_old_one_is_the_one_new_mark() -> None:
    # the old mark's own text runs to the next mark of its line: a mark put after
    # it, or before it, leaves that text as it was
    after = bar(
        patch(
            "plug.py",
            minus=(f"import plugin  {NOQA}: F401",),
            plus=(f"import plugin  {NOQA}: F401  {TYPE_IGNORE}",),
        )
    )
    assert lowered(after) == [("plug.py", TYPE_IGNORE)]
    before = bar(
        patch(
            "plug.py",
            minus=(f"x = plugin.load()  {NOQA}: E501",),
            plus=(f"x = plugin.load()  {TYPE_IGNORE}  {NOQA}: E501",),
        )
    )
    assert lowered(before) == [("plug.py", TYPE_IGNORE)]
    # a rule list that grew is a wider suppression, beside a new mark too
    grew = bar(
        patch(
            "plug.py",
            minus=(f"import plugin  {NOQA}: F401",),
            plus=(f"import plugin  {NOQA}: F401, E501",),
        ),
        patch(
            "load.py",
            minus=(f"import load  {NOQA}: F401",),
            plus=(f"import load  {NOQA}: F401, E501  {TYPE_IGNORE}",),
        ),
    )
    assert lowered(grew) == [
        ("load.py", NOQA),
        ("load.py", TYPE_IGNORE),
        ("plug.py", NOQA),
    ]
    # a mark that moved with its code to another line is none
    moved = bar(
        patch(
            "plug.py",
            minus=(f"import plugin  {NOQA}: F401", "import os"),
            plus=("import os", f"import plugin  {NOQA}: F401"),
        )
    )
    assert moved.lowered == ()


def test_an_old_mark_cancels_a_new_one_only_on_its_own_line() -> None:
    # the import is used now and loses its suppression, its type comment moves to
    # another line, and a new import elsewhere takes the same suppression
    gone = f"import os  {NOQA}: F401  {TYPE_IGNORE}"
    elsewhere = "\n".join(
        [
            "diff --git a/calc.py b/calc.py",
            "--- a/calc.py",
            "+++ b/calc.py",
            "@@ -1 +1 @@",
            f"-{gone}",
            "+import os",
            "@@ -10,0 +11 @@",
            f"+x = os.getcwd()  {TYPE_IGNORE}",
            "@@ -20,0 +22 @@",
            f"+import sys  {NOQA}: F401",
        ]
    )
    assert lowered(bar(elsewhere)) == [("calc.py", NOQA), ("calc.py", TYPE_IGNORE)]
    # in one hunk, the new import first: the line that keeps its code is the one
    # the old marks stood on
    here = bar(
        patch(
            "calc.py",
            minus=(gone,),
            plus=(f"import sys  {NOQA}: F401", f"import os  {TYPE_IGNORE}"),
        )
    )
    assert [(mark.what, mark.line) for mark in here.lowered] == [
        (NOQA, f"import sys  {NOQA}: F401")
    ]


def test_a_line_with_many_marks_is_walked_once() -> None:
    # one added line of a bundle with 8,000 focused calls: each counts, each with
    # its own text, and the walk over them is one pass, counted in its steps
    count = 8000
    line = "it.only(1);" * count
    marks = [
        re.compile(mark)
        for suffixes, found in BAR_MARKS.items()
        if ".js" in suffixes
        for mark in found
    ]
    found = marks_of(line, marks, [])
    assert len(found) == count
    assert {own for _, own in found} == {"it.only(1);"}
    steps = 0
    start = re.Match.start

    class Counted:
        """A match whose `start` counts its calls."""

        def __init__(self, found: re.Match[str]) -> None:
            self.found = found
            self.re = found.re

        def start(self) -> int:
            nonlocal steps
            steps += 1
            return start(self.found)

    class Pattern:
        """A mark whose matches count."""

        def __init__(self, mark: re.Pattern[str]) -> None:
            self.mark = mark

        def finditer(self, text: str) -> Iterator[Counted]:
            return (Counted(found) for found in self.mark.finditer(text))

    marks_of(line, cast("list[re.Pattern[str]]", [Pattern(m) for m in marks]), [])
    # a walk over all hits for each hit takes count * count steps
    assert steps < 10 * count


def test_a_second_mark_of_one_kind_on_a_line_counts() -> None:
    # a runner's settings put several marks of one kind on one line
    two = 'addopts = "--deselect tests/a.py --deselect tests/b.py'
    three = f'{two} --deselect tests/c.py"'
    result = bar(patch("pyproject.toml", minus=(f'{two}"',), plus=(three,)))
    assert [mark.line for mark in result.lowered] == [three]


def test_a_skip_of_a_whole_module() -> None:
    result = bar(
        patch(
            "tests/test_base.py",
            plus=("import pytest", f'pytestmark = {SKIP}(reason="later")'),
        )
    )
    assert lowered(result) == [("tests/test_base.py", SKIP)]


def test_fewer_assertions_in_a_test_file() -> None:
    fewer = bar(
        patch(
            "tests/test_base.py",
            minus=("    assert 1 + 1 == 2", "    assert 2 + 2 == 4"),
            plus=("    assert 1 + 1 == 2",),
        )
    )
    more = bar(patch("tests/test_base.py", plus=("    assert 3 + 3 == 6",)))
    assert lowered(fewer) == [("tests/test_base.py", "1 assertion(s) fewer")]
    assert more.lowered == ()


def test_an_assertion_out_of_a_rust_module() -> None:
    result = bar(
        patch(
            "lib.rs",
            minus=(
                "#[cfg(test)]",
                "mod tests {",
                "    #[test]",
                "    fn it_is_one() { assert_eq!(super::one(), 1); }",
                "}",
            ),
        )
    )
    assert lowered(result) == [("lib.rs", "1 assertion(s) fewer")]


def test_a_deleted_test_file_is_one_entry() -> None:
    result = bar(
        patch(
            "tests/test_base.py",
            minus=("def test_base():", "    assert 1 + 1 == 2"),
            gone=True,
        ),
        rows=("D\ttests/test_base.py",),
    )
    assert lowered(result) == [("tests/test_base.py", "a test file is deleted")]


def test_a_test_file_moved_out_of_the_tests() -> None:
    out = bar(rows=("R100\ttests/test_old.py\tattic/old.py",))
    within = bar(rows=("R100\ttests/test_old.py\ttests/unit/test_old.py",))
    assert lowered(out) == [
        (
            "tests/test_old.py",
            "a test file is moved out of the tests, to attic/old.py",
        )
    ]
    assert within.lowered == ()


def test_a_focus_mark_is_named_without_its_parenthesis() -> None:
    result = bar(
        patch(
            "tests/focus.test.js",
            plus=(
                'it.only("runs alone", () => {});',
                'fit("runs alone too", () => {});',
                'fdescribe("a group alone", () => {});',
                'test.only("one test", () => {});',
                'describe.only("one group", () => {});',
                "profit(1);",
            ),
            new=True,
        )
    )
    assert [what for _, what in lowered(result)] == [
        "describe.only",
        "fdescribe",
        "fit",
        "it.only",
        "test.only",
    ]


def test_a_method_of_a_focus_or_skip_marks_name_is_no_mark() -> None:
    # the two `fit` methods of the chart controller in the built board-app.js
    # (sidebar-fold-arrow, 2026-11-22), and mermaid.min.js's `a.fit(`, `e.fit(` and
    # `b.cy.fit(`: a line of a bundle that changed after them
    line = "new R(()=>this.fit()),this.onDrawn=()=>{a.fit(),b.cy.fit()};v="
    bundle = bar(
        patch(
            "skills/lem/assets/vendor/board-app.js",
            minus=(f"{line}1",),
            plus=(f"{line}2",),
        )
    )
    assert bundle.lowered == ()
    calls = bar(
        patch(
            "chart.js",
            plus=(
                "this.fit(); e.fdescribe(1); q.xit(2); r.xtest(3); s.xdescribe(4);",
                "t?.fit(5);",
                "u",
                "  .fit(6);",
            ),
            new=True,
        )
    )
    assert calls.lowered == ()
    # after a dot, `.only` stays a mark: Playwright's test.describe.only; and a
    # real mark after a method call of the same name on its line still counts
    marks = bar(
        patch(
            "tests/shop.spec.js",
            plus=(
                'test.describe.only("the shop", () => {});',
                'this.fit(); fit("runs alone", () => {});',
                'xit("later", () => {});',
            ),
            new=True,
        )
    )
    assert lowered(marks) == [
        ("tests/shop.spec.js", "describe.only"),
        ("tests/shop.spec.js", "fit"),
        ("tests/shop.spec.js", "xit"),
    ]


def test_a_file_with_no_suffix_is_read_as_its_first_line_names() -> None:
    lines = {
        "#!/usr/bin/env python3\n": ".py",
        "#!/usr/bin/env -S python3 -I\n": ".py",
        "#!/usr/bin/python3.11\n": ".py",
        "#!/bin/sh -e\n": ".sh",
        "#!/usr/bin/env bash\n": ".sh",
        "#!/usr/bin/env node\n": "",
        "#!/usr/bin/env -S uv run --script\n": "",
        "#!/usr/bin/env\n": "",
        "import os\n": "",
        "": "",
    }
    assert {line: shebang_suffix(line) for line in lines} == lines
    script = patch("bin/lem", minus=("import os",), plus=(f"import os  {NOQA}: F401",))
    tool = patch("tools/run", plus=("# shellcheck" + " disable=SC2086",), new=True)
    kinds = {"bin/lem": ".py", "tools/run": ".sh"}
    assert lowered(bar_of(f"{script}\n{tool}", [], "", kinds, where="")) == [
        ("bin/lem", NOQA),
        ("tools/run", "# shellcheck" + " disable"),
    ]
    # with no kind, a file with no suffix takes no marks, and is no kind of file
    # the bar misses
    plain = bar(script, tool, files=tuple(kinds))
    assert (plain.lowered, plain.not_covered) == ((), ())


def test_marks_in_a_runners_settings() -> None:
    result = bar(
        patch(
            "pyproject.toml",
            plus=(
                "[tool.pytest.ini_options]",
                (
                    'addopts = "--deselect tests/test_calc.py::test_add -k '
                    "'not slow' --reruns 3\""
                ),
            ),
        ),
        patch(
            "package.json",
            minus=('{"name": "shop"}',),
            plus=('{"name": "shop", "jest": {"testPathIgnorePatterns": ["slow"]}}',),
        ),
    )
    assert lowered(result) == [
        ("package.json", "testPathIgnorePatterns"),
        ("pyproject.toml", "--deselect"),
        ("pyproject.toml", "--reruns"),
        ("pyproject.toml", "-k 'not"),
    ]


def test_a_coverage_threshold_that_went_down() -> None:
    result = bar(
        patch("pyproject.toml", minus=("fail_under = 90",), plus=("fail_under = 10",)),
        patch(
            "package.json",
            minus=('{"jest": {"coverageThreshold": {"global": {"lines": 80}}}}',),
            plus=('{"jest": {"coverageThreshold": {"global": {"lines": 50}}}}',),
        ),
        patch(
            ".github/workflows/ci.yml",
            minus=("      - run: pytest --cov-fail-under=80",),
            plus=("      - run: pytest",),
        ),
        patch("setup.cfg", minus=("fail_under = 70",), plus=("fail_under = 75",)),
    )
    assert lowered(result) == [
        (".github/workflows/ci.yml", "cov-fail-under (80) is gone"),
        ("package.json", "lines went from 80 to 50"),
        ("pyproject.toml", "fail_under went from 90 to 10"),
    ]


def test_a_flaky_decorator() -> None:
    result = bar(
        patch("tests/test_calc.py", plus=("import pytest", f"@{FLAKY}(reruns=5)"))
    )
    assert lowered(result) == [("tests/test_calc.py", FLAKY)]


def test_a_pyrefly_a_ty_and_a_file_wide_ruff_suppression() -> None:
    result = bar(
        patch(
            "m.py",
            plus=(
                f"x = f()  {PYREFLY}[bad-assignment]",
                f"y = g()  {PYREFLY}",
                f"z = h()  {TY}[invalid-assignment]",
                f"w = k()  {TY}",
                f"{RUFF}: E501",
                RUFF,
            ),
            new=True,
        ),
    )
    assert lowered(result) == [
        ("m.py", PYREFLY),
        ("m.py", PYREFLY),
        ("m.py", RUFF),
        ("m.py", RUFF),
        ("m.py", TY),
        ("m.py", TY),
    ]


def test_a_new_mark_in_a_string_counts_as_a_noqa_in_one() -> None:
    result = bar(
        patch(
            "say.py",
            plus=(f'OLD = "{NOQA}"', f'NEW = "{PYREFLY}, {TY}, {RUFF}"'),
            new=True,
        ),
    )
    assert lowered(result) == [
        ("say.py", NOQA),
        ("say.py", PYREFLY),
        ("say.py", RUFF),
        ("say.py", TY),
    ]


# Each line with the mark it is named by, or None where the tool's own rule of case
# takes no mark: ruff's `noqa` in any case after the name `ruff` or `flake8` in lower
# case, and pyrefly's comments in lower case only. Pyrefly honors the other checkers'
# comments with `permissive-ignores`, or with no settings file.
FORMS = {
    f"x = 1  {H} NOQA": f"{H} NOQA",
    f"x = 1  {H} NoQA: E501": f"{H} NoQA",
    f"{H} flake8: noqa": f"{H} flake8: noqa",
    f"{H} flake8: noqa: E501": f"{H} flake8: noqa",
    f"{H} ruff : noqa": f"{H} ruff : noqa",
    f"{H} ruff: NOQA": f"{H} ruff: NOQA",
    f"{H} RUFF: noqa": None,
    f"{H} ruff: disable[E501]": f"{H} ruff: disable",
    f"{H} ruff: file-ignore[F401, ARG001]": f"{H} ruff: file-ignore",
    f"{H} pyrefly: ignore-errors": f"{H} pyrefly: ignore-errors",
    f"{H} pyrefly: ignore-errors[bad-assignment]": f"{H} pyrefly: ignore-errors",
    f"x: int = ''  {H} PYREFLY: IGNORE": None,
    f"x: int = ''  {H} pyre-ignore": f"{H} pyre-ignore",
    f"x: int = ''  {H} pyre-ignore[9]": f"{H} pyre-ignore",
    f"{H} pyre-ignore-all-errors": f"{H} pyre-ignore-all-errors",
    f"x: int = ''  {H} pyre-fixme[9]": f"{H} pyre-fixme",
    f"x: int = ''  {H} pyre: ignore": f"{H} pyre: ignore",
    f"{H} mypy: ignore-errors": f"{H} mypy: ignore-errors",
    f"x: int = ''  {H} zuban: ignore": f"{H} zuban: ignore",
    f"x: int = ''  {H} mypy: ignore": f"{H} mypy: ignore",
    f"{H} flake8 : noqa": f"{H} flake8 : noqa",
    f"import os  {H} ruff: ignore[F401]": f"{H} ruff: ignore",
    f"{H} ruff: ignore[F401]  {H} the plugin registers": f"{H} ruff: ignore",
    f"import os  {H}ruff:ignore[F401]": f"{H}ruff:ignore",
    f"import os  {H} ruff : ignore [F401]": f"{H} ruff : ignore",
    f"import os  {H} RUFF: ignore[F401]": None,
    f"import os  {H} ruff: ignore F401": None,
    f"{H} ruff: disable [F401]": f"{H} ruff: disable",
    f"{H} ruff : disable[F401]": f"{H} ruff : disable",
    f"{H} ruff: file-ignore [F401]": f"{H} ruff: file-ignore",
    f"{H} ruff : file-ignore[F401]": f"{H} ruff : file-ignore",
    f"{H} isort: skip_file": f"{H} isort: skip_file",
    f"{H} isort:skip_file": f"{H} isort:skip_file",
    f"{H} isort: off": f"{H} isort: off",
    f"import sys  {H} isort: skip": f"{H} isort: skip",
    f"import sys  {H} isort:skip": f"{H} isort:skip",
    f"{H} ruff: isort: skip_file": f"{H} ruff: isort: skip_file",
    f"{H} ruff: isort: off": f"{H} ruff: isort: off",
    f"{H} ISORT: skip_file": None,
    f"{H} isort: split": None,
    f"x=1  {H} fmt: skip": f"{H} fmt: skip",
    f"x=1  {H}fmt:skip": f"{H}fmt:skip",
    f"{H} fmt: off": f"{H} fmt: off",
    f"{H} yapf: disable": f"{H} yapf: disable",
    f"{H} FMT: off": None,
    f"{H} fmt : off": None,
}


@pytest.mark.parametrize(("line", "mark"), list(FORMS.items()))
def test_each_form_ruff_and_pyrefly_obey(line: str, mark: str | None) -> None:
    assert lowered(bar(patch("m.py", plus=(line,), new=True))) == (
        [("m.py", mark)] if mark else []
    )


# ruff 0.17.6 hides I001 for `isort: skip` or `isort:skip` anywhere in a comment, and
# pyrefly 1.5.0 and ruff obey no other mark with a `-` or a word character after it,
# but `pyre-ignore-all-errors` (each form run on a copy, 2026-11-24)
OBEYED = {
    f"import sys  {H} keep first isort:skip": f"{H} keep first isort:skip",
    f"import sys  {H} pragma isort:skip": f"{H} pragma isort:skip",
    f"import sys  {H} isort:skip_this": f"{H} isort:skip_this",
    f"import sys  {H} isort: skipped": f"{H} isort: skipped",
    f"import sys  {H} text ruff: isort: skip": f"{H} text ruff: isort: skip",
    f"import sys  {H} isort:  skip": None,
    f"{H} fmt: off-topic": None,
    f"x=1  {H} fmt: skip-this": None,
    f"{H} yapf: disable-x": None,
    f"{H} isort: off-topic": None,
    f"{H} mypy: ignore-missing-imports": None,
    f"{H} mypy: ignore-errors": f"{H} mypy: ignore-errors",
    f"x: int = ''  {H} type: ignored": None,
    f"x: int = ''  {H} type: ignore[assignment]": f"{H} type: ignore",
    f"x: int = ''  {H} pyrefly: ignore-x": None,
    f"x: int = ''  {H} pyright: ignored": None,
    f"x: int = ''  {H} ty: ignore-x": None,
    f"x: int = ''  {H} pyre-fixme-x": None,
    f"x: int = ''  {H} pyre-ignored": None,
    f"{H} pyre-ignore-all-errors-x": f"{H} pyre-ignore-all-errors",
    f"x: int = ''  {H} zuban: ignored": None,
    f"import os  {H} noqa-x": None,
    f"import os  {H} noqax": None,
    f"{H} ruff: noqa-x": None,
}


@pytest.mark.parametrize(("line", "mark"), list(OBEYED.items()))
def test_a_mark_is_named_as_far_as_its_tool_obeys_it(
    line: str, mark: str | None
) -> None:
    assert lowered(bar(patch("m.py", plus=(line,), new=True))) == (
        [("m.py", mark)] if mark else []
    )


def test_a_document_may_quote_a_mark() -> None:
    result = bar(
        patch(
            "docs/backlog/a-note.md",
            plus=(
                f"A {NOQA} in a note is no mark.",
                f"{SKIP} neither.",
                f"Nor {PYREFLY}, {TY} or {RUFF}.",
            ),
            new=True,
        ),
        files=("docs/backlog/a-note.md",),
    )
    assert (result.lowered, result.not_covered) == ((), ())


def test_the_tests_snapshots_and_settings_the_change_edits() -> None:
    rows = (
        "M\t.github/workflows/ci.yml",
        "M\tpackage.json",
        "M\tpyproject.toml",
        "M\ttests/__snapshots__/total.snap",
        "M\ttests/test_calc.py",
        "A\ttests/test_new.py",
        "R100\ttests/test_a.py\ttests/test_b.py",
        "R090\ttests/test_c.py\ttests/test_d.py",
        "M\tshop.py",
    )
    assert bar(rows=rows).edited == (
        Edited(path=".github/workflows/ci.yml", kind="test configuration"),
        Edited(path="package.json", kind="test configuration"),
        Edited(path="pyproject.toml", kind="test configuration"),
        Edited(path="tests/__snapshots__/total.snap", kind="snapshot"),
        Edited(path="tests/test_calc.py", kind="test"),
        Edited(path="tests/test_d.py", kind="test"),
    )


def test_the_kinds_of_file_the_bar_has_no_marks_for() -> None:
    result = bar(
        files=(
            "x.rb",
            "calc.py",
            "docs/guide.md",
            "data.json",
            "Makefile",
            "lib/y.RB",
        )
    )
    assert result.not_covered == (".rb",)
    assert not hasattr(result, "own_patterns")


def test_the_plan_gives_each_file_its_reason() -> None:
    plan = (
        "# bar-change\n"
        "\n"
        "## Tasks\n"
        "\n"
        "- calc.py: a line of another section is no reason.\n"
        "\n"
        "## The bar\n"
        "\n"
        "- calc.py: the import registers a plugin.\n"
        "- `tests/test_base.py`: the sum moved to another module with its test.\n"
        "\n"
        "## Notes\n"
        "\n"
        "- plug.py: after the section, no reason either."
    )
    result = bar(
        patch("calc.py", plus=(f"import os  {NOQA}: F401",)),
        patch("plug.py", plus=(f"import other  {NOQA}",)),
        patch("tests/test_base.py", plus=(f"pytestmark = {SKIP}",)),
        plan=plan,
    )
    assert sorted((mark.path, mark.reason) for mark in result.lowered) == [
        ("calc.py", "the import registers a plugin."),
        ("plug.py", None),
        (
            "tests/test_base.py",
            "the sum moved to another module with its test.",
        ),
    ]


# A plan's sample in a code block whose lines look like a heading or a numbered line.
SAMPLE = "```markdown\n## Notes\n\n1. a line of the sample\n```\n"


def test_a_heading_inside_a_fence_of_the_bar_ends_no_section() -> None:
    plan = (
        "# bar-change\n\n## The bar\n\n- `tests/test_base.py`: the sample:\n\n"
        f"{SAMPLE}\n- calc.py: the import registers a plugin.\n"
    )
    result = bar(
        patch("calc.py", plus=(f"import os  {NOQA}: F401",)),
        plan=plan,
    )
    assert [mark.reason for mark in result.lowered] == [
        "the import registers a plugin."
    ]


# The two shapes of a block that never closes, each with its line in the block: a
# fence with no close, and a sample in three backticks that holds a block of its own
# in three backticks, whose inner close ends the sample and whose outer close opens a
# block.
SHAPES = (
    ("```markdown\n## Notes\n\n1. a line of the sample\n", 0),
    ("```markdown\n## Notes\n\n```python\nprint(1)\n```\n```\n", 6),
)


def opens(text: str, offset: int) -> str:
    """The words of the refusal for the block of TEXT that opens OFFSET lines after its
    sample's first line."""
    first = text.splitlines().index("```markdown")
    return f"line {first + offset + 1} opens a code block that never closes"


@pytest.mark.parametrize(("sample", "offset"), SHAPES)
def test_a_plan_s_bar(sample: str, offset: int) -> None:
    plan = (
        "# bar-change\n\n## The bar\n\n- `tests/test_base.py`: the sample:\n\n"
        f"{sample}\n- calc.py: the import registers a plugin.\n"
    )
    with pytest.raises(Refusal) as raised:
        bar_of(
            patch("calc.py", plus=(f"import os  {NOQA}: F401",)),
            [],
            plan,
            {},
            where="docs/plans/bar-change.md",
        )
    assert "docs/plans/bar-change.md" in str(raised.value)
    assert opens(plan, offset) in str(raised.value)
    assert raised.value.code == "fence"
    assert "close the fence" in raised.value.fix


def test_the_fast_track_has_no_plan_and_names_the_standard_track() -> None:
    found = bar(patch("tests/test_old.py", plus=(f"@{SKIP}",), new=True), plan="")
    said = refusal(found.lowered, small=True)
    assert [mark.reason for mark in found.lowered] == [None]
    assert said is not None
    assert said.code == "bar"
    assert f"tests/test_old.py ({SKIP})" in said.why
    assert "standard track" in said.fix


def test_the_standard_track_names_the_plans_section() -> None:
    found = bar(patch("calc.py", plus=(f"import os  {NOQA}",)))
    said = refusal(found.lowered, small=False)
    assert said is not None
    assert f"calc.py ({NOQA})" in said.why
    assert "`## The bar`" in said.fix
    assert "standard track" not in f"{said.why}. {said.fix}"


def test_a_reason_for_each_file_is_no_refusal() -> None:
    found = bar(
        patch("calc.py", plus=(f"import os  {NOQA}",)),
        plan="## The bar\n\n- calc.py: the import registers a plugin.\n",
    )
    assert refusal(found.lowered, small=False) is None
    assert refusal([], small=True) is None
