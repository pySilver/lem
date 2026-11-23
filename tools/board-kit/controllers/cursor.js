// A mark moved by the keys over the items of a view: the cards of the kanban, in their columns, and the
// rows of "Waits for you", one group whose link is each row's verb (on a page for this Mac it may carry
// the agterm controller's jump, which then takes the click and Enter alike) or each stack's summary, whose
// Enter is the browser's own, which opens and closes it. J or
// the down arrow moves it to the next item of its group, K or the up arrow to the one before; H or the
// left arrow and L or the right arrow to the next group with an item you can see (a folded column and an
// empty one are passed over), to its item at the height of the marked one or the closest to it. With no
// mark, the first of these keys marks the first item of the first group you can see. Moving the mark
// moves the focus to the item's link, so Enter is the browser's own press of that link, the same as a
// click; with the focus on no link, Enter clicks the marked item's link. A click on an item's link, or on
// a task's row in the sidebar or in the search (a link outside the view with data-task), moves the mark to that item, so
// Escape after the panel it opened (the hotkeys controller, then panel.js, which gives the focus back to
// the marked card or row) leaves the mark and the focus on it. With no item you can see, the move keys
// stay the browser's.
//
// The mark is the attribute data-js-cur on the item, which a morph keeps (app.js), and its value is the
// id of the item's group. After a morph a marked item that is now in another group loses the mark, and
// an item the morph drew anew in the same group gets it back. No key acts in a field, with Cmd, Ctrl or
// Alt held, or while a menu of the page is open; while the focus is in the task's panel, the arrows and
// Enter stay the panel's.
//
// The values: `item`, the selector of an item; `group`, the selector of a group of items (none: the
// controller's element is the one group); `link`, the selector of the item's link; `pick`, the selector of
// the links whose click marks their item (none: the item's link alone).
import {Controller} from '@hotwired/stimulus';

const DOWN = new Set(['KeyJ', 'ArrowDown']), UP = new Set(['KeyK', 'ArrowUp']);
const LEFT = new Set(['KeyH', 'ArrowLeft']), RIGHT = new Set(['KeyL', 'ArrowRight']);
const ARROWS = new Set(['ArrowDown', 'ArrowUp', 'ArrowLeft', 'ArrowRight']);

const shown = node => node.getClientRects().length > 0;
const middle = node => { const box = node.getBoundingClientRect(); return box.top + box.height / 2; };

export default class extends Controller {
  static values = {item: String, group: String, link: String, pick: String};

  connect() {
    // the item marked last and its group, for an item a morph drew anew
    this.last = null;
    this.onMorph = () => this.keep();
    this.onSide = ev => this.side(ev);
    document.addEventListener('turbo:morph', this.onMorph);
    document.addEventListener('click', this.onSide);
    this.keep();
  }

  disconnect() {
    document.removeEventListener('turbo:morph', this.onMorph);
    document.removeEventListener('click', this.onSide);
  }

  items(scope = this.element) {
    return [...scope.querySelectorAll(this.itemValue)];
  }

  groups() {
    return this.groupValue ? [...this.element.querySelectorAll(this.groupValue)] : [this.element];
  }

  groupOf(item) {
    return this.groupValue ? item.closest(this.groupValue) : this.element;
  }

  // the groups with an item you can see, each with those items
  visible() {
    return this.groups().map(group => ({group, items: this.items(group).filter(shown)})).filter(g => g.items.length);
  }

  current() {
    return this.items().find(item => item.hasAttribute('data-js-cur')) ?? null;
  }

  mark(item, focus = true) {
    for (const other of this.items()) if (other !== item) other.removeAttribute('data-js-cur');
    if (!item) { this.last = null; return; }
    const group = this.groupOf(item)?.id ?? '';
    item.setAttribute('data-js-cur', group);
    this.last = {id: item.id, group};
    if (!focus) return;
    const link = item.querySelector(this.linkValue);
    link?.focus({preventScroll: true});
    item.scrollIntoView({block: 'nearest', inline: 'nearest'});
  }

  // after a morph: the mark stays on its item while the item is in the same group, and goes otherwise
  keep() {
    const cur = this.current();
    const want = cur ? {id: cur.id, group: cur.getAttribute('data-js-cur')} : this.last;
    if (!want) return;
    const item = want.id ? document.getElementById(want.id) : null;
    const same = item && this.element.contains(item) && item.matches(this.itemValue) && (this.groupOf(item)?.id ?? '') === want.group;
    if (same && !item.hasAttribute('data-js-cur')) this.mark(item, false);
    else if (!same) {
      // the focus that went with the mark goes with it, so that Enter opens no card that moved away
      if (item && item.contains(document.activeElement)) document.activeElement.blur();
      this.mark(null);
    }
  }

  // moves the mark by CODE, and says whether there was an item to mark
  move(code) {
    const groups = this.visible();
    if (!groups.length) return false;
    const cur = this.current();
    const at = cur && shown(cur) ? groups.findIndex(g => g.items.includes(cur)) : -1;
    if (at < 0) { this.mark(groups[0].items[0]); return true; }
    const {items} = groups[at];
    const index = items.indexOf(cur);
    if (DOWN.has(code)) this.mark(items[Math.min(items.length - 1, index + 1)]);
    else if (UP.has(code)) this.mark(items[Math.max(0, index - 1)]);
    else {
      const next = groups[at + (RIGHT.has(code) ? 1 : -1)];
      if (!next) return true;
      const height = middle(cur);
      this.mark(next.items.reduce((best, item) => Math.abs(middle(item) - height) < Math.abs(middle(best) - height) ? item : best));
    }
    return true;
  }

  key(ev) {
    if (ev.metaKey || ev.ctrlKey || ev.altKey || ev.defaultPrevented) return;
    const target = ev.target instanceof Element ? ev.target : null;
    if (target?.closest('input, textarea, select, [contenteditable]')) return;
    if (document.querySelector('details[data-menu][open]')) return;
    const inPanel = Boolean(target?.closest('#task'));
    const code = ev.code;
    if (DOWN.has(code) || UP.has(code) || LEFT.has(code) || RIGHT.has(code)) {
      if (inPanel && ARROWS.has(code)) return;
      if (this.move(code)) ev.preventDefault();
    } else if (ev.key === 'Enter' && !inPanel && !target?.closest('a, button, summary')) {
      const link = this.current()?.querySelector(this.linkValue);
      if (!link) return;
      ev.preventDefault();
      link.click();
    }
  }

  // a click on an item's link, or on another link the `pick` value names, marks the item
  pick(ev) {
    const link = ev.target instanceof Element ? ev.target.closest(this.pickValue || this.linkValue) : null;
    const item = link?.closest(this.itemValue);
    if (item && this.element.contains(item)) this.mark(item, false);
  }

  // a click on a task's row in the sidebar or in the search, which opens the task's panel, marks the view's item of that task
  side(ev) {
    const link = ev.target instanceof Element ? ev.target.closest('a[data-task]') : null;
    if (!link || this.element.contains(link)) return;
    const item = this.items().find(node => node.dataset.task === link.dataset.task);
    if (item) this.mark(item, false);
  }
}
