#!/usr/bin/env bash
# Where Lem keeps a repository's state: `.lem/state/` of the main checkout, which git never sees, and
# the one move of the state folder Lem kept in the git directory before (`.git/lem/`), here with a
# task that the scripts of that time took to `open` and that the scripts of now then land.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

# A repository onboarded before the state moved: its .lem/.gitignore names only the machine's own file.
ST=$WORK/state-repo
git init -q -b main "$ST" && ident "$ST"
project --repo "$ST" init --base main >/dev/null
fresh_ignore=$(cat "$ST/.lem/.gitignore")
printf 'project.local.toml\n' > "$ST/.lem/.gitignore"
git -C "$ST" add -A && git -C "$ST" commit -q -m "chore: start"
git -C "$ST" worktree add -q "$WORK/state-wt" -b side
from_wt=$(project --repo "$WORK/state-wt" state-dir 2>"$WORK/state.err")
project --repo "$WORK/state-wt" task-dir one-task --ask "Keep the state out of git." >/dev/null
project --repo "$WORK/state-wt" state one-task held "the interview waits for the owner" >/dev/null
if [ "$fresh_ignore" = "$(printf 'project.local.toml\nstate/')" ] && [ "$from_wt" = "$ST/.lem/state" ] && [ -f "$ST/.lem/state/tasks/one-task/state.md" ] \
  && [ ! -s "$WORK/state.err" ] && [ ! -e "$WORK/state-wt/.lem/state" ] && [ ! -e "$ST/.git/lem" ] \
  && [ -z "$(git -C "$ST" status --porcelain --untracked-files=all --ignored=no)" ] && [ -z "$(git -C "$WORK/state-wt" status --porcelain --untracked-files=all)" ] \
  && [ "$(cat "$ST/.lem/.gitignore")" = "project.local.toml" ] && [ "$(cat "$ST/.lem/state/.gitignore")" = "*" ]; then
  pass "the state is in .lem/state of the main checkout, also for a script run in a task's worktree; git sees none of it where .lem/.gitignore does not name it, no tracked file changes for it, and a new project's .lem/.gitignore names it"
else
  fail "the place of the state: $fresh_ignore / $from_wt / $(cat "$WORK/state.err") / $(git -C "$ST" status --porcelain --untracked-files=all)"
fi
# Outside a repository there is no state folder, and the script says why.
mkdir -p "$WORK/no-repo"
err=$(cd "$WORK/no-repo" && "$PY" -B "$PROJECT" state-dir 2>&1 || true)
code=$(cd "$WORK/no-repo" && status_of "$PY" -B "$PROJECT" state-dir)
corr_err=$("$PY" -B "$PWD/skills/lem/scripts/corrections.py" --repo "$WORK/no-repo" list 2>&1 || true)
if [ "$code" = 1 ] && grep -qF "is not inside a git checkout" <<<"$err" && grep -qF "is not inside a git checkout" <<<"$corr_err" && [ ! -e "$WORK/no-repo/.lem" ]; then
  pass "outside a repository the state folder is refused with exit 1 and the reason, and nothing is made"
else
  fail "the state outside a repository: $err / $corr_err"
fi

# The owner says whether he is there, and Lem assumes nothing: `owner away` makes every open task run without him,
# and one opened while he is away too, from its opening; `owner active` takes them back, also a task an older Lem's
# "go alone" put so; `waiting` says first that he is away and since when; an ended task is no task of his "away".
MO=$WORK/mode-repo
git init -q -b main "$MO" && commit "$MO" start && project --repo "$MO" init --base main >/dev/null
for slug in gift-note other-task landed-task; do project --repo "$MO" task-dir "$slug" >/dev/null; project --repo "$MO" state "$slug" building "it builds" >/dev/null; done
project --repo "$MO" state landed-task landed "main a..b" >/dev/null
modes() { project --repo "$MO" tasks | field '[(t["slug"], t["mode"], len(t["without_owner"])) for t in d]'; }
before=$(modes)
old_mode "$MO" gift-note alone "go alone"
after_old=$(modes)
sleep 1
away=$(project --repo "$MO" owner away --words "I'm away" | field '(d["away"], d["written"], d["tasks"])')
again=$(project --repo "$MO" owner away --words "away" | field '(d["away"], d["written"])')
listed=$(project --repo "$MO" waiting | field '(d["owner"]["away"], d["owner"]["words"], d["owner"]["since"] is not None)')
away_since=$(project --repo "$MO" waiting | field 'd["owner"]["since"]')
sleep 1
project --repo "$MO" task-dir new-task --ask "Opened while he is away." >/dev/null && project --repo "$MO" state new-task building "it builds" >/dev/null
opened=$(project --repo "$MO" tasks | field "[t['without_owner'][0]['from'] > '$away_since' and t['without_owner'][0]['started']['words'] == \"I'm away\" for t in d if t['slug'] == 'new-task'][0]")
during=$(modes)
back=$(project --repo "$MO" owner active --words "/lem active" | field '(d["away"], d["written"], d["tasks"])')
after=$(modes)
there=$(project --repo "$MO" owner active --words "I'm back" | field 'd["written"]')
wrong=$(project --repo "$MO" owner sideways --words "go" 2>&1 || true)
nowords=$(status_of project --repo "$MO" owner away --words " ")
forged=$(project --repo "$MO" log gift-note task.mode mode=alone 2>&1 || true)
events=$(grep -c '"event": "owner"' "$MO/.lem/state/events.jsonl")
if [ "$before" = "[('gift-note', 'with-owner', 0), ('landed-task', 'with-owner', 0), ('other-task', 'with-owner', 0)]" ] \
  && [ "$after_old" = "[('gift-note', 'alone', 1), ('landed-task', 'with-owner', 0), ('other-task', 'with-owner', 0)]" ] \
  && [ "$away" = "(True, True, ['gift-note', 'other-task'])" ] && [ "$again" = "(True, False)" ] && [ "$listed" = "(True, \"I'm away\", True)" ] \
  && [ "$during" = "[('gift-note', 'alone', 1), ('landed-task', 'with-owner', 0), ('new-task', 'alone', 1), ('other-task', 'alone', 1)]" ] \
  && [ "$opened" = True ] \
  && [ "$back" = "(False, True, ['gift-note', 'new-task', 'other-task'])" ] \
  && [ "$after" = "[('gift-note', 'with-owner', 1), ('landed-task', 'with-owner', 0), ('new-task', 'with-owner', 1), ('other-task', 'with-owner', 1)]" ] \
  && [ "$there" = False ] && grep -qF "the owner is away or active, not 'sideways'" <<<"$wrong" && [ "$nowords" = 1 ] \
  && grep -qF "task.mode is written by \`lem project owner\` and \`task-dir --night\` only" <<<"$forged" && [ "$events" = 2 ]; then
  pass "the owner says whether he is there: away makes every open task run without him, one opened while he is away from its opening, active takes them all back with an older Lem's \"go alone\", the list says that he is away, an ended task stays out of it, and nothing is written for words that change nothing"
else
  fail "the owner's status: $before / $after_old / $away / $again / $listed / $opened / $during / $back / $after / $there / $wrong / $nowords / $forged / $events"
fi

# The scripts of the commit before the move, for a repository whose state they wrote. A shallow clone may not have
# that commit: the checks that need it are skipped there, with a line for each.
OLD=$WORK/old-lem
if ! git cat-file -e "ccba3bd^{commit}" 2>/dev/null; then
  skip_rest "this clone does not have commit ccba3bd"
  finish
  exit 0
fi
mkdir -p "$OLD"
git archive ccba3bd skills | tar -x -C "$OLD"
oproject() { "$PY" -B "$OLD/skills/lem/scripts/project.py" "$@"; }
ostories() { "$PY" -B "$OLD/skills/lem/scripts/stories.py" "$@"; }
oland() { "$PY" -B "$OLD/skills/lem/scripts/land.py" "$@"; }
# old_open REPO SLUG: a small change that the scripts before the move took through the checks and one read to `open`
old_open() {
  local tree directory
  directory=$(oproject --repo "$1" task-dir "$2" --ask "Put the word into $2.txt.")
  printf '%s\n' '## Stories' '' 'Kind: correction, because the request is one sentence.' '' '1. The file holds the word the owner asked for.' > "$directory/stories.md"
  ostories --repo "$1" approve "$2" --file "$directory/stories.md" --correction >/dev/null
  printf '%s\n' "   - test: \`sh tests/$2.sh\` in \`tests/$2.sh\`" >> "$directory/stories.md"
  tree=$(oproject --repo "$1" worktree-dir "$2")
  git -C "$1" worktree add -q "$tree" -b "fix/$2" main
  mkdir -p "$tree/tests" && echo word > "$tree/$2.txt" && echo "grep -qx word $2.txt" > "$tree/tests/$2.sh"
  git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: $2"
  oproject --repo "$tree" state "$2" ready "the small change is built" >/dev/null
  oland --repo "$1" start "$2" >/dev/null && oland --repo "$1" base "$2" >/dev/null && oland --repo "$1" gate "$2" >/dev/null
  oland --repo "$1" read "$2" --record "$(clean 1)" >/dev/null
  oland --repo "$1" propose "$2" --title "fix: $2" --notes "$NOTES" >/dev/null
}
OS=$WORK/old-shape
git init -q -b main "$OS" && ident "$OS"
oproject --repo "$OS" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "owner"' '[gate]' 'commands = ["true"]' > "$OS/.lem/project.toml"
git -C "$OS" add -A && git -C "$OS" commit -q -m "chore: start"
old_open "$OS" old-word
before=$(oproject --repo "$OS" tasks | field '[(t["slug"], t["status"]) for t in d]')
# the scripts of now read the checks as [checks], and refuse the older [gate] with the lines the owner writes in its place
printf '%s\n' '[branch]' 'base = "main"' 'land = "owner"' '[checks]' 'commands = ["true"]' > "$OS/.lem/project.toml"
# The first script of now that reads the state moves it, says so in one line on stderr, and its JSON is as before.
tasks=$(project --repo "$OS" tasks 2>"$WORK/move.err")
again=$(project --repo "$OS" tasks 2>&1 >/dev/null)
if [ "$before" = "[('old-word', 'open')]" ] && [ "$(field '[(t["slug"], t["status"]) for t in d]' <<<"$tasks")" = "$before" ] \
  && [ "$(cat "$WORK/move.err")" = "project.py: moved Lem's state from $OS/.git/lem to $OS/.lem/state (renamed); nothing reads $OS/.git/lem any more" ] \
  && [ -z "$again" ] && [ ! -e "$OS/.git/lem" ] && [ -f "$OS/.lem/state/tasks/old-word/landing.json" ] && [ -f "$OS/.lem/state/events.jsonl" ] \
  && [ -z "$(git -C "$OS" status --porcelain --untracked-files=all -- . ':!.lem/project.toml')" ]; then
  pass "a repository whose state is in .git/lem is moved once by the first script that reads it, which says so in one line on stderr; the next call says nothing, and git sees nothing"
else
  fail "the move of the state: $before / $tasks / $(cat "$WORK/move.err") / $again"
fi
# The task the scripts before the move proposed lands with the scripts of now, by the owner's word, and its worktree goes.
landed=$(land --repo "$OS" land old-word --by owner 2>"$WORK/land.err" | field 'd["range"]' 2>&1 || true)
cleaned=$(land --repo "$OS" clean old-word 2>&1 | field 'd["worktree"]' 2>&1 || true)
if [ -n "$landed" ] && [ "$(status_in "$OS" old-word)" = landed ] && [ "$(git -C "$OS" show main:old-word.txt)" = word ] && [ "$cleaned" = True ] \
  && [ ! -e "$OS/.lem/worktrees/old-word" ] && [ ! -e "$OS/.git/lem" ] && [ -z "$(git -C "$OS" status --porcelain --untracked-files=all -- . ':!.lem/project.toml')" ]; then
  pass "a task the scripts before the move took to open lands by the owner's word with the scripts of now, a fast-forward in the checkout that holds the state, and clean removes its worktree"
else
  fail "the landing of an old task: $landed / $cleaned / $(cat "$WORK/land.err") / $(status_in "$OS" old-word)"
fi
# A sibling script that reads the state through project.py says the move on its own stderr.
RL=$WORK/old-relay
git init -q -b main "$RL" && ident "$RL"
oproject --repo "$RL" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "owner"' '[gate]' 'commands = ["true"]' > "$RL/.lem/project.toml"
git -C "$RL" add -A && git -C "$RL" commit -q -m "chore: start"
old_open "$RL" relayed
printf '%s\n' '[branch]' 'base = "main"' 'land = "owner"' '[checks]' 'commands = ["true"]' > "$RL/.lem/project.toml"
land --repo "$RL" land relayed --by owner >/dev/null 2>"$WORK/relay.err" || true
if grep -qF "project.py: moved Lem's state from $RL/.git/lem to $RL/.lem/state (renamed)" "$WORK/relay.err" && [ "$(status_in "$RL" relayed)" = landed ] && [ ! -e "$RL/.git/lem" ]; then
  pass "when land.py is the first script of now, the line of the move reaches its stderr from the project.py it runs, and the landing goes on"
else
  fail "the move through land.py: $(cat "$WORK/relay.err") / $(status_in "$RL" relayed)"
fi
# Two state folders are never merged: the script refuses, names both, and changes neither.
mkdir -p "$OS/.git/lem/tasks/other-task"
err=$(project --repo "$OS" tasks 2>&1 >/dev/null || true)
code=$(status_of project --repo "$OS" tasks)
if [ "$code" = 1 ] && grep -qF "Lem's state is in two folders, $OS/.git/lem (where Lem kept it before) and $OS/.lem/state, and two are never merged" <<<"$err" \
  && [ -d "$OS/.git/lem/tasks/other-task" ] && [ ! -e "$OS/.lem/state/tasks/other-task" ] && [ -d "$OS/.lem/state/tasks/old-word" ]; then
  pass "with a state folder in both places every script refuses with exit 1, names the two folders, and merges nothing"
else
  fail "two state folders: $code / $err"
fi
rm -r "$OS/.git/lem"

# The correction hook moves the state too, and tells of it in its log, since a hook says nothing.
CH=$WORK/old-hook
git init -q -b main "$CH" && ident "$CH"
oproject --repo "$CH" init --base main >/dev/null
sed -i.bak 's/^collect = false$/collect = true/' "$CH/.lem/project.toml" && rm "$CH/.lem/project.toml.bak"
git -C "$CH" add -A && git -C "$CH" commit -q -m "chore: start"
mkdir -p "$CH/.git/lem" && printf '%s\n' '{"ts": "2026-11-16T10:00:00Z", "session": "old", "cwd": "x", "owner": "an older entry", "previous": "", "p_lesson": 0.8}' > "$CH/.git/lem/corrections.jsonl"
out=$(printf '{"prompt": "never push without asking", "cwd": "%s", "session_id": "s1", "transcript_path": ""}' "$CH" \
  | env LEM_JEV=/usr/bin/false "$PY" -B "$PWD/skills/lem/scripts/corrections.py" hook 2>&1; echo "exit=$?")
soon grep -qs "moved Lem's state" "$CH/.lem/state/corrections.log"
listed=$("$PY" -B "$PWD/skills/lem/scripts/corrections.py" --repo "$CH" list 2>&1 | field '[g["owner"] for g in d["groups"]]' 2>&1 || true)
if [ "$out" = "exit=0" ] && grep -qF "moved Lem's state from $CH/.git/lem to $CH/.lem/state (renamed)" "$CH/.lem/state/corrections.log" && [ ! -e "$CH/.git/lem" ] \
  && [ "$listed" = "['an older entry']" ]; then
  pass "the correction hook moves an older state folder with no output, writes the move into its log, and the queue reads the entries from before"
else
  fail "the hook and the move: $out / $(cat "$CH/.lem/state/corrections.log" 2>&1) / $listed"
fi

finish
