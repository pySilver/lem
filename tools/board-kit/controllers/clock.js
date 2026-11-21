// The times that move: each [data-since] says how long since its moment, each [data-ago] how long ago,
// once a second, from the timestamp (ms) the server rendered. The server writes the same words at
// its render, so a page reads right before this runs.
import {Controller} from '@hotwired/stimulus';
import {ago, span} from './time.js';

export default class extends Controller {
  connect() {
    this.tick();
    this.timer = setInterval(() => this.tick(), 1000);
    this.onMorph = () => this.tick();
    document.addEventListener('turbo:morph', this.onMorph);
  }

  disconnect() {
    clearInterval(this.timer);
    document.removeEventListener('turbo:morph', this.onMorph);
  }

  tick() {
    const now = Date.now();
    for (const n of this.element.querySelectorAll('[data-since]')) {
      const text = span(now - Number(n.dataset.since));
      if (n.textContent !== text) n.textContent = text;
    }
    for (const n of this.element.querySelectorAll('[data-ago]')) {
      const text = Number(n.dataset.ago) ? ago(now - Number(n.dataset.ago)) : 'never';
      if (n.textContent !== text) n.textContent = text;
    }
  }
}
