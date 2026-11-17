#!/usr/bin/env bash
# The machine check, the correction queue and its hook, the plugin form and the setup script, each
# in a home and a repository of its own, and the personas' row of the machine check.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

# The machine check: a required tool that is absent fails it, an optional one only changes its row.
DOCTOR=$PWD/skills/lem/scripts/doctor.py
BIN=$WORK/bin
FAKEHOME=$WORK/home
# doctor.py reads the repository it runs in (its builder, an install of Lem for it, its personas),
# so the check runs in a repository of its own: nothing of the checkout that runs these tests reaches it.
MACHINE=$WORK/machine-repo
mkdir -p "$BIN" "$FAKEHOME"
git init -q -b main "$MACHINE"
ln -s "$(command -v git)" "$BIN/git"
fake() { printf '#!/bin/sh\necho "%s"\n' "$2" > "$BIN/$1"; chmod +x "$BIN/$1"; }
doctor() { (cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" "$PY" -B "$DOCTOR"); }
row() { field "next(t for t in d[\"tools\"] if t[\"name\"] == \"$1\")[\"$2\"]"; }
out=$(doctor || true)
if [ "$(status_of doctor)" = 1 ] && [ "$(field 'd["ok"]' <<<"$out")" = "False" ] && [ "$(row revmux found <<<"$out")" = "False" ] && [ "$(row git found <<<"$out")" = "True" ] \
  && [ "$(row python3 found <<<"$out")" = "True" ] && [ "$(row python3 need <<<"$out")" = "required" ] && [ "$(row claude found <<<"$out")" = "False" ] && [ "$(row claude need <<<"$out")" = "required" ] \
  && grep -qF "before the pull request" <<<"$(row revmux used_for <<<"$out")" && grep -qF "is not proposed" <<<"$(row revmux without_it <<<"$out")" \
  && ! grep -qiE "landed (range|change)|queue" <<<"$(row revmux used_for <<<"$out") $(row revmux without_it <<<"$out")"; then
  pass "doctor exits 1 and says so when the review tool is absent, its row says the review comes before the pull request and what is not proposed without it, and the agent that runs Lem is a required row"
else
  fail "doctor without revmux: $out"
fi
fake revmux "revmux v9.9.9"
out=$(doctor || true)
if [ "$(status_of doctor)" = 1 ] && [ "$(row revmux detail <<<"$out")" = "revmux v9.9.9" ] && [ "$(row agterm found <<<"$out")" = "False" ] \
  && [ "$(field '[t["name"] for t in d["tools"] if t["name"] == "agterm skill"]' <<<"$out")" = "[]" ] && [ "$(row mailbox-chat need <<<"$out")" = "required" ] \
  && [ "$(row 'revmux skill' found <<<"$out")" = "False" ] && [ "$(row 'revmux skill' need <<<"$out")" = "required" ] && [ "$(row 'mailbox-chat skill' found <<<"$out")" = "False" ]; then
  pass "the review tool alone is not enough: its skill, agterm and the mailbox with its skill are required, and there is no row for the agterm skill without agterm"
else
  fail "doctor with revmux only: $out"
fi
fake agtermctl "agtermctl 1.0"
fake mailbox-chat.py "mailbox-chat"
out=$(doctor || true)
if [ "$(status_of doctor)" = 1 ] && [ "$(row agterm found <<<"$out")" = "True" ] && [ "$(row agterm in_session <<<"$out")" = "False" ] && [ "$(row 'agterm skill' found <<<"$out")" = "False" ]; then
  pass "agterm without its skill fails the check, and a run outside agterm says it is not in a session"
else
  fail "doctor with agterm, no skill: $out"
fi
# The skills an agent needs beside the commands: in a skills folder, or as a plugin the agent installed.
mkdir -p "$FAKEHOME/.agents/skills/agterm" "$FAKEHOME/.agents/skills/mailbox-chat" "$FAKEHOME/.claude/plugins" "$FAKEHOME/.config/cronn"
touch "$FAKEHOME/.agents/skills/agterm/SKILL.md" "$FAKEHOME/.agents/skills/mailbox-chat/SKILL.md"
printf '%s\n' '{"version": 2, "plugins": {"revmux@some-market": [{"scope": "user"}], "other@x": []}}' > "$FAKEHOME/.claude/plugins/installed_plugins.json"
out=$(doctor || true)
if [ "$(status_of doctor)" = 1 ] && [ "$(row 'revmux skill' detail <<<"$out")" = "the plugin revmux@some-market" ] && [ "$(row 'mailbox-chat skill' detail <<<"$out")" = "$FAKEHOME/.agents/skills/mailbox-chat" ] \
  && [ "$(row 'agterm skill' detail <<<"$out")" = "$FAKEHOME/.agents/skills/agterm" ] && [ "$(field '[t["name"] for t in d["tools"] if t["need"] == "required" and not t["found"]]' <<<"$out")" = "['claude']" ]; then
  pass "the skills are found in a skills folder or in the agent's list of plugins, and without Claude Code the check still fails: nothing else runs /lem"
else
  fail "doctor with the skills and no agent: $out"
fi
# The agent's list of plugins in a shape this check does not know is no answer, and no traceback.
shapes=""
for shape in '{"plugins": null}' '{"plugins": 1}' '[]' '{"plugins": {"1": []}}' 'not json' '{"plugins": {"revmux@x": []}}' '{"plugins": {"revmux@x": null}}' '{"plugins": {"revmux@x": [{"scope": "project"}]}}'; do
  printf '%s\n' "$shape" > "$FAKEHOME/.claude/plugins/installed_plugins.json"
  shapes="$shapes$( (doctor 2>&1 || true) | field 'next(t for t in d["tools"] if t["name"] == "revmux skill")["found"]' 2>&1 | tail -1) "
done
rm "$FAKEHOME/.claude/plugins/installed_plugins.json"
gone=$(doctor | field 'next(t for t in d["tools"] if t["name"] == "revmux skill")["found"]' || true)
mkdir -p "$FAKEHOME/.claude/plugins/cache/some-market/revmux/1.2.3/.claude-plugin/skills/revmux" && touch "$FAKEHOME/.claude/plugins/cache/some-market/revmux/1.2.3/.claude-plugin/skills/revmux/SKILL.md"
printf '%s\n' '{"plugins": null}' > "$FAKEHOME/.claude/plugins/installed_plugins.json"
out=$(doctor || true)
rm "$FAKEHOME/.claude/plugins/installed_plugins.json"
if [ "$gone" = "False" ] && [ "$shapes" = "False False False False False False False False " ] && [ "$(row 'revmux skill' detail <<<"$out")" = "$FAKEHOME/.claude/plugins/cache/some-market/revmux/1.2.3/.claude-plugin/skills/revmux" ]; then
  pass "a list of plugins in an unknown shape, or an entry that names no user and no project, is no answer and no traceback; with no list to read the plugin's own folder with the skill in it counts"
else
  fail "doctor with the plugin's folder only: $gone / $out"
fi
fake claude "2.1.325 (Claude Code)"
out=$(doctor || true)
if [ "$(status_of doctor)" = 1 ] && [ "$(row 'lem-builder agent' found <<<"$out")" = "False" ] && [ "$(row 'lem-builder agent' need <<<"$out")" = "required" ]; then
  pass "a machine with Claude Code and no lem-builder agent fails the check"
else
  fail "doctor with claude, no builder: $out"
fi
# A trial's builder is linked into the main checkout and git does not track it: the check run in a task's worktree finds it there.
commit "$MACHINE" start && git -C "$MACHINE" worktree add -q "$WORK/machine-wt" -b a-task
mkdir -p "$MACHINE/.claude/agents" && ln -s "$PWD/agents/lem-builder.md" "$MACHINE/.claude/agents/lem-builder.md"
in_tree=$( (cd "$WORK/machine-wt" && env -i PATH="$BIN" HOME="$FAKEHOME" "$PY" -B "$DOCTOR" || true) | row 'lem-builder agent' detail)
rm -r "$MACHINE/.claude" && git -C "$MACHINE" worktree remove --force "$WORK/machine-wt"
if [ "$in_tree" = "$MACHINE/.claude/agents/lem-builder.md" ] && grep -qF "scripts/setup.py --project DIR" <<<"$(row 'lem-builder agent' without_it <<<"$out")" \
  && [ "$(row agterm without_it <<<"$out")" = "\`/lem\` stops at once: Lem runs inside agterm only" ] && ! grep -q coordinator <<<"$(row mailbox-chat used_for <<<"$out")"; then
  pass "in a task's worktree the check finds the builder a trial linked into the main checkout, and the builder's row names the trial's setup"
else
  fail "the builder of a trial from a worktree: $in_tree / $(row 'lem-builder agent' without_it <<<"$out")"
fi
# Lem installed as a plugin brings the builder too, for the user or for the one repository it was installed in.
printf '%s\n' "{\"version\": 2, \"plugins\": {\"lem@lem\": [{\"scope\": \"project\", \"projectPath\": \"$WORK/another-repository\"}]}}" > "$FAKEHOME/.claude/plugins/installed_plugins.json"
elsewhere=$(doctor | field 'next(t for t in d["tools"] if t["name"] == "lem-builder agent")["found"]' || true)
printf '%s\n' '{"version": 2, "plugins": {"lem@lem": []}}' > "$FAKEHOME/.claude/plugins/installed_plugins.json"
elsewhere="$elsewhere$(doctor | field 'next(t for t in d["tools"] if t["name"] == "lem-builder agent")["found"]' || true)"
printf '%s\n' "{\"version\": 2, \"plugins\": {\"lem@lem\": [{\"scope\": \"project\", \"projectPath\": \"$MACHINE\"}]}}" > "$FAKEHOME/.claude/plugins/installed_plugins.json"
here=$(doctor | field 'next(t for t in d["tools"] if t["name"] == "lem-builder agent")["detail"]' || true)
printf '%s\n' '{"version": 2, "plugins": {"lem@lem": [{"scope": "user"}]}}' > "$FAKEHOME/.claude/plugins/installed_plugins.json"
user=$(doctor | field '(d["ok"], next(t for t in d["tools"] if t["name"] == "lem-builder agent")["found"])' || true)
rm "$FAKEHOME/.claude/plugins/installed_plugins.json"
if [ "$elsewhere" = "FalseFalse" ] && [ "$here" = "lem:lem-builder, from the plugin lem@lem" ] && [ "$user" = "(True, True)" ]; then
  pass "Lem installed as a plugin for the user or for this repository satisfies the builder row, with the name the agent has there; an install for another repository, and an entry with no install in it, do not"
else
  fail "doctor with Lem as a plugin: $elsewhere / $here / $user"
fi
mkdir -p "$FAKEHOME/.claude/agents"
ln -s "$PWD/agents/lem-builder.md" "$FAKEHOME/.claude/agents/lem-builder.md"
out=$(doctor)
if [ "$(field 'd["ok"]' <<<"$out")" = "True" ] && [ "$(row 'lem-builder agent' detail <<<"$out")" = "$FAKEHOME/.claude/agents/lem-builder.md" ] && [ "$(row cronn found <<<"$out")" = "False" ] \
  && [ "$(row plannotator found <<<"$out")" = "False" ] && [ "$(row plannotator need <<<"$out")" = "optional" ] && [ "$(row codex found <<<"$out")" = "False" ] \
  && [ "$(field '[t["name"] for t in d["tools"] if t["name"] == "codex persona agent"]' <<<"$out")" = "[]" ] \
  && [ "$(row plannotator without_it <<<"$out" | grep -c 'webrev is the default')" = 1 ] \
  && [ "$(field '[(t["name"], t["found"], t["guide"].rsplit("/", 1)[1]) for t in d["tools"] if t["need"] == "recommended"]' <<<"$out")" \
    = "[('webrev skill', False, 'annotate-document'), ('agdoc skill', False, 'html-doc-overlay'), ('plannotator-tui', False, 'annotate-in-plannotator-tui')]" ] \
  && [ ! -e "$PWD/skills/lem-webrev" ]; then
  pass "with git, the review tool, agterm, the mailbox, their skills, Claude Code and the linked builder the check passes; absent optional tools only change their rows, and each recommended tool, none of them a part of Lem, has a row with its guide"
else
  fail "doctor with the required set: $out"
fi
keyed=$(cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" OPENROUTER_API_KEY=sk-not-a-real-key "$PY" -B "$DOCTOR")
if [ "$(field '[t["name"] for t in d["tools"] if "lem-ask" in t["name"]]' <<<"$out")" = "[]" ] && [ "$(row 'OpenRouter key' found <<<"$out")" = "False" ] && [ "$(row 'OpenRouter key' need <<<"$out")" = "optional" ] && [ "$(row 'OpenRouter key' found <<<"$keyed")" = "True" ] \
  && ! grep -q "sk-not-a-real-key" <<<"$keyed"; then
  pass "the check has no row for the question page, which is a part of Lem; it says whether the key of the decision model is in the environment, and never prints it"
else
  fail "doctor and the key: $keyed"
fi
fake codex "codex-cli 9.9"
without=$(doctor | field '(next(t for t in d["tools"] if t["name"] == "codex persona agent")["found"], d["ok"])')
mkdir -p "$FAKEHOME/.codex/agents" && touch "$FAKEHOME/.codex/agents/persona.toml"
with=$(doctor | field 'next(t for t in d["tools"] if t["name"] == "codex persona agent")["detail"]')
rm "$BIN/codex"
if [ "$without" = "(False, True)" ] && [ "$with" = "$FAKEHOME/.codex/agents/persona.toml" ]; then
  pass "a machine with Codex gets a row for the agent file a persona panel needs there, and its absence does not fail the check"
else
  fail "doctor and the persona agent of Codex: $without / $with"
fi
if "$PY" -c 'import sys; t = open(sys.argv[1]).read().split("---"); f = dict(l.split(": ", 1) for l in t[1].strip().splitlines()); sys.exit(not (f["name"] == "lem-builder" and f["model"] and f["effort"] and "tools" not in f and len(t[2]) > 500))' "$PWD/agents/lem-builder.md"; then
  pass "the builder's definition names its model and effort, and no tool list, so it can start builders"
else
  fail "agents/lem-builder.md frontmatter"
fi
# The correction queue: off unless the project's settings say yes, filled by the hook, read by the retro.
CORR=$PWD/skills/lem/scripts/corrections.py
CQ=$WORK/corr
git init -q -b main "$CQ" && commit "$CQ" start
project --repo "$CQ" init --base main >/dev/null
if grep -q '^annotate = "webrev"$' "$CQ/.lem/project.toml" && grep -q '^ask = "lem-ask"$' "$CQ/.lem/project.toml" \
  && [ "$(project --repo "$CQ" show | field 'd["tools"]')" = "{'annotate': 'webrev', 'ask': 'lem-ask'}" ]; then
  pass "a new settings file names the recommended tool for marking up and Lem's own page for questions"
else
  fail "the tools of a new settings file: $(grep -n -A8 '^\[tools\]' "$CQ/.lem/project.toml")"
fi
mkdir -p "$WORK/jevbin"
# a stand-in for jev: it answers with the probability in JEV_P, or fails as JEV_EXIT says, and adds
# a line to the file JEV_CALLED names for each call
# shellcheck disable=SC2016  # the stand-in's own variables, expanded when it runs
printf '%s\n' '#!/bin/sh' 'cat > /dev/null' 'if [ -n "$JEV_CALLED" ]; then echo called >> "$JEV_CALLED"; fi' 'if [ -n "$JEV_EXIT" ]; then echo "no key" >&2; exit "$JEV_EXIT"; fi' \
  'printf "{\"answers\": {\"lesson\": {\"probabilities\": {\"lesson\": %s}}}}" "$JEV_P"' > "$WORK/jevbin/jev"
chmod +x "$WORK/jevbin/jev"
printf '%s\n' '{"type": "user", "message": {"content": "hi"}}' '{"type": "assistant", "message": {"content": [{"type": "text", "text": "I pushed it."}]}}' > "$WORK/transcript.jsonl"
event() { printf '{"prompt": "%s", "cwd": "%s", "session_id": "%s", "transcript_path": "%s"}' "$1" "$CQ" "$2" "$WORK/transcript.jsonl"; }
# LEM_JEV in every call: without it the worker runs Lem's own jev.py, which asks a real service.
hook() { env LEM_JEV="$WORK/jevbin/jev" JEV_P="${JEV_P:-0.9}" JEV_EXIT="${JEV_EXIT:-}" JEV_CALLED="$WORK/jev-called" "$PY" -B "$CORR" "$@"; }
worker() {
  printf '{"prompt": "%s", "cwd": "%s", "session": "%s", "transcript": "%s"}' "$1" "$CQ" "$2" "$WORK/transcript.jsonl" > "$WORK/payload.json"
  hook worker "$WORK/payload.json"
}
corr() { "$PY" -B "$CORR" --repo "$CQ" "$@"; }
if [ "$(project --repo "$CQ" show | field 'd["corrections"]["collect"]')" = False ] && grep -q '^collect = false$' "$CQ/.lem/project.toml"; then
  pass "a new project does not collect corrections, and its settings file says where to turn that on"
else
  fail "corrections.collect default"
fi
event "never push without asking" s1 | hook hook
worker "never push without asking" s1
sleep 1
if [ ! -e "$CQ/.git/lem/corrections.jsonl" ] && [ ! -e "$WORK/jev-called" ] && [ ! -e "$WORK/payload.json" ] \
  && [ "$(corr list | field '(d["collect"], d["entries"])')" = "(False, 0)" ]; then
  pass "without the project's yes neither the hook nor its detached half, run alone, sends a message anywhere"
else
  fail "a message was sent without the project's yes"
fi
# The hand-over to the detached half fails (no interpreter can be started): no file with the owner's words stays behind.
sed -i.bak 's/^collect = false$/collect = true/' "$CQ/.lem/project.toml" && rm "$CQ/.lem/project.toml.bak"
mkdir -p "$WORK/hooktmp"
out=$(event "the copy cannot start" s0 | env LEM_JEV="$WORK/jevbin/jev" TMPDIR="$WORK/hooktmp" "$PY" -B -c '
import runpy, sys
script = sys.argv[1]
sys.argv = [script, "hook"]
sys.executable = "/no/such/python"   # the hook starts its copy with this
runpy.run_path(script, run_name="__main__")' "$CORR" 2>&1; echo "exit=$?")
# only the hook's own files count: git may keep a cache of its own in the temp folder
if [ "$out" = "exit=0" ] && [ -z "$(find "$WORK/hooktmp" -name 'lem-correction-*')" ] && grep -q "/no/such/python" "$CQ/.git/lem/corrections.log"; then
  pass "when the detached half cannot start, the hook removes the file with the owner's words and logs the failure"
else
  fail "the hook with a failed hand-over: $out / $(find "$WORK/hooktmp" -name 'lem-correction-*') / $(cat "$CQ/.git/lem/corrections.log" 2>&1)"
fi
rm -f "$CQ/.git/lem/corrections.log"
# The hook's own directory is gone, as a removed worktree's is: the event still names its repository.
mkdir "$WORK/gone"
out=$(cd "$WORK/gone" && rmdir "$WORK/gone" && event "typed in a directory that is gone" s9 | hook hook 2>&1; echo "exit=$?")
soon grep -qs "that is gone" "$CQ/.git/lem/corrections.jsonl"
if [ "$out" = "exit=0" ] && grep -q "that is gone" "$CQ/.git/lem/corrections.jsonl"; then
  pass "a hook whose own directory was removed still exits 0 with no output, and queues the message for the event's repository"
else
  fail "the hook in a removed directory: $out"
fi
rm -f "$CQ/.git/lem/corrections.jsonl" "$WORK/jev-called"
sed -i.bak 's/^collect = true$/collect = false/' "$CQ/.lem/project.toml" && rm "$CQ/.lem/project.toml.bak"
# An input that stays open, and an old python3: the hook returns, with exit 0 and not a word. The
# input stays open 15 seconds, and the hook returns in 10 at most, on a loaded machine too.
started=$SECONDS
out=$(hook hook < <(event "the input stays open" s0; sleep 15) 2>&1; echo "exit=$?")
if [ "$out" = "exit=0" ] && [ $((SECONDS - started)) -lt 10 ]; then
  pass "the hook does not wait for its input to close"
else
  fail "the hook with an open input: $out after $((SECONDS - started))s"
fi
old=""
for candidate in /usr/bin/python3 python3.9 python3.10; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(sys.version_info >= (3, 11))' 2>/dev/null; then old=$candidate; break; fi
done
if [ -n "$old" ]; then
  # run in another repository than the one of the event: the failure belongs in that repository's
  # log, and the one the hook ran in gets none
  git init -q -b main "$WORK/elsewhere"
  out=$(cd "$WORK/elsewhere" && event "under an old python" s0 | "$old" -B "$CORR" hook 2>&1; echo "exit=$?")
  if [ "$out" = "exit=0" ] && grep -q "tomllib" "$CQ/.git/lem/corrections.log" && [ ! -e "$WORK/elsewhere/.git/lem/corrections.log" ]; then
    pass "under a python3 before 3.11 the hook exits 0, prints nothing, and logs the failure in the repository of the message"
  else
    fail "the hook under $old: $out / $(cat "$CQ/.git/lem/corrections.log" 2>&1)"
  fi
  rm -f "$CQ/.git/lem/corrections.log"
  # The other scripts under that python3: a row or one line that says what is needed, and no traceback.
  rows=$(cd "$MACHINE" && "$old" -B "$DOCTOR" 2>&1 || true)
  said=""
  for script in "$PWD/scripts/setup.py" "$PWD/skills/lem/scripts/project.py" "$PWD/skills/lem/scripts/land.py" "$PWD/skills/lem/scripts/stories.py" "$PWD/skills/lem/scripts/board.py"; do
    said="$said$("$old" -B "$script" --help 2>&1 || true)"$'\n'
  done
  # the queue's own commands, which the retro runs: only the hook and its detached half stay silent there
  said="$said$("$old" -B "$CORR" --repo "$CQ" list 2>&1 || true)"$'\n'
  if [ "$(field '(d["ok"], d["tools"][0]["name"], d["tools"][0]["found"])' <<<"$rows")" = "(False, 'python3', False)" ] && [ "$(grep -c "Lem needs Python 3.11 or newer, and this python3 is" <<<"$said")" = 6 ] \
    && ! grep -q Traceback <<<"$rows$said" && [ "$(status_of "$old" -B "$PWD/scripts/setup.py" --check)" = 1 ] && [ "$(status_of "$old" -B "$CORR" --repo "$CQ" list)" = 1 ]; then
    pass "under a python3 before 3.11 the machine check gives its rows with python3 as absent, and every other script says in one line what it needs"
  else
    fail "the scripts under $old: $rows / $said"
  fi
else
  printf 'SKIP the hook under an old python3: none found\n'
fi
sed -i.bak 's/^collect = false$/collect = true/' "$CQ/.lem/project.toml" && rm "$CQ/.lem/project.toml.bak"
out=$(event "never push without asking" s1 | hook hook; echo "exit=$?")
soon test -s "$CQ/.git/lem/corrections.jsonl"
if [ "$out" = "exit=0" ] && [ "$("$PY" -c 'import json, sys; e = json.loads(open(sys.argv[1]).readline()); print(e["owner"], "|", e["previous"], "|", e["p_lesson"], "|", e["session"])' "$CQ/.git/lem/corrections.jsonl")" = "never push without asking | I pushed it. | 0.9 | s1" ]; then
  pass "with the project's yes the hook prints nothing, and its detached half queues the owner's words with the agent message they answer"
else
  fail "the hook: $out / $(cat "$CQ/.git/lem/corrections.jsonl" 2>&1)"
fi
worker "never  push without asking" s2
JEV_P=0.1 worker "ok go on" s3
event "/lem status" s4 | hook hook
event "[peer chat] a message from the other pane" s5 | hook hook
JEV_EXIT=3 worker "a very long message" s6
JEV_EXIT=1 worker "no key here" s7
printf '{"prompt": "a jev that is not there", "cwd": "%s", "session": "s8", "transcript": ""}' "$CQ" > "$WORK/payload.json"
env LEM_JEV="$WORK/no-such-jev" "$PY" -B "$CORR" worker "$WORK/payload.json"
# No LEM_JEV: the worker runs Lem's own jev.py by its path, with a PATH that has no jev. No key is
# set, so the copy stops before it sends anything, and its own words are in the log.
printf '{"prompt": "the copy beside the hook", "cwd": "%s", "session": "s9", "transcript": ""}' "$CQ" > "$WORK/payload.json"
env -u LEM_JEV -u OPENROUTER_API_KEY PATH="$BIN" "$PY" -B "$CORR" worker "$WORK/payload.json"
sleep 1
out=$(corr list)
if [ "$(field '(d["entries"], [(g["entries"], g["sessions"], g["p_lesson_max"]) for g in d["groups"]], d["failures"]["count"])' <<<"$out")" = "(3, [(2, 2, 0.9), (1, 1, None)], 3)" ] \
  && grep -q "no key" "$CQ/.git/lem/corrections.log" && grep -q "jev did not run" "$CQ/.git/lem/corrections.log" \
  && grep -q "jev gave no answer: jev: OPENROUTER_API_KEY is not set" "$CQ/.git/lem/corrections.log"; then
  pass "one sentence from two sessions is one group; a low score, a command and injected text queue nothing; a message too long for Jev is queued unjudged; each failure is in the log and counted; with no other jev named, the worker runs the copy beside it"
else
  fail "the queue: $out / $(cat "$CQ/.git/lem/corrections.log" 2>&1)"
fi
# One person's no, in the main checkout's untracked file: the hook queues nothing, from a worktree too.
before=$(wc -l < "$CQ/.git/lem/corrections.jsonl")
printf '%s\n' '[corrections]' 'collect = false' > "$CQ/.lem/project.local.toml"
shown=$(project --repo "$CQ" show | field '(d["corrections"]["collect"], d["local"]["overrides"])')
rm -f "$WORK/jev-called"
worker "this one says no for themselves" s10
git -C "$CQ" add .lem && git -C "$CQ" -c user.name=t -c user.email=t@t commit -q -m "chore: the settings" && git -C "$CQ" worktree add -q "$WORK/corr-wt" -b side
printf '{"prompt": "from a worktree", "cwd": "%s", "session": "s11", "transcript": ""}' "$WORK/corr-wt" > "$WORK/payload.json"
hook worker "$WORK/payload.json"
printf 'not toml [\n' > "$CQ/.lem/project.local.toml"
worker "a local file that does not read" s12
printf 'corrections = false\n' > "$CQ/.lem/project.local.toml"
worker "a local file with another shape" s13
rm "$CQ/.lem/project.local.toml"
# A repository whose main directory is a bare one: its worktree's no is read from that directory, as project.py reads it.
git clone -q --bare "$CQ" "$WORK/corr-bare.git" && git -C "$WORK/corr-bare.git" worktree add -q "$WORK/corr-bare-wt" main
mkdir -p "$WORK/corr-bare.git/.lem" && printf '%s\n' '[corrections]' 'collect = false' > "$WORK/corr-bare.git/.lem/project.local.toml"
printf '{"prompt": "from the worktree of a bare repository", "cwd": "%s", "session": "s14", "transcript": ""}' "$WORK/corr-bare-wt" > "$WORK/payload.json"
hook worker "$WORK/payload.json"
bare_log=$( (cat "$WORK/corr-bare.git/lem/corrections.log" "$WORK/corr-bare.git/lem/corrections.jsonl" 2>/dev/null || true) | wc -l | tr -d ' ')
if [ "$shown" = "(False, ['corrections.collect'])" ] && [ "$(wc -l < "$CQ/.git/lem/corrections.jsonl")" = "$before" ] && [ ! -e "$WORK/jev-called" ] && [ ! -e "$WORK/corr-wt/.lem/project.local.toml" ] && [ "$bare_log" = 0 ]; then
  pass "one person's no in the machine's own file stops the hook before anything is sent, from a worktree and from the worktree of a bare repository too; a file there that does not read, or has another shape, is a no"
else
  fail "the hook with a local no: $shown / $(wc -l < "$CQ/.git/lem/corrections.jsonl") lines, before $before"
fi
git -C "$CQ" worktree remove --force "$WORK/corr-wt"
gid=$(field 'd["groups"][0]["id"]' <<<"$out")
if [ "$(status_of corr record "$gid" --decision lesson --verdict unasked)" = 1 ] && [ "$(status_of corr record nope --decision not_lesson --verdict unasked)" = 1 ] \
  && [ "$(corr show "$gid" | field 'len(d)')" = 2 ]; then
  pass "a lesson without its sentence and an unknown group are refused, and show gives every entry of a group"
else
  fail "record refusals"
fi
corr record "$gid" --decision lesson --verdict accepted --target skills/lem/stages/land.md --lesson "Never push to a branch the settings do not name." >/dev/null
if [ "$(corr list | field '(d["entries"], len(d["groups"]))')" = "(1, 1)" ] \
  && [ "$(corr lessons | field '[(r["lesson"], r["target"], r["verdict"], r["entries"]) for r in d]')" = "[('Never push to a branch the settings do not name.', 'skills/lem/stages/land.md', 'accepted', 2)]" ]; then
  pass "a recorded group leaves the list, and lessons gives its sentence, its target and how many entries it stood for"
else
  fail "record and lessons: $(corr lessons)"
fi
# Two different messages of one second in one session are two entries: a record of one leaves the other.
printf '%s\n' '{"ts": "2026-01-01T00:00:00Z", "session": "same", "cwd": "x", "owner": "first words", "previous": "", "p_lesson": 0.5}' \
  '{"ts": "2026-01-01T00:00:00Z", "session": "same", "cwd": "x", "owner": "other words", "previous": "", "p_lesson": 0.6}' >> "$CQ/.git/lem/corrections.jsonl"
gid=$(corr list | field 'next(g["id"] for g in d["groups"] if g["owner"] == "first words")')
corr record "$gid" --decision not_lesson --verdict unasked >/dev/null
if [ "$(corr list | field 'sorted(g["owner"] for g in d["groups"])')" = "['a very long message', 'other words']" ]; then
  pass "two messages of one second in one session are two entries, and a record of one leaves the other in the list"
else
  fail "same second, same session: $(corr list)"
fi
# A queue line that was cut off, and a review file that holds a byte that is not UTF-8: named with the file and the line, no traceback.
cp "$CQ/.git/lem/corrections.jsonl" "$WORK/queue.kept"
printf '{"ts": "2026-01-01T00:00:00Z", "sess' >> "$CQ/.git/lem/corrections.jsonl"
cut_line=$(corr list 2>&1 || true)
cut_code=$(status_of corr list)
cp "$WORK/queue.kept" "$CQ/.git/lem/corrections.jsonl"
cp "$CQ/.git/lem/corrections-reviews.jsonl" "$WORK/reviews.kept" && printf 'caf\351\n' >> "$CQ/.git/lem/corrections-reviews.jsonl"
latin_line=$(corr lessons 2>&1 || true)
cp "$WORK/reviews.kept" "$CQ/.git/lem/corrections-reviews.jsonl"
cp "$CQ/.lem/project.toml" "$WORK/corr-settings.kept" && printf '# caf\351\n' >> "$CQ/.lem/project.toml"
latin_settings=$(corr list | field 'd["collect"]' 2>&1 || true)
cp "$WORK/corr-settings.kept" "$CQ/.lem/project.toml"
lines=$(grep -c '' "$CQ/.git/lem/corrections.jsonl")
if [ "$cut_code" = 1 ] && grep -qF "corrections.jsonl:$((lines + 1)) does not read as JSON" <<<"$cut_line" && grep -qF "corrections-reviews.jsonl:" <<<"$latin_line" \
  && grep -qF "is not UTF-8 text" <<<"$latin_line" && [ "$latin_settings" = False ] && ! grep -q Traceback <<<"$cut_line$latin_line$latin_settings"; then
  pass "a queue line that was cut off and a line that is not UTF-8 are named with their file and line, and settings that do not read are a no"
else
  fail "a queue that does not read: $cut_line / $latin_line / $latin_settings"
fi
# Lem's client of Jev: a timeout that is no number and a spec that is not UTF-8 are named, and nothing is sent.
JEVPY=$PWD/skills/lem/scripts/jev.py
printf '%s\n' '{"state": "s", "questions": {"q": {"instructions": "i", "choices": {"a": "x", "b": "y"}}}}' > "$WORK/jev-spec.json"
printf '{"state": "caf\351", "questions": {}}' > "$WORK/jev-latin.json"
soon_timeout=$(env -u OPENROUTER_API_KEY JEV_TIMEOUT=soon "$PY" -B "$JEVPY" check "$WORK/jev-spec.json" 2>&1 || true)
soon_code=$(env -u OPENROUTER_API_KEY JEV_TIMEOUT=soon "$PY" -B "$JEVPY" check "$WORK/jev-spec.json" >/dev/null 2>&1; echo $?)
latin_file=$(env -u OPENROUTER_API_KEY "$PY" -B "$JEVPY" check "$WORK/jev-latin.json" 2>&1 || true)
latin_stdin=$(env -u OPENROUTER_API_KEY "$PY" -B "$JEVPY" check - < "$WORK/jev-latin.json" 2>&1 || true)
checked=$(env -u OPENROUTER_API_KEY JEV_TIMEOUT=30 "$PY" -B "$JEVPY" check "$WORK/jev-spec.json" | field 'd["ok"]' 2>&1 || true)
if [ "$soon_code" = 1 ] && grep -qF "jev: JEV_TIMEOUT='soon' is not a number of seconds above 0" <<<"$soon_timeout" \
  && grep -qF "jev: the spec ($WORK/jev-latin.json) is not UTF-8 text" <<<"$latin_file" && grep -qF "jev: the spec (stdin) is not UTF-8 text" <<<"$latin_stdin" \
  && [ "$checked" = True ] && ! grep -q Traceback <<<"$soon_timeout$latin_file$latin_stdin"; then
  pass "jev names a JEV_TIMEOUT that is no number and a spec that is not UTF-8, from a file or from its input, and exits 1"
else
  fail "jev's refusals: $soon_timeout / $latin_file / $latin_stdin / $checked"
fi
# One message, one judgment: a hook registered in two or three places (the home's settings, the
# repository's, the plugin) starts once for each, at the same moment, and the first copy claims the message.
CL=$WORK/claim
git init -q -b main "$CL" && commit "$CL" start
project --repo "$CL" init --base main >/dev/null
sed -i.bak 's/^collect = false$/collect = true/' "$CL/.lem/project.toml" && rm "$CL/.lem/project.toml.bak"
CLAIMS=$CL/.git/lem/corrections-claims
CALLS=$WORK/claim-calls
claim_event() { printf '{"prompt": "%s", "cwd": "%s", "session_id": "%s", "transcript_path": ""}' "$1" "$CL" "$2"; }
claim_hook() { env LEM_JEV="$WORK/jevbin/jev" JEV_P=0.9 JEV_CALLED="$CALLS" "$PY" -B "$CORR" hook; }
lines_of() { if [ -f "$1" ]; then wc -l < "$1" | tr -d ' '; else echo 0; fi; }
queued() { lines_of "$CL/.git/lem/corrections.jsonl"; }
queued_at_least() { [ "$(queued)" -ge "$1" ]; }
claim_files() { if [ -d "$CLAIMS" ]; then find "$CLAIMS" -type f | grep -c '' || true; else echo 0; fi; }
for _ in 1 2 3; do claim_event "do not push without asking" c1 | claim_hook & done
wait
soon queued_at_least 1
# the copies a guard would have stopped have their own second to arrive
sleep 1
if [ "$(queued)" = 1 ] && [ "$(lines_of "$CALLS")" = 1 ] && [ "$(claim_files)" = 1 ]; then
  pass "three copies of the hook on one message, started at once as three registrations start them, make one call of the model and one queue entry"
else
  fail "three copies of one message: $(queued) entries, $(lines_of "$CALLS") calls, $(claim_files) claims"
fi
# The same words in the same session after the window are a new message: the stale claim is replaced, and
# a stale claim of another message is removed, so that the folder does not grow.
mkdir -p "$CLAIMS" && touch "$CLAIMS/a-stale-claim-of-another-message"
find "$CLAIMS" -type f -exec touch -t 202601010000 {} +
claim_event "do not push without asking" c1 | claim_hook
soon queued_at_least 2
fresh=$("$PY" -c 'import os, sys, time; print([round(time.time() - os.stat(os.path.join(sys.argv[1], f)).st_mtime) < 60 for f in os.listdir(sys.argv[1])])' "$CLAIMS" 2>&1 || true)
if [ "$(queued)" = 2 ] && [ "$(lines_of "$CALLS")" = 2 ] && [ "$fresh" = "[True]" ]; then
  pass "the same words in the same session after the window are judged again, the old claim is replaced, and a stale claim of another message is removed"
else
  fail "the same words after the window: $(queued) entries, $(lines_of "$CALLS") calls, claims $fresh"
fi
# Another message of the same session, and the same words in another session: each is its own message.
# A message with no session id is judged as before, with no claim: nothing tells it from the same words of another session.
claim_event "keep the tests green" c2 | claim_hook
claim_event "keep the tests green, always" c2 | claim_hook
claim_event "keep the tests green" c3 | claim_hook
printf '{"prompt": "a message with no session", "cwd": "%s"}' "$CL" | claim_hook
printf '{"prompt": "a message with no session", "cwd": "%s"}' "$CL" | claim_hook
soon queued_at_least 7
if [ "$(queued)" = 7 ] && [ "$(claim_files)" = 4 ]; then
  pass "two messages of one session, and one sentence of two sessions, each get a claim and an entry; a message with no session id is judged with no claim"
else
  fail "different messages and sessions: $(queued) entries, $(claim_files) claims"
fi
# A claim that cannot be made (here a file stands where its folder goes) never costs the message: it is
# judged as before, and the log says why a second copy could not be stopped.
rm -rf "$CLAIMS" && touch "$CLAIMS"
out=$(claim_event "a claim that cannot be made" c4 | claim_hook 2>&1; echo "exit=$?")
soon queued_at_least 8
claim_failures=$(cd "$CL" && "$PY" -B "$CORR" list | field 'd["failures"]["count"]')
if [ "$out" = "exit=0" ] && [ "$(queued)" = 8 ] && grep -q "could not claim the message" "$CL/.git/lem/corrections.log" && ! grep -q Traceback "$CL/.git/lem/corrections.log" \
  && [ "$claim_failures" = 0 ]; then
  pass "a claim folder that cannot be made still queues the message, with no output, and the log says the message was judged unclaimed, as a note that list does not count as a failure"
else
  fail "a claim that cannot be made: $out / $(queued) entries / $claim_failures failures / $(cat "$CL/.git/lem/corrections.log" 2>&1)"
fi
rm "$CLAIMS"
settings_file=$CQ/.lem/project.toml
sed -i.bak 's/^collect = true$/collect = "yes"/' "$settings_file" && rm "$settings_file.bak"
if [ "$(status_of project --repo "$CQ" show)" = 1 ]; then pass "a collect value that is not true or false is refused"; else fail "collect type"; fi

# The plugin form: the files Claude Code reads to load this repository as the plugin `lem`.
# shellcheck disable=SC2016  # ${CLAUDE_PLUGIN_ROOT} is the text of the hook's command, for Claude Code to fill
if "$PY" -c 'import json, os, sys
root = sys.argv[1]
manifest = json.load(open(f"{root}/.claude-plugin/plugin.json"))
market = json.load(open(f"{root}/.claude-plugin/marketplace.json"))
links = {name: os.path.realpath(f"{root}/bin/{name}") for name in ("lem-ask", "jev")}
ok = (manifest["name"] == "lem" and "version" not in manifest
      and [(p["name"], p["source"]) for p in market["plugins"]] == [("lem", "./")]
      and links == {"lem-ask": os.path.realpath(f"{root}/skills/lem-ask/bin/lem-ask"), "jev": os.path.realpath(f"{root}/skills/lem/scripts/jev.py")}
      and all(os.access(path, os.X_OK) for path in links.values())
      and not os.path.isabs(os.readlink(f"{root}/bin/lem-ask")))
hooks = json.load(open(f"{root}/hooks/hooks.json"))["hooks"]
commands = [h["command"] for group in hooks["UserPromptSubmit"] for h in group["hooks"]]
ok = ok and list(hooks) == ["UserPromptSubmit"] and commands == ["python3 \"${CLAUDE_PLUGIN_ROOT}/skills/lem/scripts/corrections.py\" hook"]
sys.exit(not ok)' "$PWD"; then
  pass "the plugin manifest names lem and no version, so each commit is an update; the marketplace file lists the one plugin; bin/ holds relative links to the two commands; and the one hook that comes with the plugin is the correction hook, by the plugin's own path"
else
  fail "the plugin files in .claude-plugin and bin"
fi
# The setup script: links from the clone into a home, never over something else, and the machine check after them.
SETUP=$PWD/scripts/setup.py
SETHOME=$WORK/sethome
machine_home() { for name in agterm mailbox-chat revmux; do mkdir -p "$1/.agents/skills/$name" && touch "$1/.agents/skills/$name/SKILL.md"; done; }
machine_home "$SETHOME"
setup() { env -i PATH="$BIN" HOME="$SETHOME" "$PY" -B "$SETUP" --home "$SETHOME" "$@"; }
out=$(setup --check 2>/dev/null || true)
if [ "$(status_of setup --check)" = 1 ] && [ "$(field 'sorted(set(l["state"] for l in d["links"]))' <<<"$out")" = "['absent']" ] && [ ! -e "$SETHOME/.claude" ]; then
  pass "setup --check reports every link as absent, exits 1 and makes nothing"
else
  fail "setup --check on an empty home: $out"
fi
mkdir -p "$SETHOME/.claude/skills/lem-backlog"
err=$(setup 2>&1 >/dev/null || true)
if [ "$(status_of setup)" = 1 ] && grep -q "1 place(s) hold something else, and nothing was linked" <<<"$err" && [ ! -e "$SETHOME/.claude/skills/lem" ]; then
  pass "one place that holds something else stops the setup before any link is made"
else
  fail "setup over a taken place: $err"
fi
rmdir "$SETHOME/.claude/skills/lem-backlog" && ln -s "$WORK" "$SETHOME/.claude/skills/lem-backlog"
if [ "$(status_of setup)" = 1 ] && [ ! -e "$SETHOME/.claude/skills/lem" ]; then pass "a link that points somewhere else is in the way too"; else fail "setup over another link"; fi
rm "$SETHOME/.claude/skills/lem-backlog"
out=$(setup)
if [ "$(field '(d["linked"], d["machine_ok"], len(d["links"]), [a["name"] for a in d["absent"] if a["need"] == "required"])' <<<"$out")" = "(True, True, $(( $(find "$PWD/skills" -mindepth 2 -maxdepth 2 -name SKILL.md | grep -c '') + 3 )), [])" ] \
  && [ "$(readlink "$SETHOME/.claude/skills/lem")" = "$PWD/skills/lem" ] && [ "$(readlink "$SETHOME/.claude/agents/lem-builder.md")" = "$PWD/agents/lem-builder.md" ] \
  && [ -x "$SETHOME/.local/bin/lem-ask" ] && [ "$(readlink "$SETHOME/.local/bin/jev")" = "$PWD/skills/lem/scripts/jev.py" ] && [ -x "$SETHOME/.local/bin/jev" ] \
  && [ "$(field 'd["corrections_hook"]["state"]' <<<"$out")" = "not registered" ] && [ ! -e "$SETHOME/.claude/settings.json" ] \
  && [ "$(field 'next(a["guide"] for a in d["absent"] if a["name"] == "webrev skill")' <<<"$out")" = "https://github.com/umputun/agterm/tree/master/cookbook/annotate-document" ] \
  && [ "$(status_of setup)" = 0 ] && [ "$(status_of setup --check)" = 0 ]; then
  pass "setup links every skill, the builder agent and the lem-ask and jev commands, registers no hook, names each absent recommended tool with its guide and installs none, the machine check then passes, and a second run changes nothing"
else
  fail "setup: $out"
fi
# A skill of the clone that got a new name: its old link has nothing at its end, and the next run takes it away.
ln -s "$PWD/skills/lem-old-name" "$SETHOME/.claude/skills/lem-old-name" && ln -s "$PWD/skills/lem-ask/bin/old-name" "$SETHOME/.local/bin/old-name"
ln -s "$WORK/elsewhere" "$SETHOME/.claude/skills/not-lems"
# the owner's own links into the clone, which still end somewhere: an alias for a skill, a command for a script
ln -s "$PWD/skills/lem-ask" "$SETHOME/.claude/skills/my-ask" && ln -s "$PWD/skills/lem/scripts/project.py" "$SETHOME/.local/bin/lem-project"
check=$(setup --check 2>/dev/null || true)
code=$(status_of setup --check)
if [ -L "$SETHOME/.claude/skills/lem-old-name" ]; then code="$code still-there"; fi
out=$(setup)
if [ "$code" = "1 still-there" ] && [ "$(field '(d["linked"], sorted(l["state"] for l in d["leftovers"]))' <<<"$check")" = "(False, ['leftover', 'leftover'])" ] \
  && [ "$(field '(d["linked"], sorted(l["state"] for l in d["leftovers"]))' <<<"$out")" = "(True, ['removed', 'removed'])" ] \
  && [ ! -L "$SETHOME/.claude/skills/lem-old-name" ] && [ ! -L "$SETHOME/.local/bin/old-name" ] && [ -L "$SETHOME/.claude/skills/not-lems" ] \
  && [ -L "$SETHOME/.claude/skills/my-ask" ] && [ -L "$SETHOME/.local/bin/lem-project" ] && [ "$(status_of setup --check)" = 0 ]; then
  pass "a link into the clone with nothing at its end is named by --check and removed by the next run; a link to another place and the owner's own live links into the clone stay"
else
  fail "setup with leftover links: $check / $out"
fi
rm "$SETHOME/.claude/skills/not-lems" "$SETHOME/.claude/skills/my-ask" "$SETHOME/.local/bin/lem-project"
# A link that only ends at the same file by another route is the owner's: a small stand-in clone whose
# agent file is itself a link shows it, and --remove leaves the owner's link alone.
TWIN=$WORK/twin
mkdir -p "$TWIN/scripts" "$TWIN/skills/lem/scripts" "$TWIN/skills/lem-ask/bin" "$TWIN/agents" "$WORK/twinhome/.claude/agents"
cp "$SETUP" "$TWIN/scripts/setup.py" && cp "$DOCTOR" "$TWIN/skills/lem/scripts/doctor.py"
touch "$TWIN/skills/lem/SKILL.md" "$TWIN/skills/lem-ask/SKILL.md" "$TWIN/skills/lem-ask/bin/lem-ask" "$WORK/shared-agent.md"
ln -s "$WORK/shared-agent.md" "$TWIN/agents/lem-builder.md"
ln -s "$WORK/shared-agent.md" "$WORK/twinhome/.claude/agents/lem-builder.md"
twin() { env -i PATH="$BIN" HOME="$WORK/twinhome" "$PY" -B "$TWIN/scripts/setup.py" --home "$WORK/twinhome" "$@"; }
out=$(twin --remove)
if [ "$(field 'next(l["state"] for l in d["links"] if l["place"].endswith("lem-builder.md"))' <<<"$out")" = "other link" ] && [ -L "$WORK/twinhome/.claude/agents/lem-builder.md" ] \
  && [ "$(status_of twin)" = 1 ] && [ ! -e "$WORK/twinhome/.claude/skills" ]; then
  pass "a link of the owner's that ends at the same file by another route is not this clone's: setup stops on it and --remove leaves it"
else
  fail "setup with a shared target: $out"
fi
# A link that cannot be made after others were: the folder for agents is read-only.
rm "$WORK/twinhome/.claude/agents/lem-builder.md" && chmod a-w "$WORK/twinhome/.claude/agents"
out=$(twin 2>"$WORK/twin.err" || true)
chmod u+w "$WORK/twinhome/.claude/agents"
if grep -q "the 2 link(s) this run made are removed again" "$WORK/twin.err" && [ "$(field 'sorted(set(l["state"] for l in d["links"]))' <<<"$out")" = "['absent']" ] \
  && [ -z "$(find "$WORK/twinhome" -type l)" ]; then
  pass "when one link cannot be made, the links of that run are taken away again and the report shows every place as absent"
else
  fail "setup with a link that fails: $out / $(cat "$WORK/twin.err")"
fi
mkdir -p "$WORK/filehome/.claude" && touch "$WORK/filehome/.claude/agents"
out=$(env -i PATH="$BIN" HOME="$WORK/filehome" "$PY" -B "$SETUP" --home "$WORK/filehome" 2>/dev/null || true)
if [ "$(field 'next(l["state"] for l in d["links"] if l["place"].endswith("lem-builder.md")).startswith("blocked by")' <<<"$out")" = True ] && [ ! -e "$WORK/filehome/.claude/skills" ]; then
  pass "a file where a folder has to be is found before any link is made"
else
  fail "setup with a file in the place of a folder: $out"
fi
# A link that cannot be removed: the others go, the report names the one that stays, and the exit is 1.
chmod a-w "$SETHOME/.claude/agents"
out=$(setup --remove 2>"$WORK/remove.err" || true)
chmod u+w "$SETHOME/.claude/agents"
if grep -q "1 link(s) could not be removed and are still there: $SETHOME/.claude/agents/lem-builder.md" "$WORK/remove.err" \
  && [ "$(field 'sorted(set(l["state"] for l in d["links"]))' <<<"$out")" = "['linked', 'removed']" ] && [ -L "$SETHOME/.claude/agents/lem-builder.md" ] && [ ! -e "$SETHOME/.claude/skills/lem" ]; then
  pass "a link that cannot be removed is reported with the ones that went, and the exit is 1"
else
  fail "setup --remove with a link that stays: $out / $(cat "$WORK/remove.err")"
fi
setup >/dev/null
# For a trial, Lem is linked into one repository only: no other repository sees it, and that tree stays clean.
TRIAL=$WORK/trial
git init -q -b main "$TRIAL" && commit "$TRIAL" start
trial() { env -i PATH="$BIN" HOME="$WORK/trialhome" "$PY" -B "$SETUP" --home "$WORK/trialhome" --project "$TRIAL" "$@"; }
machine_home "$WORK/trialhome"
out=$(trial)
if [ "$(field '(d["linked"], d["machine_ok"], d["scope"], d["commands"].startswith("lem-ask and jev are not linked"))' <<<"$out")" = "(True, True, '$TRIAL', True)" ] \
  && [ "$(readlink "$TRIAL/.claude/skills/lem")" = "$PWD/skills/lem" ] && [ "$(readlink "$TRIAL/.claude/agents/lem-builder.md")" = "$PWD/agents/lem-builder.md" ] \
  && [ ! -e "$WORK/trialhome/.claude" ] && [ ! -e "$WORK/trialhome/.local" ] && [ -z "$(git -C "$TRIAL" status --porcelain)" ]; then
  pass "setup --project links Lem into one repository, nothing into the home, the machine check finds that repository's builder, and git sees no new file"
else
  fail "setup --project: $out / $(git -C "$TRIAL" status --porcelain)"
fi
# The ignore files are this checkout's own: a worktree's own file stays visible to git there, and
# another clone's --remove takes away neither a link nor an ignore file.
git -C "$TRIAL" worktree add -q "$WORK/trial-wt" -b feat/trial
mkdir -p "$WORK/trial-wt/.claude/skills/lem" && echo own > "$WORK/trial-wt/.claude/skills/lem/OWN.md"
out=$(env -i PATH="$BIN" HOME="$WORK/trialhome" "$PY" -B "$TWIN/scripts/setup.py" --home "$WORK/trialhome" --project "$TRIAL" --remove)
# the worktree's own file must still show in its status, and the shared exclude file must not name Lem
if git -C "$WORK/trial-wt" status --porcelain | grep -q '.claude/' && ! grep -qs lem "$TRIAL/.git/info/exclude"; then shared=clean; else shared=touched; fi
if [ "$shared" = clean ] && [ "$(field 'sorted(set(l["state"] for l in d["links"]))' <<<"$out")" = "['other link']" ] && [ -L "$TRIAL/.claude/skills/lem" ] \
  && [ -f "$TRIAL/.claude/skills/.gitignore" ] && [ -f "$TRIAL/.claude/agents/.gitignore" ] && [ -z "$(git -C "$TRIAL" status --porcelain)" ]; then
  pass "a trial writes nothing that another worktree shares, and another clone's --remove leaves its links and its ignore files"
else
  fail "the reach of a trial: $out / wt: $(git -C "$WORK/trial-wt" status --porcelain) / main: $(git -C "$TRIAL" status --porcelain)"
fi
# A second repository whose .claude is a link to this one's: its --remove changes nothing here.
git init -q -b main "$WORK/trial-b" && ln -s "$TRIAL/.claude" "$WORK/trial-b/.claude"
out=$(env -i PATH="$BIN" HOME="$WORK/trialhome" "$PY" -B "$SETUP" --home "$WORK/trialhome" --project "$WORK/trial-b" --remove)
if [ "$(field 'all(l["state"].startswith("blocked") for l in d["links"])' <<<"$out")" = True ] && [ -L "$TRIAL/.claude/skills/lem" ] \
  && [ -f "$TRIAL/.claude/skills/.gitignore" ] && [ -f "$TRIAL/.claude/agents/.gitignore" ] && [ -z "$(git -C "$TRIAL" status --porcelain)" ]; then
  pass "--remove through a .claude that is a link into another repository takes away nothing there, not a link and not an ignore file"
else
  fail "setup --project --remove through a linked .claude: $out / $(git -C "$TRIAL" status --porcelain)"
fi
out=$(trial --remove)
if [ "$(field 'sorted(set(l["state"] for l in d["links"]))' <<<"$out")" = "['removed']" ] && [ ! -e "$TRIAL/.claude" ] && [ "$(field '[f.rsplit("/", 2)[-2:] for f in d["folders_removed"]]' <<<"$out")" = "[['trial', '.claude'], ['.claude', 'agents'], ['.claude', 'skills']]" ] \
  && [ "$(status_of env -i PATH="$BIN" HOME="$WORK/trialhome" "$PY" -B "$SETUP" --project "$WORK")" = 1 ]; then
  pass "setup --project --remove takes its links, its ignore files and the folders they leave empty away, and a folder that is no repository is refused"
else
  fail "setup --project --remove: $out / $(find "$TRIAL/.claude")"
fi
# A folder that has an ignore file of its own keeps it, and the result says that git sees the links there.
mkdir -p "$TRIAL/.claude/skills" && echo '# kept by the project' > "$TRIAL/.claude/skills/.gitignore"
out=$(trial)
if [ "$(cat "$TRIAL/.claude/skills/.gitignore")" = "# kept by the project" ] && [ "$(field 'd["git_sees_the_links_in"]' <<<"$out")" = "['$TRIAL/.claude/skills']" ]; then
  pass "an ignore file of the project's own is left as it is, and the result names the folder where git sees the links"
else
  fail "setup --project beside the project's own ignore file: $out"
fi
echo '*' > "$TRIAL/.claude/skills/.gitignore"
out=$(trial)
if [ "$(cat "$TRIAL/.claude/skills/.gitignore")" = "*" ] && [ "$(field 'd["git_sees_the_links_in"]' <<<"$out")" = "[]" ] && [ -z "$(git -C "$TRIAL" status --porcelain)" ]; then
  pass "an ignore file of the project's own that already hides the links is left as it is, and no folder is reported"
else
  fail "setup --project beside an ignore file that hides the links: $out / $(git -C "$TRIAL" status --porcelain)"
fi
# No git on PATH: the script cannot ask, so it reports the folder, gives its whole account and leaves the rest to the machine check.
out=$(env -i PATH="$WORK/nogit-setup" HOME="$WORK/trialhome" "$PY" -B "$SETUP" --home "$WORK/trialhome" --project "$TRIAL" 2>"$WORK/nogit.err" || true)
hook=$(env -i PATH="$WORK/nogit-setup" HOME="$WORK/trialhome" "$PY" -B "$SETUP" --home "$WORK/trialhome" --project "$TRIAL" --corrections on | field 'd["corrections_hook"]["git_sees_the_file"]')
trial --corrections off >/dev/null
if [ "$(field '(d["linked"], d["machine_ok"], d["git_sees_the_links_in"], [a["name"] for a in d["absent"] if a["name"] == "git"])' <<<"$out")" = "(True, False, ['$TRIAL/.claude/skills'], ['git'])" ] \
  && ! grep -q Traceback "$WORK/nogit.err" && [ "$hook" = "True" ]; then
  pass "with no git on PATH the setup still gives its whole account: the folder it could not ask about is reported, and the machine check names git"
else
  fail "setup --project with no git: $out / $(cat "$WORK/nogit.err")"
fi
trial --remove >/dev/null
rm -r "$TRIAL/.claude" && mkdir -p "$WORK/shared-claude" && ln -s "$WORK/shared-claude" "$TRIAL/.claude"
out=$(trial 2>/dev/null || true)
if [ "$(status_of trial)" = 1 ] && [ "$(field 'all(l["state"].startswith("blocked by a link that leaves the repository") for l in d["links"])' <<<"$out")" = True ] \
  && [ -z "$(ls -A "$WORK/shared-claude")" ]; then
  pass "a .claude folder that is a link out of the repository is refused, and nothing is made where it points"
else
  fail "setup --project through a linked .claude: $out / $(ls -A "$WORK/shared-claude")"
fi
rm "$TRIAL/.claude"
touch "$SETHOME/.claude/skills/mine"
out=$(setup --remove)
if [ "$(field 'sorted(set(l["state"] for l in d["links"]))' <<<"$out")" = "['removed']" ] && [ ! -e "$SETHOME/.claude/skills/lem" ] && [ -e "$SETHOME/.claude/skills/mine" ] && [ ! -e "$SETHOME/.local/bin/lem-ask" ] && [ ! -e "$SETHOME/.local/bin/jev" ] \
  && [ ! -e "$SETHOME/.claude/agents" ] && [ ! -e "$SETHOME/.local" ] && [ -d "$SETHOME/.agents/skills/agterm" ]; then
  pass "setup --remove takes away the links it made and the folders they leave empty, and nothing else"
else
  fail "setup --remove: $out"
fi
# The hook of the correction queue: one command in the agent's settings, the owner's step, and nothing else in the file changes.
HOOKHOME=$WORK/hookhome
mkdir -p "$HOOKHOME"
# outside any repository: a hook for the home looks at the repository it runs in, and this checkout is not one to read
hooksetup() { (cd "$HOOKHOME" && env -i PATH="$BIN" HOME="$HOOKHOME" "$PY" -B "$SETUP" --home "$HOOKHOME" "$@"); }
want=$("$PY" -c 'import shlex, sys; print("python3 " + shlex.quote(sys.argv[1]) + " hook")' "$PWD/skills/lem/scripts/corrections.py")
out=$(hooksetup --corrections on)
first=$(cat "$HOOKHOME/.claude/settings.json")
again=$(hooksetup --corrections on)
if [ "$(field '(d["corrections_hook"]["state"], d["corrections_hook"]["changed"], d["corrections_hook"]["command"])' <<<"$out")" = "('registered', True, '$want')" ] \
  && [ "$("$PY" -c 'import json, sys; print(json.load(open(sys.argv[1])))' "$HOOKHOME/.claude/settings.json")" = "{'hooks': {'UserPromptSubmit': [{'hooks': [{'type': 'command', 'command': '$want', 'timeout': 10}]}]}}" ] \
  && [ "$(field 'd["corrections_hook"]["changed"]' <<<"$again")" = "False" ] && [ "$(cat "$HOOKHOME/.claude/settings.json")" = "$first" ] && [ ! -e "$HOOKHOME/.claude/skills" ] \
  && [ "$(hooksetup --check 2>/dev/null | field 'd["corrections_hook"]["state"]')" = "registered" ]; then
  pass "setup --corrections on writes one hook command with the clone's real path, makes no link, a second run changes nothing, and --check reports it"
else
  fail "setup --corrections on: $out / $(cat "$HOOKHOME/.claude/settings.json" 2>&1)"
fi
out=$(hooksetup --corrections off)
if [ "$(field '(d["corrections_hook"]["state"], d["corrections_hook"]["changed"], d["corrections_hook"]["file_removed"])' <<<"$out")" = "('not registered', True, True)" ] && [ ! -e "$HOOKHOME/.claude/settings.json" ] \
  && [ ! -e "$HOOKHOME/.claude" ] && [ "$(hooksetup --corrections off | field 'd["corrections_hook"]["changed"]')" = "False" ]; then
  pass "setup --corrections off takes the hook out, removes a settings file that then holds nothing and the .claude folder that then holds nothing, and a second run changes nothing"
else
  fail "setup --corrections off: $out / $(ls -A "$HOOKHOME")"
fi
# The owner's own settings stay: another key, another hook of the same event, a group that was empty before.
mkdir -p "$WORK/dotfiles" "$HOOKHOME/.claude"
printf '%s\n' '{"model": "opus", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "true"}]}], "UserPromptSubmit": [{"hooks": []}, {"matcher": "", "hooks": [{"type": "command", "command": "echo mine"}]}]}}' > "$WORK/dotfiles/settings.json"
ln -s "$WORK/dotfiles/settings.json" "$HOOKHOME/.claude/settings.json"
before=$("$PY" -c 'import json, sys; print(json.load(open(sys.argv[1])))' "$HOOKHOME/.claude/settings.json")
hooksetup --corrections on >/dev/null
with=$("$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])); print(d["model"], len(d["hooks"]["Stop"]), [len(g["hooks"]) for g in d["hooks"]["UserPromptSubmit"]], d["hooks"]["UserPromptSubmit"][2]["hooks"][0]["command"])' "$HOOKHOME/.claude/settings.json")
hooksetup --corrections off >/dev/null
if [ "$with" = "opus 1 [0, 1, 1] $want" ] && [ -L "$HOOKHOME/.claude/settings.json" ] \
  && [ "$("$PY" -c 'import json, sys; print(json.load(open(sys.argv[1])))' "$HOOKHOME/.claude/settings.json")" = "$before" ]; then
  pass "the hook goes in beside the owner's settings and comes out again with nothing else changed, and a settings file that is a link stays one"
else
  fail "setup --corrections beside other settings: $with / $(cat "$HOOKHOME/.claude/settings.json")"
fi
# A form of the hook that is there already (added by hand, or another clone's) is not doubled, and a file that is not JSON is left alone.
rm "$HOOKHOME/.claude/settings.json"
printf '%s\n' '{"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "LEM_JEV=/x/jev python3 /elsewhere/corrections.py hook", "timeout": 10}]}]}}' > "$HOOKHOME/.claude/settings.json"
kept=$(cat "$HOOKHOME/.claude/settings.json")
err=$(hooksetup --corrections on 2>&1 >/dev/null || true)
state=$( (hooksetup --check 2>/dev/null || true) | field 'd["corrections_hook"]["state"]')
off=$(hooksetup --corrections off | field '(d["corrections_hook"]["state"], d["corrections_hook"]["changed"])')
if [ "$(status_of hooksetup --corrections on)" = 1 ] && grep -q 'already holds the correction hook in another form: {"type": "command", "command": "LEM_JEV=/x/jev python3 /elsewhere/corrections.py hook", "timeout": 10}. Take that entry out' <<<"$err" \
  && [ "$state" = "another form" ] && [ "$off" = "('another form', False)" ] && [ "$(cat "$HOOKHOME/.claude/settings.json")" = "$kept" ]; then
  pass "another form of the hook stops --corrections on, is named, and is not taken out by --corrections off"
else
  fail "setup --corrections over another form: $err / $state / $off"
fi
# This clone's own command with another timeout is another form too: it is not what the script wrote.
"$PY" -c 'import json, sys; print(json.dumps({"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": sys.argv[1], "timeout": 1}]}]}}))' "$want" > "$HOOKHOME/.claude/settings.json"
kept=$(cat "$HOOKHOME/.claude/settings.json")
off=$(hooksetup --corrections off | field '(d["corrections_hook"]["state"], d["corrections_hook"]["changed"])')
if [ "$(status_of hooksetup --corrections on)" = 1 ] && [ "$off" = "('another form', False)" ] && [ "$(cat "$HOOKHOME/.claude/settings.json")" = "$kept" ]; then
  pass "the clone's own command with another timeout is not taken for the script's entry: on refuses it and off leaves it"
else
  fail "setup --corrections over the same command with another timeout: $off / $(cat "$HOOKHOME/.claude/settings.json")"
fi
# A hooks list that Claude Code would not read is the owner's to correct: nothing is written beside it.
shapes=ok
for shape in '{"hooks": {"UserPromptSubmit": [{"matcher": ""}]}}' '{"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command"}]}]}}' '{"hooks": {"UserPromptSubmit": [{"hooks": ["echo"]}]}}' '{"hooks": []}' '[]'; do
  printf '%s\n' "$shape" > "$HOOKHOME/.claude/settings.json"
  if [ "$(status_of hooksetup --corrections on)" != 1 ] || [ "$(status_of hooksetup --corrections off)" != 1 ] || [ "$(cat "$HOOKHOME/.claude/settings.json")" != "$shape" ]; then shapes="$shape"; fi
done
err=$(hooksetup --corrections on 2>&1 >/dev/null || true)
if [ "$shapes" = ok ] && grep -q "does not have the shape of Claude Code's settings" <<<"$err" && grep -q "correct the file, then run this again" <<<"$err"; then
  pass "a settings file whose hooks do not have the shape the agent reads is refused with the fix and left as it is"
else
  fail "setup --corrections over a wrong shape: $shapes / $err"
fi
# A write that fails leaves the file as it was and no draft with the owner's settings beside it.
printf '%s\n' '{"model": "opus"}' > "$HOOKHOME/.claude/settings.json"
chmod a-w "$HOOKHOME/.claude"
err=$(hooksetup --corrections on 2>&1 >/dev/null || true)
code=$(status_of hooksetup --corrections on)
chmod u+w "$HOOKHOME/.claude"
if [ "$code" = 1 ] && grep -q "could not be written" <<<"$err" && grep -q "is as it was; make it writable, then run this again" <<<"$err" && ! grep -q Traceback <<<"$err" \
  && [ "$(cat "$HOOKHOME/.claude/settings.json")" = '{"model": "opus"}' ] && [ "$(find "$HOOKHOME/.claude" -name 'settings.json.lem-*' | grep -c '')" = 0 ]; then
  pass "a settings file that cannot be written is left as it was, with no draft beside it and the fix in the message"
else
  fail "setup --corrections with a write that fails: $err / $(ls -A "$HOOKHOME/.claude")"
fi
printf '%s\n' '{"hooks": // mine' > "$HOOKHOME/.claude/settings.json"
err=$(hooksetup --corrections on 2>&1 >/dev/null || true)
if [ "$(status_of hooksetup --corrections on)" = 1 ] && [ "$(status_of hooksetup --corrections off)" = 1 ] && grep -q "does not read as JSON" <<<"$err" && grep -q "correct the file, then run this again" <<<"$err" \
  && [ "$(cat "$HOOKHOME/.claude/settings.json")" = '{"hooks": // mine' ] && [ "$(hooksetup --check 2>/dev/null | field 'd["corrections_hook"]["state"]')" = "unreadable" ] \
  && [ "$(status_of hooksetup --corrections on --check)" = 1 ]; then
  pass "a settings file that is not JSON is refused with the fix and left as it is, and --corrections goes with no other action"
else
  fail "setup --corrections over a file that is not JSON: $err"
fi
# For one repository the hook goes into that checkout's own settings, and the home is not touched.
out=$(trial --corrections on)
if [ "$(field '(d["corrections_hook"]["state"], d["corrections_hook"]["file"], d["corrections_hook"]["git_sees_the_file"], d["scope"])' <<<"$out")" = "('registered', '$TRIAL/.claude/settings.local.json', True, '$TRIAL')" ] \
  && [ ! -e "$WORK/trialhome/.claude" ] && trial --corrections off >/dev/null && [ ! -e "$TRIAL/.claude/settings.local.json" ] && [ ! -e "$TRIAL/.claude" ] \
  && [ -z "$(git -C "$TRIAL" status --porcelain)" ]; then
  pass "setup --project --corrections on writes the hook into that checkout's local settings, says that git sees the file, and off removes it with the .claude folder it made"
else
  fail "setup --project --corrections: $out / $(git -C "$TRIAL" status --porcelain)"
fi
ln -s "$WORK/shared-claude" "$TRIAL/.claude"
err=$(trial --corrections on 2>&1 >/dev/null || true)
code=$(status_of trial --corrections on)
rm "$TRIAL/.claude" && mkdir "$TRIAL/.claude"
# the folder is the repository's own, and the file in it is a link to a shared one: once to a file that is there, once to none
printf '%s\n' '{"model": "opus"}' > "$WORK/shared-claude/shared.json" && ln -s "$WORK/shared-claude/shared.json" "$TRIAL/.claude/settings.local.json"
code="$code $(status_of trial --corrections on)"
ln -sf "$WORK/shared-claude/none.json" "$TRIAL/.claude/settings.local.json"
code="$code $(status_of trial --corrections on) $(status_of trial --corrections off)"
if [ "$code" = "1 1 1 1" ] && grep -q "is behind a link that leaves the repository" <<<"$err" && [ ! -e "$WORK/shared-claude/settings.local.json" ] \
  && [ "$(cat "$WORK/shared-claude/shared.json")" = '{"model": "opus"}' ] && [ ! -e "$WORK/shared-claude/none.json" ]; then
  pass "the hook of one repository is not written through a .claude folder or a settings file that is a link out of it"
else
  fail "setup --project --corrections through a link out of the repository: $code / $err"
fi
rm -r "$TRIAL/.claude"
# A relative --home names a folder from where the setup starts: the machine check, which runs in the repository of
# --project, gets it whole, so that a tool that writes into its home (`codex --version` makes ~/.codex/tmp) writes
# there and never into the repository.
cp -R "$BIN" "$WORK/homebin"
# shellcheck disable=SC2016  # the fake tool's own $HOME, read when it runs
printf '%s\n' '#!/bin/sh' '/bin/mkdir -p "$HOME/.codex/tmp"' 'echo "codex-cli 9.9"' > "$WORK/homebin/codex" && chmod +x "$WORK/homebin/codex"
machine_home "$WORK/relhome"
relative=$(cd "$WORK" && env -i PATH="$WORK/homebin" HOME="$WORK/elsewhere-home" "$PY" -B "$SETUP" --home relhome --project "$TRIAL" --check 2>&1 || true)
if [ ! -e "$TRIAL/relhome" ] && [ -d "$WORK/relhome/.codex/tmp" ] && [ -z "$(git -C "$TRIAL" status --porcelain --untracked-files=all)" ]; then
  pass "a relative --home is resolved from where the setup starts: the machine check's tools write into that home and nothing into the repository"
else
  fail "setup with a relative --home: $(git -C "$TRIAL" status --porcelain --untracked-files=all) / $relative"
fi
rm -rf "$WORK/homebin" "$WORK/relhome"
# A machine with Claude Code and no git still gets its rows, not a traceback.
mkdir -p "$WORK/nogit" && cp "$BIN/claude" "$WORK/nogit/claude"
out=$(cd "$WORK" && env -i PATH="$WORK/nogit" HOME="$FAKEHOME" "$PY" -B "$DOCTOR" 2>&1 || true)
if [ "$(row git found <<<"$out")" = "False" ] && [ "$(row 'lem-builder agent' found <<<"$out")" = "True" ] && [ "$(field 'd["ok"]' <<<"$out")" = "False" ]; then
  pass "doctor without git reports git as absent and still gives every other row"
else
  fail "doctor without git: $out"
fi
printf 'CRONN_PORT=1\n' > "$FAKEHOME/.config/cronn/cronn.env"
fake cronn "cronn"
out=$(doctor)
if [ "$(row cronn found <<<"$out")" = "True" ] && [ "$(row cronn running <<<"$out")" = "False" ]; then
  pass "an installed cronn that does not answer is reported as not running"
else
  fail "doctor with cronn: $out"
fi
# The correction hook registered in two places for one repository: the machine check names each place and the
# command that takes the extra one out, never says to remove the plugin, and never fails the machine for it.
with_hook() { "$PY" -c 'import json, sys; json.dump({"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": sys.argv[2], "timeout": 10}]}]}, **json.loads(sys.argv[3])}, open(sys.argv[1], "w"))' "$@"; }
hookrow() { doctor | field '[(t["need"], t["found"], t["detail"], t["without_it"], d["ok"]) for t in d["tools"] if t["name"] == "correction hook"]'; }
hookfield() { doctor | field "next(t for t in d[\"tools\"] if t[\"name\"] == \"correction hook\")[\"$1\"]"; }
mkdir -p "$FAKEHOME/.claude" "$MACHINE/.claude"
with_hook "$MACHINE/.claude/settings.local.json" "$want" '{}'
one=$(hookrow)
with_hook "$FAKEHOME/.claude/settings.json" "$want" '{}'
home_detail=$(hookfield detail || true)
home_fix=$(hookfield without_it || true)
home_need=$(doctor | field '[(t["need"], t["found"], d["ok"]) for t in d["tools"] if t["name"] == "correction hook"]' || true)
if [ "$one" = "[]" ] && [ "$home_detail" = "registered 2 times for this repository: $FAKEHOME/.claude/settings.json, $MACHINE/.claude/settings.local.json" ] \
  && grep -qF "Keep one of them, and remove the others: $FAKEHOME/.claude/settings.json: python3 $PWD/scripts/setup.py --corrections off; $MACHINE/.claude/settings.local.json: python3 $PWD/scripts/setup.py --corrections off --project $MACHINE." <<<"$home_fix" \
  && grep -qF "it is still judged once" <<<"$home_fix" && [ "$home_need" = "[('project', False, True)]" ]; then
  pass "the hook in the home's settings and in the repository's is named in one row with the command that removes each, and that row never fails the machine; one place gets no row"
else
  fail "doctor with the hook in two settings files: $one / $home_detail / $home_fix / $home_need"
fi
rm "$FAKEHOME/.claude/settings.json"
printf '%s\n' "{\"version\": 2, \"plugins\": {\"lem@lem\": [{\"scope\": \"project\", \"projectPath\": \"$MACHINE\"}]}}" > "$FAKEHOME/.claude/plugins/installed_plugins.json"
plugin_detail=$(hookfield detail || true)
plugin_fix=$(hookfield without_it || true)
# switched off in the repository's local settings, the plugin brings no hook; and the plugin alone is one place
with_hook "$MACHINE/.claude/settings.local.json" "$want" '{"enabledPlugins": {"lem@lem": false}}'
off=$(hookrow)
rm "$MACHINE/.claude/settings.local.json"
alone=$(hookrow)
# a form added by hand to the repository's shared settings comes out by hand, and the file is committed
with_hook "$MACHINE/.claude/settings.json" "LEM_JEV=/x/jev python3 /elsewhere/corrections.py hook" '{}'
shared_fix=$(hookfield without_it || true)
rm -r "$MACHINE/.claude" "$FAKEHOME/.claude/plugins/installed_plugins.json"
if [ "$plugin_detail" = "registered 2 times for this repository: $MACHINE/.claude/settings.local.json, the plugin lem@lem" ] \
  && grep -qF "The plugin brings the hook, so remove each other place: $MACHINE/.claude/settings.local.json: python3 $PWD/scripts/setup.py --corrections off --project $MACHINE." <<<"$plugin_fix" \
  && ! grep -qi "uninstall" <<<"$plugin_fix" && grep -qF "it does not see managed settings, a session's --settings, or a plugin loaded for one session by a flag" <<<"$plugin_fix" \
  && [ "$off" = "[]" ] && [ "$alone" = "[]" ] \
  && grep -qF "$MACHINE/.claude/settings.json: take the entry out of $MACHINE/.claude/settings.json by hand, and commit that." <<<"$shared_fix"; then
  pass "the hook in a settings file beside Lem's plugin is named with the command that removes the file's entry and never the plugin; a plugin switched off there, or alone, gets no row; an entry the setup did not write comes out by hand"
else
  fail "doctor with the hook beside the plugin: $plugin_detail / $plugin_fix / $off / $alone / $shared_fix"
fi
# The setup registers no second place: not beside the plugin, for one repository or for the home, and not
# for one scope when the other has the hook. Each refusal names the fix, and --corrections off is as before.
homesetup() { (cd "$1" && env -i PATH="$BIN" HOME="$WORK/trialhome" "$PY" -B "$SETUP" --home "$WORK/trialhome" --corrections on); }
mkdir -p "$WORK/trialhome/.claude/plugins"
printf '%s\n' "{\"version\": 2, \"plugins\": {\"lem@lem\": [{\"scope\": \"project\", \"projectPath\": \"$TRIAL\"}]}}" > "$WORK/trialhome/.claude/plugins/installed_plugins.json"
err_project=$(trial --corrections on 2>&1 >/dev/null || true)
codes="$(status_of trial --corrections on)"
err_home=$(homesetup "$WORK" 2>&1 >/dev/null || true)
codes="$codes $(status_of homesetup "$WORK")"
printf '%s\n' '{"version": 2, "plugins": {"lem@lem": [{"scope": "user"}]}}' > "$WORK/trialhome/.claude/plugins/installed_plugins.json"
err_user=$(homesetup "$WORK" 2>&1 >/dev/null || true)
# the move from the links to the plugin: the hook the links registered comes out as before
mkdir -p "$TRIAL/.claude" && with_hook "$TRIAL/.claude/settings.local.json" "$want" '{}'
moved=$(trial --corrections off | field '(d["corrections_hook"]["state"], d["corrections_hook"]["changed"])')
rm "$WORK/trialhome/.claude/plugins/installed_plugins.json"
if [ "$codes" = "1 1" ] && grep -qF "setup.py: the plugin lem@lem is installed for $TRIAL, and nothing was registered. The plugin brings the hook; to turn the queue on, set \`collect = true\` under \`[corrections]\` in the repository's \`.lem/project.toml\` and commit it" <<<"$err_project" \
  && grep -qF "the plugin lem@lem is installed for $TRIAL, where a hook in the home starts too, and nothing was registered" <<<"$err_home" \
  && grep -qF "the plugin lem@lem is installed for the user, where a hook in the home starts too" <<<"$err_user" \
  && [ ! -e "$WORK/trialhome/.claude/settings.json" ] && [ "$moved" = "('not registered', True)" ] && [ ! -e "$TRIAL/.claude" ]; then
  pass "setup --corrections on registers nothing where Lem's plugin brings the hook, for one repository or for the home, and says that the tracked yes turns the queue on; --corrections off still takes out what the links registered"
else
  fail "setup --corrections on beside the plugin: $codes / $err_project / $err_home / $err_user / $moved"
fi
with_hook "$WORK/trialhome/.claude/settings.json" "$want" '{}'
err_home_has=$(trial --corrections on 2>&1 >/dev/null || true)
codes="$(status_of trial --corrections on) $([ -e "$TRIAL/.claude" ] && echo made || echo none)"
rm "$WORK/trialhome/.claude/settings.json"
trial --corrections on >/dev/null
err_repo_has=$(homesetup "$TRIAL" 2>&1 >/dev/null || true)
codes="$codes $(status_of homesetup "$TRIAL") $([ -e "$WORK/trialhome/.claude/settings.json" ] && echo made || echo none)"
trial --corrections off >/dev/null
if [ "$codes" = "1 none 1 none" ] \
  && grep -qF "setup.py: $WORK/trialhome/.claude/settings.json registers the correction hook already, and a hook in the home starts in every repository, $TRIAL too; nothing was registered. Keep that one, or take it out first with \`python3 $PWD/scripts/setup.py --corrections off\`, then run this again" <<<"$err_home_has" \
  && grep -qF "setup.py: $TRIAL/.claude/settings.local.json registers the correction hook for $TRIAL already, and a hook in the home would start there a second time; nothing was registered. Take that one out first with \`python3 $PWD/scripts/setup.py --corrections off --project $TRIAL\`" <<<"$err_repo_has" \
  && [ ! -e "$TRIAL/.claude" ]; then
  pass "setup --corrections on for one repository when the home has the hook, and for the home in a repository that has it, registers nothing and names the place that has it with the command that removes it"
else
  fail "setup --corrections on beside the other scope: $codes / $err_home_has / $err_repo_has"
fi
rm -r "$WORK/trialhome/.claude"
# Every project of Lem has personas: the machine check, run in a repository that has settings, says when
# there are none or one, through the panel's own check, and that row never fails the machine.
PPL=$WORK/people-repo
git init -q -b main "$PPL" && commit "$PPL" start && project --repo "$PPL" init --base main >/dev/null
git -C "$PPL" add -A && commit "$PPL" "chore: the settings" && git -C "$PPL" worktree add -q "$WORK/people-wt" -b before-the-people
people() { (cd "$1" && env -i PATH="$BIN" HOME="$FAKEHOME" "$PY" -B "$DOCTOR" || true) | field '(d["ok"], [(t["need"], t["found"], t["detail"].split(": ")[-1] if t["found"] else t["detail"][:38]) for t in d["tools"] if t["name"] == "project personas"])'; }
none=$(people "$PPL")
mkdir -p "$PPL/.lem/personas" && echo '# The people' > "$PPL/.lem/personas/README.md" && echo '# A merchant' > "$PPL/.lem/personas/merchant.md"
one=$(people "$PPL")
echo '# The engineer on call' > "$PPL/.lem/personas/on-call.md" && git -C "$PPL" add -A && commit "$PPL" "feat: the people"
two=$(people "$PPL")
older=$(people "$WORK/people-wt")
outside=$(doctor | field '[t["name"] for t in d["tools"] if t["name"] == "project personas"]')
if [ "$none" = "(True, [('project', False, 'this project has no personas in .lem/p')])" ] && [ "$one" = "(True, [('project', True, 'a panel needs a second person who would notice other things')])" ] \
  && [ "$two" = "(True, [('project', True, '2 (project, checkout)')])" ] && grep -q "'project', True, '2 (project, main at " <<<"$older" && [ "$outside" = "[]" ] \
  && [ "$(project --repo "$PPL" show | field 'sorted(d["paths"]["personas"])')" = "['exists', 'path']" ]; then
  pass "in a repository that uses Lem the machine check says when the project has no personas or one, finds the cast of a worktree that is older than it, never fails for it, and has no such row anywhere else"
else
  fail "the project's personas: $none / $one / $two / $older / $outside"
fi
git -C "$PPL" worktree remove --force "$WORK/people-wt"

finish
