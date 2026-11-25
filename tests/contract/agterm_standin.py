"""A stand-in for `agtermctl`: a script of that name in a folder of the test's own, which keeps
agterm's sessions in a file, records each call, and answers as agterm does (`agtermctl tree
--json`, `session new --json`, a call on a session that is gone with exit 1).

Its parser is as strict as agterm's own: each subcommand takes the options its `--help` names
(agtermctl 2026-11-25: `session new`, `close`, `rename`, `status`, `select`, `overlay open`,
`msg send`, `msg read`, `pick`, `tree`), the number of arguments it names, and refuses the pairs
it names as exclusive (`--workspace` with `--workspace-name`, `--after` or `--before`, whose
anchor carries its own workspace; `--after` with `--before`; `--parent` with either), with exit
64 as Swift's argument parser gives. `msg send` and `msg read` take no `--window`.

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

WS = {"--socket", "--window"}
SPEC = {
    ("tree",): (WS, {"--json"}, 0, 0),
    ("session", "new"): (
        WS | {"--cwd", "--workspace", "--workspace-name", "--command", "--name", "--after",
              "--before", "--parent", "--tint", "--tint-on"},
        {"--create-workspace", "--wait", "--no-select", "--json"}, 0, 0),
    ("session", "close"): (WS | {"--target"}, {"--undoable", "--terminate", "--json"}, 0, 0),
    ("session", "rename"): (WS | {"--target"}, {"--json"}, 1, 1),
    ("session", "status"): (
        WS | {"--target", "--sound", "--color", "--shape", "--pane", "--pane-id"},
        {"--blink", "--auto-reset", "--if-idle", "--json"}, 1, 1),
    ("session", "select"): (WS | {"--target"}, {"--json"}, 0, 0),
    ("session", "move"): (WS | {"--target", "--to"}, {"--json"}, 0, 1),
    ("session", "overlay", "open"): (
        WS | {"--url", "--html", "--target", "--cwd"},
        {"--js", "--companion", "--browse", "--navigation", "--chromeless", "--follow", "--json"},
        0, 1),
    ("msg", "send"): ({"--socket", "--to", "--workspace", "--as"}, {"--stdin", "--all", "--json"}, 1, 1),
    ("msg", "read"): ({"--socket", "--timeout", "--as"}, {"--ack", "--wait", "--json"}, 0, 0),
    ("pick",): (
        WS | {"--prompt", "--query", "--select", "--timeout", "--session"},
        {"--allow-custom", "--follow", "--no-block", "--json"}, 0, 0),
}
EXCLUSIVE = {
    ("session", "new"): (
        ("--workspace", "--workspace-name"), ("--after", "--workspace"),
        ("--before", "--workspace"), ("--after", "--before"), ("--parent", "--workspace"),
        ("--parent", "--after"), ("--parent", "--before")),
}
STATES = ("idle", "active", "completed", "blocked")


def refuse(why):
    sys.stderr.write("Error: " + why + "\n")
    sys.exit(64)


def strict(args):
    key = next((k for k in sorted(SPEC, key=len, reverse=True) if tuple(args[:len(k)]) == k), None)
    if key is None:
        refuse("unknown subcommand " + " ".join(args[:3]))
    valued, flags, least, most = SPEC[key]
    rest, given, positional = args[len(key):], set(), []
    while rest:
        word = rest.pop(0)
        if word in valued:
            if not rest:
                refuse("missing value for " + word)
            rest.pop(0)
        elif word not in flags:
            if word.startswith("--"):
                refuse("unknown option " + word)
            positional.append(word)
            continue
        if word in given:
            refuse("option given twice " + word)
        given.add(word)
    if not least <= len(positional) <= most:
        refuse("wrong number of arguments: " + repr(positional))
    for one, other in EXCLUSIVE.get(key, ()):
        if one in given and other in given:
            refuse(one + " and " + other + " are mutually exclusive")
    if key == ("session", "status") and positional[0] not in STATES:
        refuse("unknown state " + positional[0])
    if "--browse" in given and "--url" not in given:
        refuse("--browse requires --url")


strict(args)
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
    elif "--after" in args:
        space = [n for n in tree["sessions"] if n["id"] == value("--after")][0]["workspace"]
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
