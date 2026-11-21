"""The short AGENTS.md and the owner's rulings as one list.

docs/rulings/rulings.md is the list: one bullet for each ruling of the owner in force, under the
heading of its group, and in its last part the choices of the maintaining session that are open to
him. A bullet is its rule in one sentence in bold, at most three lines that say more, and its day.
docs/rulings/history.md holds what left the list, each line with what keeps it now: a test, which
must exist, so that a renamed or removed test fails here and the rule does not drift; or one place,
which must exist. The plan of the move has one row for each file the list took the place of, and no
tracked file still names one of those files.

It reads only the repository's own files and `git ls-files`, so a missing file is a failed case.

    python3 -B -m unittest discover -s tests/unit -p test_agents_md.py
"""

import ast
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
AGENTS = ROOT / "AGENTS.md"
LIST = ROOT / "docs/rulings/rulings.md"
HISTORY = ROOT / "docs/rulings/history.md"
PLAN = ROOT / "docs/plans/2026-11-21-rulings-as-one-list.md"
# AGENTS.md was 6,142 words by wc -w with a sentence and a link for each ruling, and 3,638 with the
# list in its own file (2026-11-21): the bound is that size with some room, the session's choice,
# not a measured need.
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
# The files the list and the history took the place of, counted with `ls | wc -l` before the move
# (2026-11-21): 130 rulings and 41 decisions.
FOLDERS = {"docs/rulings": 130, ".lem/decisions": 41}
DATE = r"\d{4}-\d{2}-\d{2}"
DAY = re.compile(rf"\((?P<decided>decided\s+)?{DATE}(?:(?:,\s+|\s+and\s+){DATE})*\)$")
CODE = re.compile(r"`([^`]+)`")
PATH = re.compile(r"[^/\s:@*][^\s:@*]*/[^\s:@*]+")
PLACEHOLDER = re.compile(r"<[^>]*>|\b[A-Z]{2,}\b")
QUOTED = re.compile(r'"[^"]*"')
UNIT = re.compile(r"tests/unit/(?P<file>\w+\.py)::(?:(?P<cls>\w+)\.)?(?P<name>test_\w+)")
BLOCK = re.compile(r'tests/(?P<file>[\w-]+\.sh): "(?P<text>[^"]+)"')
SCRIPT = re.compile(r"(?P<file>skills/\S+\.py): (?P<name>\w+)")
# The paths the list names in another repository, each with where it is.
ELSEWHERE = {".claude/rules": "the folder of rules in a project that adopts Lem"}
# The files that may name a file the list took the place of: the record of the task that made those
# files, and the plan of the move, whose table names each.
MAY_NAME = ("docs/plans/2026-11-21-agents-md-read-on-demand/map.json", "docs/plans/2026-11-21-rulings-as-one-list.md")


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parts(path: Path) -> list[tuple[str | None, list[str]]]:
    """Each bullet of a file as its lines, with the `##` heading it stands under."""
    out, heading = [], None
    for line in path.read_text(encoding="utf-8").split("\n"):
        if line.startswith("## "):
            heading = line[3:]
        elif line.startswith("- "):
            out.append((heading, [line]))
        elif line.startswith("  ") and out and line.strip():
            out[-1][1].append(line)
    return out


def headings(path: Path) -> list[str]:
    return [line[3:] for line in path.read_text(encoding="utf-8").split("\n") if line.startswith("## ")]


def first_line_under(path: Path, heading: str) -> str:
    after = path.read_text(encoding="utf-8").split(f"\n## {heading}\n", 1)
    return after[1].lstrip("\n").split("\n", 1)[0] if len(after) == 2 else ""


def description_lines(lines: list[str]) -> int:
    """The lines of a bullet that hold words after its sentence in bold, its day left out (a day
    may wrap onto a line of its own)."""
    text = "\n".join(line.strip() for line in lines)[2:]
    text = DAY.sub("", text.rstrip())
    bold = re.match(r"\*\*[^*]+\*\*", text)
    after = text[bold.end():] if bold else text
    return sum(1 for line in after.split("\n") if line.strip(" .,;:"))


def plan_rows() -> list[tuple[str, str]]:
    """The (folder, stem) of each row of the plan's table."""
    rows = []
    for line in PLAN.read_text(encoding="utf-8").split("\n"):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")] if line.startswith("|") else []
        if len(cells) >= 2 and cells[0].strip("`") in FOLDERS:
            rows.append((cells[0].strip("`"), cells[1].strip("`")))
    return rows


def tracked() -> list[str]:
    ran = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True, check=False)
    if ran.returncode != 0:
        raise AssertionError(f"git ls-files failed in {ROOT}: {ran.stderr.strip()}; run the test in a clone of Lem")
    return ran.stdout.split()


def defined(path: Path, name: str, cls: str | None = None) -> bool:
    """Whether a Python file defines the function NAME (in the class CLS when one is given), or a
    module-level NAME."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    scopes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == cls] if cls else [tree]
    for scope in scopes:
        for node in ast.walk(scope) if cls is None else scope.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                return True
            if cls is None and isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                    return True
    return False


def has_check(path: Path, text: str) -> bool:
    """Whether a block's file has a check, a call of `pass "..."`, whose text starts with TEXT."""
    return any(line[line.find('pass "') + 6:].startswith(text) for line in path.read_text(encoding="utf-8").split("\n") if 'pass "' in line)


class TheList(unittest.TestCase):
    def bullets(self) -> list[tuple[str | None, list[str]]]:
        self.assertTrue(LIST.is_file(), f"{LIST.relative_to(ROOT)} does not exist")
        found = parts(LIST)
        self.assertTrue(found, f"{LIST.relative_to(ROOT)} holds no bullet")
        return found

    def test_each_bullet_has_its_sentence_in_bold_its_day_and_three_lines_at_most_after_it(self):
        for heading, lines in self.bullets():
            text = flat(" ".join(lines))
            with self.subTest(bullet=text[:80]):
                self.assertRegex(text, r"^- \*\*[^*]+\*\*", "a bullet opens with its rule, one sentence in bold")
                day = DAY.search(text)
                self.assertIsNotNone(day, "a bullet ends with its day in parentheses, (YYYY-MM-DD) or (decided YYYY-MM-DD)")
                self.assertEqual(bool(day["decided"]), heading == LAST, f'a bullet of "{LAST}" says decided before its day, and only there')
                self.assertLessEqual(description_lines(lines), 3, "a bullet says more in three lines at most")
                for line in lines:
                    self.assertLessEqual(len(line), 100, f"a line of the list is 100 characters at most: {line[:60]}")

    def test_each_heading_is_a_group_in_its_order_and_the_last_part_closes_the_list(self):
        found = headings(LIST)
        self.assertEqual(found[-1:], [LAST], f'the last heading of the list is "{LAST}"')
        groups = found[:-1]
        self.assertTrue(set(groups) <= set(GROUPS), f"a heading of the list is no group: {sorted(set(groups) - set(GROUPS))}")
        self.assertEqual(groups, [group for group in GROUPS if group in groups], "the groups stand in their order, each once")
        under = {heading for heading, _ in self.bullets()}
        for heading in found:
            with self.subTest(heading=heading):
                self.assertIn(heading, under, "a heading with no bullet is left out")
        self.assertRegex(first_line_under(LIST, LAST), r"^None of these is his ruling\b", "the last part opens with the line that none of its bullets is his ruling")

    def test_each_path_the_list_names_exists(self):
        # A path is a name in backticks with a slash between two names, no space, no `:`, `@` or `*`,
        # no placeholder (`<slug>`, SLUG) and no leading `/` (a command), outside his quoted words. It
        # resolves from the root or from the skill's folder skills/lem/.
        text = QUOTED.sub('""', flat(LIST.read_text(encoding="utf-8")))
        for match in CODE.finditer(text):
            name = match[1]
            if not PATH.fullmatch(name) or PLACEHOLDER.search(name) or name.startswith((".lem/state/", "~")) or name in ELSEWHERE:
                continue
            with self.subTest(path=name):
                self.assertTrue((ROOT / name).exists() or (ROOT / "skills" / "lem" / name).exists(), f"the list names `{name}`, which is not in the repository")


class TheHistory(unittest.TestCase):
    def lines(self, heading: str) -> list[str]:
        self.assertTrue(HISTORY.is_file(), f"{HISTORY.relative_to(ROOT)} does not exist")
        found = [flat(" ".join(lines)) for under, lines in parts(HISTORY) if under == heading]
        self.assertTrue(found, f'the history has no line under "{heading}"')
        return found

    def test_the_history_has_its_two_parts_and_names_where_the_full_text_is(self):
        self.assertEqual(headings(HISTORY), [HELD, KEPT])
        opening = HISTORY.read_text(encoding="utf-8").split("\n## ", 1)[0]
        self.assertRegex(opening, r"`[0-9a-f]{7,40}`", "the opening names the commit that still holds the files the list took the place of")

    def test_each_rule_a_test_holds_names_a_guard_that_exists(self):
        # His "it will not drift": a test renamed or removed fails here, and its rule goes back to the list.
        for line in self.lines(HELD):
            with self.subTest(line=line[:80]):
                self.assertIsNotNone(DAY.search(line), "a line ends with its day")
                guards = [span for span in CODE.findall(line) if UNIT.fullmatch(span) or BLOCK.fullmatch(span) or SCRIPT.fullmatch(span)]
                self.assertTrue(guards, "a line names its guard: `tests/unit/FILE.py::test_name`, `tests/FILE.sh: \"the check's first words\"` or `skills/.../FILE.py: function`")
                for guard in guards:
                    if match := UNIT.fullmatch(guard):
                        path = ROOT / "tests/unit" / match["file"]
                        self.assertTrue(path.is_file() and defined(path, match["name"], match["cls"]), f"{guard}: no such test")
                    elif match := BLOCK.fullmatch(guard):
                        path = ROOT / "tests" / match["file"]
                        self.assertTrue(path.is_file() and has_check(path, match["text"]), f'{guard}: no check of that block starts with these words')
                    elif match := SCRIPT.fullmatch(guard):
                        path = ROOT / match["file"]
                        self.assertTrue(path.is_file() and defined(path, match["name"]), f"{guard}: no such function")

    def test_each_rule_kept_in_one_place_names_a_path_that_exists(self):
        for line in self.lines(KEPT):
            with self.subTest(line=line[:80]):
                self.assertIsNotNone(DAY.search(line), "a line ends with its day")
                paths = [span for span in CODE.findall(line) if PATH.fullmatch(span) or span in ("AGENTS.md", "README.md")]
                self.assertTrue(paths, "a line names its place by its path")
                for path in paths:
                    self.assertTrue((ROOT / path).exists(), f"`{path}` does not exist")


class TheMove(unittest.TestCase):
    def test_the_plan_has_a_row_for_each_file_the_list_took_the_place_of(self):
        rows = plan_rows()
        self.assertEqual(len(rows), len(set(rows)), "a file has two rows")
        for folder, count in FOLDERS.items():
            with self.subTest(folder=folder):
                stems = [stem for where, stem in rows if where == folder]
                self.assertEqual(len(stems), count, f"the plan's table has {len(stems)} rows of {folder}, which held {count} files")
                self.assertTrue(all(re.fullmatch(r"[a-z0-9-]+", stem) for stem in stems), "a row names its file by its stem")

    def test_the_rulings_folder_holds_the_list_and_the_history_only(self):
        self.assertEqual(sorted(path.name for path in (ROOT / "docs/rulings").iterdir()), ["history.md", "rulings.md"])
        self.assertFalse((ROOT / ".lem/decisions").exists(), ".lem/decisions is gone: its choices are in the list's last part or in the history")

    def test_no_file_names_a_file_the_list_took_the_place_of(self):
        rulings = {stem for folder, stem in plan_rows() if folder == "docs/rulings"}
        decisions = {stem for folder, stem in plan_rows() if folder == ".lem/decisions"}
        self.assertTrue(rulings and decisions, "the plan's table names no file")
        named = re.compile(r"(?P<folder>rulings|decisions)/(?P<stem>[a-z0-9-]+)\.md|\.lem/decisions/[\w-]")
        for path in tracked():
            if path in MAY_NAME or not (ROOT / path).is_file():
                continue
            try:
                text = (ROOT / path).read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for match in named.finditer(text):
                gone = match["stem"] in (rulings if match["folder"] == "rulings" else decisions) if match["stem"] else True
                with self.subTest(file=path, name=match[0]):
                    self.assertFalse(gone, f'{path} names {match[0]}: cite the rule\'s sentence in quotes with docs/rulings/rulings.md or docs/rulings/history.md')


class ShortAgents(unittest.TestCase):
    def test_agents_md_is_short(self):
        words = len(AGENTS.read_text(encoding="utf-8").split())
        self.assertLessEqual(words, WORDS, f"AGENTS.md has {words} words by wc -w; the bound is {WORDS}")

    def test_agents_md_names_the_list_and_the_history_and_no_ruling_by_link(self):
        text = AGENTS.read_text(encoding="utf-8")
        for name in ("docs/rulings/rulings.md", "docs/rulings/history.md"):
            self.assertIn(f"`{name}`", text)
        self.assertNotRegex(text, r"\]\(docs/rulings/|\]\(\.lem/decisions/", "AGENTS.md links no ruling's file: the list holds them")

    def test_the_names_docs_free_hour_cites_are_headings_of_agents_md_or_bullets_of_the_list(self):
        # docs/free-hour.md sends an unattended session to these by name.
        text = AGENTS.read_text(encoding="utf-8")
        found = {line.lstrip("#").strip() for line in text.split("\n") if line.startswith("#")}
        found |= {re.match(r"- \*\*([^*]+)\*\*", flat(" ".join(lines)))[1].rstrip(".") for _, lines in parts(LIST)}
        for name in ("Opinionated and small", "The owner's rulings", "Rules for a change here", "Checks"):
            with self.subTest(name=name):
                self.assertIn(name, found, f'"{name}", which docs/free-hour.md cites, is no heading of AGENTS.md and no bullet of the list')


if __name__ == "__main__":
    unittest.main()
