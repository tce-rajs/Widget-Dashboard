const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');
const fs = require('fs');
const path = require('path');

async function runAllScenarios() {
    console.log('========================================================');
    console.log('STARTING COMPREHENSIVE USER PERSISTENCE SCENARIOS TEST');
    console.log('========================================================\n');

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
    await page.setViewport({ width: 1440, height: 900 });

    const errors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') {
            console.error('[BROWSER ERROR]:', msg.text());
        }
    });

    async function loginAs(user, pass) {
        // Clear auth sessions safely
        await page.evaluate(() => {
            localStorage.removeItem('widget_dashboard_auth_state_v1');
            sessionStorage.removeItem('widget_dashboard_auth_state_v1');
        }).catch(() => {});
        await page.goto('http://localhost:8000/login.html', { waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 300));
        await page.evaluate((u, p) => {
            document.getElementById('email').value = u;
            document.getElementById('password').value = p;
            document.querySelector('form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        }, user, pass);
        await page.waitForNavigation({ waitUntil: 'domcontentloaded' });
    }

    try {
        // Setup: Clean state & login as Admin
        await page.goto('http://localhost:8000/login.html', { waitUntil: 'domcontentloaded' });
        await page.evaluate(() => {
            localStorage.clear();
            sessionStorage.clear();
        });
        await loginAs('admin', 'Admin@123');
        console.log('[SETUP] Logged in as Admin.');

        // -----------------------------------------------------------------
        // SCENARIO 1: Add new user, stay on Users tab, refresh page (F5)
        // -----------------------------------------------------------------
        console.log('\n--- Scenario 1: Add New User & Page Refresh (F5) ---');
        await page.evaluate(() => switchTab('users'));
        await new Promise(r => setTimeout(r, 400));

        const initialUsersCount = await page.evaluate(() => authManager.getUsers().length);
        console.log(`Initial total users: ${initialUsersCount}`);

        // Add user: John Wick (john.wick@continental.com)
        await page.evaluate(() => {
            document.getElementById('addUserName').value = 'John Wick';
            document.getElementById('addUserEmail').value = 'john.wick@continental.com';
            document.getElementById('addUserRole').value = 'developer';
            document.getElementById('addUserPass').value = 'Continental@123';
            const form = document.querySelector('#addUserModal form');
            form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        });
        await new Promise(r => setTimeout(r, 500));

        let usersAfterAdd = await page.evaluate(() => authManager.getUsers());
        const foundNewUser = usersAfterAdd.find(u => u.email === 'john.wick@continental.com');
        console.log(`User created: ${foundNewUser ? 'YES' : 'NO'} (Total: ${usersAfterAdd.length})`);
        if (!foundNewUser) errors.push('Scenario 1 Failed: User not created in authManager.');

        // Take screenshot before refresh
        await page.screenshot({ path: path.join(screenshotDir, '142_scenario1_before_refresh.png') });

        // REFRESH PAGE (F5)
        console.log('Simulating browser refresh (F5)...');
        await page.reload({ waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 800));

        // Verify active tab remains 'users'
        const currentActiveTab = await page.evaluate(() => {
            const usersView = document.getElementById('view-users');
            return usersView && !usersView.classList.contains('hidden') ? 'users' : 'other';
        });
        console.log(`Active view after refresh: ${currentActiveTab}`);
        if (currentActiveTab !== 'users') {
            errors.push(`Scenario 1 Failed: Tab was reset to ${currentActiveTab} instead of remaining on users.`);
        }

        // Verify user is still in the DOM table after refresh
        const userInTableAfterRefresh = await page.evaluate(() => {
            const row = Array.from(document.querySelectorAll('#userTableBody tr')).find(tr => tr.innerText.includes('john.wick@continental.com'));
            return !!row;
        });
        console.log(`User displayed in DOM table after refresh: ${userInTableAfterRefresh}`);
        if (!userInTableAfterRefresh) {
            errors.push('Scenario 1 Failed: User was removed from table after refresh!');
        }

        const usersCountAfterRefresh = await page.evaluate(() => authManager.getUsers().length);
        console.log(`Total users after refresh: ${usersCountAfterRefresh} (Expected: ${initialUsersCount + 1})`);
        if (usersCountAfterRefresh !== initialUsersCount + 1) {
            errors.push(`Scenario 1 Failed: Count mismatch after refresh (${usersCountAfterRefresh} vs ${initialUsersCount + 1})`);
        }
        await page.screenshot({ path: path.join(screenshotDir, '143_scenario1_after_refresh_persisted.png') });
        console.log('[PASS] Scenario 1: User addition and page refresh passed!');

        // -----------------------------------------------------------------
        // SCENARIO 2: Re-adding a previously deleted user & page refresh
        // -----------------------------------------------------------------
        console.log('\n--- Scenario 2: Re-Add Previously Deleted Email & Refresh ---');
        // Delete John Wick first
        const johnId = await page.evaluate(() => {
            const u = authManager.getUsers().find(x => x.email === 'john.wick@continental.com');
            return u ? u.id : null;
        });
        await page.evaluate((id) => {
            authManager.deleteUser(id);
            renderUsersTable();
        }, johnId);

        let afterDeleteCount = await page.evaluate(() => authManager.getUsers().length);
        console.log(`After deleting John Wick: ${afterDeleteCount}`);

        // Now re-add John Wick with same email
        await page.evaluate(() => {
            authManager.addUser('John Wick Reborn', 'john.wick@continental.com', 'Reborn@123', 'qa');
            renderUsersTable();
        });
        console.log('Re-added John Wick with same email.');

        // Refresh page again
        await page.reload({ waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 800));

        const foundReborn = await page.evaluate(() => {
            const u = authManager.getUsers().find(x => x.email === 'john.wick@continental.com');
            return u && u.fullName === 'John Wick Reborn';
        });
        console.log(`Re-added user retained after refresh: ${foundReborn}`);
        if (!foundReborn) {
            errors.push('Scenario 2 Failed: Re-added user was wiped by deleted list filter on refresh!');
        } else {
            console.log('[PASS] Scenario 2: Re-added user persisted successfully across refresh!');
        }

        // -----------------------------------------------------------------
        // SCENARIO 3: Log in as newly created user
        // -----------------------------------------------------------------
        console.log('\n--- Scenario 3: Login as Newly Created User ---');
        await page.evaluate(() => authManager.logout());
        await page.waitForNavigation({ waitUntil: 'domcontentloaded' });

        // Log in using newly created user's credentials
        await page.evaluate(() => {
            document.getElementById('email').value = 'john.wick@continental.com';
            document.getElementById('password').value = 'Reborn@123';
            document.querySelector('form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        });
        await page.waitForNavigation({ waitUntil: 'domcontentloaded' });

        const loggedInUserRole = await page.evaluate(() => {
            const pill = document.getElementById('userRoleBadge');
            return pill ? pill.innerText : '';
        });
        console.log(`Logged in as new user with role: ${loggedInUserRole}`);
        if (loggedInUserRole !== 'QA') {
            errors.push(`Scenario 3 Failed: Expected QA role but got ${loggedInUserRole}`);
        }

        // Verify QA cannot see Users tab
        const canSeeUsersTab = await page.evaluate(() => {
            const tab = document.getElementById('tab-users');
            return tab && !tab.classList.contains('hidden');
        });
        console.log(`Non-admin can see Users tab: ${canSeeUsersTab} (Expected: false)`);
        if (canSeeUsersTab) errors.push('Scenario 3 Failed: Non-admin user can see admin Users tab!');

        // Refresh while logged in as new user
        await page.reload({ waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 600));
        const roleAfterReload = await page.evaluate(() => document.getElementById('userRoleBadge').innerText);
        console.log(`Role after reload: ${roleAfterReload} (Expected: QA)`);
        if (roleAfterReload !== 'QA') errors.push('Scenario 3 Failed: Session lost on reload.');
        console.log('[PASS] Scenario 3: New user login & session persistence verified!');

        // -----------------------------------------------------------------
        // SCENARIO 4: Edit User details & Refresh
        // -----------------------------------------------------------------
        console.log('\n--- Scenario 4: Edit User Details & Refresh ---');
        // Log back in as admin
        await loginAs('admin', 'Admin@123');
        await page.evaluate(() => switchTab('users'));
        await new Promise(r => setTimeout(r, 400));

        // Find John Wick Reborn and edit name to "Jonathan Wick" and role to "developer"
        const targetUserId = await page.evaluate(() => {
            const u = authManager.getUsers().find(x => x.email === 'john.wick@continental.com');
            return u ? u.id : null;
        });

        await page.evaluate((id) => {
            authManager.editUser(id, {
                fullName: 'Jonathan Wick Sr',
                email: 'john.wick@continental.com',
                role: 'developer',
                password: 'NewPass@123'
            });
            renderUsersTable();
        }, targetUserId);

        // Refresh
        await page.reload({ waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 800));

        const editedUser = await page.evaluate(() => {
            return authManager.getUsers().find(x => x.email === 'john.wick@continental.com');
        });
        console.log(`Edited user name: ${editedUser ? editedUser.fullName : 'NOT FOUND'}`);
        console.log(`Edited user role: ${editedUser ? editedUser.role : 'NOT FOUND'}`);
        if (!editedUser || editedUser.fullName !== 'Jonathan Wick Sr' || editedUser.role !== 'developer') {
            errors.push('Scenario 4 Failed: Edited details not persisted on refresh.');
        } else {
            console.log('[PASS] Scenario 4: Edit user details persisted on refresh!');
        }

        // -----------------------------------------------------------------
        // SCENARIO 5: Disable User & Refresh & Login Denial
        // -----------------------------------------------------------------
        console.log('\n--- Scenario 5: Disable User, Refresh & Verify Login Denial ---');
        await page.evaluate((id) => {
            authManager.toggleUserStatus(id);
            renderUsersTable();
        }, targetUserId);

        // Refresh
        await page.reload({ waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 800));

        const disabledStatus = await page.evaluate((id) => {
            const u = authManager.getUsers().find(x => x.id === id);
            return u ? u.status : null;
        }, targetUserId);
        console.log(`User status after reload: ${disabledStatus} (Expected: disabled)`);
        if (disabledStatus !== 'disabled') errors.push('Scenario 5 Failed: Status not disabled after reload.');

        // Test login with disabled user
        await page.evaluate(() => {
            localStorage.removeItem('widget_dashboard_auth_state_v1');
            sessionStorage.removeItem('widget_dashboard_auth_state_v1');
        }).catch(() => {});
        await page.goto('http://localhost:8000/login.html', { waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 300));
        await page.evaluate(() => {
            document.getElementById('email').value = 'john.wick@continental.com';
            document.getElementById('password').value = 'NewPass@123';
            document.querySelector('form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        });
        await new Promise(r => setTimeout(r, 600));

        const errorMsg = await page.evaluate(() => {
            const err = document.getElementById('errorBanner');
            return err && !err.classList.contains('hidden') ? err.innerText : '';
        });
        console.log(`Disabled login rejected with message: "${errorMsg.trim()}"`);
        if (!errorMsg.toLowerCase().includes('disabled')) {
            errors.push('Scenario 5 Failed: Disabled account was not rejected properly.');
        } else {
            console.log('[PASS] Scenario 5: Disabled user persistence and login denial verified!');
        }

        // -----------------------------------------------------------------
        // SCENARIO 6: Re-Enable User, Refresh & Successful Login
        // -----------------------------------------------------------------
        console.log('\n--- Scenario 6: Re-Enable User, Refresh & Verify Login ---');
        await loginAs('admin', 'Admin@123');
        await page.evaluate(() => switchTab('users'));
        await new Promise(r => setTimeout(r, 400));

        await page.evaluate((id) => {
            authManager.toggleUserStatus(id);
            renderUsersTable();
        }, targetUserId);

        // Refresh
        await page.reload({ waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 800));

        const enabledStatus = await page.evaluate((id) => {
            const u = authManager.getUsers().find(x => x.id === id);
            return u ? u.status : null;
        }, targetUserId);
        console.log(`User status after re-enabling & reload: ${enabledStatus} (Expected: active)`);
        if (enabledStatus !== 'active') errors.push('Scenario 6 Failed: User not active after re-enabling.');
        else console.log('[PASS] Scenario 6: Re-enabled user persisted successfully!');

        // -----------------------------------------------------------------
        // SCENARIO 7: Non-Admin Direct Tab URL Navigation Security Guard
        // -----------------------------------------------------------------
        console.log('\n--- Scenario 7: Non-Admin URL Hash Guard ---');
        await loginAs('nitin', 'Nitin@123');
        // Try to access #users directly
        await page.goto('http://localhost:8000/index.html#users', { waitUntil: 'domcontentloaded' });
        await new Promise(r => setTimeout(r, 800));

        const nonAdminUsersVisible = await page.evaluate(() => {
            const v = document.getElementById('view-users');
            return v && !v.classList.contains('hidden');
        });
        console.log(`Non-admin on #users can view users: ${nonAdminUsersVisible} (Expected: false)`);
        if (nonAdminUsersVisible) {
            errors.push('Scenario 7 Failed: Non-admin accessed Users tab via URL hash on reload!');
        } else {
            console.log('[PASS] Scenario 7: Security guard correctly blocked unauthorized tab access.');
        }

    } catch (e) {
        errors.push(`Unhandled Test Exception: ${e.message}`);
        console.error('Unhandled exception:', e);
    } finally {
        await browser.close();
    }

    console.log('\n======================================================');
    console.log('COMPREHENSIVE USER PERSISTENCE TEST RESULTS:');
    console.log(`- Errors: ${errors.length}`);
    if (errors.length > 0) {
        console.error('Errors encountered:');
        errors.forEach(e => console.error('  *', e));
        process.exit(1);
    } else {
        console.log('- ALL SCENARIOS PASSED WITH 0 ERRORS!');
        console.log('======================================================');
        process.exit(0);
    }
}

runAllScenarios();
