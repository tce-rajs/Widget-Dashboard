const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');
const fs = require('fs');
const path = require('path');

(async () => {
    const screenshotDir = 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots';
    const browser = await puppeteer.launch({
        executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const page = await browser.newPage();
    
    // Clear storage first
    await page.goto('http://localhost:8000/login.html', { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => localStorage.clear());

    // 1. Desktop Login Page
    await page.setViewport({ width: 1440, height: 900 });
    await page.goto('http://localhost:8000/login.html', { waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 600));
    await page.screenshot({ path: path.join(screenshotDir, '138_crystal_logo_login_desktop.png') });
    console.log('Saved 138_crystal_logo_login_desktop.png');

    // 2. Open Forgot Password Modal
    await page.click('button[onclick*="showForgotPasswordModal"]');
    await new Promise(r => setTimeout(r, 400));
    const modalText = await page.$eval('#forgotModal', el => el.innerText);
    console.log('--- Modal Text Content ---');
    console.log(modalText);
    console.log('--------------------------');
    if (modalText.includes('admin@company.com') || modalText.includes('@')) {
        console.error('ERROR: sample email still present in modal!');
    } else {
        console.log('[PASS] No sample email found in modal.');
    }
    await page.screenshot({ path: path.join(screenshotDir, '139_forgot_modal_professional.png') });
    console.log('Saved 139_forgot_modal_professional.png');

    // 3. Mobile Login Page
    await page.setViewport({ width: 375, height: 812, isMobile: true, hasTouch: true });
    await page.goto('http://localhost:8000/login.html', { waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 600));
    await page.screenshot({ path: path.join(screenshotDir, '140_crystal_logo_login_mobile.png') });
    console.log('Saved 140_crystal_logo_login_mobile.png');

    // 4. Log in as Admin and check Dashboard Header Logo
    await page.setViewport({ width: 1440, height: 900 });
    await page.goto('http://localhost:8000/login.html', { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => {
        document.getElementById('email').value = 'admin';
        document.getElementById('password').value = 'Admin@123';
        document.querySelector('form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    });
    await page.waitForNavigation({ waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 1000));
    await page.screenshot({ path: path.join(screenshotDir, '141_crystal_logo_dashboard_header.png') });
    console.log('Saved 141_crystal_logo_dashboard_header.png');

    await browser.close();
    console.log('All screenshots and verifications completed successfully!');
})();
