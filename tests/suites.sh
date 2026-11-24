# shellcheck shell=bash
# What tests/all.sh and tests/test-lem.sh share: the time limit of one suite, and the line that says
# whether a suite passed. A suite passed when it exited 0, printed no FAIL line, and its ok and SKIP
# lines add up to the checks it collected (tests/checks.sh).
# LEM_TEST_LIMIT=SECONDS is how long one suite may run before it is stopped and fails.

# 30 minutes: the slowest block, lem-land-github, took 1,005 s alone at a load of 14 before its
# scripts called their siblings in one process (cfc4831, 2026-11-18); a guess with room for a
# loaded machine, not a measure of one.
SUITE_LIMIT=${LEM_TEST_LIMIT:-1800}
# shellcheck source-path=SCRIPTDIR source=checks.sh
. "$(dirname "${BASH_SOURCE[0]}")/checks.sh"
# shellcheck source-path=SCRIPTDIR source=python.sh
. "$(dirname "${BASH_SOURCE[0]}")/python.sh"

# within_limit NAME COMMAND...: COMMAND, stopped and failed by name when it runs over the limit. A
# runner calls it in a job of its own, and a TERM or an INT to that job goes on to the suite, whose
# EXIT trap removes its folder: a run that is stopped leaves no suite running.
within_limit() {
  local name=$1 child code
  shift
  "$PY" -I -B "$(dirname "${BASH_SOURCE[0]}")/limit.py" "$SUITE_LIMIT" "$name" -- "$@" &
  child=$!
  trap 'kill "$child" 2>/dev/null' TERM INT
  wait "$child"
  code=$?
  # a signal ends the wait before the suite ends on it: the exit is the suite's, once it has
  if kill -0 "$child" 2>/dev/null; then
    wait "$child"
    code=$?
  fi
  return "$code"
}

# summary NAME LOG EXIT SECONDS [FILE]: the suite's line, `ok|FAIL NAME N ok N FAIL N SKIP exit N Ns`,
# and below it the count when the lines do not add up; returns 1 for a suite that failed. A suite
# that printed no `collected` line is counted from FILE, its source.
summary() {
  local name=$1 log=$2 code=$3 seconds=$4 file=${5:-} oks bad skips collected from="" verdict=ok
  oks=$(grep -c '^ok ' "$log")
  bad=$(grep -c '^FAIL ' "$log")
  skips=$(grep -c '^SKIP ' "$log")
  collected=$(awk '/^collected [0-9]+$/ { n += $2; seen = 1 } END { if (seen) print n }' "$log")
  if [ -z "$collected" ] && [ -n "$file" ]; then
    collected=$(count_checks "$file")
    from=", counted from $file: the suite prints no count of its own"
  fi
  if [ "$code" != 0 ] || [ "$bad" != 0 ] || [ "$((oks + skips))" != "${collected:-none}" ]; then verdict=FAIL; fi
  printf '%-4s %-16s %4d ok  %3d FAIL  %2d SKIP  exit %-3s %4ds\n' "$verdict" "$name" "$oks" "$bad" "$skips" "$code" "$seconds"
  if [ "$((oks + skips))" != "${collected:-none}" ]; then
    printf '     %s: %d ok and %d SKIP of %s checks collected%s\n' "$name" "$oks" "$skips" "${collected:-no}" "$from"
  fi
  [ "$verdict" = ok ]
}
