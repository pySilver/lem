// Builds skills/lem/assets/vendor/: board-app.js (app.js: the served board's one script, with Turbo,
// Stimulus, the controllers and the markdown reader of entry.js), board-icons.json, the icons as SVG
// symbols that the server inlines into each page it renders, and mermaid.min.js, the diagram library as
// the mermaid package ships it, which a page loads only when it has a chart (charts.js).
//
//   npm --prefix tools/board-kit run build
//
// The icons come from the Font Awesome Pro download named by FA_SVGS (default: the 6.7.2 web download in
// ~/Downloads), only those icons.mjs lists, with their comments taken out. The build fails when an icon
// is missing, and when the bundle holds an address that a page would load from the network.
import {build} from 'esbuild';
import {createHash} from 'node:crypto';
import {copyFileSync, readFileSync, statSync, writeFileSync} from 'node:fs';
import {homedir} from 'node:os';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {REGULAR} from './icons.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, '../../skills/lem/assets/vendor');
const SVGS = process.env.FA_SVGS ?? join(homedir(), 'Downloads/fontawesome-pro-6.7.2-web/svgs');

function svg(name) {
  const file = join(SVGS, 'regular', `${name}.svg`);
  let text;
  try {
    text = readFileSync(file, 'utf8');
  } catch {
    throw new Error(`no icon regular/${name} in ${SVGS}: set FA_SVGS to the svgs folder of the Font Awesome Pro download`);
  }
  return text.replace(/<!--[\s\S]*?-->/g, '').trim();
}

await build({
  entryPoints: [join(HERE, 'app.js')], bundle: true, format: 'iife', target: ['safari17', 'chrome120'], minify: true, legalComments: 'none',
  banner: {js: '/* Lem board kit, built by tools/board-kit: Turbo and Stimulus (37signals, MIT), marked (MIT). */'},
  outfile: join(OUT, 'board-app.js'), logLevel: 'warning',
});
// The diagram library, as its package ships it: the same file, byte for byte, that lem-ask pins
// (MERMAID_SHA256 in skills/lem-ask/bin/lem-ask), so that both show a chart the same way.
const MERMAID = join(HERE, 'node_modules/mermaid/dist/mermaid.min.js');
const MERMAID_SHA256 = '07e37dfa97b337ccc85365d57eddf99b9706f09db3b59b260d0333b23b343c4b';
const mermaidHash = createHash('sha256').update(readFileSync(MERMAID)).digest('hex');
if (mermaidHash !== MERMAID_SHA256) throw new Error(`${MERMAID} is not mermaid 11.12.0 as lem-ask pins it (sha256 ${mermaidHash})`);
copyFileSync(MERMAID, join(OUT, 'mermaid.min.js'));
console.log(`mermaid.min.js: ${statSync(join(OUT, 'mermaid.min.js')).size} bytes, sha256 as pinned`);

// The icons for the server's pages: {NAME: {"viewBox": "...", "body": "<path .../>"}}, which a page puts
// into one <svg> of <symbol>s and draws with <use>, so that an icon paints at once and a morph has nothing
// to break.
const symbols = Object.fromEntries(REGULAR.map(name => {
  const text = svg(name);
  const viewBox = text.match(/viewBox="([^"]+)"/)?.[1];
  const body = text.replace(/^<svg[^>]*>/, '').replace(/<\/svg>\s*$/, '');
  if (!viewBox || !body) throw new Error(`the icon ${name} has no viewBox or no body`);
  return [name, {viewBox, body}];
}));
writeFileSync(join(OUT, 'board-icons.json'), `${JSON.stringify(symbols, null, 0)}\n`);

// An address the page would request: an http(s) address in the script other than the SVG namespace,
// which names and loads nothing.
for (const name of ['board-app.js', 'board-icons.json']) {
  const text = readFileSync(join(OUT, name), 'utf8');
  const found = [...new Set(text.match(/https?:\/\/[^\s"'`)]+/g) ?? [])].filter(url => url !== 'http://www.w3.org/2000/svg');
  console.log(`${name}: ${statSync(join(OUT, name)).size} bytes${found.length ? `; addresses: ${found.join(', ')}` : ''}`);
}
