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
    await page.setViewport({ width: 1440, height: 900 });

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

    // Step 1: Switch to Dark Mode to match user's reference image
    console.log('Activating Dark Mode...');
    await page.click('#quickThemeBtn');
    await new Promise(r => setTimeout(r, 400));

    // Inspect Header Elements
    const headerInfo = await page.evaluate(() => {
        const h1 = document.querySelector('header h1');
        const btns = Array.from(document.querySelectorAll('header .flex.items-center button, header #updateExcelContainer button')).map(b => b.innerText.trim());
        const tabs = Array.from(document.querySelectorAll('.nav-tab')).map(t => t.innerText.replace(/\s+/g, ' ').trim());
        return {
            title: h1 ? h1.innerText : null,
            buttons: btns,
            tabs: tabs
        };
    });
    console.log('Header verification details:', JSON.stringify(headerInfo, null, 2));

    // Capture Header & Top Viewport Screenshot
    const shot29 = path.join(screenshotsDir, '29_header_nav_matched_dark.png');
    await page.screenshot({ path: shot29, fullPage: false });
    console.log(`Saved screenshot 29: ${shot29}`);

    // Step 2: Switch to "All Widgets ( 294 )" tab
    console.log('Clicking "All Widgets ( 294 )" tab...');
    await page.click('#tab-inventory');
    await new Promise(r => setTimeout(r, 400));

    const shot30 = path.join(screenshotsDir, '30_tab_switched_matched.png');
    await page.screenshot({ path: shot30, fullPage: false });
    console.log(`Saved screenshot 30: ${shot30}`);

    console.log(`Total console/page errors: ${errors.length}`);
    if (errors.length > 0) {
        console.error('Errors encountered:', errors);
    }

    await browser.close();
    console.log('Matched header verification completed successfully!');
})();
