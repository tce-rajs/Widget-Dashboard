const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');
const path = require('path');
const fs = require('fs');

const SCREENSHOT_DIR = 'C:\\Users\\v_CrystalQA3\\.gemini\\antigravity\\brain\\f3079d64-eabf-438b-bac4-f5596cf2bcbd\\screenshots';
if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function run() {
    console.log("Launching Puppeteer for UI Alignment and Login Card verification...");
    const browser = await puppeteer.launch({
        executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();

    // 1. Verify Login Card - Light Mode
    await page.setViewport({ width: 1280, height: 800 });
    await page.goto('http://localhost:8000/login.html', { waitUntil: 'networkidle0' });
    // Clear any previous session
    await page.evaluate(() => {
        localStorage.clear();
        sessionStorage.clear();
        document.documentElement.classList.remove('dark');
        localStorage.setItem('theme-preference', 'light');
    });
    await page.goto('http://localhost:8000/login.html', { waitUntil: 'networkidle0' });
    await page.waitForSelector('main form');
    await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '149_elevated_login_card_light.png'),
        fullPage: true
    });
    console.log("Captured: 149_elevated_login_card_light.png");

    // 2. Verify Login Card - Dark Mode
    await page.evaluate(() => {
        document.documentElement.classList.add('dark');
        localStorage.setItem('theme-preference', 'dark');
        const themeIcon = document.getElementById('themeIcon');
        if (themeIcon) themeIcon.setAttribute('data-lucide', 'sun');
        lucide.createIcons();
    });
    await new Promise(r => setTimeout(r, 400));
    await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '150_elevated_login_card_dark.png'),
        fullPage: true
    });
    console.log("Captured: 150_elevated_login_card_dark.png");

    // 3. Verify Login Card - Forgot Modal
    await page.click('button[onclick="showForgotPasswordModal()"]');
    await new Promise(r => setTimeout(r, 400));
    await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '151_elevated_login_forgot_modal.png'),
        fullPage: true
    });
    console.log("Captured: 151_elevated_login_forgot_modal.png");

    // 4. Log in as Admin and Verify Desktop Header Alignment
    await page.goto('http://localhost:8000/login.html', { waitUntil: 'networkidle0' });
    await page.type('#email', 'admin@company.com');
    await page.type('#password', 'Admin@123');
    await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle0' }),
        page.click('#submitBtn')
    ]);

    // Measure bounding boxes of the desktop action controls
    const layoutMetrics = await page.evaluate(() => {
        const userPill = document.getElementById('userProfilePill')?.getBoundingClientRect();
        const themeBtn = document.getElementById('quickThemeBtn')?.getBoundingClientRect();
        const updateExcel = document.getElementById('updateExcelContainer')?.getBoundingClientRect();
        const exportBtn = document.getElementById('desktopExportBtn')?.getBoundingClientRect();
        const lastUpdated = document.getElementById('headerLastUpdatedTime')?.getBoundingClientRect();

        return {
            userPill: userPill ? { top: userPill.top, height: userPill.height, bottom: userPill.bottom } : null,
            themeBtn: themeBtn ? { top: themeBtn.top, height: themeBtn.height, bottom: themeBtn.bottom } : null,
            updateExcel: updateExcel ? { top: updateExcel.top, height: updateExcel.height, bottom: updateExcel.bottom } : null,
            exportBtn: exportBtn ? { top: exportBtn.top, height: exportBtn.height, bottom: exportBtn.bottom } : null,
            lastUpdated: lastUpdated ? { top: lastUpdated.top, right: lastUpdated.right } : null
        };
    });

    console.log("Desktop Header Controls Geometry:", JSON.stringify(layoutMetrics, null, 2));

    // Capture desktop header screenshot
    const headerEl = await page.$('header');
    if (headerEl) {
        await headerEl.screenshot({
            path: path.join(SCREENSHOT_DIR, '152_aligned_desktop_header_light.png')
        });
        console.log("Captured: 152_aligned_desktop_header_light.png");
    }

    // Toggle Dark Mode in Dashboard
    await page.click('#quickThemeBtn');
    await new Promise(r => setTimeout(r, 400));
    if (headerEl) {
        await headerEl.screenshot({
            path: path.join(SCREENSHOT_DIR, '153_aligned_desktop_header_dark.png')
        });
        console.log("Captured: 153_aligned_desktop_header_dark.png");
    }

    // 5. Mobile Viewport Alignment Check
    await page.setViewport({ width: 390, height: 844, isMobile: true });
    await new Promise(r => setTimeout(r, 400));
    await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '154_aligned_mobile_header.png')
    });
    console.log("Captured: 154_aligned_mobile_header.png");

    await browser.close();
    console.log("All UI alignment and login card verification tests completed successfully!");
}

run().catch(err => {
    console.error("Test error:", err);
    process.exit(1);
});
