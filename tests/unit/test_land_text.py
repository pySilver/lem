"""What land.py decides from a task's records at a proposal, and how its lines say it,
each called in this process.

The records are the ones the real writers write: a decision's lines as `lem decisions`
appends them, folded by decisions.py's own `Task.decisions`; the criteria as
criteria.py's `parse` reads a plan and decisions.py's `Task.changes` adds the approvals
and the changes of a criterion; a review's entry as `lem land read` keeps it. The blocks
of tests/ keep one real proposal of each family, which reads the real `pr.md`, so that
the writer and the reader still meet.
"""

import json
import sys
import tempfile
import unittest
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import criteria, decisions, land

AT = "2026-11-18T10:00:00Z"
LATER = "2026-11-18T11:00:00Z"
PLAN = (
    "## Acceptance criteria\n\nSize: full, because the ticket names the word and the "
    "file.\n\n"
    "1. The file holds the word y.\n   - test: `sh tests/t.sh` in `tests/t.sh`\n"
    "2. The file has one line.\n   - no test: printf ends every line so.\n"
)


# A decision's lines, each in the form the command of decisions.py that writes it
# gives it.
STORY = {
    "case": "1. One step.\n2. Another.",
    "case_was": "derived",
    "cause": "the personas split",
}


def taken(
    number: int, what: str, chose: str, why: str, by: str, **more: object
) -> dict:
    """`lem decisions log`: a decision taken on the ladder."""
    return {
        "id": number,
        "at": AT,
        "kind": "taken",
        "what": what,
        "chose": chose,
        "why": why,
        "by": by,
        **more,
    }


def picked(
    number: int,
    what: str,
    options: tuple[str, ...],
    chose: str,
    why: str,
    by: str = "dialectic",
    **more: object,
) -> dict:
    """`lem decisions log --by dialectic|experts`: a pick past the personas, with its
    options and its story."""
    return taken(number, what, chose, why, by, options=list(options), **STORY, **more)


def breaker(number: int, cause: str = "criteria", **more: object) -> dict:
    """`lem decisions breaker`: the stop of the build, with its cause and
    its document."""
    return {
        "id": number,
        "at": AT,
        "kind": "breaker",
        "cause": cause,
        "what": "The note has no place that keeps criterion 1",
        "document": "breaker.md",
        "handoff": "handoff.md",
        **more,
    }


def ledger(directory: Path) -> "decisions.Task":
    """decisions.py's own record of a task in DIRECTORY, without the commands that
    find it."""
    record = decisions.Task.__new__(decisions.Task)
    record.slug, record.directory, record.file = (
        "t",
        directory,
        directory / "decisions.jsonl",
    )
    directory.mkdir(parents=True, exist_ok=True)
    return record


def folded(lines: list[dict]) -> list[dict]:
    """The decisions as `lem decisions list` gives them, from their lines."""
    with tempfile.TemporaryDirectory() as folder:
        record = ledger(Path(folder))
        record.file.write_text(
            "".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8"
        )
        # as `lem decisions list` gives them, which land.py reads
        return record.decisions()


def approval(
    by: str,
    number: int = 1,
    plan: str = PLAN,
    at: str = AT,
    history: tuple[dict, ...] = (),
) -> dict:
    """criteria.json as `lem criteria approve` writes it."""
    read = criteria.parse(plan, "approved.md")
    texts = [criterion["text"] for criterion in read["criteria"]]
    return {
        "task": "t",
        "number": number,
        "at": at,
        "by": by,
        "size": read["size"],
        "why": read["why"],
        "digest": criteria.text_digest(read["size"], texts),
        "criteria": [{"n": n, "text": text} for n, text in enumerate(texts, start=1)],
        "text": plan,
        "history": list(history),
    }


def change(number: int, how: str, criterion: int, why: str, **more: object) -> dict:
    """`lem decisions criterion`: one change of an approved criterion (`was`, `now`, and
    `decision` or `by`)."""
    return {
        "change": number,
        "at": AT,
        "kind": "criterion",
        "how": how,
        "criterion": criterion,
        "why": why,
        "approval": 1,
        **more,
    }


def found_of(
    plan: str = PLAN, approved: dict | None = None, lines: tuple[dict, ...] = ()
) -> dict:
    """What `lem criteria show` gives: the plan's criteria with the approvals and
    changes of the record."""
    read = criteria.parse(plan, "plan.md")
    digest = criteria.text_digest(
        read["size"], [criterion["text"] for criterion in read["criteria"]]
    )
    with tempfile.TemporaryDirectory() as folder:
        record = ledger(Path(folder))
        if approved:
            (Path(folder) / "criteria.json").write_text(
                json.dumps(approved), encoding="utf-8"
            )
        record.file.write_text(
            "".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8"
        )
        changes = record.changes()
    return {
        "task": "t",
        "plan": "plan.md",
        "small": read["size"] == "small",
        **read,
        "criteria_digest": digest,
        **{
            key: changes[key] for key in ("approved", "approvals", "changes", "history")
        },
    }


def review(
    round_: int,
    *,
    answered_by: tuple[str, ...] = ("codex",),
    kind: str = "read",
    patch: str = "p1",
    must_fix: int = 0,
    contents: dict | None = None,
    **more: object,
) -> dict:
    """One review's entry as `lem land read --record` keeps it."""
    return {
        "attempt": round_,
        "round": round_,
        "kind": kind,
        "ran": [],
        "left_out": [],
        "answered": list(answered_by),
        "silent": [],
        "bar": [],
        "must_fix": must_fix,
        "should": 0,
        "nit": 0,
        "outside": [],
        "careful": False,
        "careful_why": "the diff reaches no topic of the settings",
        "date": AT[:10],
        "verdict": "not reviewed"
        if not answered_by
        else "must-fix"
        if must_fix
        else "clean",
        "tip": "abc123456",
        "patch": patch,
        "contents": contents
        if contents is not None
        else {
            "x.txt": {"base": "0" * 40, "tip": "1" * 40, "modes": ["000000", "100644"]}
        },
        **more,
    }


CHECKS = {
    "commands": [{"command": "true", "exit": 0, "last": "", "output": "/tmp/out"}],
    "criteria": {
        "ok": True,
        "tests": [{"criterion": 1, "command": "sh tests/t.sh", "problem": None}],
        "without_a_test": [{"criterion": 2}],
    },
    "bar": {"lowered": [], "edited": []},
    "size": {"files": 1, "lines": 1},
}


class Proposal(unittest.TestCase):
    """A land.Task over a task directory of the test's own, with the records each
    case gives."""

    # each item the branch adds to the backlog folder, with its `worth` at the tip: a
    # fact of the branch, which only git shows
    ADDED: list[dict] = []

    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        from unittest import mock

        patched = mock.patch.object(
            land, "builder_filed", side_effect=lambda task: list(self.ADDED)
        )
        patched.start()
        self.addCleanup(patched.stop)

    def task(
        self,
        lines: Sequence[dict] = (),
        found: dict | None = None,
        kept: dict | None = None,
        record: dict | None = None,
        events: tuple[dict, ...] = (),
    ) -> "land.Task":
        task = land.Task.__new__(land.Task)
        task.slug, task.base, task.onto = "t", "main", "main"
        task.settings = {"checks": {"commands": ["true"]}}
        task.main, task.worktree = self.root, self.root / "no-worktree"
        task.directory = self.root / "state" / "tasks" / "t"
        task.directory.mkdir(parents=True, exist_ok=True)
        task.kept_file = task.directory / "landing.json"
        task.kept_file.write_text(
            json.dumps(
                {
                    "checks": CHECKS,
                    "polish": {"commits": 0, "filed": []},
                    "reads": [review(1)],
                    **(kept or {}),
                }
            ),
            encoding="utf-8",
        )
        task.recorded = folded(list(lines))
        task.criteria = found or found_of(approved=approval("owner"))
        task.plan_said, task.branch_gate = False, None
        task.record = {"slug": "t", "status": "landing", **(record or {})}
        (self.root / "state" / "events.jsonl").write_text(
            "".join(
                json.dumps({"ts": AT, "task": "t", **event}) + "\n" for event in events
            ),
            encoding="utf-8",
        )
        return task

    def state(self, **more: object) -> dict:
        return {
            "careful": [],
            "due": "none",
            "why": "round 1 reviewed this change and left no must-fix",
            "tasks": 1,
            "files": ["x.txt"],
            **more,
        }

    def reasons(self, *lines: dict, **given: object) -> list[str]:
        return land.not_green(
            self.task(list(lines), **cast("dict[str, Any]", given)), self.state()
        )


class PicksWithoutHim(Proposal):
    """The ladder decides every choice of the build: a pick past the personas is not
    green, one line each, and one the gate or the personas settled is no cause. One
    expert alone is named as one."""

    WHERE = picked(
        1,
        "Where the word goes",
        ("the first line", "the last line"),
        "the first line",
        "A reader sees it at once.",
    )

    def test_a_pick_of_the_dialectic_is_not_green_and_keeps_its_story(self) -> None:
        [line] = self.reasons(self.WHERE)
        self.assertEqual(
            line,
            (
                "decision 1 was taken without the owner (Where the word goes): "
                '"the first line", by the dialectic'
            ),
        )
        said = land.decided(folded([self.WHERE])[0])
        self.assertIn("by the dialectic. A reader sees it at once.", said)

    def test_the_gate_and_the_personas_are_green(self) -> None:
        votes = [
            ["the merchant, opus", "the first line"],
            ["the accountant, sol", "the first line"],
        ]
        lines = [
            taken(1, "Where", "the first line", "a ruling says so", "gate"),
            taken(
                2,
                "Which",
                "the first line",
                "both read it first",
                "personas",
                votes=votes,
            ),
        ]
        self.assertEqual(self.reasons(*lines), [])

    def test_one_expert_alone_is_named_as_one(self) -> None:
        lines = [
            taken(
                1,
                "The word's case",
                "upper case",
                "Fable: the header is in upper case.",
                "experts",
                advisers=["fable"],
                options=["lower case", "upper case"],
            )
        ]
        [line] = self.reasons(*lines)
        self.assertTrue(
            line.startswith("decision 1 was taken without the owner (The word's case)")
        )
        self.assertTrue(line.endswith(", by one expert"))
        self.assertIn(
            "by one expert. Fable: the header is in upper case.",
            land.decided(folded(lines)[0]),
        )

    def test_two_experts_are_named_as_two(self) -> None:
        lines = [
            picked(
                1,
                "Where",
                ("a", "b"),
                "b",
                "Both read b first.",
                "experts",
                advisers=["fable", "astra"],
            )
        ]
        [line] = self.reasons(*lines)
        self.assertTrue(line.endswith(", by the experts"), line)


class TheBreaker(Proposal):
    """A breaker is a line of the pull request with its cause and how it ended; the
    owner's help on it is no cause of not green, and neither is a criterion change his
    help led to."""

    def test_his_help_is_no_cause_and_the_stop_is_a_line(self) -> None:
        lines = [
            breaker(1, "irreversible", irreversible="person"),
            taken(
                2,
                "Email the merchants",
                "send nothing",
                "They read the export anyway.",
                "owner",
                breaker=1,
                words="no email",
            ),
        ]
        self.assertEqual(self.reasons(*lines), [])
        text = land.pr_text(self.task(lines), "", self.state())
        decided = text.split("## Decisions of the build\n\n", 1)[1]
        self.assertTrue(
            decided.startswith(
                "- the build stopped at breaker 1, 2026-11-18 10:00 UTC: "
                "The note has no place that keeps criterion 1. Why it stopped: "
                "the next step could not be reversed by a later no (person); "
                "the owner helped, decision 2."
            )
        )
        self.assertIn(
            (
                '- Email the merchants: "send nothing", by the owner, his help on '
                'breaker 1. They read the export anyway. The owner\'s words: "no email"'
            ),
            decided,
        )

    def test_a_breaker_that_waits_says_so(self) -> None:
        self.assertTrue(
            land.breaker_lines(self.task([breaker(1)]))[0].endswith(
                "no option of the ladder kept the approved criteria; "
                "it waits for the owner."
            )
        )

    def test_a_criterion_his_help_changed_is_his(self) -> None:
        lines = [
            breaker(1),
            taken(
                2,
                "The one-line rule",
                "no such rule",
                "a second line holds the date",
                "owner",
                breaker=1,
            ),
        ]
        removed = change(
            1,
            "removed",
            2,
            "A second line holds the date now.",
            was="The file has one line.",
            decision=2,
        )
        plan = PLAN.replace(
            "2. The file has one line.\n   - no test: printf ends every line so.\n", ""
        )
        task = self.task(
            lines, found=found_of(plan, approval("owner"), (*lines, removed))
        )
        self.assertEqual(land.not_green(task, self.state()), [])
        self.assertIn(
            (
                "after decision 2 (The one-line rule), the owner's help on breaker 1, "
                'which took "no such rule"'
            ),
            land.change_line(task, cast("dict", task.criteria)["history"][0]),
        )


class CriteriaThatChanged(Proposal):
    """A criterion the build changed, added or removed is not green, each with its line;
    a change that an approval of his took over is his, and no cause."""

    def test_a_changed_criterion_by_the_personas(self) -> None:
        moved = change(
            1,
            "changed",
            1,
            "y is taken by another file.",
            was="The file holds the word y.",
            now="The file holds the word the owner asked for.",
            by="personas",
            said="Both personas picked x.",
        )
        plan = PLAN.replace("the word y.", "the word the owner asked for.")
        task = self.task(found=found_of(plan, approval("owner"), (moved,)))
        [reason] = land.not_green(task, self.state())
        self.assertTrue(
            reason.startswith("criterion 1 changed during the build: y is taken")
        )
        line = land.change_line(task, cast("dict", task.criteria)["history"][0])
        self.assertIn(
            (
                'was "The file holds the word y.", now "The file holds the '
                'word the owner asked for."'
            ),
            line,
        )
        self.assertTrue(line.endswith("By the personas: Both personas picked x."))

    def test_one_removed_after_a_pick_and_one_added_by_the_lead(self) -> None:
        lines = [
            picked(
                1,
                "The one-line rule",
                ("keep the rule", "no such rule"),
                "no such rule",
                "A reader counts on the date.",
            )
        ]
        removed = change(
            1,
            "removed",
            2,
            "A second line holds the date now.",
            was="The file has one line.",
            decision=1,
        )
        added = change(
            2,
            "added",
            2,
            "The importer reads whole lines only.",
            now="The file ends with a line break.",
            by="lead",
        )
        plan = PLAN.replace(
            "2. The file has one line.", "2. The file ends with a line break."
        )
        task = self.task(
            lines, found=found_of(plan, approval("owner"), (*lines, removed, added))
        )
        removed_line, added_line, pick = land.not_green(task, self.state())
        self.assertTrue(pick.startswith("decision 1 was taken without the owner"))
        self.assertTrue(
            removed_line.startswith("criterion 2 was removed during the build")
        )
        self.assertIn(
            (
                "after decision 1 (The one-line rule), where the "
                'dialectic took "no such rule"'
            ),
            removed_line,
        )
        self.assertTrue(
            added_line.startswith(
                "criterion 2 was added during the build: The importer reads"
            )
        )
        self.assertTrue(
            land.change_line(task, cast("dict", task.criteria)["history"][1]).endswith(
                "By the lead."
            )
        )

    def test_a_change_his_later_approval_took_over_is_his(self) -> None:
        moved = change(
            1,
            "changed",
            1,
            "y is taken.",
            was="The file holds the word y.",
            now="The file holds the word z.",
            by="lead",
        )
        plan = PLAN.replace("the word y.", "the word z.")
        first = {
            key: value
            for key, value in approval("owner").items()
            if key not in ("history", "task", "text")
        }
        task = self.task(
            found=found_of(plan, approval("owner", 2, plan, LATER, (first,)), (moved,))
        )
        self.assertEqual(land.not_green(task, self.state()), [])
        self.assertTrue(
            land.change_line(task, cast("dict", task.criteria)["history"][0]).endswith(
                "Approved by the owner afterwards (approval 2)."
            )
        )

    def test_criteria_approved_without_him(self) -> None:
        [line] = land.not_green(
            self.task(found=found_of(approved=approval("alone"))), self.state()
        )
        self.assertTrue(line.startswith("the owner did not approve the criteria"))


class TheRead(Proposal):
    """The personas' read of the criteria, from its event, in the pull
    request's checks."""

    def read(self, **more: object) -> dict:
        found = found_of()
        return {
            "event": "criteria.read",
            "by": "lem",
            "asked": 2,
            "answered": 2,
            "families": ["opus", "sol"],
            "silent": [],
            "criteria": 2,
            "flagged": 0,
            "split": False,
            "digest": found["criteria_digest"],
            **more,
        }

    def test_two_reads_nobody_answered_are_not_green(self) -> None:
        quiet = self.read(
            answered=0,
            families=[],
            silent=[{"name": "the buyer, opus", "why": "the model was at capacity"}],
        )
        task = self.task(
            found=found_of(approved=approval("read")), events=(quiet, quiet)
        )
        [line] = land.not_green(task, self.state())
        self.assertTrue(
            line.startswith(
                "the criteria were not read: the personas' read was started "
                "twice and nobody answered"
            )
        )
        self.assertIn(
            "no answer from the buyer, opus (the model was at capacity)", line
        )
        said = land.read_line(
            land.criteria_read_of(task),
            cast("dict", task.criteria),
            land.unanswered(task),
        )
        self.assertIn(
            "2 reads in a row, and none of the 2 personas asked answered", said
        )

    def test_a_partial_split_read_names_who_did_not_answer(self) -> None:
        read = self.read(
            asked=3,
            flagged=1,
            split=True,
            silent=[
                {"name": "the accountant, sol", "why": "the model was at capacity"}
            ],
            ts=AT,
        )
        said = land.read_line(read, found_of(approved=approval("owner", at=LATER)))
        self.assertIn(
            (
                "read by 2 of 3 personas asked, two model families (opus, sol); "
                "1 of 2 criteria flagged; the two families split"
            ),
            said,
        )
        self.assertIn(
            (
                "no answer from the accountant, sol (the model was at capacity); "
                "the owner approved them on 2026-11-18"
            ),
            said,
        )

    def test_criteria_he_changed_after_the_read(self) -> None:
        plan = PLAN.replace("the word y.", "the word z.")
        read = self.read(ts=AT, digest="other")
        said = land.unread(
            read,
            found_of(
                plan,
                approval(
                    "owner", 2, plan, LATER, ({**approval("owner"), "digest": "other"},)
                ),
            ),
        )
        self.assertEqual(
            said,
            (
                "- the criteria changed after the personas' read, by the owner's "
                "approval 2, and the change was not read"
            ),
        )

    def test_his_yes_after_a_change_from_his_note(self) -> None:
        """`unread` names his approval of the text a change from his note wrote
        (`lem criteria change`), which the personas did not read."""
        read = self.read(ts=AT)
        changed = PLAN.replace("the word y.", "the word y and its date.")
        found = found_of(changed, approval("owner", 1, changed, LATER))
        self.assertEqual(
            land.unread(read, found),
            (
                "- the criteria changed after the personas' read, by the owner's "
                "approval 1, and the change was not read"
            ),
        )


class ChangesFromHisNotes(Proposal):
    """The pull request counts each change of the criteria from his notes after the
    personas' read (logged decision 7): the held blocks `lem criteria change` writes
    last, whatever text he approved at the end."""

    READ = {
        "event": "criteria.read",
        "by": "lem",
        "asked": 2,
        "answered": 2,
        "families": ["opus"],
        "silent": [],
        "criteria": 2,
        "flagged": 0,
        "split": False,
        "ts": AT,
    }

    @staticmethod
    def changed(at: str) -> list[dict]:
        """One change, as `lem criteria change` logs it: its event, then its
        held block."""
        return [
            {"event": "criteria.changed", "ts": at, "words": "the note", "pairs": []},
            {
                "event": "task.state",
                "ts": at,
                "status": "held",
                "text": land.CHANGED_WAIT,
                "lines": [],
            },
        ]

    def test_a_change_and_its_way_back_still_show(self) -> None:
        """A, B, A: the text he approved is the one the personas read, so `unread` says
        nothing, and the line still counts two changes."""
        found = found_of(approved=approval("owner", at=LATER))
        read = {**self.READ, "digest": found["criteria_digest"]}
        events = [
            {
                "event": "task.state",
                "ts": AT,
                "status": "held",
                "text": "the interview waits for the owner",
                "lines": [],
            },
            read,
            *self.changed("2026-11-18T10:10:00Z"),
            *self.changed("2026-11-18T10:20:00Z"),
            {"event": "criteria.approved", "ts": LATER, "by": "owner", "number": 1},
        ]
        self.assertEqual(land.changed_after_read(events), 2)
        self.assertIsNone(land.unread(read, found))
        said = land.read_line(
            read,
            found,
            waited=land.criteria_waited(events),
            changed=land.changed_after_read(events),
        )
        self.assertIn(
            (
                "; nobody confused; the criteria changed 2 times after the personas' "
                "read, from the owner's notes; the criteria waited for the owner's yes"
            ),
            said,
        )

    def test_a_retry_after_a_stop_counts_one_change(self) -> None:
        """A stop between the change's event and its held block, then the run that ends
        it: two events, one block, one change."""
        found = found_of(approved=approval("owner", at=LATER))
        read = {**self.READ, "digest": found["criteria_digest"]}
        first, _ = self.changed("2026-11-18T10:10:00Z")
        events = [read, first, *self.changed("2026-11-18T10:12:00Z")]
        self.assertEqual(land.changed_after_read(events), 1)
        self.assertIn(
            (
                "the criteria changed once after the personas' read, "
                "from the owner's notes"
            ),
            land.read_line(read, found, changed=1),
        )

    def test_a_change_before_the_read_and_no_read(self) -> None:
        events = [*self.changed(AT), {**self.READ, "ts": LATER}]
        self.assertEqual(land.changed_after_read(events), 0)
        self.assertEqual(land.changed_after_read(self.changed(AT)), 0)
        found = found_of(approved=approval("owner", at=LATER))
        self.assertNotIn(
            "changed",
            land.read_line({**self.READ, "digest": found["criteria_digest"]}, found),
        )

    def test_the_text_of_a_proposal_reads_the_changes_from_the_log(self) -> None:
        found = found_of(approved=approval("owner", at=LATER))
        task = self.task(
            found=found,
            events=(
                {**self.READ, "digest": found["criteria_digest"]},
                *self.changed("2026-11-18T10:10:00Z"),
            ),
        )
        self.assertIn(
            (
                "the criteria changed once after the personas' read, "
                "from the owner's notes"
            ),
            land.pr_text(task, "", self.state()),
        )


class TheWait(Proposal):
    """The criteria that waited for the owner's yes, and the approval that ended the
    wait, in the line of the read: the events as `lem project state` and
    `lem criteria approve` log them."""

    WAITED = "2026-11-18T09:30:00Z"
    YES = "2026-11-18T10:05:00Z"
    AGAIN = "2026-11-19T08:00:00Z"
    READ = {
        "event": "criteria.read",
        "by": "lead",
        "asked": 2,
        "answered": 2,
        "families": ["opus", "sol"],
        "silent": [],
        "criteria": 2,
        "flagged": 0,
        "split": False,
        "ts": AT,
    }

    def held(
        self,
        text: str = "the criteria wait for the owner: a request someone else wrote",
        at: str = WAITED,
    ) -> dict:
        return {
            "event": "task.state",
            "ts": at,
            "status": "held",
            "text": text,
            "lines": [],
        }

    @staticmethod
    def approved(by: str, number: int, at: str) -> dict:
        return {"event": "criteria.approved", "ts": at, "by": by, "number": number}

    def line(self, events: tuple[dict, ...], found: dict) -> str:
        read = {**self.READ, "digest": found["criteria_digest"]}
        return land.read_line(read, found, waited=land.criteria_waited([read, *events]))

    def test_a_wait_and_the_owners_yes(self) -> None:
        said = self.line(
            (self.held(), self.approved("owner", 1, self.YES)),
            found_of(approved=approval("owner", at=self.YES)),
        )
        self.assertTrue(
            said.endswith(
                "; nobody confused; the criteria waited for the owner's yes from "
                "2026-11-18 09:30 UTC, and the owner gave it on 2026-11-18 10:05 UTC"
            ),
            said,
        )

    def test_a_later_approval_with_no_wait_leaves_the_first_as_the_end(self) -> None:
        first = {
            key: value
            for key, value in approval("owner", at=self.YES).items()
            if key not in ("history", "task", "text")
        }
        events = (
            self.held(),
            self.approved("owner", 1, self.YES),
            {
                "event": "task.state",
                "ts": LATER,
                "status": "building",
                "text": "lead: builder",
                "lines": [],
            },
            self.approved("owner", 2, self.AGAIN),
        )
        said = self.line(
            events,
            found_of(approved=approval("owner", 2, at=self.AGAIN, history=(first,))),
        )
        self.assertTrue(
            said.endswith(
                "and the owner gave it on 2026-11-18 10:05 UTC; the owner approved "
                "them again on 2026-11-19"
            ),
            said,
        )

    def test_a_wait_that_ended_without_him_and_his_later_approval(self) -> None:
        first = {
            key: value
            for key, value in approval("alone", at=self.YES).items()
            if key not in ("history", "task", "text")
        }
        events = (
            self.held(),
            self.approved("alone", 1, self.YES),
            self.approved("owner", 2, self.AGAIN),
        )
        said = self.line(
            events,
            found_of(approved=approval("owner", 2, at=self.AGAIN, history=(first,))),
        )
        self.assertTrue(
            said.endswith(
                "the criteria waited for the owner's yes from 2026-11-18 09:30 UTC, "
                "and the wait ended without the owner: approved on 2026-11-18 10:05 "
                "UTC while the task ran without the owner; "
                "the owner approved them on 2026-11-19"
            ),
            said,
        )
        self.assertNotIn("gave it", said)

    def test_an_approval_with_no_wait_keeps_the_line_of_today(self) -> None:
        events = (
            self.held("the interview waits for the owner"),
            self.approved("owner", 1, self.YES),
        )
        said = self.line(events, found_of(approved=approval("owner", at=self.YES)))
        self.assertTrue(
            said.endswith("; nobody confused; the owner approved them on 2026-11-18"),
            said,
        )
        self.assertNotIn("waited", said)

    def test_the_fast_tracks_grown_change_is_no_wait(self) -> None:
        events = (
            self.held(
                "the criteria wait for the owner: the small change is a full change"
            ),
            self.approved("owner", 1, self.YES),
        )
        self.assertIsNone(land.criteria_waited(list(events)))

    def test_the_newest_wait_counts_and_an_approval_before_it_ends_nothing(
        self,
    ) -> None:
        events = [self.approved("owner", 1, AT), self.held(at=LATER)]
        self.assertIsNone(land.criteria_waited(events))
        events.append(self.approved("alone", 2, self.AGAIN))
        self.assertEqual(
            land.criteria_waited(events), {"from": LATER, "end": events[-1]}
        )

    def test_the_text_of_a_proposal_reads_the_wait_from_the_log(self) -> None:
        found = found_of(approved=approval("owner", at=self.YES))
        task = self.task(
            found=found,
            events=(
                {**self.READ, "digest": found["criteria_digest"]},
                self.held(),
                self.approved("owner", 1, self.YES),
            ),
        )
        text = land.pr_text(task, "", self.state())
        self.assertIn(
            (
                "the criteria waited for the owner's yes from 2026-11-18 09:30 UTC, "
                "and the owner gave it on 2026-11-18 10:05 UTC"
            ),
            text,
        )


class TheText(Proposal):
    """The whole text of a proposal: green or not first, then the checks and the
    decisions of the build."""

    def test_green_with_no_decision(self) -> None:
        text = land.pr_text(self.task(), "## Not done\n\nnone", self.state())
        self.assertEqual(text.splitlines()[0], land.GREEN)
        self.assertEqual(
            text.split("## Decisions of the build\n\n", 1)[1].splitlines()[0], "none"
        )

    def test_not_green_puts_each_reason_first(self) -> None:
        lines = [picked(1, "Where", ("a", "b"), "a", "A reads first.")]
        out = land.pr_text(self.task(lines), "", self.state()).splitlines()
        self.assertEqual(out[:3], ["**Not green.**", "", out[2]])
        self.assertTrue(
            out[2].startswith("- decision 1 was taken without the owner (Where)")
        )

    def test_the_cause_of_a_bug_is_named_once_with_its_place(self) -> None:
        bug = {
            "ts": AT,
            "event": "investigation",
            "task": "t",
            "type": "fix",
            "call": "full",
            "line": "the total adds the refund as a payment",
            "where": "billing/invoice.py:total",
            "reproduced": True,
        }
        checks = (
            land.pr_text(self.task(record={"investigation": bug}), "", self.state())
            .split("## Checks", 1)[1]
            .split("## Decisions of the build", 1)[0]
        )
        self.assertEqual(
            [line for line in checks.splitlines() if "the cause" in line],
            [
                (
                    "- the cause, as the investigation before the build found it: "
                    "the total adds the refund as a payment (billing/invoice.py:total)"
                )
            ],
        )

    def test_a_question_or_no_investigation_names_no_cause(self) -> None:
        question = {
            "ts": AT,
            "event": "investigation",
            "task": "t",
            "type": "question",
            "call": "answer",
            "line": "the export reads the totals of the night before",
        }
        for record in ({"investigation": question}, {"investigation": None}, {}):
            with self.subTest(record=record):
                self.assertNotIn(
                    "the cause",
                    land.pr_text(self.task(record=record), "", self.state()),
                )


class StandIns(Proposal):
    """Each seat that stood in for another is one line of the pull request's checks, a
    fact and no reason of not green, on either track; one that gave an error itself says
    so on its line."""

    STOOD = {
        "event": "seat.stand-in",
        "seat": "reviewer",
        "failed": "codex/gpt-6.2-sol:high",
        "took": "claude/opus:high",
        "error": "tokens",
    }
    LINE = (
        "- the reviewer was `claude/opus:high` in place of `codex/gpt-6.2-sol:high`: "
        "Codex had no tokens"
    )

    def checks(self, text: str) -> list[str]:
        part = text.split("## Checks", 1)[1].split("\n## ", 1)[0]
        return [line for line in part.splitlines() if " in place of " in line]

    def test_one_stand_in_is_its_line_and_no_reason_of_not_green(self) -> None:
        # criterion 4, word for word
        task = self.task(events=(self.STOOD,))
        self.assertEqual(self.checks(land.pr_text(task, "", self.state())), [self.LINE])
        self.assertEqual(land.not_green(task, self.state()), [])
        self.assertEqual(
            land.pr_text(task, "", self.state()).splitlines()[0], land.GREEN
        )

    def test_every_stand_in_is_listed_also_one_a_block_of_another_cause_followed(
        self,
    ) -> None:
        merger = {
            "event": "seat.stand-in",
            "seat": "merger",
            "failed": "codex/gpt-6.2-sol:high",
            "took": "claude/opus:high",
            "error": "missing",
        }
        blocked = {
            "event": "seat.blocked",
            "seat": "reviewer",
            "failed": "codex/gpt-6.2-sol:high",
            "error": "tokens",
        }
        task = self.task(
            events=(
                self.STOOD,
                blocked,
                {"event": "seat.again", "seat": "reviewer"},
                merger,
            )
        )
        self.assertEqual(
            self.checks(land.pr_text(task, "", self.state())),
            [
                self.LINE,
                (
                    "- the merge agent was `claude/opus:high` in place of "
                    "`codex/gpt-6.2-sol:high`: Codex is not on this Mac"
                ),
            ],
        )

    def test_a_stand_in_whose_own_start_failed_says_so(self) -> None:
        stood = {
            **self.STOOD,
            "failed": "claude/opus:high",
            "took": "codex/gpt-6.2-sol:high",
            "error": "model",
        }
        failed = {
            "event": "seat.blocked",
            "seat": "reviewer",
            "failed": "codex/gpt-6.2-sol:high",
            "error": "missing",
        }
        task = self.task(events=(stood, failed))
        self.assertEqual(
            self.checks(land.pr_text(task, "", self.state())),
            [
                (
                    "- the reviewer was to be `codex/gpt-6.2-sol:high` in place of "
                    "`claude/opus:high`: Claude Code did not know the model; "
                    "then Codex gave an error too: Codex is not on this Mac"
                )
            ],
        )
        # a block after the owner's go on is of the named seat, and no failure of
        # the stand-in
        again = self.task(
            events=(stood, {"event": "seat.again", "seat": "reviewer"}, failed)
        )
        self.assertEqual(
            land.stand_ins_of(land.events_of(again))[0]["failed_too"], None
        )

    def test_the_fast_track_lists_it_too(self) -> None:
        from unittest import mock

        small = (
            "## Acceptance criteria\n\nSize: small, because one word changes.\n\n"
            "1. The file holds the word y.\n   - test: "
            "`sh tests/t.sh` in `tests/t.sh`\n"
        )
        task = self.task(
            found=found_of(small, approved=approval("owner", plan=small)),
            events=(self.STOOD,),
        )
        with mock.patch.object(land, "builder_filed", return_value=[]):
            self.assertEqual(
                self.checks(land.pr_text(task, "none\n", self.state())), [self.LINE]
            )


class TheCriteriasCheck(Proposal):
    """The line of the check of the criteria among the pull request's checks: run by the
    checks, or taken from the polish pass at its commit and not run again."""

    @staticmethod
    def line(text: str) -> list[str]:
        return [
            row
            for row in text.splitlines()
            if row.startswith("- the tests of the criteria")
        ]

    def test_tests_the_checks_ran_pass_on_the_branch_and_fail_on_the_base_commit(
        self,
    ) -> None:
        text = land.pr_text(self.task(), "", self.state())
        self.assertEqual(
            self.line(text),
            [
                (
                    "- the tests of the criteria: 1 pass on the branch and fail on the "
                    "base commit; 1 criterion has no test"
                )
            ],
        )

    def test_tests_taken_from_the_polish_pass_name_it_and_its_commit(self) -> None:
        taken = {
            **CHECKS,
            "criteria": {
                **CHECKS["criteria"],
                "taken": {"from": "polish", "at": "a1b2c3d4e5f6a7b8"},
            },
        }
        text = land.pr_text(self.task(kept={"checks": taken}), "", self.state())
        self.assertEqual(
            self.line(text),
            [
                (
                    "- the tests of the criteria: 1 pass on the branch and fail on the "
                    "base commit, taken from the polish pass at a1b2c3d4e, and not run "
                    "again; 1 criterion has no test"
                )
            ],
        )
        # each test still says what the pass's run gave it
        self.assertIn(
            "   - `sh tests/t.sh`: passes on the branch, fails on the base commit",
            text.splitlines(),
        )


class WithoutHim(Proposal):
    """The line of the time a task ran without the owner, under green or not green, on
    both tracks."""

    SMALL = (
        "## Acceptance criteria\n\nSize: small, because one word changes.\n\n"
        "1. The file holds the word y.\n   - test: `sh tests/t.sh` in `tests/t.sh`\n"
    )
    AWAY = [
        {
            "from": AT,
            "to": LATER,
            "started": {"by": "owner", "words": "/lem im-away"},
            "ended": {"by": "owner", "words": "/lem im-back"},
        }
    ]
    LINE = (
        "It ran without the owner from 2026-11-18 10:00 UTC (the owner: "
        '"/lem im-away") to 2026-11-18 11:00 UTC (the owner: "/lem im-back").'
    )

    def test_each_track_names_the_time_without_him(self) -> None:
        for name, plan in (("standard", PLAN), ("fast", self.SMALL)):
            with self.subTest(track=name):
                found = found_of(plan, approved=approval("owner", plan=plan))
                out = land.pr_text(
                    self.task(found=found, record={"without_owner": self.AWAY}),
                    "",
                    self.state(),
                ).splitlines()
                self.assertEqual(out[:4], [land.GREEN, "", self.LINE, ""])

    def test_a_task_that_ran_with_him_has_no_such_line(self) -> None:
        found = found_of(self.SMALL, approved=approval("owner", plan=self.SMALL))
        self.assertNotIn(
            "ran without the owner",
            land.pr_text(self.task(found=found), "", self.state()),
        )


class TheDocuments(Proposal):
    """The pull request's text in the forms of `prompts/writing.md`: an important
    decision's story folded under it, a label cut at its colon, and no link to a picture
    the forge does not hold."""

    CHART = (
        'flowchart TD\n  A["The real run ends"] --> B{"GitHub?"}\n'
        '  B -->|"no"| C["Waits for the merge"]'
    )
    LONG = (
        "B. One held line for each criterion: 'Criterion 1: held: the answer came 1 "
        "min 9 s after the checks started', the times under each line"
    )

    def important(self) -> list[dict]:
        pick = picked(
            8,
            "How the report of the real run shows criteria 1 and 3",
            ("A. Times only: a table of times", self.LONG),
            self.LONG,
            "Two lines to read.",
            chart=self.CHART,
        )
        return [
            pick,
            taken(
                2,
                "how a run of the checks is stopped",
                (
                    "by the script, lem land checks SLUG --stop, "
                    "with the process id its lock file holds"
                ),
                "a new session does not hold the first one's task",
                "lead",
                undo="name the tool's own stop again",
            ),
        ]

    def test_a_label_ends_at_its_colon_and_never_inside_a_quote(self) -> None:
        self.assertEqual(
            land.label("the Fable expert's picks: c4 as written"),
            "the Fable expert's picks",
        )
        self.assertEqual(
            land.label(
                "it ends as refused, with the say 'the checks refused: "
                "a builder repairs it'"
            ),
            (
                "it ends as refused, with the say 'the checks refused: "
                "a builder repairs it'"
            ),
        )

    def test_the_pull_request_links_no_picture_and_folds_an_important_story(
        self,
    ) -> None:
        notes = "## Worth a look\n\n![The file after](media/after.png)\n"
        plain = land.pr_text(self.task(), notes, self.state())
        self.assertNotIn("media/", plain)
        self.assertIn("The file after (a picture on the task's board)", plain)
        self.assertNotIn("<details>", plain)
        folded = land.pr_text(self.task(self.important()), "", self.state())
        self.assertEqual(folded.count("<details>"), 1)
        self.assertIn(f"```mermaid\n{self.CHART}\n```\n\n</details>", folded)


class SeenOutside(Proposal):
    """What the pull request's text says of the defects a review saw outside the change,
    on both tracks: each item the branch adds under the heading its `worth` at the tip
    gives, a line under `## Seen, not filed` for a cheap one nobody fixed, and a cheap
    one that a fix line names by its number under `## Fixed on the way`
    (backlog-filing-judged, criteria 2 and 6; backlog-refuted-items-and-jev,
    criterion 1)."""

    SMALL = (
        "## Acceptance criteria\n\nSize: small, because one word changes.\n\n"
        "1. The file holds the word y.\n   - test: `sh tests/t.sh` in `tests/t.sh`\n"
    )
    NOTES = (
        "## Decisions\n\nnone\n\n## Left open\n\nnone\n\n## Worth a look\n\nnone\n\n"
        "## Filed in the backlog\n\nnone\n\n## Not done\n\nnone\n"
    )
    GUARD = {
        "where": "tests/unit/test_board_model.py",
        "title": "two test classes come after the main guard",
        "what": "the file runs them after its main guard.",
        "bar": "under",
        "why": "only a reader of the code meets it",
        "number": "r1.1",
        "item": "docs/backlog/two-test-classes-come-after-the-main-guard.md",
    }
    SUPPRESSION = {
        "where": "app.py:run",
        "title": "an outdated lint suppression",
        "what": "the mark names a rule the linter no longer has.",
        "bar": "cheap",
        "why": "a comment of the code, no behavior",
        "number": "r1.2",
    }
    FILED = {
        "where": "app.py:load",
        "title": "load crashes on an empty file",
        "what": "load of an empty file raises KeyError.",
        "bar": "over",
        "number": "r1.3",
        "item": "docs/backlog/load-crashes-on-an-empty-file.md",
    }
    # the two items as the tip holds them, in the order git lists them, and the
    # builder's one by hand
    ADDED = [
        {
            "item": "docs/backlog/load-crashes-on-an-empty-file.md",
            "title": "load crashes on an empty file",
            "worth": "later",
        },
        {
            "item": "docs/backlog/two-test-classes-come-after-the-main-guard.md",
            "title": "two test classes come after the main guard",
            "worth": "no",
        },
    ]

    def text(self, plan: str, notes: str) -> list[str]:
        found = found_of(plan, approved=approval("owner", plan=plan))
        task = self.task(
            found=found,
            kept={
                "reads": [
                    review(
                        1,
                        must_fix=0,
                        outside=[self.GUARD, self.SUPPRESSION, self.FILED],
                    )
                ]
            },
        )
        return land.pr_text(task, notes, self.state()).splitlines()

    def test_an_item_under_the_bar_is_filed_as_not_worth_it_and_a_cheap_one_nobody_fixed_is_a_line(
        self,
    ) -> None:
        for name, plan, notes in (
            ("standard", PLAN, self.NOTES),
            ("fast", self.SMALL, "none\n"),
        ):
            with self.subTest(track=name):
                out = self.text(plan, notes)
                seen = out.index("## Seen, not filed")
                self.assertEqual(
                    out[seen + 2],
                    (
                        "- `app.py:run`: an outdated lint suppression; cheap: "
                        "a comment of the code, no behavior"
                    ),
                )
                self.assertIn(out[seen + 3 : seen + 4], ([], [""]))
                filed = out.index("## Filed in the backlog")
                self.assertEqual(
                    out[filed + 2 : filed + 4],
                    [
                        (
                            "- `docs/backlog/load-crashes-on-an-empty-file.md`: "
                            "load crashes on an empty file"
                        ),
                        "",
                    ],
                )
                not_worth = out.index("## Filed as not worth it")
                self.assertEqual(
                    out[not_worth + 2],
                    (
                        "- "
                        "`docs/backlog/two-test-classes-come-after-the-main-guard.md`: "
                        "two test classes come after the main guard"
                    ),
                )
                self.assertLess(filed, not_worth)
                self.assertLess(not_worth, seen)
                self.assertNotIn("## Fixed on the way", out)
                line = next(
                    line for line in out if line.startswith("- the review, round 1")
                )
                self.assertTrue(
                    line.endswith(
                        "; it saw 3 defects outside the change, filed as "
                        "`docs/backlog/two-test-classes-come-after-the-main-guard.md`, "
                        "`docs/backlog/load-crashes-on-an-empty-file.md`; "
                        "1 seen, not filed"
                    ),
                    line,
                )

    def test_the_heading_of_an_item_is_its_worth_at_the_tip_and_a_notes_line_that_names_it_is_not_written_twice(
        self,
    ) -> None:
        # the owner made the review's item `worth: no`, and the polish pass's line names
        # it under the other heading
        self.ADDED = [
            {**self.ADDED[0], "worth": "no"},
            self.ADDED[1],
            {
                "item": "docs/backlog/a-css-rule-matches-nothing.md",
                "title": "a CSS rule matches nothing",
                "worth": "no",
            },
        ]
        notes = self.NOTES.replace(
            "## Filed in the backlog\n\nnone",
            (
                "## Filed in the backlog\n\n- "
                "`docs/backlog/a-css-rule-matches-nothing.md`, worth: no, "
                "filed by the polish pass"
            ),
        )
        out = self.text(PLAN, notes)
        filed, not_worth = (
            out.index("## Filed in the backlog"),
            out.index("## Filed as not worth it"),
        )
        self.assertEqual(out[filed + 2 : filed + 4], ["none", ""])
        self.assertEqual(
            out[not_worth + 2 : not_worth + 5],
            [
                (
                    "- `docs/backlog/load-crashes-on-an-empty-file.md`: "
                    "load crashes on an empty file"
                ),
                (
                    "- `docs/backlog/two-test-classes-come-after-the-main-guard.md`: "
                    "two test classes come after the main guard"
                ),
                (
                    "- `docs/backlog/a-css-rule-matches-nothing.md`, worth: "
                    "no, filed by the polish pass"
                ),
            ],
        )
        self.assertEqual(sum("a-css-rule-matches-nothing" in line for line in out), 1)

    def test_a_fix_line_that_names_the_cheap_entry_takes_its_line_out(self) -> None:
        fix = (
            "## Fixed on the way\n\n- `app.py` (abc1234): r1.2, the suppression named "
            "a rule the linter no longer has\n\n"
        )
        for name, plan, notes in (
            ("standard", PLAN, self.NOTES.replace("## Not done", fix + "## Not done")),
            ("fast", self.SMALL, fix),
        ):
            with self.subTest(track=name):
                out = self.text(plan, notes)
                self.assertLess(
                    out.index("## Filed in the backlog"),
                    out.index("## Filed as not worth it"),
                )
                self.assertLess(
                    out.index("## Filed as not worth it"),
                    out.index("## Fixed on the way"),
                )
                # its line was the one line of `## Seen, not filed`, which then has none
                self.assertNotIn("## Seen, not filed", out)
                self.assertIn(
                    (
                        "- `app.py` (abc1234): r1.2, the suppression named a rule "
                        "the linter no longer has"
                    ),
                    out,
                )
                self.assertTrue(
                    next(
                        line for line in out if line.startswith("- the review, round 1")
                    ).endswith("; 1 fixed on the way")
                )

    def test_a_review_that_saw_nothing_outside_keeps_the_text_as_it_was(self) -> None:
        self.ADDED = []
        task = self.task()
        out = land.pr_text(task, self.NOTES, self.state())
        self.assertTrue(out.endswith("\n\n" + self.NOTES))
        self.assertNotIn("## Seen, not filed", out)


class TheIssue(Proposal):
    """A task from a GitHub issue names it in its pull request with `Issue: #42`, which
    GitHub links both ways, and no word that closes it, on both tracks
    (github-issues-tracker, criterion 5.1)."""

    SMALL = (
        "## Acceptance criteria\n\nSize: small, because one word changes.\n\n"
        "1. The file holds the word y.\n   - test: `sh tests/t.sh` in `tests/t.sh`\n"
    )

    def text(self, plan: str, kind: str | None, ticket: str | None) -> str:
        task = self.task(
            found=found_of(plan, approved=approval("owner", plan=plan)),
            record={"ticket": ticket},
        )
        task.settings = {**task.settings, "tracker": {"kind": kind} if kind else None}
        return land.pr_text(task, "", self.state())

    def test_each_track_names_the_issue_under_the_request(self) -> None:
        for name, plan in (("standard", PLAN), ("fast", self.SMALL)):
            with self.subTest(track=name):
                out = self.text(plan, "github", "#42").splitlines()
                self.assertEqual(out.count("Issue: #42"), 1)
                request = out.index("## The request")
                # right under the quote of the request
                self.assertGreater(out.index("Issue: #42"), request)
                self.assertTrue(out[out.index("Issue: #42") - 2].startswith("> "))
                text = "\n".join(out).lower()
                for word in (
                    "closes #42",
                    "fixes #42",
                    "resolves #42",
                    "close #42",
                    "fix #42",
                    "resolve #42",
                ):
                    self.assertNotIn(word, text)

    def test_a_linear_ticket_or_no_ticket_has_no_such_line(self) -> None:
        for kind, ticket in (("linear", "MBZ-12"), ("github", None), (None, None)):
            with self.subTest(kind=kind, ticket=ticket):
                self.assertNotIn("Issue:", self.text(PLAN, kind, ticket))


class Due(unittest.TestCase):
    """`due_of`: which review is due for the change as it is now, from the
    kept reviews."""

    FOLDER = "docs/backlog"

    def now(self, patch: str = "p1", contents: dict | None = None) -> dict:
        contents = (
            contents
            if contents is not None
            else {
                "x.txt": {
                    "base": "0" * 40,
                    "tip": "1" * 40,
                    "modes": ["000000", "100644"],
                }
            }
        )
        return {
            "tip": "abc",
            "base": "def",
            "files": sorted(contents),
            "patch": patch,
            "contents": contents,
            "lines": 2,
        }

    def due(
        self,
        reads: list[dict],
        now: dict | None = None,
        careful: tuple[str, ...] = (),
        tasks: int = 1,
    ) -> dict:
        return land.due_of(
            now or self.now(),
            reads,
            None,
            list(careful),
            tasks,
            small=False,
            folder=self.FOLDER,
        )

    def test_a_change_with_no_review_gets_one_read(self) -> None:
        said = self.due([])
        self.assertEqual(
            (said["due"], said["floor"], said["round"]), ("review", "read", 1)
        )

    def test_a_reviewed_change_needs_none(self) -> None:
        self.assertEqual(self.due([review(1)])["due"], "none")

    def test_a_change_after_the_review_gets_another(self) -> None:
        said = self.due([review(1)], self.now("p2"))
        self.assertEqual((said["due"], said["round"]), ("review", 2))

    def test_an_item_filed_in_the_backlog_after_the_review_is_covered(self) -> None:
        contents = {
            **self.now()["contents"],
            "docs/backlog/a-defect.md": {
                "base": "0" * 40,
                "tip": "2" * 40,
                "modes": ["000000", "100644"],
            },
        }
        self.assertEqual(self.due([review(1)], self.now("p2", contents))["due"], "none")
        elsewhere = {
            **self.now()["contents"],
            "docs/a-defect.md": contents["docs/backlog/a-defect.md"],
        }
        self.assertEqual(
            self.due([review(1)], self.now("p3", elsewhere))["due"], "review"
        )

    def test_careful_after_one_read_asks_for_the_full_set(self) -> None:
        said = self.due([review(1)], careful=("the owner says so",))
        self.assertEqual((said["due"], said["floor"]), ("review", "full"))

    def test_after_two_rounds_the_request_waits_for_the_owner(self) -> None:
        said = self.due(
            [review(1), review(2, patch="p2")],
            self.now("p2"),
            careful=("the owner says so",),
        )
        self.assertEqual(said["due"], "owner")
        self.assertIn(
            "it was one read, and this change gets the project's full set at the least",
            said["why"],
        )

    def test_two_reviews_nobody_answered(self) -> None:
        said = self.due([review(1, answered_by=()), review(2, answered_by=())])
        self.assertEqual(
            (said["due"], said["why"]),
            (
                "owner",
                "not reviewed: the review was started twice and no source answered",
            ),
        )

    def test_a_large_plan_gets_a_round(self) -> None:
        said = self.due([], tasks=4)
        self.assertEqual(
            (said["floor"], said["why"]),
            ("round", "the plan has 4 tasks, more than three"),
        )

    def test_a_must_fix_asks_for_a_round_after_its_fix(self) -> None:
        said = self.due([review(1, must_fix=1)], self.now("p2"))
        self.assertEqual((said["due"], said["floor"]), ("review", "round"))


if __name__ == "__main__":
    unittest.main()
