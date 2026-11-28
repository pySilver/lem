"""`lem task split NAME --file CRITERIA`: the headings of the feature's approved criteria give
its parts, each a task with the feature's read and approval copied onto its own criteria, in
order; the feature waits for all of them on `feature/NAME`; a split run again, or after a cut,
makes only what is missing (`docs/plans/2026-11-27-a-feature-in-parts.md`, step 36b)."""

from typing import TYPE_CHECKING

import msgspec
import pytest
from msgspec.structs import replace

from fakes.records import record
from fakes.repo import RealRepo, run_git
from lem.app.criteria import approve, persona
from lem.app.landing import pr_read, pr_unread
from lem.app.tasks import split, worktree
from lem.kernel.errors import Refusal
from lem.model.criteria import digest, reads
from lem.model.criteria.read import sheet_of
from lem.model.landing import green, green_owner, propose_criteria
from lem.model.task import part_carry, parts, queue, split_records
from lem.records.criterion import Criterion, CriterionTest
from lem.records.record import Record
from lem.records.task import Shape
from lem.records.tickets import Ticket
from lem.store import tasks, workspace
from unit.task.spaces import made, read
from unit.task.spaces import workspace as space

if TYPE_CHECKING:
    from pathlib import Path

    from lem.store.places import Workspace

FEATURE = "save-items"
BRANCH = f"feature/{FEATURE}"
SLUGS = ("save-endpoint", "ios-save-button", "android-saved-list")
CRITERIA = """# Save items

## Acceptance criteria

Size: full, because the server and both apps change.

### save-endpoint: the server saves an item and returns it

1. A POST of an item to /items saves it: the item "milk" comes back with an id.

### ios-save-button: the iOS app saves the item it shows

2. The iOS app's Save button saves the item on the screen: "milk" is in /items after a tap.
3. A Save with no network says so, and saves nothing.

### android-saved-list: the Android app lists the saved items (independent)

4. The Android app lists each saved item: "milk" and "bread" are in the list.

### The whole feature

5. An item saved on iOS is in the Android list: "milk" saved on the phone is on the tablet.
"""
SHAPE = Shape(type="feat", why="a new feature", track="full", then="interview")


def approved(where: Workspace, text: str = CRITERIA, flagged: int = 0) -> Path:
    """The feature's criteria file, read by the personas and approved by the owner."""
    path = where.checkout / "criteria.md"
    path.write_text(text, encoding="utf-8")
    sheet = sheet_of(text, path.name)
    found = reads.Found(
        asked=2,
        answered=2,
        families=("opus", "sol"),
        criteria=len(sheet.criteria),
        flagged=flagged,
        digest=digest.of_texts(sheet.size, sheet.criteria),
    )
    persona.noted(where.checkout, FEATURE, ("done", "lem"), found)
    approve.approved(where.checkout, FEATURE, approve.Asked(by="owner", path=path))
    return path


def feature(tmp_path: Path, flagged: int = 0) -> tuple[Workspace, Path]:
    """A real repository with origin, and the feature shaping, read and approved in it."""
    repo = RealRepo.init(tmp_path / "repo", {"README.md": b"one\n"})
    where = space(repo.checkout)
    made(where, FEATURE, ask="save items, in parts", status="shaping", shape=SHAPE)
    return where, approved(where, flagged=flagged)


def refused(where: Workspace, path: Path) -> Refusal:
    with pytest.raises(Refusal) as error:
        split.split(where.checkout, FEATURE, path)
    return error.value


def criterion(**fields: object) -> Criterion:
    return msgspec.convert({"number": 1, "text": "A rule.", **fields}, Criterion)


# The form of the criteria, and the marks of a task with no parts


def test_a_task_with_no_parts_writes_no_part_and_keeps_its_marks() -> None:
    # the marks of this set before `Criterion.part` was added (Lem 0.4.2)
    old = (
        Criterion(
            number=1,
            text="A CSV export holds the gift note.",
            case=("1. Order 1042.", "2. Its row."),
        ),
        Criterion(
            number=2,
            text="The board shows it.",
            tests=(CriterionTest(command="pytest t.py", files=("t.py",)),),
        ),
    )
    assert digest.of_tests("full", old) == "a67d6f74e25f"
    assert digest.of_texts("full", old) == "ea2913115ade"
    assert b"part" not in msgspec.json.encode(old)


def test_a_record_of_0_4_2_reads_and_is_written_with_each_of_its_keys() -> None:
    criteria = {"number": 1, "text": "A rule.", "case": ["1. Step."]}
    approval = {
        "number": 1,
        "at": "2026-11-27T10:00:00Z",
        "by": "owner",
        "size": "full",
        "why": "a reason",
        "digest": "0123456789ab",
        "criteria": [criteria],
    }
    task = {
        "slug": "gift-note",
        "ask": "the gift note",
        "opened": "2026-11-27T09:00:00Z",
        "status": "shaping",
        "since": "2026-11-27T09:00:00Z",
        "criteria": {"size": "full", "criteria": [criteria], "approvals": [approval]},
    }
    old = {"schema": 1, "release": "0.4.2", "revision": 1, "task": task, "journal": []}
    found = msgspec.json.decode(msgspec.json.encode(old), type=Record)
    assert found.task.criteria.criteria[0].part is None
    again = msgspec.json.decode(msgspec.json.encode(found))
    assert again["task"]["criteria"] == task["criteria"]


def test_the_headings_give_each_criterion_its_part_and_none_for_the_whole_feature() -> (
    None
):
    sheet = sheet_of(CRITERIA, "criteria.md")
    assert [one.part for one in sheet.criteria] == [
        "save-endpoint: the server saves an item and returns it",
        "ios-save-button: the iOS app saves the item it shows",
        "ios-save-button: the iOS app saves the item it shows",
        "android-saved-list: the Android app lists the saved items (independent)",
        None,
    ]


@pytest.mark.parametrize(
    ("text", "said"),
    [
        (
            "1. A rule.\n\n### a-part: it does a thing\n\n2. Another.\n",
            "criterion 1 is under no heading",
        ),
        (
            "### a-part: one\n\n### b-part: two\n\n1. A rule.\n",
            "the heading 'a-part: one' has no criterion under it",
        ),
        (
            "### a-part: one\n\n1. A rule.\n\n### The whole feature\n",
            "the heading 'The whole feature' has no criterion under it",
        ),
        (
            "### a-part: one\n\n1. A rule.\n\n### a-part:  one\n\n2. Another.\n",
            "the heading 'a-part: one' comes twice",
        ),
    ],
)
def test_criteria_with_headings_put_each_criterion_under_one(
    text: str, said: str
) -> None:
    section = f"## Acceptance criteria\n\nSize: full, because of a reason.\n\n{text}"
    with pytest.raises(Refusal) as error:
        sheet_of(section, "criteria.md")
    assert error.value.code == "criteria-form"
    assert error.value.why.endswith(said)


# The parts and their order


def test_each_part_waits_for_the_one_before_it_and_an_independent_one_for_none() -> (
    None
):
    found = parts.parts_of(FEATURE, sheet_of(CRITERIA, "criteria.md").criteria)
    assert [(one.slug, one.after, len(one.criteria)) for one in found] == [
        ("save-endpoint", (), 1),
        ("ios-save-button", ("save-endpoint",), 2),
        ("android-saved-list", (), 1),
    ]
    assert found[1].ask == "the iOS app saves the item it shows"
    assert found[2].ask == "the Android app lists the saved items"


@pytest.mark.parametrize(
    ("headings", "said"),
    [
        ((None,), "have no part's heading"),
        (("a-part: one",), "have no criterion under ### The whole feature"),
        (("A Part: one", None), "the heading 'A Part: one' names no part"),
        (("a-part", None), "the heading 'a-part' names no part"),
        ((f"{FEATURE}: itself", None), f"names the feature {FEATURE} itself"),
        (("a-part: one", "a-part: two", None), "two headings name the part a-part"),
    ],
)
def test_a_split_needs_parts_of_their_own_and_the_whole_feature(
    headings: tuple[str | None, ...], said: str
) -> None:
    criteria = tuple(
        criterion(number=number, part=part)
        for number, part in enumerate(headings, start=1)
    )
    with pytest.raises(Refusal) as error:
        parts.parts_of(FEATURE, criteria)
    assert error.value.code == "split"
    assert said in error.value.why


# The copy of the criteria


@pytest.mark.parametrize(
    ("was", "now", "said"),
    [
        (
            'the item "milk" comes back',
            'the item "bread" comes back',
            "criterion 1 says",
        ),
        (
            "### ios-save-button: the iOS app saves the item it shows",
            "### ios-save-button: the iOS app saves the item it has",
            "criterion 2 is under",
        ),
        (
            "Size: full, because",
            "Size: small, because",
            "a task on the fast track has one criterion",
        ),
    ],
)
def test_a_file_that_is_not_the_approval_word_for_word_is_refused(
    tmp_path: Path, was: str, now: str, said: str
) -> None:
    where, path = feature(tmp_path)
    path.write_text(CRITERIA.replace(was, now), encoding="utf-8")
    found = refused(where, path)
    assert found.code in {"split-differs", "criteria-form"}
    assert said in found.why
    assert read(where, FEATURE).task.status == "shaping"
    assert not (where.lem / "worktrees" / FEATURE).exists()


def test_a_feature_with_no_read_of_its_criteria_is_not_split(tmp_path: Path) -> None:
    repo = RealRepo.init(tmp_path / "repo", {"README.md": b"one\n"})
    where = space(repo.checkout)
    made(where, FEATURE, ask="save items", status="shaping", shape=SHAPE)
    path = where.checkout / "criteria.md"
    path.write_text(CRITERIA, encoding="utf-8")
    approve.approved(where.checkout, FEATURE, approve.Asked(by="owner", path=path))
    assert refused(where, path).code == "no-read"


def test_a_part_carries_the_read_and_the_approval_with_its_own_mark(
    tmp_path: Path,
) -> None:
    where, path = feature(tmp_path)
    split.split(where.checkout, FEATURE, path)
    task = read(where, "ios-save-button").task
    kept = task.criteria
    assert [(one.number, one.part) for one in kept.criteria] == [(1, None), (2, None)]
    assert kept.criteria[0].text.startswith("The iOS app's Save button")
    mark = digest.of_texts("full", kept.criteria)
    approval = kept.approvals[0]
    assert (approval.number, approval.by, approval.digest) == (1, "owner", mark)
    assert approval.at == read(where, FEATURE).task.criteria.approvals[-1].at
    assert (kept.reads[0].digest, kept.reads[0].criteria) == (mark, 5)


def test_green_and_propose_pass_for_a_part_with_no_second_read_or_yes(
    tmp_path: Path,
) -> None:
    where, path = feature(tmp_path)
    split.split(where.checkout, FEATURE, path)
    for slug in SLUGS:
        record = read(where, slug)
        assert propose_criteria.unread(record) is None
        assert propose_criteria.silent(record) is None
        assert pr_unread.unread(record) == ()
        assert green.unread(record) == ()
        assert green_owner.approval(record.task) == ()

    day = read(where, FEATURE).task.criteria.approvals[-1].at.date().isoformat()
    assert pr_read.read_line(read(where, "save-endpoint")) == (
        f"- the criteria were read as part of {FEATURE}'s criteria by 2 of 2 personas "
        "asked, two model families (opus, sol); nobody confused; the owner approved them "
        f"as part of {FEATURE}'s criteria on {day}"
    )


def test_the_feature_reads_counts_are_said_to_be_the_feature_s(tmp_path: Path) -> None:
    where, path = feature(tmp_path, flagged=1)
    split.split(where.checkout, FEATURE, path)
    line = pr_read.read_line(read(where, "save-endpoint"))
    assert f"; 1 of 5 criteria of {FEATURE} flagged;" in line


def test_a_part_with_an_approval_of_its_own_says_it_plainly(tmp_path: Path) -> None:
    where, path = feature(tmp_path)
    split.split(where.checkout, FEATURE, path)
    record = read(where, "save-endpoint")
    # a part `lem task open --part-of` opened has its own lines, none carried
    own = replace(record, journal=())
    day = record.task.criteria.approvals[0].at.date().isoformat()
    assert pr_read.read_line(own) == (
        "- the criteria were read by 2 of 2 personas asked, two model families (opus, "
        f"sol); nobody confused; the owner approved them on {day}"
    )


def test_a_read_of_other_texts_than_the_approved_ones_keeps_its_own_mark(
    tmp_path: Path,
) -> None:
    where, _ = feature(tmp_path)
    task = read(where, FEATURE).task
    stale = replace(task.criteria.reads[0], digest="0123456789ab")
    task = replace(task, criteria=replace(task.criteria, reads=(stale,)))
    approval = task.criteria.approvals[-1]
    kept = part_carry.carried(task, approval, approval.criteria[:1])
    part = Record(
        release="0.4.2", task=replace(task, slug="save-endpoint", criteria=kept)
    )
    assert kept.reads[0].digest == "0123456789ab"
    said = (
        "- the criteria changed after the personas' read, by the owner's approval 1, and "
        "the change was not read"
    )
    assert pr_unread.unread(part) == (said,)


# The records of the split


def test_a_split_queues_the_feature_after_its_parts_on_its_own_branch(
    tmp_path: Path,
) -> None:
    where, path = feature(tmp_path)
    done = split.split(where.checkout, FEATURE, path)
    assert (done.branch, done.starts) == (
        BRANCH,
        ("save-endpoint", "android-saved-list"),
    )
    assert [(one.slug, one.status, one.after, one.made) for one in done.parts] == [
        ("save-endpoint", "shaping", (), True),
        ("ios-save-button", "queued", ("save-endpoint",), True),
        ("android-saved-list", "shaping", (), True),
    ]
    task = read(where, FEATURE).task
    assert (task.status, task.after, task.branch) == ("queued", SLUGS, BRANCH)
    assert task.shape is not None
    assert task.shape.then == "lead"
    assert queue.started_in(task) == "building"
    for slug in SLUGS:
        part = read(where, slug).task
        assert (part.part_of, part.shape and part.shape.then) == (FEATURE, "lead")
    origin = run_git(where.checkout, "ls-remote", "origin", BRANCH)
    assert origin.endswith(f"refs/heads/{BRANCH}")
    tree = where.lem / "worktrees" / FEATURE
    assert run_git(tree, "rev-parse", "--abbrev-ref", "HEAD") == BRANCH


def test_only_the_feature_holds_its_ticket_after_the_split(tmp_path: Path) -> None:
    where, path = feature(tmp_path)
    ticket = Ticket(tracker="github", id="#42", repo="acme/shop")
    tasks.update(
        where.state,
        FEATURE,
        lambda found: replace(found, task=replace(found.task, ticket=ticket)),
        read(where, FEATURE).revision,
    )
    split.split(where.checkout, FEATURE, path)
    assert read(where, FEATURE).task.ticket == ticket
    assert [read(where, slug).task.ticket for slug in SLUGS] == [None, None, None]


def test_a_split_run_twice_makes_each_part_once(tmp_path: Path) -> None:
    where, path = feature(tmp_path)
    split.split(where.checkout, FEATURE, path)
    revisions = {slug: read(where, slug).revision for slug in SLUGS}
    again = split.split(where.checkout, FEATURE, path)
    assert [one.made for one in again.parts] == [False, False, False]
    assert {slug: read(where, slug).revision for slug in SLUGS} == revisions
    task = read(where, FEATURE).task
    assert (task.status, task.after) == ("queued", SLUGS)


def test_an_approval_of_the_same_texts_again_lets_the_split_run_again(
    tmp_path: Path,
) -> None:
    where, path = feature(tmp_path)
    split.split(where.checkout, FEATURE, path)
    approve.approved(where.checkout, FEATURE, approve.Asked(by="owner", path=path))
    again = split.split(where.checkout, FEATURE, path)
    assert [one.made for one in again.parts] == [False, False, False]


def test_a_split_cut_off_after_one_part_makes_only_the_missing_ones(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    where, path = feature(tmp_path)
    published = workspace.published
    count = 0

    def cut(state: Path, record: Record) -> Record:
        nonlocal count
        count += 1
        if count > 1:
            raise KeyboardInterrupt
        return published(state, record)

    monkeypatch.setattr(workspace, "published", cut)
    with pytest.raises(KeyboardInterrupt):
        split.split(where.checkout, FEATURE, path)
    monkeypatch.setattr(workspace, "published", published)
    task = read(where, FEATURE).task
    assert (task.status, task.after) == ("queued", SLUGS)
    # the feature waits for parts with no record yet, which hold it queued
    assert queue.start_refusal(task, tasks.every(where.state)) is not None
    again = split.split(where.checkout, FEATURE, path)
    assert [one.made for one in again.parts] == [False, True, True]


def test_a_part_slug_another_task_holds_is_refused_before_any_write(
    tmp_path: Path,
) -> None:
    where, path = feature(tmp_path)
    made(where, "ios-save-button", ask="something else", status="shaping")
    found = refused(where, path)
    assert found.code == "task-exists"
    assert read(where, FEATURE).task.status == "shaping"
    assert not (where.state / "tasks" / "save-endpoint").exists()
    assert not (where.lem / "worktrees" / FEATURE).exists()


@pytest.mark.parametrize(
    ("fields", "said"),
    [
        ({"status": "building"}, f"{FEATURE} is building, and a split takes a feature"),
        (
            {"part_of": "other"},
            f"{FEATURE} is a part of other, and a part has no parts",
        ),
        ({"shape": None}, f"{FEATURE} has no read of its request yet"),
    ],
)
def test_only_a_feature_that_is_shaping_and_no_part_is_split(
    fields: dict[str, object], said: str
) -> None:
    task = record(FEATURE, **{"status": "shaping", "shape": SHAPE, **fields}).task
    found = split_records.splittable(task, SLUGS)
    assert found is not None
    assert found.why.startswith(said)


@pytest.mark.parametrize(
    ("was", "now"),
    [
        ('"milk" is in /items after a tap', '"bread" is in /items after a tap'),
        ("### ios-save-button: the iOS", "### ios-save: the iOS"),
    ],
)
def test_a_split_again_after_another_approval_is_refused_and_changes_nothing(
    tmp_path: Path, was: str, now: str
) -> None:
    where, path = feature(tmp_path)
    split.split(where.checkout, FEATURE, path)
    before = {slug: read(where, slug) for slug in (FEATURE, *SLUGS)}
    path.write_text(CRITERIA.replace(was, now), encoding="utf-8")
    approve.approved(where.checkout, FEATURE, approve.Asked(by="owner", path=path))
    before[FEATURE] = read(where, FEATURE)
    found = refused(where, path)
    assert found.code == "split-moved"
    assert found.why.startswith(
        f"ios-save-button took the criteria of {FEATURE} at the split, and the owner's "
        "newest approval of them, 2, words them otherwise or has no such part"
    )
    assert "lem criteria change PART --file FILE" in found.fix
    assert {slug: read(where, slug) for slug in before} == before
    assert not (where.state / "tasks" / "ios-save").exists()


def test_a_feature_whose_worktree_is_on_another_branch_is_refused_with_the_way_on(
    tmp_path: Path,
) -> None:
    where, path = feature(tmp_path)
    worktree.worktree(
        where.checkout, FEATURE, path_only=False, asked=(f"feat/{FEATURE}", None)
    )
    tree = where.lem / "worktrees" / FEATURE
    found = refused(where, path)
    assert found.code == "split-worktree"
    assert found.why.startswith(f"the worktree of {FEATURE}, {tree}, is on feat/")
    command = f"git -C {tree} switch --create {BRANCH} origin/main"
    assert command in found.fix
    assert read(where, FEATURE).task.status == "shaping"
    run_git(tree, "switch", "--quiet", "--create", BRANCH, "origin/main")
    done = split.split(where.checkout, FEATURE, path)
    assert (done.branch, read(where, FEATURE).task.branch) == (BRANCH, BRANCH)
    assert run_git(where.checkout, "ls-remote", "origin", BRANCH).endswith(BRANCH)
