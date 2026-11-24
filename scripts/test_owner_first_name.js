const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  await page.goto('http://localhost:8000/login.html', { waitUntil: 'networkidle2' });
  await page.evaluate(() => authManager.login('admin@company.com', 'Admin@123', true));
  await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle2' });

  await page.evaluate(() => switchTab('inventory'));
  await new Promise(r => setTimeout(r, 400));

  // Check the first 5 rows for owner badge and name
  const rows = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('#widgetTableBody tr')).slice(0, 5).map(tr => {
      const tds = tr.querySelectorAll('td');
      const ownerEl = tds[2];
      const initial = ownerEl?.querySelector('span')?.innerText.trim();
      const fullName = ownerEl?.querySelectorAll('span')[1]?.innerText.trim();
      return {
        sr: tds[0]?.innerText.trim(),
        widgetName: tds[1]?.querySelector('div')?.innerText.trim(),
        ownerInitial: initial,
        ownerFirstName: fullName
      };
    });
  });
  console.log('Sample rows:', rows);

  // Test Owner filter by 'Prasanna'
  await page.evaluate(() => {
    const sel = document.getElementById('ownerFilter');
    sel.value = 'Prasanna';
    filterWidgets();
  });
  await new Promise(r => setTimeout(r, 300));
  const prasannaCount = await page.$eval('#totalFiltered', el => el.innerText);
  console.log('Prasanna count:', prasannaCount);

  // Test Owner filter by 'Nitin'
  await page.evaluate(() => {
    const sel = document.getElementById('ownerFilter');
    sel.value = 'Nitin';
    filterWidgets();
  });
  await new Promise(r => setTimeout(r, 300));
  const nitinCount = await page.$eval('#totalFiltered', el => el.innerText);
  console.log('Nitin count:', nitinCount);

  // Screenshot
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/280_owner_first_name_only.png' });
  console.log('Screenshot 280 captured: Owner first name only.');

  await browser.close();
})();
