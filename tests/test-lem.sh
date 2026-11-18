#!/usr/bin/env bash
# Lem's scripts, in throwaway repositories. The checks are in blocks, `tests/lem-*.sh`, and each
# block runs alone with a folder of its own. This file starts every block at the same time, each
# within the time limit of tests/suites.sh, prints the output of each block in the order below and
# one line for each block, and says `all checks passed` only when each block passed (it exited 0,
# its ok and SKIP lines add up to the checks it collected, and it said `all checks passed` last)
# and the scripts left no __pycache__. One block alone: `bash tests/lem-settings.sh`.
set -uo pipefail
cd -P "$(dirname "$0")/.." || exit 1
# shellcheck source-path=SCRIPTDIR source=suites.sh
. tests/suites.sh

blocks=(lem-settings lem-machine lem-state lem-decisions lem-land-shop lem-land-local lem-land-review lem-land-backlog lem-land-github lem-land-guards lem-land-small lem-serial)
blocks+=(lem-naps)
blocks+=(lem-command)
blocks+=(lem-picker)
LOGS=$(mktemp -d)
pids=()
# A run that is stopped stops its blocks, and each block removes its own folder on the way out.
trap 'exit 143' TERM
trap 'exit 130' INT
trap 'kill ${pids[@]+"${pids[@]}"} 2>/dev/null; wait; rm -rf "$LOGS"' EXIT
started=$SECONDS
for block in "${blocks[@]}"; do
  within_limit "$block" bash "tests/$block.sh" > "$LOGS/$block.log" 2>&1 &
  pids+=("$!")
done

failed=""
lines=()
for index in "${!blocks[@]}"; do
  block=${blocks[$index]}
  wait "${pids[$index]}"
  code=$?
  printf '\n== %s\n' "$block"
  cat "$LOGS/$block.log"
  line=$(summary "$block" "$LOGS/$block.log" "$code" "$((SECONDS - started))" "tests/$block.sh")
  passed=$?
  lines+=("$line")
  # a block that ended before its last line, killed or cut off, has not passed whatever its exit says
  if [ "$passed" != 0 ] || [ "$(tail -n 1 "$LOGS/$block.log")" != "all checks passed" ]; then
    failed="$failed $block"
  fi
done
pids=()

printf '\n== the blocks (seconds since the start)\n'
printf '%s\n' "${lines[@]}"
printf '\n== the run\n'
if [ -d skills/lem/scripts/__pycache__ ]; then fail "the scripts left no __pycache__"; else pass "the scripts left no __pycache__"; fi
if [ -n "$failed" ]; then
  printf '\nthe block(s) that failed:%s\n' "$failed"
  exit 1
fi
if [ "$fails" -gt 0 ]; then
  printf '\n%s check(s) failed\n' "$fails"
  exit 1
fi
printf '\nall checks passed\n'
