const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');

async function testRoleVisibility() {
    console.log('Starting Role-Based Component Visibility E2E Test...');
    const errors = [];

    const browser = await puppeteer.launch({
        executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 960 });

    const adminElements = [
        'tab-users',
        'tab-activity',
        'tab-docs',
        'section-project-status-overview',
        'section-management-insights',
        'section-management-action-plan'
    ];

    async function loginAs(user, pass) {
        await page.goto('http://localhost:8000/login.html', { waitUntil: 'networkidle0' });
        // Clear session so login.html does not auto-redirect
        await page.evaluate(() => {
            localStorage.removeItem('widget_dashboard_auth_state_v1');
            sessionStorage.removeItem('widget_dashboard_auth_state_v1');
        });
        await page.reload({ waitUntil: 'networkidle0' });
        await page.waitForSelector('#email');
        await Promise.all([
            page.waitForNavigation({ waitUntil: 'networkidle0' }),
            page.evaluate((u, p) => {
                document.getElementById('email').value = u;
                document.getElementById('password').value = p;
                document.querySelector('form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
            }, user, pass)
        ]);
        console.log(`[PASS] Successfully logged in as: ${user} (Current URL: ${page.url()})`);
    }

    async function checkVisibility(expectedAdmin, roleName) {
        const results = {};
        for (const id of adminElements) {
            const isHidden = await page.$eval('#' + id, el => el.classList.contains('hidden'));
            const isVisible = !isHidden;
            results[id] = isVisible;
            if (expectedAdmin && !isVisible) {
                errors.push(`${roleName} should SEE #${id}, but it is HIDDEN!`);
            } else if (!expectedAdmin && isVisible) {
                errors.push(`${roleName} should NOT see #${id}, but it is VISIBLE!`);
            }
        }
        return results;
    }

    // 1. Test Admin Login (Should see ALL 6 components)
    console.log('\n--- 1. Testing Admin Role (admin) ---');
    await loginAs('admin', 'Admin@123');
    const adminVis = await checkVisibility(true, 'Admin');
    console.log('Admin Visibility (All should be true):', adminVis);

    // 2. Test Developer Role (Should have ALL 6 components HIDDEN)
    console.log('\n--- 2. Testing Developer Role (nitin) ---');
    await loginAs('nitin', 'Nitin@123');
    const devVis = await checkVisibility(false, 'Developer');
    console.log('Developer Visibility (All should be false):', devVis);

    // 3. Test QA Role (Should have ALL 6 components HIDDEN)
    console.log('\n--- 3. Testing QA Role (qa) ---');
    await loginAs('qa', 'Qa@123');
    const qaVis = await checkVisibility(false, 'QA');
    console.log('QA Visibility (All should be false):', qaVis);

    // 4. Test Content Role (Should have ALL 6 components HIDDEN)
    console.log('\n--- 4. Testing Content Role (content) ---');
    await loginAs('content', 'Content@123');
    const contentVis = await checkVisibility(false, 'Content');
    console.log('Content Visibility (All should be false):', contentVis);

    await browser.close();

    console.log('\n======================================================');
    console.log('ROLE-BASED VISIBILITY TEST RESULTS:');
    console.log(`- Total Checked Roles: 4 (Admin, Developer, QA, Content)`);
    console.log(`- Total Checked Components per Role: ${adminElements.length}`);
    console.log(`- Errors: ${errors.length}`);
    if (errors.length > 0) {
        console.error('Errors encountered:', errors);
        process.exit(1);
    } else {
        console.log('- ALL ROLE VISIBILITY TESTS PASSED (0 ERRORS)!');
        console.log('  Admin sees all 6 components; non-admin roles have all 6 strictly hidden.');
        console.log('======================================================');
    }
}

testRoleVisibility().catch(err => {
    console.error('Test execution error:', err);
    process.exit(1);
});
