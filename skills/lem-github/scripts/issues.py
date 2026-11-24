"""The GitHub tracker of Lem: a repository's issues, through GitHub's `gh`, for the
`lem-github` skill.

An issue is one more place an ask comes from. This script reads one, and keeps it true
while Lem works: an assignee when the build starts, one comment and a close when the
task lands, one comment when it is dropped or answered. The repository is origin's,
always: every call of `gh` names it with `--repo OWNER/REPO`, read from
`remote.origin.url`, so a fork whose `gh` default is its upstream still reads and writes
its own issues.

    lem issue check          whether this repository's issues can be Lem's tracker: origin on
                             GitHub, `gh` installed and signed in, the issues on; and whether the
                             repository holds at least one issue of any state. Writes nothing.
                             Exit 1 when something is missing, each with its fix
    lem issue read ID|URL    one issue of origin's repository, by its number (42, #42) or its
                             address: its title, its text as written, open or closed, its labels,
                             its address, its author, its assignees and its comments apart from the
                             text. Writes nothing. The address of another repository's issue is refused
    lem issue start SLUG     the build of the task started: an issue with no assignee gets the
                             person signed in to `gh`; an issue with one keeps its assignees
    lem issue land SLUG      the task landed: one comment, then the issue is closed as completed
    lem issue drop SLUG      the task was dropped: one comment, and the assignee Lem added goes
    lem issue answer SLUG    the task ended with an answer: one comment with it, and the assignee
                             Lem added goes

Each write takes the slug alone and reads its words from the task's record, so any
session, or the owner, can run a step a task still owes. Before it writes, it reads the
task in `lem project tasks` and refuses a status the step does not belong to, a task
whose issue another task holds now (a resume went on from it), and an origin that names
another repository than the one the issue was read from. What it did is written down
through `lem project ticket-step` after `gh` took it, and never done twice; the
assignee's step is written before the add, with the login, since a removal reads the
assignees first. Each comment's last line is `lem: SLUG STEP`, which the script adds,
and before a comment the issue's comments are read for that line: a session cut off
after the post posts no second one.

Each command prints one JSON object. The fields of `gh issue view --json` and the flags
of `gh issue edit`, `gh issue comment`, `gh issue close`, `gh issue list`,
`gh repo view`, `gh api` and `gh auth status` were read from their `--help` in gh
2.101.0 (2026-09-15), on 2026-11-22; no call of this script has run against a real
repository yet.
"""  # noqa: E501 - the usage table of `--help` keeps its columns

import sys

if sys.version_info < (3, 11):
    sys.exit(
        "issues.py: Lem needs Python 3.11 or newer, and this python3 is "
        f"{sys.version.split()[0]}; put a newer one first on PATH, "
        "or run this file with it"
    )

import argparse
import contextlib
import importlib
import io
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

# Lem's own scripts, beside this skill in the same plugin
SCRIPTS = Path(__file__).resolve().parents[2] / "lem" / "scripts"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
# the settings, the tasks and the record of each step
project = importlib.import_module("project")
# the release a task began on, and the rule that stops a command for a task two
# releases back
lem_release = importlib.import_module("lem_release")

# origin on GitHub, in the three forms git takes, as OWNER/REPO
ORIGIN = re.compile(
    r"(?:https://github\.com/|ssh://git@github\.com/|git@github\.com:)(?P<repo>[^/\s:]+/[^/\s]+?)(?:\.git)?/?"
)
# an issue's address, with what GitHub may put after it (a comment's anchor, a query)
ADDRESS = re.compile(
    r"https://github\.com/(?P<repo>[^/\s]+/[^/\s]+)/issues/(?P<number>[0-9]+)(?:[/?#]\S*)?"
)
# the fields of `gh issue view --json` a read gives (gh 2.101.0: assignees, author,
# body, labels, number, state, stateReason, title and url are among its JSON FIELDS)
VIEW = "number,title,body,state,stateReason,labels,url,author,assignees"
# the status each step belongs to; `start` belongs to every status but an ended or
# parked one
STATUS_OF = {"land": "landed", "drop": "dropped", "answer": "answered"}
# the step of `lem project ticket-step` each comment writes down, and the word of its
# last line
COMMENTED = {"land": "commented", "drop": "dropped", "answer": "answered"}
LAST_WORD = {"land": "landed", "drop": "dropped", "answer": "answered"}
INSTALL_GH = (
    "install GitHub's command gh (https://cli.github.com), "
    "then sign it in with `gh auth login`"
)


class IssueError(Exception):
    pass


def gh(root: Path, *args: str, stdin: str = "") -> subprocess.CompletedProcess:
    """One call of `gh`, in the checkout, with no prompt: a call that would ask
    fails instead."""
    if not shutil.which("gh"):
        raise IssueError(f"gh is not on PATH: {INSTALL_GH}, then run this again")
    return subprocess.run(
        ["gh", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        input=stdin,
        env={**os.environ, "GH_PROMPT_DISABLED": "1"},
    )


def why(ran: subprocess.CompletedProcess) -> str:
    """What gh said when it refused, on one line."""
    said = (ran.stderr or ran.stdout).strip().splitlines()
    return said[0].strip() if said else f"it exited {ran.returncode} and said nothing"


def gh_ok(root: Path, *args: str, stdin: str = "") -> str:
    ran = gh(root, *args, stdin=stdin)
    if ran.returncode != 0:
        raise IssueError(
            f"gh {' '.join(args[:2])} failed: {why(ran)}; check `gh auth status`, "
            "then run this again"
        )
    return ran.stdout


def gh_json(root: Path, *args: str) -> dict[str, Any] | list[Any]:
    out = gh_ok(root, *args)
    try:
        return json.loads(out)
    except ValueError as error:
        raise IssueError(
            f"gh {' '.join(args[:2])} gave no JSON ({error}): {out.strip()[:200]}"
        ) from error


def origin_url(root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()


def origin_repo(root: Path) -> str:
    """OWNER/REPO of origin, or a refusal that says how to point origin at GitHub."""
    url = origin_url(root)
    if not url:
        raise IssueError(
            "this repository has no origin, and Lem reads the issues of origin's "
            "repository on GitHub: add it (`git remote add origin "
            "https://github.com/OWNER/REPO.git`), then run this again"
        )
    found = ORIGIN.fullmatch(url)
    if not found:
        raise IssueError(
            f"origin is {url}, which is not a repository on GitHub, and Lem reads the "
            "issues of origin: point origin at the repository on GitHub (`git remote "
            "set-url origin https://github.com/OWNER/REPO.git`), then run this again"
        )
    return found["repo"]


def same(one: str, other: str) -> bool:
    """Whether two OWNER/REPO name one repository: GitHub takes either case."""
    return one.lower() == other.lower()


def last_line(text: str | None) -> str:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    return lines[-1] if lines else ""


def logins(people: list | None) -> list[str]:
    return [
        person.get("login")
        for person in people or []
        if isinstance(person, dict) and person.get("login")
    ]


def comments_of(root: Path, repo: str, number: int) -> list[dict]:
    """Every comment of an issue, page after page, oldest first: the REST list, which
    `--paginate` reads to its end and `--slurp` gives as one array of the pages."""
    pages = gh_json(
        root, "api", f"repos/{repo}/issues/{number}/comments", "--paginate", "--slurp"
    )
    found = [
        comment
        for page in pages
        for comment in (page if isinstance(page, list) else [page])
    ]
    return [
        {
            "author": (comment.get("user") or {}).get("login"),
            "at": comment.get("created_at"),
            "text": comment.get("body") or "",
            "url": comment.get("html_url"),
        }
        for comment in found
        if isinstance(comment, dict)
    ]


def view(root: Path, repo: str, number: int) -> dict:
    issue = gh_json(root, "issue", "view", str(number), "--repo", repo, "--json", VIEW)
    if not isinstance(issue, dict):
        raise IssueError(f"gh issue view gave no issue for #{number} of {repo}")
    return issue


def foreign(repo: str, origin: str) -> str:
    return (
        f"the address names an issue of {repo}, and Lem reads the issues of origin, "
        f"which is {origin}: give the number or the address of an issue of {origin}, "
        "or start the task from the owner's own words, with the address in them"
    )


def issue_number(given: str, origin: str) -> int:
    """The number of an issue of origin from 42, #42 or its address; an address of
    another repository is refused."""
    given = given.strip()
    address = ADDRESS.fullmatch(given)
    if address:
        if not same(address["repo"], origin):
            raise IssueError(foreign(address["repo"], origin))
        number = int(address["number"])
    else:
        found = project.ISSUE.fullmatch(given)
        if not found:
            raise IssueError(
                f"{given!r} is no issue's number or address: give 42, "
                f"#42 or https://github.com/{origin}/issues/42"
            )
        number = int(found[1])
    if number == 0:
        raise IssueError("issue 0 is no issue: GitHub numbers its issues from 1")
    return number


def cmd_read(root: Path, given: str) -> dict:
    tracker(root)
    origin = origin_repo(root)
    number = issue_number(given, origin)
    issue = view(root, origin, number)
    # the repository comes from the issue's own address: an issue moved to another
    # repository answers with that one
    address = ADDRESS.fullmatch(issue.get("url") or "")
    if not address and "/pull/" in (issue.get("url") or ""):
        # gh issue view answers for a pull request's number too (gh 2.101.0, read on a
        # public repository on 2026-11-22)
        raise IssueError(
            f"#{number} of {origin} is a pull request ({issue['url']}), not an issue: "
            "give the number of an issue"
        )
    if not address:
        raise IssueError(
            f"gh issue view gave #{number} of {origin} no address of "
            f"an issue: {issue.get('url')!r}"
        )
    if not same(address["repo"], origin):
        raise IssueError(
            f"issue #{number} of {origin} is now {issue['url']}, an issue of another "
            f"repository, and Lem reads the issues of origin, which is {origin}: "
            "start the task from the owner's own words, with the address in them"
        )
    text = issue.get("body") or ""
    title = issue.get("title") or ""
    repo = address["repo"]
    return {
        "id": f"#{number}",
        "number": number,
        "repository": repo,
        "url": issue["url"],
        "title": title,
        "text": text,
        "state": (issue.get("state") or "").lower(),
        "state_reason": (issue.get("stateReason") or "").lower() or None,
        "labels": [
            label.get("name")
            for label in issue.get("labels") or []
            if isinstance(label, dict)
        ],
        "author": (issue.get("author") or {}).get("login"),
        "assignees": logins(issue.get("assignees")),
        "comments": comments_of(root, repo, number),
        # the text is the ask, as written; the title only when the text is empty; never
        # a comment
        "ask": text if text.strip() else title,
        "ask_is": "text" if text.strip() else "title",
        "task_dir": ["--ticket", f"#{number}", "--ticket-repo", repo],
    }


def tracker(root: Path) -> dict:
    """The settings, when their tracker is GitHub's."""
    settings = project.load(root)
    kind = (settings["tracker"] or {}).get("kind")
    if kind != "github":
        raise IssueError(
            (
                f"the project's tracker is {kind or 'none'} ({project.SETTINGS}, "
                '[tracker]), and lem issue acts for kind = "github" only'
            )
            + (
                ": a Linear ticket's steps are the lem-linear skill's"
                if kind == "linear"
                else ': add the table with kind = "github" first'
            )
        )
    return settings


def the_task(root: Path, slug: str, step: str) -> tuple[dict, list[dict]]:
    """The task SLUG as `lem project tasks` gives it, once the guards of STEP passed: a
    task of an issue, in the status the step belongs to, that holds its issue itself,
    and whose issue is of origin's repository."""
    if not project.SLUG.fullmatch(slug):
        raise IssueError(f"slug {slug!r} must be lower-case words joined by hyphens")
    settings = tracker(root)
    tasks = project.read_tasks(root, settings)
    task = next((task for task in tasks if task["slug"] == slug), None)
    if task is None:
        raise IssueError(
            f"no task {slug!r}; the tasks are: "
            f"{', '.join(task['slug'] for task in tasks) or 'none yet'}"
        )
    # the release rule (lem_release), before any call to GitHub: the writes at a task's
    # end pass
    stopped = lem_release.check(
        project.state_root(root) / "tasks" / slug,
        passes=step in ("land", "drop", "answer"),
    )
    if stopped:
        raise IssueError(stopped)
    if not task["ticket"]:
        raise IssueError(
            f"the task {slug!r} came from no issue, so lem issue has "
            "nothing to write for it"
        )
    if not task["ticket"].startswith("#") or not task["ticket_repo"]:
        raise IssueError(
            f"the task {slug!r} keeps the ticket {task['ticket']} with no repository "
            "of GitHub (ticket-repo.txt): it is no issue lem issue can write to, and "
            "the owner writes to it by hand"
        )
    status = task["status"]
    if step == "start" and (status in project.ENDED or status == project.PARKED):
        raise IssueError(
            f"the task {slug!r} is {status}: the start belongs to a task whose build "
            f"starts, so nothing is written to issue {task['ticket']}"
        )
    if step in STATUS_OF and status != STATUS_OF[step]:
        raise IssueError(
            f"the task {slug!r} is {status or 'new'}, and `lem issue {step}` belongs "
            f"to a task that is {STATUS_OF[step]}: nothing is written "
            f"to issue {task['ticket']}"
        )
    holder = task.get("ticket_held_by")
    if holder:
        raise IssueError(
            f"issue {task['ticket']} is held by the task {holder!r} now, which went on "
            f"from {slug!r}: {slug} owes the issue nothing, and what the issue gets is "
            f"{holder}'s to write (`lem issue STEP {holder}` when that task ends)"
        )
    origin = origin_repo(root)
    if not same(origin, task["ticket_repo"]):
        raise IssueError(
            f"origin names {origin}, and the task {slug!r} came from issue "
            f"{task['ticket']} of {task['ticket_repo']}: Lem writes to an issue of "
            "origin's repository only. Set origin back (`git remote set-url origin "
            f"https://github.com/{task['ticket_repo']}.git`) and run this again, or "
            f"the owner writes to issue {task['ticket']} of "
            f"{task['ticket_repo']} by hand"
        )
    return task, tasks


def write_step(root: Path, slug: str, step: str, login: str | None = None) -> str:
    """Write one step down through `lem project ticket-step`; its JSON line is not this
    command's output."""
    with contextlib.redirect_stdout(io.StringIO()):
        project.cmd_ticket_step(root, slug, step, login)
    return f"{step} {login}" if login else step


def signed_in(root: Path) -> str:
    """The login of the person signed in to gh."""
    ran = gh(root, "api", "user", "--jq", ".login")
    login = ran.stdout.strip()
    if ran.returncode != 0 or not login:
        raise IssueError(
            f"gh cannot tell who is signed in ({why(ran)}): sign it in with "
            "`gh auth login`, then run this again"
        )
    return login


def carried(root: Path, task: dict, tasks: list[dict]) -> str | None:
    """The assignee Lem added for the dropped task this one went on from, with the same
    issue, and did not remove: the resumed task takes it over, so that its own end
    removes it."""
    file = project.state_root(root) / "tasks" / task["slug"] / project.RESUMED_FROM
    if not file.is_file():
        return None
    before = next(
        (other for other in tasks if other["slug"] == project.text_of(file).strip()),
        None,
    )
    if (
        before is None
        or before["ticket"] != task["ticket"]
        or "unassigned" in before["ticket_steps"]
    ):
        return None
    return before["ticket_assignee"]


def result(  # noqa: PLR0913, PLR0917 - over the limit before the limit was set
    task: dict,
    step: str,
    issue: dict | None,
    did: list[str],
    wrote: list[str],
    says: str | None,
) -> dict:
    return {
        "slug": task["slug"],
        "ticket": task["ticket"],
        "repository": task["ticket_repo"],
        "step": step,
        "url": (issue or {}).get("url"),
        "state": ((issue or {}).get("state") or "").lower() or None,
        "assignees": logins((issue or {}).get("assignees")) if issue else None,
        "did": did,
        "wrote": wrote,
        "says": says,
    }


def cmd_start(root: Path, slug: str) -> dict:
    task, tasks = the_task(root, slug, "start")
    steps = task["ticket_steps"]
    if "started" in steps:
        return result(task, "start", None, [], [], None)
    repo, number, ticket = task["ticket_repo"], int(task["ticket"][1:]), task["ticket"]
    issue = view(root, repo, number)
    assignees = logins(issue.get("assignees"))
    did: list[str] = []
    wrote: list[str] = []
    says = None

    def add(login: str) -> None:
        nonlocal says
        ran = gh(
            root, "issue", "edit", str(number), "--repo", repo, "--add-assignee", login
        )
        if ran.returncode == 0:
            did.append(f"added the assignee {login}")
            assignees.append(login)
            return
        wrote.append(write_step(root, slug, "unassigned"))
        says = (
            f"gh could not make {login} the assignee of issue {ticket} of {repo} "
            f"({why(ran)}): the build goes on with no assignee there"
        )

    if "assigned" in steps:
        # a start cut off after its record: the add, only while the issue still
        # has nobody
        if "unassigned" not in steps and not assignees:
            add(task["ticket_assignee"])
    else:
        before = carried(root, task, tasks)
        if before and any(same(before, login) for login in assignees):
            wrote.append(write_step(root, slug, "assigned", before))
        elif not assignees:
            login = signed_in(root)
            # written before the add: a cut-off between the two leaves a record whose
            # removal reads the assignees first
            wrote.append(write_step(root, slug, "assigned", login))
            add(login)
        else:
            me = signed_in(root)
            others = [login for login in assignees if not same(login, me)]
            if others:
                says = (
                    f"issue {ticket} of {repo} is assigned to {', '.join(others)}: "
                    "Lem added nobody, and the build goes on"
                )
    wrote.append(write_step(root, slug, "started"))
    return result(
        task,
        "start",
        {**issue, "assignees": [{"login": login} for login in assignees]},
        did,
        wrote,
        says,
    )


def landed_words(root: Path, task: dict) -> str:
    """The landed comment, from the task's record: its outcome, and the pull request
    with green or not green."""
    directory = project.state_root(root) / "tasks" / task["slug"]
    text = (
        project.text_of(directory / "task.md")
        if (directory / "task.md").is_file()
        else ""
    )
    outcome = project.outcome_of(text)
    what = outcome or project.first_sentence(task["ask"] or task["slug"])
    proposal = task["proposal"] or {}
    if proposal.get("pull_request"):
        verdict = "green" if proposal.get("green") else "not green"
        pull = (
            f"The pull request: {proposal['pull_request']}, "
            f"{verdict} when it was proposed."
        )
    else:
        pull = (
            f"No pull request is on record; the task's state says: {first_line(task)}."
        )
    return f"Lem landed the work of this issue: {what}.\n\n{pull}"


def first_line(task: dict) -> str:
    """The text of the newest state block's first line, without its time and status."""
    found = (
        project.STATE_LINE.fullmatch((task["state"] or "").splitlines()[0])
        if task["state"]
        else None
    )
    return found["text"] if found else (task["status"] or "")


def dropped_words(task: dict) -> str:
    return f"Lem dropped its task for this issue: {first_line(task)}."


def answered_words(root: Path, task: dict) -> str:
    """The answer's comment: the investigation's line and where, and where its report is
    while the task's directory holds it; an answer still owed after `lem project prune`
    removed the report names none."""
    found = task["investigation"] or {}
    line = found.get("line") or first_line(task)
    where = f" ({found['where']})" if found.get("where") else ""
    said = f"Lem's investigation answered this issue: {line}{where}."
    if (
        project.state_root(root) / "tasks" / task["slug"] / "investigation.md"
    ).is_file():
        said += (
            "\n\nThe report is in the task's directory on the owner's machine, "
            "not on this issue."
        )
    return said


def comment(  # noqa: PLR0913, PLR0917 - over the limit before the limit was set
    root: Path,
    task: dict,
    step: str,
    number: int,
    words: str,
    did: list[str],
    wrote: list[str],
) -> None:
    """The one comment of STEP, unless it is written down or on the issue already; its
    last line is Lem's."""
    if COMMENTED[step] in task["ticket_steps"]:
        return
    marker = f"lem: {task['slug']} {LAST_WORD[step]}"
    if any(
        last_line(found["text"]) == marker
        for found in comments_of(root, task["ticket_repo"], number)
    ):
        # a session was cut off after the post: the comment is there, and only its
        # record was missing
        wrote.append(write_step(root, task["slug"], COMMENTED[step]))
        return
    gh_ok(
        root,
        "issue",
        "comment",
        str(number),
        "--repo",
        task["ticket_repo"],
        "--body-file",
        "-",
        stdin=f"{words}\n\n{marker}\n",
    )
    did.append("posted the comment")
    wrote.append(write_step(root, task["slug"], COMMENTED[step]))


def cmd_land(root: Path, slug: str) -> dict:
    task, _ = the_task(root, slug, "land")
    number = int(task["ticket"][1:])
    did: list[str] = []
    wrote: list[str] = []
    comment(root, task, "land", number, landed_words(root, task), did, wrote)
    issue = None
    if "landed" not in task["ticket_steps"]:
        issue = view(root, task["ticket_repo"], number)
        if (issue.get("state") or "").upper() != "CLOSED":
            gh_ok(
                root,
                "issue",
                "close",
                str(number),
                "--repo",
                task["ticket_repo"],
                "--reason",
                "completed",
            )
            did.append("closed the issue as completed")
            issue = {**issue, "state": "CLOSED"}
        wrote.append(write_step(root, slug, "landed"))
    return result(task, "land", issue, did, wrote, None)


def cmd_end(root: Path, slug: str, step: str) -> dict:
    """`drop` and `answer`: the comment, then the assignee Lem added goes; the issue
    stays open."""
    task, _ = the_task(root, slug, step)
    number, repo, ticket = int(task["ticket"][1:]), task["ticket_repo"], task["ticket"]
    did: list[str] = []
    wrote: list[str] = []
    comment(
        root,
        task,
        step,
        number,
        dropped_words(task) if step == "drop" else answered_words(root, task),
        did,
        wrote,
    )
    issue = view(root, repo, number)
    assignees = logins(issue.get("assignees"))
    login = task["ticket_assignee"]
    if "assigned" in task["ticket_steps"] and "unassigned" not in task["ticket_steps"]:
        # the login the record names, whoever is signed in to gh now; every other
        # assignee stays
        if any(same(login, found) for found in assignees):
            gh_ok(
                root,
                "issue",
                "edit",
                str(number),
                "--repo",
                repo,
                "--remove-assignee",
                login,
            )
            did.append(f"removed the assignee {login}")
            assignees = [found for found in assignees if not same(login, found)]
        wrote.append(write_step(root, slug, "unassigned"))
    closed = (issue.get("state") or "").upper() == "CLOSED"
    says = (
        f"issue {ticket} of {repo} is closed already, by someone else than Lem"
        if closed
        else (
            f"issue {ticket} of {repo} stays open: "
            "whether it closes is the owner's call"
        )
    )
    return result(
        task,
        step,
        {**issue, "assignees": [{"login": found} for found in assignees]},
        did,
        wrote,
        says,
    )


def cmd_check(root: Path) -> tuple[dict, bool]:  # noqa: C901, PLR0912 - over the limit before the limit was set
    """The tracker's check: each missing thing with its fix, and the facts the
    onboarding needs."""
    missing: list[dict] = []
    found: dict[str, Any] = {
        "repository": None,
        "gh": shutil.which("gh"),
        "signed_in": None,
        "issues_on": None,
        "has_issues": None,
    }
    url = origin_url(root)
    if not url:
        missing.append(
            {
                "what": "this repository has no origin",
                "fix": "git remote add origin https://github.com/OWNER/REPO.git",
            }
        )
    elif not (matched := ORIGIN.fullmatch(url)):
        missing.append(
            {
                "what": f"origin is {url}, which is not a repository on GitHub",
                "fix": (
                    "point origin at the repository on GitHub: git remote "
                    "set-url origin https://github.com/OWNER/REPO.git"
                ),
            }
        )
    else:
        found["repository"] = matched["repo"]
    if not found["gh"]:
        missing.append({"what": "gh is not installed", "fix": INSTALL_GH})
    else:
        found["signed_in"] = (
            gh(root, "auth", "status", "--hostname", "github.com").returncode == 0
        )
        if not found["signed_in"]:
            missing.append(
                {"what": "gh is not signed in to github.com", "fix": "gh auth login"}
            )
    repo = found["repository"]
    if repo and found["signed_in"]:
        ran = gh(root, "repo", "view", repo, "--json", "hasIssuesEnabled")
        try:
            on = (
                json.loads(ran.stdout).get("hasIssuesEnabled")
                if ran.returncode == 0
                else None
            )
        except (ValueError, AttributeError):
            on = None
        if on is None:
            missing.append(
                {
                    "what": f"gh cannot read the repository {repo} ({why(ran)})",
                    "fix": (
                        "check that the account gh is signed in to can see "
                        f"{repo} (`gh auth status`)"
                    ),
                }
            )
        else:
            found["issues_on"] = bool(on)
            if not on:
                missing.append(
                    {
                        "what": f"the issues of {repo} are off in its settings",
                        "fix": (
                            "turn Issues on under Settings, General, "
                            f"Features of https://github.com/{repo}"
                        ),
                    }
                )
            else:
                # `--state all`: gh lists the open issues alone by default
                ran = gh(
                    root,
                    "issue",
                    "list",
                    "--repo",
                    repo,
                    "--state",
                    "all",
                    "--limit",
                    "1",
                    "--json",
                    "number",
                )
                try:
                    found["has_issues"] = (
                        bool(json.loads(ran.stdout)) if ran.returncode == 0 else None
                    )
                except ValueError:
                    found["has_issues"] = None
                if found["has_issues"] is None:
                    missing.append(
                        {
                            "what": f"gh cannot list the issues of {repo} ({why(ran)})",
                            "fix": (
                                "check that the account gh is signed in to can see the "
                                f"issues of {repo} (`gh auth status`)"
                            ),
                        }
                    )
    if missing:
        says = "; ".join(f"{item['what']}: {item['fix']}" for item in missing)
    else:
        says = (
            f"the issues of {repo} are on, and gh is signed in: "
            "Lem can read and write them; "
        ) + (
            "the repository holds at least one issue"
            if found["has_issues"]
            else "the repository holds no issue yet"
        )
    return {**found, "missing": missing, "says": says}, not missing


@lem_release.one_command
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="lem issue",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="a directory inside the checkout (default: the current one)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "check",
        help=(
            "whether origin's issues can be Lem's tracker, each missing thing with "
            "its fix; writes nothing"
        ),
    )
    commands.add_parser(
        "read",
        help=(
            "one issue of origin's repository, by its number or its address; "
            "writes nothing"
        ),
    ).add_argument("issue", metavar="ID|URL")
    for name, about in (
        (
            "start",
            (
                "the build started: the person signed in to gh becomes the assignee of "
                "an issue that has none"
            ),
        ),
        ("land", "the task landed: one comment, then the issue is closed as completed"),
        ("drop", "the task was dropped: one comment, and the assignee Lem added goes"),
        (
            "answer",
            (
                "the task ended with an answer: one comment with it, "
                "and the assignee Lem added goes"
            ),
        ),
    ):
        commands.add_parser(name, help=about).add_argument("slug")
    args = parser.parse_args(argv)
    try:
        root = project.repo_root(Path(args.repo))
        if args.command == "check":
            found, ok = cmd_check(root)
            print(json.dumps(found, ensure_ascii=False))
            if not ok:
                sys.exit(1)
            return
        if args.command == "read":
            out = cmd_read(root, args.issue)
        elif args.command == "start":
            out = cmd_start(root, args.slug)
        elif args.command == "land":
            out = cmd_land(root, args.slug)
        else:
            out = cmd_end(root, args.slug, args.command)
    except (IssueError, project.SettingsError) as error:
        sys.exit(f"lem issue: {error}")
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
