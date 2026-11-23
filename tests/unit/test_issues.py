"""The GitHub tracker, `lem issue` (skills/lem-github/scripts/issues.py), each step and each refusal,
over a stand-in for `gh` on PATH, in the manner of the one tests/lib.sh keeps: a Python file that a
shell script on PATH runs, which keeps the issues of each repository in a JSON file, and one line
of each call in that file's `calls`. The repository is a throwaway checkout whose origin names
GitHub and is never asked; a task is its files in the state folder, as `lem project` writes them.

    python3 -B -m unittest discover -s tests/unit
"""

import contextlib
import importlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HERE / "skills" / "lem-github" / "scripts"))
issues = importlib.import_module("issues")
project = issues.project

STANDIN = r"""
import json, os, sys
args = sys.argv[1:]
path = os.environ["GH_STANDIN"]
state = json.load(open(path))
state["calls"].append(args)
def save():
    with open(path + ".new", "w") as out:
        json.dump(state, out)
    os.replace(path + ".new", path)
def opt(key): return args[args.index(key) + 1] if key in args else None
def refuse(line):
    save()
    sys.exit(line)
def issue_of(repo, number):
    found = state["repos"].get(repo, {}).get("issues", {}).get(str(number))
    if found is None:
        refuse(f"GraphQL: Could not resolve to an issue or pull request with the number of {number}. (repository.issue)")
    return found
out = ""
login = state.get("login")
if args[:2] == ["auth", "status"]:
    if not login:
        refuse("You are not logged into any GitHub hosts. To log in, run: gh auth login")
elif args[:2] == ["api", "user"]:
    if not login:
        refuse("gh: To use GitHub CLI in automation, set the GH_TOKEN environment variable.")
    out = login
elif args[0] == "api" and args[1].endswith("/comments"):
    _, owner, name, _, number, _ = args[1].split("/")
    found = issue_of(f"{owner}/{name}", number)
    # two pages, as --paginate --slurp gives them for a long thread
    rows = [{"user": {"login": c["author"]}, "body": c["body"], "created_at": "2026-11-22T10:00:00Z", "html_url": "https://github.com/x"} for c in found["comments"]]
    out = json.dumps([rows[:2], rows[2:]])
elif args[:2] == ["repo", "view"]:
    repo = state["repos"].get(args[2])
    if repo is None:
        refuse(f"GraphQL: Could not resolve to a Repository with the name '{args[2]}'. (repository)")
    out = json.dumps({"hasIssuesEnabled": repo.get("has_issues", True)})
elif args[:2] == ["issue", "list"]:
    out = json.dumps([{"number": int(n)} for n in state["repos"][opt("--repo")].get("issues", {})][: int(opt("--limit"))])
elif args[:2] == ["issue", "view"]:
    repo, number = opt("--repo"), args[2]
    found = issue_of(repo, number)
    out = json.dumps({"number": int(number), "title": found["title"], "body": found["body"], "state": found["state"], "stateReason": found.get("reason"),
                      "labels": [{"name": n, "id": "L", "color": "fff", "description": ""} for n in found.get("labels", [])],
                      "url": found.get("url") or f"https://github.com/{repo}/issues/{number}", "author": {"login": found["author"], "name": "A"},
                      "assignees": [{"login": a, "name": "", "id": "U"} for a in found["assignees"]]})
elif args[:2] == ["issue", "edit"]:
    found = issue_of(opt("--repo"), args[2])
    if state.get("refuse_edit"):
        refuse(state["refuse_edit"])
    if opt("--add-assignee"):
        found["assignees"].append(opt("--add-assignee"))
    if opt("--remove-assignee"):
        found["assignees"] = [a for a in found["assignees"] if a != opt("--remove-assignee")]
    save()
    out = f"https://github.com/{opt('--repo')}/issues/{args[2]}"
elif args[:2] == ["issue", "comment"]:
    found = issue_of(opt("--repo"), args[2])
    assert opt("--body-file") == "-"
    found["comments"].append({"author": login, "body": sys.stdin.read()})
    save()
    out = f"https://github.com/{opt('--repo')}/issues/{args[2]}#issuecomment-1"
elif args[:2] == ["issue", "close"]:
    found = issue_of(opt("--repo"), args[2])
    found.update(state="CLOSED", reason=opt("--reason").upper())
    save()
else:
    refuse("gh stand-in: no such command: " + " ".join(args))
save()
print(out)
"""

OUTCOME = "# The gift note\n\n## Outcome\n\n**The export keeps the gift note of each order, as the shop shows it.**\n\nToday:\n\n1. The export drops it.\n"


class Issues(unittest.TestCase):
    """A repository whose origin is acme/shop on GitHub and whose tracker is github, with issue 42."""

    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.work = Path(folder.name)
        self.root = self.work / "shop"
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.root)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "remote",
                "add",
                "origin",
                "git@github.com:acme/shop.git",
            ],
            check=True,
        )
        (self.root / ".lem").mkdir()
        (self.root / ".lem" / "settings.toml").write_text(
            '[branch]\nbase = "main"\n[tracker]\nkind = "github"\n', encoding="utf-8"
        )
        self.root = Path(
            subprocess.run(
                ["git", "-C", str(self.root), "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        )
        bindir = self.work / "standin"
        bindir.mkdir()
        (bindir / "gh-standin.py").write_text(STANDIN, encoding="utf-8")
        (bindir / "gh").write_text(
            f"#!/bin/sh\nexec '{sys.executable}' -I -S '{bindir / 'gh-standin.py'}' \"$@\"\n",
            encoding="utf-8",
        )
        (bindir / "gh").chmod(0o755)
        self.gh_state = self.work / "gh.json"
        self.issues = {
            "42": {
                "title": "The export drops the gift note",
                "body": "Each export drops the gift note.\n\nSee order 7.",
                "state": "OPEN",
                "labels": ["bug"],
                "author": "ann",
                "assignees": [],
                "comments": [{"author": "bob", "body": "Same here, on order 9."}],
            }
        }
        self.gh_save(
            {
                "login": "octo-cat",
                "repos": {"acme/shop": {"has_issues": True, "issues": self.issues}},
                "calls": [],
            }
        )
        environ = {
            "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}",
            "GH_STANDIN": str(self.gh_state),
            "XDG_CONFIG_HOME": str(self.work / "config"),
        }
        saved = {key: os.environ.get(key) for key in environ}
        os.environ.update(environ)
        self.addCleanup(self.restore, saved)
        project.STATE_ROOTS.pop(self.root, None)
        self.addCleanup(project.STATE_ROOTS.pop, self.root, None)
        self.state = project.state_root(self.root)

    @staticmethod
    def restore(saved: dict) -> None:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def gh_save(self, state: dict) -> None:
        self.gh_state.write_text(json.dumps(state), encoding="utf-8")

    def gh(self) -> dict:
        return json.loads(self.gh_state.read_text(encoding="utf-8"))

    def gh_set(self, **fields) -> None:
        self.gh_save({**self.gh(), **fields})

    def issue(self, number: str = "42") -> dict:
        return self.gh()["repos"]["acme/shop"]["issues"][number]

    def edit_issue(self, number: str = "42", **fields) -> None:
        state = self.gh()
        state["repos"]["acme/shop"]["issues"][number].update(fields)
        self.gh_save(state)

    def writes(self) -> list[list[str]]:
        """The calls of gh that change an issue."""
        return [
            call
            for call in self.gh()["calls"]
            if call[:2] in (["issue", "edit"], ["issue", "comment"], ["issue", "close"])
        ]

    def task(
        self,
        slug: str,
        status: str,
        line: str = "task 1 of 2",
        ticket: str = "#42",
        repo: str = "acme/shop",
        steps: tuple[str, ...] = (),
        mark: bool = True,
    ) -> Path:
        directory = self.state / "tasks" / slug
        (directory / "reports").mkdir(parents=True, exist_ok=True)
        (directory / "ask.txt").write_text(
            "Each export drops the gift note.\n", encoding="utf-8"
        )
        (directory / "task.md").write_text(OUTCOME, encoding="utf-8")
        (directory / "state.md").write_text(
            f"2026-11-22T10:00Z {status}: {line}\n", encoding="utf-8"
        )
        (directory / "ticket.txt").write_text(ticket + "\n", encoding="utf-8")
        (directory / "ticket-repo.txt").write_text(repo + "\n", encoding="utf-8")
        if steps:
            (directory / "ticket-steps.txt").write_text(
                "\n".join(steps) + "\n", encoding="utf-8"
            )
        if mark:
            (self.state / "tickets").mkdir(exist_ok=True)
            (self.state / "tickets" / ticket.lstrip("#")).write_text(
                slug + "\n", encoding="utf-8"
            )
        return directory

    def set_status(self, slug: str, status: str, line: str) -> None:
        (self.state / "tasks" / slug / "state.md").write_text(
            f"2026-11-22T11:00Z {status}: {line}\n", encoding="utf-8"
        )

    def steps(self, slug: str) -> list[str]:
        file = self.state / "tasks" / slug / "ticket-steps.txt"
        return file.read_text(encoding="utf-8").splitlines() if file.is_file() else []

    def run_issue(self, *args: str) -> tuple[int, dict | None, str]:
        out, err = io.StringIO(), io.StringIO()
        code = 0
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                issues.main(["--repo", str(self.root), *args])
            except SystemExit as stop:
                code = stop.code if isinstance(stop.code, int) else 1
                if isinstance(stop.code, str):
                    err.write(stop.code)
        text = out.getvalue().strip()
        return code, json.loads(text) if text else None, err.getvalue()

    def ok(self, *args: str) -> dict:
        code, out, err = self.run_issue(*args)
        self.assertEqual(code, 0, err)
        return out

    def refused(self, *args: str) -> str:
        code, out, err = self.run_issue(*args)
        self.assertEqual(code, 1, out)
        self.assertTrue(err.startswith("lem issue: "), err)
        return err


class Read(Issues):
    """Criterion 3: an issue of origin, by its number or its address; nothing written; another repository refused."""

    def test_by_number_and_by_address_it_gives_the_issue_and_the_comments_apart_and_writes_nothing(
        self,
    ) -> None:
        for given in (
            "42",
            "#42",
            "https://github.com/acme/shop/issues/42",
            "https://github.com/ACME/shop/issues/42#issuecomment-5",
        ):
            with self.subTest(given=given):
                read = self.ok("read", given)
                self.assertEqual(
                    (read["id"], read["repository"], read["url"]),
                    ("#42", "acme/shop", "https://github.com/acme/shop/issues/42"),
                )
                self.assertEqual(
                    (
                        read["title"],
                        read["text"],
                        read["state"],
                        read["labels"],
                        read["author"],
                    ),
                    (
                        "The export drops the gift note",
                        "Each export drops the gift note.\n\nSee order 7.",
                        "open",
                        ["bug"],
                        "ann",
                    ),
                )
                self.assertEqual(
                    [(c["author"], c["text"]) for c in read["comments"]],
                    [("bob", "Same here, on order 9.")],
                )
                # only the text is the ask, never a comment; and the arguments of task-dir
                self.assertEqual(
                    (read["ask"], read["ask_is"]),
                    ("Each export drops the gift note.\n\nSee order 7.", "text"),
                )
                self.assertEqual(
                    read["task_dir"], ["--ticket", "#42", "--ticket-repo", "acme/shop"]
                )
        self.assertEqual(self.writes(), [])
        # every call named origin's repository
        self.assertTrue(
            all("acme/shop" in " ".join(call) for call in self.gh()["calls"])
        )

    def test_an_issue_with_no_text_has_its_title_as_the_ask_and_a_closed_one_says_so(
        self,
    ) -> None:
        self.edit_issue(body="", state="CLOSED", reason="COMPLETED")
        read = self.ok("read", "42")
        self.assertEqual(
            (read["ask"], read["ask_is"], read["state"], read["state_reason"]),
            ("The export drops the gift note", "title", "closed", "completed"),
        )

    def test_the_address_of_another_repository_is_refused_with_origin_named(
        self,
    ) -> None:
        said = self.refused("read", "https://github.com/upstream/shop/issues/42")
        self.assertIn(
            "names an issue of upstream/shop, and Lem reads the issues of origin, which is acme/shop",
            said,
        )
        self.assertEqual(self.gh()["calls"], [])

    def test_an_issue_moved_to_another_repository_is_refused(self) -> None:
        self.edit_issue(url="https://github.com/other/place/issues/3")
        self.assertIn(
            "an issue of another repository, and Lem reads the issues of origin, which is acme/shop",
            self.refused("read", "42"),
        )

    def test_the_number_of_a_pull_request_is_refused(self) -> None:
        self.edit_issue(url="https://github.com/acme/shop/pull/42", state="MERGED")
        self.assertIn(
            "#42 of acme/shop is a pull request (https://github.com/acme/shop/pull/42), not an issue",
            self.refused("read", "42"),
        )

    def test_a_word_that_is_no_issue_an_origin_off_github_and_another_tracker_are_refused(
        self,
    ) -> None:
        self.assertIn("is no issue's number or address", self.refused("read", "MBZ-12"))
        self.assertIn("issue 0 is no issue", self.refused("read", "#0"))
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "remote",
                "set-url",
                "origin",
                "https://gitlab.com/acme/shop.git",
            ],
            check=True,
        )
        self.assertIn(
            "origin is https://gitlab.com/acme/shop.git, which is not a repository on GitHub",
            self.refused("read", "42"),
        )
        (self.root / ".lem" / "settings.toml").write_text(
            '[branch]\nbase = "main"\n[tracker]\nkind = "linear"\n', encoding="utf-8"
        )
        self.assertIn("the project's tracker is linear", self.refused("read", "42"))


class Start(Issues):
    """Criterion 4: the assignee when the build starts."""

    def test_an_issue_with_no_assignee_gets_the_person_signed_in_and_a_second_start_writes_nothing(
        self,
    ) -> None:
        self.task("export-keeps-gift-note", "building")
        out = self.ok("start", "export-keeps-gift-note")
        self.assertEqual(self.issue()["assignees"], ["octo-cat"])
        self.assertEqual(
            self.steps("export-keeps-gift-note"), ["assigned octo-cat", "started"]
        )
        self.assertEqual(
            (out["did"], out["wrote"], out["says"]),
            (["added the assignee octo-cat"], ["assigned octo-cat", "started"], None),
        )
        calls = len(self.gh()["calls"])
        again = self.ok("start", "export-keeps-gift-note")
        self.assertEqual((again["did"], again["wrote"]), ([], []))
        self.assertEqual(len(self.gh()["calls"]), calls)

    def test_an_issue_with_another_assignee_keeps_it_and_the_owner_is_told_who(
        self,
    ) -> None:
        self.edit_issue(assignees=["dana"])
        self.task("export-keeps-gift-note", "planned")
        out = self.ok("start", "export-keeps-gift-note")
        self.assertEqual(self.issue()["assignees"], ["dana"])
        self.assertEqual(
            out["says"],
            "issue #42 of acme/shop is assigned to dana: Lem added nobody, and the build goes on",
        )
        self.assertEqual(self.steps("export-keeps-gift-note"), ["started"])
        self.assertEqual(self.writes(), [])

    def test_an_issue_the_person_signed_in_holds_already_is_left_with_no_line(
        self,
    ) -> None:
        self.edit_issue(assignees=["octo-cat"])
        self.task("export-keeps-gift-note", "building")
        out = self.ok("start", "export-keeps-gift-note")
        self.assertEqual(
            (out["says"], self.steps("export-keeps-gift-note"), self.writes()),
            (None, ["started"], []),
        )

    def test_when_gh_cannot_assign_the_owner_is_told_why_and_the_step_is_undone(
        self,
    ) -> None:
        self.gh_set(
            refuse_edit="GraphQL: octo-cat cannot be assigned to this issue (addAssigneesToAssignable)"
        )
        self.task("export-keeps-gift-note", "building")
        out = self.ok("start", "export-keeps-gift-note")
        self.assertIn(
            "gh could not make octo-cat the assignee of issue #42 of acme/shop (GraphQL: octo-cat cannot be assigned",
            out["says"],
        )
        self.assertEqual(
            self.steps("export-keeps-gift-note"),
            ["assigned octo-cat", "unassigned", "started"],
        )

    def test_a_start_cut_off_after_its_record_adds_the_login_only_while_the_issue_has_nobody(
        self,
    ) -> None:
        self.task("export-keeps-gift-note", "building", steps=("assigned octo-cat",))
        self.ok("start", "export-keeps-gift-note")
        self.assertEqual(self.issue()["assignees"], ["octo-cat"])
        self.task(
            "gift-note-two", "building", ticket="#43", steps=("assigned octo-cat",)
        )
        state = self.gh()
        state["repos"]["acme/shop"]["issues"]["43"] = {
            **self.issues["42"],
            "assignees": ["dana"],
            "comments": [],
        }
        self.gh_save(state)
        self.ok("start", "gift-note-two")
        self.assertEqual(self.issue("43")["assignees"], ["dana"])

    def test_gh_not_signed_in_is_refused_with_the_fix(self) -> None:
        self.gh_set(login=None)
        self.task("export-keeps-gift-note", "building")
        self.assertIn("gh auth login", self.refused("start", "export-keeps-gift-note"))
        self.assertEqual(self.steps("export-keeps-gift-note"), [])

    def test_a_resumed_task_takes_over_the_assignee_its_dropped_task_added(
        self,
    ) -> None:
        self.task(
            "gift-note",
            "dropped",
            line="breaker 1 waits",
            steps=("assigned octo-cat", "started"),
            mark=False,
        )
        new = self.task("gift-note-2", "held", line="breaker 1 waits for the owner")
        (new / "resumed-from.txt").write_text("gift-note\n", encoding="utf-8")
        self.edit_issue(assignees=["octo-cat"])
        out = self.ok("start", "gift-note-2")
        self.assertEqual(
            (out["wrote"], self.writes()), (["assigned octo-cat", "started"], [])
        )


class Refusals(Issues):
    """Each write's guards: the status, the task that holds the issue now, and origin's repository."""

    def test_each_step_refuses_a_status_it_does_not_belong_to(self) -> None:
        self.task("export-keeps-gift-note", "building")
        for step, wants in (
            ("land", "landed"),
            ("drop", "dropped"),
            ("answer", "answered"),
        ):
            with self.subTest(step=step):
                self.assertIn(
                    f"is building, and `lem issue {step}` belongs to a task that is {wants}",
                    self.refused(step, "export-keeps-gift-note"),
                )
        for status in ("landed", "dropped", "answered", "parked"):
            with self.subTest(status=status):
                self.set_status("export-keeps-gift-note", status, "x")
                self.assertIn(
                    f"is {status}: the start belongs to a task whose build starts",
                    self.refused("start", "export-keeps-gift-note"),
                )
        self.assertEqual(self.gh()["calls"], [])

    def test_another_repository_in_origin_is_refused_with_both_named_and_the_fix(
        self,
    ) -> None:
        self.task(
            "export-keeps-gift-note",
            "dropped",
            line="the owner dropped it",
            steps=("assigned octo-cat", "started"),
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "remote",
                "set-url",
                "origin",
                "https://github.com/acme/fork.git",
            ],
            check=True,
        )
        said = self.refused("drop", "export-keeps-gift-note")
        self.assertIn(
            "origin names acme/fork, and the task 'export-keeps-gift-note' came from issue #42 of acme/shop",
            said,
        )
        self.assertIn(
            "git remote set-url origin https://github.com/acme/shop.git", said
        )
        self.assertIn("the owner writes to issue #42 of acme/shop by hand", said)
        self.assertEqual(self.gh()["calls"], [])

    def test_a_task_a_resume_went_on_from_owes_nothing_and_each_write_names_the_holder(
        self,
    ) -> None:
        # decision 23: the mark moved to the resumed task
        self.task(
            "gift-note",
            "dropped",
            line="breaker 1 waits",
            steps=("assigned octo-cat", "started"),
            mark=False,
        )
        new = self.task("gift-note-2", "building")
        (new / "resumed-from.txt").write_text("gift-note\n", encoding="utf-8")
        old = next(
            task
            for task in project.read_tasks(self.root)
            if task["slug"] == "gift-note"
        )
        self.assertEqual(
            (old["ticket_owed"], old["ticket_held_by"]), ([], "gift-note-2")
        )
        said = self.refused("drop", "gift-note")
        self.assertIn(
            "issue #42 is held by the task 'gift-note-2' now, which went on from 'gift-note'",
            said,
        )
        self.assertEqual(self.gh()["calls"], [])

    def test_a_task_of_no_issue_and_a_task_that_is_not_there_are_refused(self) -> None:
        self.assertIn("no task 'gone'", self.refused("start", "gone"))
        directory = self.task("from-words", "building")
        (directory / "ticket.txt").unlink()
        self.assertIn("came from no issue", self.refused("start", "from-words"))


class Land(Issues):
    """Criterion 5: one comment, then the close as completed."""

    def landed(
        self,
        steps: tuple[str, ...] = ("assigned octo-cat", "started"),
        green: bool = True,
    ) -> None:
        directory = self.task(
            "export-keeps-gift-note", "landed", line="main a1b2..c3d4", steps=steps
        )
        (directory / "landing.json").write_text(
            json.dumps(
                {
                    "proposed": "c3d4",
                    "pr": {"number": 57, "url": "https://github.com/acme/shop/pull/57"},
                    "not_green": [] if green else ["a check failed"],
                }
            ),
            encoding="utf-8",
        )

    def test_the_comment_says_what_changed_the_pull_request_and_green_then_the_issue_is_closed(
        self,
    ) -> None:
        self.landed()
        self.edit_issue(assignees=["octo-cat"])
        out = self.ok("land", "export-keeps-gift-note")
        body = self.issue()["comments"][-1]["body"]
        self.assertEqual(
            body,
            "Lem landed the work of this issue: The export keeps the gift note of each order, as the shop shows it.\n\n"
            "The pull request: https://github.com/acme/shop/pull/57, green when it was proposed.\n\nlem: export-keeps-gift-note landed\n",
        )
        self.assertEqual(
            (self.issue()["state"], self.issue()["reason"]), ("CLOSED", "COMPLETED")
        )
        self.assertEqual(
            self.steps("export-keeps-gift-note"),
            ["assigned octo-cat", "started", "commented", "landed"],
        )
        self.assertEqual(
            out["did"], ["posted the comment", "closed the issue as completed"]
        )
        # a second land writes nothing
        calls = len(self.gh()["calls"])
        self.assertEqual(self.ok("land", "export-keeps-gift-note")["did"], [])
        self.assertEqual(len(self.gh()["calls"]), calls)
        # the landed task's issue keeps the assignee Lem added
        self.assertEqual(self.issue()["assignees"], ["octo-cat"])

    def test_not_green_is_said_and_a_closed_issue_stays_as_it_is(self) -> None:
        self.landed(green=False)
        self.edit_issue(state="CLOSED", reason="NOT_PLANNED")
        self.ok("land", "export-keeps-gift-note")
        self.assertIn(
            "pull/57, not green when it was proposed.",
            self.issue()["comments"][-1]["body"],
        )
        self.assertEqual(self.issue()["reason"], "NOT_PLANNED")
        self.assertFalse(
            any(call[:2] == ["issue", "close"] for call in self.gh()["calls"])
        )

    def test_a_session_cut_off_after_the_comment_posts_no_second_one_and_goes_on_to_the_close(
        self,
    ) -> None:
        self.landed()
        comments = [
            {"author": "bob", "body": "one"},
            {"author": "carl", "body": "two"},
            {
                "author": "octo-cat",
                "body": "Lem landed the work of this issue: x.\n\nlem: export-keeps-gift-note landed\n",
            },
        ]
        self.edit_issue(comments=comments)
        out = self.ok("land", "export-keeps-gift-note")
        # the marker is on the second page of the comments
        self.assertEqual(len(self.issue()["comments"]), 3)
        self.assertEqual(out["did"], ["closed the issue as completed"])
        self.assertEqual(
            self.steps("export-keeps-gift-note")[-2:], ["commented", "landed"]
        )

    def test_a_comment_of_another_task_does_not_count(self) -> None:
        self.landed()
        self.edit_issue(
            comments=[{"author": "octo-cat", "body": "lem: gift-note-old dropped"}]
        )
        self.ok("land", "export-keeps-gift-note")
        self.assertEqual(len(self.issue()["comments"]), 2)


class DropAndAnswer(Issues):
    """Criterion 6: one comment, the assignee Lem added goes, any other stays, the issue stays open."""

    def test_a_drop_comments_why_removes_the_assignee_lem_added_and_keeps_the_others(
        self,
    ) -> None:
        self.task(
            "export-keeps-gift-note",
            "dropped",
            line="the owner dropped it: the shop drops gift notes",
            steps=("assigned octo-cat", "started"),
        )
        self.edit_issue(assignees=["octo-cat", "dana"])
        out = self.ok("drop", "export-keeps-gift-note")
        self.assertEqual(
            self.issue()["comments"][-1]["body"],
            "Lem dropped its task for this issue: the owner dropped it: the shop drops gift notes.\n\nlem: export-keeps-gift-note dropped\n",
        )
        self.assertEqual(
            (self.issue()["assignees"], self.issue()["state"]), (["dana"], "OPEN")
        )
        self.assertEqual(
            out["says"],
            "issue #42 of acme/shop stays open: whether it closes is the owner's call",
        )
        self.assertEqual(
            self.steps("export-keeps-gift-note")[-2:], ["dropped", "unassigned"]
        )
        task = next(
            task
            for task in project.read_tasks(self.root)
            if task["slug"] == "export-keeps-gift-note"
        )
        self.assertEqual(task["ticket_owed"], [])
        # the ticket went back: its mark is gone
        self.assertFalse((self.state / "tickets" / "42").exists())
        self.assertEqual(self.ok("drop", "export-keeps-gift-note")["did"], [])

    def test_the_login_the_record_names_goes_whoever_is_signed_in_now(self) -> None:
        self.task(
            "export-keeps-gift-note",
            "dropped",
            line="the owner dropped it",
            steps=("assigned octo-cat", "started"),
        )
        self.edit_issue(assignees=["octo-cat"])
        self.gh_set(login="someone-else")
        self.ok("drop", "export-keeps-gift-note")
        self.assertEqual(self.issue()["assignees"], [])

    def test_an_assignee_lem_never_added_stays_and_a_removed_one_is_written_down_all_the_same(
        self,
    ) -> None:
        self.task(
            "export-keeps-gift-note",
            "dropped",
            line="the owner dropped it",
            steps=("started",),
        )
        self.edit_issue(assignees=["octo-cat"])
        self.ok("drop", "export-keeps-gift-note")
        self.assertEqual(self.issue()["assignees"], ["octo-cat"])
        self.task(
            "gift-note-two",
            "dropped",
            line="x",
            ticket="#43",
            steps=("assigned octo-cat", "started"),
        )
        state = self.gh()
        state["repos"]["acme/shop"]["issues"]["43"] = {
            **self.issues["42"],
            "assignees": [],
            "comments": [],
        }
        self.gh_save(state)
        self.ok("drop", "gift-note-two")
        self.assertEqual(self.steps("gift-note-two")[-1], "unassigned")
        self.assertFalse(
            any(call[:2] == ["issue", "edit"] for call in self.gh()["calls"])
        )

    def test_an_answer_comments_the_answer_and_where_and_the_report_stays_home(
        self,
    ) -> None:
        directory = self.task(
            "export-keeps-gift-note",
            "answered",
            line="not a bug: the export keeps the note",
            steps=("assigned octo-cat", "started"),
        )
        (directory / "investigation.md").write_text(
            "# Investigation\n", encoding="utf-8"
        )
        project.append_event(
            self.root,
            "investigation",
            "export-keeps-gift-note",
            {
                "type": "fix",
                "call": "not-a-bug",
                "line": "the export keeps the note in its last column",
                "where": "export.py:rows",
            },
        )
        self.edit_issue(assignees=["octo-cat"])
        out = self.ok("answer", "export-keeps-gift-note")
        self.assertEqual(
            self.issue()["comments"][-1]["body"],
            "Lem's investigation answered this issue: the export keeps the note in its last column (export.py:rows).\n\n"
            "The report is in the task's directory on the owner's machine, not on this issue.\n\nlem: export-keeps-gift-note answered\n",
        )
        self.assertEqual(
            (self.issue()["assignees"], self.issue()["state"]), ([], "OPEN")
        )
        self.assertIn("stays open", out["says"])

    def test_an_answer_owed_after_prune_removed_the_report_names_no_report(
        self,
    ) -> None:
        # an answered task past state.keep_days: prune left its small record, and its comment was never posted
        directory = self.task(
            "export-keeps-gift-note",
            "answered",
            line="not a bug: the export keeps the note",
            steps=("assigned octo-cat", "started"),
        )
        project.append_event(
            self.root,
            "investigation",
            "export-keeps-gift-note",
            {
                "type": "fix",
                "call": "not-a-bug",
                "line": "the export keeps the note in its last column",
                "where": "export.py:rows",
            },
        )
        self.assertFalse((directory / "investigation.md").exists())
        self.edit_issue(assignees=["octo-cat"])
        self.ok("answer", "export-keeps-gift-note")
        self.assertEqual(
            self.issue()["comments"][-1]["body"],
            "Lem's investigation answered this issue: the export keeps the note in its last column (export.py:rows).\n\n"
            "lem: export-keeps-gift-note answered\n",
        )

    def test_a_drop_cut_off_after_the_comment_posts_none_and_removes_the_assignee(
        self,
    ) -> None:
        self.task(
            "export-keeps-gift-note",
            "dropped",
            line="the owner dropped it",
            steps=("assigned octo-cat", "started"),
        )
        self.edit_issue(
            assignees=["octo-cat"],
            comments=[
                {
                    "author": "octo-cat",
                    "body": "Lem dropped ...\n\nlem: export-keeps-gift-note dropped",
                }
            ],
        )
        out = self.ok("drop", "export-keeps-gift-note")
        self.assertEqual(
            (len(self.issue()["comments"]), self.issue()["assignees"]), (1, [])
        )
        self.assertEqual(out["did"], ["removed the assignee octo-cat"])


class Check(Issues):
    """Criterion 7: the repository and its issues, or each missing thing with its fix; nothing written."""

    def test_all_there_says_the_repository_and_the_facts_of_the_onboarding(
        self,
    ) -> None:
        code, out, _ = self.run_issue("check")
        self.assertEqual(code, 0)
        self.assertEqual(
            (
                out["repository"],
                out["signed_in"],
                out["issues_on"],
                out["has_issues"],
                out["missing"],
            ),
            ("acme/shop", True, True, True, []),
        )
        self.assertIn("the issues of acme/shop are on", out["says"])
        self.assertEqual(self.writes(), [])
        # every state counts: gh lists the open issues alone by default
        listed = next(
            call for call in self.gh()["calls"] if call[:2] == ["issue", "list"]
        )
        self.assertIn("--state", listed)
        self.assertEqual(listed[listed.index("--state") + 1], "all")

    def test_a_repository_with_no_issue_is_said(self) -> None:
        state = self.gh()
        state["repos"]["acme/shop"]["issues"] = {}
        self.gh_save(state)
        code, out, _ = self.run_issue("check")
        self.assertEqual((code, out["has_issues"]), (0, False))
        self.assertIn("holds no issue yet", out["says"])

    def missing(self) -> list[dict]:
        code, out, _ = self.run_issue("check")
        self.assertEqual(code, 1)
        return out["missing"]

    def test_each_missing_thing_with_its_fix(self) -> None:
        self.gh_set(login=None)
        self.assertEqual(
            self.missing(),
            [{"what": "gh is not signed in to github.com", "fix": "gh auth login"}],
        )
        self.gh_set(login="octo-cat")
        state = self.gh()
        state["repos"]["acme/shop"]["has_issues"] = False
        self.gh_save(state)
        [off] = self.missing()
        self.assertIn("the issues of acme/shop are off in its settings", off["what"])
        self.assertIn("turn Issues on", off["fix"])
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "remote",
                "set-url",
                "origin",
                "https://gitlab.com/acme/shop.git",
            ],
            check=True,
        )
        [elsewhere] = self.missing()
        self.assertIn("not a repository on GitHub", elsewhere["what"])
        self.assertIn(
            "git remote set-url origin https://github.com/OWNER/REPO.git",
            elsewhere["fix"],
        )

    def test_gh_not_installed(self) -> None:
        # a PATH with git and no gh
        (self.work / "nogh").mkdir()
        (self.work / "nogh" / "git").symlink_to(shutil.which("git"))
        os.environ["PATH"] = str(self.work / "nogh")
        found = self.missing()
        self.assertEqual(found[0]["what"], "gh is not installed")
        self.assertIn("https://cli.github.com", found[0]["fix"])

    def test_the_check_needs_no_tracker_and_touches_no_settings(self) -> None:
        settings = self.root / ".lem" / "settings.toml"
        settings.write_text('[branch]\nbase = "main"\n', encoding="utf-8")
        code, _, _ = self.run_issue("check")
        self.assertEqual(
            (code, settings.read_text(encoding="utf-8")),
            (0, '[branch]\nbase = "main"\n'),
        )


if __name__ == "__main__":
    unittest.main()
