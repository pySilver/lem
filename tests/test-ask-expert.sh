#!/usr/bin/env bash
# The experts of a choice that waits for the owner, offline: decisions.py keeps each expert's
# advice under the task's lock and refuses a pick that is no option; when the task runs without the
# owner a choice that waits is taken with the experts' shared pick, and the recommended option when
# they split, never an irreversible step; and the lem-ask-expert skill's brief file holds the choice
# and the criteria. No expert runs here.
set -euo pipefail

cd "$(dirname "$0")/.."
PROJECT=$PWD/skills/lem/scripts/project.py
DECISIONS=$PWD/skills/lem/scripts/decisions.py
EXPERTS=$PWD/skills/lem-ask-expert/scripts/experts.py
WORK=$(cd "$(mktemp -d)" && pwd -P)
trap 'rm -rf "$WORK"' EXIT
PY=$(python3 -I -c 'import sys; print(sys.executable)')
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1

fails=0
pass() { printf 'ok   %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1"; fails=$((fails + 1)); }
project() { "$PY" -B "$PROJECT" "$@"; }
status_of() { set +e; "$@" >/dev/null 2>&1; local code=$?; set -e; echo "$code"; }
field() { "$PY" -c 'import json, sys; d = json.load(sys.stdin); print(eval(sys.argv[1], {"d": d}))' "$1"; }

EX=$WORK/experts-repo
git init -q -b main "$EX" && git -C "$EX" config user.name t && git -C "$EX" config user.email t@t
echo 'echo "1042,for Ania"' > "$EX/export.sh" && git -C "$EX" add -A && git -C "$EX" commit -q -m start
project --repo "$EX" init --base main >/dev/null && git -C "$EX" add -A && git -C "$EX" commit -q -m "chore: the settings"
SLUG=gift-note
project --repo "$EX" task-dir "$SLUG" >/dev/null
tree=$(project --repo "$EX" worktree-dir "$SLUG")
git -C "$EX" worktree add -q -b "feat/$SLUG" "$tree" main
project --repo "$EX" state "$SLUG" building 'lead: builder' >/dev/null
mkdir -p "$tree/docs/plans"
printf '%s\n' '# The export has the gift note' '' '## Acceptance criteria' '' 'Size: full, because the export gets a new column.' '' \
  '1. A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has that text in its row.' \
  '2. An order with no gift note has an empty cell, not the word "None".' '' '## Tasks' '' '1. The column.' > "$tree/docs/plans/20261116-$SLUG.md"
git -C "$tree" add -A && git -C "$tree" commit -q -m "docs: the plan"
TASKDIR=$EX/.lem/state/tasks/$SLUG
RECORD=$TASKDIR/decisions.jsonl

decide() { "$PY" -B "$DECISIONS" --repo "$EX" "$@"; }
experts() { "$PY" -B "$EXPERTS" --repo "$EX" "$@"; }
# CASE: the run that ends badly, which every choice for the owner carries above his card
CASE=(--case $'1. An importer reads the export\'s columns by place (`import.py:read_row`).\n2. A new column after the price moves the total one place to the right.\n3. The importer reads the note "for Ania" as the total of order 1042, and stops.'
  --case-was derived --cause "The importer reads columns by place, and so does every reader that copies it.")
# ask WHAT [--irreversible KIND]: a choice of two options, the last column recommended; prints its number
ask() {
  local what=$1; shift
  decide ask "$SLUG" --what "$what" "${CASE[@]}" --option "the last column" --option "after the price" --recommended "the last column" \
    --why "an import that reads the columns by place keeps working" --said "The merchant picked the last column, the accountant after the price." "$@" | field 'd["id"]'
}
# old_wait ID...: each choice as the Lem before 2026-11-18 asked it, which records of open tasks still hold: a wait of
# 15 minutes whose deadline is past, and no timeout written
old_wait() { "$PY" -c 'import json, sys
lines = [json.loads(line) for line in open(sys.argv[1])]
for line in lines:
    if line["kind"] == "asked" and str(line["id"]) in sys.argv[2:]: line.update(wait_minutes=15, deadline="2026-01-01T00:00:00Z")
open(sys.argv[1], "w").write("".join(json.dumps(line) + "\n" for line in lines))' "$RECORD" "$@"; }
# old_mode SLUG alone|with-owner: the event the "go alone" and "I am back" of the Lem before 2026-11-18 wrote for one task
old_mode() { "$PY" -c 'import json, sys, datetime
line = json.dumps({"ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "event": "task.mode", "task": sys.argv[2], "mode": sys.argv[3], "by": "owner", "words": "go alone", "all": False, "was": "with-owner"})
open(sys.argv[1] + "/events.jsonl", "a").write(line + "\n")
open(sys.argv[1] + "/events.js", "a").write("lemEvent(" + line + ");\n")' "$EX/.lem/state" "$@"; }
one() { decide list "$SLUG" | "$PY" -c 'import json, sys; print(json.dumps(next(c for c in json.load(sys.stdin) if c["id"] == int(sys.argv[1]))))' "$1"; }
advised_lines() { grep -c "\"id\": $1, .*\"kind\": \"advised\"" "$RECORD" || true; }

# advise: one advice of each expert, a pick word for word, or none
c1=$(ask "Where the note goes in the row")
wrong=$(decide advise "$SLUG" "$c1" --expert fable --pick "the first column" --why "It reads first." 2>&1 || true)
wrongcode=$(status_of decide advise "$SLUG" "$c1" --expert fable --pick "the first column" --why "It reads first.")
both=$(status_of decide advise "$SLUG" "$c1" --expert fable --pick "the last column" --none --why "w")
neither=$(status_of decide advise "$SLUG" "$c1" --expert fable --why "w")
nothing=$(advised_lines "$c1")
fable=$(decide advise "$SLUG" "$c1" --expert fable --pick "after the price" --why "The accountant reads the price first. A note beside it is seen." | field '(d["kind"], d["expert"], d["pick"], d["advised"], d["experts_pick"])' || true)
again=$(decide advise "$SLUG" "$c1" --expert fable --pick "the last column" --why "w" 2>&1 || true)
astra=$(decide advise "$SLUG" "$c1" --expert astra --none --why "Both options break an import. A new file is safer." | field '(d["none"], "pick" in d, d["advised"], d["experts_pick"])' || true)
pending=$(decide pending "$SLUG" | field '[(c["id"], c["advice"]["fable"]["pick"], c["advice"]["astra"].get("none"), c["experts_pick"]) for c in d["waiting"]]' || true)
events=$(grep -c '"event": "decision.advised", "task": "gift-note"' "$EX/.lem/state/events.jsonl" || true)
if grep -qF "the pick of an expert is one of the options of choice $c1, word for word: the last column; after the price" <<<"$wrong" \
  && [ "$wrongcode" = 1 ] && [ "$both" = 1 ] && [ "$neither" = 1 ] && [ "$nothing" = 0 ] \
  && [ "$fable" = "('advised', 'fable', 'after the price', ['fable'], None)" ] \
  && grep -qF "choice $c1 has the advice of fable already" <<<"$again" \
  && [ "$astra" = "(True, False, ['astra', 'fable'], None)" ] \
  && [ "$pending" = "[($c1, 'after the price', True, None)]" ] && [ "$events" = 2 ] && [ "$(advised_lines "$c1")" = 2 ]; then
  pass "advise keeps one advice of each expert: a pick that is no option, a pick with --none and neither are refused with exit 1 and write nothing; --none is advice too, and pending shows both answers and that they share no pick"
else
  fail "advise: $wrong / $wrongcode / $both / $neither / $nothing / $fable / $again / $astra / $pending / $events"
fi

# advise under the lock: four writers of one expert at one time leave one advice, and the other expert's still goes in
c2=$(ask "The header of the column")
for n in 1 2 3; do
  decide advise "$SLUG" "$c2" --expert fable --pick "after the price" --why "writer $n" >"$WORK/race-$n.out" 2>&1 &
done
decide advise "$SLUG" "$c2" --expert astra --pick "after the price" --why "the other expert" >"$WORK/race-astra.out" 2>&1 &
wait
fables=$(grep -c "\"id\": $c2, .*\"kind\": \"advised\", \"expert\": \"fable\"" "$RECORD" || true)
astras=$(grep -c "\"id\": $c2, .*\"kind\": \"advised\", \"expert\": \"astra\"" "$RECORD" || true)
refused=$(grep -h "has the advice of fable already" "$WORK"/race-[123].out | grep -c '' || true)
if [ "$fables" = 1 ] && [ "$astras" = 1 ] && [ "$refused" = 2 ] && [ "$(one "$c2" | field 'd["state"]')" = waits ]; then
  pass "advise checks and writes under the task's lock: of three writers of one expert at one time one is written and two are refused, and the other expert's advice goes in beside it"
else
  fail "advise under the lock: $fables / $astras / $refused / $(cat "$WORK"/race-*.out)"
fi

# advice comes while a choice waits, however long, also past the deadline an older Lem wrote; an irreversible step takes
# advice too, and an answered choice none
c3=$(ask "The note's font")
old_wait "$c3"
late=$(decide advise "$SLUG" "$c3" --expert fable --pick "after the price" --why "w" 2>&1 | field 'd["kind"]' || true)
c4=$(ask "Email the merchants about the column" --irreversible person)
old_wait "$c4"
forever=$(decide advise "$SLUG" "$c4" --expert fable --pick "after the price" --why "The merchants read the email." | field 'd["kind"]' || true)
c5=$(ask "The note's length")
decide answer "$SLUG" "$c5" --chose "the last column" >/dev/null || true
over=$(decide advise "$SLUG" "$c5" --expert fable --pick "after the price" --why "w" 2>&1 || true)
if [ "$late" = advised ] && [ "$(advised_lines "$c3")" = 1 ] \
  && [ "$forever" = advised ] && grep -qF "choice $c5 does not wait: it is answered, with 'the last column'; advice on it changes nothing" <<<"$over"; then
  pass "advice goes in while a choice waits, however long, also past an older Lem's deadline; an irreversible step takes advice too, and an answered choice takes none"
else
  fail "advice and the wait: $late / $forever / $over"
fi

# When the task runs without the owner (here by the "go alone" of an older Lem, so that only this task's choices go),
# `lem decisions away` takes each choice that waits: the experts' shared pick, by: experts with both reasons, marked
# early; when they split, one found none fits, one is missing or none advised, the recommended option, by: timeout.
# A choice an older Lem asked, whose deadline passed, takes the owner's answer as an answer.
KEEP_SLUG=$SLUG KEEP_RECORD=$RECORD
SLUG=gift-away RECORD=$EX/.lem/state/tasks/gift-away/decisions.jsonl
project --repo "$EX" task-dir "$SLUG" >/dev/null && project --repo "$EX" state "$SLUG" building 'lead: builder' >/dev/null
c6=$(ask "The note in the summary")
decide advise "$SLUG" "$c6" --expert fable --pick "after the price" --why "The accountant reads the price first." >/dev/null || true
decide advise "$SLUG" "$c6" --expert astra --pick "after the price" --why "A note beside the price is seen." >/dev/null || true
c7=$(ask "The note in the footer")
decide advise "$SLUG" "$c7" --expert fable --pick "after the price" --why "f" >/dev/null || true
decide advise "$SLUG" "$c7" --expert astra --pick "the last column" --why "a" >/dev/null || true
c8=$(ask "The note in the header")
decide advise "$SLUG" "$c8" --expert fable --pick "after the price" --why "f" >/dev/null || true
decide advise "$SLUG" "$c8" --expert astra --none --why "a" >/dev/null || true
c9=$(ask "The note's separator")
decide advise "$SLUG" "$c9" --expert fable --pick "after the price" --why "f" >/dev/null || true
c10=$(ask "The note's escape")
c11=$(ask "The note's quotes")
decide advise "$SLUG" "$c11" --expert fable --pick "after the price" --why "f" >/dev/null || true
decide advise "$SLUG" "$c11" --expert astra --pick "after the price" --why "a" >/dev/null || true
old_wait "$c11"
lateanswer=$(decide answer "$SLUG" "$c11" --chose "the last column" | field '(d["kind"], d["chose"])' || true)
with_him=$(decide away | field 'd["taken"]' || true)
old_mode "$SLUG" alone
taken=$(decide away | field '[(t["id"], t["chose"], t["by"]) for t in d["taken"]]' || true)
old_mode "$SLUG" with-owner
listed=$(one "$c6" | field '(d["state"], d["chose"], d["by"], d.get("early"), d["experts"], sorted(d["advice"]))' || true)
ended=$(decide wait "$SLUG" "$c6" --seconds 1 | field 'd["ended"]' || true)
untouched=$(decide list "$KEEP_SLUG" | field '[c["state"] for c in d if c["id"] in (1, 2)]' || true)
SLUG=$KEEP_SLUG RECORD=$KEEP_RECORD
if [ "$lateanswer" = "('answered', 'the last column')" ] && [ "$with_him" = "[]" ] \
  && [ "$taken" = "[($c6, 'after the price', 'experts'), ($c7, 'the last column', 'timeout'), ($c8, 'the last column', 'timeout'), ($c9, 'the last column', 'timeout'), ($c10, 'the last column', 'timeout')]" ] \
  && [ "$listed" = "('timeout', 'after the price', 'experts', True, {'fable': 'The accountant reads the price first.', 'astra': 'A note beside the price is seen.'}, ['astra', 'fable'])" ] \
  && [ "$ended" = "taken without the owner" ] && [ "$untouched" = "['waits', 'waits']" ]; then
  pass "a task that runs without the owner has each choice that waits taken: the experts' shared pick, by: experts with both reasons, marked early; when they split, one found none fits, one is missing or none advised, the recommended option; nothing of a task that runs with him; and a choice past an older Lem's deadline takes his answer as an answer"
else
  fail "the owner's away and the experts: $lateanswer / $with_him / $taken / $listed / $ended / $untouched"
fi

# A record of an older Lem: a `settled` line, which `settle --away` wrote, still reads as the experts' pick, and an answer
# after it is late. And a lead's wait on a choice with both experts' shared pick, when the task runs without the owner:
# the wait takes that pick at once, early; an irreversible step is never taken so.
c12=$(ask "The note's column name")
decide advise "$SLUG" "$c12" --expert fable --pick "after the price" --why "The accountant reads the price first." >/dev/null || true
decide advise "$SLUG" "$c12" --expert astra --pick "after the price" --why "A note beside the price is seen." >/dev/null || true
printf '{"id": %s, "at": "2026-11-17T10:00:00Z", "kind": "settled", "chose": "after the price", "by": "experts", "away": true, "experts": {"fable": "f", "astra": "a"}}\n' "$c12" >> "$RECORD"
stood=$(one "$c12" | field '(d["state"], d["chose"], d["by"], d["away"])' || true)
waitsays=$(decide wait "$SLUG" "$c12" --seconds 1 | field 'd["ended"]' || true)
gone=$(decide pending "$SLUG" | field "[c['id'] for c in d['waiting'] if c['id'] == $c12]" || true)
after=$(decide answer "$SLUG" "$c12" --chose "the last column" | field '(d["kind"], d["state"], d["taken"], "it is a correction" in d["next"])' || true)
c13=$(ask "The note's width")
decide advise "$SLUG" "$c13" --expert fable --pick "after the price" --why "f" >/dev/null || true
decide advise "$SLUG" "$c13" --expert astra --pick "after the price" --why "a" >/dev/null || true
c14=$(ask "Email the accountants about the column" --irreversible person)
old_mode "$SLUG" alone
early=$(decide wait "$SLUG" "$c13" --seconds 30 | field '(d["chose"], d["by"], d["early"], sorted(d["experts"]))' || true)
irreversible=$(decide wait "$SLUG" "$c14" --seconds 1 | field 'd["ended"]' || true)
others=$(decide list "$SLUG" | field '[c["state"] for c in d if c["id"] in (1, 2)]' || true)
old_mode "$SLUG" with-owner
if [ "$stood" = "('settled', 'after the price', 'experts', True)" ] && [ "$waitsays" = "settled by the experts while the owner was away" ] && [ "$gone" = "[]" ] \
  && [ "$after" = "('late', 'settled', 'after the price', True)" ] \
  && [ "$early" = "('after the price', 'experts', True, ['astra', 'fable'])" ] && [ "$irreversible" = "still waits" ] && [ "$others" = "['waits', 'waits']" ]; then
  pass "a settled line of an older Lem still reads as the experts' pick, and an answer after it is late; when the task runs without the owner, a wait takes the experts' shared pick of its own choice at once, marked early, and never an irreversible step"
else
  fail "an older settled line and a choice taken early: $stood / $waitsays / $gone / $after / $early / $irreversible / $others"
fi

# the skill's brief: the choice, the criteria, the plan and the files, in one file of the task's directory
c16=$(ask "Where the note goes in the second export")
nofile=$(experts brief "$SLUG" "$c16" --file missing.sh 2>&1 || true)
nofilecode=$(status_of experts brief "$SLUG" "$c16" --file missing.sh)
made=$(experts brief "$SLUG" "$c16" --file export.sh)
brief=$TASKDIR/experts/choice-$c16.brief.md
paths=$(field '(d["brief"], d["answers"]["fable"], d["answers"]["astra"], d["ask"], d["worktree"])' <<<"$made")
holds=yes
for want in "# Choice $c16 of $SLUG: the experts' brief" "Where the note goes in the second export" "1. the last column" "2. after the price" \
  "Recommended: the last column. Why: an import that reads the columns by place keeps working" \
  "What the personas said: The merchant picked the last column, the accountant after the price." \
  "The run that ends badly, as the lead derived it:" "1. An importer reads the export's columns by place (\`import.py:read_row\`)." \
  '3. The importer reads the note "for Ania" as the total of order 1042, and stops.' \
  "Why it can happen: The importer reads columns by place, and so does every reader that copies it." \
  "Size: full, because the export gets a new column." \
  '1. A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has that text in its row.' \
  '2. An order with no gift note has an empty cell, not the word "None".' \
  "\`$tree/docs/plans/20261116-$SLUG.md\`" "- $tree/export.sh" "Read only. Change no file" "    pick: ONE OPTION" "    none fits"; do
  grep -qF -- "$want" "$brief" || { holds="no: $want"; break; }
done
decide answer "$SLUG" "$c16" --chose "after the price" >/dev/null || true
answered=$(experts brief "$SLUG" "$c16" 2>&1 || true)
alladvised=$(experts brief "$SLUG" "$c2" 2>&1 || true)
c17=$(ask "Where the note goes in the third export" --irreversible data)
decide advise "$SLUG" "$c17" --expert fable --pick "the last column" --why "f" >/dev/null || true
rest=$(experts brief "$SLUG" "$c17" | field '(d["ask"], d["advised"])' || true)
forbrief=$(grep -c "cannot be undone by a later \"no\" (data)" "$TASKDIR/experts/choice-$c17.brief.md" || true)
if [ "$holds" = yes ] && [ "$paths" = "('$brief', '$TASKDIR/experts/choice-$c16.fable.md', '$TASKDIR/experts/choice-$c16.astra.md', ['fable', 'astra'], '$tree')" ] \
  && grep -qF -- "--file missing.sh is not in the task's worktree" <<<"$nofile" && [ "$nofilecode" = 1 ] \
  && grep -qF "choice $c16 of $SLUG does not wait: it is answered" <<<"$answered" && grep -qF "has the advice of both experts already" <<<"$alladvised" \
  && [ "$rest" = "(['astra'], ['fable'])" ] && [ "$forbrief" = 1 ]; then
  pass "the skill's brief file holds the choice word for word, the run that ends badly with its cause, the recommended option and the personas, the task's criteria and its plan, the files the choice is about and the answer's form; it names the experts still to ask, and is refused for a choice that does not wait or that both advised"
else
  fail "the experts' brief: $holds / $paths / $nofile / $answered / $alladvised / $rest / $forbrief"
fi

# record: an expert's last message, in the brief's form, goes into the record through advise
c18=$(ask "Where the note goes in the fourth export")
experts brief "$SLUG" "$c18" >/dev/null || true
answers=$TASKDIR/experts
absent=$(experts record "$SLUG" "$c18" --expert fable 2>&1 || true)
printf '%s\n' '**My answer**' 'after the price, I think' > "$answers/choice-$c18.fable.md"
badform=$(experts record "$SLUG" "$c18" --expert fable 2>&1 || true)
printf 'pick: after the price\nwhy: caf\351.\n' > "$answers/choice-$c18.fable.md"
latin=$(experts record "$SLUG" "$c18" --expert fable 2>&1 || true)
printf '%s\n' 'pick: the first column' 'why: It reads first.' > "$answers/choice-$c18.fable.md"
noption=$(experts record "$SLUG" "$c18" --expert fable 2>&1 || true)
printf '%s\n' 'pick: after the price' 'why: The accountant reads the price first.' '  A note beside it is seen.' > "$answers/choice-$c18.fable.md"
fabled=$(experts record "$SLUG" "$c18" --expert fable | field '(d["expert"], d["pick"], d["why"])' || true)
printf '%s\n' 'None fits' 'why: Both break an import.' > "$answers/choice-$c18.astra.md"
astrad=$(experts record "$SLUG" "$c18" --expert astra | field '(d["expert"], d.get("none"), d["experts_pick"])' || true)
# the refusal says what the skill allows: one more ask with the same brief, then nothing recorded for that expert
if grep -qF "choice-$c18.fable.md is not there" <<<"$absent" && grep -qF "is not an answer in the brief's form" <<<"$badform" \
  && grep -qF "choice-$c18.fable.md is not UTF-8 text" <<<"$latin" && ! grep -q Traceback <<<"$latin" \
  && grep -qF "Ask fable once more with the same brief" <<<"$badform" && grep -qF "record nothing for fable" <<<"$badform" && ! grep -qF "lem decisions advise" <<<"$badform" \
  && grep -qF "the pick of an expert is one of the options of choice $c18, word for word" <<<"$noption" \
  && [ "$fabled" = "('fable', 'after the price', 'The accountant reads the price first. A note beside it is seen.')" ] \
  && [ "$astrad" = "('astra', True, None)" ] && [ "$(advised_lines "$c18")" = 2 ]; then
  pass "record writes an expert's answer file into the record through advise: an answer not in the brief's form, a pick that is no option and a missing file are refused"
else
  fail "record: $absent / $badform / $noption / $fabled / $astrad"
fi

# a question in words: a folder of its own in the state folder, with the brief, the answers and a short record
QS=$EX/.lem/state/experts
asked=$(experts brief --question "Which store for the sessions?" --context "Sessions live in process memory, so every deploy logs everyone out." \
  --option "Redis" --option "a Postgres table" --file export.sh || true)
folder=$(field 'd["folder"]' <<<"$asked" 2>/dev/null || true)
# made by brief; made here only so that a brief that failed shows as a FAIL line and does not stop the suite
mkdir -p "$QS/$folder"
shape=$(field '(d["dir"] == d["brief"].rsplit("/", 1)[0], [(e["name"], e["seat"], e["agent"], e["model"], e["effort"]) for e in d["experts"]], d["ask"], d["worktree"], d["answers"]["astra"].endswith("/astra.md"))' <<<"$asked" 2>/dev/null || true)
holds=yes
for want in "# A question for the experts" "Which store for the sessions?" "## What is being decided" "Sessions live in process memory, so every deploy logs everyone out." \
  "1. Redis" "2. a Postgres table" "- $EX/export.sh" "Read only. Change no file" "    pick: ONE OPTION, COPIED WORD FOR WORD FROM THE OPTIONS ABOVE" "    none fits"; do
  grep -qF -- "$want" "$QS/$folder/brief.md" 2>/dev/null || { holds="no: $want"; break; }
done
printf '%s\n' 'pick: Memcached' 'why: It is fast.' > "$QS/$folder/fable.md"
noption=$(experts record --folder "$folder" --expert fable 2>&1 || true)
printf '%s\n' 'answer: Redis' 'why: It runs already.' > "$QS/$folder/fable.md"
badform=$(experts record --folder "$folder" --expert fable 2>&1 || true)
stranger=$(experts record --folder "$folder" --expert opus 2>&1 || true)
printf '%s\n' 'pick: Redis' 'why: It runs already for the job queue.' > "$QS/$folder/fable.md"
half=$(experts record --folder "$folder" --expert fable | field '(d["answers"]["fable"]["pick"], d["waiting"], d["agree"], "astra" in d["next"])' || true)
twice=$(experts record --folder "$folder" --expert fable 2>&1 || true)
printf '%s\n' 'pick: Redis' 'why: A key with an expiry is what a session is.' > "$QS/$folder/astra.md"
whole=$(experts record --folder "$folder" --expert astra | field '(d["agree"], d["waiting"], sorted(d["answers"]), "all picked" in d["next"])' || true)
kept=$(field '(d["question"], d["options"], sorted(d["answers"]))' < "$QS/$folder/record.json" || true)
if [ "$(dirname "$QS/$folder")" = "$QS" ] && [ "$holds" = yes ] && [ -z "$(git -C "$EX" status --porcelain --untracked-files=all)" ] \
  && [ "$shape" = "(True, [('fable', 'claude/fable:high', 'claude', 'fable', 'high'), ('astra', 'codex/gpt-6.2-astra:high', 'codex', 'gpt-6.2-astra', 'high')], ['fable', 'astra'], '$EX', True)" ] \
  && grep -qF "'Memcached' is none of them" <<<"$noption" && grep -qF "is not an answer in the brief's form" <<<"$badform" \
  && grep -qF -- "--expert opus is none of this question's experts (fable, astra)" <<<"$stranger" && grep -qF "fable answered question $folder already" <<<"$twice" \
  && [ "$half" = "('Redis', ['astra'], None, True)" ] && [ "$whole" = "('Redis', [], ['astra', 'fable'], True)" ] \
  && [ "$kept" = "('Which store for the sessions?', ['Redis', 'a Postgres table'], ['astra', 'fable'])" ]; then
  pass "a question in words gets a folder of its own in the state folder, which git does not show: the brief holds the question, what is decided, the options and the files; the default experts are fable and astra by their seats; record takes each answer once, refuses a pick that is no option, a wrong form and a stranger, and says when all share a pick"
else
  fail "a question in words: $folder / $holds / $shape / $noption / $badform / $stranger / $half / $twice / $whole / $kept"
fi

# an open question has no options: the answer is in words, and two answers that differ are no split the script can see
open=$(experts brief --question "What would be the best solution for sessions that die at each deploy?" || true)
ofolder=$(field 'd["folder"]' <<<"$open" 2>/dev/null || true)
mkdir -p "$QS/$ofolder"
oform=$(grep -c "    answer: one to three sentences" "$QS/$ofolder/brief.md" 2>/dev/null || true)
printf '%s\n' 'pick: Redis' 'why: It runs already.' > "$QS/$ofolder/fable.md"
opick=$(experts record --folder "$ofolder" --expert fable 2>&1 || true)
printf '%s\n' 'answer: Keep sessions in Redis,' '  with an expiry on each key.' 'why: It runs already.' > "$QS/$ofolder/fable.md"
printf '%s\n' 'answer: A signed cookie.' 'why: No store to run.' > "$QS/$ofolder/astra.md"
experts record --folder "$ofolder" --expert fable >/dev/null || true
oboth=$(experts record --folder "$ofolder" --expert astra | field '(d["answers"]["fable"]["answer"], d["answers"]["astra"]["answer"], d["agree"], d["waiting"], "where they agree and where they split" in d["next"])' || true)
if [ "$oform" = 1 ] && grep -qF "is not an answer in the brief's form (\`answer: ...\`, then \`why: ...\`)" <<<"$opick" \
  && [ "$oboth" = "('Keep sessions in Redis, with an expiry on each key.', 'A signed cookie.', None, [], True)" ] && [[ "$ofolder" == *-what-would-be-the-best-solution ]]; then
  pass "an open question asks for an answer in words, refuses a pick, and leaves the comparison of two answers to the skill"
else
  fail "an open question: $ofolder / $oform / $opick / $oboth"
fi

# who the experts are: --seat names them for one call, and a seat that does not read is refused
seated=$(experts brief --question "Which store?" --seat claude/opus:high --seat codex/gpt-6.1-sol:xhigh | field '[(e["name"], e["model"], e["effort"]) for e in d["experts"]]' || true)
noform=$(experts brief --question "Which store?" --seat claude-opus 2>&1 || true)
noagent=$(experts brief --question "Which store?" --seat gemini/pro:high --seat claude/fable:high 2>&1 || true)
same=$(experts brief --question "Which store?" --seat claude/fable:high --seat claude/fable:max 2>&1 || true)
nochoice=$(experts brief "$SLUG" "$c18" --seat claude/opus:high 2>&1 || true)
neither=$(experts brief 2>&1 || true)
both=$(experts brief "$SLUG" "$c18" --question "Which store?" 2>&1 || true)
alone=$(experts brief --question "Which store?" --option "Redis" 2>&1 || true)
mixed=$(experts brief "$SLUG" "$c18" --option "Redis" --option "a table" 2>&1 || true)
if [ "$seated" = "[('opus', 'opus', 'high'), ('sol', 'gpt-6.1-sol', 'xhigh')]" ] && grep -qF "'claude-opus' is no seat: write it as agent/model:effort" <<<"$noform" \
  && grep -qF "names the agent 'gemini': an expert is started by claude or codex" <<<"$noagent" && grep -qF "two experts are named fable" <<<"$same" \
  && grep -qF "a choice of a task has 2 experts, and its record keeps their advice as fable and astra: give --seat 2 times" <<<"$nochoice" \
  && grep -qF "brief takes a task's SLUG N or --question TEXT, one of the two" <<<"$neither" && grep -qF "one of the two" <<<"$both" \
  && grep -qF "one --option is no choice" <<<"$alone" && grep -qF -- "--context and --option belong to a question in words" <<<"$mixed"; then
  pass "--seat names the experts for one call, by the last word of each model; a seat not written agent/model:effort, an agent the harness does not know, two experts of one name, one --seat for a task's choice and a brief with no question or two are refused"
else
  fail "the experts' seats: $seated / $noform / $noagent / $same / $nochoice / $neither / $both / $alone / $mixed"
fi

# the folders of questions in words go after 30 days without a write, at the next brief; other files in the folder stay
"$PY" -c 'import os, sys, time
old = time.time() - 31 * 86400
for root, dirs, files in os.walk(sys.argv[1]):
    for name in files: os.utime(os.path.join(root, name), (old, old))
os.utime(sys.argv[1], (old, old))' "$QS/$folder"
mkdir -p "$QS/notes" && "$PY" -c 'import os, sys, time; old = time.time() - 40 * 86400; os.utime(sys.argv[1], (old, old))' "$QS/notes"
pruned=$(experts brief --question "Which store, once more?" | field 'd["removed"]' || true)
if [ "$pruned" = "['$folder']" ] && [ ! -e "$QS/$folder" ] && [ -d "$QS/$ofolder" ] && [ -d "$QS/notes" ]; then
  pass "a question's folder is removed at the next brief once 30 days passed since its last write, and a newer one and a folder of another name stay"
else
  fail "the old folders: $pruned / $(ls "$QS")"
fi
# who the experts are: the settings' seats.experts, which experts.py reads through project.py show, the project's and
# this machine's own; a choice of a task names each by its place in the record, whatever model sits there
seats_in() { "$PY" -I -c 'import re, sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(re.sub(r"(?m)^experts = .*$", "experts = " + sys.argv[2], s, count=1))' "$EX/.lem/project.toml" "$1"; }
# Lem reads the settings as the base branch's commit has them, so an edit counts once it is committed
settings_committed() { git -C "$EX" add .lem/project.toml && git -C "$EX" -c user.name=t -c user.email=t@t commit -q --allow-empty -m "chore: the settings" -- .lem/project.toml; }
cp "$EX/.lem/project.toml" "$WORK/project.toml"
seats_in '["claude/opus:high", "codex/gpt-6.1-sol"]'
settings_committed
tracked=$(experts brief --question "Which store, by the project's seats?" | field '[(e["name"], e["agent"], e["model"], e["effort"], e["place"]) for e in d["experts"]]' || true)
cS=$(ask "Where the note goes, by the project's seats")
forchoice=$(experts brief "$SLUG" "$cS" | field '([(e["name"], e["seat"], e["model"], e["effort"], e["answer"].rsplit("/", 1)[1]) for e in d["experts"]], d["ask"])' || true)
printf '%s\n' 'pick: the last column' 'why: An import reads the columns by place.' > "$TASKDIR/experts/choice-$cS.fable.md"
recorded=$(experts record "$SLUG" "$cS" --expert fable | field 'd["advised"]' || true)
printf '%s\n' '[seats]' 'experts = ["claude", "codex:xhigh"]' > "$EX/.lem/project.local.toml"
nomodel=$(experts brief "$SLUG" "$cS" | field '([(e["name"], e["agent"], e["model"], e["effort"]) for e in d["experts"]], d["ask"])' || true)
nomodelq=$(experts brief --question "Which store, by this machine's seats?" | field '[e["name"] for e in d["experts"]]' || true)
rm "$EX/.lem/project.local.toml"
givenchoice=$(experts brief "$SLUG" "$cS" --seat claude/opus:high --seat codex/gpt-6-astra | field '[(e["name"], e["model"]) for e in d["experts"]]' || true)
# one model in both places is two experts still: a choice names them by place, so no name is taken twice
oneboth=$(experts brief "$SLUG" "$cS" --seat claude/fable:high --seat codex/fable | field '[e["name"] for e in d["experts"]]' || true)
cp "$WORK/project.toml" "$EX/.lem/project.toml"
settings_committed
places=$("$PY" -B -c 'import sys; sys.path.insert(0, sys.argv[1]); import decisions, project; print(decisions.EXPERTS == project.EXPERT_PLACES, project.EXPERT_PLACES)' "$PWD/skills/lem/scripts")
if [ "$tracked" = "[('opus', 'claude', 'opus', 'high', 'fable'), ('sol', 'codex', 'gpt-6.1-sol', None, 'astra')]" ] \
  && [ "$forchoice" = "([('fable', 'claude/opus:high', 'opus', 'high', 'choice-$cS.fable.md'), ('astra', 'codex/gpt-6.1-sol', 'gpt-6.1-sol', None, 'choice-$cS.astra.md')], ['fable', 'astra'])" ] \
  && [ "$recorded" = "['fable']" ] && [ "$nomodel" = "([('fable', 'claude', None, None), ('astra', 'codex', None, 'xhigh')], ['astra'])" ] \
  && [ "$nomodelq" = "['fable', 'astra']" ] && [ "$givenchoice" = "[('fable', 'opus'), ('astra', 'gpt-6-astra')]" ] && [ "$oneboth" = "['fable', 'astra']" ] && [ "$places" = "True ('fable', 'astra')" ]; then
  pass "the experts are the settings' seats.experts, the project's or this machine's, each with its agent, model and effort; a choice of a task names the first fable and the second astra whatever model sits there, records the advice under that place, and takes a seat with no model; a question in words names each by its model"
else
  fail "the experts from the settings: $tracked / $forchoice / $recorded / $nomodel / $nomodelq / $givenchoice / $oneboth / $places"
fi

if [ -d "$PWD/skills/lem/scripts/__pycache__" ] || [ -d "$(dirname "$EXPERTS")/__pycache__" ]; then fail "experts.py left a __pycache__"; else pass "experts.py left no __pycache__, also of the decisions.py it imports"; fi

if [ "$fails" -gt 0 ]; then
  echo "$fails failed"
  exit 1
fi
echo "all passed"
