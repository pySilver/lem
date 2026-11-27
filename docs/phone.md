# The board on your phone

Your phone opens [the board](board.md) through [Tailscale](https://tailscale.com), a private
network of your devices. Only your Tailscale login gets access. Lem needs Tailscale only for
another device.

## Set it up one time

1. Install Tailscale on the computer and on the phone.
2. Sign in to both with the same account.
3. In the Tailscale admin console, turn on MagicDNS and HTTPS.
4. Type `/lem serve tailscale` in Claude Code. This opens the door: a second port of the board
   server, 4537 by default, that only your Tailscale login reaches.
5. On the phone, open the `tailscale` address that Lem gives.
6. In the browser's share menu, select "Add to Home Screen".
7. Open Lem from the Home Screen, and open "Waits for you".
8. Tap "Turn on", and allow notifications.

The phone then gets a notification when something starts to wait for you. When the computer
sleeps, the phone cannot open the board.

On a phone, **Merge…**, **Park**, **Drop** and a card (a question of the task) open over the
task. The page then shows the result, or why Lem refused.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/screens/phone-dark.png">
  <img src="assets/screens/phone-light.png" alt="The board on a phone: the column Waits for you, with three tasks" width="390" height="844">
</picture>

*The board on a phone. The picture shows demo data.*

### The key and the devices

You supply no key for the notifications. The board server makes its key, `push-key.pem` in
`~/.config/lem/`, the first time that the board opens in a browser that can show notifications.
The server signs each notification with this key. When a device turns on the notifications, the server adds the device
to `push.json` in the same folder.

## Two computers, one address

1. On each computer, type `/lem serve tailscale` one time.
2. On the computer whose address you open, type `/lem serve join HOST[:PORT]`.

`HOST` is the Tailscale name of the other computer. Lem uses this computer's door port if you
omit `:PORT`.

- If both doors use the same port, type `/lem serve join mac-mini`.
- If the other door uses a different port, add that port. For port 4538, type
  `/lem serve join mac-mini:4538`.

That address then lists the repositories of both computers. A computer that does not answer shows
"not reachable". `/lem serve leave HOST` removes it.

The browser tab, the sidebar header and the switcher show the computer and the repository. Each
repository has its own `/HOST/REPOSITORY/` address, even when two repositories have the same name.

## Commands

Type these in Claude Code:

- `/lem serve`: starts the [board server](board.md#the-server) if necessary, and gives the
  board's address.
- `/lem serve tailscale`, `/lem serve tailscale off`: opens or closes the door.
- `/lem serve join HOST[:PORT]`, `/lem serve leave HOST`: adds or removes a second computer.

After a remote login with no Claude Code, run Lem's command to start the server:

```bash
lem serve ensure
```
