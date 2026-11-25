#!/usr/bin/env python3
"""Assign each ledger row to the step that must account for it."""

import argparse
import csv
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile

HERE = Path(__file__).resolve().parent

STEPS = frozenset("""
ledger core tree slice-land slice-board slice-session trial-skeleton
land-base land-checks land-review land-propose land-merge task criteria sessions settings
land-text owner board-inputs board-views board-pages board-acts board-duties board-service
ask addons-flow addons-outside journeys browser guides pack-trial mutation trials close cutover
""".split())

# The six assignments by ID in part 9.
BY_ID = {
    "command:lem land alike": "land-review",
    "route:GET /{host}/{workspace}/stream": "board-pages",
    "ruling:a-correction-hook-registered-twice-judges-ea-f309bf034a652b95": "sessions",
    "act:Question card/replay-tune": "ask",
    "event:builder.start": "task",
    "guide:docs/settings.md": "settings",
}

MODULES = {
    "core": "clock files proc state paths python release",
    "tree": "names sibling",
    "task": "plans issues",
    "criteria": "criteria decisions",
    "sessions": "session session_hook hooks serve_hook signs tokens",
    "settings": "doctor",
    "board-views": "board_model artifacts",
    "board-pages": "board_pages board_task markup",
    "board-acts": "answers",
    "board-service": "board push",
    "ask": "ask cards",
    "addons-flow": "corrections picker",
    "addons-outside": "experts cast inbox peers jev",
}

# Only functions that a ledger row names need an entry. Shared landing
# helpers without a single destination are resolved in owners-judged.tsv.
LAND_FUNCTIONS = {
    "land-base": """
        cmd_start start_locked keep_reviews moving_refusal cmd_base rebase_failed
        merge_of pairs git_bytes git Task.need_landing Task.own_remote
    """,
    "land-checks": """
        cmd_polish cmd_checks checks_body checks_run checks_run.end checks_ready
        checks_stop checks_status line_join line_wanted wait_for_load tasks_of
        stale_bytecode remove_bytecode polish_missing gate_missing
    """,
    "land-review": """
        due cmd_read cmd_file cmd_alike check_alike defects_of flag_line
        jev_read same_flags named record_tip_refusal
    """,
    "land-propose": "cmd_propose gh_in not_github pr_text",
    "land-merge": """
        cmd_clean after_push cmd_merge cmd_merge_review merge_lock merge_locked
        cmd_merged forge_done noted moved_line follow may_merge step carry_merge
        drop_forge_copy base_refusal remove_item
    """,
}
PROJECT_FUNCTIONS = {
    "task": """
        cmd_log cmd_may_start cmd_plan_file cmd_resume cmd_state cmd_task_dir cmd_ticket_step
        cmd_worktree cmd_worktree_dir opening_line read_tasks state_root STARTS
    """,
    "sessions": "cmd_seat cmd_seat_again cmd_seat_failed",
    "settings": """
        cmd_handoff cmd_init cmd_load cmd_path cmd_rules cmd_set load
    """,
    "land-base": "cmd_may_land",
    "land-checks": "cmd_serial",
    "owner": "cmd_owner cmd_waiting",
    "board-duties": "cmd_prune summary_of",
    "addons-flow": "cmd_may_nap proposals_command",
}
SERVE_FUNCTIONS = {
    "ask": "act_card Handler.card_page",
    "board-acts": """
        act_answer act_approve act_drop act_merge act_park act_session act_start
        agterm_act asked_from tell_session
    """,
    "board-duties": """
        Workspace.look_sessions duties forge_loop forge_once inbox_wake merge_due
        merge_in_thread.merge prune_once run_duties stands_due
    """,
    "board-service": """
        Door.reread Handler.act Handler.answer Handler.in_workspace Handler.media
        Handler.push_act Handler.push_read Handler.raw Handler.refreshes Handler.spaces
        Workspace.count Machine.workspaces configure door_refusal ensure_held listen
        settle_names start_server stop_all
    """,
}

UNIT_FILES = {
    "core": "clock files proc state paths unit_runner release",
    "tree": "commands command_lines sibling",
    "land-propose": "land_text",
    "land-checks": "the_bar",
    "task": "task task_rules issues",
    "criteria": "criteria criteria_change decisions",
    "sessions": "session hooks signs tokens",
    "settings": "settings settings_files rule_picker doctor",
    "owner": "owner",
    "board-views": "board_model",
    "board-pages": "board_pages board_task markup",
    "board-acts": "board_answers board_criteria_change",
    "board-service": "board push",
    "ask": "ask cards serve_cards",
    "addons-flow": "corrections picker proposals backlog",
    "addons-outside": "experts cast inbox peers jev",
    "guides": "agents_md",
}
LAND_CLASSES = {
    "land-base": "KeepReviews ConflictNames RebaseUnshown RebaseFailed",
    "land-checks": """
        Bar FencedPlan UnclosedFence BarRefusal ChecksSay StaleBytecode RemoveBytecode
        Duration LastRun Overdue Resumed HeldRefusal SameChecks TakenFromPolish
        TheLongestWaitStartsFirst OneLineForTheMachine WantedGoesFirst
        ASecondWaitCountsFromItsStart TheLoadStillDecides AGoneRunLosesItsPlace
        TheWait WaitsBehindSays
    """,
    "land-review": """
        DefectsOutside TheItemOfADefect TheNotesLines EventLog ResumedRead
        FailedAttempt ReadOfATip ExpectedTip BarFile JevAsk TheBarJevReads
        TheFindingsUnderTheBar TheSpecOfAFinding TheReadOfEachFinding
        TheItemsThatMayHoldAFinding AnOverDefectOfARefutedItem JevOnTheLines
    """,
    "land-propose": "InterviewApproved",
    "land-merge": """
        TheSquashBody WhoMerges MergeReview MergeSeat MergeBriefPictures MergeBriefTry
        MovedBase ForgeBase FirstDiffer ReadOfAMovedBase
    """,
}
SERVE_CLASSES = {
    "board-duties": """
        Duties MovedBaseRead StoppedSession DutyKey ForgeLookBesideAMerge Prune WorkingSession
    """,
    "board-service": """
        Door Actions StartBehind Reads Notes StreamOpen Names StoppedOpen KeepDays
        Look LogLook Configure SwitcherCount PeersTrouble DeepBody Install AskHome
    """,
}
SHELL_FILES = {
    "core": "lint shellcheck checks suites all test-lem lib python",
    "tree": "lem-command",
    "land-base": "lem-land-guards",
    "land-checks": "lem-serial",
    "land-review": "lem-land-review lem-land-backlog",
    "land-propose": "lem-land-local lem-land-github",
    "land-merge": "lem-land-shop",
    "land-text": "lem-land-small",
    "task": "lem-state",
    "criteria": "lem-decisions",
    "sessions": "lem-session",
    "settings": "lem-settings lem-machine",
    "board-acts": "lem-board-act",
    "board-service": "lem-serve",
    "ask": "test-ask",
    "addons-flow": "lem-naps lem-picker",
    "addons-outside": "test-ask-expert test-gate-panel lem-peers",
    "browser": "lem-board-keys",
    "guides": "test-site",
}

TEXT_FILES = {
    "task": """
        stages/new.md stages/start.md stages/park.md stages/correct.md stages/investigate.md
        prompts/investigator.md prompts/scout.md harness/claude-code/tracker.md
    """,
    "criteria": """
        stages/interview.md stages/plan.md stages/build.md stages/talk.md stages/ladder.md
        stages/breaker.md prompts/lead.md prompts/defender.md prompts/reviewer.md
        prompts/writing.md templates/handoff.md templates/breaker.md
    """,
    "sessions": """
        prompts/session.md harness/README.md harness/claude-code.md
        harness/claude-code/task-session.md harness/claude-code/plan-talk.md
        harness/claude-code/second-opinion.md harness/claude-code/reviewer-guard.json
    """,
    "settings": """
        stages/init.md harness/claude-code/onboarding.md harness/claude-code/owner-steps.md
        templates/profile.md templates/persona.md
    """,
    "land-text": """
        stages/land.md stages/polish.md stages/conflict.md prompts/landing.md
        prompts/review.md prompts/merge.md prompts/small.md
        harness/claude-code/ask-merger.md harness/claude-code/review-tool.md
    """,
    "owner": "SKILL.md stages/status.md stages/away.md",
    "board-acts": "harness/claude-code/show-page.md harness/claude-code/take-screenshot.md",
    "ask": "harness/claude-code/ask-owner.md",
    "addons-flow": """
        stages/night.md stages/learn.md stages/nap.md prompts/proposals.md prompts/nap.md
        harness/claude-code/correction-hook.md harness/claude-code/start-nap.md
    """,
    "addons-outside": "harness/claude-code/ask-experts.md",
}
SKILLS = {
    "task": "lem-github lem-linear",
    "criteria": "lem-gate lem-interview-me lem-dialectic lem-root-cause",
    "ask": "lem-ask",
    "addons-outside": "lem-ask-expert lem-panel",
}
GUIDES = {
    "README.md", "AGENTS.md", "docs/board.md", "docs/flow.md", "docs/github-issues.md",
    "docs/install.md", "docs/linear.md", "docs/pull-request.md", "docs/when-lem-needs-you.md",
    "site/index.html",
}

# The old parser coalesces some surfaces that the rebuild splits. These are
# the handlers named in surfaces.md A and in the old project and land parsers.
PROJECT_COMMANDS = {
    "handoff": "cmd_handoff", "init": "cmd_init", "load": "cmd_load",
    "may-land": "cmd_may_land", "may-nap": "cmd_may_nap", "may-start": "cmd_may_start",
    "owner": "cmd_owner", "path": "cmd_path", "plan-file": "cmd_plan_file",
    "proposals": "proposals_command", "prune": "cmd_prune", "resume": "cmd_resume",
    "rules": "cmd_rules", "seat": "cmd_seat", "seat-again": "cmd_seat_again",
    "seat-failed": "cmd_seat_failed", "serial": "cmd_serial", "set": "cmd_set",
    "show": "load", "state": "cmd_state", "state-dir": "cmd_path", "task-dir": "cmd_task_dir",
    "tasks": "read_tasks", "ticket-step": "cmd_ticket_step", "waiting": "cmd_waiting",
    "worktree": "cmd_worktree", "worktree-dir": "cmd_worktree_dir",
}
COMMAND_GROUPS = {
    "ask": "ask", "board": "board-service", "cast": "addons-outside",
    "corrections": "addons-flow", "criteria": "criteria", "decisions": "criteria",
    "doctor": "settings", "experts": "addons-outside", "help": "tree", "issue": "task",
    "jev": "addons-outside", "picker": "addons-flow", "session": "sessions", "version": "tree",
}
COMMAND_LEAVES = {
    ("ask", "hook-stop"): "sessions",
    ("corrections", "collect"): "settings",
    ("corrections", "hook"): "sessions",
}

# The page is the source of navigation and display controls. For submitted
# actions, surfaces.md B names the handler that performs the act.
BOARD_ACTS = {
    "board-acts": {
        "New task": "start",
        "Backlog": "start-task drop-reviewer-item",
        "Waits for you": """
            open-session select-session plan-build breaker-help skip-personas-yes
            skip-personas-no approve-one-yes approve-one-no
        """,
        "Task panel": "open-session select-session",
        "Overview": """
            approve-plan-build approve-plan-drop breaker-help breaker-park breaker-drop
            skip-personas-yes skip-personas-no approve-one-yes approve-one-no
        """,
        "Criteria and decisions": "approve-yes approve-no approve-previous-release",
        "Merge confirmation": "confirm",
        "Park confirmation": "confirm",
        "Drop confirmation": "confirm",
    },
    "board-service": {"Waits for you": "turn-on test-push turn-off"},
    "addons-outside": {"Task panel": "open-inbox"},
}

RULING_GROUPS = {
    "What Lem is, and who it is for": "guides",
    "What Lem needs on the machine": "settings",
    "A request: its type, its track and its commands": "task",
    "The interview, the criteria and the personas": "criteria",
    "The plan, the build and the tests": "criteria",
    "A decision without him: the ladder, the experts and the breaker": "criteria",
    "The review, the pull request and the merge": "land-text",
    "A task's session, and whether he is there": "sessions",
    "The board and the pages for him": "board-views",
    "The settings, the seats and the tracker": "settings",
    "The README, the guides and the logo": "guides",
    "The lessons, the correction queue, the naps, the night and the free hour": "addons-flow",
    "Choices of the maintaining session": "close",
}

# Match a path to the implementation part 9 gives the landing step. Paths
# spanning multiple steps, or with no named landing implementation, go to land-text.
PATHS = {
    "land-base": """
        recovery conflict-with-the-base rebase-refused-by-git merge-only-change relands
    """,
    "land-checks": "red-base repair-limit fast-track-lowers-the-bar no-checks",
    "land-propose": "push-recorded-first",
    "land-merge": """
        base-moved-open-pr base-moved-after-a-safe-read two-unusable-answers
        two-unusable-answers-base-moved no-answer stale-tap owner-merge-refused-for-the-base
        github-refuses stop-after-the-intent-before-the-call stop-after-the-call
        forge-took-the-call-not-merged-yet merge-taken-text-not-updated retarget-before-the-read
        retarget-after-the-locked-read merge-on-github-between-look-and-call
        the-parent-by-merge-method base-checkout-cannot-follow closed-on-github
        clean-landed clean-the-forge-s-copy clean-dropped-or-answered clean-dirty
    """,
}
SEAMS = {
    "board-duties": "forge-look-fails duties-fail prune-fails",
    "land-review": "alike-read-list",
    "land-merge": "pr-text-edit-fails",
    "core": "step-lock-not-inherited",
    "sessions": "hooks-on-mismatch other-lem",
}

LEDGER_HEADER = ("id", "kind", "source", "what", "fate", "proof", "note")
JUDGED_HEADER = ("id", "step", "why")
CITATION = re.compile(
    r"`((?:tests|src|skills|agents|docs|hooks|tools|\.[^/ ]+)/[^:` ]+|AGENTS\.md|README\.md)"
    r"(?:::(\w+))?"
)


def in_groups(groups, name):
    return {step for step, names in groups.items() if name in names.split()}


def read_tsv(path, columns):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames != list(columns):
            raise ValueError(f"{path}: use the header {' '.join(columns)}")
        for row in reader:
            if None in row or None in row.values() or not row["id"].strip():
                raise ValueError(f"{path}:{reader.line_num}: fix the TSV row")
            yield row


def write_owners(path, owners):
    temp_path = None
    try:
        with NamedTemporaryFile(mode="w", dir=path.parent, encoding="utf-8",
                                newline="", delete=False) as stream:
            temp_path = Path(stream.name)
            writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
            writer.writerow(("id", "step"))
            writer.writerows(sorted(owners.items()))
        temp_path.replace(path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def file_steps(file, symbol=""):
    if file == "src/lem/land.py":
        if symbol in {"main via release.check", "main via release.stop"}:
            return {"task"}  # Part 9 gives the release stop to task.
        return in_groups(LAND_FUNCTIONS, symbol.split(" via ")[0])
    if file == "src/lem/project.py":
        return in_groups(PROJECT_FUNCTIONS, symbol)
    if file == "src/lem/serve.py":
        return in_groups(SERVE_FUNCTIONS, symbol)
    if file == "src/lem/__main__.py":
        return {"board-service"} if symbol == "look_for_server" else {"tree"}
    if file == "src/lem/release.py" and symbol == "log_stop":
        return {"task"}
    if file == "src/lem/criteria.py" and symbol in {"cmd_red", "cmd_inputs"}:
        return {"land-checks"}
    if file.startswith("src/lem/"):
        return in_groups(MODULES, Path(file).stem)
    if file == "tests/unit/test_land.py":
        return in_groups(LAND_CLASSES, symbol)
    if file == "tests/unit/test_serve.py":
        return in_groups(SERVE_CLASSES, symbol)
    if file.startswith("tests/unit/test_") and file.endswith(".py"):
        return in_groups(UNIT_FILES, Path(file).stem.removeprefix("test_"))
    if file.startswith("tests/") and file.endswith(".sh"):
        return in_groups(SHELL_FILES, Path(file).stem)
    if file.startswith("hooks/"):
        return {"sessions"}
    if file == "agents/lem-builder.md":
        return {"criteria"}
    if file.startswith("skills/lem/"):
        return in_groups(TEXT_FILES, file.removeprefix("skills/lem/"))
    if file.startswith("skills/") and file.endswith("/SKILL.md"):
        return in_groups(SKILLS, file.split("/")[1])
    if file.startswith(("tools/board-kit/", "skills/lem/assets/")):
        return {"board-pages"}
    if file == "tests/board-cdp.mjs":
        return {"browser"}
    if file in GUIDES:
        return {"guides"}
    if file == "docs/settings.md":
        return {"settings"}
    if file in {".github/workflows/ci.yml", ".claude-plugin/plugin.json"}:
        return {"core"}
    return set()


def command_steps(name):
    words = name.split()
    if len(words) < 2 or words[0] != "lem":
        return set()
    _, group, *args = words
    if not args and group in {"land", "project"}:
        return {"tree"}  # The two old command groups require a subcommand.
    leaf = args[0] if args else ""
    if group == "project":
        if leaf == "log":
            return {"task", "criteria"}  # The single old logger splits in the rebuild.
        return in_groups(PROJECT_FUNCTIONS, PROJECT_COMMANDS.get(leaf, ""))
    if group == "land":
        return in_groups(LAND_FUNCTIONS, "cmd_" + leaf.replace("-", "_"))
    if group == "serve":
        return {"board-service", "addons-outside"}  # One old parser for both option sets.
    if group in COMMAND_GROUPS:
        return {COMMAND_LEAVES.get((group, leaf), COMMAND_GROUPS[group])}
    return set()


def route_steps(handler, key):
    if key.endswith("/manifest.webmanifest"):
        return {"board-service"}
    if key.endswith("/assets/{asset}"):
        return {"board-pages"}
    handler = handler.rsplit(" → ", 1)[-1]
    module, dot, symbol = handler.partition(".")
    if dot and module != "Handler":
        return file_steps(f"src/lem/{module}.py", symbol)
    return file_steps("src/lem/serve.py", handler)


def act_steps(file, key):
    page, act = key.rsplit("/", 1)
    handlers = {step for step, pages in BOARD_ACTS.items() if act in pages.get(page, "").split()}
    if handlers:
        return handlers
    if page == "Question card":
        return {"ask"}
    if page == "Phone notifications":
        return {"board-service"}
    return file_steps(file)


def history_steps(references):
    places = []
    refs = list(CITATION.finditer(references))
    for index, ref in enumerate(refs):
        file, symbol = ref.groups()
        if file in {"src/lem/serve.py", "src/lem/project.py", "src/lem/land.py"}:
            end = refs[index + 1].start() if index + 1 < len(refs) else len(references)
            detail = references[ref.end():end]
            names = re.findall(r"`([\w.]+)`", detail[1:])
            before = re.search(r"`([\w.]+)` in $", references[:ref.start()])
            if before:
                names.append(before[1])
            for name in names:
                places.extend(file_steps(file, name))
            if file == "src/lem/serve.py" and "module docstring" in detail:
                if "look at the forge" in detail:
                    places.append("board-duties")
                elif "`merge_due`" not in detail:
                    places.append("board-service")
        else:
            places.extend(file_steps(file, symbol or ""))
    return set(places)


def candidates(row):
    identity, kind, source = row["id"], row["kind"], row["source"]
    if identity in BY_ID:
        return {BY_ID[identity]}
    key = identity.split(":", 1)[-1]
    file, _, section = source.partition(" — ")
    if kind == "unit":
        return file_steps(file, row["what"].split(".", 1)[0])
    if kind == "command":
        return command_steps(key)
    if kind == "route":
        return route_steps(section, key)
    if kind == "act":
        return act_steps(file, key)
    if kind == "event":
        # Resuming copies old events; those copies do not own the original rows.
        section = section.split(";", 1)[0]
        if file in {"src/lem/land.py", "src/lem/project.py", "src/lem/serve.py"}:
            return {step for symbol in section.split(", ") for step in file_steps(file, symbol)}
    if kind == "ruling":
        if file == "docs/rulings/history.md":
            return history_steps(section.partition(" — ")[2])
        step = RULING_GROUPS.get(section)
        return {step} if step else set()
    if kind == "path":
        return in_groups(PATHS, key) or {"land-text"}
    if kind == "seam":
        return in_groups(SEAMS, key)
    return file_steps(file, section)


def assign(rows, judgments):
    owners = {}
    missing = []
    multiple = {}
    for identity, row in rows.items():
        options = candidates(row)
        if identity in judgments:
            judgment = judgments[identity]
            if len(options) == 1:
                multiple[identity] = sorted(options) + [judgment["step"]]
                continue
            options = {judgment["step"]}
        if not options:
            missing.append(identity)
        elif len(options) > 1:
            multiple[identity] = sorted(options)
        else:
            owners[identity] = options.pop()
    return owners, {"no_owner": missing, "multiple_owners": multiple}


def index(path, columns):
    indexed = {}
    duplicates = set()
    for row in read_tsv(path, columns):
        identity = row["id"]
        if identity in indexed:
            duplicates.add(identity)
        indexed[identity] = row
    return indexed, sorted(duplicates)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, default=HERE / "rows.tsv")
    parser.add_argument("--judged", type=Path, default=HERE / "owners-judged.tsv")
    parser.add_argument("--out", type=Path, default=HERE / "owners.tsv")
    args = parser.parse_args()
    try:
        rows, duplicate_rows = index(args.rows, LEDGER_HEADER)
        judgments, duplicate_judgments = index(args.judged, JUDGED_HEADER)
        owners, issues = assign(rows, judgments)
        issues.update(
            duplicate_rows=duplicate_rows,
            duplicate_judgments=duplicate_judgments,
            unknown_judgments=sorted(judgments.keys() - rows.keys()),
            invalid_judgments=sorted(
                identity for identity, judgment in judgments.items()
                if judgment["step"] not in STEPS or not judgment["why"].strip()
            ),
        )
        if any(issues.values()):
            print(json.dumps(issues, indent=2, sort_keys=True))
            return 1
        write_owners(args.out, owners)
    except (OSError, ValueError, csv.Error) as error:
        print(json.dumps({"error": str(error)}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
