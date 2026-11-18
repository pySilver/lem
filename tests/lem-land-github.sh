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
printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' 'land = "agent"' '[checks]' 'commands = ["true"]' > "$GHS/.lem/project.toml"
git -C "$GHS" add -A && git -C "$GHS" commit -q -m "chore: start" && git -C "$GHS" push -q origin main
mkdir -p "$WORK/bin"
cat > "$WORK/gh.py" <<'PY'
import json, os, subprocess, sys
state_file, origin = os.environ["GH_STATE"], os.environ["GH_ORIGIN"]
state = json.load(open(state_file)) if os.path.exists(state_file) else {"prs": {}, "calls": []}
args = sys.argv[1:]
# every call, one JSON line each, in a log of its own: a call that only reads writes no state, so that a
# test that changes a pull request while a watch reads them is never undone by a write of the stand-in
with open(state_file + ".log", "a") as log:
    log.write(json.dumps(args) + "\n")
def opt(name): return args[args.index(name) + 1] if name in args else None
def rev(ref): return subprocess.run(["git", "-C", origin, "rev-parse", "--verify", "-q", ref], capture_output=True, text=True).stdout.strip()
def shown(n, pr): return {"number": int(n), "url": pr["url"], "state": pr["state"], "mergeable": pr.get("mergeable", "MERGEABLE"),
                          "headRefOid": rev("refs/heads/" + pr["head"]), "mergeCommit": {"oid": pr["merge"]} if pr["merge"] else None}
def save():
    state["calls"].append(args)
    with open(state_file + ".new", "w") as out:
        json.dump(state, out)
    os.replace(state_file + ".new", state_file)
out = ""
if args[:2] == ["auth", "status"]:
    if os.environ.get("GH_SIGNED_OUT"):
        sys.exit("You are not logged into any GitHub hosts. To log in, run: gh auth login")
elif args[:2] == ["pr", "list"] and "--head" in args:
    out = json.dumps([{"number": int(n), "url": pr["url"], "headRefOid": rev("refs/heads/" + pr["head"]), "author": {"login": pr.get("author", "lem-owner")}}
                      for n, pr in state["prs"].items() if pr["head"] == opt("--head") and pr["state"] == "OPEN"])
elif args[:2] == ["pr", "list"]:
    # the base branch's pull requests, the newest first, as many as --limit says
    found = [shown(n, pr) for n, pr in sorted(state["prs"].items(), key=lambda item: -int(item[0]))
             if pr["base"] == opt("--base") and (opt("--state") == "all" or pr["state"] == "OPEN")]
    out = json.dumps(found[:int(opt("--limit") or 30)])
elif args[:2] == ["pr", "create"]:
    n = str(7 + len(state["prs"]))
    state["prs"][n] = {"url": "https://github.com/acme/shop/pull/" + n, "head": opt("--head"), "base": opt("--base"), "title": opt("--title"),
                       "body": open(opt("--body-file")).read(), "state": "OPEN", "merge": None}
    out = state["prs"][n]["url"]
    save()
elif args[:2] == ["pr", "edit"]:
    state["prs"][args[2]].update(title=opt("--title"), body=open(opt("--body-file")).read())
    save()
elif args[:2] == ["pr", "view"]:
    out = json.dumps(shown(args[2], state["prs"][args[2]]))
elif args[:2] == ["pr", "merge"]:
    pr = state["prs"][args[2]]
    head = rev("refs/heads/" + pr["head"])
    if opt("--match-head-commit") != head:
        sys.exit("the head is another commit")
    subprocess.run(["git", "-C", origin, "update-ref", "refs/heads/" + pr["base"], head], check=True)
    pr.update(state="MERGED", merge=head)
    save()
else:
    sys.exit("gh stand-in: no such command: " + " ".join(args))
print(out)
PY
printf '%s\n' '#!/bin/sh' "exec '$PY' -I '$WORK/gh.py' \"\$@\"" > "$WORK/bin/gh" && chmod +x "$WORK/bin/gh"
gh_land() { PATH="$WORK/bin:$PATH" GH_STATE="$WORK/gh.json" GH_ORIGIN="$GHO" "$PY" -B "$LAND" --repo "$GHS" "$@"; }
gh_state() { "$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])); print(eval(sys.argv[2], {"d": d}))' "$WORK/gh.json" "$1"; }
# gh_set PYTHON [FILE]: change the stand-in's pull requests as the forge would, written whole, since a watch may read them at that moment
gh_set() { "$PY" -c 'import json, os, sys; d = json.load(open(sys.argv[2])); exec(sys.argv[1]); json.dump(d, open(sys.argv[2] + ".set", "w")); os.replace(sys.argv[2] + ".set", sys.argv[2])' "$1" "${2:-$WORK/gh.json}"; }
gh_checked() { gh_land start "$1" >/dev/null && gh_land base "$1" >/dev/null && gh_land checks "$1" >/dev/null; }
small_task_in "$GHS" pr-change p.txt nine
out=$(gh_land start pr-change)
gh_land base pr-change >/dev/null && gh_land checks pr-change >/dev/null && gh_land read pr-change --record "$(clean 1)" >/dev/null
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
# with the record of the pull request lost, a merge does not go past the forge
main_before=$(git -C "$GHO" rev-parse main)
no_pr=$(gh_land land pr-change --by owner 2>&1 || true)
main_after=$(git -C "$GHO" rev-parse main)
gh_checked pr-change && gh_land propose pr-change --title "fix: nine, a third time" --notes "$NOTES" >/dev/null
if [ "$(gh_state '(len(d["prs"]), d["prs"]["7"]["title"], sum(c[:2] == ["pr", "create"] for c in d["calls"]), sum(c[:2] == ["pr", "edit"] for c in d["calls"]))')" = "(1, 'fix: nine, a third time', 1, 2)" ] \
  && [ "$(kept_in "$GHS" pr-change pr)" = "{'number': 7, 'url': 'https://github.com/acme/shop/pull/7'}" ] \
  && [ "$again" = "{'number': 7, 'url': 'https://github.com/acme/shop/pull/7'}/None" ] \
  && grep -qF "the project lands through pull requests and pr-change has none on record" <<<"$no_pr" && [ "$main_after" = "$main_before" ]; then
  pass "a task whose landing starts over starts its reviews over and keeps its pull request; a second proposal changes the one that is there, also when the record of it was lost: the forge is asked, and no second one is opened; a merge with no pull request on record is refused, and nothing reaches the base past the forge"
else
  fail "a second proposal: $no_pr / $(cat "$WORK/gh.json")"
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
if grep -q "origin/main moved after the checks ran, by files (late.txt)" <<<"$err" && grep -q "the pull request is not merged yet" <<<"$early" \
  && [ "$(gh_state 'sum(c[:3] == ["pr", "merge", "8"] for c in d["calls"])')" = 0 ] \
  && [ "$(field '(d["merged"], d["left_behind"])' <<<"$out")" = "('$oid', None)" ] && [ "$(status_in "$GHS" pr-squashed)" = landed ] && [ "$(git -C "$GHS" rev-parse main)" = "$oid" ]; then
  pass "a pull request is not merged over a base that moved; one the owner merged on the forge as one commit is finished by its own step, also while the task has the landing line again"
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
# The owner pressed "Update branch" on the forge, then merged as one commit: the head the forge merged holds the branch's
# tip and a merge of the base after it, which this checkout never fetched. clean says so, and the one command that removes
# the branch; it guesses nothing.
small_task_in "$GHS" pr-updated u.txt eleven
gh_checked pr-updated && gh_land read pr-updated --record "$(clean 1)" >/dev/null && gh_land propose pr-updated --title "fix: eleven" --notes "$NOTES" >/dev/null
updated_pr=$(gh_state 'next(n for n, pr in d["prs"].items() if pr["head"] == "fix/pr-updated")')
git -C "$gh_other" pull -q origin main
echo base-later > "$gh_other/base-later.txt" && git -C "$gh_other" add -A && git -C "$gh_other" commit -q -m "feat: base later" && git -C "$gh_other" push -q origin main
# "Update branch": the forge merges the base into the pull request's branch, on the forge only
local_tip=$(git -C "$GHS/.lem/worktrees/pr-updated" rev-parse HEAD)
update=$(git -C "$GHO" -c user.name=t -c user.email=t@t commit-tree -p "$local_tip" -p "$(git -C "$GHO" rev-parse main)" -m "Merge branch 'main' into fix/pr-updated" "$(git -C "$gh_other" rev-parse 'HEAD^{tree}')")
git -C "$GHO" update-ref refs/heads/fix/pr-updated "$update"
git -C "$gh_other" fetch -q origin && git -C "$gh_other" merge -q --squash origin/fix/pr-updated && git -C "$gh_other" commit -q -m "fix: eleven (#$updated_pr)" && git -C "$gh_other" push -q origin main
squashed=$(git -C "$gh_other" rev-parse HEAD)
gh_set "d['prs']['$updated_pr'].update(state='MERGED', merge='$squashed')"
gh_land merged pr-updated >/dev/null
updated_clean=$(gh_land clean pr-updated 2>&1 || true)
# shellcheck disable=SC2016  # the backticks are the message's own
if grep -qF "the forge merged ${update:0:9}, which is not the tip of fix/pr-updated and which this checkout does not hold: a commit made on the forge after the tip, as its \"Update branch\" makes" <<<"$updated_clean" \
  && ! grep -qF "the branch has commits after it" <<<"$updated_clean" \
  && grep -qF '`git branch -D fix/pr-updated` removes it' <<<"$updated_clean" && [ -n "$(git -C "$GHS" branch --list fix/pr-updated)" ]; then
  pass "after an Update branch on the forge and a merge as one commit, clean says that the forge merged a commit made on the forge after the branch's tip, not that the branch has commits after it, keeps the branch, and names the one command that removes it"
else
  fail "clean after an Update branch on the forge: $updated_clean"
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
if grep -qF "the pull request's head is not the tip that was proposed; run \`lem land start\`, \`lem land base\`, \`lem land checks\` and \`lem land propose\` again" <<<"$moved_head" \
  && grep -qF "the pull request was closed without a merge: \`lem land merged pr-guards\` writes the task dropped" <<<"$closed_land" \
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
# A teammate's commit on a task's branch (a "Commit suggestion" on the forge) is never removed by a push of Lem's, also
# after a plain fetch moved the remote-tracking branch to it: base refuses before its rebase and names the commit. Once
# the worktree holds it, it is part of the change, with the checks and a read, and the push keeps it.
small_task_in "$GHS" pr-mate t.txt thirteen
gh_checked pr-mate && gh_land read pr-mate --record "$(clean 1)" >/dev/null
pr_mate=$(gh_land propose pr-mate --title "fix: thirteen" --notes "$NOTES" | field 'd["pull_request"]["number"]')
mate=$WORK/gh-mate
git clone -q "$GHO" "$mate" && git -C "$mate" config user.name "Ania Mate" && git -C "$mate" config user.email ania@example.com
git -C "$mate" switch -q fix/pr-mate && echo suggestion > "$mate/t2.txt" && git -C "$mate" add -A && git -C "$mate" commit -q -m "fix: a suggestion"
git -C "$mate" push -q origin fix/pr-mate
suggestion=$(git -C "$mate" rev-parse HEAD)
# an editor's fetch in the background: the remote-tracking branch now names the teammate's commit
git -C "$GHS" fetch -q origin
gh_land start pr-mate >/dev/null
kept_out=$(gh_land base pr-mate 2>&1 || true)
on_forge=$(git -C "$GHO" rev-parse refs/heads/fix/pr-mate)
tree=$GHS/.lem/worktrees/pr-mate
git -C "$tree" pull -q --rebase origin fix/pr-mate
gh_land base pr-mate >/dev/null && gh_land checks pr-mate >/dev/null
due_mate=$(gh_land read pr-mate | field '(d["due"], d["why"])')
gh_land read pr-mate --record "$(clean 2)" >/dev/null
again=$(gh_land propose pr-mate --title "fix: thirteen" --notes "$NOTES" 2>&1 || true)
if grep -qF "${suggestion:0:9} Ania Mate \"fix: a suggestion\"" <<<"$kept_out" && grep -qF "git -C $tree pull --rebase origin fix/pr-mate" <<<"$kept_out" \
  && [ "$on_forge" = "$suggestion" ] && [ "$due_mate" = "('review', 'nothing asks for more than one read: the diff and what each profile is for decide')" ] \
  && [ "$(field 'd["pull_request"]["number"]' <<<"$again" 2>&1)" = "$pr_mate" ] \
  && [ "$(git -C "$GHO" rev-parse refs/heads/fix/pr-mate)" = "$(git -C "$tree" rev-parse HEAD)" ] && git -C "$GHO" merge-base --is-ancestor "$suggestion" refs/heads/fix/pr-mate; then
  pass "a teammate's commit on the task's branch stops base before its rebase, also after a plain fetch, naming its commit, author and subject and the pull that takes it in; then it is part of the change: the checks and a read come again, and the push keeps it"
else
  fail "a teammate's commit on the task's branch: $kept_out / $on_forge / $due_mate / $again"
fi
# A first push onto a branch of the same name that a teammate pushed meanwhile is refused, and so is the adoption of an
# open pull request whose head is no commit Lem pushed for this task: the teammate's commits and pull request stay his.
small_task_in "$GHS" pr-first u.txt fourteen
gh_checked pr-first && gh_land read pr-first --record "$(clean 1)" >/dev/null
git -C "$mate" fetch -q origin && git -C "$mate" switch -q -c fix/pr-first origin/main
echo his > "$mate/u2.txt" && git -C "$mate" add -A && git -C "$mate" commit -q -m "feat: his own work" && git -C "$mate" push -q origin fix/pr-first
his=$(git -C "$mate" rev-parse HEAD)
first=$(gh_land propose pr-first --title "fix: fourteen" --notes "$NOTES" 2>&1 || true)
first_forge=$(git -C "$GHO" rev-parse refs/heads/fix/pr-first)
project --repo "$GHS" state pr-first dropped "the test is over" >/dev/null
small_task_in "$GHS" pr-foreign v.txt fifteen
gh_checked pr-foreign && gh_land read pr-foreign --record "$(clean 1)" >/dev/null
# his pull request from a branch of the same name, which holds nothing beyond main yet
git -C "$GHO" update-ref refs/heads/fix/pr-foreign "$(git -C "$GHO" rev-parse refs/heads/main)"
gh_set "d['prs']['99'] = {'url': 'https://github.com/acme/shop/pull/99', 'head': 'fix/pr-foreign', 'base': 'main', 'title': 'his title', 'body': 'his text', 'state': 'OPEN', 'merge': None, 'author': 'ania'}"
foreign=$(gh_land propose pr-foreign --title "fix: fifteen" --notes "$NOTES" 2>&1 || true)
if grep -qF "${his:0:9} Ania Mate \"feat: his own work\"" <<<"$first" && [ "$first_forge" = "$his" ] && [ "$(gh_state 'sum(p["head"] == "fix/pr-first" for p in d["prs"].values())')" = 0 ] \
  && grep -qF "pull request #99 by ania is open on fix/pr-foreign" <<<"$foreign" && [ "$(gh_state '(d["prs"]["99"]["title"], d["prs"]["99"]["body"])')" = "('his title', 'his text')" ] \
  && [ "$(git -C "$GHO" rev-parse refs/heads/fix/pr-foreign)" = "$(git -C "$GHO" rev-parse refs/heads/main)" ] && [ "$(status_in "$GHS" pr-foreign)" = landing ]; then
  pass "a first push onto a branch a teammate pushed meanwhile is refused with his commit named, and an open pull request on the task's branch name whose head Lem did not push is not taken: its number and author are named, and its title, text and branch stay his"
else
  fail "a teammate's branch and pull request of the same name: $first / $first_forge / $foreign"
fi
project --repo "$GHS" state pr-foreign dropped "the test is over" >/dev/null
# A slug whose branch is on the remote and is no task's here is refused at the task's opening, with its semantic type or the name given.
git -C "$GHO" update-ref refs/heads/feat/taken-name "$(git -C "$GHO" rev-parse refs/heads/main)"
git -C "$GHO" update-ref refs/heads/ania/mbz-12-export "$(git -C "$GHO" rev-parse refs/heads/main)"
taken=$(project --repo "$GHS" task-dir taken-name --ask "Take the name." 2>&1 || true)
named_branch=$(project --repo "$GHS" task-dir mbz-export --ask "The export." --branch ania/mbz-12-export 2>&1 || true)
free=$(project --repo "$GHS" task-dir free-name --ask "A free name." --branch feat/free-name 2>&1 || true)
if grep -qF "origin has the branch feat/taken-name" <<<"$taken" && grep -qF "add a word to the slug" <<<"$taken" && [ ! -e "$GHS/.lem/state/tasks/taken-name" ] \
  && grep -qF "origin has the branch ania/mbz-12-export" <<<"$named_branch" && [ ! -e "$GHS/.lem/state/tasks/mbz-export" ] && [ "$free" = "$GHS/.lem/state/tasks/free-name" ]; then
  pass "a task is not opened under a slug whose branch origin has already, by its semantic type or by the name --branch gives, and one whose branch is free opens"
else
  fail "a slug on the remote: $taken / $named_branch / $free"
fi
# A new task's worktree starts from origin's base branch after a fetch, never from the local base branch that may be days
# old, and with no upstream; a second call finds it; with no remote it starts from the local base branch.
git -C "$mate" fetch -q origin && git -C "$mate" switch -q main && git -C "$mate" merge -q --ff-only origin/main
echo newer > "$mate/newer.txt" && git -C "$mate" add -A && git -C "$mate" commit -q -m "feat: newer on origin" && git -C "$mate" push -q origin main
fresh=$(project --repo "$GHS" worktree free-name feat/free-name 2>&1 || true)
fresh_tree=$GHS/.lem/worktrees/free-name
second=$(project --repo "$GHS" worktree free-name feat/free-name 2>&1 || true)
upstream=$(status_of git -C "$fresh_tree" rev-parse --abbrev-ref '@{upstream}')
NR=$WORK/no-remote
git init -q -b main "$NR" && ident "$NR" && commit "$NR" "chore: start"
project --repo "$NR" init --base main >/dev/null && project --repo "$NR" task-dir local-one --ask "One." >/dev/null
local_tree=$(project --repo "$NR" worktree local-one fix/local-one 2>&1 || true)
# an origin that does not answer: the task starts from the local base branch, and one line on stderr says so
git -C "$GHS" config remote.origin.url "$WORK/no-such-origin.git"
project --repo "$GHS" task-dir quiet-origin --ask "Origin is away." >/dev/null 2>&1
away=$(project --repo "$GHS" worktree quiet-origin feat/quiet-origin 2>"$WORK/away.err" || true)
git -C "$GHS" config remote.origin.url https://github.com/acme/shop.git
if [ "$(field '(d["made"], d["from"], d["commit"])' <<<"$fresh" 2>&1)" = "(True, 'origin/main', '$(git -C "$mate" rev-parse HEAD)')" ] \
  && [ "$(git -C "$fresh_tree" rev-parse HEAD)" = "$(git -C "$mate" rev-parse HEAD)" ] && [ "$(git -C "$GHS" rev-parse main)" != "$(git -C "$mate" rev-parse HEAD)" ] \
  && [ "$upstream" != 0 ] && [ "$(field '(d["made"], d["worktree"])' <<<"$second" 2>&1)" = "(False, '$fresh_tree')" ] \
  && [ "$(field '(d["made"], d["from"], d["commit"])' <<<"$local_tree" 2>&1)" = "(True, 'main', '$(git -C "$NR" rev-parse main)')" ] \
  && [ "$(field '(d["made"], d["from"], d["commit"])' <<<"$away" 2>&1)" = "(True, 'main', '$(git -C "$GHS" rev-parse main)')" ] \
  && grep -qF "project.py: origin did not answer (" "$WORK/away.err" && grep -qF "so quiet-origin starts from the local main as it is now" "$WORK/away.err"; then
  pass "a new task's worktree starts from origin's base branch after a fetch, with no upstream, while the local base branch is older; a second call finds it; with no remote, or an origin that does not answer, it starts from the local base branch, and the second says so on stderr"
else
  fail "a new task's worktree: $fresh / $second / $upstream / $local_tree / $away / $(cat "$WORK/away.err")"
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
printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' 'land = "agent"' 'propose = "merge"' '[checks]' 'commands = ["true"]' > "$GMS/.lem/project.toml"
git -C "$GMS" add -A && git -C "$GMS" commit -q -m "chore: start" && git -C "$GMS" push -q origin main
mkdir -p "$WORK/gm-bin"
printf '%s\n' '#!/bin/sh' "echo \"\$*\" >> '$WORK/gm-gh-calls'" 'exit 1' > "$WORK/gm-bin/gh" && chmod +x "$WORK/gm-bin/gh"
gm_land() { PATH="$WORK/gm-bin:$PATH" "$PY" -B "$LAND" --repo "$GMS" "$@"; }
small_task_in "$GMS" solo-change s.txt eleven
out=$(gm_land start solo-change)
gm_land base solo-change >/dev/null && gm_land checks solo-change >/dev/null && gm_land read solo-change --record "$(clean 1)" >/dev/null
proposed=$(gm_land propose solo-change --title "fix: eleven" --notes "$NOTES" 2>&1 || true)
tip=$(git -C "$GMS/.lem/worktrees/solo-change" rev-parse HEAD)
opened=$(cat "$GMS/.lem/state/tasks/solo-change/state.md")
pushed_branch=$(git -C "$GMO" branch --list fix/solo-change)
merged=$(gm_land merged solo-change 2>&1 || true)
landed=$(gm_land land solo-change --by agent 2>&1 || true)
cleaned=$(gm_land clean solo-change 2>&1 || true)
if [ "$(field 'd["forge"]' <<<"$out")" = None ] && [ "$(field '(d["pull_request"], d["green"])' <<<"$proposed")" = "(None, True)" ] \
  && head -1 "$GMS/.lem/state/tasks/solo-change/pr.md" | grep -q '^\*\*Green\.\*\*' && grep -q "ready to land on main at ${tip:0:9}" <<<"$opened" && [ -z "$pushed_branch" ] \
  && grep -qF 'branch.propose is "merge"' <<<"$merged" && grep -qF "lem land land solo-change" <<<"$merged" \
  && [ "$(field '(d["tip"], d["pushed"], d["left_behind"])' <<<"$landed")" = "('$tip', True, None)" ] && [ "$(git -C "$GMO" rev-parse main)" = "$tip" ] \
  && [ "$(git -C "$GMS" rev-parse main)" = "$tip" ] && [ "$(status_in "$GMS" solo-change)" = landed ] \
  && [ "$(field '(d["worktree"], d["branch"], d["remote"])' <<<"$cleaned")" = "(True, 'fix/solo-change', None)" ] && [ -z "$(git -C "$GMS" branch --list fix/solo-change)" ] \
  && [ ! -e "$WORK/gm-gh-calls" ]; then
  pass "with a GitHub remote and branch.propose = merge, no pull request is opened and no task branch is pushed; the branch lands on origin's base branch, merged is refused with the step that lands, and clean removes the worktree and the branch, with no call of gh"
else
  fail "a GitHub remote with no pull requests: $out / $proposed / $opened / $merged / $landed / $cleaned / $(cat "$WORK/gm-gh-calls" 2>/dev/null)"
fi

# The watch of the open pull requests, which looks once a second here (`--every 1`; Lem's own call waits 60); the owner merges
# and closes on the forge, here by the stand-in's file, and the watch ends and names the task.
GWO=$WORK/gw-origin.git
GWS=$WORK/gw-shop
git init -q --bare -b main "$GWO"
git clone -q "$GWO" "$GWS" 2>/dev/null && ident "$GWS"
git -C "$GWS" config remote.origin.url https://github.com/acme/watch.git
git -C "$GWS" config "url.$GWO.insteadOf" https://github.com/acme/watch.git
project --repo "$GWS" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' '[checks]' 'commands = ["true"]' > "$GWS/.lem/project.toml"
printf 'l%s\n' 1 2 3 4 5 6 7 8 9 > "$GWS/shop.txt"
git -C "$GWS" add -A && git -C "$GWS" commit -q -m "chore: start" && git -C "$GWS" push -q origin main
GW=$WORK/gw.json
gw_land() { PATH="$WORK/bin:$PATH" GH_STATE="$GW" GH_ORIGIN="$GWO" "$PY" -B "$LAND" --repo "$GWS" "$@"; }
gw_state() { "$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])); print(eval(sys.argv[2], {"d": d}))' "$GW" "$1"; }
# gw_watch: the watch in the background, the command itself (exec), so that $! is its own process and a TERM reaches it;
# the function's subshell would take the TERM in its place and leave the watch running with no parent
gw_watch() { PATH="$WORK/bin:$PATH" GH_STATE="$GW" GH_ORIGIN="$GWO" exec "$PY" -B "$LAND" --repo "$GWS" watch --every 1; }
watched() { "$PY" -c 'import json, re, sys; print(eval(sys.argv[2], {"d": json.loads(re.fullmatch(r"lemWatch\((.*)\);\n", open(sys.argv[1]).read(), re.S).group(1))}))' "$GWS/.lem/state/watch.js" "$1" 2>/dev/null; }
# looked N: the watch this test started ($wpid), and no other, looked N times
looked() { [ "$(watched 'd.get("looks") or 0 if d.get("pid") == '"$wpid"' else 0')" -ge "$1" ] 2>/dev/null; }
# line_task SLUG small|full LINE TEXT: a task that writes TEXT on line LINE of shop.txt, with the test `grep -q TEXT shop.txt`, `ready`
line_task() {
  local tree directory
  directory=$(project --repo "$GWS" task-dir "$1" --ask "Put $4 on line $3 of shop.txt.")
  tree=$(project --repo "$GWS" worktree-dir "$1")
  git -C "$GWS" worktree add -q "$tree" -b "fix/$1" main
  if [ "$2" = small ]; then
    printf '%s\n' '## Acceptance criteria' '' 'Size: small, because the request is one sentence.' '' '1. The file holds the word the owner asked for.' > "$directory/criteria.md"
    "$PY" -B "$CRITERIA" --repo "$GWS" approve "$1" --file "$directory/criteria.md" --small >/dev/null
    printf '%s\n' "   - test: \`sh tests/$1.sh\` in \`tests/$1.sh\`" >> "$directory/criteria.md"
  else
    plan_in "$tree" "$1" "sh tests/$1.sh"
  fi
  mkdir -p "$tree/tests" && echo "grep -q $4 shop.txt" > "$tree/tests/$1.sh"
  "$PY" -I -c 'import sys; p, n, t = sys.argv[1], int(sys.argv[2]), sys.argv[3]; lines = open(p).read().splitlines(); lines[n - 1] = t; open(p, "w").write("\n".join(lines) + "\n")' "$tree/shop.txt" "$3" "$4"
  git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: $1"
  project --repo "$tree" state "$1" ready "the report is written" >/dev/null
  if [ "$2" = full ]; then read_in "$GWS" "$1"; fi
}
# proposed SLUG: its landing to the pull request, with a polish pass for a full change and one clean read
proposed() {
  gw_land start "$1" >/dev/null && gw_land base "$1" >/dev/null
  if [ -e "$GWS/docs/plans/20261115-$1.md" ] || [ -e "$GWS/.lem/worktrees/$1/docs/plans/20261115-$1.md" ]; then polish_in_gw "$1"; fi
  gw_land checks "$1" >/dev/null && gw_land read "$1" --record "$(clean 1)" >/dev/null && gw_land propose "$1" --title "fix: $1" --notes "$NOTES" >/dev/null
}
polish_in_gw() {
  local started
  started=$(gw_land polish "$1") || return 1
  if [ "$(field 'd["done"]' <<<"$started")" = False ]; then gw_land polish "$1" --done >/dev/null; fi
}
# forge_merge NUMBER [PYTHON]: the owner merges the pull request on the forge, a fast-forward of main there; PYTHON changes the others
forge_merge() {
  local head
  head=$(git -C "$GWO" rev-parse "refs/heads/$(gw_state "d['prs']['$1']['head']")")
  git -C "$GWO" update-ref refs/heads/main "$head"
  gh_set "d['prs']['$1'].update(state='MERGED', merge='$head'); ${2:-pass}" "$GW"
}

# What ends a watch at once, with what to do: nothing open, no gh, gh signed out, and a project with no pull requests.
none=$(gw_land watch 2>&1 || true)
none_code=$(status_of gw_land watch)
none_file=$(watched '(d["checked"], d["ended"] is not None, d["why"])')
line_task w-one small 1 one
line_task w-two full 9 nine
proposed w-one && proposed w-two
no_gh=$(PATH="$WORK/no-gh" GH_STATE="$GW" GH_ORIGIN="$GWO" "$PY" -B "$LAND" --repo "$GWS" watch 2>&1 || true)
signed_out=$(GH_SIGNED_OUT=1 gw_land watch 2>&1 || true)
merge_mode=$(PATH="$WORK/gm-bin:$PATH" "$PY" -B "$LAND" --repo "$GMS" watch 2>&1 || true)
if grep -qF "land.py: nothing to watch: no task is open with a pull request; Lem starts the watch after its next proposal" <<<"$none" && [ "$none_code" = 1 ] \
  && [ "$none_file" = "(None, True, 'nothing to watch: no task is open with a pull request; Lem starts the watch after its next proposal')" ] \
  && grep -qF "the \`gh\` command is not on PATH" <<<"$no_gh" && grep -qF "the \`gh\` command is not signed in to github.com (You are not logged into any GitHub hosts. To log in, run: gh auth login): \`gh auth login\` signs it in" <<<"$signed_out" \
  && grep -qF 'branch.propose is "merge" in .lem/project.toml: no task opens a pull request, so there is none to watch' <<<"$merge_mode" \
  && [ "$(gw_state '(sorted(d["prs"]), [p["head"] for p in d["prs"].values()])')" = "(['7', '8'], ['fix/w-one', 'fix/w-two'])" ]; then
  pass "a watch with nothing open, with no gh, with gh signed out or in a project that opens no pull requests ends at once with exit 1 and what to do, and the board's file says that it ended and why"
else
  fail "the ends of a watch: $none / $none_file / $no_gh / $signed_out / $merge_mode"
fi
# A watch that looks while nothing changed (each watch starts with no file of an earlier one, so that its own looks are waited for), one call of the forge for both pull requests at each look, and ends on a merge.
: > "$GW.log"
rm -f "$GWS/.lem/state/watch.js"
gw_watch > "$WORK/watch.out" 2> "$WORK/watch.err" &
wpid=$!
soon looked 3
alive=$(kill -0 "$wpid" 2>/dev/null && echo yes || echo no)
looks_before=$(watched 'd["looks"]')
calls_before=$("$PY" -c 'import json, sys; c = [json.loads(l) for l in open(sys.argv[1])]; print((sum(x[:2] == ["pr", "list"] for x in c), sum(x[:2] == ["pr", "view"] for x in c), sum(x[:2] == ["auth", "status"] for x in c)))' "$GW.log")
forge_merge 7
set +e; wait "$wpid"; wcode=$?; set -e
if [ "$alive" = yes ] && [ "$wcode" = 0 ] && [ "$calls_before" = "($looks_before, 0, 1)" ] \
  && [ "$(field '([(e["task"], e["pr"], e["what"]) for e in d["ended"]], [(e["task"], e["pr"], e["state"]) for e in d["open"]], d["every"], d["looks"] > 3)' < "$WORK/watch.out")" = "([('w-one', 7, 'merged')], [('w-two', 8, 'OPEN')], 1, True)" ] \
  && [ "$(watched '([e["task"] for e in d["open"]], d["ended"], d["every"])')" = "(['w-two'], None, 1)" ] && [ "$(status_in "$GWS" w-one)" = open ]; then
  pass "the watch looks at the forge once a second while nothing changes, with one call for every open task's pull request, writes each look for the board, and ends with exit 0 when the owner merged one, naming the task; it changes no task"
else
  fail "a watch to a merge: alive=$alive code=$wcode looks=$looks_before calls=$calls_before / $(cat "$WORK/watch.out" "$WORK/watch.err")"
fi
# After the merge the other open task waits as it is. The owner's word to land it meets the moved base, and the steps
# the refusal names bring it onto the new base: the same file in other lines, a rebase with no conflict, so the review
# stands; the checks run again, and the proposal keeps its pull request.
gw_land merged w-one >/dev/null
waited=$(status_in "$GWS" w-two)
refused=$(gw_land land w-two --by owner 2>&1 || true)
started=$(gw_land start w-two 2>&1 || true)
based=$(gw_land base w-two 2>&1 || true)
polished=$(gw_land polish w-two 2>&1 || true)
gw_land checks w-two >/dev/null 2>&1 || true
due_after=$(gw_land read w-two 2>&1 || true)
again=$(gw_land propose w-two --title "fix: w-two" --notes "$NOTES" 2>&1 || true)
tree=$GWS/.lem/worktrees/w-two
text=$GWS/.lem/state/tasks/w-two/pr.md
if [ "$(status_in "$GWS" w-one)" = landed ] && [ "$waited" = open ] && grep -qF "origin/main moved after the checks ran, by files (" <<<"$refused" \
  && [ "$(gw_state 'sum(c[:2] == ["pr", "merge"] for c in d["calls"])')" = 0 ] \
  && [ "$(field 'd["task"]' <<<"$started" 2>&1)" = w-two ] && grep -qF "the base moved: the checks run again" "$GWS/.lem/state/tasks/w-two/state.md" \
  && [ "$(field '(d["moved"], d["resolved"])' <<<"$based" 2>&1)" = "(True, None)" ] && [ "$(field 'd["done"]' <<<"$polished" 2>&1)" = True ] \
  && [ "$(field '(d["due"], d["why"])' <<<"$due_after" 2>&1)" = "('none', 'round 1 reviewed this change and left no must-fix')" ] \
  && [ "$(field '(d["pull_request"]["number"], d["green"], d["synced"])' <<<"$again" 2>&1)" = "(8, True, 'rebased on main; the checks passed again')" ] \
  && [ "$(status_in "$GWS" w-two)" = open ] && [ "$(git -C "$GWO" rev-parse refs/heads/fix/w-two)" = "$(git -C "$tree" rev-parse HEAD)" ] \
  && git -C "$tree" merge-base --is-ancestor "$(git -C "$GWO" rev-parse main)" HEAD \
  && [ "$(gw_state '(sum(c[:2] == ["pr", "create"] for c in d["calls"]), [c[2] for c in d["calls"] if c[:2] == ["pr", "edit"]], "Rebased on main; the checks passed again." in d["prs"]["8"]["body"])')" = "(2, ['8'], True)" ] \
  && sed -n 3p "$text" | grep -qxF "Rebased on main; the checks passed again." && grep -qxF "rebased on main; the checks passed again" "$GWS/.lem/state/tasks/w-two/state.md"; then
  pass "after a merge an open task with no conflict waits as it is; the owner's word to land it is refused on the moved base with the steps, and they bring it onto the new base: the polish pass and the review it had stand through a rebase with no conflict, the checks run again, and propose pushes it and keeps its pull request, whose text and state say what happened in one line"
else
  fail "an open task after a merge: $waited / $refused / $started / $based / $polished / $due_after / $again"
fi
# A conflict: the owner merges #9, which changed the line #10 changes too. The watch names #10 as conflicting, base stops,
# a builder (here the test) rebases and keeps both, and the resolution gets one read of its own.
line_task w-three small 5 three
line_task w-four full 5 four
proposed w-three && proposed w-four
rm -f "$GWS/.lem/state/watch.js"
gw_watch > "$WORK/watch.out" 2>&1 &
wpid=$!
soon looked 1
forge_merge 9 "d['prs']['10']['mergeable'] = 'CONFLICTING'"
set +e; wait "$wpid"; wcode=$?; set -e
conflicted=$(field '([(e["task"], e["what"]) for e in d["ended"]], [(e["task"], e["mergeable"]) for e in d["open"]])' < "$WORK/watch.out" 2>&1)
gw_land merged w-three >/dev/null
gw_land start w-four --conflicting >/dev/null
stopped=$(gw_land base w-four 2>/dev/null || true)
tree=$GWS/.lem/worktrees/w-four
git -C "$tree" rebase -q origin/main >/dev/null 2>&1 || true
"$PY" -I -c 'import sys; p = sys.argv[1]; lines = [l for l in open(p).read().splitlines() if not l.startswith(("<<<<<<<", "=======", ">>>>>>>", "three", "four"))]; lines.insert(4, "three four"); open(p, "w").write("\n".join(lines) + "\n")' "$tree/shop.txt"
git -C "$tree" add shop.txt && GIT_EDITOR=true git -C "$tree" rebase --continue >/dev/null 2>&1
resolved=$(gw_land base w-four 2>&1 || true)
polished=$(gw_land polish w-four 2>&1 || true)
gw_land checks w-four >/dev/null 2>&1 || true
due_read=$(gw_land read w-four 2>&1 || true)
recorded=$(gw_land read w-four --record "$(clean 2)" 2>&1 || true)
due_after=$(gw_land read w-four 2>&1 || true)
again=$(gw_land propose w-four --title "fix: w-four" --notes "$NOTES" 2>&1 || true)
text=$GWS/.lem/state/tasks/w-four/pr.md
# the forge works out again that the pushed head merges with no conflict
gh_set "d['prs']['10']['mergeable'] = 'MERGEABLE'" "$GW"
if [ "$wcode" = 0 ] && [ "$conflicted" = "([('w-three', 'merged')], [('w-four', 'CONFLICTING'), ('w-two', 'MERGEABLE')])" ] \
  && [ "$(field 'd["conflict"]' <<<"$stopped" 2>&1)" = "['shop.txt']" ] && [ "$(field '(d["resolved"], d["moved"])' <<<"$resolved" 2>&1)" = "(['shop.txt'], False)" ] \
  && [ "$(field 'd["done"]' <<<"$polished" 2>&1)" = True ] \
  && [ "$(field '(d["due"], d["floor"], d["round"], d["resolution"]["files"], d["resolution"]["range_diff"].startswith("git range-diff "))' <<<"$due_read" 2>&1)" = "('review', 'read', 1, ['shop.txt'], True)" ] \
  && grep -qF "a builder resolved a conflict with the base in shop.txt: one read of what the resolution changed" <<<"$due_read" \
  && [ "$(field '(d["recorded"]["of"], d["recorded"]["round"], d["next"])' <<<"$recorded" 2>&1)" = "('resolution', 1, 'none')" ] && [ "$(field 'd["due"]' <<<"$due_after" 2>&1)" = none ] \
  && [ "$(field '(d["pull_request"]["number"], d["green"], d["synced"])' <<<"$again" 2>&1)" = "(10, True, 'rebased on main after the forge called it conflicting; one conflict in shop.txt, resolved by a builder; the checks passed again')" ] \
  && grep -qxF -- "- the read of the conflict's resolution (one read; answered: codex): clean, 0 must-fix, 0 should, 0 nit" "$text" \
  && grep -qxF "Rebased on main after the forge called it conflicting; one conflict in shop.txt, resolved by a builder; the checks passed again." "$text" \
  && [ "$(git -C "$GWO" rev-parse refs/heads/fix/w-four)" = "$(git -C "$tree" rev-parse HEAD)" ] && [ "$(status_in "$GWS" w-four)" = open ]; then
  pass "a conflict after a merge: the watch names the conflicting pull request first, base stops on its files, and after a builder's resolution base keeps the polish pass by its new names; the resolution gets one read that is no round, and propose keeps the pull request, whose text says that a builder resolved the conflict"
else
  fail "a conflict after a merge: code=$wcode $conflicted / $stopped / $resolved / $polished / $due_read / $recorded / $due_after / $again"
fi
# A pull request the owner closed with no merge ends the watch too, and names what happened.
line_task w-five small 2 five
proposed w-five
rm -f "$GWS/.lem/state/watch.js"
gw_watch > "$WORK/watch.out" 2>&1 &
wpid=$!
soon looked 1
gh_set "d['prs']['11']['state'] = 'CLOSED'" "$GW"
set +e; wait "$wpid"; wcode=$?; set -e
closed=$(field '[(e["task"], e["pr"], e["what"]) for e in d["ended"]]' < "$WORK/watch.out" 2>&1)
dropped=$(gw_land merged w-five 2>&1 || true)
if [ "$wcode" = 0 ] && [ "$closed" = "[('w-five', 11, 'closed')]" ] && [ "$(field '(d["closed"], d["state"])' <<<"$dropped" 2>&1)" = "(True, 'dropped')" ] && [ "$(status_in "$GWS" w-five)" = dropped ]; then
  pass "the watch ends when the owner closed a pull request with no merge, and names it as closed; merged then writes the task dropped"
else
  fail "a watch to a close: code=$wcode $closed / $dropped / $(cat "$WORK/watch.out")"
fi
# A commit on the base that is no task's merge (here a push of the owner's) makes an open pull request conflicting:
# the watch ends and names it, once for one head; a watch started again while it waits does not end for it again,
# and a watch with no look before ends at its first look. start --conflicting brings it onto the base, and the
# pull request's text says why in one line.
line_task w-six small 3 six
proposed w-six
rm -f "$GWS/.lem/state/watch.js"
gw_watch > "$WORK/watch.out" 2>&1 &
wpid=$!
soon looked 1
pusher=$WORK/gw-pusher
git clone -q "$GWO" "$pusher" && ident "$pusher"
"$PY" -I -c 'import sys; p = sys.argv[1]; lines = open(p).read().splitlines(); lines[2] = "the owner"; open(p, "w").write("\n".join(lines) + "\n")' "$pusher/shop.txt"
git -C "$pusher" commit -q -am "docs: the owner's own line" && git -C "$pusher" push -q origin main
gh_set "d['prs']['12']['mergeable'] = 'CONFLICTING'" "$GW"
set +e; wait "$wpid"; wcode=$?; set -e
newly=$(field '(d["ended"], [(e["task"], e["pr"], e["why"]) for e in d["conflicting"]], [e["task"] for e in d["open"]][0])' < "$WORK/watch.out" 2>&1)
gw_watch > "$WORK/watch-again.out" 2>&1 &
wpid=$!
soon looked 2
again_alive=$(kill -0 "$wpid" 2>/dev/null && echo yes || echo no)
kill -TERM "$wpid" 2>/dev/null || true
set +e; wait "$wpid" 2>/dev/null; set -e
rm -f "$GWS/.lem/state/watch.js"
first=$(gw_land watch 2>&1 | field '[(e["task"], e["why"]) for e in d["conflicting"]]' 2>&1 || true)
gw_land start w-six --conflicting >/dev/null
stopped=$(gw_land base w-six 2>/dev/null || true)
tree=$GWS/.lem/worktrees/w-six
git -C "$tree" rebase -q origin/main >/dev/null 2>&1 || true
"$PY" -I -c 'import sys; p = sys.argv[1]; lines = [l for l in open(p).read().splitlines() if not l.startswith(("<<<<<<<", "=======", ">>>>>>>", "six", "the owner"))]; lines.insert(2, "the owner six"); open(p, "w").write("\n".join(lines) + "\n")' "$tree/shop.txt"
git -C "$tree" add shop.txt && GIT_EDITOR=true git -C "$tree" rebase --continue >/dev/null 2>&1
gw_land base w-six >/dev/null 2>&1 || true
gw_land checks w-six >/dev/null 2>&1 || true
gw_land read w-six --record "$(clean 2)" >/dev/null 2>&1 || true
synced=$(gw_land propose w-six --title "fix: w-six" --notes "$NOTES" 2>&1 | field '(d["pull_request"]["number"], d["synced"])' 2>&1 || true)
gh_set "d['prs']['12']['mergeable'] = 'MERGEABLE'" "$GW"
why12="the forge calls pull request #12 conflicting with main"
if [ "$wcode" = 0 ] && [ "$newly" = "([], [('w-six', 12, '$why12, and it did not at the look before: a commit on the base met its change')], 'w-six')" ] \
  && [ "$again_alive" = yes ] && [ "$first" = "[('w-six', '$why12, at the first look of the watch: a commit on the base met its change')]" ] \
  && grep -qF "the forge calls the pull request conflicting with main: the branch is brought onto it again" "$GWS/.lem/state/tasks/w-six/state.md" \
  && [ "$(field 'd["conflict"]' <<<"$stopped" 2>&1)" = "['shop.txt']" ] \
  && [ "$synced" = "(12, 'rebased on main after the forge called it conflicting; one conflict in shop.txt, resolved by a builder; the checks passed again')" ] \
  && grep -qxF "Rebased on main after the forge called it conflicting; one conflict in shop.txt, resolved by a builder; the checks passed again." "$GWS/.lem/state/tasks/w-six/pr.md"; then
  pass "a pull request a commit on the base made conflicting ends the watch, which names it and why, once for one head: a watch started again does not end for it, one with no look before ends at its first look; start --conflicting brings it onto the base, and its text says why"
else
  fail "a pull request that became conflicting: code=$wcode $newly / $again_alive / $first / $stopped / $synced"
fi

# The status asks merged for each open task: a pull request still open is "not merged yet", and merged keeps what the
# forge says of a conflict on the pushed head, so the list of what waits says it beside green without the watch.
line_task w-seven small 8 seven
proposed w-seven
seven=$(gw_state 'next(n for n, p in d["prs"].items() if p["head"] == "fix/w-seven")')
conflict_seven() { project --repo "$GWS" waiting | field 'next((t["green"], t["conflict"]) for t in d["pull_requests"] if t["task"] == "w-seven")'; }
unasked=$(conflict_seven)
clear_said=$(gw_land merged w-seven 2>&1 || true)
clear=$(conflict_seven)
gh_set "d['prs']['$seven']['mergeable'] = 'CONFLICTING'" "$GW"
conflict_said=$(gw_land merged w-seven 2>&1 || true)
conflicting=$(conflict_seven)
# somebody pushed to the branch on the forge: what the forge says is of a head Lem did not push, and says nothing of it
pushed_seven=$(git -C "$GWO" rev-parse refs/heads/fix/w-seven)
git -C "$GWO" update-ref refs/heads/fix/w-seven "$(git -C "$GWO" -c user.name=t -c user.email=t@t commit-tree -p "$pushed_seven" -m "fix: pushed by someone else" "$pushed_seven^{tree}")"
gw_land merged w-seven >/dev/null 2>&1 || true
moved=$(conflict_seven)
git -C "$GWO" update-ref refs/heads/fix/w-seven "$pushed_seven"
gh_set "d['prs']['$seven']['mergeable'] = 'MERGEABLE'" "$GW"
project --repo "$GWS" state w-seven dropped "the test is over" >/dev/null
if [ "$unasked" = "(True, None)" ] && [ "$clear_said" = "land.py: the pull request is not merged yet" ] && [ "$clear" = "(True, False)" ] \
  && [ "$conflict_said" = "land.py: the pull request is not merged yet, and the forge calls it conflicting with main" ] && [ "$conflicting" = "(True, True)" ] \
  && [ "$moved" = "(True, None)" ]; then
  pass "merged on a pull request that is still open keeps what the forge says of a conflict on the pushed head, and waiting gives conflict beside green: null before any look and when the head moved, false, then true"
else
  fail "a conflict in the list of what waits: $unasked / $clear_said / $clear / $conflict_said / $conflicting / $moved"
fi

# A careful change keeps its review through a rebase with no conflict, onto a base that left its files alone and onto
# one that changed one of them in other lines.
line_task w-care small 7 care
printf '%s\n' 'slug: w-care' 'careful: the owner says so' > "$GWS/.lem/state/tasks/w-care/brief.md"
full_read='{"kind": "full", "ran": [{"name": "default", "why": "the owner calls it careful"}], "answered": ["codex"]}'
gw_land start w-care >/dev/null && gw_land base w-care >/dev/null && gw_land checks w-care >/dev/null
gw_land read w-care --record "$(record 1 "$full_read")" >/dev/null && gw_land propose w-care --title "fix: w-care" --notes "$MIG" >/dev/null
git -C "$pusher" fetch -q origin && git -C "$pusher" merge -q --ff-only origin/main
echo other > "$pusher/other.txt" && git -C "$pusher" add -A && git -C "$pusher" commit -q -m "docs: another file" && git -C "$pusher" push -q origin main
gw_land start w-care >/dev/null && gw_land base w-care >/dev/null && gw_land checks w-care >/dev/null
care_alone=$(gw_land read w-care | field 'd["due"]' 2>&1 || true)
"$PY" -I -c 'import sys; p = sys.argv[1]; lines = open(p).read().splitlines(); lines[0] = lines[0] + " first"; open(p, "w").write("\n".join(lines) + "\n")' "$pusher/shop.txt"
git -C "$pusher" commit -q -am "fix: the first line" && git -C "$pusher" push -q origin main
gw_land start w-care >/dev/null && gw_land base w-care >/dev/null && gw_land checks w-care >/dev/null
care_meet=$(gw_land read w-care | field '(d["due"], d["why"])' 2>&1 || true)
gw_land propose w-care --title "fix: w-care" --notes "$MIG" >/dev/null 2>&1 || true
if [ "$care_alone" = none ] && [ "$care_meet" = "('none', 'round 1 reviewed this change and left no must-fix')" ]; then
  pass "a careful change keeps its review through a rebase with no conflict, onto a base that left its files alone and onto one that changed one of them in other lines"
else
  fail "a careful change after a rebase with no conflict: $care_alone / $care_meet"
fi

# A watch that is stopped ends the forge's calls, says so, and leaves the board's file saying that nobody watches.
rm -f "$GWS/.lem/state/watch.js"
gw_watch > "$WORK/watch.out" 2> "$WORK/watch.err" &
wpid=$!
soon looked 1
kill -TERM "$wpid"
set +e; wait "$wpid"; wcode=$?; set -e
if [ "$wcode" = 1 ] && grep -qF "land.py: the watch was stopped" "$WORK/watch.err" && [ "$(watched '(d["ended"] is not None, d["why"].startswith("the watch was stopped"))')" = "(True, True)" ]; then
  pass "a watch that is stopped exits 1, says so, and its file for the board says that it ended"
else
  fail "a stopped watch: code=$wcode / $(cat "$WORK/watch.err")"
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
  printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' 'land = "owner"' '[gate]' 'commands = ["true"]' > "$GXS/.lem/project.toml"
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
  # the settings of that commit name the checks `[gate]`, which the scripts of now refuse with the lines the owner writes
  printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' 'land = "owner"' '[checks]' 'commands = ["true"]' > "$GXS/.lem/project.toml"
  gx_land() { PATH="$WORK/bin:$PATH" GH_STATE="$WORK/gx.json" GH_ORIGIN="$GXO" "$PY" -B "$LAND" --repo "$GXS" "$@"; }
  merged=$(gx_land merged old-pr 2>"$WORK/gx.err" | field 'd["merged"]' 2>&1 || true)
  cleaned=$(gx_land clean old-pr 2>&1 | field 'd["worktree"]' 2>&1 || true)
  if [ "$opened" = "[('old-pr', 'open')]" ] && grep -qF "project.py: moved Lem's state from $GXS/.git/lem to $GXS/.lem/state (renamed)" "$WORK/gx.err" \
    && [ "$merged" = "$head" ] && [ "$(status_in "$GXS" old-pr)" = landed ] && [ "$cleaned" = True ] && [ ! -e "$GXS/.git/lem" ] \
    && [ "$(git -C "$GXS" rev-parse main)" = "$head" ] && [ -z "$(git -C "$GXS" status --porcelain --untracked-files=all -- . ':!.lem/project.toml')" ]; then
    pass "a pull request opened by the scripts before the state moved and merged by the owner on the forge is finished by merged of now, which moves the state and says so; tasks and clean read it there"
  else
    fail "an old pull request after the move: $opened / $merged / $cleaned / $(cat "$WORK/gx.err")"
  fi
else
  skip "a pull request opened before the state moved: this clone does not have commit ccba3bd"
fi

finish
