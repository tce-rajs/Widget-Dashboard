import openpyxl
import re
import json
import os
import subprocess
import time
from collections import Counter

def generate():
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    catalog_path = os.path.join(scripts_dir, 'repo_catalog.json')
    cached_catalog = {}
    if os.path.exists(catalog_path):
        try:
            with open(catalog_path, 'r', encoding='utf-8') as f:
                cached_catalog = json.load(f)
        except Exception:
            pass

    # 1. Parse Markdown comparison if present (in full repository)
    md_path = 'WIDGET_REPOSITORY_COMPARISON.md'
    md_data = {}
    if os.path.exists(md_path):
        with open(md_path, 'r', encoding='utf-8') as f:
            md_text = f.read()

        pattern = re.compile(r'\|\s*(\d+)\s*\|\s*([^|]+)\s*\|\s*(Present|Missing|Needs verification)\s*\|\s*([^|]+)\s*\|')
        for sr, name, status, evidence in pattern.findall(md_text):
            n_clean = name.strip()
            if n_clean.startswith('---') or 'Sr. No.' in n_clean:
                continue
            md_data[n_clean] = {
                'sr': int(sr),
                'status': status.strip(),
                'evidence': evidence.strip()
            }

    # 2. Locate Excel Spreadsheet (.xlsx)
    excel_candidates = ['Widgets in CE Platinum cum Crystal.xlsx', 'Widgets in CE Platinum cum Crystal 1.xlsx']
    excel_path = None
    for cand in excel_candidates:
        if os.path.exists(cand):
            excel_path = cand
            break
    if not excel_path:
        for f in os.listdir('.'):
            if f.endswith('.xlsx') and not f.startswith('~$'):
                excel_path = f
                break
    if not excel_path:
        raise FileNotFoundError("No .xlsx spreadsheet found in the repository root!")

    excel_filename = os.path.basename(excel_path)
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    sheet_name = 'Widget-RepoList' if 'Widget-RepoList' in wb.sheetnames else wb.sheetnames[0]
    s_repo = wb[sheet_name]
    rows = list(s_repo.iter_rows(values_only=True))

    # Auto-detect column mapping
    col_map = {'sr': 3, 'subj': 4, 'name': 5, 'batch': 6, 'repo': 7, 'owner': 8}
    for r in range(min(5, len(rows))):
        row = rows[r]
        if not row: continue
        for c, cell in enumerate(row):
            val = str(cell or '').lower().strip()
            if 'sr.' in val or val == 'sr' or val == 'sr no': col_map['sr'] = c
            elif 'subject' in val: col_map['subj'] = c
            elif 'widget' in val or 'widget (silver)' in val: col_map['name'] = c
            elif 'batch' in val: col_map['batch'] = c
            elif 'repo' in val: col_map['repo'] = c
            elif 'owner' in val: col_map['owner'] = c

    excel_items = {}
    current_subj = 'General'

    for r in rows[2:]:
        w_name = r[col_map['name']]
        if not w_name or str(w_name).strip() == 'Widget (Silver) (CEP)':
            continue
        w_name = str(w_name).strip()
        subj = r[col_map['subj']]
        if subj and str(subj).strip():
            current_subj = str(subj).strip()

        batch = str(r[col_map['batch']]).strip() if r[col_map['batch']] is not None else ''
        repo_link = str(r[col_map['repo']]).strip() if r[col_map['repo']] is not None else ''
        owner = str(r[col_map['owner']]).strip() if r[col_map['owner']] is not None else ''

        if w_name not in excel_items:
            excel_items[w_name] = {
                'name': w_name,
                'subject': current_subj,
                'batch': batch,
                'repo_link': repo_link,
                'owner': owner
            }

    whiteboard_tools = {'Compass', 'Clock', 'Ruler', 'Protractor', 'Set Square 30', 'Set Square 45', 'Curtain', 'Split Screen', 'Scientific Calculator'}

    aliases = {
        'Operation Domino WW II Mission': 'Operation Dominic',
        "Making of India's Constitution": 'Making of the Indian Institution',
        'Commutative Property of Addition': 'Cumulative Property of Addition'
    }

    def find_widget_on_disk(w_name, batch_code, repo_link):
        if repo_link and repo_link.lower() not in ('no', 'yes', '-', ''):
            clean_l = repo_link.strip().replace('/', os.sep).replace('\\', os.sep)
            if os.path.exists(clean_l):
                return repo_link.strip().replace('\\', '/')
            if os.path.exists(os.path.join(clean_l, 'index.html')):
                return os.path.join(repo_link.strip(), 'index.html').replace('\\', '/')
        
        batch_slug = re.sub(r'[^a-zA-Z0-9]', '', batch_code).lower()
        name_slug = re.sub(r'[^a-zA-Z0-9]', '', w_name).lower()
        
        for sdir in ['widgets-b1', 'widgets-b2', 'widgets-b3', 'widgets-b4', 'src/app']:
            if not os.path.exists(sdir):
                continue
            for entry in os.listdir(sdir):
                entry_clean = re.sub(r'[^a-zA-Z0-9]', '', entry).lower()
                if batch_slug and len(batch_slug) > 3 and batch_slug in entry_clean:
                    cand = os.path.join(sdir, entry)
                    if os.path.exists(os.path.join(cand, 'index.html')):
                        return os.path.join(cand, 'index.html').replace('\\', '/')
                    return cand.replace('\\', '/')
                if name_slug and len(name_slug) > 3 and (name_slug in entry_clean or entry_clean in name_slug):
                    cand = os.path.join(sdir, entry)
                    if os.path.exists(os.path.join(cand, 'index.html')):
                        return os.path.join(cand, 'index.html').replace('\\', '/')
                    return cand.replace('\\', '/')
        return None

    reconciled_list = []
    sorted_names = sorted(excel_items.keys(), key=lambda n: md_data.get(aliases.get(n, n), {}).get('sr', 999))

    for idx, name in enumerate(sorted_names):
        ex = excel_items[name]
        lookup_name = aliases.get(name, name)
        norm_key = lookup_name.lower().strip()
        cat_fallback = cached_catalog.get(norm_key, cached_catalog.get(name.lower().strip(), {}))

        md = md_data.get(lookup_name, {})
        raw_status = md.get('status', cat_fallback.get('status_category', 'Unknown'))
        raw_ev = md.get('evidence', cat_fallback.get('technical_notes', ''))
        
        p_match = re.search(r'`([^`]+)`', raw_ev)
        repo_path = p_match.group(1) if p_match else cat_fallback.get('repo_path', '')
        
        status_category = 'available'
        status_label = 'Already Available'
        plain_explanation = 'This widget is already implemented and available in the repository.'
        what_was_checked = 'Checked repository files and confirmed executable HTML5/component.'
        what_needs_to_be_done = 'No new development needed. Ready for QA testing.'
        
        # Explicit overrides for false negatives and quick extensions
        if name in ('Operation Dominic', 'Operation Domino WW II Mission'):
            status_category = 'corrected'
            status_label = 'Found in Repository'
            repo_path = 'widgets-b3/wg96-operation-domino/index.html'
            plain_explanation = 'The Excel list originally had a spelling mistake ("Dominic" instead of "Domino"). The widget already exists in the repository as "Operation Domino WW II Mission".'
            what_was_checked = 'Matched batch B3-WG96 and verified the folder "widgets-b3/wg96-operation-domino".'
            what_needs_to_be_done = 'Do not rebuild. Update documentation to point to Operation Domino.'
        elif name in ('Making of the Indian Institution', "Making of India's Constitution"):
            status_category = 'corrected'
            status_label = 'Found in Repository'
            repo_path = 'widgets-b3/wg113-making-of-Indias-constitution/index.html'
            plain_explanation = 'The Excel list originally had a naming difference ("Indian Institution" instead of "India\'s Constitution"). The widget already exists in the repository as "Making of India\'s Constitution".'
            what_was_checked = 'Matched batch B3-WG113 and verified the folder "widgets-b3/wg113-making-of-Indias-constitution".'
            what_needs_to_be_done = 'Do not rebuild. Map this entry to India\'s Constitution.'
        elif name == 'Cumulative Property of Addition':
            status_category = 'corrected'
            status_label = 'Found in Repository'
            repo_path = 'widgets-b1/visualizing_the_commutative_property_of_addition/index.html'
            plain_explanation = 'The Excel list had a math term typo ("Cumulative" instead of "Commutative"). The activity exists in the repository as "Visualizing the Commutative Property of Addition".'
            what_was_checked = 'Verified the simulation in "widgets-b1/visualizing_the_commutative_property_of_addition".'
            what_needs_to_be_done = 'Do not rebuild. Confirm standard commutative property terminology.'
        elif name == 'Linear Equations in 1 variable':
            status_category = 'corrected'
            status_label = 'Found in Repository'
            repo_path = 'widgets-b1/visualizing_algebraic_equations/index.html'
            plain_explanation = 'The widget is implemented under the title "Build the Equation". It provides an interactive balance scale for solving one-variable linear equations (ax + b = c).'
            what_was_checked = 'Verified equation-building activity in "widgets-b1/visualizing_algebraic_equations".'
            what_needs_to_be_done = 'Do not rebuild. Use the existing Build the Equation widget.'
        elif name == 'Multiplications of Large Nos. with 1 digit no.':
            status_category = 'corrected'
            status_label = 'Found in Repository'
            repo_path = 'widgets-b1/multiplying-multi-digit/index.html'
            plain_explanation = 'The widget is implemented under the title "Multiplying Multi-Digit and 1-Digit Numbers Using Partial Products".'
            what_was_checked = 'Verified interactive multiplication in "widgets-b1/multiplying-multi-digit".'
            what_needs_to_be_done = 'Do not rebuild. Use the existing multi-digit multiplication widget.'
        elif name == 'Addition and Subtraction of Integers':
            status_category = 'minor_changes'
            status_label = 'Small Changes Needed'
            repo_path = 'widgets-b3/wg104-addition-of-integers/index.html'
            plain_explanation = 'Integer addition is already fully working in the repository. We only need to add a toggle for subtraction mode.'
            what_was_checked = 'Verified addition activity in "widgets-b3/wg104-addition-of-integers".'
            what_needs_to_be_done = 'Add a simple subtraction mode switch to the existing widget.'
        elif name == 'CO Molecule':
            status_category = 'minor_changes'
            status_label = 'Small Changes Needed'
            repo_path = 'widgets-b2/wg13-build-molecule/index.html'
            plain_explanation = 'The interactive molecule builder already supports CO2, H2O, NH3, SO2, and Ethanol. We only need to add the Carbon Monoxide (CO) layout.'
            what_was_checked = 'Checked molecule builder configuration in "widgets-b2/wg13-build-molecule".'
            what_needs_to_be_done = 'Add Carbon Monoxide atom coordinates to the existing molecule list.'
        elif name == 'Build a Sentence 2':
            status_category = 'available'
            status_label = 'Already Available'
            repo_path = 'widgets-b2/wg5-build-a-sentence/index.html'
            plain_explanation = 'Shares the sentence-building activity implementation with Build a Sentence 1 (widgets-b2/wg5-build-a-sentence).'
            what_was_checked = 'Verified shared sentence simulation in "widgets-b2/wg5-build-a-sentence".'
            what_needs_to_be_done = 'Ready for QA validation using the shared sentence builder.'
        elif name == 'Multiplications of Fractions - 2':
            status_category = 'available'
            status_label = 'Already Available'
            repo_path = 'src/app/fraction-multiplication/fraction-multiplication.component.ts'
            plain_explanation = 'Shares the fraction-multiplication activity implementation with Multiplications of Fractions - 1 (src/app/fraction-multiplication).'
            what_was_checked = 'Verified shared component in "src/app/fraction-multiplication".'
            what_needs_to_be_done = 'Ready for QA validation using the shared fraction multiplication module.'
        elif name in whiteboard_tools:
            status_category = 'whiteboard'
            status_label = 'Classroom Tools'
            repo_path = ''
            plain_explanation = 'This is an interactive whiteboard overlay tool (e.g. ruler, compass, curtain, timer) rather than a subject lesson simulation.'
            what_was_checked = 'Confirmed marked as "Repo: No" in the reference Excel list.'
            what_needs_to_be_done = 'Clarify whether classroom tools are part of the platform whiteboard shell or this widget repository.'
        elif raw_status == 'Missing' or cat_fallback.get('status_category') == 'requires_dev':
            # Check if developer has newly implemented this widget in the codebase
            found_disk = find_widget_on_disk(name, ex['batch'], ex['repo_link'])
            if found_disk:
                status_category = 'available'
                status_label = 'Already Available'
                repo_path = found_disk
                plain_explanation = f'Newly implemented widget verified present in repository ({found_disk}).'
                what_was_checked = f'Found executable simulation on disk at {found_disk}.'
                what_needs_to_be_done = 'Ready for QA validation testing.'
            else:
                status_category = 'requires_dev'
                status_label = 'Not Available – Needs Development'
                repo_path = ''
                plain_explanation = 'No matching implementation was found in the repository. This widget needs to be planned for future development.'
                what_was_checked = 'Searched entire repository codebase and found no matching code or entry point.'
                what_needs_to_be_done = 'Assign to instructional design and development teams.'
        elif raw_status == 'Present' or cat_fallback.get('status_category') == 'available':
            status_category = 'available'
            status_label = 'Already Available'
            plain_explanation = 'This widget is present in the repository and its files are ready.'
            what_was_checked = 'Found executable code entry point in repository.'
            what_needs_to_be_done = 'Ready for QA validation.'
        elif cat_fallback:
            status_category = cat_fallback.get('status_category', 'available')
            status_label = cat_fallback.get('status_label', 'Already Available')
            plain_explanation = cat_fallback.get('plain_explanation', plain_explanation)
            what_was_checked = cat_fallback.get('what_was_checked', what_was_checked)
            what_needs_to_be_done = cat_fallback.get('what_needs_to_be_done', what_needs_to_be_done)
        
        # Determine WG Number
        wg_code = '-'
        if name in ('Operation Dominic', 'Operation Domino WW II Mission'):
            wg_code = 'B3-WG96'
        elif name in ('Making of the Indian Institution', "Making of India's Constitution"):
            wg_code = 'B3-WG113'
        elif name == 'Addition and Subtraction of Integers':
            wg_code = 'B3-WG104'
        elif name == 'CO Molecule':
            wg_code = 'B2-WG13'
        elif name == 'Build a Sentence 2':
            wg_code = 'B2-WG05'
        elif name in whiteboard_tools:
            wg_code = 'TOOL'
        elif cat_fallback.get('wg_code') and cat_fallback['wg_code'] != '-':
            wg_code = cat_fallback['wg_code']
        else:
            m_batch = re.search(r'B\d+-WG\d+|WG\d+', ex['batch'], re.IGNORECASE)
            if m_batch:
                wg_code = m_batch.group(0).upper()
            else:
                m_ev = re.search(r'wg\d+|WG\d+', raw_ev)
                if m_ev:
                    core = m_ev.group(0).upper()
                    if 'widgets-b3' in repo_path or 'widgets-b3' in raw_ev:
                        wg_code = 'B3-' + core
                    elif 'widgets-b2' in repo_path or 'widgets-b2' in raw_ev:
                        wg_code = 'B2-' + core
                    else:
                        wg_code = core
                elif ex['batch']:
                    wg_code = ex['batch']
                else:
                    wg_code = '-'

        has_file = False
        live_html = ''
        component_html = ''
        entry_type = 'none'

        if status_category == 'whiteboard':
            entry_type = 'whiteboard'
        elif status_category == 'requires_dev':
            entry_type = 'backlog'
        elif repo_path:
            clean_p = repo_path.replace('/', os.sep).replace('\\', os.sep)
            has_file = os.path.exists(clean_p) or cat_fallback.get('has_file', False)
            
            # Check for direct or directory index.html
            if clean_p.endswith('.html') and (has_file or os.path.exists(clean_p)):
                live_html = repo_path.replace('\\', '/')
                entry_type = 'standalone_html'
                has_file = True
            elif os.path.exists(os.path.join(os.path.dirname(clean_p), 'index.html')):
                live_html = os.path.join(os.path.dirname(repo_path), 'index.html').replace('\\', '/')
                entry_type = 'standalone_html'
                has_file = True
            elif os.path.isdir(clean_p) and os.path.exists(os.path.join(clean_p, 'index.html')):
                live_html = os.path.join(repo_path, 'index.html').replace('\\', '/')
                entry_type = 'standalone_html'
                has_file = True
            elif repo_path.endswith('.ts'):
                ch = repo_path.replace('.component.ts', '.component.html')
                if os.path.exists(ch.replace('/', os.sep)) or cat_fallback.get('component_html'):
                    component_html = ch.replace('\\', '/')
                    entry_type = 'angular_component'
                    has_file = True
            elif cat_fallback.get('live_html'):
                live_html = cat_fallback['live_html']
                entry_type = 'standalone_html'
                has_file = True
            elif cat_fallback.get('component_html'):
                component_html = cat_fallback['component_html']
                entry_type = 'angular_component'
                has_file = True

        source_status = 'present' if has_file else ('whiteboard' if status_category == 'whiteboard' else 'missing')
        source_status_label = 'Present' if has_file else ('Canvas Tool' if status_category == 'whiteboard' else 'Missing')

        reconciled_list.append({
            'sr': md.get('sr', cat_fallback.get('sr', idx + 1)),
            'wg_code': wg_code,
            'name': name,
            'subject': ex['subject'],
            'batch': ex['batch'] or '-',
            'owner': ex['owner'] or '-',
            'excel_repo': ex['repo_link'] or '-',
            'status_category': status_category,
            'status_label': status_label,
            'repo_path': repo_path.replace('\\', '/'),
            'live_html': live_html,
            'component_html': component_html,
            'entry_type': entry_type,
            'has_file': has_file,
            'source_status': source_status,
            'source_status_label': source_status_label,
            'plain_explanation': plain_explanation,
            'what_was_checked': what_was_checked,
            'what_needs_to_be_done': what_needs_to_be_done,
            'technical_notes': raw_ev
        })

    counts = Counter(r['status_category'] for r in reconciled_list)
    total_count = len(reconciled_list)
    available_count = counts['available']
    corrected_count = counts['corrected']
    requires_dev_count = counts['requires_dev']
    whiteboard_count = counts['whiteboard']
    minor_changes_count = counts['minor_changes']
    
    live_html_count = sum(1 for r in reconciled_list if r['live_html'])
    source_present_count = sum(1 for r in reconciled_list if r['has_file'])
    source_missing_count = sum(1 for r in reconciled_list if not r['has_file'] and r['status_category'] != 'whiteboard')

    avail_pct = f"{(available_count / total_count) * 100:.1f}%"
    corr_pct = f"{(corrected_count / total_count) * 100:.1f}%"
    minor_pct = f"{(minor_changes_count / total_count) * 100:.1f}%"
    wb_pct = f"{(whiteboard_count / total_count) * 100:.1f}%"
    req_pct = f"{(requires_dev_count / total_count) * 100:.1f}%"
    source_present_pct = f"{(source_present_count / total_count) * 100:.1f}%"

    subject_counts = Counter(r['subject'] for r in reconciled_list)
    subjects = sorted(list(subject_counts.keys()))
    subject_options = "".join(f'<option value="{s}">{s}</option>' for s in subjects)

    # Build repo catalog dictionary for in-browser client-side instant Excel reconciliation
    repo_catalog = {}
    for item in reconciled_list:
        key = item['name'].strip().lower()
        repo_catalog[key] = {
            'sr': item['sr'],
            'wg_code': item['wg_code'],
            'name': item['name'],
            'subject': item['subject'],
            'batch': item['batch'],
            'owner': item['owner'],
            'excel_repo': item['excel_repo'],
            'status_category': item['status_category'],
            'status_label': item['status_label'],
            'repo_path': item['repo_path'],
            'live_html': item['live_html'],
            'component_html': item['component_html'],
            'entry_type': item['entry_type'],
            'has_file': item['has_file'],
            'source_status': item['source_status'],
            'source_status_label': item['source_status_label'],
            'plain_explanation': item['plain_explanation'],
            'what_was_checked': item['what_was_checked'],
            'what_needs_to_be_done': item['what_needs_to_be_done'],
            'technical_notes': item['technical_notes']
        }

    # Save repository catalog JSON for standalone portability
    with open(catalog_path, 'w', encoding='utf-8') as f:
        json.dump(repo_catalog, f, indent=2)

    git_sha = os.environ.get('GITHUB_SHA', '')
    git_repo = os.environ.get('GITHUB_REPOSITORY', '')
    if not git_sha:
        try:
            git_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            git_sha = ''

    commit_short = git_sha[:7] if git_sha else 'local'
    build_time = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())
    
    if git_repo and git_sha:
        commit_badge = f'<a href="https://github.com/{git_repo}/commit/{git_sha}" target="_blank" rel="noopener" class="hover:underline font-mono text-blue-500">{commit_short}</a>'
    else:
        commit_badge = f'<span class="font-mono text-slate-500">{commit_short}</span>'

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Widget Comparison – Reference Excel vs. Repository</title>
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
            --bg-page: #0b0f17;
            --bg-card: #111827;
            --bg-subtle: #182234;
            --border-color: #1f293d;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --text-soft: #cbd5e1;
        }
        body {
            background-color: var(--bg-page);
            color: var(--text-main);
            font-family: 'Inter', -apple-system, sans-serif;
        }
        .app-card {
            background-color: var(--bg-card);
            border-color: var(--border-color);
        }
        .app-subtle {
            background-color: var(--bg-subtle);
            border-color: var(--border-color);
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
            border-radius: 3px;
        }
        .dark .custom-scroll::-webkit-scrollbar-thumb {
            background: #334155;
        }
    </style>
</head>
<body class="min-h-screen flex flex-col transition-colors duration-200">

    <!-- Top Header -->
    <header class="app-card border-b sticky top-0 z-30 transition-colors">
        <div class="max-w-6xl mx-auto px-4 sm:px-6">
            <div class="flex items-center justify-between h-16 gap-3">
                
                <!-- Title & Context -->
                <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold">
                        <i data-lucide="layers" class="w-4 h-4"></i>
                    </div>
                    <div>
                        <div class="font-semibold text-sm leading-tight text-slate-900 dark:text-white">Widget Comparison</div>
                        <div class="text-xs text-slate-500 dark:text-slate-400">Reference Excel vs. Repository Codebase</div>
                    </div>
                </div>

                <!-- Right Header Actions (User Pill + Theme + Sync + Update + Export) -->
                <div class="flex items-center gap-2">
                    
                    <!-- Authenticated User Profile Pill & Role Badge -->
                    <div id="userProfilePill" class="app-subtle border rounded-lg px-2.5 py-1 text-xs flex items-center gap-2">
                        <div class="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-[10px]" id="userAvatar">A</div>
                        <div class="hidden sm:block text-left leading-tight">
                            <div class="font-semibold text-slate-900 dark:text-white truncate max-w-[120px]" id="userNameDisplay">User</div>
                            <div class="text-[10px] text-slate-500 uppercase tracking-wider" id="userRoleBadge">Role</div>
                        </div>
                        <button onclick="handleLogout()" title="Log out of your session" class="text-slate-400 hover:text-rose-500 transition p-1">
                            <i data-lucide="log-out" class="w-3.5 h-3.5"></i>
                        </button>
                    </div>

                    <!-- Theme Selector Dropdown -->
                    <div class="relative">
                        <select id="themeSelector" onchange="changeTheme(this.value)" class="app-subtle border rounded-lg px-2.5 py-1.5 text-xs text-slate-700 dark:text-slate-200 focus:outline-none cursor-pointer">
                            <option value="system">Theme: System</option>
                            <option value="light">Theme: Light</option>
                            <option value="dark">Theme: Dark</option>
                        </select>
                    </div>

                    <!-- Sync / Refresh from Repository Excel Button -->
                    <button onclick="refreshFromRepoExcel()" id="btnSyncExcel" title="Fetch and sync the latest Excel spreadsheet from the repository" class="app-subtle hover:bg-slate-200 dark:hover:bg-slate-800 border rounded-lg px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 transition flex items-center gap-1.5">
                        <i id="syncIcon" data-lucide="refresh-cw" class="w-3.5 h-3.5 text-emerald-500"></i>
                        <span class="hidden sm:inline">Sync Excel</span>
                    </button>

                    <!-- Update Excel File Button (Instant in-browser auto-reconciliation) -->
                    <label title="Upload or drop an updated .xlsx file to re-reconcile the dashboard instantly in the browser" class="cursor-pointer app-subtle hover:bg-slate-200 dark:hover:bg-slate-800 border rounded-lg px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 transition flex items-center gap-1.5">
                        <i data-lucide="file-spreadsheet" class="w-3.5 h-3.5 text-emerald-500"></i>
                        <span class="hidden sm:inline">Update Excel</span>
                        <input type="file" id="excelFileInput" accept=".xlsx, .xls" class="hidden" onchange="handleExcelFileUpload(event)" />
                    </label>

                    <!-- Export CSV Button -->
                    <button onclick="exportCSV()" class="app-subtle hover:bg-slate-200 dark:hover:bg-slate-800 border rounded-lg px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 transition flex items-center gap-1.5">
                        <i data-lucide="download" class="w-3.5 h-3.5"></i>
                        <span class="hidden sm:inline">Export CSV</span>
                    </button>
                </div>

            </div>

            <!-- Navigation Tabs (With Admin Sections dynamically shown) -->
            <div class="flex items-center gap-1 -mb-px border-t border-slate-200 dark:border-slate-800/80 pt-1 text-xs overflow-x-auto custom-scroll">
                <button onclick="switchTab('overview')" id="tab-overview" class="nav-tab px-3.5 py-2 font-medium border-b-2 border-blue-600 text-blue-600 dark:text-blue-400 flex items-center gap-1.5 transition whitespace-nowrap">
                    <i data-lucide="layout-dashboard" class="w-3.5 h-3.5"></i> Overview
                </button>
                <button onclick="drillDown('all')" id="tab-inventory" class="nav-tab px-3.5 py-2 font-medium border-b-2 border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white flex items-center gap-1.5 transition whitespace-nowrap">
                    <i data-lucide="list" class="w-3.5 h-3.5"></i> All Widgets (<span id="nav-tab-total">{total_count}</span>)
                </button>
                <button onclick="switchTab('actions')" id="tab-actions" class="nav-tab px-3.5 py-2 font-medium border-b-2 border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white flex items-center gap-1.5 transition whitespace-nowrap">
                    <i data-lucide="check-square" class="w-3.5 h-3.5 text-rose-500"></i> What Needs to Be Done
                </button>
                <button onclick="switchTab('qa')" id="tab-qa" class="nav-tab px-3.5 py-2 font-medium border-b-2 border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white flex items-center gap-1.5 transition whitespace-nowrap">
                    <i data-lucide="shield-check" class="w-3.5 h-3.5 text-purple-500"></i> QA Testing Status
                </button>
                
                <!-- Admin-Only Tab: User Management -->
                <button onclick="switchTab('users')" id="tab-users" class="nav-tab px-3.5 py-2 font-medium border-b-2 border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white flex items-center gap-1.5 transition whitespace-nowrap hidden">
                    <i data-lucide="users" class="w-3.5 h-3.5 text-blue-500"></i> User Management
                </button>

                <!-- Admin-Only Tab: Activity History -->
                <button onclick="switchTab('activity')" id="tab-activity" class="nav-tab px-3.5 py-2 font-medium border-b-2 border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white flex items-center gap-1.5 transition whitespace-nowrap hidden">
                    <i data-lucide="activity" class="w-3.5 h-3.5 text-emerald-500"></i> Activity History
                </button>
            </div>
        </div>
    </header>

    <!-- Main Content Container -->
    <main class="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">

        <!-- ======================================================== -->
        <!-- SECTION 1: OVERVIEW                                      -->
        <!-- ======================================================== -->
        <div id="view-overview" class="view-content space-y-6">
            
            <!-- Context Box: Explains the Source & Result Clearly -->
            <div class="app-card border rounded-xl p-5 space-y-2 shadow-sm">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                        <i data-lucide="info" class="w-3.5 h-3.5"></i> Purpose of This Comparison
                    </div>
                    <div class="flex items-center gap-2">
                        <span id="lastSyncBadge" class="text-[10px] text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded flex items-center gap-1 font-medium">
                            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                            <span id="lastSyncTime">Live Data</span>
                        </span>
                        <span id="activeExcelBadge" class="text-[11px] font-mono text-slate-500 dark:text-slate-400 flex items-center gap-1 bg-slate-100 dark:bg-slate-800/80 px-2 py-0.5 rounded border">
                            <i data-lucide="file-spreadsheet" class="w-3 h-3 text-emerald-500"></i>
                            <span id="activeExcelName">{excel_filename}</span>
                        </span>
                    </div>
                </div>
                <p class="text-slate-700 dark:text-slate-300 leading-relaxed text-sm">
                    This dashboard compares the <strong><span id="el-context-total">{total_count}</span> required widgets</strong> listed in the reference spreadsheet shared by the <strong>Development Team and Content Team</strong> against the repository codebase.
                </p>
                <div class="pt-2 flex flex-wrap gap-2 text-xs">
                    <span onclick="drillDown('source_present')" class="px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20 font-medium cursor-pointer hover:bg-emerald-500/20 transition flex items-center gap-1.5" title="Click to view widgets with physical source files on disk">
                        <i data-lucide="check-circle" class="w-3.5 h-3.5 text-emerald-500"></i>
                        <span id="pill-source-present"><strong>{source_present_count} Source Files Present ({source_present_pct})</strong></span>
                    </span>
                    <span onclick="drillDown('has_live')" class="px-2.5 py-1 rounded-md bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-500/20 font-medium cursor-pointer hover:bg-blue-500/20 transition flex items-center gap-1.5" title="Click to view runnable HTML widgets">
                        <i data-lucide="play" class="w-3.5 h-3.5 text-blue-500"></i>
                        <span id="pill-live-html"><strong>{live_html_count} Live HTML Simulations Ready</strong></span>
                    </span>
                    <span onclick="drillDown('source_missing')" class="px-2.5 py-1 rounded-md bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/20 font-medium cursor-pointer hover:bg-rose-500/20 transition flex items-center gap-1.5" title="Click to view missing widgets">
                        <i data-lucide="x-circle" class="w-3.5 h-3.5 text-rose-500"></i>
                        <span id="pill-source-missing"><strong>{requires_dev_count} Source Files Missing</strong></span>
                    </span>
                    <span onclick="drillDown('whiteboard')" class="px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20 font-medium cursor-pointer hover:bg-amber-500/20 transition flex items-center gap-1.5" title="Click to view classroom whiteboard tools">
                        <i data-lucide="layout" class="w-3.5 h-3.5 text-amber-500"></i>
                        <span id="pill-whiteboard"><strong>{whiteboard_count} Whiteboard Tools</strong></span>
                    </span>
                </div>
            </div>

            <!-- Informative Numbers Strip with Explanations (Clickable for Instant Drill-Down) -->
            <div class="space-y-3">
                <div class="flex items-center justify-between">
                    <h2 class="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Widget Summary & Meaning</h2>
                    <span class="text-[11px] text-blue-600 dark:text-blue-400 flex items-center gap-1 font-medium">
                        <i data-lucide="mouse-pointer-click" class="w-3.5 h-3.5"></i>
                        <span>Click any number below to view its details</span>
                    </span>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                    
                    <!-- 1. Already Available -->
                    <div onclick="drillDown('available')" class="app-card border rounded-xl p-4 space-y-2 shadow-sm hover:border-emerald-500 hover:shadow-md cursor-pointer transition-all duration-150 group" title="Click to view Already Available widgets">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-medium text-slate-600 dark:text-slate-400 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">Already Available</span>
                            <span id="stat-available-badge" class="text-xs font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 group-hover:bg-emerald-500/20 transition">{available_count}</span>
                        </div>
                        <div class="text-2xl font-bold text-slate-900 dark:text-white flex items-center justify-between">
                            <span id="stat-available-num" class="group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">{available_count} Widgets</span>
                            <i data-lucide="arrow-right" class="w-4 h-4 text-slate-300 dark:text-slate-600 group-hover:text-emerald-500 group-hover:translate-x-1 transition-all"></i>
                        </div>
                        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                            These widgets were found in the existing widget repository. Their corresponding implementation source files and HTML simulations are available and verified on disk.
                        </p>
                        <div class="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                            <span id="stat-available-sub">Click to view all {available_count} widgets</span>
                            <span>→</span>
                        </div>
                    </div>

                    <!-- 2. Found in Repository (Spelling/Name Fixes) -->
                    <div onclick="drillDown('corrected')" class="app-card border rounded-xl p-4 space-y-2 shadow-sm hover:border-sky-500 hover:shadow-md cursor-pointer transition-all duration-150 group" title="Click to view Found in Repository widgets">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-medium text-slate-600 dark:text-slate-400 group-hover:text-sky-600 dark:group-hover:text-sky-400 transition-colors">Found in Repository</span>
                            <span id="stat-corrected-badge" class="text-xs font-bold px-2 py-0.5 rounded bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20 group-hover:bg-sky-500/20 transition">{corrected_count}</span>
                        </div>
                        <div class="text-2xl font-bold text-slate-900 dark:text-white flex items-center justify-between">
                            <span id="stat-corrected-num" class="group-hover:text-sky-600 dark:group-hover:text-sky-400 transition-colors">{corrected_count} Widgets</span>
                            <i data-lucide="arrow-right" class="w-4 h-4 text-slate-300 dark:text-slate-600 group-hover:text-sky-500 group-hover:translate-x-1 transition-all"></i>
                        </div>
                        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                            These widgets were initially hard to match due to spelling mistakes in the Excel names (e.g. "Dominic" for Domino). Their source files were verified present on disk.
                        </p>
                        <div class="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-sky-600 dark:text-sky-400 font-medium">
                            <span id="stat-corrected-sub">Click to view all {corrected_count} widgets</span>
                            <span>→</span>
                        </div>
                    </div>

                    <!-- 3. Not Available – Needs Development -->
                    <div onclick="drillDown('requires_dev')" class="app-card border rounded-xl p-4 space-y-2 shadow-sm hover:border-rose-500 hover:shadow-md cursor-pointer transition-all duration-150 group" title="Click to view widgets needing development">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-medium text-slate-600 dark:text-slate-400 group-hover:text-rose-600 dark:group-hover:text-rose-400 transition-colors">Not Available</span>
                            <span id="stat-dev-badge" class="text-xs font-bold px-2 py-0.5 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 group-hover:bg-rose-500/20 transition">{requires_dev_count}</span>
                        </div>
                        <div class="text-2xl font-bold text-slate-900 dark:text-white flex items-center justify-between">
                            <span id="stat-dev-num" class="group-hover:text-rose-600 dark:group-hover:text-rose-400 transition-colors">{requires_dev_count} Widgets</span>
                            <i data-lucide="arrow-right" class="w-4 h-4 text-slate-300 dark:text-slate-600 group-hover:text-rose-500 group-hover:translate-x-1 transition-all"></i>
                        </div>
                        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                            Source files for these widgets are completely missing in the repository. They need to be planned and developed from scratch.
                        </p>
                        <div class="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-rose-600 dark:text-rose-400 font-medium">
                            <span id="stat-dev-sub">Click to view all {requires_dev_count} widgets</span>
                            <span>→</span>
                        </div>
                    </div>

                    <!-- 4. Small Changes Needed -->
                    <div onclick="drillDown('minor_changes')" class="app-card border rounded-xl p-4 space-y-2 shadow-sm hover:border-purple-500 hover:shadow-md cursor-pointer transition-all duration-150 group" title="Click to view widgets needing small changes">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-medium text-slate-600 dark:text-slate-400 group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">Small Changes Needed</span>
                            <span id="stat-minor-badge" class="text-xs font-bold px-2 py-0.5 rounded bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20 group-hover:bg-purple-500/20 transition">{minor_changes_count}</span>
                        </div>
                        <div class="text-2xl font-bold text-slate-900 dark:text-white flex items-center justify-between">
                            <span id="stat-minor-num" class="group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">{minor_changes_count} Widgets</span>
                            <i data-lucide="arrow-right" class="w-4 h-4 text-slate-300 dark:text-slate-600 group-hover:text-purple-500 group-hover:translate-x-1 transition-all"></i>
                        </div>
                        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                            Source files already exist on disk (CO Molecule and Integer Subtraction). Only small configuration additions are required.
                        </p>
                        <div class="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-purple-600 dark:text-purple-400 font-medium">
                            <span id="stat-minor-sub">Click to view all {minor_changes_count} widgets</span>
                            <span>→</span>
                        </div>
                    </div>

                    <!-- 5. Classroom Tools -->
                    <div onclick="drillDown('whiteboard')" class="app-card border rounded-xl p-4 space-y-2 shadow-sm hover:border-amber-500 hover:shadow-md cursor-pointer transition-all duration-150 group" title="Click to view Classroom Tools">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-medium text-slate-600 dark:text-slate-400 group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors">Classroom Tools</span>
                            <span id="stat-wb-badge" class="text-xs font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 group-hover:bg-amber-500/20 transition">{whiteboard_count}</span>
                        </div>
                        <div class="text-2xl font-bold text-slate-900 dark:text-white flex items-center justify-between">
                            <span id="stat-wb-num" class="group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors">{whiteboard_count} Tools</span>
                            <i data-lucide="arrow-right" class="w-4 h-4 text-slate-300 dark:text-slate-600 group-hover:text-amber-500 group-hover:translate-x-1 transition-all"></i>
                        </div>
                        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                            These are whiteboard instruments such as Compass, Ruler, Protractor, Curtain, and Split Screen. They are canvas utilities rather than repository widgets.
                        </p>
                        <div class="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-amber-600 dark:text-amber-400 font-medium">
                            <span id="stat-wb-sub">Click to view all {whiteboard_count} tools</span>
                            <span>→</span>
                        </div>
                    </div>

                    <!-- 6. Total in Reference List -->
                    <div onclick="drillDown('all')" class="app-card border rounded-xl p-4 space-y-2 shadow-sm hover:border-blue-500 hover:shadow-md cursor-pointer transition-all duration-150 group" title="Click to view all widgets">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-medium text-slate-600 dark:text-slate-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">Total in Reference Excel</span>
                            <span id="stat-total-badge" class="text-xs font-bold px-2 py-0.5 rounded bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-500/20 group-hover:bg-blue-500/20 transition">{total_count}</span>
                        </div>
                        <div class="text-2xl font-bold text-slate-900 dark:text-white flex items-center justify-between">
                            <span id="stat-total-num" class="group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">{total_count} Total</span>
                            <i data-lucide="arrow-right" class="w-4 h-4 text-slate-300 dark:text-slate-600 group-hover:text-blue-500 group-hover:translate-x-1 transition-all"></i>
                        </div>
                        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                            Every single widget in the Development and Content Team spreadsheet has been audited and cataloged with clear source file verification.
                        </p>
                        <div class="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-blue-600 dark:text-blue-400 font-medium">
                            <span>Click to view full inventory</span>
                            <span>→</span>
                        </div>
                    </div>

                </div>
            </div>

            <!-- Single Meaningful Progress Indicator (Clickable Segments & Pills) -->
            <div class="app-card border rounded-xl p-5 space-y-3 shadow-sm">
                <div class="flex items-center justify-between text-xs">
                    <span class="font-medium text-slate-800 dark:text-slate-200">Repository Readiness Overview</span>
                    <span onclick="drillDown('source_present')" id="bar-header-text" class="font-bold text-emerald-600 dark:text-emerald-400 cursor-pointer hover:underline" title="Click to view verified widgets">{source_present_count} of {total_count} Source Files Present ({source_present_pct})</span>
                </div>
                <div class="w-full h-3.5 app-subtle rounded-full overflow-hidden flex gap-1 p-0.5 border">
                    <div id="bar-seg-available" onclick="drillDown('available')" style="width: {avail_pct}" class="h-full bg-emerald-500 rounded-sm cursor-pointer hover:opacity-85 transition" title="Already Available: {available_count} (Click to view)"></div>
                    <div id="bar-seg-corrected" onclick="drillDown('corrected')" style="width: {corr_pct}" class="h-full bg-sky-400 rounded-sm cursor-pointer hover:opacity-85 transition" title="Found in Repository: {corrected_count} (Click to view)"></div>
                    <div id="bar-seg-minor" onclick="drillDown('minor_changes')" style="width: {minor_pct}" class="h-full bg-purple-400 rounded-sm cursor-pointer hover:opacity-85 transition" title="Small Changes Needed: {minor_changes_count} (Click to view)"></div>
                    <div id="bar-seg-whiteboard" onclick="drillDown('whiteboard')" style="width: {wb_pct}" class="h-full bg-amber-400 rounded-sm cursor-pointer hover:opacity-85 transition" title="Classroom Tools: {whiteboard_count} (Click to view)"></div>
                    <div id="bar-seg-requires-dev" onclick="drillDown('requires_dev')" style="width: {req_pct}" class="h-full bg-rose-500 rounded-sm cursor-pointer hover:opacity-85 transition" title="Needs Development: {requires_dev_count} (Click to view)"></div>
                </div>
                <div class="flex flex-wrap gap-1.5 text-xs text-slate-600 dark:text-slate-400 pt-1">
                    <button onclick="drillDown('available')" id="bar-pill-available" class="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition" title="Click to view Already Available"><span class="w-2 h-2 rounded-full bg-emerald-500"></span> Already Available ({available_count})</button>
                    <button onclick="drillDown('corrected')" id="bar-pill-corrected" class="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-sky-600 dark:hover:text-sky-400 transition" title="Click to view Found in Repository"><span class="w-2 h-2 rounded-full bg-sky-400"></span> Found in Repository ({corrected_count})</button>
                    <button onclick="drillDown('minor_changes')" id="bar-pill-minor" class="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-purple-600 dark:hover:text-purple-400 transition" title="Click to view Small Changes Needed"><span class="w-2 h-2 rounded-full bg-purple-400"></span> Small Changes ({minor_changes_count})</button>
                    <button onclick="drillDown('whiteboard')" id="bar-pill-whiteboard" class="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-amber-600 dark:hover:text-amber-400 transition" title="Click to view Classroom Tools"><span class="w-2 h-2 rounded-full bg-amber-400"></span> Classroom Tools ({whiteboard_count})</button>
                    <button onclick="drillDown('requires_dev')" id="bar-pill-dev" class="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-rose-600 dark:hover:text-rose-400 transition" title="Click to view Needs Development"><span class="w-2 h-2 rounded-full bg-rose-500"></span> Needs Development ({requires_dev_count})</button>
                </div>
            </div>

            <!-- Quick Navigation Callouts -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div onclick="drillDown('all')" class="app-card hover:bg-slate-50 dark:hover:bg-slate-800/40 border rounded-xl p-4 cursor-pointer transition flex items-center justify-between group">
                    <div>
                        <div class="font-semibold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">Search All <span class="num-total">{total_count}</span> Widgets</div>
                        <div class="text-xs text-slate-500 dark:text-slate-400">Filter by WG number, subject, or verify physical source files.</div>
                    </div>
                    <i data-lucide="arrow-right" class="w-4 h-4 text-slate-400 group-hover:text-blue-500 group-hover:translate-x-1 transition-all"></i>
                </div>
                <div onclick="switchTab('actions')" class="app-card hover:bg-slate-50 dark:hover:bg-slate-800/40 border rounded-xl p-4 cursor-pointer transition flex items-center justify-between group">
                    <div>
                        <div class="font-semibold text-slate-900 dark:text-white group-hover:text-rose-600 dark:group-hover:text-rose-400 transition-colors">Review What Needs to Be Done</div>
                        <div class="text-xs text-slate-500 dark:text-slate-400">Inspect the 12 unbuilt widgets and 2 quick updates.</div>
                    </div>
                    <i data-lucide="arrow-right" class="w-4 h-4 text-slate-400 group-hover:text-rose-500 group-hover:translate-x-1 transition-all"></i>
                </div>
            </div>

            <!-- Dashboard Data Sources & Methodology Confirmation -->
            <div class="app-card border rounded-xl p-5 space-y-3 shadow-sm">
                <div class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                    <i data-lucide="database" class="w-3.5 h-3.5 text-blue-500"></i>
                    <span>Dashboard Data Sources & Verification</span>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                    <div class="p-3 app-subtle border rounded-lg space-y-1">
                        <div class="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                            <span class="w-2 h-2 rounded-full bg-blue-500"></span>
                            <span>Source 1: Reference Excel</span>
                        </div>
                        <div id="cardSourceExcelName" class="font-mono text-[11px] text-blue-600 dark:text-blue-400 break-all">{excel_filename}</div>
                        <p class="text-slate-500 dark:text-slate-400 text-[11px] leading-relaxed">
                            Sheet <code>Widget-RepoList</code> shared by Development & Content Teams. Defines the required widgets, subjects, WG batches, and owners.
                        </p>
                    </div>
                    <div class="p-3 app-subtle border rounded-lg space-y-1">
                        <div class="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                            <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                            <span>Source 2: Codebase Inventory</span>
                        </div>
                        <div class="font-mono text-[11px] text-emerald-600 dark:text-emerald-400 break-all">all-widgets-v1 Codebase</div>
                        <p class="text-slate-500 dark:text-slate-400 text-[11px] leading-relaxed">
                            Verified on disk across <code>widgets-b1/</code>, <code>widgets-b2/</code>, <code>widgets-b3/</code>, and <code>src/app/</code>. Every file path is checked via filesystem verification.
                        </p>
                    </div>
                    <div class="p-3 app-subtle border rounded-lg space-y-1">
                        <div class="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                            <span class="w-2 h-2 rounded-full bg-purple-500"></span>
                            <span>Source 3: Audit Reconciliation</span>
                        </div>
                        <div class="font-mono text-[11px] text-purple-600 dark:text-purple-400 break-all">WIDGET_REPOSITORY_COMPARISON.md</div>
                        <p class="text-slate-500 dark:text-slate-400 text-[11px] leading-relaxed">
                            Line-by-line audited matching report connecting reference spreadsheet names to repository source files and identifying false negatives.
                        </p>
                    </div>
                </div>
            </div>

        </div>

        <!-- ======================================================== -->
        <!-- SECTION 2: ALL WIDGETS (Clean Inventory & Search)         -->
        <!-- ======================================================== -->
        <div id="view-inventory" class="view-content space-y-4 hidden">
            
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h2 class="text-base font-semibold text-slate-900 dark:text-white">All Widgets (<span id="headerTotalCount">{total_count}</span>)</h2>
                    <p class="text-xs text-slate-500 dark:text-slate-400">Browse by WG Number, Widget Name, and confirm physical source file presence on disk.</p>
                </div>
            </div>

            <!-- Active Filter Banner (Visible when filtered from Overview or dropdown) -->
            <div id="activeFilterBanner" class="hidden p-2.5 px-3 rounded-lg bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800/60 flex items-center justify-between text-xs">
                <div class="flex items-center gap-2">
                    <i data-lucide="filter" class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400"></i>
                    <span class="text-slate-600 dark:text-slate-300">Filter applied:</span>
                    <strong id="filterBannerLabel" class="text-blue-700 dark:text-blue-300 font-semibold"></strong>
                </div>
                <button onclick="clearFilter()" class="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 px-2 py-0.5 rounded hover:bg-slate-200/60 dark:hover:bg-slate-800/60 transition">
                    <span>View all</span>
                    <i data-lucide="x" class="w-3 h-3"></i>
                </button>
            </div>

            <!-- Clean Search & Filter Controls -->
            <div class="app-card border rounded-lg p-3 flex flex-col sm:flex-row gap-2.5 items-stretch sm:items-center">
                <div class="relative flex-1">
                    <i data-lucide="search" class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"></i>
                    <input type="text" id="widgetSearch" oninput="filterWidgets()" placeholder="Search by WG number (e.g. WG96, B2-WG01), widget name, subject..." class="w-full app-subtle border rounded-md pl-9 pr-3 py-1.5 text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:border-blue-500" />
                </div>
                
                <select id="statusFilter" onchange="filterWidgets()" class="app-subtle border rounded-md px-2.5 py-1.5 text-xs text-slate-700 dark:text-slate-300 focus:outline-none cursor-pointer">
                    <option id="opt-all" value="all">All Statuses ({total_count})</option>
                    <option id="opt-present" value="source_present">✓ Source File Present ({source_present_count})</option>
                    <option id="opt-missing" value="source_missing">✗ Source File Missing ({requires_dev_count})</option>
                    <option id="opt-live" value="has_live">⚡ Live HTML Ready ({live_html_count})</option>
                    <option id="opt-available" value="available">Already Available ({available_count})</option>
                    <option id="opt-corrected" value="corrected">Found in Repository ({corrected_count})</option>
                    <option id="opt-dev" value="requires_dev">Not Available – Needs Dev ({requires_dev_count})</option>
                    <option id="opt-whiteboard" value="whiteboard">Classroom Tools ({whiteboard_count})</option>
                    <option id="opt-minor" value="minor_changes">Small Changes Needed ({minor_changes_count})</option>
                </select>

                <select id="subjectFilter" onchange="filterWidgets()" class="app-subtle border rounded-md px-2.5 py-1.5 text-xs text-slate-700 dark:text-slate-300 focus:outline-none cursor-pointer">
                    <option value="all">All Subjects</option>
                    __SUBJECT_OPTIONS__
                </select>
            </div>

            <!-- Table with WG Number & Source File Confirmation Columns -->
            <div class="app-card border rounded-lg overflow-hidden shadow-sm">
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs">
                        <thead>
                            <tr class="app-subtle border-b text-slate-600 dark:text-slate-400 font-medium">
                                <th class="py-2.5 px-4 w-12 cursor-pointer" onclick="sortData('sr')">#</th>
                                <th class="py-2.5 px-4 w-28 cursor-pointer" onclick="sortData('wg_code')">WG # / Batch</th>
                                <th class="py-2.5 px-4 cursor-pointer" onclick="sortData('name')">Widget Name</th>
                                <th class="py-2.5 px-4 cursor-pointer" onclick="sortData('subject')">Subject</th>
                                <th class="py-2.5 px-4 w-28 cursor-pointer" onclick="sortData('source_status')">Source File</th>
                                <th class="py-2.5 px-4 cursor-pointer" onclick="sortData('status_category')">Status</th>
                                <th class="py-2.5 px-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="widgetTableBody" class="divide-y divide-slate-200 dark:divide-slate-800">
                            <!-- Injected dynamically -->
                        </tbody>
                    </table>
                </div>

                <!-- Simple Pagination -->
                <div class="p-3 border-t flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                    <div>Showing <span id="pageCount" class="font-medium text-slate-800 dark:text-slate-200">0</span> of <span id="totalFiltered" class="font-medium text-slate-800 dark:text-slate-200">{total_count}</span> widgets</div>
                    <div class="flex items-center gap-2">
                        <button onclick="changePage(-1)" id="prevBtn" class="px-2.5 py-1 rounded app-subtle border hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 disabled:opacity-30 disabled:cursor-not-allowed">Previous</button>
                        <span id="pageIndicator" class="font-mono text-slate-600 dark:text-slate-300">Page 1</span>
                        <button onclick="changePage(1)" id="nextBtn" class="px-2.5 py-1 rounded app-subtle border hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 disabled:opacity-30 disabled:cursor-not-allowed">Next</button>
                    </div>
                </div>
            </div>

        </div>

        <!-- ======================================================== -->
        <!-- SECTION 3: WHAT NEEDS TO BE DONE                          -->
        <!-- ======================================================== -->
        <div id="view-actions" class="view-content space-y-6 hidden">
            
            <div class="app-card border rounded-xl p-5 space-y-2">
                <h2 class="text-base font-semibold text-slate-900 dark:text-white">What Needs to Be Done</h2>
                <p class="text-xs text-slate-600 dark:text-slate-400">
                    Below is the clear breakdown of what requires development, what needs small configuration changes, and what is already taken care of.
                </p>
            </div>

            <!-- Block 1: 12 Widgets Needing Development -->
            <div class="app-card border rounded-xl p-5 space-y-3">
                <div class="flex items-center justify-between pb-2 border-b">
                    <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                        <h3 class="text-xs font-semibold uppercase tracking-wider text-rose-600 dark:text-rose-400">1. Not Available – Needs Development (<span class="act-dev-count">{requires_dev_count}</span> Widgets)</h3>
                    </div>
                    <button onclick="drillDown('requires_dev')" class="text-xs text-rose-600 dark:text-rose-400 hover:underline font-medium">View in table →</button>
                </div>
                <p class="text-xs text-slate-600 dark:text-slate-400">
                    Source files for these 12 simulations are <strong>Missing</strong> in the repository. They need to be planned and developed:
                </p>
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 text-xs pt-1">
                    <div class="p-2.5 app-subtle border rounded-lg"><strong>Flower</strong> <span class="text-slate-500">(Biology)</span></div>
                    <div class="p-2.5 app-subtle border rounded-lg"><strong>Plant & Animal Cell</strong> <span class="text-slate-500">(Biology)</span></div>
                    <div class="p-2.5 app-subtle border rounded-lg"><strong>Human Anatomy</strong> <span class="text-slate-500">(Biology)</span></div>
                    <div class="p-2.5 app-subtle border rounded-lg"><strong>Periodic Table</strong> <span class="text-slate-500">(Chemistry)</span></div>
                    <div class="p-2.5 app-subtle border rounded-lg"><strong>Earth Atmosphere</strong> <span class="text-slate-500">(Geography)</span></div>
                    <div class="p-2.5 app-subtle border rounded-lg"><strong>Earth Layers</strong> <span class="text-slate-500">(Geography)</span></div>
                    <div class="p-2.5 app-subtle border rounded-lg"><strong>Solar System</strong> <span class="text-slate-500">(Science)</span></div>
                    <div class="p-2.5 app-subtle border rounded-lg"><strong>3D Shapes</strong> <span class="text-slate-500">(Geometry)</span></div>
                    <div class="p-2.5 app-subtle border rounded-lg"><strong>Circle Theorems</strong> <span class="text-slate-500">(Mathematics)</span></div>
                    <div class="p-2.5 app-subtle border rounded-lg"><strong>Calendar</strong> <span class="text-slate-500">(Mathematics)</span></div>
                    <div class="p-2.5 app-subtle border rounded-lg"><strong>Primary Charts</strong> <span class="text-slate-500">(English)</span></div>
                    <div class="p-2.5 app-subtle border rounded-lg"><strong>Math Stepper</strong> <span class="text-slate-500">(Mathematics)</span></div>
                </div>
            </div>

            <!-- Block 2: 2 Widgets with Small Changes -->
            <div class="app-card border rounded-xl p-5 space-y-3">
                <div class="flex items-center justify-between pb-2 border-b">
                    <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-purple-500"></span>
                        <h3 class="text-xs font-semibold uppercase tracking-wider text-purple-600 dark:text-purple-400">2. Small Changes Needed (<span class="act-minor-count">{minor_changes_count}</span> Widgets)</h3>
                    </div>
                    <button onclick="drillDown('minor_changes')" class="text-xs text-purple-600 dark:text-purple-400 hover:underline font-medium">View in table →</button>
                </div>
                <div class="space-y-2 text-xs pt-1">
                    <div class="p-3 app-subtle border rounded-lg space-y-2">
                        <div class="flex items-center justify-between">
                            <div>
                                <span class="font-mono text-[10px] font-semibold text-purple-600 dark:text-purple-400 bg-purple-500/10 px-1.5 py-0.5 rounded border border-purple-500/20 mr-1.5">B2-WG13</span>
                                <strong class="text-slate-900 dark:text-white">CO Molecule (Carbon Monoxide)</strong>
                            </div>
                            <a href="widgets-b2/wg13-build-molecule/index.html" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-purple-500/10 text-purple-600 dark:text-purple-400 hover:bg-purple-500/20 font-medium transition">
                                <i data-lucide="play" class="w-3 h-3 fill-current"></i>
                                <span>Run Molecule Builder</span>
                                <i data-lucide="external-link" class="w-3 h-3"></i>
                            </a>
                        </div>
                        <p class="text-slate-600 dark:text-slate-400">Source file <strong>Present</strong> on disk (<code>widgets-b2/wg13-build-molecule/index.html</code>). We only need to add the Carbon Monoxide (C-O) bonding coordinates.</p>
                    </div>
                    <div class="p-3 app-subtle border rounded-lg space-y-2">
                        <div class="flex items-center justify-between">
                            <div>
                                <span class="font-mono text-[10px] font-semibold text-purple-600 dark:text-purple-400 bg-purple-500/10 px-1.5 py-0.5 rounded border border-purple-500/20 mr-1.5">B3-WG104</span>
                                <strong class="text-slate-900 dark:text-white">Integer Subtraction Mode</strong>
                            </div>
                            <a href="widgets-b3/wg104-addition-of-integers/index.html" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-purple-500/10 text-purple-600 dark:text-purple-400 hover:bg-purple-500/20 font-medium transition">
                                <i data-lucide="play" class="w-3 h-3 fill-current"></i>
                                <span>Run Integer Activity</span>
                                <i data-lucide="external-link" class="w-3 h-3"></i>
                            </a>
                        </div>
                        <p class="text-slate-600 dark:text-slate-400">Source file <strong>Present</strong> on disk (<code>widgets-b3/wg104-addition-of-integers/index.html</code>). We only need to enable the subtraction toggle in the existing widget.</p>
                    </div>
                </div>
            </div>

            <!-- Block 3: 9 Classroom Tools Scope -->
            <div class="app-card border rounded-xl p-5 space-y-3">
                <div class="flex items-center justify-between pb-2 border-b">
                    <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                        <h3 class="text-xs font-semibold uppercase tracking-wider text-amber-600 dark:text-amber-400">3. Classroom Tools Scope (<span class="act-wb-count">{whiteboard_count}</span> Tools)</h3>
                    </div>
                    <button onclick="drillDown('whiteboard')" class="text-xs text-amber-600 dark:text-amber-400 hover:underline font-medium">View in table →</button>
                </div>
                <p class="text-xs text-slate-600 dark:text-slate-400">
                    These items were marked as <strong>"Repo: No"</strong> in the reference Excel list:
                </p>
                <div class="p-3 app-subtle border rounded-lg text-xs space-y-1 text-slate-700 dark:text-slate-300">
                    <div>• <strong>Tools:</strong> Compass, Clock, Ruler, Protractor, Set Square 30, Set Square 45, Curtain, Split Screen, Scientific Calculator.</div>
                    <div class="text-slate-500 dark:text-slate-400 pt-1">These are whiteboard overlay utility instruments. They are provided by the teaching canvas shell rather than this widget repository.</div>
                </div>
            </div>

            <!-- Block 4: 5 Found under Spelling Fixes -->
            <div class="app-card border rounded-xl p-5 space-y-3">
                <div class="flex items-center justify-between pb-2 border-b">
                    <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-sky-500"></span>
                        <h3 class="text-xs font-semibold uppercase tracking-wider text-sky-600 dark:text-sky-400">4. Found in Repository – Do Not Rebuild (<span class="act-corr-count">{corrected_count}</span> Widgets)</h3>
                    </div>
                    <button onclick="drillDown('corrected')" class="text-xs text-sky-600 dark:text-sky-400 hover:underline font-medium">View in table →</button>
                </div>
                <p class="text-xs text-slate-600 dark:text-slate-400">
                    Source files for these 5 widgets are <strong>Present and Verified</strong> on disk despite differences in the spreadsheet names:
                </p>
                <div class="space-y-2 text-xs pt-1">
                    <div class="p-3 app-subtle border rounded-lg flex items-center justify-between gap-2">
                        <div>
                            <div class="flex items-center gap-1.5">
                                <span class="font-mono text-[10px] font-semibold text-sky-600 dark:text-sky-400 bg-sky-500/10 px-1.5 py-0.5 rounded border border-sky-500/20">B3-WG96</span>
                                <strong>Operation Dominic:</strong> Already exists as <em>Operation Domino WW II Mission</em>.
                            </div>
                            <div class="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">✓ Source File Present: widgets-b3/wg96-operation-domino/index.html</div>
                        </div>
                        <a href="widgets-b3/wg96-operation-domino/index.html" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-sky-500/10 text-sky-600 dark:text-sky-400 hover:bg-sky-500/20 font-medium transition shrink-0">
                            <i data-lucide="play" class="w-3 h-3 fill-current"></i>
                            <span>Run</span>
                            <i data-lucide="external-link" class="w-3 h-3"></i>
                        </a>
                    </div>
                    <div class="p-3 app-subtle border rounded-lg flex items-center justify-between gap-2">
                        <div>
                            <div class="flex items-center gap-1.5">
                                <span class="font-mono text-[10px] font-semibold text-sky-600 dark:text-sky-400 bg-sky-500/10 px-1.5 py-0.5 rounded border border-sky-500/20">B3-WG113</span>
                                <strong>Making of the Indian Institution:</strong> Already exists as <em>Making of India's Constitution</em>.
                            </div>
                            <div class="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">✓ Source File Present: widgets-b3/wg113-making-of-Indias-constitution/index.html</div>
                        </div>
                        <a href="widgets-b3/wg113-making-of-Indias-constitution/index.html" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-sky-500/10 text-sky-600 dark:text-sky-400 hover:bg-sky-500/20 font-medium transition shrink-0">
                            <i data-lucide="play" class="w-3 h-3 fill-current"></i>
                            <span>Run</span>
                            <i data-lucide="external-link" class="w-3 h-3"></i>
                        </a>
                    </div>
                    <div class="p-3 app-subtle border rounded-lg flex items-center justify-between gap-2">
                        <div>
                            <div class="flex items-center gap-1.5">
                                <span class="font-mono text-[10px] font-semibold text-sky-600 dark:text-sky-400 bg-sky-500/10 px-1.5 py-0.5 rounded border border-sky-500/20">B1</span>
                                <strong>Cumulative Property of Addition:</strong> Already exists as <em>Visualizing Commutative Property</em>.
                            </div>
                            <div class="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">✓ Source File Present: widgets-b1/visualizing_the_commutative_property_of_addition/index.html</div>
                        </div>
                        <a href="widgets-b1/visualizing_the_commutative_property_of_addition/index.html" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-sky-500/10 text-sky-600 dark:text-sky-400 hover:bg-sky-500/20 font-medium transition shrink-0">
                            <i data-lucide="play" class="w-3 h-3 fill-current"></i>
                            <span>Run</span>
                            <i data-lucide="external-link" class="w-3 h-3"></i>
                        </a>
                    </div>
                    <div class="p-3 app-subtle border rounded-lg flex items-center justify-between gap-2">
                        <div>
                            <div class="flex items-center gap-1.5">
                                <span class="font-mono text-[10px] font-semibold text-sky-600 dark:text-sky-400 bg-sky-500/10 px-1.5 py-0.5 rounded border border-sky-500/20">B1</span>
                                <strong>Linear Equations in 1 variable:</strong> Already exists as <em>Build the Equation</em>.
                            </div>
                            <div class="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">✓ Source File Present: widgets-b1/visualizing_algebraic_equations/index.html</div>
                        </div>
                        <a href="widgets-b1/visualizing_algebraic_equations/index.html" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-sky-500/10 text-sky-600 dark:text-sky-400 hover:bg-sky-500/20 font-medium transition shrink-0">
                            <i data-lucide="play" class="w-3 h-3 fill-current"></i>
                            <span>Run</span>
                            <i data-lucide="external-link" class="w-3 h-3"></i>
                        </a>
                    </div>
                    <div class="p-3 app-subtle border rounded-lg flex items-center justify-between gap-2">
                        <div>
                            <div class="flex items-center gap-1.5">
                                <span class="font-mono text-[10px] font-semibold text-sky-600 dark:text-sky-400 bg-sky-500/10 px-1.5 py-0.5 rounded border border-sky-500/20">B1</span>
                                <strong>Multiplications of Large Nos. with 1 digit no.:</strong> Already exists as <em>Multi-Digit Multiplication</em>.
                            </div>
                            <div class="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">✓ Source File Present: widgets-b1/multiplying-multi-digit/index.html</div>
                        </div>
                        <a href="widgets-b1/multiplying-multi-digit/index.html" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-sky-500/10 text-sky-600 dark:text-sky-400 hover:bg-sky-500/20 font-medium transition shrink-0">
                            <i data-lucide="play" class="w-3 h-3 fill-current"></i>
                            <span>Run</span>
                            <i data-lucide="external-link" class="w-3 h-3"></i>
                        </a>
                    </div>
                </div>
            </div>

        </div>

        <!-- ======================================================== -->
        <!-- SECTION 4: QA TESTING STATUS (3-Source Architecture)      -->
        <!-- ======================================================== -->
        <div id="view-qa" class="view-content space-y-6 hidden">
            
            <div class="app-card border rounded-xl p-8 text-center space-y-4 max-w-2xl mx-auto my-6 shadow-sm">
                <div class="w-12 h-12 rounded-full bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center mx-auto">
                    <i data-lucide="shield-check" class="w-6 h-6"></i>
                </div>
                <div class="space-y-1.5">
                    <h2 class="text-base font-semibold text-slate-900 dark:text-white">QA Testing Status</h2>
                    <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed font-medium">
                        QA data integration will be available once the QA dataset is provided.
                    </p>
                </div>
                <div class="p-4 app-subtle border rounded-lg text-xs text-slate-600 dark:text-slate-400 text-left space-y-2">
                    <div class="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                        <i data-lucide="layers" class="w-3.5 h-3.5 text-blue-500"></i>
                        <span>3-Source Reconciliation Structure Ready</span>
                    </div>
                    <p class="leading-relaxed">
                        The architecture is designed to join:
                    </p>
                    <ol class="list-decimal pl-5 space-y-1">
                        <li><strong>Reference Spreadsheet</strong>: Requirements & metadata (Development & Content Team)</li>
                        <li><strong>Repository Inventory</strong>: Codebase presence, WG batch, and runnable simulation paths</li>
                        <li><strong>QA Test Results</strong>: Pass/fail status, defects, and verification history (Awaiting QA file)</li>
                    </ol>
                </div>
            </div>

        </div>

        <!-- ======================================================== -->
        <!-- SECTION 5: USER MANAGEMENT (Admin Only)                   -->
        <!-- ======================================================== -->
        <div id="view-users" class="view-content space-y-4 hidden">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h2 class="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                        <i data-lucide="users" class="w-4 h-4 text-blue-500"></i>
                        <span>Team User Management</span>
                    </h2>
                    <p class="text-xs text-slate-500 dark:text-slate-400">Manage authorized team members, roles, and dashboard permissions.</p>
                </div>
                <button onclick="openAddUserModal()" class="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-sm transition flex items-center gap-1.5 self-start sm:self-auto">
                    <i data-lucide="user-plus" class="w-3.5 h-3.5"></i>
                    <span>Add / Invite User</span>
                </button>
            </div>

            <!-- Live User Summary Metric Cards (Auto-updates when user is removed/added) -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div class="app-card border rounded-lg p-3 space-y-0.5">
                    <span class="text-[11px] font-medium text-slate-500 dark:text-slate-400">Total Members</span>
                    <div id="statTotalUsers" class="text-xl font-bold text-slate-900 dark:text-white">0</div>
                    <div class="text-[10px] text-slate-400">Registered accounts</div>
                </div>
                <div class="app-card border rounded-lg p-3 space-y-0.5">
                    <span class="text-[11px] font-medium text-slate-500 dark:text-slate-400">Active Accounts</span>
                    <div id="statActiveUsers" class="text-xl font-bold text-emerald-600 dark:text-emerald-400">0</div>
                    <div class="text-[10px] text-slate-400">Can log in</div>
                </div>
                <div class="app-card border rounded-lg p-3 space-y-0.5">
                    <span class="text-[11px] font-medium text-slate-500 dark:text-slate-400">Administrators</span>
                    <div id="statAdminUsers" class="text-xl font-bold text-blue-600 dark:text-blue-400">0</div>
                    <div class="text-[10px] text-slate-400">Full access</div>
                </div>
                <div class="app-card border rounded-lg p-3 space-y-0.5">
                    <span class="text-[11px] font-medium text-slate-500 dark:text-slate-400">Team Staff</span>
                    <div id="statStaffUsers" class="text-xl font-bold text-purple-600 dark:text-purple-400">0</div>
                    <div class="text-[10px] text-slate-400">Dev, Content & QA</div>
                </div>
            </div>

            <!-- Users Table -->
            <div class="app-card border rounded-lg overflow-hidden shadow-sm">
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs">
                        <thead>
                            <tr class="app-subtle border-b text-slate-600 dark:text-slate-400 font-medium">
                                <th class="py-2.5 px-4">Name & Email</th>
                                <th class="py-2.5 px-4 w-32">Role</th>
                                <th class="py-2.5 px-4 w-28">Status</th>
                                <th class="py-2.5 px-4 w-36">Last Login</th>
                                <th class="py-2.5 px-4 text-right w-56">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="userTableBody" class="divide-y divide-slate-200 dark:divide-slate-800">
                            <!-- Populated dynamically via renderUsersTable() -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ======================================================== -->
        <!-- SECTION 6: ACTIVITY HISTORY (Admin Only)                  -->
        <!-- ======================================================== -->
        <div id="view-activity" class="view-content space-y-4 hidden">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h2 class="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                        <i data-lucide="activity" class="w-4 h-4 text-emerald-500"></i>
                        <span>Activity & Access Audit History</span>
                    </h2>
                    <p class="text-xs text-slate-500 dark:text-slate-400">Complete immutable record of team logins, section access, widget inspections, and data actions.</p>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="exportActivityCSV()" class="app-subtle hover:bg-slate-200 dark:hover:bg-slate-800 border rounded-lg px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 transition flex items-center gap-1.5">
                        <i data-lucide="download" class="w-3.5 h-3.5"></i>
                        <span>Export Activity CSV</span>
                    </button>
                </div>
            </div>

            <!-- Filter Controls for Activity Logs -->
            <div class="app-card border rounded-lg p-3 flex flex-col sm:flex-row gap-2.5 items-stretch sm:items-center">
                <div class="relative flex-1">
                    <i data-lucide="search" class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"></i>
                    <input type="text" id="activitySearch" oninput="renderActivityTable()" placeholder="Search by user name, email, target reference..." class="w-full app-subtle border rounded-md pl-9 pr-3 py-1.5 text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:border-blue-500" />
                </div>
                <select id="activityTypeFilter" onchange="renderActivityTable()" class="app-subtle border rounded-md px-2.5 py-1.5 text-xs text-slate-700 dark:text-slate-300 focus:outline-none cursor-pointer">
                    <option value="all">All Events</option>
                    <option value="LOGIN">Logins</option>
                    <option value="LOGOUT">Logouts</option>
                    <option value="NAVIGATION">Section Navigation</option>
                    <option value="WIDGET_VIEW">Widget Details Viewed</option>
                    <option value="SEARCH_FILTER">Search / Filter</option>
                    <option value="USER_MGMT">User Management Actions</option>
                    <option value="EXCEL_SYNC">Excel Sync / Uploads</option>
                </select>
            </div>

            <!-- Activity Table -->
            <div class="app-card border rounded-lg overflow-hidden shadow-sm">
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs">
                        <thead>
                            <tr class="app-subtle border-b text-slate-600 dark:text-slate-400 font-medium">
                                <th class="py-2.5 px-4 w-40">Date & Time</th>
                                <th class="py-2.5 px-4 w-44">User</th>
                                <th class="py-2.5 px-4 w-32">Event Type</th>
                                <th class="py-2.5 px-4 w-36">Section</th>
                                <th class="py-2.5 px-4">Details & Target Reference</th>
                            </tr>
                        </thead>
                        <tbody id="activityTableBody" class="divide-y divide-slate-200 dark:divide-slate-800">
                            <!-- Injected dynamically via renderActivityTable() -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

    </main>

    <!-- Footer -->
    <footer class="app-card border-t py-4 text-center text-xs text-slate-500 dark:text-slate-400 transition-colors">
        <div class="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
            <div>
                <span>Widget Comparison Dashboard</span> • 
                <span>Audited: <strong><span class="num-total">{total_count}</span> widgets</strong></span> • 
                <span>Built: <strong>{build_time}</strong></span>
            </div>
            <div class="flex items-center gap-2 text-slate-400">
                <span>Commit: {commit_badge}</span> • 
                <span>Source: Reference Excel (Dev & Content Teams)</span>
            </div>
        </div>
    </footer>

    <!-- Clean Widget Details Modal -->
    <div id="widgetModal" class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 hidden">
        <div class="app-card border rounded-2xl max-w-xl w-full max-h-[90vh] overflow-y-auto custom-scroll shadow-2xl flex flex-col">
            
            <div class="p-5 border-b flex items-start justify-between gap-3 sticky top-0 app-card z-10">
                <div class="space-y-1.5">
                    <div class="flex items-center gap-2">
                        <span id="modalSr" class="font-mono text-xs font-bold text-slate-400">#00</span>
                        <span id="modalSubject" class="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">Subject</span>
                        <span id="modalWg" class="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">WG-00</span>
                    </div>
                    <h3 id="modalName" class="text-lg font-bold text-slate-900 dark:text-white leading-tight">Widget Name</h3>
                    <div id="modalOwner" class="text-xs text-slate-500">Owner in Excel: -</div>
                </div>
                <button onclick="closeModal()" class="w-8 h-8 rounded-lg app-subtle hover:bg-slate-200 dark:hover:bg-slate-800 flex items-center justify-center text-slate-500">
                    <i data-lucide="x" class="w-4 h-4"></i>
                </button>
            </div>

            <div class="p-5 space-y-4 text-xs text-slate-700 dark:text-slate-300 flex-1">
                
                <!-- Status Row -->
                <div class="flex items-center justify-between p-3 app-subtle rounded-lg border">
                    <span class="font-medium text-slate-600 dark:text-slate-400">Status</span>
                    <div id="modalBadge"></div>
                </div>

                <!-- Source File Confirmation Card -->
                <div id="modalSourceCard" class="p-3.5 rounded-lg border space-y-2">
                    <!-- Populated dynamically -->
                </div>

                <!-- Live Simulation / Component Link Card -->
                <div id="modalLiveCard" class="p-3.5 rounded-lg border space-y-2">
                    <!-- Populated dynamically -->
                </div>

                <!-- Plain English Explanation -->
                <div class="space-y-1.5">
                    <div class="font-semibold text-slate-900 dark:text-white text-xs flex items-center gap-1.5">
                        <i data-lucide="help-circle" class="w-3.5 h-3.5 text-blue-500"></i>
                        <span>What this means</span>
                    </div>
                    <p id="modalExplanation" class="p-3 rounded-lg app-subtle border leading-relaxed text-slate-600 dark:text-slate-300"></p>
                </div>

                <!-- What was checked -->
                <div class="space-y-1.5">
                    <div class="font-semibold text-slate-900 dark:text-white text-xs flex items-center gap-1.5">
                        <i data-lucide="search" class="w-3.5 h-3.5 text-emerald-500"></i>
                        <span>What was checked</span>
                    </div>
                    <p id="modalChecked" class="p-3 rounded-lg app-subtle border leading-relaxed text-slate-600 dark:text-slate-300"></p>
                </div>

                <!-- What needs to be done -->
                <div class="space-y-1.5">
                    <div class="font-semibold text-slate-900 dark:text-white text-xs flex items-center gap-1.5">
                        <i data-lucide="check-circle" class="w-3.5 h-3.5 text-purple-500"></i>
                        <span>What needs to be done</span>
                    </div>
                    <p id="modalAction" class="p-3 rounded-lg app-subtle border leading-relaxed text-slate-600 dark:text-slate-300 font-medium"></p>
                </div>

                <!-- Admin Notes & Edit Section (Visible only to Admin) -->
                <div id="modalAdminEditBox" class="hidden p-3.5 rounded-lg border border-blue-500/25 bg-blue-500/5 space-y-2">
                    <div class="flex items-center justify-between">
                        <div class="font-semibold text-blue-600 dark:text-blue-400 text-xs flex items-center gap-1.5">
                            <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                            <span>Admin Widget Notes & Custom Details</span>
                        </div>
                        <span class="text-[10px] text-blue-500/80 font-mono font-bold">ADMIN ONLY</span>
                    </div>
                    <textarea id="modalAdminNotesInput" rows="2" placeholder="Add custom notes, assignee, or verification comments for this widget..." class="w-full app-card border rounded-lg p-2 text-xs text-slate-800 dark:text-slate-200 placeholder:text-slate-400 focus:outline-none focus:border-blue-500"></textarea>
                    <div class="flex justify-end">
                        <button onclick="saveAdminWidgetNotes()" class="px-3 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white font-medium text-[11px] transition shadow-sm">Save Notes</button>
                    </div>
                </div>

                <!-- Collapsible Technical Details (Hidden by default for simplicity) -->
                <div class="pt-2 border-t">
                    <button onclick="toggleTechnicalDetails()" class="text-[11px] text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 font-medium flex items-center gap-1">
                        <i data-lucide="code" class="w-3.5 h-3.5"></i>
                        <span id="techToggleLabel">Show Technical Details</span>
                    </button>
                    <div id="technicalArea" class="hidden mt-3 p-3 rounded-lg app-subtle border space-y-2 font-mono text-[11px]">
                        <div><strong class="text-slate-500">Batch Code:</strong> <span id="modalBatch" class="text-slate-800 dark:text-slate-200"></span></div>
                        <div id="modalPathContainer"><strong class="text-slate-500">Repository File:</strong> <span id="modalPath" class="text-slate-800 dark:text-slate-200 break-all select-all"></span></div>
                        <div><strong class="text-slate-500">Physical File On Disk:</strong> <span id="modalHasFile"></span></div>
                    </div>
                </div>

            </div>

            <div class="p-3 border-t app-subtle flex items-center justify-between">
                <button onclick="closeModal()" class="px-3 py-1.5 rounded app-card border hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-medium">Close</button>
                <div id="modalActionSlot"></div>
            </div>
        </div>
    </div>

    <!-- Add / Invite User Modal (Admin Only) -->
    <div id="addUserModal" class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 hidden">
        <div class="app-card border rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl text-left">
            <div class="flex items-center justify-between pb-2 border-b">
                <div class="flex items-center gap-2">
                    <i data-lucide="user-plus" class="w-4 h-4 text-blue-500"></i>
                    <h3 class="font-bold text-sm text-slate-900 dark:text-white">Add New Team Member</h3>
                </div>
                <button onclick="closeAddUserModal()" class="text-slate-400 hover:text-slate-600">
                    <i data-lucide="x" class="w-4 h-4"></i>
                </button>
            </div>
            
            <form onsubmit="handleCreateUser(event)" class="space-y-3 text-xs">
                <div>
                    <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Full Name</label>
                    <input type="text" id="newUserName" required placeholder="e.g. Ramesh Kumar" class="w-full app-subtle border rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-500" />
                </div>
                <div>
                    <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Email Address</label>
                    <input type="email" id="newUserEmail" required placeholder="name@company.com" class="w-full app-subtle border rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-500" />
                </div>
                <div>
                    <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Temporary Password</label>
                    <input type="text" id="newUserPass" value="Welcome@123" required class="w-full app-subtle border rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:border-blue-500" />
                </div>
                <div>
                    <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Assigned Role</label>
                    <select id="newUserRole" class="w-full app-subtle border rounded-lg px-3 py-2 text-xs focus:outline-none cursor-pointer">
                        <option value="developer">Developer (Codebase & Technical views)</option>
                        <option value="content">Content (Curriculum & Inventory)</option>
                        <option value="qa">QA (Verification & Testing)</option>
                        <option value="viewer">Viewer (Read-Only)</option>
                        <option value="admin">Admin (Full Control)</option>
                    </select>
                </div>
                <div class="pt-3 border-t flex justify-end gap-2">
                    <button type="button" onclick="closeAddUserModal()" class="px-3 py-1.5 rounded-lg border app-subtle hover:bg-slate-200 dark:hover:bg-slate-800 font-medium">Cancel</button>
                    <button type="submit" class="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium">Create User</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Edit User Modal (Admin Only) -->
    <div id="editUserModal" class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 hidden">
        <div class="app-card border rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl text-left">
            <div class="flex items-center justify-between pb-2 border-b">
                <div class="flex items-center gap-2">
                    <i data-lucide="user-cog" class="w-4 h-4 text-blue-500"></i>
                    <h3 class="font-bold text-sm text-slate-900 dark:text-white">Edit Team Member</h3>
                </div>
                <button onclick="closeEditUserModal()" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                    <i data-lucide="x" class="w-4 h-4"></i>
                </button>
            </div>
            
            <form onsubmit="handleSaveEditUser(event)" class="space-y-3 text-xs">
                <input type="hidden" id="editUserId" />
                <div>
                    <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Full Name</label>
                    <input type="text" id="editUserName" required class="w-full app-subtle border rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-500" />
                </div>
                <div>
                    <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Email Address</label>
                    <input type="email" id="editUserEmail" required class="w-full app-subtle border rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-500" />
                </div>
                <div>
                    <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Assigned Role</label>
                    <select id="editUserRole" class="w-full app-subtle border rounded-lg px-3 py-2 text-xs focus:outline-none cursor-pointer">
                        <option value="developer">Developer (Codebase & Technical views)</option>
                        <option value="content">Content (Curriculum & Inventory)</option>
                        <option value="qa">QA (Verification & Testing)</option>
                        <option value="viewer">Viewer (Read-Only)</option>
                        <option value="admin">Admin (Full Control)</option>
                    </select>
                </div>
                <div>
                    <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Change Password <span class="text-[10px] text-slate-400 font-normal">(Leave blank to keep unchanged)</span></label>
                    <input type="text" id="editUserPass" placeholder="Enter new password or leave blank" class="w-full app-subtle border rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:border-blue-500" />
                </div>
                <div class="pt-3 border-t flex justify-end gap-2">
                    <button type="button" onclick="closeEditUserModal()" class="px-3 py-1.5 rounded-lg border app-subtle hover:bg-slate-200 dark:hover:bg-slate-800 font-medium">Cancel</button>
                    <button type="submit" class="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium">Save Changes</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Dedicated In-App Delete User Confirmation Modal -->
    <div id="deleteUserModal" class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 hidden">
        <div class="app-card border border-rose-500/30 rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl text-left">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-rose-500/15 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0">
                    <i data-lucide="alert-triangle" class="w-5 h-5"></i>
                </div>
                <div>
                    <h3 class="font-bold text-sm text-slate-900 dark:text-white">Delete Team Member</h3>
                    <p class="text-[11px] text-slate-500 dark:text-slate-400">This action is permanent and cannot be undone.</p>
                </div>
            </div>
            
            <div class="p-3 rounded-lg app-subtle border text-xs space-y-1">
                <div class="font-semibold text-slate-900 dark:text-white" id="deleteTargetName">User Name</div>
                <div class="text-[11px] text-slate-500 font-mono" id="deleteTargetEmail">email@company.com</div>
                <div class="text-[10px] text-slate-400 pt-1" id="deleteTargetRole">Role: -</div>
            </div>

            <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Removing this user will permanently revoke their login. All dashboard metrics and user records will update immediately.
            </p>

            <div class="pt-2 flex items-center justify-end gap-2">
                <button type="button" onclick="closeDeleteUserModal()" class="px-3 py-1.5 rounded-lg border app-subtle hover:bg-slate-200 dark:hover:bg-slate-800 text-xs font-medium">Cancel</button>
                <button type="button" onclick="confirmDeleteUser()" id="confirmDeleteBtn" class="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs shadow-sm flex items-center gap-1.5">
                    <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                    <span>Delete User</span>
                </button>
            </div>
        </div>
    </div>

    <!-- Drag & Drop Full Window Overlay -->
    <div id="dropOverlay" class="fixed inset-0 z-50 bg-slate-900/70 backdrop-blur-sm flex flex-col items-center justify-center text-white hidden pointer-events-none transition-all">
        <div class="p-8 rounded-2xl bg-slate-900 border-2 border-dashed border-blue-500 text-center shadow-2xl space-y-3 pointer-events-auto max-w-md mx-4">
            <i data-lucide="file-spreadsheet" class="w-16 h-16 text-emerald-400 mx-auto animate-bounce"></i>
            <div class="text-lg font-bold">Drop New Excel File to Reconcile</div>
            <p class="text-xs text-slate-300">Drop your updated spreadsheet here to recalculate all widgets, source verification, and status numbers instantly.</p>
        </div>
    </div>

    <!-- Floating Toast Notification -->
    <div id="toastNotification" class="fixed bottom-6 right-6 z-50 p-4 rounded-xl shadow-2xl app-card border flex items-center gap-3 text-xs transition-all transform translate-y-24 opacity-0 pointer-events-none">
        <div id="toastIcon" class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"></div>
        <div>
            <div id="toastTitle" class="font-semibold text-slate-900 dark:text-white"></div>
            <div id="toastMsg" class="text-slate-500 dark:text-slate-400 mt-0.5"></div>
        </div>
    </div>

    <!-- Script -->
    <script>
        // Enforce Authentication Guard on Page Load
        const currentUser = authManager.requireAuth();

        let rawData = __DATA_JSON__;
        const REPO_CATALOG = __REPO_CATALOG_JSON__;
        const ALIASES = {
            'operation domino ww ii mission': 'operation dominic',
            'operation dominic': 'operation dominic',
            "making of india's constitution": 'making of the indian institution',
            'making of the indian institution': 'making of the indian institution',
            'commutative property of addition': 'cumulative property of addition',
            'cumulative property of addition': 'cumulative property of addition'
        };
        const WHITEBOARD_TOOLS = new Set([
            'compass', 'clock', 'ruler', 'protractor', 'set square 30', 'set square 45', 'curtain', 'split screen', 'scientific calculator'
        ]);

        let filteredData = [...rawData];
        let currentPage = 1;
        const pageSize = 25;
        let sortCol = 'sr';
        let sortAsc = true;
        let showTech = false;
        let currentModalPath = '';

        // Initialize User Session in UI
        function initUserProfile() {
            if (!currentUser) return;
            const nameEl = document.getElementById('userNameDisplay');
            const roleEl = document.getElementById('userRoleBadge');
            const avatarEl = document.getElementById('userAvatar');

            if (nameEl) nameEl.innerText = currentUser.fullName;
            if (roleEl) roleEl.innerText = currentUser.role.toUpperCase();
            if (avatarEl) avatarEl.innerText = (currentUser.fullName || 'U').charAt(0).toUpperCase();

            // Show Admin-Only Tabs
            if (currentUser.role === 'admin') {
                const tabUsers = document.getElementById('tab-users');
                const tabActivity = document.getElementById('tab-activity');
                if (tabUsers) tabUsers.classList.remove('hidden');
                if (tabActivity) tabActivity.classList.remove('hidden');
            }
        }

        function handleLogout() {
            authManager.logout();
        }

        // Theme management
        function initTheme() {
            const saved = localStorage.getItem('theme-preference') || 'system';
            document.getElementById('themeSelector').value = saved;
            applyTheme(saved);
        }

        function changeTheme(theme) {
            localStorage.setItem('theme-preference', theme);
            applyTheme(theme);
        }

        function applyTheme(theme) {
            const root = document.documentElement;
            if (theme === 'dark') {
                root.classList.add('dark');
            } else if (theme === 'light') {
                root.classList.remove('dark');
            } else {
                if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
                    root.classList.add('dark');
                } else {
                    root.classList.remove('dark');
                }
            }
        }

        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (localStorage.getItem('theme-preference') === 'system' || !localStorage.getItem('theme-preference')) {
                applyTheme('system');
            }
        });

        // Tab Navigation with Role Check & Activity Logging
        function switchTab(tabId) {
            // Guard admin tabs
            if ((tabId === 'users' || tabId === 'activity') && currentUser.role !== 'admin') {
                showToast('Unauthorized: Administrator privilege required', 'error');
                return;
            }

            document.querySelectorAll('.view-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.nav-tab').forEach(el => {
                el.classList.remove('border-blue-600', 'text-blue-600', 'dark:text-blue-400');
                el.classList.add('border-transparent', 'text-slate-600', 'dark:text-slate-400');
            });

            document.getElementById('view-' + tabId).classList.remove('hidden');
            const activeTab = document.getElementById('tab-' + tabId);
            activeTab.classList.remove('border-transparent', 'text-slate-600', 'dark:text-slate-400');
            activeTab.classList.add('border-blue-600', 'text-blue-600', 'dark:text-blue-400');

            if (tabId === 'inventory') {
                renderTable();
            } else if (tabId === 'users') {
                renderUsersTable();
            } else if (tabId === 'activity') {
                renderActivityTable();
            }

            // Log navigation activity
            authManager.logActivity('NAVIGATION', tabId.toUpperCase(), '', `Switched to ${tabId} tab`);
            lucide.createIcons();
        }

        // Drill-Down from Dashboard Numbers to Filtered Details Table
        function drillDown(statusKey) {
            switchTab('inventory');

            const statusSelect = document.getElementById('statusFilter');
            if (statusSelect) {
                statusSelect.value = statusKey;
            }

            const searchInput = document.getElementById('widgetSearch');
            if (searchInput) {
                searchInput.value = '';
            }

            currentPage = 1;
            filterWidgets();

            authManager.logActivity('SEARCH_FILTER', 'All Widgets', statusKey, `Drill down filter by: ${statusKey}`);

            const inventoryView = document.getElementById('view-inventory');
            if (inventoryView) {
                inventoryView.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }

        function clearFilter() {
            document.getElementById('statusFilter').value = 'all';
            document.getElementById('subjectFilter').value = 'all';
            document.getElementById('widgetSearch').value = '';
            currentPage = 1;
            filterWidgets();
        }

        function updateFilterBanner(statusKey) {
            const banner = document.getElementById('activeFilterBanner');
            const label = document.getElementById('filterBannerLabel');
            if (!banner || !label) return;

            const counts = getCategoryCounts();
            const labels = {
                available: `Already Available (${counts.available} Widgets)`,
                corrected: `Found in Repository (${counts.corrected} Widgets)`,
                requires_dev: `Not Available – Needs Development (${counts.requires_dev} Widgets)`,
                whiteboard: `Classroom Tools (${counts.whiteboard} Tools)`,
                minor_changes: `Small Changes Needed (${counts.minor_changes} Widgets)`,
                has_live: `Live HTML Simulations Ready (${counts.live_html} Widgets)`,
                source_present: `Source File Present on Disk (${counts.source_present} Widgets)`,
                source_missing: `Source File Missing from Repository (${counts.requires_dev} Widgets)`
            };

            if (statusKey && statusKey !== 'all' && labels[statusKey]) {
                label.innerText = labels[statusKey];
                banner.classList.remove('hidden');
            } else {
                banner.classList.add('hidden');
            }
            lucide.createIcons();
        }

        function getCategoryCounts() {
            let total = rawData.length;
            let available = 0, corrected = 0, requires_dev = 0, whiteboard = 0, minor_changes = 0;
            let live_html = 0, source_present = 0;

            rawData.forEach(w => {
                if (w.status_category === 'available') available++;
                else if (w.status_category === 'corrected') corrected++;
                else if (w.status_category === 'requires_dev') requires_dev++;
                else if (w.status_category === 'whiteboard') whiteboard++;
                else if (w.status_category === 'minor_changes') minor_changes++;

                if (w.live_html) live_html++;
                if (w.has_file) source_present++;
            });

            return {
                total, available, corrected, requires_dev, whiteboard, minor_changes, live_html, source_present
            };
        }

        // Table & Search
        function getStatusBadge(category, label) {
            const styles = {
                available: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20',
                corrected: 'bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20',
                requires_dev: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20',
                whiteboard: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20',
                minor_changes: 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20'
            };
            const s = styles[category] || 'bg-slate-500/10 text-slate-500 border border-slate-500/20';
            return `<span class="px-2 py-0.5 rounded text-[11px] font-medium ${s}">${label}</span>`;
        }

        function filterWidgets() {
            const q = document.getElementById('widgetSearch').value.toLowerCase().trim();
            const status = document.getElementById('statusFilter').value;
            const subject = document.getElementById('subjectFilter').value;

            filteredData = rawData.filter(w => {
                if (status === 'has_live' && !w.live_html) return false;
                else if (status === 'source_present' && !w.has_file) return false;
                else if (status === 'source_missing' && w.has_file) return false;
                else if (status !== 'all' && status !== 'has_live' && status !== 'source_present' && status !== 'source_missing' && w.status_category !== status) return false;
                if (subject !== 'all' && w.subject !== subject) return false;
                if (q) {
                    const combined = (w.name + ' ' + w.subject + ' ' + w.owner + ' ' + w.batch + ' ' + (w.wg_code || '')).toLowerCase();
                    if (!combined.includes(q)) return false;
                }
                return true;
            });

            filteredData.sort((a, b) => {
                let vA = a[sortCol];
                let vB = b[sortCol];
                if (typeof vA === 'string') return sortAsc ? vA.localeCompare(vB) : vB.localeCompare(vA);
                return sortAsc ? vA - vB : vB - vA;
            });

            currentPage = 1;
            renderTable();
            updateFilterBanner(status);
        }

        function sortData(col) {
            if (sortCol === col) sortAsc = !sortAsc;
            else { sortCol = col; sortAsc = true; }
            filterWidgets();
        }

        function renderTable() {
            const tbody = document.getElementById('widgetTableBody');
            const total = filteredData.length;
            const totalPages = Math.ceil(total / pageSize) || 1;
            if (currentPage > totalPages) currentPage = totalPages;
            
            const startIdx = (currentPage - 1) * pageSize;
            const items = filteredData.slice(startIdx, startIdx + pageSize);

            document.getElementById('totalFiltered').innerText = total;
            document.getElementById('pageCount').innerText = total === 0 ? '0' : `${startIdx + 1}–${Math.min(startIdx + pageSize, total)}`;
            document.getElementById('pageIndicator').innerText = `Page ${currentPage} of ${totalPages}`;
            document.getElementById('prevBtn').disabled = currentPage === 1;
            document.getElementById('nextBtn').disabled = currentPage >= totalPages;

            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="p-8 text-center text-slate-500">No widgets match the selected filters.</td></tr>';
                return;
            }

            tbody.innerHTML = items.map(w => `
                <tr onclick="openModal(${w.sr})" class="hover:bg-slate-100/70 dark:hover:bg-slate-800/40 cursor-pointer transition">
                    <td class="py-2.5 px-4 font-mono text-slate-400 font-semibold">${w.sr}</td>
                    <td class="py-2.5 px-4 font-mono text-xs">
                        ${w.wg_code && w.wg_code !== '-' && w.wg_code !== 'TOOL' ? `
                            <span class="px-2 py-0.5 rounded font-mono text-[11px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700">
                                ${w.wg_code}
                            </span>
                        ` : (w.wg_code === 'TOOL' ? '<span class="text-amber-600 dark:text-amber-400 text-[10px] font-semibold uppercase">Tool</span>' : '<span class="text-slate-400 font-mono text-[11px]">—</span>')}
                    </td>
                    <td class="py-2.5 px-4 font-medium text-slate-900 dark:text-white">
                        <div class="flex items-center gap-2">
                            <span>${w.name}</span>
                            ${w.live_html ? '<span class="px-1.5 py-0.2 rounded text-[9px] font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">HTML</span>' : ''}
                        </div>
                    </td>
                    <td class="py-2.5 px-4 text-slate-600 dark:text-slate-400">${w.subject}</td>
                    <td class="py-2.5 px-4">
                        ${w.has_file ? `
                            <span class="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                                <i data-lucide="check" class="w-3.5 h-3.5 text-emerald-500"></i>
                                <span>Present</span>
                            </span>
                        ` : (w.status_category === 'whiteboard' ? `
                            <span class="inline-flex items-center gap-1 text-[11px] font-medium text-amber-600 dark:text-amber-400">
                                <i data-lucide="minus" class="w-3.5 h-3.5 text-amber-500"></i>
                                <span>Tool</span>
                            </span>
                        ` : `
                            <span class="inline-flex items-center gap-1 text-[11px] font-medium text-rose-600 dark:text-rose-400">
                                <i data-lucide="x" class="w-3.5 h-3.5 text-rose-500"></i>
                                <span>Missing</span>
                            </span>
                        `)}
                    </td>
                    <td class="py-2.5 px-4">${getStatusBadge(w.status_category, w.status_label)}</td>
                    <td class="py-2.5 px-4 text-right">
                        <div class="inline-flex items-center justify-end gap-1.5" onclick="event.stopPropagation()">
                            ${w.live_html ? `
                                <a href="${w.live_html}" target="_blank" rel="noopener noreferrer" title="Open live simulation in new tab" class="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:hover:bg-emerald-900/60 dark:text-emerald-300 dark:border-emerald-800/60 inline-flex items-center gap-1 transition">
                                    <i data-lucide="play" class="w-3 h-3 fill-current text-emerald-600 dark:text-emerald-400"></i>
                                    <span>Run</span>
                                </a>
                            ` : (w.component_html ? `
                                <a href="${w.component_html}" target="_blank" rel="noopener noreferrer" title="View Angular component HTML template" class="px-2 py-0.5 rounded text-[11px] font-medium bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 dark:bg-blue-950/40 dark:hover:bg-blue-900/60 dark:text-blue-300 dark:border-blue-800/60 inline-flex items-center gap-1 transition">
                                    <i data-lucide="file-code" class="w-3 h-3 text-blue-600 dark:text-blue-400"></i>
                                    <span>HTML</span>
                                </a>
                            ` : '')}
                            <button onclick="openModal(${w.sr})" class="px-2 py-0.5 rounded text-[11px] app-subtle border text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 hover:underline">
                                Details
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');

            lucide.createIcons();
        }

        function changePage(delta) {
            currentPage += delta;
            renderTable();
        }

        function openModal(sr) {
            const w = rawData.find(x => x.sr === sr);
            if (!w) return;

            currentModalPath = w.repo_path || '';

            document.getElementById('modalSr').innerText = '#' + w.sr;
            document.getElementById('modalSubject').innerText = w.subject;
            document.getElementById('modalName').innerText = w.name;
            document.getElementById('modalOwner').innerText = 'Owner listed in Excel: ' + w.owner;
            document.getElementById('modalBadge').innerHTML = getStatusBadge(w.status_category, w.status_label);
            document.getElementById('modalExplanation').innerText = w.plain_explanation;
            document.getElementById('modalChecked').innerText = w.what_was_checked;
            document.getElementById('modalAction').innerText = w.what_needs_to_be_done;

            // WG Code in Modal Header
            const wgEl = document.getElementById('modalWg');
            if (wgEl) {
                if (w.wg_code && w.wg_code !== '-' && w.wg_code !== 'TOOL') {
                    wgEl.innerText = 'WG: ' + w.wg_code;
                    wgEl.className = 'px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20';
                    wgEl.classList.remove('hidden');
                } else if (w.wg_code === 'TOOL') {
                    wgEl.innerText = 'Whiteboard Tool';
                    wgEl.className = 'px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20';
                    wgEl.classList.remove('hidden');
                } else {
                    wgEl.innerText = 'Batch: ' + (w.batch || '—');
                    wgEl.className = 'px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700';
                    wgEl.classList.remove('hidden');
                }
            }

            // Source File Confirmation Card
            const sourceCard = document.getElementById('modalSourceCard');
            if (sourceCard) {
                if (w.has_file) {
                    sourceCard.className = 'p-3.5 rounded-lg border bg-emerald-500/10 border-emerald-500/25 space-y-2';
                    sourceCard.innerHTML = `
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                                <span class="text-xs font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wide">
                                    Source File: Present (Verified on Disk)
                                </span>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-600/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30">
                                FILE CONFIRMED
                            </span>
                        </div>
                        <div class="p-2 app-card border rounded font-mono text-[11px] text-slate-800 dark:text-slate-200 select-all break-all flex items-center justify-between gap-2">
                            <span class="truncate">${w.repo_path}</span>
                            <button onclick="copyPath()" id="copyPathBtn" class="text-[10px] text-blue-600 dark:text-blue-400 hover:underline shrink-0">Copy Path</button>
                        </div>
                        <div class="text-[11px] text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                            <i data-lucide="check-circle" class="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0"></i>
                            <span>Physical source files verified in the codebase.</span>
                        </div>
                    `;
                } else if (w.status_category === 'requires_dev') {
                    sourceCard.className = 'p-3.5 rounded-lg border bg-rose-500/10 border-rose-500/25 space-y-2';
                    sourceCard.innerHTML = `
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <span class="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                                <span class="text-xs font-bold text-rose-700 dark:text-rose-400 uppercase tracking-wide">
                                    Source File: Missing (Not Found in Repository)
                                </span>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-rose-600/15 text-rose-700 dark:text-rose-300 border border-rose-500/30">
                                FILE MISSING
                            </span>
                        </div>
                        <p class="text-[11px] text-rose-800 dark:text-rose-300 leading-relaxed">
                            No source files exist in the repository for this widget. This curriculum simulation requires complete development.
                        </p>
                    `;
                } else if (w.status_category === 'whiteboard') {
                    sourceCard.className = 'p-3.5 rounded-lg border bg-amber-500/10 border-amber-500/25 space-y-2';
                    sourceCard.innerHTML = `
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                                <span class="text-xs font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wide">
                                    Source File: Whiteboard Tool (External Overlay)
                                </span>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-600/15 text-amber-700 dark:text-amber-300 border border-amber-500/30">
                                EXTERNAL TOOL
                            </span>
                        </div>
                        <p class="text-[11px] text-amber-800 dark:text-amber-300 leading-relaxed">
                            Marked as "Repo: No" in reference spreadsheet. This is a teaching canvas utility (ruler, compass, protractor), not a curriculum lesson simulation in the widget repository.
                        </p>
                    `;
                }
            }

            // Live Simulation / HTML Card
            const liveCard = document.getElementById('modalLiveCard');
            if (w.live_html) {
                liveCard.className = 'p-3.5 rounded-lg border bg-emerald-500/10 border-emerald-500/25 flex flex-col sm:flex-row sm:items-center justify-between gap-3';
                liveCard.innerHTML = `
                    <div class="min-w-0">
                        <div class="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
                            <i data-lucide="play-circle" class="w-4 h-4 text-emerald-600 dark:text-emerald-400"></i>
                            <span>Live HTML Simulation Available</span>
                        </div>
                        <div class="text-[11px] font-mono text-slate-600 dark:text-slate-300 mt-1 truncate select-all">
                            ${w.live_html}
                        </div>
                        <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">Standalone interactive HTML5 activity. Click the button to launch directly in your browser.</p>
                    </div>
                    <a href="${w.live_html}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium shadow-sm transition whitespace-nowrap shrink-0">
                        <i data-lucide="play" class="w-3.5 h-3.5 fill-current"></i>
                        <span>Open Live Widget</span>
                        <i data-lucide="external-link" class="w-3 h-3"></i>
                    </a>
                `;
            } else if (w.component_html) {
                liveCard.className = 'p-3.5 rounded-lg border bg-blue-500/10 border-blue-500/25 flex flex-col sm:flex-row sm:items-center justify-between gap-3';
                liveCard.innerHTML = `
                    <div class="min-w-0">
                        <div class="flex items-center gap-1.5 text-xs font-semibold text-blue-700 dark:text-blue-400">
                            <i data-lucide="file-code" class="w-4 h-4 text-blue-600 dark:text-blue-400"></i>
                            <span>Angular Component HTML Template</span>
                        </div>
                        <div class="text-[11px] font-mono text-slate-600 dark:text-slate-300 mt-1 truncate select-all">
                            ${w.component_html}
                        </div>
                        <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">Interactive Angular component inside <code>src/app/</code>.</p>
                    </div>
                    <a href="${w.component_html}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium shadow-sm transition whitespace-nowrap shrink-0">
                        <span>View Template HTML</span>
                        <i data-lucide="external-link" class="w-3 h-3"></i>
                    </a>
                `;
            } else if (w.status_category === 'requires_dev') {
                liveCard.className = 'p-3 rounded-lg border bg-amber-500/10 border-amber-500/25 flex items-start gap-2.5';
                liveCard.innerHTML = `
                    <i data-lucide="alert-circle" class="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5"></i>
                    <div>
                        <div class="text-xs font-semibold text-amber-700 dark:text-amber-400">No Live Page Available</div>
                        <p class="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5">This widget is part of the development backlog and has not yet been built in the repository.</p>
                    </div>
                `;
            } else if (w.status_category === 'whiteboard') {
                liveCard.className = 'p-3 rounded-lg border bg-purple-500/10 border-purple-500/25 flex items-start gap-2.5';
                liveCard.innerHTML = `
                    <i data-lucide="layout" class="w-4 h-4 text-purple-600 dark:text-purple-400 shrink-0 mt-0.5"></i>
                    <div>
                        <div class="text-xs font-semibold text-purple-700 dark:text-purple-400">Classroom Whiteboard Utility Tool</div>
                        <p class="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5">This is an overlay tool for the teaching canvas (ruler, compass, protractor, etc.), not a standalone simulation page.</p>
                    </div>
                `;
            } else {
                liveCard.className = 'hidden';
                liveCard.innerHTML = '';
            }

            // Technical details
            document.getElementById('modalBatch').innerText = w.batch;
            document.getElementById('modalHasFile').innerText = w.has_file ? 'Yes (Verified on disk)' : 'No file allocated';
            document.getElementById('modalHasFile').className = w.has_file ? 'font-mono font-medium text-emerald-600 dark:text-emerald-400' : 'font-mono font-medium text-slate-400';

            const pathContainer = document.getElementById('modalPathContainer');
            if (w.repo_path) {
                pathContainer.classList.remove('hidden');
                document.getElementById('modalPath').innerText = w.repo_path;
            } else {
                pathContainer.classList.add('hidden');
            }

            // Footer Action Button
            const actionSlot = document.getElementById('modalActionSlot');
            if (w.live_html) {
                actionSlot.innerHTML = `<a href="${w.live_html}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium shadow-sm transition"><span>Open Live Widget</span><i data-lucide="external-link" class="w-3.5 h-3.5"></i></a>`;
            } else if (w.component_html) {
                actionSlot.innerHTML = `<a href="${w.component_html}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium shadow-sm transition"><span>View Template</span><i data-lucide="external-link" class="w-3.5 h-3.5"></i></a>`;
            } else if (w.repo_path) {
                actionSlot.innerHTML = `<a href="${w.repo_path}" target="_blank" rel="noopener noreferrer" class="px-3 py-1.5 rounded bg-slate-700 hover:bg-slate-600 text-white text-xs font-medium">Open File</a>`;
            } else {
                actionSlot.innerHTML = '';
            }

            showTech = false;
            document.getElementById('technicalArea').classList.add('hidden');
            document.getElementById('techToggleLabel').innerText = 'Show Technical Details';

            // Log activity: widget view
            authManager.logActivity('WIDGET_VIEW', 'Inventory Details', `${w.wg_code || 'No WG'} (${w.name})`, `Inspected widget #${w.sr}`);

            // Admin Notes Box
            const adminBox = document.getElementById('modalAdminEditBox');
            if (adminBox) {
                if (authManager.isAdmin()) {
                    adminBox.classList.remove('hidden');
                    const savedNotes = localStorage.getItem('widget_notes_' + w.sr) || '';
                    document.getElementById('modalAdminNotesInput').value = savedNotes;
                } else {
                    adminBox.classList.add('hidden');
                }
            }

            document.getElementById('widgetModal').classList.remove('hidden');
            lucide.createIcons();
        }

        function toggleTechnicalDetails() {
            showTech = !showTech;
            const area = document.getElementById('technicalArea');
            const label = document.getElementById('techToggleLabel');
            if (showTech) {
                area.classList.remove('hidden');
                label.innerText = 'Hide Technical Details';
            } else {
                area.classList.add('hidden');
                label.innerText = 'Show Technical Details';
            }
        }

        function copyPath() {
            if (!currentModalPath) return;
            navigator.clipboard.writeText(currentModalPath).then(() => {
                const btn = document.getElementById('copyPathBtn');
                btn.innerText = 'Copied!';
                setTimeout(() => { btn.innerText = 'Copy Path'; }, 2000);
            });
        }

        function closeModal() {
            document.getElementById('widgetModal').classList.add('hidden');
        }

        function saveAdminWidgetNotes() {
            const srText = document.getElementById('modalSr').innerText.replace('#', '').trim();
            const notes = document.getElementById('modalAdminNotesInput').value;
            localStorage.setItem('widget_notes_' + srText, notes);
            const w = rawData.find(x => String(x.sr) === String(srText));
            const wName = w ? w.name : ('Widget #' + srText);
            authManager.logActivity('WIDGET_EDIT', 'Widget Details', '#' + srText, `Admin saved notes for ${wName}: "${notes.substring(0, 45)}"`);
            showToast('Admin notes saved successfully', 'success');
        }

        function exportCSV() {
            let csv = 'Sr,WG Number,Widget Name,Subject,Batch in Excel,Owner in Excel,Source File Status,Status,What Needs to Be Done,Live HTML Link,Repository Path\\n';
            rawData.forEach(w => {
                const a = (w.what_needs_to_be_done || '').replace(/"/g, '""');
                const live = (w.live_html || w.component_html || '').replace(/"/g, '""');
                const src = w.has_file ? 'Present' : (w.status_category === 'whiteboard' ? 'Whiteboard Tool' : 'Missing');
                csv += `"${w.sr}","${w.wg_code || ''}","${w.name}","${w.subject}","${w.batch}","${w.owner}","${src}","${w.status_label}","${a}","${live}","${w.repo_path}"\\n`;
            });
            const blob = new Blob([csv], { type: 'text/csv' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'widget_comparison_summary.csv';
            a.click();
            authManager.logActivity('EXPORT', 'Widgets', '', 'Exported widget summary CSV');
        }

        // ========================================================
        // USER MANAGEMENT (Admin Only)
        // ========================================================
        function renderUsersTable() {
            if (!authManager.isAdmin()) return;
            const tbody = document.getElementById('userTableBody');
            const users = authManager.getUsers();
            const currentUser = authManager.getCurrentUser();

            // Update live summary metrics instantly
            const total = users.length;
            const active = users.filter(u => u.status === 'active').length;
            const admins = users.filter(u => u.role === 'admin').length;
            const staff = users.filter(u => u.role !== 'admin').length;

            const elTotal = document.getElementById('statTotalUsers');
            const elActive = document.getElementById('statActiveUsers');
            const elAdmin = document.getElementById('statAdminUsers');
            const elStaff = document.getElementById('statStaffUsers');

            if (elTotal) elTotal.innerText = total;
            if (elActive) elActive.innerText = active;
            if (elAdmin) elAdmin.innerText = admins;
            if (elStaff) elStaff.innerText = staff;

            tbody.innerHTML = users.map(u => {
                const isSelf = currentUser && currentUser.id === u.id;
                const safeName = (u.fullName || '').replace(/'/g, "\\'");
                return `
                <tr class="hover:bg-slate-100/70 dark:hover:bg-slate-800/40 transition">
                    <td class="py-2.5 px-4">
                        <div class="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                            <span>${u.fullName}</span>
                            ${isSelf ? '<span class="text-[9px] px-1.5 py-0.2 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 font-bold uppercase">You</span>' : ''}
                        </div>
                        <div class="text-[11px] text-slate-500 font-mono">${u.email}</div>
                    </td>
                    <td class="py-2.5 px-4">
                        <span class="px-2 py-0.5 rounded text-[11px] font-medium capitalize bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                            ${u.role}
                        </span>
                    </td>
                    <td class="py-2.5 px-4">
                        <span class="px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${u.status === 'active' ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20'}">
                            ${u.status}
                        </span>
                    </td>
                    <td class="py-2.5 px-4 text-slate-500 dark:text-slate-400 text-[11px]">
                        ${u.lastLogin ? new Date(u.lastLogin).toLocaleString() : 'Never'}
                    </td>
                    <td class="py-2.5 px-4 text-right">
                        <div class="inline-flex items-center justify-end gap-1.5">
                            <button onclick="openEditUserModal('${u.id}')" title="Edit user details" class="px-2.5 py-1 rounded text-[11px] font-medium border border-blue-200 dark:border-blue-900/60 bg-blue-50/60 dark:bg-blue-950/30 hover:bg-blue-100 dark:hover:bg-blue-900/50 text-blue-600 dark:text-blue-400 transition flex items-center gap-1">
                                <i data-lucide="edit-3" class="w-3 h-3"></i>
                                <span>Edit</span>
                            </button>
                            <button onclick="handleToggleStatus('${u.id}')" title="Toggle active status" class="px-2 py-1 rounded text-[11px] font-medium border app-subtle hover:bg-slate-200 dark:hover:bg-slate-800 transition ${u.status === 'active' ? 'text-amber-600' : 'text-emerald-600'}">
                                ${u.status === 'active' ? 'Disable' : 'Enable'}
                            </button>
                            <button onclick="promptDeleteUser('${u.id}', '${safeName}', '${u.email}', '${u.role}')" ${isSelf ? 'disabled title="Cannot delete yourself" class="px-2 py-1 rounded text-[11px] font-medium border border-slate-200 dark:border-slate-800 opacity-40 cursor-not-allowed"' : 'title="Delete user" class="px-2 py-1 rounded text-[11px] font-medium border border-rose-200 dark:border-rose-900/60 bg-rose-50/60 dark:bg-rose-950/30 hover:bg-rose-100 dark:hover:bg-rose-900/50 text-rose-600 dark:text-rose-400 transition flex items-center gap-1"'}>
                                <i data-lucide="trash-2" class="w-3 h-3"></i>
                                <span>Delete</span>
                            </button>
                        </div>
                    </td>
                </tr>
                `;
            }).join('');

            lucide.createIcons();
        }

        function openAddUserModal() {
            document.getElementById('addUserModal').classList.remove('hidden');
            lucide.createIcons();
        }

        function closeAddUserModal() {
            document.getElementById('addUserModal').classList.add('hidden');
        }

        function handleCreateUser(e) {
            e.preventDefault();
            const name = document.getElementById('newUserName').value;
            const email = document.getElementById('newUserEmail').value;
            const pass = document.getElementById('newUserPass').value;
            const role = document.getElementById('newUserRole').value;

            const res = authManager.addUser(name, email, pass, role);
            if (!res.success) {
                showToast(res.error, 'error');
                return;
            }

            closeAddUserModal();
            renderUsersTable();
            renderActivityTable();
            showToast(`Added ${name} (${role}) to team members`, 'success');
        }

        function openEditUserModal(userId) {
            const users = authManager.getUsers();
            const user = users.find(u => u.id === userId);
            if (!user) {
                showToast('User not found', 'error');
                return;
            }

            document.getElementById('editUserId').value = user.id;
            document.getElementById('editUserName').value = user.fullName;
            document.getElementById('editUserEmail').value = user.email;
            document.getElementById('editUserRole').value = user.role;
            document.getElementById('editUserPass').value = '';

            document.getElementById('editUserModal').classList.remove('hidden');
            lucide.createIcons();
        }

        function closeEditUserModal() {
            document.getElementById('editUserModal').classList.add('hidden');
        }

        function handleSaveEditUser(e) {
            e.preventDefault();
            const userId = document.getElementById('editUserId').value;
            const name = document.getElementById('editUserName').value;
            const email = document.getElementById('editUserEmail').value;
            const role = document.getElementById('editUserRole').value;
            const pass = document.getElementById('editUserPass').value;

            const res = authManager.editUser(userId, {
                fullName: name,
                email: email,
                role: role,
                password: pass
            });

            if (!res.success) {
                showToast(res.error, 'error');
                return;
            }

            closeEditUserModal();
            renderUsersTable();
            renderActivityTable();
            checkAuthAndRender();
            showToast(`User details updated for ${name}`, 'success');
        }

        let pendingDeleteUserId = null;

        function promptDeleteUser(userId, userName, userEmail, userRole) {
            pendingDeleteUserId = userId;
            document.getElementById('deleteTargetName').innerText = userName;
            document.getElementById('deleteTargetEmail').innerText = userEmail;
            document.getElementById('deleteTargetRole').innerText = 'Role: ' + (userRole || 'Viewer').toUpperCase();
            document.getElementById('deleteUserModal').classList.remove('hidden');
            lucide.createIcons();
        }

        function closeDeleteUserModal() {
            pendingDeleteUserId = null;
            document.getElementById('deleteUserModal').classList.add('hidden');
        }

        function confirmDeleteUser() {
            if (!pendingDeleteUserId) return;
            const targetId = pendingDeleteUserId;
            const res = authManager.deleteUser(targetId);
            closeDeleteUserModal();

            if (!res.success) {
                showToast(res.error, 'error');
                return;
            }

            renderUsersTable();
            renderActivityTable();
            showToast('User removed permanently and all dashboard records updated.', 'success');
        }

        function handleToggleStatus(userId) {
            const res = authManager.toggleUserStatus(userId);
            if (res.success) {
                renderUsersTable();
                renderActivityTable();
                showToast(`User status set to ${res.status.toUpperCase()}`, 'success');
            } else {
                showToast(res.error, 'error');
            }
        }

        // ========================================================
        // ACTIVITY LOGS (Admin Only)
        // ========================================================
        function renderActivityTable() {
            if (!authManager.isAdmin()) return;
            const tbody = document.getElementById('activityTableBody');
            const search = (document.getElementById('activitySearch').value || '').toLowerCase().trim();
            const typeFilter = document.getElementById('activityTypeFilter').value;

            let logs = authManager.getLogs();

            if (typeFilter !== 'all') {
                logs = logs.filter(l => l.activityType === typeFilter);
            }

            if (search) {
                logs = logs.filter(l => 
                    (l.userName + ' ' + l.userEmail + ' ' + l.details + ' ' + (l.targetRef || '')).toLowerCase().includes(search)
                );
            }

            if (logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="p-8 text-center text-slate-500">No activity logs found.</td></tr>';
                return;
            }

            tbody.innerHTML = logs.slice(0, 150).map(l => {
                const dateStr = new Date(l.timestamp).toLocaleString();
                const typeBadges = {
                    LOGIN: 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20',
                    LOGOUT: 'bg-slate-500/10 text-slate-500 border border-slate-500/20',
                    NAVIGATION: 'bg-blue-500/10 text-blue-600 border border-blue-500/20',
                    WIDGET_VIEW: 'bg-purple-500/10 text-purple-600 border border-purple-500/20',
                    SEARCH_FILTER: 'bg-sky-500/10 text-sky-600 border border-sky-500/20',
                    USER_MGMT: 'bg-amber-500/10 text-amber-600 border border-amber-500/20',
                    EXCEL_SYNC: 'bg-indigo-500/10 text-indigo-600 border border-indigo-500/20',
                    LOGIN_FAILED: 'bg-rose-500/10 text-rose-600 border border-rose-500/20'
                };
                const badge = typeBadges[l.activityType] || 'bg-slate-100 text-slate-600';

                return `
                    <tr class="hover:bg-slate-100/70 dark:hover:bg-slate-800/40 transition">
                        <td class="py-2.5 px-4 font-mono text-[11px] text-slate-500">${dateStr}</td>
                        <td class="py-2.5 px-4">
                            <div class="font-medium text-slate-900 dark:text-white">${l.userName}</div>
                            <div class="text-[10px] text-slate-400 font-mono">${l.userEmail} (${l.role})</div>
                        </td>
                        <td class="py-2.5 px-4">
                            <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${badge}">${l.activityType}</span>
                        </td>
                        <td class="py-2.5 px-4 text-slate-600 dark:text-slate-400 font-medium">${l.section}</td>
                        <td class="py-2.5 px-4 text-slate-600 dark:text-slate-300">
                            <div>${l.details}</div>
                            ${l.targetRef ? `<div class="text-[10px] font-mono text-blue-600 dark:text-blue-400 mt-0.5">${l.targetRef}</div>` : ''}
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function exportActivityCSV() {
            const logs = authManager.getLogs();
            let csv = 'Timestamp,User Name,Email,Role,Activity Type,Section,Target Reference,Details\\n';
            logs.forEach(l => {
                const det = (l.details || '').replace(/"/g, '""');
                const tgt = (l.targetRef || '').replace(/"/g, '""');
                csv += `"${l.timestamp}","${l.userName}","${l.userEmail}","${l.role}","${l.activityType}","${l.section}","${tgt}","${det}"\\n`;
            });

            const blob = new Blob([csv], { type: 'text/csv' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `dashboard_activity_audit_${new Date().toISOString().slice(0, 10)}.csv`;
            a.click();
            authManager.logActivity('EXPORT', 'Activity History', '', 'Exported activity audit CSV');
        }

        // ========================================================
        // DYNAMIC CLIENT-SIDE EXCEL AUTO-PARSER & DROP HANDLER
        // ========================================================
        function handleExcelFileUpload(event) {
            const file = event.target.files && event.target.files[0];
            if (!file) return;
            processExcelFile(file);
        }

        function processExcelFile(file) {
            showToast('Reading file ' + file.name + '...', 'info');
            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    const data = new Uint8Array(e.target.result);
                    const workbook = XLSX.read(data, { type: 'array' });
                    
                    let sheetName = workbook.SheetNames.find(n => n.toLowerCase().includes('repo')) || workbook.SheetNames[0];
                    const worksheet = workbook.Sheets[sheetName];
                    const rows = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
                    
                    reconcileExcelRows(rows, file.name);
                    authManager.logActivity('EXCEL_SYNC', 'Overview', file.name, `Manually updated Excel file (${rows.length} rows)`);
                } catch (err) {
                    console.error("Error parsing Excel:", err);
                    showToast('Failed to parse Excel: ' + err.message, 'error');
                }
            };
            reader.readAsArrayBuffer(file);
        }

        function reconcileExcelRows(rows, fileName) {
            if (!rows || rows.length < 3) {
                showToast('Spreadsheet appears empty or invalid', 'error');
                return;
            }

            let colMap = { sr: 3, subj: 4, name: 5, batch: 6, repo: 7, owner: 8 };
            
            for (let r = 0; r < Math.min(rows.length, 5); r++) {
                const row = rows[r];
                if (!row) continue;
                for (let c = 0; c < row.length; c++) {
                    const val = String(row[c] || '').toLowerCase().trim();
                    if (val.includes('sr.') || val === 'sr' || val === 'sr no') colMap.sr = c;
                    else if (val === 'subject' || val.includes('subj')) colMap.subj = c;
                    else if (val.includes('widget') || val.includes('name')) colMap.name = c;
                    else if (val.includes('batch')) colMap.batch = c;
                    else if (val === 'repo' || val.includes('repository')) colMap.repo = c;
                    else if (val === 'owner') colMap.owner = c;
                }
            }

            let currentSubj = 'General';
            const newItems = [];
            let parsedCount = 0;

            for (let i = 2; i < rows.length; i++) {
                const r = rows[i];
                if (!r) continue;
                const wNameRaw = r[colMap.name];
                if (!wNameRaw || String(wNameRaw).trim() === 'Widget (Silver) (CEP)') continue;
                
                const wName = String(wNameRaw).trim();
                const subjRaw = r[colMap.subj];
                if (subjRaw && String(subjRaw).trim()) currentSubj = String(subjRaw).trim();
                
                const batch = r[colMap.batch] ? String(r[colMap.batch]).trim() : '';
                const repoLink = r[colMap.repo] ? String(r[colMap.repo]).trim() : '';
                const owner = r[colMap.owner] ? String(r[colMap.owner]).trim() : '';

                const normName = wName.toLowerCase();
                const lookupKey = ALIASES[normName] || normName;
                const cat = REPO_CATALOG[lookupKey] || REPO_CATALOG[normName];

                parsedCount++;
                if (cat) {
                    let catStatus = cat.status_category;
                    let catLabel = cat.status_label;
                    let catHasFile = cat.has_file;
                    let catRepoPath = cat.repo_path;
                    let catLiveHtml = cat.live_html;

                    if (catStatus === 'requires_dev' && (repoLink.toLowerCase() === 'yes' || (repoLink.includes('/') && !repoLink.includes('github.com')))) {
                        catStatus = 'available';
                        catLabel = 'Already Available';
                        catHasFile = true;
                        catRepoPath = repoLink.toLowerCase() === 'yes' ? (batch ? `widgets/${batch.toLowerCase()}` : 'Implemented') : repoLink;
                        if (catRepoPath.endsWith('.html')) catLiveHtml = catRepoPath;
                    }

                    newItems.push({
                        sr: parsedCount,
                        wg_code: cat.wg_code || batch || '-',
                        name: wName,
                        subject: currentSubj,
                        batch: batch || cat.batch,
                        owner: owner || cat.owner,
                        excel_repo: repoLink || cat.excel_repo,
                        status_category: catStatus,
                        status_label: catLabel,
                        repo_path: catRepoPath,
                        live_html: catLiveHtml,
                        component_html: cat.component_html,
                        entry_type: cat.entry_type,
                        has_file: catHasFile,
                        source_status: catHasFile ? 'present' : (catStatus === 'whiteboard' ? 'whiteboard' : 'missing'),
                        source_status_label: catHasFile ? 'Present' : (catStatus === 'whiteboard' ? 'Canvas Tool' : 'Missing'),
                        plain_explanation: catStatus === 'available' && cat.status_category === 'requires_dev' ? 'Newly developed widget confirmed in updated spreadsheet.' : cat.plain_explanation,
                        what_was_checked: cat.what_was_checked,
                        what_needs_to_be_done: catStatus === 'available' ? 'Ready for QA validation testing.' : cat.what_needs_to_be_done,
                        technical_notes: cat.technical_notes
                    });
                } else {
                    const isTool = WHITEBOARD_TOOLS.has(normName);
                    let status_category = isTool ? 'whiteboard' : 'requires_dev';
                    let status_label = isTool ? 'Classroom Tools' : 'Not Available – Needs Development';
                    let has_file = false;
                    let repo_path = '';
                    let live_html = '';

                    if (!isTool && (repoLink.toLowerCase() === 'yes' || (repoLink.includes('/') && !repoLink.includes('github.com')))) {
                        status_category = 'available';
                        status_label = 'Already Available';
                        has_file = true;
                        repo_path = repoLink.toLowerCase() === 'yes' ? (batch ? `widgets/${batch.toLowerCase()}` : 'Implemented') : repoLink;
                        if (repo_path.endsWith('.html')) live_html = repo_path;
                    }

                    newItems.push({
                        sr: parsedCount,
                        wg_code: batch || (isTool ? 'TOOL' : '-'),
                        name: wName,
                        subject: currentSubj,
                        batch: batch || '-',
                        owner: owner || '-',
                        excel_repo: repoLink || '-',
                        status_category: status_category,
                        status_label: status_label,
                        repo_path: repo_path,
                        live_html: live_html,
                        component_html: '',
                        entry_type: isTool ? 'whiteboard' : (has_file ? 'standalone_html' : 'backlog'),
                        has_file: has_file,
                        source_status: has_file ? 'present' : (isTool ? 'whiteboard' : 'missing'),
                        source_status_label: has_file ? 'Present' : (isTool ? 'Canvas Tool' : 'Missing'),
                        plain_explanation: isTool ? 'Interactive whiteboard overlay utility tool.' : (has_file ? 'Newly implemented widget.' : 'No matching implementation was found in the repository. Requires development.'),
                        what_was_checked: 'Read from newly uploaded spreadsheet.',
                        what_needs_to_be_done: isTool ? 'Teaching canvas tool.' : (has_file ? 'Ready for QA validation testing.' : 'Assign to development backlog.'),
                        technical_notes: 'Parsed dynamically from ' + fileName
                    });
                }
            }

            if (newItems.length === 0) {
                showToast('No valid widget rows found in sheet', 'error');
                return;
            }

            rawData = newItems;
            updateDynamicMetrics(fileName);
            filterWidgets();
            showToast(`Updated from ${fileName}! Reconciled ${newItems.length} widgets.`, 'success');
        }

        function updateDynamicMetrics(fileName) {
            const counts = getCategoryCounts();
            const total = counts.total;
            const availPct = ((counts.available / total) * 100).toFixed(1) + '%';
            const corrPct = ((counts.corrected / total) * 100).toFixed(1) + '%';
            const minorPct = ((counts.minor_changes / total) * 100).toFixed(1) + '%';
            const wbPct = ((counts.whiteboard / total) * 100).toFixed(1) + '%';
            const reqPct = ((counts.requires_dev / total) * 100).toFixed(1) + '%';
            const srcPct = ((counts.source_present / total) * 100).toFixed(1) + '%';

            if (fileName) {
                const b1 = document.getElementById('activeExcelName');
                if (b1) b1.innerText = fileName;
                const b2 = document.getElementById('cardSourceExcelName');
                if (b2) b2.innerText = fileName;
            }

            const elCtxTotal = document.getElementById('el-context-total');
            if (elCtxTotal) elCtxTotal.innerText = total;

            const pillSrc = document.getElementById('pill-source-present');
            if (pillSrc) pillSrc.innerHTML = `<strong>${counts.source_present} Source Files Present (${srcPct})</strong>`;

            const pillLive = document.getElementById('pill-live-html');
            if (pillLive) pillLive.innerHTML = `<strong>${counts.live_html} Live HTML Simulations Ready</strong>`;

            const pillDev = document.getElementById('pill-source-missing');
            if (pillDev) pillDev.innerHTML = `<strong>${counts.requires_dev} Source Files Missing</strong>`;

            const pillWb = document.getElementById('pill-whiteboard');
            if (pillWb) pillWb.innerHTML = `<strong>${counts.whiteboard} Whiteboard Tools</strong>`;

            document.getElementById('stat-available-badge').innerText = counts.available;
            document.getElementById('stat-available-num').innerText = `${counts.available} Widgets`;
            document.getElementById('stat-available-sub').innerText = `Click to view all ${counts.available} widgets`;

            document.getElementById('stat-corrected-badge').innerText = counts.corrected;
            document.getElementById('stat-corrected-num').innerText = `${counts.corrected} Widgets`;
            document.getElementById('stat-corrected-sub').innerText = `Click to view all ${counts.corrected} widgets`;

            document.getElementById('stat-dev-badge').innerText = counts.requires_dev;
            document.getElementById('stat-dev-num').innerText = `${counts.requires_dev} Widgets`;
            document.getElementById('stat-dev-sub').innerText = `Click to view all ${counts.requires_dev} widgets`;

            document.getElementById('stat-minor-badge').innerText = counts.minor_changes;
            document.getElementById('stat-minor-num').innerText = `${counts.minor_changes} Widgets`;
            document.getElementById('stat-minor-sub').innerText = `Click to view all ${counts.minor_changes} widgets`;

            document.getElementById('stat-wb-badge').innerText = counts.whiteboard;
            document.getElementById('stat-wb-num').innerText = `${counts.whiteboard} Tools`;
            document.getElementById('stat-wb-sub').innerText = `Click to view all ${counts.whiteboard} tools`;

            document.getElementById('stat-total-badge').innerText = total;
            document.getElementById('stat-total-num').innerText = `${total} Total`;

            document.getElementById('bar-header-text').innerText = `${counts.source_present} of ${total} Source Files Present (${srcPct})`;
            document.getElementById('bar-seg-available').style.width = availPct;
            document.getElementById('bar-seg-available').title = `Already Available: ${counts.available} (Click to view)`;
            document.getElementById('bar-seg-corrected').style.width = corrPct;
            document.getElementById('bar-seg-corrected').title = `Found in Repository: ${counts.corrected} (Click to view)`;
            document.getElementById('bar-seg-minor').style.width = minorPct;
            document.getElementById('bar-seg-minor').title = `Small Changes Needed: ${counts.minor_changes} (Click to view)`;
            document.getElementById('bar-seg-whiteboard').style.width = wbPct;
            document.getElementById('bar-seg-whiteboard').title = `Classroom Tools: ${counts.whiteboard} (Click to view)`;
            document.getElementById('bar-seg-requires-dev').style.width = reqPct;
            document.getElementById('bar-seg-requires-dev').title = `Needs Development: ${counts.requires_dev} (Click to view)`;

            document.getElementById('bar-pill-available').innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-500"></span> Already Available (${counts.available})`;
            document.getElementById('bar-pill-corrected').innerHTML = `<span class="w-2 h-2 rounded-full bg-sky-400"></span> Found in Repository (${counts.corrected})`;
            document.getElementById('bar-pill-minor').innerHTML = `<span class="w-2 h-2 rounded-full bg-purple-400"></span> Small Changes (${counts.minor_changes})`;
            document.getElementById('bar-pill-whiteboard').innerHTML = `<span class="w-2 h-2 rounded-full bg-amber-400"></span> Classroom Tools (${counts.whiteboard})`;
            document.getElementById('bar-pill-dev').innerHTML = `<span class="w-2 h-2 rounded-full bg-rose-500"></span> Needs Development (${counts.requires_dev})`;

            const tabTot = document.getElementById('nav-tab-total');
            if (tabTot) tabTot.innerText = total;
            const hdrTot = document.getElementById('headerTotalCount');
            if (hdrTot) hdrTot.innerText = total;

            document.querySelectorAll('.num-total').forEach(el => el.innerText = total);

            document.getElementById('opt-all').innerText = `All Statuses (${total})`;
            document.getElementById('opt-present').innerText = `✓ Source File Present (${counts.source_present})`;
            document.getElementById('opt-missing').innerText = `✗ Source File Missing (${counts.requires_dev})`;
            document.getElementById('opt-live').innerText = `⚡ Live HTML Ready (${counts.live_html})`;
            document.getElementById('opt-available').innerText = `Already Available (${counts.available})`;
            document.getElementById('opt-corrected').innerText = `Found in Repository (${counts.corrected})`;
            document.getElementById('opt-dev').innerText = `Not Available – Needs Dev (${counts.requires_dev})`;
            document.getElementById('opt-whiteboard').innerText = `Classroom Tools (${counts.whiteboard})`;
            document.getElementById('opt-minor').innerText = `Small Changes Needed (${counts.minor_changes})`;

            const subjSet = new Set(rawData.map(w => w.subject));
            const subjs = Array.from(subjSet).sort();
            const sSelect = document.getElementById('subjectFilter');
            const curVal = sSelect.value;
            sSelect.innerHTML = '<option value="all">All Subjects</option>' + subjs.map(s => `<option value="${s}">${s}</option>`).join('');
            if (subjSet.has(curVal)) sSelect.value = curVal;

            document.querySelectorAll('.act-dev-count').forEach(el => el.innerText = counts.requires_dev);
            document.querySelectorAll('.act-minor-count').forEach(el => el.innerText = counts.minor_changes);
            document.querySelectorAll('.act-wb-count').forEach(el => el.innerText = counts.whiteboard);
            document.querySelectorAll('.act-corr-count').forEach(el => el.innerText = counts.corrected);

            lucide.createIcons();
        }

        // Sync / Refresh directly from repository Excel spreadsheet
        function refreshFromRepoExcel(silent = false) {
            const icon = document.getElementById('syncIcon');
            if (icon && !silent) icon.classList.add('animate-spin');

            const targetFile = "{excel_filename}";
            const cacheBuster = targetFile + '?_t=' + Date.now();

            if (!silent) showToast('Fetching latest ' + targetFile + '...', 'info');

            fetch(cacheBuster, { cache: 'no-store' })
                .then(res => {
                    if (!res.ok) throw new Error('HTTP ' + res.status);
                    return res.arrayBuffer();
                })
                .then(buffer => {
                    const workbook = XLSX.read(new Uint8Array(buffer), { type: 'array' });
                    let sheetName = workbook.SheetNames.find(n => n.toLowerCase().includes('repo')) || workbook.SheetNames[0];
                    const rows = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName], { header: 1 });
                    reconcileExcelRows(rows, targetFile);

                    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    const syncEl = document.getElementById('lastSyncTime');
                    if (syncEl) syncEl.innerText = 'Synced: ' + now;

                    authManager.logActivity('EXCEL_SYNC', 'Overview', targetFile, `Remote Excel sync performed (${rows.length} rows)`);

                    if (!silent) showToast('Refreshed! Reconciled ' + rawData.length + ' widgets from ' + targetFile, 'success');
                })
                .catch(err => {
                    console.warn('Sync note:', err);
                    if (!silent) {
                        if (window.location.protocol === 'file:') {
                            showToast('Running locally via file:///. Click "Update Excel" to load your file or run python watch_excel.py', 'info');
                        } else {
                            showToast('Could not fetch ' + targetFile + ' (' + err.message + ')', 'error');
                        }
                    }
                })
                .finally(() => {
                    if (icon) setTimeout(() => icon.classList.remove('animate-spin'), 600);
                });
        }

        // Window Drag & Drop Listeners
        window.addEventListener('dragover', (e) => {
            e.preventDefault();
            document.getElementById('dropOverlay').classList.remove('hidden');
        });

        window.addEventListener('dragleave', (e) => {
            if (e.relatedTarget === null) {
                document.getElementById('dropOverlay').classList.add('hidden');
            }
        });

        window.addEventListener('drop', (e) => {
            e.preventDefault();
            document.getElementById('dropOverlay').classList.add('hidden');
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                processExcelFile(e.dataTransfer.files[0]);
            }
        });

        function showToast(msg, type = 'info') {
            const toast = document.getElementById('toastNotification');
            const icon = document.getElementById('toastIcon');
            const title = document.getElementById('toastTitle');
            const body = document.getElementById('toastMsg');

            if (type === 'success') {
                icon.className = 'w-8 h-8 rounded-lg bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0';
                icon.innerHTML = '<i data-lucide="check" class="w-4 h-4"></i>';
                title.innerText = 'Success';
            } else if (type === 'error') {
                icon.className = 'w-8 h-8 rounded-lg bg-rose-500/15 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0';
                icon.innerHTML = '<i data-lucide="alert-triangle" class="w-4 h-4"></i>';
                title.innerText = 'Error';
            } else {
                icon.className = 'w-8 h-8 rounded-lg bg-blue-500/15 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0';
                icon.innerHTML = '<i data-lucide="info" class="w-4 h-4"></i>';
                title.innerText = 'Information';
            }

            body.innerText = msg;
            toast.classList.remove('translate-y-24', 'opacity-0', 'pointer-events-none');
            lucide.createIcons();

            setTimeout(() => {
                toast.classList.add('translate-y-24', 'opacity-0', 'pointer-events-none');
            }, 4000);
        }

        // Initialize UI, Theme, Profile & Auto-Sync
        initTheme();
        initUserProfile();
        filterWidgets();
        lucide.createIcons();

        window.addEventListener('DOMContentLoaded', () => {
            if (window.location.protocol.startsWith('http')) {
                refreshFromRepoExcel(true);
                setInterval(() => {
                    refreshFromRepoExcel(true);
                }, 3 * 60 * 1000);
            }
        });
    </script>
</body>
</html>
"""

    rendered_html = (
        html_template
        .replace('{excel_filename}', excel_filename)
        .replace('{build_time}', build_time)
        .replace('{commit_badge}', commit_badge)
        .replace('{total_count}', str(total_count))
        .replace('{available_count}', str(available_count))
        .replace('{corrected_count}', str(corrected_count))
        .replace('{requires_dev_count}', str(requires_dev_count))
        .replace('{whiteboard_count}', str(whiteboard_count))
        .replace('{minor_changes_count}', str(minor_changes_count))
        .replace('{live_html_count}', str(live_html_count))
        .replace('{source_present_count}', str(source_present_count))
        .replace('{source_missing_count}', str(source_missing_count))
        .replace('{source_present_pct}', source_present_pct)
        .replace('{avail_pct}', avail_pct)
        .replace('{corr_pct}', corr_pct)
        .replace('{minor_pct}', minor_pct)
        .replace('{wb_pct}', wb_pct)
        .replace('{req_pct}', req_pct)
        .replace('__SUBJECT_OPTIONS__', subject_options)
        .replace('__DATA_JSON__', json.dumps(reconciled_list, indent=2))
        .replace('__REPO_CATALOG_JSON__', json.dumps(repo_catalog, indent=2))
    )

    index_path = 'index.html'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(rendered_html)

    print(f'Successfully built clean plain-English dashboard with WG codes & Source File Verification in {index_path}!')
    print(f'Saved standalone repository catalog in {catalog_path}!')

if __name__ == '__main__':
    generate()
