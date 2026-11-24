"""The board's criteria card of the standard track, with Yes and No with a note (the
task criteria-change-asks-again, task 2): the criteria's row of kind `criterion` with
its own question, "Approve the criteria?"; the card's one answer form, and on "Waits for
you" the way to it; a No with his note on record, which wakes the task's session, and a
No with no note refused; the change of task 1 on the card, each changed criterion's text
before beside its new text; no yes while a change stopped in the middle; no row for a
task begun on an older release; the newest answer of a block; and the words of an answer
on record. The task folders are real, and `lem criteria change` runs in this process
(criteria.py `cmd_change`) with `lem project state` stood in for by a write of its
event, as in tests/unit/test_criteria_change.py. The routes run in
tests/lem-board-act.sh with a server, and the card on a phone in
tests/lem-board-keys.sh.

    python3 -B -m unittest tests.unit.test_board_criteria_change
"""

import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills" / "lem" / "scripts"))
serve = importlib.import_module("serve")
bm = importlib.import_module("lem_board_model")
pages = importlib.import_module("lem_board_pages")
task_pages = importlib.import_module("lem_board_task")
lem_answers = importlib.import_module("lem_answers")
lem_artifacts = importlib.import_module("lem_artifacts")
lem_release = importlib.import_module("lem_release")
criteria = importlib.import_module("criteria")

SLUG = "invoice-export-empty-cells"
START = datetime(2026, 11, 23, 15, 0, tzinfo=UTC)
HEAD = (
    "## Acceptance criteria\n\nSize: full, because the export "
    "changes in three places.\n\n"
)
ONE = "1. An export keeps the order's number: order 1042 exports as 1042.\n"
TWO = (
    "2. An export keeps an empty cell: order 1042 with no note "
    "exports an empty note cell.\n"
)
THREE = "3. An export ends with a line break.\n"
NEW_TWO = (
    "2. An export keeps an empty cell and an empty row: order 1042 with no note and a "
    "blank line exports both.\n"
)
CRITERIA = HEAD + ONE + TWO + THREE
CHANGED = HEAD + ONE + NEW_TWO + THREE
NOTE = "criterion 2 must also cover empty rows"
IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1"
)
PHONE = {"via": "door", "device": "phone", "agent": IPHONE}


class Folder(unittest.TestCase):
    """A state folder with the task's folder, its log, and the board's workspace over
    them: the model as the server makes it (`bm.Reader`, `task_files_look`,
    `answers_look`) and the criteria as the server reads them
    (`serve.Workspace.criteria_waiting`). `lem criteria change` runs in this process,
    its `lem project state` written as the event; `lem session wake`, the scripts the
    acts run and the log of `board.act` are stood in for."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name) / ".lem" / "state"
        self.folder = self.state / "tasks" / SLUG
        self.folder.mkdir(parents=True)
        (self.folder / lem_release.MARK).write_text(
            lem_release.running() + "\n", encoding="utf-8"
        )
        self.minute = 0
        self.stop_state = False
        self.calls: list = []
        self.refuse = False
        self.space = serve.Workspace("shop", str(Path(self.tmp.name)))
        self.space.state = self.state
        self.space.look_sessions = lambda: None
        self.space.model = self.model

        def run(ws: object, file: str, *args: str) -> subprocess.CompletedProcess:
            self.calls.append((file, *args))
            return subprocess.CompletedProcess(
                args, 1 if self.refuse else 0, "", "it refused" if self.refuse else ""
            )

        for target, name, fake in (
            (
                serve,
                "tell_session",
                lambda ws, slug: (
                    self.calls.append(("wake", slug))
                    or {"woke": True, "opened": False, "said": ""}
                ),
            ),
            (
                serve,
                "asked_from",
                lambda ws, slug, act, via, *more: (
                    self.calls.append(("board.act", act, via, *more)) or ""
                ),
            ),
            (serve, "lem_run", run),
            (criteria, "script", self.script),
        ):
            patcher = mock.patch.object(target, name, side_effect=fake)
            patcher.start()
            self.addCleanup(patcher.stop)

    def append(self, event: str, **fields: object) -> dict:
        self.minute += 1
        record = {
            "ts": (START + timedelta(minutes=self.minute)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "event": event,
            "task": SLUG,
            **fields,
        }
        with (self.state / "events.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def script(self, name: str, repo: Path, *args: str) -> str:
        if name == "project.py" and args[0] == "state":
            if self.stop_state:
                raise KeyboardInterrupt("the change stopped before its held block")
            record = self.append(
                "task.state", status=args[2], text=args[3], lines=list(args[4:])
            )
            return json.dumps({"slug": SLUG, "status": args[2], "since": record["ts"]})
        raise AssertionError(f"no stand-in for {name} {args}")

    def task(self) -> "criteria.Task":
        """criteria.py's task over the folder, as `lem criteria change` makes it."""
        task = criteria.Task.__new__(criteria.Task)
        task.slug, task.night, task.mode, task.repo = (
            SLUG,
            None,
            "with-owner",
            Path(self.tmp.name),
        )
        task.directory = self.folder
        task.approved_file, task.small_file = (
            self.folder / "criteria.json",
            self.folder / "criteria.md",
        )
        task.read_mode = lambda: task.mode
        task.log = self.append
        return task

    def waiting(
        self, text: str = CRITERIA, block: str = criteria.CRITERIA_WAIT
    ) -> dict:
        """The criteria that wait for his yes on the standard track: criteria.md, and
        its held block."""
        (self.folder / "criteria.md").write_text(text, encoding="utf-8")
        self.append("session.open", session="S1", name=SLUG, phase="shape", why="new")
        return self.append(
            "task.state",
            status="held",
            text=block,
            lines=["type: fix, because the export loses empty cells"],
        )

    def changed(self) -> dict:
        """His No with NOTE on the board, then the session's change in its own
        words, `lem criteria change --file`."""
        source = Path(self.tmp.name) / "criteria-change.md"
        source.write_text(CHANGED, encoding="utf-8")
        return criteria.cmd_change(self.task(), str(source), NOTE)

    def model(self) -> "bm.Model":
        reader = bm.Reader(Path(self.tmp.name), self.state)
        reader.read_log()
        m = bm.derive(
            reader.events, [], int((START + timedelta(hours=1)).timestamp() * 1000)
        )
        bm.task_files_look(self.state, m)
        m.answers = bm.answers_look(self.state, m)
        return m

    def t(self) -> "bm.Task":
        return self.model().by_slug[SLUG]

    def ctx(self, view: str = "tasks") -> "pages.Ctx":
        ctx = pages.Ctx(
            host="h",
            workspace="w",
            model=self.model(),
            asset=lambda name: name,
            can_act=True,
            task=SLUG,
            tab="criteria",
        )
        ctx.view = view
        ctx.criteria_waiting = self.space.criteria_waiting
        return ctx

    def card(self) -> str:
        ctx = self.ctx()
        return str(task_pages.approve_card(ctx, ctx.model.by_slug[SLUG]))

    def answer(self, form: dict) -> dict:
        return serve.act_answer(self.space, SLUG, form, dict(PHONE))

    def key(self) -> str:
        return bm.answer_row(self.t())["key"]


class TheRow(Folder):
    """Criteria 2 and 5: the standard track's criteria have the row of kind `criterion`
    with "Approve the criteria?" while his yes would count, at once after a change, and
    the fast track keeps its own question."""

    def test_criterion_2_the_standard_tracks_criteria_have_yes_and_no_with_their_own_question(
        self,
    ) -> None:
        block = self.waiting()
        row = bm.answer_row(self.t())
        self.assertEqual(
            (
                row["kind"],
                row["key"],
                row["question"],
                list(row["options"].values()),
                row["note"],
            ),
            (
                "criterion",
                f"criterion:{SLUG}:{lem_answers.stamp_of(block['ts'])}",
                "Approve the criteria?",
                ["Yes", "No"],
                "No needs your words: what should the criteria say?",
            ),
        )
        # the question is the one the owner's typed No records (criteria.py), and the
        # session's texts name
        self.assertEqual(row["question"], criteria.CRITERIA_QUESTION)

    def test_criterion_5_after_a_change_the_request_for_his_yes_comes_at_once(
        self,
    ) -> None:
        self.waiting()
        self.changed()
        t = self.t()
        self.assertEqual(
            (t.text, t.need, t.turn, t.reading),
            (criteria.CHANGED_WAIT, {"need": "criteria", "number": None}, "asks", None),
        )
        self.assertEqual(bm.answer_row(t)["question"], "Approve the criteria?")
        self.assertEqual(bm.acts_of(t, None), ["approve"])
        self.assertEqual(bm.CHANGED_CRITERIA, criteria.CHANGED_WAIT)
        self.assertEqual(bm.CRITERIA_BEFORE, criteria.BEFORE)

    def test_an_interviews_criteria_have_the_row_after_the_read_and_not_before(
        self,
    ) -> None:
        self.waiting(block=criteria.INTERVIEW_WAIT)
        self.append("interview.end")
        self.assertIsNone(bm.answer_row(self.t()))
        self.append("criteria.read.start", by="lem")
        self.append(
            "criteria.read",
            by="lem",
            asked=3,
            answered=3,
            families=["opus"],
            silent=[],
            criteria=3,
            flagged=0,
            split=False,
            digest="x",
        )
        self.assertEqual(bm.answer_row(self.t())["question"], "Approve the criteria?")

    def test_the_fast_track_keeps_approve_this_criterion(self) -> None:
        self.waiting(
            text=(
                "## Acceptance criteria\n\nSize: small, because one cell.\n\n"
                "1. An empty note writes an empty cell.\n"
            ),
            block=bm.FAST_CRITERION,
        )
        row = bm.answer_row(self.t())
        self.assertEqual(
            (row["question"], row["note"]),
            (
                "Approve this criterion?",
                "No needs your words: what should the criterion say?",
            ),
        )


class TheCard(Folder):
    """Criteria 2 and 4: the card's one answer form, the way to it from "Waits for you",
    and the text before each changed criterion beside its new text."""

    def test_criterion_2_the_card_has_yes_and_no_with_a_note_and_the_digest_of_the_text_shown(
        self,
    ) -> None:
        self.waiting()
        html = self.card()
        digest = self.space.criteria_waiting(SLUG)["digest"]
        for part in (
            f'action="/h/w/tasks/{SLUG}/answer"',
            f'name="key" value="{self.key()}"',
            f'name="digest" value="{digest}"',
            'name="words"',
            'name="option" value="yes"',
            'name="option" value="no"',
            "No needs your words: what should the criteria say?",
            'aria-label="Approve the criteria"',
            'data-controller="sheet"',
        ):
            self.assertIn(part, html)
        self.assertNotIn("Before · criterion", html, "no change, no pairs")

    def test_talk_question_7_waits_for_you_keeps_read_and_approve_for_the_standard_track(
        self,
    ) -> None:
        self.waiting()
        html = str(pages.waits_page(self.ctx("waits")))
        self.assertIn("Read and approve…", html)
        self.assertNotIn("/answer", html)
        self.assertNotIn('name="option"', html)

    def test_criterion_4_the_card_shows_the_text_before_beside_the_new_text(
        self,
    ) -> None:
        self.waiting()
        self.changed()
        waiting = self.space.criteria_waiting(SLUG)
        self.assertEqual(
            (waiting["before"], waiting["words"], waiting["text"]),
            (CRITERIA, NOTE, CHANGED),
        )
        html = self.card()
        pairs = html[
            html.index('class="cf-pairs"') : html.index('data-controller="markdown"')
        ]
        self.assertEqual(pairs.count('class="cf-pair cf-changed"'), 1)
        before, now = (
            pairs.index("Before · criterion 2"),
            pairs.index("Now · criterion 2"),
        )
        self.assertLess(before, now)
        self.assertIn(
            (
                "An export keeps an empty cell: order 1042 with no note "
                "exports an empty note cell."
            ),
            pairs[before:now],
        )
        self.assertIn(
            (
                "An export keeps an empty cell and an empty row: order 1042 with no "
                "note and a blank line exports both."
            ),
            pairs[now:],
        )
        self.assertNotIn("criterion 1", pairs)
        self.assertIn(f"Lem changed them from your note “{NOTE}”.", html)
        # the whole criteria follow, and the form takes the new text's digest
        self.assertIn(f'name="digest" value="{waiting["digest"]}"', html)
        self.assertIn(
            "order 1042 with no note and a blank line exports both",
            html[html.index("<noscript>") :],
        )

    def test_the_pairs_show_only_while_the_changes_wait_stands(self) -> None:
        self.waiting()
        self.changed()
        self.append(
            "task.state",
            status="held",
            text=criteria.CRITERIA_WAIT,
            lines=["a lead's doubt"],
        )
        self.assertNotIn("cf-pairs", self.card())

    def test_a_phone_puts_the_two_texts_one_under_the_other(self) -> None:
        css = (ROOT / "skills" / "lem" / "assets" / "board.css").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            (
                "@media (max-width: 700px) { .cf-pair { grid-template-columns: "
                "minmax(0, 1fr); } }"
            ),
            css,
        )
        self.assertIn(".cf-side { min-width: 0;", css)


class HisNo(Folder):
    """Criteria 2 and 3: a No with his note is on record and wakes the task's session; a
    No with no note is refused, and the criteria, the state and the record stay as
    they were."""

    def test_criterion_2_a_no_with_his_note_is_on_record_and_wakes_the_session(
        self,
    ) -> None:
        block = self.waiting()
        key, digest = self.key(), self.space.criteria_waiting(SLUG)["digest"]
        done = self.answer(
            {"key": key, "option": "no", "digest": digest, "words": f"  {NOTE} "}
        )
        self.assertEqual(
            done,
            {
                "ok": True,
                "said": (
                    f"{bm.ANSWER_ON_RECORD} The task’s session got word of it, and it "
                    "changes the criteria from your words and asks for your yes again."
                ),
            },
        )
        made = lem_answers.on_record(self.folder, key)
        self.assertEqual(
            {
                k: made[k]
                for k in (
                    "kind",
                    "question",
                    "option",
                    "note",
                    "from",
                    "device",
                    "digest",
                )
            },
            {
                "kind": "criterion",
                "question": "Approve the criteria?",
                "option": "no",
                "note": NOTE,
                "from": "board",
                "device": "phone",
                "digest": digest,
            },
        )
        self.assertIn(("wake", SLUG), self.calls)
        self.assertIn(
            (
                "board.act",
                "answer",
                bm.VIA["door"],
                f"key={key}",
                "option=no",
                "question=Approve the criteria?",
            ),
            self.calls,
        )
        self.assertEqual(
            [c for c in self.calls if c[0] not in ("wake", "board.act")],
            [],
            "the server changes nothing itself",
        )
        # the session reads it on its wake, and `lem criteria change` then goes on
        # from it
        self.assertEqual(
            lem_answers.answer_of_block(self.folder, SLUG, block["ts"]), made
        )
        self.assertEqual(self.changed()["pairs"][0]["change"], "changed")

    def test_criterion_3_a_no_with_no_note_is_refused_and_nothing_changes(self) -> None:
        self.waiting()
        key, digest = self.key(), self.space.criteria_waiting(SLUG)["digest"]
        log = (self.state / "events.jsonl").read_text()
        said = self.answer(
            {"key": key, "option": "no", "digest": digest, "words": "   "}
        )
        self.assertEqual(
            said,
            {
                "ok": False,
                "said": (
                    "No needs your words: what should the criteria say? "
                    "Nothing was recorded."
                ),
            },
        )
        self.assertIsNone(lem_answers.on_record(self.folder, key))
        self.assertEqual(
            (
                (self.folder / "criteria.md").read_text(),
                (self.state / "events.jsonl").read_text(),
            ),
            (CRITERIA, log),
        )
        self.assertEqual(self.calls, [])
        # a page that showed other criteria is refused too, in the standard
        # track's words
        stale = self.answer(
            {"key": key, "option": "no", "digest": "0000", "words": NOTE}
        )
        self.assertEqual(
            stale["said"],
            (
                "The criteria changed since the page showed them. Read them again, "
                "then answer: nothing was recorded."
            ),
        )

    def test_criterion_6_yes_on_the_changed_text_approves_the_bytes_the_card_showed(
        self,
    ) -> None:
        self.waiting()
        self.changed()
        key, digest = self.key(), self.space.criteria_waiting(SLUG)["digest"]
        done = self.answer({"key": key, "option": "yes", "digest": digest})
        self.assertTrue(done["ok"], done)
        self.assertIn(
            (
                "criteria.py",
                "approve",
                SLUG,
                "--file",
                str(self.folder / "criteria.md"),
                "--shown",
                digest,
            ),
            self.calls,
        )
        self.assertEqual(
            (
                lem_answers.on_record(self.folder, key)["option"],
                lem_answers.on_record(self.folder, key)["question"],
            ),
            ("yes", "Approve the criteria?"),
        )

    def test_criterion_6_a_yes_to_the_text_before_the_change_is_refused(self) -> None:
        self.waiting()
        old_key, old_digest = self.key(), self.space.criteria_waiting(SLUG)["digest"]
        self.changed()
        said = self.answer({"key": old_key, "option": "yes", "digest": old_digest})
        self.assertFalse(said["ok"])
        self.assertIn("waits again since", said["said"])
        self.assertNotIn("criteria.py", [c[0] for c in self.calls])

    def test_his_typed_no_first_refuses_the_boards_yes_with_where_it_came_from(
        self,
    ) -> None:
        self.waiting()
        key, digest = self.key(), self.space.criteria_waiting(SLUG)["digest"]
        criteria.cmd_typed(self.task(), NOTE)
        said = self.answer({"key": key, "option": "yes", "digest": digest})
        self.assertRegex(
            said["said"],
            (
                r"^You picked No on “Approve the criteria\?” at \d\d:\d\d, in the "
                r"task’s session: the task’s session takes it\.$"
            ),
        )
        self.assertNotIn("criteria.py", [c[0] for c in self.calls])


class AStopInTheMiddle(Folder):
    """Logged decision 5: while `criteria-before.json` names the newest state block, a
    change began and did not end, so no yes is taken and the card says the new request
    comes; the end of the change gives the row back."""

    def test_no_yes_while_a_change_stopped_in_the_middle(self) -> None:
        self.waiting()
        digest_before = self.space.criteria_waiting(SLUG)["digest"]
        self.stop_state = True
        with self.assertRaises(KeyboardInterrupt):
            self.changed()
        t = self.t()
        self.assertEqual(
            (t.text, t.changing, t.approvable, bm.answer_row(t), bm.acts_of(t, None)),
            (criteria.CRITERIA_WAIT, True, False, None, []),
        )
        said = serve.act_approve(
            self.space,
            SLUG,
            {"digest": self.space.criteria_waiting(SLUG)["digest"]},
            bm.VIA["local"],
            heard=PHONE,
        )
        self.assertEqual(
            said,
            {
                "ok": False,
                "said": (
                    "Lem writes the changed criteria: the new request comes in a "
                    "moment. Nothing was approved."
                ),
            },
        )
        self.assertNotEqual(
            digest_before,
            self.space.criteria_waiting(SLUG)["digest"],
            "criteria.md moved before the stop",
        )
        self.assertIn(
            "Lem writes the changed criteria: the new request comes in a moment",
            self.card(),
        )
        self.assertNotIn('name="option"', self.card())
        self.assertEqual(self.calls, [])
        # the session runs the change again, which ends it: the new wait is approvable,
        # with the pairs
        self.stop_state = False
        self.assertTrue(self.changed()["resumed"])
        t = self.t()
        self.assertEqual(
            (t.text, t.changing, t.approvable), (criteria.CHANGED_WAIT, False, True)
        )
        self.assertIn("Before · criterion 2", self.card())

    def test_a_model_the_folders_look_did_not_reach_keeps_the_logs_value_and_a_second_look_gives_the_same(
        self,
    ) -> None:
        self.waiting()
        self.stop_state = True
        with self.assertRaises(KeyboardInterrupt):
            self.changed()
        reader = bm.Reader(Path(self.tmp.name), self.state)
        reader.read_log()
        m = bm.derive(
            reader.events, [], int((START + timedelta(hours=1)).timestamp() * 1000)
        )
        t = m.by_slug[SLUG]
        self.assertEqual(
            (t.changing, t.approvable, t.approvable_events), (False, True, True)
        )
        bm.task_files_look(self.state, m)
        once = (t.changing, t.approvable, t.began, t.behind)
        bm.task_files_look(self.state, m)
        self.assertEqual((t.changing, t.approvable, t.began, t.behind), once)
        self.assertEqual(once, (True, False, lem_release.running(), False))


class AnOlderRelease(Folder):
    """Talk question 6 (logged decision 8): a task begun on an older release than the
    board's has no row the board answers, of any kind, and keeps the one Approve under
    its criteria."""

    def test_a_task_of_the_release_before_has_no_row_and_keeps_its_approve(
        self,
    ) -> None:
        (self.folder / lem_release.MARK).write_text(
            lem_release.BEFORE + "\n", encoding="utf-8"
        )
        self.waiting()
        t = self.t()
        self.assertEqual(
            (t.began, t.behind, bm.answer_row(t), bm.acts_of(t, None)),
            (lem_release.BEFORE, True, None, ["approve"]),
        )
        html = self.card()
        self.assertIn("<span>Approve the criteria</span>", html)
        self.assertIn(f'action="/h/w/tasks/{SLUG}/approve"', html)
        self.assertNotIn('name="option"', html)
        self.assertIn("approve them there.", bm.answer_of(t))
        # a breaker and a plan have none either
        self.append(
            "decision.breaker",
            id=1,
            cause="criteria",
            what="No place",
            document="breaker.md",
        )
        self.append(
            "task.state", status="held", text="breaker 1 waits for the owner", lines=[]
        )
        self.assertIsNone(bm.answer_row(self.t()))
        self.append(
            "task.state", status="planned", text="the owner reads the plan", lines=[]
        )
        self.assertIsNone(bm.answer_row(self.t()))

    def test_a_task_of_the_boards_release_has_its_rows(self) -> None:
        self.waiting()
        t = self.t()
        self.assertEqual((t.began, t.behind), (lem_release.running(), False))
        self.assertIsNotNone(bm.answer_row(t))
        self.assertIn("Yes, or No with your words", bm.answer_of(t))


class TheNewestAnswerOfABlock(unittest.TestCase):
    """Talk question 3: the skip row and the criteria row of one interview stand on one
    block; `board_answer` gives the newest record of the block, his No to the criteria
    after his No to the skip."""

    def test_a_skips_no_then_a_criteria_no_on_one_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            block = "2026-11-23T15:00:00Z"
            ms = int(START.timestamp() * 1000)
            with mock.patch.object(
                lem_answers, "now", return_value="2026-11-23T15:10:00Z"
            ):
                lem_answers.record(
                    folder,
                    lem_answers.key_of("skip", SLUG, ms),
                    "Skip the persona read?",
                    "no",
                    "",
                    **PHONE,
                )
            skip = lem_answers.answer_of_block(folder, SLUG, block)
            self.assertEqual(skip["kind"], "skip")
            # after the read his No to the criteria: the newest is the criteria's
            with mock.patch.object(
                lem_answers, "now", return_value="2026-11-23T15:20:00Z"
            ):
                _, made = lem_answers.record(
                    folder,
                    lem_answers.key_of("criterion", SLUG, ms),
                    "Approve the criteria?",
                    "no",
                    NOTE,
                    **PHONE,
                )
            self.assertEqual(lem_answers.answer_of_block(folder, SLUG, block), made)


class TheWords(unittest.TestCase):
    """What an answer on record says, and the activity's line, read the question from
    the record and the event."""

    def test_took_effect_reads_the_question_of_the_record_and_says_where_it_was_typed(
        self,
    ) -> None:
        key = f"criterion:{SLUG}:20261123T150000Z"
        board = {
            "key": key,
            "kind": "criterion",
            "question": "Approve the criteria?",
            "option": "no",
            "label": "No",
            "at": "2026-11-23T15:40:00Z",
            "device": "phone",
        }
        self.assertRegex(
            lem_answers.took_effect(board),
            r"^You picked No on “Approve the criteria\?” at \d\d:\d\d, from the phone$",
        )
        typed = {**board, "from": "session"}
        del typed["device"]
        self.assertRegex(
            lem_answers.took_effect(typed),
            (
                r"^You picked No on “Approve the criteria\?” at \d\d:\d\d, "
                r"in the task’s session$"
            ),
        )
        # a record of the older form, with no question, names the fast track's
        old = {k: v for k, v in board.items() if k != "question"}
        self.assertRegex(
            lem_answers.took_effect(old),
            r"^You picked No on “Approve this criterion\?”",
        )

    def test_the_activity_names_the_question_of_the_event(self) -> None:
        e = {
            "event": "board.act",
            "act": "answer",
            "key": f"criterion:{SLUG}:20261123T150000Z",
            "option": "no",
            "question": "Approve the criteria?",
        }
        self.assertEqual(
            bm.acted_head(e), "You picked No on “Approve the criteria?” from the board"
        )
        self.assertEqual(
            bm.acted_head({k: v for k, v in e.items() if k != "question"}),
            "You picked No on “Approve this criterion?” from the board",
        )

    def test_the_held_line_of_a_change_in_words(self) -> None:
        self.assertEqual(
            bm.words(criteria.CHANGED_WAIT),
            "the criteria changed from your note, and wait for your yes again",
        )


class TheFiles(unittest.TestCase):
    """The files a change writes into the task directory are on the artifacts' map under
    the criteria, not among the working files."""

    def test_the_text_before_and_the_changed_criteria_are_the_criterias(self) -> None:
        self.assertEqual(
            lem_artifacts.place("criteria-before.json"),
            {
                "group": "criteria",
                "title": "Acceptance criteria (text before the change)",
                "role": "record",
                "of": "criteria.md",
                "label": "text before the change",
                "tab": "criteria",
            },
        )
        self.assertEqual(
            lem_artifacts.place("criteria-change.md"),
            {
                "group": "criteria",
                "title": (
                    "The changed criteria, as the session wrote them for the change"
                ),
                "role": "doc",
            },
        )


if __name__ == "__main__":
    unittest.main()
