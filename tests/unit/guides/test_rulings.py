"""AGENTS.md and the owner's rulings as one list (`test_agents_md.py` on `main`).

docs/rulings/rulings.md is the list: one bullet for each ruling of the owner in force, under the
heading of its group, and in its last part the choices of the maintaining session that are open to
him. A bullet is its rule in one sentence in bold, at most three lines that say more, and its day.
docs/rulings/history.md holds what left the list, each line with what keeps it now: a test, which
must exist, so that a renamed or removed test fails here and the rule does not drift; or one place,
which must exist. The plan of the move has one row for each file the list took the place of, and no
tracked file still names one of those files.
"""

import ast
import re
import subprocess
from pathlib import Path

import pytest

from unit.cli import reading

ROOT = Path(__file__).resolve().parents[3]
AGENTS = ROOT / "AGENTS.md"
LIST = ROOT / "docs/rulings/rulings.md"
HISTORY = ROOT / "docs/rulings/history.md"
FREE_HOUR = ROOT / "docs/free-hour.md"
PLAN = ROOT / "docs/plans/2026-11-21-rulings-as-one-list.md"
# AGENTS.md was 6,142 words by wc -w with a sentence and a link for each ruling, and 3,638 with
# the list in its own file (2026-11-21): the bound is that size with some room, the session's
# choice, not a measured need.
WORDS = 4200
GROUPS = [
    "What Lem is, and who it is for",
    "What Lem needs on the machine",
    "A request: its type, its track and its commands",
    "The interview, the criteria and the personas",
    "The plan, the build and the tests",
    "A decision without him: the ladder, the experts and the breaker",
    "The review, the pull request and the merge",
    "A task's session, and whether he is there",
    "The board and the pages for him",
    "The settings, the seats and the tracker",
    "The README, the guides and the logo",
    "The lessons, the correction queue, the naps, the night and the free hour",
]
LAST = "Choices of the maintaining session"
HELD, KEPT = "Held by a test or by the code", "Kept in one place"
# The files the list and the history took the place of, counted with `ls | wc -l` before the
# move (2026-11-21): 130 rulings and 41 decisions.
FOLDERS = {"docs/rulings": 130, ".lem/decisions": 41}
DATE = r"\d{4}-\d{2}-\d{2}"
DAY = re.compile(rf"\((?P<decided>decided\s+)?{DATE}(?:(?:,\s+|\s+and\s+){DATE})*\)$")
CODE = re.compile(r"`([^`]+)`")
PATH = re.compile(r"[^/\s:@*][^\s:@*]*/[^\s:@*]+")
PLACEHOLDER = re.compile(r"<[^>]*>|\b[A-Z]{2,}\b")
QUOTED = re.compile(r'"[^"]*"')
# A test of any level, by its file and its function: tests/unit/guides/test_site.py::test_x.
TEST = re.compile(r"tests/(?P<file>[\w/]+\.py)::(?:(?P<cls>\w+)\.)?(?P<name>test_\w+)")
SOURCE = re.compile(r"(?P<file>(?:src|skills)/\S+\.py): (?P<name>\w+)")
# The paths the list names in another repository, each with where it is.
ELSEWHERE = {
    ".claude/rules": "the folder of rules in a project that adopts Lem",
    # the ruling on Python names what held "until that release"; the file went with the
    # release that brings Lem's own Python (2026-11-25), and his words stay as he ruled
    "src/lem/python.py": "the file of a Lem before the app",
}
# The paths git ignores (`.lem/.gitignore`), which a clone never holds: one machine's settings.
IGNORED = (".lem/settings.local.toml",)
# The files that may name a file the list took the place of: the record of the task that made
# those files, and the plan of the move, whose table names each.
MAY_NAME = (
    "docs/plans/2026-11-21-agents-md-read-on-demand/map.json",
    "docs/plans/2026-11-21-rulings-as-one-list.md",
)


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parts(path: Path) -> list[tuple[str | None, list[str]]]:
    """Each bullet of a file as its lines, with the `##` heading it stands under."""
    found: list[tuple[str | None, list[str]]] = []
    heading = None
    for line in path.read_text(encoding="utf-8").split("\n"):
        if line.startswith("## "):
            heading = line[3:]
        elif line.startswith("- "):
            found.append((heading, [line]))
        elif line.startswith("  ") and found and line.strip():
            found[-1][1].append(line)
    return found


def headings(path: Path) -> list[str]:
    return [
        line[3:]
        for line in path.read_text(encoding="utf-8").split("\n")
        if line.startswith("## ")
    ]


def first_line_under(path: Path, heading: str) -> str:
    after = path.read_text(encoding="utf-8").split(f"\n## {heading}\n", 1)
    return after[1].lstrip("\n").split("\n", 1)[0] if len(after) == 2 else ""


def description_lines(lines: list[str]) -> int:
    """The lines of a bullet that hold words after its sentence in bold, its day left out (a
    day may wrap onto a line of its own)."""
    text = "\n".join(line.strip() for line in lines)[2:]
    text = DAY.sub("", text.rstrip())
    bold = re.match(r"\*\*[^*]+\*\*", text)
    after = text[bold.end() :] if bold else text
    return sum(1 for line in after.split("\n") if line.strip(" .,;:"))


def plan_rows() -> list[tuple[str, str]]:
    """The (folder, stem) of each row of the plan's table."""
    rows = []
    for line in PLAN.read_text(encoding="utf-8").split("\n"):
        cells = (
            [cell.strip() for cell in line.strip().strip("|").split("|")]
            if line.startswith("|")
            else []
        )
        if len(cells) >= 2 and cells[0].strip("`") in FOLDERS:
            rows.append((cells[0].strip("`"), cells[1].strip("`")))
    return rows


def tracked() -> list[str]:
    ran = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert ran.returncode == 0, f"git ls-files failed in {ROOT}: {ran.stderr.strip()}"
    return ran.stdout.split()


def defined(path: Path, name: str, cls: str | None = None) -> bool:
    """Whether a Python file defines the function NAME (in the class CLS when one is given), or
    a module-level NAME."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    scopes: list[ast.AST] = (
        [
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == cls
        ]
        if cls
        else [tree]
    )
    for scope in scopes:
        nodes = ast.walk(scope) if cls is None else iter(getattr(scope, "body", []))
        for node in nodes:
            if (
                isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
                and node.name == name
            ):
                return True
            if cls is None and isinstance(node, ast.Assign | ast.AnnAssign):
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
                if any(isinstance(one, ast.Name) and one.id == name for one in targets):
                    return True
    return False


def bullets() -> list[tuple[str | None, list[str]]]:
    assert LIST.is_file(), f"{LIST.relative_to(ROOT)} does not exist"
    found = parts(LIST)
    assert found, f"{LIST.relative_to(ROOT)} holds no bullet"
    return found


def test_each_bullet_has_its_sentence_in_bold_its_day_and_three_lines_at_most_after_it() -> (
    None
):
    for heading, lines in bullets():
        text = flat(" ".join(lines))
        assert re.match(r"^- \*\*[^*]+\*\*", text), f"no rule in bold: {text[:80]}"
        day = DAY.search(text)
        assert day is not None, f"no day in parentheses at the end: {text[:80]}"
        assert bool(day["decided"]) == (heading == LAST), (
            f'a bullet of "{LAST}" says decided before its day, and only there: {text[:80]}'
        )
        # The owner's exact words at cd257cb0 need four lines at this width.
        limit = 4 if text.startswith("- **The board's button says Approve,") else 3
        assert description_lines(lines) <= limit, (
            f"more than {limit} lines: {text[:80]}"
        )
        for line in lines:
            assert len(line) <= 100, (
                f"a line of the list over 100 characters: {line[:60]}"
            )


def test_each_heading_is_a_group_in_its_order_and_the_last_part_closes_the_list() -> (
    None
):
    found = headings(LIST)
    assert found[-1:] == [LAST]
    groups = found[:-1]
    assert set(groups) <= set(GROUPS), sorted(set(groups) - set(GROUPS))
    assert groups == [group for group in GROUPS if group in groups]
    under = {heading for heading, _ in bullets()}
    assert [heading for heading in found if heading not in under] == []
    assert re.match(r"^None of these is his ruling\b", first_line_under(LIST, LAST))


def test_each_path_the_list_names_exists() -> None:
    # A path is a name in backticks with a slash between two names, no space, no `:`, `@` or
    # `*`, no placeholder and no leading `/` (a command), outside his quoted words. It resolves
    # from the root or from the skill's folder skills/lem/.
    text = QUOTED.sub('""', flat(LIST.read_text(encoding="utf-8")))
    missing = [
        name
        for name in CODE.findall(text)
        if PATH.fullmatch(name)
        and not PLACEHOLDER.search(name)
        and not name.startswith((".lem/state/", "~"))
        and name not in ELSEWHERE
        and name not in IGNORED
        and not (ROOT / name).exists()
        and not (ROOT / "skills" / "lem" / name).exists()
    ]
    assert missing == []


def history_lines(heading: str) -> list[str]:
    assert HISTORY.is_file(), f"{HISTORY.relative_to(ROOT)} does not exist"
    found = [
        flat(" ".join(lines)) for under, lines in parts(HISTORY) if under == heading
    ]
    assert found, f'the history has no line under "{heading}"'
    return found


def test_the_history_has_its_two_parts_and_names_where_the_full_text_is() -> None:
    assert headings(HISTORY) == [HELD, KEPT]
    opening = HISTORY.read_text(encoding="utf-8").split("\n## ", 1)[0]
    assert re.search(r"`[0-9a-f]{7,40}`", opening), "the opening names no commit"


def test_each_rule_a_test_holds_names_a_guard_that_exists() -> None:
    # His "it will not drift": a test renamed or removed fails here, and its rule goes back to
    # the list. Until each step names its new tests in the history, the file carries the
    # old-form mark, and this case waits for it.
    if reading.marked(HISTORY.read_text(encoding="utf-8")):
        pytest.skip(
            "docs/rulings/history.md carries the old-form mark: its guards are main's"
        )
    for line in history_lines(HELD):
        assert DAY.search(line), f"no day: {line[:80]}"
        guards = [
            span
            for span in CODE.findall(line)
            if TEST.fullmatch(span) or SOURCE.fullmatch(span)
        ]
        assert guards, f"no guard named: {line[:80]}"
        for guard in guards:
            if found := TEST.fullmatch(guard):
                path = ROOT / "tests" / found["file"]
                assert path.is_file() and defined(path, found["name"], found["cls"]), (
                    guard
                )
            elif found := SOURCE.fullmatch(guard):
                path = ROOT / found["file"]
                assert path.is_file() and defined(path, found["name"]), guard


def test_each_rule_kept_in_one_place_names_a_path_that_exists() -> None:
    for line in history_lines(KEPT):
        assert DAY.search(line), f"no day: {line[:80]}"
        paths = [
            span
            for span in CODE.findall(line)
            if PATH.fullmatch(span) or span in {"AGENTS.md", "README.md"}
        ]
        assert paths, f"no place named: {line[:80]}"
        missing = [path for path in paths if not (ROOT / path).exists()]
        if missing and reading.marked(HISTORY.read_text(encoding="utf-8")):
            pytest.skip(f"docs/rulings/history.md carries the old-form mark: {missing}")
        assert missing == [], line[:80]


def test_the_plan_has_a_row_for_each_file_the_list_took_the_place_of() -> None:
    rows = plan_rows()
    assert len(rows) == len(set(rows)), "a file has two rows"
    for folder, count in FOLDERS.items():
        stems = [stem for where, stem in rows if where == folder]
        assert len(stems) == count, (folder, len(stems))
        assert all(re.fullmatch(r"[a-z0-9-]+", stem) for stem in stems)


def test_the_rulings_folder_holds_the_list_and_the_history_only() -> None:
    assert sorted(path.name for path in (ROOT / "docs/rulings").iterdir()) == [
        "history.md",
        "rulings.md",
    ]
    assert not (ROOT / ".lem/decisions").exists()


def test_no_file_names_a_file_the_list_took_the_place_of() -> None:
    rulings = {stem for folder, stem in plan_rows() if folder == "docs/rulings"}
    decisions = {stem for folder, stem in plan_rows() if folder == ".lem/decisions"}
    assert rulings and decisions, "the plan's table names no file"
    named = re.compile(
        r"(?P<folder>rulings|decisions)/(?P<stem>[a-z0-9-]+)\.md|\.lem/decisions/[\w-]"
    )
    found = []
    for path in tracked():
        if path in MAY_NAME or not (ROOT / path).is_file():
            continue
        try:
            text = (ROOT / path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in named.finditer(text):
            gone = (
                match["stem"]
                in (rulings if match["folder"] == "rulings" else decisions)
                if match["stem"]
                else True
            )
            if gone:
                found.append(f"{path}: {match[0]}")
    assert found == [], (
        "cite the rule's sentence in quotes with the list or the history"
    )


def test_agents_md_is_short() -> None:
    words = len(AGENTS.read_text(encoding="utf-8").split())
    assert words <= WORDS, f"AGENTS.md has {words} words by wc -w; the bound is {WORDS}"


def test_agents_md_names_the_list_and_the_history_and_no_ruling_by_link() -> None:
    text = AGENTS.read_text(encoding="utf-8")
    for name in ("docs/rulings/rulings.md", "docs/rulings/history.md"):
        assert f"`{name}`" in text
    assert not re.search(r"\]\(docs/rulings/|\]\(\.lem/decisions/", text)


def test_agents_md_says_where_the_docs_live() -> None:
    text = flat(AGENTS.read_text(encoding="utf-8"))
    assert "The pages of `docs/` are the one source of the site" in text
    assert "`zensical.toml`, `overrides/` and `docs/assets/`: the site." in text
    assert "site/index.html" not in text


def test_the_names_docs_free_hour_cites_are_headings_of_agents_md_or_bullets_of_the_list() -> (
    None
):
    # docs/free-hour.md sends an unattended session to these by name.
    text = AGENTS.read_text(encoding="utf-8")
    page = flat(FREE_HOUR.read_text(encoding="utf-8"))
    found = {
        line.lstrip("#").strip() for line in text.split("\n") if line.startswith("#")
    }
    for _, lines in parts(LIST):
        bold = re.match(r"- \*\*([^*]+)\*\*", flat(" ".join(lines)))
        if bold:
            found.add(bold[1].rstrip("."))
    for name in (
        "Opinionated",
        "The owner's rulings",
        "Rules for a change here",
        "A project that uses Lem gets Lem's improvements only through the agreed paths",
    ):
        assert f'"{name}"' in page, f'docs/free-hour.md no longer cites "{name}"'
        assert name in found, (
            f'"{name}" is no heading of AGENTS.md and no bullet of the list'
        )


def maintainer_bullet() -> str:
    found = [
        flat(" ".join(lines))
        for _, lines in parts(AGENTS)
        if lines[0].startswith("- **A maintainer's session with nobody at the terminal")
    ]
    assert len(found) == 1, (
        "AGENTS.md has one bullet on a session with nobody at the terminal"
    )
    return found[0]


def test_the_free_hour_page_makes_no_worktree_and_no_free_hour_branch() -> None:
    page = FREE_HOUR.read_text(encoding="utf-8")
    assert "git worktree add" not in page
    assert not re.search(r'-b\s+"?free-hour/', page)
    assert "make no branch and no worktree" in flat(page)


def test_the_night_here_writes_proposals_and_the_scheduled_retro_takes_no_free_hour() -> (
    None
):
    bullet = maintainer_bullet()
    assert "makes no branch and no worktree" in bullet
    assert (
        "writes what it finds as proposals into the night's file of the day" in bullet
    )
    assert (
        "The scheduled `/lem retro` of this repository takes no free hour: it is a retro only."
        in bullet
    )
    assert "on a branch" not in bullet
