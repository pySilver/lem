"""A stand-in for `gh` on the PATH of a contract test: the words of `gh` that `lem.adapters.
forge_gh` speaks, answered by a `LocalForge` over the test's real origin, in gh's own JSON shapes.

Each call reads the forge from the state file `GH_STANDIN_STATE` names, appends its words to the
file's `calls`, and writes the forge back. It makes no network call. A test starts it as the
module `contract.gh_standin`, through a small launcher on its PATH that puts `tests/` first on
`sys.path` (`test_forge.py`).
"""

import os
import subprocess
import sys
from pathlib import Path

import msgspec

from fakes.forge import LocalForge
from fakes.repo import RealRepo, git_env
from lem.ports.faults import Unanswered
from lem.ports.forge_facts import MergeDenied, MergeMethod, MergeText, Pull


class State(msgspec.Struct, kw_only=True):
    """The forge between two calls: its repository, its pull requests, and every call."""

    origin: str
    checkout: str
    teammate: str
    name: str = "owner/project"
    pulls: dict[int, Pull] = {}
    calls: list[list[str]] = []
    # A merge call whose connection is lost before it reaches the forge, or after.
    lose: str | None = None
    # Whether gh has a login for the host: without one, every call says so and exits 4.
    login: bool = True
    queue_events: list[dict[str, object]] = []
    in_queue: bool = False


def option(words: list[str], name: str) -> str | None:
    """The value after `name` in `words`, or None."""
    return words[words.index(name) + 1] if name in words else None


def shaped(pull: Pull) -> dict[str, object]:
    """A pull request as `gh pr view --json` prints it."""
    return {
        "number": pull.number,
        "url": pull.url,
        "title": pull.title,
        "body": pull.body,
        "state": pull.state.upper(),
        "author": {"login": pull.author} if pull.author else None,
        "headRefOid": pull.head,
        "headRefName": pull.head_ref,
        "baseRefName": pull.base,
        "mergeable": pull.mergeable.upper(),
        "mergeCommit": {"oid": pull.merge_commit} if pull.merge_commit else None,
        "autoMergeRequest": {"enabledBy": "lem"} if pull.queued else None,
    }


def printed(found: object) -> None:
    """Write `found` as gh does: JSON for a struct or a list, else the text."""
    text = found if isinstance(found, str) else msgspec.json.encode(found).decode()
    sys.stdout.write(f"{text}\n")


def outside(forge: LocalForge, state: State, words: list[str]) -> object:
    """What gh prints for `repo view` and for `api`: a pull request's `commits`, GitHub's
    total, which no list caps, or a commit's first parent."""
    if words[:2] == ["api", "graphql"]:
        number = int(
            next(word.split("=", 1)[1] for word in words if word.startswith("number="))
        )
        pull = forge.pull(number)
        assert option(words, "--jq") == ".data.repository.pullRequest"
        return {
            **shaped(pull),
            "mergeQueueEntry": {"id": "queue-entry"} if state.in_queue else None,
            "timelineItems": {"nodes": state.queue_events[-1:]},
        }
    if "/pulls/" in words[1]:
        return counted(state, forge.pull(int(words[1].rsplit("/", 1)[-1])))
    if words[0] == "repo":
        if option(words, "--jq") == ".nameWithOwner":
            return state.name
        return {"nameWithOwner": state.name, "url": f"https://github.com/{state.name}"}
    sha = words[1].rsplit("/", 1)[-1]
    ran = subprocess.run(
        ["git", "-C", state.origin, "rev-parse", f"{sha}^1"],
        capture_output=True,
        text=True,
        env=git_env(),
        check=True,
    )
    return ran.stdout.strip()


def body_of(words: list[str]) -> str:
    """The text a call gives: on standard input with `--body-file -`, as the adapter sends
    it, else after `--body`."""
    if option(words, "--body-file") == "-":
        return sys.stdin.read()
    return option(words, "--body") or ""


def counted(state: State, pull: Pull) -> int:
    """How many commits the pull request's head holds that its base lacks."""
    ran = subprocess.run(
        [
            "git",
            "-C",
            state.origin,
            "rev-list",
            "--count",
            f"refs/heads/{pull.base}..{pull.head}",
        ],
        capture_output=True,
        text=True,
        env=git_env(),
        check=True,
    )
    return int(ran.stdout.strip())


def listed(forge: LocalForge, words: list[str]) -> object:
    """What gh prints for `pr list` and `pr create`."""
    if words[1] == "list":
        if option(words, "--state") == "open":
            return [shaped(pull) for pull in forge.open_pulls()]
        found = forge.find_pulls(option(words, "--head") or "", option(words, "--base"))
        return [shaped(pull) for pull in found]
    head, base = option(words, "--head") or "", option(words, "--base") or ""
    title = option(words, "--title") or ""
    return forge.open_pull(head, base, title, body_of(words)).url


def merged(forge: LocalForge, state: State, number: int, words: list[str]) -> object:
    """What gh prints for `pr merge`: nothing, or GitHub's refusal on its errors."""
    methods: dict[str, MergeMethod] = {
        "--squash": "squash",
        "--rebase": "rebase",
        "--merge": "merge",
    }
    chosen = [methods[word] for word in words if word in methods]
    method: MergeMethod = chosen[0] if chosen else "merge"
    subject, body = option(words, "--subject") or "", body_of(words)
    head = option(words, "--match-head-commit") or ""
    if state.lose == "before":
        raise Unanswered("gh", "error connecting to api.github.com")
    outcome = forge.merge(number, head, method, MergeText(subject=subject, body=body))
    if state.lose == "after":
        raise Unanswered("gh", "read tcp: connection reset by peer")
    if isinstance(outcome, MergeDenied):
        raise Unanswered("gh", f"GraphQL: {outcome.said}")
    return ""


def aimed(state: State, words: list[str]) -> None:
    """Refuse a call that names another repository than the test's, as gh would find none."""
    named = option(words, "--repo") or (
        words[2] if words[:2] == ["repo", "view"] else None
    )
    if words[:2] == ["api", "graphql"]:
        fields = dict(word.split("=", 1) for word in words[2:] if "=" in word)
        named = f"{fields.get('owner')}/{fields.get('repo')}"
    elif words[0] == "api":
        named = "/".join(words[1].removeprefix("repos/").split("/")[:2])
    if named != state.name:
        raise Unanswered(
            "gh", f"Could not resolve to a Repository with the name '{named}'"
        )


def answered(forge: LocalForge, state: State, words: list[str]) -> object:
    """What gh prints for `words`."""
    aimed(state, words)
    if words[0] in {"repo", "api"}:
        return outside(forge, state, words)
    if words[1] in {"list", "create"}:
        return listed(forge, words)
    number = int(words[2])
    if words[1] == "view" and option(words, "--json") == "commits":
        return counted(state, forge.pull(number))
    if words[1] == "view":
        return shaped(forge.pull(number))
    if words[1] == "edit":
        title = option(words, "--title") or ""
        return forge.update_pull(number, title, body_of(words)).url
    if words[1] == "merge":
        return merged(forge, state, number, words)
    raise Unanswered("gh", f"unknown command {' '.join(words)}")


def main(words: list[str]) -> int:
    """Answer one call of gh, and keep the forge for the next."""
    path = Path(os.environ["GH_STANDIN_STATE"])
    state = msgspec.json.decode(path.read_bytes(), type=State)
    state.calls.append(words)
    if not state.login:
        sys.stderr.write("To get started with GitHub CLI, please run:  gh auth login\n")
        path.write_bytes(msgspec.json.encode(state))
        return 4
    repo = RealRepo(
        origin=Path(state.origin),
        checkout=Path(state.checkout),
        teammate=Path(state.teammate),
        branch="main",
    )
    forge = LocalForge(remote=repo, name=state.name, pulls=dict(state.pulls))
    try:
        printed(answered(forge, state, words))
        code = 0
    except Unanswered as error:
        sys.stderr.write(f"{error.said}\n")
        code = 1
    state.pulls = forge.pulls
    path.write_bytes(msgspec.json.encode(state))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
