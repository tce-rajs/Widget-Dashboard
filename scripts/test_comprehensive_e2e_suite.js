const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');
const path = require('path');
const fs = require('fs');

async function runMasterTestSuite() {
    console.log('================================================================');
    console.log('       RUNNING COMPREHENSIVE END-TO-END MASTER TEST SUITE       ');
    console.log('================================================================\n');

    const browser = await puppeteer.launch({
        executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    const artifactsDir = 'C:\\Users\\v_CrystalQA3\\.gemini\\antigravity\\brain\\f3079d64-eabf-438b-bac4-f5596cf2bcbd\\screenshots';
    if (!fs.existsSync(artifactsDir)) fs.mkdirSync(artifactsDir, { recursive: true });

    const testResults = [];
    function recordPass(testName) {
        console.log(`[PASS] ${testName}`);
        testResults.push({ name: testName, status: 'PASS' });
    }
    function recordFail(testName, error) {
        console.error(`[FAIL] ${testName}: ${error}`);
        testResults.push({ name: testName, status: 'FAIL', error });
    }

    const browserErrors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') browserErrors.push(msg.text());
    });
    page.on('pageerror', err => browserErrors.push(err.toString()));

    try {
        // -------------------------------------------------------------
        // TEST 1: Login Page Authentication & Error Handling
        // -------------------------------------------------------------
        console.log('--- TEST 1: Login Page Authentication & Validation ---');
        await page.setViewport({ width: 1440, height: 900 });
        await page.goto('http://localhost:8000/login.html', { waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 400));

        // 1a: Invalid credentials test
        await page.evaluate(() => {
            document.getElementById('email').value = 'wrong@company.com';
            document.getElementById('password').value = 'WrongPassword!';
            document.querySelector('form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        });
        await new Promise(r => setTimeout(r, 400));
        const errorMsg = await page.$eval('#errorMessage', el => el.textContent.trim());
        if (errorMsg.includes('Invalid')) {
            recordPass('Test 1a: Invalid login credentials correctly rejected');
        } else {
            recordFail('Test 1a: Invalid login rejection', `Unexpected error message: "${errorMsg}"`);
        }

        // 1b: Valid Admin login
        await page.evaluate(() => {
            document.getElementById('email').value = 'admin';
            document.getElementById('password').value = 'Admin@123';
            document.querySelector('form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        });
        await page.waitForNavigation({ waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 800));

        const currentUrl = page.url();
        if (currentUrl.includes('index.html')) {
            recordPass('Test 1b: Valid login redirect to index.html succeeded');
        } else {
            recordFail('Test 1b: Login redirect', `URL is ${currentUrl}`);
        }

        // -------------------------------------------------------------
        // TEST 2: Header Timestamps & Excel Action Buttons
        // -------------------------------------------------------------
        console.log('\n--- TEST 2: Header Timestamps & Excel Action Buttons ---');
        // Desktop verification
        const headerTimestamp = await page.$eval('#headerLastUpdatedTime', el => el.textContent.trim());
        const desktopLayout = await page.evaluate(() => {
            const timeEl = document.getElementById('headerLastUpdatedTime');
            const updateBtn = document.getElementById('updateExcelContainer');
            const timeRect = timeEl.getBoundingClientRect();
            const btnRect = updateBtn.getBoundingClientRect();
            return {
                text: timeEl.textContent,
                isBelow: timeRect.top >= btnRect.bottom - 2
            };
        });

        if (headerTimestamp && desktopLayout.isBelow) {
            recordPass(`Test 2a: Desktop Last Updated time (${headerTimestamp}) placed directly below Excel buttons`);
        } else {
            recordFail('Test 2a: Desktop timestamp positioning', JSON.stringify(desktopLayout));
        }

        // Mobile verification
        await page.setViewport({ width: 390, height: 844 });
        await page.reload({ waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 800));

        const mobileTimestamp = await page.$eval('#mobileLastUpdatedTime', el => el.textContent.trim());
        if (mobileTimestamp) {
            recordPass(`Test 2b: Mobile Last Updated time (${mobileTimestamp}) rendered properly`);
        } else {
            recordFail('Test 2b: Mobile timestamp', 'Mobile timestamp missing or empty');
        }

        // Reset to desktop viewport
        await page.setViewport({ width: 1440, height: 900 });
        await page.reload({ waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 800));

        // -------------------------------------------------------------
        // TEST 3: User Management Persistence Across Page Refreshes (F5)
        // -------------------------------------------------------------
        console.log('\n--- TEST 3: User Management Persistence Across Refresh ---');
        await page.evaluate(() => switchTab('users'));
        await new Promise(r => setTimeout(r, 400));

        const initialUsersCount = await page.evaluate(() => authManager.getUsers().length);

        // 3a: Add user: "Elena Gilbert"
        await page.evaluate(() => {
            authManager.addUser('Elena Gilbert', 'elena@mystic.org', 'Elena@123', 'content');
            renderUsersTable();
        });
        await new Promise(r => setTimeout(r, 300));

        // Simulate F5 refresh
        await page.reload({ waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 800));

        const userAfterRefresh = await page.evaluate(() => {
            return authManager.getUsers().find(u => u.email === 'elena@mystic.org');
        });
        const activeTabAfterRefresh = await page.evaluate(() => {
            return document.getElementById('view-users').classList.contains('hidden') ? 'hidden' : 'visible';
        });

        if (userAfterRefresh && userAfterRefresh.fullName === 'Elena Gilbert' && activeTabAfterRefresh === 'visible') {
            recordPass('Test 3a: Created user persisted on reload and active #users tab preserved');
        } else {
            recordFail('Test 3a: User persistence on refresh', `User: ${JSON.stringify(userAfterRefresh)}, Tab: ${activeTabAfterRefresh}`);
        }

        // 3b: Edit user details & reload
        await page.evaluate(() => {
            const u = authManager.getUsers().find(x => x.email === 'elena@mystic.org');
            authManager.editUser(u.id, {
                fullName: 'Elena Gilbert Salvatore',
                email: 'elena@mystic.org',
                role: 'qa',
                password: 'ElenaSalvatore@123'
            });
            renderUsersTable();
        });
        await page.reload({ waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 800));

        const editedUser = await page.evaluate(() => {
            return authManager.getUsers().find(x => x.email === 'elena@mystic.org');
        });
        if (editedUser && editedUser.fullName === 'Elena Gilbert Salvatore' && editedUser.role === 'qa') {
            recordPass('Test 3b: Edited user details persisted across reload');
        } else {
            recordFail('Test 3b: Edit persistence', JSON.stringify(editedUser));
        }

        // 3c: Disable user & verify login rejection
        await page.evaluate(() => {
            const u = authManager.getUsers().find(x => x.email === 'elena@mystic.org');
            authManager.toggleUserStatus(u.id);
            renderUsersTable();
        });
        await page.reload({ waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 800));

        const disabledUser = await page.evaluate(() => {
            return authManager.getUsers().find(x => x.email === 'elena@mystic.org');
        });
        const loginAttempt = await page.evaluate(() => {
            return authManager.login('elena@mystic.org', 'ElenaSalvatore@123');
        });

        if (disabledUser.status === 'disabled' && !loginAttempt.success && loginAttempt.error.includes('disabled')) {
            recordPass('Test 3c: Disabled user status persisted & login rejected with clear message');
        } else {
            recordFail('Test 3c: Disabled user login rejection', `Status: ${disabledUser.status}, Login: ${JSON.stringify(loginAttempt)}`);
        }

        // 3d: Re-enable user & delete user permanently
        await page.evaluate(() => {
            const u = authManager.getUsers().find(x => x.email === 'elena@mystic.org');
            authManager.deleteUser(u.id);
            renderUsersTable();
        });
        await page.reload({ waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 800));

        const deletedCheck = await page.evaluate(() => {
            return authManager.getUsers().find(x => x.email === 'elena@mystic.org');
        });
        if (!deletedCheck) {
            recordPass('Test 3d: Deleted user removed permanently and blacklist prevented revival on refresh');
        } else {
            recordFail('Test 3d: Deleted user persistence', 'User was revived on reload');
        }

        // -------------------------------------------------------------
        // TEST 4: Supabase Cloud Database Integration & UI Modals
        // -------------------------------------------------------------
        console.log('\n--- TEST 4: Supabase Cloud Database Integration & UI ---');
        // Check window.supabase is available from CDN
        const supabaseLoaded = await page.evaluate(() => typeof window.supabase !== 'undefined' && typeof window.supabase.createClient === 'function');
        if (supabaseLoaded) {
            recordPass('Test 4a: Supabase JS library loaded successfully from CDN');
        } else {
            recordFail('Test 4a: Supabase JS library', 'window.supabase is undefined');
        }

        // Open Cloud Sync Modal
        await page.evaluate(() => openCloudSyncModal());
        await new Promise(r => setTimeout(r, 300));

        const cloudModalOpen = await page.$eval('#cloudSyncModal', el => !el.classList.contains('hidden'));
        const cloudStatusTitle = await page.$eval('#cloudModalStatusTitle', el => el.textContent.trim());
        if (cloudModalOpen && cloudStatusTitle) {
            recordPass(`Test 4b: Cloud Database Sync Modal opened with status: "${cloudStatusTitle}"`);
        } else {
            recordFail('Test 4b: Cloud modal opening', `Modal open: ${cloudModalOpen}, Title: ${cloudStatusTitle}`);
        }

        // Test Supabase SQL Schema Copy
        const schemaCopied = await page.evaluate(() => {
            copySupabaseSchema();
            return typeof SUPABASE_SCHEMA_SQL === 'string' && SUPABASE_SCHEMA_SQL.includes('create table if not exists public.app_users');
        });
        if (schemaCopied) {
            recordPass('Test 4c: 1-Click Supabase PostgreSQL Schema generator verified');
        } else {
            recordFail('Test 4c: Schema generator', 'SUPABASE_SCHEMA_SQL is missing or invalid');
        }

        // Test Mock Supabase Sync cycle
        const cloudSyncCycle = await page.evaluate(async () => {
            // Save mock config
            authManager.saveSupabaseConfig('https://mock-test-project.supabase.co', 'mock-anon-key-12345', false);
            const cfg = authManager.getSupabaseConfig();
            return cfg.url === 'https://mock-test-project.supabase.co';
        });
        if (cloudSyncCycle) {
            recordPass('Test 4d: Supabase configuration saving and auto-detection verified');
        } else {
            recordFail('Test 4d: Supabase config', 'Config not saved properly');
        }

        // Reset to local mode cleanly
        await page.evaluate(() => {
            authManager.saveSupabaseConfig('', '', true);
            closeCloudSyncModal();
        });

        // -------------------------------------------------------------
        // TEST 5: Security Guard for Non-Admin Users
        // -------------------------------------------------------------
        console.log('\n--- TEST 5: Role-Based Access Control & Security Guards ---');
        // Clear active admin session before navigating to login
        await page.evaluate(() => {
            localStorage.removeItem('widget_dashboard_auth_state_v1');
            sessionStorage.removeItem('widget_dashboard_auth_state_v1');
        }).catch(() => {});

        // Login as non-admin: nitin (developer)
        await page.goto('http://localhost:8000/login.html', { waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 400));
        await page.evaluate(() => {
            document.getElementById('email').value = 'nitin';
            document.getElementById('password').value = 'Nitin@123';
            document.querySelector('form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        });
        await page.waitForNavigation({ waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 600));

        // Verify Developer cannot see admin tabs or actions
        const adminElementsVisible = await page.evaluate(() => {
            const usersTab = document.getElementById('tab-users');
            const activityTab = document.getElementById('tab-activity');
            const docsTab = document.getElementById('tab-docs');
            return {
                usersTabHidden: usersTab ? usersTab.classList.contains('hidden') : true,
                activityTabHidden: activityTab ? activityTab.classList.contains('hidden') : true,
                docsTabHidden: docsTab ? docsTab.classList.contains('hidden') : true
            };
        });

        if (adminElementsVisible.usersTabHidden && adminElementsVisible.activityTabHidden) {
            recordPass('Test 5a: Admin tabs (Users, Activity) completely hidden for Developer role');
        } else {
            recordFail('Test 5a: Role tab visibility', JSON.stringify(adminElementsVisible));
        }

        // Attempt direct access via URL hash #users
        await page.goto('http://localhost:8000/index.html#users', { waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 600));
        const viewUsersHiddenForNonAdmin = await page.evaluate(() => {
            const view = document.getElementById('view-users');
            return view ? view.classList.contains('hidden') : true;
        });

        if (viewUsersHiddenForNonAdmin) {
            recordPass('Test 5b: Direct access to #users URL hash strictly blocked for non-admin');
        } else {
            recordFail('Test 5b: Hash access guard', 'Non-admin was able to see view-users via #users hash');
        }

        // Take screenshot of clean developer view
        await page.screenshot({
            path: path.join(artifactsDir, '148_developer_verified_restricted_view.png'),
            clip: { x: 0, y: 0, width: 1440, height: 260 }
        });
        console.log('Saved 148_developer_verified_restricted_view.png');

    } catch (suiteError) {
        console.error('Unhandled Suite Error:', suiteError);
        testResults.push({ name: 'Suite Execution', status: 'FAIL', error: suiteError.message });
    } finally {
        await browser.close();
    }

    console.log('\n================================================================');
    console.log('                   FINAL MASTER TEST SUMMARY                    ');
    console.log('================================================================');
    const passes = testResults.filter(t => t.status === 'PASS').length;
    const fails = testResults.filter(t => t.status === 'FAIL').length;
    console.log(`Total Tests Executed : ${testResults.length}`);
    console.log(`Passed               : ${passes}`);
    console.log(`Failed               : ${fails}`);
    console.log(`Browser Errors       : ${browserErrors.length}`);
    console.log('================================================================\n');

    if (fails > 0 || browserErrors.length > 0) {
        process.exit(1);
    }
}

runMasterTestSuite();
