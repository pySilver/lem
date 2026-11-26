"""`propose`: what it pushes and adopts, each gate it refuses with its code, the notes' lines it
asks a bar call of, and the pull request's text the owner reads, in the words of today's text
(`main:tests/unit/test_land_text.py`, `test_land.py`)."""

from typing import TYPE_CHECKING

import pytest
from inline_snapshot import snapshot
from msgspec.structs import replace

from lem.app.landing import (
    pr_decisions,
    pr_outside,
    pr_read,
    pr_talk,
    pr_text,
    pull_identity,
)
from lem.kernel.errors import Refusal
from lem.model.criteria import approve, skip
from lem.model.criteria.read import Sheet
from lem.model.landing import (
    items,
    propose,
    propose_careful,
    propose_filed,
    propose_jev,
    propose_lines,
    propose_notes,
)
from lem.model.landing.propose_facts import Facts, Filing
from lem.model.landing.world import Due, Held, Rules
from lem.model.task import span_forms, spans
from lem.records.holds import OwnerHold
from lem.records.landing.checks import CriterionCheck, Edited
from lem.records.landing.review import Counts, Filed, Finding
from lem.records.landing.start import Polished
from lem.records.task import Shape
from lem.records.tickets import Ticket
from lem.records.work import Investigation, Plan, StandIn, Talk
from unit.landing.proposals import (
    FACTS,
    FULL_NOTES,
    LATER,
    QUIET,
    approval,
    breaker,
    changed,
    full,
    picked,
    read,
    small,
    span,
    taken,
    with_landing,
)
from unit.landing.worlds import (
    CHECKED,
    MOMENT,
    OPENED,
    OTHER,
    PREPARED,
    REVIEWED,
    SEEN,
    TIP,
    task,
    world,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime
    from pathlib import Path

    from lem.records.record import Record

SMALL_NOTES = Facts(notes="none\n")


def code_of(found: object) -> str:
    """The code of a refusal; a case fails on anything else."""
    assert isinstance(found, Refusal), found
    return found.code


def refusal_words(found: object) -> tuple[str, str, str]:
    """The refusal as it is printed for the owner."""
    assert isinstance(found, Refusal), found
    return found.code, found.why, found.fix


def decided(
    record: Record, facts: Facts = FACTS, **seen: object
) -> propose.Proposal | Refusal:
    """What `propose` decides for `record` in the world with `seen` over it."""
    return propose.decide(record, world(**seen), facts, "feat: the word")


def text_of(record: Record, facts: Facts = FACTS) -> str:
    """The text of a proposal of `record`, whether or not its gates would let it go."""
    careful = propose_careful.why(record, facts)
    notes = propose_notes.parsed(facts.notes)
    assert not isinstance(notes, Refusal)
    proposal = propose.Proposal(
        push=False,
        proposed=propose.made(record, world(), careful),
        careful=careful,
        notes=notes,
    )
    return pr_text.body(record, proposal, facts)


# ---- what it pushes and adopts ----


def test_propose_pushes_a_tip_origin_lacks_and_adopts_only_a_request_lem_pushed() -> (
    None
):
    record = task(**PREPARED)
    made = decided(record, SMALL_NOTES)
    assert not isinstance(made, Refusal)
    assert (made.push, made.adopt, made.proposed.green, made.proposed.who_acts) == (
        True,
        None,
        True,
        "merger",
    )
    pushed = task(**{**PREPARED, "pushed": TIP})
    cut = decided(pushed, SMALL_NOTES, remote=TIP, candidates=(SEEN,))
    assert not isinstance(cut, Refusal)
    assert (cut.push, cut.adopt) == (False, SEEN)
    assert code_of(decided(record, SMALL_NOTES, remote=TIP, candidates=(SEEN,))) == (
        "foreign-pull"
    )
    two = (SEEN, replace(SEEN, number=2, head=OTHER))
    assert code_of(decided(pushed, SMALL_NOTES, candidates=two)) == "foreign-pull"
    guarded = Rules(base="main", commands=("true",), protected=("docs/fix-the-login",))
    assert code_of(decided(record, SMALL_NOTES, rules=guarded)) == "protected"
    owner = decided(record, SMALL_NOTES, rules=Rules(base="main", land="owner"))
    assert not isinstance(owner, Refusal)
    assert owner.proposed.who_acts == "owner"


def test_a_new_round_edits_the_request_on_record_and_a_closed_one_is_refused() -> None:
    record = task(**{**PREPARED, "pushed": OTHER})
    again = decided(record, SMALL_NOTES, pull=replace(SEEN, head=OTHER))
    assert not isinstance(again, Refusal)
    assert again.adopt is not None
    assert again.adopt.number == SEEN.number
    merged = decided(record, SMALL_NOTES, pull=replace(SEEN, state="merged"))
    assert refusal_words(merged) == snapshot(
        (
            "closed",
            "the pull request https://github.com/o/p/pull/1 is merged",
            "lem land merged fix-the-login finishes the task, and the branch keeps its commits",
        )
    )
    closed = decided(record, SMALL_NOTES, pull=replace(SEEN, state="closed"))
    assert refusal_words(closed) == snapshot(
        (
            "closed",
            "the pull request https://github.com/o/p/pull/1 is closed",
            "lem land merged fix-the-login writes it dropped, and the branch keeps its commits",
        )
    )


def test_a_careful_request_is_not_green_on_the_fast_track_and_the_owner_merges_it() -> (
    None
):
    shape = Shape(type="docs", why="w", track="small", careful=("money",))
    notes = Facts(notes="none\n\n## Migration\n\nnone\n")
    full_set = (replace(REVIEWED, kind="full"),)
    made = decided(with_landing(small(shape=shape), reviews=full_set), notes)
    assert not isinstance(made, Refusal)
    assert made.proposed.who_acts == "owner"
    assert made.proposed.careful
    assert made.careful == ("money",)


# ---- the gates of the build ----


def test_the_task_own_item_on_its_branch_is_refused() -> None:
    record = small(backlog_item="docs/backlog/the-item.md")
    held = Facts(notes="none\n", in_tip=frozenset(("docs/backlog/the-item.md",)))
    assert refusal_words(decided(record, held)) == snapshot(
        (
            "own-item",
            "fix-the-login was started from the backlog item docs/backlog/the-item.md (its ask is that path), and the branch still holds it: the task does that item's work, so its branch removes it",
            "a builder removes it in the task's worktree in a commit of its own (git rm -q -- docs/backlog/the-item.md, then a commit in the project's message form), then lem land checks fix-the-login and this step run again; the review that read the change still covers it",
        )
    )
    assert not isinstance(decided(record, SMALL_NOTES), Refusal)


def test_a_plan_that_called_for_a_talk_with_none_on_record_is_refused() -> None:
    careful = Facts(
        notes=FULL_NOTES.replace("## Not done", "## Migration\n\nnone\n\n## Not done")
    )
    assert code_of(
        decided(full(plan=Plan(path="p.md", careful="a charge")), careful)
    ) == ("plan-talk")
    large = full(plan=Plan(path="p.md", tasks=4))
    assert refusal_words(decided(large)) == snapshot(
        (
            "plan-talk",
            "the plan has 4 tasks, more than three, so its defender and the reviewer talk its plan through in the plan talk's companion before any code (stages/talk.md), and fix-the-login has no plan talk on record",
            "the task goes back to its build as planned, with needs a session: the plan has 4 tasks, more than three; its lead holds the talk, and its defender records it with lem task talked fix-the-login",
        )
    )
    talk = Talk(
        reviewer="codex",
        turns=6,
        questions=3,
        settled=2,
        open=1,
        repaired=1,
        design=1,
        unargued=0,
        root=1,
        layer=0,
        shared=0,
        at=MOMENT,
    )
    assert not isinstance(
        decided(replace(large, task=replace(large.task, talk=talk))), Refusal
    )
    assert not isinstance(decided(full(plan=Plan(path="p.md", tasks=3))), Refusal)


def test_an_explicit_large_plan_with_one_task_has_its_own_talk_reason() -> None:
    record = full(plan=Plan(path="p.md", tasks=1, large=True))
    code, why, fix = refusal_words(decided(record))
    assert code == "plan-talk"
    assert why.startswith("the plan is marked large, so ")
    assert "with needs a session: the plan is marked large;" in fix


def test_the_standard_track_with_no_read_is_refused_unless_his_word_and_approval_stand() -> (
    None
):
    record = full()
    unread = replace(record.task.criteria, reads=())
    bare = replace(record, task=replace(record.task, criteria=unread))
    assert refusal_words(decided(bare)) == snapshot(
        (
            "no-read",
            "fix-the-login takes the standard track, and no read of its criteria by the personas is on record: the personas read its criteria before the build (stages/interview.md, step 5; for the standard track from a complete request stages/plan.md, step 1)",
            "whoever ran the read records it with lem criteria read fix-the-login done; only the owner skips a read, with lem criteria skip fix-the-login yes and his approval after it, both before a lead starts",
        )
    )
    skipped = replace(unread, skip="yes")
    word = replace(record, task=replace(record.task, criteria=skipped))
    lead = replace(word, task=replace(word.task, spans=(span("lead", MOMENT),)))
    assert refusal_words(decided(lead)) == snapshot(
        (
            "skip-late",
            "a lead of fix-the-login started before the owner completed the skip and approval: on the standard track from a complete request the read always runs, as the only approval there (stages/plan.md, step 1)",
            "the lead runs the read and records it with lem criteria read fix-the-login done",
        )
    )
    alone = replace(skipped, approvals=(approval("alone"),))
    assert refusal_words(
        decided(replace(record, task=replace(record.task, criteria=alone)))
    ) == snapshot(
        (
            "skip-unapproved",
            "the owner's word to skip the personas' read of fix-the-login's criteria is on record, and no approval of the owner's came after it",
            "the owner's yes to the criteria is kept with lem criteria approve fix-the-login --file FILE (stages/interview.md, step 7)",
        )
    )
    assert not isinstance(decided(small(), SMALL_NOTES), Refusal)


def test_a_read_nobody_answered_is_refused_once_and_proposed_not_green_after_two() -> (
    None
):
    record = full()
    once = replace(record.task.criteria, reads=(QUIET,))
    assert refusal_words(
        decided(replace(record, task=replace(record.task, criteria=once)))
    ) == snapshot(
        (
            "criteria-silent",
            "nobody answered the newest read of fix-the-login's criteria; after a second read in a row that nobody answered, the request is proposed as not green",
            "start the read once more and record it with lem criteria read fix-the-login (stages/interview.md, step 5; for the standard track from a complete request stages/plan.md, step 1)",
        )
    )
    twice = replace(record.task.criteria, reads=(QUIET, QUIET))
    made = decided(replace(record, task=replace(record.task, criteria=twice)))
    assert not isinstance(made, Refusal)
    assert made.proposed.reasons[0].startswith("the criteria were not read")


def test_a_flagged_or_split_read_waits_for_his_approval_or_one_without_him() -> None:
    record = full()
    early = approval(at=MOMENT.replace(hour=9))
    for doubt, reason in (
        (read(flagged=1), "1 flagged criterion"),
        (read(flagged=2), "2 flagged criteria"),
        (read(split=True), "a split between the two families"),
    ):
        criteria = replace(record.task.criteria, reads=(doubt,), approvals=(early,))
        doubted = replace(record, task=replace(record.task, criteria=criteria))
        code, why, fix = refusal_words(decided(doubted))
        assert code == "criteria-doubt"
        assert why == (
            f"the newest read of fix-the-login's criteria found {reason}, and no approval of "
            "the owner's came after it"
        )
        assert fix == (
            "the criteria with the personas' answers on top go to the owner "
            "(stages/interview.md, step 6), and his yes is kept with "
            "lem criteria approve fix-the-login --file FILE"
        )
        for after in (approval(), approval("alone")):
            approved = replace(criteria, approvals=(early, after))
            assert not isinstance(
                decided(replace(record, task=replace(record.task, criteria=approved))),
                Refusal,
            )


def test_an_interview_or_someone_elses_request_waits_for_his_yes() -> None:
    record = full(spans=(span("interview"),))
    frozen = replace(record.task.criteria, approvals=(approval("read"),))
    asked = replace(record, task=replace(record.task, criteria=frozen))
    assert refusal_words(decided(asked)) == snapshot(
        (
            "interview-unapproved",
            "fix-the-login had an interview, and its criteria carry no approval of the owner's: the interview ends with his yes",
            "lem criteria approve fix-the-login --file FILE (stages/interview.md, steps 6 and 7), or, while the task runs without him, lem criteria approve fix-the-login --alone (stages/away.md)",
        )
    )
    for by in ("owner", "alone"):
        his = replace(frozen, approvals=(approval(by),))
        assert not isinstance(
            decided(replace(record, task=replace(record.task, criteria=his))), Refusal
        )
    shape = Shape(type="feat", why="a word", track="full", someone_else=True)
    other = full(shape=shape)
    read_only = replace(other.task.criteria, approvals=(approval("read"),))
    assert refusal_words(
        decided(replace(other, task=replace(other.task, criteria=read_only)))
    ) == snapshot(
        (
            "someone-else",
            "fix-the-login is a complete request that someone else wrote, and no approval of the owner's came after the newest read of its criteria: nobody at the terminal read that request, and a freeze by the read is not his yes (stages/plan.md, step 1)",
            "the criteria with the personas' answers go to the owner, and his yes is kept with lem criteria approve fix-the-login --file FILE",
        )
    )
    assert not isinstance(decided(other), Refusal)


def test_an_approval_counts_for_a_read_at_its_end_or_after_it() -> None:
    record = full()
    flagged = read(flagged=1, ended=LATER)
    before = replace(
        record.task.criteria, reads=(flagged,), approvals=(approval(at=MOMENT),)
    )
    assert code_of(
        decided(replace(record, task=replace(record.task, criteria=before)))
    ) == ("criteria-doubt")
    at_end = replace(before, approvals=(approval(at=LATER),))
    assert not isinstance(
        decided(replace(record, task=replace(record.task, criteria=at_end))), Refusal
    )


def test_an_item_removed_after_it_was_filed_and_a_breaker_that_waits_are_refused() -> (
    None
):
    filed = Filed(
        finding="r1.1", disposition="item", path="docs/backlog/a.md", worth="later"
    )
    record = with_landing(full(), filed=(filed,))
    assert code_of(decided(record)) == "item-gone"
    held = Facts(notes=FULL_NOTES, in_tip=frozenset(("docs/backlog/a.md",)))
    assert not isinstance(decided(record, held), Refusal)
    waits = full(decisions=(breaker(1),))
    assert refusal_words(decided(waits)) == snapshot(
        (
            "breaker",
            "breaker 1 of fix-the-login waits for the owner (The note has no place that keeps criterion 1): its build stopped there, and a request is never proposed over it",
            "the owner reads its document and helps (lem decisions log fix-the-login --by owner --breaker 1 ...), parks the task or drops it",
        )
    )
    helped = full(decisions=(breaker(1), taken(2, "w", "c", "owner", breaker=1)))
    assert not isinstance(decided(helped), Refusal)


def test_the_title_is_one_line() -> None:
    record = task(**PREPARED)
    for title in ("", "  ", "one\ntwo"):
        assert refusal_words(propose.decide(record, world(), SMALL_NOTES, title)) == (
            "title",
            "--title is one line: the subject of the change",
            "give the report's commit subject as --title",
        )


# ---- the notes ----


def test_notes_that_lack_a_heading_or_leave_a_fence_open_are_refused() -> None:
    lacking = Facts(notes=FULL_NOTES.replace("## Worth a look\n\nnone\n\n", ""))
    refused = decided(full(), lacking)
    assert refusal_words(refused) == snapshot(
        (
            "notes-headings",
            "the notes lack ## Worth a look: they hold ## Decisions, ## Left open, ## Worth a look, ## Filed in the backlog, ## Not done",
            "give each heading what is true of this task or the one word `none`, then lem land propose fix-the-login again",
        )
    )
    fenced = Facts(notes=FULL_NOTES + "\n```\n## Not done\n")
    assert code_of(decided(full(), fenced)) == "notes-fence"
    quoted = Facts(notes=FULL_NOTES + "\n```\n## Decisions\n```\n")
    assert not isinstance(decided(full(), quoted), Refusal)
    shape = Shape(type="docs", why="w", track="small", careful=("money",))
    careful = with_landing(
        small(shape=shape), reviews=(replace(REVIEWED, kind="full"),)
    )
    assert code_of(decided(careful, SMALL_NOTES)) == "notes-headings"


HELD = frozenset(("docs/backlog/a-held-item.md",))


def bare(notes: str, *, small_track: bool = False) -> tuple[str, ...]:
    """The lines `propose` would refuse."""
    parsed = propose_notes.parsed(notes)
    assert not isinstance(parsed, Refusal)
    return propose_lines.bare(parsed, small=small_track, in_tip=HELD)


def with_line(line: str, heading: str = "## Seen, not filed") -> str:
    """The standard track's notes with `line` under `heading`."""
    return FULL_NOTES.replace("## Not done", f"{heading}\n\n{line}\n\n## Not done")


def test_a_hand_written_line_with_no_call_is_named() -> None:
    line = "- `land.py:cmd_start` writes over `reviews/review-1.*`"
    assert bare(with_line(line)) == (line,)
    for passes in (
        f"{line}; under: a second landing is rare, and the review files are kept in git",
        f"{line}; cheap: a comment says the opposite",
        f"{line}; Under: the owner reads the reviews in the pull request",
        f"{line}; filed as `docs/backlog/a-held-item.md`",
    ):
        assert bare(with_line(passes)) == ()


def test_a_call_with_no_reason_or_an_item_the_tip_lacks_is_no_call() -> None:
    for line in (
        "- `a.py`: one; under:",
        "- `a.py`: one; under:   ",
        "- `a.py`: one; underline: the word",
        "- `a.py`: one; filed as docs/backlog/gone.md",
        "- `a.py`: one; over: worth an item",
    ):
        notes = FULL_NOTES.replace("## Left open\n\nnone", f"## Left open\n\n{line}")
        assert bare(notes) == (line.strip(),)


def test_a_should_finding_left_open_is_checked_and_its_continued_line_is_one_entry() -> (
    None
):
    notes = FULL_NOTES.replace(
        "## Left open\n\nnone",
        "## Left open\n\n- `land.py:start_locked`: no test holds the carry,\n"
        "  under: the journey of the moved base holds it\n- `land.py:cmd_base`: a long line",
    )
    assert bare(notes) == ("- `land.py:cmd_base`: a long line",)


def test_an_indented_bullet_continues_the_entry_above_it() -> None:
    notes = FULL_NOTES.replace(
        "## Left open\n\nnone",
        "## Left open\n\n- `a.py`: the first\n  - under: a reason on its own line",
    )
    assert bare(notes) == ()


def test_an_item_path_before_a_colon_is_the_item() -> None:
    line = (
        "- land.py:cmd_start overwrites reviews; "
        "held by docs/backlog/a-held-item.md: same defect"
    )
    assert bare(with_line(line)) == ()


def test_the_fast_track_reads_its_lines_before_any_heading_and_a_left_open_it_wrote() -> (
    None
):
    notes = "- `a.py`: a should finding\n\n## Left open\n\n- `b.py`: another\n"
    assert bare(notes, small_track=True) == (
        "- `a.py`: a should finding",
        "- `b.py`: another",
    )
    assert bare(notes) == ("- `b.py`: another",)


def test_the_other_parts_and_a_lone_none_are_not_read() -> None:
    notes = FULL_NOTES.replace(
        "## Worth a look\n\nnone", "## Worth a look\n\n- the one line"
    )
    assert bare(notes) == ()
    assert bare("none\n", small_track=True) == ()


def test_a_line_the_script_writes_passes() -> None:
    line = "- `README.md`: the README has no heading; under: a reader reads one line"
    assert bare(with_line(line)) == ()


# ---- the text ----


def test_green_with_no_decision() -> None:
    text = text_of(full())
    assert text.splitlines()[0] == pr_text.pr_head.GREEN
    assert text.split("## Decisions of the build\n\n", 1)[1].splitlines()[0] == "none"
    assert text.endswith("## Not done\n\nnone\n")


def test_not_green_puts_each_reason_first() -> None:
    out = text_of(full(decisions=(picked(1, "Where", "a"),))).splitlines()
    assert out[:2] == ["**Not green.**", ""]
    assert out[2].startswith("- decision 1 was taken without the owner (Where)")


def test_the_request_in_his_words_and_the_issue_under_it_on_each_track() -> None:
    issue = Ticket(tracker="github", id="#42", repo="o/p")
    for record in (full(ticket=issue), small(ticket=issue)):
        facts = FACTS if record.task.criteria.size == "full" else SMALL_NOTES
        out = text_of(record, facts).splitlines()
        assert out.count("Issue: #42") == 1
        assert out[out.index("Issue: #42") - 2] == "> fix the login"
        lowered = "\n".join(out).lower()
        assert not any(
            word in lowered for word in ("closes #42", "fixes #42", "resolves #42")
        )
    for ticket in (Ticket(tracker="linear", id="MBZ-12"), None):
        assert "Issue:" not in text_of(full(ticket=ticket))


def test_the_cause_of_a_bug_is_named_once_with_its_place_and_a_question_names_none() -> (
    None
):
    bug = Investigation(
        kind="fix",
        line="the total adds the refund as a payment",
        where="billing/invoice.py:total",
    )
    checks = text_of(full(investigation=bug)).split("## Checks", 1)[1]
    cause = (
        "- the cause, as the investigation before the build found it: the total adds the "
        "refund as a payment (billing/invoice.py:total)"
    )
    assert [line for line in checks.splitlines() if "the cause" in line] == [cause]
    question = Investigation(kind="question", line="the export reads the night before")
    assert "the cause" not in text_of(full(investigation=question))
    assert "the cause, as the investigation found it" in text_of(
        small(investigation=bug), SMALL_NOTES
    )


def test_a_check_that_passed_in_silence_shows_its_exit() -> None:
    from lem.records.landing.checks import Outcome

    quiet = Outcome(
        command="sh tests/words.sh", exit=0, last="", output="c.log", passed=True
    )
    record = with_landing(small(), checked=replace(CHECKED, outcomes=(quiet,)))
    assert (
        "- check, `sh tests/words.sh`: exit 0"
        in text_of(record, SMALL_NOTES).splitlines()
    )


def test_the_criteria_with_their_tests_the_check_line_and_tests_taken_from_the_polish_pass() -> (
    None
):
    text = text_of(full())
    assert (
        "   - `sh tests/t.sh`: passes on the branch, fails on the base commit" in text
    )
    assert "   - no test: printf ends every line so." in text
    assert (
        "- the tests of the criteria: 1 pass on the branch and fail on the base commit; "
        "1 criterion has no test"
    ) in text.splitlines()
    taken_at = CriterionCheck(
        criterion=1,
        red_on_base=True,
        green_on_tip=True,
        taken_at="a1b2c3d4e5f6a7b8" * 2 + "a" * 8,
    )
    polished = with_landing(full(), checked=replace(CHECKED, criteria=(taken_at,)))
    assert (
        "- the tests of the criteria: 1 pass on the branch and fail on the base commit, "
        "taken from the polish pass at a1b2c3d4e, and not run again; 1 criterion has no test"
    ) in text_of(polished).splitlines()
    unchecked = with_landing(full(), checked=CHECKED)
    assert "   - `sh tests/t.sh`: not checked" in text_of(unchecked)


def test_the_polish_pass_the_size_and_the_bar() -> None:
    record = with_landing(
        full(), polished=Polished(before=TIP, after=TIP, commits=1, at=MOMENT)
    )
    out = text_of(record).splitlines()
    assert "- the polish pass: 1 commit, 0 items filed in the backlog" in out
    assert "- the bar: no mark of a lowered bar found" in out
    assert "- size: ? files, ? changed lines" in out


def test_the_personas_read_and_his_approval_in_the_checks() -> None:
    record = full()
    split = read(asked=3, flagged=1, split=True, silent=(QUIET.silent[0],))
    criteria = replace(record.task.criteria, reads=(split,))
    said = text_of(replace(record, task=replace(record.task, criteria=criteria)))
    assert (
        "- the criteria were read by 2 of 3 personas asked, two model families (opus, sol); "
        "1 of 2 criteria flagged; the two families split; no answer from the buyer, opus "
        "(the model was at capacity); the owner approved them on 2026-11-25"
    ) in said.splitlines()
    twice = replace(record.task.criteria, reads=(QUIET, QUIET))
    quiet = text_of(replace(record, task=replace(record.task, criteria=twice)))
    assert "2 reads in a row, and none of the 2 personas asked answered" in quiet


def test_an_interview_hold_is_not_an_approval_wait_in_the_pull_request() -> None:
    record = full()
    held = OwnerHold(on="interview", since=MOMENT, line="The interview waits")
    changed = replace(record, task=replace(record.task, hold=held))
    words = pr_read.read_line(changed)
    assert words.endswith("the owner approved them on 2026-11-25")
    assert "waited" not in words


def test_criteria_he_changed_after_the_read_are_one_line() -> None:
    record = full()
    changed_after = replace(
        record.task.criteria, digest="d2", approvals=(replace(approval(), digest="d2"),)
    )
    said = text_of(replace(record, task=replace(record.task, criteria=changed_after)))
    assert (
        "- the criteria changed after the personas' read, by the owner's approval 1, and "
        "the change was not read"
    ) in said.splitlines()
    assert "the criteria changed after" not in text_of(record)


def test_each_stand_in_is_its_line_and_no_reason_of_not_green_on_both_tracks() -> None:
    stood = StandIn(
        seat="reviewer",
        failed="codex/gpt-6.2-sol:high",
        took="claude/opus:high",
        error="tokens",
        at=MOMENT,
    )
    line = (
        "- the reviewer was `claude/opus:high` in place of `codex/gpt-6.2-sol:high`: "
        "Codex had no tokens"
    )
    text = text_of(full(stand_ins=(stood,)))
    assert line in text.splitlines()
    assert text.splitlines()[0] == pr_text.pr_head.GREEN
    assert line in text_of(small(stand_ins=(stood,)), SMALL_NOTES).splitlines()


def test_each_track_names_the_time_without_him_and_one_with_him_has_no_such_line() -> (
    None
):
    line = "It ran without the owner from 2026-11-25 10:00 UTC."
    for record, facts in (
        (full(mode="alone"), FACTS),
        (small(mode="alone"), SMALL_NOTES),
    ):
        out = text_of(record, facts).splitlines()
        assert out[:4] == [pr_text.pr_head.GREEN, "", line, ""]
    assert "ran without the owner" not in text_of(full())


def test_the_breaker_and_each_decision_with_who_and_why() -> None:
    lines = (
        breaker(1, "irreversible", irreversible="person"),
        taken(
            2,
            "Email the merchants",
            "send nothing",
            "owner",
            breaker=1,
            words="no email",
            why="They read the export anyway.",
        ),
    )
    decided_part = text_of(full(decisions=lines)).split(
        "## Decisions of the build\n\n", 1
    )[1]
    assert decided_part.startswith(
        "- the build stopped at breaker 1, 2026-11-25 10:00 UTC: The note has no place that "
        "keeps criterion 1. Why it stopped: the next step could not be reversed by a later "
        "no (person); the owner helped, decision 2."
    )
    assert (
        '- Email the merchants: "send nothing", by the owner, his help on breaker 1. They '
        'read the export anyway. The owner\'s words: "no email"'
    ) in decided_part
    waits = pr_decisions.lines(full(decisions=(breaker(1),)))
    assert waits[0].endswith(
        "no option of the ladder kept the approved criteria; it waits for the owner."
    )
    votes = (("the merchant, opus", "a"), ("the accountant, sol", "a"))
    personas = pr_decisions.lines(
        full(decisions=(taken(1, "Which", "a", "personas", votes=votes),))
    )
    voted = (
        '- Which: "a", by the personas: 2 votes of 2 personas, two model families, all for '
        "it. it holds"
    )
    assert personas == (voted,)


def test_a_change_of_a_criterion_is_one_line_with_what_it_was_and_who() -> None:
    moved = changed(
        1,
        "changed",
        1,
        "y is taken by another file.",
        was="The file holds the word y.",
        now="The file holds the word z.",
        by="personas",
        said="Both personas picked x.",
    )
    text = text_of(full(decisions=(moved,)))
    assert (
        '- criterion 1: was "The file holds the word y.", now "The file holds the word z.". '
        "y is taken by another file. By the personas: Both personas picked x."
    ) in text.splitlines()
    lead = changed(
        2, "added", 2, "Whole lines only.", now="It ends with a line break.", by="lead"
    )
    record = full(decisions=(lead,))
    criteria = replace(record.task.criteria, approvals=(approval(), approval(number=2)))
    over = text_of(replace(record, task=replace(record.task, criteria=criteria)))
    assert over.splitlines()[0] == pr_text.pr_head.GREEN
    assert (
        '- criterion 2: added, "It ends with a line break.". Whole lines only. By the lead. '
        "Approved by the owner afterwards (approval 2)."
    ) in over.splitlines()


def test_the_pull_request_links_no_picture_and_folds_an_important_story() -> None:
    notes = FULL_NOTES.replace(
        "## Worth a look\n\nnone",
        "## Worth a look\n\n![The file after](media/after.png)",
    )
    plain = text_of(full(), Facts(notes=notes))
    assert "media/" not in plain
    assert "The file after (a picture on the task's board)" in plain
    assert "<details>" not in plain
    chart = 'flowchart TD\n  A["The real run ends"] --> B{"GitHub?"}'
    folded = text_of(
        full(decisions=(picked(8, "How the report shows", "B", chart=chart),))
    )
    assert folded.count("<details>") == 1
    assert f"```mermaid\n{chart}\n```\n\n</details>" in folded
    assert "**The case** (derived from the code, not run):" in folded


GUARD = Finding(
    id="r1.1",
    level="nit",
    where="tests/unit/test_board_model.py",
    title="two test classes come after the main guard",
    what="the file runs them after its main guard.",
    against="under",
    why="only a reader of the code meets it",
)
SUPPRESSION = Finding(
    id="r1.2",
    level="nit",
    where="app.py:run",
    title="an outdated lint suppression",
    what="the mark names a rule the linter no longer has.",
    against="cheap",
    why="a comment of the code, no behavior",
)
LOAD = Finding(
    id="r1.3",
    level="nit",
    where="app.py:load",
    title="load crashes on an empty file",
    what="load of an empty file raises KeyError.",
    against="over",
)
GUARD_ITEM = "docs/backlog/two-test-classes-come-after-the-main-guard.md"
LOAD_ITEM = "docs/backlog/load-crashes-on-an-empty-file.md"
ADDED = (
    Filing(path=LOAD_ITEM, title="load crashes on an empty file", worth="later"),
    Filing(
        path=GUARD_ITEM, title="two test classes come after the main guard", worth="no"
    ),
)


def outside(record: Record, notes: str, added: tuple[Filing, ...] = ADDED) -> list[str]:
    """The text of `record` whose review saw three defects outside the change."""
    review = replace(
        REVIEWED,
        findings=(GUARD, SUPPRESSION, LOAD),
        counts=Counts(outside=3),
        to_file=("r1.1", "r1.2", "r1.3"),
    )
    filed = (
        Filed(finding="r1.1", disposition="item", path=GUARD_ITEM, worth="no"),
        Filed(finding="r1.2", disposition="seen", line="cheap: a comment"),
        Filed(finding="r1.3", disposition="item", path=LOAD_ITEM, worth="later"),
    )
    found = with_landing(record, reviews=(review,), filed=filed)
    return text_of(found, Facts(notes=notes, added=added)).splitlines()


def test_an_item_under_the_bar_is_not_worth_it_and_a_cheap_one_nobody_fixed_is_a_line() -> (
    None
):
    for record, notes in ((full(), FULL_NOTES), (small(), "none\n")):
        out = outside(record, notes)
        seen = out.index("## Seen, not filed")
        assert out[seen + 2] == (
            "- `app.py:run`: an outdated lint suppression; cheap: a comment of the code, no "
            "behavior"
        )
        filed = out.index("## Filed in the backlog")
        assert out[filed + 2] == f"- `{LOAD_ITEM}`: load crashes on an empty file"
        not_worth = out.index("## Filed as not worth it")
        assert (
            out[not_worth + 2]
            == f"- `{GUARD_ITEM}`: two test classes come after the main guard"
        )
        assert filed < not_worth < seen
        assert "## Fixed on the way" not in out
        line = next(line for line in out if line.startswith("- the review, round 1"))
        assert line.endswith(
            f"; it saw 3 defects outside the change, filed as `{GUARD_ITEM}`, `{LOAD_ITEM}`; "
            "1 seen, not filed"
        )


def test_the_heading_of_an_item_is_its_worth_at_the_tip_and_a_notes_line_naming_it_is_one() -> (
    None
):
    from lem.app.landing.propose_items import head_of

    css = "docs/backlog/a-css-rule-matches-nothing.md"
    # the items as the tip's files hold them: a bare `no` is the word, never false
    added = (
        head_of(b"---\nworth: no\n---\n\n# load crashes on an empty file\n", LOAD_ITEM),
        head_of(
            b"---\nwhere: tests/unit/test_board_model.py\nworth: no\n---\n"
            b"# two test classes come after the main guard\n",
            GUARD_ITEM,
        ),
        head_of(b"---\nworth: no\n---\n# a CSS rule matches nothing\n", css),
    )
    notes = FULL_NOTES.replace(
        "## Filed in the backlog\n\nnone",
        f"## Filed in the backlog\n\n- `{css}`, worth: no, filed by the polish pass",
    )
    out = outside(full(), notes, added)
    filed, not_worth = (
        out.index("## Filed in the backlog"),
        out.index("## Filed as not worth it"),
    )
    assert out[filed + 2 : filed + 4] == ["none", ""]
    assert out[not_worth + 2 : not_worth + 5] == [
        f"- `{LOAD_ITEM}`: load crashes on an empty file",
        f"- `{GUARD_ITEM}`: two test classes come after the main guard",
        f"- `{css}`, worth: no, filed by the polish pass",
    ]
    assert sum("a-css-rule-matches-nothing" in line for line in out) == 1


def test_a_fix_line_that_names_the_cheap_entry_takes_its_line_out() -> None:
    fix = (
        "## Fixed on the way\n\n- `app.py` (abc1234): r1.2, the suppression named a rule "
        "the linter no longer has\n\n"
    )
    for record, notes in (
        (full(), FULL_NOTES.replace("## Not done", fix + "## Not done")),
        (small(), fix),
    ):
        out = outside(record, notes)
        assert out.index("## Filed in the backlog") < out.index(
            "## Filed as not worth it"
        )
        assert out.index("## Filed as not worth it") < out.index("## Fixed on the way")
        assert "## Seen, not filed" not in out
        line = next(line for line in out if line.startswith("- the review, round 1"))
        assert line.endswith("; 1 fixed on the way")


def test_a_review_that_saw_nothing_outside_keeps_the_notes_as_they_were() -> None:
    clean = replace(REVIEWED, findings=(), counts=Counts(), to_file=())
    text = text_of(with_landing(full(), reviews=(clean,), filed=()))
    assert text.endswith("\n\n" + FULL_NOTES)
    assert "## Seen, not filed" not in text


def test_the_notes_keep_their_fixed_and_seen_lines_before_the_new_findings() -> None:
    fixed = "- `app.py` (abc1234): correct the comment"
    noted = "- `other.py`: the polish pass saw an old comment; cheap: text only"
    notes = FULL_NOTES.replace(
        "## Not done",
        f"## Fixed on the way\n\n{fixed}\n\n## Seen, not filed\n\n{noted}\n\n## Not done",
    )
    shown = outside(full(), notes)
    fixed_at = shown.index("## Fixed on the way")
    seen_at = shown.index("## Seen, not filed")
    assert shown[fixed_at + 2] == fixed
    assert shown[seen_at + 2] == noted
    assert shown[seen_at + 3].startswith("- `app.py:run`: an outdated lint suppression")
    assert fixed_at < seen_at < shown.index("## Not done")
    assert shown.count(f"- `{LOAD_ITEM}`: load crashes on an empty file") == 1


def test_an_open_finding_points_to_its_item_and_a_new_item_is_filed() -> None:
    held = "docs/backlog/older-load-failure.md"
    opened = replace(LOAD, id="r1.4", open=held)
    review = replace(
        REVIEWED,
        findings=(opened, GUARD),
        counts=Counts(outside=2),
        to_file=(opened.id, GUARD.id),
    )
    filed = (
        Filed(finding=GUARD.id, disposition="item", path=GUARD_ITEM, worth="later"),
    )
    record = with_landing(full(), reviews=(review,), filed=filed)
    headings, seen = pr_outside.parts(record, Facts(), "")
    assert headings["## Filed in the backlog"] == [f"- `{GUARD_ITEM}`: {GUARD.title}"]
    assert headings["## Filed as not worth it"] == []
    assert seen == (f"- `{LOAD.where}`: {LOAD.title}; an open item holds it, `{held}`",)


def test_a_fenced_notes_example_cannot_start_a_new_section() -> None:
    notes = (
        "## Decisions\n\n```md\n## Seen, not filed\nnone\n```\n\n## Not done\nnone\n"
    )
    parsed = propose_notes.parsed(notes)
    assert not isinstance(parsed, Refusal)
    assert [part.heading for part in parsed.parts] == ["## Decisions", "## Not done"]
    assert "## Seen, not filed" in parsed.parts[0].lines


def test_an_item_reason_does_not_change_its_jev_identity() -> None:
    path = "docs/backlog/tidy.md"
    text = "---\nworth: no\nwhere: src/v.py:tidy\n---\n# Tidy keeps a space\n\nTidy keeps two spaces.\n"
    bare = items.read(path, text)
    reasoned = items.read(path, text + "\nDecided against: the owner never sees it.\n")
    changed = items.read(path, text.replace("two spaces", "three spaces"))
    assert bare and reasoned and changed
    first, second, other = map(propose_jev.item_asked, (bare, reasoned, changed))
    assert (first.label, first.defect.where, first.defect.what) == (
        path,
        "src/v.py:tidy",
        "Tidy keeps two spaces.",
    )
    assert not first.reason and second.reason
    assert first.key == second.key != other.key


def test_the_careful_line_and_the_review_lines_on_the_standard_track() -> None:
    called = replace(REVIEWED, careful=False, careful_why="it reaches no topic.")
    bar_read = replace(
        CHECKED,
        edited=(Edited(path="tests/test_login.py", kind="test"),),
        not_covered=(".custom",),
    )
    facts = Facts(notes=FULL_NOTES, bar_read=bar_read)
    out = text_of(with_landing(full(), reviews=(called,)), facts).splitlines()
    assert "- the change edits 1 existing test (`tests/test_login.py`)" in out
    assert "- the bar has no marks of its own for files of these kinds: .custom" in out
    assert "- careful: no; the review says no: it reaches no topic" in out
    assert (
        "- the review, round 1 (one read; answered: claude): clean, 0 must-fix, 0 should, "
        "0 nit; it saw 1 defect outside the change; 1 seen, not filed"
    ) in out
    plan = Plan(path="p.md", careful="a charge")
    talk = Talk(
        reviewer="codex",
        turns=1,
        questions=1,
        settled=1,
        open=0,
        repaired=0,
        design=0,
        unargued=0,
        root=0,
        layer=1,
        shared=2,
        at=MOMENT,
    )
    talked = text_of(
        full(plan=plan, talk=talk), Facts(notes=FULL_NOTES + "\n## Migration\n\nnone\n")
    )
    assert (
        "- the plan talk: codex argued the plan with its defender, 1 turn; 1 position "
        "settled by the two, 0 left open; 1 question in the reviewer's first list, 0 "
        "repaired by the defender, 0 of the open ones a design choice, 0 raised after the "
        "list and not argued, 0 repaired at the cause, 1 layer over a cited decision, 2 "
        "decisions two questions named"
    ) in talked.splitlines()
    careful = replace(REVIEWED, careful=True, careful_why="it charges.", kind="full")
    later = text_of(
        with_landing(full(), reviews=(careful,)),
        Facts(notes=FULL_NOTES + "\n## Migration\n\nnone\n"),
    )
    assert (
        "- no plan talk: the request became careful after its plan, by its review"
        in later
    )
    assert (
        "**Careful**, so the owner merges it: the review says so: it charges." in later
    )


def test_propose_is_not_due_while_its_checks_review_or_filing_do_not_hold() -> None:
    from lem.model.landing import checks, phases

    record = task(**PREPARED)
    assert phases.due(record, world()).step == "propose"
    red = with_landing(record, checked=replace(CHECKED, outcome="red"))
    assert phases.due(red, world()).step == "checks"
    moved = with_landing(record, checked=replace(CHECKED, inputs="other"))
    assert moved.landing is not None
    assert moved.landing.checked is not None
    assert moved.landing.checked.inputs != checks.inputs(world().rules)
    assert phases.due(moved, world()).step == "checks"
    assert phases.due(with_landing(record, reviews=()), world()).step == "read"
    assert phases.due(with_landing(record, filed=()), world()).step == "file"


def test_the_base_branch_and_a_protected_one_take_no_push() -> None:
    record = task(**PREPARED)
    on_base = propose.decide(record, world(branch="main"), SMALL_NOTES, "docs: x")
    assert code_of(on_base) == "protected"
    assert isinstance(on_base, Refusal)
    assert on_base.why.startswith("main is the base branch")


def test_notes_that_are_no_file_of_text_are_refused_by_name(tmp_path: Path) -> None:
    from lem.app.landing import propose_seen

    missing = tmp_path / "notes.md"
    try:
        propose_seen.notes_of(str(missing))
    except Refusal as refused:
        assert refused.code == "notes"
        assert str(missing) in refused.why
    else:
        raise AssertionError("a missing notes file is refused")


# ---- the review of 2026-11-25 (findings 3, 5, 6, 7, 9) ----


def test_a_finding_whose_open_item_is_gone_or_now_says_no_is_refused() -> None:
    over = Finding(
        id="r1.2", level="nit", where="a", title="t", what="w", against="over"
    )
    review = replace(
        REVIEWED,
        findings=(*REVIEWED.findings, over),
        counts=Counts(outside=2),
        to_file=("r1.1", "r1.2"),
    )
    held = Filed(finding="r1.2", disposition="same", path="docs/backlog/held.md")
    record = with_landing(full(), reviews=(review,), filed=(*PREPARED["filed"], held))
    assert code_of(decided(record)) == "item-gone"
    there = Facts(
        notes=FULL_NOTES,
        in_tip=frozenset(("docs/backlog/held.md",)),
        heads=(Filing(path="docs/backlog/held.md", title="t", worth="no"),),
    )
    assert refusal_words(decided(record, there)) == snapshot(
        (
            "item-refuted",
            "the finding r1.2 is over the bar, and the open item docs/backlog/held.md that holds it says `worth: no` at the tip",
            "lem land file fix-the-login --again files it as an item of its own, `worth: later`, that names the old one; then this step runs again",
        )
    )
    later = replace(there, heads=(Filing(path="docs/backlog/held.md", worth="later"),))
    assert not isinstance(decided(record, later), Refusal)


def test_a_careful_request_needs_the_full_set_and_the_owner_merges_it_green() -> None:
    plan_free = full(
        shape=Shape(type="feat", why="w", track="full", careful=("money",))
    )
    careful = Facts(notes=FULL_NOTES + "\n## Migration\n\nnone\n")
    assert refusal_words(decided(plan_free, careful)) == snapshot(
        (
            "review-floor",
            "the request is careful, and its newest review was read: a careful change gets the project's full set",
            "lem land read fix-the-login says what a reviewer gets; run the full set, then record it with lem land read fix-the-login --record FILE",
        )
    )
    whole = with_landing(plan_free, reviews=(replace(REVIEWED, kind="full"),))
    made = decided(whole, careful)
    assert not isinstance(made, Refusal)
    assert (made.proposed.green, made.proposed.who_acts) == (True, "owner")


def test_the_first_approval_of_his_answers_his_word_to_skip_the_read() -> None:
    record = full()
    criteria = replace(record.task.criteria, reads=(), approvals=())
    bare = replace(record, task=replace(record.task, criteria=criteria))
    first = owner_approval(skip_word(bare))
    both = owner_approval(lead_start(first), now=LATER)
    assert both.task.criteria.skip_approval == 1
    assert not isinstance(decided(both), Refusal)
    skipped_again = skip_word(both, now=LATER)
    assert code_of(decided(skipped_again)) == "skip-late"


def test_an_item_head_keeps_its_worth_as_the_word_written() -> None:
    from lem.app.landing import propose_items

    head = propose_items.head_of(
        b"---\nworth: no\nwhere: a.py\n---\n# A title\n", "p.md"
    )
    assert (head.title, head.worth) == ("A title", "no")
    later = propose_items.head_of(b"---\nworth: later\n---\n\n# T\n", "q.md")
    assert later.worth == "later"


def test_a_closing_fence_indented_four_spaces_is_code_and_the_block_stays_open() -> (
    None
):
    notes = FULL_NOTES + "\n```\nsample\n    ```\n"
    assert code_of(decided(full(), Facts(notes=notes))) == "notes-fence"
    closed = FULL_NOTES + "\n```\nsample\n   ```\n"
    assert not isinstance(decided(full(), Facts(notes=closed)), Refusal)


def test_a_list_fence_needs_a_close_even_when_a_paragraph_ends_the_list() -> None:
    notes = FULL_NOTES + "\n- ```python\n  sample()\n\nA new paragraph.\n"
    code, why, _ = refusal_words(decided(full(), Facts(notes=notes)))
    assert code == "notes-fence"
    assert f"line {len(FULL_NOTES.splitlines()) + 2} opens" in why


def test_a_block_quote_fence_can_close_at_the_end_of_the_notes() -> None:
    notes = FULL_NOTES + "\n> ```python\n> sample()\n> ```"
    assert isinstance(decided(full(), Facts(notes=notes)), propose.Proposal)


def test_unclosed_fence_content_includes_the_last_line_without_a_newline() -> None:
    notes = "```python\nfirst()\nlast()"
    code, why, _ = refusal_words(propose_notes.parsed(notes))
    assert code == "notes-fence"
    assert "line 1 opens" in why


def test_a_tilde_fence_with_a_backtick_in_its_label_hides_a_notes_heading() -> None:
    sample = "~~~sample`part\n## Not done\n```\n~~~\n"
    notes = FULL_NOTES.replace("## Not done\n\nnone\n", sample)
    assert code_of(decided(full(), Facts(notes=notes))) == "notes-headings"
    assert isinstance(
        decided(full(), Facts(notes=notes + "\n## Not done\n\nnone\n")),
        propose.Proposal,
    )


def test_a_full_change_with_no_read_or_a_doubt_is_refused_and_its_read_is_a_line() -> (
    None
):
    record = full()
    unread = replace(record.task.criteria, reads=())
    assert code_of(
        decided(replace(record, task=replace(record.task, criteria=unread)))
    ) == ("no-read")
    early = approval(at=MOMENT.replace(hour=9))
    flagged = replace(
        record.task.criteria, reads=(read(flagged=1),), approvals=(early,)
    )
    doubted = replace(record, task=replace(record.task, criteria=flagged))
    assert code_of(decided(doubted)) == "criteria-doubt"
    partial = read(asked=3, silent=(QUIET.silent[0],))
    changed_after = replace(
        record.task.criteria,
        reads=(partial,),
        digest="d2",
        approvals=(replace(approval(), digest="d2"),),
    )
    later = replace(record, task=replace(record.task, criteria=changed_after))
    made = decided(later)
    assert not isinstance(made, Refusal)
    assert made.proposed.green
    lines = text_of(later).splitlines()
    assert (
        "- the criteria were read by 2 of 3 personas asked, two model families (opus, sol); "
        "nobody confused; no answer from the buyer, opus (the model was at capacity); the "
        "owner approved them on 2026-11-25"
    ) in lines
    assert (
        "- the criteria changed after the personas' read, by the owner's approval 1, and "
        "the change was not read"
    ) in lines


def test_a_pick_of_the_dialectic_is_a_line_with_its_reason_and_its_story() -> None:
    where = picked(1, "Where the word goes", "the first line")
    text = text_of(full(decisions=(where,)))
    lines = text.splitlines()
    assert lines[2] == (
        '- decision 1 was taken without the owner (Where the word goes): "the first line", '
        "by the dialectic"
    )
    decided_part = text.split("## Decisions of the build\n\n", 1)[1]
    assert decided_part.startswith(
        '- Where the word goes: "the first line", by the dialectic. A reads first.'
    )
    assert (
        "<details><summary>Decision 1, its story: Where the word goes</summary>" in text
    )
    assert "**Why it could happen:** a split" in text


def test_the_retro_can_read_every_proposal_after_the_tip_changes() -> None:
    import msgspec

    from lem.app.landing.propose_made import opened
    from lem.records.landing.propose import OwnerMerge
    from lem.records.record import Record
    from unit.landing.worlds import BASED, PROPOSED, PULL

    tips = (TIP, OTHER, "a" * 40)
    reasons = ((), (), ("the owner did not approve the criteria",))
    record = small()
    owner_merge = OwnerMerge(state="stands", why="the change and its reasons stay")
    for number, (tip, why) in enumerate(zip(tips, reasons, strict=True)):
        made = replace(PROPOSED, tip=tip, green=not why, reasons=why)
        if number == 1:
            based = replace(BASED, tip=tip, before=TIP, reviewed=TIP, carried=True)
            record = with_landing(record, based=based, reviews=(REVIEWED,))
            made = replace(made, merge_review="carried", owner_merge=owner_merge)
        record = opened(record, made=made, pull=PULL)
    saved = msgspec.json.decode(msgspec.json.encode(record), type=Record)
    entries = msgspec.json.decode(msgspec.json.encode(saved.journal))
    proposals = [entry for entry in entries if entry["kind"] == "proposed"]
    assert proposals[1]["review_carry"] == "The review carried over the rebase."
    assert proposals[1]["merge_review"] == "carried"
    assert proposals[1]["owner_merge"] == {"state": "stands", "why": owner_merge.why}
    assert "owner_merge" not in proposals[0]
    assert [
        (entry["tip"], entry["green"], entry.get("reasons", []), entry["at"])
        for entry in entries
        if entry["kind"] == "proposed"
    ] == [
        (tip, not why, list(why), msgspec.to_builtins(PROPOSED.at))
        for tip, why in zip(tips, reasons, strict=True)
    ]


def test_a_foreign_pull_request_refusal_keeps_the_forges_author() -> None:
    from lem.ports.forge_facts import Pull

    pull = Pull(
        number=99,
        url="https://github.com/owner/project/pull/99",
        title="Ania's title",
        state="open",
        head=TIP,
        head_ref="docs/fix-the-login",
        base="main",
        author="ania",
    )
    foreign = propose.adopted(small(), world(candidates=(pull_identity.seen(pull),)))
    assert refusal_words(foreign) == snapshot(
        (
            "foreign-pull",
            "pull request #99 by ania is open on docs/fix-the-login at 1111111111111111111111111111111111111111, a head Lem did not push: it is somebody else's, and Lem does not push over it or rewrite its text",
            "the owner closes that pull request on GitHub, or asks its author to, then lem land propose fix-the-login again; the task's branch is on its record, so a rename in the worktree alone does not give it another",
        )
    )
    anonymous = propose.adopted(
        small(), world(candidates=(pull_identity.seen(replace(pull, author=None)),))
    )
    assert isinstance(anonymous, Refusal)
    assert anonymous.why.startswith("pull request #99 by someone is open on")


def test_the_plan_talk_names_its_bound_only_when_it_goes_over() -> None:
    talk = Talk(
        reviewer="codex",
        turns=22,
        questions=5,
        settled=4,
        open=1,
        repaired=2,
        design=1,
        unargued=0,
        root=0,
        layer=0,
        shared=0,
        at=MOMENT,
    )
    assert "over the bound" not in pr_talk.talked(talk)
    over = pr_talk.talked(replace(talk, turns=23))
    assert "23 turns, over the bound of 22 for its 5 questions;" in over


def test_a_resolved_conflict_has_one_account_in_the_reply_and_the_pull_request() -> (
    None
):
    from lem.app.landing import propose_made
    from lem.records.landing.start import Resolution, Started
    from unit.landing.worlds import BASE, PROPOSED, PULL

    record = with_landing(
        small(),
        started=Started(
            round=2,
            branch="docs/fix-the-login",
            base_ref="main",
            conflicting=True,
            at=MOMENT,
        ),
        resolution=Resolution(
            files=("shop.txt",), before=OTHER, after=TIP, base=BASE, read=2
        ),
        reviews=(replace(REVIEWED, attempt=2, of="resolution", tip=TIP),),
        checked=CHECKED,
    )
    made = propose_made.given(record, PROPOSED, (PULL, "docs/fix-the-login"))
    line = (
        "rebased on main after the forge called it conflicting; one conflict in shop.txt, "
        "resolved by a builder; one read of the resolution"
    )
    assert line in propose_made.said(made)
    text = text_of(record, SMALL_NOTES)
    assert f"{line[0].upper()}{line[1:]}" in text
    assert "the checks passed again" in propose_made.said(made)
    assert "the checks passed again" in text


def test_a_fence_as_the_last_line_reports_where_it_opens() -> None:
    notes = "## Decisions\n\nnone\n\n```\n"
    assert refusal_words(propose_notes.parsed(notes)) == (
        "notes-fence",
        (
            "the notes of the pull request (--notes): line 5 opens a code block that never "
            "closes. A heading inside the block does not count."
        ),
        (
            "close the fence, or put a sample that holds fences of its own in a "
            "longer fence (```` around ```), then propose again"
        ),
    )


def test_fences_allow_trailing_space_and_reject_text_after_their_closing_marks() -> (
    None
):
    closed = propose_notes.parsed("```text\nSample\n   ```  \n")
    assert isinstance(closed, propose_notes.Notes)
    for fake in ("`", "```extra", "X```", "\t```"):
        assert (
            code_of(propose_notes.parsed(f"```text\nSample\n{fake}\n")) == "notes-fence"
        )


def test_only_top_level_second_level_headings_divide_the_notes() -> None:
    text = "# Title\n\n### Detail\n\n> ## Quote\n\n## Decisions\n\nNone.\n"
    parsed = propose_notes.parsed(text)
    assert isinstance(parsed, propose_notes.Notes)
    assert parsed.head == ("# Title", "", "### Detail", "", "> ## Quote", "")
    assert parsed.parts == (
        propose_notes.Part(heading="## Decisions", lines=("", "None.")),
    )


def test_a_subheading_separates_entries_in_one_notes_section() -> None:
    notes = (
        "## Seen, not filed\n"
        "The first finding has no decision.\n"
        "  ### More findings\n"
        "The second is minor; under: it is a typo.\n"
    )
    assert bare(notes) == ("The first finding has no decision.",)


def test_a_bar_call_needs_its_reason_on_its_line() -> None:
    first = "- The parser drops a line; under:"
    assert bare(with_line(f"{first}\n  See the report.")) == (first,)
    assert bare(with_line(f"{first}\n\nThe next finding.")) == (
        first,
        "The next finding.",
    )


def test_a_jev_ask_keeps_the_place_the_full_finding_and_the_first_line() -> None:
    first = "- `a.py:read` drops a line under Model X;"
    asked = propose_jev.line_asked((first, "  under: the owner never sees it"))
    assert asked == propose_jev.Asked(
        label=first,
        defect=items.Defect(
            where="a.py:read",
            title="`a.py:read` drops a line under Model X",
            what="`a.py:read` drops a line under Model X",
        ),
    )
    plain = propose_jev.line_asked(("A line drops; under: no data is lost",))
    assert plain is not None and plain.defect.where == ""


def test_a_jev_refusal_names_every_score_and_the_existing_decision_options() -> None:
    refused = propose_jev.refused("fix-the-login", {"a.md": 0.9, "b.md": 0.7})
    assert refusal_words(refused) == (
        "jev-over",
        (
            "2 finding(s) called under the bar, which Jev reads as over it at 0.7 or more: "
            '"a.md" (Jev: 0.90); "b.md" (Jev: 0.70)'
        ),
        (
            "look at the finding again: make its item `worth: later` (a commit, so lem land "
            "checks fix-the-login runs first), or keep `worth: no` with its `Decided against:` line, "
            "or keep the notes line `under:` with its reason; Jev is not asked again about it"
        ),
    )


def test_a_proposal_holds_only_for_the_actual_pull_and_push_on_the_tip() -> None:
    record = task("open", **OPENED)
    waiting = propose.holds(record, world(tip=OTHER, pull=SEEN))
    assert waiting == Due(step="propose", why="no pull request proposes this tip")
    unpushed = with_landing(record, pushed=OTHER)
    assert propose.holds(unpushed, world(pull=SEEN)) == Due(
        step="propose", why="the tip is not on the forge as Lem pushed it"
    )
    assert propose.holds(record, world(pull=replace(SEEN, head=OTHER))) == Due(
        step="propose", why="the pull request's head is not this tip"
    )
    assert propose.holds(record, world(pull=SEEN)) == Held(
        why="pull request 1 proposes this tip"
    )


def test_propose_refuses_all_notes_findings_with_no_bar_call_or_item() -> None:
    facts = Facts(notes=with_line("- One finding\n- Another finding"))
    refused = decided(full(), facts)
    assert refusal_words(refused) == (
        "no-bar-call",
        (
            "2 line(s) of the notes name a finding with no bar call and no item: "
            '"- One finding"; "- Another finding"'
        ),
        (
            "give it a bar call and a reason, or file it: by the bar of rule 6 of the "
            "builder's standing rules, the line ends with `under: REASON` or `cheap: REASON`, "
            "or a builder files it as an item of docs/backlog and the line names the item's "
            "path; then this step runs again"
        ),
    )


def test_propose_keeps_the_notes_the_owner_will_read() -> None:
    notes = Facts(notes="## Summary\n\nThe login works.\n")
    proposal = decided(small(), notes)
    assert isinstance(proposal, propose.Proposal)
    assert proposal.notes == propose_notes.Notes(
        parts=(
            propose_notes.Part(heading="## Summary", lines=("", "The login works.")),
        ),
    )


def test_propose_names_the_first_missing_item_and_counts_the_others() -> None:
    one = Filed(finding="r1.1", disposition="same", path="docs/backlog/first.md")
    two = Filed(finding="r1.2", disposition="item", path="docs/backlog/second.md")
    record = with_landing(full(), filed=(one, two))
    absent = decided(record)
    assert refusal_words(absent) == (
        "item-gone",
        "the item docs/backlog/first.md of the finding r1.1 was removed after it was filed, and 1 more",
        (
            "a builder puts it back with lem land file fix-the-login --again, then this "
            "step runs again; when the owner does not want it, the item stays with `worth: no` "
            "and his reason in it, never deleted"
        ),
    )


def test_an_empty_code_block_in_the_notes_is_closed() -> None:
    parsed = propose_notes.parsed("```\n```")
    assert isinstance(parsed, propose_notes.Notes)


def test_the_review_of_a_careful_proposal_names_a_missing_reason() -> None:
    made = replace(REVIEWED, careful=True, careful_why="")
    record = with_landing(small(), reviews=(made,))
    assert propose_careful.review_call(record) == (
        "the review says so: no reason given",
    )
    bare = replace(record, task=replace(record.task, shape=None))
    assert propose_careful.why(bare, Facts()) == (
        "the review says so: no reason given",
    )


def test_backlog_reference_at_the_end_of_a_line_holds_the_whole_entry() -> None:
    line = "- The parser misses an edge case, held by docs/backlog/a-held-item.md"
    assert bare(with_line(f"{line}\n  See the report for its first case.")) == ()
    assert propose_lines.named("see docs/backlog/providerX: same defect") == (
        "docs/backlog/providerX",
    )


def test_the_two_missing_headings_are_named_in_order() -> None:
    notes = Facts(
        notes=FULL_NOTES.replace("## Decisions\n\nnone\n\n", "").replace(
            "## Worth a look\n\nnone\n\n", ""
        )
    )
    code, why, _ = refusal_words(decided(full(), notes))
    assert code == "notes-headings"
    assert why.startswith("the notes lack ## Decisions, ## Worth a look:")


def test_a_jev_item_keeps_both_paragraphs_when_it_has_no_location() -> None:
    item = items.BacklogItem(
        path="docs/backlog/login.md",
        title="Login loses a field",
        paragraphs=("First fact.", "Second fact."),
    )
    asked = propose_jev.item_asked(item)
    assert (asked.defect.where, asked.defect.what) == (
        "",
        "First fact.\n\nSecond fact.",
    )


def test_a_filing_gate_has_nothing_to_reopen_before_a_landing() -> None:
    record = task("ready")
    assert propose_filed.gone(record, Facts()) is None
    assert propose_filed.refuted(record, Facts()) is None


def test_a_single_missing_item_does_not_report_any_more() -> None:
    path = "docs/backlog/only.md"
    filed = Filed(finding="r1.1", disposition="item", path=path)
    record = with_landing(full(), filed=(filed,))
    code, why, _ = refusal_words(decided(record))
    assert code == "item-gone"
    assert why == f"the item {path} of the finding r1.1 was removed after it was filed"


def test_a_careful_plan_refusal_names_the_plan_talk() -> None:
    careful = full(plan=Plan(path="p.md", careful="a charge"))
    refused = decided(careful)
    assert refusal_words(refused)[1].startswith(
        "the plan says that the request is careful, so its defender and the reviewer talk"
    )


def test_the_shape_can_record_the_interview_before_its_span_exists() -> None:
    shape = Shape(type="feat", why="add the field", track="full", then="interview")
    record = full(shape=shape)
    criteria = replace(record.task.criteria, approvals=(approval("read"),))
    shaped = replace(record, task=replace(record.task, criteria=criteria))
    assert code_of(decided(shaped)) == "interview-unapproved"


def test_a_complete_request_from_the_owner_needs_no_second_approval() -> None:
    shape = Shape(type="feat", why="add the field", track="full", someone_else=False)
    record = full(shape=shape)
    criteria = replace(record.task.criteria, approvals=(approval("read"),))
    given = replace(record, task=replace(record.task, criteria=criteria))
    assert isinstance(decided(given), propose.Proposal)


def test_a_branch_protection_refusal_names_the_push_it_stops() -> None:
    rule = Rules(base="main", commands=("true",), protected=("docs/fix-the-login",))
    refused = refusal_words(decided(small(), SMALL_NOTES, rules=rule))
    assert refused[:2] == (
        "protected",
        "docs/fix-the-login is in branch.protected of .lem/settings.toml: Lem pushes nothing",
    )


def skip_word(record: Record, *, now: datetime = MOMENT) -> Record:
    return replace(record, task=skip.skipped(record.task, "yes", now))


def owner_approval(record: Record, *, now: datetime = MOMENT) -> Record:
    criteria = record.task.criteria
    sheet = Sheet(
        size="full",
        why="the ticket names the word and the file",
        criteria=criteria.criteria,
        digest="d1",
    )
    return approve.approved(
        record, asked=approve.Asked(by="owner", sheet=sheet, plan=True), now=now
    )


def lead_start(record: Record) -> Record:
    lead = span_forms.Given(name="lead", edge="start", by="session")
    return spans.started(record, lead, MOMENT)


@pytest.mark.parametrize(
    "order",
    [
        (owner_approval, lead_start, skip_word),
        (skip_word, lead_start, owner_approval),
        (lead_start, skip_word, owner_approval),
    ],
    ids=["approval before skip", "lead before approval", "lead before skip"],
)
def test_a_skip_cannot_move_past_prior_acts_at_the_same_moment(
    order: tuple[Callable[[Record], Record], ...],
) -> None:
    record = full()
    criteria = replace(record.task.criteria, reads=(), approvals=())
    record = replace(record, task=replace(record.task, criteria=criteria))
    for act in order:
        record = act(record)
    assert code_of(decided(record)) == "skip-late"


def test_a_skip_and_approval_before_the_lead_count_at_the_same_moment() -> None:
    record = full()
    criteria = replace(record.task.criteria, reads=(), approvals=())
    record = replace(record, task=replace(record.task, criteria=criteria))
    approved = owner_approval(skip_word(record))
    assert approved.task.criteria.skip_at == MOMENT
    assert isinstance(decided(lead_start(approved)), propose.Proposal)


def test_an_owner_approval_before_the_skip_does_not_answer_it() -> None:
    record = full()
    criteria = replace(record.task.criteria, reads=(), approvals=())
    record = replace(record, task=replace(record.task, criteria=criteria))
    approved = owner_approval(record)
    skipped = skip_word(approved, now=LATER)
    assert code_of(decided(skipped)) == "skip-unapproved"
