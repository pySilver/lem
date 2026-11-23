// The search over every card of the workspace (search_box in lem_board_pages.py). Cmd-K, or Ctrl-K off the
// Mac, opens it with the cursor in its field, also while the focus is in another field; so does a search
// button of the bars (data-search-open), which stands outside the box and is caught by a click on the
// document. With nothing typed the box shows the tasks that have not ended (data-open), in the order the
// server drew them; with letters typed, every card whose title holds them in order (`match`), the closest
// together first and the drawn order between two of the same. The first row shown is marked, the arrows
// move the mark, and Enter or a click picks a row: the box closes and the row's link is followed, so a task
// opens in its panel as its card does and a backlog item opens the Backlog view on that item (backlog.js
// reads #item-KEY). Escape, or a click beside the box, closes it with no pick and gives the focus back.
//
// The keys are read on window in the capture phase, before every controller's keydown@window (drawer.js's
// Escape, cursor.js, backlog.js, hotkeys.js), and a key the box takes stops there, so the panel and the
// drawer stay as they were. While the box is open the focus stays in it, so no key of the board acts
// behind it. The box's state is data-js-open and each row's data-js-out and data-js-cur, which a morph
// keeps (app.js); the field is data-turbo-permanent, so what the owner typed stays too; and a morph draws
// the rows anew in the server's order, so they are filtered and ordered again after it.
import {Controller} from '@hotwired/stimulus';

// The match rule: null when the title does not hold the letters typed in their order (case folded, the
// spaces typed taken out), else the length of the shortest stretch of the title that holds them, which
// orders the results ("card" is a stretch of 4 in "Board card search" and of 16 in "Clear a reported
// deadline"). Nothing typed matches every title with 0.
export function match(query, title) {
  const letters = String(query).toLowerCase().replace(/\s+/g, '');
  if (!letters) return 0;
  const text = String(title).toLowerCase();
  let best = null;
  for (let start = text.indexOf(letters[0]); start >= 0; start = text.indexOf(letters[0], start + 1)) {
    let at = start;
    for (let i = 1; i < letters.length && at >= 0; i++) at = text.indexOf(letters[i], at + 1);
    // no later start holds them all either
    if (at < 0) break;
    if (best === null || at - start + 1 < best) best = at - start + 1;
  }
  return best;
}

// the rule, for a check in the page (tests/lem-board-keys.sh)
window.LemKit = Object.assign(window.LemKit ?? {}, {match});

const plainClick = ev => !(ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey || ev.button > 0);

export default class extends Controller {
  static targets = ['query', 'row', 'none'];

  connect() {
    // the rows in the order the server drew them; the DOM holds them in the order shown
    this.drawn = this.rowTargets;
    // where the focus was when the box opened, for Escape
    this.back = null;
    this.onKey = ev => this.key(ev);
    this.onOpen = ev => {
      const button = ev.target instanceof Element ? ev.target.closest('[data-search-open]') : null;
      if (button) { ev.preventDefault(); this.open(); }
    };
    this.onMorph = () => {
      this.drawn = this.rowTargets;
      if (this.isOpen) this.filter(true);
    };
    this.onFocus = ev => { if (this.isOpen && ev.target instanceof Node && !this.element.contains(ev.target)) this.queryTarget.focus(); };
    // a page Turbo keeps for the back button keeps no open box
    this.onCache = () => this.element.removeAttribute('data-js-open');
    window.addEventListener('keydown', this.onKey, true);
    document.addEventListener('click', this.onOpen);
    document.addEventListener('turbo:morph', this.onMorph);
    document.addEventListener('focusin', this.onFocus);
    document.addEventListener('turbo:before-cache', this.onCache);
    if (this.isOpen) this.filter(true);
  }

  disconnect() {
    window.removeEventListener('keydown', this.onKey, true);
    document.removeEventListener('click', this.onOpen);
    document.removeEventListener('turbo:morph', this.onMorph);
    document.removeEventListener('focusin', this.onFocus);
    document.removeEventListener('turbo:before-cache', this.onCache);
  }

  get isOpen() {
    return this.element.hasAttribute('data-js-open');
  }

  open() {
    if (!this.isOpen) {
      const from = document.activeElement;
      this.back = from instanceof HTMLElement && from !== document.body && !this.element.contains(from) ? from : null;
      this.element.setAttribute('data-js-open', '');
      this.filter();
    }
    this.queryTarget.focus();
    this.queryTarget.select();
  }

  // closes the box and empties its field; `restore` gives the focus back to where it was (Escape), while a
  // pick leaves it to what the pick opens (panel.js gives it to the panel's title)
  close(restore) {
    if (!this.isOpen) return;
    this.element.removeAttribute('data-js-open');
    this.queryTarget.value = '';
    const back = this.back;
    this.back = null;
    if (restore && back?.isConnected) back.focus({preventScroll: true});
    else if (this.element.contains(document.activeElement)) document.activeElement.blur();
  }

  key(ev) {
    if (ev.code === 'KeyK' && (ev.metaKey || ev.ctrlKey) && !ev.altKey && !ev.shiftKey) {
      // preventDefault keeps the key from the browser's own search (Firefox)
      ev.preventDefault();
      ev.stopImmediatePropagation();
      this.open();
      return;
    }
    if (!this.isOpen || ev.isComposing) return;
    const take = () => { ev.preventDefault(); ev.stopImmediatePropagation(); };
    if (ev.key === 'Escape') { take(); this.close(true); }
    else if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') { take(); this.move(ev.key === 'ArrowDown' ? 1 : -1); }
    else if (ev.key === 'Enter') {
      take();
      // the row's own click, which closes the box (click) and which Turbo follows
      this.current()?.click();
    }
  }

  input() {
    this.filter();
  }

  // a click on a row follows its link and closes the box; a click beside the box closes it
  click(ev) {
    const row = ev.target instanceof Element ? ev.target.closest('[data-search-target="row"]') : null;
    if (row) { if (plainClick(ev)) this.close(false); }
    else if (ev.target === this.element) this.close(true);
  }

  // shows the rows the field's letters match, in their order, and marks the first; `keep` keeps the mark on
  // its row while that row is still shown (after a morph)
  filter(keep = false) {
    const query = this.queryTarget.value;
    const shown = query.replace(/\s+/g, '')
      ? this.drawn.map((row, at) => ({row, at, span: match(query, row.dataset.title ?? '')}))
        .filter(hit => hit.span !== null).sort((a, b) => a.span - b.span || a.at - b.at).map(hit => hit.row)
      : this.drawn.filter(row => row.dataset.open);
    const on = new Set(shown);
    for (const row of this.drawn) row.toggleAttribute('data-js-out', !on.has(row));
    const order = [...shown, ...this.drawn.filter(row => !on.has(row))];
    const now = this.rowTargets;
    if (order.some((row, i) => now[i] !== row)) for (const row of order) this.noneTarget.before(row);
    this.noneTarget.toggleAttribute('data-js-out', Boolean(shown.length || !query.trim()));
    const cur = keep ? this.current() : null;
    this.mark(cur && on.has(cur) ? cur : shown[0] ?? null);
  }

  current() {
    return this.rowTargets.find(row => row.hasAttribute('data-js-cur') && !row.hasAttribute('data-js-out')) ?? null;
  }

  mark(row) {
    for (const other of this.rowTargets) {
      other.toggleAttribute('data-js-cur', other === row);
      other.setAttribute('aria-selected', other === row ? 'true' : 'false');
    }
    if (!row) { this.queryTarget.removeAttribute('aria-activedescendant'); return; }
    this.queryTarget.setAttribute('aria-activedescendant', row.id);
    row.scrollIntoView({block: 'nearest'});
  }

  move(step) {
    const shown = this.rowTargets.filter(row => !row.hasAttribute('data-js-out'));
    if (!shown.length) return;
    const at = shown.indexOf(this.current());
    this.mark(shown[at < 0 ? 0 : Math.min(shown.length - 1, Math.max(0, at + step))]);
  }
}
