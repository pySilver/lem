"""The GitHub tracker (`lem.adapters.tracker_github`) against the `Tracker` port's contract, and
`lem issue` end to end, with a stand-in for `gh` on the PATH (`gh_issues_standin.py`): the issues
of acme/shop in a JSON file, answered in gh's own shapes, every call recorded. The repository is
a real checkout whose origin names GitHub and is never asked. No call leaves the machine."""

import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import msgspec
import pytest

from contract.gh_issues_standin import install
from contract.suites.outside import TrackerContract
from fakes.command import Ran, lem
from fakes.records import MOMENT, noted, record
from fakes.repo import git_env, run_git
from lem.adapters import tracker_github
from lem.kernel.errors import Refusal
from lem.ports.place import Place
from lem.records.landing.propose import Proposed
from lem.records.landing.record import Landing, Pull
from lem.records.tickets import Ticket, TicketStep
from lem.store import places, tasks

REPO = "acme/shop"
SLUG = "export-keeps-gift-note"
SETTINGS = '[branch]\nbase = "main"\n[tracker]\nkind = "github"\n'


def gift_note(**fields: object) -> dict[str, Any]:
    """Issue 42 of acme/shop as the stand-in keeps it."""
    return {
        "title": "The export drops the gift note",
        "body": "Each export drops the gift note.\n\nSee order 7.",
        "state": "OPEN",
        "labels": ["bug"],
        "author": "ann",
        "assignees": [],
        "comments": [
            {"author": "bob", "body": "Same here, on order 9."},
            {"author": "carl", "body": "And on order 11."},
            {"author": "dana", "body": "A third, on the second page."},
        ],
        **fields,
    }


@dataclass
class GhWorld:
    """A checkout whose origin is acme/shop on GitHub, the stand-in's state, and the
    environment that puts the stand-in first on PATH."""

    checkout: Path
    environ: dict[str, str]

    @property
    def state_file(self) -> Path:
        return Path(self.environ["GH_ISSUES_STATE"])

    def gh(self) -> dict[str, Any]:
        return json.loads(self.state_file.read_text())

    def gh_set(self, **fields: object) -> None:
        self.state_file.write_text(json.dumps({**self.gh(), **fields}))

    def issue(self, number: str = "42") -> dict[str, Any]:
        return self.gh()["repos"][REPO]["issues"][number]

    def edit_issue(self, number: str = "42", **fields: object) -> None:
        state = self.gh()
        state["repos"][REPO]["issues"][number].update(fields)
        self.state_file.write_text(json.dumps(state))

    def calls(self) -> list[list[str]]:
        return self.gh()["calls"]

    def writes(self) -> list[list[str]]:
        """The calls of gh that change an issue or one of its comments."""
        changing = (["issue", "edit"], ["issue", "comment"], ["issue", "close"])
        return [
            call
            for call in self.calls()
            if call[:2] in changing or (call[0] == "api" and "PATCH" in call)
        ]

    def adapter(self) -> tracker_github.TrackerGh:
        place = Place(
            checkout=self.checkout, home=self.checkout / "home", environ=self.environ
        )
        return tracker_github.bind(place)

    def lem(self, *args: str) -> Ran:
        return lem(*args, cwd=self.checkout, env=self.environ)

    def task(
        self,
        status: str,
        steps: tuple[str, ...] = (),
        line: str = "x",
        **fields: object,
    ) -> None:
        """A task of issue 42 in `status` with the steps written down."""
        parts = (step.partition(" ") for step in steps)
        written = tuple(
            msgspec.convert(
                {"act": act, "at": MOMENT, "login": login or None}, TicketStep
            )
            for act, _, login in parts
        )
        ticket = Ticket(tracker="github", id="#42", repo=REPO, steps=written)
        state = places.state_of(self.checkout)
        made = tasks.create(state, record(SLUG, status=status, ticket=ticket, **fields))
        tasks.update(state, SLUG, noted(line), made.revision)

    def steps(self) -> list[str]:
        ticket = tasks.read(places.state_of(self.checkout), SLUG).task.ticket
        found = ticket.steps if ticket else ()
        return [
            f"{step.act} {step.login}" if step.login else step.act for step in found
        ]


def gh_world(folder: Path, *, settings: str = SETTINGS) -> GhWorld:
    """A real checkout with origin on GitHub and Lem set up, and the stand-in for gh."""
    checkout = folder / "shop"
    checkout.mkdir(parents=True)
    run_git(checkout, "init", "-q", "-b", "main")
    run_git(checkout, "config", "remote.origin.url", "git@github.com:acme/shop.git")
    (checkout / ".lem").mkdir()
    (checkout / ".lem" / "settings.toml").write_text(settings, encoding="utf-8")
    places.state_of(checkout)
    begun = {
        "login": "octo-cat",
        "repos": {REPO: {"has_issues": True, "issues": {"42": gift_note()}}},
    }
    environ = {**git_env(), **install(folder / "gh", begun)}
    return GhWorld(checkout=checkout, environ=environ)


class TestTrackerGh(TrackerContract):
    @pytest.fixture(autouse=True)
    def folder(self, tmp_path: Path) -> None:
        self.world = gh_world(tmp_path)

    def tracker(self) -> tuple[tracker_github.TrackerGh, str]:
        return self.world.adapter(), "#42"


# The adapter's own words to gh


def test_every_call_names_origins_repository_and_reads_every_page_of_comments(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    adapter = world.adapter()
    assert adapter.origin() == REPO
    issue = adapter.issue(REPO, 42)
    assert (issue.state, issue.labels, issue.author) == ("open", ("bug",), "ann")
    found = adapter.comments(REPO, 42)
    assert [comment.author for comment in found] == ["bob", "carl", "dana"]
    assert all(REPO in " ".join(call) for call in world.calls())


def test_the_port_step_assigns_at_the_start_and_comments_and_closes_at_the_landing(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    adapter = world.adapter()
    started = adapter.step("#42", "start", "")
    assert started.did == ("added the assignee octo-cat",)
    assert adapter.step("#42", "start", "").did == ()
    landed = adapter.step("#42", "land", "Lem landed it.")
    assert landed.did == ("posted the comment", "closed the issue as completed")
    assert (world.issue()["state"], world.issue()["reason"]) == ("CLOSED", "COMPLETED")
    assert world.issue()["comments"][-1]["body"] == "Lem landed it."


def test_a_comment_goes_by_standard_input_and_a_refused_add_gives_ghs_words(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    adapter = world.adapter()
    adapter.comment(REPO, 42, "Line one.\n\nlem: x dropped\n")
    assert world.issue()["comments"][-1]["body"] == "Line one.\n\nlem: x dropped\n"
    world.gh_set(refuse_edit="GraphQL: octo-cat cannot be assigned to this issue")
    assert adapter.assign(REPO, 42, "octo-cat") == (
        "GraphQL: octo-cat cannot be assigned to this issue"
    )


def test_a_comment_is_edited_by_its_id_with_its_json_on_standard_input(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    adapter = world.adapter()
    adapter.comment(REPO, 42, "- [ ] one: a part\n\nlem: x parts\n")
    mine = adapter.comments(REPO, 42)[-1]
    assert mine.id == 42004
    adapter.edit_comment(REPO, mine.id, "- [x] one: a part\n\nlem: x parts\n")
    found = adapter.comments(REPO, 42)
    assert [comment.text for comment in found] == [
        "Same here, on order 9.",
        "And on order 11.",
        "A third, on the second page.",
        "- [x] one: a part\n\nlem: x parts\n",
    ]
    assert world.writes()[-1] == [
        "api",
        f"repos/{REPO}/issues/comments/42004",
        "--method",
        "PATCH",
        "--input",
        "-",
    ]


def test_gh_signed_out_and_an_issue_that_is_not_there_are_refused_with_their_fix(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    world.gh_set(login=None)
    with pytest.raises(Refusal) as signed_out:
        world.adapter().who()
    assert "gh auth login" in signed_out.value.fix
    with pytest.raises(Refusal) as missing:
        world.adapter().issue(REPO, 999)
    assert missing.value.code == "no-issue"


def test_an_origin_off_github_and_no_origin_are_refused_with_the_fix(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    run_git(
        world.checkout,
        "remote",
        "set-url",
        "origin",
        "https://gitlab.com/acme/shop.git",
    )
    with pytest.raises(Refusal) as elsewhere:
        world.adapter().origin()
    assert (
        "origin is https://gitlab.com/acme/shop.git, which is not a repository on GitHub"
        in elsewhere.value.why
    )
    run_git(world.checkout, "remote", "remove", "origin")
    with pytest.raises(Refusal) as none:
        world.adapter().origin()
    assert none.value.code == "no-origin"


# lem issue, each command


def test_lem_issue_check_says_the_repository_and_the_facts_of_the_onboarding(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    ran = world.lem("issue", "check")
    assert ran.code == 0, ran.stdout + ran.stderr
    found = ran.result()
    assert isinstance(found, dict)
    assert (
        found["repository"],
        found["signed_in"],
        found["issues_on"],
        found["has_issues"],
        found["missing"],
    ) == (REPO, True, True, True, [])
    assert "the issues of acme/shop are on" in str(ran.envelope()["say"])
    assert world.writes() == []
    listed = next(call for call in world.calls() if call[:2] == ["issue", "list"])
    assert listed[listed.index("--state") + 1] == "all"


def test_lem_issue_check_says_a_repository_with_no_issue(tmp_path: Path) -> None:
    world = gh_world(tmp_path)
    state = world.gh()
    state["repos"][REPO]["issues"] = {}
    world.state_file.write_text(json.dumps(state))
    ran = world.lem("issue", "check")
    assert ran.code == 0
    found = ran.result()
    assert isinstance(found, dict)
    assert found["has_issues"] is False
    assert "holds no issue yet" in str(ran.envelope()["say"])


def refusal_of(ran: Ran) -> dict[str, str]:
    assert ran.code == 1, ran.stdout + ran.stderr
    found = ran.envelope()["refusal"]
    assert isinstance(found, dict)
    return found


def test_lem_issue_check_refuses_each_missing_thing_with_its_fix(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    world.gh_set(login=None)
    refused = refusal_of(world.lem("issue", "check"))
    assert (refused["why"], refused["fix"]) == (
        "gh is not signed in to github.com",
        "gh auth login",
    )
    world.gh_set(login="octo-cat")
    state = world.gh()
    state["repos"][REPO]["has_issues"] = False
    world.state_file.write_text(json.dumps(state))
    refused = refusal_of(world.lem("issue", "check"))
    assert "the issues of acme/shop are off in its settings" in refused["why"]
    assert "turn Issues on" in refused["fix"]
    run_git(
        world.checkout,
        "remote",
        "set-url",
        "origin",
        "https://gitlab.com/acme/shop.git",
    )
    refused = refusal_of(world.lem("issue", "check"))
    assert "not a repository on GitHub" in refused["why"]
    assert (
        "git remote set-url origin https://github.com/OWNER/REPO.git" in refused["fix"]
    )


def test_lem_issue_check_with_no_gh_installed(tmp_path: Path) -> None:
    world = gh_world(tmp_path)
    nogh = tmp_path / "nogh"
    nogh.mkdir()
    git = shutil.which("git")
    assert git is not None
    (nogh / "git").symlink_to(git)
    world.environ["PATH"] = f"{nogh}{os.pathsep}{Path(sys.executable).parent}"
    refused = refusal_of(world.lem("issue", "check"))
    assert refused["why"].startswith("gh is not installed")
    assert "https://cli.github.com" in refused["fix"]


def test_lem_issue_check_needs_no_tracker_and_touches_no_settings(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path, settings='[branch]\nbase = "main"\n')
    settings = world.checkout / ".lem" / "settings.toml"
    assert world.lem("issue", "check").code == 0
    assert settings.read_text(encoding="utf-8") == '[branch]\nbase = "main"\n'


def test_lem_issue_read_gives_the_issue_and_refuses_another_tracker(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    ran = world.lem("issue", "read", "https://github.com/acme/shop/issues/42")
    assert ran.code == 0, ran.stdout + ran.stderr
    found = ran.result()
    assert isinstance(found, dict)
    assert (found["id"], found["ask_is"], len(found["comments"])) == ("#42", "text", 3)
    assert found["task_open"] == ["--ticket", "#42", "--ticket-repo", REPO]
    assert world.writes() == []
    (world.checkout / ".lem" / "settings.toml").write_text(
        '[branch]\nbase = "main"\n[tracker]\nkind = "linear"\n', encoding="utf-8"
    )
    assert (
        "the project's tracker is linear"
        in refusal_of(world.lem("issue", "read", "42"))["why"]
    )


def test_lem_issue_start_assigns_the_person_signed_in_and_is_refused_signed_out(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    world.task("building")
    world.gh_set(login=None)
    assert "gh auth login" in refusal_of(world.lem("issue", "start", SLUG))["fix"]
    assert world.steps() == []
    world.gh_set(login="octo-cat")
    ran = world.lem("issue", "start", SLUG)
    assert ran.code == 0, ran.stdout + ran.stderr
    assert world.issue()["assignees"] == ["octo-cat"]
    assert world.steps() == ["assigned octo-cat", "started"]


def test_lem_issue_land_comments_once_and_closes(tmp_path: Path) -> None:
    world = gh_world(tmp_path)
    world.task("landed", steps=("assigned octo-cat", "started"))
    state = places.state_of(world.checkout)
    pull = Pull(number=57, url="https://github.com/acme/shop/pull/57", title="Gift")
    proposed = Proposed(
        tip="c" * 40, base="a" * 40, green=True, who_acts="owner", at=MOMENT
    )
    landing = Landing(phase="ended", pull=pull, proposed=proposed)
    before = tasks.read(state, SLUG)
    tasks.update(
        state,
        SLUG,
        lambda found: msgspec.structs.replace(found, landing=landing),
        before.revision,
    )
    ran = world.lem("issue", "land", SLUG)
    assert ran.code == 0, ran.stdout + ran.stderr
    body = world.issue()["comments"][-1]["body"]
    assert "The pull request: https://github.com/acme/shop/pull/57, green" in body
    assert body.endswith(f"lem: {SLUG} landed\n")
    assert (world.issue()["state"], world.issue()["reason"]) == ("CLOSED", "COMPLETED")
    assert world.steps()[-2:] == ["commented", "landed"]


def test_lem_issue_drop_comments_and_removes_the_assignee_lem_added(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    world.task(
        "dropped", steps=("assigned octo-cat", "started"), line="the owner dropped it"
    )
    world.edit_issue(assignees=["octo-cat", "dana"])
    ran = world.lem("issue", "drop", SLUG)
    assert ran.code == 0, ran.stdout + ran.stderr
    assert world.issue()["assignees"] == ["dana"]
    assert world.issue()["comments"][-1]["body"] == (
        f"Lem dropped its task for this issue: the owner dropped it.\n\nlem: {SLUG} dropped\n"
    )
    assert "stays open" in str(ran.envelope()["say"])


def test_lem_issue_answer_comments_the_answer(tmp_path: Path) -> None:
    world = gh_world(tmp_path)
    world.task(
        "answered", steps=("started",), line="not a bug: the export keeps the note"
    )
    ran = world.lem("issue", "answer", SLUG)
    assert ran.code == 0, ran.stdout + ran.stderr
    assert world.issue()["comments"][-1]["body"] == (
        "Lem's investigation answered this issue: not a bug: the export keeps the note."
        f"\n\nlem: {SLUG} answered\n"
    )
    assert world.steps()[-1] == "answered"


def feature_of(world: GhWorld, *statuses: str) -> None:
    """The feature `x` of issue 42, queued after two parts in the statuses given."""
    state = places.state_of(world.checkout)
    ticket = Ticket(tracker="github", id="#42", repo=REPO)
    parts = ("save-endpoint", "ios-save-button")
    tasks.create(state, record("x", ticket=ticket, after=parts, ask="save items"))
    asks = ("the server saves an item", "the iOS app saves the item")
    for slug, ask, status in zip(parts, asks, statuses, strict=True):
        tasks.create(state, record(slug, ask=ask, status=status, part_of="x"))


def test_lem_issue_tick_posts_the_parts_comment_then_edits_it_only_when_it_differs(
    tmp_path: Path,
) -> None:
    world = gh_world(tmp_path)
    feature_of(world, "shaping", "queued")
    ran = world.lem("issue", "tick", "x")
    assert ran.code == 0, ran.stdout + ran.stderr
    assert world.issue()["comments"][-1]["body"] == (
        "- [ ] save-endpoint: the server saves an item\n"
        "- [ ] ios-save-button: the iOS app saves the item\n"
        "\n"
        "lem: x parts\n"
    )
    assert "0 of 2 parts landed" in str(ran.envelope()["say"])
    assert world.lem("issue", "tick", "x").code == 0
    assert len(world.writes()) == 1
    state = places.state_of(world.checkout)
    before = tasks.read(state, "save-endpoint")
    landed = msgspec.structs.replace(before.task, status="landed")
    tasks.update(
        state,
        "save-endpoint",
        lambda found: msgspec.structs.replace(found, task=landed),
        before.revision,
    )
    ran = world.lem("issue", "tick", "x")
    assert ran.code == 0, ran.stdout + ran.stderr
    assert world.issue()["comments"][-1]["body"].startswith(
        "- [x] save-endpoint: the server saves an item\n"
    )
    assert len(world.issue()["comments"]) == 4
    assert [call[0] for call in world.writes()] == ["issue", "api"]
    assert tasks.read(state, "x").task.ticket == Ticket(
        tracker="github", id="#42", repo=REPO
    )
