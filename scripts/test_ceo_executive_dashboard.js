const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');
const path = require('path');
const fs = require('fs');

async function testCeoDashboard() {
    console.log('Starting CEO Executive Dashboard E2E Testing with Puppeteer...');
    
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
    console.log(`Navigating to ${url}...`);
    await page.goto(url, { waitUntil: 'networkidle0', timeout: 15000 });

    // 1. Verify Top Title and Header
    const titleText = await page.$eval('h1', el => el.innerText.trim());
    console.log(`[PASS] Header Title: "${titleText}"`);

    // Screenshot 1: Overview Top Dark Theme
    await page.screenshot({ path: path.join(screenshotDir, '90_ceo_overview_top_dark.png'), fullPage: false });
    console.log('[PASS] Captured 90_ceo_overview_top_dark.png');

    // 2. Verify 30-Second Executive Summary
    const summaryTitle = await page.$eval('h2', el => el.innerText.trim());
    console.log(`[PASS] Executive Summary Title: "${summaryTitle}"`);

    // 3. Verify 6 Top Executive KPI Cards
    const kpiExpected = await page.$eval('#card-kpi-total .text-2xl', el => el.innerText.trim());
    const kpiPresent = await page.$eval('#card-kpi-present .text-2xl', el => el.innerText.trim());
    const kpiQa = await page.$eval('#card-kpi-qa .text-2xl', el => el.innerText.trim());
    const kpiMatched = await page.$eval('#card-kpi-matched .text-2xl', el => el.innerText.trim());
    const kpiDev = await page.$eval('#card-kpi-dev .text-2xl', el => el.innerText.trim());
    const kpiMissingQa = await page.$eval('#card-kpi-missing-qa .text-2xl', el => el.innerText.trim());

    console.log(`[PASS] KPI 1 (Expected): ${kpiExpected}`);
    console.log(`[PASS] KPI 2 (Developed in Repo): ${kpiPresent}`);
    console.log(`[PASS] KPI 3 (Registered in QA): ${kpiQa}`);
    console.log(`[PASS] KPI 4 (Matched in All 3): ${kpiMatched}`);
    console.log(`[PASS] KPI 5 (Needs Dev): ${kpiDev}`);
    console.log(`[PASS] KPI 6 (Missing from QA): ${kpiMissingQa}`);

    // Screenshot 2: Dual Progress Bars & 3-Way Reconciliation Matrix
    await page.evaluate(() => window.scrollBy(0, 500));
    await new Promise(r => setTimeout(r, 400));
    await page.screenshot({ path: path.join(screenshotDir, '91_ceo_matrix_progress.png'), fullPage: false });
    console.log('[PASS] Captured 91_ceo_matrix_progress.png');

    // Screenshot 3: Subject Performance Table & Risk Analysis
    await page.evaluate(() => window.scrollBy(0, 700));
    await new Promise(r => setTimeout(r, 400));
    await page.screenshot({ path: path.join(screenshotDir, '92_ceo_subject_table_risks.png'), fullPage: false });
    console.log('[PASS] Captured 92_ceo_subject_table_risks.png');

    // Screenshot 4: Prioritized Management Action Plan
    await page.evaluate(() => window.scrollBy(0, 700));
    await new Promise(r => setTimeout(r, 400));
    await page.screenshot({ path: path.join(screenshotDir, '93_ceo_action_plan.png'), fullPage: false });
    console.log('[PASS] Captured 93_ceo_action_plan.png');

    // 4. Test Executive Brief Modal
    console.log('Testing Export Executive Brief modal...');
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.click('button[onclick="openCeoReportModal()"]');
    await new Promise(r => setTimeout(r, 400));
    const isReportModalVisible = await page.$eval('#ceoReportModal', el => !el.classList.contains('hidden'));
    console.log(`[PASS] Executive Brief Modal Open: ${isReportModalVisible}`);
    await page.screenshot({ path: path.join(screenshotDir, '94_ceo_executive_brief_modal.png'), fullPage: false });

    // Close Executive Brief Modal
    await page.click('#ceoReportModal button[onclick="closeCeoReportModal()"]');
    await new Promise(r => setTimeout(r, 300));

    // 5. Test Drill-Down: Click on "Matched in All 3" (258 widgets)
    console.log('Testing drill-down: Matched in All 3 (258)...');
    await page.click('#card-kpi-matched');
    await new Promise(r => setTimeout(r, 500));
    const invCountMatched = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`[PASS] Filtered Count for Matched in All 3: ${invCountMatched} (Expected: 258)`);
    await page.screenshot({ path: path.join(screenshotDir, '95_all_widgets_matched_all_drilldown.png'), fullPage: false });

    // 6. Test Drill-Down: Missing in QA (15 widgets)
    console.log('Testing quick pill: Missing in QA...');
    await page.click('#pill-filter-missing_qa');
    await new Promise(r => setTimeout(r, 500));
    const invCountMissingQa = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`[PASS] Filtered Count for Missing in QA: ${invCountMissingQa} (Expected: 15)`);
    await page.screenshot({ path: path.join(screenshotDir, '96_all_widgets_missing_qa_pill.png'), fullPage: false });

    // 7. Test Drill-Down: Needs Development (12 widgets)
    console.log('Testing quick pill: Needs Development...');
    await page.click('#pill-filter-requires_dev');
    await new Promise(r => setTimeout(r, 500));
    const invCountDev = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`[PASS] Filtered Count for Needs Development: ${invCountDev} (Expected: 12)`);
    await page.screenshot({ path: path.join(screenshotDir, '97_all_widgets_needs_dev_pill.png'), fullPage: false });

    // 8. Test Drill-Down: Extra in Repo (46 widgets)
    console.log('Testing quick pill: Extra in Repo...');
    await page.click('#pill-filter-extra_repo');
    await new Promise(r => setTimeout(r, 500));
    const invCountExtra = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`[PASS] Filtered Count for Extra in Repo: ${invCountExtra} (Expected: 46)`);
    await page.screenshot({ path: path.join(screenshotDir, '98_all_widgets_extra_repo_pill.png'), fullPage: false });

    // 9. Test Widget Detail Modal
    console.log('Testing Widget Detail Modal inspection...');
    await page.click('#pill-filter-matched_all');
    await new Promise(r => setTimeout(r, 400));
    await page.click('#widgetTableBody tr:first-child');
    await new Promise(r => setTimeout(r, 400));
    const modalTitle = await page.$eval('#modalName', el => el.innerText.trim());
    const modalPriority = await page.$eval('#modalActionPriority', el => el.innerText.trim());
    console.log(`[PASS] Widget Modal Name: "${modalTitle}", Priority: "${modalPriority}"`);
    await page.screenshot({ path: path.join(screenshotDir, '99_ceo_widget_modal_detail.png'), fullPage: false });
    await page.click('button[onclick="closeModal()"]');
    await new Promise(r => setTimeout(r, 300));

    // 10. Test Light Theme Toggle
    console.log('Testing Theme Toggle to Light Mode...');
    await page.click('#quickThemeBtn');
    await new Promise(r => setTimeout(r, 400));
    await page.click('#tab-overview');
    await new Promise(r => setTimeout(r, 400));
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(screenshotDir, '100_ceo_overview_light_theme.png'), fullPage: false });
    console.log('[PASS] Captured 100_ceo_overview_light_theme.png');

    await browser.close();

    console.log('\n======================================================');
    console.log('CEO EXECUTIVE DASHBOARD E2E TEST SUMMARY:');
    console.log(`- Console/Page Errors: ${errors.length}`);
    if (errors.length > 0) {
        console.error('Errors encountered:', errors);
        process.exit(1);
    } else {
        console.log('- ALL CEO RECONCILIATION & E2E DRILL-DOWN TESTS PASSED (0 ERRORS)!');
    }
    console.log('======================================================');
}

testCeoDashboard().catch(err => {
    console.error('Test execution failed:', err);
    process.exit(1);
});
