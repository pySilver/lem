#!/usr/bin/env bash
# Tasks that an older Lem proposed, finished by the Lem of now. The scripts of the commit before a task
# got a type and a size, and before its stories became acceptance criteria, take three tasks to `open`, each with a pull request on a GitHub remote: a small
# change, a bug whose investigation found its cause, and a full change with its plan, its approval and
# the personas' read. A trial repository held three such tasks when the names changed (2026-11-17), with
# `stories.md`, `stories.json`, `## Stories`, `stories.read` and `kind:` lines, which stay as written. The
# scripts of now list them with their types, land them by each way there is, clean them, propose one of
# them again, and the board draws them. A later change may drop this file with the old forms the scripts
# read, once no task that an older Lem proposed is open.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

# The scripts of the commit before the rename. A shallow clone may not have it: then nothing here runs.
BEFORE=9a35e30
if ! git cat-file -e "$BEFORE^{commit}" 2>/dev/null; then
  printf 'SKIP the tasks an older Lem proposed: this clone does not have commit %s\n' "$BEFORE"
  finish
  exit 0
fi
OLDLEM=$WORK/old-lem
mkdir -p "$OLDLEM" && git archive "$BEFORE" skills | tar -x -C "$OLDLEM"
OLDS=$OLDLEM/skills/lem/scripts

# A GitHub remote, through a stand-in for `gh` that keeps the pull requests in a file and merges in the
# bare repository, as tests/lem-land-github.sh has it.
GHO=$WORK/origin.git
OT=$WORK/old-tasks
git init -q --bare -b main "$GHO"
git clone -q "$GHO" "$OT" 2>/dev/null && ident "$OT"
git -C "$OT" config remote.origin.url https://github.com/acme/shop.git
git -C "$OT" config "url.$GHO.insteadOf" https://github.com/acme/shop.git
mkdir -p "$WORK/bin"
cat > "$WORK/gh.py" <<'PY'
import json, os, subprocess, sys
state_file, origin = os.environ["GH_STATE"], os.environ["GH_ORIGIN"]
state = json.load(open(state_file)) if os.path.exists(state_file) else {"prs": {}, "calls": []}
args = sys.argv[1:]
state["calls"].append(args)
def opt(name): return args[args.index(name) + 1] if name in args else None
def rev(ref): return subprocess.run(["git", "-C", origin, "rev-parse", "--verify", "-q", ref], capture_output=True, text=True).stdout.strip()
out = ""
if args[:2] == ["pr", "list"]:
    out = json.dumps([{"number": int(n), "url": pr["url"]} for n, pr in state["prs"].items() if pr["head"] == opt("--head") and pr["state"] == "OPEN"])
elif args[:2] == ["pr", "create"]:
    n = str(2 + len(state["prs"]))
    state["prs"][n] = {"url": "https://github.com/acme/shop/pull/" + n, "head": opt("--head"), "base": opt("--base"), "title": opt("--title"),
                       "body": open(opt("--body-file")).read(), "state": "OPEN", "merge": None}
    out = state["prs"][n]["url"]
elif args[:2] == ["pr", "edit"]:
    state["prs"][args[2]].update(title=opt("--title"), body=open(opt("--body-file")).read())
elif args[:2] == ["pr", "view"]:
    pr = state["prs"][args[2]]
    out = json.dumps({"state": pr["state"], "headRefOid": rev("refs/heads/" + pr["head"]), "mergeCommit": {"oid": pr["merge"]} if pr["merge"] else None})
elif args[:2] == ["pr", "merge"]:
    pr = state["prs"][args[2]]
    head = rev("refs/heads/" + pr["head"])
    if opt("--match-head-commit") != head:
        sys.exit("the head is another commit")
    subprocess.run(["git", "-C", origin, "update-ref", "refs/heads/" + pr["base"], head], check=True)
    pr.update(state="MERGED", merge=head)
else:
    sys.exit("gh stand-in: no such command: " + " ".join(args))
json.dump(state, open(state_file, "w"))
print(out)
PY
printf '%s\n' '#!/bin/sh' "exec '$PY' -I '$WORK/gh.py' \"\$@\"" > "$WORK/bin/gh" && chmod +x "$WORK/bin/gh"
export GH_STATE=$WORK/gh.json GH_ORIGIN=$GHO
export PATH="$WORK/bin:$PATH"
oproject() { "$PY" -B "$OLDS/project.py" --repo "$OT" "$@"; }
ostories() { "$PY" -B "$OLDS/stories.py" --repo "$OT" "$@"; }
oland() { "$PY" -B "$OLDS/land.py" --repo "$OT" "$@"; }
nland() { land --repo "$OT" "$@"; }
oproject init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[gate]' 'commands = ["true"]' > "$OT/.lem/project.toml"
git -C "$OT" add -A && git -C "$OT" commit -q -m "chore: start" && git -C "$OT" push -q origin main

# old_small SLUG FILE: the one story of a small change in the task directory (`stories.md`), as the older Lem wrote and approved it
old_small() {
  local directory
  directory=$OT/.lem/state/tasks/$1
  printf '%s\n' '## Stories' '' 'Kind: correction, because the request is one sentence.' '' "1. The file $2 holds the word the owner asked for." > "$directory/stories.md"
  ostories approve "$1" --file "$directory/stories.md" --correction >/dev/null
  printf '%s\n' "   - test: \`sh tests/$1.sh\` in \`tests/$1.sh\`" >> "$directory/stories.md"
}
# old_change SLUG FILE: the worktree on the task's branch, one commit with FILE and its test
old_change() {
  local tree
  tree=$(oproject worktree-dir "$1")
  git -C "$OT" worktree add -q "$tree" -b "fix/$1" main
  mkdir -p "$tree/tests" && echo word > "$tree/$2" && echo "grep -qx word $2" > "$tree/tests/$1.sh"
  git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: $1"
}
# old_propose SLUG: the older landing up to the pull request
old_propose() {
  oland start "$1" >/dev/null && oland base "$1" >/dev/null && oland gate "$1" >/dev/null
  oland read "$1" --record "$(clean 1)" >/dev/null
  oland propose "$1" --title "fix: $1" --notes "${2:-$NOTES}" >/dev/null
}

# A small change: its story in the task directory with `Kind: correction`, approved by Lem with --correction.
oproject task-dir old-small --ask "Put the word into small.txt." >/dev/null
old_small old-small small.txt
old_change old-small small.txt
oproject state old-small building "one builder makes the small change" "small change: one builder" "kind: correction, because the ask is one rule in the owner's own sentence" >/dev/null
oproject state old-small ready "the small change is built" >/dev/null
old_propose old-small

# A bug: investigated first (`kind: bug`, `investigation kind=bug call=correction`), then a small change.
oproject task-dir old-bug --ask "The word is missing from bug.txt." >/dev/null
oproject state old-bug building "a builder reproduces the bug and finds its cause" "investigation: bug" "kind: bug, because the file is wrong today" >/dev/null
oproject log old-bug investigation.start kind=bug >/dev/null
old_change old-bug bug.txt
oproject log old-bug investigation kind=bug call=correction "line=nothing writes the word into bug.txt" where=bug.txt reproduced:=true >/dev/null
old_small old-bug bug.txt
oproject state old-bug building "the investigation found the cause; one builder makes the small change" "small change: one builder" "kind: bug, because the file is wrong today" >/dev/null
oproject state old-bug ready "the small change is built" >/dev/null
old_propose old-bug

# A full change: its stories approved by the owner after the personas' read, its plan with `## Stories` and `Kind: feature`.
oproject task-dir old-full --ask "Put the word into full.txt, and say so in the README." >/dev/null
printf '%s\n' '## Stories' '' 'Kind: feature, because the file gets a word and the README a line.' '' '1. The file full.txt holds the word the owner asked for.' > "$WORK/full-stories.md"
digest=$(ostories digest old-full --file "$WORK/full-stories.md" | field 'd["digest"]')
oproject state old-full held "the interview waits for the owner" "kind: feature, because the file gets a word and the README a line" >/dev/null
oproject log old-full stories.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest" >/dev/null
ostories approve old-full --file "$WORK/full-stories.md" >/dev/null
oproject state old-full building "lead: builder" >/dev/null
old_change old-full full.txt
tree=$OT/.lem/worktrees/old-full
mkdir -p "$tree/docs/plans"
printf '%s\n' '# old-full' '' '## Stories' '' 'Kind: feature, because the file gets a word and the README a line.' '' '1. The file full.txt holds the word the owner asked for.' \
  "   - test: \`sh tests/old-full.sh\` in \`tests/old-full.sh\`" '' '## Tasks' '' '1. The word.' > "$tree/docs/plans/20261117-old-full.md"
git -C "$tree" add -A && git -C "$tree" commit -q -m "docs(plans): old-full"
ostories record old-full >/dev/null
oproject state old-full ready "the report is written" >/dev/null
oland start old-full >/dev/null && oland base old-full >/dev/null
oland polish old-full >/dev/null && oland polish old-full --done >/dev/null
oland gate old-full >/dev/null && oland read old-full --record "$(clean 1)" >/dev/null
oland propose old-full --title "feat: old-full" --notes "$NOTES" >/dev/null

# The scripts of now list the three as they are, with the type each older kind reads as.
listed=$(project --repo "$OT" tasks | field '[(t["slug"], t["status"], (t["type"] or {}).get("type"), (t["investigation"] or {}).get("type"), (t["investigation"] or {}).get("call")) for t in d]')
if [ "$listed" = "[('old-bug', 'open', 'fix', 'fix', 'small'), ('old-full', 'open', 'feat', None, None), ('old-small', 'open', 'fix', None, None)]" ]; then
  pass "the tasks an older Lem proposed are listed as open, a kind line read as its type and an older investigation's record in the form of now"
else
  fail "the tasks of an older Lem: $listed"
fi

# The bug lands by an agent's merge: the landing reads its older story, approval and review, finds it green, and the forge merges it.
merged_bug=$(nland land old-bug --by agent 2>&1 | field '(d["pull_request"]["number"], d["left_behind"])' 2>&1 || true)
clean_bug=$(nland clean old-bug 2>&1 | field '(d["worktree"], d["branch"], d["remote"])' 2>&1 || true)
if [ "$merged_bug" = "(3, None)" ] && [ "$(status_in "$OT" old-bug)" = landed ] && [ "$clean_bug" = "(True, 'fix/old-bug', 'fix/old-bug')" ] \
  && [ "$(git -C "$OT" show main:bug.txt)" = word ]; then
  pass "a bug an older Lem proposed lands by an agent's merge, since the landing finds its older records green, and clean removes its worktree and both its branches"
else
  fail "the bug of an older Lem: $merged_bug / $clean_bug / $(status_in "$OT" old-bug)"
fi

# The small change is merged by the owner on the forge; `merged` finishes it, and `clean` removes it.
head=$(git -C "$GHO" rev-parse refs/heads/fix/old-small)
git -C "$GHO" update-ref refs/heads/main "$(git -C "$GHO" -c user.name=t -c user.email=t@t commit-tree -p main -p "$head" -m "Merge pull request #2" "$head^{tree}")"
"$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])); d["prs"]["2"].update(state="MERGED", merge=sys.argv[2]); json.dump(d, open(sys.argv[1], "w"))' "$GH_STATE" "$(git -C "$GHO" rev-parse main)"
merged_small=$(nland merged old-small 2>&1 | field 'd["pull_request"]["number"]' 2>&1 || true)
clean_small=$(nland clean old-small 2>&1 | field '(d["worktree"], d["branch"])' 2>&1 || true)
if [ "$merged_small" = 2 ] && [ "$(status_in "$OT" old-small)" = landed ] && [ "$clean_small" = "(True, 'fix/old-small')" ] && [ ! -e "$OT/.lem/worktrees/old-small" ]; then
  pass "a small change an older Lem proposed, which the owner merged on the forge, is finished by merged and cleaned"
else
  fail "the small change of an older Lem: $merged_small / $clean_small / $(status_in "$OT" old-small)"
fi

# The full change: the base moved twice, so its landing starts over with the scripts of now, which read its
# older plan, approval and read and propose it again on the same pull request; then the owner's word lands it.
project --repo "$OT" state old-full ready --start-over "the base moved: the landing starts over" >/dev/null
nland start old-full >/dev/null && nland base old-full >/dev/null
polished=$(nland polish old-full 2>&1 | field 'd["done"]' 2>&1 || true)
nland polish old-full --done >/dev/null 2>&1 || true
gated=$(nland gate old-full 2>&1 | field 'd["green"]' 2>&1 || true)
nland read old-full --record "$(clean 1)" >/dev/null 2>&1 || true
again=$(nland propose old-full --title "feat: old-full" --notes "$NOTES" 2>&1 | field '(d["green"], d["pull_request"]["number"])' 2>&1 || true)
text=$OT/.lem/state/tasks/old-full/pr.md
landed_full=$(nland land old-full --by owner 2>&1 | field 'd["pull_request"]["number"]' 2>&1 || true)
clean_full=$(nland clean old-full 2>&1 | field 'd["worktree"]' 2>&1 || true)
if [ "$polished" = False ] && [ "$gated" = True ] && [ "$again" = "(True, 4)" ] \
  && grep -qxF -- "1. The file full.txt holds the word the owner asked for." "$text" && grep -qx "## Acceptance criteria" "$text" \
  && [ -f "$OT/.lem/state/tasks/old-full/stories.json" ] && [ ! -e "$OT/.lem/state/tasks/old-full/criteria.json" ] \
  && grep -qF -- "read by 2 of 2 personas asked, two model families (opus, sol); nobody confused; the owner approved them on" "$text" \
  && [ "$landed_full" = 4 ] && [ "$(status_in "$OT" old-full)" = landed ] && [ "$clean_full" = True ] && [ "$(git -C "$OT" show main:full.txt)" = word ]; then
  pass "a full change an older Lem proposed is checked, reviewed and proposed again by the scripts of now on its own pull request, green, from its older plan, approval and read, and lands by the owner's word"
else
  fail "the full change of an older Lem: $polished / $gated / $again / $landed_full / $clean_full / $(cat "$text" 2>/dev/null)"
fi

# The board draws the tasks of the older Lem: their types, the small change's approval in the owner's name, the full change's read.
chrome=""
for c in google-chrome chromium chromium-browser "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
  if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then chrome=$c; break; fi
done
SHOWN=$(cat <<'PY'
import sys
from html.parser import HTMLParser
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.skip = 0; self.text = []
    def handle_starttag(self, tag, attrs): self.skip += tag in ("script", "style")
    def handle_endtag(self, tag): self.skip -= tag in ("script", "style")
    def handle_data(self, data):
        if not self.skip: self.text.append(data)
p = P(); p.feed(open(sys.argv[1], encoding="utf-8").read())
shown = " ".join(" ".join(p.text).split())
missing = [want for want in sys.argv[2:] if not want.startswith("!") and want not in shown]
missing += [f"no {want[1:]!r}" for want in sys.argv[2:] if want.startswith("!") and want[1:] in shown]
if "does not parse" in shown: missing.append("no problem on the page")
print("; ".join(missing))
sys.exit(bool(missing))
PY
)
if [ -z "$chrome" ]; then
  printf 'SKIP the board of the tasks an older Lem proposed: no Chrome or Chromium on this machine\n'
else
  draw() {
    "$PY" -B "$PWD/skills/lem/scripts/board.py" --repo "$OT" ${2:+--task "$2"} --no-open >/dev/null
    mkdir -p "$WORK/chrome-tmp" && TMPDIR="$WORK/chrome-tmp" MAC_CHROMIUM_TMPDIR="$WORK/chrome-tmp" "$chrome" --headless=new --disable-gpu --no-sandbox --no-first-run \
      --use-mock-keychain --user-data-dir="$WORK/chrome" --virtual-time-budget=5000 --dump-dom "file://$OT/.lem/state/$1.html" > "$WORK/$1.dom" 2>/dev/null || true
  }
  draw task-old-bug old-bug
  draw task-old-full old-full
  if [ ! -s "$WORK/task-old-bug.dom" ]; then
    printf 'SKIP the board of the tasks an older Lem proposed: %s printed no page\n' "$chrome"
  elif why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-old-bug.dom" "fix" "Taken as a small change: Lem approved its one criterion in your name" "small change, because the request is one sentence." \
      "nothing writes the word into bug.txt" "!kind: bug" "!correction, because" "!stories" "!one story") \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-old-full.dom" "feat" "full change, because the file gets a word and the README a line." "Approved by you" \
      "The file full.txt holds the word the owner asked for." "Acceptance criteria" "read by 2 of 2 personas" "!feature, because" "!stories" "!one story"); then
    pass "the board draws the tasks an older Lem proposed with their types, the small change's approval in the owner's name, its cause, and the full change's acceptance criteria"
  else
    fail "the board of the tasks of an older Lem: $why"
  fi
fi

finish
