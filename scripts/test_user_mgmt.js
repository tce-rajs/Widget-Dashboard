const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');
const path = require('path');
const fs = require('fs');

async function testUserManagement() {
    console.log('Starting User Addition & Deletion E2E Test...');
    const errors = [];

    const browser = await puppeteer.launch({
        executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 960 });

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

    // 1. Log in as Admin
    console.log('1. Logging in as Admin...');
    await page.goto('http://localhost:8000/login.html', { waitUntil: 'networkidle0' });
    await page.type('#email', 'admin');
    await page.type('#password', 'Admin@123');
    await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle0' }),
        page.click('button[type="submit"]')
    ]);

    // 2. Open User Management Tab
    console.log('2. Switching to User Management Tab...');
    await page.click('#tab-users');
    await new Promise(r => setTimeout(r, 400));

    const initialTotal = parseInt(await page.$eval('#statTotalUsers', el => el.innerText.trim()));
    console.log(`Initial total users: ${initialTotal}`);

    // 3. Test Add User Modal
    console.log('3. Opening Add User modal and submitting new user...');
    await page.click('button[onclick="openAddUserModal()"]');
    await new Promise(r => setTimeout(r, 300));

    const isModalOpen = await page.$eval('#addUserModal', el => !el.classList.contains('hidden'));
    console.log(`Add User Modal Open: ${isModalOpen}`);
    if (!isModalOpen) errors.push('Add User modal failed to open');

    await page.type('#addUserName', 'Sarah Connor');
    await page.type('#addUserEmail', 'sarah.connor@sky.net');
    await page.select('#addUserRole', 'developer');
    await page.evaluate(() => { document.getElementById('addUserPass').value = ''; });
    await page.type('#addUserPass', 'Sarah@1234');

    await page.click('#addUserModal button[type="submit"]');
    await new Promise(r => setTimeout(r, 500));

    const isModalClosed = await page.$eval('#addUserModal', el => el.classList.contains('hidden'));
    console.log(`Add User Modal Closed: ${isModalClosed}`);
    if (!isModalClosed) errors.push('Add User modal did not close after submit');

    const afterAddTotal = parseInt(await page.$eval('#statTotalUsers', el => el.innerText.trim()));
    console.log(`Total users after add: ${afterAddTotal} (Expected: ${initialTotal + 1})`);
    if (afterAddTotal !== initialTotal + 1) errors.push(`Expected total users ${initialTotal + 1}, got ${afterAddTotal}`);

    // Verify user in table
    const tableText = await page.$eval('#userTableBody', el => el.innerText);
    const userFound = tableText.includes('Sarah Connor') && tableText.includes('sarah.connor@sky.net');
    console.log(`New user in table: ${userFound}`);
    if (!userFound) errors.push('Newly added user not found in table text');

    // 4. Test Logging in as Newly Added User
    console.log('4. Testing login with newly added user credentials...');
    await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle0' }),
        page.evaluate(() => handleLogout())
    ]);

    await page.type('#email', 'sarah.connor@sky.net');
    await page.type('#password', 'Sarah@1234');
    await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle0' }),
        page.click('button[type="submit"]')
    ]);

    const loggedInName = await page.$eval('#userNameDisplay', el => el.innerText.trim());
    const loggedInRole = await page.$eval('#userRoleBadge', el => el.innerText.trim());
    console.log(`Logged in as: "${loggedInName}" with role: "${loggedInRole}"`);
    if (loggedInName !== 'Sarah Connor' || loggedInRole !== 'DEVELOPER') {
        errors.push(`Expected Sarah Connor / DEVELOPER, got ${loggedInName} / ${loggedInRole}`);
    }

    // 5. Log back in as Admin and Delete Sarah Connor
    console.log('5. Logging back in as Admin to delete user...');
    await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle0' }),
        page.evaluate(() => handleLogout())
    ]);

    await page.type('#email', 'admin');
    await page.type('#password', 'Admin@123');
    await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle0' }),
        page.click('button[type="submit"]')
    ]);

    await page.click('#tab-users');
    await new Promise(r => setTimeout(r, 400));

    // Find delete button for sarah.connor@sky.net
    console.log('6. Deleting Sarah Connor...');
    const sarahUserId = await page.evaluate(() => {
        const rows = Array.from(document.querySelectorAll('#userTableBody tr'));
        for (const row of rows) {
            if (row.innerText.includes('sarah.connor@sky.net')) {
                const deleteBtn = row.querySelector('button[onclick*="openDeleteUserModal"]');
                if (deleteBtn) {
                    const match = deleteBtn.getAttribute('onclick').match(/openDeleteUserModal\('([^']+)'\)/);
                    return match ? match[1] : null;
                }
            }
        }
        return null;
    });

    console.log(`Found Sarah's user ID: ${sarahUserId}`);
    if (!sarahUserId) errors.push("Could not find Sarah's delete button");

    await page.evaluate(id => openDeleteUserModal(id), sarahUserId);
    await new Promise(r => setTimeout(r, 300));

    const isDeleteModalOpen = await page.$eval('#deleteUserModal', el => !el.classList.contains('hidden'));
    console.log(`Delete modal open: ${isDeleteModalOpen}`);
    if (!isDeleteModalOpen) errors.push('Delete user modal failed to open');

    await page.click('#confirmDeleteBtn');
    await new Promise(r => setTimeout(r, 500));

    const isDeleteModalClosed = await page.$eval('#deleteUserModal', el => el.classList.contains('hidden'));
    console.log(`Delete modal closed: ${isDeleteModalClosed}`);

    const finalTotal = parseInt(await page.$eval('#statTotalUsers', el => el.innerText.trim()));
    console.log(`Final total users after delete: ${finalTotal} (Expected: ${initialTotal})`);
    if (finalTotal !== initialTotal) errors.push(`Expected total ${initialTotal}, got ${finalTotal}`);

    const finalTableText = await page.$eval('#userTableBody', el => el.innerText);
    const stillPresent = finalTableText.includes('sarah.connor@sky.net');
    console.log(`User still in table: ${stillPresent} (Expected: false)`);
    if (stillPresent) errors.push('Deleted user is still present in table');

    // 7. Verify Deleted User CANNOT Log In
    console.log('7. Verifying deleted user cannot log in...');
    await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle0' }),
        page.evaluate(() => handleLogout())
    ]);

    await page.type('#email', 'sarah.connor@sky.net');
    await page.type('#password', 'Sarah@1234');
    await page.click('button[type="submit"]');
    await new Promise(r => setTimeout(r, 400));

    const errorVisible = await page.$eval('#errorBanner', el => !el.classList.contains('hidden'));
    console.log(`Login rejected for deleted user: ${errorVisible} (Expected: true)`);
    if (!errorVisible) errors.push('Deleted user was able to log in!');

    await browser.close();

    console.log('\n======================================================');
    console.log(`USER MANAGEMENT TEST RESULTS:`);
    console.log(`- Errors: ${errors.length}`);
    if (errors.length > 0) {
        console.error('Errors encountered:', errors);
        process.exit(1);
    } else {
        console.log('- ALL USER ADDITION & DELETION TESTS PASSED (0 ERRORS)!');
        console.log('======================================================');
    }
}

testUserManagement().catch(err => {
    console.error('Test execution error:', err);
    process.exit(1);
});
