const fs = require('fs');
const path = require('path');
const glob = require('glob');

function stripQuery(p){ return p.split('?')[0]; }
function basename(p){ return path.basename(stripQuery(p)); }

function findIndexFiles(){
  return glob.sync('widgets-b1/**/index.html').concat(glob.sync('widgets-b2/**/index.html')).concat(glob.sync('widgets-b3/**/index.html'));
}

function extractRefs(html){
  const refs = new Set();
  const scriptRe = /<script[^>]+src=[\"']([^\"']+)[\"']/gi;
  let m;
  while ((m = scriptRe.exec(html))) refs.add(m[1]);
  const linkRe = /<link[^>]+href=[\"']([^\"']+)[\"']/gi;
  while ((m = linkRe.exec(html))) refs.add(m[1]);
  const assetRe = /["'](assets\/[\w\-\/.]+)["']/gi;
  while ((m = assetRe.exec(html))) refs.add(m[1]);
  return Array.from(refs);
}

function searchCandidate(folder, name){
  // search for files whose basename matches name (case-sensitive)
  const matches = glob.sync(folder + '/**/*' + name, { nodir: true });
  return matches;
}

function relPath(from, to){
  return path.relative(path.dirname(from), to).replace(/\\/g, '/');
}

const indexFiles = findIndexFiles();
let changed = 0;
indexFiles.forEach(index => {
  const html = fs.readFileSync(index,'utf8');
  const refs = extractRefs(html);
  let newHtml = html;
  let madeChange = false;
  refs.forEach(ref => {
    if (/^https?:\/\//i.test(ref) || ref.startsWith('data:')) return;
    const resolved = path.resolve(path.dirname(index), stripQuery(ref));
    if (!fs.existsSync(resolved)){
      const name = basename(ref);
      const candidates = glob.sync(path.join(path.dirname(index),'**',name));
      if (candidates.length === 1){
        const cand = candidates[0];
        const relative = relPath(index, cand);
        // replace all occurrences of ref (with possible query) with relative (keep existing query removed)
        const escaped = ref.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
        const re = new RegExp(escaped.replace(/\?/g,'\\?'),'g');
        newHtml = newHtml.replace(re, relative);
        madeChange = true;
        console.log('Patched', index, '=>', ref, '->', relative);
      }
    }
  });
  if (madeChange){
    // backup and write
    fs.copyFileSync(index, index + '.bak');
    fs.writeFileSync(index, newHtml, 'utf8');
    changed++;
  }
});
console.log('Done. Files changed:', changed);
