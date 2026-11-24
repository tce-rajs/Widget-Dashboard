const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  page.on('pageerror', err => errors.push(err.message));

  await page.goto('http://localhost:8000/login.html', { waitUntil: 'networkidle2' });
  await page.evaluate(() => authManager.login('admin@company.com', 'Admin@123', true));
  await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle2' });

  const hasDocsTab = await page.evaluate(() => !!document.getElementById('tab-docs'));
  const hasDocsView = await page.evaluate(() => !!document.getElementById('view-docs'));

  console.log('tab-docs in DOM (should be false):', hasDocsTab);
  console.log('view-docs in DOM (should be false):', hasDocsView);

  const tabs = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('.nav-tab')).map(el => ({
      id: el.id,
      text: el.innerText.trim(),
      visible: !el.classList.contains('hidden')
    }));
  });
  console.log('Active navigation tabs:', tabs);

  // Test switching to inventory
  await page.evaluate(() => switchTab('inventory'));
  await new Promise(r => setTimeout(r, 300));

  // Capture screenshot of navigation bar
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/290_no_documentation_tab.png' });
  console.log('Screenshot 290 captured: No Documentation tab.');
  console.log('Total console/page errors:', errors.length);

  await browser.close();
})();
