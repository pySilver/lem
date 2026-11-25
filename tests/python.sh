# shellcheck shell=bash
# shellcheck disable=SC2034  # PY and LEM are read by the suite that sources this file
# The Python every suite runs its own helpers and stand-ins with, and the command `lem` every journey drives.
#
# PY: the checkout's .venv, which `uv sync` makes with Lem installed from the checkout (an editable install) and the
# maintainer's tools. Never another python3 on the PATH.
#
# LEM: LEM_UNDER_TEST, the absolute path of the `lem` a suite drives; by default the checkout's own, .venv/bin/lem.
# A journey starts Lem only through it, so that tests/installed.sh runs every journey against an app installed from a
# wheel outside the checkout. A check that needs the checkout itself (a source file's text, its commit, a copy of its
# package) says so, and asks `in_checkout` where it means nothing for an installed app.
#
# LEM_SERVE=off: no command a suite runs starts a board server, which would outlive the run; a check of the start on
# demand lifts it for its one call, in a home folder of its own.
#
# A suite sources this file from the root of the checkout; with no .venv/bin/python or .venv/bin/lem, or a
# LEM_UNDER_TEST that is no absolute path to a command, it says so in one line and fails.
PY=$PWD/.venv/bin/python
if [ ! -x "$PY" ] || [ ! -x "$PWD/.venv/bin/lem" ]; then
  printf 'FAIL %s has no .venv/bin/python and .venv/bin/lem: run uv sync at the root of the checkout\n' "$PWD"
  exit 1
fi
export LEM_UNDER_TEST=${LEM_UNDER_TEST:-$PWD/.venv/bin/lem}
case $LEM_UNDER_TEST in
  /*) ;;
  *) printf 'FAIL LEM_UNDER_TEST=%s is no absolute path: name the command lem a suite drives by its whole path\n' "$LEM_UNDER_TEST"; exit 1 ;;
esac
if [ ! -x "$LEM_UNDER_TEST" ]; then
  printf 'FAIL LEM_UNDER_TEST=%s is no command: name an installed lem, or leave it out for the checkout'"'"'s .venv/bin/lem\n' "$LEM_UNDER_TEST"
  exit 1
fi
LEM=$LEM_UNDER_TEST
export LEM_SERVE=off
# lem_root: the folder of the plugin's files of the lem under test, which `lem version` prints as root: this checkout,
# or an installed app's data folder
lem_root() { "$LEM" version | "$PY" -I -c 'import json, sys; print(json.load(sys.stdin)["root"])'; }
# in_checkout: whether the lem under test is this checkout's own, whose files are the files git has here
in_checkout() {
  case $LEM_UNDER_TEST in
    "$PWD"/*) return 0 ;;
    *) return 1 ;;
  esac
}
# A suite run in a Claude Code session whose SessionStart hook named Lem's plugin gets that plugin's
# LEM_PLUGIN_ROOT, and a plugin of another version than the app under test would stop each `lem` of the run
# (`lem.__main__.same_plugin`): the app under test is the one LEM_UNDER_TEST names, with no plugin to match.
unset LEM_PLUGIN_ROOT CLAUDE_PLUGIN_ROOT CLAUDE_ENV_FILE
