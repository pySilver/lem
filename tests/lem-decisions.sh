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
carried=$(git -C "$BR" log --format=%s feat/gift-note-2 | head -2 | tr '\n' '|')
copied=$(cd "$nd" && printf '%s ' *)
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
printf '%s\n' '[branch]' 'base = "main"' '[checks]' 'setup = ["echo half; exit 3"]' > "$BR/.lem/project.toml"
br state gift-note-2 dropped "the owner dropped it again" >/dev/null
unset_up=$(br resume gift-note-2 2>&1; echo "exit $?")
whole=$(br tasks | field 'next((t["status"], t["state"].splitlines()[0].split(": ", 1)[1]) for t in d if t["slug"] == "gift-note-3")' 2>&1 || true)
if grep -qF "gift-note-2 goes on in gift-note-3, which is held by its breaker 3" <<<"$unset_up" && grep -qF "\`echo half; exit 3\` of checks.setup failed" <<<"$unset_up" \
  && [ "$(tail -n 1 <<<"$unset_up")" = "exit 1" ] && [ "$whole" = "('held', 'breaker 3 waits for the owner')" ]; then
  pass "a resume whose new worktree's setup fails keeps the new task whole, held by the breaker that waits, and says what is left to do"
else
  fail "a resume with a setup that fails: $unset_up / $whole"
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
gate=$(decide log ladder-task --what "The header's name" --chose "Gift note" --by gate --why "docs/rulings/headers.md: a header says what the cell holds" | field 'd["by"]')
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
if [ "$queued" = queued ] && [ "$held_code" = 1 ] \
  && grep -qF "the task 'shows-the-list' is queued after 'caches-the-list', which is building: it starts when caches-the-list is landed, answered or dropped" <<<"$held_back" \
  && grep -qF "it is with its landing" <<<"$over_landing" && [ "$(status_in "$WQ" in-landing)" = dropped ] && [ "$freed" = "['in-landing']" ]; then
  pass "a lead whose task needs another task's result writes its own task queued after that task; may-start keeps it queued until the other one ended and starts it then, and a task with its landing is never queued"
else
  fail "a lead that queues its task: $queued / $held_back / $over_landing / $freed"
fi

# The one list of what waits for the owner: a breaker, criteria that wait for his yes, a step of his, a pull
# request with green or not whose merge review calls him, and a retro's proposals.
wq() { project --repo "$WQ" "$@"; }
for slug in a-breaker his-criteria his-step proposed-one; do wq task-dir "$slug" --ask "The ask of $slug." >/dev/null; done
# a breaker holds its task: the list names it once, under breakers
breaker_doc "$WQ/.lem/state/tasks/a-breaker" && "$PY" -B "$DECISIONS" --repo "$WQ" breaker a-breaker --cause criteria >/dev/null
wq state his-criteria held "the criteria wait for the owner" "type: feat, because the export gets a column" >/dev/null
wq state his-step held "the reviewer's pane waits for the owner's trust of the folder" >/dev/null
wq state proposed-one open "pull request https://github.com/acme/shop/pull/7" "not green: the bar is lower" >/dev/null
printf '%s\n' '{"proposed": "abc1234", "pushed": "abc1234", "forge": {"mergeable": "CONFLICTING", "head": "abc1234"}, "pr": {"number": 7, "url": "https://github.com/acme/shop/pull/7"}, "not_green": ["the bar is lower"], "merge_review": {"tip": "abc1234", "verdict": "call", "calls": true, "why": "Verdict: call. It is not green."}}' > "$WQ/.lem/state/tasks/proposed-one/landing.json"
mkdir -p "$WQ/.lem/state/retros"
printf '%s\n' '{"title": "The retro of 2026-11-17", "questions": [{"id": "p1", "prompt": "Move the rule?", "options": ["approve", "reject", "later"]}, {"id": "p2", "prompt": "Drop the step?", "options": ["approve", "reject", "later"]}]}' > "$WQ/.lem/state/retros/2026-11-17.json"
printf '%s\n' 'not json' > "$WQ/.lem/state/retros/2026-11-18.json"
listed=$(wq waiting)
seen=$( (cat "$XDG_CONFIG_HOME/lem/owner.jsonl" 2>/dev/null || true) | grep -c '' || true)
wq owner away --words "I'm away" >/dev/null
away_list=$(wq waiting | field '(d["owner"]["away"], d["owner"]["words"], d["owner"]["since"] is not None, [b["task"] for b in d["breakers"]], d["count"])' 2>&1 || true)
wq owner back --words "/lem im-back" >/dev/null
shape=$(field '([(c["task"], c["id"]) for c in d["breakers"]], [(t["task"], t["line"]) for t in d["criteria"]], [(t["task"], t["line"]) for t in d["held"]], [(t["task"], t["pull_request"], t["green"], t["not_green"], t["conflict"]) for t in d["pull_requests"]], [(r["date"], r["proposals"], "problem" in r) for r in d["retros"]], d["count"])' <<<"$listed" 2>&1 || true)
if [ "$shape" = "([('a-breaker', 1)], [('his-criteria', 'the criteria wait for the owner')], [('his-step', \"the reviewer's pane waits for the owner's trust of the folder\")], [('proposed-one', 'https://github.com/acme/shop/pull/7', False, ['the bar is lower'], True)], [('2026-11-17', 2, False), ('2026-11-18', None, True)], 7)" ] \
  && [ "$(field '(d["owner"]["away"], d["owner"]["seen"])' <<<"$listed")" = "(False, $seen)" ] && [ "$(field 'd["pull_requests"][0]["ask"]' <<<"$listed")" = "The ask of proposed-one." ] \
  && [ "$away_list" = "(True, \"I'm away\", True, ['a-breaker'], 7)" ]; then
  pass "waiting lists in one JSON what waits for the owner: whether he is away, each breaker as decisions.py pending gives it, once though it holds its task, the criteria and the steps that hold a task, each pull request with green or not and whether the forge calls it conflicting, and each retro's proposals, with a file that does not read named as such; while he is away it says so first, since when and in his words, and the breaker still waits for him"
else
  fail "waiting: $shape / $away_list / $listed"
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
if [ "$nightly" = "([('night-full', False, '2026-11-18'), ('night-small', True, '2026-11-18'), ('proposed-one', False, None)], 2)" ] \
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
  && [ "$morning" = "([('his-step', None), ('night-held', '2026-11-18')], [('night-full', '2026-11-18'), ('night-small', '2026-11-18'), ('proposed-one', None)], '$last_night')" ]; then
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

finish
