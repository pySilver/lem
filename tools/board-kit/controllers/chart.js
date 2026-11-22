// A chart of a document (charts.js draws it). In its box it fits the box's width: whole, never larger than
// it was drawn, and only as tall as it then is. When fitting would make its smallest words smaller than
// READABLE, it keeps them at that size instead and scrolls sideways inside its box, with a fade at each
// edge it cuts. A click on it, or its button, opens it large: one view over the whole window, which pans
// with a drag or the arrow keys, zooms with the wheel, a pinch or the keys + and -, fits again with 0,
// and closes with Escape or its button, and the focus goes back where it was. The view is one <dialog>
// for the page, kept through a morph (data-turbo-permanent), and shows a copy of the drawing.
import {Controller} from '@hotwired/stimulus';
import {icon, renamed} from '../charts.js';

// the smallest size in CSS pixels at which a chart's words still read, a guess (the board's own smallest text is 11 px)
const READABLE = 10;
const ZOOM = {min: 0.2, max: 6};

export default class extends Controller {
  connect() {
    this.sized = new ResizeObserver(() => this.fitBox());
    this.sized.observe(this.element);
    this.onDrawn = () => { this.text = null; this.fitBox(); if (view.chart === this) view.show(this); };
    this.element.addEventListener('lem:chart', this.onDrawn);
    this.fitBox();
  }

  disconnect() {
    this.sized.disconnect();
    this.element.removeEventListener('lem:chart', this.onDrawn);
  }

  get box() { return this.element.querySelector(':scope > .chart-svg'); }
  get svg() { return this.box?.querySelector(':scope > svg[data-w]'); }

  // the smallest font size of the drawing's words, in its own units
  smallest(svg) {
    if (this.text) return this.text;
    const sizes = [...svg.querySelectorAll('text, foreignObject div, foreignObject span')].map(node => parseFloat(getComputedStyle(node).fontSize)).filter(n => n > 0);
    this.text = sizes.length ? Math.min(...sizes) : 13;
    return this.text;
  }

  fitBox() {
    const box = this.box, svg = this.svg;
    if (!box || !svg) return;
    const style = getComputedStyle(box);
    const room = box.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
    const width = Number(svg.dataset.w), height = Number(svg.dataset.h);
    if (room <= 0 || !width || !height) return;
    const floor = Math.min(1, READABLE / this.smallest(svg));
    const scale = Math.max(Math.min(1, room / width), floor);
    svg.style.width = `${(width * scale).toFixed(1)}px`;
    svg.style.height = `${(height * scale).toFixed(1)}px`;
    box.classList.toggle('wide', width * scale > room + 1);
    this.edges();
  }

  edges() {
    const box = this.box;
    if (!box) return;
    box.toggleAttribute('data-js-cut-start', box.classList.contains('wide') && box.scrollLeft > 1);
    box.toggleAttribute('data-js-cut-end', box.classList.contains('wide') && box.scrollLeft + box.clientWidth < box.scrollWidth - 1);
  }

  open(ev) {
    if (!this.svg) return;
    ev?.preventDefault();
    view.show(this, ev?.currentTarget instanceof HTMLElement ? ev.currentTarget : this.element.querySelector('.chart-open'));
  }
}

// ---- the chart opened large: one view for the page ----

// a copy of a drawing whose ids are its own, so that its styles, arrows and markers do not take the
// original's and a page holds no id twice
function copyOf(svg) {
  const copy = renamed(svg.cloneNode(true), id => `${id}-large`);
  copy.removeAttribute('style');
  return copy;
}

const view = {
  chart: null, scale: 1, x: 0, y: 0, w: 0, h: 0, back: null,

  build() {
    let dialog = document.getElementById('chart-large');
    if (dialog) return dialog;
    dialog = document.createElement('dialog');
    dialog.id = 'chart-large';
    dialog.className = 'chart-large';
    dialog.setAttribute('data-turbo-permanent', '');
    dialog.setAttribute('aria-label', 'The chart, large');
    dialog.innerHTML = `<div class="cl-bar"><span class="cl-title">Chart</span><span class="cl-hint">drag to move · wheel or pinch to zoom · Escape closes</span>
      <span class="cl-tools"><button type="button" class="ibtn" data-zoom="out" title="Smaller · key -" aria-label="Smaller">${icon('minus')}</button>
      <button type="button" class="cl-pct" data-zoom="fit" title="Fit the window · key 0" aria-label="Fit the window">100%</button>
      <button type="button" class="ibtn" data-zoom="in" title="Larger · key +" aria-label="Larger">${icon('plus')}</button>
      <button type="button" class="ibtn" data-zoom="close" title="Close · Escape" aria-label="Close the chart">${icon('xmark')}</button></span></div>
      <div class="cl-stage" tabindex="0" aria-label="The chart: the arrow keys move it, + and - zoom"><div class="cl-pane"></div></div>`;
    document.body.append(dialog);
    this.wire(dialog);
    return dialog;
  },

  wire(dialog) {
    const stage = dialog.querySelector('.cl-stage');
    dialog.addEventListener('click', ev => {
      const zoom = ev.target.closest?.('[data-zoom]')?.dataset.zoom;
      if (zoom === 'close') dialog.close();
      else if (zoom === 'fit') this.fitWindow();
      else if (zoom) this.zoomBy(zoom === 'in' ? 1.25 : 0.8);
    });
    dialog.addEventListener('close', () => { this.chart = null; dialog.querySelector('.cl-pane').replaceChildren(); this.back?.focus?.({preventScroll: true}); this.back = null; });
    dialog.addEventListener('keydown', ev => {
      // the board's own keys (a view, a tab, Escape that closes the panel) wait while the chart is open
      ev.stopPropagation();
      if (ev.metaKey || ev.ctrlKey || ev.altKey) return;
      const step = 60;
      const act = {'+': () => this.zoomBy(1.25), '=': () => this.zoomBy(1.25), '-': () => this.zoomBy(0.8), 0: () => this.fitWindow(),
                   ArrowLeft: () => this.move(step, 0), ArrowRight: () => this.move(-step, 0), ArrowUp: () => this.move(0, step), ArrowDown: () => this.move(0, -step)}[ev.key];
      if (act && !ev.target.closest?.('button')) { ev.preventDefault(); act(); }
    });
    stage.addEventListener('wheel', ev => {
      ev.preventDefault();
      const rect = stage.getBoundingClientRect();
      // a pinch on a trackpad comes as a wheel with ctrlKey, in small steps
      this.zoomBy(Math.exp(-ev.deltaY * (ev.ctrlKey ? 0.01 : 0.0015)), ev.clientX - rect.left, ev.clientY - rect.top);
    }, {passive: false});
    const pointers = new Map();
    let pinch = null;
    stage.addEventListener('pointerdown', ev => {
      stage.setPointerCapture(ev.pointerId);
      pointers.set(ev.pointerId, {x: ev.clientX, y: ev.clientY});
      stage.classList.add('drag');
    });
    stage.addEventListener('pointermove', ev => {
      const was = pointers.get(ev.pointerId);
      if (!was) return;
      const now = {x: ev.clientX, y: ev.clientY};
      if (pointers.size === 2) {
        const other = [...pointers.entries()].find(([id]) => id !== ev.pointerId)[1];
        const apart = Math.hypot(now.x - other.x, now.y - other.y);
        const rect = stage.getBoundingClientRect();
        if (pinch) this.zoomBy(apart / pinch, (now.x + other.x) / 2 - rect.left, (now.y + other.y) / 2 - rect.top);
        pinch = apart;
      } else {
        this.move(now.x - was.x, now.y - was.y);
      }
      pointers.set(ev.pointerId, now);
    });
    const up = ev => { pointers.delete(ev.pointerId); pinch = null; if (!pointers.size) stage.classList.remove('drag'); };
    stage.addEventListener('pointerup', up);
    stage.addEventListener('pointercancel', up);
  },

  show(chart, back = null) {
    const dialog = this.build();
    const svg = chart.svg;
    if (!svg) return;
    this.chart = chart;
    if (back) this.back = back;
    const pane = dialog.querySelector('.cl-pane');
    const copy = copyOf(svg);
    this.w = Number(svg.dataset.w);
    this.h = Number(svg.dataset.h);
    copy.style.width = `${this.w}px`;
    copy.style.height = `${this.h}px`;
    pane.replaceChildren(copy);
    // the chart's name: its decision's, else its card's heading
    const where = chart.element.closest('details.dec')?.querySelector('.dec-what') ?? chart.element.closest('.card, section')?.querySelector('h2, .eyebrow');
    const named = where?.textContent?.trim();
    dialog.querySelector('.cl-title').textContent = named || 'Chart';
    dialog.setAttribute('aria-label', named ? `The chart: ${named}` : 'The chart');
    if (!dialog.open) dialog.showModal();
    dialog.querySelector('.cl-stage').focus({preventScroll: true, focusVisible: false});
    this.fitWindow();
  },

  fitWindow() {
    const stage = this.stage();
    if (!stage) return;
    const room = {w: stage.clientWidth - 48, h: stage.clientHeight - 48};
    this.scale = Math.min(2, Math.max(ZOOM.min, Math.min(room.w / this.w, room.h / this.h)));
    this.x = (stage.clientWidth - this.w * this.scale) / 2;
    this.y = (stage.clientHeight - this.h * this.scale) / 2;
    this.paint();
  },

  stage() { return document.querySelector('#chart-large .cl-stage'); },

  zoomBy(factor, atX, atY) {
    const stage = this.stage();
    if (!stage) return;
    const x = atX ?? stage.clientWidth / 2, y = atY ?? stage.clientHeight / 2;
    const next = Math.min(ZOOM.max, Math.max(ZOOM.min, this.scale * factor));
    // the point under the pointer stays where it is
    this.x = x - (x - this.x) * (next / this.scale);
    this.y = y - (y - this.y) * (next / this.scale);
    this.scale = next;
    this.paint();
  },

  move(dx, dy) {
    this.x += dx;
    this.y += dy;
    this.paint();
  },

  paint() {
    const dialog = document.getElementById('chart-large');
    if (!dialog) return;
    dialog.querySelector('.cl-pane').style.transform = `translate(${this.x.toFixed(1)}px, ${this.y.toFixed(1)}px) scale(${this.scale.toFixed(4)})`;
    dialog.querySelector('.cl-pct').textContent = `${Math.round(this.scale * 100)}%`;
  },
};
