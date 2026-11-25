"""A stand-in for `gh` on the PATH of a contract test of the GitHub tracker: the words of `gh`
that `lem.adapters.tracker_github` speaks, answered from the issues of each repository in a JSON
state file, in gh's own shapes.

Each call reads the state from the file `GH_ISSUES_STATE` names, appends its words to the file's
`calls`, and writes the state back. It makes no network call. A test starts it as the module
`contract.gh_issues_standin`, through a small launcher on its PATH (`install`).
"""

import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

TESTS = Path(__file__).resolve().parents[1]
LAUNCHER = """#!/bin/sh
exec {python} -I -B -c 'import runpy, sys; sys.path.insert(0, "{tests}"); \
runpy.run_module("contract.gh_issues_standin", run_name="__main__")' "$@"
"""
STATE = "GH_ISSUES_STATE"

type State = dict[str, Any]


class Refused(Exception):
    """gh's refusal: its line on standard error, exit 1."""


def install(folder: Path, state: State) -> dict[str, str]:
    """The launcher in `folder/bin` and the state in `folder/gh-issues.json`; the variables a
    call's environment needs to reach them first."""
    bin_folder = folder / "bin"
    bin_folder.mkdir(parents=True, exist_ok=True)
    launcher = bin_folder / "gh"
    launcher.write_text(LAUNCHER.format(python=sys.executable, tests=TESTS))
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR)
    path = folder / "gh-issues.json"
    path.write_text(json.dumps({"calls": [], **state}))
    return {
        "PATH": f"{bin_folder}{os.pathsep}{os.environ['PATH']}",
        STATE: str(path),
    }


def option(words: list[str], name: str) -> str | None:
    """The value after `name` in `words`, or None."""
    return words[words.index(name) + 1] if name in words else None


def issue_of(state: State, repo: str, number: str) -> dict[str, Any]:
    """The issue `number` of `repo`, or gh's refusal."""
    found = state["repos"].get(repo, {}).get("issues", {}).get(number)
    if found is None:
        raise Refused(
            "GraphQL: Could not resolve to an issue or pull request with the number of "
            f"{number}. (repository.issue)"
        )
    return found


def viewed(repo: str, number: str, found: dict[str, Any]) -> dict[str, Any]:
    """An issue as `gh issue view --json` prints it."""
    url = found.get("url") or f"https://github.com/{repo}/issues/{number}"
    return {
        "number": int(number),
        "title": found["title"],
        "body": found["body"],
        "state": found["state"],
        "stateReason": found.get("reason") or "",
        "labels": [{"name": name, "color": "fff"} for name in found.get("labels", [])],
        "url": url,
        "author": {"login": found["author"], "name": "A"},
        "assignees": [{"login": login, "id": "U"} for login in found["assignees"]],
    }


def api(state: State, words: list[str]) -> str:
    """`gh api user --jq .login`, and the REST list of an issue's comments in two pages."""
    if words[1] == "user":
        if not state.get("login"):
            raise Refused(
                "gh: To use GitHub CLI in automation, set the GH_TOKEN environment variable."
            )
        return state["login"]
    _, owner, name, _, number, _ = words[1].split("/")
    found = issue_of(state, f"{owner}/{name}", number)
    rows = [
        {
            "user": {"login": comment["author"]},
            "body": comment["body"],
            "created_at": "2026-11-22T10:00:00Z",
            "html_url": f"https://github.com/{owner}/{name}/issues/{number}#c",
        }
        for comment in found["comments"]
    ]
    return json.dumps([rows[:2], rows[2:]])


def checked(state: State, words: list[str]) -> str:
    """`gh auth status`, `gh repo view --json hasIssuesEnabled` and `gh issue list`."""
    if words[0] == "auth":
        if not state.get("login"):
            raise Refused(
                "You are not logged into any GitHub hosts. To log in, run: gh auth login"
            )
        return "Logged in to github.com"
    if words[0] == "repo":
        repo = state["repos"].get(words[2])
        if repo is None:
            raise Refused(
                f"GraphQL: Could not resolve to a Repository with the name '{words[2]}'."
            )
        return json.dumps({"hasIssuesEnabled": repo.get("has_issues", True)})
    issues = state["repos"][option(words, "--repo")].get("issues", {})
    limit = int(option(words, "--limit") or 30)
    return json.dumps([{"number": int(number)} for number in issues][:limit])


def issue(state: State, words: list[str]) -> str:
    """`gh issue view`, `edit`, `comment` and `close`."""
    repo, number = option(words, "--repo") or "", words[2]
    found = issue_of(state, repo, number)
    if words[1] == "view":
        return json.dumps(viewed(repo, number, found))
    if words[1] == "edit":
        if state.get("refuse_edit"):
            raise Refused(state["refuse_edit"])
        if added := option(words, "--add-assignee"):
            found["assignees"].append(added)
        gone = option(words, "--remove-assignee")
        found["assignees"] = [login for login in found["assignees"] if login != gone]
    elif words[1] == "comment":
        assert option(words, "--body-file") == "-"
        found["comments"].append(
            {"author": state.get("login"), "body": sys.stdin.read()}
        )
    else:
        found.update(state="CLOSED", reason=(option(words, "--reason") or "").upper())
    return f"https://github.com/{repo}/issues/{number}#issuecomment-1"


def answer(state: State, words: list[str]) -> str:
    """What gh prints for `words`."""
    if words[0] == "api":
        return api(state, words)
    if words[0] in {"auth", "repo"} or words[:2] == ["issue", "list"]:
        return checked(state, words)
    if words[0] == "issue":
        return issue(state, words)
    raise Refused("gh stand-in: no such command: " + " ".join(words))


def main() -> None:
    path = Path(os.environ[STATE])
    state = json.loads(path.read_text())
    words = sys.argv[1:]
    state["calls"].append(words)
    try:
        said = answer(state, words)
    except Refused as refused:
        path.write_text(json.dumps(state))
        sys.exit(str(refused))
    path.write_text(json.dumps(state))
    print(said)


if __name__ == "__main__":
    main()
