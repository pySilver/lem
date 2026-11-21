// Lem's palette: light or dark, as agterm already chose it for the page. Every page of Lem loads
// this file beside lem.css, in its head, after the stylesheet link, so the board and the onboarding
// page cannot choose apart.
//
// agterm puts its theme stylesheet into each file page it opens, at document start and before the
// page's own styles: `:where(html) { color-scheme: dark; ... }`, or `light`, by its own rule on the
// terminal's background (HtmlOverlayTheme.stylesheet and ThemeBrightness.isDark in agterm's source,
// read on 2026-11-19). A changed theme reloads the page, so one read here is enough; it is read on
// the root once, before this sets the mark that lem.css keys its two palettes on, since a
// color-scheme that lem.css set first would hide agterm's.
//
// A page agterm shows by its address (the board, which lem serve sends) gets no color-scheme, only
// agterm's theme as CSS variables, `--agterm-background` among them (agterm's reference, "a URL page
// keeps browser styling ... only the theme variables"; read on the board's address in agterm 0.41.1 on
// 2026-11-20: `#2E3440` under the theme Nord). There the background's lightness decides, by the
// WCAG luminance at the middle of its range (0.18, a gray of lightness 50), a guess that puts every
// terminal theme's background on its side. A theme changed while such a page is open shows at its
// next load. Anything else (a page opened in a browser, a phone) follows the system's setting, and
// again when it changes.
(() => {
  const root = document.documentElement;
  const mark = dark => { root.dataset.palette = dark ? 'dark' : 'light'; };
  const chosen = getComputedStyle(root).colorScheme.trim();
  if (chosen === 'dark' || chosen === 'light') return mark(chosen === 'dark');
  // agterm's background as a page served by its address has it, dark or light, or null
  const agterm = () => {
    const found = getComputedStyle(root).getPropertyValue('--agterm-background').trim().match(/^#([0-9a-f]{6})/i);
    if (!found) return null;
    const [r, g, b] = [0, 2, 4].map(at => parseInt(found[1].slice(at, at + 2), 16) / 255)
      .map(c => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
    return 0.2126 * r + 0.7152 * g + 0.0722 * b < 0.18;
  };
  const system = matchMedia('(prefers-color-scheme: dark)');
  let theme = agterm();
  if (theme !== null) return mark(theme);
  mark(system.matches);
  const follow = ev => { if (theme === null) mark(ev.matches); };
  system.addEventListener('change', follow);
  // agterm may add its variables after this ran: the first read after the page loaded settles it
  for (const moment of ['DOMContentLoaded', 'load']) {
    addEventListener(moment, () => { if (theme === null && (theme = agterm()) !== null) mark(theme); }, {once: true});
  }
})();
