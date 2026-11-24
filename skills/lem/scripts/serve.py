"""Serve Lem's boards over HTTP, for every repository on this machine that uses Lem,
from one server.

    lem serve --ensure                 make sure the server runs, from this code, and print it as JSON
    lem serve --stop                   end the server that runs
    lem serve --tailscale              open the tailnet door too, from now on; --tailscale-off closes it
    lem serve --port N                 serve port N, from now on; --tailscale-port N for the door
    lem serve [--host HOST] [--verbose]
                                       serve in the foreground until Ctrl-C or SIGTERM, for a developer
    lem serve --add DIR                put DIR's repository into the list, and exit
    lem serve --remove DIR             take DIR's repository out of the list, and exit
    lem serve --list                   print the list as the server reads it, and exit
    lem serve --push-test              send one push to every device that turned the board's notifications on,
                                       and print each push service's answer as JSON
    lem serve --join HOST[:PORT]       show the boards of the machine HOST of the tailnet here too, under /HOST/
    lem serve --leave HOST             show them no more; --peers lists the machines joined, and whether each answers

The server renders the board as pages (`lem_board_pages`, and the board of one task
`lem_board_task`, from the model of `lem_board_model`), for agterm on this Mac
(`lem board` opens it there as a page companion), a browser on this Mac, or another
device: a phone, a laptop. It runs where the repositories are, as one process for the
machine, and it is no part of a task.

Nothing supervises it. It starts on demand, as a process of its own with no terminal:
the plugin's SessionStart hook (`serve_hook.py`) runs `--ensure` when a Claude Code
session starts in a repository that uses Lem, `lem board` runs it before it opens a
board, and the owner runs it after a remote login. `--ensure` asks the main port who
serves it (`GET /api/server`: its pid, the version of its code, the folder it runs from,
its start); no answer means none runs, and it starts one, with its output in SERVE_LOG
in Lem's home folder (`lem_state.config()`), and waits at most START_WAIT for its
answer. A server of older code, or of other code as new, is asked to end
(`POST /api/server/stop`) and replaced (`outdated`: the newest change time of the
scripts decides), so that the first `lem` command after an update of the plugin loads
the new code, and a session that still runs the old plugin does not bring the old code
back. SERVE_LOCK spaces two starts at one moment. The environment variable LEM_SERVE=off
makes `--ensure` start nothing: a test suite sets it. A server writes its pid and its
port to `serve.pid` in Lem's home folder at its start and removes the file at a clean
stop (`write_pid`): `bin/lem` reads it, and asks the kernel whether that process lives,
to tell whether to start one.

The settings of the server are the machine's: `[serve]` in `machine.toml` (`lem_state`),
with `tailscale`, `port` and `tailscale_port`. `--tailscale`, `--tailscale-off`,
`--port` and `--tailscale-port` write them and then do what `--ensure` does, so that
each later start serves the way the owner last chose. The foreground server reads
them too.

The repositories are the machine's list of workspaces (`lem_state.workspaces_file()`):
`lem project task-dir`, `lem session open` and every run of `lem board` put their
repository there, and `--add` and `--remove` change it by hand. The server reads the
list at each request of `/` and of `/api/workspaces`, and leaves out an entry whose
folder or whose `.lem/state` is gone, without a change to the list. A workspace's name
in the address is its folder's name in lower case, with every other character than a
letter, a digit, `.`, `_` and `-` as `-`; two of one name are `NAME-2`, `NAME-3` in the
order of the list, gone entries included, so that a name does not move while a
repository is away.

The first part of every board's address is this machine's name (`HOST`), so that the
workspaces of a second machine can join under their own: the machine's name on the
tailnet, the first label of `Self.DNSName` in `tailscale status --json`, when Tailscale
is installed and connected, else its short host name; in lower case, with each character
that is not a letter, a digit or `-` as `-`. The server reads it once, at its start
(`machine_names`), and `/api/server` gives it. The other name of the two (`ALIASES`) is
redirected to the same page under `HOST`, so that an address with the plain host name
still opens. `api`, `assets`, `manifest.webmanifest` and the machine's names are the
server's own words, and so is `sw.js`, so a folder of such a name is `api-2`, and so on.

Other machines of the owner join this one's board (`lem_peers`): `--join HOST` writes
HOST into `[peers]` of the machine's file, and from the next look on, `/`,
`/api/workspaces` and the switcher list HOST's workspaces beside this machine's as
`HOST/WORKSPACE`, and every address under `/HOST/` is fetched from HOST's tailnet door
at the same address and passed back, its stream too. Only GET and HEAD pass. A request
that another machine's server forwarded (`Lem-Hop`) is never forwarded again and lists
no peer, so two machines that joined each other do not loop. A machine that does not
answer is listed as not reachable, with when it last answered, and never slows a page.

    GET /                      the workspaces, each with how many tasks wait for the owner and how many
                               tasks build and land; with one workspace, a redirect to its board
    GET /api/workspaces        the same as JSON, `[{"name", "path", "url", "waits", "building", "checks", "running", "host"}]`;
                               a workspace of a machine that does not answer has `"reachable": false`, `answered`, `said`
    GET /api/server            who this server is, as JSON, which `--ensure`, `lem board`, `lem doctor` and a
                               page whose stream is down read
    POST /api/server/stop      end the server: on the main listener only, from 127.0.0.1, and never from a
                               web page (a request with `Origin` or `Sec-Fetch-Site` is refused)
    GET /HOST/assets/NAME      the files the pages link (ASSETS): the looks, the kit's one script, the icons;
                               an address with `?v=` and the content's hash is kept a year; `/assets/NAME` too
    GET /manifest.webmanifest  the board as an app of a phone's home screen
    GET /sw.js                 the board's service worker, at the root so that its scope is the whole board: it
                               shows a notification when the server pushes (lem_push)
    GET /api/push/key          the machine's public key for the board's notifications, made at first use
    GET /api/push/latest       what the worker shows for the newest push
    POST /api/push/subscribe, /api/push/unsubscribe, /api/push/test
                               a device turns the board's notifications on or off, or asks for one push to itself:
                               through the door, and on the main listener from the board's own page on this Mac
    GET /HOST/NAME/            the kanban of that workspace; `waits`, `backlog` and `activity` beside it, and `done`,
                               the ended tasks the kanban's Done has no card for
    GET /HOST/NAME/tasks/SLUG  the board of one task over the kanban (`?in=waits`, `backlog`, `activity`, `done` over
                               that view), on its Overview; `/criteria`, `/checks`, `/timeline`,
                               `/artifacts` and `/artifacts/PATH/` (an artifact, each part encoded) beside it;
                               with the header `Turbo-Frame: task`, the panel alone in its frame
    GET /HOST/NAME/tasks/SLUG/raw/PATH
                               an HTML artifact of the task, the one file of a task folder sent as it is,
                               for the panel's sandboxed frame, under `Content-Security-Policy: sandbox`
    GET /HOST/NAME/tasks/SLUG/media/PATH
                               a picture of the task's `media/` folder, which a document shows: only a PNG,
                               JPEG, GIF or WebP whose first bytes are that format too (`image_type`); an SVG
                               is refused, since it can carry a script; nothing else of the task's folder
    GET /HOST/NAME/stream      server-sent events: Turbo's `refresh` each time the workspace changed;
                               `?task=SLUG` watches that task's files too
    POST /HOST/NAME/agterm/select
                               the jump to a task's session, which only agterm does, on the main listener only (below)
    GET /HOST/NAME/tasks/SLUG/merge, /park, /drop
                               the step of an act that asks first, as the task's panel: a merge's confirm step, a park,
                               a drop
    GET /HOST/NAME/tasks/SLUG/card/PAGEID
                               the step of a card of the task's session, as the task's panel, which frames the card's page
    GET /HOST/NAME/tasks/SLUG/cards/PAGEID/
                               the card's own page as `lem-ask` built it, under the card's policy (`card_page`)
    POST /HOST/NAME/tasks/SLUG/approve, /merge, /park, /session, /answer
                               the owner's acts on a task (below), on the main listener and through the door; a 303 to
                               the task's page, whose `?note=` says what came of the act
    POST /HOST/NAME/tasks/SLUG/cards/PAGEID/answer
                               the owner's answer to a card, which its page posts as JSON (`card_answer`), through the
                               same checks; the reply is JSON, `{"said": ...}`
    GET /HOST/NAME/new         the form of a new task in the owner's words ("+")
    POST /HOST/NAME/start      a new task, from that form (`words`) or from a backlog item (`item`, its path from the
                               root of the main checkout), through the same checks as an act on a task; a 303 to the
                               new task's page, or back to the form or the backlog when nothing started
    POST /HOST/NAME/backlog/drop
                               the owner's drop of a reviewer's item (`item`, its path), through the same checks; a 303
                               to the backlog with the note of the result
    GET /PEER/...              a page, a file or the stream of a machine joined, passed through from it
    GET /ALIAS/...             the same page under HOST
    GET /NAME/...              an address with no machine's name in it: a redirect to the same page under HOST

A page reads the workspace's model at its request (`Workspace.reader`, which reads a
file again only when it changed, and the settings and the backlog at most once in
REFRESH_SECONDS), and says on its status bar what did not read. A route that fails
answers with a page that says why. The board's own state that is the browser's (the
folded columns, the folded sidebar, the panel's width and whether it is expanded) comes
in the cookie PREFS_COOKIE.

The stream of the pages is HTTP/1.0 with no length, so it ends when the socket closes,
with one thread for each. Each message but the ping below is the default event, with no
`event:` line: `id:` is the version of the workspace's `events.jsonl`, its inode and its
number of lines in one id (`bm.log_version`), and `data:`
`<turbo-stream action="refresh">`, at which the page fetches itself again and morphs in
what changed; while the page posts a form, the refresh waits for the post's end (the
stream controller, `tools/board-kit/controllers/stream.js`). A message goes when the log
grew or `lem project prune` replaced it, or when a file the pages read beside it
changed: the owner's mark, the settings, the demo mark, the backlog's folder, the
reviewer's folder, and with `?task=SLUG` (a page with a task open) each file of that
task's folder, so that an artifact written with no event still shows. The thread looks
every WATCH_SECONDS, so a burst of events is one message, and ends when its client hung
up. A stream with nothing to say sends a `ping` event every PING_SECONDS: the page sees
it (Turbo renders only the default event, so not this one) and takes a stream silent for
longer than its limit as dead, and a client that vanished with no close shows as a
failed write. A page's open after a render (its load, or a visit to another task) names
the id its page shows (`?rendered=ID`) and gets a message at once only when that is not
the log's version now, so a page rendered before a prune replaced the log is told even
when the count is the same; an open after the page may have missed a change (`?since=ID`
from a page back on the screen or whose stream went down, or the browser's
`Last-Event-ID`) gets one at once whatever the log, since what it missed may be a change
that adds no line to it (`opens_with_refresh`). The server's stop ends every stream
within WATCH_SECONDS.

Each task lives in its own agterm session, and what reaches across tasks is the
server's: it holds no context, and it reads every duty from the files at each look, so a
pause of the server costs only time. A thread of its own (`forge_loop`, never on a
request's path) does, every FORGE_TICK, for each workspace, one call at a time with the
server's other calls into Lem's scripts (SCRIPT_LOCK):

- the look at the forge: while a workspace has a task `open` with a pull request and
  nobody looked at the forge in the last FORGE_SECONDS, it asks `gh` once for all of
  them (`land.py`'s `forge_look`), and for one the forge calls merged or closed it runs
  the bookkeeping, `lem land merged SLUG`, once for each such task, except one whose
  merge this server runs: that merge's step records the landing, and a merge that ends
  with none leaves the task to the next look. The record then says `landed` or
  `dropped`. What it saw of each pull request's merge with the base goes into
  `forge.json` of the state folder (`keep_forge_look`), which the board's model and
  `lem project waiting` read. `gh` missing or signed out is one line on the status bar
  until it changes;
- the look at the task sessions: `lem session list` (`Workspace.look_sessions`), which
  says of each task whether its session is in agterm, whether an agent runs in it,
  whether a wake-up waits in it unanswered, and its signs of work (`lem_signs`), for the
  board's row "no session" and its "Open a session", and for the guard of a stopped
  session below;
- the duties (`duties`, `run_duties`), each a command of `lem session` (SESSION_SCRIPT):
  after a merge, `wake SLUG --why merged`, so that the task's session removes its
  worktree and its branch; for a pull request the forge calls conflicting,
  `wake SLUG --why conflict`, once for each head; and for a task queued `after:` one
  that ended, `open SLUG --why queue`, or `wake SLUG --why queue` once when its session
  still lives. `wake` opens a session when none lives. The guard of a stopped session
  (`lem_board_model.stop_due`): for a task in `building`, `ready` or `landing` whose
  live session showed no sign of work for 45 minutes, `wake SLUG --why status`; 10
  minutes after it with still no sign, `open SLUG --why stopped`, a fresh session beside
  the old pane, once for one stop; and when that restart is spent, `stopped SLUG`, which
  logs the stop for the owner's row "stopped". A session whose signs do not read gets
  the status message after 45 minutes with no event of the task, and `stopped SLUG` 10
  minutes after it with still none, never a restart: the owner's "Open a session" opens
  the fresh one. Each looks once more in the task's lock and acts on nothing
  (`acted: false`) when the step is no longer due. A duty whose command failed
  waits DUTY_RETRY;
- the merge agent's merge (`merge_due`): for an open task whose merge agent's review of
  the tip Lem proposed last says `merge`, calls nobody and does not say `another round`
  of a moved base, with no refused merge of that tip that no read answered and none
  running, the server runs land.py's MERGE_STEP `--by merger --via server` as it runs
  the owner's merge from the board (`merge_in_thread`: in a thread of its own, as a
  process of its own outside SCRIPT_LOCK, and "Merging…" on the board while it runs).
  land.py's own rules decide whether it merges; the server only runs the call, since a
  task's session that ran it met a block of Claude Code's auto mode
  (pySilver/lem-scratch#12, 2026-11-21). A refusal is kept for its tip by land.py, which
  ends the duty for that tip, and the task's session gets `wake SLUG --why refused`
  once. Lem's refusal because the base moved is answered by the merge agent's read of
  what moved: a read that says `safe`, or a read on the checks' own base once main has
  their tree again (a revert), makes the merge due again at the server's next look, the
  owner's too when his was the merge refused (`merge.stands`, `stands_due`), since a
  failed merge waits DUTY_RETRY for its read alone (`duty_key`); one that says
  `another round` makes none, and the session lands the task again. After a merge,
  `wake … merged` above;
- the keeping of the state folder (`prune_once`): at its first look and each
  PRUNE_SECONDS after, it runs `lem project prune`, which removes what the workspace's
  state folder no longer needs, older than its settings' `state.keep_days`: every file
  of a task that ended but its small record, and old questions to the experts, panels,
  naps and copies of the cast. It reaches across tasks, so it is the server's and no
  task's: a task's own cleanup (`lem land clean`) runs once, at its merge, and a dropped
  or answered task has none. What it removed, skipped or failed is one line in the
  server's log.

A server started from a session leaves it at its start (`detach_from_session`):
`lem session` reads agterm's variables as its caller's place, and the server is no part
of any session.

The server never types into a session, never selects one without the owner's click,
never closes one, decides nothing, and writes a task's files only through
`lem land merged`, the merge agent's `lem land merge` and `lem session`, the end of a
card the owner answered on the board (`lem_cards.end`), and the record of his answer to
a row the board answers with its own buttons (`lem_answers.record`), and removes them
only through `lem project prune`. A workspace of example tasks has no forge to ask and
no duty, and one whose remote is not GitHub has no forge to ask.

Apart from that, the server reads. Its actions are its own stop, the board's
notifications, the owner's acts on a task, his answer to a card of a task's session, and
the jump to a task's session, which only agterm does and which agterm gives no page
served over http (an `--url` page has no bridge: measured in agterm 0.41.1 on
2026-11-20). A page drawn for the main listener and a client on this Mac (`Ctx.local`)
has its button, which posts to `agterm/select`. The server takes it only on the main
listener, from the loopback address, for its own `Host`, from its own origin and never
from another site (`action_refusal`), and then runs `agtermctl session select` for the
session of a task's newest `session.open`, and no other.

The owner's acts on a task (`board_act`) are forms of the board's pages, and each runs
the command a session runs on his word, in this process and one at a time with the
server's other calls into Lem's scripts (SCRIPT_LOCK): his yes to the criteria that wait
for it, `lem criteria approve SLUG --file criteria.md`, only for the text the page
showed (a digest of the file); the merge of an open task from its confirm step,
land.py's MERGE_STEP `--by owner`, only at the commit the step showed, which alone runs
as a process of its own (below); the park of a task a breaker holds,
`lem project state SLUG parked WHY`, with his line of why; and a fresh session of a task
none of whose sessions lives (`act_session`), `lem session open SLUG --why dead`, or
`--why owner` for a task that never had one, or `--why stopped` beside the live session
of a task whose stop the guard logged, which opens nothing when that session works
again; and a new task (`act_start`), from his words on the form of "+" or from a backlog
item's "Start a task": an item that a task that has not ended holds by its path is
refused with that task's name; its slug by a fixed rule (an item's file's stem, with the
first free `-2`, `-3` when a task of the stem ended; else the first SLUG_WORDS plain
words of his text, in lower case, joined by hyphens),
`lem project task-dir SLUG --ask ASK` (his words, or the item's path as the night gives
it), then `lem session open SLUG --why new` with no focus, whose agent reads the type
and the track itself; the drop of a reviewer's item from its "Drop" (`act_drop`),
`lem project proposals drop PATH`, one call that refuses while a task that has not ended
holds the item; and his answer to a row the board answers with its own buttons
(`act_answer`: a plan's Build or Drop, a breaker's Help, Park or Drop, Yes or No on
"Skip the persona read?" and on the criteria, "Approve this criterion?" on the fast
track and "Approve the criteria?" on the standard track, where a No with his note makes
the session change them and ask again), which records it as `answers/KEY.json` in the
task's folder (lem_answers) and wakes the task's session, which acts on it as on his
typed word; the record of a row's key comes first for every act of the board on that row
(a park, a yes to the criteria, a drop of the task), and a second act on it is refused
with what the record says. A task whose session opened and wrote no state yet is on the
board as starting (`lem_board_model.NEW`), so its acts and "Open a session" work. Each
act on a task the script took is logged as `board.act` with where he asked (`via`: the
board on this Mac, or through the tailnet door), never his login; a drop of a reviewer's
item is kept in the day's record of the proposals instead. A merge runs in a thread of
its own, since it reads the base branch and asks the forge, and as a process of its own
outside SCRIPT_LOCK (`merge_apart`), so that a slow forge holds no other act of the
board; the process takes the task's step lock and the repository's merge lock itself, so
two merges of one repository still take turns. The answer is at once, its page says that
it runs, and the stream refreshes the page at its end (`Workspace.acted`). The line of
each result is kept in memory for NOTE_SECONDS (`NOTES`), so a server that restarts
forgets it, and the files still say what happened. What only the task's session does
after an act stays the session's, and the page says so: after his yes and after a park
the server sends it `lem session wake SLUG --why owner` (`tell_session`), since it may
wait for him, and a task that needs a session and has none gets one; after a merge the
duty below wakes it for the cleanup.

A `lem-ask` card that a task's live session put up is a row of "Waits for you"
(lem_board_model `open_cards`), and its step in the task's panel frames the card's own
page, which the server sends from the task's folder as `lem-ask` built it (`card_page`,
`cards/PAGEID/`), under a policy that runs only the page's own scripts (`card_policy`).
The page posts the owner's answer to `cards/PAGEID/answer` (`card_answer`, `act_card`),
through the checks of an act. The board takes an answer with a note, never a
conversation: a wish to talk and a note with no option picked are refused, and so is an
answer to a card that ended, with what took effect. Before it takes one it reads
agterm's result for the card's page, `agtermctl session overlay result --page PAGEID`,
and refuses while agterm holds an answer from the Mac that no waiter read
(`agterm_card_refusal`). Then it links the card's end file with the answer, from the
board, with where he asked (`via`), the device the request names (`device_of`) and its
User-Agent, which logs `card.answered`, and logs `board.act act=answer`. The card's own
`lem-ask` in the session sees the end at its next poll, closes its own page and ends
with the answer, which wakes the session: the server sends it nothing.

It has no login of its own. It shows the tasks' files and the copied talk of a new task
to anyone who reaches its address, so it listens on 127.0.0.1 unless the foreground
server's `--host` names another address, and that address must be one that only the
owner's own devices reach. A tailnet's own address is no such address: every device of
the tailnet reaches it, a shared one too, over plain http and with no check of who asks.

The way from another device is the tailnet door, `serve.tailscale = true`. The server
opens a second listener on 127.0.0.1, the door, at `serve.tailscale_port` (TAILNET_PORT
by default), and puts `tailscale serve --bg --https=PORT http://127.0.0.1:PORT` in front
of it, so that the owner's phone opens `https://MAC.TAILNET.ts.net:PORT/` with the
tailnet's certificate. The main listener still serves this Mac with no login, and reads
a request only for a `Host` of its own (`host_refusal`: 127.0.0.1, localhost, [::1] or
the address of `--host`, with its port or without), so that a page of another site that
points its own name at this machine (DNS rebinding) reads nothing. The door checks every
request, a read too (`door_refusal`): Tailscale puts the login of the person who asks
into `Tailscale-User-Login`, and the door lets in only the owner's login, the one this
Mac is signed in with (`tailscale status --json`), never a request that came through
Funnel, and only the Mac's own name in `Host`; a method other than GET and HEAD also
only from the board's own origin. At the door every such method is answered 405 after
the check, except the three routes of the board's notifications, the owner's acts on a
task and his answer to a card, and the stop is no route of the door's.

The board's notifications (`lem_push`): a device turns them on from "Waits for you" or a
phone's drawer, and its subscription is kept in Lem's home folder. A thread of the
server (`lem_push.Watcher`) looks at each workspace's list of what waits for the owner
every few seconds, and when the list gains a row it sends one push with no payload to
each device; the worker then asks `/api/push/latest` what to say. Nothing is sent for a
demo workspace, and a failure is a line in the log and `push` in `/api/server`, never a
stop of the server.

The owner's Inbox (`lem_inbox`): while his mark says away, another thread of the server
(`lem_inbox.Watcher`) sends each row of the same lists to the Plannotator Inbox on this
Mac, in the task's own thread and as the task's Claude Code session, so that his reply
there comes back into that session; it withdraws a question whose row left the list, and
wakes the task's session with `lem session wake SLUG --why inbox` (`inbox_wake`). A
task's page links to its message through the Inbox's tailnet address (`inbox.json` of
the state folder). Nothing is sent for a demo workspace, and a failure is a line in the
log, never a stop of the server or of a task.

Before it publishes, the server reads `tailscale serve status --json`: a port that
another target holds is refused, never taken over, and an entry that already points at
the door is kept. The entry stays when the server stops, and Tailscale keeps it across a
restart of the Mac; `--tailscale-off` takes it out, only when it points at Lem's door.
Funnel is never used.
"""  # noqa: E501 - the usage table and the table of addresses of `--help` keep their columns

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not
    # a traceback
    sys.exit(
        "serve.py: Lem needs Python 3.11 or newer, and this python3 is "
        f"{sys.version.split()[0]}; put a newer one first on PATH, "
        "or run this file with it"
    )

import argparse
import base64
import contextlib
import email.header
import email.message
import errno
import fcntl
import gzip
import hashlib
import html.parser
import http.client
import http.cookies
import importlib
import json
import os
import re
import select
import shutil
import signal
import socket
import subprocess
import threading
import time
import types
import urllib.error
import urllib.request
from collections.abc import Callable, Generator
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import cast
from urllib.parse import parse_qs, quote, unquote, urlencode, urlsplit

SCRIPTS = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
board = importlib.import_module("board")
lem_state = importlib.import_module("lem_state")
lem_project = board.lem_project
bm = importlib.import_module("lem_board_model")
pages = importlib.import_module("lem_board_pages")
task_pages = importlib.import_module("lem_board_task")
lem_artifacts = importlib.import_module("lem_artifacts")
lem_push = importlib.import_module("lem_push")
lem_inbox = importlib.import_module("lem_inbox")
lem_peers = importlib.import_module("lem_peers")
lem_sibling = importlib.import_module("lem_sibling")
lem_release = importlib.import_module("lem_release")
lem_cards = importlib.import_module("lem_cards")
lem_answers = importlib.import_module("lem_answers")

# A port that no common tool takes by default (a pick, not a measurement).
PORT = 4536
# The first number past the highest TCP port, 65535.
PORT_LIMIT = 65536
HOST = "127.0.0.1"
# How often, at most, the server counts a workspace's tasks again for the list of
# workspaces, and reads the settings and the backlog again for a page. A guess: a phone
# does not need fresher counts than this, and the stream tells a page each change of the
# log at once.
REFRESH_SECONDS = 5


def host_word(name: str) -> str:
    """A machine's name as a word of an address: lower case, each character that is not
    a letter, a digit or `-` as `-`."""
    return re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")


# This machine's short host name, as a word of an address.
SHORT_NAME = host_word(socket.gethostname().split(".")[0]) or "this-mac"
# The first part of every board's address, and the machine's other name, which is
# redirected to it: `machine_names` sets both at the server's start; until then the
# short host name alone.
HOSTNAME = SHORT_NAME
ALIASES: tuple[str, ...] = ()
# How long the server's start waits for `tailscale status --json` to learn the machine's
# name on the tailnet. A guess: the CLI answers from the local daemon in well under a
# second, and `--ensure` waits START_WAIT for the whole start.
NAME_TIMEOUT = 3


def reserved() -> tuple[str, ...]:
    """The server's own first words of an address, which no workspace takes."""
    return ("api", "assets", "manifest.webmanifest", "sw.js", HOSTNAME, *ALIASES)


# The files of the plugin the pages link, by the name in their address (`/assets/NAME`).
ICONS = board.SCRIPTS.parent / "assets" / "icons"
ASSETS = {
    "lem.css": board.STYLE,
    "lem.js": board.PALETTE,
    "board.css": board.BOARD_STYLE,
    "board-app.js": board.VENDOR / "board-app.js",
    "mermaid.min.js": board.VENDOR / "mermaid.min.js",
    **{file.name: file for file in sorted(ICONS.glob("*.png"))},
}
# The look of the control of the board's notifications, and their service worker, which
# `/sw.js` sends from the root so that its scope is the whole board (lem_push).
ASSETS["push.css"] = board.SCRIPTS.parent / "assets" / "push.css"
SERVICE_WORKER = board.SCRIPTS.parent / "assets" / "sw.js"
# The routes of the board's notifications that take a POST, through the door
# too (`push_act`).
PUSH_ACTS = ("subscribe", "unsubscribe", "test")
# The assets sent compressed to a client that takes gzip, by their content's hash: the
# diagram library is 2.7 MB as it is and about a quarter of that compressed, which a
# phone feels.
PACKED: dict[tuple, bytes] = {}
# The views of a workspace the server renders, by the rest of their address.
PAGES = {
    "": "kanban_page",
    "waits": "waits_page",
    "backlog": "backlog_page",
    "activity": "activity_page",
    "done": "older_page",
    "new": "new_page",
}
# The one cookie of the board's own state (tools/board-kit/controllers/prefs.js).
PREFS_COOKIE = "lem_board"
# The panel's widths a dragged width may take, in px: a guess at what any screen and any
# panel holds.
PANEL_WIDTHS = (300, 4000)
# The user agent of the Hotwire Native apps (hotwire-native-ios and -android): their
# links are whole visits.
NATIVE = re.compile(r"\b(Turbo|Hotwire) Native\b")
# A task's name in an address, as project.py names its folder.
TASK_SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json",
    ".png": "image/png",
    ".webmanifest": "application/manifest+json",
}
# How long a request's connection may stay silent before the server drops it, so that a
# stop, which waits for the requests in flight, never waits for a client that sends
# nothing. A guess: a request of the board is answered in well under a second.
REQUEST_TIMEOUT = 30

# The tailnet door. Its HTTPS port on the tailnet, and its port on 127.0.0.1 behind it:
# one number for both. A pick, not a measurement: no common tool takes it by default,
# and it is none of the ports that the maintainer's Mac already serves on its tailnet
# (443, 8443, 8317, 50026; 2026-11-20).
TAILNET_PORT = 4537
# Where the tailscale CLI is, after the PATH: a process started with a short PATH has
# none of these (2026-11-20, on the standalone Tailscale 1.104.7 for macOS, whose
# /usr/local/bin/tailscale wraps the app's binary).
TAILSCALE_PLACES = (
    "/usr/local/bin/tailscale",
    "/Applications/Tailscale.app/Contents/MacOS/Tailscale",
    "/opt/homebrew/bin/tailscale",
)
# How long one call of the tailscale CLI may take before the server gives up on it.
# A guess.
TAILSCALE_TIMEOUT = 20
# How often, at most, a request whose login is not the owner's makes the door read the
# owner's login again from Tailscale (a login can change while the server runs). A
# guess: often enough to follow a change of account, rare enough that a peer of the
# tailnet cannot make the Mac run the CLI at will.
LOGIN_RECHECK_SECONDS = 30
# The refusal when the login is someone else's: the one refusal after which the door
# reads the owner's login again.
NOT_THE_OWNER = (
    "Only the owner's own Tailscale login opens this board, "
    "and this request carries another login."
)

# The folder of Lem this server runs from.
LEM_ROOT = SCRIPTS.parents[2]

# The start on demand: the server's output, in Lem's home folder, and the lock that
# spaces two starts.
SERVE_LOG = lem_state.SERVE_LOG
SERVE_LOCK = "serve.lock"
# Over this size the log is emptied when a server starts, so that it cannot grow without
# end. A guess: a server writes a line at its start and at a failure, and a megabyte
# holds thousands of them.
LOG_CAP = 1_000_000
# How long `--ensure` waits for a server it started to answer. A guess: the server
# answers in well under a second, and the door's three calls of the tailscale CLI take a
# few seconds at most.
START_WAIT = 10
# How long `--ensure` and `--stop` wait for a server they asked to end to free its port.
# A guess: a stop waits for the requests in flight, and a stream ends
# within WATCH_SECONDS.
STOP_WAIT = 10
# How long one question to the server on the main port (`GET /api/server`) may take. A
# guess: it is answered from memory.
ASK_TIMEOUT = 2
# The environment variable that keeps `--ensure` from a start, and its one value.
NO_START = ("LEM_SERVE", "off")

# The stream. How often its thread looks at the workspace's files with `stat`: a guess,
# short enough that a new event reaches a phone in about a second, and a `stat` of a few
# files costs nothing.
WATCH_SECONDS = 0.5
# How often a stream with nothing to say sends a ping event: often enough that a page
# hears one well within its silence limit (SILENCE_MS of the board's stream.js, 25 s, so
# that it says "reconnecting" within 30 s of a stop), that a client that went away is
# found and its thread ends, and that no proxy on the way takes the stream for idle. 10
# s is an unmeasured estimate (the plan of 2026-11-22), under the 15 s that is the usual
# pick for server-sent events (the research of 2026-11-20 for the board).
PING_SECONDS = 10
EVENT_LOG = "events.jsonl"

# Who this server is, which `GET /api/server` answers; `listen` fills it.
RUNNING: dict = {}
# Set when the server stops: every stream's thread ends at its next look.
STOPPING = threading.Event()


class ServeError(Exception):
    pass


def name_of(folder: str) -> str:
    """A folder's name as a word of an address."""
    return re.sub(r"[^a-z0-9._-]+", "-", folder.lower()).strip("-.") or "workspace"


def named(paths: list[str]) -> list[tuple[str, str]]:
    """Each path of the list with its name, in the order of the list."""
    taken = set(reserved())
    out = []
    for path in paths:
        base = name_of(Path(path).name)
        name, n = base, 2
        while name in taken:
            name, n = f"{base}-{n}", n + 1
        taken.add(name)
        out.append((name, path))
    return out


def live(path: str) -> bool:
    return (Path(path) / lem_state.STATE).is_dir()


class Workspace:
    """One repository the server shows: its state folder, and when its files and counts
    were last made."""

    def __init__(self, name: str, path: str) -> None:
        self.name = name
        self.path = path
        self.state = Path(path) / lem_state.STATE
        self.counted = 0.0
        self.counts: dict = {}
        # the facts of the board's pages, read again where a file changed
        # (lem_board_model.Reader)
        self.reader = bm.Reader(Path(path), self.state, REFRESH_SECONDS)
        # "What we are building" of each task, which asks git, at most once
        # in REFRESH_SECONDS
        self.told: dict[str, tuple[float, dict]] = {}
        self.onto: tuple[float, str] | None = None
        # the server's own look at the forge (forge_loop): when it looked (ms), what
        # stopped it, and the pull requests whose bookkeeping it ran, so that each
        # runs once
        self.forge: dict = {"looked": None, "problem": None, "done": set()}
        # how many acts of the board ended here: a stream sends a refresh at each, also
        # for one that wrote no file
        self.acted = 0
        # what the server's last `lem session list` said of each task's session
        # (lem_board_model.Model.sessions), or None while it has not asked or the answer
        # did not read, and why not; the tasks that ended and whose worktree is still
        # there; and each duty whose command failed, with when (`run_duties`)
        self.sessions: dict | None = None
        self.session_problem: str | None = None
        self.kept: set[str] = set()
        self.needs: dict[str, str] = {}
        # the held tasks whose session works on the owner's answer at the last
        # look (`lem_board_model.put_sessions`)
        self.works: set[str] = set()
        self.failed: dict[tuple, float] = {}
        # when the server last ran `lem project prune` here (`prune_once`), on the
        # monotonic clock
        self.pruned: float | None = None

    def model(self) -> "bm.Model":
        found = self.reader.current(board)
        bm.put_sessions(found, self.sessions)
        # the server's own look, once it looked; before it, the last look on file
        # (bm.FORGE_LOOK), which the Reader read
        if self.forge.get("seen") is not None:
            found.seen = self.forge["seen"]
        return found

    def worktree_of(self, slug: str) -> Path | None:
        """Where the task's worktree is, as the settings place it, or None when the
        settings do not read."""
        settings = self.settings()
        if settings is None:
            return None
        try:
            root = Path(settings["root"])
            return (
                Path(settings["main"])
                / Path(settings["places"]["worktrees"]["path"]).relative_to(root)
                / slug
            )
        except (KeyError, TypeError, ValueError):
            return None

    def look_sessions(self) -> None:
        """Ask `lem session list` which task sessions live, for the board's rows and its
        "Open a session" (`Model.sessions`), with the worktree of each task that ended
        and still has one. Nothing for a demo workspace, which has no agterm of its own
        to ask. A page open on the workspace gets a refresh when a task becomes stuck
        for want of its session, or stops being so, and when a held task's session
        starts or ends a turn on the owner's answer (`lem_board_model.put_sessions`)."""
        model = self.reader.current(board)
        if model.meta.get("demo") or not self.settings():
            self.sessions = None
            return
        kept = set()
        for t in model.tasks:
            tree = self.worktree_of(t.slug) if t.closed else None
            if tree is not None and tree.is_dir():
                kept.add(t.slug)
        self.kept = kept
        ran = session_run(self, "list")
        try:
            if ran.returncode != 0:
                raise ValueError(said_of(ran))
            entries = session_entries(ran.stdout)
        except ValueError as error:
            self.sessions, self.session_problem = (
                None,
                (
                    "the board cannot tell which task sessions run: "
                    f"`lem session list` said {error}"
                ),
            )
            return
        self.sessions = bm.sessions_of(entries, kept)
        self.session_problem = None
        bm.put_sessions(model, self.sessions)
        needs = {
            t.slug: need for t in model.tasks if (need := bm.session_need(t, model))
        }
        works = {t.slug for t in model.tasks if t.works}
        if needs != self.needs or works != self.works:
            self.needs, self.works = needs, works
            self.acted += 1

    def backlog_folder(self) -> Path | None:
        """The backlog's folder of the main checkout, as board.backlog reads it, or None
        when the settings do not read."""
        settings = self.settings()
        if not settings:
            return None
        try:
            return Path(settings["main"]) / Path(
                settings["places"]["backlog"]["path"]
            ).relative_to(settings["root"])
        except (KeyError, ValueError):
            return None

    def settings(self) -> dict | None:
        self.reader.read_settings(board)
        return self.reader.settings

    def plan_of(self, slug: str) -> tuple[Path, str] | None:
        """The task's plan in its worktree, as the artifacts list it, or None."""
        settings = self.settings()
        if not settings:
            return None
        try:
            return lem_project.task_plan(Path(self.path), settings, slug)
        except (OSError, KeyError, ValueError, lem_project.SettingsError):
            return None

    def how_of(self, slug: str) -> str:
        """The plan's `## How it works` as criteria.py reads it (`parse`, its `how`):
        from the task's plan in its worktree, else from the approved criteria's record;
        "" when neither has one."""
        criteria = lem_sibling.module(SCRIPTS / "criteria.py")
        plan = self.plan_of(slug)
        try:
            if plan:
                return (
                    criteria.parse(
                        plan[0].read_text(encoding="utf-8", errors="replace"), plan[1]
                    ).get("how")
                    or ""
                )
        except (OSError, criteria.CriteriaError):
            pass
        try:
            record = json.loads(
                (self.state / "tasks" / slug / "criteria.json").read_text(
                    encoding="utf-8"
                )
            )
            return str(record.get("how") or "") if isinstance(record, dict) else ""
        except (OSError, ValueError):
            return ""

    def told_of(self, slug: str) -> dict | None:
        """What "What we are building" says of a task (lem_board_task.told_of), at most
        once in REFRESH_SECONDS."""
        known = self.told.get(slug)
        if known and time.monotonic() - known[0] < REFRESH_SECONDS:
            return known[1]
        settings = self.settings()
        worktree = backlog = None
        onto = ""
        if settings:
            try:
                main, root = Path(settings["main"]), Path(settings["root"])
                worktree = (
                    main
                    / Path(settings["places"]["worktrees"]["path"]).relative_to(root)
                    / slug
                )
                backlog = (
                    Path(settings["places"]["backlog"]["path"])
                    .relative_to(root)
                    .as_posix()
                )
                onto = self.onto_of(main, settings["branch"]["base"] or "")
            except (KeyError, ValueError):
                worktree = backlog = None
        told = task_pages.told_of(self.state, board, slug, worktree, onto, backlog)
        self.told[slug] = (time.monotonic(), told)
        return told

    def onto_of(self, main: Path, base: str) -> str:
        """The ref a landing compares a branch with (land.py `onto`): `origin/BASE`
        where origin is, else BASE."""
        if not base:
            return ""
        if self.onto is None or time.monotonic() - self.onto[0] >= REFRESH_SECONDS:
            remote = (
                subprocess.run(
                    ["git", "-C", str(main), "remote", "get-url", "origin"],
                    capture_output=True,
                    text=True,
                    check=False,
                ).returncode
                == 0
            )
            self.onto = (time.monotonic(), f"origin/{base}" if remote else base)
        return self.onto[1]

    def criteria_waiting(self, slug: str) -> dict | None:
        """The criteria of the task directory that wait for the owner's yes,
        `criteria.md`, as the task's session writes them: its path, its text and a
        digest of its bytes, which the approval's form carries back, so that a yes never
        takes criteria the page did not show: `lem criteria approve --shown` compares it
        with the bytes it approves, in the same form (criteria.py's `shown_digest`).
        With them `before` and `words`, the text the newest change from the owner's note
        kept and his note (`criteria-before.json`, `lem criteria change`), or None: the
        card shows it beside the new text while that change's wait stands
        (`bm.change_of`). None when criteria.md is not there."""
        folder = self.state / "tasks" / slug
        try:
            data = (folder / "criteria.md").read_bytes()
        except OSError:
            return None
        try:
            kept = json.loads((folder / bm.CRITERIA_BEFORE).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            kept = None
        kept = (
            kept if isinstance(kept, dict) and isinstance(kept.get("text"), str) else {}
        )
        return {
            "path": str(folder / "criteria.md"),
            "text": data.decode("utf-8", errors="replace"),
            "digest": hashlib.sha256(data).hexdigest()[:16],
            "before": kept.get("text"),
            "words": kept.get("words") if isinstance(kept.get("words"), str) else None,
        }

    def card_end(self, slug: str, page: str) -> dict | None:
        """The end on record of the card PAGE of the task (`lem_cards.ended`), or None
        while it is open or does not read."""
        try:
            return lem_cards.ended(self.state / "tasks" / slug, page)
        except (lem_cards.CardError, OSError):
            return None

    def landing_of(self, slug: str) -> dict:
        """The task's landing record (land.py's `landing.json`: the tip it proposed, its
        pull request and title), with the base branch and `branch.history` of the
        settings; {} when it does not read."""
        try:
            record = json.loads(
                (self.state / "tasks" / slug / "landing.json").read_text(
                    encoding="utf-8"
                )
            )
        except (OSError, ValueError):
            return {}
        if not isinstance(record, dict):
            return {}
        branch = (self.settings() or {}).get("branch") or {}
        return {**record, "base": branch.get("base"), "history": branch.get("history")}

    def count(self) -> dict:
        """How many tasks wait for the owner (the entries of the board's "Waits for
        you", its rows grouped by task, `wait_stacks`), how many tasks build and how
        many are in their checks and review (`landing`), and the two together
        (`running`), from the board's model, at most once in REFRESH_SECONDS."""
        if time.monotonic() - self.counted < REFRESH_SECONDS:
            return self.counts
        try:
            model = self.model()
        except Exception as error:  # noqa: BLE001 - a workspace that cannot be read says why, and the others still show
            self.counts = {
                "waits": None,
                "building": None,
                "checks": None,
                "running": None,
                "problem": str(error),
            }
        else:
            building = sum(t.status == "building" for t in model.tasks)
            checks = sum(t.status == "landing" for t in model.tasks)
            self.counts = {
                "waits": len(bm.wait_stacks(bm.waits_of(model))),
                "building": building,
                "checks": checks,
                "running": building + checks,
            }
            if self.reader.problems:
                self.counts["problem"] = "; ".join(self.reader.problems.values())
        self.counted = time.monotonic()
        return self.counts


class Machine:
    """The workspaces of the list, each made once and kept while the list names it."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.known: dict[str, Workspace] = {}

    def workspaces(self) -> list[Workspace]:
        """The live workspaces of the list as it is now, in its order."""
        listed = named(lem_state.workspaces())
        with self.lock:
            kept = {}
            for name, path in listed:
                old = self.known.get(name)
                kept[name] = (
                    old
                    if old is not None and old.path == path
                    else Workspace(name, path)
                )
            self.known = kept
        return [kept[name] for name, path in listed if live(path)]

    def one(self, name: str) -> Workspace | None:
        with self.lock:
            found = self.known.get(name)
        if found is None:
            found = next((w for w in self.workspaces() if w.name == name), None)
        return found if found is not None and live(found.path) else None

    def listing(self) -> list[dict]:
        return [
            {
                "name": w.name,
                "path": w.path,
                "url": f"/{quote(HOSTNAME)}/{quote(w.name)}/",
                **w.count(),
            }
            for w in self.workspaces()
        ]


# The content hash of each asset, by its path and its change time, so that an address
# changes with the file.
DIGESTS: dict[tuple, str] = {}


def asset_link(name: str) -> str:
    """The address of one of the plugin's files the pages link, under the machine's
    name, with `?v=` and a hash of its content: a page of another machine that this
    server passes through gets that machine's own files, of its own
    version (`lem_peers`)."""
    file = ASSETS[name]
    try:
        key = (file, file.stat().st_mtime_ns)
    except OSError:
        return f"/{HOSTNAME}/assets/{name}"
    if key not in DIGESTS:
        DIGESTS[key] = hashlib.sha256(file.read_bytes()).hexdigest()[:12]
    return f"/{HOSTNAME}/assets/{name}?v={DIGESTS[key]}"


def keep_days_of(reader: "bm.Reader") -> int | None:
    """The workspace's `state.keep_days` as its settings give it now
    (`lem_project.load`, this machine's own number too), for the page of a task whose
    files prune removed; None while the settings do not read, which the page shows among
    its problems, never a number of an older read."""
    if "settings" in reader.problems or not isinstance(reader.settings, dict):
        return None
    days = (reader.settings.get("state") or {}).get("keep_days")
    return days if isinstance(days, int) and not isinstance(days, bool) else None


def prefs_of(header: str | None) -> dict:
    """The board's own state from its cookie: the folded columns, the folded sidebar,
    the panel's width and whether it is expanded, and whether a task's header shows its
    details on a phone (`head`); none when it does not read."""
    if not header:
        return {}
    try:
        jar = http.cookies.SimpleCookie(header)
    except http.cookies.CookieError:
        return {}
    morsel = jar.get(PREFS_COOKIE)
    try:
        value = json.loads(unquote(morsel.value)) if morsel else {}
    except ValueError:
        return {}
    if not isinstance(value, dict):
        return {}
    folded = (
        [
            key
            for key in value.get("folded") or []
            if isinstance(key, str) and key in bm.LANE
        ]
        if isinstance(value.get("folded"), list)
        else []
    )
    width = value.get("pw")
    width = (
        width
        if isinstance(width, int)
        and not isinstance(width, bool)
        and PANEL_WIDTHS[0] <= width <= PANEL_WIDTHS[1]
        else None
    )
    return {
        "folded": folded,
        "rail": value.get("rail") is True,
        "pw": width,
        "full": value.get("full") is True,
        "head": value.get("head") is True,
    }


def decoded(value: str) -> str:
    """A header's value with its RFC 2047 encoded words decoded (`=?utf-8?q?...?=`),
    which Tailscale uses for a login that is not plain ASCII; the value as it came when
    it does not decode."""
    try:
        return str(email.header.make_header(email.header.decode_header(value)))
    except (ValueError, LookupError):
        return value


def door_refusal(  # noqa: PLR0911 - over the limit before the limit was set
    headers: email.message.Message, method: str, owner: str, served: str, port: int
) -> str | None:
    """Whether the door lets a request in: None when it does, else the one line its
    403 says.

    `headers` is any mapping or message whose `items()` gives each header once for each
    time it came; `owner` the owner's Tailscale login, `served` the Mac's name on the
    tailnet and `port` the door's HTTPS port there. A request through Funnel, one for
    another host name, one with no login or with two, and one with a login that is not
    the owner's are refused. A method other than GET and HEAD must also come from the
    board's own page: a `Sec-Fetch-Site` that is not same-origin and an `Origin` that is
    not the board's are refused."""
    seen: dict[str, list[str]] = {}
    for key, value in headers.items():
        seen.setdefault(key.lower(), []).append(value)
    if "tailscale-funnel-request" in seen:
        return "This board is not served through Tailscale Funnel."
    host = [value.strip().lower() for value in seen.get("host", [])]
    if len(host) != 1 or host[0] not in (served.lower(), f"{served.lower()}:{port}"):
        return "This address is not the board's name on the tailnet."
    logins = seen.get("tailscale-user-login", [])
    if not logins:
        return (
            "Only the owner's own Tailscale login opens this board, "
            "and this request carries none."
        )
    if (
        len(logins) > 1
        or decoded(logins[0]).strip().casefold() != owner.strip().casefold()
    ):
        return NOT_THE_OWNER
    if method.upper() not in ("GET", "HEAD"):
        fetch = [value.strip().lower() for value in seen.get("sec-fetch-site", [])]
        if any(value not in ("same-origin", "none") for value in fetch):
            return (
                "A change comes only from the board's own page, "
                "and this request comes from another site."
            )
        origins = {f"https://{served.lower()}:{port}"} | (
            {f"https://{served.lower()}"} if port == http.client.HTTPS_PORT else set()
        )
        if any(
            value.strip().lower() not in origins for value in seen.get("origin", [])
        ):
            return (
                "A change comes only from the board's own page, "
                "and this request names another origin."
            )
    return None


class Door:
    """The facts the door checks a request against: the CLI, the Mac's name on the
    tailnet, the door's port, and the owner's login, which it reads again when a login
    does not match."""

    def __init__(self, cli: str, name: str, port: int, owner: str) -> None:
        self.cli = cli
        self.name = name
        self.port = port
        self.owner = owner
        self.lock = threading.Lock()
        self.read_at = time.monotonic()

    def url(self) -> str:
        return (
            f"https://{self.name}:{self.port}/"
            if self.port != http.client.HTTPS_PORT
            else f"https://{self.name}/"
        )

    def reread(self) -> bool:
        """Read the owner's login again, at most once in LOGIN_RECHECK_SECONDS; True
        when it changed."""
        with self.lock:
            if time.monotonic() - self.read_at < LOGIN_RECHECK_SECONDS:
                return False
            self.read_at = time.monotonic()
            try:
                facts = tailnet(self.cli)
            except ServeError as error:
                sys.stderr.write(
                    f"serve.py: the owner's login was not read again: {error}\n"
                )
                return False
            changed = facts["login"] != self.owner
            self.owner = facts["login"]
            return changed


# The client addresses of a program or a page on this machine.
LOOPBACK = ("127.0.0.1", "::1", "::ffff:127.0.0.1")


def own_names(port: int, host: str = HOST) -> set[str]:
    """The `Host` values of the main listener's own: 127.0.0.1, localhost and [::1], and
    the address of the foreground server's `--host`, each with its port and without it,
    in lower case."""
    names = {"127.0.0.1", "localhost", "[::1]"}
    if host:
        names.add(f"[{host.lower()}]" if ":" in host else host.lower())
    return names | {f"{name}:{port}" for name in names}


def host_refusal(
    headers: email.message.Message, port: int, host: str = HOST
) -> str | None:
    """Whether the main listener reads a request: None when its one `Host` is a name of
    its own (`own_names`), else the line its 403 says. A page of another site whose name
    the site points at this machine (DNS rebinding) carries that site's name, so the
    board's files never reach that site's script."""
    seen = [
        value.strip().lower() for key, value in headers.items() if key.lower() == "host"
    ]
    if len(seen) != 1 or seen[0] not in own_names(port, host):
        return (
            "This address is not the board's own on this Mac: "
            "open it as http://127.0.0.1:PORT/."
        )
    return None


def stop_refusal(client: str, headers: email.message.Message) -> str | None:
    """Whether the main listener takes a request to stop the server: None when it does,
    else the line its 403 says. Only a program on this machine stops it: the request
    comes from the loopback address, and it carries no `Origin` and no `Sec-Fetch-Site`,
    one of which a browser adds to each request of a web page, so that no page can stop
    the server."""
    if client not in LOOPBACK:
        return (
            "Only a program on this machine stops the server: `lem serve --stop` there."
        )
    names = {key.lower() for key, _ in headers.items()}
    if "origin" in names or "sec-fetch-site" in names:
        return (
            "A web page does not stop the server: `lem serve --stop` on this machine "
            "does."
        )
    return None


def action_refusal(
    client: str, headers: email.message.Message, port: int
) -> str | None:
    """Whether the main listener takes an act of a page (one of agterm, the board's
    notifications, an act on a task): None when it does, else the line its 403 says.
    Only a page of this board on this machine asks it: the request comes from the
    loopback address, its `Host` is the main listener's own (a page of another site that
    a name of its own points at this machine carries that name), its `Origin` is the
    board's own origin, and a `Sec-Fetch-Site` it carries says same-origin."""
    if client not in LOOPBACK:
        return "Only a page on this Mac acts through the board's main address."
    seen: dict[str, list[str]] = {}
    for key, value in headers.items():
        seen.setdefault(key.lower(), []).append(value.strip().lower())
    own = {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}
    host = seen.get("host", [])
    if len(host) != 1 or host[0] not in own:
        return "This address is not the board's own on this Mac."
    origin = seen.get("origin", [])
    if len(origin) != 1 or origin[0] not in {f"http://{each}" for each in own}:
        return (
            "An act comes only from the board's own page, and this request names "
            "another origin or none."
        )
    if any(value != "same-origin" for value in seen.get("sec-fetch-site", [])):
        return (
            "An act comes only from the board's own page, "
            "and this request comes from another site."
        )
    return None


# The one act of agterm a page asks for (`agterm_act`): the jump to a task's session.
AGTERM_ACTS = ("select",)
# A session's id as agterm gives it.
SESSION_ID = re.compile(r"[A-Za-z0-9-]{1,64}")
# Where agtermctl is when the PATH of the server has none: the app's own binary.
AGTERMCTL_PLACES = (
    "/Applications/agterm.app/Contents/MacOS/agtermctl",
    "/opt/homebrew/bin/agtermctl",
    "/usr/local/bin/agtermctl",
)
# How long one call of agtermctl may take. A guess: agterm answers its socket at once.
AGTERM_TIMEOUT = 10
# The largest JSON body of an act of agterm that the server reads, in bytes.
AGTERM_BYTES = 4096


class AgtermRefused(Exception):
    pass


def agtermctl() -> str | None:
    """agtermctl on the server's PATH, else the app's own binary, else None."""
    return shutil.which("agtermctl") or next(
        (place for place in AGTERMCTL_PLACES if os.access(place, os.X_OK)), None
    )


def agterm_act(workspace: "Workspace", act: str, asked: dict) -> str:
    """The jump to a task's session for a page of the workspace, on the owner's click,
    and what was done; AgtermRefused says why not. Only the session of a task's newest
    `session.open` is taken, and agtermctl finds agterm's socket itself (measured with
    no `--socket`, plan-task-4.md's trial, 2026-11-21)."""
    ctl = agtermctl()
    if ctl is None:
        raise AgtermRefused(
            "agtermctl is not on this Mac: install agterm's command line tool (Help > "
            "Install Command Line Tool)."
        )
    session = asked.get("session")
    named = {t.session.upper() for t in workspace.model().tasks if t.session}
    if (
        not isinstance(session, str)
        or not SESSION_ID.fullmatch(session)
        or session.upper() not in named
    ):
        raise AgtermRefused("That is no session of this workspace's tasks.")
    try:
        ran = subprocess.run(
            [ctl, "session", "select", "--target", session],
            capture_output=True,
            text=True,
            check=False,
            timeout=AGTERM_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise AgtermRefused(f"agtermctl session did not answer ({error}).") from error
    if ran.returncode != 0:
        raise AgtermRefused(
            "agtermctl session select failed: "
            f"{(ran.stderr or ran.stdout).strip() or f'exit {ran.returncode}'}."
        )
    return "Switched to the session."


# ---- the board's acts: the owner's word from a page ----

# The acts a page posts to `/HOST/NAME/tasks/SLUG/ACT`, each the command a session runs
# on his word, or, for `answer`, the record of his answer to a row, which the task's
# session acts on (`act_answer`).
BOARD_ACTS = ("approve", "merge", "park", "session", "answer")
# land.py's step that merges an open pull request on the owner's word:
# `lem land merge SLUG --by owner`.
MERGE_STEP = "merge"
# How long the line of an act's result stays for the page whose address names it
# (`?note=TOKEN`). A guess: long enough for a second look on the phone, short enough
# that the server keeps few lines.
NOTE_SECONDS = 3600
# The largest form an act takes, in bytes: a few short fields and a reason of one line.
FORM_BYTES = 4096
# The longest reason of a park the board takes, in characters: one line (a guess).
WHY_CHARS = 300


class Notes:
    """The line of each act's result, by a token that the address of the page after it
    carries, so that a refresh of that page, and every morph of it, still says what came
    of the act. A merge that runs (`merging`) holds its token until its end, so that a
    second press finds the first."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.kept: dict[str, dict] = {}
        self.merging: dict[tuple[str, str], str] = {}

    def put(self, **note: object) -> str:
        token = os.urandom(6).hex()
        with self.lock:
            now = time.monotonic()
            self.kept = {
                k: v for k, v in self.kept.items() if now - v["at"] < NOTE_SECONDS
            }
            self.kept[token] = {**note, "at": now}
        return token

    def change(self, token: str, **note: object) -> None:
        with self.lock:
            if token in self.kept:
                self.kept[token] = {**self.kept[token], **note, "at": time.monotonic()}

    def get(self, token: str | None) -> dict | None:
        with self.lock:
            found = self.kept.get(token or "")
            return (
                dict(found)
                if found and time.monotonic() - found["at"] < NOTE_SECONDS
                else None
            )

    def start_merge(self, key: tuple[str, str], **note: object) -> tuple[str, bool]:
        """The token of the merge of a task: the one that runs, or a new one that this
        call starts (True)."""
        with self.lock:
            running = self.merging.get(key)
            if running:
                return running, False
        token = self.put(**note)
        with self.lock:
            running = self.merging.setdefault(key, token)
        return running, running == token

    def running(self, workspace: str) -> set[str]:
        """The tasks of a workspace whose merge runs now."""
        with self.lock:
            return {slug for (name, slug) in self.merging if name == workspace}


NOTES = Notes()


def said_of(ran: subprocess.CompletedProcess) -> str:
    """The script's own line: the last line it wrote to stderr, or to stdout, or
    its exit."""
    lines = [
        line.strip()
        for line in (ran.stderr or ran.stdout or "").splitlines()
        if line.strip()
    ]
    return lines[-1] if lines else f"it exited {ran.returncode} and said nothing"


def lem_run(workspace: Workspace, file: str, *args: str) -> subprocess.CompletedProcess:
    """One command of Lem's scripts for the workspace, as a session runs it, one at a
    time with the server's other calls (SCRIPT_LOCK)."""
    with SCRIPT_LOCK:
        return lem_sibling.run(SCRIPTS / file, Path(workspace.path), *args)


# The task sessions' script (stage A of task 4, `lem session`), which the server runs
# only as `open`, `wake` and `list`. LEM_SESSION_SCRIPT names another file in its place:
# a test's stand-in.
SESSION_SCRIPT = SCRIPTS / "session.py"


def session_run(workspace: Workspace, *args: str) -> subprocess.CompletedProcess:
    """One command of `lem session` for the workspace (`open SLUG --why WHY`,
    `wake SLUG --why WHY`, `list`), one at a time with the server's other calls into
    Lem's scripts (SCRIPT_LOCK)."""
    script = Path(os.environ.get("LEM_SESSION_SCRIPT") or SESSION_SCRIPT)
    with SCRIPT_LOCK:
        return lem_sibling.run(script, Path(workspace.path), *args)


# What `lem session list` printed, by task: the model's one reading of it, which
# `lem project waiting` shares.
session_entries = bm.session_entries


def asked_from(workspace: Workspace, slug: str, act: str, via: str, *more: str) -> str:
    """Log who asked for an act that the script took, as the event `board.act`: the act
    and where the owner's word came from (bm.VIA), never his login, and MORE fields
    (`key=`, `option=` of a row's answer). "" when it is written, else why not."""
    ran = lem_run(
        workspace,
        "project.py",
        "log",
        slug,
        "board.act",
        f"act={act}",
        f"via={via}",
        *more,
    )
    return (
        ""
        if ran.returncode == 0
        else f" The record of where you asked was not written: {said_of(ran)}"
    )


def task_of(workspace: Workspace, slug: str) -> "bm.Task | None":
    """The task as the board shows it, also one whose session opened and wrote no state
    yet (bm.NEW), or None."""
    t = workspace.model().by_slug.get(slug)
    return t if t is not None and t.blocks else None


def inbox_link(name: str, slug: str) -> str:
    """The address of a task's page on the board for a message of the Inbox: through the
    tailnet door when it is open, so that the owner's phone opens it, else on
    this Mac."""
    base = RUNNING.get("tailscale") or RUNNING.get("url") or f"http://{HOST}:{PORT}/"
    return f"{base}{quote(HOSTNAME)}/{quote(name)}/tasks/{quote(slug, safe='')}"


def inbox_wake(workspace: Workspace, slug: str) -> bool:
    """The word to the task's live session that the Inbox has a thing of it, or a reply
    of the owner's for it: `lem session wake SLUG --why inbox`, which opens no session.
    Whether a live session got it."""
    ran = session_run(workspace, "wake", slug, "--why", "inbox")
    if ran.returncode != 0:
        sys.stderr.write(
            f"serve.py: {workspace.name}: `lem session wake {slug} --why inbox` exited "
            f"{ran.returncode}: {said_of(ran)}\n"
        )
        return False
    try:
        told = json.loads(ran.stdout)
    except ValueError:
        return False
    return isinstance(told, dict) and told.get("woke") is True


def tell_session(workspace: Workspace, slug: str) -> dict:
    """After the owner's act on a task, the word to its session, which may wait for him:
    `lem session wake SLUG --why owner`, a pane message to the live one, or a session
    opened when none lives and the task needs one. What came of it: `woke`, `opened`, or
    `said` with why nobody was told."""
    ran = session_run(workspace, "wake", slug, "--why", "owner")
    if ran.returncode != 0:
        return {"woke": False, "opened": False, "said": said_of(ran)}
    try:
        told = json.loads(ran.stdout)
    except ValueError:
        told = {}
    told = told if isinstance(told, dict) else {}
    workspace.look_sessions()
    return {
        "woke": bool(told.get("woke")),
        "opened": bool(told.get("opened")),
        "name": told.get("name"),
        "said": "",
    }


def row_refusal(
    t: "bm.Task", asks: dict | None, given: object, folder: Path
) -> str | None:
    """Why the board takes no act on the row GIVEN (a row's key, from the page) of the
    task T, whose row the board answers now is ASKS (`bm.answer_row`), else None: the
    record of the row's key is the one arbiter of every act of the board on it
    (lem_answers). A key with an answer on record says what took effect; a key that is
    not the row that waits now says what holds instead; ASKS with an answer on record
    says it."""
    key = str(given or "") or (asks["key"] if asks else "")
    try:
        parts = lem_answers.parse(key)
        made = lem_answers.on_record(folder, key)
    except lem_answers.AnswerError as error:
        return f"{bm.cap(str(error))}: nothing was recorded."
    if made is not None:
        return f"{lem_answers.took_effect(made)}: the task’s session takes it."
    if asks is not None and asks["key"] == key:
        return None
    what = {
        "breaker": f"Breaker {parts['number']} of {t.slug}",
        "plan": f"The plan of {t.slug}",
        "skip": f"“Skip the persona read?” of {t.slug}",
        "criterion": f"“{bm.criterion_question(t)}” of {t.slug}",
    }[parts["kind"]]
    if (
        asks is not None
        and asks["kind"] == parts["kind"]
        and lem_answers.parse(asks["key"])["number"] == parts["number"]
    ):
        return (
            f"{what} waits again since {bm.hhmm(t.blocks[-1]['ts'])}, and the page you "
            "answered from showed an earlier wait: read it again, then answer. "
            "Nothing was recorded."
        )
    now = (
        f"you parked it at {bm.hhmm(t.since)}"
        if t.status == bm.PARKED
        else f"it is {t.info['label'].lower()} since {bm.hhmm(t.since)}"
    )
    return f"{what} no longer waits: {now}. Nothing was recorded."


def told_then(told: dict, then: str) -> str:
    """What came of the word to the task's session after an act (`tell_session`), with
    what it does THEN."""
    if told["woke"]:
        return f"The task’s session got word of it, and {then}."
    if told["opened"]:
        return (
            "No session of the task ran: Lem opened one in agterm, at the end of its "
            f"workspace, and it {then.removeprefix('it ')}."
        )
    return (
        f"The task’s session was not told: {told['said']} Open a session of the task "
        f"here, and it {then.removeprefix('it ')}."
    )


def act_approve(  # noqa: C901, PLR0911 - over the limit before the limit was set
    workspace: Workspace, slug: str, form: dict, via: str, heard: dict | None = None
) -> dict:
    """The owner's yes to the criteria of the task directory, `lem criteria approve SLUG
    --file criteria.md`, while they wait for it and are the criteria the page showed
    (`digest`). His yes to the criteria that have a row the board answers
    (`bm.answer_row`: the fast track's one criterion, and the standard track's criteria
    on a task of the board's release) is his Yes on that row: its record is linked first
    (lem_answers, with HEARD: `via`, `device`, `agent`), and taken back when the
    approval's script refuses. While a change of the criteria from his note stopped in
    the middle (`Task.changing`) no yes is taken: the new text has no request with the
    old text beside it yet."""
    t = task_of(workspace, slug)
    model = workspace.model()
    if t is not None and t.changing:
        return {
            "ok": False,
            "said": (
                "Lem writes the changed criteria: the new request comes in a moment. "
                "Nothing was approved."
            ),
        }
    if t is None or "approve" not in bm.acts_of(t, model.seen):
        return {
            "ok": False,
            "said": f"The criteria of {slug} do not wait for your yes now"
            + (f": it is {t.info['label'].lower()}." if t else "."),
        }
    folder = workspace.state / "tasks" / slug
    asks = bm.answer_row(t)
    criterion = asks if asks and asks["kind"] == "criterion" else None
    if criterion:
        said = row_refusal(t, criterion, form.get("key"), folder)
        if said:
            return {"ok": False, "said": said}
    waiting = workspace.criteria_waiting(slug)
    if waiting is None:
        return {
            "ok": False,
            "said": (
                "criteria.md is not in the task directory yet: the task's session "
                "writes it. Approve the criteria there."
            ),
        }
    if form.get("digest") != waiting["digest"]:
        return {
            "ok": False,
            "said": (
                "The criteria changed since the page showed them. Read them again, "
                "then approve."
            ),
        }
    made = None
    if criterion:
        won, made = lem_answers.record(
            folder,
            criterion["key"],
            criterion["question"],
            "yes",
            note_of(form),
            digest=waiting["digest"],
            **(heard or {}),
        )
        if not won:
            return {
                "ok": False,
                "said": (
                    f"{lem_answers.took_effect(made)}: the task’s session takes it."
                ),
            }
    # the digest goes with the file, so that the step approves the bytes the page showed
    # or nothing
    ran = lem_run(
        workspace,
        "criteria.py",
        "approve",
        slug,
        "--file",
        waiting["path"],
        "--shown",
        waiting["digest"],
    )
    if ran.returncode != 0:
        if made:
            lem_answers.withdraw(folder, made)
        return {"ok": False, "said": said_of(ran)}
    asked = asked_from(workspace, slug, "approve", via)
    then = told_then(tell_session(workspace, slug), "it goes on to the build")
    return {
        "ok": True,
        "said": f"Your yes to the criteria is on record. {then}" + asked,
    }


def act_park(
    workspace: Workspace, slug: str, form: dict, via: str, heard: dict | None = None
) -> dict:
    """The owner puts aside a task whose breaker waits for him,
    `lem project state SLUG parked WHY`, with his one line of why (`/lem park`,
    stages/park.md). His Park is the answer to the breaker's row (`bm.answer_row`): its
    record is linked first (lem_answers, with HEARD), and taken back when the state's
    script refuses."""
    t = task_of(workspace, slug)
    if t is None or "park" not in bm.acts_of(t, workspace.model().seen):
        return {
            "ok": False,
            "said": (
                f"No breaker of {slug} waits for you now: the board parks a task whose "
                "breaker stopped its build."
            ),
        }
    folder = workspace.state / "tasks" / slug
    asks = bm.answer_row(t)
    asks = asks if asks and asks["kind"] == "breaker" else None
    made = None
    if asks:
        said = row_refusal(t, asks, form.get("key"), folder)
        if said:
            return {"ok": False, "said": said}
    why = (
        " ".join(str(form.get("why") or "").split())[:WHY_CHARS]
        or "the owner parked it"
    )
    if asks:
        won, made = lem_answers.record(
            folder, asks["key"], asks["question"], "park", why, **(heard or {})
        )
        if not won:
            return {
                "ok": False,
                "said": (
                    f"{lem_answers.took_effect(made)}: the task’s session takes it."
                ),
            }
    ran = lem_run(workspace, "project.py", "state", slug, "parked", why)
    if ran.returncode != 0:
        if made:
            lem_answers.withdraw(folder, made)
        return {"ok": False, "said": said_of(ran)}
    asked = asked_from(workspace, slug, "park", via)
    told = tell_session(workspace, slug)
    ends = (
        "Its session got word of it, and closes once you have left it. "
        if told["woke"]
        else ""
        if not told["said"]
        else f"Its session was not told ({told['said']}): close it yourself in agterm. "
    )
    return {
        "ok": True,
        "said": (
            f"The task is parked. {ends}/lem resume {slug} in any "
            "session brings it back."
        )
        + asked,
    }


# The longest note of a row's answer the board takes, in characters
# (lem_board_pages.NOTE_CHARS, the form's own bound).
NOTE_CHARS = pages.NOTE_CHARS
# What the task's session does with each answer it takes from the board, for the
# act's note.
ANSWER_THEN = {
    "build": "it builds the plan",
    "drop": "it drops the task as on /lem drop",
    "help": "it takes your words to the lead as your part of the talk",
    "yes": "it takes your yes",
    "no": "it takes your no",
}


def note_of(form: dict) -> str:
    """The owner's note of an answer, from the form's `words`: its words on one line, at
    most NOTE_CHARS."""
    return " ".join(str(form.get("words") or "").split())[:NOTE_CHARS]


def act_answer(workspace: Workspace, slug: str, form: dict, heard: dict) -> dict:  # noqa: C901, PLR0911, PLR0912 - over the limit before the limit was set
    """The owner's answer to a row the board answers with its own buttons
    (`bm.answer_row`: a plan, a breaker, "Skip the persona read?", the criteria's yes),
    from its answer form: the row's `key`, the `option` and his note (`words`). It
    refuses a key that is not the row that waits now, a key with an answer on record
    (`row_refusal`), no option, an option the row does not have, Help and the
    criterion's No with no words, the criterion's No on a text that changed since the
    page showed it, and a Drop with no confirm. Park is `act_park`, and Yes on the
    criterion `act_approve`, each of which links the row's record first. Else it links
    the record (lem_answers, with HEARD), logs `board.act act=answer` and wakes the
    task's session, which takes the answer as his typed word: the server
    decides nothing."""
    t = task_of(workspace, slug)
    if t is None:
        return {
            "ok": False,
            "said": f"No task {slug} is on record: nothing was recorded.",
        }
    folder = workspace.state / "tasks" / slug
    asks = bm.answer_row(t)
    said = row_refusal(t, asks, form.get("key") or "-", folder)
    if said:
        return {"ok": False, "said": said}
    option, words = str(form.get("option") or ""), note_of(form)
    if not option:
        return {"ok": False, "said": "Pick an option first: nothing was recorded."}
    if option not in asks["options"]:
        return {
            "ok": False,
            "said": (
                f"“{asks['question']}” takes {', '.join(asks['options'].values())}: "
                "nothing was recorded."
            ),
        }
    via = bm.VIA[heard.get("via") or "local"]
    if option == "park":
        return act_park(workspace, slug, {**form, "why": words}, via, heard=heard)
    if asks["kind"] == "criterion" and option == "yes":
        return act_approve(workspace, slug, form, via, heard=heard)
    if option == "help" and not words:
        return {
            "ok": False,
            "said": "Help needs your words for the lead: nothing was recorded.",
        }
    more = {}
    if asks["kind"] == "criterion":
        # his No changes the criteria: the fast track's session writes his words in, the
        # standard track's writes the change in its own words and asks again
        # (`lem criteria change`); either needs his words
        fast = bm.fast_criterion(t)
        if not words:
            return {"ok": False, "said": f"{asks['note']} Nothing was recorded."}
        waiting = workspace.criteria_waiting(slug)
        if waiting is None or form.get("digest") != waiting["digest"]:
            return {
                "ok": False,
                "said": (
                    "The criterion changed since the page showed it. "
                    "Read it again, then answer: nothing was recorded."
                )
                if fast
                else (
                    "The criteria changed since the page showed them. Read them again, "
                    "then answer: nothing was recorded."
                ),
            }
        more["digest"] = waiting["digest"]
    if option == "drop" and form.get("confirm") != "yes":
        return {
            "ok": False,
            "said": (
                "Drop asks for a confirm first: open Drop… and confirm there. "
                "Nothing was recorded."
            ),
        }
    try:
        won, made = lem_answers.record(
            folder, asks["key"], asks["question"], option, words, **more, **heard
        )
    except (lem_answers.AnswerError, OSError) as error:
        return {"ok": False, "said": f"The answer was not recorded: {error}."}
    if not won:
        return {
            "ok": False,
            "said": f"{lem_answers.took_effect(made)}: the task’s session takes it.",
        }
    asked = asked_from(
        workspace,
        slug,
        "answer",
        via,
        f"key={asks['key']}",
        f"option={option}",
        f"question={asks['question']}",
    )
    then = told_then(
        tell_session(workspace, slug),
        ANSWER_THEN[option]
        if not (
            asks["kind"] == "criterion" and option == "no" and not bm.fast_criterion(t)
        )
        else "it changes the criteria from your words and asks for your yes again",
    )
    return {"ok": True, "said": f"{bm.ANSWER_ON_RECORD} {then}" + asked}


# What the board says when the owner's "Open a session" of a stopped task opened nothing
# (`lem session open SLUG --why stopped` printed `acted: false`), by its `why`
# (session.py REFUSALS).
NOT_OPENED = {
    "working": "Its session works again, so no session was opened",
    "gone": (
        "Its session is gone from agterm, so no session was opened beside it: "
        "the board offers a fresh one in its place within a minute"
    ),
    "status": (
        "The task is no longer building, ready or landing, so no session was opened"
    ),
    "unread": (
        "The board cannot read whether its session works, and its stop no longer waits "
        "for you, so no session was opened beside it"
    ),
}


def act_session(workspace: Workspace, slug: str, form: dict, via: str) -> dict:
    """A fresh session of a task none of whose sessions lives
    (`lem_board_model.opens_session`), on the owner's click:
    `lem session open SLUG --why dead` for a task that had one, `--why owner` for one
    that never did, and `--why stopped` for a task whose stop the guard logged while its
    session lives (`lem_board_model.stopped_of`), which opens beside that session, or
    opens nothing and says why (NOT_OPENED) when the look once more refuses it. The
    server never selects it: it opens with no focus, at the end of agterm's
    workspace."""
    t = task_of(workspace, slug)
    model = workspace.model()
    if t is None or not bm.opens_session(t, model):
        live = bm.live_of(t, model) if t else None
        why = (
            "its session runs: go to it in agterm"
            if live and live["live"]
            else (
                "the board does not know yet whether its session runs; "
                "look again in a minute"
            )
            if t and live is None
            else f"it is {t.info['label'].lower()}"
            if t
            else "no such task is on record"
        )
        return {"ok": False, "said": f"No session of {slug} was opened: {why}."}
    stopped = bm.stopped_of(t, model) is not None
    ran = session_run(
        workspace,
        "open",
        slug,
        "--why",
        "stopped" if stopped else "dead" if t.opened else "owner",
    )
    if ran.returncode != 0:
        return {"ok": False, "said": said_of(ran)}
    try:
        opened = json.loads(ran.stdout)
    except ValueError:
        opened = {}
    if isinstance(opened, dict) and opened.get("acted") is False:
        workspace.look_sessions()
        why_not = NOT_OPENED.get(
            opened.get("why", ""), opened.get("say") or "No session was opened"
        )
        return {
            "ok": False,
            "said": f"{why_not}.",
        }
    name = opened.get("name") if isinstance(opened, dict) else None
    workspace.look_sessions()
    if isinstance(opened, dict) and opened.get("already"):
        return {
            "ok": True,
            "said": (
                f"The session {name or 'of the task'} runs already: go to it in agterm."
            )
            + asked_from(workspace, slug, "session", via),
        }
    beside = (
        f" beside the one that stopped, which agterm now names “{slug} · replaced”"
        if stopped
        else ""
    )
    return {
        "ok": True,
        "said": (
            f"A session of the task opened in agterm{f', “{name}”' if name else ''}, "
            f"at the end of its workspace{beside}. Its agent reads the task’s state "
            "and goes on from there."
        )
        + asked_from(workspace, slug, "session", via),
    }


# ---- a card of a task's session, answered on the board ----

# The largest answer of a card the board takes, in bytes: the page's JSON, with a note
# of a few paragraphs and the values of a few sliders (a guess).
CARD_BYTES = 65536
# What the board says to a note with no option picked, and to the page's wish to talk:
# the owner's ruling of 2026-11-23, "The board takes an answer with a note, never
# a conversation."
TO_THE_SESSION = (
    "A question goes to the task’s session, at the Mac: nothing was recorded."
)
# The words of the end of a card the board recorded (task 1 of board-answers-a-card: the
# session reads it).
ON_RECORD = bm.ANSWER_ON_RECORD
# A request that names a phone, by decision 5 of the plan of board-answers-a-card: the
# client hint of a mobile browser, or a User-Agent that names an iPhone, an iPad or
# Android. A phone in a desktop mode says it is a computer, and the record keeps the
# User-Agent whole beside it.
PHONE_AGENT = re.compile(r"\b(iPhone|iPad|Android)\b")


def device_of(headers: email.message.Message) -> str:
    """`phone` when the request names a phone (PHONE_AGENT, `Sec-CH-UA-Mobile: ?1`),
    else `computer`."""
    if (headers.get("Sec-CH-UA-Mobile") or "").strip() == "?1":
        return "phone"
    return (
        "phone" if PHONE_AGENT.search(headers.get("User-Agent") or "") else "computer"
    )


class PageScripts(html.parser.HTMLParser):
    """The text of each script a page runs inline: a `<script>` with no `src`, whose
    `type` is none or JavaScript's. Its `script` and `style` text is read as the browser
    reads it (CDATA, up to the closing tag), so a spec's text in the page's JSON block
    is never taken for a tag."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.found: list[str] = []
        self.inside: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag != "script":
            return
        given = dict(attrs)
        kind = (given.get("type") or "").strip().lower()
        self.inside = (
            []
            if "src" not in given
            and kind in ("", "text/javascript", "module", "application/javascript")
            else None
        )

    def handle_data(self, data: str) -> None:
        if self.inside is not None:
            self.inside.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.inside is not None:
            self.found.append("".join(self.inside))
            self.inside = None


def card_policy(page: bytes) -> str:
    """The Content-Security-Policy of a card's page on the board (decision 2 of
    board-answers-a-card): it runs only the inline scripts `lem-ask` builds into the
    page (`build_html`: its runtime and the pinned mermaid bundle), each by its hash,
    with no `unsafe-eval`, so that a spec's own `script` and `js` blocks, which the
    runtime runs through `new Function`, and an inline handler in its raw `html` or
    `svg` markup do not run on the board's origin, where the owner's acts are.
    `form-action` keeps a form in that markup from posting an act, `base-uri` keeps a
    `<base>` from moving the runtime's own post, and only the board frames the page. The
    spec's text is JSON in the page, escaped so that it opens no tag."""
    reader = PageScripts()
    reader.feed(page.decode("utf-8", errors="replace"))
    reader.close()
    hashes = sorted(
        {
            "'sha256-"
            + base64.b64encode(hashlib.sha256(text.encode("utf-8")).digest()).decode(
                "ascii"
            )
            + "'"
            for text in reader.found
        }
    )
    sources = " ".join(hashes) or "'none'"
    return (
        f"script-src {sources}; form-action 'none'; base-uri 'none'; "
        "object-src 'none'; frame-src 'none'; frame-ancestors 'self'"
    )


def card_refusal(card: dict, given: object) -> str | None:  # noqa: C901, PLR0911, PLR0912 - over the limit before the limit was set
    """Why the board takes no answer GIVEN to CARD (the card's record,
    `lem_cards.card`), else None. A wish to talk, and a note with no option picked on a
    question with options, go to the session (the page's own rule: `valid` and `finish`
    in `runtime/ask.js` send a note alone as a `text` with an empty `selected` on a
    `single` or `multi` question); a `tune` question's answer is its values, a `text`
    question's its text, and an `optional` question answered with nothing is an answer.
    An answer that names a question or an option the card does not have is refused."""
    if not isinstance(given, dict):
        return "The card’s page sent no answer: nothing was recorded."
    if given.get("status") == "chat":
        return TO_THE_SESSION
    if given.get("status") != "answered" or not isinstance(given.get("answers"), dict):
        return "The card’s page sent no answer: nothing was recorded."
    questions = {
        str(q.get("id")): q for q in card.get("questions") or [] if isinstance(q, dict)
    }
    answers = given["answers"]
    if set(answers) != set(questions):
        return (
            "This answer names questions the card does not ask: nothing was recorded. "
            "Load the card again."
        )
    for qid, q in questions.items():
        a = answers[qid]
        if not isinstance(a, dict):
            return "The card’s page sent no answer: nothing was recorded."
        selected = a.get("selected") if a.get("selected") is not None else []
        text = a.get("text")
        if (
            not isinstance(selected, list)
            or not all(isinstance(x, str) for x in selected)
            or (text is not None and not isinstance(text, str))
        ):
            return "The card’s page sent no answer: nothing was recorded."
        ids = {str(o.get("id")) for o in q.get("options") or [] if isinstance(o, dict)}
        if not set(selected) <= ids or (
            q.get("mode") == "single" and len(selected) > 1
        ):
            return (
                "This answer names an option the card does not have: "
                "nothing was recorded. Load the card again."
            )
        if q.get("mode") in ("single", "multi") and not selected:
            if (text or "").strip():
                return TO_THE_SESSION
            if not q.get("optional"):
                return "Pick an option first: nothing was recorded."
        if (
            q.get("mode") == "text"
            and not (text or "").strip()
            and not q.get("optional")
        ):
            return "Type an answer first: nothing was recorded."
        if q.get("mode") == "tune" and not isinstance(a.get("values"), dict):
            return "The card’s page sent no values: nothing was recorded."
    return None


def card_answer_of(card: dict, given: dict) -> dict:
    """The answer the record keeps, from what the page sent (`card_refusal` took it):
    each question's picks, with the card's own labels of them, its text and its values
    as the page gave them."""
    questions = {
        str(q.get("id")): q for q in card.get("questions") or [] if isinstance(q, dict)
    }
    out = {}
    for qid, q in questions.items():
        a = given["answers"][qid]
        labels = {
            str(o.get("id")): str(o.get("label") or o.get("id"))
            for o in q.get("options") or []
            if isinstance(o, dict)
        }
        selected = list(a.get("selected") or [])
        kept = {"selected": selected, "labels": [labels[x] for x in selected]}
        for key in ("text", "values", "from", "extra"):
            if a.get(key) is not None:
                kept[key] = a[key]
        out[qid] = kept
    return {"status": "answered", "answers": out}


def agterm_card_refusal(page: str) -> str | None:  # noqa: PLR0911 - over the limit before the limit was set
    """agterm's word on the card's page before the board takes an answer (decision 8 of
    board-answers-a-card), else None: a read of `agtermctl session overlay result --page
    PAGE`, the read lem-ask's own wait makes. When agterm holds an answer or a dismissal
    no waiter has read yet, the pick at the Mac came first and the board takes nothing;
    when agterm does not answer, the board cannot tell. A read only: the server never
    answers, closes or types into a session's page."""
    ctl = agtermctl()
    if ctl is None:
        return (
            "agtermctl is not on this Mac, so the board cannot tell whether the card "
            "was answered at the Mac: nothing was recorded."
        )
    try:
        ran = subprocess.run(
            [ctl, "session", "overlay", "result", "--page", page, "--json"],
            capture_output=True,
            text=True,
            check=False,
            timeout=AGTERM_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return (
            f"agterm did not say whether the card was answered at the Mac ({error}): "
            "nothing was recorded."
        )
    try:
        reply = json.loads(ran.stdout)
    except ValueError:
        said = (
            ran.stderr or ran.stdout
        ).strip() or f"agtermctl exited {ran.returncode}"
        return (
            f"agterm did not say whether the card was answered at the Mac ({said}): "
            "nothing was recorded."
        )
    if not isinstance(reply, dict) or reply.get("ok") is False:
        said = reply.get("error") if isinstance(reply, dict) else None
        return (
            "agterm did not say whether the card was answered at the Mac "
            f"({said or 'no outcome'}): nothing was recorded."
        )
    outcome = ((reply.get("result") or {}).get("pageOutcome") or {}).get("outcome")
    if outcome == "submitted":
        return (
            "An answer was given on the card at the Mac: the task’s session takes it, "
            "and nothing was recorded here."
        )
    if outcome == "dismissed":
        return (
            "The card was dismissed at the Mac: the task’s session takes it, and "
            "nothing was recorded here."
        )
    return None


def act_card(  # noqa: C901, PLR0911, PLR0913, PLR0917 - over the limit before the limit was set
    workspace: Workspace,
    slug: str,
    page: str,
    given: object,
    via: str,
    device: str,
    agent: str,
) -> tuple[int, str | None]:
    """The owner's answer to the card PAGE of the task's session, from the card's page
    on the board: the status of the reply and its `said`, which the page shows. In this
    order it refuses a card that is not open (what took effect), one whose session no
    longer waits for it, a wish to talk or a note with no pick (`card_refusal`), and an
    answer agterm already holds (`agterm_card_refusal`); a dismissal, which the page's
    `pagehide` sends, records nothing (204). Else it ends the card in its folder with
    the answer, from the board (`lem_cards.end`, which logs `card.answered`), unless the
    session's own end was linked first, and logs `board.act act=answer`. The end of the
    card's own `lem-ask` in the session is the wake: the server sends the
    session nothing."""
    folder = workspace.state / "tasks" / slug
    try:
        card = lem_cards.card(folder, page)
    except lem_cards.CardError as error:
        return HTTPStatus.NOT_FOUND, str(error)
    if card is None:
        return HTTPStatus.NOT_FOUND, f"No card {page} of {slug} is on record."
    if isinstance(given, dict) and given.get("status") == "dismissed":
        return HTTPStatus.NO_CONTENT, None
    try:
        end = lem_cards.ended(folder, page)
    except lem_cards.CardError as error:
        return HTTPStatus.CONFLICT, f"{error}: nothing was recorded."
    if end is not None:
        return (
            HTTPStatus.CONFLICT,
            f"{bm.cap(lem_cards.took_effect(end))}: nothing was recorded.",
        )
    model = workspace.model()
    t = task_of(workspace, slug)
    if t is None or not any(c["page"] == page for c in bm.open_cards(t, model)):
        live = bm.live_of(t, model) if t else None
        why = (
            (
                "the board does not know yet whether the task’s session runs; "
                "look again in a minute"
            )
            if t is not None and live is None and not model.meta.get("demo")
            else (
                "the session that put it up no longer runs, "
                "so nothing waits for this answer"
            )
        )
        return HTTPStatus.CONFLICT, f"{bm.cap(why)}: nothing was recorded."
    said = card_refusal(card, given)
    if said:
        return HTTPStatus.UNPROCESSABLE_ENTITY, said
    said = agterm_card_refusal(page)
    if said:
        return HTTPStatus.CONFLICT, said
    try:
        won, record = lem_cards.end(
            folder,
            page,
            "answered",
            "board",
            card_answer_of(card, cast("dict", given)),  # a dict: card_refusal took it
            via=via,
            device=device,
            agent=agent,
        )
    except (lem_cards.CardError, OSError) as error:
        return (
            HTTPStatus.INTERNAL_SERVER_ERROR,
            f"The answer was not recorded: {error}.",
        )
    if not won:
        return (
            HTTPStatus.CONFLICT,
            f"{bm.cap(lem_cards.took_effect(record))}: nothing was recorded.",
        )
    workspace.acted += 1
    return HTTPStatus.OK, ON_RECORD + asked_from(workspace, slug, "answer", bm.VIA[via])


# How many plain words of the owner's text name a task he starts from the board: a slug
# is two to five plain words (stages/new.md, "The slug"), so five, the most it takes.
SLUG_WORDS = 5
# The longest text of a new task the board takes, in characters: a few sentences
# (a guess).
WORDS_CHARS = 2000
PLAIN_WORD = re.compile(r"[a-z0-9]+")


def slug_of(text: str, words: int | None = SLUG_WORDS) -> str:
    """The slug of a task from text: its first WORDS plain words (letters a to z and
    digits), in lower case, joined by hyphens; all of them with no WORDS. "" when it
    holds none."""
    plain = PLAIN_WORD.findall(text.lower())
    return "-".join(plain[:words] if words else plain)


def item_slug(
    stem: str, ended: Callable[[str], bool], taken: Callable[[str], bool]
) -> str:
    """The slug of a task started from a backlog item that no task holds: its file's
    STEM (or its plain words, `slug_of`, for a stem that is no slug), or, when
    ENDED(slug) says that a task of that slug ended, the stem with the first `-2`, `-3`
    that TAKEN(slug) says no task has: an item whose task was dropped is undecided again
    and starts again. A task of the stem that has not ended keeps the stem, which the
    start then refuses."""
    slug = stem if TASK_SLUG.fullmatch(stem) else slug_of(stem, None)
    if not slug or not ended(slug):
        return slug
    n = 2
    while taken(f"{slug}-{n}"):
        n += 1
    return f"{slug}-{n}"


def release_behind(workspace: Workspace) -> str | None:
    """Why the board starts no task for the workspace, or None: the Lem its sessions
    load is older than this Lem's release before (lem_release.BEFORE). Its new task
    would carry that release as its mark, and every act of this board on it would stop
    at once."""
    try:
        version = lem_release.running()
    except ValueError as error:
        return str(error)
    release = lem_release.chosen(lem_release.installs(), workspace.path, version)
    if lem_release.numbers(release) >= lem_release.numbers(lem_release.BEFORE):
        return None
    return (
        f"The Lem this project's sessions load is {release}, and this board runs Lem "
        f"{version}, which reads only tasks begun on {lem_release.BEFORE} or "
        f"{version}: a task started here would stop at its first step. "
        f"{lem_release.UPDATE} in a Claude Code session of this project brings the "
        "newer release; then start the task again."
    )


def act_start(workspace: Workspace, form: dict, via: str) -> dict:  # noqa: C901, PLR0911 - over the limit before the limit was set
    """A new task, on the owner's word from the board: from his words (`words`, the form
    of "+") or from a backlog item (`item`, its path from the root of the main checkout,
    of the backlog folder or of the reviewer's folder, so that two items of one stem
    stay two). An item a task that has not ended holds by its path (project.py's
    `item_holder`, the rule of the drop and of the board's mark) is refused with that
    task. The slug is the item's slug (`item_slug`), or the first SLUG_WORDS plain words
    of his text; `lem project task-dir SLUG --ask ASK` makes its directory, with his
    words or the item's path as the ask, as the night gives one;
    `lem session open SLUG --why new` opens its session with no focus. A slug of a task
    that runs is refused here, and one of a task that ended by task-dir, with its own
    line, and so is a project whose sessions load a Lem older than this one's release
    before (`release_behind`). What came of it, with `slug` when the task is
    on record."""
    item = str(form.get("item") or "").strip()
    words = " ".join(str(form.get("words") or "").split())[:WORDS_CHARS]
    model = workspace.model()
    if item:
        backlog = workspace.reader.read_backlog(board, fresh=True) or {}
        found = next(
            (it for it in backlog.get("items") or [] if it.get("path") == item), None
        )
        if found is None:
            return {
                "ok": False,
                "said": (
                    f"No item {item} is in the backlog now: read the backlog again."
                ),
            }
        holder = lem_project.item_holder(workspace.state, item)
        if holder:
            return {
                "ok": False,
                "said": (
                    f"This item has a task already: {holder['task']}, "
                    f"{holder['status'] or 'new'}."
                ),
            }
        tasks = workspace.state / "tasks"
        slug = item_slug(
            found["slug"],
            lambda name: (t := model.by_slug.get(name)) is not None and t.closed,
            lambda name: name in model.by_slug or (tasks / name).exists(),
        )
        ask = item
    elif words:
        slug, ask = slug_of(words), words
    else:
        return {
            "ok": False,
            "said": (
                "Type a few words that say what the task is: they are its ask, "
                "and its first words its name."
            ),
        }
    if not slug:
        return {
            "ok": False,
            "said": (
                "The words hold no plain letter or digit (a to z, 0 to 9) for the "
                "task's name: begin with such a word."
            ),
        }
    known = model.by_slug.get(slug)
    if known is not None and known.blocks and not known.closed:
        return {
            "ok": False,
            "slug": slug,
            "said": (
                f"{slug} is a task already, and it is {known.info['label'].lower()}: "
                "say the new one in other words."
            ),
        }
    behind = release_behind(workspace)
    if behind:
        return {"ok": False, "said": behind}
    made = lem_run(workspace, "project.py", "task-dir", slug, "--ask", ask)
    if made.returncode != 0:
        return {"ok": False, "said": said_of(made)}
    asked = asked_from(workspace, slug, "start", via)
    ran = session_run(workspace, "open", slug, "--why", "new")
    if ran.returncode != 0:
        return {
            "ok": False,
            "slug": slug,
            "said": (
                f"The task {slug} is on record, and its session did "
                f"not open: {said_of(ran)}"
            )
            + asked,
        }
    try:
        opened = json.loads(ran.stdout)
    except ValueError:
        opened = {}
    name = (opened.get("name") if isinstance(opened, dict) else None) or slug
    workspace.look_sessions()
    return {
        "ok": True,
        "slug": slug,
        "said": (
            f"Lem opened the session {name} in agterm, at the end of its workspace. "
            "Its agent reads the ask, and takes its type and its track."
        )
        + asked,
    }


def act_drop(workspace: Workspace, form: dict) -> dict:
    """The owner's drop of a reviewer's item from the board (`item`, its path from the
    root of the main checkout): `lem project proposals drop PATH`, one call under
    SCRIPT_LOCK, which reads whether a task that has not ended holds the item and
    refuses with that task, else keeps the drop in the day's record of each of its
    proposals and removes the file; a start from the board comes before it or after it,
    never between the two. An item of the backlog folder is refused by the same call: it
    leaves that folder on a branch. The event log gets no line, as no task is the
    drop's: the record is the day's file of the proposals. What came of it."""
    item = str(form.get("item") or "").strip()
    if not item:
        return {
            "ok": False,
            "said": (
                "The drop names no item: open the backlog again, "
                "and press Drop on the item."
            ),
        }
    ran = lem_run(workspace, "project.py", "proposals", "drop", item)
    if ran.returncode != 0:
        return {"ok": False, "said": said_of(ran)}
    try:
        done = json.loads(ran.stdout)
    except ValueError:
        done = {}
    names = ", ".join(done.get("proposals") or []) if isinstance(done, dict) else ""
    return {
        "ok": True,
        "said": (
            f"Dropped: {item} is gone from the backlog, and the day's record keeps the "
            f"drop of {names or 'its proposals'}, so no later "
            "reviewer proposes it again."
        ),
    }


def act_merge(workspace: Workspace, slug: str, form: dict, via: str) -> str:
    """The owner's merge, from its confirm step only (`confirm`, and the tip it showed,
    `tip`): land.py's MERGE_STEP `--by owner`, with the proposal's title as the one
    commit's subject where the history is squashed. It runs in a thread of its own, so
    that the page does not wait for the base branch and the forge: the answer is the
    token of its note at once, which says that it runs until the step ends. A task whose
    merge runs already gets that merge's token. While the owner's merge stands
    (`bm.owner_stands`), a press starts nothing: its note says that his merge stands, in
    the state `stands`, with the tip it is for; while the forge calls the pull request
    conflicting, it gets the conflict's text instead."""
    t = task_of(workspace, slug)
    stands = bm.stands_said(t, seen=workspace.model().seen) if t is not None else None
    if stands and t is not None:
        with NOTES.lock:
            running = NOTES.merging.get((workspace.name, slug))
        return running or NOTES.put(
            task=slug,
            act="merge",
            state="stands",
            tip=(t.proposal or {}).get("tip"),
            said=stands,
        )
    if t is None or "merge" not in bm.acts_of(t, workspace.model().seen):
        said = (
            f"{slug} is not open for a merge now: it is {t.info['label'].lower()}."
            if t and t.status != "open"
            else (
                "Lem lands it again: the base moved after the checks ran, so a merge "
                f"of {slug} now is refused the same way. The task’s session lands it "
                "again, and its new proposal is open for a merge."
            )
            if t and t.merge_wait == "relands"
            else (
                f"The forge calls the pull request of {slug} conflicting: "
                "the task’s session brings it onto the base first."
            )
            if t
            else f"No task {slug} is on record."
        )
        return NOTES.put(task=slug, act="merge", state="refused", said=said)
    with NOTES.lock:
        running = NOTES.merging.get((workspace.name, slug))
    if running:
        return running
    if form.get("confirm") != "yes":
        return NOTES.put(
            task=slug,
            act="merge",
            state="refused",
            said=(
                "A merge runs only from its confirm step, which names the pull request "
                "and the commit: nothing was merged."
            ),
        )
    landing = workspace.landing_of(slug)
    tip = str(landing.get("proposed") or "")
    if not tip or form.get("tip") != tip:
        return NOTES.put(
            task=slug,
            act="merge",
            state="refused",
            said=(
                "The branch was proposed again since the confirm step showed it: "
                "nothing was merged. Read the confirm step again."
            ),
        )
    # the tip the confirm step showed goes with the merge: land.py merges that proposal
    # or nothing
    return merge_in_thread(
        workspace,
        slug,
        landing,
        "owner",
        tip,
        lambda: asked_from(workspace, slug, "merge", via),
    )


def merge_tip_of(landing: dict, by: str) -> str:
    """The tip the server's own merge is for, from the landing record: the merge
    agent's, the one its review read; the owner's that stood through a new landing or a
    read of the moved base that said `safe`, the one his merge stands for. "" when the
    record has none, which land.py refuses."""
    kept = landing.get("merge_review" if by == "merger" else "owner_tap")
    return str(kept.get("tip") or "") if isinstance(kept, dict) else ""


def merge_args(
    landing: dict, slug: str, by: str, tip: str, *, standing: bool = False
) -> list[str]:
    """land.py's MERGE_STEP for a task, `--by BY --via server --tip TIP`, TIP being the
    commit the merge is for (the one the owner saw, or the one the merge agent read),
    with the proposal's title as the one commit's subject where the history is squashed,
    and `--standing` for the owner's merge that a moved base refused and that stood
    through the new landing or a read of the moved base that said `safe`."""
    args = [
        MERGE_STEP,
        slug,
        "--by",
        by,
        "--via",
        "server",
        "--tip",
        tip,
        *(["--standing"] if standing else []),
    ]
    if landing.get("history") == "squash" and landing.get("title"):
        args += ["--message", str(landing["title"])]
    return args


def merge_apart(workspace: Workspace, *args: str) -> subprocess.CompletedProcess:
    """land.py's merge for the workspace as a process of its own,
    `python3 -B land.py --repo MAIN ARGS`, with the server's environment as it is, and
    outside SCRIPT_LOCK: it waits for the base branch and the forge, and the server's
    other calls go on meanwhile. The process takes the task's step lock and the
    repository's merge lock itself, as a task's session that runs `lem land merge` does,
    so two merges of one repository still take turns; its output is its own and mixes
    with no call in this process."""
    return subprocess.run(
        [
            sys.executable,
            "-B",
            str(SCRIPTS / "land.py"),
            "--repo",
            workspace.path,
            *args,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def merge_in_thread(  # noqa: C901, PLR0913, PLR0917 - over the limit before the limit was set
    workspace: Workspace,
    slug: str,
    landing: dict,
    by: str,
    tip: str,
    after: Callable[[], str] | None = None,
    failed: Callable[[], None] | None = None,
    *,
    standing: bool = False,
) -> str:
    """Run the merge of a task, the owner's or the merge agent's (`merge_args`), in a
    thread of its own, as a process of its own (`merge_apart`), and the token of its
    note at once: the note says that it runs (NOTES.merging, which the board reads as
    "Merging…") until the step ends. A task whose merge runs already gets that merge's
    token, and no second one starts. AFTER gives what the note adds to a merge that went
    through; FAILED is called with no argument when the step did not. STANDING runs the
    owner's merge that stood through a new landing or a safe read of the moved base
    (`merge_args`). The owner's merge from the board (BY owner, not STANDING) reads the
    task again in its thread, on a fresh model, before land.py, so that a press whose
    request read the model before his first merge's refusal was logged runs none while
    that merge stands (`bm.owner_stands`); every merge of the owner's, STANDING too,
    reads it after land.py's exit 1, when the moved base refused it and his merge
    stands, which a second press that got this token reads. Either way the note's state
    is `stands`, with TIP and the sentence of the span that holds (`bm.stands_said`);
    any other exit 1 is `refused`, with land.py's line."""
    pr = landing.get("pr") if isinstance(landing.get("pr"), dict) else None
    what = (
        f"pull request #{pr['number']}"
        if pr and pr.get("number")
        else f"the branch {landing.get('branch') or slug}"
    )
    base = landing.get("base") or "the base branch"
    args = merge_args(landing, slug, by, tip, standing=standing)
    token, new = NOTES.start_merge(
        (workspace.name, slug),
        task=slug,
        act="merge",
        state="running",
        tip=tip,
        said=f"Lem merges {what} into {base}. The page shows the result when it ends.",
    )
    if not new:
        return token

    def stands(*, ended: bool) -> bool:
        # the task read again, on the log as it is now: whether his merge stands for the
        # tip of this press; before land.py only for his merge from the board, since a
        # standing merge runs while it stands
        his = by == "owner" and (ended or not standing)
        t = task_of(workspace, slug) if his else None
        said = bm.stands_said(t, tip) if t is not None else None
        if said:
            NOTES.change(token, state="stands", said=said)
        return bool(said)

    def merge() -> None:
        try:
            if stands(ended=False):
                if failed:
                    failed()
                return
            ran = merge_apart(workspace, *args)
            if ran.returncode == 0:
                NOTES.change(
                    token,
                    state="done",
                    said=(
                        f"Merged: {what} is on {base}. Within a minute the board’s "
                        "server wakes the task’s session, or opens one, which removes "
                        "its worktree, and its branch when it holds "
                        "nothing that was not merged."
                    )
                    + (after() if after else ""),
                )
            else:
                if not stands(ended=True):
                    NOTES.change(token, state="refused", said=said_of(ran))
                if failed:
                    failed()
        except Exception as error:  # noqa: BLE001 - a merge that fails says why on its page, and the server goes on
            NOTES.change(token, state="refused", said=f"The merge failed: {error!r}")
            if failed:
                failed()
        finally:
            with NOTES.lock:
                NOTES.merging.pop((workspace.name, slug), None)
            workspace.acted += 1

    threading.Thread(target=merge, name=f"merge {slug}", daemon=True).start()
    return token


# The listeners of this process, the main one first; `listen` fills it.
SERVERS: list[ThreadingHTTPServer] = []


def stop_all() -> None:
    """End the server: every stream at its next look, then the main listener, after
    which `listen` closes the door's and returns."""
    STOPPING.set()
    if SERVERS:
        SERVERS[0].shutdown()


def refresh(version: str) -> bytes:
    """One message of a served page's stream: Turbo's `refresh`, the default event, its
    id the version of the event log (`bm.log_version`: its inode and its count
    of lines)."""
    return (
        f'id: {version}\ndata: <turbo-stream action="refresh"></turbo-stream>\n\n'
    ).encode()


def behind(given: str | None, version: str) -> bool:
    """Whether a page that names the id it saw (GIVEN) is behind the log's version now:
    any id that is not the version now, also one of the same count on a log that
    `lem project prune` replaced. A request with no id is no page that saw a version."""
    return given is not None and bool(given.strip()) and given.strip() != version


def ping(version: str) -> bytes:
    """The sign of life of a quiet stream: a `ping` event, which the page hears and
    Turbo does not render, its id the version of the event log."""
    return f"id: {version}\nevent: ping\ndata: {version}\n\n".encode()


def opens_with_refresh(
    rendered: str | None, since: str | None, last_id: str | None, version: str
) -> bool:
    """Whether a stream gets a refresh the moment it opens, from its request and the
    log's version now. A page's open after a render (its load, or a visit to another
    task) names the id its page shows (`rendered`), and gets one only when it is behind
    the log (`behind`). An open after the page may have missed a change, `since` from a
    page back on the screen or whose stream went down, or the browser's own
    `Last-Event-ID`, gets one whatever the log: what it missed may be a change that adds
    no line to the log (the owner's mark, the settings, the backlog, a task's files, an
    act of the server). An open that names none of them gets none."""
    if last_id or since is not None:
        return True
    return behind(rendered, version)


class Look:
    """What a stream last told of a state folder: the version of its event log (its
    inode and its count of lines), a digest of the content of each watched file, which
    it reads again only when the file's `stat` changed, and of a watched folder the
    names, sizes and times of its files (of every file under it, for the folder named
    `task`). A file written again with the same content is no change."""

    def __init__(self, state: Path, files: dict[str, Path]) -> None:
        self.state = state
        # the files and folders it watches beside the log, by name
        self.files = files
        self.log_at = (0, 0)
        self.lines = 0
        self.cache: dict[Path, tuple] = {}
        self.told: dict[str, str] | None = None
        self.told_version = ""

    def count(self) -> int:
        """The lines of the event log, read on from where the last look stopped; a log
        that shrank or was replaced is counted again from its start. The inode and the
        size are the ones of the file this look holds open (`os.fstat`), so a replace
        between a look at the name and the open never counts the new file from the old
        one's offset."""
        file = self.state / EVENT_LOG
        try:
            handle = file.open("rb")
        except OSError:
            self.log_at, self.lines = (0, 0), 0
            return 0
        with handle:
            try:
                facts = os.fstat(handle.fileno())
            except OSError:
                return self.lines
            start = (
                self.log_at[1]
                if self.log_at[0] == facts.st_ino and facts.st_size >= self.log_at[1]
                else 0
            )
            if start == 0:
                self.lines = 0
            left = facts.st_size - start
            try:
                handle.seek(start)
                while left > 0:
                    chunk = handle.read(min(left, 1 << 20))
                    if not chunk:
                        break
                    self.lines += chunk.count(b"\n")
                    left -= len(chunk)
            except OSError:
                self.log_at = (facts.st_ino, facts.st_size - left)
                return self.lines
        self.log_at = (facts.st_ino, facts.st_size - left)
        return self.lines

    def version(self) -> str:
        """The log's version at the last count (`bm.log_version`)."""
        return bm.log_version(self.log_at[0], self.lines)

    def digest(self, path: Path) -> tuple[str, int] | None:
        """The file's content digest and its change time in ns, or None when it is
        not there."""
        try:
            facts = path.stat()
        except OSError:
            return None
        key = (facts.st_ino, facts.st_mtime_ns, facts.st_size)
        known = self.cache.get(path)
        if known is not None and known[0] == key:
            return known[1], facts.st_mtime_ns
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            return None
        self.cache[path] = (key, digest)
        return digest, facts.st_mtime_ns

    def changes(self) -> tuple[str, dict | None]:
        """The version of the log (its inode and its count of lines), and the watched
        files whose content changed since the last look, each with its change time in ms
        (None for a file that went); None when nothing changed. The first look names
        every file."""
        self.count()
        version = self.version()
        now: dict[str, tuple[str, int]] = {}
        for name, path in self.files.items():
            if path.is_dir():
                # a folder whose files are read elsewhere (the backlog, a task's
                # folder): a change of a name, a size or a time in it
                listing = listed(path, deep=name == "task")
                now[name] = (
                    hashlib.sha256(repr(listing).encode("utf-8")).hexdigest(),
                    max((x[2] for x in listing), default=0),
                )
            else:
                got = self.digest(path)
                if got:
                    now[name] = got
        before = self.told or {}
        changed = {
            name: now[name][1] // 1_000_000
            for name in now
            if before.get(name) != now[name][0]
        }
        changed |= {name: None for name in before if name not in now}
        first = self.told is None
        # a log that `lem project prune` replaced is a change also when its count is
        # the same
        moved = version != self.told_version
        self.told = {name: now[name][0] for name in now}
        self.told_version = version
        return version, (changed if first or changed or moved else None)


def listed(folder: Path, *, deep: bool) -> list[tuple[str, int, int]]:
    """The files of a folder that are not hidden, each with its size and its change time
    in ns; with `deep`, the files of its folders too, by their path under it. A folder
    that does not read lists what it read."""
    found = []
    for at, folders, names in os.walk(folder):
        folders[:] = (
            sorted(name for name in folders if not name.startswith(".")) if deep else []
        )
        for name in names:
            if name.startswith("."):
                continue
            file = Path(at) / name
            try:
                facts = file.stat()
            except OSError:
                continue
            found.append(
                (
                    os.path.relpath(file, folder),
                    facts.st_size,
                    facts.st_mtime_ns,
                )
            )
    return sorted(found)


class Handler(BaseHTTPRequestHandler):
    server_version = "lem-serve"
    machine: Machine
    verbose = False
    # set on the door's own handler only: the main listener serves this Mac, and checks
    # only its `Host` (`host_refusal`)
    door: Door | None = None
    # the address the main listener serves, for its own names (`own_names`); `listen`
    # sets it
    listen_host = HOST
    # the machines joined (`lem serve --join`), whose boards pass through; `listen`
    # sets it
    peers: "lem_peers.Peers"
    timeout = REQUEST_TIMEOUT

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - the base class names it so
        if self.verbose:
            sys.stderr.write(
                f"serve.py: {'door ' if self.door else ''}{self.address_string()} "
                f"{format % args}\n"
            )

    def listen_port(self) -> int:
        # the port of the listener this request came to: each of them is a
        # ThreadingHTTPServer (`bind`)
        return cast("ThreadingHTTPServer", self.server).server_address[1]

    def do_HEAD(self) -> None:
        if not self.refused(body=False):
            self.answer(body=False)

    def do_GET(self) -> None:
        if not self.refused(body=True):
            self.answer(body=True)

    def act(self) -> None:  # noqa: C901, PLR0911 - over the limit before the limit was set
        """Every method that is not a read comes here, after the door's check. The
        actions are the server's own stop (`stop_refusal`) and the two acts of agterm
        (`agterm_act`), on the main listener only; the board's notifications; and the
        board's acts on a task (`board_act`), on the main listener and through
        the door."""
        if self.refused(body=True):
            return None
        path = urlsplit(self.path).path
        if self.door is None and self.command == "POST" and path == "/api/server/stop":
            said = stop_refusal(self.client_address[0], self.headers)
            if said:
                return self.text(HTTPStatus.FORBIDDEN, said, body=True)
            self.send(
                HTTPStatus.ACCEPTED,
                json.dumps({"stopping": True, "pid": os.getpid()}).encode("utf-8"),
                "application/json",
                body=True,
            )
            threading.Thread(target=stop_all, daemon=True).start()
            return None
        if (
            self.command == "POST"
            and path.startswith("/api/push/")
            and path.removeprefix("/api/push/") in PUSH_ACTS
        ):
            return self.push_act(path.removeprefix("/api/push/"))
        parts = unquote(path).strip("/").split("/")
        if (
            self.door is None
            and self.command == "POST"
            and len(parts) == 4  # noqa: PLR2004 - the address HOST/NAME/agterm/ACT
            and parts[0] == HOSTNAME
            and parts[2] == "agterm"
            and parts[3] in AGTERM_ACTS
        ):
            return self.agterm(parts[1], parts[3])
        if (
            self.command == "POST"
            and len(parts) == 5  # noqa: PLR2004 - the address HOST/NAME/tasks/SLUG/ACT
            and parts[0] == HOSTNAME
            and parts[2] == "tasks"
            and parts[4] in BOARD_ACTS
            and not lem_peers.hopped(self.headers)
        ):
            return self.board_act(parts[1], parts[3], parts[4])
        if (
            self.command == "POST"
            and len(parts) == 7  # noqa: PLR2004 - the address HOST/NAME/tasks/SLUG/cards/PAGE/answer
            and parts[0] == HOSTNAME
            and parts[2] == "tasks"
            and parts[4] == "cards"
            and parts[6] == "answer"
            and not lem_peers.hopped(self.headers)
        ):
            return self.card_answer(parts[1], parts[3], parts[5])
        if (
            self.command == "POST"
            and len(parts) == 3  # noqa: PLR2004 - the address HOST/NAME/start
            and parts[0] == HOSTNAME
            and parts[2] == "start"
            and not lem_peers.hopped(self.headers)
        ):
            return self.board_start(parts[1])
        if (
            self.command == "POST"
            and len(parts) == 4  # noqa: PLR2004 - the address HOST/NAME/backlog/drop
            and parts[0] == HOSTNAME
            and parts[2:] == ["backlog", "drop"]
            and not lem_peers.hopped(self.headers)
        ):
            return self.board_drop(parts[1])
        if not lem_peers.hopped(self.headers) and self.peers.get(parts[0]) is not None:
            return self.send(
                HTTPStatus.METHOD_NOT_ALLOWED,
                (
                    f"This page is the board of the machine {parts[0]}, which this "
                    f"server only shows: open {parts[0]}'s own board to act on it.\n"
                ).encode(),
                "text/plain; charset=utf-8",
                body=True,
                headers={"Allow": "GET, HEAD"},
            )
        return self.send(
            HTTPStatus.METHOD_NOT_ALLOWED,
            b"This address takes no action: it is only read.\n",
            "text/plain; charset=utf-8",
            body=True,
            headers={"Allow": "GET, HEAD"},
        )

    def agterm(self, name: str, act: str) -> None:
        """One act of agterm for a page of the workspace NAME: its checks
        (`action_refusal`), then `agterm_act`; the answer is JSON,
        `{"done": true, "said": ...}` or `{"done": false, "said": ...}`."""

        def answer(status: int, *, done: bool, said: str) -> None:
            self.send(
                status,
                json.dumps({"done": done, "said": said}).encode("utf-8"),
                "application/json",
                body=True,
            )

        port = self.listen_port()
        said = action_refusal(self.client_address[0], self.headers, port)
        if said:
            return answer(HTTPStatus.FORBIDDEN, done=False, said=said)
        workspace = self.machine.one(name)
        if workspace is None:
            return answer(
                HTTPStatus.NOT_FOUND,
                done=False,
                said=f"No workspace {name!r} on this machine.",
            )
        try:
            length = int(self.headers.get("Content-Length") or 0)
            asked = (
                json.loads(self.rfile.read(min(length, AGTERM_BYTES)) or b"{}")
                if 0 < length <= AGTERM_BYTES
                else None
            )
        except (ValueError, OSError):
            asked = None
        if not isinstance(asked, dict):
            return answer(
                HTTPStatus.BAD_REQUEST,
                done=False,
                said=(
                    "The request carries no JSON object of at "
                    f"most {AGTERM_BYTES} bytes."
                ),
            )
        try:
            done = agterm_act(workspace, act, asked)
        except AgtermRefused as error:
            return answer(HTTPStatus.UNPROCESSABLE_ENTITY, done=False, said=str(error))
        return answer(HTTPStatus.OK, done=True, said=done)

    def board_act(self, name: str, slug: str, act: str) -> None:
        """One act of the board on a task of the workspace NAME, from a form of its
        page: the owner's yes to the criteria, a merge from its confirm step, the park
        of a task a breaker holds, or a fresh session of a task with none. At the door
        the owner's login and the board's origin were checked (`door_refusal`); on the
        main listener the request must come from the board's own page on this Mac
        (`action_refusal`). The answer is a 303 to the task's page, whose address names
        the note of the result (`?note=`): what was done and what happens next, or the
        script's own line when it refused."""
        if self.door is None:
            said = action_refusal(
                self.client_address[0], self.headers, self.listen_port()
            )
            if said:
                return self.text(HTTPStatus.FORBIDDEN, said, body=True)
        workspace = self.machine.one(name)
        if workspace is None or not TASK_SLUG.fullmatch(slug):
            return self.missing(
                f"No workspace {name!r} or no task {slug!r} on this machine.", body=True
            )
        form = self.form()
        if form is None:
            return self.text(
                HTTPStatus.BAD_REQUEST,
                (
                    "The request carries no form of the board: form fields of at "
                    f"most {FORM_BYTES} bytes."
                ),
                body=True,
            )
        listener = "door" if self.door is not None else "local"
        via = bm.VIA[listener]
        # the record of a row's answer keeps where it came from as the card's end does:
        # the listener's key, the device, the User-Agent whole
        heard = {
            "via": listener,
            "device": device_of(self.headers),
            "agent": self.headers.get("User-Agent") or "",
        }
        if act == "merge":
            token = act_merge(workspace, slug, form, via)
        else:
            result = (
                act_answer(workspace, slug, form, heard)
                if act == "answer"
                else {"approve": act_approve, "park": act_park, "session": act_session}[
                    act
                ](
                    workspace,
                    slug,
                    form,
                    via,
                    **({} if act == "session" else {"heard": heard}),
                )
            )
            token = NOTES.put(
                task=slug,
                act=act,
                state="done" if result["ok"] else "refused",
                said=result["said"],
            )
            workspace.acted += 1
        under = (
            form.get("in")
            if form.get("in") in pages.UNDER and form.get("in") != "tasks"
            else None
        )
        tab = form.get("tab") if form.get("tab") == "criteria" else ""
        query = urlencode({**({"in": under} if under else {}), "note": token})
        to = (
            f"/{quote(HOSTNAME)}/{quote(name)}/tasks/{quote(slug)}"
            + (f"/{tab}" if tab else "")
            + f"?{query}"
        )
        return self.send(
            HTTPStatus.SEE_OTHER,
            b"",
            "text/plain; charset=utf-8",
            body=True,
            headers={"Location": to},
        )

    def card_answer(self, name: str, slug: str, page: str) -> None:
        """The owner's answer to a card of a task's session, posted by the card's own
        page on the board as JSON (`runtime/ask.js`), through the checks of an act on a
        task (`board_act`), then `act_card`. The answer is JSON, `{"said": ...}`, which
        the page shows: 200 when it is on record, else the refusal; the page's
        dismissal, which records nothing, gets 204 and no body."""

        def answer(status: int, said: str | None) -> None:
            if status == HTTPStatus.NO_CONTENT:
                self.send(status, b"", "text/plain; charset=utf-8", body=True)
            else:
                self.send(
                    status,
                    json.dumps({"said": said}, ensure_ascii=False).encode("utf-8"),
                    "application/json",
                    body=True,
                )

        if self.door is None:
            said = action_refusal(
                self.client_address[0], self.headers, self.listen_port()
            )
            if said:
                return answer(HTTPStatus.FORBIDDEN, said)
        workspace = self.machine.one(name)
        if workspace is None or not TASK_SLUG.fullmatch(slug):
            return answer(
                HTTPStatus.NOT_FOUND,
                f"No workspace {name!r} or no task {slug!r} on this machine.",
            )
        try:
            length = int(self.headers.get("Content-Length") or 0)
            given = (
                json.loads(self.rfile.read(length))
                if 0 < length <= CARD_BYTES
                else None
            )
        except (ValueError, OSError):
            given = None
        if not isinstance(given, dict):
            return answer(
                HTTPStatus.BAD_REQUEST,
                (
                    f"The request carries no JSON object of at most {CARD_BYTES} "
                    "bytes: nothing was recorded."
                ),
            )
        status, said = act_card(
            workspace,
            slug,
            page,
            given,
            "door" if self.door is not None else "local",
            device_of(self.headers),
            self.headers.get("User-Agent") or "",
        )
        return answer(status, said)

    def board_start(self, name: str) -> None:
        """A new task of the workspace NAME, from the form of "+" or a backlog item's
        "Start a task", through the checks of an act on a task (`board_act`), then
        `act_start`. The answer is a 303 to the new task's page with the note of the
        result, or, when no task is on record, back to the form or the backlog."""
        if self.door is None:
            said = action_refusal(
                self.client_address[0], self.headers, self.listen_port()
            )
            if said:
                return self.text(HTTPStatus.FORBIDDEN, said, body=True)
        workspace = self.machine.one(name)
        if workspace is None:
            return self.missing(f"No workspace {name!r} on this machine.", body=True)
        form = self.form()
        if form is None:
            return self.text(
                HTTPStatus.BAD_REQUEST,
                (
                    "The request carries no form of the board: form fields of at "
                    f"most {FORM_BYTES} bytes."
                ),
                body=True,
            )
        result = act_start(
            workspace, form, bm.VIA["door" if self.door is not None else "local"]
        )
        slug = result.get("slug")
        token = NOTES.put(
            task=slug,
            act="start",
            state="done" if result["ok"] else "refused",
            said=result["said"],
        )
        workspace.acted += 1
        base = f"/{quote(HOSTNAME)}/{quote(name)}"
        if slug and workspace.model().by_slug.get(slug) is not None:
            to = f"{base}/tasks/{quote(slug)}?{urlencode({'note': token})}"
        else:
            to = (
                f"{base}/{'backlog' if form.get('item') else 'new'}"
                f"?{urlencode({'note': token})}"
            )
        return self.send(
            HTTPStatus.SEE_OTHER,
            b"",
            "text/plain; charset=utf-8",
            body=True,
            headers={"Location": to},
        )

    def board_drop(self, name: str) -> None:
        """The owner's drop of a reviewer's item of the workspace NAME, from its "Drop"
        on the Backlog view, through the checks of an act on a task (`board_act`), then
        `act_drop`. The answer is a 303 to the Backlog view with the note of
        the result."""
        if self.door is None:
            said = action_refusal(
                self.client_address[0], self.headers, self.listen_port()
            )
            if said:
                return self.text(HTTPStatus.FORBIDDEN, said, body=True)
        workspace = self.machine.one(name)
        if workspace is None:
            return self.missing(f"No workspace {name!r} on this machine.", body=True)
        form = self.form()
        if form is None:
            return self.text(
                HTTPStatus.BAD_REQUEST,
                (
                    "The request carries no form of the board: form fields of at "
                    f"most {FORM_BYTES} bytes."
                ),
                body=True,
            )
        result = act_drop(workspace, form)
        token = NOTES.put(
            task=None,
            act="drop",
            state="done" if result["ok"] else "refused",
            said=result["said"],
        )
        workspace.acted += 1
        return self.send(
            HTTPStatus.SEE_OTHER,
            b"",
            "text/plain; charset=utf-8",
            body=True,
            headers={
                "Location": (
                    f"/{quote(HOSTNAME)}/{quote(name)}/backlog"
                    f"?{urlencode({'note': token})}"
                )
            },
        )

    def form(self) -> dict | None:
        """The fields of a form the board posts (urlencoded, one value each), or None
        for any other body."""
        kind = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return None
        if kind != "application/x-www-form-urlencoded" or not 0 <= length <= FORM_BYTES:
            return None
        try:
            fields = parse_qs(
                self.rfile.read(length).decode("utf-8"),
                keep_blank_values=True,
                max_num_fields=20,
            )
        except (UnicodeDecodeError, ValueError, OSError):
            return None
        return {key: values[-1] for key, values in fields.items()}

    def push_read(self, path: str, *, body: bool) -> None:
        """The board's notifications, read: the service worker, the machine's public key
        (made at first use), and what the worker shows for the newest
        push (lem_push)."""
        if path == "/sw.js":
            return self.send(
                HTTPStatus.OK,
                SERVICE_WORKER.read_bytes(),
                TYPES[".js"],
                body=body,
                headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"},
            )
        if path == "/api/push/latest":
            return self.send(
                HTTPStatus.OK,
                json.dumps(lem_push.latest()).encode("utf-8"),
                "application/json",
                body=body,
            )
        try:
            said = {"key": lem_push.machine_key()[1]}
        except lem_push.PushError as error:
            return self.send(
                HTTPStatus.SERVICE_UNAVAILABLE,
                json.dumps({"said": str(error)}).encode("utf-8"),
                "application/json",
                body=body,
            )
        return self.send(
            HTTPStatus.OK,
            json.dumps(said).encode("utf-8"),
            "application/json",
            body=body,
        )

    def push_act(self, act: str) -> None:
        """A device turns the board's notifications on or off, or asks for a test push
        to itself, with its subscription as JSON. At the door the owner's login and the
        board's origin were checked (`door_refusal`); on the main listener the request
        must come from the board's own page on this Mac (`action_refusal`). The answer
        is JSON, with `said` when it is refused."""

        def answer(status: int, said: dict) -> None:
            self.send(
                status, json.dumps(said).encode("utf-8"), "application/json", body=True
            )

        if self.door is None and action_refusal(
            self.client_address[0], self.headers, self.listen_port()
        ):
            return answer(
                HTTPStatus.FORBIDDEN,
                {
                    "said": (
                        "The board's notifications are turned on only from the board's "
                        "own page, on this Mac or through the tailnet door."
                    )
                },
            )
        try:
            length = int(self.headers.get("Content-Length") or 0)
            given = (
                json.loads(self.rfile.read(length))
                if 0 < length <= lem_push.MAX_BODY
                else None
            )
        except (ValueError, OSError):
            given = None
        if not isinstance(given, dict):
            return answer(
                HTTPStatus.BAD_REQUEST,
                {
                    "said": (
                        "The request carries no JSON object of at "
                        f"most {lem_push.MAX_BODY} bytes."
                    )
                },
            )
        try:
            if act == "subscribe":
                return answer(
                    HTTPStatus.OK,
                    lem_push.subscribe(given, self.headers.get("User-Agent") or ""),
                )
            if act == "unsubscribe":
                return answer(
                    HTTPStatus.OK, lem_push.unsubscribe(given.get("endpoint"))
                )
            return answer(HTTPStatus.OK, lem_push.send_test(given.get("endpoint")))
        except lem_push.PushError as error:
            return answer(HTTPStatus.UNPROCESSABLE_ENTITY, {"said": str(error)})

    do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = act  # noqa: N815 - the base class looks them up by these names

    def refused(self, *, body: bool) -> bool:
        """Check the request and answer 403 when it is refused; True then. At the door,
        the whole check (`door_refusal`); on the main listener, its `Host`
        (`host_refusal`)."""
        door = self.door
        if door is None:
            said = host_refusal(self.headers, self.listen_port(), self.listen_host)
        else:
            said = door_refusal(
                self.headers, self.command, door.owner, door.name, door.port
            )
            if said == NOT_THE_OWNER and door.reread():
                said = door_refusal(
                    self.headers, self.command, door.owner, door.name, door.port
                )
        if said is None:
            return False
        with contextlib.suppress(BrokenPipeError, ConnectionResetError):
            self.text(HTTPStatus.FORBIDDEN, said, body=body)
        return True

    def send(
        self,
        status: int,
        data: bytes,
        kind: str,
        *,
        body: bool,
        headers: dict | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        # same-origin: no Referer leaves for another site, and a form posted with no
        # script carries the board's own Origin (under no-referrer the browser sends
        # `null`, which `action_refusal` refuses)
        self.send_header("Referrer-Policy", "same-origin")
        for key, value in {"Cache-Control": "no-store", **(headers or {})}.items():
            self.send_header(key, value)
        self.end_headers()
        if body:
            self.wfile.write(data)

    def text(self, status: int, said: str, *, body: bool) -> None:
        self.send(
            status,
            (said + "\n").encode("utf-8"),
            "text/plain; charset=utf-8",
            body=body,
        )

    def redirect(self, to: str, *, body: bool) -> None:
        self.send(
            HTTPStatus.FOUND,
            b"",
            "text/plain; charset=utf-8",
            body=body,
            headers={"Location": to},
        )

    def answer(self, *, body: bool) -> None:  # noqa: C901, PLR0911, PLR0912 - over the limit before the limit was set
        split = urlsplit(self.path)
        path = unquote(split.path)
        machine = self.machine
        try:
            if path == "/":
                listing = self.spaces()
                if len(listing) == 1 and listing[0]["url"]:
                    return self.redirect(listing[0]["url"], body=body)
                return self.html(
                    HTTPStatus.OK,
                    pages.index_page(HOSTNAME, listing, asset_link),
                    body=body,
                )
            if path == "/api/workspaces":
                return self.send(
                    HTTPStatus.OK,
                    json.dumps(self.spaces()).encode("utf-8"),
                    "application/json",
                    body=body,
                )
            if path == "/api/server":
                return self.send(
                    HTTPStatus.OK,
                    json.dumps({**RUNNING, "push": lem_push.status()}).encode("utf-8"),
                    "application/json",
                    body=body,
                )
            if path in ("/sw.js", "/api/push/key", "/api/push/latest"):
                return self.push_read(path, body=body)
            if path == "/manifest.webmanifest":
                return self.send(
                    HTTPStatus.OK,
                    pages.manifest(asset_link).encode("utf-8"),
                    TYPES[".webmanifest"],
                    body=body,
                    headers={"Cache-Control": "no-cache"},
                )
            first, slash, rest = path[1:].partition("/")
            peer = (
                None
                if lem_peers.hopped(self.headers) or first == HOSTNAME
                else self.peers.get(first)
            )
            if peer is not None:
                return self.forwarded(peer, body=body)
            if path.startswith(("/assets/", f"/{HOSTNAME}/assets/")):
                file = ASSETS.get(
                    path.removeprefix(f"/{HOSTNAME}").removeprefix("/assets/")
                )
                if file is None or not file.is_file():
                    return self.text(HTTPStatus.NOT_FOUND, "Not found.", body=body)
                data, more = file.read_bytes(), self.caching(split.query)
                if file.suffix in (".js", ".css") and "gzip" in (
                    self.headers.get("Accept-Encoding") or ""
                ):
                    data, more = (
                        packed(file, data),
                        {**more, "Content-Encoding": "gzip", "Vary": "Accept-Encoding"},
                    )
                return self.send(
                    HTTPStatus.OK, data, TYPES[file.suffix], body=body, headers=more
                )
            if first in ALIASES:
                # the machine's other name: the same page under the one in every address
                return self.redirect(
                    f"/{quote(HOSTNAME)}/{quote(rest)}"
                    + (f"?{split.query}" if split.query else ""),
                    body=body,
                )
            if first == HOSTNAME:
                name, slash, rest = rest.partition("/")
                workspace = machine.one(name) if name else None
                if workspace is None:
                    return self.missing(
                        f"No workspace {name!r} on this machine.", body=body
                    )
                if not slash:
                    return self.redirect(
                        f"/{quote(HOSTNAME)}/{quote(name)}/", body=body
                    )
                return self.in_workspace(workspace, rest, split.query, body=body)
            # an address with no machine's name in it: the same page under it, or the
            # kanban for an address no page has
            workspace = machine.one(first)
            if workspace is None:
                return self.missing(f"No page {path!r} on this server.", body=body)
            known = (
                rest.split("/")[0] in PAGES
                or rest == "stream"
                or rest.startswith("tasks/")
            )
            to = f"/{quote(HOSTNAME)}/{quote(first)}/{quote(rest) if known else ''}"
            return self.redirect(
                to + (f"?{split.query}" if split.query and known else ""), body=body
            )
        except (lem_state.StateError, lem_project.SettingsError) as error:
            return self.failed(str(error), body=body)
        except (BrokenPipeError, ConnectionResetError):
            return None

    def spaces(self) -> list:
        """The workspaces a page lists: this machine's and each joined machine's
        (`lem_peers.merged`); for a request of another machine's server, this machine's
        in the list that server sent."""
        own = self.machine.listing()
        if lem_peers.hopped(self.headers):
            return lem_peers.with_own(
                lem_peers.spaces_of(self.headers.get(lem_peers.SPACES)), own, HOSTNAME
            )
        return lem_peers.merged(own, HOSTNAME, self.peers.states())

    def forwarded(self, peer: "lem_peers.Peer", *, body: bool) -> None:
        """A page, a file or a stream of a joined machine, passed through
        (`lem_peers.forward`); a machine that does not answer gets a page that
        says so."""
        if self.command not in ("GET", "HEAD"):
            return self.text(
                HTTPStatus.METHOD_NOT_ALLOWED,
                "Only a read passes to another machine.",
                body=body,
            )
        try:
            lem_peers.forward(
                self, peer, self.peers.base(peer), STOPPING, self.spaces()
            )
        except lem_peers.PeerError as error:
            self.html(
                HTTPStatus.BAD_GATEWAY,
                pages.error_page(
                    f"{peer.name} is not reachable",
                    f"{error}.",
                    asset_link,
                    (
                        f"{peer.name} may sleep, or its board server may not run: "
                        f"`lem serve --tailscale` on {peer.name} starts it with its "
                        "door. The workspaces of the machines that answer are at /."
                    ),
                ),
                body=body,
            )

    def in_workspace(
        self, workspace: Workspace, rest: str, query: str, *, body: bool
    ) -> None:
        """A page, or the stream, of one workspace."""
        if rest in PAGES:
            return self.page(workspace, PAGES[rest], query, body=body)
        if rest == "tasks" or rest.startswith("tasks/"):
            return self.task(
                workspace, rest.removeprefix("tasks").strip("/"), query, body=body
            )
        if rest == "stream":
            return (
                self.refreshes(workspace, query)
                if body
                else self.send(HTTPStatus.OK, b"", "text/event-stream", body=False)
            )
        return self.missing(
            f"No page {rest!r} in the workspace {workspace.name}.", body=body
        )

    def context(
        self, workspace: Workspace, query: str, *, fresh_backlog: bool = False
    ) -> "pages.Ctx":
        """What a page of the workspace is drawn from, read now."""
        model = workspace.model()
        reader = workspace.reader
        backlog = reader.read_backlog(board, fresh=fresh_backlog)
        return pages.Ctx(
            host=HOSTNAME,
            workspace=workspace.name,
            model=model,
            asset=asset_link,
            prefs=prefs_of(self.headers.get("Cookie")),
            backlog=backlog,
            problems=[
                *reader.problems.values(),
                *([workspace.session_problem] if workspace.session_problem else []),
            ],
            read_at=model.now,
            events=len(reader.events),
            log_id=reader.log_id(),
            keep_days=keep_days_of(reader),
            spaces=self.spaces(),
            native=bool(NATIVE.search(self.headers.get("User-Agent") or "")),
            local=self.door is None
            and self.client_address[0] in LOOPBACK
            and not lem_peers.hopped(self.headers),
            forge_look=dict(workspace.forge),
            filters=pages.backlog_filter(parse_qs(query)),
            # the board's acts: on this Mac, or through the door for the owner's login;
            # never on a page another machine passed through
            can_act=not lem_peers.hopped(self.headers)
            and (self.door is not None or self.client_address[0] in LOOPBACK),
            criteria_waiting=workspace.criteria_waiting,
            landing_of=workspace.landing_of,
            merging=NOTES.running(workspace.name),
            card_end=workspace.card_end,
            note=NOTES.get((parse_qs(query).get("note") or [None])[0]),
        )

    def page(self, workspace: Workspace, name: str, query: str, *, body: bool) -> None:
        """One page of the workspace, rendered from its model now; with the header
        `Turbo-Frame: task` (the panel's close), the empty frame alone."""
        try:
            ctx = self.context(
                workspace,
                query,
                fresh_backlog=name == "backlog_page" and "read" in parse_qs(query),
            )
            if self.headers.get("Turbo-Frame") == "task":
                ctx.view = {v: k for k, v in PAGES.items()}[name] or "tasks"
                status, html_ = task_pages.frame_page(ctx)
                return self.html(status, html_, body=body)
            html_ = getattr(pages, name)(ctx)
        except Exception as error:  # noqa: BLE001 - a page that fails says why, and the server goes on
            return self.broke(workspace, name, error, body=body)
        return self.html(HTTPStatus.OK, html_, body=body)

    def broke(
        self, workspace: Workspace, name: str, error: Exception, *, body: bool
    ) -> None:
        sys.stderr.write(
            f"serve.py: the page {name} of {workspace.path} failed: {error!r}\n"
        )
        import traceback

        traceback.print_exc()
        return self.failed(
            f"The page of {workspace.name} was not drawn: {error!r}.", body=body
        )

    def task(self, workspace: Workspace, rest: str, query: str, *, body: bool) -> None:
        """The board of one task: `SLUG`, `SLUG/TAB`, `SLUG/artifacts/PATH/`, and
        `SLUG/raw/PATH`, an HTML artifact. The view under the panel is `?in=VIEW`, the
        kanban by default."""
        slug, _, more = rest.partition("/")
        if not TASK_SLUG.fullmatch(slug):
            return self.missing(
                (
                    f"No task {slug!r} in the workspace {workspace.name}: "
                    "a task's name is lower-case words joined by hyphens."
                ),
                body=body,
            )
        tab, _, path = more.partition("/")
        path = path.strip("/")
        if tab == "raw":
            return self.raw(workspace, slug, path, body=body)
        if tab == "cards":
            return self.card_page(
                workspace,
                slug,
                path,
                query,
                slashed=urlsplit(self.path).path.endswith("/"),
                body=body,
            )
        if tab == "media":
            return self.media(workspace, slug, path, body=body)
        try:
            ctx = self.context(workspace, query)
            under = (parse_qs(query).get("in") or ["tasks"])[0]
            ctx.view = under if under in pages.UNDER else "tasks"
            ctx.task, ctx.tab, ctx.file = (
                slug,
                tab or "overview",
                (path or None) if tab == "artifacts" else None,
            )
            ctx.query = {name: values[-1] for name, values in parse_qs(query).items()}
            if path and tab != "artifacts":
                ctx.tab = f"{tab}/{path}"
            state = workspace.state
            plan = workspace.plan_of(slug)
            try:
                ctx.artifact_files = task_pages.artifact_files(state, slug, plan)
                ctx.artifact_map = task_pages.artifact_map(
                    state, slug, ctx.artifact_files
                )
            except OSError as error:
                ctx.artifacts_problem = (
                    f"the files of the task do not read: {error.strerror or error}"
                )
            ctx.told = workspace.told_of
            ctx.how_of = workspace.how_of
            ctx.folder_of = lambda task: task_pages.folder_of(state, task)
            ctx.media_href = lambda task: f"{ctx.base}/tasks/{quote(task)}/media/"

            def artifact(task: str, file: str) -> dict | None:
                found = lem_artifacts.one(state / "tasks" / task, task, file, plan)
                return found[0] if found else None

            ctx.artifact = artifact
            ctx.raw_href = lambda task, file: (
                f"{ctx.base}/tasks/{quote(task)}/raw/"
                + "/".join(quote(part, safe="") for part in file.split("/"))
            )
            if self.headers.get("Turbo-Frame") == "task":
                status, html_ = task_pages.frame_page(ctx)
            else:
                status, html_ = task_pages.task_page(ctx)
        except Exception as error:  # noqa: BLE001 - a page that fails says why, and the server goes on
            return self.broke(workspace, f"task {slug}", error, body=body)
        return self.html(status, html_, body=body)

    def raw(self, workspace: Workspace, slug: str, path: str, *, body: bool) -> None:
        """An HTML artifact of a task, as it is, for the panel's sandboxed frame: only a
        file the task's artifacts list as a page, and under a sandbox of its own, so
        that opened alone it runs as no page of the board's origin."""
        found = (
            lem_artifacts.one(workspace.state / "tasks" / slug, slug, path)
            if path
            else None
        )
        if not found or found[0]["kind"] != "html":
            return self.text(HTTPStatus.NOT_FOUND, "Not found.", body=body)
        try:
            data = found[1].read_bytes()
        except OSError:
            return self.text(HTTPStatus.NOT_FOUND, "Not found.", body=body)
        # a link of the page that opens a tab of its own (the pull request) may leave
        # the sandbox; an in-page link scrolls the frame
        return self.send(
            HTTPStatus.OK,
            data,
            TYPES[".html"],
            body=body,
            headers={
                "Content-Security-Policy": (
                    "sandbox allow-scripts allow-popups allow-popups-to-escape-sandbox"
                )
            },
        )

    def card_page(  # noqa: PLR0913 - over the limit before the limit was set
        self,
        workspace: Workspace,
        slug: str,
        page: str,
        query: str,
        *,
        slashed: bool,
        body: bool,
    ) -> None:
        """A card of the task's session as `lem-ask` built it (`cards/PAGEID.html`), as
        it is, under the card's own policy (`card_policy`), at an address that ends in a
        slash, so that the page's relative `answer` is the card's own route."""
        folder = workspace.state / "tasks" / slug
        try:
            data = (
                lem_cards.html_file(folder, page).read_bytes()
                if lem_cards.card(folder, page) is not None
                else None
            )
        except (lem_cards.CardError, OSError):
            data = None
        if data is None:
            return self.text(
                HTTPStatus.NOT_FOUND,
                "Not found: no card of this task has that page.",
                body=body,
            )
        if not slashed:
            return self.redirect(
                f"/{quote(HOSTNAME)}/{quote(workspace.name)}/tasks/{quote(slug)}"
                f"/cards/{quote(page)}/" + (f"?{query}" if query else ""),
                body=body,
            )
        return self.send(
            HTTPStatus.OK,
            data,
            TYPES[".html"],
            body=body,
            headers={"Content-Security-Policy": card_policy(data)},
        )

    def media(self, workspace: Workspace, slug: str, path: str, *, body: bool) -> None:
        """A picture of the task's media folder, for a document that shows it: a file
        under `media/` with no hidden part, whose extension and first bytes are one
        picture format (`image_type`); anything else, an SVG among them, is
        not found."""
        folder = workspace.state / "tasks" / slug / "media"
        parts = [part for part in path.split("/") if part]
        if not parts or any(part.startswith(".") for part in parts):
            return self.text(HTTPStatus.NOT_FOUND, "Not found.", body=body)
        file = folder.joinpath(*parts)
        try:
            if not file.is_file() or not file.resolve().is_relative_to(
                folder.resolve()
            ):
                return self.text(HTTPStatus.NOT_FOUND, "Not found.", body=body)
            data = file.read_bytes()
        except OSError:
            return self.text(HTTPStatus.NOT_FOUND, "Not found.", body=body)
        kind = lem_artifacts.image_type(file.name, data[:16])
        if kind is None:
            return self.text(
                HTTPStatus.NOT_FOUND,
                (
                    "Not found: the board shows only a PNG, JPEG, GIF or WebP picture "
                    "from a task's media folder."
                ),
                body=body,
            )
        return self.send(
            HTTPStatus.OK,
            data,
            kind,
            body=body,
            headers={
                "Cache-Control": "no-cache",
                "Content-Security-Policy": "default-src 'none'; sandbox",
            },
        )

    def html(self, status: int, text: str, *, body: bool) -> None:
        self.send(status, text.encode("utf-8"), TYPES[".html"], body=body)

    def missing(self, said: str, *, body: bool) -> None:
        self.html(
            HTTPStatus.NOT_FOUND,
            pages.error_page(
                "Not found",
                said,
                asset_link,
                "The list of the workspaces of this machine is at /.",
            ),
            body=body,
        )

    def failed(self, said: str, *, body: bool) -> None:
        self.html(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            pages.error_page(
                "The board failed",
                said,
                asset_link,
                (
                    "The server's log says more: lem serve writes it to "
                    "serve.log in Lem's home folder."
                ),
            ),
            body=body,
        )

    def refreshes(self, workspace: Workspace, query: str) -> None:
        """Server-sent events for the served pages: a Turbo `refresh` each time the
        workspace's log grew or a file the pages read changed (the owner's mark, the
        settings, the Inbox's record), or what the server itself knows changed (an act
        of the board, its look at the forge or at the task sessions: `Workspace.acted`),
        `id:` the version of the log (`bm.log_version`: its inode and its count of
        lines), and a `ping` event after each PING_SECONDS with nothing to say. A page's
        open after a render (`?rendered=ID`) gets a refresh at once when ID is not the
        log's version now (`behind`), also after `lem project prune` replaced the log
        with one of the same count, and an open after the page may have missed a change
        (`?since=ID`, `Last-Event-ID`) gets one at once whatever the log
        (`opens_with_refresh`). The thread ends when its client hung up or the
        server stops."""
        asked = parse_qs(query)
        rendered, since = (
            (asked.get(key) or [None])[0] for key in ("rendered", "since")
        )
        self.send_response(HTTPStatus.OK)
        for key, value in {
            "Content-Type": "text/event-stream; charset=utf-8",
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "same-origin",
            "X-Accel-Buffering": "no",
            "Connection": "close",
        }.items():
            self.send_header(key, value)
        self.end_headers()
        self.close_connection = True
        # the Inbox's record too, which the Inbox thread writes only when a look changed
        # it (lem_inbox), so that a task's page shows the link to its thread, or why
        # there is none, within seconds of the send
        files = {
            "demo": workspace.state / "demo",
            "inbox": workspace.state / bm.INBOX_LOOK,
            "settings": Path(workspace.path) / lem_state.TEAM_SETTINGS,
        }
        task = (asked.get("task") or [""])[0]
        if TASK_SLUG.fullmatch(task) and (workspace.state / "tasks" / task).is_dir():
            files["task"] = workspace.state / "tasks" / task
        backlog = workspace.backlog_folder()
        if backlog is not None:
            files["backlog"] = backlog
        # the reviewer's items, which the reviewer writes and a drop or a landing
        # removes with no line of the log
        files["reviewer"] = workspace.state / lem_project.STATE_BACKLOG
        with contextlib.suppress(lem_state.StateError):
            files["owner"] = lem_state.owner_mark()
        look = Look(workspace.state, files)
        version, _ = look.changes()
        acted = workspace.acted
        try:
            self.wfile.write(
                refresh(version)
                if opens_with_refresh(
                    rendered, since, self.headers.get("Last-Event-ID"), version
                )
                else b": open\n\n"
            )
            quiet = time.monotonic()
            while not STOPPING.wait(WATCH_SECONDS):
                if self.hung_up():
                    return
                version, changed = look.changes()
                # an act of the board that ended, also one that wrote no file (a merge
                # the script refused)
                if workspace.acted != acted:
                    acted, changed = workspace.acted, changed or {}
                if changed is not None:
                    self.wfile.write(refresh(version))
                    quiet = time.monotonic()
                elif time.monotonic() - quiet >= PING_SECONDS:
                    self.wfile.write(ping(version))
                    quiet = time.monotonic()
        except (OSError, ValueError):
            return

    def hung_up(self) -> bool:
        """Whether the client of a stream closed its end. It sends nothing after its
        request, so a socket with something to read holds the end of the stream: a write
        to it would still pass once, and only the ping after it would fail."""
        try:
            if not select.select([self.connection], [], [], 0)[0]:
                return False
            return self.connection.recv(1, socket.MSG_PEEK) == b""
        except (OSError, ValueError):
            return True

    def caching(self, query: str) -> dict:
        """A file whose address carries `?v=` (a hash of its content) is kept for a
        year; any other is asked again each time, with its ETag."""
        return (
            {"Cache-Control": "public, max-age=31536000, immutable"}
            if parse_qs(query).get("v")
            else {"Cache-Control": "no-cache"}
        )


def packed(file: Path, data: bytes) -> bytes:
    """An asset's bytes compressed with gzip, made once for each content."""
    key = (file, hashlib.sha256(data).hexdigest())
    if key not in PACKED:
        PACKED[key] = gzip.compress(data, compresslevel=6, mtime=0)
    return PACKED[key]


# ---- the server's look at the forge ----

# How often, at most, the server asks the forge about one workspace's open pull
# requests. A guess (2026-11-20): a merge on GitHub shows within a few minutes, and a
# call a few minutes stays far under the forge's limits.
FORGE_SECONDS = 180
# How often the thread looks whether a workspace is due: a guess, short
# beside FORGE_SECONDS.
FORGE_TICK = 20
# One call of Lem's scripts at a time from this process: the server's bookkeeping runs
# them in it. A merge is a process of its own and takes no part in it (`merge_apart`).
SCRIPT_LOCK = threading.Lock()
GITHUB_REMOTE = re.compile(r"(https://|ssh://git@|git@)github\.com[:/]")


def open_prs(model: "bm.Model") -> list[dict]:
    """Each task that is `open` with a pull request, as the model has it: its name and
    its number. A task its merge agent's seat blocked counts as open (`failed_seat`):
    its pull request waits for the owner's go on, and a merge on GitHub meanwhile still
    lands it."""
    return [
        {"task": t.slug, "n": int(bm.pr_of(t)["n"]), "url": bm.pr_of(t)["url"]}
        for t in model.tasks
        if (t.status == "open" or t.failed_seat == "merger") and bm.pr_of(t)
    ]


def has_forge(workspace: Workspace, model: "bm.Model") -> bool:
    """Whether the workspace has a forge to ask: no example tasks, and a
    GitHub remote."""
    settings = workspace.settings()
    if model.meta.get("demo") or not settings:
        return False
    url = subprocess.run(
        ["git", "-C", str(settings["main"]), "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return bool(GITHUB_REMOTE.match(url))


def forge_once(workspace: Workspace, now: int | None = None) -> list[dict]:  # noqa: C901, PLR0912, PLR0915 - over the limit before the limit was set
    """One look at the forge for a workspace when it is due
    (`lem_board_model.forge_due`), and the bookkeeping of each pull request the forge
    calls merged or closed, except of a task whose merge this server runs
    (NOTES.running) when the look begins or when its pull request's turn comes: what
    ran, one entry each."""
    now = bm.now_ms() if now is None else now
    # read before the model: a merge that ends during the look at the forge is still
    # left to itself, and one that ended before this line has its landing in the
    # model already
    running = NOTES.running(workspace.name)
    model = workspace.model()
    prs = open_prs(model)
    if not prs:
        workspace.forge["problem"] = None
        return []
    due = bm.forge_due(
        prs,
        workspace.forge["looked"],
        now,
        FORGE_SECONDS * 1000,
        forge=prs and has_forge(workspace, model),
    )
    if not due:
        return []
    workspace.forge["looked"] = now
    # has_forge read these settings for `due`, and a look is due only with a forge
    settings = cast("dict", workspace.settings())
    main = Path(settings["main"])
    if not shutil.which("gh"):
        workspace.forge["problem"] = (
            "the board cannot ask GitHub about the open pull requests: "
            "the `gh` command is not on PATH (install it and run `gh auth login`)"
        )
        return []
    land = lem_sibling.module(SCRIPTS / "land.py")
    try:
        with SCRIPT_LOCK:
            looked = land.forge_look(main, str(settings["branch"]["base"]), due)
    except (land.LandError, ValueError, OSError) as error:
        said = str(error)
        why = (
            "`gh` is not signed in to github.com (`gh auth login` signs it in)"
            if "auth" in said.lower() or "login" in said.lower()
            else said
        )
        workspace.forge["problem"] = (
            f"the board cannot ask GitHub about the open pull requests: {why}"
        )
        return []
    workspace.forge["problem"] = None
    # what the forge says of each open pull request's merge with the base, on which
    # head: the board's conflict mark (`Model.seen`) and the duty of a conflict read it
    seen = {
        pr["task"]: {
            "mergeable": (looked.get(pr["n"]) or {}).get("mergeable"),
            "head": (looked.get(pr["n"]) or {}).get("headRefOid"),
        }
        for pr in prs
    }
    if seen != workspace.forge.get("seen"):
        # an open page shows a conflict that came or went
        workspace.acted += 1
    workspace.forge["seen"] = seen
    keep_forge_look(workspace.state, seen, now)
    ran = []
    # each bookkeeping that failed, by (task, number): when, and its line, which stays
    # the problem until it runs
    failed = workspace.forge.setdefault("failed", {})
    clock = time.monotonic()
    for pr in prs:
        if pr["task"] in running or pr["task"] in NOTES.running(workspace.name):
            # this server runs or ran its merge (`merge_in_thread`), whose process holds
            # the task's step lock or has landed it, so a `merged` now is refused with a
            # false line; the merge's own step records the landing, and a merge that
            # ends without one leaves the task open for the next look
            continue
        state = (looked.get(pr["n"]) or {}).get("state")
        key = (pr["task"], pr["n"])
        if state not in ("MERGED", "CLOSED") or not merged_due(
            key, workspace.forge["done"], failed, clock
        ):
            if key in failed and key not in workspace.forge["done"]:
                workspace.forge["problem"] = failed[key][1]
            continue
        with SCRIPT_LOCK:
            result = lem_sibling.run(SCRIPTS / "land.py", main, "merged", pr["task"])
        said = result.stderr.strip().splitlines()
        if result.returncode == 0:
            try:
                said = [json.loads(result.stdout).get("state") or "landed"]
            except (ValueError, AttributeError):
                said = ["done"]
        ran.append(
            {
                "task": pr["task"],
                "pr": pr["n"],
                "state": state,
                "exit": result.returncode,
                "said": said[-1] if said else "",
            }
        )
        if result.returncode == 0:
            # done only once it ran: a failure is tried again after DUTY_RETRY
            workspace.forge["done"].add(key)
            failed.pop(key, None)
        else:
            line = (
                f"`lem land merged {pr['task']}` failed after GitHub called pull "
                f"request {pr['n']} {state.lower()}: "
                f"{said[-1] if said else 'no output'}; the board tries it "
                "again in a few minutes"
            )
            failed[key] = (clock, line)
            workspace.forge["problem"] = line
    return ran


def merged_due(key: tuple, done: set, failed: dict, clock: float) -> bool:
    """Whether the server runs `lem land merged` for a pull request the forge called
    merged or closed now: not once it ran (DONE), and not within DUTY_RETRY of a failed
    try (FAILED, by key: its time on CLOCK's scale and its line)."""
    return key not in done and (
        key not in failed or clock - failed[key][0] >= DUTY_RETRY
    )


def keep_forge_look(state: Path, seen: dict, now: int) -> None:
    """Write the forge's last look into the state folder (bm.FORGE_LOOK), whole, through
    a temporary file and a rename, so that the board's model and `lem project waiting`
    read what the server saw. A write that fails is a line in the server's log: the
    server's own look still holds in memory."""
    file = state / bm.FORGE_LOOK
    looked = datetime.fromtimestamp(now / 1000, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    temporary = file.with_name(f".{file.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps({"looked": looked, "seen": seen}, indent=1) + "\n",
            encoding="utf-8",
        )
        temporary.replace(file)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        sys.stderr.write(
            f"serve.py: the forge's look was not written to {file}: {error}\n"
        )


# ---- the server's duties across tasks ----

# How long a duty whose command failed waits before the server tries it again. A guess
# (2026-11-21): long beside a tick, so a missing agterm does not run a command every
# FORGE_TICK, and short beside the owner's day; the board's "no session" row tells
# him meanwhile.
DUTY_RETRY = 300
# The first line of the state with which `lem land merged` ends a task whose pull
# request was closed on the forge.
CLOSED_ON_FORGE = "the pull request was closed on the forge"


def same_head(head: object, tip: object) -> bool:
    """A head the forge names and a tip Lem proposed are one commit, whichever is
    the shorter."""
    return bool(head and tip) and (
        str(head).startswith(str(tip)) or str(tip).startswith(str(head))
    )


def run_start(t: "bm.Task") -> int:
    """The place in the task's events of the first block of the status it has now."""
    i = len(t.blocks) - 1
    while i > 0 and t.blocks[i - 1]["status"] == t.status:
        i -= 1
    return t.blocks[i]["order"]


def wait_start(t: "bm.Task") -> int:
    """The place in a queued task's events of the first block of its wait now: the run
    of `queued` blocks with the `after:` line of the newest one. A queued block behind
    another task starts a new wait, so a session opened or woken for the wait before it
    does not count for this one."""

    def after(block: dict) -> list[str]:
        return [line for line in bm.lines_of(block) if line.startswith("after: ")]

    i = len(t.blocks) - 1
    while (
        i > 0
        and t.blocks[i - 1]["status"] == "queued"
        and after(t.blocks[i - 1]) == after(t.blocks[i])
    ):
        i -= 1
    return t.blocks[i]["order"]


def duties(  # noqa: C901, PLR0912 - over the limit before the limit was set
    model: "bm.Model",
    seen: dict,
    kept: set,
    merging: set[str] | frozenset[str] = frozenset(),
) -> list[tuple[str, str, str]]:
    """What the server owes the tasks of a workspace now, each `(VERB, SLUG, WHY)` for
    `lem session VERB SLUG --why WHY`, or `("merge", SLUG, "merger")` for the merge
    agent's merge, read from the files and the forge's last look (`seen`, by task)
    alone, so that a pause of the server loses nothing; MERGING names the tasks whose
    merge this server runs. Never for a demo workspace.

    - `wake … merged`: a task the merge ended (`landed`, or `dropped` because its pull
      request was closed on the forge) whose worktree is still there (`kept`), and no
      session was woken or opened since.
    - `wake … conflict`: an open task whose pull request the forge calls conflicting on
      the head Lem proposed last, and no session was woken or opened for a conflict
      since that proposal: one wake for each head.
    - `open … queue`: a queued task whose `after:` task ended, that has no live session
      (`Model.sessions`, so never while the server does not know) and no session opened
      since its wait began (`wait_start`: a task queued again behind another task
      waits anew).
    - `wake … queue`: the same task whose session still lives (the one its ask was typed
      in, which the owner may keep selected, so that its close never comes), when no
      session was woken or opened since its wait began: one wake.
    - `merge … owner`: an open task for whose tip Lem proposed last the owner's merge
      stands, after a moved base refused it and a read of the moved base said `safe` (or
      a read on the checks' own base after a revert answered the refusal), or the
      session landed the task again with the same change and the same reasons
      (`merge.stands`, `stands_due`): `lem land merge SLUG --by owner --via
      server --standing`.
    - `merge … merger`: an open task whose merge agent's review of the tip Lem proposed
      last says `merge` and calls nobody (`merge_due`), also one that `propose` carried
      onto that tip, and one whose read of a moved base said `safe` after Lem refused
      the merge because the base moved; never one whose read said `another round`, which
      the session lands again. land.py's own refusals stay the gate: the server only
      runs it.
    - `wake … refused`: an open task whose merge was refused on the tip Lem proposed
      last, and no session was woken or opened since the refusal: the merge agent's, by
      GitHub or by Lem's rules, and the owner's when Lem refused it because the base
      moved (`kind: base`, `refusal_of`).
    - `wake … status`: a task in `building`, `ready` or `landing` whose live session
      showed no sign of work for 45 minutes (`bm.stop_due`), or, when its signs do not
      read, no event of the task for 45 minutes: the line that asks the session where
      the task stands.
    - `open … stopped`: the same task 10 minutes after that line with still no sign of
      work, when its signs read, Lem did not restart it since its newest work event and
      no stop of it stands: a fresh session beside the old pane.
    - `stopped … stopped`: the same once the restart was spent, or at once when its
      signs do not read: `lem session stopped SLUG` logs the stop, once, and the owner's
      "Waits for you" shows it.
    Each of the three names the session it is for (`--session`), and `lem session` looks
    once more in the task's lock before it acts: a sign of work since, a status that
    changed, a session that is gone, or a restart beside signs that do not read or over
    a standing stop make it act on nothing (`acted: false`), and the next look
    asks again."""
    if model.meta.get("demo"):
        return []
    out = []
    for t in model.tasks:
        ended = t.status == "landed" or (
            t.status == "dropped" and t.text.startswith(CLOSED_ON_FORGE)
        )
        if ended and t.slug in kept:
            since = run_start(t)
            if not any(w["order"] > since for w in t.wakes) and not (
                t.opened and t.opened["order"] > since
            ):
                out.append(("wake", t.slug, "merged"))
        elif t.status == "open" and t.proposal:
            look = seen.get(t.slug) or {}
            since = t.proposal["order"]
            woke = any(
                w["order"] > since and w.get("why") in ("conflict", None)
                for w in t.wakes
            ) or bool(
                t.opened
                and t.opened["order"] > since
                and t.opened.get("why") == "conflict"
            )
            if (
                look.get("mergeable") == "CONFLICTING"
                and same_head(look.get("head"), t.proposal.get("tip"))
                and not woke
            ):
                out.append(("wake", t.slug, "conflict"))
            elif stands_due(t, seen, merging):
                out.append(("merge", t.slug, "owner"))
            elif merge_due(t, seen, merging):
                out.append(("merge", t.slug, "merger"))
            elif t.refused and (
                t.refused.get("by") == "merger"
                or (
                    refusal_of(t).get("from") == "lem"
                    and refusal_of(t).get("kind") == "base"
                )
            ):
                after = t.refused["order"]
                if not any(w["order"] > after for w in t.wakes) and not (
                    t.opened and t.opened["order"] > after
                ):
                    out.append(("wake", t.slug, "refused"))
        elif (due := bm.stop_due(t, model)) is not None:
            out.append(STOP_DUTIES[due["step"]](t.slug))
        elif (
            t.status == "queued"
            and bm.after_ended(t, model)
            and model.sessions is not None
        ):
            live = bm.live_of(t, model) or {}
            since = wait_start(t)
            if t.opened and t.opened["order"] > since:
                continue
            if not live.get("live"):
                out.append(("open", t.slug, "queue"))
            elif not any(w["order"] > since for w in t.wakes):
                # the session the ask was typed in lives on: the owner may keep it
                # selected, so its close never comes and nothing else would start
                # the task
                out.append(("wake", t.slug, "queue"))
    return out


# The duty of each step of the guard of a stopped session (`bm.stop_due`),
# as `(VERB, SLUG, WHY)`.
STOP_DUTIES = {
    "status": lambda slug: ("wake", slug, "status"),
    "restart": lambda slug: ("open", slug, "stopped"),
    "stopped": lambda slug: ("stopped", slug, "stopped"),
}


def merge_due(t: "bm.Task", seen: dict, merging: set[str] | frozenset[str]) -> bool:
    """Whether the server runs the merge agent's merge of an open task now: the merge
    agent's review is of the tip Lem proposed last, says `merge`, calls nobody and does
    not say `another round` of a moved base (the task's session lands it again); no
    merge of that tip was refused, or the refusal was Lem's because the base moved and a
    read of the moved base that said `safe`, or a read on the checks' own base after a
    revert, answered it (`bm.answers_refusal`; a new proposal, and its new review, make
    a new try); the forge does not call it conflicting (its session brings it onto the
    base first); and this server runs no merge of it (MERGING)."""
    review = t.merge_review
    return bool(
        t.status == "open"
        and t.proposal
        and review
        and review.get("verdict") == "merge"
        and not review.get("calls")
        and review.get("base_call") != "another round"
        and same_head(review.get("tip"), t.proposal.get("tip"))
        and not t.refused
        and not bm.conflicts(t, seen)
        and t.slug not in merging
    )


def since_proposal(t: "bm.Task") -> list[dict]:
    """The task's events after its newest proposal, oldest first; [] with none."""
    return t.events[t.proposal["order"] :] if t.proposal else []


def refusal_of(t: "bm.Task") -> dict:
    """The newest refusal of a merge of the tip Lem proposed last, as its
    `merge.refused` event has it (`by`, `via`, `from`, and for Lem's own `kind`),
    or {}."""
    return next(
        (e for e in reversed(since_proposal(t)) if e.get("event") == "merge.refused"),
        {},
    )


def stands_due(t: "bm.Task", seen: dict, merging: set[str] | frozenset[str]) -> bool:
    """Whether the server runs the owner's merge that a moved base refused now:
    `merge.stands` is logged for the tip Lem proposed last, by `propose` after a new
    landing or by the record of a read that answered Lem's refusal because the base
    moved (a read of the moved base that said `safe`, or a read on the checks' own base
    after a revert); no merge of that tip was refused since, or such a read answered
    that refusal (`bm.answers_refusal`); the newest review of that tip does not say
    `another round` (the task's session lands it again); the forge does not call it
    conflicting; and this server runs no merge of it (MERGING)."""
    tip = (t.proposal or {}).get("tip")
    review = t.merge_review or {}
    again = (
        same_head(review.get("tip"), tip) and review.get("base_call") == "another round"
    )
    return bool(
        t.status == "open"
        and t.proposal
        and not t.refused
        and not again
        and not bm.conflicts(t, seen)
        and t.slug not in merging
        and any(
            e.get("event") == "merge.stands" and same_head(e.get("tip"), tip)
            for e in since_proposal(t)
        )
    )


def duty_key(verb: str, slug: str, why: str, landing: dict) -> tuple:
    """What a failed duty waits DUTY_RETRY under. A merge is of one proposed tip and of
    the newest merge review of it (its `at` in `landing.json`), so its wait is that
    read's: a task that landed again after a refused merge is merged at the next look,
    not after the old tip's wait (lem-scratch, 2026-11-21: a carried review waited 4
    minutes for its merge), and so is the merge after a new read of a moved base that
    said `safe`, which answers the refusal of the read before it."""
    if verb != "merge":
        return (verb, slug, why)
    proposed = str(landing.get("proposed") or "")
    review = (
        landing.get("merge_review")
        if isinstance(landing.get("merge_review"), dict)
        else {}
    )
    read = (
        str(review.get("at") or "")
        if proposed and review.get("tip") == proposed
        else ""
    )
    return (verb, slug, why, proposed, read)


def duty_args(
    verb: str, slug: str, why: str, seen: dict, model: "bm.Model"
) -> list[str]:
    """The words of `lem session` for one duty. A conflict's wake keeps the head the
    forge named on its record (`session.wake`), one wake for each head. A step of the
    guard of a stopped session names the session it is for, the one `lem session list`
    gave (`Model.sessions`), so that the act refuses another one; the stop is
    `lem session stopped SLUG`, which has no why."""
    head = (seen.get(slug) or {}).get("head") if why == "conflict" else None
    named = (
        ((model.sessions or {}).get(slug) or {}).get("session")
        if why in ("status", "stopped")
        else None
    )
    words = [verb, slug] + ([] if verb == "stopped" else ["--why", why])
    return (
        words
        + (["--head", str(head)] if head else [])
        + (["--session", str(named)] if named else [])
    )


def run_duties(workspace: Workspace, now: float | None = None) -> list[dict]:
    """Run each duty the workspace has now (`duties`), one command at a time, and what
    ran: a duty whose command failed waits DUTY_RETRY before the next try. The merge
    agent's merge starts in a thread of its own (`merge_in_thread`, as the owner's merge
    from the board), so a merge that waits for the base branch and the forge holds up no
    other duty. The server never types into a session, never selects one and never
    closes one: `lem session wake` sends a pane message, and `lem session open` opens
    one with no focus."""
    now = time.monotonic() if now is None else now
    model = workspace.model()
    seen = workspace.forge.get("seen") or {}
    ran: list[dict] = []
    for verb, slug, why in duties(
        model, seen, workspace.kept, NOTES.running(workspace.name)
    ):
        key = duty_key(
            verb, slug, why, workspace.landing_of(slug) if verb == "merge" else {}
        )
        if key in workspace.failed and now - workspace.failed[key] < DUTY_RETRY:
            continue
        if verb == "merge":

            def failed(key: tuple = key) -> None:
                # a refusal land.py kept ends the duty for that tip; any other end
                # waits DUTY_RETRY
                workspace.failed[key] = time.monotonic()

            # `why` is who merges: the merge agent, or the owner whose merge stood
            # through a new landing or a safe read of the moved base
            landing = workspace.landing_of(slug)
            merge_in_thread(
                workspace,
                slug,
                landing,
                why,
                merge_tip_of(landing, why),
                failed=failed,
                standing=why == "owner",
            )
            ran.append(
                {
                    "verb": verb,
                    "task": slug,
                    "why": why,
                    "exit": None,
                    "said": "started",
                }
            )
            continue
        words = duty_args(verb, slug, why, seen, model)
        result = session_run(workspace, *words)
        if result.returncode == 0:
            workspace.failed.pop(key, None)
        else:
            workspace.failed[key] = now
        ran.append(
            {
                "verb": verb,
                "task": slug,
                "why": why,
                "words": words,
                "exit": result.returncode,
                "said": said_of(result) if result.returncode else not_acted(result),
            }
        )
    return ran


def not_acted(ran: subprocess.CompletedProcess) -> str:
    """What a step of the guard of a stopped session said when it acted on nothing
    (`acted: false`, exit 0: its look once more in the task's lock found a reason),
    else ""."""
    try:
        said = json.loads(ran.stdout)
    except ValueError:
        return ""
    return (
        str(said.get("say") or said.get("why") or "")
        if isinstance(said, dict) and said.get("acted") is False
        else ""
    )


# How often the server runs `lem project prune` for one workspace. A guess (2026-11-21):
# the number it keeps is in days, so an hour late costs nothing, and a run reads the
# event log and walks the ended tasks' folders, which is quick beside an hour.
PRUNE_SECONDS = 3600


def prune_once(workspace: Workspace, now: float | None = None) -> dict | None:
    """`lem project prune` for the workspace when it is due: at the server's first look,
    then each PRUNE_SECONDS. None when it did not run: not due, a workspace of example
    tasks, or settings that do not read (the board says so already). Else its exit, its
    own line, the files, folders, bytes and events it removed or replaced, and what it
    skipped and failed."""
    now = time.monotonic() if now is None else now
    if workspace.pruned is not None and now - workspace.pruned < PRUNE_SECONDS:
        return None
    if workspace.model().meta.get("demo") or not workspace.settings():
        return None
    workspace.pruned = now
    ran = lem_run(workspace, "project.py", "prune")
    try:
        answer = json.loads(ran.stdout)
    except ValueError:
        return {
            "exit": ran.returncode or 1,
            "said": said_of(ran),
            "skipped": [],
            "failed": [],
        }
    return {
        "exit": ran.returncode,
        "said": answer.get("said") or said_of(ran),
        "files": answer.get("files", 0),
        "folders": len(answer.get("folders") or []),
        "bytes": answer.get("bytes", 0),
        "events": answer.get("events", 0),
        "skipped": answer.get("skipped") or [],
        "failed": answer.get("failed") or [],
    }


def prune_line(name: str, ran: dict) -> str | None:
    """The server's log line for a run of `prune`: none when it removed, summarized,
    skipped and failed nothing. A removed file counts when it was empty too, so a run of
    0 bytes may have a line."""
    if (
        ran["exit"] == 0
        and not ran.get("files")
        and not ran.get("folders")
        and not ran.get("bytes")
        and not ran.get("events")
        and not ran["skipped"]
        and not ran["failed"]
    ):
        return None
    parts = [
        f"serve.py: {name}: `lem project prune` exited {ran['exit']}: {ran['said']}"
    ]
    parts += [f"skipped {one['path']}: {one['why']}" for one in ran["skipped"]]
    parts += [f"failed {one['path']}: {one['error']}" for one in ran["failed"]]
    return "; ".join(parts) + "\n"


def forge_loop(machine: "Machine") -> None:
    """The server's thread, until the server stops: at each FORGE_TICK, for each
    workspace, its look at the forge (`forge_once`), its look at the task sessions
    (`Workspace.look_sessions`), and its duties (`run_duties`), each failure one line in
    the server's log and the others still looked at."""
    while not STOPPING.wait(FORGE_TICK):
        for workspace in machine.workspaces():
            try:
                for one in forge_once(workspace):
                    sys.stderr.write(
                        f"serve.py: {workspace.name}: pull request {one['pr']} of "
                        f"{one['task']} is {one['state'].lower()} on GitHub; "
                        f"`lem land merged {one['task']}` exited {one['exit']}: "
                        f"{one['said']}\n"
                    )
            except Exception as error:  # noqa: BLE001 - one workspace that fails says why, and the others are still looked at
                workspace.forge["problem"] = (
                    f"the board's look at GitHub failed: {error!r}"
                )
            try:
                workspace.look_sessions()
                for one in run_duties(workspace):
                    if one["verb"] == "merge":
                        owner = one["why"] == "owner"
                        sys.stderr.write(
                            (
                                f"serve.py: {workspace.name}: `lem land merge "
                                f"{one['task']} --by {one['why']} --via "
                                f"server{' --standing' if owner else ''}` started, "
                            )
                            + (
                                (
                                    "after the owner's merge stood through a new "
                                    "landing or a safe read of the moved base\n"
                                )
                                if owner
                                else "after the merge agent's verdict `merge`\n"
                            )
                        )
                        continue
                    sys.stderr.write(
                        f"serve.py: {workspace.name}: "
                        f"`lem session {' '.join(one['words'])}` exited "
                        f"{one['exit']}{': ' + one['said'] if one['said'] else ''}\n"
                    )
            except Exception as error:  # noqa: BLE001 - as above: one workspace that fails says why
                workspace.session_problem = (
                    f"the board's look at the task sessions failed: {error!r}"
                )
            try:
                ran = prune_once(workspace)
                line = prune_line(workspace.name, ran) if ran else None
                if line:
                    sys.stderr.write(line)
            except Exception as error:  # noqa: BLE001 - as above: one workspace that fails says why
                sys.stderr.write(
                    f"serve.py: {workspace.name}: `lem project prune` failed: "
                    f"{error!r}\n"
                )


def checkout_of(directory: str) -> Path:
    try:
        return lem_state.main_checkout(Path(directory))
    except lem_state.StateError as error:
        raise ServeError(str(error)) from error


def address(host: str, port: int) -> tuple[int, tuple]:
    try:
        found = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as error:
        raise ServeError(
            f"--host {host} does not resolve to an address of this machine "
            f"({error.strerror}): name an address of it"
        ) from error
    family, _, _, _, where = found[0]
    return family, where


def bind(host: str, port: int, handler: type, flag: str) -> ThreadingHTTPServer:
    """A server on HOST:PORT that answers each request in a thread of its own and, when
    it closes, waits for the requests in flight."""
    family, where = address(host, port)

    class Server(ThreadingHTTPServer):
        address_family = family
        daemon_threads = False
        block_on_close = True

    try:
        return Server(where[:2] if family == socket.AF_INET else where, handler)
    except OSError as error:
        if error.errno == errno.EADDRINUSE:
            raise ServeError(
                f"port {port} on {host} is in use: another `lem serve` runs "
                "(`lem serve --stop` ends it), or another program; name a free one "
                f"with `lem serve {flag} N`"
            ) from error
        raise ServeError(
            f"cannot listen on {host}:{port} ({error.strerror}): name an address of "
            f"this machine with --host, or another port with {flag}"
        ) from error


# What the tailnet door says when it cannot start: the Mac itself is still served
# without it.
STILL_LOCAL = "plain `lem serve`, with no --tailscale, still serves this Mac"


def tailscale_cli() -> str | None:
    """The tailscale CLI by its absolute path: the one on PATH, else the first
    of TAILSCALE_PLACES."""
    found = shutil.which("tailscale")
    if found:
        return os.path.abspath(found)  # noqa: PTH100 - Path.absolute keeps `..`, which abspath folds, and the path shows in a failure's message
    return next(
        (
            place
            for place in TAILSCALE_PLACES
            if Path(place).is_file() and os.access(place, os.X_OK)
        ),
        None,
    )


def need_cli() -> str:
    cli = tailscale_cli()
    if cli is None:
        raise ServeError(
            "no tailscale CLI on this Mac (not on PATH, nor at "
            f"{', '.join(TAILSCALE_PLACES)}): install Tailscale from "
            "https://tailscale.com/download on this Mac and on the phone, and sign "
            f"both in with the owner's account; {STILL_LOCAL}"
        )
    return cli


def tailscale_json(
    cli: str, args: list[str], timeout: float = TAILSCALE_TIMEOUT
) -> dict:
    """What `tailscale ARGS` prints, read as JSON; an empty answer is an
    empty object."""
    said = f"`tailscale {' '.join(args)}`"
    try:
        ran = subprocess.run(
            [cli, *args], capture_output=True, text=True, check=False, timeout=timeout
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ServeError(
            f"{said} did not run ({error}): start the Tailscale app, "
            f"then try again; {STILL_LOCAL}"
        ) from error
    if ran.returncode != 0:
        raise ServeError(
            f"{said} failed: {(ran.stderr or ran.stdout).strip()}; start the Tailscale "
            f"app and connect, then try again; {STILL_LOCAL}"
        )
    try:
        data = json.loads(ran.stdout) if ran.stdout.strip() else {}
    except ValueError as error:
        raise ServeError(f"{said} printed no JSON ({error}); {STILL_LOCAL}") from error
    if not isinstance(data, dict):
        raise ServeError(f"{said} printed JSON of another shape; {STILL_LOCAL}")
    return data


def tailnet(cli: str, *, strict: bool = True) -> dict:
    """This Mac on the tailnet: its served name (`Self.DNSName`) and the owner's login
    (`Self.UserID` in `User`). With `strict`, also what the door needs: a connected
    backend, a node that a person owns (no tag) and HTTPS certificates."""
    status = tailscale_json(cli, ["status", "--json"])
    state = status.get("BackendState")
    if state != "Running":
        raise ServeError(
            f"Tailscale is not connected on this Mac (its state is {state}): "
            f"open Tailscale and connect, then try again; {STILL_LOCAL}"
        )
    me = status.get("Self") if isinstance(status.get("Self"), dict) else {}
    if strict and me.get("Tags"):
        raise ServeError(
            "this Mac is a tagged node of the tailnet, so no person owns it and "
            "Tailscale sends no login for the door to check: sign this Mac in to "
            f"Tailscale with the owner's own account; {STILL_LOCAL}"
        )
    if strict and not status.get("CertDomains"):
        raise ServeError(
            "HTTPS certificates are off for this tailnet: turn on MagicDNS and HTTPS "
            "in the Tailscale admin console "
            "(https://tailscale.com/kb/1153/enabling-https), "
            f"then try again; {STILL_LOCAL}"
        )
    users = status.get("User") if isinstance(status.get("User"), dict) else {}
    user = users.get(str(me.get("UserID")))
    name = str(me.get("DNSName") or "").rstrip(".")
    login = user.get("LoginName") if isinstance(user, dict) else None
    if not name or not isinstance(login, str) or not login:
        raise ServeError(
            "`tailscale status --json` names no DNS name or no login for this Mac: "
            f"sign it in to Tailscale with the owner's account; {STILL_LOCAL}"
        )
    return {"name": name, "login": login}


def names_of(tailnet_name: str | None) -> tuple[str, tuple[str, ...]]:
    """The machine's name in every address and its other name, from its name on the
    tailnet (the DNS name Tailscale gives it, or None where Tailscale does not run): the
    tailnet's first label when there is one, with the short host name as the other; else
    the short host name alone."""
    first = host_word(tailnet_name.split(".")[0]) if tailnet_name else ""
    if not first:
        return SHORT_NAME, ()
    return first, (() if first == SHORT_NAME else (SHORT_NAME,))


def machine_names(tailnet_name: str | None = None) -> tuple[str, tuple[str, ...]]:
    """The machine's names (`names_of`), from the name Tailscale gives it: TAILNET_NAME
    when the caller read it already, else `tailscale status --json` asked once, within
    NAME_TIMEOUT. A machine with no Tailscale, or whose Tailscale is not connected, has
    its short host name."""
    if tailnet_name is None:
        cli = tailscale_cli()
        if cli is not None:
            try:
                status = tailscale_json(cli, ["status", "--json"], timeout=NAME_TIMEOUT)
            except ServeError:
                status = {}
            me = status.get("Self") if isinstance(status.get("Self"), dict) else {}
            if status.get("BackendState") == "Running" and isinstance(
                me.get("DNSName"), str
            ):
                tailnet_name = me["DNSName"].rstrip(".")
    return names_of(tailnet_name)


def settle_names(tailnet_name: str | None = None) -> None:
    """Set the machine's names of this process (HOSTNAME, ALIASES) once; a test names
    the machine itself (`lem_peers.NAME_SWITCH`), so that two servers on one Mac are
    two machines."""
    global HOSTNAME, ALIASES
    try:
        named = lem_peers.test_name()
    except lem_peers.PeerError as error:
        raise ServeError(str(error)) from error
    HOSTNAME, ALIASES = (named, ()) if named else machine_names(tailnet_name)


def tailnet_status() -> dict:
    """`tailscale status --json`, for the peers: the tailnet's suffix and
    its machines."""
    return tailscale_json(need_cli(), ["status", "--json"], timeout=NAME_TIMEOUT)


def door_address(port: int) -> str:
    return f"http://{HOST}:{port}"


def served_target(cli: str, name: str, port: int) -> tuple[bool, str | None, bool]:
    """Port PORT of this Mac on the tailnet, from `tailscale serve status --json`:
    whether an entry holds it, the one target its `/` proxies to (None when it serves
    anything else), and whether Funnel is on for it."""
    status = tailscale_json(cli, ["serve", "status", "--json"])
    tcp = status.get("TCP") if isinstance(status.get("TCP"), dict) else {}
    web = status.get("Web") if isinstance(status.get("Web"), dict) else {}
    funnel = (
        status.get("AllowFunnel") if isinstance(status.get("AllowFunnel"), dict) else {}
    )
    site = web.get(f"{name}:{port}")
    site = site if isinstance(site, dict) else {}
    handlers = site.get("Handlers") if isinstance(site.get("Handlers"), dict) else {}
    root = (
        handlers.get("/")
        if len(handlers) == 1 and isinstance(handlers.get("/"), dict)
        else {}
    )
    target = root.get("Proxy") if isinstance(root.get("Proxy"), str) else None
    return (
        str(port) in tcp or bool(handlers),
        (target.rstrip("/") if target else None),
        bool(funnel.get(f"{name}:{port}")),
    )


def publish(cli: str, name: str, port: int) -> str:
    """Put the tailnet's HTTPS port PORT in front of the door: `kept` when it is there
    already, `published` when this call put it there. A port another target holds is
    refused, never taken."""
    door = door_address(port)
    held, target, funnel = served_target(cli, name, port)
    if funnel:
        raise ServeError(
            f"Tailscale Funnel is on for port {port}, which would put the board on the "
            f"internet: `tailscale funnel --https={port} off` turns it off, or name "
            "another port with --tailscale-port"
        )
    if held and target == door:
        return "kept"
    if held:
        raise ServeError(
            f"port {port} of this Mac on the tailnet already serves "
            f"{target or 'another target'}, and Lem never takes a port from another "
            "entry: name a free one with --tailscale-port (`tailscale serve status` "
            "lists the ports in use)"
        )
    try:
        ran = subprocess.run(
            [cli, "serve", "--bg", f"--https={port}", door],
            capture_output=True,
            text=True,
            check=False,
            timeout=TAILSCALE_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ServeError(
            f"`tailscale serve --bg --https={port} {door}` did not "
            f"run ({error}); {STILL_LOCAL}"
        ) from error
    held, target, _ = served_target(cli, name, port)
    if ran.returncode != 0 or target != door:
        raise ServeError(
            f"`tailscale serve --bg --https={port} {door}` did not put the door on the "
            "tailnet: "
            f"{(ran.stderr or ran.stdout).strip() or 'the entry is not there'}; "
            f"{STILL_LOCAL}"
        )
    return "published"


def tailscale_off(port: int) -> dict:
    """Take Lem's entry for PORT out of `tailscale serve`, only when it points at
    Lem's door."""
    cli = need_cli()
    name = tailnet(cli, strict=False)["name"]
    door = door_address(port)
    held, target, _ = served_target(cli, name, port)
    if not held:
        return {
            "removed": False,
            "port": port,
            "said": (
                f"port {port} of this Mac on the tailnet serves nothing; "
                "there is nothing of Lem's to take out"
            ),
        }
    if target != door:
        raise ServeError(
            f"port {port} of this Mac on the tailnet serves "
            f"{target or 'another target'}, not Lem's door ({door}): "
            "Lem leaves another entry as it is; name Lem's port with --tailscale-port"
        )
    try:
        ran = subprocess.run(
            [cli, "serve", f"--https={port}", "off"],
            capture_output=True,
            text=True,
            check=False,
            timeout=TAILSCALE_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ServeError(
            f"`tailscale serve --https={port} off` did not run ({error}): "
            "run it by hand"
        ) from error
    if ran.returncode != 0 or served_target(cli, name, port)[0]:
        raise ServeError(
            f"`tailscale serve --https={port} off` did not take the entry out: "
            f"{(ran.stderr or ran.stdout).strip()}; run it by hand"
        )
    return {"removed": True, "port": port, "url": f"https://{name}:{port}/"}


def git_commit(root: Path) -> str | None:  # noqa: C901, PLR0911 - over the limit before the limit was set
    """The commit the checkout at `root` is on, read from its git files with no git
    command (a worktree's `.git` file, a ref in the common folder, `packed-refs`); None
    when it reads no commit."""
    try:
        dot = root / ".git"
        if dot.is_file():
            text = dot.read_text(encoding="utf-8").strip()
            if not text.startswith("gitdir:"):
                return None
            gitdir = (root / text.removeprefix("gitdir:").strip()).resolve()
        elif dot.is_dir():
            gitdir = dot
        else:
            return None
        head = (gitdir / "HEAD").read_text(encoding="utf-8").strip()
        if not head.startswith("ref:"):
            return head or None
        ref = head.removeprefix("ref:").strip()
        common = gitdir
        if (gitdir / "commondir").is_file():
            common = (
                gitdir / (gitdir / "commondir").read_text(encoding="utf-8").strip()
            ).resolve()
        for place in (gitdir, common):
            if (place / ref).is_file():
                return (place / ref).read_text(encoding="utf-8").strip() or None
        if (common / "packed-refs").is_file():
            for line in (
                (common / "packed-refs").read_text(encoding="utf-8").splitlines()
            ):
                parts = line.split()
                if (
                    len(parts) == 2  # noqa: PLR2004 - a line of packed-refs is a commit and a ref
                    and parts[1] == ref
                    and not line.startswith(("#", "^"))
                ):
                    return parts[0]
    except OSError:
        return None
    return None


def code_version(root: Path = LEM_ROOT) -> str:
    """The identity of the code in the folder of Lem `root`: the plugin's version when
    its manifest names one, else the commit of the folder, else the newest change time
    of its scripts."""
    try:
        manifest = json.loads(
            (root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        manifest = {}
    named = manifest.get("version") if isinstance(manifest, dict) else None
    if isinstance(named, str) and named.strip():
        return f"version {named.strip()}"
    commit = git_commit(root)
    if commit:
        return f"commit {commit[:12]}"
    return f"files {code_stamp(root)}"


def code_stamp(root: Path = LEM_ROOT) -> int:
    """The newest change time of the scripts in the folder of Lem `root`, in ns: of two
    codes, the newer one has the larger stamp, as an update writes its files anew."""
    return max(
        (
            file.stat().st_mtime_ns
            for file in (root / "skills" / "lem" / "scripts").glob("*.py")
        ),
        default=0,
    )


def serve_settings() -> dict:
    """How the server runs on this machine: `[serve]` of the machine's file, with
    the defaults."""
    table = lem_state.machine_table("serve")
    settings = {
        "tailscale": table.get("tailscale", False),
        "port": table.get("port", PORT),
        "tailscale_port": table.get("tailscale_port", TAILNET_PORT),
    }
    for key, flag in (("port", "--port"), ("tailscale_port", "--tailscale-port")):
        if not 0 < settings[key] < PORT_LIMIT:
            raise ServeError(
                f"serve.{key} in {lem_state.machine_file()} is {settings[key]}, which "
                f"is no port: `lem serve {flag} N` writes one from 1 to 65535"
            )
    if settings["tailscale"] and settings["port"] == settings["tailscale_port"]:
        raise ServeError(
            f"serve.port and serve.tailscale_port in {lem_state.machine_file()} are "
            f"both {settings['port']}: the door needs a port of its own; "
            "`lem serve --tailscale-port N` writes another"
        )
    return settings


def reach(
    request: str | urllib.request.Request, timeout: float
) -> http.client.HTTPResponse:
    """Open a request to this machine's own server, past any proxy of
    the environment."""
    return urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
        request, timeout=timeout
    )


def nobody_listens(error: Exception) -> bool:
    """Whether a failed request found nothing that listens."""
    reason = getattr(error, "reason", error)
    return (
        isinstance(reason, ConnectionRefusedError)
        or getattr(reason, "errno", None) == errno.ECONNREFUSED
    )


def ask(port: int, timeout: float = ASK_TIMEOUT) -> dict | None:
    """Who serves the main port: the running server's own facts (`GET /api/server`), or
    None when nothing listens there. A port that answers as no `lem serve` of this home
    folder is refused, with the flag that names another port."""
    where = f"http://{HOST}:{port}/api/server"
    fix = "or name a free port with `lem serve --port N`"
    try:
        with reach(where, timeout) as reply:
            text, server = reply.read(65536), reply.headers.get("Server") or ""
    except urllib.error.HTTPError as error:
        raise ServeError(
            f"port {port} on {HOST} is held by another program, which answered {where} "
            f"with {error.code} ({error.headers.get('Server') or 'no Server header'}): "
            f"end it, {fix}"
        ) from error
    except (urllib.error.URLError, OSError) as error:
        if nobody_listens(error):
            return None
        raise ServeError(
            f"port {port} on {HOST} takes connections and gave no answer in "
            f"{timeout:g} s ({getattr(error, 'reason', error)}): end the program that "
            f"holds it (`lsof -nP -iTCP:{port} -sTCP:LISTEN` names it), {fix}"
        ) from error
    try:
        facts = json.loads(text)
    except ValueError:
        facts = None
    if (
        not server.startswith(Handler.server_version)
        or not isinstance(facts, dict)
        or not isinstance(facts.get("pid"), int)
        or not isinstance(facts.get("version"), str)
    ):
        raise ServeError(
            f"port {port} on {HOST} is held by another program "
            f"({server or 'no Server header'}), which does not answer {where} as Lem's "
            f"server: end it (`lsof -nP -iTCP:{port} -sTCP:LISTEN` names it), {fix}"
        )
    if facts.get("config") != str(lem_state.config()):
        raise ServeError(
            f"port {port} on {HOST} is held by the `lem serve` (pid {facts['pid']}) of "
            f"another home folder of Lem, {facts.get('config')}, and this one is "
            f"{lem_state.config()}: end it with `kill {facts['pid']}`, {fix}"
        )
    return facts


@contextlib.contextmanager
def start_lock() -> Generator[None, None, None]:
    """Hold SERVE_LOCK, so that two starts at one moment make one server; wait for
    another's at most as long as its stop and its start may take."""
    home = lem_state.config()
    home.mkdir(parents=True, exist_ok=True)
    path = home / SERVE_LOCK
    with path.open("a") as handle:
        deadline = time.monotonic() + START_WAIT + STOP_WAIT
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() > deadline:
                    raise ServeError(
                        f"another start of the server holds {path} for over "
                        f"{START_WAIT + STOP_WAIT} s: wait a moment, "
                        "then run this again"
                    ) from None
                time.sleep(0.1)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def stop_server(port: int, facts: dict) -> None:
    """Ask the server on the main port to end (`POST /api/server/stop`), and wait at
    most STOP_WAIT until its port is free."""
    pid = facts["pid"]
    fix = f"end it with `kill {pid}`, then run this again"
    try:
        with reach(
            urllib.request.Request(
                f"http://{HOST}:{port}/api/server/stop", data=b"", method="POST"
            ),
            ASK_TIMEOUT,
        ) as reply:
            reply.read()
    except urllib.error.HTTPError as error:
        raise ServeError(
            f"the server (pid {pid}) on port {port} refused the stop ({error.code}: "
            f"{error.read(500).decode('utf-8', 'replace').strip()}); {fix}"
        ) from error
    except (urllib.error.URLError, OSError) as error:
        if nobody_listens(error):
            return
        raise ServeError(
            f"the server (pid {pid}) on port {port} did not take the "
            f"stop ({getattr(error, 'reason', error)}); {fix}"
        ) from error
    deadline = time.monotonic() + STOP_WAIT
    while time.monotonic() < deadline:
        try:
            if ask(port, timeout=0.5) is None:
                return
        except ServeError:
            pass
        time.sleep(0.1)
    raise ServeError(
        f"the server (pid {pid}) on port {port} did not end in {STOP_WAIT} s; {fix}"
    )


def start_server(settings: dict) -> dict:
    """Start a server of this code as a process of its own, in a new session with no
    terminal and its output in SERVE_LOG, and wait at most START_WAIT for its answer on
    the main port."""
    home = lem_state.config()
    log = home / SERVE_LOG
    try:
        if log.stat().st_size > LOG_CAP:
            os.truncate(log, 0)
    except FileNotFoundError:
        pass
    with log.open("ab") as out:
        offset = out.tell()
        out.write(
            (
                f"{datetime.now(UTC).isoformat(timespec='seconds')} lem serve --ensure "
                f"starts a server of {code_version()} from {LEM_ROOT}\n"
            ).encode()
        )
        out.flush()
        child = subprocess.Popen(
            [sys.executable, "-B", str(SCRIPTS / "serve.py")],
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=out,
            start_new_session=True,
            close_fds=True,
            cwd=str(home),
        )
    deadline = time.monotonic() + START_WAIT
    while time.monotonic() < deadline:
        code = child.poll()
        if code is not None:
            with log.open("rb") as handle:
                handle.seek(offset)
                said = " ".join(
                    handle.read()
                    .decode("utf-8", "replace")
                    .strip()
                    .splitlines()[1:][-4:]
                )
            raise ServeError(
                f"the server ended at its start with status {code}: "
                f"{said or 'it said nothing'} (its log is {log})"
            )
        try:
            facts = ask(settings["port"], timeout=0.5)
        except ServeError:
            facts = None
        if facts is not None and facts["pid"] == child.pid:
            # it runs on its own now: nobody waits for its status
            child.returncode = 0
            return facts
        time.sleep(0.1)
    raise ServeError(
        f"the server (pid {child.pid}) gave no answer in {START_WAIT} s; "
        f"it may still start, and `lem serve --ensure` says so then. Its log is {log}"
    )


def outdated(facts: dict) -> bool:
    """Whether this code replaces the running server's: its scripts are newer, or as new
    with another identity. A server whose scripts are newer stays, so that a session
    that still runs an older plugin never brings the older code back."""
    mine = code_stamp()
    theirs = facts.get("stamp") if isinstance(facts.get("stamp"), int) else 0
    return mine > theirs or (mine == theirs and facts["version"] != code_version())


def shown(facts: dict | None, *, started: bool) -> dict:
    """What `--ensure` prints of a server."""
    if facts is None:
        return {
            "running": False,
            "started": False,
            "pid": None,
            "url": None,
            "tailscale": None,
            "version": None,
        }
    return {
        "running": True,
        "started": started,
        "pid": facts["pid"],
        "url": facts.get("url"),
        "tailscale": facts.get("tailscale"),
        "version": facts["version"],
    }


def ensure_held(settings: dict) -> dict:
    """`--ensure`, with SERVE_LOCK held: keep the server that runs when it serves these
    settings and its code is not `outdated`, else end it and start one of this code."""
    found = ask(settings["port"])
    if os.environ.get(NO_START[0]) == NO_START[1]:
        return {
            **shown(found, started=False),
            "said": (
                f"{NO_START[0]}={NO_START[1]} is set: no server starts and none ends"
            ),
        }
    door = settings["tailscale_port"] if settings["tailscale"] else None
    if (
        found is not None
        and found.get("tailscale_port") == door
        and not outdated(found)
    ):
        return shown(found, started=False)
    if found is not None:
        stop_server(settings["port"], found)
    return shown(start_server(settings), started=True)


def ensure() -> dict:
    """Make sure one server runs for this machine, the way its settings say, and
    say which."""
    with start_lock():
        return ensure_held(serve_settings())


def stop() -> dict:
    """End the server that runs on the main port, if one does."""
    port = serve_settings()["port"]
    with start_lock():
        found = ask(port)
        if found is None:
            return {"stopped": False, "said": f"no server runs on port {port}"}
        stop_server(port, found)
        return {"stopped": True, "pid": found["pid"], "version": found["version"]}


def configure(args: argparse.Namespace) -> dict:  # noqa: C901 - over the limit before the limit was set
    """Write the machine's `[serve]` from the flags given, end a server on a port it no
    longer serves, make sure the server runs the new way, and take Lem's tailnet entry
    out where the door closed."""
    # What `write_machine` would refuse (a file that does not read, another table or key
    # that is not valid there, a value of the wrong type in another table) is refused
    # here, before any server stops: refused after the stop, it would leave the
    # board down.
    lem_state.kept_tables("serve")
    try:
        before = serve_settings()
    except (ServeError, lem_state.StateError):
        # a [serve] with an unknown key, a value of the wrong type, a number that is no
        # port or one port twice is written again whole from the flags and the defaults,
        # as its refusal's fix says
        before = {"tailscale": False, "port": PORT, "tailscale_port": TAILNET_PORT}
    after = dict(before)
    if args.port is not None:
        after["port"] = args.port
    if args.tailscale_port is not None:
        after["tailscale_port"] = args.tailscale_port
    if args.tailscale or args.tailscale_off:
        after["tailscale"] = bool(args.tailscale)
    if after["tailscale"] and after["port"] == after["tailscale_port"]:
        raise ServeError(
            f"the main port and the door's port would both be {after['port']}: "
            "the door needs a port of its own; name another with --tailscale-port"
        )
    if after["tailscale"]:
        # what the door needs, checked now, so that nothing is written that would stop
        # every start
        tailnet(need_cli())
    with start_lock():
        if before["port"] != after["port"]:
            try:
                old = ask(before["port"])
            except ServeError:
                old = None
            if old is not None:
                stop_server(before["port"], old)
        lem_state.write_machine("serve", after)
        said = {
            **ensure_held(after),
            "settings": after,
            "file": str(lem_state.machine_file()),
        }
    if args.tailscale_off or (
        before["tailscale"] and before["tailscale_port"] != after["tailscale_port"]
    ):
        try:
            said["tailscale_entry"] = tailscale_off(before["tailscale_port"])
        except ServeError as error:
            said["tailscale_entry"] = {
                "removed": False,
                "port": before["tailscale_port"],
                "said": str(error),
            }
    return said


# The variables of the session a server was started from (agterm's, the short names
# session.py also reads, and a task's `LEM_TASK`): the server is no part of that
# session, and `lem session`, which it runs in its own process, would read them as the
# place of its caller (session.py `place`: its window and workspace).
SESSION_VARIABLES = re.compile(r"AGTERM_\w+|AGT_(SESSION_ID|SOCKET|WINDOW_ID)|LEM_TASK")


def detach_from_session() -> None:
    """Leave the session the server was started from: drop its variables, and put
    agtermctl's folder on PATH when the PATH of the hook or of the command that started
    the server has none (`AGTERMCTL_PLACES`), so that `lem session` finds it as the
    board's act of agterm does."""
    for name in [name for name in os.environ if SESSION_VARIABLES.fullmatch(name)]:
        del os.environ[name]
    if not shutil.which("agtermctl"):
        found = next(
            (place for place in AGTERMCTL_PLACES if os.access(place, os.X_OK)), None
        )
        if found:
            os.environ["PATH"] = os.pathsep.join(
                [str(Path(found).parent), *filter(None, [os.environ.get("PATH")])]
            )


def pid_file() -> Path:
    return lem_state.config() / lem_state.SERVE_PID


def write_pid(port: int) -> None:
    """The server's pid and its main port in Lem's home folder (`lem_state.SERVE_PID`),
    which `bin/lem` reads to tell whether a server runs, with no connect and no import
    of Lem's modules."""
    file = pid_file()
    file.parent.mkdir(parents=True, exist_ok=True)
    fresh = file.with_name(f"{file.name}.{os.getpid()}.new")
    fresh.write_text(f"{os.getpid()} {port}\n", encoding="utf-8")
    fresh.replace(file)


def remove_pid() -> None:
    """Remove the pid file at a clean stop, only when it is still this server's."""
    file = pid_file()
    try:
        if file.read_text(encoding="utf-8").split()[:1] == [str(os.getpid())]:
            file.unlink()
    except (OSError, IndexError):
        pass


def listen(host: str, *, verbose: bool, settings: dict) -> None:  # noqa: C901, PLR0915 - over the limit before the limit was set
    """Serve in the foreground, the way the settings say, until a stop, SIGTERM
    or Ctrl-C."""
    detach_from_session()
    port = settings["port"]
    tailnet_port = settings["tailscale_port"] if settings["tailscale"] else None
    Handler.machine = Machine()
    Handler.peers = lem_peers.Peers(tailnet_status)
    Handler.verbose = verbose
    Handler.listen_host = host
    door = None
    if tailnet_port is not None:
        if tailnet_port == port and host in (HOST, "localhost"):
            raise ServeError(
                f"the main port and the door's port are both {port}: the door needs a "
                "port of its own; `lem serve --tailscale-port N` writes another"
            )
        cli = need_cli()
        facts = tailnet(cli)
        door = Door(cli, facts["name"], tailnet_port, facts["login"])
    settle_names(door.name if door is not None else None)
    server = bind(host, port, Handler, "--port")
    servers = [server]
    entry = None
    try:
        if door is not None:
            servers.append(
                bind(
                    HOST,
                    door.port,
                    type("DoorHandler", (Handler,), {"door": door}),
                    "--tailscale-port",
                )
            )
            entry = publish(door.cli, door.name, door.port)
    except BaseException:
        for each in servers:
            each.server_close()
        raise
    bound = server.server_address[1]
    shown_host = f"[{host}]" if ":" in host else host
    said: dict[str, object] = {
        "host": host,
        "port": bound,
        "url": f"http://{shown_host}:{bound}/",
    }
    if door is not None:
        # the entry stays when the server stops: `lem serve --tailscale-off` takes
        # it out
        said["tailscale"] = {
            "url": door.url(),
            "login": door.owner,
            "port": door.port,
            "door": door_address(door.port),
            "entry": entry,
        }
    RUNNING.update(
        {
            "pid": os.getpid(),
            "version": code_version(),
            "stamp": code_stamp(),
            "root": str(LEM_ROOT),
            "config": str(lem_state.config()),
            "started": datetime.now(UTC).isoformat(timespec="seconds"),
            "port": bound,
            "url": said["url"],
            "host": HOSTNAME,
            "aliases": list(ALIASES),
            "tailscale": door.url() if door else None,
            "tailscale_port": door.port if door else None,
        }
    )
    SERVERS[:] = servers
    write_pid(bound)
    # the board's notifications: a look at each workspace's list of what waits, in a
    # thread of its own (lem_push)
    watcher = lem_push.Watcher(
        lambda: [(w.name, w.path, w.model) for w in Handler.machine.workspaces()],
        HOSTNAME,
    )
    threading.Thread(target=watcher.run, args=(STOPPING,), daemon=True).start()
    # the owner's Inbox while he is away: a look at the same lists, in a thread of its
    # own (lem_inbox)
    inbox = lem_inbox.Watcher(Handler.machine.workspaces, inbox_link, inbox_wake)
    threading.Thread(
        target=inbox.run, args=(STOPPING,), daemon=True, name="inbox"
    ).start()
    print(
        json.dumps(
            {
                **said,
                "version": RUNNING["version"],
                "workspaces": [
                    {"name": w["name"], "path": w["path"]}
                    for w in Handler.machine.listing()
                ],
            }
        ),
        flush=True,
    )

    def stop_now(_signum: int, _frame: types.FrameType | None) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop_now)
    for each in servers[1:]:
        threading.Thread(target=each.serve_forever, daemon=True).start()
    threading.Thread(
        target=forge_loop, args=(Handler.machine,), daemon=True, name="forge"
    ).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        STOPPING.set()
        for each in servers[1:]:
            each.shutdown()
        for each in servers:
            each.server_close()
        remove_pid()
    print(json.dumps({"stopped": True, "pid": os.getpid()}), flush=True)


def main() -> None:  # noqa: C901, PLR0911, PLR0912, PLR0915 - over the limit before the limit was set
    parser = argparse.ArgumentParser(
        prog="lem serve",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--ensure",
        action="store_true",
        help=(
            "make sure one server runs for this machine, from this code, the way the "
            "machine's settings say: keep the one that runs, or end one of older code "
            "and start this one, as a process of its own; print it as JSON. "
            "Safe to run twice at once"
        ),
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="end the server that runs, and print what ended",
    )
    parser.add_argument(
        "--tailscale",
        action="store_true",
        help=(
            "from now on, open the tailnet door too: a second listener on 127.0.0.1 at "
            "the door's port, behind `tailscale serve --bg --https=PORT`, which lets "
            "in only the owner's own Tailscale login. Written to the machine's "
            "settings, then as --ensure. The entry stays when the server stops, and "
            "Tailscale keeps it across a restart; --tailscale-off takes it out. "
            "Funnel is never used"
        ),
    )
    parser.add_argument(
        "--tailscale-off",
        action="store_true",
        help=(
            "from now on, no door: written to the machine's settings, then as "
            "--ensure, and Lem's entry of the door's port goes out of "
            "`tailscale serve`, only when it points at Lem's door"
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        metavar="N",
        help=(
            f"from now on, serve port N on 127.0.0.1 (default: {PORT}): "
            "written to the machine's settings, then as --ensure"
        ),
    )
    parser.add_argument(
        "--tailscale-port",
        type=int,
        metavar="N",
        help=(
            "from now on, the door's HTTPS port on the tailnet, and its port on "
            f"127.0.0.1 (default: {TAILNET_PORT}): written to the machine's settings, "
            "then as --ensure; a port that another entry of "
            "`tailscale serve` holds is refused"
        ),
    )
    parser.add_argument(
        "--host",
        help=(
            "the foreground server only: the address to listen on (default: "
            f"{HOST}, this machine only). The server has no login and shows the tasks' "
            "files and the copied talk of interviews: name only an address that the "
            "owner's own devices alone reach; for a tailnet, "
            "keep the default and use --tailscale"
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="the foreground server only: log each request on stderr",
    )
    parser.add_argument(
        "--add",
        metavar="DIR",
        action="append",
        help="put the repository DIR is in into the list of workspaces, and exit",
    )
    parser.add_argument(
        "--remove",
        metavar="DIR",
        action="append",
        help="take the repository DIR is in out of the list of workspaces, and exit",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="print the workspaces as the server shows them, as JSON, and exit",
    )
    parser.add_argument(
        "--push-test",
        action="store_true",
        help=(
            "send one push to every device that turned the board's notifications on, "
            "and print each push service's status code as JSON (201: "
            "it took the push); a device the service no longer knows (404, "
            "410) goes off the list"
        ),
    )
    parser.add_argument(
        "--join",
        metavar="HOST[:PORT]",
        help=(
            "show the boards of the machine HOST of the tailnet on this machine's "
            "board too, under /HOST/, and exit: HOST runs `lem serve --tailscale`, and "
            "PORT is its door's port when it is not this machine's own. "
            "It asks HOST once and says what it found; a machine that does not answer "
            "is joined all the same. The running server takes it at its next look"
        ),
    )
    parser.add_argument(
        "--leave", metavar="HOST", help="show the boards of HOST no more, and exit"
    )
    parser.add_argument(
        "--peers",
        action="store_true",
        help=(
            "print each machine joined, its address and whether it answers now, "
            "as JSON, and exit"
        ),
    )
    args = parser.parse_args()
    try:
        settings_flags = (
            args.tailscale
            or args.tailscale_off
            or args.port is not None
            or args.tailscale_port is not None
        )
        actions = [
            name
            for name, on in (
                ("--add", args.add),
                ("--remove", args.remove),
                ("--list", args.list),
                ("--ensure", args.ensure),
                ("--stop", args.stop),
                ("a setting", settings_flags),
                ("--push-test", args.push_test),
                ("--join", args.join),
                ("--leave", args.leave),
                ("--peers", args.peers),
            )
            if on
        ]
        if len(actions) > 1 and set(actions) != {"--add", "--remove"}:
            raise ServeError(
                f"{' and '.join(actions)} are two commands: give one of them"
            )
        if args.tailscale and args.tailscale_off:
            raise ServeError(
                "--tailscale and --tailscale-off say two things: give one of them"
            )
        if actions and (args.host is not None or args.verbose):
            raise ServeError(
                "--host and --verbose belong to the foreground server, plain "
                "`lem serve`; the server that starts on demand serves 127.0.0.1"
            )
        for value, flag in (
            (args.port, "--port"),
            (args.tailscale_port, "--tailscale-port"),
        ):
            if value is not None and not 0 < value < PORT_LIMIT:
                raise ServeError(f"{flag} {value} is no port: give one from 1 to 65535")
        if args.ensure:
            print(json.dumps(ensure(), indent=2))
            return
        if args.stop:
            print(json.dumps(stop(), indent=2))
            return
        if settings_flags:
            print(json.dumps(configure(args), indent=2))
            return
        if args.add or args.remove:
            done = {"added": [], "removed": [], "kept": []}
            for directory in args.add or []:
                main_dir = checkout_of(directory)
                if not (main_dir / ".lem").is_dir():
                    raise ServeError(
                        f"{main_dir} has no .lem folder: Lem is not set up there; "
                        "run /lem init in it first"
                    )
                done["added" if lem_state.register(main_dir) else "kept"].append(
                    str(main_dir)
                )
            for directory in args.remove or []:
                try:
                    gone = lem_state.main_checkout(Path(directory))
                except lem_state.StateError:
                    # a repository that is gone is still taken out by the path it had
                    gone = Path(os.path.abspath(directory))  # noqa: PTH100 - abspath folds `..` and follows no link; pathlib has no such call
                if not lem_state.unregister(gone):
                    raise ServeError(
                        f"{gone} is not in the list of workspaces; "
                        "`lem serve --list` shows it"
                    )
                done["removed"].append(str(gone))
            print(json.dumps({**done, "workspaces": lem_state.workspaces()}, indent=2))
            return
        if args.push_test:
            sent = lem_push.send_all()
            said = (
                (
                    f"{len(sent)} {'device' if len(sent) == 1 else 'devices'}; "
                    "the push service took "
                    f"{sum(r['status'] == HTTPStatus.CREATED for r in sent)}"
                )
                if sent
                else (
                    "no device has turned the board's notifications on: "
                    'open the board on the device, then "Notify this '
                    'device" on Waits for you'
                )
            )
            print(
                json.dumps(
                    {"devices": len(sent), "results": sent, "said": said}, indent=2
                )
            )
            return
        if args.join or args.leave or args.peers:
            try:
                if args.join:
                    settle_names()
                    said = lem_peers.join(
                        args.join,
                        HOSTNAME,
                        reserved(),
                        serve_settings()["tailscale_port"],
                        tailnet_status,
                    )
                else:
                    said = (
                        lem_peers.leave(args.leave)
                        if args.leave
                        else lem_peers.report(tailnet_status)
                    )
            except lem_peers.PeerError as error:
                raise ServeError(str(error)) from error
            print(json.dumps(said, indent=2))
            return
        if args.list:
            settle_names()
            print(json.dumps(Machine().listing(), indent=2))
            return
        listen(args.host or HOST, verbose=args.verbose, settings=serve_settings())
    except (ServeError, lem_state.StateError, lem_push.PushError) as error:
        sys.exit(f"serve.py: {error}")


if __name__ == "__main__":
    main()
