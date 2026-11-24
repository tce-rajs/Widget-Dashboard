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
    await page.setViewport({ width: 1440, height: 1100 });

    const errors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') errors.push(msg.text());
    });
    page.on('pageerror', err => errors.push(err.toString()));

    const targetUrl = 'http://localhost:8000/index.html';
    console.log(`Navigating to ${targetUrl}...`);
    await page.goto(targetUrl, { waitUntil: 'networkidle0' });

    // Step 1: Switch to Dark Mode
    console.log('Testing Dark Mode toggle...');
    await page.evaluate(() => changeTheme('dark'));
    await new Promise(r => setTimeout(r, 500));

    const isDark = await page.evaluate(() => document.documentElement.classList.contains('dark'));
    console.log(`Is dark mode active: ${isDark}`);

    const screenshotsDir = 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots';
    if (!fs.existsSync(screenshotsDir)) {
        fs.mkdirSync(screenshotsDir, { recursive: true });
    }

    const darkShot = path.join(screenshotsDir, '16_dark_mode_enhanced.png');
    await page.screenshot({ path: darkShot, fullPage: false });
    console.log(`Saved screenshot: ${darkShot}`);

    // Step 2: Test Available Widgets and Run button
    console.log('Filtering by Codebase: Already Available (available)...');
    await page.select('#statusFilter', 'available');
    await new Promise(r => setTimeout(r, 400));

    const tableReport = await page.evaluate(() => {
        const rows = document.querySelectorAll('#widgetTableBody tr');
        let count = 0;
        let withRunBtn = 0;
        const sampleWidgets = [];

        rows.forEach(r => {
            const cells = r.querySelectorAll('td');
            if (cells.length < 7) return;
            count++;
            const sr = cells[0].innerText.trim();
            const name = cells[2].innerText.trim();
            const runBtn = cells[6].querySelector('a[href]');
            const hasRun = Boolean(runBtn && runBtn.innerText.includes('Run'));
            const target = runBtn ? runBtn.getAttribute('target') : null;
            const href = runBtn ? runBtn.getAttribute('href') : null;
            if (hasRun) withRunBtn++;

            if (sampleWidgets.length < 6) {
                sampleWidgets.push({ sr, name, hasRun, target, href });
            }
        });

        const totalFiltered = document.getElementById('totalFiltered').innerText;
        return { totalFiltered, rowsOnPage: count, withRunBtn, sampleWidgets };
    });

    console.log('Table report for available widgets:', JSON.stringify(tableReport, null, 2));

    // Step 3: Open details modal for widget #4 (Lungs)
    console.log('Opening modal for #4 Lungs directly via openModal(4)...');
    await page.evaluate(() => openModal(4));
    await new Promise(r => setTimeout(r, 600));

    const modalData = await page.evaluate(() => {
        const modal = document.getElementById('widgetModal');
        const isVisible = !modal.classList.contains('hidden');
        const sr = document.getElementById('modalSr').innerText;
        const name = document.getElementById('modalName').innerText;
        const liveCard = document.getElementById('modalLiveCard');
        const liveCardText = liveCard ? liveCard.innerText : '';
        const runBtn = liveCard ? liveCard.querySelector('a[href]') : null;
        const footerBtn = document.getElementById('modalActionSlot').querySelector('a[href]');
        return {
            isVisible,
            sr,
            name,
            liveCardVisible: !liveCard.classList.contains('hidden'),
            liveCardText: liveCardText,
            runBtnText: runBtn ? runBtn.innerText.trim() : null,
            runBtnHref: runBtn ? runBtn.getAttribute('href') : null,
            runBtnTarget: runBtn ? runBtn.getAttribute('target') : null,
            footerBtnText: footerBtn ? footerBtn.innerText.trim() : null,
            footerBtnHref: footerBtn ? footerBtn.getAttribute('href') : null,
            footerBtnTarget: footerBtn ? footerBtn.getAttribute('target') : null
        };
    });

    console.log('Modal details for #4 Lungs:', JSON.stringify(modalData, null, 2));

    const modalShot = path.join(screenshotsDir, '17_available_widget_modal_run.png');
    await page.screenshot({ path: modalShot, fullPage: false });
    console.log(`Saved screenshot: ${modalShot}`);

    console.log(`Total console/page errors: ${errors.length}`);
    if (errors.length > 0) {
        console.error('Errors encountered:', errors);
    }

    await browser.close();
    console.log('Verification finished successfully!');
})();
