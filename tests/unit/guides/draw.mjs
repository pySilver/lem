// Run the site's chart script with the chart blocks from one built page.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { runInNewContext } from 'node:vm'

const [site, chartScript] = process.argv.slice(2)
const blocks = JSON.parse(readFileSync(0, 'utf8'))
const figures = []
const charts = blocks.map(textContent => ({
  textContent,
  before (line) { assert.fail(line.textContent) },
  replaceWith (figure) { figures.push(figure) },
}))
const window = {
  getComputedStyle: () => ({ getPropertyValue: () => '' }),
}
const scriptUrl = new URL(chartScript, 'https://pysilver.github.io/lem/')
const document = {
  currentScript: { src: scriptUrl.href },
  querySelectorAll (selector) {
    assert.equal(selector, 'pre.lem-chart')
    return charts
  },
  createElement: tagName => ({ tagName }),
  head: {
    append (script) {
      assert.equal(script.tagName, 'script')
      const source = new URL(script.src)
      assert.equal(source.href, new URL('pele.js', scriptUrl).href)
      const pele = readFileSync(site + '/' + source.pathname.replace('/lem/', ''), 'utf8')
      runInNewContext(pele + '\nwindow.pele = pele', { window })
      script.onload()
    },
  },
}
runInNewContext(readFileSync(site + '/' + chartScript, 'utf8'), { document, window, URL })
await Promise.resolve()
assert.equal(figures.length, blocks.length)
for (const figure of figures) {
  assert.equal(figure.tagName, 'figure')
  assert.equal(figure.className, 'lem-chart-drawn')
  assert.match(figure.innerHTML, /^<svg\b/)
  assert.match(figure.innerHTML, /class="pele pele-flowchart"/)
  assert.match(figure.innerHTML, /var\(--pele-bg/)
}
