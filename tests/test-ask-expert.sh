#!/usr/bin/env bash
# The experts of a choice that waits for the owner, offline: decisions.py keeps each expert's
# advice under the task's lock and refuses a pick that is no option; the end of the wait takes the
# experts' shared pick, and the recommended option when they split; settle --away takes the shared
# pick before the wait ends, never for an irreversible step; and the lem-ask-expert skill's
# brief file holds the choice and the stories. No expert runs here.
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
printf '%s\n' '# The export has the gift note' '' '## Stories' '' 'Kind: feature, because the export gets a new column.' '' \
  '1. A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has that text in its row.' \
  '2. An order with no gift note has an empty cell, not the word "None".' '' '## Tasks' '' '1. The column.' > "$tree/docs/plans/20261116-$SLUG.md"
git -C "$tree" add -A && git -C "$tree" commit -q -m "docs: the plan"
TASKDIR=$EX/.git/lem/tasks/$SLUG
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
# past ID...: the wait of each choice ends, as its deadline is written into the past, the way fifteen minutes later would find it
past() { "$PY" -c 'import json, sys
lines = [json.loads(line) for line in open(sys.argv[1])]
for line in lines:
    if line["kind"] == "asked" and str(line["id"]) in sys.argv[2:]: line["deadline"] = "2026-01-01T00:00:00Z"
open(sys.argv[1], "w").write("".join(json.dumps(line) + "\n" for line in lines))' "$RECORD" "$@"; }
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
events=$(grep -c '"event": "decision.advised", "task": "gift-note"' "$EX/.git/lem/events.jsonl" || true)
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

# advice comes before the wait ends, and only for a choice that waits; an irreversible step takes advice at any time
c3=$(ask "The note's font")
past "$c3"
late=$(decide advise "$SLUG" "$c3" --expert fable --pick "after the price" --why "w" 2>&1 || true)
c4=$(ask "Email the merchants about the column" --irreversible person)
past "$c4"
forever=$(decide advise "$SLUG" "$c4" --expert fable --pick "after the price" --why "The merchants read the email." | field 'd["kind"]' || true)
c5=$(ask "The note's length")
decide answer "$SLUG" "$c5" --chose "the last column" >/dev/null || true
over=$(decide advise "$SLUG" "$c5" --expert fable --pick "after the price" --why "w" 2>&1 || true)
if grep -qF "the wait of choice $c3 ended at 2026-01-01T00:00:00Z: advice after it changes nothing" <<<"$late" && [ "$(advised_lines "$c3")" = 0 ] \
  && [ "$forever" = advised ] && grep -qF "choice $c5 does not wait: it is answered, with 'the last column'; advice on it changes nothing" <<<"$over"; then
  pass "advice after the wait ended is refused, so what the timeout takes does not depend on when it is written; an irreversible step takes advice with no end, and an answered choice takes none"
else
  fail "advice and the wait: $late / $forever / $over"
fi

# timeout: the experts' shared pick at the end of the wait, the recommended option when they split, one found none fits, or one is missing
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
early=$(decide timeout "$SLUG" "$c6" 2>&1 || true)
past "$c6" "$c7" "$c8" "$c9" "$c10"
waited=$(decide wait "$SLUG" "$c6" --seconds 5 | field '(d["ended"], d["experts_pick"], "shared pick" in d["next"])' || true)
shared=$(decide timeout "$SLUG" "$c6" | field '(d["chose"], d["by"], d["experts"])' || true)
split=$(decide timeout "$SLUG" "$c7" | field '(d["chose"], d["by"], "experts" in d)' || true)
none=$(decide timeout "$SLUG" "$c8" | field '(d["chose"], d["by"])' || true)
missing=$(decide timeout "$SLUG" "$c9" | field '(d["chose"], d["by"])' || true)
plain=$(decide timeout "$SLUG" "$c10" | field '(d["chose"], d["by"])' || true)
listed=$(one "$c6" | field '(d["state"], d["chose"], d["by"], sorted(d["experts"]), sorted(d["advice"]))' || true)
ended=$(decide wait "$SLUG" "$c6" --seconds 1 | field 'd["ended"]' || true)
if grep -q "the wait of choice $c6 has [0-9]* seconds left" <<<"$early" && [ "$waited" = "('the wait is over', 'after the price', True)" ] \
  && [ "$shared" = "('after the price', 'experts', {'fable': 'The accountant reads the price first.', 'astra': 'A note beside the price is seen.'})" ] \
  && [ "$split" = "('the last column', 'timeout', False)" ] && [ "$none" = "('the last column', 'timeout')" ] \
  && [ "$missing" = "('the last column', 'timeout')" ] && [ "$plain" = "('the last column', 'timeout')" ] \
  && [ "$listed" = "('timeout', 'after the price', 'experts', ['astra', 'fable'], ['astra', 'fable'])" ] \
  && [ "$ended" = "taken by timeout, with the experts' shared pick" ]; then
  pass "at the end of the wait the timeout takes the experts' shared pick, by: experts with both reasons; when they split, one found none fits, one is missing or none advised, it takes the recommended option, by: timeout"
else
  fail "timeout and the experts: $early / $waited / $shared / $split / $none / $missing / $plain / $listed / $ended"
fi

# an answer after the wait with no timeout written: the timeout that goes in with it takes the experts' shared pick too
c11=$(ask "The note's quotes")
decide advise "$SLUG" "$c11" --expert fable --pick "after the price" --why "f" >/dev/null || true
decide advise "$SLUG" "$c11" --expert astra --pick "after the price" --why "a" >/dev/null || true
past "$c11"
lateanswer=$(decide answer "$SLUG" "$c11" --chose "the last column" | field '(d["kind"], d["state"], d["taken"], d["timeout_written"], "it is a correction" in d["next"])' || true)
written=$(grep "\"id\": $c11, .*\"kind\": \"timeout\"" "$RECORD" | field '(d["chose"], d["by"])' || true)
if [ "$lateanswer" = "('late', 'timeout', 'after the price', True, True)" ] && [ "$written" = "('after the price', 'experts')" ]; then
  pass "an answer after the wait, before anybody wrote the timeout, writes the timeout with the experts' shared pick, and an answer that differs is a correction"
else
  fail "a late answer and the experts: $lateanswer / $written"
fi

# settle --away: the shared pick before the deadline; refused when they split, for an irreversible step, and after the deadline
c12=$(ask "The note's column name")
decide advise "$SLUG" "$c12" --expert fable --pick "after the price" --why "The accountant reads the price first." >/dev/null || true
noaway=$(decide settle "$SLUG" "$c12" 2>&1 || true)
noawaycode=$(status_of decide settle "$SLUG" "$c12")
halfway=$(decide settle "$SLUG" "$c12" --away 2>&1 || true)
decide advise "$SLUG" "$c12" --expert astra --pick "after the price" --why "A note beside the price is seen." >/dev/null || true
settled=$(decide settle "$SLUG" "$c12" --away | field '(d["kind"], d["chose"], d["by"], d["away"], sorted(d["experts"]))' || true)
twice=$(decide settle "$SLUG" "$c12" --away 2>&1 || true)
stood=$(one "$c12" | field '(d["state"], d["chose"], d["by"], d["away"])' || true)
waitsays=$(decide wait "$SLUG" "$c12" --seconds 1 | field 'd["ended"]' || true)
gone=$(decide pending "$SLUG" | field "[c['id'] for c in d['waiting'] if c['id'] == $c12]" || true)
after=$(decide answer "$SLUG" "$c12" --chose "the last column" | field '(d["kind"], d["state"], d["taken"], d["timeout_written"], "it is a correction" in d["next"])' || true)
c13=$(ask "The note's width")
decide advise "$SLUG" "$c13" --expert fable --pick "after the price" --why "f" >/dev/null || true
decide advise "$SLUG" "$c13" --expert astra --pick "the last column" --why "a" >/dev/null || true
splitaway=$(decide settle "$SLUG" "$c13" --away 2>&1 || true)
splitcode=$(status_of decide settle "$SLUG" "$c13" --away)
c14=$(ask "Email the accountants about the column" --irreversible person)
decide advise "$SLUG" "$c14" --expert fable --pick "after the price" --why "f" >/dev/null || true
decide advise "$SLUG" "$c14" --expert astra --pick "after the price" --why "a" >/dev/null || true
irreversible=$(decide settle "$SLUG" "$c14" --away 2>&1 || true)
past "$c14"
irrtimeout=$(decide timeout "$SLUG" "$c14" 2>&1 || true)
c15=$(ask "The note's language")
decide advise "$SLUG" "$c15" --expert fable --pick "after the price" --why "f" >/dev/null || true
decide advise "$SLUG" "$c15" --expert astra --pick "after the price" --why "a" >/dev/null || true
past "$c15"
overaway=$(decide settle "$SLUG" "$c15" --away 2>&1 || true)
thentimeout=$(decide timeout "$SLUG" "$c15" | field '(d["chose"], d["by"])' || true)
if grep -qF "add --away when his own words or his away channel say so" <<<"$noaway" && [ "$noawaycode" = 1 ] \
  && grep -qF "the experts have no shared pick for choice $c12 (fable: after the price; no advice of astra yet): settle it again when both advised" <<<"$halfway" \
  && [ "$settled" = "('settled', 'after the price', 'experts', True, ['astra', 'fable'])" ] \
  && grep -qF "choice $c12 does not wait: it is settled, with 'after the price'" <<<"$twice" \
  && [ "$stood" = "('settled', 'after the price', 'experts', True)" ] && [ "$waitsays" = "settled by the experts while the owner is away" ] && [ "$gone" = "[]" ] \
  && [ "$after" = "('late', 'settled', 'after the price', False, True)" ] \
  && grep -qF "the experts have no shared pick for choice $c13 (fable: after the price; astra: the last column): it waits its time" <<<"$splitaway" && [ "$splitcode" = 1 ] \
  && [ "$(one "$c13" | field 'd["state"]')" = waits ] \
  && grep -qF "choice $c14 is a step that a later \"no\" cannot reverse (it sends something to a person): the experts never take it" <<<"$irreversible" \
  && grep -qF "choice $c14 is a step that a later \"no\" cannot reverse (it sends something to a person): no timeout takes it" <<<"$irrtimeout" \
  && [ "$(one "$c14" | field '(d["state"], sorted(d["advice"]))')" = "('waits', ['astra', 'fable'])" ] \
  && grep -qF "the wait of choice $c15 ended at 2026-01-01T00:00:00Z: \`decisions.py timeout $SLUG $c15\` takes it" <<<"$overaway" \
  && [ "$thentimeout" = "('after the price', 'experts')" ]; then
  pass "settle --away takes the experts' shared pick before the wait ends, once, and an answer after it is late; it is refused without --away, with one expert or a split, for an irreversible step (which no timeout takes either) and after the deadline, where the timeout takes the shared pick"
else
  fail "settle --away: $noaway / $halfway / $settled / $twice / $stood / $waitsays / $gone / $after / $splitaway / $irreversible / $irrtimeout / $overaway / $thentimeout"
fi

# the skill's brief: the choice, the stories, the plan and the files, in one file of the task's directory
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
  "Kind: feature, because the export gets a new column." \
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
  pass "the skill's brief file holds the choice word for word, the run that ends badly with its cause, the recommended option and the personas, the task's stories and its plan, the files the choice is about and the answer's form; it names the experts still to ask, and is refused for a choice that does not wait or that both advised"
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
printf '%s\n' 'pick: the first column' 'why: It reads first.' > "$answers/choice-$c18.fable.md"
noption=$(experts record "$SLUG" "$c18" --expert fable 2>&1 || true)
printf '%s\n' 'pick: after the price' 'why: The accountant reads the price first.' '  A note beside it is seen.' > "$answers/choice-$c18.fable.md"
fabled=$(experts record "$SLUG" "$c18" --expert fable | field '(d["expert"], d["pick"], d["why"])' || true)
printf '%s\n' 'None fits' 'why: Both break an import.' > "$answers/choice-$c18.astra.md"
astrad=$(experts record "$SLUG" "$c18" --expert astra | field '(d["expert"], d.get("none"), d["experts_pick"])' || true)
# the refusal says what the skill allows: one more ask with the same brief, then nothing recorded for that expert
if grep -qF "choice-$c18.fable.md is not there" <<<"$absent" && grep -qF "is not an answer in the brief's form" <<<"$badform" \
  && grep -qF "Ask fable once more with the same brief" <<<"$badform" && grep -qF "record nothing for fable" <<<"$badform" && ! grep -qF "decisions.py advise" <<<"$badform" \
  && grep -qF "the pick of an expert is one of the options of choice $c18, word for word" <<<"$noption" \
  && [ "$fabled" = "('fable', 'after the price', 'The accountant reads the price first. A note beside it is seen.')" ] \
  && [ "$astrad" = "('astra', True, None)" ] && [ "$(advised_lines "$c18")" = 2 ]; then
  pass "record writes an expert's answer file into the record through advise: an answer not in the brief's form, a pick that is no option and a missing file are refused"
else
  fail "record: $absent / $badform / $noption / $fabled / $astrad"
fi

if [ "$fails" -gt 0 ]; then
  echo "$fails failed"
  exit 1
fi
echo "all passed"
