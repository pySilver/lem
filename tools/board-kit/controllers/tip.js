// The hover of the time card of a task: what a band, a span or a mark is, how long it took and its two
// clock times, from the attributes the server put on it (data-head, data-sub, data-from, data-to as ms
// or `now`, data-fill). A tap shows it too, where there is no pointer to hover. The name of a stage
// stands in its band only where it fits; the server cannot know the width the card gets.
import { Controller } from '@hotwired/stimulus'
import { hms, span } from './time.js'

export default class extends Controller {
  static targets = ['box']

  connect () {
    this.fit = () => {
      for (const label of this.element.querySelectorAll('.tt-band em')) {
        label.removeAttribute('data-js-hidden')
        label.toggleAttribute('data-js-hidden', label.offsetWidth + 10 > label.parentElement.clientWidth)
      }
    }
    this.observer = new ResizeObserver(this.fit)
    this.observer.observe(this.element)
    document.addEventListener('turbo:morph', this.fit)
  }

  disconnect () {
    this.observer?.disconnect()
    document.removeEventListener('turbo:morph', this.fit)
  }

  move (ev) {
    const node = ev.target.closest?.('[data-head]')
    if (!node || !this.element.contains(node)) return this.hide()
    const box = this.boxTarget
    const from = Number(node.dataset.from); const now = node.dataset.to === 'now'; const to = now ? Date.now() : Number(node.dataset.to)
    const line = (cls, text) => { const div = document.createElement('div'); div.className = cls; div.textContent = text; return div }
    const head = line('tt', node.dataset.head)
    if (node.dataset.fill) { const dot = document.createElement('i'); dot.style.background = node.dataset.fill; head.prepend(dot) }
    box.replaceChildren(head, ...(node.dataset.sub ? [line('ts', node.dataset.sub)] : []),
      line('td', from === to ? `at ${hms(from)}` : `${span(to - from)} · ${hms(from)} → ${now ? 'now' : hms(to, from)}`))
    box.hidden = false
    const area = this.element.getBoundingClientRect()
    const x = ev.clientX - area.left; const y = ev.clientY - area.top; const w = box.offsetWidth; const h = box.offsetHeight
    box.style.left = `${x + 14 + w > area.width ? Math.max(0, x - 14 - w) : x + 14}px`
    box.style.top = `${Math.max(0, Math.min(y + 14, area.height - h))}px`
  }

  hide () {
    if (this.hasBoxTarget) this.boxTarget.hidden = true
  }
}
