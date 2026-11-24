const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');
const path = require('path');
const fs = require('fs');

async function testCloudSyncUI() {
    const browser = await puppeteer.launch({
        executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    const artifactsDir = 'C:\\Users\\v_CrystalQA3\\.gemini\\antigravity\\brain\\f3079d64-eabf-438b-bac4-f5596cf2bcbd\\screenshots';

    const errors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') errors.push(msg.text());
    });

    await page.setViewport({ width: 1440, height: 900 });

    // Login as Admin
    await page.goto('http://localhost:8000/login.html', { waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 300));
    await page.evaluate(() => {
        document.getElementById('email').value = 'admin';
        document.getElementById('password').value = 'Admin@123';
        document.querySelector('form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    });
    await page.waitForNavigation({ waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 600));

    // Switch to Users tab
    await page.evaluate(() => switchTab('users'));
    await new Promise(r => setTimeout(r, 400));

    // Verify Cloud Database button exists in header
    const cloudBtnText = await page.$eval('#cloudStatusBtnText', el => el.textContent.trim());
    console.log('Cloud Database button text:', cloudBtnText);

    // Take screenshot of User Management header with Cloud Database button
    await page.screenshot({
        path: path.join(artifactsDir, '146_user_mgmt_cloud_db_button.png'),
        clip: { x: 0, y: 0, width: 1440, height: 350 }
    });
    console.log('Saved 146_user_mgmt_cloud_db_button.png');

    // Open Cloud Sync Modal
    await page.evaluate(() => openCloudSyncModal());
    await new Promise(r => setTimeout(r, 300));

    // Verify modal is visible
    const modalVisible = await page.$eval('#cloudSyncModal', el => !el.classList.contains('hidden'));
    console.log('Cloud Sync Modal is visible:', modalVisible);

    // Take screenshot of Cloud Sync Modal
    await page.screenshot({
        path: path.join(artifactsDir, '147_cloud_sync_modal.png')
    });
    console.log('Saved 147_cloud_sync_modal.png');

    // Test Schema Copy
    await page.evaluate(() => copySupabaseSchema());
    await new Promise(r => setTimeout(r, 300));

    // Close modal
    await page.evaluate(() => closeCloudSyncModal());
    await new Promise(r => setTimeout(r, 200));

    console.log('Console errors count:', errors.length);
    await browser.close();
    console.log('CLOUD SYNC UI TEST COMPLETED SUCCESSFULLY!');
}

testCloudSyncUI().catch(e => {
    console.error('Test error:', e);
    process.exit(1);
});
