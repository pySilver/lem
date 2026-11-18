#!/usr/bin/env bash
# The machine check, the correction queue and its hook, and the plugin's files, each
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
# --help prints the usage and exits 0 with no check run; an unknown argument is a usage error, exit 2, with the usage.
helped=$(cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" "$PY" -B "$DOCTOR" --help 2>&1; echo "exit $?")
wrong=$(cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" "$PY" -B "$DOCTOR" --all 2>&1; echo "exit $?")
if [ "$(head -n 1 <<<"$helped")" = "usage: lem doctor [-h]" ] && [ "$(tail -n 1 <<<"$helped")" = "exit 0" ] && ! grep -qF '"tools"' <<<"$helped" \
  && grep -qxF "usage: lem doctor [-h]" <<<"$wrong" && grep -qF "lem doctor: error: unrecognized arguments: --all" <<<"$wrong" && [ "$(tail -n 1 <<<"$wrong")" = "exit 2" ] && ! grep -qF '"tools"' <<<"$wrong"; then
  pass "doctor --help prints its usage and exits 0 with no check run, and an unknown argument exits 2 with the usage"
else
  fail "doctor's arguments: $helped / $wrong"
fi
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
# The GitHub CLI: not on PATH, on PATH and signed out, on PATH and signed in. Its row is optional: a project with no
# GitHub remote never calls it.
gh_row() { (doctor || true) | field '(lambda t: (t["need"], t["found"], t["signed_in"], t["detail"]))(next(t for t in d["tools"] if t["name"] == "gh"))'; }
no_gh=$(gh_row)
# shellcheck disable=SC2016  # the stand-in's own argument, read when it runs
printf '%s\n' '#!/bin/sh' 'case "$1" in --version) echo "gh version 2.80.0" ;; auth) exit 1 ;; esac' > "$BIN/gh" && chmod +x "$BIN/gh"
gh_out=$(gh_row)
# shellcheck disable=SC2016  # the stand-in's own argument, read when it runs
printf '%s\n' '#!/bin/sh' 'case "$1" in --version) echo "gh version 2.80.0" ;; auth) exit 0 ;; esac' > "$BIN/gh"
gh_in=$(gh_row)
rm "$BIN/gh"
if [ "$no_gh" = "('optional', False, False, None)" ] && [ "$gh_out" = "('optional', True, False, 'gh version 2.80.0; not signed in: \`gh auth login\` signs it in')" ] \
  && [ "$gh_in" = "('optional', True, True, 'gh version 2.80.0')" ]; then
  pass "the machine check has a row for gh: not found, found and not signed in with the command that signs it in, or found and signed in"
else
  fail "the gh row: $no_gh / $gh_out / $gh_in"
fi
fake agtermctl "agtermctl 1.0"
fake mailbox-chat.py "mailbox-chat"
out=$(doctor || true)
if [ "$(status_of doctor)" = 1 ] && [ "$(row agterm found <<<"$out")" = "True" ] && [ "$(row agterm in_session <<<"$out")" = "False" ] && [ "$(row 'agterm skill' found <<<"$out")" = "False" ]; then
  pass "agterm without its skill fails the check, and a run outside agterm says it is not in a session"
else
  fail "doctor with agterm, no skill: $out"
fi
# The skills an agent needs beside the commands: in a skills folder, or as a plugin the agent installed. The
# three recipes of the agterm cookbook that Lem needs are skills of the user here; a check below takes them away.
mkdir -p "$FAKEHOME/.agents/skills/agterm" "$FAKEHOME/.agents/skills/mailbox-chat" "$FAKEHOME/.claude/plugins" "$FAKEHOME/.config/cronn"
touch "$FAKEHOME/.agents/skills/agterm/SKILL.md" "$FAKEHOME/.agents/skills/mailbox-chat/SKILL.md"
for recipe in webrev agdoc backlog; do mkdir -p "$FAKEHOME/.claude/skills/$recipe" && touch "$FAKEHOME/.claude/skills/$recipe/SKILL.md"; done
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
# A project's own builder that git does not track is in the main checkout only: the check run in a task's worktree finds it there.
commit "$MACHINE" start && git -C "$MACHINE" worktree add -q "$WORK/machine-wt" -b a-task
mkdir -p "$MACHINE/.claude/agents" && ln -s "$PWD/agents/lem-builder.md" "$MACHINE/.claude/agents/lem-builder.md"
in_tree=$( (cd "$WORK/machine-wt" && env -i PATH="$BIN" HOME="$FAKEHOME" "$PY" -B "$DOCTOR" || true) | row 'lem-builder agent' detail)
rm -r "$MACHINE/.claude" && git -C "$MACHINE" worktree remove --force "$WORK/machine-wt"
if [ "$in_tree" = "$MACHINE/.claude/agents/lem-builder.md" ] && grep -qF "\`claude plugin marketplace add pySilver/lem --scope project\`, then \`claude plugin install lem@lem --scope project\`" <<<"$(row 'lem-builder agent' without_it <<<"$out")" \
  && ! grep -q "setup" <<<"$(row 'lem-builder agent' without_it <<<"$out")" \
  && [ "$(row agterm without_it <<<"$out")" = "\`/lem\` stops at once: Lem runs inside agterm only" ] && ! grep -q coordinator <<<"$(row mailbox-chat used_for <<<"$out")"; then
  pass "in a task's worktree the check finds a project's own builder in the main checkout, and the builder's row names the plugin's install and no setup"
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
# A plugin loaded for one session by a flag is in no list of installs: the session's CLAUDE_PLUGIN_ROOT finds it, when that
# folder holds the builder; a folder without one finds nothing, and the row says what such a session has all the same.
flagged() { (cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" CLAUDE_PLUGIN_ROOT="$1" "$PY" -B "$DOCTOR" || true) | field 'next((t["found"], t["detail"]) for t in d["tools"] if t["name"] == "lem-builder agent")'; }
by_flag=$(flagged "$PWD")
other_plugin=$(flagged "$WORK")
said=$(doctor | row 'lem-builder agent' without_it || true)
if [ "$by_flag" = "(True, 'lem:lem-builder, from the plugin loaded for this session ($PWD)')" ] && [ "$other_plugin" = "(False, None)" ] \
  && grep -qF "A session that loaded the plugin by a flag (\`claude --plugin-dir DIR\`) has the builder as lem:lem-builder all the same: this check finds such a plugin only through CLAUDE_PLUGIN_ROOT" <<<"$said"; then
  pass "a plugin loaded for one session by a flag satisfies the builder row through CLAUDE_PLUGIN_ROOT when its folder holds the builder, and the row says so; another plugin's folder does not, and the row's words name that case"
else
  fail "doctor with the plugin loaded by a flag: $by_flag / $other_plugin / $said"
fi
# A builder file in the home is no builder of Lem's: the plugin brings it. From here on the plugin is installed for the user.
mkdir -p "$FAKEHOME/.claude/agents"
ln -s "$PWD/agents/lem-builder.md" "$FAKEHOME/.claude/agents/lem-builder.md"
home_only=$(doctor | field '(d["ok"], next(t for t in d["tools"] if t["name"] == "lem-builder agent")["found"])' || true)
rm -r "$FAKEHOME/.claude/agents"
printf '%s\n' '{"version": 2, "plugins": {"lem@lem": [{"scope": "user"}]}}' > "$FAKEHOME/.claude/plugins/installed_plugins.json"
# The three recipes of the agterm cookbook that Lem needs are required, each with its guide: webrev and agdoc as
# skills of the user, the backlog as a skill of the user or of the repository.
recipes() { (doctor || true) | field '(d["ok"], [(t["name"], t["found"], t["guide"].rsplit("/", 1)[1]) for t in d["tools"] if t["name"] in ("webrev skill", "agdoc skill", "backlog skill")], [t["need"] for t in d["tools"] if t["name"] in ("webrev skill", "agdoc skill", "backlog skill")])'; }
mv "$FAKEHOME/.claude/skills" "$WORK/skills-away"
none_yet=$(recipes)
mkdir -p "$FAKEHOME/.claude/skills" "$MACHINE/.claude/skills/backlog" && mv "$WORK/skills-away/webrev" "$WORK/skills-away/agdoc" "$FAKEHOME/.claude/skills/"
touch "$MACHINE/.claude/skills/backlog/SKILL.md"
in_project=$( (doctor || true) | row 'backlog skill' detail)
rm -r "$MACHINE/.claude" && mv "$WORK/skills-away/backlog" "$FAKEHOME/.claude/skills/" && rmdir "$WORK/skills-away"
for_user=$( (doctor || true) | row 'backlog skill' detail)
if [ "$none_yet" = "(False, [('webrev skill', False, 'annotate-document'), ('agdoc skill', False, 'html-doc-overlay'), ('backlog skill', False, 'backlog-picker')], ['required', 'required', 'required'])" ] \
  && [ "$in_project" = "$MACHINE/.claude/skills/backlog" ] && [ "$for_user" = "$FAKEHOME/.claude/skills/backlog" ]; then
  pass "webrev, agdoc and the backlog recipe are required, each with its guide, and the backlog's skill counts for the user or for the repository"
else
  fail "the recipes Lem needs: $none_yet / $in_project / $for_user"
fi
out=$(doctor)
if [ "$home_only" = "(False, False)" ] && [ "$(field 'd["ok"]' <<<"$out")" = "True" ] && [ "$(field '[t["name"] for t in d["tools"] if "jev" in t["name"]]' <<<"$out")" = "[]" ] && [ "$(row 'lem-builder agent' detail <<<"$out")" = "lem:lem-builder, from the plugin lem@lem" ] && [ "$(row cronn found <<<"$out")" = "False" ] \
  && [ "$(row plannotator found <<<"$out")" = "False" ] && [ "$(row plannotator need <<<"$out")" = "optional" ] && [ "$(row codex found <<<"$out")" = "False" ] \
  && [ "$(field '[t["name"] for t in d["tools"] if t["name"] == "codex persona agent"]' <<<"$out")" = "[]" ] \
  && [ "$(row plannotator without_it <<<"$out" | grep -c 'webrev is the default')" = 1 ] \
  && [ "$(field '[(t["name"], t["found"], t["guide"].rsplit("/", 1)[1]) for t in d["tools"] if t["need"] == "recommended"]' <<<"$out")" \
    = "[('plannotator-tui', False, 'annotate-in-plannotator-tui')]" ] \
  && [ ! -e "$PWD/skills/lem-webrev" ]; then
  pass "a builder file in the home is not Lem's; with git, the review tool, agterm, the mailbox, the cookbook's recipes, their skills, Claude Code and Lem's plugin the check passes; absent optional tools only change their rows, the recommended tool, no part of Lem, has a row with its guide, and no row speaks of a jev command"
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
if [ ! -e "$CQ/.lem/state/corrections.jsonl" ] && [ ! -e "$WORK/jev-called" ] && [ ! -e "$WORK/payload.json" ] \
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
if [ "$out" = "exit=0" ] && [ -z "$(find "$WORK/hooktmp" -name 'lem-correction-*')" ] && grep -q "/no/such/python" "$CQ/.lem/state/corrections.log"; then
  pass "when the detached half cannot start, the hook removes the file with the owner's words and logs the failure"
else
  fail "the hook with a failed hand-over: $out / $(find "$WORK/hooktmp" -name 'lem-correction-*') / $(cat "$CQ/.lem/state/corrections.log" 2>&1)"
fi
rm -f "$CQ/.lem/state/corrections.log"
# The hook's own directory is gone, as a removed worktree's is: the event still names its repository.
mkdir "$WORK/gone"
out=$(cd "$WORK/gone" && rmdir "$WORK/gone" && event "typed in a directory that is gone" s9 | hook hook 2>&1; echo "exit=$?")
soon grep -qs "that is gone" "$CQ/.lem/state/corrections.jsonl"
if [ "$out" = "exit=0" ] && grep -q "that is gone" "$CQ/.lem/state/corrections.jsonl"; then
  pass "a hook whose own directory was removed still exits 0 with no output, and queues the message for the event's repository"
else
  fail "the hook in a removed directory: $out"
fi
rm -f "$CQ/.lem/state/corrections.jsonl" "$WORK/jev-called"
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
  if [ "$out" = "exit=0" ] && grep -q "tomllib" "$CQ/.lem/state/corrections.log" && [ ! -e "$WORK/elsewhere/.lem/state/corrections.log" ]; then
    pass "under a python3 before 3.11 the hook exits 0, prints nothing, and logs the failure in the repository of the message"
  else
    fail "the hook under $old: $out / $(cat "$CQ/.lem/state/corrections.log" 2>&1)"
  fi
  rm -f "$CQ/.lem/state/corrections.log"
  # The other scripts under that python3: a row or one line that says what is needed, and no traceback.
  rows=$(cd "$MACHINE" && "$old" -B "$DOCTOR" 2>&1 || true)
  said=""
  for script in "$PWD/skills/lem/scripts/project.py" "$PWD/skills/lem/scripts/land.py" "$PWD/skills/lem/scripts/criteria.py" "$PWD/skills/lem/scripts/board.py"; do
    said="$said$("$old" -B "$script" --help 2>&1 || true)"$'\n'
  done
  # the queue's own commands, which the retro runs: only the hook and its detached half stay silent there
  said="$said$("$old" -B "$CORR" --repo "$CQ" list 2>&1 || true)"$'\n'
  if [ "$(field '(d["ok"], d["tools"][0]["name"], d["tools"][0]["found"])' <<<"$rows")" = "(False, 'python3', False)" ] && [ "$(grep -c "Lem needs Python 3.11 or newer, and this python3 is" <<<"$said")" = 5 ] \
    && ! grep -q Traceback <<<"$rows$said" && [ "$(status_of "$old" -B "$CORR" --repo "$CQ" list)" = 1 ]; then
    pass "under a python3 before 3.11 the machine check gives its rows with python3 as absent, and every other script says in one line what it needs"
  else
    fail "the scripts under $old: $rows / $said"
  fi
else
  printf 'SKIP the hook under an old python3: none found\n'
fi
sed -i.bak 's/^collect = false$/collect = true/' "$CQ/.lem/project.toml" && rm "$CQ/.lem/project.toml.bak"
out=$(event "never push without asking" s1 | hook hook; echo "exit=$?")
soon test -s "$CQ/.lem/state/corrections.jsonl"
if [ "$out" = "exit=0" ] && [ "$("$PY" -c 'import json, sys; e = json.loads(open(sys.argv[1]).readline()); print(e["owner"], "|", e["previous"], "|", e["p_lesson"], "|", e["session"])' "$CQ/.lem/state/corrections.jsonl")" = "never push without asking | I pushed it. | 0.9 | s1" ]; then
  pass "with the project's yes the hook prints nothing, and its detached half queues the owner's words with the agent message they answer"
else
  fail "the hook: $out / $(cat "$CQ/.lem/state/corrections.jsonl" 2>&1)"
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
  && grep -q "no key" "$CQ/.lem/state/corrections.log" && grep -q "jev did not run" "$CQ/.lem/state/corrections.log" \
  && grep -q "jev gave no answer: lem-jev: OPENROUTER_API_KEY is not set" "$CQ/.lem/state/corrections.log"; then
  pass "one sentence from two sessions is one group; a low score, a command and injected text queue nothing; a message too long for Jev is queued unjudged; each failure is in the log and counted; with no other jev named, the worker runs the copy beside it"
else
  fail "the queue: $out / $(cat "$CQ/.lem/state/corrections.log" 2>&1)"
fi
# One person's no, in the main checkout's untracked file: the hook queues nothing, from a worktree too.
before=$(wc -l < "$CQ/.lem/state/corrections.jsonl")
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
bare_log=$( (cat "$WORK/corr-bare.lem/state/corrections.log" "$WORK/corr-bare.lem/state/corrections.jsonl" 2>/dev/null || true) | wc -l | tr -d ' ')
if [ "$shown" = "(False, ['corrections.collect'])" ] && [ "$(wc -l < "$CQ/.lem/state/corrections.jsonl")" = "$before" ] && [ ! -e "$WORK/jev-called" ] && [ ! -e "$WORK/corr-wt/.lem/project.local.toml" ] && [ "$bare_log" = 0 ]; then
  pass "one person's no in the machine's own file stops the hook before anything is sent, from a worktree and from the worktree of a bare repository too; a file there that does not read, or has another shape, is a no"
else
  fail "the hook with a local no: $shown / $(wc -l < "$CQ/.lem/state/corrections.jsonl") lines, before $before"
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
  '{"ts": "2026-01-01T00:00:00Z", "session": "same", "cwd": "x", "owner": "other words", "previous": "", "p_lesson": 0.6}' >> "$CQ/.lem/state/corrections.jsonl"
gid=$(corr list | field 'next(g["id"] for g in d["groups"] if g["owner"] == "first words")')
corr record "$gid" --decision not_lesson --verdict unasked >/dev/null
if [ "$(corr list | field 'sorted(g["owner"] for g in d["groups"])')" = "['a very long message', 'other words']" ]; then
  pass "two messages of one second in one session are two entries, and a record of one leaves the other in the list"
else
  fail "same second, same session: $(corr list)"
fi
# A queue line that was cut off, and a review file that holds a byte that is not UTF-8: named with the file and the line, no traceback.
cp "$CQ/.lem/state/corrections.jsonl" "$WORK/queue.kept"
printf '{"ts": "2026-01-01T00:00:00Z", "sess' >> "$CQ/.lem/state/corrections.jsonl"
cut_line=$(corr list 2>&1 || true)
cut_code=$(status_of corr list)
cp "$WORK/queue.kept" "$CQ/.lem/state/corrections.jsonl"
cp "$CQ/.lem/state/corrections-reviews.jsonl" "$WORK/reviews.kept" && printf 'caf\351\n' >> "$CQ/.lem/state/corrections-reviews.jsonl"
latin_line=$(corr lessons 2>&1 || true)
cp "$WORK/reviews.kept" "$CQ/.lem/state/corrections-reviews.jsonl"
cp "$CQ/.lem/project.toml" "$WORK/corr-settings.kept" && printf '# caf\351\n' >> "$CQ/.lem/project.toml"
latin_settings=$(corr list | field 'd["collect"]' 2>&1 || true)
cp "$WORK/corr-settings.kept" "$CQ/.lem/project.toml"
lines=$(grep -c '' "$CQ/.lem/state/corrections.jsonl")
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
if [ "$soon_code" = 1 ] && grep -qF "lem-jev: JEV_TIMEOUT='soon' is not a number of seconds above 0" <<<"$soon_timeout" \
  && grep -qF "lem-jev: the spec ($WORK/jev-latin.json) is not UTF-8 text" <<<"$latin_file" && grep -qF "lem-jev: the spec (stdin) is not UTF-8 text" <<<"$latin_stdin" \
  && [ "$checked" = True ] && ! grep -q Traceback <<<"$soon_timeout$latin_file$latin_stdin"; then
  pass "lem-jev names a JEV_TIMEOUT that is no number and a spec that is not UTF-8, from a file or from its input, and exits 1"
else
  fail "jev's refusals: $soon_timeout / $latin_file / $latin_stdin / $checked"
fi
# One message, one judgment: a hook registered in two or three places (the home's settings, the
# repository's, the plugin) starts once for each, at the same moment, and the first copy claims the message.
CL=$WORK/claim
git init -q -b main "$CL" && commit "$CL" start
project --repo "$CL" init --base main >/dev/null
sed -i.bak 's/^collect = false$/collect = true/' "$CL/.lem/project.toml" && rm "$CL/.lem/project.toml.bak"
CLAIMS=$CL/.lem/state/corrections-claims
CALLS=$WORK/claim-calls
claim_event() { printf '{"prompt": "%s", "cwd": "%s", "session_id": "%s", "transcript_path": ""}' "$1" "$CL" "$2"; }
claim_hook() { env LEM_JEV="$WORK/jevbin/jev" JEV_P=0.9 JEV_CALLED="$CALLS" "$PY" -B "$CORR" hook; }
lines_of() { if [ -f "$1" ]; then wc -l < "$1" | tr -d ' '; else echo 0; fi; }
queued() { lines_of "$CL/.lem/state/corrections.jsonl"; }
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
if [ "$out" = "exit=0" ] && [ "$(queued)" = 8 ] && grep -q "could not claim the message" "$CL/.lem/state/corrections.log" && ! grep -q Traceback "$CL/.lem/state/corrections.log" \
  && [ "$claim_failures" = 0 ]; then
  pass "a claim folder that cannot be made still queues the message, with no output, and the log says the message was judged unclaimed, as a note that list does not count as a failure"
else
  fail "a claim that cannot be made: $out / $(queued) entries / $claim_failures failures / $(cat "$CL/.lem/state/corrections.log" 2>&1)"
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
links = {name: os.path.realpath(f"{root}/bin/{name}") for name in ("lem-ask", "lem-jev")}
ok = (manifest["name"] == "lem" and "version" not in manifest
      and [(p["name"], p["source"]) for p in market["plugins"]] == [("lem", "./")]
      and links == {"lem-ask": os.path.realpath(f"{root}/skills/lem-ask/bin/lem-ask"), "lem-jev": os.path.realpath(f"{root}/skills/lem/scripts/jev.py")}
      and sorted(os.listdir(f"{root}/bin")) == ["lem", "lem-ask", "lem-jev"] and not os.path.exists(f"{root}/scripts/setup.py")
      and os.path.isfile(f"{root}/bin/lem") and not os.path.islink(f"{root}/bin/lem") and os.access(f"{root}/bin/lem", os.X_OK)
      and all(os.access(path, os.X_OK) for path in links.values())
      and not os.path.isabs(os.readlink(f"{root}/bin/lem-ask")))
hooks = json.load(open(f"{root}/hooks/hooks.json"))["hooks"]
commands = [h["command"] for group in hooks["UserPromptSubmit"] for h in group["hooks"]]
ok = ok and list(hooks) == ["UserPromptSubmit"] and commands == ["python3 \"${CLAUDE_PLUGIN_ROOT}/skills/lem/scripts/corrections.py\" hook"]
sys.exit(not ok)' "$PWD"; then
  pass "the plugin manifest names lem and no version, so each commit is an update; the marketplace file lists the one plugin; bin/ holds the command lem, a file of its own, and relative links to the two commands lem-ask and lem-jev, and no plain jev; there is no setup script; and the one hook that comes with the plugin is the correction hook, by the plugin's own path"
else
  fail "the plugin files in .claude-plugin and bin"
fi
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
# The correction hook comes with Lem's plugin. A settings file that still holds the hook an older install of Lem
# wrote is a second place: the machine check names each file with the entry to delete from it by hand, never says
# to remove the plugin, and never fails the machine for it.
want=$("$PY" -c 'import shlex, sys; print("python3 " + shlex.quote(sys.argv[1]) + " hook")' "$PWD/skills/lem/scripts/corrections.py")
with_hook() { "$PY" -c 'import json, sys; json.dump({"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": sys.argv[2], "timeout": 10}]}]}, **json.loads(sys.argv[3])}, open(sys.argv[1], "w"))' "$@"; }
entry_of() { "$PY" -c 'import json, sys; print(json.dumps({"type": "command", "command": sys.argv[1], "timeout": 10}))' "$1"; }
hookrow() { doctor | field '[(t["need"], t["found"], t["detail"], t["without_it"], d["ok"]) for t in d["tools"] if t["name"] == "correction hook"]'; }
hookfield() { doctor | field "next(t for t in d[\"tools\"] if t[\"name\"] == \"correction hook\")[\"$1\"]"; }
mkdir -p "$FAKEHOME/.claude" "$MACHINE/.claude"
alone=$(hookrow)
with_hook "$MACHINE/.claude/settings.local.json" "$want" '{}'
plugin_detail=$(hookfield detail || true)
plugin_fix=$(hookfield without_it || true)
plugin_need=$(doctor | field '[(t["need"], t["found"], d["ok"]) for t in d["tools"] if t["name"] == "correction hook"]' || true)
with_hook "$FAKEHOME/.claude/settings.json" "$want" '{}'
three=$(hookfield detail || true)
rm "$FAKEHOME/.claude/settings.json"
# switched off in the repository's local settings, the plugin brings no hook, and the file's entry is the one place
with_hook "$MACHINE/.claude/settings.local.json" "$want" '{"enabledPlugins": {"lem@lem": false}}'
off=$(hookrow)
rm "$MACHINE/.claude/settings.local.json"
# a form added by hand to the repository's shared settings comes out by hand, and the file is committed
with_hook "$MACHINE/.claude/settings.json" "LEM_JEV=/x/jev python3 /elsewhere/corrections.py hook" '{}'
shared_fix=$(hookfield without_it || true)
rm -r "$MACHINE/.claude"
if [ "$alone" = "[]" ] && [ "$plugin_detail" = "registered 2 times for this repository: $MACHINE/.claude/settings.local.json, the plugin lem@lem" ] \
  && grep -qF "The plugin brings the hook, so remove each other place: $MACHINE/.claude/settings.local.json: delete the entry $(entry_of "$want") from the UserPromptSubmit hooks of $MACHINE/.claude/settings.local.json by hand." <<<"$plugin_fix" \
  && grep -qF "it is still judged once" <<<"$plugin_fix" && ! grep -qi "uninstall\|setup" <<<"$plugin_fix" \
  && grep -qF "it does not see managed settings, a session's --settings, or a plugin loaded for one session by a flag" <<<"$plugin_fix" \
  && [ "$plugin_need" = "[('project', False, True)]" ] \
  && [ "$three" = "registered 3 times for this repository: $FAKEHOME/.claude/settings.json, $MACHINE/.claude/settings.local.json, the plugin lem@lem" ] && [ "$off" = "[]" ] \
  && grep -qF "$MACHINE/.claude/settings.json: delete the entry $(entry_of "LEM_JEV=/x/jev python3 /elsewhere/corrections.py hook") from the UserPromptSubmit hooks of $MACHINE/.claude/settings.json by hand, and commit that." <<<"$shared_fix"; then
  pass "a settings file that still holds the hook beside Lem's plugin is named with the entry to delete from it by hand, never the plugin, and never fails the machine; the plugin alone, or switched off there, gets no row; an entry in the shared settings is a change to commit"
else
  fail "doctor with the hook beside the plugin: $alone / $plugin_detail / $plugin_fix / $plugin_need / $three / $off / $shared_fix"
fi
# With no plugin, two settings files that hold the hook are both an older install's: the row says that the hook comes with the plugin.
mv "$FAKEHOME/.claude/plugins/installed_plugins.json" "$WORK/installed.kept"
mkdir -p "$MACHINE/.claude"
with_hook "$MACHINE/.claude/settings.local.json" "$want" '{}'
with_hook "$FAKEHOME/.claude/settings.json" "$want" '{}'
no_plugin=$(hookfield without_it || true)
no_plugin_need=$(doctor | field '[(t["need"], t["found"]) for t in d["tools"] if t["name"] == "correction hook"]' || true)
rm -r "$MACHINE/.claude" "$FAKEHOME/.claude/settings.json"
mv "$WORK/installed.kept" "$FAKEHOME/.claude/plugins/installed_plugins.json"
if grep -qF "The hook comes with Lem's plugin: install it, and remove each of these: $FAKEHOME/.claude/settings.json: delete the entry" <<<"$no_plugin" \
  && [ "$no_plugin_need" = "[('project', False)]" ]; then
  pass "with no plugin, the hook in two settings files is named with the plugin that brings it now and the entry to delete from each"
else
  fail "doctor with the hook in two settings files and no plugin: $no_plugin / $no_plugin_need"
fi
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
  && [ "$(project --repo "$PPL" show | field 'sorted(d["places"]["personas"])')" = "['exists', 'path']" ]; then
  pass "in a repository that uses Lem the machine check says when the project has no personas or one, finds the cast of a worktree that is older than it, never fails for it, and has no such row anywhere else"
else
  fail "the project's personas: $none / $one / $two / $older / $outside"
fi
git -C "$PPL" worktree remove --force "$WORK/people-wt"

# Without Codex the codex row says what a task loses: the reviewer's other family, the second expert, half of a panel.
codexless=$(doctor | row codex without_it)
if grep -qF "an expert whose seat names codex (the second of seats.experts by default, GPT-6 Astra) does not answer" <<<"$codexless" \
  && grep -qF "its pull request is not green for it" <<<"$codexless" && grep -qF "a persona panel has the answers of one model family" <<<"$codexless"; then
  pass "with no Codex the codex row says that the reviewer is a second Claude, that the second expert does not answer so a choice ends not green, and that a panel has one model family"
else
  fail "the codex row without codex: $codexless"
fi
# The permission mode a builder in the background meets: the repository's local settings first, then its shared ones,
# then the user's; auto and bypassPermissions count from the user's only. The row never fails the machine.
mode() { (cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" "$PY" -B "$DOCTOR" || true) | field '[(t["need"], t["found"], t["detail"], t["without_it"][:44]) for t in d["tools"] if t["name"] == "permission mode"]'; }
mkdir -p "$MACHINE/.claude"
rm -f "$FAKEHOME/.claude/settings.json"
plain=$(mode)
printf '%s\n' '{"permissions": {"defaultMode": "acceptEdits"}}' > "$MACHINE/.claude/settings.json"
shared=$(mode)
printf '%s\n' '{"permissions": {"defaultMode": "bypassPermissions"}}' > "$MACHINE/.claude/settings.local.json"
local_bypass=$(mode)
printf '%s\n' '{"permissions": {"defaultMode": "auto"}}' > "$FAKEHOME/.claude/settings.json"
rm "$MACHINE/.claude/settings.json"
user_auto=$(mode)
rm -r "$MACHINE/.claude" "$FAKEHOME/.claude/settings.json"
outside=$( (cd "$WORK" && env -i PATH="$BIN" HOME="$FAKEHOME" "$PY" -B "$DOCTOR" || true) | field '[t["name"] for t in d["tools"] if t["name"] == "permission mode"]')
if [ "$plain" = "[('project', False, 'default: no settings file names one', 'each command the allow list does not hold as')]" ] \
  && [ "$shared" = "[('project', False, 'acceptEdits, from $MACHINE/.claude/settings.json', 'an edit goes through, and each other command')]" ] \
  && [ "$local_bypass" = "$shared" ] \
  && [ "$user_auto" = "[('project', True, 'auto, from $FAKEHOME/.claude/settings.json', 'a builder asks nobody; the classifier may st')]" ] \
  && [ "$outside" = "[]" ]; then
  pass "the machine check says the permission mode a builder meets in the repository, from its local settings, its shared ones or the user's, takes auto and bypassPermissions from the user's only, says what a builder meets, and has no row outside a repository"
else
  fail "the permission mode: $plain / $shared / $local_bypass / $user_auto / $outside"
fi
# Lem's plugin installed for the user loads in every repository: a row says so with the two commands that move it.
mkdir -p "$FAKEHOME/.claude/plugins"
printf '%s\n' '{"version": 2, "plugins": {"lem@lem": [{"scope": "user"}]}}' > "$FAKEHOME/.claude/plugins/installed_plugins.json"
for_user=$(doctor | field '(d["ok"], [(t["need"], t["found"], t["detail"]) for t in d["tools"] if t["name"] == "lem plugin scope"], next(t["without_it"] for t in d["tools"] if t["name"] == "lem plugin scope"))' || true)
printf '%s\n' "{\"version\": 2, \"plugins\": {\"lem@lem\": [{\"scope\": \"project\", \"projectPath\": \"$MACHINE\"}]}}" > "$FAKEHOME/.claude/plugins/installed_plugins.json"
for_project=$(doctor | field '[t["name"] for t in d["tools"] if t["name"] == "lem plugin scope"]' || true)
rm "$FAKEHOME/.claude/plugins/installed_plugins.json"
if grep -qF "[('project', False, 'lem@lem is installed for the user, so every repository on this machine loads it')]" <<<"$for_user" \
  && grep -qF "\`claude plugin uninstall lem@lem --scope user\` removes that install; then \`claude plugin install lem@lem --scope project\`" <<<"$for_user" \
  && grep -qF "a median of 99.4 ms over 20 runs" <<<"$for_user" && [ "$for_project" = "[]" ]; then
  pass "Lem's plugin installed for the user gets a row that says every repository loads it, what its hook costs there, and the two commands that move it to a project; one installed for the project gets none"
else
  fail "the plugin's scope: $for_user / $for_project"
fi

finish
