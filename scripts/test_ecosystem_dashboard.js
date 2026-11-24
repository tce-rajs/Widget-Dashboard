const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');
const path = require('path');
const fs = require('fs');

async function testEcosystemDashboard() {
    console.log('Starting Complete E2E Testing for Mobile-Friendly Reordered Dashboard...');

    const screenshotDir = 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots';
    if (!fs.existsSync(screenshotDir)) {
        fs.mkdirSync(screenshotDir, { recursive: true });
    }

    const browser = await puppeteer.launch({
        executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 960 });

    const errors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') {
            errors.push(msg.text());
            console.error('Browser console error:', msg.text());
        }
    });

    page.on('pageerror', err => {
        errors.push(err.message);
        console.error('Page error:', err.message);
    });

    const url = 'http://localhost:8000/index.html';
    // Log in as Developer (nitin) to test default restricted visibility
    console.log('Logging in as Developer (nitin) via login.html...');
    await page.goto('http://localhost:8000/login.html', { waitUntil: 'networkidle0' });
    await page.type('#email', 'nitin');
    await page.type('#password', 'Nitin@123');
    await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle0' }),
        page.click('button[type="submit"]')
    ]);
    console.log(`Current page after login: ${page.url()}`);

    // Force Dark Mode for consistent styling
    await page.evaluate(() => {
        if (typeof changeTheme === 'function') changeTheme('dark');
    });
    await new Promise(r => setTimeout(r, 400));

    // 1. Verify Top Title and Header
    const titleText = await page.$eval('h1', el => el.innerText.trim());
    console.log(`[PASS] Header Title: "${titleText}"`);
    if (titleText.toLowerCase().includes('ceo')) {
        errors.push(`Header title contains forbidden word 'CEO': ${titleText}`);
    }
    if (titleText.toLowerCase().includes('reconciliation')) {
        errors.push(`Header title contains forbidden word 'reconciliation': ${titleText}`);
    }

    // 1b. Verify "100% Checked" badge is removed
    const headerText = await page.$eval('header', el => el.innerText);
    if (headerText.includes('100% Checked')) {
        errors.push('Header still contains "100% Checked" mark badge!');
    } else {
        console.log('[PASS] Verified "100% Checked" mark is completely removed from header');
    }

    // 1c. Verify No Forbidden Words in Visible Overview Text
    const visibleOverviewText = await page.$eval('#view-overview', el => el.innerText);
    const forbiddenWords = ['reconciliation', 'reconciled', 'discrepancies', 'inconsistencies', 'empirical audit'];
    for (const word of forbiddenWords) {
        if (visibleOverviewText.toLowerCase().includes(word)) {
            errors.push(`Visible overview text contains forbidden jargon word: '${word}'`);
        } else {
            console.log(`[PASS] Verified zero occurrences of '${word}' in visible overview`);
        }
    }

    // 2. Verify Hidden Sections (Risk Analysis, Action Plan, Project Status, Docs Tab, Removed Button)
    const isInsightsHidden = await page.$eval('#section-management-insights', el => el.classList.contains('hidden'));
    const isActionPlanHidden = await page.$eval('#section-management-action-plan', el => el.classList.contains('hidden'));
    const isProjectStatusHidden = await page.$eval('#section-project-status-overview', el => el.classList.contains('hidden'));
    const isDocsTabHidden = await page.$eval('#tab-docs', el => el.classList.contains('hidden'));
    const statusBriefBtn = await page.$('button[onclick="openStatusReportModal()"]');

    console.log(`[PASS] Management Insights Hidden: ${isInsightsHidden}`);
    console.log(`[PASS] Prioritized Action Plan Hidden: ${isActionPlanHidden}`);
    console.log(`[PASS] Project Status Section Hidden: ${isProjectStatusHidden}`);
    console.log(`[PASS] Documentation Tab Hidden: ${isDocsTabHidden}`);
    console.log(`[PASS] Status Brief Button Removed: ${statusBriefBtn === null}`);

    if (!isInsightsHidden || !isActionPlanHidden) {
        errors.push('Management Insights or Action Plan is not hidden!');
    }
    if (!isProjectStatusHidden) {
        errors.push('Project Status Section is not hidden!');
    }
    if (!isDocsTabHidden) {
        errors.push('Documentation tab is not hidden!');
    }
    if (statusBriefBtn !== null) {
        errors.push('Status Brief button was not removed!');
    }

    // 3. Screenshot 1: Desktop Top KPI Cards & Progress Bars
    await page.screenshot({ path: path.join(screenshotDir, '118_desktop_top_dark.png'), fullPage: false });
    console.log('[PASS] Captured 118_desktop_top_dark.png');

    // 4. Test Clickable Numbers Drill-Down:
    console.log('Testing click on "12 backlog simulations" in Progress Bar...');
    await page.$eval('span[onclick="drillDown(\'requires_dev\')"]', el => el.click());
    await new Promise(r => setTimeout(r, 400));
    let count = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`[PASS] Filtered for backlog simulations: ${count} (Expected: 12)`);
    if (count !== '12') errors.push(`Expected 12 backlog simulations, got ${count}`);

    // Return to Overview
    await page.click('#tab-overview');
    await new Promise(r => setTimeout(r, 300));

    // 5. Test Mobile Responsiveness (Viewport: 375x812 iPhone)
    console.log('\nTesting Mobile Viewport (375x812 iPhone)...');
    await page.setViewport({ width: 375, height: 812, isMobile: true, hasTouch: true });
    await page.goto(url, { waitUntil: 'networkidle0' });
    await page.evaluate(() => { if (typeof changeTheme === 'function') changeTheme('dark'); });
    await new Promise(r => setTimeout(r, 400));

    // Check horizontal overflow
    const isOverflowing = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    console.log(`[PASS] Mobile Horizontal Overflow Free: ${!isOverflowing}`);
    if (isOverflowing) errors.push('Page has horizontal overflow on 375px mobile viewport!');

    // Capture Mobile Overview Screenshot
    await page.screenshot({ path: path.join(screenshotDir, '119_mobile_375_top.png'), fullPage: false });
    console.log('[PASS] Captured 119_mobile_375_top.png');

    // Scroll to charts & mobile subject cards
    await page.evaluate(() => window.scrollBy(0, 650));
    await new Promise(r => setTimeout(r, 300));
    await page.screenshot({ path: path.join(screenshotDir, '120_mobile_375_charts.png'), fullPage: false });
    console.log('[PASS] Captured 120_mobile_375_charts.png');

    await page.evaluate(() => window.scrollBy(0, 650));
    await new Promise(r => setTimeout(r, 300));
    await page.screenshot({ path: path.join(screenshotDir, '121_mobile_375_subject_cards.png'), fullPage: false });
    console.log('[PASS] Captured 121_mobile_375_subject_cards.png');

    // Scroll to bottom (Mobile 3-Way Cards)
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await new Promise(r => setTimeout(r, 300));
    await page.screenshot({ path: path.join(screenshotDir, '122_mobile_375_bottom.png'), fullPage: false });
    console.log('[PASS] Captured 122_mobile_375_bottom.png');

    // 6. Test Mobile All Widgets Tab & Cards
    console.log('Testing Mobile All Widgets tab & cards...');
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.click('#tab-inventory');
    await new Promise(r => setTimeout(r, 400));
    const mobileCardsCount = await page.$$eval('#widgetMobileCardsList > div', els => els.length);
    console.log(`[PASS] Mobile Widget Cards Rendered: ${mobileCardsCount} cards`);
    if (mobileCardsCount === 0) errors.push('Mobile Widget Cards did not render!');
    await page.screenshot({ path: path.join(screenshotDir, '123_mobile_375_all_widgets_cards.png'), fullPage: false });
    console.log('[PASS] Captured 123_mobile_375_all_widgets_cards.png');

    await browser.close();

    console.log('\n======================================================');
    console.log('MOBILE & DESKTOP E2E TEST RESULTS:');
    console.log(`- Console/Page Errors: ${errors.length}`);
    if (errors.length > 0) {
        console.error('Errors encountered:', errors);
        process.exit(1);
    } else {
        console.log('- ALL DESKTOP & MOBILE TESTS PASSED WITH 0 ERRORS!');
    }
    console.log('======================================================');
}

testEcosystemDashboard().catch(err => {
    console.error('Test execution failed:', err);
    process.exit(1);
});
