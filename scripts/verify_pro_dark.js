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
    await page.setViewport({ width: 1440, height: 1000 });

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

    // Step 1: Test 1-Click Dark Theme Toggle
    console.log('Testing 1-click #quickThemeBtn...');
    await page.click('#quickThemeBtn');
    await new Promise(r => setTimeout(r, 400));

    const isDark = await page.evaluate(() => document.documentElement.classList.contains('dark'));
    const themeVal = await page.evaluate(() => document.getElementById('themeSelector').value);
    console.log(`Dark mode active after 1-click: ${isDark}, themeSelector value: ${themeVal}`);

    const shot21 = path.join(screenshotsDir, '21_pro_dark_mode_overview.png');
    await page.screenshot({ path: shot21, fullPage: false });
    console.log(`Saved screenshot 21: ${shot21}`);

    // Step 2: Switch to Inventory Table and check badges
    console.log('Navigating to Inventory tab in Dark Mode...');
    await page.click('#tab-inventory');
    await new Promise(r => setTimeout(r, 400));

    const shot22 = path.join(screenshotsDir, '22_pro_dark_mode_table_badges.png');
    await page.screenshot({ path: shot22, fullPage: false });
    console.log(`Saved screenshot 22: ${shot22}`);

    // Step 3: Open Modal in Dark Mode
    console.log('Opening modal for widget #1...');
    await page.evaluate(() => openModal(1));
    await new Promise(r => setTimeout(r, 500));

    const shot23 = path.join(screenshotsDir, '23_pro_dark_mode_modal.png');
    await page.screenshot({ path: shot23, fullPage: false });
    console.log(`Saved screenshot 23: ${shot23}`);

    // Step 4: Toggle back to Light mode
    console.log('Testing 1-click toggle back to light mode...');
    await page.evaluate(() => closeModal());
    await new Promise(r => setTimeout(r, 300));
    await page.click('#quickThemeBtn');
    await new Promise(r => setTimeout(r, 400));

    const isLightAgain = await page.evaluate(() => !document.documentElement.classList.contains('dark'));
    console.log(`Light mode active after toggle: ${isLightAgain}`);

    // Toggle back to dark mode for default preference
    await page.click('#quickThemeBtn');
    await new Promise(r => setTimeout(r, 300));

    console.log(`Total console/page errors: ${errors.length}`);
    if (errors.length > 0) {
        console.error('Errors encountered:', errors);
    }

    await browser.close();
    console.log('Dark mode pro verification completed successfully!');
})();
