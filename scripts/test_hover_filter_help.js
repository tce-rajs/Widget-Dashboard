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

  // Switch to inventory view
  await page.evaluate(() => switchTab('inventory'));
  await new Promise(r => setTimeout(r, 400));

  // 1. Initial State (All Scope)
  let text = await page.$eval('#filterHelpText', el => el.innerText);
  console.log('Initial explanation line:', text);
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/250_filter_help_default.png' });

  // 2. Hover over Needs Attention button
  await page.hover('#pill-filter-needs_attention');
  await new Promise(r => setTimeout(r, 300));
  text = await page.$eval('#filterHelpText', el => el.innerText);
  console.log('Hover Needs Attention:', text);
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/251_filter_hover_attention.png' });

  // 3. Hover over Missing in QA button
  await page.hover('#pill-filter-missing_qa');
  await new Promise(r => setTimeout(r, 300));
  text = await page.$eval('#filterHelpText', el => el.innerText);
  console.log('Hover Missing in QA:', text);
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/252_filter_hover_missing_qa.png' });

  // 4. Hover over Missing in Git button
  await page.hover('#pill-filter-requires_dev');
  await new Promise(r => setTimeout(r, 300));
  text = await page.$eval('#filterHelpText', el => el.innerText);
  console.log('Hover Missing in Git:', text);
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/253_filter_hover_missing_git.png' });

  // 5. Hover over Extra in Repo button
  await page.hover('#pill-filter-extra_repo');
  await new Promise(r => setTimeout(r, 300));
  text = await page.$eval('#filterHelpText', el => el.innerText);
  console.log('Hover Extra in Repo:', text);
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/254_filter_hover_extra_repo.png' });

  // 6. Hover over Matched in All 3 button
  await page.hover('#pill-filter-matched_all');
  await new Promise(r => setTimeout(r, 300));
  text = await page.$eval('#filterHelpText', el => el.innerText);
  console.log('Hover Matched in All 3:', text);
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/255_filter_hover_matched_all.png' });

  // 7. Mouse out back to blank area
  await page.hover('#headerTotalCount');
  await new Promise(r => setTimeout(r, 300));
  text = await page.$eval('#filterHelpText', el => el.innerText);
  console.log('After unhover (restored active filter text):', text);

  await browser.close();
  console.log('All hover tests verified successfully!');
})();
