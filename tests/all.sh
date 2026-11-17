#!/usr/bin/env bash
# Every check of this repository at the same time: the blocks of Lem's scripts, the board, the
# gate and the panel, lem-ask, the experts, and ShellCheck. Each suite writes a log of its own; at
# the end one line for each suite gives its count of `ok` and `FAIL` and its time, and the log of
# each suite that failed follows. The exit is 0 only when every suite passed.
# LEM_TEST_LOGS=DIR keeps the logs in DIR; without it they go with the run.
set -uo pipefail
cd -P "$(dirname "$0")/.." || exit 1

suites=(lem-settings lem-machine lem-decisions lem-land-shop lem-land-local lem-land-backlog lem-land-github lem-land-guards lem-land-small
  test-board test-gate-panel test-ask test-ask-expert shellcheck)
if [ -n "${LEM_TEST_LOGS:-}" ]; then
  LOGS=$LEM_TEST_LOGS
  mkdir -p "$LOGS" || exit 1
  keep=yes
else
  LOGS=$(mktemp -d)
  keep=""
fi
pids=()
trap 'exit 143' TERM
trap 'exit 130' INT
trap 'kill ${pids[@]+"${pids[@]}"} 2>/dev/null; wait; [ -n "$keep" ] || rm -rf "$LOGS"' EXIT

# run NAME COMMAND...: the suite's output into its log, then its exit and its seconds
run() {
  local name=$1 started=$SECONDS code
  shift
  "$@" > "$LOGS/$name.log" 2>&1
  code=$?
  echo "$code $((SECONDS - started))" > "$LOGS/$name.exit"
}
started=$SECONDS
for suite in "${suites[@]}"; do
  if [ "$suite" = shellcheck ]; then
    run shellcheck shellcheck tests/*.sh &
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
  oks=$(grep -c '^ok ' "$LOGS/$suite.log")
  bad=$(grep -c '^FAIL ' "$LOGS/$suite.log")
  skips=$(grep -c '^SKIP ' "$LOGS/$suite.log")
  verdict=ok
  # a suite whose own checks all passed and that still exited with another code failed all the same
  if [ "$code" != 0 ] || [ "$bad" != 0 ]; then verdict=FAIL; failed+=("$suite"); fi
  printf '%-4s %-16s %4d ok  %3d FAIL  %2d SKIP  exit %-3s %4ds\n' "$verdict" "$suite" "$oks" "$bad" "$skips" "$code" "$seconds"
done
# what no suite checks alone: the scripts of every suite, run at one time, left no cache
caches=$(find skills bin -name __pycache__ -type d 2>/dev/null)
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
