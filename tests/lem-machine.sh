#!/usr/bin/env bash
# The machine check, the correction queue and its hook, and the plugin's files, each
# in a home and a repository of its own, and the personas' row of the machine check.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

# The machine check: a required tool that is absent fails it, an optional one only changes its row.
BIN=$WORK/bin
FAKEHOME=$WORK/home
# doctor.py reads the repository it runs in (its builder, an install of Lem for it, its personas),
# so the check runs in a repository of its own: nothing of the checkout that runs these tests reaches it.
MACHINE=$WORK/machine-repo
mkdir -p "$BIN" "$FAKEHOME"
# APP_PY: the interpreter beside the lem under test, in its own environment, for a check that calls one function of the
# app in the place of a whole command; it imports the app's own package, the checkout's or an installed one
APP_PY=$(dirname "$LEM")/python
git init -q -b main "$MACHINE"
ln -s "$(command -v git)" "$BIN/git"
fake() { printf '#!/bin/sh\necho "%s"\n' "$2" > "$BIN/$1"; chmod +x "$BIN/$1"; }
doctor() { (cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" "$LEM" doctor); }
row() { field "next(t for t in d[\"tools\"] if t[\"name\"] == \"$1\")[\"$2\"]"; }
# --help prints the usage and exits 0 with no check run; an unknown argument is a usage error, exit 2, with the usage.
helped=$(cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" "$LEM" doctor --help 2>&1; echo "exit $?")
wrong=$(cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" "$LEM" doctor --all 2>&1; echo "exit $?")
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
fake cronn "cronn"
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
in_tree=$( (cd "$WORK/machine-wt" && env -i PATH="$BIN" HOME="$FAKEHOME" "$LEM" doctor || true) | row 'lem-builder agent' detail)
rm -r "$MACHINE/.claude" && git -C "$MACHINE" worktree remove --force "$WORK/machine-wt"
if [ "$in_tree" = "$MACHINE/.claude/agents/lem-builder.md" ] && grep -qF "\`claude plugin marketplace add pySilver/lem --scope project\`, then \`claude plugin install lem@lem --scope project\`" <<<"$(row 'lem-builder agent' without_it <<<"$out")" \
  && ! grep -q "setup" <<<"$(row 'lem-builder agent' without_it <<<"$out")" \
  && [ "$(row agterm without_it <<<"$out")" = "\`/lem\` stops at once: Lem runs inside agterm only" ]; then
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
flagged() { (cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" CLAUDE_PLUGIN_ROOT="$1" "$LEM" doctor || true) | field 'next((t["found"], t["detail"]) for t in d["tools"] if t["name"] == "lem-builder agent")'; }
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
# The recipes of the agterm cookbook: webrev and the backlog are required and agdoc is recommended, each with its guide:
# webrev and agdoc as skills of the user, the backlog as a skill of the user or of the repository.
recipes() { (doctor || true) | field '(d["ok"], [(t["name"], t["found"], t["guide"].rsplit("/", 1)[1]) for t in d["tools"] if t["name"] in ("webrev skill", "agdoc skill", "backlog skill")], [t["need"] for t in d["tools"] if t["name"] in ("webrev skill", "agdoc skill", "backlog skill")])'; }
mv "$FAKEHOME/.claude/skills" "$WORK/skills-away"
none_yet=$(recipes)
mkdir -p "$FAKEHOME/.claude/skills" "$MACHINE/.claude/skills/backlog" && mv "$WORK/skills-away/webrev" "$WORK/skills-away/agdoc" "$FAKEHOME/.claude/skills/"
touch "$MACHINE/.claude/skills/backlog/SKILL.md"
in_project=$( (doctor || true) | row 'backlog skill' detail)
rm -r "$MACHINE/.claude"
# The owner's own backlog skill may ride in a plugin of another name, as `tracking:backlog` does.
mkdir -p "$WORK/tracking-plugin/skills/backlog" && touch "$WORK/tracking-plugin/skills/backlog/SKILL.md"
printf '%s\n' "{\"version\": 2, \"plugins\": {\"lem@lem\": [{\"scope\": \"user\"}], \"tracking@some-market\": [{\"scope\": \"project\", \"projectPath\": \"$WORK/another-repository\", \"installPath\": \"$WORK/tracking-plugin\"}]}}" > "$FAKEHOME/.claude/plugins/installed_plugins.json"
plugin_elsewhere=$( (doctor || true) | row 'backlog skill' found)
printf '%s\n' "{\"version\": 2, \"plugins\": {\"lem@lem\": [{\"scope\": \"user\"}], \"tracking@some-market\": [{\"scope\": \"user\", \"installPath\": \"$WORK/tracking-plugin\"}]}}" > "$FAKEHOME/.claude/plugins/installed_plugins.json"
in_plugin=$( (doctor || true) | row 'backlog skill' detail)
printf '%s\n' '{"version": 2, "plugins": {"lem@lem": [{"scope": "user"}]}}' > "$FAKEHOME/.claude/plugins/installed_plugins.json"
mv "$WORK/skills-away/backlog" "$FAKEHOME/.claude/skills/" && rmdir "$WORK/skills-away"
for_user=$( (doctor || true) | row 'backlog skill' detail)
if [ "$none_yet" = "(False, [('webrev skill', False, 'annotate-document'), ('agdoc skill', False, 'html-doc-overlay'), ('backlog skill', False, 'backlog-picker')], ['required', 'recommended', 'required'])" ] \
  && [ "$in_project" = "$MACHINE/.claude/skills/backlog" ] && [ "$for_user" = "$FAKEHOME/.claude/skills/backlog" ] \
  && [ "$plugin_elsewhere" = "False" ] && [ "$in_plugin" = "the skill tracking:backlog" ]; then
  pass "webrev and the backlog recipe are required and agdoc is recommended, each with its guide, and the backlog's skill counts for the user or for the repository, in a skills folder or in a plugin of another name"
else
  fail "the recipes Lem needs: $none_yet / $in_project / $for_user / $plugin_elsewhere / $in_plugin"
fi
out=$(doctor)
if [ "$home_only" = "(False, False)" ] && [ "$(field 'd["ok"]' <<<"$out")" = "True" ] && [ "$(field '[t["name"] for t in d["tools"] if "jev" in t["name"]]' <<<"$out")" = "[]" ] && [ "$(row 'lem-builder agent' detail <<<"$out")" = "lem:lem-builder, from the plugin lem@lem" ] && [ "$(row cronn found <<<"$out")" = "True" ] \
  && [ "$(row plannotator found <<<"$out")" = "False" ] && [ "$(row plannotator without_it <<<"$out" | grep -c 'nothing goes to the Inbox')" = 1 ] && [ "$(row codex found <<<"$out")" = "False" ] \
  && [ "$(field '[t["name"] for t in d["tools"] if t["name"] == "codex persona agent"]' <<<"$out")" = "[]" ] \
  && [ "$(field '[(t["name"], t["found"], t["guide"].rsplit("/", 1)[1]) for t in d["tools"] if t["need"] == "recommended"]' <<<"$out")" \
    = "[('agdoc skill', True, 'html-doc-overlay'), ('plannotator-tui', False, 'annotate-in-plannotator-tui'), ('plannotator', False, 'plannotator'), ('codex', False, 'codex')]" ] \
  && [ "$(row cronn used_for <<<"$out")" = "a scheduled retro and a night run" ] \
  && [ ! -e "$PWD/skills/lem-webrev" ]; then
  pass "a builder file in the home is not Lem's; with git, the review tool, agterm, the mailbox, the cookbook's recipes, their skills, Claude Code and Lem's plugin the check passes; absent optional tools only change their rows, the recommended tools, no part of Lem, have a row with their guide, no row speaks of a jev command, and the cronn row names no free hour, which is the maintainer's"
else
  fail "doctor with the required set: $out"
fi
# The task picker's row: optional, with the keymap line for this machine, which runs the app's command `lem picker` by
# the path an update keeps: here the lem beside the Python of the app under test, by its resolved path. The row is
# found when agterm's keymap holds the line; a line of a Lem before the app (an interpreter and the marketplace clone's
# picker.py from ~/, as a Mac's keymap held it on 2026-11-23) is named as one that no longer works, with the line to put
# in its place and `agtermctl keymap reload`. Lem only reads that file.
picker_row() { field '(lambda t: (t["need"], t["found"], t["line"]))(next(t for t in d["tools"] if t["name"] == "task picker"))'; }
own_lem=$("$APP_PY" -I -B -c 'import os, sys; print(os.path.realpath(os.path.join(os.path.dirname(sys.executable), "lem")))')
picker_line="command \"Lem tasks ›\" ctrl+cmd+t --error-hud $own_lem picker"
absent=$(doctor | picker_row || true)
mkdir -p "$FAKEHOME/.config/agterm"
printf '%s\n' "$picker_line" > "$FAKEHOME/.config/agterm/keymap.conf"
held=$(doctor | picker_row || true)
old_line="command \"Lem tasks ›\"  ctrl+cmd+t  --error-hud /usr/bin/python3 ~/.claude/plugins/marketplaces/lem/skills/lem/scripts/picker.py"
printf '%s\n' "$old_line" > "$FAKEHOME/.config/agterm/keymap.conf"
older=$(doctor | field '(lambda t: (t["found"], t["line"], t["detail"]))(next(t for t in d["tools"] if t["name"] == "task picker"))' || true)
rm -r "$FAKEHOME/.config/agterm"
if [ "$absent" = "('optional', False, '$picker_line')" ] && [ "$held" = "('optional', True, '$picker_line')" ] \
  && [ "$older" = "(False, '$picker_line', '$FAKEHOME/.config/agterm/keymap.conf holds a line of a Lem before the app, which no longer works: $old_line; the owner puts this row\\'s line in its place and runs \`agtermctl keymap reload\`')" ]; then
  pass "the task picker's row is optional and gives the keymap line that runs the app's own lem picker by its path; it is found when agterm's keymap holds the line, and a line of a Lem before the app, an interpreter and the marketplace clone's picker.py, is named as one that no longer works, with the line to put in its place and agtermctl keymap reload"
else
  fail "the task picker's row: $absent / $held / $older"
fi
rm "$BIN/cronn"
out=$(doctor || true)
if [ "$(status_of doctor)" = 1 ] && [ "$(field 'd["ok"]' <<<"$out")" = "False" ] && [ "$(row cronn need <<<"$out")" = "required" ] && [ "$(row cronn found <<<"$out")" = "False" ] \
  && grep -q "cronn.umputun.dev" <<<"$(row cronn without_it <<<"$out")"; then
  pass "cronn is required: without it the check fails, and the row says where to get it"
else
  fail "doctor without cronn: $out"
fi
fake cronn "cronn"
keyed=$(cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" JEV_API_KEY=sk-not-a-real-key "$LEM" doctor)
# a key under another name than JEV_API_KEY is no key; JEV_API_URL names another provider
other_name=$(cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" OPENROUTER_API_KEY=sk-not-a-real-key "$LEM" doctor)
elsewhere=$(cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" JEV_API_KEY=sk-not-a-real-key JEV_API_URL=https://api.example.test/v1/systemone "$LEM" doctor)
nokey_says=$(row 'Jev key' without_it <<<"$out")
if [ "$(field '[t["name"] for t in d["tools"] if "lem-ask" in t["name"]]' <<<"$out")" = "[]" ] && [ "$(row 'Jev key' found <<<"$out")" = "False" ] && [ "$(row 'Jev key' need <<<"$out")" = "optional" ] \
  && [ "$(row 'Jev key' found <<<"$keyed")" = "True" ] && [ "$(row 'Jev key' detail <<<"$keyed")" = "JEV_API_KEY, to OpenRouter" ] \
  && [ "$(row 'Jev key' found <<<"$other_name")" = "False" ] && [ "$(row 'Jev key' detail <<<"$other_name")" = "JEV_API_KEY is not set, and it is the one name Lem reads for the key" ] \
  && [ "$(row 'Jev key' detail <<<"$out")" = "JEV_API_KEY is not set, and it is the one name Lem reads for the key" ] \
  && [ "$(row 'Jev key' detail <<<"$elsewhere")" = "JEV_API_KEY, to https://api.example.test/v1/systemone" ] \
  && grep -qF "JEV_API_KEY in the environment the agent starts with" <<<"$nokey_says" && grep -qF "OpenRouter unless JEV_API_URL names another" <<<"$nokey_says" \
  && grep -qF "the landing's read of each finding called under the bar" <<<"$(row 'Jev key' used_for <<<"$out")" && grep -qF 'Jev: not asked (no key)' <<<"$nokey_says" \
  && ! grep -q "OPENROUTER_API_KEY" <<<"$out$other_name" && ! grep -q "sk-not-a-real-key" <<<"$keyed$other_name$elsewhere"; then
  pass "the check has no row for the question page, which is a part of Lem; its Jev key row says that JEV_API_KEY gives the key and to which provider; with no JEV_API_KEY, also when the key is under another name, the row is not found and says that JEV_API_KEY is the one name, names OpenRouter as the default, says that a pull request then says Jev was not asked about a finding under the bar, and never prints the key"
else
  fail "doctor and the key: $keyed / $other_name / $elsewhere / $nokey_says"
fi
# Where the correction queue is on, the key is required: with no key the hook fails on each message and the queue stays
# empty. The row names both ways out; the machine's no, or no line at all, leaves it optional.
KEYED=$WORK/key-repo
KEY_MACHINE=$FAKEHOME/.config/lem/machine.toml
git init -q -b main "$KEYED" && mkdir -p "$KEYED/.lem" "$FAKEHOME/.config/lem"
printf '%s\n' '[branch]' 'base = "main"' > "$KEYED/.lem/settings.toml"
printf '%s\n' '[corrections]' 'collect = true' > "$KEY_MACHINE"
key_doctor() { (cd "$KEYED" && env -i PATH="$BIN" HOME="$FAKEHOME" "$@" "$LEM" doctor); }
key_row() { field '(lambda t: (t["need"], t["found"]))(next(t for t in d["tools"] if t["name"] == "Jev key"))'; }
on_out=$(key_doctor || true)
on_code=$(status_of key_doctor)
on_keyed=$(key_doctor JEV_API_KEY=sk-not-a-real-key | key_row)
on_keyed_code=$(status_of key_doctor JEV_API_KEY=sk-not-a-real-key)
printf '%s\n' '[corrections]' 'collect = false' > "$KEY_MACHINE"
off=$(key_doctor | key_row)
off_code=$(status_of key_doctor)
rm "$KEY_MACHINE"
unsaid=$(key_doctor | key_row)
unsaid_code=$(status_of key_doctor)
rm -r "$FAKEHOME/.config/lem"
on_says=$(row 'Jev key' without_it <<<"$on_out")
if [ "$on_code" = 1 ] && [ "$(key_row <<<"$on_out")" = "('required', False)" ] && [ "$(field 'd["ok"]' <<<"$on_out")" = False ] \
  && grep -qF "collect = true under [corrections] in ~/.config/lem/machine.toml" <<<"$(row 'Jev key' detail <<<"$on_out")" \
  && grep -qF "the queue stays empty" <<<"$on_says" && grep -qF "Put JEV_API_KEY in the environment the agent starts with" <<<"$on_says" \
  && grep -qF "turn the queue off for every repository on this machine with \`lem corrections collect no\`" <<<"$on_says" \
  && [ "$on_keyed" = "('required', True)" ] && [ "$on_keyed_code" = 0 ] \
  && [ "$off" = "('optional', False)" ] && [ "$off_code" = 0 ] && [ "$unsaid" = "('optional', False)" ] && [ "$unsaid_code" = 0 ]; then
  pass "where the machine's file turns the correction queue on, the key is required: with none the check fails, names the file, the key and lem corrections collect no; with the key it passes; the machine's no, or no line, leaves it optional"
else
  fail "the key where the queue is on: $on_code $(key_row <<<"$on_out") / $on_says / $on_keyed $on_keyed_code / $off $off_code / $unsaid $unsaid_code"
fi
fake plannotator "plannotator 0.29.0"
inbox=$(doctor | field '(next((t["need"], t["found"], t["detail"]) for t in d["tools"] if t["name"] == "plannotator"), d["ok"])' || true)
rm "$BIN/plannotator"
if [ "$inbox" = "(('recommended', True, 'plannotator 0.29.0'), True)" ]; then
  pass "a machine with Plannotator has its row found with its version, the Inbox of what waits for the owner while he is away"
else
  fail "doctor and Plannotator: $inbox"
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
# The correction queue: off unless the machine's own file says yes, filled by the hook, read by the retro.
CQ=$WORK/corr
git init -q -b main "$CQ" && commit "$CQ" start
project --repo "$CQ" init --base main >/dev/null
if ! grep -qE '^\[tools\]|^(annotate|ask) = ' "$CQ/.lem/settings.toml" && [ "$(project --repo "$CQ" show | field '"tools" in d')" = False ]; then
  pass "a new settings file has no [tools]: Lem asks with its own page and opens a text with webrev"
else
  fail "the tools of a new settings file: $(grep -n -A8 '^\[tools\]' "$CQ/.lem/settings.toml")"
fi
mkdir -p "$WORK/jevbin"
# a stand-in for jev: it answers with the probability in JEV_P, or fails as JEV_EXIT says, and adds
# a line to the file JEV_CALLED names for each call
# shellcheck disable=SC2016  # the stand-in's own variables, expanded when it runs
printf '%s\n' '#!/bin/sh' 'cat > /dev/null' 'if [ -n "$JEV_CALLED" ]; then echo called >> "$JEV_CALLED"; fi' 'if [ -n "$JEV_EXIT" ]; then echo "no key" >&2; exit "$JEV_EXIT"; fi' \
  'printf "{\"answers\": {\"lesson\": {\"type\": \"choice\", \"probabilities\": {\"lesson\": %s}}}}" "$JEV_P"' > "$WORK/jevbin/jev"
chmod +x "$WORK/jevbin/jev"
printf '%s\n' '{"type": "user", "message": {"content": "hi"}}' '{"type": "assistant", "message": {"content": [{"type": "text", "text": "I pushed it."}]}}' > "$WORK/transcript.jsonl"
event() { printf '{"prompt": "%s", "cwd": "%s", "session_id": "%s", "transcript_path": "%s"}' "$1" "$CQ" "$2" "$WORK/transcript.jsonl"; }
# LEM_JEV in every call: without it the worker runs Lem's own jev.py, which asks a real service.
hook() { env LEM_JEV="$WORK/jevbin/jev" JEV_P="${JEV_P:-0.9}" JEV_EXIT="${JEV_EXIT:-}" JEV_CALLED="$WORK/jev-called" "$LEM" corrections "$@"; }
worker() {
  printf '{"prompt": "%s", "cwd": "%s", "session": "%s", "transcript": "%s"}' "$1" "$CQ" "$2" "$WORK/transcript.jsonl" > "$WORK/payload.json"
  hook worker "$WORK/payload.json"
}
corr() { "$LEM" corrections --repo "$CQ" "$@"; }
# The switch is the machine's: `collect` under [corrections] in machine.toml of Lem's home folder, which only
# `lem corrections collect yes|no` writes, keeping the file's other tables. With no line it is Lem's default, a no.
MACHINE_FILE=$XDG_CONFIG_HOME/lem/machine.toml
cp "$MACHINE_FILE" "$WORK/machine.kept"
queue_on() { corr collect yes >/dev/null; }
queue_off() { corr collect no >/dev/null; }
# the machine's file as lib.sh wrote it, with no [corrections] table
queue_unsaid() { cp "$WORK/machine.kept" "$MACHINE_FILE"; }
switch_of() { project --repo "$CQ" show | field '(d["corrections"]["collect"], d["corrections"]["from"])'; }
unsaid_show=$(switch_of)
said_no=$(corr collect no)
no_show=$(switch_of)
# it is the machine's, so it needs no repository
said_yes=$(cd "$WORK" && "$LEM" corrections collect yes)
yes_show=$(switch_of)
kept=$("$PY" -c 'import sys, tomllib; d = tomllib.load(open(sys.argv[1], "rb")); print(sorted(d), d["load"], d["serve"]["port"] == int(sys.argv[2]), d["corrections"])' "$MACHINE_FILE" "$SERVE_PORT")
maybe_code=$(status_of corr collect maybe)
queue_unsaid
if [ "$unsaid_show" = "(False, \"Lem's default\")" ] && ! grep -q '^\[corrections\]' "$CQ/.lem/settings.toml" \
  && [ "$said_no" = "{\"collect\": false, \"file\": \"$MACHINE_FILE\"}" ] && [ "$no_show" = "(False, '$MACHINE_FILE')" ] \
  && [ "$said_yes" = "{\"collect\": true, \"file\": \"$MACHINE_FILE\"}" ] && [ "$yes_show" = "(True, '$MACHINE_FILE')" ] \
  && [ "$kept" = "['corrections', 'load', 'serve'] {'start': 0} True {'collect': True}" ] && [ "$maybe_code" = 2 ]; then
  pass "a new project's settings hold no switch of the queue, and show gives it as no, from Lem's default; lem corrections collect no and yes, run anywhere, write the line in the machine's file and keep its other tables, and show then names that file"
else
  fail "the machine's switch: $unsaid_show / $said_no / $no_show / $said_yes / $yes_show / $kept / $maybe_code"
fi
# Without the machine's yes nothing is sent: the hook prints nothing and exits 0, and its detached half, run alone as the
# hook would start it, never calls the stand-in of Jev and queues nothing. Four machines: no line, a no, a file that does
# not read, and a yes that only a repository's file says, which show refuses with the machine's file as its place.
# No hook writes the machine's file or the home folder's settings.toml.
SENT=""
nothing_sent() {
  local before out
  before=$(cksum < "$MACHINE_FILE")
  out=$(event "never push without asking" "$1" | hook hook 2>&1; echo "exit=$?")
  worker "never push without asking" "$1"
  SENT="$SENT $1:$out"
  if [ "$(cksum < "$MACHINE_FILE")" != "$before" ]; then SENT="$SENT $1:wrote-the-machine-file"; fi
}
nothing_sent unsaid
nothing_sent_list=$(corr list | field '(d["collect"], d["entries"])')
queue_off
nothing_sent no
printf 'not toml [\n' > "$MACHINE_FILE"
nothing_sent broken
broken_show=$(project --repo "$CQ" show 2>&1 || true)
broken_code=$(status_of project --repo "$CQ" show)
printf '[corrections]\ncollect = true\n# caf\351\n' > "$MACHINE_FILE"
nothing_sent latin
latin_show=$(project --repo "$CQ" show 2>&1 || true)
queue_unsaid
cp "$CQ/.lem/settings.toml" "$WORK/corr-team.kept"
printf '\n[corrections]\ncollect = true\n' >> "$CQ/.lem/settings.toml"
nothing_sent team
team_show=$(project --repo "$CQ" show 2>&1 || true)
team_code=$(status_of project --repo "$CQ" show)
cp "$WORK/corr-team.kept" "$CQ/.lem/settings.toml"
printf '[corrections]\ncollect = true\n' > "$CQ/.lem/settings.local.toml"
nothing_sent local
local_show=$(project --repo "$CQ" show 2>&1 || true)
rm "$CQ/.lem/settings.local.toml"
sleep 1
if [ "$SENT" = " unsaid:exit=0 no:exit=0 broken:exit=0 latin:exit=0 team:exit=0 local:exit=0" ] && [ "$nothing_sent_list" = "(False, 0)" ] \
  && [ ! -e "$CQ/.lem/state/corrections.jsonl" ] && [ ! -e "$WORK/jev-called" ] && [ ! -e "$WORK/payload.json" ] && [ ! -e "$XDG_CONFIG_HOME/lem/settings.toml" ] \
  && [ "$broken_code" = 1 ] && grep -qF "$MACHINE_FILE does not read as TOML" <<<"$broken_show" && grep -qF "$MACHINE_FILE is not UTF-8 text" <<<"$latin_show" \
  && [ "$team_code" = 1 ] && grep -qF "[corrections] is not valid in this file: its place is $MACHINE_FILE" <<<"$team_show" \
  && grep -qF "[corrections] is not valid in this file: its place is $MACHINE_FILE" <<<"$local_show" && grep -qF "settings.local.toml" <<<"$local_show" \
  && ! grep -q Traceback <<<"$broken_show$latin_show$team_show$local_show"; then
  pass "without the machine's yes (no line, a no, a file that does not read, a yes in the team's or the local file) the hook prints nothing and its detached half sends nothing; show refuses the broken file and the repository's table by the machine file's name, and no hook writes a file of the home folder"
else
  fail "a message was sent, or a file written, without the machine's yes: $SENT / $nothing_sent_list / $broken_show / $latin_show / $team_show / $local_show / $(ls "$XDG_CONFIG_HOME/lem" "$CQ/.lem/state" 2>&1)"
fi
# The hand-over to the detached half fails (no interpreter can be started): no file with the owner's words stays behind.
queue_on
mkdir -p "$WORK/hooktmp"
out=$(event "the copy cannot start" s0 | env LEM_JEV="$WORK/jevbin/jev" TMPDIR="$WORK/hooktmp" "$APP_PY" -B -c '
import runpy, sys
sys.argv = ["corrections.py", "hook"]
sys.executable = "/no/such/python"   # the hook starts its copy with this
runpy.run_module("lem.corrections", run_name="__main__", alter_sys=True)' 2>&1; echo "exit=$?")
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
queue_off
# An input that stays open: the hook returns, with exit 0 and not a word. The
# input stays open 15 seconds, and the hook returns in 10 at most, on a loaded machine too.
started=$SECONDS
out=$(hook hook < <(event "the input stays open" s0; sleep 15) 2>&1; echo "exit=$?")
if [ "$out" = "exit=0" ] && [ $((SECONDS - started)) -lt 10 ]; then
  pass "the hook does not wait for its input to close"
else
  fail "the hook with an open input: $out after $((SECONDS - started))s"
fi
queue_on
out=$(event "never push without asking" s1 | hook hook; echo "exit=$?")
soon test -s "$CQ/.lem/state/corrections.jsonl"
if [ "$out" = "exit=0" ] && [ "$("$PY" -c 'import json, sys; e = json.loads(open(sys.argv[1]).readline()); print(e["owner"], "|", e["previous"], "|", e["p_lesson"], "|", e["session"])' "$CQ/.lem/state/corrections.jsonl")" = "never push without asking | I pushed it. | 0.9 | s1" ]; then
  pass "with the machine's yes the hook prints nothing, and its detached half queues the owner's words with the agent message they answer"
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
env LEM_JEV="$WORK/no-such-jev" "$LEM" corrections worker "$WORK/payload.json"
# No LEM_JEV: the worker runs Lem's own jev.py by its path, with a PATH that has no jev. No key is
# set, so the copy stops before it sends anything, and its own words are in the log.
printf '{"prompt": "the copy beside the hook", "cwd": "%s", "session": "s9", "transcript": ""}' "$CQ" > "$WORK/payload.json"
env -u LEM_JEV -u JEV_API_KEY PATH="$BIN" "$LEM" corrections worker "$WORK/payload.json"
sleep 1
out=$(corr list)
if [ "$(field '(d["entries"], [(g["entries"], g["sessions"], g["p_lesson_max"]) for g in d["groups"]], d["failures"]["count"])' <<<"$out")" = "(3, [(2, 2, 0.9), (1, 1, None)], 3)" ] \
  && grep -q "no key" "$CQ/.lem/state/corrections.log" && grep -q "jev did not run" "$CQ/.lem/state/corrections.log" \
  && grep -q "jev gave no answer: lem jev: JEV_API_KEY is not set in this process's environment, and it is the one name Lem reads for the key" "$CQ/.lem/state/corrections.log"; then
  pass "one sentence from two sessions is one group; a low score, a command and injected text queue nothing; a message too long for Jev is queued unjudged; each failure is in the log and counted; with no other jev named, the worker runs the copy beside it"
else
  fail "the queue: $out / $(cat "$CQ/.lem/state/corrections.log" 2>&1)"
fi
# The machine's switch holds in each repository on it: with its yes, a message typed in a worktree is queued in its
# repository's state folder, and one typed in another repository in that one's; with its no, nothing is sent from the
# main checkout, from a worktree, or from the worktree of a bare repository.
cp "$CQ/.lem/state/corrections.jsonl" "$WORK/queue.before"
git -C "$CQ" add .lem && git -C "$CQ" -c user.name=t -c user.email=t@t commit -q -m "chore: the settings" && git -C "$CQ" worktree add -q "$WORK/corr-wt" -b side
OTHER=$WORK/corr-other
git init -q -b main "$OTHER" && commit "$OTHER" start
project --repo "$OTHER" init --base main >/dev/null
rm -f "$WORK/jev-called"
printf '{"prompt": "from a worktree", "cwd": "%s", "session": "s10", "transcript": ""}' "$WORK/corr-wt" > "$WORK/payload.json"
hook worker "$WORK/payload.json"
printf '{"prompt": "from another repository", "cwd": "%s", "session": "s11", "transcript": ""}' "$OTHER" > "$WORK/payload.json"
hook worker "$WORK/payload.json"
yes_calls=$(grep -c '' "$WORK/jev-called" || true)
wt_queued=$(grep -c '"owner": "from a worktree"' "$CQ/.lem/state/corrections.jsonl" || true)
other_queued=$(grep -c '"owner": "from another repository"' "$OTHER/.lem/state/corrections.jsonl" || true)
queue_off
rm -f "$WORK/jev-called"
cp "$CQ/.lem/state/corrections.jsonl" "$WORK/queue.on"
worker "the machine says no" s12
printf '{"prompt": "from a worktree, with the no", "cwd": "%s", "session": "s13", "transcript": ""}' "$WORK/corr-wt" > "$WORK/payload.json"
hook worker "$WORK/payload.json"
git clone -q --bare "$CQ" "$WORK/corr-bare.git" && git -C "$WORK/corr-bare.git" worktree add -q "$WORK/corr-bare-wt" main
printf '{"prompt": "from the worktree of a bare repository", "cwd": "%s", "session": "s14", "transcript": ""}' "$WORK/corr-bare-wt" > "$WORK/payload.json"
hook worker "$WORK/payload.json"
bare_log=$( (cat "$WORK/corr-bare.git/.lem/state/corrections.log" "$WORK/corr-bare.git/.lem/state/corrections.jsonl" 2>/dev/null || true) | wc -l | tr -d ' ')
if [ "$yes_calls" = 2 ] && [ "$wt_queued" = 1 ] && [ "$other_queued" = 1 ] && cmp -s "$CQ/.lem/state/corrections.jsonl" "$WORK/queue.on" \
  && [ ! -e "$WORK/jev-called" ] && [ "$bare_log" = 0 ]; then
  pass "the machine's yes holds in each repository on it, from a worktree and in another repository; its no stops the hook before anything is sent, from the main checkout, a worktree and the worktree of a bare repository"
else
  fail "the machine's switch across repositories: $yes_calls calls, $wt_queued from the worktree, $other_queued in the other repository, bare $bare_log / $(diff "$CQ/.lem/state/corrections.jsonl" "$WORK/queue.on" 2>&1)"
fi
# the queue as the checks below count it, without the worktree's entry
cp "$WORK/queue.before" "$CQ/.lem/state/corrections.jsonl"
git -C "$CQ" worktree remove --force "$WORK/corr-wt"
gid=$(field 'd["groups"][0]["id"]' <<<"$out")
if [ "$(status_of corr record "$gid" --decision lesson --verdict unasked)" = 1 ] && [ "$(status_of corr record nope --decision not_lesson --verdict unasked)" = 1 ] \
  && [ "$(status_of corr record "$gid" --decision lesson --verdict unasked --lesson "Never push to a branch the settings do not name.")" = 1 ] \
  && [ "$(corr show "$gid" | field 'len(d)')" = 2 ]; then
  pass "a lesson without its sentence or without its file and an unknown group are refused, and show gives every entry of a group"
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
# A settings file that does not read stops list as it stops every command that reads the settings.
cp "$CQ/.lem/state/corrections.jsonl" "$WORK/queue.kept"
printf '{"ts": "2026-01-01T00:00:00Z", "sess' >> "$CQ/.lem/state/corrections.jsonl"
cut_line=$(corr list 2>&1 || true)
cut_code=$(status_of corr list)
cp "$WORK/queue.kept" "$CQ/.lem/state/corrections.jsonl"
cp "$CQ/.lem/state/corrections-reviews.jsonl" "$WORK/reviews.kept" && printf 'caf\351\n' >> "$CQ/.lem/state/corrections-reviews.jsonl"
latin_line=$(corr lessons 2>&1 || true)
cp "$WORK/reviews.kept" "$CQ/.lem/state/corrections-reviews.jsonl"
cp "$CQ/.lem/settings.toml" "$WORK/corr-settings.kept" && printf '# caf\351\n' >> "$CQ/.lem/settings.toml"
latin_code=$(status_of corr list)
latin_settings=$(corr list 2>&1 || true)
cp "$WORK/corr-settings.kept" "$CQ/.lem/settings.toml"
lines=$(grep -c '' "$CQ/.lem/state/corrections.jsonl")
if [ "$cut_code" = 1 ] && grep -qF "corrections.jsonl:$((lines + 1)) does not read as JSON" <<<"$cut_line" && grep -qF "corrections-reviews.jsonl:" <<<"$latin_line" \
  && grep -qF "is not UTF-8 text" <<<"$latin_line" && [ "$latin_code" = 1 ] && grep -qF "corrections.py: $CQ/.lem/settings.toml is not UTF-8 text" <<<"$latin_settings" \
  && ! grep -q Traceback <<<"$cut_line$latin_line$latin_settings"; then
  pass "a queue line that was cut off and a line that is not UTF-8 are named with their file and line, and settings that do not read stop list with the fix"
else
  fail "a queue that does not read: $cut_line / $latin_line / $latin_code / $latin_settings"
fi
# Lem's client of Jev: a timeout that is no number and a spec that is not UTF-8 are named, and nothing is sent.
printf '%s\n' '{"state": "s", "questions": {"q": {"type": "choice", "instructions": "i", "choices": {"a": "x", "b": "y"}}}}' > "$WORK/jev-spec.json"
printf '{"state": "caf\351", "questions": {}}' > "$WORK/jev-latin.json"
soon_timeout=$(env JEV_TIMEOUT=soon "$LEM" jev check "$WORK/jev-spec.json" 2>&1 || true)
soon_code=$(env JEV_TIMEOUT=soon "$LEM" jev check "$WORK/jev-spec.json" >/dev/null 2>&1; echo $?)
latin_file=$("$LEM" jev check "$WORK/jev-latin.json" 2>&1 || true)
latin_stdin=$("$LEM" jev check - < "$WORK/jev-latin.json" 2>&1 || true)
checked=$(env JEV_TIMEOUT=30 "$LEM" jev check "$WORK/jev-spec.json" | field 'd["ok"]' 2>&1 || true)
printf '%s\n' '{"state": "s", "questions": {"q": {"instructions": "i", "choices": {"a": "x", "b": "y"}}}}' > "$WORK/jev-untyped.json"
untyped=$("$LEM" jev check "$WORK/jev-untyped.json" 2>&1 || true)
untyped_code=$("$LEM" jev check "$WORK/jev-untyped.json" >/dev/null 2>&1; echo $?)
if [ "$soon_code" = 1 ] && grep -qF "lem jev: JEV_TIMEOUT='soon' is not a number of seconds above 0" <<<"$soon_timeout" \
  && grep -qF "lem jev: the spec ($WORK/jev-latin.json) is not UTF-8 text" <<<"$latin_file" && grep -qF "lem jev: the spec (stdin) is not UTF-8 text" <<<"$latin_stdin" \
  && [ "$untyped_code" = 1 ] && grep -qF "lem jev: question 'q' names no type; give it \"type\": \"choice\" (with choices) or \"type\": \"noul\"" <<<"$untyped" \
  && [ "$checked" = True ] && ! grep -q Traceback <<<"$soon_timeout$latin_file$latin_stdin$untyped"; then
  pass "lem jev names a JEV_TIMEOUT that is no number, a spec that is not UTF-8, from a file or from its input, and a question with no type, and exits 1"
else
  fail "jev's refusals: $soon_timeout / $latin_file / $latin_stdin / $untyped_code $untyped / $checked"
fi
# The key and the address of the Jev model: JEV_API_KEY, and a key under another name is none; JEV_API_URL, else
# OpenRouter's. A request goes to that address with that key, as a stand-in server of Jev's form sees it; it
# answers a choice and a noul, and a second request with a noul whose answer has no number.
jcheck() { env -u JEV_API_KEY -u OPENROUTER_API_KEY -u JEV_API_URL "$@" "$LEM" jev check "$WORK/jev-spec.json" | field '(d["url"], d["key_from"])' 2>&1 || true; }
by_jev=$(jcheck JEV_API_KEY=k1 OPENROUTER_API_KEY=k2)
by_other=$(jcheck OPENROUTER_API_KEY=k2)
by_none=$(jcheck)
other_ask=$(env -u JEV_API_KEY OPENROUTER_API_KEY=k2 "$LEM" jev "$WORK/jev-spec.json" 2>&1 || true)
other_code=$(env -u JEV_API_KEY OPENROUTER_API_KEY=k2 "$LEM" jev "$WORK/jev-spec.json" >/dev/null 2>&1; echo $?)
by_url=$(jcheck JEV_API_KEY=k1 JEV_API_URL=https://api.example.test/v1/systemone)
bad_url=$(env JEV_API_KEY=k1 JEV_API_URL=api.example.test "$LEM" jev check "$WORK/jev-spec.json" 2>&1 || true)
printf '%s\n' 'import http.server, json, sys' \
  'class H(http.server.BaseHTTPRequestHandler):' \
  '    def do_POST(self):' \
  '        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))' \
  '        if "bad" not in body["questions"]: open(sys.argv[2], "w").write(json.dumps({"path": self.path, "auth": self.headers["Authorization"], "model": body["model"], "state": body["state"], "n": body["questions"]["n"]}))' \
  '        given = {"q": {"type": "choice", "choice": "a", "confidence": 0.9, "probabilities": {"a": 0.9, "b": 0.1}}, "n": {"type": "noul", "noul": 0.98}, "bad": {"type": "noul"}}' \
  '        reply = json.dumps({"model": body["model"], "answers": {name: given[name] for name in body["questions"]}, "usage": {"tokens": 12}}).encode()' \
  '        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(reply))); self.end_headers(); self.wfile.write(reply)' \
  '    def log_message(self, *args): pass' \
  's = http.server.HTTPServer(("127.0.0.1", 0), H)' \
  'open(sys.argv[1], "w").write(str(s.server_address[1]))' \
  's.handle_request()' 's.handle_request()' > "$WORK/jev-server.py"
printf '%s\n' '{"state": {"said": "s"}, "questions": {"q": {"type": "choice", "instructions": "i", "choices": {"a": "x", "b": "y"}}, "n": {"type": "noul", "instructions": "i", "yes": "y", "no": "n"}}}' > "$WORK/jev-both.json"
printf '%s\n' '{"state": "s", "questions": {"bad": {"type": "noul", "instructions": "i"}}}' > "$WORK/jev-bad.json"
"$PY" -B "$WORK/jev-server.py" "$WORK/jev-port" "$WORK/jev-seen" &
jev_server=$!
soon test -s "$WORK/jev-port"
asked=$(env JEV_API_KEY=sk-test-key JEV_API_URL="http://127.0.0.1:$(cat "$WORK/jev-port")/v1/systemone" JEV_MODEL=jev-latest "$LEM" jev "$WORK/jev-both.json" | field '(d["model"], d["answers"]["q"]["choice"], d["answers"]["n"], d["cost"])' 2>&1 || true)
no_number=$(env JEV_API_KEY=sk-test-key JEV_API_URL="http://127.0.0.1:$(cat "$WORK/jev-port")/v1/systemone" "$LEM" jev "$WORK/jev-bad.json" 2>&1; echo "exit=$?")
wait "$jev_server" 2>/dev/null || true
seen=$(field '(d["path"], d["auth"], d["model"], d["state"], d["n"])' < "$WORK/jev-seen" 2>&1 || true)
if [ "$by_jev" = "('https://openrouter.ai/api/alpha/decisions', 'JEV_API_KEY')" ] && [ "$by_other" = "('https://openrouter.ai/api/alpha/decisions', None)" ] \
  && [ "$by_none" = "('https://openrouter.ai/api/alpha/decisions', None)" ] && [ "$by_url" = "('https://api.example.test/v1/systemone', 'JEV_API_KEY')" ] \
  && [ "$other_code" = 1 ] && [ "$other_ask" = "lem jev: JEV_API_KEY is not set in this process's environment, and it is the one name Lem reads for the key; put the key of the Jev model's provider there" ] \
  && grep -qF "lem jev: JEV_API_URL='api.example.test' is not an address" <<<"$bad_url" \
  && [ "$asked" = "('jev-latest', 'a', {'type': 'noul', 'noul': 0.98}, None)" ] \
  && [ "$seen" = "('/v1/systemone', 'Bearer sk-test-key', 'jev-latest', {'said': 's'}, {'type': 'noul', 'instructions': 'i', 'criteria': {'true': 'y', 'false': 'n'}})" ] \
  && grep -qF "lem jev: the reply's answer to question 'bad', a noul, lacks a noul, a number from 0 to 1" <<<"$no_number" && grep -q 'exit=1$' <<<"$no_number" \
  && ! grep -q Traceback <<<"$no_number"; then
  pass "lem jev takes its key from JEV_API_KEY alone, and with a key under another name it sends nothing, exits 1 and says that JEV_API_KEY is the one name; its address is JEV_API_URL, else OpenRouter's; a request goes to that address with that key, a state object as JSON and a noul's yes and no as its criteria, a choice and a noul are answered in one reply and one with no cost reads, and a noul answered with no number exits 1 and names the question"
else
  fail "jev's key and address: $by_jev / $by_other / $by_none / $by_url / $other_code $other_ask / $bad_url / $asked / $seen / $no_number"
fi
# One message, one judgment: a hook registered in two or three places (the home's settings, the
# repository's, the plugin) starts once for each, at the same moment, and the first copy claims the message.
CL=$WORK/claim
git init -q -b main "$CL" && commit "$CL" start
project --repo "$CL" init --base main >/dev/null
queue_on
CLAIMS=$CL/.lem/state/corrections-claims
CALLS=$WORK/claim-calls
claim_event() { printf '{"prompt": "%s", "cwd": "%s", "session_id": "%s", "transcript_path": ""}' "$1" "$CL" "$2"; }
claim_hook() { env LEM_JEV="$WORK/jevbin/jev" JEV_P=0.9 JEV_CALLED="$CALLS" "$LEM" corrections hook; }
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
claim_failures=$(cd "$CL" && "$LEM" corrections list | field 'd["failures"]["count"]')
if [ "$out" = "exit=0" ] && [ "$(queued)" = 8 ] && grep -q "could not claim the message" "$CL/.lem/state/corrections.log" && ! grep -q Traceback "$CL/.lem/state/corrections.log" \
  && [ "$claim_failures" = 0 ]; then
  pass "a claim folder that cannot be made still queues the message, with no output, and the log says the message was judged unclaimed, as a note that list does not count as a failure"
else
  fail "a claim that cannot be made: $out / $(queued) entries / $claim_failures failures / $(cat "$CL/.lem/state/corrections.log" 2>&1)"
fi
rm "$CLAIMS"
# A collect that is not true or false is refused by show with the command that writes it, and is a no for the hook; the
# command then writes the line over it. A file that does not read is refused by the command too, and stays as it is.
printf '[corrections]\ncollect = "yes"\n' > "$MACHINE_FILE"
typed_show=$(project --repo "$CQ" show 2>&1 || true)
typed_code=$(status_of project --repo "$CQ" show)
typed_hook=$("$APP_PY" -B -c 'import sys; from lem import corrections; print(corrections.collects(sys.argv[1]))' "$CQ")
corr collect no >/dev/null
typed_fixed=$(switch_of)
printf 'not toml [\n' > "$MACHINE_FILE"
broken_write=$(corr collect yes 2>&1 || true)
broken_write_code=$(status_of corr collect yes)
broken_kept=$(cat "$MACHINE_FILE")
queue_unsaid
if [ "$typed_code" = 1 ] && grep -qF "corrections.collect in $MACHINE_FILE is 'yes', of the wrong type; \`lem corrections collect yes\` or \`lem corrections collect no\` writes it" <<<"$typed_show" \
  && [ "$typed_hook" = False ] && [ "$typed_fixed" = "(False, '$MACHINE_FILE')" ] \
  && [ "$broken_write_code" = 1 ] && grep -qF "corrections.py: $MACHINE_FILE does not read as TOML" <<<"$broken_write" && [ "$broken_kept" = "not toml [" ] \
  && ! grep -q Traceback <<<"$typed_show$broken_write"; then
  pass "a collect that is not true or false is refused by show with the command that writes it and is a no for the hook, and the command writes the line over it; a file that does not read is refused by the command and stays as it is"
else
  fail "collect type: $typed_code $typed_show / $typed_hook / $typed_fixed / $broken_write_code $broken_write / $broken_kept"
fi

# The plugin form: the files Claude Code reads to load this repository as the plugin `lem`.
# shellcheck disable=SC2016  # $CLAUDE_PLUGIN_ROOT is the text of the hook's command, for Claude Code to fill
if "$PY" -c 'import json, os, re, sys
root = sys.argv[1]
manifest = json.load(open(f"{root}/.claude-plugin/plugin.json"))
market = json.load(open(f"{root}/.claude-plugin/marketplace.json"))
ok = (manifest["name"] == "lem" and re.fullmatch(r"\d+\.\d+\.\d+", manifest.get("version") or "") is not None
      and [(p["name"], p["source"], p.get("version")) for p in market["plugins"]] == [("lem", {"source": "github", "repo": "pySilver/lem", "ref": "v" + manifest["version"]}, manifest["version"])]
      and not os.path.exists(f"{root}/bin") and not os.path.exists(f"{root}/scripts/setup.py")
      and os.access(f"{root}/hooks/run", os.X_OK))
hooks = json.load(open(f"{root}/hooks/hooks.json"))["hooks"]
commands = {event: [h["command"] for group in groups for h in group["hooks"]] for event, groups in hooks.items()}
def launch(selector):
    return f"/bin/sh \"$CLAUDE_PLUGIN_ROOT/hooks/run\" {selector} 2>/dev/null || :"
matchers = {event: [group.get("matcher") for group in groups] for event, groups in hooks.items()}
timeouts = [h.get("timeout") for groups in hooks.values() for group in groups for h in group["hooks"]]
ok = ok and commands == {"UserPromptSubmit": [launch("corrections")],
                         "SessionStart": [launch("serve"), launch("session-start")],
                         "PreCompact": [launch("precompact")],
                         "Stop": [launch("stop")]}
ok = ok and matchers["SessionStart"] == ["startup|resume", "startup|resume|clear|compact|fork"] and matchers["PreCompact"] == ["auto|manual"]
ok = ok and matchers["Stop"] == [None] and hooks["Stop"][0]["hooks"][0].get("async") is True and timeouts == [10, 5, 5, 5, None]
sys.exit(not ok)' "$PWD"; then
  pass "the plugin manifest names lem and a version of three numbers, which is the release; the marketplace file lists the one plugin, from GitHub at the tag of that release and with its version; the plugin has no bin/, since the command lem is the app's; there is no setup script; and the hooks that come with the plugin are the correction hook, the start of the board server, a task session's hooks of each session's start and of a compaction, and lem-ask's Stop hook in the background, each one line that runs the plugin's hooks/run with its selector of lem-hook"
else
  fail "the plugin files in .claude-plugin and hooks"
fi
# Each line of hooks/hooks.json as Claude Code runs it, through `sh -c` (code.claude.com/docs/en/hooks, "Shell form",
# read 2026-11-24), with CLAUDE_PLUGIN_ROOT at this checkout and LEM_HOOK_BIN at the lem-hook beside the lem under test:
# in a task's session of a repository, each gives what its handler gives run alone, the summary's form before a
# compaction and the task's files after it among them, with the app's folder first on PATH and on a PATH of /usr/bin:/bin
# alone (a Claude Code that a GUI app started). With no app the line ends with exit 0 and no output: LEM_HOOK_BIN at a file that is not there or a relative
# path, no app in any place, and an app that exits 3 after it printed.
HOOKHOME=$WORK/hookhome
TASKREPO=$WORK/hook-task-repo
mkdir -p "$HOOKHOME" "$TASKREPO/.lem/state/tasks/gift-note"
git init -q -b main "$TASKREPO"
printf '%s\n' '# the team' > "$TASKREPO/.lem/settings.toml"
printf '%s\n\n%s\n' 'phase: build, step 2' 'older block' > "$TASKREPO/.lem/state/tasks/gift-note/state.md"
printf '%s\n' '## Settled' 'the plan' > "$TASKREPO/.lem/state/tasks/gift-note/handoff.md"
HOOK_BIN=$(dirname "$LEM")/lem-hook
PLUGIN_ROOT=$PWD
hook_lines() { "$PY" -c 'import json, sys; [print(h["command"]) for groups in json.load(open(sys.argv[1]))["hooks"].values() for group in groups for h in group["hooks"]]' "$PWD/hooks/hooks.json"; }
# hook_event SELECTOR: the event Claude Code gives that hook in the task's repository
hook_event() {
  case $1 in
    corrections) printf '{"hook_event_name": "UserPromptSubmit", "prompt": "never push", "session_id": "S1", "cwd": "%s"}' "$TASKREPO" ;;
    session-start) printf '{"hook_event_name": "SessionStart", "source": "compact", "session_id": "S1", "transcript_path": "/t.jsonl", "cwd": "%s"}' "$TASKREPO" ;;
    precompact) printf '{"hook_event_name": "PreCompact", "trigger": "auto", "cwd": "%s"}' "$TASKREPO" ;;
    *) printf '{"hook_event_name": "SessionStart", "source": "startup", "cwd": "%s"}' "$TASKREPO" ;;
  esac
}
# in_hook PATH COMMAND...: COMMAND in the environment a hook has, with no agterm, a home of its own and the task's
in_hook() {
  local path=$1
  shift
  (cd "$TASKREPO" && env -i PATH="$path" HOME="$HOOKHOME" XDG_CONFIG_HOME="$XDG_CONFIG_HOME" LEM_SERVE=off LEM_TASK=gift-note \
    CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 "$@")
}
# outcome OUTPUT CODE: OUTPUT, then `exit=CODE` on a line of its own; OUTPUT as $(...) has it, with no newline at its end,
# which a hook's text keeps as context all the same
outcome() { if [ -n "$1" ]; then printf '%s\nexit=%s\n' "$1" "$2"; else printf 'exit=%s\n' "$2"; fi; }
# run_line LINE PATH [VAR=VALUE...]: the line through sh -c, its event on stdin; prints its outcome
run_line() {
  local line=$1 path=$2 selector said code=0
  shift 2
  selector=$(sed -n 's/.*hooks\/run" \([a-z-]*\) .*/\1/p' <<<"$line")
  said=$(hook_event "$selector" | in_hook "$path" env "$@" /bin/sh -c "$line" 2>&1) || code=$?
  outcome "$said" "$code"
}
same=yes
shown=""
while IFS= read -r line; do
  selector=$(sed -n 's/.*hooks\/run" \([a-z-]*\) .*/\1/p' <<<"$line")
  handler=$("$APP_PY" -B -c 'import sys; from lem import hooks; print(*hooks.HANDLERS[sys.argv[1]])' "$selector")
  read -r module function <<<"$handler"
  code=0
  alone=$(hook_event "$selector" | in_hook /usr/bin:/bin "$APP_PY" -B -c "from lem import $module; $module.$function()" 2>&1) || code=$?
  alone=$(outcome "$alone" "$code")
  for path in "$(dirname "$HOOK_BIN"):/usr/bin:/bin" /usr/bin:/bin; do
    said=$(run_line "$line" "$path" LEM_HOOK_BIN="$HOOK_BIN")
    [ "$said" = "$alone" ] || { same=no; shown+=" [$selector on $path: $said, alone: $alone]"; }
  done
  shown+=" $selector:$(wc -l <<<"$alone" | tr -d ' ')"
done < <(hook_lines)
compacted=$(run_line "$(hook_lines | sed -n 3p)" /usr/bin:/bin LEM_HOOK_BIN="$HOOK_BIN")
summary=$(run_line "$(hook_lines | sed -n 4p)" /usr/bin:/bin LEM_HOOK_BIN="$HOOK_BIN")
if [ "$same" = yes ] && grep -qF "phase: build, step 2" <<<"$compacted" && grep -qF "the plan" <<<"$compacted" \
  && grep -qF "This summary is the handoff of task gift-note" <<<"$summary" && [ "$(tail -n 1 <<<"$summary")" = "exit=0" ]; then
  pass "each line of hooks/hooks.json, run through sh -c with LEM_HOOK_BIN at the app's lem-hook, gives what its handler gives run alone, the task's files after a compaction and the summary's form before one among them, on a PATH of /usr/bin:/bin too"
else
  fail "the hook lines against their handlers:$shown / $compacted / $summary"
fi
quiet=yes
said_all=""
mkdir -p "$WORK/failing-app"
printf '%s\n' '#!/bin/sh' 'echo "a traceback"' 'echo "on stderr" >&2' 'exit 3' > "$WORK/failing-app/lem-hook"
chmod +x "$WORK/failing-app/lem-hook"
while IFS= read -r line; do
  for case in "LEM_HOOK_BIN=$WORK/no-such-app/lem-hook" "LEM_HOOK_BIN=relative/lem-hook" "LEM_HOOK_BIN=$WORK/failing-app/lem-hook"; do
    said=$(run_line "$line" /usr/bin:/bin "$case")
    [ "$said" = "exit=0" ] || { quiet=no; said_all+=" [$case: $said]"; }
  done
done < <(hook_lines)
if [ "$quiet" = yes ]; then
  pass "a hook line with LEM_HOOK_BIN at a file that is not there, at a relative path, or at an app that prints and exits 3 ends with exit 0 and no output"
else
  fail "a hook line with no app or a failing one:$said_all"
fi
if [ -e /opt/homebrew/opt/lem/libexec/bin/lem-hook ] || [ -e /usr/local/opt/lem/libexec/bin/lem-hook ]; then
  skip "a hook line with no app in any place: this machine has Homebrew's Lem, which the line finds"
else
  none=yes
  while IFS= read -r line; do
    said=$(run_line "$line" /usr/bin:/bin)
    [ "$said" = "exit=0" ] || { none=no; said_all+=" [$said]"; }
  done < <(hook_lines)
  if [ "$none" = yes ] && [ ! -e "$HOOKHOME/.local/bin" ]; then
    pass "a hook line with no LEM_HOOK_BIN and no app in any place (no Homebrew Lem, a home with no .local/bin) ends with exit 0 and no output"
  else
    fail "a hook line with no app:$said_all"
  fi
fi
# The plugin and the app of two versions: a plugin of 0.0.1, with this checkout's hooks, beside this app. The SessionStart line of a session says one
# line as a systemMessage, which names the plugin as the one behind and its update, and writes LEM_PLUGIN_ROOT into the
# file CLAUDE_ENV_FILE names; the line before a compaction does nothing. A command `lem NAME` with that LEM_PLUGIN_ROOT
# stops with the same line and exit 1, but for `lem version`, `lem help` and `lem doctor`; with the plugin of this
# checkout, or with no LEM_PLUGIN_ROOT, it runs.
OLDPLUGIN=$WORK/old-plugin
mkdir -p "$OLDPLUGIN/.claude-plugin" && printf '{"name": "lem", "version": "0.0.1"}\n' > "$OLDPLUGIN/.claude-plugin/plugin.json"
cp -R "$PLUGIN_ROOT/hooks" "$OLDPLUGIN/hooks"
: > "$WORK/session.env"
started=$(hook_event session-start | in_hook /usr/bin:/bin env CLAUDE_PLUGIN_ROOT="$OLDPLUGIN" CLAUDE_ENV_FILE="$WORK/session.env" LEM_HOOK_BIN="$HOOK_BIN" \
  /bin/sh -c "$(hook_lines | sed -n 3p)" 2>&1; echo "exit=$?")
before=$(hook_event precompact | in_hook /usr/bin:/bin env CLAUDE_PLUGIN_ROOT="$OLDPLUGIN" LEM_HOOK_BIN="$HOOK_BIN" /bin/sh -c "$(hook_lines | sed -n 4p)" 2>&1; echo "exit=$?")
message=$(head -n 1 <<<"$started" | field 'd["systemMessage"]' 2>&1 || true)
version_of() { (cd "$HOOKHOME" && env -i PATH=/usr/bin:/bin HOME="$HOOKHOME" XDG_CONFIG_HOME="$XDG_CONFIG_HOME" LEM_SERVE=off "$@"; echo "exit=$?") 2>&1; }
refused=$(version_of LEM_PLUGIN_ROOT="$OLDPLUGIN" "$LEM" project --help)
kept=""
for words in version help "doctor --help"; do
  # shellcheck disable=SC2086  # the words of the command, split as written
  kept+="$(version_of LEM_PLUGIN_ROOT="$OLDPLUGIN" "$LEM" $words | tail -n 1) "
done
same=$(version_of LEM_PLUGIN_ROOT="$PLUGIN_ROOT" "$LEM" project --help | tail -n 1)
plain=$(version_of "$LEM" project --help | tail -n 1)
if grep -qF "lem: Lem's plugin 0.0.1 ($OLDPLUGIN) is behind Lem's app" <<<"$message" && grep -qF "the owner runs \`claude plugin update lem@lem\` and starts the session again" <<<"$message" \
  && [ "$(tail -n 1 <<<"$started")" = "exit=0" ] && [ "$(wc -l <<<"$started" | tr -d ' ')" = 2 ] \
  && [ "$(cat "$WORK/session.env")" = "export LEM_PLUGIN_ROOT='$OLDPLUGIN'" ] && [ "$before" = "exit=0" ] \
  && [ "$refused" = "$message"$'\n'"exit=1" ] && [ "$kept" = "exit=0 exit=0 exit=0 " ] && [ "$same" = "exit=0" ] && [ "$plain" = "exit=0" ]; then
  pass "with a plugin of another version than the app, the SessionStart line says the one line that names the plugin as behind with its update, as a systemMessage, and writes LEM_PLUGIN_ROOT into CLAUDE_ENV_FILE, the line before a compaction does nothing, and a command with that LEM_PLUGIN_ROOT stops with the same line and exit 1 but for version, help and doctor"
else
  fail "two versions: $started / $before / $message / $(cat "$WORK/session.env") / $refused / $kept / $same / $plain"
fi
# The release before this one (lem_release.BEFORE), which each release moves: the version plugin.json held before its
# newest change of version, as git shows it. A release that forgot to move it would stop every task of the release
# before. A clone too shallow to hold that change cannot tell, and says so. The check needs the checkout itself: it
# reads this checkout's release.py beside this checkout's history, in the installed mode too.
before=$(git -C "$PWD" log -p --format=%x00 -- .claude-plugin/plugin.json | "$PY" -c 'import json, re, sys
for change in sys.stdin.read().split("\0"):
    was = re.findall(r"^-\s*\"version\":\s*\"([^\"]+)\"", change, re.M)
    now = re.findall(r"^\+\s*\"version\":\s*\"([^\"]+)\"", change, re.M)
    if was and now:
        print(was[0], now[0])
        break')
read -r was now <<<"${before:-none none}"
said=$("$PY" -B -c 'import sys; sys.path.insert(0, "src"); from lem import release as lem_release; print(lem_release.BEFORE, lem_release.running())')
if [ "$was" = none ]; then
  skip "lem_release.BEFORE is the version plugin.json held before its newest change of version: this clone holds no change of the version (shallow: $(git -C "$PWD" rev-parse --is-shallow-repository))"
elif [ "$said" = "$was $now" ]; then
  pass "lem_release.BEFORE is the version plugin.json held before its newest change of version"
else
  fail "lem_release.BEFORE and the running release are $said, and plugin.json's newest change of version went from $was to $now: a release moves BEFORE to the release before it"
fi
# A machine with Claude Code and no git still gets its rows, not a traceback.
mkdir -p "$WORK/nogit" && cp "$BIN/claude" "$WORK/nogit/claude"
out=$(cd "$WORK" && env -i PATH="$WORK/nogit" HOME="$FAKEHOME" "$LEM" doctor 2>&1 || true)
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
# The correction hook comes with Lem's plugin. A settings file that also names the hook is a second place: the
# machine check names each file with the entry to delete from it by hand, never says to remove the plugin, and never
# fails the machine for it.
want=$("$PY" -c 'import shlex, sys; print("/bin/sh " + shlex.quote(sys.argv[1]) + " corrections")' "$PWD/hooks/run")
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
with_hook "$MACHINE/.claude/settings.json" "LEM_JEV=/x/jev /opt/homebrew/opt/lem/libexec/bin/lem-hook corrections" '{}'
shared_fix=$(hookfield without_it || true)
rm -r "$MACHINE/.claude"
if [ "$alone" = "[]" ] && [ "$plugin_detail" = "registered 2 times for this repository: $MACHINE/.claude/settings.local.json, the plugin lem@lem" ] \
  && grep -qF "The plugin brings the hook, so remove each other place: $MACHINE/.claude/settings.local.json: delete the entry $(entry_of "$want") from the UserPromptSubmit hooks of $MACHINE/.claude/settings.local.json by hand." <<<"$plugin_fix" \
  && grep -qF "it is still judged once" <<<"$plugin_fix" && ! grep -qi "uninstall\|setup" <<<"$plugin_fix" \
  && grep -qF "it does not see managed settings, a session's --settings, or a plugin loaded for one session by a flag" <<<"$plugin_fix" \
  && [ "$plugin_need" = "[('project', False, True)]" ] \
  && [ "$three" = "registered 3 times for this repository: $FAKEHOME/.claude/settings.json, $MACHINE/.claude/settings.local.json, the plugin lem@lem" ] && [ "$off" = "[]" ] \
  && grep -qF "$MACHINE/.claude/settings.json: delete the entry $(entry_of "LEM_JEV=/x/jev /opt/homebrew/opt/lem/libexec/bin/lem-hook corrections") from the UserPromptSubmit hooks of $MACHINE/.claude/settings.json by hand, and commit that." <<<"$shared_fix"; then
  pass "a settings file that also holds the hook beside Lem's plugin is named with the entry to delete from it by hand, never the plugin, and never fails the machine; the plugin alone, or switched off there, gets no row; an entry in the shared settings is a change to commit"
else
  fail "doctor with the hook beside the plugin: $alone / $plugin_detail / $plugin_fix / $plugin_need / $three / $off / $shared_fix"
fi
# With no plugin, two settings files that hold the hook: the row says that the hook comes with the plugin.
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
  pass "with no plugin, the hook in two settings files is named with the plugin that brings it and the entry to delete from each"
else
  fail "doctor with the hook in two settings files and no plugin: $no_plugin / $no_plugin_need"
fi
# Every project of Lem has personas: the machine check, run in a repository that has settings, says when
# there are none or one, through the panel's own check, and that row never fails the machine.
PPL=$WORK/people-repo
git init -q -b main "$PPL" && commit "$PPL" start && project --repo "$PPL" init --base main >/dev/null
git -C "$PPL" add -A && commit "$PPL" "chore: the settings" && git -C "$PPL" worktree add -q "$WORK/people-wt" -b before-the-people
people() { (cd "$1" && env -i PATH="$BIN" HOME="$FAKEHOME" "$LEM" doctor || true) | field '(d["ok"], [(t["need"], t["found"], t["detail"].split(": ")[-1] if t["found"] else t["detail"][:38]) for t in d["tools"] if t["name"] == "project personas"])'; }
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
# It is recommended, as the owner ruled, so onboarding offers it with its guide; nothing fails without it, and it says why.
codexless=$(doctor | row codex without_it)
codex_need=$(doctor | row codex need)
if [ "$codex_need" = recommended ] && grep -qF "highly recommended, since without it Claude reviews the work of Claude" <<<"$codexless" \
  && grep -qF "an expert whose seat names codex (by default the second of seats.experts, the newest Astra of OpenAI) does not answer, so the one expert that can answer" <<<"$codexless" \
  && grep -qF "answers alone and its pick settles a decision the experts take" <<<"$codexless" && grep -qF "a persona panel has the answers of one model family" <<<"$codexless"; then
  pass "with no Codex the codex row is recommended and says it is highly recommended, since without it Claude reviews the work of Claude: the reviewer is a second Claude, the second expert does not answer so its decision ends not green, and a panel has one model family"
else
  fail "the codex row without codex: $codexless"
fi
# The permission mode a builder in the background meets: the repository's local settings first, then its shared ones,
# then the user's; auto and bypassPermissions count from the user's only. The row never fails the machine.
mode() { (cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" "$LEM" doctor || true) | field '[(t["need"], t["found"], t["detail"], t["without_it"][:44]) for t in d["tools"] if t["name"] == "permission mode"]'; }
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
assumed=$( (cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" "$LEM" doctor || true) | field 'next(t["used_for"] for t in d["tools"] if t["name"] == "permission mode")')
rm "$FAKEHOME/.claude/settings.json"
to_auto=$( (cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" "$LEM" doctor || true) | field 'next(t["without_it"] for t in d["tools"] if t["name"] == "permission mode")')
rm -r "$MACHINE/.claude"
outside=$( (cd "$WORK" && env -i PATH="$BIN" HOME="$FAKEHOME" "$LEM" doctor || true) | field '[t["name"] for t in d["tools"] if t["name"] == "permission mode"]')
if [ "$plain" = "[('project', False, 'default: no settings file names one', 'each command the allow list does not hold as')]" ] \
  && [ "$shared" = "[('project', False, 'acceptEdits, from $MACHINE/.claude/settings.json', 'an edit goes through, and each other command')]" ] \
  && [ "$local_bypass" = "$shared" ] \
  && [ "$user_auto" = "[('project', True, 'auto, from $FAKEHOME/.claude/settings.json', 'a builder asks nobody; the classifier may st')]" ] \
  && [ "$outside" = "[]" ] && grep -qF "Lem assumes that Claude Code runs in auto mode" <<<"$assumed" \
  && grep -qF 'Lem assumes auto mode: put "defaultMode": "auto" under "permissions" in your own ~/.claude/settings.json' <<<"$to_auto"; then
  pass "the machine check says that Lem assumes auto mode, and the permission mode a builder meets in the repository, from its local settings, its shared ones or the user's, takes auto and bypassPermissions from the user's only, says what a builder meets and, in another mode, the one line to change, and has no row outside a repository"
else
  fail "the permission mode: $plain / $shared / $local_bypass / $user_auto / $outside / $assumed / $to_auto"
fi
# The modules the plugin's hooks start: a hook whose module is gone or does not compile ends with nothing printed, so
# the machine check names it (tests/unit/test_doctor.py has the broken cases).
hooked=$( (cd "$MACHINE" && env -i PATH="$BIN" HOME="$FAKEHOME" "$LEM" doctor || true) | field '[(t["need"], t["found"]) for t in d["tools"] if t["name"] == "hook modules"]')
if [ "$hooked" = "[('required', True)]" ]; then
  pass "the machine check has a required row of the modules the plugin's hooks start, whole in this clone"
else
  fail "the hook modules row: $hooked"
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
