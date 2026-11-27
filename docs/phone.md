# The board on your phone

Your phone opens [the board](board.md) through [Tailscale](https://tailscale.com), a private
network of your devices. Only your Tailscale login gets access. Lem needs Tailscale only for
another device.

## Set it up one time

1. Install Tailscale on the computer and on the phone.
2. Sign in to both with the same account.
3. In the Tailscale admin console, turn on MagicDNS and HTTPS.
4. Type `/lem serve tailscale` in Claude Code.
5. On the phone, open the `tailscale` address that Lem gives.
6. In the browser's share menu, select "Add to Home Screen".
7. Open Lem from the Home Screen, and open "Waits for you".
8. Tap "Turn on", and allow notifications.

The phone then gets a notification when something starts to wait for you. When the computer
sleeps, the phone cannot open the board.

On a phone, **Merge…**, **Park**, **Drop** and a card open over the task. The page then shows the
result, or why Lem refused. While you are away, a task that waits for you can link to its thread
in the optional [Plannotator Inbox](away.md#answer-from-the-inbox).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/screens/phone-dark.png">
  <img src="assets/screens/phone-light.png" alt="The board on a phone: the column Waits for you, with three tasks" width="390" height="844">
</picture>

*The board on a phone. The picture shows demo data.*

## Two computers, one address

1. On each computer, type `/lem serve tailscale` one time.
2. On the computer whose address you open, type `/lem serve join HOST[:PORT]`.

`HOST` is the Tailscale name of the other computer. Lem uses this computer's door port if you
omit `:PORT`. The default door port is 4537.

- If both doors use the same port, type `/lem serve join silvers-mac-mini`.
- If the other door uses a different port, add that port. For port 4538, type
  `/lem serve join silvers-mac-mini:4538`.

That address then lists the repositories of both computers. A computer that does not answer shows
"not reachable". `/lem serve leave HOST` removes it.

The browser tab, the sidebar header, and the workspace switcher show the machine and workspace.
Each workspace has its own `/HOST/WORKSPACE/` address, even when two workspaces have the same name.

## The server

A new Claude Code session in a repository that uses Lem starts the server, and so does the first
`lem` command of any session. The first session after an update replaces it.

The server can merge a green change that is not careful when the verdict is merge and
`branch.land` is `"agent"`. With `branch.land = "owner"`, you merge even if the verdict is merge.
See [the merge rules](merge.md#the-merge-review).

Each hour the server removes the old files, as [`state.keep_days`](settings.md#state) tells. While
you are away, it sends what waits for you to the Plannotator Inbox if it runs. It never types into a session.

The server also watches each task that builds or lands. When its session does no work for 45
minutes, the server asks the session for its status. After 10 more minutes with no work, the server
opens a fresh session one time. When that session also stops, the task waits for you as "stopped".

When the server cannot read the work of a session, it uses only the record of the task. After 45
minutes with no change, it asks the session for its status. After 10 more minutes, the task waits
for you as "stopped", and the row says that Lem cannot read its session. "Open a session" then
opens a fresh one.

## Commands

Type these in Claude Code:

- `/lem serve`: starts the server if necessary, and gives the board's address.
- `/lem serve tailscale`, `/lem serve tailscale off`: lets your phone in, or closes the door.
- `/lem serve join HOST[:PORT]`, `/lem serve leave HOST`: adds or removes a second computer.
- `/lem serve stop`: stops the server.

After a remote login with no Claude Code, run Lem's command:

```bash
lem serve ensure
```
