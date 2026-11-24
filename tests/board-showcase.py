"""The board of a normal afternoon in one shop, for the README's pictures, for a look at
the board, and for tests/lem-serve.sh.

    python3 tests/board-showcase.py OUT              the pictures, into OUT: board-*, task-*, backlog-*, phone-*, waits-*, phone-waits-*,
                                                     story-*, phone-review-*, phone-merge-off-* and phone-merge-on-*, light and dark
    python3 tests/board-showcase.py --demo DIR       the repository alone, in DIR; print its path and its state folder as JSON

It is eleven tasks a team could have on one afternoon, written by Lem's own scripts
(project.py, criteria.py, decisions.py) in a throwaway repository, with a task in every
column: two that build, one in its checks, a breaker and criteria that changed from the
owner's note and wait for his yes again, a pull request the merge agent calls the owner
for, a typo the merge agent found nothing in and the board's server merged, another
landed task, an answered question, one task the owner parked after its breaker, and one
he parked that he started from a reviewer's item. The night and the retro proposed, and
the reviewer passed two proposals into the state folder's backlog: that item, held by
the parked task, and one that is undecided; the proposal it refuted is a third item
there, `worth: no`. The careful change's session has a `lem-ask` card up (`CARD_SPEC`),
kept in its task's folder as lem-ask keeps it, so that "Waits for you" has its row and
the board serves its page. Each task has the `session.open` of its agterm session, as
`lem session open` logs it, and one that builds has none, so that "Waits for you" has
its row "No session runs this task"; the pull request that is not green has the merge
agent's review (`merge-review.md` and its `merge.review`), which calls the owner, and
the landing's record (`landing.json`) that every open task has, so that its merge step
has its button. The breaker's question is in the board server's record of the owner's
Inbox (`inbox.json`), which a page shows only while his mark says away. The landed task
has a `task.md` with its outcome, and its polish pass files one backlog item on its
branch, so that its "Overview" shows "What we are building" whole; the task of the
picture of one task (`refund_line`) has every form a document of Lem's takes, and its
picture shows the merge review that calls the owner. The scripts write the events
seconds apart, and their times are then moved to the minutes before NOW, the minute the
run started, that a run would have spaced them. The state folder is marked as demo data,
as `lem board --demo` marks one, before the first task: `lem project task-dir` and
`lem session open` put no repository with that mark into the machine's list
of workspaces.

The pictures are of the board as `lem serve` sends it: a server of this checkout on a
free port, with a home folder of Lem of its own (XDG_CONFIG_HOME), shows the repository,
and headless Chrome takes each picture through the DevTools protocol
(tests/board-cdp.mjs, which needs Node): 1440 x 900 px for the desktop and 390 x 844 px
for a phone, both at two device pixels for each pixel, with the color scheme the
picture's theme names. The merge step of pull request 44 on a phone, as it opens with
its button off (phone-merge-off-*) and with its text scrolled to the end and the button
on (phone-merge-on-*), is 390 x 664 px, since its whole text fits at 390 x
844 (MERGE_PHONE).
"""

import json
import os
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
import zlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import IO, cast

ROOT = Path(__file__).resolve().parent.parent
# Lem's one entry, which runs the command a name stands for, and the folder of its package
MAIN = ROOT / "src" / "lem" / "__main__.py"
SRC = ROOT / "src"
NOW = datetime.now(UTC).replace(second=0, microsecond=0)
TODAY = NOW.strftime("%Y-%m-%d")
WIDTH, HEIGHT = 1440, 900
PHONE = (390, 844)
# The screen of the merge step's pictures: at PHONE the whole text of pull request 44
# fits in the overlay (its body 675 px of 675, measured 2026-11-22), so its button is on
# at once; at 664 px it goes on below the body's end (495 px of 609).
MERGE_PHONE = (390, 664)
# the tailnet address of the owner's Inbox in this afternoon's record of it (inbox.json)
INBOX_TAILNET = "https://studio.tail4e2a.ts.net:8443/"


def run(*args: str, cwd: Path | None = None) -> str:
    ran = subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
        env={
            **os.environ,
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
        },
    )
    if ran.returncode != 0:
        sys.exit(
            f"board-showcase: {' '.join(args[:4])}: "
            f"{ran.stderr.strip() or ran.stdout.strip()}"
        )
    return ran.stdout


class Shop:
    """A repository with Lem's settings, and the steps of each task with the minute
    (before NOW) it ran at."""

    def __init__(self, work: Path) -> None:
        self.repo = work / "shop"
        self.work = work
        self.times: dict[str, list[float]] = {}
        # the agterm session of each task's newest `session.open`, which a card of the
        # task names
        self.sids: dict[str, str] = {}
        run("git", "init", "-q", "-b", "main", str(self.repo))
        (self.repo / "app.txt").write_text("one\n")
        self.git("add", "-A")
        self.git(
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "commit",
            "-q",
            "-m",
            "chore: start",
        )
        self.project("init", "--base", "main")
        toml = self.repo / ".lem" / "settings.toml"
        text, count = re.subn(
            r"(?m)^commands = \[\]$",
            'commands = ["make test", "make lint"]',
            toml.read_text(),
            count=1,
        )
        if not count:
            sys.exit("board-showcase: the settings have no empty gate commands to fill")
        toml.write_text(text)
        self.git("add", "-A")
        self.git(
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "commit",
            "-q",
            "-m",
            "chore: the settings",
        )
        self.dir = Path(self.project("state-dir").strip())
        # the mark first, so that no script of the afternoon puts this repository into a
        # list of workspaces
        (self.dir / "demo").write_text(
            "The tasks in this folder are examples, "
            "written by tests/board-showcase.py.\n"
        )

    def git(self, *args: str) -> str:
        return run("git", "-C", str(self.repo), *args)

    def project(self, *args: str) -> str:
        return run(
            sys.executable,
            "-B",
            str(MAIN),
            "project",
            "--repo",
            str(self.repo),
            *args,
        )

    def criteria(self, *args: str) -> str:
        return run(
            sys.executable,
            "-B",
            str(MAIN),
            "criteria",
            "--repo",
            str(self.repo),
            *args,
        )

    def commit_in(self, tree: Path, message: str, files: dict[str, str]) -> None:
        for name, text in files.items():
            (tree / name).parent.mkdir(parents=True, exist_ok=True)
            (tree / name).write_text(text)
        run("git", "-C", str(tree), "add", "-A")
        run(
            "git",
            "-C",
            str(tree),
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "commit",
            "-q",
            "-m",
            message,
        )

    def head(self, tree: Path) -> str:
        return run("git", "-C", str(tree), "rev-parse", "--short=9", "HEAD").strip()

    def at(self, slug: str, minutes: float) -> None:
        """The event just written ran MINUTES before NOW."""
        self.times.setdefault(slug, []).append(minutes)

    def task(self, slug: str, ask: str, *more: str) -> None:
        self.project("task-dir", slug, "--ask", ask, *more)

    def state(self, slug: str, minutes: float, status: str, *lines: str) -> None:
        self.project("state", slug, status, *lines)
        self.at(slug, minutes)

    def log(self, slug: str, minutes: float, event: str, *fields: str) -> None:
        self.project("log", slug, event, *fields)
        self.at(slug, minutes)

    def criteria_file(self, slug: str, size: str, why: str, *criteria: str) -> Path:
        path = self.work / f"{slug}.md"
        path.write_text(
            "\n".join(
                [
                    "## Acceptance criteria",
                    "",
                    f"Size: {size}, because {why}",
                    "",
                    *(f"{n}. {text}" for n, text in enumerate(criteria, 1)),
                ]
            )
            + "\n"
        )
        return path

    def read(self, slug: str, minutes: float, file: Path, flagged: int) -> None:
        digest = json.loads(self.criteria("digest", slug, "--file", str(file)))[
            "digest"
        ]
        count = sum(
            1 for line in file.read_text().splitlines() if re.match(r"\d+\. ", line)
        )
        self.log(
            slug,
            minutes,
            "criteria.read",
            "by=lem",
            "asked:=3",
            "answered:=3",
            'families:=["opus", "sol"]',
            "silent:=[]",
            f"criteria:={count}",
            f"flagged:={flagged}",
            "split:=false",
            f"digest={digest}",
        )

    def approve(self, slug: str, minutes: float, file: Path, *flags: str) -> None:
        self.criteria("approve", slug, "--file", str(file), *flags)
        self.at(slug, minutes)

    def no_on_the_board(
        self, slug: str, minutes: float, block: float, note: str
    ) -> None:
        """The owner's No with NOTE on the criteria's row of the held block of BLOCK
        minutes before NOW, from his phone through the tailnet door, MINUTES before NOW:
        its record in the task's folder (lem_answers) and the board's `board.act`, as
        serve.py `act_answer` writes them."""
        if str(SRC) not in sys.path:
            sys.path.insert(0, str(SRC))
        from lem import (
            answers as lem_answers,  # the record of the owner's answer on the board
        )

        key = f"criterion:{slug}:{(NOW - timedelta(minutes=block)).strftime('%Y%m%dT%H%M%SZ')}"
        lem_answers.record(
            self.dir / "tasks" / slug,
            key,
            "Approve the criteria?",
            "no",
            note,
            via="door",
            device="phone",
            agent="Mozilla/5.0 (iPhone)",
        )
        self.log(
            slug,
            minutes,
            "board.act",
            "act=answer",
            "via=the board, through the tailnet door",
            f"key={key}",
            "option=no",
            "question=Approve the criteria?",
        )

    def session(self, slug: str, minutes: float, phase: str, why: str) -> None:
        """The task's agterm session opened MINUTES before NOW, as `lem session open`
        logs it: an id of agterm's form, made from the task's name and the minute, so
        that each run writes the same."""
        sid = f"{zlib.crc32(slug.encode()):08X}-0000-4000-8000-{int(minutes * 10):012X}"
        self.sids[slug] = sid
        self.log(
            slug,
            minutes,
            "session.open",
            f"session={sid}",
            f"name={slug}",
            f"phase={phase}",
            f"why={why}",
            "workspace=demo",
        )

    def card(self, slug: str, minutes: float, page: str, spec: dict) -> None:
        """A `lem-ask` card the task's newest session put up MINUTES before NOW, kept in
        the task's folder as lem-ask keeps it (`lem_cards.keep`, which logs
        `card.asked`), with the page `lem-ask render` builds."""
        spec_file, page_file = (
            self.work / f"{slug}-card.json",
            self.work / f"{slug}-card.html",
        )
        spec_file.write_text(json.dumps(spec))
        run(
            sys.executable,
            "-B",
            str(MAIN),
            "lem-ask",
            "render",
            str(spec_file),
            "-o",
            str(page_file),
        )
        if str(SRC) not in sys.path:
            sys.path.insert(0, str(SRC))
        from lem import (
            cards as lem_cards,  # Lem's record of a task's cards, as a task's session keeps it
        )

        lem_cards.keep(
            self.dir / "tasks" / slug,
            page,
            page_file.read_bytes(),
            spec,
            self.sids[slug],
        )
        self.at(slug, minutes)

    def closed(self, slug: str, minutes: float, why: str) -> None:
        self.log(slug, minutes, "session.close", f"why={why}")

    def decide(self, slug: str, minutes: float, *args: str) -> None:
        run(
            sys.executable,
            "-B",
            str(MAIN),
            "decisions",
            "--repo",
            str(self.repo),
            *args,
        )
        self.at(slug, minutes)

    def retime(self) -> None:
        """Each task's events, in the order the scripts wrote them, get the times of
        their steps."""
        log = self.dir / "events.jsonl"
        rows = [
            json.loads(line) for line in log.read_text().splitlines() if line.strip()
        ]
        seen: dict[str, int] = {}
        for row in rows:
            slug = row["task"]
            times = self.times.get(slug, [])
            k = seen.get(slug, 0)
            if k >= len(times):
                sys.exit(
                    f"board-showcase: {slug} wrote more events than it has times: "
                    f"{[r['event'] for r in rows if r['task'] == slug]}"
                )
            row["ts"] = (NOW - timedelta(minutes=times[k])).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            if "at" in row:
                # a line of decisions.jsonl carries its own time, which the board takes
                # before the event's
                row["at"] = row["ts"]
            seen[slug] = k + 1
        short = [
            slug
            for slug, times in self.times.items()
            if seen.get(slug, 0) != len(times)
        ]
        if short:
            sys.exit(
                f"board-showcase: these tasks have more times than events: {short}"
            )
        log.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
        )


# The owner's note on the criteria of stock-on-product-page, and the criteria the
# session wrote from it.
STOCK_NOTE = "criterion 1 should also warn when only one is left"
STOCK_CHANGED = (
    (
        'A product with 3 in stock says "3 left" under its price, and one with 1 in '
        'stock says "Only 1 left" in the warning color: the blue mug, with 1 in stock, '
        'says "Only 1 left".'
    ),
    'A product with none in stock says "Sold out" and no number.',
)

FOOTER_ITEM = (
    "---\nworth: yes\nwhere: invoice/footer.py:footer\nadded: {today}\n---\n\n"
    "# The invoice footer wraps on A5\n\n"
    "Seen in the polish pass of the order date: the footer's last line wraps when the "
    "invoice prints on A5.\n"
)


# The breaker's document of the task on its second task of three, in the form of
# templates/breaker.md: the picture of the task's Overview shows it, so it is written as
# the owner would read it. A paragraph is one line, since the board's markdown keeps
# each line break.
GIFT_BREAKER = """# The gift note has no place in the export that keeps criterion 1 and the export's readers

> [!IMPORTANT]
> **The build of {slug} stopped here, and only this task.** No option keeps criterion 1 as you approved it: the gift note "in the last column of its row" takes the place where two readers of the export find the total.
>
> Help with the choice below, `/lem park {slug}`, or `/lem drop {slug}`. `/lem resume {slug}` brings it back after either.

**You asked for the gift note in the CSV export, with every reader of the export working as before. Criterion 1 puts the note in the last column, and the last column is where the accounting import and the packing slip read the total.**

## Today and after

**Today**, as the build left it:

1. Order 1042 has the gift note "for Ania" and a total of 54.90 EUR.
2. The export writes the note into the last column, as criterion 1 says.
3. The accounting import reads "for Ania" as the total of order 1042, and refuses the whole file.

**After**, with the recommendation:

1. Order 1042 has the gift note "for Ania" and a total of 54.90 EUR.
2. The export writes the note into a column of its own, `gift_note`, just before `total`.
3. The accounting import reads 54.90 EUR, and the gift note is in its own cell.

## The case that broke

1. `export/orders_csv.py:41` writes the columns of a row in a fixed order, and `total` is the last.
2. Task 2 of the plan added `gift_note` after it, so that criterion 1 holds: `tests/test_export.py::test_gift_note_last` passes.
3. `accounting/import.py:18` takes `row[-1]` as the total; `make test` fails in `test_import_totals` with `could not convert 'for Ania' to a number`.
4. `warehouse/slip.py:27` prints `row[-1]` as the amount on the packing slip: the slip of order 1042 would say "for Ania" where the amount stands.

```mermaid
flowchart TD
  A["Order 1042: for Ania, 54.90"] --> B{"Where is the note?"}
  B -->|"last, as in criterion 1"| C["Accounting: the total is for Ania"]
  B -->|"A: own column"| D["Every reader finds 54.90"]
  B -->|"B: in the notes"| E["The slip prints it to the packer"]
```

## The root cause

Criterion 1 names a place, "the last column", where it means a column that holds only the gift note. Two readers of the export take the total by its place, and the scout listed neither: they live outside `export/`, and nothing in the export's tests reads them.

The same cause reaches every new column of the export: whatever goes last moves the total. It is a fact only the build could find, not a plan that missed a step.

## The options

| | A: own column | B: notes column |
| --- | --- | --- |
| The row | `gift_note` before `total` | "Leave at door. Gift: for Ania" |
| Criterion 1 | changes: `gift_note`, not last | changes: the notes |
| The readers | as today | the slip prints the note |
| Undo | yes: nothing is sent | yes: nothing is sent |

- **A: a column of its own** leads to one more column before the total: the readers go on as today, and the build goes on with task 3 of 3.
- **B: appended to the notes column** leads to no new column, and the warehouse prints the gift note as a packing instruction on every slip.

## The recommendation

> [!TIP]
> **A: a column of its own, before the total.** It keeps what criterion 1 is for, a cell with only the gift note, and every reader of the export. Only the place the criterion names changes, and that place is yours to change.

What the ladder said:

- The gate: no ruling on the order of the export's columns.
- The personas: both model families picked A.
- The dialectic: A held; the case against it found no reader that takes the gift note by its header.
- The experts: Fable and Astra both picked A.

No option keeps criterion 1 as written, so the build stops here, and the change of the criterion is yours.

## The assumptions

- The accounting import and the packing slip are the only readers of the export: a search for `orders.csv` in the repository found these two.
- Nobody outside the repository reads the file by the place of its columns.
- A gift note holds no line break that the CSV writer leaves unquoted.
- A reader outside the repository that takes the last column would make B the better option.
"""

GIFT_HANDOFF = """# Handoff

- Settled: the export writes the gift note (tasks 1 and 2 of 3, commits on the branch); an empty note is an empty cell (criterion 2).
- Open: the column's place, breaker 1.
- Next: on A, move `gift_note` before `total` in `export/orders_csv.py:41`, change `test_gift_note_last`, then task 3 of 3.
- Tried and failed: the note last, as criterion 1 says (`make test`: `test_import_totals`).
"""

FEE_BREAKER = """# The fee notice goes to 212 merchants, and a mail cannot be called back

> [!IMPORTANT]
> **The build of {slug} stopped here, and only this task.** The next step sends a mail to 212 merchants, which a later "no" cannot undo.
>
> Help with the choice below, `/lem park {slug}`, or `/lem drop {slug}`. `/lem resume {slug}` brings it back after either.

**You asked to tell each merchant about the new card fee. The mail is ready; the date of the fee in it is the one step left to confirm.**

## Today and after

**Today**, as the build left it:

1. 212 merchants are on the list, and the mail says the fee starts on 1 December.
2. `make send-fee-notice` sends it.
3. Each merchant reads a date that nobody confirmed.

**After**, with the recommendation:

1. The date is confirmed, or changed in the mail.
2. `make send-fee-notice` sends it once.
3. Each merchant reads the date that holds.

## The case that broke

1. `billing/fees.py:12` has the fee from 1 December, from the plan.
2. `mail/fee_notice.md` says the same date to every merchant.
3. The send is the next step, and a mail that went out stays out.

```mermaid
flowchart TD
  A["The fee notice, ready for 212 merchants"] --> B{"Is 1 December confirmed?"}
  B -->|"yes"| C["Send it once: every merchant reads the right date"]
  B -->|"not yet"| D["Wait: nothing is sent"]
```

## The root cause

The plan took the date from the ticket, and the ticket took it from a draft of the association's letter.

## The options

| | A: send now | B: wait for the date |
| --- | --- | --- |
| What a person sees | the mail today | the mail after the confirmation |
| Can a later no undo it | no: a mail cannot be called back | yes: nothing is sent |

- **A: send now** leads to 212 mails with a date nobody confirmed.
- **B: wait for the date** leads to a task that waits, with nothing sent.

## The recommendation

> [!TIP]
> **B: wait for the date.** A wrong date in 212 mails costs a second mail and the merchants' trust.

What the ladder said: a step that cannot be undone is never the ladder's to take.

## The assumptions

- The association confirms the date this week.
"""


# The card of the careful change's session (`refund-rounding`): a `lem-ask` spec as a
# session writes one, and the agterm page id it went up as.
CARD_PAGE = "4F9A1C2E-7B3D-4E8F-A1B2-C3D4E5F60718"
CARD_SPEC = {
    "title": "Refund rounding",
    "context": (
        "The payment provider rounds each line of a refund on its own. "
        "The shop's receipts round the total once."
    ),
    "prompt": "Round each line of a refund, or only its total?",
    "options": [
        {
            "id": "line",
            "label": "Each line",
            "subtitle": (
                "As the provider does: a refund of three lines can be 1 cent "
                "off the total's rounding"
            ),
            "recommended": (
                "The criterion says a refund pays back what the provider pays"
            ),
        },
        {
            "id": "total",
            "label": "Only the total",
            "subtitle": "As the receipts do today",
        },
    ],
}


def afternoon(shop: Shop) -> None:  # noqa: PLR0915 - over the limit before the limit was set
    s = shop
    # A task on the fast track, built, checked, read once and proposed green: the merge
    # agent finds nothing for the owner, and the board's server merges it (`lem land
    # merge --by merger --via server`).
    t = "footer-terms-typo"
    s.task(t, 'The footer says "Terms and condtions"')
    s.session(t, 52.5, "fast", "new")
    s.approve(
        t,
        52,
        s.criteria_file(
            t,
            "small",
            "the request is one sentence.",
            'The footer says "Terms and conditions".',
        ),
        "--small",
    )
    s.state(
        t,
        52,
        "building",
        "small change: one builder",
        "type: fix, because the footer shows a typo today",
    )
    s.log(t, 51.5, "builder.start", "job=the small change")
    s.state(t, 44, "ready", "the report is written")
    s.state(t, 43.5, "landing", "the checks start")
    s.log(t, 43, "gate.start", "tip=4c1d2e3f5", "commands:=2")
    s.log(
        t,
        40.5,
        "gate",
        "command=make test",
        "exit:=0",
        "last=212 passed",
        "tip=4c1d2e3",
    )
    s.log(
        t,
        39.5,
        "gate",
        "command=make lint",
        "exit:=0",
        "last=All checks passed",
        "tip=4c1d2e3",
    )
    s.log(
        t,
        39,
        "task.red",
        "ok:=true",
        "digest=000000000000",
        "base=0a1b2c3d4",
        "tip=4c1d2e3f5",
        "tests:=[]",
        "without_a_test:=[]",
        "run_without:=[]",
    )
    s.log(t, 38.5, "review.start", "attempt:=1", "floor=read")
    s.log(
        t,
        35,
        "review",
        "attempt:=1",
        "round:=1",
        "kind=read",
        "verdict=clean",
        "must_fix:=0",
        "should:=0",
        "nit:=1",
        'answered:=["codex"]',
        "silent:=[]",
        "ran:=[]",
        "left_out:=[]",
        "tip=4c1d2e3",
    )
    s.log(t, 34, "proposed", "green:=true", "not_green:=[]", "tip=4c1d2e3")
    s.state(t, 34, "open", "pull request https://github.com/acme/shop/pull/41", "green")
    folder = s.dir / "tasks" / t
    (folder / "merge-review.md").write_text(TYPO_REVIEW)
    s.log(
        t,
        33,
        "merge.review",
        "verdict=merge",
        "calls:=false",
        "by=claude",
        "tip=4c1d2e3",
    )
    s.log(t, 32.5, "merge.start", "by=merger", "via=server")
    s.state(
        t,
        32,
        "landed",
        "main: pull request https://github.com/acme/shop/pull/41 is merged",
    )
    s.closed(t, 31, "ended")

    # A task on the fast track in its checks: the first command passed, the second runs.
    t = "coupon-has-a-slug"
    s.task(t, "Give each coupon a slug for its link")
    s.session(t, 30.5, "fast", "new")
    s.approve(
        t,
        30,
        s.criteria_file(
            t,
            "small",
            "the request is one sentence.",
            "A coupon named Summer Sale has the slug summer-sale.",
        ),
        "--small",
    )
    s.state(
        t,
        30,
        "building",
        "small change: one builder",
        "type: feat, because a coupon gets a new field",
    )
    s.log(t, 29.5, "builder.start", "job=the small change")
    s.state(t, 9, "ready", "the report is written")
    s.state(t, 8.5, "landing", "the checks start")
    s.log(t, 8, "gate.start", "tip=7e8f9a0b1", "commands:=2")
    s.log(
        t, 5, "gate", "command=make test", "exit:=0", "last=213 passed", "tip=7e8f9a0"
    )

    # A task on the standard track, on its second task of three.
    t = "gift-note-in-export"
    s.task(t, "Add the gift note to the CSV export")
    s.session(t, 150.5, "shape", "new")
    s.state(
        t,
        150,
        "held",
        "the interview waits for the owner",
        "type: feat, because the export gets a new column",
    )
    s.log(t, 149.5, "scout.start")
    s.log(t, 149, "interview.start")
    s.log(t, 147, "scout")
    s.log(t, 141, "interview.end")
    gift = s.criteria_file(
        t,
        "full",
        "the export gets a new column and two readers of it.",
        (
            'An order with the gift note "for Ania" has that text in the '
            "last column of its row."
        ),
        "An order with no gift note has an empty cell, not the word None.",
    )
    s.log(t, 138, "criteria.read.start", "by=lem")
    s.read(t, 133, gift, 0)
    s.state(t, 133, "held", "the criteria wait for the owner")
    s.approve(t, 128, gift)
    s.session(t, 127.5, "build", "handoff")
    s.state(t, 127, "building", "lead: builder")
    s.state(t, 112, "building", "plan committed, 3 tasks")
    s.state(t, 111, "building", "task 1 of 3")
    s.log(t, 110.5, "builder.start", "job=task 1 of 3")
    s.state(t, 74, "building", "task 2 of 3")
    s.log(t, 73.5, "builder.start", "job=task 2 of 3")
    # the build meets a choice that no option settles inside the criteria: the circuit
    # breaker stops it, with the lead's document and handoff in the task
    # directory (templates/breaker.md)
    (s.dir / "tasks" / t / "breaker.md").write_text(GIFT_BREAKER.replace("{slug}", t))
    (s.dir / "tasks" / t / "handoff.md").write_text(GIFT_HANDOFF)
    s.decide(t, 20, "breaker", t, "--cause", "criteria")
    s.at(t, 20)
    # the board's server sent the breaker to the owner's Inbox as the task's session
    # (lem_inbox.Watcher, which sends nothing for a demo, so the record is written here
    # as it writes it); a page says so only while his mark says away, which this
    # afternoon has not the breaker's row is named by its held block, 20 minutes before
    # NOW (lem_board_model.answer_row)
    sent = {
        "key": f"breaker:{t}:1:{(NOW - timedelta(minutes=20)).strftime('%Y%m%dT%H%M%SZ')}",
        "task": t,
        "kind": "breaker",
        "form": "question",
        "asks": True,
        "session": "6f1c2a9e-demo",
        "tip": None,
        "message_id": "msg_01DEMOGIFTNOTEBREAKER1",
        "thread_id": "msg_01DEMOGIFTNOTEBREAKER1",
        "thread_url": "http://plannotator.localhost:50026/#thread=msg_01DEMOGIFTNOTEBREAKER1",
        "questions": ["q1"],
        "woke": [],
    }
    (s.dir / "inbox.json").write_text(
        json.dumps(
            {
                "running": True,
                "url": "http://plannotator.localhost:50026/",
                "tailnet_url": INBOX_TAILNET,
                "why": None,
                "said": "",
                "problem": None,
                "sent": [sent],
            },
            indent=2,
        )
        + "\n"
    )

    # A task whose breaker stopped it before a step no "no" undoes, which the owner
    # then parked.
    t = "fee-notice-to-merchants"
    s.task(t, "Tell each merchant about the new card fee by mail")
    s.session(t, 260.5, "build", "new")
    s.state(
        t,
        260,
        "building",
        "lead: builder",
        "type: feat, because the merchants get a new mail",
    )
    s.state(t, 238, "building", "plan committed, 2 tasks")
    s.state(t, 237, "building", "task 2 of 2")
    s.log(t, 236.5, "builder.start", "job=task 2 of 2")
    (s.dir / "tasks" / t / "breaker.md").write_text(FEE_BREAKER.replace("{slug}", t))
    (s.dir / "tasks" / t / "handoff.md").write_text(
        "# Handoff\n\nSettled: the mail's text and its list of 212 merchants. "
        "Open: whether the fee date stands. Next: `make send-fee-notice`, "
        "after his word.\n"
    )
    s.decide(
        t, 205, "breaker", t, "--cause", "irreversible", "--irreversible", "person"
    )
    s.at(t, 205)
    s.state(
        t,
        190,
        "parked",
        (
            "the owner parked it: wait for the merchants' association "
            "to confirm the fee date"
        ),
    )
    s.closed(t, 189.5, "owner")

    # Criteria the personas read, with one flagged, which waited for his yes; he said No
    # on his phone with a note, and the session wrote the change in its own words
    # (`lem criteria change`): they wait for his yes again, each changed criterion with
    # its text before beside its new text.
    t = "stock-on-product-page"
    s.task(t, "Show how many are left on the product page")
    s.session(t, 31.5, "shape", "new")
    s.state(
        t,
        31,
        "held",
        "the interview waits for the owner",
        "type: feat, because the product page gets a new line",
    )
    s.log(t, 30.5, "scout.start")
    s.log(t, 30, "interview.start")
    s.log(t, 28, "scout")
    s.log(t, 22, "interview.end")
    stock = s.criteria_file(
        t,
        "full",
        "the product page gets a new line.",
        'A product with 3 in stock says "3 left" under its price.',
        'A product with none in stock says "Sold out" and no number.',
    )
    s.log(t, 19, "criteria.read.start", "by=lem")
    s.read(t, 14, stock, 1)
    s.state(t, 14, "held", "the criteria wait for the owner")
    # its session keeps them in the task directory, where the board shows them with the
    # owner's Yes and No
    (s.dir / "tasks" / t / "criteria.md").write_text(stock.read_text())
    s.no_on_the_board(t, 10, 14, STOCK_NOTE)
    changed = s.criteria_file(
        t, "full", "the product page gets a new line.", *STOCK_CHANGED
    )
    s.criteria("change", t, "--file", str(changed), "--words", STOCK_NOTE)
    # the change writes two events, `criteria.changed` and the held block's `task.state`
    s.at(t, 8)
    s.at(t, 8)

    # A careful change: its plan is talked through with the reviewer before anything
    # is built.
    t = "refund-rounding"
    s.task(t, "Round refunds the way the payment provider does")
    s.session(t, 95.5, "shape", "new")
    s.state(
        t,
        95,
        "held",
        "the interview waits for the owner",
        "type: feat, because refunds get a new rule",
    )
    s.log(t, 94.5, "interview.start")
    s.log(t, 86, "interview.end")
    refund = s.criteria_file(
        t,
        "full",
        "refunds get a new rule.",
        "A refund of 10.005 EUR pays back 10.01 EUR, as the provider rounds it.",
    )
    s.log(t, 82, "criteria.read.start", "by=lem")
    s.read(t, 78, refund, 0)
    s.state(t, 78, "held", "the criteria wait for the owner")
    s.approve(t, 70, refund)
    s.session(t, 69.5, "build", "handoff")
    s.state(t, 69, "building", "lead: session")
    s.log(t, 55, "plan.talk.start", "reviewer=codex")
    # the plan talk meets a choice only the owner makes: the session puts up a card,
    # which waits for his pick, in agterm and on the board
    s.card(t, 50, CARD_PAGE, CARD_SPEC)

    # A bug whose investigation runs, and whose session is gone: no agent runs it, so it
    # waits for the owner's "Open a session" (a demo workspace knows a session from the
    # log alone, and this task has none)
    t = "cart-total-after-coupon"
    s.task(t, "The cart total is wrong after a coupon since yesterday")
    s.state(
        t,
        12,
        "building",
        "an investigator reproduces the bug and finds its cause",
        "investigation: bug",
        "type: fix, because the ask says the total is wrong since yesterday",
    )
    s.log(t, 11.5, "investigation.start", "type=fix")

    # A task on the standard track that landed today, from its interview to the merge.
    t = "order-date-on-invoice"
    s.task(t, "Print the order date on the invoice")
    # task.md as Lem writes it at new: its outcome is what the board of one task shows
    # in "What we are building"
    (s.dir / "tasks" / t / "task.md").write_text(
        "\n".join(
            [
                f"# {t}",
                "",
                "## The ask, verbatim",
                "",
                "Print the order date on the invoice",
                "",
                "## Type",
                "",
                "feat, because the invoice gets a new line",
                "",
                "## Outcome",
                "",
                (
                    "Each invoice says when its order was placed, under the order's "
                    "number, in the shop's language."
                ),
                (
                    "A customer who asks about an old order finds the date on the "
                    "paper they already have."
                ),
                "",
            ]
        )
    )
    s.session(t, 330.5, "shape", "new")
    s.state(
        t,
        330,
        "held",
        "the interview waits for the owner",
        "type: feat, because the invoice gets a new line",
    )
    s.log(t, 329.5, "scout.start")
    s.log(t, 329, "interview.start")
    s.log(t, 327, "scout")
    s.log(t, 321, "interview.end")
    date = s.criteria_file(
        t,
        "full",
        "the invoice gets a new line.",
        (
            "The invoice of order 1042, placed on 3 May, "
            'says "Ordered 3 May 2026" under its number.'
        ),
    )
    s.log(t, 318, "criteria.read.start", "by=lem")
    s.read(t, 314, date, 0)
    s.state(t, 314, "held", "the criteria wait for the owner")
    s.approve(t, 309, date)
    # Its worktree and its branch, with the plan, the commits of the build and of the
    # polish pass: the state blocks carry the newest commit, and criteria.py checks the
    # criterion's test on the branch and on the base commit, as a real build does.
    tree = Path(s.project("worktree-dir", t).strip())
    s.git("worktree", "add", "-q", "-b", f"feat/{t}", str(tree), "main")
    s.commit_in(
        tree,
        "docs(plans): the order date on the invoice",
        {
            "docs/plans/2026-11-17-order-date-on-invoice.md": (
                "# The order date on the invoice\n"
                "\n"
                "## Acceptance criteria\n"
                "\n"
                "Size: full, because the invoice gets a new line.\n"
                "\n"
                '1. The invoice of order 1042, placed on 3 May, says "Ordered 3 May '
                '2026" under its number.\n'
                "   - test: `sh tests/order-date.sh` in `tests/order-date.sh`\n"
                "\n"
                "## Tasks\n"
                "\n"
                "1. The date under the order's number.\n"
                "2. The date in the shop's language.\n"
            )
        },
    )
    s.session(t, 308.5, "build", "handoff")
    s.state(t, 308, "building", "lead: builder")
    s.state(t, 296, "building", "plan committed, 2 tasks")
    s.criteria("record", t)
    s.at(t, 295.5)
    s.state(t, 295, "building", "task 1 of 2")
    s.log(t, 294.5, "builder.start", "job=task 1 of 2")
    s.commit_in(
        tree,
        "feat(invoice): the order date under the order's number",
        {
            "invoice/date.py": (
                'def ordered(order):\n    return f"Ordered {order.placed:%-d %B %Y}"\n'
            ),
            "tests/order-date.sh": (
                "#!/bin/sh\ngrep -q 'Ordered {order.placed' invoice/date.py\n"
            ),
        },
    )
    s.state(t, 268, "building", "task 2 of 2")
    s.log(t, 267.5, "builder.start", "job=task 2 of 2")
    s.commit_in(
        tree,
        "feat(invoice): the order date in the shop's language",
        {
            "invoice/date.py": (
                'def ordered(order):\n    return f"Ordered {order.placed:%-d %B '
                '%Y}"\n\n\ndef language(order):\n    return order.shop.language\n'
            )
        },
    )
    s.criteria("red", t)
    s.at(t, 247)
    s.state(t, 246, "ready", "the report is written")
    s.session(t, 245.5, "land", "handoff")
    s.state(t, 245, "landing", "the checks start")
    before = s.head(tree)
    s.log(t, 244, "polish.start", f"before={before}")
    s.commit_in(
        tree,
        "style(invoice): one name for the date's format",
        {
            "invoice/date.py": (
                'DATE = "%-d %B %Y"\n\n\ndef ordered(order):\n'
                '    return f"Ordered {order.placed:%-d %B %Y}"\n\n\n'
                "def language(order):\n    return order.shop.language\n"
            )
        },
    )
    # the polish pass files a defect it saw outside the change, in a commit of its own:
    # the board of the task lists it on "Overview", and the backlog of the main checkout
    # has it once the task landed
    s.commit_in(
        tree,
        "docs(backlog): the invoice footer wraps on A5",
        {"docs/backlog/invoice-footer-wraps.md": FOOTER_ITEM.format(today=TODAY)},
    )
    tip = s.head(tree)
    s.log(
        t,
        236,
        "polish",
        f"before={before[:7]}",
        f"after={tip[:7]}",
        "commits:=2",
        'filed:=["docs/backlog/invoice-footer-wraps.md"]',
    )
    s.log(t, 235.5, "gate.start", f"tip={tip}", "commands:=2")
    s.log(
        t,
        232,
        "gate",
        "command=make test",
        "exit:=0",
        "last=214 passed",
        f"tip={tip[:7]}",
    )
    s.log(
        t,
        231,
        "gate",
        "command=make lint",
        "exit:=0",
        "last=All checks passed",
        f"tip={tip[:7]}",
    )
    s.criteria("red", t)
    s.at(t, 230.5)
    s.log(t, 230, "review.start", "attempt:=1", "floor=round")
    s.log(
        t,
        219,
        "review",
        "attempt:=1",
        "round:=1",
        "kind=round",
        "verdict=clean",
        "must_fix:=0",
        "should:=1",
        "nit:=2",
        'answered:=["codex", "claude"]',
        "silent:=[]",
        'ran:=[{"name": "correctness", "why": "the invoice changes"}]',
        'left_out:=[{"name": "security", "why": "no input is read"}]',
        f"tip={tip[:7]}",
    )
    s.log(t, 218, "proposed", "green:=true", "not_green:=[]", f"tip={tip[:7]}")
    s.state(
        t, 218, "open", "pull request https://github.com/acme/shop/pull/38", "green"
    )
    s.state(
        t,
        160,
        "landed",
        "main: pull request https://github.com/acme/shop/pull/38 is merged",
    )
    s.closed(t, 158, "ended")

    # A question, answered by its investigation.
    t = "why-export-is-slow"
    s.task(t, "Why does the monthly export take a minute?")
    s.session(t, 205.5, "build", "new")
    s.state(
        t,
        205,
        "building",
        "an investigator finds the answer",
        "investigation: question",
        "type: question, because the ask asks why",
    )
    s.log(t, 204.5, "investigation.start", "type=question")
    # written as plain lines, as an agent writes a short report: the board keeps its
    # line breaks
    (s.dir / "tasks" / t / "investigation.md").write_text(
        "# Investigation\n\nThe export reads every order of the month one query at a "
        "time.\n"
        "A month of 4,000 orders makes 4,000 queries.\n"
        "Each query waits about 15 ms for the database.\n"
    )
    s.log(
        t,
        186,
        "investigation",
        "type=question",
        "call=answer",
        "line=the export reads each order of the month with its own query",
        "where=reports/export.py:monthly",
    )
    s.state(
        t,
        185,
        "answered",
        "the answer: one query for each order",
        "report: investigation.md",
    )
    s.closed(t, 184.5, "ended")

    # Two items of the backlog.
    folder = s.repo / "docs" / "backlog"
    folder.mkdir(parents=True)
    (s.repo / "invoice").mkdir()
    (s.repo / "invoice" / "footer.py").write_text(
        "def footer(order):\n    return order.shop.address\n"
    )
    (folder / "invoice-footer-wraps.md").write_text(FOOTER_ITEM.format(today=TODAY))
    # the places the reviewer's items below name
    (s.repo / "AGENTS.md").write_text(
        "# The shop\n\nRun `make test` and `make lint` before a commit.\n"
    )
    (s.repo / "tests").mkdir()
    (s.repo / "tests" / "test_export.py").write_text(
        "def test_monthly():\n    assert True\n"
    )
    (folder / "export-in-one-query.md").write_text(
        f"---\nworth: later\nadded: {TODAY}\n---\n\n# Read the monthly export in one "
        "query\n\nThe investigation of the slow export found one query for each order. "
        "One query for the month would take the minute away.\n"
    )
    s.git("add", "-A")
    s.git(
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@t",
        "commit",
        "-q",
        "-m",
        "docs: the backlog",
    )

    # The night's and the retro's proposals, and the reviewer's verdicts, through
    # `lem project proposals`: two items of the state folder's backlog, one undecided
    # and one a queued task holds, and one proposal refuted, which stays there as a
    # third item, `worth: no`, under "Decided against".
    night = s.work / "night.json"
    night.write_text(
        json.dumps(
            {
                "read": "the free search of the night",
                "proposals": [
                    {
                        "area": "tests",
                        "move": (
                            "Make the check of the monthly export wait for its file"
                        ),
                        "where": "tests/test_export.py:test_monthly",
                        "body": (
                            "The check read the export before its file was whole, and "
                            "failed once in the last ten runs."
                        ),
                        "source": "the checks of coupon-has-a-slug",
                    }
                ],
            }
        )
    )
    s.project(
        "proposals", "add", "--kind", "night", "--date", TODAY, "--file", str(night)
    )
    retro = s.work / "retro.json"
    retro.write_text(
        json.dumps(
            {
                "read": "the tasks and the naps since the retro before",
                "proposals": [
                    {
                        "area": "lessons",
                        "move": (
                            "Read the receipt's total by its label, never by its row"
                        ),
                        "where": "AGENTS.md",
                        "body": (
                            "A refund line moved the total's row, "
                            "and a test that read the row failed."
                        ),
                        "source": "the task refund-line-on-receipt's records",
                    },
                    {
                        "area": "lessons",
                        "move": "Run make lint before each commit",
                        "where": "AGENTS.md",
                        "body": "A builder forgot it once.",
                        "source": "the task coupon-has-a-slug's records",
                    },
                ],
            }
        )
    )
    s.project(
        "proposals", "add", "--kind", "retro", "--date", TODAY, "--file", str(retro)
    )
    verdicts = s.work / "verdicts.json"
    verdicts.write_text(
        json.dumps(
            {
                "verdicts": [
                    {"proposal": f"night of {TODAY} #1", "passed": "tests"},
                    {"proposal": f"retro of {TODAY} #1", "passed": "lessons"},
                    {
                        "proposal": f"retro of {TODAY} #2",
                        "refuted": "a first-time lesson, with no question in it",
                    },
                ],
                "titles": {
                    "tests": "The export's check fails by chance",
                    "lessons": "Read the receipt's total by its label",
                },
            }
        )
    )
    s.project("proposals", "verdict", "--file", str(verdicts))
    t = "export-check-by-chance"
    s.task(t, ".lem/state/backlog/the-export-s-check-fails-by-chance.md")
    s.state(t, 7, "queued", "it starts after refund-rounding", "after: refund-rounding")
    s.state(t, 6, "parked", "the owner parked it: the check waits for the new export")


# The merge agent's review of the task that is not green, in the form of
# skills/lem/prompts/merge.md: the pictures of "Waits for you" and of the task's
# Overview show it, so it is written as the owner would read it.
TYPO_REVIEW = """Verdict: merge. The footer says "Terms and conditions", as the criterion asks, and nothing else changed.

**What was built, and why.** You asked to fix the typo in the footer. One word of the template changed.

**The results.** The checks passed: 212 tests and the lint. One read found no must-fix.

**Decisions taken without you.** None.

**Time.** 18 minutes from the request to the pull request.
"""

MERGE_REVIEW = """Verdict: call. The change does what both criteria say; it is not green for two choices taken without you, and I would keep both.

**What was built, and why.** You asked: "Show a refund as a line of its own on the receipt."

Today:

1. Order 1042 is 100.00 EUR, and a refund of 30.00 EUR comes in.
2. The receipt shows 70.00 EUR, and no line says why.

After:

1. Order 1042 is 100.00 EUR, and a refund of 30.00 EUR comes in.
2. The receipt shows `Refund -30.00` under the items, and `Total 70.00` under it.
3. A refund of 120.00 EUR shows `Total 0.00` and a credit note for 20.00 EUR.

**The results.** `make test` and `make lint` passed. The tests of both criteria pass on the branch and fail on the base. Round 2 of the review left no must-fix.

**Decided without you.**

- Where the line goes, by the dialectic: under the items, before the total. I agree: the receipt prints its total last, so the refund reads as a change of the total and not as an item.
- The criteria were approved at night, while the task ran without you. They say what your words ask, and nothing more.

**The time.** 2 h 42 min, against about 2 h for a change of this size in this repository.

**What I found.** Nothing wrong. One assertion left `tests/test_receipt.py`: it read the total from a fixed row, which the refund line moves, and `test_total_after_refund` now reads the total by its label.
"""


def png(
    width: int,
    height: int,
    rows: list[tuple[int, int, int, int, tuple[int, int, int]]],
    back: tuple[int, int, int] = (250, 248, 243),
) -> bytes:
    """A small PNG of flat boxes, (x, y, w, h, color) each on BACK: the demo's stand-in
    for a screenshot."""
    pixels = [bytearray(back * width) for _ in range(height)]
    for x, y, w, h, color in rows:
        for yy in range(max(0, y), min(height, y + h)):
            pixels[yy][3 * max(0, x) : 3 * min(width, x + w)] = bytes(color) * (
                min(width, x + w) - max(0, x)
            )
    raw = b"".join(b"\0" + bytes(row) for row in pixels)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def receipt(*, after: bool) -> bytes:
    """The receipt of order 1042, before and after the refund line: lines of text as
    gray bars."""
    ink, dim, line, ok = (40, 38, 34), (150, 146, 140), (226, 224, 219), (98, 151, 66)
    rows = [
        (0, 0, 360, 240, (255, 255, 255)),
        (24, 22, 150, 12, ink),
        (24, 46, 90, 8, dim),
    ]
    for k, w in enumerate((210, 180, 230)):
        rows += [(24, 72 + 22 * k, w, 8, dim), (290, 72 + 22 * k, 46, 8, dim)]
    rows += [(24, 142, 312, 1, line), (24, 156, 70, 10, ink), (282, 156, 54, 10, ink)]
    if after:
        rows += [
            (20, 178, 320, 22, (236, 244, 230)),
            (24, 184, 120, 9, ok),
            (284, 184, 52, 9, ok),
            (24, 214, 90, 10, ink),
            (282, 214, 54, 10, ink),
        ]
    return png(360, 240, rows)


DEMO_CHART = """flowchart TD
  A["A refund of 30 EUR comes in"] --> B{"Is it larger than the total?"}
  B -->|"no"| C["The receipt shows a line: Refund -30.00"]
  B -->|"yes"| D["The receipt shows 0.00 and a credit note"]
  C --> E["The new total stands under it"]"""


def refund_line(s: Shop) -> None:  # noqa: PLR0915 - over the limit before the limit was set
    """A task of the night that shows every form a document of Lem's takes: an outcome
    with Today and After and a chart, a criterion with its case and its chart, the
    plan's chart, an important decision with its story and a chart, a pull request that
    is not green for four reasons, a before and an after picture, a wide table, and the
    owner's page with links inside it."""
    t = "refund-line-on-receipt"
    s.task(t, "Show a refund as a line of its own on the receipt", "--night", TODAY)
    s.at(t, 610)
    s.session(t, 609.5, "shape", "night")
    folder = s.dir / "tasks" / t
    (folder / "task.md").write_text(
        "\n".join(
            [
                f"# {t}",
                "",
                "## The ask, verbatim",
                "",
                "Show a refund as a line of its own on the receipt",
                "",
                "## Type",
                "",
                "feat, because the receipt gets a new line",
                "",
                "## Outcome",
                "",
                (
                    "**A refund shows on the receipt as a line of its own, and the "
                    "total under it is what the customer paid.**"
                ),
                "",
                "Today:",
                "1. Order 1042 is 100.00 EUR.",
                "2. A refund of 30.00 EUR comes in.",
                "3. The receipt shows 70.00 EUR, and no line says why.",
                "",
                "After:",
                "1. Order 1042 is 100.00 EUR.",
                "2. A refund of 30.00 EUR comes in.",
                (
                    "3. The receipt shows `Refund -30.00` under the items, and "
                    "`Total 70.00` under it."
                ),
                "",
                "```mermaid",
                DEMO_CHART,
                "```",
                "",
                "| Receipt | Today | After |",
                "| --- | --- | --- |",
                "| The refund | not shown | a line of its own, in green |",
                "| The total | 70.00 | 70.00, under the refund |",
                "",
            ]
        )
    )
    s.state(
        t,
        605,
        "held",
        "the interview waits for the owner",
        "type: feat, because the receipt gets a new line",
    )
    crit = s.work / f"{t}.md"
    body = [
        "## Acceptance criteria",
        "",
        (
            "Size: full, because the receipt gets a new line and a rule for a refund "
            "larger than the total."
        ),
        "",
        (
            "1. A refund shows on the receipt as a line of its own, "
            "and the total stands under it:"
        ),
        "   1. Order 1042 is 100.00 EUR, and a refund of 30.00 EUR comes in.",
        "   2. The receipt shows `Refund -30.00` under the items.",
        "   3. The total under it is 70.00.",
        "",
        "   ```mermaid",
        *(f"   {line}" for line in DEMO_CHART.splitlines()),
        "   ```",
        "",
        "2. A refund larger than the total shows 0.00 and a credit note for the rest.",
    ]
    crit.write_text("\n".join(body) + "\n")
    s.approve(t, 598, crit, "--alone")
    tree = Path(s.project("worktree-dir", t).strip())
    s.git("worktree", "add", "-q", "-b", f"feat/{t}", str(tree), "main")
    test = "   - test: `sh tests/refund.sh` in `tests/refund.sh`"
    plan = [
        *body[:-1],
        test,
        "",
        body[-1],
        test,
        "",
        "## How it works",
        "",
        (
            "A refund becomes a line of the receipt; the rule for one larger than the "
            "total is the second branch."
        ),
        "",
        "```mermaid",
        "flowchart LR",
        '  A["The refund event"] --> B["The receipt\'s lines"]',
        '  B --> C{"Refund larger than the total?"}',
        '  C -->|"no"| D["Refund line, then the total"]',
        '  C -->|"yes"| E["Total 0.00, then a credit note"]',
        "```",
        "",
        "## Tasks",
        "",
        "1. The refund line.",
        "2. The credit note.",
        "",
    ]
    s.commit_in(
        tree,
        "docs(plans): the refund line on the receipt",
        {
            f"docs/plans/{TODAY}-{t}.md": "# The refund line on the receipt\n\n"
            + "\n".join(plan),
            "tests/refund.sh": "#!/bin/sh\nexit 0\n",
        },
    )
    s.state(t, 596, "building", "lead: builder")
    s.state(t, 590, "building", "plan committed, 2 tasks")
    s.criteria("record", t)
    s.at(t, 589)
    s.state(t, 588, "building", "task 1 of 2")
    s.log(t, 587.5, "builder.start", "job=task 1 of 2")
    # a decision of the build in doubt: the ladder climbed to the dialectic, whose pick
    # is taken at once
    chart = s.work / f"{t}-decision.mmd"
    chart.write_text(
        'flowchart TD\n  A["The receipt has its items"] --> B{"Where does the refund '
        'go?"}\n  B -->|"A"| C["In the items: the total reads as a price"]\n'
        '  B -->|"B"| D["Under the items: the total stands under it"]\n'
        '  B -->|"C"| E["In a footer: the customer looks for it"]\n'
    )
    s.decide(
        t,
        560,
        "log",
        t,
        "--by",
        "dialectic",
        "--what",
        "Where the refund line goes on the receipt",
        "--case",
        (
            "1. Order 1042 has three items, 100.00 EUR.\n"
            "2. A refund of 30.00 EUR comes in.\n3. The receipt prints its lines in "
            "the order of the choice.\n"
            "4. A customer reads the last line above the total as the price of an item."
        ),
        "--case-was",
        "derived",
        "--cause",
        (
            "The receipt prints every line of an order in one list, "
            "and the total is the last of them."
        ),
        "--option",
        "A: in the items, as a negative price",
        "--option",
        "B: a line of its own under the items, then the total",
        "--option",
        "C: in the footer, beside the payment",
        "--chose",
        "B: a line of its own under the items, then the total",
        "--why",
        "the total stands under what changed it",
        "--said",
        (
            "the developer picked B, the support person picked B, "
            "the accountant leaned to C"
        ),
        "--level",
        "gate=no ruling covers it",
        "--level",
        "personas=two for B, one for C: no clear pick",
        "--level",
        (
            "dialectic=B held: the case against it found no reader that takes the last "
            "line above the total as an item"
        ),
        "--chart",
        str(chart),
    )
    s.decide(
        t,
        540,
        "log",
        t,
        "--by",
        "lead",
        "--what",
        "How the refund line is colored",
        "--chose",
        "the theme's green, as a credit",
        "--why",
        (
            "a refund is money back to the customer, "
            "which the shop's receipts show in green"
        ),
    )
    s.state(t, 520, "building", "task 2 of 2")
    s.log(t, 519.5, "builder.start", "job=task 2 of 2")
    (folder / "media").mkdir(exist_ok=True)
    (folder / "media" / "receipt-before.png").write_bytes(receipt(after=False))
    (folder / "media" / "receipt-after.png").write_bytes(receipt(after=True))
    (folder / "report.md").write_text(
        "# Report\n\nThe refund line is in, under the items, and the total under "
        "it.\n\n"
        "![The receipt of order 1042 after a refund of 30.00 "
        "EUR](media/receipt-after.png)\n*The refund reads `-30.00` in green; "
        "the total under it is 70.00.*\n"
    )
    s.state(t, 480, "ready", "the report is written")
    s.session(t, 479.5, "land", "handoff")
    s.state(t, 479, "landing", "the checks start")
    tip = s.head(tree)
    s.log(t, 478, "gate.start", f"tip={tip}", "commands:=2")
    (folder / "gate").mkdir(exist_ok=True)
    (folder / "gate" / "01.log").write_text(
        "\x1b[32m....................\x1b[0m\n214 passed in 3.1s\n"
    )
    (folder / "gate" / "02.log").write_text("All checks passed!\n")
    s.log(
        t,
        475,
        "gate",
        "command=make test",
        "exit:=0",
        "last=214 passed",
        f"tip={tip[:7]}",
    )
    s.log(
        t,
        474,
        "gate",
        "command=make lint",
        "exit:=0",
        "last=All checks passed",
        f"tip={tip[:7]}",
    )
    s.log(t, 473, "review.start", "attempt:=1", "floor=round")
    s.log(
        t,
        462,
        "review",
        "attempt:=1",
        "round:=1",
        "kind=round",
        "verdict=must-fix",
        "must_fix:=1",
        "should:=1",
        "nit:=0",
        'answered:=["codex", "claude"]',
        "silent:=[]",
        'ran:=[{"name": "correctness", "why": "the total changes"}]',
        "left_out:=[]",
        f"tip={tip[:7]}",
    )
    s.log(
        t,
        450,
        "review",
        "attempt:=2",
        "round:=2",
        "kind=round",
        "verdict=clean",
        "must_fix:=0",
        "should:=0",
        "nit:=1",
        'answered:=["codex", "claude"]',
        "silent:=[]",
        'ran:=[{"name": "correctness", "why": "the total changes"}]',
        "left_out:=[]",
        f"tip={tip[:7]}",
    )
    reasons = [
        (
            "decision 1 was taken without the owner (Where the refund line goes on the "
            'receipt): "B: a line of its own under the items, then the total", '
            "by the dialectic"
        ),
        (
            f"the owner did not approve the criteria: they were approved on {TODAY} "
            "while the task ran without the owner"
        ),
        (
            "the bar is lower in `tests/test_receipt.py` (one assertion fewer). "
            "The builder: the old check read the total from a fixed row of the "
            "receipt, which the refund line moves; `test_total_after_refund` reads the "
            "same value by its label, which is what a customer reads. The review: "
            "the reason holds; the new test covers the row the old one read, and no "
            "other test lost a line. The resolution of round 1 did not touch the file"
        ),
        (
            "two rounds reviewed it: the last one left no must-fix, and round 1 left 1 "
            "must-fix that pull request #44 answers"
        ),
    ]
    s.log(
        t,
        448,
        "proposed",
        "green:=false",
        f"not_green:={json.dumps(reasons)}",
        f"tip={tip[:7]}",
    )
    s.state(
        t, 448, "open", "pull request https://github.com/acme/shop/pull/44", "not green"
    )
    # the merge agent's read of it (land.py `merge-review`): a request that is not green
    # is the owner's to merge, so it calls him
    (folder / "merge-review.md").write_text(MERGE_REVIEW)
    why = (
        "Verdict: call. The change does what both criteria say; it is not green for "
        "two choices taken without you, and I would keep both."
    )
    s.log(
        t,
        440,
        "merge.review",
        "verdict=call",
        "calls:=true",
        "by=claude",
        f"tip={tip[:9]}",
        f"why={why}",
    )
    # the landing's record of an open task, in land.py's form (`propose`,
    # `merge-review`): the whole commit it proposed and its pull request, which the
    # merge step shows and its form carries, and the merge agent's review of that commit
    whole = run("git", "-C", str(tree), "rev-parse", "HEAD").strip()
    (folder / "landing.json").write_text(
        json.dumps(
            {
                "branch": f"feat/{t}",
                "pushed": whole,
                "pr": {"number": 44, "url": "https://github.com/acme/shop/pull/44"},
                "proposed": whole,
                "title": "feat(receipt): a refund shows as a line of its own",
                "not_green": reasons,
                "merge_review": {
                    "tip": whole,
                    "verdict": "call",
                    "calls": True,
                    "why": why,
                    "by": "claude",
                    "at": (NOW - timedelta(minutes=440)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
            },
            indent=2,
        )
        + "\n"
    )
    (folder / "pr.md").write_text(
        (
            "feat(receipt): a refund shows as a line of its own\n\n"
            "Not green: four reasons, in `decisions.md`.\n\n"
            "<details><summary>Decision 1, its story: where the refund line "
            "goes</summary>\n\n"
            "1. Order 1042 has three items.\n2. A refund of 30.00 EUR "
            "comes in.\n\n```mermaid\n"
        )
        + chart.read_text()
        + "```\n\n</details>\n"
    )
    (folder / "decisions.md").write_text(
        "\n".join(
            [
                "# Decisions: a refund shows as a line of its own",
                "",
                "> [!CAUTION]",
                "> **2 things wait for the owner.**",
                ">",
                (
                    "> 1. Decision 1 was taken without the owner, by the dialectic: "
                    '"B: a line of its own under the items, then the total".'
                ),
                "> 2. The criteria were approved while the task ran without the owner.",
                "",
                (
                    "Pull request [#44](https://github.com/acme/shop/pull/44). "
                    "2 decisions: 1 by the dialectic, taken without the owner; "
                    "1 by the lead."
                ),
                "",
                (
                    "| # | The decision | Taken | Who decided | What it "
                    "costs | What undoes it |"
                ),
                "| --- | --- | --- | --- | --- | --- |",
                (
                    "| [1](#1-where-the-refund-line-goes-on-the-receipt) | Where the "
                    "refund line goes on the receipt | B. A line of its own under the "
                    "items, then the total | the dialectic, without the owner; "
                    "**not green** | nothing more | a change of the template, "
                    "one line |"
                ),
                (
                    "| 2 | How the refund line is colored | the theme's green, as a "
                    "credit | the lead | nothing | the theme's color |"
                ),
                "",
                "## 1. Where the refund line goes on the receipt",
                "",
                "**The case** (derived from the code, not run):",
                "",
                "1. Order 1042 has three items, 100.00 EUR.",
                "2. A refund of 30.00 EUR comes in.",
                (
                    "3. A customer reads the last line above the total "
                    "as the price of an item."
                ),
                "",
                "**This or that:**",
                "",
                "- A. In the items, as a negative price",
                "- **B. A line of its own under the items, then the total** (taken)",
                "- C. In the footer, beside the payment",
                "",
                "```mermaid",
                chart.read_text().rstrip(),
                "```",
                "",
            ]
        )
    )
    (folder / "built.md").write_text(
        "# What was built: a refund shows as a line of its own\n\n> [!NOTE]\n"
        "> A demo task: no run made these files.\n\n"
        "## What was built\n\n![The receipt before](media/receipt-before.png)\n"
        "*Before: no line says why the total is 70.00.*\n\n"
        "![The receipt after](media/receipt-after.png)\n"
        "*After: the refund is a line of its own.*\n"
    )
    rows = "".join(
        (
            f'<tr><td>{n}</td><td>{what}</td><td>{took}</td><td><span class="pill '
            f'{c}">{who}</span></td></tr>'
        )
        for n, what, took, who, c in (
            (
                1,
                "Where the refund line goes on the receipt",
                "B. A line of its own under the items, then the total",
                "the dialectic, without the owner",
                "bad",
            ),
            (
                2,
                "How the refund line is colored",
                "the theme's green, as a credit",
                "the lead",
                "muted",
            ),
        )
    )
    (folder / "page.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>A refund '
        "shows as a line of its own</title><style>body{font:15px/1.6 "
        "-apple-system,sans-serif;margin:0;padding:0 28px "
        "40px;color:#222;background:#fbf9f5} "
        "nav{position:sticky;top:0;background:#f1efeb;padding:8px "
        "0;display:flex;gap:8px}nav a{padding:2px 9px;border:1px solid "
        "#ddd;border-radius:999px;color:#222;text-decoration:none} "
        "[id]{scroll-margin-top:52px} section{min-height:520px}.tbl{overflow-x:auto} "
        "table{border-collapse:collapse;min-width:900px} "
        "td,th{text-align:left;padding:6px 10px;border-bottom:1px solid "
        "#ddd;vertical-align:top}.pill{display:inline-block;padding:1px "
        "9px;border-radius:999px;font-size:12px;border:1px solid "
        "currentColor;white-space:nowrap} .bad{color:#ae4022} "
        '.muted{color:#777}</style></head><body><h1 id="top">A refund shows as a line '
        'of its own</h1><nav><a href="#asked">What was asked</a><a '
        'href="#decisions">Decisions</a><a href="#top">Top</a></nav><section '
        'id="asked"><h2>What was asked</h2><p>Show a refund as a line of its own on '
        'the receipt.</p></section><section id="decisions"><h2>Decisions</h2><div '
        'class="tbl"><table><tr><th>#</th><th>The decision</th><th>Taken</th><th>Who '
        f"decided</th></tr>{rows}</table></div></section></body></html>\n"
    )


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def build(work: Path) -> Shop:
    """The repository of the afternoon in WORK, with its times moved to the minutes
    before NOW."""
    shop = Shop(work)
    afternoon(shop)
    refund_line(shop)
    shop.retime()
    return shop


def shots(out: Path, base: str) -> None:
    """Each picture, light and dark, through tests/board-cdp.mjs."""
    node = shutil.which("node")
    if node is None:
        sys.exit(
            "board-showcase: the pictures need Node (tests/board-cdp.mjs drives Chrome)"
        )
    # the task of the picture of one task: its Overview, with the merge review that
    # calls the owner first; `story` is the same page scrolled to the story of its
    # outcome and its chart
    task = f"{base}tasks/refund-line-on-receipt"
    story = [
        {
            "eval": (
                "const tab = document.querySelector('.tabbody'), after = "
                "[...document.querySelectorAll('.building .b-md p')].find(p => "
                "p.textContent.trim() === 'After:'); tab.scrollTop += "
                "after.getBoundingClientRect().top - "
                "tab.getBoundingClientRect().top - 14"
            ),
            "after": 800,
        }
    ]
    # its merge step on a phone, as it opens (the button off) and with its body scrolled
    # to the end (the button on)
    to_end = [
        {
            "eval": (
                "const body = document.querySelector('#confirm .cf-body'); "
                "body.scrollTop = body.scrollHeight"
            ),
            "after": 800,
        }
    ]
    pictures = {
        "board": (base, (WIDTH, HEIGHT), False, []),
        "task": (task, (WIDTH, HEIGHT), False, []),
        "backlog": (f"{base}backlog", (WIDTH, HEIGHT), False, []),
        "phone": (base, PHONE, True, []),
        "waits": (f"{base}waits", (WIDTH, HEIGHT), False, []),
        "phone-waits": (f"{base}waits", PHONE, True, []),
        "story": (task, (WIDTH, HEIGHT), False, story),
        "phone-review": (task, PHONE, True, []),
        "phone-merge-off": (f"{task}/merge", MERGE_PHONE, True, []),
        "phone-merge-on": (f"{task}/merge", MERGE_PHONE, True, to_end),
    }
    for name, (url, (width, height), mobile, steps) in pictures.items():
        for theme in ("light", "dark"):
            target = out / f"{name}-{theme}.png"
            spec = {
                "width": width,
                "height": height,
                "scale": 2,
                "mobile": mobile,
                "dark": theme == "dark",
                "steps": [{"goto": url, "wait": 3500}, *steps, {"shot": str(target)}],
            }
            spec_file = out / f".{name}-{theme}.json"
            spec_file.write_text(json.dumps(spec))
            ran = subprocess.run(
                [node, str(ROOT / "tests" / "board-cdp.mjs"), str(spec_file)],
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
            spec_file.unlink()
            if ran.returncode != 0 or not target.is_file():
                sys.exit(
                    f"board-showcase: no picture {target}: "
                    f"{(ran.stderr or ran.stdout).strip()[-400:]}"
                )
            print(f"shot {target} ({width} x {height})")


def main() -> None:
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--demo":
        work = Path(args[1]).resolve()
        work.mkdir(parents=True, exist_ok=True)
        shop = build(work)
        print(json.dumps({"repo": str(shop.repo), "state": str(shop.dir)}))
        return
    if len(args) != 1 or args[0].startswith("-"):
        sys.exit(__doc__)
    out = Path(args[0]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="lem-showcase-"))
    # the owner's status of this afternoon: no mark, so he is there, whatever the
    # machine's own mark says; and a list of workspaces with this one repository, served
    # by a server of its own
    env = {k: v for k, v in os.environ.items() if not k.startswith(("AGTERM_", "AGT_"))}
    env |= {"XDG_CONFIG_HOME": str(work / "config"), "LEM_SERVE": "off"}
    os.environ.update(env)
    port = free_port()
    server = None
    try:
        shop = build(work)
        (work / "config" / "lem").mkdir(parents=True, exist_ok=True)
        (work / "config" / "lem" / "machine.toml").write_text(
            f"[serve]\nport = {port}\n"
        )
        run(sys.executable, "-B", str(MAIN), "serve", "--add", str(shop.repo))
        server = subprocess.Popen(
            [sys.executable, "-B", str(MAIN), "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
            text=True,
        )
        # stdout=PIPE above: the process has its stdout
        said = json.loads(cast("IO[str]", server.stdout).readline())
        facts = {}
        for _ in range(50):
            try:
                with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
                    f"http://127.0.0.1:{port}/api/workspaces", timeout=2
                ) as reply:
                    facts = json.loads(reply.read())[0]
                break
            except OSError:
                time.sleep(0.1)
        if not facts:
            sys.exit(
                f"board-showcase: the server on port {port} listed "
                f"no workspace ({said})"
            )
        shots(out, f"http://127.0.0.1:{port}{facts['url']}")
    finally:
        if server is not None:
            server.terminate()
            server.wait(timeout=15)
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
