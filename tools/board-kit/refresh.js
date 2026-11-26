// What Turbo does with the stream's refresh (a morph of the page into its new version), set right for
// the board in two places.
import { registerAdapter, session } from '@hotwired/turbo'

// A refresh the stream or its poll asked for: the next visit of the page's own address with action
// `replace` is that refresh. A visit the owner started (the backlog's filter, `?only=new`, also a
// `replace`) is never marked, and fails as Turbo has it.
const REFRESH = Symbol('lem refresh')
let asked = false

// A visit of the task's frame with data-turbo-action="advance" moves the address, and Turbo keeps the
// address before it as the page it rendered last (hotwired/turbo#1214, open in 8.0.23). The stream's next
// refresh was then no page refresh to Turbo: it replaced the whole body in place of a morph, and an open
// card's frame loaded again without the owner's choice and words (trial R6, 2026-11-26). The page shows
// what its address renders, so a refresh first names that address as the page rendered last.
document.addEventListener('turbo:before-stream-render', ev => {
  if (ev.detail.newStream?.action !== 'refresh') return
  asked = true
  if (session.view.lastRenderedLocation.href !== location.href) session.view.lastRenderedLocation = new URL(location.href)
})

// A refresh that finds no server (no answer, or a server error: the server stops or starts again behind
// the tailnet door, which then answers 502 with no body) made Turbo load the address as a new page, and
// the owner saw the door's blank page in place of the board (trial R6, 2026-11-26). Such a refresh ends as
// failed and the page stays as it is; the stream hears it (`lem:refresh-failed`), says "reconnecting" and
// reads the page again once the server answers. A refresh the server answers for good (a 404 for a
// workspace taken off the list) shows the board's own page of it, as every other visit does.
const NO_ANSWER = new Set([0, -1])
const NOT_HTML = -2

function lost (status) {
  return NO_ANSWER.has(status) || status >= 500
}

const browser = session.adapter
registerAdapter(Object.assign(Object.create(browser), {
  visitStarted (visit) {
    if (asked && visit.action === 'replace' && visit.location.href === location.href) visit[REFRESH] = true
    asked = false
    return browser.visitStarted.call(this, visit)
  },
  visitRequestFailedWithStatusCode (visit, statusCode) {
    const failed = status => {
      if (!lost(status)) return browser.visitRequestFailedWithStatusCode.call(this, visit, statusCode)
      visit.fail()
      document.dispatchEvent(new CustomEvent('lem:refresh-failed', { detail: { status } }))
    }
    if (!visit[REFRESH]) return browser.visitRequestFailedWithStatusCode.call(this, visit, statusCode)
    if (statusCode !== NOT_HTML) return failed(statusCode)
    // Turbo says only "not HTML" of an answer with no HTML in it (the door's 502): its status says which
    visit.request.response.then(response => failed(response.status), () => failed(0))
  }
}))
