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

    // 1. Initial State: Overview in Dark Mode
    await page.screenshot({ path: path.join(outDir, '64_overview_dark_final.png') });
    console.log('Captured 64_overview_dark_final.png');

    // Header close-up
    const headerEl = await page.$('header');
    if (headerEl) {
        await headerEl.screenshot({ path: path.join(outDir, '65_header_nav_dark.png') });
        console.log('Captured 65_header_nav_dark.png');
    }

    // 2. Click "Extra in Repository" KPI card
    console.log('Clicking "Extra in Repository" card...');
    const extraCard = await page.$('#card-kpi-extra');
    if (extraCard) {
        await extraCard.click();
        await new Promise(r => setTimeout(r, 400));
        
        const count = await page.$eval('#totalFiltered', el => el.innerText.trim());
        const pillActive = await page.$eval('#pill-filter-extra_repo', el => el.className);
        console.log(`Extra in Repo filtered count: ${count}, pill active: ${pillActive.includes('bg-blue-600')}`);
        
        await page.screenshot({ path: path.join(outDir, '66_all_widgets_extra_filtered.png') });
        console.log('Captured 66_all_widgets_extra_filtered.png');
    } else {
        console.error('KPI extra card not found!');
    }

    // 3. Click "Needs Development" pill
    console.log('Clicking "Needs Development" pill...');
    await page.click('#pill-filter-requires_dev');
    await new Promise(r => setTimeout(r, 400));
    const devCount = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`Needs Development count: ${devCount}`);
    await page.screenshot({ path: path.join(outDir, '67_all_widgets_needs_dev_filtered.png') });
    console.log('Captured 67_all_widgets_needs_dev_filtered.png');

    // 4. Click "Missing from Repo" pill
    console.log('Clicking "Missing from Repo" pill...');
    await page.click('#pill-filter-source_missing');
    await new Promise(r => setTimeout(r, 400));
    const missingCount = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`Missing from Repo count: ${missingCount}`);

    // 5. Click "Present in Repo" pill
    console.log('Clicking "Present in Repo" pill...');
    await page.click('#pill-filter-source_present');
    await new Promise(r => setTimeout(r, 400));
    const presentCount = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`Present in Repo count: ${presentCount}`);

    // 6. Click "All Required" pill
    console.log('Clicking "All Required" pill...');
    await page.click('#pill-filter-all');
    await new Promise(r => setTimeout(r, 400));
    const allCount = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`All Required count: ${allCount}`);
    await page.screenshot({ path: path.join(outDir, '68_all_widgets_all_required.png') });
    console.log('Captured 68_all_widgets_all_required.png');

    // 7. Toggle to Light Mode
    console.log('Toggling to Light Mode...');
    await page.click('#quickThemeBtn');
    await new Promise(r => setTimeout(r, 300));
    await page.click('#tab-overview');
    await new Promise(r => setTimeout(r, 300));
    await page.screenshot({ path: path.join(outDir, '69_overview_light_final.png') });
    console.log('Captured 69_overview_light_final.png');

    // Check errors
    console.log('=== Console / Page Errors ===');
    if (errors.length === 0) {
        console.log('0 errors encountered! Everything passed smoothly.');
    } else {
        errors.forEach(e => console.error(e));
    }

    await browser.close();
})();
