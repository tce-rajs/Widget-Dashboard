#!/usr/bin/env python3
"""
Generate Minimal, Responsive "Widget Comparison" Dashboard
Specification-compliant generator.
"""

import os
import json
from datetime import datetime

# Sample data covering all permutations to match exact numbers:
# Total: 50 | Need attention: 7 | QA: 47 (94%) | Git: 46 (92%) | XL: 47 (94%)
SAMPLE_WIDGETS = [
    # 2 GAPS (Most gaps first)
    {
        "sn": 1,
        "name": "Cell Division (Mitosis)",
        "qa": True,
        "git": False,
        "xl": False,
        "rep_folder": "reports/cell-division",
        "link_web": "simulations/cell-division.html"
    },
    {
        "sn": 2,
        "name": "Acid Base Titration",
        "qa": False,
        "git": True,
        "xl": False,
        "rep_folder": "reports/acid-base-titration",
        "link_web": "simulations/acid-base-titration.html"
    },
    {
        "sn": 3,
        "name": "Pendulum Clock Harmonics",
        "qa": False,
        "git": False,
        "xl": True,
        "rep_folder": "reports/pendulum-clock",
        "link_web": "simulations/pendulum-clock.html"
    },
    # 1 GAP
    {
        "sn": 4,
        "name": "Flower (Plant Anatomy)",
        "qa": True,
        "git": False,
        "xl": True,
        "rep_folder": "reports/flower",
        "link_web": "simulations/flower.html"
    },
    {
        "sn": 5,
        "name": "Solar System & Planetary Orbits",
        "qa": True,
        "git": True,
        "xl": False,
        "rep_folder": "reports/solar-system",
        "link_web": "simulations/solar-system.html"
    },
    {
        "sn": 6,
        "name": "Wave Motion & Interference",
        "qa": False,
        "git": True,
        "xl": True,
        "rep_folder": "reports/wave-motion",
        "link_web": "simulations/wave-motion.html"
    },
    {
        "sn": 7,
        "name": "Friction & Gravity Simulation",
        "qa": True,
        "git": False,
        "xl": True,
        "rep_folder": "reports/friction-gravity",
        "link_web": "simulations/friction-gravity.html"
    },
]

# 43 Widgets present in all 3 sources (QA, Git, XL) -> 50 total
CURRICULUM_COMPLETE_NAMES = [
    "Electric Circuit Simulator", "Photosynthesis Engine", "Pythagorean Theorem Visualizer",
    "DNA Structure & Replication", "Periodic Table Interactive", "Optics & Light Refraction",
    "Magnetism & Field Lines", "Thermodynamics Heat Engine", "Kinetic & Potential Energy",
    "Ohm's Law Lab", "Chemical Bonding Simulator", "Digestive System Explorer",
    "Human Respiratory Cycle", "Sound Waves & Frequency", "Projectile Motion Trajectory",
    "Balancing Chemical Equations", "Hydraulic Lift & Pascal Law", "Electromagnetic Spectrum",
    "Bernoulli Principle Simulator", "Doppler Effect Acoustic Wave", "Archimedes Buoyancy Principle",
    "Resonance Tube Acoustics", "Capacitor Charge & Discharge", "Logic Gates Workbench",
    "Number Line Operations", "Fraction Multiplication Bar", "Graphic Inequalities Plane",
    "Quadratic Equation Parabola", "Trigonometric Unit Circle", "Coordinate Geometry Plotter",
    "Probability Dice & Coin Toss", "Linear Algebra Vector Field", "Calculus Derivative Slope",
    "Integral Area Under Curve", "Bar Graph & Histogram Builder", "Standard Deviation Bell Curve",
    "Matrix Multiplication Grid", "Complex Numbers Argand Plane", "Set Theory Venn Diagrams",
    "Logarithmic Scale Zoom", "Geometric Sequences Spiral", "Polynomial Factorization Tile",
    "Statistical Box Plot Explorer"
]

for idx, name in enumerate(CURRICULUM_COMPLETE_NAMES, start=8):
    slug = name.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("&", "and")
    SAMPLE_WIDGETS.append({
        "sn": idx,
        "name": name,
        "qa": True,
        "git": True,
        "xl": True,
        "rep_folder": f"reports/{slug}",
        "link_web": f"simulations/{slug}.html"
    })

def build_dashboard_html():
    now_str = datetime.now().strftime("%b %d, %Y · %I:%M %p")
    widgets_json = json.dumps(SAMPLE_WIDGETS, indent=2)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Widget Comparison</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    fontFamily: {{
                        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
                    }},
                    colors: {{
                        canvas: '#F7F8FA',
                        borderSubtle: '#E4E7EC',
                        borderStrong: '#D0D5DD',
                        alertRed: '#B42318',
                        alertRedBg: '#FEF3F2',
                        alertRedBorder: '#FECDCA',
                        successGreen: '#027A48',
                        textPrimary: '#101828',
                        textSecondary: '#475467',
                        textTertiary: '#667085',
                    }}
                }}
            }}
        }}
    </script>
    <style>
        body {{
            background-color: #F7F8FA;
            color: #101828;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            -webkit-font-smoothing: antialiased;
        }}
        /* Tooltip visibility handling */
        .metric-card .tooltip {{
            visibility: hidden;
            opacity: 0;
            transition: opacity 0.15s ease-in-out;
            pointer-events: none;
        }}
        .metric-card:hover .tooltip,
        .metric-card:focus .tooltip,
        .metric-card:focus-within .tooltip,
        .metric-card.active-tap .tooltip {{
            visibility: visible;
            opacity: 1;
        }}
        /* Focus state accessibility */
        .metric-card:focus-visible {{
            outline: 2px solid #101828;
            outline-offset: 2px;
        }}
        button:focus-visible, a:focus-visible {{
            outline: 2px solid #101828;
            outline-offset: 2px;
        }}
    </style>
</head>
<body class="min-h-screen py-8 sm:py-12 px-4 sm:px-6">

    <!-- Single Column Layout (max-w 1100px) -->
    <main class="w-full max-w-[1100px] mx-auto space-y-8">

        <!-- 1. Header (Title & Timestamp) -->
        <header class="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-1 pb-2 border-b border-borderSubtle">
            <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-textPrimary">Widget Comparison</h1>
            <p class="text-xs text-textTertiary font-normal" id="lastUpdatedLabel">Last updated: {now_str}</p>
        </header>

        <!-- 2. Row of Five Numbers (wraps on small screens) -->
        <section aria-label="Widget Metrics Overview" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
            
            <!-- 1. Total Widgets -->
            <div tabindex="0" 
                 role="region"
                 aria-label="Total Widgets: 50. Hover or focus for formula equation."
                 class="metric-card relative bg-white border border-borderSubtle rounded-xl p-4 sm:p-5 transition hover:border-borderStrong cursor-default">
                <span class="block text-[11px] font-semibold uppercase tracking-wider text-textTertiary">TOTAL WIDGETS</span>
                <span class="block text-2xl sm:text-3xl font-bold text-textPrimary mt-1.5" id="metricTotal">50</span>
                <span class="block text-xs text-textSecondary mt-1 truncate" id="subTotal">across QA, Git & XL</span>

                <!-- Dark Tooltip Equation -->
                <div role="tooltip" class="tooltip absolute z-30 bottom-full left-0 mb-2 w-64 sm:w-72 p-2.5 rounded-lg bg-[#101828] text-white text-xs font-mono shadow-xl border border-slate-700">
                    <p class="leading-relaxed">Total widgets = unique widgets found in at least one of QA, Git or XL</p>
                    <div class="absolute left-6 top-full -mt-1 border-4 border-transparent border-t-[#101828]"></div>
                </div>
            </div>

            <!-- 2. Need Attention (Red Number) -->
            <div tabindex="0" 
                 role="region"
                 aria-label="Need Attention: 7 widgets. Hover or focus for formula equation."
                 class="metric-card relative bg-white border border-borderSubtle rounded-xl p-4 sm:p-5 transition hover:border-borderStrong cursor-default">
                <span class="block text-[11px] font-semibold uppercase tracking-wider text-textTertiary">NEED ATTENTION</span>
                <span class="block text-2xl sm:text-3xl font-bold text-alertRed mt-1.5" id="metricAttention">7</span>
                <span class="block text-xs text-textSecondary mt-1 truncate" id="subAttention">of 50 widgets</span>

                <!-- Dark Tooltip Equation -->
                <div role="tooltip" class="tooltip absolute z-30 bottom-full left-0 mb-2 w-64 sm:w-80 p-2.5 rounded-lg bg-[#101828] text-white text-xs font-mono shadow-xl border border-slate-700">
                    <p class="leading-relaxed">Need attention = widgets missing from at least one source = 50 total − 43 in all three = 7</p>
                    <div class="absolute left-6 top-full -mt-1 border-4 border-transparent border-t-[#101828]"></div>
                </div>
            </div>

            <!-- 3. QA -->
            <div tabindex="0" 
                 role="region"
                 aria-label="QA Presence: 47 widgets, 94 percent coverage. Hover or focus for formula equation."
                 class="metric-card relative bg-white border border-borderSubtle rounded-xl p-4 sm:p-5 transition hover:border-borderStrong cursor-default">
                <span class="block text-[11px] font-semibold uppercase tracking-wider text-textTertiary">QA</span>
                <span class="block text-2xl sm:text-3xl font-bold text-textPrimary mt-1.5" id="metricQA">47</span>
                <span class="block text-xs text-textSecondary mt-1 truncate" id="subQA">present · 94%</span>

                <!-- Dark Tooltip Equation -->
                <div role="tooltip" class="tooltip absolute z-30 bottom-full left-0 sm:left-1/2 sm:-translate-x-1/2 mb-2 w-64 sm:w-72 p-2.5 rounded-lg bg-[#101828] text-white text-xs font-mono shadow-xl border border-slate-700">
                    <p class="leading-relaxed">QA coverage = found in QA ÷ total = 47 ÷ 50 = 94%</p>
                    <div class="absolute left-6 sm:left-1/2 sm:-translate-x-1/2 top-full -mt-1 border-4 border-transparent border-t-[#101828]"></div>
                </div>
            </div>

            <!-- 4. Git -->
            <div tabindex="0" 
                 role="region"
                 aria-label="Git Presence: 46 widgets, 92 percent coverage. Hover or focus for formula equation."
                 class="metric-card relative bg-white border border-borderSubtle rounded-xl p-4 sm:p-5 transition hover:border-borderStrong cursor-default">
                <span class="block text-[11px] font-semibold uppercase tracking-wider text-textTertiary">GIT</span>
                <span class="block text-2xl sm:text-3xl font-bold text-textPrimary mt-1.5" id="metricGit">46</span>
                <span class="block text-xs text-textSecondary mt-1 truncate" id="subGit">present · 92%</span>

                <!-- Dark Tooltip Equation (kept safely inside viewport on right edge) -->
                <div role="tooltip" class="tooltip absolute z-30 bottom-full right-0 sm:right-auto sm:left-1/2 sm:-translate-x-1/2 mb-2 w-64 sm:w-72 p-2.5 rounded-lg bg-[#101828] text-white text-xs font-mono shadow-xl border border-slate-700">
                    <p class="leading-relaxed">Git coverage = 46 ÷ 50 = 92%</p>
                    <div class="absolute right-6 sm:right-auto sm:left-1/2 sm:-translate-x-1/2 top-full -mt-1 border-4 border-transparent border-t-[#101828]"></div>
                </div>
            </div>

            <!-- 5. XL -->
            <div tabindex="0" 
                 role="region"
                 aria-label="Excel Presence: 47 widgets, 94 percent coverage. Hover or focus for formula equation."
                 class="metric-card relative bg-white border border-borderSubtle rounded-xl p-4 sm:p-5 transition hover:border-borderStrong cursor-default col-span-2 sm:col-span-1">
                <span class="block text-[11px] font-semibold uppercase tracking-wider text-textTertiary">XL</span>
                <span class="block text-2xl sm:text-3xl font-bold text-textPrimary mt-1.5" id="metricXL">47</span>
                <span class="block text-xs text-textSecondary mt-1 truncate" id="subXL">present · 94%</span>

                <!-- Dark Tooltip Equation (aligned right to prevent screen overflow) -->
                <div role="tooltip" class="tooltip absolute z-30 bottom-full right-0 mb-2 w-64 sm:w-72 p-2.5 rounded-lg bg-[#101828] text-white text-xs font-mono shadow-xl border border-slate-700">
                    <p class="leading-relaxed">XL coverage = 47 ÷ 50 = 94%</p>
                    <div class="absolute right-6 top-full -mt-1 border-4 border-transparent border-t-[#101828]"></div>
                </div>
            </div>

        </section>

        <!-- 3. Toggle Control (44px min tap target) -->
        <section aria-label="Filter Controls" class="flex items-center">
            <div class="inline-flex p-1 bg-white border border-borderSubtle rounded-xl shadow-xs" role="tablist" aria-label="Widget View Filter">
                <button type="button" 
                        role="tab"
                        aria-selected="true"
                        id="toggleAttention" 
                        onclick="setFilter('attention')"
                        class="min-h-[44px] px-5 text-xs font-semibold rounded-lg transition transition-colors bg-[#101828] text-white flex items-center justify-center cursor-pointer select-none">
                    Needs attention (<span id="btnAttentionCount">7</span>)
                </button>
                <button type="button" 
                        role="tab"
                        aria-selected="false"
                        id="toggleAll" 
                        onclick="setFilter('all')"
                        class="min-h-[44px] px-5 text-xs font-medium rounded-lg transition transition-colors text-textSecondary hover:text-textPrimary flex items-center justify-center cursor-pointer select-none">
                    All (<span id="btnAllCount">50</span>)
                </button>
            </div>
        </section>

        <!-- 4. Table Container (horizontally scrollable on narrow screens) -->
        <section aria-label="Widget Comparison Table" class="space-y-3">
            <div class="overflow-x-auto bg-white border border-borderSubtle rounded-xl shadow-xs">
                <table class="w-full text-left border-collapse min-w-[700px]">
                    <thead>
                        <tr class="border-b border-borderSubtle bg-[#FAFAFC] text-[11px] font-semibold text-textTertiary tracking-wider">
                            <th scope="col" class="py-3.5 px-4 w-14 text-center">SN</th>
                            <th scope="col" class="py-3.5 px-4">
                                <span class="block text-textPrimary">IWN</span>
                                <span class="block text-[10px] font-normal text-textTertiary lowercase first-letter:uppercase">Widget name</span>
                            </th>
                            <th scope="col" class="py-3.5 px-4 w-28 text-center">
                                <span class="block text-textPrimary">QA</span>
                                <span class="block text-[10px] font-normal text-textTertiary lowercase first-letter:uppercase">In QA</span>
                            </th>
                            <th scope="col" class="py-3.5 px-4 w-28 text-center">
                                <span class="block text-textPrimary">GIT</span>
                                <span class="block text-[10px] font-normal text-textTertiary lowercase first-letter:uppercase">In Git</span>
                            </th>
                            <th scope="col" class="py-3.5 px-4 w-28 text-center">
                                <span class="block text-textPrimary">XL</span>
                                <span class="block text-[10px] font-normal text-textTertiary lowercase first-letter:uppercase">In Excel</span>
                            </th>
                            <th scope="col" class="py-3.5 px-4 w-24 text-center">
                                <span class="block text-textPrimary">REP FOLDER</span>
                                <span class="block text-[10px] font-normal text-textTertiary lowercase first-letter:uppercase">Report folder</span>
                            </th>
                            <th scope="col" class="py-3.5 px-4 w-24 text-center">
                                <span class="block text-textPrimary">LINK WEB</span>
                                <span class="block text-[10px] font-normal text-textTertiary lowercase first-letter:uppercase">Web link</span>
                            </th>
                        </tr>
                    </thead>
                    <tbody id="widgetTableBody" class="divide-y divide-borderSubtle text-xs text-textPrimary font-medium">
                        <!-- Populated by JavaScript -->
                    </tbody>
                </table>
            </div>

            <!-- Footnote / Caption -->
            <footer class="flex items-center justify-between text-[11px] text-textTertiary px-1 pt-1">
                <p>Sample data: 7 of 50 widgets need attention across QA, Git, and Excel sources. Sorted with most gaps first.</p>
                <p id="tableRowsCount">Showing 7 rows</p>
            </footer>
        </section>

    </main>

    <!-- Client-Side Engine -->
    <script>
        // Master widget dataset (Structured for live pipeline integration)
        const RAW_WIDGETS = {widgets_json};

        // Active state
        let currentFilter = 'attention'; // 'attention' | 'all'

        // Count missing gaps for sorting (most gaps come first)
        function getGapCount(item) {{
            let gaps = 0;
            if (!item.qa) gaps++;
            if (!item.git) gaps++;
            if (!item.xl) gaps++;
            return gaps;
        }}

        // Render table rows based on active filter
        function renderTable() {{
            const tbody = document.getElementById('widgetTableBody');
            tbody.innerHTML = '';

            // Filter
            let list = RAW_WIDGETS.slice();
            if (currentFilter === 'attention') {{
                list = list.filter(w => getGapCount(w) > 0);
            }}

            // Sort: widgets with the most gaps come first
            list.sort((a, b) => {{
                const gapDiff = getGapCount(b) - getGapCount(a);
                if (gapDiff !== 0) return gapDiff;
                return a.sn - b.sn;
            }});

            // Build rows
            list.forEach((item, index) => {{
                const tr = document.createElement('tr');
                tr.className = "hover:bg-[#F9FAFB] transition-colors";

                // Cell QA
                const qaCell = renderSourceCell(item.qa);
                // Cell Git
                const gitCell = renderSourceCell(item.git);
                // Cell XL
                const xlCell = renderSourceCell(item.xl);

                tr.innerHTML = `
                    <td class="py-3 px-4 text-center text-textTertiary font-mono text-[11px]">${{item.sn}}</td>
                    <td class="py-3 px-4 font-semibold text-textPrimary">${{escapeHtml(item.name)}}</td>
                    <td class="py-3 px-4 text-center ${{item.qa ? '' : 'bg-alertRedBg'}}">${{qaCell}}</td>
                    <td class="py-3 px-4 text-center ${{item.git ? '' : 'bg-alertRedBg'}}">${{gitCell}}</td>
                    <td class="py-3 px-4 text-center ${{item.xl ? '' : 'bg-alertRedBg'}}">${{xlCell}}</td>
                    <td class="py-2.5 px-4 text-center">
                        <button type="button" 
                                onclick="openReportFolder('${{escapeHtml(item.name)}}', '${{item.rep_folder}}')"
                                aria-label="Open report folder for ${{escapeHtml(item.name)}}"
                                title="Open report folder for ${{escapeHtml(item.name)}}"
                                class="inline-flex items-center justify-center w-11 h-11 rounded-lg border border-borderStrong bg-white hover:bg-slate-50 text-textSecondary hover:text-textPrimary transition cursor-pointer">
                            <i data-lucide="folder" class="w-4 h-4"></i>
                        </button>
                    </td>
                    <td class="py-2.5 px-4 text-center">
                        <a href="${{item.link_web}}" 
                           target="_blank" 
                           rel="noopener noreferrer"
                           aria-label="Open web link for ${{escapeHtml(item.name)}}"
                           title="Open web link for ${{escapeHtml(item.name)}}"
                           class="inline-flex items-center justify-center w-11 h-11 rounded-lg border border-borderStrong bg-white hover:bg-slate-50 text-textSecondary hover:text-textPrimary transition cursor-pointer">
                            <i data-lucide="external-link" class="w-4 h-4"></i>
                        </a>
                    </td>
                `;
                tbody.appendChild(tr);
            }});

            document.getElementById('tableRowsCount').textContent = `Showing ${{list.length}} of ${{RAW_WIDGETS.length}} widgets`;
            lucide.createIcons();
        }}

        // Render QA / Git / XL cell contents with icon + text
        function renderSourceCell(isPresent) {{
            if (isPresent) {{
                return `
                    <div class="inline-flex items-center gap-1.5 text-successGreen text-xs font-medium">
                        <i data-lucide="check" class="w-4 h-4 stroke-[2.5]"></i>
                        <span>Present</span>
                    </div>
                `;
            }} else {{
                return `
                    <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-alertRed text-white text-[11px] font-semibold tracking-wide">
                        <i data-lucide="x" class="w-3.5 h-3.5 stroke-[2.5]"></i>
                        <span>Missing</span>
                    </span>
                `;
            }}
        }}

        // Toggle filter view
        function setFilter(filterType) {{
            currentFilter = filterType;
            const btnAttention = document.getElementById('toggleAttention');
            const btnAll = document.getElementById('toggleAll');

            if (filterType === 'attention') {{
                btnAttention.className = "min-h-[44px] px-5 text-xs font-semibold rounded-lg transition transition-colors bg-[#101828] text-white flex items-center justify-center cursor-pointer select-none";
                btnAttention.setAttribute('aria-selected', 'true');
                btnAll.className = "min-h-[44px] px-5 text-xs font-medium rounded-lg transition transition-colors text-textSecondary hover:text-textPrimary flex items-center justify-center cursor-pointer select-none";
                btnAll.setAttribute('aria-selected', 'false');
            }} else {{
                btnAll.className = "min-h-[44px] px-5 text-xs font-semibold rounded-lg transition transition-colors bg-[#101828] text-white flex items-center justify-center cursor-pointer select-none";
                btnAll.setAttribute('aria-selected', 'true');
                btnAttention.className = "min-h-[44px] px-5 text-xs font-medium rounded-lg transition transition-colors text-textSecondary hover:text-textPrimary flex items-center justify-center cursor-pointer select-none";
                btnAttention.setAttribute('aria-selected', 'false');
            }}

            renderTable();
        }}

        // Simple action handler for folder button
        function openReportFolder(name, folderPath) {{
            alert(`Report Folder: ${{folderPath}}\\n(IWN: ${{name}})`);
        }}

        // Tap toggle support for mobile tooltips
        document.querySelectorAll('.metric-card').forEach(card => {{
            card.addEventListener('click', (e) => {{
                document.querySelectorAll('.metric-card').forEach(c => {{
                    if (c !== card) c.classList.remove('active-tap');
                }});
                card.classList.toggle('active-tap');
            }});
        }});
        document.addEventListener('click', (e) => {{
            if (!e.target.closest('.metric-card')) {{
                document.querySelectorAll('.metric-card').forEach(c => c.classList.remove('active-tap'));
            }}
        }});

        // Utility: HTML escape
        function escapeHtml(str) {{
            if (!str) return '';
            return str
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }}

        // Initial setup
        window.addEventListener('DOMContentLoaded', () => {{
            renderTable();
            lucide.createIcons();
        }});
    </script>
</body>
</html>
"""
    return html

def generate():
    html = build_dashboard_html()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_index = os.path.join(base_dir, "index.html")
    out_comp = os.path.join(base_dir, "widget-comparison.html")
    with open(out_index, "w", encoding="utf-8") as f:
        f.write(html)
    with open(out_comp, "w", encoding="utf-8") as f:
        f.write(html)
    print("Successfully generated minimal Widget Comparison dashboard in index.html and widget-comparison.html!")

if __name__ == "__main__":
    generate()
