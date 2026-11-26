"""`lem task park` and `lem task resume`: only a task no agent works on is parked, its park
keeps the hold it put aside, and the resume of a dropped task opens a new one: from its breaker's
handoff, or as a new request when the release stop dropped it."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.command import lem
from fakes.records import MOMENT, record
from fakes.repo import RealRepo, run_git
from lem.adapters.git_cli import GitCli
from lem.addons.proposals import dropping
from lem.app.tasks import carry, park, resume
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.landing import propose_criteria, propose_doubts
from lem.model.task import resumes
from lem.ports.faults import Unanswered
from lem.records.approvals import Approval, PersonaRead
from lem.records.criteria import Criteria
from lem.records.criterion import Criterion
from lem.records.decisions import Breaker, Taken
from lem.records.holds import Blocked, BreakerHold, OwnerHold, Parked, ReleaseHold
from lem.records.journal.task import OwnerAct, StateNoted, Summary
from lem.records.task import Shape
from lem.records.tickets import Ticket
from lem.records.work import Span
from lem.store import places, tasks
from lem.store import workspace as claims
from unit.addons.flow.test_proposals import TODAY, passed_item
from unit.task.spaces import made, read, result, said, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.task import Status
    from lem.store.places import Workspace

SLUG = "gift-note"
BREAKER = Breaker(
    id=3,
    at=MOMENT,
    cause="criteria",
    what="the criteria cannot all hold",
    document="breaker-3.md",
    handoff="handoff.md",
)


@pytest.mark.parametrize("status", ["queued", "planned"])
def test_a_task_that_waits_is_parked_and_the_resume_brings_it_back(
    tmp_path: Path, status: Status
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status=status)
    park.parked(tmp_path, SLUG, "later")
    task = read(where, SLUG).task
    assert task.status == status
    assert isinstance(task.hold, Parked)
    assert task.hold.words == "later"
    back = resume.resumed(tmp_path, SLUG)
    assert (back.resumed, back.status) == ("parked", status)
    resumed = read(where, SLUG)
    assert resumed.task.hold is None
    entry = resumed.journal[-1]
    assert isinstance(entry, StateNoted)
    assert entry.line == "resumed" and entry.hold is None


def test_resume_finds_the_hold_before_the_park(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    where = workspace(tmp_path)
    made(
        where,
        SLUG,
        status="building",
        hold=BreakerHold(number=BREAKER.id, since=MOMENT),
        decisions=(BREAKER,),
    )
    park.parked(tmp_path, SLUG, "not now")
    parked = read(where, SLUG)
    assert result(lem("waiting", "--task", SLUG, cwd=tmp_path))["breakers"] == []
    now = clock.now()
    monkeypatch.setattr(clock, "now", lambda: now)
    back = resume.resumed(tmp_path, SLUG)
    waiting = result(lem("waiting", "--task", SLUG, cwd=tmp_path))
    assert [one["breaker"]["id"] for one in waiting["breakers"]] == [BREAKER.id]
    assert back.breaker == BREAKER.id
    resumed = read(where, SLUG)
    assert resumed.revision == parked.revision + 1
    assert resumed.task.hold == BreakerHold(number=BREAKER.id, since=now)
    assert resumed.journal[-1] == StateNoted(
        at=now, status="building", hold="breaker", line="resumed"
    )


@pytest.mark.parametrize(
    ("status", "said"),
    [
        ("building", "works now"),
        ("shaping", "shapes it now"),
        ("ready", "build is done"),
        ("open", "build is done"),
        ("landed", "stays ended"),
    ],
)
def test_only_a_task_no_agent_works_on_is_parked(
    tmp_path: Path, status: Status, said: str
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status=status)
    with pytest.raises(Refusal) as refused:
        park.parked(tmp_path, SLUG, "later")
    assert refused.value.code == "park"
    assert said in refused.value.why


def test_a_task_that_waits_for_the_owner_is_parked(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    wait = OwnerHold(on="interview", line="the interview waits", since=MOMENT)
    made(where, SLUG, status="shaping", hold=wait)
    park.parked(tmp_path, SLUG, "later")
    resume.resumed(tmp_path, SLUG)
    resumed = read(where, SLUG)
    assert resumed.task.hold == wait
    entry = resumed.journal[-1]
    assert isinstance(entry, StateNoted)
    assert (entry.line, entry.hold) == ("resumed", "owner")


def test_resume_records_the_block_before_the_park(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    block = Blocked(why="the base is red", fix="repair the base", since=MOMENT)
    made(where, SLUG, status="ready", hold=block)
    park.parked(tmp_path, SLUG, "later")
    resume.resumed(tmp_path, SLUG)
    resumed = read(where, SLUG)
    assert resumed.task.hold == block
    entry = resumed.journal[-1]
    assert isinstance(entry, StateNoted)
    assert (entry.line, entry.hold) == ("resumed", "blocked")


def test_a_task_that_runs_or_ended_is_no_resume(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="building")
    made(where, "done", status="landed")
    for slug in (SLUG, "done"):
        with pytest.raises(Refusal) as refused:
            resume.resumed(tmp_path, slug)
        assert refused.value.code == "resume"


def dropped_with_breaker(where: Workspace, **fields: object) -> None:
    """A task dropped while its breaker waited, with its handoff and its notes."""
    shape = Shape(type="fix", why="the total is wrong", track="full")
    made(where, SLUG, status="dropped", decisions=(BREAKER,), shape=shape, **fields)
    folder = places.task_folder(where.state, SLUG)
    for name in ("handoff.md", "breaker-3.md", "task.md"):
        (folder / name).write_text(f"# {name}\n", encoding="utf-8")
    (folder / "brief.md").write_text(
        f"task: {SLUG}\nbranch: fix/{SLUG}\nworktree: /old/{SLUG}\nthe lead's brief\n",
        encoding="utf-8",
    )
    (folder / "landing.json").write_text("{}", encoding="utf-8")


def real(tmp_path: Path) -> Workspace:
    """A workspace over a real repository with an origin."""
    repo = RealRepo.init(tmp_path / "repo", {"README.md": b"one\n"})
    return workspace(repo.checkout)


def test_a_dropped_task_with_its_breaker_goes_on_in_a_new_task(tmp_path: Path) -> None:
    where = real(tmp_path)
    ticket = Ticket(tracker="linear", id="MBZ-12")
    talk = Span(name="plan-talk", start=MOMENT, end=MOMENT)
    open_lead = Span(name="lead", start=MOMENT)
    dropped_with_breaker(
        where, ticket=ticket, branch=f"fix/{SLUG}", spans=(talk, open_lead)
    )
    run_git(where.checkout, "branch", f"fix/{SLUG}")
    back = resume.resumed(where.checkout, SLUG)
    new = f"{SLUG}-2"
    assert (back.task, back.resumed, back.breaker, back.branch) == (
        new,
        "dropped",
        3,
        f"fix/{new}",
    )
    task = read(where, new).task
    assert (task.status, task.hold, task.resumed_from) == (
        "building",
        BreakerHold(number=3, since=task.since),
        SLUG,
    )
    assert (task.ticket, task.decisions, task.shape) == (
        ticket,
        (BREAKER,),
        read(where, SLUG).task.shape,
    )
    folder = places.task_folder(where.state, new)
    assert sorted(path.name for path in folder.iterdir() if path.suffix == ".md") == [
        "breaker-3.md",
        "brief.md",
        "handoff.md",
        "task.md",
    ]
    assert not (folder / "landing.json").exists()
    brief = (folder / "brief.md").read_text(encoding="utf-8")
    assert f"task: {new}\nbranch: fix/{new}\n" in brief
    assert f"resumed from: {SLUG}; read handoff.md and breaker-3.md first" in brief
    assert (where.lem / "worktrees" / new / "README.md").is_file()
    assert read(where, SLUG).task.status == "dropped"
    assert read(where, new).release == read(where, SLUG).release
    assert task.spans == (talk,)
    with pytest.raises(Refusal) as again:
        resume.resumed(where.checkout, SLUG)
    assert again.value.code == "resumed"


def test_the_first_task_of_the_line_with_the_next_free_number(tmp_path: Path) -> None:
    where = real(tmp_path)
    dropped_with_breaker(where)
    made(where, f"{SLUG}-2", status="landed")
    assert resume.resumed(where.checkout, SLUG).task == f"{SLUG}-3"


def test_a_resume_keeps_the_owner_approval_and_the_history_the_proposal_reads(
    tmp_path: Path,
) -> None:
    for variant in ("flagged", "skipped"):
        check_carried_approval(tmp_path / variant, skipped=variant == "skipped")


def check_carried_approval(tmp_path: Path, *, skipped: bool) -> None:
    where = real(tmp_path)
    criterion = Criterion(number=1, text="The export keeps the note.")
    before = MOMENT - timedelta(minutes=5)
    read_by_personas = PersonaRead(
        by="lem",
        started=before,
        ended=before,
        asked=2,
        answered=2,
        families=("opus",),
        criteria=1,
        flagged=1,
        digest="a" * 12,
    )
    approval = Approval(
        number=1,
        at=MOMENT,
        by="owner",
        size="full",
        why="Two readers",
        digest="a" * 12,
        criteria=(criterion,),
    )
    criteria = Criteria(
        size="full",
        why=approval.why,
        criteria=approval.criteria,
        digest=approval.digest,
        approvals=(approval,),
        reads=() if skipped else (read_by_personas,),
        skip="yes" if skipped else None,
        skip_at=before if skipped else None,
        skip_approval=1 if skipped else None,
    )
    dropped_with_breaker(where, criteria=criteria)
    resumed = read(where, resume.resumed(where.checkout, SLUG).task)
    assert resumed.task.criteria == criteria
    assert resumed.journal == (OwnerAct(at=approval.at, act="approve-carried"),)
    assert propose_criteria.unread(resumed) is None
    assert propose_doubts.doubted(resumed) is None
    assert propose_doubts.unapproved(resumed) is None


def test_a_task_the_release_stop_dropped_goes_on_as_a_new_request(
    tmp_path: Path,
) -> None:
    where = real(tmp_path)
    stop = ReleaseHold(began="0.1.0", running="0.3.1", say="x", since=MOMENT)
    dropped_with_breaker(where, hold=stop, branch=f"fix/{SLUG}")
    run_git(where.checkout, "branch", f"fix/{SLUG}")
    back = resume.resumed(where.checkout, SLUG)
    task = read(where, back.task).task
    assert (back.resumed, task.status, task.shape, task.decisions) == (
        "request",
        "shaping",
        None,
        (),
    )
    assert task.branch == f"fix/{back.task}"
    folder = places.task_folder(where.state, back.task)
    assert (folder / "handoff.md").is_file()
    assert not (folder / "brief.md").exists()
    ran = lem("task", "resume", "other", cwd=where.checkout)
    assert ran.code == 1


def test_a_release_stop_successor_claims_the_same_reviewer_item(tmp_path: Path) -> None:
    where = real(tmp_path)
    path = passed_item(where.state)
    stop = ReleaseHold(began="0.1.0", running="0.3.1", say="x", since=MOMENT)
    dropped_with_breaker(where, hold=stop, ask=path, backlog_item=path)

    back = resume.resumed(where.checkout, SLUG)
    assert read(where, back.task).task.backlog_item == path
    with pytest.raises(Refusal) as caught:
        dropping.dropped(where, path, TODAY)
    assert caught.value.code == "item-held"
    assert back.task in caught.value.why


def test_a_stop_that_named_no_branch_starts_the_request_from_the_base(
    tmp_path: Path,
) -> None:
    where = real(tmp_path)
    stop = ReleaseHold(began="0.1.0", running="0.3.1", say="x", since=MOMENT)
    dropped_with_breaker(where, hold=stop, branch="fix/gone")
    back = resume.resumed(where.checkout, SLUG)
    assert back.branch is None
    assert "the base branch" in back.says


def test_a_dropped_task_with_no_breaker_that_waits_is_refused_with_its_ask(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    helped = Taken(id=4, at=MOMENT, what="w", chose="c", why="y", by="owner", breaker=3)
    dropped_with_breaker(where)
    tasks.update(
        where.state,
        SLUG,
        lambda one: replace(one, task=replace(one.task, decisions=(BREAKER, helped))),
        1,
    )
    with pytest.raises(Refusal) as refused:
        resume.resumed(tmp_path, SLUG)
    assert "no breaker that waits" in refused.value.why
    assert refused.value.fix == "new work for it is a new ask: /lem fix the login"


def test_a_dropped_task_whose_journal_became_a_summary_is_refused_with_its_ask(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    summary = Summary(
        at=MOMENT, statuses=("dropped",), first=MOMENT, last=MOMENT, entries=3
    )
    dropped_with_breaker(where)
    tasks.update(where.state, SLUG, lambda one: replace(one, journal=(summary,)), 1)
    with pytest.raises(Refusal) as refused:
        resume.resumed(tmp_path, SLUG)
    assert "summary" in refused.value.why
    assert not (where.state / "tasks" / f"{SLUG}-2").exists()


def test_a_resume_whose_brief_is_not_utf8_makes_nothing(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    dropped_with_breaker(where)
    brief = places.task_folder(where.state, SLUG) / "brief.md"
    brief.write_bytes(b"task: \xff\n")
    with pytest.raises(Refusal) as refused:
        resume.resumed(tmp_path, SLUG)
    assert refused.value.code == "unreadable"
    assert not (where.state / "tasks" / f"{SLUG}-2").exists()


def test_the_command_parks_and_resumes(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="queued")
    parked = lem("task", "park", SLUG, "--why", "after the release", cwd=tmp_path)
    assert result(parked)["resumed"] == "parked"
    again = lem("task", "resume", SLUG, cwd=tmp_path)
    assert said(again).endswith("from where it was put aside")
    assert read(where, SLUG).task.hold is None


def test_a_parked_task_two_releases_back_stops_and_a_dropped_one_passes(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="planned", hold=Parked(since=MOMENT))
    tasks.update(where.state, SLUG, lambda one: replace(one, release="0.1.0"), 1)
    with pytest.raises(Refusal) as refused:
        resume.resumed(tmp_path, SLUG)
    assert refused.value.code == "release"
    made(where, "old", status="dropped", ticket=Ticket(tracker="linear", id="MBZ-1"))
    tasks.update(where.state, "old", lambda one: replace(one, release="0.1.0"), 1)
    record = read(where, "old")
    assert record.task.hold is None
    assert isinstance(
        resume.release.checked(where.state, "old", ends=True).task.hold, ReleaseHold
    )


def test_a_line_of_resumes_that_goes_round_is_refused() -> None:
    first = record("first", status="dropped", resumed_from="second")
    second = record("second", status="dropped", resumed_from="first")
    with pytest.raises(Refusal) as refused:
        resumes.next_slug("second", (first, second))
    assert refused.value.code == "resume-line"


def test_a_successor_git_could_not_check_out_is_made_whole_by_the_resume_again(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    where = real(tmp_path)
    old, new = f"fix/{SLUG}", f"fix/{SLUG}-2"
    dropped_with_breaker(where, branch=old)
    run_git(where.checkout, "branch", old)

    def stopped(*_args: object) -> None:
        raise Unanswered("git", "the worktree could not be checked out")

    with monkeypatch.context() as patch:
        patch.setattr(GitCli, "worktree_add", stopped)
        with pytest.raises(Unanswered, match="could not be checked out"):
            resume.resumed(where.checkout, SLUG)
    assert read(where, f"{SLUG}-2").task.status == "building"
    assert run_git(where.checkout, "rev-parse", new) == run_git(
        where.checkout, "rev-parse", old
    )
    back = resume.resumed(where.checkout, SLUG)
    assert (back.task, back.breaker) == (f"{SLUG}-2", 3)
    assert (where.lem / "worktrees" / f"{SLUG}-2" / "README.md").is_file()
    brief = (places.task_folder(where.state, f"{SLUG}-2") / "brief.md").read_text()
    assert f"worktree: {where.lem / 'worktrees' / f'{SLUG}-2'}\n" in brief
    with pytest.raises(Refusal) as again:
        resume.resumed(where.checkout, SLUG)
    assert again.value.code == "resumed"


def test_a_request_whose_branch_git_lost_names_it_missing(tmp_path: Path) -> None:
    where = real(tmp_path)
    stop = ReleaseHold(began="0.1.0", running="0.3.1", say="x", since=MOMENT)
    dropped_with_breaker(where, hold=stop, branch="fix/gone")
    assert resume.resumed(where.checkout, SLUG).missing == "fix/gone"


def test_a_fold_while_the_files_are_read_makes_no_successor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    where = workspace(tmp_path)
    dropped_with_breaker(where)
    summary = Summary(
        at=MOMENT, statuses=("dropped",), first=MOMENT, last=MOMENT, entries=3
    )
    reading = carry.taken

    def folded_meanwhile(folder: Path) -> carry.Taken:
        taken = reading(folder)
        revision = read(where, SLUG).revision
        tasks.update(
            where.state, SLUG, lambda one: replace(one, journal=(summary,)), revision
        )
        return taken

    monkeypatch.setattr(carry, "taken", folded_meanwhile)
    with pytest.raises(Refusal) as refused:
        resume.resumed(tmp_path, SLUG)
    assert "folded into its summary" in refused.value.why
    assert not (where.state / "tasks" / f"{SLUG}-2").exists()


def test_a_resume_waits_for_origin_without_stopping_another_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    where = real(tmp_path)
    old = f"fix/{SLUG}"
    dropped_with_breaker(where, branch=old)
    run_git(where.checkout, "branch", old)
    fetching, release = Event(), Event()
    fetch = GitCli.fetch
    # Bound the waits for the worker and its local Git calls (unmeasured estimate).
    reach = 10.0

    def slow(git: GitCli, checkout: Path) -> None:
        fetching.set()
        assert release.wait(timeout=2 * reach), "the test did not release the fetch"
        fetch(git, checkout)

    monkeypatch.setattr(GitCli, "fetch", slow)
    with ThreadPoolExecutor(max_workers=2) as pool:
        resumed = pool.submit(resume.resumed, where.checkout, SLUG)
        try:
            assert fetching.wait(timeout=reach), "the resume did not start a fetch"
            other = pool.submit(claims.claimed, where.state, lambda _: record("other"))
            assert other.result(timeout=reach).task.slug == "other"
            assert not resumed.done()
        finally:
            release.set()
        assert resumed.result(timeout=reach).task == f"{SLUG}-2"


@pytest.mark.parametrize("release_stop", [False, True], ids=["breaker", "release"])
def test_a_resume_does_not_claim_an_existing_branch(
    tmp_path: Path, *, release_stop: bool
) -> None:
    where = real(tmp_path)
    old, new = f"fix/{SLUG}", f"fix/{SLUG}-2"
    stop = ReleaseHold(began="0.1.0", running="0.3.1", say="x", since=MOMENT)
    dropped_with_breaker(where, branch=old, hold=stop if release_stop else None)
    run_git(where.checkout, "branch", old)
    run_git(where.checkout, "commit", "--allow-empty", "-m", "unrelated local work")
    run_git(where.checkout, "branch", new)
    unrelated = run_git(where.checkout, "rev-parse", new)

    with pytest.raises(Refusal) as refused:
        resume.resumed(where.checkout, SLUG)
    assert refused.value.code == "branch-taken"
    assert new in refused.value.why
    assert not places.task_folder(where.state, f"{SLUG}-2").exists()
    assert run_git(where.checkout, "rev-parse", new) == unrelated
