#!/usr/bin/env python3
"""The board of a normal afternoon in one shop, for the README's pictures and for a look at the page.

    python3 tests/board-showcase.py DIR             the pictures, into DIR: board-*, task-*, backlog-*, dreams-*, light and dark
    python3 tests/board-showcase.py DIR --measure   also where the lanes start at 900, 1400 and 1800 px, as JSON

The fixture of tests/test-board.sh is a stress case (30 tasks, more places taken than the limit, 12
waits): right for its checks, wrong for a picture. This one is seven tasks a team could have on one
afternoon, written by Lem's own scripts (project.py, criteria.py) in a throwaway repository, with
every count possible: three places of four taken, one wait for the owner, one pull request.
The scripts write the events seconds apart, and their times are then moved to the minutes a run
would have spaced them. The board is drawn with its clock stopped at NOW, marked as demo data
(board.py --demo), and each picture is 1440 px wide at two device pixels for each pixel.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "lem" / "scripts"
NOW = datetime(2026, 11, 17, 15, 30, tzinfo=timezone.utc)
CHROMES = ("google-chrome", "chromium", "chromium-browser", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
# The dark theme as agterm gives it to a page: its background and its text color.
DARK = ":root { --agterm-background: #15181c; --agterm-foreground: #dde1e6; }"
WIDTH = 1440


def run(*args: str, cwd: Path | None = None) -> str:
    ran = subprocess.run(args, capture_output=True, text=True, cwd=cwd, env={**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"})
    if ran.returncode != 0:
        sys.exit(f"board-showcase: {' '.join(args[:4])}: {ran.stderr.strip() or ran.stdout.strip()}")
    return ran.stdout


class Shop:
    """A repository with Lem's settings, and the steps of each task with the minute (before NOW) it ran at."""

    def __init__(self, work: Path):
        self.repo = work / "shop"
        self.work = work
        self.times: dict[str, list[float]] = {}
        run("git", "init", "-q", "-b", "main", str(self.repo))
        (self.repo / "app.txt").write_text("one\n")
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "chore: start")
        self.project("init", "--base", "main")
        toml = self.repo / ".lem" / "project.toml"
        text, count = re.subn(r"(?m)^commands = \[\]$", 'commands = ["make test", "make lint"]', toml.read_text(), count=1)
        if not count:
            sys.exit("board-showcase: the settings have no empty gate commands to fill")
        toml.write_text(text)
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "chore: the settings")
        self.dir = Path(self.project("state-dir").strip())

    def git(self, *args: str) -> str:
        return run("git", "-C", str(self.repo), *args)

    def project(self, *args: str) -> str:
        return run(sys.executable, "-B", str(SCRIPTS / "project.py"), "--repo", str(self.repo), *args)

    def criteria(self, *args: str) -> str:
        return run(sys.executable, "-B", str(SCRIPTS / "criteria.py"), "--repo", str(self.repo), *args)

    def commit_in(self, tree: Path, message: str, files: dict[str, str]) -> None:
        for name, text in files.items():
            (tree / name).parent.mkdir(parents=True, exist_ok=True)
            (tree / name).write_text(text)
        run("git", "-C", str(tree), "add", "-A")
        run("git", "-C", str(tree), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", message)

    def head(self, tree: Path) -> str:
        return run("git", "-C", str(tree), "rev-parse", "--short=9", "HEAD").strip()

    def at(self, slug: str, minutes: float) -> None:
        """The event just written ran MINUTES before NOW."""
        self.times.setdefault(slug, []).append(minutes)

    def task(self, slug: str, ask: str) -> None:
        self.project("task-dir", slug, "--ask", ask)

    def state(self, slug: str, minutes: float, status: str, *lines: str) -> None:
        self.project("state", slug, status, *lines)
        self.at(slug, minutes)

    def log(self, slug: str, minutes: float, event: str, *fields: str) -> None:
        self.project("log", slug, event, *fields)
        self.at(slug, minutes)

    def criteria_file(self, slug: str, size: str, why: str, *criteria: str) -> Path:
        path = self.work / f"{slug}.md"
        path.write_text("\n".join(["## Acceptance criteria", "", f"Size: {size}, because {why}", "", *(f"{n}. {text}" for n, text in enumerate(criteria, 1))]) + "\n")
        return path

    def read(self, slug: str, minutes: float, file: Path, flagged: int) -> None:
        digest = json.loads(self.criteria("digest", slug, "--file", str(file)))["digest"]
        count = sum(1 for line in file.read_text().splitlines() if re.match(r"\d+\. ", line))
        self.log(slug, minutes, "criteria.read", "by=lem", "asked:=3", "answered:=3", 'families:=["opus", "sol"]', "silent:=[]",
                 f"criteria:={count}", f"flagged:={flagged}", "split:=false", f"digest={digest}")

    def approve(self, slug: str, minutes: float, file: Path, *flags: str) -> None:
        self.criteria("approve", slug, "--file", str(file), *flags)
        self.at(slug, minutes)

    def retime(self) -> None:
        """Each task's events, in the order the scripts wrote them, get the times of their steps."""
        log = self.dir / "events.jsonl"
        rows = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
        seen: dict[str, int] = {}
        for row in rows:
            slug = row["task"]
            times = self.times.get(slug, [])
            k = seen.get(slug, 0)
            if k >= len(times):
                sys.exit(f"board-showcase: {slug} wrote more events than it has times: {[r['event'] for r in rows if r['task'] == slug]}")
            row["ts"] = (NOW - timedelta(minutes=times[k])).strftime("%Y-%m-%dT%H:%M:%SZ")
            seen[slug] = k + 1
        short = [slug for slug, times in self.times.items() if seen.get(slug, 0) != len(times)]
        if short:
            sys.exit(f"board-showcase: these tasks have more times than events: {short}")
        log.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
        (self.dir / "events.js").write_text("".join(f"lemEvent({json.dumps(row, ensure_ascii=False)});\n" for row in rows))


def afternoon(shop: Shop) -> None:
    s = shop
    # A small change, built, checked, read once and proposed green: it waits for the merge.
    t = "footer-terms-typo"
    s.task(t, 'The footer says "Terms and condtions"')
    s.approve(t, 52, s.criteria_file(t, "small", "the request is one sentence.", 'The footer says "Terms and conditions".'), "--small")
    s.state(t, 52, "building", "small change: one builder", "type: fix, because the footer shows a typo today")
    s.log(t, 51.5, "builder.start", "job=the small change")
    s.state(t, 44, "ready", "the report is written")
    s.state(t, 43.5, "landing", "the checks start")
    s.log(t, 43, "gate.start", "tip=4c1d2e3f5", "commands:=2")
    s.log(t, 40.5, "gate", "command=make test", "exit:=0", "last=212 passed", "tip=4c1d2e3")
    s.log(t, 39.5, "gate", "command=make lint", "exit:=0", "last=All checks passed", "tip=4c1d2e3")
    s.log(t, 39, "task.red", "ok:=true", "digest=000000000000", "base=0a1b2c3d4", "tip=4c1d2e3f5", "tests:=[]", "without_a_test:=[]", "run_without:=[]")
    s.log(t, 38.5, "review.start", "attempt:=1", "floor=read")
    s.log(t, 35, "review", "attempt:=1", "round:=1", "kind=read", "verdict=clean", "must_fix:=0", "should:=0", "nit:=1", 'answered:=["codex"]',
          "silent:=[]", "ran:=[]", "left_out:=[]", "tip=4c1d2e3")
    s.log(t, 34, "proposed", "green:=true", "not_green:=[]", "tip=4c1d2e3")
    s.state(t, 34, "open", "pull request https://github.com/acme/shop/pull/41", "green")

    # A full change on its second task of three.
    t = "gift-note-in-export"
    s.task(t, "Add the gift note to the CSV export")
    s.state(t, 150, "held", "the interview waits for the owner", "type: feat, because the export gets a new column")
    s.log(t, 149.5, "scout.start")
    s.log(t, 149, "interview.start")
    s.log(t, 147, "scout")
    gift = s.criteria_file(t, "full", "the export gets a new column and two readers of it.",
                        'An order with the gift note "for Ania" has that text in the last column of its row.',
                        "An order with no gift note has an empty cell, not the word None.")
    s.log(t, 138, "criteria.read.start", "by=lem")
    s.read(t, 133, gift, 0)
    s.state(t, 133, "held", "the criteria wait for the owner")
    s.approve(t, 128, gift)
    s.state(t, 127, "building", "lead: builder")
    s.state(t, 112, "building", "plan committed, 3 tasks")
    s.state(t, 111, "building", "task 1 of 3")
    s.log(t, 110.5, "builder.start", "job=task 1 of 3")
    s.state(t, 74, "building", "task 2 of 3")
    s.log(t, 73.5, "builder.start", "job=task 2 of 3")

    # Criteria the personas read, with one flagged, which wait for his yes.
    t = "stock-on-product-page"
    s.task(t, "Show how many are left on the product page")
    s.state(t, 31, "held", "the interview waits for the owner", "type: feat, because the product page gets a new line")
    s.log(t, 30.5, "scout.start")
    s.log(t, 30, "interview.start")
    s.log(t, 28, "scout")
    stock = s.criteria_file(t, "full", "the product page gets a new line.",
                         'A product with 3 in stock says "3 left" under its price.',
                         'A product with none in stock says "Sold out" and no number.')
    s.log(t, 19, "criteria.read.start", "by=lem")
    s.read(t, 14, stock, 1)
    s.state(t, 14, "held", "the criteria wait for the owner")

    # A careful change: its plan is talked through with the reviewer before anything is built.
    t = "refund-rounding"
    s.task(t, "Round refunds the way the payment provider does")
    s.state(t, 95, "held", "the interview waits for the owner", "type: feat, because refunds get a new rule")
    s.log(t, 94.5, "interview.start")
    refund = s.criteria_file(t, "full", "refunds get a new rule.", "A refund of 10.005 EUR pays back 10.01 EUR, as the provider rounds it.")
    s.log(t, 82, "criteria.read.start", "by=lem")
    s.read(t, 78, refund, 0)
    s.state(t, 78, "held", "the criteria wait for the owner")
    s.approve(t, 70, refund)
    s.state(t, 69, "building", "lead: session")
    s.log(t, 55, "plan.talk.start", "reviewer=codex")

    # A bug whose investigation runs.
    t = "cart-total-after-coupon"
    s.task(t, "The cart total is wrong after a coupon since yesterday")
    s.state(t, 12, "building", "a builder reproduces the bug and finds its cause", "investigation: bug",
            "type: fix, because the ask says the total is wrong since yesterday")
    s.log(t, 11.5, "investigation.start", "type=fix")

    # A full change that landed today, from its interview to the merge.
    t = "order-date-on-invoice"
    s.task(t, "Print the order date on the invoice")
    s.state(t, 330, "held", "the interview waits for the owner", "type: feat, because the invoice gets a new line")
    s.log(t, 329.5, "scout.start")
    s.log(t, 329, "interview.start")
    s.log(t, 327, "scout")
    date = s.criteria_file(t, "full", "the invoice gets a new line.", 'The invoice of order 1042, placed on 3 May, says "Ordered 3 May 2026" under its number.')
    s.log(t, 318, "criteria.read.start", "by=lem")
    s.read(t, 314, date, 0)
    s.state(t, 314, "held", "the criteria wait for the owner")
    s.approve(t, 309, date)
    # Its worktree and its branch, with the plan, the commits of the build and of the polish pass: the
    # state blocks carry the newest commit, and criteria.py checks the criterion's test on the branch and on
    # the base commit, as a real build does.
    tree = Path(s.project("worktree-dir", t).strip())
    s.git("worktree", "add", "-q", "-b", f"feat/{t}", str(tree), "main")
    s.commit_in(tree, "docs(plans): the order date on the invoice", {"docs/plans/20261117-order-date-on-invoice.md": "\n".join([
        "# The order date on the invoice", "", "## Acceptance criteria", "", "Size: full, because the invoice gets a new line.", "",
        '1. The invoice of order 1042, placed on 3 May, says "Ordered 3 May 2026" under its number.',
        "   - test: `sh tests/order-date.sh` in `tests/order-date.sh`", "", "## Tasks", "",
        "1. The date under the order's number.", "2. The date in the shop's language.", ""])})
    s.state(t, 308, "building", "lead: builder")
    s.state(t, 296, "building", "plan committed, 2 tasks")
    s.criteria("record", t)
    s.at(t, 295.5)
    s.state(t, 295, "building", "task 1 of 2")
    s.log(t, 294.5, "builder.start", "job=task 1 of 2")
    s.commit_in(tree, "feat(invoice): the order date under the order's number", {
        "invoice/date.py": 'def ordered(order):\n    return f"Ordered {order.placed:%-d %B %Y}"\n',
        "tests/order-date.sh": "#!/bin/sh\ngrep -q 'Ordered {order.placed' invoice/date.py\n"})
    s.state(t, 268, "building", "task 2 of 2")
    s.log(t, 267.5, "builder.start", "job=task 2 of 2")
    s.commit_in(tree, "feat(invoice): the order date in the shop's language", {
        "invoice/date.py": 'def ordered(order):\n    return f"Ordered {order.placed:%-d %B %Y}"\n\n\ndef language(order):\n    return order.shop.language\n'})
    s.criteria("red", t)
    s.at(t, 247)
    s.state(t, 246, "ready", "the report is written")
    s.state(t, 245, "landing", "the checks start")
    before = s.head(tree)
    s.log(t, 244, "polish.start", f"before={before}")
    s.commit_in(tree, "style(invoice): one name for the date's format", {
        "invoice/date.py": 'DATE = "%-d %B %Y"\n\n\ndef ordered(order):\n    return f"Ordered {order.placed:%-d %B %Y}"\n\n\ndef language(order):\n    return order.shop.language\n'})
    tip = s.head(tree)
    s.log(t, 236, "polish", f"before={before[:7]}", f"after={tip[:7]}", "commits:=1", "filed:=[]")
    s.log(t, 235.5, "gate.start", f"tip={tip}", "commands:=2")
    s.log(t, 232, "gate", "command=make test", "exit:=0", "last=214 passed", f"tip={tip[:7]}")
    s.log(t, 231, "gate", "command=make lint", "exit:=0", "last=All checks passed", f"tip={tip[:7]}")
    s.criteria("red", t)
    s.at(t, 230.5)
    s.log(t, 230, "review.start", "attempt:=1", "floor=round")
    s.log(t, 219, "review", "attempt:=1", "round:=1", "kind=round", "verdict=clean", "must_fix:=0", "should:=1", "nit:=2", 'answered:=["codex", "claude"]',
          "silent:=[]", 'ran:=[{"name": "correctness", "why": "the invoice changes"}]', 'left_out:=[{"name": "security", "why": "no input is read"}]', f"tip={tip[:7]}")
    s.log(t, 218, "proposed", "green:=true", "not_green:=[]", f"tip={tip[:7]}")
    s.state(t, 218, "open", "pull request https://github.com/acme/shop/pull/38", "green")
    s.state(t, 160, "landed", "main: pull request https://github.com/acme/shop/pull/38 is merged")

    # A question, answered by its investigation.
    t = "why-export-is-slow"
    s.task(t, "Why does the monthly export take a minute?")
    s.state(t, 205, "building", "a builder finds the answer", "investigation: question", "type: question, because the ask asks why")
    s.log(t, 204.5, "investigation.start", "type=question")
    (s.dir / "tasks" / t / "investigation.md").write_text("# Investigation\n\nThe export reads every order of the month one query at a time.\n")
    s.log(t, 186, "investigation", "type=question", "call=answer", "line=the export reads each order of the month with its own query", "where=reports/export.py:monthly")
    s.state(t, 185, "answered", "the answer: one query for each order", "report: investigation.md")

    # Two items of the backlog.
    folder = s.repo / "docs" / "backlog"
    folder.mkdir(parents=True)
    (s.repo / "invoice").mkdir()
    (s.repo / "invoice" / "footer.py").write_text("def footer(order):\n    return order.shop.address\n")
    (folder / "invoice-footer-wraps.md").write_text("---\nworth: yes\nwhere: invoice/footer.py:footer\nadded: 2026-11-16\n---\n\n# The invoice footer wraps on A5\n\nSeen in the review of the order date: the footer's last line wraps when the invoice prints on A5.\n")
    (folder / "export-in-one-query.md").write_text("---\nworth: later\nadded: 2026-11-17\n---\n\n# Read the monthly export in one query\n\nThe investigation of the slow export found one query for each order. One query for the month would take the minute away.\n")
    s.git("add", "-A")
    s.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "docs: the backlog")


# The page's clock stops at NOW, and a probe may write what it measured into the page.
CLOCK = '<script>/* the showcase clock */ {{ const fixed = Date.parse("{now}"); Date.now = () => fixed; }}</script>'
PROBE = """<script>
setTimeout(() => {
  const top = el => Math.round(el.getBoundingClientRect().top + scrollY), bottom = el => Math.round(el.getBoundingClientRect().bottom + scrollY);
  const lanes = document.getElementById('lanes-section');
  const firsts = [...document.querySelectorAll('#lanes .lane')].map(l => l.querySelector('.tcard, .lane-empty')).filter(Boolean);
  // the tallest card of each lane over its shortest
  const ratio = [...document.querySelectorAll('#lanes .lane')].map(l => [...l.querySelectorAll('.tcard')].map(c => c.offsetHeight)).filter(hs => hs.length)
    .map(hs => Math.round((100 * Math.max(...hs)) / Math.min(...hs)) / 100);
  // the empty band of the large card: from the end of what it says to its last line
  const now = document.querySelector('#now .now-in'), next = document.querySelector('#now .now-next');
  const out = {now_card: document.getElementById('now').offsetHeight, now_empty: now && next ? Math.round(next.getBoundingClientRect().top - now.getBoundingClientRect().bottom) : null,
    lanes: lanes && !lanes.hidden ? top(lanes) : null, first_cards_end: firsts.length ? Math.max(...firsts.map(bottom)) : null,
    card_height_ratio: ratio, page: bottom(document.getElementById('page'))};
  const pre = document.createElement('pre'); pre.id = 'measured'; pre.textContent = JSON.stringify(out); document.body.append(pre);
}, 2500);
</script>"""


def chrome() -> str:
    for name in CHROMES:
        found = shutil.which(name) or (name if os.access(name, os.X_OK) else None)
        if found:
            return found
    sys.exit("board-showcase: no Chrome or Chromium found")


def page_copy(state: Path, page: str, dark: bool, probe: bool) -> Path:
    """The page as board.py wrote it, with the stopped clock, the theme and the probe put in. It keeps
    its own name in the state folder: the page reads the files beside it, and a page named
    task-SLUG.html opens on that task."""
    target = state / f"{page}.html"
    pristine = state / f"{page}.pristine"
    if not pristine.is_file():
        shutil.copyfile(target, pristine)
    text = pristine.read_text()
    head = CLOCK.format(now=NOW.strftime("%Y-%m-%dT%H:%M:%SZ")) + (f"<style>{DARK}</style>" if dark else "")
    text = text.replace("<head>", f"<head>{head}", 1)
    if probe:
        text = text.replace("</body>", f"{PROBE}</body>", 1)
    target.write_text(text)
    return target


def headless(binary: str, profile: Path, *args: str) -> str:
    # Chrome's temporary folders go into the run's own folder, which is removed with it: a picture left a
    # com.google.Chrome.* folder in the user's temporary folder at every run. On macOS Chrome reads
    # MAC_CHROMIUM_TMPDIR, not TMPDIR (measured with Chrome on 2026-11-17); elsewhere it reads TMPDIR.
    tmp = profile.parent / "chrome-tmp"
    tmp.mkdir(exist_ok=True)
    ran = subprocess.run([binary, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run", "--use-mock-keychain",
                          f"--user-data-dir={profile}", "--hide-scrollbars", *args], capture_output=True, text=True,
                         env={**os.environ, "TZ": "UTC", "TMPDIR": str(tmp), "MAC_CHROMIUM_TMPDIR": str(tmp)})
    return ran.stdout


def measure(binary: str, profile: Path, state: Path, page: str, width: int, height: int, dark: bool = False, hash_: str = "") -> dict:
    copy = page_copy(state, page, dark, True)
    dom = headless(binary, profile, f"--window-size={width},{height}", "--virtual-time-budget=6000", "--dump-dom", f"file://{copy}{hash_}")
    found = re.search(r'<pre id="measured">(.*?)</pre>', dom)
    if not found:
        sys.exit(f"board-showcase: the probe of {page} at {width} px printed nothing")
    return json.loads(found.group(1).replace("&quot;", '"'))


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        sys.exit(__doc__)
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    binary = chrome()
    work = Path(tempfile.mkdtemp(prefix="lem-showcase-"))
    try:
        shop = Shop(work)
        afternoon(shop)
        shop.retime()
        board = [sys.executable, "-B", str(SCRIPTS / "board.py"), "--repo", str(shop.repo), "--no-open"]
        env = {k: v for k, v in os.environ.items() if not k.startswith(("AGTERM_", "AGT_"))}
        for extra in (["--demo"], ["--task", "order-date-on-invoice"]):
            subprocess.run([*board, *extra], check=True, capture_output=True, env=env)
        # the backlog was read at NOW too, where the page's clock stands
        feed = shop.dir / "backlog.js"
        feed.write_text(re.sub(r'"read": "[^"]*"', f'"read": "{NOW.strftime("%Y-%m-%dT%H:%M:%SZ")}"', feed.read_text(), count=1))
        profile = work / "chrome"
        if "--measure" in sys.argv:
            print(json.dumps({f"{w}x900": measure(binary, profile, shop.dir, "board", w, 900) for w in (900, 1400, 1800)}
                             | {"task 1400x900": measure(binary, profile, shop.dir, "task-order-date-on-invoice", 1400, 900)}, indent=2))
        shots = {"board": ("board", ""), "task": ("task-order-date-on-invoice", ""), "backlog": ("board", "#backlog"), "dreams": ("board", "#dreams")}
        for name, (page, hash_) in shots.items():
            for theme in ("light", "dark"):
                # the picture ends with the page: its height is measured first, in the same theme
                tall = measure(binary, profile, shop.dir, page, WIDTH, 900, theme == "dark", hash_)["page"]
                copy = page_copy(shop.dir, page, theme == "dark", False)
                target = out / f"{name}-{theme}.png"
                headless(binary, profile, f"--window-size={WIDTH},{tall}", "--force-device-scale-factor=2", "--virtual-time-budget=6000",
                         f"--screenshot={target}", f"file://{copy}{hash_}")
                if not target.is_file():
                    sys.exit(f"board-showcase: Chrome wrote no picture {target}")
                print(f"shot {target} ({WIDTH} x {tall})")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
