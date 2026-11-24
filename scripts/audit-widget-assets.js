const fs = require('fs');
const path = require('path');
const glob = require('glob');

function findWidgets(rootGlob) {
  return glob.sync(rootGlob, { nodir: false });
}

function extractRefs(html) {
  const refs = new Set();
  // script src
  const scriptRe = /<script[^>]+src=["']([^"']+)["']/gi;
  let m;
  while ((m = scriptRe.exec(html))) refs.add(m[1]);
  // link href
  const linkRe = /<link[^>]+href=["']([^"']+)["']/gi;
  while ((m = linkRe.exec(html))) refs.add(m[1]);
  // any asset path in JS like path: 'assets/...' or "assets/..."
  const assetRe = /['\"](assets\/[\w\-\/.]+)['\"]/gi;
  while ((m = assetRe.exec(html))) refs.add(m[1]);
  // generic src/href-like raw strings (script may add them dynamically)
  return Array.from(refs);
}

function checkWidget(indexPath) {
  const folder = path.dirname(indexPath);
  const html = fs.readFileSync(indexPath, 'utf8');
  const refs = extractRefs(html);
  const missing = [];
  refs.forEach((ref) => {
    // ignore absolute urls
    if (/^https?:\/\//i.test(ref) || ref.startsWith('data:')) return;
    // resolve relative to index.html
    const resolved = path.resolve(folder, ref);
    if (!fs.existsSync(resolved)) {
      // try resolve as absolute under widget folder (remove leading slash)
      const alt = path.resolve(folder, '.' + (ref.startsWith('/') ? ref : '/' + ref));
      if (!fs.existsSync(alt)) {
        missing.push({ ref, resolved, altExists: fs.existsSync(alt) });
      }
    }
  });
  return { indexPath, refsCount: refs.length, missing };
}

function main() {
  const roots = ['widgets-b1/**/index.html','widgets-b2/**/index.html','widgets-b3/**/index.html'];
  const results = [];
  roots.forEach((g) => {
    const matches = glob.sync(g);
    matches.forEach((m) => {
      results.push(checkWidget(path.resolve(m)));
    });
  });
  // print summary of widgets with missing assets
  results.forEach(r => {
    if (r.missing.length) {
      console.log('WIDGET:', r.indexPath.replace(process.cwd()+path.sep,''));
      r.missing.forEach(m => console.log('  MISSING:', m.ref));
    }
  });
  const tot = results.length;
  const bad = results.filter(r => r.missing.length).length;
  console.log('\nScanned', tot, 'widgets —', bad, 'had missing assets.');
}

main();
