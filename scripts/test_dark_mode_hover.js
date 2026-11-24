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

  // 1. Enable Dark Mode
  await page.evaluate(() => {
    document.documentElement.classList.add('dark');
  });
  await new Promise(r => setTimeout(r, 400));

  // 2. Hover over Need Attention KPI card in dark mode
  await page.hover('#card-kpi-attention');
  await new Promise(r => setTimeout(r, 300));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/300_hover_kpi_attention_dark.png' });
  console.log('Screenshot 300: Hover KPI Need Attention in dark mode.');

  // 3. Hover over QA Presence KPI card in dark mode
  await page.hover('#card-kpi-qa');
  await new Promise(r => setTimeout(r, 300));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f301_hover_kpi_qa_dark.png' });
  console.log('Screenshot 301: Hover KPI QA in dark mode.');

  // 4. Scroll to Donut Chart section and hover over Matched Everywhere tile
  await page.evaluate(() => {
    document.getElementById('reconciliationDonutChart').scrollIntoView({ behavior: 'instant', block: 'center' });
  });
  await new Promise(r => setTimeout(r, 300));

  const tiles = await page.$$('.md\\:col-span-7 > div');
  if (tiles.length > 0) {
    await tiles[0].hover();
    await new Promise(r => setTimeout(r, 300));
    await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/302_hover_donut_tile_dark.png' });
    console.log('Screenshot 302: Hover Donut Tile in dark mode.');
  }

  // 5. Scroll to Reconciliation Matrix table and hover over row 1
  await page.evaluate(() => {
    document.querySelector('table').scrollIntoView({ behavior: 'instant', block: 'center' });
  });
  await new Promise(r => setTimeout(r, 300));

  const rows = await page.$$('tbody tr');
  if (rows.length > 0) {
    await rows[0].hover();
    await new Promise(r => setTimeout(r, 300));
    await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/303_hover_reconcile_row_dark.png' });
    console.log('Screenshot 303: Hover Reconciliation Row in dark mode.');
  }

  await browser.close();
  console.log('Dark mode hover verification completed successfully!');
})();
