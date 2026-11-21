// What only agterm does, on a page the server drew for this Mac (its body carries the address of the
// acts, data-agterm-url-value): go to a task's session. agterm gives a page served over http no bridge,
// so the page asks the server, which runs agtermctl (serve.py `agterm_act`) and answers with what it did
// or why not.
import {Controller} from '@hotwired/stimulus';

export default class extends Controller {
  static values = {url: String};

  async post(act, body) {
    const reply = await fetch(`${this.urlValue}/${act}`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body), cache: 'no-store'});
    let answer = null;
    try { answer = await reply.json(); } catch { /* the server said no JSON */ }
    if (!reply.ok || !answer?.done) throw new Error(answer?.said ?? `the server answered ${reply.status}`);
    return answer.said;
  }

  async jump(ev) {
    if (!this.urlValue || !ev.params.session) return;
    ev.preventDefault();
    const at = ev.currentTarget;
    try { await this.post('select', {session: ev.params.session}); } catch (err) { this.note(at, `It did not switch: ${err?.message ?? err}`, true); }
  }

  // why the jump failed, in a note of its own after its button
  note(at, text, bad = false) {
    const place = at.nextElementSibling?.matches('[data-js-note]') ? at.nextElementSibling : document.createElement('span');
    place.setAttribute('data-js-note', '');
    place.className = 'bl-note';
    at.after(place);
    place.textContent = text;
    place.classList.toggle('bad', bad);
  }
}
