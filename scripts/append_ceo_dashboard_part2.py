# Append Part 2 to build_ceo_dashboard.py
import os

part2_code = r'''
with open(output_path, 'a', encoding='utf-8') as f:
    f.write(r"""
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CEO Executive Dashboard – Widget Reconciliation & Business Analysis</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📊</text></svg>">
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <!-- SheetJS for Client-Side Excel Auto-Parsing & Drag-and-Drop -->
    <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
    <!-- Auth & Activity Manager -->
    <script src="auth.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
                        mono: ['"JetBrains Mono"', 'monospace'],
                    }
                }
            }
        }
    </script>
    <style>
        :root {
            --bg-page: #f8fafc;
            --bg-card: #ffffff;
            --bg-subtle: #f1f5f9;
            --border-color: #e2e8f0;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --text-soft: #475569;
        }
        .dark {
            --bg-page: #090d16;
            --bg-card: #0f1626;
            --bg-subtle: #151f33;
            --border-color: #1e2c44;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --text-soft: #cbd5e1;
        }
        body {
            background-color: var(--bg-page);
            color: var(--text-main);
            font-family: 'Inter', -apple-system, sans-serif;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            transition: background-color 0.2s cubic-bezier(0.4, 0, 0.2, 1), color 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .app-card {
            background-color: var(--bg-card);
            border-color: var(--border-color);
            transition: background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, transform 0.15s ease;
        }
        .app-subtle {
            background-color: var(--bg-subtle);
            border-color: var(--border-color);
            transition: background-color 0.2s ease, border-color 0.2s ease;
        }
        
        .dark .app-card {
            background-color: #0f1626;
            border-color: #1e2c44;
            box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.55);
        }
        .dark .app-subtle {
            background-color: #141d30;
            border-color: #202e48;
        }
        .dark .app-subtle:hover {
            background-color: #1a263d;
            border-color: #2a3c5d;
        }
        
        .dark header {
            background-color: rgba(13, 19, 32, 0.94) !important;
            border-bottom-color: #1e2c44 !important;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
        }

        .dark .kpi-card {
            background: linear-gradient(180deg, #111a2d 0%, #0c1322 100%);
            border: 1px solid #1e2c44;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.5);
            transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .dark .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 30px -4px rgba(0, 0, 0, 0.75);
        }

        .dark thead {
            background-color: #121b2d !important;
            border-bottom-color: #202e48 !important;
        }
        .dark thead th {
            color: #94a3b8 !important;
            background-color: #121b2d !important;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.05em;
        }
        .dark tbody tr {
            border-color: #162237 !important;
            transition: background-color 0.15s ease;
        }
        .dark tbody tr:nth-child(even) {
            background-color: rgba(18, 26, 43, 0.35);
        }
        .dark tbody tr:hover {
            background-color: rgba(59, 130, 246, 0.1) !important;
        }

        .dark input, .dark select, .dark textarea {
            background-color: #0b111e !important;
            border-color: #22324c !important;
            color: #f8fafc !important;
        }
        .dark select option, .dark select optgroup {
            background-color: #0f1626 !important;
            color: #f8fafc !important;
        }
        .dark input:focus, .dark select:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.35) !important;
        }

        .custom-scroll::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        .custom-scroll::-webkit-scrollbar-track {
            background: transparent;
        }
        .custom-scroll::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 4px;
        }
        .dark .custom-scroll::-webkit-scrollbar-thumb {
            background: #253550;
        }
    </style>
</head>
<body class="min-h-screen flex flex-col transition-colors duration-200">

    <!-- Top Executive Header -->
    <header class="app-card border-b sticky top-0 z-30 transition-colors">
        <div class="max-w-7xl mx-auto px-4 sm:px-6">
            
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center gap-3">
                    <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center font-bold shadow-md shadow-blue-500/20">
                        <i data-lucide="bar-chart-3" class="w-5 h-5"></i>
                    </div>
                    <div>
                        <div class="flex items-center gap-2">
                            <h1 class="text-base sm:text-lg font-bold text-slate-900 dark:text-white tracking-tight">
                                CEO Executive Dashboard
                            </h1>
                            <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                                100% Reconciled
                            </span>
                        </div>
                        <p class="text-[11px] text-slate-500 dark:text-slate-400 hidden sm:block">
                            Widget Reconciliation, Codebase Audit & Business Readiness Across Excel, Repo & QA
                        </p>
                    </div>
                </div>

                <div class="flex items-center gap-2 sm:gap-2.5">
                    
                    <!-- Export Executive Brief Button -->
                    <button onclick="openCeoReportModal()" class="px-3 py-1.5 rounded-lg border border-blue-500/30 bg-blue-500/10 hover:bg-blue-500/20 text-blue-600 dark:text-blue-400 text-xs font-semibold transition shadow-sm cursor-pointer flex items-center gap-1.5">
                        <i data-lucide="file-text" class="w-3.5 h-3.5"></i>
                        <span>Export Executive Brief</span>
                    </button>

                    <!-- User Profile Pill (if logged in) -->
                    <div id="userProfilePill" class="app-subtle border rounded-lg px-2.5 py-1 text-xs items-center gap-2 hidden">
                        <div class="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-[10px]" id="userAvatar">A</div>
                        <div class="hidden sm:block text-left leading-tight">
                            <div class="font-semibold text-slate-900 dark:text-white truncate max-w-[120px]" id="userNameDisplay">User</div>
                            <div class="text-[10px] text-slate-500 uppercase tracking-wider" id="userRoleBadge">Role</div>
                        </div>
                        <button onclick="handleLogout()" title="Log out of your session" class="text-slate-400 hover:text-rose-500 transition p-1">
                            <i data-lucide="log-out" class="w-3.5 h-3.5"></i>
                        </button>
                    </div>

                    <!-- Theme Toggle -->
                    <button type="button" onclick="toggleThemeQuick()" id="quickThemeBtn" title="Toggle Dark/Light Mode" class="w-8 h-8 rounded-lg border border-slate-300 dark:border-slate-700/80 bg-slate-100 dark:bg-slate-800/40 hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 transition flex items-center justify-center cursor-pointer shadow-sm">
                        <i data-lucide="moon" id="quickThemeIcon" class="w-4 h-4"></i>
                    </button>

                    <!-- Update Excel Button with Hover Dropdown Popover -->
                    <div class="relative group" id="updateExcelContainer">
                        <button type="button" class="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700/80 bg-slate-100 dark:bg-slate-800/40 hover:bg-slate-200 dark:hover:bg-slate-800 text-xs font-medium text-slate-800 dark:text-slate-200 transition shadow-sm cursor-pointer">
                            Update Excel
                        </button>

                        <div class="absolute right-0 top-full pt-2 w-80 sm:w-96 hidden group-hover:block hover:block focus-within:block z-50 transition-all duration-200 drop-shadow-2xl">
                            <div class="app-card border rounded-2xl p-4 shadow-2xl space-y-3.5 bg-white dark:bg-[#111622] border-slate-200 dark:border-slate-800">
                                <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80 pb-2.5">
                                    <div class="flex items-center gap-2">
                                        <div class="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
                                            <i data-lucide="upload-cloud" class="w-4 h-4"></i>
                                        </div>
                                        <div>
                                            <div class="text-xs font-bold text-slate-900 dark:text-white">Update Spreadsheet</div>
                                            <div class="text-[10px] text-slate-500 dark:text-slate-400">Recalculate dashboard live</div>
                                        </div>
                                    </div>
                                    <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 font-semibold">
                                        Live Sync
                                    </span>
                                </div>

                                <div id="dropZoneCard" onclick="document.getElementById('excelFileInput').click()" class="border-2 border-dashed border-blue-500/40 hover:border-blue-500 dark:border-blue-500/30 dark:hover:border-blue-400 rounded-xl p-4 bg-gradient-to-b from-blue-500/[0.04] to-transparent cursor-pointer transition text-center group/drop">
                                    <input type="file" id="excelFileInput" accept=".xlsx, .xls" class="hidden" onchange="handleExcelFileUpload(event)" />
                                    <div class="w-10 h-10 mx-auto rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center mb-2 group-hover/drop:scale-110 transition shadow-sm">
                                        <i data-lucide="file-up" class="w-5 h-5"></i>
                                    </div>
                                    <div class="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover/drop:text-blue-600 dark:group-hover/drop:text-blue-400 transition-colors">
                                        Drag & Drop Updated Excel Here
                                    </div>
                                    <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                                        or <span class="text-blue-600 dark:text-blue-400 font-medium underline">browse file from computer</span>
                                    </p>
                                </div>

                                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800/80 text-[11px] space-y-1.5">
                                    <div class="flex items-center justify-between text-slate-500 dark:text-slate-400 text-[10px] uppercase font-semibold tracking-wider">
                                        <span>Current Active Sheet</span>
                                        <span class="text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1">
                                            <i data-lucide="check" class="w-3 h-3"></i> Loaded
                                        </span>
                                    </div>
                                    <div class="font-mono text-xs font-medium text-slate-800 dark:text-slate-200 truncate" id="activeExcelNamePopover">
                                        {excel_filename}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Export CSV Button -->
                    <button onclick="exportCSV()" class="px-3.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700/80 bg-slate-100 dark:bg-slate-800/40 hover:bg-slate-200 dark:hover:bg-slate-800 text-xs font-medium text-slate-800 dark:text-slate-200 transition shadow-sm cursor-pointer">
                        Export CSV
                    </button>
                </div>
            </div>

            <!-- Navigation Tabs -->
            <div class="flex items-center gap-6 sm:gap-8 -mb-px pt-1 text-sm overflow-x-auto custom-scroll">
                <button onclick="switchTab('overview')" id="tab-overview" class="nav-tab pb-2.5 font-medium border-b-2 border-blue-500 text-blue-500 dark:text-blue-400 transition whitespace-nowrap">
                    Overview
                </button>
                <button onclick="drillDown('all')" id="tab-inventory" class="nav-tab pb-2.5 font-medium border-b-2 border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition whitespace-nowrap">
                    All Widgets ( <span id="nav-tab-total">{total_count}</span> )
                </button>
                <button onclick="switchTab('docs')" id="tab-docs" class="nav-tab pb-2.5 font-medium border-b-2 border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition whitespace-nowrap">
                    Documentation
                </button>

                <!-- Admin Tabs -->
                <button onclick="switchTab('users')" id="tab-users" class="nav-tab pb-2.5 font-medium border-b-2 border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition whitespace-nowrap hidden">
                    User Management
                </button>
                <button onclick="switchTab('activity')" id="tab-activity" class="nav-tab pb-2.5 font-medium border-b-2 border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition whitespace-nowrap hidden">
                    Activity History
                </button>
            </div>

        </div>
    </header>

    <!-- Main Container -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">

        <!-- File Protocol Banner -->
        <div id="localFileBanner" class="hidden p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-800 dark:text-amber-300 flex items-center justify-between gap-3 shadow-sm">
            <div class="flex items-center gap-2.5 min-w-0">
                <i data-lucide="info" class="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0"></i>
                <span>Browsing via <code>file://</code> protocol. Launching interactive simulations with audio & JSON works best on a local server. Run <strong>run_local_dashboard.bat</strong> for full HTTP server mode.</span>
            </div>
            <button type="button" onclick="document.getElementById('localFileBanner').classList.add('hidden')" class="p-1 rounded text-amber-600 dark:text-amber-400 hover:bg-amber-500/20 shrink-0">
                <i data-lucide="x" class="w-4 h-4"></i>
            </button>
        </div>

        <!-- ======================================================== -->
        <!-- SECTION 1: CEO EXECUTIVE OVERVIEW                        -->
        <!-- ======================================================== -->
        <div id="view-overview" class="view-content space-y-6">

            <!-- 1. 30-Second Executive Summary Callout Box -->
            <div class="app-card border border-blue-500/30 rounded-2xl p-5 sm:p-6 shadow-sm bg-gradient-to-r from-blue-500/[0.05] via-indigo-500/[0.03] to-emerald-500/[0.05]">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200/80 dark:border-slate-800 pb-3 mb-4">
                    <div class="flex items-center gap-2.5">
                        <div class="w-8 h-8 rounded-lg bg-blue-500/15 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
                            <i data-lucide="sparkles" class="w-4 h-4"></i>
                        </div>
                        <div>
                            <h2 class="text-sm sm:text-base font-bold text-slate-900 dark:text-white">
                                30-Second Executive Briefing: Complete Widget Ecosystem at a Glance
                            </h2>
                            <p class="text-xs text-slate-500 dark:text-slate-400">
                                Definitive cross-source audit answering 5 core leadership questions across Excel, Repository Codebase, and QA.
                            </p>
                        </div>
                    </div>
                    <div class="flex items-center gap-2 self-start sm:self-auto">
                        <span class="text-[11px] font-mono px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 font-semibold">
                            Production Readiness: 87.8%
                        </span>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-5 gap-3.5 text-xs">
                    <!-- Q1 -->
                    <div class="p-3 rounded-xl bg-white/70 dark:bg-slate-900/60 border border-slate-200/70 dark:border-slate-800 space-y-1">
                        <div class="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider">1. Expected Scope</div>
                        <div class="text-base font-bold text-slate-900 dark:text-white">{total_count} Widgets</div>
                        <p class="text-[11px] text-slate-600 dark:text-slate-400 leading-snug">
                            Master curriculum requirements across 15 subject strands agreed between Content and Dev.
                        </p>
                    </div>

                    <!-- Q2 -->
                    <div class="p-3 rounded-xl bg-white/70 dark:bg-slate-900/60 border border-slate-200/70 dark:border-slate-800 space-y-1">
                        <div class="text-[10px] font-bold text-teal-600 dark:text-teal-400 uppercase tracking-wider">2. Dev Progress</div>
                        <div class="text-base font-bold text-teal-600 dark:text-teal-400">{present_both_count} / {total_count} ({dev_coverage_pct})</div>
                        <p class="text-[11px] text-slate-600 dark:text-slate-400 leading-snug">
                            Verified on disk (+{extra_repo_count} bonus standalone simulations = <strong>{total_runnable_assets}</strong> runnable assets).
                        </p>
                    </div>

                    <!-- Q3 -->
                    <div class="p-3 rounded-xl bg-white/70 dark:bg-slate-900/60 border border-slate-200/70 dark:border-slate-800 space-y-1">
                        <div class="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">3. QA Availability</div>
                        <div class="text-base font-bold text-emerald-600 dark:text-emerald-400">{matched_all_count} / {total_count} ({qa_coverage_pct})</div>
                        <p class="text-[11px] text-slate-600 dark:text-slate-400 leading-snug">
                            Validated in Gold QA Catalog ({qa_tool_count} total registered tool profiles).
                        </p>
                    </div>

                    <!-- Q4 -->
                    <div class="p-3 rounded-xl bg-white/70 dark:bg-slate-900/60 border border-slate-200/70 dark:border-slate-800 space-y-1">
                        <div class="text-[10px] font-bold text-rose-600 dark:text-rose-400 uppercase tracking-wider">4. Critical Gaps</div>
                        <div class="text-base font-bold text-rose-600 dark:text-rose-400">{pending_dev_count} Dev + {missing_qa_count} QA</div>
                        <p class="text-[11px] text-slate-600 dark:text-slate-400 leading-snug">
                            12 net-new dev backlog; 15 finished widgets on disk missing from QA registry; 9 canvas tools.
                        </p>
                    </div>

                    <!-- Q5 -->
                    <div class="p-3 rounded-xl bg-white/70 dark:bg-slate-900/60 border border-slate-200/70 dark:border-slate-800 space-y-1">
                        <div class="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">5. Priority Actions</div>
                        <div class="text-base font-bold text-indigo-600 dark:text-indigo-400">Sprint Staffing</div>
                        <p class="text-[11px] text-slate-600 dark:text-slate-400 leading-snug">
                            Staff 12 backlog simulations; ingest 15 finished widgets into QA; adopt 46 bonus simulations.
                        </p>
                    </div>
                </div>
            </div>

            <!-- 2. Top 6 Executive KPI Cards -->
            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                
                <!-- KPI 1: Expected Widgets -->
                <div id="card-kpi-total" onclick="drillDown('all')" class="kpi-card app-card border border-t-[3px] border-t-blue-500 rounded-xl p-3.5 cursor-pointer transition hover:border-blue-500 group shadow-sm hover:shadow-md hover:-translate-y-0.5 duration-200" title="Click to view all 294 required widgets in All Widgets">
                    <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                        <span class="font-semibold text-slate-700 dark:text-slate-300 group-hover:text-blue-600 dark:group-hover:text-blue-400 truncate">Expected Widgets</span>
                        <i data-lucide="file-spreadsheet" class="w-3.5 h-3.5 text-blue-500 shrink-0"></i>
                    </div>
                    <div class="text-2xl font-bold text-slate-900 dark:text-white flex items-baseline gap-1">
                        <span>{total_count}</span>
                        <span class="text-[11px] font-normal text-slate-400">Required</span>
                    </div>
                    <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-1 truncate">
                        <span>100% Curriculum Scope</span>
                    </div>
                </div>

                <!-- KPI 2: Developed in Repo -->
                <div id="card-kpi-present" onclick="drillDown('source_present')" class="kpi-card app-card border border-t-[3px] border-t-teal-500 rounded-xl p-3.5 cursor-pointer transition hover:border-teal-500 group shadow-sm hover:shadow-md hover:-translate-y-0.5 duration-200" title="Click to filter 273 widgets verified in repository">
                    <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                        <span class="font-semibold text-teal-700 dark:text-teal-400 group-hover:text-teal-500 truncate">Developed in Repo</span>
                        <i data-lucide="folder-check" class="w-3.5 h-3.5 text-teal-500 shrink-0"></i>
                    </div>
                    <div class="text-2xl font-bold text-teal-600 dark:text-teal-400 flex items-baseline gap-1">
                        <span id="stat-present-both">{present_both_count}</span>
                        <span class="text-[11px] font-normal text-slate-400">({dev_coverage_pct})</span>
                    </div>
                    <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-1 truncate">
                        <span>Verified Files on Disk</span>
                    </div>
                </div>

                <!-- KPI 3: Registered in QA -->
                <div id="card-kpi-qa" onclick="drillDown('qa_verified')" class="kpi-card app-card border border-t-[3px] border-t-emerald-500 rounded-xl p-3.5 cursor-pointer transition hover:border-emerald-500 group shadow-sm hover:shadow-md hover:-translate-y-0.5 duration-200" title="Click to view 273 registered QA tools in All Widgets">
                    <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                        <span class="font-semibold text-emerald-700 dark:text-emerald-400 group-hover:text-emerald-500 truncate">Registered in QA</span>
                        <i data-lucide="check-check" class="w-3.5 h-3.5 text-emerald-500 shrink-0"></i>
                    </div>
                    <div class="text-2xl font-bold text-emerald-600 dark:text-emerald-400 flex items-baseline gap-1">
                        <span id="stat-qa-tools">{qa_tool_count}</span>
                        <span class="text-[11px] font-normal text-slate-400">Tools</span>
                    </div>
                    <div class="text-[10px] text-emerald-600 dark:text-emerald-400 mt-1 font-medium truncate">
                        <span>87.8% Syllabus Matched</span>
                    </div>
                </div>

                <!-- KPI 4: Matched in All 3 Sources -->
                <div id="card-kpi-matched" onclick="drillDown('matched_all')" class="kpi-card app-card border border-t-[3px] border-t-indigo-500 rounded-xl p-3.5 cursor-pointer transition hover:border-indigo-500 group shadow-sm hover:shadow-md hover:-translate-y-0.5 duration-200" title="Click to view 258 widgets verified in Excel, Repo, and QA">
                    <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                        <span class="font-semibold text-indigo-700 dark:text-indigo-400 group-hover:text-indigo-500 truncate">Matched in All 3</span>
                        <i data-lucide="shield-check" class="w-3.5 h-3.5 text-indigo-500 shrink-0"></i>
                    </div>
                    <div class="text-2xl font-bold text-indigo-600 dark:text-indigo-400 flex items-baseline gap-1">
                        <span>{matched_all_count}</span>
                        <span class="text-[11px] font-normal text-slate-400">({matched_all_pct})</span>
                    </div>
                    <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-1 truncate">
                        <span>Production Ready</span>
                    </div>
                </div>

                <!-- KPI 5: Pending Development -->
                <div id="card-kpi-dev" onclick="drillDown('requires_dev')" class="kpi-card app-card border border-t-[3px] border-t-rose-500 rounded-xl p-3.5 cursor-pointer transition hover:border-rose-500 group shadow-sm hover:shadow-md hover:-translate-y-0.5 duration-200" title="Click to view 12 widgets needing development">
                    <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                        <span class="font-semibold text-rose-700 dark:text-rose-400 group-hover:text-rose-500 truncate">Needs Development</span>
                        <i data-lucide="alert-circle" class="w-3.5 h-3.5 text-rose-500 shrink-0"></i>
                    </div>
                    <div class="text-2xl font-bold text-rose-600 dark:text-rose-400 flex items-baseline gap-1">
                        <span id="stat-dev-num">{pending_dev_count}</span>
                        <span class="text-[11px] font-normal text-slate-400">({pending_dev_pct})</span>
                    </div>
                    <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-1 truncate">
                        <span>Net-New Dev Backlog</span>
                    </div>
                </div>

                <!-- KPI 6: Missing from QA -->
                <div id="card-kpi-missing-qa" onclick="drillDown('missing_qa')" class="kpi-card app-card border border-t-[3px] border-t-amber-500 rounded-xl p-3.5 cursor-pointer transition hover:border-amber-500 group shadow-sm hover:shadow-md hover:-translate-y-0.5 duration-200" title="Click to view 15 developed widgets missing from QA">
                    <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                        <span class="font-semibold text-amber-700 dark:text-amber-400 group-hover:text-amber-500 truncate">Missing in QA</span>
                        <i data-lucide="help-circle" class="w-3.5 h-3.5 text-amber-500 shrink-0"></i>
                    </div>
                    <div class="text-2xl font-bold text-amber-600 dark:text-amber-400 flex items-baseline gap-1">
                        <span>{missing_qa_count}</span>
                        <span class="text-[11px] font-normal text-slate-400">({missing_qa_pct})</span>
                    </div>
                    <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-1 truncate">
                        <span>QA Ingestion Gap</span>
                    </div>
                </div>

            </div>

            <!-- Secondary Metrics Strip -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div onclick="drillDown('extra_repo')" class="app-subtle border rounded-xl p-3 cursor-pointer hover:border-purple-500 transition flex items-center justify-between">
                    <div>
                        <div class="text-[10px] uppercase font-semibold text-purple-600 dark:text-purple-400 tracking-wider">Uncataloged Repo Assets</div>
                        <div class="text-base font-bold text-slate-900 dark:text-white mt-0.5">+{extra_repo_count} Standalone Simulations</div>
                        <div class="text-[10px] text-slate-500">Runnable on disk, omitted from syllabus</div>
                    </div>
                    <i data-lucide="package-plus" class="w-5 h-5 text-purple-500 shrink-0"></i>
                </div>

                <div onclick="drillDown('naming_issues')" class="app-subtle border rounded-xl p-3 cursor-pointer hover:border-sky-500 transition flex items-center justify-between">
                    <div>
                        <div class="text-[10px] uppercase font-semibold text-sky-600 dark:text-sky-400 tracking-wider">Naming Inconsistencies</div>
                        <div class="text-base font-bold text-slate-900 dark:text-white mt-0.5">{naming_issue_count} Cross-Source Discrepancies</div>
                        <div class="text-[10px] text-slate-500">Mismatches resolved via alias mapping</div>
                    </div>
                    <i data-lucide="spell-check" class="w-5 h-5 text-sky-500 shrink-0"></i>
                </div>

                <div onclick="drillDown('investigation')" class="app-subtle border rounded-xl p-3 cursor-pointer hover:border-rose-500 transition flex items-center justify-between">
                    <div>
                        <div class="text-[10px] uppercase font-semibold text-rose-600 dark:text-rose-400 tracking-wider">Investigation Required</div>
                        <div class="text-base font-bold text-slate-900 dark:text-white mt-0.5">{investigation_count} Data Quality Concerns</div>
                        <div class="text-[10px] text-slate-500">2 duplicates (#25, #257) + 4 flag issues</div>
                    </div>
                    <i data-lucide="search-code" class="w-5 h-5 text-rose-500 shrink-0"></i>
                </div>

                <div onclick="drillDown('whiteboard')" class="app-subtle border rounded-xl p-3 cursor-pointer hover:border-indigo-500 transition flex items-center justify-between">
                    <div>
                        <div class="text-[10px] uppercase font-semibold text-indigo-600 dark:text-indigo-400 tracking-wider">Classroom Whiteboard Tools</div>
                        <div class="text-base font-bold text-slate-900 dark:text-white mt-0.5">{whiteboard_count} Canvas Overlays</div>
                        <div class="text-[10px] text-slate-500">Compass, ruler, timer (Canvas platform)</div>
                    </div>
                    <i data-lucide="pen-tool" class="w-5 h-5 text-indigo-500 shrink-0"></i>
                </div>
            </div>

            <!-- 3. Business & Development Progress Section -->
            <div class="app-card border rounded-2xl p-5 sm:p-6 space-y-4 shadow-sm">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
                    <div class="flex items-center gap-2.5">
                        <div class="w-8 h-8 rounded-lg bg-teal-500/10 text-teal-600 dark:text-teal-400 flex items-center justify-center shrink-0">
                            <i data-lucide="git-merge" class="w-4 h-4"></i>
                        </div>
                        <div>
                            <h2 class="text-sm font-bold text-slate-900 dark:text-white">
                                Business & Development Progress Comparison
                            </h2>
                            <p class="text-[11px] text-slate-500 dark:text-slate-400">
                                Clear distinction between Codebase Development Completion and QA Pipeline Delivery Readiness.
                            </p>
                        </div>
                    </div>
                    <div class="text-[11px] text-slate-500 dark:text-slate-400 italic">
                        * Codebase presence does not equal functional approval; QA validation verifies delivery readiness.
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <!-- Progress Bar 1: Development Coverage -->
                    <div class="space-y-2">
                        <div class="flex items-center justify-between text-xs">
                            <span class="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                                <span class="w-2.5 h-2.5 rounded-full bg-teal-500"></span>
                                <span>Codebase Development Coverage</span>
                            </span>
                            <span class="font-bold text-teal-600 dark:text-teal-400">{present_both_count} / {total_count} ({dev_coverage_pct})</span>
                        </div>
                        <div class="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-3 overflow-hidden p-0.5 border border-slate-300 dark:border-slate-700">
                            <div class="bg-teal-500 h-full rounded-full transition-all duration-500" style="width: {dev_coverage_pct}"></div>
                        </div>
                        <div class="flex justify-between text-[11px] text-slate-500 dark:text-slate-400">
                            <span>273 widgets verified executable on disk</span>
                            <span class="text-rose-600 dark:text-rose-400 font-medium">12 backlog simulations</span>
                        </div>
                    </div>

                    <!-- Progress Bar 2: QA Catalog Availability -->
                    <div class="space-y-2">
                        <div class="flex items-center justify-between text-xs">
                            <span class="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                                <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                                <span>QA Pipeline Availability (Production Ready)</span>
                            </span>
                            <span class="font-bold text-emerald-600 dark:text-emerald-400">{matched_all_count} / {total_count} ({qa_coverage_pct})</span>
                        </div>
                        <div class="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-3 overflow-hidden p-0.5 border border-slate-300 dark:border-slate-700">
                            <div class="bg-emerald-500 h-full rounded-full transition-all duration-500" style="width: {qa_coverage_pct}"></div>
                        </div>
                        <div class="flex justify-between text-[11px] text-slate-500 dark:text-slate-400">
                            <span>258 syllabus widgets matched in QA</span>
                            <span class="text-amber-600 dark:text-amber-400 font-medium">15 developed widgets missing from QA</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 4. Executive 3-Way Reconciliation Matrix Table -->
            <div class="app-card border rounded-2xl p-5 sm:p-6 space-y-4 shadow-sm">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
                    <div class="flex items-center gap-2.5">
                        <div class="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0">
                            <i data-lucide="scale" class="w-4 h-4"></i>
                        </div>
                        <div>
                            <h2 class="text-sm font-bold text-slate-900 dark:text-white">
                                Executive 3-Way Reconciliation Matrix
                            </h2>
                            <p class="text-[11px] text-slate-500 dark:text-slate-400">
                                Empirical audit reconciling Excel (Master Syllabus), Repository Codebase, and Gold QA Catalog.
                            </p>
                        </div>
                    </div>
                    <span class="text-[11px] font-mono px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 font-semibold self-start sm:self-auto">
                        7 Audit Dimensions Reconciled
                    </span>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs">
                        <thead>
                            <tr class="app-subtle border-b text-slate-600 dark:text-slate-400 font-medium">
                                <th class="py-2.5 px-3">Audit Category & Reconciliation Condition</th>
                                <th class="py-2.5 px-3">Primary Source(s)</th>
                                <th class="py-2.5 px-3 text-center">Verified Count</th>
                                <th class="py-2.5 px-3">Business Explanation & Discrepancy Analysis</th>
                                <th class="py-2.5 px-3 text-right">Drill-Down</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100 dark:divide-slate-800/80">
                            
                            <!-- Row 1: Matched in All 3 Sources -->
                            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                                <td class="py-3 px-3 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <div class="w-6 h-6 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0"><i data-lucide="check-check" class="w-3.5 h-3.5"></i></div>
                                    <span>1. Matched in All 3 Sources (Excel ∩ Repo ∩ QA)</span>
                                </td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400 font-mono text-[11px]">Excel ∩ Repo ∩ QA</td>
                                <td class="py-3 px-3 text-center font-bold text-emerald-600 dark:text-emerald-400 text-sm">{matched_all_count}</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">Production ready. Required in syllabus, verified executable in repo, and registered in Gold QA catalog.</td>
                                <td class="py-3 px-3 text-right"><button onclick="drillDown('matched_all')" class="px-2.5 py-1 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/20 transition cursor-pointer">View 258</button></td>
                            </tr>

                            <!-- Row 2: Present in Repo but Missing in Excel -->
                            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                                <td class="py-3 px-3 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <div class="w-6 h-6 rounded-md bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center shrink-0"><i data-lucide="package-plus" class="w-3.5 h-3.5"></i></div>
                                    <span>2. Present in Repo but Missing in Excel (Extra)</span>
                                </td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400 font-mono text-[11px]">Repository Disk</td>
                                <td class="py-3 px-3 text-center font-bold text-purple-600 dark:text-purple-400 text-sm">+{extra_repo_count}</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">46 standalone HTML simulations exist physically on disk in widgets-b1/b2/b3 with runnable index.html files not documented in syllabus.</td>
                                <td class="py-3 px-3 text-right"><button onclick="drillDown('extra_repo')" class="px-2.5 py-1 rounded text-[11px] font-medium bg-purple-500/10 text-purple-600 dark:text-purple-400 hover:bg-purple-500/20 border border-purple-500/20 transition cursor-pointer">View Extra (46)</button></td>
                            </tr>

                            <!-- Row 3: Present in Excel but Missing in Repo -->
                            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                                <td class="py-3 px-3 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <div class="w-6 h-6 rounded-md bg-rose-500/10 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0"><i data-lucide="x-circle" class="w-3.5 h-3.5"></i></div>
                                    <span>3. Present in Excel but Missing in Repo</span>
                                </td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400 font-mono text-[11px]">Excel Syllabus</td>
                                <td class="py-3 px-3 text-center font-bold text-rose-600 dark:text-rose-400 text-sm">{missing_repo_count}</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">21 items: 12 genuine curriculum simulations needing net-new development + 9 interactive whiteboard canvas tools.</td>
                                <td class="py-3 px-3 text-right"><button onclick="drillDown('source_missing')" class="px-2.5 py-1 rounded text-[11px] font-medium bg-rose-500/10 text-rose-600 dark:text-rose-400 hover:bg-rose-500/20 border border-rose-500/20 transition cursor-pointer">View Missing (21)</button></td>
                            </tr>

                            <!-- Row 4: Present in Excel & Repo but Missing in QA -->
                            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                                <td class="py-3 px-3 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <div class="w-6 h-6 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0"><i data-lucide="help-circle" class="w-3.5 h-3.5"></i></div>
                                    <span>4. Present in Excel & Repo but Missing in QA</span>
                                </td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400 font-mono text-[11px]">Excel ∩ Repo</td>
                                <td class="py-3 px-3 text-center font-bold text-amber-600 dark:text-amber-400 text-sm">{missing_qa_count}</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">15 finished widgets are verified on disk but omitted from Gold QA catalog (Chemistry 4, Math 5, Biology 2, History 2, Env Sci 1, Geography 1).</td>
                                <td class="py-3 px-3 text-right"><button onclick="drillDown('missing_qa')" class="px-2.5 py-1 rounded text-[11px] font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400 hover:bg-amber-500/20 border border-amber-500/20 transition cursor-pointer">View QA Gap (15)</button></td>
                            </tr>

                            <!-- Row 5: Naming Inconsistencies -->
                            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                                <td class="py-3 px-3 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <div class="w-6 h-6 rounded-md bg-sky-500/10 text-sky-600 dark:text-sky-400 flex items-center justify-center shrink-0"><i data-lucide="spell-check" class="w-3.5 h-3.5"></i></div>
                                    <span>5. Widgets with Different Names Across Sources</span>
                                </td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400 font-mono text-[11px]">Naming Audit</td>
                                <td class="py-3 px-3 text-center font-bold text-sky-600 dark:text-sky-400 text-sm">{naming_issue_count}</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">7 widgets with typo or title variants (e.g. Domino vs Dominic, Indian Constitution vs Institution, Commutative vs Cumulative) resolved via alias mapping.</td>
                                <td class="py-3 px-3 text-right"><button onclick="drillDown('naming_issues')" class="px-2.5 py-1 rounded text-[11px] font-medium bg-sky-500/10 text-sky-600 dark:text-sky-400 hover:bg-sky-500/20 border border-sky-500/20 transition cursor-pointer">View Mappings (7)</button></td>
                            </tr>

                            <!-- Row 6: Duplicate or Potentially Duplicate Widgets -->
                            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                                <td class="py-3 px-3 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <div class="w-6 h-6 rounded-md bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center shrink-0"><i data-lucide="copy" class="w-3.5 h-3.5"></i></div>
                                    <span>6. Duplicate Records in Excel Reference</span>
                                </td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400 font-mono text-[11px]">Excel Catalog</td>
                                <td class="py-3 px-3 text-center font-bold text-purple-600 dark:text-purple-400 text-sm">{duplicate_count}</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">2 spreadsheet entries repeated in master Excel (#25 Plant Detective Challenge, #257 Multiplication of two binomials); both map to existing code.</td>
                                <td class="py-3 px-3 text-right"><button onclick="drillDown('duplicates')" class="px-2.5 py-1 rounded text-[11px] font-medium bg-purple-500/10 text-purple-600 dark:text-purple-400 hover:bg-purple-500/20 border border-purple-500/20 transition cursor-pointer">View Duplicates (2)</button></td>
                            </tr>

                            <!-- Row 7: Unmatched Records Requiring Investigation -->
                            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                                <td class="py-3 px-3 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <div class="w-6 h-6 rounded-md bg-rose-500/10 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0"><i data-lucide="search-code" class="w-3.5 h-3.5"></i></div>
                                    <span>7. Unmatched Records Requiring Investigation</span>
                                </td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400 font-mono text-[11px]">Data Integrity</td>
                                <td class="py-3 px-3 text-center font-bold text-rose-600 dark:text-rose-400 text-sm">{investigation_count}</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">6 entries requiring product alignment (2 duplicate rows + 2 missing unassigned rows #61, #251 + 2 minor extension rows #31 CO Molecule, #210 Integer Subtraction).</td>
                                <td class="py-3 px-3 text-right"><button onclick="drillDown('investigation')" class="px-2.5 py-1 rounded text-[11px] font-medium bg-rose-500/10 text-rose-600 dark:text-rose-400 hover:bg-rose-500/20 border border-rose-500/20 transition cursor-pointer">View Records (6)</button></td>
                            </tr>

                        </tbody>
                    </table>
                </div>
            </div>

            <!-- 5. Subject-Wise Performance Summary & Cards -->
            <div class="app-card border rounded-2xl p-5 sm:p-6 space-y-4 shadow-sm">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
                    <div class="flex items-center gap-2.5">
                        <div class="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
                            <i data-lucide="layers" class="w-4 h-4"></i>
                        </div>
                        <div>
                            <h2 class="text-sm font-bold text-slate-900 dark:text-white">
                                Subject-Wise Performance & Development Status
                            </h2>
                            <p class="text-[11px] text-slate-500 dark:text-slate-400">
                                Detailed curriculum breakdown showing expected vs developed vs QA-ready across all 15 strands.
                            </p>
                        </div>
                    </div>
                    <span class="text-[11px] text-slate-400 self-start sm:self-auto">Click any row or card to filter All Widgets</span>
                </div>

                <!-- Subject Performance Table -->
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs">
                        <thead>
                            <tr class="app-subtle border-b text-slate-600 dark:text-slate-400 font-medium">
                                <th class="py-2.5 px-3">Subject Strand</th>
                                <th class="py-2.5 px-3 text-center">Expected</th>
                                <th class="py-2.5 px-3 text-center">Developed</th>
                                <th class="py-2.5 px-3 text-center">QA Ready</th>
                                <th class="py-2.5 px-3 text-center">Dev Gap</th>
                                <th class="py-2.5 px-3 text-center">Canvas</th>
                                <th class="py-2.5 px-3 text-center">Naming</th>
                                <th class="py-2.5 px-3 text-center">Dev %</th>
                                <th class="py-2.5 px-3 text-center">QA %</th>
                                <th class="py-2.5 px-3 text-center">Executive Status</th>
                                <th class="py-2.5 px-3 text-right">Drill-Down</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100 dark:divide-slate-800/80">
{subject_performance_table_html}
                        </tbody>
                    </table>
                </div>

                <!-- Subject Cards Grid -->
                <div class="pt-3 border-t border-slate-100 dark:border-slate-800">
                    <div class="text-xs font-bold text-slate-700 dark:text-slate-300 mb-3 uppercase tracking-wider">
                        Subject Visual Cards Overview
                    </div>
                    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
{subject_cards_html}
                    </div>
                </div>
            </div>

            <!-- 6. Management Insights & Business Risk Analysis -->
            <div class="space-y-3">
                <div class="flex items-center gap-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                    <h2 class="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                        Management Insights & Strategic Business Risk Analysis
                    </h2>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    
                    <!-- Insight 1: Dev Backlog -->
                    <div class="app-card border border-rose-500/20 rounded-xl p-4 space-y-2.5 shadow-sm">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold text-rose-600 dark:text-rose-400 flex items-center gap-1.5 uppercase tracking-wider">
                                <i data-lucide="alert-octagon" class="w-3.5 h-3.5"></i>
                                <span>1. Major Development Gap (12 Widgets)</span>
                            </span>
                            <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">HIGH RISK</span>
                        </div>
                        <p class="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                            <strong>Scope:</strong> Biology (3), Mathematics (3), Geography (2), Chemistry (1), Science (1), English (1), Geometry (1) have zero implementation in the repository codebase.
                        </p>
                        <div class="p-2.5 rounded-lg bg-rose-500/[0.06] border border-rose-500/15 text-[11px] space-y-1">
                            <div><strong class="text-rose-700 dark:text-rose-400">Business Impact:</strong> Term launch delays for core STEM subjects; syllabus cannot be certified complete without these 12 interactive simulations.</div>
                            <div><strong class="text-rose-700 dark:text-rose-400">Recommended Action:</strong> Spin up a dedicated 3-week engineering sprint with 2 senior front-end developers to complete all 12 simulations.</div>
                        </div>
                    </div>

                    <!-- Insight 2: QA Deployment Bottleneck -->
                    <div class="app-card border border-amber-500/20 rounded-xl p-4 space-y-2.5 shadow-sm">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold text-amber-600 dark:text-amber-400 flex items-center gap-1.5 uppercase tracking-wider">
                                <i data-lucide="clock" class="w-3.5 h-3.5"></i>
                                <span>2. QA Deployment Bottleneck (15 Widgets)</span>
                            </span>
                            <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">MEDIUM RISK</span>
                        </div>
                        <p class="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                            <strong>Scope:</strong> 15 widgets are fully developed and verified on disk (Chemistry 4, Math 5, Biology 2, History 2, Env Sci 1, Geography 1) but missing from Gold QA Catalog.
                        </p>
                        <div class="p-2.5 rounded-lg bg-amber-500/[0.06] border border-amber-500/15 text-[11px] space-y-1">
                            <div><strong class="text-amber-700 dark:text-amber-400">Business Impact:</strong> Engineering investment blocked at deployment gate; students cannot access completed lessons due to catalog registration delay.</div>
                            <div><strong class="text-amber-700 dark:text-amber-400">Recommended Action:</strong> QA Lead to ingest launchPage metadata and test cases for all 15 widgets within 5 business days.</div>
                        </div>
                    </div>

                    <!-- Insight 3: Uncataloged Assets -->
                    <div class="app-card border border-purple-500/20 rounded-xl p-4 space-y-2.5 shadow-sm">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold text-purple-600 dark:text-purple-400 flex items-center gap-1.5 uppercase tracking-wider">
                                <i data-lucide="package-plus" class="w-3.5 h-3.5"></i>
                                <span>3. Uncataloged Content Value (46 Bonus Assets)</span>
                            </span>
                            <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">OPPORTUNITY</span>
                        </div>
                        <p class="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                            <strong>Scope:</strong> 46 standalone HTML simulations in widgets-b1/b2/b3 are fully runnable but omitted from the reference curriculum syllabus spreadsheet.
                        </p>
                        <div class="p-2.5 rounded-lg bg-purple-500/[0.06] border border-purple-500/15 text-[11px] space-y-1">
                            <div><strong class="text-purple-700 dark:text-purple-400">Business Impact:</strong> Sunk engineering investment is sitting dormant on disk with zero curriculum credit or student engagement.</div>
                            <div><strong class="text-purple-700 dark:text-purple-400">Recommended Action:</strong> Academic curriculum committee to evaluate and adopt these 46 bonus simulations into corresponding syllabus grades.</div>
                        </div>
                    </div>

                    <!-- Insight 4: Data Governance & Scope -->
                    <div class="app-card border border-indigo-500/20 rounded-xl p-4 space-y-2.5 shadow-sm">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold text-indigo-600 dark:text-indigo-400 flex items-center gap-1.5 uppercase tracking-wider">
                                <i data-lucide="shield-alert" class="w-3.5 h-3.5"></i>
                                <span>4. Data Integrity & Scope Governance</span>
                            </span>
                            <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">GOVERNANCE</span>
                        </div>
                        <p class="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                            <strong>Scope:</strong> 9 whiteboard canvas tools misclassified as lesson simulations, 7 title discrepancies across files, and 2 duplicate rows in Excel (#25, #257).
                        </p>
                        <div class="p-2.5 rounded-lg bg-indigo-500/[0.06] border border-indigo-500/15 text-[11px] space-y-1">
                            <div><strong class="text-indigo-700 dark:text-indigo-400">Business Impact:</strong> Distorts completion metrics with false missing alarms; confusion between whiteboard platform team and simulation team.</div>
                            <div><strong class="text-indigo-700 dark:text-indigo-400">Recommended Action:</strong> Reclassify 9 canvas tools to Platform Infrastructure; remove duplicate rows; standardize 7 titles in master sheet.</div>
                        </div>
                    </div>

                </div>
            </div>

            <!-- 7. Prioritized Management Action Plan -->
            <div class="app-card border rounded-2xl p-5 sm:p-6 space-y-4 shadow-sm">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
                    <div class="flex items-center gap-2.5">
                        <div class="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
                            <i data-lucide="check-square" class="w-4 h-4"></i>
                        </div>
                        <div>
                            <h2 class="text-sm font-bold text-slate-900 dark:text-white">
                                Prioritized Management Action Plan
                            </h2>
                            <p class="text-[11px] text-slate-500 dark:text-slate-400">
                                Clear, actionable classification of pending work with priority, owner, timeline, and business justification.
                            </p>
                        </div>
                    </div>
                    <span class="text-[11px] font-mono px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 font-semibold self-start sm:self-auto">
                        6 Strategic Initiatives
                    </span>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs">
                        <thead>
                            <tr class="app-subtle border-b text-slate-600 dark:text-slate-400 font-medium">
                                <th class="py-2.5 px-3">Action Item & Objective</th>
                                <th class="py-2.5 px-3">Category</th>
                                <th class="py-2.5 px-3 text-center">Priority</th>
                                <th class="py-2.5 px-3">Owner</th>
                                <th class="py-2.5 px-3">Timeline</th>
                                <th class="py-2.5 px-3">Business Justification</th>
                                <th class="py-2.5 px-3 text-right">View Scope</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100 dark:divide-slate-800/80">
                            
                            <!-- Action 1 -->
                            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                                <td class="py-3 px-3 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <div class="w-6 h-6 rounded-md bg-rose-500/10 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0">1</div>
                                    <span>Build 12 Backlog Simulations</span>
                                </td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400 font-medium">Development Required</td>
                                <td class="py-3 px-3 text-center"><span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">HIGH</span></td>
                                <td class="py-3 px-3 text-slate-700 dark:text-slate-300 font-medium">Lead Frontend Dev</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">3-Week Sprint</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">Delivers remaining 4.1% of curriculum scope; eliminates final syllabus blockers.</td>
                                <td class="py-3 px-3 text-right"><button onclick="drillDown('requires_dev')" class="px-2.5 py-1 rounded text-[11px] font-medium bg-rose-500/10 text-rose-600 dark:text-rose-400 hover:bg-rose-500/20 border border-rose-500/20 transition cursor-pointer">View 12</button></td>
                            </tr>

                            <!-- Action 2 -->
                            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                                <td class="py-3 px-3 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <div class="w-6 h-6 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0">2</div>
                                    <span>Ingest 15 Finished Widgets into QA</span>
                                </td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400 font-medium">QA Deployment Required</td>
                                <td class="py-3 px-3 text-center"><span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">MEDIUM</span></td>
                                <td class="py-3 px-3 text-slate-700 dark:text-slate-300 font-medium">QA Lead</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">5 Business Days</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">Instantly boosts production readiness from 87.8% to 92.9% by unblocking finished code.</td>
                                <td class="py-3 px-3 text-right"><button onclick="drillDown('missing_qa')" class="px-2.5 py-1 rounded text-[11px] font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400 hover:bg-amber-500/20 border border-amber-500/20 transition cursor-pointer">View 15</button></td>
                            </tr>

                            <!-- Action 3 -->
                            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                                <td class="py-3 px-3 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <div class="w-6 h-6 rounded-md bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center shrink-0">3</div>
                                    <span>Adopt 46 Extra Standalone Simulations</span>
                                </td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400 font-medium">Content Catalog Update</td>
                                <td class="py-3 px-3 text-center"><span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">MEDIUM</span></td>
                                <td class="py-3 px-3 text-slate-700 dark:text-slate-300 font-medium">Curriculum Head</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">2 Weeks</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">Monetizes existing engineering work by incorporating 46 high-value simulations into syllabus.</td>
                                <td class="py-3 px-3 text-right"><button onclick="drillDown('extra_repo')" class="px-2.5 py-1 rounded text-[11px] font-medium bg-purple-500/10 text-purple-600 dark:text-purple-400 hover:bg-purple-500/20 border border-purple-500/20 transition cursor-pointer">View 46</button></td>
                            </tr>

                            <!-- Action 4 -->
                            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                                <td class="py-3 px-3 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <div class="w-6 h-6 rounded-md bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0">4</div>
                                    <span>Clean 6 Investigation & Duplicate Records</span>
                                </td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400 font-medium">Data Quality & Cleansing</td>
                                <td class="py-3 px-3 text-center"><span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">MEDIUM</span></td>
                                <td class="py-3 px-3 text-slate-700 dark:text-slate-300 font-medium">Data Steward / BA</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">2 Business Days</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">Removes duplicate rows #25 and #257 in master Excel and aligns config flags.</td>
                                <td class="py-3 px-3 text-right"><button onclick="drillDown('investigation')" class="px-2.5 py-1 rounded text-[11px] font-medium bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-500/20 border border-indigo-500/20 transition cursor-pointer">View 6</button></td>
                            </tr>

                            <!-- Action 5 -->
                            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                                <td class="py-3 px-3 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <div class="w-6 h-6 rounded-md bg-slate-500/10 text-slate-600 dark:text-slate-400 flex items-center justify-center shrink-0">5</div>
                                    <span>Reclassify 9 Whiteboard Tools to Platform</span>
                                </td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400 font-medium">Scope Governance</td>
                                <td class="py-3 px-3 text-center"><span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-500/20">LOW</span></td>
                                <td class="py-3 px-3 text-slate-700 dark:text-slate-300 font-medium">Product Manager</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">1 Business Day</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">Separates classroom canvas overlay utilities from interactive curriculum simulation count.</td>
                                <td class="py-3 px-3 text-right"><button onclick="drillDown('whiteboard')" class="px-2.5 py-1 rounded text-[11px] font-medium bg-slate-500/10 text-slate-600 dark:text-slate-400 hover:bg-slate-500/20 border border-slate-500/20 transition cursor-pointer">View 9</button></td>
                            </tr>

                            <!-- Action 6 -->
                            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                                <td class="py-3 px-3 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <div class="w-6 h-6 rounded-md bg-slate-500/10 text-slate-600 dark:text-slate-400 flex items-center justify-center shrink-0">6</div>
                                    <span>Standardize 7 Excel Widget Titles</span>
                                </td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400 font-medium">Documentation Update</td>
                                <td class="py-3 px-3 text-center"><span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-500/20">LOW</span></td>
                                <td class="py-3 px-3 text-slate-700 dark:text-slate-300 font-medium">Content Specialist</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">1 Business Day</td>
                                <td class="py-3 px-3 text-slate-600 dark:text-slate-400">Harmonizes spreadsheet titles with codebase folder names for clean automated tracking.</td>
                                <td class="py-3 px-3 text-right"><button onclick="drillDown('naming_issues')" class="px-2.5 py-1 rounded text-[11px] font-medium bg-slate-500/10 text-slate-600 dark:text-slate-400 hover:bg-slate-500/20 border border-slate-500/20 transition cursor-pointer">View 7</button></td>
                            </tr>

                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Invisible hooks to maintain full compatibility with updateDynamicMetrics -->
            <span id="stat-excel-found" class="hidden"></span>
            <span id="stat-excel-found-pct" class="hidden"></span>
            <span id="stat-excel-notfound" class="hidden"></span>
            <span id="stat-excel-notfound-num" class="hidden"></span>
            <span id="stat-excel-notfound-pct" class="hidden"></span>
            <span id="stat-excel-repeated" class="hidden"></span>
            <span id="stat-excel-repeated-num" class="hidden"></span>
            <span id="stat-excel-notfound-sub" class="hidden"></span>
            <span id="stat-excel-notfound-sub-num" class="hidden"></span>
            <span id="sheetRefName" class="hidden"></span>
            <span id="pill-source-present" class="hidden"></span>
            <span id="pill-live-html" class="hidden"></span>
            <span id="pill-source-missing" class="hidden"></span>
            <span id="pill-whiteboard" class="hidden"></span>
            <span id="stat-minor-badge" class="hidden"></span>
            <span id="stat-dev-badge" class="hidden"></span>
            <span id="stat-wb-badge" class="hidden"></span>

        </div>
    """)
'''

with open('scripts/build_ceo_dashboard.py', 'a', encoding='utf-8') as f:
    f.write(part2_code)

print("Part 2 code appended to build_ceo_dashboard.py successfully.")
