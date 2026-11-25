"""The task's first line to the owner, composed by Lem from the typed record and the files of the
task's folder, in its own session's form and in another session's, with the commands that
correct the read (`FirstLine` of `main`'s `tests/unit/test_task.py`)."""

from datetime import date
from typing import TYPE_CHECKING

from msgspec.structs import replace

from fakes.records import MOMENT, record
from lem.app.tasks import first_line as saying
from lem.model.task import first_line, quotes
from lem.model.task.outcome import outcome_of
from lem.records.holds import OwnerHold
from lem.records.task import Shape, Task
from lem.records.tickets import Ticket
from lem.records.work import Investigation
from unit.task import spaces

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.task import TaskType, Then

FAST = "Fast track: one builder, the checks, one read, then the pull request."
WRONG_FAST = "Wrong read? /lem standard-track, /lem be-careful."
WRONG = "Wrong read? /lem be-careful."
AFTER = "After that it runs to the pull request without you."
CRITERIA = "## Acceptance criteria\n\nSize: small, because one word.\n\n1. {}\n"
NEXT = "\n\nThe picker keeps the same twenty tasks in its list.\n"
PICKER = "The picker keeps the same twenty tasks in its list"


def shaped(kind: TaskType, then: Then, **fields: object) -> Shape:
    """A read of the request: its type and what comes next."""
    return replace(Shape(type=kind, why="x", track="full", then=then), **fields)


def task(slug: str, ask: str, shape: Shape, **fields: object) -> Task:
    """A task with the owner's `ask` and its read."""
    return record(slug, ask=ask, shape=shape, **fields).task


def say(
    of: Task, read: first_line.Read | None = None, named: str | None = None
) -> str | None:
    """The task's first line, or None."""
    line = first_line.line_of(of, read or first_line.Read())
    return first_line.composed(line, named) if line else None


def present(said: str | None) -> str:
    """The line, which the case expects to be there."""
    assert said is not None
    return said


def test_the_fast_track_quotes_its_criterion() -> None:
    read = first_line.Read(
        criteria=CRITERIA.format("The README says receive, not recieve.")
    )
    readme = task(
        "readme-receive-typo",
        "fix the typo recieve in the README",
        shaped("docs", "fast"),
        status="building",
        branch="docs/readme-receive-typo",
    )
    assert say(readme, read) == (
        f'docs: "the README says receive, not recieve". Branch docs/readme-receive-typo. '
        f"{FAST} Nothing waits for you. {WRONG_FAST}"
    )


def test_the_fast_track_of_someone_elses_ticket_waits_for_his_yes() -> None:
    read = first_line.Read(criteria=CRITERIA.format("The footer says Terms."))
    footer = task(
        "shop-14-footer-terms",
        "SHOP-14",
        shaped("fix", "fast", someone_else=True),
        status="shaping",
        branch="fix/shop-14-footer-terms",
        ticket=Ticket(tracker="linear", id="SHOP-14"),
    )
    fast = f'fix: "the footer says Terms". Branch fix/shop-14-footer-terms. {FAST} '
    yes = (
        "Someone else wrote the request, so its criterion waits for your yes before the "
        "builder starts."
    )
    # with the owner there, his yes comes before the builder
    assert say(footer, read) == f"{fast}{yes} {WRONG_FAST}"
    # a builder that started without it leaves him the pull request
    assert say(replace(footer, status="building"), read) == (
        f"{fast}Nothing waits for you but the pull request, which calls you: you did not "
        f"approve its criterion. {WRONG_FAST}"
    )
    # queued behind another task, the wait comes first, then the steps, then his yes
    queued = replace(footer, status="queued", after="footer-text")
    assert (
        "It waits for footer-text, and starts when that task lands or is answered. Then "
        "the fast track: one builder, the checks, one read, then the pull request. "
        f"{yes}"
    ) in present(say(queued, read))


def test_the_standard_track_with_an_interview_quotes_the_outcome() -> None:
    read = first_line.Read(
        outcome=(
            "# Gift note\n\n## Outcome\n\nAn export holds the gift note. "
            "The shop reads it.\n\n## Done when\n\n- a row\n"
        )
    )
    note = task(
        "gift-note-in-export",
        "Add the gift note to the CSV export, Ania asked twice",
        shaped("feat", "interview"),
        status="shaping",
        branch="feat/gift-note-in-export",
    )
    assert say(note, read) == (
        'feat: "an export holds the gift note". Branch feat/gift-note-in-export. '
        "Standard track: an interview here now, then acceptance criteria for your yes. "
        f"{AFTER} {WRONG}"
    )


def test_a_plan_asked_for_says_so() -> None:
    plan = task(
        "gift-note",
        "/lem plan the gift note in the export",
        shaped("feat", "interview"),
        status="shaping",
        plan_only=True,
    )
    said = present(say(plan))
    assert (
        "Standard track, because you asked for its plan: an interview here now" in said
    )
    assert "After that a lead writes the plan and stops for you to read it." in said


def test_an_investigation_names_no_track() -> None:
    bug = task(
        "invoice-total-after-refund",
        "Invoices show 0 after a refund since yesterday. Anna saw it on 1042.",
        shaped("fix", "investigation"),
        status="building",
        branch="fix/invoice-total-after-refund",
    )
    assert say(bug) == (
        'fix: "invoices show 0 after a refund since yesterday". '
        "Branch fix/invoice-total-after-refund. An investigator finds the cause first. "
        "Then I tell you what it found: the fast track, the standard track, or no bug."
    )
    question = task("why-zero", "why 0?", shaped("question", "investigation"))
    assert present(say(question)).endswith(
        "An investigator finds the answer first. Then I tell you the answer."
    )
    found = Investigation(kind="question")
    asked = task("why", "why 0?", shaped("docs", "investigation"), investigation=found)
    assert present(say(asked)).endswith("Then I tell you the answer.")


def test_a_complete_request_names_what_stands_in_for_the_interview() -> None:
    export = task(
        "shop-12-export-the-gift-note",
        "Export the gift note",
        shaped("feat", "lead", someone_else=True),
        status="building",
        branch="shop-12-export-the-gift-note",
        ticket=Ticket(tracker="linear", id="SHOP-12"),
    )
    assert say(export) == (
        'feat: "export the gift note". Branch shop-12-export-the-gift-note. Standard '
        "track, with no interview, since the ticket says what is wanted: a lead writes "
        "acceptance criteria, the personas read them, and they wait for your yes. "
        f"{AFTER} {WRONG}"
    )
    item = replace(
        export,
        ticket=None,
        backlog_item="docs/backlog/x.md",
        shape=shaped("feat", "lead"),
    )
    assert (
        "since the backlog item says what is wanted: a lead writes acceptance criteria, "
        "and the personas read them."
    ) in present(say(item))
    report = first_line.Read(report=True)
    plain = replace(item, backlog_item=None)
    assert "since the investigation's report says" in present(say(plain, report))
    assert "since your request says" in present(say(plain))


def test_careful_comes_first() -> None:
    fee = task(
        "card-fee",
        "Round the card fee up",
        shaped("fix", "interview", careful=("this changes how a customer is charged",)),
        status="shaping",
    )
    assert present(say(fee)).startswith(
        'Careful: this changes how a customer is charged. fix: "round the card fee up".'
    )
    two = replace(
        fee, shape=shaped("fix", "interview", careful=("the fee", "the export."))
    )
    assert present(say(two)).startswith("Careful: the fee; the export. fix:")


def test_a_night_task_gets_none() -> None:
    night = task(
        "export-note",
        "docs/backlog/export-note.md",
        shaped("docs", "fast"),
        status="building",
        night=date(2026, 11, 25),
    )
    assert say(night) is None
    assert say(night, named="export-note") is None


def test_no_branch_yet_leaves_the_branch_out() -> None:
    note = task(
        "gift-note", "Add the gift note to the export", shaped("feat", "interview")
    )
    said = present(say(note))
    assert "Branch" not in said
    assert said.startswith('feat: "add the gift note to the export". Standard track:')


def test_the_line_needs_the_read_that_names_the_path_and_is_the_records() -> None:
    plain = record("gift-note", ask="Add the gift note", status="shaping").task
    assert say(plain) is None
    assert say(replace(plain, shape=Shape(type="feat", why="x", track="full"))) is None
    read = replace(plain, shape=shaped("feat", "interview"))
    # the line is the record's: asked again, it says the same, whatever the status
    assert say(read) == say(replace(read, status="building"))


def test_a_queued_task_says_what_it_waits_for() -> None:
    label = task(
        "note-on-label",
        "Put the gift note on the label too",
        shaped("feat", "fast"),
        status="queued",
        after="gift-note-in-export",
        branch="feat/note-on-label",
    )
    assert say(label) == (
        'feat: "put the gift note on the label too". Branch feat/note-on-label. It waits '
        "for gift-note-in-export, and starts when that task lands or is answered. Then "
        "the fast track: one builder, the checks, one read, then the pull request. "
        f"Nothing waits for you. {WRONG_FAST}"
    )


def test_a_task_queued_by_his_order_says_so_and_his_word_that_starts_it() -> None:
    slug = "tests-at-the-unit-level"
    ordered = task(
        slug,
        "After one-lem-parallel-landings: unit cases for the functions that are pure today",
        shaped("test", "interview"),
        status="queued",
        after="one-lem-parallel-landings",
        order="After one-lem-parallel-landings",
        branch="test/tests-at-the-unit-level",
    )
    assert say(ordered) == (
        'test: "after one-lem-parallel-landings: unit cases for the functions that are '
        'pure today". Branch test/tests-at-the-unit-level. It waits for '
        f'one-lem-parallel-landings, as you said; "start {slug} now" starts it before '
        "that. Then the standard track: an interview here, then acceptance criteria for "
        f"your yes. {AFTER} {WRONG}"
    )
    # the fast track's line puts his word in place of "Nothing waits for you"
    fast = present(say(replace(ordered, shape=shaped("test", "fast"))))
    assert (
        f'as you said; "start {slug} now" starts it before that. Then the fast track: '
        "one builder,"
    ) in fast
    assert "Nothing waits for you" not in fast
    # another session names the task in his word too
    lead = replace(ordered, shape=shaped("test", "lead"))
    assert (
        f'"start {slug} now" starts it before that. Then the standard track, with no '
        "interview,"
    ) in present(say(lead, named=slug))


def test_a_task_put_after_the_one_task_that_fits_says_which() -> None:
    fits = task(
        "notes-in-order",
        "when the gift note lands, keep the notes in their order",
        shaped("feat", "interview", fits=True),
        status="queued",
        after="gift-note-in-export",
        order='when the "gift note" lands',
    )
    assert (
        "It waits for gift-note-in-export, the one open task that fits \"when the 'gift "
        'note\' lands"; "start notes-in-order now" starts it before that.'
    ) in present(say(fits))


def held_for_his_order() -> Task:
    """The task held while he was away, since two open tasks fit "the gift note"."""
    return task(
        "export-notes-in-order",
        "/lem After the gift note: the export keeps the notes in their order",
        shaped("feat", "interview"),
        status="shaping",
        order="After the gift note",
        branch="feat/export-notes-in-order",
        hold=OwnerHold(on="order", line="the order waits for the owner", since=MOMENT),
    )


def test_a_task_held_for_his_order_gets_its_first_line_with_his_answer() -> None:
    held = held_for_his_order()
    read = first_line.Read(
        outcome="# Notes\n\n## Outcome\n\nThe export keeps the notes in their order.\n"
    )
    # the hold names no path: no line while he is away
    assert say(held, read) is None
    # his answer "after gift-note-in-export": queued, with his order kept
    answered = replace(held, hold=None, status="queued", after="gift-note-in-export")
    assert say(answered, read) == (
        'feat: "the export keeps the notes in their order". Branch '
        "feat/export-notes-in-order. It waits for gift-note-in-export, as you said; "
        '"start export-notes-in-order now" starts it before that. Then the standard '
        "track: an interview here, then acceptance criteria for your yes. "
        f"{AFTER} {WRONG}"
    )
    assert present(say(answered, read, named="export-notes-in-order")).startswith(
        'export-notes-in-order · feat: "the export keeps the notes in their order".'
    )


def test_no_order_gives_the_line_of_a_task_that_starts_at_once() -> None:
    read = first_line.Read(
        outcome="# Notes\n\n## Outcome\n\nThe export keeps the notes in their order.\n"
    )
    at_once = replace(held_for_his_order(), hold=None)
    assert say(at_once, read) == (
        'feat: "the export keeps the notes in their order". Branch '
        "feat/export-notes-in-order. Standard track: an interview here now, then "
        f"acceptance criteria for your yes. {AFTER} {WRONG}"
    )


def test_a_task_that_waits_by_a_need_says_the_wait() -> None:
    need = task(
        "notes-in-order",
        "After gift-note-in-export: the export keeps the notes in their order",
        shaped("feat", "interview"),
        status="queued",
        after="gift-note-in-export",
    )
    assert say(need) == (
        'feat: "after gift-note-in-export: the export keeps the notes in their order". '
        "It waits for gift-note-in-export, and starts when that task lands or is "
        "answered. Then the standard track: an interview here, then acceptance criteria "
        f"for your yes. {AFTER} {WRONG}"
    )
    bug = replace(need, shape=shaped("fix", "investigation"))
    assert (
        "starts when that task lands or is answered. Then an investigator finds the "
        "cause first."
    ) in present(say(bug))


def test_the_ask_is_quoted_without_the_lem_that_carried_it() -> None:
    carried = task(
        "notes-in-order",
        "/lem After the gift note: the export keeps the notes in their order",
        shaped("feat", "interview"),
    )
    said = present(say(carried))
    assert said.startswith(
        'feat: "after the gift note: the export keeps the notes in their order". '
        "Standard track:"
    )
    assert "/lem After" not in said


def test_another_session_names_the_task_and_its_commands() -> None:
    read = first_line.Read(criteria=CRITERIA.format("The footer says Terms."))
    footer = task(
        "footer-terms",
        "the footer says Terms, not Terms and Conditions",
        shaped("fix", "fast"),
        status="building",
        branch="fix/footer-terms",
    )
    assert say(footer, read, named="footer-terms") == (
        'footer-terms · fix: "the footer says Terms". Branch fix/footer-terms. '
        f"{FAST} Nothing waits for you. Wrong read? /lem standard-track footer-terms, "
        "/lem be-careful footer-terms."
    )
    assert present(say(footer, read)).endswith(WRONG_FAST)
    fee = task(
        "card-fee",
        "Round the fee",
        shaped("fix", "interview", careful=("this changes how a customer is charged",)),
        branch="fix/card-fee",
    )
    said = present(say(fee, named="card-fee"))
    assert said.startswith(
        "card-fee · Careful: this changes how a customer is charged. fix:"
    )
    assert said.endswith("Wrong read? /lem be-careful card-fee.")
    # the interview and the investigator's answer are the task's session's
    assert "Standard track: an interview in its own session now," in said
    bug = replace(fee, shape=shaped("fix", "investigation"))
    assert present(say(bug, named="card-fee")).endswith(
        "Then its session tells you what it found: the fast track, the standard track, "
        "or no bug."
    )


def test_the_backlog_items_title_is_quoted_before_the_ask() -> None:
    item = task("export-note", "docs/backlog/export-note.md", shaped("docs", "lead"))
    title = quotes.title_of(
        "<!-- x -->\n# The export keeps the note. Today it drops it.\n"
    )
    assert title == "The export keeps the note"
    read = first_line.Read(title=title)
    assert present(say(item, read)).startswith('docs: "the export keeps the note".')
    assert present(say(item)).startswith('docs: "docs/backlog/export-note.md".')


def test_said_reads_the_tasks_folder_and_the_item(tmp_path: Path) -> None:
    where = spaces.workspace(tmp_path / "repo")
    backlog = where.checkout / "docs" / "backlog"
    backlog.mkdir(parents=True)
    (backlog / "note.md").write_text("# The slip shows the note.\n", encoding="utf-8")
    shape = shaped("feat", "lead")
    made = spaces.made(
        where,
        "note",
        status="shaping",
        shape=shape,
        backlog_item="docs/backlog/note.md",
    )
    assert present(saying.said(where, made, named=False)).startswith(
        'feat: "the slip shows the note". Standard track, with no interview, since the '
        "backlog item says"
    )
    folder = where.state / "tasks" / "note"
    (folder / "task.md").write_text(
        "## Outcome\n\nThe slip shows the gift note.\n", encoding="utf-8"
    )
    assert present(saying.said(where, made, named=True)).startswith(
        'note · feat: "the slip shows the gift note".'
    )
    fast = replace(made, task=replace(made.task, shape=shaped("feat", "fast")))
    (folder / "criteria.md").write_text(CRITERIA.format("The slip says Note."))
    assert present(saying.said(where, fast, named=False)).startswith(
        'feat: "the slip says Note".'
    )


def test_an_outcome_in_bold_as_prompts_writing_asks() -> None:
    assert outcome_of(
        "## Outcome\n\n**A developer whose team keeps its work in GitHub Issues gives Lem "
        "an issue, and Lem reads it,\nworks it and reports on it the way it does a Linear "
        "ticket.**\n\nToday:\n\n1. step\n"
    ) == (
        "A developer whose team keeps its work in GitHub Issues gives Lem an issue, and "
        "Lem reads it, works it and reports on it the way it does a Linear ticket"
    )
    assert (
        outcome_of("## Outcome\n\n**The export keeps the gift note of each order.**\n")
        == "The export keeps the gift note of each order"
    )
    assert (
        outcome_of(
            "## Outcome\n\n**Today:**\n\n1. Invoice 1042 is 100 EUR.\n2. It shows 70.\n"
        )
        is None
    )
    assert (
        outcome_of(
            "## Outcome\n\nThe export keeps the gift note\nof each order. It shows on the "
            "slip.\n"
        )
        == "The export keeps the gift note of each order"
    )


def test_the_words_it_quotes() -> None:
    assert quotes.first_sentence("The footer says Terms.  It is wrong.") == (
        "The footer says Terms"
    )
    assert quotes.in_his_words("README says it") == "README says it"
    assert quotes.in_his_words("I see 0") == "I see 0"
    assert quotes.in_his_words("The footer") == "the footer"
    assert (
        quotes.criterion_of(
            "1. A refund lowers the total,\n   never below 0:\n   1. Invoice 1042\n"
        )
        == "A refund lowers the total, never below 0"
    )
    assert (
        outcome_of("## Outcome\n\n1. Invoice 1042 is 100 EUR.\n2. It shows 70.\n")
        is None
    )
    assert (
        outcome_of(
            "## Outcome\n\n**Today:**\n\n1. step\n\nThe invoice shows 70 EUR after the "
            "refund.\n"
        )
        == "The invoice shows 70 EUR after the refund"
    )
    assert outcome_of(
        "## Outcome\n\n**A merge from the board no longer holds the owner's other acts\n"
        "on the board.** It still merges under the task's own lock.\n\nToday:\n\n"
        "1. step\n"
    ) == ("A merge from the board no longer holds the owner's other acts on the board")
    assert (
        outcome_of(
            "## Outcome\n\n**What the owner sees after it:**\n\n1. step\n\nThe invoice "
            "shows 70 EUR after the refund.\n"
        )
        == "The invoice shows 70 EUR after the refund"
    )
    assert (
        outcome_of(
            "## Outcome\n\n**Today:** the invoice shows 100 EUR after the refund.\n\n"
            "The invoice shows 70 EUR after the refund.\n"
        )
        == "The invoice shows 70 EUR after the refund"
    )


def test_a_line_inside_a_fence_is_never_a_heading() -> None:
    quoted = "The board shows the outcome of each task in one line"
    for sample in (
        "```sh\n# make the folder\nmkdir -p out\n```\n",
        "~~~sh\n# make the folder\nmkdir -p out\n~~~\n",
        "1. Make the folder:\n\n   ```sh\n   # make it\n   mkdir -p out\n   ```\n",
        "````md\n```sh\n# a comment\n```\n# a heading of the sample\n````\n",
        "```sh\n# one\n```python\n# two\n```\n",
    ):
        assert (
            outcome_of(f"## Outcome\n\n{sample}\n{quoted}. It reads task.md.\n")
            == quoted
        ), sample
    assert outcome_of(f"## Outcome\n\n~~~\nx\n~~~\n\n## Notes\n\n{quoted}.\n") is None


def test_a_block_that_never_closes_hides_no_sentence_it_showed() -> None:
    quoted = "The board shows the outcome of each task in one line"
    for between in ("", "\n"):
        assert (
            outcome_of(
                "## Outcome\n\n```md\n```python\nprint(1)\n```\n"
                f"{between}```\n\n{quoted}. It reads task.md.\n"
            )
            == quoted
        ), repr(between)
    assert (
        outcome_of(f"## Outcome\n\n```sh\nmkdir -p out && cp a b\n\n{quoted}.\n")
        is None
    )
    assert outcome_of(f"## Outcome\n\n{quoted}.\n\n```sh\nmkdir -p out\n") == quoted


def test_a_bold_outcome_is_quoted_whole() -> None:
    assert (
        outcome_of(
            "## Outcome\n\n**The brief names the Lem that is\ninstalled when it starts.**\n"
        )
        == "The brief names the Lem that is installed when it starts"
    )
    assert outcome_of(
        "## Outcome\n\n**Done shows at most the 20 newest ended tasks, and one row at its "
        "foot leads to the rest.**\n\nThe rest stay in the backlog.\n"
    ) == (
        "Done shows at most the 20 newest ended tasks, and one row at its foot leads to "
        "the rest"
    )
    assert (
        outcome_of(
            "## Outcome\n\n**Today:**\nThe invoice shows 100 EUR after the refund.\n"
        )
        == "The invoice shows 100 EUR after the refund"
    )
    assert outcome_of("## Outcome\n\n**Today:** it shows 100.\n\n1. step\n") is None


def test_only_the_marks_of_a_bold_run_leave_the_quote() -> None:
    assert outcome_of(
        "## Outcome\n\nWhen the Outcome is one bold sentence, the first line quotes it, "
        "without the `**` marks. A label is no quote.\n"
    ) == (
        "When the Outcome is one bold sentence, the first line quotes it, without the "
        "`**` marks"
    )
    assert (
        outcome_of(
            "## Outcome\n\n**The check reads `src/**/*.py` and\npasses `**kwargs` on.**\n"
        )
        == "The check reads `src/**/*.py` and passes `**kwargs` on"
    )


def test_a_code_span_among_the_first_words_makes_no_label() -> None:
    assert (
        outcome_of(
            "## Outcome\n\n**Lem reads `**/*.md` and\nquotes each file once.**\n"
        )
        == "Lem reads `**/*.md` and quotes each file once"
    )
    assert (
        outcome_of("## Outcome\n\n**Pass `**kwargs` on to the handler every time.**\n")
        == "Pass `**kwargs` on to the handler every time"
    )
    assert outcome_of("## Outcome\n\n**Today:** `**` shows 100.\n\n1. step\n") is None


def test_a_bold_label_or_a_rule_is_no_quote() -> None:
    for outcome in (
        "**Before and after the change:**\n\nThe invoice shows 70 EUR after the refund.\n",
        "**Before and after the change**:\nThe invoice shows 70 EUR after the refund.\n",
        "***\nThe invoice shows 70 EUR after the refund.\n",
    ):
        assert (
            outcome_of("## Outcome\n\n" + outcome)
            == "The invoice shows 70 EUR after the refund"
        ), outcome


def test_a_short_bold_phrase_with_a_word_after_it_opens_the_outcome() -> None:
    assert (
        outcome_of(
            "## Outcome\n\n**Done** shows the 20 newest ended tasks, and one row leads to "
            "the rest." + NEXT
        )
        == "Done shows the 20 newest ended tasks, and one row leads to the rest"
    )
    assert (
        outcome_of(
            "## Outcome\n\n**Lem board** `--follow` opens the task that waits." + NEXT
        )
        == "Lem board `--follow` opens the task that waits"
    )


def test_a_short_bold_label_stays_a_label() -> None:
    for label in (
        "**Today**\n\n1. The owner opens the board.",
        "**Today**, the landing of merge-leaves-board-lock:",
        "**Today** - the footer says 2025.",
        "**Before.** The invoice shows 100 EUR after the refund.",
        "**1.** The owner opens the board.",
        "**Today:** the footer says 2025.",
        "**Today**: the footer says 2025.",
    ):
        assert outcome_of("## Outcome\n\n" + label + NEXT) == PICKER, label


def test_the_wrapped_line_of_a_step_is_no_quote() -> None:
    story = (
        "## Outcome\n\n**Today**\n\n"
        '1. The owner is on the board\'s "Tasks" view.\n'
        "2. A parked task is not on the view at all: he\n"
        '   goes to "Waits for you" or gives up.\n\n'
        "**After**\n\n1. He presses `Cmd-K`.\n"
    )
    assert outcome_of(story) is None
    assert outcome_of(story + NEXT) == PICKER
    for steps in (
        '- A parked task is not on the view at all: he\n  goes to "Waits for you" or gives up.\n',
        '1. A parked task is not on the view.\n\n   He goes to "Waits for you" or gives up.\n',
        '1. A parked task is not on the view at all: he\ngoes to "Waits for you" or gives up.\n',
    ):
        assert outcome_of("## Outcome\n\n" + steps + NEXT) == PICKER, steps


def test_a_block_after_a_step_ends_it_as_markdown_reads_it() -> None:
    for outcome in (
        "1. The owner opens the refund.\n\n " + NEXT.strip() + "\n",
        "- The owner runs the command.\n```\nlem board\n```\n" + NEXT.strip(),
        (
            "**Before** the refund | **After** the refund\n--- | ---\n"
            "| 100 EUR | 80 EUR |\n" + NEXT
        ),
    ):
        assert outcome_of("## Outcome\n\n" + outcome) == PICKER, outcome
    assert (
        outcome_of(
            "## Outcome\n\n- The owner runs the command:\n\n  ```\n  lem board\n  ```\n\n"
            "  It opens the board.\n"
        )
        is None
    )
