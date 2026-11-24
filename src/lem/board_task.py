"""The board of one task, as HTML: its panel, with its header and its five tabs, from
the model.

    task_page(ctx)     /HOST/WORKSPACE/tasks/SLUG[/TAB][/ARTIFACT/]   the view under the panel, with the panel open
    frame_page(ctx)                                                    the panel alone, for a request of its frame

The panel lies in `<turbo-frame id="task">` beside the kanban or over a list
(`lem_board_pages.layout`). A link of the panel changes the frame and the address
(`data-turbo-action="advance"` on the frame), so the address is always the task, its tab
and its artifact, and a refresh renders the same panel: Turbo morphs it, and each
repeated part has a stable `id`, so a morph keeps the tab's scroll, the opened decisions
(`<details>`, whose `open` the browser keeps) and the artifact.

The header: the status with its time, the title, the ask, the facts as a definition list
(the type and the track, careful and why, what it waits for, the branch, the pull
request, the session that leads it, the times), and the chips; on a phone, and in a
window too short for them, the ask, the facts and the chips fold under "Details" behind
one key line, the pull request with green or not green or what the task waits for. The
tabs: "Overview" (what we are building, the outcome of task.md as markdown with its
story, its chart and its pictures, a before and an after side by side; green or not
green with each reason a row; what runs now and where the owner answers; the phases),
"Criteria and decisions" (the plan's chart, each criterion with its case and its chart,
and each decision with its story: the case, why it could happen, this or that, who took
it, its chart; an important one open at first), "Checks and review" (each command with
its output, the rounds, the proposal's reasons as rows), "Timeline" (who held the work,
drawn as lanes of HTML from `lem_board_model.time_of`, and the task's events) and
"Artifacts" (the task's map, the same seven sections in every project, and the file
opened: markdown that the browser renders from the escaped text in a `<template>`, a
record with the tab that shows it readable, JSON lines, a log without its colors, a
picture, an HTML page in a sandboxed frame from the server's raw route, the whole width,
and the panel's height with the header folded). Every pull request a line names is a
link. The words are the model's.

A task whose events became one summary (`lem project prune`, past `state.keep_days`) has
the same header, and its Overview opens with a card that says so, with what the summary
keeps and what its folder holds, as the folder says it now (`folder_of`): its small
record, and that its other files left by the rule of `state.keep_days`, with the number
as the settings give it now; or, while files beyond the record are still there, only how
many. "Criteria and decisions", "Checks and review" and "Timeline" each say in one line
that their detail went with the events (`summary_card`, `files_line`, `went_tab`).

Each task lives in its own agterm session. The jump to it has its button only on a page
for this Mac (`Ctx.local`, the agterm controller), and only while the session lives; a
task with no live session has "Open a session" in its header on every page that may act,
which the server answers with `lem session open` (serve.py `act_session`). While the
owner's mark says away and the board's server sent a thing of the task to his Inbox, the
line of where he answers names both places, the task's session on the Mac and the Inbox,
with a link to the task's thread at the Inbox's tailnet address; with no link, it says
why (`inbox_action`).
"""  # noqa: E501 - the table of the pages and their addresses keeps its columns

import hashlib
import json
import re
from pathlib import Path
from types import ModuleType
from typing import Any, cast
from urllib.parse import quote

from lem import answers as lem_answers
from lem import artifacts as lem_artifacts
from lem import board_model as bm
from lem import board_pages as P  # noqa: N812 - the pages module, named on 148 lines of this file
from lem import cards as lem_cards
from lem.markup import Markup, h, join, page

# The tabs of a task, with their names and their keys.
TABS = [
    ("overview", "Overview"),
    ("criteria", "Criteria and decisions"),
    ("checks", "Checks and review"),
    ("timeline", "Timeline"),
    ("artifacts", "Artifacts"),
]
TAB = dict(TABS)
# The steps of the board's acts that ask first, each a page of the panel at
# /tasks/SLUG/ACT, whose form posts the act (serve.py `board_act`): a merge's confirm
# step, a park with its one line of why, and a drop with the owner's note, whose Confirm
# posts his Drop to the answer route (serve.py `act_answer`).
ACT_TABS = {"merge": "Merge", "park": "Park", "drop": "Drop"}
# How a note of an act's result reads (serve.py `NOTES`): its look, its icon and its
# first word.
KIND_ICON = {
    "markdown": "file-lines",
    "text": "file",
    "json": "brackets-curly",
    "jsonl": "list",
    "log": "terminal",
    "html": "globe",
    "binary": "file-zipper",
    "image": "image",
}
KIND_WORD = {
    "markdown": "markdown",
    "text": "text",
    "json": "JSON",
    "jsonl": "JSON lines",
    "log": "log",
    "html": "page",
    "binary": "binary",
    "image": "picture",
}
# Lem's own words, which a developer meets on the page with no other place that says
# what they are: an element that holds one gets a hover of one line that says it (the
# final audit of 2026-11-17).
TERMS = [
    (
        re.compile(r"\bcompanion\b", re.IGNORECASE),
        (
            "The companion: a session under the task’s own, for the plan talk of a "
            "careful or large plan, with the reviewer in its other pane. "
            "It builds nothing."
        ),
    ),
    (
        re.compile(r"\bbreaker\b", re.IGNORECASE),
        (
            "The breaker: the one thing that stops a build, when its next step cannot "
            "be undone by a later “no” or no option keeps the criteria you approved. "
            "Its document says what happened and what Lem recommends."
        ),
    ),
    (
        re.compile(r"\bplan talk\b", re.IGNORECASE),
        (
            "The plan talk: before a careful or large plan is built, the agent of its "
            "companion argues the plan with the reviewer, one question at a time, "
            "and repairs it."
        ),
    ),
    (
        re.compile(r"\btrust prompt\b", re.IGNORECASE),
        (
            "A trust prompt: the question an agent asks before it works in a folder "
            "that is new to it. Only you answer it, in the pane of that agent."
        ),
    ),
]
# The bytes of a kilobyte and of a megabyte, as `size_of` writes a file's size.
KB = 1024
MB = 1024 * 1024
# The color codes of a terminal in a log, which the reader shows as its words.
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
JSON_TOKEN = re.compile(
    r'("(?:\\.|[^"\\])*")(\s*:)?|\b(true|false|null)\b|-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b'
)


class NotFound(Exception):
    """The address names no task, no tab or no artifact of the workspace: the page
    says which."""


def gloss(*texts: object) -> str | None:
    """The hover of an element whose text holds a word of Lem's own, or None."""
    said = [
        meaning
        for word, meaning in TERMS
        if any(word.search(str(text or "")) for text in texts)
    ]
    return " ".join(said) or None


def size_of(n: int | None) -> str:
    if n is None:
        return ""
    return (
        f"{n} B"
        if n < KB
        else f"{n / KB:.{1 if n < 10 * KB else 0}f} KB"
        if n < MB
        else f"{n / MB:.1f} MB"
    )


def row(  # noqa: PLR0913, PLR0917 - over the limit before the limit was set
    ctx: P.Ctx, key: str, actor: str, name: str, text: list, time: object = ""
) -> Markup:
    """One row of a card: an icon in the actor's color, its text, and its time at
    the right."""
    return h(
        "div",
        {"class": f"row a-{actor}", "id": key},
        h("span", {"class": "fi"}, P.icon(ctx, name)),
        h(
            "div",
            {
                "class": "rtext",
                "title": gloss(*[x for x in text if isinstance(x, str)]),
            },
            text,
        ),
        h("span", {"class": "rtime"}, time),
    )


def case_list(ctx: P.Ctx, steps: list) -> Markup | None:
    """A case as numbered steps, each run of it (Today, After) a list of its own under
    its label."""
    runs = bm.case_runs(steps)
    if not runs:
        return None
    return h(
        "div",
        {"class": "case-runs"},
        [
            [
                r["label"] and h("div", {"class": "case-label"}, r["label"]),
                r["steps"]
                and h(
                    "ol",
                    {"class": "case"},
                    [h("li", None, P.rich(ctx, step)) for step in r["steps"]],
                ),
            ]
            for r in runs
        ],
    )


def sub(*kids: object, cls: str = "sub") -> Markup:
    return h("span", {"class": cls}, *kids)


def card(key: str, title: str, summary: str, rows_: list, cls: str = "") -> Markup:
    return h(
        "section",
        {"class": f"card {cls}".strip(), "id": key},
        h(
            "div",
            {"class": "card-head"},
            h("h2", None, title),
            h("div", {"class": "dim small"}, summary) if summary else None,
        ),
        h("div", {"class": "rows"}, rows_),
    )


# ---- the header ----


def pill(ctx: P.Ctx, t: bm.Task) -> Markup:
    """The status and how long it has held; for a task that ended, how long ago
    it ended."""
    now = ctx.model.now
    return h(
        "span",
        {"class": f"pill a-{t.info['actor']}{' live' if t.info['live'] else ''}"},
        h("i"),
        t.info["label"],
        " ",
        h("span", None, P.since(t.since, now), " ago" if t.closed else ""),
    )


def jump(ctx: P.Ctx, session: str | None, label: str) -> Markup | None:
    """The jump to a session of agterm, on a page for this Mac only."""
    if not session or not ctx.local:
        return None
    return h(
        "button",
        {
            "class": "btn",
            "type": "button",
            "data-action": "agterm#jump",
            "data-agterm-session-param": session,
        },
        label,
        " ",
        P.icon(ctx, "arrow"),
    )


def tags(ctx: P.Ctx, t: bm.Task) -> list:
    """The chips of the panel: each says something a developer acts on. The type is a
    fact of the header."""
    out = []
    b = t.stopped
    if b:
        out.append(
            h(
                "span",
                {
                    "class": f"tag{' c-you live' if t.breaker else ''}",
                    "title": f"{b.what}\n{bm.stop_words(b)}",
                },
                P.icon(ctx, "alert"),
                h(
                    "span",
                    None,
                    f"breaker {b.id} waits" if t.breaker else f"breaker {b.id}, parked",
                ),
            )
        )
    need = bm.session_need(t, ctx.model)
    if need:
        out.append(
            P.tag(
                ctx,
                "alert",
                "session does not answer" if need == "deaf" else "no session",
                "bad",
                "A wake-up has waited in the task’s session for 10 minutes or more"
                if need == "deaf"
                else "No agent runs the task now: “Open a session” starts a fresh one",
            )
        )
    lead = bm.LEAD[bm.lead_of(t)] if t.lead else None
    if lead and lead["chip"]:
        out.append(
            P.tag(
                ctx,
                "split" if t.lead == "session" else "code",
                lead["chip"],
                "lead",
                f"{lead['title']}. {gloss(lead['chip']) or ''}".strip(),
                live=t.status == "building",
            )
        )
    if t.progress and t.status == "building":
        out.append(
            P.tag(
                ctx,
                "layers",
                f"task {t.progress['n']} of {t.progress['of']}",
                None,
                "The task of the plan that is built now",
            )
        )
    if t.criteria:
        out.append(
            P.tag(
                ctx,
                "file",
                bm.criteria_count(len(t.criteria["list"])),
                None,
                "\n".join(
                    f"{st.get('n')}. {st.get('text')}" for st in t.criteria["list"]
                ),
            )
        )
    if t.gates:
        out.append(
            P.tag(
                ctx,
                "alert" if t.gate_bad else "check",
                f"checks red: {t.gate_bad} of {len(t.gates)}"
                if t.gate_bad
                else f"checks green: {len(t.gates)}",
                "bad" if t.gate_bad else "ok",
                "\n".join(
                    (
                        f"{'green' if g['exit'] == 0 else 'exit ' + str(g['exit'])}  "
                        f"{g['command']}  {g['last'] or ''}"
                    )
                    for g in t.gates
                ),
            )
        )
    r = t.reviews[-1] if t.reviews else None
    if r:
        said = (
            f"review {r['round']}: clean"
            if r["verdict"] == "clean"
            else f"review {r['round']}: {r['must_fix']} must-fix"
            if r["verdict"] == "must-fix"
            else f"review {r['round']}: not reviewed"
        )
        out.append(
            P.tag(
                ctx,
                "eye",
                said,
                "ok" if r["verdict"] == "clean" else "bad",
                "\n".join(bm.review_line(x) for x in t.reviews),
            )
        )
    if t.proposal:
        green = t.proposal["green"]
        out.append(
            P.tag(
                ctx,
                "check" if green else "alert",
                "green" if green else "not green",
                "ok" if green else "you",
                bm.GREEN if green else "\n".join(map(str, t.proposal["reasons"])),
            )
        )
    return out


def copy_control(ctx: P.Ctx, text: str, what: str) -> Markup:
    """A control that copies a text: a branch's name, an artifact's path."""
    return h(
        "button",
        {
            "class": "ibtn copy",
            "type": "button",
            "data-controller": "copy",
            "data-copy-text-value": text,
            "data-action": "copy#copy",
            "title": f"Copy {what}",
            "aria-label": f"Copy {what}",
        },
        P.icon(ctx, "copy"),
        P.icon(ctx, "check", "ic done"),
    )


def facts(ctx: P.Ctx, t: bm.Task, waits: list) -> list:  # noqa: C901 - over the limit before the limit was set
    """The facts of the header, each a term and its description; a fact with nothing to
    say is left out."""
    now = ctx.model.now
    careful = bm.careful_of(t)
    pr = bm.pr_of(t)
    wait = bm.waits_for(t, waits)
    track = bm.track_of(t)
    out = []

    def fact(key: str, label: str, *kids: object) -> None:
        shown = [k for k in kids if k not in (None, "", False)]
        if shown:
            out.append(h("dt", {"id": f"dt-{key}"}, label))
            out.append(h("dd", {"id": f"dd-{key}"}, shown))

    if t.type:
        fact(
            "type",
            "Type",
            h(
                "span",
                {"title": f"because {t.type['why']}"},
                h("b", None, t.type["type"]),
                f" · {track}" if track else "",
            ),
        )
    elif track:
        fact("type", "Type", track)
    if careful:
        fact(
            "careful",
            "Careful",
            h(
                "b",
                {"class": "you-ink" if careful["yes"] else None},
                "yes" if careful["yes"] else "no",
            ),
            careful["why"]
            and h(
                "span",
                {"class": "sub clip", "title": f"{careful['by']}: {careful['why']}"},
                P.rich(ctx, careful["why"]),
            ),
        )
    elif not t.closed:
        fact(
            "careful",
            "Careful",
            h("span", {"class": "sub"}, "the review calls it, before the proposal"),
        )
    if wait:
        fact(
            "waits",
            "Waits for",
            h(
                "span",
                {
                    "class": "clip you-ink strong" if wait["you"] else "sub clip",
                    "title": f"Where you answer: {wait['where']}"
                    if wait.get("where")
                    else None,
                },
                P.rich(ctx, wait["text"]),
            ),
        )
    parked = bm.parked_of(t)
    if parked:
        fact(
            "parked",
            "Parked",
            h(
                "span",
                {"class": "clip", "title": parked["why"]},
                P.rich(ctx, parked["why"] or "no reason is on record"),
            ),
            h(
                "span",
                {"class": "sub"},
                f"since {bm.stamp(parked['since'], now)} · type ",
                h("code", None, parked["resume"]),
                " to bring it back",
            ),
        )
    if t.branch:
        fact(
            "branch",
            "Branch",
            h("span", {"class": "mono"}, t.branch),
            copy_control(ctx, t.branch, "the branch's name"),
        )
    if pr:
        fact(
            "pr",
            "Pull request",
            h(
                "a",
                {
                    "href": pr["url"],
                    "target": "_blank",
                    "rel": "noopener",
                    "title": f"Open the pull request on the forge: {pr['url']}",
                },
                f"{pr['repo']}#{pr['n']}",
            ),
            t.proposal
            and h(
                "span",
                {"class": "sub"},
                "green" if t.proposal["green"] else "not green",
            ),
        )
    live = bm.live_of(t, ctx.model)
    if live and live["live"]:
        fact(
            "session",
            "Session",
            h(
                "span",
                {
                    "class": "mono",
                    "title": f"The agterm session of the task: {live['session'] or ''}",
                },
                (t.opened or {}).get("name") or t.slug,
            ),
            jump(ctx, live["session"], "Go to the session"),
        )
    elif live and not t.closed:
        fact(
            "session",
            "Session",
            h("span", {"class": "you-ink"}, "none runs"),
            t.opened
            and h(
                "span",
                {"class": "sub"},
                f"the last opened {bm.stamp(t.opened['ts'], now)}",
            ),
        )
    if t.closed:
        fact(
            "time",
            "Ended",
            h("span", {"data-ago": t.since}, bm.ago(now - t.since)),
            h("span", {"class": "sub"}, f"· open for {bm.span(t.since - t.first)}"),
        )
    else:
        fact(
            "time",
            "In this state",
            h("span", {"class": "mono"}, P.since(t.since, now)),
            h(
                "span",
                {"class": "sub"},
                f"since {bm.stamp(t.since, now)} · opened {bm.stamp(t.first, now)}",
            ),
        )
    return out


def key_line(ctx: P.Ctx, t: bm.Task) -> Markup | None:
    """The one line of the header that matters most when its details are folded (a
    phone, a short window): the pull request as a link with green or not green, or what
    the task waits for, or what runs now."""
    pr = bm.pr_of(t)
    if pr:
        v = bm.verdict_of(t)
        word = None if v is None else "green" if v["green"] else "not green"
        return h(
            "div",
            {"class": "p-key", "id": "p-key"},
            P.icon(ctx, "pull"),
            h(
                "a",
                {
                    "href": pr["url"],
                    "target": "_blank",
                    "rel": "noopener",
                    "title": f"Open the pull request on the forge: {pr['url']}",
                },
                f"{pr['repo']}#{pr['n']}",
            ),
            word
            and v
            and h(
                "span", {"class": f"p-key-word {'ok' if v['green'] else 'you'}"}, word
            ),
        )
    wait = bm.waits_for(t, bm.waits_of(ctx.model))
    if wait:
        return h(
            "div",
            {"class": f"p-key{' you' if wait['you'] else ''}", "id": "p-key"},
            P.icon(ctx, "help" if wait["you"] else "clock"),
            h("span", None, P.rich(ctx, wait["text"])),
        )
    if t.shown:
        return h(
            "div",
            {"class": "p-key", "id": "p-key"},
            h("span", None, P.rich(ctx, bm.cap(t.shown))),
        )
    return None


def head(ctx: P.Ctx, t: bm.Task | None, title: str, said: str | None = None) -> Markup:
    """The panel's header: the controls, then the task's status, title, ask, facts and
    chips, or what the address names when it is no task. On a phone, in a window too
    short for it, and while an HTML page is open among the artifacts (`page-open` on the
    panel), the ask, the facts and the chips fold under "Details" behind one key line
    (`key_line`); the cookie keeps the fold (`head`). The title takes the focus when a
    link outside the panel opened it (the panel controller)."""
    view_href = f"{ctx.href(ctx.view)}"
    back = h(
        "a",
        {
            "class": "ibtn p-back",
            **P.frame_link(ctx, view_href),
            "title": "Back to the board",
            "aria-label": "Back to the board",
        },
        P.icon(ctx, "arrow-left"),
    )
    controls = [
        h(
            "button",
            {
                "class": "ibtn p-expand",
                "type": "button",
                "data-action": "panel#expand",
                "title": (
                    "Show the task across the whole width, or dock it at the right"
                ),
                "aria-label": "Expand or dock the panel",
            },
            P.icon(ctx, "up-right-and-down-left-from-center", "ic on-docked"),
            P.icon(ctx, "down-left-and-up-right-to-center", "ic on-full"),
        ),
        h(
            "a",
            {
                "class": "ibtn p-close",
                **P.frame_link(ctx, view_href),
                "data-hotkey": "Escape",
                "title": "Close the panel · Escape",
                "aria-label": "Close the panel",
            },
            P.icon(ctx, "x"),
        ),
    ]
    if t is None:
        return h(
            "header",
            {"class": "p-head", "id": "p-head"},
            h(
                "div",
                {"class": "p-top"},
                back,
                h("span", {"class": "p-crumb"}, "A task"),
                h("span", {"class": "sp"}),
                controls,
            ),
            h("h2", {"class": "p-title"}, title),
            h("p", {"class": "p-ask"}, said),
        )
    ask = t.ask if t.ask and bm.flat(t.ask) != bm.flat(t.title) else None
    opened = bool(ctx.prefs.get("head"))
    fold = h(
        "button",
        {
            "class": "p-fold",
            "type": "button",
            "data-action": "fold#head",
            "aria-expanded": "true" if opened else "false",
            "aria-controls": "p-more",
            "title": "Show or hide the ask, the facts and the chips",
        },
        h("span", {"class": "on-closed"}, "Details"),
        h("span", {"class": "on-open"}, "Less"),
        P.icon(ctx, "chevron-down", "ic chev"),
    )
    return h(
        "header",
        {"class": f"p-head{' open' if opened else ''}", "id": "p-head"},
        h(
            "div",
            {"class": "p-top"},
            back,
            pill(ctx, t),
            h("span", {"class": "sp"}),
            controls,
        ),
        h("h2", {"class": "p-title", "tabindex": "-1"}, t.title),
        h("div", {"class": "p-sum", "id": "p-sum"}, key_line(ctx, t), fold),
        head_acts(ctx, t),
        h(
            "div",
            {"class": "p-more", "id": "p-more"},
            ask and h("p", {"class": "p-ask", "title": ask}, P.rich(ctx, ask)),
            h(
                "dl",
                {"class": "facts", "id": "facts"},
                facts(ctx, t, bm.waits_of(ctx.model)),
            ),
            h("div", {"class": "p-tags", "id": "p-tags"}, tags(ctx, t)),
        ),
    )


def merge_label(ctx: P.Ctx, t: bm.Task) -> str:
    pr = (ctx.landing_of(t.slug) or {}).get("pr") or {}
    return (
        f"Merge #{pr['number']}…"
        if isinstance(pr, dict) and pr.get("number")
        else "Merge…"
    )


def open_form(ctx: P.Ctx, t: bm.Task) -> Markup:
    """The one button that opens a fresh session of the task (serve.py
    `act_session`, `lem session open`)."""
    return P.act_form(
        ctx,
        t.slug,
        "session",
        "Open a session",
        "play",
        "go",
        "Opening…",
        {"in": ctx.view if ctx.view != "tasks" else None},
    )


def head_acts(ctx: P.Ctx, t: bm.Task) -> Markup | None:
    """The header's acts: "Open a session" while no session of the task lives or the
    guard of a stopped session logged its stop (`bm.opens_session`), and the way to the
    confirm step of a merge while the board offers it (`bm.acts_of`: none while the
    owner's merge stands; while a merge runs, a line that says so). None on a page that
    may not act, and on a step of an act itself."""
    if not ctx.can_act or ctx.tab in ACT_TABS:
        return None
    out = []
    if bm.opens_session(t, ctx.model):
        out.append(open_form(ctx, t))
    offered = "merge" in bm.acts_of(t, ctx.model.seen)
    # the owner's merge that stands offers no second press, and says "Merging…" while
    # the server runs it
    if t.slug in ctx.merging and (offered or bm.owner_stands(t)):
        out.append(
            h(
                "span",
                {"class": "btn busy", "role": "status"},
                P.icon(ctx, "clock"),
                h("span", None, "Merging…"),
            )
        )
    elif offered:
        out.append(
            P.act_link(
                ctx, t.slug, "merge", merge_label(ctx, t), "pull", "risk", frame=True
            )
        )
    return h("div", {"class": "p-acts", "id": "p-acts"}, out) if out else None


def tab_nav(ctx: P.Ctx, t: bm.Task) -> Markup:
    """The five tabs, each a link that changes the frame; the one shown is
    the address's."""
    files = ctx.artifact_count
    links = []
    for i, (key, name) in enumerate(TABS, 1):
        count = None
        if key == "artifacts" and files:
            count = h("em", {"class": "n"}, files)
        on = ctx.tab == key
        links.append(
            h(
                "a",
                {
                    "class": "ptab",
                    "id": f"ptab-{key}",
                    **P.frame_link(ctx, P.task_href(ctx, t.slug, key)),
                    "aria-current": "page" if on else None,
                    "data-hotkey": f"Digit{i}",
                    "title": f"{name} · key {i}",
                },
                name,
                count,
            )
        )
    return h(
        "nav",
        {"class": "ptabs", "id": "ptabs", "aria-label": "The tabs of the task"},
        links,
    )


# ---- the way to the task's session ----


def session_action(ctx: P.Ctx, t: bm.Task) -> Markup | None:
    """The way from a thing that waits for the owner to the task's session, where he
    answers it: the jump to it while it lives (a page for this Mac), "Open a session"
    while none lives (a page that may act), else where it is in words."""
    live = bm.live_of(t, ctx.model)
    if live and live["live"]:
        go = jump(ctx, live["session"], "Go to the task’s session")
        return h(
            "div",
            {"class": "wl-actions"},
            go
            or h(
                "span",
                {"class": "bl-note"},
                (
                    f"The task’s session, “{(t.opened or {}).get('name') or t.slug}”, "
                    "is in agterm on the Mac."
                ),
            ),
        )
    if bm.opens_session(t, ctx.model):
        return h(
            "div",
            {"class": "wl-actions"},
            h("span", {"class": "bl-note"}, "No session of the task runs now."),
            open_form(ctx, t) if ctx.can_act else None,
        )
    return None


def inbox_action(ctx: P.Ctx, t: bm.Task) -> Markup | None:
    """Where the owner answers while his mark says away and the board's server sent the
    task's thing to his Inbox (`bm.inbox_of`): a question, in the task's session on the
    Mac or in the Inbox, its thread a link at the Inbox's tailnet address, in place of
    `session_action`'s line about the session (its jump stays on a page for this Mac); a
    note, which no session can take a reply to, that no session runs or answers, or that
    the task's session stopped, with the link and "Open a session" where the page may
    act; a note of a row that asks nothing (a refused merge, a merge with no review of
    its tip), `session_action` as today and a line that the Inbox has a note of it, with
    the link; and with no link, `session_action` as today and one line that says why.
    None while it changes nothing of today's lines: the large card and the breaker's
    card show `row_action` then."""
    said = bm.inbox_of(t, ctx.model)
    if said is None:
        return None

    def line(*words: object, then: Markup | None = None) -> Markup:
        return h(
            "div",
            {"class": "wl-actions", "id": "inbox"},
            h("span", {"class": "bl-note"}, *words),
            then,
        )

    if said["why"]:
        return join([session_action(ctx, t) or "", line(said["why"])])
    inbox = h(
        "a",
        {
            "class": "inbox-link",
            "href": said["thread"],
            "target": "_blank",
            "rel": "noopener",
            "title": "Open the task’s thread in the Inbox",
        },
        "Inbox",
    )
    live = bm.live_of(t, ctx.model) or {}
    if said["asks"]:
        go = (
            jump(ctx, live.get("session"), "Go to the task’s session")
            if live.get("live")
            else None
        )
        return line(
            "Answer in the task’s session on the Mac, or in the ", inbox, ".", then=go
        )
    if said["gone"]:
        opens = bm.opens_session(t, ctx.model) and ctx.can_act
        stopped = bm.stopped_of(t, ctx.model) is not None
        first = (
            "The task’s session stopped: open a fresh one here."
            if stopped and opens
            else "The task’s session stopped."
            if stopped
            else "The task’s session does not answer."
            if live.get("live")
            else "No session of the task runs now: open one here."
            if opens
            else "No session of the task runs now."
        )
        return line(
            first,
            " The ",
            inbox,
            " has a note, not a question.",
            then=open_form(ctx, t) if opens else None,
        )
    return join(
        [
            session_action(ctx, t) or "",
            line("The ", inbox, " has a note of it, not a question."),
        ]
    )


def row_action(ctx: P.Ctx, t: bm.Task) -> Markup | None:
    """The way to the task's session for a thing of the task that waits for the owner:
    its breaker, or its held block's need."""
    if t.breaker is not None or (t.need and not t.approved and not t.helped):
        return session_action(ctx, t)
    return None


def owner_lines(ctx: P.Ctx, t: bm.Task, *, park_link: bool = True) -> Markup | None:
    """The owner's two other words to a task a breaker holds, or to a parked one, as
    lines to type in any session; for a breaker, on a page that may act, the way to park
    it from the board first, unless the breaker's answer form above has it
    (PARK_LINK false)."""
    park = None
    if t.breaker is not None:
        lines = [
            (f"/lem park {t.slug}", "puts the task aside"),
            (f"/lem drop {t.slug}", "ends it"),
        ]
        park = (
            P.act_link(ctx, t.slug, "park", "Park it…", "park", frame=True)
            if ctx.can_act and park_link
            else None
        )
    elif t.status == bm.PARKED:
        lines = [
            (f"/lem resume {t.slug}", "brings it back as it was"),
            (f"/lem drop {t.slug}", "ends it"),
        ]
    else:
        return None
    return h(
        "div",
        {"class": "wl-actions"},
        park,
        h("span", {"class": "bl-note"}, "Or type in any session:"),
        [
            [h("code", None, line), h("span", {"class": "bl-note"}, said)]
            for line, said in lines
        ],
    )


# ---- Overview ----

# A picture's name that pairs it with another of the same view: NAME-before.EXT
# and NAME-after.EXT.
PAIR = re.compile(
    r"^media/(?P<name>.+)-(?P<side>before|after)\.(?:png|jpe?g|gif|webp)$",
    re.IGNORECASE,
)


def pairs_of(files: list, shown: str) -> list[dict]:
    """The before and after pictures of the task's media folder, by the view's name,
    that the outcome does not show itself (`shown`, its text): the Overview shows each
    pair side by side."""
    found: dict[str, dict] = {}
    for f in files:
        m = PAIR.match(f["path"])
        if m:
            found.setdefault(m["name"], {})[m["side"].lower()] = f["path"]
    return [
        {"name": name, **sides}
        for name, sides in sorted(found.items())
        if "after" in sides and sides["after"] not in shown
    ]


def caption_of(name: str) -> str:
    return bm.cap(name.replace("-", " ").replace("_", " "))


def media_pair(ctx: P.Ctx, t: bm.Task, pair: dict) -> Markup:
    """A before and an after of one view side by side, each opening at its full size; a
    view that is new has only its after."""

    def one(side: str) -> Markup | None:
        path = pair.get(side)
        if not path:
            return None
        src = ctx.media_href(t.slug) + "/".join(
            quote(part, safe="") for part in path.removeprefix("media/").split("/")
        )
        return h(
            "figure",
            {"class": f"m-{side}"},
            h(
                "a",
                {
                    "class": "pic",
                    "href": src,
                    "target": "_blank",
                    "rel": "noopener",
                    "title": "Open the picture at its full size",
                },
                h(
                    "img",
                    {
                        "src": src,
                        "alt": f"{caption_of(pair['name'])}, {side}",
                        "loading": "lazy",
                    },
                ),
            ),
            h("figcaption", None, bm.cap(side)),
        )

    return h(
        "div",
        {"class": "shots", "id": f"shots-{pair['name']}"},
        h("div", {"class": "shots-head"}, caption_of(pair["name"])),
        h("div", {"class": "pair"}, one("before"), one("after")),
    )


def building(ctx: P.Ctx, t: bm.Task) -> Markup | None:
    """ "What we are building": the goal, what the owner gets (the outcome of task.md,
    as markdown: its story, its lists, its chart and its pictures), the before and after
    pictures of the task, the important decisions, the filed items."""
    told = ctx.told(t.slug)
    b = bm.building_of(t, told)
    if not b:
        return None
    lines = []
    if b["important"]:
        lines.append(
            h(
                "a",
                {
                    "class": "btn b-look",
                    **P.frame_link(ctx, P.task_href(ctx, t.slug, "criteria")),
                    "title": "Open the tab Criteria and decisions · key 2",
                },
                P.icon(ctx, "alert"),
                (
                    f"{bm.plural(b['important'], 'important decision')} "
                    f"{'waits' if b['important'] == 1 else 'wait'} for a look"
                ),
                " ",
                P.icon(ctx, "arrow"),
            )
        )
    if b["filed"] is not None:
        filed = b["filed"]
        lines.append(
            h(
                "div",
                {"class": "b-line"},
                h(
                    "b",
                    None,
                    f"{bm.plural(len(filed), 'backlog item')} filed"
                    if filed
                    else "no backlog item filed",
                ),
                h("span", None, "· on the task’s branch"),
                filed
                and h(
                    "ul",
                    {"class": "b-items"},
                    [
                        h(
                            "li",
                            {"title": item.get("path")},
                            item.get("title"),
                            h("span", {"class": "cmd"}, f" · {item.get('path')}"),
                        )
                        for item in filed
                    ],
                ),
            )
        )
    shots = [
        media_pair(ctx, t, pair) for pair in pairs_of(ctx.artifact_files, b["outcome"])
    ]
    return h(
        "section",
        {
            "class": "card building",
            "id": "building",
            "aria-label": "What we are building",
        },
        h("div", {"class": "eyebrow"}, "What we are building"),
        b["goal"] and h("h3", {"class": "b-goal"}, bm.cap(b["goal"])),
        b["outcome"]
        and P.md_block(ctx, f"outcome-{t.slug}", b["outcome"], slug=t.slug, cls="b-md"),
        shots,
        lines and h("div", {"class": "b-lines"}, lines),
    )


def verdict(ctx: P.Ctx, t: bm.Task) -> Markup | None:
    """Green or not green, with each reason a row of its own
    (`lem_board_pages.reason_list`); before a proposal, when the word comes."""
    v = bm.verdict_of(t)
    if not v and t.closed:
        return None

    def line(actor: str, name: str, *kids: object, title: str | None = None) -> Markup:
        return h(
            "section",
            {
                "class": f"card verdict a-{actor}",
                "id": "verdict",
                "role": "status",
                "aria-label": "Green or not green",
            },
            h(
                "div",
                {"class": "v-line"},
                h("span", {"class": "fi"}, P.icon(ctx, name)),
                h("div", {"class": "v-text", "title": title}, *kids),
            ),
        )

    if not v:
        return line(
            "quiet",
            "clock",
            h("b", {"class": "v-word"}, "not proposed yet:"),
            (
                " green or not green comes with the proposal, "
                "after the checks and the review"
            ),
        )
    if v["green"]:
        return line(
            "done",
            "check",
            h("b", {"class": "v-word"}, "green:"),
            f" {bm.GREEN[0].lower()}{bm.GREEN[1:]}",
        )
    n = len(v["reasons"])
    return line(
        "you",
        "alert",
        h(
            "b",
            {"class": "v-word"},
            "not green"
            + (
                f", for {n} reasons:"
                if n > 1
                else ":"
                if n
                else ": no reason is on record"
            ),
        ),
        n and P.reason_list(ctx, t, v["reasons"], "v"),
    )


def now_foot(
    ctx: P.Ctx, t: bm.Task, time: Markup, note: str, *, apart: bool = False
) -> Markup:
    """The foot of the large card: the last update, the time in this state and its note,
    the jump."""
    live = bm.live_of(t, ctx.model) or {}
    return h(
        "div",
        {"class": f"now-next{' apart' if apart else ''}"},
        h(
            "span",
            {"class": "ago"},
            "last update ",
            h("span", {"data-ago": t.last_ts}, bm.ago(ctx.model.now - t.last_ts)),
        ),
        h(
            "div",
            {"class": "timer-row"},
            h("span", {"class": "timer"}, time),
            h("span", {"class": "note"}, note),
        ),
        h(
            "span",
            {"class": "right"},
            jump(ctx, live.get("session"), "Go to the session"),
        )
        if live.get("live")
        else None,
    )


def breaker_card(ctx: P.Ctx, t: bm.Task) -> Markup | None:
    """The breaker's document, first on the Overview while it waits (for the owner, or
    for nobody while the task is parked): its markdown as the artifacts render it, with
    its callouts, its stories, its chart, its table and the task's pictures. Once his
    help is on record it leaves the Overview, and Artifacts and "Criteria and decisions"
    keep it. None while no breaker waits."""
    b = t.stopped
    if b is None:
        return None
    name = str(b.document or "breaker.md")
    f = ctx.artifact(t.slug, name)
    text = (f or {}).get("text")
    now = ctx.model.now
    link = h(
        "a",
        {
            "class": "btn b-look",
            **P.frame_link(ctx, P.task_href(ctx, t.slug, "artifacts", name)),
            "title": f"Open {name} on Artifacts",
        },
        P.icon(ctx, "file"),
        name,
        " ",
        P.icon(ctx, "arrow"),
    )
    handoff = (
        b.handoff
        and any(x["path"] == b.handoff for x in ctx.artifact_files)
        and h(
            "a",
            {
                "class": "btn b-look",
                **P.frame_link(
                    ctx, P.task_href(ctx, t.slug, "artifacts", str(b.handoff))
                ),
                "title": "What a fresh agent goes on from",
            },
            P.icon(ctx, "file"),
            "the handoff",
            " ",
            P.icon(ctx, "arrow"),
        )
    )
    body = (
        P.md_block(ctx, f"breaker-{t.slug}-{b.id}", text, slug=t.slug)
        if text is not None
        else h(
            "p",
            {"class": "sub"},
            (
                f"{name} is not in the task directory: "
                "the board has nothing to show of it."
            ),
        )
    )
    # while he is away and the breaker went to his Inbox, its line says where he
    # answers, once
    inbox = inbox_action(ctx, t) if t.breaker else None
    both = (
        inbox is not None
        and cast("dict", bm.inbox_of(t, ctx.model))[
            "asks"
        ]  # inbox_action is None while it is None
    )
    # on a page that may act, his Help, Park and Drop under the document, until his
    # answer is on record
    asks = bm.answer_row(t) if t.breaker else None
    form = (
        P.answer_form(ctx, t, asks, "panel", ctx.view)
        if asks
        and asks["kind"] == "breaker"
        and ctx.can_act
        and bm.answered_of(t, ctx.model) is None
        else None
    )
    said = (
        "help, park or drop it here, or help in the task’s session."
        if form is not None
        else "help in the task’s session."
    )
    where = (
        h(
            "div",
            {"class": "b-lines"},
            None
            if both
            else h(
                "div", {"class": "b-line"}, h("b", None, "Where you answer: "), said
            ),
            form,
            inbox or row_action(ctx, t),
            owner_lines(ctx, t, park_link=form is None),
        )
        if t.breaker
        else h(
            "div",
            {"class": "b-lines"},
            h(
                "div",
                {"class": "b-line"},
                (
                    "The task is parked: this breaker waits for nobody "
                    "until you bring it back."
                ),
            ),
            owner_lines(ctx, t),
        )
    )
    return h(
        "section",
        {
            "class": f"card building a-{'you' if t.breaker else 'quiet'}",
            "id": "breaker",
            "aria-label": "What stopped the build",
        },
        h(
            "div",
            {"class": "eyebrow", "title": bm.cap(bm.stop_words(b))},
            f"The build stopped · breaker {b.id} · ",
            h("span", {"title": bm.stamp(b.ts, now)}, P.since(b.ts, now), " ago"),
        ),
        body,
        h("div", {"class": "b-lines"}, h("div", {"class": "b-line"}, link, handoff)),
        where,
    )


def merge_review_card(ctx: P.Ctx, t: bm.Task) -> Markup | None:
    """The merge agent's review, the first card of the Overview while the task is open
    and the file is in its directory: its markdown as the artifacts render it, under its
    verdict. None otherwise."""
    if t.status != "open":
        return None
    f = ctx.artifact(t.slug, "merge-review.md")
    text = (f or {}).get("text")
    if text is None:
        return None
    r = t.merge_review or {}
    calls = r.get("calls", True)
    now = ctx.model.now
    head = (
        "The merge review · it calls you" if calls else "The merge review · it merges"
    )
    when = r.get("ts") and h(
        "span", {"title": bm.stamp(r["ts"], now)}, " · ", P.since(r["ts"], now), " ago"
    )
    link = h(
        "a",
        {
            "class": "btn b-look",
            **P.frame_link(
                ctx, P.task_href(ctx, t.slug, "artifacts", "merge-review.md")
            ),
            "title": "Open merge-review.md on Artifacts",
        },
        P.icon(ctx, "file"),
        "merge-review.md",
        " ",
        P.icon(ctx, "arrow"),
    )
    return h(
        "section",
        {
            "class": f"card building a-{'you' if calls else 'quiet'}",
            "id": "merge-review",
            "aria-label": "The merge review",
        },
        h("div", {"class": "eyebrow", "title": r.get("why") or ""}, head, when or None),
        P.md_block(ctx, f"merge-review-{t.slug}", text, slug=t.slug),
        h("div", {"class": "b-lines"}, h("div", {"class": "b-line"}, link)),
    )


def cards_card(ctx: P.Ctx, t: bm.Task) -> Markup | None:
    """Each `lem-ask` card the task's live session waits on (`bm.open_cards`), first on
    the Overview: its question, since when, and on a page that may act the way to answer
    it on the board."""
    found = bm.open_cards(t, ctx.model)
    if not found:
        return None
    rows_ = []
    for c in found:
        go = ctx.can_act and h(
            "a",
            {
                "class": "btn go",
                **P.frame_link(ctx, P.task_href(ctx, t.slug, f"card/{c['page']}")),
            },
            P.icon(ctx, "user"),
            h("span", None, "Answer the card…"),
        )
        rows_.append(
            row(
                ctx,
                f"card-{c['page']}",
                "you",
                "user",
                [
                    h(
                        "b",
                        None,
                        P.rich(
                            ctx, bm.cap(c["prompt"] or "The task’s session asks you")
                        ),
                    ),
                    " ",
                    sub(
                        "Answer it here or in the task’s session at the Mac. "
                        "A question back goes to the session."
                    ),
                    go and h("div", {"class": "wl-actions"}, go),
                ],
                P.since(c["since"], ctx.model.now),
            )
        )
    return card(
        "cards",
        "The task’s session asks you",
        (
            f"{bm.plural(len(found), 'card')} {'waits' if len(found) == 1 else 'wait'} "
            "for your answer"
        ),
        rows_,
        "a-you",
    )


def now_answer(ctx: P.Ctx, t: bm.Task) -> Markup | None:
    """The answer form of a plan that waits for the owner's read and of "Skip the
    persona read?" on the large card (`P.answer_form`), on a page that may act, until
    his answer is on record. A breaker's is under its document, and the one criterion's
    under its text on "Criteria and decisions"."""
    asks = bm.answer_row(t)
    if (
        not ctx.can_act
        or asks is None
        or asks["kind"] not in ("plan", "skip")
        or bm.answered_of(t, ctx.model) is not None
    ):
        return None
    return P.answer_form(ctx, t, asks, "panel", ctx.view)


def answered_card(ctx: P.Ctx, t: bm.Task) -> Markup | None:
    """The owner's answer on record for the row the board answers with its own buttons,
    first on the Overview until the task's session writes its next state block
    (`bm.answered_of`): that the session takes it, what he picked, when and from where,
    and his note."""
    made = bm.answered_of(t, ctx.model)
    if made is None:
        return None
    return h(
        "section",
        {
            "class": "card verdict a-gate",
            "id": "answered",
            "role": "status",
            "aria-label": "Your answer",
        },
        h(
            "div",
            {"class": "v-line"},
            h("span", {"class": "fi"}, P.icon(ctx, "clock")),
            h(
                "div",
                {"class": "v-text"},
                h("b", {"class": "v-word"}, bm.ANSWER_ON_RECORD),
                " ",
                f"{lem_answers.took_effect(made)}.",
                made.get("note")
                and h(
                    "div",
                    {"class": "sub"},
                    "Your note: “",
                    P.rich(ctx, made["note"]),
                    "”",
                ),
            ),
        ),
    )


def now_card(ctx: P.Ctx, t: bm.Task) -> Markup:
    """What runs now, or what waits for the owner, with where he answers, under the
    task's first line while the block that said it is the task's newest."""
    now = ctx.model.now
    x = t.investigation
    found = []
    if x:
        where = bm.investigation_sub(x)
        # the report's file only while the folder holds it: prune removes it with the
        # other files of an old ended task
        folder = ctx.folder_of(t.slug)
        found = [
            h(
                "div",
                {"class": "now-ctx"},
                h("b", None, f"{bm.CALLS.get(x['call'], {}).get('now', x['call'])}: "),
                x.get("line") or "",
                f" · {where}" if where else "",
            ),
            folder
            and "investigation.md" in folder["left"]
            and h(
                "div",
                {"class": "now-ctx"},
                "The report is investigation.md in the task directory",
            ),
        ]
    headline = bm.now_head(t)
    # Lem's first line of the task, its read of the request, while the block that said
    # it is the newest
    said = t.opening and h(
        "div",
        {
            "class": "now-said",
            "title": "Lem's first line of this task: its read of the request",
        },
        P.rich(ctx, t.opening),
    )
    body = [
        said,
        h("div", {"class": "now-eyebrow"}, bm.who_acts(t)),
        h("div", {"class": "now-head"}, headline),
        t.shown
        and not t.breaker
        and h("div", {"class": "now-status"}, P.rich(ctx, t.shown)),
        t.more and h("div", {"class": "now-ctx"}, P.rich(ctx, " · ".join(t.more))),
        found,
        t.for_owner
        and not t.breaker
        and h(
            "div",
            {"class": "now-ctx"},
            h("b", None, "Where you answer: "),
            P.rich(ctx, bm.answer_of(t)),
        ),
        # the breaker's call to its document, only while it waits for him: not while the
        # session works on his help
        t.breaker
        and not t.works
        and h(
            "div",
            {"class": "now-ctx"},
            (
                "Its document is the first card above: read it, then help, "
                "park or drop the task."
            ),
        ),
        None
        if t.breaker
        else inbox_action(ctx, t) or (row_action(ctx, t) if t.for_owner else None),
        None if t.breaker else now_answer(ctx, t),
        t.status == bm.PARKED and owner_lines(ctx, t),
    ]
    time = (
        h("span", None, bm.stamp(t.since, now)) if t.closed else P.since(t.since, now)
    )
    return h(
        "section",
        {"class": f"card now a-{t.info['actor']}", "id": "now"},
        h(
            "div",
            {"class": f"now-wrap{'' if t.info['live'] else ' still'}"},
            h(
                "div",
                {"class": "now-in", "title": gloss(headline, t.shown, *t.more)},
                h("div", {"class": "avatar"}, P.icon(ctx, t.info["icon"])),
                h("div", {"class": "now-body"}, body),
            ),
            h("div", {"class": "now-spacer"}),
            now_foot(
                ctx,
                t,
                time,
                f"after {bm.span(t.since - t.first)}" if t.closed else "in this state",
            ),
        ),
    )


def ring(done: int, current: int, total: int, big: str, small: str) -> Markup:
    """The ring of the plan's tasks: the finished ones, the one built now, the ones
    to come."""
    r, c = 58, 2 * 3.141592653589793 * 58
    safe = max(1, total)

    def arc(cls: str, start: int, n: int) -> Markup | None:
        if n <= 0:
            return None
        return Markup(
            f'<circle class="{cls}" cx="68" cy="68" r="{r}" '
            f'stroke-dasharray="{c * n / safe:.3f} {c:.3f}" '
            f'stroke-dashoffset="{-c * start / safe:.3f}" '
            'transform="rotate(-90 68 68)"></circle>'
        )

    svg = (
        Markup(
            '<svg class="ring" width="136" height="136" viewBox="0 0 136 136" '
            f'aria-hidden="true"><circle class="todo" cx="68" cy="68" r="{r}"></circle>'
        )
        + join([arc("done", 0, done), arc("cur", done, current)])
        + Markup("</svg>")
    )
    return h(
        "div",
        {"class": "ring-wrap"},
        svg,
        h("div", {"class": "ring-center"}, h("b", None, big), h("span", None, small)),
    )


def stat(label: str, value: object, said: str | None, cls: str = "") -> Markup:
    return h(
        "div",
        {"class": f"stat {cls}".strip(), "title": said or None},
        h("div", {"class": "sk"}, label),
        h("div", {"class": "sv"}, value),
        h("div", {"class": "ss"}, said),
    )


def progress(ctx: P.Ctx, t: bm.Task) -> Markup:
    """The phases of the task, the ring of its plan's tasks, and its stats."""
    now = ctx.model.now
    p = bm.progress_of(t)
    phases = [
        h(
            "div",
            {
                "class": (
                    "phase "
                    f"{'past' if k < p['past'] else 'cur' if k == p['at'] else ''}"
                ).strip()
            },
            h("i"),
            name,
            h("small", None, p["subs"][k]),
        )
        for k, name in enumerate(p["names"])
    ]
    review = p["review"]
    lead = bm.LEAD[bm.lead_of(t)] if t.lead else None
    who = (
        lead["tag"] if lead else "investigator" if t.investigated else "–",
        lead["stat"]
        if lead
        else "an investigator examined the bug or the question first"
        if t.investigated
        else "no agent was started"
        if t.closed
        else "no agent was started yet",
    )
    taken, past, breakers = p["taken"], p["past_personas"], p["breakers"]
    stats = [
        stat("Who works on it", who[0], who[1]),
        stat(
            "Last commit",
            t.commit["head"] if t.commit else "–",
            t.commit["subject"]
            if t.commit
            else "no commit of its branch is on record"
            if t.closed
            else "no commit on its branch yet",
        ),
        stat(
            "Open for",
            bm.span(t.since - t.first) if t.closed else P.since(t.first, now),
            f"opened {bm.stamp(t.first, now)}",
        ),
        stat(
            "Checks",
            ("red" if t.gate_bad else "green") if t.gates else "–",
            f"{bm.plural(len(t.gates), 'command')} in the last run"
            if t.gates
            else "none: it ended with a report"
            if t.status == "answered"
            else "they run before the pull request",
            ("bad" if t.gate_bad else "ok") if t.gates else "",
        ),
        stat(
            "Review",
            review["verdict"] if review else "–",
            f"round {review['round']}, {bm.KIND.get(review['kind'], review['kind'])}"
            if review
            else "none: it ended with a report"
            if t.status == "answered"
            else "after the checks, before the proposal",
            ("ok" if review["verdict"] == "clean" else "bad") if review else "",
        ),
        stat(
            "Decisions",
            taken,
            (
                (
                    f"{taken} taken{f', {past} past the personas' if past else ''}"
                    f"{', ' + bm.plural(breakers, 'breaker') if breakers else ''}"
                )
                if t.decided
                else "none"
                if t.closed
                else "none yet"
            ),
            "you" if t.breaker else "bad" if past else "",
        ),
    ]
    total = p["total"]
    return h(
        "section",
        {"class": "card", "id": "progress"},
        h(
            "div",
            {"class": "prog"},
            ring(
                p["finished"],
                p["current"],
                total or 1,
                f"{p['finished']}/{total}" if total else "–",
                "plan tasks",
            ),
            h("div", {"class": f"phases a-{t.info['actor']}"}, phases),
            h("div", {"class": "stats"}, stats),
        ),
    )


def parked_card(ctx: P.Ctx, t: bm.Task) -> Markup | None:
    """A parked task's first line on the Overview: since when, why in the owner's words,
    and the command that brings it back, in the quiet look of a line that waits
    for nobody."""
    p = bm.parked_of(t)
    if p is None:
        return None
    return h(
        "section",
        {
            "class": "card verdict a-quiet",
            "id": "parked-card",
            "role": "status",
            "aria-label": "Parked",
        },
        h(
            "div",
            {"class": "v-line"},
            h("span", {"class": "fi"}, P.icon(ctx, "park")),
            h(
                "div",
                {"class": "v-text"},
                h(
                    "b",
                    {"class": "v-word"},
                    f"parked since {bm.stamp(p['since'], ctx.model.now)}:",
                ),
                " ",
                P.rich(ctx, p["why"] or "no reason is on record"),
                h(
                    "div",
                    {"class": "sub"},
                    "Nothing of it waits for you, and nobody works on it. Type ",
                    h("code", None, p["resume"]),
                    " in any session to bring it back.",
                ),
            ),
        ),
    )


# ---- a task whose events became one summary ----

# What went with the events of a summarized task, by the tab that showed it: the tab
# says so in one line, never with an empty section that reads as nothing on record.
WENT = {
    "criteria": (
        "Its acceptance criteria, their approval, the personas’ read and its decisions"
    ),
    "checks": "Its runs of the checks, its review rounds and the proposal’s reasons",
    "timeline": "Its timeline and its events",
}


def artifacts_link(ctx: P.Ctx, t: bm.Task) -> Markup:
    return h(
        "a",
        {
            "class": "btn b-look",
            **P.frame_link(ctx, P.task_href(ctx, t.slug, "artifacts")),
            "title": "Open the tab Artifacts · key 5",
        },
        P.icon(ctx, "folder"),
        "Artifacts",
        " ",
        P.icon(ctx, "arrow"),
    )


# What each file of a task's small record (`lem_artifacts.SMALL_RECORD`) is to the
# owner, on the card of a task whose other files prune removed: one name for a part that
# is more than one file.
RECORD_WORDS = (
    (("state.md",), "its state"),
    (("ask.txt", "task.md"), "its request"),
    (("landing.json",), "its pull request"),
    (("ticket.txt", "ticket-repo.txt", "ticket-steps.txt"), "its ticket’s files"),
    (("resumed-from.txt",), "the name of the task it was resumed from"),
)


def listed(parts: list[str]) -> str:
    """Parts of one sentence: "a", "a and b", "a, b and c"."""
    return parts[0] if len(parts) == 1 else f"{', '.join(parts[:-1])} and {parts[-1]}"


def files_line(ctx: P.Ctx, t: bm.Task) -> str:
    """What the folder of a summarized task holds, as the folder says it now
    (`Ctx.folder_of`), never as the summary alone: with no path outside its small
    record, what stayed and the rule that removed the rest, with the workspace's
    `state.keep_days` as the settings give it now (no day at which they left, which the
    page cannot know); with paths outside it, only how many are still there, with no
    claim of why (a removal that has not ended yet, or one the folder denies run
    after run)."""
    folder = ctx.folder_of(t.slug)
    if folder is None:
        return (
            "Its folder does not read, so the board cannot say which of its "
            "files are still there."
        )
    kept = [
        words
        for names, words in RECORD_WORDS
        if any(name in folder["kept"] for name in names)
    ]
    record = (
        f"its small record: {listed(kept)}" if kept else "no file of its small record"
    )
    if folder["left"]:
        return (
            f"{bm.plural(len(folder['left']), 'file')} of its folder "
            f"{'is' if len(folder['left']) == 1 else 'are'} still "
            f"there beside {record}."
        )
    days = (
        (
            f"after {bm.plural(ctx.keep_days, 'day')} in which nothing of it happened "
            "(state.keep_days, as the settings say now)"
        )
        if ctx.keep_days
        else (
            "after state.keep_days days in which nothing of it happened (the settings "
            "do not read now, so the board does not say that number)"
        )
    )
    return (
        f"What stayed of its folder is {record}. Its other files left: "
        f"Lem keeps only this record of an ended task {days}."
    )


def summary_card(ctx: P.Ctx, t: bm.Task) -> Markup | None:
    """The first card of the Overview of a task whose events became one summary
    (`t.summary`): that they did, and why; what the summary keeps, with its values; what
    went with the events; and what its folder holds now (`files_line`), on Artifacts.
    None for any other task."""
    s = t.summary
    if s is None:
        return None
    now = ctx.model.now
    n = s.get("events") if isinstance(s.get("events"), int) else 0
    pr = bm.pr_of(t)
    v = bm.verdict_of(t)
    lead = bm.LEAD[bm.lead_of(t)] if t.lead else None
    careful = bm.careful_of(t)
    kept = [
        f"{t.info['label'].lower()} {bm.stamp(t.since, now)}",
        f"opened {bm.stamp(t.first, now)}",
        pr and f"pull request {pr['repo']}#{pr['n']}",
        v and ("green" if v["green"] else "not green"),
        t.type and f"type {t.type['type']}",
        lead and f"who worked on it: {lead['tag']}",
        careful and f"careful: {'yes' if careful['yes'] else 'no'}",
        t.branch and f"branch {t.branch}",
        "its last line, its ask and its card",
    ]
    return h(
        "section",
        {
            "class": "card verdict a-quiet",
            "id": "summary",
            "role": "status",
            "aria-label": "Its events became one summary",
        },
        h(
            "div",
            {"class": "v-line"},
            h("span", {"class": "fi"}, P.icon(ctx, "layers")),
            h(
                "div",
                {"class": "v-text"},
                h(
                    "b",
                    {"class": "v-word"},
                    f"Its {bm.plural(n, 'event')} became one summary:",
                ),
                (
                    " nothing of the task happened for state.keep_days days after its "
                    "end, so lem project prune kept one event in their place."
                ),
                h(
                    "div",
                    {"class": "sub", "id": "summary-kept"},
                    "It keeps: ",
                    "; ".join(x for x in kept if isinstance(x, str) and x),
                    ".",
                ),
                h(
                    "div",
                    {"class": "sub", "id": "summary-went"},
                    "What went with the events: ",
                    "; ".join(x[0].lower() + x[1:] for x in WENT.values()),
                    ".",
                ),
                h("div", {"class": "sub", "id": "summary-files"}, files_line(ctx, t)),
                h(
                    "div",
                    {"class": "b-lines"},
                    h("div", {"class": "b-line"}, artifacts_link(ctx, t)),
                ),
            ),
        ),
    )


def went_tab(ctx: P.Ctx, t: bm.Task, tab: str) -> list:
    """A tab of a summarized task whose detail went with its events: one line that says
    so, and where the files of its folder are listed."""
    return [
        h(
            "div",
            {"class": "lane-empty panel-empty", "id": f"went-{tab}"},
            (
                f"{WENT[tab]} went with its events: they became one summary, as "
                "nothing of the task happened for state.keep_days days after its end. "
                "The Overview shows what the summary keeps and what its folder holds, "
                "and Artifacts lists the files that are there. "
            ),
            artifacts_link(ctx, t),
        )
    ]


def overview_tab(ctx: P.Ctx, t: bm.Task) -> list:
    if t.summary is not None:
        # no phases and no stats: their checks, review and decisions went with the
        # events, and would read as none
        return [
            summary_card(ctx, t),
            building(ctx, t),
            verdict(ctx, t),
            now_card(ctx, t),
        ]
    return [
        answered_card(ctx, t),
        cards_card(ctx, t),
        merge_review_card(ctx, t),
        parked_card(ctx, t),
        breaker_card(ctx, t),
        building(ctx, t),
        verdict(ctx, t),
        now_card(ctx, t),
        progress(ctx, t),
    ]


# ---- Criteria and decisions ----


def criteria_head(ctx: P.Ctx, t: bm.Task) -> list:
    """What happened to the criteria before the build: the personas' read, the approval,
    and each change of an approved criterion."""
    now = ctx.model.now
    rows_ = []
    a = t.approvals[-1] if t.approvals else None
    r = t.reads[-1] if t.reads else None
    size = (t.criteria or {}).get("size") or (a or {}).get("size")
    run_by = lambda x: "the agent" if x["by"] == "lead" else "Lem"  # noqa: E731
    if r and r["answered"] == 0:
        rows_.append(
            row(
                ctx,
                "crit-read",
                "bad",
                "alert",
                [
                    h("b", None, "Nobody answered the personas’ read"),
                    (
                        f" (0 of {r['asked']}), run by {run_by(r)}: it found nothing, "
                        "either way"
                    ),
                    [
                        sub(f"no answer from {x.get('name')} ({x.get('why')})")
                        for x in r["silent"]
                        if isinstance(x, dict)
                    ],
                ],
                bm.stamp(r["ts"], now),
            )
        )
    elif r:
        doubt = r["split"] or bool(r["flagged"])
        stale = bm.read_stale(t, r)
        fams = r["families"]
        rows_.append(
            row(
                ctx,
                "crit-read",
                "you" if doubt else "done",
                "users",
                [
                    r["split"]
                    and h("b", None, "The two model families split on a criterion. "),
                    h(
                        "b",
                        None,
                        (
                            f"{r['flagged']} of "
                            f"{bm.criteria_count(r['criteria'] or 0)} flagged"
                        )
                        if r["flagged"]
                        else "Nobody confused",
                    ),
                    (
                        f" · read by {r['answered']} of {r['asked']} personas, "
                        f"{bm.FAMILIES.get(len(fams), f'{len(fams)} model families')} "
                        f"({', '.join(map(str, fams))}), run by {run_by(r)}"
                    ),
                    [
                        sub(f"no answer from {x.get('name')} ({x.get('why')})")
                        for x in r["silent"]
                        if isinstance(x, dict)
                    ],
                    stale and sub(stale),
                ],
                bm.stamp(r["ts"], now),
            )
        )
    elif size == "small":
        rows_.append(
            row(
                ctx,
                "crit-read",
                "quiet",
                "users",
                [
                    (
                        "The personas do not read the one criterion of a "
                        "task on the fast track."
                    )
                ],
            )
        )
    elif size:
        rows_.append(
            row(
                ctx,
                "crit-read",
                "quiet",
                "users",
                [
                    "The personas did not read these criteria."
                    if t.closed
                    else "The personas have not read these criteria yet."
                ],
            )
        )
    if a:
        said = {
            "owner": "Approved by you",
            "lem": "The fast track: Lem approved its one criterion in your name",
            "read": "Frozen by the personas’ read, with no wait for you",
            "alone": "Approved without you, as the task ran alone",
        }.get(a["by"], f"Approved by {a['by']}")
        replaces = a["replaces"]
        rows_.append(
            row(
                ctx,
                "crit-approved",
                "done" if a["by"] == "owner" else "quiet",
                "check"
                if a["by"] == "owner"
                else "users"
                if a["by"] == "read"
                else "user",
                [
                    h("b", None, said),
                    (
                        " after the personas’ read"
                        if r["order"] < a["order"]
                        else " before the personas’ read was in"
                    )
                    if r and a["by"] == "owner"
                    else "",
                    a["by"] == "lem"
                    and sub(
                        "You may still say “/lem standard-track”: then the personas "
                        "read it, and your approval replaces this one."
                    ),
                    a["by"] == "read"
                    and sub(
                        "The whole request was written, and nobody was confused: "
                        "the build started, and you can still stop it "
                        "or change a criterion."
                    ),
                    ((a["number"] or 0) > 1 or replaces is not None)
                    and sub(
                        f"approval {a['number']}"
                        + (
                            f"; it replaces approval {replaces}"
                            if isinstance(replaces, int)
                            else "; it replaces an earlier approval"
                            if replaces
                            else ""
                        )
                    ),
                ],
                bm.stamp(a["ts"], now),
            )
        )
    for c in t.changes:
        said = (
            f"was “{c['was']}”, now “{c['now']}”"
            if c["how"] == "changed"
            else f"“{c['now']}”"
            if c["how"] == "added"
            else f"was “{c['was']}”"
        )
        said_by = f": {c['said']}" if c.get("said") else ""
        who = (
            f"after decision {c['decision']}"
            if c["decision"] is not None
            else f"by {bm.BY_WHOM.get(c['by'], c['by'])}{said_by}"
        )
        his = bm.taken_over(t, c)
        how = (
            "changed"
            if c["how"] == "changed"
            else "was added"
            if c["how"] == "added"
            else "was removed"
        )
        rows_.append(
            row(
                ctx,
                f"crit-change-{c['change']}",
                "done" if his else "you",
                "check" if his else "alert",
                [
                    h("b", None, f"Criterion {c['criterion']} {how} during the build"),
                    sub(said),
                    sub(
                        f"{c['why']} · {who} · ",
                        (
                            f"Approved by you afterwards (approval {his}): "
                            "it is yours, and no cause of not green"
                        )
                        if his
                        else "the pull request is not green for it",
                    ),
                ],
                bm.stamp(c["ts"], now),
            )
        )
    return rows_


def criteria_rows(ctx: P.Ctx, t: bm.Task) -> list:
    head_ = criteria_head(ctx, t)
    current = bm.standing(t)
    if current is not None and not bm.plan_criteria_stand(t):
        note = (
            (
                (
                    "approved after the plan’s criteria were recorded, "
                    "which were not recorded again"
                )
                if t.closed
                else (
                    "approved after the plan’s criteria were recorded: "
                    "the agent records them again, with their tests"
                )
            )
            if t.criteria
            else "no test of it is on record: the plan’s criteria were never recorded"
            if t.closed
            else "no test yet: the agent adds its tests in the plan"
        )

        def said(i: int, text: str, chart: str | None) -> list:
            first, *steps = text.split("\n")
            return [
                h("b", None, f"{i}. "),
                P.rich(ctx, first),
                case_list(ctx, steps),
                chart and P.chart_block(ctx, f"crit-{t.slug}-{i}", chart),
                sub(note),
            ]

        return [
            *head_,
            *[
                row(
                    ctx,
                    f"criterion-{i}",
                    "quiet",
                    "file",
                    said(i, text, current["charts"][i - 1]),
                )
                for i, text in enumerate(current["texts"], 1)
            ],
        ]
    if not t.criteria:
        return head_ or [
            h(
                "div",
                {"class": "empty", "id": "crit-empty"},
                "The agent writes the acceptance criteria at the top of the plan",
            )
        ]
    out = list(head_)
    for st in bm.criterion_checks(t):
        icon_ = (
            "alert"
            if st["state"] == "bad"
            else "check"
            if st["state"] == "done"
            else "file"
        )
        tests = [
            sub(command or "", " · ", said, cls="sub cmd")
            for command, said in st["tests"]
        ]
        out.append(
            row(
                ctx,
                f"criterion-{st['n']}",
                st["state"],
                icon_,
                [
                    h("b", None, f"{st['n']}. "),
                    P.rich(ctx, st["text"]),
                    case_list(ctx, st["case"]),
                    st["chart"]
                    and P.chart_block(ctx, f"crit-{t.slug}-{st['n']}", st["chart"]),
                    tests,
                    st["no_test"] and sub(f"no test: {st['no_test']}"),
                    not st["tests"]
                    and not st["no_test"]
                    and sub("no test" if t.closed else "no test yet"),
                ],
                st["label"],
            )
        )
    return out


CASE_WAS: dict[object, str] = {
    "reproduced": "reproduced: a run showed it",
    "derived": "derived from the code, not run",
}
_land = None
# The longest label of an option that shows as a key, in bold before its text; a longer
# one is a line of its own.
KEY_LABEL_LONGEST = 3


def option_parts(option: object) -> tuple[str, str]:
    """An option's label and what the person sees after it ("LABEL: what the person sees
    after it"), cut by land.py's own rule (`label`: never at a colon inside a quote);
    ("", the option) when it has no label."""
    global _land  # noqa: PLW0603 - land.py is loaded once, at the first option
    if _land is None:
        from lem import land

        _land = land
    text = str(option)
    head = _land.label(text)
    if ":" in text and head != _land.one_line(text):
        return head, text.partition(":")[2].strip()
    return "", text


def picks_of(d: bm.Decision) -> dict[str, list[str]]:
    """The experts who took a decision, by the option they picked: each expert that
    answers on the machine (`advisers`) picked the option taken."""
    if d.by != "experts":
        return {}
    return {str(d.chose): [bm.expert_name(key) for key in bm.advisers_of(d)]}


def options_rows(ctx: P.Ctx, d: bm.Decision, at: int) -> Markup | None:
    """ "This or that": each option on its row, its label and what it leads to, the one
    taken marked, and the experts who picked it."""
    if not d.options:
        return None
    picks = picks_of(d)
    rows_ = []
    for k, option in enumerate(d.options):
        text = str(option)
        label, leads = option_parts(text)
        taken = k == at
        marks = [
            taken
            and h("span", {"class": "o-mark taken"}, P.icon(ctx, "check"), "taken"),
            *[
                h("span", {"class": "o-mark expert"}, f"{name} picked it")
                for name in picks.get(text, [])
            ],
        ]
        rows_.append(
            h(
                "li",
                {"class": f"opt{' taken' if taken else ''}"},
                h("span", {"class": "o-dot"}, P.icon(ctx, "check") if taken else None),
                h(
                    "div",
                    {"class": "o-body"},
                    h(
                        "div",
                        {"class": "o-text"},
                        h("b", {"class": "o-key"}, label),
                        " ",
                        P.rich(ctx, leads),
                    )
                    if label and len(label) <= KEY_LABEL_LONGEST
                    else [
                        label and h("div", {"class": "o-label"}, P.rich(ctx, label)),
                        h("div", {"class": "o-text"}, P.rich(ctx, leads)),
                    ],
                    any(marks) and h("div", {"class": "o-marks"}, marks),
                ),
            )
        )
    return h("ol", {"class": "opts"}, rows_)


def story(
    ctx: P.Ctx, t: bm.Task, d: bm.Decision, at: int, who: str | None = None
) -> list:
    """A decision's story, in the order of its record: the case as numbered steps and
    how it is known, why it could happen, this or that, who took it, and its chart. A
    record with no story gives what it has, with no empty heading."""
    out = []
    if d.case:
        out.append(
            h(
                "div",
                {"class": "st-part"},
                h(
                    "div",
                    {"class": "st-label"},
                    "The case",
                    d.case_was
                    and h(
                        "span",
                        {"class": "st-was"},
                        f" · {CASE_WAS.get(d.case_was, d.case_was)}",
                    ),
                ),
                case_list(ctx, d.case),
            )
        )
    if d.cause:
        out.append(
            h(
                "div",
                {"class": "st-part"},
                h("div", {"class": "st-label"}, "Why it could happen"),
                h("p", {"class": "st-cause"}, P.rich(ctx, d.cause)),
            )
        )
    opts = options_rows(ctx, d, at)
    if opts:
        out.append(
            h(
                "div",
                {"class": "st-part"},
                h("div", {"class": "st-label"}, "This or that"),
                opts,
                d.chose is not None
                and at < 0
                and h(
                    "div",
                    {"class": "sub"},
                    "taken, none of these: “",
                    P.rich(ctx, d.chose),
                    "”",
                ),
            )
        )
    if out and who:
        out.append(
            h(
                "div",
                {"class": "st-part"},
                h("div", {"class": "st-label"}, "Who took it"),
                h("p", {"class": "st-cause"}, P.rich(ctx, who)),
            )
        )
    if isinstance(d.chart, str) and d.chart:
        out.append(
            h(
                "div",
                {"class": "st-part"},
                P.chart_block(ctx, f"dec-{t.slug}-{d.id}", d.chart),
            )
        )
    return out


def decision_row(ctx: P.Ctx, t: bm.Task, d: bm.Decision) -> Markup:
    """A decision taken, by an agent, a level of the ladder or the owner, as one row
    that opens: closed, its note, what was chosen and by whom; opened, its story (the
    case, the cause, this or that, its chart), then who took it and how, the ladder,
    what undoes it. An important one is open at first."""
    now = ctx.model.now
    says = bm.decision_says(t, d)
    why = says["why"]
    name = (
        "alert"
        if why
        else "user"
        if d.by == "owner"
        else "users"
        if d.by == "personas"
        else "check"
    )

    def part(key: str, label: str, *kids: object) -> Markup | None:
        shown = [k for k in kids if k not in (None, "", False, [])]
        return (
            h(
                "div",
                {"class": "dec-part"},
                h("span", {"class": "dec-label"}, label),
                h("div", {"class": "dec-says"}, shown),
            )
            if shown
            else None
        )

    def listed(items: list) -> Markup | None:
        return h("ul", None, items) if items else None

    told = story(ctx, t, d, says["at"], bm.cap(says["how"]))
    return h(
        "details",
        {
            "class": f"dec a-{'you' if why else 'done'}{' important' if why else ''}",
            "id": f"dec-{d.id}",
            "open": bool(why),
        },
        h(
            "summary",
            {"class": "dec-head"},
            h("span", {"class": "fi"}, P.icon(ctx, name)),
            h(
                "span",
                {"class": "dec-main"},
                h(
                    "span",
                    {"class": "dec-top"},
                    why
                    and h(
                        "span",
                        {"class": "dec-mark", "title": f"Important: {why}"},
                        P.icon(ctx, "alert"),
                        "important",
                    ),
                    h(
                        "span",
                        {"class": "dec-what", "title": str(d.what or "")},
                        f"{d.id}. {d.what}",
                    ),
                ),
                h(
                    "span",
                    {
                        "class": "dec-chose",
                        "title": str(d.chose) if d.chose is not None else None,
                    },
                    "→ ",
                    h("b", None, "" if d.chose is None else P.rich(ctx, d.chose)),
                ),
                h(
                    "span",
                    {"class": "dec-by"},
                    f"{says['who']} · {bm.stamp(d.ts, now)}",
                ),
            ),
        ),
        told and h("div", {"class": "dec-story"}, told),
        h(
            "div",
            {"class": "dec-body"},
            part("note", "The decision", P.rich(ctx, d.what or "")),
            part("important", "Important", bm.cap(why) if why else ""),
            None
            if any("Who took it" in str(x) for x in told)
            else part("how", "Who took it", P.rich(ctx, bm.cap(says["how"]))),
            None
            if told
            else part(
                "options",
                "Options",
                listed([h("li", None, P.rich(ctx, o)) for o in d.options]),
            ),
            part(
                "ladder",
                "The ladder",
                listed(
                    [
                        h("li", None, h("b", None, f"{name_}: "), P.rich(ctx, said))
                        for _, name_, said in says["levels"]
                    ]
                ),
            ),
            part("personas", "The personas", P.rich(ctx, d.said or "")),
            part("undo", "To undo", P.rich(ctx, d.undo or "")),
        ),
    )


def breaker_row(ctx: P.Ctx, t: bm.Task, d: bm.Decision) -> Markup:
    """A breaker as one row that opens, in the look of a decision: what stopped the
    build and why, where it stands (it waits for the owner, for nobody while the task is
    parked, helped by a decision of his, or the task ended), its document and its
    handoff on Artifacts, and the decision that helped it. One that waits is open
    at first."""
    now = ctx.model.now
    says = bm.breaker_says(t, d)

    def part(label: str, *kids: object) -> Markup | None:
        shown = [k for k in kids if k not in (None, "", False, [])]
        return (
            h(
                "div",
                {"class": "dec-part"},
                h("span", {"class": "dec-label"}, label),
                h("div", {"class": "dec-says"}, shown),
            )
            if shown
            else None
        )

    def file_link(name: object, label: str) -> Markup | None:
        if not name or not any(f["path"] == name for f in ctx.artifact_files):
            return None
        return h(
            "a",
            {
                "class": "rlink",
                **P.frame_link(ctx, P.task_href(ctx, t.slug, "artifacts", str(name))),
                "title": f"Open {name} on Artifacts",
            },
            label,
            " ",
            P.icon(ctx, "arrow"),
        )

    helped = d.help is not None and h(
        "a",
        {
            "class": "rs-to",
            "href": f"#dec-{d.help}",
            "data-row": f"dec-{d.help}",
            "title": f"Decision {d.help}, your help",
        },
        f"decision {d.help}",
    )
    waits = says["actor"] == "you"
    return h(
        "details",
        {
            "class": f"dec a-{says['actor']}{' important' if waits else ''}",
            "id": f"dec-{d.id}",
            "open": waits,
        },
        h(
            "summary",
            {"class": "dec-head"},
            h("span", {"class": "fi"}, P.icon(ctx, "alert")),
            h(
                "span",
                {"class": "dec-main"},
                h(
                    "span",
                    {"class": "dec-top"},
                    h(
                        "span",
                        {"class": "dec-mark", "title": says["why"]},
                        P.icon(ctx, "alert"),
                        "breaker",
                    ),
                    h(
                        "span",
                        {"class": "dec-what", "title": str(d.what or "")},
                        f"{d.id}. {d.what}",
                    ),
                ),
                h("span", {"class": "dec-chose"}, h("b", None, bm.cap(says["why"]))),
                h(
                    "span",
                    {"class": "dec-by"},
                    f"{says['now']} · {bm.stamp(d.ts, now)}",
                ),
            ),
        ),
        h(
            "div",
            {"class": "dec-body"},
            part("Now", bm.cap(says["now"]), helped and [" · ", helped]),
            part(
                "Its files",
                file_link(d.document, "the document"),
                " · " if d.handoff and d.document else None,
                file_link(d.handoff, "the handoff"),
            ),
            part("Where you answer", waits and P.rich(ctx, bm.answer_of(t))),
            part("Carried over", says["copied"] or ""),
        ),
    )


def decision_rows(ctx: P.Ctx, t: bm.Task) -> list:
    """Each decision and each breaker of the build: the breaker that waits first, then
    the important decisions, then every other one with the breakers that no longer wait,
    each group in the record's order."""
    now = ctx.model.now
    if not t.decided and not t.orphans:
        return [
            h(
                "div",
                {"class": "empty", "id": "dec-empty"},
                (
                    "Each decision the build takes, and each breaker that stops it, "
                    "comes here"
                ),
            )
        ]
    first = [d for d in t.decided if t.stopped is d]
    rest = [d for d in t.decided if d is not t.stopped]
    ordered = [
        *first,
        *[d for d in rest if bm.importance(t, d)],
        *[d for d in rest if not bm.importance(t, d)],
    ]
    out = [
        breaker_row(ctx, t, d) if d.kind == "breaker" else decision_row(ctx, t, d)
        for d in ordered
    ]
    out.extend(
        row(
            ctx,
            f"orphan-{o['id']}-{o['ts']}",
            "bad",
            "alert",
            [
                (
                    f"Your help, decision {o['id']}, names breaker {o['breaker']}, "
                    "which is not in the log"
                ),
                f": {o['chose']}" if o.get("chose") else "",
            ],
            bm.stamp(o["ts"], now),
        )
        for o in t.orphans
    )
    return out


def how_card(ctx: P.Ctx, t: bm.Task) -> Markup | None:
    """The plan's `## How it works`, its sentences and its chart, above the criteria, as
    criteria.py reads it (`how`); a plan that has none, or no plan, has no card."""
    how = ctx.how_of(t.slug)
    if not how:
        return None
    return h(
        "section",
        {"class": "card how", "id": "how-card"},
        h(
            "div",
            {"class": "card-head"},
            h("h2", None, "How it works"),
            h("div", {"class": "dim small"}, "from the plan"),
        ),
        P.md_block(ctx, f"how-{t.slug}", how),
    )


def approve_holds_form(ctx: P.Ctx, t: bm.Task) -> bool:
    """Whether the approval card of the criteria tab holds the owner's button: the
    criteria wait for a yes that would count, criteria.md is in the task directory, and
    the page may act."""
    return (
        ctx.can_act
        and "approve" in bm.acts_of(t, ctx.model.seen)
        and ctx.criteria_waiting(t.slug) is not None
    )


# Each side of a pair of a change of the criteria (criteria.py `pairs`), as its label
# says it.
PAIR_SIDES = {
    "changed": (("before", "Before"), ("after", "Now")),
    "removed": (("before", "Removed"),),
    "added": (("after", "Added"),),
}


def criterion_text(ctx: P.Ctx, c: dict) -> Markup:
    """One criterion of a pair: its sentence, and the steps of its case as a list."""
    case = [str(x) for x in c.get("case") or []]
    return h(
        "div",
        {"class": "cf-text"},
        h("p", None, P.rich(ctx, c.get("text") or "")),
        case and h("ul", None, [h("li", None, P.rich(ctx, step)) for step in case]),
    )


def change_block(ctx: P.Ctx, change: dict, words: str | None) -> Markup:
    """The change of the criteria from the owner's note (`bm.change_of`), above the
    whole criteria: his note, and each changed criterion's text before beside its new
    text, a removed one with its text before and an added one with its new text. Side by
    side on a wide screen, one under the other on a phone (board.css), each wrapped, so
    nothing is cut off."""
    said = (
        f"Lem changed them from your note “{words}”."
        if words
        else "Lem changed them from your note."
    )
    if change.get("error"):
        return h(
            "div",
            {"class": "cf-change"},
            h(
                "p",
                {"class": "sub"},
                f"{said} The text before the change does not read: {change['error']}.",
            ),
        )
    pairs = []
    for pair in change.get("pairs") or []:
        sides = [
            h(
                "div",
                {"class": f"cf-side cf-{key}"},
                h(
                    "div",
                    {"class": "cf-label"},
                    f"{label} · criterion {pair[key]['n']}",
                ),
                criterion_text(ctx, pair[key]),
            )
            for key, label in PAIR_SIDES.get(pair.get("change"), ())
        ]
        pairs.append(h("div", {"class": f"cf-pair cf-{pair.get('change')}"}, sides))
    return h(
        "div",
        {"class": "cf-change"},
        h(
            "p",
            {"class": "sub"},
            said,
            (
                " Each changed criterion shows its text before beside its new text; "
                "the whole criteria follow."
            ),
        ),
        h("div", {"class": "cf-pairs"}, pairs),
    )


def approve_card(ctx: P.Ctx, t: bm.Task, note: Markup | None = None) -> Markup | None:
    """The criteria that wait for the owner's yes, as the task's session wrote them
    (`criteria.md` of the task directory), first on "Criteria and decisions", with the
    personas' read in one line and his answer under them on a page that may act. None
    while they do not wait for a yes that would count. While they have a row the board
    answers (`bm.answer_row`: the fast track's one criterion, the standard track's
    criteria on a task of the board's release) the answer is the one answer form, Yes,
    or No with his words, and the digest of the text shown; else one button, "Approve
    the criteria". After a change from his note (`bm.change_of`) each changed
    criterion's text before stands beside its new text, above the whole criteria; while
    that change stopped in the middle (`Task.changing`) the card says the new request
    comes, and takes no answer. A card that holds an answer is an act's step
    (`confirm_card`): on a phone's screen an overlay whose button comes on when the
    criteria were read to the end, with "Back" to the Overview, which a desktop does not
    show. Its body holds the act's NOTE first, which the overlay would cover above the
    card, and after the markdown block the criteria as plain text for a browser with no
    script, which draws the markdown block empty."""
    if t.changing and not t.closed:
        return h(
            "section",
            {"class": "card approve a-you", "id": "approve-card"},
            h(
                "div",
                {"class": "card-head"},
                h("h2", None, "The criteria change from your note"),
            ),
            h(
                "div",
                {"class": "approve-body"},
                h(
                    "p",
                    {"class": "sub"},
                    (
                        "Lem writes the changed criteria: the new request comes in a "
                        "moment, with each changed criterion’s text "
                        "before beside its new text."
                    ),
                ),
            ),
        )
    if "approve" not in bm.acts_of(t, ctx.model.seen):
        return None
    waiting = ctx.criteria_waiting(t.slug)
    change = bm.change_of(t, waiting)
    r = t.reads[-1] if t.reads else None
    read = None
    if r:
        read = (
            "Nobody answered the personas’ read."
            if r["answered"] == 0
            else (
                f"The personas flagged {r['flagged']} of "
                f"{bm.criteria_count(r['criteria'] or 0)}"
                f"{'; the two model families split' if r['split'] else ''}: "
                "read the flagged one before you approve."
            )
            if r["flagged"] or r["split"]
            else "The personas read them, and nobody was confused."
        )
    head_ = h(
        "div",
        {"class": "card-head"},
        h("h2", None, "The criteria wait for your yes"),
        h("div", {"class": "dim small"}, read or "criteria.md in the task directory"),
    )
    asks = bm.answer_row(t)
    criterion = asks if asks and asks["kind"] == "criterion" else None
    made = bm.answered_of(t, ctx.model) if criterion else None
    changed = (
        change_block(ctx, change, waiting.get("words")) if change and waiting else None
    )
    if waiting is not None and made is not None:
        body = [
            note,
            changed,
            P.md_block(
                ctx, f"waiting-{t.slug}", waiting["text"], slug=t.slug, cls="b-md"
            ),
            h(
                "p",
                {"class": "sub"},
                f"{bm.ANSWER_ON_RECORD} {lem_answers.took_effect(made)}.",
            ),
        ]
        return h(
            "section",
            {"class": "card approve a-you", "id": "approve-card"},
            head_,
            h("div", {"class": "approve-body"}, body),
        )
    if waiting is not None and ctx.can_act and criterion:
        # his Yes or No under the text, in the one answer form, with the digest of the
        # text shown: a No needs his words, which go into the fast track's criteria.md
        # as they are, and from which the standard track's session writes the changed
        # criteria and asks again
        body = [
            note,
            changed,
            P.md_block(
                ctx, f"waiting-{t.slug}", waiting["text"], slug=t.slug, cls="b-md"
            ),
            h("noscript", None, h("pre", {"class": "cf-plain"}, waiting["text"])),
        ]
        form = P.answer_form(
            ctx,
            t,
            criterion,
            "panel",
            ctx.view,
            digest=waiting["digest"],
            tab="criteria",
        )
        return confirm_card(
            "card approve a-you",
            "Approve the criterion" if bm.fast_criterion(t) else "Approve the criteria",
            head_,
            body,
            h(
                "div",
                {"class": "act-row cf-acts"},
                form,
                act_back(ctx, t, "Back", "cf-back"),
            ),
            sheet=True,
            card_id="approve-card",
            wrap="approve-body",
        )
    if waiting is not None and ctx.can_act:
        body = [
            note,
            changed,
            P.md_block(
                ctx, f"waiting-{t.slug}", waiting["text"], slug=t.slug, cls="b-md"
            ),
            h("noscript", None, h("pre", {"class": "cf-plain"}, waiting["text"])),
        ]
        form = P.act_form(
            ctx,
            t.slug,
            "approve",
            "Approve the criteria",
            "check",
            "go",
            "Approving…",
            {
                "digest": waiting["digest"],
                "tab": "criteria",
                "in": ctx.view if ctx.view != "tasks" else None,
            },
            h(
                "span",
                {"class": "act-say"},
                (
                    "Your yes freezes them as they stand here, "
                    "and the task’s session goes on from it."
                ),
            ),
        )
        return confirm_card(
            "card approve a-you",
            "Approve the criteria",
            head_,
            body,
            h(
                "div",
                {"class": "act-row cf-acts"},
                form,
                act_back(ctx, t, "Back", "cf-back"),
            ),
            sheet=True,
            card_id="approve-card",
            wrap="approve-body",
        )
    if waiting is None:
        body = [
            h(
                "p",
                {"class": "sub"},
                (
                    "The task’s session writes them to criteria.md in the task "
                    "directory, and the board shows them here then. "
                    "Until then, approve them in the task’s session."
                ),
            )
        ]
    else:
        body = [
            changed,
            P.md_block(
                ctx, f"waiting-{t.slug}", waiting["text"], slug=t.slug, cls="b-md"
            ),
            h(
                "p",
                {"class": "sub"},
                (
                    "Approve them in the task’s session, or on this board on the Mac "
                    "or through the tailnet door."
                ),
            ),
        ]
    return h(
        "section",
        {"class": "card approve a-you", "id": "approve-card"},
        head_,
        h("div", {"class": "approve-body"}, body),
    )


def criteria_tab(ctx: P.Ctx, t: bm.Task) -> list:
    """The criteria, the decisions and, while the criteria wait for the owner's yes, the
    approval first, with the act's note first in the tab, or first in the approval card
    while that holds the button."""
    note = note_card(ctx, t.slug)
    if t.summary is not None:
        return [note, *went_tab(ctx, t, "criteria")]
    crit = criteria_rows(ctx, t)
    decs = decision_rows(ctx, t)
    # a card of a task that ended with nothing in it is not drawn; a tab whose cards are
    # all gone says so
    empty = lambda rows_: t.closed and all('class="empty"' in str(x) for x in rows_)  # noqa: E731
    cards = [
        None
        if empty(crit)
        else card("criteria-card", "Acceptance criteria", bm.criteria_sum(t), crit),
        None
        if empty(decs)
        else card("decisions-card", "Decisions", bm.decisions_sum(t), decs),
    ]
    cards = [c for c in cards if c]
    if cards:
        how = how_card(ctx, t)
        inside = approve_holds_form(ctx, t)
        return [
            None if inside else note,
            approve_card(ctx, t, note if inside else None),
            *([how] if how else []),
            *cards,
        ]
    return [
        note,
        h(
            "div",
            {"class": "lane-empty panel-empty"},
            "The task ended with no criteria and no decision on record",
        ),
    ]


# ---- Checks and review ----


def log_link(ctx: P.Ctx, t: bm.Task, k: int) -> Markup | None:
    """The link to the output of the k-th command of the last run of the checks
    (`gate/NN.log`, as land.py numbers them in the order they ran), where the task's
    folder has it."""
    path = f"gate/{k + 1:02d}.log"
    if not any(f["path"] == path for f in ctx.artifact_files):
        return None
    return h(
        "a",
        {
            "class": "log-link",
            **P.frame_link(ctx, P.task_href(ctx, t.slug, "artifacts", path)),
            "title": f"Open its output, {path}",
        },
        P.icon(ctx, "terminal"),
        "output",
    )


def checks_tab(ctx: P.Ctx, t: bm.Task) -> list:
    if t.summary is not None:
        return went_tab(ctx, t, "checks")
    now = ctx.model.now
    gates = [
        row(
            ctx,
            f"gate-{k}",
            "done" if g["exit"] == 0 else "bad",
            "check" if g["exit"] == 0 else "alert",
            [
                h("b", None, "green" if g["exit"] == 0 else f"exit {g['exit']}"),
                " · ",
                h("span", {"class": "cmd"}, g["command"] or ""),
                log_link(ctx, t, k),
                sub(
                    g["last"] or "",
                    f" · on {g['tip']}" if g["tip"] else "",
                    cls="sub cmd",
                ),
            ],
            bm.stamp(g["ts"], now),
        )
        for k, g in enumerate(t.gates)
    ]
    if t.checks_stop and not gates:
        end = bm.checks_end(t.checks_stop.get("result"))
        gates = [
            row(
                ctx,
                "gate-end",
                "lem" if t.checks_stop.get("result") == "stopped" else "bad",
                "x" if t.checks_stop.get("result") == "stopped" else "alert",
                [h("b", None, end["head"]), sub(bm.say_of(t.checks_stop))],
            )
        ]
    if not gates:
        gates = [
            h(
                "div",
                {"class": "empty", "id": "gate-empty"},
                "The checks run when the branch’s turn to land comes",
            )
        ]
    reviews = []
    for k, r in enumerate(t.reviews):
        silent = "".join(
            f" · no answer from {x.get('name')} ({x.get('why')})"
            for x in r["silent"]
            if isinstance(x, dict)
        )

        def names(xs: list) -> str:
            return ", ".join(
                str(x.get("name") if isinstance(x, dict) else x) for x in xs
            )

        reviews.append(
            row(
                ctx,
                f"review-{k}",
                "done" if r["verdict"] == "clean" else "bad",
                "check" if r["verdict"] == "clean" else "eye",
                [
                    h("b", None, bm.review_line(r)),
                    sub(
                        f"answered: {', '.join(map(str, r['answered']))}"
                        if r["answered"]
                        else "no source answered",
                        silent,
                        f" · ran {names(r['ran'])}" if r["ran"] else "",
                        f" · left out {names(r['left_out'])}" if r["left_out"] else "",
                        f" · on {r['tip']}" if r["tip"] else "",
                    ),
                ],
                bm.stamp(r["ts"], now),
            )
        )
    if t.proposal:
        green = t.proposal["green"]
        reasons = t.proposal["reasons"]
        reviews.append(
            row(
                ctx,
                "proposal",
                "done" if green else "you",
                "check" if green else "alert",
                [
                    h(
                        "b",
                        None,
                        "Proposed: green"
                        if green
                        else (
                            "Proposed: not green, for "
                            f"{bm.plural(len(reasons), 'reason')}"
                        )
                        if reasons
                        else "Proposed: not green",
                    ),
                    sub(bm.GREEN.lower())
                    if green
                    else P.reason_list(ctx, t, reasons, "pr"),
                ],
                bm.stamp(t.proposal["ts"], now),
            )
        )
    if not reviews:
        reviews = [
            h(
                "div",
                {"class": "empty", "id": "review-empty"},
                (
                    "The review comes after the machine checks, "
                    "before anything is proposed"
                ),
            )
        ]
    gate_sum = (
        (
            f"{t.gate_bad} of {len(t.gates)} red"
            if t.gate_bad
            else f"{bm.plural(len(t.gates), 'command')} green"
        )
        if t.gates
        else ""
    )
    rounds = [x for x in t.reviews if x["of"] != "resolution"]
    review_sum = " · ".join(
        p
        for p in (
            t.reviews and bm.plural(len(rounds), "round"),
            any(x["of"] == "resolution" for x in t.reviews)
            and "a read of a resolution",
        )
        if p
    )
    empty = lambda rows_: t.closed and all('class="empty"' in str(x) for x in rows_)  # noqa: E731
    cards = [
        None if empty(gates) else card("gate-card", "Checks", gate_sum, gates),
        None if empty(reviews) else card("review-card", "Review", review_sum, reviews),
    ]
    return [c for c in cards if c] or [
        h(
            "div",
            {"class": "lane-empty panel-empty"},
            "The task ended with no checks and no review on record",
        )
    ]


# ---- Timeline ----


def pct(ms: float, t0: float, whole: float) -> float:
    return 100 * min(whole, max(0, ms - t0)) / whole


def tip(head_: str, said: str, frm: float, to: float | str, fill: str | None) -> dict:
    """The attributes the hover reads (the tip controller): what a mark is, and its
    two times."""
    return {
        "data-head": head_,
        "data-sub": said or None,
        "data-from": int(frm),
        "data-to": to if to == "now" else int(to),
        "data-fill": fill,
    }


def time_card(ctx: P.Ctx, t: bm.Task) -> Markup:
    """Where the time of the task went: one lane for each who held the work, the stages
    as bands behind them, a mark for what logged only its end, and the shares of each in
    the legend."""
    m = ctx.model
    end = bm.time_end(t, m.now)
    tm = bm.time_of(t, end, m.meta)
    rows_ = bm.time_rows(tm)
    whole = bm.nice_ceil(max(60000, tm["end"] - tm["t0"]))
    t0 = tm["t0"]
    shares = bm.time_shares(tm, rows_)
    legend = [h("span", {"class": "whole"}, f"{bm.span(tm['whole'])} in all")]
    legend.extend(
        h(
            "span",
            {
                "title": (
                    f"{r['label']} held the work for {bm.span(tm['totals'][r['key']])} "
                    f"of the task’s {bm.span(tm['whole'])}"
                )
            },
            h("i", {"style": f"background:{r['fill']}"}),
            r["label"],
            h(
                "em",
                None,
                f"{bm.span(tm['totals'][r['key']])} · {shares['share'][r['key']]}%",
            ),
        )
        for r in shares["held"]
    )
    if shares["over"]:
        legend.append(
            h(
                "span",
                {"class": "over"},
                (
                    f"the shares add up to {shares['over']}%, "
                    "as two rows can hold the same minutes"
                ),
            )
        )
    bands = []
    for i, b in enumerate(tm["bands"]):
        x1, x2 = (
            pct(b["from"], t0, whole),
            pct(tm["end"] if b["live"] else b["to"], t0, whole),
        )
        bands.append(
            h(
                "span",
                {
                    "class": (
                        f"tt-band{' odd' if i % 2 else ''}{' hot' if b['live'] else ''}"
                    ),
                    "id": f"tb-{t.slug}-{i}",
                    "style": f"left:{x1:.3f}%;width:{max(0.0, x2 - x1):.3f}%",
                    **tip(
                        b["label"],
                        b.get("sub") or "",
                        b["from"],
                        "now" if b["live"] else b["to"],
                        None,
                    ),
                },
                h("em", None, b["short"]),
            )
        )
    grid = [
        h("i", {"class": "tt-grid", "style": f"left:{100 * i / 6:.3f}%"})
        for i in range(7)
    ]
    now_line = (
        None
        if t.closed
        else h(
            "i", {"class": "tt-now", "style": f"left:{pct(tm['end'], t0, whole):.3f}%"}
        )
    )
    lanes = []
    for k, r in enumerate(rows_, 2):
        marks_ = []
        seen: dict[str, int] = {}
        for g in (x for x in tm["spans"] if x["row"] == r["key"]):
            x1, x2 = (
                pct(g["from"], t0, whole),
                pct(tm["end"] if g["live"] else g["to"], t0, whole),
            )
            key = f"ts-{r['key']}-{int(g['from'])}"
            seen[key] = seen.get(key, 0) + 1
            marks_.append(
                h(
                    "span",
                    {
                        "class": f"tt-seg{' live' if g['live'] else ''}",
                        "id": f"{key}-{seen[key]}",
                        "style": (
                            f"left:{x1:.3f}%;width:max(2px, "
                            f"{x2 - x1:.3f}%);background:{r['fill']}"
                        ),
                        **tip(
                            f"{r['label']} · {g['head']}",
                            g["sub"],
                            g["from"],
                            "now" if g["live"] else g["to"],
                            r["fill"],
                        ),
                    },
                )
            )
        for g in (x for x in tm["marks"] if x["row"] == r["key"]):
            key = f"tm-{r['key']}-{int(g['at'])}"
            seen[key] = seen.get(key, 0) + 1
            marks_.append(
                h(
                    "span",
                    {
                        "class": "tt-mark",
                        "id": f"{key}-{seen[key]}",
                        "style": (
                            f"left:{pct(g['at'], t0, whole):.3f}%;"
                            f"background:{r['fill']}"
                        ),
                        **tip(
                            f"{r['label']} · {g['head']}",
                            g["sub"],
                            g["at"],
                            g["at"],
                            r["fill"],
                        ),
                    },
                )
            )
        lanes.append(
            h(
                "div",
                {"class": "tt-label", "style": f"grid-row:{k}"},
                h("i", {"style": f"background:{r['fill']}"}),
                r["label"],
            )
        )
        lanes.append(
            h(
                "div",
                {"class": "tt-track", "id": f"tt-{r['key']}", "style": f"grid-row:{k}"},
                marks_,
            )
        )
    # a tick names its date only where the axis passes into another day; the axis's
    # first day stands at its left
    labels = [
        bm.tick_label(t0 + whole * i / 6, whole, t0 + whole * (i - 1) / 6 if i else t0)
        for i in range(7)
    ]
    ticks = [
        P.tick(
            f"tt-tick{' first' if i == 0 else ' last' if i == len(labels) - 1 else ''}",
            100 * i / 6,
            label,
        )
        for i, label in enumerate(labels)
    ]
    dated = any(" " in label for label in labels)
    first_day = (
        "today" if bm.local(t0).date() == bm.local(m.now).date() else bm.day_label(t0)
    )
    plot = h(
        "div",
        {
            "class": "tt-plot",
            "style": (
                f"grid-template-rows:22px repeat({len(rows_)}, "
                f"25px) {34 if dated else 22}px"
            ),
        },
        h(
            "div",
            {"class": "tt-back", "style": f"grid-row:1 / {len(rows_) + 2}"},
            bands,
            grid,
            now_line,
        ),
        lanes,
        h("div", {"class": "tt-day", "style": f"grid-row:{len(rows_) + 2}"}, first_day),
        h("div", {"class": "tt-axis", "style": f"grid-row:{len(rows_) + 2}"}, ticks),
    )
    return h(
        "section",
        {"class": f"card a-{t.info['actor']}", "id": "tl-card"},
        h(
            "div",
            {"class": "card-head"},
            h("h2", None, "Where the time went"),
            h(
                "div",
                {
                    "class": "legend",
                    "id": "tl-legend",
                    "title": (
                        "Two rows can hold the same minutes, so the shares need not "
                        "add up to 100. Each stage runs from its logged start to the "
                        "event that ends it. In a log written before the stages logged "
                        "their starts, the personas’ read and a plan talk with no "
                        "start are a dot where they ended, and a polish pass runs "
                        "from the event before it."
                    ),
                },
                legend,
            ),
        ),
        h(
            "div",
            {
                "class": "tt",
                "id": "tt",
                "data-controller": "tip",
                "data-action": (
                    "mousemove->tip#move mouseleave->tip#hide click->tip#move"
                ),
            },
            plot,
            h("div", {"class": "tip", "hidden": True, "data-tip-target": "box"}),
        ),
        h(
            "div",
            {"class": "tl-note"},
            (
                "Each row is who held the work; a band is a stage. Hover a mark for "
                "its times, and the legend for how the shares add up."
            ),
        ),
    )


def feed_card(ctx: P.Ctx, t: bm.Task) -> Markup:
    """The task's events, the newest first. The newest block's words are the large
    card's, so its row names only the status."""
    m = ctx.model
    current = max(
        (i for i, e in enumerate(t.events) if e.get("event") == "task.state"),
        default=-1,
    )
    rows_ = []
    for i, e in bm.feed(t.events):
        d: dict[str, Any] = bm.describe(e, m)
        if i == current:
            d = {**d, "text": "", "sub": ""}
        rows_.append(
            row(
                ctx,
                f"tev-{i}",
                d["info"]["actor"],
                d["info"]["icon"],
                [
                    h("b", None, d["head"]),
                    d.get("text") and " · ",
                    h(
                        "span",
                        {"class": "cmd" if d.get("mono") else None},
                        d.get("text") or "",
                    ),
                    d.get("sub") and sub(d["sub"]),
                ],
                bm.stamp(
                    cast("int", bm.at(e.get("ts"))), m.now
                ),  # the feed's events have a time
            )
        )
    return card(
        "feed-card",
        "Activity",
        bm.plural(len(t.events), "event")
        + (f" · the newest {P.FEED_NEWEST}" if len(t.events) > P.FEED_NEWEST else ""),
        rows_ or [h("div", {"class": "empty"}, "No events yet")],
        "feed",
    )


def timeline_tab(ctx: P.Ctx, t: bm.Task) -> list:
    if t.summary is not None:
        return went_tab(ctx, t, "timeline")
    return [time_card(ctx, t), feed_card(ctx, t)]


# ---- Artifacts ----


def json_marks(text: str) -> Markup:
    """JSON with its keys, strings, numbers and literals marked; every part
    is escaped."""
    out, at = [], 0
    for found in JSON_TOKEN.finditer(text):
        out.append(text[at : found.start()])
        if found[1]:
            out.append(h("span", {"class": "j-key" if found[2] else "j-str"}, found[1]))
            if found[2]:
                out.append(found[2])
        elif found[3]:
            out.append(h("span", {"class": "j-lit"}, found[0]))
        else:
            out.append(h("span", {"class": "j-num"}, found[0]))
        at = found.end()
    out.append(text[at:])
    return join(out)


def art_body(ctx: P.Ctx, f: dict, t: bm.Task) -> Markup:  # noqa: C901, PLR0911 - over the limit before the limit was set
    """The opened file, by its kind; a record with one line on top that links to the tab
    that shows it readable."""
    if f["kind"] == "html" and f.get("href"):
        return h(
            "iframe",
            {
                "src": ctx.raw_href(t.slug, f["path"]),
                "sandbox": "allow-scripts allow-popups allow-popups-to-escape-sandbox",
                "title": f.get("title") or f["path"],
                "loading": "lazy",
                "referrerpolicy": "no-referrer",
            },
        )
    if f["kind"] == "image" and f["path"].startswith("media/"):
        src = ctx.media_href(t.slug) + "/".join(
            quote(part, safe="") for part in f["path"].removeprefix("media/").split("/")
        )
        return h(
            "figure",
            {"class": "av-pic"},
            h(
                "a",
                {
                    "class": "pic",
                    "href": src,
                    "target": "_blank",
                    "rel": "noopener",
                    "title": "Open the picture at its full size",
                },
                h("img", {"src": src, "alt": f.get("title") or f["path"]}),
            ),
        )
    plan = f.get("group") == "plan" and f.get("title") == "The plan"
    where = [
        h("br"),
        "It is at ",
        h("span", {"class": "cmd"}, f["path"]),
        " in the task’s worktree." if plan else " in the task’s folder.",
    ]
    if f.get("cut") or (f.get("text") is None and f["kind"] not in ("binary", "image")):
        return h(
            "div",
            {"class": "av-none"},
            f"This file is {size_of(f.get('bytes'))}, over the size the board shows."
            if f.get("cut")
            else "The board has no text of this file.",
            where,
        )
    if f["kind"] in ("binary", "image"):
        return h(
            "div",
            {"class": "av-none"},
            "A binary file: the board does not show it.",
            where,
        )
    text = str(f["text"])
    readable = f.get("role") == "record" and f.get("tab") in lem_artifacts.TAB_NAMES
    top = readable and h(
        "div",
        {"class": "av-rec"},
        "Shown readable on: ",
        h(
            "a",
            {**P.frame_link(ctx, P.task_href(ctx, t.slug, f["tab"]))},
            lem_artifacts.TAB_NAMES[f["tab"]],
        ),
    )
    if f["kind"] in ("log", "text"):
        text = ANSI.sub("", text)
    if f["kind"] == "markdown":
        return P.md_block(
            ctx,
            f"art-{hashlib.sha256(f['path'].encode()).hexdigest()[:8]}",
            text,
            slug=t.slug,
            folder=f["path"].rpartition("/")[0] if not plan else "",
        )
    if f["kind"] == "json":
        try:
            pretty = json.dumps(json.loads(text), indent=2, ensure_ascii=False)
        except ValueError:
            return h(
                "div",
                None,
                top,
                h(
                    "div",
                    {"class": "av-none left"},
                    "This file is not valid JSON; it is shown as written.",
                ),
                h("pre", {"class": "code"}, text),
            )
        return h("div", None, top, h("pre", {"class": "code"}, json_marks(pretty)))
    if f["kind"] == "jsonl":
        lines = [line for line in text.split("\n") if line.strip()]
        out = []
        for i, line in enumerate(lines, 1):
            try:
                one = json.dumps(json.loads(line), ensure_ascii=False)
                said = json_marks(one)
            except ValueError:
                said = line
            out.append(
                h(
                    "div",
                    {"class": "jl-row"},
                    h("span", {"class": "n"}, i),
                    h("span", None, said),
                )
            )
        return h("div", None, top, h("div", {"class": "jl"}, out))
    if f["kind"] == "log":
        lines = text.rstrip("\n").split("\n")
        return h(
            "pre",
            {"class": "code log"},
            [
                h(
                    "div",
                    {"class": "ln"},
                    h("span", {"class": "n"}, i),
                    h("span", None, line or " "),
                )
                for i, line in enumerate(lines, 1)
            ],
        )
    return h("pre", {"class": "code"}, text)


def empty_reason(t: bm.Task, key: str) -> str:  # noqa: PLR0911 - over the limit before the limit was set
    """The gray line of a section of the map that holds no document, by the task's path
    and where it stands: what is on a tab of the board instead, not yet, or none."""
    small = bm.track_of(t) == "fast track" or t.lead == "small"
    ended = (
        "none: it ended with a report"
        if t.status == "answered"
        else "none: the task was dropped"
        if t.status == "dropped"
        else "none"
    )
    if key == "request":
        return "none: the request was typed in a session"
    if t.summary is not None and key in ("criteria", "checks", "review", "proposal"):
        # what showed them went with the events, into the summary
        return (
            "no document: green or not green is on the Overview"
            if key == "proposal" and t.proposal
            else "no document: what showed it went with the events, into one summary"
        )
    if key == "criteria":
        return (
            "no document: Criteria and decisions shows them"
            if t.approvals or t.criteria
            else ended
            if t.closed
            else "not yet: the interview writes them"
        )
    if key == "plan":
        return (
            "no plan: the fast track"
            if small
            else ended
            if t.closed
            else "not yet: the lead writes it"
        )
    if key == "build":
        return (
            ended
            if t.closed or t.status in ("ready", "landing", "open")
            else "not yet: the build runs"
        )
    if key == "checks":
        return (
            "no output kept: Checks and review shows the results"
            if t.gates
            else ended
            if t.closed
            else "not yet: the checks run when the branch’s turn to land comes"
        )
    if key == "review":
        return (
            "no document: Checks and review shows each round"
            if t.reviews
            else ended
            if t.closed
            else "not yet: the review comes after the checks"
        )
    return (
        "no document: the proposal is on Checks and review"
        if t.proposal
        else ended
        if t.closed
        else "not yet: the proposal writes it"
    )


def art_tree(ctx: P.Ctx, t: bm.Task, chosen: str | None) -> list:
    """The task's map (`lem_artifacts.arrange`): the seven sections, each a `<details>`
    the owner folds with its count of documents, each document a row with its records
    and pictures as small links, an empty section with its gray line; then "Working
    files", folded, by folder."""
    amap = cast("dict", ctx.artifact_map)  # artifacts_tab sets it first

    def fid(path: str) -> str:
        return "af-" + hashlib.sha256(path.encode()).hexdigest()[:12]

    def link(f: dict, label: str, cls: str = "a-item") -> Markup:
        on = f["path"] == chosen
        return h(
            "a",
            {
                "class": f"{cls}{' sel' if on else ''}",
                "id": fid(f["path"]),
                "title": f["path"],
                **P.frame_link(ctx, P.task_href(ctx, t.slug, "artifacts", f["path"])),
                "aria-current": "page" if on else None,
            },
            cls == "a-item" and P.icon(ctx, KIND_ICON.get(f["kind"], "file")),
            h("span", None, label),
        )

    def doc_row(f: dict) -> Markup:
        extra = [link(x, x.get("label") or "record", "a-rec") for x in f["attached"]]
        return h(
            "div",
            {"class": "a-row"},
            link(f, f.get("title") or f["path"]),
            extra and h("span", {"class": "a-recs"}, extra),
        )

    out = []
    for sec in amap["sections"]:
        docs = sec["docs"]
        body = (
            [doc_row(f) for f in docs]
            if docs
            else [h("div", {"class": "a-empty"}, empty_reason(t, sec["key"]))]
        )
        out.append(
            h(
                "details",
                {
                    "class": f"a-grp{'' if docs else ' none'}",
                    "id": f"ag-{sec['key']}",
                    "open": True,
                },
                h(
                    "summary",
                    None,
                    P.icon(ctx, "chevron-right", "ic chev"),
                    h(
                        "span",
                        {"class": "a-group"},
                        sec["name"],
                        h("em", None, len(docs) or None),
                    ),
                ),
                h("div", {"class": "a-list"}, body),
            )
        )
    if amap["work"]:
        inside = any(f["path"] == chosen for w in amap["work"] for f in w["files"])
        drawn = []
        for w in amap["work"]:
            leaves = [link(f, f.get("title") or f["path"]) for f in w["files"]]
            if w["folder"] is None:
                drawn += leaves
                continue
            drawn.append(
                h(
                    "details",
                    {
                        "class": "a-sub",
                        "id": "as-"
                        + hashlib.sha256(w["folder"].encode()).hexdigest()[:10],
                        "open": any(f["path"] == chosen for f in w["files"]),
                    },
                    h(
                        "summary",
                        None,
                        P.icon(ctx, "chevron-right", "ic chev"),
                        P.icon(ctx, "folder"),
                        h("span", None, w["folder"]),
                        h("em", {"class": "a-n"}, len(w["files"])),
                    ),
                    h("div", {"class": "a-list"}, leaves),
                )
            )
        out.append(
            h(
                "details",
                {"class": "a-grp a-work", "id": "ag-work", "open": inside},
                h(
                    "summary",
                    {
                        "title": (
                            "An agent’s scratch, the review tool’s archive of each "
                            "round, records with no document, "
                            "and files the map does not know"
                        )
                    },
                    P.icon(ctx, "chevron-right", "ic chev"),
                    h(
                        "span",
                        {"class": "a-group"},
                        "Working files",
                        h("em", None, amap["work_count"]),
                    ),
                ),
                h("div", {"class": "a-list"}, drawn),
            )
        )
    return out


def artifacts_tab(ctx: P.Ctx, t: bm.Task) -> Markup:
    """The task's map at the left, and the file opened at the right; on a phone, the
    list, then the file with a way back to the list. An HTML page takes the whole width,
    with the way back to the list."""
    now = ctx.model.now
    files = ctx.artifact_files
    amap = ctx.artifact_map or lem_artifacts.arrange(files)
    ctx.artifact_map = amap
    chosen = ctx.file
    if chosen and not any(f["path"] == chosen for f in files):
        raise NotFound(f"The task {t.title} has no file {chosen!r}.")
    first = next(
        (
            d["path"]
            for sec in amap["sections"]
            for d in sec["docs"]
            if d["kind"] == "markdown"
        ),
        None,
    )
    shown = (
        chosen
        or first
        or next((d["path"] for sec in amap["sections"] for d in sec["docs"]), None)
        or (files[0]["path"] if files else None)
    )
    side = [
        h(
            "nav",
            {"class": "a-tree", "id": "a-tree", "aria-label": "The files of the task"},
            art_tree(ctx, t, shown),
        )
    ]
    side.append(
        h(
            "div",
            {"class": "arts-note", "id": "arts-note"},
            ctx.artifacts_problem
            and h("span", {"class": "error"}, ctx.artifacts_problem),
            not files and not ctx.artifacts_problem and "The task has no file yet.",
            files
            and f"{bm.plural(amap['count'], 'document')}, read {bm.stamp(now, now)}",
        )
    )
    f = ctx.artifact(t.slug, shown) if shown else None
    wide = bool(f and f["kind"] == "html" and f.get("href"))
    if f is None:
        view = [
            h(
                "div",
                {"class": "av-none"},
                "Pick a file at the left." if files else "Nothing to show.",
            )
        ]
    else:
        changed = bm.at(f.get("mtime"))
        meta = " · ".join(
            x
            for x in (
                f["path"],
                KIND_WORD.get(f["kind"], f["kind"]),
                size_of(f.get("bytes")),
                changed and f"changed {bm.stamp(changed, now)}",
            )
            if x
        )
        alone = wide and h(
            "a",
            {
                "class": "btn av-alone",
                "href": ctx.raw_href(t.slug, f["path"]),
                "target": "_blank",
                "rel": "noopener",
                "title": (
                    "Open the page alone in a tab of its own, "
                    "at the whole width of the window"
                ),
            },
            "Open alone ",
            P.icon(ctx, "arrow-up-right-from-square"),
        )
        view = [
            h(
                "div",
                {"class": "av-head", "id": "av-head"},
                h(
                    "a",
                    {
                        "class": "btn av-back",
                        **P.frame_link(ctx, P.task_href(ctx, t.slug, "artifacts")),
                    },
                    P.icon(ctx, "arrow-left"),
                    "The files",
                ),
                h(
                    "div",
                    {"class": "av-title"},
                    P.icon(ctx, KIND_ICON.get(f["kind"], "file")),
                    h("span", None, f.get("title") or f["path"]),
                    alone,
                ),
                h(
                    "div",
                    {"class": "av-meta"},
                    h("span", None, meta),
                    copy_control(ctx, f["path"], "the file's path"),
                ),
            ),
            h(
                "div",
                {"class": f"av-body{' frame' if wide else ''}", "id": "av-body"},
                art_body(ctx, f, t),
            ),
        ]
    return h(
        "div",
        {
            "class": (
                f"arts{' show-file' if chosen else ''}"
                f"{' wide' if wide and chosen else ''}"
            ),
            "id": "arts",
            "data-controller": "artifacts",
            "data-artifacts-task-value": t.slug,
        },
        h(
            "div",
            {"class": "arts-side", "id": "arts-side", "data-artifacts-target": "side"},
            side,
        ),
        h("div", {"class": "arts-view", "id": "arts-view"}, view),
    )


# ---- the panel and the pages ----

# ---- the steps of the board's acts ----


def note_card(ctx: P.Ctx, slug: str) -> Markup | None:
    """The result of the act the address names (`?note=`) on the task SLUG, first in the
    tab: running, done with what happens next, not done with the script's own line, or
    the owner's merge that stands while it stands (`P.act_note`)."""
    note = ctx.note
    if not note or note.get("task") != slug:
        return None
    return P.act_note(ctx, note)


def act_back(ctx: P.Ctx, t: bm.Task, label: str, cls: str = "") -> Markup:
    return h(
        "a",
        {"class": f"btn {cls}".strip(), **P.frame_link(ctx, P.task_href(ctx, t.slug))},
        h("span", None, label),
    )


def not_now(
    ctx: P.Ctx,
    t: bm.Task,
    said: str,
    *,
    card_id: str = "confirm",
    keep: str | None = None,
) -> list:
    return [
        h(
            "section",
            {"class": "card confirm a-quiet", "id": card_id, "data-keep": keep},
            h("p", None, said),
            h("div", {"class": "act-row"}, act_back(ctx, t, "Back to the task")),
        )
    ]


def merge_step(ctx: P.Ctx, t: bm.Task) -> list:
    """The confirm step of a merge: green or not green first, careful when it is, then
    the pull request, the commit it merges, the base branch and how it lands, and one
    button. The form carries the commit it shows, so that a branch proposed again since
    is not merged on this look."""
    if t.slug in ctx.merging:
        return not_now(
            ctx, t, "Lem merges it now. This page shows the result when it ends."
        )
    stands = bm.stands_said(t, seen=ctx.model.seen)
    if stands:
        return not_now(ctx, t, stands)
    if "merge" not in bm.acts_of(t, ctx.model.seen):
        return not_now(
            ctx,
            t,
            f"Nothing to merge now: the task is {t.info['label'].lower()}."
            if t.status != "open"
            else (
                "Lem lands it again: the base moved after the checks ran, so a merge "
                "now is refused the same way. The task’s session lands it again, and "
                "its new proposal is open for a merge."
            )
            if t.merge_wait == "relands"
            else (
                "The forge calls its pull request conflicting with the base: "
                "Lem brings it onto the base first, and then it waits for you again."
            ),
        )
    says = bm.merge_says(t)
    landing = ctx.landing_of(t.slug) or {}
    tip = str(landing.get("proposed") or "")
    pr = landing.get("pr") if isinstance(landing.get("pr"), dict) else {}
    found = bm.pr_of(t)
    base = landing.get("base") or ctx.model.meta.get("base") or "the base branch"
    subject = (
        (t.commit or {}).get("subject")
        if t.commit
        and tip
        and (
            tip.startswith(str(t.commit.get("head") or "-"))
            or str(t.commit.get("head") or "").startswith(tip)
        )
        else None
    )
    green = says["green"]
    first = h(
        "div",
        {"class": f"cf-first a-{'done' if green else 'you'}"},
        h("span", {"class": "fi"}, P.icon(ctx, "check" if green else "alert")),
        h(
            "div",
            None,
            h("b", {"class": "cf-word"}, "Green" if green else "Not green"),
            says["careful"]
            and h(
                "span",
                {"class": "tag c-bad cf-careful", "title": says["careful_why"] or None},
                P.icon(ctx, "careful"),
                h("span", None, "careful"),
            ),
            h(
                "div",
                {"class": "sub"},
                f"{bm.GREEN}."
                if green
                else "The pull request says why, and so do the rows below.",
            ),
        ),
    )
    reasons = None if green else P.reason_list(ctx, t, says["reasons"], "cf")
    careful = says["careful"] and h(
        "p",
        {"class": "cf-careful-why"},
        h("b", None, "Careful: "),
        P.rich(ctx, says["careful_why"] or "the review called it careful"),
        " A careful change is merged by a person.",
    )
    facts_ = []

    def fact(key: str, label: str, *kids: object) -> None:
        facts_.extend(
            [
                h("dt", {"id": f"cf-dt-{key}"}, label),
                h("dd", {"id": f"cf-dd-{key}"}, *kids),
            ]
        )

    if pr.get("number") and found:
        fact(
            "pr",
            "Pull request",
            h(
                "a",
                {"href": found["url"], "target": "_blank", "rel": "noopener"},
                f"{found['repo']}#{found['n']}",
            ),
        )
    else:
        fact(
            "pr",
            "Pull request",
            h("span", {"class": "sub"}, "none: the branch lands on the base itself"),
        )
    fact(
        "commit",
        "Commit",
        h("span", {"class": "mono"}, tip[:12] or "none on record"),
        subject and h("span", {"class": "sub"}, " ", subject),
    )
    if t.branch:
        fact("branch", "Branch", h("span", {"class": "mono"}, t.branch))
    fact("into", "Into", h("span", {"class": "mono"}, base))
    if landing.get("history") == "squash":
        fact(
            "as",
            "Lands as",
            "one commit: ",
            h(
                "span",
                {"class": "mono"},
                landing.get("title") or "the proposal's title",
            ),
        )
    elif landing.get("history"):
        fact("as", "Lands as", "the branch’s own commits")
    label = (
        f"Merge pull request #{pr['number']}"
        if pr.get("number")
        else f"Merge it into {base}"
    )
    body = [
        first,
        reasons,
        careful,
        h("dl", {"class": "facts cf-facts", "id": "cf-facts"}, facts_),
        h(
            "p",
            {"class": "cf-note"},
            (
                "A merge cannot be undone from the board. Lem’s merge call reads the "
                "base branch first, and it can take a minute."
            ),
        ),
    ]
    if ctx.can_act and tip:
        act = P.act_form(
            ctx,
            t.slug,
            "merge",
            label,
            "pull",
            "risk",
            "Merging…",
            {
                "confirm": "yes",
                "tip": tip,
                "in": ctx.view if ctx.view != "tasks" else None,
            },
        )
        acts = h("div", {"class": "act-row"}, act, act_back(ctx, t, "Back"))
    else:
        acts = h(
            "p",
            {"class": "sub"},
            (
                "Merge it on this board on the Mac or through the tailnet door, or "
                f"type /lem land {t.slug} in the task’s session."
            ),
        )
    return [
        confirm_card(
            f"card confirm a-{'done' if green else 'you'}",
            "Merge: confirm",
            h(
                "div",
                {"class": "eyebrow"},
                f"Merge #{pr['number']} · confirm"
                if pr.get("number")
                else "Merge · confirm",
            ),
            body,
            acts,
            sheet=ctx.can_act and bool(tip),
        )
    ]


def confirm_card(  # noqa: PLR0913 - over the limit before the limit was set
    cls: str,
    label: str,
    head_: Markup,
    body: list,
    foot: Markup,
    *,
    sheet: bool,
    card_id: str = "confirm",
    wrap: str | None = None,
    keep: str | None = None,
) -> Markup:
    """The card of an act's step in its three parts: the head, the body with what the
    owner reads, and the foot with the button and the way back, the last two in a box of
    class WRAP where the card has one (the approval's). Outside the overlay the three
    parts take no box of their own (board.css), so the card shows as one column. A card
    that has its button (SHEET) gets the `sheet` controller and the key of its read, the
    digest of the body as rendered here: on a phone's screen the card is then an overlay
    whose button comes on when the body was scrolled to its end, and any change of what
    the body says is another key, which the owner reads again from its top. A card with
    KEEP stays as it is through a refresh that renders the same key
    (`data-keep`, app.js)."""
    text = h(
        "div",
        {"class": "cf-body", "data-sheet-target": "body" if sheet else None},
        body,
    )
    rest = [text, h("div", {"class": "cf-foot"}, foot)]
    return h(
        "section",
        {
            "class": f"{cls}{' cf-sheet' if sheet else ''}",
            "id": card_id,
            "aria-label": label,
            "data-keep": keep,
            **(
                {
                    "data-controller": "sheet",
                    "data-sheet-key-value": hashlib.sha256(text.encode()).hexdigest()[
                        :12
                    ],
                }
                if sheet
                else {}
            ),
        },
        h(
            "div",
            {
                "class": "cf-head",
                **({"data-sheet-target": "head", "tabindex": "-1"} if sheet else {}),
            },
            head_,
        ),
        h("div", {"class": wrap}, rest) if wrap else rest,
    )


def park_step(ctx: P.Ctx, t: bm.Task) -> list:
    """The park of a task whose breaker waits for the owner: what stopped it, what a
    park keeps, a field for his one line of why, and one button."""
    b = t.breaker
    if b is None or "park" not in bm.acts_of(t, ctx.model.seen):
        return not_now(
            ctx,
            t,
            (
                "Nothing to park: no breaker of this task waits for you. "
                f"The task is {t.info['label'].lower()}."
            ),
        )
    asks = bm.answer_row(t)
    key = asks["key"] if asks and asks["kind"] == "breaker" else None
    made = bm.answered_of(t, ctx.model) if key else None
    if made is not None:
        return not_now(
            ctx, t, f"{lem_answers.took_effect(made)}: the task’s session takes it."
        )
    if key and ctx.query.get("key") and ctx.query["key"] != key:
        return not_now(
            ctx,
            t,
            (
                f"The Park you opened was for a wait of {t.slug} that is over: "
                "its breaker waits again. Read it, then answer it on its Overview."
            ),
        )
    # permanent, as the new task's field is: a refresh keeps the line he is typing; the
    # note of the breaker's form goes with Park…
    field_ = h(
        "label",
        {"class": "act-field"},
        h("span", None, "Why, in one line"),
        h(
            "input",
            {
                "id": f"park-why-{ctx.workspace}-{t.slug}",
                "type": "text",
                "name": "why",
                "data-turbo-permanent": True,
                "maxlength": "300",
                "autocomplete": "off",
                "enterkeyhint": "done",
                "placeholder": "the owner parked it",
                "value": " ".join(str(ctx.query.get("words") or "").split())[:300]
                or None,
            },
        ),
    )
    if ctx.can_act:
        act = P.act_form(
            ctx,
            t.slug,
            "park",
            "Park the task",
            "park",
            "go",
            "Parking…",
            {"in": ctx.view if ctx.view != "tasks" else None, "key": key},
            field_,
            form_cls="act-stack",
        )
        acts = h("div", {"class": "act-row"}, act, act_back(ctx, t, "Back"))
    else:
        acts = h(
            "p",
            {"class": "sub"},
            (
                "Park it on this board on the Mac or through the tailnet door, or type "
                f"/lem park {t.slug} in any session."
            ),
        )
    body = [
        h(
            "p",
            None,
            h("b", None, "The build stopped: "),
            P.rich(ctx, b.what or ""),
            f", since {bm.stop_words(b)}.",
        ),
        h(
            "p",
            {"class": "sub"},
            (
                "A parked task keeps its worktree, its branch and its files. "
                "Nothing of it waits for you, and nobody works on it, until /lem "
                f"resume {t.slug} in any session brings it back."
            ),
        ),
    ]
    return [
        confirm_card(
            "card confirm a-you",
            "Park: confirm",
            h("div", {"class": "eyebrow"}, f"Park · breaker {b.id}"),
            body,
            acts,
            sheet=ctx.can_act,
        )
    ]


def drop_step(ctx: P.Ctx, t: bm.Task) -> list:
    """The confirm step of a drop from the board, which asks first as a park does: "Drop
    SLUG?", what waits, what a drop ends, the owner's note (what he typed in the row's
    form, which Drop… brings), and Confirm, which posts his Drop to the answer route
    with the row's key (serve.py `act_answer`). The server records it and wakes the
    task's session, which drops the task as on /lem drop."""
    asks = bm.answer_row(t)
    if asks is None or "drop" not in asks["options"]:
        return not_now(
            ctx,
            t,
            (
                "Nothing to drop from the board: no plan or breaker of this task waits "
                f"for you. The task is {t.info['label'].lower()}; /lem drop {t.slug} "
                "in any session ends it."
            ),
        )
    made = bm.answered_of(t, ctx.model)
    if made is not None:
        return not_now(
            ctx, t, f"{lem_answers.took_effect(made)}: the task’s session takes it."
        )
    if ctx.query.get("key") and ctx.query["key"] != asks["key"]:
        return not_now(
            ctx,
            t,
            (
                f"The Drop you opened was for a wait of {t.slug} that is over. "
                "Read what waits now, then answer it on its Overview."
            ),
        )
    what = (
        h(
            "p",
            None,
            h("b", None, "The build stopped: "),
            P.rich(ctx, t.breaker.what or ""),
            f", since {bm.stop_words(t.breaker)}.",
        )
        # a breaker's row is there only while its breaker is (`answer_row`)
        if asks["kind"] == "breaker" and t.breaker is not None
        else h(
            "p",
            None,
            h("b", None, "The plan waits for your read: "),
            "a drop ends the task before its build.",
        )
    )
    field_ = h(
        "label",
        {"class": "act-field"},
        h("span", None, "Your note, if you like"),
        h(
            "textarea",
            {
                "id": f"drop-words-{ctx.workspace}-{t.slug}",
                "name": "words",
                "rows": "2",
                "data-turbo-permanent": True,
                "maxlength": str(P.NOTE_CHARS),
                "autocomplete": "off",
                "placeholder": "why, in your words",
            },
            str(ctx.query.get("words") or "")[: P.NOTE_CHARS],
        ),
    )
    if ctx.can_act:
        act = P.act_form(
            ctx,
            t.slug,
            "answer",
            "Confirm",
            "x",
            "risk",
            "Dropping…",
            {
                "key": asks["key"],
                "option": "drop",
                "confirm": "yes",
                "in": ctx.view if ctx.view != "tasks" else None,
            },
            field_,
            form_cls="act-stack",
        )
        acts = h("div", {"class": "act-row"}, act, act_back(ctx, t, "Back"))
    else:
        acts = h(
            "p",
            {"class": "sub"},
            (
                "Drop it on this board on the Mac or through the tailnet door, or type "
                f"/lem drop {t.slug} in any session."
            ),
        )
    body = [
        what,
        h(
            "p",
            {"class": "sub"},
            (
                "A drop ends the task: its session gives a ticket what it is still "
                "owed, then removes the worktree, and the branch keeps its commits. "
                "The board records your Drop and wakes the task’s session, which drops "
                f"it as /lem drop {t.slug} does."
            ),
        ),
    ]
    return [
        confirm_card(
            "card confirm a-you",
            "Drop: confirm",
            h("div", {"class": "eyebrow"}, f"Drop {t.slug}?"),
            body,
            acts,
            sheet=ctx.can_act,
        )
    ]


def card_step(ctx: P.Ctx, t: bm.Task, page_id: str) -> list:
    """The step of a card of the task's session: the card's own page as `lem-ask` built
    it, in a frame of the board (serve.py's `card_page`), which posts its answer itself
    and shows what the board said; on a phone's screen an overlay of the whole screen
    (`sheet`), as a park's step is. A card that no longer waits says what took effect,
    and a page that may not act says where to answer.

    The step and what it says once the card ended share their id and, for an answer from
    the board, their `data-keep`: the board logs the answer before its reply reaches the
    frame, so the refresh that the log brings would otherwise take the frame away, with
    what the board said there, before or just after the frame showed it. A step that the
    board's answer ended stays as the owner saw it until he leaves it; one that the
    session ended turns into what took effect."""
    keep = f"card-{page_id}"
    c = next((c for c in bm.open_cards(t, ctx.model) if c["page"] == page_id), None)
    if c is None:
        end = ctx.card_end(t.slug, page_id)
        said = (
            f"{bm.cap(lem_cards.took_effect(end))}. This card no longer waits for you."
            if end
            else (
                "This card no longer waits for you: the session that put it up no "
                "longer runs, or it holds no such card."
            )
        )
        return not_now(
            ctx,
            t,
            said,
            card_id="card-step",
            keep=keep if end and end.get("from") == "board" else None,
        )
    if not ctx.can_act:
        return not_now(
            ctx,
            t,
            (
                "Answer this card on the board on the Mac the task runs on or through "
                "its tailnet door, or in the task’s session there."
            ),
        )
    src = f"{ctx.base}/tasks/{quote(t.slug, safe='')}/cards/{quote(page_id, safe='')}/"
    frame = h(
        "iframe",
        {
            "class": "card-frame",
            "id": f"card-frame-{page_id}",
            "src": src,
            "title": c["prompt"] or "The card of the task’s session",
        },
    )
    foot = h(
        "div",
        {"class": "act-row"},
        act_back(ctx, t, "Back"),
        h(
            "span",
            {"class": "sub"},
            "A question back goes to the task’s session, at the Mac.",
        ),
    )
    return [
        confirm_card(
            "card confirm a-you card-step",
            "A card of the task’s session",
            h("div", {"class": "eyebrow"}, "Card · the task’s session asks"),
            [frame],
            foot,
            sheet=True,
            card_id="card-step",
            keep=keep,
        )
    ]


def panel(ctx: P.Ctx) -> Markup:
    """The panel of the task the address names, with the tab it names; NotFound for a
    task the log does not hold, a tab that is none, or an artifact the task does
    not have."""
    m = ctx.model
    slug = ctx.task
    ctx.scope = "task"
    try:
        t = next((x for x in m.tasks if x.slug == slug), None)
        asked = ctx.tab.removeprefix("card/") if ctx.tab.startswith("card/") else None
        if ctx.tab not in TAB and ctx.tab not in ACT_TABS and not asked:
            raise NotFound(
                f"A task has no tab {ctx.tab!r}: its tabs are {', '.join(TAB)}."
            )
        if t is None:
            early = m.by_slug.get(slug)
            if early is None:
                raise NotFound(f"No task “{slug}” is on record in this repository.")
            n = len(early.events)
            said = (
                f"No state was written yet for the task “{slug}”: "
                f"its {bm.plural(n, 'event')} {'is' if n == 1 else 'are'} on record, "
                "and the rest comes with its first state."
            )
            known = cast("str", slug)  # the log holds a task under it
            inner = [
                head(ctx, None, bm.title_of(known), said),
                h("div", {"class": "tabbody", "id": "tb-early"}, note_card(ctx, known)),
            ]
        else:
            if ctx.tab == "artifacts":
                body = artifacts_tab(ctx, t)
                tab_body = h(
                    "div", {"class": "tabbody arts-panel", "id": "tb-artifacts"}, body
                )
            else:
                parts = (
                    card_step(ctx, t, asked)
                    if asked
                    else {
                        "overview": overview_tab,
                        "criteria": criteria_tab,
                        "checks": checks_tab,
                        "timeline": timeline_tab,
                        "merge": merge_step,
                        "park": park_step,
                        "drop": drop_step,
                    }[ctx.tab](ctx, t)
                )
                # the criteria tab places the act's note itself: in the approval card
                # while that holds the button
                tab_body = h(
                    "div",
                    {"class": "tabbody", "id": f"tb-{ctx.tab.replace('/', '-')}"},
                    None if ctx.tab == "criteria" else note_card(ctx, t.slug),
                    parts,
                )
            inner = [head(ctx, t, t.title), tab_nav(ctx, t), tab_body]
        # an HTML page opened among the artifacts takes the panel's height: the header
        # folds as on a phone
        page_open = (
            t is not None
            and ctx.tab == "artifacts"
            and ctx.file is not None
            and any(
                f["path"] == ctx.file and f["kind"] == "html" and f.get("href")
                for f in ctx.artifact_files
            )
        )
        return h(
            "section",
            {
                "class": f"panel{' page-open' if page_open else ''}",
                "id": "panel",
                "data-task": slug,
                "aria-label": "The task",
                "data-controller": "panel",
            },
            h(
                "div",
                {
                    "class": "p-grip",
                    "role": "separator",
                    "aria-orientation": "vertical",
                    "aria-label": "The panel's width",
                    "data-controller": "splitter",
                    "data-action": (
                        "pointerdown->splitter#start dblclick->splitter#reset"
                    ),
                    "title": (
                        "Drag to make the panel wider or narrower · "
                        "double-click for its usual width"
                    ),
                },
            ),
            inner,
            P.sprite(ctx, "task"),
        )
    finally:
        ctx.scope = "page"


def missing_panel(ctx: P.Ctx, said: str) -> Markup:
    """The panel of an address that names nothing: what it names, and the way back."""
    ctx.scope = "task"
    try:
        return h(
            "section",
            {
                "class": "panel",
                "id": "panel",
                "data-task": ctx.task or "",
                "aria-label": "Not found",
                "data-controller": "panel",
            },
            head(ctx, None, "Not found", said),
            P.sprite(ctx, "task"),
        )
    finally:
        ctx.scope = "page"


VIEW_PAGES = {
    "tasks": P.kanban_page,
    "waits": P.waits_page,
    "backlog": P.backlog_page,
    "activity": P.activity_page,
    "done": P.older_page,
}


def task_page(ctx: P.Ctx) -> tuple[int, Markup]:
    """The view under the panel with the task's panel open, and the status of the
    answer: 404 when the address names no task, tab or artifact, in the board's layout
    with the panel that says so."""
    status = 200
    try:
        ctx.panel = panel(ctx)
    except NotFound as missing:
        status, ctx.panel = 404, missing_panel(ctx, str(missing))
    if ctx.native:
        # the Hotwire Native app shows a task as a page of its own: the panel across
        # the stage
        return status, P.layout(
            ctx, "Tasks", "", h("div", {"class": "view"}), stage_cls="native"
        )
    return status, VIEW_PAGES[ctx.view](ctx)


def frame_page(ctx: P.Ctx) -> tuple[int, Markup]:
    """The panel alone, in its frame, for a request of the frame (`Turbo-Frame: task`),
    with the head of every page so that Turbo finds the same assets; an address of a
    view gives an empty frame."""
    status = 200
    if ctx.task:
        try:
            ctx.panel = panel(ctx)
        except NotFound as missing:
            status, ctx.panel = 404, missing_panel(ctx, str(missing))
    t = ctx.model.by_slug.get(ctx.task) if ctx.task else None
    repo = ctx.model.meta.get("repo") or ctx.workspace
    title = (
        f"{t.title} · Lem · {repo}"
        if t
        else f"{P.UNDER.get(ctx.view, P.VIEW['tasks'])['label']} · Lem · {repo}"
    )
    return status, page(
        P.head(title, ctx.asset), h("body", {"class": "app"}, P.task_frame(ctx))
    )


def told_of(  # noqa: PLR0913, PLR0917 - over the limit before the limit was set
    state: Path,
    board: ModuleType,
    slug: str,
    worktree: Path | None,
    onto: str,
    backlog: str | None,
) -> dict:
    """What "What we are building" reads of a task: the outcome of its task.md, and the
    backlog items its branch filed against `onto` (board.py's `outcome` and `filed`;
    None when git cannot tell)."""
    request = state / "tasks" / slug / "task.md"
    try:
        text = (
            request.read_text(encoding="utf-8", errors="replace")
            if request.is_file()
            else ""
        )
    except OSError:
        text = ""
    filed = (
        board.filed(worktree, onto, backlog)
        if worktree is not None and backlog
        else None
    )
    return {"outcome": board.outcome(text), "filed": filed}


def artifact_files(state: Path, slug: str, plan: tuple[Path, str] | None) -> list[dict]:
    """The task's files as the explorer lists them, with no text."""
    directory = state / "tasks" / slug
    if not directory.is_dir():
        return []
    return lem_artifacts.files(directory, slug, plan, read=False)


def folder_of(state: Path, slug: str) -> dict | None:
    """What the task's folder holds beside the model: the files of its small record that
    are there, in the order of `lem_artifacts.SMALL_RECORD`, and the paths outside it
    (`lem_artifacts.outside_record`); None when the folder is not there or does not
    list, so that no page says what a folder it did not read holds."""
    directory = state / "tasks" / slug
    try:
        names = {entry.name for entry in directory.iterdir()}
    except OSError:
        return None
    return {
        "kept": [name for name in lem_artifacts.SMALL_RECORD if name in names],
        "left": lem_artifacts.outside_record(directory),
    }


def artifact_map(state: Path, slug: str, files: list[dict]) -> dict:
    """The task's files on the map of every task (`lem_artifacts.arrange`), with the
    pictures each document shows."""
    return lem_artifacts.arrange(
        files, lem_artifacts.pictures_named(state / "tasks" / slug, files)
    )
