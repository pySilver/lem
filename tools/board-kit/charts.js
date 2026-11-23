// The board's charts: a fenced `mermaid` block of a document, drawn in the board's palette. The diagram
// library is large (vendor/mermaid.min.js, mermaid 11.12.0), so a page loads it only when it has a chart:
// the first chart adds its <script>, from the address that the document holding it names
// (`data-lem-mermaid`, which the server writes only on a document with a chart), one of the server's own
// files. Each chart is drawn once for its palette, and again when the palette changes (light or dark).
// The drawing keeps its own size as `data-w` and `data-h`, and the chart controller fits it to its box
// and opens it large. Under the drawing a "source" disclosure holds the chart's text; a chart that does
// not parse shows that text with the parser's first line.
let loading = null
let made = 0

function library () {
  if (window.mermaid) return Promise.resolve(window.mermaid)
  if (loading) return loading
  const src = document.querySelector('[data-lem-mermaid]')?.dataset.lemMermaid
  if (!src) return Promise.resolve(null)
  loading = new Promise(resolve => {
    const script = document.createElement('script')
    script.src = src
    script.async = true
    script.dataset.turboTrack = 'dynamic'
    script.onload = () => resolve(window.mermaid ?? null)
    script.onerror = () => { loading = null; resolve(null) }
    document.head.append(script)
  })
  return loading
}

const palette = () => document.documentElement.dataset.palette === 'dark' ? 'dark' : 'light'

// the board's palette as mermaid's theme variables, read from lem.css at the time of the drawing
function theme () {
  const css = getComputedStyle(document.documentElement)
  const v = name => css.getPropertyValue(name).trim()
  const dark = palette() === 'dark'
  return {
    startOnLoad: false,
    securityLevel: 'strict',
    theme: 'base',
    darkMode: dark,
    htmlLabels: false,
    fontFamily: v('--sans') || 'system-ui, sans-serif',
    flowchart: { useMaxWidth: false, htmlLabels: false, padding: 12, nodeSpacing: 36, rankSpacing: 44, curve: 'basis' },
    sequence: { useMaxWidth: false, mirrorActors: false, boxMargin: 8, messageFontSize: 13, actorFontSize: 13, noteFontSize: 13 },
    state: { useMaxWidth: false },
    themeVariables: {
      darkMode: dark,
      fontSize: '13.5px',
      fontFamily: v('--sans'),
      background: v('--bg'),
      mainBkg: v('--card'),
      primaryColor: v('--card'),
      primaryTextColor: v('--fg'),
      primaryBorderColor: v('--line-strong'),
      secondaryColor: v('--card-hi'),
      secondaryTextColor: v('--fg'),
      secondaryBorderColor: v('--line-strong'),
      tertiaryColor: v('--bg'),
      tertiaryTextColor: v('--fg'),
      tertiaryBorderColor: v('--line'),
      lineColor: v('--dim'),
      textColor: v('--fg'),
      nodeBorder: v('--line-strong'),
      clusterBkg: v('--bg'),
      clusterBorder: v('--line'),
      edgeLabelBackground: v('--bg'),
      titleColor: v('--fg'),
      actorBkg: v('--card'),
      actorBorder: v('--line-strong'),
      actorTextColor: v('--fg'),
      actorLineColor: v('--line-strong'),
      signalColor: v('--dim'),
      signalTextColor: v('--fg'),
      labelBoxBkgColor: v('--card'),
      labelBoxBorderColor: v('--line-strong'),
      labelTextColor: v('--fg'),
      loopTextColor: v('--fg'),
      noteBkgColor: v('--card-hi'),
      noteBorderColor: v('--line-strong'),
      noteTextColor: v('--fg'),
      activationBkgColor: v('--card-hi'),
      activationBorderColor: v('--line-strong'),
      sequenceNumberColor: v('--bg'),
      stateBkg: v('--card'),
      stateLabelColor: v('--fg'),
      compositeBackground: v('--bg'),
      altBackground: v('--card-hi'),
      transitionColor: v('--dim'),
    },
  }
}

// an icon of the page's sprite (the server puts the chart's icons into a page that has a chart): the
// panel's own symbols when the chart is in the panel, else the page's
export function icon (name) {
  const id = document.getElementById(`t-i-${name}`) ? `t-i-${name}` : `i-${name}`
  return `<svg class="ic" aria-hidden="true"><use href="#${id}"></use></svg>`
}

function frame (chart) {
  if (chart.querySelector(':scope > .chart-svg')) return
  const open = document.createElement('button')
  open.type = 'button'
  open.className = 'chart-open'
  open.title = 'Open the chart large'
  open.setAttribute('aria-label', 'Open the chart large')
  open.dataset.action = 'chart#open'
  open.innerHTML = icon('expand')
  const svg = document.createElement('div')
  svg.className = 'chart-svg'
  svg.dataset.action = 'click->chart#open scroll->chart#edges'
  const source = document.createElement('details')
  source.className = 'chart-src'
  const summary = document.createElement('summary')
  summary.textContent = 'source'
  const pre = document.createElement('pre')
  pre.textContent = chart.dataset.src
  source.append(summary, pre)
  chart.append(open, svg, source)
}

// Gives every id inside a drawing a new name (`to(id)`), with each reference to it in an attribute or in
// the drawing's <style>: mermaid names the nodes of each chart alike (`flowchart-A-0`), and a page holds
// no id twice.
export function renamed (svg, to) {
  const ids = new Map([svg, ...svg.querySelectorAll('[id]')].filter(n => n.id).map(n => [n.id, to(n.id)]).filter(([a, b]) => a !== b))
  if (!ids.size) return svg
  const swap = text => text.replace(/#([\w-]+)/g, (all, id) => ids.has(id) ? `#${ids.get(id)}` : all)
  for (const node of [svg, ...svg.querySelectorAll('*')]) {
    for (const attr of [...node.attributes]) {
      if (attr.name === 'id') { if (ids.has(attr.value)) node.id = ids.get(attr.value) } else if (attr.value.includes('#')) node.setAttribute(attr.name, swap(attr.value))
    }
    if (node.localName === 'style') node.textContent = swap(node.textContent)
  }
  return svg
}

// The drawing as the chart controller sizes it: its own width and height from its viewBox, and no size
// of mermaid's, so that nothing but the controller sets how large it shows; and its ids its own.
function settle (svg) {
  renamed(svg, id => (id === svg.id || id.startsWith(`${svg.id}`) ? id : `${svg.id}-${id}`))
  const box = svg.viewBox?.baseVal
  const width = box?.width || svg.getBBox?.().width || 0
  const height = box?.height || svg.getBBox?.().height || 0
  svg.removeAttribute('width')
  svg.removeAttribute('height')
  svg.style.removeProperty('max-width')
  svg.dataset.w = String(width)
  svg.dataset.h = String(height)
}

function failed (chart, why) {
  chart.classList.add('chart-bad')
  chart.dataset.drawn = palette()
  chart.replaceChildren()
  const said = document.createElement('div')
  said.className = 'chart-err'
  said.textContent = `The chart did not draw: ${why}`
  const pre = document.createElement('pre')
  pre.textContent = chart.dataset.src
  chart.append(said, pre)
}

// draws the charts under ROOT that are not drawn for the palette shown, one after another
let queue = Promise.resolve()
export function draw (root = document) {
  const charts = [...root.querySelectorAll('.chart[data-src]')].filter(c => c.dataset.drawn !== palette() && !c.classList.contains('chart-bad'))
  if (!charts.length) return queue
  for (const chart of charts) frame(chart)
  queue = queue.then(async () => {
    const mermaid = await library()
    if (!mermaid) { for (const chart of charts) failed(chart, 'the diagram library did not load'); return }
    mermaid.initialize(theme())
    for (const chart of charts) {
      if (!chart.isConnected || chart.dataset.drawn === palette()) continue
      try {
        const { svg } = await mermaid.render(`lem-chart-${++made}`, chart.dataset.src)
        const box = chart.querySelector(':scope > .chart-svg')
        box.innerHTML = svg
        const drawn = box.querySelector('svg')
        if (drawn) settle(drawn)
        chart.dataset.drawn = palette()
        chart.dispatchEvent(new CustomEvent('lem:chart', { bubbles: false }))
      } catch (error) {
        failed(chart, String(error?.message ?? error).split('\n').find(line => line.trim()) ?? 'it does not parse')
      } finally {
        // mermaid leaves a measuring element in the body when a render fails
        document.getElementById(`dlem-chart-${made}`)?.remove()
      }
    }
  })
  return queue
}

// a change of the palette (lem.js sets data-palette) draws every chart of the page again
new MutationObserver(() => draw(document)).observe(document.documentElement, { attributes: true, attributeFilter: ['data-palette'] })
