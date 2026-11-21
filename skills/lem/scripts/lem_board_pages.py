"""The pages of the served board, as HTML: functions from the model (`lem_board_model`) to `Markup`.

    kanban_page(ctx)     /HOST/WORKSPACE/            the tasks in four columns, by who acts
    waits_page(ctx)      /HOST/WORKSPACE/waits       one row for each thing the owner does
    backlog_page(ctx)    /HOST/WORKSPACE/backlog     the backlog's items by their worth
    activity_page(ctx)   /HOST/WORKSPACE/activity    where the time went, and every event
    index_page(...)      /                           the workspaces of this machine
    error_page(...)                                  a route that failed, with its reason

Every page of a workspace is one layout (`layout`): the sidebar (the mark and the repository, the
notices, "Waits for you", the views and the switcher of the workspaces in its foot), the bar above the
view (its name, what it holds, the base branch and the counts of the pull requests), the view, and the
status bar (when the log was read, when the forge was looked at, and whether the page is live). On a
phone the sidebar is a drawer behind a bar at the top, and the kanban shows one column at a time.

The page is drawn whole by the server for its URL, and Turbo morphs it into its next version when the
stream says the workspace changed (meta `turbo-refresh-method`): each repeated part has a stable
`id`, so a morph keeps the nodes that stay, with their scroll and their focus. What is the browser's own
state comes back in the cookie the fold controller writes (`Ctx.prefs`: the folded columns and the
folded sidebar), so the first paint and every morph show it. The words are the model's. The icons are Font Awesome's, from the kit's `board-icons.json`, put into each page as
one `<svg>` of symbols, so that an icon paints at once.

A task opens in the panel at the right of the view, inside `<turbo-frame id="task">` (its pages are
`lem_board_task`'s, which put the panel into `Ctx.panel`): a link to a task carries
`data-turbo-frame="task"` and `data-turbo-action="advance"`, so the panel changes and the address
follows it, and the same address loaded whole renders the view under it with the panel open.
`task_href` is the one place that says where a task opens. The view under the panel is in the address
(`?in=waits`, `backlog`, `activity`; the kanban has none), so that a refresh, a reload or a shared link
shows the same page. For the Hotwire Native app (`Ctx.native`) every link is a whole visit.

The backlog's filter is in the address (`?q=`, `worth=`, `only=`, `backlog_filter`), so a shared link
and a refresh show the same list. The server draws every item and the chips the address picks; the
backlog controller holds the one rule of which items the filter shows, and applies it as one types.
A line of Lem's reaches a page through `rich` (its code as code, each pull request it names a link)
and a markdown text through `md_block`.

Each task lives in its own agterm session. The jump to it, which only agterm does, has its button only
on a page drawn for the main listener and a client on this Mac (`Ctx.local`): it posts to the server,
which runs `agtermctl session select` (`serve.agterm_act`). A task with no live session is a row of
"Waits for you" when it is stuck for want of one (`lem_board_model.session_need`), and the row and the
task's header have "Open a session" on every page that may act, which the server answers with `lem
session open` (`serve.act_session`).
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

from lem_html import Markup, h, page
import lem_board_model as bm

ASSETS = Path(__file__).resolve().parent.parent / "assets"
LEM_ROOT = Path(__file__).resolve().parents[3]
MARKS = (LEM_ROOT / "assets" / "lem-mark.svg", LEM_ROOT / "assets" / "lem-mark-night.svg")
ICONS = ASSETS / "vendor" / "board-icons.json"

# Each of Lem's icon names as its Font Awesome icon (tools/board-kit bundles them, icons.mjs).
FA = {"code": "code", "user": "user", "check": "check", "commit": "code-commit", "alert": "triangle-exclamation", "play": "play", "flag": "flag",
      "branch": "code-branch", "clock": "clock", "arrow": "arrow-right", "eye": "eye", "file": "file-lines", "moon": "moon", "x": "xmark", "layers": "layer-group",
      "split": "table-columns", "cpu": "microchip", "dot": "circle-small", "users": "users", "help": "circle-question", "pull": "code-pull-request",
      "careful": "shield-exclamation", "park": "folder"}
# The views of a workspace, each with its address under the workspace and its key.
VIEWS = [
    {"key": "tasks", "path": "", "label": "Tasks", "icon": "square-kanban", "kbd": "T", "code": "KeyT"},
    {"key": "waits", "path": "waits", "label": "Waits for you", "icon": "inbox", "kbd": "W", "code": "KeyW"},
    {"key": "backlog", "path": "backlog", "label": "Backlog", "icon": "list-check", "kbd": "B", "code": "KeyB"},
    {"key": "activity", "path": "activity", "label": "Activity", "icon": "list-timeline", "kbd": "A", "code": "KeyA"},
]
VIEW = {v["key"]: v for v in VIEWS}
# The backlog's groups, from each item's own `worth`.
BY_WORTH = [
    {"key": "yes", "name": "Worth doing", "actor": "gate"},
    {"key": "later", "name": "Later", "actor": "you"},
    {"key": "unset", "name": "No verdict in the item", "actor": "quiet"},
    {"key": "no", "name": "Decided against", "actor": "quiet", "recessive": True},
]
# How long the board's own look at GitHub counts as fresh: a few of its looks (serve.FORGE_SECONDS), a guess.
BOARD_LOOK_FRESH = 10 * 60 * 1000
# A path in a line the owner types into a session: anything but plain path characters is refused.
SAFE_PATH = re.compile(r"^[A-Za-z0-9._/-]+$")
# The light and the dark background of lem.css, for the browser's bar and the home-screen app.
THEME = {"light": "#fbf9f5", "dark": "#1a1813"}

_icons: dict | None = None
_marks: Markup | None = None


def icon_set() -> dict:
    global _icons
    if _icons is None:
        _icons = json.loads(ICONS.read_text(encoding="utf-8"))
    return _icons


def marks() -> Markup:
    """Lem's mark, day and night, as lem.css shows one of them by the palette: a file of the plugin's own."""
    global _marks
    if _marks is None:
        _marks = Markup("".join(file.read_text(encoding="utf-8").strip() for file in MARKS))
    return _marks


@dataclass
class Ctx:
    """What a page of one workspace is drawn from: where it is, the model and the facts beside it."""

    host: str
    workspace: str
    model: bm.Model
    asset: object  # name -> its address with the content's hash
    prefs: dict = field(default_factory=dict)
    backlog: dict | None = None
    problems: list = field(default_factory=list)
    read_at: int = 0
    events: int = 0
    spaces: list = field(default_factory=list)
    view: str = "tasks"
    used: set = field(default_factory=set)
    # the task whose panel is open, its tab and the artifact it shows, from the address
    task: str | None = None
    tab: str = "overview"
    file: str | None = None
    # the panel, which lem_board_task draws, and the icons it uses (a sprite of its own, so that a
    # panel the frame brings alone has its icons)
    panel: Markup | None = None
    scope: str = "page"
    used_task: set = field(default_factory=set)
    # a request of the Hotwire Native app: every link is a whole visit, and a task is a page of its own
    native: bool = False
    # a page for the main listener and a client on this Mac: the buttons of what only agterm does
    local: bool = False
    # what the task's tabs read beside the model, from the caller: "What we are building" of a task
    # (`told(slug)`), the task's files (`artifact_files`, with no text) and one of them with its text
    # (`artifact(slug, path)`), what did not read of them, and the address of an HTML artifact
    told: object = lambda slug: None
    artifact_files: list = field(default_factory=list)
    artifact: object = lambda slug, path: None
    artifacts_problem: str = ""
    raw_href: object = lambda slug, path: ""
    # the address of a task's media folder, from which a document shows its pictures
    media_href: object = lambda slug: ""
    # the artifacts as their map has them (`lem_artifacts.arrange`), and the plan's `## How it works`
    artifact_map: dict | None = None
    how_of: object = lambda slug: ""
    # the server's own look at the forge for the workspace: when it last looked, and what stops it
    forge_look: dict = field(default_factory=dict)
    # the backlog's filter, from the address (`backlog_filter`)
    filters: dict = field(default_factory=dict)
    # the board's acts on a task (serve.py `board_act`): whether this page may post them (on this Mac, or
    # through the tailnet door), the criteria that wait for the owner's yes in a task directory, a task's
    # landing record, the tasks whose merge runs now, and the result of an act the address names
    can_act: bool = False
    criteria_waiting: object = lambda slug: None
    landing_of: object = lambda slug: {}
    merging: set = field(default_factory=set)
    note: dict | None = None
    _forge: object = False

    @property
    def artifact_count(self) -> int:
        return self.artifact_map["count"] if self.artifact_map else len(self.artifact_files)

    @property
    def forge(self) -> str | None:
        """The address of the workspace's repository on its forge, for a bare `#N` (`lem_board_model.forge_of`)."""
        if self._forge is False:
            self._forge = bm.forge_of(self.model)
        return self._forge

    @property
    def base(self) -> str:
        return f"/{quote(self.host)}/{quote(self.workspace)}"

    def href(self, view: str) -> str:
        return f"{self.base}/{VIEW[view]['path']}"


def under_query(ctx: Ctx, under: str | None = None) -> str:
    """The view a panel lies over, as the address keeps it: `?in=VIEW`, or nothing for the kanban."""
    under = ctx.view if under is None else under
    return f"?in={quote(under)}" if under in VIEW and under != "tasks" else ""


def task_href(ctx: Ctx, slug: str, tab: str = "overview", file: str | None = None, under: str | None = None) -> str:
    """Where a task opens: `/HOST/WORKSPACE/tasks/SLUG`, a tab after it, and for an artifact its path,
    each part encoded, with a slash at its end, so that no address ends in an extension Turbo refuses to
    visit (`report.md/`); the view under the panel in the query."""
    path = f"{ctx.base}/tasks/{quote(slug, safe='')}" + ("" if tab == "overview" and not file else f"/{quote(tab, safe='')}")
    if file:
        path += "/" + "/".join(quote(part, safe="") for part in file.split("/")) + "/"
    return path + under_query(ctx, under)


def frame_link(ctx: Ctx, href: str) -> dict:
    """The attributes of a link that changes the panel: the frame and the address, or, for the native
    app, a whole visit."""
    return {"href": href} if ctx.native else {"href": href, "data-turbo-frame": "task", "data-turbo-action": "advance"}


def task_link(ctx: Ctx, slug: str, tab: str = "overview") -> dict:
    """The attributes of a link to a task, from anywhere on the page."""
    return frame_link(ctx, task_href(ctx, slug, tab))


def icon(ctx: Ctx, name: str, cls: str = "ic") -> Markup:
    fa = FA.get(name, name)
    if fa not in icon_set():
        return Markup("")
    task = ctx.scope == "task"
    (ctx.used_task if task else ctx.used).add(fa)
    return h("svg", {"class": cls, "aria-hidden": "true"}, h("use", {"href": f"#{'t-' if task else ''}i-{fa}"}))


def sprite(ctx: Ctx, scope: str = "page") -> Markup:
    """The page's icons as one `<svg>` of symbols, or the panel's own (`scope` "task", ids `t-i-NAME`)."""
    known = icon_set()
    task = scope == "task"
    used = ctx.used_task if task else ctx.used
    prefix = "t-i-" if task else "i-"
    symbols = (Markup(f'<symbol id="{prefix}{name}" viewBox="{known[name]["viewBox"]}">{known[name]["body"]}</symbol>') for name in sorted(used))
    return h("svg", {"id": "icons-task" if task else "icons", "class": "sprite", "aria-hidden": "true"}, *symbols)


# ---- text with its links, its code and its markdown ----

# A name in a line of Lem's that reads as code: a span in backticks, a path with a file's extension.
CODE_SPAN = re.compile(r"`([^`\n]+)`|(?<![\w/.-])((?:[\w.-]+/)+[\w.-]+\.[a-z]{1,5}(?::[\w.]+)?)(?![\w/])")


def linked(ctx: Ctx, text: object) -> list:
    """A text with each pull request it names as a link (`lem_board_model.pull_refs`, the one rule of the
    board); every other part stays text."""
    return [part if isinstance(part, str) else h("a", {"class": "pr-link", "href": part["url"], "target": "_blank", "rel": "noopener",
                                                        "title": f"Open the pull request on the forge: {part['url']}"}, part["text"])
            for part in bm.pull_refs(str(text if text is not None else ""), ctx.forge)]


def rich(ctx: Ctx, text: object) -> list:
    """A line of Lem's as the board shows it: its names in backticks and its paths as code, and each
    pull request it names as a link."""
    text = str(text if text is not None else "")
    out, at = [], 0
    for found in CODE_SPAN.finditer(text):
        out += [*linked(ctx, text[at:found.start()]), h("code", None, found[1] or found[2])]
        at = found.end()
    return [*out, *linked(ctx, text[at:])]


# A fenced `mermaid` block of a markdown text, which the browser draws as a chart, and the icons of the
# chart's controls (tools/board-kit/controllers/chart.js), which the page's sprite then holds.
MERMAID_FENCE = re.compile(r"^[ \t>]*(?:`{3,}|~{3,})[ \t]*mermaid\b", re.M)
CHART_ICONS = ("expand", "plus", "minus", "xmark")


def md_block(ctx: Ctx, key: str, text: str, *, slug: str | None = None, folder: str = "", cls: str = "") -> Markup:
    """A markdown text the browser renders (the markdown controller), with each pull request it names as
    a link, its pictures from the task's media folder, and its mermaid blocks as charts; kept through a
    refresh while its text is the same (`data-keep`). A text with a chart names the diagram library
    (`data-lem-mermaid`), which the browser loads at the first chart; a page with none never names it."""
    text = bm.pull_links_md(str(text), ctx.forge)
    digest = hashlib.sha256(f"{key}|{text}".encode("utf-8")).hexdigest()[:12]
    charts = bool(MERMAID_FENCE.search(text))
    if charts:
        for name in CHART_ICONS:
            icon(ctx, name)
    return h("div", {"class": f"md {cls}".strip(), "id": f"md-{key}-{digest}", "data-controller": "markdown", "data-markdown-key-value": digest, "data-keep": digest,
                     "data-markdown-media-value": ctx.media_href(slug) if slug else None, "data-markdown-dir-value": folder or None,
                     "data-lem-mermaid": ctx.asset("mermaid.min.js") if charts else None},
             h("template", None, text))


def chart_block(ctx: Ctx, key: str, source: str) -> Markup:
    """A mermaid chart of a record (a decision's, a criterion's), drawn as a document's fenced block is."""
    return md_block(ctx, key, f"```mermaid\n{source.strip()}\n```", cls="md-chart")


def since(ms: int, now: int) -> Markup:
    """A length of time that ticks in the browser (the clock controller), written right at the render."""
    return h("span", {"data-since": ms}, bm.span(now - ms))


def ago_(ms: int, now: int) -> Markup:
    return h("span", {"data-ago": ms or 0}, bm.ago(now - ms) if ms else "never")


def tag(ctx: Ctx, name: str, text: str, c: str | None = None, title: str | None = None, live: bool = False) -> Markup:
    return h("span", {"class": f"tag{f' c-{c}' if c else ''}{' live' if live else ''}", "title": title}, icon(ctx, name), h("span", None, text))


def chip(ctx: Ctx, name: str, cls: str, *kids, title: str | None = None) -> Markup:
    return h("span", {"class": f"chip {cls}".strip(), "title": title}, icon(ctx, name), *kids)


# ---- the board's acts ----

def act_href(ctx: Ctx, slug: str, act: str, under: str | None = None) -> str:
    """The address of a task's act: its confirm step for a GET, the act itself for a POST."""
    return f"{ctx.base}/tasks/{quote(slug, safe='')}/{act}" + under_query(ctx, under)


def act_form(ctx: Ctx, slug: str, act: str, label: str, name: str, cls: str, busy: str, fields: dict, *kids, form_cls: str = "") -> Markup:
    """A form that posts one act of a task: hidden fields, what it holds besides (a field of text), and
    one button. It works with no script; with Turbo the button is disabled and says BUSY while the request
    runs, and the page that follows is a whole visit (`_top`), so that its address keeps the act's note."""
    return h("form", {"class": f"act-form {form_cls}".strip(), "method": "post", "action": f"{ctx.base}/tasks/{quote(slug, safe='')}/{act}", "data-turbo-frame": "_top"},
             [h("input", {"type": "hidden", "name": key, "value": value}) for key, value in fields.items() if value is not None],
             *kids,
             h("button", {"class": f"btn {cls}".strip(), "type": "submit", "data-turbo-submits-with": busy}, icon(ctx, name), h("span", None, label)))


# How the note of an act looks, by its state: the actor's color, the icon and the first word.
NOTE_LOOK = {"running": ("gate", "clock", "Running."), "done": ("done", "check", "Done."), "refused": ("bad", "alert", "Not done.")}


def act_note(ctx: Ctx, note: dict | None) -> Markup | None:
    """The result of an act (`?note=`): running, done with what happens next, or not done with the
    script's own line; first in a task's tab, or at the top of the view the act came from."""
    if not note:
        return None
    actor, name, word = NOTE_LOOK.get(note.get("state"), NOTE_LOOK["refused"])
    return h("section", {"class": f"card verdict act-note a-{actor}", "id": "act-note", "role": "status", "aria-live": "polite"},
             h("div", {"class": "v-line"}, h("span", {"class": "fi"}, icon(ctx, name)),
               h("div", {"class": "v-text"}, h("b", {"class": "v-word"}, word), " ", rich(ctx, note.get("said") or ""))))


def new_task_link(ctx: Ctx, cls: str = "") -> Markup:
    """The "+" of a new task, which opens its form."""
    return h("a", {"class": f"btn new-task {cls}".strip(), "href": f"{ctx.base}/new", "title": "A new task, in your words · key N", "aria-label": "A new task",
                   "data-hotkey": "KeyN"}, icon(ctx, "plus"), h("span", None, "New task"))


def act_link(ctx: Ctx, slug: str, act: str, label: str, name: str, cls: str = "", under: str | None = None, frame: bool = False) -> Markup:
    """A link to the confirm step of an act: a button's look, a whole page on a phone."""
    href = act_href(ctx, slug, act, under)
    return h("a", {"class": f"btn {cls}".strip(), **(frame_link(ctx, href) if frame else {"href": href})}, icon(ctx, name), h("span", None, label))


# ---- the head and the layout ----

def head(ctx_title: str, asset) -> list:
    return [
        h("meta", {"charset": "utf-8"}),
        h("meta", {"name": "viewport", "content": "width=device-width, initial-scale=1, viewport-fit=cover"}),
        h("title", None, ctx_title),
        h("meta", {"name": "turbo-refresh-method", "content": "morph"}),
        h("meta", {"name": "turbo-refresh-scroll", "content": "preserve"}),
        h("meta", {"name": "theme-color", "content": THEME["light"], "media": "(prefers-color-scheme: light)"}),
        h("meta", {"name": "theme-color", "content": THEME["dark"], "media": "(prefers-color-scheme: dark)"}),
        h("meta", {"name": "apple-mobile-web-app-capable", "content": "yes"}),
        h("meta", {"name": "apple-mobile-web-app-title", "content": "Lem"}),
        h("meta", {"name": "apple-mobile-web-app-status-bar-style", "content": "default"}),
        h("link", {"rel": "manifest", "href": "/manifest.webmanifest"}),
        h("link", {"rel": "icon", "type": "image/png", "sizes": "64x64", "href": asset("icon-64.png"), "media": "(prefers-color-scheme: light)"}),
        h("link", {"rel": "icon", "type": "image/png", "sizes": "64x64", "href": asset("icon-64-night.png"), "media": "(prefers-color-scheme: dark)"}),
        h("link", {"rel": "apple-touch-icon", "href": asset("apple-touch-icon.png")}),
        h("link", {"rel": "stylesheet", "href": asset("lem.css"), "data-turbo-track": "reload"}),
        h("script", {"src": asset("lem.js"), "data-turbo-track": "reload"}),
        h("link", {"rel": "stylesheet", "href": asset("board.css"), "data-turbo-track": "reload"}),
        h("link", {"rel": "stylesheet", "href": asset("push.css"), "data-turbo-track": "reload"}),
        h("script", {"src": asset("board-app.js"), "defer": True, "data-turbo-track": "reload"}),
    ]


def stage_attrs(ctx: Ctx, stage_cls: str = "") -> dict:
    """The stage of the view and the panel: the view's name for the panel's look over it (beside the
    kanban, over a list), the panel across the whole stage when the owner expanded it, and the width he
    dragged it to; the cookie keeps both (`Ctx.prefs`)."""
    width = ctx.prefs.get("pw")
    return {"class": f"stage v-{ctx.view}{' full' if ctx.prefs.get('full') else ''}{' native' if ctx.native else ''} {stage_cls}".strip(), "id": "stage",
            "style": f"--pw: {width}px" if width else None}


def task_frame(ctx: Ctx) -> Markup:
    """The frame the panel of a task opens in: empty while no task is open."""
    return h("turbo-frame", {"id": "task", "data-turbo-action": None if ctx.native else "advance"}, ctx.panel)


def layout(ctx: Ctx, title: str, summary: str, view: Markup, *, stage_cls: str = "") -> Markup:
    m = ctx.model
    waits = bm.waits_of(m)
    railed = bool(ctx.prefs.get("rail"))
    trouble = ctx.problems
    meta = m.meta
    repo = meta.get("repo") or ctx.workspace
    shell = h("div", {"class": f"shell{' railed' if railed else ''}", "id": "shell",
                       "data-controller": "drawer fold hotkeys",
                       "data-action": "keydown@window->drawer#escape keydown@window->hotkeys#key"},
               sidebar(ctx, waits, repo),
               h("div", {"class": "scrim", "data-action": "click->drawer#close", "aria-hidden": "true"}),
               h("div", {"class": "main"},
                 h("header", {"class": "mbar"},
                   h("button", {"class": "ibtn", "type": "button", "data-action": "drawer#open", "title": "Menu", "aria-label": "Open the menu"}, icon(ctx, "bars")),
                   # the phone's bar says demo data too: the sidebar's notice is behind the drawer there
                   h("div", {"class": "m-title"}, h("b", None, "Lem"), h("span", None, f"{ctx.workspace} · demo data" if meta.get("demo") else ctx.workspace)),
                   new_task_link(ctx, "m-new") if ctx.can_act else None,
                   h("a", {"class": f"m-waits{' you' if waits else ''}", "href": ctx.href("waits"),
                           "aria-label": f"{bm.plural(len(waits), 'thing')} {'waits' if len(waits) == 1 else 'wait'} for you: open the list"},
                     icon(ctx, "inbox"), h("span", None, len(waits)))),
                 topbar(ctx, title, summary),
                 h("main", stage_attrs(ctx, stage_cls), view, task_frame(ctx)),
                 statusbar(ctx)))
    # the icons last, once the page named every one it uses
    body = h("body", {"class": "app", "data-controller": "clock agterm", "data-agterm-url-value": f"{ctx.base}/agterm" if ctx.local else None}, shell, sprite(ctx))
    trouble_mark = "PROBLEM · " if trouble else ""
    demo_mark = "DEMO · " if meta.get("demo") else ""
    builds = sum(1 for t in m.lane["build"] if t.status == "building")
    open_task = m.by_slug.get(ctx.task) if ctx.task else None
    doc_title = (f"{trouble_mark}{demo_mark}{open_task.title} · {open_task.info['label'] if open_task.blocks else 'no state yet'} · Lem · {repo}" if open_task
                 else f"{trouble_mark}{demo_mark}{title} · Lem · {repo} · {builds} build · {len(waits)} for you")
    return page(head(doc_title, ctx.asset), body)


def sidebar(ctx: Ctx, waits: list, repo: str) -> Markup:
    m = ctx.model
    trouble = ctx.problems
    rows = [wait_row(ctx, w) for w in waits] or [h("div", {"class": "w-none", "id": "w-none"}, icon(ctx, "circle-check"), "Nothing waits for you")]
    tasks_open = sum(1 for t in m.tasks if not t.closed)
    backlog = ctx.backlog
    counts = {"tasks": tasks_open, "waits": len(waits), "backlog": sum(1 for it in backlog["items"] if it.get("worth") != "no") if backlog else None}
    return h("aside", {"class": "side", "id": "side", "aria-label": "Lem"},
             h("div", {"class": "brand"},
               h("div", {"class": "mark"}, marks()),
               h("div", None, h("div", {"class": "b-name"}, "Lem"),
                 h("div", {"class": "b-repo", "title": f"{repo} · tasks land on {m.meta['base']}" if m.meta.get("base") else repo}, repo)),
               h("span", {"class": f"beacon{' bad' if trouble else ''}", "id": "beacon",
                          "title": "; ".join(trouble) if trouble else "lem serve reads this workspace's files and tells the page each change"}),
               h("button", {"id": "side-fold", "class": "ibtn", "type": "button", "data-action": "fold#side", "title": "Fold the sidebar", "aria-label": "Fold the sidebar"},
                 icon(ctx, "sidebar"))),
             h("div", {"class": "rail", "id": "rail", "aria-label": "Lem, folded"}, rail(ctx, waits, counts)),
             h("div", {"class": "notices", "id": "notices"}, notices(ctx)),
             h("div", {"class": "side-head"}, "Waits for you",
               h("em", {"class": "you" if waits else None, "title": f"{bm.plural(len(waits), 'thing')} you do, in {bm.plural(len({w['t'].slug for w in waits}), 'task')}"}, len(waits))),
             h("div", {"id": "waits", "class": f"wlist{' many' if len(waits) > 1 else ''}", "role": "list", "aria-label": "Waits for you", "data-controller": "edges"}, rows),
             h("div", {"class": "side-head"}, "Views"),
             h("nav", {"id": "views", "class": "views", "aria-label": "Views"},
               [h("a", {"class": "vbtn", "id": f"view-{v['key']}", "href": ctx.href(v["key"]), "aria-current": "page" if ctx.view == v["key"] else None,
                        "title": f"Key {v['kbd']}", "data-hotkey": v["code"]},
                  icon(ctx, v["icon"]), v["label"], h("em", None, counts[v["key"]]) if counts.get(v["key"]) is not None else None) for v in VIEWS]),
             push_row(ctx, "side"),
             h("div", {"class": "side-foot", "id": "side-foot"}, switcher(ctx)))


def wait_row(ctx: Ctx, w: dict) -> Markup:
    """One row of "Waits for you" in the sidebar: what, of which task, since when; its hover says where he answers."""
    t, c = w["t"], w["c"]
    say = bm.wait_say(w)
    where = say.get("where") or bm.answer_of(t)
    # the thing that waits, under the verb: a breaker's what (a merge review's row carries the review's record, which says it in `where`)
    what = f"{c.what}\n" if w["kind"] == "breaker" and c is not None else ""
    title = f"{say['verb']} · {t.title}\n{what}Where you answer: {where}"
    sel = t.slug == ctx.task
    return h("a", {"class": f"wi a-{say.get('actor', 'you')}{' sel' if sel else ''}", "id": f"w-{w['key'].replace(':', '-')}", "role": "listitem", "title": title,
                   "data-task": t.slug, "aria-current": "page" if sel else None,
                   **task_link(ctx, t.slug, say["to"])},
             h("span", {"class": "fi"}, icon(ctx, say["icon"])),
             h("span", {"class": "wi-verb"}, say["verb"]),
             h("span", {"class": "wi-time", "title": say["note"]}, since(w["since"], ctx.model.now)),
             h("span", {"class": "wi-task"}, t.title))


def notices(ctx: Ctx) -> list:
    m = ctx.model
    out = []

    def notice(key: str, actor: str, name: str, *kids) -> Markup:
        return h("div", {"class": f"notice a-{actor}", "id": f"notice-{key}"}, icon(ctx, name), h("div", None, *kids))

    if m.meta.get("demo"):
        out.append(h("div", {"class": "notice demo", "id": "notice-demo"}, icon(ctx, "alert"),
                     h("div", None, h("b", None, "Demo data. "), "These tasks are examples and not real work. Nothing on this page waits for you.")))
    if m.away:
        out.append(notice("away", "you", "moon", h("b", None, f"You are away since {bm.stamp(m.away['since'], m.now)}. "), "The tasks go on without you until you type /lem im-back."))
    for t in m.blocked:
        out.append(notice(f"blocked-{t.slug}", "bad", "alert", h("b", None, "Blocked: "), h("a", {"class": "rlink", **task_link(ctx, t.slug)}, t.title), " · ", rich(ctx, t.shown)))
    for t in m.unknown:
        out.append(notice(f"unknown-{t.slug}", "bad", "alert", f"{t.title} has the status “{t.status}”, which no stage writes: nobody acts on it."))
    return out


def rail(ctx: Ctx, waits: list, counts: dict) -> list:
    """The sidebar folded: what waits for the owner, the views, a notice as its mark, and the workspaces."""
    m = ctx.model

    def em(count, cls=None):
        return h("em", {"class": cls}, count) if count is not None else None

    out = [h("a", {"class": f"rbtn{' a-you' if waits else ''}", "href": ctx.href("waits"), "id": "rail-waits",
                   "title": f"{bm.plural(len(waits), 'thing')} {'waits' if len(waits) == 1 else 'wait'} for you" if waits else "Nothing waits for you"},
             icon(ctx, "inbox"), em(len(waits), "you" if waits else None)), h("hr")]
    for v in VIEWS:
        if v["key"] == "waits":
            continue
        out.append(h("a", {"class": "rbtn", "href": ctx.href(v["key"]), "id": f"rail-{v['key']}", "aria-current": "page" if ctx.view == v["key"] else None,
                           "title": f"{v['label']} · key {v['kbd']}"}, icon(ctx, v["icon"]), em(counts.get(v["key"]))))
    flags = []
    if m.meta.get("demo"):
        flags.append(h("button", {"class": "rbtn demo", "type": "button", "data-action": "fold#side",
                                  "title": "Demo data: these tasks are examples and not real work. Nothing on this page waits for you."}, icon(ctx, "alert")))
    if m.away:
        flags.append(h("button", {"class": "rbtn a-you", "type": "button", "data-action": "fold#side",
                                  "title": f"You are away since {bm.stamp(m.away['since'], m.now)}. The tasks go on without you until you type /lem im-back."}, icon(ctx, "moon")))
    bad = len(m.blocked) + len(m.unknown)
    if bad:
        flags.append(h("button", {"class": "rbtn a-bad", "type": "button", "data-action": "fold#side",
                                  "title": f"{bm.plural(bad, 'task')} stopped or with a status no stage writes: unfold the sidebar"}, icon(ctx, "alert"), em(bad)))
    if flags:
        out += [h("hr"), *flags]
    if len(ctx.spaces) > 1:
        others = sum(1 for s in ctx.spaces if not is_here(ctx, s) and (s.get("waits") or 0) > 0)
        out.append(h("a", {"class": "rbtn", "href": "/", "title": f"Another workspace{f': something waits for you in {others}' if others else ''}"},
                     icon(ctx, "grid-2"), em(others or None, "you")))
    return out


def runs_say(s: dict) -> str:
    """What a workspace's tasks do now, in the board's words: "nothing runs", "1 builds",
    "2 build · 1 in checks and review"."""
    building, checks = s.get("building") or 0, s.get("checks") or 0
    parts = [building and f"{building} {'builds' if building == 1 else 'build'}", checks and f"{checks} in checks and review"]
    return " · ".join(part for part in parts if part) or "nothing runs"


def space_says(s: dict, now: int | None = None) -> str:
    if s.get("reachable") is False:
        # a workspace of a machine that does not answer (lem_peers), with when it last answered
        last = f" · last answer {bm.ago((now or bm.now_ms()) - s['answered'])}" if s.get("answered") else ""
        return f"not reachable{last}"
    if s.get("waits") is None:
        return s.get("problem") or "not read"
    waits = s["waits"]
    said = f"{waits} {'waits' if waits == 1 else 'wait'} for you" if waits else "nothing waits for you"
    return f"{said} · {runs_say(s)}"


def is_here(ctx: Ctx, s: dict) -> bool:
    """Whether a row of the list of workspaces is the board this page shows."""
    return s.get("url") == f"{ctx.base}/"


def machines_of(spaces: list) -> list:
    """The machines of a list of workspaces, in its order (`lem_peers`: each row names its `host`)."""
    return list(dict.fromkeys(s["host"] for s in spaces if s.get("host")))


def space_name(s: dict, many: bool) -> str:
    """A workspace's name in a list: `HOST/WORKSPACE` when the list holds more than one machine, the
    machine's name alone for a machine that never answered."""
    if not many:
        return s["name"]
    return f"{s['host']}/{s['name']}" if s["name"] else s["host"]


def space_label(s: dict | None, workspace: str, many: bool) -> Markup:
    """A workspace's name whole, and with more than one machine its machine's name as a second, smaller line."""
    if s is None:
        return h("span", {"class": "ws-label"}, h("span", {"class": "ws-name"}, workspace))
    return h("span", {"class": "ws-label"}, h("span", {"class": "ws-name"}, s["name"] or s["host"]),
             h("span", {"class": "ws-host"}, s["host"]) if many and s["name"] else None)


def switcher(ctx: Ctx) -> Markup:
    """The workspace this board shows, its machine under it when there are more, and a menu of every
    workspace: with more than one machine in a group for each, this machine's first; in a group, those with
    a wait first and a machine that does not answer last, grayed."""
    spaces = ctx.spaces
    machines = machines_of(spaces)
    many = len(machines) > 1
    here = next((s for s in spaces if is_here(ctx, s)), None)
    title = f"{space_name(here, many)}: {space_says(here, ctx.model.now)}\n{here['path']}" if here else ctx.workspace
    if len(spaces) <= 1:
        return h("div", {"class": "ws ws-one", "id": "ws", "title": title}, icon(ctx, "grid-2"), space_label(here, ctx.workspace, many))
    waiting = sum(1 for s in spaces if not is_here(ctx, s) and (s.get("waits") or 0) > 0)

    def order(group: list) -> list:
        return sorted(group, key=lambda s: (s.get("reachable") is False, -int((s.get("waits") or 0) > 0)))

    def item(s: dict) -> Markup:
        ident = f"ws-{s['host']}-{s['name'] or 'machine'}" if many else f"ws-{s['name']}"
        if s.get("reachable") is False:
            return h("div", {"class": "ws-item off", "id": ident, "role": "menuitem", "aria-disabled": "true", "title": s.get("said") or s["path"]},
                     h("span", {"class": "ws-n"}, s["name"] or "its workspaces"), h("span", {"class": "ws-mark"}, ""), h("span", {"class": "ws-c"}, space_says(s, ctx.model.now)))
        return h("a", {"class": f"ws-item{' a-you' if (s.get('waits') or 0) > 0 else ''}", "id": ident, "href": s["url"], "role": "menuitem",
                       "aria-current": "page" if s is here else None, "title": s["path"]},
                 h("span", {"class": "ws-n"}, s["name"]), h("span", {"class": "ws-mark"}, "this board" if s is here else ""), h("span", {"class": "ws-c"}, space_says(s)))

    if many:
        mine = here["host"] if here else machines[0]
        groups = [[h("div", {"class": "ws-head", "id": f"ws-head-{host}"}, host), [item(s) for s in order([s for s in spaces if s.get("host") == host])]]
                  for host in sorted(machines, key=lambda host: host != mine)]
    else:
        groups = [h("div", {"class": "ws-head"}, "Workspaces"), [item(s) for s in order(spaces)]]
    return h("details", {"class": "ws", "id": "ws", "data-menu": True},
             h("summary", {"class": "ws-cur", "title": f"{title}\nAnother workspace: click", "aria-haspopup": "menu",
                           "aria-label": f"{space_name(here, many) if here else ctx.workspace}: another workspace"},
               icon(ctx, "grid-2"), space_label(here, ctx.workspace, many),
               h("em", {"title": f"In {'one other workspace' if waiting == 1 else f'{waiting} other workspaces'} something waits for you"}, waiting) if waiting else None,
               icon(ctx, "chevron-down")),
             h("div", {"class": "ws-menu", "role": "menu", "aria-label": "The workspaces of the machines" if many else "The workspaces of this machine"},
               groups, h("a", {"class": "ws-all", "href": "/"}, "All the workspaces of the machines" if many else "All the workspaces of this machine")))


def topbar(ctx: Ctx, title: str, summary: str) -> Markup:
    m = ctx.model
    meta = m.meta
    not_green = sum(1 for t in m.proposed if not bm.is_green(t))
    chips = []
    if meta.get("base"):
        chips.append(chip(ctx, "branch", "", "tasks land on ", h("b", None, meta["base"])))
    if m.proposed:
        chips.append(chip(ctx, "pull", "you" if not_green else "", h("b", None, len(m.proposed)), " proposed", f" · {not_green} not green" if not_green else ", green"))
    pulls = [t for t in m.proposed if bm.pr_of(t)]
    looked = ctx.forge_look.get("looked") or 0
    if pulls and not meta.get("demo"):
        what = "the pull request" if len(pulls) == 1 else f"the {len(pulls)} pull requests"
        if looked and not ctx.forge_look.get("problem") and m.now - looked <= BOARD_LOOK_FRESH:
            chips.append(chip(ctx, "eye", "", "checked ", ago_(looked, m.now),
                              title=f"The board asks GitHub about {what} a few minutes apart, records a merge or a close there at once, and wakes the task's session"))
        else:
            chips.append(chip(ctx, "eye", "you", "nobody looks at ", what,
                              title=ctx.forge_look.get("problem") or f"The board's server has not asked GitHub about {what} lately: a merge or a close there shows here after its next look"))
    if m.landed_today:
        chips.append(chip(ctx, "check", "ok", h("b", None, len(m.landed_today)), " landed today"))
    return h("header", {"class": "bar"}, h("h1", None, title), h("span", {"class": "sum", "title": summary}, summary), h("div", {"class": "meta"}, chips),
             new_task_link(ctx, "bar-new") if ctx.can_act else None)


def statusbar(ctx: Ctx) -> Markup:
    m = ctx.model
    trouble = ctx.problems
    looked = ctx.forge_look.get("looked") or 0
    if ctx.forge_look.get("problem"):
        forge, forge_title = [h("span", {"class": "error"}, ctx.forge_look["problem"])], "The board asks GitHub itself while a pull request is open"
    elif looked:
        forge, forge_title = ["the board looked at GitHub ", ago_(looked, m.now)], "The board asks GitHub itself, a few minutes apart, while a pull request is open; a merge or a close there is recorded at once, and the task's session is woken"
    elif m.meta.get("demo"):
        forge, forge_title = ["example tasks: no forge is asked"], "A board of example tasks asks GitHub nothing"
    else:
        forge, forge_title = ["GitHub was not asked yet"], "The board asks GitHub itself, a few minutes apart, while a task is open with a pull request"
    return h("footer", {"class": f"status{' bad' if trouble else ''}", "id": "status"},
             h("span", {"title": "\n".join(trouble) or "Lem's files of this workspace read cleanly"},
               h("i", {"class": f"dot{' bad' if trouble else ''}"}), h("span", {"class": "error"}, f"{' · '.join(trouble)} · ") if trouble else None,
               "the event log read ", ago_(ctx.read_at, m.now), f" · {bm.plural(ctx.events, 'event')}"),
             h("span", {"title": forge_title}, *forge),
             h("span", {"class": "st-right"},
               h("span", {"class": "st-live", "id": f"live-{ctx.host}-{ctx.workspace}", "data-turbo-permanent": True, "data-controller": "stream",
                          "data-stream-url-value": f"{ctx.base}/stream", "data-stream-since-value": ctx.events}, "connecting…")))


def summary_of(m: bm.Model) -> str:
    """What the kanban holds, in one line, as the bar says it."""
    def in_build(status: str) -> int:
        return sum(1 for t in m.lane["build"] if t.status == status)

    approved = sum(1 for t in m.lane["build"] if t.approved)
    helped = sum(1 for t in m.lane["build"] if t.helped)
    n = len(m.for_owner)
    parts = [n and f"{n} wait{'s' if n == 1 else ''} for you", in_build("building") and f"{in_build('building')} build{'s' if in_build('building') == 1 else ''}",
             m.lane["checks"] and f"{len(m.lane['checks'])} in checks and review", in_build("queued") and f"{in_build('queued')} queued",
             in_build("planned") and f"{in_build('planned')} wait for their plan talk", in_build("blocked") and f"{in_build('blocked')} blocked",
             approved and f"{approved} approved, with no lead yet", helped and f"{helped} helped, with no lead yet", m.parked and f"{len(m.parked)} parked"]
    parts = [p for p in parts if p]
    if parts:
        return bm.cap(", ".join(parts))
    return "Nothing runs" if m.tasks else "Waiting for the first task: type /lem and an ask in any session"


# ---- the kanban ----

def card_chips(ctx: Ctx, t: bm.Task) -> list:
    """The chips a developer acts on: the type, who works on it, careful, the breaker that waits, a task stuck
    for want of its session, red checks, a review that was not clean, green or not green, and the pull request."""
    out = []
    if t.type:
        out.append(tag(ctx, "flag", t.type["type"], None, f"The type of the request, as Lem took it from the request: {t.type['type']}, because {t.type['why']}"))
    lead = bm.LEAD[bm.lead_of(t)] if t.lead else None
    if lead and lead["chip"]:
        out.append(tag(ctx, "split" if t.lead == "session" else "code", lead["chip"], "lead", lead["title"], t.status == "building"))
    careful = bm.careful_of(t)
    if careful and careful["yes"]:
        out.append(tag(ctx, "careful", "careful", "you", f"Careful, by {careful['by']}: {careful['why']}"))
    if t.breaker:
        out.append(h("span", {"class": "tag c-you live tc-wait", "title": f"Breaker {t.breaker.id}: {t.breaker.what}\n{bm.stop_words(t.breaker)}"}, icon(ctx, "alert"),
                     h("span", None, f"breaker {t.breaker.id} waits")))
    need = bm.session_need(t, ctx.model)
    if need:
        out.append(tag(ctx, "alert", "session does not answer" if need == "deaf" else "no session", "bad",
                       "A wake-up has waited in the task’s session for 10 minutes or more" if need == "deaf" else "No agent runs the task now: “Open a session” on its page starts a fresh one"))
    if t.gates and t.gate_bad:
        out.append(tag(ctx, "alert", f"checks red: {t.gate_bad} of {len(t.gates)}", "bad",
                       "\n".join(f"{'green' if g['exit'] == 0 else 'exit ' + str(g['exit'])}  {g['command']}  {g['last'] or ''}" for g in t.gates)))
    r = t.reviews[-1] if t.reviews else None
    if r and r["verdict"] != "clean" and not t.proposal:
        out.append(tag(ctx, "eye", f"{r['must_fix']} must-fix" if r["verdict"] == "must-fix" else "not reviewed", "bad", "\n".join(bm.review_line(x) for x in t.reviews)))
    if t.proposal:
        green = t.proposal["green"]
        out.append(tag(ctx, "check" if green else "alert", "green" if green else "not green", "ok" if green else "you", bm.GREEN if green else "\n".join(map(str, t.proposal["reasons"]))))
    pr = bm.pr_of(t)
    if pr:
        out.append(h("a", {"class": "tag c-gate tc-out", "href": pr["url"], "title": f"Open the pull request on the forge: {pr['url']}", "target": "_blank", "rel": "noopener"},
                     icon(ctx, "pull"), h("span", None, f"#{pr['n']}")))
    return out


def task_card(ctx: Ctx, t: bm.Task, lane: dict, selected: str | None = None) -> Markup:
    m = ctx.model
    sel = t.slug == selected
    line = bm.card_line(t, lane)
    time_ = h("span", {"data-ago": t.since}, bm.ago(m.now - t.since)) if t.closed else since(t.since, m.now)
    progress = None
    if t.progress and t.status == "building":
        n, of = t.progress["n"], t.progress["of"]
        progress = h("div", {"class": "mini", "title": f"task {n} of {of} of the plan"}, h("span", {"style": f"width:{100 * (n - 1) / of:.3f}%"}),
                     h("span", {"class": "cur", "style": f"left:{100 * (n - 1) / of:.3f}%;width:{100 / of:.3f}%"}))
    return h("article", {"class": f"tc s-{t.status} a-{t.info['actor']}{' sel' if sel else ''}", "id": f"card-{t.slug}", "data-task": t.slug},
             h("div", {"class": "tc-top"},
               h("a", {"class": "tc-title tc-link", **task_link(ctx, t.slug), "aria-current": "page" if sel else None}, t.title),
               h("div", {"class": "tc-time", "title": f"ended {bm.stamp(t.since, m.now)}" if t.closed else f"in this state since {bm.stamp(t.since, m.now)}"}, time_)),
             h("div", {"class": "tc-ask", "title": t.ask}, t.ask) if t.ask and bm.flat(t.ask) != bm.flat(t.title) else None,
             h("div", {"class": f"tc-line{' live' if t.info['live'] and not t.closed else ''}", "title": "\n".join(t.more) or None}, h("i"), h("span", None, rich(ctx, line))),
             progress,
             h("div", {"class": "tc-chips"}, card_chips(ctx, t)))


def kanban(ctx: Ctx) -> Markup:
    m = ctx.model
    selected = ctx.task
    folded = set(ctx.prefs.get("folded") or [])
    columns, tabs = [], []
    for i, lane in enumerate(bm.LANES):
        tasks = m.lane[lane["key"]]
        fold = lane["key"] in folded
        attrs = {"class": f"col a-{lane['actor']}{' folded' if fold else ''}", "id": f"col-{lane['key']}", "aria-label": lane["title"],
                 "data-action": "click->fold#column", "data-fold-key-param": lane["key"], "title": f"{lane['title']}: {bm.plural(len(tasks), 'task')}. Click to unfold." if fold else None}
        columns.append(h("section", attrs,
                         h("div", {"class": "col-head"}, h("i"), h("span", {"class": "col-name"}, lane["title"]), h("em", None, len(tasks)),
                           h("button", {"class": "ibtn", "type": "button", "data-action": "fold#column", "data-fold-key-param": lane["key"],
                                        "title": "Unfold the column" if fold else "Fold the column", "aria-label": f"Fold or unfold {lane['title']}"},
                             icon(ctx, "chevron-left"))),
                         h("div", {"class": "col-body", "id": f"col-body-{lane['key']}"},
                           [task_card(ctx, t, lane, selected) for t in tasks] or h("div", {"class": "col-empty"}, lane["empty"]))))
        tabs.append(h("button", {"class": f"ktab a-{lane['actor']}{' some' if tasks else ''}", "type": "button", "id": f"ktab-{lane['key']}",
                                 "data-columns-target": "tab", "data-action": "columns#show", "data-columns-index-param": i},
                      h("i"), lane["title"], h("em", None, len(tasks))))
    return h("div", {"class": "board-wrap", "data-controller": "columns"},
             h("nav", {"class": "ktabs", "id": "ktabs", "aria-label": "The columns"}, tabs),
             h("div", {"class": "view kanban", "id": "kanban", "data-columns-target": "board"}, columns))


def kanban_page(ctx: Ctx) -> Markup:
    ctx.view = "tasks"
    return layout(ctx, "Tasks", summary_of(ctx.model), kanban(ctx))


# ---- the reasons of not green ----

def reason_list(ctx: Ctx, t: bm.Task, reasons: list, key: str) -> Markup:
    """The reasons a proposal is not green, one row each: the reason in plain words first, what it is
    about beside it, and its detail folded under it (`lem_board_model.reason_rows`); a reason about a
    decision or a breaker links to it on "Criteria and decisions"."""
    rows = bm.reason_rows(reasons)
    if not rows:
        return h("ul", {"class": "reasons", "id": f"{key}-reasons"}, h("li", {"class": "rs-none"}, "no reason is on record"))
    out = []
    for i, r in enumerate(rows, 1):
        ref = r["ref"]
        to = h("a", {"class": "rs-to", **task_link(ctx, t.slug, "criteria"), "data-row": f"dec-{ref['id']}", "title": f"Open {ref['kind']} {ref['id']} on Criteria and decisions"},
               f"{ref['kind']} {ref['id']}", " ", icon(ctx, "arrow")) if ref else None
        head_ = [h("span", {"class": "rs-head"}, rich(ctx, r["head"])), r["about"] and h("span", {"class": "rs-about"}, rich(ctx, r["about"]))]
        if r["detail"]:
            out.append(h("li", {"class": "rs"}, h("details", {"class": "rs-fold", "id": f"{key}-r{i}"},
                                                  h("summary", None, icon(ctx, "chevron-right", "ic chev"), h("span", {"class": "rs-line"}, head_), to),
                                                  h("ul", {"class": "rs-detail"}, [h("li", None, rich(ctx, bm.cap(x))) for x in r["detail"]]))))
        else:
            out.append(h("li", {"class": "rs"}, h("div", {"class": "rs-flat"}, h("span", {"class": "ic chev"}), h("span", {"class": "rs-line"}, head_), to)))
    return h("ul", {"class": "reasons", "id": f"{key}-reasons"}, out)


# ---- "Waits for you" ----

def waits_page(ctx: Ctx) -> Markup:
    """One row for each thing the owner does, the most pressing first: what he does, in which task,
    since when, where he answers, and for a merge green or not green with the pull request."""
    ctx.view = "waits"
    m = ctx.model
    rows = []
    for w in bm.waits_of(m):
        t, c = w["t"], w["c"]
        say = bm.wait_say(w)
        where = say.get("where") or bm.answer_of(t)
        facts = []
        if w["kind"] == "breaker":
            facts.append(h("div", {"class": "wr-what"}, rich(ctx, c.what or "")))
            facts.append(h("div", {"class": "wr-sub"}, rich(ctx, bm.cap(bm.stop_words(c)))))
        if w["kind"] == "merge":
            verdict = bm.verdict_of(t)
            pr = bm.pr_of(t)
            marks = []
            if verdict is not None:
                marks.append(tag(ctx, "check" if verdict["green"] else "alert", "green" if verdict["green"] else "not green", "ok" if verdict["green"] else "you",
                                 bm.GREEN if verdict["green"] else None))
            if pr:
                marks.append(h("a", {"class": "tag c-gate", "href": pr["url"], "target": "_blank", "rel": "noopener", "title": f"Open the pull request on the forge: {pr['url']}"},
                               icon(ctx, "pull"), h("span", None, f"{pr['repo']}#{pr['n']}")))
            if marks:
                facts.append(h("div", {"class": "wr-marks"}, marks))
            if verdict and not verdict["green"]:
                facts.append(reason_list(ctx, t, verdict["reasons"], f"wr-{t.slug}"))
            elif verdict and verdict["green"]:
                facts.append(h("div", {"class": "wr-sub"}, bm.cap(bm.GREEN.lower()) + "."))
        elif w["kind"] in ("held", "criteria") and t.shown and say["verb"].lower() != t.shown.lower():
            facts.append(h("div", {"class": "wr-sub"}, rich(ctx, bm.cap(t.shown))))
        acts = row_acts(ctx, w)
        rows.append(h("article", {"class": f"wrow a-{say.get('actor', 'you')}", "id": f"wait-{w['key'].replace(':', '-')}"},
                      h("span", {"class": "fi"}, icon(ctx, say["icon"])),
                      h("div", {"class": "wr-main"},
                        h("div", {"class": "wr-top"}, h("a", {"class": "wr-verb", **task_link(ctx, t.slug, say["to"])}, say["verb"]),
                          h("span", {"class": "wr-time", "title": say["note"]}, since(w["since"], m.now))),
                        h("a", {"class": "wr-task", **task_link(ctx, t.slug, say["to"])}, t.title, h("span", {"class": "wr-state"}, f" · {t.info['label']}")),
                        facts,
                        acts,
                        h("div", {"class": "wr-where"}, h("b", None, "Where you answer: "), rich(ctx, where)))))
    if not rows:
        rows = [h("div", {"class": "wait-none"}, icon(ctx, "circle-check"), h("div", None, h("b", None, "Nothing waits for you."),
                  " A breaker, criteria to approve, a plan to read, a pull request to merge or a task with no session shows here when it comes."))]
    n = len(bm.waits_of(m))
    summary = f"{bm.plural(n, 'thing')} you do, the most pressing first" if n else "Nothing waits for you"
    return layout(ctx, "Waits for you", summary, h("div", {"class": "view scroll", "id": "waits-view"}, h("div", {"class": "waits-list"}, rows, parked_group(ctx)), push_row(ctx, "page")))


def row_acts(ctx: Ctx, w: dict) -> Markup | None:
    """The buttons of a row of "Waits for you": the way to criteria that wait for the owner's yes, which he
    gives under their text, the way to a merge's confirm step, the way to park a task whose breaker waits, and
    "Open a session" for a task stuck with none. None on a page that may not act, and for a row with no act."""
    if not ctx.can_act:
        return None
    t = w["t"]
    acts = bm.acts_of(t, ctx.model.seen)
    out = []
    if w["kind"] == "criteria" or (w["kind"] == "held" and "approve" in acts):
        waiting = ctx.criteria_waiting(t.slug) if "approve" in acts else None
        if waiting:
            # his yes is under the criteria themselves, on the task's tab: no yes to a contract from one tap on a list
            out.append(h("a", {"class": "btn go", **task_link(ctx, t.slug, "criteria")}, icon(ctx, "file"), h("span", None, "Read and approve…")))
    if w["kind"] == "merge" and "merge" in acts:
        out.append(h("span", {"class": "btn busy", "role": "status"}, icon(ctx, "clock"), h("span", None, "Merging…")) if t.slug in ctx.merging
                   else act_link(ctx, t.slug, "merge", "Merge…", "pull", "risk", "waits", frame=True))
    if w["kind"] == "breaker" and "park" in acts:
        out.append(act_link(ctx, t.slug, "park", "Park it…", "park", "", "waits", frame=True))
    if w["kind"] == "session" and bm.opens_session(t, ctx.model):
        out.append(act_form(ctx, t.slug, "session", "Open a session", "play", "go", "Opening…", {"in": "waits"}))
    return h("div", {"class": "wr-acts"}, out) if out else None


def parked_group(ctx: Ctx) -> Markup | None:
    """The tasks the owner parked, at the foot of "Waits for you" and apart from it: a group in the look of
    the backlog's recessive one, each task folded, with since when, why in his words, and the command that
    brings it back. Nothing of them waits, so they are no row above and no count of the sidebar."""
    m = ctx.model
    if not m.parked:
        return None
    items = []
    for t in m.parked:
        p = bm.parked_of(t)
        stopped = t.stopped
        items.append(h("details", {"class": "bl-item", "id": f"parked-{t.slug}"},
                       h("summary", {"class": "bl-head"},
                         h("span", {"class": "bl-title"}, t.title),
                         h("span", {"class": "bl-side"}, tag(ctx, "park", "parked", None, f"Parked at {bm.stamp(p['since'], m.now)}"),
                           h("span", {"class": "wr-time", "title": f"parked at {bm.stamp(p['since'], m.now)}"}, since(p["since"], m.now))),
                         h("span", {"class": "wr-sub"}, rich(ctx, bm.cap(p["why"])) if p["why"] else "No reason is on record.")),
                       h("div", {"class": "bl-body"},
                         stopped and h("div", {"class": "wr-sub"}, f"Breaker {stopped.id} stopped its build: “", rich(ctx, stopped.what or ""), f"”, since {bm.stop_words(stopped)}."),
                         h("div", {"class": "wr-sub"}, f"Parked at {bm.stamp(p['since'], m.now)}. Its worktree, its branch and its files stay as they are."),
                         h("div", {"class": "bl-actions"}, h("span", {"class": "bl-note"}, "To bring it back, type in any session: "), h("code", None, p["resume"]),
                           h("a", {"class": "btn", **task_link(ctx, t.slug)}, "Open the task ", icon(ctx, "arrow"))))))
    return h("div", {"class": "bl-group a-quiet recessive", "id": "parked", "aria-label": "Parked: nothing of these waits"},
             h("div", {"class": "lane-head", "title": "Tasks you put aside: nothing of them waits for you"}, h("i"), "Parked", h("em", None, len(m.parked))), items)


# The control of the board's notifications: a sentence for each state the `push` controller can set
# (data-js-push), and the buttons of each; push.css shows the ones of the state set.
PUSH_SAYS = {
    "busy": ("…", None),
    "insecure": ("not on this address", "Notifications need a secure address: the board through the tailnet door (https), or on this Mac at 127.0.0.1. This page has another address over plain http."),
    "home": ("Home Screen first", "On an iPhone or an iPad, only the board on the Home Screen gets notifications. Tap Share, then Add to Home Screen, and open Lem from there."),
    "none": ("not in this browser", "This browser has no web push."),
    "blocked": ("blocked", "This browser blocks notifications for the board. Allow them in its settings for this site (on an iPhone: Settings, Notifications, Lem), then load the page again."),
    "off": ("off", "A tap turns them on for this device. The browser asks you once."),
    "on": ("on", "This device gets a notification each time something starts to wait for you."),
}


def push_row(ctx: Ctx, where: str) -> Markup:
    """The one row that turns this device's notifications on and off (the `push` controller, lem_push):
    on "Waits for you", and in the sidebar, where push.css shows it only in a phone's drawer."""
    return h("section", {"class": f"push push-{where}", "id": f"push-{where}", "data-controller": "push", "aria-label": "Notifications on this device"},
             h("span", {"class": "fi"}, icon(ctx, "bell")),
             h("div", {"class": "push-main"},
               h("div", {"class": "push-top"}, h("b", None, "Notify this device when something waits"),
                 [h("span", {"class": f"push-state s-{key}", "data-for": key}, word) for key, (word, _) in PUSH_SAYS.items()]),
               [h("p", {"class": "push-say", "data-for": key}, said) for key, (_, said) in PUSH_SAYS.items() if said]),
             h("div", {"class": "push-acts"},
               h("button", {"class": "btn go", "type": "button", "data-for": "off", "data-action": "push#on"}, "Turn on"),
               h("button", {"class": "btn", "type": "button", "data-for": "on", "data-action": "push#test"}, "Send a test"),
               h("button", {"class": "btn", "type": "button", "data-for": "on", "data-action": "push#off"}, "Turn off")))


# ---- the backlog ----

def days_old(iso: str, now: int) -> int | None:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", iso or ""):
        return None
    noon = bm.at(f"{iso}T12:00:00")
    return max(0, round((now - noon) / 86400000)) if noon else None


# The backlog's filter in the address: words (`q`), one worth (`worth`), and one fact (`only`): a place
# that no longer resolves, or an item git does not have committed.
WORTHS = {"yes", "later", "unset", "no"}
FACTS = {"stale": ("Where no longer resolves", "the place the item names is not there any more"),
         "new": ("Not committed", "added or edited, and not committed yet")}


def backlog_filter(query: dict) -> dict:
    """The backlog's filter from the address's query (`parse_qs`): the words in the field, the chip that
    is on, and what the links of the chips carry, so that a shared link shows the same list (the backlog
    controller hides the items it leaves out). A value it does not know is no filter."""
    one = lambda key: (query.get(key) or [""])[0].strip()  # noqa: E731
    worth, only = one("worth"), one("only")
    return {"q": one("q")[:200], "worth": worth if worth in WORTHS else "", "only": only if only in FACTS else ""}


def worth_of(it: dict) -> str:
    return it.get("worth") if it.get("worth") in ("yes", "later", "no") else "unset"


def filter_href(ctx: Ctx, f: dict, **change: str) -> str:
    """The address of the backlog with the filter F changed: a value given again takes it off."""
    want = {**f, **{k: ("" if f.get(k) == v else v) for k, v in change.items()}}
    query = "&".join(f"{k}={quote(v)}" for k, v in want.items() if v)
    return f"{ctx.href('backlog')}{'?' + query if query else ''}"


def backlog_item(ctx: Ctx, it: dict) -> Markup:
    days = days_old(it.get("added", ""), ctx.model.now)

    def t_(text, title, c=None):
        return h("span", {"class": f"tag{f' c-{c}' if c else ''}", "title": title}, h("span", None, text))

    side = []
    if it.get("state") == "unreadable":
        side.append(t_("cannot be read", "The file of this item is a link to nothing, a folder, or not readable", "bad"))
    elif it.get("state"):
        side.append(t_("new, not committed" if it["state"] == "new" else "edited, not committed", "git does not have this version of the item yet", "gate"))
    if days is not None:
        side.append(t_("today" if days == 0 else f"{days} d", f"added {it.get('added')}"))
    where = it.get("where") or ""
    if where and it.get("where_problem"):
        place = h("span", {"class": "bl-where stale", "title": "The place this item points at is not there any more. The item may be done, or the code moved."},
                  icon(ctx, "alert"), h("span", None, f"{where} · {it['where_problem']}"))
    else:
        place = h("span", {"class": "bl-where"}, where or "no place in the code named")
    cmd = f"/lem new {it['path']}"
    if ctx.can_act:
        actions = h("div", {"class": "bl-actions"},
                    h("form", {"class": "act-form", "method": "post", "action": f"{ctx.base}/start", "data-turbo-frame": "_top"},
                      h("input", {"type": "hidden", "name": "item", "value": it["slug"]}),
                      h("button", {"class": "btn go", "type": "submit", "data-turbo-submits-with": "Starting…"}, icon(ctx, "play"), h("span", None, "Start a task"))),
                    h("span", {"class": "bl-note"}, "Lem opens the task's own session in agterm, which reads this item."))
    elif SAFE_PATH.fullmatch(it["path"]):
        actions = h("div", {"class": "bl-actions"}, h("span", {"class": "bl-note"}, "To start a task, type in any session: "), h("code", None, cmd),
                    h("button", {"class": "ibtn copy", "type": "button", "data-controller": "copy", "data-copy-text-value": cmd, "data-action": "copy#copy",
                                 "title": "Copy the line", "aria-label": "Copy the line"}, icon(ctx, "copy"), icon(ctx, "check", "ic done")))
    else:
        actions = h("div", {"class": "bl-actions"}, h("span", {"class": "bl-note bad"},
                    "The name of this file has a character that a line to type would not keep. Start the task yourself in a session, with your own words."))
    body = it.get("body") or ""
    return h("details", {"class": "bl-item", "id": f"item-{it['slug']}", "data-backlog-target": "item", "data-worth": worth_of(it),
                         "data-stale": "1" if it.get("where_problem") else None, "data-new": "1" if it.get("state") in ("new", "edited") else None},
             h("summary", {"class": "bl-head"}, h("span", {"class": "bl-title"}, rich(ctx, it["title"])), h("span", {"class": "bl-side"}, side), place),
             h("div", {"class": "bl-body"},
               md_block(ctx, f"bl-{it['slug']}", body, cls="bl-text") if body else h("div", {"class": "bl-text dim"}, "The item has no text below its title."),
               actions))


def backlog_page(ctx: Ctx) -> Markup:
    ctx.view = "backlog"
    backlog = ctx.backlog
    m = ctx.model
    items = backlog["items"] if backlog else []
    f = {"q": "", "worth": "", "only": "", **(ctx.filters or {})}
    groups = []
    for g in BY_WORTH:
        mine = [it for it in items if worth_of(it) == g["key"]]
        if mine:
            groups.append(h("div", {"class": f"bl-group a-{g['actor']}{' recessive' if g.get('recessive') else ''}", "id": f"group-{g['key']}", "data-backlog-target": "group"},
                            h("div", {"class": "lane-head"}, h("i"), g["name"], h("em", None, len(mine))), [backlog_item(ctx, it) for it in mine]))
    if backlog is None:
        empty = h("div", {"class": "lane-empty"}, "The backlog was not read: the status bar says why.")
    elif not items:
        empty = h("div", {"class": "lane-empty"}, f"No item in {backlog['folder']}. The polish pass of a landing files items, and /backlog adds one.")
    else:
        empty = None
    stale = sum(1 for it in items if it.get("where_problem"))
    fresh = sum(1 for it in items if it.get("state") in ("new", "edited"))
    broken = sum(1 for it in items if it.get("state") == "unreadable")
    sum_ = ""
    if backlog:
        read = bm.at(backlog.get("read"))
        sum_ = (f"{bm.plural(len(items), 'item')} in {backlog['folder']}{f' · {broken} cannot be read' if broken else ''}"
                f"{f' · read {bm.stamp(read, m.now)}' if read else ''}")

    def chip_(key: str, value: str, label: str, n: int, actor: str, title: str) -> Markup:
        on = f.get(key) == value
        return h("a", {"class": f"fchip a-{actor}{' on' if on else ''}{' zero' if not n else ''}", "id": f"f-{key}-{value}", "href": filter_href(ctx, f, **{key: value}),
                       "data-turbo-action": "replace", "data-backlog-target": "chip", "data-key": key, "data-value": value,
                       "data-action": "backlog#pick", "aria-pressed": "true" if on else "false", "title": title},
                 h("i"), h("span", None, label), h("em", None, n))

    counts = {g["key"]: sum(1 for it in items if worth_of(it) == g["key"]) for g in BY_WORTH}
    chips = [chip_("worth", g["key"], g["name"], counts[g["key"]], g["actor"], f"Only the items whose worth is {g['key']}") for g in BY_WORTH if counts[g["key"]]]
    facts_ = [chip_("only", "stale", FACTS["stale"][0], stale, "bad", f"Only the items where {FACTS['stale'][1]}"),
              chip_("only", "new", FACTS["new"][0], fresh, "gate", f"Only the items {FACTS['new'][1]}")]
    filtered = bool(f["q"] or f["worth"] or f["only"])
    view = h("div", {"class": "view scroll", "id": "backlog-view"},
             h("div", {"class": "backlog", "id": "backlog", "data-controller": "backlog", "data-action": "keydown@window->backlog#key", "data-backlog-base-value": ctx.href("backlog")},
               act_note(ctx, ctx.note if ctx.note and ctx.note.get("act") == "start" else None),
               h("div", {"class": "bl-bar"},
                 h("input", {"id": f"bl-q-{ctx.workspace}", "type": "search", "placeholder": "Filter by the words of a title, a text or a place", "aria-label": "Filter the items of the backlog",
                             "autocomplete": "off", "spellcheck": "false", "value": f["q"] or None, "data-backlog-target": "query", "data-turbo-permanent": True,
                             "data-action": "input->backlog#filter keydown->backlog#clear", "data-hotkey": "Slash"}),
                 h("a", {"class": "btn", "href": f"{ctx.href('backlog')}?read=1", "data-turbo-action": "replace", "data-hotkey": "KeyR"}, "Read again ", h("kbd", None, "R"))),
               h("div", {"class": "fchips", "id": "bl-chips", "role": "group", "aria-label": "Filter by worth or by a fact"},
                 h("a", {"class": f"fchip all{'' if filtered else ' on'}", "id": "f-all", "href": ctx.href("backlog"), "data-turbo-action": "replace", "data-backlog-target": "chip",
                         "data-key": "all", "data-action": "backlog#pick", "aria-pressed": "false" if filtered else "true", "title": "Every item: the filter off"},
                   h("span", None, "All"), h("em", None, len(items))),
                 chips, h("span", {"class": "fsep", "aria-hidden": "true"}), facts_),
               h("div", {"class": "dim small bl-sum"}, h("span", {"data-backlog-target": "count"}), sum_),
               h("div", {"class": "backlog", "id": "bl-groups"}, groups, empty,
                 h("div", {"class": "lane-empty", "data-backlog-target": "none", "data-js-out": True}, "No item fits the filter.")),
               h("div", {"class": "keys"}, h("kbd", None, "/"), " filter · ", h("kbd", None, "J"), " ", h("kbd", None, "K"), " move · ", h("kbd", None, "Enter"),
                 " open or close · ", h("kbd", None, "R"), " read again")))
    return layout(ctx, "Backlog", "The items of the backlog, by the worth each one gives itself", view)


# ---- a new task ----

def new_page(ctx: Ctx) -> Markup:
    """The form of a new task in the owner's words: the board's "+". Lem names the task from its first
    words and opens its own session in agterm, with no focus; that session reads the type and the track
    and asks him what it needs. A page another machine passed through, or one that cannot act, says how
    to start it in a session instead."""
    ctx.view = "new"
    if ctx.can_act:
        form = h("form", {"class": "act-form act-stack nt-form", "method": "post", "action": f"{ctx.base}/start", "data-turbo-frame": "_top"},
                 h("label", {"class": "act-field"}, h("span", None, "What should Lem do?"),
                   h("textarea", {"name": "words", "rows": "5", "maxlength": "2000", "required": True, "autocomplete": "off", "spellcheck": "true",
                                  "enterkeyhint": "done", "placeholder": "Add the gift note to the CSV export"})),
                 h("div", {"class": "act-row"},
                   h("button", {"class": "btn go", "type": "submit", "data-turbo-submits-with": "Starting…"}, icon(ctx, "play"), h("span", None, "Start the task")),
                   h("a", {"class": "btn", "href": ctx.href("tasks")}, h("span", None, "Cancel"))))
    else:
        form = h("p", {"class": "sub"}, "This page starts nothing here: start a task on the board on the Mac or through the tailnet door, or type /lem and your words in any session.")
    card = h("section", {"class": "card confirm a-you nt-card", "id": "new-task", "aria-label": "A new task"},
             h("div", {"class": "eyebrow"}, "New task"),
             h("p", None, "Say it as you would to a colleague, in a sentence or two. Lem names the task from its first words, "
                          "and opens the task's own session in agterm, at the top of its workspace."),
             h("p", {"class": "sub"}, "That session reads your words, tells the type and the track, and asks you what it needs."),
             form)
    view = h("div", {"class": "view scroll", "id": "new-view"},
             h("div", {"class": "nt", "id": "nt"}, act_note(ctx, ctx.note if ctx.note and ctx.note.get("act") == "start" else None), card))
    return layout(ctx, "New task", "A new task, in your words", view)


# ---- the activity ----

NICE_MINUTES = [1, 2, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 240, 360, 480, 720, 1080, 1440]


def nice_ceil(ms: float) -> int:
    found = next((m for m in NICE_MINUTES if m * 60000 >= ms), None)
    return (found if found is not None else -(-int(ms) // 86400000) * 1440) * 60000


def timeline(ctx: Ctx) -> Markup:
    """What each task of today waited on, over time: one row for each task, a bar for each status it
    held, in the color of who acted then; each bar says its status, who acted and its times in its hover."""
    m = ctx.model
    shown = sorted((t for t in m.tasks if not t.closed or bm.local(t.since).date() == bm.local(m.now).date()), key=lambda t: t.first)
    rows = [t for t in shown if t.segments]
    if not rows:
        return h("div", {"class": "tl-empty"}, "A row appears when a task writes its first state")
    t0 = min(t.first for t in rows)
    any_open = any(not t.closed for t in rows)
    coarse = -(-m.now // 15000) * 15000 if any_open else max(t.last_ts for t in rows)
    whole = nice_ceil(max(60000, coarse - t0))

    def x(ms: float) -> float:
        return 100 * min(whole, max(0, ms - t0)) / whole

    lines = []
    for t in rows:
        bars = []
        for g in t.segments:
            info = t.info if g["open"] and t.checks_stop else bm.STATUS.get(g["status"], bm.UNKNOWN)
            x1, x2 = x(g["start"]), x(coarse if g["open"] else g["end"])
            if g["end"] == g["start"] and not g["open"]:
                bars.append(h("span", {"class": f"tl-dot a-{info['actor']}", "style": f"left:{x1:.3f}%", "title": f"{info['label']} at {bm.stamp(g['start'], m.now)}"}))
                continue
            to = "now" if g["open"] else bm.stamp(g["end"], m.now)
            bars.append(h("span", {"class": f"tl-seg s-{g['status']} a-{info['actor']}{' live' if g['open'] and info['live'] else ''}",
                                   "style": f"left:{x1:.3f}%;width:max(2px, {x2 - x1:.3f}%)",
                                   "title": f"{info['label']} · {info['who']} · {bm.stamp(g['start'], m.now)} to {to} · {bm.span((m.now if g['open'] else g['end']) - g['start'])}"}))
        lines.append(h("div", {"class": "tl-row", "id": f"tl-{t.slug}"},
                       h("a", {"class": "tl-label", "title": t.title, **task_link(ctx, t.slug, "timeline")}, t.title),
                       h("div", {"class": "tl-track"}, bars)))
    # a tick names its date only where the axis passes into another day; the axis's first day stands at its left
    labels = [bm.tick_label(t0 + whole * i / 6, whole, t0 + whole * (i - 1) / 6 if i else t0) for i in range(7)]
    ticks = [tick(f"tl-tick{' first' if i == 0 else ' last' if i == 6 else ''}", 100 * i / 6, label) for i, label in enumerate(labels)]
    first_day = "today" if bm.local(t0).date() == bm.local(m.now).date() else bm.day_label(t0)
    now_line = h("span", {"class": "tl-now", "style": f"left:{x(coarse):.3f}%"}) if any_open and coarse - t0 <= whole else None
    return h("div", {"class": "tl"}, h("div", {"class": "tl-rows"}, lines, h("div", {"class": "tl-grid", "aria-hidden": "true"}, [h("i", {"style": f"left:{100 * i / 6:.3f}%"}) for i in range(7)], now_line)),
             h("div", {"class": "tl-axis"}, h("span", {"class": "tl-day"}, first_day), h("div", {"class": "tl-ticks"}, ticks)))


def tick(cls: str, left: float, label: str) -> Markup:
    """A tick of a time axis: its time, and under it its date where the axis passes into another day
    (`Nov 21 01:18`), so that a dated tick is no wider than its neighbors."""
    date, _, clock = label.rpartition(" ")
    return h("span", {"class": f"{cls}{' dated' if date else ''}", "style": f"left:{left:.3f}%"}, clock, h("small", None, date) if date else None)


def legend(ctx: Ctx) -> list:
    """One entry for each look a bar can have; statuses drawn alike share an entry."""
    m = ctx.model
    shown = [t for t in m.tasks if not t.closed or bm.local(t.since).date() == bm.local(m.now).date()]
    total: dict[str, float] = {}
    for t in shown:
        for g in t.segments:
            total[g["status"]] = total.get(g["status"], 0) + (m.now if g["open"] else g["end"]) - g["start"]
    looks: dict[str, list] = {}
    for k in bm.STATUS:
        if total.get(k, 0) > 0:
            look = bm.STATUS[k]["actor"] + (f":{k}" if k in ("queued", "ready") else "")
            looks.setdefault(look, []).append(k)
    return [h("span", {"class": f"a-{bm.STATUS[keys[0]]['actor']}", "title": "\n".join(f"{bm.STATUS[k]['label']}: {bm.STATUS[k]['who']} acts" for k in keys)},
              h("i", {"class": f"s-{keys[0]}" if ":" in look else None}), " · ".join(bm.STATUS[k]["label"] for k in keys)) for look, keys in looks.items()]


def feed_rows(ctx: Ctx) -> list:
    m = ctx.model
    rows = []
    for i, e in bm.feed(m.events):
        d = bm.describe(e, m)
        rows.append(h("div", {"class": f"row a-{d['info']['actor']}", "id": f"ev-{i}"},
                      h("span", {"class": "fi"}, icon(ctx, d["info"]["icon"])),
                      h("div", {"class": "rtext"},
                        h("a", {"class": "rlink", **task_link(ctx, e.get("task"), "timeline")}, d["title"]) if e.get("task") else None, " · " if e.get("task") else None,
                        h("b", None, d["head"]), " · " if d.get("text") else None, h("span", {"class": "cmd" if d.get("mono") else None}, linked(ctx, d.get("text") or "")),
                        h("span", {"class": "sub"}, linked(ctx, d["sub"])) if d.get("sub") else None),
                      h("span", {"class": "rtime"}, bm.stamp(bm.at(e.get("ts")), m.now))))
    return rows or [h("div", {"class": "empty"}, "No events yet")]


def activity_page(ctx: Ctx) -> Markup:
    ctx.view = "activity"
    m = ctx.model
    count = len(m.events)
    view = h("div", {"class": "view scroll", "id": "activity-view"},
             h("section", {"class": "card", "id": "a-time"},
               h("div", {"class": "card-head"}, h("h2", None, "Where the time went"), h("div", {"class": "legend"}, legend(ctx))), timeline(ctx)),
             h("section", {"class": "card", "id": "a-feed"},
               h("div", {"class": "card-head"}, h("h2", None, "Activity"),
                 h("div", {"class": "dim small"}, bm.plural(count, "event") + (" · the newest 200" if count > 200 else ""))),
               h("div", {"class": "feed rows"}, feed_rows(ctx))))
    return layout(ctx, "Activity", "What each task waited on today, and every event, the newest first", view)


# ---- the pages outside a workspace ----

def plain_page(title: str, asset, body: list, eyebrow: str) -> Markup:
    """A page in lem.css's document look, with the mark: the list of workspaces, an error."""
    ident = h("div", {"class": "top"}, h("div", {"class": "ident"},
                                         h("div", {"class": "mark"}, marks()),
                                         h("div", {"class": "eyebrow"}, eyebrow),
                                         h("div", {"class": "title", "data-title": title}, h("h1", None, title)),
                                         body[0] if body else None))
    return page(head(f"{title} · Lem", asset), h("body", {"class": "app plain"}, h("main", {"class": "page doc"}, ident, body[1:])))


def index_page(host: str, spaces: list, asset) -> Markup:
    """The workspaces of this machine, and of each machine joined (`lem_peers`), each with how many things
    wait for the owner and what its tasks do now, the ones that wait for him first; a workspace of a
    machine that does not answer last, grayed, with when it last answered. With one machine a workspace is
    its name, with more `HOST/WORKSPACE`."""
    machines = machines_of(spaces)
    many = len(machines) > 1
    now = bm.now_ms()
    rows = []
    for s in sorted(spaces, key=lambda s: (s.get("reachable") is False, -(s.get("waits") or 0))):
        ident = f"space-{s['host']}-{s['name'] or 'machine'}" if many else f"space-{s['name']}"
        if s.get("reachable") is False:
            chips = [h("span", {"class": "chip bad", "title": s.get("said") or None}, "not reachable"),
                     h("span", {"class": "chip"}, f"last answer {bm.ago(now - s['answered'])}") if s.get("answered") else None]
            rows.append(h("div", {"class": "box quiet ws-box off", "id": ident, "title": s.get("said") or None},
                          h("h2", None, space_name(s, many)), h("p", {"class": "mono dim small"}, s["path"] or s.get("said") or ""), h("div", {"class": "meta"}, chips)))
            continue
        if s.get("problem"):
            chips = h("span", {"class": "chip bad"}, s["problem"])
        else:
            waits = s["waits"]
            chips = [h("span", {"class": "chip you"}, h("b", None, waits), f" {'waits' if waits == 1 else 'wait'} for you") if waits else h("span", {"class": "chip"}, "nothing waits for you"),
                     h("span", {"class": "chip"}, runs_say(s))]
        rows.append(h("a", {"class": f"box ws-box{' you' if s.get('waits') else ''}", "href": s["url"], "id": ident},
                      h("h2", None, space_name(s, many)), h("p", {"class": "mono dim small"}, s["path"]), h("div", {"class": "meta"}, chips)))
    if not rows:
        rows.append(h("section", {"class": "box quiet"}, h("h2", None, "No workspace yet"),
                      h("p", None, "Run ", h("code", None, "lem board"), " in a repository that uses Lem, or ", h("code", None, "lem serve --add DIR"), ". Then load this page again.")))
    named = sum(1 for s in spaces if s["name"])
    count = f"{named} {'repository' if named == 1 else 'repositories'}"
    where = f"on {len(machines)} machines" if many else "on this machine"
    return plain_page("Workspaces", asset, [h("p", {"class": "ask"}, f"{count} {where} that use Lem."), *rows], f"Lem · {host}")


def error_page(title: str, said: str, asset, fix: str | None = None) -> Markup:
    """A route that failed, with its reason and what fixes it: never a blank page."""
    return plain_page(title, asset, [h("p", {"class": "ask"}, said), h("section", {"class": "box"}, h("p", None, fix)) if fix else None,
                                      h("p", None, h("a", {"class": "btn", "href": "/"}, "The workspaces of this machine"))], "Lem · the board")


def manifest(asset) -> str:
    """The web app manifest: the board added to a phone's home screen opens as an app of its own, at `/`."""
    return json.dumps({
        "name": "Lem", "short_name": "Lem", "description": "The board of Lem's tasks on this machine",
        "start_url": "/", "scope": "/", "display": "standalone", "background_color": THEME["dark"], "theme_color": THEME["dark"],
        "icons": [{"src": asset("icon-192.png"), "sizes": "192x192", "type": "image/png"},
                  {"src": asset("icon-512.png"), "sizes": "512x512", "type": "image/png"}],
    }, indent=2)

