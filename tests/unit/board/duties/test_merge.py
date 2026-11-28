"""The merges that are the board server's to make: the merge agent's `merge` and the owner's merge
that stands, never while the forge calls the request conflicting, a call waits on the forge or
this server runs the merge; the count of approved tasks that wait at each (the merge line); and
the wait of a merge that failed, which a new read ends."""

from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec
import pytest
from msgspec.structs import replace

from fakes.records import MOMENT
from lem.app.landing import merge
from lem.app.owner import forge
from lem.app.sessions import waking
from lem.app.tasks import resume
from lem.board.duties import merge as duty
from lem.board.duties import merge_count
from lem.board.duties.memory import Kept
from lem.kernel import clock
from lem.kernel.envelope import Envelope
from lem.kernel.errors import Refusal
from lem.model.criteria import contract
from lem.model.landing import merge_standing
from lem.model.owner.looks import MergeBasis
from lem.records.holds import Parked
from lem.records.landing.checks import Checked
from lem.records.landing.merge import MergeIntent
from lem.records.landing.propose import Standing
from lem.records.landing.start import Started
from lem.store import steps, tasks
from unit.board.duties.world import duty_of, landing_of, looked, opened
from unit.owner.looked import BASE, TIP, proposed, read, refused
from unit.sessions.world import here_of, made

if TYPE_CHECKING:
    from lem.app.landing.merge_called import BeforeCall
    from lem.app.sessions.here import Here
    from lem.model.landing.merge_asked import Asked
    from lem.records.record import Record

HOUR = MOMENT + timedelta(hours=1)
LOOK = forge.Look()


def asking(
    monkeypatch: pytest.MonkeyPatch, refusal: Refusal | None = None
) -> list[Asked]:
    """The merges the server asks for, each refused with `refusal` when one is named."""
    asked: list[Asked] = []

    def merged(
        folder: Path, slug: str, given: Asked, *, before_call: BeforeCall | None
    ) -> Envelope:
        asked.append(given)
        if refusal is not None:
            raise refusal
        return Envelope(
            ok=True, outcome=msgspec.Raw(msgspec.json.encode({"commit": TIP}))
        )

    monkeypatch.setattr(merge, "run", merged)
    return asked


def ended(kept: Kept) -> None:
    """Wait for each merge the server started."""
    for run in kept.merging.values():
        run.join()


def standing_task(here: Here, slug: str) -> Record:
    """An open task whose owner's merge, refused for the base, stands for the proposed tip."""
    found = opened(
        here, slug, proposed=proposed(green=False, who="owner"), reads=(read("call"),)
    )
    digest = merge_standing.digest_of(
        merge_standing.reasons_now(found), contract.mark(found.task)
    )
    kept = Standing(tip=TIP, reasons_digest=digest, by_act="board", at=MOMENT)
    landing = replace(landing_of(found), standing=kept)
    return tasks.update(
        here.where.state, slug, lambda one: replace(one, landing=landing), 1
    )


@pytest.mark.parametrize(
    "peers", ["", "[peers]\nbeta = -1\n", '[peers]\nbeta = "bad"\n']
)
def test_the_merge_agents_merge_of_the_proposed_tip_is_the_servers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, peers: str
) -> None:
    here = here_of(tmp_path)
    assert here.home is not None
    here.home.mkdir()
    (here.home / "machine.toml").write_text(peers)
    opened(here, "agent-merges", proposed=proposed(), reads=(read("merge"),))
    opened(here, "calls-owner", proposed=proposed(), reads=(read("call"),))
    opened(
        here,
        "owner-merges",
        proposed=proposed(green=False, who="owner"),
        reads=(read("merge"),),
    )
    asked = asking(monkeypatch)
    kept = Kept()
    duty.tick(duty_of(here, HOUR, kept))
    ended(kept)
    assert [(one.by, one.via, one.tip, one.standing) for one in asked] == [
        ("merger", "server", TIP, False)
    ]
    assert asked[0].subject == "Gift note"


KEEP = '[branch]\nbase = "main"\nhistory = "keep"\n'


def feature_of(here: Here, slug: str) -> None:
    """The open task `slug` made a feature: a landed part names it, and its `after` names
    the part, as `lem task open --part-of` leaves them."""
    made(here, "a-part", part_of=slug, status="landed")
    found = tasks.read(here.where.state, slug)

    def joined(record: Record) -> Record:
        return replace(record, task=replace(record.task, after=("a-part",)))

    tasks.update(here.where.state, slug, joined, found.revision)


@pytest.mark.parametrize("feature", [False, True])
def test_the_server_leaves_a_features_merge_to_the_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, feature: bool
) -> None:
    here = here_of(tmp_path)
    opened(here, "the-feature", proposed=proposed(), reads=(read("merge"),))
    if feature:
        feature_of(here, "the-feature")
    asked = asking(monkeypatch)
    kept = Kept()
    duty.tick(duty_of(here, HOUR, kept))
    ended(kept)
    merged = [(one.by, one.tip) for one in asked]
    assert merged == ([] if feature else [("merger", TIP)])


@pytest.mark.parametrize(("feature", "subject"), [(False, None), (True, "Gift note")])
def test_where_the_history_keeps_commits_a_features_standing_merge_is_a_squash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    feature: bool,
    subject: str | None,
) -> None:
    here = here_of(tmp_path)
    (tmp_path / ".lem" / "settings.toml").write_text(KEEP)
    standing_task(here, "stands")
    if feature:
        feature_of(here, "stands")
    asked = asking(monkeypatch)
    kept = Kept()
    duty.tick(duty_of(here, HOUR, kept))
    ended(kept)
    assert [(one.by, one.standing, one.subject) for one in asked] == [
        ("owner", True, subject)
    ]


def test_the_owners_merge_that_stands_is_carried_out_by_the_server(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    standing_task(here, "stands")
    asked = asking(monkeypatch)
    kept = Kept()
    duty.tick(duty_of(here, HOUR, kept))
    ended(kept)
    assert [(one.by, one.standing) for one in asked] == [("owner", True)]


def test_a_parked_approval_waits_for_resume_before_the_server_dispatches_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    found = standing_task(here, "stands")
    hold = Parked(since=MOMENT, words="wait for the owner")
    tasks.update(
        here.where.state,
        "stands",
        lambda one: replace(one, task=replace(one.task, hold=hold)),
        found.revision,
    )
    asked = asking(monkeypatch)
    board = duty_of(here, HOUR)
    intent = MergeIntent(tip=BASE, by="merger", via="server", at=HOUR)
    assert merge_count.waited(board, "other", intent).behind == ()
    duty.tick(board)
    ended(board.kept)
    assert asked == []

    resume.resumed(here.where.checkout, "stands")
    assert merge_count.waited(board, "other", intent).behind == ("stands",)
    duty.tick(board)
    ended(board.kept)
    assert [(one.by, one.standing, one.tip) for one in asked] == [("owner", True, TIP)]


def test_no_merge_while_the_forge_calls_it_conflicting_a_call_waits_or_it_runs(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    found = opened(here, "x", proposed=proposed(), reads=(read("merge"),))
    assert duty.merger_of(found, LOOK, frozenset()) == "merger"
    looked(here, "x", forge.CONFLICTING)
    assert duty.merger_of(found, forge.read(here.where.state), frozenset()) is None
    assert duty.merger_of(found, LOOK, frozenset({"x"})) is None
    intent = MergeIntent(tip=TIP, by="merger", via="server", at=MOMENT)
    waiting = replace(found, landing=replace(landing_of(found), intent=intent))
    assert duty.merger_of(waiting, LOOK, frozenset()) is None


def test_a_failed_merge_waits_for_its_own_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    found = opened(here, "x", proposed=proposed(), reads=(read("merge"),))
    asked = asking(monkeypatch, Refusal("lock", "the merge lock is held", "wait"))
    kept = Kept()
    for minutes in (0, 1, 4):
        moment = HOUR + timedelta(minutes=minutes)
        monkeypatch.setattr(clock, "now", lambda at=moment: at)
        duty.tick(duty_of(here, moment, kept))
        ended(kept)
    assert len(asked) == 1
    newer = replace(read("merge"), at=HOUR)
    reads = landing_of(found).reads
    landing = replace(landing_of(found), reads=(*reads, newer))
    tasks.update(here.where.state, "x", lambda one: replace(one, landing=landing), 1)
    duty.tick(duty_of(here, HOUR + timedelta(minutes=4), kept))
    ended(kept)
    assert len(asked) == 2
    duty.tick(duty_of(here, HOUR + timedelta(minutes=9), kept))
    ended(kept)
    assert len(asked) == 3


def test_a_merge_that_ran_says_so_and_one_refused_says_why(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    here = here_of(tmp_path)
    goes = opened(here, "goes", proposed=proposed(), reads=(read("merge"),))
    asking(monkeypatch)
    kept = Kept()
    duty.tick(duty_of(here, HOUR, kept))
    ended(kept)
    assert kept.said["goes"].startswith("Merged: goes is on the base.")
    tasks.update(
        here.where.state,
        "goes",
        lambda one: replace(one, task=replace(one.task, status="landed")),
        goes.revision,
    )
    asking(monkeypatch, Refusal("github", "GitHub refused it", "the owner acts"))
    opened(here, "refused", proposed=proposed(), reads=(read("merge"),))
    duty.tick(duty_of(here, HOUR, kept))
    ended(kept)
    assert (
        kept.said["refused"]
        == "The merge did not go: GitHub refused it; the owner acts"
    )
    said = capsys.readouterr().err
    assert "lem serve: shop: Merged: goes is on the base." in said


def test_the_server_picks_a_passed_run_on_the_current_base_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    (tmp_path / ".lem" / "settings.toml").write_text('[branch]\nbase = "main"\n')
    refs: list[str] = []

    def head(_git: object, _where: Path, ref: str) -> str:
        refs.append(ref)
        return BASE

    monkeypatch.setattr(type(here.ports.git), "remote_head", head)
    monkeypatch.setattr(
        type(here.ports.git), "tree", lambda *_: read("merge").base_tree
    )
    checked = Checked(
        tip=TIP, tree=TIP, base=BASE, inputs="inputs", outcome="passed", at=HOUR
    )
    for slug, base in (("a-stale", TIP), ("z-current", BASE)):
        opened(
            here,
            slug,
            proposed=proposed(),
            reads=(read("merge"),),
            checked=replace(checked, base=base),
        )
    asking(monkeypatch)
    kept = Kept()
    duty.tick(duty_of(here, HOUR, kept))
    ended(kept)
    assert tuple(kept.merging) == ("z-current",)
    assert refs == ["main"]


def test_his_standing_merge_that_the_base_refuses_again_still_stands_in_its_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    standing_task(here, "stands")
    asking(
        monkeypatch, Refusal("base", "origin's base moved", "a read of the moved base")
    )
    kept = Kept()
    duty.tick(duty_of(here, HOUR, kept))
    ended(kept)
    assert kept.said["stands"] == (
        f"The owner's merge still stands for {TIP}, and Lem merges it when it may: origin's "
        "base moved; a read of the moved base"
    )


def test_a_github_refusal_calls_the_owner_even_with_standing_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    standing_task(here, "stands")
    asking(
        monkeypatch,
        Refusal("github", "a required check failed", "the owner acts on GitHub"),
    )
    kept = Kept()
    duty.tick(duty_of(here, HOUR, kept))
    ended(kept)
    assert kept.said["stands"] == (
        "The merge did not go: a required check failed; the owner acts on GitHub"
    )


def test_a_base_back_at_the_checked_commit_releases_the_standing_merge(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    found = standing_task(here, "stands")
    landing = replace(landing_of(found), refused=refused("lem", "base"))
    assert landing.checked is not None
    record = replace(found, landing=landing)
    basis = MergeBasis(base=landing.checked.base, tree=read("call").base_tree)
    assert duty.merger_of(record, LOOK, frozenset(), basis) == "owner"
    assert duty.merger_of(record, LOOK, frozenset(), replace(basis, base=TIP)) is None


def test_a_task_uses_its_recorded_destination_once_for_order_and_eligibility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    (tmp_path / ".lem" / "settings.toml").write_text('[branch]\nbase = "stable"\n')
    found = standing_task(here, "stands")
    landing = landing_of(found)
    assert landing.checked is not None
    started = Started(round=1, branch="docs/stands", base_ref="main", at=MOMENT)
    resumed = replace(landing, refused=refused("lem", "base"), started=started)
    tasks.update(
        here.where.state,
        "stands",
        lambda one: replace(one, landing=resumed),
        found.revision,
    )
    refs: list[str] = []
    checked = landing.checked.base

    def head(_git: object, _checkout: Path, branch: str) -> str:
        refs.append(branch)
        return checked if branch == "main" else TIP

    monkeypatch.setattr(type(here.ports.git), "remote_head", head)
    monkeypatch.setattr(type(here.ports.git), "tree", lambda *_: read("call").base_tree)
    asked = asking(monkeypatch)
    kept = Kept()
    duty.tick(duty_of(here, HOUR, kept))
    ended(kept)
    assert [(one.by, one.standing) for one in asked] == [("owner", True)]
    assert refs == ["main"]


def test_ready_merges_do_not_delay_the_wake_for_stale_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    (tmp_path / ".lem" / "settings.toml").write_text('[branch]\nbase = "main"\n')
    stale = standing_task(here, "a-stale")
    parked = standing_task(here, "b-parked")
    tasks.update(
        here.where.state,
        "b-parked",
        lambda one: replace(one, task=replace(one.task, hold=Parked(since=MOMENT))),
        parked.revision,
    )
    landing = landing_of(stale)
    assert landing.checked is not None
    base = TIP
    assert landing.checked.base != base
    current = replace(landing.checked, base=base)
    opened(
        here, "z-ready", proposed=proposed(), reads=(read("merge"),), checked=current
    )
    monkeypatch.setattr(type(here.ports.git), "remote_head", lambda *_: base)
    monkeypatch.setattr(
        type(here.ports.git), "tree", lambda *_: read("merge").base_tree
    )
    sent: list[str] = []

    def wake(
        _here: Here, slug: str, why: str, _head: str, _now: object
    ) -> waking.Woken:
        sent.append(slug)
        return waking.Woken(
            task=slug, session="session", why=why, woke=True, opened=False, say="woke"
        )

    monkeypatch.setattr(waking, "wake", wake)
    asking(monkeypatch)
    kept = Kept()
    for now in (HOUR, HOUR + timedelta(seconds=1)):
        duty.tick(duty_of(here, now, kept))
        ended(kept)
    assert sent == ["a-stale"]
    assert tuple(kept.merging) == ("z-ready",)


@pytest.mark.parametrize(
    "stage", ["conflict", "moved-base", "rebasing", "red", "repairing"]
)
def test_the_merge_wait_count_keeps_standing_approval_until_rebase_checks_fail(
    tmp_path: Path, stage: str
) -> None:
    here = here_of(tmp_path)
    found = standing_task(here, "stands")
    landing = landing_of(found)
    if stage == "conflict":
        looked(here, "stands", forge.CONFLICTING)
    if stage == "moved-base":
        landing = replace(landing, refused=refused("lem", "base"))
    if stage in {"rebasing", "red", "repairing"}:
        found = replace(found, task=replace(found.task, status="landing"))
        landing = replace(landing, phase="preparing")
    if stage == "red":
        checked = Checked(
            tip=TIP, tree=TIP, base=TIP, inputs="inputs", outcome="red", at=HOUR
        )
        landing = replace(landing, checked=checked)
    if stage == "repairing":
        landing = replace(landing, checked=None, refused=refused("lem", "rule"))
    tasks.update(
        here.where.state,
        "stands",
        lambda one: replace(found, landing=landing),
        found.revision,
    )
    intent = MergeIntent(tip=TIP, by="merger", via="server", at=HOUR)
    waited = merge_count.waited(duty_of(here, HOUR), "merges", intent)
    assert (waited.waiting, waited.behind) == (
        (0, ()) if stage in {"red", "repairing"} else (1, ("stands",))
    )


def test_after_lems_base_refusal_the_server_merges_only_once_a_read_answers_it(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    base = replace(refused("lem", "base"), by="merger")
    found = opened(here, "x", proposed=proposed(), reads=(read("merge"),), refused=base)
    assert duty.merger_of(found, LOOK, frozenset()) is None
    answered = replace(found, landing=replace(landing_of(found), refused=None))
    assert duty.merger_of(answered, LOOK, frozenset()) == "merger"
    another = replace(read("merge"), base_call="another round")
    again = replace(answered, landing=replace(landing_of(answered), reads=(another,)))
    assert duty.merger_of(again, LOOK, frozenset()) is None
    github = replace(
        found, landing=replace(landing_of(found), refused=refused("github", "rule"))
    )
    assert duty.merger_of(github, LOOK, frozenset()) is None


def test_a_failed_merge_waits_under_its_own_tip_and_read_and_a_wake_under_its_own_why(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    found = opened(here, "x", proposed=proposed(), reads=(read("merge"),))
    key = duty.key_of(found)
    assert key == ("merge", "x", TIP, read("merge").at.isoformat())
    other = replace(proposed(), tip="e" * 40)
    moved = replace(found, landing=replace(landing_of(found), proposed=other))
    assert duty.key_of(moved) != key
    assert key != ("wake", "x", "queue")


def test_a_standing_merge_with_the_step_lock_held_tells_the_owner_to_wait(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    standing_task(here, "stands")
    board = duty_of(here, HOUR)

    with steps.step(here.where.state, "stands", "merge-review", HOUR):
        duty.tick(board)
        ended(board.kept)

    line = board.kept.said["stands"]
    assert "lem land merge-review stands" in line
    assert "wait for it to end, then run lem land merge stands again" in line


def test_the_ledger_names_the_standing_merge_step_lock_test() -> None:
    path = Path(__file__).parents[3] / "ledger" / "fates" / "board-duties.tsv"
    row = "Duties.test_his_standing_merge_whose_step_lock_is_held_is_refused_with_land_s_line"
    (proof,) = (
        line.split("\t")[2]
        for line in path.read_text().splitlines()
        if line.split("\t")[0].endswith(row)
    )
    test = test_a_standing_merge_with_the_step_lock_held_tells_the_owner_to_wait
    assert proof == f"unit.board.duties.test_merge.{test.__name__}"
