#!/usr/bin/env bash
# The decisions of a task: each one a level of the ladder took, at once, with the owner there or away; and
# the circuit breaker, the one stop of a build, from its trip to the owner's help, his park, his drop and
# his resume.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

DC=$WORK/decisions-repo
git init -q -b main "$DC" && commit "$DC" start && project --repo "$DC" init --base main >/dev/null
project --repo "$DC" task-dir gift-note >/dev/null && project --repo "$DC" task-dir other-task >/dev/null && project --repo "$DC" task-dir race-task >/dev/null
project --repo "$DC" task-dir dropped-task >/dev/null && project --repo "$DC" task-dir landed-task >/dev/null
decide() { "$PY" -B "$DECISIONS" --repo "$DC" "$@"; }
dlist() { decide list gift-note | field "$1"; }
dfile=$DC/.lem/state/tasks/gift-note/decisions.jsonl
lead=$(decide log gift-note --what "The name of the new column" --chose gift_note --why "the other columns of the export are in snake case" --by lead --undo "rename the column" | field '(d["id"], d["kind"], d["by"], d["undo"])')
nosaid=$(decide log gift-note --what "Two notes on one order" --chose "both" --why "nobody loses one" --by personas 2>&1 || true)
nostory=$(status_of decide log gift-note --what "Two notes on one order" --chose "both" --why "nobody loses one" --by lead --criterion 2 --was "the old text")
personas=$(decide log gift-note --what "Two notes on one order" --chose "both notes, with a semicolon between them" --why "a merchant reads both" --by personas \
  --vote "the merchant, opus=both notes, with a semicolon between them" --vote "the accountant, opus=both notes, with a semicolon between them" \
  --said "The merchant and the accountant both picked the semicolon." | field '(d["id"], d["by"], "criterion" in d, d["said"])')
if [ "$lead" = "(1, 'taken', 'lead', 'rename the column')" ] \
  && [ "$personas" = "(2, 'personas', False, 'The merchant and the accountant both picked the semicolon.')" ] \
  && grep -qF -- "--by personas needs a --vote for each answer of a persona" <<<"$nosaid" && [ "$nostory" = 2 ] \
  && [ "$(grep -c '' "$dfile")" = 2 ] && [ "$(grep -c '"event": "decision.taken", "task": "gift-note"' "$DC/.lem/state/events.jsonl")" = 2 ]; then
  pass "a decision of the lead or of the personas is written down with its number, and each is an event too; the personas' one needs their votes, and a decision carries no criterion: a criterion's change has a record of its own"
else
  fail "decisions.py log: $lead / $personas / $nosaid / $nostory / $(cat "$dfile")"
fi

# The circuit breaker, from its trip to a resumed task. A lead of gift-note meets what no option of the ladder keeps:
# the breaker refuses a stop with no document, a document that is a bare question, no handoff and an uncommitted
# change of the worktree; then it records the stop, holds the task with the breaker's line, and the list of what
# waits names it once. A second breaker of the same task waits behind the first.
BR=$WORK/breaker-repo
git init -q -b main "$BR" && ident "$BR" && commit "$BR" start && project --repo "$BR" init --base main >/dev/null
br() { project --repo "$BR" "$@"; }
bdecide() { "$PY" -B "$DECISIONS" --repo "$@"; }
br task-dir gift-note --ask "Add the gift note to the CSV export" >/dev/null
BT=$(br worktree gift-note feat/gift-note | field 'd["worktree"]')
br state gift-note building "lead: builder" "type: feat, because the export gets a column" >/dev/null
bd=$BR/.lem/state/tasks/gift-note
nodoc=$(bdecide "$BT" breaker gift-note --cause criteria 2>&1 || true)
printf '%s\n' '# Where does the note go?' '' '## The options' '' '| | A | B |' '| --- | --- | --- |' '| x | y | z |' > "$bd/breaker.md"
bare=$(bdecide "$BT" breaker gift-note --cause criteria 2>&1 || true)
breaker_doc "$bd" && rm "$bd/handoff.md"
nohandoff=$(bdecide "$BT" breaker gift-note --cause criteria 2>&1 || true)
breaker_doc "$bd"
printf 'half of the note\n' > "$BT/note.txt" && git -C "$BT" add note.txt
dirty=$(bdecide "$BT" breaker gift-note --cause criteria 2>&1 || true)
git -C "$BT" commit -q -m "feat: half of the note"
tripped=$(bdecide "$BT" breaker gift-note --cause criteria | field '(d["id"], d["kind"], d["cause"], d["what"], d["document"])')
breaker_doc "$bd"
twice=$(bdecide "$BT" breaker gift-note --cause irreversible --irreversible person 2>&1 || true)
held=$(br tasks | field 'next((t["status"], t["state"].splitlines()[0].split(": ", 1)[1], t["state"].splitlines()[1]) for t in d if t["slug"] == "gift-note")')
listed=$(br waiting | field '([(b["task"], b["id"], b["status"]) for b in d["breakers"]], d["held"], d["count"])')
if grep -qF "breaker.md is not a file: write the breaker's document first" <<<"$nodoc" \
  && grep -qF "lacks ## Today and after" <<<"$bare" && grep -qF "## The root cause" <<<"$bare" && grep -qF "## The assumptions" <<<"$bare" && ! grep -qF "## The options (" <<<"$bare" \
  && grep -qF "handoff.md is missing" <<<"$nohandoff" && grep -qF "has uncommitted changes of tracked files (1): commit what the task has first" <<<"$dirty" \
  && [ "$tripped" = "(1, 'breaker', 'criteria', 'The gift note has no place that keeps the last column for the total', 'breaker-1.md')" ] && [ -s "$bd/breaker-1.md" ] \
  && grep -qF "breaker 1 of gift-note waits for the owner already" <<<"$twice" \
  && [ "$held" = "('held', 'breaker 1 waits for the owner', 'The gift note has no place that keeps the last column for the total: no option of the ladder keeps the outcome the owner approved')" ] \
  && [ "$listed" = "([('gift-note', 1, 'held')], [], 1)" ] && [ "$(grep -c '"event": "decision.breaker", "task": "gift-note"' "$BR/.lem/state/events.jsonl")" = 1 ]; then
  pass "the breaker stops a task only with its document in every part, the handoff beside it and the work committed; it keeps the document under its number and holds the task with its line, one breaker at a time, and the list of what waits names it once"
else
  fail "the breaker's trip: $nodoc / $bare / $nohandoff / $dirty / $tripped / $twice / $held / $listed"
fi
# The owner parks it: no lead starts, a lead that woke late writes nothing, his help waits for the resume, and the
# list of what waits no longer names it. A task whose lead builds is not parked. His resume brings the breaker's
# block back, and his help settles the breaker; a second help on it is refused.
br task-dir coupon-slug --ask "Give each coupon a slug" >/dev/null && br state coupon-slug building "lead: builder" >/dev/null
building=$(br state coupon-slug parked "the owner parked it" 2>&1 || true)
br state gift-note parked "the owner parked it: wait for the merchants' answer" >/dev/null
started=$(br may-start gift-note 2>&1 || true)
late=$(br state gift-note building "task 3 of 3" 2>&1 || true)
early_help=$(bdecide "$BT" log gift-note --by owner --breaker 1 --what "Where the note goes" --chose "A: a column of its own" --why "readers take columns by place" 2>&1 || true)
parked=$(br waiting | field '(d["breakers"], [(t["task"], t["line"]) for t in d["parked"]], d["count"])')
back=$(br resume gift-note | field '(d["resumed"], d["status"], d["line"], d["breaker"])')
helped=$(bdecide "$BT" log gift-note --by owner --breaker 1 --what "Where the note goes" --chose "A: a column of its own" --why "readers take columns by place" --words "take A, a column" | field '(d["id"], d["by"], d["breaker"], d["words"])')
state=$(bdecide "$BR" list gift-note | field '[(c["id"], c["kind"], c["state"], c.get("help")) for c in d]')
again=$(bdecide "$BT" log gift-note --by owner --breaker 1 --what w --chose c --why y 2>&1 || true)
not_owner=$(status_of bdecide "$BT" log gift-note --by lead --breaker 1 --what w --chose c --why y)
if grep -qF "its lead or its investigator works now, so park it once it stops, or drop it now" <<<"$building" \
  && grep -qF "the task 'gift-note' is parked: it gets no lead until the owner's \`/lem resume gift-note\`" <<<"$started" \
  && grep -qF "the task 'gift-note' is parked: the owner put it aside" <<<"$late" && grep -qF "gift-note is parked: \`lem project resume gift-note\` brings its breaker back first" <<<"$early_help" \
  && [ "$parked" = "([], [('gift-note', \"the owner parked it: wait for the merchants' answer\")], 0)" ] \
  && [ "$back" = "('parked', 'held', 'breaker 1 waits for the owner', 1)" ] && [ "$helped" = "(2, 'owner', 1, 'take A, a column')" ] \
  && [ "$state" = "[(1, 'breaker', 'helped', 2), (2, 'taken', 'taken', None)]" ] && grep -qF "breaker 1 of gift-note is helped already, by decision 2" <<<"$again" && [ "$not_owner" = 1 ]; then
  pass "a parked task gets no lead, takes no late state and waits for nobody; a building one is not parked; resume brings the breaker's block back, his help settles it once, and only his"
else
  fail "the park, the resume and the help: $building / $started / $late / $early_help / $parked / $back / $helped / $state / $again / $not_owner"
fi
# A breaker that trips again, and the owner drops the task: it stays ended, and his resume opens a new task from its
# files and the commits of its branch, which names where it came from; a second resume of the same task is refused.
printf '%s\n' "the second half" >> "$BT/note.txt" && git -C "$BT" commit -q -am "feat: the second half of the note"
breaker_doc "$bd"
bdecide "$BT" breaker gift-note --cause irreversible --irreversible person >/dev/null
br state gift-note dropped "the owner dropped it" >/dev/null
git -C "$BR" worktree remove --force "$BT"
resumed=$(br resume gift-note | field '(d["task"], d["resumed"], d["branch"], d["from_branch"], d["breaker"], d["status"])')
nd=$BR/.lem/state/tasks/gift-note-2
carried=$(git -C "$BR" log -2 --format=%s feat/gift-note-2 | tr '\n' '|')
# a lock is no copied file: each write of the new task's state takes its state.lock
copied=$(cd "$nd" && find . -mindepth 1 -maxdepth 1 ! -name '*.lock' | sed 's|^\./||' | sort | tr '\n' ' ')
first=$(br tasks | field 'next((t["status"], t["state"].splitlines()[0].split(": ", 1)[1], t["state"].splitlines()[1:3]) for t in d if t["slug"] == "gift-note-2")')
old=$(br tasks | field 'next(t["status"] for t in d if t["slug"] == "gift-note")')
record=$(bdecide "$BR" list gift-note-2 | field '[(c["id"], c["kind"], c["state"]) for c in d]')
again=$(br resume gift-note 2>&1 || true)
if [ "$resumed" = "('gift-note-2', 'dropped', 'feat/gift-note-2', 'feat/gift-note', 3, 'held')" ] \
  && [ "$carried" = "feat: the second half of the note|feat: half of the note|" ] \
  && [ "$copied" = "ask.txt breaker-1.md breaker-3.md decisions.jsonl handoff.md reports resumed-from.txt state.md " ] \
  && [ "$first" = "('held', 'breaker 3 waits for the owner', ['resumed from gift-note, which was dropped', 'type: feat, because the export gets a column'])" ] \
  && [ "$old" = dropped ] && [ "$record" = "[(1, 'breaker', 'helped'), (2, 'taken', 'taken'), (3, 'breaker', 'waits')]" ] \
  && grep -qF "the dropped task 'gift-note' goes on in 'gift-note-2' already" <<<"$again"; then
  pass "a dropped task stays dropped, and its resume opens a new task on a branch cut from its commits, with its handoff, each breaker's document and its record, held by the breaker that waits; a second resume of it is refused"
else
  fail "the resume of a dropped task: $resumed / $carried / $copied / $first / $old / $record / $again"
fi
# A resume whose worktree's checks.setup fails still leaves the new task whole, held by its breaker, and says what is left.
printf '%s\n' '[branch]' 'base = "main"' '[checks]' 'setup = ["echo half; exit 3"]' > "$BR/.lem/settings.toml"
br state gift-note-2 dropped "the owner dropped it again" >/dev/null
unset_up=$(br resume gift-note-2 2>&1; echo "exit $?")
whole=$(br tasks | field 'next((t["status"], t["state"].splitlines()[0].split(": ", 1)[1]) for t in d if t["slug"] == "gift-note-3")' 2>&1 || true)
if grep -qF "gift-note-2 goes on in gift-note-3, which is held by its breaker 3" <<<"$unset_up" && grep -qF "\`echo half; exit 3\` of checks.setup failed" <<<"$unset_up" \
  && [ "$(tail -n 1 <<<"$unset_up")" = "exit 1" ] && [ "$whole" = "('held', 'breaker 3 waits for the owner')" ]; then
  pass "a resume whose new worktree's setup fails keeps the new task whole, held by the breaker that waits, and says what is left to do"
else
  fail "a resume with a setup that fails: $unset_up / $whole"
fi
# A task two releases back (lem_release): its open marks it with the release its sessions load, here this Lem's own, since
# Claude Code lists no install in this run (lib.sh). Its first command on a release two later stops with the message of
# criterion 4 and logs the stop once; the list of what waits names it blocked with the message as its line, its status
# stays the one its work wrote, and its drop passes.
project --repo "$DC" task-dir old-release --ask "Keep the old export" >/dev/null
project --repo "$DC" state old-release building "lead: builder" >/dev/null
od=$DC/.lem/state/tasks/old-release
marked=$(cat "$od/release.txt" 2>/dev/null || true)
printf '0.0.1\n' > "$od/release.txt"
version=$("$PY" -c 'import json; print(json.load(open(".claude-plugin/plugin.json"))["version"])')
prior=$("$PY" -B -c 'import sys; sys.path.insert(0, "skills/lem/scripts"); import lem_release; print(lem_release.BEFORE)' 2>/dev/null || true)
say="old-release began on Lem 0.0.1, and Lem $version reads only tasks begun on $prior or $version. Your branch and its commits stay. /lem drop old-release, then /lem resume old-release, starts a new task on $version from that branch and from the notes the task left."
stopped=$("$PY" -B "$CRITERIA" --repo "$DC" approved old-release 2>&1; echo "exit $?")
again=$(status_of "$PY" -B "$CRITERIA" --repo "$DC" approved old-release)
waits=$(project --repo "$DC" waiting | field '[(t["task"], t["line"]) for t in d["blocked"]]')
own=$(project --repo "$DC" tasks | field 'next(t["status"] for t in d if t["slug"] == "old-release")')
ended=$(status_of project --repo "$DC" state old-release dropped "the owner dropped it: it began two releases back")
stops=$(grep -c '"event": "release.stop", "task": "old-release"' "$DC/.lem/state/events.jsonl" || true)
if [ "$marked" = "$version" ] && [ -n "$prior" ] && grep -qxF "criteria.py: $say" <<<"$stopped" && [ "$(tail -n 1 <<<"$stopped")" = "exit 1" ] && [ "$again" = 1 ] \
  && [ "$waits" = "[('old-release', '$say')]" ] && [ "$own" = building ] && [ "$ended" = 0 ] && [ "$stops" = 1 ] \
  && [ "$(project --repo "$DC" tasks | field 'next(t["status"] for t in d if t["slug"] == "old-release")')" = dropped ]; then
  pass "a task two releases back stops at its first command with the message that names its release and the way on, logged once; the list of what waits names it blocked with that message, its status stays its own, and its drop passes"
else
  fail "a task two releases back: $marked / $stopped / $again / $waits / $own / $ended / $stops"
fi
# A task that is dropped or landed has nothing that waits: pending leaves its breakers out and says why, and list still shows them.
for slug in dropped-task landed-task; do breaker_doc "$DC/.lem/state/tasks/$slug" && decide breaker "$slug" --cause irreversible --irreversible person >/dev/null; done
project --repo "$DC" state dropped-task dropped "the owner dropped it" >/dev/null && project --repo "$DC" state landed-task landed "main a..b" >/dev/null
all_open=$(decide pending | field '(d["waiting"], [(e["task"], e["status"], e["breakers"]) for e in d["ended"]])')
one_ended=$(decide pending dropped-task | field '(d["waiting"], d["ended"][0]["status"], d["ended"][0]["says"])')
kept=$(decide list dropped-task | field '[(c["id"], c["state"]) for c in d]')
if [ "$all_open" = "([], [('dropped-task', 'dropped', [1]), ('landed-task', 'landed', [1])])" ] \
  && [ "$one_ended" = "([], 'dropped', 'the task is dropped: its breakers no longer wait for anybody')" ] && [ "$kept" = "[(1, 'waits')]" ]; then
  pass "a dropped or landed task has no breaker that waits: pending leaves it out and says why, and list still shows its record"
else
  fail "the breakers of an ended task: $all_open / $one_ended / $kept"
fi
# Nothing more is decided in a task that ended: a decision, a breaker and his help are refused, with its state, and write nothing.
ended_lines=$(cat "$DC/.lem/state/tasks/dropped-task/decisions.jsonl" "$DC/.lem/state/tasks/landed-task/decisions.jsonl" | grep -c '')
late_log=$(decide log dropped-task --what "The name of the column" --chose gift_note --why "snake case" --by lead 2>&1 || true)
breaker_doc "$DC/.lem/state/tasks/landed-task"
late_breaker=$(decide breaker landed-task --cause criteria 2>&1 || true)
late_help=$(decide log dropped-task --by owner --breaker 1 --what w --chose c --why y 2>&1 || true)
if grep -qF "dropped-task is dropped" <<<"$late_log" && grep -qF "landed-task is landed" <<<"$late_breaker" && grep -qF "dropped-task is dropped" <<<"$late_help" \
  && [ "$(cat "$DC/.lem/state/tasks/dropped-task/decisions.jsonl" "$DC/.lem/state/tasks/landed-task/decisions.jsonl" | grep -c '')" = "$ended_lines" ]; then
  pass "a dropped or landed task takes no new decision, breaker or help: each is refused with the task's state and writes nothing"
else
  fail "a write to an ended task: $late_log / $late_breaker / $late_help"
fi
# Text that is not UTF-8 is refused before anything is written: in an argument, and in the record itself.
lines_before=$(grep -c '' "$DC/.lem/state/tasks/other-task/decisions.jsonl" 2>/dev/null || echo 0)
latin=$(decide log other-task --what $'caf\xe9' --chose a --why b --by lead 2>&1 || true)
cp "$dfile" "$WORK/gift-record.kept" && printf 'caf\351\n' >> "$dfile"
latin_record=$(decide list gift-note 2>&1 || true)
cp "$WORK/gift-record.kept" "$dfile"
if grep -qF "the argument b'caf\\xe9' is not UTF-8 text" <<<"$latin" && [ "$(grep -c '' "$DC/.lem/state/tasks/other-task/decisions.jsonl" 2>/dev/null || echo 0)" = "$lines_before" ] \
  && grep -qF "gift-note/decisions.jsonl is not UTF-8 text" <<<"$latin_record" && ! grep -q Traceback <<<"$latin$latin_record"; then
  pass "an argument that is not UTF-8 text is refused before it is written, and a record that holds such bytes is named"
else
  fail "text that is not UTF-8 in a decision: $latin / $latin_record"
fi
# Two writers never take one number: while another process holds the lock, two writes wait, and then each gets its own.
"$PY" -c 'import fcntl, sys, time; f = open(sys.argv[1], "w"); fcntl.flock(f, fcntl.LOCK_EX); print("held", flush=True); time.sleep(30)' "$DC/.lem/state/tasks/other-task/decisions.lock" > "$WORK/dlock.out" &
holder=$!
soon test -s "$WORK/dlock.out"
"$PY" -B "$DECISIONS" --repo "$DC" log other-task --what "first" --chose a --why b --by lead > "$WORK/dw1.out" 2>&1 &
w1=$!
"$PY" -B "$DECISIONS" --repo "$DC" log other-task --what "second" --chose a --why b --by lead > "$WORK/dw2.out" 2>&1 &
w2=$!
sleep 2
held=$(grep -c '' "$DC/.lem/state/tasks/other-task/decisions.jsonl" 2>/dev/null || true)
kill "$holder" 2>/dev/null || true; wait "$holder" 2>/dev/null || true
wait "$w1" || true; wait "$w2" || true
numbers=$(decide list other-task | field 'sorted(c["id"] for c in d)')
if [ "${held:-0}" = 0 ] && [ "$numbers" = "[1, 2]" ]; then
  pass "two writes while another process holds the lock wait for it, and then each takes a number of its own"
else
  fail "the lock of decisions.jsonl: held $held / $numbers / $(cat "$WORK/dw1.out" "$WORK/dw2.out")"
fi

# The ladder's record: each level that settles logs with its own name; the personas settle with two votes or more, all for
# the option taken, and a split, one vote or a vote for another option is refused and writes nothing.
project --repo "$DC" task-dir ladder-task >/dev/null
lfile=$DC/.lem/state/tasks/ladder-task/decisions.jsonl
ladder() { decide log ladder-task --what "Where the note goes" --option "the last column" --option "after the price" --why "the import reads by place" "$@"; }
voted=$(ladder --chose "the last column" --by personas --vote "the merchant, opus=the last column" --vote "the accountant, opus=the last column" | field '(d["by"], d["votes"], d["options"])')
split=$(ladder --chose "the last column" --by personas --vote "the merchant, opus=the last column" --vote "the accountant, opus=after the price" 2>&1 || true)
alone_vote=$(ladder --chose "the last column" --by personas --vote "the merchant, opus=the last column" 2>&1 || true)
bad_vote=$(status_of ladder --chose "the last column" --by personas --vote "the merchant" --vote "the clerk, opus=the last column")
lines_after_refusals=$(grep -c '' "$lfile")
gate=$(decide log ladder-task --what "The header's name" --chose "Gift note" --by gate --why "docs/rulings.md, Headers: A header says what the cell holds." | field 'd["by"]')
dialectic=$(ladder "${CASE[@]}" --chose "after the price" --by dialectic --level "personas=1 for the last column, 1 for after the price" --level "dialectic=no break" | field '(d["by"], d["levels"])')
unsettled=$(ladder "${CASE[@]}" --chose "the last column" --by lead --unsettled --level "experts=split" | field '(d["by"], d["unsettled"])')
not_lead=$(status_of ladder --chose "the last column" --by experts --unsettled)
if [ "$voted" = "('personas', [['the merchant, opus', 'the last column'], ['the accountant, opus', 'the last column']], ['the last column', 'after the price'])" ] \
  && grep -qF "the accountant, opus voted otherwise" <<<"$split" && grep -qF "this one has 1" <<<"$alone_vote" && [ "$bad_vote" = 1 ] && [ "$lines_after_refusals" = 1 ] \
  && [ "$gate" = gate ] && [ "$dialectic" = "('dialectic', {'personas': '1 for the last column, 1 for after the price', 'dialectic': 'no break'})" ] \
  && [ "$unsettled" = "('lead', True)" ] && [ "$not_lead" = 1 ]; then
  pass "each level of the ladder logs the decision it settles: the personas only with two votes or more, all for the option taken, else nothing is written; the gate, the dialectic and the lead's unsettled pick each with their own name and what each level answered"
else
  fail "the ladder's record: $voted / $split / $alone_vote / $bad_vote / $lines_after_refusals / $gate / $dialectic / $unsettled / $not_lead"
fi

# A lead that finds at its plan that its task needs the result of a task that has not landed queues its own task
# behind it: the state guard takes `queued` with an `after:` line from a task that builds, and refuses it over one
# with its landing; may-start keeps the task in the queue until the other one has ended, and starts it then.
WQ=$WORK/waiting-repo
git init -q -b main "$WQ" && ident "$WQ" && commit "$WQ" start && project --repo "$WQ" init --base main >/dev/null
for slug in caches-the-list shows-the-list in-landing; do project --repo "$WQ" task-dir "$slug" --ask "The ask of $slug." >/dev/null; done
project --repo "$WQ" state caches-the-list building "lead: builder" >/dev/null
project --repo "$WQ" state shows-the-list building "lead: builder" >/dev/null
queued=$(project --repo "$WQ" state shows-the-list queued "it needs the cache of the product list that caches-the-list adds" "after: caches-the-list" | field 'd["status"]' 2>&1 || true)
held_back=$(project --repo "$WQ" may-start shows-the-list 2>&1 || true)
held_code=$(status_of project --repo "$WQ" may-start shows-the-list)
project --repo "$WQ" state in-landing landing "the checks start" >/dev/null
over_landing=$(project --repo "$WQ" state in-landing queued "it needs the cache" "after: caches-the-list" 2>&1 || true)
project --repo "$WQ" state caches-the-list landed "main 1234567..89abcde" >/dev/null
freed=$(project --repo "$WQ" may-start shows-the-list 2>&1 | field 'd["running"]' 2>&1 || true)
project --repo "$WQ" state in-landing dropped "the test is over" >/dev/null
# a task queued after one that was dropped stays queued for the owner's word: the result it waited for never came
project --repo "$WQ" task-dir after-dropped --ask "The ask of after-dropped." >/dev/null && project --repo "$WQ" state after-dropped building "lead: builder" >/dev/null
project --repo "$WQ" state after-dropped queued "it needs what in-landing adds" "after: in-landing" >/dev/null
after_dropped=$(project --repo "$WQ" may-start after-dropped 2>&1 || true)
if [ "$queued" = queued ] && [ "$held_code" = 1 ] \
  && grep -qF "the task 'shows-the-list' is queued after 'caches-the-list', which is building: it starts when caches-the-list is landed or answered" <<<"$held_back" \
  && grep -qF "it is with its landing" <<<"$over_landing" && [ "$(status_in "$WQ" in-landing)" = dropped ] && [ "$freed" = "['in-landing']" ] \
  && grep -qF "queued after 'in-landing', which was dropped, so the result it waited for never came: it stays queued for the owner's word" <<<"$after_dropped"; then
  pass "a lead whose task needs another task's result writes its own task queued after that task; may-start keeps it queued until the other one landed and starts it then, keeps it queued for the owner's word when the other one was dropped, and a task with its landing is never queued"
else
  fail "a lead that queues its task: $queued / $held_back / $over_landing / $freed / $after_dropped"
fi

# A task queued after a dropped task, by a need or by his order, is one row of what waits for the owner, with the two
# words he types in any Lem session; one queued after a task that runs has none. His word ends the row: "start it"
# writes the queued block again without its `after:` line, and /lem drop ends the task.
project --repo "$WQ" task-dir ordered-after --ask "After in-landing: the export keeps the notes in their order." >/dev/null
project --repo "$WQ" state ordered-after queued "the owner's order: \"After in-landing\"" "after: in-landing" "type: feat, because a new order" "then: the interview" >/dev/null
project --repo "$WQ" task-dir still-runs --ask "The ask of still-runs." >/dev/null && project --repo "$WQ" state still-runs building "lead: builder" >/dev/null
project --repo "$WQ" task-dir behind-runs --ask "The ask of behind-runs." >/dev/null
project --repo "$WQ" state behind-runs queued "it needs what still-runs adds" "after: still-runs" >/dev/null
orphans=$(project --repo "$WQ" waiting | field '([(t["task"], t["after"], t["start"], t["drop"]) for t in d["after_dropped"]], [r["key"] for r in d["rows"] if "behind-runs" in r["key"]], d["after_dropped"][0]["where"].replace("“", "<").replace("”", ">"))' 2>&1 || true)
project --repo "$WQ" state after-dropped queued "it needs what in-landing adds" >/dev/null
project --repo "$WQ" state ordered-after dropped "the owner dropped it: /lem drop ordered-after" >/dev/null
project --repo "$WQ" state still-runs dropped "the test is over" >/dev/null && project --repo "$WQ" state behind-runs dropped "the test is over" >/dev/null
answered=$(project --repo "$WQ" waiting | field '(d["after_dropped"], [r["key"] for r in d["rows"] if r["kind"] == "after_dropped"])' 2>&1 || true)
if [ "$orphans" = "([('after-dropped', 'in-landing', 'start after-dropped now', '/lem drop after-dropped'), ('ordered-after', 'in-landing', 'start ordered-after now', '/lem drop ordered-after')], [], 'It waited for in-landing, which was dropped, so the result it waited for never came. Type <start after-dropped now> to start it without that result, or /lem drop after-dropped to end it, in any Lem session of this repository.')" ] \
  && [ "$answered" = "([], [])" ]; then
  pass "a task queued after a dropped task, by a need or by his order, is a row of what waits for the owner with the dropped task, \"start SLUG now\" and /lem drop SLUG, typed in any Lem session; one queued after a task that runs has none; and after his word, either one, the row is gone"
else
  fail "a task queued after a dropped task: $orphans / $answered"
fi

# His "start it" for a task queued behind a dropped task: may-start, run again on his word, prints the commands of his
# word from the task's own block, and each runs as printed through the shell, from the repository, with his words put
# in as the refusal says ('\'' for a single quote of his). The state then keeps his order, its type and its path, says
# that his word removed the order, his word is on record, and the task may start. A need, here one whose first line
# is its `after:` line, gets its block again with no log.
WS=$WORK/start-it-repo
LEMBIN=$PWD/bin
git init -q -b main "$WS" && ident "$WS" && commit "$WS" start && project --repo "$WS" init --base main >/dev/null
for slug in gift-note-in-export export-notes-in-order shows-the-note; do project --repo "$WS" task-dir "$slug" --ask "The ask of $slug." >/dev/null; done
project --repo "$WS" state gift-note-in-export building "lead: builder" >/dev/null
ORDER='the owner'\''s order: "After the "gift note" task"'
REPLY='start it, it'\''s the "gift note" one'
project --repo "$WS" state export-notes-in-order queued "$ORDER" "after: gift-note-in-export" "type: feat, because a new order" "then: the interview" >/dev/null
project --repo "$WS" state shows-the-note queued "after: gift-note-in-export" "it needs the note that gift-note-in-export adds" "then: the lead" >/dev/null
project --repo "$WS" state gift-note-in-export dropped "the owner dropped it" >/dev/null
# start_it TASK: may-start on his word, then each command it printed, as printed, with his words where HIS WORDS stands
start_it() {
  local refusal line
  refusal=$(project --repo "$WS" may-start "$1" 2>&1 || true)
  while IFS= read -r line; do
    (cd "$WS" && PATH="$LEMBIN:$PATH" bash -c "$line") >/dev/null || return 1
  done < <("$PY" -c 'import sys; q = chr(39); [print(r.replace("HIS WORDS", sys.argv[2].replace(q, q + "\\" + q + q))) for r in sys.argv[1].splitlines() if r.startswith("lem ")]' "$refusal" "$REPLY")
  echo "$refusal"
}
ordered=$(start_it export-notes-in-order 2>&1 || true)
needed=$(start_it shows-the-note 2>&1 || true)
# the newest block's lines, its first without the time and the status
newest() { project --repo "$WS" tasks | field "'\n'.join([r.split(': ', 1)[1] if i == 0 else r for i, r in enumerate(next(t['state'] for t in d if t['slug'] == '$1').split('\n'))])"; }
kept=$(newest export-notes-in-order 2>&1 || true)
need_kept=$(newest shows-the-note 2>&1 || true)
his_word=$("$PY" -B "$DECISIONS" --repo "$WS" list export-notes-in-order | field '"\n".join(" | ".join([c["by"], c["what"], c["chose"], c["words"]]) for c in d)' 2>&1 || true)
no_word=$("$PY" -B "$DECISIONS" --repo "$WS" list shows-the-note | field 'len(d)' 2>&1 || true)
may=$(project --repo "$WS" may-start export-notes-in-order 2>&1 | field 'd["running"]' 2>&1 || true)
need_may=$(project --repo "$WS" may-start shows-the-note 2>&1 | field 'd["running"]' 2>&1 || true)
if grep -qF "nothing below runs before it" <<<"$ordered" && grep -qF "lem project may-start export-notes-in-order\` once more" <<<"$ordered" \
  && [ "$kept" = "$(printf '%s\n' "$ORDER" "type: feat, because a new order" "then: the interview" "the owner's order was removed: \"$REPLY\"")" ] \
  && [ "$his_word" = "owner | the owner's order | start now | $REPLY" ] && [ "$may" = "[]" ] \
  && grep -qF "queued after 'gift-note-in-export', which was dropped" <<<"$needed" \
  && [ "$need_kept" = "$(printf '%s\n' "it needs the note that gift-note-in-export adds" "then: the lead")" ] && [ "$no_word" = 0 ] && [ "$need_may" = "[]" ]; then
  pass "his \"start it\" for a task queued behind a dropped task runs the commands may-start prints on his word, as printed through the shell, with a double quote and an apostrophe of his: the state keeps his order, its type and its path and says his word removed the order, his word is on record and the task may start; a need, whose first line is its after: line, gets its block again with no log"
else
  fail "his start of a task behind a dropped task: $ordered / $needed / $kept / $need_kept / $his_word / $no_word / $may / $need_may"
fi

# The one list of what waits for the owner: a breaker, criteria that wait for his yes, a step of his, and a pull
# request with green or not whose merge review calls him. A retro's proposals are not on it and not counted, in the
# record's form or in the old form of the question page: they reach him only as the reviewer's items. An interview whose
# criteria the personas read is not on it until their read is in, and then it is.
wq() { project --repo "$WQ" "$@"; }
for slug in a-breaker his-criteria his-step proposed-one in-read; do wq task-dir "$slug" --ask "The ask of $slug." >/dev/null; done
wq state in-read held "the interview waits for the owner" "type: feat, because the export gets a note" >/dev/null
wq log in-read criteria.read.start by=lem >/dev/null
# a breaker holds its task: the list names it once, under breakers
breaker_doc "$WQ/.lem/state/tasks/a-breaker" && "$PY" -B "$DECISIONS" --repo "$WQ" breaker a-breaker --cause criteria >/dev/null
wq state his-criteria held "the criteria wait for the owner" "type: feat, because the export gets a column" >/dev/null
wq state his-step held "the reviewer's pane waits for the owner's trust of the folder" >/dev/null
wq state proposed-one open "pull request https://github.com/acme/shop/pull/7" "not green: the bar is lower" >/dev/null
printf '%s\n' '{"proposed": "abc1234", "pushed": "abc1234", "forge": {"mergeable": "CONFLICTING", "head": "abc1234"}, "pr": {"number": 7, "url": "https://github.com/acme/shop/pull/7"}, "not_green": ["the bar is lower"], "merge_review": {"tip": "abc1234", "verdict": "call", "calls": true, "why": "Verdict: call. It is not green."}}' > "$WQ/.lem/state/tasks/proposed-one/landing.json"
printf '%s\n' '{"read": "the tasks since the retro before", "proposals": [{"area": "lessons", "move": "Move the rule", "body": "It came back twice.", "source": "the task a-breaker", "where": ".lem/lessons.md"}]}' > "$WORK/retro-run.json"
wq proposals add --kind retro --date 2026-11-18 --file "$WORK/retro-run.json" >/dev/null
printf '%s\n' '{"title": "The retro of 2026-11-17", "questions": [{"id": "p1", "prompt": "Move the rule?", "options": ["approve", "reject", "later"]}, {"id": "p2", "prompt": "Drop the step?", "options": ["approve", "reject", "later"]}]}' > "$WQ/.lem/state/retros/2026-11-17.json"
listed=$(wq waiting)
# the drop of a path that is no reviewer's item is refused with exit 1, and its JSON on stdout names no task that holds it
drop_code=0
drop_said=$(wq proposals drop docs/backlog/refund-total-zero.md 2>/dev/null) || drop_code=$?
seen=$( (cat "$XDG_CONFIG_HOME/lem/owner.jsonl" 2>/dev/null || true) | grep -c '' || true)
wq owner away --words "I'm away" >/dev/null
away_list=$(wq waiting | field '(d["owner"]["away"], d["owner"]["words"], d["owner"]["since"] is not None, [b["task"] for b in d["breakers"]], d["count"])' 2>&1 || true)
wq owner back --words "/lem im-back" >/dev/null
wq log in-read criteria.read by=lem asked:=2 answered:=2 families:='["opus"]' silent:='[]' criteria:=1 flagged:=0 split:=false digest=0123456789ab >/dev/null
read_in=$(wq waiting | field '([t["task"] for t in d["held"]], d["count"])' 2>&1 || true)
wq state in-read dropped "the test is over" >/dev/null
shape=$(field '([(c["task"], c["id"]) for c in d["breakers"]], [(t["task"], t["line"]) for t in d["criteria"]], [(t["task"], t["line"]) for t in d["held"]], [(t["task"], t["pull_request"], t["green"], t["not_green"], t["conflict"]) for t in d["pull_requests"]], "retros" in d, d["count"])' <<<"$listed" 2>&1 || true)
if [ "$shape" = "([('a-breaker', 1)], [('his-criteria', 'the criteria wait for the owner')], [('his-step', \"the reviewer's pane waits for the owner's trust of the folder\")], [('proposed-one', 'https://github.com/acme/shop/pull/7', False, ['the bar is lower'], True)], False, 4)" ] \
  && [ "$(field '(d["owner"]["away"], d["owner"]["seen"])' <<<"$listed")" = "(False, $seen)" ] && [ "$(field 'd["pull_requests"][0]["ask"]' <<<"$listed")" = "The ask of proposed-one." ] \
  && [ "$drop_code" = 1 ] && [ "$(field '(d["dropped"], d["held_by"])' <<<"$drop_said")" = "(False, None)" ] \
  && [ "$away_list" = "(True, \"I'm away\", True, ['a-breaker'], 3)" ] && [ "$read_in" = "(['in-read', 'his-step'], 5)" ]; then
  pass "waiting lists in one JSON what waits for the owner: whether he is away, each breaker as decisions.py pending gives it, once though it holds its task, the criteria and the steps that hold a task, and each pull request with green or not and whether the forge calls it conflicting, and neither lists nor counts a retro's proposals, in the record's form or the question page's; while he is away it says so first, since when and in his words, criteria that wait for his yes go on without him, and the breaker still waits for him; an interview whose criteria the personas read is neither listed nor counted until their read is in"
else
  fail "waiting: $shape / $drop_code / $drop_said / $away_list / $read_in / $listed"
fi

# A night's task is told from a day's task by the night's mark, and the night's brake counts its pull requests that
# nobody merged or closed: two here, beside a day's request, one the night opened that merged and one whose request
# was closed. A night's task runs without the owner until it ends, also after he went away and came back; a night that
# is no date is refused.
for slug in night-small night-full night-merged night-closed; do
  wq task-dir "$slug" --ask "The backlog item of $slug." --night 2026-11-18 >/dev/null
done
night_mode=$(wq tasks | field '[t["mode"] for t in d if t["slug"] == "night-small"][0]')
wq state night-small open "pull request https://github.com/acme/shop/pull/8" "green" >/dev/null
printf '%s\n' '{"proposed": "def5678", "pr": {"number": 8, "url": "https://github.com/acme/shop/pull/8"}, "not_green": [], "merge_review": {"tip": "def5678", "verdict": "call", "calls": true, "why": "Verdict: call. It is careful."}}' > "$WQ/.lem/state/tasks/night-small/landing.json"
wq state night-full open "pull request https://github.com/acme/shop/pull/9" "not green: the owner did not approve the criteria" >/dev/null
printf '%s\n' '{"proposed": "0a1b2c3", "pr": {"number": 9, "url": "https://github.com/acme/shop/pull/9"}, "not_green": ["the owner did not approve the criteria"], "merge_review": {"tip": "0a1b2c3", "verdict": "call", "calls": true, "why": "Verdict: call. It is not green."}}' > "$WQ/.lem/state/tasks/night-full/landing.json"
wq owner away --words "I'm away" >/dev/null && wq owner back --words "/lem im-back" >/dev/null
back_again=$(wq owner back --words "/lem im-back" | field '(d["written"], d["tasks"])' 2>&1 || true)
wq state night-merged landed "main 1234567..89abcde" >/dev/null
wq state night-closed dropped "the pull request was closed on the forge" >/dev/null
other_form=$(wq task-dir night-other --ask "The backlog item of night-other." --night "the night run" 2>&1 || true)
nightly=$(wq waiting | field '([(t["task"], t["green"], t["night"]) for t in d["pull_requests"]], sum(1 for t in d["pull_requests"] if t["night"]))' 2>&1 || true)
marked=$(wq tasks | field '[(t["slug"], t["night"]) for t in d if t["slug"].startswith("night-") or t["slug"] == "proposed-one"]' 2>&1 || true)
if [ "$nightly" = "([('proposed-one', False, None), ('night-small', True, '2026-11-18'), ('night-full', False, '2026-11-18')], 2)" ] \
  && [ "$marked" = "[('night-closed', '2026-11-18'), ('night-full', '2026-11-18'), ('night-merged', '2026-11-18'), ('night-small', '2026-11-18'), ('proposed-one', None)]" ] \
  && grep -qF -- "--night is the night's date, YYYY-MM-DD, not 'the night run'" <<<"$other_form" && [ "$night_mode" = alone ] \
  && [ "$(wq tasks | field '[t["mode"] for t in d if t["slug"] == "night-small"][0]')" = alone ] && [ "$back_again" = "(False, [])" ]; then
  pass "a task the night opened runs without the owner and carries the night's date in tasks and in waiting, also after he went away and said he is back, and a second back writes nothing and names no task as come back; the brake counts the night's pull requests that nobody merged or closed; and a night that is no date is refused"
else
  fail "the night's pull requests: $nightly / $marked / $other_form / $night_mode / $back_again"
fi

# The morning: a task the night left held for the owner is marked with its night beside a day's, the night's pull
# requests are among the others, and the list names last night's report, today's or yesterday's, never an older one.
wq task-dir night-held --ask "The backlog item of night-held." --night 2026-11-18 >/dev/null
wq state night-held held "the reviewer's pane waits for the owner's trust of the folder" >/dev/null
no_report=$(wq waiting | field 'd["night_report"]' 2>&1 || true)
mkdir -p "$WQ/.lem/state/night"
printf '%s\n' '# The night of 2026-01-01' > "$WQ/.lem/state/night/2026-01-01.md"
before=$(wq waiting | field 'd["night_report"]' 2>&1 || true)
last_night=$WQ/.lem/state/night/$(date +%F).md
printf '%s\n' '# The night' '- night-small: pull request 8, green' '- night-full: pull request 9, not green' '- night-held: the reviewer pane waits for the owner' > "$last_night"
morning=$(wq waiting | field '([(t["task"], t["night"]) for t in d["held"]], [(t["task"], t["night"]) for t in d["pull_requests"]], d["night_report"]["file"])' 2>&1 || true)
if [ "$no_report" = None ] && [ "$before" = None ] \
  && [ "$morning" = "([('his-step', None), ('night-held', '2026-11-18')], [('proposed-one', None), ('night-small', '2026-11-18'), ('night-full', '2026-11-18')], '$last_night')" ]; then
  pass "in the morning the list marks a task the night held and the night's pull requests with the night, beside a day's, and names last night's report and no older one"
else
  fail "the morning: $no_report / $before / $morning"
fi


# The owner's status is the machine's, and it changes nothing in a build: a task the night opened in another repository
# runs without him after his back here too. An approval of criteria without him reads his status again under its lock:
# here he comes back in the first repository while the approval of the second waits for the lock, and it is refused.
D2=$WORK/second-repo
git init -q -b main "$D2" && commit "$D2" start && project --repo "$D2" init --base main >/dev/null
project --repo "$DC" owner away --words "/lem im-away" >/dev/null
project --repo "$D2" task-dir night-dates --ask "The backlog item of night-dates." --night 2026-11-19 >/dev/null
project --repo "$D2" task-dir report-dates >/dev/null && project --repo "$D2" state report-dates building "lead: builder" >/dev/null
project --repo "$DC" owner back --words "/lem im-back" >/dev/null
night_mode=$(project --repo "$D2" tasks | field '[(t["slug"], t["mode"]) for t in d if t["slug"] in ("night-dates", "report-dates")]')
project --repo "$D2" task-dir late-approve >/dev/null && project --repo "$D2" state late-approve building "lead: builder" >/dev/null
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the report gets a new column.' '' '1. The report shows each date as 2026-11-19.' > "$WORK/late-approve.md"
project --repo "$DC" owner away --words "I'm away" >/dev/null
"$PY" -c 'import fcntl, sys, time; f = open(sys.argv[1], "w"); fcntl.flock(f, fcntl.LOCK_EX); print("held", flush=True); time.sleep(30)' "$D2/.lem/state/tasks/late-approve/criteria.lock" > "$WORK/alock.out" &
holder=$!
soon test -s "$WORK/alock.out"
"$PY" -B "$CRITERIA" --repo "$D2" approve late-approve --file "$WORK/late-approve.md" --alone > "$WORK/late-approve.out" 2>&1 &
approver=$!
# at_lock PID: the approval PID has the lock's file open, which it opens only to wait for the lock: a sign in place of a
# second of waiting, so that a late start of the approval cannot read his back before it reaches the lock
at_lock() { lsof -t "$D2/.lem/state/tasks/late-approve/criteria.lock" 2>/dev/null | grep -qx "$1"; }
soon at_lock "$approver"
at_lock "$approver" && waited=yes || waited=no
project --repo "$DC" owner back --words "I'm back" >/dev/null
kill "$holder" 2>/dev/null || true; wait "$holder" 2>/dev/null || true
wait "$approver" || true
if [ "$night_mode" = "[('night-dates', 'alone'), ('report-dates', 'with-owner')]" ] && [ "$waited" = yes ] \
  && grep -qF "late-approve runs with the owner" "$WORK/late-approve.out" && [ ! -e "$D2/.lem/state/tasks/late-approve/criteria.json" ]; then
  pass "his back in one repository leaves a task the night opened in another without him; an approval without him that waited for its lock while he came back is refused"
else
  fail "the owner's status across two repositories: $night_mode / at the lock: $waited / $(cat "$WORK/late-approve.out")"
fi

# A resumed task keeps the owner's approvals. One task's read flagged a criterion and he approved the criteria after it;
# another's read he skipped by his word, and approved after it. A breaker stops each, he drops it and resumes it, helps
# the breaker of the new task, and the new task is proposed with no second question to him.
RS=$WORK/resume-repo
git init -q -b main "$RS" && ident "$RS" && project --repo "$RS" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[checks]' 'commands = ["true"]' > "$RS/.lem/settings.toml"
git -C "$RS" add -A && git -C "$RS" commit -q -m "chore: start" && on_github "$RS"
rs_criteria() { printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the ticket names the word and the file.' '' '1. The file holds the word the owner asked for.' > "$WORK/$1-approved.md"; }
# rs_resume SLUG: a breaker stops the task, the owner drops it and resumes it, helps the new task's breaker, and the new
# task lands as far as its proposal; prints what the proposal said
rs_resume() {
  local dir=$RS/.lem/state/tasks/$1 new number
  project --repo "$RS" state "$1" building "lead: builder" >/dev/null
  breaker_doc "$dir" && number=$("$PY" -B "$DECISIONS" --repo "$RS" breaker "$1" --cause criteria | field 'd["id"]')
  project --repo "$RS" state "$1" dropped "the owner dropped it" >/dev/null
  new=$(project --repo "$RS" resume "$1" | field 'd["task"]')
  "$PY" -B "$DECISIONS" --repo "$RS" log "$new" --by owner --breaker "$number" --what "Where the word goes" --chose "the first line" --why "a reader sees it at once" >/dev/null
  project --repo "$RS" state "$new" ready "the report is written" >/dev/null
  land --repo "$RS" start "$new" >/dev/null && land --repo "$RS" base "$new" >/dev/null && polish_in "$RS" "$new" && land --repo "$RS" checks "$new" >/dev/null \
    && land --repo "$RS" read "$new" --record "$(clean "$new" 1)" >/dev/null && land --repo "$RS" propose "$new" --title "fix: $new" --notes "$NOTES" 2>&1
}
task_in "$RS" flagged-word f.txt f
rs_criteria flagged-word
flag_digest=$("$PY" -B "$CRITERIA" --repo "$RS" digest flagged-word | field 'd["digest"]')
project --repo "$RS" log flagged-word criteria.read by=lem asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=1 split:=false "digest=$flag_digest" >/dev/null
"$PY" -B "$CRITERIA" --repo "$RS" approve flagged-word --file "$WORK/flagged-word-approved.md" >/dev/null
# the read and his approval a day before the resume, as their times in the log and in criteria.json say
"$PY" -c '
import json, sys
log, kept = sys.argv[1], sys.argv[2]
day = {"criteria.read": "2026-11-20T10:00:00Z", "criteria.approved": "2026-11-20T10:05:00Z"}
rows = [json.loads(line) for line in open(log)]
rows = [{**r, "ts": day[r["event"]]} if r.get("task") == "flagged-word" and r.get("event") in day else r for r in rows]
open(log, "w").write("".join(json.dumps(r) + "\n" for r in rows))
record = json.load(open(kept))
record["at"] = day["criteria.approved"]
json.dump(record, open(kept, "w"))
' "$RS/.lem/state/events.jsonl" "$RS/.lem/state/tasks/flagged-word/criteria.json"
flagged=$(rs_resume flagged-word || true)
task_in "$RS" skipped-word s.txt s
rs_criteria skipped-word
"$PY" -B "$DECISIONS" --repo "$RS" log skipped-word --by owner --what "the personas' read of the criteria" --chose "no read: the criteria name only the developer" --why "the criteria name only the developer" >/dev/null
"$PY" -B "$CRITERIA" --repo "$RS" approve skipped-word --file "$WORK/skipped-word-approved.md" >/dev/null
skipped=$(rs_resume skipped-word || true)
copied=$("$PY" -c 'import json, sys; rows = [json.loads(line) for line in open(sys.argv[1]) if json.loads(line).get("task") == "skipped-word-2"]; print([(r["event"], "was_at" in r) for r in rows[:2]])' "$RS/.lem/state/events.jsonl")
if [ "$(field '(d["task"], d["pull_request"]["number"])' <<<"$flagged" 2>/dev/null)" = "('flagged-word-2', 1)" ] \
  && [ "$(field '(d["task"], d["pull_request"]["number"])' <<<"$skipped" 2>/dev/null)" = "('skipped-word-2', 2)" ] \
  && [ "$copied" = "[('decision.taken', True), ('criteria.approved', True)]" ] && [ "$(status_in "$RS" skipped-word-2)" = open ]; then
  pass "a resumed task keeps the owner's approval after a read that flagged a criterion, and after his word to skip the read: each copied event keeps its time and its order, and the new task is proposed with no second question"
else
  fail "the proposal of a resumed task: $flagged / $skipped / $copied"
fi

finish
