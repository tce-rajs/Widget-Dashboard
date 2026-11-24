const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');
const path = require('path');
const fs = require('fs');

const SCREENSHOT_DIR = 'C:\\Users\\v_CrystalQA3\\.gemini\\antigravity\\brain\\f3079d64-eabf-438b-bac4-f5596cf2bcbd\\screenshots';
if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function run() {
    console.log("==================================================================");
    console.log("    VERIFYING GITHUB-STYLED WIDGET COMPARISON ON LOCALHOST        ");
    console.log("==================================================================\n");

    const browser = await puppeteer.launch({
        executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    let failures = 0;

    function assert(condition, message) {
        if (condition) {
            console.log(`[PASS] ${message}`);
        } else {
            console.error(`[FAIL] ${message}`);
            failures++;
        }
    }

    // 1. Desktop Viewport
    await page.setViewport({ width: 1280, height: 900 });
    await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle0' });

    // Check title
    const titleText = await page.$eval('h1', el => el.textContent.trim());
    assert(titleText === "Widget Comparison", `Title is "${titleText}"`);

    // Check header controls exist matching GitHub style
    const hasThemeBtn = await page.$('#quickThemeBtn') !== null;
    const hasUpdateExcel = await page.$('#updateExcelContainer') !== null;
    const hasExportBtn = await page.$('#desktopExportBtn') !== null;
    const hasTimestamp = await page.$('#headerLastUpdatedTime') !== null;

    assert(hasThemeBtn, "Theme Toggle button present in header");
    assert(hasUpdateExcel, "Update Excel button present in header");
    assert(hasExportBtn, "Export Excel button present in header");
    assert(hasTimestamp, "Last Updated timestamp present in header");

    // Check 5 numbers for Real Curriculum Dataset
    const metrics = await page.evaluate(() => {
        return {
            total: document.getElementById('metricTotal')?.textContent.trim(),
            subTotal: document.getElementById('subTotal')?.textContent.trim(),
            attention: document.getElementById('metricAttention')?.textContent.trim(),
            subAttention: document.getElementById('subAttention')?.textContent.trim(),
            qa: document.getElementById('metricQA')?.textContent.trim(),
            subQA: document.getElementById('subQA')?.textContent.trim(),
            git: document.getElementById('metricGit')?.textContent.trim(),
            subGit: document.getElementById('subGit')?.textContent.trim(),
            xl: document.getElementById('metricXL')?.textContent.trim(),
            subXL: document.getElementById('subXL')?.textContent.trim(),
        };
    });

    assert(metrics.total === "294" && metrics.subTotal === "across QA, Git & XL", `Total: ${metrics.total} (${metrics.subTotal})`);
    assert(metrics.attention === "21" && metrics.subAttention === "of 294 widgets", `Attention: ${metrics.attention} (${metrics.subAttention})`);
    assert(metrics.qa === "273" && metrics.subQA === "present · 93%", `QA: ${metrics.qa} (${metrics.subQA})`);
    assert(metrics.git === "273" && metrics.subGit === "present · 93%", `Git: ${metrics.git} (${metrics.subGit})`);
    assert(metrics.xl === "294" && metrics.subXL === "present · 100%", `XL: ${metrics.xl} (${metrics.subXL})`);

    // Check Tooltip equations
    const tooltipTexts = await page.$$eval('.metric-card .tooltip', tips => tips.map(t => t.textContent.trim()));
    assert(tooltipTexts[1].includes("Need attention = widgets missing from at least one source = 294 total − 273 in all three = 21"), "Tooltip 2 equation matches real counts");

    // Check Initial Attention rows count = 21
    let rowsCount = await page.$$eval('#widgetTableBody tr', rows => rows.length);
    assert(rowsCount === 21, `Initial Needs Attention rows: ${rowsCount} (expected 21)`);

    // Check first row has most gaps
    const firstRowGaps = await page.$$eval('#widgetTableBody tr:first-child .bg-rose-600', pills => pills.length);
    assert(firstRowGaps >= 2, `First row sorted with most gaps (${firstRowGaps} missing sources)`);

    // Check Tap targets >= 44px
    const buttonDimensions = await page.evaluate(() => {
        const toggleBtn = document.getElementById('toggleAttention')?.getBoundingClientRect();
        const folderBtn = document.querySelector('button[aria-label^="Open report folder"]')?.getBoundingClientRect();
        const linkBtn = document.querySelector('a[aria-label^="Open web link"]')?.getBoundingClientRect();
        return {
            toggleH: toggleBtn?.height,
            folderW: folderBtn?.width,
            folderH: folderBtn?.height,
            linkW: linkBtn?.width,
            linkH: linkBtn?.height
        };
    });
    assert(buttonDimensions.toggleH >= 44, `Toggle height: ${buttonDimensions.toggleH}px (>=44px)`);
    assert(buttonDimensions.folderW >= 44 && buttonDimensions.folderH >= 44, `Folder button: ${buttonDimensions.folderW}x${buttonDimensions.folderH}px (>=44px)`);
    assert(buttonDimensions.linkW >= 44 && buttonDimensions.linkH >= 44, `Link button: ${buttonDimensions.linkW}x${buttonDimensions.linkH}px (>=44px)`);

    // Screenshot: GitHub-styled Desktop Light Mode (Needs Attention 21)
    await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '169_github_styled_comparison_light_desktop.png'),
        clip: { x: 0, y: 0, width: 1280, height: 900 }
    });
    console.log("Captured: 169_github_styled_comparison_light_desktop.png");

    // Click "All (294)" toggle
    await page.click('#toggleAll');
    await new Promise(r => setTimeout(r, 300));
    rowsCount = await page.$$eval('#widgetTableBody tr', rows => rows.length);
    assert(rowsCount === 294, `Toggling 'All (294)' renders ${rowsCount} rows (expected 294)`);

    // Screenshot: GitHub-styled Desktop Light Mode (All 294)
    await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '170_github_styled_comparison_all_desktop.png'),
        clip: { x: 0, y: 0, width: 1280, height: 900 }
    });
    console.log("Captured: 170_github_styled_comparison_all_desktop.png");

    // Test Dark Mode toggle
    await page.click('#quickThemeBtn');
    await new Promise(r => setTimeout(r, 200));
    const isDark = await page.evaluate(() => document.documentElement.classList.contains('dark'));
    assert(isDark, "Dark Mode successfully toggled matching GitHub dark theme");

    // Screenshot: GitHub-styled Desktop Dark Mode
    await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '171_github_styled_comparison_dark_desktop.png'),
        clip: { x: 0, y: 0, width: 1280, height: 900 }
    });
    console.log("Captured: 171_github_styled_comparison_dark_desktop.png");

    // Test Mobile Viewport (390x844)
    await page.setViewport({ width: 390, height: 844, isMobile: true });
    await page.click('#toggleAttention');
    await new Promise(r => setTimeout(r, 200));
    await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '172_github_styled_comparison_mobile.png'),
        fullPage: true
    });
    console.log("Captured: 172_github_styled_comparison_mobile.png");

    await browser.close();

    console.log("\n==================================================================");
    if (failures === 0) {
        console.log("   ALL GITHUB-STYLED DASHBOARD CHECKS PASSED WITH ZERO FAILURES!  ");
    } else {
        console.error(`   VERIFICATION FINISHED WITH ${failures} FAILURE(S)!             `);
    }
    console.log("==================================================================");

    process.exit(failures === 0 ? 0 : 1);
}

run().catch(err => {
    console.error("Test execution failed:", err);
    process.exit(1);
});
