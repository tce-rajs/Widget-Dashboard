const fs = require('fs');
const path = require('path');

const MASTER = path.join('src','app','master','master.ts');
const OUT = path.join('src','assets','widgets-all.json');

if (!fs.existsSync(MASTER)) {
  console.error('master.ts not found at', MASTER);
  process.exit(1);
}

const text = fs.readFileSync(MASTER,'utf8');

// Find array literal starting with "export const json"
const arrMatch = text.match(/export\s+const\s+json\s*:\s*Widget\[\]\s*=\s*\[([\s\S]*?)\];/);
let arrayText = '';
if (arrMatch) {
  arrayText = arrMatch[1];
} else {
  // fallback: try to find "export const json = [ ... ];"
  const arrMatch2 = text.match(/export\s+const\s+json\s*=\s*\[([\s\S]*?)\];/);
  if (arrMatch2) arrayText = arrMatch2[1];
}

if (!arrayText) {
  console.error('Could not extract json array from master.ts');
  process.exit(1);
}

// Split into objects by top-level '},' occurrences.
const objs = [];
let depth = 0;
let cur = '';
for (let i=0;i<arrayText.length;i++){
  const ch = arrayText[i];
  cur += ch;
  if (ch === '{') depth++;
  else if (ch === '}') depth--;
  if (depth === 0 && cur.trim()) {
    objs.push(cur.trim().replace(/^,?\s*/,''));
    cur = '';
  }
}

function extractField(objText, field){
  const re = new RegExp(field+"\s*:\s*([^,\n]+)", 'm');
  const m = objText.match(re);
  if (!m) return null;
  return m[1].trim();
}

function parseStringLiteral(text){
  if (!text) return null;
  const m = text.match(/['\"]([\s\S]*?)['\"]/);
  return m ? m[1] : null;
}

function parseArrayOfStrings(text){
  if (!text) return [];
  const m = text.match(/\[([\s\S]*?)\]/);
  if (!m) return [];
  const inner = m[1];
  const parts = inner.split(',').map(s=>s.trim()).filter(Boolean);
  return parts.map(p=>{
    const str = parseStringLiteral(p);
    return str!==null?str:p;
  }).filter(Boolean);
}

const parsed = objs.map(o=>{
  const id = parseStringLiteral(extractField(o,'id')) || null;
  const link = parseStringLiteral(extractField(o,'link')) || null;
  const title = parseStringLiteral(extractField(o,'title')) || (id || null);
  const img = parseStringLiteral(extractField(o,'img')) || null;
  const thumb = parseStringLiteral(extractField(o,'thumb')) || null;
  const tags = parseArrayOfStrings(extractField(o,'tags'));
  const category = parseArrayOfStrings(extractField(o,'category'));
  let orderRaw = extractField(o,'order');
  let order = null;
  if (orderRaw) {
    const n = orderRaw.match(/(\d+)/);
    order = n ? parseInt(n[1],10) : null;
  }
  // status may refer to ProgressEnum.SOMETHING
  let statusRaw = extractField(o,'status');
  let status = null;
  if (statusRaw) {
    const m = statusRaw.match(/ProgressEnum\.([A-Z0-9_]+)/i);
    status = m ? m[1] : statusRaw.replace(/['\"]/g,'').trim();
  }
  return { id, link, title, img, thumb, tags, category, order, status };
}).filter(x=>x.id);

// Group by subject: use tags[1] if present, else tags[0], else first category word, else 'Uncategorized'
const grouped = {};
parsed.forEach(w=>{
  let subject = 'Uncategorized';
  if (w.tags && w.tags.length>1) subject = w.tags[1];
  else if (w.tags && w.tags.length>0) subject = w.tags[0];
  else if (w.category && w.category.length>0) subject = w.category[0];
  subject = subject || 'Uncategorized';
  if (!grouped[subject]) grouped[subject]=[];
  grouped[subject].push(w);
});

// Sort widgets within each subject A->Z by title
Object.keys(grouped).forEach(k=>{
  grouped[k].sort((a,b)=> (a.title||'').localeCompare(b.title||'', undefined, {sensitivity:'base'}));
});

fs.writeFileSync(OUT, JSON.stringify(grouped, null, 2), 'utf8');
console.log('Wrote', OUT);
