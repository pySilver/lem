#!/usr/bin/env bash
# Lem's project settings, offline: project.py resolves where a repository keeps what the skill reads.
# With no settings file it answers from Lem's own places; what Lem reads beside the settings has one
# place each and no setting, and a settings file that still names one, or another key that is gone,
# is refused once with every line to delete; a settings file with an unknown key, a wrong value or a
# path that leaves the repository is refused, and so is a list of careful paths; a worktree reads
# the main checkout's flow table. Then the task state and the event log, the rule picker, a task's criteria and the check that
# each one's tests fail on the base commit, and the board, which reads them all.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

NEW=$WORK/new
git init -q -b main "$NEW"
out=$(project --repo "$NEW" show)
if [ "$(field 'd["settings"]' <<<"$out")" = "None" ] && [ "$(field 'd["places"]["rules"]["path"]' <<<"$out")" = "$NEW/.claude/rules" ] \
  && [ "$(field 'd["branch"]["land"]' <<<"$out")" = "owner" ] && [ "$(field 'sorted(d["paths"])' <<<"$out")" = "['plan_file', 'plans']" ]; then
  pass "with no settings file, show answers from Lem's own places, the paths are the plans folder and the plan's name, and the owner lands"
else
  fail "defaults: $out"
fi
if [ "$(status_of project --repo "$NEW" init)" = 1 ]; then pass "init refuses a checkout whose base branch it cannot tell"; else fail "init without a base"; fi
project --repo "$NEW" init --base main --reviewer codex >/dev/null
# The template names every key show prints under [checks], each with its line in the file init writes.
shown_keys=$(project --repo "$NEW" show | field 'sorted(d["checks"])')
template_keys=$("$PY" -I -c 'import sys, tomllib; print(sorted(tomllib.load(open(sys.argv[1], "rb"))["checks"]))' "$NEW/.lem/project.toml")
if [ "$shown_keys" = "$template_keys" ] && grep -qxF 'bar = []' "$NEW/.lem/project.toml"; then
  pass "the settings init writes name every key show prints under [checks], bar among them"
else
  fail "the [checks] keys of the template: $template_keys, of show: $shown_keys"
fi
out=$(project --repo "$NEW" show)
if [ "$(field 'd["branch"]["base"]' <<<"$out")" = "main" ] && [ "$(field 'd["places"]["personas"]["path"]' <<<"$out")" = "$NEW/.lem/personas" ] \
  && [ "$(field '(d["seats"]["reviewer"]["agent"], d["seats"]["reviewer"]["model"])' <<<"$out")" = "('codex', None)" ] \
  && [ "$(cat "$NEW/.lem/.gitignore")" = "$(printf 'project.local.toml\nstate/')" ] && [ "$(field 'd["local"]' <<<"$out")" = "{'file': None, 'overrides': []}" ]; then
  pass "init in a new project writes Lem's own places, the given base, the reviewer's agent, and ignore rules for the machine's own settings and for Lem's state"
else
  fail "init in a new project: $out"
fi
if [ "$(status_of project --repo "$NEW" init --base main)" = 1 ]; then pass "init refuses a settings file that already exists"; else fail "second init"; fi

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
if [ "$places" = "{'profile': ('.lem/profile.md', False), 'personas': ('.lem/personas', False), 'lessons': ('.lem/lessons.md', False), 'worktrees': ('.lem/worktrees', False), 'rules': ('.claude/rules', True), 'review': ('.revmux', True), 'backlog': ('docs/backlog', False), 'rulings': ('docs/rulings', False)}" ] \
  && [ "$answered" = " .lem/profile.md .lem/personas .lem/lessons.md .lem/worktrees .claude/rules .revmux docs/backlog docs/rulings docs/plans" ] \
  && ! grep -qE '^(profile|personas|lessons|worktrees|styleguide|review|backlog|rulings) = ' "$OLD/.lem/project.toml" && [ -d "$OLD/.personas/cast" ] \
  && [ "$(status_of project --repo "$OLD" init --base master --existing link)" = 2 ]; then
  pass "init over another tool's cast and profile links nothing and moves nothing; each place is Lem's one place, show says whether it exists, and path answers for each name"
else
  fail "init over another tool's folders: $places /$answered"
fi
if [ "$(project --repo "$OLD/docs" path plans)" = "$OLD/docs/plans" ]; then pass "path prints one absolute path, from any directory of the checkout"; else fail "path plans"; fi
if [ "$(status_of project --repo "$OLD" path plan)" = 1 ] && [ "$(status_of project --repo "$OLD" path styleguide)" = 1 ]; then pass "an unknown path name is refused, the style guide's older name among them"; else fail "unknown path name"; fi

settings() { printf '%s\n' "$@" > "$OLD/.lem/project.toml"; }
settings '[branch]' 'base = "master"' 'lands = "agent"'
err=$(project --repo "$OLD" show 2>&1 || true)
if [ "$(status_of project --repo "$OLD" show)" = 1 ] && grep -q "did you mean 'land'" <<<"$err"; then pass "an unknown key is refused with the nearest valid one"; else fail "unknown key: $err"; fi
settings '[branch]' 'base = "master"' 'land = "robot"'
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "a land value other than owner or agent is refused"; else fail "land value"; fi
settings '[paths]' 'plans = "../elsewhere"'
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "a path that leaves the repository is refused"; else fail "path outside"; fi
settings '[checks]' 'commands = "pytest"'
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "gate commands that are not a list are refused"; else fail "gate type"; fi
# The tracker: no table means no tracker; a table names its kind, its server, its team and who moves a ticket.
settings '[branch]' 'base = "master"'
none=$(project --repo "$OLD" show | field 'd["tracker"]')
settings '[tracker]' 'kind = "linear"' 'server = "linear"' 'workspace = "acme"' 'team = "MBZ"' 'moves = "lem"' 'started = "In Progress"' 'landed = "Done"'
full=$(project --repo "$OLD" show | field '(d["tracker"]["workspace"], d["tracker"]["team"], d["tracker"]["moves"], d["tracker"]["started"], d["tracker"]["landed"])')
settings '[tracker]' 'kind = "linear"' 'server = "linear"' 'workspace = "acme"' 'team = "MBZ"' 'moves = "tracker"'
auto=$(project --repo "$OLD" show | field '(d["tracker"]["moves"], d["tracker"]["started"])')
if [ "$none" = None ] && [ "$full" = "('acme', 'MBZ', 'lem', 'In Progress', 'Done')" ] && [ "$auto" = "('tracker', None)" ]; then
  pass "a project has no tracker unless its settings name one, with who moves a ticket and, when Lem does, the two status names"
else
  fail "tracker settings: $none / $full / $auto"
fi
refused=""
for bad in 'kind = "jira"|server = "x"|workspace = "w"|team = "A"|moves = "lem"|started = "a"|landed = "b"' 'kind = "linear"|server = "x"|workspace = "w"|team = "A"|moves = "lem"|started = "a"' \
           'kind = "linear"|server = "x"|workspace = "w"|team = "A"|moves = "tracker"|landed = "Done"' 'kind = "linear"|workspace = "w"|team = "A"|moves = "tracker"' \
           'kind = "linear"|server = "x"|workspace = "w"|team = "A"|moves = "both"' 'kind = "linear"|server = "x"|workspace = "w"|team = ""|moves = "tracker"' \
           'kind = "linear"|server = "x"|team = "A"|moves = "tracker"' 'kind = "linear"|server = "x"|workspace = "w"|team = "A"|moves = "lem"|started = "Done"|landed = "done"'; do
  IFS='|' read -r -a lines <<<"$bad"
  settings '[tracker]' "${lines[@]}"
  if [ "$(status_of project --repo "$OLD" show)" != 1 ]; then refused="$refused [$bad]"; fi
done
if [ -z "$refused" ]; then
  pass "a tracker table is refused for an unknown kind, a missing key (the workspace too), an empty word, one status name alone, one status for both, or status names when the tracker moves the ticket"
else
  fail "tracker tables accepted:$refused"
fi
settings '[branch]' 'base = "master"' 'history = "rewrite"'
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "a history other than keep or squash is refused"; else fail "history value"; fi
# How a task is proposed: a pull request on the forge unless the settings say a merge with none.
settings '[branch]' 'base = "master"' 'propose = "push"'
err=$(project --repo "$OLD" show 2>&1 || true)
settings '[branch]' 'base = "master"' 'propose = "merge"'
merge=$(project --repo "$OLD" show | field 'd["branch"]["propose"]')
settings '[branch]' 'base = "master"'
if [ "$(status_of project --repo "$OLD" show)" = 0 ] && grep -qF "branch.propose = 'push' must be one of pull-request, merge" <<<"$err" \
  && [ "$merge" = merge ] && [ "$(project --repo "$OLD" show | field 'd["branch"]["propose"]')" = pull-request ] && grep -q '^propose = "pull-request"$' "$NEW/.lem/project.toml"; then
  pass "a task ends as a pull request unless the settings say a merge with none, and any other word is refused with the two it may be"
else
  fail "branch.propose: $err / $merge"
fi
settings '[branch]' 'base = "master"' '[checks]' 'ignores = ["docs/*"]'
if [ "$(project --repo "$OLD" show | field '(d["branch"]["history"], d["checks"]["ignores"])')" = "('keep', ['docs/*'])" ] && grep -q '^history = "keep"$' "$NEW/.lem/project.toml"; then
  pass "a branch's own commits land unless the settings say one commit, and the gate may name paths it does not read"
else
  fail "history and checks.ignores"
fi
# A seat is one string, agent/model:effort: the effort, or the model and the effort, may be left out, and then
# nothing is passed for it. show gives each seat parsed; the experts are two, in the two places of a choice's record.
settings '[seats]' 'reviewer = "codex/gpt-6.1-sol:high"' 'planner = "claude/opus"' 'experts = ["claude/fable:high", "codex"]'
seats=$(project --repo "$OLD" show | field '(d["seats"]["reviewer"], d["seats"]["planner"], [(e["agent"], e["model"], e["effort"], e["place"]) for e in d["seats"]["experts"]])' 2>&1 || true)
settings '[seats]' 'reviewer = "codex:high"'
no_model=$(project --repo "$OLD" show | field '(d["seats"]["reviewer"]["agent"], d["seats"]["reviewer"]["model"], d["seats"]["reviewer"]["effort"])' 2>&1 || true)
settings '[branch]' 'base = "master"'
unset=$(project --repo "$OLD" show | field '(d["seats"]["reviewer"], d["seats"]["planner"]["agent"], [e["seat"] for e in d["seats"]["experts"]])' 2>&1 || true)
if [ "$seats" = "({'agent': 'codex', 'model': 'gpt-6.1-sol', 'effort': 'high', 'seat': 'codex/gpt-6.1-sol:high'}, {'agent': 'claude', 'model': 'opus', 'effort': None, 'seat': 'claude/opus'}, [('claude', 'fable', 'high', 'fable'), ('codex', None, None, 'astra')])" ] \
  && [ "$no_model" = "('codex', None, 'high')" ] \
  && [ "$unset" = "({'agent': None, 'model': None, 'effort': None, 'seat': None}, None, ['claude/fable', 'codex/gpt-6-astra:high'])" ] \
  && grep -qxF 'plan_file = "YYYY-MM-DD-<slug>.md"' "$NEW/.lem/project.toml" && grep -qxF 'reviewer = "codex"' "$NEW/.lem/project.toml" \
  && grep -qxF '# experts = ["claude/fable", "codex/gpt-6-astra:high"]' "$NEW/.lem/project.toml"; then
  pass "a seat is one string agent/model:effort, shown parsed: the effort or the model may be left out, the experts are two in the record's two places, and with no seat the reviewer is unset and the experts are Fable and GPT-6 Astra"
else
  fail "seats: $seats / $no_model / $unset"
fi
refused=""
for bad in 'reviewer = ""' 'reviewer = "codex /gpt"' 'reviewer = "gemini/pro:high"' 'reviewer = "codex/"' 'reviewer = "codex/gpt:"' 'reviewer = "/gpt:high"' \
           'reviewer = 3' 'planner = "codex/gpt:high"' 'experts = ["claude/fable"]' 'experts = "claude/fable"' 'experts = ["claude/fable", "gemini"]'; do
  settings '[seats]' "$bad"
  err=$(project --repo "$OLD" show 2>&1 || true)
  if [ "$(status_of project --repo "$OLD" show)" != 1 ] || grep -q Traceback <<<"$err" || ! grep -q "agent/model:effort\|must be claude\|must be claude or codex" <<<"$err"; then refused="$refused [$bad: $err]"; fi
done
settings '[seats]' 'reviewer = "codex/gpt:"'
no_effort=$(project --repo "$OLD" show 2>&1 || true)
settings '[seats]' 'planner = "codex/gpt:high"'
planner_codex=$(project --repo "$OLD" show 2>&1 || true)
if [ -z "$refused" ] && grep -qF "names no effort after the \`:\`" <<<"$no_effort" && grep -qF "checked in Claude Code only" <<<"$planner_codex"; then
  pass "a seat is refused empty, with a space, for an agent that cannot sit there, with a / or a : and nothing after it, and the experts as anything but two seats; each refusal names the form"
else
  fail "seat refusals:$refused / $no_effort / $planner_codex"
fi
# A seat has one `:` at most: a second one is refused, by the reviewer command and in a settings file, and nothing is written.
settings '[branch]' 'base = "master"'
two_colons=$(project --repo "$OLD" reviewer claude/opus:high:max 2>&1 || true)
two_code=$(status_of project --repo "$OLD" reviewer claude/opus:high:max)
settings '[seats]' 'reviewer = "codex:high:max"'
two_in_file=$(project --repo "$OLD" show 2>&1 || true)
if [ "$two_code" = 1 ] && grep -qF "the reviewer = 'claude/opus:high:max' holds 2 \`:\`, and a seat has one at most, before the effort" <<<"$two_colons" \
  && ! grep -qsF "opus:high" "$OLD/.lem/project.local.toml" && [ "$(status_of project --repo "$OLD" show)" = 1 ] \
  && grep -qF "seats.reviewer = 'codex:high:max' holds 2 \`:\`, and a seat has one at most" <<<"$two_in_file"; then
  pass "a seat with two colons is refused, by reviewer and in a settings file, naming the colons, and reviewer writes nothing"
else
  fail "a seat with two colons: $two_colons / $two_in_file"
fi
# The tables of an older Lem are refused with the one line that says the same now.
settings '[seats.reviewer]' 'agent = "codex"' 'model = "gpt-6.1-sol"' 'effort = "xhigh"' 'plan_effort = "high"'
old_reviewer=$(project --repo "$OLD" show 2>&1 || true)
settings '[seats.planner]' 'agent = "claude"' 'model = "opus"' 'effort = "high"'
old_planner=$(project --repo "$OLD" show 2>&1 || true)
settings '[seats.reviewer]' 'model = "gpt"'
old_agentless=$(project --repo "$OLD" show 2>&1 || true)
if grep -qF "[seats.reviewer] is one line under [seats] now, \"agent/model:effort\"; the reviewer's effort for the review of a diff was used by no step" <<<"$old_reviewer" \
  && grep -qF "Write these lines in place of the [seats.reviewer] table:" <<<"$old_reviewer" \
  && [ "$(printf '%s\n' "$old_reviewer" | sed -n 2,3p)" = "$(printf '%s\n' '[seats]' 'reviewer = "codex/gpt-6.1-sol:high"')" ] \
  && grep -qxF 'planner = "claude/opus:high"' <<<"$old_planner" && ! grep -qF "[seats.reviewer]" <<<"$old_planner" && grep -qxF 'reviewer = "AGENT/gpt"' <<<"$old_agentless" \
  && [ "$(status_of project --repo "$OLD" show)" = 1 ]; then
  pass "a seat table of an older Lem is refused alone, with the line to write under [seats], its effort for the plan talk as the effort"
else
  fail "older seat tables: $old_reviewer / $old_planner / $old_agentless"
fi
# The checks: [gate] is their older name, refused with the lines to write in its place.
settings '[gate]' 'commands = ["make test", "make lint"]' 'ignores = ["docs/*"]' 'alone = ["npx playwright test"]'
gate_err=$(project --repo "$OLD" show 2>&1 || true)
if [ "$(status_of project --repo "$OLD" show)" = 1 ] && grep -qF "[gate] is called [checks] now" <<<"$gate_err" && ! grep -qF "[seats" <<<"$gate_err" \
  && grep -qF "Write these lines in place of the [gate] table:" <<<"$gate_err" && [ "$(printf '%s\n' "$gate_err" | sed -n 2,5p)" = "$(printf '%s\n' '[checks]' 'commands = ["make test", "make lint"]' 'ignores = ["docs/*"]' 'alone = ["npx playwright test"]')" ]; then
  pass "a settings file with the older [gate] table is refused with the [checks] lines to write in its place, its own values in them"
else
  fail "the older [gate] table: $gate_err"
fi
# All three older tables at once: one refusal names each, and gives the whole text to paste in their place.
settings '[gate]' 'commands = ["make test"]' '[seats]' 'experts = ["claude/fable", "codex/gpt-6-astra:high"]' \
  '[seats.reviewer]' 'agent = "codex"' 'model = "gpt-6.1-sol"' 'plan_effort = "high"' '[seats.planner]' 'agent = "claude"' 'model = "opus"' 'effort = "high"'
all_err=$(project --repo "$OLD" show 2>&1 || true)
pasted=$(printf '%s\n' "$all_err" | sed -n '2,/^planner = /p')
if [ "$(status_of project --repo "$OLD" show)" = 1 ] && [ "$(grep -c "has the form of an older Lem" <<<"$all_err")" = 1 ] \
  && grep -qF "Write these lines in place of the [gate], [seats], [seats.reviewer] and [seats.planner] tables:" <<<"$all_err" \
  && grep -qF "[gate] is called [checks] now" <<<"$all_err" && grep -qF "[seats.reviewer] and [seats.planner] are each one line under [seats] now" <<<"$all_err" \
  && [ "$(tail -n 2 <<<"$all_err")" = "$(printf '%s\n' '' 'Then commit the file on the base branch and push it: that makes the fix count for the tasks that are open, whose branches take the file from the base')" ] \
  && [ "$pasted" = "$(printf '%s\n' '[checks]' 'commands = ["make test"]' '' '[seats]' 'experts = ["claude/fable", "codex/gpt-6-astra:high"]' 'reviewer = "codex/gpt-6.1-sol:high"' 'planner = "claude/opus:high"')" ]; then
  printf '%s\n' "$pasted" > "$OLD/.lem/project.toml"
  if [ "$(project --repo "$OLD" show | field '(d["checks"]["commands"], d["seats"]["reviewer"]["seat"], d["seats"]["planner"]["seat"], len(d["seats"]["experts"]))')" = "(['make test'], 'codex/gpt-6.1-sol:high', 'claude/opus:high', 2)" ]; then
    pass "a file with [gate], [seats.reviewer] and [seats.planner] is refused once, naming all three, with the whole text to write in their place and, last, the commit and push that make it count for the open tasks; that text pasted reads"
  else
    fail "the pasted text of the older tables does not read: $pasted"
  fi
else
  fail "the three older tables at once: $all_err"
fi
# A key of [paths] that named a place is gone: refused once with the line to delete, also when it names the place of now,
# and with the move, both paths named, when it names another place. Nothing moves by itself.
settings '[branch]' 'base = "master"' '[paths]' 'personas = ".personas/cast"' 'backlog = "docs/backlog"' 'worktrees = ".claude/worktrees"' 'plans = "docs/plans"'
paths_err=$(project --repo "$OLD" show 2>&1 || true)
if [ "$(status_of project --repo "$OLD" show)" = 1 ] && grep -qF ".lem/project.toml has settings of an older Lem that are gone. Delete these lines:" <<<"$paths_err" \
  && grep -qxF -- '- delete `personas = ".personas/cast"` under [paths], and move .personas/cast to .lem/personas first, with `git mv .personas/cast .lem/personas`: .lem/personas is its one place, with no setting' <<<"$paths_err" \
  && grep -qxF -- '- delete `backlog = "docs/backlog"` under [paths]: docs/backlog is its one place, with no setting' <<<"$paths_err" \
  && grep -qxF -- '- delete `worktrees = ".claude/worktrees"` under [paths], and move each task'"'"'s worktree from .claude/worktrees to .lem/worktrees first, with `git worktree move .claude/worktrees/SLUG .lem/worktrees/SLUG`: .lem/worktrees is its one place, with no setting' <<<"$paths_err" \
  && ! grep -qF "plans" <<<"$paths_err" && [ -d "$OLD/.personas/cast" ]; then
  pass "a key of [paths] that named a place is refused once with the line to delete, and a place of another name with the move that brings it, both paths named; plans stays a setting"
else
  fail "the place keys of an older Lem: $paths_err"
fi

# A plan's file name: paths.plan_file, YYYY-MM-DD-<slug>.md by default; a plan of the older name YYYYMMDD-<slug>.md is found too.
settings '[branch]' 'base = "master"'
mkdir -p "$OLD/docs/plans"
built=$(project --repo "$OLD" plan-file gift-note --date 2026-11-17 | field '(d["name"], d["found"])')
touch "$OLD/docs/plans/20261116-gift-note.md" "$OLD/docs/plans/20261116-gift-note-extra.md" "$OLD/docs/plans/2026-11-17-other.md"
older=$(project --repo "$OLD" plan-file gift-note | field 'd["found"]')
touch "$OLD/docs/plans/2026-11-17-gift-note.md"
newer=$(project --repo "$OLD" plan-file gift-note | field 'd["found"]')
settings '[paths]' 'plan_file = "<slug>-YYYYMMDD.md"'
own=$(project --repo "$OLD" plan-file gift-note --date 2026-11-18 | field '(d["name"], d["found"])')
touch "$OLD/docs/plans/gift-note-20261118.md"
own_found=$(project --repo "$OLD" plan-file gift-note | field 'd["found"]')
plan_refused=""
for bad in 'plan_file = "YYYY-MM-DD.md"' 'plan_file = "plans/<slug>.md"' 'plan_file = "<slug>.txt"' 'plan_file = "<slug>-<date>.md"' 'plan_file = "<slug>-<slug>.md"' 'plan_file = ""' 'plan_file = "YYYY-YYYY-<slug>.md"'; do
  settings '[paths]' "$bad"
  err=$(project --repo "$OLD" show 2>&1 || true)
  if [ "$(status_of project --repo "$OLD" show)" != 1 ] || ! grep -q "paths.plan_file" <<<"$err" || grep -q Traceback <<<"$err"; then plan_refused="$plan_refused [$bad: $err]"; fi
done
settings '[branch]' 'base = "master"'
path_err=$(project --repo "$OLD" path plan_file 2>&1 || true)
rm -f "$OLD"/docs/plans/*.md
if [ "$built" = "('2026-11-17-gift-note.md', None)" ] && [ "$older" = "$OLD/docs/plans/20261116-gift-note.md" ] && [ "$newer" = "$OLD/docs/plans/2026-11-17-gift-note.md" ] \
  && [ "$own" = "('gift-note-20261118.md', '$OLD/docs/plans/20261116-gift-note.md')" ] && [ "$own_found" = "$OLD/docs/plans/gift-note-20261118.md" ] \
  && [ -z "$plan_refused" ] && grep -qF "paths.plan_file is the pattern of a plan's name, not a path" <<<"$path_err"; then
  pass "a plan's name is paths.plan_file, YYYY-MM-DD-<slug>.md by default; a plan of the older YYYYMMDD-<slug>.md is found, the newest day wins, another task's plan is never it, and a pattern with no <slug>, a folder, another ending, an unknown or a twice-named token is refused"
else
  fail "plan file names: $built / $older / $newer / $own / $own_found /$plan_refused / $path_err"
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
settings '[branch]' 'base = ""'
empty_base=$(project --repo "$OLD" show 2>&1 || true)
settings '[checks]' 'commands = ["make test", " "]'
blank_command=$(project --repo "$OLD" show 2>&1 || true)
settings '[checks]' 'setup = [""]'
blank_setup=$(project --repo "$OLD" show 2>&1 || true)
settings '[paths]' 'plans = ""'
root_backlog=$(project --repo "$OLD" show 2>&1 || true)
settings '[paths]' 'plans = "."'
root_worktrees=$(project --repo "$OLD" worktree-dir some-task 2>&1 || true)
if grep -qF "branch.base = '' names no branch" <<<"$empty_base" && grep -qF "checks.commands holds an empty command" <<<"$blank_command" \
  && grep -qF "checks.setup holds an empty command" <<<"$blank_setup" && grep -qF "paths.plans = '' names the root of the checkout" <<<"$root_backlog" \
  && grep -qF "paths.plans = '.' names the root of the checkout" <<<"$root_worktrees" && [ ! -e "$OLD/.gitignore" ] \
  && ! grep -q Traceback <<<"$empty_base$blank_command$blank_setup$root_backlog$root_worktrees"; then
  pass "an empty base branch, an empty command of the gate or its setup, and a path that is the root of the checkout are refused, each with what to write"
else
  fail "empty settings values: $empty_base / $blank_command / $blank_setup / $root_backlog / $root_worktrees / $(cat "$OLD/.gitignore" 2>&1)"
fi
settings '[branch]' 'base = "master"' 'protected = ["master"]'
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "a base branch that is also protected is refused as a contradiction"; else fail "protected base"; fi
settings '[tools]' 'annotate = "my-own-rev"'
if [ "$(project --repo "$OLD" show | field '(d["tools"]["annotate"], d["tools"]["ask"])')" = "('my-own-rev', 'lem-ask')" ]; then pass "a project names its own tool for marking up a plan, and questions keep Lem's page"; else fail "tools.annotate"; fi
settings '[tools]' 'ask = "terminal"'
if [ "$(project --repo "$OLD" show | field '(d["tools"]["annotate"], d["tools"]["ask"])')" = "('webrev', 'terminal')" ]; then pass "a project takes its questions in the terminal, or names its own tool for them"; else fail "tools.ask"; fi
settings '[tools]' 'ask = ""'
err=$(project --repo "$OLD" show 2>&1 || true)
if [ "$(status_of project --repo "$OLD" show)" = 1 ] && grep -q "tools.ask = '' must name a skill or a command in quotes, as in ask = \"lem-ask\"" <<<"$err"; then pass "an empty tool for questions is refused with the fix"; else fail "tools.ask empty: $err"; fi
settings 'not toml ['
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "a settings file that does not parse is refused"; else fail "parse error"; fi

# No list of paths says whether a change is careful: a settings file that still has one is refused,
# with the sentence to write in its place, made from its first pattern, and the line to remove.
settings '[branch]' 'base = "master"' '[flow]' 'careful = ["app/outbox/*", "*/migrations/*"]'
err=$(project --repo "$OLD" show 2>&1 || true)
settings '[branch]' 'base = "master"' '[flow]' 'careful = []'
empty=$(project --repo "$OLD" show 2>&1 || true)
if [ "$(status_of project --repo "$OLD" show)" = 1 ] && grep -qF ".lem/project.toml: flow.careful is gone" <<<"$err" \
  && grep -qF 'topics = ["what goes wrong for a person when app/outbox/* breaks, in your words"]' <<<"$err" \
  && grep -qF "then remove the line careful = [...]" <<<"$err" && grep -qF "flow.careful is gone" <<<"$empty" && ! grep -q Traceback <<<"$err$empty"; then
  pass "a settings file that still names careful paths is refused, with the sentence of flow.topics to write in their place, made from the first pattern, and the line to remove"
else
  fail "flow.careful refused: $err / $empty"
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
err=$(project --repo "$OLD" state report-dates-stay-whole build "task 3" 2>&1 || true)
if [ "$(status_of project --repo "$OLD" state report-dates-stay-whole build "task 3")" = 1 ] && grep -q "did you mean 'building'" <<<"$err" \
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
cp "$OLD/.lem/project.toml" "$WORK/settings.kept" && printf '[branch]\nbase = "caf\351"\n' > "$OLD/.lem/project.toml"
bad_settings=$(project --repo "$OLD" show 2>&1 || true)
cp "$WORK/settings.kept" "$OLD/.lem/project.toml"
mkdir -p "$OLD/.lem/state/tasks/latin-state" && printf '2026-01-01T00:00Z building: caf\351\n' > "$OLD/.lem/state/tasks/latin-state/state.md"
bad_state=$(project --repo "$OLD" tasks 2>&1 || true)
rm -r "$OLD/.lem/state/tasks/latin-state"
if grep -qF "the argument b'caf\\xe9 au lait' is not UTF-8 text" <<<"$bad_ask" && [ ! -e "$OLD/.lem/state/tasks/bad-bytes" ] \
  && grep -qF "is not UTF-8 text" <<<"$bad_line" && grep -qF "is not UTF-8 text; give it in UTF-8" <<<"$bad_field" && grep -qF "a field of the event is not UTF-8 text" <<<"$bad_field" \
  && grep -qF "$OLD/.lem/project.toml is not UTF-8 text" <<<"$bad_settings" && grep -qF "latin-state/state.md is not UTF-8 text" <<<"$bad_state" \
  && [ "$(grep -c '' "$OLD/.lem/state/events.jsonl")" = "$events_before" ] && ! grep -q Traceback <<<"$bad_ask$bad_line$bad_field$bad_settings$bad_state"; then
  pass "an argument or a file of text that is not UTF-8 is refused with the argument or the file named, and nothing is written"
else
  fail "text that is not UTF-8: $bad_ask / $bad_line / $bad_field / $bad_settings / $bad_state"
fi
# One ticket is one task, until that task is dropped or answered.
project --repo "$OLD" task-dir from-a-ticket --ticket mbz-12 --ask "Report dates are cut" >/dev/null
err=$(project --repo "$OLD" task-dir the-same-ticket --ticket MBZ-12 2>&1 || true)
if [ "$(project --repo "$OLD" tasks | field '{t["slug"]: t["ticket"] for t in d}')" = "{'from-a-ticket': 'MBZ-12', 'report-dates-stay-whole': None}" ] \
  && grep -q "the task 'from-a-ticket' already holds the ticket MBZ-12" <<<"$err" && [ ! -e "$OLD/.lem/state/tasks/the-same-ticket" ] \
  && [ "$(status_of project --repo "$OLD" task-dir bad-ticket --ticket "not a ticket")" = 1 ] && [ ! -e "$OLD/.lem/state/tasks/bad-ticket" ] \
  && [ "$(status_of project --repo "$OLD" task-dir from-a-ticket --ticket MBZ-13)" = 1 ] && [ "$(cat "$OLD/.lem/state/tasks/from-a-ticket/ticket.txt")" = MBZ-12 ] \
  && project --repo "$OLD" task-dir from-a-ticket --ticket MBZ-12 >/dev/null; then
  pass "a task keeps the ticket its ask came from: a second task for that ticket, another ticket for that task and a word that is no ticket are refused"
else
  fail "a task's ticket: $(project --repo "$OLD" tasks | field '[(t["slug"], t["ticket"]) for t in d]') / $err"
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
# A task that ended still owes its ticket the steps that are not written down. The states are written
# by hand in the script's own form, so that the event log the next checks count stays as it is.
settings '[branch]' 'base = "master"' '[tracker]' 'kind = "linear"' 'server = "linear"' 'workspace = "acme"' 'team = "MBZ"' 'moves = "lem"' 'started = "In Progress"' 'landed = "Done"'
owed() { project --repo "$OLD" tasks | field 'next(t["ticket_owed"] for t in d if t["slug"] == "from-a-ticket")'; }
printf '%s\n' '2026-01-01T00:00Z building: task 1 of 1' > "$OLD/.lem/state/tasks/from-a-ticket/state.md"
building=$(owed)
printf '%s\n' '2026-01-01T00:00Z landed: master a..b' > "$OLD/.lem/state/tasks/from-a-ticket/state.md"
landed=$(owed)
printf '%s\n' '2026-01-01T00:00Z dropped: the owner dropped it' > "$OLD/.lem/state/tasks/from-a-ticket/state.md"
dropped=$(owed)
if [ "$building" = "[]" ] && [ "$landed" = "['landed']" ] && [ "$dropped" = "['dropped']" ]; then
  pass "a landed task owes its ticket the steps that are not written down, a dropped task its drop comment, and a task that still runs owes nothing"
else
  fail "ticket_owed: $building / $landed / $dropped"
fi
err=$(project --repo "$OLD" task-dir from-a-ticket --ticket MBZ-12 2>&1 || true)
if grep -q "is dropped; a new task takes a slug of its own" <<<"$err" && project --repo "$OLD" task-dir the-same-ticket --ticket MBZ-12 >/dev/null \
  && [ "$(project --repo "$OLD" tasks | field 'next(t["ticket_steps"] for t in d if t["slug"] == "the-same-ticket")')" = "[]" ]; then
  pass "a dropped task gives its ticket back to a task with a slug of its own, which starts with no step written down"
else
  fail "the ticket of a dropped task: $err"
fi
# A task that ended with an answer gives its ticket back too, and the ticket is owed the answer's
# comment until that step is written down.
owed_by() { project --repo "$OLD" tasks | field "next(t[\"ticket_owed\"] for t in d if t[\"slug\"] == \"$1\")"; }
printf '%s\n' '2026-01-01T00:00Z answered: not a bug: the report cuts no date' > "$OLD/.lem/state/tasks/the-same-ticket/state.md"
answered=$(owed_by the-same-ticket)
again=$(project --repo "$OLD" task-dir after-the-answer --ticket MBZ-12 2>&1 || true)
project --repo "$OLD" ticket-step the-same-ticket answered >/dev/null 2>&1 || true
if [ "$answered" = "['answered']" ] && [ "$(project --repo "$OLD" tasks | field '{t["slug"]: t["ticket"] for t in d if t["ticket"]}')" = "{'after-the-answer': 'MBZ-12', 'from-a-ticket': 'MBZ-12', 'the-same-ticket': 'MBZ-12'}" ] \
  && [ "$(owed_by the-same-ticket)" = "[]" ] && [ "$(owed_by after-the-answer)" = "[]" ]; then
  pass "an answered task gives its ticket back to a task with a slug of its own, and its ticket is owed the answer's comment until the step answered is written down"
else
  fail "the ticket of an answered task: $answered / $again / $(owed_by the-same-ticket)"
fi
settings '[branch]' 'base = "master"'
rm -r "$OLD/.lem/state/tasks/from-a-ticket" "$OLD/.lem/state/tasks/the-same-ticket"
rm -rf "$OLD/.lem/state/tasks/after-the-answer"
none=$(project --repo "$OLD" tasks | field '[t["proposal"] for t in d]')
echo '{"proposed": "0123", "pr": {"number": 7, "url": "https://github.com/acme/shop/pull/7"}, "not_green": ["criterion 1 changed during the build: y is taken."]}' > "$dir/landing.json"
if [ "$none" = "[None]" ] && [ "$(project --repo "$OLD" tasks | field '[t["proposal"] for t in d]')" = "[{'pull_request': 'https://github.com/acme/shop/pull/7', 'green': False, 'not_green': ['criterion 1 changed during the build: y is taken.'], 'conflict': None}]" ]; then
  pass "tasks says what a landing proposed: the pull request's address, green or each reason it is not, and no conflict while nothing asked the forge"
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

# This machine's own settings: read from the main checkout in a worktree too, only seats and tools.
settings '[branch]' 'base = "master"' '[seats]' 'reviewer = "codex/the-usual:high"'
out=$(project --repo "$WORK/wt" reviewer claude/a-claude-model:high)
if [ "$(field '(d["reviewer"], d["local"]["overrides"])' <<<"$out")" = "({'agent': 'claude', 'model': 'a-claude-model', 'effort': 'high', 'seat': 'claude/a-claude-model:high'}, ['seats.reviewer'])" ] \
  && [ -f "$OLD/.lem/project.local.toml" ] && [ ! -e "$WORK/wt/.lem/project.local.toml" ] && grep -qxF 'reviewer = "claude/a-claude-model:high"' "$OLD/.lem/project.local.toml" \
  && [ "$(project --repo "$OLD" show | field '(d["seats"]["reviewer"]["agent"], d["seats"]["reviewer"]["model"], d["local"]["file"])')" = "('claude', 'a-claude-model', '$OLD/.lem/project.local.toml')" ]; then
  pass "reviewer AGENT/MODEL:EFFORT, run in a worktree, writes this machine's seat in the main checkout in the same form; it replaces the project's seat whole and show says so"
else
  fail "reviewer override: $out"
fi
# A value the owner wrote by hand keeps every character through a rewrite: a rocket, a quote, a backslash.
printf '%s\n' '[tools]' 'annotate = "/opt/my \"own\" rev-🚀\\x"' >> "$OLD/.lem/project.local.toml"
project --repo "$OLD" reviewer claude >/dev/null
out=$(project --repo "$OLD" reviewer default)
if [ "$(field '(d["reviewer"]["agent"], d["reviewer"]["model"], d["reviewer"]["effort"], d["local"]["overrides"])' <<<"$out")" = "('codex', 'the-usual', 'high', ['tools.annotate'])" ] \
  && [ "$(project --repo "$OLD" show | field 'd["tools"]["annotate"]')" = '/opt/my "own" rev-🚀\x' ] && ! grep -q "seats" "$OLD/.lem/project.local.toml"; then
  pass "reviewer default gives the project's reviewer back and keeps what else the machine set, character for character"
else
  fail "reviewer default: $out / $(cat "$OLD/.lem/project.local.toml")"
fi
printf '%s\n' '[checks]' 'commands = []' > "$OLD/.lem/project.local.toml"
err=$(project --repo "$OLD" show 2>&1 || true)
printf '%s\n' '[gate]' 'commands = []' > "$OLD/.lem/project.local.toml"
old_err=$(project --repo "$OLD" show 2>&1 || true)
if [ "$(status_of project --repo "$OLD" show)" = 1 ] && grep -q "\[checks\] is the project's rule" <<<"$err" && grep -qF "[gate] is called [checks] now" <<<"$old_err" \
  && [ "$(status_of project --repo "$OLD" reviewer claude)" = 1 ]; then
  pass "the machine's own file may not hold the checks or any other rule of the project, nor the checks' older table"
else
  fail "the checks in the local file: $err / $old_err"
fi
printf '%s\n' '[tools]' 'ask = "my-asker"' > "$OLD/.lem/project.local.toml"
if [ "$(project --repo "$OLD" show | field '(d["tools"]["ask"], d["tools"]["annotate"], d["local"]["overrides"])')" = "('my-asker', 'webrev', ['tools.ask'])" ]; then
  pass "one machine names its own tool for questions, and show says that the value is the machine's"
else
  fail "tools.ask in the local file: $(project --repo "$OLD" show 2>&1)"
fi
# One person may say no to the correction queue in the machine's own file, and never yes.
printf '%s\n' '[corrections]' 'collect = false' '[tools]' 'ask = "my-asker"' > "$OLD/.lem/project.local.toml"
off=$(project --repo "$OLD" show | field '(d["corrections"]["collect"], d["local"]["overrides"])')
project --repo "$OLD" reviewer claude >/dev/null && project --repo "$OLD" reviewer default >/dev/null
kept=$(grep -c '^collect = false$' "$OLD/.lem/project.local.toml")
printf '%s\n' '[corrections]' 'collect = true' > "$OLD/.lem/project.local.toml"
err=$(project --repo "$OLD" show 2>&1 || true)
if [ "$off" = "(False, ['tools.ask'])" ] && [ "$kept" = 1 ] && [ "$(status_of project --repo "$OLD" show)" = 1 ] && [ "$(status_of project --repo "$OLD" reviewer claude)" = 1 ] \
  && grep -q "It may say .collect = false." <<<"$err" && grep -q "only .lem/project.toml, which everybody reads in git, switches the queue on" <<<"$err"; then
  pass "the machine's own file may say no to the correction queue and keeps that line through a rewrite; a yes there is refused with the reason"
else
  fail "corrections in the local file: $off / $kept / $err"
fi
printf '%s\n' '[tools]' 'annotate = 42' > "$OLD/.lem/project.local.toml"
err=$(project --repo "$OLD" reviewer claude 2>&1 || true)
if [ "$(status_of project --repo "$OLD" reviewer claude)" = 1 ] && [ "$(status_of project --repo "$OLD" reviewer default)" = 1 ] \
  && grep -q "project.py: .lem/project.local.toml: tools.annotate = 42 must name" <<<"$err" && ! grep -q Traceback <<<"$err" \
  && [ "$(cat "$OLD/.lem/project.local.toml")" = "$(printf '%s\n' '[tools]' 'annotate = 42')" ]; then
  pass "a wrong value already in the machine's own file is refused with its fix, and the file is left as it was"
else
  fail "a number as the local annotate tool: $err"
fi
printf '%s\n' '[seats.reviewer]' 'agent = "codex"' > "$OLD/.lem/project.local.toml"
old_local=$(project --repo "$OLD" reviewer default 2>&1 || true)
rm "$OLD/.lem/project.local.toml"
words=$(project --repo "$OLD" reviewer codex gpt-6.1-sol high 2>&1 || true)
gemini=$(project --repo "$OLD" reviewer gemini/pro 2>&1 || true)
if [ "$(status_of project --repo "$OLD" reviewer gemini)" = 1 ] && grep -qF "reviewer takes one seat, \"agent/model:effort\", as \`reviewer codex/gpt-6.1-sol:high\`" <<<"$words" \
  && grep -qF "the agent 'gemini' must be claude or codex" <<<"$gemini" && [ "$(status_of project --repo "$OLD" reviewer codex/)" = 1 ] && [ ! -e "$OLD/.lem/project.local.toml" ] \
  && grep -qF "Write these lines in place of the [seats.reviewer] table:" <<<"$old_local" && grep -qxF 'reviewer = "codex"' <<<"$old_local" && ! grep -qF "commit the file" <<<"$old_local"; then
  pass "reviewer refuses an agent that cannot review, the older three words and a seat that does not parse, and writes nothing then; an older seat table already in the file is refused with its line"
else
  fail "reviewer refusals: $words / $gemini / $old_local"
fi
project --repo "$OLD" reviewer codex >/dev/null && project --repo "$OLD" reviewer default >/dev/null
if [ ! -e "$OLD/.lem/project.local.toml" ]; then pass "a local file with nothing left in it is removed"; else fail "empty local file stays"; fi
# One machine may name its own defender and experts too, read from the main checkout, and a rewrite of the reviewer's seat keeps them.
settings '[branch]' 'base = "master"' '[seats]' 'planner = "claude/the-usual:high"'
printf '%s\n' '[seats]' 'planner = "claude/a-local-model"' 'experts = ["claude/opus:high", "codex/gpt-6.1-sol:high"]' > "$OLD/.lem/project.local.toml"
local_seat=$(project --repo "$WORK/wt" show | field '(d["seats"]["planner"], [e["seat"] for e in d["seats"]["experts"]], d["local"]["overrides"])' 2>&1 || true)
project --repo "$OLD" reviewer codex >/dev/null 2>&1 || true
both=$(project --repo "$OLD" show | field '(d["seats"]["planner"]["model"], d["seats"]["reviewer"]["agent"], len(d["seats"]["experts"]), d["local"]["overrides"])' 2>&1 || true)
project --repo "$OLD" reviewer default >/dev/null 2>&1 || true
kept=$(project --repo "$OLD" show | field '(d["seats"]["planner"]["model"], d["local"]["overrides"])' 2>&1 || true)
printf '%s\n' '[seats]' 'planner = "codex"' > "$OLD/.lem/project.local.toml"
err=$(project --repo "$OLD" reviewer claude 2>&1 || true)
if [ "$local_seat" = "({'agent': 'claude', 'model': 'a-local-model', 'effort': None, 'seat': 'claude/a-local-model'}, ['claude/opus:high', 'codex/gpt-6.1-sol:high'], ['seats.planner', 'seats.experts'])" ] \
  && [ "$both" = "('a-local-model', 'codex', 2, ['seats.reviewer', 'seats.planner', 'seats.experts'])" ] && [ "$kept" = "('a-local-model', ['seats.planner', 'seats.experts'])" ] \
  && grep -qF "project.py: .lem/project.local.toml: seats.planner = 'codex': the agent 'codex' must be claude" <<<"$err" \
  && [ "$(cat "$OLD/.lem/project.local.toml")" = "$(printf '%s\n' '[seats]' 'planner = "codex"')" ]; then
  pass "the machine's own file may name the defender's seat and the experts, which replace the project's whole and show says so; reviewer keeps them through a rewrite, and refuses a wrong one already there, leaving the file as it was"
else
  fail "the defender's seat in the local file: $local_seat / $both / $kept / $err"
fi
rm "$OLD/.lem/project.local.toml"
# One person may say no to the naps, which spend their tokens, and name how many tasks build or land at one
# time on their machine, which is a machine's load and no guard; never yes to the naps there, and no other key.
settings '[branch]' 'base = "master"' '[flow]' 'max_tasks = 4' '[naps]' 'on = true'
printf '%s\n' '[flow]' 'max_tasks = 2' '[naps]' 'on = false' > "$OLD/.lem/project.local.toml"
machine=$(project --repo "$OLD" show 2>&1 | field '(d["flow"]["max_tasks"], d["naps"]["on"], d["local"]["overrides"])' 2>&1 || true)
in_tree=$(project --repo "$WORK/wt" show 2>&1 | field '(d["flow"]["max_tasks"], "flow.max_tasks" in d["local"]["overrides"])' 2>&1 || true)
asleep=$(project --repo "$OLD" may-nap 2>&1 | field '(d["may"], d["why"])' 2>&1 || true)
project --repo "$OLD" reviewer claude >/dev/null 2>&1 && project --repo "$OLD" reviewer default >/dev/null 2>&1 || true
rewritten=$(cat "$OLD/.lem/project.local.toml")
printf '%s\n' '[naps]' 'on = true' > "$OLD/.lem/project.local.toml"
naps_yes=$(project --repo "$OLD" show 2>&1 || true)
naps_yes_code=$(status_of project --repo "$OLD" reviewer claude)
printf '%s\n' '[naps]' 'keep_days = 3' > "$OLD/.lem/project.local.toml"
naps_key=$(project --repo "$OLD" show 2>&1 || true)
printf '%s\n' '[flow]' 'decision_wait = 1' > "$OLD/.lem/project.local.toml"
flow_key=$(project --repo "$OLD" show 2>&1 || true)
flow_key_code=$(status_of project --repo "$OLD" reviewer claude)
printf '%s\n' '[flow]' 'max_tasks = 0' > "$OLD/.lem/project.local.toml"
flow_bad=$(project --repo "$OLD" show 2>&1 || true)
rm "$OLD/.lem/project.local.toml"
alone=$(project --repo "$OLD" show 2>&1 | field '(d["flow"]["max_tasks"], d["naps"]["on"], d["local"]["overrides"])' 2>&1 || true)
if [ "$machine" = "(2, False, ['flow.max_tasks', 'naps.on'])" ] && [ "$in_tree" = "(2, True)" ] && [ "$asleep" = "(False, 'the naps are off on this machine (naps.on = false in .lem/project.local.toml)')" ] \
  && [ "$rewritten" = "$(printf '%s\n' "# This machine's own settings for Lem. Not committed; \`lem project reviewer\` writes the seat." '' '[flow]' 'max_tasks = 2' '' '[naps]' 'on = false')" ] \
  && grep -qF ".lem/project.local.toml: naps.on = True is not for this file. It may say \`on = false\`" <<<"$naps_yes" \
  && grep -qF "only .lem/project.toml, which everybody reads in git, switches the naps on" <<<"$naps_yes" && [ "$naps_yes_code" = 1 ] \
  && grep -qF ".lem/project.local.toml: naps.keep_days is the project's and belongs in .lem/project.toml" <<<"$naps_key" \
  && grep -qF ".lem/project.local.toml: flow.decision_wait is the project's rule and belongs in .lem/project.toml; this file may hold only max_tasks under [flow]" <<<"$flow_key" \
  && [ "$flow_key_code" = 1 ] && grep -qF ".lem/project.local.toml: flow.max_tasks = 0 must be a whole number, 1 or more" <<<"$flow_bad" \
  && [ "$alone" = "(4, True, [])" ]; then
  pass "the machine's own file may say no to the naps and name its own flow.max_tasks, also for a task's worktree, show and may-nap say that the value is the machine's, and a rewrite keeps both; a yes to the naps, another key of [naps] or [flow] and a wrong limit there are refused with the reason"
else
  fail "the naps and the limit in the local file: $machine / $in_tree / $asleep / $rewritten / $naps_yes / $naps_key / $flow_key / $flow_bad / $alone"
fi
settings '[branch]' 'base = "master"'
# A checkout whose folder name holds a line break is still one path.
ODD="$WORK/odd
name"
git init -q -b main "$ODD"
commit "$ODD" start
project --repo "$ODD" init --base main --reviewer codex >/dev/null
project --repo "$ODD" reviewer claude >/dev/null
git -C "$ODD" worktree add -q "$WORK/odd-wt" -b feat/odd
if [ "$(project --repo "$WORK/odd-wt" show | field '(d["seats"]["reviewer"]["agent"], d["main"] == d["local"]["file"][:len(d["main"])], "\n" in d["main"])')" = "('claude', True, True)" ]; then
  pass "the main checkout is found whole when its path holds a line break, so a worktree reads its local settings"
else
  fail "a checkout path with a line break: $(project --repo "$WORK/odd-wt" show | field '(d["main"], d["local"])')"
fi

# The event log: every state block is an event the board can load, with the worktree's newest commit.
events() { "$PY" -c 'import json, sys; d = [json.loads(line) for line in open(sys.argv[1])]; print(eval(sys.argv[2], {"d": d}))' "$OLD/.lem/state/events.jsonl" "$1"; }
if [ "$(events '[(e["event"], e["task"], e["status"], e["text"], e["lines"]) for e in d[:2]]')" = "[('task.state', 'report-dates-stay-whole', 'queued', 'waits for a free place', []), ('task.state', 'report-dates-stay-whole', 'building', 'task 2 of 3', ['next: the report'])]" ] \
  && [ "$(events 'len(d)')" = 2 ] && [ "$(events 'd[1]["ask"], d[1]["limit"], "head" in d[1]')" = "('Keep report dates whole.', 4, False)" ] \
  && [ "$(sed -n 2p "$OLD/.lem/state/events.js")" = "lemEvent($(sed -n 2p "$OLD/.lem/state/events.jsonl"));" ]; then
  pass "each state block is one event with the ask and the limit, a refused one is none, and the board's copy holds the same record"
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
# A plan talk's record counts the repairs at the cause and the layers over a cited decision, and
# the decisions two questions named; `tasks` gives each task its newest talk, which Lem and a
# builder read before the build of a careful or large plan.
talk() { project --repo "$OLD" log with-a-worktree plan.talk reviewer=codex turns:=6 questions:=3 settled:=2 open:=1 design:=1 unargued:=0 "$@" 2>&1 || true; }
before=$(grep -c '' "$OLD/.lem/state/events.jsonl")
untold=$(talk repaired:=2)
layered=$(talk repaired:=2 root:=1 layer:=2 shared:=0)
typed=$(talk repaired:=2 root:=1 layer=1 shared:=0)
none_yet=$(project --repo "$OLD" tasks | field '[t["talk"] for t in d if t["slug"] == "with-a-worktree"]' 2>&1 || true)
after_refusals=$(grep -c '' "$OLD/.lem/state/events.jsonl")
# more decisions two questions named than design choices breaks a rule of the talk, not a count: the record is taken
unshared=$(talk repaired:=2 root:=1 layer:=1 shared:=2)
talk repaired:=1 root:=0 layer:=1 shared:=0 >/dev/null
written=$(talk repaired:=2 root:=1 layer:=1 shared:=1)
told=$(project --repo "$OLD" tasks | field '[(t["slug"], t["talk"] and (t["talk"]["root"], t["talk"]["layer"], t["talk"]["shared"], bool(t["talk"]["ts"]))) for t in d if t["slug"] in ("with-a-worktree", "report-dates-stay-whole")]' 2>&1 || true)
if grep -qF "and nothing else; this one has design, open, questions, repaired, reviewer, settled, turns, unargued" <<<"$untold" \
  && grep -qF "root and layer add up to at most repaired" <<<"$layered" && [ "$(field '(d["shared"], d["design"], d["bound"])' <<<"$unshared")" = "(2, 1, 14)" ] \
  && grep -qF "each N is a whole number" <<<"$typed" && [ "$none_yet" = "[None]" ] && [ "$after_refusals" = "$before" ] \
  && [ "$(field '(d["root"], d["layer"], d["shared"])' <<<"$written")" = "(1, 1, 1)" ] \
  && [ "$told" = "[('report-dates-stay-whole', None), ('with-a-worktree', (1, 1, 1, True))]" ]; then
  pass "a plan talk's record names its repairs at the cause, its layers over a cited decision and its decisions two questions named: root and layer add up to at most repaired, a record with more decisions two questions named than design choices is taken with its bound, and a refused record writes nothing; tasks gives each task its newest talk, or none"
else
  fail "the talk's new counts: $untold / $layered / $unshared / $typed / $none_yet / $written / $told"
fi
project --repo "$OLD" state with-a-worktree dropped "the test is over" >/dev/null

# The limit on tasks that build at one time.
if [ "$(project --repo "$OLD" show | field 'd["flow"]["max_tasks"]')" = 4 ] && grep -q '^max_tasks = 4$' "$NEW/.lem/project.toml"; then
  pass "four tasks build at one time unless the settings say otherwise, and init writes that number where the owner sees it"
else
  fail "max_tasks default"
fi
settings '[branch]' 'base = "master"' '[flow]' 'topics = ["a price a customer pays", "data that cannot be rebuilt"]'
if [ "$(project --repo "$OLD" show | field '(d["flow"]["topics"], sorted(d["flow"]))')" = "(['a price a customer pays', 'data that cannot be rebuilt'], ['decision_wait', 'max_tasks', 'topics', 'watch_seconds'])" ] \
  && ! grep -q '^careful' "$NEW/.lem/project.toml" && grep -q '^topics = \[\]$' "$NEW/.lem/project.toml"; then
  pass "a project names what must never go wrong as sentences in the owner's words, and init writes no list of paths beside them"
else
  fail "flow.topics: $(project --repo "$OLD" show 2>&1)"
fi
# The table that says what must never go wrong is the main checkout's: a task's branch that empties
# its topics or shortens the owner's wait reads them as the main checkout has them.
FLOW=$WORK/flow
git init -q -b main "$FLOW" && ident "$FLOW"
project --repo "$FLOW" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' '[flow]' 'topics = ["a customer is charged the wrong price"]' 'decision_wait = 15' > "$FLOW/.lem/project.toml"
git -C "$FLOW" add -A && git -C "$FLOW" commit -q -m "chore: start"
git -C "$FLOW" worktree add -q "$WORK/flow-tree" -b feat/lift main
printf '%s\n' '[branch]' 'base = "main"' '[flow]' 'topics = []' 'decision_wait = 1' > "$WORK/flow-tree/.lem/project.toml"
git -C "$WORK/flow-tree" commit -q -am "chore: no topics"
lifted=$(project --repo "$WORK/flow-tree" show | field '(d["flow"]["topics"], d["flow"]["decision_wait"], d["root"] == d["main"])')
if [ "$lifted" = "(['a customer is charged the wrong price'], 15, False)" ]; then
  pass "in a task's worktree the flow table is the main checkout's: a branch that empties its own topics or shortens the wait changes nothing a lead or the landing reads"
else
  fail "the flow table of a worktree: $lifted"
fi
# While the main checkout is on the base branch, its working tree's settings count, an edit nobody committed yet too:
# the owner's own edit is his act. A colleague's branch checked out there (`gh pr checkout 57`) changes nothing a landing,
# a lead or a review reads: the settings are then read as the base branch's newest commit has them, and the line on
# stderr says so. The settings of an onboarding, on no commit of the base yet, are read from the working tree.
git -C "$FLOW" switch -q -c feat/colleague
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[flow]' 'topics = []' 'decision_wait = 1' > "$FLOW/.lem/project.toml"
git -C "$FLOW" commit -q -am "chore: the colleague's settings"
checked_out=$(project --repo "$FLOW" show 2>"$WORK/flow.err" | field '(d["branch"]["land"], d["flow"]["topics"], d["flow"]["decision_wait"], d["settings_from"][:5])')
checked_err=$(cat "$WORK/flow.err")
from_tree=$(project --repo "$WORK/flow-tree" show 2>/dev/null | field '(d["flow"]["topics"], d["flow"]["decision_wait"])')
git -C "$FLOW" switch -q main
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[flow]' 'topics = []' > "$FLOW/.lem/project.toml"
edited=$(project --repo "$FLOW" show 2>"$WORK/flow.err" | field '(d["branch"]["land"], d["flow"]["topics"], d["settings_from"])')
from_tree_edited=$(project --repo "$WORK/flow-tree" show 2>/dev/null | field 'd["flow"]["topics"]')
edited_err=$(cat "$WORK/flow.err")
git -C "$FLOW" commit -q -am "chore: the owner's new settings"
committed=$(project --repo "$FLOW" show 2>"$WORK/flow.err" | field '(d["branch"]["land"], d["flow"]["topics"])')
committed_err=$(cat "$WORK/flow.err")
ONB=$WORK/onboarding
git init -q -b main "$ONB" && ident "$ONB" && commit "$ONB" "chore: start"
git -C "$ONB" switch -q -c chore/lem-setup && project --repo "$ONB" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' > "$ONB/.lem/project.toml"
git -C "$ONB" add -A && git -C "$ONB" commit -q -m "chore: set up Lem"
onboarding=$(project --repo "$ONB" show 2>&1 | field '(d["branch"]["land"], d["settings_from"])')
if [ "$checked_out" = "('owner', ['a customer is charged the wrong price'], 15, 'main@')" ] \
  && grep -qF "the main checkout is not on main, so Lem reads .lem/project.toml as main has it" <<<"$checked_err" \
  && [ "$from_tree" = "(['a customer is charged the wrong price'], 15)" ] \
  && [ "$edited" = "('agent', [], 'the working tree')" ] && [ -z "$edited_err" ] && [ "$from_tree_edited" = "[]" ] \
  && [ "$committed" = "('agent', [])" ] && [ -z "$committed_err" ] && [ "$onboarding" = "('agent', 'the working tree')" ]; then
  pass "while the main checkout is on the base branch its working tree's settings count, an uncommitted edit too; a colleague's branch checked out there changes nothing, the base branch's commit is read, and stderr says so; an onboarding's settings, on no commit of the base yet, are read from the working tree"
else
  fail "where the settings are read: $checked_out / $checked_err / $from_tree / $edited / $edited_err / $from_tree_edited / $committed / $committed_err / $onboarding"
fi
settings '[flow]' 'topics = "money"'
err=$(project --repo "$OLD" show 2>&1 || true)
if [ "$(status_of project --repo "$OLD" show)" = 1 ] && grep -q "flow.topics" <<<"$err" && ! grep -q Traceback <<<"$err"; then pass "danger topics that are not a list are refused"; else fail "flow.topics as a string: $err"; fi
settings '[branch]' 'base = "master"' '[flow]' 'max_tasks = 2'
project --repo "$OLD" task-dir second-task >/dev/null
out=$(project --repo "$OLD" may-start second-task)
if [ "$(field 'd["running"]' <<<"$out")" = "['report-dates-stay-whole']" ] && [ "$(field 'd["limit"]' <<<"$out")" = 2 ]; then
  pass "may-start names the tasks that build and the limit while a place is free"
else
  fail "may-start below the limit: $out"
fi
project --repo "$OLD" state second-task building "the plan" >/dev/null
err=$(project --repo "$OLD" may-start written-by-hand 2>&1 || true)
if [ "$(status_of project --repo "$OLD" may-start written-by-hand)" = 1 ] && grep -q "flow.max_tasks is 2" <<<"$err" && grep -q "queued" <<<"$err"; then
  pass "may-start refuses a new task at the limit and says to queue it"
else
  fail "may-start at the limit: $err"
fi
# A task whose next lead starts (a lead after its investigator, one started again after it stopped)
# holds its place already: at the limit it may start, and the place it holds is not counted twice.
own=$(project --repo "$OLD" may-start second-task 2>&1 || true)
unknown=$(project --repo "$OLD" may-start no-such-task 2>&1 || true)
if [ "$(field 'd["running"]' <<<"$own" 2>&1)" = "['report-dates-stay-whole']" ] && [ "$(status_of project --repo "$OLD" may-start report-dates-stay-whole)" = 0 ] \
  && grep -qF "no task 'no-such-task'" <<<"$unknown" && [ "$(status_of project --repo "$OLD" may-start)" = 2 ]; then
  pass "may-start names the task whose lead starts and does not count that task's own place, so a task at the limit starts its next lead; an unknown task and no task are refused"
else
  fail "may-start for a task that builds: $own / $unknown"
fi
project --repo "$OLD" state second-task ready "the report is written" >/dev/null
if [ "$(status_of project --repo "$OLD" may-start written-by-hand)" = 0 ]; then pass "a task that waits for its landing takes no place"; else fail "may-start after ready"; fi
project --repo "$OLD" state second-task landing "the gate runs" >/dev/null
err=$(project --repo "$OLD" may-start written-by-hand 2>&1 || true)
if [ "$(status_of project --repo "$OLD" may-start written-by-hand)" = 1 ] && grep -q "report-dates-stay-whole, second-task" <<<"$err"; then
  pass "a task whose gate runs holds a place, because a builder may repair what the gate shows"
else
  fail "may-start during a landing: $err"
fi
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
accepted=""
for bad in 0 true '"four"' 2.5; do
  settings '[flow]' "max_tasks = $bad"
  if [ "$(status_of project --repo "$OLD" show)" != 1 ]; then accepted="$accepted $bad"; fi
done
if [ -z "$accepted" ]; then pass "a limit that is not a whole number of 1 or more is refused"; else fail "max_tasks accepted:$accepted"; fi
# The watch of the open pull requests looks once a minute unless the settings say otherwise, and init writes the line.
accepted=""
for bad in 0 true '"60"' 2.5; do
  settings '[flow]' "watch_seconds = $bad"
  if [ "$(status_of project --repo "$OLD" show)" != 1 ]; then accepted="$accepted $bad"; fi
done
settings '[flow]' 'watch_seconds = 1'
short=$(project --repo "$OLD" show | field 'd["flow"]["watch_seconds"]')
settings '[branch]' 'base = "master"'
if [ -z "$accepted" ] && [ "$short" = 1 ] && [ "$(project --repo "$OLD" show | field 'd["flow"]["watch_seconds"]')" = 60 ] && grep -q '^watch_seconds = 60$' "$NEW/.lem/project.toml"; then
  pass "the watch's interval is flow.watch_seconds, 60 unless the settings say otherwise, which init writes; a value that is not a whole number of 1 or more is refused"
else
  fail "flow.watch_seconds accepted:$accepted short:$short"
fi
settings '[branch]' 'base = "master"'

# The type of a request, and a task that ends with a report and nothing to merge: `answered`.
ANS=$WORK/answered
git init -q -b main "$ANS"
project --repo "$ANS" init --base main --reviewer codex >/dev/null
"$PY" -I -c 'import re, sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(re.sub(r"(?m)^max_tasks = 4$", "max_tasks = 1", s, count=1))' "$ANS/.lem/project.toml"
ans_dir=$(project --repo "$ANS" task-dir zero-after-refund --ask "invoices show 0 after a refund")
before=$(grep -c '' "$ANS/.lem/state/events.jsonl" 2>/dev/null || echo 0)
unknown=$(project --repo "$ANS" state zero-after-refund building "a builder reproduces the bug and finds its cause" "investigation: bug" "type: defect, because the total is wrong" 2>&1 || true)
unsaid=$(project --repo "$ANS" state zero-after-refund building "a builder reproduces the bug and finds its cause" "investigation: bug" "type: fix" 2>&1 || true)
old_line=$(project --repo "$ANS" state zero-after-refund building "a builder reproduces the bug and finds its cause" "investigation: bug" "kind: bug, because the total is wrong" 2>&1 || true)
after_refusals=$(grep -c '' "$ANS/.lem/state/events.jsonl" 2>/dev/null || echo 0)
project --repo "$ANS" state zero-after-refund building "a builder reproduces the bug and finds its cause" "investigation: bug" "type: fix, because the ask says the total is wrong today" >/dev/null
project --repo "$ANS" state zero-after-refund building "the test that reproduces the bug is committed" "investigation: bug" >/dev/null
kind=$(project --repo "$ANS" tasks | field 'next(t["type"] for t in d if t["slug"] == "zero-after-refund")' 2>&1 || true)
if grep -qF "'defect' is not a type of request" <<<"$unknown" && grep -qF "feat, fix, docs, refactor, perf, test, chore, question" <<<"$unknown" \
  && grep -qF "write it as \`type: fix, because ...\`" <<<"$unsaid" && grep -qF "write it as \`type: fix, because the total is wrong\`" <<<"$old_line" \
  && grep -qF "the kind line of an older Lem" <<<"$old_line" && [ "$after_refusals" = "$before" ] \
  && [ "$kind" = "{'type': 'fix', 'why': 'the ask says the total is wrong today'}" ]; then
  pass "a state line that names the type of a request names one of the eight with its reason, a kind line of an older Lem is refused with the type line to write, and tasks gives the newest type also when a later block says nothing of it"
else
  fail "the type of a request: $unknown / $unsaid / $old_line / $before $after_refusals / $kind"
fi
# The investigation's record: a fix's call, whether the bug was reproduced and where the cause is; a question's answer.
inv() { project --repo "$ANS" log zero-after-refund investigation "$@" 2>&1 || true; }
before=$(grep -c '' "$ANS/.lem/state/events.jsonl")
asked_back=$(inv type=question call=answer "line=the refund writes a credit note" reproduced:=true)
nowhere=$(inv type=fix call=small "line=the total skips credit notes" reproduced:=true)
not_so=$(inv type=fix call=not-reproduced "line=a refund of 10 gave 90" reproduced:=true)
odd_call=$(inv type=fix call=maybe "line=x" reproduced:=false)
untyped=$(inv type=fix call=full "line=x" where=a.py:f reproduced=true)
old_form=$(inv kind=bug call=correction "line=x" where=a.py:f reproduced:=true)
after_refusals=$(grep -c '' "$ANS/.lem/state/events.jsonl")
none_yet=$(project --repo "$ANS" tasks | field 'next(t["investigation"] for t in d if t["slug"] == "zero-after-refund")' 2>&1 || true)
inv type=fix call=full "line=the invoice total adds the refund as a payment" where=billing/invoice.py:total reproduced:=true >/dev/null
found=$(project --repo "$ANS" tasks | field 'next((t["investigation"]["call"], t["investigation"]["where"], t["investigation"]["reproduced"]) for t in d if t["slug"] == "zero-after-refund")' 2>&1 || true)
if grep -qF "reproduced is a fix's" <<<"$asked_back" && grep -qF "where names the cause" <<<"$nowhere" && grep -qF "not-reproduced is a bug that was not reproduced" <<<"$not_so" \
  && grep -qF "call is small, full, not-a-bug or not-reproduced for a fix" <<<"$odd_call" && grep -qF "written with :=" <<<"$untyped" \
  && grep -qF "kind=bug|investigation is the form of an older Lem; write type=fix call=small" <<<"$old_form" \
  && [ "$after_refusals" = "$before" ] && [ "$none_yet" = "None" ] && [ "$found" = "('full', 'billing/invoice.py:total', True)" ]; then
  pass "an investigation's record names its type, its call and its one line, a fix's whether the bug was reproduced and a cause's place; a wrong one or one of an older Lem's form writes nothing, and tasks gives the newest"
else
  fail "the investigation's record: $asked_back / $nowhere / $not_so / $odd_call / $untyped / $old_form / $before $after_refusals / $none_yet / $found"
fi
# The start of each stage an agent runs has one form, so that the board draws its span from it to the event that ends it.
starts() { project --repo "$ANS" log zero-after-refund "$@" 2>&1 || true; }
before=$(grep -c '' "$ANS/.lem/state/events.jsonl")
good=$(for form in "interview.start" "scout.start" "scout" "criteria.read.start by=lem" "criteria.read.start by=lead" "investigation.start type=fix" "investigation.start type=question" \
  "builder.start job=task 2 of 3" "builder.start job=the small change" "builder.start job=the repair of a conflict with the base" "builder.start job=the repair of a failed check" "builder.start job=the fix of a review's findings"; do
  read -r -a words <<<"${form%% *}"; if [ "$form" = "${form%% *}" ]; then starts "${words[0]}" | field 'd["event"]'; else starts "${words[0]}" "${form#* }" | field 'd["event"]'; fi; done | sort -u | tr '\n' ' ')
added=$(( $(grep -c '' "$ANS/.lem/state/events.jsonl") - before ))
with_field=$(starts interview.start by=lem)
no_by=$(starts criteria.read.start)
odd_by=$(starts criteria.read.start by=owner)
odd_kind=$(starts investigation.start kind=question)
odd_job=$(starts builder.start "job=the polish pass")
task_zero=$(starts builder.start "job=task 0 of 3")
script_start=$(starts gate.start tip=abc123456)
if [ "$good" = "builder.start criteria.read.start interview.start investigation.start scout scout.start " ] && [ "$added" = 12 ] \
  && grep -qF "interview.start takes nothing" <<<"$with_field" && grep -qF "criteria.read.start takes by=lem|lead, and nothing else" <<<"$no_by" && grep -qF "by is 'owner'" <<<"$odd_by" \
  && grep -qF "investigation.start takes type=fix|question" <<<"$odd_kind" && grep -qF "builder.start takes job=" <<<"$odd_job" && grep -qF "the polish pass logs its own start" <<<"$odd_job" \
  && grep -qF "builder.start takes job=" <<<"$task_zero" && grep -qF "gate.start takes tip=TIP commands:=N" <<<"$script_start" \
  && [ "$(grep -c '' "$ANS/.lem/state/events.jsonl")" = $((before + 12)) ]; then
  pass "the start of the interview, the scout, the personas' read, an investigation and a builder's job each has one form, the scout's end too; a start with a wrong field, a job no builder has or a script's start in another form writes nothing"
else
  fail "the forms of the starts: $good / $added / $with_field / $no_by / $odd_by / $odd_kind / $odd_job / $task_zero / $script_start"
fi
# a choice the investigation asked while the task built, which nobody answered before the task ended
"$PY" -B "$PWD/skills/lem/scripts/decisions.py" --repo "$ANS" ask zero-after-refund "${CASE[@]}" --what "Keep the test" --option "keep it" --option "drop it" --recommended "keep it" \
  --why "it pins the behavior" --said "The two personas split." >/dev/null
# `answered` needs the report and a record whose call ends the task; it takes no place and keeps its slug.
no_report=$(project --repo "$ANS" state zero-after-refund answered "not a bug: a refund is a credit note" 2>&1 || true)
printf '%s\n' '# Investigation' '' 'Reproduced: yes.' > "$ans_dir/investigation.md"
goes_on=$(project --repo "$ANS" state zero-after-refund answered "not a bug: a refund is a credit note" 2>&1 || true)
inv type=fix call=not-a-bug "line=a refund is a credit note, and the invoice shows what is left to pay" where=billing/invoice.py:total reproduced:=true >/dev/null
project --repo "$ANS" state zero-after-refund answered "not a bug: the invoice shows what is left to pay" "report: investigation.md" >/dev/null 2>&1 || true
answered=$(project --repo "$ANS" tasks | field 'next((t["status"], t["investigation"]["call"]) for t in d if t["slug"] == "zero-after-refund")' 2>&1 || true)
project --repo "$ANS" task-dir other-task >/dev/null
project --repo "$ANS" state other-task building "lead: builder" "type: feat, because the ask wants a new column" >/dev/null
project --repo "$ANS" task-dir waits-for-a-place >/dev/null
places=$(project --repo "$ANS" may-start waits-for-a-place 2>&1 || true)
# with one place, the task that holds it starts its next lead: the investigator's call was a small change
itself=$(project --repo "$ANS" may-start other-task 2>&1 | field 'd["running"]' 2>&1 || true)
project --repo "$ANS" state other-task answered "the question is answered" >/dev/null 2>&1 || true
unreported=$(project --repo "$ANS" tasks | field 'next(t["status"] for t in d if t["slug"] == "other-task")')
project --repo "$ANS" state other-task dropped "the test is over" >/dev/null
free=$(project --repo "$ANS" may-start waits-for-a-place 2>&1 | field 'd["running"]' 2>&1 || true)
taken=$(project --repo "$ANS" task-dir zero-after-refund --ask "again" 2>&1 || true)
if grep -qF "investigation.md" <<<"$no_report" && grep -qF "not-a-bug or answer" <<<"$goes_on" && [ "$answered" = "('answered', 'not-a-bug')" ] \
  && grep -qF "1 tasks build or land (other-task)" <<<"$places" && [ "$itself" = "[]" ] && [ "$unreported" = "building" ] && [ "$free" = "[]" ] \
  && grep -qF "the task 'zero-after-refund' is answered; a new task takes a slug of its own" <<<"$taken"; then
  pass "a task is answered only with its investigation's report and a record whose call ends it; an answered task takes no place, and its slug stays its own"
else
  fail "the state answered: $no_report / $goes_on / $answered / $places / $unreported / $free / $taken"
fi
# A choice of an answered task waits for nobody, and the task takes no new one.
ended=$("$PY" -B "$PWD/skills/lem/scripts/decisions.py" --repo "$ANS" pending | field '(d["waiting"], [(e["task"], e["status"]) for e in d["ended"]])' 2>&1 || true)
again=$("$PY" -B "$PWD/skills/lem/scripts/decisions.py" --repo "$ANS" ask zero-after-refund "${CASE[@]}" --what "Keep the test" --option "keep it" --option "drop it" --recommended "keep it" \
  --why "it pins the behavior" --said "The two personas split." 2>&1 || true)
if [ "$ended" = "([], [('zero-after-refund', 'answered')])" ] && grep -qF "zero-after-refund is answered" <<<"$again" \
  && [ "$(grep -c '' "$ANS/.lem/state/tasks/zero-after-refund/decisions.jsonl")" = 1 ]; then
  pass "an answered task has no choice that waits: pending puts it with the tasks that ended, and a new choice of it is refused"
else
  fail "the choices of an answered task: $ended / $again"
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
got=""
for file in src/api/v1/x.ts src/x.ts x.ts README.md docs/README.md src/components/a.tsx src/components/deep/a.tsx src/components/a.css lib/a.ts lib/a.tsx tests/unit/a.test.ts tests/a.ts \
  models.py app/models.py app/models/user/x.py app/models.pyc .revmux/lenses/a.md scripts/verify.sh scripts/other.sh docs/a/x.md docs/c/x.md db/001.sql 'db/a#b.psql' api/v1.proto lib/../src/x.ts Makefile; do
  got="$got$file=$(picked "$file");"
done
want="src/api/v1/x.ts=00 01 10 11 14;src/x.ts=00 01 10 11 14;x.ts=00 01 10;README.md=00 01 12;docs/README.md=00 01;src/components/a.tsx=00 01 11 13 14;src/components/deep/a.tsx=00 01 11 14;"
want="${want}src/components/a.css=00 01 11;lib/a.ts=00 01 10 14;lib/a.tsx=00 01;tests/unit/a.test.ts=00 01 10 14;tests/a.ts=00 01 10;"
want="${want}models.py=00 01 20;app/models.py=00 01 20;app/models/user/x.py=00 01 20;app/models.pyc=00 01;.revmux/lenses/a.md=00 01 20;scripts/verify.sh=00 01 21;scripts/other.sh=00 01;"
want="${want}docs/a/x.md=00 01 20;docs/c/x.md=00 01;db/001.sql=00 01 30;db/a#b.psql=00 01 30;api/v1.proto=00 01 15;lib/../src/x.ts=00 01 10 11 14;Makefile=00 01;"
if [ "$got" = "$want" ]; then
  pass "the rule picker matches the glob forms the agent's documentation gives for paths: a star stays in one folder, two stars cross folders, braces list endings, a file with no scope covers every path, and a comment or a byte order mark in the frontmatter changes nothing"
else
  fail "the rule picker: $(tr ';' '\n' <<<"$got" | diff - <(tr ';' '\n' <<<"$want"))"
fi
out=$(project --repo "$RUL" rules src/components/a.tsx "$RUL/app/models.py")
if [ "$(field '[(r["file"].rsplit("/", 1)[1], r["scope"], r.get("covers")) for r in d["rules"] if r["scope"] != "every path"]' <<<"$out")" \
  = "[('11-under-src.md', ['src/**/*'], ['src/components/a.tsx']), ('13-one-folder.md', ['src/components/*.tsx'], ['src/components/a.tsx']), ('14-braces.md', ['src/**/*.{ts,tsx}'], ['src/components/a.tsx']), ('20-models.md', ['**/models.py'], ['app/models.py'])]" ] \
  && [ "$(field '(d["files"], d["exists"], d["folder"], d["rules"][0]["file"])' <<<"$out")" = "(['app/models.py', 'src/components/a.tsx'], True, '$RUL/.claude/rules', '$RUL/.claude/rules/00-conduct.md')" ]; then
  pass "the picker says for each rule which glob matched and which files it covers, reads rule files in subfolders and through links, and does not turn in a loop of links"
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
printf '%s\n' '---' 'paths: ["src/[!].ts"]' '---' > "$RUL/.claude/rules/40-empty.md"
code="$code $(status_of project --repo "$RUL" rules x.ts)"
printf '%s\n' '---' 'paths: ["a{b", "c}", "[", "src/**/", "d**e/*.x"]' '---' > "$RUL/.claude/rules/40-empty.md"
odd=$(project --repo "$RUL" rules 'dxe/f.x' 'a{b' 'src/x.ts' | field '[r.get("covers") for r in d["rules"] if r["file"].endswith("40-empty.md")]')
rm "$RUL/.claude/rules/40-empty.md"
if [ "$code" = "1 1 1 1" ] && grep -q "name them, or pass --range BASE..TIP" <<<"$err" && grep -q "is not inside $RUL" <<<"$outside" \
  && grep -q ".claude/rules/40-empty.md: its .paths:. names no glob" <<<"$empty" && grep -q "or take the line out so the file covers every path" <<<"$empty" \
  && grep -q "a line under .paths:. is not a list item" <<<"$shape" \
  && grep -q ".claude/rules/40-empty.md: a glob of its .paths:. does not read as a pattern" <<<"$glob" && ! grep -q Traceback <<<"$glob" && [ "$odd" = "[['a{b', 'dxe/f.x']]" ]; then
  pass "the picker refuses a call with no file, a file of another folder, and a rule whose paths name no glob, are no list or hold a pattern that does not read, each with the fix; an odd glob that reads matches as written"
else
  fail "the picker's refusals: $code / $err / $outside / $empty / $shape / $glob / $odd"
fi
# A project with no rules yet gets an empty answer, not an error. Rule files where an older Lem kept them, in
# .lem/styleguide, are refused with the move that brings them to .claude/rules: they must not go unread.
FRESH=$WORK/rules-fresh
git init -q -b main "$FRESH" && commit "$FRESH" start
project --repo "$FRESH" init --base main >/dev/null
none=$(project --repo "$FRESH" rules app/x.py | field '(d["exists"], d["rules"])')
mkdir -p "$FRESH/.lem/styleguide" && printf '%s\n' '---' 'paths:' '  - "app/**/*.py"' '---' > "$FRESH/.lem/styleguide/python.md"
older=$(project --repo "$FRESH" rules app/x.py 2>&1 || true)
older_code=$(status_of project --repo "$FRESH" rules app/x.py)
mkdir -p "$FRESH/.claude/rules"
beside=$(project --repo "$FRESH" rules app/x.py 2>&1 || true)
if [ "$none" = "(False, [])" ] && [ "$older_code" = 1 ] && grep -qF 'Move them there: `mkdir -p .claude && git mv .lem/styleguide .claude/rules`' <<<"$older" \
  && grep -qF 'Move them there: `git mv .lem/styleguide/* .claude/rules/`' <<<"$beside" && [ -f "$FRESH/.lem/styleguide/python.md" ]; then
  pass "a project with no rules gets no rule and no error, and rule files in the folder an older Lem kept them in are refused with the move to .claude/rules, which nothing makes by itself"
else
  fail "the rules of an older Lem's folder: $none / $older / $beside"
fi
if [ "$(status_of project --repo "$RUL" migrate plan)" != 0 ] && [ -d "$RUL/.claude/rules" ] && [ ! -e "$RUL/.lem/styleguide" ] \
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
plan=$stw/docs/plans/20261115-export-has-the-gift-note.md
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
  && [ "$(grep -c '"event": "task.criteria"' "$ST/.lem/state/events.jsonl")" = 1 ] && grep -q '"size": "full"' "$ST/.lem/state/events.js"; then
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
echo 'grep -q max_tasks .lem/project.toml || exit 1; echo changed >> .lem/project.toml' > "$stw/tests/config.sh"
# The helper starts by its path, so that a helper that is not there exits 127 in every shell: `sh
# FILE` with no FILE is 127 in bash and 2 in dash.
echo './tests/runner.sh' > "$stw/tests/calls.sh" && echo 'exit 0' > "$stw/tests/runner.sh" && chmod +x "$stw/tests/runner.sh"
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
  && grep -q 'criterion 3: `sh tests/runner.sh` does not start on the base commit (exit 2), so its failure there proves nothing' <<<"$unstarted" \
  && grep -q "criterion 3: 'tests' is a folder on the branch. Name each file that holds the test, one by one" <<<"$folder" \
  && grep -q "criterion 3 names no test: every criterion is held by a test at the end of a build" <<<"$bare" \
  && [ "$said" = "(True, [{'criterion': 3, 'why': 'the count of rows is the export of today, which no change here touches.'}])" ] \
  && grep -q "the worktree has changes nobody committed" <<<"$dirty" && [ "$(git -C "$stw" rev-parse HEAD)" = "$before" ] \
  && [ "$(find "$ST/.lem/worktrees" -maxdepth 1 -name '*.red-*' | grep -c '')" = 0 ]; then
  pass "a criterion is not held by a test that passes on the base commit too, that only changes a file both commits have, whose helper file is not named, or that starts a shell on a script the base commit lacks, whatever that shell's exit; a folder as a test file and a criterion with no test are refused, and one that says why it has none is listed"
else
  fail "criteria red refusals: $weak / $writes / $helper / $unstarted / $folder / $bare / $said / $dirty"
fi
# A test that needs what a fresh worktree lacks is named as such, and the settings' checks.setup makes it.
echo 'test -f .made-by-setup && sh export.sh | grep -q "1042,for Ania"' > "$stw/tests/env.sh" && git -C "$stw" add -A && git -C "$stw" commit -q -m "test: one that needs a setup" && before=$(git -C "$stw" rev-parse HEAD)
# shellcheck disable=SC2016
lacks=$(story3 '3. The export has the note, in a set-up worktree.' '   - test: `sh tests/env.sh` in `tests/env.sh`')
sed -i.bak 's|^setup = \[\]$|setup = ["touch .made-by-setup"]|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
# shellcheck disable=SC2016
made=$(story3 '3. The export has the note, in a set-up worktree.' '   - test: `sh tests/env.sh` in `tests/env.sh`' | field '(d["ok"], d["setup"], d["tests"][2]["problem"])')
sed -i.bak 's|^setup = .*$|setup = ["exit 3"]|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
broken=$(criteria red export-has-the-gift-note 2>&1 || true)
sed -i.bak 's|^setup = .*$|setup = []|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
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
sed -i.bak 's|^setup = .*$|setup = ["echo correct > .test-state"]|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
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
sed -i.bak 's|^setup = .*$|setup = ["git worktree lock ."]|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
locked=$(criteria red export-has-the-gift-note | field 'd["ok"]')
after_lock="$(git -C "$ST" worktree list | grep -c '') $(find "$ST/.lem/worktrees" -maxdepth 1 -name '*.red-*' | grep -c '' || true)"
# A worktree that cannot be removed is said beside the failure that came first, and the next run removes it.
sed -i.bak 's|^setup = .*$|setup = ["chmod 500 ..; exit 3"]|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
stuck=$(criteria red export-has-the-gift-note 2>&1 || true)
chmod 700 "$ST/.lem/worktrees"
sed -i.bak 's|^setup = .*$|setup = []|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
criteria red export-has-the-gift-note >/dev/null
after_stuck="$(git -C "$ST" worktree list | grep -c '') $(find "$ST/.lem/worktrees" -maxdepth 1 -name '*.red-*' | grep -c '' || true)"
# One check of a task at a time: while another process holds the task's lock, a second check is refused.
"$PY" -c 'import fcntl, sys, time; f = open(sys.argv[1], "w"); fcntl.flock(f, fcntl.LOCK_EX); print("held", flush=True); time.sleep(30)' "$ST/.lem/state/tasks/export-has-the-gift-note/red.lock" > "$WORK/lock.out" &
holder=$!
soon test -s "$WORK/lock.out"
second=$(criteria red export-has-the-gift-note 2>&1 || true)
kill "$holder" 2>/dev/null || true; wait "$holder" 2>/dev/null || true
# A check that is stopped ends the command it runs, and leaves no worktree.
sed -i.bak "s|^setup = .*\$|setup = [\"sleep $NAP2\"]|" "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
"$PY" -B "$CRITERIA" --repo "$ST" red export-has-the-gift-note > "$WORK/stopped.out" 2>&1 &
check=$!
napping() { pgrep -f "sleep ${NAP2/./\\.}" >/dev/null 2>&1; }
soon napping
started=$(pgrep -f "sleep ${NAP2/./\\.}" | grep -c '' || true)
kill -TERM "$check" 2>/dev/null || true; wait "$check" 2>/dev/null || true
left=$(pgrep -f "sleep ${NAP2/./\\.}" | grep -c '' || true)
after_stop="$(git -C "$ST" worktree list | grep -c '') $(find "$ST/.lem/worktrees" -maxdepth 1 -name '*.red-*' | grep -c '' || true)"
sed -i.bak 's|^setup = .*$|setup = []|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
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
# The section an older Lem wrote, `## Stories` with `Kind: feature` or `Kind: correction`, reads as its size; another word there does not.
old_kind=$(form '## Stories' '' 'Kind: feature, because an older Lem wrote it.' '' '1. One.' | field '(d["size"], d["mark"])' 2>&1 || true)
odd_size=$(form '## Acceptance criteria' '' 'Size: medium, because it is between.' '' '1. One.')
# An example of the form in a code fence is not the section, and a plan of another task whose name ends the same way is not this task's.
# shellcheck disable=SC2016
fenced=$(form '# A plan' '' '````markdown' 'An example in an example:' '```' '## Acceptance criteria' '' 'Size: small, because it is an example.' '' '1. An example.' '```' '````' '' '## Acceptance criteria' '' 'Size: full, because it is the real one.' '' '1. The real criterion.' | field '(d["size"], d["criteria"][0]["text"])')
git -C "$stw" checkout -q -- docs
printf '%s\n' '## Acceptance criteria' '' 'Size: small, because it is another task.' '' '1. Not this task.' > "$stw/docs/plans/20261116-csv-export-has-the-gift-note.md"
other=$(criteria show export-has-the-gift-note | field '(d["size"], d["plan"].rsplit("/", 1)[1])')
rm "$stw/docs/plans/20261116-csv-export-has-the-gift-note.md"
criteria record export-has-the-gift-note >/dev/null && criteria red export-has-the-gift-note >/dev/null
# shellcheck disable=SC2016
if [ "$fenced" = "('full', 'The real criterion.')" ] && [ "$other" = "('full', '20261115-export-has-the-gift-note.md')" ] \
  && [ "$old_kind" = "('full', 'feature')" ] && grep -q "20261115-export-has-the-gift-note.md:3: the section starts with \`Size: full, because ...\`" <<<"$odd_size" \
  && grep -q 'has no `## Acceptance criteria` section' <<<"$no_section" && grep -q "20261115-export-has-the-gift-note.md:3: the section starts with" <<<"$no_kind" \
  && grep -q "a small change has one criterion, and this one has 2: it is a full change" <<<"$two" && grep -q ":6: the criteria are numbered 1, 2, 3 in order" <<<"$order" \
  && [ "$(status_of criteria show no-such-task)" = 1 ]; then
  pass "a plan with no criteria section, no size, a small change of two criteria, an unknown size or a gap in the numbers is refused with the place and the fix; the Kind line of an older Lem reads as its size; a fenced example is not the section, and a plan of another task is not read"
else
  fail "the form of the criteria: $no_section / $no_kind / $two / $order / $old_kind / $odd_size"
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
  && grep -q "says .Size: full.: a full change waits for the owner's own yes" <<<"$not_one" && grep -q "approve needs --file" <<<"$no_file" \
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
aplan=$atw/docs/plans/20261116-approved-note.md
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
if grep -qF "criterion 3 of 20261116-approved-note.md, 'The note file ends with a line break.', is not among the expected criteria, which end at 2" <<<"$extra" \
  && grep -qF -- "\`--added N --now TEXT\`" <<<"$extra" && grep -qF "criterion 3 of 20261116-approved-note.md, 'The note file ends with a line break.', is not among" <<<"$red_extra"; then
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
# The command takes one change, its reason, and who made it: a choice of the build, or the lead or the personas.
neither=$(adecide criterion approved-note --added 2 --now "x" --why "w" 2>&1 || true)
both=$(adecide criterion approved-note --added 2 --now "x" --why "w" --choice 1 --by lead 2>&1 || true)
nosaid=$(adecide criterion approved-note --added 2 --now "x" --why "w" --by personas 2>&1 || true)
twoways=$(adecide criterion approved-note --changed 1 --added 2 --now "x" --why "w" --by lead 2>&1 || true)
added_was=$(adecide criterion approved-note --added 2 --now "x" --was "y" --why "w" --by lead 2>&1 || true)
nochoice=$(adecide criterion approved-note --added 2 --now "x" --why "w" --choice 9 2>&1 || true)
not_approved=$(adecide criterion export-has-the-gift-note --changed 1 --was "x" --now "y" --why "w" --by lead 2>&1 || true)
log_story=$(status_of adecide log approved-note --what x --chose y --why z --by lead --criterion 1 --was "$t1")
records=$(grep -c '"kind": "criterion"' "$ST/.lem/state/tasks/approved-note/decisions.jsonl" || true)
plain=$(criteria show export-has-the-gift-note 2>/dev/null | field '(d["approved"], d["changes"])' 2>&1 || true)
if grep -qF "criterion 1 of 20261116-approved-note.md says '$c1', and the expected criterion 1 is '$t1'" <<<"$reworded" \
  && grep -qF 'lem decisions criterion approved-note --changed N --was TEXT --now TEXT' <<<"$reworded" \
  && grep -qF "criterion 1 of 20261116-approved-note.md says '$c1'" <<<"$red_reworded" && [ "$changed_now" = "[(1, 1, 'changed')]" ] \
  && grep -qF "criterion 1 of 20261116-approved-note.md says '$c2', and the expected criterion 1 is '$c1'" <<<"$again" \
  && grep -qF "criterion 1 is '$c1' after every earlier change, and --was says '$t1'" <<<"$stale" && [ "$chained" = "[1, 1]" ] \
  && [ "$added_now" = 3 ] && [ "$gone_again" = "[('changed', 1), ('changed', 1), ('added', 3), ('removed', 3)]" ] \
  && grep -qF "20261116-approved-note.md lacks criterion 2, '$t2', which the expected criteria hold" <<<"$dropped" \
  && grep -qF "criterion 2 is '$t2' after every earlier change, and --was says 'An order with no gift note has the line 1043.'" <<<"$wrong_was" \
  && [ "$removed_now" = "('removed', 'personas', 'The merchant and the accountant both dropped it.')" ] && [ "$expected" = "['$c2']" ] \
  && grep -qF "names --choice ID, the choice of the build that led to it, or --by lead|personas when no choice did: one of the two" <<<"$neither" \
  && grep -qF "one of the two" <<<"$both" && grep -qF -- "--by personas needs --said" <<<"$nosaid" \
  && grep -qF "a criterion change is one of --changed N, --added N or --removed N" <<<"$twoways" && grep -qF -- "--added takes no --was: an added criterion had no text before" <<<"$added_was" \
  && grep -qF "no choice 9 went to the owner in approved-note" <<<"$nochoice" \
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
  && grep -qF "20261116-approved-note.md says \`Size: small\`, and the owner approved its criteria as a full change: a change of the size is the owner's only" <<<"$kind" \
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
if grep -qF "approved-note has approval 5 of its criteria already (by owner): Lem approves a small change in the owner's name only as the first contract" <<<"$over_feature" \
  && grep -qF "the size only through the owner's own approval" <<<"$over_feature" && [ "$contract" = "(5, 'owner', 'full', '$code1')" ]; then
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

# The backlog tab of the board: board.py writes the items for the page, with what each needs beside its text.
BKB=$WORK/backlog-board
git init -q -b main "$BKB" && mkdir -p "$BKB/docs/backlog" "$BKB/app" && printf 'def export_rows():\n    return []\n' > "$BKB/app/export.py"
bitem() { printf '%s\n' '---' "worth: $2" "where: $3" "added: $4" '---' "# $5" '' "$6" > "$BKB/docs/backlog/$1.md"; }
# shellcheck disable=SC2016  # the backticks are markdown in an item's title
bitem export-drops-columns yes app/export.py:export_rows 2026-11-02 'The export drops `custom` columns' 'A merchant does not find the gift note. </script><b>not markup</b>'
bitem slow-report later app/report.py:monthly 2026-10-20 'The monthly report takes nine seconds' 'It reads each order one by one.'
bitem which-currency yes app/export.py:no_such_name 2026-11-14 'Which currency rounds half up' 'Nobody decided for PLN.'
printf '%s\n' '---' 'worth: no' '---' '# A dark theme' '' 'Decided against.' > "$BKB/docs/backlog/dark-theme.md"
git -C "$BKB" add -A && git -C "$BKB" -c user.name=t -c user.email=t@t commit -q -m start
bitem new-from-a-landing maybe app/export.py 2026-11-15 'A new item' 'Not committed yet.'
: > "$BKB/docs/backlog/a b;c.md"
ln -s moved-away.md "$BKB/docs/backlog/broken-link.md" && mkdir "$BKB/docs/backlog/folder-item.md"
project --repo "$BKB" init --base main >/dev/null
# one task with a state, so that the page has an event log to read
project --repo "$BKB" task-dir a-first-task >/dev/null && project --repo "$BKB" state a-first-task building 'lead: builder' >/dev/null
"$PY" -B "$PWD/skills/lem/scripts/board.py" --repo "$BKB" --no-open >/dev/null
feed() { "$PY" -c 'import json, re, sys; d = json.loads(re.fullmatch(r"lemBacklog\((.*)\);\n", open(sys.argv[1], encoding="utf-8").read().replace("<\\/", "</"), re.S).group(1)); print(eval(sys.argv[2], {"d": d, "by": {i["slug"]: i for i in d["items"]}}))' "$BKB/.lem/state/backlog.js" "$1"; }
if [ "$(feed '(d["folder"], "judged" in d, sorted(by))')" = "('docs/backlog', False, ['a b;c', 'broken-link', 'dark-theme', 'export-drops-columns', 'folder-item', 'new-from-a-landing', 'slow-report', 'which-currency'])" ] \
  && [ "$(feed '(by["export-drops-columns"]["title"], by["export-drops-columns"]["worth"], by["export-drops-columns"]["where_problem"], by["export-drops-columns"]["state"], by["export-drops-columns"]["path"])')" = "('The export drops custom columns', 'yes', '', '', 'docs/backlog/export-drops-columns.md')" ] \
  && [ "$(feed '(by["slow-report"]["where_problem"], by["which-currency"]["where_problem"], by["dark-theme"]["worth"], by["dark-theme"]["where"])')" = "('the file is not there', 'not in the file: no_such_name', 'no', '')" ] \
  && [ "$(feed '(by["new-from-a-landing"]["worth"], by["new-from-a-landing"]["state"], by["a b;c"]["title"])')" = "('unset', 'new', 'a b;c')" ] \
  && [ "$(feed '(by["broken-link"]["state"], by["folder-item"]["state"], "cannot be read" in by["broken-link"]["body"])')" = "('unreadable', 'unreadable', True)" ] \
  && ! grep -q '</script>' "$BKB/.lem/state/backlog.js" && [ "$(feed '"</script><b>not markup</b>" in by["export-drops-columns"]["body"]')" = True ]; then
  pass "the board's backlog file has each item with its worth, whether its place in the code is still there and whether git has it; an item that cannot be read is listed as such; and no text of an item can end the script that carries it"
else
  fail "backlog.js: $(head -c 600 "$BKB/.lem/state/backlog.js")"
fi
# A backlog folder that git does not know yet: its first item is new, though git names only the folder.
FIRST=$WORK/backlog-first
git init -q -b main "$FIRST" && commit "$FIRST" start && project --repo "$FIRST" init --base main >/dev/null && mkdir -p "$FIRST/docs/backlog"
printf '%s\n' '# The first item' '' 'No frontmatter at all.' > "$FIRST/docs/backlog/first.md"
# A run that opens nothing keeps the session the board names: the page types an ask into it.
env AGTERM_SESSION_ID=LEM-SESSION AGTERM_SOCKET=/nowhere "$PY" -B "$PWD/skills/lem/scripts/board.py" --repo "$FIRST" --no-open >/dev/null
env AGTERM_SESSION_ID=A-LEAD-SESSION AGTERM_SOCKET=/nowhere "$PY" -B "$PWD/skills/lem/scripts/board.py" --repo "$FIRST" --no-open >/dev/null
env -u AGTERM_SESSION_ID -u AGT_SESSION_ID "$PY" -B "$PWD/skills/lem/scripts/board.py" --repo "$FIRST" --no-open >/dev/null
if grep -q '"state": "new"' "$FIRST/.lem/state/backlog.js" && grep -q '"title": "The first item"' "$FIRST/.lem/state/backlog.js" && grep -q '"session": "LEM-SESSION"' "$FIRST/.lem/state/meta.js"; then
  pass "the first item of a backlog folder that git does not know yet is new, and a run that opens nothing keeps the session the board named before"
else
  fail "a first backlog item, and the session after --no-open: $(cat "$FIRST/.lem/state/backlog.js" "$FIRST/.lem/state/meta.js" | head -c 500)"
fi
# The verdicts an older Lem's backlog sorting left in the state folder are no part of the board:
# the tab groups the items by their own worth, and the file stays as it was.
printf '%s\n' '{"export-drops-columns": {"verdict": "agent", "confidence": 0.86}}' > "$BKB/.lem/state/backlog-triage.json"
"$PY" -B "$PWD/skills/lem/scripts/board.py" --repo "$BKB" --no-open >/dev/null
if [ "$(feed '("judged" in d, "who" in by["export-drops-columns"], "confidence" in by["export-drops-columns"])')" = "(False, False, False)" ] \
  && [ "$(cat "$BKB/.lem/state/backlog-triage.json")" = '{"export-drops-columns": {"verdict": "agent", "confidence": 0.86}}' ]; then
  pass "the board's backlog file reads no verdict of an older sorting: each item has its own worth, and the old file stays as it is"
else
  fail "backlog.js beside an older sorting's verdicts: $(head -c 400 "$BKB/.lem/state/backlog.js")"
fi

# The board: board.py writes the page and what it reads beside the events, and the page draws them.
BOARD=$PWD/skills/lem/scripts/board.py
board() { env -u AGTERM_SESSION_ID -u AGTERM_SOCKET -u AGT_SESSION_ID -u AGT_SOCKET "$PY" -B "$BOARD" "$@"; }
# The test's settings file is not committed, so a worktree has none: the worktree run shows where
# the page goes and whose name it carries, the run in the main checkout shows the base.
out=$(board --repo "$WORK/wt" --no-open)
named=$(cat "$OLD/.lem/state/meta.js")
board --repo "$OLD" --no-open >/dev/null
if [ "$(field 'd["page"]' <<<"$out")" = "$OLD/.lem/state/board.html" ] && cmp -s "$OLD/.lem/state/board.html" "$PWD/skills/lem/assets/board.html" \
  && cmp -s "$OLD/.lem/state/lem.css" "$PWD/skills/lem/assets/lem.css" \
  && [ "$named" = 'lemMeta({"repo": "old", "base": null, "session": "", "ask": "lem-ask", "gates": 0, "alone": 0});' ] \
  && [ "$(cat "$OLD/.lem/state/meta.js")" = 'lemMeta({"repo": "old", "base": "master", "session": "", "ask": "lem-ask", "gates": 0, "alone": 0});' ]; then
  pass "board --no-open writes the page and the stylesheet it links into the shared state folder, from a worktree too, with the repository's name and its base"
else
  fail "board --no-open: $out / $named / $(cat "$OLD/.lem/state/meta.js" 2>&1)"
fi
out=$(board --repo "$OLD" --no-open --task with-a-worktree)
err=$(board --repo "$OLD" --no-open --task no-such-task 2>&1 || true)
if [ "$(field 'd["page"]' <<<"$out")" = "$OLD/.lem/state/task-with-a-worktree.html" ] && [ "$(field 'd["name"]' <<<"$out")" = "with-a-worktree board" ] \
  && [ "$(status_of board --repo "$OLD" --no-open --task no-such-task)" = 1 ] && grep -q "the tasks are: .*second-task" <<<"$err" && [ ! -e "$OLD/.lem/state/task-no-such-task.html" ]; then
  pass "a task's board is a copy named after the task, and an unknown task is refused with the names of the known ones"
else
  fail "board --task: $out / $err"
fi
if [ "$(status_of board --repo "$OLD")" = 1 ]; then pass "outside an agterm session board opens nothing and says so"; else fail "board outside agterm"; fi
board --repo "$OLD" --no-open --demo >/dev/null
board --repo "$OLD" --no-open --task with-a-worktree >/dev/null
if grep -q '"demo": true' "$OLD/.lem/state/meta.js" && [ -f "$OLD/.lem/state/demo" ]; then
  pass "board --demo marks the state folder's tasks as examples, and a later open with no flag keeps the mark"
else
  fail "board --demo: $(cat "$OLD/.lem/state/meta.js")"
fi
rm "$OLD/.lem/state/demo"
board --repo "$OLD" --no-open >/dev/null

# A board is known by the file it shows. Two repositories' Lems may be companions of one top session
# (AAA here has this repository's board, PA, and another repository's, PX, both with the old name),
# and a third Lem has its own top session (BBB). A board reloads its own and touches no other.
# agtermctl is a stand-in that prints a tree and records its calls.
FAKE=$WORK/fake
mkdir -p "$FAKE"
# shellcheck disable=SC2016  # the stand-in's own variables, expanded when it runs
printf '%s\n' '#!/bin/sh' 'echo "$*" >> "$AGT_CALLS"' 'case "$1" in tree) cat "$AGT_TREE" ;; *) echo "{\"result\": {\"id\": \"NEW\"}}" ;; esac' > "$FAKE/agtermctl"
chmod +x "$FAKE/agtermctl"
printf '%s\n' '{"result": {"tree": {"workspaces": [{"sessions": [' \
  '{"id": "AAA", "name": "lem a"}, {"id": "BBB", "name": "lem b"}, {"id": "CCC", "name": "lem c"},' \
  '{"id": "PX", "name": "Lem board", "content": "page", "parent": "AAA", "htmlOverlays": [{"file": "/elsewhere/.lem/state/board.html"}]},' \
  "{\"id\": \"PA\", \"name\": \"Lem board\", \"content\": \"page\", \"parent\": \"AAA\", \"htmlOverlays\": [{\"file\": \"$OLD/.lem/state/board.html\"}]}," \
  "{\"id\": \"PB\", \"name\": \"Lem board\", \"content\": \"page\", \"parent\": \"BBB\", \"htmlOverlays\": [{\"file\": \"$OLD/.lem/state/board.html\"}]}]}]}}}" > "$WORK/tree.json"
opened() { : > "$WORK/calls"; env PATH="$FAKE:$PATH" AGT_CALLS="$WORK/calls" AGT_TREE="$WORK/tree.json" AGTERM_SESSION_ID="$1" AGTERM_SOCKET=/none "$PY" -B "$BOARD" --repo "$OLD"; }
out=$(opened AAA)
if [ "$(field '(d["companion"], d["reloaded"], d["name"])' <<<"$out")" = "('PA', True, 'Lem board · old')" ] && grep -q "session overlay reload --target PA" "$WORK/calls" \
  && grep -q "session rename Lem board · old --target PA" "$WORK/calls" && ! grep -q "session close" "$WORK/calls" && ! grep -q "PX\|PB" "$WORK/calls"; then
  pass "a board is known by the file it shows: this repository's is reloaded and gets the repository's name, and another repository's board under the same top session is left alone"
else
  fail "board reload: $out / $(cat "$WORK/calls")"
fi
out=$(opened CCC)
if [ "$(field '(d["companion"], d["reloaded"], d["parent"])' <<<"$out")" = "('NEW', False, 'CCC')" ] && grep -q "session overlay open --html $OLD/.lem/state/board.html .* --companion --target CCC" "$WORK/calls" \
  && ! grep -q "session close" "$WORK/calls"; then
  pass "a session with no board opens one as its own page companion and closes nobody's"
else
  fail "board open: $out / $(cat "$WORK/calls")"
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
if sed -n '/^<!-- lem-mark:/,/^<!-- \/lem-mark -->/p' "$PWD/skills/lem/assets/board.html" | sed '1d;$d' | cmp -s - "$PWD/assets/lem-mark.svg"; then
  pass "the mark in the board's header is the logo's own file, line for line"
else
  fail "the mark inside board.html differs from assets/lem-mark.svg: copy the file between the two lem-mark comments again"
fi
# Every page of Lem has one look: the pattern of the onboarding's page links the board's stylesheet and brings no style of its own.
PATTERN=$PWD/skills/lem/assets/handover.html
if sed -n '/^<!-- lem-mark:/,/^<!-- \/lem-mark -->/p' "$PATTERN" | sed '1d;$d' | cmp -s - "$PWD/assets/lem-mark.svg" \
  && [ "$(grep -c '<link rel="stylesheet" href="lem.css">' "$PATTERN")" = 1 ] && [ "$(grep -c '<link rel="stylesheet" href="lem.css">' "$PWD/skills/lem/assets/board.html")" = 1 ] \
  && ! grep -q '<style\| style="' "$PATTERN" && grep -q '^\.doc \.box {' "$PWD/skills/lem/assets/lem.css" && grep -q -- '--you: #' "$PWD/skills/lem/assets/lem.css" \
  && ! grep -q -- '--you: #' "$PWD/skills/lem/assets/board.html"; then
  pass "the onboarding's page pattern and the board link one stylesheet, which alone holds Lem's colors; the pattern brings no style of its own and carries the logo's own mark"
else
  fail "the pattern of the onboarding's page and the shared stylesheet"
fi

SHOWN=$(cat <<'PY'
import sys
from html.parser import HTMLParser
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.skip = 0; self.text = []; self.title = ""; self.in_title = False
    def handle_starttag(self, tag, attrs):
        self.skip += tag in ("script", "style"); self.in_title = tag == "title" and not self.skip
    def handle_endtag(self, tag):
        self.skip -= tag in ("script", "style"); self.in_title = False
    def handle_data(self, data):
        if self.in_title and not self.title: self.title = data
        elif not self.skip: self.text.append(data)
p = P(); p.feed(open(sys.argv[1], encoding="utf-8").read())
shown = " ".join(" ".join(p.text).split())
missing = [want for want in sys.argv[2:] if not want.startswith("!") and want not in shown and want not in p.title]
missing += [f"no {want[1:]!r}" for want in sys.argv[2:] if want.startswith("!") and (want[1:] in shown or want[1:] in p.title)]
if "PROBLEM" in p.title or "does not parse" in shown: missing.append(f"no problem on the page (title {p.title!r})")
print("; ".join(missing))
sys.exit(bool(missing))
PY
)
chrome=""
for c in google-chrome chromium chromium-browser "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
  if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then chrome=$c; break; fi
done
# Chrome's temporary folders go into the work folder, which the run removes: each run of Chrome left a
# com.google.Chrome.* folder in the user's temporary folder. On macOS Chrome reads MAC_CHROMIUM_TMPDIR,
# not TMPDIR (measured on 2026-11-17); elsewhere it reads TMPDIR.
chrome_run() { mkdir -p "$WORK/chrome-tmp" && TMPDIR="$WORK/chrome-tmp" MAC_CHROMIUM_TMPDIR="$WORK/chrome-tmp" "$chrome" "$@"; }
if [ -n "$chrome" ]; then
  draw() {
    chrome_run --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" \
      --virtual-time-budget=5000 --dump-dom "file://$OLD/.lem/state/$1.html" > "$WORK/$1.dom" 2>/dev/null || true
  }
  draw board
  if [ ! -s "$WORK/board.dom" ]; then
    # A Chrome that cannot start (a sandbox that forbids it) says nothing about the page.
    printf 'SKIP the board pages: %s printed no page\n' "$chrome"
  elif why=$("$PY" -I -B -c "$SHOWN" "$WORK/board.dom" "Lem · old" "1 waits for you, 1 builds, 1 in checks and review" "Report dates stay whole" \
    "Owner lands it" "Tell Lem in its session to land it." "!Demo data" "Keep report dates whole." \
    "Task 2 of 3" "Second task" "Ready for its checks: the gate was cut off" "1 of 4" "1 proposed · 1 not green" "tasks land on master" "!Review queue"); then
    pass "the board draws each task in its lane from the events, with what waits for the merge and whether it is green"
  else
    fail "the board: missing $why"
  fi
  draw task-with-a-worktree
  if [ ! -s "$WORK/task-with-a-worktree.dom" ]; then
    printf 'SKIP the board of one task: %s printed no page\n' "$chrome"
  elif why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-with-a-worktree.dom" "With a worktree · Dropped" "fix/with-a-worktree" "fix: 0123 is a string" \
    "make test" "5 passed in 0.1s" "the test is over" "All tasks" "checks green: 1" "!checks red"); then
    pass "a task's board draws its state blocks, its newest commit and the gate's newest result, not a failure a later run repaired"
  else
    fail "a task's board: missing $why"
  fi
  board --repo "$OLD" --no-open --task owner-lands-it >/dev/null
  draw task-owner-lands-it
  if [ -s "$WORK/task-owner-lands-it.dom" ] && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-owner-lands-it.dom" "Owner lands it · Waits for the merge" "3/3" "Where you answer:" "!2/3" \
    "round 1, one read: clean, 0 must-fix, 1 should, 0 nit" "answered: codex" "Proposed: not green" "criterion 1 changed during the build: y is taken."); then
    pass "a task that waits for the merge keeps the phase and the plan tasks it reached, and its board shows its review and why it is not green"
  elif [ -s "$WORK/task-owner-lands-it.dom" ]; then
    fail "a task that waits for the merge: missing $why"
  fi
  # A closed task looked at much later: its time axis ends at its last block and has no line for now.
  mkdir -p "$WORK/aged" && cp "$OLD/.lem/state/task-with-a-worktree.html" "$OLD/.lem/state/meta.js" "$WORK/aged/"
  "$PY" -c 'import json, sys
rows = [json.loads(line) for line in open(sys.argv[1]) if line.strip()]
mine = [r for r in rows if r["task"] == "with-a-worktree"]
for i, r in enumerate(mine): r["ts"] = "2026-01-10T12:00:%02dZ" % i
open(sys.argv[2], "w").write("".join("lemEvent(%s);\n" % json.dumps(r) for r in mine))' "$OLD/.lem/state/events.jsonl" "$WORK/aged/events.js"
  chrome_run --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" \
    --virtual-time-budget=5000 --dump-dom "file://$WORK/aged/task-with-a-worktree.html" > "$WORK/aged.dom" 2>/dev/null || true
  if [ -s "$WORK/aged.dom" ] && "$PY" -c 'import re, sys
dom = open(sys.argv[1], encoding="utf-8").read()
labels = re.findall(r"<text class=\"axis\"[^>]*>([^<]*)</text>", dom)
days = {label.rsplit(" ", 1)[0] for label in labels}
sys.exit(not (len(labels) >= 2 and len(days) == 1 and all(" " in label for label in labels) and "class=\"nowline\"" not in dom))' "$WORK/aged.dom"; then
    pass "the board of a task that closed long ago draws its own interval, on its own day, with no line for now"
  elif [ -s "$WORK/aged.dom" ]; then
    fail "a closed task's time axis: $(grep -o '<text class="axis"[^>]*>[^<]*' "$WORK/aged.dom" | sed 's/.*>//' | tr '\n' '|') nowline: $(grep -c 'class="nowline"' "$WORK/aged.dom")"
  fi
  # A file that does not parse is a problem on the page, never a quiet default.
  printf 'lemMeta({"repo": \n' > "$OLD/.lem/state/meta.js"
  draw board
  if [ -s "$WORK/board.dom" ] && grep -q "<title>PROBLEM" "$WORK/board.dom" && grep -q "meta.js does not parse" "$WORK/board.dom"; then
    pass "a meta.js that does not parse is shown as a problem"
  elif [ -s "$WORK/board.dom" ]; then
    fail "a broken meta.js shows no problem: $(grep -o '<title>[^<]*' "$WORK/board.dom")"
  fi
  board --repo "$OLD" --no-open >/dev/null
  # The board of one task shows its criteria, each with its tests and what the last check gave.
  "$PY" -B "$BOARD" --repo "$ST" --task export-has-the-gift-note --no-open >/dev/null
  chrome_run --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" \
    --virtual-time-budget=5000 --dump-dom "file://$ST/.lem/state/task-export-has-the-gift-note.html" > "$WORK/criteria.dom" 2>/dev/null || true
  if [ ! -s "$WORK/criteria.dom" ]; then
    printf 'SKIP the criteria on the board: %s printed no page\n' "$chrome"
  elif why=$("$PY" -I -B -c "$SHOWN" "$WORK/criteria.dom" "Acceptance criteria" "full change, because the export gets a new column and an empty cell." \
    'A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has that text in its row.' "sh tests/gift.sh" \
    "passes on the branch, fails on the base commit (checked on " "held by its tests" "An order with no gift note has an empty cell"); then
    pass "the board of one task shows its criteria as the plan has them, each with its tests and the result of the last check"
  else
    fail "the criteria on the board: missing $why"
  fi
  # A criterion that changed after the check has no check: the old result is not shown for it.
  "$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("has that text in its row.", "has that text in the third cell of its row."))' "$stw/docs/plans/20261115-export-has-the-gift-note.md"
  criteria record export-has-the-gift-note >/dev/null && git -C "$stw" checkout -q -- docs
  chrome_run --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" \
    --virtual-time-budget=5000 --dump-dom "file://$ST/.lem/state/task-export-has-the-gift-note.html" > "$WORK/criteria-changed.dom" 2>/dev/null || true
  if [ -s "$WORK/criteria-changed.dom" ] && why=$("$PY" -I -B -c "$SHOWN" "$WORK/criteria-changed.dom" "in the third cell of its row" "not checked yet" "!held by its tests"); then
    pass "after a criterion changed, the board shows no result of the older check for any criterion"
  elif [ -s "$WORK/criteria-changed.dom" ]; then
    fail "the criteria on the board after a change: missing $why"
  fi
  # The backlog tab: drawn from backlog.js, and its one action types the item into Lem's session.
  chrome_run --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" \
    --virtual-time-budget=5000 --dump-dom "file://$BKB/.lem/state/board.html#backlog" > "$WORK/backlog.dom" 2>/dev/null || true
  if [ ! -s "$WORK/backlog.dom" ]; then
    printf 'SKIP the backlog tab: %s printed no page\n' "$chrome"
  elif why=$("$PY" -I -B -c "$SHOWN" "$WORK/backlog.dom" "Backlog · backlog-board" "8 items in docs/backlog" "2 items name a place that is gone or cannot be read" "2 cannot be read" "sorted by the worth of each item" \
    "Worth doing" "Later" "No verdict in the item" "Decided against" "The export drops custom columns" \
    "app/report.py:monthly · the file is not there" "new, not committed" "!Needs you" "!An agent can take it" "!0.86"); then
    pass "the backlog tab draws the items in groups by their worth, each with its word and its count, and shows a place that is gone"
  else
    fail "the backlog tab: missing $why"
  fi
  cat > "$BKB/.lem/state/probe.html" <<'PROBE'
<!doctype html><meta charset="utf-8"><iframe id="f" src="board.html#backlog" style="width:1280px;height:900px;border:0"></iframe><pre id="out"></pre>
<script>
const wait = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  await wait(1500);
  const d = document.getElementById('f').contentDocument, w = document.getElementById('f').contentWindow, log = {};
  const key = (code, key) => d.body.dispatchEvent(new w.KeyboardEvent('keydown', {code, key, bubbles: true}));
  const actions = () => d.querySelector('.bl-item.cur .bl-actions')?.textContent ?? '';
  const pickItem = title => { for (let i = 0; i < 16 && d.querySelector('.bl-item.cur .bl-title')?.textContent !== title; i++) key('KeyJ', 'j'); };
  const on = (node, code, key) => node.dispatchEvent(new w.KeyboardEvent('keydown', {code, key, bubbles: true}));
  pickItem('Which currency rounds half up'); key('Enter', 'Enter');
  log.noAgterm = actions();
  w.eval("globalThis.typed = []; globalThis.fg = []; globalThis.hold = null; globalThis.agterm = {request: async (cmd, o) => { if (cmd === 'tree') return {tree: {workspaces: [{sessions: [{id: 'LEM1', foreground: globalThis.fg}]}]}}; globalThis.typed.push([cmd, o]); if (globalThis.hold) await globalThis.hold; return {}; }};");
  await wait(3500);
  log.shellOnly = actions();
  w.eval("globalThis.fg = ['/usr/bin/less', '/tmp/claude']"); await wait(3500);
  key('KeyS', 's'); log.otherProgram = actions();
  w.eval("globalThis.fg = ['/usr/bin/vim', 'claude']"); await wait(3500);
  key('KeyS', 's'); log.otherProgram += ' // ' + actions();
  w.eval("globalThis.fg = ['/opt/homebrew/bin/fish', '-l', '-c', 'claude (cat brief.md)']"); await wait(3500);
  key('KeyS', 's'); log.confirm = actions(); log.focusOnStart = d.activeElement?.dataset?.blStart ?? null;
  key('Enter', 'Enter'); await wait(200); log.enterElsewhere = w.typed.length;
  const cancel = d.querySelector('[data-bl-cancel]'); cancel.focus(); on(cancel, 'Enter', 'Enter'); await wait(200); log.enterOnCancel = w.typed.length;
  cancel.click(); log.afterCancel = actions();
  // agterm is slow to answer: a second S and Start in that time must not type a second line
  w.eval("globalThis.hold = new Promise(done => { globalThis.release = done; })");
  key('KeyS', 's'); d.querySelector('[data-bl-start]').click(); await wait(200);
  key('KeyS', 's'); log.whilePending = [w.typed.length, d.querySelector('[data-bl-start]') === null, actions().startsWith('Typing into')];
  w.eval("globalThis.release(); globalThis.hold = null"); await wait(300);
  log.typed = w.typed; log.sent = actions();
  key('KeyS', 's'); key('Enter', 'Enter'); await wait(200); log.secondTry = [w.typed.length, d.querySelector('[data-bl-start]') === null];
  pickItem('a b;c'); key('KeyS', 's'); await wait(100);
  log.unsafe = actions(); log.typedAfterUnsafe = w.typed.length;
  const q = d.getElementById('bl-q'); q.value = 'gift note'; q.dispatchEvent(new w.Event('input', {bubbles: true}));
  log.filtered = [...d.querySelectorAll('.bl-title')].map(n => n.textContent);
  d.getElementById('bl-read').click(); await wait(600); log.afterRead = d.getElementById('bl-sum').textContent.startsWith('reading');
  key('KeyT', 't'); log.tasksTab = [d.getElementById('backlog').hidden, d.getElementById('lanes-section').hidden];
  document.getElementById('out').textContent = JSON.stringify(log);
})().catch(e => { document.getElementById('out').textContent = JSON.stringify({error: String(e)}); });
</script>
PROBE
  "$PY" -c 'import json, re, sys; s = open(sys.argv[1]).read(); d = json.loads(re.fullmatch(r"lemMeta\((.*)\);\n", s, re.S).group(1)); d["session"] = "LEM1"; open(sys.argv[1], "w").write("lemMeta(%s);\n" % json.dumps(d))' "$BKB/.lem/state/meta.js"
  chrome_run --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" --allow-file-access-from-files \
    --virtual-time-budget=40000 --dump-dom "file://$BKB/.lem/state/probe.html" > "$WORK/probe.dom" 2>/dev/null || true
  rm -f "$BKB/.lem/state/probe.html"
  acted=$("$PY" -c 'import html, json, re, sys
found = re.search(r"<pre id=\"out\">(.*?)</pre>", open(sys.argv[1], encoding="utf-8").read(), re.S)
d = json.loads(html.unescape(found.group(1))) if found and found.group(1) else {"error": "the probe printed nothing"}
cmd = "/lem new docs/backlog/which-currency.md"
wrong = [name for name, ok in {
    "an error": "error" not in d,
    "no agterm: the command to type, and nothing typed": "not open in this window" in d.get("noAgterm", "") and cmd in d.get("noAgterm", ""),
    "a shell and no agent: nothing typed": "No agent runs" in d.get("shellOnly", ""),
    "a pager or an editor that shows a file named claude is no agent": d.get("otherProgram", "").count("No agent runs") == 2,
    "S asks first, and the Start button has the focus": "This types" in d.get("confirm", "") and d.get("focusOnStart") == "which-currency",
    "Enter away from the button types nothing": d.get("enterElsewhere") == 0,
    "Enter on Cancel types nothing": d.get("enterOnCancel") == 0 and "Start a task" in d.get("afterCancel", ""),
    "Start types the one line into Lem": d.get("typed") == [["session.type", {"target": "LEM1", "args": {"text": cmd + "\n"}}]],
    "while agterm has not answered, the item is taken": d.get("whilePending") == [1, True, True],
    "the item says that it was sent": "Typed into" in d.get("sent", ""),
    "a sent item is not asked about or sent again": d.get("secondTry") == [1, True],
    "an unsafe file name is never typed": "is not typed into a session" in d.get("unsafe", "") and d.get("typedAfterUnsafe") == 1,
    "the filter reads the text of an item": d.get("filtered") == ["The export drops custom columns"],
    "a second read of the same file ends its note": d.get("afterRead") is False,
    "T goes back to the tasks": d.get("tasksTab") == [True, False],
}.items() if not ok]
print("; ".join(wrong) or "ok", "" if not wrong else json.dumps(d)[:900])' "$WORK/probe.dom" 2>&1 || true)
  if [ ! -s "$WORK/probe.dom" ]; then
    printf 'SKIP the keys of the backlog tab: %s printed no page\n' "$chrome"
  elif [ "$acted" = "ok " ]; then
    pass "on the backlog tab a key moves, opens and filters; S asks first and only the Start button types one line into Lem's session, one time, only where the agent runs, and never a file name with a character a shell could read"
  else
    fail "the keys of the backlog tab: $acted"
  fi
else
  printf 'SKIP the board pages: no Chrome or Chromium found\n'
fi

finish
