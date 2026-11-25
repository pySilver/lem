// The first Mermaid fence loads the board's local Pele asset. The chart keeps its source and
// intrinsic size for the large view, and takes its colors from the board's CSS.
let loading = null
let made = 0

function library () {
  if (window.pele) return Promise.resolve(window.pele)
  if (loading) return loading
  const kit = document.querySelector('script[src$="/vendor/board-app.js"]')
  if (!kit) return Promise.reject(new Error('The board kit has no asset address'))
  loading = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = new URL('pele.js', kit.src).href
    script.async = true
    script.dataset.turboTrack = 'dynamic'
    script.onload = () => {
      if (window.pele) resolve(window.pele)
      else reject(new Error('Pele did not start'))
    }
    script.onerror = () => {
      script.remove()
      reject(new Error('Pele did not load'))
    }
    document.head.append(script)
  }).catch(error => {
    loading = null
    throw error
  })
  return loading
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
// the drawing's <style>: a renderer can name the nodes of each chart alike (`flowchart-A-0`), and a page holds
// no id twice.
export function renamed (svg, to) {
  const ids = new Map([svg, ...svg.querySelectorAll('[id]')].filter(n => n.id).map(n => [n.id, to(n.id)]).filter(([a, b]) => a !== b))
  if (!ids.size) return svg
  const swap = text => text.replace(/#([\w-]+)/g, (all, id) => ids.has(id) ? `#${ids.get(id)}` : all)
  for (const node of [svg, ...svg.querySelectorAll('*')]) {
    for (const attr of [...node.attributes]) {
      if (attr.name === 'id') { if (ids.has(attr.value)) node.id = ids.get(attr.value) } else if (attr.value.includes('#')) node.setAttribute(attr.name, swap(attr.value))
      else if (['aria-labelledby', 'aria-describedby'].includes(attr.name)) {
        node.setAttribute(attr.name, attr.value.split(/\s+/).map(id => ids.get(id) ?? id).join(' '))
      }
    }
    if (node.localName === 'style') node.textContent = swap(node.textContent)
  }
  return svg
}

// The drawing as the chart controller sizes it: its own width and height from its viewBox, and no size
// from the renderer, so that nothing but the controller sets how large it shows; and its ids its own.
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
  chart.dataset.drawn = 'failed'
  chart.replaceChildren()
  const said = document.createElement('div')
  said.className = 'chart-err'
  said.textContent = `The chart did not draw: ${why}`
  const pre = document.createElement('pre')
  pre.textContent = chart.dataset.src
  chart.append(said, pre)
}

// The SVG inherits its palette, so a theme change leaves its pan and zoom intact.
export async function draw (root = document) {
  const charts = [...root.querySelectorAll('.chart[data-src]:not([data-drawn])')]
  await Promise.all(charts.map(async chart => {
    chart.dataset.drawn = 'loading'
    try {
      const pele = await library()
      if (!chart.isConnected) return
      frame(chart)
      const css = getComputedStyle(chart)
      const id = `lem-chart-${++made}`
      const { svg } = pele.render(chart.dataset.src, {
        idPrefix: id,
        autoDirection: false,
        responsive: false,
        links: false,
        images: false,
        fontFamily: css.getPropertyValue('--sans').trim(),
        fontFamilyMono: css.getPropertyValue('--mono').trim(),
        fontSize: 13.5,
      })
      const box = chart.querySelector(':scope > .chart-svg')
      box.innerHTML = svg
      const drawing = box.querySelector('svg')
      drawing.id = id
      settle(drawing)
      chart.dataset.drawn = 'done'
      chart.dispatchEvent(new CustomEvent('lem:chart'))
    } catch (error) {
      failed(chart, String(error?.message ?? error).split('\n').find(line => line.trim()) ?? 'It did not parse')
    }
  }))
}
