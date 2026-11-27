"""What the state folder keeps (`lem prune` and the server's hourly run): an ended task with
nothing new for `state.keep_days` keeps its small record, its journal folded into one summary
and its citations of the files that go cleared; an open or young task keeps every file; the old
folders of the experts, the panels, the naps and the cast's copies go; a link is never followed;
a failed removal is named and the next run finishes it; a dry run changes nothing; and a second
run changes nothing."""

import os
from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.records import MOMENT, record
from lem.app.sessions import acts, log
from lem.kernel.errors import Refusal
from lem.model.task import ending
from lem.records.approvals import Approval
from lem.records.criteria import Criteria
from lem.records.criterion import Criterion
from lem.records.journal.landing import CheckEnd, CheckWait, MergeWait
from lem.records.journal.task import StateNoted, Summary, Total
from lem.records.landing.record import Landing, Pull
from lem.records.sessions import SessionLine
from lem.records.tickets import Ticket
from lem.records.work import Investigation, Span, Talk
from lem.store import guard, sessions, tasks
from lem.store.retention import fold, rules
from lem.store.retention import run as retention_run
from lem.store.retention.run import pruned
from lem.store.retention.said import said
from unit.owner.looked import proposed

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from lem.records.record import Record

ENDED = MOMENT + timedelta(days=1)
LATER = ENDED + timedelta(days=40)
SMALL = (
    "session-acts.jsonl",
    "sessions.jsonl",
    "task.json",
    "task.lock",
    "task.md",
)
OTHER = (
    "handoff.md",
    "report.md",
    "checks/1-make.txt",
    "reviews/review-1.json",
    "pr-1-abc.md",
)


@pytest.fixture
def state(tmp_path: Path) -> Path:
    """A state folder of this Lem's form."""
    found = tmp_path / ".lem" / "state"
    found.mkdir(parents=True)
    (found / ".gitignore").write_text("*\n")
    return found


def landed(state: Path, slug: str, at: datetime = ENDED, **task: object) -> Record:
    """A landed task with a journal, a pull request, a proposal, cited files, and each file of
    its folder."""
    entries = (
        StateNoted(at=MOMENT, status="building", line="one builder"),
        CheckWait(at=MOMENT + timedelta(minutes=1), reason="load"),
        CheckEnd(at=MOMENT + timedelta(minutes=4), outcome="passed", say="passed"),
        StateNoted(at=MOMENT + timedelta(minutes=5), status="open", line="proposed"),
        MergeWait(at=MOMENT + timedelta(minutes=6)),
        StateNoted(at=at, status="landed", line="the pull request is merged"),
    )
    pull = Pull(number=44, url="https://github.com/o/r/pull/44", title="Gift note")
    cited = replace(proposed(green=False), notes_path="notes.md", text="pr-1-abc.md")
    landing = Landing(phase="ended", pull=pull, proposed=cited)
    investigation = Investigation(
        kind="fix", call="small", line="found it", report="investigation.md"
    )
    span = Span(name="small", start=MOMENT, end=MOMENT + timedelta(minutes=3))
    made = record(
        slug,
        status="landed",
        since=at,
        spans=(span,),
        investigation=investigation,
        **task,
    )
    found = tasks.create(state, replace(made, landing=landing, journal=entries))
    folder = state / "tasks" / slug
    for name in (*SMALL, *OTHER):
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(f"{name}\n")
    return found


def files(state: Path, slug: str) -> list[str]:
    folder = state / "tasks" / slug
    return sorted(
        str(path.relative_to(folder))
        for path in folder.rglob("*")
        if path.is_file() or path.is_symlink()
    )


@pytest.mark.parametrize("dry", [True, False])
def test_prune_refuses_old_state_before_it_touches_an_expert_folder(
    state: Path, *, dry: bool
) -> None:
    (state / "events.jsonl").write_text("{}\n")
    expert = state / "experts" / "old"
    expert.mkdir(parents=True)
    brief = expert / "brief.md"
    brief.write_text("the expert's brief\n")
    for path in (brief, expert):
        os.utime(path, (MOMENT.timestamp(), MOMENT.timestamp()))

    try:
        with pytest.raises(Refusal, match=r"Lem 0\.3") as caught:
            pruned(state, 30, "test", LATER, dry=dry)
        assert caught.value.code == "old-state"
    finally:
        assert brief.read_text() == "the expert's brief\n"


def test_prune_leaves_the_whole_task_when_task_json_is_a_link(state: Path) -> None:
    landed(state, "old-task")
    folder = state / "tasks" / "old-task"
    record_path = folder / "task.json"
    outside = state.parent / "old-record.json"
    record_path.rename(outside)
    record_path.symlink_to(outside)
    before = files(state, "old-task")
    snapshot = outside.read_bytes()

    run = pruned(state, 30, "test", LATER, dry=False)

    assert [one.path for one in run.skipped] == ["tasks/old-task/task.json"]
    assert record_path.is_symlink()
    assert files(state, "old-task") == before
    assert outside.read_bytes() == snapshot


@pytest.mark.parametrize("activity", ["transcript", "session-act"])
def test_prune_keeps_a_task_with_recent_session_activity(
    state: Path, activity: str
) -> None:
    slug = "old-task"
    landed(state, slug)
    folder = state / "tasks" / slug
    recent = LATER - timedelta(days=1)
    if activity == "transcript":
        sessions.append(
            folder,
            SessionLine(
                at=recent,
                source="resume",
                claude="claude-1",
                transcript="/transcripts/claude-1.jsonl",
                task=slug,
            ),
        )
    else:
        log.append(folder, acts.Wake(at=recent, session="session-1", why="merged"))
    before = files(state, slug)

    run = pruned(state, 30, "test", LATER, dry=False)

    assert (run.young, run.old) == (1, 0)
    assert files(state, slug) == before


def test_prune_keeps_the_size_and_removes_the_criteria_and_approval_history(
    state: Path,
) -> None:
    criterion = Criterion(number=1, text="Keep the gift note")
    approval = Approval(
        number=1,
        at=MOMENT,
        by="owner",
        size="small",
        why="one file",
        digest="approved",
        criteria=(criterion,),
        how="write it",
    )
    history = Criteria(
        size="small",
        why="one file",
        criteria=(criterion,),
        how="write it",
        approvals=(approval,),
        digest="approved",
        changed=(MOMENT,),
    )
    landed(state, "old-task", criteria=history)

    pruned(state, 30, "test", LATER, dry=False)

    found = tasks.read(state, "old-task")
    assert found.task.criteria == Criteria(size="small")
    (summary,) = found.journal
    assert isinstance(summary, Summary)
    assert summary.statuses == ("building", "open", "landed")


def test_a_run_past_the_cutoff_leaves_an_old_ended_task_its_small_record_only(
    state: Path,
) -> None:
    landed(state, "old-task")
    run = pruned(state, 30, ".lem/settings.toml", LATER, dry=False)
    assert files(state, "old-task") == sorted(SMALL)
    assert [(one.task, sorted(one.files)) for one in run.tasks] == [
        ("old-task", sorted(OTHER))
    ]
    assert (run.old, run.young, run.open) == (1, 0, 0)
    assert run.source == ".lem/settings.toml"
    assert run.before == LATER - timedelta(days=30)
    found = tasks.read(state, "old-task")
    assert ending.summarized(found) is True
    assert found.landing is not None
    assert found.landing.proposed is not None
    assert (found.landing.proposed.text, found.landing.proposed.notes_path) == (
        None,
        None,
    )
    assert found.task.investigation is not None
    assert found.task.investigation.report is None
    assert found.task.investigation.line == "found it"


def test_a_young_ended_task_an_open_one_and_one_inside_the_cutoff_keep_every_file(
    state: Path,
) -> None:
    landed(state, "young", at=LATER - timedelta(days=29))
    landed(state, "edge", at=LATER - timedelta(days=30, seconds=-1))
    tasks.create(state, record("still-open", status="building"))
    (state / "tasks" / "still-open" / "handoff.md").write_text("handoff\n")
    run = pruned(state, 30, "Lem's default", LATER, dry=False)
    assert (run.old, run.young, run.open) == (0, 2, 1)
    assert files(state, "young") == sorted((*SMALL, *OTHER))
    assert files(state, "edge") == sorted((*SMALL, *OTHER))
    assert "handoff.md" in files(state, "still-open")
    assert run.files == 0


def test_the_summary_keeps_the_statuses_the_last_state_the_pull_request_and_the_totals(
    state: Path,
) -> None:
    found = landed(
        state,
        "old-task",
        talk=Talk(
            reviewer="sol",
            turns=3,
            questions=1,
            settled=1,
            open=0,
            repaired=0,
            design=0,
            unargued=0,
            root=0,
            layer=0,
            shared=0,
            at=MOMENT,
        ),
    )
    summary = fold.summary_of(found, LATER)
    assert summary.statuses == ("building", "open", "landed")
    assert summary.last_state is not None
    assert summary.last_state.line == "the pull request is merged"
    assert (summary.first, summary.last, summary.entries) == (MOMENT, ENDED, 6)
    assert (summary.pull, summary.green, summary.talked) == (44, False, True)
    assert summary.reasons == ("the review left a must-fix",)
    assert summary.spans == (Total(name="small", seconds=180),)
    merge_wait = int((ENDED - MOMENT - timedelta(minutes=6)).total_seconds())
    assert summary.waits == (
        Total(name="checks", seconds=180),
        Total(name="merge", seconds=merge_wait),
    )


def test_a_summary_with_a_newer_entry_is_summarized_again_over_the_old_one(
    state: Path,
) -> None:
    found = landed(state, "old-task")
    pruned(state, 30, "Lem's default", LATER, dry=False)
    late = StateNoted(at=LATER, status="landed", line="a late line")
    once = tasks.read(state, "old-task")
    tasks.update(
        state,
        "old-task",
        lambda one: replace(one, journal=(*one.journal, late)),
        once.revision,
    )
    pruned(state, 30, "Lem's default", LATER + timedelta(days=31), dry=False)
    again = tasks.read(state, "old-task")
    assert len(again.journal) == 1
    summary = again.journal[0]
    assert isinstance(summary, Summary)
    assert summary.entries == len(found.journal) + 1
    assert summary.statuses == ("building", "open", "landed")
    assert summary.last_state == late
    assert summary.first == MOMENT


def test_a_second_run_changes_nothing(state: Path) -> None:
    landed(state, "old-task")
    pruned(state, 30, "Lem's default", LATER, dry=False)
    body = (state / "tasks" / "old-task" / "task.json").read_bytes()
    again = pruned(state, 30, "Lem's default", LATER + timedelta(hours=1), dry=False)
    assert (again.files, again.entries, again.summarized, again.tasks) == (0, 0, (), ())
    assert (state / "tasks" / "old-task" / "task.json").read_bytes() == body
    assert rules.call_of(tasks.read(state, "old-task"), LATER) == "old"


def test_a_dry_run_names_what_would_go_and_changes_no_file(state: Path) -> None:
    landed(state, "old-task")
    body = (state / "tasks" / "old-task" / "task.json").read_bytes()
    run = pruned(state, 30, "--days 30", LATER, dry=True)
    assert run.dry_run is True
    assert [(one.task, one.entries) for one in run.summarized] == [("old-task", 6)]
    assert run.files == len(OTHER)
    assert files(state, "old-task") == sorted((*SMALL, *OTHER))
    assert (state / "tasks" / "old-task" / "task.json").read_bytes() == body
    assert said(run).startswith(f"would remove {len(OTHER)} files of 1 ended tasks")


def test_a_link_is_never_followed_and_a_record_that_does_not_read_keeps_every_file(
    state: Path, tmp_path: Path
) -> None:
    landed(state, "old-task")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "precious.txt").write_text("keep me\n")
    (state / "tasks" / "old-task" / "linked").symlink_to(outside)
    (state / "tasks" / "old-task" / "linked.txt").symlink_to(outside / "precious.txt")
    (state / "tasks" / "a-link").symlink_to(outside)
    broken = state / "tasks" / "broken"
    broken.mkdir()
    (broken / "task.json").write_text("{not json")
    (broken / "handoff.md").write_text("handoff\n")
    run = pruned(state, 30, "Lem's default", LATER, dry=False)
    assert (outside / "precious.txt").read_text() == "keep me\n"
    assert (state / "tasks" / "old-task" / "linked").is_symlink()
    assert (broken / "handoff.md").is_file()
    skipped = {one.path: one.why for one in run.skipped}
    assert (
        skipped["tasks/a-link"] == "a link, which prune never follows and never removes"
    )
    assert skipped["tasks/old-task/linked"].startswith("a link")
    assert skipped["tasks/old-task/linked.txt"].startswith("a link")
    assert skipped["tasks/broken"].startswith("its task.json does not read")


@pytest.mark.parametrize("dry", [True, False])
def test_a_record_that_lem_cannot_open_is_skipped_and_the_rest_is_pruned(
    state: Path, *, dry: bool
) -> None:
    landed(state, "old-task")
    broken = state / "tasks" / "broken"
    (broken / "task.json").mkdir(parents=True)
    run = pruned(state, 30, "Lem's default", LATER, dry=dry)
    assert [one.task for one in run.summarized] == ["old-task"]
    skipped = {one.path: one.why for one in run.skipped}
    assert skipped["tasks/broken"].startswith("its task.json does not read")


def test_a_failed_removal_is_named_and_the_next_run_finishes_it(state: Path) -> None:
    landed(state, "old-task")
    checks = state / "tasks" / "old-task" / "checks"
    checks.chmod(0o500)
    try:
        run = pruned(state, 30, "Lem's default", LATER, dry=False)
    finally:
        checks.chmod(0o700)
    assert [one.path for one in run.failed] == ["tasks/old-task/checks/1-make.txt"]
    again = pruned(state, 30, "Lem's default", LATER, dry=False)
    assert again.failed == ()
    assert [one.files for one in again.tasks] == [("checks/1-make.txt",)]
    assert files(state, "old-task") == sorted(SMALL)


def test_the_old_folders_of_the_experts_panels_naps_and_casts_copies_go(
    state: Path,
) -> None:
    guard.writable(state)
    old = (LATER - timedelta(days=31)).timestamp()
    made = {
        "experts/2026-10-01-120001-a-question/brief.md": True,
        "experts/2026-12-30-120001-new-question/brief.md": False,
        "experts/loose-file.md": False,
        "panels/2026-10-01-panel/answers.json": True,
        "personas-cast/abc123/cast.md": True,
        "naps/2026-10-01-0300-dream/notes.md": True,
        "naps/2027-01-01-0300/notes.md": False,
        "backlog/item.md": False,
        "night/2026-10-01.json": False,
        "retros/2026-10-01.json": False,
    }
    for name, aged in made.items():
        path = state / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n")
        stamp = old if aged else LATER.timestamp()
        os.utime(path, (stamp, stamp))
        os.utime(path.parent, (stamp, stamp))
    unrelated = state / "experts" / "2026-10-01-other"
    unrelated.mkdir()
    os.utime(unrelated, (old, old))
    run = pruned(state, 30, "Lem's default", LATER, dry=False)
    assert unrelated.is_dir()
    assert sorted(one.path for one in run.folders) == [
        "experts/2026-10-01-120001-a-question",
        "naps/2026-10-01-0300-dream",
        "panels/2026-10-01-panel",
        "personas-cast/abc123",
    ]
    for name, aged in made.items():
        assert (state / name).exists() is not aged, name
    assert {one.kind for one in run.folders} == {"experts", "panels", "naps", "cast"}


def test_the_record_another_writer_changed_first_is_left_whole_for_the_next_run(
    state: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    landed(state, "old-task")
    aged = retention_run.aged_of

    def raced(records: list[Record], calls: list[rules.Call]) -> list[Record]:
        tasks.update(state, "old-task", lambda one: one, 1)
        return aged(records, calls)

    monkeypatch.setattr(retention_run, "aged_of", raced)
    run = pruned(state, 30, "Lem's default", LATER, dry=False)
    assert run.summarized == ()
    assert run.tasks == ()
    assert run.skipped[0].why.startswith("old-task is at revision 2, not 1")
    assert ending.summarized(tasks.read(state, "old-task")) is False
    assert files(state, "old-task") == sorted((*SMALL, *OTHER))


def test_a_pruned_tasks_ticket_and_the_steps_it_still_owes_stay_on_its_record(
    state: Path,
) -> None:
    ticket = Ticket(tracker="github", id="12", repo="acme/shop")
    landed(state, "old-task", ticket=ticket, night=MOMENT.date())
    pruned(state, 30, "Lem's default", LATER, dry=False)
    found = tasks.read(state, "old-task")
    assert (found.task.ticket, found.task.night) == (ticket, MOMENT.date())
    assert found.task.status == "landed"


def test_a_record_from_a_backup_folder_cannot_prune_the_live_task(state: Path) -> None:
    old = landed(state, "invoice")
    folder = state / "tasks" / "invoice"
    backup = folder.with_name("invoice-backup")
    backup.mkdir()
    (backup / "task.json").write_bytes(tasks.encode(old))
    live = replace(old, task=replace(old.task, status="building"))
    (folder / "task.json").write_bytes(tasks.encode(live))

    run = pruned(state, 30, "test", LATER, dry=False)

    assert (folder / "report.md").is_file()
    assert tasks.read(state, "invoice") == live
    assert [one.path for one in run.skipped] == ["tasks/invoice-backup"]


@pytest.mark.parametrize("dry", [True, False])
def test_a_summary_from_a_newer_release_cannot_prune_the_task(
    state: Path, *, dry: bool
) -> None:
    old = landed(state, "invoice")
    summary = rules.folded_into(old, summary=fold.summary_of(old, LATER))
    path = state / "tasks" / "invoice" / "task.json"
    path.write_bytes(tasks.encode(replace(summary, release="999.0.0")))
    lock = path.parent / tasks.LOCK
    lock.unlink()

    run = pruned(state, 30, "test", LATER, dry=dry)

    assert run.tasks == ()
    assert (path.parent / "report.md").is_file()
    assert not lock.exists()
    assert [one.path for one in run.skipped] == ["tasks/invoice"]


def test_a_cleanup_wake_after_classification_keeps_the_whole_task(
    state: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old = landed(state, "invoice")
    folder = state / "tasks" / "invoice"
    aged = retention_run.aged_of

    def woke(records: list[Record], calls: list[rules.Call]) -> list[Record]:
        found = aged(records, calls)
        assert found == [old]
        log.reached(folder, acts.Wake(at=LATER, session="session-1", why="merged"))
        return found

    monkeypatch.setattr(retention_run, "aged_of", woke)
    run = pruned(state, 30, "test", LATER, dry=False)

    assert tasks.read(state, "invoice") == old
    assert (folder / "report.md").is_file()
    assert run.tasks == ()
    assert log.read(folder)[-1].at == LATER


def test_an_invalid_nap_date_does_not_stop_the_other_folders(state: Path) -> None:
    guard.writable(state)
    invalid = state / "naps" / "2026-02-30-0900"
    valid = invalid.with_name("2026-03-01-0900")
    for folder in (invalid, valid):
        folder.mkdir(parents=True)
        (folder / "notes.md").write_text("a note\n")

    run = pruned(state, 30, "test", LATER, dry=False)

    assert invalid.is_dir()
    assert not valid.exists()
    assert [one.path for one in run.folders] == ["naps/2026-03-01-0900"]
