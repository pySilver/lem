"""lem_board_pages.py's rules, each a page drawn from a model of a few events: what the kanban's Done
column draws of the ended tasks, its foot row, the page that lists the ended tasks it has no card for, and the
kanban's mark over its cards and its line of keys.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import json
import re
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
bm = importlib.import_module("lem_board_model")
pages = importlib.import_module("lem_board_pages")
task_pages = importlib.import_module("lem_board_task")
serve = importlib.import_module("serve")

START = datetime(2026, 11, 20, 9, 0, tzinfo=timezone.utc)
NOW = int((START + timedelta(hours=2)).timestamp() * 1000)
ENDED = ("landed", "dropped", "answered")


def state(minute: float, status: str, text: str, *lines: str, task: str) -> dict:
    return {"ts": (START + timedelta(minutes=minute)).strftime("%Y-%m-%dT%H:%M:%SZ"), "event": "task.state", "task": task,
            "status": status, "text": text, "lines": list(lines)}


def ended(n: int) -> list:
    """N ended tasks, task-00 the first to end and each next one a minute later, landed, dropped and
    answered in turn; task-02 landed with its pull request. One task builds beside them."""
    events = []
    for i in range(n):
        lines = ("pull request https://github.com/acme/shop/pull/41",) if i == 2 else ()
        events.append(state(i, ENDED[i % 3], "it ended", *lines, task=f"task-{i:02d}"))
    return [*events, state(60, "building", "task 1 of 2", task="builds")]


def ctx_of(events: list) -> "pages.Ctx":
    return pages.Ctx(host="h", workspace="w", model=bm.derive(events, [], NOW), asset=lambda name: name)


def column(html: str, key: str) -> str:
    """One column of the kanban, from its section to the next one."""
    return re.split(r'<section class="col [^"]*" id="col-', html.split(f'id="col-{key}"', 1)[1])[0]


def cards(html: str) -> list:
    return re.findall(r'<article[^>]*id="card-([a-z0-9-]+)"', html)


class Done(unittest.TestCase):
    def test_done_draws_the_20_tasks_that_ended_last_the_newest_on_top(self):
        html = str(pages.kanban_page(ctx_of(ended(25))))
        self.assertEqual(cards(column(html, "done")), [f"task-{i:02d}" for i in range(24, 4, -1)])
        for i in range(5):
            self.assertNotIn(f'id="card-task-{i:02d}"', html)

    def test_dones_head_and_its_phone_tab_count_every_ended_task(self):
        html = str(pages.kanban_page(ctx_of(ended(25))))
        self.assertEqual(len(cards(column(html, "done"))), 20)
        self.assertRegex(column(html, "done"), r'<span class="col-name">Done</span><em>25</em>')
        self.assertRegex(html, r'id="ktab-done"[^>]*><i></i>Done<em>25</em></button>')

    def test_a_row_under_the_20_cards_counts_the_rest_and_leads_to_their_list(self):
        done = column(str(pages.kanban_page(ctx_of(ended(25)))), "done")
        row = re.search(r'<a class="col-more" id="done-older" href="([^"]+)"[^>]*>(.*?)</a>', done)
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "/h/w/done")
        self.assertIn("<span>5 older</span>", row[2])
        self.assertGreater(done.index('id="done-older"'), done.index('id="card-task-05"'))

    def test_with_20_ended_tasks_or_fewer_done_draws_each_and_no_row(self):
        for n in (20, 3):
            done = column(str(pages.kanban_page(ctx_of(ended(n)))), "done")
            self.assertEqual(len(cards(done)), n)
            self.assertNotIn("done-older", done)

    def test_the_list_is_a_page_of_the_board_whose_tasks_link_goes_back_to_the_columns(self):
        self.assertEqual(serve.PAGES["done"], "older_page")
        html = str(getattr(pages, serve.PAGES["done"])(ctx_of(ended(25))))
        self.assertIn('id="side"', html)
        self.assertRegex(html, r'<a class="vbtn" id="view-tasks" href="/h/w/"')
        self.assertNotIn('id="view-done"', html)
        self.assertIn('<h2>Older ended tasks</h2>', html)


class Older(unittest.TestCase):
    def rows(self, html: str) -> list:
        return re.findall(r'<div class="row [^"]*" id="older-([a-z0-9-]+)">(.*?)</span></div>', html)

    def test_it_lists_the_tasks_done_has_no_card_for_newest_first_each_with_how_and_when_it_ended(self):
        ctx = ctx_of(ended(25))
        html = str(pages.older_page(ctx))
        rows = self.rows(html)
        self.assertEqual([slug for slug, _ in rows], ["task-04", "task-03", "task-02", "task-01", "task-00"])
        words = {slug: re.sub(r"<[^>]+>", " ", body) for slug, body in rows}
        for slug, how in (("task-04", "Dropped"), ("task-03", "Landed"), ("task-02", "Answered"), ("task-01", "Dropped"), ("task-00", "Landed")):
            t = ctx.model.by_slug[slug]
            self.assertIn(t.title, words[slug])
            self.assertIn(how, words[slug])
            self.assertIn(bm.stamp(t.since, NOW), words[slug])

    def test_each_row_opens_the_tasks_board_over_the_list_and_its_pull_request_when_it_has_one(self):
        html = str(pages.older_page(ctx_of(ended(25))))
        rows = dict(self.rows(html))
        self.assertIn('href="/h/w/tasks/task-04?in=done"', rows["task-04"])
        self.assertIn('data-turbo-frame="task"', rows["task-04"])
        self.assertIn('href="https://github.com/acme/shop/pull/41"', rows["task-02"])
        self.assertNotIn("github.com", rows["task-03"])

    def test_a_task_opened_from_the_list_lies_over_the_list_and_closes_back_to_it(self):
        ctx = ctx_of(ended(25))
        ctx.view, ctx.task = "done", "task-04"
        status, html = task_pages.task_page(ctx)
        self.assertEqual(status, 200)
        self.assertIn('id="older-task-04"', str(html))
        self.assertIn('class="ibtn p-close" href="/h/w/done"', str(html))

    def test_with_no_older_task_the_list_says_done_shows_every_one(self):
        html = str(pages.older_page(ctx_of(ended(20))))
        self.assertEqual(self.rows(html), [])
        self.assertIn("Done shows every ended task", html)


class Views(unittest.TestCase):
    def test_each_view_button_shows_its_plain_key_on_the_button_and_takes_that_key(self):
        html = str(pages.kanban_page(ctx_of(ended(3))))
        for key, label, kbd in (("tasks", "Tasks", "T"), ("waits", "Waits for you", "W"), ("backlog", "Backlog", "B"), ("activity", "Activity", "A")):
            button = re.search(rf'<a class="vbtn" id="view-{key}"[^>]*>(.*?)</a>', html)
            self.assertIsNotNone(button, key)
            self.assertIn(f'data-hotkey="Key{kbd}"', button[0])
            self.assertIn(f"{label}<kbd>{kbd}</kbd>", button[1])
            self.assertIn(f'title="Key {kbd}, with no Shift"', button[0])


class SideFold(unittest.TestCase):
    """The one arrow at the sidebar's foot that folds it to a rail and unfolds it."""

    def page(self, rail: bool) -> str:
        ctx = ctx_of(ended(3))
        ctx.prefs = {"rail": True} if rail else {}
        return str(pages.kanban_page(ctx))

    def fold(self, html: str) -> re.Match:
        return re.search(r'<button id="side-fold" class="ibtn" type="button" data-action="fold#side" title="([^"]+)" aria-label="([^"]+)">'
                         r'<svg class="ic" aria-hidden="true"><use href="#i-chevron-left"></use></svg></button>', html)

    def test_an_open_sidebar_has_an_arrow_that_points_left_at_its_foot_and_the_old_icon_is_gone(self):
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

    def test_a_folded_sidebar_keeps_the_arrow_at_its_foot_and_it_unfolds_it(self):
        html = self.page(rail=True)
        self.assertRegex(html, r'<div class="shell railed" id="shell"')
        found = self.fold(html)
        self.assertIsNotNone(found)
        self.assertEqual((found[1], found[2]), ("Unfold the sidebar", "Unfold the sidebar"))
        self.assertIn('id="side-fold"', html.split('id="side-foot"', 1)[1].split("</aside>", 1)[0])

    def test_the_rail_shows_the_foot_with_the_arrow_alone_turned_to_the_right(self):
        css = (pages.ASSETS / "board.css").read_text(encoding="utf-8")
        hidden = re.search(r"\.shell\.railed \.side > :not\(([^)]*)\) \{ display: none !important; \}", css)
        self.assertIsNotNone(hidden)
        self.assertIn(".side-foot", hidden[1])
        self.assertIn(".shell.railed .side-foot > :not(#side-fold) { display: none; }", css)
        self.assertIn(".shell.railed #side-fold .ic { transform: scaleX(-1); }", css)

    def test_a_click_says_the_next_click_on_the_arrow(self):
        script = (pages.ASSETS / "vendor" / "board-app.js").read_text(encoding="utf-8")
        self.assertIn('"Unfold the sidebar":"Fold the sidebar"', script)
        self.assertNotIn("sidebar", json.loads(pages.ICONS.read_text(encoding="utf-8")))


class Keys(unittest.TestCase):
    def test_the_kanban_carries_the_cursor_over_its_cards_and_one_line_of_its_keys(self):
        html = str(pages.kanban_page(ctx_of(ended(3))))
        kanban = re.search(r'<div class="view kanban" id="kanban"[^>]*>', html)[0]
        for attr in ('data-controller="cursor"', 'data-cursor-item-value="article.tc"', 'data-cursor-group-value="section.col"',
                     'data-cursor-link-value=".tc-link"', 'data-action="keydown@window-&gt;cursor#key click-&gt;cursor#pick"'):
            self.assertIn(attr, kanban)
        line = re.search(r'<div class="keys" id="kanban-keys">(.*?)</div>', html)
        self.assertIsNotNone(line)
        self.assertEqual(" ".join(re.sub(r"<[^>]+>", " ", line[1]).split()), "J K ↑ ↓ move · H L ← → column · Enter open · Esc close")
        self.assertEqual(re.findall(r"<kbd>([^<]+)</kbd>", line[1]), ["J", "K", "↑", "↓", "H", "L", "←", "→", "Enter", "Esc"])
        self.assertEqual(html.count('class="keys"'), 1)


class WaitsVerb(unittest.TestCase):
    """The verb of a row of "Waits for you" goes where the owner acts: on a page for this Mac, for a row he
    answers in the task's session while it lives, the jump of agterm; elsewhere the task's panel alone."""

    OPEN = {"ts": (START + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ"), "event": "session.open", "task": "gift-note", "session": "S1", "name": "gift-note"}

    def verb(self, *events, row="held", local=True, sessions=None) -> str:
        """The verb link of the row ROW-gift-note"""
        m = bm.derive([self.OPEN, *events], [], NOW)
        m.sessions = {"gift-note": {"live": True, "agent": True, "session": "S1"}} if sessions is None else sessions
        html = str(pages.waits_page(pages.Ctx(host="h", workspace="w", model=m, asset=lambda name: name, local=local)))
        verbs = re.findall(rf'<article class="wrow[^"]*" id="wait-{row}-gift-note"[^>]*>.*?(<a class="wr-verb"[^>]*>)', html)
        self.assertEqual(len(verbs), 1, verbs)
        return verbs[0]

    def test_a_held_row_on_a_page_for_this_mac_with_a_live_session_jumps_to_it_and_keeps_its_address(self):
        verb = self.verb(state(2, "held", "the interview waits for the owner", task="gift-note"))
        self.assertIn('data-action="agterm#jump"', verb)
        self.assertIn('data-agterm-session-param="S1"', verb)
        self.assertIn('href="/h/w/tasks/gift-note?in=waits"', verb)

    def test_no_jump_on_a_page_that_is_not_for_this_mac_or_with_no_live_session(self):
        held = state(2, "held", "the interview waits for the owner", task="gift-note")
        for verb in (self.verb(held, local=False), self.verb(held, sessions={"gift-note": {"live": False, "session": "S1"}})):
            self.assertNotIn("agterm#jump", verb)
            self.assertNotIn("data-agterm-session-param", verb)
            self.assertIn('href="/h/w/tasks/gift-note?in=waits"', verb)

    def test_no_jump_for_a_merge_row(self):
        verb = self.verb(state(2, "open", "pull request https://github.com/acme/shop/pull/41", task="gift-note"), row="merge")
        self.assertNotIn("agterm#jump", verb)
        self.assertIn('href="/h/w/tasks/gift-note?in=waits"', verb)

    def test_the_list_carries_the_cursor_over_its_rows_and_one_line_of_its_keys(self):
        m = bm.derive([self.OPEN, state(2, "held", "the interview waits for the owner", task="gift-note")], [], NOW)
        html = str(pages.waits_page(pages.Ctx(host="h", workspace="w", model=m, asset=lambda name: name)))
        listing = re.search(r'<div class="waits-list" id="waits-list"[^>]*>', html)
        self.assertIsNotNone(listing)
        for attr in ('data-controller="cursor"', 'data-cursor-item-value="article.wrow"', 'data-cursor-link-value="a.wr-verb"',
                     'data-cursor-pick-value="a.wr-verb, a.wr-task"', 'data-action="keydown@window-&gt;cursor#key click-&gt;cursor#pick"'):
            self.assertIn(attr, listing[0])
        self.assertNotIn("data-cursor-group-value", listing[0])
        line = re.search(r'<div class="keys" id="waits-keys">(.*?)</div>', html)
        self.assertIsNotNone(line)
        self.assertEqual(" ".join(re.sub(r"<[^>]+>", " ", line[1]).split()), "J K ↑ ↓ move · Enter go")
        self.assertEqual(html.count('class="keys"'), 1)
        # the title link of the row opens the panel and carries no jump
        self.assertNotIn("agterm", re.search(r'<a class="wr-task"[^>]*>', html)[0])

    def test_with_nothing_waiting_no_line_of_keys(self):
        html = str(pages.waits_page(ctx_of(ended(2))))
        self.assertIn("Nothing waits for you.", html)
        self.assertNotIn('id="waits-keys"', html)


class Search(unittest.TestCase):
    """The search over every card, as the server draws it (criteria 1, 2, 4 and 5 of
    docs/plans/2026-11-22-board-card-search.md): closed on every page of the workspace, one row for each card
    with its title, its chip and the link a pick follows, and its button in the bar and in the phone's bar."""

    BACKLOG = {"folder": "docs/backlog", "items": [{"slug": "the-board-s-done-column-has-no-limit", "path": "docs/backlog/the-board-s-done-column-has-no-limit.md",
                                                     "title": "The board's done column has no limit", "worth": "yes"}]}

    def ctx(self, **kw) -> "pages.Ctx":
        events = [*ended(22), state(61, "held", "the criteria wait for the owner", task="board-card-search"),
                  state(62, "parked", "wait for the merchants", task="old-export-fix")]
        return pages.Ctx(host="h", workspace="w", model=bm.derive(events, [], NOW), asset=lambda name: name, backlog=self.BACKLOG, **kw)

    def box(self, html: str) -> str:
        found = re.findall(r'<div class="search" id="search"[^>]*>.*?<div class="keys search-keys" id="search-keys">.*?</div></div></div>', html, re.S)
        self.assertEqual(len(found), 1)
        return found[0]

    def test_every_page_of_the_workspace_draws_the_box_once_closed_with_its_field(self):
        ctx = self.ctx()
        drawn = {"tasks": pages.kanban_page(ctx), "waits": pages.waits_page(ctx), "backlog": pages.backlog_page(ctx), "activity": pages.activity_page(ctx),
                 "done": pages.older_page(ctx), "new": pages.new_page(ctx)}
        task_ctx = self.ctx()
        task_ctx.task = "board-card-search"
        drawn["task"] = task_pages.task_page(task_ctx)[1]
        native = self.ctx(native=True)
        native.task = "board-card-search"
        drawn["native"] = task_pages.task_page(native)[1]
        for name, page_ in drawn.items():
            box = self.box(str(page_))
            head = re.match(r"<div[^>]*>", box)[0]
            self.assertNotIn("data-js-open", head, name)
            self.assertIn('data-controller="search"', head, name)
            self.assertIn('role="dialog"', head, name)
            self.assertRegex(box, r'<input id="search-q-w" type="search"[^>]*data-search-target="query"[^>]*data-turbo-permanent>', name)
            self.assertIn('data-search-target="none" data-js-out', box, name)
            self.assertEqual(len(re.findall(r'<a class="sr ', box)), 22 + 2 + 1 + 1, name)

    def test_each_row_has_its_title_its_chip_and_the_link_a_card_has(self):
        ctx = self.ctx()
        html = str(pages.waits_page(ctx))
        box = self.box(html)
        row = lambda slug, kind="task": re.search(rf'<a class="sr [^"]*" id="sr-{kind}-{slug}"[^>]*>(.*?)</a>', box, re.S)  # noqa: E731
        held = row("board-card-search")
        self.assertIsNotNone(held)
        for attr in ('class="sr a-you"', 'role="option"', 'href="/h/w/tasks/board-card-search?in=waits"', 'data-turbo-frame="task"', 'data-turbo-action="advance"',
                     'data-search-target="row"', 'data-kind="task"', 'data-slug="board-card-search"', 'data-title="Board card search"', 'data-open="1"'):
            self.assertIn(attr, held[0])
        self.assertIn('<span class="sr-title">Board card search</span><span class="pill sr-chip"><i></i><span>Waits for you · held</span></span>', held[1])
        parked = row("old-export-fix")
        self.assertIn('data-open="1"', parked[0])
        self.assertIn("<span>parked</span>", parked[1])
        # an ended task Done draws no card for: in the box, with no data-open, and its chip the day it ended
        old = row("task-00")
        self.assertIsNotNone(old)
        self.assertNotIn('id="card-task-00"', str(pages.kanban_page(self.ctx())))
        self.assertNotIn("data-open", old[0])
        self.assertIn('class="sr a-done"', old[0])
        self.assertIn(f"<span>landed {bm.local(ctx.model.by_slug['task-00'].since).date().isoformat()}</span>", old[1])
        item = row("the-board-s-done-column-has-no-limit", "item")
        for attr in ('class="sr a-gate"', 'href="/h/w/backlog#item-the-board-s-done-column-has-no-limit"', 'data-kind="item"', 'data-title="The board&#x27;s done column has no limit"'):
            self.assertIn(attr, item[0])
        self.assertNotIn("data-open", item[0])
        self.assertNotIn("data-turbo-frame", item[0])
        self.assertIn("<span>Backlog · worth: yes</span>", item[1])
        # the order: the columns, the parked task, the ended ones newest first, the backlog
        order = re.findall(r'id="sr-([a-z]+-[a-z0-9-]+)"', box)
        self.assertEqual(order[:4], ["task-board-card-search", "task-builds", "task-old-export-fix", "task-task-21"])
        self.assertEqual(order[-2:], ["task-task-00", "item-the-board-s-done-column-has-no-limit"])

    def test_the_bar_and_the_phones_bar_have_the_button_that_names_its_key(self):
        html = str(pages.activity_page(self.ctx()))
        for bar in ("bar", "mbar"):
            header = re.search(rf'<header class="{bar}">(.*?)</header>', html, re.S)
            self.assertIsNotNone(header, bar)
            button = re.search(r'<button class="btn search-open [^"]*"[^>]*>(.*?)</button>', header[1], re.S)
            self.assertIsNotNone(button, bar)
            self.assertIn('data-search-open', button[0])
            self.assertIn('aria-controls="search"', button[0])
            self.assertRegex(button[0], r'title="[^"]*Cmd-K[^"]*"')
            self.assertRegex(button[0], r'aria-label="[^"]*Cmd-K[^"]*"')
            self.assertIn('<use href="#i-magnifying-glass">', button[1])
        self.assertIn('<symbol id="i-magnifying-glass"', html)


if __name__ == "__main__":
    unittest.main()
