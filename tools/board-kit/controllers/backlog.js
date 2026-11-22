// The backlog's filter and keys. The filter is in the address (`?q=`, `worth=`, `only=`), and this
// controller holds its one rule: the server draws every item, with the chip the address picks
// (lem_board_pages.backlog_filter), and the list shows only the items where every word typed is in the
// item's title, name, place or text, whose worth (data-worth) is the one picked, and with the fact picked
// (data-stale, data-new). Typing filters at once, with no request (200 items take a frame), and the
// address follows with no visit, so that a shared link and a refresh show the same list. A chip (a worth,
// a fact, All) is a visit of its address, with the words typed so far. J and K move a cursor over the
// items shown, Enter opens or closes the one under it, S copies the line that starts a task from it,
// and / goes to the field. The item the address names (#item-SLUG, as the search's row of an item links to it) opens, takes the
// cursor and comes into view, when the page comes and when the address's # changes.
import {Controller} from '@hotwired/stimulus';

export default class extends Controller {
  static targets = ['query', 'item', 'group', 'none', 'count', 'chip'];
  static values = {base: String};

  connect() {
    this.onMorph = () => this.filter(false);
    this.onHash = () => this.named();
    document.addEventListener('turbo:morph', this.onMorph);
    window.addEventListener('hashchange', this.onHash);
    this.filter(false);
    this.named();
  }

  disconnect() {
    document.removeEventListener('turbo:morph', this.onMorph);
    window.removeEventListener('hashchange', this.onHash);
  }

  // the item the address names, open, under the cursor and in view; words in the field that hide it go, and the
  // address keeps its # (no history entry)
  named() {
    let id = '';
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    const item = id.startsWith('item-') ? this.itemTargets.find(node => node.id === id) : null;
    if (!item) return;
    if (item.hasAttribute('data-js-out') && this.hasQueryTarget && this.queryTarget.value) { this.queryTarget.value = ''; this.filter(false); }
    item.open = true;
    for (const other of this.itemTargets) other.toggleAttribute('data-js-cur', other === item);
    requestAnimationFrame(() => item.scrollIntoView({block: 'start'}));
  }

  // the filter as the address has it
  state() {
    const query = new URLSearchParams(location.search);
    return {q: this.hasQueryTarget ? this.queryTarget.value : query.get('q') ?? '', worth: query.get('worth') ?? '', only: query.get('only') ?? ''};
  }

  address(state) {
    const query = new URLSearchParams();
    for (const key of ['q', 'worth', 'only']) if (state[key]?.trim()) query.set(key, state[key].trim());
    const text = query.toString();
    return `${this.baseValue || location.pathname}${text ? `?${text}` : ''}`;
  }

  filter(follow = true) {
    const state = this.state();
    const words = state.q.trim().toLowerCase().split(/\s+/).filter(Boolean);
    let shown = 0;
    for (const item of this.itemTargets) {
      const hay = words.length ? this.hay(item) : '';
      const hit = words.every(w => hay.includes(w)) && (!state.worth || item.dataset.worth === state.worth)
        && (state.only !== 'stale' || item.dataset.stale) && (state.only !== 'new' || item.dataset.new);
      item.toggleAttribute('data-js-out', !hit);
      if (hit) shown++;
    }
    for (const group of this.groupTargets) group.toggleAttribute('data-js-out', !group.querySelector('[data-backlog-target="item"]:not([data-js-out])'));
    const filtered = Boolean(words.length || state.worth || state.only);
    if (this.hasNoneTarget) this.noneTarget.toggleAttribute('data-js-out', !(filtered && !shown && this.itemTargets.length));
    if (this.hasCountTarget) this.countTarget.textContent = filtered ? `${shown} of ${this.itemTargets.length} shown · ` : '';
    // the chips carry the words typed, so that a pick keeps them
    for (const chip of this.chipTargets) {
      const {key, value} = chip.dataset;
      const want = key === 'all' ? {q: state.q} : {...state, [key]: state[key] === value ? '' : value};
      chip.href = this.address(want);
    }
    if (follow) {
      const url = this.address(state);
      if (url !== location.pathname + location.search) history.replaceState(history.state, '', url);
    }
    const cur = this.current();
    if (cur?.hasAttribute('data-js-out')) cur.removeAttribute('data-js-cur');
  }

  // what the words typed are looked for in: the item's title, its name, its place and its text
  hay(item) {
    const text = item.querySelector('.bl-text template')?.content.textContent ?? '';
    return [item.querySelector('.bl-title')?.textContent, item.id.replace(/^item-/, ''), item.querySelector('.bl-where')?.textContent, text].join(' ').toLowerCase();
  }

  pick(ev) {
    if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.button > 0) return;
    ev.preventDefault();
    window.Turbo.visit(ev.currentTarget.href, {action: 'replace'});
  }

  clear(ev) {
    if (ev.key === 'Escape') {
      ev.preventDefault();
      if (this.queryTarget.value) { this.queryTarget.value = ''; this.filter(); } else this.queryTarget.blur();
    } else if (ev.key === 'Enter' || ev.key === 'ArrowDown') {
      ev.preventDefault();
      this.queryTarget.blur();
      this.move(1);
    }
  }

  current() {
    return this.itemTargets.find(item => item.hasAttribute('data-js-cur')) ?? null;
  }

  move(step) {
    const shown = this.itemTargets.filter(item => !item.hasAttribute('data-js-out'));
    if (!shown.length) return;
    const at = shown.indexOf(this.current());
    const next = shown[at < 0 ? (step > 0 ? 0 : shown.length - 1) : Math.min(shown.length - 1, Math.max(0, at + step))];
    for (const item of this.itemTargets) item.toggleAttribute('data-js-cur', item === next);
    next.scrollIntoView({block: 'nearest'});
  }

  key(ev) {
    if (ev.metaKey || ev.ctrlKey || ev.altKey || ev.defaultPrevented) return;
    if (ev.target instanceof Element && ev.target.closest('input, textarea, select')) return;
    const cur = this.current();
    const act = fn => { ev.preventDefault(); fn(); };
    if (ev.code === 'KeyJ' || ev.key === 'ArrowDown') act(() => this.move(1));
    else if (ev.code === 'KeyK' || ev.key === 'ArrowUp') act(() => this.move(-1));
    else if (ev.code === 'Slash' && this.hasQueryTarget) act(() => { this.queryTarget.focus(); this.queryTarget.select(); });
    else if (ev.key === 'Enter' && cur && !ev.target.closest?.('button, a, summary')) act(() => { cur.open = !cur.open; });
    else if (ev.code === 'KeyS' && cur) {
      const copy = cur.querySelector('.bl-actions [data-controller~="copy"]');
      if (copy) act(() => { cur.open = true; copy.click(); });
    }
  }
}
