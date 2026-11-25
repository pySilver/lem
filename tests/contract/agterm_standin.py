"""A stand-in for `agtermctl`: a script of that name in a folder of the test's own, which keeps
agterm's sessions in a file, records each call, and answers as agterm does (`agtermctl tree
--json`, `session new --json`, a call on a session that is gone with exit 1).

A test puts its folder first on the PATH of the place it binds the adapter to, before
`/usr/bin:/bin` alone, so that no call reaches the owner's real agterm.
"""

import json
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

SCRIPT = r"""
import json, os, sys

state = os.environ["AGTERM_STANDIN"]
args = sys.argv[1:]
with open(os.path.join(state, "raw.jsonl"), "a") as raw:
    raw.write(json.dumps(args) + "\n")
for flag in ("--socket", "--window"):
    if flag in args:
        at = args.index(flag)
        del args[at:at + 2]
with open(os.path.join(state, "calls.jsonl"), "a") as calls:
    calls.write(json.dumps(args) + "\n")
with open(os.path.join(state, "tree.json")) as read:
    tree = json.load(read)
if args[:1] == [tree.get("fail", "")]:
    sys.exit("agterm does not answer")


def value(flag):
    return args[args.index(flag) + 1]


def target():
    wanted = value("--target")
    for node in tree["sessions"]:
        if node["id"] == wanted:
            return node
    sys.exit("no session " + wanted)


def holder(pane):
    wanted = pane.split(":")[0]
    for node in tree["sessions"]:
        if node["id"] == wanted:
            return node
    sys.exit("no session " + wanted)


def save():
    with open(os.path.join(state, "tree.json"), "w") as written:
        json.dump(tree, written)


if args[:2] == ["tree", "--json"]:
    spaces = [
        {"id": space, "sessions": [n for n in tree["sessions"] if n["workspace"] == space]}
        for space in tree["workspaces"]
    ]
    print(json.dumps({"result": {"tree": {"workspaces": spaces}}}))
elif args[:2] == ["session", "new"]:
    tree["count"] = tree.get("count", 0) + 1
    made = "S-%d" % tree["count"]
    if "--parent" in args:
        parent = [n for n in tree["sessions"] if n["id"] == value("--parent")][0]
        space = parent["workspace"]
    else:
        space = value("--workspace") if "--workspace" in args else tree["workspaces"][0]
    node = {
        "id": made, "name": value("--name"), "workspace": space, "cwd": value("--cwd"),
        "foreground": ["/usr/local/bin/claude"], "command": value("--command"),
    }
    if "--after" in args:
        anchor = [n["id"] for n in tree["sessions"]].index(value("--after"))
        tree["sessions"].insert(anchor + 1, node)
    else:
        tree["sessions"].append(node)
    save()
    print(json.dumps({"result": {"id": made}}))
elif args[:2] == ["session", "move"]:
    moved = target()
    tree["sessions"].remove(moved)
    tree["sessions"].append(moved)
    save()
elif args[:2] == ["session", "close"]:
    tree["sessions"].remove(target())
    save()
elif args[:2] == ["session", "select"]:
    chosen = target()
    for node in tree["sessions"]:
        node["active"] = node is chosen
    save()
elif args[:2] == ["session", "status"]:
    target()["status"] = args[2]
    save()
elif args[:2] == ["session", "rename"]:
    target()["name"] = args[2]
    save()
elif args[:3] == ["session", "overlay", "open"]:
    node = target()
    node.setdefault("pages", []).append(args[3:args.index("--target")])
    save()
elif args[:2] == ["msg", "send"]:
    node = holder(value("--to"))
    node.setdefault("mailbox", []).append(args[2])
    save()
elif args[:2] == ["msg", "read"]:
    node = holder(value("--as"))
    print(json.dumps({"result": {"messages": [{"text": t} for t in node.get("mailbox", [])]}}))
elif args[:1] == ["pick"]:
    rows = sys.stdin.read().splitlines()
    answer = tree.get("pick")
    if answer is None:
        sys.exit(2)
    print(json.dumps({"result": "picked", "id": answer, "label": answer}))
else:
    sys.exit("the stand-in does not know " + " ".join(args))
"""


@dataclass(frozen=True)
class Standin:
    """The stand-in's folder: its script, its sessions and its record of calls."""

    folder: Path

    def environ(self, **more: str) -> dict[str, str]:
        """An environment whose PATH finds the stand-in, and no real agterm."""
        return {
            "PATH": f"{self.folder / 'bin'}:/usr/bin:/bin",
            "AGTERM_STANDIN": str(self.folder),
            **more,
        }

    def calls(self) -> list[list[str]]:
        """Each call the stand-in took, in order."""
        path = self.folder / "calls.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text().splitlines()]

    def raw(self) -> list[list[str]]:
        """Each call as agtermctl got it, with its socket and window."""
        path = self.folder / "raw.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text().splitlines()]

    def sessions(self) -> list[dict[str, object]]:
        """agterm's sessions now, in their order."""
        return json.loads((self.folder / "tree.json").read_text())["sessions"]

    def change(self, **fields: object) -> None:
        """Set fields of the tree: `fail="tree"` makes `tree` fail."""
        path = self.folder / "tree.json"
        path.write_text(json.dumps({**json.loads(path.read_text()), **fields}))


def install(
    folder: Path,
    sessions: Sequence[Mapping[str, object]] = (),
    workspaces: tuple[str, ...] = (),
) -> Standin:
    """A stand-in in `folder`, with agterm's `sessions` in `workspaces`: by default the ones
    the sessions name, else one."""
    named = tuple(dict.fromkeys(str(node["workspace"]) for node in sessions))
    workspaces = workspaces or named or ("W-1",)
    (folder / "bin").mkdir(parents=True)
    script = folder / "bin" / "agtermctl"
    script.write_text(f"#!{sys.executable}\n{SCRIPT}")
    script.chmod(0o755)
    tree = {
        "workspaces": list(workspaces),
        "sessions": [dict(node) for node in sessions],
    }
    (folder / "tree.json").write_text(json.dumps(tree))
    return Standin(folder)
