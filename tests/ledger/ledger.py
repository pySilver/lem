#!/usr/bin/env python3
"""Make the rebuild ledger from a fixed Lem commit and the hand-kept rows."""

import argparse
import ast
from collections import Counter
import csv
from dataclasses import dataclass, fields
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
from tempfile import TemporaryDirectory


HERE = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Row:
    id: str
    kind: str
    source: str
    what: str
    fate: str = ""
    proof: str = ""
    note: str = ""


HEADER = [field.name for field in fields(Row)]


def words(text):
    return re.sub(r"[ \t\r\n]+", " ", text).strip()


def text_id(text):
    # A readable prefix for a long natural-language name, plus its full-text identity.
    label = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:44].rstrip("-")
    return f"{label or 'text'}-{sha256(text.encode()).hexdigest()[:16]}"


class Ledger:
    def __init__(self, root, source_notes):
        self.root = root
        self.source_notes = source_notes
        self.rows = {}
        self.sources = {}

    def read(self, file):
        return (self.root / file).read_text(encoding="utf-8")

    def tree(self, file):
        return ast.parse(self.read(file), filename=file)

    def files(self, pattern):
        return sorted(
            path.relative_to(self.root).as_posix()
            for path in self.root.glob(pattern)
            if path.is_file()
        )

    def track(self, kind, file):
        self.sources.setdefault(kind, Counter())[file] += 0

    def add(self, kind, key, file, what, *, section="", source_note=""):
        identity = f"{kind}:{key}"
        if identity in self.rows:
            raise ValueError(f"Duplicate row {identity} in {file}: {what}")
        self.track(kind, file)
        self.sources[kind][file] += 1
        source = f"{file} — {section}" if section else file
        note = source_note if self.source_notes else ""
        self.rows[identity] = Row(identity, kind, source, words(what), note=note)


def literal(tree, name):
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                return ast.literal_eval(node.value)
    raise ValueError(f"Missing assignment for {name}")


def units(ledger):
    def classes(body, prefix=""):
        for node in body:
            if isinstance(node, ast.ClassDef):
                name = prefix + node.name
                yield name, node
                yield from classes(node.body, name + ".")

    for file in ledger.files("tests/unit/test_*.py"):
        ledger.track("unit", file)
        for name, node in classes(ledger.tree(file).body):
            bases = [ast.unparse(base) for base in node.bases]
            plain = bases in (["TestCase"], ["unittest.TestCase"])
            for method in node.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if method.name.startswith("test"):
                        label = f"{name}.{method.name}"
                        note = "Bases: " + ", ".join(bases or ["(none)"])
                        ledger.add("unit", f"{file}:{label}", file, label,
                                   source_note="" if plain else note)


# In Bash double quotes, backslash quotes these characters. Nested command
# substitutions in a check label can have double quotes of their own.
def check_text(line, start):
    result = []
    contexts = []
    index = start
    while index < len(line):
        char = line[index]
        following = line[index + 1:index + 2]
        if char == "\\":
            if following in ('"', "$", "`", "\\") and not contexts:
                result.append(following)
            else:
                result.append(char + following)
            index += 2
            continue
        if char == '"' and not contexts:
            return "".join(result)
        if char == "$" and following == "(" and (not contexts or contexts[-1] != "'"):
            contexts.append("(")
            result.append("$(")
            index += 2
            continue
        if contexts:
            if char == contexts[-1] and char in ("'", '"'):
                contexts.pop()
            elif contexts[-1] == "(":
                if char in ("'", '"', "("):
                    contexts.append(char)
                elif char == ")":
                    contexts.pop()
        result.append(char)
        index += 1
    raise ValueError(f"No closing quote in check: {line}")


def checks(ledger):
    source = "tests/checks.sh"
    rule, = re.findall(r"^CHECK_SITE='([^']+)'$", ledger.read(source), re.M)
    # grep -cE counts matching lines. Translate the POSIX space class for
    # Python and read each input line independently, as grep does.
    rule = re.compile(rule.replace("[[:space:]]", r"[ \t\r\f\v]"))
    for file in ledger.files("tests/*.sh"):
        ledger.track("check", file)
        helper = ""
        body = ledger.read(file)
        loop_notes = check_loop_notes(ledger, file, body)
        for line in body.split("\n"):
            function = re.match(r"^(\w+)\(\)\s*\{", line)
            if function:
                helper = function[1]
            site = rule.search(line)
            if site is not None:
                label = check_text(line, site.end())
                # Two helpers can emit the same variable. Their function names
                # distinguish the sites even when their order changes.
                scope = helper if re.fullmatch(r"\$[1-9a-zA-Z_][\w]*", label) else ""
                key = ":".join(part for part in (file, scope, text_id(label)) if part)
                ledger.add("check", key, file, label,
                           source_note=loop_notes.get(scope or label, ""))
            if re.match(r"^}\s*(?:#.*)?$", line):
                helper = ""


def check_loop_notes(ledger, file, body):
    if file == "tests/shellcheck.sh":
        total = len(ledger.files("tests/*.sh"))
        return {"shellcheck $file": f"${{#files[@]}} results, {total} by default"}
    if file != "tests/test-ask.sh":
        return {}

    notes = {
        "expect": "One result per literal bad, expect or stub call in helpers",
        "refuses": "One result per literal refuses call in helpers",
        "card": "One result per literal card call in helpers",
        "check": "One result per literal check call in helpers",
    }
    called = Counter(re.findall(r'^\s*(bad|expect|refuses|check|stub|card) "[^$]',
                                body, re.M))
    called["expect"] += called["bad"] + called["stub"]
    for helper, description in notes.items():
        notes[helper] = f"{called[helper]} results. {description}."

    specs = sum(len(ledger.files(f"skills/lem-ask/{folder}/*.json"))
                for folder in ("templates", "demos"))
    notes["render $n"] = f"{specs} results (${{#specs[@]}}), one per template and demo"
    scenarios = re.search(r"^for scenario in (.+); do$", body, re.M)
    if scenarios:
        label = ("wait gives a JSON value that is no object the form of a value "
                 "that is no JSON: its text, as one answer")
        notes[label] = f"One result for the aggregate of {len(scenarios[1].split())} scenarios"
    before_pages = body.split("pages=()", 1)[0]
    md_cases = re.search(r"^cases = (\{\n.*?^\})", before_pages, re.M | re.S)
    if md_cases:
        markdown = len(ast.literal_eval(md_cases[1]))
        notes["$why"] = f"{markdown} results (${{#mdnames[@]}}), one per name in MDNAMES"
        # The malformed or refused renders do not add pages to the successful run.
        fixed = set(re.findall(r' -o "\$WORK/([\w-]+)\.html"', before_pages))
        fixed -= {"bad", "plain"}
        total = specs + markdown + len(fixed)
        notes["page loads: $n"] = (
            f"{total} results (${{#pages[@]}}) when the renders succeed, "
            "one per generated HTML page except bad.html"
        )
    return notes


def rulings(ledger):
    for file in ("docs/rulings/rulings.md", "docs/rulings/history.md"):
        heading = ""
        bullet = []

        def add():
            if not bullet:
                return
            bold = re.match(r"\*\*(.+?)\*\*", words(" ".join(bullet)))
            if not bold:
                raise ValueError(f"Ruling has no bold name in {file}: {bullet[0]}")
            title = bold[1]
            section = heading
            if file.endswith("/history.md"):
                # Keep the cited tests and places with the row so owners.py
                # can resolve the ruling without opening the old checkout.
                section += " — " + words(" ".join(bullet))[bold.end():].strip()
            ledger.add("ruling", text_id(title), file, title, section=section)

        for line in ledger.read(file).splitlines():
            if line.startswith(("- ", "* ", "+ ", "#")) or not line.strip():
                add()
                bullet = []
            if line.startswith("## "):
                heading = line[3:].strip()
            elif line.startswith(("- ", "* ", "+ ")):
                bullet = [line[2:]]
            elif bullet:
                bullet.append(line)
        add()


def commands(ledger):
    file = "tests/unit/commands.json"

    def visit(name, shape):
        detail = {key: value for key, value in shape.items() if key != "subcommands"}
        contract = json.dumps(detail, ensure_ascii=False, sort_keys=True)
        ledger.add("command", name, file, f"{name} {contract}")
        for child, spec in shape.get("subcommands", {}).items():
            visit(f"{name} {child}", spec)

    for name, shape in json.loads(ledger.read(file))["commands"].items():
        visit("lem " + name, shape)


def settings(ledger):
    file = "docs/settings.md"
    headings = {}
    previous = ""
    columns = ""
    for line in ledger.read(file).splitlines():
        heading = re.match(r"^(#+) (.+)", line)
        if heading:
            level = len(heading[1])
            headings = {k: v for k, v in headings.items() if k < level}
            headings[level] = heading[2]
        if line.startswith("|"):
            if re.fullmatch(r"\|(?:\s*:?-+:?\s*\|)+", line):
                table = tuple(headings.values())[1:]
                columns = previous
            elif previous.startswith("|") and columns:
                name = line.split("|", 2)[1].strip()
                key = "/".join((*table, name))
                ledger.add("setting", key, file, line,
                           section=" / ".join((*table, columns.split("|")[1].strip())))
            else:
                columns = ""
        previous = line


def hooks(ledger):
    file = "hooks/hooks.json"
    for event, groups in json.loads(ledger.read(file))["hooks"].items():
        for group in groups:
            matcher = group.get("matcher", "")
            for hook in group["hooks"]:
                command = hook["command"]
                key = f"{event}:{matcher}:{text_id(command)}"
                details = ", ".join(f"{k}={json.dumps(v)}" for k, v in hook.items()
                                    if k not in ("command", "type"))
                ledger.add("hook", key, file,
                           f"{event} ({matcher or 'any matcher'}): {command}"
                           + (f" [{details}]" if details else ""))


def reading(ledger):
    patterns = ["skills/lem/" + folder + "/**/*"
                for folder in ("stages", "prompts", "templates", "harness")]
    for file in sorted({file for pattern in (*patterns, "agents/**/*", "skills/**/SKILL.md")
                        for file in ledger.files(pattern)}):
        ledger.add("text", file, file, file)
    docs = [file for file in ledger.files("docs/**/*")
            if Path(file).parts[1] not in {"plans", "backlog", "rulings"}]
    for file in ("README.md", *docs, "site/index.html"):
        (ledger.root / file).stat()
        ledger.add("guide", file, file, file)


def routes(ledger):
    file = "src/lem/serve.py"
    tree = ledger.tree(file)
    workspace = "/{host}/{workspace}"
    task = workspace + "/tasks/{slug}"

    def add(method, path, handler, *, detail=""):
        label = f"{method} {path}"
        ledger.add("route", label, file, label + (f" — {detail}" if detail else ""),
                   section=handler, source_note=handler)

    reads = [
        ("/", "Handler.answer → board_pages.index_page", "Workspace index or redirect"),
        ("/api/workspaces", "Handler.answer → Handler.spaces", ""),
        ("/api/server", "Handler.answer", ""),
        ("/sw.js", "Handler.push_read", "Service worker"),
        ("/api/push/key", "Handler.push_read → push.machine_key", ""),
        ("/api/push/latest", "Handler.push_read → push.latest", ""),
        ("/manifest.webmanifest", "Handler.answer → board_pages.manifest", ""),
        ("/assets/{asset}", "Handler.answer", ""),
        ("/{host}/assets/{asset}", "Handler.answer", ""),
        ("/{peer}/{rest...}", "Handler.forwarded → peers.forward",
         "Joined machine. The remainder can be empty."),
        ("/{alias}/{rest...}", "Handler.answer",
         "Redirect the local host alias. The remainder can be empty."),
        ("/{workspace}[/{rest...}]", "Handler.answer",
         "Redirect an old address to the local host. Unknown views go to Tasks."),
        (workspace, "Handler.answer", "Redirect to the address with a final slash"),
        (workspace + "/stream", "Handler.refreshes", "Workspace event stream"),
        (task, "Handler.task → board_task.overview_tab", "Default task tab"),
        (task + "/artifacts/{path...}", "Handler.task → board_task.artifacts_tab", ""),
        (task + "/raw/{path...}", "Handler.raw", "HTML artifact"),
        (task + "/media/{path...}", "Handler.media", "Task image"),
        (task + "/cards/{page}", "Handler.card_page", "Redirect to the card with a final slash"),
        (task + "/cards/{page}/", "Handler.card_page", "The question card itself"),
        (task + "/card/{page}", "Handler.task → board_task.card_step", "Board panel for a card"),
    ]
    for view, handler in literal(tree, "PAGES").items():
        reads.append((workspace + "/" + view, f"Handler.page → board_pages.{handler}", ""))
    task_tree = ledger.tree("src/lem/board_task.py")
    tabs = {name: name + "_tab" for name, _ in literal(task_tree, "TABS")}
    tabs.update({name: name + "_step" for name in literal(task_tree, "ACT_TABS")})
    for tab, handler in tabs.items():
        reads.append((f"{task}/{tab}", f"Handler.task → board_task.{handler}", ""))
    for method in ("GET", "HEAD"):
        for path, handler, detail in reads:
            if method == "HEAD" and path == workspace + "/stream":
                handler = "Handler.in_workspace"
            add(method, path, handler, detail=detail)

    add("POST", "/api/server/stop", "Handler.act → stop_all", detail="Local listener")
    for act in literal(tree, "PUSH_ACTS"):
        add("POST", f"/api/push/{act}", "Handler.push_act")
    for act in literal(tree, "AGTERM_ACTS"):
        add("POST", f"{workspace}/agterm/{act}", "Handler.agterm → agterm_act",
            detail="Local listener")
    for act in literal(tree, "BOARD_ACTS"):
        add("POST", f"{task}/{act}", f"Handler.board_act → act_{act}")
    add("POST", task + "/cards/{page}/answer", "Handler.card_answer → act_card")
    add("POST", workspace + "/start", "Handler.board_start → act_start")
    add("POST", workspace + "/backlog/drop", "Handler.board_drop → act_drop")


# The page and action names are the stable parts of each act. Descriptions can
# change as controls or keys change. Read the cited page and implementation
# together when updating this list.
BOARD_ACTS = {
    ("Workspace index", "src/lem/board_pages.py:index_page"): """
        open-workspace | Open a workspace from the directory for this machine or a joined machine.
    """,
    ("Workspace shell", "src/lem/board_pages.py:sidebar,rail,switcher,layout"): """
        tasks | Open Tasks from the sidebar or rail or with T.
        waits | Open Waits for you from the sidebar or rail or with W.
        backlog | Open Backlog from the sidebar or rail or with B.
        activity | Open Activity from the sidebar or rail or with A.
        new-task | Open New task with + or N.
        switch-workspace | Open the workspace menu and choose a workspace on this or another machine.
        workspace-index | Open the index of workspaces.
        close-menu | Press Escape to close the workspace menu.
        fold-sidebar | Fold or unfold the sidebar. The board keeps the choice for this device.
        phone-drawer | Open the sidebar drawer on a phone.
        close-phone-drawer | Close the drawer with the backdrop or Escape. A visit closes it too.
        open-wait | Open a task or its next step from a row in the sidebar.
        open-notice | Open the task linked from a board notice.
    """,
    ("Search", "tools/board-kit/controllers/search.js"): """
        open | Open Search with its button or Cmd-K or Ctrl-K. An empty search shows open tasks.
        filter | Type letters from a task or backlog title. The best matching titles come first.
        move | Move the mark with Up or Down.
        open-result | Open the marked result with Enter or select a result by click. A backlog result opens its item.
        close | Close Search with Escape or a click outside it. Focus returns to the opener.
    """,
    ("Tasks", "src/lem/board_pages.py:kanban,task_card; tools/board-kit/controllers/cursor.js"): """
        open-task | Open a task card or one of its links to a task tab.
        mark-vertical | Move the mark within a column with J or K or the Up or Down arrow.
        mark-horizontal | Move the mark between columns with H or L or the Left or Right arrow.
        open-marked | Press Enter to open the marked task.
        fold-column | Fold or unfold a column. The board keeps the choice for this device.
        jump-column | Select a column on the phone and scroll its cards into view.
        older | Open The older tasks from the Done column.
    """,
    ("Older tasks", "src/lem/board_pages.py:older_page"): """
        open-task | Open an older ended task.
        return | Return to Tasks.
    """,
    ("Waits for you", "src/lem/board_pages.py:waits_page,row_acts,parked_group; tools/board-kit/controllers/cursor.js"): """
        mark | Move the mark with J or K or the Up or Down arrow.
        open-marked | Press Enter to open a task or its task session, or toggle the marked stack.
        stack | Open or close the stack of requests for one task.
        open-task | Open a task from its row.
        open-session | Start a task session if one is absent or stopped.
        select-session | Jump to the task session in agterm from a row with that action.
        read-criteria | Open Read and approve… for the criteria card.
        plan-build | Choose Build on the row for a plan that waits. Add a note if needed.
        plan-drop | Open the drop confirmation for a plan that waits.
        breaker-help | Send Help and its required note from the row for a breaker.
        breaker-drop | Open the drop confirmation from the row for a breaker.
        skip-personas-yes | Answer Yes on the row that asks to skip the persona read.
        skip-personas-no | Answer No on the row that asks to skip the persona read.
        approve-one-yes | Read and approve the criterion of a small change on its row.
        approve-one-no | Choose No and give the required note on the row for a criterion.
        read-merge | Open the merge confirmation or read the merge review.
        park | Open the park confirmation.
        open-card | Open the pending card.
        parked-task | Open a parked task or its session.
        turn-on | Turn on notifications and authorize them for this device.
        test-push | Send a test notification to this device.
        turn-off | Turn notifications off for this device.
    """,
    ("New task", "src/lem/board_pages.py:new_page; src/lem/serve.py:act_start"): """
        start | Type a request and submit Start the task. Lem creates the task and opens a session.
        cancel | Return to the task board without a new task.
    """,
    ("Backlog", "src/lem/board_pages.py:backlog_item,backlog_page; tools/board-kit/controllers/backlog.js"): """
        expand | Open or close an item with its title or Enter on its marked row.
        filter-text | Filter on words in titles, paths, places or item text.
        filter-worth | Filter by worth or clear that choice with All.
        filter-facts | Filter for stale or new items.
        focus-filter | Press / to focus and select the filter text.
        clear-filter | Press Escape to clear the filter field or leave it when it is empty.
        move-from-filter | Press Enter or Down in the filter field to leave it and move the mark.
        mark | Move the mark with J or K or the Up or Down arrow.
        read-again | Press Read again or R to refresh the backlog.
        copy-start-command | Copy the start command for an item with its copy control or S.
        start-task | Start a task from a backlog item when the item has no open task.
        open-held-task | Open the task that already holds an item.
        drop-reviewer-item | Drop an undecided reviewer's item. An item with an open task is refused.
        open-source | Open the task or pull request named as the source of a backlog item.
        show-named-item | Follow an item link to open, mark and scroll to that item.
    """,
    ("Activity", "src/lem/board_pages.py:activity_page,timeline,feed_rows; tools/board-kit/controllers/tip.js"): """
        open-task | Open the task from its timeline or event row.
        read-interval | Point to or focus a time segment to read its details.
    """,
    ("Task panel", "src/lem/board_task.py:head,tab_nav,head_acts,panel; tools/board-kit/controllers/panel.js; tools/board-kit/controllers/splitter.js"): """
        close | Close the panel with its close control or Escape. The board restores focus to the marked row or card.
        overview | Open Overview with its tab or 1.
        criteria | Open Criteria and decisions with its tab or 2.
        checks | Open Checks and review with its tab or 3.
        timeline | Open Timeline with its tab or 4.
        artifacts | Open Artifacts with its tab or 5.
        details | Fold or unfold the task header details.
        expand | Expand the panel to the full stage or dock it at the right.
        resize | Drag the panel separator to set its width.
        reset-width | Double-click the separator to restore the usual width.
        copy-branch | Copy the task's branch name.
        open-pr | Follow the link to the task's pull request.
        open-ticket | Follow the link to its issue or ticket.
        select-session | Open the current task session in agterm.
        open-session | Start a task session when no session runs.
        open-inbox | Open the Inbox thread from the task while away.
        merge | Open the merge confirmation.
        park | Open the park confirmation from an eligible task.
    """,
    ("Overview", "src/lem/board_task.py:overview_tab,verdict,breaker_card,now_answer,cards_card"): """
        read-artifact | Open an artifact, plan or report from a task summary or next step.
        read-reason | Follow a reason to the open row that gives its criterion, check or decision.
        open-card | Open the pending card from Overview.
        read-answer | Open a previous card or view the answer that took effect.
        read-breaker | Open the breaker document.
        read-merge-review | Open the merge review artifact.
        approve-plan-build | Choose Build on a plan that waits. Add a note if needed.
        approve-plan-drop | Choose Drop on a plan that waits and confirm the drop.
        breaker-help | Send Help and its required note to the lead.
        breaker-park | Choose Park for a breaker and confirm the park.
        breaker-drop | Choose Drop for a breaker and confirm the drop.
        skip-personas-yes | Answer Yes when asked to skip the persona read.
        skip-personas-no | Answer No when asked to skip the persona read.
        approve-one-yes | Approve the criterion of a small change.
        approve-one-no | Request a change to the small change's criterion with No and a required note.
    """,
    ("Criteria and decisions", "src/lem/board_task.py:approve_card,criteria_tab,decision_row,breaker_row"): """
        approve-yes | Approve the standard track criteria with Yes.
        approve-no | Choose No and add the required note. Read changed criteria or the same criteria on the next card.
        approve-previous-release | Approve criteria for an eligible task from the previous release.
        read-decision | Expand a decision to read its story, options, votes and reason.
        read-criterion | Expand criterion details and read its text or chart.
        read-breaker-file | Follow a link to a breaker document.
    """,
    ("Checks and review", "src/lem/board_task.py:checks_tab,log_link"): """
        open-log | Open a check command's log from its result.
        read-review | Expand review details or open a linked review artifact.
    """,
    ("Timeline", "src/lem/board_task.py:time_card,feed_card; tools/board-kit/controllers/tip.js"): """
        read-interval | Point to or focus a segment to read the time and actor.
        read-event | Expand an event's details where present.
    """,
    ("Artifacts", "src/lem/board_task.py:artifacts_tab,art_tree,art_body,media_pair; tools/board-kit/controllers/artifacts.js; tools/board-kit/controllers/markdown.js"): """
        fold-group | Open or close an artifact group. The board keeps that choice across visits to this task.
        select-artifact | Select a plan, report, log, picture or other listed file.
        copy-path | Copy the chosen artifact's path.
        open-html | Read an HTML artifact in its frame and follow its allowed links.
        open-image | Open or enlarge a picture from an artifact or its rendered Markdown.
        compare-pictures | View the two sides of a picture pair.
    """,
    ("Merge confirmation", "src/lem/board_task.py:merge_step,confirm_card; tools/board-kit/controllers/sheet.js"): """
        review | Read the green or not green state, pull request and commit before merge.
        open-pr | Open the pull request from the confirmation.
        confirm | Confirm the merge of the displayed commit. On a phone, scroll to the end to enable the button.
        cancel | Cancel and return to the task.
    """,
    ("Park confirmation", "src/lem/board_task.py:park_step; tools/board-kit/controllers/sheet.js"): """
        confirm | Confirm Park. Enter a reason if needed.
        cancel | Cancel the park and return to the task.
    """,
    ("Drop confirmation", "src/lem/board_task.py:drop_step; tools/board-kit/controllers/sheet.js"): """
        confirm | Confirm Drop for a plan or breaker. Add a note if needed.
        cancel | Cancel the drop and return to the task.
    """,
    ("Question card", "src/lem/board_task.py:card_step; src/lem/cards.py; src/lem/answers.py; skills/lem-ask/runtime/ask.js"): """
        open | Open the same card that the task session shows in agterm, with its pictures and options.
        pick-one | Select one option on a single-choice question.
        pick-many | Select options on a multiple-choice question.
        note | Add a note to an option. A note alone on an option question leaves the card open.
        text | Type the answer on a text question.
        tune | Set the values or choose a preset on a tune question. The preview follows the changes.
        reset-tune | Reset a tune control to its initial value.
        replay-tune | Replay the tune preview with its button or R.
        move-mark | Move the option mark with H, J, K, L or the arrow keys.
        keyboard-pick | Pick an option with a number key or Space. Enter can pick the marked single choice.
        option-details | Open option details with the details control or E. Shift-E toggles all details.
        focus-note | Focus the text field with / or Tab. Escape leaves the field.
        keyboard-help | Press ? to show or hide the card's keys.
        skip-optional | Continue from an optional question with no value.
        navigate | Move through the questions or go back to edit where the card offers these controls.
        review | Review the answers before submission when the card asks for review.
        submit | Submit an answer to the task. Only the first answer takes effect.
        retry | Correct a refused answer and submit it again while the card still waits.
        result | Read the answer taken or the reason the card no longer waits.
        cancel | Return to the task without an answer.
    """,
    ("Charts", "tools/board-kit/controllers/chart.js"): """
        enlarge | Open the larger diagram from its chart control.
        zoom | Zoom with the buttons, +, =, -, wheel or pinch.
        pan | Move the diagram by drag or the arrow keys.
        fit | Fit the diagram to the window with its button or 0.
        close | Close the diagram with its close button or Escape and return focus.
    """,
    ("Phone notifications", "docs/board.md; skills/lem/assets/sw.js"): """
        install | Use the browser's Add to Home Screen command to open Lem from its own icon.
        open-notification | Tap a notification to open or focus its board address.
    """,
}


def board_acts(ledger):
    for (page, citations), records in BOARD_ACTS.items():
        paths = []
        for citation in citations.split("; "):
            file = citation.split(":", 1)[0]
            (ledger.root / file).stat()
            paths.append(file)
        references = citations.removeprefix(paths[0] + ":") if ":" in citations else ""
        section = f"{page} ({references})" if references else page
        for line in records.strip().splitlines():
            key, description = line.strip().split(" | ", 1)
            ledger.add("act", f"{page}/{key}", paths[0], description,
                       section=section)


DOCTOR_DETAILS = {
    "python3": "Check that the Python interpreter meets Lem's minimum version.",
    "gh": "Find the GitHub CLI and report whether it is signed in.",
    "agterm": "Find agtermctl, read its version and report whether this is an agterm session.",
    "agterm skill": "Find the installed agterm instructions.",
    "task picker": "Find the agterm keymap chord that runs Lem's task picker.",
    "claude": "Find Claude Code and read its version.",
    "lem-builder agent": "Find the Lem builder definition Claude Code can use.",
    "codex": "Find Codex and read its version.",
    "codex persona agent": "Find the Codex persona definition in the user configuration.",
    "permission mode": "Read the effective permission modes of a new session and a background builder.",
    "lem plugin scope": "Report a user-scope Lem install that loads in every repository.",
    "project personas": "Read the effective project cast. If there is one persona, say that a panel needs a second.",
    "correction hook": "Look for an older correction hook alongside the plugin hook, and give the applicable removal step.",
    "hook modules": "Check the plugin hook launchers and the app modules and imports they need.",
    "Jev key": "Check for JEV_API_KEY. The key is required if correction collection is on.",
    "load gate": "Read the machine's load gate settings and show the configured and current load.",
    "handoff tokens": "Read the token threshold that compacts the task's session.",
    "board server": "Read the server's addresses, process, log and code version. Report when the installed code replaces it.",
    "installed Lem": "Compare each workspace's installed plugin code with the board server code.",
    "board notifications": "Read the device subscriptions and the last push result.",
    "cronn": "Find cronn, read its configured port and report whether its status API answers.",
}


def doctor(ledger):
    file = "src/lem/doctor.py"
    tree = ledger.tree(file)
    for func in tree.body:
        if not isinstance(func, ast.FunctionDef):
            continue
        for node in ast.walk(func):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                call = node.func.id
                if call not in {"tool", "skill"}:
                    continue
                label = ast.literal_eval(node.args[0])
                if call == "tool":
                    need = ast.literal_eval(node.args[1])
                    detail = ast.literal_eval(node.args[2])
                else:
                    label += " skill"
                    need = next((ast.literal_eval(arg.value) for arg in node.keywords
                                 if arg.arg == "need"), "required")
                    detail = ast.literal_eval(node.args[1])
            elif isinstance(node, ast.Dict):
                values = {key.value: value for key, value in zip(node.keys, node.values)
                          if isinstance(key, ast.Constant)}
                if not {"name", "need", "used_for"} <= values.keys():
                    continue
                name = values["name"]
                if isinstance(name, ast.Constant):
                    label = name.value
                elif func.name == "install_rows":
                    label = "installed Lem"
                else:
                    continue  # Dictionary returned by tool() or skill() itself.
                need = ast.literal_eval(values["need"])
                detail = ast.literal_eval(values["used_for"])
            else:
                continue
            what = DOCTOR_DETAILS.get(label, detail)
            ledger.add("doctor", label, file, f"{label} ({need}) — {what}", section=func.name)


def functions_in(tree):
    def visit(nodes, prefix=""):
        for node in nodes:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                name = prefix + node.name
                if not isinstance(node, ast.ClassDef):
                    yield name, node
                yield from visit(node.body, name + ".")

    return dict(visit(tree.body))


def in_function(func):
    """Walk a function without descending into another scope."""
    def visit(node):
        yield node
        for child in ast.iter_child_nodes(node):
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                yield from visit(child)

    return visit(func)


def message(node, constants, replacements=None):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(message(piece, constants, replacements) for piece in node.values)
    if isinstance(node, ast.FormattedValue):
        expr = ast.unparse(node.value)
        if replacements and expr in replacements:
            return replacements[expr]
        if isinstance(node.value, ast.Name) and expr in constants:
            return constants[expr]
        return "{" + expr + (f"!{chr(node.conversion)}" if node.conversion != -1 else "") + "}"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return message(node.left, constants, replacements) + message(node.right, constants, replacements)
    return "{" + ast.unparse(node) + "}"


def first_sentence(text):
    # Periods in quoted commands, dotted names, and substitutions are not
    # sentence boundaries. Keep the source's capitalization and punctuation.
    text = words(text)
    text_without_inline = re.sub(r"`[^`]*`|\{[^{}]*\}", lambda m: "x" * len(m[0]), text)
    end = re.search(r"[.!?](?= |$)", text_without_inline)
    return text[:end.end()] if end else text


def returned(func, *, part=None):
    for node in in_function(func):
        if not isinstance(node, ast.Return) or node.value is None:
            continue
        value = node.value
        if part is not None and isinstance(value, ast.Tuple):
            value = value.elts[part]
        if isinstance(value, (ast.JoinedStr, ast.BinOp)):
            yield value
        elif isinstance(value, ast.Constant) and isinstance(value.value, str):
            yield value


def assigned(func, name):
    for node in in_function(func):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            yield node.value


REFUSAL_HELPERS = {
    ("cmd_base", "rebase_failed"): "rebase_failed",
    ("step_lock", "held_refusal"): "held_refusal",
    ("checks_ready", "missing"): "polish_missing",
    ("cmd_read", "stale"): "record_tip_refusal",
    ("cmd_read", "the review is of the tip the checks passed on, and {missing}"):
        "gate_missing",
    ("cmd_propose", "{missing}"): "gate_missing",
    ("cmd_propose", "not_github"): "not_github",
    ("cmd_propose", "why_not"): "read_skipped",
    ("may_merge", "refusal"): "merger_refusal",
    ("forge_done", "wrong"): "base_refusal",
    ("cmd_merge", "wrong"): "expected_refusal",
    ("merge_locked", "wrong"): "base_refusal",
    ("merge_locked", "{missing}"): "gate_missing",
    ("merge_locked", "moved_refusal"): "moved_refusal",
}


def refusals(ledger):
    file = "src/lem/land.py"
    tree = ledger.tree(file)
    functions = functions_in(tree)
    constants = {
        target.id: node.value.value
        for node in tree.body if isinstance(node, ast.Assign)
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
        for target in node.targets if isinstance(target, ast.Name)
    }

    def add(function, description, *, variant="", producer=""):
        label = first_sentence(description)
        key = f"{function}:{variant + ':' if variant else ''}{text_id(label)}"
        section = function + (f" via {producer}" if producer else "")
        ledger.add("refusal", key, file, label, section=section)

    def show(node, **replacements):
        return message(node, constants, replacements)

    for function, func in functions.items():
        parents = {child: parent for parent in in_function(func)
                   for child in ast.iter_child_nodes(parent)}
        for node in in_function(func):
            if not isinstance(node, ast.Raise) or not isinstance(node.exc, ast.Call):
                continue
            exc = node.exc
            if not isinstance(exc.func, ast.Name) or exc.func.id not in {
                "LandError", "Refusal", "ForgeSaid"
            }:
                continue
            arg = exc.args[1 if exc.func.id == "Refusal" else 0]
            if isinstance(arg, ast.Name):
                selector = arg.id
            elif isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name):
                selector = arg.func.id
            else:
                selector = show(arg).split(";", 1)[0]
            helper = REFUSAL_HELPERS.get((function, selector))
            if helper:
                for value in returned(functions[helper], part=1 if helper == "read_skipped" else None):
                    detail = show(value)
                    if helper == "base_refusal":
                        # The two call sites have already checked the forge state.
                        if function == "forge_done" and " is on {there}" in detail:
                            continue
                        if function == "merge_locked" and " was merged into {there}" in detail:
                            continue
                    if helper == "gate_missing":
                        detail = show(arg, missing=detail)
                    if helper == "moved_refusal":
                        moved = functions[helper]
                        said, = assigned(moved, "said")
                        if "{read}" in detail:
                            read, = assigned(moved, "read")
                            for reason in (read.body, read.orelse):
                                add(function, show(value, said=show(said), read=show(reason)),
                                    producer=helper)
                            continue
                        detail = show(value, said=show(said))
                    add(function, detail, producer=helper)
            elif function == "checks_run" and selector == "refusal":
                bodies = ("checks_body", "checks_body.criteria_refused")
                for producer in bodies:
                    for value in returned(functions[producer], part=1):
                        add(function, show(value), producer=producer)
                for value in returned(functions["bar_refusal"]):
                    add(function, show(value), producer="checks_body → bar_refusal")
            elif function == "main" and selector == "stopped":
                release = "src/lem/release.py"
                stop = functions_in(ledger.tree(release))["stop"]
                for branch in in_function(stop):
                    if isinstance(branch, ast.Dict):
                        for key, value in zip(branch.keys, branch.values):
                            if isinstance(key, ast.Constant) and key.value == "say":
                                add(function, show(value), producer="release.stop")
                add(function, "{error from the task's release record or installed release}",
                    producer="release.check")
            elif function == "cmd_merge_review" and selector == "{problem}":
                for value in assigned(func, "problem"):
                    add(function, show(arg, problem=show(value)), producer="merge review reply")
            elif function == "checks_run" and selector == "stopped":
                value, = assigned(func, "stopped")
                handler = parents[node]
                tried = parents[handler]
                call = next(part.func for part in ast.walk(tried.body[0])
                            if isinstance(part, ast.Call))
                add(function, show(value), variant=ast.unparse(call))
            elif function == "project_now" and "has no .lem/settings.toml" in selector:
                scope = parents[node]
                while scope is not func and not isinstance(scope, ast.Try):
                    scope = parents[scope]
                variant = "in-process" if isinstance(scope, ast.Try) else "subprocess"
                add(function, show(arg), variant=variant)
            elif function == "keep_reviews" and "{why}" in show(arg):
                for value in returned(functions["moving_refusal"]):
                    add(function, show(arg, why=show(value)), producer="moving_refusal")
            elif function in {"cmd_propose", "cmd_clean"} and selector.startswith("{protected}"):
                does, what = ("pushes", "to") if function == "cmd_propose" else ("deletes", "of")
                for value in returned(functions["protected_refusal"]):
                    detail = show(value, does=does, what=what)
                    add(function, show(arg, protected=detail), producer="protected_refusal")
            elif isinstance(arg, ast.IfExp):
                add(function, show(arg.body))
                add(function, show(arg.orelse))
            else:
                add(function, show(arg))


# A duty has its own name even when several jobs share a loop or a function.
# Values in braces are the timers from this checkout, rather than copies of them.
DUTIES = {
    ("serve", "forge_loop"): """
        scan-workspaces | At each {forge_tick}-second forge tick, run the forge, session and retention jobs for each registered workspace with a state directory.
    """,
    ("serve", "Machine.workspaces"): """
        reload-workspaces | When a watcher or board listing asks for workspaces, reread the registry. Reuse a workspace when its name and path match. Include only workspaces with a state directory.
    """,
    ("serve", "Workspace.count"): """
        refresh-workspace-counts | When a board listing needs workspace counts, recompute them if the cached counts are at least {refresh_seconds} seconds old. Recompute the active workspace's counts for its page.
    """,
    ("serve", "prune_once"): """
        prune | At the first forge tick and every {prune_seconds} seconds after the last run, prune a real workspace whose settings read. Apply state.keep_days to old files and summarize eligible ended tasks.
    """,
    ("serve", "forge_once"): """
        poll-github | At a forge tick, ask GitHub about relevant open pull requests in a real workspace with a GitHub remote. Look the first time and after at least {forge_seconds} seconds. Save mergeability and the head for the board and conflict wake.
        record-forge-merge | When the forge reports a merged pull request, run the landing bookkeeping if this server does not hold its merge. Retry a failed bookkeeping call after {duty_retry} seconds.
        record-forge-close | When the forge reports a closed pull request and this server does not hold its merge, record the task as dropped and keep the branch. Retry a failed bookkeeping call after {duty_retry} seconds.
    """,
    ("serve", "Workspace.look_sessions"): """
        poll-sessions | At a forge tick, read the live task sessions and find the worktrees of ended tasks in each real workspace with settings. Refresh the board when a session need or a held task's work changes.
    """,
    ("serve", "duties"): """
        wake-ended | Wake a task after its pull request merges or closes on GitHub, if its worktree remains and the end has had no wake or open.
        wake-conflict | Wake an open task when GitHub reports a conflict on the head it proposed and that proposal has had no conflict wake or open.
        wake-refused | Wake an open task after a merge-agent refusal or after Lem refuses the owner's merge because the base moved. The refusal has had no later wake or open.
        open-queued | Open a session for a queued task when its predecessor ends, the board knows no session lives, and none opened during this wait.
        wake-queued | Wake the live session of a queued task when its predecessor ends and no session opened or woke during this wait.
        wake-status | Ask a live task session for status after {quiet_minutes} minutes without work. If Lem cannot read its signs, use the task's events. The guard covers building, ready and landing tasks with a live agent and no shell command.
        restart-stopped | After a status wake and {answer_minutes} more minutes without work, open a fresh session if the signs read, no stop stands and the restart for this stretch of work remains available.
        record-stop | After the status wake and {answer_minutes} more minutes without work, log the stop when Lem cannot read the session's signs or the restart is already spent or blocked by a stop. The board then shows the stop if it still stands.
    """,
    ("serve", "merge_due"): """
        merge-agent | Start a separate merge job when the review of the proposed tip says merge, calls nobody and needs no new checks for a moved base. Skip a current refusal, a forge conflict or a merge already in progress.
    """,
    ("serve", "stands_due"): """
        merge-standing-owner | Start the owner's standing merge when a safe read or a new landing preserves the owner's word for the present tip. A new refusal, a conflict, a required new round or a merge in progress holds it.
    """,
    ("serve", "run_duties"): """
        retry-duties | After a duty command fails, retry when it is still due after {duty_retry} seconds. A merge retry belongs to the proposed tip and its review.
    """,
    ("serve", "merge_in_thread.merge"): """
        publish-merge-result | When a server merge ends, record its outcome for the board. The note can report a merge that stands after a base change. Clear the active merge and refresh the workspace.
    """,
    ("board_model", "Reader.read_owner"): """
        watch-owner | When a model read finds a change to the machine's owner mark, read the new status. The board and the Inbox watcher use it to tell whether the owner is away.
    """,
    ("serve", "Handler.refreshes"): """
        refresh-on-connect | When a stream opens with an old rendered version, a since query or Last-Event-ID, send a refresh at once.
        refresh-on-change | Every {watch_seconds} seconds per open workspace stream, check the event log, owner mark, settings, backlog, Inbox and selected task files. Send a refresh on a change or when a board act, session look or forge look changes the workspace.
        stream-heartbeat | On an open stream with no refresh for {ping_seconds} seconds, send a ping with the log version.
    """,
    ("inbox", "Watcher.look_at"): """
        poll-inbox | Every {inbox_seconds} seconds, check each real workspace with known session status. Read the Inbox status while the owner is away or a sent item remains on record.
        send-inbox-question | While the owner is away and the Inbox has a tailnet address, send a new wait with a live session that can answer. Use that Claude Code session and the task's own thread. The merge wait includes its review. Cards have their own board page.
        send-inbox-note | While away with an Inbox tailnet address, send a board link and the cause when a new wait has no session that can answer or is ineligible for a question. Cases include a missing, deaf or stopped session, a dropped predecessor, a refused or unreviewed merge and a release stop.
        retry-inbox-send | After a send gives no answer, retry on a later look with the same payload and key while the owner is away, the door is open and the wait still matches.
        withdraw-inbox-question | When an open Inbox question no longer applies or a replacement is due, withdraw it while the Inbox runs. Keep a question that the task still holds while it works on the owner's answer.
        forget-inbox-note | When a sent note no longer matches or an unsent item no longer qualifies, remove it from the local record.
    """,
    ("inbox", "message_of"): """
        inbox-plan | For an eligible wait for plan approval, ask Build or Drop and attach the plan when it is available.
        inbox-breaker | For an eligible breaker, send its document or summary with Help, Park and Drop.
        inbox-merge | For an eligible merge wait, send the pull request, the full proposed commit and why the merge agent calls the owner. Offer Merge or Not now.
        inbox-order | When a task waits for the owner to resolve its order, send a text question that asks which task it follows.
        inbox-blocked | When an eligible blocked task needs the owner's direction, send its state and ask what to do or whether to drop it.
        inbox-other-question | For other eligible waits, send the task's state and the board's instructions for the owner as a text question.
    """,
    ("serve", "inbox_wake"): """
        wake-inbox-question | After the Inbox accepts a new or retried question, wake the live session so it can show its card.
    """,
    ("inbox", "Watcher.replies"): """
        wake-inbox-reply | When a sent question names a session that no longer runs the task, read its thread. Wake the live replacement for a new owner reply and remember which replies it heard about.
    """,
    ("serve", "tell_session"): """
        wake-board-answer | After an owner board act that needs to tell the task, send the live session a wake. The session command can open a session when the task needs one.
    """,
    ("push", "Watcher.look"): """
        push-new-waits | Every {push_seconds} seconds, detect newly waiting rows in real workspaces. Use the first row's action and task link, with a count of further rows, in one push per device whose workspace filter matches. A first look sets the baseline. A row that returns within {flap_seconds} seconds sends no second push.
    """,
    ("push", "send_test"): """
        push-test-device | When a subscribed device asks for a test from the board, send that device a test push.
    """,
    ("push", "send_all"): """
        push-test-all | When the owner runs lem serve --push-test, send a test push to every subscribed device.
    """,
    ("push", "Pusher.send"): """
        expire-push-subscription | After a push service reports 404 or 410, remove that subscription. Keep the last push results for the server status.
    """,
    ("peers", "Peers.all"): """
        reload-peers | When a request needs peer state or a named peer, reread the machine's peers table. Refresh the local peer objects when a name or port changes.
    """,
    ("peers", "Peer.fresh"): """
        poll-peers | When the board requests peer lists and a peer's last look is at least {peer_fresh} seconds old, fetch its workspaces in parallel with other due peers. Keep the last answer and record if the peer is unreachable.
    """,
    ("peers", "forward"): """
        relay-peer-read | When a request reads a joined machine's page, file or stream, pass the read to that peer and relay its answer. Record a failed connection as unreachable.
    """,
    ("peers", "pipe.watch"): """
        close-peer-stream | During a relayed peer stream, check every {peer_watch} seconds for client disconnect or local shutdown. Close the peer socket when either occurs.
    """,
    ("serve_hook", "main"): """
        ensure-on-session-start | When a Claude Code startup or resume hook finds a repository with Lem team settings, start a detached ensure without holding up the session.
    """,
    ("board", "ensure_server"): """
        ensure-on-board-open | Before the board command opens a workspace or task page, run ensure and use the server address it reports.
    """,
    ("__main__", "look_for_server"): """
        restart-on-command | On an eligible Lem command, run a detached ensure if the board's PID file has no live process and LEM_SERVE is not off.
    """,
    ("serve", "ensure_held"): """
        start-if-missing | When ensure finds the configured port free and LEM_SERVE is not off, start the detached server and wait for its answer.
        replace-server | {replace_server}
    """,
    ("serve", "start_server"): """
        trim-server-log | Before a detached start, empty the server log if it is larger than {log_cap} bytes. Append the startup identity and the child's output.
    """,
    ("serve", "configure"): """
        rebind-main-port | On a requested main-port change, stop the old server for this home before the new configuration takes effect.
        remove-tailnet-door | When the owner turns the door off or moves it to a different port, remove Lem's old Tailscale entry if it still points at its loopback door.
    """,
    ("serve", "listen"): """
        bind-tailnet-door | At startup with the door enabled, check the local Tailscale state and bind a separate loopback listener. Publish the matching HTTPS entry or keep it if already set.
        stop-server-jobs | On a local stop request, SIGTERM or Ctrl-C, end the background jobs and streams, close the listeners and remove the PID file.
    """,
    ("serve", "settle_names"): """
        name-server | At startup, use the local Tailscale name when available. Keep the short host name as an alias if it differs. Otherwise use the short name.
    """,
    ("serve", "door_refusal"): """
        check-door-request | For each tailnet request, check the board host and the owner's Tailscale login. Refuse Funnel requests and cross-origin actions.
    """,
    ("serve", "Door.reread"): """
        refresh-door-owner | When the door sees a login that differs from the remembered owner, reread the current login at most once per {login_recheck} seconds. Recheck the request if the login changed.
    """,
}


def server_duties(ledger):
    constants = {
        "serve": {
            "forge_tick": "FORGE_TICK", "forge_seconds": "FORGE_SECONDS",
            "prune_seconds": "PRUNE_SECONDS", "duty_retry": "DUTY_RETRY",
            "watch_seconds": "WATCH_SECONDS", "ping_seconds": "PING_SECONDS",
            "login_recheck": "LOGIN_RECHECK_SECONDS", "log_cap": "LOG_CAP",
            "refresh_seconds": "REFRESH_SECONDS",
        },
        "board_model": {"quiet_minutes": "QUIET_MINUTES", "answer_minutes": "ANSWER_MINUTES"},
        "inbox": {"inbox_seconds": "LOOK_SECONDS"},
        "push": {"push_seconds": "LOOK_SECONDS", "flap_seconds": "FLAP_SECONDS"},
        "peers": {"peer_fresh": "LIST_FRESH", "peer_watch": "WATCH_SECONDS"},
    }
    modules = {module for module, _ in DUTIES} | constants.keys()
    trees = {name: ledger.tree(f"src/lem/{name}.py") for name in modules}
    timers = {key: literal(trees[name], constant)
              for name, group in constants.items() for key, constant in group.items()}
    functions = {name: functions_in(tree) for name, tree in trees.items()}
    if "same_install" in functions["serve"]:
        timers["replace_server"] = (
            "When ensure finds a server for this home with a different door setting or "
            "install identity, stop it and start the caller's install. The identity "
            "uses the version, build commit and real package path. With no build commit, "
            "it also uses the newest module change time."
        )
    else:
        timers["replace_server"] = (
            "When ensure finds a server for this home with a different door setting or "
            "older code, stop it and start one with the requested settings. A different "
            "identity at the same code stamp also triggers replacement."
        )
    for (module, func), entries in DUTIES.items():
        if func not in functions[module]:
            raise ValueError(f"Duty source moved: {module}.{func}")
        file = f"src/lem/{module}.py"
        for line in entries.strip().splitlines():
            key, trigger = line.strip().split(" | ", 1)
            ledger.add("duty", key, file, trigger.format_map(timers), section=func)
    if literal(trees["board_model"], "WRITES_WORKED"):
        ledger.add("duty", "record-session-work", "src/lem/board_model.py",
                   "When readable signs show a turn since a status wake sent while the signs were unreadable, record the turn once and end the stop.",
                   section="stop_due")


# The command accepts caller-defined event names. This pattern finds the names
# the shipped stage text tells an agent to supply, including wrapped lines.
STAGE_EVENT = re.compile(
    r"\bproject(?:\s+--repo\s+[^\s`]+)?\s+log\s+SLUG\s+([a-z][a-z0-9.-]*)\b"
)
DIRECT_EVENT_RECORDS = {
    "src/lem/project.py": "summary_of",
    "src/lem/release.py": "log_stop",
    "src/lem/session_hook.py": "keep_transcript",
}


def dict_fields(func, key):
    return [
        value
        for node in in_function(func)
        if isinstance(node, ast.Dict)
        for name, value in zip(node.keys, node.values)
        if isinstance(name, ast.Constant) and name.value == key
    ]


def event_values(node, tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.Name):
        return [literal(tree, node.id)]
    if isinstance(node, ast.IfExp):
        return event_values(node.body, tree) + event_values(node.orelse, tree)
    raise ValueError(f"Unlisted event expression: {ast.unparse(node)}")


def call_name(expr):
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        return expr.attr
    return None


def events(ledger):
    writers = {}

    def record(event, file, func):
        writers.setdefault(event, {}).setdefault(file, set()).add(func)

    model = ledger.tree("src/lem/board_model.py")
    worked = literal(model, "WORKED")
    writes_worked = literal(model, "WRITES_WORKED")
    project_file = "src/lem/project.py"
    project = ledger.tree(project_file)

    for file in ledger.files("src/lem/**/*.py"):
        tree = ledger.tree(file)
        functions = functions_in(tree)
        for func, block in functions.items():
            for call in in_function(block):
                if not isinstance(call, ast.Call):
                    continue
                name = call_name(call.func)
                args = call.args
                given = [arg.value if isinstance(arg, ast.Constant) else None for arg in args]
                if name == "append_event" and len(args) == 4:
                    if (file, func) in {
                        (project_file, "cmd_log"),
                        (project_file, "cmd_resume"),
                        ("src/lem/cards.py", "log"),
                    }:
                        # The callers supply the event. Resume is added below.
                        continue
                    if file == "src/lem/session.py" and func == "cmd_worked":
                        gate = "" if writes_worked else " (gated off by board_model.WRITES_WORKED)"
                        record(worked, file, func + gate)
                        continue
                    event = args[1]
                elif file == "src/lem/cards.py" and name == "log":
                    event = args[1]
                elif file == "src/lem/criteria.py" and ast.unparse(call.func) == "task.log":
                    event = args[0]
                elif "project.py" in given and "log" in given:
                    event = args[given.index("log") + 2]
                    if (file, func) in {
                        ("src/lem/criteria.py", "Task.log"),
                        ("src/lem/decisions.py", "Task.add"),
                    }:
                        # The actual writers using the two wrappers are below.
                        continue
                else:
                    continue
                for value in event_values(event, tree):
                    record(value, file, func)

        if direct := DIRECT_EVENT_RECORDS.get(file):
            for node in dict_fields(functions[direct], "event"):
                for value in event_values(node, tree):
                    record(value, file, direct)
        if file == "src/lem/decisions.py":
            for func, block in functions.items():
                calls_add = any(isinstance(node, ast.Call) and ast.unparse(node.func) == "task.add"
                                for node in in_function(block))
                if calls_add:
                    kind, = dict_fields(block, "kind")
                    for value in event_values(kind, tree):
                        record("decision." + value, file, func + " via Task.add")

    for pattern in ("skills/**/*.md", "agents/**/*.md"):
        for file in ledger.files(pattern):
            for event in STAGE_EVENT.findall(ledger.read(file)):
                role = "lead" if file == "skills/lem/stages/plan.md" else "agent"
                record(event, file, role + " via project.cmd_log")
    # The plan tells the lead to use the criteria-read form from the interview.
    plan = "skills/lem/stages/plan.md"
    if "criteria.read.start" in ledger.read(plan) and "stages/interview.md" in ledger.read(plan):
        record("criteria.read", plan, "lead via project.cmd_log")

    copied = set(literal(project, "RESUMED_EVENTS"))
    decisions = {key for key in writers if key.startswith("decision.")}
    for name in copied | decisions:
        if name not in writers:
            raise ValueError(f"Resumed event has no originating writer: {name}")
        record(name, project_file, "cmd_resume (copies the old event)")

    for name, by_file in writers.items():
        # Put an originating writer first. A copied event still has one row.
        file = next(iter(by_file))
        source = ", ".join(sorted(by_file[file]))
        for other, functions in sorted(by_file.items()):
            if other != file:
                source += f"; {other}: {', '.join(sorted(functions))}"
        ledger.add("event", name, file, name, section=source)


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames != HEADER:
            raise ValueError(f"{path}: expected the ledger's TSV header")
        seen = set()
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path}: invalid TSV row at line {reader.line_num}")
            if not row["id"] or row["id"] in seen:
                raise ValueError(f"{path}: empty or repeated ID {row['id']!r}")
            seen.add(row["id"])
            yield Row(**row)


def add_extra(ledger, path):
    for row in read_rows(path):
        if row.id in ledger.rows:
            raise ValueError(f"{path}: {row.id} already exists in the commit ledger")
        if row.kind not in {"path", "seam"} or not row.id.startswith(row.kind + ":"):
            raise ValueError(f"{path}: give {row.id} a matching path or seam kind and ID")
        ledger.rows[row.id] = row
        ledger.sources.setdefault(row.kind, Counter())[path.name] += 1


def collect_commit(rev, root, source_notes):
    repo = subprocess.check_output(
        ["git", "-C", str(HERE), "rev-parse", "--show-toplevel"], text=True,
    ).strip()
    commit = subprocess.run(
        ["git", "-C", repo, "rev-parse", "--verify", "--end-of-options", f"{rev}^{{commit}}"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    archive = subprocess.check_output(["git", "-C", repo, "archive", commit])
    with tarfile.open(fileobj=BytesIO(archive)) as tar:
        tar.extractall(root, filter="data")
    ledger = Ledger(root, source_notes)
    for collect in (units, checks, rulings, commands, settings, routes, board_acts,
                    hooks, doctor, refusals, reading, server_duties, events):
        collect(ledger)
    return ledger


def write_rows(path, rows, saved):
    # A plain open, so the file gets the umask's mode (NamedTemporaryFile gives 0600).
    temp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temp_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
            writer.writerow(HEADER)
            for row in sorted(rows, key=lambda row: row.id):
                marks = saved.get(row.id, (row.fate, row.proof, row.note))
                writer.writerow((row.id, row.kind, row.source, row.what, *marks))
        temp_path.replace(path)
    finally:
        temp_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rev", default="bf6d2836", help="commit to read (default: %(default)s)")
    parser.add_argument("--out", type=Path, default=HERE / "rows.tsv")
    parser.add_argument("--keep", type=Path, help="copy fate, proof and note from this TSV by ID")
    parser.add_argument("--counts", action="store_true", help="print totals and source file counts as JSON")
    parser.add_argument("--source-notes", action="store_true",
                        help="put source annotations in unfilled note cells for an audit copy")
    args = parser.parse_args()

    try:
        with TemporaryDirectory(prefix="lem-ledger-") as directory:
            ledger = collect_commit(args.rev, Path(directory), args.source_notes)
        add_extra(ledger, HERE / "extra.tsv")
        saved = {row.id: (row.fate, row.proof, row.note) for row in read_rows(args.keep)} if args.keep else {}
        write_rows(args.out, ledger.rows.values(), saved)
    except subprocess.CalledProcessError as error:
        parser.exit(1, f"ledger.py: the owner must give a readable commit with --rev: {error}\n")
    except (OSError, ValueError, SyntaxError, tarfile.TarError) as error:
        parser.exit(1, f"ledger.py: {error}\n")
    if args.counts:
        print(json.dumps({kind: {"total": counts.total(), "files": counts}
                          for kind, counts in ledger.sources.items()},
                         indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
