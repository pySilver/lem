#!/usr/bin/env bash
# The commands that need the machine to themselves (`gate.alone`): `project.py alone` runs one under
# the repository's one lock, the checks of a landing run them after `gate.commands` pass, and the check
# of the criteria runs a test of such a suite under the same lock.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

AL=$WORK/alone
git init -q -b main "$AL" && ident "$AL"
project --repo "$AL" init --base main >/dev/null
git -C "$AL" add -A && git -C "$AL" commit -q -m "chore: start"
alone() { "$PY" -B "$PROJECT" --repo "$AL" alone "$@"; }
LOCK=$AL/.lem/state/alone.lock

# The exit status of the command is the exit of the run; a command of one word list runs as it is, one line runs in the shell.
code=$(status_of alone -- sh -c 'exit 7')
# shellcheck disable=SC2016  # the shell of the command expands it, not this one
said=$(alone -- 'echo "$((6 * 7))"')
refused=$(alone 2>&1 || true)
if [ "$code" = 7 ] && [ "$said" = 42 ] && grep -qF "alone takes the command to run" <<<"$refused" && [ "$(status_of alone)" = 1 ]; then
  pass "alone passes the command's exit status through, runs one quoted line in the shell, and refuses a call with no command"
else
  fail "alone's exit and its forms: $code / $said / $refused"
fi

# Two runs at one moment take turns: the second waits, says so on stderr, and starts when the first ended.
: > "$WORK/turns"
alone -- sh -c "echo start-a >> '$WORK/turns'; sleep 2; echo end-a >> '$WORK/turns'" 2> "$WORK/a.err" &
first=$!
soon test -s "$WORK/turns"
alone -- sh -c "echo start-b >> '$WORK/turns'; echo end-b >> '$WORK/turns'" 2> "$WORK/b.err"
wait "$first"
if [ "$(tr '\n' ' ' < "$WORK/turns")" = "start-a end-a start-b end-b " ] && grep -qF "the machine is held by a command that needs it alone" "$WORK/b.err" \
  && grep -qF "start-a" "$WORK/b.err" && grep -qF "this one waits" "$WORK/b.err" && [ ! -s "$WORK/a.err" ]; then
  pass "two runs at one moment take turns: the second waits for the first, and says on stderr who holds the machine"
else
  fail "two runs at one moment: $(cat "$WORK/turns") / $(cat "$WORK/b.err")"
fi

# A run that is stopped ends its command's process group, what that command started too, and frees the lock.
"$PY" -B "$PROJECT" --repo "$AL" alone -- sh -c "sleep 60 & echo \$! > '$WORK/child'; wait" 2> "$WORK/stopped.err" &
held=$!
soon test -s "$WORK/child"
child=$(cat "$WORK/child")
kill -TERM "$held"
set +e; wait "$held"; stopped=$?; set -e
gone=no
soon sh -c "! kill -0 $child 2>/dev/null" && { kill -0 "$child" 2>/dev/null || gone=yes; }
started=$SECONDS
alone -- true
if [ "$stopped" = 143 ] && [ "$gone" = yes ] && [ $((SECONDS - started)) -lt 5 ]; then
  pass "a run that is stopped ends its command with everything it started, exits as the signal says, and the next run starts at once"
else
  fail "a stopped run: exit $stopped, child gone: $gone, next run after $((SECONDS - started)) s"
fi

# A lock file that a dead process left, and a holder killed with no chance to clean up: neither blocks the next run.
printf '%s\n' "pid 99999, since 2026-11-17T09:00:00Z, in /nowhere: make e2e" > "$LOCK"
started=$SECONDS
stale=$(alone -- echo through 2>&1)
"$PY" -B "$PROJECT" --repo "$AL" alone -- sh -c "echo \$\$ > '$WORK/orphan'; exec sleep 60" &
killed=$!
soon test -s "$WORK/orphan"
kill -KILL "$killed"
set +e; wait "$killed"; set -e
orphan=$(cat "$WORK/orphan")
after=$(alone -- echo through 2>&1)
kill "$orphan" 2>/dev/null || true
if [ "$stale" = through ] && [ "$after" = through ] && [ $((SECONDS - started)) -lt 10 ]; then
  pass "a stale lock file of a dead process does not block, nor does a holder that was killed with no chance to end its run: the lock is the kernel's, and it goes with the process"
else
  fail "a stale lock: $stale / $after / $((SECONDS - started)) s"
fi

# The checks of a landing: gate.commands first, then each gate.alone command under the lock, each with its output and its result.
small_task_in "$AL" alone-change a.txt one
printf '%s\n' '[branch]' 'base = "main"' '[gate]' 'commands = ["echo 3 passed"]' "alone = [\"sh e2e.sh\"]" > "$AL/.lem/project.toml"
git -C "$AL" add -A && git -C "$AL" commit -q -m "chore: an e2e suite that needs the machine"
tree=$AL/.lem/worktrees/alone-change
# the e2e suite says whether it ran under the lock, by the holder line project.py writes there
printf '%s\n' "grep -q 'sh e2e.sh' '$LOCK' && echo 'e2e: 2 passed, alone' || { echo 'e2e: not alone'; exit 1; }" > "$tree/e2e.sh"
git -C "$tree" add -A && git -C "$tree" commit -q -m "test: the e2e suite"
git -C "$tree" rebase -q main
land --repo "$AL" start alone-change >/dev/null && land --repo "$AL" base alone-change >/dev/null
# a builder holds the machine for a moment: the gate's alone command waits for it
alone -- sleep 6 &
holder=$!
soon test -s "$LOCK"
gated=$(land --repo "$AL" gate alone-change 2>&1 || true)
wait "$holder"
if [ "$(field '[(c["command"], c["exit"], c["last"], c.get("alone", False)) for c in d["commands"]]' <<<"$gated" 2>&1)" = "[('echo 3 passed', 0, '3 passed', False), ('sh e2e.sh', 0, 'e2e: 2 passed, alone', True)]" ] \
  && grep -qF "the machine is held by a command that needs it alone" "$AL/.lem/state/tasks/alone-change/gate/02.log" \
  && [ "$(grep -c '"event": "gate", "task": "alone-change"' "$AL/.lem/state/events.jsonl")" = 2 ] && grep -q '"event": "gate.start", "task": "alone-change", "tip": "[0-9a-f]*", "commands": 2' "$AL/.lem/state/events.jsonl"; then
  pass "the checks run each gate.alone command after gate.commands, under the one lock (waiting while a builder holds it), with its output in a file and its result logged"
else
  fail "the gate's alone commands: $gated"
fi
# The board knows how many commands one run of the checks has, and how many of them run alone.
"$PY" -B "$PWD/skills/lem/scripts/board.py" --repo "$AL" --no-open >/dev/null
if grep -qF '"gates": 2, "alone": 1' "$AL/.lem/state/meta.js"; then
  pass "the board's meta.js counts the alone commands in one run of the checks, and says how many there are"
else
  fail "the board's count of the checks: $(cat "$AL/.lem/state/meta.js")"
fi
# A red gate.commands leaves the alone commands out: they run only after the others passed.
printf '%s\n' '[branch]' 'base = "main"' '[gate]' 'commands = ["echo 1 failed; exit 1"]' "alone = [\"sh e2e.sh\"]" > "$AL/.lem/project.toml"
red=$(land --repo "$AL" gate alone-change 2>/dev/null || true)
if [ "$(field '[(c["command"], c["exit"]) for c in d["commands"]]' <<<"$red" 2>&1)" = "[('echo 1 failed; exit 1', 1)]" ]; then
  pass "a red gate command leaves the alone commands out: they run only after gate.commands pass"
else
  fail "a red gate before the alone commands: $red"
fi

# The check of the criteria runs a test of an alone suite under the lock, and any other test bare.
printf '%s\n' '[branch]' 'base = "main"' '[gate]' 'commands = ["true"]' "alone = [\"sh tests/e2e\"]" > "$AL/.lem/project.toml"
git -C "$AL" add -A && git -C "$AL" commit -q -m "chore: the e2e suite is a folder of tests"
small_task_in "$AL" alone-criterion b.txt two
tree=$AL/.lem/worktrees/alone-criterion
directory=$AL/.lem/state/tasks/alone-criterion
mkdir -p "$tree/tests/e2e"
printf '%s\n' "grep -q 'sh tests/e2e' '$LOCK' || exit 3" 'grep -qx two b.txt' > "$tree/tests/e2e/b.sh"
git -C "$tree" add -A && git -C "$tree" commit -q -m "test: the criterion in the e2e suite"
# shellcheck disable=SC2016  # the backticks are the criterion line's own
"$PY" -I -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("`sh tests/alone-criterion.sh` in `tests/alone-criterion.sh`", "`sh tests/e2e/b.sh` in `tests/e2e/b.sh`"))' "$directory/criteria.md"
held=$("$PY" -B "$CRITERIA" --repo "$AL" red alone-criterion 2>&1 || true)
if [ "$(field '(d["ok"], [(t["command"], t["on_branch"], t["on_base"]) for t in d["tests"]])' <<<"$held" 2>&1)" = "(True, [('sh tests/e2e/b.sh', 0, 2)])" ]; then
  pass "the check of the criteria runs a test whose command starts with a gate.alone command under the one lock, on the branch and on the base commit"
else
  fail "a criterion's test of an alone suite: $held"
fi

finish
