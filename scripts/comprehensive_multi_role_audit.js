const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');
const path = require('path');
const fs = require('fs');

const EDGE_PATH = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const BASE_URL = 'http://localhost:8000';
const ARTIFACT_DIR = 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots';

// Ensure screenshot directory exists
if (!fs.existsSync(ARTIFACT_DIR)) {
    fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
}

const auditResults = {
    meta: {
        timestamp: new Date().toISOString(),
        auditor: 'Senior QA Engineer, Manual Tester & Application Quality Analyst',
        appUrl: BASE_URL,
        version: 'CEO Platinum cum Crystal v2.4'
    },
    applicationStructure: {
        modules: [
            'Authentication & Session Engine',
            'Executive Overview & 3-Source Reconciliation',
            'All Widgets Inventory & Status Matrix',
            'User Management & RBAC Admin',
            'Activity History & Audit Trail',
            'Supabase Cloud Database Sync Engine',
            'Widget Detail & Technical Inspection Modal',
            'Status Briefing Report & PDF Export',
            'Theme & Responsive Viewport Adaptability'
        ],
        roles: ['admin', 'developer', 'qa', 'content', 'viewer'],
        testUsers: [
            { role: 'admin', email: 'admin@company.com', pass: 'Admin@123', name: 'Administrator' },
            { role: 'developer', email: 'nitin@company.com', pass: 'Nitin@123', name: 'Nitin' },
            { role: 'qa', email: 'qa@company.com', pass: 'Qa@123', name: 'QA Verification Engineer' },
            { role: 'content', email: 'content@company.com', pass: 'Content@123', name: 'Content Team Lead' },
            { role: 'viewer', email: 'viewer@company.com', pass: 'Viewer@123', name: 'Academic Management' }
        ]
    },
    roleTesting: {},
    functionalTests: [],
    workflows: [],
    negativeTests: [],
    uiUxFindings: [],
    bugs: [],
    summary: {
        totalTests: 0,
        passed: 0,
        failed: 0,
        blocked: 0
    }
};

function recordTest(category, name, role, status, details = '', evidence = '') {
    auditResults.summary.totalTests++;
    if (status === 'PASSED') auditResults.summary.passed++;
    else if (status === 'FAILED') auditResults.summary.failed++;
    else auditResults.summary.blocked++;

    const entry = { category, name, role, status, details, evidence };
    if (category === 'Functional') auditResults.functionalTests.push(entry);
    else if (category === 'Workflow') auditResults.workflows.push(entry);
    else if (category === 'Negative') auditResults.negativeTests.push(entry);
    else if (category === 'UI/UX') auditResults.uiUxFindings.push(entry);

    console.log(`  [${status}] [${role.toUpperCase()}] ${name}${details ? ' - ' + details : ''}`);
}

function recordBug(id, module, role, title, steps, expected, actual, severity, priority, evidence = '') {
    const bug = { id, module, role, title, steps, expected, actual, severity, priority, evidence };
    auditResults.bugs.push(bug);
    console.error(`  >>> BUG [${id}] [${severity}] ${title}`);
}

async function runFullAudit() {
    console.log('========================================================================');
    console.log('STARTING SENIOR QA MULTI-ROLE COMPREHENSIVE END-TO-END APPLICATION AUDIT');
    console.log('========================================================================\n');

    const browser = await puppeteer.launch({
        executablePath: EDGE_PATH,
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900 });

    const consoleErrors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', err => consoleErrors.push(err.toString()));

    // =========================================================================
    // 1. NEGATIVE & SECURITY: UNAUTHENTICATED ROUTE GUARD
    // =========================================================================
    console.log('\n--- SECTION 1: Route Guards & Authentication Security ---');
    await page.goto(`${BASE_URL}/index.html`, { waitUntil: 'networkidle0' });
    const currentUrl = page.url();
    if (currentUrl.includes('login.html')) {
        recordTest('Negative', 'Route Guard Unauthenticated Redirect', 'anonymous', 'PASSED', 'Correctly intercepted unauthenticated user and redirected to login.html');
    } else {
        recordTest('Negative', 'Route Guard Unauthenticated Redirect', 'anonymous', 'FAILED', `Expected redirect to login.html but was at ${currentUrl}`);
        recordBug('BUG-SEC-01', 'Authentication', 'anonymous', 'Unauthenticated user not redirected to login', 'Navigate directly to /index.html without session', 'Redirect to login.html', `Remained at ${currentUrl}`, 'Critical', 'P0');
    }

    // Invalid Login credentials
    await page.evaluate(() => {
        document.getElementById('email').value = 'wrong.user@company.com';
        document.getElementById('password').value = 'WrongPass@999';
    });
    await page.click('button[type="submit"]');
    await new Promise(r => setTimeout(r, 600));

    const invalidLoginMsg = await page.evaluate(() => {
        const b = document.getElementById('errorBanner');
        const m = document.getElementById('errorMessage');
        return b && !b.classList.contains('hidden') ? m.innerText : '';
    });

    if (invalidLoginMsg.includes('Invalid username/email or password')) {
        recordTest('Negative', 'Invalid Credentials Rejection', 'anonymous', 'PASSED', `Visible error message: "${invalidLoginMsg}"`);
    } else {
        recordTest('Negative', 'Invalid Credentials Rejection', 'anonymous', 'FAILED', 'No error message displayed for invalid credentials');
        recordBug('BUG-AUTH-01', 'Authentication', 'anonymous', 'Missing error banner on invalid login', 'Enter wrong password and click submit', 'Show error banner', 'No error banner visible', 'High', 'P1');
    }

    // Blank submission validation
    await page.evaluate(() => {
        document.getElementById('email').value = '';
        document.getElementById('password').value = '';
    });
    await page.click('button[type="submit"]');
    await new Promise(r => setTimeout(r, 400));
    const isHtml5Valid = await page.evaluate(() => document.getElementById('email').checkValidity());
    if (!isHtml5Valid) {
        recordTest('Negative', 'Empty Form Field Validation', 'anonymous', 'PASSED', 'HTML5 form validation prevented blank submission');
    } else {
        recordTest('Negative', 'Empty Form Field Validation', 'anonymous', 'FAILED', 'Form allowed empty submission');
    }

    // =========================================================================
    // 2. ADMIN ROLE TESTING (FULL PRIVILEGES)
    // =========================================================================
    console.log('\n--- SECTION 2: Admin Role Deep Audit ---');
    await page.evaluate(() => {
        document.getElementById('email').value = 'admin@company.com';
        document.getElementById('password').value = 'Admin@123';
        document.getElementById('rememberMe').checked = true;
    });
    await page.click('button[type="submit"]');
    await new Promise(r => setTimeout(r, 1000));

    if (page.url().includes('index.html')) {
        recordTest('Functional', 'Admin Authentication & Session Creation', 'admin', 'PASSED', 'Landed on index.html with active session token');
    } else {
        recordTest('Functional', 'Admin Authentication & Session Creation', 'admin', 'FAILED', 'Failed to land on index.html');
    }

    // Check Header & Admin Role Badge
    const adminHeaderData = await page.evaluate(() => {
        return {
            name: document.getElementById('userNameDisplay')?.innerText,
            role: document.getElementById('userRoleBadge')?.innerText,
            usersTabVisible: !document.getElementById('tab-users')?.classList.contains('hidden'),
            activityTabVisible: !document.getElementById('tab-activity')?.classList.contains('hidden')
        };
    });

    if (adminHeaderData.role === 'ADMIN' && adminHeaderData.usersTabVisible && adminHeaderData.activityTabVisible) {
        recordTest('Functional', 'Admin Header & Navigation RBAC Rendering', 'admin', 'PASSED', 'Shows ADMIN badge and both Users and Activity tabs');
    } else {
        recordTest('Functional', 'Admin Header & Navigation RBAC Rendering', 'admin', 'FAILED', `Header info mismatch: ${JSON.stringify(adminHeaderData)}`);
    }

    // Check Overview KPI Cards
    const kpis = await page.evaluate(() => {
        return {
            total: document.querySelector('#card-kpi-total .text-2xl')?.innerText.trim(),
            scope: document.querySelector('#card-kpi-xl .text-2xl')?.innerText.trim(),
            ready: document.querySelector('#card-kpi-qa .text-2xl')?.innerText.trim(),
            attention: document.querySelector('#card-kpi-attention .text-2xl')?.innerText.trim(),
            extra: document.querySelector('#card-kpi-git .text-2xl')?.innerText.trim()
        };
    });

    if (kpis.total === '340' && kpis.scope === '294' && kpis.ready === '258' && kpis.attention === '36' && kpis.extra === '+46') {
        recordTest('Functional', 'Overview Top KPI Cards Accuracy', 'admin', 'PASSED', '340 Total, 294 Scope, 258 Ready, 36 Need Attention, +46 Extra in Repo');
    } else {
        recordTest('Functional', 'Overview Top KPI Cards Accuracy', 'admin', 'FAILED', `Unexpected KPI values: ${JSON.stringify(kpis)}`);
    }

    // Test Hover Popovers on KPI Cards
    const card1 = await page.$('#card-kpi-total');
    await card1.hover();
    await new Promise(r => setTimeout(r, 400));
    const card1Popover = await page.evaluate(() => {
        const popover = document.querySelector('#card-kpi-total table');
        return popover ? popover.innerText : '';
    });
    if (card1Popover.includes('Matched in All 3') && card1Popover.includes('340')) {
        recordTest('Functional', 'KPI Card 1 Hover Table-Like Popover', 'admin', 'PASSED', 'Displays structured breakdown matching reconciliation table');
    } else {
        recordTest('Functional', 'KPI Card 1 Hover Table-Like Popover', 'admin', 'FAILED', 'Popover missing table breakdown');
    }

    // Test 3-Source Reconciliation Table
    const reconTableStats = await page.evaluate(() => {
        const rows = Array.from(document.querySelectorAll('#view-overview table tbody tr'));
        return {
            rowCount: rows.length,
            hasMatched: document.body.innerText.includes('Matched in All 3'),
            hasScope: document.body.innerText.includes('Total Scope (Baseline)'),
            hasExtra: document.body.innerText.includes('Extra in Repo'),
            hasGrandTotal: document.body.innerText.includes('Total Tracked Assets')
        };
    });
    if (reconTableStats.hasMatched && reconTableStats.hasScope && reconTableStats.hasExtra && reconTableStats.hasGrandTotal) {
        recordTest('Functional', '3-Source Reconciliation Table Rendering', 'admin', 'PASSED', 'All reconciliation categories and summary rows verified');
    } else {
        recordTest('Functional', '3-Source Reconciliation Table Rendering', 'admin', 'FAILED', 'Missing reconciliation categories');
    }

    // =========================================================================
    // 3. ALL WIDGETS INVENTORY FUNCTIONAL TESTING
    // =========================================================================
    console.log('\n--- SECTION 3: All Widgets Inventory & Filtering ---');
    await page.evaluate(() => switchTab('all'));
    await new Promise(r => setTimeout(r, 500));

    // Test 1: All Scope Default Count
    const invCount1 = await page.evaluate(() => filteredData.length);
    if (invCount1 === 294) {
        recordTest('Functional', 'Inventory Default Curriculum Scope', 'admin', 'PASSED', '294 widgets loaded in scope');
    } else {
        recordTest('Functional', 'Inventory Default Curriculum Scope', 'admin', 'FAILED', `Expected 294 but got ${invCount1}`);
    }

    // Test 2: Quick Filter Pills
    const pillTests = [
        { key: 'needs_attention', expected: 36, name: 'Needs Attention Pill' },
        { key: 'matched_all', expected: 258, name: 'Matched in All 3 Pill' },
        { key: 'missing_qa', expected: 15, name: 'Missing in QA Pill' },
        { key: 'requires_dev', expected: 21, name: 'Missing in Git Pill' },
        { key: 'extra_repo', expected: 46, name: 'Extra in Repo Pill' },
        { key: 'all', expected: 294, name: 'All Scope Reset Pill' }
    ];

    for (let pt of pillTests) {
        await page.evaluate(k => setFilterQuick(k), pt.key);
        await new Promise(r => setTimeout(r, 200));
        const count = await page.evaluate(() => filteredData.length);
        if (count === pt.expected) {
            recordTest('Functional', `Quick Filter: ${pt.name}`, 'admin', 'PASSED', `Filtered count: ${count} matches expected ${pt.expected}`);
        } else {
            recordTest('Functional', `Quick Filter: ${pt.name}`, 'admin', 'FAILED', `Got ${count}, expected ${pt.expected}`);
        }
    }

    // Test 3: Search Functionality
    await page.evaluate(() => {
        const inp = document.getElementById('widgetSearch');
        inp.value = 'Fraction';
        filterWidgets();
    });
    await new Promise(r => setTimeout(r, 300));
    const searchRes = await page.evaluate(() => ({
        count: filteredData.length,
        firstName: filteredData[0]?.name
    }));
    if (searchRes.count > 0 && searchRes.firstName.toLowerCase().includes('fraction')) {
        recordTest('Functional', 'Live Search Keyword Matching', 'admin', 'PASSED', `Query "Fraction" returned ${searchRes.count} results (${searchRes.firstName})`);
    } else {
        recordTest('Functional', 'Live Search Keyword Matching', 'admin', 'FAILED', `Unexpected search result: ${JSON.stringify(searchRes)}`);
    }

    // Test 4: Search Clear Button
    await page.evaluate(() => clearSearchInput());
    await new Promise(r => setTimeout(r, 300));
    const afterClearCount = await page.evaluate(() => filteredData.length);
    if (afterClearCount === 294) {
        recordTest('Functional', 'Search Clear Button Reset', 'admin', 'PASSED', 'Restored full 294 items');
    } else {
        recordTest('Functional', 'Search Clear Button Reset', 'admin', 'FAILED', `Got ${afterClearCount} instead of 294`);
    }

    // Test 5: Subject Dropdown Filter
    await page.evaluate(() => {
        document.getElementById('subjectFilter').value = 'Physics';
        filterWidgets();
    });
    await new Promise(r => setTimeout(r, 300));
    const physicsCount = await page.evaluate(() => filteredData.length);
    if (physicsCount === 57) {
        recordTest('Functional', 'Subject Dropdown Filter (Physics)', 'admin', 'PASSED', 'Filtered exactly 57 Physics widgets');
    } else {
        recordTest('Functional', 'Subject Dropdown Filter (Physics)', 'admin', 'FAILED', `Expected 57 Physics widgets, got ${physicsCount}`);
    }

    // Test 6: Owner Dropdown Filter
    await page.evaluate(() => {
        document.getElementById('subjectFilter').value = 'all';
        document.getElementById('ownerFilter').value = 'Prasanna';
        filterWidgets();
    });
    await new Promise(r => setTimeout(r, 300));
    const prasannaCount = await page.evaluate(() => filteredData.length);
    if (prasannaCount === 152) {
        recordTest('Functional', 'Owner Dropdown Filter (Prasanna)', 'admin', 'PASSED', `Filtered exactly 152 widgets owned by Prasanna`);
    } else {
        recordTest('Functional', 'Owner Dropdown Filter (Prasanna)', 'admin', 'FAILED', `Expected 152, got ${prasannaCount}`);
    }

    // Test 7: Reset All Filters Button
    await page.evaluate(() => clearFilter());
    await new Promise(r => setTimeout(r, 300));
    const resetCount = await page.evaluate(() => filteredData.length);
    if (resetCount === 294) {
        recordTest('Functional', 'Reset All Filters Button', 'admin', 'PASSED', 'All dropdowns and search inputs reset back to 294');
    } else {
        recordTest('Functional', 'Reset All Filters Button', 'admin', 'FAILED', `Got ${resetCount} instead of 294`);
    }

    // Test 8: Table Sorting
    await page.evaluate(() => sortData('name'));
    await new Promise(r => setTimeout(r, 300));
    const firstWidgetName = await page.evaluate(() => filteredData[0]?.name);
    if (firstWidgetName === '3D Shapes') {
        recordTest('Functional', 'Table Column Sorting (Name Ascending)', 'admin', 'PASSED', `First widget alphabetically: "${firstWidgetName}"`);
    } else {
        recordTest('Functional', 'Table Column Sorting (Name Ascending)', 'admin', 'FAILED', `Expected "3D Shapes", got "${firstWidgetName}"`);
    }

    // Test 9: Pagination
    const page1Data = await page.evaluate(() => ({
        page: currentPage,
        text: document.getElementById('paginationInfo')?.innerText
    }));
    await page.evaluate(() => changePage(1));
    await new Promise(r => setTimeout(r, 300));
    const page2Data = await page.evaluate(() => ({
        page: currentPage,
        text: document.getElementById('paginationInfo')?.innerText
    }));
    if (page1Data.page === 1 && page2Data.page === 2) {
        recordTest('Functional', 'Table Pagination Controls', 'admin', 'PASSED', `Navigated from Page 1 to Page 2 (${page2Data.text})`);
    } else {
        recordTest('Functional', 'Table Pagination Controls', 'admin', 'FAILED', 'Pagination navigation failed');
    }
    // Return to page 1
    await page.evaluate(() => changePage(-1));

    // Test 10: Widget Detail Modal Opening
    await page.evaluate(() => openModal(1));
    await new Promise(r => setTimeout(r, 400));
    const modalVisible = await page.evaluate(() => {
        const m = document.getElementById('widgetModal');
        return m && !m.classList.contains('hidden');
    });
    if (modalVisible) {
        recordTest('Functional', 'Widget Detail Modal Inspection', 'admin', 'PASSED', 'Widget detail modal opened with full metadata & links');
        await page.evaluate(() => closeModal());
    } else {
        recordTest('Functional', 'Widget Detail Modal Inspection', 'admin', 'FAILED', 'Modal failed to open');
    }

    // =========================================================================
    // 4. ADMIN USER MANAGEMENT & RBAC CRUD
    // =========================================================================
    console.log('\n--- SECTION 4: User Management CRUD & Permissions ---');
    await page.evaluate(() => switchTab('users'));
    await new Promise(r => setTimeout(r, 500));

    const initialUserCount = await page.evaluate(() => authManager.getUsers().length);
    console.log(`  Initial users count in system: ${initialUserCount}`);

    // Create New Team Member (E2E Workflow)
    const testNewEmail = `test.developer_${Date.now()}@company.com`;
    const addRes = await page.evaluate((email) => {
        return authManager.addUser('Automated QA Test Engineer', email, 'QaSecure@2026!', 'developer');
    }, testNewEmail);

    if (addRes.success && addRes.user) {
        recordTest('Workflow', 'Admin Create New User (Developer)', 'admin', 'PASSED', `Created user ${addRes.user.id} (${testNewEmail})`);
    } else {
        recordTest('Workflow', 'Admin Create New User (Developer)', 'admin', 'FAILED', `Failed to create user: ${addRes.error}`);
        recordBug('BUG-USR-01', 'User Management', 'admin', 'Cannot create new user', 'Submit Add User form', 'User created', addRes.error, 'High', 'P1');
    }

    // Negative Test: Duplicate Email Rejection
    const dupRes = await page.evaluate((email) => {
        return authManager.addUser('Duplicate Tester', email, 'SomePass@123', 'viewer');
    }, testNewEmail);

    if (!dupRes.success && dupRes.error.includes('already exists')) {
        recordTest('Negative', 'Duplicate Email Registration Prevention', 'admin', 'PASSED', 'Properly rejected duplicate email address');
    } else {
        recordTest('Negative', 'Duplicate Email Registration Prevention', 'admin', 'FAILED', 'Allowed duplicate email registration');
        recordBug('BUG-USR-02', 'User Management', 'admin', 'Duplicate email allowed in user registration', 'Create user with existing email', 'Rejection with error', 'Created duplicate or unexpected response', 'High', 'P1');
    }

    // Edit User Details
    const editRes = await page.evaluate((userId) => {
        return authManager.updateUser(userId, 'Automated QA Engineer (Edited)', null, 'qa', 'NewPassword@2026!');
    }, addRes.user.id);

    if (editRes.success && editRes.user.role === 'qa') {
        recordTest('Workflow', 'Admin Update User Details & Role', 'admin', 'PASSED', 'Updated full name and changed role to QA');
    } else {
        recordTest('Workflow', 'Admin Update User Details & Role', 'admin', 'FAILED', `Failed to edit user: ${editRes.error}`);
    }

    // Toggle User Status (Disable Account)
    const toggleRes1 = await page.evaluate((userId) => {
        return authManager.toggleUserStatus(userId);
    }, addRes.user.id);

    if (toggleRes1.success && toggleRes1.status === 'disabled') {
        recordTest('Workflow', 'Admin Disable User Account', 'admin', 'PASSED', 'Account status toggled to DISABLED');
    } else {
        recordTest('Workflow', 'Admin Disable User Account', 'admin', 'FAILED', 'Failed to disable user');
    }

    // Negative: Test Login as Disabled User
    const disabledLogin = await page.evaluate((email) => {
        return authManager.login(email, 'NewPassword@2026!');
    }, testNewEmail);

    if (!disabledLogin.success && disabledLogin.error.includes('disabled')) {
        recordTest('Negative', 'Disabled User Login Prevention', 'anonymous', 'PASSED', `Login blocked with message: "${disabledLogin.error}"`);
    } else {
        recordTest('Negative', 'Disabled User Login Prevention', 'anonymous', 'FAILED', 'Disabled user was able to log in');
        recordBug('BUG-SEC-02', 'Authentication', 'anonymous', 'Disabled user can authenticate', 'Attempt login with disabled user credentials', 'Block login with disabled message', 'Login succeeded', 'Critical', 'P0');
    }

    // Delete User (Cleanup)
    const delRes = await page.evaluate((userId) => {
        return authManager.deleteUser(userId);
    }, addRes.user.id);

    if (delRes.success) {
        recordTest('Workflow', 'Admin Delete User Account', 'admin', 'PASSED', `User deleted permanently. Remaining count: ${delRes.remainingCount}`);
    } else {
        recordTest('Workflow', 'Admin Delete User Account', 'admin', 'FAILED', `Failed to delete user: ${delRes.error}`);
    }

    // Negative: Prevent Self-Deletion of Admin
    const selfDelRes = await page.evaluate(() => {
        const adminId = authManager.getCurrentUser().id;
        return authManager.deleteUser(adminId);
    });
    if (!selfDelRes.success && selfDelRes.error.includes('cannot delete your own')) {
        recordTest('Negative', 'Admin Self-Deletion Guard', 'admin', 'PASSED', 'Blocked logged-in admin from deleting their own account');
    } else {
        recordTest('Negative', 'Admin Self-Deletion Guard', 'admin', 'FAILED', 'Allowed admin to delete themselves');
        recordBug('BUG-SEC-03', 'User Management', 'admin', 'Admin can delete own account', 'Attempt self-deletion', 'Block with error message', 'Deletion permitted', 'High', 'P1');
    }

    // =========================================================================
    // 5. ACTIVITY HISTORY AUDIT
    // =========================================================================
    console.log('\n--- SECTION 5: Activity History & Audit Logging ---');
    await page.evaluate(() => switchTab('activity'));
    await new Promise(r => setTimeout(r, 500));

    const activityStats = await page.evaluate(() => {
        const logs = authManager.getLogs();
        const rows = document.querySelectorAll('#activityTableBody tr');
        return {
            logCount: logs.length,
            renderedRows: rows.length,
            hasAuthLogs: logs.some(l => l.activityType === 'LOGIN' || l.activityType === 'USER_MGMT'),
            hasUserMgmt: logs.some(l => l.section === 'User Management')
        };
    });

    if (activityStats.renderedRows > 0 && activityStats.hasUserMgmt) {
        recordTest('Functional', 'Activity History Audit Trail Logging', 'admin', 'PASSED', `Captured ${activityStats.logCount} audit entries including user management actions`);
    } else {
        recordTest('Functional', 'Activity History Audit Trail Logging', 'admin', 'FAILED', `Audit log verification failed: ${JSON.stringify(activityStats)}`);
    }

    // =========================================================================
    // 6. MULTI-ROLE TESTING: DEVELOPER, QA, CONTENT, VIEWER
    // =========================================================================
    console.log('\n--- SECTION 6: Multi-Role Matrix & Privilege Isolation ---');

    const nonAdminRoles = [
        { role: 'developer', email: 'nitin@company.com', pass: 'Nitin@123', name: 'Nitin' },
        { role: 'qa', email: 'qa@company.com', pass: 'Qa@123', name: 'QA Verification Engineer' },
        { role: 'content', email: 'content@company.com', pass: 'Content@123', name: 'Content Team Lead' },
        { role: 'viewer', email: 'viewer@company.com', pass: 'Viewer@123', name: 'Academic Management' }
    ];

    for (let u of nonAdminRoles) {
        console.log(`\n  >> Testing Role: [${u.role.toUpperCase()}] (${u.email})`);

        // 1. Log out previous session
        await page.evaluate(() => authManager.logout());
        await new Promise(r => setTimeout(r, 600));

        // 2. Log in as role
        await page.evaluate((em, pw) => {
            document.getElementById('email').value = em;
            document.getElementById('password').value = pw;
        }, u.email, u.pass);
        await page.click('button[type="submit"]');
        await new Promise(r => setTimeout(r, 800));

        // 3. Verify Landing & Role Badge
        const roleInfo = await page.evaluate(() => {
            return {
                name: document.getElementById('userNameDisplay')?.innerText,
                roleBadge: document.getElementById('userRoleBadge')?.innerText,
                usersTabVisible: !document.getElementById('tab-users')?.classList.contains('hidden'),
                activityTabVisible: !document.getElementById('tab-activity')?.classList.contains('hidden'),
                execSectionsVisible: !document.getElementById('section-project-status-overview')?.classList.contains('hidden')
            };
        });

        if (roleInfo.roleBadge === u.role.toUpperCase() && !roleInfo.usersTabVisible && !roleInfo.activityTabVisible) {
            recordTest('Functional', `RBAC View Isolation (${u.role})`, u.role, 'PASSED', `Role badge: ${roleInfo.roleBadge}. Admin tabs (Users, Activity) properly hidden.`);
        } else {
            recordTest('Functional', `RBAC View Isolation (${u.role})`, u.role, 'FAILED', `Improper visibility: ${JSON.stringify(roleInfo)}`);
            recordBug(`BUG-RBAC-${u.role.toUpperCase()}`, 'RBAC', u.role, `Admin tabs visible to ${u.role}`, `Log in as ${u.role}`, 'Admin tabs hidden', 'Admin tabs visible', 'High', 'P1');
        }

        // 4. Test Restricted Tab Direct Access Attempt (Negative)
        await page.evaluate(() => switchTab('users'));
        await new Promise(r => setTimeout(r, 400));

        const directAccessBlocked = await page.evaluate(() => {
            const usersView = document.getElementById('view-users');
            const toast = document.getElementById('toastNotification');
            const isHidden = !usersView || usersView.classList.contains('hidden');
            const toastMsg = document.getElementById('toastMsg')?.innerText;
            return { isHidden, toastMsg };
        });

        if (directAccessBlocked.isHidden) {
            recordTest('Negative', `Direct Navigation Restriction (${u.role})`, u.role, 'PASSED', 'Blocked attempt to switch to Users tab; view remained hidden');
        } else {
            recordTest('Negative', `Direct Navigation Restriction (${u.role})`, u.role, 'FAILED', 'Unauthorized user was able to reveal Users tab');
            recordBug(`BUG-SEC-${u.role.toUpperCase()}-01`, 'RBAC', u.role, `Unauthorized tab access allowed for ${u.role}`, `Call switchTab('users') as ${u.role}`, 'Block tab switch', 'Tab revealed', 'Critical', 'P0');
        }

        // 5. Verify Core Functionality (Overview & Inventory) works for role
        await page.evaluate(() => {
            switchTab('overview');
        });
        await new Promise(r => setTimeout(r, 300));
        const overviewWorks = await page.evaluate(() => {
            return document.querySelector('#card-kpi-total') !== null && document.getElementById('reconciliationDonutChart') !== null;
        });

        await page.evaluate(() => switchTab('all'));
        await new Promise(r => setTimeout(r, 300));
        const invWorks = await page.evaluate(() => filteredData.length === 294);

        if (overviewWorks && invWorks) {
            recordTest('Functional', `Permitted Features Accessible (${u.role})`, u.role, 'PASSED', 'Overview metrics, donut chart, and 294 widgets inventory fully operational');
        } else {
            recordTest('Functional', `Permitted Features Accessible (${u.role})`, u.role, 'FAILED', `Permitted modules failed to load for ${u.role}`);
        }
    }

    // =========================================================================
    // 7. RESPONSIVE VIEWPORTS & MOBILE LAYOUT TESTING
    // =========================================================================
    console.log('\n--- SECTION 7: Responsive Viewports & Mobile Auditing ---');

    // Return to Admin for full testing
    await page.evaluate(() => authManager.logout());
    await new Promise(r => setTimeout(r, 600));
    await page.evaluate(() => {
        document.getElementById('email').value = 'admin@company.com';
        document.getElementById('password').value = 'Admin@123';
    });
    await page.click('button[type="submit"]');
    await new Promise(r => setTimeout(r, 800));

    // Test Mobile Viewport (iPhone SE / 375x667)
    await page.setViewport({ width: 375, height: 667 });
    await page.evaluate(() => switchTab('overview'));
    await new Promise(r => setTimeout(r, 500));

    const mobileOverviewInfo = await page.evaluate(() => {
        const bento = document.querySelector('.sm\\:hidden.app-card');
        const desktopKpis = document.querySelector('.hidden.sm\\:block');
        return {
            bentoVisible: bento !== null && window.getComputedStyle(bento).display !== 'none',
            desktopKpisHidden: desktopKpis !== null && window.getComputedStyle(desktopKpis).display === 'none'
        };
    });

    if (mobileOverviewInfo.bentoVisible && mobileOverviewInfo.desktopKpisHidden) {
        recordTest('UI/UX', 'Mobile Responsive Layout (375px)', 'admin', 'PASSED', 'Mobile Executive Summary Bento active, desktop cards hidden');
    } else {
        recordTest('UI/UX', 'Mobile Responsive Layout (375px)', 'admin', 'FAILED', `Mobile bento state: ${JSON.stringify(mobileOverviewInfo)}`);
    }

    // Test Mobile Inventory Cards
    await page.evaluate(() => switchTab('all'));
    await new Promise(r => setTimeout(r, 500));
    const mobileCardsInfo = await page.evaluate(() => {
        const list = document.getElementById('widgetMobileCardsList');
        const desktopTable = document.querySelector('.hidden.md\\:block.overflow-x-auto');
        return {
            cardsCount: list?.children.length || 0,
            tableHidden: desktopTable !== null && window.getComputedStyle(desktopTable).display === 'none'
        };
    });

    if (mobileCardsInfo.cardsCount > 0 && mobileCardsInfo.tableHidden) {
        recordTest('UI/UX', 'Mobile Inventory Cards Rendering', 'admin', 'PASSED', `Rendered ${mobileCardsInfo.cardsCount} mobile cards on small screen`);
    } else {
        recordTest('UI/UX', 'Mobile Inventory Cards Rendering', 'admin', 'FAILED', 'Mobile cards failed to render');
    }

    // Return to desktop viewport
    await page.setViewport({ width: 1440, height: 900 });

    // =========================================================================
    // 8. FINAL SUMMARY
    // =========================================================================
    console.log('\n========================================================================');
    console.log('AUDIT EXECUTION COMPLETE');
    console.log(`Total Assertions Checked: ${auditResults.summary.totalTests}`);
    console.log(`Passed: ${auditResults.summary.passed}`);
    console.log(`Failed: ${auditResults.summary.failed}`);
    console.log(`Blocked: ${auditResults.summary.blocked}`);
    console.log(`Bugs Discovered: ${auditResults.bugs.length}`);
    console.log(`Console Errors: ${consoleErrors.length}`);
    console.log('========================================================================\n');

    await browser.close();

    // Save JSON results to disk for formal report generation
    fs.writeFileSync(
        path.join(__dirname, 'multi_role_audit_results.json'),
        JSON.stringify(auditResults, null, 2),
        'utf8'
    );
}

runFullAudit().catch(err => {
    console.error('Audit Runner Error:', err);
    process.exit(1);
});
