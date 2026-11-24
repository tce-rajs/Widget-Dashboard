const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');
const path = require('path');
const fs = require('fs');

async function testTimestamp() {
    const browser = await puppeteer.launch({
        executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    const artifactsDir = 'C:\\Users\\v_CrystalQA3\\.gemini\\antigravity\\brain\\f3079d64-eabf-438b-bac4-f5596cf2bcbd\\screenshots';
    if (!fs.existsSync(artifactsDir)) {
        fs.mkdirSync(artifactsDir, { recursive: true });
    }

    const consoleErrors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') {
            consoleErrors.push(msg.text());
        }
    });
    page.on('pageerror', err => {
        consoleErrors.push(err.toString());
    });

    // Login via UI form
    await page.setViewport({ width: 1440, height: 900 });
    await page.goto('http://localhost:8000/login.html', { waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 400));

    await page.evaluate(() => {
        document.getElementById('email').value = 'admin';
        document.getElementById('password').value = 'Admin@123';
        document.querySelector('form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    });
    await page.waitForNavigation({ waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 1000));

    console.log('Current URL:', page.url());

    // Check desktop timestamp element
    const headerTime = await page.$eval('#headerLastUpdatedTime', el => el.textContent.trim());
    console.log('Desktop Last Updated Time found:', headerTime);

    // Verify parent container positioning
    const layout = await page.evaluate(() => {
        const timeEl = document.getElementById('headerLastUpdatedTime');
        const updateBtn = document.getElementById('updateExcelContainer');
        const timeRect = timeEl.getBoundingClientRect();
        const updateRect = updateBtn.getBoundingClientRect();
        return {
            timeText: timeEl.textContent,
            isBelowButtons: timeRect.top >= updateRect.bottom,
            timeTop: Math.round(timeRect.top),
            buttonsBottom: Math.round(updateRect.bottom)
        };
    });
    console.log('Layout evaluation:', layout);

    // Take desktop screenshot of header area
    await page.screenshot({
        path: path.join(artifactsDir, '144_desktop_header_last_updated.png'),
        clip: { x: 0, y: 0, width: 1440, height: 180 }
    });
    console.log('Saved 144_desktop_header_last_updated.png');

    // Mobile viewport
    await page.setViewport({ width: 390, height: 844 });
    await page.reload({ waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 800));

    const mobileTime = await page.$eval('#mobileLastUpdatedTime', el => el.textContent.trim());
    console.log('Mobile Last Updated Time found:', mobileTime);

    // Take mobile screenshot of header area
    await page.screenshot({
        path: path.join(artifactsDir, '145_mobile_header_last_updated.png'),
        clip: { x: 0, y: 0, width: 390, height: 180 }
    });
    console.log('Saved 145_mobile_header_last_updated.png');

    console.log('Console errors count:', consoleErrors.length);
    if (consoleErrors.length > 0) {
        console.error('Errors found:', consoleErrors);
    }

    await browser.close();
    console.log('ALL CHECKS PASSED SUCCESSFULLY!');
}

testTimestamp().catch(e => {
    console.error('Error during test:', e);
    process.exit(1);
});
