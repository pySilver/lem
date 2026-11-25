"""Template behavior that depends on the typed inputs, including empty states and forms."""

from pathlib import Path
from typing import TYPE_CHECKING

import msgspec
import pytest

from fixtures.board import columns, frame, panel, shelves, waiting
from fixtures.board.moments import BASE, NOW
from lem.board.inputs.activity import Activity, Happened, Lane, NewTask, Stretch, Tick
from lem.board.inputs.forms import ActForm, Choice, Field, TextBox
from lem.board.inputs.layout import Viewer
from lem.board.inputs.page import Page
from lem.board.inputs.parts import Document, Link, Note, When
from lem.board.inputs.sidebar import Notice
from lem.board.inputs.switcher import Box, Failure, Workspaces
from lem.board.inputs.task.artifacts import Artifacts, Body, Doc, Folder, Section, Shown
from lem.board.inputs.task.cards import Asked, Breaker, Picture, Shot
from lem.board.inputs.task.checks import Checks
from lem.board.inputs.task.criteria import Approve
from lem.board.inputs.task.decisions import Criteria, Decision, Part
from lem.board.inputs.task.head import Fact
from lem.board.inputs.task.overview import Answered, Pruned
from lem.board.inputs.task.panel import Missing, Panel
from lem.board.inputs.task.steps import Card, Confirm, Drop, NotNow, Park
from lem.board.inputs.task.timeline import Mark, Spell, Time, Timeline, Track
from lem.board.inputs.tasks import Ended, Older
from lem.board.pages import printing, render
from unit.board.pages.markup import Parsed
from unit.board.pages.test_showcase import for_view

if TYPE_CHECKING:
    from unit.board.pages.markup import Node

REFUND = f"{BASE}/tasks/refund-line-on-receipt"
STAMP = When(at=NOW, shown="16:00")
BACK = Link(href=f"{BASE}/", label="Back to Tasks")
TASK_LINK = Link(href=REFUND, label="Refund line on receipt")
HAPPENED = Happened(
    id="moved",
    look="lead",
    icon="play",
    task=TASK_LINK,
    head="Started the build",
    at=STAMP,
)
SOURCE = "docs/backlog/fix special & cases.md"
MALICIOUS = '<img src=x onerror="bad()">&'
COPY = "Copy path"
FORM = ActForm(
    action=f"{BASE}/tasks",
    label="Start a task",
    icon="plus",
    busy="Starting…",
    box=TextBox(name="words", id="new-words", rows=4, required=True, longest=100),
)

ACTIVITY = Activity(
    day="today",
    ticks=(Tick(left=0, clock="14:00"), Tick(left=50, clock="16:00")),
    now=75.0,
    events="Two events.",
    lanes=(
        Lane(
            slug="refund-line-on-receipt",
            task=TASK_LINK,
            stretches=(
                Stretch(
                    left=12.0,
                    width=14.0,
                    look="lead",
                    status="building",
                    title="Build · 14:00 to 14:30",
                ),
                Stretch(
                    left=27.0,
                    width=0.0,
                    look="ok",
                    status="ready",
                    dot=True,
                    title="Ready at 14:30",
                ),
            ),
        ),
    ),
    feed=(HAPPENED, msgspec.structs.replace(HAPPENED, id="global", task=None)),
)
TIMELINE = Timeline(
    time=Time(
        look="lead",
        whole="8h in all",
        day="today",
        now=75.0,
        tracks=(
            Track(
                key="lead",
                label="The lead",
                fill="var(--lead)",
                held="5m",
                spells=(
                    Spell(
                        id="now-work",
                        left=12.0,
                        width=14.0,
                        head="Build",
                        live=True,
                        start=NOW,
                    ),
                ),
                marks=(Mark(id="one-mark", left=27.0, head="Ready", at=NOW),),
            ),
        ),
    ),
    events="One event.",
    feed=(HAPPENED,),
)


def read(board: Page, template: str = "page.html") -> Node:
    return Parsed(render.section(template, board)).root


def task(**parts: object) -> Node:
    task_panel = msgspec.structs.replace(
        panel.OPEN, **(({"overview": None} | parts) if "shows" in parts else parts)
    )
    return read(
        Page(frame=frame.FRAME, tasks=columns.TASKS, panel=task_panel), "fragment.html"
    )


def test_activity_and_timeline_link_tasks_and_expose_live_spans_and_points() -> None:
    board = read(Page(frame=for_view("activity", "Activity"), activity=ACTIVITY))
    assert board.one(cls="tl-label").attrs["href"] == REFUND
    assert board.one(id_="moved").one(tag="a").attrs["href"] == REFUND
    assert not board.one(id_="global").all(tag="a")
    assert board.one(cls="tl-seg").attrs["aria-label"] == "Build · 14:00 to 14:30"
    assert board.one(cls="tl-dot").attrs["tabindex"] == "0"
    grid = board.one(cls="tl-grid")
    assert [tick.attrs["style"] for tick in grid.all(tag="i")] == [
        "left:0%;",
        "left:50%;",
    ]
    assert grid.one(cls="tl-now").attrs["style"] == "left:75.0%"
    assert board.one(id_="events").one(tag="h2").words() == "Activity"
    timeline = task(shows="timeline", timeline=TIMELINE)
    assert timeline.one(cls="tl-note").words().startswith("Each row")
    assert timeline.one(id_="tt").one(cls="tip").attrs["role"] == "tooltip"
    assert timeline.one(id_="events").one(tag="h2").words() == "Activity"
    assert timeline.one(id_="now-work").attrs["data-to"] == "now"
    mark = timeline.one(id_="one-mark")
    assert (
        mark.attrs["data-from"]
        == mark.attrs["data-to"]
        == str(printing.milliseconds(NOW))
    )
    assert mark.attrs["tabindex"] == "0"


def test_artifacts_display_the_file_and_copy_its_path() -> None:
    photo = Picture(
        src=f"{REFUND}/media/view.png", href=f"{REFUND}/media/view.png", alt="View"
    )
    doc = Doc(
        id="file-special",
        path=SOURCE,
        icon="file",
        title="The file",
        href=f"{REFUND}/artifacts/doc",
    )
    body = Body(where=SOURCE, picture=photo, text=MALICIOUS)
    shown = Shown(
        path=SOURCE,
        title=doc.title,
        kind="image",
        icon=doc.icon,
        meta="image",
        body=body,
    )
    tab = Artifacts(
        sections=(Section(key="request", name="The request", docs=(doc,)),),
        work=(Folder(id="pictures", name="Pictures", docs=(doc,), open=True),),
        shown=shown,
        chosen=True,
        said="Two documents",
    )
    board = task(shows="artifacts", artifacts=tab)
    assert board.one(id_="pictures").tag == "details"
    assert "open" in board.one(id_="pictures").attrs
    assert board.one(tag="img").attrs["alt"] == "View"
    assert board.one(tag="pre").raw() == MALICIOUS
    copy = [
        button
        for button in board.all(tag="button")
        if button.attrs.get("title") == COPY
    ]
    assert copy[0].attrs["data-copy-text-value"] == SOURCE
    assert board.one(id_="arts").attrs["data-artifacts-task-value"] == panel.SLUG
    assert board.one(id_="arts").has("show-file")
    assert board.one(cls="av-back").words() == "The files"
    assert board.one(cls="av-back").attrs["href"] == f"{REFUND}/artifacts"
    group = board.one(id_="ag-request")
    assert group.tag == "details" and "open" in group.attrs
    assert group.one(tag="summary").one(tag="em").words() == "1"
    assert group.one(id_=doc.id)


def test_artifacts_html_uses_a_sandbox_and_exposes_the_standalone_link() -> None:
    raw = f"{REFUND}/raw/view.html"
    shown = Shown(
        path="view.html",
        title="View",
        kind="html",
        icon="file-code",
        meta="HTML",
        body=Body(where="view.html", frame=raw),
        alone=raw,
    )
    board = task(
        shows="artifacts",
        artifacts=Artifacts(
            sections=(), shown=shown, said="One file", chosen=True, wide=True
        ),
    )
    assert board.one(id_="panel").has("page-open")
    assert board.one(id_="arts").has("wide")
    assert board.one(cls="av-back").words() == "The files"
    assert board.one(tag="iframe").attrs == {
        "class": "art-html",
        "src": raw,
        "title": "View",
        "sandbox": "allow-scripts allow-popups allow-popups-to-escape-sandbox",
    }
    assert any(
        link.attrs.get("href") == raw and link.attrs.get("target") == "_blank"
        for link in board.all(tag="a")
    )


def test_artifacts_document_keeps_its_id_and_escaped_source() -> None:
    doc = Document(
        id="md-plan-first", text=f"{MALICIOUS}\n</template>", media=f"{REFUND}/media/"
    )
    board = read(
        Page(
            frame=frame.FRAME,
            tasks=columns.TASKS,
            panel=msgspec.structs.replace(
                panel.OPEN,
                shows="artifacts",
                overview=None,
                artifacts=Artifacts(
                    sections=(),
                    said="One document",
                    shown=Shown(
                        path="plan.md",
                        title="Plan",
                        kind="markdown",
                        icon="file",
                        meta="markdown",
                        body=Body(where="plan.md", document=doc),
                    ),
                ),
            ),
        ),
        "fragment.html",
    )
    node = board.one(id_=doc.id)
    assert node.attrs["data-keep"] == doc.id
    assert node.attrs["data-markdown-media-value"] == doc.media
    assert node.one(tag="template").raw() == doc.text
    assert not node.all(tag="img")


def test_an_older_row_opens_the_task_and_an_external_pull_request() -> None:
    board = read(
        Page(
            frame=for_view("done", "Older tasks"),
            older=Older(
                newer=BACK,
                rows=(
                    Ended(
                        slug=panel.SLUG,
                        href=f"{REFUND}?in=done",
                        title="Refund line on receipt",
                        label="Landed",
                        icon="check",
                        look="done",
                        ended=STAMP,
                    ),
                ),
            ),
        )
    )
    assert (
        board.one(id_=f"older-{panel.SLUG}")
        .one(cls="wr-verb")
        .attrs["data-turbo-frame"]
        == "task"
    )
    assert board.one(cls="older-back").attrs["href"] == BACK.href
    assert board.one(id_="older-view").has("scroll")
    assert board.one(id_="older").one(tag="h2").words() == "Older tasks"


def test_new_task_provides_words_and_cancel_or_no_form() -> None:
    for form in (FORM, None):
        board = read(
            Page(frame=for_view("new", "New task"), new=NewTask(form=form, cancel=BACK))
        )
        new = board.one(id_="new-task")
        assert new.one(tag="a").attrs["href"] == BACK.href
        if form:
            assert new.one(tag="form").attrs["action"] == f"{BASE}/tasks"
            assert new.one(tag="textarea").attrs["maxlength"] == "100"
        else:
            assert not new.all(tag="form")
            assert "/lem" in new.words() and "in any session" in new.words()


def test_each_confirmation_and_card_draw_only_their_typed_action() -> None:
    confirm = Confirm(
        look="you",
        label="Read the step",
        eyebrow="Confirm",
        form=FORM,
        back=BACK,
        sheet=True,
    )
    park = task(
        shows="park",
        park=Park(confirm=confirm, what="The build stopped.", said="Work stays."),
    )
    dropped = task(
        shows="drop",
        drop=Drop(confirm=confirm, what="The build waits.", said="Work stops."),
    )
    card = task(
        shows="card",
        card=Card(
            confirm=msgspec.structs.replace(confirm, form=None),
            frame=f"{REFUND}/cards/a",
            title="A question",
            keep="card-a",
        ),
    )
    for parsed in (park, dropped):
        step = parsed.one(id_="confirm")
        assert step.attrs["data-controller"] == "sheet"
        assert step.one(cls="cf-body").attrs["data-sheet-target"] == "body"
        back = step.one(cls="cf-foot").one(tag="a")
        assert back.words() == "Back to Tasks"
        assert back.has("btn") and not back.has("cf-back")
    assert card.one(id_="card-step").attrs["data-keep"] == "card-a"
    assert card.one(id_="card-step").attrs["data-controller"] == "sheet"
    assert not card.one(id_="card-step").all(tag="form")
    assert card.one(tag="iframe").attrs["title"] == "A question"


def test_card_answer_keeps_the_frame_only_for_a_board_receipt() -> None:
    for keep in ("card-a", None):
        receipt = task(
            shows="card",
            not_now=NotNow(id="card-step", said="B was taken.", back=BACK, keep=keep),
        ).one(id_="card-step")
        if keep:
            assert receipt.attrs["data-keep"] == keep
        else:
            assert "data-keep" not in receipt.attrs


def test_merge_shows_the_bound_tip_and_each_reason_id() -> None:
    board = read(
        Page(frame=frame.FRAME, tasks=columns.TASKS, panel=panel.MERGE_STEP),
        "fragment.html",
    )
    step = board.one(id_="confirm")
    assert step.attrs["data-controller"] == "sheet"
    assert step.one(tag="form").attrs["action"] == f"{REFUND}/merge"
    assert {
        field.attrs["name"]: field.attrs["value"] for field in step.all(tag="input")
    } == {
        "tip": panel.TIP,
        "confirm": "yes",
    }
    back = step.one(cls="cf-foot").one(tag="a")
    assert back.has("btn") and not back.has("cf-back")
    assert (
        panel.MERGE.confirm.back and back.attrs["href"] == panel.MERGE.confirm.back.href
    )
    assert step.one(cls="cf-facts").all(tag="dt")[0].words() == "Pull request"
    assert step.one(id_="cf-reasons").one(id_="cf-r1")
    changed = msgspec.structs.replace(panel.MERGE, careful_why="Changed careful call.")
    assert (
        task(shows="merge", merge=changed)
        .one(id_="confirm")
        .attrs["data-sheet-key-value"]
        != step.attrs["data-sheet-key-value"]
    )
    confirm = panel.MERGE.confirm
    assert confirm.form
    new_tip = "a" * len(panel.TIP)
    fields = tuple(
        msgspec.structs.replace(field, shown=new_tip) if field.name == "tip" else field
        for field in confirm.form.fields
    )
    changed_tip = msgspec.structs.replace(
        panel.MERGE,
        confirm=msgspec.structs.replace(
            confirm, form=msgspec.structs.replace(confirm.form, fields=fields)
        ),
    )
    next_step = task(shows="merge", merge=changed_tip).one(id_="confirm")
    assert next_step.attrs["data-sheet-key-value"] != step.attrs["data-sheet-key-value"]


def test_waits_stack_buttons_and_parked_row() -> None:
    board = read(Page(frame=for_view("waits", "Waits for you"), waits=waiting.WAITS))
    stack = board.one(cls="wstack")
    assert "open" not in stack.attrs
    assert len(stack.all(cls="wrow", tag="article")) == 2
    choices = [
        button for button in board.all(tag="button") if "formaction" in button.attrs
    ]
    assert choices and all(choice.attrs["formmethod"] == "get" for choice in choices)
    assert board.one(id_="parked").all(tag="details")
    assert board.one(id_="waits").all(cls="wi")


def test_backlog_filters_and_reply_forms_have_stable_ids_and_fields() -> None:
    board = read(Page(frame=for_view("backlog", "Backlog"), backlog=shelves.BACKLOG))
    assert (
        board.one(id_="bl-query").attrs["data-action"]
        == "input->backlog#filter keydown->backlog#clear"
    )
    for button in board.all(cls="fchip"):
        assert button.attrs["data-backlog-target"] == "chip"
        assert button.attrs["data-key"]
    reviewer = board.one(id_="group-reviewer")
    assert board.all(cls="bl-group")[0] is reviewer
    assert [row.attrs["id"] for row in reviewer.all(cls="bl-item")] == [
        f"item-{shelves.RECEIPT_ITEM.key}",
        f"item-{shelves.CHECK_ITEM.key}",
    ]
    assert len(reviewer.all(tag="form")) == 2
    assert all(
        form.one(tag="input").attrs["name"] == "item"
        for form in reviewer.all(tag="form")
    )
    assert board.one(id_="group-no").has("recessive")


def test_index_and_failure_escape_words_and_link_to_the_board() -> None:
    boxes = (
        Box(id="online", name=MALICIOUS, path=SOURCE, href=f"{BASE}/", waits=True),
        Box(id="offline", name="Another workspace", path=SOURCE),
    )
    board = Parsed(
        render.section(
            "workspaces.html",
            Workspaces(host="studio", ask="Two workspaces", boxes=boxes),
        )
    ).root
    assert board.one(id_="online").one(tag="a").raw() == MALICIOUS
    assert not board.one(id_="offline").all(tag="a")
    assert not board.all(tag="img")
    refused = Parsed(
        render.section("failure.html", Failure(title="Refused", said=MALICIOUS))
    ).root
    assert refused.one(tag="main").one(tag="p").raw() == MALICIOUS
    assert refused.one(tag="main").one(tag="a").attrs["href"] == "/"


def test_a_missing_task_has_its_own_panel_and_http_status() -> None:
    panel_input = Panel(
        slug="no-task",
        missing=Missing(title="No task", said="Missing", back=f"{BASE}/"),
    )
    board = Page(frame=frame.FRAME, tasks=columns.TASKS, panel=panel_input)
    assert render.page(board, fragment=True).status_code == 404
    root = read(board, "fragment.html")
    assert root.one(id_="tb-missing").words() == "Missing"
    assert root.one(cls="p-back").attrs["href"] == f"{BASE}/"


def test_inline_markdown_leaves_raw_html_as_text() -> None:
    card = columns.TASKS.columns[0].cards[0]
    lane = msgspec.structs.replace(
        columns.TASKS.columns[0],
        cards=(
            msgspec.structs.replace(
                card,
                title=MALICIOUS,
                line=f"{MALICIOUS} `code` [link](https://example.org) ![external](https://example.org/image.png)",
            ),
        ),
    )
    board = read(
        Page(
            frame=frame.FRAME,
            tasks=msgspec.structs.replace(columns.TASKS, columns=(lane,)),
        )
    )
    row = board.one(id_=f"card-{card.slug}")
    assert row.one(cls="tc-link").raw() == MALICIOUS
    assert not row.all(tag="img")
    assert row.one(tag="code").raw() == "code"
    assert any(
        link.words() == "link" and link.attrs["href"] == "https://example.org"
        for link in row.one(cls="tc-line").all(tag="a")
    )


@pytest.mark.parametrize(
    "bad", ["javascript:alert(1)", "//example.org", "/\\example.org", "\t//example.org"]
)
def test_address_refuses_unsafe_targets(bad: str) -> None:
    with pytest.raises(ValueError, match="relative address"):
        printing.address(bad)


def test_handover_has_the_shared_style_palette_and_no_inline_styles() -> None:
    root = Path(__file__).resolve().parents[4]
    assets = root / "skills" / "lem" / "assets"
    pattern = (assets / "handover.html").read_text(encoding="utf-8")
    assert pattern.count('<link rel="stylesheet" href="lem.css">') == 1
    assert pattern.count('<script src="lem.js"></script>') == 1
    assert "<style" not in pattern and ' style="' not in pattern
    shared = (assets / "lem.css").read_text(encoding="utf-8")
    board = (assets / "board.css").read_text(encoding="utf-8")
    assert ".doc .box {" in shared
    assert "--you: #" in shared and "--you: #" not in board
    assert all("--agterm-" not in text for text in (shared, board, pattern))


def test_handover_has_the_original_day_and_night_marks_in_order() -> None:
    root = Path(__file__).resolve().parents[4]
    pattern = (root / "skills/lem/assets/handover.html").read_text(encoding="utf-8")
    marks = ("lem-mark", "lem-mark-night")
    assert pattern.index("<!-- lem-mark:") < pattern.index("<!-- lem-mark-night:")
    for mark in marks:
        embedded = pattern.split(f"<!-- {mark}:", 1)[1].split(f"<!-- /{mark} -->", 1)[0]
        expected = (root / "assets" / f"{mark}.svg").read_text(encoding="utf-8")
        assert embedded.split("\n", 1)[1] == expected


def test_rail_and_panel_properties_show_the_values_from_the_viewer() -> None:
    viewer = Viewer(
        host="studio", workspace="shop", base=BASE, rail=True, full=True, width=530
    )
    changed = msgspec.structs.replace(frame.FRAME, viewer=viewer)
    board = read(Page(frame=changed, tasks=columns.TASKS, panel=panel.OPEN))
    assert board.one(id_="shell").has("railed")
    assert board.one(id_="side-fold").attrs["title"] == "Unfold the sidebar"
    assert board.one(id_="stage").has("full")
    assert board.one(id_="stage").attrs["style"] == "--pw: 530px"
    assert board.one(id_="p-more")


def test_panel_can_show_a_ticket_or_a_copyable_branch() -> None:
    ticket = Link(
        href="https://github.com/acme/shop/issues/3", label="Issue #3", out=True
    )
    head = msgspec.structs.replace(
        panel.HEAD,
        facts=(
            Fact(key="ticket", term="Ticket", link=ticket),
            Fact(
                key="branch",
                term="Branch",
                text="feat/the-branch",
                copy="feat/the-branch",
                mono=True,
            ),
        ),
    )
    board = task(head=head)
    ticket_link = board.one(id_="fact-ticket").one(tag="a")
    assert ticket_link.attrs["href"] == ticket.href
    assert ticket_link.attrs["rel"] == "noopener"
    assert (
        board.one(id_="fact-branch").one(tag="button").attrs["data-copy-text-value"]
        == "feat/the-branch"
    )
    assert not task(head=msgspec.structs.replace(head, facts=())).all(id_="fact-branch")


def test_checks_only_link_to_a_log_when_the_input_has_one() -> None:
    commands = panel.CHECKS.commands
    tab = msgspec.structs.replace(
        panel.CHECKS,
        commands=(
            commands[0],
            msgspec.structs.replace(commands[1], output=None),
        ),
    )
    board = task(shows="checks", checks=tab)
    assert (
        board.one(id_="gate-0").one(tag="a").attrs["href"]
        == f"{REFUND}/artifacts/gate/01.log/"
    )
    assert not board.one(id_="gate-1").all(tag="a")


def test_decision_disclosures_keep_the_story_votes_and_breaker_link() -> None:
    target = Link(
        href=f"{REFUND}/artifacts/breaker.md", label="Breaker document", frame=True
    )
    breaker = Decision(
        kind="breaker",
        id=3,
        look="you",
        what="Build stopped",
        chose="Stop",
        who="Lem",
        parts=(Part(label="Its files", links=(target,)),),
    )
    no_file = msgspec.structs.replace(breaker, id=4, parts=())
    criteria = msgspec.structs.replace(
        panel.CRITERIA, decisions=(*panel.CRITERIA.decisions, breaker, no_file)
    )
    board = task(shows="criteria", criteria=criteria)
    assert "open" in board.one(id_="dec-1").attrs
    assert "open" not in board.one(id_="dec-2").attrs
    assert board.one(id_="dec-1").one(cls="story").all(tag="li")
    decision = board.one(id_="dec-1")
    assert "a line of its own" in decision.one(cls="taken").words()
    assert "the developer picked B" in decision.words()
    assert board.one(id_="breaker-3").one(tag="a").attrs["href"] == target.href
    assert not board.one(id_="breaker-4").all(tag="a")


@pytest.mark.parametrize("before", [True, False], ids=("pair", "after-only"))
def test_overview_shows_both_matching_pictures_or_the_one_it_has(
    *, before: bool
) -> None:
    first = Picture(
        src=f"{REFUND}/media/page-before.png",
        href=f"{REFUND}/media/page-before.png",
        alt="Old",
    )
    last = Picture(
        src=f"{REFUND}/media/page-after.png",
        href=f"{REFUND}/media/page-after.png",
        alt="New",
    )
    building = panel.OVERVIEW.building
    assert building
    changed = msgspec.structs.replace(
        building,
        shots=(
            Shot(
                id="pair", caption="Page", before=first if before else None, after=last
            ),
        ),
    )
    overview = msgspec.structs.replace(panel.OVERVIEW, building=changed)
    pair = task(overview=overview).one(id_="pair")
    pictures = [image.attrs["alt"] for image in pair.all(tag="img")]
    assert pictures == (["Old", "New"] if before else ["New"])
    assert pair.all(tag="a")[-1].attrs["href"] == last.href


def test_notice_only_links_when_the_input_names_a_task() -> None:
    sidebar = msgspec.structs.replace(
        frame.FRAME.sidebar,
        notices=(
            *frame.FRAME.sidebar.notices,
            Notice(
                id="notice-blocked",
                kind="blocked",
                said="Blocked",
                task=REFUND,
                task_title="Refund",
            ),
            Notice(id="notice-unknown", kind="unknown", said="Unreadable"),
        ),
    )
    board = read(
        Page(
            frame=msgspec.structs.replace(frame.FRAME, sidebar=sidebar),
            tasks=columns.TASKS,
        )
    )
    assert board.one(id_="notice-blocked").one(tag="a").attrs["href"] == REFUND
    assert not board.one(id_="notice-unknown").all(tag="a")
    assert "demo data" in board.one(cls="m-title").words()


def test_only_one_format_controls_every_view_key() -> None:
    board = read(Page(frame=frame.FRAME, tasks=columns.TASKS))
    expected = {"tasks": "KeyT", "waits": "KeyW", "backlog": "KeyB", "activity": "KeyA"}
    for view, key in expected.items():
        link = board.one(id_=f"view-{view}")
        assert link.attrs["data-hotkey"] == key
        assert link.one(tag="kbd").words().upper() == key[-1]
    stage = board.one(id_="stage")
    assert not stage.all(id_="kanban-keys")
    assert board.one(id_="kanban-keys").all(tag="kbd")
    assert len(board.all(id_="search")) == 1


def test_approval_keeps_its_note_terms_and_read_key() -> None:
    terms = Document(id="md-approval", text="Read this criterion.")
    approve = Approve(
        label="Approve the criteria",
        head="Read this",
        criteria=terms,
        plain=terms.text,
        form=FORM,
        back=BACK,
        sheet=True,
    )
    note = Note(look="you", icon="eye", said="The text changed.")
    ready = msgspec.structs.replace(panel.CRITERIA, approve=approve, note=note)
    tab = task(shows="criteria", criteria=ready)
    card = tab.one(id_="approve-criteria")
    assert card.one(cls="act-note").words() == note.said
    assert card.one(tag="noscript").raw() == terms.text
    assert card.one(cls="cf-body").attrs["data-sheet-target"] == "body"
    assert card.one(cls="cf-foot").one(tag="a").attrs["href"] == BACK.href
    changed = msgspec.structs.replace(
        approve, criteria=msgspec.structs.replace(terms, text="Another criterion.")
    )
    later = task(
        shows="criteria", criteria=msgspec.structs.replace(ready, approve=changed)
    )
    assert (
        later.one(id_="approve-criteria").attrs["data-sheet-key-value"]
        != card.attrs["data-sheet-key-value"]
    )
    readonly = msgspec.structs.replace(
        ready, approve=msgspec.structs.replace(approve, form=None)
    )
    passive = task(shows="criteria", criteria=readonly)
    assert "data-controller" not in passive.one(id_="approve-criteria").attrs
    assert not passive.one(id_="approve-criteria").all(cls="act-note")
    assert passive.one(cls="act-note").words() == note.said


def test_waits_links_to_the_card_criteria_and_merge_and_can_jump_to_a_local_session() -> (
    None
):
    local = msgspec.structs.replace(waiting.BREAKER, jump="terminal-id")
    first = msgspec.structs.replace(waiting.WAITS.stacks[0], waits=(local,))
    waits = msgspec.structs.replace(
        waiting.WAITS, stacks=(first, *waiting.WAITS.stacks[1:])
    )
    shown = msgspec.structs.replace(
        for_view("waits", "Waits for you"), keys=waiting.KEYS
    )
    tree = read(Page(frame=shown, waits=waits))
    verb = tree.one(id_=local.id).one(cls="wr-verb")
    assert verb.attrs["href"] == local.href
    assert verb.attrs["data-agterm-session-param"] == "terminal-id"
    assert (
        tree.one(id_="waits-list").attrs["data-cursor-item-value"]
        == "article.wrow, details.wstack"
    )
    assert tree.one(id_="waits-keys").all(tag="kbd")
    for wait in (waiting.ASKED, waiting.CRITERIA, waiting.MERGE):
        assert wait.acts and wait.acts.links
        assert wait.acts.links[0].href in [
            link.attrs["href"] for link in tree.one(id_=wait.id).all(tag="a")
        ]


def test_overview_links_to_the_card_artifacts_and_reason_and_shows_the_answer() -> None:
    asked = Asked(
        page="a-card",
        prompt="Which route?",
        since=STAMP,
        link=Link(
            href=f"{REFUND}/card/a-card",
            label="Read the card",
            frame=True,
        ),
    )
    overview = msgspec.structs.replace(
        panel.OVERVIEW,
        cards=(asked,),
        answered=Answered(took="You picked B", note="Use B."),
    )
    board = task(overview=overview)
    assert (
        board.one(id_="asked-a-card").one(tag="a").attrs["href"]
        == f"{REFUND}/card/a-card"
    )
    assert "You picked B" in board.one(id_="answered").words()
    assert (
        board.one(id_="merge-review").one(tag="a").attrs["href"]
        == f"{REFUND}/artifacts/merge-review.md/"
    )
    assert any(
        link.attrs.get("data-row") for link in board.one(id_="verdict").all(tag="a")
    )


def test_new_task_links_and_sidebar_waits_keep_their_targets() -> None:
    board = read(Page(frame=frame.FRAME, tasks=columns.TASKS))
    links = [
        link for link in board.all(tag="a") if link.attrs.get("data-hotkey") == "KeyN"
    ]
    assert [link.attrs["href"] for link in links] == [f"{BASE}/new", f"{BASE}/new"]
    link = board.one(id_=frame.FRAME.sidebar.waits[0].id)
    assert link.attrs["href"] == frame.FRAME.sidebar.waits[0].href
    assert link.attrs["data-turbo-frame"] == "task"


def test_backlog_links_to_held_and_source_tasks_and_can_read_again() -> None:
    reviewer = shelves.BACKLOG.shelves[0]
    entry = reviewer.entries[1]
    assert entry.added and entry.holds.held_by
    attribution = msgspec.structs.replace(
        entry.added, task=TASK_LINK, after=", in pull request #44"
    )
    shelf = msgspec.structs.replace(
        reviewer, entries=(msgspec.structs.replace(entry, added=attribution),)
    )
    backlog = msgspec.structs.replace(shelves.BACKLOG, shelves=(shelf,))
    board = read(Page(frame=for_view("backlog", "Backlog"), backlog=backlog))
    row = board.one(id_=f"item-{entry.key}")
    assert row.one(cls="bl-added").one(tag="a").attrs["href"] == REFUND
    assert (
        row.one(cls="bl-actions").one(tag="a").attrs["href"] == entry.holds.held_by.href
    )
    assert not row.all(tag="form")
    assert [
        link.attrs["href"]
        for link in board.all(tag="a")
        if link.attrs.get("data-hotkey") == "KeyR"
    ] == [backlog.read_again]


def test_a_review_round_can_link_to_its_artifact_and_keep_its_details() -> None:
    artifact = f"{REFUND}/artifacts/review.md"
    round_row = msgspec.structs.replace(
        panel.CHECKS.rounds[0], text=f"[Read its report]({artifact})"
    )
    tab = msgspec.structs.replace(panel.CHECKS, rounds=(round_row,))
    row = task(shows="checks", checks=tab).one(id_=round_row.id)
    assert row.one(tag="a").attrs["href"] == artifact
    assert row.one(cls="ev-sub").words() == round_row.subs[0]


def test_criterion_discloses_its_steps_tests_and_chart() -> None:
    criterion = panel.CRITERIA.criteria[0]
    assert criterion.chart and criterion.cases and criterion.tests
    board = task(shows="criteria", criteria=panel.CRITERIA)
    row = board.one(id_=criterion.id)
    assert row.tag == "details" and "open" not in row.attrs
    assert (
        row.one(id_=criterion.chart.id).one(tag="template").raw()
        == criterion.chart.text
    )
    assert row.one(tag="ol").all(tag="li")
    assert any(criterion.tests[0][0] in name.words() for name in row.all(tag="code"))


def test_breaker_card_has_its_document_and_artifact_link() -> None:
    text = Document(id="md-breaker", text="What the owner needs to read.")
    overview = msgspec.structs.replace(
        panel.OVERVIEW,
        breaker=Breaker(
            waits=True,
            head="The build stopped",
            why="The next step is irreversible",
            at=STAMP,
            document=text,
            artifact=Link(
                href=f"{REFUND}/artifacts/breaker.md", label="Read the breaker"
            ),
        ),
    )
    card = task(overview=overview).one(id_="breaker")
    assert card.one(id_=text.id).one(tag="template").raw() == text.text
    assert card.one(tag="a").attrs["href"] == f"{REFUND}/artifacts/breaker.md"


def test_panel_offers_the_merge_and_the_pull_request_links_from_its_head() -> None:
    head = task(head=panel.HEAD).one(id_="p-head")
    landing = head.one(cls="p-acts").one(tag="a")
    assert landing.attrs["href"] == f"{REFUND}/merge"
    assert landing.attrs["data-turbo-frame"] == "task"
    assert head.one(id_="fact-pr").one(tag="a").attrs["href"] == panel.PULL.href


def test_done_links_to_older_tasks_only_with_an_older_input() -> None:
    done = columns.TASKS.columns[-1]
    older = Link(href=f"{BASE}/done", label="Older tasks")
    for option in (older, None):
        changed = msgspec.structs.replace(done, older=option)
        tasks = msgspec.structs.replace(columns.TASKS, columns=(changed,))
        board = read(Page(frame=frame.FRAME, tasks=tasks))
        links = board.one(id_="col-done").all(cls="older-row")
        assert [link.attrs["href"] for link in links] == (
            [older.href] if option else []
        )


def test_timeline_event_renders_its_detail_as_a_line_below_it() -> None:
    detail = msgspec.structs.replace(HAPPENED, sub="The lead owns this work.")
    timeline = msgspec.structs.replace(TIMELINE, feed=(detail,))
    board = task(shows="timeline", timeline=timeline)
    assert board.one(id_=detail.id).one(cls="sub").words() == detail.sub


def test_plan_drop_posts_its_own_id_to_the_confirmation() -> None:
    original = waiting.BREAKER
    assert original.acts and original.acts.answer
    plan = original.acts.answer
    drop = Choice(
        option="drop",
        label="Drop…",
        icon="xmark",
        confirm=f"{REFUND}/drop",
        press="risk",
    )
    answer = msgspec.structs.replace(
        plan, fields=(Field(name="key", shown="plan-request"),), choices=(drop,)
    )
    row = msgspec.structs.replace(
        original,
        kind="plan",
        acts=msgspec.structs.replace(original.acts, answer=answer),
    )
    stack = msgspec.structs.replace(waiting.WAITS.stacks[0], waits=(row,))
    waits = msgspec.structs.replace(waiting.WAITS, stacks=(stack,))
    board = read(Page(frame=for_view("waits", "Waits for you"), waits=waits))
    form = board.one(id_=row.id).one(tag="form")
    assert form.one(tag="input").attrs["value"] == "plan-request"
    assert form.one(tag="button").attrs["formaction"] == drop.confirm
    assert form.one(tag="button").attrs["formmethod"] == "get"
    assert form.attrs["data-turbo-frame"] == "_top"
    assert form.one(tag="button").attrs["data-turbo-frame"] == "task"


def test_panel_posts_target_the_page_but_confirmation_reads_target_the_panel() -> None:
    reply = waiting.BREAKER.acts
    assert reply and reply.answer and panel.OPEN.overview
    choices = tuple(
        Choice(option=verb, label=verb, icon="xmark", confirm=f"{REFUND}/{verb}")
        for verb in ("park", "drop")
    )
    answer = msgspec.structs.replace(reply.answer, choices=choices)
    overview = panel.OPEN.overview
    ready = msgspec.structs.replace(
        overview, now=msgspec.structs.replace(overview.now, answer=answer)
    )
    parsed = task(overview=ready)
    form = parsed.one(id_=answer.id)
    assert form.attrs["data-turbo-frame"] == "_top"
    for button in form.all(tag="button"):
        assert button.attrs["data-turbo-frame"] == "task"
        assert button.attrs["data-turbo-action"] == "advance"
    merge = task(shows="merge", merge=panel.MERGE)
    assert merge.one(id_="confirm").one(tag="form").attrs["data-turbo-frame"] == "_top"


def test_workspace_search_and_phone_status_expose_their_controls() -> None:
    shown = msgspec.structs.replace(
        frame.FRAME,
        statusbar=msgspec.structs.replace(
            frame.FRAME.statusbar, problems=("Read error",)
        ),
    )
    root = read(Page(frame=shown, tasks=columns.TASKS))
    search = root.one(id_="search")
    assert search.one(tag="input").attrs["aria-controls"] == "search-list"
    assert search.one(id_="search-list").attrs["role"] == "listbox"
    assert [key.words() for key in search.one(id_="search-keys").all(tag="kbd")] == [
        "↑",
        "↓",
        "Enter",
        "Esc",
    ]
    assert root.one(id_="status").has("bad")


def test_empty_waits_and_workspaces_tell_the_owner_what_to_do() -> None:
    waits = msgspec.structs.replace(waiting.WAITS, stacks=())
    root = read(Page(frame=for_view("waits", "Waits for you"), waits=waits))
    assert "criteria to approve" in root.one(cls="wait-none").words()
    index = Parsed(
        render.section(
            "workspaces.html", Workspaces(host="studio", ask="No workspaces")
        )
    ).root
    assert [command.words() for command in index.all(tag="code")] == [
        "lem board",
        "lem serve add DIR",
    ]


def test_stale_backlog_location_is_visible_while_the_item_is_closed() -> None:
    frame_input = msgspec.structs.replace(
        for_view("backlog", "Backlog"), keys=shelves.KEYS
    )
    source = msgspec.structs.replace(shelves.FOOTER_ITEM, where_problem="File moved")
    shelf = msgspec.structs.replace(shelves.BACKLOG.shelves[1], entries=(source,))
    backlog = msgspec.structs.replace(shelves.BACKLOG, shelves=(shelf,))
    root = read(Page(frame=frame_input, backlog=backlog))
    row = root.one(id_=f"item-{source.key}")
    location = row.one(tag="summary").one(cls="bl-where")
    assert location.has("stale") and source.where in location.words()
    assert [key.words() for key in root.one(id_="backlog-keys").all(tag="kbd")] == [
        "/",
        "J",
        "K",
        "Enter",
        "R",
    ]


def test_pruned_overview_shows_now() -> None:
    assert panel.OPEN.overview
    pruned = Pruned(
        events="Earlier events", kept="Kept", went="Went", files="Files", artifacts=BACK
    )
    overview = msgspec.structs.replace(panel.OPEN.overview, pruned=pruned, phases=None)
    root = task(overview=overview)
    assert root.one(id_="pruned")
    assert root.one(id_="now").one(cls="now-head").words()


def test_ended_tabs_omit_the_empty_sibling_card() -> None:
    criteria = Criteria(decisions=panel.CRITERIA.decisions)
    root = task(shows="criteria", criteria=criteria)
    assert root.one(id_="decisions") and not root.all(id_="criteria")
    checks = Checks(commands=panel.CHECKS.commands)
    root = task(shows="checks", checks=checks)
    assert root.one(id_="checks-card") and not root.all(id_="review-card")
