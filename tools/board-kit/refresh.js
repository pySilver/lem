// What Turbo does with a page refresh (the stream's `refresh`, a morph of the page into its new version),
// set right for the board in two places.
import { registerAdapter, session } from '@hotwired/turbo'

// A visit of the task's frame with data-turbo-action="advance" moves the address, and Turbo keeps the
// address before it as the page it rendered last (hotwired/turbo#1214, open in 8.0.23). The stream's next
// refresh was then no page refresh to Turbo: it replaced the whole body in place of a morph, and an open
// card's frame loaded again without the owner's choice and words (trial R6, 2026-11-26). The page shows
// what its address renders, so a refresh first names that address as the page rendered last.
document.addEventListener('turbo:before-stream-render', ev => {
  if (ev.detail.newStream?.action !== 'refresh') return
  if (session.view.lastRenderedLocation.href !== location.href) session.view.lastRenderedLocation = new URL(location.href)
})

// A page refresh whose read fails (the server stops or starts again behind the tailnet door, which then
// answers 502 with no body) made Turbo load the address as a new page, and the owner saw the door's blank
// page in place of the board (trial R6, 2026-11-26). Such a refresh ends as failed and the page stays as
// it is; the stream hears it (`lem:refresh-failed`), says "reconnecting" and reads the page again once
// the server answers. Every other visit fails as Turbo has it.
const browser = session.adapter
registerAdapter(Object.assign(Object.create(browser), {
  visitRequestFailedWithStatusCode (visit, statusCode) {
    if (!visit.isPageRefresh) return browser.visitRequestFailedWithStatusCode.call(this, visit, statusCode)
    visit.fail()
    document.dispatchEvent(new CustomEvent('lem:refresh-failed', { detail: { statusCode } }))
  }
}))
