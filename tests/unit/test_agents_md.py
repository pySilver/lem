"""The short AGENTS.md and the files of its rulings and decisions: each sentence of "The owner's
rulings" and "Decisions the maintaining session took" is the text of a link to one file of
docs/rulings/ or .lem/decisions/, and the files and the sentences agree. Each path a ruling names in
its in-force text is in the repository.

It reads only the repository's own files, so a missing folder or file is a failed case.

    python3 -B -m unittest discover -s tests/unit -p test_agents_md.py
"""

import re
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
AGENTS = ROOT / "AGENTS.md"
RULINGS = "docs/rulings"
DECISIONS = ".lem/decisions"
HEADS = {"## The owner's rulings": RULINGS, "## Decisions the maintaining session took": DECISIONS}
# Criterion 1 of docs/plans/2026-11-21-agents-md-read-on-demand.md: the session's estimate with
# room, not a measured size (2026-11-21).
WORDS = 8000
LINE = re.compile(r"- \[(?P<text>.*)\]\((?P<path>[^()\s]+)\)")
LINK = re.compile(r"\]\((?P<path>[^()\s]+\.md)\)")
CODE = re.compile(r"`([^`]+)`")
PATH = re.compile(r"[^/\s:@*][^\s:@*]*/[^\s:@*]+")
PLACEHOLDER = re.compile(r"<[^>]*>|\b[A-Z]{2,}\b")
QUOTED = re.compile(r'"[^"]*"')
# A name right after "takes the place of", "in place of" or "replaces", or followed in its clause by
# "not taken", "is gone" or "was removed", names what is no longer there.
GONE_BEFORE = re.compile(r"\b(takes the place of|in place of|replaces)\s*$")
GONE_AFTER = re.compile(r"^[^.;:]*\b(not taken|is gone|was removed)\b")
# The paths a ruling names in another repository, each with where it is.
ELSEWHERE = {
    ".claude/rules": "the folder of rules in a project that adopts Lem (the-rules-of-an-existing-project-stay-where-they-are)",
    "codex-rs/protocol/src/permissions.rs": "a file of Codex's own repository, read 2026-11-17 (the-state-of-lem-is-not-in-the-git-directory)",
}


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def in_force(text: str) -> str:
    """A file's text without its front matter and without the words that no longer hold: the
    sections `## Replaced, not in force` and `## As ruled on DAY, changed in part since`."""
    kept, keep = [], True
    for line in re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S).split("\n"):
        if line.startswith("## "):
            keep = not (line == "## Replaced, not in force" or re.fullmatch(r"## As (ruled|decided) on .+, changed in part since", line))
        if keep:
            kept.append(line)
    return "\n".join(kept)


def sentences() -> list[dict]:
    """Each link line of the two sections: its text, its path from the root, its section's folder
    and the `###` heading it stands under."""
    lines = AGENTS.read_text(encoding="utf-8").split("\n")
    out, folder, group = [], None, None
    for line in lines:
        if line.startswith("## "):
            folder, group = HEADS.get(line), None
        elif line.startswith("### "):
            group = line[4:]
        elif folder and line.startswith("- "):
            match = LINE.fullmatch(line)
            out.append({"line": line, "text": match and match["text"], "path": match and match["path"], "folder": folder, "group": group})
    return out


def front(text: str) -> dict:
    """The front matter block of a file, as keys and values; {} when the file has none."""
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    return dict(line.split(": ", 1) for line in match[1].split("\n") if ": " in line)


def title(text: str) -> str | None:
    match = re.search(r"^# (.+)$", text, re.M)
    return match[1] if match else None


class ShortAgents(unittest.TestCase):
    def files(self, folder: str) -> list[Path]:
        found = sorted((ROOT / folder).glob("*.md"))
        if not found:
            self.fail(f"{folder} holds no file: the rulings and the decisions have not moved out of AGENTS.md")
        return found

    def links(self) -> list[dict]:
        found = sentences()
        if not found:
            self.fail("the two sections of AGENTS.md hold no line with a link: the rulings and the decisions have not moved")
        return found

    def test_each_sentence_is_one_link_to_a_file_that_exists_in_its_sections_folder(self):
        for each in self.links():
            with self.subTest(line=each["line"][:80]):
                self.assertIsNotNone(each["path"], "a line of the two sections is the sentence as a link, and nothing else")
                self.assertTrue((ROOT / each["path"]).is_file(), f"{each['path']} does not exist")
                self.assertEqual(str(Path(each["path"]).parent), each["folder"], "a ruling links docs/rulings, a decision .lem/decisions")

    def test_each_link_in_a_file_of_the_two_folders_names_a_file_that_exists(self):
        for path in self.files(RULINGS) + self.files(DECISIONS):
            for match in LINK.finditer(path.read_text(encoding="utf-8")):
                with self.subTest(file=path.name, link=match["path"]):
                    self.assertTrue((path.parent / match["path"]).resolve().is_file(), f"{path.name} links {match['path']}, which does not exist")

    def test_each_file_is_linked_by_one_sentence_or_by_the_file_of_what_replaced_it(self):
        linked = [(ROOT / each["path"]).resolve() for each in self.links() if each["path"]]
        self.assertEqual(len(linked), len(set(linked)), "two sentences link one file")
        for path in self.files(RULINGS) + self.files(DECISIONS):
            if path.resolve() in linked:
                continue
            with self.subTest(file=path.name):
                text = path.read_text(encoding="utf-8")
                after = text.split(f"# {title(text)}\n", 1)[-1].lstrip("\n").split("\n", 1)[0]
                self.assertTrue(after.startswith("Replaced, not in force"), f"{path.name} has no sentence in AGENTS.md and is not marked replaced")
                match = LINK.search(after)
                self.assertIsNotNone(match, f"{path.name} does not link what replaced it")
                by = (path.parent / match["path"]).resolve()
                self.assertIn(by, linked, f"what replaced {path.name} has no sentence in AGENTS.md")
                back = [(by.parent / found["path"]).resolve() for found in LINK.finditer(by.read_text(encoding="utf-8"))]
                self.assertIn(path.resolve(), back, f"{by.name} does not link {path.name}, which it replaced")

    def test_each_sentence_is_the_title_of_its_file_and_its_group_the_files_area(self):
        for each in self.links():
            with self.subTest(line=each["line"][:80]):
                self.assertIsNotNone(each["path"])
                text = (ROOT / each["path"]).read_text(encoding="utf-8")
                self.assertEqual(title(text), each["text"], "the sentence is the # title of its file")
                self.assertIsNotNone(each["group"], "a sentence stands under a ### heading of its group")
                self.assertEqual(front(text).get("area"), each["group"], "the file's area: is the heading of its sentence's group")

    def test_a_ruling_says_ruled_and_a_decision_says_decided(self):
        for path in self.files(RULINGS):
            with self.subTest(file=path.name):
                head = front(path.read_text(encoding="utf-8"))
                self.assertIn("ruled", head)
                self.assertIn("area", head)
        for path in self.files(DECISIONS):
            with self.subTest(file=path.name):
                head = front(path.read_text(encoding="utf-8"))
                self.assertIn("decided", head)
                self.assertNotIn("ruled", head, "no line of a decision's file names the owner's ruling")
                self.assertIn("area", head)

    def test_agents_md_is_short(self):
        words = len(AGENTS.read_text(encoding="utf-8").split())
        self.assertLessEqual(words, WORDS, f"AGENTS.md has {words} words by wc -w; the bound of {WORDS} is criterion 1 of "
                             "docs/plans/2026-11-21-agents-md-read-on-demand.md, the session's estimate (2026-11-21)")

    def test_a_replaced_ruling_is_only_in_the_file_of_the_ruling_that_replaced_it(self):
        holders = [path for path in self.files(RULINGS) if "Codex in each role" in path.read_text(encoding="utf-8")]
        self.assertEqual([path.name for path in holders], ["claude-code-and-agterm-first-and-codex-for-reviews.md"])
        text = holders[0].read_text(encoding="utf-8")
        self.assertEqual(title(text), "Claude Code and agterm first, and Codex for reviews")
        self.assertIn("**Codex in each role is wanted**", text.split("\n## Replaced, not in force\n", 1)[-1])
        self.assertIn("\n## Replaced, not in force\n", text)
        self.assertNotIn("Codex in each role", "\n".join(each["line"] for each in self.links()))

    def test_a_decision_of_the_session_is_not_in_docs(self):
        self.assertEqual([path.name for path in self.files(DECISIONS) if "Lem is a companion, not a gate" in path.read_text(encoding="utf-8")],
                         ["lem-is-a-companion-not-a-gate.md"])
        self.assertEqual([path.name for path in self.files(RULINGS) if "Lem is a companion, not a gate" in path.read_text(encoding="utf-8")], [])

    def test_the_logos_paragraph_is_whole_in_one_file(self):
        paragraph = flat("""**The logo is the owner's pick** ("The Line in the Field"). Change it only on his word. The
  night palette of its dark-theme version is his pick too.""")
        holders = [path.name for path in self.files(RULINGS) if paragraph in flat(path.read_text(encoding="utf-8"))]
        self.assertEqual(holders, ["the-logo-is-the-owners-pick.md"])

    def test_a_rulings_file_starts_with_its_day_and_its_area(self):
        path = ROOT / RULINGS / "github-pull-requests-are-the-one-way-to-land.md"
        self.assertTrue(path.is_file(), f"{path} does not exist")
        lines = path.read_text(encoding="utf-8").split("\n")
        self.assertEqual(lines[:6], ["---", "ruled: 2026-11-20", "area: The review, the pull request and the merge", "---", "",
                                     "# GitHub pull requests are the one way to land"])

    def test_a_ruling_changed_in_part_says_what_changed_before_its_old_words(self):
        path = ROOT / RULINGS / "the-plan-talk-is-a-pair-in-a-companion-that-closes-after-it.md"
        self.assertTrue(path.is_file(), f"{path} does not exist")
        text = path.read_text(encoding="utf-8")
        changed, _, old = text.partition("\n## As ruled on 2026-11-16, changed in part since\n")
        self.assertIn("\n## Changed in part\n", changed)
        for later in ("2026-11-19, [", "[The build asks him nothing, and the ladder always decides]", "2026-11-20, [Each task lives in a session of its own"):
            self.assertIn(later, changed)
        self.assertIn("**The plan talk is a pair in a companion that closes after it**", old)

    def test_a_sentence_drops_the_part_that_a_later_ruling_took_away(self):
        # Criterion 4: "and agdoc is required too" went on 2026-11-20 with the page at the end of a
        # task ("GitHub pull requests are the one way to land"), so no sentence and no title says it.
        sentence = "agterm, the mailbox chat and revmux stay required"
        found = [each for each in self.links() if each["text"] == sentence]
        self.assertEqual(len(found), 1, f'AGENTS.md has no sentence "{sentence}"')
        self.assertEqual(found[0]["path"], f"{RULINGS}/agterm-the-mailbox-chat-and-revmux-stay-required.md")
        self.assertNotIn("agdoc is required", "\n".join(each["line"] for each in self.links()))
        titles = [path.name for path in self.files(RULINGS) if "agdoc is required" in (title(path.read_text(encoding="utf-8")) or "")]
        self.assertEqual(titles, [], "a title is the rule as it stands, and agdoc is no longer required")

    def test_the_names_docs_free_hour_cites_are_headings_or_sentences_of_agents_md(self):
        # Criterion 9: docs/free-hour.md sends an unattended session to these four by name.
        text = AGENTS.read_text(encoding="utf-8")
        headings = {line.lstrip("#").strip() for line in text.split("\n") if line.startswith("#")}
        linked = {each["text"].rstrip(".") for each in self.links() if each["text"]}
        for name in ("Opinionated and small", "The owner's rulings", "Rules for a change here", "Checks"):
            with self.subTest(name=name):
                self.assertTrue(name in headings or name in linked, f'"{name}", which docs/free-hour.md cites, is no heading and no sentence of AGENTS.md')

    def test_each_path_a_ruling_names_in_force_exists(self):
        # A path is a name in backticks with a slash between two names, no space, no `:`, `@` or `*`
        # (a seat, a glob), no placeholder (`<slug>`, SLUG, YYYY) and no leading `/` (a command or a
        # route). It counts in the in-force text only, outside his quoted words, and resolves from the
        # root or from the skill's folder skills/lem/, as the stages name stages/, prompts/ and scripts/.
        # A name the text says is gone (GONE_BEFORE, GONE_AFTER) claims no file.
        for path in self.files(RULINGS):
            for paragraph in re.split(r"\n\s*\n", in_force(path.read_text(encoding="utf-8"))):
                text = QUOTED.sub('""', flat(paragraph))
                for match in CODE.finditer(text):
                    name = match[1]
                    if not PATH.fullmatch(name) or PLACEHOLDER.search(name) or name.startswith((".lem/state/", "~")) or name in ELSEWHERE:
                        continue
                    if GONE_BEFORE.search(text[:match.start()]) or GONE_AFTER.search(text[match.end():].lstrip(")")):
                        continue
                    with self.subTest(file=path.name, path=name):
                        self.assertTrue((ROOT / name).exists() or (ROOT / "skills" / "lem" / name).exists(),
                                        f"{path.name} names `{name}`, which is not in the repository: correct the name, or mark the ruling changed in part")

    def test_the_first_line_under_the_decisions_says_none_is_his_ruling(self):
        # Criterion 5: the heading of the session's decisions opens with the line that none of them is the owner's.
        after = AGENTS.read_text(encoding="utf-8").split("\n## Decisions the maintaining session took\n", 1)
        self.assertEqual(len(after), 2, 'AGENTS.md has no heading "Decisions the maintaining session took"')
        first = after[1].lstrip("\n").split("\n", 1)[0]
        self.assertRegex(first, r"^None of these is (his|the owner's) ruling\b", "the first line under the decisions' heading says that none of these is his ruling")


if __name__ == "__main__":
    unittest.main()
