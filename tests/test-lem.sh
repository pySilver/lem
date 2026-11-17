#!/usr/bin/env bash
# Lem's scripts, in throwaway repositories. The checks are in blocks, `tests/lem-*.sh`, and each
# block runs alone with a folder of its own. This file starts every block at the same time, prints
# the output of each block in the order below, and says `all checks passed` only when each block
# said it and the scripts left no __pycache__. One block alone: `bash tests/lem-settings.sh`.
set -uo pipefail
cd -P "$(dirname "$0")/.." || exit 1

blocks=(lem-settings lem-machine lem-state lem-old-tasks lem-decisions lem-land-shop lem-land-local lem-land-review lem-land-backlog lem-land-github lem-land-guards lem-land-small lem-alone)
LOGS=$(mktemp -d)
pids=()
# A run that is stopped stops its blocks, and each block removes its own folder on the way out.
trap 'exit 143' TERM
trap 'exit 130' INT
trap 'kill ${pids[@]+"${pids[@]}"} 2>/dev/null; wait; rm -rf "$LOGS"' EXIT
for block in "${blocks[@]}"; do
  bash "tests/$block.sh" > "$LOGS/$block.log" 2>&1 &
  pids+=("$!")
done

fails=0
pass() { printf 'ok   %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1"; fails=$((fails + 1)); }
failed=""
for index in "${!blocks[@]}"; do
  block=${blocks[$index]}
  wait "${pids[$index]}"
  code=$?
  printf '\n== %s\n' "$block"
  cat "$LOGS/$block.log"
  # a block that ended before its last line, killed or cut off, has not passed whatever its exit says
  if [ "$code" != 0 ] || [ "$(tail -n 1 "$LOGS/$block.log")" != "all checks passed" ]; then
    failed="$failed $block"
  fi
done
pids=()

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
