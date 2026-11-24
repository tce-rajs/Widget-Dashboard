const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  // Go to login page and log in directly via authManager
  await page.goto('http://localhost:8000/login.html', { waitUntil: 'networkidle2' });
  await page.evaluate(() => authManager.login('admin@company.com', 'Admin@123', true));

  // Navigate to index.html with active session
  await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle2' });

  // 1. Capture Pipeline Flow View (Light)
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/194_pipeline_flow_light.png' });
  console.log('Screenshot 194 captured: Pipeline Flow Light.');

  // 2. Toggle to Venn Diagram View (Light)
  await page.evaluate(() => setReconciliationView('venn'));
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/195_venn_diagram_light.png' });
  console.log('Screenshot 195 captured: Venn Diagram Light.');

  // 3. Toggle Dark Mode
  await page.evaluate(() => {
    document.documentElement.classList.add('dark');
  });
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/196_venn_diagram_dark.png' });
  console.log('Screenshot 196 captured: Venn Diagram Dark.');

  // 4. Toggle back to Pipeline Flow View (Dark)
  await page.evaluate(() => setReconciliationView('pipeline'));
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/197_pipeline_flow_dark.png' });
  console.log('Screenshot 197 captured: Pipeline Flow Dark.');

  // 5. Mobile Viewport (Dark)
  await page.setViewport({ width: 390, height: 844 });
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/198_pipeline_mobile_dark.png' });
  console.log('Screenshot 198 captured: Pipeline Mobile Dark.');

  await browser.close();
  console.log('All verification screenshots captured successfully!');
})();
