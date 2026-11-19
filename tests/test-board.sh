#!/usr/bin/env bash
# Lem's board, offline: one repository whose tasks stand in every lane, written with Lem's own
# scripts (project.py state and log, decisions.py, criteria.py), and the pages headless Chrome draws
# from it: the lanes, each task for the owner with where he answers, and the board of one task with
# its decisions, the approval and read of its criteria, and where its time went.
#
# A real run writes its events minutes apart, and a test writes them in seconds, so the events of
# two tasks get their times moved afterwards (`retime`), the way a run would have spaced them. The
# scripts wrote every other field. LEM_BOARD_SHOTS=DIR also writes pictures of the pages there,
# over the same tasks marked as examples (board.py --demo), at 900, 1400 and 1800 px in a light and a
# dark theme, and prints where the lanes start on a 1400 x 900 window. The README's pictures are of
# a normal afternoon instead: tests/board-showcase.py.
set -eEuo pipefail

cd "$(dirname "$0")/.."
# shellcheck source-path=SCRIPTDIR source=checks.sh
. tests/checks.sh
collected
SCRIPTS=$PWD/skills/lem/scripts
WORK=$(cd "$(mktemp -d)" && pwd -P)
trap 'stopped; rm -rf "$WORK"' EXIT
PY=$(python3 -I -c 'import sys; print(sys.executable)')
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
# A stand-in for Codex on PATH, so that both experts of the default seats answer here (`here` in `lem project show`),
# whatever this machine has.
mkdir -p "$WORK/standin" && printf '%s\n' '#!/bin/sh' 'exit 0' > "$WORK/standin/codex" && chmod +x "$WORK/standin/codex"
export PATH="$WORK/standin:$PATH"

R=$WORK/shop
STATE=$R/.lem/state
project() { "$PY" -B "$SCRIPTS/project.py" --repo "$R" "$@"; }
decide() { "$PY" -B "$SCRIPTS/decisions.py" --repo "$R" "$@"; }
# CASE: the run that ends badly, which every choice for the owner carries above his card
CASE=(--case $'1. Order 1042 has the gift note "for Ania".\n2. The export writes the note where the choice puts it.\n3. A reader that takes the columns by place reads the note as the total.'
  --case-was derived --cause "Readers of the export take its columns by place.")
criteria() { "$PY" -B "$SCRIPTS/criteria.py" --repo "$R" "$@"; }
board() { env -u AGTERM_SESSION_ID -u AGTERM_SOCKET -u AGT_SESSION_ID -u AGT_SOCKET "$PY" -B "$SCRIPTS/board.py" --repo "$R" "$@"; }
field() { "$PY" -c 'import json, sys; d = json.load(sys.stdin); print(eval(sys.argv[1], {"d": d}))' "$1"; }
task() { project task-dir "$1" --ask "$2" >/dev/null; }

git init -q -b main "$R" && git -C "$R" config user.name t && git -C "$R" config user.email t@t
echo one > "$R/app.txt" && git -C "$R" add -A && git -C "$R" commit -q -m "chore: start"
project init --base main >/dev/null
# two gate commands: one run of the gate is both, on one tip
"$PY" -I -c 'import re, sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(re.sub(r"(?m)^commands = \[\]$", "commands = [\"make test\", \"make lint\"]", s, count=1))' "$R/.lem/project.toml"
grep -q '^commands = \["make test", "make lint"\]$' "$R/.lem/project.toml" || { printf 'FAIL the fixture: the settings got no gate commands\n'; exit 1; }
git -C "$R" add -A && git -C "$R" commit -q -m "chore: the settings"

# retime SLUG BASE MINUTES...: the events of one task, in the order the scripts wrote them, get the
# times BASE + MINUTES (BASE is an ISO time, or `now`). A decision's own time moves with its event.
#
# `now` is one fixed moment, NOW, the next whole minute after the last event of the fixture, and the
# pages are drawn with their clock stopped at it (draw). So a count-down or a share of an open task
# reads the same on a fast run and on a loaded one. Each retime is noted where its task's events end
# and run once NOW is known, before the board is written.
RETIME=$(cat <<'PY'
import json, sys
from datetime import datetime, timedelta, timezone
log, now, slug, base, *minutes = sys.argv[1:]
start = datetime.strptime(now if base == "now" else base, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
rows = [json.loads(line) for line in open(log, encoding="utf-8") if line.strip()]
mine = [row for row in rows if row["task"] == slug]
if len(mine) != len(minutes):
    sys.exit(f"retime: {slug} has {len(mine)} events and {len(minutes)} times were given: {[row['event'] for row in mine]}")
iso = lambda moment: moment.strftime("%Y-%m-%dT%H:%M:%SZ")
for row, offset in zip(mine, minutes):
    moment = start + timedelta(minutes=float(offset))
    row["ts"] = iso(moment)
    if row["event"].startswith("decision."):
        row["at"] = iso(moment)
open(log, "w", encoding="utf-8").write("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
open(log.removesuffix("jsonl") + "js", "w", encoding="utf-8").write("".join(f"lemEvent({json.dumps(row, ensure_ascii=False)});\n" for row in rows))
PY
)
retime() { printf '%s\n' "$*" >> "$WORK/retimes"; }
retime_all() {
  local args
  while read -r -a args; do "$PY" -I -c "$RETIME" "$STATE/events.jsonl" "$NOW" "${args[@]}"; done < "$WORK/retimes"
}
# taken SLUG ID...: each choice as decisions.py takes it while its task runs without the owner (`ending`), in its
# record and in the event log: a `timeout` line marked early, with the experts' shared pick, or the recommended option
# when they split. Written here, so that only these choices of the task go and the rest still wait.
TAKEN=$(cat <<'PY'
import json, sys
from datetime import datetime, timezone
state, slug, *ids = sys.argv[1:]
record, log = f"{state}/tasks/{slug}/decisions.jsonl", f"{state}/events.jsonl"
lines = [json.loads(line) for line in open(record, encoding="utf-8")]
events = [json.loads(line) for line in open(log, encoding="utf-8") if line.strip()]
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
for number in map(int, ids):
    asked = next(line for line in lines if line["kind"] == "asked" and line["id"] == number)
    advice = {line["expert"]: line for line in lines if line["kind"] == "advised" and line["id"] == number}
    picks = {one.get("pick") for one in advice.values()}
    shared = len(advice) == 2 and len(picks) == 1 and None not in picks
    end = {"id": number, "at": now, "kind": "timeout", "chose": next(iter(picks)) if shared else asked["recommended"], "by": "experts" if shared else "timeout"}
    if shared:
        end["experts"] = {name: advice[name]["why"] for name in ("fable", "astra")}
    end["early"] = True
    lines.append(end)
    events.append({"ts": now, "event": "decision.timeout", "task": slug, **{key: value for key, value in end.items() if key != "kind"}})
open(record, "w", encoding="utf-8").write("".join(json.dumps(line, ensure_ascii=False) + "\n" for line in lines))
open(log, "w", encoding="utf-8").write("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in events))
open(log.removesuffix("jsonl") + "js", "w", encoding="utf-8").write("".join(f"lemEvent({json.dumps(row, ensure_ascii=False)});\n" for row in events))
PY
)
taken() { "$PY" -I -c "$TAKEN" "$STATE" "$@"; }
# criteria_file FILE SIZE: the criteria the owner approves, in the form `lem criteria --help` gives
criteria_file() {
  if [ "$2" = small ]; then
    printf '%s\n' '## Acceptance criteria' '' 'Size: small, because the request is one sentence.' '' '1. The footer says "Terms", not "Terms and condtions".' > "$1"
  else
    printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the export gets a new column and two readers of it.' '' \
      '1. A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has that text in its row.' \
      '2. An order with no gift note has an empty cell, not the word "None".' > "$1"
  fi
}

# The task with the decisions: criteria read and approved, a build with a choice of each kind.
G=gift-note-export
task "$G" "Add the gift note to the CSV export"
criteria_file "$WORK/gift.md" full
digest=$(criteria digest "$G" --file "$WORK/gift.md" | field 'd["digest"]')
project log "$G" criteria.read by=lem asked:=3 answered:=2 'families:=["opus", "sol"]' 'silent:=[{"name": "Accountant, sol", "why": "the model was at capacity"}]' \
  criteria:=2 flagged:=1 split:=true "digest=$digest" >/dev/null
criteria approve "$G" --file "$WORK/gift.md" >/dev/null
project state "$G" building "lead: builder" >/dev/null
project state "$G" building "plan committed, 3 tasks" >/dev/null
project state "$G" building "task 1 of 3" >/dev/null
decide log "$G" --what "The name of the new column" --chose gift_note --why "the other columns of the export are in snake case" --by lead --undo "rename the column" >/dev/null
decide log "$G" --what "Two notes on one order" --chose "both notes, with a semicolon between them" --why "a merchant reads both" --by personas \
  --vote "the merchant, opus=both notes, with a semicolon between them" --vote "the accountant, opus=both notes, with a semicolon between them" \
  --said "The merchant and the accountant both picked the semicolon." >/dev/null
decide ask "$G" "${CASE[@]}" --what "Where the note goes in the row" --option "the last column" --option "after the price" --recommended "the last column" \
  --why "an import that reads the columns by place keeps working" --said "The merchant picked the last column, the accountant after the price." >/dev/null
decide answer "$G" 3 --chose "the last column" --words "last, like the other new columns" >/dev/null
project state "$G" building "task 2 of 3" >/dev/null
decide ask "$G" "${CASE[@]}" --what "Email the merchants about the new column" --option "send it" --option "do not send it" --recommended "do not send it" \
  --why "the column is visible in the export" --said "The merchant wants the email, the accountant does not." --irreversible person >/dev/null
decide ask "$G" "${CASE[@]}" --what "The header of the column" --option "Gift note" --option "Note" --recommended "Gift note" --why "it says what the cell holds" --said "The two personas split." >/dev/null
decide ask "$G" "${CASE[@]}" --what "A note longer than the cell" --option "all of it" --option "200 characters" --recommended "all of it" --why "nothing is lost" --said "The two personas split." >/dev/null
taken "$G" 5
decide ask "$G" "${CASE[@]}" --what "The note of a cancelled order" --option "keep it" --option "leave it out" --recommended "keep it" --why "the export shows cancelled orders as they were" \
  --said "The merchant would keep it, the accountant is in doubt." >/dev/null
retime "$G" now -60 -52 -51 -45 -44 -40 -35 -34 -31 -30 -27 -26 -25 -10 -5

# The task whose time the card draws: it ran from its criteria to a merged pull request, on 10 November.
L=landed-one
task "$L" "Show the order's currency on the invoice"
criteria_file "$WORK/landed.md" full
digest=$(criteria digest "$L" --file "$WORK/landed.md" | field 'd["digest"]')
project log "$L" criteria.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' criteria:=2 flagged:=1 split:=false "digest=$digest" >/dev/null
criteria approve "$L" --file "$WORK/landed.md" >/dev/null
project state "$L" building "lead: session" >/dev/null
# the talk's start is not in this log, as in a log written before the lead logged it
project log "$L" plan.talk reviewer=codex turns:=19 questions:=4 settled:=3 open:=1 repaired:=2 design:=1 unargued:=1 root:=2 layer:=0 shared:=0 >/dev/null
project state "$L" building "plan committed, 2 tasks" >/dev/null
project state "$L" building "task 1 of 2" >/dev/null
project state "$L" building "task 2 of 2" >/dev/null
decide ask "$L" "${CASE[@]}" --what "The symbol or the code of the currency" --option "the symbol" --option "the code" --recommended "the code" --why "two currencies share the dollar sign" --said "The two personas split." >/dev/null
decide answer "$L" 1 --chose "the code" >/dev/null
project log "$L" task.red ok:=true "digest=$digest" base=0a1b2c3d4 tip=abc123456 'tests:=[]' 'without_a_test:=[]' 'run_without:=[]' >/dev/null
project state "$L" ready "the report is written" >/dev/null
project state "$L" landing "the checks start" >/dev/null
project log "$L" gate "command=make test" exit:=0 "last=12 passed" tip=abc1234 >/dev/null
project log "$L" gate "command=make lint" exit:=0 "last=All checks passed" tip=abc1234 >/dev/null
project log "$L" task.red ok:=true "digest=$digest" base=0a1b2c3d4 tip=abc123456 'tests:=[]' 'without_a_test:=[]' 'run_without:=[]' >/dev/null
project log "$L" review attempt:=1 round:=1 kind=round verdict=clean must_fix:=0 should:=1 nit:=2 'answered:=["codex", "claude"]' 'silent:=[]' \
  'ran:=[{"name": "correctness", "why": "the invoice changes"}]' 'left_out:=[{"name": "security", "why": "no input is read"}]' tip=abc1234 >/dev/null
project log "$L" proposed green:=true 'not_green:=[]' tip=abc1234 >/dev/null
project state "$L" open "pull request https://github.com/acme/shop/pull/7" "green" >/dev/null
project state "$L" landed "main: pull request https://github.com/acme/shop/pull/7 is merged" >/dev/null
retime "$L" 2026-11-10T09:00:00Z 10 22 23 34 35 40 58 65 72 80 82 85 87 88 90 101 103 104 150

# One task for each other thing a lane holds.
task criteria-wait "Round the totals of the monthly report"
project state criteria-wait held "the criteria wait for the owner" >/dev/null
task held-question "Which currency rounds half up"
project state held-question building "lead: builder" >/dev/null
project state held-question held "the investigation waits for one more fact" >/dev/null
task held-choice "Refund the duplicate orders"
project state held-choice building "lead: builder" >/dev/null
decide ask held-choice "${CASE[@]}" --what "Refund the 12 duplicate orders now" --option "refund them" --option "leave them" --recommended "leave them" --why "a refund cannot be taken back" \
  --said "The two personas split." --irreversible money >/dev/null
project state held-choice held "choice 1 waits for the owner" >/dev/null
task open-pr "Sort the export by date"
project state open-pr open "pull request https://github.com/acme/shop/pull/9" "not green: criterion 1 changed during the build" >/dev/null
task ready-to-land "Fix the typo in the invoice"
project state ready-to-land open "ready to land on main at abc1234" "green" >/dev/null
task plan-for-you "Move the reports to a queue"
project state plan-for-you planned "the plan waits for the owner to read it" >/dev/null
task building-one "Cache the product list"
# the type fix on a task with a plan: the tag fix, and no small change
project state building-one building "task 1 of 2" "type: fix, because one rule of the cache is wrong" >/dev/null
task queued-one "Add a dark theme"
project state queued-one queued "waits for its turn" >/dev/null
task blocked-one "Upgrade the database driver"
project state blocked-one blocked "the base moved and the rebase has a conflict" >/dev/null
task ready-one "Name the export files by date"
project state ready-one ready "the report is written" >/dev/null
task in-checks "Trim the order notes"
project state in-checks ready "the report is written" >/dev/null
project state in-checks landing "the checks start" >/dev/null
project log in-checks gate "command=make test" exit:=0 "last=9 passed" tip=def5678 >/dev/null
task correction-one "The footer says Terms and condtions"
criteria_file "$WORK/correction.md" small
criteria approve correction-one --file "$WORK/correction.md" --small >/dev/null
# a small change has no lead: one builder makes it (stages/new.md, "A small change")
project state correction-one building "small change: one builder" >/dev/null
project log correction-one builder.start "job=the small change" >/dev/null

# A choice taken without the owner an hour after it was asked, and a review logged in the same second
# as the next state block: on 11 November.
T=timed-out
task "$T" "Round the shipping costs"
project state "$T" building "lead: builder" >/dev/null
decide ask "$T" "${CASE[@]}" --what "Round up or to the nearest cent" --option "up" --option "to the nearest cent" --recommended "to the nearest cent" --why "the carrier rounds so" --said "The two personas split." >/dev/null
taken "$T" 1
project state "$T" ready "the report is written" >/dev/null
project state "$T" landing "the checks start" >/dev/null
project log "$T" gate "command=make test" exit:=0 "last=3 passed" tip=abc1234 >/dev/null
project log "$T" task.red ok:=true digest=000000000000 base=0a1b2c3d4 tip=abc123456 'tests:=[]' 'without_a_test:=[]' 'run_without:=[]' >/dev/null
project log "$T" review attempt:=1 round:=1 kind=read verdict=clean must_fix:=0 should:=0 nit:=0 'answered:=["codex"]' 'silent:=[]' 'ran:=[]' 'left_out:=[]' tip=abc1234 >/dev/null
project state "$T" open "ready to land on main at abc1234" "green" >/dev/null
project state "$T" landed "main abc1234" >/dev/null
retime "$T" 2026-11-11T09:00:00Z 0 5 65 70 72 74 76 80 80 90

# One run of the gate in a landing that is still open: its first command failed, and its second ran after it.
task red-gate "Keep the cart for a week"
project state red-gate ready "the report is written" >/dev/null
project state red-gate landing "the checks start" >/dev/null
project log red-gate gate "command=make test" exit:=1 "last=1 failed, 8 passed" tip=fed4321 >/dev/null
project log red-gate gate "command=make lint" exit:=0 "last=All checks passed" tip=fed4321 >/dev/null
retime red-gate now -40 -30 -25 -20

# Criteria that nobody was confused by, which still wait for the owner's yes: he left before he gave it.
task clear-read-held "Show the stock on the product page"
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the page gets a new line.' '' '1. A product with 3 in stock says "3 left".' > "$WORK/stock.md"
digest=$(criteria digest clear-read-held --file "$WORK/stock.md" | field 'd["digest"]')
project log clear-read-held criteria.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$digest" >/dev/null
project state clear-read-held held "the criteria wait for the owner" >/dev/null

# A criterion change of the build that the owner's next approval took over, and one after that approval.
C=changed-then-approved
task "$C" "Name the export file by its date"
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the file name changes.' '' '1. The export of 3 May is named export-05-03.csv.' '2. A second export that day gets -2.' > "$WORK/name-1.md"
criteria approve "$C" --file "$WORK/name-1.md" >/dev/null
project state "$C" building "lead: builder" >/dev/null
decide criterion "$C" --changed 1 --was "The export of 3 May is named export-05-03.csv." --now "The export of 3 May is named export-2026-05-03.csv." --why "a year keeps the names apart" --by lead >/dev/null
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the file name changes.' '' '1. The export of 3 May is named export-2026-05-03.csv.' '2. A second export that day gets -2.' > "$WORK/name-2.md"
criteria approve "$C" --file "$WORK/name-2.md" >/dev/null
decide criterion "$C" --changed 2 --was "A second export that day gets -2." --now "A second export that day gets -2, a third -3." --why "the counter goes on" --by lead >/dev/null

# A full change from a complete request: the lead's read found nobody confused, and froze the plan's criteria.
task rare-path "Show the VAT number on the invoice"
rw=$(project worktree-dir rare-path)
git -C "$R" worktree add -q -b feat/rare-path "$rw" main
mkdir -p "$rw/docs/plans"
printf '%s\n' '# A complete request' '' '## Acceptance criteria' '' 'Size: full, because the invoice gets a new line.' '' '1. An invoice to a company shows its VAT number under its name.' '' '## Tasks' '' '1. The line.' > "$rw/docs/plans/2026-11-16-rare-path.md"
project state rare-path building "lead: builder" >/dev/null
digest=$(criteria digest rare-path | field 'd["digest"]')
project log rare-path criteria.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$digest" >/dev/null
criteria approve rare-path --read >/dev/null

# A task the owner holds at the reviewer's trust prompt: a step of his, and no decision.
task trust-prompt "Move the review to Codex"
project state trust-prompt building "lead: session" >/dev/null
project state trust-prompt held "the reviewer's trust prompt waits for the owner's yes" >/dev/null

# A full change with an interview writes the personas' read before the task's first state block.
task read-first "Show the order's weight on the label"
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the label gets a new line.' '' '1. A parcel of 2.5 kg says "2.5 kg" on its label.' > "$WORK/weight.md"
digest=$(criteria digest read-first --file "$WORK/weight.md" | field 'd["digest"]')
project log read-first criteria.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$digest" >/dev/null

# The plan's criteria and their tests' result, and then a new approval of other criteria.
task approved-again "Print the packing slip in German"
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the slip gets a language.' '' '1. A slip for Berlin is in German.' > "$WORK/slip-1.md"
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the slip gets a language.' '' '1. A slip for Berlin or Vienna is in German.' > "$WORK/slip-2.md"
criteria approve approved-again --file "$WORK/slip-1.md" >/dev/null
project state approved-again building "task 1 of 1" >/dev/null
project log approved-again task.criteria size=full "why=the slip gets a language." digest=0123456789ab \
  'criteria:=[{"n": 1, "text": "A slip for Berlin is in German.", "tests": [{"command": "sh tests/slip.sh", "files": ["tests/slip.sh"]}], "no_test": null}]' >/dev/null
project log approved-again task.red ok:=true digest=0123456789ab base=0a1b2c3d4 tip=abc123456 \
  'tests:=[{"criterion": 1, "command": "sh tests/slip.sh", "files": ["tests/slip.sh"], "on_branch": 0, "on_base": 1, "problem": null}]' 'without_a_test:=[]' 'run_without:=[]' >/dev/null
criteria approve approved-again --file "$WORK/slip-2.md" >/dev/null

# Criteria read and approved, changed by the build, then approved again as they were read: nothing is unread.
# Beside it the same without the second approval: the change was not read.
for slug in restored-read unread-change; do
  task "$slug" "Name the carrier on the slip"
  printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the slip gets a line.' '' '1. A DHL parcel says "DHL" on its slip.' > "$WORK/$slug.md"
  digest=$(criteria digest "$slug" --file "$WORK/$slug.md" | field 'd["digest"]')
  project log "$slug" criteria.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$digest" >/dev/null
  criteria approve "$slug" --file "$WORK/$slug.md" >/dev/null
  project state "$slug" building "lead: builder" >/dev/null
  decide criterion "$slug" --changed 1 --was 'A DHL parcel says "DHL" on its slip.' --now 'A DHL parcel says "DHL Express" on its slip.' --why "the carrier's own name" --by lead >/dev/null
done
criteria approve restored-read --file "$WORK/restored-read.md" >/dev/null

# The two experts' advice on five choices: two taken without the owner with their shared pick, the
# first with his answer after it, one taken without him while they split, and two that still wait,
# the first with a shared pick and the second with none. Its state block comes a
# minute after the gift note's, so that the gift note stays the news of the board of all tasks.
X=expert-advice
task "$X" "Print the invoice for the post"
project state "$X" building "lead: builder" >/dev/null
decide ask "$X" "${CASE[@]}" --what "The paper size" --option "A4" --option "Letter" --recommended "Letter" --why "the printer has Letter in its tray" --said "The two personas split." >/dev/null
decide advise "$X" 1 --expert fable --pick A4 --why "every customer of the shop is in Europe, where the post reads A4" >/dev/null
decide advise "$X" 1 --expert astra --pick A4 --why "the envelopes of the shop are cut for A4" >/dev/null
taken "$X" 1
decide answer "$X" 1 --chose Letter --words "Letter, it is in the tray" >/dev/null
decide ask "$X" "${CASE[@]}" --what "The color of the logo" --option "black" --option "the green of the shop" --recommended "black" --why "a black logo prints on every printer" --said "The two personas split." >/dev/null
decide advise "$X" 2 --expert fable --pick "the green of the shop" --why "the invoice is a page of the shop" >/dev/null
decide advise "$X" 2 --expert astra --pick "the green of the shop" --why "the printer prints in color" >/dev/null
decide ask "$X" "${CASE[@]}" --what "The order number on the page" --option "at the top" --option "at the foot" --recommended "at the top" --why "the post office reads the top first" --said "The two personas split." >/dev/null
decide advise "$X" 3 --expert fable --pick "at the top" --why "a reader looks for it first" >/dev/null
decide advise "$X" 3 --expert astra --pick "at the foot" --why "the top holds the address window" >/dev/null
taken "$X" 2 3
decide ask "$X" "${CASE[@]}" --what "The font of the invoice" --option "serif" --option "sans" --recommended "sans" --why "it reads well on a screen" --said "The two personas split." >/dev/null
decide advise "$X" 4 --expert fable --pick serif --why "a printed invoice reads better in serif" >/dev/null
decide advise "$X" 4 --expert astra --pick serif --why "the letters of the shop are in serif" >/dev/null
decide ask "$X" "${CASE[@]}" --what "The size of the total" --option "12 pt" --option "14 pt" --recommended "14 pt" --why "a reader finds the total first" --said "The two personas split." >/dev/null
decide advise "$X" 5 --expert fable --none --why "the total should be bold, not bigger" >/dev/null
decide advise "$X" 5 --expert astra --pick "12 pt" --why "the other lines are 12 pt" >/dev/null
retime "$X" now -50 -49 -48 -47 -46 -45.5 -45 -44 -43 -42 -41 -40 -29 -26 -6 -5 -4 -3 -2 -1

# A landing whose polish pass is logged and whose checks run, and one that has only started.
P=polished
task "$P" "Name the invoice files by order"
project state "$P" ready "the report is written" >/dev/null
project state "$P" landing "the checks start" >/dev/null
project log "$P" polish.start before=abc1234 >/dev/null
project log "$P" polish before=abc1234 after=def5678 commits:=2 'filed:=["docs/backlog/invoice-footer-typo.md"]' >/dev/null
# the review read the diff against the topics and called it careful, which the plan did not
project log "$P" careful.missed round:=1 "why=the file name holds the order's total, which a customer pays" >/dev/null
project log "$P" gate.start tip=def5678 commands:=2 >/dev/null
retime "$P" now -40 -30 -30 -12 -12 -12
task landing-starts "Print the order date on the invoice"
project state landing-starts ready "the report is written" >/dev/null
project state landing-starts landing "the checks start" >/dev/null
retime landing-starts now -20 -10

# A plan talk from its start to its record, on 12 November, and one that has started and has no record yet.
K=talked-plan
task "$K" "Move the price rounding into one place"
project state "$K" building "lead: session" >/dev/null
project log "$K" plan.talk.start reviewer=codex >/dev/null
project log "$K" plan.talk reviewer=codex turns:=7 questions:=3 settled:=2 open:=1 repaired:=2 design:=1 unargued:=2 root:=1 layer:=1 shared:=1 >/dev/null
project state "$K" building "plan committed, 4 tasks" >/dev/null
project state "$K" dropped "the test is over" >/dev/null
retime "$K" 2026-11-12T09:00:00Z 0 2 20 21 25
task talk-runs "Split the invoice service"
project state talk-runs building "lead: session" >/dev/null
project log talk-runs plan.talk.start reviewer=claude >/dev/null
retime talk-runs now -70 -10
# A careful plan's talk in a companion that Lem opened, then the builder lead that builds it.
M=talk-then-build
task "$M" "Round the prices once"
project state "$M" building "lead: session" >/dev/null
project state "$M" building "session: C0FFEE" >/dev/null
project log "$M" plan.talk.start reviewer=codex >/dev/null
project log "$M" plan.talk reviewer=codex turns:=5 questions:=2 settled:=2 open:=0 repaired:=2 design:=0 unargued:=0 root:=0 layer:=1 shared:=0 >/dev/null
project state "$M" planned "the plan talk is done" >/dev/null
project state "$M" building "lead: builder" >/dev/null
project state "$M" building "plan committed, 4 tasks" >/dev/null
project state "$M" building "task 1 of 4" >/dev/null
retime "$M" now -60 -59 -58 -40 -39 -38 -37 -36

# A bug that its investigation found to be none: the task ends answered, with its report.
A=refund-shows-zero
task "$A" "Invoices show 0 after a refund"
project state "$A" building "an investigator reproduces the bug and finds its cause" "investigation: bug" "type: fix, because the ask says the total is wrong today" >/dev/null
printf '%s\n' '# Investigation' '' 'Reproduced: yes, with tests/refund.sh.' > "$STATE/tasks/$A/investigation.md"
project log "$A" investigation type=fix call=not-a-bug "line=a refund is a credit note, and the invoice shows what is left to pay" where=billing/invoice.py:total reproduced:=true >/dev/null
project state "$A" answered "not a bug: the invoice shows what is left to pay" "report: investigation.md" >/dev/null
retime "$A" now -30 -12 -11
# A bug whose investigation runs.
task cart-total-wrong "The cart total is wrong since yesterday"
project state cart-total-wrong building "an investigator reproduces the bug and finds its cause" "investigation: bug" "type: fix, because the ask says the total is wrong since yesterday" >/dev/null
project log cart-total-wrong investigation.start type=fix >/dev/null

# A full change whose every stage logged its start (SKILL.md), from the interview to the merge, on 13
# November: the time card draws each span from its start to the event that ends it.
S=started-stages
task "$S" "Print the order date on the invoice"
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the invoice gets a line.' '' '1. The invoice of order 1042, placed on 3 May, says "Ordered 3 May".' > "$WORK/started.md"
digest=$(criteria digest "$S" --file "$WORK/started.md" | field 'd["digest"]')
project state "$S" held "the interview waits for the owner" "type: feat, because the invoice gets a line" >/dev/null
project log "$S" scout.start >/dev/null
project log "$S" interview.start >/dev/null
project log "$S" scout >/dev/null
project log "$S" criteria.read.start by=lem >/dev/null
project log "$S" criteria.read by=lem asked:=3 answered:=3 'families:=["opus", "sol"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$digest" >/dev/null
project state "$S" held "the criteria wait for the owner" >/dev/null
criteria approve "$S" --file "$WORK/started.md" >/dev/null
project state "$S" building "lead: builder" >/dev/null
project state "$S" building "plan committed, 2 tasks" >/dev/null
project state "$S" building "task 1 of 2" >/dev/null
project log "$S" builder.start "job=task 1 of 2" >/dev/null
project state "$S" building "task 2 of 2" >/dev/null
project log "$S" builder.start "job=task 2 of 2" >/dev/null
project state "$S" ready "the report is written" >/dev/null
project state "$S" landing "the checks start" >/dev/null
project log "$S" polish.start before=abc123456 >/dev/null
project log "$S" polish before=abc1234 after=def5678 commits:=1 'filed:=[]' >/dev/null
project log "$S" gate.start tip=def567890 commands:=2 >/dev/null
project log "$S" gate "command=make test" exit:=0 "last=14 passed" tip=def5678 >/dev/null
project log "$S" gate "command=make lint" exit:=0 "last=All checks passed" tip=def5678 >/dev/null
project log "$S" task.red ok:=true "digest=$digest" base=0a1b2c3d4 tip=def567890 'tests:=[]' 'without_a_test:=[]' 'run_without:=[]' >/dev/null
project log "$S" review.start attempt:=1 floor=read >/dev/null
project log "$S" review attempt:=1 round:=1 kind=read verdict=clean must_fix:=0 should:=0 nit:=0 'answered:=["codex"]' 'silent:=[]' 'ran:=[]' 'left_out:=[]' tip=def5678 >/dev/null
project log "$S" proposed green:=true 'not_green:=[]' tip=def5678 >/dev/null
project state "$S" open "pull request https://github.com/acme/shop/pull/12" "green" >/dev/null
project state "$S" landed "main: pull request https://github.com/acme/shop/pull/12 is merged" >/dev/null
retime "$S" 2026-11-13T09:00:00Z 0 1 2 6 20 25 25 30 31 40 41 42 60 61 80 81 83 90 91 94 95 96 97 101 102 102 110
# A landing whose checks started and have no result yet.
task gate-runs "Trim the cart notes"
project state gate-runs ready "the report is written" >/dev/null
project state gate-runs landing "the checks start" >/dev/null
project log gate-runs gate.start tip=abc123456 commands:=2 >/dev/null
retime gate-runs now -20 -10 -5

# A read of the criteria in which no persona answered, and the criteria still wait for the owner.
task silent-read "Show the delivery date on the order page"
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the page gets a new line.' '' '1. An order shipped on 3 May says "arrives 5 May".' > "$WORK/delivery.md"
digest=$(criteria digest silent-read --file "$WORK/delivery.md" | field 'd["digest"]')
project log silent-read criteria.read by=lem asked:=2 answered:=0 'families:=[]' \
  'silent:=[{"name": "Merchant, opus", "why": "the model timed out"}, {"name": "Accountant, sol", "why": "the model was at capacity"}]' \
  criteria:=1 flagged:=0 split:=false "digest=$digest" >/dev/null
project state silent-read held "the criteria wait for the owner" >/dev/null
# A task queued behind another one whose result it needs (stages/new.md, step 7).
task queued-after "Cache the product images"
project state queued-after queued "waits for the task that caches the product list" "after: building-one" >/dev/null

# The backlog of the main checkout: an item whose place is gone, one whose place is there, one whose
# file cannot be read by anyone, and one decided against.
mkdir -p "$R/docs/backlog"
printf '%s\n' '---' 'worth: yes' 'where: billing/gone.py:total' 'added: 2026-11-01' '---' '' '# The total of a refund is rounded twice' '' 'Seen in a review.' > "$R/docs/backlog/refund-rounded-twice.md"
printf '%s\n' '---' 'worth: later' 'where: app.txt' 'added: 2026-11-02' '---' '' '# The app file has one line' > "$R/docs/backlog/app-one-line.md"
printf '%s\n' '---' 'worth: yes' 'where: locked.txt:secret' 'added: 2026-11-03' '---' '' '# The locked file' > "$R/docs/backlog/locked-file.md"
printf '%s\n' '---' 'worth: no' 'added: 2026-11-04' '---' '' '# Rewrite the shop in another language' '' 'Decided against: the shop works.' > "$R/docs/backlog/rewrite-the-shop.md"
echo secret > "$R/locked.txt"
git -C "$R" add -A && git -C "$R" commit -q -m "docs: the backlog"
chmod 000 "$R/locked.txt"

NOW=$("$PY" -I -c 'from datetime import datetime, timedelta, timezone; print((datetime.now(timezone.utc) + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:00Z"))')
# the board's copy of the log as Lem's scripts fed it, before retime writes it again from the moved log
fed=$(grep -c '"task": "gift-note-export"' "$STATE/events.js" || true)
retime_all

if [ "$(grep -c '"event": "decision.' "$STATE/events.jsonl")" = 37 ] && [ "$fed" = 15 ] && [ "$(grep -c '"task": "gift-note-export"' "$STATE/events.jsonl")" = 15 ]; then
  pass "the fixture is written by Lem's scripts: every decision is an event, and the board's copy of the log, as the scripts fed it, holds each event of a task"
else
  fail "the fixture: $(grep -c '"event": "decision.' "$STATE/events.jsonl") decision events, $fed events of gift-note-export in the board's copy"
fi

# Green has one wording: the board's sentence is the first line of a green pull request, land.py's GREEN.
if greens=$("$PY" -I -c 'import re, sys
board = re.search(r"^const GREEN = (.+);$", open(sys.argv[1]).read(), re.M)
land = re.search(r"^GREEN = (.+)$", open(sys.argv[2]).read(), re.M)
said = eval(board.group(1)) if board else None
meant = eval(land.group(1)).removeprefix("**Green.** ").removesuffix(".") if land else None
print(f"{said!r} / {meant!r}")
sys.exit(0 if said and said == meant else 1)' skills/lem/assets/board.html "$SCRIPTS/land.py"); then
  pass "the board says what green means in the words of a green pull request's first line"
else
  fail "two wordings of green: $greens"
fi

# An item whose place is a file nobody can read is shown with that problem, and the board of the
# other items is still written.
if board --no-open > "$WORK/board.json" 2> "$WORK/board.err" \
  && why=$("$PY" -I -c 'import json, re, sys
feed = json.loads(re.fullmatch(r"lemBacklog\((.*)\);\n", open(sys.argv[1], encoding="utf-8").read(), re.S).group(1))
problems = {item["slug"]: item["where_problem"] for item in feed["items"]}
want = {"locked-file": "the file cannot be read", "refund-rounded-twice": "the file is not there", "app-one-line": "", "rewrite-the-shop": ""}
print("" if problems == want else f"the items: {problems}")
sys.exit(problems != want)' "$STATE/backlog.js"); then
  pass "a backlog item whose place is a file nobody can read says so, and the board of the other items is written"
else
  fail "a backlog item with an unreadable place: ${why:-$(tail -1 "$WORK/board.err")}"
fi
for slug in "$G" "$L" correction-one "$T" red-gate clear-read-held "$C" rare-path read-first approved-again restored-read unread-change "$X" "$P" landing-starts "$K" talk-runs "$M" "$A" cart-total-wrong silent-read queued-after queued-one \
  "$S" gate-runs held-choice held-question trust-prompt criteria-wait plan-for-you open-pr ready-to-land; do board --no-open --task "$slug" >/dev/null; done

SHOWN=$(cat <<'PY'
import re, sys
from html.parser import HTMLParser
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
class P(HTMLParser):
    def __init__(self, visible):
        super().__init__(); self.skip = 0; self.text = []; self.title = ""; self.in_title = False; self.visible = visible; self.hidden = []
    def handle_starttag(self, tag, attrs):
        self.skip += tag in ("script", "style"); self.in_title = tag == "title" and not self.skip
        if tag not in VOID: self.hidden.append("hidden" in dict(attrs))
    def handle_endtag(self, tag):
        self.skip -= tag in ("script", "style"); self.in_title = False
        if tag not in VOID and self.hidden: self.hidden.pop()
    def handle_data(self, data):
        if self.in_title and not self.title: self.title = data
        elif not self.skip and not (self.visible and any(self.hidden)): self.text.append(data)
# "@visible": only the text the owner sees, none under an element with `hidden` (the panel of another tab)
wants = [w for w in sys.argv[2:] if w != "@visible"]
p = P("@visible" in sys.argv[2:]); p.feed(open(sys.argv[1], encoding="utf-8").read())
shown = " ".join(" ".join(p.text).split())
# "!TEXT" must not be on the page, "~PATTERN" is a regular expression that must match it, and
# "=N:TEXT" is a text that is on the page N times
missing = [want for want in wants if want[0] not in "!~=" and want not in shown and want not in p.title]
for want in [w for w in wants if w.startswith("=")]:
    n, _, text = want[1:].partition(":")
    if shown.count(text) != int(n): missing.append(f"{text!r} is on the page {shown.count(text)} times, not {n}")
missing += [f"no match of {want[1:]!r}" for want in wants if want.startswith("~") and not re.search(want[1:], shown)]
missing += [f"no {want[1:]!r}" for want in wants if want.startswith("!") and (want[1:] in shown or want[1:] in p.title)]
if "PROBLEM" in p.title or "does not parse" in shown: missing.append(f"no problem on the page (title {p.title!r})")
print("; ".join(missing))
sys.exit(bool(missing))
PY
)
# TIMECARD DOM 'ROW|ROW|...' 'ROW=TOTAL · SHARE' ...: the rows of the time card, in order, and its legend, item for item
TIMECARD=$(cat <<'PY'
import html, re, sys
dom = open(sys.argv[1], encoding="utf-8").read()
rows = [html.unescape(row) for row in re.findall(r'<text class="lane-label"[^>]*>([^<]*)</text>', dom)]
area = dom[dom.index('id="legend"'):]
area = area[:area.index("</div>")]
legend = {html.unescape(label): html.unescape(value) for label, value in re.findall(r"<span[^>]*><i[^>]*></i>(.*?)<em>(.*?)</em></span>", area)}
want = dict(item.split("=", 1) for item in sys.argv[3:])
# a value that starts with "~" is a regular expression, for a total that grows with the clock
same = set(legend) == set(want) and all(re.fullmatch(value[1:], legend[label]) if value.startswith("~") else value == legend[label] for label, value in want.items())
wrong = ([f"the rows are {rows}"] if rows != sys.argv[2].split("|") else []) + ([f"the legend is {legend}"] if not same else [])
print("; ".join(wrong))
sys.exit(bool(wrong))
PY
)
# BANNERS DOM PATTERN ...: each regular expression matches the text of one banner, and "!PATTERN"
# none. A banner folded under the first ones counts too; "#N" says that N banners are shown, and
# "=PATTERN" matches the text of the line that unfolds the rest.
BANNERS=$(cat <<'PY'
import re, sys
from html.parser import HTMLParser
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.stack = []; self.banners = []; self.fold = []; self.inside = None; self.done = False
    def handle_starttag(self, tag, attrs):
        if tag in VOID or self.done: return
        a = dict(attrs); cls = (a.get("class") or "").split()
        if a.get("id") == "banners": self.inside = len(self.stack)
        hidden = "hidden" in a or any(n["hidden"] for n in self.stack)
        node = {"tag": tag, "hidden": hidden, "banner": None, "fold": None}
        if self.inside is not None and tag == "div" and "banner" in cls and not any(n["banner"] is not None for n in self.stack):
            node["banner"] = {"text": [], "shown": not hidden}; self.banners.append(node["banner"])
        if self.inside is not None and "banner-fold" in cls:
            node["fold"] = []; self.fold.append(node["fold"])
        self.stack.append(node)
    def handle_endtag(self, tag):
        if tag in VOID or self.done or not self.stack: return
        self.stack.pop()
        if self.inside is not None and len(self.stack) == self.inside: self.done = True
    def handle_data(self, data):
        for n in self.stack:
            if n["banner"] is not None: n["banner"]["text"].append(data)
            if n["fold"] is not None: n["fold"].append(data)
p = P(); p.feed(open(sys.argv[1], encoding="utf-8").read())
banners = [" ".join(" ".join(b["text"]).split()) for b in p.banners]
shown = sum(b["shown"] for b in p.banners)
fold = " ".join(" ".join(" ".join(f) for f in p.fold).split())
wrong = []
for want in sys.argv[2:]:
    if want.startswith("#"):
        if shown != int(want[1:]): wrong.append(f"{shown} banners are shown, not {want[1:]}")
    elif want.startswith("="):
        if not re.search(want[1:], fold): wrong.append(f"the fold says {fold!r}, not {want[1:]!r}")
    elif want.startswith("!"):
        if any(re.search(want[1:], text) for text in banners): wrong.append(f"a banner matches {want[1:]!r}")
    elif not any(re.search(want, text) for text in banners):
        wrong.append(f"no banner matches {want!r}")
print("; ".join(wrong) + (f" (the banners: {banners})" if wrong else ""))
sys.exit(bool(wrong))
PY
)
# LANES DOM 'LANE=TITLE|LINE' ...: the card of TITLE is in LANE, and its one line of where the task
# is, is LINE. "#counts": the head of each lane counts its cards and the older ones it names.
# "#short": every card has one such line and no paragraph of where the owner answers.
LANES=$(cat <<'PY'
import html, re, sys
dom = open(sys.argv[1], encoding="utf-8").read()
text = lambda s: " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())
lanes, counts, lines = {}, {}, {}
for part in re.split(r'<div class="lane a-', dom)[1:]:
    title = text(re.search(r'<div class="lane-head">(.*?)<em', part, re.S).group(1))
    head = text(re.search(r'<div class="lane-head">.*?<em[^>]*>(.*?)</em>', part, re.S).group(1))
    older = re.search(r'<div class="more">and (\d+) older', part)
    cards = {}
    for card in re.split(r'<button class="tcard ', part)[1:]:
        name = text(re.search(r'<div class="tc-title">(.*?)</div>', card, re.S).group(1))
        # a card's line may carry a hover, so its tag may have attributes
        said = [text(x) for x in re.findall(r'<div class="tc-text"[^>]*>(.*?)</div>', card, re.S)]
        cards[name] = said[0] if said else ""
        lines[name] = (len(said), 'class="tc-where"' in card)
    lanes[title] = cards
    counts[title] = (head, len(cards) + int(older.group(1) if older else 0))
wrong = []
if "#counts" in sys.argv[2:]:
    wrong += [f"the head of {lane!r} says {head!r} over {n} cards" for lane, (head, n) in counts.items() if head != str(n)]
if "#short" in sys.argv[2:]:
    wrong += [f"{name!r} has {n} lines and {'a' if where else 'no'} paragraph of where to answer" for name, (n, where) in lines.items() if n != 1 or where]
for want in [w for w in sys.argv[2:] if not w.startswith("#")]:
    lane, _, rest = want.partition("=")
    name, _, where = rest.partition("|")
    if name not in lanes.get(lane, {}):
        wrong.append(f"{name!r} is not in {lane!r} ({ {k: list(v) for k, v in lanes.items()} })")
    # "~PATTERN": the line is the whole of a regular expression, for a time the page's own clock says
    elif where and (not re.fullmatch(where[1:], lanes[lane][name]) if where.startswith("~") else lanes[lane][name] != where):
        wrong.append(f"{name!r} says {lanes[lane][name]!r}, not {where!r}")
print("; ".join(wrong))
sys.exit(bool(wrong))
PY
)
# ROWS DOM ID 'ANCHOR|WANT|...' ...: a row of the element ID (one of its children) holds the text
# ANCHOR, and that same row holds each WANT: a text, "!TEXT" that it must not hold, "~PATTERN" a
# regular expression, "@CLASS" a class of the row. So a text of another row cannot stand in.
ROWS=$(cat <<'PY'
import re, sys
from html.parser import HTMLParser
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
class P(HTMLParser):
    def __init__(self, target):
        super().__init__(); self.target = target; self.depth = 0; self.inside = None; self.done = False; self.rows = []
    def handle_starttag(self, tag, attrs):
        if tag in VOID: return
        self.depth += 1
        if self.inside is None and not self.done and dict(attrs).get("id") == self.target: self.inside = self.depth
        elif self.inside is not None and self.depth == self.inside + 1: self.rows.append({"cls": (dict(attrs).get("class") or "").split(), "text": []})
    def handle_endtag(self, tag):
        if tag in VOID: return
        if self.inside is not None and self.depth == self.inside: self.inside = None; self.done = True
        self.depth -= 1
    def handle_data(self, data):
        if self.inside is not None and self.depth > self.inside and self.rows: self.rows[-1]["text"].append(data)
p = P(sys.argv[2]); p.feed(open(sys.argv[1], encoding="utf-8").read())
rows = [{"cls": r["cls"], "text": " ".join(" ".join(r["text"]).split())} for r in p.rows]
wrong = []
for want in sys.argv[3:]:
    anchor, *needs = want.split("|")
    row = next((r for r in rows if anchor in r["text"]), None)
    if row is None:
        wrong.append(f"no row of #{sys.argv[2]} holds {anchor!r} (its rows: {[r['text'][:90] for r in rows]})")
        continue
    for need in needs:
        ok = (need[1:] in row["cls"]) if need.startswith("@") else (need[1:] not in row["text"]) if need.startswith("!") \
            else bool(re.search(need[1:], row["text"])) if need.startswith("~") else need in row["text"]
        if not ok: wrong.append(f"the row {anchor!r} does not hold {need!r}: {row['text']!r} (class {' '.join(row['cls'])})")
print("; ".join(wrong))
sys.exit(bool(wrong))
PY
)

chrome=""
for c in google-chrome chromium chromium-browser "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
  if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then chrome=$c; break; fi
done
# Every clock time on the pages is in UTC, so a check of one reads the same on every machine. Chrome's
# temporary folders go into the work folder, which the run removes: each run of Chrome left a
# com.google.Chrome.* folder in the user's temporary folder. On macOS Chrome reads MAC_CHROMIUM_TMPDIR,
# not TMPDIR (measured on 2026-11-17); elsewhere it reads TMPDIR.
mkdir -p "$WORK/chrome-tmp"
headless() { TZ=UTC TMPDIR="$WORK/chrome-tmp" MAC_CHROMIUM_TMPDIR="$WORK/chrome-tmp" "$chrome" --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" "$@" 2>/dev/null || true; }
# draw PAGE [TAB]: the page as Chrome leaves it, into PAGE.dom (PAGE-TAB.dom for a tab), with its clock
# stopped at NOW: a script before the page's own makes Date.now() give NOW. board.py writes the page
# again at every run, so each draw puts the script in once more.
STOP=$(cat <<'PY'
import sys
page, now = sys.argv[1:]
text = open(page, encoding="utf-8").read()
mark = "<script>/* the fixture's clock */"
if mark not in text:
    text = text.replace("<head>", f'<head>{mark} {{ const fixed = Date.parse("{now}"); Date.now = () => fixed; }}</script>', 1)
open(page, "w", encoding="utf-8").write(text)
PY
)
# shown_text PAGE TEXT: how many times the drawn page holds TEXT outside its scripts, whose source holds every wording
shown_text() { "$PY" -I -c 'import re, sys; print(re.sub(r"(?s)<script\b.*?</script>", "", open(sys.argv[1], encoding="utf-8").read()).count(sys.argv[2]))' "$WORK/$1.dom" "$2"; }
draw() {
  "$PY" -I -c "$STOP" "$STATE/$1.html" "$NOW"
  headless --virtual-time-budget=5000 --dump-dom "file://$STATE/$1.html${2:+#$2}" > "$WORK/$1${2:+-$2}.dom"
}

# Every check from here on reads a page Chrome drew: with none, or with a Chrome that cannot start
# (a sandbox that forbids it) and so says nothing about the page, each says so in a SKIP line.
if [ -z "$chrome" ]; then
  skip_rest "no Chrome or Chromium found"
else
  draw board
  if [ ! -s "$WORK/board.dom" ]; then skip_rest "$chrome printed no page"; fi
fi
if [ -n "$chrome" ] && [ -s "$WORK/board.dom" ]; then
  # shellcheck disable=SC1111  # the curly quotes around a state's own line are the page's
  if why=$("$PY" -I -B -c "$LANES" "$WORK/board.dom" "#short" \
    "Waits for you=Gift note export|Building: task 2 of 3" \
    "Waits for you=Held choice|Choice 1 waits for you" \
    "Waits for you=Held question|The investigation waits for one more fact" \
    "Waits for you=Trust prompt|The reviewer's trust prompt waits for your yes" \
    "Building=Approved again" "Building=Restored read" "Building=Unread change" \
    "Waits for you=Clear read held|The criteria wait for you" "Waits for you=Criteria wait|The criteria wait for you" "Waits for you=Silent read|The criteria wait for you" \
    "Waits for you=Plan for you|Planned: the plan waits for you to read it" \
    "Waits for you=Open pr|Waits for the merge: pull request #9" \
    "Waits for you=Ready to land|Waits for the merge: ready to land on main at abc1234" \
    "Building=Building one|Task 1 of 2" "Building=Queued one|Queued: waits for its turn" "Building=Blocked one|Blocked: the base moved and the rebase has a conflict" \
    "Building=Correction one|One builder makes the change" "Building=Changed then approved" "Building=Rare path" \
    "Checks and review=Ready one|Ready for its checks: the report is written" "Checks and review=In checks|The checks start" "Checks and review=Red gate" \
    "Done=Landed one|Landed: main: pull request #7 is merged" "Done=Timed out" "Building=Queued after"); then
    pass "each task is in the lane of who acts, and its card says in one line its state, in your words and not the lane's title again, also when a choice waits; no card has a paragraph of where you answer"
  else
    fail "the lanes: $why"
  fi
  # Where you answer is on the task's own board: a choice, one more fact, a step of his, the criteria,
  # a plan, a pull request, a branch to land.
  wheres=()
  # shellcheck disable=SC1111,SC1112  # the curly quotes are the page's
  for want in "held-question|It waits on what its state says: “the investigation waits for one more fact”. Lem tells you in its session what to do and where." \
    "trust-prompt|It waits on what its state says: “the reviewer's trust prompt waits for your yes”. Lem tells you in its session what to do and where." \
    "held-choice|Lem puts choice 1 to you as a page in its session. Answer it there: it waits for your word, also while you are away." \
    "criteria-wait|Lem shows you the acceptance criteria, with the personas’ read on top, as a page in its session. Approve or change them there." \
    "silent-read|Lem shows you the acceptance criteria as a page in its session. No persona answered the read of them. Approve or change them there." \
    "plan-for-you|Read the plan, then tell Lem in its session: build it or drop it." \
    "open-pr|Merge the pull request, or tell Lem in its session to land it." \
    "ready-to-land|Tell Lem in its session to land it."; do
    draw "task-${want%%|*}"
    why=$("$PY" -I -B -c "$ROWS" "$WORK/task-${want%%|*}.dom" now "Where you answer:|${want#*|}") || wheres+=("${want%%|*}: $why")
  done
  if [ "${#wheres[@]}" -eq 0 ]; then
    pass "each task that waits for you says on its own board where you answer: a choice, one more fact, a step of yours, the criteria, a plan, a draft, a pull request, a branch to land"
  else
    fail "where you answer: ${wheres[*]}"
  fi
  # The head of a lane counts the cards under it, and the page's title counts what the lanes hold.
  if why=$("$PY" -I -B -c "$LANES" "$WORK/board.dom" "#counts") \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/board.dom" "11 wait for you, 10 build, 6 in checks and review, 2 queued, 1 blocked"); then
    pass "the head of each lane counts the cards under it, and the title's numbers add up to the lanes: a task that builds while a choice waits for the owner is counted once, where it waits"
  else
    fail "the counts of the lanes: $why"
  fi
  # Each banner is read alone, so that a card's text elsewhere on the page cannot stand in for one. A
  # banner is only for a blocked task: what waits for the owner is a row of "Waits for you". The first
  # wait, choice 6, is the large card's, with where you answer, said once on the Tasks tab.
  if why=$("$PY" -I -B -c "$BANNERS" "$WORK/board.dom" "#1" "^Blocked: Blocked one · the base moved and the rebase has a conflict · " \
    "!^Choice" "!^Waits for you" "!Lem puts" "!Lem shows you") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/board.dom" now \
      "You · choice 6 of the task|Gift note export|A note longer than the cell|25m|since it was asked|Where you answer: Lem puts choice 6 to you as a page in its session. Answer it there: it waits for your answer. If you say you are away, the build goes on with the recommended action.") \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/board.dom" @visible "=1:Lem puts choice 6 to you" "=0:Lem puts choice 4 to you" "=0:Lem shows you the acceptance criteria" "!Demo data"); then
    pass "the large card has the first wait with where you answer, said once on the Tasks tab; a banner is only for a blocked task, and no banner repeats what waits for you"
  else
    fail "the banners: $why"
  fi
  # "Waits for you" has a row for each thing the owner does, each with its verb and where he answers.
  # A task that waits on two things has two rows; a held task whose choice waits has one, its choice's.
  draw board waits
  # shellcheck disable=SC1111  # the curly quotes around a pick are the page's
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/board-waits.dom" waits-rows \
      "A note longer than the cell|Answer choice 6|Gift note export|Where you answer: Lem puts choice 6 to you" \
      "The note of a cancelled order|Answer choice 7|Gift note export" \
      "Email the merchants about the new column|Answer choice 4|it waits for your word, also while you are away" \
      "Refund the 12 duplicate orders now|Answer choice 1|Held choice" \
      "The font of the invoice|Answer choice 4|Expert advice|the experts: Fable “serif” · Astra “serif”" \
      "Round the totals of the monthly report|Approve the criteria|Criteria wait|Lem shows you the acceptance criteria" \
      "Show the delivery date on the order page|Approve the criteria|No persona answered" \
      "Which currency rounds half up|The investigation waits for one more fact" \
      "Move the review to Codex|The reviewer's trust prompt waits for your yes" \
      "Move the reports to a queue|Read the plan|build it or drop it" \
      "Sort the export by date|Merge the pull request|Not green: criterion 1 changed during the build" \
      "Fix the typo in the invoice|Tell Lem to land it|Green|!Merge") \
    && why=$("$PY" -I -c 'import re, sys
dom = open(sys.argv[1], encoding="utf-8").read()
area = dom[dom.index("id=\"waits-rows\""):dom.index("id=\"backlog\"")]
rows = area.count("<div class=\"wrow ")
tab = re.search(r"data-tab=\"waits\"[^>]*>Waits for you<em[^>]*>(\d+)</em>", dom)
held = area.count("data-open=\"held-choice\"")
wrong = ([f"{rows} rows, not 14"] if rows != 14 else []) + ([f"the tab counts {tab.group(1) if tab else None}, the rows are {rows}"] if not tab or int(tab.group(1)) != rows else []) \
  + ([f"Held choice has {held // 2} rows"] if held != 2 else [])
print("; ".join(wrong)); sys.exit(bool(wrong))' "$WORK/board-waits.dom"); then
    pass "the Waits for you tab has a row for each thing you do, with its verb and where you answer: each choice, the criteria, what a held task's state asks, a plan, a merge or a landing; a held task whose choice waits is one row, and the tab counts the rows"
  else
    fail "the rows of Waits for you: $why"
  fi
  # Each number once: the title and the lanes count the tasks; a chip says what no other place says.
  # The board of all tasks has no ring and no grid, and no count of places: no setting limits the tasks.
  if ! grep -q 'class="ring-wrap"' "$WORK/board.dom" && ! grep -q 'class="stats"' "$WORK/board.dom" \
    && ! grep -q ' places</span>' "$WORK/board.dom" \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/board.dom" "2 proposed · 1 not green" "!landed today" "!places" "!wait for the merge"); then
    pass "the board of all tasks says each number once: no ring and no grid of counts, no chip of places, and the proposed requests that are not green"
  else
    fail "the numbers of the board: ${why:-a ring, a grid or a chip of places}"
  fi

  # How fresh the board's word on the pull requests is: no watch ran, a look 40 seconds ago, a look older than three of
  # its intervals, and a watch that ended. A copy of the page under another name opens on all tasks too.
  # watch_at SECONDS_AGO [WHY]: watch.js as land.py watch writes it, with its last look that long before NOW, or ended with WHY
  watch_at() { "$PY" -I -c 'import json, sys; from datetime import datetime, timedelta, timezone
now = datetime.strptime(sys.argv[2], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
at = (now - timedelta(seconds=int(sys.argv[3]))).strftime("%Y-%m-%dT%H:%M:%SZ")
record = {"checked": at, "every": 60, "looks": 4, "open": [], "ended": None} if len(sys.argv) < 5 else {"checked": None, "every": 60, "ended": at, "why": sys.argv[4]}
open(sys.argv[1], "w").write("lemWatch(" + json.dumps(record) + ");\n")' "$STATE/watch.js" "$NOW" "$@"; }
  watches=()
  rm -f "$STATE/watch.js"
  cp "$STATE/board.html" "$STATE/watchprobe.html" && draw watchprobe
  why=$("$PY" -I -B -c "$SHOWN" "$WORK/watchprobe.dom" "nobody watches the pull request · type /lem" "!checked") || watches+=("none: $why")
  grep -q '<span class="chip you"[^>]*title="Nobody has looked at the forge for the pull request: a merge or a close there shows here only after Lem looks. Type /lem in Lem' "$WORK/watchprobe.dom" || watches+=("none: the chip's colour or its hover")
  watch_at 40 && draw watchprobe
  why=$("$PY" -I -B -c "$SHOWN" "$WORK/watchprobe.dom" "checked 40s ago" "!nobody watches") || watches+=("40 s: $why")
  grep -q '<span class="chip"[^>]*title="Lem looks at the forge every 60s for a merge or a close of the pull request' "$WORK/watchprobe.dom" || watches+=("40 s: the chip's hover")
  watch_at 200 && draw watchprobe
  why=$("$PY" -I -B -c "$SHOWN" "$WORK/watchprobe.dom" "nobody watches the pull request · type /lem" "!checked") || watches+=("200 s: $why")
  watch_at 5 "gh is not signed in" && draw watchprobe
  why=$("$PY" -I -B -c "$SHOWN" "$WORK/watchprobe.dom" "nobody watches the pull request · type /lem" "!checked") || watches+=("ended: $why")
  grep -q 'The watch ended: gh is not signed in. Type /lem' "$WORK/watchprobe.dom" || watches+=("ended: the reason in the hover")
  rm -f "$STATE/watch.js" "$STATE/watchprobe.html"
  if [ "${#watches[@]}" -eq 0 ]; then
    pass "beside the proposed requests the board says when the pull requests were last checked, and that nobody watches, with /lem to type, when no watch ran, when its last look is older than three of its intervals and when it ended, with why in the hover"
  else
    fail "the watch's chip: ${watches[*]}"
  fi

  # The read of a builder's resolution of a conflict is no round: the task's board names it apart. A folder of its own,
  # so that no lane or time card of the fixture changes.
  mkdir -p "$WORK/resolved"
  cp "$STATE/board.html" "$WORK/resolved/task-resolved.html" && cp "$STATE/lem.css" "$STATE/lem.js" "$WORK/resolved/"
  "$PY" -I -c 'import json, sys
at = sys.argv[2]
common = {"kind": "read", "verdict": "clean", "must_fix": 0, "should": 0, "nit": 0, "answered": ["codex"], "silent": [], "ran": [], "left_out": [], "tip": "abc1234"}
events = [{"ts": at, "event": "task.state", "task": "resolved", "status": "landing", "text": "the checks start", "lines": [], "ask": "Keep both lines"},
          {"ts": at, "event": "review", "task": "resolved", "attempt": 1, "round": 1, **common},
          {"ts": at, "event": "review", "task": "resolved", "attempt": 2, "round": 1, "of": "resolution", **common}]
open(sys.argv[1] + "/events.js", "w").write("".join("lemEvent(" + json.dumps(e) + ");\n" for e in events))
open(sys.argv[1] + "/meta.js", "w").write("lemMeta(" + json.dumps({"repo": "shop", "base": "main", "session": "", "ask": "lem-ask", "gates": 1}) + ");\n")' "$WORK/resolved" "$NOW"
  "$PY" -I -c "$STOP" "$WORK/resolved/task-resolved.html" "$NOW"
  headless --virtual-time-budget=5000 --dump-dom "file://$WORK/resolved/task-resolved.html" > "$WORK/resolved.dom"
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/resolved.dom" "round 1, one read: clean, 0 must-fix, 0 should, 0 nit" "the conflict’s resolution, one read: clean, 0 must-fix, 0 should, 0 nit" "1 round · a read of a resolution" "!round 1, one read: clean, 0 must-fix, 0 should, 0 nit round 1"); then
    pass "the read of a conflict's resolution is drawn apart from the review's rounds, and the review card counts the rounds alone"
  else
    fail "the read of a resolution on the board: $why"
  fi

  draw "task-$G"
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$G.dom" "Decisions" "3 wait for you · 4 taken" \
    "Choice 7 waits for you: The note of a cancelled order" "options: keep it · leave it out" "recommended: keep it, because the export shows cancelled orders as they were" \
    "the personas: The merchant would keep it, the accountant is in doubt." 'It waits for your answer. If you say you are away, the build goes on with “keep it”, the recommended option.' \
    "Choice 4 waits for you: Email the merchants about the new column" "It waits for your answer, also while you are away: it sends something to a person. The experts advise on it and never take it." \
    "Choice 6 waits for you: A note longer than the cell" 'If you say you are away, the build goes on with “all of it”, the recommended option.' "!wait over" "!left" "!its wait is over" \
    "5. The header of the column → Gift note" "taken as the recommended option at " "as the task ran without you. The pull request is not green for it." \
    "1. The name of the new column → gift_note" "taken by the agent, because the other columns of the export are in snake case" "to undo: rename the column" \
    "2. Two notes on one order → both notes, with a semicolon between them" "taken by the personas, because a merchant reads both" "the personas: The merchant and the accountant both picked the semicolon." \
    "3. Where the note goes in the row → the last column" 'answered by you: “last, like the other new columns”' \
    "3 choices wait for you" "since it was asked · if you say you are away, the build goes on with"); then
    pass "the board of one task has a Decisions card: each choice that waits with what your away would take, an irreversible one that waits also then, one taken without you, and each taken one with what, by whom and why"
  else
    fail "the Decisions card: $why"
  fi
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$G.dom" "The two model families split on a criterion." "1 of 2 criteria flagged" \
    "read by 2 of 3 personas, two model families (opus, sol), run by Lem" "no answer from Accountant, sol (the model was at capacity)" "Approved by you after the personas’ read" \
    'A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has that text in its row.' "no test yet: the agent adds its tests in the plan") \
    && "$PY" -I -c 'import re, sys
dom = re.sub(r"<[^>]+>", " ", open(sys.argv[1], encoding="utf-8").read())
sys.exit(not dom.index("The two model families split") < dom.index("1 of 2 criteria flagged") < dom.index("read by 2 of 3 personas"))' "$WORK/task-$G.dom"; then
    pass "the Acceptance criteria card shows the personas' read with a split between the families said first, who answered of how many, who did not and why, and the owner's approval after it"
  else
    fail "the Acceptance criteria card: ${why:-the split is not said first}"
  fi
  draw task-correction-one
  # shellcheck disable=SC1112  # the curly quotes are the page's
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-correction-one.dom" "The fast track: Lem approved its one criterion in your name" \
    'You may still say “/lem standard-track”' "The personas do not read the one criterion of a task on the fast track." "fast track, because the request is one sentence." \
    "One builder makes the change" "!a correction" "!correction, because" "!one-rule"); then
    pass "a small change's Acceptance criteria card says that Lem approved its one criterion in your name, that you may call it full, and that the personas do not read it; the size of its criteria is a small change, and no text says correction"
  else
    fail "a small change's Acceptance criteria card: $why"
  fi
  # A small change has one builder and no lead: the builders' row from its start, and phases with no
  # criteria to wait in and no plan.
  if grep -q 'data-head="The builders · The change"' "$WORK/task-correction-one.dom" \
    && ! grep -q 'data-head="The agent · It plans the task"' "$WORK/task-correction-one.dom" \
    && why=$("$PY" -I -c 'import re, sys
dom = open(sys.argv[1], encoding="utf-8").read()
phases = re.findall(r"class=\"phase ?(cur|past)?\"><i[^>]*></i>([^<]*)<", dom)
names = [name for _, name in phases]
ok = names == ["Change", "Checks", "Review", "Proposed", "Landed"] and phases[0][0] == "cur"
print("" if ok else f"the phases are {phases}")
sys.exit(not ok)' "$WORK/task-correction-one.dom"); then
    pass "a small change is drawn as one builder's work, on the builders' row, and its phases are the change, the checks, the review, proposed and landed"
  else
    fail "a small change on the board: ${why:-its span on the time card}"
  fi

  draw "task-$L"
  # The rows and the legend are read from the card itself, so that a name elsewhere on the page cannot stand in for a row.
  if why=$("$PY" -I -B -c "$TIMECARD" "$WORK/task-$L.dom" "You|Lem|The agent|The builders|The personas|The checks|The review" \
    "You=1h 05m · 46%" "Lem=6m 00s · 4%" "The agent=17m · 12%" "The builders=42m · 30%" "The checks=5m 00s · 4%" "The review=11m · 8%") \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$L.dom" "Where the time went" "Criteria" "Plan" "T1" "T2" "Checks" "PR") \
    && ! grep -q 'class="nowline"' "$WORK/task-$L.dom" && grep -q 'class="ring-wrap"' "$WORK/task-$L.dom"; then
    pass "the time card of a task has a row for each actor that held its work and a band for each stage and plan task, and its legend gives each actor's total and share of the task's time"
  else
    fail "the time card: $why"
  fi
  # Under the card one short line; what the card leaves out is the hover of its legend.
  if grep -q '<div id="tl-note" class="tl-note">Each row is who held the work; a band is a stage. Hover the legend for how the shares add up.</div>' "$WORK/task-$L.dom" \
    && grep -q 'id="legend" class="legend" title="Rows overlap where the build goes on while a choice waits for you' "$WORK/task-$L.dom"; then
    pass "the time card's note is one short line, and the rest of what it said is the hover of the legend"
  else
    fail "the note of the time card: $(grep -o '<div id="tl-note"[^<]*' "$WORK/task-$L.dom")"
  fi
  # Each stage whose start is logged is a span from its start to the event that ends it, on the row
  # of who held the work, and the rest of each block is the coordinator's.
  draw "task-$S"
  # shellcheck disable=SC1112  # the curly quote is the page's
  if why=$("$PY" -I -B -c "$TIMECARD" "$WORK/task-$S.dom" "You|Lem|The agent|The builders|The personas|The checks|The review" \
      "You=33m · 30%" "Lem=6m 00s · 5%" "The agent=12m · 11%" "The builders=49m · 45%" "The personas=5m 00s · 5%" "The checks=5m 00s · 5%" "The review=4m 00s · 4%") \
    && grep -q 'data-head="You · The interview" data-sub="Lem asks you one question at a time"' "$WORK/task-$S.dom" \
    && grep -q 'data-head="The builders · The scout reads the code"' "$WORK/task-$S.dom" \
    && grep -q 'data-head="The personas · The personas’ read of the criteria" data-sub="3 of 3 answered, two model families · nobody confused"' "$WORK/task-$S.dom" \
    && ! grep -q '<circle[^>]*data-head="The personas' "$WORK/task-$S.dom" \
    && grep -q 'data-head="The builders · Task 1 of 2"' "$WORK/task-$S.dom" && grep -q 'data-head="The agent · It briefs the builder"' "$WORK/task-$S.dom" \
    && grep -q 'data-head="Lem · The rebase onto the base"' "$WORK/task-$S.dom" \
    && grep -q 'data-head="The builders · The polish pass" data-sub="abc1234 → def5678 · 1 commit"' "$WORK/task-$S.dom" \
    && grep -q 'data-head="The checks · The checks: make test"' "$WORK/task-$S.dom" \
    && grep -q 'data-head="The review · Review round 1: one read"' "$WORK/task-$S.dom" \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$S.dom" feed "A builder started · task 1 of 2" "The checks started|2 commands on def567890" "The review started|attempt 1 · one read" \
      "The interview started" "The scout started" "The personas’ read of the criteria started|run by Lem" "The polish pass started|on abc123456"); then
    pass "the interview, the scout, the personas' read, each builder, the polish pass, the checks and the review are drawn from their logged start to the event that ends each, on the row of who held the work, and the activity says each start in words"
  else
    fail "the logged starts on the time card: ${why:-a span of a stage}"
  fi
  # A step that started and has not ended runs to now: the checks with no result yet, an investigation.
  draw task-gate-runs && draw task-cart-total-wrong
  if grep -q 'data-head="The checks · The checks run: 0 of 2 commands done"' "$WORK/task-gate-runs.dom" \
    && grep -q 'data-head="Lem · The rebase onto the base"' "$WORK/task-gate-runs.dom" \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-gate-runs.dom" now "The checks run") \
    && grep -Eq 'class="seg live"[^>]*data-head="The builders · The investigation"' "$WORK/task-cart-total-wrong.dom"; then
    pass "a step whose start is logged and whose end is not runs to now: the checks with no result yet, and an investigation"
  else
    fail "a step that runs: ${why:-a live span}"
  fi
  # The hover, as a reader's mouse makes it: over a band of the plan, and over a span of the owner's row.
  cat > "$STATE/probe.html" <<'PROBE'
<!doctype html><meta charset="utf-8"><iframe id="f" src="task-landed-one.html" style="width:1400px;height:1400px;border:0"></iframe><pre id="out"></pre>
<script>
const wait = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  await wait(1500);
  const w = document.getElementById('f').contentWindow, d = w.document, log = {};
  // the time card is on the tab Timeline
  d.querySelector('[data-tab="timeline"]').click(); await wait(300);
  const hover = node => {
    const box = node.getBoundingClientRect();
    node.dispatchEvent(new w.MouseEvent('mousemove', {bubbles: true, clientX: box.left + Math.min(4, box.width / 2), clientY: box.top + box.height / 2}));
    const tip = d.getElementById('tip');
    return tip.hidden ? 'hidden' : [...tip.children].map(n => n.textContent).join(' | ');
  };
  log.band = hover(d.querySelector('[data-head="Task 1"]'));
  log.span = hover(d.querySelector('[data-head^="You · Choice 1"]'));
  log.mark = hover(d.querySelector('circle[data-head^="The personas"]'));
  d.getElementById('tl-wrap').dispatchEvent(new w.MouseEvent('mouseleave'));
  log.left = d.getElementById('tip').hidden;
  document.getElementById('out').textContent = JSON.stringify(log);
})().catch(e => { document.getElementById('out').textContent = JSON.stringify({error: String(e)}); });
</script>
PROBE
  headless --allow-file-access-from-files --virtual-time-budget=8000 --dump-dom "file://$STATE/probe.html" > "$WORK/probe.dom"
  rm -f "$STATE/probe.html"
  # shellcheck disable=SC1112  # the apostrophe in the expected hover is the page's own
  hovered=$("$PY" -I -c 'import html, json, re, sys
found = re.search(r"<pre id=\"out\">(.*?)</pre>", open(sys.argv[1], encoding="utf-8").read(), re.S)
d = json.loads(html.unescape(found.group(1))) if found and found.group(1) else {"error": "the probe printed nothing"}
wrong = [name for name, ok in {
    "an error": "error" not in d,
    "a band: its stage, its length and its two clock times": d.get("band") == "Task 1 | of 2 | 18m · Nov 10 09:40:00 → 09:58:00",
    "a span: who, what, its length and its clock times": d.get("span", "").startswith("You · Choice 1: The symbol or the code of the currency | you answered: the code | 7m 00s · Nov 10 10:05:00 → 10:12:00"),
    "a mark: what ended, and when": d.get("mark", "").startswith("The personas · The personas’ read of the criteria ended | 2 of 2 answered") and d.get("mark", "").endswith("at Nov 10 09:10:00"),
    "the hover goes when the mouse leaves": d.get("left") is True,
}.items() if not ok]
print("; ".join(wrong) or "ok", "" if not wrong else json.dumps(d))' "$WORK/probe.dom" 2>&1 || true)
  if [ ! -s "$WORK/probe.dom" ]; then
    skip "the hover of the time card: $chrome printed no page"
  elif [ "$hovered" = "ok " ]; then
    pass "a hover on a band, a span or a mark of the time card says what it is, how long it took and its two clock times, as in \"Task 1 · 18m · 09:40:00 → 09:58:00\""
  else
    fail "the hover of the time card: $hovered"
  fi

  draw "task-$T"
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$T.dom" "The review 4m 00s · 4%" "Lem 2m 00s · 2%" "The checks 4m 00s · 4%"); then
    pass "a review logged in the same second as the next state block is still the review's time: the order of the log, not the second, says which block an event belongs to"
  else
    fail "an event in the second of the next block: $why"
  fi
  draw task-red-gate
  # The task is open, so its card runs to NOW, where the page's clock stands: Lem holds 30m, the checks 10m.
  if why=$("$PY" -I -B -c "$TIMECARD" "$WORK/task-red-gate.dom" "You|Lem|The checks" "The checks=10m · 25%" "Lem=30m · 75%") \
    && grep -q 'data-head="Lem · After a failed check: a repair or a stop, and no event says which yet"' "$WORK/task-red-gate.dom" \
    && ! grep -q 'data-head="The checks · The checks run' "$WORK/task-red-gate.dom"; then
    pass "a gate run whose first command failed is checks until its last command, with no repair between its commands, and after the whole run failed the time is not drawn as checks that go on"
  else
    fail "after a failed check: ${why:-the span after the red gate}"
  fi
  draw task-read-first
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-read-first.dom" "No state was written yet for the task \"read-first\": its 1 event is in the activity below" \
    "The personas read the criteria" "nobody confused · 2 of 2 answered"); then
    pass "the board of a task whose criteria were read before its first state block draws its events and says that its state comes later"
  else
    fail "a task with events and no state: $why"
  fi
  draw task-approved-again
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-approved-again.dom" "1. A slip for Berlin or Vienna is in German." \
    "approved after the plan’s criteria were recorded: the agent records them again, with their tests" "approval 2; it replaces approval 1" \
    "!held by its tests" "!A slip for Berlin is in German." "standard track, because the slip gets a language."); then
    pass "after a new approval the Acceptance criteria card shows the approved criteria, not the plan's older ones and their tests' result"
  else
    fail "criteria approved after the plan's: $why"
  fi
  draw task-restored-read && draw task-unread-change
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-restored-read.dom" "Criterion 1 changed during the build" "!the change was not read") \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-unread-change.dom" "The criteria changed after this read by a change of the build, and the change was not read."); then
    pass "the Acceptance criteria card says that a change was not read only while the criteria as they stand are not the ones read: his approval of the read criteria again clears it"
  else
    fail "the unread change: $why"
  fi
  draw task-clear-read-held
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-clear-read-held.dom" "Nobody confused" "The criteria wait for your yes" "!The build started with no wait for you"); then
    pass "a read that found nobody confused does not say that the build started, while the criteria wait for the owner's yes"
  else
    fail "a clear read that waits for him: $why"
  fi
  draw "task-$C"
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$C.dom" "approval 2; it replaces approval 1" \
    "Criterion 1 changed during the build" "Approved by you afterwards (approval 2): it is yours, and no cause of not green" \
    "Criterion 2 changed during the build" "the counter goes on · by the agent · the pull request is not green for it" \
    "!a year keeps the names apart · by the agent · the pull request is not green for it"); then
    pass "a criterion change that the owner's later approval took over is his and no cause of not green, and a change after that approval still is one"
  else
    fail "criterion changes and approvals: $why"
  fi
  draw task-rare-path
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-rare-path.dom" "Frozen by the personas’ read, with no wait for you" "!The fast track: Lem approved" "!Approved by you"); then
    pass "criteria the personas' read froze for a full change from a complete request are shown as such, never as a small change or as the owner's yes"
  else
    fail "the read's approval: $why"
  fi

  # The experts' advice. Each check reads one row of one card, or of Waits for you, so that a text of
  # another choice or of the activity cannot stand in for it.
  draw "task-$X"
  # shellcheck disable=SC1111,SC1112  # the curly quotes around a pick are the page's
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" decisions \
      "Choice 4 waits for you: The font of the invoice|Fable picks “serif”, because a printed invoice reads better in serif|Astra picks “serif”, because the letters of the shop are in serif|If you say you are away, the build goes on with “serif”, the experts’ shared pick.|Where you answer: Lem puts choice 4 to you as a page in its session. Answer it there: it waits for your answer. If you say you are away, the build goes on with the experts’ shared pick.|!the recommended option" \
      "Choice 5 waits for you: The size of the total|Fable finds that none of the options fits, because the total should be bold, not bigger|Astra picks “12 pt”, because the other lines are 12 pt|If you say you are away, the build goes on with “14 pt”, the recommended option.|the build goes on with the recommended action.|!the experts’ shared pick" \
      "1. The paper size|!Fable picks|!waits for you") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" now \
      "2 choices wait for you|The font of the invoice|the experts: Fable “serif” · Astra “serif”|if you say you are away, the build goes on with “serif”, the experts’ shared pick") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/board-waits.dom" waits-rows \
      "The font of the invoice|~^Answer choice 4 Expert advice · Print the invoice for the post The font of the invoice · recommended: sans · the experts: Fable “serif” · Astra “serif” .* [0-9][0-9ms ]* since it was asked Open the task$" \
      "The size of the total|~^Answer choice 5 Expert advice .* the experts: Fable none fits · Astra “12 pt” .* [0-9][0-9ms ]* since it was asked Open the task$"); then
    pass "a choice that waits shows each expert's advice in its own row of the Decisions card, a pick or none fits with its reasons, and its row and the head of its board say that the owner's away takes the experts' shared pick when both agree, else the recommended option; its row of Waits for you says how long it waits"
  else
    fail "the experts' advice on a choice that waits: $why"
  fi
  # shellcheck disable=SC1111,SC1112  # the curly quotes around a pick are the page's
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" decisions \
      "1. The paper size → A4|@a-bad|~taken by the experts, as both picked it, at [0-9]{2}:[0-9]{2}, as the task ran without you\. The pull request is not green for it\.|Fable picked “A4”, because every customer of the shop is in Europe, where the post reads A4|Astra picked “A4”, because the envelopes of the shop are cut for A4|~Your answer came at [0-9]{2}:[0-9]{2}, after it was taken: “Letter” \(Letter, it is in the tray\)\. It differs from what was taken|!as the recommended option") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" feed \
      "Choice 1 taken by the experts without you|A4|Fable: every customer of the shop is in Europe, where the post reads A4 · Astra: the envelopes of the shop are cut for A4" \
      "Your answer to choice 1 came after it was taken|Letter") \
    && grep -Eq 'data-head="You · Choice 1: The paper size" data-sub="“A4” was taken at [0-9]{2}:[0-9]{2}, as the task ran without you"' "$WORK/task-$X.dom"; then
    pass "a choice the experts took without the owner is in the Decisions card as taken by the experts, marked like a timeout, with their pick and both reasons, and his answer after it as after it was taken; the activity and the time card say so"
  else
    fail "a choice the experts took: ${why:-the hover of the choice the experts took}"
  fi
  # shellcheck disable=SC1111,SC1112  # the curly quotes around a pick are the page's
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" decisions \
      "2. The color of the logo → the green of the shop|@a-bad|~taken by the experts, as both picked it, at [0-9]{2}:[0-9]{2}, as the task ran without you\. The pull request is not green for it\.|Fable picked “the green of the shop”, because the invoice is a page of the shop|Astra picked “the green of the shop”, because the printer prints in color|!as the recommended option" \
      "3. The order number on the page → at the top|@a-bad|~taken as the recommended option at [0-9]{2}:[0-9]{2}, as the task ran without you\. The pull request is not green for it\.|the experts split: Fable picked “at the top”, because a reader looks for it first · Astra picked “at the foot”, because the top holds the address window|!taken by the experts") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" feed \
      "Choice 2 taken by the experts without you|the green of the shop|Fable: the invoice is a page of the shop · Astra: the printer prints in color" \
      "Choice 3 taken without you|at the top|!experts" \
      "Astra advised on choice 3|picks “at the foot”|the top holds the address window" \
      "Fable advised on choice 5|none of the options fits|the total should be bold, not bigger") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" progress "Decisions|3 taken, 1 by the timeout, 2 by the experts") \
    && grep -Eq 'data-head="You · Choice 2: The color of the logo" data-sub="“the green of the shop” was taken at [0-9]{2}:[0-9]{2}, as the task ran without you"' "$WORK/task-$X.dom"; then
    pass "a choice taken without the owner with the experts' shared pick names them with both reasons, and one whose experts split is the recommended option with each expert's advice, in the Decisions card, the activity, the count of decisions and the time card"
  else
    fail "a timeout with the experts' advice: ${why:-the hover of the timeout the experts took}"
  fi
  draw "task-$P" && draw task-landing-starts
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$P.dom" feed "The polish pass|2 commits, 1 item filed in the backlog|abc1234 → def5678|docs/backlog/invoice-footer-typo.md") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$P.dom" feed "Careful by the review, not by the plan|round 1: the file name holds the order's total, which a customer pays") \
    && why=$("$PY" -I -B -c "$TIMECARD" "$WORK/task-$P.dom" "You|Lem|The builders|The checks" "Lem=10m · 25%" "The builders=18m · 45%" "The checks=12m · 30%") \
    && grep -q 'data-head="The builders · The polish pass" data-sub="abc1234 → def5678 · 2 commits"' "$WORK/task-$P.dom" \
    && grep -q 'data-head="The checks · The checks run: 0 of 2 commands done"' "$WORK/task-$P.dom" \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$P.dom" now "The checks run") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-landing-starts.dom" now "It starts its landing: the rebase onto the base, then the polish pass|!The checks and the review run on it") \
    && grep -q 'data-head="Lem · The landing starts: the rebase onto the base, then the polish pass, and no event says which runs yet"' "$WORK/task-landing-starts.dom" \
    && ! grep -q 'data-head="The checks · The checks run"' "$WORK/task-landing-starts.dom"; then
    pass "the polish pass is in the activity with its commits and the items it filed, and on the time card as the builders' span from its start; a landing with no polish and no check yet says that it starts, not that its checks run; a careful call the review made and the plan missed is in the activity with the review's reason"
  else
    fail "the polish pass: ${why:-a span of the time card}"
  fi
  # The plan talk from its start to its record is a span of the review's row, with its counts; with
  # no start in the log it is a dot where it ended, and with a start and no record yet it runs.
  draw "task-$K" && draw task-talk-runs && draw "task-$L"
  if grep -q 'data-head="The review · The plan talk" data-sub="with codex: 3 questions in 7 turns · 2 settled, 1 open, 1 of them a design choice · 2 repaired: 1 at the cause, 1 a layer over a cited decision · 1 decision two questions named · 2 raised, not argued"' "$WORK/task-$K.dom" \
    && why=$("$PY" -I -B -c "$TIMECARD" "$WORK/task-$K.dom" "You|The agent|The review" "The agent=25m · 100%" "The review=18m · 72%") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$K.dom" feed "The plan talk started|with codex" "The plan talk ended|with codex: 3 questions in 7 turns|1 of them a design choice|2 raised, not argued") \
    && ! grep -q 'data-sub="[^"]*its start is not logged' "$WORK/task-$K.dom" \
    && grep -q 'data-head="The review · The plan talk ended" data-sub="with codex: 4 questions in 19 turns, over the bound of 18 for its 4 questions · 3 settled, 1 open, 1 of them a design choice · 2 repaired: 2 at the cause · 1 raised, not argued · its start is not logged"' "$WORK/task-$L.dom" \
    && grep -q 'data-head="The review · The plan talk runs" data-sub="with claude; its record comes when the talk ends"' "$WORK/task-talk-runs.dom"; then
    pass "the plan talk is the review's span from its start to its record, with its questions, turns, settled, open, design choices, repairs at the cause and layers over a cited decision, decisions two questions named and questions raised and not argued; one with no start logged is a dot where it ended, and one with no record yet runs"
  else
    fail "the plan talk on the time card: ${why:-a span or a dot of the talk}"
  fi
  # The talk's companion is shown as a companion of the talk, and the builder lead after it.
  draw "task-$M"
  if grep -q 'title="A companion session talks the plan through, with the reviewer in its other pane; an agent builds it after the talk' "$WORK/task-talk-runs.dom" \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-talk-runs.dom" "Its companion talks the plan through" "plan talk" "a companion talks the plan through, with the reviewer in its other pane" "!Its session builds it" "!defend") \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$M.dom" "one agent builds the plan its companion talked through" "An agent builds it" "!builder lead") \
    && grep -q 'data-head="Lem · The plan talk is done: the plan waits for the agent that builds it"' "$WORK/task-$M.dom" \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$M.dom" feed "The plan talk ended|with codex: 2 questions in 5 turns|2 repaired: 1 a layer over a cited decision|!at the cause") \
    && grep -q 'title="A companion session talks the plan through' "$WORK/board.dom" && why=$("$PY" -I -B -c "$SHOWN" "$WORK/board.dom" "!one agent"); then
    pass "a task whose plan talk runs in its companion shows the companion as the talk's, and after the talk the builder lead that builds it, with the wait between the two as Lem's and the layer the talk accepted"
  else
    fail "the talk's companion and the builder after it: ${why:-a tag, a head or a span}"
  fi
  # An answered task is in the lane of what ended, with its investigation's answer, on the board and on its own.
  draw "task-$A"
  if why=$("$PY" -I -B -c "$LANES" "$WORK/board.dom" "Done=Refund shows zero|") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/board.dom" lanes \
      "Refund shows zero|No bug: a refund is a credit note, and the invoice shows what is left to pay|fix|!Waits for you|!Answered: not a bug") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$A.dom" now \
      "Answered: it ended with a report and nothing to merge|Closed|No bug: the code does what it should:|a refund is a credit note, and the invoice shows what is left to pay|billing/invoice.py:total|reproduced|investigation.md in the task directory") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$A.dom" feed \
      "The investigation found no bug|a refund is a credit note, and the invoice shows what is left to pay|billing/invoice.py:total · reproduced" "Answered|!not a bug: the invoice shows what is left to pay") \
    && ! grep -q 'class="phase cur"' "$WORK/task-$A.dom" \
    && grep -q 'data-head="The builders · The investigation" data-sub="an investigator reproduces the bug and finds its cause · fix, because the ask says the total is wrong today"' "$WORK/task-$A.dom" \
    && grep -q 'data-head="Investigation"' "$WORK/task-$A.dom" && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$A.dom" "Inv." "!Waits for you"); then
    pass "an answered task is in the lane of what ended with its type and its investigation's answer; its own board says it ended with a report, names the call, the cause's place and the report, and draws the investigation as the builders' span"
  else
    fail "an answered task: ${why:-the span of the investigation, or a phase marked as current}"
  fi
  draw task-cart-total-wrong
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/board.dom" lanes "Cart total wrong|Investigating: an investigator reproduces the bug and finds its cause|fix") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-cart-total-wrong.dom" now "The investigator acts|Its investigator examines it, before any criterion|fix, because the ask says the total is wrong since yesterday|!lead") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-cart-total-wrong.dom" feed "The investigation started|an investigator reproduces the bug and finds its cause|!a builder"); then
    pass "a task whose investigation runs says so on its card and on its own board, and names the investigator, not a lead and not a builder"
  else
    fail "a task whose investigation runs: $why"
  fi
  # The investigation is the first step of the task's phases while it runs, and the time card of a
  # span under six minutes reads its axis to the second, so no two ticks say the same minute.
  if grep -Eq 'class="phase cur"><i[^>]*></i>Investigation<' "$WORK/task-cart-total-wrong.dom" \
    && ! grep -q 'class="phase past"' "$WORK/task-cart-total-wrong.dom" \
    && grep -Eq 'class="phase past"><i[^>]*></i>Investigation<' "$WORK/task-$A.dom" \
    && why=$("$PY" -I -c 'import re, sys
dom = open(sys.argv[1], encoding="utf-8").read()
area = dom[dom.index("id=\"timeline\""):]
ticks = re.findall(r"<text class=\"axis\"[^>]*>([^<]*)</text>", area)
ok = len(ticks) == 7 and len(set(ticks)) == 7 and all(re.fullmatch(r"\d\d:\d\d:\d\d", x) for x in ticks)
print("" if ok else f"the ticks are {ticks}")
sys.exit(not ok)' "$WORK/task-cart-total-wrong.dom"); then
    pass "a task whose bug is investigated has the investigation as its first phase, current while it runs and done after it, and a short time card reads its axis to the second"
  else
    fail "the investigation's phase or a short axis: ${why:-a phase}"
  fi
  # An answered task lands nowhere and has no criteria, decisions, checks or review: none is drawn empty.
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$A.dom" "!lands on" "!The agent writes the criteria") \
    && grep -Eq 'id="criteria-card"[^>]* hidden' "$WORK/task-$A.dom" && grep -Eq 'id="decisions-card"[^>]* hidden' "$WORK/task-$A.dom" \
    && grep -Eq 'id="gate-card"[^>]* hidden' "$WORK/task-$A.dom" && grep -Eq 'id="review-card"[^>]* hidden' "$WORK/task-$A.dom" \
    && ! grep -Eq 'id="decisions-card"[^>]* hidden' "$WORK/task-$G.dom"; then
    pass "an answered task names no branch it lands on, and draws no empty card of criteria, decisions, checks or review"
  else
    fail "the empty cards of an answered task: ${why:-a card is drawn}"
  fi
  # The rest of an answered task's card: its phases end with the answer, and its checks and review say why there are none.
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$A.dom" progress "Investigation|Answered|!Criteria|!Landed|none: it ended with a report") \
    && [ "$(grep -o 'class="phase past"' "$WORK/task-$A.dom" | wc -l | tr -d ' ')" = 2 ]; then
    pass "an answered task's phases are its investigation and its answer, and its checks and review say that it ended with a report"
  else
    fail "the phases of an answered task: ${why:-a phase is not done}"
  fi
  # The time card gives the task's whole time beside the rows' totals, which are shares of it; a
  # choice that no expert advised on yet says so in one line.
  # shellcheck disable=SC1111,SC1112  # the curly quotes are the page's
  if grep -Eq '<span class="whole"[^>]*>2h 20m in all</span>' "$WORK/task-$L.dom" \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$G.dom" decisions "Choice 7 waits for you: The note of a cancelled order|No expert advised on it yet.|!Fable: no advice yet|!Astra: no advice yet"); then
    pass "the time card says the task's whole time beside the rows' shares of it, and a choice with no advice yet says so in one line"
  else
    fail "the whole time, or the experts' empty advice: ${why:-no whole time on the card}"
  fi
  # A read in which nobody answered says so, in the bad color, with each persona that was silent.
  draw task-silent-read && draw task-queued-after && draw task-queued-one
  # shellcheck disable=SC1111,SC1112  # the curly quotes are the page's
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-silent-read.dom" criteria "Nobody answered the personas’ read|(0 of 2)|@a-bad|no answer from Merchant, opus (the model timed out)|no answer from Accountant, sol|!Nobody confused|!read by 0") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-queued-after.dom" now "Waits for the task it needs|!free place|it starts after “Building one” ends") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-queued-one.dom" now "Waits to start|!task it needs|!free place") \
    && why="no block of the queued time names the task it needs" && [ "$(shown_text task-queued-after "Queued: it waits for the task it needs")" -gt 0 ] \
    && why="the page of a task with no after: line names a task it needs" && [ "$(shown_text task-queued-one "task it needs")" = 0 ] \
    && [ "$(shown_text task-queued-one "Queued: it waits to start")" -gt 0 ]; then
    pass "a read of the criteria that no persona answered is shown as no read, with who was silent and why; a queued task with no after: line says it waits to start, and one queued behind another says it waits for the task it needs, which it names once"
  else
    fail "a read nobody answered, or a task queued after another: $why"
  fi
  # The activity is in time order, the newest first, also where the log is not: the investigation of
  # "Cart total wrong" was written a minute before NOW and before the checks of "Gate runs", which
  # the fixture moved to five minutes before NOW. Two events of one second keep the log's order, the
  # later first: the careful call of "Polished" after its polish pass.
  if why=$("$PY" -I -c 'import re, sys
wrong = []
for path in sys.argv[1:]:
    dom = open(path, encoding="utf-8").read()
    feed = dom[dom.index("id=\"feed\""):]
    times = [int(x) for x in re.findall(r"<div class=\"row [^\"]*\" data-at=\"(\d+)\"", feed)]
    if not times or times != sorted(times, reverse=True): wrong.append(path.rsplit("/", 1)[-1] + f": {len(times)} rows, not newest first")
board = open(sys.argv[1], encoding="utf-8").read()
board = board[board.index("id=\"feed\""):]
first, second = board.find("Cart total wrong</button> · <b>The investigation started"), board.find("Gate runs</button> · <b>The checks started")
if not 0 <= first < second: wrong.append(f"the investigation of Cart total wrong is at {first}, the checks of Gate runs at {second}")
polished = open(sys.argv[2], encoding="utf-8").read()
polished = polished[polished.index("id=\"feed\""):]
if not 0 <= polished.find("Careful by the review") < polished.find("The polish pass"): wrong.append("the two events of one second of Polished are not the later first")
print("; ".join(wrong))
sys.exit(bool(wrong))' "$WORK/board.dom" "$WORK/task-$P.dom" "$WORK/task-$S.dom" "$WORK/task-$L.dom"); then
    pass "the activity is in time order, the newest first, on the board of all tasks and on a task's own, also where the log's order is not the time's; two events of one second keep the log's order, the later first"
  else
    fail "the order of the activity: $why"
  fi
  # A task that ended says no "yet": nothing more comes for it.
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$S.dom" "!yet" "none" "no commit of its branch is on record" "no test of it is on record: the plan’s criteria were never recorded"); then
    pass "the board of a task that ended says no \"yet\" (no decision, no commit, no test on record)"
  else
    fail "a task that ended: $why"
  fi
  # The board of all tasks: its activity is a card of its own across the page, with none of a task's
  # panels beside it, and its legend has one entry for each look of a bar, so three statuses drawn in
  # one color are one entry.
  if grep -Eq '<section id="feed-card" class="card" data-tasks(="")? data-task-tab="timeline">' "$WORK/board.dom" \
    && grep -Eq 'id="crit-panel"[^>]* hidden' "$WORK/board.dom" && grep -Eq 'id="checks-panel"[^>]* hidden' "$WORK/board.dom" \
    && why=$("$PY" -I -c 'import html, re, sys
dom = open(sys.argv[1], encoding="utf-8").read()
area = dom[dom.index("id=\"legend\""):]
area = area[:area.index("</div>")]
items = [(cls, i or "", html.unescape(label)) for cls, i, label in re.findall(r"<span class=\"([^\"]*)\"[^>]*><i(?: class=\"([^\"]*)\")?></i>([^<]*)</span>", area)]
looks = [(cls, i) for cls, i, _ in items]
labels = [label for *_, label in items]
ok = len(set(looks)) == len(looks) and "Waits for you · Waits for the merge" in labels and "Waits for the merge" not in labels
print("" if ok else f"the legend is {items}")
sys.exit(not ok)' "$WORK/board.dom"); then
    pass "on the board of all tasks the activity takes the whole width, and the legend has one entry for each look of a bar: the statuses that wait for the owner share one"
  else
    fail "the activity's width or the legend: ${why:-the activity is in a column}"
  fi
  # The backlog tab counts the items whose place is gone or cannot be read, in a sentence.
  draw board backlog
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/board-backlog.dom" "4 items in docs/backlog · 2 items name a place that is gone or cannot be read" \
    "billing/gone.py:total · the file is not there" "locked.txt:secret · the file cannot be read" "Decided against" "!points at" "!2 point "); then
    pass "the backlog tab says how many items name a place that is gone or cannot be read, and marks each one"
  else
    fail "the backlog tab: $why"
  fi
  # A fixed line of a state block is said in words on every page, or left out; never shown as it is written.
  raw=()
  for dom in "$WORK/board.dom" "$WORK"/task-*.dom; do
    [ -e "$dom" ] || continue
    why=$("$PY" -I -B -c "$SHOWN" "$dom" "!lead: builder" "!lead: session" "!session: C0FFEE" "!plan committed" "!investigation: bug" "!type: fix" "!kind: bug" "!after: building-one" "!report: investigation.md" \
      "!small change: one builder" "!the owner" "!careful path" "!interview.start" "!scout.start" "!criteria.read.start" "!investigation.start" "!builder.start" "!polish.start" "!gate.start" "!review.start") \
      || raw+=("$(basename "$dom"): $why")
  done
  if [ "${#raw[@]}" -eq 0 ] \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/board.dom" lanes "Correction one|One builder makes the change|fast track" "Talk runs|Its companion talks the plan through|plan talk"); then
    pass "no page shows a fixed line of a state block or a stage's start as it is written, says the owner in the third person, or names a careful path: who works on a task, its plan, its kind, its investigation and what it waits for are said in words to you"
  else
    fail "a fixed line of a state block: ${raw[*]:-} ${why:-}"
  fi
  # LOOK CHECK DOM...: what a reader sees of one part of a page, read from the elements themselves.
  #   cards DOM 'TITLE|TEXT|!TEXT'...  a lane card, by its title, holds each TEXT and not each !TEXT
  #   likeit DOM                       the large card counts the other tasks with a wait of its kind
  #   timer DOM...                     each large timer says its unit
  #   shares DOM WANT                  the legend says the shares' sum when they add up past 100 (WANT
  #                                    "sum"), or says nothing of it ("none")
  #   terms DOM...                     every place a word of Lem's own stands has its meaning on hover
  LOOK=$(cat <<'PY'
import html, re, sys
from html.parser import HTMLParser
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
class Node:
    def __init__(self, tag, attrs, up):
        self.tag, self.attrs, self.up, self.kids = tag, dict(attrs), up, []
    def cls(self):
        return (self.attrs.get("class") or "").split()
    def text(self):
        return " ".join(" ".join(k if isinstance(k, str) else k.text() for k in self.kids).split())
    def all(self):
        for k in self.kids:
            if not isinstance(k, str):
                yield k
                yield from k.all()
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.root = Node("root", [], None); self.at = self.root; self.texts = []
    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.at); self.at.kids.append(n)
        if tag not in VOID: self.at = n
    def handle_endtag(self, tag):
        n = self.at
        while n is not self.root and n.tag != tag: n = n.up
        if n is not self.root: self.at = n.up
    def handle_data(self, data):
        self.at.kids.append(data); self.texts.append((data, self.at))
def read(path):
    p = P(); p.feed(open(path, encoding="utf-8").read()); return p
check, *args = sys.argv[1:]
wrong = []
if check == "cards":
    p = read(args[0])
    cards = {}
    for n in p.root.all():
        if n.tag == "button" and "tcard" in n.cls():
            title = next((k.text() for k in n.all() if "tc-title" in k.cls()), "")
            cards[title] = n.text()
    for want in args[1:]:
        title, *needs = want.split("|")
        if title not in cards: wrong.append(f"no card {title!r}"); continue
        for need in needs:
            if (need[1:] in cards[title]) if need.startswith("!") else (need not in cards[title]):
                wrong.append(f"the card {title!r} {'holds' if need.startswith('!') else 'does not hold'} {need.lstrip('!')!r}: {cards[title]!r}")
elif check == "likeit":
    p = read(args[0])
    lane = next(n for n in p.root.all() if "lane" in n.cls() and any("lane-head" in k.cls() and k.text().startswith("Waits for you") for k in n.kids if not isinstance(k, str)))
    choices = [k for k in lane.all() if "tc-wait" in k.cls()]
    others = len(choices) - 1
    now = next(n for n in p.root.all() if n.attrs.get("id") == "now").text()
    said = re.search(r"(\d+) more tasks? like it", now)
    if others > 0 and (not said or int(said.group(1)) != others):
        wrong.append(f"{len(choices)} tasks have a choice that waits, and the large card says {said.group(0) if said else 'no count'!r}")
elif check == "timer":
    for path in args:
        for n in read(path).root.all():
            if "timer" in n.cls() and not re.search(r"\d+\s*[hms]\b", n.text()):
                wrong.append(f"{path.rsplit('/', 1)[-1]}: the timer {n.text()!r} has no unit")
elif check == "shares":
    p = read(args[0])
    legend = next(n for n in p.root.all() if n.attrs.get("id") == "legend")
    total = sum(int(x) for x in re.findall(r"· (\d+)%", " ".join(k.text() for k in legend.all() if k.tag == "em")))
    said = re.search(r"the shares add up to (\d+)%", legend.text())
    if args[1] == "sum" and (total <= 100 or not said or int(said.group(1)) != total):
        wrong.append(f"the shares add up to {total}%, and the legend says {said.group(0) if said else 'nothing of it'!r}")
    if args[1] == "none" and said:
        wrong.append(f"the shares add up to {total}%, and the legend says {said.group(0)!r}")
elif check == "terms":
    TERMS = {r"\bcompanion\b": "The companion:", r"\bplan talk\b": "The plan talk:", r"\btrust prompt\b": "A trust prompt:"}
    found = {t: 0 for t in TERMS}
    for path in args:
        for data, at in read(path).texts:
            for term, meaning in TERMS.items():
                if not re.search(term, data, re.I): continue
                if {"tc-title", "rlink"} & set(at.cls()) or (at.tag == "h1" and path.rsplit("/", 1)[-1].startswith("task-")): continue  # a task's name
                n = at
                while n is not None and n.tag not in ("svg", "script", "style", "title") and "title" not in n.attrs: n = n.up
                if n is not None and n.tag in ("svg", "script", "style", "title"): continue
                found[term] += 1
                if n is None or meaning not in n.attrs["title"]:
                    wrong.append(f"{path.rsplit('/', 1)[-1]}: {data.strip()!r} has no hover with {meaning!r}")
    wrong += [f"no page holds {term!r}" for term, n in found.items() if not n]
print("; ".join(dict.fromkeys(wrong)))
sys.exit(bool(wrong))
PY
)
  # The type is shown as Lem wrote it, on a task of either track, and only the one builder of the fast
  # track puts a task on the fast track.
  if why=$("$PY" -I -B -c "$LOOK" cards "$WORK/board.dom" "Building one|fix|!fast track|!one-rule" "Correction one|One builder makes the change|fast track|!one-rule"); then
    pass "the type fix shows as fix, also on a task with a plan, and the track shows only as the fast track chip of a task with one builder"
  else
    fail "the type and the track: $why"
  fi
  # A12: each small thing of the look a reader stumbled on.
  if why=$("$PY" -I -B -c "$LOOK" likeit "$WORK/board.dom"); then
    pass "the large card's \"more tasks like it\" counts only the tasks whose wait is of the same kind"
  else
    fail "the count of the tasks like it: $why"
  fi
  if why=$("$PY" -I -B -c "$LOOK" timer "$WORK/board.dom" "$WORK/task-$G.dom" "$WORK/task-talk-runs.dom" "$WORK/task-held-choice.dom"); then
    pass "a timer of a wait says its unit, as 10m or 4m 05s, never a bare 31:00"
  else
    fail "the timer's unit: $why"
  fi
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$L.dom" meta "Landed|~^Landed [0-9][0-9a-z ]* ago$") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$G.dom" meta "Building|!ago"); then
    pass "the status of a task that ended says how long ago it ended, and the status of an open task how long it has been in it"
  else
    fail "the status's time: $why"
  fi
  if why=$("$PY" -I -B -c "$LOOK" shares "$WORK/task-$K.dom" sum) && why=$("$PY" -I -B -c "$LOOK" shares "$WORK/task-red-gate.dom" none); then
    pass "where the rows overlap, the legend of the time card says in its own line what the shares add up to, and where they do not it says nothing of it"
  else
    fail "the shares' sum: $why"
  fi
  # The board of one task says its newest state once, in the large card: the activity has every state
  # block with its time, and no History card repeats it.
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$L.dom" "=1:is merged" "!History") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$L.dom" feed "Ready for its checks|the report is written" "Waits for the merge|pull request https://github.com/acme/shop/pull/7|green"); then
    pass "the board of one task says the merged line once, in its large card, and its activity holds every earlier state block, with no History card to repeat them"
  else
    fail "the merged line and the History card: $why"
  fi
  if why=$("$PY" -I -B -c "$LOOK" terms "$WORK/board.dom" "$WORK/task-talk-runs.dom" "$WORK/task-trust-prompt.dom" "$WORK/task-queued-after.dom" "$WORK/task-$M.dom"); then
    pass "where the page says the companion, the plan talk or a trust prompt, a hover says in one line what it is"
  else
    fail "the hovers of Lem's own words: $why"
  fi
  # At 1300 px the phases' labels keep a gap: "task 2 of 2" under Build and "2 green" under Checks
  # stood 3 px apart and read as "task 2 of 22 green" (the final audit, 2026-11-17).
  cat > "$STATE/probe.html" <<PROBE
<!doctype html><meta charset="utf-8"><iframe id="f" src="task-$L.html" style="width:1300px;height:900px;border:0"></iframe><pre id="out"></pre>
<script>
setTimeout(() => {
  const d = document.getElementById('f').contentDocument, gaps = [];
  // where the words of a phase stand: the boxes of its text, not of its elements, which fill the column
  const box = node => {
    const walk = d.createTreeWalker(node, NodeFilter.SHOW_TEXT), all = [];
    for (let t = walk.nextNode(); t; t = walk.nextNode()) if (t.data.trim()) { const r = d.createRange(); r.selectNodeContents(t); all.push(...r.getClientRects()); }
    return [Math.min(...all.map(x => x.left)), Math.max(...all.map(x => x.right))];
  };
  const phases = [...d.querySelectorAll('.phase')].map(box);
  for (let i = 1; i < phases.length; i++) gaps.push(Math.round(phases[i][0] - phases[i - 1][1]));
  document.getElementById('out').textContent = JSON.stringify({gaps, labels: [...d.querySelectorAll('.phase small')].map(n => n.textContent)});
}, 2500);
</script>
PROBE
  headless --allow-file-access-from-files --virtual-time-budget=6000 --dump-dom "file://$STATE/probe.html" > "$WORK/phases.dom"
  rm -f "$STATE/probe.html"
  if why=$("$PY" -I -c 'import html, json, re, sys
found = re.search(r"<pre id=\"out\">(.*?)</pre>", open(sys.argv[1], encoding="utf-8").read(), re.S)
d = json.loads(html.unescape(found.group(1))) if found and found.group(1) else {"gaps": [], "labels": []}
ok = len(d["gaps"]) >= 6 and min(d["gaps"]) >= 8 and "task 2 of 2" in d["labels"] and "2 green" in d["labels"]
print("" if ok else f"the gaps between the phases are {d}")
sys.exit(not ok)' "$WORK/phases.dom"); then
    pass "at 1300 px each phase's label keeps 8 px or more from the next, so \"task 2 of 2\" and \"2 green\" read as two"
  else
    fail "the phases at 1300 px: $why"
  fi
  # Where the owner answers: Lem's own page in its session, on the large card of the board and on the task's own board.
  draw task-held-choice && draw task-criteria-wait
  # shellcheck disable=SC1112  # the curly quote is the page's
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-held-choice.dom" now \
      "Where you answer: Lem puts choice 1 to you as a page in its session. Answer it there: it waits for your word, also while you are away.") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-criteria-wait.dom" now \
      "Where you answer: Lem shows you the acceptance criteria, with the personas’ read on top, as a page in its session. Approve or change them there."); then
    pass "where the owner answers is Lem's own page in its session, on the board of a task with a choice and of one whose criteria wait"
  else
    fail "where the owner answers: $why"
  fi

  # Lem's look (lem.css and lem.js), drawn from the skill's own files in a folder of its own, so that no
  # lane of the fixture changes: the head of a task's board with a short and a 160-character title at 900
  # and 1400 px, Lem's palette under five agterm themes and under the system's light and dark, and the
  # onboarding page beside the board. agterm's theme stylesheet goes in as agterm writes it
  # (HtmlOverlayTheme.stylesheet), with the scheme its own rule gives the background (Rec. 601 luminance
  # under 0.5 is dark, ThemeBrightness.isDark); a stand-in for agterm's bridge names Lem's session.
  STEADY=$WORK/steady
  mkdir -p "$STEADY"
  STEADY_FIXTURE=$(cat <<'PY'
import json, sys
from datetime import datetime, timedelta, timezone
assets, out = sys.argv[1:]
short = "the-dates-stay-whole"
long_words = "the export keeps every date of an order whole when the merchant opens the file in a spreadsheet that reads the dates in a locale other than the one a store uses"
assert len(long_words) == 160, len(long_words)
long_slug = long_words.replace(" ", "-")
now = datetime.now(timezone.utc)
iso = lambda minutes: (now - timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
state = lambda minutes, task, status, text, ask: {"ts": iso(minutes), "event": "task.state", "task": task, "status": status, "text": text, "lines": [], "ask": ask}
events = [
    state(30, short, "building", "task 1 of 2", "Keep the dates whole in the export"),
    state(25, long_slug, "held", "the criteria wait for the owner", "Dates in the export read the same in every locale"),
    state(20, "in-checks", "landing", "the checks start", "Round the totals once"),
    state(90, "landed-one", "landing", "the checks start", "Name the column"),
    state(60, "landed-one", "landed", "main: pull request #7 is merged", "Name the column"),
]
open(f"{out}/events.js", "w", encoding="utf-8").write("".join(f"lemEvent({json.dumps(e)});\n" for e in events))
open(f"{out}/meta.js", "w", encoding="utf-8").write("lemMeta(" + json.dumps({"repo": "shop", "base": "main", "session": "LEM1", "gates": 1, "serial": 0}) + ");\n")
for name in ("lem.css", "lem.js"):
    open(f"{out}/{name}", "w", encoding="utf-8").write(open(f"{assets}/{name}", encoding="utf-8").read())
board = open(f"{assets}/board.html", encoding="utf-8").read()
handover = open(f"{assets}/handover.html", encoding="utf-8").read()
bridge = "<script>globalThis.agterm = {request: async cmd => cmd === 'tree' ? {tree: {workspaces: [{sessions: [{id: 'LEM1', status: 'idle'}]}]}} : {}};</script>"
def dark(hex_):
    r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.299 * r + 0.587 * g + 0.114 * b < 0.5
def theme(background, foreground):
    look = f"color-scheme: {'dark' if dark(background) else 'light'}; color: {foreground}; "
    return f"<style id=\"agterm-theme\">:where(html) {{ {look}--agterm-background: {background}; --agterm-foreground: {foreground}; }}</style>"
def page(name, text, head=""):
    assert text.count("<head>") == 1
    open(f"{out}/{name}.html", "w", encoding="utf-8").write(text.replace("<head>", "<head>" + head, 1))
# the backgrounds of the criterion, and an installed light theme just under the middle of relative luminance
themes = {"15181c": "#dde1e6", "ffffff": "#1e1e1e", "fdf6e3": "#657b83", "002b36": "#839496", "d8b590": "#2b2118"}
frames = []
for slug, size in ((short, "short"), (long_slug, "long")):
    page(f"task-{slug}", board, bridge)
    frames += [{"id": f"head-{size}-{width}", "src": f"task-{slug}.html", "width": width, "kind": "head"} for width in (900, 1400)]
for bg, fg in themes.items():
    page(f"board-{bg}", board, theme(f"#{bg}", fg) + bridge)
    page(f"handover-{bg}", handover, theme(f"#{bg}", fg))
    frames += [{"id": f"board-{bg}", "src": f"board-{bg}.html", "width": 1400, "kind": "look", "agterm": [f"#{bg}", fg]},
               {"id": f"handover-{bg}", "src": f"handover-{bg}.html", "width": 1400, "kind": "look", "agterm": [f"#{bg}", fg]}]
    if bg in ("15181c", "ffffff"):
        page(f"task-look-{bg}", board.replace("<head>", "<head>" + theme(f"#{bg}", fg), 1), bridge)
page("board-system", board, bridge)
page("handover-system", handover)
system = [{"id": "board-system", "src": "board-system.html", "width": 1400, "kind": "look", "agterm": []},
          {"id": "handover-system", "src": "handover-system.html", "width": 1400, "kind": "look", "agterm": []}]
PROBE = """<!doctype html><meta charset="utf-8"><body><pre id="out"></pre>
<script>
const FRAMES = %s;
for (const f of FRAMES) {
  const node = document.createElement('iframe');
  node.id = f.id; node.src = f.src; node.style.cssText = `width:${f.width}px;height:900px;border:0;display:block`;
  document.body.append(node);
}
const ctx = Object.assign(document.createElement('canvas'), {width: 1, height: 1}).getContext('2d', {willReadFrequently: true});
const rgba = css => { ctx.clearRect(0, 0, 1, 1); ctx.fillStyle = 'rgba(0, 0, 0, 0)'; ctx.fillStyle = css; ctx.fillRect(0, 0, 1, 1); const d = ctx.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
const over = (top, under) => [0, 1, 2].map(i => top[i] * top[3] + under[i] * (1 - top[3])).concat(1);
const lum = c => { const l = c.slice(0, 3).map(v => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * l[0] + 0.7152 * l[1] + 0.0722 * l[2]; };
const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
const box = n => { const r = n.getBoundingClientRect(); return {left: r.left, right: r.right, top: r.top, height: r.height}; };
function head(f, d, w) {
  const top = d.querySelector('header.top'), h1 = d.getElementById('title');
  const buttons = () => [...d.querySelectorAll('#top-right button')].map(b => ({text: b.textContent.trim(), ...box(b)}));
  const hover = [...d.styleSheets].flatMap(s => { try { return [...s.cssRules]; } catch { return []; } })
    .some(r => /h1[^,]*:hover/.test(r.selectorText ?? '') && /:focus/.test(r.selectorText ?? '') && r.style.getPropertyValue('-webkit-line-clamp') === 'unset');
  const out = {header: box(top), buttons: buttons(), title: h1.textContent, lineHeight: parseFloat(w.getComputedStyle(h1).lineHeight),
    tabIndex: h1.tabIndex, hover, before: {...box(h1), clipped: h1.scrollHeight > h1.clientHeight + 1}};
  w.focus(); h1.focus({focusVisible: true});
  out.after = {...box(h1), whole: h1.scrollHeight <= h1.clientHeight + 1, focused: h1.matches(':focus-visible')};
  out.buttonsFocused = buttons();
  h1.blur();
  return out;
}
function look(f, d, w) {
  const cs = n => w.getComputedStyle(n), root = d.documentElement;
  const background = n => { const layers = []; for (let m = n; m; m = m.parentElement) { const c = rgba(cs(m).backgroundColor); if (c[3] > 0) layers.push(c); if (c[3] === 1) break; }
    return layers.reverse().reduce((under, c) => over(c, under), [255, 255, 255, 1]); };
  const low = [], colors = new Set();
  let least = 99;
  for (const n of d.body.querySelectorAll('*')) {
    if (n.closest('svg, script, style, [hidden]')) continue;
    const s = cs(n);
    for (const c of [s.color, s.backgroundColor, s.borderTopColor]) { const v = rgba(c); if (v[3] > 0) colors.add(v.slice(0, 3).join(',')); }
    if (![...n.childNodes].some(c => c.nodeType === 3 && c.data.trim()) || !n.getClientRects().length || s.visibility !== 'visible') continue;
    const bg = background(n), r = ratio(over(rgba(s.color), bg), bg);
    least = Math.min(least, r);
    if (r < 4.5) low.push(`${n.tagName.toLowerCase()}.${[...n.classList].join('.')} "${n.textContent.trim().slice(0, 40)}" ${r.toFixed(2)}`);
  }
  const pick = (sel, ...props) => { const n = d.querySelector(sel); return n ? Object.fromEntries(props.map(p => [p, cs(n).getPropertyValue(p)])) : null; };
  return {palette: root.dataset.palette ?? null, scheme: cs(root).colorScheme, tokenBg: cs(root).getPropertyValue('--bg').trim(),
    logo: [...d.querySelectorAll('.mark > svg')].filter(s => cs(s).display !== 'none').map(s => s.getAttribute('aria-labelledby')),
    body: pick('body', 'background-color', 'color', 'font-family'), h1: pick('h1', 'font-size', 'font-weight', 'font-family', 'line-height', 'color'),
    eyebrow: pick('.eyebrow', 'font-size', 'font-weight', 'letter-spacing', 'color'), mark: pick('.mark', 'width', 'height', 'border-radius', 'box-shadow'),
    chip: pick('.chip:not(.ok):not(.bad):not(.you)', 'font-size', 'border-radius', 'color', 'background-color', 'border-top-color'),
    least: Math.round(least * 100) / 100, low, colors: [...colors]};
}
setTimeout(() => {
  const out = {};
  for (const f of FRAMES) {
    const w = document.getElementById(f.id).contentWindow, d = w.document;
    try { out[f.id] = {...f, ...(f.kind === 'head' ? head(f, d, w) : look(f, d, w))}; } catch (err) { out[f.id] = {error: String(err)}; }
  }
  document.getElementById('out').textContent = JSON.stringify(out);
}, 4000);
</script>"""
looked = frames + [{"id": f"task-look-{bg}", "src": f"task-look-{bg}.html", "width": 1400, "kind": "look", "agterm": [f"#{bg}", themes[bg]]} for bg in ("15181c", "ffffff")]
open(f"{out}/probe.html", "w", encoding="utf-8").write(PROBE % json.dumps(looked + system))
open(f"{out}/probe-dark.html", "w", encoding="utf-8").write(PROBE % json.dumps(system))
PY
)
  "$PY" -I -c "$STEADY_FIXTURE" "$PWD/skills/lem/assets" "$STEADY"
  # the system's setting: light for the first draw, dark for the second, whatever this machine says
  headless --allow-file-access-from-files --blink-settings=preferredColorScheme=1 --virtual-time-budget=9000 --dump-dom "file://$STEADY/probe.html" > "$WORK/steady.dom"
  headless --allow-file-access-from-files --blink-settings=preferredColorScheme=0 --virtual-time-budget=9000 --dump-dom "file://$STEADY/probe-dark.html" > "$WORK/steady-dark.dom"
  STEADY_CHECK=$(cat <<'PY'
import html, json, re, sys
check, light, dark = sys.argv[1:]
def read(path):
    found = re.search(r"<pre id=\"out\">(.*?)</pre>", open(path, encoding="utf-8").read(), re.S)
    return json.loads(html.unescape(found.group(1))) if found and found.group(1) else {}
got, got_dark = read(light), read(dark)
wrong = []
if not got or not got_dark:
    print(f"the probe printed nothing ({len(got)} and {len(got_dark)} frames)"); sys.exit(1)
for name, frame in [*got.items(), *(("dark " + k, v) for k, v in got_dark.items())]:
    if "error" in frame: wrong.append(f"{name}: {frame['error']}")
rgb = lambda hex_: ",".join(str(int(hex_[i:i + 2], 16)) for i in (1, 3, 5))
if check == "head":
    for width in (900, 1400):
        short, long_ = got.get(f"head-short-{width}", {}), got.get(f"head-long-{width}", {})
        for size, f in (("short", short), ("long", long_)):
            names = [b["text"] for b in f.get("buttons", [])]
            if names != ["All tasks", "Go to Lem’s session (idle)"]: wrong.append(f"{size} at {width}: the buttons are {names}"); continue
            right = f["header"]["right"]
            if any(abs(b["right"] - right) > 1 for b in f["buttons"]): wrong.append(f"{size} at {width}: a button is not at the right edge {right}: {f['buttons']}")
            if abs(f["buttons"][0]["top"] - f["header"]["top"]) > 1: wrong.append(f"{size} at {width}: the first button is not at the top {f['header']['top']}: {f['buttons'][0]}")
            if f["buttonsFocused"] != f["buttons"]: wrong.append(f"{size} at {width}: the focus on the title moved a button: {f['buttonsFocused']}")
        if short.get("buttons") and long_.get("buttons") and any(abs(a[k] - b[k]) > 0.5 for a, b in zip(short["buttons"], long_["buttons"]) for k in ("left", "right", "top")):
            wrong.append(f"at {width} the buttons stand elsewhere for the long title: {short['buttons']} / {long_['buttons']}")
        if long_:
            if len(long_["title"]) != 160: wrong.append(f"the long title has {len(long_['title'])} characters")
            # at 900 px the title needs more than two lines, so it is cut there; at 1400 px two may hold it
            if long_["before"]["height"] > 2 * long_["lineHeight"] + 1 or (width == 900 and not long_["before"]["clipped"]):
                wrong.append(f"at {width} the long title takes more than two lines, or is not cut where it needs more: {long_['before']}, line {long_['lineHeight']}")
            if not (long_["after"]["focused"] and long_["after"]["whole"]) or (long_["before"]["clipped"] and long_["after"]["height"] <= long_["before"]["height"]):
                wrong.append(f"at {width} the long title with the focus does not show whole: {long_['after']}")
            if long_["tabIndex"] != 0 or not long_["hover"]: wrong.append(f"the title takes no focus ({long_['tabIndex']}) or no hover shows it whole ({long_['hover']})")
        if short and short["before"]["clipped"]: wrong.append(f"at {width} the short title is cut: {short['before']}")
elif check == "palette":
    want = {"15181c": "dark", "ffffff": "light", "fdf6e3": "light", "002b36": "dark", "d8b590": "light"}
    night = lambda f: f.get("logo") == ["c2mn-title c2mn-desc"]
    day = lambda f: f.get("logo") == ["c2m-title c2m-desc"]
    tokens = {}
    for bg, palette in want.items():
        f = got.get(f"board-{bg}", {})
        if f.get("palette") != palette or f.get("scheme") != palette: wrong.append(f"#{bg}: the palette is {f.get('palette')} ({f.get('scheme')}), not {palette}")
        if not (night(f) if palette == "dark" else day(f)): wrong.append(f"#{bg}: the header shows {f.get('logo')}")
        tokens.setdefault(palette, set()).add(f.get("tokenBg"))
        # Lem's light card is white too, so the colors are compared under the other themes
        agterm = {rgb(c) for c in f.get("agterm", [])} if bg != "ffffff" else set()
        if agterm & set(f.get("colors", [])): wrong.append(f"#{bg}: the board draws a color of agterm's theme: {sorted(agterm & set(f.get('colors', [])))}")
        if f.get("body", {}).get("background-color") in (f"rgb({rgb('#' + bg).replace(',', ', ')})",): wrong.append(f"#{bg}: the page's background is agterm's")
    if any(len(v) != 1 for v in tokens.values()) or tokens.get("dark") == tokens.get("light"): wrong.append(f"the palettes' backgrounds are {tokens}")
    system_light, system_dark = got.get("board-system", {}), got_dark.get("board-system", {})
    if system_light.get("palette") != "light" or not day(system_light): wrong.append(f"outside agterm, under the system's light: {system_light.get('palette')}, {system_light.get('logo')}")
    if system_dark.get("palette") != "dark" or not night(system_dark): wrong.append(f"outside agterm, under the system's dark: {system_dark.get('palette')}, {system_dark.get('logo')}")
    for name, f in [*got.items(), ("dark board-system", system_dark)]:
        if name.startswith("head-") or "handover" in name: continue
        if f.get("least", 0) < 4.5 or f.get("low"): wrong.append(f"{name}: text under 4.5:1 (least {f.get('least')}): {f.get('low', [])[:6]}")
elif check == "pages":
    same = ("body", "h1", "eyebrow", "mark", "chip", "logo", "palette")
    for name, b, o in (("light", got.get("board-ffffff"), got.get("handover-ffffff")), ("dark", got.get("board-15181c"), got.get("handover-15181c")),
                       ("the system's light", got.get("board-system"), got.get("handover-system")), ("the system's dark", got_dark.get("board-system"), got_dark.get("handover-system"))):
        if not b or not o: wrong.append(f"{name}: a page was not drawn"); continue
        for key in same:
            if b.get(key) is None or b.get(key) != o.get(key): wrong.append(f"{name}: the {key} of the board is {b.get(key)}, of the onboarding page {o.get(key)}")
print("; ".join(wrong))
sys.exit(bool(wrong))
PY
)
  if why=$("$PY" -I -c "$STEADY_CHECK" head "$WORK/steady.dom" "$WORK/steady-dark.dom"); then
    pass "on a task's board \"All tasks\" and \"Go to Lem’s session\" stand at the top right for a short and a 160-character title at 900 and 1400 px; the long title takes two lines and shows whole on the focus and on a hover, with no button moved"
  else
    fail "the head of a task's board: $why"
  fi
  if why=$("$PY" -I -c "$STEADY_CHECK" palette "$WORK/steady.dom" "$WORK/steady-dark.dom"); then
    pass "the board takes Lem's own palette from agterm's scheme: dark with the night logo on #15181c and #002b36, light with the day logo on #ffffff, #fdf6e3 and #d8b590, no color of agterm's, the system's setting outside agterm, and text of 4.5:1 or more in both"
  else
    fail "Lem's light and dark: $why"
  fi
  if why=$("$PY" -I -c "$STEADY_CHECK" pages "$WORK/steady.dom" "$WORK/steady-dark.dom"); then
    pass "the onboarding page has the board's header, fonts and colors, in light and in dark, from agterm and from the system"
  else
    fail "one look for every page of Lem: $why"
  fi

  # The board of all tasks with two choices that wait, on a task whose ask is 300 characters long and
  # that builds while they wait, one task whose criteria wait and one green pull request, in a folder
  # of its own beside the skill's files, so that no lane of the fixture changes. A stand-in for agterm's
  # bridge names Lem's session: what runs in it (`fg`) and whether a read of the sessions fails
  # (`treeFails`) are the probe's to change.
  STAY=$WORK/stay
  mkdir -p "$STAY"
  STAY_FIXTURE=$(cat <<'PY'
import json, sys
from datetime import datetime, timedelta, timezone
assets, out = sys.argv[1:]
now = datetime.now(timezone.utc)
iso = lambda minutes: (now - timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
words = ("The export keeps every date of an order whole when the merchant opens the file in a spreadsheet that reads the dates in a locale "
         "other than the one the store uses, and the totals of each month add up to the same sum in the report, the invoice and the export, "
         "so that an accountant who checks the three finds no difference at all")
long_ask = words[:299].rstrip() + "."
long_ask = long_ask + "." * (300 - len(long_ask))
assert len(long_ask) == 300, len(long_ask)
long_choice = ("The order of the day and the month in the date column, which a spreadsheet in another locale reads as a month and a day "
               "when the day is twelve or less, so that the third of May reads as the fifth of March")
state = lambda minutes, task, status, text, ask, lines=(): {"ts": iso(minutes), "event": "task.state", "task": task, "status": status, "text": text, "lines": list(lines), "ask": ask}
asked = lambda minutes, task, number, what, options: {"ts": iso(minutes), "event": "decision.asked", "task": task, "id": number, "at": iso(minutes), "what": what,
                                                      "options": options, "recommended": options[0], "why": "the personas split"}
events = [
    state(60, "sort-the-export", "landing", "the checks start", "Sort the export by date"),
    {"ts": iso(50), "event": "proposed", "task": "sort-the-export", "green": True, "not_green": [], "tip": "abc123456"},
    state(50, "sort-the-export", "open", "pull request https://github.com/acme/shop/pull/3", "Sort the export by date", ["green"]),
    state(40, "dates-stay-whole", "building", "task 1 of 2", long_ask),
    asked(30, "dates-stay-whole", 1, long_choice, ["the day first", "the month first"]),
    asked(20, "dates-stay-whole", 2, "The name of the date column", ["ordered", "date"]),
    state(25, "round-the-totals", "held", "the criteria wait for the owner", "Round the totals once"),
    state(10, "trim-the-notes", "landing", "the checks start", "Trim the order notes"),
]
open(f"{out}/events.js", "w", encoding="utf-8").write("".join(f"lemEvent({json.dumps(e)});\n" for e in events))
open(f"{out}/meta.js", "w", encoding="utf-8").write("lemMeta(" + json.dumps({"repo": "shop", "base": "main", "session": "LEM1", "gates": 1, "serial": 0}) + ");\n")
item = {"slug": "which-currency", "path": "docs/backlog/which-currency.md", "title": "Which currency rounds half up", "worth": "yes", "where": "", "where_problem": "",
        "added": "2026-11-02", "state": "", "body": "The refund of order 1042 rounds 0.125 to 0.13. The cart rounds half to even. One of the two is wrong."}
open(f"{out}/backlog.js", "w", encoding="utf-8").write("lemBacklog(" + json.dumps({"folder": "docs/backlog", "read": iso(1), "items": [item]}) + ");\n")
for name in ("lem.css", "lem.js"):
    open(f"{out}/{name}", "w", encoding="utf-8").write(open(f"{assets}/{name}", encoding="utf-8").read())
bridge = ("<script>globalThis.fg = ['/bin/zsh']; globalThis.treeFails = false; globalThis.agterm = {request: async cmd => {"
          " if (cmd !== 'tree') return {}; if (globalThis.treeFails) throw new Error('the socket is gone');"
          " return {tree: {workspaces: [{sessions: [{id: 'LEM1', status: 'idle', foreground: globalThis.fg}]}]}}; }};</script>")
board = open(f"{assets}/board.html", encoding="utf-8").read()
assert board.count("<head>") == 1
open(f"{out}/board.html", "w", encoding="utf-8").write(board.replace("<head>", "<head>" + bridge, 1))
open(f"{out}/probe.html", "w", encoding="utf-8").write("""<!doctype html><meta charset="utf-8"><iframe id="f" src="board.html#waits" style="width:1400px;height:900px;border:0"></iframe><pre id="out"></pre>
<script>
const wait = ms => new Promise(done => setTimeout(done, ms));
(async () => {
  await wait(1500);
  const w = document.getElementById('f').contentWindow, d = w.document, log = {};
  const box = n => n.getBoundingClientRect();
  const chosen = () => d.querySelector('#tabs [aria-selected="true"]')?.dataset.tab ?? null;
  const shown = () => ['waits', 'backlog', 'lanes-section'].filter(id => d.getElementById(id) && !d.getElementById(id).hidden);
  // where a button stands in its card: how far from the card's right edge, and from its left edge
  const side = (card, button) => { const c = box(card), b = box(button); return {right: Math.round(c.right - b.right), left: Math.round(b.left - c.left), width: Math.round(c.width)}; };
  log.first = [chosen(), shown()];
  await wait(2500);
  log.later = [chosen(), shown()];
  log.rows = [...d.querySelectorAll('#waits-rows .wrow')].map(row => ({verb: row.querySelector('.wverb').textContent, button: side(row, row.querySelector('.wside button'))}));
  // the tasks: the cards of the lane "Waits for you"
  d.querySelector('[data-tab="tasks"]').click(); await wait(300);
  const lane = [...d.querySelectorAll('#lanes .lane')].find(l => l.querySelector('.lane-head').textContent.startsWith('Waits for you'));
  const cards = [...lane.querySelectorAll('.tcard')];
  const cut = n => n.scrollHeight > n.clientHeight + 1;
  const measure = () => cards.map(c => {
    const part = sel => c.querySelector(sel), ask = part('.tc-ask > span');
    return {title: part('.tc-title').textContent, height: Math.round(box(c).height * 10) / 10, titleCut: cut(part('.tc-title')),
      state: part('.tc-text').textContent, stateCut: cut(part('.tc-text')) || !part('.tc-text').getClientRects().length,
      mark: part('.tc-wait')?.textContent ?? null, markTitle: part('.tc-wait')?.title ?? null,
      ask: ask ? {height: Math.round(box(ask).height * 10) / 10, cut: cut(ask), line: parseFloat(w.getComputedStyle(ask).lineHeight)} : null};
  });
  log.cards = measure();
  log.focusable = cards.map(c => { c.focus(); const took = d.activeElement === c && c.tabIndex >= 0; c.blur(); return took; });
  const long = cards.find(c => c.querySelector('.tc-title').textContent === 'Dates stay whole');
  w.focus(); long.focus({focusVisible: true});
  log.focused = {visible: long.matches(':focus-visible'), cards: measure()};
  long.blur();
  log.hover = [...d.styleSheets].flatMap(sheet => { try { return [...sheet.cssRules]; } catch { return []; } })
    .some(rule => /\\.tcard:is\\(:hover, :focus-visible\\) \\.tc-ask/.test(rule.selectorText ?? '') && rule.style.getPropertyValue('-webkit-line-clamp') === 'unset');
  const now = d.getElementById('now');
  log.band = side(now, now.querySelector('button[data-open]'));
  // the backlog: a sentence of an item's body, then the command of its foot, selected while what runs
  // in Lem's session changes and while a read of the sessions fails
  d.querySelector('[data-tab="backlog"]').click(); await wait(800);
  d.querySelector('[data-bl-toggle="which-currency"]').click(); await wait(300);
  const sel = w.getSelection();
  const pick = range => { sel.removeAllRanges(); sel.addRange(range); return sel.toString(); };
  const still = want => [sel.toString() === want && sel.rangeCount > 0 && sel.getRangeAt(0).startContainer.isConnected, chosen()];
  const foot = () => d.querySelector('.bl-actions').textContent;
  const sentence = d.createRange(), text = d.querySelector('.bl-text').firstChild;
  sentence.setStart(text, 0); sentence.setEnd(text, 'The refund of order 1042 rounds 0.125 to 0.13.'.length);
  const said = pick(sentence);
  log.body = [said];
  w.fg = ['/opt/homebrew/bin/claude']; await wait(3500); log.body.push(still(said), foot());
  w.treeFails = true; await wait(3500); log.body.push(still(said), foot());
  w.treeFails = false; w.fg = ['/bin/zsh']; await wait(3500);
  const command = d.createRange(); command.selectNodeContents(d.querySelector('.bl-actions code'));
  const cmd = pick(command);
  log.code = [cmd];
  w.fg = ['/opt/homebrew/bin/claude']; await wait(3500); log.code.push(still(cmd), foot());
  const item = d.querySelector('.bl-item');
  log.ask = side(item, d.querySelector('[data-bl-ask]'));
  w.treeFails = true; await wait(3500); log.code.push(still(cmd), foot());
  w.treeFails = false; await wait(3500);
  d.querySelector('[data-bl-ask]').click(); await wait(100);
  const start = d.querySelector('[data-bl-start]'), cancel = d.querySelector('[data-bl-cancel]');
  log.confirm = {start: side(item, start), cancel: side(item, cancel), between: Math.round(box(cancel).left - box(start).right)};
  document.getElementById('out').textContent = JSON.stringify(log);
})().catch(err => { document.getElementById('out').textContent = JSON.stringify({error: String(err)}); });
</script>""")
PY
)
  "$PY" -I -c "$STAY_FIXTURE" "$PWD/skills/lem/assets" "$STAY"
  "$PY" -I -c "$STOP" "$STAY/board.html" "$NOW"
  headless --virtual-time-budget=5000 --dump-dom "file://$STAY/board.html#waits" > "$WORK/stay-waits.dom"
  # watch.js as land.py watch writes it, with the pull request's entry: the forge's word on HEAD
  stay_watch() { "$PY" -I -c 'import json, sys
entry = {"task": "sort-the-export", "pr": 3, "url": "https://github.com/acme/shop/pull/3", "state": "OPEN", "mergeable": "CONFLICTING", "head": sys.argv[2], "since": None}
open(sys.argv[1], "w").write("lemWatch(" + json.dumps({"checked": "2026-11-19T09:00:00Z", "every": 60, "looks": 1, "open": [entry], "ended": None}) + ");\n")' "$STAY/watch.js" "$1"; }
  stay_watch abc123456def7890abc123456def7890abc12345 && headless --virtual-time-budget=5000 --dump-dom "file://$STAY/board.html#waits" > "$WORK/stay-conflict.dom"
  stay_watch 0ff1ce0ff1ce0ff1ce0ff1ce0ff1ce0ff1ce0ff1 && headless --virtual-time-budget=5000 --dump-dom "file://$STAY/board.html#waits" > "$WORK/stay-older.dom"
  rm -f "$STAY/watch.js"
  # The test of criterion 4: the count 4 and the four rows, each with its verb, on the tab the address
  # opens; only the text of that tab is read, none of the panels the other tabs hide.
  # shellcheck disable=SC1112  # the curly quotes are the page's
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/stay-waits.dom" @visible "Waits for you 4" "Answer choice 1" "Answer choice 2" "Approve the criteria" "Merge the pull request" \
      "!Building: task 1 of 2" "!The criteria wait for you" "!Which currency rounds half up") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/stay-waits.dom" waits-rows "The order of the day and the month|Answer choice 1|Dates stay whole|recommended: the day first" \
      "The name of the date column|Answer choice 2|Dates stay whole" "Round the totals once|Approve the criteria|Lem shows you the acceptance criteria" \
      "Sort the export by date|Merge the pull request|Green|Merge the pull request, or tell Lem in its session to land it.") \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/stay-conflict.dom" @visible "Waits for you 4" "It conflicts with the base" "Lem brings it onto the base first" "!Merge" "!merge") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/stay-older.dom" waits-rows "Sort the export by date|Merge the pull request|!conflicts"); then
    pass "Waits for you counts 4 for two choices, criteria that wait and a green pull request, each row with its verb: answer the choice, approve the criteria, merge the pull request; a pull request the forge calls conflicting on the proposed head has no merge verb, and on an older head it keeps it"
  else
    fail "Waits for you: $why"
  fi
  headless --allow-file-access-from-files --virtual-time-budget=40000 --dump-dom "file://$STAY/probe.html" > "$WORK/stay-probe.dom"
  STAY_CHECK=$(cat <<'PY'
import html, json, re, sys
check, path = sys.argv[1:]
found = re.search(r"<pre id=\"out\">(.*?)</pre>", open(path, encoding="utf-8").read(), re.S)
d = json.loads(html.unescape(found.group(1))) if found and found.group(1) else {"error": "the probe printed nothing"}
wrong = [d["error"]] if "error" in d else []
# at the right: the button's right edge 24 px or less from its card's, and the button in the card's right half
right = lambda s: s["right"] <= 24 and s["left"] > s["width"] / 2
if not wrong and check == "cards":
    cards = {c["title"]: c for c in d["cards"]}
    long, short = cards.get("Dates stay whole"), cards.get("Round the totals")
    if not long or not short: wrong.append(f"the lane holds {list(cards)}")
    else:
        if len({c["height"] for c in d["cards"]}) != 1: wrong.append(f"the cards' heights are {[(c['title'], c['height']) for c in d['cards']]}")
        if long["state"] != "Building: task 1 of 2" or short["state"] != "The criteria wait for you": wrong.append(f"the state lines are {long['state']!r} and {short['state']!r}")
        if any(c["stateCut"] or c["titleCut"] for c in d["cards"]): wrong.append(f"a title or a state line is cut: {d['cards']}")
        if long["mark"] != "2 choices wait" or "The order of the day and the month" not in (long["markTitle"] or "") or "The name of the date column" not in (long["markTitle"] or ""):
            wrong.append(f"the wait mark is {long['mark']!r} with the hover {long['markTitle']!r}")
        if short["mark"] is not None: wrong.append(f"a card with no choice has the mark {short['mark']!r}")
        ask = long["ask"] or {}
        if not ask.get("cut") or ask.get("height", 0) > 2 * ask.get("line", 0) + 1: wrong.append(f"the long ask is not cut after two lines: {ask}")
        if (short["ask"] or {}).get("cut"): wrong.append(f"the short ask is cut: {short['ask']}")
        if not all(d["focusable"]) or len(d["focusable"]) != len(d["cards"]): wrong.append(f"a card does not take the focus: {d['focusable']}")
        after = {c["title"]: c for c in d["focused"]["cards"]}
        whole = after["Dates stay whole"]["ask"] or {}
        if not d["focused"]["visible"] or whole.get("cut", True) or whole.get("height", 0) <= ask.get("height", 0): wrong.append(f"the long ask with the focus does not show whole: {whole}")
        if [c["height"] for c in d["focused"]["cards"]] != [c["height"] for c in d["cards"]]: wrong.append(f"the focus changed a card's height: {d['focused']['cards']}")
        if not d["hover"]: wrong.append("no hover shows the whole ask")
elif not wrong and check == "stays":
    if d["first"] != ["waits", ["waits"]] or d["later"] != ["waits", ["waits"]]: wrong.append(f"the tab Waits for you: {d['first']} then, two draws later, {d['later']}")
    body, code = d["body"], d["code"]
    if not body[0].startswith("The refund of order 1042") or body[1] != [True, "backlog"] or body[3] != [True, "backlog"]: wrong.append(f"the selected sentence: {body}")
    if not code[0].startswith("/lem new ") or code[1] != [True, "backlog"] or code[3] != [True, "backlog"]: wrong.append(f"the selected command: {code}")
    # the words beside them did change: an agent runs, then the read of the sessions failed
    if "Start a task" not in body[2] or "not open in this window" not in body[4] or "Start a task" not in code[2] or "not open in this window" not in code[4]:
        wrong.append(f"the foot did not change with the session: {body[2]!r} / {body[4]!r} / {code[2]!r} / {code[4]!r}")
elif not wrong and check == "actions":
    places = {**{f"row {r['verb']}": r["button"] for r in d["rows"]}, "the large card": d["band"], "Start a task": d["ask"], "Cancel": d["confirm"]["cancel"]}
    if len(d["rows"]) != 4: wrong.append(f"{len(d['rows'])} rows")
    wrong += [f"{name} stands at {s}, not at the right" for name, s in places.items() if not right(s)]
    if not (d["confirm"]["start"]["left"] > d["confirm"]["start"]["width"] / 2 and 0 <= d["confirm"]["between"] <= 16):
        wrong.append(f"Start is not beside Cancel at the right: {d['confirm']}")
print("; ".join(wrong))
sys.exit(bool(wrong))
PY
)
  # The test of criterion 2.
  if why=$("$PY" -I -c "$STAY_CHECK" cards "$WORK/stay-probe.dom"); then
    pass "in one lane a card with a one-line ask and a card with a 300-character ask whose task builds while two choices wait have one height; only the ask is cut, after two lines; each says its state and the long one has the wait mark; Tab reaches each card, and the long ask shows whole on the focus and on a hover with no card changing its height"
  else
    fail "the cards' shape: $why"
  fi
  # The test of criterion 4, its second half.
  if why=$("$PY" -I -c "$STAY_CHECK" stays "$WORK/stay-probe.dom"); then
    pass "the tab the owner chose stays chosen through the draw of every second, and a sentence or a command selected in the backlog stays selected when an agent in Lem's session starts and when a read of the sessions fails"
  else
    fail "the chosen tab and a selection in the backlog: $why"
  fi
  # The test of criterion 1, the cards' actions.
  if why=$("$PY" -I -c "$STAY_CHECK" actions "$WORK/stay-probe.dom"); then
    pass "every card with an action has it at the right: \"Open the task\" on each row of Waits for you and on the large card, the backlog's \"Start a task\", and Start with Cancel beside it"
  else
    fail "the side of the cards' actions: $why"
  fi

  # The board of one task: four tabs, and green or not green on its first view. Three tasks in a folder
  # of their own: the experts took choice 2, option 2, in the very second the owner said he was away,
  # and he came back before the proposal; a night's task whose choice was taken at once while he was
  # there, beside a decision of the dialectic; and a task whose large card has many long lines. A
  # stand-in for agterm's bridge gives each task a session.
  TABS=$WORK/tabs
  mkdir -p "$TABS"
  TABS_FIXTURE=$(cat <<'PY'
import json, sys
from datetime import datetime, timedelta, timezone
assets, out = sys.argv[1:]
now = datetime.now(timezone.utc).replace(microsecond=0)
iso = lambda minutes: (now - timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
state = lambda minutes, task, status, text, ask, lines=(): {"ts": iso(minutes), "event": "task.state", "task": task, "status": status, "text": text, "lines": list(lines), "ask": ask}
def decision(minutes, kind, task, number, **rest):
    return {"ts": iso(minutes), "event": f"decision.{kind}", "task": task, "id": number, "at": iso(minutes), **rest}
owner = lambda minutes, away, words: {"ts": iso(minutes), "event": "owner", "away": away, "by": "owner", "words": words}
experts = {"fable": "the invoice is a page of the shop", "astra": "the printer prints in color"}
# land.py's own lines (not_green): a choice the experts took, a decision past the personas, a choice taken as the recommended option
by_experts = ('choice 2 was taken by the experts (The color of the logo): "the green of the shop", both picked it, at once, as the task ran without the owner. '
              'Fable: the invoice is a page of the shop · Astra: the printer prints in color')
by_dialectic = 'decision 2 was taken without the owner (The font of the label): "sans", by the dialectic'
recommended = 'choice 1 was taken without the owner (The size of the label): "A6", the recommended option, at once, as the task ran without the owner'
long_what = ("The order of the day and the month in the date column of every export, which a spreadsheet in another locale reads as a month "
             "and a day when the day is twelve or less, so that the third of May reads as the fifth of March and the totals of each month move")
long_line = "the export writes the dates in the store's own locale and the spreadsheet of the accountant reads them in its own locale "
events = [
    state(120, "logo-color", "building", "lead: session", "Print the logo in the shop's color", ["session: T1"]),
    state(118, "logo-color", "building", "plan committed, 2 tasks", "Print the logo in the shop's color"),
    decision(110, "asked", "logo-color", 1, what="The paper size", options=["A4", "Letter"], recommended="Letter", why="the printer has Letter in its tray"),
    decision(105, "answered", "logo-color", 1, chose="A4", words="A4"),
    decision(100, "asked", "logo-color", 2, what="The color of the logo", options=["black", "the green of the shop"], recommended="black", why="a black logo prints on every printer"),
    decision(99, "advised", "logo-color", 2, expert="fable", pick="the green of the shop", why=experts["fable"]),
    decision(98, "advised", "logo-color", 2, expert="astra", pick="the green of the shop", why=experts["astra"]),
    owner(90, True, "/lem im-away"),
    decision(90, "timeout", "logo-color", 2, chose="the green of the shop", by="experts", experts=experts, early=True),
    owner(60, False, "/lem im-back"),
    state(50, "logo-color", "landing", "the checks start", "Print the logo in the shop's color"),
    {"ts": iso(40), "event": "proposed", "task": "logo-color", "green": False, "not_green": [by_experts], "tip": "abc123456"},
    state(40, "logo-color", "open", "pull request https://github.com/acme/shop/pull/4", "Print the logo in the shop's color"),
    state(300, "night-labels", "building", "lead: builder", "Label the parcels"),
    decision(290, "asked", "night-labels", 1, what="The size of the label", options=["A6", "A5"], recommended="A6", why="the printer takes A6"),
    decision(290, "timeout", "night-labels", 1, chose="A6", by="timeout", early=True),
    decision(280, "taken", "night-labels", 2, what="The font of the label", chose="sans", by="dialectic", why="it reads at a glance"),
    state(200, "night-labels", "landing", "the checks start", "Label the parcels"),
    {"ts": iso(190), "event": "proposed", "task": "night-labels", "green": False, "not_green": [by_dialectic, recommended], "tip": "def456789"},
    state(190, "night-labels", "open", "pull request https://github.com/acme/shop/pull/5", "Label the parcels"),
    state(30, "long-lines", "building", "lead: session", "Keep every date of an order whole in the export",
          ["session: T3", "task 1 of 3", long_line * 2, long_line * 3, long_line * 2]),
    decision(20, "asked", "long-lines", 1, what=long_what, options=["the day first", "the month first"], recommended="the day first", why="the store is in Europe"),
    decision(19, "advised", "long-lines", 1, expert="fable", pick="the day first", why="every customer of the shop is in Europe"),
    decision(18, "advised", "long-lines", 1, expert="astra", pick="the month first", why="the accountant's spreadsheet is in English"),
]
open(f"{out}/events.js", "w", encoding="utf-8").write("".join(f"lemEvent({json.dumps(e)});\n" for e in events))
open(f"{out}/meta.js", "w", encoding="utf-8").write("lemMeta(" + json.dumps({"repo": "shop", "base": "main", "session": "LEM1", "gates": 1, "serial": 0}) + ");\n")
open(f"{out}/backlog.js", "w", encoding="utf-8").write("lemBacklog(" + json.dumps({"folder": "docs/backlog", "read": iso(1), "items": []}) + ");\n")
for name in ("lem.css", "lem.js"):
    open(f"{out}/{name}", "w", encoding="utf-8").write(open(f"{assets}/{name}", encoding="utf-8").read())
bridge = ("<script>globalThis.agterm = {request: async cmd => cmd !== 'tree' ? {} : {tree: {workspaces: [{sessions: ["
          "{id: 'LEM1', status: 'idle', foreground: ['/bin/zsh']}, {id: 'T1', status: 'idle'}, {id: 'T3', status: 'working'}]}]}}};</script>")
board = open(f"{assets}/board.html", encoding="utf-8").read()
assert board.count("<head>") == 1
for page in ("board", "task-logo-color", "task-night-labels"):
    open(f"{out}/{page}.html", "w", encoding="utf-8").write(board.replace("<head>", "<head>" + bridge, 1))
open(f"{out}/probe.html", "w", encoding="utf-8").write("""<!doctype html><meta charset="utf-8"><iframe id="f" src="board.html#waits" style="width:1400px;height:900px;border:0"></iframe><pre id="out"></pre>
<script>
const wait = ms => new Promise(done => setTimeout(done, ms));
const PHRASE = 'not green: two outside experts chose option 2 while you were away';
(async () => {
  await wait(1500);
  const w = document.getElementById('f').contentWindow, d = w.document, log = {};
  const words = text => text.split(/\\s+/).filter(Boolean).join(' ');
  // the text the owner sees: none under an element with `hidden`, the panel of another tab
  const visible = () => { const out = [], walk = d.createTreeWalker(d.body, NodeFilter.SHOW_TEXT);
    for (let n = walk.nextNode(); n; n = walk.nextNode()) if (n.parentElement && !n.parentElement.closest('[hidden], script, style')) out.push(n.data);
    return words(out.join(' ')); };
  const chosen = () => d.querySelector('#tabs [aria-selected="true"]')?.dataset.tab ?? null;
  const tabs = () => [...d.querySelectorAll('#tabs .tab')].map(b => b.firstChild.textContent);
  const panels = () => [...d.querySelectorAll('#waits, #backlog, [data-tasks], [data-task-tab]')].filter(n => !n.hidden).map(n => n.id);
  // the large card: its height, and where "Go to the session" stands from its right and its bottom edge
  const card = () => { const now = d.getElementById('now'), c = now.getBoundingClientRect(), b = now.querySelector('.now-next .right button'), r = b?.getBoundingClientRect(), body = now.querySelector('.now-in');
    return {height: Math.round(c.height), more: body.scrollHeight > body.clientHeight + 1, button: r ? {text: b.textContent.trim(), right: Math.round(c.right - r.right), bottom: Math.round(c.bottom - r.bottom)} : null}; };
  log.start = chosen();
  d.querySelector('#waits-rows .btn[data-open="logo-color"]').click(); await wait(400);
  log.open = {tab: chosen(), tabs: tabs(), panels: panels(), seen: visible().includes(PHRASE), card: card()};
  d.querySelector('[data-tab="timeline"]').click(); await wait(2500);
  log.timeline = {tab: chosen(), panels: panels(), seen: visible().includes(PHRASE), there: words(d.getElementById('verdict').textContent).includes(PHRASE)};
  d.body.dispatchEvent(new w.KeyboardEvent('keydown', {code: 'Digit3', key: '3', bubbles: true})); await wait(300);
  log.key = {tab: chosen(), panels: panels()};
  d.querySelector('#top-right [data-open=""]').click(); await wait(400);
  log.back = {tab: chosen(), panels: panels()};
  d.querySelector('#waits-rows .btn[data-open="long-lines"]').click(); await wait(400);
  log.long = {tab: chosen(), card: card()};
  document.getElementById('out').textContent = JSON.stringify(log);
})().catch(err => { document.getElementById('out').textContent = JSON.stringify({error: String(err)}); });
</script>""")
PY
)
  "$PY" -I -c "$TABS_FIXTURE" "$PWD/skills/lem/assets" "$TABS"
  headless --virtual-time-budget=5000 --dump-dom "file://$TABS/task-logo-color.html" > "$WORK/tabs-logo.dom"
  headless --virtual-time-budget=5000 --dump-dom "file://$TABS/task-night-labels.html" > "$WORK/tabs-night.dom"
  headless --allow-file-access-from-files --virtual-time-budget=12000 --dump-dom "file://$TABS/probe.html" > "$WORK/tabs-probe.dom"
  TABS_CHECK=$(cat <<'PY'
import html, json, re, sys
found = re.search(r'<pre id="out">(.*?)</pre>', open(sys.argv[1], encoding="utf-8").read(), re.S)
d = json.loads(html.unescape(found.group(1))) if found and found.group(1) else {"error": "the probe printed nothing"}
wrong = [d["error"]] if "error" in d else []
if not wrong:
    o, tl, key, back, long = d["open"], d["timeline"], d["key"], d["back"], d["long"]
    if o['tabs'] != ["Overview", "Criteria and decisions", "Checks and review", "Timeline"]: wrong.append(f"the tabs of a task are {o['tabs']}")
    if o["tab"] != "overview" or o["panels"] != ["verdict", "hero"] or not o["seen"]: wrong.append(f"the first view: {o}")
    # the line is only in the panel of another tab now: the check of what he sees does not find it
    if tl["tab"] != "timeline" or tl["panels"] != ["tl-card", "feed-card"] or tl["seen"] or not tl["there"]: wrong.append(f"the Timeline tab, two draws later: {tl}")
    if key["tab"] != "checks" or key["panels"] != ["checks-panel"]: wrong.append(f"the key 3: {key}")
    if d['start'] != "waits" or back["tab"] != "waits" or back["panels"] != ["waits"]: wrong.append(f"All tasks goes back to {back}, from {d['start']}")
    if long['tab'] != "overview": wrong.append(f"another task opens on {long['tab']}")
    a, b = o["card"], long["card"]
    if not long["card"]["more"] or a["more"]: wrong.append(f"the long card has no more lines than fit, or the short one has: {a} / {b}")
    if a['height'] != b['height']: wrong.append(f"the large card is {a['height']} px high for a few lines and {b['height']} px for many")
    if not a["button"] or not b["button"] or a["button"] != b["button"] or a["button"]["text"] != "Go to the session": wrong.append(f"Go to the session stands at {a['button']} and at {b['button']}")
print("; ".join(wrong))
sys.exit(bool(wrong))
PY
)
  # The test of criterion 5: the plain reason on the first view, read only where no `hidden` hides it.
  # shellcheck disable=SC1111,SC1112  # the curly quotes are the page's
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/tabs-logo.dom" @visible "not green: two outside experts chose option 2 while you were away" \
      "choice 2 · The color of the logo · “the green of the shop”" "!while the task ran without you" "!choice 2 was taken by the experts") \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/tabs-night.dom" @visible "not green, for 2 reasons:" \
      'decision 2 was taken without the owner (The font of the label): "sans", by the dialectic' \
      "Lem took the recommended option of choice 1 while the task ran without you" "!while you were away" "!choice 1 was taken without the owner") \
    && why=$("$PY" -I -c "$TABS_CHECK" "$WORK/tabs-probe.dom"); then
    pass "the board of one task has the tabs Overview, Criteria and decisions, Checks and review and Timeline; its first view says \"not green: two outside experts chose option 2 while you were away\" for choice 2 the experts took in the second he went away, and \"while the task ran without you\" for a night's choice; the chosen tab stays through the draw of every second, a hidden panel's line is not what he sees, All tasks goes back to the tab he left, and the large card has one height with Go to the session in one place"
  else
    fail "the board of one task, its tabs and its first view: $why"
  fi

  # The test of criterion 9: the board reads as Lem's landing page does (site/style.css). Each tab of
  # the board of all tasks (the folder of criterion 4) and of the board of one task (the folder of
  # criterion 5), in Lem's light and in its dark palette, as agterm's theme stylesheet chooses it: the
  # computed size of every text that shows (none under 12 px, the timeline's SVG text too), its
  # contrast (4.5:1 or more, as criterion 3 asks of the first tab), the body's 16 px and 1.6, the
  # page's background and its accent, the eyebrows of the small labels, and a card of the lane
  # "Waits for you": its title and its ask at 16 px, and the radius and padding of the landing page's
  # cards (.points li: 14 px, 20px 20px 22px).
  LOOK9_FIXTURE=$(cat <<'PY'
import glob, json, os, shutil, sys
stay, tabs = sys.argv[1:]
theme = lambda scheme, background, foreground: (f"<style id=\"agterm-theme\">:where(html) {{ color-scheme: {scheme}; color: {foreground}; "
                                                f"--agterm-background: {background}; --agterm-foreground: {foreground}; }}</style>")
themes = {"light": theme("light", "#ffffff", "#1e1e1e"), "dark": theme("dark", "#15181c", "#dde1e6")}
PROBE = """<!doctype html><meta charset="utf-8"><body><pre id="out"></pre>
<script>
const FRAMES = %s;
const wait = ms => new Promise(done => setTimeout(done, ms));
const ctx = Object.assign(document.createElement('canvas'), {width: 1, height: 1}).getContext('2d', {willReadFrequently: true});
const rgba = css => { ctx.clearRect(0, 0, 1, 1); ctx.fillStyle = 'rgba(0, 0, 0, 0)'; ctx.fillStyle = css; ctx.fillRect(0, 0, 1, 1); const d = ctx.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
const over = (top, under) => [0, 1, 2].map(i => top[i] * top[3] + under[i] * (1 - top[3])).concat(1);
const lum = c => { const l = c.slice(0, 3).map(v => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * l[0] + 0.7152 * l[1] + 0.0722 * l[2]; };
const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
function measure(d, w) {
  const cs = n => w.getComputedStyle(n);
  const background = n => { const layers = []; for (let m = n; m; m = m.parentElement) { const c = rgba(cs(m).backgroundColor); if (c[3] > 0) layers.push(c); if (c[3] === 1) break; }
    return layers.reverse().reduce((under, c) => over(c, under), [255, 255, 255, 1]); };
  const small = [], low = [];
  let least = 99, smallest = 99, texts = 0;
  for (const n of d.body.querySelectorAll('*')) {
    if (n.closest('script, style, [hidden], title, desc')) continue;
    const s = cs(n);
    if (![...n.childNodes].some(c => c.nodeType === 3 && c.data.trim()) || !n.getClientRects().length || s.visibility !== 'visible' || s.display === 'none') continue;
    const label = `${n.tagName.toLowerCase()}.${[...n.classList].join('.')} "${n.textContent.trim().slice(0, 40)}"`;
    const size = parseFloat(s.fontSize);
    texts += 1; smallest = Math.min(smallest, size);
    if (size < 12) small.push(`${label} ${size}px`);
    if (n.closest('svg')) continue;
    const bg = background(n), r = ratio(over(rgba(s.color), bg), bg);
    least = Math.min(least, r);
    if (r < 4.5) low.push(`${label} ${r.toFixed(2)}`);
  }
  return {texts, smallest, small, least: Math.round(least * 100) / 100, low};
}
(async () => {
  const out = {};
  for (const f of FRAMES) {
    const node = Object.assign(document.createElement('iframe'), {src: f.src});
    node.style.cssText = 'width:1400px;height:900px;border:0;display:block';
    document.body.append(node);
    await wait(1500);
    const w = node.contentWindow, d = w.document, cs = n => w.getComputedStyle(n), root = d.documentElement, body = cs(d.body);
    const frame = {palette: root.dataset.palette ?? null, bg: cs(root).getPropertyValue('--bg').trim(), accent: cs(root).getPropertyValue('--accent').trim(),
      body: {size: body.fontSize, line: body.lineHeight, background: body.backgroundColor}, tabs: {}};
    const tabs = [...d.querySelectorAll('#tabs .tab')].map(t => t.dataset.tab);
    for (const tab of tabs) {
      d.querySelector(`#tabs [data-tab="${tab}"]`).click(); await wait(500);
      if (tab === 'backlog') { d.querySelector('[data-bl-toggle]')?.click(); await wait(300); }
      frame.tabs[tab] = measure(d, w);
      if (tab === 'tasks') {
        const lane = [...d.querySelectorAll('#lanes .lane')].find(l => l.querySelector('.lane-head').textContent.startsWith('Waits for you'));
        const card = lane?.querySelector('.tcard'), s = card && cs(card);
        frame.card = card ? {title: cs(card.querySelector('.tc-title')).fontSize, ask: cs(card.querySelector('.tc-ask > span')).fontSize,
          padding: [s.paddingTop, s.paddingRight, s.paddingBottom, s.paddingLeft].join(' '), radius: s.borderTopLeftRadius} : null;
      }
      const eyebrows = [...d.querySelectorAll('.eyebrow, .lane-head, .card-head h2')].filter(n => n.getClientRects().length && !n.closest('[hidden]'));
      frame.eyebrows = [...(frame.eyebrows ?? []), ...eyebrows.map(n => { const s = cs(n); return {what: n.textContent.trim().slice(0, 30), size: s.fontSize, upper: s.textTransform, mono: /monospace/.test(s.fontFamily), spaced: parseFloat(s.letterSpacing) > 0}; })];
    }
    out[f.id] = frame;
    node.remove();
  }
  document.getElementById('out').textContent = JSON.stringify(out);
})().catch(err => { document.getElementById('out').textContent = JSON.stringify({error: String(err)}); });
</script>"""
# each palette in a folder of its own, beside the page's data, since the page's name says which board it is
for folder, page, kind in ((stay, "board.html", "all"), (tabs, "task-logo-color.html", "one")):
    text = open(f"{folder}/{page}", encoding="utf-8").read()
    frames = []
    for palette, style in themes.items():
        os.makedirs(f"{folder}/look9-{palette}", exist_ok=True)
        for data in glob.glob(f"{folder}/*.js") + glob.glob(f"{folder}/*.css"):
            shutil.copy(data, f"{folder}/look9-{palette}/")
        open(f"{folder}/look9-{palette}/{page}", "w", encoding="utf-8").write(text.replace("<head>", "<head>" + style, 1))
        frames.append({"id": f"{kind}-{palette}", "src": f"look9-{palette}/{page}"})
    open(f"{folder}/look9-probe.html", "w", encoding="utf-8").write(PROBE % json.dumps(frames))
PY
)
  "$PY" -I -c "$LOOK9_FIXTURE" "$STAY" "$TABS"
  headless --allow-file-access-from-files --virtual-time-budget=30000 --dump-dom "file://$STAY/look9-probe.html" > "$WORK/look9-all.dom"
  headless --allow-file-access-from-files --virtual-time-budget=30000 --dump-dom "file://$TABS/look9-probe.html" > "$WORK/look9-one.dom"
  LOOK9_CHECK=$(cat <<'PY'
import html, json, re, sys
got, wrong = {}, []
for path in sys.argv[1:]:
    found = re.search(r'<pre id="out">(.*?)</pre>', open(path, encoding="utf-8").read(), re.S)
    d = json.loads(html.unescape(found.group(1))) if found and found.group(1) else {"error": f"the probe printed nothing ({path})"}
    if "error" in d: wrong.append(d["error"])
    else: got.update(d)
# the landing page's background, color-mix(in srgb, var(--you) 5%, Canvas), over Chrome's light and dark Canvas
you = (0xb4, 0x90, 0x2e)
page = lambda canvas: "rgb({}, {}, {})".format(*(round(a * .05 + b * .95) for a, b in zip(you, canvas)))
want = {"light": page((255, 255, 255)), "dark": page((18, 18, 18))}
tabs = {"all": ["tasks", "waits", "backlog"], "one": ["overview", "criteria", "checks", "timeline"]}
for kind, names in tabs.items():
    for palette in want:
        name = f"{kind}-{palette}"
        f = got.get(name)
        if not f: wrong.append(f"{name}: not drawn"); continue
        if f["palette"] != palette: wrong.append(f"{name}: the palette is {f['palette']}")
        if f["body"]["size"] != "16px" or f["body"]["line"] != "25.6px": wrong.append(f"{name}: the body is {f['body']['size']} with a line of {f['body']['line']}, not 16px and 25.6px")
        if f["body"]["background"] != want[palette]: wrong.append(f"{name}: the background is {f['body']['background']}, not the landing page's {want[palette]}")
        if f["accent"].lower() != "#b4902e": wrong.append(f"{name}: the accent is {f['accent']}, not the ochre #b4902e")
        if sorted(f["tabs"]) != sorted(names): wrong.append(f"{name}: the tabs measured are {sorted(f['tabs'])}")
        for tab, m in f["tabs"].items():
            if m["texts"] < 5: wrong.append(f"{name} {tab}: only {m['texts']} texts show")
            if m["small"]: wrong.append(f"{name} {tab}: text under 12 px: {m['small'][:5]}")
            if m["low"]: wrong.append(f"{name} {tab}: text under 4.5:1 (least {m['least']}): {m['low'][:5]}")
        flat = [e for e in f["eyebrows"] if not (e["size"] == "12px" and e["upper"] == "uppercase" and e["mono"] and e["spaced"])]
        if not f["eyebrows"] or flat: wrong.append(f"{name}: a small label is not the landing page's eyebrow: {flat[:4] or 'none measured'}")
    card = (got.get("all-light") or {}).get("card")
    if kind == "all" and card != {"title": "16px", "ask": "16px", "padding": "20px 20px 22px 20px", "radius": "14px"}:
        wrong.append(f"the card of the lane Waits for you: {card}")
# on a pass, the least contrast of each palette over every tab of both boards, for the line that says it passed
least = {palette: min((m["least"] for name, f in got.items() if name.endswith(palette) for m in f["tabs"].values()), default=0) for palette in want}
print("; ".join(wrong) or f"least {least['light']}:1 in light, {least['dark']}:1 in dark")
sys.exit(bool(wrong))
PY
)
  if why=$("$PY" -I -c "$LOOK9_CHECK" "$WORK/look9-all.dom" "$WORK/look9-one.dom"); then
    pass "the board reads as the landing page: body text at 16 px with a line of 1.6, no text under 12 px and none under 4.5:1 on any tab of either board in either palette, the landing page's warm backgrounds and its ochre accent, the small labels as its eyebrows, and a card of Waits for you with its title and ask at 16 px in a card of 14 px radius and 20px 20px 22px padding ($why)"
  else
    fail "the landing page's look: $why"
  fi

  # A board of example tasks says so on every page, and a picture of it is taken over that mark.
  board --no-open --demo >/dev/null
  board --no-open --task "$L" >/dev/null
  board --no-open --task "$G" >/dev/null
  draw "task-$L"
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$L.dom" "Demo data. These tasks are examples and not real work. Nothing on this page waits for you." "Demo data · Lem · shop · one task"); then
    pass "board --demo marks the board of one task as example data, banner and eyebrow"
  else
    fail "the demo banner: $why"
  fi

  # A nap makes no page (stages/nap.md): with a nap in the state folder the board has no tab for it and
  # board.py writes no file of the naps.
  N1=$STATE/naps/2026-11-16-0900-the-older-one
  mkdir -p "$N1"
  printf '%s\n' '# The older one' '' 'A field, and a line held over it.' > "$N1/dream.md"
  printf '%s\n' '# Waking' '' 'Nothing.' > "$N1/waking.md"
  board --no-open >/dev/null && draw board napped
  if ! grep -q 'data-tab="dreams"' "$WORK/board-napped.dom" && ! grep -q 'A field, and a line held over it' "$WORK/board-napped.dom" \
    && [ ! -e "$STATE/naps.js" ] && grep -q 'data-tab="backlog"' "$WORK/board-napped.dom"; then
    pass "a nap makes no page: the board has no tab for it, shows none of its words, and board.py writes no file of the naps"
  else
    fail "a nap on the board: $(grep -o 'data-tab="[a-z]*"' "$WORK/board-napped.dom" | tr '\n' ' ') / $(ls "$STATE")"
  fi
  # The pictures of this stress case, to look at: three widths, a light and a dark theme. The README's
  # pictures come from tests/board-showcase.py, a normal afternoon.
  if [ -n "${LEM_BOARD_SHOTS:-}" ]; then
    mkdir -p "$LEM_BOARD_SHOTS"
    for page in board "task-$G" "task-$L"; do
      draw "$page"
      cp "$STATE/$page.html" "$WORK/light.html"
      for theme in light dark; do
        if [ "$theme" = dark ]; then
          "$PY" -I -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("<head>", "<head><style id=\"agterm-theme\">:where(html) { color-scheme: dark; color: #dde1e6; --agterm-background: #15181c; --agterm-foreground: #dde1e6; }</style>", 1))' "$STATE/$page.html"
        fi
        for width in 900 1400 1800; do
          headless --hide-scrollbars --window-size="$width,2400" --virtual-time-budget=5000 --screenshot="$LEM_BOARD_SHOTS/$page-$width-$theme.png" "file://$STATE/$page.html"
          printf 'shot %s\n' "$LEM_BOARD_SHOTS/$page-$width-$theme.png"
        done
      done
      cp "$WORK/light.html" "$STATE/$page.html"
    done
    # the head of the board with a watch that looked 40 seconds ago, to look at the chip beside the proposed requests
    watch_at 40
    cp "$STATE/board.html" "$STATE/watchprobe.html" && draw watchprobe
    headless --hide-scrollbars --window-size=1400,700 --virtual-time-budget=5000 --screenshot="$LEM_BOARD_SHOTS/watch-1400-light.png" "file://$STATE/watchprobe.html"
    printf 'shot %s\n' "$LEM_BOARD_SHOTS/watch-1400-light.png"
    rm -f "$STATE/watch.js" "$STATE/watchprobe.html"
    # where the lanes start on a 1400 x 900 window, and the tallest card of each lane over its shortest
    cp "$STATE/board.html" "$WORK/board-page.html"
    "$PY" -I -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("</body>", """<script>setTimeout(() => { const pre = document.createElement("pre"); pre.id = "measured";
  const ratio = [...document.querySelectorAll("#lanes .lane")].map(l => [...l.querySelectorAll(".tcard")].map(c => c.offsetHeight)).filter(h => h.length).map(h => Math.round(100 * Math.max(...h) / Math.min(...h)) / 100);
  pre.textContent = JSON.stringify({lanes: Math.round(document.getElementById("lanes-section").getBoundingClientRect().top), card_height_ratio: ratio}); document.body.append(pre); }, 2500);</script></body>""", 1))' "$STATE/board.html"
    headless --window-size=1400,900 --virtual-time-budget=6000 --dump-dom "file://$STATE/board.html" \
      | "$PY" -I -c 'import html, re, sys; found = re.search(r"<pre id=\"measured\">([^<]*)", sys.stdin.read()); print("measured at 1400 x 900:", html.unescape(found.group(1)) if found else "nothing")'
    cp "$WORK/board-page.html" "$STATE/board.html"
  fi
  # While the owner is away the head of the board says so, with the command that ends it. Last, since his
  # away takes each choice that waits.
  project owner away --words "/lem im-away" >/dev/null && board --no-open >/dev/null && draw board away
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/board-away.dom" "the tasks go on without you until /lem im-back" "!/lem active"); then
    pass "while the owner is away, the head of the board says that the tasks go on without him until /lem im-back"
  else
    fail "the head of the board while the owner is away: $why"
  fi
fi

results_add_up
finished=yes
if [ "$fails" -gt 0 ]; then
  printf '%d failed\n' "$fails"
  exit 1
fi
printf 'all passed\n'
