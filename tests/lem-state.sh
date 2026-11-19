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
events=$(grep -c '"event": "owner"' "$MO/.lem/state/events.jsonl" || true)/$(grep -c '' "$XDG_CONFIG_HOME/lem/owner.jsonl" 2>/dev/null || true)
if [ "$before" = "[('gift-note', 'with-owner', 0), ('landed-task', 'with-owner', 0), ('other-task', 'with-owner', 0)]" ] \
  && [ "$away" = "(True, True, ['gift-note', 'other-task'])" ] && [ "$again" = "(True, False)" ] && [ "$listed" = "(True, \"I'm away\", True)" ] \
  && [ "$during" = "[('gift-note', 'alone', 1), ('landed-task', 'with-owner', 0), ('new-task', 'alone', 1), ('other-task', 'alone', 1)]" ] \
  && [ "$opened" = True ] \
  && [ "$back" = "(False, True, ['gift-note', 'new-task', 'other-task'])" ] \
  && [ "$after" = "[('gift-note', 'with-owner', 1), ('landed-task', 'with-owner', 0), ('new-task', 'with-owner', 1), ('other-task', 'with-owner', 1)]" ] \
  && [ "$there" = False ] && grep -qF "the owner is away or back, not 'sideways'" <<<"$wrong" && [ "$nowords" = 1 ] \
  && grep -qF '("I'"'"'m away", "/lem im-back")' <<<"$nowords_text" \
  && grep -qF "task.mode is written by \`lem project owner\` and \`task-dir --night\` only" <<<"$forged" && [ "$events" = 0/2 ]; then
  pass "the owner says whether he is there: away makes every open task run without him, one opened while he is away from its opening, back takes them all back, the list says that he is away, an ended task stays out of it, and nothing is written for words that change nothing; his two words are two lines of the machine's mark and none of the repository's log"
else
  fail "the owner's status: $before / $away / $again / $listed / $opened / $during / $back / $after / $there / $wrong / $nowords / $forged / $events"
fi


# The owner's status is the machine's: one mark, owner.jsonl under $XDG_CONFIG_HOME/lem, which every repository reads.
# With no mark he is there, and a read makes nothing; his away in one repository is read in another with the same time,
# his back in the second is read in the first; a line of the mark that does not read is refused with the file and the
# line; a relative XDG_CONFIG_HOME is refused; and with the variable unset the mark is under HOME/.config/lem.
FIRST=$WORK/first-repo SECOND=$WORK/second-repo MACHINE=$WORK/machine-config
for repo in "$FIRST" "$SECOND"; do git init -q -b main "$repo" && commit "$repo" start && project --repo "$repo" init --base main >/dev/null; done
mkdir -p "$MACHINE"
on() { XDG_CONFIG_HOME=$MACHINE project --repo "$@"; }
said() { on "$1" waiting | field '(d["owner"]["away"], d["owner"]["since"], d["owner"]["words"], d["owner"].get("seen"))'; }
fresh=$(said "$FIRST")/$(said "$SECOND")
made=$([ -e "$MACHINE/lem" ] && echo made || echo none)
away_at=$(on "$FIRST" owner away --words "/lem im-away" | field 'd["since"]')
in_second=$(said "$SECOND")
back_at=$(on "$SECOND" owner back --words "/lem im-back" | field 'd["since"]')
in_first=$(said "$FIRST")
mark=$(field '[(r["event"], r["task"], r["away"], r["by"], r["repo"]) for r in d]' <<<"[$(paste -sd, "$MACHINE/lem/owner.jsonl" 2>/dev/null || true)]")
in_logs=$(cat "$FIRST/.lem/state/events.jsonl" "$SECOND/.lem/state/events.jsonl" 2>/dev/null | grep -c '"event": "owner"' || true)
broken="no mark at $MACHINE/lem/owner.jsonl"
if [ -f "$MACHINE/lem/owner.jsonl" ]; then
  cp "$MACHINE/lem/owner.jsonl" "$WORK/mark.kept" && printf 'not json\n' >> "$MACHINE/lem/owner.jsonl"
  broken=$(on "$SECOND" waiting 2>&1 || true)
  cp "$WORK/mark.kept" "$MACHINE/lem/owner.jsonl"
fi
relative=$(XDG_CONFIG_HOME=config project --repo "$FIRST" waiting 2>&1 || true)
mkdir -p "$WORK/home"
homed=$(env -u XDG_CONFIG_HOME HOME="$WORK/home" "$PY" -B "$PROJECT" --repo "$FIRST" owner away --words "I'm away" | field 'd["written"]')
env -u XDG_CONFIG_HOME HOME="$WORK/home" "$PY" -B "$PROJECT" --repo "$FIRST" owner back --words "I'm back" >/dev/null
if [ "$fresh" = "(False, None, None, 0)/(False, None, None, 0)" ] && [ "$made" = none ] \
  && [ "$in_second" = "(True, '$away_at', '/lem im-away', 1)" ] && [ "$in_first" = "(False, '$back_at', '/lem im-back', 2)" ] \
  && [ "$mark" = "[('owner', None, True, 'owner', '$FIRST'), ('owner', None, False, 'owner', '$SECOND')]" ] && [ "$in_logs" = 0 ] \
  && grep -qF "$MACHINE/lem/owner.jsonl:3 does not read as JSON" <<<"$broken" && grep -qF "XDG_CONFIG_HOME is 'config', a relative path" <<<"$relative" \
  && [ "$homed" = True ] && [ "$(grep -c '' "$WORK/home/.config/lem/owner.jsonl" 2>/dev/null || true)" = 2 ]; then
  pass "the owner's status is one mark of the machine: with none he is there and nothing is made; his away in one repository is read in another with its time, and his back in the second in the first; the mark holds each with the repository he typed it in, and no repository's log does; a broken line and a relative XDG_CONFIG_HOME are refused, and without the variable the mark is under HOME/.config/lem"
else
  fail "the machine's mark: $fresh / $made / $in_second / $in_first / $mark / $in_logs / $broken / $relative / $homed"
fi

# The pull request's line of the time without the owner, for a task of the second repository: the span from his away in
# the first to his back in the second.
on "$SECOND" task-dir span-task --ask "Put the word into the file." >/dev/null && on "$SECOND" state span-task building "lead: builder" >/dev/null
sleep 1
away_at=$(on "$FIRST" owner away --words "I'm away" | field 'd["since"]')
sleep 1
back_at=$(on "$SECOND" owner back --words "/lem im-back" | field 'd["since"]')
line=$(on "$SECOND" tasks | "$PY" -B -c 'import json, sys, types; sys.path.insert(0, sys.argv[1]); import land; task = next(t for t in json.load(sys.stdin) if t["slug"] == "span-task"); print(task["mode"], land.without_owner(types.SimpleNamespace(record=task)))' "$PWD/skills/lem/scripts")
if [ "$line" = "with-owner It ran without the owner from ${away_at:0:10} ${away_at:11:5} UTC (the owner: \"I'm away\") to ${back_at:0:10} ${back_at:11:5} UTC (the owner: \"/lem im-back\")." ]; then
  pass "a task of one repository ran without the owner from his away in another repository to his back in its own, and the pull request's line says that span"
else
  fail "the span without the owner across two repositories: $line / $away_at / $back_at"
fi

finish
