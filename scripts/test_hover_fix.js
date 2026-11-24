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

    // Replace tooltip innerHTML and classes on Card 1
    const tooltip = document.querySelector('#card-kpi-total .backdrop-blur-md');
    tooltip.className = 'pointer-events-none absolute top-full left-1/2 -translate-x-1/2 mt-1.5 w-60 px-3 py-2 bg-slate-900/95 dark:bg-slate-950/95 text-white text-xs rounded-xl shadow-2xl opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-all duration-150 z-50 border border-slate-700/80 backdrop-blur-md';
    tooltip.innerHTML = `
      <div class="flex items-center justify-between pb-1 border-b border-slate-800 text-[11px]">
          <span class="font-bold text-slate-200 flex items-center gap-1.5">
              <span>Total Assets Calculation</span>
          </span>
          <span class="font-mono font-bold text-blue-400 text-[11px]">340</span>
      </div>
      <div class="mt-1.5 flex items-center justify-between text-[11px] font-mono px-0.5">
          <span class="text-blue-300 font-semibold">294 Scope</span>
          <span class="text-slate-400">+</span>
          <span class="text-purple-300 font-semibold">46 Extra</span>
          <span class="text-slate-400">=</span>
          <span class="text-emerald-400 font-bold">340 Total</span>
      </div>
    `;
  });

  await page.hover('#card-kpi-total');
  await new Promise(r => setTimeout(r, 600));

  const rect = await page.evaluate(() => {
    const tooltip = document.querySelector('#card-kpi-total .backdrop-blur-md');
    const r = tooltip.getBoundingClientRect();
    const canvas = document.getElementById('reconciliationDonutChart').getBoundingClientRect();
    return {
      tooltip: { top: r.top, bottom: r.bottom, height: r.height },
      canvas: { top: canvas.top },
      gapToCanvas: canvas.top - r.bottom
    };
  });
  console.log('Metrics with sleek single-equation row:', rect);

  await page.screenshot({ path: 'C:/Users/v_CrystalQA3/.gemini/antigravity/brain/f3079d64-eabf-438b-bac4-f5596cf2bcbd/screenshots/385_sleek_formula_preview.png' });
  await browser.close();
})();
