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
# task-dir puts the repository's main checkout into the machine's list of workspaces, once, also from a task's
# worktree, so that the board server shows it from its first task; a state folder of example tasks stays out.
listed() { "$PY" -c 'import json, sys; print(json.load(open(sys.argv[1])))' "$XDG_CONFIG_HOME/lem/workspaces.json"; }
first_list=$(listed)
project --repo "$ST" task-dir second-task --ask "A second one." >/dev/null
DM=$WORK/demo-repo
git init -q -b main "$DM" && ident "$DM" && project --repo "$DM" init --base main >/dev/null && touch "$(project --repo "$DM" state-dir)/demo"
project --repo "$DM" task-dir an-example --ask "An example." >/dev/null
if [ "$first_list" = "['$ST']" ] && [ "$(listed)" = "['$ST']" ]; then
  pass "task-dir puts the main checkout into the machine's list of workspaces once, also from a task's worktree, and a state folder of example tasks stays out"
else
  fail "the list of workspaces: $first_list / $(listed)"
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
# the log's time is to the second: the task opens after the back above, which a back in its own second would end at
# its opening, a span of no length
sleep 1
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

# The watch of the mark (criterion 5's wake-up): started in the second repository with the `seen` it read, it ends after
# an away in the first with that record; started with a `seen` that is no longer the count, it ends at once; an away and a back written in one
# second, which share their `ts`, end it too, since the count is its cursor. It writes nothing to the mark, a stop ends
# it with exit 1, and it is refused outside a repository and without a count it can take.
watch_in() { XDG_CONFIG_HOME=$MACHINE "$PY" -B "$PROJECT" --repo "$SECOND" owner watch "$@"; }
# at_once ARGS...: the watch of the second repository with a clock that refuses a wait, so that "at once" is no count of
# seconds: a watch that sleeps before its next look ends here with that message
at_once() {
  XDG_CONFIG_HOME=$MACHINE "$PY" -B -c 'import sys, time, types
sys.path.insert(0, sys.argv[1])
import project
def refused(seconds): sys.exit(f"the watch waited {seconds} s for its next look")
project.time = types.SimpleNamespace(**{**{name: getattr(time, name) for name in dir(time) if not name.startswith("_")}, "sleep": refused})
project.main(sys.argv[2:])' "$PWD/skills/lem/scripts" --repo "$SECOND" owner watch "$@"
}
# looping ARGS... &: the watch of the second repository, in the job's own process (exec: a stop reaches it), whose every wait
# first leaves the file $WORK/looping: the sign that it reached its loop, where a stop has its own answer, in place of
# a second of waiting
looping() {
  XDG_CONFIG_HOME=$MACHINE exec "$PY" -B -c 'import pathlib, sys, time, types
sys.path.insert(0, sys.argv[1])
import project
def marked(seconds): pathlib.Path(sys.argv[2]).touch(); time.sleep(seconds)
project.time = types.SimpleNamespace(**{**{name: getattr(time, name) for name in dir(time) if not name.startswith("_")}, "sleep": marked})
project.main(sys.argv[3:])' "$PWD/skills/lem/scripts" "$WORK/looping" --repo "$SECOND" owner watch "$@"
}
watching() { [ -e "$WORK/looping" ]; }
seen=$(on "$SECOND" waiting | field 'd["owner"]["seen"]')
rm -f "$WORK/looping"
looping --seen "$seen" --every 1 > "$WORK/watch.out" 2>&1 &
watcher=$!
soon watching
away_at=$(on "$FIRST" owner away --words "/lem im-away" | field 'd["since"]')
started=$(date +%s)
watched=0
wait "$watcher" || watched=$?
took=$(( $(date +%s) - started ))
heard=$(field '(d["away"], d["since"], d["words"], d["seen"])' < "$WORK/watch.out" 2>&1 || true)
lines=$(grep -c '' "$MACHINE/lem/owner.jsonl")
at_once --seen 0 > "$WORK/stale.out" 2>&1 || true
stale=$(field '(d["away"], d["since"], d["seen"])' < "$WORK/stale.out" 2>/dev/null || cat "$WORK/stale.out")
# a back and an away in one second share their `ts`: two lines of the mark's form with one time, as two commands in one
# second write them, so that no two commands have to fall in one second here
before_pair=$(on "$SECOND" waiting | field 'd["owner"]["seen"]')
again_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"$PY" -I -c 'import json, sys; mark, ts, first, second = sys.argv[1:]; open(mark, "a").write("".join(json.dumps({"ts": ts, "event": "owner", "task": None, "away": away, "by": "owner", "words": words, "repo": repo}) + "\n" for away, words, repo in ((False, "/lem im-back", first), (True, "/lem im-away", second))))' \
  "$MACHINE/lem/owner.jsonl" "$again_ts" "$FIRST" "$SECOND"
at_once --seen "$before_pair" > "$WORK/paired.out" 2>&1 || true
paired=$(field '(d["away"], d["since"], d["seen"])' < "$WORK/paired.out" 2>/dev/null || cat "$WORK/paired.out")
kept=$(grep -c '' "$MACHINE/lem/owner.jsonl")
# the watch's own process in the background, so that the stop reaches it
rm -f "$WORK/looping"
looping --seen "$kept" > "$WORK/watch-stop.out" 2>&1 &
stopper=$!
soon watching
kill -TERM "$stopper"
stopped_code=0
wait "$stopper" || stopped_code=$?
no_seen=$(watch_in 2>&1 || true)
negative=$(watch_in --seen -1 2>&1 || true)
outside=$(cd "$WORK/no-repo" && XDG_CONFIG_HOME=$MACHINE "$PY" -B "$PROJECT" owner watch --seen 0 2>&1 || true)
if [ "$watched" = 0 ] && [ "$took" -lt 15 ] && [ "$heard" = "(True, '$away_at', '/lem im-away', $((seen + 1)))" ] \
  && [ "$stale" = "(True, '$away_at', $lines)" ] && [ "$(grep -c '' "$MACHINE/lem/owner.jsonl")" = "$kept" ] \
  && [ "$paired" = "(True, '$again_ts', $((before_pair + 2)))" ] && [ "$kept" = "$((before_pair + 2))" ] \
  && [ "$stopped_code" = 1 ] && grep -qF "the watch of the owner's status was stopped; start no other until the reason for the stop is gone" "$WORK/watch-stop.out" \
  && grep -qF "watch takes --seen N" <<<"$no_seen" && grep -qF "0 or more, not -1" <<<"$negative" && grep -qF "is not inside a git checkout" <<<"$outside"; then
  pass "the watch of the owner's mark in one repository ends after his away in another with that record; a count that is no longer the mark's ends it at once, as an away and a back written in one second do; it writes nothing to the mark, a stop ends it with exit 1 and asks for no second watch, and it is refused outside a repository and without a count"
else
  fail "the watch of the owner's mark: $watched / ${took}s / $heard / $stale / $again_ts $paired / $kept / $stopped_code $(cat "$WORK/watch-stop.out") / $no_seen / $negative / $outside"
fi

# What the state folder keeps: `lem project prune` removes, once state.keep_days passed, the working files of a task that
# ended and the old folders of the experts, the panels, the naps and the cast's copies. A task's documents and records
# stay, and `tasks` and `lem decisions` read it as before; an open task, a young one and one whose state does not read
# are not touched; a link is never followed, a removal that fails is named and the others go on, and a dry run
# removes nothing.
PR=$WORK/prune-repo
git init -q -b main "$PR" && commit "$PR" start && project --repo "$PR" init --base main >/dev/null
PS=$(project --repo "$PR" state-dir)
for slug in old-landed young-landed still-open old-dropped; do project --repo "$PR" task-dir "$slug" --ask "The ask of $slug." >/dev/null; done
project --repo "$PR" state old-landed landed "main: pull request 1 is merged" >/dev/null
project --repo "$PR" state young-landed landed "main: pull request 2 is merged" >/dev/null
project --repo "$PR" state still-open building "lead: builder" >/dev/null
project --repo "$PR" state old-dropped building "lead: builder" >/dev/null
"$PY" -B "$DECISIONS" --repo "$PR" log old-dropped --what "Which name?" --chose "A" --why "It reads plainly." --by lead >/dev/null
project --repo "$PR" state old-dropped dropped "nobody will build it" >/dev/null
mkdir -p "$PS/tasks/broken-state" && printf 'not a state line\n' > "$PS/tasks/broken-state/state.md"
OLD=$PS/tasks/old-landed
mkdir -p "$OLD/media" "$OLD/reviews/old-landed/01-initial/agents" "$OLD/locked"
"$PY" -c 'import sys; [open(p, "wb").write(b"\x89PNG\r\n\x1a\n" + bytes(8)) for p in sys.argv[1:]]' "$OLD/media/shown.png" "$OLD/media/unshown.png"
printf '# Report\n\nSee ![it](media/shown.png).\n' > "$OLD/report.md"
printf '{"proposed": "abc"}\n' > "$OLD/landing.json"
printf 'started landed\n' > "$OLD/ticket-steps.txt"
printf '# Round 1\n' > "$OLD/reviews/old-landed/01-initial/report.md"
printf '{}\n' > "$OLD/reviews/old-landed/01-initial/agents/a.jsonl"
printf 'scratch\n' > "$OLD/scratch.txt" && printf 'held\n' > "$OLD/locked/held.txt" && printf 'kept outside\n' > "$WORK/outside.txt"
ln -s "$WORK/outside.txt" "$OLD/link.txt"
cp "$OLD/scratch.txt" "$PS/tasks/young-landed/scratch.txt" && cp "$OLD/scratch.txt" "$PS/tasks/still-open/scratch.txt" && cp "$OLD/scratch.txt" "$PS/tasks/old-dropped/scratch.txt"
# the old tasks' events 40 days back, each line kept whole; the old folders 40 days back by their last write or their name
"$PY" -c 'import json, sys
from datetime import datetime, timedelta, timezone
old = (datetime.now(timezone.utc) - timedelta(days=40)).strftime("%Y-%m-%dT%H:%M:%SZ")
lines = open(sys.argv[1], encoding="utf-8").read().split("\n")
for n, line in enumerate(lines):
    if line.strip() and json.loads(line).get("task") in ("old-landed", "old-dropped"):
        lines[n] = line.replace(json.loads(line)["ts"], old, 1)
open(sys.argv[1], "w", encoding="utf-8").write("\n".join(lines))' "$PS/events.jsonl"
mkdir -p "$PS/experts/2026-01-02-101010-an-old-question" "$PS/experts/$(date -u +%Y-%m-%d)-101010-a-new-question" "$PS/experts/notes" \
  "$PS/panels/2026-01-02-an-old-panel" "$PS/naps/2020-01-02-0300-an-old-dream" "$PS/naps/$(date -u +%Y-%m-%d-%H%M)-a-new-dream" "$PS/personas-cast/0123abc" "$PS/personas-cast/4567def"
printf 'q\n' > "$PS/experts/2026-01-02-101010-an-old-question/brief.md" && printf 'p\n' > "$PS/panels/2026-01-02-an-old-panel/answer.md"
printf 'd\n' > "$PS/naps/2020-01-02-0300-an-old-dream/dream.md" && printf 'c\n' > "$PS/personas-cast/0123abc/merchant.md" && printf 'c\n' > "$PS/personas-cast/4567def/merchant.md"
ln -s "$WORK" "$PS/panels/2026-01-03-a-link"
"$PY" -c 'import os, sys, time
old = time.time() - 40 * 86400
for top in sys.argv[1:]:
    for root, dirs, files in os.walk(top):
        for name in files: os.utime(os.path.join(root, name), (old, old))
    os.utime(top, (old, old))' "$PS/experts/2026-01-02-101010-an-old-question" "$PS/experts/notes" "$PS/panels/2026-01-02-an-old-panel" "$PS/personas-cast/0123abc"
listing() { (cd "$PS" && find . -not -type d | LC_ALL=C sort | tr '\n' ' '); }
before_dry=$(listing)
dry=$(project --repo "$PR" prune --dry-run)
after_dry=$(listing)
dry_all=$(project --repo "$PR" prune --dry-run --days 0)
no_days=$(project --repo "$PR" prune --days 3 2>&1 || true)
chmod 555 "$OLD/locked"
real_code=0
real=$(project --repo "$PR" prune) || real_code=$?
chmod 755 "$OLD/locked"
again=$(project --repo "$PR" prune)
tasks_after=$(project --repo "$PR" tasks | field '[(t["slug"], t["status"], t["ticket_steps"]) for t in d if t["slug"] in ("old-landed", "old-dropped")]')
decided=$("$PY" -B "$DECISIONS" --repo "$PR" list old-dropped 2>&1 || true)
if [ "$before_dry" = "$after_dry" ] && [ "$(field '(d["dry_run"], d["keep_days"], d["from"], [t["task"] for t in d["tasks"]])' <<<"$dry")" = "(True, 30, 'state.keep_days', ['old-dropped', 'old-landed'])" ] \
  && [ "$(field '[t["task"] for t in d["tasks"]]' <<<"$dry_all")" = "['old-dropped', 'old-landed', 'young-landed']" ] && [ "$(field 'd["from"]' <<<"$dry_all")" = "--days 0" ] \
  && grep -qF -- "--days goes with --dry-run only" <<<"$no_days" && [ "$real_code" = 1 ] \
  && [ "$(field '[f["path"] for f in d["failed"]]' <<<"$real")" = "['tasks/old-landed/locked/held.txt']" ] \
  && [ "$(field 'sorted(f["path"] for f in d["folders"])' <<<"$real")" = "['experts/2026-01-02-101010-an-old-question', 'naps/2020-01-02-0300-an-old-dream', 'panels/2026-01-02-an-old-panel', 'personas-cast/0123abc']" ] \
  && [ "$(field '[(t["task"], t["files"]) for t in d["tasks"]]' <<<"$again")" = "[('old-landed', ['locked/held.txt'])]" ] && [ "$(field '(d["folders"], d["failed"])' <<<"$again")" = "([], [])" ] \
  && [ ! -e "$OLD/scratch.txt" ] && [ ! -e "$OLD/media/unshown.png" ] && [ ! -e "$OLD/reviews/old-landed/01-initial/agents" ] && [ ! -e "$PS/tasks/old-dropped/scratch.txt" ] \
  && [ -f "$OLD/media/shown.png" ] && [ -f "$OLD/report.md" ] && [ -f "$OLD/reviews/old-landed/01-initial/report.md" ] && [ -f "$OLD/state.md" ] && [ -f "$OLD/ask.txt" ] \
  && [ -f "$OLD/landing.json" ] && [ -f "$OLD/ticket-steps.txt" ] && [ ! -e "$OLD/locked" ] && [ -L "$OLD/link.txt" ] && [ "$(cat "$WORK/outside.txt")" = "kept outside" ] \
  && [ -f "$PS/tasks/young-landed/scratch.txt" ] && [ -f "$PS/tasks/still-open/scratch.txt" ] && [ -f "$PS/tasks/old-dropped/decisions.jsonl" ] \
  && [ ! -e "$PS/experts/2026-01-02-101010-an-old-question" ] && [ -d "$PS/experts/notes" ] && [ -d "$PS/experts/$(date -u +%Y-%m-%d)-101010-a-new-question" ] \
  && [ ! -e "$PS/panels/2026-01-02-an-old-panel" ] && [ -L "$PS/panels/2026-01-03-a-link" ] && [ -d "$WORK/no-repo" ] \
  && [ ! -e "$PS/naps/2020-01-02-0300-an-old-dream" ] && [ -d "$PS/naps/$(date -u +%Y-%m-%d-%H%M)-a-new-dream" ] && [ ! -e "$PS/personas-cast/0123abc" ] && [ -d "$PS/personas-cast/4567def" ] \
  && grep -qF "'tasks/broken-state'" <<<"$(field '[s["path"] for s in d["skipped"]]' <<<"$again")" && grep -qF "'tasks/old-landed/link.txt'" <<<"$(field '[s["path"] for s in d["skipped"]]' <<<"$again")" \
  && grep -qF "'panels/2026-01-03-a-link'" <<<"$(field '[s["path"] for s in d["skipped"]]' <<<"$again")" \
  && [ "$tasks_after" = "[('old-dropped', 'dropped', []), ('old-landed', 'landed', ['started', 'landed'])]" ] && grep -qF "Which name?" <<<"$decided"; then
  pass "lem project prune removes the working files of a task that ended before state.keep_days and the old folders of the experts, the panels, the naps and the cast's copies, keeps every document, record and shown picture, and tasks and decisions read the task as before; an open or young task and a state that does not read are not touched, a link is never followed, a failed removal is named with exit 1, and a dry run removes nothing"
else
  fail "the prune: $dry / $dry_all / $no_days / $real_code / $real / $again / $tasks_after / ${decided:0:300} / $(listing)"
fi

finish
