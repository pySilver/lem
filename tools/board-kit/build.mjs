// Builds skills/lem/assets/vendor/: board-app.js (app.js: the served board's one script, with Turbo,
// Stimulus, the controllers and the markdown reader of entry.js), board-icons.json, the icons as SVG
// symbols that the server inlines into each page it renders, and pele.js, the diagram library as
// the Pele package ships it, which a page loads only when it has a chart (charts.js).
//
//   npm --prefix tools/board-kit run build
//
// The icons come from the Font Awesome Pro download named by FA_SVGS (default: the 6.7.2 web download in
// ~/Downloads), only those icons.mjs lists, with their comments taken out. The build fails when an icon
// is missing, and when the bundle holds an address that a page would load from the network.
import { build } from 'esbuild'
import { copyFileSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { REGULAR } from './icons.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
const OUT = resolve(HERE, '../../skills/lem/assets/vendor')
const SVGS = process.env.FA_SVGS ?? join(homedir(), 'Downloads/fontawesome-pro-6.7.2-web/svgs')

function svg (name) {
  const file = join(SVGS, 'regular', `${name}.svg`)
  let text
  try {
    text = readFileSync(file, 'utf8')
  } catch {
    throw new Error(`no icon regular/${name} in ${SVGS}: set FA_SVGS to the svgs folder of the Font Awesome Pro download`)
  }
  return text.replace(/<!--[\s\S]*?-->/g, '').trim()
}

await build({
  entryPoints: [join(HERE, 'app.js')],
  bundle: true,
  format: 'iife',
  target: ['safari17', 'chrome120'],
  minify: true,
  legalComments: 'none',
  banner: { js: '/* Lem board kit, built by tools/board-kit: Turbo and Stimulus (37signals, MIT), marked (MIT). */' },
  outfile: join(OUT, 'board-app.js'),
  logLevel: 'warning',
})
// The diagram library, as its package ships it. The first chart loads this classic script.
copyFileSync(join(HERE, 'node_modules/pele/dist/pele.global.js'), join(OUT, 'pele.js'))
copyFileSync(join(HERE, 'node_modules/pele/LICENSE'), join(OUT, 'pele-LICENSE.txt'))

// The icons for the server's pages: {NAME: {"viewBox": "...", "body": "<path .../>"}}, which a page puts
// into one <svg> of <symbol>s and draws with <use>, so that an icon paints at once and a morph has nothing
// to break.
if (!process.argv.includes('--keep-icons')) {
  const symbols = Object.fromEntries(REGULAR.map(name => {
    const text = svg(name)
    const viewBox = text.match(/viewBox="([^"]+)"/)?.[1]
    const body = text.replace(/^<svg[^>]*>/, '').replace(/<\/svg>\s*$/, '')
    if (!viewBox || !body) throw new Error(`the icon ${name} has no viewBox or no body`)
    return [name, { viewBox, body }]
  }))
  writeFileSync(join(OUT, 'board-icons.json'), `${JSON.stringify(symbols, null, 0)}\n`)
}

// An address the page would request: an http(s) address in the script other than the SVG namespace,
// which names and loads nothing.
for (const name of ['board-app.js', 'board-icons.json']) {
  const text = readFileSync(join(OUT, name), 'utf8')
  const found = [...new Set(text.match(/https?:\/\/[^\s"'`)]+/g) ?? [])].filter(url => url !== 'http://www.w3.org/2000/svg')
  console.log(`${name}: ${statSync(join(OUT, name)).size} bytes${found.length ? `; addresses: ${found.join(', ')}` : ''}`)
}
