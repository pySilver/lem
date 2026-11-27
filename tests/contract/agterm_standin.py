"""A stand-in for `agtermctl`: a script of that name in a folder of the test's own, which keeps
agterm's sessions in a file, records each call, and answers as agterm does (`agtermctl tree
--json`, `session new --json`, a call on a session that is gone with exit 1).

Its parser is as strict as agterm's own: each subcommand takes the options its `--help` names
(agtermctl 2026-11-25: `session new`, `close`, `rename`, `status`, `select`, `overlay open`,
`msg send`, `msg read`, `pick`, `tree`; and from agterm's reference, 2026-11-27, `zmx tree`,
`zmx attach` and `restore mode`), the number of arguments it names, and refuses the pairs
it names as exclusive (`--workspace` with `--workspace-name`, `--after` or `--before`, whose
anchor carries its own workspace; `--after` with `--before`; `--parent` with either), with exit
64 as Swift's argument parser gives. `msg send` and `msg read` take no `--window`.

A test puts its folder first on the PATH of the place it binds the adapter to, before
`/usr/bin:/bin` alone, so that no call reaches the owner's real agterm.

Another Mac is a second stand-in: `hosts` of this one's tree names the folder of the stand-in that
each ssh destination reaches, and `zmx tree HOST` and `zmx attach HOST SESSION --companions` read
that one's sessions (agterm's reference, "Remote sessions"). A refusal of those calls is agterm's
reply on standard output with exit 1, as `agtermctl --json` gives it (agterm be92bc63,
`SocketClient.printResponse`). A destination not named fails as ssh does; the far tree's
`ssh_says` is ssh's own words, `agtermctl = false` a Mac with no agtermctl, `zmx_tree = false`
one too old for `zmx tree`, a `restore` other than `live` one outside Live sessions, which lists
nothing; `companions_known = false` an origin that names no companions, `gone_members` the companions
that fail in a group attach, which keeps the other rows, and `gone_at_attach` a session that
ends between the list and the attach. This tree's
`group_attach = false` is an app too old for a group attach, and `old_cli = true` an agtermctl
that does not know `--companions`. `windows` names this Mac's open windows (`W1` alone when it
names none, and then a call's window places nothing); a session's `window` places it, and
`tree --window` and `session select --window` read it.
`restore mode` answers in the owner's own form of 2026-11-27.
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
    ("zmx", "tree"): ({"--socket"}, {"--json"}, 0, 1),
    ("zmx", "attach"): (WS, {"--companions", "--json"}, 2, 2),
    ("restore", "mode"): ({"--socket"}, {"--json"}, 0, 1),
    ("window", "list"): ({"--socket"}, {"--json"}, 0, 0),
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
window = args[args.index("--window") + 1] if "--window" in args else None
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
if args[:1] == [tree.get("stall", "")]:
    import time
    with open(os.path.join(state, "stalled.pid"), "w") as written:
        written.write(str(os.getpid()))
    time.sleep(30)


def value(flag):
    return args[args.index(flag) + 1]


def target():
    wanted = value("--target")
    for node in tree["sessions"]:
        if node["id"] == wanted and in_window(node):
            return node
    sys.exit("no session " + wanted)


# Whether a node is in the window a call names: windows count only in a tree that names them.
def in_window(node):
    if window is None or "windows" not in tree:
        return True
    return node.get("window", tree["windows"][0]) == window


# A refusal as `agtermctl --json` gives it: agterm's reply on standard output, exit 1.
def failed(error, result=None):
    reply = {"ok": False, "error": error}
    if result is not None:
        reply["result"] = result
    print(json.dumps(reply))
    sys.exit(1)


def holder(pane):
    wanted = pane.split(":")[0]
    for node in tree["sessions"]:
        if node["id"] == wanted:
            return node
    sys.exit("no session " + wanted)


def save():
    with open(os.path.join(state, "tree.json"), "w") as written:
        json.dump(tree, written)


# The tree of the stand-in of the Mac that `host` reaches over ssh, refused in agterm's words
# for what that Mac lacks.
def farther(host):
    folder = tree.get("hosts", {}).get(host)
    if folder is None:
        failed("ssh: Could not resolve hostname " + host
               + ": nodename nor servname provided, or not known")
    with open(os.path.join(folder, "tree.json")) as read:
        far = json.load(read)
    for said in far.get("ssh_says", ()):
        failed(said)
    if far.get("agtermctl") is False:
        failed("sh: agtermctl: command not found")
    if far.get("zmx_tree") is False:
        failed("the remote did not return a readable session list")
    return far


# The far Mac's top-level sessions with live daemons: none outside Live sessions.
def offered(far):
    if far.get("restore", "live") != "live":
        return []
    nodes = far["sessions"]
    listed = []
    for n in nodes:
        row = {"id": n["id"], "name": n.get("name"), "workspaceID": n["workspace"]}
        if "parent" in n:
            row["parent"] = n["parent"]
        elif far.get("companions_known", True):
            row["companions"] = [{"id": c["id"], "name": c.get("name")} for c in nodes
                                 if c.get("parent") == n["id"]]
        listed.append(row)
    return listed


# Attach a far session and its companions here, selected, marked remote.
def attach(host, wanted):
    if tree.get("old_cli"):
        sys.stderr.write("Error: Unknown option '--companions'\n")
        sys.exit(64)
    if tree.get("group_attach") is False:
        failed("the running app is too old for group attach")
    far = farther(host)
    offers = offered(far)
    listed = [s for s in offers if s["id"] == wanted and "parent" not in s]
    if not listed or far.get("gone_at_attach"):
        failed("no attachable session " + wanted + " on " + host)
    known = "companions" in listed[0]
    members = listed[0]["companions"] if known else [
        {"id": s["id"], "name": s["name"]} for s in offers if s.get("parent") == wanted]
    tree["count"] = tree.get("count", 0) + 1
    parent = "R-%d" % tree["count"]
    front = tree.get("windows", ["W1"])[0]
    for node in tree["sessions"]:
        node["active"] = False
    tree["sessions"].append({"id": parent, "name": listed[0]["name"],
                             "workspace": tree["workspaces"][0], "window": front,
                             "remoteHost": host, "remoteSessionID": wanted, "active": True})
    outcomes, missing = [], []
    for at, member in enumerate(members):
        if member["id"] in far.get("gone_members", ()):
            outcomes.append({"origin": member["id"], "error": "unavailable on " + host})
            missing.append(member["name"] + " (unavailable on " + host + ")")
            continue
        made = "%s-C%d" % (parent, at + 1)
        tree["sessions"].append({"id": made, "name": member["name"],
                                 "workspace": tree["workspaces"][0], "window": front,
                                 "parent": parent, "remoteHost": host,
                                 "remoteSessionID": member["id"]})
        outcomes.append({"origin": member["id"], "id": made})
    save()
    result = {"id": parent,
              "remoteGroup": {"membershipKnown": known, "companions": outcomes}}
    if missing:
        failed("kept %s (%s) and %d companion(s); not attached: %s" % (
            listed[0]["name"], parent, len(outcomes) - len(missing), ", ".join(missing)), result)
    print(json.dumps({"ok": True, "result": result}))


if args[:2] == ["tree", "--json"]:
    if tree.get("stop_after_second_tree"):
        tree["reads"] = tree.get("reads", 0) + 1
        save()
        if tree["reads"] == 2:
            os.chmod(__file__, 0o644)
    seen = [n for n in tree["sessions"] if in_window(n)]
    spaces = [
        {"id": space, "sessions": [n for n in seen if n["workspace"] == space]}
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
    if "--parent" in args:
        node["parent"] = value("--parent")
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
elif args[:2] == ["restore", "mode"]:
    mode = tree.get("restore", "live")
    print(json.dumps({"result": {"restore": {
        "restartRequired": False, "configured": mode, "requestedAtLaunch": mode, "active": mode,
    }}, "ok": True}))
elif args[:2] == ["window", "list"]:
    print(json.dumps({"ok": True, "result": {"windows": [
        {"id": one, "name": one, "open": True} for one in tree.get("windows", ["W1"])
    ]}}))
elif args[:2] == ["zmx", "tree"]:
    far = farther(args[2])
    print(json.dumps({"result": {"remote": {"host": args[2], "sessions": offered(far)}}}))
elif args[:2] == ["zmx", "attach"]:
    attach(args[2], args[3])
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
