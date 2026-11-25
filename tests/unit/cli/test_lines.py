"""Each command line a text of Lem gives is one the tree takes, or its text carries the mark
`<!-- lem: old form -->`, which this case reports as a skip with the count of its old lines.
`reading.py` says where a line is and how it is read; its rules are cases here too."""

import re
from typing import TYPE_CHECKING

import pytest

from lem.cli import nouns
from unit.cli import parsing, reading, shapes

if TYPE_CHECKING:
    from pathlib import Path

TREE = shapes.tree()
# The lines the reader cannot read, each with why.
ALLOWED: dict[str, str] = {}


def wrong(text: str, *, span: bool = False) -> list[str]:
    return reading.verdict(reading.Line("a text", 1, text, span=span), TREE)


def test_a_placeholder_is_one_word() -> None:
    assert wrong("lem land start SLUG") == []
    assert wrong('lem task move SLUG answered --line "WHY"') == []
    assert (
        "the line gives `lem land start` 2 positional words, and it takes 1"
        in wrong("lem land start SLUG OTHER")
    )


def test_a_placeholder_in_a_verbs_place_is_any_of_them() -> None:
    assert wrong("lem issue STEP SLUG") == []
    assert wrong("lem NAME ARGS...") == []
    assert wrong("lem issue STEP SLUG OTHER") == [
        "no subcommand of `lem issue` takes `STEP SLUG OTHER`"
    ]


def test_a_value_with_small_letters_is_one_of_its_choices() -> None:
    assert wrong("lem land merge SLUG --by owner|merger") == []
    assert wrong("lem criteria skip SLUG yes") == []
    assert wrong("lem land merge SLUG --by owner|someone") == [
        "--by takes owner or merger, not someone"
    ]
    assert wrong("lem criteria skip SLUG maybe") == [
        "`lem criteria skip` answer takes asked or yes or no, not maybe"
    ]


def test_words_in_brackets_may_be_left_out() -> None:
    assert wrong("lem session close SLUG [--session ID] --why ...") == []
    assert wrong('lem task move SLUG STATUS [--line "a line"]') == []
    assert (
        "the line gives `lem land start` 2 positional words, and it takes 1"
        in wrong("lem land start SLUG [OTHER]")
    )


def test_a_group_of_alternatives_is_only_marks() -> None:
    assert (
        wrong(
            "lem decisions criterion SLUG (--changed N --was TEXT --now TEXT | --added N "
            "--now TEXT | --removed N --was TEXT) --why TEXT (--decision ID | --by "
            "lead|personas [--said TEXT])"
        )
        == []
    )
    assert wrong("lem decisions criterion SLUG (--changed N | --grown N)") == [
        "`lem decisions criterion` takes no option --grown"
    ]


def test_words_left_out_lift_the_count() -> None:
    assert wrong("lem decisions criterion ... --decision ID") == []
    assert wrong("lem ask … --no-wait") == []
    assert wrong("lem task ... --words X") == [
        "cannot judge: `lem task` leaves out its subcommand"
    ]


def test_a_span_with_no_positional_names_the_command_in_prose() -> None:
    for text in ("lem land merged", "lem land read --record", "lem criteria red"):
        assert wrong(text, span=True) == [], text
    assert wrong("lem land merged") != []
    assert wrong("lem land merge --by nobody", span=True) == [
        "--by takes owner or merger, not nobody"
    ]
    assert wrong("lem task") == ["`lem task` needs a subcommand"]


def test_a_comment_a_redirection_and_a_heredoc_are_not_read() -> None:
    assert wrong("lem board --task SLUG # the board of one task") == []
    assert wrong("lem proposals add --kind retro --file - <<'JSON'") == []
    assert wrong("lem waiting 2>&1") == []


def test_an_option_belongs_to_the_level_it_stands_at() -> None:
    assert wrong("lem --repo WORKTREE land base SLUG") == []
    assert "`lem land` takes no option --repo" in wrong(
        "lem land --repo WORKTREE base SLUG"
    )
    assert wrong("lem task show SLUG --repo WORKTREE") == [
        "`lem task show` takes no option --repo"
    ]
    assert wrong("lem land checks SLUG --status=1") == [
        "--status of `lem land checks` takes no value"
    ]
    assert wrong("lem land merge SLUG --by") == [
        "--by of `lem land merge` takes a value, and the line gives none"
    ]


def test_a_noun_or_a_verb_that_is_not_there_is_wrong() -> None:
    assert wrong("lem tickets approve X") == ["`lem` has no subcommand tickets"]
    assert wrong("lem land go SLUG") == ["`lem land` has no subcommand go"]


def test_a_default_verb_takes_a_first_word_that_names_no_verb() -> None:
    assert wrong("lem ask /tmp/session-storage.json") == []
    assert wrong("lem ask - <<'JSON'") == []
    assert wrong("lem ask wait PAGEID") == []
    assert wrong("lem jev SPEC") == []
    assert wrong("lem ask a.json b.json") == [
        "the line gives `lem ask ask` 2 positional words, and it takes 0 to 1"
    ]


def test_two_dashes_end_the_options() -> None:
    assert wrong("lem serial -- pytest -x tests") == []
    assert wrong("lem serial") == [
        "the line gives `lem serial` 0 positional words, and it takes 1 or more"
    ]


def test_a_whole_shell_line_is_parsed_by_click_with_a_stand_in_for_each_placeholder() -> (
    None
):
    def said(text: str) -> str | None:
        line = reading.Line("a text", 1, text, span=False)
        return parsing.clicks_word(line) if parsing.complete(line) else "not complete"

    assert said("lem land merge SLUG --by owner") is None
    assert str(said("lem land merge demo")).startswith("Click: Missing option '--by'.")
    assert said("lem --repo WORKTREE criteria read SLUG start --by lead") is None
    assert said("lem task move SLUG STATUS --line WHY") is None
    assert said("lem serial -- pytest -x") is None
    assert said("lem ask SPEC") is None
    assert said("lem settings set KEY VALUE --local") is None
    assert said("lem land merge SLUG --by owner|merger") == "not complete"
    assert said("lem session close SLUG [--session ID] --why ended") == "not complete"
    assert (
        parsing.clicks_word(reading.Line("t", 1, "lem land merge demo", span=True))
        is not None
    )
    assert not parsing.complete(reading.Line("t", 1, "lem land merge demo", span=True))


def test_the_texts_are_read_in_every_folder_of_docs_but_plans_and_backlog() -> None:
    names = {str(path.relative_to(reading.ROOT)) for path in reading.texts()}
    assert "docs/rulings/history.md" in names
    assert "README.md" in names
    assert not [
        name for name in names if name.startswith(("docs/plans/", "docs/backlog/"))
    ]


def test_quotes_that_do_not_close_cannot_be_judged() -> None:
    assert wrong('lem task move SLUG held "no end') == [
        "cannot judge: No closing quotation"
    ]


def test_a_span_runs_over_a_line_break_and_not_over_an_empty_line() -> None:
    text = 'Run `lem task move SLUG\ndropped --line "WHY"` now.\n\n`lem land` and `x\n\nlem land base SLUG`'
    assert [(line.number, line.text) for line in reading.lines_of(text, "t.md")] == [
        (1, 'lem task move SLUG dropped --line "WHY"'),
        (4, "lem land"),
    ]


def test_a_shell_block_line_is_a_call_and_a_backslash_joins_the_next() -> None:
    text = (
        "```bash\nlem corrections record ID --decision lesson \\\n"
        "  --verdict proposed\nlem\n```\n"
    )
    assert reading.lines_of(text, "t.md") == [
        reading.Line(
            "t.md",
            2,
            "lem corrections record ID --decision lesson --verdict proposed",
            span=False,
        )
    ]


def test_a_span_of_two_backticks_quotes_spans() -> None:
    text = "Brief: ``Read `a.md` where `lem version` says``."
    assert reading.lines_of(text, "t.md") == [
        reading.Line("t.md", 1, "lem version", span=True)
    ]


def test_a_text_block_is_a_transcript_whose_spans_alone_are_calls() -> None:
    text = "```text\nlem  docs: the footer\nsee `lem land base SLUG`\n```\n"
    assert reading.lines_of(text, "t.md") == [
        reading.Line("t.md", 3, "lem land base SLUG", span=True)
    ]


def test_a_code_element_of_a_page_is_a_span_and_a_slash_command_is_none() -> None:
    text = "<p>Run <code>lem land &lt;slug&gt;</code></p>\n<code>/lem init</code>"
    assert reading.page_lines(text, "site/index.html") == [
        reading.Line("site/index.html", 1, "lem land <slug>", span=True)
    ]


def test_the_mark_is_the_first_line_or_the_first_after_the_front_matter() -> None:
    mark = reading.MARK
    assert reading.marked(f"{mark}\n# Title\n")
    assert reading.marked(f"---\nname: x\n---\n{mark}\n# Title\n")
    assert not reading.marked(f"---\nname: x\n---\n# Title\n{mark}\n")
    assert not reading.marked(f"# Title\n{mark}\n")


def texts_with_lines() -> list[str]:
    """Each text that gives a command line or carries the mark, by its path."""
    return [
        str(path.relative_to(reading.ROOT))
        for path in reading.texts()
        if reading.lines_in(path) or reading.marked(path.read_text(encoding="utf-8"))
    ]


@pytest.mark.parametrize("name", texts_with_lines())
def test_each_line_of_a_text_is_one_the_tree_takes_or_the_text_is_marked(
    name: str,
) -> None:
    path = reading.ROOT / name
    lines = reading.lines_in(path)
    judged = [
        (line, reading.verdict(line, TREE))
        for line in lines
        if line.text not in ALLOWED
    ]
    unread = [
        f"{name}:{line.number}: {line.text}\n      {'; '.join(said)}"
        for line, said in judged
        if any(problem.startswith(reading.CANNOT) for problem in said)
    ]
    assert unread == [], "the reader cannot read these; put each in ALLOWED with why"
    old = [
        f"{name}:{line.number}: {line.text}\n      {'; '.join(said)}"
        for line, said in judged
        if said
    ]
    old += [
        f"{name}:{line.number}: {line.text}\n      {said}"
        for line, judgement in judged
        if not judgement
        and parsing.complete(line)
        and (said := parsing.clicks_word(line)) is not None
    ]
    if reading.marked(path.read_text(encoding="utf-8")):
        assert old, f"{name} gives no old line now: take out its mark {reading.MARK}"
        pytest.skip(f"old form: {len(old)} of {len(lines)} lines")
    assert old == [], "\n" + "\n".join(old)


def test_every_line_of_allowed_is_still_given() -> None:
    given = {line.text for path in reading.texts() for line in reading.lines_in(path)}
    assert [text for text in ALLOWED if text not in given] == []


# A script of Lem's run by its path (`python3 SKILL_DIR/scripts/land.py`, `bash .../run.sh`,
# `python src/lem/land.py`), or by its file's name (`land.py merged SLUG`), also across a line break.
SCRIPT_NAMES = "|".join((*(noun for noun, _ in nouns.NOUNS), "project", "issues"))
PATH_FORM = re.compile(r"(?:python3?|bash)\s+\S*(?:scripts|src/lem)/[\w/-]+\.(?:py|sh)")
SHORT_FORM = re.compile(rf"`(?:{SCRIPT_NAMES})\.py\s+[-a-z\[]")
# The section of the harness that gives the command's fallback by its path.
FALLBACK = (reading.ROOT / "skills/lem/harness/claude-code.md", "## lem")


def script_lines(path: Path) -> list[str]:
    """The lines of PATH a script form is looked for in: no comment of a script, and not the
    harness's section on the fallback."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    inside = False
    for number, line in enumerate(lines):
        if path == FALLBACK[0] and line.startswith("## "):
            inside = line == FALLBACK[1]
        comment = path.suffix in {".py", ".html"} and line.lstrip().startswith(
            ("#", "//")
        )
        if inside or comment:
            lines[number] = ""
    return lines


def test_no_text_or_message_tells_anyone_to_run_a_script_of_lems_by_its_path() -> None:
    root = reading.ROOT
    found = []
    for path in sorted(
        [*root.glob("skills/**/*"), *root.glob("agents/**/*"), *root.glob("src/**/*")]
    ):
        if not path.is_file() or path.suffix not in {
            ".md",
            ".html",
            ".json",
            ".py",
            "",
        }:
            continue
        lines = script_lines(path)
        forms = [SHORT_FORM] if path.suffix == ".py" else [SHORT_FORM, PATH_FORM]
        for number, line in enumerate(lines):
            pair = line + "\n" + (lines[number + 1] if number + 1 < len(lines) else "")
            if any(
                m.start() < len(line) for form in forms for m in form.finditer(pair)
            ):
                found.append(
                    f"{path.relative_to(root)}:{number + 1}: {line.strip()[:100]}"
                )
    assert found == []


def test_the_script_forms_are_found_in_a_text() -> None:
    assert PATH_FORM.search("run `python3 SKILL_DIR/scripts/land.py merged SLUG`")
    assert PATH_FORM.search("python src/lem/cli/lazy.py")
    assert SHORT_FORM.search("then `land.py merged SLUG`")
    assert not SHORT_FORM.search("then `lem land merged SLUG`")


# The one rule `Bash(lem *)` covers a plain call: a `lem` call inside `$(...)`, before a pipe
# into another command or beside `&&` or `||` is a compound command it does not cover. A `|`
# between two options of a synopsis is no pipe.
CALL = r"\blem\s+[a-z-]"
COMPOUND = (
    re.compile(r"\$\(\s*lem\s"),
    re.compile(r"(?:\s\|\s|&&|\|\|)\s*" + CALL),
    re.compile(CALL + r"[^\n]*?\s(?:\|\s+[a-z]|&&|\|\|)"),
)


def compound_lines(text: str) -> list[int]:
    """The numbers of the lines of TEXT whose code block line or code span holds a compound
    `lem` call."""
    found = []
    fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        pieces = [line] if fence else re.findall(r"`([^`]+)`", line)
        if any(form.search(piece) for piece in pieces for form in COMPOUND):
            found.append(number)
    return found


def test_no_text_gives_a_lem_call_in_a_compound_command() -> None:
    root = reading.ROOT
    found = [
        f"{path.relative_to(root)}:{number}"
        for path in sorted([*root.glob("skills/**/*.md"), *root.glob("agents/**/*.md")])
        for number in compound_lines(path.read_text(encoding="utf-8"))
    ]
    assert found == []


def test_a_compound_lem_call_is_found_and_a_synopsis_is_not() -> None:
    assert compound_lines("`x=$(lem waiting)`") == [1]
    assert compound_lines("```\nlem waiting | jq .\n```") == [2]
    assert compound_lines("`cd W && lem land base SLUG`") == [1]
    assert compound_lines("`lem session wait SLUG (--until S | --event E)`") == []
    assert compound_lines("`lem land merge SLUG --by owner|merger`") == []
