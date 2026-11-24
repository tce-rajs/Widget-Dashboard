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

    // Step 1: Check footer elements
    const footerData = await page.evaluate(() => {
        const footerTag = document.querySelector('footer');
        const lastUp = document.getElementById('lastUpdatedTime');
        const ovUp = document.getElementById('overviewLastUpdated');
        return {
            hasBulkyFooterTag: Boolean(footerTag),
            bottomLastUpdatedText: lastUp ? lastUp.innerText : null,
            overviewLastUpdatedText: ovUp ? ovUp.innerText : null
        };
    });
    console.log('Footer & Timestamp verification details:', footerData);

    // Scroll to bottom to view minimal timestamp
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await new Promise(r => setTimeout(r, 400));

    const shot31 = path.join(screenshotsDir, '31_minimal_footer_timestamp.png');
    await page.screenshot({ path: shot31, fullPage: false });
    console.log(`Saved screenshot 31: ${shot31}`);

    // Step 2: Switch to Dark Mode and view timestamp
    console.log('Testing Dark Mode...');
    await page.click('#quickThemeBtn');
    await new Promise(r => setTimeout(r, 400));

    const shot32 = path.join(screenshotsDir, '32_minimal_footer_dark.png');
    await page.screenshot({ path: shot32, fullPage: false });
    console.log(`Saved screenshot 32: ${shot32}`);

    console.log(`Total console/page errors: ${errors.length}`);
    if (errors.length > 0) {
        console.error('Errors encountered:', errors);
    }

    await browser.close();
    console.log('Minimal footer & timestamp verification completed successfully!');
})();
