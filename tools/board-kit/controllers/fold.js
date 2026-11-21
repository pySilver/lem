// Fold a column of the kanban to a strip, the sidebar to a rail, or unfold a task's header on a phone or
// in a short window (its ask, facts and chips under "Details"), and keep it in the cookie: the change
// shows at once, and the server renders it so from the next request on, so a morph keeps it.
import {Controller} from '@hotwired/stimulus';
import {read, write} from './prefs.js';

export default class extends Controller {
  column(ev) {
    const key = ev.params.key;
    if (!key) return;
    // a click inside an open column is the card's or the link's: only a folded strip, or the column's own button, folds
    const strip = ev.currentTarget.closest('.col');
    if (ev.currentTarget === strip && !strip.classList.contains('folded')) return;
    ev.preventDefault();
    ev.stopPropagation();
    const folded = new Set(read().folded ?? []);
    folded.has(key) ? folded.delete(key) : folded.add(key);
    write({folded: [...folded]});
    const column = document.getElementById(`col-${key}`);
    column?.classList.toggle('folded', folded.has(key));
    const button = column?.querySelector('[data-fold-key-param]');
    if (button) button.title = folded.has(key) ? 'Unfold the column' : 'Fold the column';
  }

  side(ev) {
    ev.preventDefault();
    const railed = !read().rail;
    write({rail: railed});
    this.element.classList.toggle('railed', railed);
  }

  head(ev) {
    ev.preventDefault();
    const head = ev.currentTarget.closest('.p-head');
    if (!head) return;
    const open = !head.classList.contains('open');
    write({head: open});
    head.classList.toggle('open', open);
    ev.currentTarget.setAttribute('aria-expanded', String(open));
  }
}
