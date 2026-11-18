#!/usr/bin/env bash
# The task picker (picker.py), offline: a stand-in for agtermctl on PATH records each call and
# answers the picker as the owner would, in a throwaway repository with tasks in several states.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

PICKER=$PWD/skills/lem/scripts/picker.py
BIN=$WORK/bin
CALLS=$WORK/calls
mkdir -p "$BIN"
# The stand-in: each call one line in CALLS; `pick` keeps the rows it read and answers with ANSWER and
# its exit status; `tree` names the session that pressed the chord; an overlay that opens names the board.
# shellcheck disable=SC2016  # the stand-in's own variables, read when it runs
printf '%s\n' '#!/bin/sh' 'echo "$*" >> "$CALLS"' \
  'case "$1" in' \
  '  pick) cat > "$CALLS.rows"; printf "%s\n" "$ANSWER"; exit "${ANSWER_EXIT:-0}" ;;' \
  '  tree) echo "{\"result\": {\"tree\": {\"workspaces\": [{\"sessions\": [{\"id\": \"S-LEM\"}]}]}}}" ;;' \
  '  session) [ "$2 $3" = "overlay open" ] && echo "{\"result\": {\"id\": \"S-BOARD\"}}" ;;' \
  'esac' 'exit 0' > "$BIN/agtermctl"
chmod +x "$BIN/agtermctl"
# chord REPO ANSWER [EXIT]: the picker as a keymap command starts it, from a session that sits in REPO
chord() {
  rm -f "$CALLS" "$CALLS.rows"
  env CALLS="$CALLS" ANSWER="$2" ANSWER_EXIT="${3:-0}" PATH="$BIN:$PATH" AGT_SESSION_PWD="$1" AGT_SESSION_ID=S-LEM AGT_SOCKET="$WORK/agterm.sock" AGT_WINDOW_ID=W1 AGT_PANE=left \
    "$PY" -B "$PICKER"
}
listed() { "$PY" -B "$PICKER" --repo "$1" --list; }

# A repository with tasks in every place of the list: a choice, criteria for his yes, a step of his, a pull request,
# two that build (one on the fast track), one queued, one landed today and one landed a month ago.
PK=$WORK/pick-repo
git init -q -b main "$PK" && ident "$PK" && commit "$PK" start && project --repo "$PK" init --base main >/dev/null
pk() { project --repo "$PK" "$@"; }
# backdate SLUG HOURS: the time of the task's newest state, written back by hand
backdate() { "$PY" -c 'import sys
from datetime import datetime, timedelta, timezone
path = sys.argv[1]
text = open(path).read()
when = (datetime.now(timezone.utc) - timedelta(hours=int(sys.argv[2]))).strftime("%Y-%m-%dT%H:%MZ")
open(path, "w").write(when + text[len(when):])' "$PK/.lem/state/tasks/$1/state.md" "$2"; }
pk task-dir old-landed --ask "Rename the old export." >/dev/null && pk state old-landed building "lead: builder" >/dev/null && pk state old-landed landed "main 1234567..89abcde" >/dev/null
backdate old-landed 720
pk task-dir fixed-total --ask "Show the total after a refund." >/dev/null && pk state fixed-total building "small change: one builder" >/dev/null && pk state fixed-total landed "main 89abcde..fedcba9" >/dev/null
pk task-dir queued-one --ask "Cache the product list." >/dev/null && pk state queued-one queued "it waits for a free place" >/dev/null
backdate fixed-total 26
pk task-dir big-export --ask "Export the gift notes, one column each." >/dev/null && pk state big-export building "lead: builder" "type: feat, because the export gets a column" >/dev/null
backdate big-export 2
pk task-dir typo-fix --ask "Fix the typo in the footer." >/dev/null && pk state typo-fix building "small change: one builder" "type: fix, because the footer is wrong" >/dev/null
pk task-dir proposed-one --ask "Sort the orders by date." >/dev/null && pk state proposed-one building "small change: one builder" >/dev/null
pk state proposed-one open "pull request https://github.com/acme/shop/pull/7" "green" >/dev/null
printf '%s\n' '{"proposed": "abc1234", "pr": {"number": 7, "url": "https://github.com/acme/shop/pull/7"}, "not_green": []}' > "$PK/.lem/state/tasks/proposed-one/landing.json"
pk task-dir his-step --ask "Move the reviewer to Codex." >/dev/null && pk state his-step held "the reviewer's pane waits for the owner's trust of the folder" >/dev/null
pk task-dir his-criteria --ask "Add the gift note to the slip." >/dev/null && pk state his-criteria held "the criteria wait for the owner" "type: feat, because the slip gets a line" >/dev/null
pk task-dir a-choice --ask "Put the note in the export." >/dev/null && pk state a-choice building "lead: builder" >/dev/null
"$PY" -B "$DECISIONS" --repo "$PK" ask a-choice "${CASE[@]}" --what "Where the note goes" --option "the last column" --option "after the price" --recommended "the last column" --why w --said s >/dev/null

rows=$(listed "$PK" 2>&1 || true)
order=$(field '[r["id"] for r in d]' <<<"$rows" 2>&1 || true)
if [ "$order" = "['a-choice', 'his-criteria', 'his-step', 'proposed-one', 'typo-fix', 'big-export', 'queued-one', 'fixed-total', ':all']" ]; then
  pass "the rows come in the order a developer reads them: a choice, criteria for his yes, a step of his and a pull request first, then what builds and the queue, then what landed lately; a task that landed a month ago has no row, and the board of all tasks is last"
else
  fail "the order of the rows: $order / $rows"
fi

said=$(field '"\n".join(r["label"] + " | " + r["subtitle"] for r in d)' <<<"$rows" 2>&1 || true)
want="Put the note in the export. | Choice 1 waits for you · standard track · now
Add the gift note to the slip. | Waits for you: the acceptance criteria · standard track · now
Move the reviewer to Codex. | Waits for you · now
Sort the orders by date. | Waits for the merge · fast track · now · #7 green
Fix the typo in the footer. | Building · fast track · now
Export the gift notes, one column each. | Building · standard track · 2h
Cache the product list. | Queued · now
Show the total after a refund. | Landed · fast track · 1d
All tasks | the board of every task · 9 tasks"
if [ "$said" = "$want" ]; then
  pass "each row is the ask in the owner's words, with the state in the board's words, the track, the age and the pull request's number with green or not green; the last row is the board of all tasks"
else
  fail "the words of the rows: $said"
fi

# The picker's words for a state are the board's: one list, held to board.html's STATUS.
same=$("$PY" -I - "$PWD" <<'PY'
import re, runpy, sys
from pathlib import Path
root = Path(sys.argv[1])
sys.dont_write_bytecode = True
words = runpy.run_path(str(root / "skills/lem/scripts/picker.py"), run_name="picker")["WORDS"]
page = (root / "skills/lem/assets/board.html").read_text(encoding="utf-8")
board = dict(re.findall(r"^  (\w+): \{actor: '[^']+', who: '[^']+', label: '([^']+)'", page, re.M))
print("same" if board and words == board else f"picker {words} / board {board}")
PY
)
if [ "$same" = same ]; then pass "the picker names each state in the words the board uses"; else fail "the picker's words and the board's: $same"; fi

# A pick opens the board of that task through lem board, which the stand-in records; the row for all tasks opens the board of all.
picked=$(chord "$PK" '{"result":"picked","id":"typo-fix","label":"Fix the typo in the footer.","index":4}' 2>&1; echo "exit $?")
picked_calls=$(cat "$CALLS")
shown=$(field '[r["id"] for r in d]' < "$CALLS.rows" 2>&1 || true)
chord "$PK" '{"result":"picked","id":":all","label":"All tasks","index":8}' >/dev/null 2>&1 || true
all_calls=$(cat "$CALLS")
if [ "$(tail -n 1 <<<"$picked")" = "exit 0" ] && [ "$shown" = "$order" ] \
  && grep -qxF "pick --prompt Open the board of a task --window W1 --socket $WORK/agterm.sock" <<<"$picked_calls" \
  && grep -qF "session overlay open --html $PK/.lem/state/task-typo-fix.html" <<<"$picked_calls" && grep -qF "session rename typo-fix board --target S-BOARD" <<<"$picked_calls" \
  && grep -qF "session select --target S-BOARD" <<<"$picked_calls" && [ -f "$PK/.lem/state/task-typo-fix.html" ] \
  && grep -qF "session overlay open --html $PK/.lem/state/board.html" <<<"$all_calls" && grep -qF "session rename Lem board · pick-repo --target S-BOARD" <<<"$all_calls"; then
  pass "a pick opens the board of that task as a companion and switches to it, the row for all tasks opens the board of all tasks, and the picker shows the rows of --list"
else
  fail "a pick: $picked / $picked_calls / $all_calls"
fi

# Escape: agterm answers cancelled with exit 2, and nothing opens.
escaped=$(chord "$PK" '{"result":"cancelled"}' 2 2>&1; echo "exit $?")
if [ "$escaped" = "exit 0" ] && ! grep -qF "overlay" "$CALLS" && [ "$(grep -c . "$CALLS")" = 1 ]; then
  pass "Escape opens nothing and says nothing"
else
  fail "Escape: $escaped / $(cat "$CALLS")"
fi

# No repository of Lem, no task yet, no agtermctl: each ends with exit 1 and one line that says why.
mkdir -p "$WORK/plain" && git init -q -b main "$WORK/plain"
EM=$WORK/empty-repo
git init -q -b main "$EM" && commit "$EM" start && project --repo "$EM" init --base main >/dev/null
no_lem=$(chord "$WORK/plain" '{}' 2>&1; echo "exit $?")
no_task=$(chord "$EM" '{}' 2>&1; echo "exit $?")
no_task_list=$(listed "$EM" 2>&1; echo "exit $?")
no_ctl=$(env PATH="/usr/bin:/bin" AGT_SESSION_PWD="$PK" AGT_SESSION_ID=S-LEM AGT_SOCKET="$WORK/agterm.sock" "$PY" -B "$PICKER" 2>&1; echo "exit $?")
if [ "$no_lem" = "lem picker: $WORK/plain is no repository of Lem: it has no .lem/project.toml; /lem init sets it up
exit 1" ] && [ "$no_task" = "lem picker: no task yet in $EM: \`/lem\` and a request opens one
exit 1" ] && [ "$no_task_list" = "$no_task" ] \
  && [ "$(tail -n 1 <<<"$no_ctl")" = "exit 1" ] && grep -qF "lem picker: agtermctl is not on the PATH of this command" <<<"$no_ctl" && [ ! -e "$CALLS" ]; then
  pass "a session outside a repository of Lem, a repository with no task yet and a machine with no agtermctl each end with exit 1 and one line that says why, and no picker opens"
else
  fail "the picker's refusals: $no_lem / $no_task / $no_task_list / $no_ctl"
fi

finish
