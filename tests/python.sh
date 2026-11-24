# shellcheck shell=bash
# shellcheck disable=SC2034  # PY is read by the suite that sources this file
# The Python every suite runs Lem's code and its own helpers with: the app's own, the checkout's .venv, which `uv sync`
# makes with Lem installed from the checkout (an editable install) and the maintainer's tools. Never another python3
# on the PATH. A suite sources this file from the root of the checkout; with no .venv/bin/python or .venv/bin/lem it
# says so in one line and fails.
PY=$PWD/.venv/bin/python
if [ ! -x "$PY" ] || [ ! -x "$PWD/.venv/bin/lem" ]; then
  printf 'FAIL %s has no .venv/bin/python and .venv/bin/lem: run uv sync at the root of the checkout\n' "$PWD"
  exit 1
fi
