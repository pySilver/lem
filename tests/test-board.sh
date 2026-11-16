#!/usr/bin/env bash
# Lem's board, offline: one repository whose tasks stand in every lane, written with Lem's own
# scripts (project.py state and log, decisions.py, stories.py), and the pages headless Chrome draws
# from it: the lanes, each task for the owner with where he answers, and the board of one task with
# its decisions, its stories' approval and read, and where its time went.
#
# A real run writes its events minutes apart, and a test writes them in seconds, so the events of
# two tasks get their times moved afterwards (`retime`), the way a run would have spaced them. The
# scripts wrote every other field. LEM_BOARD_SHOTS=DIR also writes pictures of the pages there,
# over the same tasks marked as examples (board.py --demo).
set -euo pipefail

cd "$(dirname "$0")/.."
SCRIPTS=$PWD/skills/lem/scripts
WORK=$(cd "$(mktemp -d)" && pwd -P)
trap 'rm -rf "$WORK"' EXIT
PY=$(python3 -I -c 'import sys; print(sys.executable)')
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1

fails=0
pass() { printf 'ok   %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1"; fails=$((fails + 1)); }
R=$WORK/shop
STATE=$R/.git/lem
project() { "$PY" -B "$SCRIPTS/project.py" --repo "$R" "$@"; }
decide() { "$PY" -B "$SCRIPTS/decisions.py" --repo "$R" "$@"; }
stories() { "$PY" -B "$SCRIPTS/stories.py" --repo "$R" "$@"; }
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
# times BASE + MINUTES (BASE is an ISO time, or `now`). A decision's own time moves with its event,
# and a choice's deadline stays its wait after its question, as decisions.py writes it.
RETIME=$(cat <<'PY'
import json, sys
from datetime import datetime, timedelta, timezone
log, slug, base, *minutes = sys.argv[1:]
start = datetime.now(timezone.utc).replace(microsecond=0) if base == "now" else datetime.strptime(base, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
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
    if row["event"] == "decision.asked":
        row["deadline"] = iso(moment + timedelta(minutes=row["wait_minutes"]))
open(log, "w", encoding="utf-8").write("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
open(log.removesuffix("jsonl") + "js", "w", encoding="utf-8").write("".join(f"lemEvent({json.dumps(row, ensure_ascii=False)});\n" for row in rows))
PY
)
retime() { "$PY" -I -c "$RETIME" "$STATE/events.jsonl" "$@"; }
# past SLUG ID...: the wait of each choice ends in decisions.py's own record, the way fifteen minutes later would find it
past() { "$PY" -I -c 'import json, sys
path = sys.argv[1]
lines = [json.loads(line) for line in open(path)]
for line in lines:
    if line["kind"] == "asked" and str(line["id"]) in sys.argv[2:]: line["deadline"] = "2026-01-01T00:00:00Z"
open(path, "w").write("".join(json.dumps(line) + "\n" for line in lines))' "$STATE/tasks/$1/decisions.jsonl" "${@:2}"; }
# story_file FILE KIND: the stories the owner approves, in the form `stories.py --help` gives
story_file() {
  if [ "$2" = correction ]; then
    printf '%s\n' '## Stories' '' 'Kind: correction, because the request is one sentence.' '' '1. The footer says "Terms", not "Terms and condtions".' > "$1"
  else
    printf '%s\n' '## Stories' '' 'Kind: feature, because the export gets a new column and two readers of it.' '' \
      '1. A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has that text in its row.' \
      '2. An order with no gift note has an empty cell, not the word "None".' > "$1"
  fi
}

# The task with the decisions: stories read and approved, a build with a choice of each kind.
G=gift-note-export
task "$G" "Add the gift note to the CSV export"
story_file "$WORK/gift.md" feature
digest=$(stories digest "$G" --file "$WORK/gift.md" | field 'd["digest"]')
project log "$G" stories.read by=lem asked:=3 answered:=2 'families:=["opus", "sol"]' 'silent:=[{"name": "Accountant, sol", "why": "the model was at capacity"}]' \
  stories:=2 flagged:=1 split:=true "digest=$digest" >/dev/null
stories approve "$G" --file "$WORK/gift.md" >/dev/null
project state "$G" building "lead: builder" >/dev/null
project state "$G" building "plan committed, 3 tasks" >/dev/null
project state "$G" building "task 1 of 3" >/dev/null
decide log "$G" --what "The name of the new column" --chose gift_note --why "the other columns of the export are in snake case" --by lead --undo "rename the column" >/dev/null
decide log "$G" --what "Two notes on one order" --chose "both notes, with a semicolon between them" --why "a merchant reads both" --by personas \
  --said "The merchant and the accountant both picked the semicolon." >/dev/null
decide ask "$G" --what "Where the note goes in the row" --option "the last column" --option "after the price" --recommended "the last column" \
  --why "an import that reads the columns by place keeps working" --said "The merchant picked the last column, the accountant after the price." >/dev/null
decide answer "$G" 3 --chose "the last column" --words "last, like the other new columns" >/dev/null
project state "$G" building "task 2 of 3" >/dev/null
decide ask "$G" --what "Email the merchants about the new column" --option "send it" --option "do not send it" --recommended "do not send it" \
  --why "the column is visible in the export" --said "The merchant wants the email, the accountant does not." --irreversible person >/dev/null
decide ask "$G" --what "The header of the column" --option "Gift note" --option "Note" --recommended "Gift note" --why "it says what the cell holds" --said "The two personas split." >/dev/null
decide ask "$G" --what "A note longer than the cell" --option "all of it" --option "200 characters" --recommended "all of it" --why "nothing is lost" --said "The two personas split." >/dev/null
past "$G" 5 6
decide timeout "$G" 5 >/dev/null
decide ask "$G" --what "The note of a cancelled order" --option "keep it" --option "leave it out" --recommended "keep it" --why "the export shows cancelled orders as they were" \
  --said "The merchant would keep it, the accountant is in doubt." >/dev/null
retime "$G" now -60 -52 -51 -45 -44 -40 -35 -34 -31 -30 -27 -26 -25 -10 -5

# The task whose time the card draws: it ran from its stories to a merged pull request, on 10 November.
L=landed-one
task "$L" "Show the order's currency on the invoice"
story_file "$WORK/landed.md" feature
digest=$(stories digest "$L" --file "$WORK/landed.md" | field 'd["digest"]')
project log "$L" stories.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' stories:=2 flagged:=1 split:=false "digest=$digest" >/dev/null
stories approve "$L" --file "$WORK/landed.md" >/dev/null
project state "$L" building "lead: session" >/dev/null
# the talk's start is not in this log, as in a log written before the lead logged it
project log "$L" plan.talk reviewer=codex turns:=6 questions:=4 settled:=3 open:=1 repaired:=2 design:=1 unargued:=1 root:=2 layer:=0 shared:=0 >/dev/null
project state "$L" building "plan committed, 2 tasks" >/dev/null
project state "$L" building "task 1 of 2" >/dev/null
project state "$L" building "task 2 of 2" >/dev/null
decide ask "$L" --what "The symbol or the code of the currency" --option "the symbol" --option "the code" --recommended "the code" --why "two currencies share the dollar sign" --said "The two personas split." >/dev/null
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
task stories-wait "Round the totals of the monthly report"
project state stories-wait held "the stories wait for the owner" >/dev/null
task held-question "Which currency rounds half up"
project state held-question building "lead: builder" >/dev/null
project state held-question held "how the totals round is the owner's to decide" >/dev/null
task held-choice "Refund the duplicate orders"
project state held-choice building "lead: builder" >/dev/null
decide ask held-choice --what "Refund the 12 duplicate orders now" --option "refund them" --option "leave them" --recommended "leave them" --why "a refund cannot be taken back" \
  --said "The two personas split." --irreversible money >/dev/null
project state held-choice held "choice 1 waits for the owner" >/dev/null
task open-pr "Sort the export by date"
project state open-pr open "pull request https://github.com/acme/shop/pull/9" "not green: story 1 changed during the build" >/dev/null
task ready-to-land "Fix the typo in the invoice"
project state ready-to-land open "ready to land on main at abc1234" "green" >/dev/null
task plan-for-you "Move the reports to a queue"
project state plan-for-you planned "the plan waits for the owner to read it" >/dev/null
task night-draft "Split the settings page"
project state night-draft drafted "a plan written at night" >/dev/null
task building-one "Cache the product list"
project state building-one building "task 1 of 2" >/dev/null
task queued-one "Add a dark theme"
project state queued-one queued "waits for a free place" >/dev/null
task blocked-one "Upgrade the database driver"
project state blocked-one blocked "the base moved and the rebase has a conflict" >/dev/null
task ready-one "Name the export files by date"
project state ready-one ready "the report is written" >/dev/null
task in-checks "Trim the order notes"
project state in-checks ready "the report is written" >/dev/null
project state in-checks landing "the checks start" >/dev/null
project log in-checks gate "command=make test" exit:=0 "last=9 passed" tip=def5678 >/dev/null
task correction-one "The footer says Terms and condtions"
story_file "$WORK/correction.md" correction
stories approve correction-one --file "$WORK/correction.md" --correction >/dev/null
project state correction-one building "lead: builder" >/dev/null

# A choice taken by a timeout written an hour after its wait ended, and a review logged in the same
# second as the next state block: on 11 November.
T=timed-out
task "$T" "Round the shipping costs"
project state "$T" building "lead: builder" >/dev/null
decide ask "$T" --what "Round up or to the nearest cent" --option "up" --option "to the nearest cent" --recommended "to the nearest cent" --why "the carrier rounds so" --said "The two personas split." >/dev/null
past "$T" 1
decide timeout "$T" 1 >/dev/null
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

# Stories that nobody was confused by, which still wait for the owner's yes: he left before he gave it.
task clear-read-held "Show the stock on the product page"
printf '%s\n' '## Stories' '' 'Kind: feature, because the page gets a new line.' '' '1. A product with 3 in stock says "3 left".' > "$WORK/stock.md"
digest=$(stories digest clear-read-held --file "$WORK/stock.md" | field 'd["digest"]')
project log clear-read-held stories.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest" >/dev/null
project state clear-read-held held "the stories wait for the owner" >/dev/null

# A story change of the build that the owner's next approval took over, and one after that approval.
C=changed-then-approved
task "$C" "Name the export file by its date"
printf '%s\n' '## Stories' '' 'Kind: feature, because the file name changes.' '' '1. The export of 3 May is named export-05-03.csv.' '2. A second export that day gets -2.' > "$WORK/name-1.md"
stories approve "$C" --file "$WORK/name-1.md" >/dev/null
project state "$C" building "lead: builder" >/dev/null
decide story "$C" --changed 1 --was "The export of 3 May is named export-05-03.csv." --now "The export of 3 May is named export-2026-05-03.csv." --why "a year keeps the names apart" --by lead >/dev/null
printf '%s\n' '## Stories' '' 'Kind: feature, because the file name changes.' '' '1. The export of 3 May is named export-2026-05-03.csv.' '2. A second export that day gets -2.' > "$WORK/name-2.md"
stories approve "$C" --file "$WORK/name-2.md" >/dev/null
decide story "$C" --changed 2 --was "A second export that day gets -2." --now "A second export that day gets -2, a third -3." --why "the counter goes on" --by lead >/dev/null

# The rare path: the lead's read found nobody confused, and froze the plan's stories.
task rare-path "Show the VAT number on the invoice"
rw=$(project worktree-dir rare-path)
git -C "$R" worktree add -q -b feat/rare-path "$rw" main
mkdir -p "$rw/docs/plans"
printf '%s\n' '# Rare path' '' '## Stories' '' 'Kind: feature, because the invoice gets a new line.' '' '1. An invoice to a company shows its VAT number under its name.' '' '## Tasks' '' '1. The line.' > "$rw/docs/plans/20261116-rare-path.md"
project state rare-path building "lead: builder" >/dev/null
digest=$(stories digest rare-path | field 'd["digest"]')
project log rare-path stories.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest" >/dev/null
stories approve rare-path --read >/dev/null

# A task the owner holds at the reviewer's trust prompt: a step of his, and no decision.
task trust-prompt "Move the review to Codex"
project state trust-prompt building "lead: session" >/dev/null
project state trust-prompt held "the reviewer's trust prompt waits for the owner's yes" >/dev/null

# The usual path writes the personas' read before the task's first state block.
task read-first "Show the order's weight on the label"
printf '%s\n' '## Stories' '' 'Kind: feature, because the label gets a new line.' '' '1. A parcel of 2.5 kg says "2.5 kg" on its label.' > "$WORK/weight.md"
digest=$(stories digest read-first --file "$WORK/weight.md" | field 'd["digest"]')
project log read-first stories.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest" >/dev/null

# The plan's stories and their tests' result, and then a new approval of other stories.
task approved-again "Print the packing slip in German"
printf '%s\n' '## Stories' '' 'Kind: feature, because the slip gets a language.' '' '1. A slip for Berlin is in German.' > "$WORK/slip-1.md"
printf '%s\n' '## Stories' '' 'Kind: feature, because the slip gets a language.' '' '1. A slip for Berlin or Vienna is in German.' > "$WORK/slip-2.md"
stories approve approved-again --file "$WORK/slip-1.md" >/dev/null
project state approved-again building "task 1 of 1" >/dev/null
project log approved-again task.stories kind=feature "why=the slip gets a language." digest=0123456789ab \
  'stories:=[{"n": 1, "text": "A slip for Berlin is in German.", "tests": [{"command": "sh tests/slip.sh", "files": ["tests/slip.sh"]}], "no_test": null}]' >/dev/null
project log approved-again task.red ok:=true digest=0123456789ab base=0a1b2c3d4 tip=abc123456 \
  'tests:=[{"story": 1, "command": "sh tests/slip.sh", "files": ["tests/slip.sh"], "on_branch": 0, "on_base": 1, "problem": null}]' 'without_a_test:=[]' 'run_without:=[]' >/dev/null
stories approve approved-again --file "$WORK/slip-2.md" >/dev/null

# Stories read and approved, changed by the build, then approved again as they were read: nothing is unread.
# Beside it the same without the second approval: the change was not read.
for slug in restored-read unread-change; do
  task "$slug" "Name the carrier on the slip"
  printf '%s\n' '## Stories' '' 'Kind: feature, because the slip gets a line.' '' '1. A DHL parcel says "DHL" on its slip.' > "$WORK/$slug.md"
  digest=$(stories digest "$slug" --file "$WORK/$slug.md" | field 'd["digest"]')
  project log "$slug" stories.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest" >/dev/null
  stories approve "$slug" --file "$WORK/$slug.md" >/dev/null
  project state "$slug" building "lead: builder" >/dev/null
  decide story "$slug" --changed 1 --was 'A DHL parcel says "DHL" on its slip.' --now 'A DHL parcel says "DHL Express" on its slip.' --why "the carrier's own name" --by lead >/dev/null
done
stories approve restored-read --file "$WORK/restored-read.md" >/dev/null

# The two experts' advice on five choices: one they settled while the owner was away, with his answer
# after it, one taken at
# the end of its wait with their shared pick, one at the end of its wait while they split, and two
# that still wait, the first with a shared pick and the second with none. Its state block comes a
# minute after the gift note's, so that the gift note stays the news of the board of all tasks.
X=expert-advice
task "$X" "Print the invoice for the post"
project state "$X" building "lead: builder" >/dev/null
decide ask "$X" --what "The paper size" --option "A4" --option "Letter" --recommended "Letter" --why "the printer has Letter in its tray" --said "The two personas split." >/dev/null
decide advise "$X" 1 --expert fable --pick A4 --why "every customer of the shop is in Europe, where the post reads A4" >/dev/null
decide advise "$X" 1 --expert astra --pick A4 --why "the envelopes of the shop are cut for A4" >/dev/null
decide settle "$X" 1 --away >/dev/null
decide answer "$X" 1 --chose Letter --words "Letter, it is in the tray" >/dev/null
decide ask "$X" --what "The color of the logo" --option "black" --option "the green of the shop" --recommended "black" --why "a black logo prints on every printer" --said "The two personas split." >/dev/null
decide advise "$X" 2 --expert fable --pick "the green of the shop" --why "the invoice is a page of the shop" >/dev/null
decide advise "$X" 2 --expert astra --pick "the green of the shop" --why "the printer prints in color" >/dev/null
decide ask "$X" --what "The order number on the page" --option "at the top" --option "at the foot" --recommended "at the top" --why "the post office reads the top first" --said "The two personas split." >/dev/null
decide advise "$X" 3 --expert fable --pick "at the top" --why "a reader looks for it first" >/dev/null
decide advise "$X" 3 --expert astra --pick "at the foot" --why "the top holds the address window" >/dev/null
past "$X" 2 3
decide timeout "$X" 2 >/dev/null
decide timeout "$X" 3 >/dev/null
decide ask "$X" --what "The font of the invoice" --option "serif" --option "sans" --recommended "sans" --why "it reads well on a screen" --said "The two personas split." >/dev/null
decide advise "$X" 4 --expert fable --pick serif --why "a printed invoice reads better in serif" >/dev/null
decide advise "$X" 4 --expert astra --pick serif --why "the letters of the shop are in serif" >/dev/null
decide ask "$X" --what "The size of the total" --option "12 pt" --option "14 pt" --recommended "14 pt" --why "a reader finds the total first" --said "The two personas split." >/dev/null
decide advise "$X" 5 --expert fable --none --why "the total should be bold, not bigger" >/dev/null
decide advise "$X" 5 --expert astra --pick "12 pt" --why "the other lines are 12 pt" >/dev/null
retime "$X" now -50 -49 -48 -47 -46 -45.5 -45 -44 -43 -42 -41 -40 -29 -26 -6 -5 -4 -3 -2 -1

# A landing whose polish pass is logged and whose checks run, and one that has only started.
P=polished
task "$P" "Name the invoice files by order"
project state "$P" ready "the report is written" >/dev/null
project state "$P" landing "the checks start" >/dev/null
project log "$P" polish before=abc1234 after=def5678 commits:=2 'filed:=["docs/backlog/invoice-footer-typo.md"]' >/dev/null
retime "$P" now -40 -30 -12
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
project state "$A" building "a builder reproduces the bug and finds its cause" "investigation: bug" "kind: bug, because the ask says the total is wrong today" >/dev/null
printf '%s\n' '# Investigation' '' 'Reproduced: yes, with tests/refund.sh.' > "$STATE/tasks/$A/investigation.md"
project log "$A" investigation kind=bug call=not-a-bug "line=a refund is a credit note, and the invoice shows what is left to pay" where=billing/invoice.py:total reproduced:=true >/dev/null
project state "$A" answered "not a bug: the invoice shows what is left to pay" "report: investigation.md" >/dev/null
retime "$A" now -30 -12 -11
# A bug whose investigation runs.
task cart-total-wrong "The cart total is wrong since yesterday"
project state cart-total-wrong building "a builder reproduces the bug and finds its cause" "investigation: bug" "kind: bug, because the ask says the total is wrong since yesterday" >/dev/null

if [ "$(grep -c '"event": "decision.' "$STATE/events.jsonl")" = 37 ] && [ "$(grep -c '"task": "gift-note-export"' "$STATE/events.js")" = 15 ]; then
  pass "the fixture is written by Lem's scripts: every decision is an event, and the board's copy of the log holds the moved times"
else
  fail "the fixture: $(grep -c '"event": "decision.' "$STATE/events.jsonl") decision events"
fi

board --no-open >/dev/null
for slug in "$G" "$L" correction-one "$T" red-gate clear-read-held "$C" rare-path read-first approved-again restored-read unread-change "$X" "$P" landing-starts "$K" talk-runs "$M" "$A" cart-total-wrong; do board --no-open --task "$slug" >/dev/null; done

SHOWN=$(cat <<'PY'
import re, sys
from html.parser import HTMLParser
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.skip = 0; self.text = []; self.title = ""; self.in_title = False
    def handle_starttag(self, tag, attrs):
        self.skip += tag in ("script", "style"); self.in_title = tag == "title" and not self.skip
    def handle_endtag(self, tag):
        self.skip -= tag in ("script", "style"); self.in_title = False
    def handle_data(self, data):
        if self.in_title and not self.title: self.title = data
        elif not self.skip: self.text.append(data)
p = P(); p.feed(open(sys.argv[1], encoding="utf-8").read())
shown = " ".join(" ".join(p.text).split())
# "!TEXT" must not be on the page, and "~PATTERN" is a regular expression that must match it
missing = [want for want in sys.argv[2:] if want[0] not in "!~" and want not in shown and want not in p.title]
missing += [f"no match of {want[1:]!r}" for want in sys.argv[2:] if want.startswith("~") and not re.search(want[1:], shown)]
missing += [f"no {want[1:]!r}" for want in sys.argv[2:] if want.startswith("!") and (want[1:] in shown or want[1:] in p.title)]
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
# BANNERS DOM PATTERN ...: each regular expression matches the text of one banner, and "!PATTERN" none
BANNERS=$(cat <<'PY'
import html, re, sys
dom = open(sys.argv[1], encoding="utf-8").read()
area = dom[dom.index('id="banners"'):dom.index('<header class="top">')]
banners = [" ".join(html.unescape(re.sub(r"<[^>]+>", " ", '<div class="banner ' + part)).split()) for part in re.split(r'<div class="banner ', area)[1:]]
wrong = [f"no banner matches {want!r}" for want in sys.argv[2:] if not want.startswith("!") and not any(re.search(want, text) for text in banners)]
wrong += [f"a banner matches {want[1:]!r}" for want in sys.argv[2:] if want.startswith("!") and any(re.search(want[1:], text) for text in banners)]
print("; ".join(wrong) + (f" (the banners: {banners})" if wrong else ""))
sys.exit(bool(wrong))
PY
)
# LANES DOM 'LANE=TITLE|WHERE' ...: the card of TITLE is in LANE, and its line of where the owner answers is WHERE
LANES=$(cat <<'PY'
import html, re, sys
dom = open(sys.argv[1], encoding="utf-8").read()
text = lambda s: " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())
lanes = {}
for part in re.split(r'<div class="lane a-', dom)[1:]:
    title = text(re.search(r'<div class="lane-head">(.*?)<em', part, re.S).group(1))
    cards = {}
    for card in re.split(r'<button class="tcard ', part)[1:]:
        name = text(re.search(r'<div class="tc-title">(.*?)</div>', card, re.S).group(1))
        where = re.search(r'<div class="tc-where">(.*?)</div>', card, re.S)
        cards[name] = text(where.group(1)) if where else ""
    lanes[title] = cards
wrong = []
for want in sys.argv[2:]:
    lane, _, rest = want.partition("=")
    name, _, where = rest.partition("|")
    if name not in lanes.get(lane, {}):
        wrong.append(f"{name!r} is not in {lane!r} ({ {k: list(v) for k, v in lanes.items()} })")
    elif where and lanes[lane][name] != where:
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
# Every clock time on the pages is in UTC, so a check of one reads the same on every machine.
headless() { TZ=UTC "$chrome" --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" "$@" 2>/dev/null || true; }
draw() { headless --virtual-time-budget=5000 --dump-dom "file://$STATE/$1.html" > "$WORK/$1.dom"; }

if [ -z "$chrome" ]; then
  printf 'SKIP the board pages: no Chrome or Chromium found\n'
else
  draw board
fi
if [ -n "$chrome" ] && [ ! -s "$WORK/board.dom" ]; then
  # A Chrome that cannot start (a sandbox that forbids it) says nothing about the page.
  printf 'SKIP the board pages: %s printed no page\n' "$chrome"
elif [ -n "$chrome" ]; then
  # shellcheck disable=SC1111  # the curly quotes around a state's own line are the page's
  if why=$("$PY" -I -B -c "$LANES" "$WORK/board.dom" \
    "Waits for you=Gift note export|Lem puts choice 7 to you as a page in its session. Answer it there before its wait ends; then the lead takes the recommended action." \
    "Waits for you=Held choice|Lem puts choice 1 to you as a page in its session. Answer it there: it waits for your word, with no end." \
    "Waits for you=Held question|It waits on what its state says: “how the totals round is the owner's to decide”. Lem tells you in its session what to do and where." \
    "Waits for you=Trust prompt|It waits on what its state says: “the reviewer's trust prompt waits for the owner's yes”. Lem tells you in its session what to do and where." \
    "Building=Approved again" "Building=Restored read" "Building=Unread change" \
    "Waits for you=Clear read held|Lem shows you the stories, with the personas’ read on top, as a page in its session. Approve or change them there." \
    "Waits for you=Stories wait|Lem shows you the stories, with the personas’ read on top, as a page in its session. Approve or change them there." \
    "Waits for you=Plan for you|Read the plan, then tell Lem in its session: build it or drop it." \
    "Waits for you=Night draft|Tell Lem in its session: /lem build night-draft, or drop it." \
    "Waits for you=Open pr|Merge the pull request, or tell Lem in its session to land it." \
    "Waits for you=Ready to land|Tell Lem in its session to land it." \
    "Building=Building one" "Building=Queued one" "Building=Blocked one" "Building=Correction one" "Building=Changed then approved" "Building=Rare path" \
    "Checks and review=Ready one" "Checks and review=In checks" "Checks and review=Red gate" "Done=Landed one" "Done=Timed out"); then
    pass "each task is in the lane of who acts, and each one that waits for the owner says where he answers: a choice, a held decision, the stories, a plan, a draft, a pull request, a branch to land"
  else
    fail "the lanes: $why"
  fi
  # Each banner is read alone, so that a card's text elsewhere on the page cannot stand in for one.
  if why=$("$PY" -I -B -c "$BANNERS" "$WORK/board.dom" \
    "^Choice 7 waits for you: Gift note export · The note of a cancelled order · (9m [0-9]{2}s|10m) left Lem puts choice 7 to you as a page in its session" \
    "^Choice 4 waits for you: Gift note export · Email the merchants about the new column · no end: no timeout takes it Lem puts choice 4" \
    "^Choice 1 waits for you: Held choice · Refund the 12 duplicate orders now · no end: no timeout takes it" \
    "^Waits for you: Stories wait · the stories wait for the owner" "!^Choice 6" "!Choice 5 waits for you: Gift note export" "!^Waits for you: Held choice" \
    "!^Choice [123] waits for you: Expert advice") \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/board.dom" "11 wait for you, 12 build, 5 in checks and review, 1 queued" "You · choice 7 of the task" "!Demo data"); then
    pass "the board of all tasks puts each choice that waits for the owner in a banner and in the card it opens on, with its count-down, or no end for an irreversible step, and none whose wait is over"
  else
    fail "the banners: $why"
  fi

  draw "task-$G"
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$G.dom" "Decisions" "2 wait for you · 1 with the wait over · 4 taken" \
    "Choice 7 waits for you: The note of a cancelled order" "options: keep it · leave it out" "recommended: keep it, because the export shows cancelled orders as they were" \
    "the personas: The merchant would keep it, the accountant is in doubt." "Its wait ends at " 'then the lead takes “keep it”, the recommended option, unless both experts pick one option before then.' "~(9m [0-9]{2}s|10m) left" \
    "Choice 4 waits for you: Email the merchants about the new column" "It waits for your answer, with no end: it sends something to a person, so no timeout takes it." "no end" \
    "Choice 6, its wait is over: A note longer than the cell" 'and no timeout is written yet: the lead takes “all of it”, the recommended option, as no expert advised.' "wait over" \
    "5. The header of the column → Gift note" "taken by the timeout at " "no answer came in 15 minutes. The recommended action stands, and the pull request is not green for it." \
    "1. The name of the new column → gift_note" "taken by the lead, because the other columns of the export are in snake case" "to undo: rename the column" \
    "2. Two notes on one order → both notes, with a semicolon between them" "taken by the personas, because a merchant reads both" "the personas: The merchant and the accountant both picked the semicolon." \
    "3. Where the note goes in the row → the last column" 'answered by you: “last, like the other new columns”' \
    "2 choices wait for you" "left of the wait, until "); then
    pass "the board of one task has a Decisions card: each choice that waits with the end of its wait and its count-down, an irreversible one with no end, one whose wait is over, one taken by the timeout, and each taken one with what, by whom and why"
  else
    fail "the Decisions card: $why"
  fi
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$G.dom" "The two model families split on a story." "1 of 2 stories flagged" \
    "read by 2 of 3 personas, two model families (opus, sol), run by Lem" "no answer from Accountant, sol (the model was at capacity)" "Approved by you after the personas’ read" \
    'A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has that text in its row.' "no test yet: the lead adds its tests in the plan") \
    && "$PY" -I -c 'import re, sys
dom = re.sub(r"<[^>]+>", " ", open(sys.argv[1], encoding="utf-8").read())
sys.exit(not dom.index("The two model families split") < dom.index("1 of 2 stories flagged") < dom.index("read by 2 of 3 personas"))' "$WORK/task-$G.dom"; then
    pass "the Stories card shows the personas' read with a split between the families said first, who answered of how many, who did not and why, and the owner's approval after it"
  else
    fail "the Stories card: ${why:-the split is not said first}"
  fi
  draw task-correction-one
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-correction-one.dom" "Taken as a correction: Lem approved its one story in your name" \
    'You may still say “this is a feature”' "The personas do not read a correction’s one story." "correction, because the request is one sentence."); then
    pass "a correction's Stories card says that Lem approved its one story in the owner's name, that he may call it a feature, and that the personas do not read it"
  else
    fail "a correction's Stories card: $why"
  fi

  draw "task-$L"
  # The rows and the legend are read from the card itself, so that a name elsewhere on the page cannot stand in for a row.
  if why=$("$PY" -I -B -c "$TIMECARD" "$WORK/task-$L.dom" "You|Lem|The lead|The builders|The personas|The checks|The review" \
    "You=1h 05m · 46%" "Lem=6m 00s · 4%" "The lead=17m · 12%" "The builders=42m · 30%" "The checks=5m 00s · 4%" "The review=11m · 8%") \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$L.dom" "Where the time went" "Stories" "Plan" "T1" "T2" "Checks" "PR") \
    && ! grep -q 'class="nowline"' "$WORK/task-$L.dom"; then
    pass "the time card of a task has a row for each actor that held its work and a band for each stage and plan task, and its legend gives each actor's total and share of the task's time"
  else
    fail "the time card: $why"
  fi
  # The hover, as a reader's mouse makes it: over a band of the plan, and over a span of the owner's row.
  cat > "$STATE/probe.html" <<'PROBE'
<!doctype html><meta charset="utf-8"><iframe id="f" src="task-landed-one.html" style="width:1400px;height:1400px;border:0"></iframe><pre id="out"></pre>
<script>
const wait = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  await wait(1500);
  const w = document.getElementById('f').contentWindow, d = w.document, log = {};
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
    "a mark: what ended, and when": d.get("mark", "").startswith("The personas · The personas’ read of the stories ended | 2 of 2 answered") and d.get("mark", "").endswith("at Nov 10 09:10:00"),
    "the hover goes when the mouse leaves": d.get("left") is True,
}.items() if not ok]
print("; ".join(wrong) or "ok", "" if not wrong else json.dumps(d))' "$WORK/probe.dom" 2>&1 || true)
  if [ ! -s "$WORK/probe.dom" ]; then
    printf 'SKIP the hover of the time card: %s printed no page\n' "$chrome"
  elif [ "$hovered" = "ok " ]; then
    pass "a hover on a band, a span or a mark of the time card says what it is, how long it took and its two clock times, as in \"Task 1 · 18m · 09:40:00 → 09:58:00\""
  else
    fail "the hover of the time card: $hovered"
  fi

  # A choice whose wait ended at 09:20 and whose timeout was written at 10:05 held the owner 15 minutes, not an hour.
  draw "task-$T"
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$T.dom" "You 25m · 28%") \
    && grep -q 'data-head="You · Choice 1: Round up or to the nearest cent" data-sub="its wait ended at 09:20; the timeout took “to the nearest cent” at 10:05"' "$WORK/task-$T.dom"; then
    pass "a choice holds the owner's row from its question to the end of its wait, and not until a timeout written later"
  else
    fail "a choice after its wait: ${why:-the hover of the choice}"
  fi
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$T.dom" "The review 4m 00s · 4%" "Lem 2m 00s · 2%" "The checks 4m 00s · 4%"); then
    pass "a review logged in the same second as the next state block is still the review's time: the order of the log, not the second, says which block an event belongs to"
  else
    fail "an event in the second of the next block: $why"
  fi
  draw task-red-gate
  # The task is open, so its card runs to the board's now, which is later than the fixture's now by the
  # run time between the two, d >= 0: retime floors its now to the second and the board ceils its own to
  # 15 s. The checks hold 10m whatever d is, and Lem holds 30m + d, so the two shares move with d (25% and
  # 75% at d = 0, 24% and 76% once d passes about 49 s). SHARES takes Lem's minutes as shown and accepts
  # only the shares that some d inside that minute gives.
  SHARES=$(cat <<'PY'
import html, math, re, sys
dom = open(sys.argv[1], encoding="utf-8").read()
area = dom[dom.index('id="legend"'):]
area = area[:area.index("</div>")]
legend = {html.unescape(label): html.unescape(value) for label, value in re.findall(r"<span[^>]*><i[^>]*></i>(.*?)<em>(.*?)</em></span>", area)}
lem = re.fullmatch(r"(?:(\d+)h )?(\d+)m · (\d+)%", legend.get("Lem", ""))
checks = re.fullmatch(r"10m · (\d+)%", legend.get("The checks", ""))
if not lem or not checks:
    sys.exit(f"the legend is {legend}")
minutes = 60 * int(lem.group(1) or 0) + int(lem.group(2))
share = lambda part, whole: math.floor(100 * part / whole + 0.5)  # Math.round
# Lem holds [minutes, minutes + 1) minutes, the checks 10, the whole is the sum of the two.
low, high = 60 * minutes, 60 * minutes + 60
want_checks = {share(600, 600 + low), share(600, 600 + high)}
want_lem = {share(low, 600 + low), share(high, 600 + high)}
ok = minutes >= 30 and min(want_checks) <= int(checks.group(1)) <= max(want_checks) and min(want_lem) <= int(lem.group(3)) <= max(want_lem)
print("" if ok else f"the legend is {legend}: with Lem at {minutes}m the checks' share is one of {sorted(want_checks)} and Lem's one of {sorted(want_lem)}")
sys.exit(not ok)
PY
)
  if why=$("$PY" -I -B -c "$TIMECARD" "$WORK/task-red-gate.dom" "You|Lem|The checks" "The checks=~10m · \d+%" "Lem=~(\d+h )?\d+m · \d+%") \
    && why=$("$PY" -I -B -c "$SHARES" "$WORK/task-red-gate.dom") \
    && grep -q 'data-head="Lem · After a failed check: a repair or a stop, and no event says which yet"' "$WORK/task-red-gate.dom" \
    && ! grep -q 'data-head="The checks · The checks run' "$WORK/task-red-gate.dom"; then
    pass "a gate run whose first command failed is checks until its last command, with no repair between its commands, and after the whole run failed the time is not drawn as checks that go on"
  else
    fail "after a failed check: ${why:-the span after the red gate}"
  fi
  draw task-read-first
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-read-first.dom" "No state block was written yet for the task \"read-first\": its 1 event is in the activity below" \
    "The personas read the stories" "nobody confused · 2 of 2 answered"); then
    pass "the board of a task whose stories were read before its first state block draws its events and says that its state comes later"
  else
    fail "a task with events and no state: $why"
  fi
  draw task-approved-again
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-approved-again.dom" "1. A slip for Berlin or Vienna is in German." \
    "approved after the plan’s stories were recorded: the lead records them again, with their tests" "approval 2; it replaces approval 1" \
    "!held by its tests" "!A slip for Berlin is in German." "feature, because the slip gets a language."); then
    pass "after a new approval the Stories card shows the approved stories, not the plan's older ones and their tests' result"
  else
    fail "stories approved after the plan's: $why"
  fi
  draw task-restored-read && draw task-unread-change
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-restored-read.dom" "Story 1 changed during the build" "!the change was not read") \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-unread-change.dom" "The stories changed after this read by a change of the build, and the change was not read."); then
    pass "the Stories card says that a change was not read only while the stories as they stand are not the ones read: his approval of the read stories again clears it"
  else
    fail "the unread change: $why"
  fi
  draw task-clear-read-held
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-clear-read-held.dom" "Nobody confused" "The stories wait for your yes" "!The build started with no wait for you"); then
    pass "a read that found nobody confused does not say that the build started, while the stories wait for the owner's yes"
  else
    fail "a clear read that waits for him: $why"
  fi
  draw "task-$C"
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$C.dom" "approval 2; it replaces approval 1" \
    "Story 1 changed during the build" "Approved by you afterwards (approval 2): it is yours, and no cause of not green" \
    "Story 2 changed during the build" "the counter goes on · by the lead · the pull request is not green for it" \
    "!a year keeps the names apart · by the lead · the pull request is not green for it"); then
    pass "a story change that the owner's later approval took over is his and no cause of not green, and a change after that approval still is one"
  else
    fail "story changes and approvals: $why"
  fi
  draw task-rare-path
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-rare-path.dom" "Frozen by the personas’ read, with no wait for you" "!Taken as a correction" "!Approved by you"); then
    pass "stories the personas' read froze on the rare path are shown as such, never as a correction or as the owner's yes"
  else
    fail "the read's approval: $why"
  fi

  # The experts' advice. Each check reads one row of one card, or one banner, so that a text of
  # another choice or of the activity cannot stand in for it.
  draw "task-$X"
  # shellcheck disable=SC1111,SC1112  # the curly quotes around a pick are the page's
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" decisions \
      "Choice 4 waits for you: The font of the invoice|Fable picks “serif”, because a printed invoice reads better in serif|Astra picks “serif”, because the letters of the shop are in serif|~Its wait ends at [0-9]{2}:[0-9]{2}; then the lead takes “serif”, the experts’ shared pick\.|Where you answer: Lem puts choice 4 to you as a page in its session. Answer it there before its wait ends; then the lead takes the experts’ shared pick.|!the recommended option" \
      "Choice 5 waits for you: The size of the total|Fable finds that none of the options fits, because the total should be bold, not bigger|Astra picks “12 pt”, because the other lines are 12 pt|then the lead takes “14 pt”, the recommended option, as the experts have no shared pick.|then the lead takes the recommended action.|!the experts’ shared pick" \
      "1. The paper size|!Fable picks|!waits for you") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" now \
      "2 choices wait for you|The font of the invoice|the experts: Fable “serif” · Astra “serif”|~until [0-9]{2}:[0-9]{2}; then the lead takes the experts’ shared pick") \
    && why=$("$PY" -I -B -c "$BANNERS" "$WORK/board.dom" \
      "^Choice 4 waits for you: Expert advice · The font of the invoice · .* then the lead takes the experts’ shared pick\.$" \
      "^Choice 5 waits for you: Expert advice · The size of the total · .* then the lead takes the recommended action\.$"); then
    pass "a choice that waits shows each expert's advice in its own row of the Decisions card, a pick or none fits with its reasons, and its row, its banner and the head of its board say that the end of the wait takes the experts' shared pick when both agree, else the recommended option"
  else
    fail "the experts' advice on a choice that waits: $why"
  fi
  # shellcheck disable=SC1111,SC1112  # the curly quotes around a pick are the page's
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" decisions \
      "1. The paper size → A4|@a-bad|~taken by the experts at [0-9]{2}:[0-9]{2}, while you were away, before its wait ended: both picked it\. The pull request is not green for it\.|Fable picked “A4”, because every customer of the shop is in Europe, where the post reads A4|Astra picked “A4”, because the envelopes of the shop are cut for A4|~Your answer came at [0-9]{2}:[0-9]{2}, after the experts took it: “Letter” \(Letter, it is in the tray\)\. It differs from what was taken|!taken by the timeout") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" feed \
      "Choice 1 taken by the experts while you were away|A4|Fable: every customer of the shop is in Europe, where the post reads A4 · Astra: the envelopes of the shop are cut for A4" \
      "Your answer to choice 1 came after it was taken|Letter") \
    && grep -Eq 'data-head="You · Choice 1: The paper size" data-sub="the experts took “A4” at [0-9]{2}:[0-9]{2}, while you were away"' "$WORK/task-$X.dom"; then
    pass "a choice the experts settled while the owner was away is in the Decisions card as taken by the experts, marked like a timeout, with their pick and both reasons, and his answer after it as after the experts took it; the activity and the time card say so"
  else
    fail "a choice the experts settled: ${why:-the hover of the settled choice}"
  fi
  # shellcheck disable=SC1111,SC1112  # the curly quotes around a pick are the page's
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" decisions \
      "2. The color of the logo → the green of the shop|@a-bad|~taken by the experts at the end of the wait, at [0-9]{2}:[0-9]{2}: no answer came in 15 minutes, and both picked it\. The pull request is not green for it\.|Fable picked “the green of the shop”, because the invoice is a page of the shop|Astra picked “the green of the shop”, because the printer prints in color|!taken by the timeout" \
      "3. The order number on the page → at the top|@a-bad|~taken by the timeout at [0-9]{2}:[0-9]{2}: no answer came in 15 minutes\. The recommended action stands, and the pull request is not green for it\.|the experts split: Fable picked “at the top”, because a reader looks for it first · Astra picked “at the foot”, because the top holds the address window|!taken by the experts") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" feed \
      "Choice 2 taken by the experts at the end of its wait|the green of the shop|Fable: the invoice is a page of the shop · Astra: the printer prints in color" \
      "Choice 3 taken by the timeout|at the top|!experts" \
      "Astra advised on choice 3|picks “at the foot”|the top holds the address window" \
      "Fable advised on choice 5|none of the options fits|the total should be bold, not bigger") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" progress "Decisions|3 taken, 1 by the timeout, 2 by the experts") \
    && grep -Eq 'data-head="You · Choice 2: The color of the logo" data-sub="its wait ended at [0-9]{2}:[0-9]{2}; the experts’ shared pick “the green of the shop” was taken at [0-9]{2}:[0-9]{2}"' "$WORK/task-$X.dom"; then
    pass "a timeout that took the experts' shared pick names them with both reasons, and one whose experts split is the timeout's with the recommended option and each expert's advice, in the Decisions card, the activity, the count of decisions and the time card"
  else
    fail "a timeout with the experts' advice: ${why:-the hover of the timeout the experts took}"
  fi
  draw "task-$P" && draw task-landing-starts
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$P.dom" feed "The polish pass|2 commits, 1 item filed in the backlog|abc1234 → def5678|docs/backlog/invoice-footer-typo.md") \
    && why=$("$PY" -I -B -c "$TIMECARD" "$WORK/task-$P.dom" "You|Lem|The builders|The checks" "Lem=~10m · 2[45]%" "The builders=~18m · 4[45]%" "The checks=~1[12]m · (2[89]|3[01])%") \
    && grep -q 'data-head="The builders · The polish pass" data-sub="from the event before it: its start is not logged, so the rebase onto the base is in it"' "$WORK/task-$P.dom" \
    && grep -q 'data-head="The checks · The checks run"' "$WORK/task-$P.dom" \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$P.dom" now "The checks and the review run on it") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-landing-starts.dom" now "It starts its landing: the rebase onto the base, then the polish pass|!The checks and the review run on it") \
    && grep -q 'data-head="Lem · The landing starts: the rebase onto the base, then the polish pass, and no event says which runs yet"' "$WORK/task-landing-starts.dom" \
    && ! grep -q 'data-head="The checks · The checks run"' "$WORK/task-landing-starts.dom"; then
    pass "the polish pass is in the activity with its commits and the items it filed, and on the time card as the builders' span from the event before it; a landing with no polish and no check yet says that it starts, not that its checks run"
  else
    fail "the polish pass: ${why:-a span of the time card}"
  fi
  # The plan talk from its start to its record is a span of the review's row, with its counts; with
  # no start in the log it is a dot where it ended, and with a start and no record yet it runs.
  draw "task-$K" && draw task-talk-runs && draw "task-$L"
  if grep -q 'data-head="The review · The plan talk" data-sub="with codex: 3 questions in 7 turns · 2 settled, 1 open, 1 of them a design choice · 2 repaired: 1 at the cause, 1 a layer over a cited decision · 1 decision two questions named · 2 raised, not argued"' "$WORK/task-$K.dom" \
    && why=$("$PY" -I -B -c "$TIMECARD" "$WORK/task-$K.dom" "You|The lead|The review" "The lead=25m · 100%" "The review=18m · 72%") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$K.dom" feed "The plan talk started|with codex" "The plan talk ended|with codex: 3 questions in 7 turns|1 of them a design choice|2 raised, not argued") \
    && ! grep -q 'data-sub="[^"]*its start is not logged' "$WORK/task-$K.dom" \
    && grep -q 'data-head="The review · The plan talk ended" data-sub="with codex: 4 questions in 6 turns · 3 settled, 1 open, 1 of them a design choice · 2 repaired: 2 at the cause · 1 raised, not argued · its start is not logged"' "$WORK/task-$L.dom" \
    && grep -q 'data-head="The review · The plan talk runs" data-sub="with claude; its record comes when the talk ends"' "$WORK/task-talk-runs.dom"; then
    pass "the plan talk is the review's span from its start to its record, with its questions, turns, settled, open, design choices, repairs at the cause and layers over a cited decision, decisions two questions named and questions raised and not argued; one with no start logged is a dot where it ended, and one with no record yet runs"
  else
    fail "the plan talk on the time card: ${why:-a span or a dot of the talk}"
  fi
  # The talk's companion is shown as a companion of the talk, and the builder lead after it.
  draw "task-$M"
  if grep -q 'title="A companion session holds the plan talk: its agent defends the plan, the reviewer sits in its other pane, and a builder leads the build after it"' "$WORK/task-talk-runs.dom" \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-talk-runs.dom" "Its companion talks the plan through" "talk companion" "a companion for the plan talk, with the reviewer in its other pane" "!Its session builds it") \
    && grep -q 'title="One builder leads the build, after the plan talk in its companion"' "$WORK/task-$M.dom" \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$M.dom" "one builder leads the build, after the plan talk in its companion" "!talk companion") \
    && grep -q 'data-head="Lem · The plan talk is done: the plan waits for its builder lead"' "$WORK/task-$M.dom" \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$M.dom" feed "The plan talk ended|with codex: 2 questions in 5 turns|2 repaired: 1 a layer over a cited decision|!at the cause") \
    && grep -q 'title="A companion session holds the plan talk' "$WORK/board.dom" && grep -q 'title="One builder leads the build, after the plan talk in its companion"' "$WORK/board.dom"; then
    pass "a task whose plan talk runs in its companion shows the companion as the talk's, and after the talk the builder lead that builds it, with the wait between the two as Lem's and the layer the talk accepted"
  else
    fail "the talk's companion and the builder after it: ${why:-a tag, a head or a span}"
  fi
  # An answered task is in the lane of what ended, with its investigation's answer, on the board and on its own.
  draw "task-$A"
  if why=$("$PY" -I -B -c "$LANES" "$WORK/board.dom" "Done=Refund shows zero|") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/board.dom" lanes \
      "Refund shows zero|Answered: not a bug: the invoice shows what is left to pay|No bug: a refund is a credit note, and the invoice shows what is left to pay|a bug|!Waits for you") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$A.dom" now \
      "Answered: it ended with a report and nothing to merge|Closed|No bug: the code does what it should:|a refund is a credit note, and the invoice shows what is left to pay|billing/invoice.py:total|reproduced|investigation.md in the task directory") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$A.dom" feed \
      "The investigation found no bug|a refund is a credit note, and the invoice shows what is left to pay|billing/invoice.py:total · reproduced" "Answered|not a bug: the invoice shows what is left to pay") \
    && ! grep -q 'class="phase cur"' "$WORK/task-$A.dom" \
    && grep -q 'data-head="The builders · The investigation" data-sub="a builder reproduces the bug and finds its cause · investigation: bug · kind: bug, because the ask says the total is wrong today"' "$WORK/task-$A.dom" \
    && grep -q 'data-head="Investigation"' "$WORK/task-$A.dom" && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$A.dom" "Inv." "!Waits for you"); then
    pass "an answered task is in the lane of what ended with its kind and its investigation's answer; its own board says it ended with a report, names the call, the cause's place and the report, and draws the investigation as the builders' span"
  else
    fail "an answered task: ${why:-the span of the investigation, or a phase marked as current}"
  fi
  draw task-cart-total-wrong
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/board.dom" lanes "Cart total wrong|Investigating: a builder reproduces the bug and finds its cause|a bug") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-cart-total-wrong.dom" now "The investigator acts|Its investigator examines it, before any story|investigation: bug|!lead"); then
    pass "a task whose investigation runs says so on its card and on its own board, and names the investigator, not a lead"
  else
    fail "a task whose investigation runs: $why"
  fi
  # The project's own asker: the page says where the owner answers, by the settings' tools.ask.
  printf '%s\n' '[tools]' 'ask = "terminal"' > "$R/.lem/project.local.toml"
  board --no-open >/dev/null && draw board && cp "$WORK/board.dom" "$WORK/board-terminal.dom"
  printf '%s\n' '[tools]' 'ask = "my-asker"' > "$R/.lem/project.local.toml"
  board --no-open >/dev/null && draw board
  rm "$R/.lem/project.local.toml"
  board --no-open >/dev/null
  if why=$("$PY" -I -B -c "$LANES" "$WORK/board-terminal.dom" \
      "Waits for you=Gift note export|Lem asks you choice 7 in its session, as text in the conversation. Answer it there before its wait ends; then the lead takes the recommended action." \
      "Waits for you=Stories wait|Lem shows you the stories, with the personas’ read on top, in its session, as text in the conversation. Approve or change them there.") \
    && why=$("$PY" -I -B -c "$LANES" "$WORK/board.dom" \
      "Waits for you=Held choice|Lem asks you choice 1 with my-asker, the asker this project names. Answer it there: it waits for your word, with no end." \
      "Waits for you=Stories wait|Lem shows you the stories, with the personas’ read on top, with my-asker, the asker this project names. Approve or change them there."); then
    pass "where the owner answers follows the project's tools.ask: Lem's page, the conversation, or the developer's own asker by its name"
  else
    fail "the project's asker: $why"
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
  if [ -n "${LEM_BOARD_SHOTS:-}" ]; then
    mkdir -p "$LEM_BOARD_SHOTS"
    for page in board "task-$G" "task-$L"; do
      headless --hide-scrollbars --window-size=1400,2400 --virtual-time-budget=5000 --screenshot="$LEM_BOARD_SHOTS/$page.png" "file://$STATE/$page.html"
      printf 'shot %s\n' "$LEM_BOARD_SHOTS/$page.png"
    done
  fi
fi

if [ "$fails" -gt 0 ]; then
  printf '%d failed\n' "$fails"
  exit 1
fi
printf 'all passed\n'
