const fs = require('fs');
const path = require('path');
const p = path.join(__dirname, '..', 'src', 'assets', 'widgets-all.json');
let s = fs.readFileSync(p, 'utf8');
// Remove /* ... */ comments
s = s.replace(/\/\*[\s\S]*?\*\//g, '');
// Remove // comments
s = s.replace(/(^|\n)\s*\/\/.*(?=\n|$)/g, '\n');
// Remove trailing commas before ] or }
s = s.replace(/,\s*(\]|})/g, '$1');
try {
  const obj = JSON.parse(s);
  fs.writeFileSync(p, JSON.stringify(obj, null, 2), 'utf8');
  console.log('Sanitized and wrote', p);
} catch (e) {
  console.error('Failed to parse after sanitization:', e.message);
  process.exit(1);
}