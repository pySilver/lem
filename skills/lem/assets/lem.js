// Lem's palette: light or dark, as agterm already chose it for the page. Every page of Lem loads
// this file beside lem.css, in its head, after the stylesheet link, so the board and the onboarding
// page cannot choose apart.
//
// agterm puts its theme stylesheet into each file page it opens, at document start and before the
// page's own styles: `:where(html) { color-scheme: dark; ... }`, or `light`, by its own rule on the
// terminal's background (HtmlOverlayTheme.stylesheet and ThemeBrightness.isDark in agterm's source,
// read on 2026-11-19). A changed theme reloads the page, so one read here is enough. Lem computes no
// luminance and uses no color of agterm's: it reads the scheme on the root once, before it sets the
// mark that lem.css keys its two palettes on, since a color-scheme that lem.css set first would hide
// agterm's. Anything but `dark` or `light` (no agterm theme, a page opened in a browser) leaves the
// choice to the system's setting, which the page follows when it changes.
(() => {
  const root = document.documentElement;
  const chosen = getComputedStyle(root).colorScheme.trim();
  const mark = dark => { root.dataset.palette = dark ? 'dark' : 'light'; };
  if (chosen === 'dark' || chosen === 'light') return mark(chosen === 'dark');
  const system = matchMedia('(prefers-color-scheme: dark)');
  mark(system.matches);
  system.addEventListener('change', ev => mark(ev.matches));
})();
