#!/usr/bin/env python3
"""lem ask — ask the user a rich question in an agterm HTML overlay and print the answer
as JSON.

  lem ask SPEC.json | lem ask - < spec.json      ask from a JSON spec (see SKILL.md for the schema)
  lem ask q "Prompt" "Label|subtitle" "*Recommended|subtitle|why" ... [--multi] [--context MD]
  lem ask wait PAGE_ID                          resume waiting after a timeout (exit 4)
  lem ask close [PAGE_ID]                       close the question page this session shows (that one, when named),
                                                whose answer came from elsewhere; its waiter ends as dismissed
  lem ask demo [NAME ...]                       open bundled demos (no name: list them)
  lem ask templates                             list templates with their one-line purpose
  lem ask render SPEC -o FILE                   build the page only, open nothing
  lem ask hook-stop                             the plugin's Stop hook (not for agents to run)

Common flags: --follow (pull the user to this session), --size N (floating panel, % of
the session), --timeout SEC (default 570, under the Bash tool's 600 s cap), --browser
(force the local-browser fallback), --no-status (leave the sidebar glyph alone).

Exit codes: 0 answered or "chat" (user wants to discuss in the terminal), 2 dismissed
(closed unanswered), 3 no way to show it (outside agterm without --browser, or an
unattended run), 4 still pending after --timeout (run `lem ask wait ID`), 5 the session
already shows an overlay, 1 error.

Environment: AGTERMCTL (path to agtermctl), LEM_TASK (a task's session of Lem: the card
is kept in the task's folder, where Lem's board answers it too, and the first answer
recorded counts; the answer then carries "from": "session" or "board"). The personal
defaults are the table [ask] of Lem's own settings file,
$XDG_CONFIG_HOME/lem/settings.toml or ~/.config/lem/settings.toml (`browser = true`
there opens the page in the browser outside agterm); the mermaid bundle is kept in
$XDG_CACHE_HOME/lem or ~/.cache/lem.
"""  # noqa: E501 - the usage table of `--help` keeps its columns

# What only the page server, the browser fallback, the mermaid download, an embedded
# image, a page's name or the command line uses is imported in the function that uses
# it: the plugin's Stop hook (`hook_stop`) runs this file at the end of every turn of
# every session, and loads only what it uses.
import json
import os
import re
import shutil
import subprocess
import sys
import time
import typing
from pathlib import Path
from types import MappingProxyType
from typing import Any, NoReturn

from lem import paths

if typing.TYPE_CHECKING:
    import argparse
    from collections.abc import Callable, Mapping
    from types import ModuleType

# the skill's directory, skills/lem-ask: its runtime, templates, demos and defaults
HERE = paths.ASK
RUNTIME = HERE / "runtime"
TEMPLATES = HERE / "templates"
DEMOS = HERE / "demos"
DEFAULTS = HERE / "defaults.json"
# The keys of the table [ask] of Lem's home settings file; `lem project` takes the same
# five (project.py TABLES).
ASK_KEYS = ("style", "size", "review", "browser", "status")
STATUS_KEYS = ("asking", "answered")
OUTDIR = os.path.join(os.environ.get("TMPDIR", "/tmp"), "lem-ask")  # noqa: S108 - the folder prints as TMPDIR is written, a // kept; /tmp when TMPDIR names none
# Seconds an old page stays in OUTDIR, for debugging.
PAGE_KEEP = 86400
# The end of the name of a page opened with --no-status: the Stop hook reads a page's
# choice from the file agterm shows it from, and sets no status for it.
QUIET_PAGE = ".no-status.html"
# The end of the name of the file in OUTDIR that keeps the word of the last
# `lem ask wait` on a page, "status" or "no-status", for the Stop hook: the caller's
# last word holds over the name of the page. It ends in .html, so the sweep of
# `write_page` takes it with the pages.
WAIT_WORD = ".wait.html"
MERMAID_URL = "https://cdn.jsdelivr.net/npm/mermaid@11.12.0/dist/mermaid.min.js"
MERMAID_NAME = "mermaid-11.12.0.min.js"
# jsDelivr's published sha256 for that file
# (data.jsdelivr.com/v1/package/npm/mermaid@11.12.0/flat). The page runs with agterm's
# bridge, which can type into terminals, so unverified code never goes in.
MERMAID_SHA256 = "07e37dfa97b337ccc85365d57eddf99b9706f09db3b59b260d0333b23b343c4b"
MAX_IMAGE = 8 * 1024 * 1024
# When the plugin's Stop hook finds a question page still open, it re-posts the asking
# status at these offsets (seconds): status hooks run in parallel with it, so a slower
# one may post after it does, and one slower than the last offset wins.
STOP_RECHECKS = (0.5, 1.5, 3, 6)
# Seconds the Stop hook gives each call of agtermctl: one that has not answered by then
# is killed, and the hook ends there.
STOP_CALL = 2
SOURCED = (
    "code",
    "diff",
    "md",
    "mermaid",
)  # blocks whose text may come from {"file": …}
# a whole file past this needs `lines`: nobody reads 3,000 lines to find the 20
# in question
CODE_MAX_LINES = 300


def emit(record: object, code: int) -> NoReturn:
    print(json.dumps(record, ensure_ascii=False))
    sys.exit(code)


def die(msg: str, code: int = 1) -> NoReturn:
    emit({"status": "error", "error": msg}, code)


# ---------- spec loading ----------


def load_spec(arg: str | None) -> dict[str, Any]:
    if arg in (None, "-"):
        if sys.stdin.isatty():
            die("no spec: pass a JSON file or pipe one on stdin")
        try:
            raw = sys.stdin.buffer.read().decode("utf-8")
        except UnicodeDecodeError as error:
            die(f"the spec on stdin is not UTF-8 text: {error}")
    else:
        try:
            with open(os.path.expanduser(arg), encoding="utf-8") as stream:
                raw = stream.read()
        except UnicodeDecodeError as error:
            die(f"the spec {arg} is not UTF-8 text: {error}")
        except OSError as error:
            die(f"cannot read the spec: {error}")
    try:
        # half of a UTF-16 pair alone ("\ud83d") is U+FFFD, as in what a page sends
        # (`submitted`): the page, the card and every message write as UTF-8
        return typing.cast("dict[str, Any]", lem_cards().whole(json.loads(raw)))
    except json.JSONDecodeError as error:
        die(f"spec is not valid JSON: {error}")
    except (ValueError, RecursionError) as error:
        die(
            f"spec is JSON that Python cannot read ({error}); "
            "shorten the number or the nesting"
        )


# The keys the page reads, so a misnamed one fails here instead of vanishing from the
# page. A key that starts with "_" is the author's own (`_about` in the templates, or
# data for a `script`) and passes.
TOP_KEYS = frozenset(
    (
        "title",
        "subtitle",
        "source",
        "context",
        "width",
        "submitLabel",
        "chat",
        "script",
        "style",
        "review",
        "size",
        "questions",
    )
)
QUESTION_KEYS = frozenset(
    (
        "id",
        "header",
        "prompt",
        "hint",
        "context",
        "body",
        "recommendation",
        "mode",
        "min",
        "max",
        "layout",
        "columns",
        "expanded",
        "optional",
        "text",
        "toggle",
        "options",
        "controls",
        "preview",
        "baseline",
    )
)
OPTION_KEYS = frozenset(
    (
        "id",
        "label",
        "subtitle",
        "recommended",
        "badge",
        "tags",
        "pros",
        "cons",
        "detail",
        "preview",
        "default",
        "selected",
        "values",
    )
)
CONTROL_KEYS = frozenset(
    (
        "id",
        "label",
        "type",
        "min",
        "max",
        "step",
        "value",
        "unit",
        "options",
        "on",
        "off",
    )
)
# A label that only counts ("Criterion 3", "Option B", "Step 2") points at text the user
# has to go and find. A bare number or letter can be the answer itself (3 replicas, size
# M), so the counting word is required. The word "story" stays among them: a page an
# agent writes outside Lem may count its user stories so.
POSITION_LABEL = re.compile(
    r"^\s*(?:criterion|story|option|item|task|step|choice|variant|approach|fork|finding|issue|point|"
    r"case|scenario|alternative|proposal|version|question)\s*[#№]?\s*(?:\d+|[a-z])\s*[.):]?\s*$",
    re.IGNORECASE,
)


KEY_PLACES = MappingProxyType(
    {
        "at the top level": TOP_KEYS,
        "on a question": QUESTION_KEYS,
        "on an option": OPTION_KEYS,
        "on a control": CONTROL_KEYS,
    }
)


# The type of each field the page shows or reads as a switch, as (what it is, test). A
# value of another type does not fail on the page: a label of null showed as the
# option's id ("o1"), a prompt of 5 as "5", a mode of "multiple" as options nobody can
# pick. Blocks (context, body, detail, preview) take any block and are not listed.
def _text(text: object) -> bool:
    return isinstance(text, str)


def _flag(flag: object) -> bool:
    return isinstance(flag, bool)


def _count(count: object) -> bool:
    return isinstance(count, int) and not isinstance(count, bool)


def _number(number: object) -> bool:
    return isinstance(number, (int, float)) and not isinstance(number, bool)


def _texts(texts: object) -> bool:
    return isinstance(texts, list) and all(isinstance(line, str) for line in texts)


def _one_of(*words: str) -> tuple[str, Callable[[object], bool]]:
    return (" or ".join(json.dumps(word) for word in words), lambda word: word in words)


TEXT, FLAG, COUNT, NUMBER = (
    ("a string", _text),
    ("true or false", _flag),
    ("a whole number", _count),
    ("a number", _number),
)
TEXTS = ("a list of strings", _texts)
TOP_TYPES = MappingProxyType(
    {
        "title": TEXT,
        "subtitle": TEXT,
        "source": TEXT,
        "submitLabel": TEXT,
        "chat": FLAG,
        "script": TEXT,
        "width": _one_of("narrow"),
        "style": _one_of("refined", "minimal", "bold", "terminal"),
        "review": (
            '"auto", "always", "never", true or false',
            lambda review: (
                isinstance(review, bool) or review in ("auto", "always", "never")
            ),
        ),
    }
)
QUESTION_TYPES = MappingProxyType(
    {
        "header": TEXT,
        "prompt": TEXT,
        "hint": TEXT,
        "recommendation": TEXT,
        "mode": _one_of("single", "multi", "text", "tune"),
        "layout": _one_of("list", "grid", "compare", "inline"),
        "min": COUNT,
        "max": COUNT,
        "columns": COUNT,
        "expanded": FLAG,
        "optional": FLAG,
        "toggle": FLAG,
        "baseline": (
            "true, false or a label",
            lambda label: isinstance(label, (bool, str)),
        ),
        "text": ("false or an object", lambda text: isinstance(text, (bool, dict))),
    }
)
OPTION_TYPES = MappingProxyType(
    {
        "label": TEXT,
        "subtitle": TEXT,
        "badge": TEXT,
        "tags": TEXTS,
        "pros": TEXTS,
        "cons": TEXTS,
        "recommended": (
            "true, false or the reason as a string",
            lambda reason: isinstance(reason, (bool, str)),
        ),
        "default": FLAG,
        "selected": FLAG,
        "values": ("an object", lambda settings: isinstance(settings, dict)),
    }
)
CONTROL_TYPES = MappingProxyType(
    {
        "id": TEXT,
        "label": TEXT,
        "unit": TEXT,
        "min": NUMBER,
        "max": NUMBER,
        "step": NUMBER,
        "options": (
            "a list of strings or numbers",
            lambda options: (
                isinstance(options, list)
                and all(_text(choice) or _number(choice) for choice in options)
            ),
        ),
        "type": _one_of("range", "hue", "color", "select", "toggle"),
    }
)


def check_types(
    node: dict[str, Any],
    types: Mapping[str, tuple[str, Callable[[object], bool]]],
    where: str,
) -> None:
    for key, (what, test) in types.items():
        if key in node and not test(node[key]):
            die(f"{where}: `{key}` must be {what}, got {json.dumps(node[key])}")


def check_keys(
    node: dict[str, Any], allowed: set[str] | frozenset[str], where: str
) -> None:
    unknown = sorted(
        key for key in node if key not in allowed and not key.startswith("_")
    )
    if not unknown:
        return

    def hint(key: str) -> str:
        import difflib

        near = difflib.get_close_matches(key, allowed, n=1)
        if near:
            return f"{key!r} (did you mean {near[0]!r}?)"
        near = difflib.get_close_matches(key, set().union(*KEY_PLACES.values()), n=1)
        if near:
            places = " or ".join(
                place for place, keys in KEY_PLACES.items() if near[0] in keys
            )
            return f"{key!r} (did you mean {near[0]!r}? it belongs {places})"
        return repr(key)

    hints = ", ".join(hint(key) for key in unknown)
    die(f"{where}: unknown key {hints}; the page would drop it without a word")


def says_nothing(option: str | dict[str, Any]) -> bool:
    """An option that is only a counting label: nothing on the page says what it is."""
    label = (
        option
        if isinstance(option, str)
        else str(option.get("label") or option.get("id") or "")
    )
    if not POSITION_LABEL.match(label):
        return False
    if isinstance(option, str):
        return True
    return not (
        option.get("subtitle")
        or option.get("detail")
        or option.get("preview") is not None
        or option.get("pros")
        or option.get("cons")
        or option.get("tags")
        or isinstance(option.get("recommended"), str)
        or option.get("values")
    )


SIZE_WHAT = '"auto", "full" or a whole percent of the session from 1 to 100'
MAX_OPTIONS = 9  # the keys 1-9 pick an option


def size_valid(size: object) -> bool:
    """A panel size is "auto", "full" or a whole percent of 1 to 100."""
    return size in ("auto", "full") or (
        isinstance(size, int) and not isinstance(size, bool) and 1 <= size <= 100  # noqa: PLR2004 - a percent
    )


def size_problem(size: object) -> str | None:
    """What is wrong with a panel size of a spec, or None."""
    return None if size_valid(size) else f"`size` is {SIZE_WHAT}, not {size!r}"


def check_spec(spec: object) -> None:  # noqa: C901, PLR0912 - over the limit before the limit was set
    """The spec's shape, and the type of every field this script reads itself; the page
    reads the rest."""
    if not isinstance(spec, dict):
        die("spec must be a JSON object")
    qs = spec.get("questions", [spec])
    if not isinstance(qs, list) or not qs:
        die("`questions` must be a non-empty list")
    check_keys(
        spec, TOP_KEYS if "questions" in spec else TOP_KEYS | QUESTION_KEYS, "spec"
    )
    check_types(spec, TOP_TYPES, "spec")
    if "size" in spec and (problem := size_problem(spec["size"])):
        die(f"spec: {problem}")
    ids: set[str] = set()
    for position, question in enumerate(qs, start=1):
        if not isinstance(question, dict):
            die(
                f"question {position} must be a JSON object, "
                f"got {type(question).__name__}"
            )
        if question.get("id") is not None and not isinstance(question["id"], str):
            die(
                f"question {position}: `id` must be a string, "
                f"got {json.dumps(question['id'])}"
            )
        qid = question.get("id") or (
            f"q{position}" if spec.get("questions") else "answer"
        )
        if "questions" in spec:
            check_keys(question, QUESTION_KEYS, f"question {qid!r}")
        check_types(question, QUESTION_TYPES, f"question {qid!r}")
        controls = question.get("controls") or []
        if not isinstance(controls, list):
            die(
                f"question {qid!r}: `controls` must be a list of objects, "
                f"got {json.dumps(controls)}"
            )
        for control_number, control in enumerate(controls, start=1):
            if not isinstance(control, dict):
                die(
                    f"question {qid!r}: control {control_number} must be an object "
                    f"with an id, a label and a value, got {json.dumps(control)}"
                )
            check_keys(
                control,
                CONTROL_KEYS,
                f"question {qid!r}, control {control.get('id')!r}",
            )
            check_types(
                control, CONTROL_TYPES, f"question {qid!r}, control {control_number}"
            )
        if qid in ids:
            die(f"duplicate question id {qid!r}")
        ids.add(qid)
        opts = question.get("options") or []
        if not isinstance(opts, list):
            die(f"question {qid!r}: `options` must be a list")
        if len(opts) > MAX_OPTIONS:
            die(
                f"question {qid!r} has {len(opts)} options; "
                "keys 1-9 cover at most 9 (aim for 6)"
            )
        for option_number, option in enumerate(opts, start=1):
            if not isinstance(option, (str, dict)):
                die(
                    f"question {qid!r}: option {option_number} must be "
                    "a string or an object"
                )
            if isinstance(option, dict):
                if option.get("id") is not None and not isinstance(option["id"], str):
                    die(
                        f"question {qid!r}: option {option_number}: "
                        f"`id` must be a string, got {json.dumps(option['id'])}"
                    )
                name = option.get("id") or option_number
                check_keys(option, OPTION_KEYS, f"question {qid!r}, option {name!r}")
                check_types(
                    option, OPTION_TYPES, f"question {qid!r}, option {option_number}"
                )
            if says_nothing(option):
                shown = (
                    option
                    if isinstance(option, str)
                    else option.get("label") or option.get("id")
                )
                die(
                    f"question {qid!r}: option {shown!r} only counts; "
                    "put what the user is choosing on the option itself: "
                    "a label that says it, the gist in `subtitle`, the full text in "
                    '`detail` (or {"md": {"file": …, "lines": '
                    "…}}), with `expanded: true` when the text is what they judge"
                )
        oids = [
            choice if isinstance(choice, str) else choice.get("id") or f"o{number}"
            for number, choice in enumerate(opts, start=1)
        ]  # as the runtime assigns them
        if len(oids) != len(set(oids)):
            die(
                f"question {qid!r} has duplicate option ids (an option without an id "
                "is o1, o2, … by position)"
            )
        if not question.get("prompt") and not spec.get("title"):
            die(f"question {qid!r} has no prompt")


def line_range(spec: object, total: int, path: str) -> tuple[int, int]:
    """`"40-60"`, `"40"` or `[40, 60]` → 1-based inclusive (first, last), checked
    against the file."""
    if isinstance(spec, list) and len(spec) == 2:  # noqa: PLR2004 - [first, last]
        first, last = spec
    else:
        start, _, end = str(spec).partition("-")
        first, last = start, end or start
    try:
        first, last = int(first), int(last)
    except TypeError, ValueError:
        die(f'{path}: lines must look like "40-60", "40" or [40, 60], got {spec!r}')
    if not 1 <= first <= last <= total:
        die(f"{path}: lines {first}-{last} are outside the file's 1-{total}")
    return first, last


def load_files(node: object, base: str) -> None:  # noqa: C901, PLR0912 - over the limit before the limit was set
    """Replace `{"file": …}` in code, diff, md and mermaid blocks with the file's text.

    Source code pasted into JSON by hand is where a spec breaks or a snippet drifts from
    the real file; reading it here shows the user exactly what is on disk."""
    if isinstance(node, list):
        for part in node:
            load_files(part, base)
        return
    if not isinstance(node, dict):
        return
    for kind in SOURCED:
        src = node.get(kind)
        if not (isinstance(src, dict) and "file" in src):
            continue
        shown = src["file"]
        if not isinstance(shown, str) or not shown.strip():
            die(
                f"{kind} block: `file` is the path of a file in quotes, "
                f"got {json.dumps(shown)}"
            )
        path = os.path.expanduser(shown)
        if not Path(path).is_absolute():
            path = os.path.join(base, path)
        try:
            with open(path, encoding="utf-8") as stream:
                text = stream.read()
        except (OSError, UnicodeDecodeError) as error:
            die(f"{kind} block: cannot read {shown}: {error}")
        lines = text.splitlines()
        if kind == "code" and "lines" not in src and len(lines) > CODE_MAX_LINES:
            die(
                f'code block: {shown} has {len(lines)} lines; pass "lines" ("40-62") '
                "for the part the question is about"
            )
        if kind == "code" or "lines" in src:
            first, last = (
                line_range(src["lines"], len(lines), shown)
                if "lines" in src
                else (1, len(lines))
            )
            text = "\n".join(lines[first - 1 : last])
            if kind == "code":
                node.setdefault("start", first)
                node.setdefault(
                    "title", f"{shown}:{first}-{last}" if "lines" in src else shown
                )
                ext = os.path.splitext(path)[1].lstrip(".")
                if ext:
                    node.setdefault("lang", ext)
        node[kind] = text
    for part in node.values():
        load_files(part, base)


def embed_images(node: object, base: str) -> None:
    """Replace local `image` paths with data URIs: a page without --cwd has no
    file access."""
    if isinstance(node, dict):
        for key, part in list(node.items()):
            if (
                key == "image"
                and isinstance(part, str)
                and not part.startswith(("http://", "https://", "data:"))
            ):
                # Path(base, path) is path itself when path is absolute
                path = Path(base, os.path.expanduser(part))
                if not path.is_file():
                    node[key] = ""
                    node.setdefault("alt", f"missing image: {part}")
                    continue
                if path.stat().st_size > MAX_IMAGE:
                    die(f"image too large to embed (>8MB): {part}")
                import base64
                import mimetypes

                mime = mimetypes.guess_type(path)[0] or "image/png"
                with path.open("rb") as stream:
                    encoded = base64.b64encode(stream.read()).decode()
                    node[key] = f"data:{mime};base64,{encoded}"
            else:
                embed_images(part, base)
    elif isinstance(node, list):
        for part in node:
            embed_images(part, base)


# A ```mermaid fence in markdown text, which ask.js draws as a chart, as the board's
# MERMAID_FENCE does.
MERMAID_FENCE = re.compile(r"^[ ]{0,3}(?:`{3,}|~{3,})[ \t]*mermaid\b", re.MULTILINE)


def uses_mermaid(node: object) -> bool:
    """A {"mermaid": …} block, or a mermaid fence in text the page reads as markdown.

    The text of a code or diff block is shown as written, so a fence there needs
    no bundle."""
    if isinstance(node, dict):
        return "mermaid" in node or any(
            uses_mermaid(part)
            for key, part in node.items()
            if key not in ("code", "diff")
        )
    if isinstance(node, list):
        return any(uses_mermaid(part) for part in node)
    if isinstance(node, str):
        return bool(MERMAID_FENCE.search(node))
    return False


# Seconds to wait for the pinned mermaid bundle.
MERMAID_TIMEOUT = 20


def mermaid_js() -> str:
    """The pinned mermaid bundle, verified on every read; "" (diagrams show as source)
    when unavailable."""
    import hashlib
    from http import client
    from urllib import request

    def verified(bundle: bytes) -> bool:
        return hashlib.sha256(bundle).hexdigest() == MERMAID_SHA256

    cache = lem_folder("XDG_CACHE_HOME", ".cache")
    path = os.path.join(cache, MERMAID_NAME)
    try:
        with open(path, "rb") as stream:
            bundle = stream.read()
        if verified(bundle):
            return bundle.decode("utf-8")
        print(
            f"lem ask: {path} fails its sha256 check; fetching it again",
            file=sys.stderr,
        )
    except FileNotFoundError:
        ...
    except OSError as error:
        print(
            f"lem ask: cannot read {path} ({error}); fetching it again",
            file=sys.stderr,
        )
    try:
        with request.urlopen(MERMAID_URL, timeout=MERMAID_TIMEOUT) as stream:
            bundle = stream.read()
    except (OSError, client.HTTPException) as error:
        print(
            f"lem ask: mermaid unavailable ({error}); diagrams show as source",
            file=sys.stderr,
        )
        return ""
    if not verified(bundle):
        print(
            (
                f"lem ask: {MERMAID_URL} does not match its pinned sha256; "
                "not using it, diagrams show as source"
            ),
            file=sys.stderr,
        )
        return ""
    try:
        os.makedirs(cache, exist_ok=True)
        staging = f"{path}.{os.getpid()}.tmp"
        with open(staging, "wb") as out:
            out.write(bundle)
        os.replace(staging, path)
    except (
        OSError
    ) as error:  # the page still gets the verified bundle; only the cache is lost
        print(f"lem ask: cannot cache mermaid ({error})", file=sys.stderr)
    return bundle.decode("utf-8")


# The maximum length of the escaped title in the HTML head.
TITLE_MAX = 120


def build_html(spec: dict[str, Any], base: str) -> str:
    load_files(spec, base)
    embed_images(spec, base)

    def read(name: str) -> str:
        with (RUNTIME / name).open(encoding="utf-8") as stream:
            return stream.read()

    css, js = read("ask.css"), read("ask.js")
    mm = mermaid_js() if uses_mermaid(spec) else ""
    spec_json = (
        json.dumps(spec, ensure_ascii=False)
        .replace("</", r"<\/")
        .replace("<!--", r"<\u0021--")
    )
    title = (
        spec.get("title")
        or (spec.get("questions") or [spec])[0].get("prompt")
        or "Question"
    )

    def esc(text: object) -> str:
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    page_title = esc(title)[:TITLE_MAX]
    mermaid_tag = f"<script>{mm}</script>" if mm else ""
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{page_title}</title><style>{css}</style></head>"
        '<body><div id="app"></div><script type="application/json" '
        f'id="hd-spec">{spec_json}</script>'
        f"{mermaid_tag}<script>{js}</script></body></html>"
    )


def write_page(html: str, *, quiet: bool = False) -> str:
    """Write the page into OUTDIR, under a name that ends in QUIET_PAGE when QUIET (its
    caller leaves the status glyph alone), and give its path."""
    import secrets

    try:
        os.makedirs(OUTDIR, exist_ok=True)
    except OSError as error:
        die(
            f"cannot make the folder for the page, {OUTDIR}: {error}; "
            "point TMPDIR at a folder this user may write"
        )
    now = time.time()
    for old in Path(OUTDIR).glob("*.html"):  # keep a day for debugging
        if old.name.startswith("."):
            # glob.glob's rule, which this followed: a hidden file is none of these
            continue
        try:
            if now - old.stat().st_mtime > PAGE_KEEP:
                old.unlink()
        except OSError:
            ...
    path = os.path.join(
        OUTDIR, f"{time.strftime('%Y%m%d-%H%M%S-')}{secrets.token_hex(3)}"
    )
    path = f"{path}{QUIET_PAGE}" if quiet else f"{path}.html"
    with open(path, "w", encoding="utf-8") as out:
        out.write(html)
    return path


class DefaultsError(Exception):
    """A defaults file, or a folder of Lem's, this script cannot use; the message names
    the file and the fix."""


def lem_folder(env_name: str, fallback: str) -> str:
    """Lem's folder under one base directory of XDG: `$ENV_NAME/lem` when the variable
    is set and not empty, else `~/FALLBACK/lem`. It is the rule of `lem_state.config()`,
    which this script cannot import: it runs alone, on the standard library only. A
    relative path is refused, since it would be read from the folder each command
    starts in."""
    named = os.environ.get(env_name, "")
    if not named:
        return os.path.join(os.path.expanduser("~"), fallback, "lem")
    if not Path(named).is_absolute():
        raise DefaultsError(
            f"{env_name} is {named!r}, a relative path: set it to an absolute path, or "
            f"unset it for ~/{fallback}"
        )
    return os.path.join(named, "lem")


def settings_file() -> str:
    """Lem's settings file of the home folder, whose table [ask] holds the user's
    own defaults."""
    return os.path.join(lem_folder("XDG_CONFIG_HOME", ".config"), "settings.toml")


def shown(path: str) -> str:
    """A file of the home directory as a person writes it, ~/.config/lem/settings.toml;
    another as it is."""
    home = os.path.expanduser("~")
    if path.startswith(home.rstrip(os.sep) + os.sep):
        relative = os.path.relpath(path, home)
        return f"~/{relative}"
    return path


# TOML uses the same separator for arrays and inline tables.
TOML_SEPARATOR = ", "


def toml_text(setting: object) -> str:  # noqa: PLR0911 - over the limit before the limit was set
    """A value as TOML writes it, for a message: json.dumps raises on a date, which
    TOML has."""
    import datetime as dt

    if isinstance(setting, bool):
        return "true" if setting else "false"
    if isinstance(setting, str):
        escaped = setting.replace("\\", r"\\").replace('"', r"\"")
        chars = "".join(
            rf"\u{format(ord(char), '04x')}" if char < " " or char == "\x7f" else char
            for char in escaped
        )
        return f'"{chars}"'
    if isinstance(setting, (int, float)):
        return repr(setting)
    if isinstance(setting, (dt.datetime, dt.date, dt.time)):
        return setting.isoformat()
    if isinstance(setting, list):
        entries = TOML_SEPARATOR.join(toml_text(entry) for entry in setting)
        return f"[{entries}]"
    if isinstance(setting, dict):
        bare = re.compile(r"[A-Za-z0-9_-]+")
        pairs = (
            (key if bare.fullmatch(key) else toml_text(key), entry)
            for key, entry in setting.items()
        )
        entries = TOML_SEPARATOR.join(
            f"{label} = {toml_text(entry)}" for label, entry in pairs
        )
        return f"{{{entries}}}"
    # JSON's null, which only the skill's own defaults.json can hold: TOML has none
    return "null"


def defaults_problem(settings: object) -> str | None:  # noqa: C901, PLR0911 - over the limit before the limit was set
    """What is wrong with the defaults, or None. Each key's type is checked by the
    spec's own rule (TOP_TYPES, size_valid) before its value is used, and a value is
    named as TOML writes it."""
    if not isinstance(settings, dict):
        return f"the defaults are a table of settings, not {toml_text(settings)}"
    for key in settings:
        if key not in ASK_KEYS:
            import difflib

            near = difflib.get_close_matches(key, ASK_KEYS, n=1)
            hint = f" (did you mean `{near[0]}`?)" if near else ""
            keys = ", ".join(ASK_KEYS)
            return f"`{key}` is no key of the defaults{hint}: they are {keys}"
    for key in ("style", "review"):
        what, test = TOP_TYPES[key]
        if key in settings and not test(settings[key]):
            return f"`{key}` is {what}, not {toml_text(settings[key])}"
    if "size" in settings and not size_valid(settings["size"]):
        return f"`size` is {SIZE_WHAT}, not {toml_text(settings['size'])}"
    if "browser" in settings and not isinstance(settings["browser"], bool):
        return f"`browser` is true or false, not {toml_text(settings['browser'])}"
    status = settings.get("status", {})
    if not isinstance(status, dict) or any(name not in STATUS_KEYS for name in status):
        return (
            f"`status` is a table of `asking` and `answered`, not {toml_text(status)}"
        )
    for key, glyph in status.items():
        if (
            not isinstance(glyph, list)
            or not glyph
            or not all(isinstance(word, str) and word for word in glyph)
        ):
            return (
                f"`status.{key}` is a list of the words `agtermctl session status` "
                f'takes, as ["blocked"], not {toml_text(glyph)}'
            )
    return None


def defaults() -> dict[str, Any]:
    """The skill's neutral defaults.json, overlaid by the table [ask] of Lem's home
    settings file. A file that does not read, or a value of the wrong type, is refused:
    a setting dropped without a word would be a page that looks other than its
    owner chose."""
    import tomllib

    try:
        with DEFAULTS.open(encoding="utf-8") as stream:
            merged = json.load(stream)
    except (OSError, ValueError) as error:
        raise DefaultsError(
            f"{DEFAULTS} cannot be read as JSON ({error}); install the plugin again"
        ) from error
    problem = defaults_problem(merged)
    if problem:
        raise DefaultsError(f"{DEFAULTS}: {problem}; install the plugin again")
    path = settings_file()
    try:
        with Path(path).open("rb") as stream:
            whole = tomllib.load(stream)
    except FileNotFoundError:
        return merged
    except OSError as error:
        raise DefaultsError(
            f"{shown(path)} cannot be read ({error.strerror}); "
            "correct the file or remove it"
        ) from error
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise DefaultsError(
            f"{shown(path)} does not read as TOML ({error}); correct the file"
        ) from error
    settings = whole.get("ask", {})
    if not isinstance(settings, dict):
        raise DefaultsError(
            f"{shown(path)}: `ask` is the table [ask], not {toml_text(settings)}; "
            "correct the file"
        )
    problem = defaults_problem(settings)
    if problem:
        raise DefaultsError(
            f"{shown(path)}, under [ask]: {problem}; correct the file or remove the key"
        )
    merged.update(settings)
    return merged


def apply_defaults(spec: dict[str, Any]) -> dict[str, Any]:
    settings = defaults()
    spec.setdefault("style", settings.get("style", "refined"))
    spec.setdefault("review", settings.get("review", "auto"))
    return spec


# The guessed panel percents and the spec length below which a narrow page gets
# the smaller one.
LARGE_PANEL = 90
NARROW_PANEL = 66
NORMAL_PANEL = 78
NARROW_SPEC_MAX = 1500


def auto_size(spec: dict[str, Any]) -> int:
    """Pick the floating-panel percent from how much the page has to show."""
    qs = spec.get("questions") or [spec]
    blob = json.dumps(spec)
    visual = any(
        key in blob
        for key in (
            '"preview"',
            '"mermaid"',
            '"chart"',
            '"image"',
            '"stats"',
            '"table"',
        )
    )
    compare = any(question.get("layout") == "compare" for question in qs)
    nopts = max((len(question.get("options") or []) for question in qs), default=0)
    if visual or compare or len(qs) > 2:  # noqa: PLR2004 - this guess's own bound, read nowhere else
        return LARGE_PANEL
    if spec.get("width") == "narrow" and nopts <= 4 and len(blob) < NARROW_SPEC_MAX:  # noqa: PLR2004 - this guess's own bound, read nowhere else
        return NARROW_PANEL
    return NORMAL_PANEL


# ---------- agterm ----------

# Replies in a row that do not read as JSON before a wait gives agterm up.
UNREADABLE_REPLIES = 5


def agtermctl() -> str | None:
    return (
        os.environ.get("AGTERMCTL")
        or shutil.which("agtermctl")
        or next(
            (
                path
                for path in (
                    "/opt/homebrew/bin/agtermctl",
                    "/Applications/agterm.app/Contents/MacOS/agtermctl",
                )
                if Path(path).exists()
            ),
            None,
        )
    )


def ctl(
    *args: str | None, check: bool = True, timeout: float | None = None
) -> subprocess.CompletedProcess[str]:
    exe = agtermctl()
    cmd = [exe, *args]
    if os.environ.get("AGTERM_SOCKET"):
        cmd += ["--socket", os.environ["AGTERM_SOCKET"]]
    # every caller runs inside agterm (in_agterm()), where agtermctl and the session's
    # id are found
    ran = subprocess.run(
        typing.cast("list[str]", cmd),
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
    if check and ran.returncode not in (0, 2):
        raise RuntimeError(
            (ran.stderr or ran.stdout).strip() or f"agtermctl exited {ran.returncode}"
        )
    return ran


def in_agterm() -> str | bool | None:
    return (
        os.environ.get("AGTERM_ENABLED") == "1"
        and os.environ.get("AGTERM_SESSION_ID")
        and agtermctl()
    )


def unattended() -> bool:
    """Claude Code sets CLAUDE_CODE_SESSION_ATTENDED=0 in `claude -p` runs, which
    inherit AGTERM_ENABLED=1 when started from an agterm shell. A page there waits
    for nobody.

    The variable is undocumented (absent from the env-vars page as of Claude Code
    2.1.296; read from that binary and measured), so only an explicit "0" refuses: if a
    later version drops it, the guard goes quiet rather than blocking
    attended sessions."""
    return os.environ.get("CLAUDE_CODE_SESSION_ATTENDED") == "0"


def status_args(args: list[str]) -> list[str | None]:
    """The arguments of agtermctl that set this session's status to ARGS."""
    sid, pid = os.environ.get("AGTERM_SESSION_ID"), os.environ.get("AGTERM_PANE_ID")
    extra = ["--pane-id", pid] if pid else []
    return ["session", "status", *args, "--target", sid, *extra]


def set_status(args: list[str]) -> None:
    try:
        ctl(*status_args(args), check=False)
    except OSError as error:  # the glyph is a courtesy; never fail the question over it
        print(f"lem ask: could not set the status glyph: {error}", file=sys.stderr)


def this_session(timeout: float | None = None) -> dict[str, Any] | None:
    """This session's node from `agtermctl tree`, or None when agterm cannot say. A
    call past TIMEOUT seconds raises subprocess.TimeoutExpired."""
    args = ["tree", "--json"]
    if os.environ.get("AGTERM_WINDOW_ID"):
        args.extend(["--window", os.environ["AGTERM_WINDOW_ID"]])
    try:
        workspaces = json.loads(ctl(*args, check=False, timeout=timeout).stdout)[
            "result"
        ]["tree"]["workspaces"]
        return next(
            (
                session
                for workspace in workspaces
                for session in workspace.get("sessions") or []
                if session.get("id") == os.environ["AGTERM_SESSION_ID"]
            ),
            None,
        )
    except OSError, json.JSONDecodeError, KeyError, TypeError, AttributeError:
        return None


def pending_page(timeout: float | None = None) -> str | None:
    """The id of a question page open on this session, or None.

    When the overlay slot is taken, the page in it is often this agent's own question,
    left pending by a timeout or a killed call whose output (and page id) is gone
    after compaction."""
    return (pending_overlay(timeout) or {}).get("id")


def pending_overlay(timeout: float | None = None) -> dict[str, Any] | None:
    """agterm's overlay of the question page open on this session (its `id` and its
    `file`), or None."""
    session = this_session(timeout) or {}
    ours = (
        os.path.realpath(OUTDIR) + os.sep
    )  # agterm reports /tmp/… where TMPDIR says /private/tmp/…
    for overlay in session.get("htmlOverlays") or []:
        if overlay.get("file") and os.path.realpath(overlay["file"]).startswith(ours):
            return overlay
    return None


def shown_page(session: dict[str, Any], page_id: str | None = None) -> str | None:
    """The id of the question page of this script that the session node SESSION shows
    (that one, when an id is given), or None."""
    ours = (
        os.path.realpath(OUTDIR) + os.sep
    )  # agterm reports /tmp/… where TMPDIR says /private/tmp/…
    return next(
        (
            overlay.get("id")
            for overlay in session.get("htmlOverlays") or []
            if overlay.get("file")
            and os.path.realpath(overlay["file"]).startswith(ours)
            and page_id in (None, overlay.get("id"))
        ),
        None,
    )


def close_overlay(page: str | None) -> str | None:
    """Close the overlay this session shows, which the caller found to be PAGE; what
    agterm said when it did not close it, else None."""
    ran = ctl(
        "session",
        "overlay",
        "close",
        "--target",
        os.environ["AGTERM_SESSION_ID"],
        "--json",
        check=False,
    )
    try:
        reply = json.loads(ran.stdout)
    except json.JSONDecodeError:
        return (
            ran.stderr or ran.stdout
        ).strip() or f"agtermctl session overlay close exited {ran.returncode}"
    if not reply.get("ok", True) or ran.returncode != 0:
        error = reply.get("error") or (ran.stderr or ran.stdout).strip()
        return f"agterm did not close page {page}: {error}"
    return None


def close_page(page_id: str | None = None) -> None:
    """Close the question page this session shows, the one named when an id is given: a
    card whose answer came from somewhere else (the owner answered it in his inbox), so
    that it asks no more.

    agterm's `session overlay close` closes whatever page the session shows, so it runs
    only while that page is one of this script's: another tool's overlay (a diff review,
    a plan annotation) is not ours to close, and neither is another question than the
    one named. With none of ours open there is nothing to close, which is no error. The
    `lem ask ask` or `wait` that waits on the page then ends as a dismissal (exit 2).

    A card of a task's session ends as `closed` in the task's folder first
    (`lem_cards.end`). When the board's answer is on record already, the close is not
    taken: the page still closes, and the output is the board's answer, exit 0, with a
    `said` line that names both."""
    if not in_agterm():
        die("not inside agterm, so there is no page to close", 3)
    session = this_session()
    if session is None:
        die(
            "agterm did not say what this session shows; "
            "run `agtermctl tree --json` to see why"
        )
    page = shown_page(session, page_id)
    if page is None:
        named = f" with the id {page_id}" if page_id else ""
        emit(
            {
                "status": "gone",
                "pageID": page_id,
                "hint": f"no question page of lem-ask is open on this session{named}: "
                "nothing was closed",
            },
            0,
        )
    card = card_of(page)
    lost = None
    if card is not None:
        won, on_record = card.end("closed")
        lost = None if won else on_record
    error = close_overlay(page)
    if error:
        if lost is None:
            note = (
                ""
                if card is None
                else ": the card's end is on record as closed, "
                "so a pick on it is not taken"
            )
            die(f"{error}{note}")
        print(f"lem ask: {error}", file=sys.stderr)
    if card is not None and lost is not None:
        emit(*card.output(lost, "closed"))
    emit({"status": "closed", "pageID": page}, 0)


def wait_word_file(page_id: str | None) -> Path | None:
    """The file that keeps the word of the last `lem ask wait` on the page PAGE_ID, or
    None for an id that is no plain file name."""
    if not page_id or not re.fullmatch(r"[A-Za-z0-9_-]+", page_id):
        return None
    return Path(OUTDIR, page_id + WAIT_WORD)


def keep_wait_word(page_id: str | None, *, status: bool) -> None:
    """Keep the word of this `lem ask wait` on the page PAGE_ID, status or no status,
    for the Stop hook (`quiet_page`)."""
    kept = wait_word_file(page_id)
    if kept is None:
        return
    try:
        kept.parent.mkdir(parents=True, exist_ok=True)
        kept.write_text("status" if status else "no-status", encoding="utf-8")
    except OSError as error:
        print(
            f"lem ask: the Stop hook may not keep this wait's word on page "
            f"{page_id}: {error}",
            file=sys.stderr,
        )


def quiet_page(shown: dict[str, Any]) -> bool:
    """Whether the caller said --no-status last for the page SHOWN (agterm's overlay,
    its `id` and its `file`): in its last `lem ask wait`, else when it opened it."""
    kept = wait_word_file(shown.get("id"))
    try:
        word = None if kept is None else kept.read_text(encoding="utf-8")
    except OSError:
        word = None
    if word in ("status", "no-status"):
        return word == "no-status"
    return str(shown.get("file")).endswith(QUIET_PAGE)


def hook_stop() -> None:
    """The plugin's Stop hook: when the turn ends with a question page still open, show
    the question.

    Status hooks (agterm's own, or the user's) post a "working" or "done" glyph at Stop,
    and a question waiting in the background, or one left pending by a timeout, would
    read as finished work. agterm already refuses a non-blocked status from the OTHER
    pane while this one is blocked, so only this session's own hooks can paint over it.
    Stop is the moment that is exact: the agent's turn is over and the page is still up.
    Claude Code runs matching hooks in parallel and in no fixed order, so this one
    cannot post last; it runs async (hooks.json) and re-posts the asking status at each
    STOP_RECHECKS offset whenever another hook has posted over it, then stops once the
    page is answered or closed. A Stop hook slower than the last offset still wins. It
    posts with --auto-reset: with no `lem ask wait` left to reset it, the user's visit
    clears it. Each call of agtermctl has STOP_CALL seconds: one that hangs is killed
    then, and the hook ends, so the hook lives at most the last offset and its calls.

    Not covered: Stop does not run when the user interrupts the turn (Escape), so then
    the glyph keeps whatever the last hook posted until the next turn ends; the user who
    pressed Escape is at that session, where the page is. And an async Stop hook
    outlives the next prompt (measured on Claude Code 2.1.296), so a turn that starts
    within the last offset may see asking re-posted over its own status until its next
    tool call; the question is still open then, so that is true.

    A page opened with --no-status (its name ends in QUIET_PAGE), or whose last
    `lem ask wait` said --no-status (WAIT_WORD), keeps that choice: the hook sets no
    status for it. The caller's last word holds: a plain `wait` on a page opened with
    --no-status lets the hook set it again.

    Never prints, never fails: a Stop hook's output or exit 2 could hold the session."""
    try:
        if not in_agterm() or unattended():
            return
        # the hook's JSON input is never read: nothing in it is needed, and a pipe
        # that stays open would keep the read, and the hook, alive
        shown = pending_overlay(STOP_CALL)
        page = (shown or {}).get("id")
        if not page or quiet_page(shown or {}):
            # no page, or one whose `lem ask` was told to leave the glyph alone
            return
        asking = defaults().get("status", {}).get("asking", ["blocked"])
        ours = os.path.realpath(OUTDIR) + os.sep
        started = time.time()
        for at in STOP_RECHECKS:
            time.sleep(max(0, started + at - time.time()))
            session = this_session(STOP_CALL) or {}
            if not any(
                overlay.get("id") == page
                and overlay.get("file")
                and os.path.realpath(overlay["file"]).startswith(ours)
                for overlay in session.get("htmlOverlays") or []
            ):
                return  # answered or closed in the meantime
            if session.get("status") != asking[0]:
                # not set_status, which says on stderr that the call failed
                ctl(
                    *status_args([*asking, "--auto-reset"]),
                    check=False,
                    timeout=STOP_CALL,
                )
    except Exception:  # noqa: BLE001 - a hook must never take the session down with it
        return


# ---------- a card of a task's session ----------


def lem_cards() -> ModuleType:
    """`lem_cards`, the record of a task's cards, from Lem's package."""
    # a run in a task's session reads it, and every answer's text (`submitted`)
    from lem import cards as module

    return module


def task_folder() -> Path | None:
    """The folder of the task this session works on (`LEM_TASK`, which a task's session
    has), when the repository it runs in has that task; else None, and the run keeps
    no card."""
    if not os.environ.get("LEM_TASK"):
        return None
    return lem_cards().task_folder(Path(os.getcwd()), os.environ["LEM_TASK"])


class Card:
    """A card of a task's session: its page and the task's folder that keeps it, whose
    end file says whether it is open and which answer counts (`lem_cards`)."""

    def __init__(self, task: Path, page: str) -> None:
        cards = lem_cards()
        self.task = task
        self.page = page
        self.cards = cards

    def ended(self) -> dict[str, Any] | None:
        try:
            return self.cards.ended(self.task, self.page)
        except self.cards.CardError as error:
            die(str(error))

    def end(
        self, status: str, answer: dict[str, Any] | None = None
    ) -> tuple[bool, dict[str, Any]]:
        """End the card from this session: (True, the record) when this end counts, else
        (False, the end on record)."""
        try:
            return self.cards.end(self.task, self.page, status, "session", answer)
        except (OSError, self.cards.CardError) as error:
            die(
                f"the end of card {self.page} cannot be recorded in {self.task}: "
                f"{error}"
            )

    def output(
        self, on_record: dict[str, Any], mine: dict[str, Any] | str | None = None
    ) -> tuple[dict[str, Any], int]:
        """What this run prints for the end on record, and its exit code: the answer on
        record as the card's own answer, with `from`, else a dismissal (exit 2). MINE is
        this session's own end that came after it, an answer or "dismissed" or "closed",
        which `said` names as not taken."""
        if on_record.get("status") == "answered":
            out = dict(on_record.get("answer") or {})
            out.update({"pageID": self.page, "from": on_record.get("from")})
            out.update(
                {key: on_record[key] for key in ("via", "device") if key in on_record}
            )
            code = 0
        else:
            out, code = {"status": "dismissed", "pageID": self.page}, 2
        took = self.cards.took_effect(on_record)
        if isinstance(mine, dict):
            words = self.cards.words(mine)
            said = (
                "Two answers came before the session read either, and the one recorded "
                f"first counts: {took}; {words} on the card in the "
                "session was not taken."
            )
        elif mine in ("dismissed", "closed"):
            action = "dismissal" if mine == "dismissed" else "close"
            said = (
                f"{took}, and it counts; the card's "
                f"{action} in the session "
                "came after it and was not taken."
            )
        else:
            said = f"{took}."
        out["said"] = said[:1].upper() + said[1:]
        return out, code


def card_of(page: str | None) -> Card | None:
    """The card PAGE of the task this session works on, or None when its folder keeps no
    such card."""
    task = task_folder()
    if task is None or not page:
        return None
    try:
        return None if lem_cards().card(task, page) is None else Card(task, page)
    except lem_cards().CardError:
        return None


def keep_card(path: str, page: str | None, spec: dict[str, Any]) -> Card | None:
    """Keep the card PAGE, whose page agterm shows from PATH, in the folder of the task
    this session works on, when there is one: the board reads it there. A card that
    cannot be kept is said on stderr and still waits for its answer in the session."""
    task = task_folder()
    if task is None or not page:
        return None
    cards = lem_cards()
    try:
        with open(path, "rb") as stream:
            cards.keep(
                task, page, stream.read(), spec, os.environ.get("AGTERM_SESSION_ID")
            )
    except (OSError, cards.CardError) as error:
        print(
            (
                f"lem ask: the card {page} is not kept in {task}, "
                f"so the board does not show it: {error}"
            ),
            file=sys.stderr,
        )
        return None
    return Card(task, page)


def submitted(payload: str | None) -> dict[str, Any]:
    """The answer a page sent as PAYLOAD: the object it is as JSON; a value that is no
    JSON, or JSON that is no object (what a spec's own script may send through
    `window.lemAsk.send`), is its text, as one answer. The page's runtime sends every
    value as JSON, so a JSON string's text is the string, without its quotes; a number,
    a list, `null` or `true` keeps its JSON text. Half of a character that a page's
    script cut in two is U+FFFD (`lem_cards.whole`), so the answer prints as UTF-8.
    JSON that Python cannot hold (a number of more digits than
    `sys.get_int_max_str_digits()`, nesting deeper than the stack) is no JSON to it,
    so it is its text too."""
    try:
        given = json.loads(payload or "{}")
        if isinstance(given, dict):
            return typing.cast("dict[str, Any]", lem_cards().whole(given))
    except ValueError, RecursionError:  # JSONDecodeError is a ValueError
        given = None
    text = given if isinstance(given, str) else payload
    return {
        "status": "answered",
        "answers": {
            "answer": {"selected": [], "labels": [], "text": lem_cards().whole(text)}
        },
    }


def peek(page_id: str | None) -> dict[str, Any] | str | None:
    """agterm's outcome of the page in one read, never an error: an answer, "dismissed",
    or None."""
    ran = ctl("session", "overlay", "result", "--page", page_id, "--json", check=False)
    try:
        outcome = json.loads(ran.stdout).get("result", {}).get("pageOutcome", {})
        if outcome.get("outcome") == "submitted":
            return submitted(outcome.get("value"))
    except json.JSONDecodeError, AttributeError:
        return None
    return "dismissed" if outcome.get("outcome") == "dismissed" else None


def close_after_board(page_id: str | None) -> None:
    """Close this session's own page of a card the board answered, while it is
    still shown."""
    session = this_session()
    if session is None or not shown_page(session, page_id):
        return
    error = close_overlay(page_id)
    if error:
        print(
            f"lem ask: the board's answer counts, and the page stays up: {error}",
            file=sys.stderr,
        )


def open_overlay(
    path: str, flags: argparse.Namespace, spec: dict[str, Any]
) -> str | None:
    args = [
        "session",
        "overlay",
        "open",
        "--html",
        path,
        "--js",
        "--target",
        os.environ["AGTERM_SESSION_ID"],
        "--json",
    ]
    if flags.follow:
        args.append("--follow")
    size = flags.size or spec.get("size") or defaults().get("size", "auto")
    if flags.full or size == "full":
        size = None
    elif size == "auto":
        size = auto_size(spec)
    if size:
        args += ["--size-percent", str(int(size))]
    if flags.chromeless:
        args.append("--chromeless")
    ran = ctl(*args, check=False)
    try:
        reply = json.loads(ran.stdout)
    except json.JSONDecodeError:
        die((ran.stderr or ran.stdout).strip() or "overlay open failed")
    if not reply.get("ok", True) or ran.returncode != 0:
        err = reply.get("error") or (ran.stderr or ran.stdout).strip()
        if err == "overlay already open":
            page = pending_page()
            if page:
                emit(
                    {
                        "status": "busy",
                        "error": err,
                        "pageID": page,
                        "hint": (
                            "a question page is still open on this session, most "
                            "likely your own unanswered question: "
                            f"run `lem ask wait {page}` for its answer "
                            "before asking anything new"
                        ),
                    },
                    5,
                )
            emit(
                {
                    "status": "busy",
                    "error": err,
                    "hint": (
                        "another tool's overlay is open on this session (a diff "
                        "review, a plan annotation); ask in the terminal instead, and "
                        "do not close an overlay you did not open"
                    ),
                },
                5,
            )
        die(err)
    res = reply.get("result", reply)
    return res.get("pageID") or res.get("id")


# Seconds between reads of an overlay's outcome.
OVERLAY_POLL = 0.4


def wait_page(  # noqa: C901, PLR0912, PLR0915 - over the limit before the limit was set
    page_id: str | None,
    timeout: float,
    *,
    status: bool = True,
    card: Card | None = None,
) -> int | None:
    """Wait for the page's answer. A CARD of a task's session (`Card`) ends once: each
    poll, the first too, reads its end file, and an end on record (the board's answer,
    or an earlier end in the session) is the output; a pick or a dismissal here links
    the end file first, and when another end was there already, that end is the output
    and this one is not taken."""
    deadline = time.time() + timeout
    glyphs = defaults().get("status", {})
    asking = glyphs.get("asking", ["blocked"])
    if status:
        set_status(asking)
    still_open = False
    unreadable = 0
    try:
        while True:
            on_record = None if card is None else card.ended()
            if card is not None and on_record is not None:
                mine = peek(page_id) if on_record.get("from") == "board" else None
                if (
                    on_record.get("status") == "answered"
                    and on_record.get("from") == "board"
                ):
                    close_after_board(page_id)
                out, code = card.output(
                    on_record, mine if isinstance(mine, dict) else None
                )
                print(json.dumps(out, ensure_ascii=False, indent=1))
                return code
            ran = ctl(
                "session", "overlay", "result", "--page", page_id, "--json", check=False
            )
            try:
                reply = json.loads(ran.stdout)
            except (
                json.JSONDecodeError
            ):  # agterm did not answer at all: a stopped app, a missing socket
                unreadable += 1
                if unreadable >= UNREADABLE_REPLIES:
                    error = (ran.stderr or ran.stdout).strip()
                    die(f"agterm stopped answering about page {page_id}: {error}")
                time.sleep(OVERLAY_POLL)
                continue
            unreadable = 0
            if not reply.get(
                "ok", True
            ):  # `no such page`, `invalid page id`: waiting longer cannot help
                error = reply.get("error") or "agterm refused the result request"
                die(f"page {page_id}: {error}")
            outcome = reply.get("result", {}).get("pageOutcome", {})
            out = outcome.get("outcome")
            if out == "submitted":
                ans = submitted(outcome.get("value"))
                if card is not None:
                    won, on_record = card.end("answered", ans)
                    if not won:
                        out, code = card.output(on_record, ans)
                        print(json.dumps(out, ensure_ascii=False, indent=1))
                        return code
                    ans["from"] = "session"
                ans["pageID"] = page_id
                print(json.dumps(ans, ensure_ascii=False, indent=1))
                return 0
            if out == "dismissed":
                if card is not None:
                    won, on_record = card.end("dismissed")
                    if not won:
                        out, code = card.output(on_record, "dismissed")
                        print(json.dumps(out, ensure_ascii=False, indent=1))
                        return code
                print(json.dumps({"status": "dismissed", "pageID": page_id}))
                return 2
            if time.time() > deadline:
                still_open = True  # the question is still up: keep the "asking" glyph
                # but let a visit clear it: with no waiter left, nothing else would
                # after a ⌘W
                if status:
                    set_status([*asking, "--auto-reset"])
                print(
                    json.dumps(
                        {
                            "status": "pending",
                            "pageID": page_id,
                            "hint": (
                                f"still open; run `lem ask wait {page_id}` to keep "
                                "waiting"
                            ),
                        }
                    )
                )
                return 4
            time.sleep(OVERLAY_POLL)
    finally:
        if status and not still_open:
            set_status(glyphs.get("answered", ["active"]))


# ---------- browser fallback ----------

RELOAD_GRACE = (
    3  # seconds a dismissal waits for the page to come back (a reload also unloads it)
)
# Seconds between checks for a browser dismissal or timeout.
BROWSER_POLL = 0.25
# The page GET returns HTML; a POST acknowledges the answer without a body.
PAGE_OK = 200
ANSWER_NO_CONTENT = 204


def ask_in_browser(html: str, timeout: float) -> int:
    import socketserver
    import threading
    import webbrowser
    from http import server

    state: dict[str, Any] = {"answer": None, "dismissed_at": None}
    done = threading.Event()

    class PageHandler(server.BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - the base class names it so
            ...

        def do_GET(self) -> None:
            state["dismissed_at"] = None  # the page is back: that unload was a reload
            body = html.encode()
            self.send_response(PAGE_OK)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            length = int(self.headers.get("content-length", 0))
            body = submitted(self.rfile.read(length).decode("utf-8", errors="replace"))
            self.send_response(ANSWER_NO_CONTENT)
            self.end_headers()
            if body.get("status") == "dismissed":
                state["dismissed_at"] = time.time()
            else:
                state["answer"] = body
                done.set()

    srv = socketserver.TCPServer(("127.0.0.1", 0), PageHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    if not webbrowser.open(url):
        srv.shutdown()
        die("not inside agterm and no browser could be opened", 3)
    print(f"lem ask: opened {url}", file=sys.stderr)
    deadline = time.time() + timeout
    while not done.wait(BROWSER_POLL):
        gone = state["dismissed_at"]
        if gone and time.time() - gone > RELOAD_GRACE:
            srv.shutdown()
            print(json.dumps({"status": "dismissed"}))
            return 2
        if (
            time.time() > deadline
        ):  # the server is gone with this process, so it cannot be resumed
            srv.shutdown()
            print(
                json.dumps(
                    {
                        "status": "timeout",
                        "hint": (
                            "browser questions cannot be resumed; "
                            "ask again with a longer --timeout"
                        ),
                    }
                )
            )
            return 4
    srv.shutdown()
    print(json.dumps(state["answer"], ensure_ascii=False, indent=1))
    return 0


# ---------- commands ----------


def ask(spec: dict[str, Any], args: argparse.Namespace, base: str) -> int | None:
    check_spec(spec)
    if unattended():
        emit(
            {
                "status": "unattended",
                "error": (
                    "this is an unattended run (CLAUDE_CODE_SESSION_ATTENDED=0); "
                    "nobody is there to answer"
                ),
                "hint": (
                    "do not ask: proceed on the documented default, "
                    "or stop and report what you need decided"
                ),
            },
            3,
        )
    # Outside agterm the browser is opt-in: the skill tells the agent to just run
    # `lem ask` rather than check for agterm first, so an unasked-for browser tab must
    # not be what happens in a plain terminal.
    browser = args.browser or (not in_agterm() and defaults().get("browser") is True)
    if not in_agterm() and not browser:
        where = shown(settings_file())
        emit(
            {
                "status": "no-agterm",
                "error": (
                    "not inside agterm, so there is no overlay to show the page in"
                ),
                "hint": (
                    "ask in the terminal; --browser, or `browser = true` under [ask] "
                    f"in {where}, opens the page "
                    "in the browser instead"
                ),
            },
            3,
        )
    apply_defaults(spec)
    if args.style:
        spec["style"] = args.style
    if args.review:
        spec["review"] = args.review
    html = build_html(spec, base)
    if browser:
        if args.no_wait:
            die(
                "--no-wait needs agterm: the browser fallback answers only "
                "while this process runs"
            )
        return ask_in_browser(html, args.timeout)
    path = write_page(html, quiet=args.no_status)
    page = open_overlay(path, args, spec)
    card = keep_card(path, page, spec)
    if args.no_wait:
        print(json.dumps({"status": "open", "pageID": page, "file": path}))
        return 0
    return wait_page(page, args.timeout, status=not args.no_status, card=card)


def quick_spec(args: argparse.Namespace) -> dict[str, Any]:
    opts = []
    for position, raw in enumerate(args.options, start=1):
        rec = raw.startswith("*")
        label, _, rest = raw.lstrip("*").partition("|")
        sub, _, why = rest.partition("|")
        option: dict[str, str | bool] = {"id": f"o{position}", "label": label.strip()}
        if sub.strip():
            option["subtitle"] = sub.strip()
        if rec:
            option["recommended"] = why.strip() or True
        opts.append(option)
    spec: dict[str, Any] = {"prompt": args.prompt, "options": opts}
    if args.multi:
        spec["mode"] = "multi"
    if args.context:
        spec["context"] = args.context
    if args.title:
        spec["title"] = args.title
    if opts:
        spec["width"] = "narrow"
    # a byte of argv that is no UTF-8 reads as half of a pair: U+FFFD, as in a spec
    return typing.cast("dict[str, Any]", lem_cards().whole(spec))


def list_dir(folder: Path) -> list[tuple[str, str]]:
    rows = []
    for path in sorted(folder.glob("*.json")):
        if path.name.startswith("."):
            # glob.glob's rule, which this followed: a hidden file is no template
            continue
        try:
            with path.open(encoding="utf-8") as stream:
                spec = json.load(stream)
            rows.append((path.name[:-5], spec.get("_about", "")))
        except (OSError, json.JSONDecodeError) as error:
            rows.append((path.name[:-5], f"(unreadable: {error})"))
    return rows


# Seconds to wait by default, below the Bash tool's 600-second limit.
DEFAULT_TIMEOUT = 570


def main() -> None:  # noqa: C901, PLR0912, PLR0915 - over the limit before the limit was set
    if sys.argv[1:] == ["hook-stop"]:
        # answered before the command line is read: the hook loads no argparse
        hook_stop()
        sys.exit(0)
    import argparse

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--follow",
        action="store_true",
        help="select this session so the user sees it now",
    )
    common.add_argument(
        "--size",
        type=int,
        help="floating panel, percent of the session (1-100); default auto",
    )
    common.add_argument(
        "--full",
        action="store_true",
        help="cover the whole session instead of a floating panel",
    )
    common.add_argument(
        "--style",
        choices=["refined", "minimal", "bold", "terminal"],
        help=(
            "visual style (default: style under [ask] in ~/.config/lem/settings.toml, "
            "else refined)"
        ),
    )
    common.add_argument(
        "--review",
        choices=["auto", "always", "never"],
        help="show the answer review before sending",
    )
    common.add_argument(
        "--chromeless", action="store_true", help="hide the overlay's title strip"
    )
    common.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="seconds to wait (default 570)",
    )
    common.add_argument(
        "--no-wait",
        action="store_true",
        help="open and print the page id; read it later with `lem ask wait`",
    )
    common.add_argument(
        "--no-status", action="store_true", help="leave the sidebar status glyph alone"
    )
    common.add_argument(
        "--browser",
        action="store_true",
        help=(
            "open the page in the local browser: outside agterm, "
            "or instead of the overlay"
        ),
    )

    argv = sys.argv[1:]
    sub = (
        argv[0]
        if argv
        and argv[0]
        in ("q", "wait", "close", "demo", "templates", "render", "ask", "hook-stop")
        else None
    )
    if sub is None:
        argv = ["ask", *argv]
        sub = "ask"

    parser = argparse.ArgumentParser(
        prog="lem ask",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sp = parser.add_subparsers(dest="cmd")
    s_ask = sp.add_parser("ask", parents=[common])
    s_ask.add_argument("spec", nargs="?")
    s_q = sp.add_parser("q", parents=[common])
    s_q.add_argument("prompt")
    s_q.add_argument("options", nargs="*")
    s_q.add_argument("--multi", action="store_true")
    s_q.add_argument("--context")
    s_q.add_argument("--title")
    s_w = sp.add_parser("wait", parents=[common])
    s_w.add_argument("page_id")
    s_c = sp.add_parser("close")
    s_c.add_argument("page_id", nargs="?")
    s_d = sp.add_parser("demo", parents=[common])
    s_d.add_argument("names", nargs="*")
    sp.add_parser("templates")
    s_r = sp.add_parser("render")
    s_r.add_argument("spec")
    s_r.add_argument("-o", "--out", required=True)
    sp.add_parser("hook-stop")
    args = parser.parse_args(argv)

    if args.cmd == "ask":
        base = (
            str(Path.cwd())
            if args.spec in (None, "-")
            else str(Path(os.path.abspath(args.spec)).parent)
        )
        sys.exit(ask(load_spec(args.spec), args, base))
    if args.cmd == "q":
        sys.exit(ask(quick_spec(args), args, str(Path.cwd())))
    if args.cmd == "wait":
        if not in_agterm():
            die("not inside agterm", 3)
        keep_wait_word(args.page_id, status=not args.no_status)
        sys.exit(
            wait_page(
                args.page_id,
                args.timeout,
                status=not args.no_status,
                card=card_of(args.page_id),
            )
        )
    if args.cmd == "close":
        close_page(args.page_id)
    if args.cmd == "templates":
        for name, about in list_dir(TEMPLATES):
            print(f"{name:<18} {about}")
        print(f"\n{TEMPLATES}")
        return
    if args.cmd == "demo":
        if not args.names:
            for name, about in list_dir(DEMOS) + list_dir(TEMPLATES):
                print(f"{name:<18} {about}")
            return
        code = 0
        for name in args.names:
            path = next(
                (
                    os.path.join(folder, f"{name}.json")
                    for folder in (DEMOS, TEMPLATES)
                    if (folder / f"{name}.json").is_file()
                ),
                None,
            )
            if not path:
                die(f"no demo or template named {name!r}")
            code = ask(load_spec(path), args, os.path.dirname(path))
            if code not in (0, 2):
                break
        sys.exit(code)
    if args.cmd == "render":
        spec = load_spec(args.spec)
        check_spec(spec)
        apply_defaults(spec)
        base = (
            str(Path.cwd())
            if args.spec == "-"
            else str(Path(os.path.abspath(args.spec)).parent)
        )
        html = build_html(spec, base)
        try:
            with open(args.out, "w", encoding="utf-8") as out:
                out.write(html)
        except OSError as error:
            die(f"cannot write the page to {args.out}: {error}")
        print(args.out)


if __name__ == "__main__":
    try:
        main()
    except DefaultsError as error:
        die(str(error))
