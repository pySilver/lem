#!/usr/bin/env bash
# Every check of this repository at the same time: the unit level (tests/unit), the blocks of Lem's
# scripts, the board server among them, the gate and the panel, lem-ask, the experts, the page on GitHub Pages, ShellCheck,
# the lint of the Python and the JavaScript and the map of tests/pick.py. Each suite writes a log of its own and runs within a time limit
# (tests/suites.sh). At the end one line for each suite gives its count of `ok`, `FAIL` and `SKIP`,
# its exit and its time, and the log of each suite that failed follows. A suite passes only when its
# ok and SKIP lines add up to the checks it collected. The exit is 0 only when every suite passed.
# Every suite runs on the checkout's .venv, which `uv sync` makes (tests/python.sh).
# LEM_TEST_LOGS=DIR keeps the logs in DIR; without it they go with the run.
#
# --installed: the journeys, each lem-* and test-* suite but test-site, against an app installed outside the
# checkout: the one LEM_UNDER_TEST names, or else a wheel uv builds from this checkout, installed into a folder of the
# run's own that goes with it. The suites that read the checkout itself (unit, lint, pick, shellcheck, test-site) are
# the checkout mode's, and the summary names the install it drove.
set -uo pipefail
cd -P "$(dirname "$0")/.." || exit 1
given=${LEM_UNDER_TEST:-}
installed=""
case ${1:-} in
  --installed) installed=yes ;;
  "") ;;
  *) printf 'usage: bash tests/all.sh [--installed]\n'; exit 1 ;;
esac
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
suites+=(lint)
# the suites that read the checkout itself, which the installed mode leaves to the checkout mode
CHECKOUT_SUITES=(shellcheck pick unit test-site lint)
if [ -n "$installed" ]; then
  journeys=()
  for suite in "${suites[@]}"; do
    case " ${CHECKOUT_SUITES[*]} " in *" $suite "*) ;; *) journeys+=("$suite") ;; esac
  done
  suites=("${journeys[@]}")
fi
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
APP=""
trap 'kill ${pids[@]+"${pids[@]}"} 2>/dev/null; wait; rm -rf "$MARKS" ${APP:+"$APP"}; [ -n "$keep" ] || rm -rf "$LOGS"' EXIT

if [ -n "$installed" ]; then
  if [ -n "$given" ] && ! in_checkout; then
    drove="$LEM_UNDER_TEST, as LEM_UNDER_TEST names it"
  else
    APP=$(mktemp -d) || exit 1
    # the wheel, built as an install builds it (the sdist, then the wheel from it), offline when uv's cache holds the
    # build backend
    if ! { uv build --offline -q --out-dir "$APP/dist" > "$APP/build.out" 2>&1 || uv build -q --out-dir "$APP/dist" > "$APP/build.out" 2>&1; } \
      || ! uv venv -q --python "$PY" "$APP/app" >> "$APP/build.out" 2>&1 \
      || ! uv pip install -q --offline --no-deps --python "$APP/app/bin/python" "$APP"/dist/lem-*.whl >> "$APP/build.out" 2>&1; then
      printf 'FAIL the wheel of this checkout did not build or install: %s\n' "$(tail -n 5 "$APP/build.out")"
      exit 1
    fi
    export LEM_UNDER_TEST=$APP/app/bin/lem
    LEM=$LEM_UNDER_TEST
    drove="$LEM_UNDER_TEST, installed from $(basename "$APP"/dist/lem-*.whl), built from this checkout"
  fi
  said=$("$LEM" version 2>&1) || { printf 'FAIL %s does not answer lem version: %s\n' "$LEM" "$said"; exit 1; }
  drove="$drove; lem version: $(tr -s ' \n' ' ' <<<"$said")"
  printf 'installed: %s\n' "$drove"
fi

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
    run pick "$PY" -I -B tests/pick.py --check &
  elif [ "$suite" = unit ]; then
    run unit "$PY" -I -B tests/unit &
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
caches=$(find src skills tests -name __pycache__ -type d 2>/dev/null)
if [ -n "$caches" ]; then
  printf 'FAIL the scripts left a __pycache__: %s\n' "$caches"
  failed+=(__pycache__)
fi
printf '%ds in all\n' "$((SECONDS - started))"
if [ -n "$installed" ]; then
  printf 'the journeys ran against %s\nnot run here, since they read the checkout itself: %s\n' "$drove" "${CHECKOUT_SUITES[*]}"
fi
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
