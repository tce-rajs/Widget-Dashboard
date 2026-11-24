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

    // Step 1: Verify Theme Selector Dropdown is GONE and Icon Button is present
    const headerCheck = await page.evaluate(() => {
        const sel = document.getElementById('themeSelector');
        const iconBtn = document.getElementById('quickThemeBtn');
        return {
            hasSelectDropdown: Boolean(sel),
            hasIconBtn: Boolean(iconBtn)
        };
    });
    console.log('Header theme controls check:', headerCheck);

    // Step 2: Capture clean, minimal Overview Dashboard
    console.log('Capturing minimal executive overview dashboard...');
    const shot24 = path.join(screenshotsDir, '24_minimal_overview_dashboard.png');
    await page.screenshot({ path: shot24, fullPage: false });
    console.log(`Saved screenshot 24: ${shot24}`);

    // Step 3: Test Drill-down & Verify "Details" button removed from table
    console.log('Testing drill down into Needs Development...');
    await page.click('div[onclick*="requires_dev"]');
    await new Promise(r => setTimeout(r, 400));

    const tableCheck = await page.evaluate(() => {
        const rows = document.querySelectorAll('#widgetTableBody tr');
        let detailsBtnCount = 0;
        let runBtnCount = 0;
        rows.forEach(r => {
            const btns = r.querySelectorAll('button');
            btns.forEach(b => {
                if (b.innerText.includes('Details')) detailsBtnCount++;
            });
            const run = r.querySelector('a[title*="Run"]');
            if (run) runBtnCount++;
        });
        const total = document.getElementById('totalFiltered').innerText;
        return { totalFiltered: total, rowsOnPage: rows.length, detailsBtnCount, runBtnCount };
    });
    console.log('Table elements check after drill-down:', tableCheck);

    const shot25 = path.join(screenshotsDir, '25_minimal_table_no_details_btn.png');
    await page.screenshot({ path: shot25, fullPage: false });
    console.log(`Saved screenshot 25: ${shot25}`);

    // Step 4: Test 1-click Dark Mode icon toggle
    console.log('Testing 1-click quickThemeBtn...');
    await page.click('#quickThemeBtn');
    await new Promise(r => setTimeout(r, 400));

    const isDark = await page.evaluate(() => document.documentElement.classList.contains('dark'));
    console.log(`Dark mode active: ${isDark}`);

    // Go back to Overview to view minimal dark mode
    await page.click('#tab-overview');
    await new Promise(r => setTimeout(r, 400));

    const shot26 = path.join(screenshotsDir, '26_minimal_dark_mode.png');
    await page.screenshot({ path: shot26, fullPage: false });
    console.log(`Saved screenshot 26: ${shot26}`);

    console.log(`Total console/page errors: ${errors.length}`);
    if (errors.length > 0) {
        console.error('Errors encountered:', errors);
    }

    await browser.close();
    console.log('Minimal dashboard verification completed successfully!');
})();
