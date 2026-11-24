const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 950 });

  page.on('console', msg => console.log('PAGE_LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE_ERR:', err.message));

  // Go to login page and log in directly via authManager
  await page.goto('http://localhost:8000/login.html', { waitUntil: 'networkidle2' });
  await page.evaluate(() => authManager.login('admin@company.com', 'Admin@123', true));

  // Navigate to index.html with active session
  await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 600));

  // 1. Capture Data Reconciliation Matrix (Light)
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/201_reconciliation_matrix_light.png' });
  console.log('Screenshot 201 captured: Data Reconciliation Matrix Light.');

  // 2. Toggle Dark Mode
  await page.evaluate(() => {
    document.documentElement.classList.add('dark');
  });
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/202_reconciliation_matrix_dark.png' });
  console.log('Screenshot 202 captured: Data Reconciliation Matrix Dark.');

  // 3. Test Clicking Filter (e.g. View 15 Missing in QA)
  await page.evaluate(() => drillDown('missing_qa'));
  await new Promise(r => setTimeout(r, 500));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/203_filtered_missing_qa.png' });
  console.log('Screenshot 203 captured: Filtered Missing in QA (15 items).');

  // 4. Return to Overview and Test Mobile Viewport
  await page.evaluate(() => switchTab('overview'));
  await page.setViewport({ width: 390, height: 844 });
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/204_matrix_mobile_dark.png' });
  console.log('Screenshot 204 captured: Mobile View Dark.');

  await browser.close();
  console.log('All verification screenshots captured successfully!');
})();
