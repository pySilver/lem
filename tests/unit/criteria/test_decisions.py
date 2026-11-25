"""A task's decisions: each level of the ladder logs what it settles, a criterion's change is
checked against the criteria as they stand, the breaker stops a task only with its document in
every part, and a task that ended takes no write."""

import dataclasses
import threading
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.harness import FakeHarness
from fakes.ports import fake_ports
from lem.app.criteria import approve
from lem.app.decisions import breaker, criterion, listing, log, stopping
from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.model.decisions import chart, document
from lem.model.decisions.criterion import Asked
from lem.model.decisions.log import Logged
from lem.ports.harness import Missing
from lem.records.holds import BreakerHold, Parked
from lem.records.journal.task import DecisionNoted
from lem.store import places, tasks
from unit.criteria import world

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from lem.app.wiring import Ports
    from lem.records.decisions import Breaker, Taken
    from lem.records.holds import Hold
    from lem.records.task import Status

STORY = (
    "1. Order 1042 has two notes.\n2. The export keeps one.",
    "derived",
    "An order has one cell for its note.",
)
CHART = (
    'flowchart TD\n  A["An order with two notes"] --> B{"One cell?"}\n'
    '  B -->|"yes"| C["One note is lost"]'
)
TEMPLATE = paths.root() / "skills/lem/templates/breaker.md"
DOCUMENT = """# The export would write over the archive of orders

## Today and after

**Today**:

1. Order 1042 is exported.
2. The archive keeps it.

**After**:

1. Order 1042 is exported.
2. The archive is gone.

## The case that broke

1. The export writes to /srv/archive.
2. The old file goes.

```mermaid
flowchart TD
  A["Export"] --> B["Archive gone"]
```

## The root cause

The plan named the archive's folder as the export's.

## The options

| | A: keep | B: move |
| --- | --- | --- |
| Sees | old | new |

## The recommendation

A: keep.

## The assumptions

- The archive has no copy.
"""


LEAD = Logged(
    what="Two notes on one order", chose="both", why="nobody loses one", by="lead"
)


def lead(**given: object) -> Logged:
    return replace(LEAD, **given)


def refused(call: Callable[..., object], *args: object) -> Refusal:
    with pytest.raises(Refusal) as caught:
        call(*args)
    return caught.value


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    found = world.workspace(tmp_path / "shop")
    world.task(found, status="building")
    return found


@pytest.fixture
def ports(checkout: Path) -> Ports:
    git = ModelGit(checkout=checkout)
    return fake_ports(git, LocalForge(remote=git))


def logs(
    ports: Ports, checkout: Path, asked: Logged, chart_file: str | None = None
) -> Taken:
    return log.logged(ports, checkout, world.SLUG, asked, chart_file)


def test_a_decision_is_written_with_its_number_and_a_line_of_the_journal(
    checkout: Path, ports: Ports
) -> None:
    first = logs(ports, checkout, lead(undo="a revert of one commit"))
    second = logs(ports, checkout, lead(what="  The   column's name ", chose="note"))
    record = world.read(checkout)
    assert (first.id, second.id) == (1, 2)
    assert second.what == "The column's name"
    assert [type(entry) for entry in record.journal[-2:]] == [
        DecisionNoted,
        DecisionNoted,
    ]


def test_the_personas_settle_with_two_votes_or_more_all_for_the_option_taken(
    checkout: Path, ports: Ports
) -> None:
    one = lead(by="personas", votes=("Ania, opus=both",), said="Ania picked both")
    assert refused(logs, ports, checkout, one).code == "not-settled"
    split = lead(by="personas", votes=("Ania, opus=both", "Olek, opus=one"))
    assert "Olek, opus voted otherwise" in refused(logs, ports, checkout, split).why
    clear = lead(by="personas", votes=("Ania, opus=both", "Olek, opus=both"))
    assert logs(ports, checkout, clear).votes == (
        ("Ania, opus", "both"),
        ("Olek, opus", "both"),
    )
    assert world.read(checkout).task.decisions[-1].id == 1
    bad = lead(by="personas", votes=("Ania both",))
    assert refused(logs, ports, checkout, bad).code == "decision-form"


def test_each_level_logs_with_its_own_name_and_what_each_level_answered(
    checkout: Path, ports: Ports
) -> None:
    gate = logs(
        ports, checkout, lead(by="gate", levels=("gate=a ruling of 2026-11-16",))
    )
    assert (gate.by, gate.levels) == ("gate", (("gate", "a ruling of 2026-11-16"),))
    told = lead(
        by="dialectic", story=STORY, levels=("personas=split", "dialectic=both")
    )
    assert logs(ports, checkout, told).story is not None
    unsettled = lead(unsettled=True, story=STORY)
    assert logs(ports, checkout, unsettled).unsettled
    assert refused(logs, ports, checkout, lead(by="gate", unsettled=True)).code == (
        "decision-form"
    )


def test_an_important_log_without_its_story_is_refused(
    checkout: Path, ports: Ports
) -> None:
    for given in ({"by": "dialectic"}, {"unsettled": True}):
        assert "carries its story" in refused(logs, ports, checkout, lead(**given)).why
    one_step = lead(by="dialectic", story=("1. one step", "derived", "a cause"))
    assert "numbered steps" in refused(logs, ports, checkout, one_step).why
    unknown = lead(by="dialectic", story=(STORY[0], "guessed", STORY[2]))
    assert refused(logs, ports, checkout, unknown).code == "decision-form"


def test_a_plain_log_needs_none_and_takes_all_three_or_none(
    checkout: Path, ports: Ports
) -> None:
    assert logs(ports, checkout, lead()).story is None
    assert refused(logs, ports, checkout, lead(story=(STORY[0], None, None))).code == (
        "decision-form"
    )
    kept = logs(ports, checkout, lead(story=STORY)).story
    assert kept is not None
    assert kept.case == ("1. Order 1042 has two notes.", "2. The export keeps one.")


def test_the_experts_write_which_of_them_answer_here(
    checkout: Path, ports: Ports
) -> None:
    told = lead(by="experts", story=STORY)
    assert logs(ports, checkout, told).advisers == ("fable", "astra")
    harness = FakeHarness(missing={"codex": Missing(error="missing")})
    one = dataclasses.replace(ports, harness=harness)
    assert logs(one, checkout, told).advisers == ("fable",)
    none = dataclasses.replace(
        ports,
        harness=FakeHarness(
            missing={
                "claude": Missing(error="missing"),
                "codex": Missing(error="missing"),
            }
        ),
    )
    assert refused(logs, none, checkout, told).code == "no-expert"


def test_a_chart_keeps_its_lines_without_its_fence(
    checkout: Path, ports: Ports
) -> None:
    path = checkout / "chart.md"
    path.write_text(f"```mermaid\n{CHART}\n```\n", encoding="utf-8")
    assert logs(ports, checkout, lead(), str(path)).chart == CHART


def test_charts_that_are_refused() -> None:
    for text, said in (
        ("", "holds no chart"),
        ("flowchart TD\n" + "  A --> B\n" * 600, "a record keeps"),
        ("chart TD\n  A --> B", "no chart type"),
        ('flowchart TD\n  A[two notes] --> B["x"]', "out of double quotes"),
        ('flowchart TD\n  A["x"] -->|yes| B["y"]', "out of double quotes"),
        ("```python\nx = 1\n```", "```python block"),
    ):
        with pytest.raises(Refusal) as caught:
            chart.chart_of(text, "c.md")
        assert said in caught.value.why, text
    assert chart.chart_of("sequenceDiagram\n  A->>B: two notes", "c.md").startswith(
        "seq"
    )


def test_his_help_on_a_breaker_is_the_owners_and_settles_it_once(
    checkout: Path, ports: Ports
) -> None:
    tripped(ports, checkout)
    assert isinstance(world.read(checkout).task.hold, BreakerHold)
    assert refused(logs, ports, checkout, lead(breaker=1)).code == "decision-form"
    helped = logs(
        ports, checkout, lead(by="owner", breaker=1, words="keep both, said he")
    )
    task = world.read(checkout).task
    assert (helped.breaker, task.hold) == (1, None)
    assert [one.state for one in listing.listed(checkout, world.SLUG)] == [
        "helped",
        "taken",
    ]
    assert (
        refused(logs, ports, checkout, lead(by="owner", breaker=1)).code == "no-breaker"
    )


def test_a_parked_task_takes_his_help_after_its_resume(
    checkout: Path, ports: Ports
) -> None:
    tripped(ports, checkout)
    held(checkout, Parked(since=world.EARLY))
    assert refused(logs, ports, checkout, lead(by="owner", breaker=1)).code == "parked"
    waiting = listing.waiting(checkout, None)
    assert ([one.task for one in waiting.parked], waiting.waiting) == ([world.SLUG], ())


def held(checkout: Path, hold: Hold | None, status: Status | None = None) -> None:
    state = checkout / places.STATE
    record = tasks.read(state, world.SLUG)
    tasks.update(
        state,
        world.SLUG,
        lambda found: replace(
            found,
            task=replace(found.task, hold=hold, status=status or found.task.status),
        ),
        record.revision,
    )


def tripped(ports: Ports, checkout: Path, text: str = DOCUMENT) -> Breaker:
    folder = places.task_folder(checkout / places.STATE, world.SLUG)
    (folder / "breaker.md").write_text(text, encoding="utf-8")
    (folder / "handoff.md").write_text("## Settled\n\n- the export\n", encoding="utf-8")
    asked = stopping.Asked(cause="irreversible", kind="data")
    return breaker.tripped(ports, checkout, world.SLUG, asked)


def test_the_breaker_keeps_its_document_under_its_number_and_holds_the_task(
    checkout: Path, ports: Ports
) -> None:
    logs(ports, checkout, lead())
    made = tripped(ports, checkout)
    folder = places.task_folder(checkout / places.STATE, world.SLUG)
    record = world.read(checkout)
    assert (made.id, made.document, made.what) == (
        2,
        "breaker-2.md",
        "The export would write over the archive of orders",
    )
    assert (folder / "breaker-2.md").read_text() == DOCUMENT
    assert not (folder / "breaker.md").exists()
    assert record.task.hold == BreakerHold(number=2, since=made.at)
    assert "breaker 2 waits for the owner" in str(record.journal[-2])
    assert refused(tripped, ports, checkout).code == "breaker-waits"
    waiting = listing.waiting(checkout, world.SLUG)
    assert [one.breaker.id for one in waiting.waiting] == [2]


def test_the_breaker_needs_its_document_the_handoff_and_the_work_committed(
    checkout: Path, ports: Ports
) -> None:
    folder = places.task_folder(checkout / places.STATE, world.SLUG)
    asked = stopping.Asked(cause="criteria")
    assert (
        refused(breaker.tripped, ports, checkout, world.SLUG, asked).code
        == "no-document"
    )
    (folder / "breaker.md").write_text(DOCUMENT, encoding="utf-8")
    assert (
        refused(breaker.tripped, ports, checkout, world.SLUG, asked).code
        == "no-handoff"
    )
    (folder / "handoff.md").write_text("## Settled\n", encoding="utf-8")
    worktree = world.worktree(checkout)
    dirty = dataclasses.replace(ports, git=Dirty())
    assert (
        refused(breaker.tripped, dirty, checkout, world.SLUG, asked).code
        == "not-committed"
    )
    assert worktree.is_dir()
    wrong = stopping.Asked(cause="criteria", kind="money")
    assert (
        refused(breaker.tripped, ports, checkout, world.SLUG, wrong).code
        == "breaker-cause"
    )
    other = checkout / "breaker.md"
    other.write_text(DOCUMENT, encoding="utf-8")
    outside = stopping.Asked(cause="criteria", document=str(other))
    assert refused(breaker.tripped, ports, checkout, world.SLUG, outside).code == (
        "document-place"
    )


class Dirty:
    """A git whose every worktree has work no commit holds."""

    @staticmethod
    def clean(where: Path) -> bool:
        return not where


def test_no_breaker_stops_a_landing(checkout: Path, ports: Ports) -> None:
    held(checkout, None, "landing")
    assert refused(tripped, ports, checkout).code == "with-landing"


def test_a_document_without_a_part_names_each_it_lacks() -> None:
    lacking = DOCUMENT.split("## The options", maxsplit=1)[0]
    with pytest.raises(Refusal) as caught:
        document.title_of(lacking, "breaker.md")
    why = caught.value.why
    assert "## The options" in why
    assert "## The assumptions" in why
    assert "## The case" not in why
    with pytest.raises(Refusal) as untitled:
        document.title_of(DOCUMENT.replace("# The export", "The export", 1), "b.md")
    assert "a first line #" in untitled.value.why


def test_a_parts_heading_inside_a_code_fence_is_a_line_of_its_part() -> None:
    fenced = DOCUMENT.replace(
        "## The root cause\n", "## The root cause\n\n```\n## The options\n```\n"
    ).split("## The options\n\n|")[0]
    with pytest.raises(Refusal) as caught:
        document.title_of(fenced, "breaker.md")
    assert "## The options" in caught.value.why


def test_a_code_block_that_never_closes_is_refused_with_its_line() -> None:
    with pytest.raises(Refusal) as caught:
        document.title_of(DOCUMENT + "```\nopen\n", "breaker.md")
    assert caught.value.code == "open-fence"
    number = len(DOCUMENT.splitlines()) + 1
    assert f"line {number} opens" in caught.value.why


def test_the_template_has_every_part() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    assert document.title_of(text, "breaker.md").startswith("WHAT STOPPED")


def test_a_criterion_change_is_checked_against_the_criteria_as_they_stand(
    checkout: Path, ports: Ports
) -> None:
    changed = Asked(
        how="changed", number=2, was="An order", now="x", why="w", by="lead"
    )
    assert (
        refused(criterion.recorded, checkout, world.SLUG, changed).code
        == "not-approved"
    )
    path = world.sheet(checkout, world.FULL)
    approve.approved(checkout, world.SLUG, approve.Asked(by="owner", path=path))
    assert refused(criterion.recorded, checkout, world.SLUG, changed).code == (
        "criterion-change"
    )
    was = 'An order with no gift note has an empty cell, not the word "None".'
    made = criterion.recorded(
        checkout,
        world.SLUG,
        replace(changed, was=was, now="An order with no note is empty."),
    )
    assert made.criteria[1] == "An order with no note is empty."
    added = Asked(how="added", number=3, now="A third, 7.", why="w", decision=9)
    assert (
        refused(criterion.recorded, checkout, world.SLUG, added).code == "no-decision"
    )
    taken = logs(ports, checkout, lead())
    criterion.recorded(checkout, world.SLUG, replace(added, decision=taken.id))
    found = listing.changes_of(checkout, world.SLUG)
    assert found.expected is not None
    assert len(found.expected) == 3
    assert [one.change.criterion for one in found.history] == [2, 3]


def test_a_criterion_change_names_its_texts_and_who(checkout: Path) -> None:
    path = world.sheet(checkout, world.FULL)
    approve.approved(checkout, world.SLUG, approve.Asked(by="owner", path=path))
    for asked in (
        Asked(how="changed", number=1, now="x", why="w", by="lead"),
        Asked(how="removed", number=1, was="x", now="y", why="w", by="lead"),
        Asked(how="removed", number=1, was="x", why="w"),
        Asked(how="removed", number=1, was="x", why="w", by="personas"),
        Asked(how="removed", number=1, was="x", why=" ", by="lead"),
        Asked(how="added", number=9, now="x", why="w", by="lead"),
    ):
        assert refused(criterion.recorded, checkout, world.SLUG, asked).code in {
            "criterion-form",
            "criterion-change",
        }, asked


def test_a_dropped_or_landed_task_takes_no_new_decision_breaker_or_help(
    checkout: Path, ports: Ports
) -> None:
    held(checkout, None, "dropped")
    assert refused(logs, ports, checkout, lead()).code == "ended"
    assert refused(tripped, ports, checkout).code == "ended"
    ended = listing.waiting(checkout, world.SLUG).ended
    assert [(one.task, one.status) for one in ended] == [(world.SLUG, "dropped")]
    assert listing.waiting(checkout, None).ended == ()


def test_two_writes_at_once_each_take_a_number_of_their_own(
    checkout: Path, ports: Ports
) -> None:
    taken: list[int] = []
    threads = [
        threading.Thread(target=lambda: taken.append(logs(ports, checkout, lead()).id))
        for _ in range(4)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(taken) == [1, 2, 3, 4]
    assert [one.id for one in world.read(checkout).task.decisions] == [1, 2, 3, 4]


def test_a_decision_whose_words_hold_a_line_separator_is_kept_as_one_line(
    checkout: Path, ports: Ports
) -> None:
    made = logs(ports, checkout, lead(why="one\u2028two"))
    assert made.why == "one two"
