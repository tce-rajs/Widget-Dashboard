const puppeteer = require('C:/Users/v_CrystalQA3/AppData/Roaming/npm/node_modules/puppeteer-core');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 950 });

  await page.goto('http://localhost:8000/login.html', { waitUntil: 'networkidle2' });
  await page.evaluate(() => authManager.login('admin@company.com', 'Admin@123', true));
  await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle2' });

  // Enable Dark Mode
  await page.evaluate(() => {
    document.documentElement.classList.add('dark');
    localStorage.setItem('theme', 'dark');

    // Replace Card 5 tooltip
    const tooltip = document.querySelector('#card-kpi-git .backdrop-blur-md');
    tooltip.className = 'pointer-events-none absolute top-full right-0 mt-1.5 w-80 px-3.5 py-2.5 bg-slate-900/95 dark:bg-slate-950/95 text-white text-xs rounded-xl shadow-2xl opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-all duration-150 z-50 border border-slate-700/80 backdrop-blur-md';
    tooltip.innerHTML = `
      <div class="flex items-center justify-between pb-1.5 border-b border-slate-800 text-[11px]">
          <span class="font-bold text-purple-300 flex items-center gap-1.5">
              <span>Extra in Repo Calculation</span>
          </span>
          <span class="font-mono font-bold text-purple-400 text-[11px]">+46 Extra</span>
      </div>
      <div class="mt-1.5 space-y-1.5 text-[10px] font-mono">
          <div class="flex items-center justify-between text-[11px]">
              <span class="text-blue-300 font-semibold">340 Total Assets</span>
              <span class="text-slate-400">−</span>
              <span class="text-indigo-300 font-semibold">294 Scope</span>
              <span class="text-slate-400">=</span>
              <span class="text-purple-400 font-bold">+46 Extra</span>
          </div>
          <div class="flex items-center justify-between text-[10.5px] text-slate-300 border-t border-slate-800/80 pt-1">
              <span class="text-purple-300 font-semibold">319 in Repo</span>
              <span class="text-slate-400">−</span>
              <span class="text-indigo-300 font-semibold">273 in Scope</span>
              <span class="text-slate-400">=</span>
              <span class="text-purple-400 font-bold">+46 Extra</span>
          </div>
          <div class="flex items-center justify-between text-[10px] border-t border-slate-800/80 pt-1 text-slate-400">
              <span>QA Reconciliation:</span>
              <span class="text-emerald-400 font-semibold">13 in QA</span>
              <span class="text-slate-500">+</span>
              <span class="text-slate-300 font-semibold">33 Git Only</span>
              <span class="text-slate-500">=</span>
              <span class="text-purple-300 font-bold">+46</span>
          </div>
      </div>
    `;
  });

  await page.hover('#card-kpi-git');
  await new Promise(r => setTimeout(r, 600));

  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/397_card5_ultimate_formula.png' });
  await browser.close();
  console.log('Captured 397_card5_ultimate_formula.png');
})();
