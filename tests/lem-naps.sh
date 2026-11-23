#!/usr/bin/env bash
# The naps (stages/nap.md): the settings of `[naps]` and `lem project may-nap`, which says whether a nap
# may start and removes the old ones. No agent naps here: a nap's folder is written by hand, the way a
# nap's agent leaves it.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

NP=$WORK/nap-repo
git init -q -b main "$NP" && commit "$NP" start
project --repo "$NP" init --base main >/dev/null
git -C "$NP" add -A && commit "$NP" "chore: the settings"
NAPS=$NP/.lem/state/naps
nap() { project --repo "$NP" may-nap; }
# ago HOURS: the folder time of a nap that started HOURS ago, by the clock
ago() { "$PY" -c 'import sys, datetime as d; print((d.datetime.now(d.timezone.utc) - d.timedelta(hours=float(sys.argv[1]))).strftime("%Y-%m-%d-%H%M"))' "$1"; }
# woke NAME: a nap's folder as its agent leaves it, with the dream, one made thing and the waking note
woke() { mkdir -p "$NAPS/$1" && printf '# A dream\n\nA field.\n' > "$NAPS/$1/dream.md" && printf 'x\n' > "$NAPS/$1/thing.txt" && printf '# Waking\n\nNothing.\n' > "$NAPS/$1/waking.md"; }
naps_on() { "$PY" -I -c 'import re, sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(re.sub(r"(?m)^on = false$", "on = true", s, count=1))' "$NP/.lem/settings.toml"; }

# The settings: one switch, off; the 6 hours are fixed, a guess the file says so of, and a nap's folder is kept for
# state.keep_days; a wrong value or a key it does not know is refused by its key.
shown=$(project --repo "$NP" show | field 'd["naps"]')
template=$(sed -n '/^\[naps\]$/,$p' "$NP/.lem/settings.toml")
bad() {
  local repo=$WORK/naps-bad-$1
  git init -q -b main "$repo"
  printf '%s\n' '[naps]' "$2" > "$repo/.lem-settings" && mkdir -p "$repo/.lem" && mv "$repo/.lem-settings" "$repo/.lem/settings.toml"
  { project --repo "$repo" show >/dev/null; } 2>&1 || true
}
if [ "$shown" = "{'on': False, 'from': '.lem/settings.toml'}" ] \
  && grep -qx 'on = false' <<<"$template" \
  && grep -qF '6 hours pass between two naps: a guess' <<<"$template" && grep -qF "A nap's folder is kept for state.keep_days." <<<"$template" && grep -q 'nobody has shown that it helps' <<<"$template" \
  && grep -qF "naps.on = 'yes' must be true or false" <<<"$(bad word 'on = "yes"')" \
  && grep -qF "unknown key naps.often" <<<"$(bad key 'often = 2')"; then
  pass "the naps' settings: one switch, off; 6 hours are fixed and the template says it is a guess, and a nap's folder is kept for state.keep_days; a wrong value or a key it does not know is refused by its key"
else
  fail "the naps' settings: $shown / $template"
fi

# The naps' table is the main checkout's, as [flow] is: a task's branch that switches them on changes
# nothing that its worktree reads, since a nap spends the tokens of whoever works on the machine.
git -C "$NP" worktree add -q "$WORK/nap-tree" -b feat/naps-on main
"$PY" -I -c 'import re, sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(re.sub(r"(?m)^on = false$", "on = true", s, count=1))' "$WORK/nap-tree/.lem/settings.toml"
git -C "$WORK/nap-tree" -c user.name=t -c user.email=t@t commit -q -am "chore: the naps on"
from_branch=$(project --repo "$WORK/nap-tree" show | field '(d["naps"]["on"], d["settings_from"].startswith("this worktree'"'"'s branch, with [flow], [naps] and [state] from the main checkout"))')
git -C "$NP" worktree remove --force "$WORK/nap-tree" && git -C "$NP" branch -q -D feat/naps-on
if [ "$from_branch" = "(False, True)" ]; then
  pass "in a task's worktree the naps' table is the main checkout's: a branch that switches the naps on changes nothing, and show says where both tables come from"
else
  fail "the naps' table of a worktree: $from_branch"
fi

# Off, Lem's call says no and writes nothing down, and no word of the owner's starts one; on, it says yes at the
# clock's minute and writes the nap down, and a second call finds it running.
off=$(nap); off_code=$(status_of nap); asked_code=$(status_of project --repo "$NP" may-nap --asked)
off_marker=no; [ -e "$NAPS/.asleep" ] && off_marker=yes
naps_on
started=$(nap)
time=$(field 'd["time"]' <<<"$started")
# the clock's minute, or the one before it when the minute turned between the call and this line
clock=no
if [ "$time" = "$(ago 0)" ] || [ "$time" = "$(ago 0.017)" ]; then clock=yes; fi
again=$(nap)
if [ "$off_code" = 0 ] && [ "$(field 'd["may"]' <<<"$off")" = False ] && grep -qF 'the naps are off' <<<"$(field 'd["why"]' <<<"$off")" \
  && [ "$off_marker" = no ] && [ "$asked_code" = 2 ] \
  && [ "$(field 'd["may"]' <<<"$started")" = True ] && [ "$(field 'd["why"]' <<<"$started")" = "there is no nap yet" ] \
  && [[ $time =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4}$ ]] && [ "$clock" = yes ] \
  && [ "$(field 'd["folder"]' <<<"$started")" = "$NAPS" ] && [ -f "$NAPS/.asleep" ] && [ "$(field 'd["time"]' < "$NAPS/.asleep")" = "$time" ] \
  && [ "$(field 'd["may"]' <<<"$again")" = False ] && grep -qF "a nap runs since" <<<"$(field 'd["why"]' <<<"$again")"; then
  pass "may-nap: with the naps off it is a no with exit 0 that writes nothing, and it takes no --asked; with them on it starts one at the clock's minute and writes it down, and while it runs a second call is a no"
else
  fail "may-nap off and on: $off / $asked_code / $started / $again"
fi

# The nap ends when its folder holds waking.md; then the gap holds.
woke "$time-a-field"
gap=$(nap)
if [ "$(field 'd["may"]' <<<"$gap")" = False ] && grep -qF 'and 6 hours pass between two naps' <<<"$(field 'd["why"]' <<<"$gap")" \
  && [ "$(field 'd["newest"]' <<<"$gap")" = "$time-a-field" ]; then
  pass "may-nap: a nap that wrote waking.md runs no more, and the next call waits 6 hours from the newest start"
else
  fail "may-nap after a nap: $gap"
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

# Old naps go with `lem project prune`, which may-nap leaves to it; a folder whose name holds no time, and a link, never
# do. A broken record is refused by its file.
rm -f "$NAPS/.asleep"
woke "2026-01-01-0000-the-first"
TWO=$(ago 47)-two-days
woke "$TWO"
mkdir -p "$NAPS/not-a-nap" && touch -t 202601010000 "$NAPS/not-a-nap"
ln -s "$NAPS/2026-01-01-0000-the-first" "$NAPS/2026-01-02-0000-a-link"
cleaned=$(nap)
pruned=$(project --repo "$NP" prune)
printf 'not json\n' > "$NAPS/.asleep"
broken=$(nap 2>&1 || true); broken_code=$(status_of nap)
rm -f "$NAPS/.asleep"
if [ "$(field '"removed" in d' <<<"$cleaned")" = False ] && [ "$(field '[f["path"] for f in d["folders"]]' <<<"$pruned")" = "['naps/2026-01-01-0000-the-first']" ] \
  && [ ! -e "$NAPS/2026-01-01-0000-the-first" ] && [ -d "$NAPS/not-a-nap" ] && [ -L "$NAPS/2026-01-02-0000-a-link" ] \
  && [ -d "$NAPS/$TWO" ] && [ -d "$NAPS/$LONG" ] \
  && [ "$broken_code" = 1 ] && grep -qF "$NAPS/.asleep is not the record may-nap writes" <<<"$broken"; then
  pass "lem project prune removes the naps older than state.keep_days and names them, may-nap removes none, a younger one stays, and so do a folder whose name holds no time and a link; may-nap refuses a broken record of a start by its file"
else
  fail "the removal of old naps: $cleaned / $pruned / $broken"
fi
rm -f "$NAPS/2026-01-02-0000-a-link"

# One person says no to the naps on their machine, since a nap spends their tokens: Lem's call is refused
# with that reason; the machine's file can never switch them on.
printf '%s\n' '[naps]' 'on = false' > "$NP/.lem/settings.local.toml"
off_here=$(project --repo "$NP" show 2>&1 | field '(d["naps"]["on"], d["local"]["overrides"])' 2>&1 || true)
own_call=$(nap 2>&1 | field '(d["may"], d["why"])' 2>&1 || true)
rm -f "$NAPS/.asleep"
printf '%s\n' '[naps]' 'on = true' > "$NP/.lem/settings.local.toml"
on_here=$(status_of project --repo "$NP" may-nap)
rm "$NP/.lem/settings.local.toml"
if grep -qx 'on = true' "$NP/.lem/settings.toml" && [ "$off_here" = "(False, ['naps.on'])" ] && [ "$own_call" = "(False, 'the naps are off on this machine (naps.on = false in .lem/settings.local.toml)')" ] \
  && [ "$on_here" = 1 ]; then
  pass "the machine's own file says no to the naps for its person: Lem's call is refused with that reason, and a yes there is refused"
else
  fail "the naps off on one machine: $off_here / $own_call / $on_here"
fi

# the settings file is the one this block edited by hand
if git -C "$NP" status --porcelain --untracked-files=all -- . ':!.lem/settings.toml' | grep -q .; then
  fail "a nap changes nothing git sees: $(git -C "$NP" status --porcelain --untracked-files=all)"
else
  pass "a nap and its record change nothing git sees in the repository"
fi

finish
