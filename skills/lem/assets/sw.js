// The service worker of Lem's board, served at /sw.js so that its scope is the whole board. It has one
// job: show a notification when the board server pushes that something waits for the owner (push.py).
//
// A push carries no payload, so event.data is null. The worker asks the server what to say
// (/api/push/latest, same origin: through the tailnet door it carries the owner's login as a page does)
// and shows that; when the answer does not come, it shows a fixed sentence, because a push that shows no
// notification makes the browser take the permission back (Safari does at once).
//
// What it deliberately does not do: it handles no fetch, so it caches no page and the board has no
// offline view; it keeps no data; it badges nothing. A click on the notification brings an open board
// window forward and takes it to the task, or opens one.
const FIXED = { title: 'Lem', body: 'Something waits for you in Lem', url: '/' }
// How long the worker waits for the server's words before it shows the fixed sentence (a guess: the
// browser gives a push event some seconds, and the board answers in well under one).
const ASK_MS = 6000

self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', ev => ev.waitUntil(self.clients.claim()))

async function said () {
  const stop = new AbortController()
  const timer = setTimeout(() => stop.abort(), ASK_MS)
  try {
    const reply = await fetch('/api/push/latest', { credentials: 'include', cache: 'no-store', signal: stop.signal })
    const got = reply.ok ? await reply.json() : null
    return got && typeof got.title === 'string' ? got : FIXED
  } catch {
    return FIXED
  } finally {
    clearTimeout(timer)
  }
}

self.addEventListener('push', ev => {
  ev.waitUntil(said().then(say => self.registration.showNotification(say.title || FIXED.title, {
    body: say.body || FIXED.body,
    tag: say.tag || 'lem',
    icon: '/assets/icon-192.png',
    data: { url: typeof say.url === 'string' && say.url.startsWith('/') ? say.url : '/' },
  })))
})

self.addEventListener('notificationclick', ev => {
  ev.notification.close()
  const url = new URL(ev.notification.data?.url || '/', self.location.origin).href
  ev.waitUntil((async () => {
    const open = await self.clients.matchAll({ type: 'window', includeUncontrolled: true })
    for (const client of open) {
      if (new URL(client.url).origin !== self.location.origin) continue
      await client.focus()
      try {
        if (await client.navigate(url)) return
      } catch { /* a page this worker does not control cannot be moved: open a new one */ }
      break
    }
    await self.clients.openWindow(url)
  })())
})
