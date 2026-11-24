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
        if (msg.type() === 'error') errors.push(`[Console Error] ${msg.text()}`);
    });
    page.on('pageerror', err => errors.push(`[Page Error] ${err.message}`));

    console.log('Navigating to http://localhost:8000/index.html ...');
    await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle0' });

    const outDir = 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots';
    if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

    // 1. Check navigation tabs
    const visibleNavTabs = await page.$$eval('.nav-tab:not(.hidden)', els => els.map(e => e.innerText.trim()));
    console.log('Visible Nav Tabs:', visibleNavTabs);
    
    const qaTabExists = await page.$('#tab-qa');
    console.log('#tab-qa exists in DOM:', qaTabExists !== null);

    const qaViewExists = await page.$('#view-qa');
    console.log('#view-qa exists in DOM:', qaViewExists !== null);

    // 2. Overview Screenshot
    await page.screenshot({ path: path.join(outDir, '76_two_tab_overview_dark.png') });
    console.log('Captured 76_two_tab_overview_dark.png');

    const headerEl = await page.$('header');
    if (headerEl) {
        await headerEl.screenshot({ path: path.join(outDir, '77_two_tab_header_clean.png') });
        console.log('Captured 77_two_tab_header_clean.png');
    }

    // 3. Check KPI Card values
    const kpiQa = await page.$eval('#stat-qa-tools', el => el.innerText.trim());
    const kpiTotal = await page.$eval('#stat-total-repo', el => el.innerText.trim());
    const kpiPresent = await page.$eval('#stat-present-both', el => el.innerText.trim());
    const kpiMissing = await page.$eval('#stat-missing-repo', el => el.innerText.trim());
    const kpiExtra = await page.$eval('#stat-extra-repo', el => el.innerText.trim());
    const kpiDev = await page.$eval('#stat-dev-num', el => el.innerText.trim());
    console.log(`KPIs: QA=${kpiQa}, TotalAssets=${kpiTotal}, Present=${kpiPresent}, Missing=${kpiMissing}, Extra=${kpiExtra}, Dev=${kpiDev}`);

    // 4. Click QA KPI Card -> drill down to All Widgets with QA filter
    console.log('Clicking QA KPI Card (#card-kpi-qa)...');
    await page.click('#card-kpi-qa');
    await new Promise(r => setTimeout(r, 400));

    const activeViewInventory = await page.$eval('#view-inventory', el => !el.classList.contains('hidden'));
    const qaPillCls = await page.$eval('#pill-filter-qa_verified', el => el.className);
    const totalFilteredQa = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`All Widgets View Active: ${activeViewInventory}, QA Pill Active: ${qaPillCls.includes('bg-blue-600')}, Filtered Count: ${totalFilteredQa}`);

    await page.screenshot({ path: path.join(outDir, '78_all_widgets_qa_filtered.png') });
    console.log('Captured 78_all_widgets_qa_filtered.png');

    // 5. Open Modal on first row
    console.log('Opening modal on first row in QA filter...');
    const firstRow = await page.$('#widgetTableBody tr');
    if (firstRow) {
        await firstRow.click();
        await new Promise(r => setTimeout(r, 400));

        const modalVisible = await page.$eval('#widgetModal', el => !el.classList.contains('hidden'));
        const modalQaVisible = await page.$eval('#modalQaSection', el => !el.classList.contains('hidden'));
        const modalQaText = await page.$eval('#modalQaSection', el => el.innerText.trim());
        console.log(`Modal Visible: ${modalVisible}, QA Section Visible: ${modalQaVisible}`);
        console.log('QA Section Text snippet:', modalQaText.split('\n')[0]);

        await page.screenshot({ path: path.join(outDir, '79_modal_qa_details.png') });
        console.log('Captured 79_modal_qa_details.png');

        // Close modal via Escape key
        await page.keyboard.press('Escape');
        await new Promise(r => setTimeout(r, 400));
        const modalHidden = await page.$eval('#widgetModal', el => el.classList.contains('hidden'));
        console.log(`Modal Closed cleanly: ${modalHidden}`);
    }

    // 6. Test All Required Pill
    console.log('Clicking All Required pill...');
    await page.click('#pill-filter-all');
    await new Promise(r => setTimeout(r, 400));
    const allRequiredCount = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`All Required Filtered Count: ${allRequiredCount}`);

    // 7. Test Search by QA Tool UID
    console.log('Testing search by QA tool UID (tool-0001)...');
    await page.type('#widgetSearch', 'tool-');
    await new Promise(r => setTimeout(r, 400));
    const searchCount = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`Search by 'tool-' returned: ${searchCount} widgets`);
    // Clear search
    await page.$eval('#widgetSearch', el => el.value = '');
    await page.type('#widgetSearch', ' ');
    await page.keyboard.press('Backspace');
    await new Promise(r => setTimeout(r, 300));

    // 7. Light Theme Overview Screenshot
    await page.click('#tab-overview');
    await new Promise(r => setTimeout(r, 300));
    const themeBtn = await page.$('#themeToggleBtn');
    if (themeBtn) {
        await themeBtn.click();
        await new Promise(r => setTimeout(r, 300));
        await page.screenshot({ path: path.join(outDir, '80_two_tab_overview_light.png') });
        console.log('Captured 80_two_tab_overview_light.png');
        // switch back to dark
        await themeBtn.click();
        await new Promise(r => setTimeout(r, 200));
    }

    console.log('\n--- VERIFICATION SUMMARY ---');
    console.log(`Total Errors Detected: ${errors.length}`);
    if (errors.length > 0) {
        errors.forEach(e => console.error(e));
    } else {
        console.log('SUCCESS: 0 console or runtime errors!');
    }

    await browser.close();
})();
