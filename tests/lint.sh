#!/usr/bin/env bash
# The style of this repository's code, one check for each tool: ruff's format and ruff's rules over
# the Python, pyrefly's types (pyproject.toml), and ESLint with JavaScript Standard Style over the
# JavaScript (eslint.config.mjs). `bash tests/lint.sh` runs the four; `bash tests/lint.sh --fix`
# first lets ruff and ESLint fix what each can by itself, then runs them.
#
# The tools are the maintainer's, not Lem's: uv brings ruff and pyrefly at the versions of uv.lock
# (`uv run --locked`, which makes .venv at its first run), and npm brings ESLint at the versions of
# package-lock.json (`npm ci`, which this suite runs when node_modules has no eslint yet). A machine
# with no uv prints a SKIP line for each Python check, and one with no npm for the JavaScript's.
set -uo pipefail
cd -P "$(dirname "$0")/.." || exit 1
# shellcheck source-path=SCRIPTDIR source=checks.sh
. tests/checks.sh
trap stopped EXIT
collected

fix=""
[ "${1:-}" = --fix ] && fix=yes

# said TEXT OUTPUT: what a tool said, below the FAIL line of its check
said() {
  fail "$1"
  printf '%s\n' "$2"
}

python_checks() {
  local out
  if [ -n "$fix" ]; then
    uv run --locked ruff check --fix --quiet
    uv run --locked ruff format --quiet
  fi
  if out=$(uv run --locked ruff format --check --quiet 2>&1); then
    pass "ruff format: every Python file has the one format"
  else
    said "ruff format: every Python file has the one format" "$out"
  fi
  if out=$(uv run --locked ruff check --quiet --output-format concise 2>&1); then
    pass "ruff check: no Python file breaks a rule of pyproject.toml"
  else
    said "ruff check: no Python file breaks a rule of pyproject.toml" "$out"
  fi
  if out=$(uv run --locked pyrefly check --output-format min-text 2>&1); then
    pass "pyrefly check: the types of every Python file hold under Python 3.11"
  else
    said "pyrefly check: the types of every Python file hold under Python 3.11" "$out"
  fi
}

javascript_checks() {
  local out
  if [ ! -x node_modules/.bin/eslint ] && ! out=$(npm ci --silent 2>&1); then
    said "eslint: no JavaScript file breaks JavaScript Standard Style" "npm ci failed, so ESLint is not installed: run \`npm ci\` at the root of the checkout. It said: $out"
    return
  fi
  [ -z "$fix" ] || npx eslint . --fix
  if out=$(npx eslint . 2>&1); then
    pass "eslint: no JavaScript file breaks JavaScript Standard Style"
  else
    said "eslint: no JavaScript file breaks JavaScript Standard Style" "$out"
  fi
}

if command -v uv >/dev/null 2>&1; then
  python_checks
else
  skip_function python_checks "no uv here to bring ruff and pyrefly (https://docs.astral.sh/uv/)"
fi
if command -v npm >/dev/null 2>&1; then
  javascript_checks
else
  skip_function javascript_checks "no npm here to bring ESLint"
fi

results_add_up
finished=yes
[ "$fails" -eq 0 ] || exit 1
