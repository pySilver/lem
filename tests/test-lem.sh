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
if [ "$(status_of project --repo "$OLD" init --base master)" = 1 ] && grep -q "styleguide in .claude/rules" <<<"$err" && [ ! -e "$OLD/.lem" ]; then
  pass "init refuses to choose between the folders already there and a new layout, and names them"
else
  fail "init without --existing: $err"
fi
if [ "$(project --repo "$OLD" existing | field 'sorted(d)')" = "['personas', 'profile', 'review', 'styleguide']" ]; then
  pass "existing lists the settings an older tool already keeps here"
else
  fail "existing: $(project --repo "$OLD" existing)"
fi
NEWLAYOUT=$WORK/newlayout
git init -q -b master "$NEWLAYOUT"
mkdir -p "$NEWLAYOUT/.claude/rules"
project --repo "$NEWLAYOUT" init --base master --existing new >/dev/null
if [ "$(project --repo "$NEWLAYOUT" path styleguide)" = "$NEWLAYOUT/.lem/styleguide" ]; then
  pass "init --existing new starts the skill's own layout beside the older folders"
else
  fail "init --existing new"
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
if [ "$(project --repo "$OLD" show | field 'd["tools"]["annotate"]')" = "my-own-rev" ]; then pass "a project names its own tool for marking up a plan"; else fail "tools.annotate"; fi
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

# The review queue: a landing adds an item, high risk first, and an unread normal item expires.
QUEUE=$PWD/skills/lem/scripts/review_queue.py
queue() { "$PY" -B "$QUEUE" --repo "$OLD" "$@"; }
first=$(queue add report-dates --range abc..def --risk normal)
second=$("$PY" -B "$QUEUE" --repo "$WORK/wt" add auth-token-index --range def..123 --risk high --note "touches the token lookup")
out=$(queue list)
if [ "$first" = 1 ] && [ "$second" = 2 ] && [ "$(field '[i["id"] for i in d]' <<<"$out")" = "[2, 1]" ] && [ "$(field 'd[0]["due"]' <<<"$out")" = "today" ]; then
  pass "a landing from any worktree joins one queue, and a high item is listed first and due today"
else
  fail "queue order: $out"
fi
queue close 2 --outcome "fixed in token-index-added"
if [ "$(queue list --all | field '[(i["id"], i["outcome"]) for i in d]')" = "[(1, None), (2, 'fixed in token-index-added')]" ]; then
  pass "list --all gives every item, closed ones too"
else
  fail "list --all: $(queue list --all)"
fi
if [ "$(grep -c '' "$OLD/.git/lem/review-queue.js")" = 3 ] \
  && [ "$(sed -n 3p "$OLD/.git/lem/review-queue.js")" = "lemReview($(sed -n 3p "$OLD/.git/lem/review-queue.jsonl"));" ]; then
  pass "each queue event is also a line the board can load"
else
  fail "review-queue.js: $(cat "$OLD/.git/lem/review-queue.js")"
fi
if [ "$(status_of queue close 2 --outcome again)" = 1 ] && [ "$(status_of queue close 9 --outcome x)" = 1 ]; then
  pass "closing an item twice, or one that does not exist, is refused"
else
  fail "close refusals"
fi
printf '%s\n' '{"id": 3, "slug": "old-normal", "range": "a..b", "risk": "normal", "note": null, "added": "2020-01-01T00:00:00+00:00", "outcome": null}' \
  '{"id": 4, "slug": "old-high", "range": "b..c", "risk": "high", "note": null, "added": "2020-01-01T00:00:00+00:00", "outcome": null}' >> "$OLD/.git/lem/review-queue.jsonl"
out=$(queue expire)
left=$(queue list)
if [ "$(field 'd["expired"]' <<<"$out")" = "[3]" ] && [ "$(field '[(i["id"], i["due"]) for i in d]' <<<"$left")" = "[(4, 'overdue'), (1, 'when the day allows')]" ]; then
  pass "expire closes an old normal item as not reviewed, and an old high item stays open and overdue"
else
  fail "expire: $out / $left"
fi

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
if [ "$(status_of doctor)" = 1 ] && [ "$(field 'd["ok"]' <<<"$out")" = "False" ] && [ "$(row revmux found <<<"$out")" = "False" ] && [ "$(row git found <<<"$out")" = "True" ]; then
  pass "doctor exits 1 and says so when the review tool is absent"
else
  fail "doctor without revmux: $out"
fi
fake revmux "revmux v9.9.9"
out=$(doctor || true)
if [ "$(status_of doctor)" = 1 ] && [ "$(row revmux detail <<<"$out")" = "revmux v9.9.9" ] && [ "$(row agterm found <<<"$out")" = "False" ] \
  && [ "$(field '[t["name"] for t in d["tools"] if t["name"] == "agterm skill"]' <<<"$out")" = "[]" ] && [ "$(row mailbox-chat need <<<"$out")" = "required" ]; then
  pass "the review tool alone is not enough: agterm and the mailbox are required, and there is no row for the agterm skill without agterm"
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
mkdir -p "$FAKEHOME/.agents/skills/agterm" "$FAKEHOME/.config/cronn"
touch "$FAKEHOME/.agents/skills/agterm/SKILL.md"
out=$(doctor)
if [ "$(field 'd["ok"]' <<<"$out")" = "True" ] && [ "$(row 'agterm skill' detail <<<"$out")" = "$FAKEHOME/.agents/skills/agterm" ] && [ "$(row cronn found <<<"$out")" = "False" ] \
  && [ "$(row plannotator found <<<"$out")" = "False" ] && [ "$(row plannotator need <<<"$out")" = "optional" ] && [ "$(row codex found <<<"$out")" = "False" ]; then
  pass "with git, the review tool, agterm, its skill and the mailbox the check passes, and absent optional tools only change their rows"
else
  fail "doctor with the required set: $out"
fi
fake claude "2.1.325 (Claude Code)"
out=$(doctor || true)
if [ "$(status_of doctor)" = 1 ] && [ "$(row 'lem-builder agent' found <<<"$out")" = "False" ] && [ "$(row 'lem-builder agent' need <<<"$out")" = "required" ]; then
  pass "a machine with Claude Code and no lem-builder agent fails the check"
else
  fail "doctor with claude, no builder: $out"
fi
mkdir -p "$FAKEHOME/.claude/agents"
ln -s "$PWD/agents/lem-builder.md" "$FAKEHOME/.claude/agents/lem-builder.md"
out=$(doctor)
if [ "$(field 'd["ok"]' <<<"$out")" = "True" ] && [ "$(row 'lem-builder agent' detail <<<"$out")" = "$FAKEHOME/.claude/agents/lem-builder.md" ]; then
  pass "the linked lem-builder agent satisfies it"
else
  fail "doctor with the builder linked: $out"
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
mkdir -p "$WORK/jevbin"
# a stand-in for jev: it answers with the probability in JEV_P, or fails as JEV_EXIT says
# shellcheck disable=SC2016  # the stand-in's own variables, expanded when it runs
printf '%s\n' '#!/bin/sh' 'cat > /dev/null' 'if [ -n "$JEV_EXIT" ]; then echo "no key" >&2; exit "$JEV_EXIT"; fi' \
  'printf "{\"answers\": {\"lesson\": {\"probabilities\": {\"lesson\": %s}}}}" "$JEV_P"' > "$WORK/jevbin/jev"
chmod +x "$WORK/jevbin/jev"
printf '%s\n' '{"type": "user", "message": {"content": "hi"}}' '{"type": "assistant", "message": {"content": [{"type": "text", "text": "I pushed it."}]}}' > "$WORK/transcript.jsonl"
event() { printf '{"prompt": "%s", "cwd": "%s", "session_id": "%s", "transcript_path": "%s"}' "$1" "$CQ" "$2" "$WORK/transcript.jsonl"; }
hook() { env PATH="$WORK/jevbin:$PATH" JEV_P="${JEV_P:-0.9}" JEV_EXIT="${JEV_EXIT:-}" "$PY" -B "$CORR" "$1"; }
worker() { printf '{"prompt": "%s", "cwd": "%s", "session": "%s", "transcript": "%s"}' "$1" "$CQ" "$2" "$WORK/transcript.jsonl" | hook worker; }
corr() { "$PY" -B "$CORR" --repo "$CQ" "$@"; }
if [ "$(project --repo "$CQ" show | field 'd["corrections"]["collect"]')" = False ] && grep -q '^collect = false$' "$CQ/.lem/project.toml"; then
  pass "a new project does not collect corrections, and its settings file says where to turn that on"
else
  fail "corrections.collect default"
fi
event "never push without asking" s1 | hook hook
sleep 1
if [ ! -e "$CQ/.git/lem/corrections.jsonl" ] && [ "$(corr list | field '(d["collect"], d["entries"])')" = "(False, 0)" ]; then
  pass "the hook does nothing in a repository whose settings do not say yes"
else
  fail "the hook ran without the project's yes"
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
env PATH="$BIN" "$PY" -B "$CORR" worker <<<"$(printf '{"prompt": "no jev at all", "cwd": "%s", "session": "s8", "transcript": ""}' "$CQ")"
sleep 1
out=$(corr list)
if [ "$(field '(d["entries"], [(g["entries"], g["sessions"], g["p_lesson_max"]) for g in d["groups"]], d["failures"]["count"])' <<<"$out")" = "(3, [(2, 2, 0.9), (1, 1, None)], 2)" ] \
  && grep -q "no key" "$CQ/.git/lem/corrections.log" && grep -q "no .jev. on PATH" "$CQ/.git/lem/corrections.log"; then
  pass "one sentence from two sessions is one group; a low score, a command and injected text queue nothing; a message too long for Jev is queued unjudged; each failure is in the log and counted"
else
  fail "the queue: $out / $(cat "$CQ/.git/lem/corrections.log" 2>&1)"
fi
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
settings_file=$CQ/.lem/project.toml
sed -i.bak 's/^collect = true$/collect = "yes"/' "$settings_file" && rm "$settings_file.bak"
if [ "$(status_of project --repo "$CQ" show)" = 1 ]; then pass "a collect value that is not true or false is refused"; else fail "collect type"; fi

# The setup script: links from the clone into a home, never over something else, and the machine check after them.
SETUP=$PWD/scripts/setup.py
SETHOME=$WORK/sethome
mkdir -p "$SETHOME/.agents/skills/agterm" && touch "$SETHOME/.agents/skills/agterm/SKILL.md"
setup() { env -i PATH="$BIN" HOME="$SETHOME" "$PY" -B "$SETUP" --home "$SETHOME" "$@"; }
out=$(setup --check 2>/dev/null || true)
if [ "$(status_of setup --check)" = 1 ] && [ "$(field 'sorted(set(l["state"] for l in d["links"]))' <<<"$out")" = "['absent']" ] && [ ! -e "$SETHOME/.claude" ]; then
  pass "setup --check reports every link as absent, exits 1 and makes nothing"
else
  fail "setup --check on an empty home: $out"
fi
mkdir -p "$SETHOME/.claude/skills/lem-webrev"
err=$(setup 2>&1 >/dev/null || true)
if [ "$(status_of setup)" = 1 ] && grep -q "1 place(s) hold something else, and nothing was linked" <<<"$err" && [ ! -e "$SETHOME/.claude/skills/lem" ]; then
  pass "one place that holds something else stops the setup before any link is made"
else
  fail "setup over a taken place: $err"
fi
rmdir "$SETHOME/.claude/skills/lem-webrev" && ln -s "$WORK" "$SETHOME/.claude/skills/lem-webrev"
if [ "$(status_of setup)" = 1 ] && [ ! -e "$SETHOME/.claude/skills/lem" ]; then pass "a link that points somewhere else is in the way too"; else fail "setup over another link"; fi
rm "$SETHOME/.claude/skills/lem-webrev"
out=$(setup)
if [ "$(field '(d["linked"], d["machine_ok"], len(d["links"]), [a["name"] for a in d["absent"] if a["need"] == "required"])' <<<"$out")" = "(True, True, $(( $(find "$PWD/skills" -mindepth 2 -maxdepth 2 -name SKILL.md | grep -c '') + 2 )), [])" ] \
  && [ "$(readlink "$SETHOME/.claude/skills/lem")" = "$PWD/skills/lem" ] && [ "$(readlink "$SETHOME/.claude/agents/lem-builder.md")" = "$PWD/agents/lem-builder.md" ] \
  && [ -x "$SETHOME/.local/bin/huddle" ] && [ "$(status_of setup)" = 0 ] && [ "$(status_of setup --check)" = 0 ]; then
  pass "setup links every skill, the builder agent and the huddle command, the machine check then passes, and a second run changes nothing"
else
  fail "setup: $out"
fi
# A link that only ends at the same file by another route is the owner's: a small stand-in clone whose
# agent file is itself a link shows it, and --remove leaves the owner's link alone.
TWIN=$WORK/twin
mkdir -p "$TWIN/scripts" "$TWIN/skills/lem/scripts" "$TWIN/skills/lem-huddle/bin" "$TWIN/agents" "$WORK/twinhome/.claude/agents"
cp "$SETUP" "$TWIN/scripts/setup.py" && cp "$DOCTOR" "$TWIN/skills/lem/scripts/doctor.py"
touch "$TWIN/skills/lem/SKILL.md" "$TWIN/skills/lem-huddle/SKILL.md" "$TWIN/skills/lem-huddle/bin/huddle" "$WORK/shared-agent.md"
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
mkdir -p "$WORK/trialhome/.agents/skills/agterm" && touch "$WORK/trialhome/.agents/skills/agterm/SKILL.md"
out=$(trial)
if [ "$(field '(d["linked"], d["machine_ok"], d["scope"], d["huddle"].startswith("not linked"))' <<<"$out")" = "(True, True, '$TRIAL', True)" ] \
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
if [ "$(field 'sorted(set(l["state"] for l in d["links"]))' <<<"$out")" = "['removed']" ] && [ ! -e "$SETHOME/.claude/skills/lem" ] && [ -e "$SETHOME/.claude/skills/mine" ] && [ ! -e "$SETHOME/.local/bin/huddle" ]; then
  pass "setup --remove takes away the links it made and nothing else"
else
  fail "setup --remove: $out"
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
# A task whose gate is green and whose landing is the owner's: it waits, and it does not go back a phase.
project --repo "$OLD" task-dir owner-lands-it >/dev/null
for block in 'building|plan committed, 3 tasks' 'building|task 3 of 3' 'ready|the report is written' 'landing|the gate runs' 'held|the gate is green on abc1234: the owner lands'; do
  project --repo "$OLD" state owner-lands-it "${block%%|*}" "${block#*|}" >/dev/null
done

# The move of linked settings under .lem: on a task's branch, from a clean tree, with the links two tools need.
MIG=$WORK/mig
git init -q -b main "$MIG"
git -C "$MIG" config user.name t && git -C "$MIG" config user.email t@t
mkdir -p "$MIG/.claude/rules/nested" "$MIG/.revmux/lenses" "$MIG/.revmux/tasks" "$MIG/.personas/cast" "$MIG/docs"
printf '%s\n' '---' 'paths: ["src/**/*.py"]' '---' 'Type every function.' > "$MIG/.claude/rules/10-python.md"
printf '%s\n' 'Never dig up a deleted document.' > "$MIG/.claude/rules/20-conduct.md"
printf '%s\n' '---' 'paths: ["api/**"]' '---' 'Version every route.' > "$MIG/.claude/rules/nested/30-api.md"
echo lens > "$MIG/.revmux/lenses/a.md" && echo round > "$MIG/.revmux/tasks/round-1" && echo shopper > "$MIG/.personas/cast/shopper.md" && echo profile > "$MIG/.personas/profile.md"
printf '%s\n' '.revmux/tasks/' > "$MIG/.gitignore"
printf '%s\n' 'Read .claude/rules/10-python.md first. The lenses are in .revmux/lenses.' > "$MIG/docs/guide.md"
project --repo "$MIG" init --base main --existing link >/dev/null
git -C "$MIG" add -A && git -C "$MIG" commit -q -m "chore: start"
out=$(project --repo "$MIG" migrate plan)
if [ "$(field 'sorted(d["linked"])' <<<"$out")" = "['personas', 'profile', 'review', 'styleguide']" ] \
  && [ "$(field '[(r["file"], r["scoped_to_paths"]) for r in d["rules"]]' <<<"$out")" = "[('10-python.md', True), ('20-conduct.md', False), ('nested/30-api.md', True)]" ] \
  && [ -z "$(git -C "$MIG" status --porcelain)" ]; then
  pass "migrate plan lists the linked folders and each rule file with whether it scopes itself to paths, and changes nothing"
else
  fail "migrate plan: $out"
fi
err=$(project --repo "$MIG" migrate run --styleguide 10-python.md 2>&1 || true)
git -C "$MIG" checkout -q -b chore/settings-move-under-lem
echo stray > "$MIG/stray.txt"
dirty=$(status_of project --repo "$MIG" migrate run --styleguide 10-python.md)
rm "$MIG/stray.txt"
if grep -q "run it on a task's branch, not on main" <<<"$err" && [ "$dirty" = 1 ] && [ "$(status_of project --repo "$MIG" migrate run)" = 1 ] \
  && [ "$(status_of project --repo "$MIG" migrate run --styleguide 99-missing.md)" = 1 ] && [ -z "$(git -C "$MIG" status --porcelain)" ] && [ -d "$MIG/.revmux/lenses" ]; then
  pass "migrate run refuses the base branch, a tree with changes, a rules folder with no file named and an unknown rule file, and moves nothing then"
else
  fail "migrate run refusals: $err"
fi
out=$(project --repo "$MIG" migrate run --styleguide 10-python.md nested/30-api.md)
shown=$(project --repo "$MIG" show)
if [ "$(cat "$MIG/.claude/rules/10-python.md" | tail -1)" = "Type every function." ] && [ -L "$MIG/.claude/rules/10-python.md" ] && [ ! -L "$MIG/.lem/styleguide/10-python.md" ] \
  && [ "$(tail -1 "$MIG/.claude/rules/nested/30-api.md")" = "Version every route." ] && [ -L "$MIG/.claude/rules/nested/30-api.md" ] \
  && [ ! -L "$MIG/.claude/rules/20-conduct.md" ] && [ ! -e "$MIG/.lem/styleguide/20-conduct.md" ] \
  && [ -L "$MIG/.revmux" ] && [ "$(cat "$MIG/.revmux/lenses/a.md")" = lens ] && [ "$(readlink "$MIG/.revmux")" = ".lem/review" ] \
  && [ "$(cat "$MIG/.lem/review/tasks/round-1")" = round ] && [ "$(cat "$MIG/.lem/personas/shopper.md")" = shopper ] && [ "$(cat "$MIG/.lem/profile.md")" = profile ] && [ ! -e "$MIG/.personas/cast" ] \
  && [ "$(field '[d["paths"][n]["path"].split("/mig/")[1] for n in ("styleguide", "review", "personas", "profile")]' <<<"$shown")" = "['.lem/styleguide', '.lem/review', '.lem/personas', '.lem/profile.md']" ]; then
  pass "migrate run moves the named rules, the review folder, the cast and the profile under .lem, leaves a link for each rule and for the review folder, and rewrites the settings"
else
  fail "migrate run: $out / $(git -C "$MIG" status --porcelain)"
fi
if [ "$(field '(d["mentions"][".claude/rules"], d["mentions"][".revmux"])' <<<"$out")" = "(['docs/guide.md'], ['.gitignore', 'docs/guide.md'])" ] \
  && [ "$(git -C "$MIG" status --porcelain | grep -c '^?? ')" = 1 ] && git -C "$MIG" status --porcelain | grep -q '^?? .lem/review/tasks/' \
  && [ "$(git -C "$MIG" diff --cached --name-status | grep -c '^R')" = 3 ] && [ "$(git -C "$MIG" diff --cached --name-status | grep -c '^T')" = 2 ] && [ "$(status_of project --repo "$MIG" migrate run --styleguide)" = 1 ]; then
  pass "it names every tracked file that still holds an old path, stages its own moves and nothing that git ignored, and a second run finds nothing to move"
else
  fail "migrate run output: $out / $(git -C "$MIG" status --porcelain)"
fi

# More shapes of an adoption. small_repo NAME makes a linked repository on a task's branch, ready for a run.
small_repo() {
  local r=$WORK/$1
  git init -q -b main "$r"
  git -C "$r" config user.name t && git -C "$r" config user.email t@t
  mkdir -p "$r/.claude/rules" "$r/.revmux" "$r/.personas/cast"
  echo 'Type every function.' > "$r/.claude/rules/a.md" && echo config > "$r/.revmux/config" && echo shopper > "$r/.personas/cast/shopper.md"
  echo 'The other one is .personas/cast/b.md.' > "$r/.personas/cast/a.md"
  project --repo "$r" init --base main --existing link >/dev/null
  git -C "$r" add -A && git -C "$r" commit -q -m "chore: start" && git -C "$r" checkout -q -b chore/move
  echo "$r"
}
r=$(small_repo twice)
mkdir -p "$r/.lem/styleguide" && echo taken > "$r/.lem/styleguide/sub" && git -C "$r" add -A && git -C "$r" commit -q -m "chore: a file in the way"
mkdir "$r/.claude/rules/sub" && echo 'Nested.' > "$r/.claude/rules/sub/b.md" && git -C "$r" add -A && git -C "$r" commit -q -m "docs: a nested rule"
if [ "$(status_of project --repo "$r" migrate run --styleguide a.md a.md)" = 1 ] && [ "$(status_of project --repo "$r" migrate run --styleguide sub/b.md)" = 1 ] \
  && [ -z "$(git -C "$r" status --porcelain)" ] && [ -d "$r/.personas/cast" ] && [ ! -L "$r/.revmux" ]; then
  pass "a rule named twice, and a rule whose new place has a file in the way, are refused before anything moves"
else
  fail "migrate preflight: $(git -C "$r" status --porcelain)"
fi
r=$(small_repo ignored)
printf '%s\n' '.revmux' > "$r/.gitignore" && mkdir "$r/.revmux/tasks" && echo session > "$r/.revmux/tasks/session"
git -C "$r" add -A && git -C "$r" commit -q -m "chore: ignore the review folder, keep its config"
out=$(project --repo "$r" migrate run --styleguide)
if [ "$(cat "$r/.lem/review/tasks/session")" = session ] && [ "$(cat "$r/.revmux/config")" = config ] && [ -L "$r/.revmux" ] \
  && [ "$(git -C "$r" ls-files .lem/review .revmux | tr '\n' ' ')" = ".lem/review/config .revmux " ] \
  && [ "$(field '[x["name"] for x in d["left"]]' <<<"$out")" = "['styleguide']" ] && [ "$(project --repo "$r" migrate plan | field 'sorted(d["linked"])')" = "['styleguide']" ] \
  && [ "$(field 'd["mentions"][".personas/cast"]' <<<"$out")" = "['.lem/personas/a.md']" ]; then
  pass "an ignored review folder moves with its untracked files, its tracked file and its link stay tracked, an empty rule list leaves the rules linked, and a moved file that names an old path is in the mentions"
else
  fail "migrate with an ignored review folder: $out / $(git -C "$r" status --porcelain)"
fi
r=$(small_repo untracked)
git -C "$r" rm -q --cached .lem/project.toml && git -C "$r" commit -q -m "chore: stop tracking the settings" && echo '.lem/project.toml' > "$r/.gitignore" && git -C "$r" add .gitignore && git -C "$r" commit -q -m "chore: ignore them"
err=$(project --repo "$r" migrate run --styleguide 2>&1 || true)
if grep -q "is not tracked by git" <<<"$err" && [ -d "$r/.revmux" ] && [ ! -L "$r/.revmux" ] && [ -z "$(git -C "$r" status --porcelain)" ]; then
  pass "settings that git does not track stop the move before it starts"
else
  fail "migrate with untracked settings: $err"
fi
r=$(small_repo linked)
git -C "$r" mv .revmux old-review && ln -s old-review "$r/.revmux" && git -C "$r" add -A && git -C "$r" commit -q -m "chore: the review folder behind a link"
err=$(project --repo "$r" migrate run --styleguide 2>&1 || true)
if grep -q ".revmux is a link to old-review" <<<"$err" && [ "$(cat "$r/.revmux/config")" = config ] && [ -d "$r/.personas/cast" ] && [ -z "$(git -C "$r" status --porcelain)" ]; then
  pass "a linked folder that is itself a link is refused with the two ways to fix it, and nothing moves"
else
  fail "migrate with a link as the source: $err"
fi
r=$(small_repo slash)
sed -i.bak 's|^review = ".revmux"$|review = ".revmux/"|' "$r/.lem/project.toml" && rm "$r/.lem/project.toml.bak" && git -C "$r" commit -q -am "chore: a trailing slash"
if [ "$(project --repo "$r" migrate plan | field '"review" in d["linked"]')" = True ] && project --repo "$r" migrate run --styleguide >/dev/null \
  && [ "$(project --repo "$r" show | field 'd["paths"]["review"]["path"].endswith("/.lem/review")')" = True ] && [ -L "$r/.revmux" ]; then
  pass "a path written with a trailing slash is the same folder, and it moves"
else
  fail "migrate with a trailing slash"
fi
# A rule file whose name reads as a pattern, beside an ignored file that the pattern would match.
r=$(small_repo pattern)
echo 'Brackets.' > "$r/.claude/rules/rule[ab].md" && mkdir -p "$r/.lem/styleguide" && echo local > "$r/.lem/styleguide/rulea.md"
echo '.lem/styleguide/rulea.md' > "$r/.gitignore" && git -C "$r" add -A && git -C "$r" commit -q -m "docs: a rule with brackets in its name"
project --repo "$r" migrate run --styleguide 'rule[ab].md' >/dev/null
if [ "$(git -C "$r" ls-files .lem/styleguide)" = ".lem/styleguide/rule[ab].md" ] && [ -L "$r/.claude/rules/rule[ab].md" ] && [ "$(cat "$r/.claude/rules/rule[ab].md")" = "Brackets." ] \
  && [ "$(cat "$r/.lem/styleguide/rulea.md")" = local ] && [ ! -L "$r/.claude/rules/a.md" ]; then
  pass "a rule file with brackets in its name moves as that one file, and an ignored file the name would match as a pattern is not staged"
else
  fail "migrate with a pattern-like file name: $(git -C "$r" ls-files .lem/styleguide)"
fi
# A step that fails after the first move: the git directory cannot be written, so nothing can be staged.
r=$(small_repo rollback)
mkdir "$r/.revmux/tasks" && echo session > "$r/.revmux/tasks/session" && echo '.revmux/tasks/' > "$r/.gitignore" && git -C "$r" add -A && git -C "$r" commit -q -m "chore: ignore the rounds"
settings_before=$(cat "$r/.lem/project.toml")
chmod u-w "$r/.git"
err=$(project --repo "$r" migrate run --styleguide a.md 2>&1 || true)
chmod u+w "$r/.git"
if grep -q "every file was put back" <<<"$err" && [ -z "$(git -C "$r" status --porcelain)" ] && [ "$(cat "$r/.revmux/tasks/session")" = session ] && [ ! -L "$r/.revmux" ] \
  && [ ! -L "$r/.claude/rules/a.md" ] && [ ! -e "$r/.lem/styleguide" ] && [ ! -e "$r/.lem/review" ] && [ "$(cat "$r/.lem/project.toml")" = "$settings_before" ]; then
  pass "a move that fails in the middle puts every file back, the ignored ones too, and leaves the settings as they were"
else
  fail "migrate rollback: $err / $(git -C "$r" status --porcelain) / $(ls -a "$r/.lem")"
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
  && [ "$named" = 'lemMeta({"repo": "old", "base": null, "session": ""});' ] \
  && [ "$(cat "$OLD/.git/lem/meta.js")" = 'lemMeta({"repo": "old", "base": "master", "session": ""});' ]; then
  pass "board --no-open writes the page into the shared state folder, from a worktree too, with the repository's name and its base"
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

# Two repositories' Lem sessions in one window each have a page named "Lem board": a board reloads
# its own and never closes the other's. agtermctl is a stand-in that prints a tree and records its calls.
FAKE=$WORK/fake
mkdir -p "$FAKE"
# shellcheck disable=SC2016  # the stand-in's own variables, expanded when it runs
printf '%s\n' '#!/bin/sh' 'echo "$*" >> "$AGT_CALLS"' 'case "$1" in tree) cat "$AGT_TREE" ;; *) echo "{\"result\": {\"id\": \"NEW\"}}" ;; esac' > "$FAKE/agtermctl"
chmod +x "$FAKE/agtermctl"
printf '%s\n' '{"result": {"tree": {"workspaces": [{"sessions": [' \
  '{"id": "AAA", "name": "lem a"}, {"id": "BBB", "name": "lem b"}, {"id": "CCC", "name": "lem c"},' \
  '{"id": "PA", "name": "Lem board", "content": "page", "parent": "AAA"},' \
  '{"id": "PB", "name": "Lem board", "content": "page", "parent": "BBB"}]}]}}}' > "$WORK/tree.json"
opened() { : > "$WORK/calls"; env PATH="$FAKE:$PATH" AGT_CALLS="$WORK/calls" AGT_TREE="$WORK/tree.json" AGTERM_SESSION_ID="$1" AGTERM_SOCKET=/none "$PY" -B "$BOARD" --repo "$OLD"; }
out=$(opened AAA)
if [ "$(field '(d["companion"], d["reloaded"])' <<<"$out")" = "('PA', True)" ] && grep -q "session overlay reload --target PA" "$WORK/calls" && ! grep -q "session close" "$WORK/calls"; then
  pass "a board that is already under this session is reloaded, and another session's board of the same name is left alone"
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
  elif why=$("$PY" -I -B -c "$SHOWN" "$WORK/board.dom" "Lem · old" "1 waits for you, 1 builds, 1 in the landing line" "Report dates stay whole" \
    "Owner lands it" "Land the branch, then tell Lem in its session that it landed." "!Demo data" "Keep report dates whole." \
    "Building: task 2 of 3" "Second task" "Ready to land: the gate was cut off" "1 of 4" "normal, due when the day allows" "tasks land on master"); then
    pass "the board draws each task in its lane from the events, with the review queue"
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
  if [ -s "$WORK/task-owner-lands-it.dom" ] && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-owner-lands-it.dom" "Owner lands it · Waits for you" "3/3" "Where you answer:" "!2/3"); then
    pass "a task that waits for the owner after a green gate keeps the phase and the plan tasks it reached"
  elif [ -s "$WORK/task-owner-lands-it.dom" ]; then
    fail "a task that waits after the gate: missing $why"
  fi
  # A closed task looked at much later: its time axis ends at its last block and has no line for now.
  mkdir -p "$WORK/aged" && cp "$OLD/.git/lem/task-with-a-worktree.html" "$OLD/.git/lem/meta.js" "$OLD/.git/lem/review-queue.js" "$WORK/aged/"
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
else
  printf 'SKIP the board pages: no Chrome or Chromium found\n'
fi
# The landing: land.py takes one task from `ready` to the base branch, one refusable step at a time.
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
mkdir "$SHOP/docs" && echo guide > "$SHOP/docs/guide.md" && echo one > "$SHOP/app.txt"
git -C "$SHOP" add -A && git -C "$SHOP" commit -q -m "chore: start" && git -C "$SHOP" push -q origin main
# open_task SLUG FILE TEXT: a task with a worktree, one commit that writes FILE, and the state `ready`
open_task() {
  local tree
  project --repo "$SHOP" task-dir "$1" >/dev/null
  tree=$(project --repo "$SHOP" worktree-dir "$1")
  git -C "$SHOP" worktree add -q "$tree" -b "fix/$1" main
  printf '%s\n' "$3" > "$tree/$2" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: $1"
  project --repo "$tree" state "$1" ready "the report is written" >/dev/null
}
status() { project --repo "$SHOP" tasks | field "next(t[\"status\"] for t in d if t[\"slug\"] == \"$1\")"; }
kept() { "$PY" -c 'import json, sys; print(json.load(open(sys.argv[1])).get(sys.argv[2]))' "$SHOP/.git/lem/tasks/$1/landing.json" "$2"; }

open_task first-change ok.txt yes
open_task second-change app.txt two
if [ "$(status_of land --repo "$SHOP" gate first-change)" = 1 ] && [ "$(status_of land --repo "$SHOP" base first-change)" = 1 ] && [ "$(status first-change)" = ready ]; then
  pass "base and gate refuse a task that did not take the landing line"
else
  fail "land steps before start"
fi
out=$(land --repo "$SHOP" start first-change)
err=$(land --repo "$SHOP" start second-change 2>&1 || true)
if [ "$(field 'd["remote"]' <<<"$out")" = True ] && [ "$(status first-change)" = landing ] && [ "$(status_of land --repo "$SHOP" start second-change)" = 1 ] \
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
err=$(land --repo "$SHOP" land first-change --risk normal 2>&1 || true)
if [ "$(status_of land --repo "$SHOP" land first-change --risk normal)" = 1 ] && grep -q "the owner lands" <<<"$err" \
  && [ "$(git -C "$ORIGIN" rev-parse main)" = "$(git -C "$SHOP" rev-parse main)" ]; then
  pass "land changes nothing when the settings say the owner lands"
else
  fail "land with branch.land = owner: $err"
fi
shop_settings agent keep
if [ "$(status_of land --repo "$SHOP" land first-change --risk normal --message "fix: x")" = 1 ]; then
  pass "a commit subject is refused when the branch's own commits land"
else
  fail "land --message with history = keep"
fi
# The base moves after the gate ran: by a file the gate reads, then only by one it does not.
other=$WORK/other
git clone -q "$ORIGIN" "$other" && ident "$other"
echo late > "$other/late.txt" && git -C "$other" add -A && git -C "$other" commit -q -m "feat: late" && git -C "$other" push -q origin main
err=$(land --repo "$SHOP" land first-change --risk normal 2>&1 || true)
if [ "$(status_of land --repo "$SHOP" land first-change --risk normal)" = 1 ] && grep -q "moved after the gate ran, by files the gate reads (late.txt)" <<<"$err" \
  && [ "$(status first-change)" = landing ]; then
  pass "land refuses when the base moved by a file the gate reads, and says to run base and gate again"
else
  fail "land after the base moved: $err"
fi
land --repo "$SHOP" base first-change >/dev/null
if [ "$(kept first-change gated)" = None ] && [ "$(status_of land --repo "$SHOP" land first-change --risk normal)" = 1 ]; then
  pass "a new base forgets the gate's result, so land waits for a new one"
else
  fail "base after a green gate keeps the result"
fi
land --repo "$SHOP" gate first-change >/dev/null
echo more >> "$other/docs/guide.md" && git -C "$other" add -A && git -C "$other" commit -q -m "docs: more" && git -C "$other" push -q origin main
out=$(land --repo "$SHOP" land first-change --risk high)
if [ "$(field '(d["pushed"], d["arrived"], d["review"], d["left_behind"])' <<<"$out")" = "(True, ['docs/guide.md'], 1, None)" ] && [ "$(status first-change)" = landed ] \
  && [ "$(git -C "$ORIGIN" log -1 --format=%s main)" = "fix: first-change" ] && [ "$(git -C "$SHOP" rev-parse main)" = "$(git -C "$ORIGIN" rev-parse main)" ] \
  && [ -f "$SHOP/ok.txt" ] && [ -f "$SHOP/late.txt" ] \
  && [ "$("$PY" -B "$QUEUE" --repo "$SHOP" list | field '[(i["slug"], i["risk"], i["range"]) for i in d]')" = "[('first-change', 'high', '$(field 'd["range"]' <<<"$out")')]" ]; then
  pass "a base that moved only by files the gate ignores still lands: pushed, the main checkout fast-forwarded, the review queued, the state landed"
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
land --repo "$SHOP" start second-change >/dev/null
out=$(land --repo "$SHOP" base second-change 2>/dev/null || true)
if [ "$(status_of land --repo "$SHOP" base second-change)" = 1 ] && [ "$(field '(d["conflict"], d["branch"])' <<<"$out")" = "(['app.txt'], 'fix/second-change')" ] \
  && [ -z "$(git -C "$SHOP/.lem/worktrees/second-change" status --porcelain)" ] && [ ! -d "$SHOP/.git/worktrees/second-change/rebase-merge" ]; then
  pass "a conflict with the base names its files and leaves the worktree as it was"
else
  fail "land base with a conflict: $out"
fi
# The builder resolves it; here the test does. Then a red gate, then one commit for the whole branch.
tree=$SHOP/.lem/worktrees/second-change
git -C "$tree" rebase -q origin/main >/dev/null 2>&1 || true
echo both > "$tree/app.txt" && git -C "$tree" add -A && GIT_EDITOR=true git -C "$tree" rebase --continue >/dev/null 2>&1
git -C "$tree" rm -q ok.txt && git -C "$tree" commit -q -m "fix: lose the file the gate wants"
land --repo "$SHOP" base second-change >/dev/null
out=$(land --repo "$SHOP" gate second-change 2>/dev/null || true)
if [ "$(status_of land --repo "$SHOP" gate second-change)" = 1 ] && [ "$(field '(d["green"], [c["exit"] for c in d["commands"]])' <<<"$out")" = "(False, [1, 0])" ] \
  && [ "$(kept second-change gated)" = None ] && [ "$(status_of land --repo "$SHOP" land second-change --risk normal)" = 1 ]; then
  pass "a red gate exits 1 with each command's result, and nothing lands on it"
else
  fail "red gate: $out"
fi
git -C "$tree" revert --no-edit HEAD >/dev/null
shop_settings agent squash
land --repo "$SHOP" gate second-change >/dev/null
if [ "$(status_of land --repo "$SHOP" land second-change --risk normal)" = 1 ]; then pass "one commit for the branch needs its subject"; else fail "squash without a message"; fi
before=$(git -C "$ORIGIN" rev-parse main)
# A commit hook that changes a tracked file makes the one commit another tree than the gate saw.
gated=$(git -C "$tree" rev-parse HEAD)
printf '%s\n' '#!/bin/sh' 'echo stamped >> app.txt && git add app.txt' > "$SHOP/.git/hooks/pre-commit"
chmod +x "$SHOP/.git/hooks/pre-commit"
err=$(land --repo "$SHOP" land second-change --risk normal --message "fix(app): both lines stay" 2>&1 || true)
rm "$SHOP/.git/hooks/pre-commit"
if grep -q "a commit hook changed the files" <<<"$err" && [ "$(git -C "$ORIGIN" rev-parse main)" = "$before" ] && [ "$(git -C "$tree" rev-parse HEAD)" = "$gated" ] \
  && [ -z "$(git -C "$tree" status --porcelain)" ] && [ "$(status second-change)" = landing ]; then
  pass "a commit hook that changes the one commit's files stops the landing, and the branch is put back as the gate saw it"
else
  fail "squash with a hook that changes the tree: $err"
fi
out=$(land --repo "$SHOP" land second-change --risk normal --message "fix(app): both lines stay")
if [ "$(git -C "$ORIGIN" rev-list --count "$before..main")" = 1 ] && [ "$(git -C "$ORIGIN" log -1 --format=%s main)" = "fix(app): both lines stay" ] \
  && [ "$(git -C "$ORIGIN" show main:app.txt)" = both ] && [ "$(git -C "$ORIGIN" rev-parse 'main^{tree}')" = "$(kept second-change tree)" ]; then
  pass "with history = squash the branch lands as one commit, and its tree is the tree the gate passed on"
else
  fail "squash landing: $out"
fi
land --repo "$SHOP" clean second-change >/dev/null

# A file that moves into an ignored folder also leaves a folder the gate reads.
shop_settings agent keep
open_task moved-file extra.txt four
land --repo "$SHOP" start moved-file >/dev/null && land --repo "$SHOP" base moved-file >/dev/null && land --repo "$SHOP" gate moved-file >/dev/null
git -C "$other" pull -q origin main && git -C "$other" mv late.txt docs/late.txt && git -C "$other" commit -q -m "docs: move late" && git -C "$other" push -q origin main
err=$(land --repo "$SHOP" land moved-file --risk normal 2>&1 || true)
if [ "$(status_of land --repo "$SHOP" land moved-file --risk normal)" = 1 ] && grep -q "files the gate reads (.*late.txt" <<<"$err" && [ "$(status moved-file)" = landing ]; then
  pass "a file moved into an ignored folder still counts as a change of the path it left"
else
  fail "a rename across gate.ignores: $err"
fi
land --repo "$SHOP" base moved-file >/dev/null && land --repo "$SHOP" gate moved-file >/dev/null
# The landing is cut off after the push: a copy of the scripts whose review queue fails stands in for
# the kill. The main checkout also has a commit of its own, so it cannot follow the remote.
BROKEN=$WORK/broken
cp -R "$PWD/skills/lem/scripts" "$BROKEN"
printf '%s\n' 'import sys' 'sys.exit("review_queue.py: cut off")' > "$BROKEN/review_queue.py"
git -C "$SHOP" commit -q --allow-empty -m "chore: only here"
before=$(git -C "$ORIGIN" rev-parse main)
if [ "$(status_of "$PY" -B "$BROKEN/land.py" --repo "$SHOP" land moved-file --risk normal)" = 1 ] && [ "$(git -C "$ORIGIN" rev-list --count "$before..main")" = 1 ] \
  && [ "$(status moved-file)" = landing ]; then
  pass "a landing cut off after the push leaves the commit on the base and the task in landing"
else
  fail "the cut-off landing did not reach the state the next check needs"
fi
landed_tip=$(git -C "$ORIGIN" rev-parse main)
# The item was queued and its review closed before the landing was run again: no second item.
reviewed=$("$PY" -B "$QUEUE" --repo "$SHOP" add moved-file --range "$("$PY" -c 'import json, sys; print(json.load(open(sys.argv[1]))["intent"]["range"])' "$SHOP/.git/lem/tasks/moved-file/landing.json")" --risk normal)
"$PY" -B "$QUEUE" --repo "$SHOP" close "$reviewed" --outcome clean
# Cut off again, one step later: the item is found and written down, the state is not. A copy of
# the scripts whose project.py refuses to write `landed` stands in for that kill.
LATE=$WORK/late
cp -R "$PWD/skills/lem/scripts" "$LATE"
printf '%s\n' 'import runpy, sys' 'if "landed" in sys.argv: sys.exit("project.py: cut off")' \
  "sys.argv[0] = '$PWD/skills/lem/scripts/project.py'" "runpy.run_path(sys.argv[0], run_name='__main__')" > "$LATE/project.py"
"$PY" -B "$LATE/land.py" --repo "$SHOP" land moved-file --risk normal >/dev/null 2>&1 || true
if [ "$(status moved-file)" = landing ] && [ "$(kept moved-file intent)" != None ] && [ "$(kept moved-file review)" = "$reviewed" ]; then
  pass "a landing cut off before its last state write keeps the record the next run needs"
else
  fail "a landing cut off before the landed state: status $(status moved-file), intent $(kept moved-file intent)"
fi
out=$(land --repo "$SHOP" land moved-file --risk normal)
if [ "$(status moved-file)" = landed ] && [ "$(git -C "$ORIGIN" rev-parse main)" = "$landed_tip" ] && [ "$(field 'd["tip"]' <<<"$out")" = "$landed_tip" ] \
  && [ "$(field 'd["review"]' <<<"$out")" = "$reviewed" ] && [ "$(kept moved-file intent)" = None ] \
  && [ "$("$PY" -B "$QUEUE" --repo "$SHOP" list --all | field '[i["slug"] for i in d].count("moved-file")')" = 1 ] \
  && [ "$(field '"did not follow origin/main" in d["left_behind"] and "brings it up" not in d["left_behind"]' <<<"$out")" = True ]; then
  pass "the next run finishes it: the review item that was already queued and closed is kept, the state is landed, nothing is pushed twice, and a main checkout that cannot follow is reported with git's own reason"
else
  fail "finishing a cut-off landing: $out"
fi
out=$(land --repo "$SHOP" land moved-file --risk normal 2>&1 || true)
if grep -q "is 'landed', not .landing." <<<"$out"; then pass "a landed task does not land again"; else fail "land twice: $out"; fi
git -C "$SHOP" reset -q --hard origin/main
out=$(land --repo "$SHOP" clean moved-file)
if [ "$(field '(d["worktree"], d["branch"])' <<<"$out")" = "(True, 'fix/moved-file')" ] && [ ! -e "$SHOP/.lem/worktrees/moved-file" ] && [ -z "$(git -C "$SHOP" branch --list fix/moved-file)" ]; then
  pass "clean removes a landed task's worktree and its branch in one run"
else
  fail "land clean: $out"
fi

# A landing cut off after the push, and then more work on the branch: what was pushed gets its
# review item, and the new tip lands only through its own base and gate.
shop_settings agent keep
open_task more-work m.txt five
land --repo "$SHOP" start more-work >/dev/null && land --repo "$SHOP" base more-work >/dev/null && land --repo "$SHOP" gate more-work >/dev/null
"$PY" -B "$BROKEN/land.py" --repo "$SHOP" land more-work --risk normal >/dev/null 2>&1 || true
git -C "$SHOP" merge -q --ff-only origin/main
tree=$SHOP/.lem/worktrees/more-work
echo six > "$tree/n.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: more-work, the second half"
err=$(land --repo "$SHOP" land more-work --risk normal 2>&1 || true)
if grep -q "run .land.py base. and .land.py gate. again" <<<"$err" && [ "$(status more-work)" = landing ] && ! git -C "$ORIGIN" cat-file -e main:n.txt 2>/dev/null \
  && [ "$("$PY" -B "$QUEUE" --repo "$SHOP" list --all | field '[i["slug"] for i in d].count("more-work")')" = 1 ]; then
  pass "after a cut-off landing and more work, the pushed range is queued for review and the new tip is refused until its own gate ran"
else
  fail "a stale landing record with more work: $err"
fi
land --repo "$SHOP" base more-work >/dev/null && land --repo "$SHOP" gate more-work >/dev/null
out=$(land --repo "$SHOP" land more-work --risk normal)
if [ "$(git -C "$ORIGIN" show main:n.txt)" = six ] && [ "$(status more-work)" = landed ] && [ "$(field 'd["tip"]' <<<"$out")" = "$(git -C "$ORIGIN" rev-parse main)" ] \
  && [ "$("$PY" -B "$QUEUE" --repo "$SHOP" list --all | field '[i["slug"] for i in d].count("more-work")')" = 2 ]; then
  pass "then the second half lands as its own range, with its own review item"
else
  fail "landing the work added after a cut-off landing: $out"
fi
land --repo "$SHOP" clean more-work >/dev/null

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
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[gate]' 'commands = ["true"]' > "$LOCAL/.lem/project.toml"
git -C "$LOCAL" add -A && git -C "$LOCAL" commit -q -m "chore: start"
project --repo "$LOCAL" task-dir local-change >/dev/null
tree=$(project --repo "$LOCAL" worktree-dir local-change)
git -C "$LOCAL" worktree add -q "$tree" -b fix/local-change main
echo x > "$tree/x.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: x"
project --repo "$tree" state local-change ready "the report is written" >/dev/null
land --repo "$LOCAL" start local-change >/dev/null && land --repo "$LOCAL" base local-change >/dev/null && land --repo "$LOCAL" gate local-change >/dev/null
out=$(land --repo "$LOCAL" land local-change --risk normal)
if [ "$(field 'd["pushed"]' <<<"$out")" = False ] && [ -f "$LOCAL/x.txt" ] && [ "$(git -C "$LOCAL" log -1 --format=%s main)" = "fix: x" ]; then
  pass "with no remote the base branch is fast-forwarded in the checkout that holds it"
else
  fail "local landing: $out"
fi

if [ -d "$(dirname "$PROJECT")/__pycache__" ]; then fail "the scripts left no __pycache__"; else pass "the scripts left no __pycache__"; fi

if [ "$fails" -gt 0 ]; then
  printf '\n%s check(s) failed\n' "$fails"
  exit 1
fi
printf '\nall checks passed\n'
