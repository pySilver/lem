"""The rules of the board of one task (lem_board_model.py, lem_board_task.py), each called over a few
events: where the time went, the criteria as they stand and their checks, which decisions are important
and what a reason of not green says, what the task waits for, the head of its large card, its progress,
and the artifacts the panel reads; and that a task's text reaches the page escaped.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import re
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
bm = importlib.import_module("lem_board_model")
task_pages = importlib.import_module("lem_board_task")
lem_artifacts = importlib.import_module("lem_artifacts")
pages = importlib.import_module("lem_board_pages")

START = datetime(2026, 11, 20, 9, 0, tzinfo=timezone.utc)
NOW = int((START + timedelta(hours=2)).timestamp() * 1000)


def ms(minute: float) -> int:
    return int((START + timedelta(minutes=minute)).timestamp() * 1000)


def ev(minute: float, event: str, task: str = "gift-note", **fields) -> dict:
    return {"ts": (START + timedelta(minutes=minute)).strftime("%Y-%m-%dT%H:%M:%SZ"), "event": event, "task": task, **fields}


def state(minute: float, status: str, text: str, *lines: str, task: str = "gift-note") -> dict:
    return ev(minute, "task.state", task, status=status, text=text, lines=list(lines))


def model(*events: dict, owner=()):
    return bm.derive(list(events), list(owner), NOW)


def one(*events: dict, **kw) -> "bm.Task":
    return model(*events, **kw).tasks[0]


def spans(t, row: str | None = None, meta=None, end=None) -> list[tuple]:
    tm = bm.time_of(t, end if end is not None else bm.time_end(t, NOW), meta or {"gates": 2, "serial": 0})
    return [(g["row"], g["from"], g["to"], g["head"], g["live"]) for g in tm["spans"] if row is None or g["row"] == row]


class Time(unittest.TestCase):
    def test_a_builders_span_leaves_the_brief_and_the_report_to_the_agent(self):
        t = one(state(0, "building", "task 1 of 2"), ev(5, "builder.start", job="task 1 of 2"), state(30, "building", "task 2 of 2"))
        self.assertIn(("lead", ms(0), ms(5), "It briefs the builder", False), spans(t))
        self.assertIn(("builders", ms(5), ms(30), "Task 1 of 2", False), spans(t))

    def test_a_stopped_run_of_the_checks_ends_at_its_end_and_the_time_after_it_is_lems(self):
        t = one(state(0, "landing", "the checks start"), ev(1, "gate.start", tip="4c1d2e3f5", commands=2),
                ev(5, "gate.end", result="stopped", seconds=240, tip="4c1d2e3", say="gift-note: the checks were stopped; the landing waits for your word"))
        checks = spans(t, "checks")
        self.assertEqual(checks, [("checks", ms(1), ms(5), "The checks were stopped", False)])
        self.assertEqual(spans(t, "lem")[-1][3:], ("The checks were stopped: the landing waits for your word", True))

    def test_a_refused_run_names_what_was_refused_and_keeps_its_commands(self):
        t = one(state(0, "landing", "the checks start"), ev(1, "gate.start", tip="4c1d2e3f5", commands=2),
                ev(2, "gate", command="make test", exit=0, last="ok", tip="4c1d2e3"),
                ev(2, "gate.end", result="refused", seconds=60, tip="4c1d2e3", say="gift-note: the checks refused the change: tests/x.py changed; a builder repairs it, nothing for you"))
        tm = bm.time_of(t, bm.time_end(t, NOW), {"gates": 2})
        end = next(g for g in tm["spans"] if g["head"] == "The checks refused the change")
        self.assertEqual(end["sub"], "tests/x.py changed · 1 of 2 commands done · 1m 00s")
        self.assertIn(("checks", ms(1), ms(2), "The checks: make test", False), spans(t, "checks"))

    def test_a_breaker_holds_the_task_for_the_owner_and_a_carried_over_event_takes_no_time(self):
        t = one(ev(0, "interview.start", **{"from": "old-note"}), state(0, "building", "task 1 of 2"),
                state(10, "held", "breaker 1 waits for the owner", "w: why"), state(25, "building", "task 1 of 2"))
        self.assertIn(("you", ms(10), ms(25), "The build stopped: its breaker waits for you", False), spans(t, "you"))
        self.assertNotIn("The interview", [g[3] for g in spans(t)])

    def test_a_read_whose_start_is_not_logged_is_a_mark_where_it_ended(self):
        t = one(state(0, "held", "the criteria wait for the owner"), ev(5, "criteria.read", by="lem", asked=3, answered=3, families=["opus"], flagged=0, digest="d"))
        tm = bm.time_of(t, bm.time_end(t, NOW))
        self.assertEqual([(x["row"], x["at"]) for x in tm["marks"]], [("personas", ms(5))])

    def test_shares_say_when_two_rows_held_the_same_minutes(self):
        t = one(state(0, "building", "lead: builder"), ev(0, "plan.talk.start", reviewer="codex"),
                ev(60, "plan.talk", reviewer="codex", turns=4, questions=1, settled=1, open=0, repaired=1), state(60, "landed", "merged"))
        tm = bm.time_of(t, bm.time_end(t, NOW))
        shares = bm.time_shares(tm, bm.time_rows(tm))
        self.assertEqual((shares["share"]["review"], shares["share"]["lead"], shares["over"]), (100, 100, 200))

    def test_a_tick_names_its_date_only_where_the_day_changes(self):
        late = ms(14 * 60 + 50)  # 23:50 local time or so: the next tick is another day in any zone east of it
        self.assertEqual(bm.tick_label(late, 3600000, late), bm.local(late).strftime("%H:%M"))
        self.assertTrue(bm.tick_label(late + 86400000, 3600000, late).startswith(bm.day_label(late + 86400000)))


class Criteria(unittest.TestCase):
    def approval(self, minute, number, texts, by="owner", digest="d1"):
        return ev(minute, "criteria.approved", by=by, number=number, size="full", why="w", digest=digest, criteria=[{"n": i, "text": x} for i, x in enumerate(texts, 1)])

    def test_the_criteria_stand_as_approved_with_each_change_of_the_build_applied(self):
        t = one(state(0, "building", "lead: builder"), self.approval(1, 1, ["one", "two"]),
                ev(5, "decision.criterion", change=1, how="changed", criterion=2, was="two", now="two, said again", why="w", by="lead", approval=1))
        self.assertEqual(bm.standing(t)["texts"], ["one", "two, said again"])
        self.assertIsNone(bm.standing(t)["digest"])

    def test_a_read_is_stale_when_the_owner_approved_other_criteria_after_it(self):
        t = one(state(0, "held", "the criteria wait for the owner"), ev(2, "criteria.read", by="lem", asked=3, answered=3, families=["opus"], flagged=0, digest="d1", criteria=1),
                self.approval(1, 1, ["one"], digest="d1"), self.approval(5, 2, ["one, sharper"], digest="d2"))
        self.assertEqual(bm.read_stale(t, t.reads[-1]), "The criteria changed after this read by your approval 2, and the change was not read.")

    def test_a_check_counts_only_for_the_criteria_it_ran_on(self):
        crit = ev(1, "task.criteria", size="full", why="w", digest="d1", criteria=[{"n": 1, "text": "one", "tests": [{"command": "make t"}]}])
        held = one(state(0, "building", "lead: builder"), crit, ev(3, "task.red", ok=True, digest="d1", tip="abc", tests=[{"criterion": 1, "command": "make t"}]))
        stale = one(state(0, "building", "lead: builder"), crit, ev(3, "task.red", ok=True, digest="old", tests=[{"criterion": 1, "command": "make t"}]))
        bad = one(state(0, "building", "lead: builder"), crit, ev(3, "task.red", ok=False, digest="d1", tests=[{"criterion": 1, "command": "make t", "problem": "it passes on the base"}]))
        self.assertEqual(bm.criterion_checks(held)[0]["state"], "done")
        self.assertEqual(bm.criterion_checks(stale)[0]["tests"], [("make t", "not checked yet")])
        self.assertEqual((bm.criterion_checks(bad)[0]["state"], bm.criterion_checks(bad)[0]["tests"][0][1]), ("bad", "it passes on the base"))


class Decisions(unittest.TestCase):
    def test_a_pick_past_the_personas_an_unsettled_pick_a_named_one_and_his_help_are_important_and_a_breaker_is_not(self):
        t = one(state(0, "building", "lead: builder"),
                ev(1, "decision.taken", id=1, what="w", chose="x", why="y", by="dialectic"),
                ev(2, "decision.taken", id=2, what="w", chose="x", why="y", by="lead", levels={"experts": "both picked x"}),
                ev(3, "decision.taken", id=3, what="w", chose="x", why="y", by="lead", unsettled=True),
                ev(4, "decision.taken", id=4, what="w", chose="x", why="y", by="lead"),
                ev(5, "decision.breaker", id=5, cause="irreversible", irreversible="person", what="The mail goes to 40 merchants", document="breaker.md"),
                ev(6, "decision.taken", id=6, what="w", chose="x", why="y", by="personas"),
                ev(9, "proposed", green=False, not_green=['decision 6 was taken without the owner (w): "x", by the personas']))
        self.assertEqual([d.id for d in bm.important_of(t)], [1, 2, 3, 6])
        self.assertEqual(bm.importance(t, t.decisions[2]), "it went past the personas: the experts answered it")
        self.assertEqual(bm.stop_words(t.decisions[5]), "the next step cannot be undone by a later “no”: it sends something to a person")

    def test_a_short_label_finds_the_option_only_when_one_option_has_it(self):
        d = bm.Decision(id=1, kind="taken", ts=0, chose="D: the backlog, by keys", options=["C: the board", "D: the backlog is patched by keys"])
        self.assertEqual(bm.chosen_at(d), 1)
        d.options.append("D: something else")
        self.assertEqual(bm.chosen_at(d), -1)


class Overview(unittest.TestCase):
    def test_a_queued_task_waits_for_the_task_it_needs(self):
        m = model(state(0, "queued", "it waits", "after: card-foot"))
        self.assertEqual(bm.waits_for(m.tasks[0], bm.waits_of(m)), {"you": False, "text": "It starts after “Card foot” ends", "where": None})

    def test_a_queued_task_waits_for_another_task_by_a_need_or_by_the_owners_order(self):
        # "another task" is true of both: the board reads no line for which of the two it is
        for first in ("it needs the export's column", 'the owner\'s order: "After card-foot: unit cases"'):
            with self.subTest(first=first):
                t = one(state(0, "queued", first, "after: card-foot", "then: the interview"))
                self.assertEqual(bm.now_head(t), "Waits for another task")
                self.assertEqual(spans(t, "lem")[0][3], "Queued: it waits for another task")
        alone = one(state(0, "queued", "it waits", "then: the lead"))
        self.assertEqual((bm.now_head(alone), spans(alone, "lem")[0][3]), ("Waits to start", "Queued: it waits to start"))

    def test_an_interview_whose_criteria_the_personas_read_waits_for_nothing_of_his(self):
        m = model(state(0, "held", "the interview waits for the owner"), ev(1, "interview.start"), ev(10, "criteria.read.start", by="lem"))
        self.assertEqual(bm.waits_for(m.tasks[0], bm.waits_of(m)), None)
        self.assertEqual(pages.summary_of(m), "1 with the personas’ read of its criteria")

    def test_the_bar_counts_an_interview_whose_criteria_lem_writes_and_one_it_shapes_without_him(self):
        interview = (state(0, "held", "the interview waits for the owner"), ev(1, "interview.start"))
        self.assertEqual(pages.summary_of(model(*interview, ev(5, "interview.end"))), "1 whose criteria Lem writes")
        away = {"ts": "2026-11-20T09:02:00Z", "event": "owner", "away": True, "words": "out"}
        self.assertEqual(pages.summary_of(model(*interview, owner=[away])), "1 that Lem shapes without you")

    def test_the_large_card_says_how_a_stopped_run_ended_and_never_that_the_checks_run(self):
        t = one(state(0, "landing", "the checks start"), ev(1, "gate.start", tip="4c1d2e3f5", commands=2), ev(2, "gate.end", result="stopped", seconds=60))
        self.assertEqual(bm.now_head(t), "The checks were stopped")
        self.assertEqual(bm.now_head(one(state(0, "landing", "the checks start"))), "It starts its landing: the rebase onto the base, then the polish pass, before the checks")

    def test_what_we_are_building_says_nothing_of_filed_items_after_an_end_with_none(self):
        closed = one(state(0, "landed", "merged"))
        self.assertIsNone(bm.building_of(closed, {"outcome": "", "filed": []}))
        self.assertEqual(bm.building_of(one(state(0, "building", "lead: builder")), {"outcome": "One.\n\nTwo.", "filed": []})["outcome"], "One.\n\nTwo.")

    def test_the_breakers_document_is_first_on_the_overview_while_it_waits_and_leaves_after_his_help(self):
        stop = ev(20, "decision.breaker", id=1, cause="criteria", what="The note has no place", document="breaker.md", handoff="handoff.md")
        held = state(20, "held", "breaker 1 waits for the owner", "The note has no place: no option keeps the criteria")
        read = []

        def overview(*events):
            ctx = pages.Ctx(host="h", workspace="w", model=model(*events), asset=lambda name: name)
            ctx.artifact = lambda slug, path: read.append(path) or {"path": path, "kind": "markdown", "text": "# The note has no place\n\n> [!TIP]\n> **A.**"}
            return [str(x) for x in task_pages.overview_tab(ctx, ctx.model.tasks[0]) if x]

        parts = overview(state(0, "building", "task 2 of 3"), stop, held)
        self.assertIn('id="breaker"', parts[0])
        self.assertIn("# The note has no place", parts[0])
        self.assertEqual(read, ["breaker.md"])
        helped = overview(state(0, "building", "task 2 of 3"), stop, held, ev(30, "decision.taken", id=2, what="w", chose="A", why="y", by="owner", breaker=1))
        self.assertFalse(any('id="breaker"' in x for x in helped))

    def test_the_merge_review_is_first_on_the_overview_of_an_open_task(self):
        ctx = pages.Ctx(host="h", workspace="w", model=model(state(0, "open", "pull request https://github.com/acme/shop/pull/41"),
                                                              ev(1, "merge.review", verdict="call", calls=True, why="a careful request", by="claude", tip="abc")),
                        asset=lambda name: name)
        ctx.artifact = lambda slug, path: {"path": path, "kind": "markdown", "text": "Verdict: call. The change is careful."} if path == "merge-review.md" else None
        parts = [str(x) for x in task_pages.overview_tab(ctx, ctx.model.tasks[0]) if x]
        self.assertIn('id="merge-review"', parts[0])
        self.assertIn("it calls you", parts[0])
        self.assertIn("Verdict: call. The change is careful.", parts[0])

    def test_after_a_moved_base_the_page_offers_no_merge_and_its_step_says_lem_lands_it_again(self):
        proposed = (ev(0, "proposed", green=True, not_green=[], tip="abc123456"), state(1, "open", "pull request https://github.com/acme/shop/pull/41"))
        # the merge agent's read of the moved base asked for another round, and the refusal it keeps waits for the new landing
        refused = (*proposed, ev(2, "merge.review", verdict="merge", calls=False, by="claude", tip="abc123456", base="m2m2m2m2m", base_call="another round",
                                 base_why="B changed skills/lem/scripts/land.py, which the change edits too"),
                   ev(2, "merge.refused", by="owner", via="server", kind="base", said="the merge agent asks for another round of the checks", tip="abc123456", **{"from": "lem"}))

        def page(*events):
            ctx = pages.Ctx(host="h", workspace="w", model=model(*events), asset=lambda name: name, can_act=True)
            t = ctx.model.tasks[0]
            return ctx, t, str(task_pages.head_acts(ctx, t) or "")

        _, _, offered = page(*proposed)
        self.assertIn("/merge", offered)
        ctx, t, shown = page(*refused)
        self.assertNotIn("/merge", shown)
        step = "".join(str(x) for x in task_pages.merge_step(ctx, t))
        self.assertIn("Lem lands it again", step)
        self.assertNotIn("conflicting", step)
        # it is Lem's turn, not the owner's: the large card's head says so
        self.assertEqual((t.merge_wait, bm.now_head(t)), ("relands", "Proposed: Lem lands it again on the moved base"))

    def test_the_large_card_opens_with_the_tasks_first_line_while_its_block_is_the_newest(self):
        line = 'fix: "the footer says Terms and conditions". Fast track: one builder, the checks, one read, then the pull request. Nothing waits for you.'
        first = {**state(0, "building", "small change: one builder", "type: fix, because a typo"), "say": line}

        def card(*events):
            ctx = pages.Ctx(host="h", workspace="w", model=model(*events), asset=lambda name: name)
            return str(task_pages.now_card(ctx, ctx.model.tasks[0]))

        shown = card(first, ev(1, "builder.start", job="the small change"))
        self.assertIn('class="now-said"', shown)
        self.assertLess(shown.index("now-said"), shown.index("now-eyebrow"))
        self.assertIn("the footer says Terms and conditions", shown)
        self.assertNotIn("now-said", card(first, state(5, "ready", "the report is written")))
        self.assertNotIn("now-said", card(state(0, "building", "lead: builder")))

    def test_the_ring_counts_the_plans_finished_tasks_and_the_one_built_now(self):
        p = bm.progress_of(one(state(0, "building", "plan committed, 3 tasks"), state(9, "building", "task 2 of 3")))
        self.assertEqual((p["finished"], p["current"], p["total"], p["subs"][2]), (1, 1, 3, "task 2 of 3"))


class InboxLine(unittest.TestCase):
    """Where the owner answers on the phone's page of a task while his mark says away and the board's server
    sent the task's thing to his Inbox: both places with a link to the thread (criterion 6 of
    away-questions-reach-phone), today's line and why with no link (criterion 7), and the line of a note
    (decision 8). The page here is the phone's: not for this Mac, and it may act through the tailnet door."""

    AWAY = [{"ts": "2026-11-20T10:00:00Z", "event": "owner", "away": True, "words": "I'm away"}]
    LIVE = {"gift-note": {"live": True, "agent": True, "session": "S1"}}
    TAILNET = "https://studio.tail4e2a.ts.net:8443/"
    OPENED = ev(0, "session.open", session="S1", name="gift-note")
    BREAKER = (ev(20, "decision.breaker", id=1, cause="criteria", what="The note has no place", document="breaker.md", handoff="handoff.md"),
               state(20, "held", "breaker 1 waits for the owner", "The note has no place: no option keeps the criteria"))
    TODAY = "The task’s session, “gift-note”, is in agterm on the Mac."
    BOTH = "Answer in the task’s session on the Mac, or in the Inbox"

    @classmethod
    def record(cls, key="breaker:gift-note:1", kind="breaker", form="question", asks=True, **door) -> dict:
        sent = {"key": key, "task": "gift-note", "kind": kind, "form": form, "asks": asks, "message_id": "msg_01ABC", "thread_id": "msg_01ABC"}
        return {"running": True, "tailnet_url": cls.TAILNET, "why": None, "problem": None, **door, "sent": [sent]}

    def overview(self, *events, record=None, owner=AWAY, sessions=LIVE) -> str:
        m = model(self.OPENED, *events, owner=owner)
        m.sessions, m.inbox = sessions, record
        ctx = pages.Ctx(host="h", workspace="w", model=m, asset=lambda name: name, local=False, can_act=True)
        ctx.artifact = lambda slug, path: {"path": path, "kind": "markdown", "text": "# The note has no place"}
        return "".join(str(x) for x in task_pages.overview_tab(ctx, m.by_slug["gift-note"]) if x)

    @staticmethod
    def text(html: str) -> str:
        return " ".join(re.sub(r"<[^>]+>", " ", html).split()).replace(" .", ".")

    def test_criterion_6_a_breaker_sent_to_the_inbox_names_both_places_once_with_the_threads_link(self):
        shown = self.overview(state(1, "building", "task 2 of 3"), *self.BREAKER, record=self.record())
        said = self.text(shown)
        self.assertIn(f"{self.BOTH}.", said)
        self.assertIn(f'href="{self.TAILNET}#thread=msg_01ABC"', shown)
        self.assertEqual(shown.count('id="inbox"'), 1)
        self.assertNotIn(self.TODAY, said)
        self.assertNotIn("Where you answer: help in the task’s session.", said)
        self.assertIn("/lem park gift-note", said)
        # while he is there, the same record changes nothing: today's line alone
        there = self.text(self.overview(state(1, "building", "task 2 of 3"), *self.BREAKER, record=self.record(), owner=[]))
        self.assertIn(self.TODAY, there)
        self.assertNotIn("Inbox", there)

    def test_criterion_6_a_merge_and_a_blocked_task_get_the_line_that_row_action_never_gave_them(self):
        merge = (state(1, "open", "pull request https://github.com/acme/shop/pull/41"), ev(2, "merge.review", verdict="call", calls=True, why="careful", by="claude", tip="abc"))
        blocked = (state(1, "building", "lead: builder"), state(5, "blocked", "a builder ended two times with no report"))
        for events, key, kind in ((merge, "merge:gift-note", "merge"), (blocked, "blocked:gift-note", "blocked")):
            with self.subTest(kind=kind):
                self.assertNotIn("Inbox", self.text(self.overview(*events, record=self.record(key, kind), owner=[])))
                shown = self.overview(*events, record=self.record(key, kind))
                self.assertIn(self.BOTH, self.text(shown))
                self.assertIn(f'href="{self.TAILNET}#thread=msg_01ABC"', shown)

    def test_criterion_7_with_no_inbox_or_no_tailnet_address_the_page_says_todays_line_and_why(self):
        for door, why in (({"running": False, "tailnet_url": None, "why": "not running"},
                           "A message of this task went to the Inbox, but the Inbox does not run on this Mac now, so the phone cannot open it."),
                          ({"tailnet_url": None, "why": "no tailnet address"}, "The Inbox has no tailnet address, so the phone cannot open it.")):
            with self.subTest(why=door["why"]):
                shown = self.overview(state(1, "building", "task 2 of 3"), *self.BREAKER, record=self.record(**door))
                said = self.text(shown)
                self.assertIn(self.TODAY, said)
                self.assertIn(why, said)
                self.assertNotIn("#thread=", shown)
                self.assertNotIn(self.BOTH, said)

    def test_a_task_whose_thing_went_as_a_note_says_no_session_runs_and_offers_one(self):
        shown = self.overview(state(1, "building", "lead: builder"), record=self.record("session:gift-note", "session", "note", False),
                              sessions={"gift-note": {"live": True, "agent": False}})
        said = self.text(shown)
        self.assertIn("No session of the task runs now: open one here. The Inbox has a note, not a question.", said)
        self.assertIn(f'href="{self.TAILNET}#thread=msg_01ABC"', shown)
        self.assertIn('action="/h/w/tasks/gift-note/session"', shown)
        self.assertNotIn(self.BOTH, said)

    def test_the_record_reaches_the_page_escaped(self):
        record = self.record(running=False, tailnet_url=None, why='<img src=x onerror="alert(1)">')
        shown = self.overview(state(1, "building", "task 2 of 3"), *self.BREAKER, record=record)
        self.assertIn("&lt;img src=x onerror=", shown)
        self.assertNotIn("<img src=x", shown)
        sent = self.record()
        sent["sent"][0]["thread_id"] = '"><script>x</script>'
        shown = self.overview(state(1, "building", "task 2 of 3"), *self.BREAKER, record=sent)
        self.assertIn("#thread=%22%3E%3Cscript%3Ex%3C%2Fscript%3E", shown)
        self.assertNotIn("<script>x", shown)


class Artifacts(unittest.TestCase):
    def test_one_file_is_read_only_by_a_path_the_task_lists(self):
        with tempfile.TemporaryDirectory() as folder:
            task = Path(folder) / "tasks" / "gift-note"
            task.mkdir(parents=True)
            (task / "report.md").write_text("# Report\n")
            (Path(folder) / "secret.txt").write_text("no")
            self.assertEqual([f["text"] for f in lem_artifacts.files(task, "gift-note", read=False)], [None])
            self.assertEqual(lem_artifacts.one(task, "gift-note", "report.md")[0]["text"], "# Report\n")
            self.assertIsNone(lem_artifacts.one(task, "gift-note", "../../secret.txt"))

    def test_an_artifacts_text_reaches_the_page_escaped(self):
        f = {"path": "report.md", "kind": "markdown", "text": "<script>alert(1)</script>", "bytes": 26, "mtime": "2026-11-20T09:00:00Z"}
        ctx = pages.Ctx(host="h", workspace="w", model=model(), asset=lambda name: name)
        html = task_pages.art_body(ctx, f, one(state(0, "building", "lead: builder")))
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<b>", task_pages.json_marks('{"a": "<b>"}'))


class Links(unittest.TestCase):
    def test_every_form_of_a_pull_request_is_one_link_and_a_bare_number_needs_the_forge(self):
        forge = "https://github.com/acme/shop"
        parts = bm.pull_refs("merge pull request #41, acme/x#3 or https://github.com/a/b/pull/9.", forge)
        self.assertEqual([x["url"] for x in parts if isinstance(x, dict)],
                         ["https://github.com/acme/shop/pull/41", "https://github.com/acme/x/pull/3", "https://github.com/a/b/pull/9"])
        self.assertEqual(bm.pull_refs("pull request #41 and #d8", None), ["pull request #41 and #d8"])

    def test_markdown_gets_links_outside_its_code_and_its_links(self):
        text = "see #41, `#5`, [x](https://g/pull/3)\n```\n#7\n```\n# Head"
        self.assertEqual(bm.pull_links_md(text, "https://github.com/acme/shop"),
                         "see [#41](https://github.com/acme/shop/pull/41), `#5`, [x](https://g/pull/3)\n```\n#7\n```\n# Head")


class Reasons(unittest.TestCase):
    def test_a_reason_is_cut_at_its_own_separators_never_inside_a_quote_or_a_parenthesis(self):
        r = bm.reason_parts('decision 4 was taken without the owner (criterion 2: the span): "C: as W; and one line", by the dialectic')
        self.assertEqual((r["head"], r["about"], r["detail"], r["ref"]),
                         ("Decision 4 was taken without the owner", "criterion 2: the span", ['"C: as W; and one line", by the dialectic'], {"kind": "decision", "id": 4}))
        bar = bm.reason_parts("the bar is lower in `t.py` (one assertion fewer). The builder: a reason. The review: it holds")
        self.assertEqual((bar["head"], bar["about"], bar["detail"]), ("The bar is lower in `t.py`", "one assertion fewer", ["The builder: a reason", "The review: it holds"]))
        self.assertEqual(bm.reason_parts("two rounds reviewed it: the last one left 1 must-fix; round 1 left 2")["detail"], ["the last one left 1 must-fix", "round 1 left 2"])


class Map(unittest.TestCase):
    def test_a_record_hangs_on_its_document_and_what_the_map_does_not_know_is_a_working_file(self):
        entries = [{"path": p, "kind": "markdown", **lem_artifacts.place(p)} for p in
                   ("criteria.md", "criteria.json", "decisions.jsonl", "notes-of-mine.txt", "reviews/t/01-initial/report.md", "reviews/t/01-initial/findings.json", "media/a.png")]
        m = lem_artifacts.arrange(entries, {"criteria.md": ["media/a.png"]})
        self.assertEqual([s["name"] for s in m["sections"]], ["Request", "Criteria", "Plan", "Build", "Checks", "Review", "Pull request"])
        criteria = m["sections"][1]["docs"]
        self.assertEqual([(d["path"], [a["path"] for a in d["attached"]]) for d in criteria], [("criteria.md", ["criteria.json", "media/a.png"])])
        self.assertEqual([d["title"] for d in m["sections"][5]["docs"]], ["Review round 01-initial"])
        self.assertEqual(sorted((w["folder"], [f["path"] for f in w["files"]]) for w in m["work"] if w["folder"]),
                         [("Records with no document", ["decisions.jsonl"]), ("Review round 01-initial", ["reviews/t/01-initial/findings.json"])])
        self.assertIn("notes-of-mine.txt", [f["path"] for w in m["work"] for f in w["files"]])
        self.assertEqual(m["count"], 2)

    def test_the_merge_agents_brief_of_a_tip_on_a_base_is_a_document_of_the_pull_request(self):
        placed = lem_artifacts.place("merge-brief-abc123456789-def456789012.md")
        self.assertEqual(placed, {"group": "pr", "title": "The merge agent's brief of abc123456 on def456789", "role": "doc"})

    def test_a_task_loses_only_its_working_files_and_keeps_its_state_and_every_record(self):
        with tempfile.TemporaryDirectory() as folder:
            task = Path(folder) / "gift-note"
            files = {"ask.txt": "Add a gift note.", "state.md": "2026-11-20T10:00Z landed: main a..b", "ticket-steps.txt": "started\nassigned octocat\nlanded",
                     "ticket-repo.txt": "acme/shop", "resumed-from.txt": "gift", "decisions.jsonl": "{}", "report.md": "# Report\n\n![the note](media/a.png)\n",
                     "media/a.png": "a", "media/b.png": "b", "reviews/t/01-initial/report.md": "# Round", "reviews/t/01-initial/agents/a.jsonl": "{}",
                     "scratch.txt": "notes", "look/x.png": "x"}
            for path, text in files.items():
                (task / path).parent.mkdir(parents=True, exist_ok=True)
                (task / path).write_text(text)
            self.assertEqual(sorted(e["path"] for e in lem_artifacts.working(task, "gift-note")),
                             ["look/x.png", "media/b.png", "reviews/t/01-initial/agents/a.jsonl", "scratch.txt"])
            self.assertEqual({p: lem_artifacts.place(p)["role"] for p in ("state.md", "ticket-steps.txt", "ticket-repo.txt", "resumed-from.txt")},
                             {"state.md": "record", "ticket-steps.txt": "record", "ticket-repo.txt": "record", "resumed-from.txt": "record"})

    def test_a_picture_is_one_by_its_name_and_its_first_bytes(self):
        png = b"\x89PNG\r\n\x1a\n" + bytes(8)
        self.assertEqual(lem_artifacts.image_type("a.png", png), "image/png")
        self.assertIsNone(lem_artifacts.image_type("a.jpg", png))
        self.assertIsNone(lem_artifacts.image_type("a.png", b"<svg onload=x>"))
        self.assertIsNone(lem_artifacts.image_type("a.svg", b"<svg/>"))


class Backlog(unittest.TestCase):
    def test_the_filter_comes_from_the_address_and_a_value_it_does_not_know_is_no_filter(self):
        self.assertEqual(pages.backlog_filter({"q": [" board "], "worth": ["bogus"], "only": ["stale"]}), {"q": "board", "worth": "", "only": "stale"})
        self.assertEqual(pages.backlog_filter({"worth": ["later"], "only": ["everything"]}), {"q": "", "worth": "later", "only": ""})
        self.assertEqual(pages.backlog_filter({"q": ["x" * 300]})["q"], "x" * 200)


class Forge(unittest.TestCase):
    def test_the_server_asks_only_when_a_pull_request_is_open_and_nobody_looked_lately(self):
        prs, every = [{"task": "t", "n": 44}, {"task": "u", "n": 41}], 180_000
        self.assertEqual(bm.forge_due(prs, None, NOW, every, True), [41, 44])
        self.assertEqual(bm.forge_due(prs, NOW - 60_000, NOW, every, True), [], "the server looked a minute ago")
        self.assertEqual(bm.forge_due(prs, NOW - 200_000, NOW, every, True), [41, 44])
        self.assertEqual(bm.forge_due(prs, None, NOW, every, False), [], "a demo, or no GitHub remote")
        self.assertEqual(bm.forge_due([], None, NOW, every, True), [])


class Feed(unittest.TestCase):
    def test_only_an_event_a_resumed_task_carried_over_says_so(self):
        m = model(state(0, "open", "pull request https://github.com/acme/shop/pull/41"))
        refused = ev(1, "merge.refused", by="merger", via="server", kind="base", said="origin/main moved after the checks ran", tip="abc123456", **{"from": "lem"})
        self.assertNotIn("carried over", bm.describe(refused, m)["sub"])
        carried = ev(1, "criteria.approved", by="owner", was_at="2026-11-20T08:00:00Z", **{"from": "card-foot"})
        self.assertIn("carried over from", bm.describe(carried, m)["sub"])

    def test_the_owners_merge_that_stands_is_said_in_words(self):
        m = model(state(0, "open", "pull request https://github.com/acme/shop/pull/41"))
        read = bm.describe(ev(1, "merge.stands", by="owner", tip="abc123456", after="a read of the moved base", base="def456789"), m)
        landed = bm.describe(ev(1, "merge.stands", by="owner", tip="abc123456", **{"from": "fed987654"}), m)
        self.assertEqual((read["head"], landed["head"]), ("Your merge stands", "Your merge stands"))
        self.assertIn("the merge agent read the moved base and said safe", read["text"])
        self.assertIn("the new landing kept the change you merged", landed["text"])
        self.assertNotIn("carried over", landed["sub"])


class MergeStep(unittest.TestCase):
    """The confirm step of a merge (`merge_step`): its head, its body and its foot, and the key of its read."""

    REASONS = ["the owner did not approve the criteria: they were approved while the task ran without the owner",
               "two rounds reviewed it: the last one left no must-fix"]

    def step(self, *events, tip="4c1d2e3f5a6b7c8d9e0f4c1d2e3f5a6b7c8d9e0f", pr=44, can_act=True):
        base = (ev(0, "proposed", green=False, not_green=self.REASONS, tip=tip[:9]),
                state(1, "open", f"pull request https://github.com/acme/shop/pull/{pr}" if pr else "the branch lands on the base itself"))
        ctx = pages.Ctx(host="h", workspace="w", model=model(*base, *events), asset=lambda name: name, can_act=can_act)
        landing = {"proposed": tip, "history": "squash", "title": "feat: a refund line", "base": "main", **({"pr": {"number": pr, "url": f"https://github.com/acme/shop/pull/{pr}"}} if pr else {})}
        ctx.landing_of = lambda slug: landing
        return "".join(str(x) for x in task_pages.merge_step(ctx, ctx.model.tasks[0]))

    def careful(self, why):
        return ev(2, "review", attempt=2, round=2, kind="round", verdict="clean", careful=True, careful_why=why)

    def key(self, html):
        found = re.search(r'data-sheet-key-value="([0-9a-f]+)"', html)
        return found and found.group(1)

    def test_the_step_is_a_head_a_body_with_the_six_items_in_their_order_and_a_foot_with_the_form_and_back(self):
        html = self.step(self.careful("the total is money"))
        head, body, foot = html.index('class="cf-head"'), html.index('class="cf-body"'), html.index('class="cf-foot"')
        self.assertLess(head, body)
        self.assertLess(body, foot)
        self.assertIn('<div class="eyebrow">Merge #44 · confirm</div>', html[head:body])
        items = [html.index(x, body) for x in ('class="cf-first', 'class="reasons"', 'class="cf-careful-why"', 'id="cf-facts"', 'class="cf-note"')]
        self.assertEqual(items, sorted(items))
        self.assertLess(items[-1], foot)
        facts = [html.index(f'id="cf-dt-{x}"') for x in ("pr", "commit", "into", "as")]
        self.assertEqual(facts, sorted(facts))
        form = html[foot:]
        self.assertIn('name="confirm" value="yes"', form)
        self.assertIn('name="tip" value="4c1d2e3f5a6b7c8d9e0f4c1d2e3f5a6b7c8d9e0f"', form)
        self.assertIn("<span>Merge pull request #44</span>", form)
        self.assertIn("<span>Back</span>", form)
        self.assertNotIn("Cancel", html)

    def test_only_a_step_with_its_button_has_the_controller_the_overlays_class_and_the_key_of_its_read(self):
        shown = self.step()
        self.assertIn('data-controller="sheet"', shown)
        self.assertIn("cf-sheet", shown)
        self.assertRegex(self.key(shown) or "", r"^[0-9a-f]{12}$")
        self.assertIn('data-sheet-target="body"', shown)
        self.assertIn('data-sheet-target="head" tabindex="-1"', shown)
        for html in (self.step(can_act=False), self.step(tip="")):
            self.assertNotIn("sheet", html)
            self.assertNotIn('name="confirm"', html)
            self.assertIn('class="cf-body"', html)

    def test_the_key_of_the_read_is_another_for_another_commit_and_for_another_careful_call_on_the_same_commit(self):
        first = self.key(self.step(self.careful("the total is money")))
        self.assertEqual(first, self.key(self.step(self.careful("the total is money"))), "the same text is the same key")
        self.assertNotEqual(first, self.key(self.step(self.careful("the total is money"), tip="9" * 40)))
        self.assertNotEqual(first, self.key(self.step(self.careful("a refund larger than the total"))))
        self.assertNotEqual(first, self.key(self.step()))

    def test_the_head_names_the_pull_request_when_it_has_a_number(self):
        self.assertIn('<div class="eyebrow">Merge #7 · confirm</div>', self.step(pr=7))
        no_pr = self.step(pr=None)
        self.assertIn('<div class="eyebrow">Merge · confirm</div>', no_pr)
        self.assertIn("<span>Merge it into main</span>", no_pr)


class ParkAndApproveSteps(unittest.TestCase):
    """The park step (`park_step`) and the approval of the criteria (`approve_card`): the three parts of an act's
    step, as the merge step has them, the key of their read, and where the approval's note and its plain text go."""

    STOP = ev(20, "decision.breaker", id=1, cause="criteria", what="The note has no place", document="breaker.md", handoff="handoff.md")
    TEXT = '## Acceptance criteria\n\n1. A product with 3 in stock says "3 left" under its price.\n'
    REFUSED = {"task": "gift-note", "state": "refused", "said": "The criteria changed since the page showed them. Read them again, then approve."}

    def key(self, html):
        found = re.search(r'data-sheet-key-value="([0-9a-f]+)"', html)
        return found and found.group(1)

    def park(self, can_act=True):
        ctx = pages.Ctx(host="h", workspace="w", model=model(state(0, "building", "task 2 of 3"), self.STOP,
                                                              state(20, "held", "breaker 1 waits for the owner", "The note has no place: no option keeps the criteria")),
                        asset=lambda name: name, can_act=can_act)
        return "".join(str(x) for x in task_pages.park_step(ctx, ctx.model.tasks[0]))

    def ctx(self, text=TEXT, can_act=True, note=None):
        ctx = pages.Ctx(host="h", workspace="w", model=model(state(0, "held", "the criteria wait for the owner")), asset=lambda name: name, can_act=can_act, note=note)
        ctx.criteria_waiting = lambda slug: None if text is None else {"text": text, "digest": "d1g3st"}
        return ctx

    def approve(self, **kw):
        ctx = self.ctx(**kw)
        return str(task_pages.approve_card(ctx, ctx.model.tasks[0]))

    def test_the_park_step_is_a_head_a_body_with_what_stopped_and_what_a_park_keeps_and_a_foot_with_the_field_the_button_and_back(self):
        html = self.park()
        head, body, foot = html.index('class="cf-head"'), html.index('class="cf-body"'), html.index('class="cf-foot"')
        self.assertLess(head, body)
        self.assertLess(body, foot)
        self.assertIn('<div class="eyebrow">Park · breaker 1</div>', html[head:body])
        said = [html.index(x, body) for x in ("The build stopped: ", "A parked task keeps its worktree")]
        self.assertEqual(said, sorted(said))
        self.assertLess(said[-1], foot)
        form = html[foot:]
        for part in ('name="why"', "<span>Park the task</span>", "<span>Back</span>"):
            self.assertIn(part, form)
        self.assertNotIn("Cancel", html)
        self.assertIn('data-controller="sheet"', html)
        self.assertIn("cf-sheet", html)
        self.assertRegex(self.key(html) or "", r"^[0-9a-f]{12}$")
        mute = self.park(can_act=False)
        self.assertNotIn("sheet", mute)
        self.assertNotIn('name="why"', mute)
        self.assertIn("/lem park gift-note", mute)

    def test_the_approval_that_holds_the_button_is_a_head_a_body_with_the_criteria_and_their_plain_text_and_a_foot_with_the_form_and_back(self):
        html = self.approve()
        head, wrap, body, foot = (html.index(x) for x in ('class="cf-head"', 'class="approve-body"', 'class="cf-body"', 'class="cf-foot"'))
        self.assertEqual([head, wrap, body, foot], sorted([head, wrap, body, foot]))
        self.assertIn('id="approve-card"', html[:head])
        self.assertIn("The criteria wait for your yes", html[head:wrap])
        markdown, plain = html.index('data-controller="markdown"', body), html.index('<noscript><pre class="cf-plain">## Acceptance criteria', body)
        self.assertLess(markdown, plain)
        self.assertIn("&quot;3 left&quot; under its price.", html[plain:foot])
        form = html[foot:]
        self.assertIn('name="digest" value="d1g3st"', form)
        self.assertIn("<span>Approve the criteria</span>", form)
        self.assertIn('class="btn cf-back"', form)
        self.assertIn("<span>Back</span>", form)
        self.assertIn('data-controller="sheet"', html)
        self.assertIn("cf-sheet", html)

    def test_only_an_approval_with_its_button_has_the_controller_and_the_key_of_its_read_follows_the_criteria(self):
        first = self.key(self.approve())
        self.assertRegex(first or "", r"^[0-9a-f]{12}$")
        self.assertEqual(first, self.key(self.approve()))
        self.assertNotEqual(first, self.key(self.approve(text=self.TEXT + "2. A product with none in stock says \"Sold out\".\n")))
        for html in (self.approve(can_act=False), self.approve(text=None)):
            self.assertNotIn("sheet", html)
            self.assertNotIn("cf-body", html)
            self.assertNotIn('name="digest"', html)
            self.assertNotIn("noscript", html)

    def test_the_note_of_an_approval_is_first_in_the_card_that_holds_the_button_and_above_a_card_without_it(self):
        ctx = self.ctx(note=self.REFUSED)
        parts = [str(x) for x in task_pages.criteria_tab(ctx, ctx.model.tasks[0]) if x]
        self.assertIn('id="approve-card"', parts[0])
        body = parts[0].index('class="cf-body"')
        first = parts[0].index("<section", body)
        self.assertIn('id="act-note"', parts[0][first:parts[0].index(">", first)])
        self.assertLess(parts[0].index('id="act-note"'), parts[0].index('data-controller="markdown"'))
        self.assertEqual(sum('id="act-note"' in p for p in parts), 1)
        self.assertNotEqual(self.key(parts[0]), self.key(self.approve()), "the note is part of what the owner reads")
        ctx = self.ctx(note=self.REFUSED, can_act=False)
        parts = [str(x) for x in task_pages.criteria_tab(ctx, ctx.model.tasks[0]) if x]
        self.assertIn('id="act-note"', parts[0])
        self.assertIn('id="approve-card"', parts[1])
        self.assertNotIn('id="act-note"', parts[1])


if __name__ == "__main__":
    unittest.main()
