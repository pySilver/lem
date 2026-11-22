#!/usr/bin/env bash
# Every check of this repository at the same time: the unit level (tests/unit), the blocks of Lem's
# scripts, the board server among them, the gate and the panel, lem-ask, the experts, the page on GitHub Pages, ShellCheck
# and the map of tests/pick.py. Each suite writes a log of its own and runs within a time limit
# (tests/suites.sh). At the end one line for each suite gives its count of `ok`, `FAIL` and `SKIP`,
# its exit and its time, and the log of each suite that failed follows. A suite passes only when its
# ok and SKIP lines add up to the checks it collected. The exit is 0 only when every suite passed.
# LEM_TEST_LOGS=DIR keeps the logs in DIR; without it they go with the run.
set -uo pipefail
cd -P "$(dirname "$0")/.." || exit 1
# shellcheck source-path=SCRIPTDIR source=suites.sh
. tests/suites.sh

suites=(lem-settings lem-machine lem-state lem-decisions lem-land-shop lem-land-local lem-land-review lem-land-backlog lem-land-github lem-land-guards lem-land-small lem-serial
  test-gate-panel test-ask test-ask-expert shellcheck pick)
suites+=(lem-naps)
suites+=(lem-command)
suites+=(lem-picker)
suites+=(lem-session)
suites+=(lem-serve)
suites+=(lem-board-keys)
suites+=(lem-board-act)
suites+=(lem-peers)
suites+=(unit)
suites+=(test-site)
if [ -n "${LEM_TEST_LOGS:-}" ]; then
  LOGS=$LEM_TEST_LOGS
  mkdir -p "$LOGS" || exit 1
  keep=yes
else
  LOGS=$(mktemp -d)
  keep=""
fi
# The owner's status (`lem_state.owner_mark`) of this run, for a suite with no WORK of its own, which
# then exports its own: no suite reads or writes the home directory's.
MARKS=$(mktemp -d) || exit 1
export XDG_CONFIG_HOME="$MARKS/config"
# No board that a suite opens starts a board server (`serve.py`), which would outlive the run.
export LEM_SERVE=off
pids=()
trap 'exit 143' TERM
trap 'exit 130' INT
trap 'kill ${pids[@]+"${pids[@]}"} 2>/dev/null; wait; rm -rf "$MARKS"; [ -n "$keep" ] || rm -rf "$LOGS"' EXIT

# run NAME COMMAND...: the suite's output into its log, then its exit and its seconds
run() {
  local name=$1 started=$SECONDS code
  shift
  within_limit "$name" "$@" > "$LOGS/$name.log" 2>&1
  code=$?
  echo "$code $((SECONDS - started))" > "$LOGS/$name.exit"
}
started=$SECONDS
for suite in "${suites[@]}"; do
  if [ "$suite" = pick ]; then
    run pick python3 -I -B tests/pick.py --check &
  elif [ "$suite" = unit ]; then
    run unit python3 -I -B tests/unit &
  else
    run "$suite" bash "tests/$suite.sh" &
  fi
  pids+=("$!")
done
wait
pids=()

failed=()
for suite in "${suites[@]}"; do
  read -r code seconds < "$LOGS/$suite.exit"
  source_file=tests/$suite.sh
  [ -f "$source_file" ] || source_file=""
  summary "$suite" "$LOGS/$suite.log" "$code" "$seconds" "$source_file" || failed+=("$suite")
done
# what no suite checks alone: the scripts of every suite, run at one time, left no cache
caches=$(find skills bin tests -name __pycache__ -type d 2>/dev/null)
if [ -n "$caches" ]; then
  printf 'FAIL the scripts left a __pycache__: %s\n' "$caches"
  failed+=(__pycache__)
fi
printf '%ds in all\n' "$((SECONDS - started))"
if [ "${#failed[@]}" -gt 0 ]; then
  for suite in "${failed[@]}"; do
    [ -f "$LOGS/$suite.log" ] || continue
    printf '\n== %s\n' "$suite"
    cat "$LOGS/$suite.log"
  done
  printf '\nfailed: %s\n' "${failed[*]}"
  exit 1
fi
printf 'all suites passed\n'
