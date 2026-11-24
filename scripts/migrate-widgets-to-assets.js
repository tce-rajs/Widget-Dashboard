const fs = require('fs');
const path = require('path');

function copyRecursiveSync(src, dest) {
  const exists = fs.existsSync(src);
  const stats = exists && fs.statSync(src);
  const isDirectory = exists && stats.isDirectory();
  if (isDirectory) {
    if (!fs.existsSync(dest)) fs.mkdirSync(dest, { recursive: true });
    fs.readdirSync(src).forEach(function(childItemName) {
      copyRecursiveSync(path.join(src, childItemName), path.join(dest, childItemName));
    });
  } else {
    // copy file
    const destDir = path.dirname(dest);
    if (!fs.existsSync(destDir)) fs.mkdirSync(destDir, { recursive: true });
    // don't overwrite newer files
    try {
      if (fs.existsSync(dest)) {
        const sStat = fs.statSync(src);
        const dStat = fs.statSync(dest);
        if (dStat.mtimeMs >= sStat.mtimeMs) return; // keep newer
      }
      fs.copyFileSync(src, dest);
    } catch (err) {
      console.error('Copy failed', src, err);
    }
  }
}

const workspace = process.cwd();
const widgetRoots = ['widgets-b1','widgets-b2','widgets-b3'];
const targetBase = path.join('src','assets','widgets');

if (!fs.existsSync('src')) {
  console.error('This script expects to run from repository root with a src/ folder.');
  process.exit(1);
}

if (!fs.existsSync(path.join('src','assets'))) fs.mkdirSync(path.join('src','assets'));
if (!fs.existsSync(targetBase)) fs.mkdirSync(targetBase, { recursive: true });

let copied = 0;
widgetRoots.forEach(root => {
  const full = path.join(workspace, root);
  if (!fs.existsSync(full)) return;
  const entries = fs.readdirSync(full);
  entries.forEach(entry => {
    const srcPath = path.join(full, entry);
    const destPath = path.join(targetBase, entry);
    copyRecursiveSync(srcPath, destPath);
    copied++;
  });
});

console.log('Done. Copied entries:', copied, 'to', targetBase);
