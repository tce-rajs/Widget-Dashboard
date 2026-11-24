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

    // Step 1: Verify clean Overview Dashboard
    console.log('Capturing clean overview dashboard (clumsy boxes removed)...');
    const shot18 = path.join(screenshotsDir, '18_clean_dashboard_overview.png');
    await page.screenshot({ path: shot18, fullPage: false });
    console.log(`Saved screenshot 18: ${shot18}`);

    // Step 2: Hover over "Update Excel" button
    console.log('Hovering over #updateExcelContainer...');
    await page.hover('#updateExcelContainer button');
    await new Promise(r => setTimeout(r, 400));

    const popoverVisible = await page.evaluate(() => {
        const container = document.getElementById('updateExcelContainer');
        const popover = container ? container.querySelector('.app-card') : null;
        if (!popover) return false;
        const style = window.getComputedStyle(popover.parentElement);
        return style.display !== 'none';
    });
    console.log(`Popover visible on hover: ${popoverVisible}`);

    const shot19 = path.join(screenshotsDir, '19_hover_update_excel_popover.png');
    await page.screenshot({ path: shot19, fullPage: false });
    console.log(`Saved screenshot 19: ${shot19}`);

    // Step 3: Switch to Dark Mode and hover
    console.log('Switching to Dark Mode...');
    await page.evaluate(() => changeTheme('dark'));
    await new Promise(r => setTimeout(r, 400));

    await page.hover('#updateExcelContainer button');
    await new Promise(r => setTimeout(r, 400));

    const shot20 = path.join(screenshotsDir, '20_dark_mode_update_excel_popover.png');
    await page.screenshot({ path: shot20, fullPage: false });
    console.log(`Saved screenshot 20: ${shot20}`);

    console.log(`Total console/page errors: ${errors.length}`);
    if (errors.length > 0) {
        console.error('Errors encountered:', errors);
    }

    await browser.close();
    console.log('Hover verification finished successfully!');
})();
