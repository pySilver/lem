#!/usr/bin/env python3
"""Assign each ledger row to the step that must account for it.

The rules below give each row one step. Then each step's `moves/STEP.tsv` gives a row the rules
gave it to the step that builds it; owners.tsv names the step that takes it, and
owners-judged.tsv keeps each move with its reason and the step that gave it.
"""

import argparse
import csv
import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence

HERE = Path(__file__).resolve().parent

# A row of a TSV file, by its header's column names.
type Row = dict[str, str]

STEPS = frozenset(
    [
        "ledger",
        "core",
        "tree",
        "slice-land",
        "slice-board",
        "slice-session",
        "trial-skeleton",
        "land-base",
        "land-checks",
        "land-review",
        "land-propose",
        "land-merge",
        "task",
        "criteria",
        "sessions",
        "settings",
        "land-text",
        "owner",
        "board-inputs",
        "board-views",
        "board-pages",
        "board-acts",
        "board-duties",
        "board-service",
        "ask",
        "addons-flow",
        "addons-outside",
        "journeys",
        "browser",
        "guides",
        "pack-trial",
        "mutation",
        "trials",
        "close",
        "cutover",
    ]
)

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
        merge_of pairs git_bytes git Task.need_landing Task.own_remote carry_merge
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
        cmd_merged forge_done noted moved_line follow may_merge step
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
# A class goes with the function it tests: MovedBase tests `moved_carry` and the
# standing merge (landing.md D, carry); TheNotesLines (`unfiled_lines`) and
# ResumedRead (`approved_after`) are refusals of `cmd_propose`; ExpectedTip is
# `cmd_merge`'s `--tip`; EventLog tests the readers of the journal, which core owns.
LAND_CLASSES = {
    "core": "EventLog",
    "land-base": "KeepReviews ConflictNames RebaseUnshown RebaseFailed MovedBase",
    "land-checks": """
        Bar FencedPlan UnclosedFence BarRefusal ChecksSay StaleBytecode RemoveBytecode
        Duration LastRun Overdue Resumed HeldRefusal SameChecks TakenFromPolish
        TheLongestWaitStartsFirst OneLineForTheMachine WantedGoesFirst
        ASecondWaitCountsFromItsStart TheLoadStillDecides AGoneRunLosesItsPlace
        TheWait WaitsBehindSays
    """,
    "land-review": """
        DefectsOutside TheItemOfADefect FailedAttempt ReadOfATip BarFile JevAsk
        TheBarJevReads TheFindingsUnderTheBar TheSpecOfAFinding TheReadOfEachFinding
        TheItemsThatMayHoldAFinding AnOverDefectOfARefutedItem JevOnTheLines
    """,
    "land-propose": "InterviewApproved TheNotesLines ResumedRead",
    "land-merge": """
        TheSquashBody WhoMerges MergeReview MergeSeat MergeBriefPictures MergeBriefTry
        ExpectedTip ForgeBase FirstDiffer ReadOfAMovedBase
    """,
}
# StartBehind (`release_behind`) and StoppedOpen test `act_start` and `act_session`.
SERVE_CLASSES = {
    "board-acts": "StartBehind StoppedOpen",
    "board-duties": """
        Duties MovedBaseRead StoppedSession DutyKey ForgeLookBesideAMerge Prune WorkingSession
    """,
    "board-service": """
        Door Actions Reads Notes StreamOpen Names KeepDays
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
    "README.md",
    "AGENTS.md",
    "docs/board.md",
    "docs/flow.md",
    "docs/github-issues.md",
    "docs/install.md",
    "docs/linear.md",
    "docs/pull-request.md",
    "docs/when-lem-needs-you.md",
    "site/index.html",
}

# The old parser coalesces some surfaces that the rebuild splits. These are
# the handlers named in surfaces.md A and in the old project and land parsers.
PROJECT_COMMANDS = {
    "handoff": "cmd_handoff",
    "init": "cmd_init",
    "load": "cmd_load",
    "log": "cmd_log",
    "may-land": "cmd_may_land",
    "may-nap": "cmd_may_nap",
    "may-start": "cmd_may_start",
    "owner": "cmd_owner",
    "path": "cmd_path",
    "plan-file": "cmd_plan_file",
    "proposals": "proposals_command",
    "prune": "cmd_prune",
    "resume": "cmd_resume",
    "rules": "cmd_rules",
    "seat": "cmd_seat",
    "seat-again": "cmd_seat_again",
    "seat-failed": "cmd_seat_failed",
    "serial": "cmd_serial",
    "set": "cmd_set",
    "show": "load",
    "state": "cmd_state",
    "state-dir": "cmd_path",
    "task-dir": "cmd_task_dir",
    "tasks": "read_tasks",
    "ticket-step": "cmd_ticket_step",
    "waiting": "cmd_waiting",
    "worktree": "cmd_worktree",
    "worktree-dir": "cmd_worktree_dir",
}
COMMAND_GROUPS = {
    "ask": "ask",
    "board": "board-service",
    "cast": "addons-outside",
    "corrections": "addons-flow",
    "criteria": "criteria",
    "decisions": "criteria",
    "doctor": "settings",
    "experts": "addons-outside",
    "help": "tree",
    "issue": "task",
    "jev": "addons-outside",
    "picker": "addons-flow",
    "session": "sessions",
    "version": "tree",
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

# The "Proof owner" column of landing.md E, row for row. A path row missing here
# has no owner, and owners.py refuses it; test_check.py holds the map to E.
PATHS = {
    "task": "start-over drop-during-a-step ticket-after-the-end",
    "land-base": """
        recovery no-checks teammate-commit conflict-with-the-base rebase-refused-by-git
        merge-only-change conflicting-pr-on-the-forge relands
    """,
    "land-checks": "red-base repair-limit fast-track-lowers-the-bar",
    "land-review": "fast-track-turns-careful",
    "land-propose": "push-recorded-first",
    "land-merge": """
        base-moved-open-pr base-moved-after-a-safe-read two-unusable-answers
        two-unusable-answers-base-moved no-answer stale-tap owner-merge-refused-for-the-base
        github-refuses transport-fault stop-or-lost-reply-around-the-merge-call
        forge-took-the-call-not-merged-yet merge-taken-text-not-updated retarget-before-the-read
        retarget-after-the-locked-read merge-on-github-between-look-and-call
        the-parent-by-merge-method base-checkout-cannot-follow closed-on-github
        clean-landed clean-the-forge-s-copy clean-dropped-or-answered clean-dirty
    """,
}
# Functions that part 9 gives to a step other than their module's.
MOVED_FUNCTIONS = {
    ("src/lem/release.py", "log_stop"): "task",
    ("src/lem/criteria.py", "cmd_red"): "land-checks",
    ("src/lem/criteria.py", "cmd_inputs"): "land-checks",
}
SEAMS = {
    "board-duties": "forge-look-fails duties-fail prune-fails",
    "land-review": "alike-read-list",
    "land-merge": "pr-text-edit-fails",
    "core": "step-lock-not-inherited",
    "sessions": "hooks-on-mismatch other-lem",
}

LEDGER_HEADER = ("id", "kind", "source", "what", "fate", "proof", "note")
# A row of owners-judged.tsv with no `from` is the design's judgment, kept by hand; a row with a
# `from` is a move, which owners.py writes again from moves/ on each run.
JUDGED_HEADER = ("id", "step", "why", "from")
MOVES_HEADER = ("id", "to", "why")
# The lists of the moves owners.py refuses, as owners.py and check.py name them; beside them,
# `move_files_unknown` names a moves file of no step.
MOVE_ISSUES = (
    "move_unknown_rows",
    "move_bad_step",
    "move_without_why",
    "move_twice",
    "move_not_owned",
    "move_loop",
)
CITATION = re.compile(
    r"`((?:tests|src|skills|agents|docs|hooks|tools|\.[^/ ]+)/[^:` ]+|AGENTS\.md|README\.md)"
    r"(?:::(\w+))?"
)


def in_groups(groups: Mapping[str, str], name: str) -> set[str]:
    return {step for step, names in groups.items() if name in names.split()}


def read_tsv(path: Path, columns: Sequence[str]) -> Iterator[Row]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames != list(columns):
            raise ValueError(f"{path}: use the header {' '.join(columns)}")
        for row in reader:
            if None in row or None in row.values() or not row["id"].strip():
                raise ValueError(f"{path}:{reader.line_num}: fix the TSV row")
            yield row


def write_table(
    path: Path, header: Sequence[str], rows: Iterable[Sequence[str]]
) -> None:
    # A plain open, so the file gets the umask's mode (NamedTemporaryFile gives 0600).
    temp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temp_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows)
        temp_path.replace(path)
    finally:
        temp_path.unlink(missing_ok=True)


def write_owners(path: Path, owners: Mapping[str, str]) -> None:
    write_table(path, ("id", "step"), sorted(owners.items()))


def file_steps(file: str, symbol: str = "") -> set[str]:
    if file.startswith("src/lem/"):
        return module_steps(file, symbol)
    if file.startswith("tests/"):
        return suite_file_steps(file, symbol)
    if file.startswith(("hooks/", "agents/", "skills/", "tools/")):
        return plugin_file_steps(file)
    return other_file_steps(file)


def module_steps(file: str, symbol: str) -> set[str]:
    """A module of src/lem/: by its function where part 9 splits the module."""
    if file == "src/lem/land.py":
        return land_steps(symbol)
    if file == "src/lem/project.py":
        return in_groups(PROJECT_FUNCTIONS, symbol)
    if file == "src/lem/serve.py":
        return in_groups(SERVE_FUNCTIONS, symbol)
    if file == "src/lem/__main__.py":
        return {"board-service"} if symbol == "look_for_server" else {"tree"}
    if step := MOVED_FUNCTIONS.get((file, symbol)):
        return {step}
    return in_groups(MODULES, Path(file).stem)


def land_steps(symbol: str) -> set[str]:
    if symbol in {"main via release.check", "main via release.stop"}:
        return {"task"}  # Part 9 gives the release stop to task.
    return in_groups(LAND_FUNCTIONS, symbol.split(" via ", maxsplit=1)[0])


def suite_file_steps(file: str, symbol: str) -> set[str]:
    """A file of tests/: a unit file by its class where part 9 splits the file."""
    if file == "tests/unit/test_land.py":
        return in_groups(LAND_CLASSES, symbol)
    if file == "tests/unit/test_serve.py":
        return in_groups(SERVE_CLASSES, symbol)
    if file.startswith("tests/unit/test_") and file.endswith(".py"):
        return in_groups(UNIT_FILES, Path(file).stem.removeprefix("test_"))
    if file.endswith(".sh"):
        return in_groups(SHELL_FILES, Path(file).stem)
    if file == "tests/board-cdp.mjs":
        return {"browser"}
    return set()


def plugin_file_steps(file: str) -> set[str]:
    """A file of the plugin outside src/: a hook, an agent, a skill's text, the board kit."""
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
    return set()


def other_file_steps(file: str) -> set[str]:
    """A guide, the settings' page, the CI workflow or the plugin's manifest."""
    if file in GUIDES:
        return {"guides"}
    if file == "docs/settings.md":
        return {"settings"}
    if file in {".github/workflows/ci.yml", ".claude-plugin/plugin.json"}:
        return {"core"}
    return set()


def command_steps(name: str) -> set[str]:
    words = name.split()
    if len(words) < 2 or words[0] != "lem":
        return set()
    _, group, *args = words
    if not args and group in {"land", "project"}:
        return {"tree"}  # The two old command groups require a subcommand.
    return command_group_steps(group, args[0] if args else "")


def command_group_steps(group: str, leaf: str) -> set[str]:
    if group == "project":
        return in_groups(PROJECT_FUNCTIONS, PROJECT_COMMANDS.get(leaf, ""))
    if group == "land":
        return in_groups(LAND_FUNCTIONS, "cmd_" + leaf.replace("-", "_"))
    if group == "serve":
        # `serve.main` is "the rest" of serve.py; the peers options are its flags.
        return {"board-service"}
    if group in COMMAND_GROUPS:
        return {COMMAND_LEAVES.get((group, leaf), COMMAND_GROUPS[group])}
    return set()


def route_steps(handler: str, key: str) -> set[str]:
    if key.endswith("/manifest.webmanifest"):
        return {"board-service"}
    if key.endswith("/assets/{asset}"):
        return {"board-pages"}
    handler = handler.rsplit(" → ", 1)[-1]
    module, dot, symbol = handler.partition(".")
    if dot and module != "Handler":
        return file_steps(f"src/lem/{module}.py", symbol)
    return file_steps("src/lem/serve.py", handler)


def act_steps(file: str, key: str) -> set[str]:
    page, act = key.rsplit("/", 1)
    handlers = {
        step for step, pages in BOARD_ACTS.items() if act in pages.get(page, "").split()
    }
    if handlers:
        return handlers
    if page == "Question card":
        return {"ask"}
    if page == "Phone notifications":
        return {"board-service"}
    return file_steps(file)


def history_steps(references: str) -> set[str]:
    places: list[str] = []
    refs = list(CITATION.finditer(references))
    for index, ref in enumerate(refs):
        file, symbol = ref.groups()
        if file in {"src/lem/serve.py", "src/lem/project.py", "src/lem/land.py"}:
            end = refs[index + 1].start() if index + 1 < len(refs) else len(references)
            detail = references[ref.end() : end]
            names = re.findall(r"`([\w.]+)`", detail[1:])
            before = re.search(r"`([\w.]+)` in $", references[: ref.start()])
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


class Source(NamedTuple):
    """Where a row comes from: its file, the section after the file, the id after its kind."""

    file: str
    section: str
    key: str
    what: str


def unit_steps(source: Source) -> set[str]:
    return file_steps(source.file, source.what.split(".", 1)[0])


def command_row_steps(source: Source) -> set[str]:
    return command_steps(source.key)


def route_row_steps(source: Source) -> set[str]:
    return route_steps(source.section, source.key)


def act_row_steps(source: Source) -> set[str]:
    return act_steps(source.file, source.key)


def event_steps(source: Source) -> set[str]:
    # Resuming copies old events; those copies do not own the original rows.
    section = source.section.split(";", 1)[0]
    if source.file in {"src/lem/land.py", "src/lem/project.py", "src/lem/serve.py"}:
        return {
            step
            for symbol in section.split(", ")
            for step in file_steps(source.file, symbol)
        }
    return file_steps(source.file, section)


def ruling_steps(source: Source) -> set[str]:
    if source.file == "docs/rulings/history.md":
        return history_steps(source.section.partition(" — ")[2])
    step = RULING_GROUPS.get(source.section)
    return {step} if step else set()


def path_steps(source: Source) -> set[str]:
    return in_groups(PATHS, source.key)


def seam_steps(source: Source) -> set[str]:
    return in_groups(SEAMS, source.key)


def section_steps(source: Source) -> set[str]:
    return file_steps(source.file, source.section)


# The rule that gives a row its owners, by the row's kind; any other kind goes by its file
# and section.
KIND_STEPS: dict[str, Callable[[Source], set[str]]] = {
    "unit": unit_steps,
    "command": command_row_steps,
    "route": route_row_steps,
    "act": act_row_steps,
    "event": event_steps,
    "ruling": ruling_steps,
    "path": path_steps,
    "seam": seam_steps,
}


def candidates(row: Row) -> set[str]:
    identity = row["id"]
    if identity in BY_ID:
        return {BY_ID[identity]}
    file, _, section = row["source"].partition(" — ")
    source = Source(file, section, identity.split(":", 1)[-1], row["what"])
    return KIND_STEPS.get(row["kind"], section_steps)(source)


def assign(
    rows: Mapping[str, Row], judgments: Mapping[str, Row]
) -> tuple[dict[str, str], dict[str, list[str] | dict[str, list[str]]]]:
    owners: dict[str, str] = {}
    missing: list[str] = []
    multiple: dict[str, list[str]] = {}
    for identity, row in rows.items():
        options = candidates(row)
        if identity in judgments:
            judgment = judgments[identity]
            if len(options) == 1:
                multiple[identity] = [*sorted(options), judgment["step"]]
                continue
            options = {judgment["step"]}
        if not options:
            missing.append(identity)
        elif len(options) > 1:
            multiple[identity] = sorted(options)
        else:
            owners[identity] = options.pop()
    return owners, {"no_owner": missing, "multiple_owners": multiple}


def index_rows(table: Iterable[Row]) -> tuple[dict[str, Row], list[str]]:
    indexed: dict[str, Row] = {}
    duplicates: set[str] = set()
    for row in table:
        identity = row["id"]
        if identity in indexed:
            duplicates.add(identity)
        indexed[identity] = row
    return indexed, sorted(duplicates)


def index(path: Path, columns: Sequence[str]) -> tuple[dict[str, Row], list[str]]:
    return index_rows(read_tsv(path, columns))


def read_judged(path: Path) -> tuple[dict[str, Row], list[str], list[Row]]:
    """The design's judgments by id, the ids it judges twice, and the moves the file keeps."""
    table = list(read_tsv(path, JUDGED_HEADER))
    judgments, duplicates = index_rows(row for row in table if not row["from"].strip())
    return judgments, duplicates, [row for row in table if row["from"].strip()]


class Move(NamedTuple):
    """A line of moves/GIVER.tsv: the row the step GIVER gives to the step TO, and why."""

    giver: str
    row: str
    to: str
    why: str

    def entry(self) -> dict[str, str]:
        return {"id": self.row, "from": self.giver, "to": self.to}

    def judged(self) -> Row:
        return {"id": self.row, "step": self.to, "why": self.why, "from": self.giver}


# The refused moves, by the name of their list in MOVE_ISSUES.
type MoveIssues = defaultdict[str, list[dict[str, str]]]


def read_moves(folder: Path) -> tuple[list[Move], list[str]]:
    """Every line of each moves/STEP.tsv, and the files named for no step."""
    moves: list[Move] = []
    unknown: list[str] = []
    for path in sorted(folder.glob("*.tsv")):
        if path.stem not in STEPS:
            unknown.append(path.name)
            continue
        moves.extend(
            Move(path.stem, line["id"], line["to"].strip(), line["why"].strip())
            for line in read_tsv(path, MOVES_HEADER)
        )
    return moves, unknown


def move_refusal(move: Move, rows: Mapping[str, Row]) -> str | None:
    """The list a move goes on by itself, whoever owns its row."""
    if move.row not in rows:
        return "move_unknown_rows"
    if move.to not in STEPS or move.to == move.giver:
        return "move_bad_step"
    if not move.why:
        return "move_without_why"
    return None


def follow(
    start: str | None, moves: Mapping[str, Move], issues: MoveIssues
) -> tuple[str | None, list[Move]]:
    """The owner at the end of a row's chain of moves, and the moves the chain takes.

    The chain starts at the owner the rules give and goes from giver to giver, so neither the
    order of the files nor the order of their lines changes where it ends. A move by a step the
    chain never reaches is refused, and so is a move back to a step of the chain.
    """
    owner = start
    chain = [] if start is None else [start]
    taken: list[Move] = []
    givers: set[str] = set()
    while owner is not None and (move := moves.get(owner)) is not None:
        givers.add(owner)
        if move.to in chain:
            issues["move_loop"].append(
                {"id": move.row, "chain": " > ".join([*chain, move.to])}
            )
            break
        taken.append(move)
        owner = move.to
        chain.append(owner)
    issues["move_not_owned"].extend(
        {**move.entry(), "owner": owner or ""}
        for giver, move in sorted(moves.items())
        if giver not in givers
    )
    return owner, taken


def apply_moves(
    owners: Mapping[str, str],
    moves: Iterable[Move],
    rows: Mapping[str, Row],
    issues: MoveIssues,
) -> tuple[dict[str, str], list[Row]]:
    """The owner of each row after the moves, and each move taken as a row of owners-judged."""
    by_row: defaultdict[str, defaultdict[str, list[Move]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for move in moves:
        if refusal := move_refusal(move, rows):
            issues[refusal].append(move.entry())
        else:
            by_row[move.row][move.giver].append(move)
    moved = dict(owners)
    hops: list[Row] = []
    for identity, givers in sorted(by_row.items()):
        once: dict[str, Move] = {}
        for giver, given in givers.items():
            if len(given) == 1:
                once[giver] = given[0]
            else:
                issues["move_twice"].extend(move.entry() for move in given)
        owner, taken = follow(owners.get(identity), once, issues)
        if owner is not None:
            moved[identity] = owner
        hops.extend(move.judged() for move in taken)
    return moved, hops


def judged_table(judgments: Mapping[str, Row], hops: Iterable[Row]) -> list[Row]:
    """owners-judged.tsv by id: the design's judgment first, then each move in its chain's order."""
    by_id: defaultdict[str, list[Row]] = defaultdict(list)
    for identity, judgment in judgments.items():
        by_id[identity].append(judgment)
    for hop in hops:
        by_id[hop["id"]].append(hop)
    return [row for identity in sorted(by_id) for row in by_id[identity]]


def in_order(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(entries, key=lambda entry: sorted(entry.items()))


class Assigned(NamedTuple):
    """What owners.py gives: each row's owner, the table of owners-judged.tsv, and its refusals."""

    owners: dict[str, str]
    judged: list[Row]
    issues: dict[str, object]


def owners_of(rows_path: Path, judged_path: Path, moves_folder: Path) -> Assigned:
    rows, duplicate_rows = index(rows_path, LEDGER_HEADER)
    judgments, duplicate_judgments, _ = read_judged(judged_path)
    ruled, issues = assign(rows, judgments)
    moves, unknown_files = read_moves(moves_folder)
    move_issues: MoveIssues = defaultdict(list)
    owners, hops = apply_moves(ruled, moves, rows, move_issues)
    return Assigned(
        owners,
        judged_table(judgments, hops),
        {
            **issues,
            "duplicate_rows": duplicate_rows,
            "duplicate_judgments": duplicate_judgments,
            "unknown_judgments": sorted(judgments.keys() - rows.keys()),
            "invalid_judgments": sorted(
                identity
                for identity, judgment in judgments.items()
                if judgment["step"] not in STEPS or not judgment["why"].strip()
            ),
            # A misspelled step in a map above would own rows no builder reads.
            "unknown_steps": sorted(
                identity for identity, step in ruled.items() if step not in STEPS
            ),
            "move_files_unknown": unknown_files,
            **{name: in_order(move_issues[name]) for name in MOVE_ISSUES},
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--rows", type=Path, default=HERE / "rows.tsv")
    parser.add_argument(
        "--judged",
        type=Path,
        default=HERE / "owners-judged.tsv",
        help="the design's judgments, read; written again with the moves",
    )
    parser.add_argument("--out", type=Path, default=HERE / "owners.tsv")
    parser.add_argument(
        "--moves",
        type=Path,
        default=HERE / "moves",
        help="the folder of each step's moves/STEP.tsv",
    )
    args = parser.parse_args()
    try:
        assigned = owners_of(args.rows, args.judged, args.moves)
        if any(assigned.issues.values()):
            print(json.dumps(assigned.issues, indent=2, sort_keys=True))
            return 1
        write_owners(args.out, assigned.owners)
        write_table(
            args.judged,
            JUDGED_HEADER,
            ([row[column] for column in JUDGED_HEADER] for row in assigned.judged),
        )
    except (OSError, ValueError, csv.Error) as error:
        print(json.dumps({"error": str(error)}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
