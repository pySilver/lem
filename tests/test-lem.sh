#!/usr/bin/env bash
# Lem's project settings, offline: project.py resolves where a repository keeps what
# the skill reads. With no settings file it answers from the skill's own layout; init points at the
# folders an older tool already reads instead of moving them; a settings file with an unknown key,
# a wrong value or a path that leaves the repository is refused; careful names the files a
# project's careful patterns match.
set -euo pipefail

cd "$(dirname "$0")/.."
PROJECT=$PWD/skills/lem/scripts/project.py
WORK=$(cd "$(mktemp -d)" && pwd -P)
trap 'rm -rf "$WORK"' EXIT
PY=$(python3 -I -c 'import sys; print(sys.executable)')
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1

fails=0
pass() { printf 'ok   %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1"; fails=$((fails + 1)); }
project() { "$PY" -B "$PROJECT" "$@"; }
status_of() { set +e; "$@" >/dev/null 2>&1; local code=$?; set -e; echo "$code"; }
field() { "$PY" -c 'import json, sys; d = json.load(sys.stdin); print(eval(sys.argv[1], {"d": d}))' "$1"; }

NEW=$WORK/new
git init -q -b main "$NEW"
out=$(project --repo "$NEW" show)
if [ "$(field 'd["settings"]' <<<"$out")" = "None" ] && [ "$(field 'd["paths"]["styleguide"]["path"]' <<<"$out")" = "$NEW/.lem/styleguide" ] \
  && [ "$(field 'd["branch"]["land"]' <<<"$out")" = "owner" ]; then
  pass "with no settings file, show answers from the skill's own layout and the owner lands"
else
  fail "defaults: $out"
fi
if [ "$(status_of project --repo "$NEW" init)" = 1 ]; then pass "init refuses a checkout whose base branch it cannot tell"; else fail "init without a base"; fi
project --repo "$NEW" init --base main --reviewer codex >/dev/null
out=$(project --repo "$NEW" show)
if [ "$(field 'd["branch"]["base"]' <<<"$out")" = "main" ] && [ "$(field 'd["paths"]["personas"]["path"]' <<<"$out")" = "$NEW/.lem/personas" ] \
  && [ "$(field '(d["seats"]["reviewer"]["agent"], d["seats"]["reviewer"]["model"])' <<<"$out")" = "('codex', None)" ] \
  && [ "$(cat "$NEW/.lem/.gitignore")" = "project.local.toml" ] && [ "$(field 'd["local"]' <<<"$out")" = "{'file': None, 'overrides': []}" ]; then
  pass "init in a new project writes the skill's own layout, the given base, the reviewer's agent, and an ignore rule for the machine's own settings"
else
  fail "init in a new project: $out"
fi
if [ "$(status_of project --repo "$NEW" init --base main)" = 1 ]; then pass "init refuses a settings file that already exists"; else fail "second init"; fi

OLD=$WORK/old
git init -q -b master "$OLD"
mkdir -p "$OLD/.claude/rules" "$OLD/.revmux" "$OLD/.personas/cast" "$OLD/docs/plans"
touch "$OLD/.personas/profile.md"
err=$(project --repo "$OLD" init --base master 2>&1 || true)
if [ "$(status_of project --repo "$OLD" init --base master)" = 1 ] && grep -q "this repository already keeps profile in .personas/profile.md, personas in .personas/cast; pass" <<<"$err" && [ ! -e "$OLD/.lem" ]; then
  pass "init refuses to choose between a cast and a profile already there and a new layout, and names them, not the rules, which are no choice"
else
  fail "init without --existing: $err"
fi
if [ "$(project --repo "$OLD" existing | field 'sorted(d)')" = "['personas', 'profile', 'styleguide']" ]; then
  pass "existing lists the settings an older tool already keeps here"
else
  fail "existing: $(project --repo "$OLD" existing)"
fi
NEWLAYOUT=$WORK/newlayout
git init -q -b master "$NEWLAYOUT"
mkdir -p "$NEWLAYOUT/.claude/rules" "$NEWLAYOUT/.personas/cast"
project --repo "$NEWLAYOUT" init --base master --existing new >/dev/null
if [ "$(project --repo "$NEWLAYOUT" path styleguide)" = "$NEWLAYOUT/.claude/rules" ] && [ "$(project --repo "$NEWLAYOUT" path personas)" = "$NEWLAYOUT/.lem/personas" ]; then
  pass "init --existing new starts the skill's own layout for the cast, and the rules an agent already loads stay the style guide"
else
  fail "init --existing new"
fi
RULESONLY=$WORK/rulesonly
git init -q -b master "$RULESONLY"
mkdir -p "$RULESONLY/.claude/rules"
if project --repo "$RULESONLY" init --base master >/dev/null && [ "$(project --repo "$RULESONLY" path styleguide)" = "$RULESONLY/.claude/rules" ]; then
  pass "a repository with a rules folder and nothing else of an older tool needs no choice: its rules are the style guide"
else
  fail "init over a rules folder alone"
fi
# A setup that stopped half way left an empty folder of the skill's own layout: the rules still are the style guide.
HALF=$WORK/halfway
git init -q -b master "$HALF"
mkdir -p "$HALF/.claude/rules" "$HALF/.lem/styleguide" "$HALF/.claude/worktrees" && echo 'Type every function.' > "$HALF/.claude/rules/python.md"
err=$(project --repo "$HALF" init --base master 2>&1 || true)
rmdir "$HALF/.claude/worktrees"
echo 'A second guide.' > "$HALF/.lem/styleguide/other.md"
both=$(project --repo "$HALF" init --base master 2>&1 || true)
code="$(status_of project --repo "$HALF" init --base master) $(status_of project --repo "$HALF" existing)"
rm "$HALF/.lem/styleguide/other.md"
if grep -q "this repository already keeps worktrees in .claude/worktrees; pass --existing" <<<"$err" && [ "$code" = "1 1" ] && [ ! -e "$HALF/.lem/project.toml" ] \
  && grep -q ".claude/rules and .lem/styleguide each hold rule files the other lacks, and the style guide is one folder; move the files of one into the other" <<<"$both" \
  && project --repo "$HALF" init --base master >/dev/null && [ "$(project --repo "$HALF" path styleguide)" = "$HALF/.claude/rules" ] \
  && [ "$(project --repo "$HALF" rules app/x.py | field '[r["file"] for r in d["rules"]]')" = "['$HALF/.claude/rules/python.md']" ]; then
  pass "an empty style guide folder of the skill's own does not hide the rules an agent loads, two folders that each hold a rule the other lacks are refused with the fix, and a worktrees folder of an older tool still asks for the choice"
else
  fail "init over a half setup: $err / $both / $code"
fi
# One set of rules by two paths is one style guide: a rules folder that is a link, and rule files linked between two folders.
ONE=$WORK/one-guide
git init -q -b master "$ONE"
mkdir -p "$ONE/.lem/styleguide" "$ONE/.claude" && echo 'Type every function.' > "$ONE/.lem/styleguide/python.md" && ln -s ../.lem/styleguide "$ONE/.claude/rules"
linked=$(project --repo "$ONE" existing | field 'd.get("styleguide")')
rm "$ONE/.claude/rules" && mkdir "$ONE/.claude/rules" && ln -s ../../.lem/styleguide/python.md "$ONE/.claude/rules/python.md" && echo 'Never dig up a deleted document.' > "$ONE/.claude/rules/conduct.md"
superset=$(project --repo "$ONE" existing | field 'd.get("styleguide")')
rm "$ONE/.claude/rules/conduct.md" && echo 'Version every route.' > "$ONE/.lem/styleguide/api.md"
subset=$(project --repo "$ONE" existing | field 'd.get("styleguide")')
if [ "$linked / $superset / $subset" = ".claude/rules / .claude/rules / None" ] && project --repo "$ONE" init --base master >/dev/null \
  && [ "$(project --repo "$ONE" path styleguide)" = "$ONE/.lem/styleguide" ]; then
  pass "two paths to one set of rule files are one style guide: the agent's folder when it holds every file, the skill's own when only that one does"
else
  fail "one set of rules by two paths: $linked / $superset / $subset"
fi
project --repo "$OLD" init --base master --existing link >/dev/null
out=$(project --repo "$OLD" show)
if [ "$(field 'd["paths"]["styleguide"]["path"]' <<<"$out")" = "$OLD/.claude/rules" ] && [ "$(field 'd["paths"]["review"]["path"]' <<<"$out")" = "$OLD/.revmux" ] \
  && [ "$(field 'd["paths"]["personas"]["path"]' <<<"$out")" = "$OLD/.personas/cast" ] && [ "$(field 'd["paths"]["profile"]["exists"]' <<<"$out")" = "True" ] \
  && [ "$(field 'd["paths"]["lessons"]["exists"]' <<<"$out")" = "False" ]; then
  pass "init --existing link points at the folders an older tool already reads, and show says which paths exist"
else
  fail "init over older folders: $out"
fi
if [ "$(project --repo "$OLD/docs" path plans)" = "$OLD/docs/plans" ]; then pass "path prints one absolute path, from any directory of the checkout"; else fail "path plans"; fi
if [ "$(status_of project --repo "$OLD" path plan)" = 1 ]; then pass "an unknown path name is refused"; else fail "unknown path name"; fi

settings() { printf '%s\n' "$@" > "$OLD/.lem/project.toml"; }
settings '[branch]' 'base = "master"' 'lands = "agent"'
err=$(project --repo "$OLD" show 2>&1 || true)
if [ "$(status_of project --repo "$OLD" show)" = 1 ] && grep -q "did you mean 'land'" <<<"$err"; then pass "an unknown key is refused with the nearest valid one"; else fail "unknown key: $err"; fi
settings '[branch]' 'base = "master"' 'land = "robot"'
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "a land value other than owner or agent is refused"; else fail "land value"; fi
settings '[paths]' 'styleguide = "../elsewhere"'
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "a path that leaves the repository is refused"; else fail "path outside"; fi
settings '[gate]' 'commands = "pytest"'
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
settings '[branch]' 'base = "master"' '[gate]' 'ignores = ["docs/*"]'
if [ "$(project --repo "$OLD" show | field '(d["branch"]["history"], d["gate"]["ignores"])')" = "('keep', ['docs/*'])" ] && grep -q '^history = "keep"$' "$NEW/.lem/project.toml"; then
  pass "a branch's own commits land unless the settings say one commit, and the gate may name paths it does not read"
else
  fail "history and gate.ignores"
fi
settings '[seats.reviewer]' 'agent = "gemini"'
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "a reviewer that is neither claude nor codex is refused"; else fail "reviewer value"; fi
settings '[seats]' 'reviewer = "claude"'
err=$(project --repo "$OLD" show 2>&1 || true)
if [ "$(status_of project --repo "$OLD" show)" = 1 ] && grep -q "seats.reviewer is a table" <<<"$err"; then pass "the reviewer as a bare word is refused, with the table to write instead"; else fail "reviewer as a string: $err"; fi
settings '[seats.reviewer]' 'model = "some-model"'
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "a reviewer's model with no agent is refused"; else fail "model without agent"; fi
settings '[seats.reviewer]' 'agent = "codex"' 'modle = "some-model"'
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "an unknown key of the reviewer's seat is refused"; else fail "unknown seat key"; fi
settings '[seats.reviewer]' 'agent = "claude"' 'model = "some-model"' 'effort = "high"' 'plan_effort = "xhigh"'
if [ "$(project --repo "$OLD" show | field 'd["seats"]["reviewer"]')" = "{'agent': 'claude', 'model': 'some-model', 'effort': 'high', 'plan_effort': 'xhigh'}" ]; then
  pass "the reviewer's seat names the agent, which may be the builder's family, and what its pane starts with"
else
  fail "reviewer seat: $(project --repo "$OLD" show | field 'd["seats"]')"
fi
settings '[branch]' 'base = "v2"' 'protected = ["master", "develop"]'
err=$(project --repo "$OLD" may-land master 2>&1 || true)
if [ "$(status_of project --repo "$OLD" may-land master)" = 1 ] && grep -q "protected" <<<"$err" && [ "$(status_of project --repo "$OLD" may-land feature)" = 1 ] \
  && [ "$(status_of project --repo "$OLD" may-land v2)" = 0 ]; then
  pass "may-land refuses a protected branch and any branch but the base, and accepts the base"
else
  fail "may-land: $err"
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

settings '[branch]' 'base = "master"' '[flow]' 'careful = ["app/outbox/*", "*/migrations/*"]'
out=$(project --repo "$OLD" careful app/outbox/emit/site.py app/products/migrations/0002_x.py app/products/models.py "$OLD/app/outbox/a.py")
if [ "$(field 'sorted(c["file"] for c in d["careful"])' <<<"$out")" = "['app/outbox/a.py', 'app/outbox/emit/site.py', 'app/products/migrations/0002_x.py']" ] \
  && [ "$(field 'd["plain"]' <<<"$out")" = "['app/products/models.py']" ]; then
  pass "careful names the files a pattern matches, nested ones and absolute paths too"
else
  fail "careful: $out"
fi
if [ "$(status_of project --repo "$WORK" show)" = 1 ]; then pass "a directory outside any checkout is refused"; else fail "outside a checkout"; fi

# Task state: one directory per task inside the git directory, seen from every worktree.
commit() { git -C "$1" -c user.name=t -c user.email=t@t commit -q --allow-empty -m "$2"; }
commit "$OLD" start
git -C "$OLD" worktree add -q "$WORK/wt" -b feat/x
dir=$(project --repo "$WORK/wt" task-dir report-dates-stay-whole)
if [ "$dir" = "$OLD/.git/lem/tasks/report-dates-stay-whole" ] && [ -d "$dir/reports" ] && [ -z "$(git -C "$WORK/wt" status --porcelain)" ]; then
  pass "task-dir, run in a worktree, makes the task's directory in the shared git directory"
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
if [ "$(project --repo "$WORK/wt" state-dir)" = "$OLD/.git/lem" ]; then pass "state-dir prints the one folder every worktree shares"; else fail "state-dir"; fi
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
if [ -e "$OLD/.git/lem/tasks/empty-ask" ]; then fail "a refused task-dir made its directory"; fi
rm -r "$titled" "$plain"
# One ticket is one task, until that task is dropped.
project --repo "$OLD" task-dir from-a-ticket --ticket mbz-12 --ask "Report dates are cut" >/dev/null
err=$(project --repo "$OLD" task-dir the-same-ticket --ticket MBZ-12 2>&1 || true)
if [ "$(project --repo "$OLD" tasks | field '{t["slug"]: t["ticket"] for t in d}')" = "{'from-a-ticket': 'MBZ-12', 'report-dates-stay-whole': None}" ] \
  && grep -q "the task 'from-a-ticket' already holds the ticket MBZ-12" <<<"$err" && [ ! -e "$OLD/.git/lem/tasks/the-same-ticket" ] \
  && [ "$(status_of project --repo "$OLD" task-dir bad-ticket --ticket "not a ticket")" = 1 ] && [ ! -e "$OLD/.git/lem/tasks/bad-ticket" ] \
  && [ "$(status_of project --repo "$OLD" task-dir from-a-ticket --ticket MBZ-13)" = 1 ] && [ "$(cat "$OLD/.git/lem/tasks/from-a-ticket/ticket.txt")" = MBZ-12 ] \
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
printf '%s\n' '2026-01-01T00:00Z building: task 1 of 1' > "$OLD/.git/lem/tasks/from-a-ticket/state.md"
building=$(owed)
printf '%s\n' '2026-01-01T00:00Z landed: master a..b' > "$OLD/.git/lem/tasks/from-a-ticket/state.md"
landed=$(owed)
printf '%s\n' '2026-01-01T00:00Z dropped: the owner dropped it' > "$OLD/.git/lem/tasks/from-a-ticket/state.md"
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
settings '[branch]' 'base = "master"'
rm -r "$OLD/.git/lem/tasks/from-a-ticket" "$OLD/.git/lem/tasks/the-same-ticket"
none=$(project --repo "$OLD" tasks | field '[t["proposal"] for t in d]')
echo '{"proposed": "0123", "pr": {"number": 7, "url": "https://github.com/acme/shop/pull/7"}, "not_green": ["story 1 changed during the build: y is taken."]}' > "$dir/landing.json"
if [ "$none" = "[None]" ] && [ "$(project --repo "$OLD" tasks | field '[t["proposal"] for t in d]')" = "[{'pull_request': 'https://github.com/acme/shop/pull/7', 'green': False, 'not_green': ['story 1 changed during the build: y is taken.']}]" ]; then
  pass "tasks says what a landing proposed: the pull request's address, and green or each reason it is not"
else
  fail "the proposal in tasks: $(project --repo "$OLD" tasks)"
fi
rm "$dir/landing.json"
other=$(project --repo "$OLD" task-dir written-by-hand)
printf '%s\n' '2026-01-02 build: task 2 of 3 running' > "$other/state.md"
out=$(project --repo "$OLD" tasks)
if [ "$(field '[(t["slug"], t["status"]) for t in d]' <<<"$out")" = "[('report-dates-stay-whole', 'building'), ('written-by-hand', None)]" ]; then
  pass "a state block that state did not write has no status"
else
  fail "hand-written state: $out"
fi

# This machine's own settings: read from the main checkout in a worktree too, only seats and tools.
settings '[branch]' 'base = "master"' '[seats.reviewer]' 'agent = "codex"' 'model = "the-usual" ' 'effort = "high"'
out=$(project --repo "$WORK/wt" reviewer claude a-claude-model high)
if [ "$(field '(d["reviewer"], d["local"]["overrides"])' <<<"$out")" = "({'agent': 'claude', 'model': 'a-claude-model', 'effort': 'high', 'plan_effort': None}, ['seats.reviewer'])" ] \
  && [ -f "$OLD/.lem/project.local.toml" ] && [ ! -e "$WORK/wt/.lem/project.local.toml" ] \
  && [ "$(project --repo "$OLD" show | field '(d["seats"]["reviewer"]["agent"], d["seats"]["reviewer"]["model"], d["local"]["file"])')" = "('claude', 'a-claude-model', '$OLD/.lem/project.local.toml')" ]; then
  pass "reviewer, run in a worktree, writes this machine's seat in the main checkout; it replaces the project's seat whole and show says so"
else
  fail "reviewer override: $out"
fi
# A value the owner wrote by hand keeps every character through a rewrite: a rocket, a quote, a backslash.
printf '%s\n' '[tools]' 'annotate = "/opt/my \"own\" rev-🚀\\x"' >> "$OLD/.lem/project.local.toml"
project --repo "$OLD" reviewer claude >/dev/null
out=$(project --repo "$OLD" reviewer default)
if [ "$(field '(d["reviewer"]["agent"], d["reviewer"]["model"], d["local"]["overrides"])' <<<"$out")" = "('codex', 'the-usual', ['tools.annotate'])" ] \
  && [ "$(project --repo "$OLD" show | field 'd["tools"]["annotate"]')" = '/opt/my "own" rev-🚀\x' ] && ! grep -q "seats" "$OLD/.lem/project.local.toml"; then
  pass "reviewer default gives the project's reviewer back and keeps what else the machine set, character for character"
else
  fail "reviewer default: $out / $(cat "$OLD/.lem/project.local.toml")"
fi
printf '%s\n' '[gate]' 'commands = []' > "$OLD/.lem/project.local.toml"
err=$(project --repo "$OLD" show 2>&1 || true)
if [ "$(status_of project --repo "$OLD" show)" = 1 ] && grep -q "\[gate\] is the project's rule" <<<"$err" \
  && [ "$(status_of project --repo "$OLD" reviewer claude)" = 1 ]; then
  pass "the machine's own file may not hold the gate or any other rule of the project"
else
  fail "a gate in the local file: $err"
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
rm "$OLD/.lem/project.local.toml"
if [ "$(status_of project --repo "$OLD" reviewer gemini)" = 1 ] && [ "$(status_of project --repo "$OLD" reviewer codex a b c d)" = 1 ] && [ ! -e "$OLD/.lem/project.local.toml" ]; then
  pass "reviewer refuses an agent that cannot review and a fifth word, and writes nothing then"
else
  fail "reviewer refusals"
fi
project --repo "$OLD" reviewer codex >/dev/null && project --repo "$OLD" reviewer default >/dev/null
if [ ! -e "$OLD/.lem/project.local.toml" ]; then pass "a local file with nothing left in it is removed"; else fail "empty local file stays"; fi
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
events() { "$PY" -c 'import json, sys; d = [json.loads(line) for line in open(sys.argv[1])]; print(eval(sys.argv[2], {"d": d}))' "$OLD/.git/lem/events.jsonl" "$1"; }
if [ "$(events '[(e["event"], e["task"], e["status"], e["text"], e["lines"]) for e in d[:2]]')" = "[('task.state', 'report-dates-stay-whole', 'queued', 'waits for a free place', []), ('task.state', 'report-dates-stay-whole', 'building', 'task 2 of 3', ['next: the report'])]" ] \
  && [ "$(events 'len(d)')" = 2 ] && [ "$(events 'd[1]["ask"], d[1]["limit"], "head" in d[1]')" = "('Keep report dates whole.', 4, False)" ] \
  && [ "$(sed -n 2p "$OLD/.git/lem/events.js")" = "lemEvent($(sed -n 2p "$OLD/.git/lem/events.jsonl"));" ]; then
  pass "each state block is one event with the ask and the limit, a refused one is none, and the board's copy holds the same record"
else
  fail "events: $(cat "$OLD/.git/lem/events.jsonl")"
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
before=$(grep -c '' "$OLD/.git/lem/events.jsonl")
if [ "$(status_of project --repo "$OLD" log with-a-worktree task.state status=landed)" = 1 ] && [ "$(status_of project --repo "$OLD" log no-such-task gate exit:=0)" = 1 ] \
  && [ "$(status_of project --repo "$OLD" log with-a-worktree gate exit:=zero)" = 1 ] && [ "$(status_of project --repo "$OLD" log with-a-worktree gate task=other)" = 1 ] \
  && [ "$(status_of project --repo "$OLD" log with-a-worktree gate exit)" = 1 ] && [ "$(grep -c '' "$OLD/.git/lem/events.jsonl")" = "$before" ]; then
  pass "log refuses a state event, an unknown task, a value that is not JSON, a field the log sets and a bare word, and appends nothing then"
else
  fail "log refusals"
fi
project --repo "$OLD" state with-a-worktree dropped "the test is over" >/dev/null

# The limit on tasks that build at one time.
if [ "$(project --repo "$OLD" show | field 'd["flow"]["max_tasks"]')" = 4 ] && grep -q '^max_tasks = 4$' "$NEW/.lem/project.toml"; then
  pass "four tasks build at one time unless the settings say otherwise, and init writes that number where the owner sees it"
else
  fail "max_tasks default"
fi
settings '[branch]' 'base = "master"' '[flow]' 'topics = ["a price a customer pays", "data that cannot be rebuilt"]'
if [ "$(project --repo "$OLD" show | field '(d["flow"]["topics"], d["flow"]["careful"])')" = "(['a price a customer pays', 'data that cannot be rebuilt'], [])" ]; then
  pass "a project names its danger topics in the owner's words, beside its careful paths"
else
  fail "flow.topics: $(project --repo "$OLD" show 2>&1)"
fi
settings '[flow]' 'topics = "money"'
err=$(project --repo "$OLD" show 2>&1 || true)
if [ "$(status_of project --repo "$OLD" show)" = 1 ] && grep -q "flow.topics" <<<"$err" && ! grep -q Traceback <<<"$err"; then pass "danger topics that are not a list are refused"; else fail "flow.topics as a string: $err"; fi
settings '[branch]' 'base = "master"' '[flow]' 'max_tasks = 2'
out=$(project --repo "$OLD" may-start)
if [ "$(field 'd["running"]' <<<"$out")" = "['report-dates-stay-whole']" ] && [ "$(field 'd["limit"]' <<<"$out")" = 2 ]; then
  pass "may-start names the tasks that build and the limit while a place is free"
else
  fail "may-start below the limit: $out"
fi
project --repo "$OLD" task-dir second-task >/dev/null
project --repo "$OLD" state second-task building "the plan" >/dev/null
err=$(project --repo "$OLD" may-start 2>&1 || true)
if [ "$(status_of project --repo "$OLD" may-start)" = 1 ] && grep -q "flow.max_tasks is 2" <<<"$err" && grep -q "queued" <<<"$err"; then
  pass "may-start refuses a new task at the limit and says to queue it"
else
  fail "may-start at the limit: $err"
fi
project --repo "$OLD" state second-task ready "the report is written" >/dev/null
if [ "$(status_of project --repo "$OLD" may-start)" = 0 ]; then pass "a task that waits for its landing takes no place"; else fail "may-start after ready"; fi
project --repo "$OLD" state second-task landing "the gate runs" >/dev/null
err=$(project --repo "$OLD" may-start 2>&1 || true)
if [ "$(status_of project --repo "$OLD" may-start)" = 1 ] && grep -q "report-dates-stay-whole, second-task" <<<"$err"; then
  pass "a task whose gate runs holds a place, because a builder may repair what the gate shows"
else
  fail "may-start during a landing: $err"
fi
project --repo "$OLD" state second-task ready "the gate was cut off" >/dev/null
accepted=""
for bad in 0 true '"four"' 2.5; do
  settings '[flow]' "max_tasks = $bad"
  if [ "$(status_of project --repo "$OLD" show)" != 1 ]; then accepted="$accepted $bad"; fi
done
if [ -z "$accepted" ]; then pass "a limit that is not a whole number of 1 or more is refused"; else fail "max_tasks accepted:$accepted"; fi
settings '[branch]' 'base = "master"'

# The machine check: a required tool that is absent fails it, an optional one only changes its row.
DOCTOR=$PWD/skills/lem/scripts/doctor.py
BIN=$WORK/bin
FAKEHOME=$WORK/home
mkdir -p "$BIN" "$FAKEHOME"
ln -s "$(command -v git)" "$BIN/git"
fake() { printf '#!/bin/sh\necho "%s"\n' "$2" > "$BIN/$1"; chmod +x "$BIN/$1"; }
doctor() { env -i PATH="$BIN" HOME="$FAKEHOME" "$PY" -B "$DOCTOR"; }
row() { field "next(t for t in d[\"tools\"] if t[\"name\"] == \"$1\")[\"$2\"]"; }
out=$(doctor || true)
if [ "$(status_of doctor)" = 1 ] && [ "$(field 'd["ok"]' <<<"$out")" = "False" ] && [ "$(row revmux found <<<"$out")" = "False" ] && [ "$(row git found <<<"$out")" = "True" ] \
  && [ "$(row python3 found <<<"$out")" = "True" ] && [ "$(row python3 need <<<"$out")" = "required" ] && [ "$(row claude found <<<"$out")" = "False" ] && [ "$(row claude need <<<"$out")" = "required" ]; then
  pass "doctor exits 1 and says so when the review tool is absent, and the agent that runs Lem is a required row"
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
# Lem installed as a plugin brings the builder too, for the user or for the one repository it was installed in.
printf '%s\n' "{\"version\": 2, \"plugins\": {\"lem@lem\": [{\"scope\": \"project\", \"projectPath\": \"$WORK/another-repository\"}]}}" > "$FAKEHOME/.claude/plugins/installed_plugins.json"
elsewhere=$(doctor | field 'next(t for t in d["tools"] if t["name"] == "lem-builder agent")["found"]' || true)
printf '%s\n' '{"version": 2, "plugins": {"lem@lem": []}}' > "$FAKEHOME/.claude/plugins/installed_plugins.json"
elsewhere="$elsewhere$(doctor | field 'next(t for t in d["tools"] if t["name"] == "lem-builder agent")["found"]' || true)"
printf '%s\n' "{\"version\": 2, \"plugins\": {\"lem@lem\": [{\"scope\": \"project\", \"projectPath\": \"$PWD\"}]}}" > "$FAKEHOME/.claude/plugins/installed_plugins.json"
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
keyed=$(env -i PATH="$BIN" HOME="$FAKEHOME" OPENROUTER_API_KEY=sk-not-a-real-key "$PY" -B "$DOCTOR")
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
# a stand-in for jev: it answers with the probability in JEV_P, or fails as JEV_EXIT says
# shellcheck disable=SC2016  # the stand-in's own variables, expanded when it runs
printf '%s\n' '#!/bin/sh' 'cat > /dev/null' 'if [ -n "$JEV_CALLED" ]; then touch "$JEV_CALLED"; fi' 'if [ -n "$JEV_EXIT" ]; then echo "no key" >&2; exit "$JEV_EXIT"; fi' \
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
for _ in 1 2 3 4 5 6 7 8 9 10; do grep -qs "that is gone" "$CQ/.git/lem/corrections.jsonl" && break; sleep 0.3; done
if [ "$out" = "exit=0" ] && grep -q "that is gone" "$CQ/.git/lem/corrections.jsonl"; then
  pass "a hook whose own directory was removed still exits 0 with no output, and queues the message for the event's repository"
else
  fail "the hook in a removed directory: $out"
fi
rm -f "$CQ/.git/lem/corrections.jsonl" "$WORK/jev-called"
sed -i.bak 's/^collect = true$/collect = false/' "$CQ/.lem/project.toml" && rm "$CQ/.lem/project.toml.bak"
# An input that stays open, and an old python3: the hook returns, with exit 0 and not a word.
started=$SECONDS
out=$(hook hook < <(event "the input stays open" s0; sleep 6) 2>&1; echo "exit=$?")
if [ "$out" = "exit=0" ] && [ $((SECONDS - started)) -lt 4 ]; then
  pass "the hook does not wait for its input to close"
else
  fail "the hook with an open input: $out after $((SECONDS - started))s"
fi
old=""
for candidate in /usr/bin/python3 python3.9 python3.10; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(sys.version_info >= (3, 11))' 2>/dev/null; then old=$candidate; break; fi
done
if [ -n "$old" ]; then
  # run from another directory than the repository of the event: the failure belongs in that repository's log
  out=$(cd "$WORK" && event "under an old python" s0 | "$old" -B "$CORR" hook 2>&1; echo "exit=$?")
  if [ "$out" = "exit=0" ] && grep -q "tomllib" "$CQ/.git/lem/corrections.log" && [ ! -e "$PWD/.git/lem/corrections.log" ]; then
    pass "under a python3 before 3.11 the hook exits 0, prints nothing, and logs the failure in the repository of the message"
  else
    fail "the hook under $old: $out / $(cat "$CQ/.git/lem/corrections.log" 2>&1)"
  fi
  rm -f "$CQ/.git/lem/corrections.log"
  # The other scripts under that python3: a row or one line that says what is needed, and no traceback.
  rows=$("$old" -B "$DOCTOR" 2>&1 || true)
  said=""
  for script in "$PWD/scripts/setup.py" "$PWD/skills/lem/scripts/project.py" "$PWD/skills/lem/scripts/land.py" "$PWD/skills/lem/scripts/stories.py" "$PWD/skills/lem/scripts/board.py"; do
    said="$said$("$old" -B "$script" --help 2>&1 || true)"$'\n'
  done
  if [ "$(field '(d["ok"], d["tools"][0]["name"], d["tools"][0]["found"])' <<<"$rows")" = "(False, 'python3', False)" ] && [ "$(grep -c "Lem needs Python 3.11 or newer, and this python3 is" <<<"$said")" = 5 ] \
    && ! grep -q Traceback <<<"$rows$said" && [ "$(status_of "$old" -B "$PWD/scripts/setup.py" --check)" = 1 ]; then
    pass "under a python3 before 3.11 the machine check gives its rows with python3 as absent, and every other script says in one line what it needs"
  else
    fail "the scripts under $old: $rows / $said"
  fi
else
  printf 'SKIP the hook under an old python3: none found\n'
fi
sed -i.bak 's/^collect = false$/collect = true/' "$CQ/.lem/project.toml" && rm "$CQ/.lem/project.toml.bak"
out=$(event "never push without asking" s1 | hook hook; echo "exit=$?")
for _ in 1 2 3 4 5 6 7 8 9 10; do [ -s "$CQ/.git/lem/corrections.jsonl" ] && break; sleep 0.3; done
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
if [ "$(field 'sorted(set(l["state"] for l in d["links"]))' <<<"$out")" = "['removed']" ] && [ -z "$(find "$TRIAL/.claude" -type l)" ] \
  && [ ! -e "$TRIAL/.claude/skills/.gitignore" ] && [ ! -e "$TRIAL/.claude/agents/.gitignore" ] \
  && [ "$(status_of env -i PATH="$BIN" HOME="$WORK/trialhome" "$PY" -B "$SETUP" --project "$WORK")" = 1 ]; then
  pass "setup --project --remove takes its links and its ignore files away, and a folder that is no repository is refused"
else
  fail "setup --project --remove: $out / $(find "$TRIAL/.claude")"
fi
# A folder that has an ignore file of its own keeps it, and the result says that git sees the links there.
echo '# kept by the project' > "$TRIAL/.claude/skills/.gitignore"
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
if [ "$(field 'sorted(set(l["state"] for l in d["links"]))' <<<"$out")" = "['removed']" ] && [ ! -e "$SETHOME/.claude/skills/lem" ] && [ -e "$SETHOME/.claude/skills/mine" ] && [ ! -e "$SETHOME/.local/bin/lem-ask" ] && [ ! -e "$SETHOME/.local/bin/jev" ]; then
  pass "setup --remove takes away the links it made and nothing else"
else
  fail "setup --remove: $out"
fi
# The hook of the correction queue: one command in the agent's settings, the owner's step, and nothing else in the file changes.
HOOKHOME=$WORK/hookhome
mkdir -p "$HOOKHOME"
hooksetup() { env -i PATH="$BIN" HOME="$HOOKHOME" "$PY" -B "$SETUP" --home "$HOOKHOME" "$@"; }
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
  && [ "$(hooksetup --corrections off | field 'd["corrections_hook"]["changed"]')" = "False" ]; then
  pass "setup --corrections off takes the hook out, removes a settings file that then holds nothing, and a second run changes nothing"
else
  fail "setup --corrections off: $out"
fi
# The owner's own settings stay: another key, another hook of the same event, a group that was empty before.
mkdir -p "$WORK/dotfiles"
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
  && [ ! -e "$WORK/trialhome/.claude" ] && trial --corrections off >/dev/null && [ ! -e "$TRIAL/.claude/settings.local.json" ] && [ -z "$(git -C "$TRIAL" status --porcelain)" ]; then
  pass "setup --project --corrections on writes the hook into that checkout's local settings, says that git sees the file, and off removes it"
else
  fail "setup --project --corrections: $out / $(git -C "$TRIAL" status --porcelain)"
fi
rmdir "$TRIAL/.claude" && ln -s "$WORK/shared-claude" "$TRIAL/.claude"
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
# A task that was reviewed and proposed and is not green: it waits for the owner's merge, and it does not go back a phase.
project --repo "$OLD" task-dir owner-lands-it >/dev/null
for block in 'building|plan committed, 3 tasks' 'building|task 3 of 3' 'ready|the report is written' 'landing|the checks start'; do
  project --repo "$OLD" state owner-lands-it "${block%%|*}" "${block#*|}" >/dev/null
done
project --repo "$OLD" log owner-lands-it review round:=1 kind=read verdict=clean must_fix:=0 should:=1 nit:=0 'answered:=["codex"]' 'silent:=[]' 'ran:=[]' 'left_out:=[]' tip=abc1234 >/dev/null
project --repo "$OLD" log owner-lands-it proposed green:=false 'not_green:=["story 1 changed during the build: y is taken."]' tip=abc1234 >/dev/null
project --repo "$OLD" state owner-lands-it open "ready to land on master at abc1234" "not green: story 1 changed during the build: y is taken." >/dev/null

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
project --repo "$RUL" init --base main --existing link >/dev/null
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
  && [ "$(field '(d["files"], d["exists"], d["styleguide"], d["rules"][0]["file"])' <<<"$out")" = "(['app/models.py', 'src/components/a.tsx'], True, '$RUL/.claude/rules', '$RUL/.claude/rules/00-conduct.md')" ]; then
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
# The skill's own layout is read the same way, and a project with no style guide yet gets an empty answer, not an error.
FRESH=$WORK/rules-fresh
git init -q -b main "$FRESH" && commit "$FRESH" start
project --repo "$FRESH" init --base main >/dev/null
none=$(project --repo "$FRESH" rules app/x.py | field '(d["exists"], d["rules"])')
mkdir -p "$FRESH/.lem/styleguide" && printf '%s\n' '---' 'paths:' '  - "app/**/*.py"' '---' > "$FRESH/.lem/styleguide/python.md"
if [ "$none" = "(False, [])" ] && [ "$(project --repo "$FRESH" rules app/x.py web/x.js | field '[(r["file"], r["covers"]) for r in d["rules"]]')" = "[('$FRESH/.lem/styleguide/python.md', ['app/x.py'])]" ]; then
  pass "a project with no style guide gets no rule and no error, and the skill's own style guide folder is read in the same format"
else
  fail "the picker in the skill's own layout: $none / $(project --repo "$FRESH" rules app/x.py web/x.js)"
fi
if [ "$(status_of project --repo "$RUL" migrate plan)" != 0 ] && [ -d "$RUL/.claude/rules" ] && [ ! -e "$RUL/.lem/styleguide" ] \
  && [ "$(project --repo "$RUL" show | field 'd["paths"]["styleguide"]["path"]')" = "$RUL/.claude/rules" ]; then
  pass "the rules of an adopted project stay where the agent loads them: the settings name that folder, and no command moves it"
else
  fail "an adopted project's rules"
fi

# The stories of a task: read from the top of its plan, and each one held by a test that fails on the base commit.
STORIES=$PWD/skills/lem/scripts/stories.py
stories() { "$PY" -B "$STORIES" --repo "$ST" "$@"; }
ST=$WORK/stories-repo
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
printf '%s\n' '# The export has the gift note' '' '## Stories' '' 'Kind: feature, because the export gets a new column and an empty cell.' '' \
  '1. A CSV export holds the gift note of an order: order 1042 with the note "for Ania"' '   has that text in its row.' \
  '   - test: `sh tests/gift.sh` in `tests/gift.sh`' '2. An order with no gift note has an empty cell, not the word "None".' \
  '   - test: `sh tests/none.sh` in `tests/none.sh`, `tests/helper.sh`' '' '## Tasks' '' '1. The column.' > "$plan"
printf '%s\n' 'echo "1042,for Ania"' 'echo "1043,"' > "$stw/export.sh"
echo 'sh export.sh | grep -q "1042,for Ania"' > "$stw/tests/gift.sh" && echo '. tests/helper.sh; ! sh export.sh | grep -q None' > "$stw/tests/none.sh" && echo ': a helper' > "$stw/tests/helper.sh"
git -C "$stw" add -A && git -C "$stw" commit -q -m "feat: the gift note"
shown=$(stories show export-has-the-gift-note)
stories record export-has-the-gift-note >/dev/null
if [ "$(field '(d["kind"], d["why"], [(s["n"], s["text"].split(" of an order")[0].split(",")[0], [t["command"] for t in s["tests"]], [t["files"] for t in s["tests"]]) for s in d["stories"]])' <<<"$shown")" \
  = "('feature', 'the export gets a new column and an empty cell.', [(1, 'A CSV export holds the gift note', ['sh tests/gift.sh'], [['tests/gift.sh']]), (2, 'An order with no gift note has an empty cell', ['sh tests/none.sh'], [['tests/none.sh', 'tests/helper.sh']])])" ] \
  && [ "$(field 'd["stories"][0]["text"].endswith("has that text in its row.")' <<<"$shown")" = True ] \
  && [ "$(grep -c '"event": "task.stories"' "$ST/.git/lem/events.jsonl")" = 1 ] && grep -q '"kind": "feature"' "$ST/.git/lem/events.js"; then
  pass "the stories are read from the top of the task's plan, each with its text over two lines and its tests, and record puts them into the event log for the board"
else
  fail "stories show and record: $shown"
fi
before=$(git -C "$stw" rev-parse HEAD)
echo 'kept: mine' > "$stw/local.conf" && echo 'local.conf' >> "$ST/.git/info/exclude"
out=$(stories red export-has-the-gift-note)
if [ "$(field '(d["ok"], [(t["story"], t["on_branch"], t["on_base"] != 0, t["problem"]) for t in d["tests"]], d["without_a_test"])' <<<"$out")" = "(True, [(1, 0, True, None), (2, 0, True, None)], [])" ] \
  && [ "$(git -C "$stw" branch --show-current)" = "feat/export-has-the-gift-note" ] && [ "$(git -C "$stw" rev-parse HEAD)" = "$before" ] && [ -z "$(git -C "$stw" status --porcelain)" ] \
  && [ "$(cat "$stw/local.conf")" = 'kept: mine' ] && [ "$(find "$ST/.lem/worktrees" -maxdepth 1 -name '*.red-*' | grep -c '')" = 0 ] \
  && [ "$(git -C "$ST" worktree list | grep -c '')" = 2 ] && grep -q '"event": "task.red"' "$ST/.git/lem/events.jsonl"; then
  pass "red runs each story's tests in a worktree of its own, on the branch and with only the test files laid over the base commit: both fail there; the task's worktree is not touched, a file git ignores in it too, and the check's worktree is gone"
else
  fail "stories red: $out / $(git -C "$stw" status --porcelain) / $(git -C "$ST" worktree list)"
fi
# What does not hold a story: a test that passes on the base commit too, one that changes a file both
# commits have, one whose helper is not named, a folder in the place of a file. And a story with no test.
story3() { git -C "$stw" checkout -q -- docs && "$PY" -c 'import sys; p, lines = sys.argv[1], sys.argv[2:]; s = open(p).read(); open(p, "w").write(s.replace("\n## Tasks", "\n".join(lines) + "\n\n## Tasks"))' "$plan" "$@" && git -C "$stw" commit -q -am "docs: a third story" && stories red export-has-the-gift-note 2>&1 || true; git -C "$stw" reset -q --hard "$before"; }
# shellcheck disable=SC2016
weak=$(story3 '3. The export still has one row for each order.' '   - test: `sh export.sh` in `tests/gift.sh`')
# the settings file is the same on the base commit and on the branch: a test that reads it and then changes it
echo 'grep -q max_tasks .lem/project.toml || exit 1; echo changed >> .lem/project.toml' > "$stw/tests/config.sh" && echo 'sh tests/runner.sh' > "$stw/tests/calls.sh" && echo 'exit 0' > "$stw/tests/runner.sh"
git -C "$stw" add -A && git -C "$stw" commit -q -m "test: more tests" && before=$(git -C "$stw" rev-parse HEAD)
# shellcheck disable=SC2016
writes=$(story3 '3. The config is read.' '   - test: `sh tests/config.sh` in `tests/config.sh`')
# shellcheck disable=SC2016
helper=$(story3 '3. The runner runs.' '   - test: `sh tests/calls.sh` in `tests/calls.sh`')
# shellcheck disable=SC2016
folder=$(story3 '3. The tests are there.' '   - test: `sh tests/gift.sh` in `tests`')
bare=$(story3 '3. The export still has one row for each order.')
said=$(story3 '3. The export still has one row for each order.' '   - no test: the count of rows is the export of today, which no change here touches.' | field '(d["ok"], d["without_a_test"])')
echo stray > "$stw/stray.txt"
dirty=$(stories red export-has-the-gift-note 2>&1 || true)
rm "$stw/stray.txt"
# shellcheck disable=SC2016
if grep -q 'story 3: `sh export.sh` passes on the base commit too, so it does not test the change' <<<"$weak" \
  && grep -q 'story 3: `sh tests/config.sh` passes on the base commit too' <<<"$writes" \
  && grep -q 'story 3: `sh tests/calls.sh` does not start on the base commit (exit 127), so its failure there proves nothing. If a file it needs is a helper of the test, name it among' <<<"$helper" \
  && grep -q "story 3: 'tests' is a folder on the branch. Name each file that holds the test, one by one" <<<"$folder" \
  && grep -q "story 3 names no test: every story is held by a test at the end of a build" <<<"$bare" \
  && [ "$said" = "(True, [{'story': 3, 'why': 'the count of rows is the export of today, which no change here touches.'}])" ] \
  && grep -q "the worktree has changes nobody committed" <<<"$dirty" && [ "$(git -C "$stw" rev-parse HEAD)" = "$before" ] \
  && [ "$(find "$ST/.lem/worktrees" -maxdepth 1 -name '*.red-*' | grep -c '')" = 0 ]; then
  pass "a story is not held by a test that passes on the base commit too, that only changes a file both commits have, or whose helper file is not named; a folder as a test file and a story with no test are refused, and one that says why it has none is listed"
else
  fail "stories red refusals: $weak / $writes / $helper / $folder / $bare / $said / $dirty"
fi
# A test that needs what a fresh worktree lacks is named as such, and the settings' gate.setup makes it.
echo 'test -f .made-by-setup && sh export.sh | grep -q "1042,for Ania"' > "$stw/tests/env.sh" && git -C "$stw" add -A && git -C "$stw" commit -q -m "test: one that needs a setup" && before=$(git -C "$stw" rev-parse HEAD)
# shellcheck disable=SC2016
lacks=$(story3 '3. The export has the note, in a set-up worktree.' '   - test: `sh tests/env.sh` in `tests/env.sh`')
sed -i.bak 's|^setup = \[\]$|setup = ["touch .made-by-setup"]|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
# shellcheck disable=SC2016
made=$(story3 '3. The export has the note, in a set-up worktree.' '   - test: `sh tests/env.sh` in `tests/env.sh`' | field '(d["ok"], d["setup"], d["tests"][2]["problem"])')
sed -i.bak 's|^setup = .*$|setup = ["exit 3"]|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
broken=$(stories red export-has-the-gift-note 2>&1 || true)
sed -i.bak 's|^setup = .*$|setup = []|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
# A worktree that a killed run of the check left behind is removed by the next run.
git -C "$ST" worktree add -q --detach "$ST/.lem/worktrees/export-has-the-gift-note.red-tip" main && git -C "$ST" worktree lock "$ST/.lem/worktrees/export-has-the-gift-note.red-tip"
git -C "$ST" worktree add -q --detach "$ST/.lem/worktrees/export-has-the-gift-note.red-999999" main
stories red export-has-the-gift-note >/dev/null
if grep -q "fails in a fresh worktree of the branch (exit 1). If it passes in the task's worktree, it needs something a fresh one lacks: put the commands that make it into gate.setup" <<<"$lacks" \
  && [ "$made" = "(True, [{'on': 'branch', 'command': 'touch .made-by-setup', 'exit': 0}, {'on': 'base', 'command': 'touch .made-by-setup', 'exit': 0}], None)" ] \
  && grep -q "of gate.setup failed in a fresh worktree of the branch (exit 3)" <<<"$broken" \
  && [ "$(find "$ST/.lem/worktrees" -maxdepth 1 -name '*.red-*' | grep -c '')" = 0 ] && [ "$(git -C "$ST" worktree list | grep -c '')" = 2 ]; then
  pass "a test that needs what a fresh worktree lacks is named as such and not taken for proof; the settings' gate.setup makes it in each of the two worktrees; a setup command that fails stops the check; and a worktree that a killed run left is removed"
else
  fail "stories red and gate.setup: $lacks / $made / $broken / $(git -C "$ST" worktree list)"
fi
# Each run has a worktree and a setup of its own, so what a test writes on the branch does not reach the base run;
# the result names the files of the branch that the base run lacked.
echo 'grep -q correct .test-state || exit 1; echo corrupt > .test-state' > "$stw/tests/state.sh" && git -C "$stw" add -A && git -C "$stw" commit -q -m "test: one that changes a file of the setup" && before=$(git -C "$stw" rev-parse HEAD)
sed -i.bak 's|^setup = .*$|setup = ["echo correct > .test-state"]|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
# shellcheck disable=SC2016
state=$(story3 '3. The state is read.' '   - test: `sh tests/state.sh` in `tests/state.sh`')
lacked=$(stories red export-has-the-gift-note | field '("export.sh" in d["run_without"], "tests/gift.sh" in d["run_without"], "tests/runner.sh" in d["run_without"])')
# A hook that fails after git made the worktree, and a setup command that locks it: neither worktree stays.
printf '%s\n' '#!/bin/sh' 'exit 9' > "$ST/.git/hooks/post-checkout" && chmod +x "$ST/.git/hooks/post-checkout"
hooked=$(status_of stories red export-has-the-gift-note)
# a hook that leaves a process behind: the check goes on, and that process is ended
printf '%s\n' '#!/bin/sh' 'sleep 32.9 &' 'exit 0' > "$ST/.git/hooks/post-checkout"
watched=$(stories red export-has-the-gift-note | field 'd["ok"]')
watched="$watched $(pgrep -f 'sleep 32\.9' | grep -c '' || true)"
rm "$ST/.git/hooks/post-checkout"
after_hook=$(git -C "$ST" worktree list | grep -c '')
sed -i.bak 's|^setup = .*$|setup = ["git worktree lock ."]|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
locked=$(stories red export-has-the-gift-note | field 'd["ok"]')
after_lock="$(git -C "$ST" worktree list | grep -c '') $(find "$ST/.lem/worktrees" -maxdepth 1 -name '*.red-*' | grep -c '' || true)"
# A worktree that cannot be removed is said beside the failure that came first, and the next run removes it.
sed -i.bak 's|^setup = .*$|setup = ["chmod 500 ..; exit 3"]|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
stuck=$(stories red export-has-the-gift-note 2>&1 || true)
chmod 700 "$ST/.lem/worktrees"
sed -i.bak 's|^setup = .*$|setup = []|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
stories red export-has-the-gift-note >/dev/null
after_stuck="$(git -C "$ST" worktree list | grep -c '') $(find "$ST/.lem/worktrees" -maxdepth 1 -name '*.red-*' | grep -c '' || true)"
# One check of a task at a time: while another process holds the task's lock, a second check is refused.
"$PY" -c 'import fcntl, sys, time; f = open(sys.argv[1], "w"); fcntl.flock(f, fcntl.LOCK_EX); print("held", flush=True); time.sleep(30)' "$ST/.git/lem/tasks/export-has-the-gift-note/red.lock" > "$WORK/lock.out" &
holder=$!
for _ in 1 2 3 4 5 6 7 8 9 10; do [ -s "$WORK/lock.out" ] && break; sleep 0.2; done
second=$(stories red export-has-the-gift-note 2>&1 || true)
kill "$holder" 2>/dev/null || true; wait "$holder" 2>/dev/null || true
# A check that is stopped ends the command it runs, and leaves no worktree.
sed -i.bak 's|^setup = .*$|setup = ["sleep 31.7"]|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
"$PY" -B "$STORIES" --repo "$ST" red export-has-the-gift-note > "$WORK/stopped.out" 2>&1 &
check=$!
for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do pgrep -f 'sleep 31\.7' >/dev/null 2>&1 && break; sleep 0.25; done
started=$(pgrep -f 'sleep 31\.7' | grep -c '' || true)
kill -TERM "$check" 2>/dev/null || true; wait "$check" 2>/dev/null || true
left=$(pgrep -f 'sleep 31\.7' | grep -c '' || true)
after_stop="$(git -C "$ST" worktree list | grep -c '') $(find "$ST/.lem/worktrees" -maxdepth 1 -name '*.red-*' | grep -c '' || true)"
sed -i.bak 's|^setup = .*$|setup = []|' "$ST/.lem/project.toml" && rm "$ST/.lem/project.toml.bak"
# shellcheck disable=SC2016
if grep -q 'story 3: `sh tests/state.sh` passes on the base commit too' <<<"$state" && [ "$lacked" = "(True, False, True)" ] \
  && [ "$hooked" = 1 ] && [ "$watched" = "True 0" ] && [ "$after_hook" = 2 ] && [ "$locked" = True ] && [ "$after_lock" = "2 0" ] \
  && grep -q "of gate.setup failed in a fresh worktree of the branch (exit 3)" <<<"$stuck" && grep -q "red-tip could not be removed; remove it yourself: git -C" <<<"$stuck" && [ "$after_stuck" = "2 0" ] \
  && grep -q "another check of this task's stories runs now" <<<"$second" \
  && [ "$started" -ge 1 ] && [ "$left" = 0 ] && [ "$after_stop" = "2 0" ] && grep -q "the check was stopped, and its commands are ended; its worktrees are removed" "$WORK/stopped.out"; then
  pass "each run of the check has a worktree and a setup of its own, and the result names what the base run lacked; a failed hook, a locked worktree and a stopped check leave no worktree and no process; and a second check of one task waits"
else
  fail "the check's worktrees: $state / $lacked / stuck $stuck $after_stuck / hook $hooked $watched $after_hook / lock $locked $after_lock / $second / stop $started $left $after_stop $(cat "$WORK/stopped.out")"
fi
# A plan whose stories do not have the form is refused with the line that is wrong.
form() { printf '%s\n' "$@" > "$plan"; stories show export-has-the-gift-note 2>&1 || true; }
no_section=$(form '# A plan' '' '## Tasks')
no_kind=$(form '## Stories' '' '1. A story.')
two=$(form '## Stories' '' 'Kind: correction, because it is one sentence.' '' '1. One.' '2. Two.')
order=$(form '## Stories' '' 'Kind: feature, because of two things.' '' '1. One.' '3. Three.')
# An example of the form in a code fence is not the section, and a plan of another task whose name ends the same way is not this task's.
# shellcheck disable=SC2016
fenced=$(form '# A plan' '' '````markdown' 'An example in an example:' '```' '## Stories' '' 'Kind: correction, because it is an example.' '' '1. An example.' '```' '````' '' '## Stories' '' 'Kind: feature, because it is the real one.' '' '1. The real story.' | field '(d["kind"], d["stories"][0]["text"])')
git -C "$stw" checkout -q -- docs
printf '%s\n' '## Stories' '' 'Kind: correction, because it is another task.' '' '1. Not this task.' > "$stw/docs/plans/20261116-csv-export-has-the-gift-note.md"
other=$(stories show export-has-the-gift-note | field '(d["kind"], d["plan"].rsplit("/", 1)[1])')
rm "$stw/docs/plans/20261116-csv-export-has-the-gift-note.md"
stories record export-has-the-gift-note >/dev/null && stories red export-has-the-gift-note >/dev/null
# shellcheck disable=SC2016
if [ "$fenced" = "('feature', 'The real story.')" ] && [ "$other" = "('feature', '20261115-export-has-the-gift-note.md')" ] \
  && grep -q 'has no `## Stories` section' <<<"$no_section" && grep -q "20261115-export-has-the-gift-note.md:3: the section starts with" <<<"$no_kind" \
  && grep -q "a correction has one story, and this plan has 2: it is a feature" <<<"$two" && grep -q ":6: the stories are numbered 1, 2, 3 in order" <<<"$order" \
  && [ "$(status_of stories show no-such-task)" = 1 ]; then
  pass "a plan with no stories section, no kind, a correction of two stories or a gap in the numbers is refused with the place and the fix; a fenced example is not the section, and a plan of another task is not read"
else
  fail "the form of the stories: $no_section / $no_kind / $two / $order"
fi

# Approved stories are frozen as written: the plan's stories are those, word for word, with only test lines added.
# They are approved at the interview, before the task has a worktree.
project --repo "$ST" task-dir approved-note >/dev/null
printf '%s\n' '## Stories' '' 'Kind: feature, because the note gets a file and an empty case.' '' '1. The note file holds the gift note of order 1042: "for Ania".' \
  '2. An order with no gift note has the line "1043," and no word' '   after the comma.' > "$WORK/approved.md"
approved=$(stories approve approved-note --file "$WORK/approved.md" 2>&1 || true)
kept_stories=$ST/.git/lem/tasks/approved-note/stories.json
# shellcheck disable=SC2016
printf '%s\n' '## Stories' '' 'Kind: feature, because of a test.' '' '1. A story.' '   - test: `sh t.sh` in `t.sh`' > "$WORK/tested.md"
tested=$(stories approve approved-note --file "$WORK/tested.md" 2>&1 || true)
not_one=$(stories approve approved-note --file "$WORK/approved.md" --correction 2>&1 || true)
no_file=$(stories approve approved-note 2>&1 || true)
kept_now=$(stories approved approved-note 2>/dev/null | field '(d["approved"]["by"], d["approved"]["digest"], [s["text"] for s in d["approved"]["stories"]])' 2>&1 || true)
if [ "$(field '(d["by"], d["kind"], len(d["digest"]), [s["n"] for s in d["stories"]], d["stories"][1]["text"])' <<<"$approved" 2>/dev/null)" \
  = "('owner', 'feature', 12, [1, 2], 'An order with no gift note has the line \"1043,\" and no word after the comma.')" ] \
  && [ "$("$PY" -c 'import json, sys; print(json.load(open(sys.argv[1]))["text"] == open(sys.argv[2]).read())' "$kept_stories" "$WORK/approved.md" 2>/dev/null)" = True ] \
  && [ "$(grep -c '"event": "stories.approved", "task": "approved-note", "by": "owner"' "$ST/.git/lem/events.jsonl")" = 1 ] \
  && [ "$kept_now" = "('owner', '$(field 'd["digest"]' <<<"$approved" 2>/dev/null)', ['The note file holds the gift note of order 1042: \"for Ania\".', 'An order with no gift note has the line \"1043,\" and no word after the comma.'])" ] \
  && grep -q "story 1 of tested.md has a test line: the stories he approves have none, and the lead adds them in the plan" <<<"$tested" \
  && grep -q "says .Kind: feature.: a feature waits for his own yes" <<<"$not_one" && grep -q "approve needs --file" <<<"$no_file" \
  && [ "$(grep -c '"event": "stories.approved"' "$ST/.git/lem/events.jsonl")" = 1 ]; then
  pass "approve keeps the stories the owner approved, before the task has a worktree: their text as written, a digest and who approved them, with one event for the board; a file with a test line, a feature as a correction and no file are refused"
else
  fail "stories approve: $approved / $tested / $not_one / $no_file / $kept_now"
fi
# The plan copies the approved stories, broken into other lines, and adds only the test lines: show and red take it.
atw=$(project --repo "$ST" worktree-dir approved-note)
git -C "$ST" worktree add -q -b feat/approved-note "$atw" main
project --repo "$ST" state approved-note building 'lead: builder' >/dev/null
mkdir -p "$atw/docs/plans" "$atw/tests"
aplan=$atw/docs/plans/20261116-approved-note.md
# aplan_with LINE...: the plan of approved-note, with these lines as its stories, and its commit
aplan_with() {
  printf '%s\n' '# The note' '' 'careful: no, it touches one new file.' '' '## Stories' '' 'Kind: feature, because the note gets a file and an empty case.' '' "$@" '' '## Tasks' '' '1. The note.' > "$aplan"
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
copied=$(stories show approved-note 2>&1 || true)
held=$(stories red approved-note 2>&1 || true)
if [ "$(field '(d["approved"]["by"], d["changes"], [len(s["tests"]) for s in d["stories"]])' <<<"$copied" 2>/dev/null)" = "('owner', [], [1, 1])" ] \
  && [ "$(field 'd["approved"]["digest"]' <<<"$copied" 2>/dev/null)" = "$(field 'd["digest"]' <<<"$approved" 2>/dev/null)" ] \
  && [ "$(field '(d["ok"], [t["story"] for t in d["tests"]])' <<<"$held" 2>/dev/null)" = "(True, [1, 2])" ]; then
  pass "a plan whose stories are the approved ones, in other line breaks and with test lines added, passes show and red"
else
  fail "a plan of approved stories: $copied / $held"
fi
adecide() { "$PY" -B "$PWD/skills/lem/scripts/decisions.py" --repo "$ST" "$@"; }
t1='The note file holds the gift note of order 1042: "for Ania".'
t2='An order with no gift note has the line "1043," and no word after the comma.'
c1='The note file holds the gift note of order 1042, "for Ania".'
c2='The note file holds the note "for Ania" of order 1042.'
a3='The note file ends with a line break.'
# A reworded story is refused by show and red until its change is recorded, with its text before and after.
aplan_with "1. $c1" "$one" "2. $t2" "$two"
reworded=$(stories show approved-note 2>&1 || true)
red_reworded=$(stories red approved-note 2>&1 || true)
adecide story approved-note --changed 1 --was "$t1" --now "$c1" --why "The importer splits on a colon." --by lead >/dev/null 2>&1 || true
changed_now=$(stories show approved-note 2>/dev/null | field '[(c["change"], c["story"], c["how"]) for c in d["changes"]]' 2>&1 || true)
# An earlier change lets no later one pass: the plan changes story 1 again, and a record of it names what it is now.
aplan_with "1. $c2" "$one" "2. $t2" "$two"
again=$(stories show approved-note 2>&1 || true)
stale=$(adecide story approved-note --changed 1 --was "$t1" --now "$c2" --why "The note comes first." --by lead 2>&1 || true)
adecide story approved-note --changed 1 --was "$c1" --now "$c2" --why "The note comes first in the sentence." --by lead >/dev/null 2>&1 || true
chained=$(stories show approved-note 2>/dev/null | field '[c["story"] for c in d["changes"]]' 2>&1 || true)
# A story the build added can leave again, by a record of its own.
adecide story approved-note --added 3 --now "$a3" --why "The reader of the file needs it." --by lead >/dev/null 2>&1 || true
aplan_with "1. $c2" "$one" "2. $t2" "$two" "3. $a3" '   - no test: printf ends every line so.'
added_now=$(stories show approved-note 2>/dev/null | field 'len(d["changes"])' 2>&1 || true)
adecide story approved-note --removed 3 --was "$a3" --why "Printf ends every line so, and nobody needs the rule." --by lead >/dev/null 2>&1 || true
aplan_with "1. $c2" "$one" "2. $t2" "$two"
gone_again=$(stories show approved-note 2>/dev/null | field '[(c["how"], c["story"]) for c in d["changes"]]' 2>&1 || true)
# A dropped story is refused until its removal is recorded with its text.
aplan_with "1. $c2" "$one"
dropped=$(stories show approved-note 2>&1 || true)
wrong_was=$(adecide story approved-note --removed 2 --was "An order with no gift note has the line 1043." --why "Every order has a note now." --by lead 2>&1 || true)
adecide story approved-note --removed 2 --was "$t2" --why "Every order has a note now." --by personas --said "The merchant and the accountant both dropped it." >/dev/null 2>&1 || true
removed_now=$(stories show approved-note 2>/dev/null | field '(d["changes"][-1]["how"], d["changes"][-1]["by"], d["changes"][-1]["said"])' 2>&1 || true)
expected=$(adecide changes approved-note 2>/dev/null | field 'd["expected"]' 2>&1 || true)
# The command takes one change, its reason, and who made it: a choice of the build, or the lead or the personas.
neither=$(adecide story approved-note --added 2 --now "x" --why "w" 2>&1 || true)
both=$(adecide story approved-note --added 2 --now "x" --why "w" --choice 1 --by lead 2>&1 || true)
nosaid=$(adecide story approved-note --added 2 --now "x" --why "w" --by personas 2>&1 || true)
twoways=$(adecide story approved-note --changed 1 --added 2 --now "x" --why "w" --by lead 2>&1 || true)
added_was=$(adecide story approved-note --added 2 --now "x" --was "y" --why "w" --by lead 2>&1 || true)
nochoice=$(adecide story approved-note --added 2 --now "x" --why "w" --choice 9 2>&1 || true)
not_approved=$(adecide story export-has-the-gift-note --changed 1 --was "x" --now "y" --why "w" --by lead 2>&1 || true)
log_story=$(status_of adecide log approved-note --what x --chose y --why z --by lead --story 1 --was "$t1")
records=$(grep -c '"kind": "story"' "$ST/.git/lem/tasks/approved-note/decisions.jsonl" || true)
plain=$(stories show export-has-the-gift-note 2>/dev/null | field '(d["approved"], d["changes"])' 2>&1 || true)
if grep -qF "story 1 of 20261116-approved-note.md says '$c1', and the expected story 1 is '$t1'" <<<"$reworded" \
  && grep -qF 'decisions.py story approved-note --changed N --was TEXT --now TEXT' <<<"$reworded" \
  && grep -qF "story 1 of 20261116-approved-note.md says '$c1'" <<<"$red_reworded" && [ "$changed_now" = "[(1, 1, 'changed')]" ] \
  && grep -qF "story 1 of 20261116-approved-note.md says '$c2', and the expected story 1 is '$c1'" <<<"$again" \
  && grep -qF "story 1 is '$c1' after every earlier change, and --was says '$t1'" <<<"$stale" && [ "$chained" = "[1, 1]" ] \
  && [ "$added_now" = 3 ] && [ "$gone_again" = "[('changed', 1), ('changed', 1), ('added', 3), ('removed', 3)]" ] \
  && grep -qF "20261116-approved-note.md lacks story 2, '$t2', which the expected stories hold" <<<"$dropped" \
  && grep -qF "story 2 is '$t2' after every earlier change, and --was says 'An order with no gift note has the line 1043.'" <<<"$wrong_was" \
  && [ "$removed_now" = "('removed', 'personas', 'The merchant and the accountant both dropped it.')" ] && [ "$expected" = "['$c2']" ] \
  && grep -qF "names --choice ID, the choice of the build that led to it, or --by lead|personas when no choice did: one of the two" <<<"$neither" \
  && grep -qF "one of the two" <<<"$both" && grep -qF -- "--by personas needs --said" <<<"$nosaid" \
  && grep -qF "a story change is one of --changed N, --added N or --removed N" <<<"$twoways" && grep -qF -- "--added takes no --was: an added story had no text before" <<<"$added_was" \
  && grep -qF "no choice 9 went to the owner in approved-note" <<<"$nochoice" \
  && grep -qF "export-has-the-gift-note has no approved stories, so no change of them is recorded" <<<"$not_approved" && [ "$log_story" = 2 ] \
  && [ "$records" = 5 ] && [ "$plain" = "(None, [])" ]; then
  pass "a plan whose stories are not the approved ones with each recorded change applied is refused by show and red: an earlier change lets no later one pass, a story the build added can leave again, and a change whose text before is not the story as it stands is refused when it is recorded; the command takes one change with its reason and who made it; a task with no approved stories records none and keeps the plan as the source"
else
  fail "story changes against the approved stories: $reworded / $red_reworded / $changed_now / $again / $stale / $chained / $added_now / $gone_again / $dropped / $wrong_was / $removed_now / $expected / $neither / $both / $nosaid / $twoways / $added_was / $nochoice / $not_approved / $log_story / $records / $plain"
fi
# His next approval starts the changes again. A change keeps its texts as typed, and two spaces of a literal value match;
# a plan of another kind than the approved one is refused, since the kind is his.
# shellcheck disable=SC2016
code1='The note file holds the code `A  B` for order 1042.'
# shellcheck disable=SC2016
code2='The note file holds the code `A  B` for orders 1042 and 1044.'
printf '%s\n' '## Stories' '' 'Kind: feature, because the note gets a code.' '' "1. $code1" '2. Order 1043 has no note line.' > "$WORK/reapproved.md"
stories approve approved-note --file "$WORK/reapproved.md" >/dev/null 2>&1 || true
reset=$(adecide changes approved-note 2>/dev/null | field '(len(d["changes"]), d["expected"])' 2>&1 || true)
spaced=$(adecide story approved-note --changed 1 --was "$code1" --now "$code2" --why "Order 1044 has the note too." --by lead 2>/dev/null | field '(d["was"], d["now"])' 2>&1 || true)
printf '%s\n' '# The note' '' '## Stories' '' 'Kind: correction, because it is one sentence.' '' "1. $code2" '' '## Tasks' '' '1. The note.' > "$aplan"
kind=$(stories show approved-note 2>&1 || true)
# shellcheck disable=SC2016
aplan_with '1. The note file holds the code `A  B` for' '   orders 1042 and 1044.' '2. Order 1043 has no note line.'
kept_spaces=$(stories show approved-note 2>/dev/null | field '(len(d["changes"]), d["stories"][0]["text"])' 2>&1 || true)
if [ "$reset" = "(0, ['$code1', 'Order 1043 has no note line.'])" ] && [ "$spaced" = "('$code1', '$code2')" ] \
  && grep -qF "20261116-approved-note.md says \`Kind: correction\`, and he approved its stories as a feature: a change of the kind is his only" <<<"$kind" \
  && [ "$kept_spaces" = "(1, '$code2')" ]; then
  pass "his next approval starts the story changes again; a change keeps its texts as typed, two spaces of a literal value match, and a story broken over two lines is the same story; a plan of another kind than the approved one is refused"
else
  fail "a new approval, spaces and the kind: $reset / $spaced / $kind / $kept_spaces"
fi

# The decisions of a task: each one the lead or the personas took, and each choice that waits for the
# owner a fixed time and no longer, except a step that a later "no" cannot reverse.
DECISIONS=$PWD/skills/lem/scripts/decisions.py
DC=$WORK/decisions-repo
git init -q -b main "$DC" && commit "$DC" start && project --repo "$DC" init --base main >/dev/null
project --repo "$DC" task-dir gift-note >/dev/null && project --repo "$DC" task-dir other-task >/dev/null && project --repo "$DC" task-dir race-task >/dev/null
project --repo "$DC" task-dir dropped-task >/dev/null && project --repo "$DC" task-dir landed-task >/dev/null && project --repo "$DC" task-dir cancel-task >/dev/null
decide() { "$PY" -B "$DECISIONS" --repo "$DC" "$@"; }
dlist() { decide list gift-note | field "$1"; }
dfile=$DC/.git/lem/tasks/gift-note/decisions.jsonl
lead=$(decide log gift-note --what "The name of the new column" --chose gift_note --why "the other columns of the export are in snake case" --by lead --undo "rename the column" | field '(d["id"], d["kind"], d["by"], d["undo"])')
nosaid=$(decide log gift-note --what "Two notes on one order" --chose "both" --why "nobody loses one" --by personas 2>&1 || true)
nostory=$(status_of decide log gift-note --what "Two notes on one order" --chose "both" --why "nobody loses one" --by lead --story 2 --was "the old text")
personas=$(decide log gift-note --what "Two notes on one order" --chose "both notes, with a semicolon between them" --why "a merchant reads both" --by personas \
  --said "The merchant and the accountant both picked the semicolon." | field '(d["id"], d["by"], "story" in d, d["said"])')
if [ "$lead" = "(1, 'taken', 'lead', 'rename the column')" ] \
  && [ "$personas" = "(2, 'personas', False, 'The merchant and the accountant both picked the semicolon.')" ] \
  && grep -qF -- "--by personas needs --said: who answered and what each picked" <<<"$nosaid" && [ "$nostory" = 2 ] \
  && [ "$(grep -c '' "$dfile")" = 2 ] && [ "$(grep -c '"event": "decision.taken", "task": "gift-note"' "$DC/.git/lem/events.jsonl")" = 2 ]; then
  pass "a decision of the lead or of the personas is written down with its number, and each is an event too; the personas' one needs what they said, and a decision carries no story: a story's change has a record of its own"
else
  fail "decisions.py log: $lead / $personas / $nosaid / $nostory / $(cat "$dfile")"
fi
one=$(decide ask gift-note --what "Which note wins" --option "the first" --recommended "the first" --why w --said s 2>&1 || true)
notone=$(decide ask gift-note --what "Which note wins" --option "the first" --option "the last" --recommended "the newest" --why w --said s 2>&1 || true)
asked=$(decide ask gift-note --what "Where the note goes in the row" --option "the last column" --option "after the price" --recommended "the last column" \
  --why "an import that reads the columns by place keeps working" --said "The merchant picked the last column, the accountant after the price.")
forever=$(decide ask gift-note --what "Send the merchants an email about the new column" --option "send it" --option "do not send it" --recommended "do not send it" \
  --why "the column is visible in the export" --said "The merchant wants the email, the accountant does not." --irreversible person)
waits=$(decide pending gift-note)
everywhere=$(decide pending | field '([(c["task"], c["id"]) for c in d["waiting"]], d["ended"])')
if grep -q "a choice has two options or more" <<<"$one" && grep -qF -- "--recommended is one of the options, word for word: the first; the last" <<<"$notone" \
  && [ "$(field '(d["id"], d["wait_minutes"], "tell Lem that choice 3 of gift-note waits" in d["next"])' <<<"$asked")" = "(3, 15, True)" ] \
  && [ "$(field '(d["id"], d["irreversible"], "no timeout takes it" in d["next"])' <<<"$forever")" = "(4, 'person', True)" ] \
  && [ "$(field '[(c["id"], c["state"], 840 < c["seconds_left"] <= 900 if c["seconds_left"] is not None else None) for c in d["waiting"]]' <<<"$waits")" = "[(3, 'waits', True), (4, 'waits', None)]" ] \
  && [ "$everywhere" = "([('gift-note', 3), ('gift-note', 4)], [])" ] && [ "$(grep -c '"event": "decision.asked", "task": "gift-note"' "$DC/.git/lem/events.jsonl")" = 2 ]; then
  pass "a choice for the owner has two options or more and recommends one of them; it waits the settings' 15 minutes, and pending lists each choice that waits with the seconds it has left, and none for a step no timeout takes"
else
  fail "decisions.py ask and pending: $one / $notone / $asked / $forever / $waits / $everywhere"
fi
early=$(decide timeout gift-note 3 2>&1 || true)
# past FILE ID...: the wait of each choice ends, as its deadline is written into the past, the way fifteen minutes later would find it
past() { "$PY" -c 'import json, sys
lines = [json.loads(line) for line in open(sys.argv[1])]
for line in lines:
    if line["kind"] == "asked" and str(line["id"]) in sys.argv[2:]: line["deadline"] = "2026-01-01T00:00:00Z"
open(sys.argv[1], "w").write("".join(json.dumps(line) + "\n" for line in lines))' "$@"; }
past "$dfile" 3 4
never=$(decide timeout gift-note 4 2>&1 || true)
started=$(date +%s)
over=$(decide wait gift-note 3 --seconds 20 | field '(d["ended"], "timeout gift-note 3" in d["next"])')
still=$(decide wait gift-note 4 --seconds 1 | field '(d["ended"], d["seconds_left"])')
took=$(( $(date +%s) - started ))
taken=$(decide timeout gift-note 3 | field '(d["id"], d["kind"], d["chose"])')
again=$(decide timeout gift-note 3 2>&1 || true)
same=$(decide answer gift-note 3 --chose "the last column" | field '(d["kind"], d["taken"], d["next"])')
if grep -q "the wait of choice 3 has [0-9]* seconds left (until 20.*); the owner may still answer" <<<"$early" \
  && grep -q "choice 4 is a step that a later \"no\" cannot reverse (it sends something to a person): no timeout takes it" <<<"$never" \
  && [ "$over" = "('the wait is over', True)" ] && [ "$still" = "('still waits', None)" ] && [ "$took" -lt 10 ] \
  && [ "$taken" = "(3, 'timeout', 'the last column')" ] && grep -q "choice 3 does not wait: it is timeout, with 'the last column'" <<<"$again" \
  && [ "$same" = "('late', 'the last column', 'the answer is the action that was taken: nothing more to do')" ]; then
  pass "a timeout is refused while the wait runs and always for a step a later no cannot reverse; after the wait, wait says so at once, the recommended action is taken once, and a late answer that is the same needs nothing more"
else
  fail "decisions.py timeout: $early / $never / $over / $still / $took / $taken / $again / $same"
fi
decide ask gift-note --what "The header of the column" --option "Gift note" --option "Note" --recommended "Gift note" --why "it says what the cell holds" --said "The two personas split." >/dev/null
past "$dfile" 5
decide timeout gift-note 5 >/dev/null
differs=$(decide answer gift-note 5 --chose "Note" | field '(d["kind"], d["taken"], "it is a correction" in d["next"])')
decide ask gift-note --what "The note's length" --option "all of it" --option "200 characters" --recommended "all of it" --why "nothing is lost" --said "The two personas split." >/dev/null
answered=$(decide answer gift-note 6 --chose "200 characters" | field '(d["kind"], d["chose"])')
started=$(date +%s)
ended=$(decide wait gift-note 6 --seconds 20 | field '(d["ended"], d["chose"], d["by"])')
took=$(( $(date +%s) - started ))
twice=$(decide answer gift-note 6 --chose "all of it" 2>&1 || true)
unknown=$(decide answer gift-note 1 --chose x 2>&1 || true)
stands=$(dlist '[(c["id"], c["state"], c.get("chose"), c.get("by"), c.get("late", {}).get("chose")) for c in d]')
if [ "$differs" = "('late', 'Gift note', True)" ] && [ "$answered" = "('answered', '200 characters')" ] && [ "$ended" = "('answered', '200 characters', 'owner')" ] && [ "$took" -lt 10 ] \
  && grep -q "choice 6 has the owner's answer already: '200 characters'" <<<"$twice" && grep -q "no choice 1 went to the owner in gift-note; those that did: 3, 4, 5, 6" <<<"$unknown" \
  && [ "$stands" = "[(1, 'taken', 'gift_note', 'lead', None), (2, 'taken', 'both notes, with a semicolon between them', 'personas', None), (3, 'timeout', 'the last column', 'timeout', 'the last column'), (4, 'waits', None, None, None), (5, 'timeout', 'Gift note', 'timeout', 'Note'), (6, 'answered', '200 characters', 'owner', None)]" ]; then
  pass "an answer in time decides and wait returns at once with it; a late answer that differs is a correction; a second answer and an answer to a decision nobody asked are refused; and list shows each decision as it stands"
else
  fail "decisions.py answer, wait and list: $differs / $answered / $ended / $took / $twice / $unknown / $stands"
fi
# An answer after the wait, before anybody wrote the timeout, is late: the recommended option stands, and both lines are written at once.
decide ask gift-note --what "The note's font" --option "plain" --option "bold" --recommended "plain" --why "The export has no fonts." --said "The two personas split." >/dev/null
past "$dfile" 7
after=$(decide answer gift-note 7 --chose "bold" --why "Merchants miss it otherwise." | field '(d["kind"], d["state"], d["taken"], d["timeout_written"], "it is a correction" in d["next"])')
gone=$(decide timeout gift-note 7 2>&1 || true)
kinds=$(grep '"id": 7' "$dfile" | "$PY" -c 'import json, sys; print([json.loads(line)["kind"] for line in sys.stdin])')
seven=$(dlist 'next((c["state"], c["chose"], c.get("late", {}).get("chose"), c.get("late", {}).get("why")) for c in d if c["id"] == 7)')
if [ "$after" = "('late', 'timeout', 'plain', True, True)" ] && grep -q "choice 7 does not wait: it is timeout, with 'plain'" <<<"$gone" \
  && [ "$kinds" = "['asked', 'timeout', 'late']" ] && [ "$seven" = "('timeout', 'plain', 'bold', 'Merchants miss it otherwise.')" ]; then
  pass "an answer that comes after the wait, with no timeout written yet, is late: the timeout and the answer go into the record in one write, the recommended option stands, and the owner's reason is kept"
else
  fail "an answer after the wait: $after / $gone / $kinds / $seven"
fi
# A choice carries no story: the options are only its own, and a story it changes gets a record of its own after it.
carried=$(status_of decide ask gift-note --what w --option a --option b --recommended a --why w --said s --story 1 --was "the old text" --changes b)
decide ask gift-note --what "The note in the header" --option "no header" --option "a header" --recommended "no header" --why "The rows stay as they are." --said "The two personas split." >/dev/null
decide ask gift-note --what "The note in the footer" --option "no footer" --option "a footer" --recommended "no footer" --why "The rows stay as they are." --said "The two personas split." >/dev/null
decide answer gift-note 8 --chose "a header" >/dev/null && decide answer gift-note 9 --chose "no footer" >/dev/null
told=$(dlist '[(c["id"], c["state"], "story" in c) for c in d if c["id"] in (8, 9)]')
emptyundo=$(status_of decide log gift-note --what x --chose y --why z --by lead --undo " ")
if [ "$carried" = 2 ] && [ "$told" = "[(8, 'answered', False), (9, 'answered', False)]" ] && [ "$emptyundo" = 1 ] && [ "$(dlist 'len(d)')" = 9 ]; then
  pass "a choice carries no story, and its answer changes none by itself; an empty --undo is refused before anything is written"
else
  fail "a choice and a story, and empty values: $carried / $told / $emptyundo"
fi
# An answer takes one of the options, word for word, and keeps the owner's own words beside it.
decide ask gift-note --what "The note in the summary" --option "no summary" --option "a summary line" --recommended "no summary" --why "The rows stay as they are." --said "The two personas split." >/dev/null
free=$(decide answer gift-note 10 --chose "Put a line at the bottom, please." 2>&1 || true)
freecode=$(status_of decide answer gift-note 10 --chose "Put a line at the bottom, please.")
still=$(dlist 'next(c["state"] for c in d if c["id"] == 10)')
mapped=$(decide answer gift-note 10 --chose "a summary line" --words "Put a line at the bottom, please." | field '(d["kind"], d["chose"], d["words"])')
ten=$(dlist 'next((c["state"], c["chose"], c.get("owner_words")) for c in d if c["id"] == 10)')
if grep -qF "the answer to choice 10 is one of its options, word for word: no summary; a summary line" <<<"$free" && grep -qF -- "--words" <<<"$free" \
  && grep -qF -- "fits none of them, settle the choice with --instead TEXT, never with a new \`decisions.py log\`" <<<"$free" && [ "$freecode" = 1 ] && [ "$still" = waits ] \
  && [ "$mapped" = "('answered', 'a summary line', 'Put a line at the bottom, please.')" ] && [ "$ten" = "('answered', 'a summary line', 'Put a line at the bottom, please.')" ]; then
  pass "an answer names one of the choice's options word for word, and his own words go beside it; an answer that fits no option is refused and writes nothing"
else
  fail "an answer and the owner's words: $free / $freecode / $still / $mapped / $ten"
fi
# A decision of the owner's that is none of the options settles the choice with --instead; a story the choice carries is said changed or kept, never left out.
decide ask gift-note --what "Email the merchants" --option "email all customers" --option "email nobody" --recommended "email nobody" --why "Nobody asked for it." --said "The two personas split." --irreversible person >/dev/null
both=$(decide answer gift-note 11 --chose "email nobody" --instead "Email only the beta testers." 2>&1 || true)
neither=$(decide answer gift-note 11 2>&1 || true)
bothcode=$(status_of decide answer gift-note 11 --chose "email nobody" --instead "Email only the beta testers.")
settled=$(decide answer gift-note 11 --instead "Email only the beta testers." --why "They asked to hear first." | field '(d["kind"], d["chose"], d["instead"])')
eleven=$(dlist 'next((c["state"], c["chose"], c.get("instead"), c.get("owner_why")) for c in d if c["id"] == 11)')
open_ones=$(decide pending gift-note | field '[c["id"] for c in d["waiting"]]')
decide ask gift-note --what "The note in the title" --option "no title" --option "a title" --recommended "no title" --why "The rows stay as they are." --said "The two personas split." >/dev/null
flagged_answer=$(status_of decide answer gift-note 12 --instead "A title on the first page only." --story-changed --was "old")
decide answer gift-note 12 --instead "A title on the first page only." >/dev/null
twelve=$(dlist 'next((c["state"], c.get("instead"), "story" in c) for c in d if c["id"] == 12)')
if grep -qF -- "--chose names one of the options and --instead a decision of the owner's that is none of them: give one of the two" <<<"$both" && [ "$bothcode" = 1 ] \
  && grep -qF -- "give one of the two" <<<"$neither" && [ "$settled" = "('answered', 'Email only the beta testers.', True)" ] \
  && [ "$eleven" = "('answered', 'Email only the beta testers.', True, 'They asked to hear first.')" ] && [ "$open_ones" = "[4]" ] \
  && [ "$flagged_answer" = 2 ] && [ "$twelve" = "('answered', True, False)" ]; then
  pass "a decision of the owner's that is none of the options settles the choice with --instead, an irreversible one too, so it no longer waits; it is refused together with --chose or with neither; and it carries no story"
else
  fail "an answer that is none of the options: $both / $neither / $settled / $eleven / $open_ones / $flagged_answer / $twelve"
fi
# A task that is dropped or landed has nothing that waits: pending leaves its choices out and says why, wait returns at once, and list still shows them.
decide ask dropped-task --what "Email the merchants" --option "email all" --option "email nobody" --recommended "email nobody" --why "Nobody asked." --said "The two personas split." --irreversible person >/dev/null
decide ask landed-task --what "The header" --option "a header" --option "no header" --recommended "no header" --why "The rows stay." --said "The two personas split." >/dev/null
project --repo "$DC" state dropped-task dropped "the owner dropped it" >/dev/null && project --repo "$DC" state landed-task landed "main a..b" >/dev/null
all_open=$(decide pending | field '(sorted({c["task"] for c in d["waiting"]}), [(e["task"], e["status"], e["choices"]) for e in d["ended"]])')
one_ended=$(decide pending dropped-task | field '(d["waiting"], d["ended"][0]["status"], d["ended"][0]["says"])')
started=$(date +%s)
waited=$(decide wait dropped-task 1 --seconds 20 | field '(d["ended"], d["status"])')
took=$(( $(date +%s) - started ))
kept=$(decide list dropped-task | field '[(c["id"], c["state"]) for c in d]')
if [ "$all_open" = "(['gift-note'], [('dropped-task', 'dropped', [1]), ('landed-task', 'landed', [1])])" ] \
  && [ "$one_ended" = "([], 'dropped', 'the task is dropped: its choices no longer wait for an answer')" ] \
  && [ "$waited" = "('the task is dropped: the choice no longer waits', 'dropped')" ] && [ "$took" -lt 10 ] && [ "$kept" = "[(1, 'waits')]" ]; then
  pass "a dropped or landed task has no choice that waits: pending leaves it out and says why, wait returns at once with the task's status, and list still shows its record"
else
  fail "the choices of an ended task: $all_open / $one_ended / $waited / $took / $kept"
fi
# A task dropped while a wait runs ends that wait: the loop reads the task's status each time it reads the choice.
decide ask cancel-task --what "Email the merchants" --option "email all" --option "email nobody" --recommended "email nobody" --why "Nobody asked." --said "The two personas split." --irreversible person >/dev/null
started=$(date +%s)
"$PY" -B "$DECISIONS" --repo "$DC" wait cancel-task 1 --seconds 8 > "$WORK/cancel-wait.out" 2>&1 &
waiter=$!
sleep 1
project --repo "$DC" state cancel-task dropped "the owner dropped it while a choice waited" >/dev/null
wait "$waiter" || true
took=$(( $(date +%s) - started ))
cancelled=$(field '(d["ended"], d.get("status"))' < "$WORK/cancel-wait.out" || true)
if [ "$cancelled" = "('the task is dropped: the choice no longer waits', 'dropped')" ] && [ "$took" -lt 8 ]; then
  pass "a task dropped while a wait on its choice runs ends that wait before its time, with the task's status"
else
  fail "a task dropped during a wait: $cancelled / $took s / $(cat "$WORK/cancel-wait.out")"
fi
# The owner's answer to a choice that waits is written with answer, by Lem and by a session's lead: a new decision would leave the choice waiting.
SKILLTEXT=${SKILLTEXT:-$PWD/skills/lem}
lead_brief=$SKILLTEXT/prompts/lead.md
# shellcheck disable=SC2016  # the backticks are the stage text's own marks around a command
if grep -qF 'decisions.py answer SLUG N' "$lead_brief" && grep -qF -- '`--instead TEXT`' "$lead_brief" && grep -qF 'his that answers no choice is logged with `decisions.py log SLUG --by owner`' "$lead_brief" \
  && ! grep -qE 'log it with `decisions.py log SLUG --by owner`|Log each answer with `decisions.py log' "$lead_brief" "$SKILLTEXT"/stages/*.md "$SKILLTEXT"/prompts/*.md; then
  pass "the lead's brief and Lem's stage write the owner's answer to a choice that waits with answer, --instead included, and log a word of his only when it answers no choice"
else
  fail "the owner's answer in the lead's brief and the stages: $(grep -n 'by owner' "$SKILLTEXT"/stages/*.md "$SKILLTEXT"/prompts/*.md)"
fi
# An answer and a timeout at one time: each reads the state inside the lock, so the record holds one outcome.
rfile=$DC/.git/lem/tasks/race-task/decisions.jsonl
decide ask race-task --what "The order of the rows" --option "by number" --option "by date" --recommended "by number" --why "It is the order of today." --said "The two personas split." >/dev/null
past "$rfile" 1
"$PY" -c 'import fcntl, sys, time; f = open(sys.argv[1], "w"); fcntl.flock(f, fcntl.LOCK_EX); print("held", flush=True); time.sleep(30)' "$DC/.git/lem/tasks/race-task/decisions.lock" > "$WORK/rlock.out" &
holder=$!
for _ in 1 2 3 4 5 6 7 8 9 10; do [ -s "$WORK/rlock.out" ] && break; sleep 0.2; done
"$PY" -B "$DECISIONS" --repo "$DC" answer race-task 1 --chose "by date" > "$WORK/race-answer.out" 2>&1 &
ra=$!
"$PY" -B "$DECISIONS" --repo "$DC" timeout race-task 1 > "$WORK/race-timeout.out" 2>&1 &
rt=$!
sleep 2
kill "$holder" 2>/dev/null || true; wait "$holder" 2>/dev/null || true
wait "$ra" || true; wait "$rt" || true
raced=$(grep -c '"kind": "timeout"' "$rfile" || true)/$(grep -c '"kind": "answered"' "$rfile" || true)/$(decide list race-task | field '(d[0]["state"], d[0].get("chose"), d[0].get("late", {}).get("chose"))' || true)
if [ "$raced" = "1/0/('timeout', 'by number', 'by date')" ]; then
  pass "an answer after the wait and a timeout that start at one time leave one timeout and one late answer, whichever takes the lock first"
else
  fail "an answer and a timeout at one time: $raced / $(cat "$rfile" "$WORK/race-answer.out" "$WORK/race-timeout.out")"
fi
# Two writers never take one number: while another process holds the lock, two writes wait, and then each gets its own.
"$PY" -c 'import fcntl, sys, time; f = open(sys.argv[1], "w"); fcntl.flock(f, fcntl.LOCK_EX); print("held", flush=True); time.sleep(30)' "$DC/.git/lem/tasks/other-task/decisions.lock" > "$WORK/dlock.out" &
holder=$!
for _ in 1 2 3 4 5 6 7 8 9 10; do [ -s "$WORK/dlock.out" ] && break; sleep 0.2; done
"$PY" -B "$DECISIONS" --repo "$DC" log other-task --what "first" --chose a --why b --by lead > "$WORK/dw1.out" 2>&1 &
w1=$!
"$PY" -B "$DECISIONS" --repo "$DC" log other-task --what "second" --chose a --why b --by lead > "$WORK/dw2.out" 2>&1 &
w2=$!
sleep 2
held=$(grep -c '' "$DC/.git/lem/tasks/other-task/decisions.jsonl" 2>/dev/null || true)
kill "$holder" 2>/dev/null || true; wait "$holder" 2>/dev/null || true
wait "$w1" || true; wait "$w2" || true
numbers=$(decide list other-task | field 'sorted(c["id"] for c in d)')
if [ "${held:-0}" = 0 ] && [ "$numbers" = "[1, 2]" ]; then
  pass "two writes while another process holds the lock wait for it, and then each takes a number of its own"
else
  fail "the lock of decisions.jsonl: held $held / $numbers / $(cat "$WORK/dw1.out" "$WORK/dw2.out")"
fi
# The wait is the settings' flow.decision_wait: init writes it, a choice takes it, and a value that is no whole number of 1 or more is refused.
written=$(grep -c '^decision_wait = 15$' "$DC/.lem/project.toml")
sed -i.bak 's|^decision_wait = 15$|decision_wait = 1|' "$DC/.lem/project.toml" && rm "$DC/.lem/project.toml.bak"
short=$(decide ask other-task --what "x" --option a --option b --recommended a --why w --said s | field '(d["wait_minutes"], (__import__("datetime").datetime.strptime(d["deadline"], "%Y-%m-%dT%H:%M:%SZ") - __import__("datetime").datetime.strptime(d["at"], "%Y-%m-%dT%H:%M:%SZ")).seconds)')
wrong=""
for value in 0 -5 true '"15"' 2.5; do
  sed -i.bak "s|^decision_wait = .*\$|decision_wait = $value|" "$DC/.lem/project.toml" && rm "$DC/.lem/project.toml.bak"
  said=$(project --repo "$DC" show 2>&1 || true)
  if [ "$(status_of project --repo "$DC" show)" = 1 ] && grep -q "flow.decision_wait = .* must be a whole number of minutes, 1 or more" <<<"$said"; then :; else wrong="$wrong $value"; fi
done
refused=$(decide ask other-task --what "x" --option a --option b --recommended a --why w --said s 2>&1 || true)
sed -i.bak 's|^decision_wait = .*$|decision_wait = 15|' "$DC/.lem/project.toml" && rm "$DC/.lem/project.toml.bak"
if [ "$written" = 1 ] && [ "$short" = "(1, 60)" ] && [ -z "$wrong" ] && grep -q "flow.decision_wait" <<<"$refused" && [ "$(project --repo "$DC" show | field 'd["flow"]["decision_wait"]')" = 15 ]; then
  pass "init writes flow.decision_wait, a choice waits as many minutes as it says, and a value that is not a whole number of 1 or more is refused, by the settings and by a choice"
else
  fail "flow.decision_wait: $written / $short / wrong:$wrong / $refused"
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
  && [ "$(project --repo "$PPL" show | field 'sorted(d["paths"]["personas"])')" = "['exists', 'path']" ]; then
  pass "in a repository that uses Lem the machine check says when the project has no personas or one, finds the cast of a worktree that is older than it, never fails for it, and has no such row anywhere else"
else
  fail "the project's personas: $none / $one / $two / $older / $outside"
fi
git -C "$PPL" worktree remove --force "$WORK/people-wt"

# The backlog's sorting reads the folder the project's settings name, not a fixed one.
BKL=$WORK/backlog-repo
git init -q -b main "$BKL" && commit "$BKL" start
project --repo "$BKL" init --base main >/dev/null
sed -i.bak 's|^backlog = "docs/backlog"$|backlog = "notes/later"|' "$BKL/.lem/project.toml" && rm "$BKL/.lem/project.toml.bak"
mkdir -p "$BKL/notes/later" "$BKL/docs/backlog" && printf '%s\n' '# A slow report' 'It takes nine seconds.' > "$BKL/notes/later/slow-report.md" && echo '# Not the backlog' > "$BKL/docs/backlog/other.md"
printf '%s\n' '#!/bin/sh' 'cat > /dev/null' 'printf "{\"answers\": {\"triage\": {\"choice\": \"agent\", \"confidence\": 0.9, \"probabilities\": {\"agent\": 0.9}}}}"' > "$WORK/jevbin/triage-jev"
chmod +x "$WORK/jevbin/triage-jev"
TRIAGE=$PWD/skills/lem-backlog/scripts/triage.py
out=$(env JEV_BIN="$WORK/jevbin/triage-jev" "$PY" -B "$TRIAGE" refresh --json --repo "$BKL" 2>/dev/null)
err=$(env JEV_BIN="$WORK/jevbin/triage-jev" "$PY" -B "$TRIAGE" item other --repo "$BKL" 2>&1 || true)
if grep -q '"slow-report"' <<<"$out" && ! grep -q '"other"' <<<"$out" && grep -q "no item other.md in $BKL/notes/later" <<<"$err"; then
  pass "the backlog's sorting reads the items of the folder the project's settings name"
else
  fail "the backlog's folder: $out / $err"
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
feed() { "$PY" -c 'import json, re, sys; d = json.loads(re.fullmatch(r"lemBacklog\((.*)\);\n", open(sys.argv[1], encoding="utf-8").read().replace("<\\/", "</"), re.S).group(1)); print(eval(sys.argv[2], {"d": d, "by": {i["slug"]: i for i in d["items"]}}))' "$BKB/.git/lem/backlog.js" "$1"; }
if [ "$(feed '(d["folder"], d["judged"], sorted(by))')" = "('docs/backlog', False, ['a b;c', 'broken-link', 'dark-theme', 'export-drops-columns', 'folder-item', 'new-from-a-landing', 'slow-report', 'which-currency'])" ] \
  && [ "$(feed '(by["export-drops-columns"]["title"], by["export-drops-columns"]["worth"], by["export-drops-columns"]["where_problem"], by["export-drops-columns"]["state"], by["export-drops-columns"]["path"])')" = "('The export drops custom columns', 'yes', '', '', 'docs/backlog/export-drops-columns.md')" ] \
  && [ "$(feed '(by["slow-report"]["where_problem"], by["which-currency"]["where_problem"], by["dark-theme"]["worth"], by["dark-theme"]["where"])')" = "('the file is not there', 'not in the file: no_such_name', 'no', '')" ] \
  && [ "$(feed '(by["new-from-a-landing"]["worth"], by["new-from-a-landing"]["state"], by["a b;c"]["title"])')" = "('unset', 'new', 'a b;c')" ] \
  && [ "$(feed '(by["broken-link"]["state"], by["folder-item"]["state"], "cannot be read" in by["broken-link"]["body"])')" = "('unreadable', 'unreadable', True)" ] \
  && ! grep -q '</script>' "$BKB/.git/lem/backlog.js" && [ "$(feed '"</script><b>not markup</b>" in by["export-drops-columns"]["body"]')" = True ]; then
  pass "the board's backlog file has each item with its verdict, whether its place in the code is still there and whether git has it; an item that cannot be read is listed as such; and no text of an item can end the script that carries it"
else
  fail "backlog.js: $(head -c 600 "$BKB/.git/lem/backlog.js")"
fi
# A backlog folder that git does not know yet: its first item is new, though git names only the folder.
FIRST=$WORK/backlog-first
git init -q -b main "$FIRST" && commit "$FIRST" start && project --repo "$FIRST" init --base main >/dev/null && mkdir -p "$FIRST/docs/backlog"
printf '%s\n' '# The first item' '' 'No frontmatter at all.' > "$FIRST/docs/backlog/first.md"
# A run that opens nothing keeps the session the board names: the page types an ask into it.
env AGTERM_SESSION_ID=LEM-SESSION AGTERM_SOCKET=/nowhere "$PY" -B "$PWD/skills/lem/scripts/board.py" --repo "$FIRST" --no-open >/dev/null
env AGTERM_SESSION_ID=A-LEAD-SESSION AGTERM_SOCKET=/nowhere "$PY" -B "$PWD/skills/lem/scripts/board.py" --repo "$FIRST" --no-open >/dev/null
env -u AGTERM_SESSION_ID -u AGT_SESSION_ID "$PY" -B "$PWD/skills/lem/scripts/board.py" --repo "$FIRST" --no-open >/dev/null
if grep -q '"state": "new"' "$FIRST/.git/lem/backlog.js" && grep -q '"title": "The first item"' "$FIRST/.git/lem/backlog.js" && grep -q '"session": "LEM-SESSION"' "$FIRST/.git/lem/meta.js"; then
  pass "the first item of a backlog folder that git does not know yet is new, and a run that opens nothing keeps the session the board named before"
else
  fail "a first backlog item, and the session after --no-open: $(cat "$FIRST/.git/lem/backlog.js" "$FIRST/.git/lem/meta.js" | head -c 500)"
fi
printf '%s\n' '{"export-drops-columns": {"verdict": "agent", "confidence": 0.86}, "which-currency": {"verdict": "owner", "confidence": 0.58}, "slow-report": {"verdict": "nonsense"}, "gone-item": {"verdict": "agent"}}' > "$BKB/.git/backlog-triage.json"
"$PY" -B "$PWD/skills/lem/scripts/board.py" --repo "$BKB" --no-open >/dev/null
kept=$(cat "$BKB/.git/backlog-triage.json")
if [ "$(feed '(d["judged"], by["export-drops-columns"]["who"], by["export-drops-columns"]["confidence"], by["which-currency"]["who"], by["slow-report"]["who"])')" = "(True, 'agent', 0.86, 'owner', '')" ] \
  && [ "$kept" = "$(cat "$BKB/.git/backlog-triage.json")" ] && [ -z "$(git -C "$BKB" status --porcelain -- app)" ]; then
  pass "with verdicts of the backlog's sorting the file says who can act on each item, an unknown verdict is none, and the board reads that record without a change to it"
else
  fail "backlog.js with verdicts: $(head -c 400 "$BKB/.git/lem/backlog.js")"
fi

# The board: board.py writes the page and what it reads beside the events, and the page draws them.
BOARD=$PWD/skills/lem/scripts/board.py
board() { env -u AGTERM_SESSION_ID -u AGTERM_SOCKET -u AGT_SESSION_ID -u AGT_SOCKET "$PY" -B "$BOARD" "$@"; }
# The test's settings file is not committed, so a worktree has none: the worktree run shows where
# the page goes and whose name it carries, the run in the main checkout shows the base.
out=$(board --repo "$WORK/wt" --no-open)
named=$(cat "$OLD/.git/lem/meta.js")
board --repo "$OLD" --no-open >/dev/null
if [ "$(field 'd["page"]' <<<"$out")" = "$OLD/.git/lem/board.html" ] && cmp -s "$OLD/.git/lem/board.html" "$PWD/skills/lem/assets/board.html" \
  && cmp -s "$OLD/.git/lem/lem.css" "$PWD/skills/lem/assets/lem.css" \
  && [ "$named" = 'lemMeta({"repo": "old", "base": null, "session": ""});' ] \
  && [ "$(cat "$OLD/.git/lem/meta.js")" = 'lemMeta({"repo": "old", "base": "master", "session": ""});' ]; then
  pass "board --no-open writes the page and the stylesheet it links into the shared state folder, from a worktree too, with the repository's name and its base"
else
  fail "board --no-open: $out / $named / $(cat "$OLD/.git/lem/meta.js" 2>&1)"
fi
out=$(board --repo "$OLD" --no-open --task with-a-worktree)
err=$(board --repo "$OLD" --no-open --task no-such-task 2>&1 || true)
if [ "$(field 'd["page"]' <<<"$out")" = "$OLD/.git/lem/task-with-a-worktree.html" ] && [ "$(field 'd["name"]' <<<"$out")" = "with-a-worktree board" ] \
  && [ "$(status_of board --repo "$OLD" --no-open --task no-such-task)" = 1 ] && grep -q "the tasks are: .*second-task" <<<"$err" && [ ! -e "$OLD/.git/lem/task-no-such-task.html" ]; then
  pass "a task's board is a copy named after the task, and an unknown task is refused with the names of the known ones"
else
  fail "board --task: $out / $err"
fi
if [ "$(status_of board --repo "$OLD")" = 1 ]; then pass "outside an agterm session board opens nothing and says so"; else fail "board outside agterm"; fi
board --repo "$OLD" --no-open --demo >/dev/null
board --repo "$OLD" --no-open --task with-a-worktree >/dev/null
if grep -q '"demo": true' "$OLD/.git/lem/meta.js" && [ -f "$OLD/.git/lem/demo" ]; then
  pass "board --demo marks the state folder's tasks as examples, and a later open with no flag keeps the mark"
else
  fail "board --demo: $(cat "$OLD/.git/lem/meta.js")"
fi
rm "$OLD/.git/lem/demo"
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
  '{"id": "PX", "name": "Lem board", "content": "page", "parent": "AAA", "htmlOverlays": [{"file": "/elsewhere/.git/lem/board.html"}]},' \
  "{\"id\": \"PA\", \"name\": \"Lem board\", \"content\": \"page\", \"parent\": \"AAA\", \"htmlOverlays\": [{\"file\": \"$OLD/.git/lem/board.html\"}]}," \
  "{\"id\": \"PB\", \"name\": \"Lem board\", \"content\": \"page\", \"parent\": \"BBB\", \"htmlOverlays\": [{\"file\": \"$OLD/.git/lem/board.html\"}]}]}]}}}" > "$WORK/tree.json"
opened() { : > "$WORK/calls"; env PATH="$FAKE:$PATH" AGT_CALLS="$WORK/calls" AGT_TREE="$WORK/tree.json" AGTERM_SESSION_ID="$1" AGTERM_SOCKET=/none "$PY" -B "$BOARD" --repo "$OLD"; }
out=$(opened AAA)
if [ "$(field '(d["companion"], d["reloaded"], d["name"])' <<<"$out")" = "('PA', True, 'Lem board · old')" ] && grep -q "session overlay reload --target PA" "$WORK/calls" \
  && grep -q "session rename Lem board · old --target PA" "$WORK/calls" && ! grep -q "session close" "$WORK/calls" && ! grep -q "PX\|PB" "$WORK/calls"; then
  pass "a board is known by the file it shows: this repository's is reloaded and gets the repository's name, and another repository's board under the same top session is left alone"
else
  fail "board reload: $out / $(cat "$WORK/calls")"
fi
out=$(opened CCC)
if [ "$(field '(d["companion"], d["reloaded"], d["parent"])' <<<"$out")" = "('NEW', False, 'CCC')" ] && grep -q "session overlay open --html $OLD/.git/lem/board.html .* --companion --target CCC" "$WORK/calls" \
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
if [ -n "$chrome" ]; then
  draw() {
    "$chrome" --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" \
      --virtual-time-budget=5000 --dump-dom "file://$OLD/.git/lem/$1.html" > "$WORK/$1.dom" 2>/dev/null || true
  }
  draw board
  if [ ! -s "$WORK/board.dom" ]; then
    # A Chrome that cannot start (a sandbox that forbids it) says nothing about the page.
    printf 'SKIP the board pages: %s printed no page\n' "$chrome"
  elif why=$("$PY" -I -B -c "$SHOWN" "$WORK/board.dom" "Lem · old" "1 waits for you, 1 builds, 1 in checks and review" "Report dates stay whole" \
    "Owner lands it" "Tell Lem in its session to land it." "!Demo data" "Keep report dates whole." \
    "Building: task 2 of 3" "Second task" "Ready for its checks: the gate was cut off" "1 of 4" "1 waits for the merge" "1 not green" "tasks land on master" "!Review queue"); then
    pass "the board draws each task in its lane from the events, with what waits for the merge and whether it is green"
  else
    fail "the board: missing $why"
  fi
  draw task-with-a-worktree
  if [ ! -s "$WORK/task-with-a-worktree.dom" ]; then
    printf 'SKIP the board of one task: %s printed no page\n' "$chrome"
  elif why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-with-a-worktree.dom" "With a worktree · Dropped" "fix/with-a-worktree" "fix: 0123 is a string" \
    "make test" "5 passed in 0.1s" "the test is over" "All tasks" "gate green: 1" "!gate red"); then
    pass "a task's board draws its state blocks, its newest commit and the gate's newest result, not a failure a later run repaired"
  else
    fail "a task's board: missing $why"
  fi
  board --repo "$OLD" --no-open --task owner-lands-it >/dev/null
  draw task-owner-lands-it
  if [ -s "$WORK/task-owner-lands-it.dom" ] && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-owner-lands-it.dom" "Owner lands it · Waits for the merge" "3/3" "Where you answer:" "!2/3" \
    "round 1, one read: clean, 0 must-fix, 1 should, 0 nit" "answered: codex" "Proposed: not green" "story 1 changed during the build: y is taken."); then
    pass "a task that waits for the merge keeps the phase and the plan tasks it reached, and its board shows its review and why it is not green"
  elif [ -s "$WORK/task-owner-lands-it.dom" ]; then
    fail "a task that waits for the merge: missing $why"
  fi
  # A closed task looked at much later: its time axis ends at its last block and has no line for now.
  mkdir -p "$WORK/aged" && cp "$OLD/.git/lem/task-with-a-worktree.html" "$OLD/.git/lem/meta.js" "$WORK/aged/"
  "$PY" -c 'import json, sys
rows = [json.loads(line) for line in open(sys.argv[1]) if line.strip()]
mine = [r for r in rows if r["task"] == "with-a-worktree"]
for i, r in enumerate(mine): r["ts"] = "2026-01-10T12:00:%02dZ" % i
open(sys.argv[2], "w").write("".join("lemEvent(%s);\n" % json.dumps(r) for r in mine))' "$OLD/.git/lem/events.jsonl" "$WORK/aged/events.js"
  "$chrome" --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" \
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
  printf 'lemMeta({"repo": \n' > "$OLD/.git/lem/meta.js"
  draw board
  if [ -s "$WORK/board.dom" ] && grep -q "<title>PROBLEM" "$WORK/board.dom" && grep -q "meta.js does not parse" "$WORK/board.dom"; then
    pass "a meta.js that does not parse is shown as a problem"
  elif [ -s "$WORK/board.dom" ]; then
    fail "a broken meta.js shows no problem: $(grep -o '<title>[^<]*' "$WORK/board.dom")"
  fi
  board --repo "$OLD" --no-open >/dev/null
  # The board of one task shows its stories, each with its tests and what the last check gave.
  "$PY" -B "$BOARD" --repo "$ST" --task export-has-the-gift-note --no-open >/dev/null
  "$chrome" --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" \
    --virtual-time-budget=5000 --dump-dom "file://$ST/.git/lem/task-export-has-the-gift-note.html" > "$WORK/stories.dom" 2>/dev/null || true
  if [ ! -s "$WORK/stories.dom" ]; then
    printf 'SKIP the stories on the board: %s printed no page\n' "$chrome"
  elif why=$("$PY" -I -B -c "$SHOWN" "$WORK/stories.dom" "Stories" "feature, because the export gets a new column and an empty cell." \
    'A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has that text in its row.' "sh tests/gift.sh" \
    "passes on the branch, fails on the base commit (checked on " "held by its tests" "An order with no gift note has an empty cell"); then
    pass "the board of one task shows its stories as the plan has them, each with its tests and the result of the last check"
  else
    fail "the stories on the board: missing $why"
  fi
  # A story that changed after the check has no check: the old result is not shown for it.
  "$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("has that text in its row.", "has that text in the third cell of its row."))' "$stw/docs/plans/20261115-export-has-the-gift-note.md"
  stories record export-has-the-gift-note >/dev/null && git -C "$stw" checkout -q -- docs
  "$chrome" --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" \
    --virtual-time-budget=5000 --dump-dom "file://$ST/.git/lem/task-export-has-the-gift-note.html" > "$WORK/stories-changed.dom" 2>/dev/null || true
  if [ -s "$WORK/stories-changed.dom" ] && why=$("$PY" -I -B -c "$SHOWN" "$WORK/stories-changed.dom" "in the third cell of its row" "not checked yet" "!held by its tests"); then
    pass "after a story changed, the board shows no result of the older check for any story"
  elif [ -s "$WORK/stories-changed.dom" ]; then
    fail "the stories on the board after a change: missing $why"
  fi
  # The backlog tab: drawn from backlog.js, and its one action types the item into Lem's session.
  "$chrome" --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" \
    --virtual-time-budget=5000 --dump-dom "file://$BKB/.git/lem/board.html#backlog" > "$WORK/backlog.dom" 2>/dev/null || true
  if [ ! -s "$WORK/backlog.dom" ]; then
    printf 'SKIP the backlog tab: %s printed no page\n' "$chrome"
  elif why=$("$PY" -I -B -c "$SHOWN" "$WORK/backlog.dom" "Backlog · backlog-board" "8 items in docs/backlog" "2 point at a place that is gone" "2 cannot be read" "sorted by who can act" \
    "Needs you" "An agent can take it" "Not judged yet" "Decided against" "The export drops custom columns" "an agent can take it · 0.86" \
    "app/report.py:monthly · the file is not there" "new, not committed" "worth: unset" "!Waits for something"); then
    pass "the backlog tab draws the items in groups by who can act, each with its word and its count, and shows a place that is gone"
  else
    fail "the backlog tab: missing $why"
  fi
  cat > "$BKB/.git/lem/probe.html" <<'PROBE'
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
  "$PY" -c 'import json, re, sys; s = open(sys.argv[1]).read(); d = json.loads(re.fullmatch(r"lemMeta\((.*)\);\n", s, re.S).group(1)); d["session"] = "LEM1"; open(sys.argv[1], "w").write("lemMeta(%s);\n" % json.dumps(d))' "$BKB/.git/lem/meta.js"
  "$chrome" --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" --allow-file-access-from-files \
    --virtual-time-budget=40000 --dump-dom "file://$BKB/.git/lem/probe.html" > "$WORK/probe.dom" 2>/dev/null || true
  rm -f "$BKB/.git/lem/probe.html"
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
# The landing: land.py takes one task from `ready` through the machine checks and one read to a pull
# request, or to a branch that is ready to land, and from there to the base branch.
LAND=$PWD/skills/lem/scripts/land.py
land() { "$PY" -B "$LAND" "$@"; }
ORIGIN=$WORK/origin.git
SHOP=$WORK/shop
git init -q --bare -b main "$ORIGIN"
git clone -q "$ORIGIN" "$SHOP" 2>/dev/null
ident() { git -C "$1" config user.name t; git -C "$1" config user.email t@t; }
ident "$SHOP"
project --repo "$SHOP" init --base main --reviewer codex >/dev/null
shop_settings() {
  printf '%s\n' '[branch]' 'base = "main"' "land = \"$1\"" "history = \"$2\"" 'protected = ["release"]' \
    '[gate]' 'commands = ["test -f ok.txt", "echo 7 passed"]' 'ignores = ["docs/*"]' > "$SHOP/.lem/project.toml"
}
shop_settings owner keep
mkdir -p "$SHOP/docs" "$SHOP/.lem/styleguide" && echo guide > "$SHOP/docs/guide.md" && echo one > "$SHOP/app.txt"
printf '%s\n' '---' 'paths:' '  - "tests/**"' '---' 'A test names what it checks.' > "$SHOP/.lem/styleguide/tests.md"
printf '%s\n' '---' 'paths:' '  - "billing/**"' '---' 'Money is an integer.' > "$SHOP/.lem/styleguide/money.md"
git -C "$SHOP" add -A && git -C "$SHOP" commit -q -m "chore: start" && git -C "$SHOP" push -q origin main
# plan_in TREE SLUG TEST: the task's plan, with one story that TEST holds; TEST is `no test: REASON` for a story with none
plan_in() {
  local held="   - test: \`$3\` in \`tests/$2.sh\`"
  case "$3" in "no test:"*) held="   - $3" ;; esac
  mkdir -p "$1/docs/plans" "$1/tests"
  printf '%s\n' "# $2" '' '## Stories' '' 'Kind: correction, because the request is one sentence.' '' \
    '1. The file holds the word the owner asked for.' "$held" '' '## Tasks' '' '1. The change.' > "$1/docs/plans/20261115-$2.md"
}
# task_in REPO SLUG FILE TEXT: a task with a worktree, one commit that writes FILE, its plan and the test of its story, and the state `ready`
task_in() {
  local tree
  project --repo "$1" task-dir "$2" --ask "Put $4 into $3." >/dev/null
  tree=$(project --repo "$1" worktree-dir "$2")
  git -C "$1" worktree add -q "$tree" -b "fix/$2" main
  plan_in "$tree" "$2" "sh tests/$2.sh"
  printf '%s\n' "$4" > "$tree/$3" && echo "grep -qx $4 $3" > "$tree/tests/$2.sh"
  git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: $2"
  project --repo "$tree" state "$2" ready "the report is written" >/dev/null
}
open_task() { task_in "$SHOP" "$@"; }
status_in() { project --repo "$1" tasks | field "next(t[\"status\"] for t in d if t[\"slug\"] == \"$2\")"; }
status() { status_in "$SHOP" "$1"; }
kept_in() { "$PY" -c 'import json, sys; print(json.load(open(sys.argv[1])).get(sys.argv[2]))' "$1/.git/lem/tasks/$2/landing.json" "$3"; }
kept() { kept_in "$SHOP" "$@"; }
# the three machine steps, a read that found nothing, and the proposal, for the tests that are about a later step
checked() { land --repo "$SHOP" start "$1" >/dev/null && land --repo "$SHOP" base "$1" >/dev/null && land --repo "$SHOP" gate "$1" >/dev/null; }
# record N JSON: the file that says what a review was and what it found, as the Nth start of the task's review
record() {
  "$PY" -c 'import json, sys; json.dump({"attempt": int(sys.argv[1]), **json.loads(sys.argv[2])}, open(sys.argv[3], "w"))' "$1" "$2" "$WORK/record.json"
  echo "$WORK/record.json"
}
# clean N: the record of one read that found nothing
clean() { record "$1" '{"kind": "read", "answered": ["codex"]}'; }
read_clean() { land --repo "$SHOP" read "$1" --record "$(clean "${2:-1}")" >/dev/null; }
propose() { land --repo "$SHOP" propose "$1" --title "fix: $1" --notes "$NOTES" >/dev/null; }
NOTES=$WORK/notes.md
printf '%s\n' '## Decisions' '' 'none' '' '## Left open' '' 'none' '' '## Worth a look' '' '- the one line of the file.' '' '## Filed in the backlog' '' 'none' '' '## Not done' '' 'none' > "$NOTES"

open_task first-change ok.txt yes
open_task second-change app.txt two
if [ "$(status_of land --repo "$SHOP" gate first-change)" = 1 ] && [ "$(status_of land --repo "$SHOP" base first-change)" = 1 ] \
  && [ "$(status_of land --repo "$SHOP" read first-change)" = 1 ] && [ "$(status_of land --repo "$SHOP" propose first-change --title x --notes "$NOTES")" = 1 ] \
  && [ "$(status_of land --repo "$SHOP" land first-change --by owner)" = 1 ] && [ "$(status first-change)" = ready ]; then
  pass "no step runs on a task that did not take the landing line, and the owner's word lands nothing that was not proposed"
else
  fail "land steps before start"
fi
out=$(land --repo "$SHOP" start first-change)
err=$(land --repo "$SHOP" start second-change 2>&1 || true)
if [ "$(field '(d["remote"], d["forge"])' <<<"$out")" = "(True, None)" ] && [ "$(status first-change)" = landing ] && [ "$(status_of land --repo "$SHOP" start second-change)" = 1 ] \
  && grep -q "first-change is in .landing." <<<"$err" && [ "$(status second-change)" = ready ]; then
  pass "start puts one task in landing, and a second task is refused while it is there"
else
  fail "land start: $out / $err"
fi
if [ "$(status_of land --repo "$SHOP" gate first-change)" = 1 ]; then pass "the gate refuses to run before the base was brought in"; else fail "gate before base"; fi
out=$(land --repo "$SHOP" base first-change)
if [ "$(field '(d["ahead"], d["moved"], d["onto"])' <<<"$out")" = "(1, False, 'origin/main')" ]; then
  pass "base rebases onto the remote's base branch and says how many commits the branch adds"
else
  fail "land base: $out"
fi
out=$(land --repo "$SHOP" gate first-change)
tip=$(git -C "$SHOP/.lem/worktrees/first-change" rev-parse HEAD)
if [ "$(field '(d["green"], [c["exit"] for c in d["commands"]], d["commands"][1]["last"])' <<<"$out")" = "(True, [0, 0], '7 passed')" ] \
  && [ "$(kept first-change gated)" = "$tip" ] && [ "$(cat "$SHOP/.git/lem/tasks/first-change/gate/02.log")" = "7 passed" ] \
  && [ "$(grep -c '"event": "gate", "task": "first-change"' "$SHOP/.git/lem/events.jsonl")" = 2 ]; then
  pass "gate runs every command with its output in a file, keeps the last line, logs each result and records the green tip"
else
  fail "land gate: $out"
fi
if [ "$(field '(d["stories"]["ok"], [(t["story"], t["problem"]) for t in d["stories"]["tests"]], d["bar"], d["size"]["files"], d["size"]["in_parts"])' <<<"$out")" \
  = "(True, [(1, None)], {'lowered': [], 'not_covered': [], 'own_patterns': 0}, 3, False)" ] && grep -q '"event": "task.red", "task": "first-change"' "$SHOP/.git/lem/events.jsonl"; then
  pass "after the commands the gate proves each story's test on the branch and on the base commit, looks for a lowered bar and counts the size"
else
  fail "the machine checks after the gate's commands: $out"
fi
# A review before anything is proposed: the script says the least it may be, and what a reviewer gets.
err=$(land --repo "$SHOP" propose first-change --title "fix: the file is there" --notes "$NOTES" 2>&1 || true)
out=$(land --repo "$SHOP" read first-change)
base=$(git -C "$SHOP" rev-parse origin/main)
if grep -q "a review is due before anything is proposed, one read at the least" <<<"$err" && [ "$(status first-change)" = landing ] \
  && [ "$(field '(d["due"], d["floor"], d["round"], d["in_parts"], sorted(d["inputs"]), d["inputs"]["range"], [r.split("/.lem/")[-1] for r in d["inputs"]["rules"]])' <<<"$out")" \
  = "('review', 'read', 1, False, ['bar', 'plan', 'range', 'review', 'rules', 'words', 'worktree'], '$base..$tip', ['styleguide/tests.md'])" ] \
  && [ "$(cat "$(field 'd["inputs"]["words"]' <<<"$out")")" = "Put yes into ok.txt." ] && [ -f "$(field 'd["inputs"]["plan"]' <<<"$out")" ] \
  && [ "$(field 'd["inputs"]["review"]' <<<"$out")" = "$SHOP/.revmux" ]; then
  pass "nothing is proposed before its review; for a usual request the floor is one read, and a reviewer gets the owner's words, the plan, the range, the rule files of the changed files and the folder of the review tool"
else
  fail "the read that is due: $err / $out"
fi
err=$(land --repo "$SHOP" read first-change --record "$(record 1 '{"kind": "read", "answered": [], "must_fix": 1}')" 2>&1 || true)
shape=$(land --repo "$SHOP" read first-change --record "$(record 1 '{"kind": "glance", "answered": ["codex"]}')" 2>&1 || true)
late=$(land --repo "$SHOP" read first-change --record "$(clean 2)" 2>&1 || true)
out=$(land --repo "$SHOP" read first-change --record "$(record 1 '{"kind": "read", "answered": ["codex"], "should": 1}')")
if grep -q "findings and no source that answered" <<<"$err" && grep -q ".kind. is one of read, round, full" <<<"$shape" \
  && grep -q "the record says attempt 2, and the next review of this task is attempt 1" <<<"$late" \
  && [ "$(field '(d["recorded"]["round"], d["recorded"]["kind"], d["recorded"]["verdict"], d["recorded"]["should"], d["next"])' <<<"$out")" = "(1, 'read', 'clean', 1, 'none')" ] \
  && [ "$(grep -c '"event": "review", "task": "first-change"' "$SHOP/.git/lem/events.jsonl")" = 1 ] && [ "$(status_of land --repo "$SHOP" read first-change --record "$(clean 2)")" = 1 ]; then
  pass "a review is written down from a file, with its round, its kind, who answered and its counts; a record that does not have the form or the number of this review is refused, and a change that was reviewed clean is not reviewed again"
else
  fail "recording a read: $err / $out"
fi
printf '%s\n' '## Decisions' '' 'none' > "$WORK/thin.md"
err=$(land --repo "$SHOP" propose first-change --title "fix: the file is there" --notes "$WORK/thin.md" 2>&1 || true)
out=$(land --repo "$SHOP" propose first-change --title "fix: the file is there" --notes "$NOTES")
text=$SHOP/.git/lem/tasks/first-change/pr.md
if grep -q "the notes lack ## Left open, ## Worth a look, ## Filed in the backlog, ## Not done" <<<"$err" && [ "$(field '(d["pull_request"], d["green"], d["not_green"], d["branch"])' <<<"$out")" = "(None, True, [], 'fix/first-change')" ] \
  && [ "$(status first-change)" = open ] && [ "$(kept first-change proposed)" = "$tip" ] && [ "$(head -1 "$text" | cut -c1-10)" = '**Green.**' ] && grep -q '^green$' "$SHOP/.git/lem/tasks/first-change/state.md" \
  && [ "$(grep '^## ' "$text" | tr '\n' '|')" = "## The request|## Stories|## Checks|## Decisions of the build|## Decisions|## Left open|## Worth a look|## Filed in the backlog|## Not done|" ] \
  && [ "$(sed -n '/^## Decisions of the build$/,/^## Decisions$/p' "$text" | sed -n 3p)" = none ] && head -1 "$text" | grep -qF 'no story changed, and no decision was taken by timeout.' \
  && grep -q '^> Put yes into ok.txt\.$' "$text" && grep -q '^1\. The file holds the word the owner asked for\.$' "$text" \
  && grep -q 'sh tests/first-change.sh.: passes on the branch, fails on the base commit' "$text" && grep -q '^- gate, .echo 7 passed.: 7 passed$' "$text" \
  && grep -q "^- the stories' tests: 1 pass on the branch and fail on the base commit$" "$text" && grep -q '^- the bar: not lowered$' "$text" \
  && grep -q '^- the review, round 1 (one read; answered: codex): clean, 0 must-fix, 1 should, 0 nit$' "$text" && grep -q '^- careful: no$' "$text" && grep -q '^- the one line of the file\.$' "$text" \
  && ! grep -q 'plan talk' "$text" && ! grep -q '"event": "plan.talk", "task": "first-change"' "$SHOP/.git/lem/events.jsonl"; then
  pass "with no forge the branch is marked ready: the task is open, and the text for the owner says green first, then holds his words, the stories with their tests, each check with what it returned, the decisions of the record (none here), then the notes; a plain request of one task needs no plan talk, and its text has no line of one"
else
  fail "propose: $err / $out / $(cat "$text" 2>/dev/null)"
fi
err=$(land --repo "$SHOP" land first-change --by agent 2>&1 || true)
if [ "$(status_of land --repo "$SHOP" land first-change --by agent)" = 1 ] && grep -q "a person merges" <<<"$err" \
  && [ "$(git -C "$ORIGIN" rev-parse main)" = "$(git -C "$SHOP" rev-parse main)" ] && [ "$(status first-change)" = open ]; then
  pass "an agent lands nothing when the settings say that a person merges"
else
  fail "land with branch.land = owner: $err"
fi
shop_settings agent keep
if [ "$(status_of land --repo "$SHOP" land first-change --by agent --message "fix: x")" = 1 ]; then
  pass "a commit subject is refused when the branch's own commits land"
else
  fail "land --message with history = keep"
fi
# The base moves after the gate ran: by a file the gate reads, then only by one it does not.
other=$WORK/other
git clone -q "$ORIGIN" "$other" && ident "$other"
echo late > "$other/late.txt" && git -C "$other" add -A && git -C "$other" commit -q -m "feat: late" && git -C "$other" push -q origin main
err=$(land --repo "$SHOP" land first-change --by agent 2>&1 || true)
if [ "$(status_of land --repo "$SHOP" land first-change --by agent)" = 1 ] && grep -q "moved after the gate ran, by files the gate reads (late.txt)" <<<"$err" \
  && grep -q "run .land.py start., .land.py base. and .land.py gate. again" <<<"$err" && [ "$(status first-change)" = open ]; then
  pass "land refuses when the base moved by a file the gate reads, and says which steps run again"
else
  fail "land after the base moved: $err"
fi
land --repo "$SHOP" start first-change >/dev/null && land --repo "$SHOP" base first-change >/dev/null
if [ "$(status first-change)" = landing ] && [ "$(kept first-change gated)" = None ] && [ "$(status_of land --repo "$SHOP" land first-change --by agent)" = 1 ] \
  && [ "$(status_of land --repo "$SHOP" propose first-change --title x --notes "$NOTES")" = 1 ]; then
  pass "an open task takes the landing line again, and a new base forgets the gate's result, so nothing is proposed or landed before a new one"
else
  fail "base after a green gate keeps the result"
fi
land --repo "$SHOP" gate first-change >/dev/null
out=$(land --repo "$SHOP" read first-change)
if [ "$(field '(d["due"], d["why"])' <<<"$out")" = "('none', 'round 1 reviewed this change and left no must-fix')" ] && propose first-change && [ "$(status first-change)" = open ]; then
  pass "a rebase that changes nothing of the change does not undo its review"
else
  fail "the read after a rebase: $out"
fi
echo more >> "$other/docs/guide.md" && git -C "$other" add -A && git -C "$other" commit -q -m "docs: more" && git -C "$other" push -q origin main
out=$(land --repo "$SHOP" land first-change --by agent)
if [ "$(field '(d["pushed"], d["arrived"], d["left_behind"])' <<<"$out")" = "(True, ['docs/guide.md'], None)" ] && [ "$(status first-change)" = landed ] \
  && [ "$(git -C "$ORIGIN" log -1 --format=%s main)" = "fix: first-change" ] && [ "$(git -C "$SHOP" rev-parse main)" = "$(git -C "$ORIGIN" rev-parse main)" ] \
  && [ -f "$SHOP/ok.txt" ] && [ -f "$SHOP/late.txt" ]; then
  pass "where the settings allow it an agent lands a request that is green and not careful; a base that moved only by files the gate ignores still lands: pushed, the main checkout fast-forwarded, the state landed"
else
  fail "land: $out"
fi
# A clean that was cut off after the worktree went: the next run still knows the branch.
git -C "$SHOP" worktree remove "$SHOP/.lem/worktrees/first-change"
out=$(land --repo "$SHOP" clean first-change)
if [ "$(field '(d["worktree"], d["branch"])' <<<"$out")" = "(False, 'fix/first-change')" ] && [ -z "$(git -C "$SHOP" branch --list fix/first-change)" ] \
  && [ -d "$SHOP/.git/lem/tasks/first-change" ] && [ "$(field '(d["worktree"], d["branch"])' <<<"$(land --repo "$SHOP" clean first-change)")" = "(False, None)" ]; then
  pass "clean removes the landed task's branch when its worktree is already gone, keeps the task's state, and a third run finds nothing left"
else
  fail "land clean after the worktree went: $out"
fi
if [ "$(status_of land --repo "$SHOP" clean second-change)" = 1 ] && [ -d "$SHOP/.lem/worktrees/second-change" ]; then
  pass "clean refuses a task that has not landed"
else
  fail "clean before the landing"
fi

# A conflict with the base is reported and undone, never resolved here.
git -C "$other" pull -q origin main
echo other > "$other/app.txt" && git -C "$other" add -A && git -C "$other" commit -q -m "feat: other" && git -C "$other" push -q origin main
# The owner said that this task is careful: that word is in its brief, and it decides the read and who merges.
task_dir=$(project --repo "$SHOP" task-dir second-change)
printf '%s\n' 'slug: second-change' 'lead: session' 'careful: the owner says so' > "$task_dir/brief.md"
land --repo "$SHOP" start second-change >/dev/null
out=$(land --repo "$SHOP" base second-change 2>/dev/null || true)
if [ "$(status_of land --repo "$SHOP" base second-change)" = 1 ] && [ "$(field '(d["conflict"], d["branch"])' <<<"$out")" = "(['app.txt'], 'fix/second-change')" ] \
  && [ -z "$(git -C "$SHOP/.lem/worktrees/second-change" status --porcelain)" ] && [ ! -d "$SHOP/.git/worktrees/second-change/rebase-merge" ]; then
  pass "a conflict with the base names its files and leaves the worktree as it was"
else
  fail "land base with a conflict: $out"
fi
# The builder resolves it; here the test does. Then a red gate, then a round that finds a must-fix, then one commit for the whole branch.
tree=$SHOP/.lem/worktrees/second-change
git -C "$tree" rebase -q origin/main >/dev/null 2>&1 || true
echo both > "$tree/app.txt" && echo 'grep -qx both app.txt' > "$tree/tests/second-change.sh" && git -C "$tree" add -A && GIT_EDITOR=true git -C "$tree" rebase --continue >/dev/null 2>&1
git -C "$tree" rm -q ok.txt && git -C "$tree" commit -q -m "fix: lose the file the gate wants"
land --repo "$SHOP" base second-change >/dev/null
out=$(land --repo "$SHOP" gate second-change 2>/dev/null || true)
if [ "$(status_of land --repo "$SHOP" gate second-change)" = 1 ] && [ "$(field '(d["green"], [c["exit"] for c in d["commands"]], "stories" in d)' <<<"$out")" = "(False, [1, 0], False)" ] \
  && [ "$(kept second-change gated)" = None ] && [ "$(status_of land --repo "$SHOP" read second-change)" = 1 ] && [ "$(status_of land --repo "$SHOP" propose second-change --title x --notes "$NOTES")" = 1 ]; then
  pass "a red gate exits 1 with each command's result, the later checks do not run, and nothing is read or proposed on it"
else
  fail "red gate: $out"
fi
git -C "$tree" revert --no-edit HEAD >/dev/null
shop_settings agent squash
land --repo "$SHOP" gate second-change >/dev/null
out=$(land --repo "$SHOP" read second-change)
under=$(land --repo "$SHOP" read second-change --record "$(record 1 '{"kind": "round", "ran": [{"name": "correctness", "why": "a line of the app changes"}], "answered": ["codex"]}')" 2>&1 || true)
dropped=$(land --repo "$SHOP" read second-change --record "$(record 1 '{"kind": "full", "ran": [{"name": "default", "why": "the request is careful"}], "left_out": [{"name": "security", "why": "no input is read"}], "answered": ["codex"]}')" 2>&1 || true)
next=$(land --repo "$SHOP" read second-change --record "$(record 1 '{"kind": "full", "ran": [{"name": "default", "why": "the request is careful"}], "answered": ["codex", "claude"], "silent": [{"name": "gemini", "why": "at capacity"}], "must_fix": 1}')" | field '(d["recorded"]["verdict"], d["next"])')
err=$(land --repo "$SHOP" propose second-change --title x --notes "$NOTES" 2>&1 || true)
if [ "$(field '(d["due"], d["floor"], d["why"])' <<<"$out")" = "('review', 'full', 'the request is careful: the owner says so')" ] \
  && grep -q "this change gets the project's full set at the least (the request is careful: the owner says so), and the record says a review round with the profiles that fit" <<<"$under" \
  && grep -q "the project's full set leaves no profile out" <<<"$dropped" && [ "$next" = "('must-fix', 'review')" ] \
  && grep -q "a review is due before anything is proposed, the project's full set at the least" <<<"$err"; then
  pass "a request the owner called careful gets the project's full set: a record of less is refused, one that leaves a profile out too; a round in which one source did not answer counts, and a must-fix is followed by another round"
else
  fail "the read of a careful request: $out / $next / $err"
fi
echo '# and no other word' >> "$tree/tests/second-change.sh" && git -C "$tree" commit -q -am "fix: what the round found"
err=$(land --repo "$SHOP" read second-change 2>&1 || true)
land --repo "$SHOP" gate second-change >/dev/null
out=$(land --repo "$SHOP" read second-change)
land --repo "$SHOP" read second-change --record "$(record 2 '{"kind": "full", "ran": [{"name": "default", "why": "the request is careful"}], "answered": ["codex", "claude", "gemini"], "nit": 2}')" >/dev/null
if grep -q "no check is on record for this tip" <<<"$err" && [ "$(field '(d["due"], d["floor"], d["round"], len(d["reads"]))' <<<"$out")" = "('review', 'full', 2, 1)" ]; then
  pass "a fix is reviewed only after the machine checks ran on it, and the second round knows the first"
else
  fail "the second round: $err / $out"
fi
# Careful only by the owner's word, given after its plan: no talk was due, so none is asked for, and the text says why it had none.
err=$(land --repo "$SHOP" propose second-change --title "fix(app): both lines stay" --notes "$NOTES" 2>&1 || true)
printf '%s\n' '' '## Migration' '' 'none' >> "$NOTES"
land --repo "$SHOP" propose second-change --title "fix(app): both lines stay" --notes "$NOTES" >/dev/null
text=$SHOP/.git/lem/tasks/second-change/pr.md
if grep -q "^- no plan talk: the request became careful after its plan, by the owner's word$" "$text" \
  && [ "$(sed -n '/^## Checks$/,/^## Decisions of the build$/p' "$text" | grep -c 'plan talk')" = 1 ] && [ "$(head -1 "$text" | cut -c1-10)" = '**Green.**' ] \
  && ! grep -q '"event": "careful.missed", "task": "second-change"' "$SHOP/.git/lem/events.jsonl"; then
  pass "a request the owner called careful after its plan is proposed with no plan talk, its checks say in words that it had none and why, and that is no cause of not green"
else
  fail "a request careful by the owner's later word: $(cat "$text" 2>/dev/null)"
fi
agent=$(land --repo "$SHOP" land second-change --by agent --message "fix(app): both lines stay" 2>&1 || true)
if grep -q "the notes lack ## Migration" <<<"$err" && grep -q '^- careful: yes, the owner says so$' "$text" && [ "$(head -1 "$text" | cut -c1-10)" = '**Green.**' ] \
  && grep -q "^- the review, round 1 (the project's full set; answered: codex, claude; no answer from gemini (at capacity)): must-fix, 1 must-fix, 0 should, 0 nit$" "$text" \
  && grep -q '^  - ran default: the request is careful$' "$text" \
  && grep -q "^- the review, round 2 (the project's full set; answered: codex, claude, gemini): clean, 0 must-fix, 0 should, 2 nit$" "$text" \
  && grep -q "a careful request is merged by a person, whatever the settings say" <<<"$agent" && [ "$(status second-change)" = open ]; then
  pass "the notes of a careful request say whether it holds a migration, its text shows both rounds with who answered and who did not, and no agent merges it though it is green"
else
  fail "a careful request at the proposal: $err / $agent / $(cat "$text" 2>/dev/null)"
fi
if [ "$(status_of land --repo "$SHOP" land second-change --by owner)" = 1 ]; then pass "one commit for the branch needs its subject"; else fail "squash without a message"; fi
before=$(git -C "$ORIGIN" rev-parse main)
# A commit hook that changes a tracked file makes the one commit another tree than the gate saw.
gated=$(git -C "$tree" rev-parse HEAD)
printf '%s\n' '#!/bin/sh' 'echo stamped >> app.txt && git add app.txt' > "$SHOP/.git/hooks/pre-commit"
chmod +x "$SHOP/.git/hooks/pre-commit"
err=$(land --repo "$SHOP" land second-change --by owner --message "fix(app): both lines stay" 2>&1 || true)
rm "$SHOP/.git/hooks/pre-commit"
if grep -q "a commit hook changed the files" <<<"$err" && [ "$(git -C "$ORIGIN" rev-parse main)" = "$before" ] && [ "$(git -C "$tree" rev-parse HEAD)" = "$gated" ] \
  && [ -z "$(git -C "$tree" status --porcelain)" ] && [ "$(status second-change)" = open ]; then
  pass "a commit hook that changes the one commit's files stops the landing, and the branch is put back as the gate saw it"
else
  fail "squash with a hook that changes the tree: $err"
fi
out=$(land --repo "$SHOP" land second-change --by owner --message "fix(app): both lines stay")
if [ "$(git -C "$ORIGIN" rev-list --count "$before..main")" = 1 ] && [ "$(git -C "$ORIGIN" log -1 --format=%s main)" = "fix(app): both lines stay" ] \
  && [ "$(git -C "$ORIGIN" show main:app.txt)" = both ] && [ "$(git -C "$ORIGIN" rev-parse 'main^{tree}')" = "$(kept second-change tree)" ] && [ "$(status second-change)" = landed ]; then
  pass "on the owner's word, with history = squash, the branch lands as one commit, and its tree is the tree the gate passed on"
else
  fail "squash landing: $out"
fi
land --repo "$SHOP" clean second-change >/dev/null
printf '%s\n' '## Decisions' '' 'none' '' '## Left open' '' 'none' '' '## Worth a look' '' '- the one line of the file.' '' '## Filed in the backlog' '' 'none' '' '## Not done' '' 'none' > "$NOTES"

# A plan of four tasks is large: it needs a plan talk too, and the talk's event has one form. The
# event log already holds the talk of another task, which does not count for this one.
shop_settings agent keep
open_task four-tasks five.txt five
tree=$(project --repo "$SHOP" worktree-dir four-tasks)
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("1. The change.", "1. The change.\n2. Its test.\n3. Its page.\n4. Its note."))' "$tree/docs/plans/20261115-four-tasks.md"
git -C "$tree" commit -q -am "docs: four tasks"
checked four-tasks
land --repo "$SHOP" read four-tasks --record "$(record 1 '{"kind": "round", "ran": [{"name": "correctness", "why": "four tasks change the app"}], "answered": ["codex"]}')" >/dev/null
# the talk of another task, landed before: a valid event that is not this task's
project --repo "$SHOP" log second-change plan.talk reviewer=codex turns:=4 settled:=1 open:=0 >/dev/null
talkless=$(land --repo "$SHOP" propose four-tasks --title "fix: five" --notes "$NOTES" 2>&1 || true)
typed=$(project --repo "$SHOP" log four-tasks plan.talk reviewer=codex turns=5 settled:=2 open:=1 2>&1 || true)
missing=$(project --repo "$SHOP" log four-tasks plan.talk reviewer=codex turns:=5 settled:=2 2>&1 || true)
empty=$(project --repo "$SHOP" log four-tasks plan.talk reviewer=codex turns:=5 settled:=0 open:=0 2>&1 || true)
if grep -q "the plan has 4 tasks, more than three, so its plan is talked through by a session lead and the reviewer before any code" <<<"$talkless" \
  && grep -q "the event log has no .plan.talk. of four-tasks" <<<"$talkless" && [ "$(status four-tasks)" = landing ] \
  && grep -q "each N is a whole number, written with :=" <<<"$typed" && grep -q "and nothing else; this one has reviewer, settled, turns" <<<"$missing" \
  && grep -q "ends in a settled position or a disagreement left open" <<<"$empty" \
  && ! grep -q '"event": "plan.talk", "task": "four-tasks"' "$SHOP/.git/lem/events.jsonl" \
  && [ "$(grep -c '"event": "plan.talk", "task": "second-change", "reviewer": "codex", "turns": 4' "$SHOP/.git/lem/events.jsonl")" = 1 ]; then
  pass "a plan of four tasks with no plan talk is not proposed, though another task's talk is in the log; a talk's event without its form is refused, and nothing is written for it"
else
  fail "a large request with no plan talk: $talkless / $typed / $missing / $empty"
fi
project --repo "$SHOP" log four-tasks plan.talk reviewer=claude turns:=3 settled:=1 open:=0 >/dev/null
project --repo "$SHOP" log four-tasks plan.talk reviewer=codex turns:=9 settled:=4 open:=1 >/dev/null
out=$(land --repo "$SHOP" propose four-tasks --title "fix: five" --notes "$NOTES")
text=$SHOP/.git/lem/tasks/four-tasks/pr.md
if [ "$(field 'd["green"]' <<<"$out")" = True ] && [ "$(status four-tasks)" = open ] \
  && grep -q '^- the plan talk: codex argued the plan with the lead, 9 turns; 4 positions settled by the two, 1 left open$' "$text" \
  && [ "$(grep -c 'plan talk' "$text")" = 1 ] && grep -q '^- careful: no$' "$text"; then
  pass "after its plan talk a plan of four tasks is proposed, and its text holds one line of the talk, from the newest event"
else
  fail "a large request after its plan talk: $out / $(cat "$text" 2>/dev/null)"
fi
project --repo "$SHOP" state four-tasks dropped "the test is over" >/dev/null

# A plan that says careful calls for a plan talk: the request is not proposed without one, and with one its text holds the talk's line.
MIG=$WORK/notes-migration.md
cp "$NOTES" "$MIG" && printf '%s\n' '' '## Migration' '' 'none' >> "$MIG"
open_task careful-plan six.txt six
tree=$(project --repo "$SHOP" worktree-dir careful-plan)
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("\n## Stories", "careful: yes, a price is rounded here.\n\n## Stories", 1))' "$tree/docs/plans/20261115-careful-plan.md"
git -C "$tree" commit -q -am "docs: the plan is careful"
checked careful-plan
land --repo "$SHOP" read careful-plan --record "$(record 1 '{"kind": "full", "ran": [{"name": "default", "why": "the plan says careful"}], "answered": ["codex"]}')" >/dev/null
talkless=$(land --repo "$SHOP" propose careful-plan --title "fix: six" --notes "$MIG" 2>&1 || true)
if grep -q "the plan says that the request is careful, so its plan is talked through by a session lead and the reviewer before any code (.stages/plan.md., step 4)" <<<"$talkless" \
  && grep -q "the event log has no .plan.talk. of careful-plan" <<<"$talkless" && grep -q "project.py log careful-plan plan.talk reviewer=AGENT turns:=N settled:=N open:=N" <<<"$talkless" \
  && [ ! -f "$SHOP/.git/lem/tasks/careful-plan/pr.md" ] && [ "$(status careful-plan)" = landing ]; then
  pass "a request whose plan says careful is not proposed while its event log has no plan talk, and the refusal names the plan stage's step and the event the lead writes"
else
  fail "a careful plan with no plan talk: $talkless"
fi
project --repo "$SHOP" log careful-plan plan.talk reviewer=codex turns:=6 settled:=2 open:=1 >/dev/null
land --repo "$SHOP" propose careful-plan --title "fix: six" --notes "$MIG" >/dev/null
text=$SHOP/.git/lem/tasks/careful-plan/pr.md
if grep -q '^- the plan talk: codex argued the plan with the lead, 6 turns; 2 positions settled by the two, 1 left open$' "$text" \
  && [ "$(sed -n '/^## Checks$/,/^## Decisions of the build$/p' "$text" | grep -c 'plan talk')" = 1 ] && grep -q '^- careful: yes, the plan says so$' "$text" \
  && [ "$(status careful-plan)" = open ]; then
  pass "after its plan talk a request whose plan says careful is proposed, and the checks of its text say who argued the plan with the lead, the turns, and the positions settled and left open"
else
  fail "the plan talk in the text of a careful plan: $(cat "$text" 2>/dev/null)"
fi
project --repo "$SHOP" state careful-plan dropped "the test is over" >/dev/null

# A file that moves into an ignored folder also leaves a folder the gate reads.
open_task moved-file extra.txt four
checked moved-file && read_clean moved-file && propose moved-file
git -C "$other" pull -q origin main && git -C "$other" mv late.txt docs/late.txt && git -C "$other" commit -q -m "docs: move late" && git -C "$other" push -q origin main
err=$(land --repo "$SHOP" land moved-file --by agent 2>&1 || true)
if [ "$(status_of land --repo "$SHOP" land moved-file --by agent)" = 1 ] && grep -q "files the gate reads (.*late.txt" <<<"$err" && [ "$(status moved-file)" = open ]; then
  pass "a file moved into an ignored folder still counts as a change of the path it left"
else
  fail "a rename across gate.ignores: $err"
fi
checked moved-file && propose moved-file
# The landing is cut off after the push and before its last state write: a copy of the scripts whose
# project.py refuses to write `landed` stands in for the kill. The main checkout also has a commit of
# its own, so it cannot follow the remote.
LATE=$WORK/late
cp -R "$PWD/skills/lem/scripts" "$LATE"
printf '%s\n' 'import runpy, sys' 'if "landed" in sys.argv: sys.exit("project.py: cut off")' \
  "sys.argv[0] = '$PWD/skills/lem/scripts/project.py'" "runpy.run_path(sys.argv[0], run_name='__main__')" > "$LATE/project.py"
git -C "$SHOP" commit -q --allow-empty -m "chore: only here"
before=$(git -C "$ORIGIN" rev-parse main)
if [ "$(status_of "$PY" -B "$LATE/land.py" --repo "$SHOP" land moved-file --by agent)" = 1 ] && [ "$(git -C "$ORIGIN" rev-list --count "$before..main")" = 1 ] \
  && [ "$(status moved-file)" = open ] && [ "$(kept moved-file intent)" != None ]; then
  pass "a landing cut off after the push leaves the commit on the base, the task open and the record the next run needs"
else
  fail "a landing cut off before the landed state: status $(status moved-file), intent $(kept moved-file intent)"
fi
landed_tip=$(git -C "$ORIGIN" rev-parse main)
out=$(land --repo "$SHOP" land moved-file --by agent)
if [ "$(status moved-file)" = landed ] && [ "$(git -C "$ORIGIN" rev-parse main)" = "$landed_tip" ] && [ "$(field 'd["tip"]' <<<"$out")" = "$landed_tip" ] \
  && [ "$(kept moved-file intent)" = None ] \
  && [ "$(field '"did not follow origin/main" in d["left_behind"] and "brings it up" not in d["left_behind"]' <<<"$out")" = True ]; then
  pass "the next run finishes it: the state is landed, nothing is pushed twice, and a main checkout that cannot follow is reported with git's own reason"
else
  fail "finishing a cut-off landing: $out"
fi
out=$(land --repo "$SHOP" land moved-file --by agent 2>&1 || true)
if grep -q "is 'landed', not .open." <<<"$out"; then pass "a landed task does not land again"; else fail "land twice: $out"; fi
git -C "$SHOP" reset -q --hard origin/main
out=$(land --repo "$SHOP" clean moved-file)
if [ "$(field '(d["worktree"], d["branch"])' <<<"$out")" = "(True, 'fix/moved-file')" ] && [ ! -e "$SHOP/.lem/worktrees/moved-file" ] && [ -z "$(git -C "$SHOP" branch --list fix/moved-file)" ]; then
  pass "clean removes a landed task's worktree and its branch in one run"
else
  fail "land clean: $out"
fi

# A landing cut off after the push, and then more work on the branch: what was pushed is written
# down, and the new tip lands only through its own base, checks and review.
shop_settings agent keep
open_task more-work m.txt five
checked more-work && read_clean more-work && propose more-work
"$PY" -B "$LATE/land.py" --repo "$SHOP" land more-work --by agent >/dev/null 2>&1 || true
git -C "$SHOP" merge -q --ff-only origin/main
tree=$SHOP/.lem/worktrees/more-work
# the first half is on the base now, so its test no longer fails there: the story is held by a test of the second half
echo six > "$tree/n.txt" && echo 'grep -qx six n.txt' > "$tree/tests/more-work-n.sh"
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("tests/more-work.sh", "tests/more-work-n.sh"))' "$tree/docs/plans/20261115-more-work.md"
git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: more-work, the second half"
err=$(land --repo "$SHOP" land more-work --by agent 2>&1 || true)
if grep -q "from a landing that was cut off, and the branch has more work since" <<<"$err" && [ "$(status more-work)" = open ] && ! git -C "$ORIGIN" cat-file -e main:n.txt 2>/dev/null \
  && [ "$(kept more-work intent)" = None ] && [ "$(kept more-work landed_before | grep -c '\.\.')" = 1 ]; then
  pass "after a cut-off landing and more work, the pushed range is written down and the new tip is refused until its own checks ran"
else
  fail "a stale landing record with more work: $err"
fi
checked more-work
out=$(land --repo "$SHOP" read more-work)
read_clean more-work 2 && propose more-work
landed=$(land --repo "$SHOP" land more-work --by agent)
if [ "$(field '(d["due"], d["floor"], d["round"])' <<<"$out")" = "('review', 'read', 2)" ] && [ "$(git -C "$ORIGIN" show main:n.txt)" = six ] && [ "$(status more-work)" = landed ] \
  && [ "$(field 'd["tip"]' <<<"$landed")" = "$(git -C "$ORIGIN" rev-parse main)" ]; then
  pass "then the second half gets a review of its own and lands as its own range"
else
  fail "landing the work added after a cut-off landing: $out / $landed"
fi
land --repo "$SHOP" clean more-work >/dev/null

# Two rounds at most. A usual request whose read found a must-fix gets a round after the fix, and one
# that is not clean after the second round goes to the owner as not green.
open_task not-clean nc.txt seven
checked not-clean
# A run that is cut off before the review is written down leaves nothing, the next run writes it
# down once, and the same record sent again is refused: one review never takes two rounds. A copy
# of the scripts whose project.py refuses the `review` event stands in for the kill.
CUT=$WORK/cut
cp -R "$PWD/skills/lem/scripts" "$CUT"
printf '%s\n' 'import runpy, sys' 'if "review" in sys.argv: sys.exit("project.py: cut off")' \
  "sys.argv[0] = '$PWD/skills/lem/scripts/project.py'" "runpy.run_path(sys.argv[0], run_name='__main__')" > "$CUT/project.py"
first=$(record 1 '{"kind": "read", "answered": ["codex"], "must_fix": 2}')
cut_off=$(status_of "$PY" -B "$CUT/land.py" --repo "$SHOP" read not-clean --record "$first")
nothing=$(kept not-clean reads)
land --repo "$SHOP" read not-clean --record "$first" >/dev/null
twice=$(land --repo "$SHOP" read not-clean --record "$first" 2>&1 || true)
if [ "$cut_off" = 1 ] && [ "$nothing" = None ] && grep -q "attempt 1, and the next review of this task is attempt 2: that review is written down already" <<<"$twice" \
  && [ "$(land --repo "$SHOP" read not-clean | field '(d["round"], d["attempt"], len(d["reads"]))')" = "(2, 2, 1)" ]; then
  pass "a review whose record is sent again, after a cut-off run or by mistake, is written down once and takes one round"
else
  fail "a record sent twice: $cut_off / $nothing / $twice"
fi
tree=$SHOP/.lem/worktrees/not-clean
echo eight > "$tree/nc2.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: the first read's findings"
land --repo "$SHOP" gate not-clean >/dev/null
out=$(land --repo "$SHOP" read not-clean)
again=$(land --repo "$SHOP" read not-clean --record "$(clean 2)" 2>&1 || true)
land --repo "$SHOP" read not-clean --record "$(record 2 '{"kind": "round", "ran": [{"name": "correctness", "why": "a file of the app changes"}], "left_out": [{"name": "security", "why": "no input from outside is read"}], "answered": ["codex"], "must_fix": 1}')" >/dev/null
echo nine > "$tree/nc3.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: the round's finding"
land --repo "$SHOP" gate not-clean >/dev/null
third=$(land --repo "$SHOP" read not-clean)
fourth=$(land --repo "$SHOP" read not-clean --record "$(record 3 '{"kind": "round", "ran": [{"name": "correctness", "why": "a file of the app changes"}], "answered": ["codex"]}')" 2>&1 || true)
proposed=$(land --repo "$SHOP" propose not-clean --title "fix: not-clean" --notes "$NOTES")
text=$SHOP/.git/lem/tasks/not-clean/pr.md
agent=$(land --repo "$SHOP" land not-clean --by agent 2>&1 || true)
why="two rounds reviewed it: the last one left 1 must-fix, and nobody reviewed what changed after it"
if [ "$(field '(d["due"], d["floor"], d["why"])' <<<"$out")" = "('review', 'round', 'an earlier review found a must-fix: after its fix a round reviews the change')" ] && grep -q "this change gets a review round with the profiles that fit at the least" <<<"$again" \
  && [ "$(field '(d["due"], d["why"])' <<<"$third")" = "('owner', '$why')" ] && grep -q "no review is due: two rounds reviewed it" <<<"$fourth" \
  && [ "$(field '(d["green"], d["not_green"])' <<<"$proposed")" = "(False, ['$why'])" ] && [ "$(kept not-clean title)" = "fix: not-clean" ] \
  && [ "$(sed -n 1p "$text")" = '**Not green.**' ] && [ "$(sed -n 3p "$text")" = "- $why" ] && grep -q '^  - left out security: no input from outside is read$' "$text" \
  && grep -q "^not green: $why$" "$SHOP/.git/lem/tasks/not-clean/state.md" \
  && grep -q "the request is not green ($why), so a person merges it" <<<"$agent"; then
  pass "a usual request with a must-fix gets a round after its fix, with each profile it ran or left out and why; after two rounds no third is taken, the request is proposed as not green, which its first lines say with the reason, and no agent merges it"
else
  fail "two rounds at most: $out / $again / $third / $fourth / $proposed / $agent / $(sed -n 1,4p "$text" 2>/dev/null)"
fi
land --repo "$SHOP" land not-clean --by owner >/dev/null
if [ "$(status not-clean)" = landed ] && [ "$(git -C "$ORIGIN" show main:nc3.txt)" = nine ]; then pass "the owner's word lands a request that is not green"; else fail "the owner lands a request that is not green"; fi
land --repo "$SHOP" clean not-clean >/dev/null

# No gate command, a protected branch, and a repository with no remote.
open_task third-change note.txt three
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' > "$SHOP/.lem/project.toml"
err=$(land --repo "$SHOP" start third-change 2>&1 || true)
if [ "$(status_of land --repo "$SHOP" start third-change)" = 1 ] && grep -q "no gate command" <<<"$err" && [ "$(status third-change)" = blocked ]; then
  pass "a project with no gate command lands nothing, and the task is blocked instead of holding the landing line"
else
  fail "start with no gate: $err"
fi
printf '%s\n' '[branch]' 'base = "release"' 'land = "agent"' 'protected = ["release"]' > "$SHOP/.lem/project.toml"
if [ "$(status_of land --repo "$SHOP" start third-change)" = 1 ]; then pass "no step runs toward a branch the settings refuse"; else fail "land toward a protected base"; fi
LOCAL=$WORK/local
git init -q -b main "$LOCAL" && ident "$LOCAL"
project --repo "$LOCAL" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[gate]' 'commands = ["true"]' 'bar = ["rubocop:disable"]' '[flow]' 'careful = ["billing/*"]' > "$LOCAL/.lem/project.toml"
mkdir -p "$LOCAL/tests" "$LOCAL/docs" && printf '%s\n' 'def test_base():' '    assert 1 + 1 == 2' '    assert 2 + 2 == 4' > "$LOCAL/tests/test_base.py" && echo guide > "$LOCAL/docs/guide.md"
printf '%s\n' 'import plugin # noqa: F401' 'import other  # noqa: E402' > "$LOCAL/plug.py"
# app_py FIRST SECOND: two functions alike in every line but their names, each longer than the
# three lines of context a diff shows, so the same edit in either gives the same lines of a diff
app_py() {
  printf '%s\n' 'def first():' '    a = 1' '    b = 2' '    c = 3' "    return \"$1\"" '    # the end' '' '' \
    'def second():' '    a = 1' '    b = 2' '    c = 3' "    return \"$2\"" '    # the end' '' '' 'def third():' '    return 3'
}
app_py old old > "$LOCAL/app.py"
printf '%s\n' 'pub fn one() -> i32 { 1 }' '#[cfg(test)]' 'mod tests {' '    #[test]' '    fn it_is_one() { assert_eq!(super::one(), 1); }' '}' > "$LOCAL/lib.rs"
git -C "$LOCAL" add -A && git -C "$LOCAL" commit -q -m "chore: start"
local_land() { land --repo "$LOCAL" "$@"; }
task_in "$LOCAL" local-change x.txt x
# A story that changed during the build is written down by the build, as a record of its own with its text before and after; the text shows it, and a person merges.
printf '%s\n' '## Stories' '' 'Kind: correction, because the request is one sentence.' '' '1. The file holds the word y.' > "$WORK/local-approved.md"
"$PY" -B "$STORIES" --repo "$LOCAL" approve local-change --file "$WORK/local-approved.md" >/dev/null 2>&1 || true
"$PY" -B "$DECISIONS" --repo "$LOCAL" story local-change --changed 1 --was "The file holds the word y." --now "The file holds the word the owner asked for." \
  --why "y is taken by another file." --by personas --said "Both personas picked x." >/dev/null 2>&1 || true
local_land start local-change >/dev/null && local_land base local-change >/dev/null && local_land gate local-change >/dev/null && local_land read local-change --record "$(clean 1)" >/dev/null
local_land propose local-change --title "fix: x" --notes "$NOTES" >/dev/null
err=$(local_land land local-change --by agent 2>&1 || true)
out=$(local_land land local-change --by owner)
if grep -q "the request is not green (story 1 changed during the build: y is taken by another file.), so a person merges it" <<<"$err" \
  && [ "$(sed -n 1p "$LOCAL/.git/lem/tasks/local-change/pr.md")" = '**Not green.**' ] && [ "$(sed -n 3p "$LOCAL/.git/lem/tasks/local-change/pr.md")" = '- story 1 changed during the build: y is taken by another file.' ] \
  && grep -qxF -- '- story 1: was "The file holds the word y.", now "The file holds the word the owner asked for.". y is taken by another file. By the personas: Both personas picked x.' "$LOCAL/.git/lem/tasks/local-change/pr.md" \
  && [ ! -e "$LOCAL/.git/lem/tasks/local-change/story-changes.jsonl" ] \
  && [ "$(field 'd["pushed"]' <<<"$out")" = False ] && [ -f "$LOCAL/x.txt" ] && [ "$(git -C "$LOCAL" log -1 --format=%s main)" = "fix: local-change" ] && [ "$(status_in "$LOCAL" local-change)" = landed ]; then
  pass "a request with a changed story is not green: its text says so first and shows the change, with what the story was and is, and a person merges it whatever the settings say; with no remote the base branch is fast-forwarded in the checkout that holds it"
else
  fail "local landing: $err / $out"
fi
local_land clean local-change >/dev/null
# A choice that waits for the owner holds the proposal; one taken by timeout is not green, and a late answer that differs is said.
task_in "$LOCAL" waited-change w.txt w
local_land start waited-change >/dev/null && local_land base waited-change >/dev/null && local_land gate waited-change >/dev/null && local_land read waited-change --record "$(clean 1)" >/dev/null
wdec() { "$PY" -B "$DECISIONS" --repo "$LOCAL" "$@"; }
wfile=$LOCAL/.git/lem/tasks/waited-change/decisions.jsonl
wdec log waited-change --what "The name of the file" --chose w.txt --why "The other files have one letter." --by lead >/dev/null
wdec ask waited-change --what "Where the word goes" --option "the first line" --option "the last line" --recommended "the first line" --why "A reader sees it at once." --said "The two personas split." >/dev/null
waiting=$(local_land propose waited-change --title "fix: w" --notes "$NOTES" 2>&1 || true)
past "$wfile" 2 && wdec timeout waited-change 2 >/dev/null
wdec ask waited-change --what "Tell the merchants" --option "send the email" --option "send nothing" --recommended "send nothing" --why "Nothing they see changes." --said "The two personas split." --irreversible person >/dev/null
forever=$(local_land propose waited-change --title "fix: w" --notes "$NOTES" 2>&1 || true)
wdec answer waited-change 3 --chose "send the email" --words "Yes, send it." --why "The merchants asked for it." >/dev/null
wdec ask waited-change --what "The case of the word" --option "lower case" --option "upper case" --recommended "lower case" --why "The test reads it so." --said "The two personas split." >/dev/null
past "$wfile" 4 && wdec timeout waited-change 4 >/dev/null && wdec answer waited-change 4 --chose "upper case" --words "Make it upper case." --why "The header is in upper case." >/dev/null
wdec answer waited-change 2 --chose "the first line" --why "The importer reads the first line." >/dev/null
# a choice the personas left unclear: the owner takes the recommended option in time
wdec ask waited-change --what "Which line holds the word" --option "the only line" --option "the second line" --recommended "the second line" --why "A header goes first." \
  --said "The two personas split." >/dev/null
wdec answer waited-change 5 --chose "the second line" >/dev/null
# the owner decides what none of the options says: an irreversible step that would otherwise wait for ever, and one more
wdec ask waited-change --what "Email the customers" --option "email all customers" --option "email nobody" --recommended "email nobody" --why "Nobody asked for it." \
  --said "The two personas split." --irreversible person >/dev/null
wdec answer waited-change 6 --instead "Email only the beta testers." --why "They asked to hear first." >/dev/null
wdec ask waited-change --what "The word's line ending" --option "a line break" --option "no line break" --recommended "a line break" --why "Every file ends so." \
  --said "The two personas split." >/dev/null
wdec answer waited-change 7 --instead "A line break, and a second line with the date." >/dev/null
instead_pending=$(wdec pending waited-change | field '[c["id"] for c in d["waiting"]]')
local_land propose waited-change --title "fix: w" --notes "$NOTES" >/dev/null
text=$LOCAL/.git/lem/tasks/waited-change/pr.md
agent=$(local_land land waited-change --by agent 2>&1 || true)
if grep -qF "choice 2 of waited-change waits for the owner (Where the word goes): a request is never proposed over an open question of his" <<<"$waiting" \
  && grep -qF "decisions.py answer waited-change 2 --chose OPTION --words TEXT" <<<"$waiting" && grep -qF "decisions.py timeout waited-change 2" <<<"$waiting" \
  && grep -qF "choice 3 of waited-change waits for the owner (Tell the merchants)" <<<"$forever" && grep -qF "decisions.py answer waited-change 3 --chose OPTION --words TEXT" <<<"$forever" \
  && ! grep -qF "timeout waited-change 3" <<<"$forever" && [ "$(status_in "$LOCAL" waited-change)" = open ] \
  && [ "$(sed -n 1p "$text")" = '**Not green.**' ] \
  && [ "$(sed -n 3p "$text")" = "- choice 2 was taken by timeout (Where the word goes): \"the first line\", the recommended option, after the owner's wait of 15 minutes ended with no answer; he answered later with the same (his reason: The importer reads the first line)" ] \
  && [ "$(sed -n 4p "$text")" = "- choice 4 was taken by timeout (The case of the word): \"lower case\", the recommended option, after the owner's wait of 15 minutes ended with no answer; he answered later with \"upper case\", which differs (his words: \"Make it upper case.\"; his reason: The header is in upper case)" ] \
  && [ -z "$(sed -n 5p "$text")" ] && [ "$instead_pending" = "[]" ] \
  && [ "$(grep '^## ' "$text" | tr '\n' '|')" = "## The request|## Stories|## Checks|## Decisions of the build|## Decisions|## Left open|## Worth a look|## Filed in the backlog|## Not done|" ] \
  && [ "$(sed -n '/^## Decisions of the build$/,/^## Decisions$/p' "$text" | grep '^- ')" = "- The name of the file: \"w.txt\", by the lead. The other files have one letter.
- Where the word goes: \"the first line\", by the timeout, after the owner's wait of 15 minutes. A reader sees it at once. He answered later with the same (his reason: The importer reads the first line).
- Tell the merchants: \"send the email\", by the owner, over the recommended \"send nothing\" (recommended because: Nothing they see changes). His words: \"Yes, send it.\" His reason: The merchants asked for it.
- The case of the word: \"lower case\", by the timeout, after the owner's wait of 15 minutes. The test reads it so. He answered later with \"upper case\", which differs (his words: \"Make it upper case.\"; his reason: The header is in upper case).
- Which line holds the word: \"the second line\", by the owner, as recommended. A header goes first.
- Email the customers: \"Email only the beta testers.\", by the owner, none of the options; the recommended was \"email nobody\" (recommended because: Nobody asked for it). His reason: They asked to hear first.
- The word's line ending: \"A line break, and a second line with the date.\", by the owner, none of the options; the recommended was \"a line break\" (recommended because: Every file ends so). He gave no reason." ] \
  && grep -qF "the request is not green (choice 2 was taken by timeout" <<<"$agent"; then
  pass "a request is never proposed over a choice that waits for the owner, irreversible or not; each choice taken by timeout is a line of its own that is not green, with a late answer, the same or not, and his own words and reason; an answered choice is no cause of not green by itself; a decision of the owner's that is none of the options settles its choice, also an irreversible one, so the request is proposed; and the text lists each decision of the record with who took it and its reason, the recommendation's reason never as the owner's"
else
  fail "decisions in the landing: $waiting / $forever / $agent / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state waited-change dropped "the test is over" >/dev/null

# Approved stories in the landing: a story the build added or removed is not green, like a changed one; and the
# checks hold one line on the personas' read of the stories, from its event, with his approval.
lstories() { "$PY" -B "$STORIES" --repo "$LOCAL" "$@"; }
ldecide() { "$PY" -B "$DECISIONS" --repo "$LOCAL" "$@"; }
# to_open SLUG: the machine steps, a clean read and the proposal of a task of the local repository
to_open() {
  local_land start "$1" >/dev/null && local_land base "$1" >/dev/null && local_land gate "$1" >/dev/null \
    && local_land read "$1" --record "$(clean 1)" >/dev/null && local_land propose "$1" --title "fix: $1" --notes "$NOTES" >/dev/null
}
approved_day() { "$PY" -c 'import json, sys; print(json.load(open(sys.argv[1]))["at"][:10])' "$LOCAL/.git/lem/tasks/$1/stories.json" 2>/dev/null || true; }
task_in "$LOCAL" story-departs d.txt d
tree=$(project --repo "$LOCAL" worktree-dir story-departs)
printf '%s\n' '## Stories' '' 'Kind: feature, because the file gets a word and a rule of its own.' '' '1. The file holds the word the owner asked for.' '2. The file has one line.' > "$WORK/approved.md"
# the read comes first, of the stories file that he then approves
read_digest=$(lstories digest story-departs --file "$WORK/approved.md" 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
project --repo "$LOCAL" log story-departs stories.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' stories:=2 flagged:=0 split:=false "digest=$read_digest" >/dev/null 2>&1 || true
lstories approve story-departs --file "$WORK/approved.md" >/dev/null 2>&1 || true
# shellcheck disable=SC2016
printf '%s\n' '# story-departs' '' '## Stories' '' 'Kind: feature, because the file gets a word and a rule of its own.' '' '1. The file holds the word the owner asked for.' \
  '   - test: `sh tests/story-departs.sh` in `tests/story-departs.sh`' '2. The file ends with a line break.' '   - no test: printf ends every line so.' '' '## Tasks' '' '1. The change.' \
  > "$tree/docs/plans/20261115-story-departs.md"
git -C "$tree" commit -q -am "docs: the stories as they are built"
unrecorded=$(local_land start story-departs >/dev/null && local_land base story-departs >/dev/null && local_land gate story-departs 2>&1 || true)
# a story that a choice of the build removes, once the choice is answered; and one the lead adds
ldecide ask story-departs --what "The one-line rule" --option "keep the rule" --option "no such rule" --recommended "keep the rule" --why "A reader counts on it." \
  --said "The two personas split." >/dev/null 2>&1 || true
early=$(ldecide story story-departs --removed 2 --was "The file has one line." --why "A second line holds the date now." --choice 1 2>&1 || true)
ldecide answer story-departs 1 --chose "no such rule" >/dev/null 2>&1 || true
ldecide story story-departs --removed 2 --was "The file has one line." --why "A second line holds the date now." --choice 1 >/dev/null 2>&1 || true
ldecide story story-departs --added 2 --now "The file ends with a line break." --why "The importer reads whole lines only." --by lead >/dev/null 2>&1 || true
local_land gate story-departs >/dev/null 2>&1 && local_land read story-departs --record "$(clean 1)" >/dev/null 2>&1 \
  && local_land propose story-departs --title "fix: story-departs" --notes "$NOTES" >/dev/null 2>&1 || true
text=$LOCAL/.git/lem/tasks/story-departs/pr.md
agent=$(local_land land story-departs --by agent 2>&1 || true)
if grep -qF "story 2 of 20261115-story-departs.md says 'The file ends with a line break.', and the expected story 2 is 'The file has one line.'" <<<"$unrecorded" \
  && grep -qF "choice 1 is waits: a story changes after a choice that was answered or taken by timeout" <<<"$early" \
  && [ "$(sed -n 1p "$text" 2>/dev/null)" = '**Not green.**' ] \
  && [ "$(sed -n 3p "$text")" = '- story 2 was removed during the build: A second line holds the date now, after choice 1 (The one-line rule), where the owner took "no such rule"' ] \
  && [ "$(sed -n 4p "$text")" = '- story 2 was added during the build: The importer reads whole lines only.' ] \
  && grep -qxF -- '- story 2: removed, was "The file has one line.". A second line holds the date now, after choice 1 (The one-line rule), where the owner took "no such rule".' "$text" \
  && grep -qxF -- '- story 2: added, "The file ends with a line break.". The importer reads whole lines only. By the lead.' "$text" \
  && [ -n "$(approved_day story-departs)" ] \
  && grep -qxF -- "- the stories were read by 2 of 2 personas asked, two model families (opus, sol); nobody confused; he approved them on $(approved_day story-departs)" "$text" \
  && ! grep -q "after the personas' read" "$text" \
  && grep -qF "the request is not green (story 2 was removed during the build" <<<"$agent"; then
  pass "a story a choice of the build removed and one the lead added are not green, each with its line first, what it was or is, its reason and the choice that led to it; a story changes only after its choice is answered; the gate refuses the plan until both are recorded; and the checks say that two model families read the stories and when he approved them"
else
  fail "an added and a removed story in the landing: $unrecorded / $early / $agent / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state story-departs dropped "the test is over" >/dev/null
# A feature is not proposed without a read of its stories, nor over a doubt of the personas that no approval of his followed.
task_in "$LOCAL" read-doubt r.txt r
tree=$(project --repo "$LOCAL" worktree-dir read-doubt)
sed -i.bak 's/^Kind: correction, because the request is one sentence\.$/Kind: feature, because the ticket names the word and the file./' "$tree/docs/plans/20261115-read-doubt.md"
rm "$tree/docs/plans/20261115-read-doubt.md.bak" && git -C "$tree" commit -q -am "docs: a feature"
printf '%s\n' '## Stories' '' 'Kind: feature, because the ticket names the word and the file.' '' '1. The file holds the word the owner asked for.' > "$WORK/doubt.md"
plan_digest=$(lstories digest read-doubt 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
local_land start read-doubt >/dev/null && local_land base read-doubt >/dev/null && local_land gate read-doubt >/dev/null && local_land read read-doubt --record "$(clean 1)" >/dev/null
unread_feature=$(local_land propose read-doubt --title "fix: r" --notes "$NOTES" 2>&1 || true)
project --repo "$LOCAL" log read-doubt stories.read by=lead asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' stories:=1 flagged:=0 split:=true "digest=$plan_digest" >/dev/null 2>&1 || true
split_unseen=$(local_land propose read-doubt --title "fix: r" --notes "$NOTES" 2>&1 || true)
project --repo "$LOCAL" log read-doubt stories.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=1 split:=false "digest=$plan_digest" >/dev/null 2>&1 || true
flag_unseen=$(local_land propose read-doubt --title "fix: r" --notes "$NOTES" 2>&1 || true)
# the newest read: partial, one story flagged, the families split, and of other stories than he then approved
project --repo "$LOCAL" log read-doubt stories.read by=lem asked:=3 answered:=2 'families:=["opus", "sol"]' \
  'silent:=[{"name": "the accountant, sol", "why": "the model was at capacity"}]' stories:=1 flagged:=1 split:=true "digest=$read_digest" >/dev/null 2>&1 || true
lstories approve read-doubt --file "$WORK/doubt.md" >/dev/null 2>&1 || true
local_land propose read-doubt --title "fix: r" --notes "$NOTES" >/dev/null 2>&1 || true
text=$LOCAL/.git/lem/tasks/read-doubt/pr.md
if grep -qF "read-doubt is a feature, and the event log has no \`stories.read\`" <<<"$unread_feature" && grep -qF 'stages/new.md' <<<"$unread_feature" \
  && grep -qF "the newest read of read-doubt's stories found a split between the two families, and no approval of his came after it" <<<"$split_unseen" \
  && grep -qF "found 1 flagged story, and no approval of his came after it" <<<"$flag_unseen" && grep -qF "stories.py approve read-doubt --file FILE" <<<"$flag_unseen" \
  && [ "$(sed -n 1p "$text" 2>/dev/null | cut -c1-10)" = '**Green.**' ] \
  && grep -qxF -- "- the stories were read by 2 of 3 personas asked, two model families (opus, sol); 1 of 1 story flagged; the two families split; no answer from the accountant, sol (the model was at capacity); he approved them on $(approved_day read-doubt)" "$text" \
  && grep -qxF -- "- he changed the stories after the personas' read, and the change was not read" "$text"; then
  pass "a feature with no read of its stories is not proposed, nor one whose newest read flagged a story or split the families with no approval of his after it; a partial read counts and says who did not answer and why; and stories he changed after the read are one line that is no cause of not green"
else
  fail "the read before a proposal: $unread_feature / $split_unseen / $flag_unseen / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state read-doubt dropped "the test is over" >/dev/null
# The rare path: the lead ran the read with one model family, nobody was confused, and there is no approval; a scout's report is named.
task_in "$LOCAL" ticket-word t.txt t
tree=$(project --repo "$LOCAL" worktree-dir ticket-word)
sed -i.bak 's/^Kind: correction, because the request is one sentence\.$/Kind: feature, because the ticket names the word and the file./' "$tree/docs/plans/20261115-ticket-word.md"
rm "$tree/docs/plans/20261115-ticket-word.md.bak" && git -C "$tree" commit -q -am "docs: a feature"
digest=$(lstories digest ticket-word 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
read_with() { project --repo "$LOCAL" log ticket-word stories.read "$@" 2>&1 || true; }
bad_by=$(read_with by=owner asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest")
bad_one=$(read_with by=lead asked:=1 answered:=1 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest")
bad_none=$(read_with by=lead asked:=2 answered:=0 'families:=["opus"]' 'silent:=[{"name": "a", "why": "b"}]' stories:=1 flagged:=0 split:=false "digest=$digest")
bad_more=$(read_with by=lead asked:=2 answered:=3 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest")
bad_quiet=$(read_with by=lead asked:=3 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest")
bad_families=$(read_with by=lead asked:=2 answered:=2 families=opus 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest")
bad_flagged=$(read_with by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=2 split:=false "digest=$digest")
bad_split=$(read_with by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=true "digest=$digest")
bad_digest=$(read_with by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false digest=abc)
bad_missing=$(read_with by=lead asked:=2 answered:=2 'families:=["opus"]' stories:=1 flagged:=0 split:=false "digest=$digest")
project --repo "$LOCAL" log ticket-word stories.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest" >/dev/null 2>&1 || true
echo '1. t.txt does not exist on the base branch (git ls-files).' > "$LOCAL/.git/lem/tasks/ticket-word/scout.md"
to_open ticket-word || true
text=$LOCAL/.git/lem/tasks/ticket-word/pr.md
if [ "$(sed -n 1p "$text" 2>/dev/null | cut -c1-10)" = '**Green.**' ] \
  && grep -qxF -- "- the stories were read by 2 of 2 personas asked, one model family (opus); nobody confused; the build started with no wait for him" "$text" \
  && ! grep -q "after the personas' read" "$text" \
  && grep -qxF -- "- the scout's report, the facts of the code the stories were written from: \`$LOCAL/.git/lem/tasks/ticket-word/scout.md\`" "$text" \
  && grep -q "by is lem, when Lem ran the read" <<<"$bad_by" && grep -q "a read asks two personas at the least" <<<"$bad_one" \
  && grep -q "a read in which nobody answered is no read: start it once more" <<<"$bad_none" && grep -q "answered is 1 to asked" <<<"$bad_more" \
  && grep -q "silent names each source that did not, with why" <<<"$bad_quiet" \
  && grep -q "families is the list of the model families that answered" <<<"$bad_families" && grep -q "no more stories flagged than it read" <<<"$bad_flagged" \
  && grep -q "a split is between two model families, and families names one" <<<"$bad_split" && grep -q "digest is the twelve characters" <<<"$bad_digest" \
  && grep -q "stories.read takes by=lem|lead asked:=N answered:=N" <<<"$bad_missing" \
  && [ "$(grep -c '"event": "stories.read", "task": "ticket-word"' "$LOCAL/.git/lem/events.jsonl")" = 1 ]; then
  pass "a read by the lead with one model family in which nobody was confused is one line of the checks, which says the build did not wait for him, and the scout's report is named; a read's event without its form, with fewer than two personas asked, with nobody or more than were asked answering, or with a missing source unnamed is refused, and nothing is written for it"
else
  fail "the read of the rare path: $bad_by / $bad_one / $bad_none / $bad_more / $bad_quiet / $bad_families / $bad_flagged / $bad_split / $bad_digest / $bad_missing / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state ticket-word dropped "the test is over" >/dev/null
# A correction: Lem approves its one story in his name, and the personas do not read it.
task_in "$LOCAL" one-word o.txt o
printf '%s\n' '## Stories' '' 'Kind: correction, because the request is one sentence.' '' '1. The file holds the word the owner asked for.' > "$WORK/correction.md"
lstories approve one-word --file "$WORK/correction.md" --correction >/dev/null 2>&1 || true
to_open one-word || true
text=$LOCAL/.git/lem/tasks/one-word/pr.md
if [ "$(sed -n 1p "$text" 2>/dev/null | cut -c1-10)" = '**Green.**' ] && [ -n "$(approved_day one-word)" ] \
  && grep -qxF -- "- a correction: not read by the personas; Lem approved it in his name on $(approved_day one-word), as a correction" "$text" \
  && ! grep -q 'the stories were read by' "$text"; then
  pass "a correction approved in his name is proposed with the line that the personas did not read it and when Lem approved it for him"
else
  fail "a correction's line: $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state one-word dropped "the test is over" >/dev/null

# No path rule lets a change skip its review: documentation gets one read at the least. A review that no
# source answered is none; it is started once more, and then the request goes on as not reviewed.
project --repo "$LOCAL" task-dir guide-change --ask "Say more in the guide." >/dev/null
tree=$(project --repo "$LOCAL" worktree-dir guide-change)
git -C "$LOCAL" worktree add -q "$tree" -b docs/guide-change main
plan_in "$tree" guide-change "no test: a sentence of the guide, which a person reads"
echo more >> "$tree/docs/guide.md" && git -C "$tree" add -A && git -C "$tree" commit -q -m "docs: more"
project --repo "$tree" state guide-change ready "the report is written" >/dev/null
local_land start guide-change >/dev/null && local_land base guide-change >/dev/null
gate=$(local_land gate guide-change)
out=$(local_land read guide-change)
early=$(status_of local_land propose guide-change --title "docs: more" --notes "$NOTES")
quiet='{"kind": "read", "answered": [], "silent": [{"name": "codex", "why": "the model was at capacity"}]}'
once=$(local_land read guide-change --record "$(record 1 "$quiet")" | field '(d["recorded"]["verdict"], d["next"])')
twice=$(local_land read guide-change --record "$(record 2 "$quiet")" | field 'd["next"]')
local_land propose guide-change --title "docs: more" --notes "$NOTES" >/dev/null
text=$LOCAL/.git/lem/tasks/guide-change/pr.md
agent=$(local_land land guide-change --by agent 2>&1 || true)
if [ "$(field '(d["stories"]["ok"], [w["story"] for w in d["stories"]["without_a_test"]])' <<<"$gate")" = "(True, [1])" ] \
  && [ "$(field '(d["due"], d["floor"])' <<<"$out")" = "('review', 'read')" ] && [ "$early" = 1 ] && [ "$once" = "('not reviewed', 'review')" ] && [ "$twice" = owner ] \
  && [ "$(sed -n 1p "$text")" = '**Not green.**' ] && [ "$(sed -n 3p "$text")" = '- not reviewed: the review was started twice and no source answered' ] \
  && grep -q '^- the review, round 1 (one read; no source answered; no answer from codex (the model was at capacity)): not reviewed$' "$text" \
  && grep -q '^   - no test: a sentence of the guide, which a person reads$' "$text" \
  && grep -q "^- the stories' tests: 0 pass on the branch and fail on the base commit; 1 story has no test$" "$text" \
  && grep -q "the request is not green (not reviewed" <<<"$agent"; then
  pass "a change of documentation only is not proposed without a review; a review that nobody answered is started once more, and after the second the request is proposed as not reviewed, which no agent merges"
else
  fail "a documentation change and a review with no answer: $gate / $out / $once / $twice / $agent / $(cat "$text" 2>/dev/null)"
fi
local_land land guide-change --by owner >/dev/null && local_land clean guide-change >/dev/null

# A review is of the change as it is: a change of one space is another change. And a floor that rises
# after a review, because the owner says careful, asks for the larger review.
task_in "$LOCAL" spaces s.txt word
tree=$(project --repo "$LOCAL" worktree-dir spaces)
echo 'value = "a b"' > "$tree/v.py" && app_py new old > "$tree/app.py"
git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: a value"
local_land start spaces >/dev/null && local_land base spaces >/dev/null && local_land gate spaces >/dev/null
local_land read spaces --record "$(clean 1)" >/dev/null
same=$(local_land read spaces | field 'd["due"]')
# the same edit in the next function of the file: every line of the diff is the same, with its
# context, and only its place is not
app_py old new > "$tree/app.py"
git -C "$tree" commit -q -am "fix: the other function" && local_land gate spaces >/dev/null
moved=$(local_land read spaces | field '(d["due"], d["round"])')
git -C "$tree" revert --no-edit HEAD >/dev/null && local_land gate spaces >/dev/null
back=$(local_land read spaces | field 'd["due"]')
task_dir=$(project --repo "$LOCAL" task-dir spaces)
printf '%s\n' 'slug: spaces' 'careful: the owner says so' > "$task_dir/brief.md"
raised=$(local_land read spaces | field '(d["due"], d["floor"])')
rm "$task_dir/brief.md"
echo 'value = "ab"' > "$tree/v.py" && git -C "$tree" commit -q -am "fix: no space" && local_land gate spaces >/dev/null
spaced=$(local_land read spaces | field '(d["due"], d["round"])')
local_land read spaces --record "$(clean 2)" >/dev/null
printf '%s\n' 'slug: spaces' 'careful: the owner says so' > "$task_dir/brief.md"
late=$(local_land read spaces | field 'd["due"] + ": " + d["why"]')
if [ "$same" = none ] && [ "$moved" = "('review', 2)" ] && [ "$back" = none ] && [ "$raised" = "('review', 'full')" ] && [ "$spaced" = "('review', 2)" ] \
  && [ "$late" = "owner: two rounds reviewed it: it was one read, and this change gets the project's full set at the least (the request is careful: the owner says so)" ]; then
  pass "a change of one space after a review, or the same edit in another place of the file, is a change nobody reviewed, and a change that came back to what was reviewed is not; and when the owner calls a reviewed task careful, the one read no longer counts: the full set is due, or after two rounds the request is not green for it"
else
  fail "a review is of the change as it is: $same / $moved / $back / $raised / $spaced / $late"
fi
project --repo "$LOCAL" state spaces dropped "the test is over" >/dev/null

# What a review saw outside the change is filed after it, as new items in the backlog folder: that asks
# for no other review. Any other file does, an item that was on the base included; the folder is a
# folder and not a pattern, and the root of the repository is no backlog folder for this.
# backlog_repo NAME FOLDER: a repository whose settings name FOLDER as the backlog, with one item there on the base
backlog_repo() {
  local repo=$WORK/$1
  git init -q -b main "$repo" && ident "$repo" && project --repo "$repo" init --base main >/dev/null
  printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[gate]' 'commands = ["true"]' '[paths]' "backlog = \"$2\"" > "$repo/.lem/project.toml"
  mkdir -p "$repo/$2" && echo '# an item from before' > "$repo/$2/existing.md" && echo one > "$repo/app.txt"
  git -C "$repo" add -A && git -C "$repo" commit -q -m "chore: start"
}
# reviewed_then REPO SLUG CHANGE: a task whose change one read reviewed, then CHANGE run in its
# worktree and committed, and the checks again; prints what is due
reviewed_then() {
  local tree
  task_in "$1" "$2" app.txt two
  tree=$(project --repo "$1" worktree-dir "$2")
  land --repo "$1" start "$2" >/dev/null && land --repo "$1" base "$2" >/dev/null && land --repo "$1" gate "$2" >/dev/null
  land --repo "$1" read "$2" --record "$(clean 1)" >/dev/null
  (cd "$tree" && sh -c "$3")
  git -C "$tree" add -A && git -C "$tree" commit -q -m "docs(backlog): after the review" && land --repo "$1" gate "$2" >/dev/null
  land --repo "$1" read "$2" | field 'd["due"]'
  project --repo "$1" state "$2" dropped "the test is over" >/dev/null
}
backlog_repo backlog-land docs/backlog
BLG=$WORK/backlog-land
added=$(reviewed_then "$BLG" new-item 'echo "# a defect from before" > docs/backlog/new.md')
edited=$(reviewed_then "$BLG" edited-item 'echo more >> docs/backlog/existing.md')
removed=$(reviewed_then "$BLG" removed-item 'rm docs/backlog/existing.md')
if [ "$added" = none ] && [ "$edited" = review ] && [ "$removed" = review ]; then
  pass "a new item in the backlog folder after a review keeps the review, and an edit or a deletion of an item that was on the base asks for another"
else
  fail "backlog items after a review: $added / $edited / $removed"
fi
backlog_repo backlog-star 'docs/backlog-x*'
inside=$(reviewed_then "$WORK/backlog-star" in-folder 'echo "# an item" > "docs/backlog-x*/new.md"')
beside=$(reviewed_then "$WORK/backlog-star" beside-folder 'mkdir -p docs/backlog-xy && echo "x = 1" > docs/backlog-xy/app.py')
backlog_repo backlog-root .
rooted=$(reviewed_then "$WORK/backlog-root" root-item 'echo "# an item" > new.md')
if [ "$inside" = none ] && [ "$beside" = review ] && [ "$rooted" = review ]; then
  pass "the backlog folder is read as the path it names, not as a pattern: a file in docs/backlog-xy is no item of the folder docs/backlog-x*; and a backlog folder that is the root keeps no review over a new file"
else
  fail "the backlog folder as a path: $inside / $beside / $rooted"
fi

# A review names each defect it saw outside the change, and `land.py file` files each one as an item
# of the backlog: a count of them is no record. A record of the form that only counted them is refused,
# in a new record and in a kept one; 0 is no defect.
task_in "$BLG" outside-form app.txt two
land --repo "$BLG" start outside-form >/dev/null && land --repo "$BLG" base outside-form >/dev/null && land --repo "$BLG" gate outside-form >/dev/null
counted=$(land --repo "$BLG" read outside-form --record "$(record 1 '{"kind": "read", "answered": ["codex"], "outside": 2}')" 2>&1 >/dev/null || true)
unnamed=$(land --repo "$BLG" read outside-form --record "$(record 1 '{"kind": "read", "answered": ["codex"], "outside": [{"where": "app.txt"}]}')" 2>&1 >/dev/null || true)
none=$(land --repo "$BLG" read outside-form --record "$(record 1 '{"kind": "read", "answered": ["codex"], "outside": 0}')" | field '(d["recorded"]["outside"], d["to_file"])')
"$PY" -c 'import json, sys; p = sys.argv[1]; d = json.load(open(p)); d["reads"][0]["outside"] = 2; json.dump(d, open(p, "w"))' "$BLG/.git/lem/tasks/outside-form/landing.json"
kept_read=$(land --repo "$BLG" read outside-form 2>&1 >/dev/null || true)
kept_propose=$(land --repo "$BLG" propose outside-form --title "fix: outside-form" --notes "$NOTES" 2>&1 >/dev/null || true)
if grep -q '.outside. is the list of the defects' <<<"$counted" && grep -q '"where"' <<<"$counted" && grep -q '.outside. is the list of the defects' <<<"$unnamed" \
  && [ "$none" = "([], [])" ] && grep -q "a form of the record that was never released" <<<"$kept_read" && grep -q "landing.json" <<<"$kept_read" \
  && grep -q "a form of the record that was never released" <<<"$kept_propose"; then
  pass "a record names each defect outside the change, with where, title and what: a count is refused, 0 is no defect, and a kept record that only counted them stops read and propose and names its file"
else
  fail "the form of the outside defects: $counted / $unnamed / $none / $kept_read / $kept_propose"
fi
project --repo "$BLG" state outside-form dropped "the test is over" >/dev/null

# Two rounds that saw two different defects give two items, each filed by the script in a commit of
# its own; a second run files nothing; propose waits for each one, and the pull request names them.
A='{"where": "src/json.py:parse", "title": "Empty input crashes the parser", "what": "parse with an empty string raises IndexError, on the base commit too."}'
B='{"where": "src/csv.py:read", "title": "A quoted comma splits the field", "what": "read of a line with a comma inside quotes gives three fields, on the base commit too."}'
# the start of a record, and outside DEFECT...: its end, with the defects (bash 3.2 splits a quote escaped inside "$(...)")
a_read='{"kind": "read", "answered": ["codex"]'
read_must_fix='{"kind": "read", "answered": ["codex"], "must_fix": 1'
a_round='{"kind": "round", "ran": [{"name": "correctness", "why": "a file of the app changes"}], "answered": ["codex"]'
outside() { local IFS=,; printf '"outside": [%s]}' "$*"; }
task_in "$BLG" two-defects app.txt two
tree=$(project --repo "$BLG" worktree-dir two-defects)
land --repo "$BLG" start two-defects >/dev/null && land --repo "$BLG" base two-defects >/dev/null && land --repo "$BLG" gate two-defects >/dev/null
first=$(land --repo "$BLG" read two-defects --record "$(record 1 "$read_must_fix, $(outside "$A")")" | field '(d["next"], [(f["round"], f["title"]) for f in d["to_file"]])')
filed_a=$(land --repo "$BLG" file two-defects | field '([(f["round"], f["item"]) for f in d["filed"]], d["same"])')
echo fixed > "$tree/notes.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: the must-fix" && land --repo "$BLG" gate two-defects >/dev/null
second=$(land --repo "$BLG" read two-defects --record "$(record 2 "$a_round, $(outside "$B")")" | field '(d["next"], [(f["round"], f["title"]) for f in d["to_file"]])')
unfiled=$(land --repo "$BLG" propose two-defects --title "fix: two-defects" --notes "$NOTES" 2>&1 >/dev/null || true)
filed_b=$(land --repo "$BLG" file two-defects | field '[(f["round"], f["item"]) for f in d["filed"]]')
commit_b=$(git -C "$tree" show --name-only --format=%s HEAD | tr '\n' '|')
tip_b=$(git -C "$tree" rev-parse HEAD)
rerun=$(land --repo "$BLG" file two-defects | field '(d["filed"], d["same"])')
[ "$(git -C "$tree" rev-parse HEAD)" = "$tip_b" ] || rerun="$rerun, and a commit"
land --repo "$BLG" gate two-defects >/dev/null
after=$(land --repo "$BLG" read two-defects | field '(d["due"], d["to_file"])')
green=$(land --repo "$BLG" propose two-defects --title "fix: two-defects" --notes "$NOTES" | field 'd["green"]')
text=$BLG/.git/lem/tasks/two-defects/pr.md
item="$tree/docs/backlog/empty-input-crashes-the-parser.md"
logged=$("$PY" -c 'import json, sys; print([[i["item"] for i in e["items"]] for e in map(json.loads, open(sys.argv[1])) if e["event"] == "review.filed" and e["task"] == "two-defects"])' "$BLG/.git/lem/events.jsonl")
if [ "$first" = "('review', [(1, 'Empty input crashes the parser')])" ] && [ "$filed_a" = "([(1, 'docs/backlog/empty-input-crashes-the-parser.md')], [])" ] \
  && [ "$second" = "('none', [(2, 'A quoted comma splits the field')])" ] && grep -q "A quoted comma splits the field" <<<"$unfiled" && grep -q "land.py file two-defects" <<<"$unfiled" \
  && [ "$filed_b" = "[(2, 'docs/backlog/a-quoted-comma-splits-the-field.md')]" ] \
  && [ "$commit_b" = "docs(backlog): what review round 2 saw outside two-defects||docs/backlog/a-quoted-comma-splits-the-field.md|" ] \
  && [ "$rerun" = "([], [])" ] && [ "$after" = "('none', [])" ] && [ "$green" = True ] \
  && [ "$(sed -n 1,5p "$item" | tr '\n' '|')" = "---|worth: later|where: src/json.py:parse|added: $(date +%F)|---|" ] && [ "$(sed -n 6p "$item")" = "# Empty input crashes the parser" ] \
  && grep -qx "parse with an empty string raises IndexError, on the base commit too." "$item" \
  && grep -qx "Seen outside the change by review round 1 of task two-defects ($(date +%F)); the base commit has it." "$item" \
  && grep -q '^- the review, round 1 (one read; answered: codex): must-fix, 1 must-fix, 0 should, 0 nit; it saw 1 defect outside the change, filed as .docs/backlog/empty-input-crashes-the-parser.md.$' "$text" \
  && grep -q '^- the review, round 2 .*: clean, 0 must-fix, 0 should, 0 nit; it saw 1 defect outside the change, filed as .docs/backlog/a-quoted-comma-splits-the-field.md.$' "$text" \
  && [ "$logged" = "[['docs/backlog/empty-input-crashes-the-parser.md'], ['docs/backlog/a-quoted-comma-splits-the-field.md']]" ]; then
  pass "two rounds that saw two different defects outside the change give two items in the backlog's format, each committed alone by land.py file; a second run files nothing; propose waits for each, and the pull request names each item"
else
  fail "the filing of two defects: $first / $filed_a / $second / $unfiled / $filed_b / $commit_b / $rerun / $after / $green / $logged / $(cat "$item" 2>/dev/null) / $(grep 'the review, round' "$text" 2>/dev/null)"
fi
project --repo "$BLG" state two-defects dropped "the test is over" >/dev/null

# An item that was on the branch before the review is no proof that a defect was filed; an item that
# was filed and then removed stops propose until it is back, and `file --again` puts it back.
task_in "$BLG" item-goes app.txt two
tree=$(project --repo "$BLG" worktree-dir item-goes)
echo '# a slow report' > "$tree/docs/backlog/first.md" && git -C "$tree" add -A && git -C "$tree" commit -q -m "docs(backlog): a slow report"
land --repo "$BLG" start item-goes >/dev/null && land --repo "$BLG" base item-goes >/dev/null && land --repo "$BLG" gate item-goes >/dev/null
land --repo "$BLG" read item-goes --record "$(record 1 "$a_read, $(outside "$A")")" >/dev/null
before=$(land --repo "$BLG" propose item-goes --title "fix: item-goes" --notes "$NOTES" 2>&1 >/dev/null || true)
land --repo "$BLG" file item-goes >/dev/null
rm "$tree/docs/backlog/empty-input-crashes-the-parser.md" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: an item less" && land --repo "$BLG" gate item-goes >/dev/null
gone=$(land --repo "$BLG" propose item-goes --title "fix: item-goes" --notes "$NOTES" 2>&1 >/dev/null || true)
back=$(land --repo "$BLG" file item-goes --again | field '[f["item"] for f in d["filed"]]')
land --repo "$BLG" gate item-goes >/dev/null
green=$(land --repo "$BLG" propose item-goes --title "fix: item-goes" --notes "$NOTES" | field 'd["green"]')
if grep -q "Empty input crashes the parser" <<<"$before" && grep -q "land.py file item-goes" <<<"$before" \
  && grep -q "docs/backlog/empty-input-crashes-the-parser.md" <<<"$gone" && grep -q "was removed after it was filed" <<<"$gone" && grep -q -- "--again" <<<"$gone" && grep -q "worth: no" <<<"$gone" \
  && [ "$back" = "['docs/backlog/empty-input-crashes-the-parser.md']" ] && [ "$green" = True ]; then
  pass "an item that was on the branch before the review proves nothing; an item that was filed and then removed stops propose with its path and the two ways on, and file --again puts it back"
else
  fail "an item that goes: $before / $gone / $back / $green"
fi
project --repo "$BLG" state item-goes dropped "the test is over" >/dev/null

# One defect seen word for word by two rounds is one item, also when its file name needed the suffix
# of its place; two defects of one place and one title, with two different runs, are two items. And a
# worktree with a change nobody committed is refused.
D='{"where": "src/json.py:parse", "title": "An item from before", "what": "parse of a document with no root returns None, on the base commit too."}'
E='{"where": "src/json.py:parse", "title": "An item from before", "what": "parse of a document of one number returns a string, on the base commit too."}'
task_in "$BLG" same-defect app.txt two
tree=$(project --repo "$BLG" worktree-dir same-defect)
echo '# An item from before' > "$tree/docs/backlog/an-item-from-before.md" && git -C "$tree" add -A && git -C "$tree" commit -q -m "docs(backlog): an item with no place"
land --repo "$BLG" start same-defect >/dev/null && land --repo "$BLG" base same-defect >/dev/null && land --repo "$BLG" gate same-defect >/dev/null
land --repo "$BLG" read same-defect --record "$(record 1 "$read_must_fix, $(outside "$D")")" >/dev/null
once=$(land --repo "$BLG" file same-defect | field '[f["item"] for f in d["filed"]]')
echo fixed > "$tree/notes.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: the must-fix" && land --repo "$BLG" gate same-defect >/dev/null
land --repo "$BLG" read same-defect --record "$(record 2 "$a_round, $(outside "$D" "$E")")" >/dev/null
echo stray > "$tree/stray.txt"
dirty=$(land --repo "$BLG" file same-defect 2>&1 >/dev/null || true)
rm "$tree/stray.txt"
twice=$(land --repo "$BLG" file same-defect | field '([f["item"] for f in d["filed"]], [f["item"] for f in d["same"]])')
if [ "$once" = "['docs/backlog/an-item-from-before-json-parse.md']" ] \
  && [ "$twice" = "(['docs/backlog/an-item-from-before-json-parse-2.md'], ['docs/backlog/an-item-from-before-json-parse.md'])" ] \
  && [ "$(cat "$tree/docs/backlog/an-item-from-before.md")" = "# An item from before" ] && grep -q "commit them or remove them" <<<"$dirty"; then
  pass "a defect that two rounds saw word for word is one item, also under the suffix of its place, and two defects of one place and title with two runs are two; file refuses a worktree with a change nobody committed"
else
  fail "the same defect twice: $once / $twice / $dirty"
fi
project --repo "$BLG" state same-defect dropped "the test is over" >/dev/null

# The owner's "no" is `worth: no` and his reason in the item: the same defect seen again by the next
# round is still that item, and nothing is filed over his word.
task_in "$BLG" owner-says-no app.txt two
tree=$(project --repo "$BLG" worktree-dir owner-says-no)
land --repo "$BLG" start owner-says-no >/dev/null && land --repo "$BLG" base owner-says-no >/dev/null && land --repo "$BLG" gate owner-says-no >/dev/null
land --repo "$BLG" read owner-says-no --record "$(record 1 "$read_must_fix, $(outside "$A")")" >/dev/null
land --repo "$BLG" file owner-says-no >/dev/null
item=$tree/docs/backlog/empty-input-crashes-the-parser.md
"$PY" -c 'import sys; p = sys.argv[1]; t = open(p).read().replace("worth: later", "worth: no").replace("\n\nSeen outside", "\n\nThe owner: an empty input never reaches parse, the reader refuses it first.\n\nSeen outside"); open(p, "w").write(t)' "$item"
echo fixed > "$tree/notes.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: the must-fix, and the owner's no" && land --repo "$BLG" gate owner-says-no >/dev/null
land --repo "$BLG" read owner-says-no --record "$(record 2 "$a_round, $(outside "$A")")" >/dev/null
again=$(land --repo "$BLG" file owner-says-no | field '([f["item"] for f in d["filed"]], [f["item"] for f in d["same"]])')
if [ "$again" = "([], ['docs/backlog/empty-input-crashes-the-parser.md'])" ] && grep -qx "worth: no" "$item" && grep -q "^The owner: " "$item" \
  && [ "$(git -C "$tree" ls-files docs/backlog | tr '\n' ' ')" = "docs/backlog/empty-input-crashes-the-parser.md docs/backlog/existing.md " ] && [ -z "$(git -C "$tree" status --porcelain)" ]; then
  pass "an item the owner set to worth: no, with his reason in it, is still the item of the same defect when the next round sees it again: nothing is filed over his no"
else
  fail "the owner's no and the same defect again: $again / $(git -C "$tree" ls-files docs/backlog) / $(cat "$item")"
fi
project --repo "$BLG" state owner-says-no dropped "the test is over" >/dev/null

# The bar: a suppression, a pattern of the project's own, a skipped module, fewer assertions, a test
# that goes out of a Rust module and a deleted test file, each refused until the plan gives the
# file's reason. A suppression that only got another space is not a new one.
task_in "$LOCAL" bar-change calc.py one
tree=$(project --repo "$LOCAL" worktree-dir bar-change)
echo 'import os  # noqa: F401' > "$tree/calc.py" && echo 'test -f calc.py' > "$tree/tests/bar-change.sh" && echo 'puts 1 # rubocop:disable Style/X' > "$tree/x.rb"
printf '%s\n' 'import pytest' 'pytestmark = pytest.mark.skip(reason="later")' 'def test_base():' '    assert 1 + 1 == 2' > "$tree/tests/test_base.py"
printf '%s\n' 'import plugin  # noqa: F401' 'import other  # noqa' > "$tree/plug.py" && echo 'pub fn one() -> i32 { 1 }' > "$tree/lib.rs"
git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: with marks"
local_land start bar-change >/dev/null && local_land base bar-change >/dev/null
out=$(local_land gate bar-change 2>/dev/null || true)
err=$(local_land gate bar-change 2>&1 >/dev/null || true)
git -C "$tree" rm -q tests/test_base.py && git -C "$tree" commit -q -m "fix: the old test goes"
gone=$(local_land gate bar-change 2>/dev/null || true)
if [ "$(field '(sorted((e["file"], e["what"], e["reason"]) for e in d["bar"]["lowered"]), d["bar"]["not_covered"], d["bar"]["own_patterns"])' <<<"$out")" \
  = "([('calc.py', '# noqa', None), ('lib.rs', '1 assertion(s) fewer', None), ('plug.py', '# noqa', None), ('tests/test_base.py', '1 assertion(s) fewer', None), ('tests/test_base.py', 'pytest.mark.skip', None), ('x.rb', 'rubocop:disable', None)], ['.rb'], 1)" ] \
  && grep -q "the change lowers the bar with no reason given" <<<"$err" && grep -q "## The bar" <<<"$err" && [ "$(kept_in "$LOCAL" bar-change gated)" = None ] \
  && [ "$(field 'sorted((e["file"], e["what"]) for e in d["bar"]["lowered"] if e["file"].startswith("tests/"))' <<<"$gone")" = "[('tests/test_base.py', 'a test file is deleted')]" ] \
  && [ "$(field '[e["line"] for e in d["bar"]["lowered"] if e["file"] == "plug.py"]' <<<"$out")" = "['import other  # noqa']" ] \
  && [ "$(status_of local_land read bar-change)" = 1 ]; then
  pass "a change that adds a suppression, a mark the project named, a skip of a whole module, fewer assertions, a test taken out of a Rust module or a deleted test file is refused until a reason is given; a suppression that was there and only got a space is none, and one that got wider is one; and the result names the kind of file the bar has no marks for"
else
  fail "the bar: $out / $err / $gone"
fi
plan=$tree/docs/plans/20261115-bar-change.md
# shellcheck disable=SC2016  # the backticks are the plan's own marks around a path
printf '%s\n' '' '## The bar' '' '- calc.py: the import registers a plugin.' '- `x.rb`: the cop reads this line wrong.' '- tests/test_base.py: the sum moved to another module with its test.' '- lib.rs: one() has its test in tests/one.rs now.' '- plug.py: E402 and F401 both hold for that import.' >> "$plan"
git -C "$tree" commit -q -am "docs: why the bar is lower"
out=$(local_land gate bar-change)
small=$(local_land read bar-change | field 'd["floor"]')
unsaid=$(local_land read bar-change --record "$(clean 1)" 2>&1 || true)
local_land read bar-change --record "$(record 1 '{"kind": "read", "answered": ["codex"], "bar": [{"name": "calc.py", "why": "the plugin is loaded by that import."}, {"name": "x.rb", "why": "the cop is wrong here."}, {"name": "tests/test_base.py", "why": "the sum and its test are in the other module."}, {"name": "lib.rs", "why": "tests/one.rs is not in this change."}, {"name": "plug.py", "why": "name the two codes."}]}')" >/dev/null
proposed=$(local_land propose bar-change --title "fix: marks" --notes "$NOTES")
agent=$(local_land land bar-change --by agent 2>&1 || true)
text=$LOCAL/.git/lem/tasks/bar-change/pr.md
# shellcheck disable=SC2016
if [ "$(field 'sorted(e["reason"] for e in d["bar"]["lowered"])' <<<"$out")" = "['E402 and F401 both hold for that import.', 'one() has its test in tests/one.rs now.', 'the cop reads this line wrong.', 'the import registers a plugin.', 'the sum moved to another module with its test.']" ] \
  && [ "$small" = read ] && grep -q "the change lowers the bar in calc.py, lib.rs, plug.py, tests/test_base.py, x.rb and the record says nothing of it" <<<"$unsaid" \
  && [ "$(field '(d["green"], len(d["not_green"]))' <<<"$proposed")" = "(False, 5)" ] && [ "$(sed -n 1p "$text")" = '**Not green.**' ] \
  && grep -q '^- the bar is lower in `calc.py` (# noqa)\. The builder: the import registers a plugin\. The review: the plugin is loaded by that import\.$' "$text" \
  && grep -q '^- the bar is lowered, with these reasons:$' "$text" && grep -q '^  - `calc.py` (# noqa): the import registers a plugin\.$' "$text" \
  && grep -q "^- the bar has no marks of its own for files of these kinds: .rb (the project's 1 pattern(s) in gate.bar were looked for)$" "$text" \
  && grep -q "the request is not green (the bar is lower in" <<<"$agent" \
  && [ "$(grep -c '"event": "proposed", "task": "bar-change", "green": false' "$LOCAL/.git/lem/events.jsonl")" = 1 ]; then
  pass "with a reason for each file in the plan the gate passes, and the request is still not green: the review says what it thinks of each reason, the text opens with each lowered bar, its reason and the review's word, the event log counts it, and no agent merges it"
else
  fail "the bar with reasons: $out / $unsaid / $proposed / $agent / $(cat "$text" 2>/dev/null)"
fi
# What makes a request large or careful, read from its plan and its paths.
local_land start bar-change >/dev/null
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("1. The change.", "1. The change.\n2. Its test.\n3. Its page.\n4. Its note."))' "$plan"
git -C "$tree" commit -q -am "docs: four tasks" && local_land gate bar-change >/dev/null
large=$(local_land read bar-change | field '(d["floor"], d["why"])')
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("\n2. Its test.\n3. Its page.\n4. Its note.", "\n\ncareful: yes, a price is rounded here."))' "$plan"
git -C "$tree" commit -q -am "docs: one task, and careful" && local_land gate bar-change >/dev/null
said=$(local_land read bar-change | field '(d["floor"], d["why"])')
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("\n\ncareful: yes, a price is rounded here.", ""))' "$plan"
mkdir -p "$tree/billing" && echo 'PRICE = 100' > "$tree/billing/price.py" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: a price" && local_land gate bar-change >/dev/null
path=$(local_land read bar-change | field '(d["floor"], d["why"])')
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("## Tasks\n\n1. The change.\n", ""))' "$plan"
git -C "$tree" commit -q -am "docs: no tasks" && local_land gate bar-change >/dev/null
err=$(local_land read bar-change 2>&1 || true)
if [ "$large" = "('round', 'the plan has 4 tasks, more than three')" ] && [ "$said" = "('full', 'the request is careful: the plan says so')" ] \
  && [ "$path" = "('full', 'the request is careful: billing/price.py is a careful path (billing/*)')" ] && grep -q "has no .## Tasks. section with numbered tasks" <<<"$err"; then
  pass "a plan of more than three tasks gets a round at the least, a plan that says careful and a careful path get the full set, and a plan with no task list is refused, not taken for a small one"
else
  fail "large and careful: $large / $said / $path / $err"
fi
project --repo "$LOCAL" state bar-change dropped "the test is over" >/dev/null

# Careful only by its diff: a careful path the plan's own call missed. No talk was due, the text says
# why it had none, and the miss is one event for the retro, also after a second proposal.
task_in "$LOCAL" price-change seven.txt seven
tree=$(project --repo "$LOCAL" worktree-dir price-change)
mkdir -p "$tree/billing" && echo 'PRICE = 7' > "$tree/billing/price.py" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: a price"
local_land start price-change >/dev/null && local_land base price-change >/dev/null && local_land gate price-change >/dev/null
local_land read price-change --record "$(record 1 '{"kind": "full", "ran": [{"name": "default", "why": "a price changes"}], "answered": ["codex"]}')" >/dev/null
local_land propose price-change --title "fix: seven" --notes "$MIG" >/dev/null
text=$LOCAL/.git/lem/tasks/price-change/pr.md
first=$(grep -c '"event": "careful.missed", "task": "price-change"' "$LOCAL/.git/lem/events.jsonl" || true)
local_land start price-change >/dev/null && local_land base price-change >/dev/null && local_land gate price-change >/dev/null && local_land propose price-change --title "fix: seven" --notes "$MIG" >/dev/null
if grep -q '^- no plan talk: the request became careful after its plan, by its diff$' "$text" && grep -q '^- careful: yes, billing/price.py is a careful path (billing/\*)$' "$text" \
  && [ "$(head -1 "$text" | cut -c1-10)" = '**Green.**' ] && [ "$first" = 1 ] \
  && [ "$(grep -c '"event": "careful.missed", "task": "price-change"' "$LOCAL/.git/lem/events.jsonl")" = 1 ] \
  && grep -q '"event": "careful.missed", "task": "price-change", "path": "billing/price.py", "pattern": "billing/\*"' "$LOCAL/.git/lem/events.jsonl"; then
  pass "a request careful only by a path its diff matches is proposed with no plan talk, its checks say why it had none, and the careful call its plan missed is one event with the path and its pattern, also after a second proposal"
else
  fail "a request careful by its diff: first $first / $(grep careful.missed "$LOCAL/.git/lem/events.jsonl") / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state price-change dropped "the test is over" >/dev/null

# A GitHub remote: the task ends as a pull request. A stand-in for the `gh` command keeps the pull
# requests in a file and merges in the bare repository, and the remote's address is rewritten to it.
GHO=$WORK/gh-origin.git
GHS=$WORK/gh-shop
git init -q --bare -b main "$GHO"
git clone -q "$GHO" "$GHS" 2>/dev/null && ident "$GHS"
git -C "$GHS" config remote.origin.url https://github.com/acme/shop.git
git -C "$GHS" config "url.$GHO.insteadOf" https://github.com/acme/shop.git
project --repo "$GHS" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[gate]' 'commands = ["true"]' > "$GHS/.lem/project.toml"
git -C "$GHS" add -A && git -C "$GHS" commit -q -m "chore: start" && git -C "$GHS" push -q origin main
mkdir -p "$WORK/bin"
cat > "$WORK/gh.py" <<'PY'
import json, os, subprocess, sys
state_file, origin = os.environ["GH_STATE"], os.environ["GH_ORIGIN"]
state = json.load(open(state_file)) if os.path.exists(state_file) else {"prs": {}, "calls": []}
args = sys.argv[1:]
state["calls"].append(args)
def opt(name): return args[args.index(name) + 1] if name in args else None
def rev(ref): return subprocess.run(["git", "-C", origin, "rev-parse", "--verify", "-q", ref], capture_output=True, text=True).stdout.strip()
out = ""
if args[:2] == ["pr", "list"]:
    out = json.dumps([{"number": int(n), "url": pr["url"]} for n, pr in state["prs"].items() if pr["head"] == opt("--head") and pr["state"] == "OPEN"])
elif args[:2] == ["pr", "create"]:
    n = str(7 + len(state["prs"]))
    state["prs"][n] = {"url": "https://github.com/acme/shop/pull/" + n, "head": opt("--head"), "base": opt("--base"), "title": opt("--title"),
                       "body": open(opt("--body-file")).read(), "state": "OPEN", "merge": None}
    out = state["prs"][n]["url"]
elif args[:2] == ["pr", "edit"]:
    state["prs"][args[2]].update(title=opt("--title"), body=open(opt("--body-file")).read())
elif args[:2] == ["pr", "view"]:
    pr = state["prs"][args[2]]
    out = json.dumps({"state": pr["state"], "headRefOid": rev("refs/heads/" + pr["head"]), "mergeCommit": {"oid": pr["merge"]} if pr["merge"] else None})
elif args[:2] == ["pr", "merge"]:
    pr = state["prs"][args[2]]
    head = rev("refs/heads/" + pr["head"])
    if opt("--match-head-commit") != head:
        sys.exit("the head is another commit")
    subprocess.run(["git", "-C", origin, "update-ref", "refs/heads/" + pr["base"], head], check=True)
    pr.update(state="MERGED", merge=head)
else:
    sys.exit("gh stand-in: no such command: " + " ".join(args))
json.dump(state, open(state_file, "w"))
print(out)
PY
printf '%s\n' '#!/bin/sh' "exec '$PY' -I '$WORK/gh.py' \"\$@\"" > "$WORK/bin/gh" && chmod +x "$WORK/bin/gh"
gh_land() { PATH="$WORK/bin:$PATH" GH_STATE="$WORK/gh.json" GH_ORIGIN="$GHO" "$PY" -B "$LAND" --repo "$GHS" "$@"; }
gh_state() { "$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])); print(eval(sys.argv[2], {"d": d}))' "$WORK/gh.json" "$1"; }
gh_checked() { gh_land start "$1" >/dev/null && gh_land base "$1" >/dev/null && gh_land gate "$1" >/dev/null; }
task_in "$GHS" pr-change p.txt nine
out=$(gh_land start pr-change)
gh_land base pr-change >/dev/null && gh_land gate pr-change >/dev/null && gh_land read pr-change --record "$(clean 1)" >/dev/null
proposed=$(gh_land propose pr-change --title "fix: nine" --notes "$NOTES")
tip=$(git -C "$GHS/.lem/worktrees/pr-change" rev-parse HEAD)
if [ "$(field 'd["forge"]' <<<"$out")" = github ] && [ "$(field 'd["pull_request"]' <<<"$proposed")" = "{'number': 7, 'url': 'https://github.com/acme/shop/pull/7'}" ] \
  && [ "$(status_in "$GHS" pr-change)" = open ] && grep -q "pull request https://github.com/acme/shop/pull/7" "$GHS/.git/lem/tasks/pr-change/state.md" \
  && [ "$(git -C "$GHO" rev-parse refs/heads/fix/pr-change)" = "$tip" ] \
  && [ "$(gh_state '(d["prs"]["7"]["title"], d["prs"]["7"]["base"], d["prs"]["7"]["head"], "## The request" in d["prs"]["7"]["body"], "## Not done" in d["prs"]["7"]["body"])')" = "('fix: nine', 'main', 'fix/pr-change', True, True)" ]; then
  pass "with a GitHub remote the branch is pushed and a pull request is opened with the title and the text, and the task is open with its address"
else
  fail "propose with a forge: $out / $proposed / $(cat "$WORK/gh.json" 2>/dev/null)"
fi
# A second proposal updates the same pull request: once from what was kept, once after the record of it was lost.
project --repo "$GHS" state pr-change ready "the owner asked for more, and it is built" >/dev/null
gh_checked pr-change
again=$(kept_in "$GHS" pr-change pr)/$(kept_in "$GHS" pr-change reads)
gh_land read pr-change --record "$(clean 1)" >/dev/null && gh_land propose pr-change --title "fix: nine, again" --notes "$NOTES" >/dev/null
"$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])); d.pop("pr"); json.dump(d, open(sys.argv[1], "w"))' "$GHS/.git/lem/tasks/pr-change/landing.json"
gh_checked pr-change && gh_land propose pr-change --title "fix: nine, a third time" --notes "$NOTES" >/dev/null
if [ "$(gh_state '(len(d["prs"]), d["prs"]["7"]["title"], sum(c[:2] == ["pr", "create"] for c in d["calls"]), sum(c[:2] == ["pr", "edit"] for c in d["calls"]))')" = "(1, 'fix: nine, a third time', 1, 2)" ] \
  && [ "$(kept_in "$GHS" pr-change pr)" = "{'number': 7, 'url': 'https://github.com/acme/shop/pull/7'}" ] \
  && [ "$again" = "{'number': 7, 'url': 'https://github.com/acme/shop/pull/7'}/None" ]; then
  pass "a task that was built further starts its reviews over and keeps its pull request; a second proposal changes the one that is there, also when the record of it was lost: the forge is asked, and no second one is opened"
else
  fail "a second proposal: $(cat "$WORK/gh.json")"
fi
out=$(gh_land land pr-change --by agent)
if [ "$(field '(d["merged"], d["pull_request"]["number"], d["left_behind"])' <<<"$out")" = "('$tip', 7, None)" ] && [ "$(status_in "$GHS" pr-change)" = landed ] \
  && [ "$(gh_state '[c for c in d["calls"] if c[:2] == ["pr", "merge"]]')" = "[['pr', 'merge', '7', '--match-head-commit', '$tip', '--rebase']]" ] \
  && [ "$(git -C "$GHS" rev-parse main)" = "$tip" ] && [ -f "$GHS/p.txt" ]; then
  pass "a pull request is merged through the forge, only at the commit that was proposed, and the main checkout follows"
else
  fail "merging a pull request: $out"
fi
out=$(gh_land clean pr-change)
if [ "$(field '(d["worktree"], d["branch"])' <<<"$out")" = "(True, 'fix/pr-change')" ] && [ -z "$(git -C "$GHO" branch --list fix/pr-change)" ]; then
  pass "after the merge the worktree and the branch go, the forge's copy of the branch too"
else
  fail "clean after a merged pull request: $out"
fi
# The base moves before the merge; then the owner merges on the forge himself, as one commit.
task_in "$GHS" pr-squashed q.txt ten
gh_checked pr-squashed && gh_land read pr-squashed --record "$(clean 1)" >/dev/null && gh_land propose pr-squashed --title "fix: ten" --notes "$NOTES" >/dev/null
gh_other=$WORK/gh-other
git clone -q "$GHO" "$gh_other" && ident "$gh_other"
echo late > "$gh_other/late.txt" && git -C "$gh_other" add -A && git -C "$gh_other" commit -q -m "feat: late" && git -C "$gh_other" push -q origin main
err=$(gh_land land pr-squashed --by agent 2>&1 || true)
early=$(gh_land merged pr-squashed 2>&1 || true)
# the checks start again for the base that moved, and the owner merges on the forge meanwhile
gh_land start pr-squashed >/dev/null
git -C "$gh_other" merge -q --squash origin/fix/pr-squashed && git -C "$gh_other" commit -q -m "fix: ten (#8)" && git -C "$gh_other" push -q origin main
oid=$(git -C "$gh_other" rev-parse HEAD)
"$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])); d["prs"]["8"].update(state="MERGED", merge=sys.argv[2]); json.dump(d, open(sys.argv[1], "w"))' "$WORK/gh.json" "$oid"
out=$(gh_land merged pr-squashed)
if grep -q "origin/main moved after the checks ran, by files the gate reads (late.txt)" <<<"$err" && grep -q "the pull request is not merged yet" <<<"$early" \
  && [ "$(gh_state 'sum(c[:3] == ["pr", "merge", "8"] for c in d["calls"])')" = 0 ] \
  && [ "$(field '(d["merged"], d["left_behind"])' <<<"$out")" = "('$oid', None)" ] && [ "$(status_in "$GHS" pr-squashed)" = landed ] && [ "$(git -C "$GHS" rev-parse main)" = "$oid" ]; then
  pass "a pull request is not merged over a base that moved by files the gate reads; one the owner merged on the forge as one commit is finished by its own step, also while the task has the landing line again"
else
  fail "a pull request the owner merged: $err / $early / $out"
fi
# A commit that came after the one the forge merged is work nobody merged: its branch stays. And a
# forge that refuses to delete its copy of the branch is said, and the next run tries again.
tree=$GHS/.lem/worktrees/pr-squashed
head=$(git -C "$tree" rev-parse HEAD)
echo more > "$tree/q2.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: after the merge"
after=$(gh_land clean pr-squashed 2>&1 || true)
kept_branch=$(git -C "$GHS" branch --list fix/pr-squashed)
git -C "$GHS" branch -q -f fix/pr-squashed "$head"
# a branch on the forge whose name ends the same way and holds the merged commit: it is not the task's branch
git -C "$GHO" branch -q archive/fix/pr-squashed "$head"
# shellcheck disable=SC2016  # the hook's own argument, read when the hook runs
printf '%s\n' '#!/bin/sh' 'case "$3" in 0000000000000000000000000000000000000000) echo "no deletion here" >&2; exit 1 ;; esac' > "$GHO/hooks/update" && chmod +x "$GHO/hooks/update"
refused=$(gh_land clean pr-squashed 2>&1 || true)
still=$(git -C "$GHS" branch --list fix/pr-squashed)/$(git -C "$GHO" branch --list fix/pr-squashed)
rm "$GHO/hooks/update"
# somebody pushed to the task's branch on the forge after the merge: that copy stays
later=$(git -C "$GHO" -c user.name=t -c user.email=t@t commit-tree -p "$head" -m "fix: pushed later" "$head^{tree}")
git -C "$GHO" update-ref refs/heads/fix/pr-squashed "$later"
left=$(gh_land clean pr-squashed | field '(d["branch"], d["remote"], d["remote_left"] is not None)')
on_forge=$(git -C "$GHO" rev-parse refs/heads/fix/pr-squashed)
git -C "$GHO" update-ref refs/heads/fix/pr-squashed "$head" && git -C "$GHS" branch -q fix/pr-squashed "$head"
cleaned=$(gh_land clean pr-squashed)
if grep -q "the forge merged ${head:0:9}, and the branch has commits after it" <<<"$after" && [ -n "$kept_branch" ] \
  && grep -q "push failed: .*no deletion here" <<<"$refused" && [ "$(tr -d ' *' <<<"$still")" = "fix/pr-squashed/fix/pr-squashed" ] \
  && [ "$left" = "('fix/pr-squashed', None, True)" ] && [ "$on_forge" = "$later" ] && [ -n "$(git -C "$GHO" branch --list archive/fix/pr-squashed)" ] \
  && [ "$(field '(d["worktree"], d["branch"], d["remote"])' <<<"$cleaned")" = "(False, 'fix/pr-squashed', 'fix/pr-squashed')" ] \
  && [ -z "$(git -C "$GHS" branch --list fix/pr-squashed)" ] && [ -z "$(git -C "$GHO" branch --list fix/pr-squashed)" ]; then
  pass "after a merge the forge made as one commit, the branch goes only when its tip is the commit that was merged; a deletion the forge refuses is an error that keeps the local branch; the forge's copy stays when it holds a later commit, whatever another branch with the same last words holds; and a run with nothing in the way removes both"
else
  fail "clean after a merge on the forge: $after / $kept_branch / $refused / $still / $left / $cleaned"
fi

if [ -d "$(dirname "$PROJECT")/__pycache__" ]; then fail "the scripts left no __pycache__"; else pass "the scripts left no __pycache__"; fi

if [ "$fails" -gt 0 ]; then
  printf '\n%s check(s) failed\n' "$fails"
  exit 1
fi
printf '\nall checks passed\n'
