const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');
const path = require('path');
const fs = require('fs');

(async () => {
    const browser = await puppeteer.launch({
        executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 950 });

    const errors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') errors.push(msg.text());
    });
    page.on('pageerror', err => errors.push(err.toString()));

    const targetUrl = 'http://localhost:8000/index.html';
    console.log(`Navigating to ${targetUrl}...`);
    await page.goto(targetUrl, { waitUntil: 'networkidle0' });

    const screenshotsDir = 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots';
    if (!fs.existsSync(screenshotsDir)) {
        fs.mkdirSync(screenshotsDir, { recursive: true });
    }

    // Step 1: Verify QA tab label and click it
    const tabText = await page.evaluate(() => {
        const tab = document.getElementById('tab-qa');
        return tab ? tab.innerText.replace(/\s+/g, ' ').trim() : null;
    });
    console.log('QA Tab Text:', tabText);

    console.log('Clicking #tab-qa...');
    await page.click('#tab-qa');
    await new Promise(r => setTimeout(r, 400));

    const viewData = await page.evaluate(() => {
        const view = document.getElementById('view-qa');
        const isVisible = !view.classList.contains('hidden');
        const h2 = view.querySelector('h2');
        return {
            isVisible,
            title: h2 ? h2.innerText : null
        };
    });
    console.log('QA View Status:', viewData);

    const shot27 = path.join(screenshotsDir, '27_comparison_with_qa_coming_soon.png');
    await page.screenshot({ path: shot27, fullPage: false });
    console.log(`Saved screenshot 27: ${shot27}`);

    // Step 2: Switch to Dark Mode
    console.log('Testing in Dark Mode...');
    await page.click('#quickThemeBtn');
    await new Promise(r => setTimeout(r, 400));

    const shot28 = path.join(screenshotsDir, '28_comparison_with_qa_dark.png');
    await page.screenshot({ path: shot28, fullPage: false });
    console.log(`Saved screenshot 28: ${shot28}`);

    console.log(`Total console/page errors: ${errors.length}`);
    if (errors.length > 0) {
        console.error('Errors encountered:', errors);
    }

    await browser.close();
    console.log('QA Coming Soon verification completed successfully!');
})();
