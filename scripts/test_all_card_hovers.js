const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');

async function testCardHover(cardId, name, darkMode = true) {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 950 });

  await page.goto('http://localhost:8000/login.html', { waitUntil: 'networkidle2' });
  await page.evaluate(() => authManager.login('admin@company.com', 'Admin@123', true));
  await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle2' });

  if (darkMode) {
    await page.evaluate(() => {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    });
    await new Promise(r => setTimeout(r, 200));
  }

  await page.hover(cardId);
  await new Promise(r => setTimeout(r, 600));

  await page.screenshot({ path: `C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/${name}.png` });
  await browser.close();
}

(async () => {
  await testCardHover('#card-kpi-total', '386_card1_dark');
  await testCardHover('#card-kpi-xl', '387_card2_dark');
  await testCardHover('#card-kpi-qa', '388_card3_dark');
  await testCardHover('#card-kpi-attention', '389_card4_dark');
  await testCardHover('#card-kpi-git', '390_card5_dark');
  console.log('All 5 cards captured!');
})();
