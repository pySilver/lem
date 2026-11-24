"""A task's own session (session.py) and its two hooks (session_hook.py), as calls of
the functions that hold the rules: the phase from the state, the handoff's form, the
launch line with the seat and `[handoff] tokens`, and the hooks with and without
`LEM_TASK`; and the first line of `session.md` and of every brief a stage text or a
script writes, which names its standing text through `lem version`. What agterm does
with a session is in tests/lem-session.sh, with a stand-in for agtermctl.

    python3 -B -m unittest discover -s tests/unit
"""

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, cast
from unittest import mock

if TYPE_CHECKING:
    from lem import board_model as lem_board_model

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import project, session, session_hook
from lem import state as lem_state

# the folder of this checkout of Lem
ROOT_OF_LEM = Path(__file__).resolve().parents[2]
ROOT = Path("/lem-unit/repo")
SLUG = "gift-note"
HANDOFF = """task: gift-note · from shape · written: 2026-11-21T10:05Z

<!-- a comment the check leaves out -->

## Settled

- the criteria, approved (`criteria.json`)

## Open

none

## Next step

The lead plans the export's column.

## Failed

- none

## Changed files

- `docs/plans/2026-11-21-gift-note.md`: added, not committed
- src/export.py: changed in 1a2b3c4
"""


class Machine(unittest.TestCase):
    """Each case runs with a folder of its own as XDG_CONFIG_HOME: the home directory's
    file is never read."""

    def setUp(self) -> None:
        self.kept = os.environ.get("XDG_CONFIG_HOME")
        self.folder = tempfile.TemporaryDirectory()
        os.environ["XDG_CONFIG_HOME"] = self.folder.name

    def tearDown(self) -> None:
        if self.kept is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self.kept
        self.folder.cleanup()

    def written(self, text: str) -> None:
        file = lem_state.machine_file()
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding="utf-8")


class Tokens(Machine):
    def test_absent_is_lems_number_and_zero_sets_nothing(self) -> None:
        self.assertEqual(lem_state.handoff_tokens(), 600_000)
        self.written("[handoff]\ntokens = 0\n")
        self.assertIsNone(lem_state.handoff_tokens())
        self.written("[handoff]\ntokens = 250000\n")
        self.assertEqual(lem_state.handoff_tokens(), 250_000)

    def test_under_the_floor_a_negative_a_bool_and_a_float_are_refused(self) -> None:
        for value, says in (
            ("99999", "100000 or more"),
            ("-1", "100000 or more"),
            ("true", "of the wrong type"),
            ("150000.5", "of the wrong type"),
        ):
            with self.subTest(value=value):
                self.written(f"[handoff]\ntokens = {value}\n")
                with self.assertRaises(lem_state.StateError) as raised:
                    lem_state.handoff_tokens()
                self.assertIn(says, str(raised.exception))
                self.assertIn("lem project handoff --tokens N", str(raised.exception))

    def test_the_command_writes_the_number_and_default_takes_it_out_keeping_the_other_tables(
        self,
    ) -> None:
        self.written("[load]\nstart = 6\n")
        self.assertEqual(project.cmd_handoff("300000")["tokens"], 300_000)
        self.assertEqual(lem_state.machine_table("load"), {"start": 6})
        shown = project.cmd_handoff(None)
        self.assertEqual(
            (shown["tokens"], shown["default"], shown["said"]),
            (300_000, False, "handoff tokens: 300000 (set here)"),
        )
        self.assertIsNone(project.cmd_handoff("0")["tokens"])
        back = project.cmd_handoff("default")
        self.assertEqual(
            (back["tokens"], back["default"], back["said"]),
            (600_000, True, "handoff tokens: 600000 (default)"),
        )
        for wrong in ("99999", "-5", "lots", "1e6"):
            with self.subTest(wrong=wrong), self.assertRaises(project.SettingsError):
                project.cmd_handoff(wrong)


class Load(Machine):
    """`[load] start`: Lem's 40 on a machine with no number, the developer's own when he
    set one, and no gate after `--start none`, which a later read keeps."""

    def test_a_new_machine_gates_at_forty(self) -> None:
        self.assertFalse(lem_state.machine_file().exists())
        self.assertEqual(lem_state.load_start(), 40.0)
        shown = project.cmd_load(None)
        self.assertEqual((shown["start"], shown["default"]), (40.0, True))
        self.assertEqual(
            shown["gate"],
            "open"
            if shown["load"] < 40
            else "closed: the checks wait for a load below 40",
        )

    def test_his_number_wins_and_none_stays_none(self) -> None:
        self.written("[serve]\nport = 4500\n")
        mine = project.cmd_load("12")
        self.assertEqual((mine["start"], mine["default"]), (12.0, False))
        self.assertEqual(lem_state.load_start(), 12.0)
        away = project.cmd_load("none")
        self.assertEqual(
            (away["start"], away["gate"], away["default"]), (None, None, False)
        )
        later = project.cmd_load(None)
        self.assertEqual((later["start"], later["gate"]), (None, None))
        self.assertIsNone(lem_state.load_start())
        self.assertEqual(lem_state.machine_table("serve"), {"port": 4500})
        for wrong in ("0", "-3", "lots"):
            with self.subTest(wrong=wrong), self.assertRaises(project.SettingsError):
                project.cmd_load(wrong)

    def test_a_negative_number_written_by_hand_is_refused(self) -> None:
        self.written("[load]\nstart = -1\n")
        with self.assertRaises(lem_state.StateError) as raised:
            lem_state.load_start()
        self.assertIn("lem project load --start N", str(raised.exception))


class Seat(Machine):
    """`seats.session` takes the four sources of the merge agent's seat."""

    def decided(self, lines: list[str], home: dict) -> dict:
        raw = project.settings_of(
            "\n".join(lines) + "\n", ROOT / project.SETTINGS, "team"
        )
        return project.decide(ROOT, ROOT, raw, {}, raw, None, {"seats": home})["seats"][
            "session"
        ]

    def test_the_repository_the_home_file_or_the_agent(self) -> None:
        own = self.decided(
            ["[seats]", 'session = "claude/m1:high"'], {"session": "claude/m2"}
        )
        self.assertEqual(
            (own["model"], own["effort"], own["from"]),
            ("m1", "high", str(project.SETTINGS)),
        )
        mine = self.decided(["[branch]", 'base = "main"'], {"session": "claude/m2"})
        self.assertEqual(
            (mine["model"], mine["effort"], mine["from"]),
            ("m2", None, project.home_name()),
        )
        bare = self.decided(["[branch]", 'base = "main"'], {})
        self.assertEqual(
            (bare["agent"], bare["model"], bare["effort"], bare["from"]),
            ("claude", "opus", "high", "Lem's default"),
        )

    def test_only_claude_sits_there(self) -> None:
        with self.assertRaises(project.SettingsError) as raised:
            self.decided(["[seats]", 'session = "codex:high"'], {})
        self.assertIn(
            "a task's session runs Claude Code only for now", str(raised.exception)
        )

    def test_the_machine_file_refuses_the_seats_and_names_the_home_settings(
        self,
    ) -> None:
        # criterion 3 of one-home-folder-for-lem: the seats are no fact of the
        # whole machine
        self.written('[seats]\nsession = "claude:high"\n')
        with self.assertRaises(lem_state.StateError) as raised:
            lem_state.machine_table("load")
        self.assertIn(
            (
                f"{lem_state.machine_file()}: [seats] is not valid in this file: "
                f"its place is {lem_state.shown(lem_state.home_settings_file())}"
            ),
            str(raised.exception),
        )


class Phase(unittest.TestCase):
    def test_the_phase_comes_from_the_state(self) -> None:
        cases = [
            ((None, None, None, False), "shape"),
            (("held", "the interview waits for the owner", "standard", False), "shape"),
            (
                ("held", "the criteria wait for the owner's yes", "standard", True),
                "shape",
            ),
            (
                (
                    "held",
                    (
                        "the criteria wait for the owner: "
                        "the small change is a full change"
                    ),
                    "standard",
                    True,
                ),
                "shape",
            ),
            (("held", "breaker 2 waits for the owner", "standard", True), "build"),
            (("building", "lead: builder", "standard", True), "build"),
            (("planned", "the plan is committed", "standard", True), "build"),
            (("blocked", "the base is red", "standard", True), "build"),
            (("building", "small change: one builder", "fast", True), "fast"),
            (("open", "proposed", "fast", True), "fast"),
            (("landed", "merged", "fast", True), "fast"),
            (("ready", "the report is written", "standard", True), "land"),
            (("landing", "the checks run", "standard", True), "land"),
            (("open", "proposed", "standard", True), "land"),
            (("landed", "merged", "standard", True), "land"),
        ]
        for facts, phase in cases:
            with self.subTest(facts=facts):
                self.assertEqual(
                    session.phase_of(SLUG, *facts[:3], worktree=facts[3], state=""),
                    phase,
                )

    def test_a_block_of_the_merge_agents_seat_is_the_landings_and_one_of_the_talk_the_builds(
        self,
    ) -> None:
        merger = (
            "2026-11-23T10:00Z blocked: the merge agent `codex/gpt-6.2-sol:high` gave "
            "an error: no tokens, and this project permits no fallback\n"
            "the seat that failed: merger"
        )
        reviewer = merger.replace("the merge agent", "the reviewer").replace(
            "failed: merger", "failed: reviewer"
        )
        first = merger.splitlines()[0].split(": ", 1)[1]
        self.assertEqual(
            session.phase_of(
                SLUG, "blocked", first, "standard", worktree=True, state=merger
            ),
            "land",
        )
        self.assertEqual(
            session.phase_of(
                SLUG, "blocked", first, "standard", worktree=True, state=reviewer
            ),
            "build",
        )
        # a block's own lines, as a change of phase reads each block of its run
        self.assertEqual(
            session.phase_of(
                SLUG,
                "blocked",
                first,
                "standard",
                worktree=True,
                state="",
                lines=["the seat that failed: merger"],
            ),
            "land",
        )
        self.assertEqual(
            session.phase_left(
                SLUG,
                [
                    {
                        "status": "blocked",
                        "text": first,
                        "lines": ["the seat that failed: merger"],
                    }
                ],
                "standard",
                "build",
                "land",
                "",
            ),
            "land",
        )

    def test_a_task_queued_in_the_shape_goes_on_in_the_shape(self) -> None:
        # queued at step 7 of "The request": no lead ran, so its session takes step
        # 8 there
        state = (
            "2026-11-21T10:01Z queued: the owner's order: \"After coupon: "
            'unit cases"\nafter: coupon\nthen: the interview\n\n'
            "2026-11-21T10:00Z held: the interview waits for the "
            "owner\ntype: test, because w"
        )
        self.assertEqual(
            session.phase_of(
                SLUG,
                "queued",
                'the owner\'s order: "After coupon: unit cases"',
                "standard",
                worktree=False,
                state=state,
            ),
            "shape",
        )
        need = (
            "2026-11-21T10:00Z queued: needs the export's column\n"
            "after: coupon\ninvestigation: bug"
        )
        self.assertEqual(
            session.phase_of(
                SLUG,
                "queued",
                "needs the export's column",
                None,
                worktree=False,
                state=need,
            ),
            "shape",
        )

    def test_a_task_its_lead_queued_goes_on_in_the_build(self) -> None:
        # a `lead:` line in any block, the first line's text or a line under it
        for older in (
            "2026-11-21T10:00Z building: lead: builder",
            "2026-11-21T10:00Z building: the plan starts\nlead: builder",
        ):
            with self.subTest(older=older):
                state = (
                    "2026-11-21T10:30Z queued: needs the export's column\n"
                    f"after: coupon\n\n{older}"
                )
                self.assertEqual(
                    session.phase_of(
                        SLUG,
                        "queued",
                        "needs the export's column",
                        "standard",
                        worktree=True,
                        state=state,
                    ),
                    "build",
                )

    def test_a_task_that_gets_no_session(self) -> None:
        for facts, says in (
            (("parked", "put aside", "standard", True), "is parked"),
            (("landed", "merged", "standard", False), "landed and cleaned"),
            (("dropped", "nobody builds it", "standard", False), "is dropped"),
            (("answered", "the answer", None, False), "is answered"),
            (("answered", "the answer", "standard", True), "is answered"),
        ):
            with (
                self.subTest(facts=facts),
                self.assertRaises(session.SessionError) as raised,
            ):
                session.phase_of(SLUG, *facts[:3], worktree=facts[3], state="")
            self.assertIn(says, str(raised.exception))

    def test_a_dropped_task_whose_worktree_stays_gets_its_land_session(self) -> None:
        # a pull request closed on GitHub while no session ran: the server's wake opens
        # the task's session, which pays what its ticket is owed and cleans up, as it
        # does for a merged one
        closed = "the pull request was closed on the forge"
        self.assertEqual(
            session.phase_of(
                SLUG, "dropped", closed, "standard", worktree=True, state=""
            ),
            "land",
        )
        self.assertEqual(
            session.phase_of(SLUG, "dropped", closed, "fast", worktree=True, state=""),
            "fast",
        )
        with self.assertRaises(session.SessionError) as raised:
            session.phase_of(
                SLUG, "dropped", closed, "standard", worktree=False, state=""
            )
        self.assertIn("is dropped", str(raised.exception))

    def test_a_quiet_talk_ends_the_wait_after_45_minutes_counted_from_the_later_of_the_file_and_the_wait(
        self,
    ) -> None:
        began = 1_000_000.0
        minute = 60.0
        # talk-turns.md written at the wait's start: 44 minutes later the wait goes on,
        # at 45 it ends
        self.assertFalse(session.quiet_over(began, began, began + 44 * minute))
        self.assertTrue(session.quiet_over(began, began, began + 45 * minute))
        # a file not there yet counts from the wait's start
        self.assertFalse(session.quiet_over(None, began, began + 44 * minute))
        self.assertTrue(session.quiet_over(None, began, began + 45 * minute))
        # a second wait over the same old file, after a quiet end with no error, waits
        # its own 45 minutes
        second = began + 45 * minute
        self.assertFalse(session.quiet_over(began, second, second + 1))
        self.assertFalse(session.quiet_over(began, second, second + 44 * minute))
        self.assertTrue(session.quiet_over(began, second, second + 45 * minute))
        # a turn written during the wait starts the count again
        self.assertFalse(
            session.quiet_over(began + 30 * minute, began, began + 60 * minute)
        )
        self.assertEqual(session.QUIET_SECONDS, 45 * 60)

    def test_a_queued_task_waits_for_its_after_task_until_that_one_ended(self) -> None:
        queued = {
            "slug": SLUG,
            "status": "queued",
            "state": "2026-11-21T10:00Z queued: needs the column\nafter: coupon",
        }
        self.assertEqual(
            session.queued_behind(
                queued, [queued, {"slug": "coupon", "status": "open"}]
            ),
            "coupon",
        )
        self.assertIsNone(
            session.queued_behind(
                queued, [queued, {"slug": "coupon", "status": "landed"}]
            )
        )
        self.assertIsNone(
            session.queued_behind(
                queued, [queued, {"slug": "coupon", "status": "answered"}]
            )
        )

    def test_a_task_queued_behind_a_dropped_task_waits_for_the_owners_word(
        self,
    ) -> None:
        queued = {
            "slug": "export-notes-in-order",
            "status": "queued",
            "state": (
                "2026-11-22T10:00Z queued: needs the gift "
                "note\nafter: gift-note-in-export"
            ),
        }
        dropped = {"slug": "gift-note-in-export", "status": "dropped"}
        self.assertEqual(
            session.queued_behind(queued, [queued, dropped]), "gift-note-in-export"
        )
        said = session.behind_refusal(
            "export-notes-in-order", "gift-note-in-export", "dropped"
        )
        self.assertIn(
            (
                "'gift-note-in-export', which was dropped: it waits for the owner's "
                "word, which starts it or drops it"
            ),
            said,
        )
        self.assertIn("lem project may-start export-notes-in-order", said)
        # his "start export-notes-in-order now" writes it queued again without the
        # `after:` line
        started = dict(
            queued,
            state=(
                "2026-11-22T11:00Z queued: the owner's order was removed: "
                '"start export-notes-in-order now"\n\n'
            )
            + queued["state"],
        )
        self.assertIsNone(session.queued_behind(started, [started, dropped]))

    def test_the_after_line_is_read_from_every_line_its_first_too(self) -> None:
        # as `may-start` and the board read it: a block whose first line
        # is `after: coupon`
        first = {
            "slug": SLUG,
            "status": "queued",
            "state": (
                "2026-11-21T10:00Z queued: after: coupon\ntype: fix, "
                "because x\nthen: the fast track"
            ),
        }
        self.assertEqual(
            session.queued_behind(
                first, [first, {"slug": "coupon", "status": "building"}]
            ),
            "coupon",
        )
        nodes = [{"workspace": "W-coupon"}, {"workspace": "W-other"}]
        opens = {
            "coupon": {"workspace": "W-coupon", "ts": "2026-11-21T09:00:00Z"},
            "other": {"workspace": "W-other", "ts": "2026-11-21T09:30:00Z"},
        }
        with mock.patch.object(session, "node_of", return_value=None):
            self.assertEqual(
                session.workspace_for(SLUG, first, opens, nodes, ""), "W-coupon"
            )
        self.assertIsNone(
            session.after_of(
                {
                    "slug": SLUG,
                    "status": "queued",
                    "state": "2026-11-21T10:00Z queued: needs the column",
                }
            )
        )

    def test_the_phase_that_ends_is_the_states_and_not_the_one_the_session_opened_in(
        self,
    ) -> None:
        def block(status: str, text: str) -> dict:
            return {"status": status, "text": text}

        # a session that opened for the shape and led the task through the build hands
        # off from the build
        led = [
            block("building", "lead: builder"),
            block("building", "task 2 of 2"),
            block("ready", "the report is written"),
        ]
        self.assertEqual(
            session.phase_left(SLUG, led, "standard", "land", "shape", ""), "build"
        )
        # a session that wrote the build's first block hands off from the phase it
        # opened in
        self.assertEqual(
            session.phase_left(
                SLUG,
                [block("building", "lead: builder")],
                "standard",
                "build",
                "shape",
                "",
            ),
            "shape",
        )
        # a session that wrote nothing since it opened: its own phase, so `next` refuses
        # while the state gives it
        self.assertEqual(
            session.phase_left(SLUG, [], "standard", "build", "build", ""), "build"
        )
        # a park in between gives no phase
        self.assertEqual(
            session.phase_left(
                SLUG,
                [block("building", "x"), block("parked", "aside"), block("ready", "y")],
                "standard",
                "land",
                "build",
                "",
            ),
            "build",
        )
        # a queued block is the shape's when no lead ran for the task, and the build's
        # when one did
        queued = [block("queued", "needs the column")]
        self.assertEqual(
            session.phase_left(SLUG, queued, "standard", "land", "build", ""), "shape"
        )
        self.assertEqual(
            session.phase_left(
                SLUG,
                queued,
                "standard",
                "land",
                "shape",
                "2026-11-21T10:00Z building: lead: builder",
            ),
            "build",
        )


class FirstLine(unittest.TestCase):
    """`wait --first-line`: the task's first line for the session where the owner typed
    the request, or null with the reason."""

    def state(self, status: str, text: str, *lines: str, **more: object) -> dict:
        return {
            "event": "task.state",
            "task": SLUG,
            "status": status,
            "text": text,
            "lines": list(lines),
            **more,
        }

    def test_the_line_in_the_form_for_another_session(self) -> None:
        said = self.state(
            "building",
            "small change: one builder",
            "type: fix, because x",
            say="fix: x.",
            say_named="gift-note · fix: x.",
        )
        asked = self.state("held", "the request waits for one answer")
        self.assertEqual(
            session.first_line_end(SLUG, [asked, said], night=False),
            {"task": SLUG, "say": "gift-note · fix: x.", "gone": False},
        )
        # the one question of the request has no type and no line: the wait goes on
        self.assertIsNone(session.first_line_end(SLUG, [asked], night=False))
        self.assertIsNone(session.first_line_end(SLUG, [], night=False))

    def test_a_block_no_line_will_follow(self) -> None:
        typed = self.state(
            "building", "small change: one builder", "type: docs, because a line"
        )
        night = cast("dict", session.first_line_end(SLUG, [typed], night=True))
        self.assertEqual((night["say"], night["gone"]), (None, False))
        self.assertIn("a task of the night", night["why"])
        self.assertIn(
            "has no line",
            cast("dict", session.first_line_end(SLUG, [typed], night=False))["why"],
        )
        # the hold of an order that named no task: his answer brings the line, in the
        # task's own session
        held = cast(
            "dict",
            session.first_line_end(
                SLUG,
                [
                    self.state(
                        "held",
                        'the order waits for the owner: "After the gift note"',
                        "type: feat, because x",
                    )
                ],
                night=False,
            ),
        )
        self.assertEqual((held["say"], held["gone"]), (None, False))
        self.assertIn(f"{SLUG} is held: the order waits for the owner", held["why"])
        self.assertIn("comes with his answer", held["why"])
        for status in ("dropped", "answered", "landed", "parked"):
            ended = cast(
                "dict",
                session.first_line_end(
                    SLUG,
                    [
                        self.state("held", "the request waits for one answer"),
                        self.state(status, "the owner dropped it"),
                    ],
                    night=False,
                ),
            )
            self.assertEqual(ended["say"], None, status)
            self.assertIn(f"{SLUG} is {status} before its first line", ended["why"])

    def run_wait(self, records: list[dict], gone: dict | None, bound: float) -> dict:
        with (
            mock.patch.object(
                session,
                "place",
                return_value={"session": "", "socket": "", "window": ""},
            ),
            mock.patch.object(session, "gone_session", return_value=gone),
            mock.patch.object(
                project, "task_directory", return_value=Path("/lem-unit/task")
            ),
            mock.patch.object(
                project,
                "events_named",
                side_effect=lambda root, *names: [
                    r for r in records if r["event"] in names
                ],
            ),
        ):
            return session.cmd_first_line(ROOT, SLUG, 0.01, bound)

    def test_a_gone_session_and_the_bound(self) -> None:
        gone = self.run_wait([], {"session": "S-9", "name": SLUG}, 60)
        self.assertEqual(
            (gone["say"], gone["gone"], gone["session"]), (None, True, "S-9")
        )
        self.assertIn(f"`lem session open {SLUG} --why dead`", gone["why"])
        late = self.run_wait(
            [self.state("held", "the request waits for one answer")], None, 0.05
        )
        self.assertEqual((late["say"], late["gone"]), (None, False))
        self.assertIn(f"no first line of {SLUG} came in", late["why"])
        self.assertEqual(session.FIRST_LINE_BOUND, 600)
        said = self.run_wait(
            [
                self.state(
                    "held",
                    "the interview waits",
                    "type: feat, because y",
                    say="feat.",
                    say_named="gift-note · feat.",
                )
            ],
            None,
            60,
        )
        self.assertEqual(said["say"], "gift-note · feat.")


class Close(unittest.TestCase):
    OPENS = [
        {"event": "session.open", "task": SLUG, "session": "S-1"},
        {"event": "session.open", "task": "other-task", "session": "S-7"},
        {"event": "session.open", "task": SLUG, "session": "S-2"},
    ]

    def close(self, session_id: str) -> tuple[dict, list]:
        closed = []
        with (
            mock.patch.object(
                session,
                "place",
                return_value={"session": "", "socket": "", "window": ""},
            ),
            mock.patch.object(session, "tree", return_value={}),
            mock.patch.object(
                session, "node_of", return_value={"name": "x", "active": False}
            ),
            mock.patch.object(
                session, "ctl", side_effect=lambda where, *args: closed.append(args)
            ),
            mock.patch.object(project, "append_event"),
            mock.patch.object(
                project, "task_directory", return_value=Path("/lem-unit/task")
            ),
            mock.patch.object(
                project,
                "events_named",
                side_effect=lambda root, *names: [
                    r for r in self.OPENS if r["event"] in names
                ],
            ),
        ):
            return session.cmd_close(
                ROOT, SLUG, session_id, "handoff", when_unselected=False, every=0.01
            ), closed

    def test_a_close_by_id_closes_only_a_session_of_that_task(self) -> None:
        with self.assertRaises(session.SessionError) as raised:
            self.close("S-7")
        self.assertIn("S-7 is no session of gift-note", str(raised.exception))
        self.assertIn("other-task", str(raised.exception))
        with self.assertRaises(session.SessionError):
            self.close("S-404")
        # an older session of the same task is its own: a handoff closes its
        # predecessor, in any case of the id
        done, closed = self.close("s-1")
        self.assertTrue(done["closed"])
        self.assertEqual(
            closed, [("session", "close", "--target", "s-1", "--undoable")]
        )


class JobLine(unittest.TestCase):
    # agterm's foreground of an agent the cronn job's script starts: the owner's wrapper
    # execs claude with its own words first, then the job's JOB_ARGS, then the prompt
    # (the shape of `agtermctl tree --json`, 2026-11-23)
    AGENT = [
        "/Users/someone/.local/bin/claude",
        "--settings",
        "/Users/someone/.claude/gateway.json",
        "--model",
        "claude-opus-5-5",
        "--effort",
        "high",
    ]

    def test_an_agent_a_job_started_with_its_line_last(self) -> None:
        for line in ("/lem night", "/lem night 2", "/lem night 12", "/lem retro"):
            self.assertEqual(
                session.job_line({"foreground": [*self.AGENT, line]}), line
            )
        self.assertEqual(
            session.job_line({"foreground": ["node", "/opt/lib/claude", "/lem retro"]}),
            "/lem retro",
        )
        self.assertEqual(
            session.job_line({"foreground": ["codex", " /lem  night 3 "]}),
            "/lem night 3",
        )

    def test_an_agent_the_owner_started_or_a_line_that_is_no_job(self) -> None:
        # he started claude with no prompt and typed /lem retro into it
        self.assertIsNone(session.job_line({"foreground": self.AGENT}))
        self.assertIsNone(
            session.job_line(
                {"foreground": ["/usr/local/bin/claude", "--resume", "b8927615"]}
            )
        )
        for line in (
            "/lem night 0",
            "/lem night two",
            "/lem retro now",
            "/lem new the footer says Terms",
            "/lem status",
            "/lem",
        ):
            self.assertIsNone(
                session.job_line({"foreground": [*self.AGENT, line]}), line
            )
        # a task's session: the launch line's shell, whose -c string is the last word
        ground = [
            "/opt/homebrew/bin/fish",
            "-l",
            "-c",
            'LEM_TASK=x claude "Read /x/session.md and follow it."',
        ]
        self.assertIsNone(session.job_line({"foreground": ground}))
        self.assertIsNone(
            session.job_line({"foreground": ["/bin/sh", "-c", "claude '/lem night'"]})
        )
        # no agent before the line, an idle shell, and a pane agterm has not drawn
        self.assertIsNone(session.job_line({"foreground": ["/bin/echo", "/lem night"]}))
        self.assertIsNone(session.job_line({"foreground": ["/lem night"]}))
        self.assertIsNone(session.job_line({"foreground": None, "realized": True}))
        self.assertIsNone(session.job_line({"realized": False}))


class Wake(unittest.TestCase):
    OPENS = [
        {
            "event": "session.open",
            "task": SLUG,
            "session": "S-1",
            "ts": "2026-11-22T10:00:00Z",
        }
    ]

    def wake(self, why: str, *, alive: bool) -> tuple[dict, list, list]:
        sent, logged = [], []
        with (
            mock.patch.object(
                session,
                "place",
                return_value={"session": "", "socket": "", "window": ""},
            ),
            mock.patch.object(session, "tree", return_value={}),
            mock.patch.object(
                session, "node_of", return_value={"name": "gift-note", "active": False}
            ),
            mock.patch.object(session, "live", return_value=alive),
            mock.patch.object(
                session,
                "ctl",
                side_effect=lambda where, *args, window=True: sent.append(args),
            ),
            mock.patch.object(
                session,
                "cmd_open",
                side_effect=AssertionError("the Inbox's wake opens no session"),
            ),
            mock.patch.object(
                project,
                "append_event",
                side_effect=lambda root, event, slug, fields: logged.append(
                    (event, fields)
                ),
            ),
            mock.patch.object(
                project, "task_directory", return_value=Path("/lem-unit/task")
            ),
            mock.patch.object(
                project,
                "events_named",
                side_effect=lambda root, *names: [
                    r for r in self.OPENS if r["event"] in names
                ],
            ),
        ):
            return session.cmd_wake(ROOT, SLUG, why, None), sent, logged

    def test_the_inbox_wakes_a_live_session_and_opens_none(self) -> None:
        # the board server's word when a thing of the task went to the Inbox, or a reply
        # came for a gone session
        self.assertIn("inbox", session.WAKES)
        done, sent, logged = self.wake("inbox", alive=True)
        self.assertEqual((done["woke"], done["opened"]), (True, False))
        self.assertEqual(
            sent, [("msg", "send", "lem: gift-note inbox", "--to", "S-1:left")]
        )
        self.assertEqual(logged, [("session.wake", {"session": "S-1", "why": "inbox"})])
        done, sent, logged = self.wake("inbox", alive=False)
        self.assertEqual(
            (done["woke"], done["opened"], sent, logged), (False, False, [], [])
        )
        self.assertIn("waits there", done["say"])


class Agent(unittest.TestCase):
    def test_an_agent_in_the_left_pane(self) -> None:
        self.assertTrue(
            session.agent_runs(
                {"foreground": ["/usr/local/bin/claude", "--resume", "x"]}
            )
        )
        self.assertTrue(session.agent_runs({"foreground": ["node", "/opt/lib/claude"]}))
        self.assertFalse(
            session.agent_runs(
                {"foreground": ["/opt/homebrew/bin/fish"], "realized": True}
            )
        )
        self.assertFalse(session.agent_runs({"realized": True}))
        self.assertIsNone(session.agent_runs({"realized": False}))

    def test_the_launch_lines_shell_runs_the_agent_in_its_command(self) -> None:
        # agterm's tree for a live task session that Claude Code held idle
        # (lem-scratch, 2026-11-21)
        ground = [
            "/opt/homebrew/bin/fish",
            "-l",
            "-c",
            (
                "LEM_TASK=profile-names-working-days "
                "CLAUDE_CODE_AUTO_COMPACT_WINDOW=600000 claude --model opus --effort "
                'high "Read /x/session.md and follow it."'
            ),
        ]
        self.assertTrue(session.agent_runs({"foreground": ground, "realized": True}))
        now = datetime(2026, 11, 21, 10, 0, 0, tzinfo=UTC)
        self.assertTrue(
            session.live({"foreground": ground}, {"ts": "2026-11-21T08:00:00Z"}, now)
        )
        # the line launch_line builds reads the same way
        line = session.launch_line(
            "/bin/zsh",
            SLUG,
            Path("/r/session.md"),
            600_000,
            {"agent": "claude", "model": None, "effort": None},
        )
        self.assertTrue(session.agent_runs({"foreground": shlex.split(line)}))

    def test_a_shell_whose_command_is_no_agent_or_cannot_be_read(self) -> None:
        self.assertFalse(
            session.agent_runs({"foreground": ["/bin/zsh", "-l"], "realized": True})
        )
        self.assertFalse(
            session.agent_runs({"foreground": ["/bin/sh", "-c", "LEM_TASK=x htop"]})
        )
        self.assertFalse(
            session.agent_runs({"foreground": ["/bin/sh", "-c", "echo claude"]})
        )
        # an unclosed quote: a plain word that is an agent's file still counts, and none
        # does not
        self.assertTrue(
            session.agent_runs(
                {"foreground": ["/bin/sh", "-c", 'LEM_TASK=x claude "Read']}
            )
        )
        self.assertFalse(
            session.agent_runs(
                {"foreground": ["/bin/sh", "-c", 'LEM_TASK=x htop "Read']}
            )
        )

    def test_a_session_counts_while_its_agent_starts(self) -> None:
        now = datetime(2026, 11, 21, 10, 0, 0, tzinfo=UTC)
        opened = {"ts": (now - timedelta(seconds=20)).strftime("%Y-%m-%dT%H:%M:%SZ")}
        shell = {"foreground": ["/bin/zsh"]}
        self.assertTrue(session.live(shell, opened, now))
        self.assertFalse(
            session.live(shell, opened, now + timedelta(seconds=session.STARTING))
        )
        self.assertFalse(session.live(None, opened, now))


class Launch(unittest.TestCase):
    BRIEF = Path("/lem-unit/repo/.lem/state/tasks/gift-note/session.md")

    def test_the_line_holds_the_task_the_number_and_the_seat_only_where_named(
        self,
    ) -> None:
        line = session.launch_line(
            "/bin/zsh",
            SLUG,
            self.BRIEF,
            600_000,
            {"agent": "claude", "model": None, "effort": None},
        )
        self.assertEqual(
            line,
            (
                f"/bin/zsh -l -c 'LEM_TASK={SLUG} "
                'CLAUDE_CODE_AUTO_COMPACT_WINDOW=600000 claude "Read '
                f"{self.BRIEF} and follow it.\"'"
            ),
        )
        seated = session.launch_line(
            "/bin/zsh",
            SLUG,
            self.BRIEF,
            None,
            {"agent": "claude", "model": "m1", "effort": "high"},
        )
        self.assertIn(
            f"'LEM_TASK={SLUG} claude --model m1 --effort high \"Read", seated
        )
        self.assertNotIn("CLAUDE_CODE_AUTO_COMPACT_WINDOW", seated)

    def test_a_lem_that_is_not_the_installed_plugin_names_its_folder(self) -> None:
        home = {"CLAUDE_CONFIG_DIR": "/lem-unit/claude"}
        self.assertIsNone(
            session.plugin_dir(
                Path("/lem-unit/claude/plugins/cache/lem/lem/1.2.0"), home
            )
        )
        self.assertEqual(
            session.plugin_dir(Path("/lem-unit/clones/lem"), home),
            "/lem-unit/clones/lem",
        )
        line = session.launch_line(
            "/bin/zsh", SLUG, self.BRIEF, None, {}, "/lem-unit/clones/lem"
        )
        self.assertIn(' claude --plugin-dir /lem-unit/clones/lem "Read ', line)
        self.assertNotIn(
            "--plugin-dir",
            session.launch_line("/bin/zsh", SLUG, self.BRIEF, None, {}, None),
        )

    def test_the_plan_talks_pair_reads_the_same_folder(self) -> None:
        # the lead writes the pair's launch line itself
        # (harness/claude-code/plan-talk.md), with the `plugin_dir` this command prints:
        # a clone's folder, or null for the installed plugin
        import contextlib
        import io

        def printed(root: str) -> dict:
            out = io.StringIO()
            with (
                mock.patch.object(session, "PLUGIN", Path(root)),
                mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": "/lem-unit/claude"}),
                contextlib.redirect_stdout(out),
            ):
                session.main(["plugin-dir"])
            return json.loads(out.getvalue())

        self.assertEqual(
            printed("/lem-unit/clones/lem"), {"plugin_dir": "/lem-unit/clones/lem"}
        )
        self.assertEqual(
            printed("/lem-unit/claude/plugins/cache/lem/lem/1.2.0"),
            {"plugin_dir": None},
        )

    def test_a_path_the_line_cannot_carry_is_refused(self) -> None:
        # fish reads a backslash inside single quotes as an escape, so no quoting
        # carries one to every shell
        with self.assertRaises(session.SessionError) as raised:
            session.launch_line(
                "/bin/zsh", SLUG, Path("/tmp/o\\neil/session.md"), None, {}
            )
        self.assertIn("move the checkout to a path without them", str(raised.exception))

    # the shells that may read the line: agterm's outer level, and the owner's login
    # shell inside it
    SHELLS = {
        "bash": ["--norc", "--noprofile", "-c"],
        "zsh": ["-f", "-c"],
        "fish": ["--no-config", "-c"],
    }

    def through_each_shell(self, seat: dict, folder: str) -> None:
        """Run the launch line through each shell this machine has, at both of its
        levels, with a stand-in for the login shell that says its argv and a stand-in
        claude that says its own."""
        import shutil

        root = Path(tempfile.mkdtemp(prefix="lem-launch-"))
        self.addCleanup(shutil.rmtree, root)
        tools = root / "bin"
        tools.mkdir()
        for name in ("claude", "outer"):
            (tools / name).write_text(
                f"#!{sys.executable}\nimport json, os, sys\n"
                "print(json.dumps([os.environ.get('LEM_TASK'), *sys.argv[1:]]))\n"
            )
            (tools / name).chmod(0o755)
        brief = root / folder / ".lem" / "state" / "tasks" / SLUG / "session.md"
        plugin = str(root / folder / "lem")
        shells = {
            name: (found, flags)
            for name, flags in self.SHELLS.items()
            if (found := shutil.which(name))
        }
        self.assertIn(
            "bash", shells, "bash is on every machine the launch line runs on"
        )
        line = session.launch_line(
            str(tools / "outer"), SLUG, brief, None, seat, plugin
        )
        env = {"PATH": f"{tools}:/usr/bin:/bin", "HOME": str(root)}
        wanted = [SLUG] + [
            word
            for flag in ("model", "effort")
            if seat.get(flag)
            for word in (f"--{flag}", seat[flag])
        ]
        wanted += ["--plugin-dir", plugin, f"Read {brief} and follow it."]
        for outer, (path, flags) in shells.items():
            said = subprocess.run(
                [path, *flags, line],
                capture_output=True,
                text=True,
                env=env,
                cwd=root,
                check=False,
            )
            self.assertEqual(
                (said.returncode, said.stderr), (0, ""), f"{outer} at the outer level"
            )
            got = json.loads(said.stdout)
            self.assertEqual(
                got[1:],
                shlex.split(line)[1:],
                f"{outer} reads the outer level as the POSIX tokenizer does",
            )
            self.assertEqual(got[1:3], ["-l", "-c"])
            for inner, (inner_path, inner_flags) in shells.items():
                ran = subprocess.run(
                    [inner_path, *inner_flags, got[3]],
                    capture_output=True,
                    text=True,
                    env=env,
                    cwd=root,
                    check=False,
                )
                self.assertEqual(
                    (ran.returncode, ran.stderr), (0, ""), f"{inner} inside {outer}"
                )
                self.assertEqual(
                    json.loads(ran.stdout), wanted, f"{inner} inside {outer}"
                )
        self.assertTrue(
            session.agent_runs(
                {"foreground": ["/bin/zsh", "-l", "-c", shlex.split(line)[3]]}
            )
        )

    def test_a_model_with_brackets_reaches_the_agent_whole_in_every_login_shell(
        self,
    ) -> None:
        # zsh, the default login shell of macOS, stops a bare `opus[1m]` with "no
        # matches found"
        self.through_each_shell(
            {"agent": "claude", "model": "opus[1m]", "effort": "high"}, "repo"
        )

    def test_a_checkout_path_with_an_apostrophe_and_a_space_reaches_the_agent_whole(
        self,
    ) -> None:
        self.through_each_shell(
            {"agent": "claude", "model": "opus", "effort": None}, "o'neil's work"
        )


# The first line of every brief, as the stage texts and the scripts write it.
BRIEF_LINE = re.compile(
    r"Read `skills/lem/prompts/(?P<name>[\w-]+)\.md` in the folder that `lem version` "
    r"prints as `root`, and (?:follow it|do the job named here); when `lem version` "
    r"fails, stop and say that `lem` is not on the PATH, "
    r"with `lem doctor` as the check\."
)


class SessionBrief(unittest.TestCase):
    """`session.md` sends its session to the texts of the Lem installed when it starts:
    Lem in `.../lem/0.2.0` writes it, the plugin updates to `.../lem/0.2.1`, and the
    session reads 0.2.1."""

    def written_by(self, plugin: Path) -> str:
        skill = plugin / "skills" / "lem"
        with mock.patch.multiple(session, SKILL=skill, PLUGIN=plugin):
            return session.brief_text(
                SLUG, "shape", "new", ROOT / ".lem/state/tasks" / SLUG, ROOT, None
            )

    def test_the_text_names_no_folder_of_the_lem_that_wrote_it(self) -> None:
        text = self.written_by(Path("/lem-unit/claude/plugins/cache/lem/lem/0.2.0"))
        self.assertNotIn("0.2.0", text)
        self.assertNotIn("/plugins/", text)
        first = text.splitlines()[0]
        self.assertRegex(first, BRIEF_LINE)
        found = BRIEF_LINE.fullmatch(first)
        if found is None:
            self.fail(f"the brief's first line is not in its form: {first!r}")
        self.assertEqual(found["name"], "session")

    def test_after_an_update_the_first_line_leads_to_the_new_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp).resolve() / "plugins/cache/lem/lem"
            for version in ("0.2.0", "0.2.1"):
                plugin = cache / version
                (plugin / "bin").mkdir(parents=True)
                (plugin / "bin/lem").write_bytes((ROOT_OF_LEM / "bin/lem").read_bytes())
                (plugin / "bin/lem").chmod(0o755)
                (plugin / "skills/lem/prompts").mkdir(parents=True)
                (plugin / "skills/lem/prompts/session.md").write_text(
                    f"Lem {version}\n"
                )
            text = self.written_by(cache / "0.2.0")
            # the update: the session's PATH holds the bin/ of 0.2.1, the plugin
            # loaded now
            lem = shutil.which("lem", path=str(cache / "0.2.1/bin"))
            if lem is None:
                self.fail("no lem in the bin/ of 0.2.1")
            ran = subprocess.run(
                [lem, "version"],
                capture_output=True,
                text=True,
                check=True,
                env={**os.environ, "LEM_SERVE": "off"},
            )
            root = Path(json.loads(ran.stdout)["root"])
            first = text.splitlines()[0]
            self.assertRegex(first, BRIEF_LINE)
            found = BRIEF_LINE.match(first)
            if found is None:
                self.fail(f"the brief's first line is not in its form: {first!r}")
            self.assertEqual(
                (root / f"skills/lem/prompts/{found['name']}.md").read_text(),
                "Lem 0.2.1\n",
            )


class EveryBrief(unittest.TestCase):
    """Every brief a stage tells a session to write or send, and every one a script
    writes, names its standing text by its place in the plugin through `lem version`,
    never by a folder of Lem. A line that only tells the reader of a stage to read a
    prompt (`Read SKILL_DIR/prompts/writing.md first`) is no brief: that reader runs
    from the installed Lem already."""

    PLACES = ("skills", "agents", "src")
    TEXTS = {".md", ".py", ".sh", ".toml", ".json", ".txt", ""}
    # a brief's first line by its shape, and what it reads: a Lem text when it names one
    # by a path
    SHAPE = re.compile(r"Read (?P<what>.+?),? and (?:follow it|do the job named here)")
    LEM_TEXT = re.compile(r"prompts|SKILL|skills/lem|plugins/")

    def old_lines(self, text: str) -> list[str]:
        return [
            line.strip()
            for line in text.splitlines()
            for found in self.SHAPE.finditer(line)
            if self.LEM_TEXT.search(found["what"])
            and not BRIEF_LINE.match(line, found.start())
        ]

    def test_no_brief_names_a_lem_text_by_a_folder(self) -> None:
        root = ROOT_OF_LEM
        wrong, briefs = [], 0
        for place in self.PLACES:
            for path in sorted((root / place).rglob("*")):
                if (
                    not path.is_file()
                    or path.suffix not in self.TEXTS
                    or "vendor" in path.parts
                ):
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
                briefs += len(BRIEF_LINE.findall(text))
                wrong += [
                    f"{path.relative_to(root)}: {line}" for line in self.old_lines(text)
                ]
        self.assertEqual(wrong, [])
        # the lead's, the fast track's, the talk's, the scout's, the investigator's, the
        # review's, a landing builder's, session.md's and the merge brief's
        # (merge-brief-TIP-BASE.md)
        self.assertGreaterEqual(briefs, 9)

    def test_the_old_forms_are_found_and_a_stage_readers_line_is_not(self) -> None:
        self.assertEqual(
            len(self.old_lines("   Read SKILL_DIR/prompts/lead.md and follow it.")), 1
        )
        self.assertEqual(
            len(
                self.old_lines(
                    "Read SKILL_DIR/prompts/landing.md and do the job named here."
                )
            ),
            1,
        )
        self.assertEqual(
            len(
                self.old_lines(
                    "        f\"Read {SKILL / 'prompts' / 'session.md'} "
                    'and follow it.", "",'
                )
            ),
            1,
        )
        self.assertEqual(
            len(
                self.old_lines(
                    "Read /x/plugins/cache/lem/lem/0.2.0/skills/lem/prompts/merge.md "
                    "and follow it."
                )
            ),
            1,
        )
        self.assertEqual(
            self.old_lines(
                "   `SKILL_DIR/prompts/writing.md` first: the story. "
                "Read `brief.md` and follow it."
            ),
            [],
        )
        self.assertEqual(
            self.old_lines('claude "Read TASK_DIR/session.md and follow it."'), []
        )


class NoFocus(unittest.TestCase):
    """No session that Lem opens takes agterm's focus, also when it asks the owner a
    question: no text of Lem tells a session to take it, and a script selects a session
    only on the owner's own act, his pick in the picker (picker.py),
    `lem board --follow` (board.py) and his click on the board (`agterm_act`
    in serve.py)."""

    TEXTS = {".md", ".py", ".sh", ".toml", ".json", ".txt", ""}
    TAKE = re.compile(r"take[-_]focus")
    SELECT = re.compile(r"\"session\",\s*\"select\"")

    def files(self) -> Iterator[tuple[str, str]]:
        root = ROOT_OF_LEM
        for place in ("skills", "agents", "src"):
            for path in sorted((root / place).rglob("*")):
                if (
                    path.is_file()
                    and path.suffix in self.TEXTS
                    and "vendor" not in path.parts
                ):
                    yield (
                        path.relative_to(root).as_posix(),
                        path.read_text(encoding="utf-8", errors="replace"),
                    )

    def test_no_text_tells_a_session_to_take_the_focus(self) -> None:
        self.assertEqual(
            [
                f"{name}:{number}"
                for name, text in self.files()
                for number, line in enumerate(text.splitlines(), 1)
                if self.TAKE.search(line)
            ],
            [],
        )

    def test_a_script_selects_a_session_only_on_the_owners_act(self) -> None:
        self.assertEqual(
            sorted(
                name
                for name, text in self.files()
                if name.endswith(".py") and self.SELECT.search(text)
            ),
            [
                "src/lem/board.py",
                "src/lem/picker.py",
                "src/lem/serve.py",
            ],
        )


class Handoff(unittest.TestCase):
    def test_a_handoff_in_its_form(self) -> None:
        found = session.handoff_form(HANDOFF, SLUG)
        self.assertEqual(
            (found["from"], found["written"]), ("shape", "2026-11-21T10:05Z")
        )
        self.assertEqual(
            found["changed"],
            [
                {
                    "path": "docs/plans/2026-11-21-gift-note.md",
                    "status": "added, not committed",
                },
                {"path": "src/export.py", "status": "changed in 1a2b3c4"},
            ],
        )
        none = (
            HANDOFF.split("## Changed files", maxsplit=1)[0]
            + "## Changed files\n\nnone\n"
        )
        self.assertEqual(session.handoff_form(none, SLUG)["changed"], [])

    def test_the_template_reads_as_a_form_once_filled(self) -> None:
        template = (ROOT_OF_LEM / "skills/lem/templates/handoff.md").read_text(
            encoding="utf-8"
        )
        filled = (
            template.replace("SLUG", SLUG)
            .replace("PHASE", "build")
            .replace("YYYY-MM-DDTHH:MMZ", "2026-11-21T10:05Z")
        )
        self.assertEqual(
            session.handoff_form(filled, SLUG)["changed"],
            [{"path": "PATH/FROM/THE/ROOT", "status": "STATUS"}],
        )

    def test_each_missing_part_is_named(self) -> None:
        cases = [
            (
                HANDOFF.replace(
                    "task: gift-note · from shape", "task: gift-note · from talk"
                ),
                "a phase is one of",
            ),
            (
                HANDOFF.replace("task: gift-note", "task: coupon"),
                "names the task 'coupon'",
            ),
            ("## Settled\n\n- x\n", "a first line `task: gift-note · from PHASE"),
            (HANDOFF.replace("## Failed\n\n- none\n", ""), "## Failed"),
            (HANDOFF.replace("## Open\n\nnone\n", "## Open\n\n"), "## Open"),
            (
                HANDOFF + "- the export, somewhere\n",
                "a path and a status on each line of ## Changed files",
            ),
        ]
        for text, says in cases:
            with (
                self.subTest(says=says),
                self.assertRaises(session.SessionError) as raised,
            ):
                session.handoff_form(text, SLUG)
            self.assertIn(says, str(raised.exception))
            self.assertIn("templates/handoff.md", str(raised.exception))

    def test_a_part_s_heading_inside_a_code_fence_is_a_line_of_its_part(self) -> None:
        sample = "## Changed files\n- the export, somewhere\n## Failed\n- none"
        fenced = HANDOFF.replace(
            "- the criteria, approved (`criteria.json`)\n",
            "- the criteria, approved (`criteria.json`)\n\n"
            f"```markdown\n{sample}\n```\n",
        )
        # a sample in Settled is no part of its own: the changed files are the two
        # of the real part
        self.assertEqual(
            [each["path"] for each in session.handoff_form(fenced, SLUG)["changed"]],
            ["docs/plans/2026-11-21-gift-note.md", "src/export.py"],
        )
        # and a part that is only in a sample, in a tilde fence too, is missing
        for mark in ("```", "~~~~"):
            text = (
                fenced.replace("## Failed\n\n- none\n\n", "")
                .replace("```markdown", f"{mark}markdown")
                .replace("- none\n```\n", f"- none\n{mark}\n")
            )
            with (
                self.subTest(mark=mark),
                self.assertRaisesRegex(session.SessionError, "## Failed"),
            ):
                session.handoff_form(text, SLUG)


class Hooks(unittest.TestCase):
    """The hooks as Claude Code starts them, in a throwaway repository: silent with exit
    0 outside a task session."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.folder = tempfile.TemporaryDirectory()
        cls.repo = Path(cls.folder.name) / "shop"
        subprocess.run(["git", "init", "-q", str(cls.repo)], check=True)
        state = cls.repo / ".lem" / "state"
        directory = state / "tasks" / SLUG
        directory.mkdir(parents=True)
        (directory / "state.md").write_text(
            (
                "2026-11-21T10:06Z building: lead: builder\n"
                "type: feat, because the export gets a column\n\n"
                "2026-11-21T09:00Z held: the interview waits for the owner\n"
            ),
            encoding="utf-8",
        )
        (directory / "handoff.md").write_text(HANDOFF, encoding="utf-8")
        (state / "events.jsonl").write_text(
            json.dumps(
                {
                    "ts": "2026-11-21T10:07:00Z",
                    "event": "session.open",
                    "task": SLUG,
                    "phase": "build",
                }
            )
            + "\n",
            encoding="utf-8",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.folder.cleanup()

    def hook(
        self, event: dict, task: str | None = SLUG, pane: str | None = None
    ) -> subprocess.CompletedProcess:
        env = {
            key: value
            for key, value in os.environ.items()
            if key not in ("LEM_TASK", "AGTERM_SESSION_ID")
        }
        if task:
            env["LEM_TASK"] = task
        if pane:
            env["AGTERM_SESSION_ID"] = pane
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(ROOT_OF_LEM / "src/lem/python.py"),
                "session_hook",
            ],
            input=json.dumps({"cwd": str(self.repo), **event}),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_without_a_task_each_hook_is_silent(self) -> None:
        for event in (
            {"hook_event_name": "PreCompact", "trigger": "auto"},
            {"hook_event_name": "SessionStart", "source": "compact"},
        ):
            for task in (None, "no-such-task", "Not A Slug"):
                with self.subTest(event=event["hook_event_name"], task=task):
                    ran = self.hook(event, task)
                    self.assertEqual(
                        (ran.returncode, ran.stdout, ran.stderr), (0, "", "")
                    )

    def test_the_summary_gets_the_handoffs_form(self) -> None:
        ran = self.hook({"hook_event_name": "PreCompact", "trigger": "auto"})
        self.assertEqual(ran.returncode, 0)
        self.assertEqual(ran.stdout.strip(), session_hook.instructions(SLUG, "build"))
        self.assertIn(
            (
                "task gift-note, phase build, under five headings: Settled; Open; "
                "Next step; Failed; Changed files"
            ),
            ran.stdout,
        )

    def test_after_a_compaction_the_state_and_the_handoff_come_back(self) -> None:
        ran = self.hook({"hook_event_name": "SessionStart", "source": "compact"})
        self.assertEqual(ran.returncode, 0)
        self.assertIn(session_hook.TRUTH, ran.stdout)
        self.assertIn(
            (
                "2026-11-21T10:06Z building: lead: builder\n"
                "type: feat, because the export gets a column\n"
            ),
            ran.stdout,
        )
        self.assertNotIn("the interview waits", ran.stdout)
        self.assertIn("## handoff.md, written 20", ran.stdout)
        self.assertIn("The lead plans the export's column.", ran.stdout)
        started = self.hook({"hook_event_name": "SessionStart", "source": "startup"})
        self.assertEqual((started.returncode, started.stdout), (0, ""))

    def test_each_claude_session_of_the_task_is_logged_once(self) -> None:
        log = self.repo / ".lem" / "state" / "events.jsonl"
        before = log.read_text(encoding="utf-8")
        event = {
            "hook_event_name": "SessionStart",
            "source": "startup",
            "session_id": "c0ffee-1",
            "transcript_path": "/x/projects/-shop/c0ffee-1.jsonl",
        }
        try:
            for _ in range(2):
                ran = self.hook(event)
                self.assertEqual((ran.returncode, ran.stdout), (0, ""))
            self.hook({**event, "source": "compact"})
            self.hook(
                {"hook_event_name": "SessionStart", "source": "startup"},
                task="no-such-task",
            )
            records = [
                json.loads(line)
                for line in log.read_text(encoding="utf-8").splitlines()[
                    len(before.splitlines()) :
                ]
            ]
            self.assertEqual(
                [
                    (
                        r["event"],
                        r["task"],
                        r["claude"],
                        r["transcript"],
                        r["source"],
                        r["session"],
                    )
                    for r in records
                ],
                [
                    (
                        "session.transcript",
                        SLUG,
                        "c0ffee-1",
                        "/x/projects/-shop/c0ffee-1.jsonl",
                        "startup",
                        None,
                    )
                ],
            )
        finally:
            log.write_text(before, encoding="utf-8")

    def test_the_record_names_the_agterm_session_once_for_each_claude_id_and_session(
        self,
    ) -> None:
        log = self.repo / ".lem" / "state" / "events.jsonl"
        before = log.read_text(encoding="utf-8")
        event = {
            "hook_event_name": "SessionStart",
            "source": "startup",
            "session_id": "f0410fb9",
            "transcript_path": "/x/projects/-shop/f0410fb9.jsonl",
        }
        try:
            for _ in range(2):
                self.hook(event, pane="902B55C6-0001")
            # the same Claude id in a background host that runs with another pane's
            # environment is another record
            self.hook({**event, "source": "fork"}, pane="9F9C5C30-0002")
            records = [
                json.loads(line)
                for line in log.read_text(encoding="utf-8").splitlines()[
                    len(before.splitlines()) :
                ]
            ]
            self.assertEqual(
                [(r["claude"], r["session"], r["source"]) for r in records],
                [
                    ("f0410fb9", "902B55C6-0001", "startup"),
                    ("f0410fb9", "9F9C5C30-0002", "fork"),
                ],
            )
        finally:
            log.write_text(before, encoding="utf-8")


class Guard(unittest.TestCase):
    """The look once more of the guard of a stopped session (`guard_refusal`,
    `guard_check`), in the task's lock before each of its acts, and the three acts: the
    status message, the restart beside the old pane and the stop. The events are those
    of 2026-11-22 (merge-leaves-board-lock, #37)."""

    SIGNS = {"sign": "2026-11-22T10:15:42Z", "shell": False, "signs": True}
    NODES = [{"id": "S1", "name": SLUG, "workspace": "W1", "foreground": ["claude"]}]

    @staticmethod
    def ev(hhmm: str, event: str, **fields: object) -> dict:
        return {"ts": f"2026-11-22T{hhmm}:00Z", "event": event, "task": SLUG, **fields}

    def landing(self, status: str = "landing") -> list[dict]:
        return [
            self.ev(
                "01:33",
                "session.open",
                session="S1",
                name=SLUG,
                phase="land",
                why="handoff",
                workspace="W1",
            ),
            self.ev(
                "10:15",
                "task.state",
                status=status,
                text="the base moved: the checks run again",
                lines=[],
            ),
            self.ev(
                "10:54", "gate.end", result="passed", seconds=2156, tip="5ccc53d36"
            ),
            self.ev(
                "10:15",
                "session.transcript",
                claude="f0410fb9",
                transcript="/x/projects/-shop/f0410fb9.jsonl",
                session="S1",
                source="startup",
            ),
        ]

    def refusal(
        self,
        events: list[dict],
        step: str,
        at: str,
        named: str | None = "S1",
        **entry: object,
    ) -> str | None:
        bm = session.board_model()
        now = int(
            datetime.strptime(f"2026-11-22T{at}:00Z", "%Y-%m-%dT%H:%M:%SZ")
            .replace(tzinfo=UTC)
            .timestamp()
            * 1000
        )
        m = bm.derive(events, [], now)
        m.sessions = {
            SLUG: {
                "live": True,
                "agent": True,
                "unanswered": False,
                "session": "S1",
                **self.SIGNS,
                **entry,
            }
        }
        t = m.by_slug.get(SLUG)
        return session.guard_refusal(t if t and t.blocks else None, m, step, named)

    def test_each_step_acts_only_while_the_rule_still_gives_it(self) -> None:
        woken = [
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status"),
        ]
        self.assertIsNone(self.refusal(self.landing(), "status", "11:39"))
        self.assertEqual(self.refusal(self.landing(), "restart", "11:39"), "working")
        self.assertIsNone(self.refusal(woken, "restart", "11:49"))
        # the session wrote a turn since the server's look: no restart
        self.assertEqual(
            self.refusal(woken, "restart", "11:49", sign="2026-11-22T11:48:00Z"),
            "working",
        )
        self.assertEqual(self.refusal(woken, "status", "11:49"), "working")
        fresh = [
            *woken,
            self.ev(
                "11:49",
                "session.open",
                session="S1",
                name=SLUG,
                phase="land",
                why="stopped",
                workspace="W1",
            ),
            self.ev("12:34", "session.wake", session="S1", why="status"),
        ]
        self.assertIsNone(self.refusal(fresh, "stopped", "12:44", sign=None))
        self.assertEqual(
            self.refusal(
                [*fresh, self.ev("12:44", "session.stopped", session="S1")],
                "stopped",
                "12:45",
                sign=None,
            ),
            "working",
        )

    def test_a_task_out_of_its_phase_a_gone_or_other_session_and_signs_that_do_not_read(
        self,
    ) -> None:
        self.assertEqual(
            self.refusal(self.landing("held"), "status", "11:39"), "status"
        )
        self.assertEqual(
            self.refusal(self.landing("parked"), "status", "11:39"), "status"
        )
        self.assertEqual(
            self.refusal(self.landing(), "status", "11:39", named="S0"), "gone"
        )
        self.assertIsNone(self.refusal(self.landing(), "status", "11:39", named="s1"))
        self.assertEqual(
            self.refusal(self.landing(), "status", "11:39", live=False, agent=False),
            "gone",
        )
        # signs that do not read are facts of the rule, which gives them the message and
        # the stop, never a restart
        woken = [
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status", unread=True),
        ]
        self.assertIsNone(
            self.refusal(self.landing(), "status", "11:39", sign=None, signs=False)
        )
        self.assertIsNone(
            self.refusal(woken, "stopped", "11:49", sign=None, signs=False)
        )
        self.assertEqual(
            self.refusal(woken, "restart", "11:49", sign=None, signs=False), "unread"
        )
        self.assertEqual(
            self.refusal(woken, "restart", "11:49", named=None, sign=None, signs=False),
            "unread",
        )
        self.assertEqual(
            self.refusal(self.landing(), "status", "11:39", shell=True), "working"
        )
        self.assertEqual(self.refusal([], "status", "11:39"), "status")

    def test_the_status_message_is_never_a_wake_nobody_answered(self) -> None:
        # its line waits in the mailbox 20 minutes later, as an owner's wake's would:
        # only the owner's is `unanswered`, since the guard ends the status message's
        # wait itself, with the restart or the stop
        ago = (datetime.now(UTC) - timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%SZ")
        opened = {
            "ts": "2026-11-22T01:33:00Z",
            "event": "session.open",
            "task": SLUG,
            "session": "S1",
            "name": SLUG,
            "phase": "land",
            "why": "handoff",
        }

        def unanswered(why: str) -> bool:
            woke = {
                "ts": ago,
                "event": "session.wake",
                "task": SLUG,
                "session": "S1",
                "why": why,
            }
            with (
                mock.patch.object(
                    session,
                    "place",
                    return_value={"session": "", "socket": "", "window": ""},
                ),
                mock.patch.object(session, "tree", return_value=self.NODES),
                mock.patch.object(
                    session.project,
                    "events_named",
                    side_effect=lambda root, *names: [
                        e for e in (opened, woke) if e["event"] in names
                    ],
                ),
                mock.patch.object(session.project, "load", return_value={}),
                mock.patch.object(session.project, "read_tasks", return_value=[]),
                mock.patch.object(
                    session,
                    "ctl",
                    return_value=json.dumps([{"text": f"lem: {SLUG} {why}"}]),
                ),
            ):
                entry = session.cmd_list(ROOT)[0]
            # no transcript record of the session: its signs read nothing, and no
            # turn either
            self.assertEqual(
                {key: entry[key] for key in ("sign", "shell", "signs", "turn")},
                self.UNREAD,
            )
            return entry["unanswered"]

        self.assertEqual((unanswered("owner"), unanswered("status")), (True, False))

    def test_a_wake_a_parked_pane_took_with_no_turn_is_unanswered(self) -> None:
        # merge-leaves-board-lock (#37), 2026-11-22: its Claude Code process was parked
        # (`status: idle` since 10:45:48), and its own Stop hook took a wake's line out
        # of the mailbox at 15:53:31 with no turn of the agent
        woke = {
            "ts": "2026-11-22T15:53:30Z",
            "event": "session.wake",
            "task": SLUG,
            "session": "S1",
            "why": "owner",
        }
        parked = {"sign": "2026-11-22T10:45:48Z", "shell": False, "signs": True}

        def unanswered(
            signs: dict, at: str = "16:04", *, waits: bool = False, why: str = "owner"
        ) -> bool:
            return session.unanswered_of(
                {**woke, "why": why},
                signs,
                session.stamp(f"2026-11-22T{at}:00Z"),
                waits=lambda: waits,
            )

        self.assertTrue(unanswered(parked))
        self.assertTrue(unanswered({**parked, "sign": None}))
        # under 10 minutes after the wake
        self.assertFalse(unanswered(parked, at="16:03"))
        # a turn after the wake, or in its second: the session took it
        self.assertFalse(unanswered({**parked, "sign": "2026-11-22T15:55:02Z"}))
        self.assertFalse(unanswered({**parked, "sign": "2026-11-22T15:53:30Z"}))
        # signs that do not read: the mailbox alone, as before
        self.assertFalse(unanswered({**parked, "signs": False}))
        self.assertTrue(unanswered({**parked, "signs": False}, waits=True))
        # the guard's status message is never one, the guard ends its wait itself
        self.assertFalse(unanswered(parked, why="status"))
        self.assertFalse(unanswered(parked, why="status", waits=True))

    def test_a_wake_a_pane_took_while_a_turn_or_a_command_runs_is_not_taken(
        self,
    ) -> None:
        # the review's run of 2026-11-24: the wake at 11:39, an empty mailbox, and a
        # turn that began at 11:35 and still runs with a shell command; at 11:56 the
        # pane took the line into a turn that runs, and took no turn of its own after
        woke = {
            "ts": "2026-11-22T11:39:00Z",
            "event": "session.wake",
            "task": SLUG,
            "session": "S1",
            "why": "merged",
        }
        busy = {"sign": "2026-11-22T11:35:00Z", "signs": True}

        def case(**signs: object) -> dict | None:
            return session.unheard_of(
                woke,
                {**busy, **signs},
                session.stamp("2026-11-22T11:56:00Z"),
                waits=lambda: False,
            )

        runs = {"why": "merged", "line": "runs"}
        self.assertEqual(case(turn="runs", shell=True), runs)
        self.assertEqual(case(turn="runs", shell=False), runs)
        self.assertEqual(case(turn="ended", shell=True), runs)
        self.assertEqual(
            case(turn="ended", shell=False), {"why": "merged", "line": "taken"}
        )
        self.assertEqual(
            case(turn=None, shell=False), {"why": "merged", "line": "taken"}
        )

    def test_lem_session_list_reads_the_signs_for_a_wake_no_mailbox_holds(
        self,
    ) -> None:
        ago = datetime.now(UTC) - timedelta(minutes=11)
        woke = {
            "ts": ago.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event": "session.wake",
            "task": SLUG,
            "session": "S1",
            "why": "owner",
        }
        opened = {
            "ts": "2026-11-22T01:33:00Z",
            "event": "session.open",
            "task": SLUG,
            "session": "S1",
            "name": SLUG,
            "phase": "land",
            "why": "handoff",
        }

        def unanswered(minutes: int, mailbox: str = "[]") -> bool:
            sign = (ago + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
            with (
                mock.patch.object(
                    session,
                    "place",
                    return_value={"session": "", "socket": "", "window": ""},
                ),
                mock.patch.object(session, "tree", return_value=self.NODES),
                mock.patch.object(
                    session.project,
                    "events_named",
                    side_effect=lambda root, *names: [
                        e for e in (opened, woke) if e["event"] in names
                    ],
                ),
                mock.patch.object(session.project, "load", return_value={}),
                mock.patch.object(session.project, "read_tasks", return_value=[]),
                # the parked pane's Stop hook took the line: the mailbox is empty
                mock.patch.object(session, "ctl", return_value=mailbox),
                mock.patch.object(
                    session.lem_signs,
                    "signs_of",
                    return_value={
                        "sign": sign,
                        "shell": False,
                        "signs": True,
                        "turn": "ended",
                    },
                ),
            ):
                entry = session.cmd_list(ROOT)[0]
                # which of the two cases, beside `unanswered`, whose meaning stays
                unheard[minutes, mailbox] = entry["unheard"]
                return entry["unanswered"]

        unheard: dict = {}
        # the newest turn 5 hours before the wake, or 2 minutes after it
        self.assertEqual((unanswered(-300), unanswered(2)), (True, False))
        waits = json.dumps([{"text": f"lem: {SLUG} owner"}])
        self.assertTrue(unanswered(-300, waits))
        self.assertEqual(
            unheard,
            {
                (-300, "[]"): {"why": "owner", "line": "taken"},
                (2, "[]"): None,
                (-300, waits): {"why": "owner", "line": "waits"},
            },
        )

    def test_the_owners_open_of_a_stopped_task_acts_until_its_session_works_again(
        self,
    ) -> None:
        stopped = [
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status"),
            self.ev(
                "11:49",
                "session.open",
                session="S1",
                name=SLUG,
                phase="land",
                why="stopped",
                workspace="W1",
            ),
            self.ev("12:34", "session.wake", session="S1", why="status"),
            self.ev("12:44", "session.stopped", session="S1"),
        ]
        self.assertIsNone(
            self.refusal(stopped, "restart", "13:30", named=None, sign=None)
        )
        self.assertEqual(
            self.refusal(
                stopped, "restart", "13:30", named=None, sign="2026-11-22T13:00:00Z"
            ),
            "working",
        )

    UNREAD = {"sign": None, "shell": False, "signs": False, "turn": None}

    def test_the_guards_look_at_a_task_out_of_its_phase_reads_no_signs_and_no_turn(
        self,
    ) -> None:
        seen = []
        real = session.guard_refusal

        def spy(
            t: "lem_board_model.Task | None",
            m: "lem_board_model.Model",
            step: str,
            named: object,
        ) -> str | None:
            if m.sessions is None:
                self.fail("the guard's model holds no sessions")
            seen.append(dict(m.sessions[SLUG]))
            return real(t, m, step, named)

        with mock.patch.object(session, "guard_refusal", side_effect=spy):
            refused, _, _ = self.run_act(
                self.landing("held"),
                lambda: cast(
                    "dict", session.guard_check(ROOT, SLUG, "status", "S1", {})
                ),
            )[0]
        self.assertEqual(refused["why"], "status")
        self.assertEqual(
            {key: seen[0][key] for key in ("sign", "shell", "signs", "turn")},
            self.UNREAD,
        )

    def unread_stop(self) -> list[dict]:
        return [
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status", unread=True),
            self.ev("11:49", "session.stopped", session="S1", unread=True),
        ]

    def test_the_owners_open_of_an_unread_stop_acts_and_a_named_restart_over_a_standing_stop_never_does(
        self,
    ) -> None:
        # his click names no session; a turn's time beside signs that do not read is no
        # sign of work
        self.assertIsNone(
            self.refusal(
                self.unread_stop(),
                "restart",
                "12:30",
                named=None,
                sign=None,
                signs=False,
            )
        )
        self.assertIsNone(
            self.refusal(
                self.unread_stop(),
                "restart",
                "12:30",
                named=None,
                sign="2026-11-22T12:00:00Z",
                signs=False,
            )
        )
        # the server's duty names one: it refuses in both paths
        self.assertEqual(
            self.refusal(
                self.unread_stop(), "restart", "11:50", sign=None, signs=False
            ),
            "unread",
        )
        self.assertEqual(
            self.refusal(self.unread_stop(), "restart", "11:50"), "working"
        )
        # a work event after the status message ends the stop, and with it the open
        worked = [
            *self.unread_stop(),
            self.ev(
                "12:00",
                "task.state",
                status="landing",
                text="the checks run again",
                lines=[],
            ),
        ]
        self.assertEqual(
            self.refusal(
                worked, "restart", "12:30", named=None, sign=None, signs=False
            ),
            "unread",
        )

    # the writer of the record, which the release after this one turns on
    @mock.patch("lem.board_model.WRITES_WORKED", True)
    def test_a_turn_read_after_an_unread_stop_is_logged_once_and_the_open_agrees(
        self,
    ) -> None:
        # the session takes a turn at 11:55 with no state block, and the signs read
        # again: the row says stopped, and the owner's open is refused as `working`
        turned = {"sign": "2026-11-22T11:55:00Z"}
        self.assertEqual(
            self.refusal(self.unread_stop(), "restart", "11:56", named=None, **turned),
            "working",
        )
        self.assertIsNone(self.refusal(self.unread_stop(), "worked", "11:56", **turned))
        self.assertEqual(
            self.refusal(self.unread_stop(), "worked", "11:56", named="S0", **turned),
            "gone",
        )
        self.assertEqual(
            self.refusal(self.unread_stop(), "worked", "11:56", sign=None, signs=False),
            "working",
        )
        done, sent, logged = self.run_act(
            self.unread_stop(),
            lambda: session.cmd_worked(ROOT, SLUG, "S1"),
            signs={**self.SIGNS, **turned},
            at="11:56",
        )
        self.assertEqual(
            (done["acted"], sent, logged[0]["event"]),
            (True, [], "session.worked"),
        )
        self.assertEqual(
            {key: logged[0][key] for key in ("session", "turn")},
            {"session": "S1", "turn": "2026-11-22T11:55:00Z"},
        )
        self.assertEqual(
            done["say"],
            (
                f"the session of {SLUG} took a turn at 2026-11-22T11:55:00Z, after "
                "the status message Lem sent while it could not read the session: "
                "no stop of the task waits for the owner, and the guard's clock "
                "counts from that turn"
            ),
        )
        worked = [*self.unread_stop(), *logged]
        # once: a second look, a second server or a peer that asks again acts on
        # nothing
        again, _, twice = self.run_act(
            worked,
            lambda: session.cmd_worked(ROOT, SLUG, "S1"),
            signs={**self.SIGNS, **turned},
            at="11:57",
        )
        self.assertEqual((again["acted"], again["why"], twice), (False, "working", []))
        # no stop stands, so the owner's open is refused as the board offers none
        bm = session.board_model()
        m = bm.derive(worked, [], bm.at("2026-11-22T11:57:00Z") or 0)
        m.sessions = {
            SLUG: {
                "live": True,
                "agent": True,
                "unanswered": False,
                "session": "S1",
                **self.SIGNS,
                **turned,
            }
        }
        t = m.by_slug[SLUG]
        self.assertEqual(
            (
                bm.stopped_of(t, m),
                bm.opens_session(t, m),
                self.refusal(worked, "restart", "11:57", named=None, **turned),
            ),
            (None, False, "working"),
        )

    def test_a_turn_after_an_unread_stop_gets_one_newer_stop_whose_open_acts(
        self,
    ) -> None:
        # review 2 of guard-sees-unreadable-sessions (#60): the session takes a turn at
        # 12:00 with no state block, its signs read again, the server's look logs the
        # turn (`session.worked`), and the readable clock sends its own message at
        # 12:45: no fresh session comes by itself in the run of work of the stop of
        # 11:49
        bm = session.board_model()
        turned = {"sign": "2026-11-22T12:00:00Z"}
        woken = [
            *self.unread_stop(),
            self.ev(
                "12:01", "session.worked", session="S1", turn="2026-11-22T12:00:00Z"
            ),
            self.ev("12:45", "session.wake", session="S1", why="status"),
        ]
        self.assertEqual(
            self.refusal(woken, "restart", "12:55", named=None, **turned), "working"
        )
        # one newer stop is due, never a restart, and the server's look takes it
        self.assertIsNone(self.refusal(woken, "stopped", "12:55", **turned))
        self.assertEqual(self.refusal(woken, "restart", "12:55", **turned), "working")
        # the stop's words name no fresh session, since none was opened
        done, _, logged = self.run_act(
            woken,
            lambda: session.cmd_stopped(ROOT, SLUG, "S1"),
            signs={**self.SIGNS, **turned},
            at="12:55",
        )
        self.assertEqual(
            [(e["event"], e.get("unread")) for e in logged],
            [("session.stopped", None)],
        )
        self.assertEqual(
            done["say"],
            (
                f"the stop of {SLUG} is logged: its session showed no sign of work "
                "after the status message, and Lem opened no fresh session by itself, "
                "since the task already stopped once after its last work, so it waits "
                "for the owner, "
                f"whose `lem session open {SLUG} --why stopped` opens a fresh session"
            ),
        )
        stopped = [*woken, self.ev("12:55", "session.stopped", session="S1")]
        # the owner's "Open a session" acts again, and the guard gives nothing more
        self.assertIsNone(
            self.refusal(stopped, "restart", "12:56", named=None, **turned)
        )
        # a turn after the newer stop: the click waits for the next stop, as for every
        # readable stop
        self.assertEqual(
            self.refusal(
                stopped, "restart", "13:10", named=None, sign="2026-11-22T13:00:00Z"
            ),
            "working",
        )
        for at in ("12:56", "17:00"):
            m = bm.derive(stopped, [], bm.at(f"2026-11-22T{at}:00Z") or 0)
            m.sessions = {
                SLUG: {
                    "live": True,
                    "agent": True,
                    "unanswered": False,
                    "session": "S1",
                    **self.SIGNS,
                    **turned,
                }
            }
            self.assertIsNone(bm.stop_due(m.by_slug[SLUG], m), at)

    def test_a_pane_that_agterm_has_not_drawn_is_no_agent_for_any_step(self) -> None:
        drawn = [{"id": "S1", "name": SLUG, "workspace": "W1", "realized": False}]
        woken = [
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status"),
        ]
        fresh = [
            *woken,
            self.ev(
                "11:49",
                "session.open",
                session="S1",
                name=SLUG,
                phase="land",
                why="stopped",
                workspace="W1",
            ),
            self.ev("12:34", "session.wake", session="S1", why="status"),
        ]
        for step, events, act, at in (
            (
                "status",
                self.landing(),
                lambda: session.cmd_wake(ROOT, SLUG, "status", None, "S1"),
                "11:39",
            ),
            (
                "restart",
                woken,
                lambda: session.cmd_open(ROOT, SLUG, "stopped", named="S1"),
                "11:49",
            ),
            ("stopped", fresh, lambda: session.cmd_stopped(ROOT, SLUG, "S1"), "12:44"),
        ):
            done, sent, logged = self.run_act(events, act, nodes=drawn, at=at)
            self.assertEqual(
                (done["acted"], done["why"], sent, logged),
                (False, "gone", [], []),
                step,
            )

    def test_the_status_message_and_the_stop_of_a_session_lem_cannot_read_say_so_on_their_records(
        self,
    ) -> None:
        done, sent, logged = self.run_act(
            self.landing(),
            lambda: session.cmd_wake(ROOT, SLUG, "status", None, "S1"),
            signs=self.UNREAD,
            at="11:39",
        )
        self.assertEqual(
            (done["acted"], sent),
            (True, [("msg", "send", f"lem: {SLUG} status", "--to", "S1:left")]),
        )
        self.assertEqual(
            [(e["event"], e["session"], e["why"], e.get("unread")) for e in logged],
            [("session.wake", "S1", "status", True)],
        )
        woken = [
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status", unread=True),
        ]
        done, sent, logged = self.run_act(
            woken,
            lambda: session.cmd_stopped(ROOT, SLUG, "S1"),
            signs=self.UNREAD,
            at="11:49",
        )
        self.assertEqual((done["acted"], sent), (True, []))
        self.assertEqual(
            [(e["event"], e["session"], e.get("unread")) for e in logged],
            [("session.stopped", "S1", True)],
        )
        self.assertIn("Lem cannot read its session's signs of work", done["say"])
        self.assertIn("waits for the owner", done["say"])
        # a readable wake and stop carry no such field
        _, _, logged = self.run_act(
            self.landing(),
            lambda: session.cmd_wake(ROOT, SLUG, "status", None, "S1"),
            at="11:39",
        )
        self.assertNotIn("unread", logged[0])

    def test_a_stop_logged_after_a_state_block_of_the_same_moment_says_that_nothing_waits(
        self,
    ) -> None:
        woken = [
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status", unread=True),
        ]
        check = session.guard_check

        def raced(
            root: Path, slug: str, step: str, named: str | None, where: dict
        ) -> tuple[dict | None, str | None, bool]:
            # the session appends its state block under the log's lock, between the look
            # and the stop
            found = check(root, slug, step, named, where)
            project.append_event(
                ROOT,
                "task.state",
                SLUG,
                {
                    "status": "landing",
                    "text": "the pull request waits for its checks",
                    "lines": [],
                },
            )
            return found

        with mock.patch.object(session, "guard_check", side_effect=raced):
            done, _, logged = self.run_act(
                woken,
                lambda: session.cmd_stopped(ROOT, SLUG, "S1"),
                signs=self.UNREAD,
                at="11:49",
            )
        self.assertEqual(
            [e["event"] for e in logged], ["task.state", "session.stopped"]
        )
        self.assertTrue(done["acted"])
        self.assertIn(
            "the stop does not stand and nothing waits for the owner", done["say"]
        )

    def run_act(
        self,
        events: list[dict],
        act: Callable[[], dict],
        signs: dict | None = None,
        nodes: list | None = None,
        at: str = "15:37",
    ) -> tuple[dict, list, list]:
        now = int(
            datetime.strptime(f"2026-11-22T{at}:00Z", "%Y-%m-%dT%H:%M:%SZ")
            .replace(tzinfo=UTC)
            .timestamp()
            * 1000
        )
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder)
            (state / "events.jsonl").write_text(
                "".join(json.dumps(e) + "\n" for e in events), encoding="utf-8"
            )
            sent = []

            def ctl(where: dict, *args: str, window: bool = True) -> str:
                sent.append(args)
                return (
                    json.dumps({"result": {"id": "S2"}})
                    if args[:2] == ("session", "new")
                    else ""
                )

            facts = {
                "task": {"slug": SLUG, "state": "", "status": "landing"},
                "tasks": [],
                "phase": "land",
                "worktree": None,
                "settings": {"seats": {"session": {}}},
            }
            with (
                mock.patch.object(
                    session,
                    "place",
                    return_value={"session": "", "socket": "", "window": ""},
                ),
                mock.patch.object(
                    session, "tree", return_value=self.NODES if nodes is None else nodes
                ),
                mock.patch.object(session, "ctl", side_effect=ctl),
                mock.patch.object(session, "process_table", return_value="table"),
                mock.patch.object(
                    session.lem_signs, "signs_of", return_value=signs or self.SIGNS
                ),
                mock.patch.object(session, "facts_of", return_value=facts),
                mock.patch.object(session, "login_shell", return_value="/bin/zsh"),
                mock.patch.object(
                    session.lem_state, "handoff_tokens", return_value=None
                ),
                mock.patch.object(project, "register_checkout"),
                mock.patch.object(project, "task_directory", return_value=state),
                mock.patch.object(project, "state_root", return_value=state),
                mock.patch.object(project, "main_checkout", return_value=state),
                mock.patch.object(session.board_model(), "now_ms", return_value=now),
            ):
                result = act()
                logged = [
                    json.loads(line)
                    for line in (state / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                ][len(events) :]
        return result, sent, logged

    def test_the_status_message_goes_to_the_live_session_and_never_opens_one(
        self,
    ) -> None:
        done, sent, logged = self.run_act(
            self.landing(),
            lambda: session.cmd_wake(ROOT, SLUG, "status", None, "S1"),
            at="11:39",
        )
        self.assertEqual(
            (done["acted"], done["woke"], done["opened"]), (True, True, False)
        )
        self.assertEqual(
            sent, [("msg", "send", f"lem: {SLUG} status", "--to", "S1:left")]
        )
        self.assertEqual(
            [(e["event"], e["session"], e["why"]) for e in logged],
            [("session.wake", "S1", "status")],
        )
        # a pane that is gone gets no message and no session in its place
        gone, sent, logged = self.run_act(
            self.landing(),
            lambda: session.cmd_wake(ROOT, SLUG, "status", None, "S1"),
            nodes=[],
        )
        self.assertEqual(
            (gone["acted"], gone["why"], sent, logged), (False, "gone", [], [])
        )

    def test_a_sign_of_work_since_the_look_makes_the_act_act_on_nothing(self) -> None:
        woken = [
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status"),
        ]
        late = {**self.SIGNS, "sign": "2026-11-22T11:48:30Z"}
        done, sent, logged = self.run_act(
            woken,
            lambda: session.cmd_open(ROOT, SLUG, "stopped", named="S1"),
            signs=late,
            at="11:49",
        )
        self.assertEqual(
            (done["acted"], done["why"], sent, logged), (False, "working", [], [])
        )
        self.assertIn("Lem did nothing for gift-note", done["say"])

    def test_the_restart_opens_beside_the_old_pane_and_tells_it(self) -> None:
        woken = [
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status"),
        ]
        done, sent, logged = self.run_act(
            woken,
            lambda: session.cmd_open(ROOT, SLUG, "stopped", named="S1"),
            at="11:49",
        )
        self.assertEqual(
            (done["acted"], done["session"], done["old"], done["told"]),
            (True, "S2", "S1", True),
        )
        self.assertEqual(
            [args[:2] for args in sent],
            [
                ("session", "new"),
                ("session", "move"),
                ("session", "rename"),
                ("msg", "send"),
            ],
        )
        self.assertEqual(
            sent[2], ("session", "rename", f"{SLUG} · replaced", "--target", "S1")
        )
        self.assertEqual(
            sent[3], ("msg", "send", f"lem: {SLUG} replaced", "--to", "S1:left")
        )
        self.assertEqual(
            [(e["event"], e["session"], e["why"]) for e in logged],
            [("session.open", "S2", "stopped"), ("session.wake", "S1", "replaced")],
        )

    def test_the_stop_is_logged_with_its_session(self) -> None:
        fresh = [
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status"),
            self.ev(
                "11:49",
                "session.open",
                session="S1",
                name=SLUG,
                phase="land",
                why="stopped",
                workspace="W1",
            ),
            self.ev("12:34", "session.wake", session="S1", why="status"),
        ]
        done, sent, logged = self.run_act(
            fresh,
            lambda: session.cmd_stopped(ROOT, SLUG, "S1"),
            signs={**self.SIGNS, "sign": None},
            at="12:44",
        )
        self.assertEqual((done["acted"], sent), (True, []))
        self.assertEqual(
            [(e["event"], e["session"]) for e in logged], [("session.stopped", "S1")]
        )
        # after a spent restart, the stop says so
        self.assertIn(
            "no sign of work after the status message and after its restart",
            done["say"],
        )
        again, _, logged = self.run_act(
            [*fresh, self.ev("12:44", "session.stopped", session="S1")],
            lambda: session.cmd_stopped(ROOT, SLUG, "S1"),
            at="12:45",
        )
        self.assertEqual((again["acted"], logged), (False, []))

    def test_session_goes_only_with_the_guards_steps(self) -> None:
        with (
            mock.patch.object(sys, "argv", ["session.py"]),
            self.assertRaises(SystemExit) as raised,
            mock.patch.object(project, "repo_root", return_value=ROOT),
        ):
            session.main(["open", SLUG, "--why", "owner", "--session", "S1"])
        self.assertIn("--session goes with `open --why stopped`", str(raised.exception))


class ProcessTable(unittest.TestCase):
    def test_a_command_line_that_is_not_utf_8_changes_one_character_of_its_line(
        self,
    ) -> None:
        # one process of the machine, of any owner, had the byte 0xff in its command
        # line (2026-11-23)
        with tempfile.TemporaryDirectory() as folder:
            ps = Path(folder) / "ps"
            ps.write_text(
                (
                    f"#!{sys.executable}\nimport sys\nsys.stdout.buffer.write(b'  101  "
                    "   1 /usr/bin/claude\\n  202   101 odd-\\xffname --flag\\n')\n"
                ),
                encoding="utf-8",
            )
            ps.chmod(0o755)
            with mock.patch.dict(
                os.environ,
                {"PATH": f"{folder}{os.pathsep}{os.environ.get('PATH', '')}"},
            ):
                table = session.process_table()
        self.assertEqual(
            table, "  101     1 /usr/bin/claude\n  202   101 odd-�name --flag\n"
        )


if __name__ == "__main__":
    unittest.main()
