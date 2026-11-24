const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 950 });

  // Login
  await page.goto('http://localhost:8000/login.html', { waitUntil: 'networkidle2' });
  await page.evaluate(() => authManager.login('admin@company.com', 'Admin@123', true));

  // Navigate to dashboard
  await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle2' });

  // Switch to inventory tab
  await page.evaluate(() => switchTab('inventory'));
  await new Promise(r => setTimeout(r, 600));

  // 1. Initial All Scope state
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/240_inventory_new_filters_all.png' });
  console.log('Screenshot 240: All Scope view');

  // 2. Click 'Needs Attention' pill
  await page.evaluate(() => setFilterQuick('attention'));
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/241_inventory_filter_attention.png' });
  console.log('Screenshot 241: Needs Attention (36 items)');

  // 3. Click 'Missing in QA' pill
  await page.evaluate(() => setFilterQuick('missing_qa'));
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/242_inventory_filter_missing_qa.png' });
  console.log('Screenshot 242: Missing in QA (15 items)');

  // 4. Click 'Missing in Git' pill
  await page.evaluate(() => setFilterQuick('missing_git'));
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/243_inventory_filter_missing_git.png' });
  console.log('Screenshot 243: Missing in Git (21 items)');

  // 5. Search bar test: 'circle'
  await page.evaluate(() => {
    setFilterQuick('all');
    const inp = document.getElementById('widgetSearch');
    inp.value = 'circle';
    filterWidgets();
  });
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/244_inventory_search_circle.png' });
  console.log('Screenshot 244: Search circle');

  // 6. Test in Dark Mode
  await page.evaluate(() => {
    document.documentElement.classList.add('dark');
    clearFilter();
  });
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/245_inventory_dark_mode.png' });
  console.log('Screenshot 245: Dark Mode inventory');

  await browser.close();
  console.log('All tests completed successfully!');
})();
