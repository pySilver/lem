#!/usr/bin/env bash
# The decisions of a task: each one the lead or the personas took, and each choice that waits for the
# owner's answer with no time limit while he is there, and is taken at once when he says he is away, except a
# step that a later "no" cannot reverse.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

DC=$WORK/decisions-repo
git init -q -b main "$DC" && commit "$DC" start && project --repo "$DC" init --base main >/dev/null
project --repo "$DC" task-dir gift-note >/dev/null && project --repo "$DC" task-dir other-task >/dev/null && project --repo "$DC" task-dir race-task >/dev/null
project --repo "$DC" task-dir dropped-task >/dev/null && project --repo "$DC" task-dir landed-task >/dev/null && project --repo "$DC" task-dir cancel-task >/dev/null
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
one=$(decide ask gift-note "${CASE[@]}" --what "Which note wins" --option "the first" --recommended "the first" --why w --said s 2>&1 || true)
notone=$(decide ask gift-note "${CASE[@]}" --what "Which note wins" --option "the first" --option "the last" --recommended "the newest" --why w --said s 2>&1 || true)
asked=$(decide ask gift-note "${CASE[@]}" --what "Where the note goes in the row" --option "the last column" --option "after the price" --recommended "the last column" \
  --why "an import that reads the columns by place keeps working" --said "The merchant picked the last column, the accountant after the price.")
forever=$(decide ask gift-note "${CASE[@]}" --what "Send the merchants an email about the new column" --option "send it" --option "do not send it" --recommended "do not send it" \
  --why "the column is visible in the export" --said "The merchant wants the email, the accountant does not." --irreversible person)
waits=$(decide pending gift-note)
everywhere=$(decide pending | field '([(c["task"], c["id"]) for c in d["waiting"]], d["ended"])')
if grep -q "a choice has two options or more" <<<"$one" && grep -qF -- "--recommended is one of the options, word for word: the first; the last" <<<"$notone" \
  && [ "$(field '(d["id"], "deadline" in d, "wait_minutes" in d, "tell Lem that choice 3 of gift-note waits" in d["next"])' <<<"$asked")" = "(3, False, False, True)" ] \
  && [ "$(field '(d["id"], d["irreversible"], "however long" in d["next"], "tell Lem that choice 4 of gift-note waits" in d["next"])' <<<"$forever")" = "(4, 'person', True, True)" ] \
  && [ "$(field '[(c["id"], c["state"], "seconds_left" in c) for c in d["waiting"]]' <<<"$waits")" = "[(3, 'waits', False), (4, 'waits', False)]" ] \
  && [ "$everywhere" = "([('gift-note', 3), ('gift-note', 4)], [])" ] && [ "$(grep -c '"event": "decision.asked", "task": "gift-note"' "$DC/.lem/state/events.jsonl")" = 2 ]; then
  pass "a choice for the owner has two options or more and recommends one of them; it has no time limit, and pending lists each choice that waits"
else
  fail "decisions.py ask and pending: $one / $notone / $asked / $forever / $waits / $everywhere"
fi
# A choice for the owner tells him one run above his card: the case in numbered steps, how it is known,
# and its cause.
two_options=(--option "the first" --option "the last" --recommended "the first" --why w --said s)
nocase=$(decide ask gift-note --what "Which note wins" "${two_options[@]}" 2>&1 || true)
onestep=$(decide ask gift-note --what "Which note wins" --case "1. Two notes come in for order 1042." --case-was derived --cause c "${two_options[@]}" 2>&1 || true)
unknown=$(decide ask gift-note --what "Which note wins" --case $'1. a\n2. b' --case-was guessed --cause c "${two_options[@]}" 2>&1 || true)
nocause=$(decide ask gift-note --what "Which note wins" --case $'1. a\n2. b' --case-was derived "${two_options[@]}" 2>&1 || true)
choice3() { decide pending gift-note | "$PY" -c 'import json, sys; print(next(c for c in json.load(sys.stdin)["waiting"] if c["id"] == 3)[sys.argv[1]])' "$1"; }
if grep -qF -- "--case is one concrete case that ends badly, in numbered steps, one to a line" <<<"$nocase" && grep -qF "this one has 0 numbered steps" <<<"$nocase" \
  && grep -qF "this one has 1 numbered step" <<<"$onestep" && grep -qF -- "--case-was says how the case is known: reproduced or derived" <<<"$unknown" \
  && grep -qF -- "--cause needs its text" <<<"$nocause" \
  && [ "$(choice3 case)" = "${CASE[1]}" ] && [ "$(choice3 case_was)" = derived ] && [ "$(choice3 cause)" = "${CASE[5]}" ] \
  && [ "$(grep -c '"event": "decision.asked", "task": "gift-note"' "$DC/.lem/state/events.jsonl")" = 2 ]; then
  pass "a choice for the owner carries one run above his card: its case in two numbered steps or more, kept line by line, whether it was reproduced or derived, and its cause; a choice without them is refused"
else
  fail "the run of a choice: $nocase / $onestep / $unknown / $nocause / $(choice3 case)"
fi
# While the owner is there a choice waits past any time. When he says he is away, each choice that waits is taken at
# once with the ladder's pick, but a step a later "no" cannot reverse; his answer after it is late, and after he is back
# again the next choice waits again.
still=$(decide wait gift-note 3 --seconds 1 | field '(d["ended"], d["state"])')
away=$(project --repo "$DC" owner away --words "I'm away" | field '(d["written"], [(t["task"], t["id"], t["chose"]) for t in d["taken"]])')
taken=$(dlist 'next((c["state"], c["chose"], c.get("early")) for c in d if c["id"] == 3)')
never=$(dlist 'next(c["state"] for c in d if c["id"] == 4)')
project --repo "$DC" owner back --words "/lem im-back" >/dev/null
same=$(decide answer gift-note 3 --chose "the last column" | field '(d["kind"], d["taken"], d["next"])')
if [ "$still" = "('still waits', 'waits')" ] \
  && [ "$away" = "(True, [('gift-note', 3, 'the last column')])" ] && [ "$taken" = "('timeout', 'the last column', True)" ] && [ "$never" = waits ] \
  && [ "$same" = "('late', 'the last column', 'the answer is the action that was taken: nothing more to do')" ]; then
  pass "a choice waits past any time while the owner is there; his away takes each choice that waits at once with the recommended option, never an irreversible step, and a late answer that is the same needs nothing more"
else
  fail "a choice and the owner's status: $still / $away / $taken / $never / $same"
fi
decide ask gift-note "${CASE[@]}" --what "The header of the column" --option "Gift note" --option "Note" --recommended "Gift note" --why "it says what the cell holds" --said "The two personas split." >/dev/null
project --repo "$DC" owner away --words "I'm away" >/dev/null && project --repo "$DC" owner back --words "/lem im-back" >/dev/null
differs=$(decide answer gift-note 5 --chose "Note" | field '(d["kind"], d["taken"], "it is a correction" in d["next"])')
decide ask gift-note "${CASE[@]}" --what "The note's length" --option "all of it" --option "200 characters" --recommended "all of it" --why "nothing is lost" --said "The two personas split." >/dev/null
answered=$(decide answer gift-note 6 --chose "200 characters" | field '(d["kind"], d["chose"])')
started=$(date +%s)
ended=$(decide wait gift-note 6 --seconds 30 | field '(d["ended"], d["chose"], d["by"])')
took=$(( $(date +%s) - started ))
twice=$(decide answer gift-note 6 --chose "all of it" 2>&1 || true)
unknown=$(decide answer gift-note 1 --chose x 2>&1 || true)
stands=$(dlist '[(c["id"], c["state"], c.get("chose"), c.get("by"), c.get("late", {}).get("chose")) for c in d]')
if [ "$differs" = "('late', 'Gift note', True)" ] && [ "$answered" = "('answered', '200 characters')" ] && [ "$ended" = "('answered', '200 characters', 'owner')" ] && [ "$took" -lt 30 ] \
  && grep -q "choice 6 has the owner's answer already: '200 characters'" <<<"$twice" && grep -q "no choice 1 went to the owner in gift-note; those that did: 3, 4, 5, 6" <<<"$unknown" \
  && [ "$stands" = "[(1, 'taken', 'gift_note', 'lead', None), (2, 'taken', 'both notes, with a semicolon between them', 'personas', None), (3, 'timeout', 'the last column', 'timeout', 'the last column'), (4, 'waits', None, None, None), (5, 'timeout', 'Gift note', 'timeout', 'Note'), (6, 'answered', '200 characters', 'owner', None)]" ]; then
  pass "an answer in time decides and wait returns at once with it; a late answer that differs is a correction; a second answer and an answer to a decision nobody asked are refused; and list shows each decision as it stands"
else
  fail "decisions.py answer, wait and list: $differs / $answered / $ended / $took / $twice / $unknown / $stands"
fi
decide ask gift-note "${CASE[@]}" --what "The note's font" --option "plain" --option "bold" --recommended "plain" --why "The export has no fonts." --said "The two personas split." >/dev/null
decide answer gift-note 7 --chose "bold" --why "Merchants miss it otherwise." >/dev/null
# A choice carries no criterion: the options are only its own, and a criterion it changes gets a record of its own after it.
carried=$(status_of decide ask gift-note "${CASE[@]}" --what w --option a --option b --recommended a --why w --said s --criterion 1 --was "the old text" --changes b)
decide ask gift-note "${CASE[@]}" --what "The note in the header" --option "no header" --option "a header" --recommended "no header" --why "The rows stay as they are." --said "The two personas split." >/dev/null
decide ask gift-note "${CASE[@]}" --what "The note in the footer" --option "no footer" --option "a footer" --recommended "no footer" --why "The rows stay as they are." --said "The two personas split." >/dev/null
decide answer gift-note 8 --chose "a header" >/dev/null && decide answer gift-note 9 --chose "no footer" >/dev/null
told=$(dlist '[(c["id"], c["state"], "criterion" in c) for c in d if c["id"] in (8, 9)]')
emptyundo=$(status_of decide log gift-note --what x --chose y --why z --by lead --undo " ")
if [ "$carried" = 2 ] && [ "$told" = "[(8, 'answered', False), (9, 'answered', False)]" ] && [ "$emptyundo" = 1 ] && [ "$(dlist 'len(d)')" = 9 ]; then
  pass "a choice carries no criterion, and its answer changes none by itself; an empty --undo is refused before anything is written"
else
  fail "a choice and a criterion, and empty values: $carried / $told / $emptyundo"
fi
# An answer takes one of the options, word for word, and keeps the owner's own words beside it.
decide ask gift-note "${CASE[@]}" --what "The note in the summary" --option "no summary" --option "a summary line" --recommended "no summary" --why "The rows stay as they are." --said "The two personas split." >/dev/null
free=$(decide answer gift-note 10 --chose "Put a line at the bottom, please." 2>&1 || true)
freecode=$(status_of decide answer gift-note 10 --chose "Put a line at the bottom, please.")
still=$(dlist 'next(c["state"] for c in d if c["id"] == 10)')
mapped=$(decide answer gift-note 10 --chose "a summary line" --words "Put a line at the bottom, please." | field '(d["kind"], d["chose"], d["words"])')
ten=$(dlist 'next((c["state"], c["chose"], c.get("owner_words")) for c in d if c["id"] == 10)')
if grep -qF "the answer to choice 10 is one of its options, word for word: no summary; a summary line" <<<"$free" && grep -qF -- "--words" <<<"$free" \
  && grep -qF -- "fits none of them, settle the choice with --instead TEXT, never with a new \`lem decisions log\`" <<<"$free" && [ "$freecode" = 1 ] && [ "$still" = waits ] \
  && [ "$mapped" = "('answered', 'a summary line', 'Put a line at the bottom, please.')" ] && [ "$ten" = "('answered', 'a summary line', 'Put a line at the bottom, please.')" ]; then
  pass "an answer names one of the choice's options word for word, and his own words go beside it; an answer that fits no option is refused and writes nothing"
else
  fail "an answer and the owner's words: $free / $freecode / $still / $mapped / $ten"
fi
# A decision of the owner's that is none of the options settles the choice with --instead; a criterion the choice carries is said changed or kept, never left out.
decide ask gift-note "${CASE[@]}" --what "Email the merchants" --option "email all customers" --option "email nobody" --recommended "email nobody" --why "Nobody asked for it." --said "The two personas split." --irreversible person >/dev/null
both=$(decide answer gift-note 11 --chose "email nobody" --instead "Email only the beta testers." 2>&1 || true)
neither=$(decide answer gift-note 11 2>&1 || true)
bothcode=$(status_of decide answer gift-note 11 --chose "email nobody" --instead "Email only the beta testers.")
settled=$(decide answer gift-note 11 --instead "Email only the beta testers." --why "They asked to hear first." | field '(d["kind"], d["chose"], d["instead"])')
eleven=$(dlist 'next((c["state"], c["chose"], c.get("instead"), c.get("owner_why")) for c in d if c["id"] == 11)')
open_ones=$(decide pending gift-note | field '[c["id"] for c in d["waiting"]]')
decide ask gift-note "${CASE[@]}" --what "The note in the title" --option "no title" --option "a title" --recommended "no title" --why "The rows stay as they are." --said "The two personas split." >/dev/null
flagged_answer=$(status_of decide answer gift-note 12 --instead "A title on the first page only." --criterion-changed --was "old")
decide answer gift-note 12 --instead "A title on the first page only." >/dev/null
twelve=$(dlist 'next((c["state"], c.get("instead"), "criterion" in c) for c in d if c["id"] == 12)')
if grep -qF -- "--chose names one of the options and --instead a decision of the owner's that is none of them: give one of the two" <<<"$both" && [ "$bothcode" = 1 ] \
  && grep -qF -- "give one of the two" <<<"$neither" && [ "$settled" = "('answered', 'Email only the beta testers.', True)" ] \
  && [ "$eleven" = "('answered', 'Email only the beta testers.', True, 'They asked to hear first.')" ] && [ "$open_ones" = "[4]" ] \
  && [ "$flagged_answer" = 2 ] && [ "$twelve" = "('answered', True, False)" ]; then
  pass "a decision of the owner's that is none of the options settles the choice with --instead, an irreversible one too, so it no longer waits; it is refused together with --chose or with neither; and it carries no criterion"
else
  fail "an answer that is none of the options: $both / $neither / $settled / $eleven / $open_ones / $flagged_answer / $twelve"
fi
# A step that a later "no" cannot reverse has no end to its wait: his answer is an answer, never late, and no timeout goes in with it.
decide ask gift-note "${CASE[@]}" --what "Delete the old exports" --option "delete them" --option "keep them" --recommended "keep them" --why "Nobody asked." --said "The two personas split." --irreversible data >/dev/null
hour_later=$(decide answer gift-note 13 --chose "delete them" 2>&1 | field '(d["kind"], d["chose"])' 2>&1 || true)
thirteen=$(grep '"id": 13' "$dfile" | "$PY" -c 'import json, sys; print([json.loads(line)["kind"] for line in sys.stdin])')
if [ "$hour_later" = "('answered', 'delete them')" ] && [ "$thirteen" = "['asked', 'answered']" ] && [ "$(dlist 'next((c["state"], c["by"]) for c in d if c["id"] == 13)')" = "('answered', 'owner')" ]; then
  pass "an answer to an irreversible step is his answer: no timeout is written with it, and the step is taken as he said"
else
  fail "a late answer to an irreversible step: $hour_later / $thirteen"
fi
# A task that is dropped or landed has nothing that waits: pending leaves its choices out and says why, wait returns at once, and list still shows them.
decide ask dropped-task "${CASE[@]}" --what "Email the merchants" --option "email all" --option "email nobody" --recommended "email nobody" --why "Nobody asked." --said "The two personas split." --irreversible person >/dev/null
decide ask landed-task "${CASE[@]}" --what "The header" --option "a header" --option "no header" --recommended "no header" --why "The rows stay." --said "The two personas split." >/dev/null
project --repo "$DC" state dropped-task dropped "the owner dropped it" >/dev/null && project --repo "$DC" state landed-task landed "main a..b" >/dev/null
all_open=$(decide pending | field '(sorted({c["task"] for c in d["waiting"]}), [(e["task"], e["status"], e["choices"]) for e in d["ended"]])')
one_ended=$(decide pending dropped-task | field '(d["waiting"], d["ended"][0]["status"], d["ended"][0]["says"])')
started=$(date +%s)
waited=$(decide wait dropped-task 1 --seconds 30 | field '(d["ended"], d["status"])')
took=$(( $(date +%s) - started ))
kept=$(decide list dropped-task | field '[(c["id"], c["state"]) for c in d]')
if [ "$all_open" = "(['gift-note'], [('dropped-task', 'dropped', [1]), ('landed-task', 'landed', [1])])" ] \
  && [ "$one_ended" = "([], 'dropped', 'the task is dropped: its choices no longer wait for an answer')" ] \
  && [ "$waited" = "('the task is dropped: the choice no longer waits', 'dropped')" ] && [ "$took" -lt 30 ] && [ "$kept" = "[(1, 'waits')]" ]; then
  pass "a dropped or landed task has no choice that waits: pending leaves it out and says why, wait returns at once with the task's status, and list still shows its record"
else
  fail "the choices of an ended task: $all_open / $one_ended / $waited / $took / $kept"
fi
# Nothing more is decided in a task that ended: a decision, a choice, an answer and the end of a wait are refused, with its state, and write nothing.
ended_lines=$(cat "$DC/.lem/state/tasks/dropped-task/decisions.jsonl" "$DC/.lem/state/tasks/landed-task/decisions.jsonl" | grep -c '')
late_log=$(decide log dropped-task --what "The name of the column" --chose gift_note --why "snake case" --by lead 2>&1 || true)
late_ask=$(decide ask landed-task "${CASE[@]}" --what "The footer" --option "a footer" --option "none" --recommended "none" --why w --said s 2>&1 || true)
late_answer=$(decide answer dropped-task 1 --chose "email nobody" 2>&1 || true)
late_away=$(project --repo "$DC" owner away --words "I'm away" | field 'd["taken"]')
project --repo "$DC" owner back --words "I'm back" >/dev/null
if grep -qF "dropped-task is dropped" <<<"$late_log" && grep -qF "landed-task is landed" <<<"$late_ask" && grep -qF "dropped-task is dropped" <<<"$late_answer" \
  && [ "$late_away" = "[]" ] && [ "$(status_of decide log dropped-task --what w --chose c --why y --by lead)" = 1 ] \
  && [ "$(cat "$DC/.lem/state/tasks/dropped-task/decisions.jsonl" "$DC/.lem/state/tasks/landed-task/decisions.jsonl" | grep -c '')" = "$ended_lines" ]; then
  pass "a dropped or landed task takes no new decision, choice or answer, and the owner's away takes none of its choices: each is refused with the task's state and writes nothing"
else
  fail "a write to an ended task: $late_log / $late_ask / $late_answer / $late_away"
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
# A task dropped while a wait runs ends that wait: the loop reads the task's status each time it reads the choice.
decide ask cancel-task "${CASE[@]}" --what "Email the merchants" --option "email all" --option "email nobody" --recommended "email nobody" --why "Nobody asked." --said "The two personas split." --irreversible person >/dev/null
started=$(date +%s)
"$PY" -B "$DECISIONS" --repo "$DC" wait cancel-task 1 --seconds 30 > "$WORK/cancel-wait.out" 2>&1 &
waiter=$!
sleep 1
project --repo "$DC" state cancel-task dropped "the owner dropped it while a choice waited" >/dev/null
wait "$waiter" || true
took=$(( $(date +%s) - started ))
cancelled=$(field '(d["ended"], d.get("status"))' < "$WORK/cancel-wait.out" || true)
if [ "$cancelled" = "('the task is dropped: the choice no longer waits', 'dropped')" ] && [ "$took" -lt 30 ]; then
  pass "a task dropped while a wait on its choice runs ends that wait before its time, with the task's status"
else
  fail "a task dropped during a wait: $cancelled / $took s / $(cat "$WORK/cancel-wait.out")"
fi
# The owner's answer to a choice that waits is written with answer, by Lem and by a session's lead: a new decision would leave the choice waiting.
SKILLTEXT=${SKILLTEXT:-$PWD/skills/lem}
lead_brief=$SKILLTEXT/prompts/lead.md
# shellcheck disable=SC2016  # the backticks are the stage text's own marks around a command
if grep -qF 'lem decisions answer SLUG N' "$lead_brief" && grep -qF -- '`--instead TEXT`' "$lead_brief" && grep -qF 'his that answers no choice is logged with `lem decisions log SLUG --by owner`' "$lead_brief" \
  && ! grep -qE 'log it with `lem decisions log SLUG --by owner`|Log each answer with `lem decisions log' "$lead_brief" "$SKILLTEXT"/stages/*.md "$SKILLTEXT"/prompts/*.md; then
  pass "the lead's brief and Lem's stage write the owner's answer to a choice that waits with answer, --instead included, and log a word of his only when it answers no choice"
else
  fail "the owner's answer in the lead's brief and the stages: $(grep -n 'by owner' "$SKILLTEXT"/stages/*.md "$SKILLTEXT"/prompts/*.md)"
fi
# An answer and the owner's away at one time: each reads the state inside the lock, so the record holds one outcome,
# whichever takes the lock first: his answer, or the pick his away takes with his answer after it as a late one.
rfile=$DC/.lem/state/tasks/race-task/decisions.jsonl
decide ask race-task "${CASE[@]}" --what "The order of the rows" --option "by number" --option "by date" --recommended "by number" --why "It is the order of today." --said "The two personas split." >/dev/null
"$PY" -c 'import fcntl, sys, time; f = open(sys.argv[1], "w"); fcntl.flock(f, fcntl.LOCK_EX); print("held", flush=True); time.sleep(30)' "$DC/.lem/state/tasks/race-task/decisions.lock" > "$WORK/rlock.out" &
holder=$!
soon test -s "$WORK/rlock.out"
"$PY" -B "$DECISIONS" --repo "$DC" answer race-task 1 --chose "by date" > "$WORK/race-answer.out" 2>&1 &
ra=$!
"$PY" -B "$PROJECT" --repo "$DC" owner away --words "I'm away" > "$WORK/race-away.out" 2>&1 &
rt=$!
sleep 2
kill "$holder" 2>/dev/null || true; wait "$holder" 2>/dev/null || true
wait "$ra" || true; wait "$rt" || true
project --repo "$DC" owner back --words "I'm back" >/dev/null
raced=$(grep -c '"kind": "timeout"' "$rfile" || true)/$(grep -c '"kind": "answered"' "$rfile" || true)/$(decide list race-task | field '(d[0]["state"], d[0].get("chose"), d[0].get("late", {}).get("chose"))' || true)
if [ "$raced" = "1/0/('timeout', 'by number', 'by date')" ] || [ "$raced" = "0/1/('answered', 'by date', None)" ]; then
  pass "an answer and the owner's away that start at one time leave one outcome, whichever takes the lock first"
else
  fail "an answer and the owner's away at one time: $raced / $(cat "$rfile" "$WORK/race-answer.out" "$WORK/race-away.out")"
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
dialectic=$(ladder --chose "after the price" --by dialectic --level "personas=1 for the last column, 1 for after the price" --level "dialectic=no break" | field '(d["by"], d["levels"])')
unsettled=$(ladder --chose "the last column" --by lead --unsettled --level "experts=split" | field '(d["by"], d["unsettled"])')
not_lead=$(status_of ladder --chose "the last column" --by experts --unsettled)
if [ "$voted" = "('personas', [['the merchant, opus', 'the last column'], ['the accountant, opus', 'the last column']], ['the last column', 'after the price'])" ] \
  && grep -qF "the accountant, opus voted otherwise" <<<"$split" && grep -qF "this one has 1" <<<"$alone_vote" && [ "$bad_vote" = 1 ] && [ "$lines_after_refusals" = 1 ] \
  && [ "$gate" = gate ] && [ "$dialectic" = "('dialectic', {'personas': '1 for the last column, 1 for after the price', 'dialectic': 'no break'})" ] \
  && [ "$unsettled" = "('lead', True)" ] && [ "$not_lead" = 1 ]; then
  pass "each level of the ladder logs the decision it settles: the personas only with two votes or more, all for the option taken, else nothing is written; the gate, the dialectic and the lead's unsettled pick each with their own name and what each level answered"
else
  fail "the ladder's record: $voted / $split / $alone_vote / $bad_vote / $lines_after_refusals / $gate / $dialectic / $unsettled / $not_lead"
fi
# A task that runs without the owner, here by a night's mark: a lead's wait on a choice returns at once and takes the
# ladder's pick, marked early; a choice asked then is taken at once; an irreversible step still waits for him.
decide ask ladder-task "${CASE[@]}" --what "The note's font" --option plain --option bold --recommended plain --why "The export has no fonts." --said "The personas split; the experts split." >/dev/null
decide ask ladder-task "${CASE[@]}" --what "Email the merchants" --option "send it" --option "send nothing" --recommended "send nothing" --why "Nothing they see changes." --said s --irreversible person >/dev/null
project --repo "$DC" task-dir ladder-task --ask "The ladder of the gift note." --night 2026-11-18 >/dev/null
started=$(date +%s)
woke=$(decide wait ladder-task 5 --seconds 30 | field '(d["ended"], d["state"], d["chose"], d["by"], d["early"])')
took=$(( $(date +%s) - started ))
still=$(decide wait ladder-task 6 --seconds 1 | field 'd["ended"]')
asked_away=$(decide ask ladder-task "${CASE[@]}" --what "The note's colour" --option black --option red --recommended black --why "The export has no colours." --said s | field '(d["taken"], "nothing waits" in d["next"])')
seven=$(decide list ladder-task | field 'next((c["state"], c["chose"], c.get("early")) for c in d if c["id"] == 7)')
project --repo "$DC" owner back --words "I am back" >/dev/null
if [ "$woke" = "('taken without the owner: the task runs without him now', 'timeout', 'plain', 'timeout', True)" ] && [ "$took" -lt 30 ] \
  && [ "$still" = "still waits" ] && [ "$asked_away" = "('black', True)" ] && [ "$seven" = "('timeout', 'black', True)" ]; then
  pass "while a task runs without the owner a wait on a choice returns at once with the recommended option taken, marked early, and a choice asked then is taken at once; an irreversible step still waits for him"
else
  fail "a choice when the task runs without the owner: $woke / $took / $still / $asked_away / $seven"
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

# The one list of what waits for the owner: a choice, criteria that wait for his yes, a step of his, a pull
# request with green or not, and a retro's proposals.
wq() { project --repo "$WQ" "$@"; }
for slug in a-choice his-criteria his-step proposed-one; do wq task-dir "$slug" --ask "The ask of $slug." >/dev/null; done
"$PY" -B "$DECISIONS" --repo "$WQ" ask a-choice "${CASE[@]}" --what "Where the note goes" --option "the last column" --option "after the price" --recommended "the last column" --why w --said s >/dev/null
wq state his-criteria held "the criteria wait for the owner" "type: feat, because the export gets a column" >/dev/null
wq state his-step held "the reviewer's pane waits for the owner's trust of the folder" >/dev/null
wq state proposed-one open "pull request https://github.com/acme/shop/pull/7" "not green: the bar is lower" >/dev/null
printf '%s\n' '{"proposed": "abc1234", "pushed": "abc1234", "forge": {"mergeable": "CONFLICTING", "head": "abc1234"}, "pr": {"number": 7, "url": "https://github.com/acme/shop/pull/7"}, "not_green": ["the bar is lower"]}' > "$WQ/.lem/state/tasks/proposed-one/landing.json"
mkdir -p "$WQ/.lem/state/retros"
printf '%s\n' '{"title": "The retro of 2026-11-17", "questions": [{"id": "p1", "prompt": "Move the rule?", "options": ["approve", "reject", "later"]}, {"id": "p2", "prompt": "Drop the step?", "options": ["approve", "reject", "later"]}]}' > "$WQ/.lem/state/retros/2026-11-17.json"
printf '%s\n' 'not json' > "$WQ/.lem/state/retros/2026-11-18.json"
listed=$(wq waiting)
seen=$(grep -c '' "$XDG_CONFIG_HOME/lem/owner.jsonl" 2>/dev/null || true)
wq owner away --words "I'm away" >/dev/null
away_list=$(wq waiting | field '(d["owner"]["away"], d["owner"]["words"], d["owner"]["since"] is not None, d["choices"], d["count"])' 2>&1 || true)
wq owner back --words "/lem im-back" >/dev/null
shape=$(field '([(c["task"], c["id"]) for c in d["choices"]], [(t["task"], t["line"]) for t in d["criteria"]], [(t["task"], t["line"]) for t in d["held"]], [(t["task"], t["pull_request"], t["green"], t["not_green"], t["conflict"]) for t in d["pull_requests"]], [(r["date"], r["proposals"], "problem" in r) for r in d["retros"]], d["count"])' <<<"$listed" 2>&1 || true)
if [ "$shape" = "([('a-choice', 1)], [('his-criteria', 'the criteria wait for the owner')], [('his-step', \"the reviewer's pane waits for the owner's trust of the folder\")], [('proposed-one', 'https://github.com/acme/shop/pull/7', False, ['the bar is lower'], True)], [('2026-11-17', 2, False), ('2026-11-18', None, True)], 7)" ] \
  && [ "$(field '(d["owner"]["away"], d["owner"]["seen"])' <<<"$listed")" = "(False, $seen)" ] && [ "$(field 'd["pull_requests"][0]["ask"]' <<<"$listed")" = "The ask of proposed-one." ] \
  && [ "$away_list" = "(True, \"I'm away\", True, [], 6)" ]; then
  pass "waiting lists in one JSON what waits for the owner: whether he is away, each choice as decisions.py pending gives it, the criteria and the steps that hold a task, each pull request with green or not and whether the forge calls it conflicting, and each retro's proposals, with a file that does not read named as such; while he is away it says so first, since when and in his words, and his choice is taken"
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
printf '%s\n' '{"proposed": "def5678", "pr": {"number": 8, "url": "https://github.com/acme/shop/pull/8"}, "not_green": []}' > "$WQ/.lem/state/tasks/night-small/landing.json"
wq state night-full open "pull request https://github.com/acme/shop/pull/9" "not green: the owner did not approve the criteria" >/dev/null
printf '%s\n' '{"proposed": "0a1b2c3", "pr": {"number": 9, "url": "https://github.com/acme/shop/pull/9"}, "not_green": ["the owner did not approve the criteria"]}' > "$WQ/.lem/state/tasks/night-full/landing.json"
wq owner away --words "I'm away" >/dev/null && wq owner back --words "/lem im-back" >/dev/null
wq state night-merged landed "main 1234567..89abcde" >/dev/null
wq state night-closed dropped "the pull request was closed on the forge" >/dev/null
other_form=$(wq task-dir night-other --ask "The backlog item of night-other." --night "the night run" 2>&1 || true)
nightly=$(wq waiting | field '([(t["task"], t["green"], t["night"]) for t in d["pull_requests"]], sum(1 for t in d["pull_requests"] if t["night"]))' 2>&1 || true)
marked=$(wq tasks | field '[(t["slug"], t["night"]) for t in d if t["slug"].startswith("night-") or t["slug"] == "proposed-one"]' 2>&1 || true)
if [ "$nightly" = "([('night-full', False, '2026-11-18'), ('night-small', True, '2026-11-18'), ('proposed-one', False, None)], 2)" ] \
  && [ "$marked" = "[('night-closed', '2026-11-18'), ('night-full', '2026-11-18'), ('night-merged', '2026-11-18'), ('night-small', '2026-11-18'), ('proposed-one', None)]" ] \
  && grep -qF -- "--night is the night's date, YYYY-MM-DD, not 'the night run'" <<<"$other_form" && [ "$night_mode" = alone ] \
  && [ "$(wq tasks | field '[t["mode"] for t in d if t["slug"] == "night-small"][0]')" = alone ]; then
  pass "a task the night opened runs without the owner and carries the night's date in tasks and in waiting, also after he went away and said he is back; the brake counts the night's pull requests that nobody merged or closed; and a night that is no date is refused"
else
  fail "the night's pull requests: $nightly / $marked / $other_form / $night_mode"
fi

# The morning: a task the night left held for the owner is marked with its night beside a day's, the night's pull
# requests are among the others, and the list names last night's report, today's or yesterday's, never an older one.
wq task-dir night-held --ask "The backlog item of night-held." --night 2026-11-18 >/dev/null
wq state night-held held "choice 1 waits for the owner" >/dev/null
no_report=$(wq waiting | field 'd["night_report"]' 2>&1 || true)
mkdir -p "$WQ/.lem/state/night"
printf '%s\n' '# The night of 2026-01-01' > "$WQ/.lem/state/night/2026-01-01.md"
before=$(wq waiting | field 'd["night_report"]' 2>&1 || true)
last_night=$WQ/.lem/state/night/$(date +%F).md
printf '%s\n' '# The night' '- night-small: pull request 8, green' '- night-full: pull request 9, not green' '- night-held: choice 1 waits for the owner' > "$last_night"
morning=$(wq waiting | field '([(t["task"], t["night"]) for t in d["held"]], [(t["task"], t["night"]) for t in d["pull_requests"]], d["night_report"]["file"])' 2>&1 || true)
if [ "$no_report" = None ] && [ "$before" = None ] \
  && [ "$morning" = "([('his-step', None), ('night-held', '2026-11-18')], [('night-full', '2026-11-18'), ('night-small', '2026-11-18'), ('proposed-one', None)], '$last_night')" ]; then
  pass "in the morning the list marks a task the night held and the night's pull requests with the night, beside a day's, and names last night's report and no older one"
else
  fail "the morning: $no_report / $before / $morning"
fi


# The owner's status is the machine's: his away in one repository takes a choice that a lead waits on in another, and
# an irreversible step there still waits; a task the night opened in the other repository runs without him after his
# back too, and its choice is taken at once.
D2=$WORK/second-repo
git init -q -b main "$D2" && commit "$D2" start && project --repo "$D2" init --base main >/dev/null
d2() { "$PY" -B "$DECISIONS" --repo "$D2" "$@"; }
project --repo "$D2" task-dir report-dates >/dev/null && project --repo "$D2" state report-dates building "lead: builder" >/dev/null
d2 ask report-dates "${CASE[@]}" --what "The date's form" --option "2026-11-19" --option "19.11.2026" --recommended "2026-11-19" --why "it sorts" --said "The personas split." >/dev/null
d2 ask report-dates "${CASE[@]}" --what "Email the merchants" --option "send it" --option "send nothing" --recommended "send nothing" --why w --said s --irreversible person >/dev/null
started=$(date +%s)
"$PY" -B "$DECISIONS" --repo "$D2" wait report-dates 1 --seconds 30 > "$WORK/far-wait.out" 2>&1 &
waiter=$!
sleep 1
project --repo "$DC" owner away --words "/lem im-away" >/dev/null
wait "$waiter" || true
took=$(( $(date +%s) - started ))
far=$(field '(d["ended"], d["chose"], d["by"])' < "$WORK/far-wait.out" 2>&1 || true)
far_never=$(d2 wait report-dates 2 --seconds 1 | field 'd["ended"]')
project --repo "$D2" task-dir night-dates --ask "The backlog item of night-dates." --night 2026-11-19 >/dev/null
project --repo "$DC" owner back --words "/lem im-back" >/dev/null
night_mode=$(project --repo "$D2" tasks | field '[(t["slug"], t["mode"]) for t in d if t["slug"] in ("night-dates", "report-dates")]')
night_asked=$(d2 ask night-dates "${CASE[@]}" --what "The night's date form" --option "ISO" --option "local" --recommended "ISO" --why "it sorts" --said s | field 'd["taken"]')
# An approval without the owner reads his status again under its lock: here he comes back in the first repository while
# the approval of the second waits for the lock, and it is refused.
project --repo "$D2" task-dir late-approve >/dev/null && project --repo "$D2" state late-approve building "lead: builder" >/dev/null
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the report gets a new column.' '' '1. The report shows each date as 2026-11-19.' > "$WORK/late-approve.md"
project --repo "$DC" owner away --words "I'm away" >/dev/null
"$PY" -c 'import fcntl, sys, time; f = open(sys.argv[1], "w"); fcntl.flock(f, fcntl.LOCK_EX); print("held", flush=True); time.sleep(30)' "$D2/.lem/state/tasks/late-approve/criteria.lock" > "$WORK/alock.out" &
holder=$!
soon test -s "$WORK/alock.out"
"$PY" -B "$CRITERIA" --repo "$D2" approve late-approve --file "$WORK/late-approve.md" --alone > "$WORK/late-approve.out" 2>&1 &
approver=$!
sleep 1
project --repo "$DC" owner back --words "I'm back" >/dev/null
kill "$holder" 2>/dev/null || true; wait "$holder" 2>/dev/null || true
wait "$approver" || true
if [ "$far" = "('taken without the owner: the task runs without him now', '2026-11-19', 'timeout')" ] && [ "$took" -lt 30 ] && [ "$far_never" = "still waits" ] \
  && [ "$night_mode" = "[('night-dates', 'alone'), ('report-dates', 'with-owner')]" ] && [ "$night_asked" = ISO ] \
  && grep -qF "late-approve runs with the owner" "$WORK/late-approve.out" && [ ! -e "$D2/.lem/state/tasks/late-approve/criteria.json" ]; then
  pass "the owner's away in one repository takes a choice a lead waits on in another within seconds, never an irreversible step there; his back in the first leaves a task the night opened in the other without him, and its choice is taken at once; an approval without him that waited for its lock while he came back is refused"
else
  fail "the owner's status across two repositories: $far / $took / $far_never / $night_mode / $night_asked / $(cat "$WORK/far-wait.out" "$WORK/late-approve.out")"
fi

finish
