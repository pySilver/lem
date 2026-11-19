#!/usr/bin/env bash
# ShellCheck over the suites, one check for each file: `bash tests/shellcheck.sh` for every
# tests/*.sh, or `bash tests/shellcheck.sh FILE...` for the files named. One run of shellcheck
# reads them all and follows each file a suite sources (`-x`), so a file named alone reads as it
# does in the run over all; a file it says anything about fails, and what it said follows.
set -uo pipefail
cd -P "$(dirname "$0")/.." || exit 1
# shellcheck source-path=SCRIPTDIR source=checks.sh
. tests/checks.sh

if [ "$#" -gt 0 ]; then files=("$@"); else files=(tests/*.sh); fi
collected "${#files[@]}"
said=$(shellcheck -x -f gcc "${files[@]}" 2>&1)
code=$?
for file in "${files[@]}"; do
  if grep -qF "$file:" <<<"$said"; then fail "shellcheck $file"; else pass "shellcheck $file"; fi
done
[ -z "$said" ] || printf '%s\n' "$said"
results_add_up
finished=yes
if [ "$code" != 0 ] || [ "$fails" -gt 0 ]; then exit 1; fi
