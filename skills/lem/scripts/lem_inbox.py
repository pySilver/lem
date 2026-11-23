"""What waits for the owner, sent to the Plannotator Inbox while he is away, and withdrawn once it no longer waits.

A thread of `lem serve` (`Watcher`), beside the push watcher of `lem_push`, looks at each workspace's
list of what waits for the owner (`lem_board_model.waits_of`) every LOOK_SECONDS. While his mark says
away (`/lem im-away`, the model's `away`) and the Inbox runs on this Mac with a tailnet address, each
row of the list goes to the Inbox once, in the thread named by the task's slug. A row that left the
list has its open question withdrawn, the mark either way, so that the phone shows "No longer
applies", unless the task's session holds it back while it works on his answer (`plan`); a
question he answered in the Inbox gets nothing. At `/lem im-back` nothing is withdrawn, and after
it nothing new is sent.

What a row becomes (`things_of`, `thing_of`, pure functions over the model):

- A thing: the row's key, its task and kind, its form (`question`, or `note` when no session can take
  a reply), whether the row itself asks anything (`asks`), the Claude Code session it goes as, for a
  merge the whole commit it is for (`tip`: `proposed` of the task's `landing.json`, taken only when it
  is the commit the model's proposal names, whose `proposed` event keeps its first 9 digits, since
  `lem land merge --tip` takes 40), and the time of the task's newest state block (`block`). A row
  whose thing changes (another form, session, tip or block, or a row that no longer asks) is a new thing: the old one is withdrawn when it was a question, and the new one is sent. The
  merge review and the merge of one task (`review:SLUG`, `merge:SLUG`) are one thing, the merge's. A
  `lem-ask` card of a task's session (`card:SLUG:PAGEID`) is no thing: the board answers it.
  While a task has a row of its own for its missing, deaf or stopped session, that row's note stands for
  the task, and its other rows wait until a session can take a reply. A row whose task's session opened
  less than the board's `GRACE_MS` ago (2 minutes) and has not yet logged its Claude Code session is
  no thing yet: its next look tells.
- A question goes as the task's newest Claude Code session: the `claude` of its newest
  `session.transcript` after its newest `session.open`, whose `source` is not `fork` (a fork is
  another Claude Code session started from the task's, which inherits `LEM_TASK`), and only while the
  board knows that session lives and answers (`lem_board_model.live_of`). Plannotator files such a
  message under that session (`--session claude-code:ID`), and the owner's reply comes back into it.
- A note goes with no session: a task with no live session, one whose session does not answer, one
  whose session stopped (the row "stopped" of the guard of a stopped session), a task queued after a
  dropped one, a refused merge, an open task with no proposal, no review of its tip or
  no whole commit of it on record.

The rule (`plan`): a row that the task's working session holds back (`lem_board_model.held_back`: a
held task whose session's turn runs on his answer) keeps its recorded thing as it stands, away or not:
it is neither withdrawn, forgotten nor sent again, so that a turn the Inbox's own wake started sends
nothing when it ends on the same block. Of every other recorded thing, one that still matches its row
stays, and one whose row left, or whose thing changed, leaves the record: a question is withdrawn (a
message as the same session, with `reply_to` its message and `supersedes` a list of its id), a note is only forgotten. While the mark
does not say away, or the door is closed, a thing whose session alone changed, or whose form changed
with it, stays, and so does one whose row still waits behind its task's session row: the question stays
open after `/lem im-back`, and while he is away it is withdrawn only when a newer message follows it.
While the mark does not say away, nothing is sent. A row with no recorded thing is sent while the mark
says away and the door is open. A thing written before a call that never answered is sent again, with
its payload and key, only while the mark says away, the door is open and its row is still the same
thing; while he is away with the door closed it waits, and otherwise it is forgotten, since nothing of
it may go now.

The door (`door_of`): `plannotator inbox status --json`, found on the server's PATH, read at each look
while the mark says away or a sent thing waits in the record. Lem starts no Inbox on purpose: a look
runs its calls only after its own `status` said running; Plannotator starts a stopped Inbox on any
`call`, so an Inbox the owner stops between that `status` and a call of the same look starts again in
the background, and the next look reads it running. A send needs the door open (running with a
`tailnet_url`); a withdrawal needs the Inbox running; a thing forgotten needs no call. Every call
runs with the server's environment less the variables Plannotator reads to name a session
(SESSION_VARIABLES), from the workspace's main checkout, with that checkout as `project_path`.

A withdrawal that Plannotator refuses because its message has no open question (ANSWERED) names no
open question any more: the owner answered it in the Inbox, skipped it, or archived the thread, and the
thing leaves the record with no message. Any other refusal, of the payload's shape among them, is a
failure of the call. No `read_thread` is made for a withdrawal.

A reply in a thread whose session is gone (the task's session changed after `/lem im-back`, decision
11 of away-questions-reach-phone): the look reads the thread with no `--session`, so that the read is
no session's, and for each reply of the owner's after the question it wakes the task's live session,
`lem session wake SLUG --why inbox`, once (`woke` in the record), and that session reads the thread
itself. The server wakes a session and never types into one. After each question it sends, a send
again after a failed call too, it wakes the task's session with the same word, so that the session
puts up its card.

The record is `inbox.json` in each workspace's state folder, written whole under `inbox.lock` by this
thread only: the door's last look (`running`, `url`, `tailnet_url`, `why`, `said`), the last call that
failed (`problem`), each thing sent, and `looked`, the time of the last look that changed any of them: a
look that changes nothing writes no file. A thing is written with its `idempotency_key` (the
workspace, the row's key and a random part, made once for the thing) and its `payload` before the
call: a look after a crash sends the payload again with the same key, which Plannotator answers with
the first message instead of a second one (`plannotator inbox --help`, "send_message"), and a new thing
of the same row never meets the key of a withdrawn one. The board's model reads the record as it reads
`forge.json`.

A failure of a call (exit 1 with `<code>: <message>` on stderr, exit 2, a time limit) is one line in
the server's log and `problem` in the record, and the next look tries again; no step of a task waits
for it.
"""

import contextlib
import fcntl
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

RECORD = "inbox.json"
# A whole commit, as `lem land merge --tip` takes it (`expected_refusal` in land.py).
COMMIT = re.compile(r"[0-9a-f]{40}")
LOCK = "inbox.lock"
# How often the watcher looks. A guess: a phone needs no fresher news, and a `status` took 0.22 s on
# the owner's Mac (Plannotator 0.29.0, 2026-11-22).
LOOK_SECONDS = 10
# How long one call of the Inbox may take. A guess: Plannotator's own request limit is 90 s
# (`REQUEST_TIMEOUT_MS4` of its 0.29.0 binary), and a send holds up only this thread.
CALL_SECONDS = 60
# The variables Plannotator 0.29.0 reads to name the session of a call (`SESSION_VARIABLES` and
# `SESSIONLESS_HOSTS` of `inbox-call-command.ts`, `inboxHostSessionFromEnv`, read in its binary on
# 2026-11-22), and the two that name a session's project. The server inherits the environment of the
# session whose hook started it, so a call with them would write as that session, or be refused as
# `session_ambiguous` or `session_mismatch`. Every other variable stays, the ones that pick
# Plannotator's data folder (`PLANNOTATOR_DATA_DIR`, `XDG_DATA_HOME`, `HOME`) among them, so that
# `status` and every call see the same Inbox.
SESSION_VARIABLES = (
    "PLANNOTATOR_SESSION_TAG", "T3CODE_THREAD_ID", "PI_SESSION_ID", "CODEX_THREAD_ID", "QWEN_CODE_SESSION_ID", "DSH_SESSION_ID",
    "DSH_PLANNOTATOR_SESSION_ID", "DSH_PLANNOTATOR_SESSION_FOR", "MUSE_SESSION_ID",
    "CLAUDECODE", "OMPCODE", "QWEN_CODE", "OPENCODE", "GEMINI_CLI", "COPILOT_CLI", "CURSOR_AGENT", "DSH_SHELL",
    "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_CHILD_SESSION", "PLANNOTATOR_SESSION_PROJECT", "PLANNOTATOR_CWD",
)
# Why nothing went to the Inbox at the door's last look, the record's `why`, which the board's page
# says in words (task 2 of away-questions-reach-phone).
NOT_INSTALLED = "not installed"
NOT_RUNNING = "not running"
NOT_ANSWERING = "not answering"
NO_TAILNET = "no tailnet address"
FAILED = "failed"
WHYS = (NOT_INSTALLED, NOT_RUNNING, NOT_ANSWERING, NO_TAILNET, FAILED)
QUESTION, NOTE = "question", "note"
# The words of a withdrawal, which the phone shows under the question it closes: for a row that left the
# list (an answer at the Mac, a park or a drop from the board, a merge by the merge agent), and for a
# thing whose row changed while a newer message of the same thread goes out (another session, tip or block).
WITHDRAWN = "This no longer waits for you: it was settled outside this thread."
REPLACED = "This no longer applies as it was asked: the newest message of this thread says what waits now."
# The refusal of a withdrawal whose message, `{id}`, has no open question: answered, skipped or closed by an
# archive (`planSupersede` of Plannotator 0.29.0's binary, read on 2026-11-22). Its other refusals with the
# same code, a `supersedes` that is no list among them, are no answer of the owner's.
ANSWERED = "invalid_supersedes: supersedes {id}: that message has no open question."
# The held line of an order that names no task (stages/new.md, step 6).
ORDER = re.compile(r'the order waits for the owner: "(.*)"', re.S)
# The parts of a thing that make it the same thing: a change of any is a new thing.
SAME = ("form", "asks", "session", "tip", "block")


class InboxError(Exception):
    """A call of the Inbox that failed, with Plannotator's own line, and in `said` all it wrote on stderr."""

    def __init__(self, line: str, said: str = "") -> None:
        super().__init__(line)
        self.said = said or line


def now_iso(seconds: float | None = None) -> str:
    return datetime.fromtimestamp(time.time() if seconds is None else seconds, timezone.utc).isoformat(timespec="seconds")


def environment(env: dict | None = None) -> dict:
    """The environment of every call: the server's, less the variables that name a session."""
    return {name: value for name, value in (os.environ if env is None else env).items() if name not in SESSION_VARIABLES}


# --- the rule: pure functions over the model -------------------------------------------------------


def claude_of(t) -> str | None:
    """The task's newest Claude Code session: the `claude` of its newest `session.transcript` after its
    newest `session.open`, whose `source` is not `fork`; None when there is none."""
    events = t.events
    start = max((i for i, e in enumerate(events) if e.get("event") == "session.open"), default=-1)
    for e in reversed(events[start + 1:]):
        if e.get("event") == "session.transcript" and e.get("source") != "fork" and isinstance(e.get("claude"), str) and e["claude"]:
            return e["claude"]
    return None


def answers(t, m, bm) -> bool:
    """Whether the task's session can take a reply now: the board knows it lives and answers."""
    f = bm.live_of(t, m)
    return bool(f and f["live"] and not f["unanswered"])


def merge_asks(t, bm) -> bool:
    """Whether a merge row asks merge or not now: a proposal, and the merge agent's review of its tip that
    calls the owner, as one read of the model (decision 6). A refused merge, and an open task with no
    proposal or no review of its tip, go as a note."""
    review, tip = t.merge_review, (t.proposal or {}).get("tip")
    if not (t.proposal and tip and review and not t.refused):
        return False
    of = review.get("tip")
    return bool(of) and (str(tip).startswith(str(of)) or str(of).startswith(str(tip)))


def commit_of(t, whole) -> str | None:
    """The whole commit of the task's proposal: WHOLE(slug), `proposed` of its `landing.json`, when it is 40
    hex digits and the commit the model's proposal names (its first 9 digits, as the `proposed` event
    keeps them); None otherwise, and the merge then asks nothing."""
    short = (t.proposal or {}).get("tip")
    full = whole(t.slug) if whole and short else None
    return full if isinstance(full, str) and COMMIT.fullmatch(full) and full.startswith(str(short)) else None


def thing_of(row: dict, m, bm, whole=None) -> dict | None:
    """The thing a row of "Waits for you" is (see the module's docstring); WHOLE(slug) gives the whole
    commit Lem proposed last (`landing.json`'s `proposed`). None while the task's session opened less than
    GRACE_MS ago and has not logged its Claude Code session: no form can be told yet."""
    t, kind = row["t"], row["kind"]
    claude = claude_of(t)
    tip = commit_of(t, whole) if kind == "merge" else None
    # what the row itself allows, apart from who can take the reply: a task with no session, one whose
    # session stopped, one queued after a dropped task, a refused merge and a merge with no review of its tip or no whole commit ask nothing
    can = kind not in ("session", "stopped", "after_dropped") and (kind != "merge" or (merge_asks(t, bm) and tip is not None))
    live = answers(t, m, bm)
    if can and live and claude is None and t.opened and m.now - t.opened["ts"] < bm.GRACE_MS:
        return None
    asks = can and live and claude is not None
    if kind == "merge" and tip is None:
        tip = (t.proposal or {}).get("tip")
    return {"key": row["key"], "task": t.slug, "kind": kind, "form": QUESTION if asks else NOTE, "asks": can,
            "session": claude if asks else None, "tip": str(tip) if tip else None, "block": t.last_ts}


def things_of(rows: list[dict], m, bm, whole=None) -> dict:
    """The things of a workspace's rows, by key: none for a merge review (its merge's thing carries it),
    none for a `lem-ask` card of a task's session, which the board answers, only the session's own note
    for a task that has a row for its missing, deaf or stopped session, and none for a row whose session
    cannot be told yet (`thing_of`)."""
    without = {r["t"].slug for r in rows if r["kind"] in ("session", "stopped")}
    out = {}
    for row in rows:
        if row["kind"] in ("review", "card") or (row["kind"] not in ("session", "stopped") and row["t"].slug in without):
            continue
        thing = thing_of(row, m, bm, whole)
        if thing is not None:
            out[row["key"]] = thing
    return out


def same(a: dict, b: dict) -> bool:
    return all(a.get(part) == b.get(part) for part in SAME)


def session_side(a: dict, b: dict) -> bool:
    """Whether two things of one row differ only in the session they go as, or in the form that a session
    which can take a reply, or none, gives them: not in what the row itself asks, its tip or its block."""
    return all(a.get(part) == b.get(part) for part in ("asks", "tip", "block"))


def plan(want: dict, sent: list[dict], away: bool, door: bool, behind: set | frozenset = frozenset(),
         held: set | frozenset = frozenset()) -> dict:
    """What a look does, from the things the rows are now (WANT, by key), the record's things (SENT),
    the owner's mark (AWAY), whether the door is open (DOOR), the keys of rows that still wait but
    are no thing now (BEHIND: behind their task's session row, or with a session not told yet), and the
    keys of rows that a working session holds back (HELD, `lem_board_model.held_back`), whose recorded
    thing is neither withdrawn, forgotten nor sent again, away or not:
    `withdraw`, the recorded questions to withdraw; `replaced`, the keys of those a newer message of the
    same thread follows (the mark says away and the door is open); `forget`, the recorded notes, and the
    things whose call never answered, to drop; `retry`, those to send again with their payload; `send`,
    the things to send once the old thing of their row left the record."""
    withdraw, forget, retry, leaving, replaced = [], [], [], set(), set()
    for r in sent:
        key = r["key"]
        w = want.get(key)
        if key in held:
            # the task's session works on his answer: its question stays as it was sent, until the turn ends
            continue
        if not r.get("message_id"):
            # written before a call that never answered: sent again only as the same thing while he is away
            if away and r.get("payload") and w is not None and same(r, w):
                if door:
                    retry.append(r)
                continue
            forget.append(r)
            leaving.add(key)
            continue
        if w is not None and same(r, w):
            continue
        if not (away and door) and ((w is not None and session_side(r, w)) or (w is None and key in behind)):
            continue
        if r.get("form") == QUESTION:
            withdraw.append(r)
            if away and door and (w is not None or key in behind):
                replaced.add(key)
        else:
            forget.append(r)
        leaving.add(key)
    kept = {r["key"] for r in sent} - leaving
    send = [w for key, w in want.items() if key not in kept] if away and door else []
    return {"withdraw": withdraw, "replaced": replaced, "forget": forget, "retry": retry, "send": send}


# --- the bodies --------------------------------------------------------------------------------------


def task_link(link, name: str, slug: str) -> str:
    return f"[{slug} on the board]({link(name, slug)})"


def no_session(t, link_line: str, extra: str = "") -> str:
    return f"{t.slug} has no session; open it on the board: {link_line}{extra}"


def block(kind: str, prompt: str, context: str, choices: tuple = (), stopped: str = "") -> str:
    """A question block of the Inbox (`plannotator inbox --help`, "Asking the reviewer questions")."""
    parts = [f":::{kind}", prompt, "", context]
    if stopped:
        parts += ["", f"Stopped: {stopped}"]
    if choices:
        parts += [""] + [f"- [ ] {choice}" for choice in choices]
    return "\n".join(parts + [":::"])


def message_of(thing: dict, row: dict, m, bm, *, task_dir: Path, plan_file: Path | None, link_line: str) -> dict:
    """The send's subject, body and attachments for a thing: the same case as the task's session says, by
    the row's kind (the plan of away-questions-reach-phone, task 1, "The message")."""
    t, kind = row["t"], row["kind"]
    slug = t.slug
    verb = bm.wait_say(row)["verb"]
    attachments: list[str] = []
    if thing["form"] == NOTE:
        if kind == "after_dropped":
            body = no_session(t, link_line, f"\n\n{bm.answer_of(t)}")
        elif kind == "stopped" and row.get("unread"):
            body = (f"The session of {slug} stopped, and Lem cannot read it: no event of the task came after the status message. "
                    f"Lem opens no second session by itself. Open a fresh one on the board: {link_line}")
        elif kind == "stopped":
            body = f"The session of {slug} stopped, and so did the fresh one that took its place. Open a fresh one on the board: {link_line}"
        elif kind == "merge" and t.refused:
            said = t.refused.get("said") or "nothing"
            body = f"The merge of {slug} did not go through: {said}\n\nThe task on the board: {link_line}"
        elif kind == "merge" and answers(t, m, bm) and claude_of(t):
            missing = ("no proposal of Lem's on record" if not t.proposal else "no merge review of the commit Lem proposed last" if not merge_asks(t, bm)
                       else "no whole commit of Lem's last proposal on record")
            body = f"{verb}: the pull request of {slug} waits for you with {missing}. Open it on the board: {link_line}"
        else:
            body = no_session(t, link_line, "" if kind == "session" else f"\n\nWhat waits: {verb}.")
        return {"subject": f"{slug}: {verb}", "body": body, "attachments": attachments}
    state_line = t.shown or t.text
    if kind == "breaker":
        d = t.breaker
        document = task_dir / str(d.document) if d.document else None
        try:
            text = document.read_text(encoding="utf-8").strip() if document else ""
        except OSError:
            text = ""
        what = bm.flat(d.what) if d.what else state_line
        body = (text or f"Breaker {d.id} of {slug}: {what}") + "\n\n" + block(
            "question", f"Breaker {d.id} of {slug}: help, park or drop?",
            f"{what.rstrip('.')}. The task's session waits for your answer. Help: write how it goes on in your answer's note.",
            ("Help", "Park", "Drop"), f"the build of {slug} stopped at breaker {d.id}")
    elif kind == "merge":
        pr = bm.pr_of(t)
        number = f" #{pr['n']}" if pr else ""
        url = f" ({pr['url']})" if pr and pr.get("url") else ""
        tip = thing["tip"]
        why = bm.review_why(t.merge_review)
        body = f"The merge review of {slug}: {why}\n\n" + block(
            "question", f"Merge pull request{number} of {slug} at commit {tip}?",
            f"The pull request{number}{url}, at the commit {tip}: your answer is for that commit only. The merge agent calls you: {why}",
            ("Merge", "Not now"), f"the merge of {slug} waits for you")
    elif kind == "plan":
        if plan_file is not None:
            attachments.append(str(plan_file))
        body = block("question", f"Build the plan of {slug}, or drop it?",
                     f"{state_line}. The plan is attached: read it, mark it, then answer." if plan_file else f"{state_line}.",
                     ("Build", "Drop"), f"the build of {slug} waits for your word")
    elif kind == "held" and ORDER.match(t.text or ""):
        words = ORDER.match(t.text).group(1)
        body = block("question-text", f"Which task should {slug} wait for?",
                     f"Your order: “{words}”. No open task fits it alone. Name the task to queue it after, or answer “no order”.",
                     stopped=f"{slug} waits for your answer")
    elif kind == "blocked":
        body = block("question-text", f"{slug} stopped: what should its session do?",
                     f"The task's session stopped on something it cannot settle alone: “{state_line}”. Tell it what to do, or answer /lem drop {slug}.",
                     stopped=f"{slug} stopped")
    else:
        body = block("question-text", f"{slug}: {verb}", f"“{state_line}”. {bm.answer_of(t)}", stopped=f"{slug} waits for you")
    return {"subject": f"{slug}: {verb}", "body": f"{body}\n\nThe task on the board: {link_line}", "attachments": attachments}


# --- the record --------------------------------------------------------------------------------------


_lock = threading.Lock()


@contextlib.contextmanager
def held(state: Path):
    """Hold `inbox.lock` of the state folder: one writer of `inbox.json` at a time."""
    state.mkdir(parents=True, exist_ok=True)
    with _lock, (state / LOCK).open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def read_record(state: Path) -> dict:
    """`inbox.json` of a state folder; an empty record when it is not there or does not read."""
    try:
        found = json.loads((state / RECORD).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        found = {}
    if not isinstance(found, dict):
        found = {}
    found["sent"] = [s for s in found.get("sent") or [] if isinstance(s, dict) and s.get("key")]
    return found


def write_record(state: Path, record: dict) -> None:
    """Write `inbox.json` whole: a file beside it, then a rename over it."""
    file = state / RECORD
    fresh = file.with_name(f".{file.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    fresh.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    fresh.replace(file)


def unlooked(record: dict) -> str:
    """The record as text without the time of its look, to tell whether a look changed it."""
    return json.dumps({k: v for k, v in record.items() if k != "looked"}, sort_keys=True)


# --- the calls ---------------------------------------------------------------------------------------


def run_cli(args: list[str], *, cwd: str, stdin: str | None = None, runner=subprocess.run) -> tuple[int, str, str]:
    """One run of `plannotator ARGS`, with the environment less the session's variables; its exit,
    stdout and stderr. A time limit is exit 124, a program that does not start exit 127."""
    program = shutil.which("plannotator")
    if program is None:
        return 127, "", "plannotator is not on the board server's PATH"
    try:
        ran = runner([program, *args], input=stdin, capture_output=True, text=True, cwd=cwd, env=environment(), timeout=CALL_SECONDS, check=False)
    except subprocess.TimeoutExpired:
        return 124, "", f"`plannotator {' '.join(args[:3])}` took more than {CALL_SECONDS} s"
    except OSError as error:
        return 127, "", f"plannotator did not start: {error}"
    return ran.returncode, ran.stdout or "", ran.stderr or ""


def door_of(cwd: str, runner=subprocess.run) -> dict:
    """The door's look: `plannotator inbox status --json`. `running`, `url`, `tailnet_url`, and when it
    is not open for a send, `why` (WHYS) and Plannotator's own words in `said`."""
    code, out, err = run_cli(["inbox", "status", "--json"], cwd=cwd, runner=runner)
    if code == 127:
        return {"running": False, "url": None, "tailnet_url": None, "why": NOT_INSTALLED, "said": err.strip()}
    try:
        status = json.loads(out) if out.strip() else {}
    except ValueError:
        status = {}
    status = status if isinstance(status, dict) else {}
    running = code == 0 and status.get("running") is True and bool(status.get("url"))
    tailnet = status.get("tailnet_url") if running and isinstance(status.get("tailnet_url"), str) and status.get("tailnet_url") else None
    why = None if running and tailnet else NO_TAILNET if running else NOT_ANSWERING if code == 2 else NOT_RUNNING if code == 1 else FAILED
    return {"running": running, "url": status.get("url") if running else None, "tailnet_url": tailnet, "why": why,
            "said": "" if why is None else (err.strip() or str(status.get("reason") or ""))[:300]}


def call(action: str, payload: dict, *, cwd: str, session: str | None = None, runner=subprocess.run) -> dict:
    """`plannotator inbox call [--session claude-code:ID] ACTION -` with PAYLOAD on stdin; its JSON
    result. InboxError with Plannotator's line for a failure."""
    args = ["inbox", "call", *(["--session", f"claude-code:{session}"] if session else []), action, "-"]
    code, out, err = run_cli(args, cwd=cwd, stdin=json.dumps(payload), runner=runner)
    if code != 0:
        raise InboxError(err.strip().splitlines()[-1] if err.strip() else f"`plannotator inbox call {action}` exited {code}", err)
    try:
        result = json.loads(out)
    except ValueError as error:
        raise InboxError(f"`plannotator inbox call {action}` printed no JSON") from error
    if not isinstance(result, dict):
        raise InboxError(f"`plannotator inbox call {action}` printed no JSON object")
    return result


def replies_after(thread: dict, message_id: str) -> list[str]:
    """The ids of the owner's messages after MESSAGE_ID in a thread as `read_thread` gives it in full."""
    messages = (thread.get("thread") or {}).get("messages") or []
    ids = [m.get("id") for m in messages]
    if message_id not in ids:
        return []
    return [m["id"] for m in messages[ids.index(message_id) + 1:] if (m.get("author") or {}).get("kind") == "person" and m.get("id")]


# --- the watcher -------------------------------------------------------------------------------------


class Watcher:
    """The thread of `lem serve` that sends what waits for the owner to the Inbox while he is away.
    `spaces()` gives the workspaces (serve.py's `Workspace`: `name`, `path`, `state`, `model()`,
    `plan_of(slug)`, `landing_of(slug)`); `link(name, slug)` the address of a task's page on the board;
    `wake(space, slug)` runs `lem session wake SLUG --why inbox` and returns whether a live session got
    the word."""

    def __init__(self, spaces, link, wake, *, runner=subprocess.run, log=None, now=time.time) -> None:
        import lem_board_model as bm  # here: the rule's functions take the model's module as an argument, and only the watcher holds it

        self.bm = bm
        self.spaces = spaces
        self.link = link
        self.wake = wake
        self.runner = runner
        self.log = log or (lambda line: sys.stderr.write(f"serve.py: {line}\n"))
        self.now = now
        self.said: dict[str, str] = {}

    def say(self, name: str, problem: str | None) -> None:
        """One line in the log for each new problem of a workspace, and none while it stays the same."""
        if problem and self.said.get(name) != problem:
            self.log(f"{name}: the Inbox: {problem}")
        if problem:
            self.said[name] = problem
        else:
            self.said.pop(name, None)

    def look(self) -> list[dict]:
        """One look at every workspace; what it did, each `{"workspace", "did", "key"}`."""
        done = []
        for space in self.spaces():
            try:
                done += self.look_at(space)
            except Exception as error:  # one workspace that fails says why, and the others are still looked at
                self.say(space.name, repr(error))
        return done

    def look_at(self, space) -> list[dict]:
        bm = self.bm
        m = space.model()
        if m.meta.get("demo") or m.sessions is None:
            # a demo sends nothing; before the server knows which sessions live, no form can be told
            return []
        state = Path(space.state)
        cwd = str(space.path)
        with held(state):
            record = read_record(state)
        away = m.away is not None
        if not away and not record["sent"]:
            return []
        door = door_of(cwd, self.runner)
        written = {"text": unlooked(record)}
        record.update(running=door["running"], url=door["url"], tailnet_url=door["tailnet_url"], why=door["why"], said=door["said"])
        rows = bm.waits_of(m)
        by_key = {r["key"]: r for r in rows}
        want = things_of(rows, m, bm, lambda slug: space.landing_of(slug).get("proposed"))
        steps = plan(want, record["sent"], away, door["tailnet_url"] is not None, {r["key"] for r in rows} - want.keys(), bm.held_back(m))
        done: list[dict] = []
        problems: list[str] = []

        def save() -> None:
            # only a change is written, with the time of its look: a look that changes nothing touches no file
            if unlooked(record) == written["text"]:
                return
            record["looked"] = now_iso(self.now())
            with held(state):
                write_record(state, record)
            written["text"] = unlooked(record)

        # a thing forgotten needs no call, so it leaves the record whether the Inbox runs or not
        for r in steps["forget"]:
            record["sent"].remove(r)
            done.append({"workspace": space.name, "did": "forgot", "key": r["key"]})
        save()
        if not door["running"]:
            return done
        # a thing written before a call that never answered: the same payload and key again
        for r in steps["retry"]:
            try:
                result = call("send_message", r["payload"], cwd=cwd, session=r.get("session"), runner=self.runner)
            except InboxError as error:
                problems.append(f"the send of {r['key']} again: {error}")
                continue
            self.sent_as(r, result)
            save()
            done.append({"workspace": space.name, "did": "sent", "key": r["key"]})
            if r.get("form") == QUESTION:
                self.wake(space, r["task"])
        for r in steps["withdraw"]:
            body = REPLACED if r["key"] in steps["replaced"] else WITHDRAWN
            payload = {"body": body, "reply_to": r["message_id"], "supersedes": [r["message_id"]], "idempotency_key": f"{r['idempotency_key']}-withdrawn"}
            try:
                call("send_message", payload, cwd=cwd, session=r.get("session"), runner=self.runner)
                did = "withdrew"
            except InboxError as error:
                if not any(line.startswith(ANSWERED.format(id=r["message_id"])) for line in error.said.splitlines()):
                    problems.append(f"the withdrawal of {r['key']}: {error}")
                    continue
                did = "answered"
            record["sent"].remove(r)
            done.append({"workspace": space.name, "did": did, "key": r["key"]})
        save()
        recorded = {r["key"] for r in record["sent"]}
        for thing in steps["send"]:
            if thing["key"] in recorded:
                continue
            row = by_key[thing["key"]]
            found = space.plan_of(thing["task"]) if thing["kind"] == "plan" else None
            message = message_of(thing, row, m, bm, task_dir=state / "tasks" / thing["task"], plan_file=found[0] if found else None,
                                 link_line=task_link(self.link, space.name, thing["task"]))
            key = f"lem-{space.name}-{thing['key']}-{secrets.token_hex(6)}"
            payload = {**{k: v for k, v in message.items() if v}, "thread": thing["task"], "project_path": cwd, "idempotency_key": key}
            entry = {**thing, "idempotency_key": key, "payload": payload, "at": now_iso(self.now()), "woke": []}
            record["sent"].append(entry)
            save()
            try:
                result = call("send_message", payload, cwd=cwd, session=thing["session"], runner=self.runner)
            except InboxError as error:
                problems.append(f"the send of {thing['key']}: {error}")
                continue
            self.sent_as(entry, result)
            save()
            done.append({"workspace": space.name, "did": "sent", "key": thing["key"]})
            if entry["form"] == QUESTION:
                self.wake(space, thing["task"])
        done += self.replies(space, m, record, cwd, problems)
        record["problem"] = "; ".join(problems) or None
        save()
        self.say(space.name, record["problem"])
        return done

    @staticmethod
    def sent_as(entry: dict, result: dict) -> None:
        """What the Inbox answered to a send, into the thing's record; its payload is no longer needed."""
        entry.update(message_id=result.get("message_id"), thread_id=result.get("thread_id"), thread_url=result.get("url"),
                     questions=[q.get("key") for q in result.get("questions") or [] if isinstance(q, dict) and q.get("key")])
        entry.pop("payload", None)

    def replies(self, space, m, record: dict, cwd: str, problems: list[str]) -> list[dict]:
        """Wake the task's live session once for each reply of the owner's in a thread whose question went
        as a session that no longer runs the task (decision 11 of away-questions-reach-phone)."""
        done = []
        for r in record["sent"]:
            t = m.by_slug.get(r.get("task"))
            if r.get("form") != QUESTION or not r.get("message_id") or t is None or claude_of(t) == r.get("session"):
                continue
            try:
                thread = call("read_thread", {"message_id": r["message_id"], "format": "full", "project_path": cwd}, cwd=cwd, runner=self.runner)
            except InboxError as error:
                problems.append(f"the read of {r['key']}'s thread: {error}")
                continue
            fresh = [one for one in replies_after(thread, r["message_id"]) if one not in r.setdefault("woke", [])]
            if fresh and self.wake(space, r["task"]):
                r["woke"] += fresh
                done.append({"workspace": space.name, "did": "woke", "key": r["key"]})
        return done

    def run(self, stopping: threading.Event) -> None:
        while not stopping.wait(LOOK_SECONDS):
            try:
                self.look()
            except Exception as error:  # the watcher never stops the server; it says why and looks again
                self.say("*", repr(error))
