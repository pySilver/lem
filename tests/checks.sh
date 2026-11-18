# shellcheck shell=bash
# How a suite counts its checks. A suite sources this file, says how many checks it holds with
# `collected`, prints one line for each check (`ok   TEXT`, `FAIL TEXT` or `SKIP TEXT`) and ends with
# `results_add_up`. The runners (tests/all.sh, tests/test-lem.sh) pass a suite only when its ok and
# SKIP lines add up to what it collected: a check that never ran, a section skipped in one line, or a
# suite cut off in the middle is a failure, never a quiet green.

# A check is one call of `pass "..."` in the suite's file, at the start of a line or after then,
# else, ;, &&, || or {. The count of a file is the number of such calls in it.
CHECK_SITE='(^[[:space:]]*|then[[:space:]]+|else[[:space:]]+|;[[:space:]]*|&&[[:space:]]*|\|\|[[:space:]]*|\{[[:space:]]*)pass "'
count_checks() { grep -cE "$CHECK_SITE" "$1" || true; }
# The suite's own file. Every suite lives in tests/ and sources this file from the root of the
# checkout, so the name holds wherever the suite was started from.
SUITE_FILE=$PWD/tests/${0##*/}

fails=0
oks=0
skips=0
CHECKS=0
pass() { printf 'ok   %s\n' "$1"; oks=$((oks + 1)); }
fail() { printf 'FAIL %s\n' "$1"; fails=$((fails + 1)); }
# skip TEXT: a check that did not run, with why, in TEXT
skip() { printf 'SKIP %s\n' "$1"; skips=$((skips + 1)); }

# collected [N]: the suite holds N more checks; with no N, every call of pass in its file. A suite
# whose checks run in a loop says the count of each loop itself, so it may call this more than once,
# and a runner adds the lines up.
collected() {
  local more=${1:-$(count_checks "$SUITE_FILE")}
  CHECKS=$((CHECKS + more))
  printf 'collected %s\n' "$more"
}

# the text each check of a piece of a suite passes with, one to a line, from the suite's own file
check_texts() { grep -E "$CHECK_SITE" | sed -E 's/.*pass "(([^"\\]|\\.)*)".*/\1/'; }

# skip_rest WHY: one SKIP line for each check of the suite's file after the line that calls this, for a
# suite that stops early (a commit it needs is not in this clone)
skip_rest() {
  local text
  while IFS= read -r text; do skip "$text: $1"; done < <(tail -n +"$((BASH_LINENO[0] + 1))" "$SUITE_FILE" | check_texts)
}

# skip_function NAME WHY: one SKIP line for each check of the shell function NAME, for a section that
# cannot run here (no Chrome)
skip_function() {
  local text
  while IFS= read -r text; do skip "$text: $2"; done < <(declare -f "$1" | check_texts)
}

# results_add_up: a FAIL when the lines the suite printed do not add up to what it collected
results_add_up() {
  local ran=$((oks + skips + fails))
  if [ "$ran" != "$CHECKS" ]; then
    fail "the suite printed $ran results for the $CHECKS checks it collected: a check printed nothing, or printed twice"
  fi
}

# The last command that failed, and a FAIL when a suite ends before its end: `set -e` stopped it,
# or a signal did. A suite runs `stopped` from its EXIT trap and sets `finished` at its end. The
# line goes to the suite's own stdout, kept as fd 7: a trap runs with the output of the command
# that failed, which may have gone to /dev/null.
finished=""
failed_last="none"
exec 7>&1
trap 'failed_last="line $LINENO: $BASH_COMMAND"' ERR
stopped() {
  local code=$?
  if [ -z "$finished" ]; then
    printf 'FAIL the suite stopped before its end, with exit %s, after %s of its %s checks; the last command that failed: %s\n' \
      "$code" "$((oks + skips + fails))" "$CHECKS" "$failed_last" >&7
  fi
}
