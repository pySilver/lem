#!/usr/bin/env bash
# The tests that two tasks cannot run at the same time (`checks.serial`): `lem project serial` runs one under
# the repository's one lock, the checks of a landing run them after `checks.commands` pass, and the check
# of the criteria runs a test of such a suite under the same lock. And `checks.setup`, which a new worktree
# of a task gets one time from `lem project worktree`, so that the checks there can run.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

AL=$WORK/alone
git init -q -b main "$AL" && ident "$AL"
project --repo "$AL" init --base main >/dev/null
git -C "$AL" add -A && git -C "$AL" commit -q -m "chore: start"
serial() { "$PY" -B "$PROJECT" --repo "$AL" serial "$@"; }
LOCK=$AL/.lem/state/alone.lock

# The exit status of the command is the exit of the run; a command of one word list runs as it is, one line runs in the shell.
code=$(status_of serial -- sh -c 'exit 7')
# shellcheck disable=SC2016  # the shell of the command expands it, not this one
said=$(serial -- 'echo "$((6 * 7))"')
refused=$(serial 2>&1 || true)
if [ "$code" = 7 ] && [ "$said" = 42 ] && grep -qF "serial takes the command to run" <<<"$refused" && [ "$(status_of serial)" = 1 ]; then
  pass "serial passes the command's exit status through, runs one quoted line in the shell, and refuses a call with no command"
else
  fail "serial's exit and its forms: $code / $said / $refused"
fi

# Two runs at one moment take turns: the second waits, says so on stderr, and starts when the first ended.
: > "$WORK/turns"
# The first holds the machine until the second says that it waits, so a loaded machine cannot start the second late.
serial -- sh -c "echo start-a >> '$WORK/turns'; until [ -e '$WORK/turns-release' ]; do sleep 0.1; done; echo end-a >> '$WORK/turns'" 2> "$WORK/a.err" &
first=$!
soon test -s "$WORK/turns"
serial -- sh -c "echo start-b >> '$WORK/turns'; echo end-b >> '$WORK/turns'" 2> "$WORK/b.err" &
second=$!
soon grep -qF "this one waits" "$WORK/b.err"
touch "$WORK/turns-release"
wait "$first"
wait "$second"
if [ "$(tr '\n' ' ' < "$WORK/turns")" = "start-a end-a start-b end-b " ] && grep -qF "another serial test holds the lock" "$WORK/b.err" \
  && grep -qF "start-a" "$WORK/b.err" && grep -qF "this one waits" "$WORK/b.err" && [ ! -s "$WORK/a.err" ]; then
  pass "two runs at one moment take turns: the second waits for the first, and says on stderr who holds the machine"
else
  fail "two runs at one moment: $(cat "$WORK/turns") / $(cat "$WORK/b.err")"
fi

# A run that is stopped ends its command's process group, what that command started too, and frees the lock.
"$PY" -B "$PROJECT" --repo "$AL" serial -- sh -c "sleep 60 & echo \$! > '$WORK/child'; wait" 2> "$WORK/stopped.err" &
held=$!
soon test -s "$WORK/child"
child=$(cat "$WORK/child")
kill -TERM "$held"
set +e; wait "$held"; stopped=$?; set -e
gone=no
soon sh -c "! kill -0 $child 2>/dev/null" && { kill -0 "$child" 2>/dev/null || gone=yes; }
started=$SECONDS
serial -- true
if [ "$stopped" = 143 ] && [ "$gone" = yes ] && [ $((SECONDS - started)) -lt 5 ]; then
  pass "a run that is stopped ends its command with everything it started, exits as the signal says, and the next run starts at once"
else
  fail "a stopped run: exit $stopped, child gone: $gone, next run after $((SECONDS - started)) s"
fi

# A lock file that a dead process left, and a holder killed with no chance to clean up: neither blocks the next run.
printf '%s\n' "pid 99999, since 2026-11-17T09:00:00Z, in /nowhere: make e2e" > "$LOCK"
started=$SECONDS
stale=$(serial -- echo through 2>&1)
"$PY" -B "$PROJECT" --repo "$AL" serial -- sh -c "echo \$\$ > '$WORK/orphan'; exec sleep 60" &
killed=$!
soon test -s "$WORK/orphan"
kill -KILL "$killed"
set +e; wait "$killed"; set -e
orphan=$(cat "$WORK/orphan")
after=$(serial -- echo through 2>&1)
kill "$orphan" 2>/dev/null || true
if [ "$stale" = through ] && [ "$after" = through ] && [ $((SECONDS - started)) -lt 10 ]; then
  pass "a stale lock file of a dead process does not block, nor does a holder that was killed with no chance to end its run: the lock is the kernel's, and it goes with the process"
else
  fail "a stale lock: $stale / $after / $((SECONDS - started)) s"
fi

# The checks of a landing: checks.commands first, then each checks.serial command under the lock, each with its output and its result.
small_task_in "$AL" alone-change a.txt one
printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' '[checks]' 'commands = ["echo 3 passed"]' "serial = [\"sh e2e.sh\"]" > "$AL/.lem/project.toml"
git -C "$AL" add -A && git -C "$AL" commit -q -m "chore: an e2e suite that needs the machine"
tree=$AL/.lem/worktrees/alone-change
# the e2e suite says whether it ran under the lock, by the holder line project.py writes there
printf '%s\n' "grep -q 'sh e2e.sh' '$LOCK' && echo 'e2e: 2 passed, alone' || { echo 'e2e: not alone'; exit 1; }" > "$tree/e2e.sh"
git -C "$tree" add -A && git -C "$tree" commit -q -m "test: the e2e suite"
git -C "$tree" rebase -q main
land --repo "$AL" start alone-change >/dev/null && land --repo "$AL" base alone-change >/dev/null
# a builder holds the machine until the gate's alone command waits for it, and then lets go: no fixed time,
# which a loaded machine outlasts before the checks reach that command
serial -- sh -c "until [ -e '$WORK/release' ]; do sleep 0.1; done" &
holder=$!
soon test -s "$LOCK"
land --repo "$AL" checks alone-change > "$WORK/gated.out" 2>&1 &
checking=$!
soon grep -qsF "another serial test holds the lock" "$AL/.lem/state/tasks/alone-change/gate/02.log"
touch "$WORK/release"
wait "$holder"
set +e; wait "$checking"; set -e
gated=$(cat "$WORK/gated.out")
if [ "$(field '[(c["command"], c["exit"], c["last"], c.get("alone", False)) for c in d["commands"]]' <<<"$gated" 2>&1)" = "[('echo 3 passed', 0, '3 passed', False), ('sh e2e.sh', 0, 'e2e: 2 passed, alone', True)]" ] \
  && grep -qF "another serial test holds the lock" "$AL/.lem/state/tasks/alone-change/gate/02.log" \
  && [ "$(grep -c '"event": "gate", "task": "alone-change"' "$AL/.lem/state/events.jsonl")" = 2 ] && grep -q '"event": "gate.start", "task": "alone-change", "tip": "[0-9a-f]*", "commands": 2' "$AL/.lem/state/events.jsonl"; then
  pass "the checks run each checks.serial command after checks.commands, under the one lock (waiting while a builder holds it), with its output in a file and its result logged"
else
  fail "the gate's alone commands: $gated"
fi
# The board knows how many commands one run of the checks has, and how many of them are serial.
"$PY" -B "$PWD/skills/lem/scripts/board.py" --repo "$AL" --no-open >/dev/null
if grep -qF '"gates": 2, "alone": 1' "$AL/.lem/state/meta.js"; then
  pass "the board's meta.js counts the serial commands in one run of the checks, and says how many there are"
else
  fail "the board's count of the checks: $(cat "$AL/.lem/state/meta.js")"
fi
# A red checks.commands leaves the serial commands out: they run only after the others passed.
printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' '[checks]' 'commands = ["echo 1 failed; exit 1"]' "serial = [\"sh e2e.sh\"]" > "$AL/.lem/project.toml"
red=$(land --repo "$AL" checks alone-change 2>/dev/null || true)
if [ "$(field '[(c["command"], c["exit"]) for c in d["commands"]]' <<<"$red" 2>&1)" = "[('echo 1 failed; exit 1', 1)]" ]; then
  pass "a red gate command leaves the serial commands out: they run only after checks.commands pass"
else
  fail "a red gate before the alone commands: $red"
fi

# The check of the criteria runs a test of a serial suite under the lock, and any other test bare.
printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' '[checks]' 'commands = ["true"]' "serial = [\"sh tests/e2e\"]" > "$AL/.lem/project.toml"
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
  pass "the check of the criteria runs a test whose command starts with a checks.serial command under the one lock, on the branch and on the base commit"
else
  fail "a criterion's test of a serial suite: $held"
fi

# A new worktree of a task gets checks.setup one time, so that the checks there can run: a task on the fast track whose
# builder runs no test reaches its checks with what the setup installs. A setup that fails is refused with its exit.
SU=$WORK/setup-repo
git init -q -b main "$SU" && ident "$SU"
mkdir -p "$SU/.lem"
printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' '[checks]' 'commands = ["test -f deps/ok && echo 1 passed"]' 'setup = ["mkdir -p deps && touch deps/ok && echo installed"]' > "$SU/.lem/project.toml"
printf '%s\n' 'deps/' > "$SU/.gitignore" && echo readme > "$SU/README.md"
git -C "$SU" add -A && git -C "$SU" commit -q -m "chore: a project whose tests need what the setup installs"
directory=$(project --repo "$SU" task-dir readme-fix --ask "Fix the README.")
printf '%s\n' '## Acceptance criteria' '' 'Size: small, because the request is one sentence.' '' '1. The README says hello.' > "$directory/criteria.md"
"$PY" -B "$CRITERIA" --repo "$SU" approve readme-fix --file "$directory/criteria.md" --small >/dev/null
printf '%s\n' '   - no test: the change keeps behavior; the suite holds it' >> "$directory/criteria.md"
made=$(project --repo "$SU" worktree readme-fix docs/readme-fix | field '(d["made"], d["setup"])' 2>&1 || true)
tree=$(project --repo "$SU" worktree-dir readme-fix)
echo hello > "$tree/README.md" && git -C "$tree" commit -q -am "docs: hello"
project --repo "$tree" state readme-fix ready "the small change is built" >/dev/null
land --repo "$SU" start readme-fix >/dev/null && land --repo "$SU" base readme-fix >/dev/null
setup_checks=$(land --repo "$SU" checks readme-fix 2>&1 | field '(d["green"], [(c["command"], c["exit"]) for c in d["commands"]])' 2>&1 || true)
again=$(project --repo "$SU" worktree readme-fix docs/readme-fix | field '(d["made"], "setup" in d)' 2>&1 || true)
printf '%s\n' '[branch]' 'base = "main"' '[checks]' 'setup = ["echo half; exit 4"]' > "$SU/.lem/project.toml"
project --repo "$SU" task-dir other-fix >/dev/null
failed=$(project --repo "$SU" worktree other-fix docs/other-fix 2>&1 || true)
failed_code=$(status_of project --repo "$SU" worktree other-fix docs/other-fix)
# shellcheck disable=SC2016  # the backticks are the message's own
if [ "$made" = "(True, [{'command': 'mkdir -p deps && touch deps/ok && echo installed', 'exit': 0}])" ] && grep -qx installed "$directory/setup.log" \
  && [ "$setup_checks" = "(True, [('test -f deps/ok && echo 1 passed', 0)])" ] && [ "$again" = "(False, False)" ] \
  && grep -qF '`echo half; exit 4` of checks.setup failed in the new worktree' <<<"$failed" && grep -qF "(exit 4; its output is in $SU/.lem/state/tasks/other-fix/setup.log)" <<<"$failed" \
  && [ "$failed_code" = 0 ] && [ -d "$SU/.lem/worktrees/other-fix" ]; then
  pass "a task's new worktree gets checks.setup one time, with its output in the task directory, so that the checks of a change that runs no test pass there; a worktree that exists gets none again, and a setup that fails is refused with its exit while the worktree stays"
else
  fail "checks.setup in a new worktree: $made / $setup_checks / $again / $failed / $failed_code"
fi

finish
