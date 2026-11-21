// The markdown reader of Lem's board, which the markdown controller calls for a document the server put
// escaped into a <template>. A brief or a report written as plain lines keeps its line breaks.
import {Marked} from 'marked';
import {draw} from './charts.js';

// Markdown as a document to read. A document is data: raw HTML in it is shown as text, a link keeps only
// a web, mail or relative address, and a picture loads only from the task's own media folder (the
// server's media route, which sends nothing but a picture); any other picture is its words.
const escape = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const SAFE = /^(https?:|mailto:|#|\.{0,2}\/|[^:]*$)/i;
const PICTURE = /\.(png|jpe?g|gif|webp)$/i;
const marked = new Marked({gfm: true, breaks: true});
// the document being read: the address of its task's media folder and its own folder in the task's
// directory, which a relative picture is read against
let reading = {media: '', dir: ''};

// a path in the task's directory, from a document's folder and a relative path; null when it leaves it
function within(dir, href) {
  const parts = [];
  for (const part of `${dir ? `${dir}/` : ''}${href}`.split('/')) {
    if (part === '' || part === '.') continue;
    if (part === '..') { if (!parts.length) return null; parts.pop(); } else parts.push(part);
  }
  return parts.join('/');
}

// the words of a heading as the end of an address (#the-outcome)
export const slugOf = text => String(text).toLowerCase().replace(/<[^>]*>/g, '').replace(/&[a-z]+;|&#\d+;/g, '').replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-|-$/g, '');

// The one raw HTML a document may hold: a <details> fold with its <summary>, as a pull request's text holds
// the story of an important decision. Each tag is written anew, with no attribute but `open`; any other
// HTML is shown as text.
const FOLD = /^(?:\s*(?:<details(?:\s+open)?\s*>|<\/details\s*>|<summary\s*>[^<]*<\/summary\s*>|<summary\s*>|<\/summary\s*>))+\s*$/i;
function fold(html) {
  if (!FOLD.test(html)) return null;
  return html.replace(/<details(\s+open)?\s*>|<\/details\s*>|<summary\s*>([^<]*)<\/summary\s*>|<summary\s*>|<\/summary\s*>|[^<]+/gi, (tag, open, words) => {
    const low = tag.toLowerCase();
    if (low.startsWith('<details')) return open ? '<details open>' : '<details>';
    if (low.startsWith('</details')) return '</details>';
    if (words !== undefined) return `<summary>${escape(words.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&'))}</summary>`;
    if (low.startsWith('<summary')) return '<summary>';
    if (low.startsWith('</summary')) return '</summary>';
    return tag.trim() ? escape(tag) : tag;
  });
}

// GitHub's alerts, `> [!NOTE]` and the four others, as a callout of the board's: the word goes, and the
// quote takes the alert's color and its title.
const ALERTS = {note: 'Note', tip: 'Tip', important: 'Important', warning: 'Warning', caution: 'Caution'};

marked.use({
  renderer: {
    html(html) {
      const text = typeof html === 'object' ? html.text : html;
      return fold(text) ?? escape(text);
    },
    link(href, title, text) {
      const url = typeof href === 'object' ? href.href : href;
      if (!url || !SAFE.test(url)) return text;
      const out = /^(https?:|mailto:)/i.test(url) ? ' target="_blank" rel="noopener"' : '';
      return `<a href="${escape(url)}"${title ? ` title="${escape(title)}"` : ''}${out}>${text}</a>`;
    },
    image(href, title, text) {
      const url = typeof href === 'object' ? href.href : href;
      const alt = typeof href === 'object' ? href.text : text;
      const path = url && !/^[a-z]+:|^\//i.test(url) && PICTURE.test(url) ? within(reading.dir, url) : null;
      if (!path || !path.startsWith('media/') || !reading.media) return escape(alt || '');
      const src = reading.media + path.slice('media/'.length).split('/').map(encodeURIComponent).join('/');
      return `<a class="pic" href="${escape(src)}" target="_blank" rel="noopener" title="Open the picture at its full size"><img src="${escape(src)}" alt="${escape(alt || '')}" loading="lazy" data-name="${escape(path)}"></a>`;
    },
    heading(text, level) {
      const words = typeof text === 'object' ? this.parser.parseInline(text.tokens) : text;
      const depth = typeof text === 'object' ? text.depth : level;
      return `<h${depth} data-h="${slugOf(words)}">${words}</h${depth}>\n`;
    },
    table(header, body) {
      // a table scrolls sideways in a box of its own, so that no column is squeezed
      if (typeof header === 'object') return false;
      return `<div class="tbl"><table><thead>${header}</thead><tbody>${body}</tbody></table></div>\n`;
    },
  },
});

// After the reader: each table in its scroll box, each picture with its caption as a figure, a
// "before" and an "after" of the same view side by side, and each fenced mermaid block as a chart.
function enhance(root) {
  for (const table of root.querySelectorAll('table')) {
    if (table.parentElement.classList.contains('tbl')) continue;
    const box = document.createElement('div');
    box.className = 'tbl';
    table.replaceWith(box);
    box.append(table);
  }
  for (const quote of root.querySelectorAll('blockquote')) {
    const first = quote.firstElementChild;
    const found = first?.matches('p') && first.firstChild?.nodeType === 3 ? first.firstChild.textContent.match(/^\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*/i) : null;
    if (!found) continue;
    const kind = found[1].toLowerCase();
    first.firstChild.textContent = first.firstChild.textContent.slice(found[0].length);
    if (first.firstChild.textContent === '' && first.childNodes[1]?.localName === 'br') first.childNodes[1].remove();
    if (!first.textContent.trim()) first.remove();
    const title = document.createElement('div');
    title.className = 'alert-title';
    title.textContent = ALERTS[kind];
    quote.classList.add('alert', `alert-${kind}`);
    quote.prepend(title);
  }
  for (const pic of root.querySelectorAll('p > a.pic:first-child')) pic.parentElement.classList.add('figure');
  for (const before of root.querySelectorAll('img[data-name*="-before."]')) {
    const name = before.dataset.name.replace(/-before\.[^.]+$/, '-after.');
    const after = [...root.querySelectorAll('img[data-name*="-after."]')].find(img => img.dataset.name.startsWith(name));
    const one = before.closest('.figure'), two = after?.closest('.figure');
    if (!one || !two || one === two || one.closest('table') || one.closest('.pair')) continue;
    const pair = document.createElement('div');
    pair.className = 'pair';
    one.replaceWith(pair);
    pair.append(one, two);
  }
  for (const code of root.querySelectorAll('pre > code.language-mermaid')) {
    const chart = document.createElement('div');
    chart.className = 'chart';
    chart.dataset.controller = 'chart';
    chart.dataset.src = code.textContent;
    code.parentElement.replaceWith(chart);
  }
  if (root.querySelector('.chart')) draw(root);
}

window.LemKit = {
  markdown(text, where = {}) {
    reading = {media: where.media ?? '', dir: where.dir ?? ''};
    try {
      return marked.parse(String(text ?? ''));
    } finally {
      reading = {media: '', dir: ''};
    }
  },
  enhance,
};
