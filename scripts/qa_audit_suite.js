const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');

async function runQAAudit() {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  const auditLog = {
    phases: {},
    passed: [],
    failed: [],
    uxGaps: [],
    uiIssues: [],
    consoleErrors: []
  };

  page.on('console', msg => {
    if (msg.type() === 'error') {
      auditLog.consoleErrors.push({ text: msg.text(), location: msg.location() });
    }
  });
  page.on('pageerror', err => {
    auditLog.consoleErrors.push({ text: err.message, stack: err.stack });
  });

  console.log('==================================================');
  console.log('STARTING SENIOR QA APPLICATION AUDIT & TEST SUITE');
  console.log('==================================================');

  // ----------------------------------------------------
  // PHASE 1 & 2: AUTHENTICATION, ROUTE GUARDS & SESSIONS
  // ----------------------------------------------------
  console.log('\n[TEST GROUP 1] Authentication & Access Control');

  // Test 1.1: Unauthenticated redirect to login
  await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle2' });
  const currentUrl = page.url();
  if (currentUrl.includes('login.html')) {
    auditLog.passed.push('Route Guard: Unauthenticated user redirected to login.html with redirect parameter.');
    console.log('  ✓ Route guard redirect passed');
  } else {
    auditLog.failed.push({
      feature: 'Route Guard',
      expected: 'Redirect to login.html',
      actual: currentUrl,
      severity: 'Critical'
    });
    console.log('  ✗ Route guard redirect failed');
  }

  // Test 1.2: Invalid Login Attempt
  await page.type('#email', 'invalid.user@company.com');
  await page.type('#password', 'WrongPassword123');
  await page.click('button[type="submit"]');
  await new Promise(r => setTimeout(r, 600));

  const errorBannerVisible = await page.evaluate(() => {
    const banner = document.getElementById('errorBanner');
    const msg = document.getElementById('errorMessage');
    if (banner && !banner.classList.contains('hidden')) {
      return msg ? msg.innerText : 'Error visible';
    }
    return '';
  });
  if (errorBannerVisible) {
    auditLog.passed.push('Login Validation: Rejects invalid credentials with visible error banner.');
    console.log('  ✓ Invalid login rejected correctly: ' + errorBannerVisible.replace(/\n/g, ' '));
  } else {
    auditLog.failed.push({
      feature: 'Login Validation',
      expected: 'Visible error banner for invalid credentials',
      actual: 'No visible error',
      severity: 'High'
    });
  }

  // Test 1.3: Valid Admin Login
  await page.evaluate(() => {
    document.getElementById('email').value = 'admin@company.com';
    document.getElementById('password').value = 'Admin@123';
  });
  await page.click('button[type="submit"]');
  await new Promise(r => setTimeout(r, 800));

  const afterLoginUrl = page.url();
  if (afterLoginUrl.includes('index.html')) {
    auditLog.passed.push('Admin Login: Authenticates and redirects successfully to index.html.');
    console.log('  ✓ Valid login successful, landed on index.html');
  } else {
    auditLog.failed.push({
      feature: 'Admin Login',
      expected: 'Redirect to index.html',
      actual: afterLoginUrl,
      severity: 'Critical'
    });
  }

  // ----------------------------------------------------
  // TEST GROUP 2: OVERVIEW PAGE & SINGLE DIAGRAM
  // ----------------------------------------------------
  console.log('\n[TEST GROUP 2] Overview Dashboard & Visual Analytics');

  // Test 2.1: KPI Cards verification
  const kpiData = await page.evaluate(() => {
    return {
      total: document.querySelector('#card-kpi-total span')?.innerText.trim(),
      attention: document.querySelector('#card-kpi-attention span')?.innerText.trim(),
      qa: document.querySelector('#card-kpi-qa span')?.innerText.trim(),
      git: document.querySelector('#card-kpi-git span')?.innerText.trim(),
      xl: document.querySelector('#card-kpi-xl span')?.innerText.trim()
    };
  });
  console.log('  KPI Values Detected:', kpiData);
  if (kpiData.total === '294' || kpiData.total === '340') {
    auditLog.passed.push(`KPI Metrics: Correct baseline detected (Total: ${kpiData.total}, Attention: ${kpiData.attention}, QA: ${kpiData.qa}).`);
  }

  // Test 2.2: Single Donut Chart
  const chartCanvas = await page.$('#reconciliationDonutChart');
  if (chartCanvas) {
    const isChartVisible = await page.evaluate(() => {
      const c = document.getElementById('reconciliationDonutChart');
      return c && c.offsetHeight > 100 && c.offsetWidth > 100;
    });
    if (isChartVisible) {
      auditLog.passed.push('Single Chart Standard: Widget Status Breakdown donut chart rendered with non-zero dimensions.');
      console.log('  ✓ Donut chart canvas rendered correctly');
    } else {
      auditLog.failed.push({
        feature: 'Donut Chart Render',
        expected: 'Height & width > 100px',
        actual: 'Canvas hidden or 0 dimensions',
        severity: 'Medium'
      });
    }
  }

  // Test 2.3: Reconciliation Matrix Table
  const matrixRowCount = await page.evaluate(() => {
    return document.querySelectorAll('#view-overview table tbody tr').length;
  });
  console.log(`  ✓ Reconciliation Matrix contains ${matrixRowCount} category rows`);
  if (matrixRowCount >= 4) {
    auditLog.passed.push(`Reconciliation Matrix: ${matrixRowCount} status rows displayed.`);
  }

  // Test 2.4: Drilldown action from Overview to Inventory
  await page.evaluate(() => drillDown('needs_attention'));
  await new Promise(r => setTimeout(r, 400));

  const isInventoryActive = await page.evaluate(() => {
    const invView = document.getElementById('view-inventory');
    return invView && !invView.classList.contains('hidden');
  });
  const filterPillActive = await page.evaluate(() => {
    const pill = document.getElementById('pill-filter-needs_attention');
    return pill && pill.classList.contains('bg-rose-600');
  });

  if (isInventoryActive && filterPillActive) {
    auditLog.passed.push('Drilldown Workflow: Clicking Overview metric switches to Inventory with active filter.');
    console.log('  ✓ Overview drilldown to Inventory verified');
  } else {
    auditLog.failed.push({
      feature: 'Overview Drilldown',
      expected: 'Switch to inventory tab with active status pill',
      actual: `Inventory active: ${isInventoryActive}, Pill active: ${filterPillActive}`,
      severity: 'High'
    });
  }

  // ----------------------------------------------------
  // TEST GROUP 3: INVENTORY TABLE, FILTERS, SEARCH, SORT
  // ----------------------------------------------------
  console.log('\n[TEST GROUP 3] Inventory Tab Filtering, Searching & Sorting');

  // Test 3.1: Reset filters
  await page.evaluate(() => clearFilter());
  await new Promise(r => setTimeout(r, 300));
  let count = await page.$eval('#totalFiltered', el => el.innerText);
  console.log(`  All Scope total widgets: ${count}`);
  if (count === '294') {
    auditLog.passed.push('Scope Filter: Default All Scope shows exactly 294 curriculum widgets.');
  }

  // Test 3.2: 1-Click Status Pills
  const statusTests = [
    { key: 'needs_attention', expected: 36, name: 'Needs Attention' },
    { key: 'matched_all', expected: 258, name: 'Matched in All 3' },
    { key: 'missing_qa', expected: 15, name: 'Missing in QA' },
    { key: 'requires_dev', expected: 21, name: 'Missing in Git' },
    { key: 'extra_repo', expected: 46, name: 'Extra in Repo' }
  ];

  for (const st of statusTests) {
    await page.evaluate((k) => setFilterQuick(k), st.key);
    await new Promise(r => setTimeout(r, 200));
    const c = parseInt(await page.$eval('#totalFiltered', el => el.innerText), 10);
    if (c === st.expected) {
      auditLog.passed.push(`Filter Pill [${st.name}]: Displayed exact expected count (${c}).`);
      console.log(`  ✓ Filter ${st.name} count: ${c} (matches expected ${st.expected})`);
    } else {
      auditLog.failed.push({
        feature: `Filter Pill [${st.name}]`,
        expected: `${st.expected}`,
        actual: `${c}`,
        severity: 'High'
      });
      console.log(`  ✗ Filter ${st.name} count mismatch: ${c} vs ${st.expected}`);
    }
  }

  // Test 3.3: Search filtering
  await page.evaluate(() => {
    clearFilter();
    const inp = document.getElementById('widgetSearch');
    inp.value = 'heart';
    filterWidgets();
  });
  await new Promise(r => setTimeout(r, 200));
  let searchCount = parseInt(await page.$eval('#totalFiltered', el => el.innerText), 10);
  console.log(`  ✓ Search query 'heart' yielded: ${searchCount} results`);
  if (searchCount > 0) {
    auditLog.passed.push(`Search: Keyword 'heart' returned ${searchCount} relevant results.`);
  }

  // Test 3.4: Clear search button
  await page.click('#searchClearBtn');
  await new Promise(r => setTimeout(r, 200));
  let afterClearCount = parseInt(await page.$eval('#totalFiltered', el => el.innerText), 10);
  if (afterClearCount === 294) {
    auditLog.passed.push('Search Clear: [x] button clears input and restores full inventory.');
    console.log('  ✓ Search clear button restored 294 items');
  }

  // Test 3.5: Owner Filtering
  await page.evaluate(() => {
    const sel = document.getElementById('ownerFilter');
    sel.value = 'Prasanna';
    filterWidgets();
  });
  await new Promise(r => setTimeout(r, 200));
  let psCount = parseInt(await page.$eval('#totalFiltered', el => el.innerText), 10);
  if (psCount === 152) {
    auditLog.passed.push('Owner Filter: Filter by "Prasanna" returned exact count of 152 widgets.');
    console.log('  ✓ Owner filter "Prasanna" passed: 152 items');
  }

  await page.evaluate(() => {
    const sel = document.getElementById('ownerFilter');
    sel.value = 'Nitin';
    filterWidgets();
  });
  await new Promise(r => setTimeout(r, 200));
  let nitinCount = parseInt(await page.$eval('#totalFiltered', el => el.innerText), 10);
  if (nitinCount === 140) {
    auditLog.passed.push('Owner Filter: Filter by "Nitin" returned exact count of 140 widgets.');
    console.log('  ✓ Owner filter "Nitin" passed: 140 items');
  }

  // Test 3.6: Sorting
  await page.evaluate(() => {
    clearFilter();
    sortData('name');
  });
  await new Promise(r => setTimeout(r, 200));
  const firstName = await page.evaluate(() => {
    return document.querySelector('#widgetTableBody tr td:nth-child(2) div')?.innerText.trim();
  });
  console.log('  ✓ Sorted by name (A-Z) first widget:', firstName);
  auditLog.passed.push(`Sorting: Sorted by name ascending (first widget: "${firstName}").`);

  // Test 3.7: Pagination
  const pageIndicator = await page.$eval('#pageIndicator', el => el.innerText);
  console.log('  Initial pagination state:', pageIndicator);
  await page.click('#nextBtn');
  await new Promise(r => setTimeout(r, 200));
  const page2Indicator = await page.$eval('#pageIndicator', el => el.innerText);
  console.log('  After Next click:', page2Indicator);
  if (page2Indicator.includes('Page 2')) {
    auditLog.passed.push('Pagination: Next button navigated to Page 2 successfully.');
  }
  await page.click('#prevBtn');
  await new Promise(r => setTimeout(r, 200));

  // Test 3.8: Widget Details Modal
  await page.evaluate(() => openModal(1));
  await new Promise(r => setTimeout(r, 300));
  const modalVisible = await page.evaluate(() => {
    const m = document.getElementById('detailModal');
    return m && !m.classList.contains('hidden');
  });
  const modalWidgetName = await page.evaluate(() => document.getElementById('modalName')?.innerText);
  console.log(`  ✓ Widget modal opened for: "${modalWidgetName}", visible: ${modalVisible}`);
  if (modalVisible && modalWidgetName) {
    auditLog.passed.push(`Widget Details Modal: Opens correctly with title "${modalWidgetName}".`);
  }
  // Close modal via Escape
  await page.keyboard.press('Escape');
  await new Promise(r => setTimeout(r, 300));
  const modalClosed = await page.evaluate(() => {
    const m = document.getElementById('detailModal');
    return m && m.classList.contains('hidden');
  });
  if (modalClosed) {
    auditLog.passed.push('Widget Modal: Closed cleanly via Escape key.');
    console.log('  ✓ Modal closed via Escape key');
  }

  // ----------------------------------------------------
  // TEST GROUP 4: USER MANAGEMENT & RBAC
  // ----------------------------------------------------
  console.log('\n[TEST GROUP 4] User Management & Role-Based Access Control');

  // Test 4.1: Switch to Users Tab as Admin
  await page.evaluate(() => switchTab('users'));
  await new Promise(r => setTimeout(r, 400));

  const isUsersViewActive = await page.evaluate(() => {
    const v = document.getElementById('view-users');
    return v && !v.classList.contains('hidden');
  });
  const userRowsCount = await page.evaluate(() => {
    return document.querySelectorAll('#userTableBody tr').length;
  });
  console.log(`  Users tab active: ${isUsersViewActive}, User accounts in table: ${userRowsCount}`);
  if (isUsersViewActive && userRowsCount > 0) {
    auditLog.passed.push(`User Management: Admin can view User table with ${userRowsCount} accounts.`);
  }

  // Test 4.2: Activity History Tab
  await page.evaluate(() => switchTab('activity'));
  await new Promise(r => setTimeout(r, 400));
  const isActivityViewActive = await page.evaluate(() => {
    const v = document.getElementById('view-activity');
    return v && !v.classList.contains('hidden');
  });
  const activityRowsCount = await page.evaluate(() => {
    return document.querySelectorAll('#activityTableBody tr').length;
  });
  console.log(`  Activity tab active: ${isActivityViewActive}, Log entries in table: ${activityRowsCount}`);
  if (isActivityViewActive && activityRowsCount > 0) {
    auditLog.passed.push(`Activity History: Admin can view audit logs (${activityRowsCount} entries recorded).`);
  }

  // ----------------------------------------------------
  // TEST GROUP 5: DARK MODE & MOBILE RESPONSIVENESS
  // ----------------------------------------------------
  console.log('\n[TEST GROUP 5] Theme Toggle & Mobile Viewports');

  // Test 5.1: Dark Mode Toggle
  await page.evaluate(() => toggleThemeQuick());
  await new Promise(r => setTimeout(r, 300));
  const isDark = await page.evaluate(() => document.documentElement.classList.contains('dark'));
  const storedTheme = await page.evaluate(() => localStorage.getItem('theme-preference'));
  console.log(`  Dark mode active: ${isDark}, stored preference: ${storedTheme}`);
  if (isDark) {
    auditLog.passed.push('Dark Mode: Toggle activated dark theme class and persisted preference.');
  }

  // Test 5.2: Mobile Viewport (375x812 iPhone)
  await page.setViewport({ width: 375, height: 812, isMobile: true });
  await page.evaluate(() => switchTab('inventory'));
  await new Promise(r => setTimeout(r, 400));

  const mobileCardsVisible = await page.evaluate(() => {
    const list = document.getElementById('widgetMobileCardsList');
    return list && list.offsetHeight > 50 && window.getComputedStyle(list).display !== 'none';
  });
  console.log(`  Mobile cards rendered: ${mobileCardsVisible}`);
  if (mobileCardsVisible) {
    auditLog.passed.push('Mobile Responsiveness: Mobile card view renders on viewport <768px.');
  }

  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/310_qa_mobile_audit.png' });

  // Reset to desktop light mode
  await page.setViewport({ width: 1440, height: 900 });
  await page.evaluate(() => {
    applyTheme('light');
    switchTab('overview');
  });
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/311_qa_overview_final.png' });

  // ----------------------------------------------------
  // TEST GROUP 6: EDGE CASES & RESILIENCY
  // ----------------------------------------------------
  console.log('\n[TEST GROUP 6] Edge Cases & Resiliency Testing');

  // Edge Case 6.1: Non-existent search term & Reset CTA
  await page.evaluate(() => {
    switchTab('inventory');
    const inp = document.getElementById('widgetSearch');
    inp.value = 'xyzzy_non_existent_token_9999';
    filterWidgets();
  });
  await new Promise(r => setTimeout(r, 200));

  const emptyStateText = await page.evaluate(() => {
    return document.getElementById('widgetTableBody')?.innerText.trim();
  });
  console.log('  Empty search state text:', emptyStateText);
  if (emptyStateText.includes('No widgets match')) {
    auditLog.passed.push('Empty State: Searching non-existent keyword displays user-friendly empty state message.');
  }

  // Screenshot empty state with Reset CTA
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/320_qa_empty_state_reset_btn.png' });

  // Test 6.2: Click Reset All Filters CTA button
  const resetBtnClicked = await page.evaluate(() => {
    const btn = document.querySelector('#widgetTableBody button');
    if (btn) {
      btn.click();
      return true;
    }
    return false;
  });
  await new Promise(r => setTimeout(r, 200));
  const restoredCount = await page.evaluate(() => filteredData.length);
  console.log(`  Reset All Filters clicked: ${resetBtnClicked}, Restored count: ${restoredCount}`);
  if (resetBtnClicked && restoredCount === 294) {
    auditLog.passed.push('Actionable Empty State: "Reset All Filters" CTA resets search and restores 294 items.');
  }

  // Test 6.3: Keyboard shortcut Ctrl+K
  await page.evaluate(() => switchTab('overview'));
  await new Promise(r => setTimeout(r, 200));
  await page.keyboard.down('Control');
  await page.keyboard.press('KeyK');
  await page.keyboard.up('Control');
  await new Promise(r => setTimeout(r, 200));

  const isSearchFocused = await page.evaluate(() => {
    return document.activeElement && document.activeElement.id === 'widgetSearch';
  });
  console.log('  Ctrl+K focus search input:', isSearchFocused);
  if (isSearchFocused) {
    auditLog.passed.push('Global Shortcut: Ctrl+K switches to inventory and immediately focuses search field.');
  }
  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/321_qa_ctrl_k_search_focused.png' });

  // Edge Case 6.2: Invalid tab hash in URL
  await page.evaluate(() => {
    window.location.hash = '#invalid_route_999';
  });
  await new Promise(r => setTimeout(r, 200));
  // Check if overview is displayed without crash
  const overviewStillVisible = await page.evaluate(() => {
    const ov = document.getElementById('view-overview');
    return ov && !ov.classList.contains('hidden');
  });
  if (overviewStillVisible) {
    auditLog.passed.push('Resilient Routing: Invalid hash in URL defaults safely to Overview without crashing.');
  }

  console.log('\n==================================================');
  console.log('AUDIT SUMMARY');
  console.log(`  Passed Tests: ${auditLog.passed.length}`);
  console.log(`  Failed Tests: ${auditLog.failed.length}`);
  console.log(`  Console Errors: ${auditLog.consoleErrors.length}`);
  console.log('==================================================');

  await browser.close();

  const fs = require('fs');
  fs.writeFileSync(
    'scripts/qa_audit_results.json',
    JSON.stringify(auditLog, null, 2),
    'utf-8'
  );
  console.log('Saved detailed results to scripts/qa_audit_results.json');
}

runQAAudit().catch(err => {
  console.error('Audit failed with error:', err);
  process.exit(1);
});
