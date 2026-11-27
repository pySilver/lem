/* The charts of Lem's site. A guide's ```mermaid block is a pre.lem-chart here (zensical.toml),
   which Zensical's own Mermaid loader never looks for. This script loads Pele, the board's
   renderer, from beside itself, only on a page that has a chart, and puts each drawing in place
   of its block. The drawing takes its colors from the --pele-* variables of lem-site.css, so it
   follows the visitor's theme. A chart that Pele cannot read keeps its text, under a line that
   says why. */
(() => {
  const charts = [...document.querySelectorAll('pre.lem-chart')]
  if (!charts.length) return
  const here = document.currentScript.src
  // Each chart breaks its words at 110 px and keeps its boxes 20 px apart. Drawn top to bottom at
  // 15 px, the docs' charts are then 340 to 580 px wide (2026-11-27): each fits the text at 1280 px
  // and is almost as narrow as a phone. With Pele's own 200 px and 50 px, the flow's chart was too
  // wide for the text. A chart with front matter of its own keeps it.
  const layout = '---\nconfig:\n  flowchart:\n    wrappingWidth: 110\n    nodeSpacing: 20\n---\n'

  function library () {
    if (window.pele) return Promise.resolve(window.pele)
    return new Promise((resolve, reject) => {
      const script = document.createElement('script')
      script.src = new URL('pele.js', here).href
      script.onload = () => (window.pele ? resolve(window.pele) : reject(new Error('Pele did not start')))
      script.onerror = () => reject(new Error('Pele did not load'))
      document.head.append(script)
    })
  }

  function failed (chart, why) {
    const line = document.createElement('p')
    line.className = 'lem-chart-error'
    line.textContent = `The chart did not draw: ${why}`
    chart.before(line)
  }

  library().then((pele) => {
    const css = window.getComputedStyle(document.body)
    charts.forEach((chart, index) => {
      try {
        const text = chart.textContent.startsWith('---') ? chart.textContent : layout + chart.textContent
        const { svg } = pele.render(text, {
          idPrefix: `lem-chart-${index + 1}`,
          autoDirection: false,
          links: false,
          images: false,
          fontFamily: css.getPropertyValue('--md-text-font-family').trim() || 'system-ui, sans-serif',
          // Pele writes an edge's words at 7/8 of this: 13 px, over the 12.8 px of a table's words.
          fontSize: 15
        })
        const figure = document.createElement('figure')
        figure.className = 'lem-chart-drawn'
        figure.innerHTML = svg
        chart.replaceWith(figure)
      } catch (error) {
        failed(chart, String(error?.message ?? error).split('\n')[0])
      }
    })
  }, (error) => charts.forEach((chart) => failed(chart, error.message)))
})()
