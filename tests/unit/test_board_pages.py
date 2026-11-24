"""board_pages.py's rules, each a page drawn from a model of a few events: what the
kanban's Done column draws of the ended tasks, its foot row, the page that lists the
ended tasks it has no card for, and the kanban's mark over its cards, and each view's
line of keys in the page's foot.

    python3 -B -m unittest discover -s tests/unit
"""

import json
import re
import sys
import types
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import board_model as bm
from lem import board_pages as pages
from lem import board_task as task_pages
from lem import serve

START = datetime(2026, 11, 20, 9, 0, tzinfo=UTC)
NOW = int((START + timedelta(hours=2)).timestamp() * 1000)
ENDED = ("landed", "dropped", "answered")


def matched(found: re.Match[str] | None) -> re.Match[str]:
    """A match the test reads a part of: the test fails here when the pattern is not in
    the text."""
    if found is None:
        raise AssertionError("the pattern is not in the text")
    return found


def state(minute: float, status: str, text: str, *lines: str, task: str) -> dict:
    return {
        "ts": (START + timedelta(minutes=minute)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "task.state",
        "task": task,
        "status": status,
        "text": text,
        "lines": list(lines),
    }


def ended(n: int) -> list:
    """N ended tasks, task-00 the first to end and each next one a minute later, landed,
    dropped and answered in turn; task-02 landed with its pull request. One task builds
    beside them."""
    events = []
    for i in range(n):
        lines = ("pull request https://github.com/acme/shop/pull/41",) if i == 2 else ()
        events.append(state(i, ENDED[i % 3], "it ended", *lines, task=f"task-{i:02d}"))
    return [*events, state(60, "building", "task 1 of 2", task="builds")]


def ctx_of(events: list) -> pages.Ctx:
    return pages.Ctx(
        host="h",
        workspace="w",
        model=bm.derive(events, [], NOW),
        asset=lambda name: name,
    )


def column(html: str, key: str) -> str:
    """One column of the kanban, from its section to the next one."""
    return re.split(
        r'<section class="col [^"]*" id="col-', html.split(f'id="col-{key}"', 1)[1]
    )[0]


def cards(html: str) -> list:
    return re.findall(r'<article[^>]*id="card-([a-z0-9-]+)"', html)


class Done(unittest.TestCase):
    def test_done_draws_the_20_tasks_that_ended_last_the_newest_on_top(self) -> None:
        html = str(pages.kanban_page(ctx_of(ended(25))))
        self.assertEqual(
            cards(column(html, "done")), [f"task-{i:02d}" for i in range(24, 4, -1)]
        )
        for i in range(5):
            self.assertNotIn(f'id="card-task-{i:02d}"', html)

    def test_dones_head_and_its_phone_tab_count_every_ended_task(self) -> None:
        html = str(pages.kanban_page(ctx_of(ended(25))))
        self.assertEqual(len(cards(column(html, "done"))), 20)
        self.assertRegex(
            column(html, "done"), r'<span class="col-name">Done</span><em>25</em>'
        )
        self.assertRegex(html, r'id="ktab-done"[^>]*><i></i>Done<em>25</em></button>')

    def test_a_row_under_the_20_cards_counts_the_rest_and_leads_to_their_list(
        self,
    ) -> None:
        done = column(str(pages.kanban_page(ctx_of(ended(25)))), "done")
        row = matched(
            re.search(
                r'<a class="col-more" id="done-older" href="([^"]+)"[^>]*>(.*?)</a>',
                done,
            )
        )
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "/h/w/done")
        self.assertIn("<span>5 older</span>", row[2])
        self.assertGreater(
            done.index('id="done-older"'), done.index('id="card-task-05"')
        )

    def test_with_20_ended_tasks_or_fewer_done_draws_each_and_no_row(self) -> None:
        for n in (20, 3):
            done = column(str(pages.kanban_page(ctx_of(ended(n)))), "done")
            self.assertEqual(len(cards(done)), n)
            self.assertNotIn("done-older", done)

    def test_the_list_is_a_page_of_the_board_whose_tasks_link_goes_back_to_the_columns(
        self,
    ) -> None:
        self.assertEqual(serve.PAGES["done"], "older_page")
        html = str(getattr(pages, serve.PAGES["done"])(ctx_of(ended(25))))
        self.assertIn('id="side"', html)
        self.assertRegex(html, r'<a class="vbtn" id="view-tasks" href="/h/w/"')
        self.assertNotIn('id="view-done"', html)
        self.assertIn("<h2>Older ended tasks</h2>", html)


class Older(unittest.TestCase):
    def rows(self, html: str) -> list:
        return re.findall(
            r'<div class="row [^"]*" id="older-([a-z0-9-]+)">(.*?)</span></div>', html
        )

    def test_it_lists_the_tasks_done_has_no_card_for_newest_first_each_with_how_and_when_it_ended(
        self,
    ) -> None:
        ctx = ctx_of(ended(25))
        html = str(pages.older_page(ctx))
        rows = self.rows(html)
        self.assertEqual(
            [slug for slug, _ in rows],
            ["task-04", "task-03", "task-02", "task-01", "task-00"],
        )
        words = {slug: re.sub(r"<[^>]+>", " ", body) for slug, body in rows}
        for slug, how in (
            ("task-04", "Dropped"),
            ("task-03", "Landed"),
            ("task-02", "Answered"),
            ("task-01", "Dropped"),
            ("task-00", "Landed"),
        ):
            t = ctx.model.by_slug[slug]
            self.assertIn(t.title, words[slug])
            self.assertIn(how, words[slug])
            self.assertIn(bm.stamp(t.since, NOW), words[slug])

    def test_each_row_opens_the_tasks_board_over_the_list_and_its_pull_request_when_it_has_one(
        self,
    ) -> None:
        html = str(pages.older_page(ctx_of(ended(25))))
        rows = dict(self.rows(html))
        self.assertIn('href="/h/w/tasks/task-04?in=done"', rows["task-04"])
        self.assertIn('data-turbo-frame="task"', rows["task-04"])
        self.assertIn('href="https://github.com/acme/shop/pull/41"', rows["task-02"])
        self.assertNotIn("github.com", rows["task-03"])

    def test_a_task_opened_from_the_list_lies_over_the_list_and_closes_back_to_it(
        self,
    ) -> None:
        ctx = ctx_of(ended(25))
        ctx.view, ctx.task = "done", "task-04"
        status, html = task_pages.task_page(ctx)
        self.assertEqual(status, 200)
        self.assertIn('id="older-task-04"', str(html))
        self.assertIn('class="ibtn p-close" href="/h/w/done"', str(html))

    def test_with_no_older_task_the_list_says_done_shows_every_one(self) -> None:
        html = str(pages.older_page(ctx_of(ended(20))))
        self.assertEqual(self.rows(html), [])
        self.assertIn("Done shows every ended task", html)


class Views(unittest.TestCase):
    def test_each_view_button_shows_its_plain_key_on_the_button_and_takes_that_key(
        self,
    ) -> None:
        html = str(pages.kanban_page(ctx_of(ended(3))))
        for key, label, kbd in (
            ("tasks", "Tasks", "T"),
            ("waits", "Waits for you", "W"),
            ("backlog", "Backlog", "B"),
            ("activity", "Activity", "A"),
        ):
            button = matched(
                re.search(rf'<a class="vbtn" id="view-{key}"[^>]*>(.*?)</a>', html)
            )
            self.assertIsNotNone(button, key)
            self.assertIn(f'data-hotkey="Key{kbd}"', button[0])
            self.assertIn(f"{label}<kbd>{kbd}</kbd>", button[1])
            self.assertIn(f'title="Key {kbd}, with no Shift"', button[0])


class SideFold(unittest.TestCase):
    """The one arrow at the sidebar's foot that folds it to a rail and unfolds it."""

    def page(self, *, rail: bool) -> str:
        ctx = ctx_of(ended(3))
        ctx.prefs = {"rail": True} if rail else {}
        return str(pages.kanban_page(ctx))

    def fold(self, html: str) -> re.Match:
        return matched(
            re.search(
                (
                    r'<button id="side-fold" class="ibtn" type="button" '
                    r'data-action="fold#side" title="([^"]+)" '
                    r'aria-label="([^"]+)"><svg class="ic" aria-hidden="true"><use '
                    r'href="#i-chevron-left"></use></svg></button>'
                ),
                html,
            )
        )

    def test_an_open_sidebar_has_an_arrow_that_points_left_at_its_foot_and_the_old_icon_is_gone(
        self,
    ) -> None:
        html = self.page(rail=False)
        self.assertRegex(html, r'<div class="shell" id="shell"')
        found = self.fold(html)
        self.assertIsNotNone(found)
        self.assertEqual((found[1], found[2]), ("Fold the sidebar", "Fold the sidebar"))
        self.assertEqual(html.count('id="side-fold"'), 1)
        brand = html.split('<div class="brand">', 1)[1].split('<div class="rail"', 1)[0]
        self.assertNotIn("fold#side", brand)
        foot = html.split('id="side-foot"', 1)[1].split("</aside>", 1)[0]
        self.assertIn('id="side-fold"', foot)
        self.assertLess(foot.index('id="ws"'), foot.index('id="side-fold"'))
        self.assertNotIn("i-sidebar", html)

    def test_a_folded_sidebar_keeps_the_arrow_at_its_foot_and_it_unfolds_it(
        self,
    ) -> None:
        html = self.page(rail=True)
        self.assertRegex(html, r'<div class="shell railed" id="shell"')
        found = self.fold(html)
        self.assertIsNotNone(found)
        self.assertEqual(
            (found[1], found[2]), ("Unfold the sidebar", "Unfold the sidebar")
        )
        self.assertIn(
            'id="side-fold"', html.split('id="side-foot"', 1)[1].split("</aside>", 1)[0]
        )

    def test_the_rail_shows_the_foot_with_the_arrow_alone_turned_to_the_right(
        self,
    ) -> None:
        css = (pages.ASSETS / "board.css").read_text(encoding="utf-8")
        hidden = matched(
            re.search(
                (
                    r"\.shell\.railed \.side > :not\(([^)]*)\) \{ display: "
                    r"none !important; \}"
                ),
                css,
            )
        )
        self.assertIsNotNone(hidden)
        self.assertIn(".side-foot", hidden[1])
        self.assertIn(
            ".shell.railed .side-foot > :not(#side-fold) { display: none; }", css
        )
        self.assertIn(".shell.railed #side-fold .ic { transform: scaleX(-1); }", css)

    def test_a_click_says_the_next_click_on_the_arrow(self) -> None:
        script = (pages.ASSETS / "vendor" / "board-app.js").read_text(encoding="utf-8")
        self.assertIn('"Unfold the sidebar":"Fold the sidebar"', script)
        self.assertNotIn("sidebar", json.loads(pages.ICONS.read_text(encoding="utf-8")))


class Keys(unittest.TestCase):
    def test_the_kanban_carries_the_cursor_over_its_cards_and_one_line_of_its_keys(
        self,
    ) -> None:
        html = str(pages.kanban_page(ctx_of(ended(3))))
        kanban = matched(
            re.search(r'<div class="view kanban" id="kanban"[^>]*>', html)
        )[0]
        for attr in (
            'data-controller="cursor"',
            'data-cursor-item-value="article.tc"',
            'data-cursor-group-value="section.col"',
            'data-cursor-link-value=".tc-link"',
            'data-action="keydown@window-&gt;cursor#key click-&gt;cursor#pick"',
        ):
            self.assertIn(attr, kanban)
        line = matched(
            re.search(r'<div class="keys" id="kanban-keys">(.*?)</div>', html)
        )
        self.assertIsNotNone(line)
        self.assertEqual(
            " ".join(re.sub(r"<[^>]+>", " ", line[1]).split()),
            "J K ↑ ↓ move · H L ← → column · Enter open · Esc close",
        )
        self.assertEqual(
            re.findall(r"<kbd>([^<]+)</kbd>", line[1]),
            ["J", "K", "↑", "↓", "H", "L", "←", "→", "Enter", "Esc"],
        )
        self.assertEqual(html.count('class="keys"'), 1)

    def test_each_view_has_its_line_of_keys_in_one_foot_under_the_stage(self) -> None:
        """The task keys-help-in-a-sticky-footer: on Tasks, Waits for you, Backlog and
        Activity the line of keys is the row of the page between the stage and the
        status line, in no view's list, and the main column's grid gives it a row of its
        own under the stage's, so the line stays at the window's foot and the list
        scrolls above it."""
        events = [
            *ended(3),
            state(61, "held", "the criteria wait for the owner", task="gift-note"),
        ]
        backlog = {
            "folder": "docs/backlog",
            "reviewer_folder": ".lem/state/backlog",
            "items": [
                {
                    "slug": f"item-{i}",
                    "key": f"item-{i}",
                    "path": f"docs/backlog/item-{i}.md",
                    "title": f"Item {i}",
                    "worth": "later",
                    "reviewer": False,
                }
                for i in range(40)
            ],
        }
        ctx = pages.Ctx(
            host="h",
            workspace="w",
            model=bm.derive(events, [], NOW),
            asset=lambda name: name,
            backlog=backlog,
        )
        for view, draw, line in (
            (
                "tasks",
                pages.kanban_page,
                "J K ↑ ↓ move · H L ← → column · Enter open · Esc close",
            ),
            ("waits", pages.waits_page, "J K ↑ ↓ move · Enter go"),
            (
                "backlog",
                pages.backlog_page,
                "/ filter · J K move · Enter open or close · R read again",
            ),
            ("activity", pages.activity_page, "T W B A view"),
        ):
            with self.subTest(view=view):
                html = str(draw(ctx))
                foot = matched(
                    re.search(
                        (
                            r'</main>(<div class="keys" '
                            r'id="([a-z]+)-keys">(.*?)</div>)<footer class="status'
                        ),
                        html,
                    )
                )
                self.assertIsNotNone(
                    foot,
                    f"no line of keys between the stage and the status line on {view}",
                )
                self.assertEqual(foot[2], "kanban" if view == "tasks" else view)
                self.assertEqual(
                    " ".join(re.sub(r"<[^>]+>", " ", foot[3]).split()), line
                )
                self.assertEqual(html.count('class="keys"'), 1)
        css = (pages.ASSETS / "board.css").read_text(encoding="utf-8")
        self.assertIn(
            ".main { display: grid; grid-template-rows: auto minmax(0, 1fr) auto auto;",
            css,
        )
        self.assertIn(".main > .keys {", css)


class WaitsVerb(unittest.TestCase):
    """The verb of a row of "Waits for you" goes where the owner acts: on a page for
    this Mac, for a row he answers in the task's session while it lives, the jump of
    agterm; elsewhere the task's panel alone."""

    OPEN = {
        "ts": (START + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "session.open",
        "task": "gift-note",
        "session": "S1",
        "name": "gift-note",
    }

    def verb(
        self,
        *events: dict,
        row: str = "held",
        local: bool = True,
        sessions: dict | None = None,
    ) -> str:
        """The verb link of the row ROW-gift-note"""
        m = bm.derive([self.OPEN, *events], [], NOW)
        m.sessions = (
            {"gift-note": {"live": True, "agent": True, "session": "S1"}}
            if sessions is None
            else sessions
        )
        html = str(
            pages.waits_page(
                pages.Ctx(
                    host="h",
                    workspace="w",
                    model=m,
                    asset=lambda name: name,
                    local=local,
                )
            )
        )
        verbs = re.findall(
            (
                rf'<article class="wrow[^"]*" id="wait-{row}-gift-note"[^>]*>.*?(<a '
                r'class="wr-verb"[^>]*>)'
            ),
            html,
        )
        self.assertEqual(len(verbs), 1, verbs)
        return verbs[0]

    def test_a_held_row_on_a_page_for_this_mac_with_a_live_session_jumps_to_it_and_keeps_its_address(
        self,
    ) -> None:
        verb = self.verb(
            state(2, "held", "the interview waits for the owner", task="gift-note")
        )
        self.assertIn('data-action="agterm#jump"', verb)
        self.assertIn('data-agterm-session-param="S1"', verb)
        self.assertIn('href="/h/w/tasks/gift-note?in=waits"', verb)

    def test_no_jump_on_a_page_that_is_not_for_this_mac_or_with_no_live_session(
        self,
    ) -> None:
        held = state(2, "held", "the interview waits for the owner", task="gift-note")
        for verb in (
            self.verb(held, local=False),
            self.verb(held, sessions={"gift-note": {"live": False, "session": "S1"}}),
        ):
            self.assertNotIn("agterm#jump", verb)
            self.assertNotIn("data-agterm-session-param", verb)
            self.assertIn('href="/h/w/tasks/gift-note?in=waits"', verb)

    def test_no_jump_for_a_merge_row(self) -> None:
        verb = self.verb(
            state(
                2,
                "open",
                "pull request https://github.com/acme/shop/pull/41",
                task="gift-note",
            ),
            row="merge",
        )
        self.assertNotIn("agterm#jump", verb)
        self.assertIn('href="/h/w/tasks/gift-note?in=waits"', verb)

    def test_the_list_carries_the_cursor_over_its_rows_and_one_line_of_its_keys(
        self,
    ) -> None:
        m = bm.derive(
            [
                self.OPEN,
                state(2, "held", "the interview waits for the owner", task="gift-note"),
            ],
            [],
            NOW,
        )
        html = str(
            pages.waits_page(
                pages.Ctx(host="h", workspace="w", model=m, asset=lambda name: name)
            )
        )
        listing = matched(
            re.search(r'<div class="waits-list" id="waits-list"[^>]*>', html)
        )
        self.assertIsNotNone(listing)
        for attr in (
            'data-controller="cursor"',
            'data-cursor-item-value="article.wrow, details.wstack"',
            'data-cursor-link-value="a.wr-verb, summary.wst-head"',
            'data-cursor-pick-value="a.wr-verb, a.wr-task, summary.wst-head"',
            'data-action="keydown@window-&gt;cursor#key click-&gt;cursor#pick"',
        ):
            self.assertIn(attr, listing[0])
        self.assertNotIn("data-cursor-group-value", listing[0])
        line = matched(
            re.search(r'<div class="keys" id="waits-keys">(.*?)</div>', html)
        )
        self.assertIsNotNone(line)
        self.assertEqual(
            " ".join(re.sub(r"<[^>]+>", " ", line[1]).split()),
            "J K ↑ ↓ move · Enter go",
        )
        self.assertEqual(html.count('class="keys"'), 1)
        # the title link of the row opens the panel and carries no jump
        self.assertNotIn(
            "agterm", matched(re.search(r'<a class="wr-task"[^>]*>', html))[0]
        )

    def test_with_nothing_waiting_no_line_of_keys(self) -> None:
        html = str(pages.waits_page(ctx_of(ended(2))))
        self.assertIn("Nothing waits for you.", html)
        self.assertNotIn('id="waits-keys"', html)


class WaitStack(unittest.TestCase):
    """A task with two or more things that wait for the owner is one stack of "Waits for
    you", and each count counts it once (criteria 1 to 4 of
    docs/plans/2026-11-23-one-row-for-a-merge-call.md): "Logo eyes signal and favicon"
    has its merge review that calls him since 4m 22s and its merge since 7m 01s, and
    "Board answers a card" its interview since 33 minutes."""

    LOGO, CARD = "logo-eyes-signal-and-favicon", "board-answers-a-card"

    def events(self, *, card: bool = True) -> list:
        def at(minutes: float) -> str:
            return (START + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")

        # NOW is minute 120: the pull request opened at 112:59 (7m 01s), the review came
        # at 115:38 (4m 22s)
        logo = [
            {
                "ts": at(112),
                "event": "proposed",
                "task": self.LOGO,
                "green": False,
                "not_green": ["a test was deleted"],
                "tip": "abc123456",
            },
            state(
                120 - 421 / 60,
                "open",
                "pull request https://github.com/acme/shop/pull/73",
                task=self.LOGO,
            ),
            {
                "ts": at(120 - 262 / 60),
                "event": "merge.review",
                "task": self.LOGO,
                "verdict": "call",
                "calls": True,
                "why": "Verdict: call. It redraws the owner's logo.",
                "by": "claude",
                "tip": "abc123456",
            },
        ]
        return [
            *(
                [state(87, "held", "the interview waits for the owner", task=self.CARD)]
                if card
                else []
            ),
            *logo,
        ]

    def page(self, **kw: bool) -> str:
        m = bm.derive(self.events(**kw), [], NOW)
        return str(
            pages.waits_page(
                pages.Ctx(
                    host="h",
                    workspace="w",
                    model=m,
                    asset=lambda name: name,
                    can_act=True,
                )
            )
        )

    @staticmethod
    def stack(html: str, slug: str) -> str:
        found = re.search(
            rf'<details class="wstack[^"]*" id="wait-stack-{slug}"[^>]*>.*?</details>',
            html,
            re.DOTALL,
        )
        return found[0] if found else ""

    @staticmethod
    def words(html: str) -> str:
        return " ".join(re.sub(r"<[^>]+>", " ", html).split())

    def test_a_task_of_two_things_is_one_closed_stack_in_the_place_of_its_first_thing(
        self,
    ) -> None:
        html = self.page()
        stack = self.stack(html, self.LOGO)
        self.assertTrue(stack, "no stack of the logo's task")
        opening = matched(re.match(r"<details[^>]*>", stack))[0]
        self.assertNotIn(" open", opening)
        self.assertIn(f'data-task="{self.LOGO}"', opening)
        summary = matched(
            re.search(
                r'<summary class="wrow wst-head"[^>]*>(.*?)</summary>', stack, re.DOTALL
            )
        )
        self.assertIsNotNone(summary)
        self.assertEqual(
            self.words(summary[1]),
            (
                "Logo eyes signal and favicon 2 things Read the merge "
                "review · Waits for the merge"
            ),
        )
        self.assertNotIn("<a ", summary[1])
        # the entries of the list in their order: the interview's row, then the stack
        # where the merge review's row stood
        listing = html.split('id="waits-list"', 1)[1].split('id="parked"', 1)[0]
        self.assertEqual(
            re.findall(
                (
                    r'<(?:article class="wrow[^"]*"|details class="wstack[^"]*") '
                    r'id="(wait-[a-z0-9-]+)"'
                ),
                listing,
            ),
            [
                f"wait-held-{self.CARD}",
                f"wait-stack-{self.LOGO}",
                f"wait-review-{self.LOGO}",
                f"wait-merge-{self.LOGO}",
            ],
        )
        self.assertEqual(listing.count('<details class="wstack'), 1)
        cursor = matched(
            re.search(r'<div class="waits-list" id="waits-list"[^>]*>', html)
        )[0]
        for attr in (
            'data-cursor-item-value="article.wrow, details.wstack"',
            'data-cursor-link-value="a.wr-verb, summary.wst-head"',
            'data-cursor-pick-value="a.wr-verb, a.wr-task, summary.wst-head"',
        ):
            self.assertIn(attr, cursor)
        self.assertEqual(
            self.words(
                matched(
                    re.search(r'<div class="keys" id="waits-keys">(.*?)</div>', html)
                )[1]
            ),
            "J K ↑ ↓ move · Enter go or open",
        )

    def test_the_stack_holds_each_thing_as_its_own_row_with_its_time_and_the_merge_button_on_the_merge_row(
        self,
    ) -> None:
        stack = self.stack(self.page(), self.LOGO)
        rows = dict(
            re.findall(
                r'<article class="wrow[^"]*" id="wait-([a-z]+)-'
                + self.LOGO
                + r'"[^>]*>(.*?)</article>',
                stack,
                re.DOTALL,
            )
        )
        self.assertEqual(list(rows), ["review", "merge"])
        tops = {
            kind: self.words(
                matched(re.search(r'<div class="wr-top">(.*?)</div>', row, re.DOTALL))[
                    1
                ]
            )
            for kind, row in rows.items()
        }
        self.assertEqual(
            tops,
            {
                "review": "Read the merge review 4m 22s",
                "merge": "Merge the pull request #73 7m 01s",
            },
        )
        self.assertIn("Merge…", rows["merge"])
        self.assertNotIn("Merge…", rows["review"])
        self.assertNotIn(
            "Merge…", matched(re.search(r"<summary.*?</summary>", stack, re.DOTALL))[0]
        )
        self.assertIn("acme/shop#73", rows["merge"])

    def test_a_task_of_one_thing_is_its_plain_row_as_today(self) -> None:
        html = self.page()
        row = matched(
            re.search(
                (
                    r'<article class="wrow[^"]*" '
                    rf'id="wait-held-{self.CARD}"[^>]*>(.*?)</article>'
                ),
                html,
                re.DOTALL,
            )
        )
        self.assertIsNotNone(row)
        self.assertEqual(
            self.words(
                matched(
                    re.search(r'<div class="wr-top">(.*?)</div>', row[1], re.DOTALL)
                )[1]
            ),
            "The interview waits for you 33m",
        )
        self.assertFalse(self.stack(html, self.CARD))
        self.assertNotIn("1 thing", html)
        self.assertNotIn(f'id="wait-stack-{self.CARD}"', html)
        # a page whose every task has one thing has no stack and the keys of today
        alone = str(
            pages.waits_page(
                pages.Ctx(
                    host="h",
                    workspace="w",
                    model=bm.derive(self.events()[:1], [], NOW),
                    asset=lambda name: name,
                )
            )
        )
        self.assertNotIn('<details class="wstack', alone)
        self.assertEqual(
            self.words(
                matched(
                    re.search(r'<div class="keys" id="waits-keys">(.*?)</div>', alone)
                )[1]
            ),
            "J K ↑ ↓ move · Enter go",
        )
        side = matched(
            re.search(
                (
                    r'<div id="waits" class="wlist[^"]*"[^>]*>(.*?)</div><div '
                    r'class="side-head">Views'
                ),
                alone,
                re.DOTALL,
            )
        )[1]
        self.assertNotIn("wi-n", side)

    def test_each_count_counts_a_stack_once(self) -> None:
        html = self.page()
        self.assertRegex(
            html,
            (
                r'<div class="side-head">Waits for you<em class="you" title="3 things '
                r'you do, in 2 tasks">2</em></div>'
            ),
        )
        self.assertRegex(html, r'id="view-waits"[^>]*>.*?<em>2</em></a>')
        self.assertRegex(
            html,
            (
                r'id="rail-waits" title="2 tasks wait for you"><svg[^>]*>.*?</svg><em '
                r'class="you">2</em></a>'
            ),
        )
        self.assertRegex(
            html,
            (
                r'<a class="m-waits you" href="[^"]+" aria-label="2 tasks wait for '
                r'you: open the list"><svg[^>]*>.*?</svg><span>2</span></a>'
            ),
        )
        self.assertIn(
            "<title>Waits for you · Lem · w · 0 build · 2 for you</title>", html
        )
        self.assertIn("2 tasks wait for you, the most pressing first", html)
        # the sidebar: one row for each task, the logo's its first thing's with how many
        # it has
        side = matched(
            re.search(
                (
                    r'<div id="waits" class="wlist[^"]*"[^>]*>(.*?)</div><div '
                    r'class="side-head">Views'
                ),
                html,
                re.DOTALL,
            )
        )[1]
        self.assertEqual(
            re.findall(r'<a class="wi[^"]*" id="(w-[a-z0-9-]+)"', side),
            [f"w-held-{self.CARD}", f"w-review-{self.LOGO}"],
        )
        self.assertIn('<span class="wi-n">2 things</span>', side)
        self.assertEqual(side.count("wi-n"), 1)
        # the server's count of the workspace, which /api/workspaces gives
        m = bm.derive(self.events(), [], NOW)
        space = types.SimpleNamespace(
            counted=float("-inf"),
            counts={},
            model=lambda: m,
            reader=types.SimpleNamespace(problems={}),
        )
        self.assertEqual(
            serve.Workspace.count(cast("serve.Workspace", space))["waits"], 2
        )
        self.assertEqual(len(bm.waits_of(m)), 3)


class Search(unittest.TestCase):
    """The search over every card, as the server draws it (criteria 1, 2, 4 and 5 of
    docs/plans/2026-11-22-board-card-search.md): closed on every page of the workspace,
    one row for each card with its title, its chip and the link a pick follows, and its
    button in the bar and in the phone's bar."""

    BACKLOG = {
        "folder": "docs/backlog",
        "reviewer_folder": ".lem/state/backlog",
        "items": [
            {
                "slug": "the-board-s-done-column-has-no-limit",
                "key": "the-board-s-done-column-has-no-limit",
                "path": "docs/backlog/the-board-s-done-column-has-no-limit.md",
                "title": "The board's done column has no limit",
                "worth": "yes",
            }
        ],
    }

    def ctx(self, **kw: object) -> pages.Ctx:
        events = [
            *ended(22),
            state(
                61, "held", "the criteria wait for the owner", task="board-card-search"
            ),
            state(62, "parked", "wait for the merchants", task="old-export-fix"),
        ]
        return pages.Ctx(
            host="h",
            workspace="w",
            model=bm.derive(events, [], NOW),
            asset=lambda name: name,
            backlog=self.BACKLOG,
            # each a field of Ctx, as the case names it
            **cast("dict[str, Any]", kw),
        )

    def box(self, html: str) -> str:
        found = re.findall(
            (
                r'<div class="search" id="search"[^>]*>.*?<div class="keys '
                r'search-keys" id="search-keys">.*?</div></div></div>'
            ),
            html,
            re.DOTALL,
        )
        self.assertEqual(len(found), 1)
        return found[0]

    def test_every_page_of_the_workspace_draws_the_box_once_closed_with_its_field(
        self,
    ) -> None:
        ctx = self.ctx()
        drawn = {
            "tasks": pages.kanban_page(ctx),
            "waits": pages.waits_page(ctx),
            "backlog": pages.backlog_page(ctx),
            "activity": pages.activity_page(ctx),
            "done": pages.older_page(ctx),
            "new": pages.new_page(ctx),
        }
        task_ctx = self.ctx()
        task_ctx.task = "board-card-search"
        drawn["task"] = task_pages.task_page(task_ctx)[1]
        native = self.ctx(native=True)
        native.task = "board-card-search"
        drawn["native"] = task_pages.task_page(native)[1]
        for name, page_ in drawn.items():
            box = self.box(str(page_))
            head = matched(re.match(r"<div[^>]*>", box))[0]
            self.assertNotIn("data-js-open", head, name)
            self.assertIn('data-controller="search"', head, name)
            self.assertIn('role="dialog"', head, name)
            self.assertRegex(
                box,
                r'<input id="search-q-w" type="search"[^>]*data-search-target="query"[^>]*data-turbo-permanent>',
                name,
            )
            self.assertIn('data-search-target="none" data-js-out', box, name)
            self.assertEqual(
                len(re.findall(r'<a class="sr ', box)), 22 + 2 + 1 + 1, name
            )

    def test_each_row_has_its_title_its_chip_and_the_link_a_card_has(self) -> None:
        ctx = self.ctx()
        html = str(pages.waits_page(ctx))
        box = self.box(html)

        def row(slug: str, kind: str = "task") -> re.Match[str]:
            return matched(
                re.search(
                    rf'<a class="sr [^"]*" id="sr-{kind}-{slug}"[^>]*>(.*?)</a>',
                    box,
                    re.DOTALL,
                )
            )

        held = row("board-card-search")
        self.assertIsNotNone(held)
        for attr in (
            'class="sr a-you"',
            'role="option"',
            'href="/h/w/tasks/board-card-search?in=waits"',
            'data-turbo-frame="task"',
            'data-turbo-action="advance"',
            'data-search-target="row"',
            'data-kind="task"',
            'data-slug="board-card-search"',
            'data-title="Board card search"',
            'data-open="1"',
        ):
            self.assertIn(attr, held[0])
        self.assertIn(
            (
                '<span class="sr-title">Board card search</span><span class="pill '
                'sr-chip"><i></i><span>Waits for you · held</span></span>'
            ),
            held[1],
        )
        parked = row("old-export-fix")
        self.assertIn('data-open="1"', parked[0])
        self.assertIn("<span>parked</span>", parked[1])
        # an ended task Done draws no card for: in the box, with no data-open, and its
        # chip the day it ended
        old = row("task-00")
        self.assertIsNotNone(old)
        self.assertNotIn('id="card-task-00"', str(pages.kanban_page(self.ctx())))
        self.assertNotIn("data-open", old[0])
        self.assertIn('class="sr a-done"', old[0])
        self.assertIn(
            f"<span>landed {bm.local(ctx.model.by_slug['task-00'].since).date().isoformat()}</span>",
            old[1],
        )
        item = row("the-board-s-done-column-has-no-limit", "item")
        for attr in (
            'class="sr a-gate"',
            'href="/h/w/backlog#item-the-board-s-done-column-has-no-limit"',
            'data-kind="item"',
            'data-title="The board&#x27;s done column has no limit"',
        ):
            self.assertIn(attr, item[0])
        self.assertNotIn("data-open", item[0])
        self.assertNotIn("data-turbo-frame", item[0])
        self.assertIn("<span>Backlog · worth: yes</span>", item[1])
        # the order: the columns, the parked task, the ended ones newest first,
        # the backlog
        order = re.findall(r'id="sr-([a-z]+-[a-z0-9-]+)"', box)
        self.assertEqual(
            order[:4],
            [
                "task-board-card-search",
                "task-builds",
                "task-old-export-fix",
                "task-task-21",
            ],
        )
        self.assertEqual(
            order[-2:], ["task-task-00", "item-the-board-s-done-column-has-no-limit"]
        )

    def test_the_bar_and_the_phones_bar_have_the_button_that_names_its_key(
        self,
    ) -> None:
        html = str(pages.activity_page(self.ctx()))
        for bar in ("bar", "mbar"):
            header = matched(
                re.search(rf'<header class="{bar}">(.*?)</header>', html, re.DOTALL)
            )
            self.assertIsNotNone(header, bar)
            button = matched(
                re.search(
                    r'<button class="btn search-open [^"]*"[^>]*>(.*?)</button>',
                    header[1],
                    re.DOTALL,
                )
            )
            self.assertIsNotNone(button, bar)
            self.assertIn("data-search-open", button[0])
            self.assertIn('aria-controls="search"', button[0])
            self.assertRegex(button[0], r'title="[^"]*Cmd-K[^"]*"')
            self.assertRegex(button[0], r'aria-label="[^"]*Cmd-K[^"]*"')
            self.assertIn('<use href="#i-magnifying-glass">', button[1])
        self.assertIn('<symbol id="i-magnifying-glass"', html)


class StandsNote(unittest.TestCase):
    """The note of the owner's merge that stands (`act_note`, state `stands`): a wait
    with no "Not done.", drawn only while his merge stands for the note's tip, with the
    sentence of the span that holds now (guard-sees-unreadable-sessions,
    2026-11-23, #60)."""

    TIP = "faac6eb3b" + "0" * 31
    NOTE = {
        "task": "gift-note",
        "act": "merge",
        "state": "stands",
        "tip": TIP,
        "said": (
            "Your merge stands. It goes through when the merge agent’s read of "
            "the new base says safe."
        ),
    }

    @staticmethod
    def ev(minute: float, event: str, **fields: object) -> dict:
        return {
            "ts": (START + timedelta(minutes=minute)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event": event,
            "task": "gift-note",
            **fields,
        }

    def refused(self) -> list:
        return [
            self.ev(0, "proposed", green=True, not_green=[], tip=self.TIP[:9]),
            state(
                1,
                "open",
                "pull request https://github.com/acme/shop/pull/60",
                task="gift-note",
            ),
            self.ev(
                8,
                "merge.refused",
                by="owner",
                via="server",
                kind="base",
                said="origin/main moved after the checks ran",
                tip=self.TIP[:9],
                **{"from": "lem"},
            ),
        ]

    def note(self, events: list) -> str:
        return str(pages.act_note(ctx_of(events), self.NOTE) or "")

    def test_while_the_read_runs_the_note_says_his_merge_stands_in_the_look_of_a_wait(
        self,
    ) -> None:
        html = self.note(self.refused())
        self.assertIn(
            (
                "Your merge stands. It goes through when the merge agent’s read of "
                "the new base says safe."
            ),
            html,
        )
        self.assertIn("a-gate", html)
        self.assertIn("#i-clock", html)
        self.assertNotIn("Not done.", html)
        self.assertNotIn("v-word", html)

    def test_once_the_server_runs_it_the_note_says_the_sentence_of_that_span(
        self,
    ) -> None:
        safe = self.ev(
            11,
            "merge.review",
            verdict="call",
            calls=True,
            by="claude",
            tip=self.TIP[:9],
            base="d48c6a9bd",
            base_call="safe",
            base_why="docs only",
        )
        stands = self.ev(
            11, "merge.stands", by="owner", tip=self.TIP[:9], base="d48c6a9bd"
        )
        html = self.note([*self.refused(), safe, stands])
        self.assertIn("Your merge stands. Lem merges it now.", html)
        self.assertNotIn("goes through when", html)

    def test_once_it_ends_the_note_is_not_drawn(self) -> None:
        merged = [
            *self.refused(),
            state(
                20,
                "landed",
                "main: pull request https://github.com/acme/shop/pull/60 is merged",
                task="gift-note",
            ),
        ]
        self.assertEqual(self.note(merged), "")
        # the server's merge of it started: the span ended, and a try that ends with no
        # refusal on record leaves the page as it is, with his Merge
        safe = self.ev(
            11,
            "merge.review",
            verdict="call",
            calls=True,
            by="claude",
            tip=self.TIP[:9],
            base="d48c6a9bd",
            base_call="safe",
            base_why="docs only",
        )
        started = [
            *self.refused(),
            safe,
            self.ev(11, "merge.stands", by="owner", tip=self.TIP[:9], base="d48c6a9bd"),
            self.ev(
                12,
                "merge.start",
                by="owner",
                via="server",
                after="a read of the moved base",
                base="d48c6a9bd",
            ),
        ]
        self.assertEqual(self.note(started), "")
        # a new proposal carried his merge to another tip: the note of the old tip is
        # not drawn
        carried = [
            *self.refused(),
            self.ev(13, "proposed", green=True, not_green=[], tip="def456789"),
            state(
                14,
                "open",
                "pull request https://github.com/acme/shop/pull/60",
                task="gift-note",
            ),
            self.ev(
                14,
                "merge.stands",
                by="owner",
                tip="def456789",
                **{"from": self.TIP[:9]},
            ),
        ]
        self.assertEqual(self.note(carried), "")


class StoppedChip(unittest.TestCase):
    """docs/backlog/a-stopped-task-s-card-on-the-kanban-has-no-chip-of-its-own.md: a
    task in landing whose live session the guard logged as stopped has the row "Its
    session stopped" in "Waits for you", and its card on the kanban says so too."""

    def chips(self, *, stopped: bool, live: bool = True) -> str:
        events = [
            state(0, "landing", "the checks run", task="gift-note"),
            {
                **state(1, "landing", "", task="gift-note"),
                "event": "session.open",
                "session": "S1",
                "name": "gift-note",
                "phase": "land",
                "why": "handoff",
            },
        ]
        if stopped:
            events.append(
                {
                    **state(50, "landing", "", task="gift-note"),
                    "event": "session.stopped",
                    "session": "S1",
                }
            )
        ctx = ctx_of(events)
        ctx.model.sessions = {
            "gift-note": {"live": live, "agent": live, "session": "S1"}
        }
        t = ctx.model.by_slug["gift-note"]
        return "".join(str(c) for c in pages.card_chips(ctx, t))

    def test_a_stopped_session_has_its_chip_on_the_card(self) -> None:
        chips = self.chips(stopped=True)
        self.assertIn("<span>session stopped</span>", chips)
        self.assertNotIn("no session", chips)
        self.assertNotIn("session stopped", self.chips(stopped=False))
        # a stopped session that is gone from agterm is "no session", never both
        gone = self.chips(stopped=True, live=False)
        self.assertIn("<span>no session</span>", gone)
        self.assertNotIn("session stopped", gone)


class ReviewerItems(unittest.TestCase):
    """The reviewer's items on the Backlog view (criteria 6 and 7 of
    docs/plans/2026-11-23-scheduled-runs-one-branch.md): a group of their own, each
    undecided one with "Start a task" and "Drop", which post its path; a held one with
    the task that holds it and no act; an item of the backlog folder with no "Drop"; and
    the count of the undecided ones on the "Backlog" key."""

    BACKLOG = {
        "folder": "docs/backlog",
        "reviewer_folder": ".lem/state/backlog",
        "read": "2026-11-20T10:00:00Z",
        "items": [
            {
                "slug": "tests-flaky-check",
                "key": "tests-flaky-check",
                "path": "docs/backlog/tests-flaky-check.md",
                "reviewer": False,
                "title": "A developer's item of the same stem",
                "worth": "later",
                "where": "",
                "added": "",
                "state": "",
                "body": "Mine.",
            },
            {
                "slug": "the-board-s-colors",
                "key": "-the-board-s-colors",
                "path": ".lem/state/backlog/the-board-s-colors.md",
                "reviewer": True,
                "held": None,
                "title": "The board's colors",
                "worth": "later",
                "where": "",
                "added": "",
                "state": "",
                "body": (
                    "The reviewer passed 1 proposal about the board on 2026-11-23: "
                    "retro of 2026-11-23 #7."
                ),
            },
            {
                "slug": "tests-flaky-check",
                "key": "-tests-flaky-check",
                "path": ".lem/state/backlog/tests-flaky-check.md",
                "reviewer": True,
                "held": {"task": "tests-flaky-check", "status": "building"},
                "title": "A check of the board fails by chance",
                "worth": "later",
                "where": "",
                "added": "",
                "state": "",
                "body": "From the night of 2026-11-24, proposal 1.",
            },
        ],
    }

    def page(self, *, can_act: bool = True, more: list | None = None) -> str:
        events = [
            state(1, "building", "task 1 of 2", task="tests-flaky-check"),
            *(more or []),
        ]
        return str(
            pages.backlog_page(
                pages.Ctx(
                    host="h",
                    workspace="w",
                    model=bm.derive(events, [], NOW),
                    asset=lambda name: name,
                    backlog=self.BACKLOG,
                    can_act=can_act,
                )
            )
        )

    def item(self, html: str, key: str) -> str:
        return html.split(f'id="item-{key}"', 1)[1].split("</details>", 1)[0]

    def test_the_reviewer_s_group_comes_first_the_undecided_one_first(self) -> None:
        html = self.page()
        group = html.split('id="group-reviewer"', 1)[1].split('class="bl-group', 1)[0]
        self.assertIn("The reviewer&#x27;s items", group)
        self.assertLess(
            group.index('id="item--the-board-s-colors"'),
            group.index('id="item--tests-flaky-check"'),
        )
        self.assertNotIn('id="item-tests-flaky-check"', group)
        self.assertLess(
            html.index('id="group-reviewer"'), html.index('id="item-tests-flaky-check"')
        )

    def test_an_undecided_item_has_start_and_drop_each_posting_its_path(self) -> None:
        undecided = self.item(self.page(), "-the-board-s-colors")
        self.assertIn(">undecided<", undecided)
        self.assertIn('action="/h/w/start"', undecided)
        self.assertIn('action="/h/w/backlog/drop"', undecided)
        self.assertEqual(
            undecided.count(
                'name="item" value=".lem/state/backlog/the-board-s-colors.md"'
            ),
            2,
        )
        self.assertIn("<span>Drop</span>", undecided)
        # the proposal's name is code, so that its number is no link to a pull request
        self.assertIn("`retro of 2026-11-23 #7`", undecided)

    def test_a_held_item_names_its_task_and_has_no_act(self) -> None:
        held = self.item(self.page(), "-tests-flaky-check")
        self.assertIn(">held by tests-flaky-check<", held)
        self.assertIn("(building) builds this item", held)
        self.assertNotIn("<form", held)

    def test_an_item_of_the_backlog_folder_has_no_drop_and_starts_by_its_path(
        self,
    ) -> None:
        mine = self.item(self.page(), "tests-flaky-check")
        self.assertIn('name="item" value="docs/backlog/tests-flaky-check.md"', mine)
        self.assertNotIn("backlog/drop", mine)

    def test_an_item_of_the_backlog_folder_that_a_task_builds_shows_it_and_no_start(
        self,
    ) -> None:
        # docs/backlog/a-backlog-item-never-shows-that-it-has-a-task.md: the task the
        # board's "Start a task" opened, whose ask is the item's path, builds it
        building = {
            **state(2, "building", "task 1 of 2", task="flaky-fix"),
            "ask": "docs/backlog/tests-flaky-check.md",
        }
        mine = self.item(self.page(more=[building]), "tests-flaky-check")
        self.assertIn(">held by flaky-fix<", mine)
        self.assertIn("(building) builds this item", mine)
        self.assertIn('href="/h/w/tasks/flaky-fix', mine)
        self.assertNotIn("<form", mine)
        # a whole path under the main checkout, as the night may write it, is the
        # same item; a dropped task gives "Start a task" back
        night = {**building, "ask": "/Users/dev/shop/docs/backlog/tests-flaky-check.md"}
        self.assertIn(
            ">held by flaky-fix<",
            self.item(self.page(more=[night]), "tests-flaky-check"),
        )
        dropped = {**state(3, "dropped", "not needed", task="flaky-fix"), "ask": ""}
        again = self.item(self.page(more=[building, dropped]), "tests-flaky-check")
        self.assertNotIn("held by", again)
        self.assertIn('action="/h/w/start"', again)

    def test_the_backlog_key_counts_the_undecided_items_of_the_reviewer(self) -> None:
        html = self.page()
        key = matched(
            re.search(r'<a class="vbtn" id="view-backlog"[^>]*>(.*?)</a>', html)
        )[1]
        self.assertRegex(
            key,
            (
                r"<em title=\"The reviewer&#x27;s items that wait for your "
                r"start or drop\">1</em>"
            ),
        )
        self.assertRegex(
            matched(
                re.search(
                    r'<a class="rbtn" href="[^"]*" id="rail-backlog"[^>]*>(.*?)</a>',
                    html,
                )
            )[1],
            r"<em>1</em>",
        )

    def test_a_page_that_cannot_act_gives_the_line_to_type_and_no_form(self) -> None:
        undecided = self.item(self.page(can_act=False), "-the-board-s-colors")
        self.assertIn("/lem new .lem/state/backlog/the-board-s-colors.md", undecided)
        self.assertIn(
            "Drop it on this board on the Mac or through the tailnet door.", undecided
        )
        self.assertNotIn("<form", undecided)


class RefutedAndAddedBy(unittest.TestCase):
    """Criteria 4 and 5 of docs/plans/2026-11-23-backlog-refuted-items-and-jev.md on the
    Backlog view: a reviewer's refuted item (`worth: no`) is under "Decided against"
    with no "Drop" and no count on the key, and each card says who added its item, on
    which day and in which task."""

    @staticmethod
    def mine(stem: str, worth: str, held: dict | None = None) -> dict:
        return {
            "slug": stem,
            "key": f"-{stem}",
            "path": f".lem/state/backlog/{stem}.md",
            "reviewer": True,
            "held": held,
            "title": stem.replace("-", " ").capitalize(),
            "worth": worth,
            "where": "",
            "added": "2026-11-20",
            "state": "",
            "body": (
                "From the retro of 2026-11-20.\n\nDecided against: "
                "a first-time lesson, with no question in it."
            ),
        }

    @staticmethod
    def folder(stem: str, added_by: dict | None) -> dict:
        return {
            "slug": stem,
            "key": stem,
            "path": f"docs/backlog/{stem}.md",
            "reviewer": False,
            "added_by": added_by,
            "title": stem.replace("-", " ").capitalize(),
            "worth": "later",
            "where": "",
            "added": "2026-11-20",
            "state": "" if added_by else "new",
            "body": "What happens.",
        }

    def page(
        self, items: list, *, can_act: bool = True, events: list | None = None
    ) -> str:
        backlog = {
            "folder": "docs/backlog",
            "reviewer_folder": ".lem/state/backlog",
            "read": "2026-11-20T10:00:00Z",
            "items": items,
        }
        return str(
            pages.backlog_page(
                pages.Ctx(
                    host="h",
                    workspace="w",
                    model=bm.derive(events or [], [], NOW),
                    asset=lambda name: name,
                    backlog=backlog,
                    can_act=can_act,
                )
            )
        )

    def item(self, html: str, key: str) -> str:
        return html.split(f'id="item-{key}"', 1)[1].split("</details>", 1)[0]

    def test_criterion_4_two_waiting_and_one_refuted_give_2_on_the_key_and_3_in_the_view_the_refuted_one_under_decided_against(
        self,
    ) -> None:
        html = self.page(
            [
                self.mine("the-board-s-colors", "later"),
                self.mine("run-make-lint-before-each-commit", "no"),
                self.mine("a-flaky-check", "later"),
            ]
        )
        key = matched(
            re.search(r'<a class="vbtn" id="view-backlog"[^>]*>(.*?)</a>', html)
        )[1]
        self.assertRegex(
            key,
            (
                r"<em title=\"The reviewer&#x27;s items that wait for your "
                r"start or drop\">2</em>"
            ),
        )
        self.assertEqual(len(re.findall(r'<details class="bl-item"', html)), 3)
        reviewer = html.split('id="group-reviewer"', 1)[1].split('class="bl-group', 1)[
            0
        ]
        self.assertNotIn('id="item--run-make-lint-before-each-commit"', reviewer)
        against = html.split('id="group-no"', 1)[1]
        self.assertIn("Decided against", against.split('class="bl-item"', 1)[0])
        refuted = self.item(html, "-run-make-lint-before-each-commit")
        self.assertIn('id="item--run-make-lint-before-each-commit"', against)
        self.assertNotIn("Drop", refuted)
        self.assertNotIn(">undecided<", refuted)
        # it can still start a task, as any item can
        self.assertIn('action="/h/w/start"', refuted)
        self.assertIn("3 of the reviewer in .lem/state/backlog, 2 undecided", html)
        # a page that cannot act does not tell to drop it either
        self.assertNotIn(
            "Drop it on this board",
            self.item(
                self.page(
                    [self.mine("run-make-lint-before-each-commit", "no")], can_act=False
                ),
                "-run-make-lint-before-each-commit",
            ),
        )

    def test_criterion_5_the_card_says_who_added_the_item_on_which_day_and_in_which_task(
        self,
    ) -> None:
        stem = "clean-refuses-a-branch-rebased-after-its-push-and-blames-the-forge"
        by = {
            "author": "pySilver",
            "day": "2026-11-22",
            "task": "seat-defaults-and-fallback",
            "pull": "",
        }
        card = self.item(self.page([self.folder(stem, by)]), stem)
        self.assertIn(
            (
                '<div class="bl-note bl-by">added by pySilver on 2026-11-22, '
                "in task <code>seat-defaults-and-fallback</code></div>"
            ),
            card,
        )
        # a task this board has is a link to its board
        linked = self.item(
            self.page(
                [self.folder(stem, by)],
                events=[
                    state(1, "landed", "merged", task="seat-defaults-and-fallback")
                ],
            ),
            stem,
        )
        self.assertRegex(
            linked,
            r'added by pySilver on 2026-11-22, in task <a class="bl-task" [^>]*href="/h/w/tasks/seat-defaults-and-fallback[^"]*"[^>]*>seat-defaults-and-fallback</a>',
        )
        # a commit that names no task but its pull request; one that names neither; an
        # item git does not have yet
        pull = self.item(
            self.page([self.folder(stem, {**by, "task": "", "pull": "88"})]), stem
        )
        self.assertIn(">added by pySilver on 2026-11-22, in pull request #88<", pull)
        bare = self.item(self.page([self.folder(stem, {**by, "task": ""})]), stem)
        self.assertIn(">added by pySilver on 2026-11-22<", bare)
        self.assertIn(
            '<div class="bl-note bl-by">not committed yet</div>',
            self.item(self.page([self.folder(stem, None)]), stem),
        )
        # no answer from git: no line; a reviewer's item, which git never holds: the
        # reviewer and its day
        nothing = self.folder(stem, None)
        del nothing["added_by"]
        self.assertNotIn("bl-by", self.item(self.page([nothing]), stem))
        self.assertIn(
            (
                "added by the reviewer of the night&#x27;s and the retro&#x27;s "
                "proposals on 2026-11-20"
            ),
            self.item(
                self.page([self.mine("the-board-s-colors", "later")]),
                "-the-board-s-colors",
            ),
        )


class ItemSlug(unittest.TestCase):
    """The slug of a task started from a backlog item (`serve.item_slug`): the stem, or
    the stem with the first free `-2`, `-3` when a task of the stem ended, so that an
    item whose task was dropped starts again (criterion 9 and the plan's task 2)."""

    def test_the_stem_while_no_task_of_it_ended(self) -> None:
        self.assertEqual(
            serve.item_slug(
                "tests-flaky-check", lambda slug: False, lambda slug: False
            ),
            "tests-flaky-check",
        )

    def test_the_first_free_number_after_a_task_of_the_stem_ended(self) -> None:
        taken = {"tests-flaky-check", "tests-flaky-check-2"}
        self.assertEqual(
            serve.item_slug(
                "tests-flaky-check",
                lambda slug: slug == "tests-flaky-check",
                taken.__contains__,
            ),
            "tests-flaky-check-3",
        )
        self.assertEqual(
            serve.item_slug("tests-flaky-check", lambda slug: True, lambda slug: False),
            "tests-flaky-check-2",
        )

    def test_a_stem_that_is_no_slug_gives_its_plain_words(self) -> None:
        self.assertEqual(
            serve.item_slug("Two_Guides", lambda slug: False, lambda slug: False),
            "two-guides",
        )


if __name__ == "__main__":
    unittest.main()
