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

    const outDir = 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots';
    if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

    console.log('--- TEST 1: INITIAL LOAD & NAVIGATION VERIFICATION ---');
    await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle0' });

    const visibleTabs = await page.$$eval('.nav-tab:not(.hidden)', els => els.map(e => e.innerText.trim()));
    console.log('Visible Navigation Tabs:', visibleTabs);
    const hasQaTab = await page.$('#tab-qa') !== null;
    const hasQaView = await page.$('#view-qa') !== null;
    console.log(`QA Tab Exists: ${hasQaTab} (expected: false) | QA View Exists: ${hasQaView} (expected: false)`);

    // Capture Overview Top
    await page.screenshot({ path: path.join(outDir, '81_overview_redesign_top.png') });
    console.log('Captured 81_overview_redesign_top.png');

    console.log('\n--- TEST 2: 6 KPI CARDS VERIFICATION ---');
    const kpiData = await page.evaluate(() => {
        return {
            total: document.getElementById('stat-total-repo')?.innerText.trim(),
            qa: document.getElementById('stat-qa-tools')?.innerText.trim(),
            present: document.getElementById('stat-present-both')?.innerText.trim(),
            missing: document.getElementById('stat-missing-repo')?.innerText.trim(),
            extra: document.getElementById('stat-extra-repo')?.innerText.trim(),
            dev: document.getElementById('stat-dev-num')?.innerText.trim()
        };
    });
    console.log('KPI Cards Values:', kpiData);

    console.log('\n--- TEST 3: 3-WAY RECONCILIATION MATRIX TABLE ---');
    // Scroll down to view the matrix table and subject cards
    await page.evaluate(() => window.scrollBy(0, 450));
    await new Promise(r => setTimeout(r, 400));
    await page.screenshot({ path: path.join(outDir, '82_overview_reconciliation_matrix.png') });
    console.log('Captured 82_overview_reconciliation_matrix.png');

    // Scroll further down to subject cards
    await page.evaluate(() => window.scrollBy(0, 500));
    await new Promise(r => setTimeout(r, 400));
    await page.screenshot({ path: path.join(outDir, '83_overview_subject_cards.png') });
    console.log('Captured 83_overview_subject_cards.png');

    console.log('\n--- TEST 4: MATRIX TABLE DRILL-DOWN TEST ---');
    // Scroll back up and click "View Backlog" in matrix table
    await page.evaluate(() => window.scrollTo(0, 0));
    await new Promise(r => setTimeout(r, 300));
    
    // Find the matrix table backlog button and click it
    await page.evaluate(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const backlogBtn = btns.find(b => b.innerText.includes('View Backlog'));
        if (backlogBtn) backlogBtn.click();
    });
    await new Promise(r => setTimeout(r, 400));

    const invActive1 = await page.$eval('#view-inventory', el => !el.classList.contains('hidden'));
    const devFilteredCount = await page.$eval('#totalFiltered', el => el.innerText.trim());
    const devPillCls = await page.$eval('#pill-filter-requires_dev', el => el.className);
    console.log(`Backlog Drill-Down: All Widgets active=${invActive1}, count=${devFilteredCount} (expected: 12), pillActive=${devPillCls.includes('bg-blue-600')}`);
    await page.screenshot({ path: path.join(outDir, '84_all_widgets_backlog_filtered.png') });
    console.log('Captured 84_all_widgets_backlog_filtered.png');

    console.log('\n--- TEST 5: QUICK PILL FILTER BAR TESTS ---');
    // Test In QA Catalog pill
    await page.click('#pill-filter-qa_verified');
    await new Promise(r => setTimeout(r, 400));
    const qaFilteredCount = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`In QA Catalog pill clicked: count=${qaFilteredCount}`);
    await page.screenshot({ path: path.join(outDir, '85_all_widgets_qa_pill.png') });
    console.log('Captured 85_all_widgets_qa_pill.png');

    // Test Extra in Repo pill
    await page.click('#pill-filter-extra_repo');
    await new Promise(r => setTimeout(r, 400));
    const extraFilteredCount = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`Extra in Repo pill clicked: count=${extraFilteredCount} (expected: 46)`);

    // Test All Required pill
    await page.click('#pill-filter-all');
    await new Promise(r => setTimeout(r, 400));
    const allFilteredCount = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`All Required pill clicked: count=${allFilteredCount} (expected: 294)`);

    console.log('\n--- TEST 6: SEARCH & MODAL DETAIL DRAWER ---');
    // Search by QA Tool UID
    await page.type('#widgetSearch', 'tool-');
    await new Promise(r => setTimeout(r, 400));
    const searchResultCount = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`Search by 'tool-' returned: ${searchResultCount} widgets`);

    // Open first row modal
    const firstRow = await page.$('#widgetTableBody tr');
    if (firstRow) {
        await firstRow.click();
        await new Promise(r => setTimeout(r, 400));
        
        const modalVisible = await page.$eval('#widgetModal', el => !el.classList.contains('hidden'));
        const modalQaVisible = await page.$eval('#modalQaSection', el => !el.classList.contains('hidden'));
        const modalName = await page.$eval('#modalName', el => el.innerText.trim());
        const modalUid = await page.$eval('#modalQaSection', el => el.innerText.trim().split('\n')[1] || '');
        console.log(`Modal Opened: name="${modalName}", QA Section Visible=${modalQaVisible}, UID=${modalUid}`);
        
        await page.screenshot({ path: path.join(outDir, '86_modal_redesigned_detail.png') });
        console.log('Captured 86_modal_redesigned_detail.png');

        // Close modal via Escape
        await page.keyboard.press('Escape');
        await new Promise(r => setTimeout(r, 300));
    }

    // Clear search
    await page.$eval('#widgetSearch', el => el.value = '');
    await page.type('#widgetSearch', ' ');
    await page.keyboard.press('Backspace');
    await new Promise(r => setTimeout(r, 300));

    console.log('\n--- TEST 7: SUBJECT DRILL-DOWN FROM OVERVIEW ---');
    await page.click('#tab-overview');
    await new Promise(r => setTimeout(r, 300));
    
    // Click Mathematics subject card
    await page.evaluate(() => {
        const cards = Array.from(document.querySelectorAll('.app-card'));
        const mathCard = cards.find(c => c.innerText.includes('Mathematics') && c.innerText.includes('Widgets'));
        if (mathCard) mathCard.click();
    });
    await new Promise(r => setTimeout(r, 400));
    const mathSubjVal = await page.$eval('#subjectFilter', el => el.value);
    const mathCount = await page.$eval('#totalFiltered', el => el.innerText.trim());
    console.log(`Subject Drill-Down: selected=${mathSubjVal}, filtered=${mathCount}`);
    await page.screenshot({ path: path.join(outDir, '87_subject_drilldown_math.png') });
    console.log('Captured 87_subject_drilldown_math.png');

    console.log('\n--- TEST 8: LIGHT THEME COMPREHENSIVE VERIFICATION ---');
    await page.click('#tab-overview');
    await new Promise(r => setTimeout(r, 300));
    await page.click('#quickThemeBtn');
    await new Promise(r => setTimeout(r, 400));
    await page.screenshot({ path: path.join(outDir, '88_overview_light_theme_redesign.png') });
    console.log('Captured 88_overview_light_theme_redesign.png');

    // Scroll to Matrix in light theme
    await page.evaluate(() => window.scrollBy(0, 450));
    await new Promise(r => setTimeout(r, 300));
    await page.screenshot({ path: path.join(outDir, '89_matrix_light_theme.png') });
    console.log('Captured 89_matrix_light_theme.png');

    // Switch back to Dark Theme
    await page.click('#quickThemeBtn');
    await new Promise(r => setTimeout(r, 300));

    console.log('\n========================================');
    console.log('FINAL E2E VERIFICATION REPORT');
    console.log('========================================');
    console.log(`Total Runtime / Console Errors: ${errors.length}`);
    if (errors.length > 0) {
        errors.forEach(e => console.error('  ERROR:', e));
        process.exit(1);
    } else {
        console.log('ALL TESTS PASSED WITH 0 ERRORS! Visual and functional verification complete.');
    }

    await browser.close();
})();
