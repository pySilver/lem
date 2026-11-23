# shellcheck shell=bash
# shellcheck disable=SC2034  # the paths and values here are read by the blocks that source this file
# What every block of Lem's script checks shares: the strict mode, the root of the checkout, a
# folder of its own, the interpreter, the count of its checks (checks.sh), and the helpers more than
# one block calls. A block sources this file first and ends with `finish`. Each block runs alone, so
# nothing here depends on the order in which the blocks run.
set -eEuo pipefail

# -P: the folder as it is on disk, the way readlink and git name it: a checkout under /tmp is
# under /private/tmp on macOS.
cd -P "$(dirname "${BASH_SOURCE[0]}")/.."
PROJECT=$PWD/skills/lem/scripts/project.py
CRITERIA=$PWD/skills/lem/scripts/criteria.py
DECISIONS=$PWD/skills/lem/scripts/decisions.py
LAND=$PWD/skills/lem/scripts/land.py
WORK=$(cd "$(mktemp -d)" && pwd -P)
export XDG_CONFIG_HOME="$WORK/config"  # the owner's status (`lem_state.owner_mark`) of this run, never the home directory's
export LEM_SERVE=off  # a board that a check opens starts no board server (`serve.py`), which would outlive the run
# Claude Code's folder of this run, which lists no install: a task's open marks it with this Lem's own release
# (`lem_release.chosen`), never with the release the developer installed, which may be two releases behind the checkout
export CLAUDE_CONFIG_DIR="$WORK/claude"
export LEM_PUSH=record  # the board server's notifications are written to push-record.jsonl in the run's home folder, never sent (`lem_push.py`)
# shellcheck source=tests/checks.sh
. tests/checks.sh
SERVE_PID=""
trap 'stopped; [ -z "$SERVE_PID" ] || { kill -TERM "$SERVE_PID" 2>/dev/null; wait "$SERVE_PID" 2>/dev/null || true; }; rm -rf "$WORK"' EXIT
PY=$(python3 -I -c 'import sys; print(sys.executable)')
# The board server's port of this run, a free one, in the machine's settings of this run: a check that asks for the
# server (lem board, lem serve --ensure) asks this port, never the one of a server the owner runs. The load gate is
# away (`start = 0`, as `lem project load --start none` writes it): under Lem's default of 40 two landings of a block
# would start their checks a minute apart, and a loaded machine would hold every one.
SERVE_PORT=$("$PY" -I -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')
mkdir -p "$XDG_CONFIG_HOME/lem" && printf '[load]\nstart = 0\n[serve]\nport = %s\n' "$SERVE_PORT" > "$XDG_CONFIG_HOME/lem/machine.toml"
SERVE=$PWD/skills/lem/scripts/serve.py
# serve_up: the board server of this run, in the foreground of a background job, with its output in $WORK/serve.out;
# it answers before this returns, and the run's exit stops it
serve_up() {
  "$PY" -B "$SERVE" > "$WORK/serve.out" 2>&1 &
  SERVE_PID=$!
  soon curl -fs -o /dev/null "http://127.0.0.1:$SERVE_PORT/api/server"
}
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
# A stand-in for Codex on PATH, so that both experts of the default seats answer here (`here` in `lem project show`),
# whatever this machine has; a check of one expert alone runs with a PATH that has no codex.
mkdir -p "$WORK/standin" && printf '%s\n' '#!/bin/sh' 'exit 0' > "$WORK/standin/codex" && chmod +x "$WORK/standin/codex"
export PATH="$WORK/standin:$PATH"
# NOCODEX: a PATH with git and no codex, for a check of one expert alone
mkdir -p "$WORK/nocodex" && ln -s "$(command -v git)" "$WORK/nocodex/git"
NOCODEX=$WORK/nocodex

# A stand-in for GitHub's `gh` on PATH, for every repository whose origin is on GitHub (on_github): it finds the
# bare repository the origin stands for through git's own rewrite of the address, keeps that origin's pull requests in a
# file beside it (ORIGIN.gh.json, with one line of each call in ORIGIN.gh.json.log), and merges by moving the base
# branch there: one new commit on the base with --squash, of the head merged into the base as GitHub does (its message
# the --subject and the --body), the head itself with --rebase, or its commits made again on the base when the base moved
# since; a squash that conflicts is refused. GH_REFUSE=LINE makes a merge
# fail with that line, as GitHub's rules do; GH_BASE_FIRST=COMMIT moves the base there just before a merge, as a merge on
# GitHub outside Lem would; GH_EDIT_REFUSE=LINE makes `pr edit` fail with that line.
cat > "$WORK/gh-standin.py" <<'PY'
import json, os, subprocess, sys
args = sys.argv[1:]
def git(*a, where=None): return subprocess.run(["git", *(["-C", where] if where else []), *a], capture_output=True, text=True).stdout.strip()
if args[:2] == ["auth", "status"]:
    sys.exit(0)
url, origin = git("config", "--get", "remote.origin.url"), git("ls-remote", "--get-url", "origin")
name = url.rstrip("/").removesuffix(".git").rsplit("/", 1)[-1]
state_file = origin + ".gh.json"
state = json.load(open(state_file)) if os.path.exists(state_file) else {"prs": {}}
with open(state_file + ".log", "a") as log:
    log.write(json.dumps(args) + "\n")
def opt(key): return args[args.index(key) + 1] if key in args else None
def rev(ref): return git("rev-parse", "--verify", "-q", ref, where=origin)
def shown(n, pr): return {"number": int(n), "url": pr["url"], "state": pr["state"], "mergeable": pr.get("mergeable", "MERGEABLE"), "baseRefName": pr["base"],
                          "headRefOid": rev("refs/heads/" + pr["head"]), "mergeCommit": {"oid": pr["merge"]} if pr["merge"] else None, "body": pr["body"]}
def save():
    with open(state_file + ".new", "w") as out:
        json.dump(state, out)
    os.replace(state_file + ".new", state_file)
out = ""
if args[:2] == ["pr", "list"] and "--head" in args:
    out = json.dumps([{"number": int(n), "url": pr["url"], "headRefOid": rev("refs/heads/" + pr["head"]), "author": {"login": "lem-owner"}}
                      for n, pr in state["prs"].items() if pr["head"] == opt("--head") and pr["state"] == "OPEN"])
elif args[:2] == ["pr", "list"]:
    out = json.dumps([shown(n, pr) for n, pr in sorted(state["prs"].items(), key=lambda item: -int(item[0])) if pr["base"] == opt("--base")])
elif args[:2] == ["pr", "create"]:
    n = str(1 + len(state["prs"]))
    state["prs"][n] = {"url": f"https://github.com/acme/{name}/pull/{n}", "head": opt("--head"), "base": opt("--base"), "title": opt("--title"),
                       "body": open(opt("--body-file")).read(), "state": "OPEN", "merge": None}
    out = state["prs"][n]["url"]
    save()
elif args[:2] == ["pr", "edit"]:
    if os.environ.get("GH_EDIT_REFUSE"):
        sys.exit(os.environ["GH_EDIT_REFUSE"])
    # --base changes the branch the pull request goes into, as a person can on GitHub
    if opt("--base"):
        state["prs"][args[2]]["base"] = opt("--base")
    if opt("--title"):
        state["prs"][args[2]]["title"] = opt("--title")
    if opt("--body-file"):
        state["prs"][args[2]]["body"] = open(opt("--body-file")).read()
    save()
elif args[:2] == ["pr", "view"]:
    out = json.dumps(shown(args[2], state["prs"][args[2]]))
elif args[:2] == ["pr", "merge"]:
    pr = state["prs"][args[2]]
    head = rev("refs/heads/" + pr["head"])
    if os.environ.get("GH_REFUSE"):
        sys.exit(os.environ["GH_REFUSE"])
    if opt("--match-head-commit") != head:
        sys.exit("the head is another commit")
    if os.environ.get("GH_BASE_FIRST"):
        subprocess.run(["git", "-C", origin, "update-ref", "refs/heads/" + pr["base"], os.environ["GH_BASE_FIRST"]], check=True)
    base = rev("refs/heads/" + pr["base"])
    merged = head
    who = ["-c", "user.name=t", "-c", "user.email=t@t"]
    if "--squash" in args:
        # what moved on the base since the head's merge base stays: the head merged into the base, never the head's tree alone
        tree = subprocess.run(["git", "-C", origin, "merge-tree", "--write-tree", base, head], capture_output=True, text=True)
        if tree.returncode != 0:
            sys.exit("Pull request is not mergeable: the merge commit cannot be cleanly created")
        merged = git(*who, "commit-tree", "-p", base, "-m", opt("--subject"), *(["-m", opt("--body")] if opt("--body") else []), tree.stdout.split()[0], where=origin)
    elif subprocess.run(["git", "-C", origin, "merge-base", "--is-ancestor", base, head]).returncode != 0:
        # a rebase onto the base that moved: each commit of the head made again on it, as GitHub's rebase merge does
        merged = base
        for commit in git("rev-list", "--reverse", head, "^" + base, where=origin).split():
            tree = git("merge-tree", "--write-tree", "--merge-base", commit + "^", merged, commit, where=origin).split()[0]
            merged = git(*who, "commit-tree", "-p", merged, "-m", git("log", "-1", "--format=%B", commit, where=origin), tree, where=origin)
    subprocess.run(["git", "-C", origin, "update-ref", "refs/heads/" + pr["base"], merged], check=True)
    pr.update(state="MERGED", merge=merged)
    save()
else:
    sys.exit("gh stand-in: no such command: " + " ".join(args))
print(out)
PY
printf '%s\n' '#!/bin/sh' "exec '$PY' -I '$WORK/gh-standin.py' \"\$@\"" > "$WORK/standin/gh" && chmod +x "$WORK/standin/gh"
# on_github REPO: the repository's origin on GitHub, which git rewrites to a bare repository beside it (REPO.origin.git),
# with the base branch pushed there; the repository has its first commit. The stand-in for `gh` answers for it.
on_github() {
  local origin=$1.origin.git name
  name=$(basename "$1")
  git init -q --bare -b main "$origin"
  git -C "$1" remote add origin "https://github.com/acme/$name.git"
  git -C "$1" config "url.$origin.insteadOf" "https://github.com/acme/$name.git"
  git -C "$1" push -q origin main && git -C "$1" fetch -q origin
}
# gh_prs REPO PYTHON: what the stand-in keeps of REPO's pull requests, as `d`
gh_prs() { "$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])); print(eval(sys.argv[2], {"d": d}))' "$1.origin.git.gh.json" "$2"; }

# A stand-in for Plannotator's `plannotator` on PATH, so that no check reaches the owner's Inbox: each call is one JSON
# line in PLANNOTATOR_CALLS (its words, the JSON it read on stdin, its folder and the variables of its environment that
# name a session). `inbox status --json` prints the file PLANNOTATOR_STATUS and exits with the number in
# PLANNOTATOR_STATUS.exit (0 without one), or, with no such file, says the Inbox does not run and exits 1;
# `inbox call ... send_message -` answers a new message_id (msg_1, msg_2, ...) with a question key for a body that asks
# one, the first answer again for a key it saw, and refuses a `supersedes` that is no list as Plannotator 0.29.0 does
# (`normalizeSupersedes`, read in its binary on 2026-11-22); `inbox call ... read_thread -` a thread with no messages.
export PLANNOTATOR_CALLS=$WORK/plannotator-calls.jsonl PLANNOTATOR_STATUS=$WORK/plannotator-status.json
cat > "$WORK/plannotator-standin.py" <<'PY'
import json, os, sys
args = sys.argv[1:]
body = sys.stdin.read() if args[-1:] == ["-"] else ""
payload = json.loads(body) if body else None
named = sorted(k for k in os.environ if k in ("PLANNOTATOR_SESSION_TAG", "CLAUDECODE", "CODEX_THREAD_ID", "PI_SESSION_ID", "PLANNOTATOR_SESSION_PROJECT"))
with open(os.environ["PLANNOTATOR_CALLS"], "a") as calls:
    calls.write(json.dumps({"args": args, "payload": payload, "cwd": os.getcwd(), "named": named}) + "\n")
status = os.environ["PLANNOTATOR_STATUS"]
if args[:2] == ["inbox", "status"]:
    if not os.path.exists(status):
        print(json.dumps({"state": "stopped", "running": False}))
        sys.exit(1)
    print(open(status).read())
    sys.exit(int(open(status + ".exit").read()) if os.path.exists(status + ".exit") else 0)
if args[:2] == ["inbox", "call"] and "send_message" in args:
    if payload.get("supersedes") is not None and not isinstance(payload["supersedes"], list):
        sys.stderr.write("invalid_supersedes: supersedes: a list of ids, each `<message id>` or `<message id>/<key>`.\n")
        sys.exit(1)
    sent = [json.loads(line) for line in open(os.environ["PLANNOTATOR_CALLS"])]
    keys = [c["payload"]["idempotency_key"] for c in sent if c["payload"] and "send_message" in c["args"]]
    key = payload.get("idempotency_key")
    n = list(dict.fromkeys(keys)).index(key) + 1
    print(json.dumps({"message_id": f"msg_{n}", "thread_id": f"thr_{n}", "questions": [{"key": f"q-{n}"}] if ":::question" in payload.get("body", "") else [],
                      "url": f"http://plannotator.localhost:50026/#thread=thr_{n}", "replayed": keys.count(key) > 1}))
elif args[:2] == ["inbox", "call"] and "read_thread" in args:
    print(json.dumps({"thread": {"messages": []}}))
else:
    sys.exit("usage: plannotator stand-in: no such command: " + " ".join(args))
PY
printf '%s\n' '#!/bin/sh' "exec '$PY' -I '$WORK/plannotator-standin.py' \"\$@\"" > "$WORK/standin/plannotator" && chmod +x "$WORK/standin/plannotator"

# agterm_standin DIR: a stand-in for agtermctl in DIR, for `lem session` (session.py), which keeps agterm's tree in a
# file: each call one JSON line in CALLS. TREE is a list of sessions, each with its `workspace`; `tree` groups them by
# workspace, `session new` adds one (S-1, S-2, ...) that runs claude at the end of its workspace, as agterm did on
# 2026-11-23, `session move --to top|bottom` puts its --target first or last of its workspace, `session close` takes
# its --target away, `rename` and `select` change it, `msg read` gives MAILBOX, and the rest answers ok.
agterm_standin() {
  mkdir -p "$1"
  {
    printf '#!%s\n' "$PY"
    cat <<'STANDIN'
import json, os, sys
args = sys.argv[1:]
with open(os.environ["CALLS"], "a") as calls:
    calls.write(json.dumps(args) + "\n")
nodes = json.load(open(os.environ["TREE"]))
def value(flag):
    return args[args.index(flag) + 1]
def save():
    json.dump(nodes, open(os.environ["TREE"], "w"))
if args[:1] == ["tree"]:
    spaces = {}
    for node in nodes:
        spaces.setdefault(node["workspace"], []).append({key: item for key, item in node.items() if key != "workspace"})
    print(json.dumps({"result": {"tree": {"workspaces": [{"id": ws, "sessions": found} for ws, found in spaces.items()]}}}))
elif args[:2] == ["session", "new"]:
    count = os.environ["TREE"] + ".count"
    number = int(open(count).read()) + 1 if os.path.exists(count) else 1
    open(count, "w").write(str(number))
    nodes.append({"id": "S-%d" % number, "name": value("--name"), "workspace": value("--workspace"), "foreground": ["/usr/local/bin/claude"],
                  "surfaces": [{"kind": "left", "paneID": "P-%d" % number}]})
    save()
    print(json.dumps({"result": {"id": "S-%d" % number}}))
elif args[:2] == ["session", "move"] and "--to" in args:
    moved = next(node for node in nodes if node["id"] == value("--target"))
    nodes.remove(moved)
    first = next((i for i, node in enumerate(nodes) if node["workspace"] == moved["workspace"]), len(nodes))
    nodes.insert(first if value("--to") == "top" else len(nodes), moved)
    save()
elif args[:2] == ["session", "close"]:
    nodes = [node for node in nodes if node["id"] != value("--target")]
    save()
elif args[:2] == ["session", "rename"]:
    for node in nodes:
        if node["id"] == value("--target"):
            node["name"] = args[2]
    save()
elif args[:2] == ["session", "select"]:
    for node in nodes:
        node["active"] = node["id"] == value("--target")
    save()
elif args[:2] == ["msg", "read"]:
    print(os.environ.get("MAILBOX", "[]"))
STANDIN
  } > "$1/agtermctl"
  chmod +x "$1/agtermctl"
}
project() { "$PY" -B "$PROJECT" "$@"; }
status_of() { set +e; "$@" >/dev/null 2>&1; local code=$?; set -e; echo "$code"; }
field() { "$PY" -c 'import json, sys; d = json.load(sys.stdin); print(eval(sys.argv[1], {"d": d}))' "$1"; }
# log_version LOG [ADD]: the version of an event log as the board's stream names it (lem_board_model.log_version), its inode
# and its count of lines, with ADD lines more
log_version() { "$PY" -c 'import os, sys; lines = open(sys.argv[1], "rb").read().count(b"\n") + int(sys.argv[2]); print(f"{os.stat(sys.argv[1]).st_ino}-{lines}")' "$1" "${2:-0}"; }
commit() { git -C "$1" -c user.name=t -c user.email=t@t commit -q --allow-empty -m "$2"; }
# CASE: the run that ends badly, which an important decision of the ladder carries as its story (decisions.py log)
CASE=(--case $'1. Order 1042 has two gift notes, "for Ania" and "for Ola".\n2. The export writes one cell for the note of an order.\n3. The merchant prints the slip with one note, and Ola gets none.'
  --case-was derived --cause "An order has one cell for its note, and every export of notes shares that cell.")
# breaker_doc DIR: a breaker's document and the handoff beside it in the task directory DIR, in the form of
# templates/breaker.md, as a lead writes them before `lem decisions breaker`
# shellcheck disable=SC2016  # the backticks are the document's own marks around a command
breaker_doc() {
  printf '%s\n' '# The gift note has no place that keeps the last column for the total' '' \
    '> [!IMPORTANT]' '> **The build stopped here.** Help, `/lem park gift-note`, or `/lem drop gift-note`.' '' \
    '## Today and after' '' '**Today**:' '' '1. Order 1042 has a gift note.' '2. The build stops before the export.' '' \
    '**After**:' '' '1. Order 1042 has a gift note.' '2. The export has it in a column of its own.' '' \
    '## The case that broke' '' '1. Order 1042 has the note "for Ania".' '2. A reader takes the columns by place and reads the note as the total.' '' \
    '```mermaid' 'flowchart TD' '  A["An order with a note"] --> B{"Where does it go?"}' '  B -->|"A"| C["A column of its own"]' '```' '' \
    '## The root cause' '' 'Readers of the export take its columns by place.' '' \
    '## The options' '' '| | A: a column | B: the notes |' '| --- | --- | --- |' '| What a person sees | a new column | a mixed cell |' '' \
    '## The recommendation' '' '> [!TIP]' '> **A: a column.** Nothing a reader reads moves.' '' \
    '## The assumptions' '' '- Two readers take the columns by place.' > "$1/breaker.md"
  printf '%s\n' '# Handoff' '' '- settled: the criteria' '- open: where the note goes' '- next: the owner helps' > "$1/handoff.md"
}
# soon COMMAND...: run COMMAND until it succeeds, five times a second and for 30 seconds at most,
# for what another process does when a loaded machine starts it late. It never fails by itself:
# the check after it says whether what it waited for came.
soon() {
  local tries=150
  until "$@"; do
    tries=$((tries - 1))
    [ "$tries" -gt 0 ] || return 0
    sleep 0.2
  done
}

# The landing's helpers, for every block that takes a task through land.py.
land() { "$PY" -B "$LAND" "$@"; }
ident() { git -C "$1" config user.name t; git -C "$1" config user.email t@t; }
# plan_in TREE SLUG TEST: the task's plan, a full change's, with one criterion that TEST holds; TEST is `no test: REASON` for a criterion with none
plan_in() {
  local held="   - test: \`$3\` in \`tests/$2.sh\`"
  case "$3" in "no test:"*) held="   - $3" ;; esac
  mkdir -p "$1/docs/plans" "$1/tests"
  printf '%s\n' "# $2" '' '## Acceptance criteria' '' 'Size: full, because the ticket names the word and the file.' '' \
    '1. The file holds the word the owner asked for.' "$held" '' '## Tasks' '' '1. The change.' > "$1/docs/plans/2026-11-15-$2.md"
}
# task_in REPO SLUG FILE TEXT: a full change with a worktree, one commit that writes FILE, its plan and the test of its criterion,
# and the state `ready`. Its landing needs a polish pass (polish_in) and its proposal a read of its criteria (read_in).
task_in() {
  local tree
  project --repo "$1" task-dir "$2" --ask "Put $4 into $3." >/dev/null
  tree=$(project --repo "$1" worktree-dir "$2")
  git -C "$1" worktree add -q "$tree" -b "fix/$2" main
  plan_in "$tree" "$2" "sh tests/$2.sh"
  printf '%s\n' "$4" > "$tree/$3" && echo "grep -qx $4 $3" > "$tree/tests/$2.sh"
  git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: $2"
  project --repo "$tree" state "$2" ready "the report is written" >/dev/null
}
# small_task_in REPO SLUG FILE TEXT: a small change with a worktree: its one criterion in the task directory, approved in
# the owner's name, with the test line under it; one commit that writes FILE and the test, no plan; and the state `ready`
small_task_in() {
  local tree directory
  directory=$(project --repo "$1" task-dir "$2" --ask "Put $4 into $3.")
  printf '%s\n' '## Acceptance criteria' '' 'Size: small, because the request is one sentence.' '' '1. The file holds the word the owner asked for.' > "$directory/criteria.md"
  "$PY" -B "$CRITERIA" --repo "$1" approve "$2" --file "$directory/criteria.md" --small >/dev/null
  printf '%s\n' "   - test: \`sh tests/$2.sh\` in \`tests/$2.sh\`" >> "$directory/criteria.md"
  tree=$(project --repo "$1" worktree-dir "$2")
  git -C "$1" worktree add -q "$tree" -b "fix/$2" main
  mkdir -p "$tree/tests" && printf '%s\n' "$4" > "$tree/$3" && echo "grep -qx $4 $3" > "$tree/tests/$2.sh"
  git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: $2"
  project --repo "$tree" state "$2" ready "the small change is built" >/dev/null
}
# read_in REPO SLUG: the personas' read of the plan's criteria by the lead, as a full change from a complete request has it: two personas of one
# model family, nobody confused. A full change is not proposed without one.
read_in() {
  local digest
  digest=$("$PY" -B "$CRITERIA" --repo "$1" digest "$2" | field 'd["digest"]')
  project --repo "$1" log "$2" criteria.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$digest" >/dev/null
}
# polish_in REPO SLUG: the polish pass of a full change's landing, which here changes nothing; none when this landing's pass is done already
polish_in() {
  local started
  started=$(land --repo "$1" polish "$2") || return 1
  if [ "$(field 'd["done"]' <<<"$started")" = False ]; then land --repo "$1" polish "$2" --done >/dev/null; fi
}
status_in() { project --repo "$1" tasks | field "next(t[\"status\"] for t in d if t[\"slug\"] == \"$2\")"; }
kept_in() { "$PY" -c 'import json, sys; print(json.load(open(sys.argv[1])).get(sys.argv[2]))' "$1/.lem/state/tasks/$2/landing.json" "$3"; }
# tip_of SLUG: the commit the task's worktree is at, the one task of that slug in this run's repositories (refused when
# there are none or more than one), which a review's record names as the tip it read
tip_of() {
  local found
  found=$(find "$WORK" -maxdepth 4 -type d -path "*/.lem/worktrees/$1" -prune)
  if [ -z "$found" ] || [ "$(grep -c '' <<<"$found")" != 1 ]; then
    echo "tip_of: no one worktree of $1 in $WORK: ${found:-none}" >&2
    return 1
  fi
  git -C "$found" rev-parse HEAD
}
# record SLUG N JSON: the file that says what a review was and what it found, as the Nth start of the task's review of the
# tip its worktree is at; its careful call is "not careful" with one sentence of why, unless JSON makes its own
NOT_CAREFUL="the diff reaches no topic of the settings"
record() {
  local tip
  tip=$(tip_of "$1") || return 1
  "$PY" -c 'import json, sys; json.dump({"attempt": int(sys.argv[1]), "tip": sys.argv[5], "careful": False, "careful_why": sys.argv[4], **json.loads(sys.argv[2])}, open(sys.argv[3], "w"))' "$2" "$3" "$WORK/record.json" "$NOT_CAREFUL" "$tip"
  echo "$WORK/record.json"
}
# clean SLUG N: the record of one read that found nothing
clean() { record "$1" "$2" '{"kind": "read", "answered": ["codex"]}'; }
# merge_read REPO SLUG [VERDICT] [BASE_CALL]: the merge agent's read of a proposed task, its brief and then its reply with
# VERDICT (merge by default) written down, and on a base that moved since the checks a second line with BASE_CALL (safe or
# another round) and its sentence of why; prints what the step printed
merge_read() {
  local brief answer
  brief=$(land --repo "$1" merge-review "$2") || return 1
  answer=$(field 'd["answer"]' <<<"$brief")
  printf 'Verdict: %s. The change does what its criterion says.\n' "${3:-merge}" > "$answer"
  case ${4:-} in
    safe) printf 'Base: safe. What moved touches nothing the change rests on.\n' >> "$answer" ;;
    ?*) printf 'Base: %s. What moved changes a file the change rests on.\n' "$4" >> "$answer" ;;
  esac
  printf '\nIts test proves it, and the task took as long as expected.\n' >> "$answer"
  land --repo "$1" merge-review "$2" --file "$answer" --tip "$(field 'd["tip"]' <<<"$brief")" --base "$(field 'd["base"]' <<<"$brief")"
}
# the notes of a pull request, and the same notes with the migration a careful request needs
NOTES=$WORK/notes.md
printf '%s\n' '## Decisions' '' 'none' '' '## Left open' '' 'none' '' '## Worth a look' '' '- the one line of the file.' '' '## Filed in the backlog' '' 'none' '' '## Not done' '' 'none' > "$NOTES"
MIG=$WORK/notes-migration.md
cp "$NOTES" "$MIG" && printf '%s\n' '' '## Migration' '' 'none' >> "$MIG"

# The block's last line, which tests/test-lem.sh reads: `all checks passed`, or the count that failed.
finish() {
  results_add_up
  finished=yes
  if [ "$fails" -gt 0 ]; then
    printf '\n%s check(s) failed\n' "$fails"
    exit 1
  fi
  printf '\nall checks passed\n'
}

# the count of the block's checks, before the first of them
collected
