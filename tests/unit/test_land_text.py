"""What land.py decides from a task's records at a proposal, and how its lines say it, each called in this process.

The records are the ones the real writers write: a decision's lines as `lem decisions` appends them,
folded by decisions.py's own `Task.decisions`; the criteria as criteria.py's `parse` reads a plan and
decisions.py's `Task.changes` adds the approvals and the changes of a criterion; a review's entry as
`lem land read` keeps it. The blocks of tests/ keep one real proposal of each family, which reads the
real `pr.md`, so that the writer and the reader still meet.
"""

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
land = importlib.import_module("land")
decisions = importlib.import_module("decisions")
criteria = importlib.import_module("criteria")

AT = "2026-11-18T10:00:00Z"
LATER = "2026-11-18T11:00:00Z"
PLAN = (
    "## Acceptance criteria\n\nSize: full, because the ticket names the word and the file.\n\n"
    "1. The file holds the word y.\n   - test: `sh tests/t.sh` in `tests/t.sh`\n2. The file has one line.\n   - no test: printf ends every line so.\n"
)


# A decision's lines, each in the form the command of decisions.py that writes it gives it.
def asked(number: int, what: str, options: tuple[str, ...], recommended: str, why: str, *, advisers: tuple[str, ...] = ("fable", "astra")) -> dict:
    """`lem decisions ask`: a choice that waits for the owner."""
    return {
        "id": number, "at": AT, "kind": "asked", "what": what, "case": "1. One step.\n2. Another.", "case_was": "derived", "cause": "the personas split",
        "options": list(options), "recommended": recommended, "why": why, "said": "The two personas split.", "irreversible": None, "advisers": list(advisers),
    }


def taken(number: int, what: str, chose: str, why: str, by: str, **more: object) -> dict:
    """`lem decisions log`: a decision taken on the ladder."""
    return {"id": number, "at": AT, "kind": "taken", "what": what, "chose": chose, "why": why, "by": by, **more}


def answered(number: int, chose: str, **reason: object) -> dict:
    """`lem decisions answer` of a choice that waits: `words`, `why`, `instead`."""
    return {"id": number, "at": LATER, "kind": "answered", "chose": chose, **reason}


def late(number: int, chose: str, **reason: object) -> dict:
    """`lem decisions answer` of a choice that was taken without him."""
    return {"id": number, "at": LATER, "kind": "late", "chose": chose, **reason}


def advised(number: int, expert: str, pick: str, why: str) -> dict:
    """`lem decisions advise`: one expert's pick."""
    return {"id": number, "at": AT, "kind": "advised", "expert": expert, "pick": pick, "why": why}


def ledger(directory: Path) -> "decisions.Task":
    """decisions.py's own record of a task in DIRECTORY, without the commands that find it."""
    record = decisions.Task.__new__(decisions.Task)
    record.slug, record.directory, record.file = "t", directory, directory / "decisions.jsonl"
    directory.mkdir(parents=True, exist_ok=True)
    return record


def folded(lines: list[dict]) -> list[dict]:
    """The decisions as `lem decisions list` gives them, from their lines."""
    with tempfile.TemporaryDirectory() as folder:
        record = ledger(Path(folder))
        record.file.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
        return record.decisions()


def away(lines: list[dict], number: int) -> list[dict]:
    """The lines with the one that takes choice NUMBER as the owner goes away: decisions.py's `ending`."""
    choice = next(decision for decision in folded(lines) if decision["id"] == number)
    return [*lines, decisions.ending(number, choice, LATER)]


def approval(by: str, number: int = 1, plan: str = PLAN, at: str = AT, history: tuple[dict, ...] = ()) -> dict:
    """criteria.json as `lem criteria approve` writes it."""
    read = criteria.parse(plan, "approved.md")
    texts = [criterion["text"] for criterion in read["criteria"]]
    return {
        "task": "t", "number": number, "at": at, "by": by, "size": read["size"], "why": read["why"], "digest": criteria.text_digest(read["size"], texts),
        "criteria": [{"n": n, "text": text} for n, text in enumerate(texts, start=1)], "text": plan, "history": list(history),
    }


def change(number: int, how: str, criterion: int, why: str, **more: object) -> dict:
    """`lem decisions criterion`: one change of an approved criterion (`was`, `now`, and `choice` or `by`)."""
    return {"change": number, "at": AT, "kind": "criterion", "how": how, "criterion": criterion, "why": why, "approval": 1, **more}


def found_of(plan: str = PLAN, approved: dict | None = None, lines: tuple[dict, ...] = ()) -> dict:
    """What `lem criteria show` gives: the plan's criteria with the approvals and changes of the record."""
    read = criteria.parse(plan, "plan.md")
    digest = criteria.text_digest(read["size"], [criterion["text"] for criterion in read["criteria"]])
    with tempfile.TemporaryDirectory() as folder:
        record = ledger(Path(folder))
        if approved:
            (Path(folder) / "criteria.json").write_text(json.dumps(approved), encoding="utf-8")
        record.file.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
        changes = record.changes()
    return {"task": "t", "plan": "plan.md", "small": read["size"] == "small", **read, "criteria_digest": digest,
            **{key: changes[key] for key in ("approved", "approvals", "changes", "history")}}


def review(round_: int, *, answered_by: tuple[str, ...] = ("codex",), kind: str = "read", patch: str = "p1", must_fix: int = 0, contents: dict | None = None, **more: object) -> dict:
    """One review's entry as `lem land read --record` keeps it."""
    return {
        "attempt": round_, "round": round_, "kind": kind, "ran": [], "left_out": [], "answered": list(answered_by), "silent": [], "bar": [],
        "must_fix": must_fix, "should": 0, "nit": 0, "outside": [], "careful": False, "careful_why": "the diff reaches no topic of the settings",
        "date": AT[:10], "verdict": "not reviewed" if not answered_by else "must-fix" if must_fix else "clean", "tip": "abc123456", "patch": patch,
        "contents": contents if contents is not None else {"x.txt": {"base": "0" * 40, "tip": "1" * 40, "modes": ["000000", "100644"]}}, **more,
    }


CHECKS = {
    "commands": [{"command": "true", "exit": 0, "last": "", "output": "/tmp/out"}],
    "criteria": {"ok": True, "tests": [{"criterion": 1, "command": "sh tests/t.sh", "problem": None}], "without_a_test": [{"criterion": 2}]},
    "bar": {"lowered": [], "edited": []}, "size": {"files": 1, "lines": 1},
}


class Proposal(unittest.TestCase):
    """A land.Task over a task directory of the test's own, with the records each case gives."""

    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)

    def task(self, lines: list[dict] = (), found: dict | None = None, kept: dict | None = None, record: dict | None = None, events: tuple[dict, ...] = ()) -> "land.Task":
        task = land.Task.__new__(land.Task)
        task.slug, task.base, task.onto = "t", "main", "main"
        task.settings = {"checks": {"commands": ["true"]}}
        task.main, task.worktree = self.root, self.root / "no-worktree"
        task.directory = self.root / "state" / "tasks" / "t"
        task.directory.mkdir(parents=True, exist_ok=True)
        task.kept_file = task.directory / "landing.json"
        task.kept_file.write_text(json.dumps({"checks": CHECKS, "polish": {"commits": 0, "filed": []}, "reads": [review(1)], **(kept or {})}), encoding="utf-8")
        task.recorded = folded(list(lines))
        task.criteria = found or found_of(approved=approval("owner"))
        task.plan_said, task.branch_gate = False, None
        task.record = {"slug": "t", "status": "landing", **(record or {})}
        (self.root / "state" / "events.jsonl").write_text("".join(json.dumps({"ts": AT, "task": "t", **event}) + "\n" for event in events), encoding="utf-8")
        return task

    def state(self, **more: object) -> dict:
        return {"careful": [], "due": "none", "why": "round 1 reviewed this change and left no must-fix", "tasks": 1, "files": ["x.txt"], **more}

    def reasons(self, *lines: dict, **given: object) -> list[str]:
        return land.not_green(self.task(list(lines), **given), self.state())


class ChoicesWithoutHim(Proposal):
    """A choice that waited for the owner and was taken as he went away is not green, one line each,
    with a late answer of his; an answered choice is no cause of not green."""

    WHERE = asked(1, "Where the word goes", ("the first line", "the last line"), "the first line", "A reader sees it at once.")
    CASE = asked(1, "The case of the word", ("lower case", "upper case"), "lower case", "The test reads it so.")

    def test_the_ladder_pick_with_the_same_late_answer(self) -> None:
        lines = [*away([self.WHERE], 1), late(1, "the first line", why="The importer reads the first line.")]
        [line] = self.reasons(*lines)
        self.assertTrue(line.startswith("choice 1 was taken without the owner (Where the word goes): \"the first line\", the recommended option"))
        self.assertIn("the owner answered later with the same (the owner's reason: The importer reads the first line)", line)
        said = land.decided(folded(lines)[0])
        self.assertIn("the ladder's pick, taken at once", said)
        self.assertIn("A reader sees it at once.", said)

    def test_a_late_answer_that_differs_says_his_words(self) -> None:
        lines = [*away([self.CASE], 1), late(1, "upper case", words="Make it upper case.", why="The header is in upper case.")]
        [line] = self.reasons(*lines)
        self.assertIn("\"upper case\", which differs (the owner's words: \"Make it upper case.\"; the owner's reason: The header is in upper case)", line)

    def test_an_answered_choice_is_no_cause(self) -> None:
        lines = [
            asked(1, "Tell the merchants", ("send the email", "send nothing"), "send nothing", "Nothing they see changes."),
            answered(1, "send the email", words="Yes, send it.", why="The merchants asked for it."),
            asked(2, "Which line", ("the only line", "the second line"), "the second line", "A header goes first."), answered(2, "the second line"),
            asked(3, "Email the customers", ("all", "nobody"), "nobody", "Nobody asked for it."), answered(3, "Only the beta testers.", instead=True, why="They asked to hear first."),
            asked(4, "The line ending", ("a break", "none"), "a break", "Every file ends so."), answered(4, "A break and a date.", instead=True),
        ]
        self.assertEqual(self.reasons(*lines), [])
        over, recommended, instead, bare = (land.decided(decision) for decision in folded(lines))
        # the recommendation's reason is never said as his
        self.assertIn("over the recommended \"send nothing\" (recommended because: Nothing they see changes)", over)
        self.assertIn("The owner's words: \"Yes, send it.\" The owner's reason: The merchants asked for it.", over)
        self.assertIn(", as recommended. A header goes first.", recommended)
        self.assertIn("none of the options; the recommended was \"nobody\"", instead)
        self.assertNotIn("gave no reason", instead)
        self.assertIn("The owner gave no reason.", bare)

    def test_a_choice_that_waits_says_so(self) -> None:
        self.assertEqual(land.decided(folded([self.WHERE])[0]), "- Where the word goes: waits for the owner.")


class TheExperts(Proposal):
    """A choice the experts took as the owner went away names their pick and both reasons; one whose
    experts split took the recommended option; one expert alone is named as one."""

    def advised_choice(self, fable: str, astra: str) -> list[dict]:
        return [
            asked(1, "Where the word goes", ("the first line", "the last line"), "the first line", "A reader sees it at once."),
            advised(1, "fable", fable, "A reader looks at the end first."), advised(1, "astra", astra, "The importer reads the last line."),
        ]

    def test_their_shared_pick_is_not_green_with_both_reasons(self) -> None:
        lines = [*away(self.advised_choice("the last line", "the last line"), 1), late(1, "the first line", why="The test reads it so.")]
        [line] = self.reasons(*lines)
        self.assertTrue(line.startswith("choice 1 was taken by the experts (Where the word goes): \"the last line\", the option both picked"))
        self.assertIn("Fable: A reader looks at the end first. Astra: The importer reads the last line", line)
        self.assertIn("; the owner answered later with \"the first line\", which differs", line)
        said = land.decided(folded(lines)[0])
        self.assertIn("by the experts, the option both picked", said)
        self.assertIn("the recommended was \"the first line\"", said)

    def test_their_pick_that_is_the_recommended_says_so(self) -> None:
        said = land.decided(folded(away(self.advised_choice("the first line", "the first line"), 1))[0])
        self.assertIn("it is also the recommended", said)

    def test_a_split_takes_the_recommended_option(self) -> None:
        lines = away(self.advised_choice("the first line", "the last line"), 1)
        [line] = self.reasons(*lines)
        self.assertTrue(line.startswith("choice 1 was taken without the owner (Where the word goes): \"the first line\", the recommended option"))
        self.assertIn("the ladder's pick", land.decided(folded(lines)[0]))

    def test_one_expert_alone_is_named_as_one(self) -> None:
        lines = [taken(1, "The word's case", "upper case", "Fable: the header is in upper case.", "experts", advisers=["fable"], options=["lower case", "upper case"])]
        [line] = self.reasons(*lines)
        self.assertTrue(line.startswith("decision 1 was taken without the owner (The word's case)"))
        self.assertTrue(line.endswith(", by one expert"))
        self.assertIn("by one expert. Fable: the header is in upper case.", land.decided(folded(lines)[0]))
        page = land.decisions_text(self.task(lines), "o", [line], "fix/o", None)
        self.assertIn("| 1 | The word's case | upper case | one expert model; **not green** |", page)

    def test_one_experts_pick_as_he_went_away(self) -> None:
        lines = [asked(1, "Where", ("a", "b"), "a", "A reads first.", advisers=("fable",)), advised(1, "fable", "b", "B reads better.")]
        [line] = self.reasons(*away(lines, 1))
        self.assertTrue(line.startswith("choice 1 was taken by one expert (Where): \"b\", the one expert's pick"))

    def test_two_experts_on_a_shared_choice_are_named_as_two(self) -> None:
        lines = away(self.advised_choice("the last line", "the last line"), 1)
        self.assertIn("| two expert models; **not green** |", land.decisions_text(self.task(lines), "e", ["x"], "fix/e", None))


class CriteriaThatChanged(Proposal):
    """A criterion the build changed, added or removed is not green, each with its line; a change that
    an approval of his took over is his, and no cause."""

    def test_a_changed_criterion_by_the_personas(self) -> None:
        moved = change(1, "changed", 1, "y is taken by another file.", was="The file holds the word y.", now="The file holds the word the owner asked for.", by="personas", said="Both personas picked x.")
        plan = PLAN.replace("the word y.", "the word the owner asked for.")
        task = self.task(found=found_of(plan, approval("owner"), (moved,)))
        [reason] = land.not_green(task, self.state())
        self.assertTrue(reason.startswith("criterion 1 changed during the build: y is taken"))
        line = land.change_line(task, task.criteria["history"][0])
        self.assertIn("was \"The file holds the word y.\", now \"The file holds the word the owner asked for.\"", line)
        self.assertTrue(line.endswith("By the personas: Both personas picked x."))

    def test_one_removed_after_a_choice_and_one_added_by_the_lead(self) -> None:
        lines = [asked(1, "The one-line rule", ("keep the rule", "no such rule"), "keep the rule", "A reader counts on it."), answered(1, "no such rule")]
        removed = change(1, "removed", 2, "A second line holds the date now.", was="The file has one line.", choice=1)
        added = change(2, "added", 2, "The importer reads whole lines only.", now="The file ends with a line break.", by="lead")
        plan = PLAN.replace("2. The file has one line.", "2. The file ends with a line break.")
        task = self.task(lines, found=found_of(plan, approval("owner"), (*lines, removed, added)))
        removed_line, added_line = land.not_green(task, self.state())
        self.assertTrue(removed_line.startswith("criterion 2 was removed during the build"))
        self.assertIn("after choice 1 (The one-line rule), where the owner took \"no such rule\"", removed_line)
        self.assertTrue(added_line.startswith("criterion 2 was added during the build: The importer reads"))
        self.assertTrue(land.change_line(task, task.criteria["history"][1]).endswith("By the lead."))

    def test_a_change_his_later_approval_took_over_is_his(self) -> None:
        moved = change(1, "changed", 1, "y is taken.", was="The file holds the word y.", now="The file holds the word z.", by="lead")
        plan = PLAN.replace("the word y.", "the word z.")
        first = {key: value for key, value in approval("owner").items() if key not in ("history", "task", "text")}
        task = self.task(found=found_of(plan, approval("owner", 2, plan, LATER, (first,)), (moved,)))
        self.assertEqual(land.not_green(task, self.state()), [])
        self.assertTrue(land.change_line(task, task.criteria["history"][0]).endswith("Approved by the owner afterwards (approval 2)."))

    def test_criteria_approved_without_him(self) -> None:
        [line] = land.not_green(self.task(found=found_of(approved=approval("alone"))), self.state())
        self.assertTrue(line.startswith("the owner did not approve the criteria"))


class TheRead(Proposal):
    """The personas' read of the criteria, from its event, in the pull request's checks."""

    def read(self, **more: object) -> dict:
        found = found_of()
        return {"event": "criteria.read", "by": "lem", "asked": 2, "answered": 2, "families": ["opus", "sol"], "silent": [], "criteria": 2, "flagged": 0, "split": False, "digest": found["criteria_digest"], **more}

    def test_two_reads_nobody_answered_are_not_green(self) -> None:
        quiet = self.read(answered=0, families=[], silent=[{"name": "the buyer, opus", "why": "the model was at capacity"}])
        task = self.task(found=found_of(approved=approval("read")), events=(quiet, quiet))
        [line] = land.not_green(task, self.state())
        self.assertTrue(line.startswith("the criteria were not read: the personas' read was started twice and nobody answered"))
        self.assertIn("no answer from the buyer, opus (the model was at capacity)", line)
        said = land.read_line(land.criteria_read_of(task), task.criteria, land.unanswered(task))
        self.assertIn("2 reads in a row, and none of the 2 personas asked answered", said)

    def test_a_partial_split_read_names_who_did_not_answer(self) -> None:
        read = self.read(asked=3, flagged=1, split=True, silent=[{"name": "the accountant, sol", "why": "the model was at capacity"}], ts=AT)
        said = land.read_line(read, found_of(approved=approval("owner", at=LATER)))
        self.assertIn("read by 2 of 3 personas asked, two model families (opus, sol); 1 of 2 criteria flagged; the two families split", said)
        self.assertIn("no answer from the accountant, sol (the model was at capacity); the owner approved them on 2026-11-18", said)

    def test_criteria_he_changed_after_the_read(self) -> None:
        plan = PLAN.replace("the word y.", "the word z.")
        read = self.read(ts=AT, digest="other")
        said = land.unread(read, found_of(plan, approval("owner", 2, plan, LATER, ({**approval("owner"), "digest": "other"},))))
        self.assertEqual(said, "- the criteria changed after the personas' read, by the owner's approval 2, and the change was not read")


class TheText(Proposal):
    """The whole text of a proposal: green or not first, then the checks and the decisions of the build."""

    def test_green_with_no_decision(self) -> None:
        text = land.pr_text(self.task(), "## Not done\n\nnone", self.state())
        self.assertEqual(text.splitlines()[0], land.GREEN)
        self.assertEqual(text.split("## Decisions of the build\n\n", 1)[1].splitlines()[0], "none")

    def test_not_green_puts_each_reason_first(self) -> None:
        lines = away([asked(1, "Where", ("a", "b"), "a", "A reads first.")], 1)
        out = land.pr_text(self.task(lines), "", self.state()).splitlines()
        self.assertEqual(out[:3], ["**Not green.**", "", out[2]])
        self.assertTrue(out[2].startswith("- choice 1 was taken without the owner (Where)"))

    def test_the_cause_of_a_bug_is_named_once_with_its_place(self) -> None:
        bug = {"ts": AT, "event": "investigation", "task": "t", "type": "fix", "call": "full", "line": "the total adds the refund as a payment", "where": "billing/invoice.py:total", "reproduced": True}
        checks = land.pr_text(self.task(record={"investigation": bug}), "", self.state()).split("## Checks", 1)[1].split("## Decisions of the build", 1)[0]
        self.assertEqual([line for line in checks.splitlines() if "the cause" in line], ["- the cause, as the investigation before the build found it: the total adds the refund as a payment (billing/invoice.py:total)"])

    def test_a_question_or_no_investigation_names_no_cause(self) -> None:
        question = {"ts": AT, "event": "investigation", "task": "t", "type": "question", "call": "answer", "line": "the export reads the totals of the night before"}
        for record in ({"investigation": question}, {"investigation": None}, {}):
            with self.subTest(record=record):
                self.assertNotIn("the cause", land.pr_text(self.task(record=record), "", self.state()))

    def test_built_names_the_files_and_opens_with_the_red_block(self) -> None:
        reasons = ["the owner did not approve the criteria"]
        built = land.built_text(self.task(), "t", "", reasons, "fix/t", None, ["x.txt", "tests/t.sh"], [{"item": "docs/backlog/a.md", "where": "x.txt", "title": "A defect"}])
        self.assertIn("The change touches 2 files: `x.txt`, `tests/t.sh`.", built)
        self.assertIn("> **One thing waits for the owner.**", built.split("## ", 1)[0])
        self.assertIn("- `docs/backlog/a.md`: A defect", built.split("## What was not built", 1)[1])
        self.assertNotIn("[!CAUTION]", land.built_text(self.task(), "t", "", [], "fix/t", None, ["x.txt"], []))


class Due(unittest.TestCase):
    """`due_of`: which review is due for the change as it is now, from the kept reviews."""

    FOLDER = "docs/backlog"

    def now(self, patch: str = "p1", contents: dict | None = None) -> dict:
        contents = contents if contents is not None else {"x.txt": {"base": "0" * 40, "tip": "1" * 40, "modes": ["000000", "100644"]}}
        return {"tip": "abc", "base": "def", "files": sorted(contents), "patch": patch, "contents": contents, "lines": 2}

    def due(self, reads: list[dict], now: dict | None = None, careful: tuple[str, ...] = (), tasks: int = 1) -> dict:
        return land.due_of(now or self.now(), reads, None, list(careful), tasks, False, self.FOLDER)

    def test_a_change_with_no_review_gets_one_read(self) -> None:
        said = self.due([])
        self.assertEqual((said["due"], said["floor"], said["round"]), ("review", "read", 1))

    def test_a_reviewed_change_needs_none(self) -> None:
        self.assertEqual(self.due([review(1)])["due"], "none")

    def test_a_change_after_the_review_gets_another(self) -> None:
        said = self.due([review(1)], self.now("p2"))
        self.assertEqual((said["due"], said["round"]), ("review", 2))

    def test_an_item_filed_in_the_backlog_after_the_review_is_covered(self) -> None:
        contents = {**self.now()["contents"], "docs/backlog/a-defect.md": {"base": "0" * 40, "tip": "2" * 40, "modes": ["000000", "100644"]}}
        self.assertEqual(self.due([review(1)], self.now("p2", contents))["due"], "none")
        elsewhere = {**self.now()["contents"], "docs/a-defect.md": contents["docs/backlog/a-defect.md"]}
        self.assertEqual(self.due([review(1)], self.now("p3", elsewhere))["due"], "review")

    def test_careful_after_one_read_asks_for_the_full_set(self) -> None:
        said = self.due([review(1)], careful=("the owner says so",))
        self.assertEqual((said["due"], said["floor"]), ("review", "full"))

    def test_after_two_rounds_the_request_waits_for_the_owner(self) -> None:
        said = self.due([review(1), review(2, patch="p2")], self.now("p2"), careful=("the owner says so",))
        self.assertEqual(said["due"], "owner")
        self.assertIn("it was one read, and this change gets the project's full set at the least", said["why"])

    def test_two_reviews_nobody_answered(self) -> None:
        said = self.due([review(1, answered_by=()), review(2, answered_by=())])
        self.assertEqual((said["due"], said["why"]), ("owner", "not reviewed: the review was started twice and no source answered"))

    def test_a_large_plan_gets_a_round(self) -> None:
        said = self.due([], tasks=4)
        self.assertEqual((said["floor"], said["why"]), ("round", "the plan has 4 tasks, more than three"))

    def test_a_must_fix_asks_for_a_round_after_its_fix(self) -> None:
        said = self.due([review(1, must_fix=1)], self.now("p2"))
        self.assertEqual((said["due"], said["floor"]), ("review", "round"))


if __name__ == "__main__":
    unittest.main()
