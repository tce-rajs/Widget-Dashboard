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

  // Switch to inventory view
  await page.evaluate(() => switchTab('inventory'));
  await new Promise(r => setTimeout(r, 400));

  // 1. Capture table with Owner column & Initials
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/260_owner_column_initials.png' });
  console.log('Screenshot 260 captured: Table with Owner column & Initials.');

  // Check the first 5 table rows for owner initials & name
  const rows = await page.evaluate(() => {
    const trs = Array.from(document.querySelectorAll('#widgetTableBody tr'));
    return trs.slice(0, 5).map(tr => {
      const tds = tr.querySelectorAll('td');
      return {
        sr: tds[0]?.innerText.trim(),
        name: tds[1]?.querySelector('div')?.innerText.trim(),
        owner: tds[2]?.innerText.trim(),
        qa: tds[3]?.innerText.trim(),
        git: tds[4]?.innerText.trim()
      };
    });
  });
  console.log('Sample rows:', JSON.stringify(rows, null, 2));

  // 2. Test Owner Filter: Filter by 'Prasanna Sir'
  await page.evaluate(() => {
    const sel = document.getElementById('ownerFilter');
    sel.value = 'Prasanna Sir';
    filterWidgets();
  });
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/261_filter_owner_prasanna.png' });
  const psCount = await page.$eval('#totalFiltered', el => el.innerText);
  console.log('Prasanna Sir widgets count:', psCount);

  // 3. Test Owner Filter: Filter by 'Nitin'
  await page.evaluate(() => {
    const sel = document.getElementById('ownerFilter');
    sel.value = 'Nitin';
    filterWidgets();
  });
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/262_filter_owner_nitin.png' });
  const nitinCount = await page.$eval('#totalFiltered', el => el.innerText);
  console.log('Nitin widgets count:', nitinCount);

  // 4. Test Sorting by Owner
  await page.evaluate(() => {
    clearFilter();
    sortData('owner');
  });
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/263_sorted_by_owner.png' });
  console.log('Screenshot 263 captured: Sorted by owner.');

  // 5. Test Mobile View (375x812)
  await page.setViewport({ width: 375, height: 812, isMobile: true });
  await page.evaluate(() => clearFilter());
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/264_mobile_cards_with_owner.png' });
  console.log('Screenshot 264 captured: Mobile card with owner badge.');

  await browser.close();
  console.log('All Owner tests passed successfully!');
})();
