#!/usr/bin/env bash
# The naps (stages/nap.md): the settings of `[naps]`, `lem project may-nap`, which says whether a nap
# may start and removes the old ones, and the feed of the board's Dreams tab, `naps.js`. No agent
# naps here: a nap's folder is written by hand, the way a nap's agent leaves it.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

BOARD=$PWD/skills/lem/scripts/board.py
NP=$WORK/nap-repo
git init -q -b main "$NP" && commit "$NP" start
project --repo "$NP" init --base main >/dev/null
git -C "$NP" add -A && commit "$NP" "chore: the settings"
NAPS=$NP/.lem/state/naps
nap() { project --repo "$NP" may-nap "$@"; }
# ago HOURS: the folder time of a nap that started HOURS ago, by the clock
ago() { "$PY" -c 'import sys, datetime as d; print((d.datetime.now(d.timezone.utc) - d.timedelta(hours=float(sys.argv[1]))).strftime("%Y-%m-%d-%H%M"))' "$1"; }
# woke NAME: a nap's folder as its agent leaves it, with the dream, one made thing and the waking note
woke() { mkdir -p "$NAPS/$1" && printf '# A dream\n\nA field.\n' > "$NAPS/$1/dream.md" && printf 'x\n' > "$NAPS/$1/thing.txt" && printf '# Waking\n\nNothing.\n' > "$NAPS/$1/waking.md"; }
naps_on() { "$PY" -I -c 'import re, sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(re.sub(r"(?m)^on = false$", "on = true", s, count=1))' "$NP/.lem/project.toml" && settled "$NP"; }

# The settings: off, 30 days, 6 hours, each guess said so in the file; a wrong value is refused by its key.
shown=$(project --repo "$NP" show | field 'd["naps"]')
template=$(sed -n '/^\[naps\]$/,$p' "$NP/.lem/project.toml")
bad() {
  local repo=$WORK/naps-bad-$1
  git init -q -b main "$repo"
  printf '%s\n' '[naps]' "$2" > "$repo/.lem-settings" && mkdir -p "$repo/.lem" && mv "$repo/.lem-settings" "$repo/.lem/project.toml"
  { project --repo "$repo" show >/dev/null; } 2>&1 || true
}
if [ "$shown" = "{'on': False, 'keep_days': 30, 'gap_hours': 6}" ] \
  && grep -qx 'on = false' <<<"$template" && grep -qx 'keep_days = 30' <<<"$template" && grep -qx 'gap_hours = 6' <<<"$template" \
  && [ "$(grep -c 'A guess' <<<"$template")" = 2 ] && grep -q 'nobody has shown that it helps' <<<"$template" \
  && grep -qF 'naps.keep_days = 0 must be a whole number of days, 1 or more' <<<"$(bad zero 'keep_days = 0')" \
  && grep -qF "naps.on = 'yes' must be true or false" <<<"$(bad word 'on = "yes"')" \
  && grep -qF 'naps.gap_hours = True must be a whole number of hours, 1 or more' <<<"$(bad bool 'gap_hours = true')" \
  && grep -qF "unknown key naps.often" <<<"$(bad key 'often = 2')"; then
  pass "the naps' settings: off, 30 days and 6 hours unless the project says otherwise, the template says each number is a guess, and a wrong value is refused by its key"
else
  fail "the naps' settings: $shown / $template"
fi

# Off, Lem's own call says no and writes nothing down; the owner's word starts one, and a second call finds it running.
off=$(nap); off_code=$(status_of nap)
asked=$(nap --asked)
time=$(field 'd["time"]' <<<"$asked")
# the clock's minute, or the one before it when the minute turned between the call and this line
clock=no
if [ "$time" = "$(ago 0)" ] || [ "$time" = "$(ago 0.017)" ]; then clock=yes; fi
again=$(nap --asked)
if [ "$off_code" = 0 ] && [ "$(field 'd["may"]' <<<"$off")" = False ] && grep -qF 'the naps are off' <<<"$(field 'd["why"]' <<<"$off")" \
  && [ "$(field 'd["may"]' <<<"$asked")" = True ] && [ "$(field 'd["why"]' <<<"$asked")" = "the owner asked for it" ] \
  && [[ $time =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4}$ ]] && [ "$clock" = yes ] \
  && [ "$(field 'd["folder"]' <<<"$asked")" = "$NAPS" ] && [ -f "$NAPS/.asleep" ] && [ "$(field 'd["time"]' < "$NAPS/.asleep")" = "$time" ] \
  && [ "$(field 'd["may"]' <<<"$again")" = False ] && grep -qF "a nap runs since" <<<"$(field 'd["why"]' <<<"$again")"; then
  pass "may-nap: with the naps off Lem's own call is a no with exit 0; the owner's word starts one at the clock's minute and writes it down, and while it runs a second call is a no"
else
  fail "may-nap off and asked: $off / $asked / $again"
fi

# The nap ends when its folder holds waking.md; then the gap holds for Lem's own call, and not for the owner's word.
woke "$time-a-field"
naps_on
gap=$(nap)
asked_again=$(nap --asked)
if [ "$(field 'd["may"]' <<<"$gap")" = False ] && grep -qF 'and naps.gap_hours is 6' <<<"$(field 'd["why"]' <<<"$gap")" \
  && [ "$(field 'd["newest"]' <<<"$gap")" = "$time-a-field" ] && [ "$(field 'd["may"]' <<<"$asked_again")" = True ]; then
  pass "may-nap: a nap that wrote waking.md runs no more; Lem's own call waits naps.gap_hours from the newest start, and the owner's word does not wait"
else
  fail "may-nap after a nap: $gap / $asked_again"
fi

# A start with no waking note runs for an hour at most, and the gap counts from it too.
rm -rf "${NAPS:?}"/*-* "$NAPS/.asleep"
printf '{"since": "%s", "time": "%s", "asked": false}\n' "$(ago 2 | "$PY" -c 'import sys, datetime as d; print(d.datetime.strptime(sys.stdin.read().strip(), "%Y-%m-%d-%H%M").strftime("%Y-%m-%dT%H:%M:00Z"))')" "$(ago 2)" > "$NAPS/.asleep"
stale=$(nap)
rm -f "$NAPS/.asleep"
LONG=$(ago 7)-long-ago
woke "$LONG"
due=$(nap)
if [ "$(field 'd["may"]' <<<"$stale")" = False ] && grep -qF 'the newest nap started 2.0 hours ago' <<<"$(field 'd["why"]' <<<"$stale")" \
  && [ "$(field 'd["may"]' <<<"$due")" = True ] && grep -qF 'the newest nap started 7.0 hours ago' <<<"$(field 'd["why"]' <<<"$due")"; then
  pass "may-nap: a start that wrote no waking note is no nap that runs after an hour, its start still counts for the gap, and seven hours after the newest nap Lem's own call is a yes"
else
  fail "may-nap and the gap: $stale / $due"
fi

# Old naps go; a folder whose name holds no time, and a link, never do. A broken record is refused by its file.
rm -f "$NAPS/.asleep"
woke "2026-01-01-0000-the-first"
TWO=$(ago 47)-two-days
woke "$TWO"
mkdir -p "$NAPS/not-a-nap" && touch -t 202601010000 "$NAPS/not-a-nap"
ln -s "$NAPS/2026-01-01-0000-the-first" "$NAPS/2026-01-02-0000-a-link"
cleaned=$(nap)
"$PY" -I -c 'import re, sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(re.sub(r"(?m)^keep_days = 30$", "keep_days = 1", s, count=1))' "$NP/.lem/project.toml" && settled "$NP"
shorter=$(nap)
printf 'not json\n' > "$NAPS/.asleep"
broken=$(nap 2>&1 || true); broken_code=$(status_of nap)
rm -f "$NAPS/.asleep"
if [ "$(field 'd["removed"]' <<<"$cleaned")" = "['2026-01-01-0000-the-first']" ] && [ -d "$NAPS/not-a-nap" ] && [ -L "$NAPS/2026-01-02-0000-a-link" ] \
  && [ "$(field 'd["removed"]' <<<"$shorter")" = "['$TWO']" ] && [ -d "$NAPS/$LONG" ] \
  && [ "$broken_code" = 1 ] && grep -qF "$NAPS/.asleep is not the record may-nap writes" <<<"$broken"; then
  pass "may-nap removes the naps older than naps.keep_days and names them, never a folder whose name holds no time or a link, and refuses a broken record of a start by its file"
else
  fail "may-nap's removal: $cleaned / $shorter / $broken"
fi
rm -f "$NAPS/2026-01-02-0000-a-link"

# The board's feed: the naps newest first, each as text, `</` split so no text ends the script tag,
# a link in a nap not followed, a folder with no time left out, and the examples only with --demo.
TAG=$(ago 1)-the-tag
mkdir -p "$NAPS/$TAG"
printf '# The tag\n\nIt said </script><b>hello</b>.\n' > "$NAPS/$TAG/dream.md"
ln -s /etc/hosts "$NAPS/$TAG/hosts.txt"
printf '<svg xmlns="http://www.w3.org/2000/svg"/>\n' > "$NAPS/$TAG/tag.svg"
printf '<html></html>\n' > "$NAPS/$TAG/tag.html"
board_feed() { env -u AGTERM_SESSION_ID -u AGTERM_SOCKET -u AGT_SESSION_ID -u AGT_SOCKET "$PY" -B "$BOARD" --repo "$NP" --no-open "$@" >/dev/null; }
feed() { "$PY" -c 'import json, re, sys; print(json.dumps(json.loads(re.fullmatch(r"lemNaps\((.*)\);\n", open(sys.argv[1]).read(), re.S).group(1))))' "$NAPS/../naps.js"; }
board_feed
plain=$(feed)
board_feed --demo
demo=$(feed)
EMPTY=$WORK/no-naps
git init -q -b main "$EMPTY" && commit "$EMPTY" start && project --repo "$EMPTY" init --base main >/dev/null
env -u AGTERM_SESSION_ID -u AGTERM_SOCKET "$PY" -B "$BOARD" --repo "$EMPTY" --no-open >/dev/null
if [ "$(field '[n["name"] for n in d["naps"]]' <<<"$plain")" = "['$TAG', '$LONG']" ] \
  && ! grep -qF '</script' "$NAPS/../naps.js" && grep -qF '<\/script><b>hello<\/b>' "$NAPS/../naps.js" \
  && [ "$(field 'd["naps"][0]["dream"]' <<<"$plain")" = "It said </script><b>hello</b>." ] \
  && [ "$(field 'd["naps"][0]["title"]' <<<"$plain")" = "The tag" ] && [ "$(field 'd["naps"][1]["title"]' <<<"$plain")" = "Long ago" ] \
  && [ "$(field '[(m["file"], m["kind"]) for m in d["naps"][0]["made"]]' <<<"$plain")" = "[('tag.html', 'file'), ('tag.svg', 'picture')]" ] \
  && [ "$(field 'd["naps"][1]["made"]' <<<"$plain")" = "[{'file': 'thing.txt', 'kind': 'text', 'text': 'x'}]" ] \
  && [ "$(field 'd["examples"]' <<<"$plain")" = False ] && [ "$(field 'd["examples"]' <<<"$demo")" = True ] \
  && [ "$(field '[n["name"] for n in d["naps"] if n["example"]]' <<<"$demo")" = "['2026-11-17-1347-white-paper-in-february']" ] \
  && [ -f "$NAPS/../demo-naps/2026-11-17-1347-white-paper-in-february/dream.md" ] \
  && grep -qx 'lemNaps({"read": "[0-9TZ:-]*", "naps": \[\], "more": 0, "examples": false});' "$EMPTY/.lem/state/naps.js"; then
  pass "board.py writes the Dreams tab's naps.js: newest first, each nap's text with its </ split, a link in a nap not followed, a picture and a page told apart, the example naps only in a folder of examples, and no nap where there is none"
else
  fail "the naps' feed: $plain"
fi

# One person says no to the naps on their machine, since a nap spends their tokens: Lem's own call is refused
# with that reason, and the owner's word still starts one; the machine's file can never switch them on.
printf '%s\n' '[naps]' 'on = false' > "$NP/.lem/project.local.toml"
off_here=$(project --repo "$NP" show 2>&1 | field '(d["naps"]["on"], d["local"]["overrides"])' 2>&1 || true)
own_call=$(nap 2>&1 | field '(d["may"], d["why"])' 2>&1 || true)
rm -rf "$NAPS/.asleep"
asked_here=$(nap --asked 2>&1 | field 'd["may"]' 2>&1 || true)
rm -f "$NAPS/.asleep"
printf '%s\n' '[naps]' 'on = true' > "$NP/.lem/project.local.toml"
on_here=$(status_of project --repo "$NP" may-nap)
rm "$NP/.lem/project.local.toml"
if grep -qx 'on = true' "$NP/.lem/project.toml" && [ "$off_here" = "(False, ['naps.on'])" ] && [ "$own_call" = "(False, 'the naps are off on this machine (naps.on = false in .lem/project.local.toml)')" ] \
  && [ "$asked_here" = True ] && [ "$on_here" = 1 ]; then
  pass "the machine's own file says no to the naps for its person: Lem's own call is refused with that reason, the owner's word still starts one, and a yes there is refused"
else
  fail "the naps off on one machine: $off_here / $own_call / $asked_here / $on_here"
fi

# the settings file is the one this block edited by hand
if git -C "$NP" status --porcelain --untracked-files=all -- . ':!.lem/project.toml' | grep -q .; then
  fail "a nap changes nothing git sees: $(git -C "$NP" status --porcelain --untracked-files=all)"
else
  pass "a nap, its record and the board's feed change nothing git sees in the repository"
fi

finish
