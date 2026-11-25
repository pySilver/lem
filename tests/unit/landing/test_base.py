"""`base` (`model/landing/base.py`, `base_said.py`, `base_stops.py`, `base_kept.py`): when the
branch is on origin's base, what it refuses before a rebase, what it records of the move, and
the words of a rebase that stopped (`landing.md` E, "Teammate commit", "Conflict with the base",
"Rebase refused by git", "Merge-only change")."""

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import base, base_empty, base_kept, base_stops
from lem.model.landing.rebased import Clash
from lem.model.landing.world import Due, Held
from lem.records.landing.start import Based, Polished, Resolution
from unit.landing.worlds import (
    BASE,
    BASED,
    MOMENT,
    OTHER,
    PREPARED,
    TIP,
    TREE,
    task,
    world,
)

WHERE = "/work/.lem/worktrees/fix-the-login"
AHEAD = base.Facts(ahead=1)
NEW = "2" * 40
NEW_TREE = "3" * 40
MOVED = "4" * 40


def code_of(found: object) -> str:
    """The code of a refusal; a case fails on anything else."""
    assert isinstance(found, Refusal), found
    return found.code


def refusal_of(found: object) -> Refusal:
    """The refusal; a case fails on anything else."""
    assert isinstance(found, Refusal), found
    return found


def test_base_holds_while_the_branch_is_on_origins_base_with_a_commit_of_its_own() -> (
    None
):
    record = task(**PREPARED)
    assert isinstance(base.holds(record, world()), Held)
    assert base.holds(record, world(rebasing=True)).why == (
        "a rebase is in progress in the worktree"
    )
    assert isinstance(base.holds(record, world(remote=OTHER)), Due)
    assert isinstance(base.holds(record, world(remote=OTHER, remote_in_tip=True)), Held)
    assert isinstance(
        base.holds(task(**{**PREPARED, "pushed": OTHER}), world(remote=OTHER)), Held
    )
    assert isinstance(base.holds(record, world(base=OTHER)), Due)
    assert isinstance(base.holds(record, world(base_in_tip=False)), Due)
    assert isinstance(base.holds(task(**{**PREPARED, "based": None}), world()), Due)
    empty = task(**{**PREPARED, "based": replace(BASED, tip=BASE)})
    assert (
        base.holds(empty, world(tip=BASE)).why == "the branch has no commit of its own"
    )


def test_base_rebases_only_a_tip_without_origins_base() -> None:
    record = task(**PREPARED)
    assert base.decide(record, world(), AHEAD, WHERE) == "onto"
    assert base.decide(record, world(base_in_tip=False), AHEAD, WHERE) == "rebase"


def test_a_builders_own_rebase_is_refused_with_how_to_finish_or_end_it() -> None:
    found = refusal_of(
        base.decide(task(**PREPARED), world(rebasing=True), AHEAD, WHERE)
    )
    assert found.code == "rebase-in-progress"
    assert "aborts none" in found.why
    assert f"git -C {WHERE} rebase --continue" in found.fix
    assert f"git -C {WHERE} rebase --abort" in found.fix


def test_a_teammates_commits_are_each_named_with_the_pull_that_brings_them() -> None:
    theirs = tuple(f'{n:09d} "change {n}"' for n in range(12))
    facts = base.Facts(ahead=1, theirs=theirs)
    found = refusal_of(base.decide(task(**PREPARED), world(remote=OTHER), facts, WHERE))
    assert found.code == "teammate"
    assert "holds 12 commit(s) that Lem did not push" in found.why
    assert '000000000 "change 0"' in found.why
    assert '000000009 "change 9"' in found.why
    assert "change 10" not in found.why
    assert ", and 2 more" in found.why
    assert f"git -C {WHERE} pull --rebase origin docs/fix-the-login" in found.fix
    assert "lem land base fix-the-login runs again" in found.fix


def test_a_remote_commit_the_base_or_a_push_holds_is_no_teammates() -> None:
    # origin's task branch is outside the tip, and every commit of it is on origin's base
    found = base.decide(
        task(**PREPARED), world(remote=OTHER, base_in_tip=False), AHEAD, WHERE
    )
    assert found == "rebase"


def test_base_refuses_a_head_off_the_tasks_branch_before_it_rebases() -> None:
    off = base.Facts(ahead=1, on_branch=False)
    found = refusal_of(
        base.decide(task(**PREPARED), world(base_in_tip=False), off, WHERE)
    )
    assert found.code == "off-branch"


def test_a_second_rebase_of_lems_own_unpublished_rebase_is_refused_with_the_tip_before() -> (
    None
):
    made = Based(tip=NEW, base=BASE, before=TIP, carried=False, at=MOMENT)
    record = task(**{**PREPARED, "based": made})
    moved = world(tip=NEW, base=OTHER, base_in_tip=False)
    dropped = base.Facts(ahead=1, dropped=True)
    assert base.decide(record, moved, AHEAD, WHERE) == "rebase"
    found = refusal_of(base.decide(record, moved, dropped, WHERE))
    assert found.code == "rebase-again"
    assert f"git -C {WHERE} reset --hard {TIP}" in found.fix
    pushed = task(**{**PREPARED, "based": made, "pushed": NEW})
    assert base.decide(pushed, moved, dropped, WHERE) == "rebase"
    waiting = Resolution(files=("a.txt",), before=TIP, after=TIP, base=BASE)
    resolving = task(**{**PREPARED, "based": made, "resolution": waiting})
    assert base.decide(resolving, moved, dropped, WHERE) == "rebase"
    after = task(**{**PREPARED, "based": made})
    assert (
        base.decide(after, world(tip=OTHER, base_in_tip=False), AHEAD, WHERE)
        == "rebase"
    )


def test_a_stop_after_a_rebase_that_dropped_the_change_names_the_tip_before_it() -> (
    None
):
    kept = base.Facts(ahead=0, orig=TIP)
    found = refusal_of(base.decide(task(**PREPARED), world(tip=BASE), kept, WHERE))
    assert found.code == "merge-only"
    assert f"git -C {WHERE} reset --hard {TIP}" in found.fix


def test_a_branch_with_no_commit_of_its_own_has_nothing_to_land() -> None:
    found = refusal_of(
        base.decide(task(**PREPARED), world(), base.Facts(ahead=0), WHERE)
    )
    assert found.code == "nothing-to-land"
    assert "lem task move fix-the-login dropped" in found.fix


def test_the_move_is_judged_from_gits_merges() -> None:
    plain = base.judged(world(), base.After(tip=TIP, tree=TREE, ahead=1))
    assert (plain.tip, plain.before, plain.carried, plain.unshown_paths) == (
        TIP,
        TIP,
        False,
        (),
    )
    shown = base.After(
        tip=NEW, tree=NEW_TREE, ahead=1, merged=NEW_TREE, reviewed=NEW_TREE
    )
    carried = base.judged(world(), shown)
    assert (carried.tip, carried.before, carried.base, carried.carried) == (
        NEW,
        TIP,
        BASE,
        True,
    )
    other = base.judged(world(), replace(shown, reviewed=MOVED))
    assert not other.carried
    differ = replace(shown, merged=MOVED, differ=("a.txt",), left_out=(OTHER,))
    unshown = base.judged(world(), differ)
    assert (unshown.carried, unshown.unshown_paths, unshown.unshown_commits) == (
        False,
        ("a.txt",),
        (OTHER,),
    )
    clash = base.judged(world(), replace(shown, merged=Clash(files=("f.txt",))))
    assert (clash.carried, clash.unshown_paths) == (False, ("f.txt",))
    quiet = base.judged(world(), replace(shown, left_out=(OTHER,)))
    assert quiet.unshown_commits == ()


def test_a_rebase_that_drops_a_merge_only_change_is_refused_with_the_tip_before_it() -> (
    None
):
    lost = Based(
        tip=BASE,
        base=BASE,
        before=TIP,
        carried=False,
        unshown_paths=("m.txt",),
        at=MOMENT,
    )
    record = task(**PREPARED)
    found = refusal_of(base_empty.emptied(record, world(), lost, 0, WHERE))
    assert found.code == "merge-only"
    assert f"was at {TIP}" in found.why
    assert f"git -C {WHERE} reset --hard {TIP}" in found.fix
    assert base_empty.emptied(record, world(), lost, 1, WHERE) is None
    again = task(**{**PREPARED, "based": lost})
    repeated = base.decide(again, world(tip=BASE), base.Facts(ahead=0), WHERE)
    assert code_of(repeated) == "merge-only"
    plain = replace(lost, unshown_paths=())
    assert (
        code_of(base_empty.emptied(record, world(), plain, 0, WHERE))
        == "nothing-to-land"
    )


def aborted(**fields: object) -> base_stops.Aborted:
    """The worktree after the abort, as it was before the rebase, with `fields` over it."""
    made = base_stops.Aborted(
        rebasing=False, branch_tip=TIP, head=TIP, where=WHERE, on="docs/fix-the-login"
    )
    return replace(made, **fields)


def test_what_an_abort_left_is_named_with_the_command_that_puts_it_back() -> None:
    assert base_stops.left(world(), aborted()) == ""
    still = base_stops.left(world(), aborted(rebasing=True))
    assert still == f"a rebase is still in progress (`git -C {WHERE} rebase --abort`)"
    moved = base_stops.left(world(), aborted(branch_tip=OTHER, head=OTHER))
    assert f"is at 999999999, not at its tip before the rebase {TIP}" in moved
    assert f"`git -C {WHERE} reset --hard {TIP}`" in moved
    detached = base_stops.left(world(), aborted(branch_tip=OTHER, on=None))
    assert f"`git -C {WHERE} branch -f docs/fix-the-login {TIP}`" in detached
    assert f"`git -C {WHERE} switch docs/fix-the-login`" in detached
    head = base_stops.left(world(), aborted(head=OTHER, on=None))
    assert head.startswith(
        "HEAD is detached at 999999999, not on the branch docs/fix-the-login"
    )
    # HEAD at the branch's own commit, detached: named, never taken for the branch
    same = base_stops.left(world(), aborted(on=None))
    assert same.startswith(f"HEAD is detached at {TIP[:9]}")
    other = base_stops.left(world(), aborted(on="main"))
    assert other.startswith("HEAD is on main, not on the branch docs/fix-the-login")


def test_a_conflict_names_its_files_for_a_builder() -> None:
    found = base_stops.conflict(
        task(**PREPARED), world(), ("a.txt", "b.txt"), aborted()
    )
    assert found.code == "conflict"
    assert "stopped on these file(s): a.txt, b.txt; it was undone" in found.why
    assert "a builder resolves it" in found.fix
    left = base_stops.conflict(
        task(**PREPARED), world(), ("a.txt",), aborted(rebasing=True)
    )
    assert "its abort left the worktree not as it was" in left.why
    assert "nothing is kept for a builder" in left.fix


def test_a_rebase_git_refused_gives_gits_words_and_where_the_worktree_is() -> None:
    said = "no rebase today / error: The pre-rebase hook refused to rebase"
    found = base_stops.refused(task(**PREPARED), world(), said, aborted())
    assert found.code == "git-refused"
    assert found.why == (
        "the rebase onto origin/main failed with no file in conflict, and the worktree "
        f"is as it was; git said: {said}"
    )
    assert "the owner removes what git names" in found.fix
    assert "builder resolves" not in found.fix
    left = base_stops.refused(
        task(**PREPARED), world(), said, aborted(head=OTHER, on=None)
    )
    assert (
        "and the worktree is not as it was: HEAD is detached at 999999999" in left.why
    )
    assert "puts the worktree back as named, and" in left.fix


def test_base_keeps_a_conflict_for_a_builder_and_its_resolution_once_he_rebased() -> (
    None
):
    record = task(**PREPARED)
    waiting = base_kept.conflicted(record, world(), ("a.txt",))
    assert waiting.landing is not None
    assert waiting.landing.resolution == Resolution(
        files=("a.txt",), before=TIP, after=TIP, base=BASE
    )
    again = base_kept.conflicted(waiting, world(base=OTHER), ("b.txt",))
    assert again.landing is not None
    assert again.landing.resolution == Resolution(
        files=("a.txt", "b.txt"), before=TIP, after=TIP, base=OTHER
    )
    resolved = Based(tip=NEW, base=OTHER, before=NEW, carried=False, at=MOMENT)
    done = base_kept.kept(again, resolved, None, ("c.txt",))
    assert done.landing is not None
    assert done.landing.based == resolved
    # every file git's merge meets a conflict in, a later commit's stop too
    assert done.landing.resolution == Resolution(
        files=("a.txt", "b.txt", "c.txt"), before=TIP, after=NEW, base=OTHER
    )
    left = replace(resolved, tip=TIP)
    unmoved = base_kept.kept(again, left, None)
    assert unmoved.landing is not None
    assert again.landing.resolution == unmoved.landing.resolution


def test_base_keeps_the_polish_pass_by_its_new_name() -> None:
    polished = Polished(before=OTHER, after=TIP, at=MOMENT)
    record = task(**{**PREPARED, "polished": polished})
    kept = base_kept.kept(record, replace(BASED, tip=NEW), replace(polished, after=NEW))
    assert kept.landing is not None
    assert kept.landing.polished == replace(polished, after=NEW)
    dropped = base_kept.kept(
        record, replace(BASED, tip=NEW), replace(polished, after=None)
    )
    assert dropped.landing is not None
    assert dropped.landing.polished == replace(polished, after=None)
    same = base_kept.kept(record, BASED, None)
    assert same.landing is not None
    assert same.landing.polished == polished
