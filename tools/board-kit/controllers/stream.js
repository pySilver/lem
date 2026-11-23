// The live page: one EventSource on the workspace's stream, whose messages are Turbo stream actions
// (`refresh`: Turbo fetches the page again and morphs it in). The element is permanent, so it lives
// across the visits of one workspace and its words in the status bar are its own.
//
// An open after a render, the page's load or a visit that changes the task in its address, names the last
// id seen (`?rendered=`), and the server sends a refresh at once only when the log is no longer at it: the
// page shows what its live stream told it, and a refresh there would morph over the visit and over a click
// made during it. An open after the page may have missed a change (back into view, out of the back-forward
// cache, or after its stream went down) names it as `?since=`, and the server sends a refresh at once
// whatever the log, since a change the page missed may add no line to it (the owner's mark, the settings, a
// task's files). An id is the log's version, its inode and its count of lines in one text ("8812-140"),
// kept whole: a log that `lem project prune` replaced has another inode, so the page is told also when the
// count is the same. With a task open (its address), the stream watches that task's files too (`&task=`).
//
// A refresh that comes while a form of the page is posted waits for the post's end: Turbo's visit of the
// refresh would stop the post, so the page would never follow its answer (the start of a task from a
// backlog item stayed on the backlog while its session opened, 2026-11-23). An act's own lines come into
// the log before it answers, so its refresh comes during the post. At the post's end, an answer with a
// page drops the refresh, since that page was drawn after the lines and Turbo shows it; a post that ended
// with no page to show (the network failed, nothing answered) gets the refresh then.
//
// iOS drops an EventSource in the background, or keeps a dead one that still says it is open, and a
// network can stop forwarding and keep the connection open. So a page that comes back into view, or out
// of the back-forward cache, opens a new stream; and a page that heard nothing for SILENCE_MS (no message
// and no `ping` event, which the server sends every 10 s of quiet) takes its stream as down, as does one
// whose new stream did not open within that time. A stream that fails is closed here, never left to the
// browser's own reconnect, so every new one is this page's open, and the page says "reconnecting" until it
// opens. While the stream is down the page, every POLL_MS, opens a new stream when none is opening and
// refreshes itself, but only after the server answered a light request within ASK_MS: a refresh that finds
// no server would make Turbo reload the page into the browser's error.
import { Controller } from '@hotwired/stimulus'
import { ago } from './time.js'

const POLL_MS = 10000
// 25 s of silence, over two of the server's pings: the page says "reconnecting" within 30 s of a stop, at
// most one tick late. An unmeasured estimate (the plan of 2026-11-22), as is the light request's 5 s.
const SILENCE_MS = 25000
const ASK_MS = 5000
const REFRESH = '<turbo-stream action="refresh"></turbo-stream>'

export default class extends Controller {
  static values = { url: String, since: String }

  connect () {
    this.lastId = this.sinceValue
    // whether the page may have missed a change, so that its next open asks for a refresh (`?since=`)
    this.owed = false
    this.lastMessage = 0
    this.down = 0
    this.onShow = () => { if (document.visibilityState === 'visible') { this.owed = true; this.open() } }
    this.onPageShow = ev => { if (ev.persisted) { this.owed = true; this.open() } }
    // a visit to another task opens the stream again for that task's files
    this.onVisit = () => { if (this.task() !== this.watching) this.open() }
    // the forms being posted, and whether a refresh waits for their end
    this.posts = new Set()
    this.held = false
    this.onPostStart = ev => this.posts.add(ev.detail.formSubmission)
    this.onPostEnd = ev => this.posted(ev.detail)
    this.onRender = ev => {
      if (ev.detail.newStream?.action !== 'refresh' || !this.posts.size) return
      ev.preventDefault()
      this.held = true
    }
    document.addEventListener('turbo:submit-start', this.onPostStart)
    document.addEventListener('turbo:submit-end', this.onPostEnd)
    document.addEventListener('turbo:before-stream-render', this.onRender)
    document.addEventListener('visibilitychange', this.onShow)
    window.addEventListener('pageshow', this.onPageShow)
    document.addEventListener('turbo:load', this.onVisit)
    document.addEventListener('turbo:frame-load', this.onVisit)
    window.addEventListener('popstate', this.onVisit)
    this.timer = setInterval(() => this.tick(), 1000)
    this.open()
  }

  disconnect () {
    document.removeEventListener('turbo:submit-start', this.onPostStart)
    document.removeEventListener('turbo:submit-end', this.onPostEnd)
    document.removeEventListener('turbo:before-stream-render', this.onRender)
    document.removeEventListener('visibilitychange', this.onShow)
    window.removeEventListener('pageshow', this.onPageShow)
    document.removeEventListener('turbo:load', this.onVisit)
    document.removeEventListener('turbo:frame-load', this.onVisit)
    window.removeEventListener('popstate', this.onVisit)
    clearInterval(this.timer)
    this.close()
  }

  // the task open in the page's address, whose files the stream watches too (an artifact written with no event)
  task () {
    return /\/tasks\/([a-z0-9-]+)/.exec(location.pathname)?.[1] ?? ''
  }

  open () {
    this.close()
    this.watching = this.task()
    const id = `${this.owed ? 'since' : 'rendered'}=${encodeURIComponent(this.lastId)}`
    this.again = this.owed
    const source = new EventSource(`${this.urlValue}?${id}${this.watching ? `&task=${this.watching}` : ''}`)
    const heard = ev => {
      if (this.source !== source) return false
      if (ev.lastEventId) this.lastId = ev.lastEventId
      this.heard = Date.now()
      this.down = 0
      return true
    }
    source.addEventListener('open', ev => { if (heard(ev)) this.say() })
    // the server sends the refresh of a `since` open before anything else, so a ping or a message pays it
    source.addEventListener('ping', ev => { if (heard(ev)) { this.owed = false; this.say() } })
    source.addEventListener('message', ev => {
      if (!heard(ev)) return
      this.owed = false
      this.lastMessage = Date.now()
      this.say()
    })
    source.addEventListener('error', () => {
      if (this.source !== source) return
      this.close()
      this.went()
    })
    window.Turbo.connectStreamSource(source)
    this.source = source
    this.heard = Date.now()
    this.say()
  }

  close () {
    if (!this.source) return
    window.Turbo.disconnectStreamSource(this.source)
    this.source.close()
    this.source = null
  }

  // a post ended: a refresh it held is dropped when Turbo shows the answer's page, else rendered now
  posted ({ formSubmission, fetchResponse }) {
    this.posts.delete(formSubmission)
    if (this.posts.size || !this.held) return
    this.held = false
    if (!fetchResponse?.isHTML) window.Turbo.renderStreamMessage(REFRESH)
  }

  // the stream is down from now, unless it already was, and the page may miss a change until a new one opens
  went () {
    if (!this.down) this.down = Date.now()
    this.owed = true
    this.say()
  }

  async tick () {
    // a stream that said nothing for too long, or a new one that never opened, is dead
    if (this.source && Date.now() - this.heard > SILENCE_MS) { this.close(); this.went() }
    this.say()
    if (!this.down || Date.now() - (this.polled ?? 0) < POLL_MS) return
    this.polled = Date.now()
    if (!this.source) this.open()
    try {
      const reply = await fetch('/api/server', { cache: 'no-store', signal: AbortSignal.timeout(ASK_MS) })
      if (reply.ok) { window.Turbo.renderStreamMessage(REFRESH); this.answered = Date.now() }
    } catch {
      // the server does not answer, or not in time: the page stays as it is, and says so
    }
    this.say()
  }

  say () {
    const now = Date.now()
    let text, title
    if (!this.down && this.source?.readyState === EventSource.OPEN) {
      text = this.lastMessage ? `live · last change ${ago(now - this.lastMessage)}` : 'live'
      title = 'lem serve tells this page each change of the workspace, and the page changes with it'
    } else if (!this.down) {
      text = this.again ? 'reconnecting' : 'connecting…'
      title = this.again ? 'The page opens a new stream to lem serve, which sends it what it missed' : 'The page opens its stream to lem serve'
    } else {
      text = 'reconnecting'
      const since = new Date(this.down).toLocaleTimeString()
      title = this.answered && this.answered > this.down
        ? `The stream is down since ${since}, and lem serve answers: the page reads itself again and opens a new stream every ${POLL_MS / 1000}s`
        : `lem serve does not answer since ${since}: the page tries again every ${POLL_MS / 1000}s`
    }
    this.element.classList.toggle('down', Boolean(this.down))
    if (this.element.textContent !== text) this.element.textContent = text
    this.element.title = title
  }
}
