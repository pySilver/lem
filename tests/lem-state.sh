#!/usr/bin/env bash
# Where Lem keeps a repository's state: `.lem/state/` of the main checkout, which git never sees, and
# the owner's status, there or away.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

# A .lem/.gitignore that names only the machine's own file: the state folder hides itself.
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
  && [ ! -s "$WORK/state.err" ] && [ ! -e "$WORK/state-wt/.lem/state" ] \
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
# and one opened while he is away too, from its opening; `owner back` takes them back; `waiting` says first that he
# is away and since when; an ended task is no task of his "away".
MO=$WORK/mode-repo
git init -q -b main "$MO" && commit "$MO" start && project --repo "$MO" init --base main >/dev/null
for slug in gift-note other-task landed-task; do project --repo "$MO" task-dir "$slug" >/dev/null; project --repo "$MO" state "$slug" building "it builds" >/dev/null; done
project --repo "$MO" state landed-task landed "main a..b" >/dev/null
modes() { project --repo "$MO" tasks | field '[(t["slug"], t["mode"], len(t["without_owner"])) for t in d]'; }
before=$(modes)
# the log's time is to the second: the away comes after the landed task's last event
sleep 1
away=$(project --repo "$MO" owner away --words "I'm away" | field '(d["away"], d["written"], d["tasks"])')
again=$(project --repo "$MO" owner away --words "away" | field '(d["away"], d["written"])')
listed=$(project --repo "$MO" waiting | field '(d["owner"]["away"], d["owner"]["words"], d["owner"]["since"] is not None)')
away_since=$(project --repo "$MO" waiting | field 'd["owner"]["since"]')
sleep 1
project --repo "$MO" task-dir new-task --ask "Opened while he is away." >/dev/null && project --repo "$MO" state new-task building "it builds" >/dev/null
opened=$(project --repo "$MO" tasks | field "[t['without_owner'][0]['from'] > '$away_since' and t['without_owner'][0]['started']['words'] == \"I'm away\" for t in d if t['slug'] == 'new-task'][0]")
during=$(modes)
back=$(project --repo "$MO" owner back --words "/lem im-back" | field '(d["away"], d["written"], d["tasks"])')
after=$(modes)
there=$(project --repo "$MO" owner back --words "I'm back" | field 'd["written"]')
wrong=$(project --repo "$MO" owner sideways --words "go" 2>&1 || true)
nowords=$(status_of project --repo "$MO" owner away --words " ")
nowords_text=$(project --repo "$MO" owner away --words " " 2>&1 || true)
forged=$(project --repo "$MO" log gift-note task.mode mode=alone 2>&1 || true)
events=$(grep -c '"event": "owner"' "$MO/.lem/state/events.jsonl")
if [ "$before" = "[('gift-note', 'with-owner', 0), ('landed-task', 'with-owner', 0), ('other-task', 'with-owner', 0)]" ] \
  && [ "$away" = "(True, True, ['gift-note', 'other-task'])" ] && [ "$again" = "(True, False)" ] && [ "$listed" = "(True, \"I'm away\", True)" ] \
  && [ "$during" = "[('gift-note', 'alone', 1), ('landed-task', 'with-owner', 0), ('new-task', 'alone', 1), ('other-task', 'alone', 1)]" ] \
  && [ "$opened" = True ] \
  && [ "$back" = "(False, True, ['gift-note', 'new-task', 'other-task'])" ] \
  && [ "$after" = "[('gift-note', 'with-owner', 1), ('landed-task', 'with-owner', 0), ('new-task', 'with-owner', 1), ('other-task', 'with-owner', 1)]" ] \
  && [ "$there" = False ] && grep -qF "the owner is away or back, not 'sideways'" <<<"$wrong" && [ "$nowords" = 1 ] \
  && grep -qF '("I'"'"'m away", "/lem im-back")' <<<"$nowords_text" \
  && grep -qF "task.mode is written by \`lem project owner\` and \`task-dir --night\` only" <<<"$forged" && [ "$events" = 2 ]; then
  pass "the owner says whether he is there: away makes every open task run without him, one opened while he is away from its opening, back takes them all back, the list says that he is away, an ended task stays out of it, and nothing is written for words that change nothing"
else
  fail "the owner's status: $before / $away / $again / $listed / $opened / $during / $back / $after / $there / $wrong / $nowords / $forged / $events"
fi

finish
