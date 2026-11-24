#!/usr/bin/env bash
# The experts, offline: the lem-ask-expert skill's brief of a question in words, which the owner asks
# and a lead's ladder asks at its last level, its folder, the record of each answer, who the experts
# are, and one expert alone without Codex. No expert runs here.
set -euo pipefail

cd "$(dirname "$0")/.."
# Lem's one entry: `"$PY" -B "$MAIN" NAME ARGS...` is `lem NAME ARGS...`
MAIN=$PWD/src/lem/__main__.py
WORK=$(cd "$(mktemp -d)" && pwd -P)
export XDG_CONFIG_HOME="$WORK/config"  # the owner's status (`lem_state.owner_mark`) of this run, never the home directory's
trap 'rm -rf "$WORK"' EXIT
PY=$(python3 -I -c 'import sys; print(sys.executable)')
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
# A stand-in for Codex on PATH, so that both experts of the default seats answer here (`here` in `lem project show`),
# whatever this machine has; a check of one expert alone runs with a PATH that has no codex.
mkdir -p "$WORK/standin" && printf '%s\n' '#!/bin/sh' 'exit 0' > "$WORK/standin/codex" && chmod +x "$WORK/standin/codex"
export PATH="$WORK/standin:$PATH"
# NOCODEX: a PATH with git and no codex, for a check of one expert alone
mkdir -p "$WORK/nocodex" && ln -s "$(command -v git)" "$WORK/nocodex/git"
NOCODEX=$WORK/nocodex

fails=0
pass() { printf 'ok   %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1"; fails=$((fails + 1)); }
project() { "$PY" -B "$MAIN" project "$@"; }
status_of() { set +e; "$@" >/dev/null 2>&1; local code=$?; set -e; echo "$code"; }
field() { "$PY" -c 'import json, sys; d = json.load(sys.stdin); print(eval(sys.argv[1], {"d": d}))' "$1"; }

EX=$WORK/experts-repo
git init -q -b main "$EX" && git -C "$EX" config user.name t && git -C "$EX" config user.email t@t
echo 'echo "1042,for Ania"' > "$EX/export.sh" && git -C "$EX" add -A && git -C "$EX" commit -q -m start
project --repo "$EX" init --base main >/dev/null
# the project's people, which every brief names: one with its own seats, one without
mkdir -p "$EX/.lem/personas"
printf '%s\n' '---' 'seats: ["claude/opus:high"]' '---' '# A merchant who sells gifts' '' '## Who they are' '' 'Sells gifts online and sends the CSV export to an accountant each week.' > "$EX/.lem/personas/merchant.md"
printf '%s\n' '# The accountant of the shop' '' '## Who they are' '' 'Imports the export into the books each Monday.' > "$EX/.lem/personas/accountant.md"
printf '%s\n' '# A gift shop' '' 'One merchant, a few hundred orders a week.' > "$EX/.lem/profile.md"
git -C "$EX" add -A && git -C "$EX" commit -q -m "chore: the settings"
experts() { "$PY" -B "$MAIN" experts --repo "$EX" "$@"; }

# Without Codex on the machine the one expert that can answer answers alone: a question in words has one expert.
alone_brief=$(env PATH="$NOCODEX" "$PY" -B "$MAIN" experts --repo "$EX" brief --question "Which font for the note?" || true)
alone_names=$(field '[e["name"] for e in d["experts"]]' <<<"$alone_brief" || true)
alone_file=$(field 'd["brief"]' <<<"$alone_brief" || true)
if [ "$alone_names" = "['fable']" ] && grep -qF "The owner asks one expert this question" "$alone_file"; then
  pass "with no Codex on the machine one expert answers alone: a question in words has one expert"
else
  fail "one expert alone: $alone_names / $alone_file"
fi

# a question in words: a folder of its own in the state folder, with the brief, the answers and a short record
QS=$EX/.lem/state/experts
asked=$(experts brief --question "Which store for the sessions?" --context "Sessions live in process memory, so every deploy logs everyone out." \
  --option "Redis" --option "a Postgres table" --file export.sh || true)
folder=$(field 'd["folder"]' <<<"$asked" 2>/dev/null || true)
# made by brief; made here only so that a brief that failed shows as a FAIL line and does not stop the suite
mkdir -p "$QS/$folder"
shape=$(field '(d["dir"] == d["brief"].rsplit("/", 1)[0], [(e["name"], e["seat"], e["agent"], e["model"], e["effort"]) for e in d["experts"]], d["ask"], d["worktree"], d["answers"]["astra"].endswith("/astra.md"))' <<<"$asked" 2>/dev/null || true)
holds=yes
for want in "# A question for the experts" "Which store for the sessions?" "## What is being decided" "Sessions live in process memory, so every deploy logs everyone out." \
  "1. Redis" "2. a Postgres table" "- $EX/export.sh" "Read only. Change no file" "    pick: ONE OPTION, COPIED WORD FOR WORD FROM THE OPTIONS ABOVE" "    none fits"; do
  grep -qF -- "$want" "$QS/$folder/brief.md" 2>/dev/null || { holds="no: $want"; break; }
done
printf '%s\n' 'pick: Memcached' 'why: It is fast.' > "$QS/$folder/fable.md"
noption=$(experts record --folder "$folder" --expert fable 2>&1 || true)
printf '%s\n' 'answer: Redis' 'why: It runs already.' > "$QS/$folder/fable.md"
badform=$(experts record --folder "$folder" --expert fable 2>&1 || true)
stranger=$(experts record --folder "$folder" --expert opus 2>&1 || true)
printf '%s\n' 'pick: Redis' 'why: It runs already for the job queue.' > "$QS/$folder/fable.md"
half=$(experts record --folder "$folder" --expert fable | field '(d["answers"]["fable"]["pick"], d["waiting"], d["agree"], "astra" in d["next"])' || true)
twice=$(experts record --folder "$folder" --expert fable 2>&1 || true)
printf '%s\n' 'pick: Redis' 'why: A key with an expiry is what a session is.' > "$QS/$folder/astra.md"
whole=$(experts record --folder "$folder" --expert astra | field '(d["agree"], d["waiting"], sorted(d["answers"]), "all picked" in d["next"])' || true)
kept=$(field '(d["question"], d["options"], sorted(d["answers"]))' < "$QS/$folder/record.json" || true)
if [ "$(dirname "$QS/$folder")" = "$QS" ] && [ "$holds" = yes ] && [ -z "$(git -C "$EX" status --porcelain --untracked-files=all)" ] \
  && [ "$shape" = "(True, [('fable', 'claude/fable:high', 'claude', 'fable', 'high'), ('astra', 'codex/gpt-6.2-astra:high', 'codex', 'gpt-6.2-astra', 'high')], ['fable', 'astra'], '$EX', True)" ] \
  && grep -qF "'Memcached' is none of them" <<<"$noption" && grep -qF "is not an answer in the brief's form" <<<"$badform" \
  && grep -qF -- "--expert opus is none of this question's experts (fable, astra)" <<<"$stranger" && grep -qF "fable answered question $folder already" <<<"$twice" \
  && [ "$half" = "('Redis', ['astra'], None, True)" ] && [ "$whole" = "('Redis', [], ['astra', 'fable'], True)" ] \
  && [ "$kept" = "('Which store for the sessions?', ['Redis', 'a Postgres table'], ['astra', 'fable'])" ]; then
  pass "a question in words gets a folder of its own in the state folder, which git does not show: the brief holds the question, what is decided, the options and the files; the default experts are fable and astra by their seats; record takes each answer once, refuses a pick that is no option, a wrong form and a stranger, and says when all share a pick"
else
  fail "a question in words: $folder / $holds / $shape / $noption / $badform / $stranger / $half / $twice / $whole / $kept"
fi

# who the code is for: the brief names the profile and each persona, and a project with no personas gets no brief
people=yes
file=$QS/$folder/brief.md
for want in "## Who the code is for" "The project's profile, \`$EX/.lem/profile.md\`, says what the product is and who uses it: read it first." \
  "- **A merchant who sells gifts** (\`$EX/.lem/personas/merchant.md\`): Sells gifts online and sends the CSV export to an accountant each week." \
  "- **The accountant of the shop** (\`$EX/.lem/personas/accountant.md\`): Imports the export into the books each Monday." \
  "Weigh each option by what it does to these people. You still decide as an engineer"; do
  grep -qF -- "$want" "$file" 2>/dev/null || { people="no: $file: $want"; break; }
done
[ "$people" != yes ] || ! grep -qF 'seats:' "$file" || people="no: $file names a seat"
NOCAST=$WORK/no-cast
git init -q -b main "$NOCAST" && git -C "$NOCAST" config user.name t && git -C "$NOCAST" config user.email t@t
project --repo "$NOCAST" init --base main >/dev/null && git -C "$NOCAST" add -A && git -C "$NOCAST" commit -q -m start
nocast=$("$PY" -B "$MAIN" experts --repo "$NOCAST" brief --question "Which store?" 2>&1 || true)
if [ "$people" = yes ] && grep -qF "the brief says who the code is for, from the project's personas, and \`lem cast\` says: this project has no personas" <<<"$nocast" \
  && [ -z "$(ls "$NOCAST/.lem/state/experts" 2>/dev/null)" ]; then
  pass "a brief names the profile and each persona by its path, heading and who they are, without its seats, and tells the experts to weigh the options by these people; a project with no personas gets no brief"
else
  fail "who the code is for: $people / $nocast"
fi

# an open question has no options: the answer is in words, and two answers that differ are no split the script can see
open=$(experts brief --question "What would be the best solution for sessions that die at each deploy?" || true)
ofolder=$(field 'd["folder"]' <<<"$open" 2>/dev/null || true)
mkdir -p "$QS/$ofolder"
oform=$(grep -c "    answer: one to three sentences" "$QS/$ofolder/brief.md" 2>/dev/null || true)
printf '%s\n' 'pick: Redis' 'why: It runs already.' > "$QS/$ofolder/fable.md"
opick=$(experts record --folder "$ofolder" --expert fable 2>&1 || true)
printf '%s\n' 'answer: Keep sessions in Redis,' '  with an expiry on each key.' 'why: It runs already.' > "$QS/$ofolder/fable.md"
printf '%s\n' 'answer: A signed cookie.' 'why: No store to run.' > "$QS/$ofolder/astra.md"
experts record --folder "$ofolder" --expert fable >/dev/null || true
oboth=$(experts record --folder "$ofolder" --expert astra | field '(d["answers"]["fable"]["answer"], d["answers"]["astra"]["answer"], d["agree"], d["waiting"], "where they agree and where they split" in d["next"])' || true)
if [ "$oform" = 1 ] && grep -qF "is not an answer in the brief's form (\`answer: ...\`, then \`why: ...\`)" <<<"$opick" \
  && [ "$oboth" = "('Keep sessions in Redis, with an expiry on each key.', 'A signed cookie.', None, [], True)" ] && [[ "$ofolder" == *-what-would-be-the-best-solution ]]; then
  pass "an open question asks for an answer in words, refuses a pick, and leaves the comparison of two answers to the skill"
else
  fail "an open question: $ofolder / $oform / $opick / $oboth"
fi

# who the experts are: --seat names them for one call, and a seat that does not read is refused
seated=$(experts brief --question "Which store?" --seat claude/opus:high --seat codex/gpt-6.1-sol:xhigh | field '[(e["name"], e["model"], e["effort"]) for e in d["experts"]]' || true)
noform=$(experts brief --question "Which store?" --seat claude-opus 2>&1 || true)
noagent=$(experts brief --question "Which store?" --seat gemini/pro:high --seat claude/fable:high 2>&1 || true)
same=$(experts brief --question "Which store?" --seat claude/fable:high --seat claude/fable:max 2>&1 || true)
neither=$(experts brief 2>&1 || true)
alone=$(experts brief --question "Which store?" --option "Redis" 2>&1 || true)
if [ "$seated" = "[('opus', 'opus', 'high'), ('sol', 'gpt-6.1-sol', 'xhigh')]" ] && grep -qF "'claude-opus' is no seat: write it as agent/model:effort" <<<"$noform" \
  && grep -qF "names the agent 'gemini': an expert is started by claude or codex" <<<"$noagent" && grep -qF "two experts are named fable" <<<"$same" \
  && grep -qF "the following arguments are required: --question" <<<"$neither" && grep -qF "one --option is no choice" <<<"$alone"; then
  pass "--seat names the experts for one call, by the last word of each model; a seat not written agent/model:effort, an agent the harness does not know, two experts of one name, a brief with no question and one option alone are refused"
else
  fail "the experts' seats: $seated / $noform / $noagent / $same / $neither / $alone"
fi

# the folders of questions in words go state.keep_days (30 here) after their last write, with `lem project prune`; a
# newer one and a folder of another name stay, and a brief removes nothing
"$PY" -c 'import os, sys, time
old = time.time() - 31 * 86400
for root, dirs, files in os.walk(sys.argv[1]):
    for name in files: os.utime(os.path.join(root, name), (old, old))
os.utime(sys.argv[1], (old, old))' "$QS/$folder"
mkdir -p "$QS/notes" && "$PY" -c 'import os, sys, time; old = time.time() - 40 * 86400; os.utime(sys.argv[1], (old, old))' "$QS/notes"
briefed=$(experts brief --question "Which store, once more?" | field '"removed" in d' || true)
kept_by_brief=$([ -d "$QS/$folder" ] && echo yes || echo no)
pruned=$(project --repo "$EX" prune | field '[f["path"] for f in d["folders"] if f["kind"] == "experts"]' || true)
if [ "$briefed" = False ] && [ "$kept_by_brief" = yes ] && [ "$pruned" = "['experts/$folder']" ] && [ ! -e "$QS/$folder" ] && [ -d "$QS/$ofolder" ] && [ -d "$QS/notes" ]; then
  pass "a question's folder goes with lem project prune once state.keep_days passed since its last write, a brief removes none, and a newer one and a folder of another name stay"
else
  fail "the old folders: $briefed / $kept_by_brief / $pruned / $(ls "$QS")"
fi
# who the experts are: the settings' seats.experts, which experts.py reads through project.py show, the project's and
# this machine's own, each whole and named by its model; a --seat that names no model is named by its place (fable, astra)
seats_in() { "$PY" -I -c 'import re, sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(re.sub(r"(?m)^experts = .*$", "experts = " + sys.argv[2], s, count=1))' "$EX/.lem/settings.toml" "$1"; }
# Lem reads the settings as the base branch's commit has them, so an edit counts once it is committed
settings_committed() { git -C "$EX" add .lem/settings.toml && git -C "$EX" -c user.name=t -c user.email=t@t commit -q --allow-empty -m "chore: the settings" -- .lem/settings.toml; }
cp "$EX/.lem/settings.toml" "$WORK/settings.toml"
seats_in '["claude/opus:high", "codex/gpt-6.1-sol:xhigh"]'
settings_committed
tracked=$(experts brief --question "Which store, by the project's seats?" | field '[(e["name"], e["agent"], e["model"], e["effort"], e["place"]) for e in d["experts"]]' || true)
printf '%s\n' '[seats]' 'experts = ["claude/sonnet:high", "codex/gpt-6.2-astra:high"]' > "$EX/.lem/settings.local.toml"
machineq=$(experts brief --question "Which store, by this machine's seats?" | field '[e["name"] for e in d["experts"]]' || true)
rm "$EX/.lem/settings.local.toml"
nomodelq=$(experts brief --question "Which store, by no model?" --seat claude --seat codex:xhigh | field '[e["name"] for e in d["experts"]]' || true)
cp "$WORK/settings.toml" "$EX/.lem/settings.toml"
settings_committed
places=$("$PY" -B -c 'import sys; sys.path.insert(0, sys.argv[1]); from lem import experts, project; print(experts.PLACES == project.EXPERT_PLACES, project.EXPERT_PLACES)' "$PWD/src")
if [ "$tracked" = "[('opus', 'claude', 'opus', 'high', 'fable'), ('sol', 'codex', 'gpt-6.1-sol', 'xhigh', 'astra')]" ] \
  && [ "$machineq" = "['sonnet', 'astra']" ] && [ "$nomodelq" = "['fable', 'astra']" ] && [ "$places" = "True ('fable', 'astra')" ]; then
  pass "the experts are the settings' seats.experts, the project's or this machine's, each with its agent, model and effort, named by its model, and a --seat with no model by its place"
else
  fail "the experts from the settings: $tracked / $machineq / $nomodelq / $places"
fi


if [ -d "$PWD/src/lem/__pycache__" ]; then fail "experts.py left a __pycache__"; else pass "experts.py left no __pycache__, also of the scripts it imports"; fi

if [ "$fails" -gt 0 ]; then
  echo "$fails failed"
  exit 1
fi
echo "all passed"
