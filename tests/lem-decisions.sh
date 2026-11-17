#!/usr/bin/env bash
# The decisions of a task: each one the lead or the personas took, and each choice that waits for the
# owner a fixed time and no longer, except a step that a later "no" cannot reverse.
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
  --said "The merchant and the accountant both picked the semicolon." | field '(d["id"], d["by"], "criterion" in d, d["said"])')
if [ "$lead" = "(1, 'taken', 'lead', 'rename the column')" ] \
  && [ "$personas" = "(2, 'personas', False, 'The merchant and the accountant both picked the semicolon.')" ] \
  && grep -qF -- "--by personas needs --said: who answered and what each picked" <<<"$nosaid" && [ "$nostory" = 2 ] \
  && [ "$(grep -c '' "$dfile")" = 2 ] && [ "$(grep -c '"event": "decision.taken", "task": "gift-note"' "$DC/.lem/state/events.jsonl")" = 2 ]; then
  pass "a decision of the lead or of the personas is written down with its number, and each is an event too; the personas' one needs what they said, and a decision carries no criterion: a criterion's change has a record of its own"
else
  fail "decisions.py log: $lead / $personas / $nosaid / $nostory / $(cat "$dfile")"
fi
one=$(decide ask gift-note "${CASE[@]}" --what "Which note wins" --option "the first" --recommended "the first" --why w --said s 2>&1 || true)
notone=$(decide ask gift-note "${CASE[@]}" --what "Which note wins" --option "the first" --option "the last" --recommended "the newest" --why w --said s 2>&1 || true)
# the clock before the choice is asked and after its wait is read: what the wait has left is the
# settings' 15 minutes less the seconds between the two, on a machine of any speed
asked_from=$(date +%s)
asked=$(decide ask gift-note "${CASE[@]}" --what "Where the note goes in the row" --option "the last column" --option "after the price" --recommended "the last column" \
  --why "an import that reads the columns by place keeps working" --said "The merchant picked the last column, the accountant after the price.")
forever=$(decide ask gift-note "${CASE[@]}" --what "Send the merchants an email about the new column" --option "send it" --option "do not send it" --recommended "do not send it" \
  --why "the column is visible in the export" --said "The merchant wants the email, the accountant does not." --irreversible person)
waits=$(decide pending gift-note)
asked_to=$(date +%s)
everywhere=$(decide pending | field '([(c["task"], c["id"]) for c in d["waiting"]], d["ended"])')
if grep -q "a choice has two options or more" <<<"$one" && grep -qF -- "--recommended is one of the options, word for word: the first; the last" <<<"$notone" \
  && [ "$(field '(d["id"], d["wait_minutes"], "tell Lem that choice 3 of gift-note waits" in d["next"])' <<<"$asked")" = "(3, 15, True)" ] \
  && [ "$(field '(d["id"], d["irreversible"], "no timeout takes it" in d["next"], "tell Lem that choice 4 of gift-note waits" in d["next"], d["deadline"])' <<<"$forever")" = "(4, 'person', True, True, None)" ] \
  && [ "$(field '[(c["id"], c["state"], 900 - '"$((asked_to - asked_from))"' <= c["seconds_left"] <= 900 if c["seconds_left"] is not None else None) for c in d["waiting"]]' <<<"$waits")" = "[(3, 'waits', True), (4, 'waits', None)]" ] \
  && [ "$everywhere" = "([('gift-note', 3), ('gift-note', 4)], [])" ] && [ "$(grep -c '"event": "decision.asked", "task": "gift-note"' "$DC/.lem/state/events.jsonl")" = 2 ]; then
  pass "a choice for the owner has two options or more and recommends one of them; it waits the settings' 15 minutes, and pending lists each choice that waits with the seconds it has left, and none for a step no timeout takes"
else
  fail "decisions.py ask and pending: $one / $notone / $asked / $forever / $waits / $everywhere"
fi
# A choice for the owner tells him one run above his card: the case in numbered steps, how it is known,
# and its cause. A night plan asks no choice of his: nobody is there, and no wait or expert takes one at night.
two_options=(--option "the first" --option "the last" --recommended "the first" --why w --said s)
nocase=$(decide ask gift-note --what "Which note wins" "${two_options[@]}" 2>&1 || true)
onestep=$(decide ask gift-note --what "Which note wins" --case "1. Two notes come in for order 1042." --case-was derived --cause c "${two_options[@]}" 2>&1 || true)
unknown=$(decide ask gift-note --what "Which note wins" --case $'1. a\n2. b' --case-was guessed --cause c "${two_options[@]}" 2>&1 || true)
nocause=$(decide ask gift-note --what "Which note wins" --case $'1. a\n2. b' --case-was derived "${two_options[@]}" 2>&1 || true)
choice3() { decide pending gift-note | "$PY" -c 'import json, sys; print(next(c for c in json.load(sys.stdin)["waiting"] if c["id"] == 3)[sys.argv[1]])' "$1"; }
project --repo "$DC" task-dir night-task >/dev/null
printf '%s\n' 'Read SKILL_DIR/prompts/lead.md and follow it.' 'task: night-task' 'stop after the plan: yes' 'night: yes' > "$DC/.lem/state/tasks/night-task/brief.md"
at_night=$(decide ask night-task "${CASE[@]}" --what "Which note wins" "${two_options[@]}" 2>&1 || true)
if grep -qF -- "--case is one concrete case that ends badly, in numbered steps, one to a line" <<<"$nocase" && grep -qF "this one has 0 numbered steps" <<<"$nocase" \
  && grep -qF "this one has 1 numbered step" <<<"$onestep" && grep -qF -- "--case-was says how the case is known: reproduced or derived" <<<"$unknown" \
  && grep -qF -- "--cause needs its text" <<<"$nocause" \
  && [ "$(choice3 case)" = "${CASE[1]}" ] && [ "$(choice3 case_was)" = derived ] && [ "$(choice3 cause)" = "${CASE[5]}" ] \
  && grep -qF "the brief of night-task says \`night: yes\`: nobody is there to answer at night" <<<"$at_night" && grep -qF "report.md under \"for the owner\"" <<<"$at_night" \
  && [ ! -e "$DC/.lem/state/tasks/night-task/decisions.jsonl" ] && [ "$(grep -c '"event": "decision.asked", "task": "gift-note"' "$DC/.lem/state/events.jsonl")" = 2 ]; then
  pass "a choice for the owner carries one run above his card: its case in two numbered steps or more, kept line by line, whether it was reproduced or derived, and its cause; a choice without them is refused, and a night plan asks none, since nobody is there and no wait or expert takes a decision of his at night"
else
  fail "the run of a choice and the night: $nocase / $onestep / $unknown / $nocause / $(choice3 case) / $at_night"
fi
early=$(decide timeout gift-note 3 2>&1 || true)
past "$dfile" 3 4
never=$(decide timeout gift-note 4 2>&1 || true)
started=$(date +%s)
over=$(decide wait gift-note 3 --seconds 30 | field '(d["ended"], "timeout gift-note 3" in d["next"])')
still=$(decide wait gift-note 4 --seconds 1 | field '(d["ended"], d["seconds_left"])')
took=$(( $(date +%s) - started ))
taken=$(decide timeout gift-note 3 | field '(d["id"], d["kind"], d["chose"])')
again=$(decide timeout gift-note 3 2>&1 || true)
same=$(decide answer gift-note 3 --chose "the last column" | field '(d["kind"], d["taken"], d["next"])')
if grep -q "the wait of choice 3 has [0-9]* seconds left (until 20.*); the owner may still answer" <<<"$early" \
  && grep -q "choice 4 is a step that a later \"no\" cannot reverse (it sends something to a person): no timeout takes it" <<<"$never" \
  && [ "$over" = "('the wait is over', True)" ] && [ "$still" = "('still waits', None)" ] && [ "$took" -lt 30 ] \
  && [ "$taken" = "(3, 'timeout', 'the last column')" ] && grep -q "choice 3 does not wait: it is timeout, with 'the last column'" <<<"$again" \
  && [ "$same" = "('late', 'the last column', 'the answer is the action that was taken: nothing more to do')" ]; then
  pass "a timeout is refused while the wait runs and always for a step a later no cannot reverse; after the wait, wait says so at once, the recommended action is taken once, and a late answer that is the same needs nothing more"
else
  fail "decisions.py timeout: $early / $never / $over / $still / $took / $taken / $again / $same"
fi
decide ask gift-note "${CASE[@]}" --what "The header of the column" --option "Gift note" --option "Note" --recommended "Gift note" --why "it says what the cell holds" --said "The two personas split." >/dev/null
past "$dfile" 5
decide timeout gift-note 5 >/dev/null
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
# An answer after the wait, before anybody wrote the timeout, is late: the recommended option stands, and both lines are written at once.
decide ask gift-note "${CASE[@]}" --what "The note's font" --option "plain" --option "bold" --recommended "plain" --why "The export has no fonts." --said "The two personas split." >/dev/null
past "$dfile" 7
after=$(decide answer gift-note 7 --chose "bold" --why "Merchants miss it otherwise." | field '(d["kind"], d["state"], d["taken"], d["timeout_written"], "it is a correction" in d["next"])')
gone=$(decide timeout gift-note 7 2>&1 || true)
kinds=$(grep '"id": 7' "$dfile" | "$PY" -c 'import json, sys; print([json.loads(line)["kind"] for line in sys.stdin])')
seven=$(dlist 'next((c["state"], c["chose"], c.get("late", {}).get("chose"), c.get("late", {}).get("why")) for c in d if c["id"] == 7)')
if [ "$after" = "('late', 'timeout', 'plain', True, True)" ] && grep -q "choice 7 does not wait: it is timeout, with 'plain'" <<<"$gone" \
  && [ "$kinds" = "['asked', 'timeout', 'late']" ] && [ "$seven" = "('timeout', 'plain', 'bold', 'Merchants miss it otherwise.')" ]; then
  pass "an answer that comes after the wait, with no timeout written yet, is late: the timeout and the answer go into the record in one write, the recommended option stands, and the owner's reason is kept"
else
  fail "an answer after the wait: $after / $gone / $kinds / $seven"
fi
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
# A step that a later "no" cannot reverse has no end to its wait: his answer an hour later is an answer, never late, and no timeout goes in with it.
decide ask gift-note "${CASE[@]}" --what "Delete the old exports" --option "delete them" --option "keep them" --recommended "keep them" --why "Nobody asked." --said "The two personas split." --irreversible data >/dev/null
past "$dfile" 13
hour_later=$(decide answer gift-note 13 --chose "delete them" 2>&1 | field '(d["kind"], d["chose"])' 2>&1 || true)
thirteen=$(grep '"id": 13' "$dfile" | "$PY" -c 'import json, sys; print([json.loads(line)["kind"] for line in sys.stdin])')
if [ "$hour_later" = "('answered', 'delete them')" ] && [ "$thirteen" = "['asked', 'answered']" ] && [ "$(dlist 'next((c["state"], c["by"]) for c in d if c["id"] == 13)')" = "('answered', 'owner')" ]; then
  pass "an answer to an irreversible step after any time is his answer: no timeout is written with it, and the step is taken as he said"
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
past "$DC/.lem/state/tasks/landed-task/decisions.jsonl" 1
late_timeout=$(decide timeout landed-task 1 2>&1 || true)
if grep -qF "dropped-task is dropped" <<<"$late_log" && grep -qF "landed-task is landed" <<<"$late_ask" && grep -qF "dropped-task is dropped" <<<"$late_answer" \
  && grep -qF "landed-task is landed" <<<"$late_timeout" && [ "$(status_of decide log dropped-task --what w --chose c --why y --by lead)" = 1 ] \
  && [ "$(cat "$DC/.lem/state/tasks/dropped-task/decisions.jsonl" "$DC/.lem/state/tasks/landed-task/decisions.jsonl" | grep -c '')" = "$ended_lines" ]; then
  pass "a dropped or landed task takes no new decision, choice, answer or timeout: each is refused with the task's state and writes nothing"
else
  fail "a write to an ended task: $late_log / $late_ask / $late_answer / $late_timeout"
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
# An answer and a timeout at one time: each reads the state inside the lock, so the record holds one outcome.
rfile=$DC/.lem/state/tasks/race-task/decisions.jsonl
decide ask race-task "${CASE[@]}" --what "The order of the rows" --option "by number" --option "by date" --recommended "by number" --why "It is the order of today." --said "The two personas split." >/dev/null
past "$rfile" 1
"$PY" -c 'import fcntl, sys, time; f = open(sys.argv[1], "w"); fcntl.flock(f, fcntl.LOCK_EX); print("held", flush=True); time.sleep(30)' "$DC/.lem/state/tasks/race-task/decisions.lock" > "$WORK/rlock.out" &
holder=$!
soon test -s "$WORK/rlock.out"
"$PY" -B "$DECISIONS" --repo "$DC" answer race-task 1 --chose "by date" > "$WORK/race-answer.out" 2>&1 &
ra=$!
"$PY" -B "$DECISIONS" --repo "$DC" timeout race-task 1 > "$WORK/race-timeout.out" 2>&1 &
rt=$!
sleep 2
kill "$holder" 2>/dev/null || true; wait "$holder" 2>/dev/null || true
wait "$ra" || true; wait "$rt" || true
raced=$(grep -c '"kind": "timeout"' "$rfile" || true)/$(grep -c '"kind": "answered"' "$rfile" || true)/$(decide list race-task | field '(d[0]["state"], d[0].get("chose"), d[0].get("late", {}).get("chose"))' || true)
if [ "$raced" = "1/0/('timeout', 'by number', 'by date')" ]; then
  pass "an answer after the wait and a timeout that start at one time leave one timeout and one late answer, whichever takes the lock first"
else
  fail "an answer and a timeout at one time: $raced / $(cat "$rfile" "$WORK/race-answer.out" "$WORK/race-timeout.out")"
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
# The wait is the settings' flow.decision_wait: init writes it, a choice takes it, and a value that is no whole number of 1 or more is refused.
written=$(grep -c '^decision_wait = 15$' "$DC/.lem/project.toml")
sed -i.bak 's|^decision_wait = 15$|decision_wait = 1|' "$DC/.lem/project.toml" && rm "$DC/.lem/project.toml.bak"
short=$(decide ask other-task "${CASE[@]}" --what "x" --option a --option b --recommended a --why w --said s | field '(d["wait_minutes"], (__import__("datetime").datetime.strptime(d["deadline"], "%Y-%m-%dT%H:%M:%SZ") - __import__("datetime").datetime.strptime(d["at"], "%Y-%m-%dT%H:%M:%SZ")).seconds)')
wrong=""
for value in 0 -5 true '"15"' 2.5; do
  sed -i.bak "s|^decision_wait = .*\$|decision_wait = $value|" "$DC/.lem/project.toml" && rm "$DC/.lem/project.toml.bak"
  said=$(project --repo "$DC" show 2>&1 || true)
  if [ "$(status_of project --repo "$DC" show)" = 1 ] && grep -q "flow.decision_wait = .* must be a whole number of minutes, 1 or more" <<<"$said"; then :; else wrong="$wrong $value"; fi
done
refused=$(decide ask other-task "${CASE[@]}" --what "x" --option a --option b --recommended a --why w --said s 2>&1 || true)
sed -i.bak 's|^decision_wait = .*$|decision_wait = 15|' "$DC/.lem/project.toml" && rm "$DC/.lem/project.toml.bak"
if [ "$written" = 1 ] && [ "$short" = "(1, 60)" ] && [ -z "$wrong" ] && grep -q "flow.decision_wait" <<<"$refused" && [ "$(project --repo "$DC" show | field 'd["flow"]["decision_wait"]')" = 15 ]; then
  pass "init writes flow.decision_wait, a choice waits as many minutes as it says, and a value that is not a whole number of 1 or more is refused, by the settings and by a choice"
else
  fail "flow.decision_wait: $written / $short / wrong:$wrong / $refused"
fi
# A lead asks from its worktree, and the wait is the main checkout's: a branch that shortens its own
# flow.decision_wait does not shorten the owner's.
ident "$DC" && git -C "$DC" add -A && git -C "$DC" commit -q -m "chore: the settings"
git -C "$DC" worktree add -q "$WORK/dc-tree" -b feat/short-wait main
sed -i.bak 's|^decision_wait = .*$|decision_wait = 1|' "$WORK/dc-tree/.lem/project.toml" && rm "$WORK/dc-tree/.lem/project.toml.bak"
git -C "$WORK/dc-tree" commit -q -am "chore: a short wait"
branch_wait=$("$PY" -B "$DECISIONS" --repo "$WORK/dc-tree" ask other-task "${CASE[@]}" --what "y" --option a --option b --recommended a --why w --said s | field 'd["wait_minutes"]')
if [ "$branch_wait" = 15 ]; then
  pass "a choice asked from a task's worktree waits the main checkout's flow.decision_wait, not the one the task's branch writes"
else
  fail "the wait of a choice asked from a worktree: $branch_wait"
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
freed=$(project --repo "$WQ" may-start shows-the-list 2>&1 | field 'd["limit"]' 2>&1 || true)
project --repo "$WQ" state in-landing dropped "the test is over" >/dev/null
if [ "$queued" = queued ] && [ "$held_code" = 1 ] \
  && grep -qF "the task 'shows-the-list' is queued after 'caches-the-list', which is building: it starts when caches-the-list is landed, answered or dropped" <<<"$held_back" \
  && grep -qF "it is with its landing" <<<"$over_landing" && [ "$(status_in "$WQ" in-landing)" = dropped ] && [ "$freed" = 4 ]; then
  pass "a lead whose task needs another task's result writes its own task queued after that task; may-start keeps it queued until the other one ended and starts it then, and a task with its landing is never queued"
else
  fail "a lead that queues its task: $queued / $held_back / $over_landing / $freed"
fi

# The one list of what waits for the owner: a choice, criteria that wait for his yes, a step of his, a pull
# request with green or not, a plan drafted at night, and a retro's proposals.
wq() { project --repo "$WQ" "$@"; }
for slug in a-choice his-criteria his-step proposed-one drafted-one; do wq task-dir "$slug" --ask "The ask of $slug." >/dev/null; done
"$PY" -B "$DECISIONS" --repo "$WQ" ask a-choice "${CASE[@]}" --what "Where the note goes" --option "the last column" --option "after the price" --recommended "the last column" --why w --said s >/dev/null
wq state his-criteria held "the criteria wait for the owner" "type: feat, because the export gets a column" >/dev/null
wq state his-step held "the reviewer's pane waits for the owner's trust of the folder" >/dev/null
wq state proposed-one open "pull request https://github.com/acme/shop/pull/7" "not green: the bar is lower" >/dev/null
printf '%s\n' '{"proposed": "abc1234", "pushed": "abc1234", "forge": {"mergeable": "CONFLICTING", "head": "abc1234"}, "pr": {"number": 7, "url": "https://github.com/acme/shop/pull/7"}, "not_green": ["the bar is lower"]}' > "$WQ/.lem/state/tasks/proposed-one/landing.json"
dtree=$(wq worktree-dir drafted-one)
git -C "$WQ" worktree add -q "$dtree" -b plan/drafted-one main
mkdir -p "$dtree/docs/plans" && touch "$dtree/docs/plans/2026-11-17-drafted-one.md"
wq state drafted-one drafted "the plan waits for the owner's word" >/dev/null
mkdir -p "$WQ/.lem/state/retros"
printf '%s\n' '{"title": "The retro of 2026-11-17", "questions": [{"id": "p1", "prompt": "Move the rule?", "options": ["approve", "reject", "later"]}, {"id": "p2", "prompt": "Drop the step?", "options": ["approve", "reject", "later"]}]}' > "$WQ/.lem/state/retros/2026-11-17.json"
printf '%s\n' 'not json' > "$WQ/.lem/state/retros/2026-11-18.json"
listed=$(wq waiting)
shape=$(field '([(c["task"], c["id"]) for c in d["choices"]], [(t["task"], t["line"]) for t in d["criteria"]], [(t["task"], t["line"]) for t in d["held"]], [(t["task"], t["pull_request"], t["green"], t["not_green"], t["conflict"]) for t in d["pull_requests"]], [(t["task"], t["plan"]) for t in d["drafts"]], [(r["date"], r["proposals"], "problem" in r) for r in d["retros"]], d["count"])' <<<"$listed" 2>&1 || true)
if [ "$shape" = "([('a-choice', 1)], [('his-criteria', 'the criteria wait for the owner')], [('his-step', \"the reviewer's pane waits for the owner's trust of the folder\")], [('proposed-one', 'https://github.com/acme/shop/pull/7', False, ['the bar is lower'], True)], [('drafted-one', '$dtree/docs/plans/2026-11-17-drafted-one.md')], [('2026-11-17', 2, False), ('2026-11-18', None, True)], 8)" ] \
  && [ "$(field 'sorted(d["choices"][0])' <<<"$listed" | grep -c seconds_left)" = 1 ] && [ "$(field 'd["pull_requests"][0]["ask"]' <<<"$listed")" = "The ask of proposed-one." ]; then
  pass "waiting lists in one JSON what waits for the owner: each choice as decisions.py pending gives it, the criteria and the steps that hold a task, each pull request with green or not and whether the forge calls it conflicting, each night's draft with its plan, and each retro's proposals, with a file that does not read named as such"
else
  fail "waiting: $shape / $listed"
fi
git -C "$WQ" worktree remove --force "$dtree"

finish
