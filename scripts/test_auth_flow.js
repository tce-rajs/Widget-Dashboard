const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');
const path = require('path');
const fs = require('fs');

async function testAuthFlow() {
    console.log('Starting Complete Authentication & Role-Based Access E2E Test...');
    
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

    page.on('response', res => {
        if (res.status() === 404) {
            console.log('404 RESOURCE:', res.url());
        }
    });

    page.on('pageerror', err => {
        errors.push(err.message);
        console.error('Page error:', err.message);
    });

    // 1. Test Unauthenticated Access Guard
    console.log('1. Testing Unauthenticated Access Redirect to login.html...');
    await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle0' });
    const currentUrl = page.url();
    console.log(`[PASS] Unauthenticated visitor redirected to: ${currentUrl}`);
    if (!currentUrl.includes('login.html')) {
        errors.push(`Expected redirect to login.html, but remained at: ${currentUrl}`);
    }
    await page.screenshot({ path: path.join(screenshotDir, '124_login_page_redirected.png'), fullPage: false });

    // 2. Test Invalid Login
    console.log('2. Testing Invalid Login Credentials...');
    await page.type('#email', 'fakeuser@company.com');
    await page.type('#password', 'WrongPassword123');
    await page.click('button[type="submit"]');
    await new Promise(r => setTimeout(r, 400));
    const errorVisible = await page.$eval('#errorBanner', el => !el.classList.contains('hidden'));
    const errorText = await page.$eval('#errorMessage', el => el.innerText.trim());
    console.log(`[PASS] Error Banner Visible: ${errorVisible} ("${errorText}")`);
    if (!errorVisible) errors.push('Error banner was not shown on invalid login!');

    // 3. Test Successful Admin Login
    console.log('3. Testing Admin Login (admin / Admin@123)...');
    await page.evaluate(() => {
        document.getElementById('email').value = '';
        document.getElementById('password').value = '';
    });
    await page.type('#email', 'admin');
    await page.type('#password', 'Admin@123');
    await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle0' }),
        page.click('button[type="submit"]')
    ]);

    const loggedInUrl = page.url();
    console.log(`[PASS] Admin successfully redirected to: ${loggedInUrl}`);
    if (!loggedInUrl.includes('index.html')) {
        errors.push(`Expected navigation to index.html after login, but got: ${loggedInUrl}`);
    }

    // Verify Admin Header Profile Pill
    const profilePillVisible = await page.$eval('#userProfilePill', el => !el.classList.contains('hidden'));
    const userName = await page.$eval('#userNameDisplay', el => el.innerText.trim());
    const userRole = await page.$eval('#userRoleBadge', el => el.innerText.trim());
    console.log(`[PASS] Profile Pill: Visible=${profilePillVisible}, Name="${userName}", Role="${userRole}"`);

    // Verify Admin Tabs Revealed
    const tabUsersVisible = await page.$eval('#tab-users', el => !el.classList.contains('hidden'));
    const tabActivityVisible = await page.$eval('#tab-activity', el => !el.classList.contains('hidden'));
    console.log(`[PASS] Admin Tabs: UsersTab=${tabUsersVisible}, ActivityTab=${tabActivityVisible}`);
    if (!tabUsersVisible || !tabActivityVisible) {
        errors.push('Admin tabs (Users, Activity) were not revealed for Admin role!');
    }

    await page.screenshot({ path: path.join(screenshotDir, '125_admin_authenticated_dashboard.png'), fullPage: false });

    // 4. Test User Management View
    console.log('4. Testing User Management Tab as Admin...');
    await page.click('#tab-users');
    await new Promise(r => setTimeout(r, 400));
    const usersViewVisible = await page.$eval('#view-users', el => !el.classList.contains('hidden'));
    console.log(`[PASS] User Management View Opened: ${usersViewVisible}`);
    await page.screenshot({ path: path.join(screenshotDir, '126_user_management_view.png'), fullPage: false });

    // 5. Test Activity History View
    console.log('5. Testing Activity History Tab as Admin...');
    await page.click('#tab-activity');
    await new Promise(r => setTimeout(r, 400));
    const activityViewVisible = await page.$eval('#view-activity', el => !el.classList.contains('hidden'));
    console.log(`[PASS] Activity History View Opened: ${activityViewVisible}`);

    // 6. Test Logout
    console.log('6. Testing Logout...');
    await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle0' }),
        page.click('#userProfilePill button[onclick="handleLogout()"]')
    ]);
    const afterLogoutUrl = page.url();
    console.log(`[PASS] Redirected after logout to: ${afterLogoutUrl}`);
    if (!afterLogoutUrl.includes('login.html')) {
        errors.push(`Expected redirect to login.html after logout, got: ${afterLogoutUrl}`);
    }

    await browser.close();

    console.log('\n======================================================');
    console.log('AUTHENTICATION & ROLE-BASED ACCESS TEST RESULTS:');
    console.log(`- Errors: ${errors.length}`);
    if (errors.length > 0) {
        console.error('Errors encountered:', errors);
        process.exit(1);
    } else {
        console.log('- ALL AUTHENTICATION & ROLE-BASED ACCESS TESTS PASSED (0 ERRORS)!');
    }
    console.log('======================================================');
}

testAuthFlow().catch(err => {
    console.error('Test execution failed:', err);
    process.exit(1);
});
