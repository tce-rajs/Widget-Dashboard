const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 950 });

  await page.goto('http://localhost:8000/login.html', { waitUntil: 'networkidle2' });
  await page.evaluate(() => authManager.login('admin@company.com', 'Admin@123', true));
  await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle2' });

  // 1. Enable Dark Mode & take overview table screenshot
  await page.evaluate(() => {
    document.documentElement.classList.add('dark');
    localStorage.setItem('theme', 'dark');
  });
  await new Promise(r => setTimeout(r, 200));

  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/394_reconciliation_table_interactive.png' });

  // Test clicking "21" (Missing in Git)
  await page.evaluate(() => {
    // find Row 3 button or cell
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('View 21'));
    if (btn) btn.click();
  });
  await new Promise(r => setTimeout(r, 400));

  const count21 = await page.evaluate(() => {
    const totalEl = document.getElementById('totalFiltered');
    const pill = document.getElementById('pill-filter-requires_dev');
    const pillAttn = document.getElementById('pill-filter-needs_attention');
    return {
      filteredTotal: totalEl ? totalEl.innerText : 'null',
      pillActive: pill ? pill.className.includes('bg-rose-600') : false,
      attnActive: pillAttn ? pillAttn.className.includes('bg-rose-600') : false
    };
  });
  console.log('Clicking "View 21" results:', JSON.stringify(count21));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/395_inventory_missing_git_21_only.png' });

  // Test clicking "View 15"
  await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle2' });
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('View 15'));
    if (btn) btn.click();
  });
  await new Promise(r => setTimeout(r, 400));
  const count15 = await page.evaluate(() => document.getElementById('totalFiltered')?.innerText);
  console.log('Clicking "View 15" results:', count15);

  // Test clicking "View +46"
  await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle2' });
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('View +46'));
    if (btn) btn.click();
  });
  await new Promise(r => setTimeout(r, 400));
  const count46 = await page.evaluate(() => document.getElementById('totalFiltered')?.innerText);
  console.log('Clicking "View +46" results:', count46);

  // Test clicking "View All 340"
  await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle2' });
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('View All 340'));
    if (btn) btn.click();
  });
  await new Promise(r => setTimeout(r, 400));
  const count340 = await page.evaluate(() => document.getElementById('totalFiltered')?.innerText);
  console.log('Clicking "View All 340" results:', count340);

  await browser.close();
})();
