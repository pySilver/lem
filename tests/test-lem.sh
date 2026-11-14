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
  && [ "$(field 'd["seats"]["reviewer"]' <<<"$out")" = "codex" ]; then
  pass "init in a new project writes the skill's own layout, the given base and the reviewer seat"
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
settings '[seats]' 'reviewer = "gemini"'
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "a reviewer that is neither claude nor codex is refused"; else fail "reviewer value"; fi
settings '[seats]' 'reviewer = "claude"'
if [ "$(project --repo "$OLD" show | field 'd["seats"]["reviewer"]')" = "claude" ]; then pass "the reviewer seat may be the same family as the builder"; else fail "reviewer claude"; fi
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
other=$(project --repo "$OLD" task-dir written-by-hand)
printf '%s\n' '2026-01-02 build: task 2 of 3 running' > "$other/state.md"
out=$(project --repo "$OLD" tasks)
if [ "$(field '[(t["slug"], t["status"]) for t in d]' <<<"$out")" = "[('report-dates-stay-whole', 'building'), ('written-by-hand', None)]" ]; then
  pass "a state block that state did not write has no status"
else
  fail "hand-written state: $out"
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
out=$(land --repo "$SHOP" land moved-file --risk normal)
if [ "$(status moved-file)" = landed ] && [ "$(git -C "$ORIGIN" rev-parse main)" = "$landed_tip" ] && [ "$(field 'd["tip"]' <<<"$out")" = "$landed_tip" ] \
  && [ "$("$PY" -B "$QUEUE" --repo "$SHOP" list | field '[i["slug"] for i in d].count("moved-file")')" = 1 ] \
  && [ "$(field '"did not follow origin/main" in d["left_behind"] and "brings it up" not in d["left_behind"]' <<<"$out")" = True ]; then
  pass "the next run finishes it: one review item, the state landed, nothing pushed twice, and a main checkout that cannot follow is reported with git's own reason"
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
