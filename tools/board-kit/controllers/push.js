// The control of the board's notifications on this device (lem_board_pages `push_row`, lem_push.py): it says
// whether this device gets a notification when something starts to wait for the owner, and turns that on
// and off. The server renders a sentence for each state; the controller sets the state in data-js-push and
// a line of what happened in data-js-note, both kept by a morph (app.js), and board.css shows the matching
// sentence and buttons.
//
// The tap that turns it on calls PushManager.subscribe at once, in the tap's own handler: Safari asks for
// the permission only from a user's gesture, and Apple says to subscribe "immediately from the gesture's
// event handler code". So the worker and the key are made ready when the control connects, before any tap.
import { Controller } from '@hotwired/stimulus'

// the page's own state of this device's subscription, synced with the server once per tab
const SYNCED = 'lem-push-synced'

function bytes (text) {
  const plain = atob(text.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - (text.length % 4)) % 4))
  return Uint8Array.from(plain, ch => ch.charCodeAt(0))
}

function same (a, b) {
  if (!a || !b) return false
  const x = new Uint8Array(a); const y = new Uint8Array(b)
  return x.length === y.length && x.every((v, i) => v === y[i])
}

export default class extends Controller {
  async connect () {
    this.state(this.blocker() ?? 'busy')
    if (this.blocker()) return
    try {
      const [registration, answer] = await Promise.all([
        navigator.serviceWorker.register('/sw.js', { scope: '/' }).then(() => navigator.serviceWorker.ready),
        fetch('/api/push/key', { cache: 'no-store' }).then(reply => reply.json().then(body => ({ ok: reply.ok, body }))),
      ])
      if (!answer.ok) throw new Error(answer.body?.said ?? 'the server gave no key')
      this.registration = registration
      this.key = bytes(answer.body.key)
      await this.show()
    } catch (err) {
      this.state('off', `Notifications cannot start here: ${err?.message ?? err}`)
    }
  }

  // why this device cannot have them, as a state, or none
  blocker () {
    if (!window.isSecureContext) return 'insecure'
    // an iPad says it is a Mac, and only its touch tells it apart; no other device that says Mac has touch
    const ua = navigator.userAgent
    const ios = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1 && !/Android/.test(ua))
    const standalone = navigator.standalone === true || matchMedia('(display-mode: standalone)').matches
    if (ios && !standalone) return 'home'
    if (!('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window)) return 'none'
    if (Notification.permission === 'denied') return 'blocked'
    return null
  }

  // the state of this device from its subscription; a subscription under another key (the machine's key
  // was made again) is dropped, since the server can no longer push to it
  async show () {
    let sub = await this.registration.pushManager.getSubscription()
    if (sub && !same(sub.options?.applicationServerKey, this.key)) {
      await sub.unsubscribe()
      sub = null
      return this.state('off', 'The board’s key changed, so this device was turned off. Turn it on again.')
    }
    if (sub && !sessionStorage.getItem(SYNCED)) {
      // the server's list may have lost this device (its file deleted, a push the service refused): tell it once a tab
      await this.post('subscribe', sub.toJSON()).then(() => sessionStorage.setItem(SYNCED, '1'), () => {})
    }
    this.state(sub ? 'on' : (this.blocker() ?? 'off'))
  }

  state (name, note = null) {
    this.element.setAttribute('data-js-push', name)
    if (note) this.element.setAttribute('data-js-note', note)
    else this.element.removeAttribute('data-js-note')
  }

  async post (act, body) {
    const reply = await fetch(`/api/push/${act}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), cache: 'no-store' })
    let answer = null
    try { answer = await reply.json() } catch { /* the server said no JSON */ }
    if (!reply.ok) throw new Error(answer?.said ?? `the server answered ${reply.status}`)
    return answer
  }

  on (ev) {
    ev.preventDefault()
    if (!this.registration || !this.key) return this.state('off', 'Not ready yet: try again in a moment.')
    // subscribe first, in the tap's own handler: this is what asks for the permission
    const asked = this.registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: this.key })
    this.state('busy')
    asked.then(async sub => {
      try {
        await this.post('subscribe', sub.toJSON())
        sessionStorage.setItem(SYNCED, '1')
        this.state('on')
      } catch (err) {
        await sub.unsubscribe().catch(() => {})
        this.state('off', `The board did not take this device: ${err?.message ?? err}`)
      }
    }, err => {
      const state = this.blocker() ?? 'off'
      this.state(state, state === 'off' ? `It was not turned on: ${err?.message ?? err}` : null)
    })
  }

  async off (ev) {
    ev.preventDefault()
    this.state('busy')
    const sub = await this.registration?.pushManager.getSubscription()
    if (sub) {
      await this.post('unsubscribe', { endpoint: sub.endpoint }).catch(() => {})
      await sub.unsubscribe().catch(() => {})
    }
    sessionStorage.removeItem(SYNCED)
    this.state('off')
  }

  async test (ev) {
    ev.preventDefault()
    const sub = await this.registration?.pushManager.getSubscription()
    if (!sub) return this.state('off')
    this.state('on', 'Sending…')
    try {
      const sent = await this.post('test', { endpoint: sub.endpoint })
      this.state('on', sent.status === 201
        ? 'Sent: the push service took it, and the notification shows in a few seconds.'
        : `The push service answered ${sent.status ?? 'nothing'}: ${sent.said}`)
    } catch (err) {
      this.state('on', `It was not sent: ${err?.message ?? err}`)
    }
  }
}
