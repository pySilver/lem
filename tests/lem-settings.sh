#!/usr/bin/env bash
# Lem's project settings, offline: project.py resolves where a repository keeps what the skill reads.
# With no settings file it answers from Lem's own places; what Lem reads beside the settings has one
# place each and no setting; a settings file Lem cannot read is refused through the real command,
# with exit 1, the key and the file (each rule of the file is a unit case, tests/unit/test_settings.py);
# a worktree reads the main checkout's flow table, and the main checkout the base branch's copy while
# another branch is checked out there. Then the task state and the event log, through one journey of
# `state`, `log` and `tasks` for each line and record whose form a rule holds (the type line, the steps
# a ticket is owed and the form of each record are unit cases, tests/unit/test_task_rules.py): the exit
# status, the log that does not grow after a refusal and the newest record in `tasks`. Then the rule
# picker, through one journey of `rules` (a glob's braces and what it matches are unit cases,
# tests/unit/test_rule_picker.py): the rule files it finds in a subfolder and through a link, what it
# reads of their frontmatter, a range of commits with a file that moved, the path forms and the
# refusals. Then a task's criteria and the check that each one's tests fail on the base commit, and the
# board, which reads them all.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

NEW=$WORK/new
git init -q -b main "$NEW"
out=$(project --repo "$NEW" show)
ruled_default=$(project --repo "$NEW" path rulings)
no_ruling_file=0
ruling_file_err=$(project --repo "$NEW" ruling-file header-names 2>&1) || no_ruling_file=$?
if [ "$(field 'd["settings"]' <<<"$out")" = "None" ] && [ "$(field 'd["places"]["rules"]["path"]' <<<"$out")" = "$NEW/.claude/rules" ] \
  && [ "$(field 'd["branch"]["land"]' <<<"$out")" = "agent" ] && [ "$(field 'sorted(d["paths"])' <<<"$out")" = "['plan_file', 'plans', 'rulings']" ] \
  && [ "$(field 'd["paths"]["rulings"]["path"]' <<<"$out")" = "$NEW/docs/rulings.md" ] && [ "$ruled_default" = "$NEW/docs/rulings.md" ] \
  && ! grep -q ruling_file <<<"$out" && [ "$no_ruling_file" = 2 ] && grep -qF "invalid choice: 'ruling-file'" <<<"$ruling_file_err"; then
  pass "with no settings file, show answers from Lem's own places, the paths are the plans folder, a plan's name and the rulings file, docs/rulings.md, no command names a ruling's file, and the merge agent merges"
else
  fail "defaults: $out / $ruled_default / $no_ruling_file / $ruling_file_err"
fi
if [ "$(status_of project --repo "$NEW" init)" = 1 ]; then pass "init refuses a checkout whose base branch it cannot tell"; else fail "init without a base"; fi
project --repo "$NEW" init --base main >/dev/null
# The template names every key show prints under [checks], each with its line in the file init writes.
shown_keys=$(project --repo "$NEW" show | field 'sorted(d["checks"])')
template_keys=$("$PY" -I -c 'import sys, tomllib; print(sorted(tomllib.load(open(sys.argv[1], "rb"))["checks"]))' "$NEW/.lem/settings.toml")
if [ "$shown_keys" = "$template_keys" ] && [ "$shown_keys" = "['commands', 'serial', 'setup']" ]; then
  pass "the settings init writes name every key show prints under [checks]: the commands, their setup and the serial ones"
else
  fail "the [checks] keys of the template: $template_keys, of show: $shown_keys"
fi
# The team's file holds 21 keys, one to one in show (with a tracker, whose one key is its kind), in the file init writes (a
# commented line counts) and on the settings page, of the tables valid in the team's file. `from`, the file a value came
# from (naps.from, state.from, jev.from), is no key.
printf '%s\n' '' '[tracker]' 'kind = "linear"' > "$WORK/tracker.toml"
cp "$NEW/.lem/settings.toml" "$WORK/template.toml" && cat "$WORK/tracker.toml" >> "$NEW/.lem/settings.toml"
shown=$(project --repo "$NEW" show | field 'sorted(f"{table}.{key}" for table in ("paths", "branch", "checks", "flow", "seats", "tracker", "naps", "state", "jev") for key in d[table] if key != "from")')
cp "$WORK/template.toml" "$NEW/.lem/settings.toml"
written=$("$PY" -I -c 'import re, sys
table, found = None, set()
for line in open(sys.argv[1], encoding="utf-8"):
    head = re.match(r"#?\s*\[(\w+)\]\s*$", line)
    if head: table = head.group(1); continue
    key = re.match(r"#?\s*(\w+) = ", line)
    if key and table: found.add(f"{table}.{key.group(1)}")
print(sorted(found))' "$NEW/.lem/settings.toml")
# shellcheck disable=SC2016  # the backticks are the refusal's or the page's own marks
paged=$("$PY" -I -B -c 'import re, sys; sys.path.insert(0, sys.argv[2]); import lem_state
found = re.findall(r"^\| `(\w+)\.(\w+)` \|", open(sys.argv[1], encoding="utf-8").read(), re.M)
print(sorted({f"{table}.{key}" for table, key in found if "team" in lem_state.TABLE_PLACES.get(table, ())}))' "$PWD/docs/settings.md" "$PWD/skills/lem/scripts")
if [ "$shown" = "$written" ] && [ "$shown" = "$paged" ] && [ "$("$PY" -c 'import sys; print(len(eval(sys.argv[1])))' "$shown")" = 21 ]; then
  pass "the team's file holds 21 keys, the same in show, in the file init writes and on the settings page"
else
  fail "the keys of the settings: show $shown / the file $written / the page $paged"
fi
# The tables one machine's own file takes are the same in project.py and in that file's table on the settings page.
# shellcheck disable=SC2016  # the backticks are the page's own marks
local_paged=$("$PY" -I -c 'import re, sys; page = open(sys.argv[1], encoding="utf-8").read().split("## `.lem/settings.local.toml`", 1)[1]; print(re.findall(r"^\| `\[(\w+)\]` \|", page, re.M))' "$PWD/docs/settings.md")
local_coded=$("$PY" -I -B -c 'import sys; sys.path.insert(0, sys.argv[1]); import project; print(list(project.LOCAL_TABLES))' "$PWD/skills/lem/scripts")
if [ "$local_paged" = "$local_coded" ] && [ "$local_coded" = "['seats', 'naps', 'state']" ]; then
  pass "the tables of .lem/settings.local.toml are the same in project.py and on the settings page: the seats, the naps and the state"
else
  fail "the tables of the local file: the page $local_paged / project.py $local_coded"
fi
out=$(project --repo "$NEW" show)
if [ "$(field 'd["branch"]["base"]' <<<"$out")" = "main" ] && [ "$(field 'd["places"]["personas"]["path"]' <<<"$out")" = "$NEW/.lem/personas" ] \
  && [ "$(field '(d["seats"]["reviewer"]["agent"], d["seats"]["reviewer"]["model"])' <<<"$out")" = "('codex', 'gpt-6.2-sol')" ] \
  && [ "$(cat "$NEW/.lem/.gitignore")" = "$(printf 'settings.local.toml\nstate/')" ] && [ "$(field 'd["local"]' <<<"$out")" = "{'file': None, 'overrides': []}" ] \
  && grep -qxF 'land = "agent"' "$NEW/.lem/settings.toml" && grep -qxF 'history = "squash"' "$NEW/.lem/settings.toml" \
  && grep -qxF 'plan_file = "YYYY-MM-DD-<slug>.md"' "$NEW/.lem/settings.toml" && grep -qxF 'reviewer = "codex/gpt-6.2-sol:high"' "$NEW/.lem/settings.toml" \
  && grep -qxF 'planner = "claude/opus:high"' "$NEW/.lem/settings.toml" \
  && grep -qxF 'experts = ["claude/fable:high", "codex/gpt-6.2-astra:high"]' "$NEW/.lem/settings.toml"; then
  pass "init in a new project writes Lem's own places, the given base, the merge agent's merge and one commit for each task, the three seats whole, and ignore rules for the machine's own settings and for Lem's state"
else
  fail "init in a new project: $out"
fi
if [ "$(status_of project --repo "$NEW" init --base main)" = 1 ]; then pass "init refuses a settings file that already exists"; else fail "second init"; fi
# Without Codex on the machine, init writes the reviewer's seat on Claude.
BARE=$WORK/no-codex
git init -q -b main "$BARE"
project --repo "$BARE" init --base main --codex no >/dev/null
if grep -qxF 'reviewer = "claude/opus:high"' "$BARE/.lem/settings.toml" && grep -qxF 'experts = ["claude/fable:high"]' "$BARE/.lem/settings.toml" \
  && [ "$(project --repo "$BARE" show | field '(d["seats"]["reviewer"]["seat"], [(e["seat"], e["place"], e["here"]) for e in d["seats"]["experts"]])')" = "('claude/opus:high', [('claude/fable:high', 'fable', True)])" ]; then
  pass "init with --codex no, for a machine with no Codex, writes the reviewer's whole seat on Claude and one expert, which answers alone in the first place"
else
  fail "init without Codex: $(grep -A1 '^reviewer' "$BARE/.lem/settings.toml")"
fi

# The settings file has one name in three places, and a repository with only the name of an older Lem was never
# onboarded: show reads nothing of that file, init writes .lem/settings.toml beside it, and git ignores the local file.
FORMER=$WORK/former
git init -q -b main "$FORMER" && mkdir -p "$FORMER/.lem" && printf '%s\n' '[branch]' 'base = "trunk"' 'land = "owner"' > "$FORMER/.lem/project.toml"
former_show=$(project --repo "$FORMER" show | field '(d["settings"], d["branch"]["base"], d["branch"]["land"])')
former_init=$(status_of project --repo "$FORMER" init --base main)
touch "$FORMER/.lem/settings.local.toml"
if [ "$former_show" = "(None, None, 'agent')" ] && [ "$former_init" = 0 ] && [ -f "$FORMER/.lem/settings.toml" ] \
  && [ "$(project --repo "$FORMER" show | field '(d["settings"], d["branch"]["base"], d["branch"]["land"])')" = "('$FORMER/.lem/settings.toml', 'main', 'agent')" ] \
  && git -C "$FORMER" check-ignore -q .lem/settings.local.toml && ! git -C "$FORMER" check-ignore -q .lem/settings.toml; then
  pass "a repository with only .lem/project.toml was never onboarded: show reads nothing of it, init writes .lem/settings.toml, and git ignores .lem/settings.local.toml there and not the team's file"
else
  fail "a repository of the older name: $former_show / $former_init / $(cat "$FORMER/.lem/.gitignore" 2>&1)"
fi
# For a seat more than one file may hold, the nearest file that holds it wins, and show names that file in `from`:
# the developer's own file for every repository, a team's file, and his own file for that team's repository.
HOME_FILE=$XDG_CONFIG_HOME/lem/settings.toml
TEAM=$WORK/mybaze OWN=$WORK/lem-repo
git init -q -b main "$TEAM" && git init -q -b main "$OWN"
project --repo "$TEAM" init --base main >/dev/null && project --repo "$OWN" init --base main >/dev/null
merger() { project --repo "$1" show | field '(d["seats"]["merger"]["seat"], d["seats"]["merger"]["from"])'; }
printf '%s\n' '[seats]' 'merger = "claude/opus:high"' > "$HOME_FILE"
"$PY" -I -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("# merger = \"agent/model:effort\"", "merger = \"codex/gpt-6.2-sol:high\"", 1))' "$TEAM/.lem/settings.toml"
by_team=$(merger "$TEAM")
printf '%s\n' '[seats]' 'merger = "claude/fable:high"' > "$TEAM/.lem/settings.local.toml"
by_local=$(merger "$TEAM")
by_home=$(merger "$OWN")
rm "$HOME_FILE"
by_lem=$(merger "$OWN")
if [ "$by_team" = "('codex/gpt-6.2-sol:high', '.lem/settings.toml')" ] && [ "$by_local" = "('claude/fable:high', '.lem/settings.local.toml')" ] \
  && [ "$by_home" = "('claude/opus:high', '$HOME_FILE')" ] && [ "$by_lem" = "('claude/opus:high', \"Lem's default\")" ]; then
  pass "the merge agent is the nearest file's that names one, the local file's, the team's, then the developer's own for every repository, else Lem's default, and show names each in from"
else
  fail "the nearest file wins: $by_team / $by_local / $by_home / $by_lem"
fi

OLD=$WORK/old
git init -q -b master "$OLD"
mkdir -p "$OLD/.claude/rules" "$OLD/.revmux" "$OLD/.personas/cast" "$OLD/docs/plans"
touch "$OLD/.personas/profile.md"
# A repository that keeps a cast and a profile for another tool: init links nothing and asks nothing, and
# writes no setting for a place; each place is Lem's own, and `path` answers for each name.
project --repo "$OLD" init --base master >/dev/null
out=$(project --repo "$OLD" show)
places=$(field '{name: (p["path"].removeprefix(d["root"] + "/"), p["exists"]) for name, p in d["places"].items()}' <<<"$out")
answered=""
for name in profile personas lessons worktrees rules review backlog rulings plans; do answered="$answered $(project --repo "$OLD" path "$name" | sed "s|^$OLD/||")"; done
if [ "$places" = "{'profile': ('.lem/profile.md', False), 'personas': ('.lem/personas', False), 'lessons': ('.lem/lessons.md', False), 'worktrees': ('.lem/worktrees', False), 'rules': ('.claude/rules', True), 'review': ('.revmux', True), 'backlog': ('docs/backlog', False)}" ] \
  && [ "$answered" = " .lem/profile.md .lem/personas .lem/lessons.md .lem/worktrees .claude/rules .revmux docs/backlog docs/rulings.md docs/plans" ] \
  && ! grep -qE '^(profile|personas|lessons|worktrees|styleguide|review|backlog) = ' "$OLD/.lem/settings.toml" && [ -d "$OLD/.personas/cast" ] \
  && [ "$(status_of project --repo "$OLD" init --base master --existing link)" = 2 ]; then
  pass "init over another tool's cast and profile links nothing and moves nothing; each place is Lem's one place, show says whether it exists, and path answers for each name"
else
  fail "init over another tool's folders: $places /$answered"
fi
if [ "$(project --repo "$OLD/docs" path plans)" = "$OLD/docs/plans" ]; then pass "path prints one absolute path, from any directory of the checkout"; else fail "path plans"; fi
if [ "$(status_of project --repo "$OLD" path plan)" = 1 ]; then pass "an unknown path name is refused"; else fail "unknown path name"; fi

settings() { printf '%s\n' "$@" > "$OLD/.lem/settings.toml"; }
# Each rule of a settings file is a unit case of tests/unit/test_settings.py. Here one refusal goes through the real
# command: exit 1, the key and the file named, no traceback.
settings '[branch]' 'base = "master"' 'lands = "agent"'
code=0
err=$(project --repo "$OLD" show 2>&1) || code=$?
if [ "$code" = 1 ] && grep -qF "project.py: $OLD/.lem/settings.toml: unknown key branch.lands; did you mean 'land'?" <<<"$err" && ! grep -q Traceback <<<"$err"; then
  pass "show refuses a settings file with an unknown key: exit 1, and the message names the key, the file and the nearest valid key"
else
  fail "unknown key: $code / $err"
fi
# A seat has one `:` at most, and the reviewer's is written whole: set refuses a second `:` and a seat with no
# model or no effort, and writes nothing. The command reviewer is no command of Lem's: set local reviewer does its work.
settings '[branch]' 'base = "master"'
code=0
two_colons=$(project --repo "$OLD" set local reviewer claude/opus:high:max 2>&1) || code=$?
short_code=0
short=$(project --repo "$OLD" set local reviewer codex 2>&1) || short_code=$?
gone_code=0
gone=$(project --repo "$OLD" reviewer claude/opus:high 2>&1) || gone_code=$?
if [ "$code" = 1 ] && grep -qF "set local reviewer: seats.reviewer = 'claude/opus:high:max' holds 2 \`:\`, and a seat has one at most, before the effort" <<<"$two_colons" \
  && [ "$short_code" = 1 ] && grep -qF "project.py: set local reviewer: seats.reviewer = 'codex' names no model and no effort: it is one string, \"agent/model:effort\", written whole, as \"codex/gpt-6.2-sol:high\"" <<<"$short" \
  && ! grep -q Traceback <<<"$short" && [ ! -e "$OLD/.lem/settings.local.toml" ]; then
  pass "set local reviewer refuses a seat with two colons, naming the colons, and a seat with no model and no effort, showing the whole form, and writes nothing"
else
  fail "a seat with two colons or a short seat: $code / $two_colons / $short_code / $short"
fi
if [ "$gone_code" = 2 ] && grep -qF "invalid choice: 'reviewer'" <<<"$gone" && [ ! -e "$OLD/.lem/settings.local.toml" ]; then
  pass "reviewer is no command of lem project, with no alias, and writes nothing"
else
  fail "the old reviewer command: $gone_code / $gone"
fi
# The settings refuse a reviewer's seat that is not whole, in the project's file and in this machine's own.
settings '[branch]' 'base = "master"' '[seats]' 'reviewer = "codex:high"'
code=0
in_project=$(project --repo "$OLD" show 2>&1) || code=$?
settings '[branch]' 'base = "master"'
printf '%s\n' '[seats]' 'planner = "claude/opus"' > "$OLD/.lem/settings.local.toml"
local_code=0
in_local=$(project --repo "$OLD" show 2>&1) || local_code=$?
rm "$OLD/.lem/settings.local.toml"
if [ "$code" = 1 ] && grep -qF "project.py: .lem/settings.toml: seats.reviewer = 'codex:high' names no model: it is one string, \"agent/model:effort\", written whole, as \"codex/gpt-6.2-sol:high\"" <<<"$in_project" \
  && [ "$local_code" = 1 ] && grep -qF "seats.planner = 'claude/opus' names no effort: it is one string, \"agent/model:effort\", written whole, as \"claude/opus:high\"" <<<"$in_local"; then
  pass "show refuses a reviewer's seat with no model in the project's file and a defender's seat with no effort in this machine's own, each with the whole form"
else
  fail "a seat that is not whole in the settings: $code / $in_project / $local_code / $in_local"
fi

# A plan's file name: paths.plan_file, YYYY-MM-DD-<slug>.md by default.
settings '[branch]' 'base = "master"'
mkdir -p "$OLD/docs/plans"
built=$(project --repo "$OLD" plan-file gift-note --date 2026-11-17 | field '(d["name"], d["found"])')
touch "$OLD/docs/plans/2026-11-16-gift-note.md" "$OLD/docs/plans/2026-11-16-gift-note-extra.md" "$OLD/docs/plans/2026-11-17-other.md"
older=$(project --repo "$OLD" plan-file gift-note | field 'd["found"]')
touch "$OLD/docs/plans/2026-11-17-gift-note.md"
newer=$(project --repo "$OLD" plan-file gift-note | field 'd["found"]')
settings '[paths]' 'plan_file = "<slug>-YYYYMMDD.md"'
own=$(project --repo "$OLD" plan-file gift-note --date 2026-11-18 | field '(d["name"], d["found"])')
touch "$OLD/docs/plans/gift-note-20261118.md"
own_found=$(project --repo "$OLD" plan-file gift-note | field 'd["found"]')
settings '[branch]' 'base = "master"'
path_err=$(project --repo "$OLD" path plan_file 2>&1 || true)
rm -f "$OLD"/docs/plans/*.md
if [ "$built" = "('2026-11-17-gift-note.md', None)" ] && [ "$older" = "$OLD/docs/plans/2026-11-16-gift-note.md" ] && [ "$newer" = "$OLD/docs/plans/2026-11-17-gift-note.md" ] \
  && [ "$own" = "('gift-note-20261118.md', None)" ] && [ "$own_found" = "$OLD/docs/plans/gift-note-20261118.md" ] \
  && grep -qF "paths.plan_file is the pattern of a plan's name, not a path" <<<"$path_err"; then
  pass "a plan's name is paths.plan_file, YYYY-MM-DD-<slug>.md by default; of two plans of the task the newest day wins, another task's plan is never it, and path names the key a pattern"
else
  fail "plan file names: $built / $older / $newer / $own / $own_found / $path_err"
fi
# The rulings are one file of the settings, which init names with its comment and does not make. The folder form, of a
# file for each ruling, stops every command that reads the settings, with the message that names the list file.
settings '[branch]' 'base = "master"' '[paths]' 'rulings = "decisions/rulings.md"'
ruled=$(project --repo "$OLD" path rulings)
settings '[branch]' 'base = "master"' '[paths]' 'rulings = "docs/rulings"'
CORR=$PWD/skills/lem/scripts/corrections.py
stopped_codes="" stopped_said=0
for command in "project show" "project path rulings" "project plan-file header-names" "project prune --dry-run" "project may-nap" "corrections list"; do
  read -r -a argv <<<"$command"
  if [ "${argv[0]}" = project ]; then run=("$PY" -B "$PROJECT"); else run=("$PY" -B "$CORR"); fi
  code=0
  said=$("${run[@]}" --repo "$OLD" "${argv[@]:1}" 2>&1) || code=$?
  stopped_codes="$stopped_codes $code"
  grep -qF "paths.rulings = 'docs/rulings' is no markdown file: paths.rulings names the list file of the owner's rulings" <<<"$said" \
    && grep -qF 'as rulings = "docs/rulings.md"' <<<"$said" && ! grep -q Traceback <<<"$said" && stopped_said=$((stopped_said + 1))
done
settings '[branch]' 'base = "master"' '[paths]' 'rulings = "docs/rulings.md"' 'ruling_file = "<slug>.md"'
old_key_code=0
old_key=$(project --repo "$OLD" show 2>&1) || old_key_code=$?
settings '[branch]' 'base = "master"'
if [ "$ruled" = "$OLD/decisions/rulings.md" ] && [ "$stopped_codes" = " 1 1 1 1 1 1" ] && [ "$stopped_said" = 6 ] \
  && [ "$old_key_code" = 1 ] && grep -qF "unknown key paths.ruling_file; did you mean 'plan_file'? valid: plans, plan_file, rulings" <<<"$old_key" \
  && grep -qxF 'rulings = "docs/rulings.md"' "$NEW/.lem/settings.toml" && grep -qF '# The rulings file: the list of your product decisions, one bullet for each' "$NEW/.lem/settings.toml" \
  && ! grep -q ruling_file "$NEW/.lem/settings.toml" && [ ! -e "$NEW/docs/rulings.md" ]; then
  pass "the rulings file is a setting: path rulings answers from it, the folder form stops every command that reads the settings with the fix, ruling_file is a key Lem does not know, and init writes the default with its comment and no file"
else
  fail "the rulings in the settings: $ruled /$stopped_codes / $stopped_said / $old_key_code / $old_key"
fi

settings '[branch]' 'base = "v2"' 'protected = ["master", "develop"]'
err=$(project --repo "$OLD" may-land master 2>&1 || true)
unborn=$(project --repo "$OLD" may-land v2 2>&1 || true)
commit "$OLD" "the first commit" && git -C "$OLD" branch v2
if [ "$(status_of project --repo "$OLD" may-land master)" = 1 ] && grep -q "protected" <<<"$err" && [ "$(status_of project --repo "$OLD" may-land feature)" = 1 ] \
  && grep -qF "branch.base = 'v2' is no branch of this repository" <<<"$unborn" && [ "$(status_of project --repo "$OLD" may-land v2)" = 0 ]; then
  pass "may-land refuses a protected branch, any branch but the base, and a base the repository does not have, and accepts the base"
else
  fail "may-land: $err / $unborn"
fi
settings '[paths]' 'plans = "."'
root_worktrees=$(project --repo "$OLD" worktree-dir some-task 2>&1 || true)
if grep -qF "paths.plans = '.' names the root of the checkout" <<<"$root_worktrees" && [ ! -e "$OLD/.gitignore" ] && ! grep -q Traceback <<<"$root_worktrees"; then
  pass "worktree-dir refuses settings whose plans folder is the root of the checkout, and writes no ignore file then"
else
  fail "a root folder in the settings of worktree-dir: $root_worktrees / $(cat "$OLD/.gitignore" 2>&1)"
fi
if [ "$(status_of project --repo "$WORK" show)" = 1 ]; then pass "a directory outside any checkout is refused"; else fail "outside a checkout"; fi

# Task state: one directory per task in the main checkout's state folder, seen from every worktree.
commit "$OLD" start
git -C "$OLD" worktree add -q "$WORK/wt" -b feat/x
dir=$(project --repo "$WORK/wt" task-dir report-dates-stay-whole)
if [ "$dir" = "$OLD/.lem/state/tasks/report-dates-stay-whole" ] && [ -d "$dir/reports" ] && [ -z "$(git -C "$WORK/wt" status --porcelain)" ]; then
  pass "task-dir, run in a worktree, makes the task's directory in the main checkout's state folder"
else
  fail "task-dir: $dir"
fi
settings '[branch]' 'base = "master"'
where=$(project --repo "$OLD" worktree-dir report-dates-stay-whole)
if [ "$where" = "$OLD/.lem/worktrees/report-dates-stay-whole" ] && [ ! -e "$where" ] && [ -z "$(git -C "$OLD" status --porcelain -- .lem/worktrees)" ]; then
  pass "worktree-dir names a path under a folder git status never shows, and makes no worktree itself"
else
  fail "worktree-dir: $where / $(git -C "$OLD" status --porcelain -- .lem/worktrees)"
fi
if [ "$(project --repo "$WORK/wt" state-dir)" = "$OLD/.lem/state" ]; then pass "state-dir prints the one folder every worktree shares"; else fail "state-dir"; fi
if [ "$(status_of project --repo "$OLD" task-dir "Report Dates")" = 1 ]; then pass "a slug that is not hyphenated lower-case words is refused"; else fail "slug form"; fi
printf '%s\n' 'Keep report dates whole.' '' 'more' > "$dir/task.md"
project --repo "$OLD" state report-dates-stay-whole queued "waits for a free place" >/dev/null
project --repo "$WORK/wt" state report-dates-stay-whole building "task 2 of 3" "next: the report" >/dev/null
out=$(project --repo "$OLD" tasks)
if [ "$(field 'd[0]["ask"]' <<<"$out")" = "Keep report dates whole." ] && [ "$(field 'd[0]["state"].splitlines()[-1]' <<<"$out")" = "next: the report" ] \
  && [ "$(field 'len(d)' <<<"$out")" = 1 ] && [ "$(field 'd[0]["status"]' <<<"$out")" = "building" ] \
  && [ "$(field 'd[0]["state"].splitlines()[0] == d[0]["since"] + " building: task 2 of 3"' <<<"$out")" = "True" ] \
  && [ "$(grep -c '' "$dir/state.md")" = 4 ] && [ "$(sed -n 4p "$dir/state.md" | cut -d' ' -f2-)" = "queued: waits for a free place" ]; then
  pass "state puts a block with the clock's time above the older ones, and tasks lists the ask, the status and only the newest block"
else
  fail "state and tasks: $out / $(cat "$dir/state.md")"
fi
code=0
err=$(project --repo "$OLD" state report-dates-stay-whole build "task 3" 2>&1) || code=$?
if [ "$code" = 1 ] && grep -q "did you mean 'building'" <<<"$err" \
  && [ "$(status_of project --repo "$OLD" state no-such-task ready "report written")" = 1 ] \
  && [ "$(status_of project --repo "$OLD" state report-dates-stay-whole ready "report written" "")" = 1 ] \
  && [ "$(status_of project --repo "$OLD" state report-dates-stay-whole ready)" != 0 ] && [ "$(grep -c '' "$dir/state.md")" = 4 ]; then
  pass "state refuses a status no task has, a task that was never opened and an empty line, and writes nothing then"
else
  fail "state refusals: $err / $(cat "$dir/state.md")"
fi
# The owner's words have a file of their own; without it the first words of task.md stand in, without their markup.
titled=$(project --repo "$OLD" task-dir asked-in-words --ask "the report dates must stay whole,
also across a month")
printf '%s\n' '# Report dates stay whole' '' '## The ask' > "$titled/task.md"
plain=$(project --repo "$OLD" task-dir titled-only)
printf '%s\n' '' '## A heading comes first' 'text' > "$plain/task.md"
out=$(project --repo "$OLD" tasks)
if [ "$(field '{t["slug"]: t["ask"] for t in d if t["slug"] in ("asked-in-words", "titled-only")}' <<<"$out")" = "{'asked-in-words': 'the report dates must stay whole, also across a month', 'titled-only': 'A heading comes first'}" ] \
  && [ "$(status_of project --repo "$OLD" task-dir empty-ask --ask " ")" = 1 ]; then
  pass "task-dir --ask keeps the owner's words for the status and the board, and a task without them shows the first words of task.md with no markup"
else
  fail "the ask of a task: $out"
fi
if [ -e "$OLD/.lem/state/tasks/empty-ask" ]; then fail "a refused task-dir made its directory"; fi
rm -r "$titled" "$plain"
# Text that is not UTF-8, in a file Lem reads or in an argument it writes down, is refused with its place, never a traceback.
events_before=$(grep -c '' "$OLD/.lem/state/events.jsonl")
bad_ask=$(project --repo "$OLD" task-dir bad-bytes --ask $'caf\xe9 au lait' 2>&1 || true)
bad_line=$(project --repo "$OLD" state report-dates-stay-whole building $'task 3 of 3 \xff' 2>&1 || true)
bad_field=$(project --repo "$OLD" log report-dates-stay-whole gate $'last=\xff' 2>&1 || true)
bad_field="$bad_field $(project --repo "$OLD" log report-dates-stay-whole gate 'last:="\udcff"' 2>&1 || true)"
cp "$OLD/.lem/settings.toml" "$WORK/settings.kept" && printf '[branch]\nbase = "caf\351"\n' > "$OLD/.lem/settings.toml"
bad_settings=$(project --repo "$OLD" show 2>&1 || true)
cp "$WORK/settings.kept" "$OLD/.lem/settings.toml"
mkdir -p "$OLD/.lem/state/tasks/latin-state" && printf '2026-01-01T00:00Z building: caf\351\n' > "$OLD/.lem/state/tasks/latin-state/state.md"
bad_state=$(project --repo "$OLD" tasks 2>&1 || true)
rm -r "$OLD/.lem/state/tasks/latin-state"
if grep -qF "the argument b'caf\\xe9 au lait' is not UTF-8 text" <<<"$bad_ask" && [ ! -e "$OLD/.lem/state/tasks/bad-bytes" ] \
  && grep -qF "is not UTF-8 text" <<<"$bad_line" && grep -qF "is not UTF-8 text; give it in UTF-8" <<<"$bad_field" && grep -qF "a field of the event is not UTF-8 text" <<<"$bad_field" \
  && grep -qF "$OLD/.lem/settings.toml is not UTF-8 text" <<<"$bad_settings" && grep -qF "latin-state/state.md is not UTF-8 text" <<<"$bad_state" \
  && [ "$(grep -c '' "$OLD/.lem/state/events.jsonl")" = "$events_before" ] && ! grep -q Traceback <<<"$bad_ask$bad_line$bad_field$bad_settings$bad_state"; then
  pass "an argument or a file of text that is not UTF-8 is refused with the argument or the file named, and nothing is written"
else
  fail "text that is not UTF-8: $bad_ask / $bad_line / $bad_field / $bad_settings / $bad_state"
fi
# A ticket needs a tracker: with no [tracker], --ticket is refused with the table that adds one.
no_tracker=$(project --repo "$OLD" task-dir from-a-ticket --ticket MBZ-12 2>&1 || true)
no_tracker_dir=$([ -e "$OLD/.lem/state/tasks/from-a-ticket" ] && echo made || echo none)
# One ticket is one task, until that task is dropped or answered and owes the ticket nothing. The states
# are written by hand in the script's own form, so that the event log the next checks count stays as it is.
settings '[branch]' 'base = "master"' '[tracker]' 'kind = "linear"'
project --repo "$OLD" task-dir from-a-ticket --ticket mbz-12 --ask "Report dates are cut" >/dev/null
err=$(project --repo "$OLD" task-dir the-same-ticket --ticket MBZ-12 2>&1 || true)
number=$(project --repo "$OLD" task-dir an-issue-number --ticket 42 2>&1 || true)
if [ "$(project --repo "$OLD" tasks | field '{t["slug"]: t["ticket"] for t in d}')" = "{'from-a-ticket': 'MBZ-12', 'report-dates-stay-whole': None}" ] \
  && grep -qF "has no [tracker]: add the table with its kind (kind = \"linear\" or kind = \"github\")" <<<"$no_tracker" && [ "$no_tracker_dir" = none ] \
  && grep -q "the task 'from-a-ticket' already holds the ticket MBZ-12" <<<"$err" && [ ! -e "$OLD/.lem/state/tasks/the-same-ticket" ] \
  && grep -qF "is not a ticket's id, such as MBZ-12: the project's tracker is linear" <<<"$number" && [ ! -e "$OLD/.lem/state/tasks/an-issue-number" ] \
  && [ "$(status_of project --repo "$OLD" task-dir bad-ticket --ticket "not a ticket")" = 1 ] && [ ! -e "$OLD/.lem/state/tasks/bad-ticket" ] \
  && [ "$(status_of project --repo "$OLD" task-dir from-a-ticket --ticket MBZ-13)" = 1 ] && [ "$(cat "$OLD/.lem/state/tasks/from-a-ticket/ticket.txt")" = MBZ-12 ] \
  && [ "$(status_of project --repo "$OLD" task-dir with-a-repo --ticket MBZ-14 --ticket-repo acme/shop)" = 1 ] \
  && project --repo "$OLD" task-dir from-a-ticket --ticket MBZ-12 >/dev/null; then
  pass "a task keeps the ticket its ask came from: no tracker, a second task for that ticket, another ticket for that task, an issue's number in a Linear project and a word that is no ticket are refused"
else
  fail "a task's ticket: $(project --repo "$OLD" tasks | field '[(t["slug"], t["ticket"]) for t in d]') / $no_tracker / $err / $number"
fi
# What Lem did to the ticket is written down once for each step.
out=$(project --repo "$OLD" ticket-step from-a-ticket started)
project --repo "$OLD" ticket-step from-a-ticket commented >/dev/null
if [ "$(field '(d["ticket"], d["steps"])' <<<"$out")" = "('MBZ-12', ['started'])" ] && [ "$(status_of project --repo "$OLD" ticket-step from-a-ticket started)" = 1 ] \
  && [ "$(status_of project --repo "$OLD" ticket-step from-a-ticket closed)" = 1 ] && [ "$(status_of project --repo "$OLD" ticket-step report-dates-stay-whole started)" = 1 ] \
  && [ "$(project --repo "$OLD" tasks | field 'next(t["ticket_steps"] for t in d if t["slug"] == "from-a-ticket")')" = "['started', 'commented']" ]; then
  pass "ticket-step writes each thing Lem did to a ticket down once, and refuses a second time, an unknown step and a task with no ticket"
else
  fail "ticket-step: $out / $(project --repo "$OLD" tasks | field '[(t["slug"], t["ticket_steps"]) for t in d]')"
fi
# A task that ended still owes its ticket the steps that are not written down (`ticket_owed`, a unit case,
# tests/unit/test_task_rules.py).
printf '%s\n' '2026-01-01T00:00Z dropped: the owner dropped it' > "$OLD/.lem/state/tasks/from-a-ticket/state.md"
err=$(project --repo "$OLD" task-dir from-a-ticket --ticket MBZ-12 2>&1 || true)
owes=$(project --repo "$OLD" task-dir the-same-ticket --ticket MBZ-12 2>&1 || true)
owes_dir=$([ -e "$OLD/.lem/state/tasks/the-same-ticket" ] && echo made || echo none)
project --repo "$OLD" ticket-step from-a-ticket dropped >/dev/null
if grep -q "is dropped; a new task takes a slug of its own" <<<"$err" && [ "$owes_dir" = none ] \
  && grep -qF "the task 'from-a-ticket' is dropped and still owes the ticket MBZ-12 dropped: pay it with the lem-linear skill's step \`drop\` for from-a-ticket, run from a session" <<<"$owes" \
  && project --repo "$OLD" task-dir the-same-ticket --ticket MBZ-12 >/dev/null \
  && [ "$(project --repo "$OLD" tasks | field 'next(t["ticket_steps"] for t in d if t["slug"] == "the-same-ticket")')" = "[]" ]; then
  pass "a dropped task holds its ticket while it owes the drop comment, and gives it back after, to a task with a slug of its own, which starts with no step written down"
else
  fail "the ticket of a dropped task: $err / $owes"
fi
# A task that ended with an answer gives its ticket back too, once the answer's comment is written down.
owed_by() { project --repo "$OLD" tasks | field "next(t[\"ticket_owed\"] for t in d if t[\"slug\"] == \"$1\")"; }
printf '%s\n' '2026-01-01T00:00Z answered: not a bug: the report cuts no date' > "$OLD/.lem/state/tasks/the-same-ticket/state.md"
answered=$(owed_by the-same-ticket)
early=$(project --repo "$OLD" task-dir after-the-answer --ticket MBZ-12 2>&1 || true)
project --repo "$OLD" ticket-step the-same-ticket answered >/dev/null
again=$(project --repo "$OLD" task-dir after-the-answer --ticket MBZ-12 2>&1 || true)
if [ "$answered" = "['answered']" ] && grep -qF "the lem-linear skill's step \`answer\` for the-same-ticket" <<<"$early" \
  && [ "$(project --repo "$OLD" tasks | field '{t["slug"]: t["ticket"] for t in d if t["ticket"]}')" = "{'after-the-answer': 'MBZ-12', 'from-a-ticket': 'MBZ-12', 'the-same-ticket': 'MBZ-12'}" ] \
  && [ "$(owed_by the-same-ticket)" = "[]" ] && [ "$(owed_by after-the-answer)" = "[]" ] && [ "$(cat "$OLD/.lem/state/tickets/MBZ-12")" = after-the-answer ]; then
  pass "an answered task holds its ticket until the step answered is written down, then gives it to a task with a slug of its own, which takes its mark"
else
  fail "the ticket of an answered task: $answered / $early / $again / $(owed_by the-same-ticket)"
fi
settings '[branch]' 'base = "master"'
rm -r "$OLD/.lem/state/tasks/from-a-ticket" "$OLD/.lem/state/tasks/the-same-ticket" "$OLD/.lem/state/tickets"
rm -rf "$OLD/.lem/state/tasks/after-the-answer"
# A project whose tracker is GitHub, in a repository of its own so that the log the next checks count stays
# as it is: the id of an issue is its number after `#`, kept with the repository of the issue that was read.
GH=$WORK/issues
git init -q -b main "$GH"
mkdir -p "$GH/.lem"
printf '%s\n' '[branch]' 'base = "main"' '[tracker]' 'kind = "github"' > "$GH/.lem/settings.toml"
printf '%s\n' 'state/' > "$GH/.lem/.gitignore"
git -C "$GH" add .lem && commit "$GH" "the settings"
gh_tasks() { project --repo "$GH" tasks | field "$1"; }
shown_tracker=$(project --repo "$GH" show | field 'd["tracker"]')
project --repo "$GH" task-dir export-keeps-gift-note --ticket 42 --ticket-repo acme/shop --ask "the export drops the gift note" >/dev/null
hashed=$(project --repo "$GH" task-dir export-keeps-gift-note --ticket "#42" --ticket-repo acme/shop 2>&1 && echo taken)
second=$(project --repo "$GH" task-dir gift-note-in-export --ticket 42 --ticket-repo acme/shop 2>&1 || true)
linear_id=$(project --repo "$GH" task-dir a-linear-id --ticket MBZ-12 --ticket-repo acme/shop 2>&1 || true)
no_repo=$(project --repo "$GH" task-dir no-repo --ticket 43 2>&1 || true)
GD=$GH/.lem/state/tasks/export-keeps-gift-note
if [ "$shown_tracker" = "{'kind': 'github'}" ] && grep -q "taken$" <<<"$hashed" && [ "$(cat "$GD/ticket.txt")" = "#42" ] && [ "$(cat "$GD/ticket-repo.txt")" = acme/shop ] \
  && [ "$(gh_tasks '[(t["slug"], t["ticket"], t["ticket_repo"]) for t in d]')" = "[('export-keeps-gift-note', '#42', 'acme/shop')]" ] \
  && grep -qF "the task 'export-keeps-gift-note' already holds the ticket #42" <<<"$second" \
  && grep -qF "is not an issue's number, such as 42 or #42: the project's tracker is github" <<<"$linear_id" \
  && grep -qF "give it as --ticket-repo OWNER/REPO" <<<"$no_repo" \
  && [ "$(status_of project --repo "$GH" task-dir export-keeps-gift-note --ticket 42 --ticket-repo acme/fork)" = 1 ] \
  && [ "$(status_of project --repo "$GH" task-dir bad-repo --ticket 44 --ticket-repo "not a repo")" = 1 ] \
  && [ "$(find "$GH/.lem/state/tasks" -mindepth 1 -maxdepth 1 | wc -l | tr -d ' ')" = 1 ]; then
  pass "with the tracker github, --ticket 42 and --ticket '#42' keep #42 with the issue's repository; a second task for #42, a Linear id, no repository and another repository for the task are refused"
else
  fail "a GitHub ticket: $shown_tracker / $hashed / $second / $linear_id / $no_repo / $(gh_tasks '[(t["slug"], t["ticket"], t["ticket_repo"]) for t in d]')"
fi
# The assignee Lem adds is written down with its login, and a drop owes its removal.
project --repo "$GH" ticket-step export-keeps-gift-note assigned --login octo-cat >/dev/null
project --repo "$GH" ticket-step export-keeps-gift-note started >/dev/null
assignee=$(gh_tasks 'next((t["ticket_steps"], t["ticket_assignee"]) for t in d if t["slug"] == "export-keeps-gift-note")')
no_login=$(project --repo "$GH" ticket-step export-keeps-gift-note assigned 2>&1 || true)
if [ "$assignee" = "(['assigned', 'started'], 'octo-cat')" ] && [ "$(head -n 1 "$GD/ticket-steps.txt")" = "assigned octo-cat" ] \
  && grep -qF "give it as --login LOGIN" <<<"$no_login" && [ "$(status_of project --repo "$GH" ticket-step export-keeps-gift-note commented --login octo-cat)" = 1 ]; then
  pass "ticket-step assigned keeps the login on its line, tasks gives it as ticket_assignee, and a login with another step or no login with assigned is refused"
else
  fail "the assignee's step: $assignee / $(cat "$GD/ticket-steps.txt") / $no_login"
fi
# A landed task keeps its issue: a new task for it, after the issue is reopened, is refused with the landed task named.
printf '%s\n' '2026-01-01T00:00Z landed: main a..b' > "$GD/state.md"
reopened=$(project --repo "$GH" task-dir gift-note-reopened --ticket 42 --ticket-repo acme/shop 2>&1 || true)
landed_owed=$(gh_tasks 'next(t["ticket_owed"] for t in d if t["slug"] == "export-keeps-gift-note")')
if grep -qF "the task 'export-keeps-gift-note' landed the ticket #42" <<<"$reopened" && grep -qF "start the new task from the owner's own words" <<<"$reopened" \
  && [ "$landed_owed" = "['commented', 'landed']" ] && [ ! -e "$GH/.lem/state/tasks/gift-note-reopened" ]; then
  pass "a landed task keeps its issue for good: a new task for it is refused, and the refusal names the task and says to start from the owner's own words"
else
  fail "a landed task's issue: $reopened / $landed_owed"
fi
# A dropped task holds its issue until the comment and the assignee's removal are written down, and the
# refusal names the line that pays them; a resume of a dropped task takes the issue with it, its mark
# too, and is refused while another task holds the issue.
GF=$GH/.lem/state/tasks/gift-note-first
project --repo "$GH" task-dir gift-note-first --ticket 7 --ticket-repo acme/shop --ask "the gift note is lost" >/dev/null
project --repo "$GH" ticket-step gift-note-first assigned --login octo-cat >/dev/null
printf '%s\n' '2026-01-01T00:00Z dropped: the owner dropped it' > "$GF/state.md"
printf '%s\n' '{"id": 1, "at": "2026-01-01T00:00:00Z", "kind": "breaker", "cause": "criteria", "what": "no place keeps the note", "document": "breaker.md", "handoff": "handoff.md"}' > "$GF/decisions.jsonl"
printf '%s\n' '# Handoff' > "$GF/handoff.md"
owed_drop=$(project --repo "$GH" task-dir gift-note-other --ticket 7 --ticket-repo acme/shop 2>&1 || true)
project --repo "$GH" ticket-step gift-note-first dropped >/dev/null
project --repo "$GH" ticket-step gift-note-first unassigned >/dev/null
mark_gone=$([ -e "$GH/.lem/state/tickets/7" ] && echo kept || echo gone)
project --repo "$GH" task-dir gift-note-other --ticket 7 --ticket-repo acme/shop >/dev/null
held_resume=$(project --repo "$GH" resume gift-note-first 2>&1 || true)
held_dir=$([ -e "$GH/.lem/state/tasks/gift-note-first-2" ] && echo made || echo none)
printf '%s\n' '2026-01-01T00:00Z dropped: the owner dropped it too' > "$GH/.lem/state/tasks/gift-note-other/state.md"
project --repo "$GH" ticket-step gift-note-other dropped >/dev/null
resumed=$(project --repo "$GH" resume gift-note-first 2>"$WORK/resume.err" | field 'd["task"]' 2>&1 || true)
GR=$GH/.lem/state/tasks/gift-note-first-2
if grep -qF "the task 'gift-note-first' is dropped and still owes the ticket #7 dropped, unassigned: pay it with the line \`lem issue drop gift-note-first\`" <<<"$owed_drop" \
  && [ "$mark_gone" = gone ] && grep -qF "the task 'gift-note-other' already holds the ticket #7" <<<"$held_resume" && [ "$held_dir" = none ] \
  && [ "$resumed" = gift-note-first-2 ] && [ "$(cat "$GR/ticket.txt")" = "#7" ] && [ "$(cat "$GR/ticket-repo.txt")" = acme/shop ] \
  && [ "$(cat "$GH/.lem/state/tickets/7")" = gift-note-first-2 ] \
  && [ "$(gh_tasks 'next((t["ticket"], t["ticket_repo"], t["ticket_steps"]) for t in d if t["slug"] == "gift-note-first-2")')" = "('#7', 'acme/shop', [])" ]; then
  pass "a dropped task holds its issue while it owes the comment and the assignee's removal, named with lem issue drop; a resume takes the issue and its mark, and is refused while another task holds it"
else
  fail "a dropped GitHub task and its resume: $owed_drop / $mark_gone / $held_resume / $resumed / $(cat "$WORK/resume.err") / $(ls "$GH/.lem/state/tickets" 2>&1)"
fi
# An opening refused after its claim gives the issue's mark back. A slug made from the issue's title is the slug of a
# task that holds other words, so the opening is refused, and the same issue then opens under another slug. A resume
# that git refuses, since the new task's branch is there already, leaves the mark with the dropped task, which still owes.
project --repo "$GH" task-dir gift-note-words --ask "keep the gift note in the export" >/dev/null
other_words=$(project --repo "$GH" task-dir gift-note-words --ask "Each export drops the gift note." --ticket 12 --ticket-repo acme/shop 2>&1 || true)
words_mark=$([ -e "$GH/.lem/state/tickets/12" ] && echo kept || echo gone)
other_slug=$(project --repo "$GH" task-dir gift-note-in-the-export --ask "Each export drops the gift note." --ticket 12 --ticket-repo acme/shop 2>&1 && echo opened || true)
GL=$GH/.lem/state/tasks/gift-note-later
project --repo "$GH" task-dir gift-note-later --ticket 9 --ticket-repo acme/shop --ask "the gift note is lost again" >/dev/null
project --repo "$GH" ticket-step gift-note-later assigned --login octo-cat >/dev/null
printf '%s\n' '2026-01-01T00:00Z dropped: the owner dropped it' > "$GL/state.md"
printf '%s\n' '{"id": 1, "at": "2026-01-01T00:00:00Z", "kind": "breaker", "cause": "criteria", "what": "no place keeps the note", "document": "breaker.md", "handoff": "handoff.md"}' > "$GL/decisions.jsonl"
printf '%s\n' '# Handoff' > "$GL/handoff.md"
printf '%s\n' '{"ts": "2026-01-01T00:00:00Z", "event": "task.state", "task": "gift-note-later", "status": "building", "branch": "feat/gift-note-later"}' >> "$GH/.lem/state/events.jsonl"
git -C "$GH" branch feat/gift-note-later
git -C "$GH" branch feat/gift-note-later-2
git_refused=$(project --repo "$GH" resume gift-note-later 2>&1 || true)
later=$(gh_tasks 'next((t["ticket_owed"], t["ticket_held_by"]) for t in d if t["slug"] == "gift-note-later")')
if grep -qF "the task 'gift-note-words' holds other words already" <<<"$other_words" && [ "$words_mark" = gone ] && [ ! -e "$GH/.lem/state/tasks/gift-note-words/ticket.txt" ] \
  && grep -q "opened$" <<<"$other_slug" && [ "$(cat "$GH/.lem/state/tickets/12")" = gift-note-in-the-export ] \
  && grep -qF "git could not make feat/gift-note-later-2 from feat/gift-note-later" <<<"$git_refused" && [ ! -e "$GH/.lem/state/tasks/gift-note-later-2" ] \
  && [ "$(cat "$GH/.lem/state/tickets/9")" = gift-note-later ] && [ "$later" = "(['dropped', 'unassigned'], None)" ]; then
  pass "an opening refused after its claim of the issue gives the mark back: the issue opens under another slug, and a resume git refuses leaves the dropped task holding the issue it still owes"
else
  fail "a refused opening and the issue's mark: $other_words / $words_mark / $other_slug / $git_refused / $later / $(ls "$GH/.lem/state/tickets" 2>&1)"
fi
none=$(project --repo "$OLD" tasks | field '[t["proposal"] for t in d]')
echo '{"proposed": "0123", "pr": {"number": 7, "url": "https://github.com/acme/shop/pull/7"}, "not_green": ["criterion 1 changed during the build: y is taken."]}' > "$dir/landing.json"
if [ "$none" = "[None]" ] && [ "$(project --repo "$OLD" tasks | field '[t["proposal"] for t in d]')" = "[{'pull_request': 'https://github.com/acme/shop/pull/7', 'green': False, 'not_green': ['criterion 1 changed during the build: y is taken.'], 'conflict': None, 'merge_review': None, 'merge_refused': None}]" ]; then
  pass "tasks says what a landing proposed: the pull request's address, green or each reason it is not, no conflict while nothing asked the forge, and no merge review before the merge agent read it"
else
  fail "the proposal in tasks: $(project --repo "$OLD" tasks)"
fi
# A landing record that is not JSON stops `tasks` for every task, so the message names the way out land.py takes too.
printf '{"proposed": "01' > "$dir/landing.json"
cut_record=$(project --repo "$OLD" tasks 2>&1 || true)
echo '[]' > "$dir/landing.json"
list_record=$(project --repo "$OLD" tasks 2>&1 || true)
rm "$dir/landing.json"
if grep -qF "$dir/landing.json does not read as JSON" <<<"$cut_record" && grep -qF "Move it aside, then \`lem project state report-dates-stay-whole ready --start-over \"WHY\"\` and \`lem land start report-dates-stay-whole\`" <<<"$cut_record" \
  && grep -qF "$dir/landing.json is not an object" <<<"$list_record" && grep -qF "Move it aside" <<<"$list_record" && ! grep -q Traceback <<<"$cut_record$list_record"; then
  pass "a landing record that is not JSON, or not an object, is named with the way out: move it aside, the state ready, and land.py start"
else
  fail "a broken landing record in tasks: $cut_record / $list_record"
fi
other=$(project --repo "$OLD" task-dir written-by-hand)
printf '%s\n' '2026-01-02 build: task 2 of 3 running' > "$other/state.md"
out=$(project --repo "$OLD" tasks)
if [ "$(field '[(t["slug"], t["status"]) for t in d]' <<<"$out")" = "[('report-dates-stay-whole', 'building'), ('written-by-hand', None)]" ]; then
  pass "a state block that state did not write has no status"
else
  fail "hand-written state: $out"
fi

# This machine's own settings: read from the main checkout in a worktree too, only seats and the few keys one machine may set.
settings '[branch]' 'base = "master"' '[seats]' 'reviewer = "codex/the-usual:high"'
out=$(project --repo "$WORK/wt" set local reviewer claude/a-claude-model:high)
if [ "$(field '(d["seat"], d["file"])' <<<"$out")" = "({'agent': 'claude', 'model': 'a-claude-model', 'effort': 'high', 'seat': 'claude/a-claude-model:high', 'from': '.lem/settings.local.toml'}, '$OLD/.lem/settings.local.toml')" ] \
  && [ -f "$OLD/.lem/settings.local.toml" ] && [ ! -e "$WORK/wt/.lem/settings.local.toml" ] && grep -qxF 'reviewer = "claude/a-claude-model:high"' "$OLD/.lem/settings.local.toml" \
  && [ "$(project --repo "$OLD" show | field '(d["seats"]["reviewer"]["agent"], d["seats"]["reviewer"]["model"], d["local"]["file"])')" = "('claude', 'a-claude-model', '$OLD/.lem/settings.local.toml')" ]; then
  pass "set local reviewer AGENT/MODEL:EFFORT, run in a worktree, writes this machine's seat in the main checkout in the same form; it replaces the project's seat whole and its from says so"
else
  fail "reviewer override: $out"
fi
# A value the owner wrote by hand keeps every character through a rewrite: a rocket, a quote, a backslash.
printf '%s\n' 'planner = "claude/my\"own\"-🚀\\x:high"' >> "$OLD/.lem/settings.local.toml"
project --repo "$OLD" set local reviewer claude/opus:high >/dev/null
out=$(project --repo "$OLD" set local reviewer default)
if [ "$(field '(d["seat"]["agent"], d["seat"]["model"], d["seat"]["effort"], d["seat"]["from"])' <<<"$out")" = "('codex', 'the-usual', 'high', '.lem/settings.toml')" ] \
  && [ "$(project --repo "$OLD" show | field 'd["seats"]["planner"]["model"]')" = 'my"own"-🚀\x' ] && ! grep -q "^reviewer" "$OLD/.lem/settings.local.toml"; then
  pass "set local reviewer default gives the project's reviewer back and keeps what else the machine set, character for character"
else
  fail "set local reviewer default: $out / $(cat "$OLD/.lem/settings.local.toml")"
fi
printf '%s\n' '[checks]' 'commands = []' > "$OLD/.lem/settings.local.toml"
code=0
err=$(project --repo "$OLD" show 2>&1) || code=$?
if [ "$code" = 1 ] && grep -qF ".lem/settings.local.toml: [checks] is not valid in this file: its place is .lem/settings.toml; move the table there" <<<"$err" \
  && [ "$(status_of project --repo "$OLD" set local reviewer claude/opus:high)" = 1 ]; then
  pass "the machine's own file may not hold the checks or any other rule of the project"
else
  fail "the checks in the local file: $err"
fi
# The correction queue's switch is the machine's alone: a repository's two files refuse the table, and name machine.toml.
printf '%s\n' '[corrections]' 'collect = false' > "$OLD/.lem/settings.local.toml"
code=0
err=$(project --repo "$OLD" show 2>&1) || code=$?
kept=$(cat "$OLD/.lem/settings.local.toml")
rewrite=$(status_of project --repo "$OLD" set local reviewer claude/opus:high)
if [ "$code" = 1 ] && grep -qF "project.py: .lem/settings.local.toml: [corrections] is not valid in this file: its place is $XDG_CONFIG_HOME/lem/machine.toml; move the table there" <<<"$err" \
  && [ "$rewrite" = 1 ] && [ "$kept" = "$(printf '%s\n' '[corrections]' 'collect = false')" ]; then
  pass "the machine's own file for a repository refuses the correction queue's table and names machine.toml, and set local leaves the file as it was"
else
  fail "corrections in the local file: $code / $err / $rewrite / $kept"
fi
printf '%s\n' '[seats]' 'planner = 42' > "$OLD/.lem/settings.local.toml"
code=0
err=$(project --repo "$OLD" set local reviewer claude/opus:high 2>&1) || code=$?
if [ "$code" = 1 ] && [ "$(status_of project --repo "$OLD" set local reviewer default)" = 1 ] \
  && grep -q "project.py: .lem/settings.local.toml: seats.planner = 42 must be" <<<"$err" && ! grep -q Traceback <<<"$err" \
  && [ "$(cat "$OLD/.lem/settings.local.toml")" = "$(printf '%s\n' '[seats]' 'planner = 42')" ]; then
  pass "a wrong value already in the machine's own file is refused with its fix, and the file is left as it was"
else
  fail "a number as the local defender's seat: $err"
fi
rm "$OLD/.lem/settings.local.toml"
words=$(project --repo "$OLD" set local reviewer codex gpt-6.1-sol high 2>&1 || true)
gemini=$(project --repo "$OLD" set local reviewer gemini/pro 2>&1 || true)
if [ "$(status_of project --repo "$OLD" set local reviewer gemini)" = 1 ] && grep -qF "set local reviewer takes one VALUE, a whole seat \"agent/model:effort\", as \`set local reviewer codex/gpt-6.2-sol:high\`, or default; not 3 words" <<<"$words" \
  && grep -qF "the agent 'gemini' must be claude or codex" <<<"$gemini" && [ "$(status_of project --repo "$OLD" set local reviewer codex/)" = 1 ] && [ ! -e "$OLD/.lem/settings.local.toml" ]; then
  pass "set local reviewer refuses an agent that cannot review, a seat in three words and a seat that does not parse, and writes nothing then"
else
  fail "set local reviewer refusals: $words / $gemini"
fi
project --repo "$OLD" set local reviewer codex/gpt-6.2-sol:high >/dev/null && project --repo "$OLD" set local reviewer default >/dev/null
if [ ! -e "$OLD/.lem/settings.local.toml" ]; then pass "a local file with nothing left in it is removed"; else fail "empty local file stays"; fi
# One machine may name its own defender and experts too, read from the main checkout, and a write of the reviewer's seat keeps them.
settings '[branch]' 'base = "master"' '[seats]' 'planner = "claude/the-usual:high"'
printf '%s\n' '[seats]' 'planner = "claude/a-local-model:max"' 'experts = ["claude/opus:high", "codex/gpt-6.1-sol:high"]' > "$OLD/.lem/settings.local.toml"
local_seat=$(project --repo "$WORK/wt" show | field '(d["seats"]["planner"], [(e["seat"], e["from"]) for e in d["seats"]["experts"]], d["local"]["overrides"])' 2>&1 || true)
project --repo "$OLD" set local reviewer codex/gpt-6.2-sol:high >/dev/null 2>&1 || true
both=$(project --repo "$OLD" show | field '(d["seats"]["planner"]["model"], d["seats"]["reviewer"]["agent"], len(d["seats"]["experts"]), [d["seats"][which]["from"] for which in ("reviewer", "planner")])' 2>&1 || true)
project --repo "$OLD" set local reviewer default >/dev/null 2>&1 || true
kept=$(project --repo "$OLD" show | field '(d["seats"]["planner"]["model"], d["seats"]["reviewer"]["from"])' 2>&1 || true)
printf '%s\n' '[seats]' 'planner = "codex"' > "$OLD/.lem/settings.local.toml"
err=$(project --repo "$OLD" set local reviewer claude/opus:high 2>&1 || true)
if [ "$local_seat" = "({'agent': 'claude', 'model': 'a-local-model', 'effort': 'max', 'seat': 'claude/a-local-model:max', 'from': '.lem/settings.local.toml'}, [('claude/opus:high', '.lem/settings.local.toml'), ('codex/gpt-6.1-sol:high', '.lem/settings.local.toml')], [])" ] \
  && [ "$both" = "('a-local-model', 'codex', 2, ['.lem/settings.local.toml', '.lem/settings.local.toml'])" ] && [ "$kept" = "('a-local-model', \"Lem's default\")" ] \
  && grep -qF "project.py: .lem/settings.local.toml: seats.planner = 'codex': the agent 'codex' must be claude" <<<"$err" \
  && [ "$(cat "$OLD/.lem/settings.local.toml")" = "$(printf '%s\n' '[seats]' 'planner = "codex"')" ]; then
  pass "the machine's own file may name the defender's seat and the experts, which replace the project's whole and their from says so; set local reviewer keeps them through a write, and refuses a wrong one already there, leaving the file as it was"
else
  fail "the defender's seat in the local file: $local_seat / $both / $kept / $err"
fi
rm "$OLD/.lem/settings.local.toml"
# One person may say no to the naps, which spend their tokens; never yes to the naps there, no other key, and no
# table of [flow], which is the project's.
settings '[branch]' 'base = "master"' '[naps]' 'on = true'
printf '%s\n' '[naps]' 'on = false' > "$OLD/.lem/settings.local.toml"
machine=$(project --repo "$OLD" show 2>&1 | field '(d["naps"]["on"], d["local"]["overrides"])' 2>&1 || true)
in_tree=$(project --repo "$WORK/wt" show 2>&1 | field '(d["naps"]["on"], "naps.on" in d["local"]["overrides"])' 2>&1 || true)
asleep=$(project --repo "$OLD" may-nap 2>&1 | field '(d["may"], d["why"])' 2>&1 || true)
project --repo "$OLD" set local reviewer claude/opus:high >/dev/null 2>&1 && project --repo "$OLD" set local reviewer default >/dev/null 2>&1 || true
rewritten=$(cat "$OLD/.lem/settings.local.toml")
printf '%s\n' '[naps]' 'on = true' > "$OLD/.lem/settings.local.toml"
naps_yes=$(project --repo "$OLD" show 2>&1 || true)
naps_yes_code=$(status_of project --repo "$OLD" set local reviewer claude/opus:high)
printf '%s\n' '[naps]' 'when = "night"' > "$OLD/.lem/settings.local.toml"
naps_key=$(project --repo "$OLD" show 2>&1 || true)
printf '%s\n' '[flow]' 'topics = ["a price"]' > "$OLD/.lem/settings.local.toml"
flow_topics=$(project --repo "$OLD" show 2>&1 || true)
flow_key_code=$(status_of project --repo "$OLD" set local reviewer claude/opus:high)
rm "$OLD/.lem/settings.local.toml"
alone=$(project --repo "$OLD" show 2>&1 | field '(d["naps"]["on"], d["local"]["overrides"])' 2>&1 || true)
# shellcheck disable=SC2016  # the backticks are the refusal's own marks around a line
if [ "$machine" = "(False, ['naps.on'])" ] && [ "$in_tree" = "(False, True)" ] && [ "$asleep" = "(False, 'the naps are off on this machine (naps.on = false in .lem/settings.local.toml)')" ] \
  && [ "$rewritten" = "$(printf '%s\n' '[naps]' 'on = false')" ] \
  && grep -qF ".lem/settings.local.toml: naps.on = True is not for this file. It may say \`on = false\`" <<<"$naps_yes" \
  && grep -qF "only .lem/settings.toml, which everybody reads in git, switches the naps on" <<<"$naps_yes" && [ "$naps_yes_code" = 1 ] \
  && grep -qF ".lem/settings.local.toml: unknown key naps.when; valid: on" <<<"$naps_key" \
  && [ "$flow_key_code" = 1 ] && grep -qF ".lem/settings.local.toml: [flow] is not valid in this file: its place is .lem/settings.toml; move the table there" <<<"$flow_topics" \
  && [ "$alone" = "(True, [])" ]; then
  pass "the machine's own file may say no to the naps, also for a task's worktree, show and may-nap say that the no is the machine's, and a rewrite keeps it; a yes to the naps, another key of [naps] and a table of [flow] are refused with the reason"
else
  fail "the naps and [flow] in the local file: $machine / $in_tree / $asleep / $rewritten / $naps_yes / $naps_key / $flow_topics / $alone"
fi
# One machine may set how many days its state folder keeps old files, lower or higher than the project's, and it
# wins there and in a task's worktree; a rewrite keeps it, and a wrong number or another key is refused by that file.
settings '[branch]' 'base = "master"' '[state]' 'keep_days = 14'
project_days=$(project --repo "$OLD" show 2>&1 | field '(d["state"], d["local"]["overrides"])' 2>&1 || true)
printf '%s\n' '[state]' 'keep_days = 3' > "$OLD/.lem/settings.local.toml"
lower=$(project --repo "$OLD" show 2>&1 | field '(d["state"], d["local"]["overrides"])' 2>&1 || true)
lower_tree=$(project --repo "$WORK/wt" show 2>&1 | field 'd["state"]' 2>&1 || true)
project --repo "$OLD" set local reviewer claude/opus:high >/dev/null 2>&1 && project --repo "$OLD" set local reviewer default >/dev/null 2>&1 || true
days_kept=$(cat "$OLD/.lem/settings.local.toml")
printf '%s\n' '[state]' 'keep_days = 60' > "$OLD/.lem/settings.local.toml"
higher=$(project --repo "$OLD" show 2>&1 | field 'd["state"]' 2>&1 || true)
printf '%s\n' '[state]' 'keep_days = 0' > "$OLD/.lem/settings.local.toml"
days_zero_code=0
days_zero=$(project --repo "$OLD" show 2>&1) || days_zero_code=$?
days_zero_reviewer=$(status_of project --repo "$OLD" set local reviewer claude/opus:high)
printf '%s\n' '[state]' 'days = 7' > "$OLD/.lem/settings.local.toml"
days_key=$(project --repo "$OLD" show 2>&1 || true)
rm "$OLD/.lem/settings.local.toml"
if [ "$project_days" = "({'keep_days': 14, 'from': '.lem/settings.toml'}, [])" ] \
  && [ "$lower" = "({'keep_days': 3, 'from': '.lem/settings.local.toml'}, ['state.keep_days'])" ] \
  && [ "$lower_tree" = "{'keep_days': 3, 'from': '.lem/settings.local.toml'}" ] \
  && [ "$days_kept" = "$(printf '%s\n' '[state]' 'keep_days = 3')" ] \
  && [ "$higher" = "{'keep_days': 60, 'from': '.lem/settings.local.toml'}" ] \
  && [ "$days_zero_code" = 1 ] && [ "$days_zero_reviewer" = 1 ] && ! grep -q Traceback <<<"$days_zero" \
  && grep -qF "project.py: .lem/settings.local.toml: state.keep_days = 0 must be a whole number of days, 1 or more, as keep_days = 30; leave the line out for the number of .lem/settings.toml" <<<"$days_zero" \
  && grep -qF ".lem/settings.local.toml: unknown key state.days; did you mean 'keep_days'?" <<<"$days_key"; then
  pass "the machine's own file may set the days its state folder keeps, lower or higher than the project's, and show names the file in a task's worktree too; a rewrite keeps it, and a number below 1 or another key of [state] is refused by that file with exit 1"
else
  fail "keep_days in the local file: $project_days / $lower / $lower_tree / $days_kept / $higher / $days_zero_code $days_zero_reviewer $days_zero / $days_key"
fi
settings '[branch]' 'base = "master"'
# A checkout whose folder name holds a line break is still one path.
ODD="$WORK/odd
name"
git init -q -b main "$ODD"
commit "$ODD" start
project --repo "$ODD" init --base main >/dev/null
project --repo "$ODD" set local reviewer claude/opus:high >/dev/null
git -C "$ODD" worktree add -q "$WORK/odd-wt" -b feat/odd
if [ "$(project --repo "$WORK/odd-wt" show | field '(d["seats"]["reviewer"]["agent"], d["main"] == d["local"]["file"][:len(d["main"])], "\n" in d["main"])')" = "('claude', True, True)" ]; then
  pass "the main checkout is found whole when its path holds a line break, so a worktree reads its local settings"
else
  fail "a checkout path with a line break: $(project --repo "$WORK/odd-wt" show | field '(d["main"], d["local"])')"
fi

# The event log: every state block is an event, with the worktree's newest commit.
events() { "$PY" -c 'import json, sys; d = [json.loads(line) for line in open(sys.argv[1])]; print(eval(sys.argv[2], {"d": d}))' "$OLD/.lem/state/events.jsonl" "$1"; }
if [ "$(events '[(e["event"], e["task"], e["status"], e["text"], e["lines"]) for e in d[:2]]')" = "[('task.state', 'report-dates-stay-whole', 'queued', 'waits for a free place', []), ('task.state', 'report-dates-stay-whole', 'building', 'task 2 of 3', ['next: the report'])]" ] \
  && [ "$(events 'len(d)')" = 2 ] && [ "$(events 'd[1]["ask"], "limit" in d[1], "head" in d[1]')" = "('Keep report dates whole.', False, False)" ] \
  && [ ! -e "$OLD/.lem/state/events.js" ]; then
  pass "each state block is one event with the ask, a refused one is none, and the log is the one record"
else
  fail "events: $(cat "$OLD/.lem/state/events.jsonl")"
fi
tree=$(project --repo "$OLD" worktree-dir with-a-worktree)
git -C "$OLD" worktree add -q "$tree" -b fix/with-a-worktree
commit "$tree" "fix: 0123 is a string"
project --repo "$OLD" task-dir with-a-worktree >/dev/null
project --repo "$tree" state with-a-worktree building "task 1 of 1" >/dev/null
if [ "$(events '(d[-1]["branch"], d[-1]["subject"], d[-1]["head"])')" = "('fix/with-a-worktree', 'fix: 0123 is a string', '$(git -C "$tree" rev-parse --short HEAD)')" ]; then
  pass "a state written from the task's worktree carries that worktree's branch and newest commit"
else
  fail "worktree commit in the event: $(events 'd[-1]')"
fi
project --repo "$OLD" log with-a-worktree gate command="make test" exit:=1 tip=0000 "last=1 failed, 4 passed" >/dev/null
out=$(project --repo "$OLD" log with-a-worktree gate command="make test" exit:=0 tip=0123 "last=5 passed in 0.1s")
if [ "$(field '(d["event"], d["task"], d["exit"], d["tip"], d["last"])' <<<"$out")" = "('gate', 'with-a-worktree', 0, '0123', '5 passed in 0.1s')" ] \
  && [ "$(events '(d[-1]["event"], d[-1]["exit"])')" = "('gate', 0)" ]; then
  pass "log appends any other event, a number typed as JSON and a commit of digits kept a string"
else
  fail "log: $out"
fi
before=$(grep -c '' "$OLD/.lem/state/events.jsonl")
if [ "$(status_of project --repo "$OLD" log with-a-worktree task.state status=landed)" = 1 ] && [ "$(status_of project --repo "$OLD" log no-such-task gate exit:=0)" = 1 ] \
  && [ "$(status_of project --repo "$OLD" log with-a-worktree gate exit:=zero)" = 1 ] && [ "$(status_of project --repo "$OLD" log with-a-worktree gate task=other)" = 1 ] \
  && [ "$(status_of project --repo "$OLD" log with-a-worktree gate exit)" = 1 ] && [ "$(grep -c '' "$OLD/.lem/state/events.jsonl")" = "$before" ]; then
  pass "log refuses a state event, an unknown task, a value that is not JSON, a field the log sets and a bare word, and appends nothing then"
else
  fail "log refusals"
fi
# A plan talk's record goes through the real command: log refuses one whose counts do not agree with
# exit 1 and appends nothing, takes one with the bound its rules give, and `tasks` gives each task its
# newest talk, which Lem and a builder read before the build of a careful or large plan. The form of the
# record, each refusal's words among it, is a unit case (`talk_form`, tests/unit/test_task_rules.py).
talk() { project --repo "$OLD" log with-a-worktree plan.talk reviewer=codex turns:=6 questions:=3 settled:=2 open:=1 design:=1 unargued:=0 "$@" 2>&1; }
before=$(grep -c '' "$OLD/.lem/state/events.jsonl")
layered_code=0
layered=$(talk repaired:=2 root:=1 layer:=2 shared:=0) || layered_code=$?
none_yet=$(project --repo "$OLD" tasks | field '[t["talk"] for t in d if t["slug"] == "with-a-worktree"]' 2>&1 || true)
after_refusals=$(grep -c '' "$OLD/.lem/state/events.jsonl")
talk repaired:=1 root:=0 layer:=1 shared:=0 >/dev/null || true
written=$(talk repaired:=2 root:=1 layer:=1 shared:=2 || true)
told=$(project --repo "$OLD" tasks | field '[(t["slug"], t["talk"] and (t["talk"]["root"], t["talk"]["layer"], t["talk"]["shared"], bool(t["talk"]["ts"]))) for t in d if t["slug"] in ("with-a-worktree", "report-dates-stay-whole")]' 2>&1 || true)
if [ "$layered_code" = 1 ] && grep -qF "root and layer add up to at most repaired" <<<"$layered" && [ "$none_yet" = "[None]" ] && [ "$after_refusals" = "$before" ] \
  && [ "$(field '(d["root"], d["layer"], d["shared"], d["bound"])' <<<"$written")" = "(1, 1, 2, 14)" ] \
  && [ "$told" = "[('report-dates-stay-whole', None), ('with-a-worktree', (1, 1, 2, True))]" ]; then
  pass "log refuses a plan talk's record whose counts do not agree with exit 1 and writes nothing, and takes one with the bound its rules give; tasks gives each task its newest talk, or none"
else
  fail "the plan talk through log and tasks: $layered_code $layered / $none_yet / $before $after_refusals / $written / $told"
fi
project --repo "$OLD" state with-a-worktree dropped "the test is over" >/dev/null

settings '[branch]' 'base = "master"' '[flow]' 'topics = ["a price a customer pays", "data that cannot be rebuilt"]'
if [ "$(project --repo "$OLD" show | field '(d["flow"]["topics"], sorted(d["flow"]))')" = "(['a price a customer pays', 'data that cannot be rebuilt'], ['topics'])" ] \
  && ! grep -q '^careful' "$NEW/.lem/settings.toml" && grep -q '^topics = \[\]$' "$NEW/.lem/settings.toml"; then
  pass "a project names what must never go wrong as sentences in the owner's words, and init writes no list of paths beside them"
else
  fail "flow.topics: $(project --repo "$OLD" show 2>&1)"
fi
# The table that says what must never go wrong is the main checkout's: a task's branch that empties
# its topics reads them as the main checkout has them.
FLOW=$WORK/flow
git init -q -b main "$FLOW" && ident "$FLOW"
project --repo "$FLOW" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "owner"' '[flow]' 'topics = ["a customer is charged the wrong price"]' > "$FLOW/.lem/settings.toml"
git -C "$FLOW" add -A && git -C "$FLOW" commit -q -m "chore: start"
git -C "$FLOW" worktree add -q "$WORK/flow-tree" -b feat/lift main
printf '%s\n' '[branch]' 'base = "main"' '[flow]' 'topics = []' > "$WORK/flow-tree/.lem/settings.toml"
git -C "$WORK/flow-tree" commit -q -am "chore: no topics"
lifted=$(project --repo "$WORK/flow-tree" show | field '(d["flow"], d["root"] == d["main"])')
if [ "$lifted" = "({'topics': ['a customer is charged the wrong price']}, False)" ]; then
  pass "in a task's worktree the flow table is the main checkout's: a branch that empties its own topics changes nothing a lead or the landing reads"
else
  fail "the flow table of a worktree: $lifted"
fi
# While the main checkout is on the base branch, its working tree's settings count, an edit nobody committed yet too:
# the owner's own edit is his act. A colleague's branch checked out there (`gh pr checkout 57`) changes nothing a landing,
# a lead or a review reads: the settings are then read as the base branch's newest commit has them, and the line on
# stderr says so. The settings of an onboarding, on no commit of the base yet, are read from the working tree.
git -C "$FLOW" switch -q -c feat/colleague
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[flow]' 'topics = []' > "$FLOW/.lem/settings.toml"
git -C "$FLOW" commit -q -am "chore: the colleague's settings"
checked_out=$(project --repo "$FLOW" show 2>"$WORK/flow.err" | field '(d["branch"]["land"], d["flow"]["topics"], d["settings_from"][:5])')
checked_err=$(cat "$WORK/flow.err")
from_tree=$(project --repo "$WORK/flow-tree" show 2>/dev/null | field 'd["flow"]["topics"]')
git -C "$FLOW" switch -q main
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[flow]' 'topics = []' > "$FLOW/.lem/settings.toml"
edited=$(project --repo "$FLOW" show 2>"$WORK/flow.err" | field '(d["branch"]["land"], d["flow"]["topics"], d["settings_from"])')
from_tree_edited=$(project --repo "$WORK/flow-tree" show 2>/dev/null | field 'd["flow"]["topics"]')
edited_err=$(cat "$WORK/flow.err")
git -C "$FLOW" commit -q -am "chore: the owner's new settings"
committed=$(project --repo "$FLOW" show 2>"$WORK/flow.err" | field '(d["branch"]["land"], d["flow"]["topics"])')
committed_err=$(cat "$WORK/flow.err")
ONB=$WORK/onboarding
git init -q -b main "$ONB" && ident "$ONB" && commit "$ONB" "chore: start"
git -C "$ONB" switch -q -c chore/lem-setup && project --repo "$ONB" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' > "$ONB/.lem/settings.toml"
git -C "$ONB" add -A && git -C "$ONB" commit -q -m "chore: set up Lem"
onboarding=$(project --repo "$ONB" show 2>&1 | field '(d["branch"]["land"], d["settings_from"])')
if [ "$checked_out" = "('owner', ['a customer is charged the wrong price'], 'main@')" ] \
  && grep -qF "the main checkout is not on main, so Lem reads .lem/settings.toml as main has it" <<<"$checked_err" \
  && [ "$from_tree" = "['a customer is charged the wrong price']" ] \
  && [ "$edited" = "('agent', [], 'the working tree')" ] && [ -z "$edited_err" ] && [ "$from_tree_edited" = "[]" ] \
  && [ "$committed" = "('agent', [])" ] && [ -z "$committed_err" ] && [ "$onboarding" = "('agent', 'the working tree')" ]; then
  pass "while the main checkout is on the base branch its working tree's settings count, an uncommitted edit too; a colleague's branch checked out there changes nothing, the base branch's commit is read, and stderr says so; an onboarding's settings, on no commit of the base yet, are read from the working tree"
else
  fail "where the settings are read: $checked_out / $checked_err / $from_tree / $edited / $edited_err / $from_tree_edited / $committed / $committed_err / $onboarding"
fi
# By day each start is the owner's own request: no count of the tasks that build or land stops one.
settings '[branch]' 'base = "master"'
project --repo "$OLD" task-dir second-task >/dev/null
project --repo "$OLD" state second-task building "the plan" >/dev/null
project --repo "$OLD" task-dir third-task >/dev/null
project --repo "$OLD" state third-task landing "the gate runs" >/dev/null
out=$(project --repo "$OLD" may-start written-by-hand 2>&1 || true)
code=$(status_of project --repo "$OLD" may-start written-by-hand)
unknown=$(project --repo "$OLD" may-start no-such-task 2>&1 || true)
if [ "$code" = 0 ] && [ "$(field 'sorted(d["running"])' <<<"$out" 2>&1)" = "['report-dates-stay-whole', 'second-task', 'third-task']" ] && [ "$(field '"limit" in d' <<<"$out" 2>&1)" = False ] \
  && grep -qF "no task 'no-such-task'" <<<"$unknown" && [ "$(status_of project --repo "$OLD" may-start)" = 2 ]; then
  pass "may-start lets a task start whatever builds or lands, and names the tasks that do; an unknown task and no task are refused"
else
  fail "may-start with no limit: $code / $out / $unknown"
fi
project --repo "$OLD" state third-task dropped "the test is over" >/dev/null
project --repo "$OLD" state second-task ready "the report is written" >/dev/null
project --repo "$OLD" state second-task landing "the gate runs" >/dev/null
project --repo "$OLD" state second-task ready --start-over "the gate was cut off" >/dev/null
# An ended task stays ended: a stale wake-up writes no state over it and starts no lead for it, and a task in the
# landing or proposed gets no lead either. The same ended state again is taken; new work is a new ask.
ENDS=$WORK/ends
git init -q -b main "$ENDS" && project --repo "$ENDS" init --base main >/dev/null
ends() { project --repo "$ENDS" "$@"; }
ends task-dir ended-task >/dev/null && ends state ended-task landing "the gate runs" >/dev/null
in_landing=$(ends may-start ended-task 2>&1 || true)
ends state ended-task open "ready to land on main at abc1234" >/dev/null
in_open=$(ends may-start ended-task 2>&1 || true)
ends state ended-task landed "main abc1234" >/dev/null
landed_again=$(status_of ends state ended-task landed "main abc1234")
reopened=$(ends state ended-task building "the lead goes on" 2>&1 || true)
readied=$(status_of ends state ended-task ready "the report is written")
dropped_over=$(status_of ends state ended-task dropped "nobody wants it")
landed_start=$(ends may-start ended-task 2>&1 || true)
ends task-dir dropped-task >/dev/null && ends state dropped-task dropped "the owner dropped it" >/dev/null
dropped_again=$(status_of ends state dropped-task building "a late lead")
dropped_start=$(status_of ends may-start dropped-task)
if grep -qF "the task 'ended-task' is landing: its build is done, and it gets no lead" <<<"$in_landing" && grep -qF "lem land start ended-task" <<<"$in_open" \
  && grep -qF "the task 'ended-task' is open" <<<"$in_open" && [ "$landed_again" = 0 ] \
  && grep -qF "the task 'ended-task' is landed, and an ended task stays ended: new work for it is a new ask" <<<"$reopened" \
  && [ "$readied" = 1 ] && [ "$dropped_over" = 1 ] && grep -qF "the task 'ended-task' is landed: an ended task gets no lead" <<<"$landed_start" \
  && [ "$dropped_again" = 1 ] && [ "$dropped_start" = 1 ] && [ "$(status_in "$ENDS" ended-task)" = landed ] && [ "$(status_in "$ENDS" dropped-task)" = dropped ]; then
  pass "an ended task stays ended: no state moves it out of landed or dropped, and may-start gives no lead to it, nor to a task in the landing or proposed; the same ended state again is taken"
else
  fail "an ended task reopened: $in_landing / $in_open / $landed_again / $reopened / $readied / $dropped_over / $landed_start / $dropped_again / $dropped_start"
fi
# A task with its landing (`landing` or `open`) takes no state that only a lead or the start of a task writes: a lead
# that wakes late and writes `building` or `ready` would put the task back in the line and start its landing over.
LATE=$WORK/late
git init -q -b main "$LATE" && project --repo "$LATE" init --base main >/dev/null
late() { project --repo "$LATE" "$@"; }
late task-dir open-one >/dev/null && late state open-one landing "the checks start" >/dev/null && late state open-one open "ready to land on main at abc1234" >/dev/null
over_open=$(late state open-one building "lead: builder" 2>&1 || true)
ready_open=$(late state open-one ready "the report is written" 2>&1 || true)
let_through=""
for status in queued planned drafted; do [ "$(status_of late state open-one "$status" "a late lead")" = 1 ] || let_through="$let_through $status"; done
open_still=$(status_in "$LATE" open-one)
late state open-one landing "the base moved: the checks run again" >/dev/null
over_landing=$(late state open-one ready "the report is written" 2>&1 || true)
let_in_landing=""
for status in building queued planned drafted; do [ "$(status_of late state open-one "$status" "a late lead")" = 1 ] || let_in_landing="$let_in_landing $status"; done
landing_still=$(status_in "$LATE" open-one)
if grep -qF "the task 'open-one' is open: it is with its landing, and a reply or a message about open-one that comes now is a stale wake-up" <<<"$over_open" \
  && grep -qF "what the landing needs, land.py says itself" <<<"$over_open" && grep -qF "the task 'open-one' is open" <<<"$ready_open" \
  && grep -qF "the task 'open-one' is landing: it is with its landing" <<<"$over_landing" && [ -z "$let_through$let_in_landing" ] \
  && [ "$open_still" = open ] && [ "$landing_still" = landing ] && ! grep -q Traceback <<<"$over_open$ready_open$over_landing"; then
  pass "a task in the landing or proposed takes no state of a lead or of a task's start: a late lead's building, ready, queued, planned or drafted is a stale wake-up"
else
  fail "a late lead moved a task with its landing: $over_open / $ready_open / $over_landing /$let_through /$let_in_landing / $open_still / $landing_still"
fi
# The landing's own moves stay: blocked and landing again, ready again from blocked, open, landed and dropped, and a
# landing that has to start over gives its line back with `--start-over`, which only `ready` takes.
late state open-one blocked "the base is red" "after: fix-base" >/dev/null && late state open-one ready "the base is green again" >/dev/null
late state open-one landing "the checks start" >/dev/null
over_landing_again=$(status_of late state open-one ready --start-over "the landing was cut off")
late state open-one landing "the checks start" >/dev/null && late state open-one open "ready to land on main at abc1234" >/dev/null
over_open_again=$(status_of late state open-one ready --start-over "landing.json was moved aside")
other_status=$(late state open-one building --start-over "lead: builder" 2>&1 || true)
late state open-one landing "the checks start" >/dev/null && late state open-one open "ready to land on main at abc1234" >/dev/null
landed=$(status_of late state open-one landed "main abc1234")
late task-dir dropped-open >/dev/null && late state dropped-open landing "the checks start" >/dev/null && late state dropped-open open "pull request https://github.com/acme/shop/pull/7" >/dev/null
dropped=$(status_of late state dropped-open dropped "the owner closed the pull request")
# a small change whose gate found a lowered bar is a full change: its interview starts with `held` over `landing`
late task-dir small-one >/dev/null && late state small-one landing "the checks start" >/dev/null
held=$(status_of late state small-one held "the interview waits for the owner" "type: feat, because the gate found a lowered bar")
if [ "$over_landing_again" = 0 ] && [ "$over_open_again" = 0 ] && [ "$landed" = 0 ] && [ "$dropped" = 0 ] && [ "$held" = 0 ] \
  && grep -qF -- "--start-over gives a landing's line back, and only the state ready does that" <<<"$other_status" \
  && [ "$(status_in "$LATE" open-one)" = landed ] && [ "$(status_in "$LATE" dropped-open)" = dropped ] && [ "$(status_in "$LATE" small-one)" = held ]; then
  pass "the landing's own moves stay: blocked, landing again, open, landed, dropped, held for a small change that is a full change, and ready with --start-over gives the line back"
else
  fail "a landing's own move refused: $over_landing_again / $over_open_again / $other_status / $landed / $dropped / $held"
fi

# The type of a request, and a task that ends with a report and nothing to merge: `answered`.
ANS=$WORK/answered
git init -q -b main "$ANS"
project --repo "$ANS" init --base main >/dev/null
ans_dir=$(project --repo "$ANS" task-dir zero-after-refund --ask "invoices show 0 after a refund")
# The type line through the real command: state refuses one in another form with exit 1 and writes no block,
# and tasks gives the newest type. Its form, each refusal's words among it, is a unit case (`type_line`,
# tests/unit/test_task_rules.py).
before=$(grep -c '' "$ANS/.lem/state/events.jsonl" 2>/dev/null || echo 0)
unsaid_code=0
unsaid=$(project --repo "$ANS" state zero-after-refund building "an investigator reproduces the bug and finds its cause" "investigation: bug" "type: fix" 2>&1) || unsaid_code=$?
after_refusals=$(grep -c '' "$ANS/.lem/state/events.jsonl" 2>/dev/null || echo 0)
unwritten=$([ -f "$ans_dir/state.md" ] && echo written || echo none)
first_said=$(project --repo "$ANS" state zero-after-refund building "an investigator reproduces the bug and finds its cause" "investigation: bug" "type: fix, because the ask says the total is wrong today")
second_said=$(project --repo "$ANS" state zero-after-refund building "the test that reproduces the bug is committed" "investigation: bug")
kind=$(project --repo "$ANS" tasks | field 'next(t["type"] for t in d if t["slug"] == "zero-after-refund")' 2>&1 || true)
if [ "$unsaid_code" = 1 ] && grep -qF "names the type without its reason" <<<"$unsaid" && [ "$after_refusals" = "$before" ] && [ "$unwritten" = none ] \
  && [ "$kind" = "{'type': 'fix', 'why': 'the ask says the total is wrong today'}" ]; then
  pass "state refuses a type line without its reason with exit 1 and writes no block, takes one with it, and tasks gives the newest type also when a later block says nothing of it"
else
  fail "the type of a request: $unsaid_code $unsaid / $before $after_refusals / $unwritten / $kind"
fi
# The task's first line: `state` composes it for the block that names the task's path, from the task's files, and logs it
# with the block; a later block, and a task of the night, get none.
FL=$WORK/first-line
git init -q -b main "$FL"
project --repo "$FL" init --base main >/dev/null
project --repo "$FL" task-dir footer-terms-typo --ask 'The footer says "Terms and condtions"' >/dev/null
printf '%s\n' '## Acceptance criteria' '' 'Size: small, because one word.' '' '1. The footer says "Terms and conditions".' > "$FL/.lem/state/tasks/footer-terms-typo/criteria.md"
printf '%s\n' "Read \`skills/lem/prompts/small.md\` in the folder that \`lem version\` prints as \`root\`, and follow it; when \`lem version\` fails, stop and say that \`lem\` is not on the PATH, with \`lem doctor\` as the check." 'task: footer-terms-typo' 'branch: fix/footer-terms-typo' > "$FL/.lem/state/tasks/footer-terms-typo/brief.md"
fast_said=$(project --repo "$FL" state footer-terms-typo building "small change: one builder" "type: fix, because the footer shows a typo today" | field 'd.get("say")' 2>&1 || true)
fast_logged=$(tail -n 1 "$FL/.lem/state/events.jsonl" | field 'd.get("say")' 2>&1 || true)
project --repo "$FL" task-dir night-note --ask docs/backlog/night-note.md --night 2026-11-21 >/dev/null
night_said=$(project --repo "$FL" state night-note building "small change: one builder" "type: docs, because a line of a document" | field 'd.get("say")' 2>&1 || true)
if [ "$fast_said" = 'fix: "the footer says '"'"'Terms and conditions'"'"'". Branch fix/footer-terms-typo. Fast track: one builder, the checks, one read, then the pull request. Nothing waits for you. Wrong read? /lem standard-track, /lem be-careful.' ] \
  && [ "$fast_logged" = "$fast_said" ] && [ "$(field 'd.get("say")' <<<"$second_said")" = None ] && [ "$night_said" = None ] \
  && [ "$(field 'd["say"]' <<<"$first_said")" = 'fix: "invoices show 0 after a refund". An investigator finds the cause first. Then I tell you what it found: the fast track, the standard track, or no bug.' ]; then
  pass "state prints the task's first line as say for the block that names its path, with its criterion and its branch from the task's files, and logs it with the block; a later block and a task of the night get none"
else
  fail "the task's first line: $first_said / $second_said / $fast_said / $fast_logged / $night_said"
fi
# The three lines the first line reads have one form each, and `state` refuses a line that starts as one of them in
# another, with exit 1 and no block; a line that starts as none of them is free, and the wait stays in the first line.
project --repo "$FL" task-dir export-notes-in-order --ask 'After gift-note-in-export: the export keeps the notes in their order' >/dev/null
ordered() { project --repo "$FL" state export-notes-in-order queued "$1" "after: gift-note-in-export" "type: feat, because a new order" "$2" 2>&1; }
order_form=$(ordered "the owner's order: After gift-note-in-export" "then: the interview" || true)
order_code=$(status_of ordered "the owner's order: After gift-note-in-export" "then: the interview")
then_form=$(ordered "the owner's order: \"After gift-note-in-export\"" "then: an interview" || true)
then_code=$(status_of ordered "the owner's order: \"After gift-note-in-export\"" "then: an interview")
fits_form=$(project --repo "$FL" state export-notes-in-order queued "the owner's order: \"After gift-note-in-export\"" "after: gift-note-in-export" \
  "the one open task that fit his words" "type: feat, because a new order" "then: the interview" 2>&1 || true)
unwritten=$([ -f "$FL/.lem/state/tasks/export-notes-in-order/state.md" ] && echo written || echo none)
free_said=$(ordered 'the owners order: "After gift-note-in-export"' "then: the interview" | field 'd.get("say")' 2>&1 || true)
project --repo "$FL" task-dir quoted-order --ask 'After the "gift note" task: the notes keep their order' >/dev/null
quoted=$(status_of project --repo "$FL" state quoted-order queued "the owner's order: \"After the \"gift note\" task\"" "after: gift-note-in-export" "type: feat, because a new order" "then: the interview")
if grep -qF "\`the owner's order: \"HIS WORDS\"\`" <<<"$order_form" && [ "$order_code" = 1 ] \
  && grep -qF "\`then: the interview\`, \`then: the fast track\` or \`then: the lead\`" <<<"$then_form" && [ "$then_code" = 1 ] \
  && grep -qF "\`the one open task that fits his words\`" <<<"$fits_form" && [ "$unwritten" = none ] && [ "$quoted" = 0 ] \
  && grep -qF "It waits for gift-note-in-export, and starts when that task lands or is answered. Then the standard track: an interview here, then" <<<"$free_said"; then
  pass "state refuses the owner's order, a then: line and the line of the one open task that fits in another form, with exit 1, the form and no block; his own double quote is in the form, and a free order line still leaves the wait in the first line"
else
  fail "the three lines' form: $order_form ($order_code) / $then_form ($then_code) / $fits_form / $unwritten / $quoted / $free_said"
fi
# A task held because his order named no task Lem could tell gets no first line at the hold, and gets it with his answer.
project --repo "$FL" task-dir notes-held --ask '/lem After the gift note: the export keeps the notes in their order' >/dev/null
printf '%s\n' "Read \`skills/lem/prompts/lead.md\` in the folder that \`lem version\` prints as \`root\`, and follow it; when \`lem version\` fails, stop and say that \`lem\` is not on the PATH, with \`lem doctor\` as the check." 'task: notes-held' 'branch: feat/notes-held' > "$FL/.lem/state/tasks/notes-held/brief.md"
printf '%s\n' '# Notes in order' '' '## Outcome' '' 'The export keeps the notes in their order.' > "$FL/.lem/state/tasks/notes-held/task.md"
hold_said=$(project --repo "$FL" state notes-held held 'the order waits for the owner: "After the gift note"' "type: feat, because a new order" | field 'd.get("say")' 2>&1 || true)
answer_said=$(project --repo "$FL" state notes-held queued "the owner's order: \"After the gift note\"" "after: gift-note-in-export" "then: the interview" | field 'd.get("say")' 2>&1 || true)
answer_named=$(tail -n 1 "$FL/.lem/state/events.jsonl" | field 'd.get("say_named")' 2>&1 || true)
again_said=$(project --repo "$FL" state notes-held held "the interview waits for the owner" | field 'd.get("say")' 2>&1 || true)
if [ "$hold_said" = None ] && [ "$again_said" = None ] \
  && [ "$answer_said" = 'feat: "the export keeps the notes in their order". Branch feat/notes-held. It waits for gift-note-in-export, as you said; "start notes-held now" starts it before that. Then the standard track: an interview here, then acceptance criteria for your yes. After that it runs to the pull request without you. Wrong read? /lem be-careful.' ] \
  && grep -qF 'notes-held · feat: "the export keeps the notes in their order". Branch feat/notes-held. It waits for gift-note-in-export, as you said; "start notes-held now"' <<<"$answer_named"; then
  pass "a task held for an order that names no task gets no first line at the hold, its queued block after his answer prints it with the hold's type, and the block its wait ends in prints none"
else
  fail "the first line after the hold: $hold_said / $answer_said / $answer_named / $again_said"
fi
# The investigation's record through the real command: log refuses one in another form with exit 1 and appends
# nothing, takes one in its form, and tasks gives the newest. The form, each refusal's words among it, is a unit
# case (`investigation_form`, tests/unit/test_task_rules.py).
inv() { project --repo "$ANS" log zero-after-refund investigation "$@" 2>&1; }
before=$(grep -c '' "$ANS/.lem/state/events.jsonl")
nowhere_code=0
nowhere=$(inv type=fix call=small "line=the total skips credit notes" reproduced:=true) || nowhere_code=$?
after_refusals=$(grep -c '' "$ANS/.lem/state/events.jsonl")
none_yet=$(project --repo "$ANS" tasks | field 'next(t["investigation"] for t in d if t["slug"] == "zero-after-refund")' 2>&1 || true)
inv type=fix call=full "line=the invoice total adds the refund as a payment" where=billing/invoice.py:total reproduced:=true >/dev/null || true
found=$(project --repo "$ANS" tasks | field 'next((t["investigation"]["call"], t["investigation"]["where"], t["investigation"]["reproduced"]) for t in d if t["slug"] == "zero-after-refund")' 2>&1 || true)
if [ "$nowhere_code" = 1 ] && grep -qF "where names the cause" <<<"$nowhere" && [ "$after_refusals" = "$before" ] \
  && [ "$none_yet" = "None" ] && [ "$found" = "('full', 'billing/invoice.py:total', True)" ]; then
  pass "log refuses an investigation's record in another form with exit 1 and writes nothing, and takes one in its form; tasks gives the newest"
else
  fail "the investigation's record through log and tasks: $nowhere_code $nowhere / $before $after_refusals / $none_yet / $found"
fi
# A stage's start through the real command: log takes one in its form, so that the board draws its span from it to
# the event that ends it, and refuses one in another form with exit 1 and appends nothing. The form of each start,
# each refusal's words among it, is a unit case (`start_form`, tests/unit/test_task_rules.py).
starts() { project --repo "$ANS" log zero-after-refund "$@" 2>&1; }
before=$(grep -c '' "$ANS/.lem/state/events.jsonl")
started=$(starts builder.start "job=task 2 of 3" || true)
odd_job_code=0
odd_job=$(starts builder.start "job=the polish pass") || odd_job_code=$?
if [ "$(field '(d["event"], d["job"])' <<<"$started")" = "('builder.start', 'task 2 of 3')" ] && [ "$odd_job_code" = 1 ] \
  && grep -qF "the polish pass logs its own start" <<<"$odd_job" && [ "$(grep -c '' "$ANS/.lem/state/events.jsonl")" = $((before + 1)) ]; then
  pass "log takes a builder's start in its form, and refuses a job no builder has with exit 1 and writes nothing"
else
  fail "a start through log: $started / $odd_job_code $odd_job"
fi
# a breaker that stopped the investigation while the task built, which nobody helped on before the task ended
breaker_doc "$ans_dir" && "$PY" -B "$PWD/skills/lem/scripts/decisions.py" --repo "$ANS" breaker zero-after-refund --cause irreversible --irreversible data >/dev/null
# `answered` needs the report and a record whose call ends the task; it takes no place and keeps its slug.
no_report=$(project --repo "$ANS" state zero-after-refund answered "not a bug: a refund is a credit note" 2>&1 || true)
printf '%s\n' '# Investigation' '' 'Reproduced: yes.' > "$ans_dir/investigation.md"
goes_on=$(project --repo "$ANS" state zero-after-refund answered "not a bug: a refund is a credit note" 2>&1 || true)
inv type=fix call=not-a-bug "line=a refund is a credit note, and the invoice shows what is left to pay" where=billing/invoice.py:total reproduced:=true >/dev/null || true
project --repo "$ANS" state zero-after-refund answered "not a bug: the invoice shows what is left to pay" "report: investigation.md" >/dev/null 2>&1 || true
answered=$(project --repo "$ANS" tasks | field 'next((t["status"], t["investigation"]["call"]) for t in d if t["slug"] == "zero-after-refund")' 2>&1 || true)
project --repo "$ANS" task-dir other-task >/dev/null
project --repo "$ANS" state other-task building "lead: builder" "type: feat, because the ask wants a new column" >/dev/null
project --repo "$ANS" task-dir waits-for-a-place >/dev/null
places=$(project --repo "$ANS" may-start waits-for-a-place 2>&1 | field 'd["running"]' 2>&1 || true)
# the task starts its next lead: the investigator's call was a small change
itself=$(project --repo "$ANS" may-start other-task 2>&1 | field 'd["running"]' 2>&1 || true)
project --repo "$ANS" state other-task answered "the question is answered" >/dev/null 2>&1 || true
unreported=$(project --repo "$ANS" tasks | field 'next(t["status"] for t in d if t["slug"] == "other-task")')
project --repo "$ANS" state other-task dropped "the test is over" >/dev/null
free=$(project --repo "$ANS" may-start waits-for-a-place 2>&1 | field 'd["running"]' 2>&1 || true)
taken=$(project --repo "$ANS" task-dir zero-after-refund --ask "again" 2>&1 || true)
if grep -qF "investigation.md" <<<"$no_report" && grep -qF "not-a-bug or answer" <<<"$goes_on" && [ "$answered" = "('answered', 'not-a-bug')" ] \
  && [ "$places" = "['other-task']" ] && [ "$itself" = "[]" ] && [ "$unreported" = "building" ] && [ "$free" = "[]" ] \
  && grep -qF "the task 'zero-after-refund' is answered; a new task takes a slug of its own" <<<"$taken"; then
  pass "a task is answered only with its investigation's report and a record whose call ends it; an answered task takes no place, and its slug stays its own"
else
  fail "the state answered: $no_report / $goes_on / $answered / $places / $unreported / $free / $taken"
fi
# A breaker of an answered task waits for nobody, and the task takes no new decision.
ended=$("$PY" -B "$PWD/skills/lem/scripts/decisions.py" --repo "$ANS" pending | field '(d["waiting"], [(e["task"], e["status"], e["breakers"]) for e in d["ended"]])' 2>&1 || true)
again=$("$PY" -B "$PWD/skills/lem/scripts/decisions.py" --repo "$ANS" log zero-after-refund --by lead --what "Keep the test" --chose "keep it" --why "it pins the behavior" 2>&1 || true)
if [ "$ended" = "([], [('zero-after-refund', 'answered', [1])])" ] && grep -qF "zero-after-refund is answered" <<<"$again" \
  && [ "$(grep -c '' "$ANS/.lem/state/tasks/zero-after-refund/decisions.jsonl")" = 1 ]; then
  pass "an answered task has no breaker that waits: pending puts it with the tasks that ended, and a new decision of it is refused"
else
  fail "the breaker of an answered task: $ended / $again"
fi

# A task that was reviewed and proposed and is not green: it waits for the owner's merge, and it does not go back a phase.
project --repo "$OLD" task-dir owner-lands-it >/dev/null
for block in 'building|plan committed, 3 tasks' 'building|task 3 of 3' 'ready|the report is written' 'landing|the checks start'; do
  project --repo "$OLD" state owner-lands-it "${block%%|*}" "${block#*|}" >/dev/null
done
project --repo "$OLD" log owner-lands-it review round:=1 kind=read verdict=clean must_fix:=0 should:=1 nit:=0 'answered:=["codex"]' 'silent:=[]' 'ran:=[]' 'left_out:=[]' tip=abc1234 >/dev/null
project --repo "$OLD" log owner-lands-it proposed green:=false 'not_green:=["criterion 1 changed during the build: y is taken."]' tip=abc1234 >/dev/null
project --repo "$OLD" state owner-lands-it open "ready to land on master at abc1234" "not green: criterion 1 changed during the build: y is taken." >/dev/null

# The rule picker: one match of a change against the scopes of the style guide files, for every reader of the rules.
# Each glob form, a brace group and what it matches or not is a unit case (`braces`, `glob_regex`,
# tests/unit/test_rule_picker.py); here each rule file covers one file or more of one call.
RUL=$WORK/rules-repo
git init -q -b main "$RUL"
git -C "$RUL" config user.name t && git -C "$RUL" config user.email t@t
mkdir -p "$RUL/.claude/rules/backend" "$WORK/shared-rules"
printf '%s\n' '# Conduct' 'Never dig up a deleted document.' > "$RUL/.claude/rules/00-conduct.md"
printf '%s\n' '---' 'description: no scope in this one' '---' 'Say what you did not verify.' > "$RUL/.claude/rules/01-reports.md"
printf '%s\n' '---' 'paths:' '  - "**/*.ts"' '---' > "$RUL/.claude/rules/10-any-ts.md"
printf '%s\n' '---' 'paths:' '  - "src/**/*"' '---' > "$RUL/.claude/rules/11-under-src.md"
printf '%s\n' '---' 'paths:' '  - "*.md"' '---' > "$RUL/.claude/rules/12-root-md.md"
printf '%s\n' '---' 'paths:' "  - 'src/components/*.tsx'" '---' > "$RUL/.claude/rules/13-one-folder.md"
printf '%s\n' '---' 'paths:' '  # the three lines of the documentation' '  - "src/**/*.{ts,tsx}"' '  - "lib/**/*.ts"' '  - "tests/**/*.test.ts"' 'description: after the list' '---' > "$RUL/.claude/rules/14-braces.md"
printf '%s\n' '---' 'paths: ["**/models.py", "**/models/**", ".revmux/**", "docs/{a,b}/*.md"]' '---' > "$RUL/.claude/rules/backend/20-models.md"
printf '%s\n' '---' 'paths: scripts/verify.sh' '---' > "$RUL/.claude/rules/backend/21-one-file.md"
printf '%s\n' '---' 'paths: # what follows is the scope' '  - "**/*.sql" # every query' "  - '**/*#*.psql'" '---' > "$WORK/shared-rules/30-sql.md"
{ printf '\357\273\277'; printf '%s\n' '---' 'paths: ["**/*.proto"]  # with a byte order mark before the first line' '---'; } > "$RUL/.claude/rules/15-bom.md"
ln -s "$WORK/shared-rules" "$RUL/.claude/rules/shared" && ln -s .. "$RUL/.claude/rules/backend/loop"
echo 'not a rule' > "$RUL/.claude/rules/notes.txt"
project --repo "$RUL" init --base main >/dev/null
git -C "$RUL" add -A && git -C "$RUL" commit -q -m "chore: start"
picked() { project --repo "$RUL" rules "$@" | field '" ".join(r["file"].rsplit("/", 1)[1][:2] for r in d["rules"])'; }
out=$(project --repo "$RUL" rules src/components/a.tsx "$RUL/app/models.py" docs/a/x.md lib/a.ts tests/unit/a.test.ts scripts/verify.sh db/001.sql 'db/a#b.psql' api/v1.proto README.md)
if [ "$(field '[(r["file"].rsplit("/", 1)[1], r["scope"], r.get("covers")) for r in d["rules"] if r["scope"] != "every path"]' <<<"$out")" \
  = "[('10-any-ts.md', ['**/*.ts'], ['lib/a.ts', 'tests/unit/a.test.ts']), ('11-under-src.md', ['src/**/*'], ['src/components/a.tsx']), ('12-root-md.md', ['*.md'], ['README.md']), ('13-one-folder.md', ['src/components/*.tsx'], ['src/components/a.tsx']), ('14-braces.md', ['lib/**/*.ts', 'src/**/*.{ts,tsx}', 'tests/**/*.test.ts'], ['lib/a.ts', 'src/components/a.tsx', 'tests/unit/a.test.ts']), ('15-bom.md', ['**/*.proto'], ['api/v1.proto']), ('20-models.md', ['**/models.py', 'docs/{a,b}/*.md'], ['app/models.py', 'docs/a/x.md']), ('21-one-file.md', ['scripts/verify.sh'], ['scripts/verify.sh']), ('30-sql.md', ['**/*#*.psql', '**/*.sql'], ['db/001.sql', 'db/a#b.psql'])]" ] \
  && [ "$(field '[r["file"].rsplit("/", 1)[1] for r in d["rules"] if r["scope"] == "every path"]' <<<"$out")" = "['00-conduct.md', '01-reports.md']" ] \
  && [ "$(field '(d["files"][:3], d["exists"], d["folder"], d["rules"][0]["file"], len(d["rules"]))' <<<"$out")" = "(['README.md', 'api/v1.proto', 'app/models.py'], True, '$RUL/.claude/rules', '$RUL/.claude/rules/00-conduct.md', 11)" ]; then
  pass "the picker reads the scope of each rule file, in a subfolder and through a link, with a comment, a flow list, a scalar or a byte order mark in its frontmatter, says which glob matched and which files each covers, gives a file with no scope every path, and does not turn in a loop of links"
else
  fail "the picker's output: $out"
fi
mkdir -p "$RUL/db" && echo 'select 1;' > "$RUL/db/001.sql" && echo x > "$RUL/notes.md" && git -C "$RUL" add -A && git -C "$RUL" commit -q -m "feat: a query"
if [ "$(project --repo "$RUL" rules --range HEAD~1..HEAD | field '(d["files"], [r["file"].rsplit("/", 1)[1] for r in d["rules"] if r["scope"] != "every path"])')" = "(['db/001.sql', 'notes.md'], ['12-root-md.md', '30-sql.md'])" ] \
  && [ "$(status_of project --repo "$RUL" rules --range no-such-ref..HEAD)" = 1 ]; then
  pass "the picker takes the files of a range of commits, and a range git does not know is refused"
else
  fail "the picker with a range: $(project --repo "$RUL" rules --range HEAD~1..HEAD)"
fi
# A file that moved counts on both sides, and one file has one answer however it is named.
mkdir -p "$RUL/src" "$RUL/lib" && echo 'export const a = 1' > "$RUL/src/x.ts" && git -C "$RUL" add -A && git -C "$RUL" commit -q -m "feat: a module"
git -C "$RUL" mv src/x.ts lib/x.ts && git -C "$RUL" commit -q -m "refactor: the module moves"
ln -s src "$RUL/alias" && mkdir -p "$RUL/src/sub" && ln -s src/sub "$RUL/deep"
if [ "$(project --repo "$RUL" rules --range HEAD~1..HEAD | field '(d["files"], [r["file"].rsplit("/", 1)[1][:2] for r in d["rules"]])')" = "(['lib/x.ts', 'src/x.ts'], ['00', '01', '10', '11', '14'])" ] \
  && [ "$(picked alias/y.ts)" = "$(picked "$RUL/src/y.ts")" ] && [ "$(picked alias/y.ts)" = "00 01 10 11 14" ] && [ "$(project --repo "$RUL" rules alias/y.ts | field 'd["files"]')" = "['src/y.ts']" ] \
  && [ "$(project --repo "$RUL" rules deep/../y.ts "$RUL/deep/../y.ts" lib/../src/y.ts | field 'd["files"]')" = "['src/y.ts']" ] \
  && [ "$(status_of project --repo "$RUL" rules ../elsewhere.py)" = 1 ] && [ "$(status_of project --repo "$RUL" rules src/..)" = 1 ] \
  && [ "$(status_of project --repo "$RUL" rules .)" = 1 ] && [ "$(status_of project --repo "$RUL" rules "$RUL")" = 1 ] && [ "$(status_of project --repo "$RUL" rules src/sub/../..)" = 1 ]; then
  pass "a renamed file brings the rules of its old place and of its new one, a path through a linked folder or with two dots is the same file, and one that leaves the repository is refused"
else
  fail "the picker with a rename and other path forms: $(project --repo "$RUL" rules --range HEAD~1..HEAD) / $(picked alias/y.ts)"
fi
rm "$RUL/alias" "$RUL/deep"
err=$(project --repo "$RUL" rules 2>&1 || true)
outside=$(project --repo "$RUL" rules "$WORK/elsewhere.py" 2>&1 || true)
printf '%s\n' '---' 'paths:' '---' 'A scope with nothing in it.' > "$RUL/.claude/rules/40-empty.md"
empty=$(project --repo "$RUL" rules x.ts 2>&1 || true)
printf '%s\n' '---' 'paths:' '  glob: "src/**"' '---' > "$RUL/.claude/rules/40-empty.md"
shape=$(project --repo "$RUL" rules x.ts 2>&1 || true)
printf '%s\n' '---' 'paths: ["src/[z-a].ts"]' '---' > "$RUL/.claude/rules/40-empty.md"
glob=$(project --repo "$RUL" rules x.ts 2>&1 || true)
code="$(status_of project --repo "$RUL" rules) $(status_of project --repo "$RUL" rules "$WORK/elsewhere.py") $(status_of project --repo "$RUL" rules x.ts)"
rm "$RUL/.claude/rules/40-empty.md"
if [ "$code" = "1 1 1" ] && grep -q "name them, or pass --range BASE..TIP" <<<"$err" && grep -q "is not inside $RUL" <<<"$outside" \
  && grep -q ".claude/rules/40-empty.md: its .paths:. names no glob" <<<"$empty" && grep -q "or take the line out so the file covers every path" <<<"$empty" \
  && grep -q "a line under .paths:. is not a list item" <<<"$shape" \
  && grep -q ".claude/rules/40-empty.md: a glob of its .paths:. does not read as a pattern" <<<"$glob" && ! grep -q Traceback <<<"$glob"; then
  pass "the picker refuses a call with no file, a file of another folder, and a rule whose paths name no glob, are no list or hold a pattern that does not read, each with the fix"
else
  fail "the picker's refusals: $code / $err / $outside / $empty / $shape / $glob"
fi
# A project with no rules yet gets an empty answer, not an error.
FRESH=$WORK/rules-fresh
git init -q -b main "$FRESH" && commit "$FRESH" start
project --repo "$FRESH" init --base main >/dev/null
none=$(project --repo "$FRESH" rules app/x.py | field '(d["exists"], d["rules"])')
if [ "$none" = "(False, [])" ]; then
  pass "a project with no rules gets no rule and no error"
else
  fail "the rules of a project with none: $none"
fi
if [ "$(status_of project --repo "$RUL" migrate plan)" != 0 ] && [ -d "$RUL/.claude/rules" ] \
  && [ "$(project --repo "$RUL" show | field 'd["places"]["rules"]["path"]')" = "$RUL/.claude/rules" ]; then
  pass "the rules of an adopted project stay where the agent loads them: the settings name that folder, and no command moves it"
else
  fail "an adopted project's rules"
fi

# The criteria of a task: read from the top of its plan, and each one held by a test that fails on the base commit.
criteria() { "$PY" -B "$CRITERIA" --repo "$ST" "$@"; }
ST=$WORK/criteria-repo
git init -q -b main "$ST" && git -C "$ST" config user.name t && git -C "$ST" config user.email t@t
mkdir -p "$ST/tests" "$ST/docs/plans" && echo 'echo "1042,None"' > "$ST/export.sh" && git -C "$ST" add -A && git -C "$ST" commit -q -m start
project --repo "$ST" init --base main >/dev/null && git -C "$ST" add -A && git -C "$ST" commit -q -m "chore: the settings"
project --repo "$ST" task-dir export-has-the-gift-note >/dev/null
stw=$(project --repo "$ST" worktree-dir export-has-the-gift-note)
git -C "$ST" worktree add -q -b feat/export-has-the-gift-note "$stw" main
project --repo "$ST" state export-has-the-gift-note building 'lead: builder' >/dev/null
mkdir -p "$stw/docs/plans" "$stw/tests"
plan=$stw/docs/plans/2026-11-15-export-has-the-gift-note.md
# shellcheck disable=SC2016  # the backticks are the plan's own marks around a command and a file
printf '%s\n' '# The export has the gift note' '' '## Acceptance criteria' '' 'Size: full, because the export gets a new column and an empty cell.' '' \
  '1. A CSV export holds the gift note of an order: order 1042 with the note "for Ania"' '   has that text in its row.' \
  '   - test: `sh tests/gift.sh` in `tests/gift.sh`' '2. An order with no gift note has an empty cell, not the word "None".' \
  '   - test: `sh tests/none.sh` in `tests/none.sh`, `tests/helper.sh`' '' '## Tasks' '' '1. The column.' > "$plan"
printf '%s\n' 'echo "1042,for Ania"' 'echo "1043,"' > "$stw/export.sh"
echo 'sh export.sh | grep -q "1042,for Ania"' > "$stw/tests/gift.sh" && echo '. tests/helper.sh; ! sh export.sh | grep -q None' > "$stw/tests/none.sh" && echo ': a helper' > "$stw/tests/helper.sh"
git -C "$stw" add -A && git -C "$stw" commit -q -m "feat: the gift note"
shown=$(criteria show export-has-the-gift-note)
criteria record export-has-the-gift-note >/dev/null
if [ "$(field '(d["size"], d["why"], [(s["n"], s["text"].split(" of an order")[0].split(",")[0], [t["command"] for t in s["tests"]], [t["files"] for t in s["tests"]]) for s in d["criteria"]])' <<<"$shown")" \
  = "('full', 'the export gets a new column and an empty cell.', [(1, 'A CSV export holds the gift note', ['sh tests/gift.sh'], [['tests/gift.sh']]), (2, 'An order with no gift note has an empty cell', ['sh tests/none.sh'], [['tests/none.sh', 'tests/helper.sh']])])" ] \
  && [ "$(field 'd["criteria"][0]["text"].endswith("has that text in its row.")' <<<"$shown")" = True ] \
  && [ "$(grep -c '"event": "task.criteria"' "$ST/.lem/state/events.jsonl")" = 1 ] && grep -q '"event": "task.criteria".*"size": "full"' "$ST/.lem/state/events.jsonl"; then
  pass "the criteria are read from the top of the task's plan, each with its text over two lines and its tests, and record puts them into the event log for the board"
else
  fail "criteria show and record: $shown"
fi
before=$(git -C "$stw" rev-parse HEAD)
echo 'kept: mine' > "$stw/local.conf" && echo 'local.conf' >> "$ST/.git/info/exclude"
out=$(criteria red export-has-the-gift-note)
if [ "$(field '(d["ok"], [(t["criterion"], t["on_branch"], t["on_base"] != 0, t["problem"]) for t in d["tests"]], d["without_a_test"])' <<<"$out")" = "(True, [(1, 0, True, None), (2, 0, True, None)], [])" ] \
  && [ "$(git -C "$stw" branch --show-current)" = "feat/export-has-the-gift-note" ] && [ "$(git -C "$stw" rev-parse HEAD)" = "$before" ] && [ -z "$(git -C "$stw" status --porcelain)" ] \
  && [ "$(cat "$stw/local.conf")" = 'kept: mine' ] && [ "$(find "$ST/.lem/worktrees" -maxdepth 1 -name '*.red-*' | grep -c '')" = 0 ] \
  && [ "$(git -C "$ST" worktree list | grep -c '')" = 2 ] && grep -q '"event": "task.red"' "$ST/.lem/state/events.jsonl"; then
  pass "red runs each criterion's tests in a worktree of its own, on the branch and with only the test files laid over the base commit: both fail there; the task's worktree is not touched, a file git ignores in it too, and the check's worktree is gone"
else
  fail "criteria red: $out / $(git -C "$stw" status --porcelain) / $(git -C "$ST" worktree list)"
fi
# What does not hold a criterion: a test that passes on the base commit too, one that changes a file both
# commits have, one whose helper is not named, a folder in the place of a file. And a criterion with no test.
story3() { git -C "$stw" checkout -q -- docs && "$PY" -c 'import sys; p, lines = sys.argv[1], sys.argv[2:]; s = open(p).read(); open(p, "w").write(s.replace("\n## Tasks", "\n".join(lines) + "\n\n## Tasks"))' "$plan" "$@" && git -C "$stw" commit -q -am "docs: a third criterion" && criteria red export-has-the-gift-note 2>&1 || true; git -C "$stw" reset -q --hard "$before"; }
# shellcheck disable=SC2016
weak=$(story3 '3. The export still has one row for each order.' '   - test: `sh export.sh` in `tests/gift.sh`')
# the settings file is the same on the base commit and on the branch: a test that reads it and then changes it
echo 'grep -q topics .lem/settings.toml || exit 1; echo changed >> .lem/settings.toml' > "$stw/tests/config.sh"
# The helper starts by its path, so that a helper that is not there exits 127 in every shell: `sh
# FILE` with no FILE is 127 in bash and 2 in dash.
echo './tests/runner.sh' > "$stw/tests/calls.sh" && echo 'exit 0' > "$stw/tests/runner.sh" && chmod +x "$stw/tests/runner.sh"
# a Python runner of the tests, which the base commit lacks: Python ends with 2 for a script that is not there
echo 'raise SystemExit(0)' > "$stw/tests/runner.py"
git -C "$stw" add -A && git -C "$stw" commit -q -m "test: more tests" && before=$(git -C "$stw" rev-parse HEAD)
# shellcheck disable=SC2016
writes=$(story3 '3. The config is read.' '   - test: `sh tests/config.sh` in `tests/config.sh`')
# shellcheck disable=SC2016
helper=$(story3 '3. The runner runs.' '   - test: `sh tests/calls.sh` in `tests/calls.sh`')
# A test command that starts a shell on a script the base commit lacks does not start there, whatever
# the shell's exit: a stand-in `sh` that exits 2 for a script that is not there, as dash does.
# shellcheck disable=SC2016  # the stand-in's own variables, expanded when it runs
mkdir -p "$WORK/dashlike" && printf '%s\n' '#!/bin/sh' '[ -f "$1" ] || exit 2' 'exec /bin/sh "$@"' > "$WORK/dashlike/sh" && chmod +x "$WORK/dashlike/sh"
# shellcheck disable=SC2016
unstarted=$(PATH="$WORK/dashlike:$PATH" story3 '3. The runner runs.' '   - test: `sh tests/runner.sh` in `tests/calls.sh`')
# shellcheck disable=SC2016
pyrunner=$(story3 '3. The runner runs.' '   - test: `python3 -B tests/runner.py` in `tests/calls.sh`')
# shellcheck disable=SC2016
folder=$(story3 '3. The tests are there.' '   - test: `sh tests/gift.sh` in `tests`')
bare=$(story3 '3. The export still has one row for each order.')
said=$(story3 '3. The export still has one row for each order.' '   - no test: the count of rows is the export of today, which no change here touches.' | field '(d["ok"], d["without_a_test"])')
echo stray > "$stw/stray.txt"
dirty=$(criteria red export-has-the-gift-note 2>&1 || true)
rm "$stw/stray.txt"
# shellcheck disable=SC2016
if grep -q 'criterion 3: `sh export.sh` passes on the base commit too, so it does not test the change' <<<"$weak" \
  && grep -q 'criterion 3: `sh tests/config.sh` passes on the base commit too' <<<"$writes" \
  && grep -q 'criterion 3: `sh tests/calls.sh` does not start on the base commit (exit 127), so its failure there proves nothing. If a file it needs is a helper of the test, name it among' <<<"$helper" \
  && grep -q 'criterion 3: `sh tests/runner.sh` does not start on the base commit (exit 2: its script file tests/runner.sh is not on the base commit), so its failure there proves nothing' <<<"$unstarted" \
  && grep -q 'criterion 3: `python3 -B tests/runner.py` does not start on the base commit (exit 2: its script file tests/runner.py is not on the base commit)' <<<"$pyrunner" \
  && grep -q "criterion 3: 'tests' is a folder on the branch. Name each file that holds the test, one by one" <<<"$folder" \
  && grep -q "criterion 3 names no test: every criterion is held by a test at the end of a build" <<<"$bare" \
  && [ "$said" = "(True, [{'criterion': 3, 'why': 'the count of rows is the export of today, which no change here touches.'}])" ] \
  && grep -q "the worktree has changes nobody committed" <<<"$dirty" && [ "$(git -C "$stw" rev-parse HEAD)" = "$before" ] \
  && [ "$(find "$ST/.lem/worktrees" -maxdepth 1 -name '*.red-*' | grep -c '')" = 0 ]; then
  pass "a criterion is not held by a test that passes on the base commit too, that only changes a file both commits have, whose helper file is not named, or that starts a shell or Python on a script the base commit lacks, whatever its exit, named in the refusal; a folder as a test file and a criterion with no test are refused, and one that says why it has none is listed"
else
  fail "criteria red refusals: $weak / $writes / $helper / $unstarted / $pyrunner / $folder / $bare / $said / $dirty"
fi
# A test that needs what a fresh worktree lacks is named as such, and the settings' checks.setup makes it.
echo 'test -f .made-by-setup && sh export.sh | grep -q "1042,for Ania"' > "$stw/tests/env.sh" && git -C "$stw" add -A && git -C "$stw" commit -q -m "test: one that needs a setup" && before=$(git -C "$stw" rev-parse HEAD)
# shellcheck disable=SC2016
lacks=$(story3 '3. The export has the note, in a set-up worktree.' '   - test: `sh tests/env.sh` in `tests/env.sh`')
sed -i.bak 's|^setup = \[\]$|setup = ["touch .made-by-setup"]|' "$ST/.lem/settings.toml" && rm "$ST/.lem/settings.toml.bak"
# shellcheck disable=SC2016
made=$(story3 '3. The export has the note, in a set-up worktree.' '   - test: `sh tests/env.sh` in `tests/env.sh`' | field '(d["ok"], d["setup"], d["tests"][2]["problem"])')
sed -i.bak 's|^setup = .*$|setup = ["exit 3"]|' "$ST/.lem/settings.toml" && rm "$ST/.lem/settings.toml.bak"
broken=$(criteria red export-has-the-gift-note 2>&1 || true)
sed -i.bak 's|^setup = .*$|setup = []|' "$ST/.lem/settings.toml" && rm "$ST/.lem/settings.toml.bak"
# A worktree that a killed run of the check left behind is removed by the next run.
git -C "$ST" worktree add -q --detach "$ST/.lem/worktrees/export-has-the-gift-note.red-tip" main && git -C "$ST" worktree lock "$ST/.lem/worktrees/export-has-the-gift-note.red-tip"
git -C "$ST" worktree add -q --detach "$ST/.lem/worktrees/export-has-the-gift-note.red-999999" main
criteria red export-has-the-gift-note >/dev/null
if grep -q "fails in a fresh worktree of the branch (exit 1). If it passes in the task's worktree, it needs something a fresh one lacks: put the commands that make it into checks.setup" <<<"$lacks" \
  && [ "$made" = "(True, [{'on': 'branch', 'command': 'touch .made-by-setup', 'exit': 0}, {'on': 'base', 'command': 'touch .made-by-setup', 'exit': 0}], None)" ] \
  && grep -q "of checks.setup failed in a fresh worktree of the branch (exit 3)" <<<"$broken" \
  && [ "$(find "$ST/.lem/worktrees" -maxdepth 1 -name '*.red-*' | grep -c '')" = 0 ] && [ "$(git -C "$ST" worktree list | grep -c '')" = 2 ]; then
  pass "a test that needs what a fresh worktree lacks is named as such and not taken for proof; the settings' checks.setup makes it in each of the two worktrees; a setup command that fails stops the check; and a worktree that a killed run left is removed"
else
  fail "criteria red and checks.setup: $lacks / $made / $broken / $(git -C "$ST" worktree list)"
fi
# Each run has a worktree and a setup of its own, so what a test writes on the branch does not reach the base run;
# the result names the files of the branch that the base run lacked.
echo 'grep -q correct .test-state || exit 1; echo corrupt > .test-state' > "$stw/tests/state.sh" && git -C "$stw" add -A && git -C "$stw" commit -q -m "test: one that changes a file of the setup" && before=$(git -C "$stw" rev-parse HEAD)
sed -i.bak 's|^setup = .*$|setup = ["echo correct > .test-state"]|' "$ST/.lem/settings.toml" && rm "$ST/.lem/settings.toml.bak"
# shellcheck disable=SC2016
state=$(story3 '3. The state is read.' '   - test: `sh tests/state.sh` in `tests/state.sh`')
lacked=$(criteria red export-has-the-gift-note | field '("export.sh" in d["run_without"], "tests/gift.sh" in d["run_without"], "tests/runner.sh" in d["run_without"])')
# A hook that fails after git made the worktree, and a setup command that locks it: neither worktree stays.
printf '%s\n' '#!/bin/sh' 'exit 9' > "$ST/.git/hooks/post-checkout" && chmod +x "$ST/.git/hooks/post-checkout"
hooked=$(status_of criteria red export-has-the-gift-note)
# a hook that leaves a process behind: the check goes on, and that process is ended. The process
# is `sleep` by a name of this run's own, so that a second run of the suite beside this one counts
# none of its own processes here.
# A sleep of a length of this run's own (its process id is in the decimals): a name of our own for
# `sleep` does not start where one binary holds every core tool and reads its own name (Ubuntu).
NAP1="32.9$$"; NAP2="31.7$$"
printf '%s\n' '#!/bin/sh' "sleep $NAP1 &" 'exit 0' > "$ST/.git/hooks/post-checkout"
watched=$(criteria red export-has-the-gift-note | field 'd["ok"]')
watched="$watched $(pgrep -f "sleep ${NAP1/./\\.}" | grep -c '' || true)"
rm "$ST/.git/hooks/post-checkout"
after_hook=$(git -C "$ST" worktree list | grep -c '')
sed -i.bak 's|^setup = .*$|setup = ["git worktree lock ."]|' "$ST/.lem/settings.toml" && rm "$ST/.lem/settings.toml.bak"
locked=$(criteria red export-has-the-gift-note | field 'd["ok"]')
after_lock="$(git -C "$ST" worktree list | grep -c '') $(find "$ST/.lem/worktrees" -maxdepth 1 -name '*.red-*' | grep -c '' || true)"
# A worktree that cannot be removed is said beside the failure that came first, and the next run removes it.
sed -i.bak 's|^setup = .*$|setup = ["chmod 500 ..; exit 3"]|' "$ST/.lem/settings.toml" && rm "$ST/.lem/settings.toml.bak"
stuck=$(criteria red export-has-the-gift-note 2>&1 || true)
chmod 700 "$ST/.lem/worktrees"
sed -i.bak 's|^setup = .*$|setup = []|' "$ST/.lem/settings.toml" && rm "$ST/.lem/settings.toml.bak"
criteria red export-has-the-gift-note >/dev/null
after_stuck="$(git -C "$ST" worktree list | grep -c '') $(find "$ST/.lem/worktrees" -maxdepth 1 -name '*.red-*' | grep -c '' || true)"
# One check of a task at a time: while another process holds the task's lock, a second check is refused.
"$PY" -c 'import fcntl, sys, time; f = open(sys.argv[1], "w"); fcntl.flock(f, fcntl.LOCK_EX); print("held", flush=True); time.sleep(30)' "$ST/.lem/state/tasks/export-has-the-gift-note/red.lock" > "$WORK/lock.out" &
holder=$!
soon test -s "$WORK/lock.out"
second=$(criteria red export-has-the-gift-note 2>&1 || true)
kill "$holder" 2>/dev/null || true; wait "$holder" 2>/dev/null || true
# A check that is stopped ends the command it runs, and leaves no worktree.
sed -i.bak "s|^setup = .*\$|setup = [\"sleep $NAP2\"]|" "$ST/.lem/settings.toml" && rm "$ST/.lem/settings.toml.bak"
"$PY" -B "$CRITERIA" --repo "$ST" red export-has-the-gift-note > "$WORK/stopped.out" 2>&1 &
check=$!
napping() { pgrep -f "sleep ${NAP2/./\\.}" >/dev/null 2>&1; }
soon napping
started=$(pgrep -f "sleep ${NAP2/./\\.}" | grep -c '' || true)
kill -TERM "$check" 2>/dev/null || true; wait "$check" 2>/dev/null || true
left=$(pgrep -f "sleep ${NAP2/./\\.}" | grep -c '' || true)
after_stop="$(git -C "$ST" worktree list | grep -c '') $(find "$ST/.lem/worktrees" -maxdepth 1 -name '*.red-*' | grep -c '' || true)"
sed -i.bak 's|^setup = .*$|setup = []|' "$ST/.lem/settings.toml" && rm "$ST/.lem/settings.toml.bak"
# shellcheck disable=SC2016
if grep -q 'criterion 3: `sh tests/state.sh` passes on the base commit too' <<<"$state" && [ "$lacked" = "(True, False, True)" ] \
  && [ "$hooked" = 1 ] && [ "$watched" = "True 0" ] && [ "$after_hook" = 2 ] && [ "$locked" = True ] && [ "$after_lock" = "2 0" ] \
  && grep -q "of checks.setup failed in a fresh worktree of the branch (exit 3)" <<<"$stuck" && grep -q "red-tip could not be removed; remove it yourself: git -C" <<<"$stuck" && [ "$after_stuck" = "2 0" ] \
  && grep -q "another check of this task's criteria runs now" <<<"$second" \
  && [ "$started" -ge 1 ] && [ "$left" = 0 ] && [ "$after_stop" = "2 0" ] && grep -q "the check was stopped, and its commands are ended; its worktrees are removed" "$WORK/stopped.out"; then
  pass "each run of the check has a worktree and a setup of its own, and the result names what the base run lacked; a failed hook, a locked worktree and a stopped check leave no worktree and no process; and a second check of one task waits"
else
  fail "the check's worktrees: $state / $lacked / stuck $stuck $after_stuck / hook $hooked $watched $after_hook / lock $locked $after_lock / $second / stop $started $left $after_stop $(cat "$WORK/stopped.out")"
fi
# A plan whose criteria do not have the form is refused with the line that is wrong.
form() { printf '%s\n' "$@" > "$plan"; criteria show export-has-the-gift-note 2>&1 || true; }
no_section=$(form '# A plan' '' '## Tasks')
no_kind=$(form '## Acceptance criteria' '' '1. A criterion.')
two=$(form '## Acceptance criteria' '' 'Size: small, because it is one sentence.' '' '1. One.' '2. Two.')
order=$(form '## Acceptance criteria' '' 'Size: full, because of two things.' '' '1. One.' '3. Three.')
odd_size=$(form '## Acceptance criteria' '' 'Size: medium, because it is between.' '' '1. One.')
# An example of the form in a code fence is not the section, and a plan of another task whose name ends the same way is not this task's.
# shellcheck disable=SC2016
fenced=$(form '# A plan' '' '````markdown' 'An example in an example:' '```' '## Acceptance criteria' '' 'Size: small, because it is an example.' '' '1. An example.' '```' '````' '' '## Acceptance criteria' '' 'Size: full, because it is the real one.' '' '1. The real criterion.' | field '(d["size"], d["criteria"][0]["text"])')
git -C "$stw" checkout -q -- docs
printf '%s\n' '## Acceptance criteria' '' 'Size: small, because it is another task.' '' '1. Not this task.' > "$stw/docs/plans/2026-11-16-csv-export-has-the-gift-note.md"
other=$(criteria show export-has-the-gift-note | field '(d["size"], d["plan"].rsplit("/", 1)[1])')
rm "$stw/docs/plans/2026-11-16-csv-export-has-the-gift-note.md"
criteria record export-has-the-gift-note >/dev/null && criteria red export-has-the-gift-note >/dev/null
# shellcheck disable=SC2016
if [ "$fenced" = "('full', 'The real criterion.')" ] && [ "$other" = "('full', '2026-11-15-export-has-the-gift-note.md')" ] \
  && grep -q "2026-11-15-export-has-the-gift-note.md:3: the section starts with \`Size: full, because ...\`" <<<"$odd_size" \
  && grep -q 'has no `## Acceptance criteria` section' <<<"$no_section" && grep -q "2026-11-15-export-has-the-gift-note.md:3: the section starts with" <<<"$no_kind" \
  && grep -q "a task on the fast track has one criterion, and this one has 2: it takes the standard track" <<<"$two" && grep -q ":6: the criteria are numbered 1, 2, 3 in order" <<<"$order" \
  && [ "$(status_of criteria show no-such-task)" = 1 ]; then
  pass "a plan with no criteria section, no size, a small change of two criteria, an unknown size or a gap in the numbers is refused with the place and the fix; a fenced example is not the section, and a plan of another task is not read"
else
  fail "the form of the criteria: $no_section / $no_kind / $two / $order / $odd_size"
fi

# Approved criteria are frozen as written: the plan's criteria are those, word for word, with only test lines added.
# They are approved at the interview, before the task has a worktree.
project --repo "$ST" task-dir approved-note >/dev/null
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the note gets a file and an empty case.' '' '1. The note file holds the gift note of order 1042: "for Ania".' \
  '2. An order with no gift note has the line "1043," and no word' '   after the comma.' > "$WORK/approved.md"
approved=$(criteria approve approved-note --file "$WORK/approved.md" 2>&1 || true)
kept_stories=$ST/.lem/state/tasks/approved-note/criteria.json
# shellcheck disable=SC2016
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because of a test.' '' '1. A criterion.' '   - test: `sh t.sh` in `t.sh`' > "$WORK/tested.md"
tested=$(criteria approve approved-note --file "$WORK/tested.md" 2>&1 || true)
not_one=$(criteria approve approved-note --file "$WORK/approved.md" --small 2>&1 || true)
no_file=$(criteria approve approved-note 2>&1 || true)
kept_now=$(criteria approved approved-note 2>/dev/null | field '(d["approved"]["by"], d["approved"]["digest"], [s["text"] for s in d["approved"]["criteria"]])' 2>&1 || true)
if [ "$(field '(d["by"], d["size"], len(d["digest"]), [s["n"] for s in d["criteria"]], d["criteria"][1]["text"])' <<<"$approved" 2>/dev/null)" \
  = "('owner', 'full', 12, [1, 2], 'An order with no gift note has the line \"1043,\" and no word after the comma.')" ] \
  && [ "$("$PY" -c 'import json, sys; print(json.load(open(sys.argv[1]))["text"] == open(sys.argv[2]).read())' "$kept_stories" "$WORK/approved.md" 2>/dev/null)" = True ] \
  && [ "$(grep -c '"event": "criteria.approved", "task": "approved-note", "by": "owner"' "$ST/.lem/state/events.jsonl")" = 1 ] \
  && [ "$kept_now" = "('owner', '$(field 'd["digest"]' <<<"$approved" 2>/dev/null)', ['The note file holds the gift note of order 1042: \"for Ania\".', 'An order with no gift note has the line \"1043,\" and no word after the comma.'])" ] \
  && grep -q "criterion 1 of tested.md has a test line: the criteria the owner approves have none, and the lead adds them in the plan" <<<"$tested" \
  && grep -q "says .Size: full.: the standard track waits for the owner's own yes" <<<"$not_one" && grep -q "approve needs --file" <<<"$no_file" \
  && [ "$(grep -c '"event": "criteria.approved"' "$ST/.lem/state/events.jsonl")" = 1 ]; then
  pass "approve keeps the criteria the owner approved, before the task has a worktree: their text as written, a digest and who approved them, with one event for the board; a file with a test line, a full change as a small change and no file are refused"
else
  fail "criteria approve: $approved / $tested / $not_one / $no_file / $kept_now"
fi
# The plan copies the approved criteria, broken into other lines, and adds only the test lines: show and red take it.
atw=$(project --repo "$ST" worktree-dir approved-note)
git -C "$ST" worktree add -q -b feat/approved-note "$atw" main
project --repo "$ST" state approved-note building 'lead: builder' >/dev/null
mkdir -p "$atw/docs/plans" "$atw/tests"
aplan=$atw/docs/plans/2026-11-16-approved-note.md
# aplan_with LINE...: the plan of approved-note, with these lines as its criteria, and its commit
aplan_with() {
  printf '%s\n' '# The note' '' 'careful: no, it touches one new file.' '' '## Acceptance criteria' '' 'Size: full, because the note gets a file and an empty case.' '' "$@" '' '## Tasks' '' '1. The note.' > "$aplan"
  git -C "$atw" add -A && git -C "$atw" commit -q -m "docs: the plan"
}
printf '%s\n' 'for Ania' '1043,' > "$atw/note.txt"
echo 'grep -qx "for Ania" note.txt' > "$atw/tests/ania.sh" && echo 'grep -qx "1043," note.txt' > "$atw/tests/empty.sh"
# shellcheck disable=SC2016
one='   - test: `sh tests/ania.sh` in `tests/ania.sh`'
# shellcheck disable=SC2016
two='   - test: `sh tests/empty.sh` in `tests/empty.sh`'
s1='1. The note file holds the gift note of order 1042: "for Ania".'
aplan_with "$s1" "$one" '2. An order with no gift note has the line "1043," and' '   no word after the comma.' "$two"
copied=$(criteria show approved-note 2>&1 || true)
held=$(criteria red approved-note 2>&1 || true)
if [ "$(field '(d["approved"]["by"], d["changes"], [len(s["tests"]) for s in d["criteria"]])' <<<"$copied" 2>/dev/null)" = "('owner', [], [1, 1])" ] \
  && [ "$(field 'd["approved"]["digest"]' <<<"$copied" 2>/dev/null)" = "$(field 'd["digest"]' <<<"$approved" 2>/dev/null)" ] \
  && [ "$(field '(d["ok"], [t["criterion"] for t in d["tests"]])' <<<"$held" 2>/dev/null)" = "(True, [1, 2])" ]; then
  pass "a plan whose criteria are the approved ones, in other line breaks and with test lines added, passes show and red"
else
  fail "a plan of approved criteria: $copied / $held"
fi
# A criterion the plan adds after the approved ones, with no record of it, is refused by show and red.
aplan_with "$s1" "$one" '2. An order with no gift note has the line "1043," and no word after the comma.' "$two" \
  '3. The note file ends with a line break.' '   - no test: printf ends every line so.'
extra=$(criteria show approved-note 2>&1 || true)
red_extra=$(criteria red approved-note 2>&1 || true)
if grep -qF "criterion 3 of 2026-11-16-approved-note.md, 'The note file ends with a line break.', is not among the expected criteria, which end at 2" <<<"$extra" \
  && grep -qF -- "\`--added N --now TEXT\`" <<<"$extra" && grep -qF "criterion 3 of 2026-11-16-approved-note.md, 'The note file ends with a line break.', is not among" <<<"$red_extra"; then
  pass "a criterion the plan adds after the approved ones with no record of it is refused by show and red, with how its addition is recorded"
else
  fail "an extra criterion at the end of the plan: $extra / $red_extra"
fi
adecide() { "$PY" -B "$PWD/skills/lem/scripts/decisions.py" --repo "$ST" "$@"; }
t1='The note file holds the gift note of order 1042: "for Ania".'
t2='An order with no gift note has the line "1043," and no word after the comma.'
c1='The note file holds the gift note of order 1042, "for Ania".'
c2='The note file holds the note "for Ania" of order 1042.'
a3='The note file ends with a line break.'
# A reworded criterion is refused by show and red until its change is recorded, with its text before and after.
aplan_with "1. $c1" "$one" "2. $t2" "$two"
reworded=$(criteria show approved-note 2>&1 || true)
red_reworded=$(criteria red approved-note 2>&1 || true)
adecide criterion approved-note --changed 1 --was "$t1" --now "$c1" --why "The importer splits on a colon." --by lead >/dev/null 2>&1 || true
changed_now=$(criteria show approved-note 2>/dev/null | field '[(c["change"], c["criterion"], c["how"]) for c in d["changes"]]' 2>&1 || true)
# An earlier change lets no later one pass: the plan changes criterion 1 again, and a record of it names what it is now.
aplan_with "1. $c2" "$one" "2. $t2" "$two"
again=$(criteria show approved-note 2>&1 || true)
stale=$(adecide criterion approved-note --changed 1 --was "$t1" --now "$c2" --why "The note comes first." --by lead 2>&1 || true)
adecide criterion approved-note --changed 1 --was "$c1" --now "$c2" --why "The note comes first in the sentence." --by lead >/dev/null 2>&1 || true
chained=$(criteria show approved-note 2>/dev/null | field '[c["criterion"] for c in d["changes"]]' 2>&1 || true)
# A criterion the build added can leave again, by a record of its own.
adecide criterion approved-note --added 3 --now "$a3" --why "The reader of the file needs it." --by lead >/dev/null 2>&1 || true
aplan_with "1. $c2" "$one" "2. $t2" "$two" "3. $a3" '   - no test: printf ends every line so.'
added_now=$(criteria show approved-note 2>/dev/null | field 'len(d["changes"])' 2>&1 || true)
adecide criterion approved-note --removed 3 --was "$a3" --why "Printf ends every line so, and nobody needs the rule." --by lead >/dev/null 2>&1 || true
aplan_with "1. $c2" "$one" "2. $t2" "$two"
gone_again=$(criteria show approved-note 2>/dev/null | field '[(c["how"], c["criterion"]) for c in d["changes"]]' 2>&1 || true)
# A dropped criterion is refused until its removal is recorded with its text.
aplan_with "1. $c2" "$one"
dropped=$(criteria show approved-note 2>&1 || true)
wrong_was=$(adecide criterion approved-note --removed 2 --was "An order with no gift note has the line 1043." --why "Every order has a note now." --by lead 2>&1 || true)
adecide criterion approved-note --removed 2 --was "$t2" --why "Every order has a note now." --by personas --said "The merchant and the accountant both dropped it." >/dev/null 2>&1 || true
removed_now=$(criteria show approved-note 2>/dev/null | field '(d["changes"][-1]["how"], d["changes"][-1]["by"], d["changes"][-1]["said"])' 2>&1 || true)
expected=$(adecide changes approved-note 2>/dev/null | field 'd["expected"]' 2>&1 || true)
# The command takes one change, its reason, and who made it: a decision of the record, or the lead or the personas.
neither=$(adecide criterion approved-note --added 2 --now "x" --why "w" 2>&1 || true)
both=$(adecide criterion approved-note --added 2 --now "x" --why "w" --decision 1 --by lead 2>&1 || true)
nosaid=$(adecide criterion approved-note --added 2 --now "x" --why "w" --by personas 2>&1 || true)
twoways=$(adecide criterion approved-note --changed 1 --added 2 --now "x" --why "w" --by lead 2>&1 || true)
added_was=$(adecide criterion approved-note --added 2 --now "x" --was "y" --why "w" --by lead 2>&1 || true)
nochoice=$(adecide criterion approved-note --added 2 --now "x" --why "w" --decision 9 2>&1 || true)
not_approved=$(adecide criterion export-has-the-gift-note --changed 1 --was "x" --now "y" --why "w" --by lead 2>&1 || true)
log_story=$(status_of adecide log approved-note --what x --chose y --why z --by lead --criterion 1 --was "$t1")
records=$(grep -c '"kind": "criterion"' "$ST/.lem/state/tasks/approved-note/decisions.jsonl" || true)
plain=$(criteria show export-has-the-gift-note 2>/dev/null | field '(d["approved"], d["changes"])' 2>&1 || true)
if grep -qF "criterion 1 of 2026-11-16-approved-note.md says '$c1', and the expected criterion 1 is '$t1'" <<<"$reworded" \
  && grep -qF 'lem decisions criterion approved-note --changed N --was TEXT --now TEXT' <<<"$reworded" \
  && grep -qF "criterion 1 of 2026-11-16-approved-note.md says '$c1'" <<<"$red_reworded" && [ "$changed_now" = "[(1, 1, 'changed')]" ] \
  && grep -qF "criterion 1 of 2026-11-16-approved-note.md says '$c2', and the expected criterion 1 is '$c1'" <<<"$again" \
  && grep -qF "criterion 1 is '$c1' after every earlier change, and --was says '$t1'" <<<"$stale" && [ "$chained" = "[1, 1]" ] \
  && [ "$added_now" = 3 ] && [ "$gone_again" = "[('changed', 1), ('changed', 1), ('added', 3), ('removed', 3)]" ] \
  && grep -qF "2026-11-16-approved-note.md lacks criterion 2, '$t2', which the expected criteria hold" <<<"$dropped" \
  && grep -qF "criterion 2 is '$t2' after every earlier change, and --was says 'An order with no gift note has the line 1043.'" <<<"$wrong_was" \
  && [ "$removed_now" = "('removed', 'personas', 'The merchant and the accountant both dropped it.')" ] && [ "$expected" = "['$c2']" ] \
  && grep -qF "names --decision ID, the decision of the record that led to it, or --by lead|personas when none did: one of the two" <<<"$neither" \
  && grep -qF "one of the two" <<<"$both" && grep -qF -- "--by personas needs --said" <<<"$nosaid" \
  && grep -qF "a criterion change is one of --changed N, --added N or --removed N" <<<"$twoways" && grep -qF -- "--added takes no --was: an added criterion had no text before" <<<"$added_was" \
  && grep -qF "no decision 9 in approved-note" <<<"$nochoice" \
  && grep -qF "export-has-the-gift-note has no approved criteria, so no change of them is recorded" <<<"$not_approved" && [ "$log_story" = 2 ] \
  && [ "$records" = 5 ] && [ "$plain" = "(None, [])" ]; then
  pass "a plan whose criteria are not the approved ones with each recorded change applied is refused by show and red: an earlier change lets no later one pass, a criterion the build added can leave again, and a change whose text before is not the criterion as it stands is refused when it is recorded; the command takes one change with its reason and who made it; a task with no approved criteria records none and keeps the plan as the source"
else
  fail "criterion changes against the approved criteria: $reworded / $red_reworded / $changed_now / $again / $stale / $chained / $added_now / $gone_again / $dropped / $wrong_was / $removed_now / $expected / $neither / $both / $nosaid / $twoways / $added_was / $nochoice / $not_approved / $log_story / $records / $plain"
fi
# His next approval starts the changes again. A change keeps its texts as typed, and two spaces of a literal value match;
# a plan of another size than the approved one is refused, since the size is his.
# shellcheck disable=SC2016
code1='The note file holds the code `A  B` for order 1042.'
# shellcheck disable=SC2016
code2='The note file holds the code `A  B` for orders 1042 and 1044.'
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the note gets a code.' '' "1. $code1" '2. Order 1043 has no note line.' > "$WORK/reapproved.md"
criteria approve approved-note --file "$WORK/reapproved.md" >/dev/null 2>&1 || true
reset=$(adecide changes approved-note 2>/dev/null | field '(len(d["changes"]), d["expected"])' 2>&1 || true)
spaced=$(adecide criterion approved-note --changed 1 --was "$code1" --now "$code2" --why "Order 1044 has the note too." --by lead 2>/dev/null | field '(d["was"], d["now"])' 2>&1 || true)
printf '%s\n' '# The note' '' '## Acceptance criteria' '' 'Size: small, because it is one sentence.' '' "1. $code2" '' '## Tasks' '' '1. The note.' > "$aplan"
kind=$(criteria show approved-note 2>&1 || true)
# shellcheck disable=SC2016
aplan_with '1. The note file holds the code `A  B` for' '   orders 1042 and 1044.' '2. Order 1043 has no note line.'
kept_spaces=$(criteria show approved-note 2>/dev/null | field '(len(d["changes"]), d["criteria"][0]["text"])' 2>&1 || true)
if [ "$reset" = "(0, ['$code1', 'Order 1043 has no note line.'])" ] && [ "$spaced" = "('$code1', '$code2')" ] \
  && grep -qF "2026-11-16-approved-note.md says \`Size: small\`, and the owner approved its criteria with \`Size: full\`: a change of the track is the owner's only" <<<"$kind" \
  && [ "$kept_spaces" = "(1, '$code2')" ]; then
  pass "his next approval starts the criterion changes again; a change keeps its texts as typed, two spaces of a literal value match, and a criterion broken over two lines is the same criterion; a plan of another size than the approved one is refused"
else
  fail "a new approval, spaces and the size: $reset / $spaced / $kind / $kept_spaces"
fi
# An approval is known by its number, not by its text: his approval of a text approved before is a new one, with no
# change after it, and the changes of an earlier approval do not come back when its text does.
criteria approve approved-note --file "$WORK/reapproved.md" >/dev/null 2>&1 || true
same_text=$(adecide changes approved-note 2>/dev/null | field '(d["approved"]["number"], len(d["changes"]), d["expected"][0])' 2>&1 || true)
# shellcheck disable=SC2016
aplan_with '1. The note file holds the code `A  B` for order 1042.' '2. Order 1043 has no note line.'
just_approved=$(criteria show approved-note 2>&1 | field '(d["approved"]["number"], d["changes"])' 2>&1 || true)
criteria approve approved-note --file "$WORK/approved.md" >/dev/null 2>&1 || true
criteria approve approved-note --file "$WORK/reapproved.md" >/dev/null 2>&1 || true
back_again=$(adecide changes approved-note 2>/dev/null | field '(d["approved"]["number"], len(d["changes"]), [(c["approval"], c["taken_over_by"]) for c in d["history"]][-1], [a["number"] for a in d["approvals"]])' 2>&1 || true)
numbered=$(grep '"event": "criteria.approved", "task": "approved-note"' "$ST/.lem/state/events.jsonl" | "$PY" -c 'import json, sys; print([json.loads(line).get("number") for line in sys.stdin])')
if [ "$same_text" = "(3, 0, '$code1')" ] && [ "$just_approved" = "(3, [])" ] && [ "$back_again" = "(5, 0, (2, 3), [1, 2, 3, 4, 5])" ] \
  && [ "$numbered" = "[1, 2, 3, 4, 5]" ]; then
  pass "an approval has a number of its own: his approval of a text approved before starts with no change after it, the plan that holds what he just approved passes, and the changes of an earlier approval do not come back with its text; each change stays in the history with the approval that took it over"
else
  fail "approvals by number: $same_text / $just_approved / $back_again / $numbered"
fi
# An automatic approval is only ever the first contract: Lem's approval of a small change in his name does not replace his full change.
printf '%s\n' '## Acceptance criteria' '' 'Size: small, because it is one sentence.' '' '1. The note file omits the code for order 1042.' > "$WORK/omits.md"
over_feature=$(criteria approve approved-note --file "$WORK/omits.md" --small 2>&1 || true)
contract=$(criteria approved approved-note 2>/dev/null | field '(d["approved"]["number"], d["approved"]["by"], d["approved"]["size"], d["approved"]["criteria"][0]["text"])' 2>&1 || true)
if grep -qF "approved-note has approval 5 of its criteria already (by owner): Lem approves the fast track's criterion in the owner's name only as the first contract" <<<"$over_feature" \
  && grep -qF "the track only through the owner's own approval" <<<"$over_feature" && [ "$contract" = "(5, 'owner', 'full', '$code1')" ]; then
  pass "Lem's approval of a small change in his name is only a task's first contract: over his approved full change it is refused, and his criteria and their size stay"
else
  fail "a small change over his full change: $over_feature / $contract"
fi
# Every approval takes the task's lock for its check and its write: while a freeze holds it, his approval waits, and then the
# freeze, which comes too late, is refused.
project --repo "$ST" task-dir locked-note >/dev/null
"$PY" -c 'import fcntl, sys, time; f = open(sys.argv[1], "w"); fcntl.flock(f, fcntl.LOCK_EX); print("held", flush=True); time.sleep(20)' \
  "$ST/.lem/state/tasks/locked-note/criteria.lock" > "$WORK/criteria-lock.out" &
holder=$!
soon test -s "$WORK/criteria-lock.out"
"$PY" -B "$CRITERIA" --repo "$ST" approve locked-note --file "$WORK/reapproved.md" > "$WORK/his-approval.out" 2>&1 &
his=$!
sleep 0.5
while_held=$([ -e "$ST/.lem/state/tasks/locked-note/criteria.json" ] && echo written || echo waits)
kill "$holder" 2>/dev/null || true; wait "$holder" 2>/dev/null || true
wait "$his" || true
late_freeze=$(criteria approve locked-note --read 2>&1 || true)
after_lock=$(criteria approved locked-note 2>/dev/null | field '(d["approved"]["number"], d["approved"]["by"])' 2>&1 || true)
if [ "$while_held" = waits ] && [ "$after_lock" = "(1, 'owner')" ] \
  && grep -qF "locked-note has approval 1 of its criteria already (by owner): a read freezes only the first contract" <<<"$late_freeze"; then
  pass "an approval checks and writes under the task's lock: his approval waits while another holds it, and a freeze after his approval is refused"
else
  fail "approvals under one lock: $while_held / $after_lock / $late_freeze / $(cat "$WORK/his-approval.out")"
fi

# The backlog of the board: board.py reads the items for its view, with what each needs beside its text.
BKB=$WORK/backlog-board
git init -q -b main "$BKB" && mkdir -p "$BKB/docs/backlog" "$BKB/app" && printf 'def export_rows():\n    return []\n' > "$BKB/app/export.py"
bitem() { printf '%s\n' '---' "worth: $2" "where: $3" "added: $4" '---' "# $5" '' "$6" > "$BKB/docs/backlog/$1.md"; }
# shellcheck disable=SC2016  # the backticks are markdown in an item's title
bitem export-drops-columns yes app/export.py:export_rows 2026-11-02 'The export drops `custom` columns' 'A merchant does not find the gift note.'
bitem slow-report later app/report.py:monthly 2026-10-20 'The monthly report takes nine seconds' 'It reads each order one by one.'
bitem which-currency yes app/export.py:no_such_name 2026-11-14 'Which currency rounds half up' 'Nobody decided for PLN.'
printf '%s\n' '---' 'worth: no' '---' '# A dark theme' '' 'Decided against.' > "$BKB/docs/backlog/dark-theme.md"
git -C "$BKB" add -A && git -C "$BKB" -c user.name=t -c user.email=t@t commit -q -m start
bitem new-from-a-landing maybe app/export.py 2026-11-15 'A new item' 'Not committed yet.'
: > "$BKB/docs/backlog/a b;c.md"
ln -s moved-away.md "$BKB/docs/backlog/broken-link.md" && mkdir "$BKB/docs/backlog/folder-item.md"
project --repo "$BKB" init --base main >/dev/null
# backlog_of REPO: the items as the board reads them (board.backlog), as JSON in $WORK/backlog.json
backlog_of() {
  project --repo "$1" show > "$WORK/settings.json"
  "$PY" -B -c 'import json, sys; sys.path.insert(0, sys.argv[1]); import board; print(json.dumps(board.backlog(json.load(open(sys.argv[2])))))' \
    "$PWD/skills/lem/scripts" "$WORK/settings.json" > "$WORK/backlog.json"
}
feed() { "$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])); print(eval(sys.argv[2], {"d": d, "by": {i["slug"]: i for i in d["items"]}}))' "$WORK/backlog.json" "$1"; }
backlog_of "$BKB"
if [ "$(feed '(d["folder"], "judged" in d, sorted(by))')" = "('docs/backlog', False, ['a b;c', 'broken-link', 'dark-theme', 'export-drops-columns', 'folder-item', 'new-from-a-landing', 'slow-report', 'which-currency'])" ] \
  && [ "$(feed '(by["export-drops-columns"]["title"], by["export-drops-columns"]["worth"], by["export-drops-columns"]["where_problem"], by["export-drops-columns"]["state"], by["export-drops-columns"]["path"])')" = "('The export drops custom columns', 'yes', '', '', 'docs/backlog/export-drops-columns.md')" ] \
  && [ "$(feed '(by["slow-report"]["where_problem"], by["which-currency"]["where_problem"], by["dark-theme"]["worth"], by["dark-theme"]["where"])')" = "('the file is not there', 'not in the file: no_such_name', 'no', '')" ] \
  && [ "$(feed '(by["new-from-a-landing"]["worth"], by["new-from-a-landing"]["state"], by["a b;c"]["title"])')" = "('unset', 'new', 'a b;c')" ] \
  && [ "$(feed '(by["broken-link"]["state"], by["folder-item"]["state"], "cannot be read" in by["broken-link"]["body"])')" = "('unreadable', 'unreadable', True)" ]; then
  pass "the board's backlog has each item with its worth, whether its place in the code is still there and whether git has it, and an item that cannot be read is listed as such"
else
  fail "the backlog: $(head -c 600 "$WORK/backlog.json")"
fi
# A backlog folder that git does not know yet: its first item is new, though git names only the folder.
FIRST=$WORK/backlog-first
git init -q -b main "$FIRST" && commit "$FIRST" start && project --repo "$FIRST" init --base main >/dev/null && mkdir -p "$FIRST/docs/backlog"
printf '%s\n' '# The first item' '' 'No frontmatter at all.' > "$FIRST/docs/backlog/first.md"
backlog_of "$FIRST"
if [ "$(feed '(by["first"]["state"], by["first"]["title"])')" = "('new', 'The first item')" ]; then
  pass "the first item of a backlog folder that git does not know yet is new"
else
  fail "a first backlog item: $(head -c 500 "$WORK/backlog.json")"
fi
# lem board: what it refuses before it asks the board server (tests/lem-serve.sh opens the board, with a server).
BOARD=$PWD/skills/lem/scripts/board.py
board() { env -u AGTERM_SESSION_ID -u AGTERM_SOCKET -u AGT_SESSION_ID -u AGT_SOCKET "$PY" -B "$BOARD" "$@"; }
err=$(board --repo "$OLD" --no-open --task no-such-task 2>&1 || true)
if [ "$(status_of board --repo "$OLD" --no-open --task no-such-task)" = 1 ] && grep -q "the tasks are: .*second-task" <<<"$err" \
  && [ "$(status_of board --repo "$OLD")" = 1 ] && grep -qF "not inside an agterm session" <<<"$(board --repo "$OLD" 2>&1 || true)"; then
  pass "an unknown task is refused with the names of the known ones, and outside an agterm session lem board opens nothing and says so"
else
  fail "board's refusals: $err"
fi
board --repo "$OLD" --no-open --demo >/dev/null 2>&1 || true
board --repo "$OLD" --no-open >/dev/null 2>&1 || true
if [ -f "$OLD/.lem/state/demo" ] && [ "$(project --repo "$OLD" show | "$PY" -B -c 'import json, sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); import board; s = json.load(sys.stdin); print(board.meta_of(s, Path(sys.argv[2]))["demo"])' "$PWD/skills/lem/scripts" "$OLD/.lem/state")" = True ]; then
  pass "board --demo marks the state folder's tasks as examples, and a later run with no flag keeps the mark"
else
  fail "board --demo: no mark in $OLD/.lem/state"
fi
rm "$OLD/.lem/state/demo"

# Any page of Lem to read opens as a page companion of the session's group, and the same file shown again reloads its
# companion. No overlay covers the session; a file that is no page and a call outside agterm are refused.
# agtermctl is a stand-in that prints a tree and records its calls.
FAKE=$WORK/fake
mkdir -p "$FAKE"
# shellcheck disable=SC2016  # the stand-in's own variables, expanded when it runs
printf '%s\n' '#!/bin/sh' 'echo "$*" >> "$AGT_CALLS"' 'case "$1" in tree) cat "$AGT_TREE" ;; *) echo "{\"result\": {\"id\": \"NEW\"}}" ;; esac' > "$FAKE/agtermctl"
chmod +x "$FAKE/agtermctl"
printf '%s\n' '{"result": {"tree": {"workspaces": [{"sessions": [{"id": "CCC", "name": "lem c"}]}]}}}' > "$WORK/tree.json"
mkdir -p "$WORK/pages" && echo '<html><body>built</body></html>' > "$WORK/pages/page.html" && echo 'text' > "$WORK/pages/notes.md"
showpage() { : > "$WORK/calls"; env PATH="$FAKE:$PATH" AGT_CALLS="$WORK/calls" AGT_TREE="$WORK/tree.json" AGTERM_SESSION_ID=CCC AGTERM_SOCKET=/none "$PY" -B "$BOARD" "$@"; }
first=$(showpage --page "$WORK/pages/page.html" --name "gift-note page")
first_calls=$(cat "$WORK/calls")
printf '%s\n' '{"result": {"tree": {"workspaces": [{"sessions": [{"id": "CCC", "name": "lem c"},' \
  "{\"id\": \"PP\", \"name\": \"gift-note page\", \"content\": \"page\", \"parent\": \"CCC\", \"htmlOverlays\": [{\"file\": \"$WORK/pages/page.html\"}]}]}]}}}" > "$WORK/tree-page.json"
again=$(: > "$WORK/calls"; env PATH="$FAKE:$PATH" AGT_CALLS="$WORK/calls" AGT_TREE="$WORK/tree-page.json" AGTERM_SESSION_ID=CCC AGTERM_SOCKET=/none "$PY" -B "$BOARD" --page "$WORK/pages/page.html" --name "gift-note page")
again_calls=$(cat "$WORK/calls")
not_page=$(showpage --page "$WORK/pages/notes.md" 2>&1 || true)
outside=$(env -u AGTERM_SESSION_ID -u AGTERM_SOCKET -u AGT_SESSION_ID -u AGT_SOCKET "$PY" -B "$BOARD" --page "$WORK/pages/page.html" 2>&1 || true)
if [ "$(field '(d["companion"], d["reloaded"], d["parent"], d["name"])' <<<"$first")" = "('NEW', False, 'CCC', 'gift-note page')" ] \
  && grep -q "session overlay open --html $WORK/pages/page.html --cwd $WORK/pages --js --companion --target CCC" <<<"$first_calls" \
  && ! grep -q "overlay open --html [^ ]* --cwd [^ ]* --target" <<<"$first_calls" \
  && [ "$(field '(d["companion"], d["reloaded"])' <<<"$again")" = "('PP', True)" ] && grep -q "session overlay reload --current --target PP" <<<"$again_calls" \
  && ! grep -q "overlay open" <<<"$again_calls" && grep -qF "is not an HTML file" <<<"$not_page" && grep -qF "not inside an agterm session" <<<"$outside"; then
  pass "a page of Lem to read opens as a page companion of the session's group, never over the session, and the same file shown again reloads its companion; a file that is no page and a call outside agterm are refused"
else
  fail "a page as a companion: $first / $first_calls / $again / $again_calls / $not_page / $outside"
fi
night=0
for name in lem lem-mark; do
  "$PY" -B "$PWD/assets/night.py" "$PWD/assets/$name.svg" "$WORK/$name-night.svg" && cmp -s "$WORK/$name-night.svg" "$PWD/assets/$name-night.svg" || night=1
done
if [ "$night" = 0 ]; then
  pass "each night logo is the day logo's drawing in the night palette, as assets/night.py writes it"
else
  fail "a night logo differs from what assets/night.py writes from the day file: run it again"
fi
# night.py on small scenes: the night sky's group keeps its colors and the rest goes through NIGHT, the
# rule that hides a sky is swapped; a color that is no six-digit lowercase hex, inside the night sky too,
# and a scene with the mark of one sky and not the other, are refused with the fix
night_sky() {
  printf '%s\n' '<svg><style>.c2-sky-night { display: none; }</style>' "<g class=\"c2-sky-day\"><rect fill=\"$1\"/></g>" \
    "<g class=\"c2-sky-night\"><g><rect fill=\"$2\"/></g><rect fill=\"#c7a95a\"/></g>" "<rect fill=\"#b5c5c0\"/></svg>" > "$WORK/sky.svg"
  "$PY" -B "$PWD/assets/night.py" "$WORK/sky.svg" "$WORK/sky-night.svg" 2>&1
}
sky_ok=$(night_sky '#b5c5c0' '#b5c5c0' && cat "$WORK/sky-night.svg")
sky_want=$(printf '%s\n' '<svg><style>.c2n-sky-day { display: none; }</style>' '<g class="c2n-sky-day"><rect fill="#0e1a21"/></g>' \
  '<g class="c2n-sky-night"><g><rect fill="#b5c5c0"/></g><rect fill="#c7a95a"/></g>' '<rect fill="#0e1a21"/></svg>')
sky_short=$(night_sky '#b5c5c0' '#fff' || true)
sky_upper=$(night_sky '#B5C5C0' '#b5c5c0' || true)
sky_named=$(night_sky '#b5c5c0' 'red' || true)
sky_function=$(night_sky '#b5c5c0' 'rgb(1, 2, 3)' || true)
printf '%s\n' '<svg><g class="c2-sky-day"><rect fill="#b5c5c0"/></g></svg>' > "$WORK/one-sky.svg"
sky_one=$("$PY" -B "$PWD/assets/night.py" "$WORK/one-sky.svg" "$WORK/one-sky-night.svg" 2>&1 || true)
printf '%s\n' '<svg><style>.c2-sky-night { display: none; }</style><g class="c2-sky-night"><rect fill="#b5c5c0"/></g></svg>' > "$WORK/one-sky.svg"
sky_other=$("$PY" -B "$PWD/assets/night.py" "$WORK/one-sky.svg" "$WORK/one-sky-night.svg" 2>&1 || true)
hex_fix="is no six-digit lowercase hex; write each color as #rrggbb"
if [ "$sky_ok" = "$sky_want" ] && grep -qF "#fff $hex_fix" <<<"$sky_short" && grep -qF "#B5C5C0 $hex_fix" <<<"$sky_upper" \
  && grep -qF "fill red $hex_fix" <<<"$sky_named" && grep -qF "fill rgb(1, 2, 3) $hex_fix" <<<"$sky_function" \
  && grep -qF "1 group(s) of the day sky and 0 of the night sky; draw at least one" <<<"$sky_one" \
  && grep -qF "0 group(s) of the day sky and 1 of the night sky" <<<"$sky_other"; then
  pass "night.py keeps the night sky's colors as written and maps the rest, swaps the rule that hides a sky, and refuses a short, an uppercase, a named or a functional color, inside the night sky too, and a scene with one sky's mark only"
else
  fail "night.py on small scenes: $sky_ok / $sky_short / $sky_upper / $sky_named / $sky_function / $sky_one / $sky_other"
fi
# The onboarding page's header carries the two marks, the day one and then the night one, each its logo file line for
# line. The board's pages read the two files themselves (lem_board_pages.marks).
marks=()
HANDOVER=$PWD/skills/lem/assets/handover.html
sed -n '/^<!-- lem-mark:/,/^<!-- \/lem-mark -->/p' "$HANDOVER" | sed '1d;$d' | cmp -s - "$PWD/assets/lem-mark.svg" || marks+=("the day mark")
sed -n '/^<!-- lem-mark-night:/,/^<!-- \/lem-mark-night -->/p' "$HANDOVER" | sed '1d;$d' | cmp -s - "$PWD/assets/lem-mark-night.svg" || marks+=("the night mark")
[ "$(grep -n '^<!-- lem-mark' "$HANDOVER" | head -2 | cut -d' ' -f2 | tr '\n' ' ')" = "lem-mark: lem-mark-night: " ] || marks+=("the day mark is not first")
if [ "${#marks[@]}" -eq 0 ]; then
  pass "the header of the onboarding page carries the day mark and then the night mark, each the logo's own file, line for line"
else
  fail "the marks inside the pages differ from assets/lem-mark.svg and assets/lem-mark-night.svg (copy each file between its two comments again): ${marks[*]}"
fi
# Every page of Lem has one look: the pattern of the onboarding's page links the shared stylesheet and its palette's
# script and brings no style of its own, the board's own stylesheet holds no color of Lem's, and no page takes a color
# of agterm's theme.
PATTERN=$PWD/skills/lem/assets/handover.html
if [ "$(grep -c '<link rel="stylesheet" href="lem.css">' "$PATTERN")" = 1 ] && [ "$(grep -c '<script src="lem.js"></script>' "$PATTERN")" = 1 ] \
  && ! grep -q '<style\| style="' "$PATTERN" && grep -q '^\.doc \.box {' "$PWD/skills/lem/assets/lem.css" && grep -q -- '--you: #' "$PWD/skills/lem/assets/lem.css" \
  && ! grep -q -- '--you: #' "$PWD/skills/lem/assets/board.css" && ! grep -q -- '--agterm-' "$PWD/skills/lem/assets/lem.css" "$PWD/skills/lem/assets/board.css" "$PATTERN"; then
  pass "the onboarding's page pattern links one stylesheet, which alone holds Lem's colors, and one script for its palette, and brings no style of its own; the board's stylesheet holds none of those colors, and no page reads agterm's colors"
else
  fail "the pattern of the onboarding's page, the shared stylesheet and its script"
fi

finish
