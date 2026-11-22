"""lem_board_pages.py's rules, each a page drawn from a model of a few events: what the kanban's Done
column draws of the ended tasks, its foot row, and the page that lists the ended tasks it has no card for.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
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


if __name__ == "__main__":
    unittest.main()
