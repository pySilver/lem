#!/usr/bin/env bash
# The landing with a GitHub remote, through a stand-in for `gh`, and with no pull requests.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

# A GitHub remote: the task ends as a pull request. A stand-in for the `gh` command keeps the pull
# requests in a file and merges in the bare repository, and the remote's address is rewritten to it.
GHO=$WORK/gh-origin.git
GHS=$WORK/gh-shop
git init -q --bare -b main "$GHO"
git clone -q "$GHO" "$GHS" 2>/dev/null && ident "$GHS"
git -C "$GHS" config remote.origin.url https://github.com/acme/shop.git
git -C "$GHS" config "url.$GHO.insteadOf" https://github.com/acme/shop.git
project --repo "$GHS" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[gate]' 'commands = ["true"]' > "$GHS/.lem/project.toml"
git -C "$GHS" add -A && git -C "$GHS" commit -q -m "chore: start" && git -C "$GHS" push -q origin main
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
    n = str(7 + len(state["prs"]))
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
gh_land() { PATH="$WORK/bin:$PATH" GH_STATE="$WORK/gh.json" GH_ORIGIN="$GHO" "$PY" -B "$LAND" --repo "$GHS" "$@"; }
gh_state() { "$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])); print(eval(sys.argv[2], {"d": d}))' "$WORK/gh.json" "$1"; }
# gh_set PYTHON [FILE]: change the stand-in's pull requests as the forge would, written whole, since a watch may read them at that moment
gh_set() { "$PY" -c 'import json, os, sys; d = json.load(open(sys.argv[2])); exec(sys.argv[1]); json.dump(d, open(sys.argv[2] + ".set", "w")); os.replace(sys.argv[2] + ".set", sys.argv[2])' "$1" "${2:-$WORK/gh.json}"; }
gh_checked() { gh_land start "$1" >/dev/null && gh_land base "$1" >/dev/null && gh_land gate "$1" >/dev/null; }
small_task_in "$GHS" pr-change p.txt nine
out=$(gh_land start pr-change)
gh_land base pr-change >/dev/null && gh_land gate pr-change >/dev/null && gh_land read pr-change --record "$(clean 1)" >/dev/null
proposed=$(gh_land propose pr-change --title "fix: nine" --notes "$NOTES")
tip=$(git -C "$GHS/.lem/worktrees/pr-change" rev-parse HEAD)
if [ "$(field 'd["forge"]' <<<"$out")" = github ] && [ "$(field 'd["pull_request"]' <<<"$proposed")" = "{'number': 7, 'url': 'https://github.com/acme/shop/pull/7'}" ] \
  && [ "$(status_in "$GHS" pr-change)" = open ] && grep -q "pull request https://github.com/acme/shop/pull/7" "$GHS/.lem/state/tasks/pr-change/state.md" \
  && [ "$(git -C "$GHO" rev-parse refs/heads/fix/pr-change)" = "$tip" ] \
  && [ "$(gh_state '(d["prs"]["7"]["title"], d["prs"]["7"]["base"], d["prs"]["7"]["head"], "## The request" in d["prs"]["7"]["body"], "## Not done" in d["prs"]["7"]["body"])')" = "('fix: nine', 'main', 'fix/pr-change', True, True)" ]; then
  pass "with a GitHub remote the branch is pushed and a pull request is opened with the title and the text, and the task is open with its address"
else
  fail "propose with a forge: $out / $proposed / $(cat "$WORK/gh.json" 2>/dev/null)"
fi
# A second proposal updates the same pull request: once from what was kept, once after the record of it was lost.
project --repo "$GHS" state pr-change ready --start-over "the landing starts over" >/dev/null
gh_checked pr-change
again=$(kept_in "$GHS" pr-change pr)/$(kept_in "$GHS" pr-change reads)
gh_land read pr-change --record "$(clean 1)" >/dev/null && gh_land propose pr-change --title "fix: nine, again" --notes "$NOTES" >/dev/null
"$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])); d.pop("pr"); json.dump(d, open(sys.argv[1], "w"))' "$GHS/.lem/state/tasks/pr-change/landing.json"
gh_checked pr-change && gh_land propose pr-change --title "fix: nine, a third time" --notes "$NOTES" >/dev/null
if [ "$(gh_state '(len(d["prs"]), d["prs"]["7"]["title"], sum(c[:2] == ["pr", "create"] for c in d["calls"]), sum(c[:2] == ["pr", "edit"] for c in d["calls"]))')" = "(1, 'fix: nine, a third time', 1, 2)" ] \
  && [ "$(kept_in "$GHS" pr-change pr)" = "{'number': 7, 'url': 'https://github.com/acme/shop/pull/7'}" ] \
  && [ "$again" = "{'number': 7, 'url': 'https://github.com/acme/shop/pull/7'}/None" ]; then
  pass "a task whose landing starts over starts its reviews over and keeps its pull request; a second proposal changes the one that is there, also when the record of it was lost: the forge is asked, and no second one is opened"
else
  fail "a second proposal: $(cat "$WORK/gh.json")"
fi
out=$(gh_land land pr-change --by agent)
if [ "$(field '(d["merged"], d["pull_request"]["number"], d["left_behind"])' <<<"$out")" = "('$tip', 7, None)" ] && [ "$(status_in "$GHS" pr-change)" = landed ] \
  && [ "$(gh_state '[c for c in d["calls"] if c[:2] == ["pr", "merge"]]')" = "[['pr', 'merge', '7', '--match-head-commit', '$tip', '--rebase']]" ] \
  && [ "$(git -C "$GHS" rev-parse main)" = "$tip" ] && [ -f "$GHS/p.txt" ]; then
  pass "a pull request is merged through the forge, only at the commit that was proposed, and the main checkout follows"
else
  fail "merging a pull request: $out"
fi
out=$(gh_land clean pr-change)
if [ "$(field '(d["worktree"], d["branch"])' <<<"$out")" = "(True, 'fix/pr-change')" ] && [ -z "$(git -C "$GHO" branch --list fix/pr-change)" ]; then
  pass "after the merge the worktree and the branch go, the forge's copy of the branch too"
else
  fail "clean after a merged pull request: $out"
fi
# The base moves before the merge; then the owner merges on the forge himself, as one commit.
small_task_in "$GHS" pr-squashed q.txt ten
gh_checked pr-squashed && gh_land read pr-squashed --record "$(clean 1)" >/dev/null && gh_land propose pr-squashed --title "fix: ten" --notes "$NOTES" >/dev/null
gh_other=$WORK/gh-other
git clone -q "$GHO" "$gh_other" && ident "$gh_other"
echo late > "$gh_other/late.txt" && git -C "$gh_other" add -A && git -C "$gh_other" commit -q -m "feat: late" && git -C "$gh_other" push -q origin main
err=$(gh_land land pr-squashed --by agent 2>&1 || true)
early=$(gh_land merged pr-squashed 2>&1 || true)
# the checks start again for the base that moved, and the owner merges on the forge meanwhile
gh_land start pr-squashed >/dev/null
git -C "$gh_other" merge -q --squash origin/fix/pr-squashed && git -C "$gh_other" commit -q -m "fix: ten (#8)" && git -C "$gh_other" push -q origin main
oid=$(git -C "$gh_other" rev-parse HEAD)
gh_set "d['prs']['8'].update(state='MERGED', merge='$oid')"
out=$(gh_land merged pr-squashed)
if grep -q "origin/main moved after the checks ran, by files the gate reads (late.txt)" <<<"$err" && grep -q "the pull request is not merged yet" <<<"$early" \
  && [ "$(gh_state 'sum(c[:3] == ["pr", "merge", "8"] for c in d["calls"])')" = 0 ] \
  && [ "$(field '(d["merged"], d["left_behind"])' <<<"$out")" = "('$oid', None)" ] && [ "$(status_in "$GHS" pr-squashed)" = landed ] && [ "$(git -C "$GHS" rev-parse main)" = "$oid" ]; then
  pass "a pull request is not merged over a base that moved by files the gate reads; one the owner merged on the forge as one commit is finished by its own step, also while the task has the landing line again"
else
  fail "a pull request the owner merged: $err / $early / $out"
fi
# A commit that came after the one the forge merged is work nobody merged: its branch stays. And a
# forge that refuses to delete its copy of the branch is said, and the next run tries again.
tree=$GHS/.lem/worktrees/pr-squashed
head=$(git -C "$tree" rev-parse HEAD)
echo more > "$tree/q2.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: after the merge"
after=$(gh_land clean pr-squashed 2>&1 || true)
kept_branch=$(git -C "$GHS" branch --list fix/pr-squashed)
git -C "$GHS" branch -q -f fix/pr-squashed "$head"
# a branch on the forge whose name ends the same way and holds the merged commit: it is not the task's branch
git -C "$GHO" branch -q archive/fix/pr-squashed "$head"
# shellcheck disable=SC2016  # the hook's own argument, read when the hook runs
printf '%s\n' '#!/bin/sh' 'case "$3" in 0000000000000000000000000000000000000000) echo "no deletion here" >&2; exit 1 ;; esac' > "$GHO/hooks/update" && chmod +x "$GHO/hooks/update"
refused=$(gh_land clean pr-squashed 2>&1 || true)
still=$(git -C "$GHS" branch --list fix/pr-squashed)/$(git -C "$GHO" branch --list fix/pr-squashed)
rm "$GHO/hooks/update"
# somebody pushed to the task's branch on the forge after the merge: that copy stays
later=$(git -C "$GHO" -c user.name=t -c user.email=t@t commit-tree -p "$head" -m "fix: pushed later" "$head^{tree}")
git -C "$GHO" update-ref refs/heads/fix/pr-squashed "$later"
left=$(gh_land clean pr-squashed | field '(d["branch"], d["remote"], d["remote_left"] is not None)')
on_forge=$(git -C "$GHO" rev-parse refs/heads/fix/pr-squashed)
git -C "$GHO" update-ref refs/heads/fix/pr-squashed "$head" && git -C "$GHS" branch -q fix/pr-squashed "$head"
cleaned=$(gh_land clean pr-squashed)
if grep -q "the forge merged ${head:0:9}, and the branch has commits after it" <<<"$after" && [ -n "$kept_branch" ] \
  && grep -q "push failed: .*no deletion here" <<<"$refused" && [ "$(tr -d ' *' <<<"$still")" = "fix/pr-squashed/fix/pr-squashed" ] \
  && [ "$left" = "('fix/pr-squashed', None, True)" ] && [ "$on_forge" = "$later" ] && [ -n "$(git -C "$GHO" branch --list archive/fix/pr-squashed)" ] \
  && [ "$(field '(d["worktree"], d["branch"], d["remote"])' <<<"$cleaned")" = "(False, 'fix/pr-squashed', 'fix/pr-squashed')" ] \
  && [ -z "$(git -C "$GHS" branch --list fix/pr-squashed)" ] && [ -z "$(git -C "$GHO" branch --list fix/pr-squashed)" ]; then
  pass "after a merge the forge made as one commit, the branch goes only when its tip is the commit that was merged; a deletion the forge refuses is an error that keeps the local branch; the forge's copy stays when it holds a later commit, whatever another branch with the same last words holds; and a run with nothing in the way removes both"
else
  fail "clean after a merge on the forge: $after / $kept_branch / $refused / $still / $left / $cleaned"
fi
# A proposal the forge's step refused is none: no `proposed` event, and the task keeps the landing line.
# With no `gh` on PATH the refusal names the command; a forge that fails is said with what it said.
small_task_in "$GHS" pr-guards r.txt twelve
gh_checked pr-guards && gh_land read pr-guards --record "$(clean 1)" >/dev/null
mkdir -p "$WORK/no-gh" "$WORK/bad-bin"
ln -s "$(command -v git)" "$WORK/no-gh/git"
printf '%s\n' '#!/bin/sh' 'echo "HTTP 502: the forge is down" >&2' 'exit 1' > "$WORK/bad-bin/gh" && chmod +x "$WORK/bad-bin/gh"
no_gh=$(PATH="$WORK/no-gh" "$PY" -B "$LAND" --repo "$GHS" propose pr-guards --title "fix: twelve" --notes "$NOTES" 2>&1 || true)
down=$(PATH="$WORK/bad-bin:$PATH" "$PY" -B "$LAND" --repo "$GHS" propose pr-guards --title "fix: twelve" --notes "$NOTES" 2>&1 || true)
unproposed=$(grep -c '"event": "proposed", "task": "pr-guards"' "$GHS/.lem/state/events.jsonl" || true)
unopened=$(status_in "$GHS" pr-guards)
number=$(gh_land propose pr-guards --title "fix: twelve" --notes "$NOTES" | field 'd["pull_request"]["number"]')
if grep -qF "the remote is GitHub and the \`gh\` command is not on PATH: install it and sign in, then run this again" <<<"$no_gh" && ! grep -q Traceback <<<"$no_gh" \
  && grep -qF "HTTP 502: the forge is down" <<<"$down" && [ "$unproposed" = 0 ] && [ "$unopened" = landing ] \
  && [ "$(grep -c '"event": "proposed", "task": "pr-guards"' "$GHS/.lem/state/events.jsonl")" = 1 ] && [ "$(status_in "$GHS" pr-guards)" = open ]; then
  pass "a proposal that the forge's step refused writes no proposed event and keeps the task in landing, with no gh on PATH named as such and a forge's error said; the next proposal is the one event"
else
  fail "a proposal the forge refused: $no_gh / $down / $unproposed / $unopened"
fi
# The forge's head moved after the proposal, then the pull request was closed: land merges neither.
tip=$(git -C "$GHS/.lem/worktrees/pr-guards" rev-parse HEAD)
pushed=$(git -C "$GHO" -c user.name=t -c user.email=t@t commit-tree -p "$tip" -m "fix: pushed by someone else" "$tip^{tree}")
git -C "$GHO" update-ref refs/heads/fix/pr-guards "$pushed"
moved_head=$(gh_land land pr-guards --by agent 2>&1 || true)
git -C "$GHO" update-ref refs/heads/fix/pr-guards "$tip"
gh_set "d['prs']['$number']['state'] = 'CLOSED'"
closed_land=$(gh_land land pr-guards --by agent 2>&1 || true)
if grep -qF "the pull request's head is not the tip that was proposed; run \`land.py start\`, \`land.py base\`, \`land.py gate\` and \`land.py propose\` again" <<<"$moved_head" \
  && grep -qF "the pull request was closed without a merge: \`land.py merged pr-guards\` writes the task dropped" <<<"$closed_land" \
  && [ "$(gh_state "sum(c[:3] == ['pr', 'merge', '$number'] for c in d['calls'])")" = 0 ] && [ "$(status_in "$GHS" pr-guards)" = open ]; then
  pass "land merges no pull request whose head on the forge is not the proposed tip, nor a closed one, and names the step for a closed one"
else
  fail "a moved head and a closed pull request: $moved_head / $closed_land"
fi
# A pull request the owner closed on the forge ends its task as dropped, with nothing to clean by hand: the worktree goes, and the branch keeps its commits.
closed_merged=$(gh_land merged pr-guards 2>&1 || true)
closed_clean=$(gh_land clean pr-guards 2>&1 || true)
if [ "$(field '(d["closed"], d["state"], d["pull_request"]["number"])' <<<"$closed_merged" 2>&1)" = "(True, 'dropped', $number)" ] && [ "$(status_in "$GHS" pr-guards)" = dropped ] \
  && grep -qF "the pull request was closed on the forge" "$GHS/.lem/state/tasks/pr-guards/state.md" \
  && [ "$(field '(d["worktree"], d["branch"])' <<<"$closed_clean" 2>&1)" = "(True, None)" ] && grep -qF "fix/pr-guards holds the dropped task's commits" <<<"$closed_clean" \
  && git -C "$GHS" rev-parse -q --verify fix/pr-guards >/dev/null && [ ! -e "$GHS/.lem/worktrees/pr-guards" ]; then
  pass "a pull request closed on the forge with no merge ends its task: merged writes it dropped with the line that says so, and clean removes the worktree and keeps the branch with its commits"
else
  fail "a closed pull request: $closed_merged / $closed_clean / $(status_in "$GHS" pr-guards)"
fi

# A GitHub remote, and a developer who wants no pull requests (`branch.propose = "merge"`): the task
# lands on the remote's base branch as a ready branch does, so the next task starts from it, and the
# forge is never asked. The stand-in `gh` here only writes down that it was called.
GMO=$WORK/gm-origin.git
GMS=$WORK/gm-shop
git init -q --bare -b main "$GMO"
git clone -q "$GMO" "$GMS" 2>/dev/null && ident "$GMS"
git -C "$GMS" config remote.origin.url git@github.com:acme/solo.git
git -C "$GMS" config "url.$GMO.insteadOf" git@github.com:acme/solo.git
project --repo "$GMS" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' 'propose = "merge"' '[gate]' 'commands = ["true"]' > "$GMS/.lem/project.toml"
git -C "$GMS" add -A && git -C "$GMS" commit -q -m "chore: start" && git -C "$GMS" push -q origin main
mkdir -p "$WORK/gm-bin"
printf '%s\n' '#!/bin/sh' "echo \"\$*\" >> '$WORK/gm-gh-calls'" 'exit 1' > "$WORK/gm-bin/gh" && chmod +x "$WORK/gm-bin/gh"
gm_land() { PATH="$WORK/gm-bin:$PATH" "$PY" -B "$LAND" --repo "$GMS" "$@"; }
small_task_in "$GMS" solo-change s.txt eleven
out=$(gm_land start solo-change)
gm_land base solo-change >/dev/null && gm_land gate solo-change >/dev/null && gm_land read solo-change --record "$(clean 1)" >/dev/null
proposed=$(gm_land propose solo-change --title "fix: eleven" --notes "$NOTES" 2>&1 || true)
tip=$(git -C "$GMS/.lem/worktrees/solo-change" rev-parse HEAD)
opened=$(cat "$GMS/.lem/state/tasks/solo-change/state.md")
pushed_branch=$(git -C "$GMO" branch --list fix/solo-change)
merged=$(gm_land merged solo-change 2>&1 || true)
landed=$(gm_land land solo-change --by agent 2>&1 || true)
cleaned=$(gm_land clean solo-change 2>&1 || true)
if [ "$(field 'd["forge"]' <<<"$out")" = None ] && [ "$(field '(d["pull_request"], d["green"])' <<<"$proposed")" = "(None, True)" ] \
  && head -1 "$GMS/.lem/state/tasks/solo-change/pr.md" | grep -q '^\*\*Green\.\*\*' && grep -q "ready to land on main at ${tip:0:9}" <<<"$opened" && [ -z "$pushed_branch" ] \
  && grep -qF 'branch.propose is "merge"' <<<"$merged" && grep -qF "land.py land solo-change" <<<"$merged" \
  && [ "$(field '(d["tip"], d["pushed"], d["left_behind"])' <<<"$landed")" = "('$tip', True, None)" ] && [ "$(git -C "$GMO" rev-parse main)" = "$tip" ] \
  && [ "$(git -C "$GMS" rev-parse main)" = "$tip" ] && [ "$(status_in "$GMS" solo-change)" = landed ] \
  && [ "$(field '(d["worktree"], d["branch"], d["remote"])' <<<"$cleaned")" = "(True, 'fix/solo-change', None)" ] && [ -z "$(git -C "$GMS" branch --list fix/solo-change)" ] \
  && [ ! -e "$WORK/gm-gh-calls" ]; then
  pass "with a GitHub remote and branch.propose = merge, no pull request is opened and no task branch is pushed; the branch lands on origin's base branch, merged is refused with the step that lands, and clean removes the worktree and the branch, with no call of gh"
else
  fail "a GitHub remote with no pull requests: $out / $proposed / $opened / $merged / $landed / $cleaned / $(cat "$WORK/gm-gh-calls" 2>/dev/null)"
fi

# A pull request the scripts before the state moved opened, with their state in .git/lem, and the owner then
# merged on the forge, as three tasks of one scratch repository stand: the scripts of now move the state on
# their first call, and merged, tasks and clean take the task to its end.
if git cat-file -e "ccba3bd^{commit}" 2>/dev/null; then
  OLDLEM=$WORK/old-lem
  mkdir -p "$OLDLEM" && git archive ccba3bd skills | tar -x -C "$OLDLEM"
  GXO=$WORK/gx-origin.git
  GXS=$WORK/gx-shop
  git init -q --bare -b main "$GXO"
  git clone -q "$GXO" "$GXS" 2>/dev/null && ident "$GXS"
  git -C "$GXS" config remote.origin.url https://github.com/acme/shop.git
  git -C "$GXS" config "url.$GXO.insteadOf" https://github.com/acme/shop.git
  "$PY" -B "$OLDLEM/skills/lem/scripts/project.py" --repo "$GXS" init --base main >/dev/null
  printf '%s\n' '[branch]' 'base = "main"' 'land = "owner"' '[gate]' 'commands = ["true"]' > "$GXS/.lem/project.toml"
  git -C "$GXS" add -A && git -C "$GXS" commit -q -m "chore: start" && git -C "$GXS" push -q origin main
  (
    PROJECT=$OLDLEM/skills/lem/scripts/project.py STORIES=$OLDLEM/skills/lem/scripts/stories.py
    # the small change as the scripts of that commit wrote it: `Kind: correction` and --correction
    directory=$(project --repo "$GXS" task-dir old-pr --ask "Put twelve into o.txt.")
    printf '%s\n' '## Stories' '' 'Kind: correction, because the request is one sentence.' '' '1. The file holds the word the owner asked for.' > "$directory/stories.md"
    "$PY" -B "$STORIES" --repo "$GXS" approve old-pr --file "$directory/stories.md" --correction >/dev/null
    printf '%s\n' "   - test: \`sh tests/old-pr.sh\` in \`tests/old-pr.sh\`" >> "$directory/stories.md"
    tree=$(project --repo "$GXS" worktree-dir old-pr)
    git -C "$GXS" worktree add -q "$tree" -b fix/old-pr main
    mkdir -p "$tree/tests" && printf '%s\n' twelve > "$tree/o.txt" && echo "grep -qx twelve o.txt" > "$tree/tests/old-pr.sh"
    git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: old-pr"
    project --repo "$tree" state old-pr ready "the small change is built" >/dev/null
    ox() { PATH="$WORK/bin:$PATH" GH_STATE="$WORK/gx.json" GH_ORIGIN="$GXO" "$PY" -B "$OLDLEM/skills/lem/scripts/land.py" --repo "$GXS" "$@"; }
    ox start old-pr >/dev/null && ox base old-pr >/dev/null && ox gate old-pr >/dev/null && ox read old-pr --record "$(clean 1)" >/dev/null
    ox propose old-pr --title "fix: twelve" --notes "$NOTES" >/dev/null
  )
  opened=$("$PY" -B "$OLDLEM/skills/lem/scripts/project.py" --repo "$GXS" tasks | field '[(t["slug"], t["status"]) for t in d]')
  number=$("$PY" -c 'import json, sys; print(next(iter(json.load(open(sys.argv[1]))["prs"])))' "$WORK/gx.json")
  head=$(git -C "$GXO" rev-parse refs/heads/fix/old-pr)
  git -C "$GXO" update-ref refs/heads/main "$head"
  "$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])); d["prs"][sys.argv[2]].update(state="MERGED", merge=sys.argv[3]); json.dump(d, open(sys.argv[1], "w"))' "$WORK/gx.json" "$number" "$head"
  gx_land() { PATH="$WORK/bin:$PATH" GH_STATE="$WORK/gx.json" GH_ORIGIN="$GXO" "$PY" -B "$LAND" --repo "$GXS" "$@"; }
  merged=$(gx_land merged old-pr 2>"$WORK/gx.err" | field 'd["merged"]' 2>&1 || true)
  cleaned=$(gx_land clean old-pr 2>&1 | field 'd["worktree"]' 2>&1 || true)
  if [ "$opened" = "[('old-pr', 'open')]" ] && grep -qF "project.py: moved Lem's state from $GXS/.git/lem to $GXS/.lem/state (renamed)" "$WORK/gx.err" \
    && [ "$merged" = "$head" ] && [ "$(status_in "$GXS" old-pr)" = landed ] && [ "$cleaned" = True ] && [ ! -e "$GXS/.git/lem" ] \
    && [ "$(git -C "$GXS" rev-parse main)" = "$head" ] && [ -z "$(git -C "$GXS" status --porcelain --untracked-files=all)" ]; then
    pass "a pull request opened by the scripts before the state moved and merged by the owner on the forge is finished by merged of now, which moves the state and says so; tasks and clean read it there"
  else
    fail "an old pull request after the move: $opened / $merged / $cleaned / $(cat "$WORK/gx.err")"
  fi
else
  printf 'SKIP a pull request opened before the state moved: this clone does not have commit ccba3bd\n'
fi

finish
