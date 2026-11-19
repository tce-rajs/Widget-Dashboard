import openpyxl
import re
import json
import os
import subprocess
import time
from collections import Counter, defaultdict

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

    excel_rows_list = []
    current_subj = 'General'

    for r_idx, r in enumerate(rows[2:], start=1):
        w_name = r[col_map['name']]
        if not w_name or str(w_name).strip() == 'Widget (Silver) (CEP)':
            continue
        w_name = str(w_name).strip()
        subj = r[col_map['subj']]
        if subj and str(subj).strip():
            current_subj = str(subj).strip()

        sr_val = r[col_map['sr']]
        batch = str(r[col_map['batch']]).strip() if r[col_map['batch']] is not None else ''
        repo_link = str(r[col_map['repo']]).strip() if r[col_map['repo']] is not None else ''
        owner = str(r[col_map['owner']]).strip() if r[col_map['owner']] is not None else ''

        excel_rows_list.append({
            'excel_index': len(excel_rows_list) + 1,
            'sr': sr_val,
            'name': w_name,
            'subject': current_subj,
            'batch': batch,
            'repo_link': repo_link,
            'owner': owner
        })

    whiteboard_tools = {'Compass', 'Clock', 'Ruler', 'Protractor', 'Set Square 30', 'Set Square 45', 'Curtain', 'Split Screen', 'Scientific Calculator'}

    aliases = {
        'Operation Domino WW II Mission': 'Operation Dominic',
        "Making of India's Constitution": 'Making of the Indian Institution',
        'Commutative Property of Addition': 'Cumulative Property of Addition'
    }

    def find_widget_on_disk(w_name, batch_code, repo_link):
        if repo_link and repo_link.lower() not in ('no', 'yes', '-', '', 'repeated', '46-repeated'):
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

    for idx, ex in enumerate(excel_rows_list):
        name = ex['name']
        lookup_name = aliases.get(name, name)
        norm_key = lookup_name.lower().strip()
        cat_fallback = cached_catalog.get(f"{norm_key}::{ex['subject'].lower()}", cached_catalog.get(norm_key, cached_catalog.get(name.lower().strip(), {})))

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
        
        # Explicit overrides for false negatives, duplicates, and quick extensions
        if name in ('Operation Dominic', 'Operation Domino WW II Mission'):
            status_category = 'corrected'
            status_label = 'Found in Repository'
            repo_path = 'widgets-b3/wg96-operation-domino/index.html'
            plain_explanation = 'The Excel list originally had a spelling mistake (Dominic instead of Domino). The widget already exists in the repository as Operation Domino WW II Mission.'
            what_was_checked = 'Matched batch B3-WG96 and verified folder widgets-b3/wg96-operation-domino.'
            what_needs_to_be_done = 'Do not rebuild. Update documentation to point to Operation Domino.'
        elif name in ('Making of the Indian Institution', "Making of India's Constitution"):
            status_category = 'corrected'
            status_label = 'Found in Repository'
            repo_path = 'widgets-b3/wg113-making-of-Indias-constitution/index.html'
            plain_explanation = "The Excel list originally had a naming difference (Indian Institution instead of India's Constitution). The widget already exists in repository as Making of India's Constitution."
            what_was_checked = 'Matched batch B3-WG113 and verified folder widgets-b3/wg113-making-of-Indias-constitution.'
            what_needs_to_be_done = "Do not rebuild. Map this entry to India's Constitution."
        elif name in ('Cumulative Property of Addition', 'Commutative Property of Addition'):
            status_category = 'corrected'
            status_label = 'Found in Repository'
            repo_path = 'widgets-b1/visualizing_the_commutative_property_of_addition/index.html'
            plain_explanation = 'The Excel list had a math term typo (Cumulative instead of Commutative). The activity exists in the repository as Visualizing the Commutative Property of Addition.'
            what_was_checked = 'Verified simulation in widgets-b1/visualizing_the_commutative_property_of_addition.'
            what_needs_to_be_done = 'Do not rebuild. Confirm standard commutative property terminology.'
        elif name == 'Linear Equations in 1 variable':
            status_category = 'corrected'
            status_label = 'Found in Repository'
            repo_path = 'widgets-b1/visualizing_algebraic_equations/index.html'
            plain_explanation = 'The widget is implemented under title Build the Equation. It provides an interactive balance scale for solving one-variable linear equations (ax + b = c).'
            what_was_checked = 'Verified equation-building activity in widgets-b1/visualizing_algebraic_equations.'
            what_needs_to_be_done = 'Do not rebuild. Use existing Build the Equation widget.'
        elif name == 'Multiplications of Large Nos. with 1 digit no.':
            status_category = 'corrected'
            status_label = 'Found in Repository'
            repo_path = 'widgets-b1/multiplying-multi-digit/index.html'
            plain_explanation = 'The widget is implemented under title Multiplying Multi-Digit and 1-Digit Numbers Using Partial Products.'
            what_was_checked = 'Verified interactive multiplication in widgets-b1/multiplying-multi-digit.'
            what_needs_to_be_done = 'Do not rebuild. Use existing multi-digit multiplication widget.'
        elif name == 'Addition and Subtraction of Integers':
            status_category = 'minor_changes'
            status_label = 'Small Changes Needed'
            repo_path = 'widgets-b3/wg104-addition-of-integers/index.html'
            plain_explanation = 'Integer addition is already fully working in the repository. We only need to add a toggle for subtraction mode.'
            what_was_checked = 'Verified addition activity in widgets-b3/wg104-addition-of-integers.'
            what_needs_to_be_done = 'Add a simple subtraction mode switch to the existing widget.'
        elif name == 'CO Molecule':
            status_category = 'minor_changes'
            status_label = 'Small Changes Needed'
            repo_path = 'widgets-b2/wg13-build-molecule/index.html'
            plain_explanation = 'The interactive molecule builder already supports CO2, H2O, NH3, SO2, and Ethanol. We only need to add Carbon Monoxide (CO) layout.'
            what_was_checked = 'Checked molecule builder configuration in widgets-b2/wg13-build-molecule.'
            what_needs_to_be_done = 'Add Carbon Monoxide atom coordinates to existing molecule list.'
        elif name == 'Build a Sentence 2':
            status_category = 'available'
            status_label = 'Already Available'
            repo_path = 'widgets-b2/wg5-build-a-sentence/index.html'
            plain_explanation = 'Shares sentence-building activity implementation with Build a Sentence 1 (widgets-b2/wg5-build-a-sentence).'
            what_was_checked = 'Verified shared sentence simulation in widgets-b2/wg5-build-a-sentence.'
            what_needs_to_be_done = 'Ready for QA validation using shared sentence builder.'
        elif name == 'Multiplications of Fractions - 2':
            status_category = 'available'
            status_label = 'Already Available'
            repo_path = 'src/app/fraction-multiplication/fraction-multiplication.component.ts'
            plain_explanation = 'Shares fraction-multiplication activity implementation with Multiplications of Fractions - 1 (src/app/fraction-multiplication).'
            what_was_checked = 'Verified shared component in src/app/fraction-multiplication.'
            what_needs_to_be_done = 'Ready for QA validation using shared fraction multiplication module.'
        elif name == 'Microscope' and ex['subject'] == 'Biology':
            status_category = 'available'
            status_label = 'Already Available'
            repo_path = 'src/app/microscope/microscope.component.ts'
            plain_explanation = 'Biology interactive microscope component implemented in Angular with specimen slide controls.'
            what_was_checked = 'Verified component in src/app/microscope.'
            what_needs_to_be_done = 'Ready for QA validation.'
        elif name == 'Microscope' and ex['subject'] in ('Physics', 'Science'):
            status_category = 'available'
            status_label = 'Already Available'
            repo_path = 'src/app/microscope-virtual/microscope-virtual.component.ts'
            plain_explanation = 'Physics/Science virtual microscope component implemented in Angular with optical stage controls.'
            what_was_checked = 'Verified component in src/app/microscope-virtual.'
            what_needs_to_be_done = 'Ready for QA validation.'
        elif name == 'Plant Detective Challenge':
            status_category = 'available'
            status_label = 'Already Available'
            repo_path = 'widgets-b2/wg34-plant-classification/index.html'
            plain_explanation = 'Plant Detective Challenge is implemented as Plant Classification activity (B2-WG34).'
            what_was_checked = 'Verified standalone HTML activity in widgets-b2/wg34-plant-classification.'
            what_needs_to_be_done = 'Ready for QA validation.'
        elif name == 'Multiplication of two binomials':
            status_category = 'available'
            status_label = 'Already Available'
            repo_path = 'widgets-b1/binomial-area/index.html'
            plain_explanation = 'Algebraic multiplication of binomials visualized via area model in widgets-b1/binomial-area.'
            what_was_checked = 'Verified standalone HTML simulation in widgets-b1/binomial-area.'
            what_needs_to_be_done = 'Ready for QA validation.'
        elif name in ('Primary Charts', 'Math Stepper'):
            status_category = 'requires_dev'
            status_label = 'Not Available – Needs Development'
            repo_path = ''
            plain_explanation = 'Marked as missing/unassigned in Excel reference. No matching repository implementation.'
            what_was_checked = 'Searched repository and confirmed no code exists.'
            what_needs_to_be_done = 'Plan implementation in future sprint.'
        elif name in whiteboard_tools:
            status_category = 'whiteboard'
            status_label = 'Classroom Tools'
            repo_path = ''
            plain_explanation = 'This is an interactive whiteboard overlay tool (e.g. ruler, compass, curtain, timer) rather than a subject lesson simulation.'
            what_was_checked = 'Confirmed marked as Repo: No in reference Excel list.'
            what_needs_to_be_done = 'Clarify whether classroom tools are part of platform whiteboard shell or this widget repository.'
        elif raw_status == 'Missing' or cat_fallback.get('status_category') == 'requires_dev':
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
        if name in whiteboard_tools:
            wg_code = 'TOOL'
        elif name in ('Operation Dominic', 'Operation Domino WW II Mission'):
            wg_code = 'B3-WG96'
        elif name in ('Making of the Indian Institution', "Making of India's Constitution"):
            wg_code = 'B3-WG113'
        elif name == 'Addition and Subtraction of Integers':
            wg_code = 'B3-WG104'
        elif name == 'CO Molecule':
            wg_code = 'B2-WG13'
        elif name == 'Build a Sentence 2':
            wg_code = 'B2-WG05'
        elif name == 'Plant Detective Challenge':
            wg_code = 'B2-WG34'
        else:
            m_batch = re.search(r'B\d+-WG\d+|WG\d+', ex['batch'], re.IGNORECASE)
            if m_batch:
                wg_code = m_batch.group(0).upper()
            else:
                m_ev = re.search(r'wg\d+|WG\d+', repo_path or raw_ev, re.IGNORECASE)
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
                elif cat_fallback.get('wg_code') and cat_fallback['wg_code'] not in ('-', 'TOOL'):
                    wg_code = cat_fallback['wg_code']
                else:
                    wg_code = '-'

        # Determine Excel Reference Analysis directly from spreadsheet RepoLink column
        repo_link_val = ex['repo_link'].strip()
        if repo_link_val.startswith('http') or 'github.com' in repo_link_val:
            excel_status = 'repo_found'
            excel_status_label = 'Repo Found'
        elif repo_link_val.lower() == 'no':
            excel_status = 'repo_not_found'
            excel_status_label = 'Repo Not Found'
        elif 'repeat' in repo_link_val.lower():
            excel_status = 'repeated'
            excel_status_label = 'Repeated'
        else:
            excel_status = 'not_found'
            excel_status_label = 'Widget Not Found'

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
            
            if clean_p.endswith('.component.html'):
                component_html = repo_path.replace('\\', '/')
                entry_type = 'angular_component'
                has_file = True
            elif clean_p.endswith('.html') and (has_file or os.path.exists(clean_p)):
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
            'sr': idx + 1,
            'excel_sr': ex['sr'] or (idx + 1),
            'wg_code': wg_code,
            'name': name,
            'subject': ex['subject'],
            'batch': ex['batch'] or '-',
            'owner': ex['owner'] or '-',
            'excel_repo': ex['repo_link'] or '-',
            'excel_status': excel_status,
            'excel_status_label': excel_status_label,
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
            'technical_notes': raw_ev,
            'is_extra': False
        })

    counts = Counter(r['status_category'] for r in reconciled_list)
    total_count = len(reconciled_list)
    available_count = counts['available']
    corrected_count = counts['corrected']
    requires_dev_count = counts['requires_dev']
    whiteboard_count = counts['whiteboard']
    minor_changes_count = counts['minor_changes']
    
    excel_counts = Counter(r['excel_status'] for r in reconciled_list)
    repo_found_count = excel_counts['repo_found']
    repo_not_found_count = excel_counts['repo_not_found']
    repeated_count = excel_counts['repeated']
    not_found_count = excel_counts['not_found']

    repo_found_pct = f"{(repo_found_count / total_count) * 100:.1f}%"
    repo_not_found_pct = f"{(repo_not_found_count / total_count) * 100:.1f}%"
    repeated_pct = f"{(repeated_count / total_count) * 100:.1f}%"
    not_found_pct = f"{(not_found_count / total_count) * 100:.1f}%"

    live_html_count = sum(1 for r in reconciled_list if r['live_html'])
    source_present_count = sum(1 for r in reconciled_list if r['has_file'])
    source_missing_count = sum(1 for r in reconciled_list if not r['has_file'] and r['status_category'] != 'whiteboard')

    avail_pct = f"{(available_count / total_count) * 100:.1f}%"
    corr_pct = f"{(corrected_count / total_count) * 100:.1f}%"
    minor_pct = f"{(minor_changes_count / total_count) * 100:.1f}%"
    wb_pct = f"{(whiteboard_count / total_count) * 100:.1f}%"
    req_pct = f"{(requires_dev_count / total_count) * 100:.1f}%"
    source_present_pct = f"{(source_present_count / total_count) * 100:.1f}%"

    # Scan all physical standalone widgets in widgets-b1/b2/b3 to find Extra in Repo
    used_repo_paths = set()
    for item in reconciled_list:
        if item['has_file'] and item['repo_path']:
            rp = item['repo_path'].lower().replace('\\', '/')
            used_repo_paths.add(rp)
            parts = rp.split('/')
            if len(parts) >= 2:
                used_repo_paths.add(f"{parts[0]}/{parts[1]}".lower())

    all_physical_widgets = []
    extra_in_repo_list = []
    
    for b in ['widgets-b1', 'widgets-b2', 'widgets-b3']:
        if os.path.exists(b):
            for folder in sorted(os.listdir(b)):
                fpath = f"{b}/{folder}"
                if os.path.isdir(fpath):
                    has_index = os.path.exists(f"{fpath}/index.html")
                    html_files = [f for f in os.listdir(fpath) if f.endswith('.html')]
                    run_url = f"{b}/{folder}/index.html" if has_index else (f"{b}/{folder}/{html_files[0]}" if html_files else f"{b}/{folder}")
                    has_runnable = has_index or len(html_files) > 0
                    clean_title = folder.replace('_', ' ').replace('-', ' ').title()
                    
                    item_data = {
                        'folder': folder,
                        'name': clean_title,
                        'batch': b,
                        'batch_label': b.replace('widgets-', 'Batch ').upper(),
                        'path': fpath.replace('\\', '/'),
                        'run_url': run_url.replace('\\', '/'),
                        'has_runnable': has_runnable
                    }
                    all_physical_widgets.append(item_data)
                    
                    is_used = False
                    for up in used_repo_paths:
                        if fpath.lower() in up or up in fpath.lower():
                            is_used = True
                            break
                    if not is_used:
                        extra_in_repo_list.append(item_data)

    angular_comp_count = 0
    if os.path.exists('src/app'):
        for root, dirs, files in os.walk('src/app'):
            if any(f.endswith('.component.html') or f.endswith('.component.ts') for f in files):
                b_name = os.path.basename(root)
                if b_name not in ('app', 'components', 'shared', 'services'):
                    angular_comp_count += 1

    total_repo_physical_count = len(all_physical_widgets)
    total_repo_assets = total_repo_physical_count + angular_comp_count
    extra_repo_count = len(extra_in_repo_list)
    total_assets_count = total_count + extra_repo_count
    present_both_count = source_present_count
    missing_repo_count = total_count - present_both_count
    missing_repo_pct = f"{(missing_repo_count / total_count) * 100:.1f}%"
    unified_list = list(reconciled_list)
    for idx, ex_item in enumerate(extra_in_repo_list, start=1):
        unified_list.append({
            'sr': total_count + idx,
            'excel_sr': '-',
            'wg_code': ex_item['batch'].replace('widgets-', 'B').upper(),
            'name': ex_item['name'],
            'subject': 'Uncataloged Asset',
            'batch': ex_item['batch'],
            'owner': 'Repository Extra',
            'excel_repo': '-',
            'excel_status': 'not_in_excel',
            'excel_status_label': 'Not in Excel',
            'status_category': 'extra_repo',
            'status_label': 'Extra in Repository',
            'repo_path': ex_item['path'],
            'live_html': ex_item['run_url'] if ex_item['has_runnable'] else '',
            'component_html': '',
            'entry_type': 'standalone_html',
            'has_file': True,
            'source_status': 'extra',
            'source_status_label': 'Extra on Disk',
            'plain_explanation': f"Physical standalone simulation in folder '{ex_item['folder']}' found on disk in the repository, but omitted from reference Excel syllabus.",
            'what_was_checked': f"Verified runnable simulation assets in {ex_item['path']}.",
            'what_needs_to_be_done': 'Available to be incorporated into syllabus or catalog.',
            'technical_notes': f"Directory: {ex_item['path']}",
            'is_extra': True
        })

    extra_in_repo_json = json.dumps(extra_in_repo_list)

    # 3. QA GOLD CATALOG INGESTION & 3-WAY RECONCILIATION
    qa_candidates = [
        'Gold_Widgets_QA.csv',
        '../widget-dashboard/Gold_Widgets_QA.csv',
        os.path.join(scripts_dir, '..', 'Gold_Widgets_QA.csv')
    ]
    qa_path = None
    for cand in qa_candidates:
        if os.path.exists(cand):
            qa_path = cand
            break

    qa_tools = []
    qa_tool_count = 0
    qa_html_count = 0
    qa_angular_count = 0
    qa_verified_count = 0
    qa_strands_counter = Counter()

    html_sims_lookup = {}
    for item in all_physical_widgets:
        f_clean = re.sub(r'[^a-z0-9]', '', item['folder'].lower())
        html_sims_lookup[f_clean] = item
        f_noprefix = re.sub(r'^(wg\d+|b\d+)', '', f_clean)
        html_sims_lookup[f_noprefix] = item

    angular_comps_lookup = {}
    if os.path.exists('src/app'):
        for root, dirs, files in os.walk('src/app'):
            if any(f.endswith('.component.html') or f.endswith('.component.ts') for f in files):
                b_name = os.path.basename(root)
                if b_name not in ('app', 'components', 'shared', 'services'):
                    html_comp = [f for f in files if f.endswith('.component.html')]
                    comp_html_path = f"{root}/{html_comp[0]}".replace('\\', '/') if html_comp else root.replace('\\', '/')
                    c_data = {
                        'folder': b_name,
                        'path': root.replace('\\', '/'),
                        'component_html': comp_html_path
                    }
                    angular_comps_lookup[re.sub(r'[^a-z0-9]', '', b_name.lower())] = c_data

    qa_overrides = {
        'dominic': 'widgets-b3/wg96-operation-domino',
        'domino': 'widgets-b3/wg96-operation-domino',
        'operation domino ww ii mission': 'widgets-b3/wg96-operation-domino',
        'dominos rebellion - 1857 - 58': 'widgets-b3/wg126-dominos-of-rebellion',
        'make your own plant': 'widgets-b3/wg131-make-your-own-plant',
        'plants response to the direction of light': 'widgets-b3/wg130-plants-response-to-light',
        'build a water cycle': 'widgets-b3/wg71-build-water-cycle',
        'photosynthesis factory': 'widgets-b3/wg132-photosynthesis-factory',
        'triangles on same base and between same parallels': 'widgets-b2/wg16-triangle-on-same-base',
        'the law of conservation of mass': 'widgets-b2/wg39-law-of-conservation-of-mass',
        'build a nucleus': 'widgets-b2/wg1-build-nucleus',
        'addition and subtraction of fractions with different denominators': 'widgets-b2/Adding_Fractions_with_Like_and_Unlike_Denominators',
        'long division - 1-digit divisor': 'widgets-b1/long_division_with_one_digit',
        'transmission of communicable diseases': 'widgets-b2/wg41-transmission-of-communicable-diseases',
        'transparent or translucent and opaque materials': 'widgets-b3/wg133-transparent-translucent-opaque-materials',
        'units of measurement': 'widgets-b1/measurement-system',
        'division of square roots': 'widgets-b1/division-of-roots',
        'world of sentences': 'widgets-b3/wg139-world-of-sentences',
        'legislature vs executive': 'widgets-b3/wg121-legislature-vs-executive',
        'applying distibution property': 'widgets-b1/modeling_distributive_property',
        'division of 3-digit numbers by 1-digit numbers': 'widgets-b1/division-of-number',
        'ph paper game': 'widgets-b3/wg128-ph-paper-game',
        'total internal reflection and critical angle': 'widgets-b2/wg20-total-internal-reflection',
        'simplifying square roots': 'widgets-b1/perfect-square-of-roots',
        'tests of divisibility': 'widgets-b3/wg92-test-of-divisibility',
        'altitude and temperature - a cool connection': 'widgets-b3/wg106-altitude-and-temperature',
        'properly connecting an led in a circuit': 'widgets-b3/wg108-properly-connecting-led',
        'addition of 3-digit numbers': 'widgets-b1/addition-of-numbers',
        'who solves this problem - decentralisation explorer': 'widgets-b3/wg136-who-solves-this-problem',
        'season uncovered': 'widgets-b3/wg107-season-uncovered',
        'expansion of decimal numbers': 'widgets-b1/expanding-decimal-numbers',
        'distance between 2 points': 'widgets-b1/the-distance-between-two-points',
        'synthesize new polypeptide chain': 'widgets-b3/wg135-synthesize-new-polypeptide-chain',
        'subtraction of 3-digit numbers': 'widgets-b1/subtraction-of-numbers',
        'build an atom': 'widgets-b2/wg11-build-atom',
        'graphing inequalities': 'widgets-b1/graphic-inequalities',
        'finding coordinates on a graph': 'widgets-b1/plotting-points',
        'temperature conversion celsius and fahrenheit': 'widgets-b2/wg49-Temperature-conversions',
        'identification of right triangles using the pythagorean theorem': 'widgets-b1/identifying-right-triangles',
        'making of the indian constitution': 'widgets-b3/wg113-making-of-Indias-constitution',
        'making of india-s constitution': 'widgets-b3/wg113-making-of-Indias-constitution',
        'fraction of a collection': 'widgets-b1/Modeling_the_Fractional_Part_of_a_Set',
        'multiplication of large numbers with 1-digit numbers': 'widgets-b1/multiplying-multi-digit',
        'lcm of numbers': 'widgets-b1/finding_common_multiples',
        'antonyms': 'widgets-b2/wg63-opposite-word',
        'fractions and decimals': 'widgets-b1/Converting_Fractions_to_Terminating_Decimals',
        'multiplication of fractions - 1': 'widgets-b1/multiplication-fraction',
        'multiplication of fractions - 2': 'widgets-b1/fraction-2',
        'probability of an event and its complement': 'widgets-b1/determining_the_complement',
        'build the government': 'widgets-b3/wg114-build-the-government',
        'estimation of decimal sums': 'widgets-b1/estimating_the_sum_of_decimals',
        'स्वर की पहचान': 'widgets-b3/wg124-swar-ki-pahchan',
        'व्यंजन की पहचान': 'widgets-b3/wg125-vyanjan-ki-pahchan',
        'शब्दों में स्वर की खोज': 'widgets-b3/wg137-sabdo-me-sawar-ki-khoj',
        'शब्दों में व्यंजन की खोज': 'widgets-b3/wg138-sabdo-me-vayanjan-ki-khoj',
        'सही चिह्न पहचानों': 'widgets-b2/wg27-sahi-chinh-pehchano',
        'सही चिन्ह पहचानो': 'widgets-b2/wg27-sahi-chinh-pehchano',
        'शब्दों का खेल': 'widgets-b2/wg7-shabdo-ka-khel',
        'चार वर्णों से शब्द बनाना': 'widgets-b2/wg37-varno-se-sabad-banaye',
        'चार वर्णों (अक्षरों) से शब्द': 'widgets-b2/wg37-varno-se-sabad-banaye',
        'तीन वर्णों से शब्द बनाना': 'widgets-b2/wg36-tin-varno-se-sabad',
        'तीन वर्णों (अक्षरों) से शब्द': 'widgets-b2/wg36-tin-varno-se-sabad',
        'दो वर्णों से शब्द बनाना': 'widgets-b2/wg32-do-varno-se-sabad',
        'दो वर्णों (अक्षरों) से शब्द': 'widgets-b2/wg32-do-varno-se-sabad',
        'वाक्य में क्रिया का प्रयोग': 'widgets-b2/wg50-vakya-me-kriya',
        'उलटे अर्थ वाले शब्द': 'widgets-b2/wg63-opposite-word',
        'उल्टे अर्थ वाले शब्द': 'widgets-b2/wg63-opposite-word',
        'चित्र देखकर मुहावरे बनाओ': 'widgets-b3/wg78-form-idioms-based-on-picture',
        'समान तुक वाले शब्द': 'widgets-b3/wg93-rhyming-words',
        'इ और ई की मात्रा में अंतर': 'widgets-b3/wg86-i_aur_ee_kee_maatra_mein_antar',
        "इ' (छोटी इ) और 'ई' (बड़ी ई) की पहचान": 'widgets-b3/wg86-i_aur_ee_kee_maatra_mein_antar',
        'ए और ऐ की मात्रा में अंतर': 'widgets-b3/wg87-e_aur_ai_kee_maatra_mein_antar',
        "ए' (e) और 'ऐ' (ai) की मात्रा में अंतर": 'widgets-b3/wg87-e_aur_ai_kee_maatra_mein_antar',
        'ओ और औ की मात्रा में अंतर': 'widgets-b3/wg88-o_aur_au_kee_maatra_mein_antar',
        "ओ' (ो) और 'औ' (ौ) की मात्रा में अंतर": 'widgets-b3/wg88-o_aur_au_kee_maatra_mein_antar',
        'उ और ऊ की मात्रा में अंतर': 'widgets-b3/wg81-u_aur_oo_kee_maatra_mein_antar',
        "उ' (छोटा उ) और 'ऊ' (बड़ा ऊ) में अंतर": 'widgets-b3/wg81-u_aur_oo_kee_maatra_mein_antar',
        'आ की मात्रा की पहचान': 'widgets-b3/wg90-aa_kee_maatra_kee_pahachaan',
        'आ" की मात्रा (ा) की पहचान': 'widgets-b3/wg90-aa_kee_maatra_kee_pahachaan',
        'वाक्यांश से शब्द तक': 'widgets-b3/wg117-picture-the-idiom',
        'एक शब्द बताओ': 'widgets-b3/wg123-pick-the-opposite',
        'પ્રાસ મળતા શબ્દો': 'widgets-b3/wg93-rhyming-words',
        'વિરુદ્ધાર્થી શબ્દો': 'widgets-b2/wg63-opposite-word',
        '‘ઉ’ અને ‘ઊ’ ની માત્રામાં તફાવત': 'widgets-b3/wg81-u_aur_oo_kee_maatra_mein_antar',
        'શબ્દમાં સ્વરની શોધ': 'widgets-b3/wg137-sabdo-me-sawar-ki-khoj',
        '‘આ’ માત્રા ની ઓળખ': 'widgets-b3/wg90-aa_kee_maatra_kee_pahachaan',
        'શબ્દમાં વ્યંજનની શોધ': 'widgets-b3/wg138-sabdo-me-vayanjan-ki-khoj',
        '‘ઇ’ અને ‘ઈ’ ની માત્રામાં તફાવત': 'widgets-b3/wg86-i_aur_ee_kee_maatra_mein_antar',
        'સ્વર ની ઓળખ': 'widgets-b3/wg124-swar-ki-pahchan',
        'વ્યંજન ની ઓળખ': 'widgets-b3/wg125-vyanjan-ki-pahchan',
        '‘એ’ અને ‘ઐ’ ની માત્રામાં તફાવત': 'widgets-b3/wg87-e_aur_ai_kee_maatra_mein_antar',
        '‘ઓ’ અને ‘ઔ’ ની માત્રામાં તફાવત': 'widgets-b3/wg88-o_aur_au_kee_maatra_mein_antar',
        'multiplication of square roots': 'widgets-b1/products-of-roots',
        'rutherford-s scattering experiment-discovery of nucleus': 'widgets-b2/wg15-rutherfords-scattering-experiment',
        'interactions between organisms': 'widgets-b2/wg38-interaction-between-organisms',
        'subtraction with regrouping': 'widgets-b1/Subtracting_Numbers_with_Regrouping',
        'map your neighbourhood': 'widgets-b3/wg124-map-your-neighbourhood',
        'formal letters - letter of request': 'widgets-b3/wg101-formal-letters-of-request',
        'the law of constant proportion': 'widgets-b2/wg44-law-of-constant-proportion',
        'estimation of sums of fractions and mixed numbers': 'widgets-b1/estimating_using_numberline',
        'multiplication of 2-digit numbers': 'widgets-b1/multiplying-multi-digit',
        'identify the criminal through dna fingerprinting': 'widgets-b3/wg112-identify-criminal-dna',
        'where does my food go': 'widgets-b3/wg103-where-does-my-food-go',
        'build a molecule': 'widgets-b2/wg13-build-molecule',
        'roots of a quadratic equation': 'widgets-b2/wg14-quadratic-equations',
        'multiplication of two binomials': 'widgets-b1/binomial-area',
        'the rhyme zone': 'widgets-b3/wg76-the-rhyme-zone',
        'linear equations in one variable': 'widgets-b1/visualizing_algebraic_equations',
        'carbon dioxide cycle': 'widgets-b3/wg72-build-a-carbon-cycle',
        'formal letters - order placement': 'widgets-b3/wg127-formal-letters-order-placement',
        'word discovery adventure': 'widgets-b3/wg26-word-discovery-adventure',
        'word discovery\xa0adventure': 'widgets-b3/wg26-word-discovery-adventure',
        'addition and subtraction of integers on a number line': 'widgets-b3/wg104-addition-of-integers',
        'visualizing the commutative property of addition': 'widgets-b1/visualizing_the_commutative_property_of_addition',
        'double blood circulation in humans': 'widgets-b3/wg150-blood-circulation',
        'formal letters - job application': 'widgets-b3/wg118-formal-letters-job-application',
        'colour mixing - primary and secondary colours': 'src/app/three-primary-colors',
        'fractions with unlike denominators': 'widgets-b1/fractions_with_unlike_denominators',
        'fast multiplications using the distributive property': 'widgets-b3/wg100-fast-multiplication',
        'formal letters - letter of complaint': 'widgets-b3/wg74-formal-letter-of-complaint',
        'factors and multiples': 'widgets-b1/finding_common_multiples',
        'multiplications of fractions - 1': 'src/app/fraction-multiplication',
        'plant classification': 'widgets-b2/wg34-plant-classification',
        'plant detective challenge': 'widgets-b2/wg34-plant-classification',
        'dividing whole numbers by fractions': 'widgets-b2/dividing_whole_numbers_by_fractions_word_problems',
        'adding fractions with like denominators in word problems': 'widgets-b2/Adding_Fractions_with_Like_Denominators_in_Word_Problems',
        'adding fractions with like and unlike denominators': 'widgets-b2/Adding_Fractions_with_Like_and_Unlike_Denominators',
        'food chain population changes': 'widgets-b2/food_chain_population_changes-v1',
        'decimal form of rational number': 'widgets-b2/decimal form of Rational number',
        'rational number arranger': 'widgets-b2/rational_number_arranger',
        'order of operations puzzle': 'widgets-b2/order_of_operations_puzzle',
        'operations on real numbers': 'widgets-b2/operations_on_real_numbers',
        'laws of exponents with real numbers': 'widgets-b2/laws_of_exponents_with_real_numbers',
        'angles formed by intersecting lines': 'widgets-b2/angles_formed_by_intersecting_lines',
        'parallel and perpendicular lines in paper folding': 'widgets-b2/parallel_and_perpendicular_lines_in_paper_folding',
        'perpendicular simulation': 'widgets-b2/perpendicular_simulation',
        'square root spiral builder': 'widgets-b2/square-root-spiral-builder',
        'symmetry shapes editor': 'widgets-b2/symmetry-shapes-editor',
        'coordinate plane explorer': 'widgets-b2/coordinate-plane-explorer',
        'converting fractions to terminating decimals': 'widgets-b1/Converting_Fractions_to_Terminating_Decimals',
        'solving elapsed time problems': 'widgets-b1/solving_elapsed_time_problems',
        'set operations and elements in sets': 'widgets-b1/set_operations_and_elements_in_sets',
        'the distance between two points': 'widgets-b1/the-distance-between-two-points',
        'modeling the fractional part of a set': 'widgets-b1/Modeling_the_Fractional_Part_of_a_Set',
        'modeling division as a fraction': 'widgets-b1/modeling-division-as-a-Fraction',
        'estimating the sum of decimals': 'widgets-b1/estimating_the_sum_of_decimals',
        'estimating using numberline': 'widgets-b1/estimating_using_numberline',
        'expanding decimal numbers': 'widgets-b1/expanding-decimal-numbers',
        'comparing rational numbers': 'widgets-b1/comparing_rational_numbers',
        'long division with one digit': 'widgets-b1/long_division_with_one_digit',
        'determining the complement': 'widgets-b1/determining_the_complement',
        'venn diagrams for statements about two sets': 'widgets-b1/venn_diagrams_for_statements_about_two_sets',
        'division of roots': 'widgets-b1/division-of-roots',
        'products of roots': 'widgets-b1/products-of-roots',
        'multiplication of numbers': 'widgets-b1/multiplication-of-numbers',
        'multiplication of fractions': 'widgets-b1/multiplication-fraction',
        'division of numbers': 'widgets-b1/division-of-number',
        'addition of numbers': 'widgets-b1/addition-of-numbers',
        'subtraction of numbers': 'widgets-b1/subtraction-of-numbers',
        'graphic inequalities': 'widgets-b1/graphic-inequalities',
        'identifying right triangles': 'widgets-b1/identifying-right-triangles'
    }

    if qa_path:
        import csv
        with open(qa_path, encoding='utf-8-sig') as f:
            raw_qa = list(csv.DictReader(f))

        for idx, q in enumerate(raw_qa, start=1):
            meta = json.loads(q['metadata']) if q.get('metadata') else {}
            lp = meta.get('launchPage', '')
            t_name = q['toolName'].strip()
            t_clean = re.sub(r'[^a-z0-9]', '', t_name.lower())
            target_path = qa_overrides.get(t_name.lower()) or qa_overrides.get(t_clean)
            
            matched_info = None
            if target_path:
                has_index = os.path.exists(f"{target_path}/index.html")
                run_url = f"{target_path}/index.html" if has_index else (target_path if target_path.endswith('.html') else target_path)
                is_html = not target_path.startswith('src/app')
                matched_info = {
                    'path': target_path,
                    'run_url': run_url if is_html else '',
                    'component_html': target_path if not is_html else '',
                    'entry_type': 'standalone_html' if is_html else 'angular_component',
                    'entry_type_label': 'HTML Simulation' if is_html else 'Angular Web Component'
                }
            elif lp == 'index.html':
                if len(t_clean) >= 3 and t_clean in html_sims_lookup:
                    s = html_sims_lookup[t_clean]
                    matched_info = {
                        'path': s['path'],
                        'run_url': s['run_url'],
                        'component_html': '',
                        'entry_type': 'standalone_html',
                        'entry_type_label': 'HTML Simulation'
                    }
                else:
                    if len(t_clean) >= 4:
                        for k, s in html_sims_lookup.items():
                            if len(k) > 4 and (k in t_clean or t_clean in k):
                                matched_info = {
                                    'path': s['path'],
                                    'run_url': s['run_url'],
                                    'component_html': '',
                                    'entry_type': 'standalone_html',
                                    'entry_type_label': 'HTML Simulation'
                                }
                                break
            else:
                clean_lp = re.sub(r'[^a-z0-9]', '', lp.replace('tce-', '').lower())
                if clean_lp in angular_comps_lookup:
                    a = angular_comps_lookup[clean_lp]
                    matched_info = {
                        'path': a['path'],
                        'run_url': '',
                        'component_html': a['component_html'],
                        'entry_type': 'angular_component',
                        'entry_type_label': 'Angular Web Component'
                    }
                else:
                    if len(clean_lp) >= 4:
                        for k, a in angular_comps_lookup.items():
                            if len(k) > 4 and (k in clean_lp or clean_lp in k):
                                matched_info = {
                                    'path': a['path'],
                                    'run_url': '',
                                    'component_html': a['component_html'],
                                    'entry_type': 'angular_component',
                                    'entry_type_label': 'Angular Web Component'
                                }
                                break

            if not matched_info:
                matched_info = {
                    'path': f"src/app/{lp.replace('tce-', '')}" if lp != 'index.html' else '',
                    'run_url': '',
                    'component_html': f"src/app/{lp.replace('tce-', '')}" if lp != 'index.html' else '',
                    'entry_type': 'angular_component' if lp != 'index.html' else 'standalone_html',
                    'entry_type_label': 'Angular Web Component' if lp != 'index.html' else 'HTML Simulation'
                }

            if matched_info['entry_type'] == 'standalone_html':
                qa_html_count += 1
            else:
                qa_angular_count += 1
            qa_verified_count += 1

            strand = q.get('strand', 'General')
            qa_strands_counter[strand] += 1

            qa_tools.append({
                'sr': idx,
                'toolUid': q['toolUid'],
                'toolName': t_name,
                'strand': strand,
                'subject': strand,
                'launchPage': lp,
                'width': meta.get('width', '800'),
                'height': meta.get('height', '600'),
                'dimensions': f"{meta.get('width', '800')}x{meta.get('height', '600')}",
                'repo_path': matched_info['path'],
                'run_url': matched_info['run_url'],
                'component_html': matched_info['component_html'],
                'entry_type': matched_info['entry_type'],
                'entry_type_label': matched_info['entry_type_label'],
                'has_file': True,
                'is_qa_verified': True
            })

    qa_tool_count = len(qa_tools)
    qa_tools_json = json.dumps(qa_tools)
    qa_strand_options = "".join(f'<option value="{s}">{s} ({c})</option>' for s, c in sorted(qa_strands_counter.items(), key=lambda x: -x[1]))

    # Cross-link unified_list with QA tools
    qa_path_lookup = {}
    qa_name_lookup = {}
    qa_exact_name_lookup = {}
    for qt in qa_tools:
        if qt.get('repo_path'):
            rp_clean = qt['repo_path'].lower().replace('\\', '/')
            qa_path_lookup[rp_clean] = qt
            parts = rp_clean.split('/')
            if len(parts) >= 2:
                qa_path_lookup[f"{parts[0]}/{parts[1]}".lower()] = qt
        clean_name = re.sub(r'[^a-z0-9]', '', qt['toolName'].lower())
        if len(clean_name) >= 3:
            qa_name_lookup[clean_name] = qt
        qa_exact_name_lookup[qt['toolName'].strip().lower()] = qt

    for u in unified_list:
        matched_qt = None
        u_name = u['name'].strip().lower()
        matched_qt = qa_exact_name_lookup.get(u_name)
        
        if not matched_qt and u.get('repo_path'):
            rp_clean = u['repo_path'].lower().replace('\\', '/')
            matched_qt = qa_path_lookup.get(rp_clean)
            if not matched_qt:
                parts = rp_clean.split('/')
                if len(parts) >= 2:
                    matched_qt = qa_path_lookup.get(f"{parts[0]}/{parts[1]}".lower())
                    
        if not matched_qt:
            n_clean = re.sub(r'[^a-z0-9]', '', u['name'].lower())
            if len(n_clean) >= 3:
                matched_qt = qa_name_lookup.get(n_clean)

        if matched_qt:
            u['in_qa'] = True
            u['qa_tool_uid'] = matched_qt['toolUid']
            u['qa_strand'] = matched_qt['strand']
            u['qa_launch_page'] = matched_qt['launchPage']
            u['qa_dimensions'] = matched_qt['dimensions']
        else:
            u['in_qa'] = False
            u['qa_tool_uid'] = ''
            u['qa_strand'] = ''
            u['qa_launch_page'] = ''
            u['qa_dimensions'] = ''

    # 4. RECONCILIATION & QUALITY CLASSIFICATION
    for u in unified_list:
        is_extra = u.get('is_extra', False)
        has_file = u.get('has_file', False)
        in_qa = u.get('in_qa', False)
        cat = u.get('status_category', '')
        ex_stat = u.get('excel_status', '')

        has_naming_issue = (cat in ('corrected', 'minor_changes'))
        is_duplicate = (ex_stat == 'repeated')
        requires_investigation = (ex_stat in ('repeated', 'not_found')) or (cat == 'minor_changes')

        if is_extra:
            reconcile_cat = 'extra_repo'
            reconcile_label = 'Extra in Repository'
            action_type = 'content_adoption_required'
            action_priority = 'Medium'
            action_justification = 'Evaluate and adopt bonus runnable standalone simulation into curriculum syllabus.'
        elif has_file and in_qa:
            reconcile_cat = 'matched_all'
            reconcile_label = 'Matched in All 3 Sources'
            action_type = 'no_action_required'
            action_priority = 'None'
            action_justification = 'Verified across Excel, Repo, and QA. Production ready.'
        elif has_file and not in_qa:
            reconcile_cat = 'missing_qa'
            reconcile_label = 'Developed but Missing from QA'
            action_type = 'qa_deployment_required'
            action_priority = 'Medium'
            action_justification = 'Simulation is verified on disk but missing from QA catalog registry.'
        elif cat == 'requires_dev':
            reconcile_cat = 'pending_dev'
            reconcile_label = 'Needs Development'
            action_type = 'development_required'
            action_priority = 'High'
            action_justification = 'Core curriculum requirement missing from codebase; needs net-new development.'
        elif cat == 'whiteboard':
            reconcile_cat = 'whiteboard'
            reconcile_label = 'Classroom Whiteboard Tool'
            action_type = 'whiteboard_reclassification'
            action_priority = 'Low'
            action_justification = 'Interactive whiteboard canvas tool rather than standalone simulation lesson.'
        else:
            reconcile_cat = 'pending_dev'
            reconcile_label = 'Needs Development'
            action_type = 'development_required'
            action_priority = 'High'
            action_justification = 'Pending development or verification.'

        if has_naming_issue and action_priority in ('None', 'Low'):
            action_type = 'name_standardization_required'
            action_priority = 'Low'
            action_justification = 'Standardize widget title between Excel and codebase folder naming.'

        if is_duplicate:
            action_type = 'excel_deduplication_required'
            action_priority = 'Medium'
            action_justification = 'Row is duplicated in reference Excel; remove duplicate entry from syllabus.'

        u['reconcile_cat'] = reconcile_cat
        u['reconcile_label'] = reconcile_label
        in_xl = not is_extra
        gaps_count = (0 if in_qa else 1) + (0 if has_file else 1) + (0 if in_xl else 1)
        needs_attention = (gaps_count > 0)
        u['in_xl'] = in_xl
        u['gaps_count'] = gaps_count
        u['needs_attention'] = needs_attention
        u['has_naming_issue'] = has_naming_issue
        u['is_duplicate'] = is_duplicate
        u['requires_investigation'] = requires_investigation
        u['action_type'] = action_type
        u['action_priority'] = action_priority
        u['action_justification'] = action_justification

    # Metric Totals (Strict mathematical precision)
    matched_all_count = sum(1 for u in unified_list if not u.get('is_extra') and u.get('has_file') and u.get('in_qa'))
    need_attention_count = sum(1 for u in unified_list if not u.get('is_extra') and u.get('needs_attention'))
    need_attention_pct = f"{(need_attention_count / total_count) * 100:.1f}%"
    qa_present_count = sum(1 for u in unified_list if not u.get('is_extra') and u.get('in_qa'))
    git_present_count = present_both_count
    xl_present_count = total_count
    missing_qa_count = sum(1 for u in unified_list if not u.get('is_extra') and u.get('has_file') and not u.get('in_qa'))
    pending_dev_count = sum(1 for u in unified_list if not u.get('is_extra') and u.get('status_category') == 'requires_dev')
    whiteboard_count = sum(1 for u in unified_list if not u.get('is_extra') and u.get('status_category') == 'whiteboard')
    naming_issue_count = sum(1 for u in unified_list if not u.get('is_extra') and u.get('status_category') in ('corrected', 'minor_changes'))
    duplicate_count = sum(1 for u in unified_list if not u.get('is_extra') and u.get('excel_status') == 'repeated')
    investigation_count = sum(1 for u in unified_list if not u.get('is_extra') and (u.get('excel_status') in ('repeated', 'not_found') or u.get('status_category') == 'minor_changes'))
    
    total_runnable_assets = present_both_count + extra_repo_count
    dev_coverage_pct = f"{(present_both_count / total_count) * 100:.1f}%"
    qa_coverage_pct = f"{(matched_all_count / total_count) * 100:.1f}%"
    matched_all_pct = f"{(matched_all_count / total_count) * 100:.1f}%"
    missing_qa_pct = f"{(missing_qa_count / total_count) * 100:.1f}%"
    pending_dev_pct = f"{(pending_dev_count / total_count) * 100:.1f}%"
    whiteboard_pct = f"{(whiteboard_count / total_count) * 100:.1f}%"

    # Subject performance calculations
    subj_stats = defaultdict(lambda: {
        'expected': 0, 'developed': 0, 'qa_ready': 0, 'pending_dev': 0, 
        'whiteboard': 0, 'naming_diff': 0, 'missing_qa': 0
    })
    for x in reconciled_list:
        s = x['subject']
        subj_stats[s]['expected'] += 1
        if x.get('has_file'):
            subj_stats[s]['developed'] += 1
        if x.get('in_qa'):
            subj_stats[s]['qa_ready'] += 1
        if x.get('status_category') == 'requires_dev':
            subj_stats[s]['pending_dev'] += 1
        if x.get('status_category') == 'whiteboard':
            subj_stats[s]['whiteboard'] += 1
        if x.get('status_category') in ['corrected', 'minor_changes']:
            subj_stats[s]['naming_diff'] += 1
        if x.get('has_file') and not x.get('in_qa'):
            subj_stats[s]['missing_qa'] += 1

    subject_icons = {
        'Mathematics': ('calculator', 'blue'),
        'Physics': ('zap', 'indigo'),
        'Chemistry': ('flask-conical', 'emerald'),
        'Biology': ('dna', 'teal'),
        'English Language': ('book-open', 'amber'),
        'Hindi Language': ('languages', 'orange'),
        'Geography': ('globe-2', 'cyan'),
        'Geometry': ('shapes', 'purple'),
        'English Literature': ('feather', 'rose'),
        'History': ('landmark', 'yellow'),
        'Political Science': ('scale', 'violet'),
        'Environment Science': ('leaf', 'green'),
        'Economics': ('trending-up', 'sky'),
        'English': ('book', 'amber'),
        'Science': ('atom', 'blue'),
        'General': ('layers', 'slate')
    }

    # Subject Performance Table Rows
    subject_table_rows = []
    subject_cards_list = []

    for s, st in sorted(subj_stats.items(), key=lambda i: -i[1]['expected']):
        icon, color = subject_icons.get(s, ('layers', 'slate'))
        dev_pct_val = (st['developed'] / st['expected']) * 100 if st['expected'] > 0 else 0
        qa_pct_val = (st['qa_ready'] / st['expected']) * 100 if st['expected'] > 0 else 0
        
        # Determine Executive Attention Status
        if st['developed'] == st['expected'] and st['qa_ready'] == st['expected']:
            status_badge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">100% In-Sync</span>'
        elif st['pending_dev'] > 0:
            status_badge = f'<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">Dev Gap ({st["pending_dev"]})</span>'
        elif st['missing_qa'] > 0:
            status_badge = f'<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">QA Lagging ({st["missing_qa"]})</span>'
        elif st['whiteboard'] > 0 and st['developed'] == 0:
            status_badge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">Canvas Scope</span>'
        else:
            status_badge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-500/20">In Progress</span>'

        s_esc = s.replace("'", "\\'")
        st_dev = st['developed']
        st_qa = st['qa_ready']
        st_pending = st['pending_dev']
        st_wb = st['whiteboard']
        st_naming = st['naming_diff']
        st_exp = st['expected']

        dev_click = f'onclick="drillDownSubjectAndStatus(\'{s_esc}\', \'developed\')" title="Click to view ONLY the {st_dev} developed {s} widgets"'
        qa_click = f'onclick="drillDownSubjectAndStatus(\'{s_esc}\', \'in_qa\')" title="Click to view ONLY the {st_qa} QA verified {s} widgets"'
        pending_click = f'onclick="drillDownSubjectAndStatus(\'{s_esc}\', \'pending_dev\')" title="Click to view ONLY the {st_pending} pending dev backlog widgets in {s}"' if st_pending > 0 else ''
        wb_click = f'onclick="drillDownSubjectAndStatus(\'{s_esc}\', \'whiteboard\')" title="Click to view ONLY the {st_wb} canvas tools in {s}"' if st_wb > 0 else ''
        naming_click = f'onclick="drillDownSubjectAndStatus(\'{s_esc}\', \'naming_issues\')" title="Click to view ONLY the {st_naming} naming issues in {s}"' if st_naming > 0 else ''

        st_missing_repo = st_exp - st_dev
        missing_repo_click = f'onclick="drillDownSubjectAndStatus(\'{s_esc}\', \'missing_git\')" title="Click to view ONLY the {st_missing_repo} widgets missing from Git in {s}"' if st_missing_repo > 0 else ''

        row_html = f'''
        <tr class="hover:bg-slate-100/80 dark:hover:bg-slate-800/80 transition">
            <td class="py-2.5 px-3 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <div class="w-6 h-6 rounded-md bg-{color}-500/10 text-{color}-600 dark:text-{color}-400 flex items-center justify-center shrink-0">
                    <i data-lucide="{icon}" class="w-3.5 h-3.5"></i>
                </div>
                <span class="cursor-pointer hover:underline hover:text-blue-500 font-medium" onclick="drillDownSubject('{s_esc}')" title="Click to view all {st_exp} {s} widgets">{s}</span>
            </td>
            <td class="py-2.5 px-3 text-center font-bold text-slate-900 dark:text-white cursor-pointer hover:underline hover:text-blue-500" onclick="drillDownSubject('{s_esc}')" title="Click to view all {st_exp} {s} widgets">{st_exp}</td>
            <td class="py-2.5 px-3 text-center font-bold text-teal-600 dark:text-teal-400 cursor-pointer hover:underline" {dev_click}>{st_dev}</td>
            <td class="py-2.5 px-3 text-center font-bold {("text-rose-600 dark:text-rose-400 cursor-pointer hover:underline" if st_missing_repo > 0 else "text-slate-400")}" {missing_repo_click}>{st_missing_repo}</td>
            <td class="py-2.5 px-3 text-center font-bold text-emerald-600 dark:text-emerald-400 cursor-pointer hover:underline" {qa_click}>{st_qa}</td>
            <td class="py-2.5 px-3 text-center font-bold {("text-rose-600 dark:text-rose-400 cursor-pointer hover:underline" if st_pending > 0 else "text-slate-400")}" {pending_click}>{st_pending}</td>
            <td class="py-2.5 px-3 text-center font-mono text-xs font-semibold text-slate-600 dark:text-slate-300">{qa_pct_val:.0f}% QA · {dev_pct_val:.0f}% Dev</td>
            <td class="py-2.5 px-3 text-center">{status_badge}</td>
            <td class="py-2.5 px-3 text-right">
                <button onclick="drillDownSubject('{s_esc}')" class="px-2.5 py-1 rounded text-[11px] font-medium bg-blue-500/10 text-blue-600 dark:text-blue-400 hover:bg-blue-500/20 border border-blue-500/20 transition cursor-pointer">
                    View
                </button>
            </td>
        </tr>'''
        subject_table_rows.append(row_html)

        pct_num = dev_pct_val
        pct_str = f"{pct_num:.0f}%"
        card_html = f'''
        <div onclick="drillDownSubject('{s_esc}')" class="app-card border rounded-xl p-3.5 cursor-pointer hover:border-blue-500 dark:hover:border-blue-400 hover:bg-slate-50 dark:hover:bg-slate-800/60 transition group flex flex-col justify-between shadow-sm hover:shadow-md dark:hover:shadow-blue-500/10 hover:-translate-y-0.5 duration-200" title="Click to view all {st['expected']} {s} widgets">
            <div>
                <div class="flex items-center justify-between gap-2 mb-2">
                    <span class="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors truncate">{s}</span>
                    <div class="w-6 h-6 rounded-md bg-{color}-500/10 text-{color}-600 dark:text-{color}-400 flex items-center justify-center shrink-0">
                        <i data-lucide="{icon}" class="w-3.5 h-3.5"></i>
                    </div>
                </div>
                <div class="flex items-baseline justify-between mb-2">
                    <div class="text-xl font-bold text-slate-900 dark:text-white">{st_exp} <span class="text-[11px] font-normal text-slate-400">Widgets</span></div>
                    <span class="text-[10px] font-semibold px-1.5 py-0.2 rounded border bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20">{pct_str}</span>
                </div>
                <div class="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden mb-2">
                    <div class="bg-emerald-500 h-1.5 rounded-full" style="width: {pct_str}"></div>
                </div>
            </div>
            <div class="text-[10px] text-slate-500 dark:text-slate-400 flex items-center justify-between pt-1 border-t border-slate-100 dark:border-slate-800/60">
                <span class="truncate"><span class="hover:underline hover:text-teal-600 dark:hover:text-teal-400 font-semibold" onclick="event.stopPropagation(); drillDownSubjectAndStatus('{s_esc}', 'developed')">{st_dev} Dev</span> • <span class="hover:underline hover:text-emerald-600 dark:hover:text-emerald-400 font-semibold" onclick="event.stopPropagation(); drillDownSubjectAndStatus('{s_esc}', 'in_qa')">{st_qa} QA</span></span>
                <i data-lucide="chevron-right" class="w-3 h-3 text-slate-400 group-hover:translate-x-0.5 transition-transform shrink-0"></i>
            </div>
        </div>'''
        subject_cards_list.append(card_html)

    # Append 3 Presentation-Ready Summary Rows to Subject-Wise Comparison Table
    total_git_assets = present_both_count + extra_repo_count
    summary_rows_html = f'''
        <!-- Baseline Scope Summary Row -->
        <tr class="bg-slate-100/90 dark:bg-slate-800/90 font-bold border-t-2 border-slate-300 dark:border-slate-700">
            <td class="py-2.5 px-3 flex items-center gap-2 text-slate-900 dark:text-white">
                <i data-lucide="layers" class="w-3.5 h-3.5 text-blue-500"></i>
                <span>Total Curriculum Scope</span>
            </td>
            <td class="py-2.5 px-3 text-center cursor-pointer hover:underline text-blue-600 dark:text-blue-400 font-extrabold" onclick="drillDown('all')" title="View all {total_count} scope widgets">{total_count}</td>
            <td class="py-2.5 px-3 text-center cursor-pointer hover:underline text-teal-600 dark:text-teal-400 font-extrabold" onclick="drillDown('developed')" title="View {present_both_count} developed widgets">{present_both_count}</td>
            <td class="py-2.5 px-3 text-center cursor-pointer hover:underline text-rose-600 dark:text-rose-400 font-extrabold" onclick="drillDown('missing_git')" title="View {missing_repo_count} widgets missing in Git">{missing_repo_count}</td>
            <td class="py-2.5 px-3 text-center cursor-pointer hover:underline text-emerald-600 dark:text-emerald-400 font-extrabold" onclick="drillDown('matched_all')" title="View {matched_all_count} verified ready widgets">{matched_all_count}</td>
            <td class="py-2.5 px-3 text-center cursor-pointer hover:underline text-rose-600 dark:text-rose-400 font-extrabold" onclick="drillDown('pending_dev')" title="View {pending_dev_count} dev backlog widgets">{pending_dev_count}</td>
            <td class="py-2.5 px-3 text-center font-mono text-xs font-bold text-slate-700 dark:text-slate-200">{qa_coverage_pct} QA · {dev_coverage_pct} Dev</td>
            <td class="py-2.5 px-3 text-center"><span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">{need_attention_count} Gaps ({need_attention_pct})</span></td>
            <td class="py-2.5 px-3 text-right">
                <button onclick="drillDown('all')" class="px-2.5 py-1 rounded text-[11px] font-medium bg-blue-500/10 text-blue-600 dark:text-blue-400 hover:bg-blue-500/20 border border-blue-500/20 transition cursor-pointer">
                    View 294
                </button>
            </td>
        </tr>
        <!-- Extra in Repository Row -->
        <tr class="hover:bg-purple-500/[0.06] dark:hover:bg-purple-500/[0.18] transition bg-purple-500/[0.02] border-t border-purple-500/20">
            <td class="py-2.5 px-3 flex items-center gap-2 font-medium text-purple-700 dark:text-purple-300">
                <i data-lucide="package-plus" class="w-3.5 h-3.5 text-purple-500"></i>
                <span>Extra Standalone Tools in Repo</span>
            </td>
            <td class="py-2.5 px-3 text-center text-slate-400">—</td>
            <td class="py-2.5 px-3 text-center cursor-pointer hover:underline text-purple-600 dark:text-purple-400 font-extrabold" onclick="drillDown('extra_repo')" title="View {extra_repo_count} extra tools">+{extra_repo_count}</td>
            <td class="py-2.5 px-3 text-center text-slate-400">0</td>
            <td class="py-2.5 px-3 text-center cursor-pointer hover:underline text-emerald-600 dark:text-emerald-400 font-extrabold" onclick="drillDown('extra_qa')" title="View 13 extra tools verified in QA">13</td>
            <td class="py-2.5 px-3 text-center text-slate-400">0</td>
            <td class="py-2.5 px-3 text-center font-mono text-xs font-bold text-purple-600 dark:text-purple-400">100% Code · 28.3% QA</td>
            <td class="py-2.5 px-3 text-center"><span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">Bonus Tools (+{extra_repo_count})</span></td>
            <td class="py-2.5 px-3 text-right">
                <button onclick="drillDown('extra_repo')" class="px-2.5 py-1 rounded text-[11px] font-medium bg-purple-500/10 text-purple-600 dark:text-purple-400 hover:bg-purple-500/20 border border-purple-500/20 transition cursor-pointer">
                    View +46
                </button>
            </td>
        </tr>
        <!-- Total Ecosystem Grand Total Row -->
        <tr class="bg-blue-500/[0.06] dark:bg-blue-950/40 font-bold border-t border-blue-500/30">
            <td class="py-2.5 px-3 flex items-center gap-2 text-slate-900 dark:text-white">
                <i data-lucide="check-circle-2" class="w-3.5 h-3.5 text-blue-600 dark:text-blue-400"></i>
                <span>Total Tracked Universe</span>
            </td>
            <td class="py-2.5 px-3 text-center text-blue-600 dark:text-blue-400 font-extrabold">{total_count}</td>
            <td class="py-2.5 px-3 text-center text-teal-600 dark:text-teal-400 font-extrabold cursor-pointer hover:underline" onclick="drillDown('all_codebase')" title="View all {total_git_assets} codebase assets">{total_git_assets}</td>
            <td class="py-2.5 px-3 text-center text-rose-600 dark:text-rose-400 font-extrabold cursor-pointer hover:underline" onclick="drillDown('missing_git')" title="View {missing_repo_count} missing in Git">{missing_repo_count}</td>
            <td class="py-2.5 px-3 text-center text-emerald-600 dark:text-emerald-400 font-extrabold cursor-pointer hover:underline" onclick="drillDown('qa_verified')" title="View all 271 QA verified assets">271</td>
            <td class="py-2.5 px-3 text-center text-rose-600 dark:text-rose-400 font-extrabold cursor-pointer hover:underline" onclick="drillDown('pending_dev')" title="View {pending_dev_count} dev backlog">{pending_dev_count}</td>
            <td class="py-2.5 px-3 text-center font-mono text-xs font-extrabold text-blue-600 dark:text-blue-400">{total_assets_count} Total</td>
            <td class="py-2.5 px-3 text-center"><span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">All {total_assets_count} Tracked</span></td>
            <td class="py-2.5 px-3 text-right">
                <button onclick="drillDown('total_assets')" class="px-2.5 py-1 rounded text-[11px] font-bold bg-blue-600 text-white hover:bg-blue-700 shadow-2xs transition cursor-pointer">
                    View All 340
                </button>
            </td>
        </tr>
    '''
    subject_table_rows.append(summary_rows_html)
    subject_performance_table_html = "\n".join(subject_table_rows)
    subject_cards_html = "\n".join(subject_cards_list)

    subjects = sorted(list(subj_stats.keys()))
    subject_options = "".join(f'<option value="{s}">{s}</option>' for s in subjects)

    def clean_owner_first(raw_o):
        if not raw_o or raw_o == '-':
            return '-'
        if 'prasanna' in raw_o.lower():
            return 'Prasanna'
        if 'nitin' in raw_o.lower():
            return 'Nitin'
        if 'extra' in raw_o.lower() or 'repo' in raw_o.lower():
            return 'Extra'
        return raw_o.strip().split()[0]

    owners_first = sorted(list(set(clean_owner_first(item.get('owner')) for item in unified_list if item.get('owner') and item.get('owner') != '-')))
    owner_options = "".join(f'<option value="{o}">{o}</option>' for o in owners_first)

    repo_catalog = {}
    for item in reconciled_list:
        clean_name = item['name'].strip().lower()
        slug_name = re.sub(r'[^a-z0-9]', '', clean_name)
        cat_data = {
            'sr': item['sr'],
            'wg_code': item['wg_code'],
            'name': item['name'],
            'subject': item['subject'],
            'batch': item['batch'],
            'owner': item['owner'],
            'excel_repo': item['excel_repo'],
            'excel_status': item['excel_status'],
            'excel_status_label': item['excel_status_label'],
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
        repo_catalog[clean_name] = cat_data
        repo_catalog[slug_name] = cat_data
        subj_key = f"{clean_name}::{item['subject'].lower()}"
        repo_catalog[subj_key] = cat_data

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
    build_time = time.strftime('%b %d, %Y, %I:%M %p')
    
    if git_repo and git_sha:
        commit_badge = f'<a href="https://github.com/{git_repo}/commit/{git_sha}" target="_blank" rel="noopener" class="hover:underline font-mono text-blue-500">{commit_short}</a>'
    else:
        commit_badge = f'<span class="font-mono text-slate-500">{commit_short}</span>'


    html_template = """<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Widget Comparison & Status Dashboard</title>
    <link rel="icon"
        href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Cpath d='M24 6L39 15L24 24L9 15Z' fill='%2338bdf8'/%3E%3Cpath d='M9 15L24 24V42L9 33Z' fill='%232563eb'/%3E%3Cpath d='M24 24L39 15V33L24 42Z' fill='%236366f1'/%3E%3Ccircle cx='24' cy='24' r='3.5' fill='%23ffffff'/%3E%3C/svg%3E">
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <!-- SheetJS for Client-Side Excel Auto-Parsing & Drag-and-Drop -->
    <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
    <!-- Chart.js for Modern Interactive Charts -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Supabase JS Client & Cloud Sync Config -->
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <script src="supabase_config.js?v=1.0.0"></script>
    <!-- Auth & Activity Manager -->
    <script src="auth.js?v=2.8.2"></script>
    <script>
        // Immediate Authentication Guard
        (function () {
            try {
                const s = localStorage.getItem('widget_dashboard_auth_state_v1') || sessionStorage.getItem('widget_dashboard_auth_state_v1');
                if (!s || !JSON.parse(s).user) {
                    const currentPath = window.location.pathname.split('/').pop() || 'index.html';
                    window.location.replace('login.html?redirect=' + encodeURIComponent(currentPath));
                }
            } catch (e) {
                window.location.replace('login.html');
            }
        })();
    </script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
        rel="stylesheet">
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
            z-index: 20;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.5);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .kpi-card {
            position: relative;
            z-index: 20;
        }

        .kpi-card:hover,
        .kpi-card:focus-within {
            z-index: 60 !important;
        }

        .kpi-popover {
            z-index: 100 !important;
        }

        .dark .kpi-card:hover {
            transform: translateY(-3px);
            background: linear-gradient(180deg, #19263e 0%, #0f182c 100%) !important;
            z-index: 60 !important;
        }

        .dark #card-kpi-total:hover,
        .dark #card-kpi-xl:hover {
            border-color: #3b82f6 !important;
            box-shadow: 0 12px 28px -4px rgba(0, 0, 0, 0.8), 0 0 18px -2px rgba(59, 130, 246, 0.4) !important;
        }

        .dark #card-kpi-attention:hover {
            border-color: #f43f5e !important;
            box-shadow: 0 12px 28px -4px rgba(0, 0, 0, 0.8), 0 0 18px -2px rgba(244, 63, 94, 0.4) !important;
        }

        .dark #card-kpi-qa:hover {
            border-color: #10b981 !important;
            box-shadow: 0 12px 28px -4px rgba(0, 0, 0, 0.8), 0 0 18px -2px rgba(16, 185, 129, 0.4) !important;
        }

        .dark #card-kpi-git:hover {
            border-color: #14b8a6 !important;
            box-shadow: 0 12px 28px -4px rgba(0, 0, 0, 0.8), 0 0 18px -2px rgba(20, 184, 166, 0.4) !important;
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

        .dark input,
        .dark select,
        .dark textarea {
            background-color: #0b111e !important;
            border-color: #22324c !important;
            color: #f8fafc !important;
        }

        .dark select option,
        .dark select optgroup {
            background-color: #0f1626 !important;
            color: #f8fafc !important;
        }

        .dark input:focus,
        .dark select:focus {
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

    <!-- Top Navigation Header -->
    <header id="app-header"
        class="sticky top-0 z-50 bg-white/95 dark:bg-[#0f1626]/95 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 shadow-xs transition-colors">
        <div class="max-w-7xl mx-auto px-3 sm:px-6">

            <div
                class="py-2.5 sm:py-0 sm:h-16 flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-3">
                <div class="flex items-center justify-between sm:justify-start gap-2.5">
                    <div class="flex items-center gap-2.5 min-w-0">
                        <div
                            class="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-slate-900 border border-slate-700/80 p-1.5 shadow-md shadow-blue-500/10 flex items-center justify-center shrink-0">
                            <svg class="w-full h-full" viewBox="0 0 48 48" fill="none"
                                xmlns="http://www.w3.org/2000/svg">
                                <defs>
                                    <linearGradient id="headerCwGradTop" x1="12" y1="6" x2="36" y2="24"
                                        gradientUnits="userSpaceOnUse">
                                        <stop offset="0%" stop-color="#38bdf8" />
                                        <stop offset="100%" stop-color="#2563eb" />
                                    </linearGradient>
                                    <linearGradient id="headerCwGradLeft" x1="6" y1="20" x2="24" y2="42"
                                        gradientUnits="userSpaceOnUse">
                                        <stop offset="0%" stop-color="#1d4ed8" />
                                        <stop offset="100%" stop-color="#0f172a" />
                                    </linearGradient>
                                    <linearGradient id="headerCwGradRight" x1="24" y1="20" x2="42" y2="42"
                                        gradientUnits="userSpaceOnUse">
                                        <stop offset="0%" stop-color="#6366f1" />
                                        <stop offset="100%" stop-color="#1e1b4b" />
                                    </linearGradient>
                                </defs>
                                <path d="M24 6L39 15L24 24L9 15L24 6Z" fill="url(#headerCwGradTop)" />
                                <path d="M9 15L24 24V42L9 33V15Z" fill="url(#headerCwGradLeft)" />
                                <path d="M24 24L39 15V33L24 42V24Z" fill="url(#headerCwGradRight)" />
                                <path d="M24 6L24 24M9 15L24 24M39 15L24 24M24 24V42" stroke="rgba(255,255,255,0.45)"
                                    stroke-width="1.2" stroke-linejoin="round" />
                                <circle cx="24" cy="24" r="3" fill="#ffffff" />
                                <circle cx="24" cy="6" r="2" fill="#38bdf8" />
                                <circle cx="39" cy="15" r="2" fill="#818cf8" />
                                <circle cx="39" cy="33" r="2" fill="#6366f1" />
                                <circle cx="24" cy="42" r="2" fill="#3b82f6" />
                                <circle cx="9" cy="33" r="2" fill="#2563eb" />
                                <circle cx="9" cy="15" r="2" fill="#38bdf8" />
                            </svg>
                        </div>
                        <div class="min-w-0">
                            <h1
                                class="text-sm sm:text-base lg:text-lg font-bold text-slate-900 dark:text-white tracking-tight truncate">
                                Widget Comparison
                            </h1>
                            <p
                                class="text-[10px] sm:text-[11px] text-slate-500 dark:text-slate-400 hidden sm:block truncate">
                                3-Source verification across QA, Git Repository & Excel master list
                            </p>
                        </div>
                    </div>

                    <!-- Mobile Action Buttons (Right-aligned next to logo on mobile) -->
                    <div class="flex sm:hidden flex-col items-end gap-1 shrink-0">
                        <div class="flex items-center gap-1.5">
                            <button type="button" onclick="toggleThemeQuick()" title="Toggle Dark/Light Mode"
                                class="w-7 h-7 rounded-lg border border-slate-300 dark:border-slate-700/80 bg-slate-100 dark:bg-slate-800/40 text-slate-600 dark:text-slate-300 transition flex items-center justify-center cursor-pointer shadow-sm">
                                <i data-lucide="moon" class="w-3.5 h-3.5"></i>
                            </button>
                            <button onclick="handleLogout()" title="Log out"
                                class="w-7 h-7 rounded-lg border border-slate-300 dark:border-slate-700/80 bg-slate-100 dark:bg-slate-800/40 text-slate-400 hover:text-rose-500 transition flex items-center justify-center cursor-pointer shadow-sm">
                                <i data-lucide="log-out" class="w-3.5 h-3.5"></i>
                            </button>
                            <button onclick="exportCSV()" title="Export Excel / CSV"
                                class="p-1 px-2 rounded-lg border border-slate-300 dark:border-slate-700/80 bg-slate-100 dark:bg-slate-800/40 text-[11px] font-medium text-slate-800 dark:text-slate-200 transition shadow-sm cursor-pointer flex items-center gap-1">
                                <i data-lucide="download" class="w-3 h-3 text-emerald-500"></i>
                                <span>Excel</span>
                            </button>
                        </div>
                        <div class="text-[9px] text-slate-500 dark:text-slate-400 font-mono flex items-center gap-1">
                            <i data-lucide="clock" class="w-2.5 h-2.5 text-slate-400"></i>
                            <span id="mobileLastUpdatedTime">{build_time}</span>
                        </div>
                    </div>
                </div>

                <!-- Desktop Action Buttons: Perfectly aligned in a unified top row with timestamp beneath -->
                <div class="hidden sm:flex flex-col items-end gap-1.5 shrink-0">
                    <div class="flex items-center gap-2">
                        <!-- User Profile Pill (if logged in) -->
                        <div id="userProfilePill"
                            class="app-subtle border rounded-lg px-2.5 h-8 text-xs items-center gap-2 hidden shadow-sm">
                            <div class="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-[9px]"
                                id="userAvatar">A</div>
                            <div class="hidden sm:block text-left leading-tight">
                                <div class="font-semibold text-slate-900 dark:text-white truncate max-w-[120px]"
                                    id="userNameDisplay">User</div>
                                <div class="text-[9px] text-slate-500 uppercase tracking-wider" id="userRoleBadge">Role
                                </div>
                            </div>
                            <button onclick="handleLogout()" title="Log out of your session"
                                class="text-slate-400 hover:text-rose-500 transition p-0.5">
                                <i data-lucide="log-out" class="w-3.5 h-3.5"></i>
                            </button>
                        </div>

                        <!-- Theme Toggle -->
                        <button type="button" onclick="toggleThemeQuick()" id="quickThemeBtn"
                            title="Toggle Dark/Light Mode"
                            class="w-8 h-8 rounded-lg border border-slate-300 dark:border-slate-700/80 bg-slate-100 dark:bg-slate-800/40 hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 transition flex items-center justify-center cursor-pointer shadow-sm">
                            <i data-lucide="moon" id="quickThemeIcon" class="w-4 h-4"></i>
                        </button>

                        <!-- Export Excel Button -->
                        <button id="desktopExportBtn" onclick="exportCSV()" title="Export data to Excel / CSV"
                            class="h-8 px-3.5 rounded-lg border border-slate-300 dark:border-slate-700/80 bg-slate-100 dark:bg-slate-800/40 hover:bg-slate-200 dark:hover:bg-slate-800 text-xs font-medium text-slate-800 dark:text-slate-200 transition shadow-sm cursor-pointer flex items-center gap-1.5">
                            <i data-lucide="download" class="w-3.5 h-3.5 text-emerald-500"></i>
                            <span>Export Excel</span>
                        </button>
                    </div>

                    <!-- Last Updated Date & Time: Aligned right underneath the unified action row -->
                    <div
                        class="flex items-center gap-1.5 text-[10px] text-slate-500 dark:text-slate-400 font-mono tracking-tight pr-1">
                        <i data-lucide="clock" class="w-3 h-3 text-slate-400 shrink-0"></i>
                        <span>Last Updated: <strong id="headerLastUpdatedTime"
                                class="font-semibold text-slate-700 dark:text-slate-300">{build_time}</strong></span>
                    </div>
                </div>
            </div>

            <!-- Navigation Tabs (Thumb-friendly on mobile) -->
            <div class="grid grid-cols-2 sm:flex sm:items-center gap-2 sm:gap-8 -mb-px pt-1 text-xs sm:text-sm">
                <button onclick="switchTab('overview')" id="tab-overview"
                    class="nav-tab text-center pb-2 sm:pb-2.5 font-semibold border-b-2 border-blue-500 text-blue-500 dark:text-blue-400 transition whitespace-nowrap">
                    Overview
                </button>
                <button onclick="drillDown('all')" id="tab-inventory"
                    class="nav-tab text-center pb-2 sm:pb-2.5 font-semibold border-b-2 border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition whitespace-nowrap">
                    All Widgets (<span id="nav-tab-total">{total_count}</span>)
                </button>

                <!-- Admin Tabs -->
                <button onclick="switchTab('users')" id="tab-users"
                    class="nav-tab text-center pb-2 sm:pb-2.5 font-semibold border-b-2 border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition whitespace-nowrap hidden">
                    User Management
                </button>
                <button onclick="switchTab('activity')" id="tab-activity"
                    class="nav-tab text-center pb-2 sm:pb-2.5 font-semibold border-b-2 border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition whitespace-nowrap hidden">
                    Activity History
                </button>
            </div>

        </div>
    </header>

    <!-- Main Container -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">

        <!-- File Protocol Banner -->
        <div id="localFileBanner"
            class="hidden p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-800 dark:text-amber-300 flex items-center justify-between gap-3 shadow-sm">
            <div class="flex items-center gap-2.5 min-w-0">
                <i data-lucide="info" class="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0"></i>
                <span>Browsing via <code>file://</code> protocol. Launching interactive simulations with audio & JSON
                    works best on a local server. Run <strong>run_local_dashboard.bat</strong> for full HTTP server
                    mode.</span>
            </div>
            <button type="button" onclick="document.getElementById('localFileBanner').classList.add('hidden')"
                class="p-1 rounded text-amber-600 dark:text-amber-400 hover:bg-amber-500/20 shrink-0">
                <i data-lucide="x" class="w-4 h-4"></i>
            </button>
        </div>
        <!-- ======================================================== -->
        <!-- SECTION 1: OVERVIEW & COMPARISON ANALYTICS               -->
        <!-- ======================================================== -->
        <div id="view-overview" class="view-content space-y-4 sm:space-y-6">

            <!-- Mobile Executive Summary Bento (Visible on mobile screens < 640px) -->
            <div class="sm:hidden app-card border border-blue-500/20 rounded-2xl p-4 shadow-sm bg-gradient-to-b from-blue-500/[0.04] to-transparent space-y-3.5">
                <!-- Status Row -->
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <div class="w-8 h-8 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-sm">
                            <i data-lucide="layers" class="w-4 h-4"></i>
                        </div>
                        <div>
                            <div class="text-xs font-bold text-slate-900 dark:text-white">Total Ecosystem</div>
                            <div class="text-[10px] text-slate-500">{total_assets_count} Total ({total_count} Scope + {extra_repo_count} Extra)</div>
                        </div>
                    </div>
                    <span onclick="drillDown('matched_all')" class="text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 cursor-pointer active:scale-95 transition">
                        {matched_all_pct} Ready
                    </span>
                </div>

                <!-- Overall Progress Bar Card -->
                <div class="p-3 rounded-xl bg-white/80 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800 space-y-1.5">
                    <div class="flex items-center justify-between text-xs font-semibold">
                        <span class="text-slate-700 dark:text-slate-300">Overall Production Ready</span>
                        <span class="text-emerald-600 dark:text-emerald-400 font-mono font-bold cursor-pointer hover:underline" onclick="drillDown('matched_all')">{matched_all_count} / {total_count}</span>
                    </div>
                    <div class="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
                        <div class="bg-gradient-to-r from-teal-500 to-emerald-500 h-2.5 rounded-full" style="width: {qa_coverage_pct}"></div>
                    </div>
                </div>

                <!-- 2x2 High-Impact Metric Tiles -->
                <div class="grid grid-cols-2 gap-2 text-xs">
                    <div onclick="drillDown('all')" class="p-3 rounded-xl border border-blue-500/25 bg-blue-500/[0.06] hover:bg-blue-500/15 dark:hover:bg-blue-500/25 transition cursor-pointer active:scale-95">
                        <div class="text-[10px] font-semibold text-blue-700 dark:text-blue-400 uppercase tracking-wider">Curriculum Scope</div>
                        <div class="text-lg font-bold text-blue-600 dark:text-blue-400 mt-0.5">{total_count} <span class="text-[10px] font-normal text-slate-400">(100%)</span></div>
                        <div class="text-[10px] text-slate-500">Official syllabus</div>
                    </div>
                    <div onclick="drillDown('matched_all')" class="p-3 rounded-xl border border-emerald-500/25 bg-emerald-500/[0.06] hover:bg-emerald-500/15 dark:hover:bg-emerald-500/25 transition cursor-pointer active:scale-95">
                        <div class="text-[10px] font-semibold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">Matched &amp; Ready</div>
                        <div class="text-lg font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">{matched_all_count} <span class="text-[10px] font-normal text-slate-400">({qa_coverage_pct})</span></div>
                        <div class="text-[10px] text-slate-500">Verified everywhere</div>
                    </div>
                    <div onclick="drillDown('needs_attention')" class="p-3 rounded-xl border border-rose-500/25 bg-rose-500/[0.06] hover:bg-rose-500/15 dark:hover:bg-rose-500/25 transition cursor-pointer active:scale-95">
                        <div class="text-[10px] font-semibold text-rose-700 dark:text-rose-400 uppercase tracking-wider">Need Attention</div>
                        <div class="text-lg font-bold text-rose-600 dark:text-rose-400 mt-0.5">{need_attention_count} <span class="text-[10px] font-normal text-slate-400">({need_attention_pct})</span></div>
                        <div class="text-[10px] text-slate-500">15 QA + 21 Git gaps</div>
                    </div>
                    <div onclick="drillDown('extra_repo')" class="p-3 rounded-xl border border-purple-500/25 bg-purple-500/[0.06] hover:bg-purple-500/15 dark:hover:bg-purple-500/25 transition cursor-pointer active:scale-95">
                        <div class="text-[10px] font-semibold text-purple-700 dark:text-purple-400 uppercase tracking-wider">Extra in Repo</div>
                        <div class="text-lg font-bold text-purple-600 dark:text-purple-400 mt-0.5">+{extra_repo_count}</div>
                        <div class="text-[10px] text-slate-500">Standalone tools</div>
                    </div>
                </div>

                <!-- Horizontal Quick Filters Rail -->
                <div class="flex items-center gap-1.5 overflow-x-auto pb-1 custom-scroll text-[11px] whitespace-nowrap">
                    <span onclick="drillDown('extra_repo')" class="px-2.5 py-1 rounded-lg border border-purple-500/25 bg-purple-500/10 text-purple-600 dark:text-purple-400 font-medium cursor-pointer active:scale-95 transition">
                        +{extra_repo_count} Extra in Repo
                    </span>
                    <span onclick="drillDown('whiteboard')" class="px-2.5 py-1 rounded-lg border border-indigo-500/25 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-medium cursor-pointer active:scale-95 transition">
                        {whiteboard_count} Canvas Tools
                    </span>
                    <span onclick="drillDown('naming_issues')" class="px-2.5 py-1 rounded-lg border border-sky-500/25 bg-sky-500/10 text-sky-600 dark:text-sky-400 font-medium cursor-pointer active:scale-95 transition">
                        {naming_issue_count} Name Diffs
                    </span>
                    <span onclick="drillDown('investigation')" class="px-2.5 py-1 rounded-lg border border-rose-500/25 bg-rose-500/10 text-rose-600 dark:text-rose-400 font-medium cursor-pointer active:scale-95 transition">
                        {investigation_count} Review Items
                    </span>
                </div>
            </div>

            <!-- Desktop & Tablet Metrics Container (Hidden on small mobile phones < 640px) -->
            <div class="hidden sm:block space-y-6 sm:space-y-7 relative z-40">

                <!-- ======================================================== -->
                <!-- EXECUTIVE SUMMARY BANNER & PRESENTATION METRICS           -->
                <!-- ======================================================== -->
                <div class="app-card border rounded-2xl p-4 sm:p-5 shadow-sm space-y-4 bg-gradient-to-b from-blue-500/[0.03] to-transparent relative z-40">
                    <!-- Presentation Header -->
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200/80 dark:border-slate-800 pb-3">
                        <div>
                            <div class="flex items-center gap-2">
                                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 uppercase tracking-wider">Executive Presentation</span>
                                <span class="text-xs text-slate-400 dark:text-slate-500">· CEO &amp; Management Briefing</span>
                            </div>
                            <h2 class="text-base sm:text-xl font-extrabold text-slate-900 dark:text-white mt-1">Executive Summary</h2>
                            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                                Core widget inventory, repository availability, and production readiness across Excel Master, Code Repository, and QA Catalog.
                            </p>
                        </div>
                        <!-- Simple Calculation Equation Bar -->
                        <div class="flex flex-wrap items-center gap-1.5 sm:gap-2 bg-slate-100 dark:bg-slate-800/80 p-2 sm:p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-mono shrink-0">
                            <span class="text-slate-500 dark:text-slate-400 font-sans text-[11px] font-semibold">Core Equation:</span>
                            <span class="text-emerald-600 dark:text-emerald-400 font-bold" title="Matched in All 3">258 Ready</span>
                            <span class="text-slate-400">+</span>
                            <span class="text-rose-600 dark:text-rose-400 font-bold" title="Attention Gaps">36 Gaps</span>
                            <span class="text-slate-400">=</span>
                            <span class="text-indigo-600 dark:text-indigo-400 font-bold" title="Curriculum Scope">294 Scope</span>
                            <span class="text-slate-400">+</span>
                            <span class="text-purple-600 dark:text-purple-400 font-bold" title="Extra Tools">+46 Extra</span>
                            <span class="text-slate-400">=</span>
                            <span class="text-blue-600 dark:text-blue-400 font-bold" title="Total Ecosystem">340 Total</span>
                        </div>
                    </div>

                    <!-- 6 Executive KPI Metric Cards (Grid cols 2 / 3 / 6) -->
                    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 sm:gap-3 relative z-30">

                        <!-- Card 1: Total Widgets Identified (340) -->
                        <div id="card-kpi-total" onclick="drillDown('total_assets')" tabindex="0"
                            class="kpi-card app-card border border-t-[3px] border-t-blue-500 rounded-xl p-3 sm:p-3.5 cursor-pointer transition hover:border-blue-500 group shadow-xs hover:shadow-md hover:-translate-y-0.5 duration-200 relative z-20 hover:z-50 focus-within:z-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            title="Click to view all {total_assets_count} tracked assets">
                            <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                                <span class="font-bold text-[10.5px] uppercase tracking-wider text-slate-700 dark:text-slate-300 group-hover:text-blue-600 dark:group-hover:text-blue-400 truncate">Total Identified</span>
                                <i data-lucide="layers" class="w-3.5 h-3.5 text-blue-500 shrink-0"></i>
                            </div>
                            <div class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white flex items-baseline gap-1">
                                <span>{total_assets_count}</span>
                            </div>
                            <div class="text-[10.5px] text-slate-500 dark:text-slate-400 mt-1 truncate">
                                <span>294 scope + 46 extra</span>
                            </div>
                            <!-- Calculation Transparency Popover with Table -->
                            <div class="kpi-popover pointer-events-none absolute top-full left-0 mt-2 w-full min-w-[245px] sm:w-[252px] p-3 bg-slate-900 dark:bg-[#0c1220] text-white text-xs rounded-xl shadow-2xl opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-all duration-150 z-50 border border-slate-700/80 ring-1 ring-black/20">
                                <div class="flex items-center justify-between pb-1.5 border-b border-slate-800 text-[11px]">
                                    <span class="font-bold text-slate-200 flex items-center gap-1.5">
                                        <i data-lucide="table" class="w-3.5 h-3.5 text-blue-400"></i>
                                        <span>Total Identified</span>
                                    </span>
                                    <span class="font-mono font-bold text-blue-400 text-xs">340 Total</span>
                                </div>
                                
                                <table class="w-full text-[10.5px] font-mono mt-1.5 border-collapse">
                                    <tbody>
                                        <tr class="text-slate-300 border-b border-slate-800/60">
                                            <td class="py-0.5 text-emerald-300 flex items-center gap-1">
                                                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0"></span>
                                                <span>Matched in All 3</span>
                                            </td>
                                            <td class="py-0.5 text-right font-bold text-emerald-400">{matched_all_count}</td>
                                        </tr>
                                        <tr class="text-slate-300 border-b border-slate-800/60">
                                            <td class="py-0.5 text-amber-300 flex items-center gap-1">
                                                <span class="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0"></span>
                                                <span>Missing in QA</span>
                                            </td>
                                            <td class="py-0.5 text-right font-bold text-amber-400">+{missing_qa_count}</td>
                                        </tr>
                                        <tr class="text-slate-300 border-b border-slate-800/60">
                                            <td class="py-0.5 text-rose-300 flex items-center gap-1">
                                                <span class="w-1.5 h-1.5 rounded-full bg-rose-400 shrink-0"></span>
                                                <span>Missing in Git</span>
                                            </td>
                                            <td class="py-0.5 text-right font-bold text-rose-400">+21</td>
                                        </tr>
                                        <tr class="bg-indigo-500/10 text-indigo-300 font-bold border-b border-indigo-500/20">
                                            <td class="py-0.5 px-0.5">Curriculum Scope</td>
                                            <td class="py-0.5 px-0.5 text-right font-mono text-indigo-300">{total_count}</td>
                                        </tr>
                                        <tr class="text-purple-300 border-b border-purple-500/20">
                                            <td class="py-0.5 flex items-center gap-1">
                                                <span class="w-1.5 h-1.5 rounded-full bg-purple-400 shrink-0"></span>
                                                <span>Extra in Repo</span>
                                            </td>
                                            <td class="py-0.5 text-right font-bold text-purple-400">+{extra_repo_count}</td>
                                        </tr>
                                    </tbody>
                                    <tfoot>
                                        <tr class="bg-blue-500/15 text-blue-300 font-extrabold text-xs">
                                            <td class="py-1 px-0.5">= Total Identified</td>
                                            <td class="py-1 px-0.5 text-right font-mono text-emerald-400">{total_assets_count}</td>
                                        </tr>
                                    </tfoot>
                                </table>
                                <div class="text-[9px] text-slate-400 text-center mt-1.5 pt-1 border-t border-slate-800 font-sans">
                                    294 Scope + 46 Extra = 340 Total
                                </div>
                            </div>
                        </div>

                        <!-- Card 2: Curriculum Scope (294) -->
                        <div id="card-kpi-xl" onclick="drillDown('all')" tabindex="0"
                            class="kpi-card app-card border border-t-[3px] border-t-indigo-500 rounded-xl p-3 sm:p-3.5 cursor-pointer transition hover:border-indigo-500 group shadow-xs hover:shadow-md hover:-translate-y-0.5 duration-200 relative z-20 hover:z-50 focus-within:z-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            title="Click to view all {total_count} curriculum widgets">
                            <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                                <span class="font-bold text-[10.5px] uppercase tracking-wider text-indigo-700 dark:text-indigo-400 group-hover:text-indigo-500 truncate">Curriculum Scope</span>
                                <i data-lucide="file-spreadsheet" class="w-3.5 h-3.5 text-indigo-500 shrink-0"></i>
                            </div>
                            <div class="text-2xl sm:text-3xl font-extrabold text-indigo-600 dark:text-indigo-400 flex items-baseline gap-1">
                                <span>{total_count}</span>
                            </div>
                            <div class="text-[10.5px] text-slate-500 dark:text-slate-400 mt-1 truncate">
                                <span>official scope · 100%</span>
                            </div>
                            <!-- Calculation Transparency Popover -->
                            <div class="kpi-popover pointer-events-none absolute top-full left-0 mt-2 w-full min-w-[245px] sm:w-[252px] p-3 bg-slate-900 dark:bg-[#0c1220] text-white text-xs rounded-xl shadow-2xl opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-all duration-150 z-50 border border-slate-700/80 ring-1 ring-black/20">
                                <div class="flex items-center justify-between pb-1.5 border-b border-slate-800 text-[11px]">
                                    <span class="font-bold text-indigo-300 flex items-center gap-1.5">
                                        <i data-lucide="calculator" class="w-3.5 h-3.5 text-indigo-400"></i>
                                        <span>Curriculum Scope</span>
                                    </span>
                                    <span class="font-mono font-bold text-indigo-400 text-xs">294 Scope</span>
                                </div>
                                <div class="space-y-1.5 mt-2 text-[10.5px]">
                                    <div>
                                        <span class="text-slate-400 font-semibold">1. Meaning:</span>
                                        <p class="text-slate-200 leading-tight">Master syllabus requirement agreed for CE Platinum &amp; Crystal curriculum.</p>
                                    </div>
                                    <div>
                                        <span class="text-slate-400 font-semibold">2. Source:</span>
                                        <p class="text-slate-200 leading-tight">Widgets in CE Platinum cum Crystal.xlsx master sheet.</p>
                                    </div>
                                    <div class="p-1.5 rounded bg-indigo-500/10 border border-indigo-500/20 font-mono text-[10px]">
                                        <span class="text-indigo-300 font-bold">Calculation:</span>
                                        <div class="text-white font-bold">258 Ready + 15 QA Gap + 21 Git Gap = 294</div>
                                    </div>
                                    <div class="text-[10px] text-slate-400 space-y-0.5">
                                        <div><strong class="text-slate-300">Included:</strong> All 294 official syllabus entries.</div>
                                        <div><strong class="text-slate-300">Excluded:</strong> Standalone tools built outside scope.</div>
                                    </div>
                                </div>
                                <div class="text-[9.5px] text-indigo-400 text-center mt-2 pt-1 border-t border-slate-800 font-sans">
                                    Click to view all 294 scope widgets
                                </div>
                            </div>
                        </div>

                        <!-- Card 3: Available in Repository (273 / 319) -->
                        <div id="card-kpi-repo" onclick="drillDown('developed')" tabindex="0"
                            class="kpi-card app-card border border-t-[3px] border-t-teal-500 rounded-xl p-3 sm:p-3.5 cursor-pointer transition hover:border-teal-500 group shadow-xs hover:shadow-md hover:-translate-y-0.5 duration-200 relative z-20 hover:z-50 focus-within:z-50 focus:outline-none focus:ring-2 focus:ring-teal-500"
                            title="Click to view {present_both_count} developed widgets in scope">
                            <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                                <span class="font-bold text-[10.5px] uppercase tracking-wider text-teal-700 dark:text-teal-400 group-hover:text-teal-500 truncate">In Repository</span>
                                <i data-lucide="git-branch" class="w-3.5 h-3.5 text-teal-500 shrink-0"></i>
                            </div>
                            <div class="text-2xl sm:text-3xl font-extrabold text-teal-600 dark:text-teal-400 flex items-baseline gap-1">
                                <span>{present_both_count}</span>
                            </div>
                            <div class="text-[10.5px] text-slate-500 dark:text-slate-400 mt-1 truncate">
                                <span>{dev_coverage_pct} scope · {total_git_assets} codebase</span>
                            </div>
                            <!-- Calculation Transparency Popover -->
                            <div class="kpi-popover pointer-events-none absolute top-full left-0 mt-2 w-full min-w-[245px] sm:w-[252px] p-3 bg-slate-900 dark:bg-[#0c1220] text-white text-xs rounded-xl shadow-2xl opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-all duration-150 z-50 border border-slate-700/80 ring-1 ring-black/20">
                                <div class="flex items-center justify-between pb-1.5 border-b border-slate-800 text-[11px]">
                                    <span class="font-bold text-teal-300 flex items-center gap-1.5">
                                        <i data-lucide="git-branch" class="w-3.5 h-3.5 text-teal-400"></i>
                                        <span>Available in Repo</span>
                                    </span>
                                    <span class="font-mono font-bold text-teal-400 text-xs">{present_both_count} Scope</span>
                                </div>
                                <div class="space-y-1.5 mt-2 text-[10.5px]">
                                    <div>
                                        <span class="text-slate-400 font-semibold">1. Meaning:</span>
                                        <p class="text-slate-200 leading-tight">Curriculum widgets with verified runnable simulation code on disk.</p>
                                    </div>
                                    <div>
                                        <span class="text-slate-400 font-semibold">2. Source:</span>
                                        <p class="text-slate-200 leading-tight">Git filesystem scan (widgets-b1/b2/b3, src/app).</p>
                                    </div>
                                    <div class="p-1.5 rounded bg-teal-500/10 border border-teal-500/20 font-mono text-[10px]">
                                        <span class="text-teal-300 font-bold">Calculation:</span>
                                        <div class="text-white font-bold">258 Ready + 15 Missing QA = 273 in Git</div>
                                    </div>
                                    <div class="text-[10px] text-slate-400 space-y-0.5">
                                        <div><strong class="text-slate-300">Included:</strong> 273 verified scope code files.</div>
                                        <div><strong class="text-slate-300">Excluded:</strong> 21 syllabus items without code.</div>
                                    </div>
                                </div>
                                <div class="text-[9.5px] text-teal-400 text-center mt-2 pt-1 border-t border-slate-800 font-sans">
                                    Click to view 273 developed widgets
                                </div>
                            </div>
                        </div>

                        <!-- Card 4: Production Ready (258 · 87.8%) -->
                        <div id="card-kpi-qa" onclick="drillDown('matched_all')" tabindex="0"
                            class="kpi-card app-card border border-t-[3px] border-t-emerald-500 rounded-xl p-3 sm:p-3.5 cursor-pointer transition hover:border-emerald-500 group shadow-xs hover:shadow-md hover:-translate-y-0.5 duration-200 relative z-20 hover:z-50 focus-within:z-50 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                            title="Click to view {matched_all_count} verified production ready widgets">
                            <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                                <span class="font-bold text-[10.5px] uppercase tracking-wider text-emerald-700 dark:text-emerald-400 group-hover:text-emerald-500 truncate">Production Ready</span>
                                <i data-lucide="check-check" class="w-3.5 h-3.5 text-emerald-500 shrink-0"></i>
                            </div>
                            <div class="text-2xl sm:text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 flex items-baseline gap-1">
                                <span>{matched_all_count}</span>
                            </div>
                            <div class="text-[10.5px] text-slate-500 dark:text-slate-400 mt-1 truncate">
                                <span>{qa_coverage_pct} verified in all 3</span>
                            </div>
                            <!-- Calculation Transparency Popover -->
                            <div class="kpi-popover pointer-events-none absolute top-full right-0 mt-2 w-full min-w-[245px] sm:w-[252px] p-3 bg-slate-900 dark:bg-[#0c1220] text-white text-xs rounded-xl shadow-2xl opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-all duration-150 z-50 border border-slate-700/80 ring-1 ring-black/20">
                                <div class="flex items-center justify-between pb-1.5 border-b border-slate-800 text-[11px]">
                                    <span class="font-bold text-emerald-300 flex items-center gap-1.5">
                                        <i data-lucide="check-check" class="w-3.5 h-3.5 text-emerald-400"></i>
                                        <span>Production Ready</span>
                                    </span>
                                    <span class="font-mono font-bold text-emerald-400 text-xs">258 Ready</span>
                                </div>
                                <div class="space-y-1.5 mt-2 text-[10.5px]">
                                    <div>
                                        <span class="text-slate-400 font-semibold">1. Meaning:</span>
                                        <p class="text-slate-200 leading-tight">Widgets affirmative and verified across Excel Master, Git, and QA Catalog.</p>
                                    </div>
                                    <div>
                                        <span class="text-slate-400 font-semibold">2. Source:</span>
                                        <p class="text-slate-200 leading-tight">3-Source Cross-Reconciliation.</p>
                                    </div>
                                    <div class="p-1.5 rounded bg-emerald-500/10 border border-emerald-500/20 font-mono text-[10px]">
                                        <span class="text-emerald-300 font-bold">Calculation:</span>
                                        <div class="text-white font-bold">258 Ready ÷ 294 Scope = 87.8% Ready</div>
                                    </div>
                                    <div class="text-[10px] text-slate-400 space-y-0.5">
                                        <div><strong class="text-slate-300">Included:</strong> All 258 fully matched widgets.</div>
                                        <div><strong class="text-slate-300">Excluded:</strong> 36 gaps (15 QA + 21 Git gaps).</div>
                                    </div>
                                </div>
                                <div class="text-[9.5px] text-emerald-400 text-center mt-2 pt-1 border-t border-slate-800 font-sans">
                                    Click to view 258 ready widgets
                                </div>
                            </div>
                        </div>

                        <!-- Card 5: Need Attention (36) -->
                        <div id="card-kpi-attention" onclick="drillDown('needs_attention')" tabindex="0"
                            class="kpi-card app-card border border-t-[3px] border-t-rose-600 rounded-xl p-3 sm:p-3.5 cursor-pointer transition hover:border-rose-600 group shadow-xs hover:shadow-md hover:-translate-y-0.5 duration-200 relative z-20 hover:z-50 focus-within:z-50 focus:outline-none focus:ring-2 focus:ring-rose-500"
                            title="Click to filter {need_attention_count} widgets needing attention">
                            <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                                <span class="font-bold text-[10.5px] uppercase tracking-wider text-rose-700 dark:text-rose-400 group-hover:text-rose-600 truncate">Need Attention</span>
                                <i data-lucide="alert-triangle" class="w-3.5 h-3.5 text-rose-600 shrink-0"></i>
                            </div>
                            <div class="text-2xl sm:text-3xl font-extrabold text-rose-600 dark:text-rose-400 flex items-baseline gap-1">
                                <span>{need_attention_count}</span>
                            </div>
                            <div class="text-[10.5px] text-slate-500 dark:text-slate-400 mt-1 truncate">
                                <span>15 QA gap + 21 Git gap</span>
                            </div>
                            <!-- Calculation Transparency Popover -->
                            <div class="kpi-popover pointer-events-none absolute top-full right-0 mt-2 w-full min-w-[245px] sm:w-[252px] p-3 bg-slate-900 dark:bg-[#0c1220] text-white text-xs rounded-xl shadow-2xl opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-all duration-150 z-50 border border-slate-700/80 ring-1 ring-black/20">
                                <div class="flex items-center justify-between pb-1.5 border-b border-slate-800 text-[11px]">
                                    <span class="font-bold text-rose-300 flex items-center gap-1.5">
                                        <i data-lucide="calculator" class="w-3.5 h-3.5 text-rose-400"></i>
                                        <span>Attention Gaps</span>
                                    </span>
                                    <span class="font-mono font-bold text-rose-400 text-xs">36 Gaps</span>
                                </div>
                                <div class="space-y-1.5 mt-2 text-[10.5px]">
                                    <div>
                                        <span class="text-slate-400 font-semibold">1. Meaning:</span>
                                        <p class="text-slate-200 leading-tight">Widgets in official curriculum scope that are missing from either QA or Git repository.</p>
                                    </div>
                                    <div>
                                        <span class="text-slate-400 font-semibold">2. Source:</span>
                                        <p class="text-slate-200 leading-tight">Reconciliation gaps across Git &amp; QA.</p>
                                    </div>
                                    <div class="p-1.5 rounded bg-rose-500/10 border border-rose-500/20 font-mono text-[10px]">
                                        <span class="text-rose-300 font-bold">Calculation:</span>
                                        <div class="text-white font-bold">15 Missing QA + 21 Missing Git = 36 Gaps</div>
                                    </div>
                                    <div class="text-[10px] text-slate-400 space-y-0.5">
                                        <div><strong class="text-slate-300">Included:</strong> 15 QA gaps + 12 dev backlog + 9 canvas tools.</div>
                                        <div><strong class="text-slate-300">Excluded:</strong> Matched in all 3 &amp; Extra tools.</div>
                                    </div>
                                </div>
                                <div class="text-[9.5px] text-rose-400 text-center mt-2 pt-1 border-t border-slate-800 font-sans">
                                    Click to view 36 attention widgets
                                </div>
                            </div>
                        </div>

                        <!-- Card 6: Extra in Repository (+46) -->
                        <div id="card-kpi-git" onclick="drillDown('extra_repo')" tabindex="0"
                            class="kpi-card app-card border border-t-[3px] border-t-purple-500 rounded-xl p-3 sm:p-3.5 cursor-pointer transition hover:border-purple-500 group shadow-xs hover:shadow-md hover:-translate-y-0.5 duration-200 relative z-20 hover:z-50 focus-within:z-50 focus:outline-none focus:ring-2 focus:ring-purple-500"
                            title="Click to view extra repository tools">
                            <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                                <span class="font-bold text-[10.5px] uppercase tracking-wider text-purple-700 dark:text-purple-400 group-hover:text-purple-500 truncate">Extra in Repo</span>
                                <i data-lucide="package-plus" class="w-3.5 h-3.5 text-purple-500 shrink-0"></i>
                            </div>
                            <div class="text-2xl sm:text-3xl font-extrabold text-purple-600 dark:text-purple-400 flex items-baseline gap-1">
                                <span>+{extra_repo_count}</span>
                            </div>
                            <div class="text-[10.5px] text-slate-500 dark:text-slate-400 mt-1 truncate">
                                <span>standalone tools outside Excel</span>
                            </div>
                            <!-- Calculation Transparency Popover -->
                            <div class="kpi-popover pointer-events-none absolute top-full right-0 mt-2 w-full min-w-[245px] sm:w-[252px] p-3 bg-slate-900 dark:bg-[#0c1220] text-white text-xs rounded-xl shadow-2xl opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-all duration-150 z-50 border border-slate-700/80 ring-1 ring-black/20">
                                <div class="flex items-center justify-between pb-1.5 border-b border-slate-800 text-[11px]">
                                    <span class="font-bold text-purple-300 flex items-center gap-1.5">
                                        <i data-lucide="package-plus" class="w-3.5 h-3.5 text-purple-400"></i>
                                        <span>Extra in Repo</span>
                                    </span>
                                    <span class="font-mono font-bold text-purple-400 text-xs">+{extra_repo_count} Extra</span>
                                </div>
                                <div class="space-y-1.5 mt-2 text-[10.5px]">
                                    <div>
                                        <span class="text-slate-400 font-semibold">1. Meaning:</span>
                                        <p class="text-slate-200 leading-tight">Working standalone HTML5 simulations on disk omitted from Excel syllabus.</p>
                                    </div>
                                    <div>
                                        <span class="text-slate-400 font-semibold">2. Source:</span>
                                        <p class="text-slate-200 leading-tight">Directory scan of widgets-b1, widgets-b2, widgets-b3.</p>
                                    </div>
                                    <div class="p-1.5 rounded bg-purple-500/10 border border-purple-500/20 font-mono text-[10px]">
                                        <span class="text-purple-300 font-bold">Calculation:</span>
                                        <div class="text-white font-bold">319 Codebase − 273 Scope = +46 Extra</div>
                                    </div>
                                    <div class="text-[10px] text-slate-400 space-y-0.5">
                                        <div><strong class="text-slate-300">Included:</strong> 13 in QA + 33 Git codebase only.</div>
                                        <div><strong class="text-slate-300">Excluded:</strong> The 294 official syllabus entries.</div>
                                    </div>
                                </div>
                                <div class="text-[9.5px] text-purple-400 text-center mt-2 pt-1 border-t border-slate-800 font-sans">
                                    Click to view +46 extra tools
                                </div>
                            </div>
                        </div>

                    </div>
                </div>
            </div>

            <!-- 2b. Unified 3-Source Reconciliation & Ecosystem Status -->
            <div class="app-card border rounded-2xl p-4 sm:p-6 shadow-sm space-y-5 relative z-10">
                <!-- Header -->
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200/80 dark:border-slate-800 pb-4">
                    <div class="flex items-center gap-3">
                        <div class="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-sm">
                            <i data-lucide="pie-chart" class="w-4 h-4"></i>
                        </div>
                        <div>
                            <h2 class="text-sm sm:text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                <span>3-Source Reconciliation & Status Breakdown</span>
                            </h2>
                            <p class="text-xs text-slate-500 dark:text-slate-400">
                                Exact data reconciliation across Excel Master ({total_count}), Git Codebase ({present_both_count}), and QA Environment ({matched_all_count})
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Main Content: Side-by-Side Donut Visual + Reconciliation Matrix Table -->
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
                    
                    <!-- Left: Donut Chart Visual (5 cols on lg) -->
                    <div class="lg:col-span-5 flex flex-col items-center justify-center p-2">
                        <div class="w-60 h-60 sm:w-64 sm:h-64 relative flex items-center justify-center group/donut cursor-pointer" title="Calculation: 258 Matched in All 3 ÷ 294 Curriculum Scope = 87.8% Production Ready" onclick="drillDown('matched_all')">
                            <canvas id="reconciliationDonutChart"></canvas>
                            <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                                <span class="text-3xl font-extrabold text-slate-900 dark:text-white font-mono" id="donutCenterNumber">258</span>
                                <span class="text-xs font-semibold text-emerald-600 dark:text-emerald-400">Matched &amp; Ready</span>
                                <span class="text-[10px] text-slate-400 font-mono mt-0.5">87.8% of Scope (258 / 294)</span>
                            </div>
                        </div>
                        <div class="flex items-center justify-center gap-3 mt-3 flex-wrap text-[11px] text-slate-500 dark:text-slate-400">
                            <span class="inline-flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-emerald-500"></span>Matched ({matched_all_count})</span>
                            <span class="inline-flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-amber-500"></span>Missing QA ({missing_qa_count})</span>
                            <span class="inline-flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-rose-500"></span>Missing Git (21)</span>
                            <span class="inline-flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-purple-500"></span>Extra (+{extra_repo_count})</span>
                        </div>
                    </div>

                    <!-- Right: Structured Reconciliation Table (7 cols on lg) -->
                    <div class="lg:col-span-7 space-y-3">
                        <!-- Desktop / Tablet Table -->
                        <div class="hidden sm:block overflow-x-auto custom-scroll border border-slate-200/80 dark:border-slate-800 rounded-xl">
                            <table class="w-full text-left text-xs">
                                <thead>
                                    <tr class="app-subtle border-b text-slate-700 dark:text-slate-300 font-semibold uppercase tracking-wider text-[11px]">
                                        <th class="py-2.5 px-3">Classification</th>
                                        <th class="py-2.5 px-2 text-center" title="Widgets in official Excel syllabus">Excel</th>
                                        <th class="py-2.5 px-2 text-center" title="Widgets committed in Git repository">Git</th>
                                        <th class="py-2.5 px-2 text-center" title="Widgets verified in QA environment">QA</th>
                                        <th class="py-2.5 px-2 text-center" title="Total widget count for this classification">Count</th>
                                        <th class="py-2.5 px-2 text-center" title="Percentage of the 294 Curriculum Scope baseline">% Scope</th>
                                        <th class="py-2.5 px-3 text-right">Action</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-slate-200 dark:divide-slate-800">
                                    <!-- Row 1: Matched in All 3 (258) -->
                                    <tr class="hover:bg-emerald-500/[0.06] dark:hover:bg-emerald-500/[0.18] transition group">
                                        <td class="py-2.5 px-3 cursor-pointer" onclick="drillDown('matched_all')" title="Click to view 258 Matched widgets">
                                            <div class="flex items-center gap-2">
                                                <span class="w-2 h-2 rounded-full bg-emerald-500 shrink-0"></span>
                                                <div>
                                                    <div class="font-bold text-slate-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition">Matched in All 3</div>
                                                    <div class="text-[10px] text-slate-500">In Excel, Git, and QA</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-emerald-600 dark:text-emerald-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('matched_all')" title="Click to view 258 widgets in Excel">✓ 258</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-emerald-600 dark:text-emerald-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('matched_all')" title="Click to view 258 widgets in Git">✓ 258</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-emerald-600 dark:text-emerald-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('matched_all')" title="Click to view 258 widgets in QA">✓ 258</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-extrabold text-sm text-emerald-600 dark:text-emerald-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('matched_all')" title="Click to view 258 Matched widgets">{matched_all_count}</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-semibold text-slate-700 dark:text-slate-300" title="Calculation: 258 ÷ 294 = 87.8%">{qa_coverage_pct}</td>
                                        <td class="py-2.5 px-3 text-right">
                                            <button onclick="drillDown('matched_all')" type="button" class="px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 transition cursor-pointer active:scale-95" title="View 258 matched widgets">
                                                View {matched_all_count}
                                            </button>
                                        </td>
                                    </tr>

                                    <!-- Row 2: Missing in QA (15) -->
                                    <tr class="hover:bg-amber-500/[0.06] dark:hover:bg-amber-500/[0.18] transition group">
                                        <td class="py-2.5 px-3 cursor-pointer" onclick="drillDown('missing_qa')" title="Click to view 15 widgets missing in QA">
                                            <div class="flex items-center gap-2">
                                                <span class="w-2 h-2 rounded-full bg-amber-500 shrink-0"></span>
                                                <div>
                                                    <div class="font-bold text-slate-900 dark:text-white group-hover:text-amber-600 dark:group-hover:text-amber-400 transition">Missing in QA</div>
                                                    <div class="text-[10px] text-slate-500">Code in Git, uncataloged in QA</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-amber-600 dark:text-amber-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('missing_qa')" title="Click to view 15 widgets missing in QA">✓ 15</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-amber-600 dark:text-amber-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('missing_qa')" title="Click to view 15 widgets missing in QA">✓ 15</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-rose-500" title="Not present in QA">✗ 0</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-extrabold text-sm text-amber-600 dark:text-amber-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('missing_qa')" title="Click to view ONLY the 15 widgets missing in QA">{missing_qa_count}</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-semibold text-slate-700 dark:text-slate-300" title="Calculation: 15 ÷ 294 = 5.1%">{missing_qa_pct}</td>
                                        <td class="py-2.5 px-3 text-right">
                                            <button onclick="drillDown('missing_qa')" type="button" class="px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-500/10 hover:bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30 transition cursor-pointer active:scale-95" title="View 15 widgets missing in QA">
                                                View {missing_qa_count}
                                            </button>
                                        </td>
                                    </tr>

                                    <!-- Row 3: Missing in Git (21) -->
                                    <tr class="hover:bg-rose-500/[0.06] dark:hover:bg-rose-500/[0.18] transition group">
                                        <td class="py-2.5 px-3 cursor-pointer" onclick="drillDown('requires_dev')" title="Click to view ONLY the 21 widgets missing in Git">
                                            <div class="flex items-center gap-2">
                                                <span class="w-2 h-2 rounded-full bg-rose-500 shrink-0"></span>
                                                <div>
                                                    <div class="font-bold text-slate-900 dark:text-white group-hover:text-rose-600 dark:group-hover:text-rose-400 transition">Missing in Git</div>
                                                    <div class="text-[10px] text-slate-500">12 Dev Backlog + 9 Whiteboard</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-rose-600 dark:text-rose-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('requires_dev')" title="Click to view ONLY the 21 widgets missing in Git">✓ 21</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-rose-500" title="Missing in Git codebase">✗ 0</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-rose-500" title="Missing in QA">✗ 0</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-extrabold text-sm text-rose-600 dark:text-rose-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('requires_dev')" title="Click to view ONLY the 21 widgets missing in Git">21</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-semibold text-slate-700 dark:text-slate-300" title="Calculation: 21 ÷ 294 = 7.1%">7.1%</td>
                                        <td class="py-2.5 px-3 text-right">
                                            <button onclick="drillDown('requires_dev')" type="button" class="px-2.5 py-1 rounded-lg text-xs font-semibold bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-400 border border-rose-500/30 transition cursor-pointer active:scale-95" title="View ONLY the 21 widgets missing in Git">
                                                View 21
                                            </button>
                                        </td>
                                    </tr>

                                    <!-- Summary Subtotal Row: Total Curriculum Scope (294) -->
                                    <tr class="bg-slate-100/90 dark:bg-slate-800/90 font-bold border-t-2 border-slate-300 dark:border-slate-700">
                                        <td class="py-2.5 px-3 text-slate-900 dark:text-white cursor-pointer" onclick="drillDown('all')" title="Click to view all 294 Curriculum Scope widgets">
                                            <div class="flex items-center gap-1.5">
                                                <i data-lucide="calculator" class="w-3.5 h-3.5 text-blue-500"></i>
                                                <span>Total Scope (Baseline)</span>
                                            </div>
                                            <div class="text-[10px] font-normal text-slate-500 font-mono">258 + 15 + 21 = 294 (100%)</div>
                                        </td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-blue-600 dark:text-blue-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('all')" title="Excel Total: 258 + 15 + 21 = 294">{total_count}</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-teal-600 dark:text-teal-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('present_in_git')" title="Git Total: 258 + 15 = 273 (Click to view 273 in Git)">{present_both_count}</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-emerald-600 dark:text-emerald-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('matched_all')" title="QA Total: 258 (Click to view 258 in QA)">{matched_all_count}</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-extrabold text-sm text-slate-900 dark:text-white cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('all')" title="Click to view all 294 Curriculum Scope widgets">{total_count}</td>
                                        <td class="py-2.5 px-2 text-center font-mono text-slate-900 dark:text-white font-bold" title="Calculation: 87.8% + 5.1% + 7.1% = 100%">100%</td>
                                        <td class="py-2.5 px-3 text-right">
                                            <button onclick="drillDown('all')" type="button" class="px-2.5 py-1 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white transition cursor-pointer active:scale-95 shadow-xs" title="View all 294 curriculum widgets">
                                                View All {total_count}
                                            </button>
                                        </td>
                                    </tr>

                                    <!-- Row 5: Extra in Repo (Non-Scope: +46) -->
                                    <tr class="hover:bg-purple-500/[0.06] dark:hover:bg-purple-500/[0.18] transition group bg-purple-500/[0.02]">
                                        <td class="py-2.5 px-3 cursor-pointer" onclick="drillDown('extra_repo')" title="Click to view 46 extra tools in Git">
                                            <div class="flex items-center gap-2">
                                                <span class="w-2 h-2 rounded-full bg-purple-500 shrink-0"></span>
                                                <div>
                                                    <div class="font-bold text-purple-700 dark:text-purple-400 group-hover:text-purple-600 transition">Extra in Repo</div>
                                                    <div class="text-[10px] text-slate-500">{total_git_assets} in Repo − {present_both_count} in Scope = +{extra_repo_count} Extra (13 in QA, 33 Git only)</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-2.5 px-2 text-center font-mono text-slate-400" title="Not in official curriculum scope">—</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-purple-600 dark:text-purple-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('extra_repo')" title="Click to view 46 extra tools in Git">✓ 46</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-purple-600 dark:text-purple-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('extra_qa')" title="Click to view 13 extra tools cataloged in QA">✓ 13</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-extrabold text-sm text-purple-600 dark:text-purple-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('extra_repo')" title="Click to view 46 extra tools">+{extra_repo_count}</td>
                                        <td class="py-2.5 px-2 text-center font-mono text-slate-400" title="Outside curriculum scope baseline">—</td>
                                        <td class="py-2.5 px-3 text-right">
                                            <button onclick="drillDown('extra_repo')" type="button" class="px-2.5 py-1 rounded-lg text-xs font-semibold bg-purple-500/10 hover:bg-purple-500/20 text-purple-600 dark:text-purple-400 border border-purple-500/30 transition cursor-pointer active:scale-95" title="View 46 extra repository tools">
                                                View +{extra_repo_count}
                                            </button>
                                        </td>
                                    </tr>

                                    <!-- Row 6: Grand Total All Tracked Assets (340) -->
                                    <tr class="bg-blue-500/[0.06] dark:bg-blue-950/40 font-bold border-t border-blue-500/30">
                                        <td class="py-2.5 px-3 text-blue-700 dark:text-blue-300 cursor-pointer" onclick="drillDown('all_including_extra')" title="Click to view all 340 tracked assets">
                                            <div class="flex items-center gap-1.5">
                                                <i data-lucide="layers" class="w-3.5 h-3.5 text-blue-500"></i>
                                                <span>Total Tracked Assets</span>
                                            </div>
                                            <div class="text-[10px] font-normal text-blue-600/80 dark:text-blue-400/80 font-mono">294 Scope + 46 Extra = 340 Total</div>
                                        </td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-blue-600 dark:text-blue-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('all')" title="Click to view 294 in Excel Scope">294</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-purple-600 dark:text-purple-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('all_codebase')" title="273 Scope + 46 Extra = 319 in Codebase (Click to view)">319</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-bold text-emerald-600 dark:text-emerald-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('qa_verified')" title="258 Scope + 13 Extra = 271 in QA (Click to view)">271</td>
                                        <td class="py-2.5 px-2 text-center font-mono font-extrabold text-sm text-blue-600 dark:text-blue-400 cursor-pointer hover:underline active:scale-95 transition" onclick="drillDown('all_including_extra')" title="Click to view all 340 tracked assets">{total_assets_count}</td>
                                        <td class="py-2.5 px-2 text-center font-mono text-slate-500" title="Calculated: 294 Scope + 46 Extra = 340 Assets">—</td>
                                        <td class="py-2.5 px-3 text-right">
                                            <button onclick="drillDown('all_including_extra')" type="button" class="px-2.5 py-1 rounded-lg text-xs font-semibold bg-blue-600/10 hover:bg-blue-600/20 text-blue-600 dark:text-blue-400 border border-blue-600/30 transition cursor-pointer active:scale-95" title="View all 340 tracked assets">
                                                View All {total_assets_count}
                                            </button>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <!-- Mobile Cards View for Small Screens (< 640px) -->
                        <div class="sm:hidden space-y-2">
                            <!-- Mobile Card 1: Matched in All 3 -->
                            <div onclick="drillDown('matched_all')" class="p-2.5 rounded-xl border border-emerald-500/30 bg-emerald-500/[0.05] flex items-center justify-between cursor-pointer active:scale-98 transition">
                                <div>
                                    <div class="text-xs font-bold text-emerald-800 dark:text-emerald-300">Matched in All 3</div>
                                    <div class="text-[10px] text-slate-500">Excel: ✓ &bull; Git: ✓ &bull; QA: ✓</div>
                                </div>
                                <div class="text-right">
                                    <div class="font-mono font-extrabold text-sm text-emerald-600 dark:text-emerald-400">{matched_all_count}</div>
                                    <div class="text-[10px] text-slate-400">{qa_coverage_pct}</div>
                                </div>
                            </div>

                            <!-- Mobile Card 2: Missing in QA -->
                            <div onclick="drillDown('missing_qa')" class="p-2.5 rounded-xl border border-amber-500/30 bg-amber-500/[0.05] flex items-center justify-between cursor-pointer active:scale-98 transition">
                                <div>
                                    <div class="text-xs font-bold text-amber-800 dark:text-amber-300">Missing in QA</div>
                                    <div class="text-[10px] text-slate-500">Excel: ✓ &bull; Git: ✓ &bull; QA: ✗</div>
                                </div>
                                <div class="text-right">
                                    <div class="font-mono font-extrabold text-sm text-amber-600 dark:text-amber-400">{missing_qa_count}</div>
                                    <div class="text-[10px] text-slate-400">{missing_qa_pct}</div>
                                </div>
                            </div>

                            <!-- Mobile Card 3: Missing in Git -->
                            <div onclick="drillDown('requires_dev')" class="p-2.5 rounded-xl border border-rose-500/30 bg-rose-500/[0.05] flex items-center justify-between cursor-pointer active:scale-98 transition">
                                <div>
                                    <div class="text-xs font-bold text-rose-800 dark:text-rose-300">Missing in Git</div>
                                    <div class="text-[10px] text-slate-500">Excel: ✓ &bull; Git: ✗ &bull; QA: ✗</div>
                                </div>
                                <div class="text-right">
                                    <div class="font-mono font-extrabold text-sm text-rose-600 dark:text-rose-400">21</div>
                                    <div class="text-[10px] text-slate-400">7.1%</div>
                                </div>
                            </div>

                            <!-- Mobile Card 4: Total Scope Baseline -->
                            <div onclick="drillDown('all')" class="p-2.5 rounded-xl border border-blue-500/30 bg-blue-500/[0.05] flex items-center justify-between cursor-pointer active:scale-98 transition">
                                <div>
                                    <div class="text-xs font-bold text-blue-800 dark:text-blue-300">Total Scope (Baseline)</div>
                                    <div class="text-[10px] text-slate-500">258 + 15 + 21 = 294 (100%)</div>
                                </div>
                                <div class="text-right">
                                    <div class="font-mono font-extrabold text-sm text-blue-600 dark:text-blue-400">{total_count}</div>
                                    <div class="text-[10px] text-slate-400">100%</div>
                                </div>
                            </div>

                            <!-- Mobile Card 5: Extra in Repo -->
                            <div onclick="drillDown('extra_repo')" class="p-2.5 rounded-xl border border-purple-500/30 bg-purple-500/[0.05] flex items-center justify-between cursor-pointer active:scale-98 transition">
                                <div>
                                    <div class="text-xs font-bold text-purple-700 dark:text-purple-300">Additional Repo Assets</div>
                                    <div class="text-[10px] text-slate-500">340 Total − 294 Scope = +46</div>
                                </div>
                                <div class="text-right">
                                    <div class="font-mono font-extrabold text-sm text-purple-600 dark:text-purple-400">+{extra_repo_count}</div>
                                    <div class="text-[10px] text-slate-400">Bonus</div>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>
            </div>

            <!-- 5. Subject-Wise Performance -->
            <div class="app-card border rounded-2xl p-4 sm:p-5 shadow-sm space-y-4">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200/80 dark:border-slate-800 pb-3">
                    <div>
                        <h2 class="text-sm sm:text-base font-bold text-slate-900 dark:text-white">
                            Subject-Wise Performance & Availability
                        </h2>
                        <p class="text-xs text-slate-500 dark:text-slate-400">
                            Detailed breakdown across 15 subject strands showing Expected, Developed, QA, and Gaps. Click any number to filter.
                        </p>
                    </div>
                    <div class="flex items-center gap-2 self-start sm:self-auto text-xs">
                        <span class="text-[11px] font-mono px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                            {subject_count} Subject Strands
                        </span>
                    </div>
                </div>

                <!-- Responsive Card View for Mobile Screens -->
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 md:hidden">
                    {subject_cards_html}
                </div>

                <!-- Desktop Table View with Multi-Attribute Clickable Cells -->
                <div class="hidden md:block overflow-x-auto custom-scroll">
                    <table class="w-full text-left text-xs">
                        <thead>
                              <tr class="app-subtle border-b text-slate-600 dark:text-slate-400 font-semibold text-[11px] uppercase tracking-wider">
                                  <th class="py-2.5 px-3">Subject Strand</th>
                                  <th class="py-2.5 px-3 text-center">Total Scope</th>
                                  <th class="py-2.5 px-3 text-center">In Repository</th>
                                  <th class="py-2.5 px-3 text-center">Missing from Repo</th>
                                  <th class="py-2.5 px-3 text-center">In QA Catalog</th>
                                  <th class="py-2.5 px-3 text-center">Needs Dev</th>
                                  <th class="py-2.5 px-3 text-center">Readiness Rate</th>
                                  <th class="py-2.5 px-3 text-center">Management Priority</th>
                                  <th class="py-2.5 px-3 text-right">Action</th>
                              </tr>
                          </thead>
                        <tbody class="divide-y divide-slate-200 dark:divide-slate-800">
                            {subject_performance_table_html}
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

        <!-- ======================================================== -->
        <!-- SECTION 2: ALL WIDGETS INVENTORY & STATUS DETAILS -->
        <!-- ======================================================== -->
        <div id="view-inventory" class="view-content space-y-4 hidden">
            
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h2 class="text-base font-bold text-slate-900 dark:text-white">Widget Comparison (<span id="headerTotalCount">{total_count}</span>)</h2>
                    <p class="text-xs text-slate-500 dark:text-slate-400">Verifying presence across QA environment, Git repository, and Excel master list for each curriculum widget.</p>
                </div>
            </div>

            <!-- Unified Filter & Search Toolbar -->
            <div class="app-card border rounded-2xl p-3 sm:p-4 shadow-sm space-y-3">
                
                <!-- Row 1: Search Input + Subject Select + Reset Button -->
                <div class="flex flex-col sm:flex-row gap-2.5 items-stretch sm:items-center justify-between">
                    <!-- Search Input with Clear Button -->
                    <div class="relative flex-1" onmouseenter="showFilterHelp('search')" onmouseleave="resetFilterHelp()">
                        <i data-lucide="search" class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"></i>
                        <input type="text" id="widgetSearch" oninput="filterWidgets()" placeholder="Search by name, WG code, UID (tool-xxxx), subject, or owner..." class="w-full app-subtle border rounded-xl pl-9 pr-14 py-2 text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition" />
                        <kbd id="searchKbdHint" class="hidden sm:inline-block pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] font-mono text-slate-400 bg-slate-100 dark:bg-slate-800/80 px-1.5 py-0.5 rounded border border-slate-200 dark:border-slate-700">Ctrl K</kbd>
                        <button id="searchClearBtn" type="button" onclick="clearSearchInput()" class="hidden absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer">
                            <i data-lucide="x" class="w-3.5 h-3.5"></i>
                        </button>
                    </div>

                    <div class="flex items-center gap-2 flex-wrap sm:flex-nowrap">
                        <!-- Subject Filter -->
                        <div class="relative min-w-[150px]" onmouseenter="showFilterHelp('subject')" onmouseleave="resetFilterHelp()">
                            <select id="subjectFilter" onchange="filterWidgets()" class="w-full app-subtle border rounded-xl px-3 py-2 text-xs text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 cursor-pointer font-medium">
                                <option value="all">All Subjects (15)</option>
                                __SUBJECT_OPTIONS__
                            </select>
                        </div>

                        <!-- Owner Filter -->
                        <div class="relative min-w-[140px]" onmouseenter="showFilterHelp('owner')" onmouseleave="resetFilterHelp()">
                            <select id="ownerFilter" onchange="filterWidgets()" class="w-full app-subtle border rounded-xl px-3 py-2 text-xs text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 cursor-pointer font-medium">
                                <option value="all">All Owners</option>
                                __OWNER_OPTIONS__
                            </select>
                        </div>

                        <!-- Reset All Filters -->
                        <button type="button" onclick="clearFilter()" onmouseenter="showFilterHelp('reset')" onmouseleave="resetFilterHelp()" class="px-3 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition cursor-pointer flex items-center gap-1.5 shrink-0 active:scale-95">
                            <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i>
                            <span class="hidden sm:inline">Reset</span>
                        </button>
                    </div>
                </div>

                <!-- Row 2: 1-Click Status Filter Pills (Matching Overview Categories Exactly) -->
                <div class="flex items-center gap-1.5 overflow-x-auto pb-1 custom-scroll text-xs whitespace-nowrap pt-2 border-t border-slate-200/60 dark:border-slate-800">
                    <span class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 mr-1 uppercase tracking-wider shrink-0">Status:</span>

                    <!-- Pill 1: All Scope (294) -->
                    <button type="button" onclick="setFilterQuick('all')" onmouseenter="showFilterHelp('all')" onmouseleave="resetFilterHelp()" id="pill-filter-all" class="quick-pill px-3 py-1.5 rounded-lg border font-bold transition cursor-pointer bg-blue-600 text-white border-blue-600 shadow-xs flex items-center gap-1.5 active:scale-95">
                        <i data-lucide="layers" class="w-3.5 h-3.5"></i>
                        <span>All Scope ({total_count})</span>
                    </button>

                    <!-- Pill 2: Needs Attention (36) -->
                    <button type="button" onclick="setFilterQuick('needs_attention')" onmouseenter="showFilterHelp('needs_attention')" onmouseleave="resetFilterHelp()" id="pill-filter-needs_attention" class="quick-pill px-3 py-1.5 rounded-lg border font-semibold transition cursor-pointer text-rose-700 dark:text-rose-400 bg-rose-500/10 hover:bg-rose-500/20 border-rose-500/25 flex items-center gap-1.5 active:scale-95">
                        <i data-lucide="alert-triangle" class="w-3.5 h-3.5 text-rose-500"></i>
                        <span>Needs Attention ({need_attention_count})</span>
                    </button>

                    <!-- Pill 3: Matched in All 3 (258) -->
                    <button type="button" onclick="setFilterQuick('matched_all')" onmouseenter="showFilterHelp('matched_all')" onmouseleave="resetFilterHelp()" id="pill-filter-matched_all" class="quick-pill px-3 py-1.5 rounded-lg border font-semibold transition cursor-pointer text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 border-emerald-500/25 flex items-center gap-1.5 active:scale-95">
                        <i data-lucide="check-check" class="w-3.5 h-3.5 text-emerald-500"></i>
                        <span>Matched in All 3 ({matched_all_count})</span>
                    </button>

                    <!-- Pill 4: Missing in QA (15) -->
                    <button type="button" onclick="setFilterQuick('missing_qa')" onmouseenter="showFilterHelp('missing_qa')" onmouseleave="resetFilterHelp()" id="pill-filter-missing_qa" class="quick-pill px-3 py-1.5 rounded-lg border font-semibold transition cursor-pointer text-amber-700 dark:text-amber-400 bg-amber-500/10 hover:bg-amber-500/20 border-amber-500/25 flex items-center gap-1.5 active:scale-95">
                        <i data-lucide="clock" class="w-3.5 h-3.5 text-amber-500"></i>
                        <span>Missing in QA ({missing_qa_count})</span>
                    </button>

                    <!-- Pill 5: Missing in Git (21) -->
                    <button type="button" onclick="setFilterQuick('requires_dev')" onmouseenter="showFilterHelp('requires_dev')" onmouseleave="resetFilterHelp()" id="pill-filter-requires_dev" class="quick-pill px-3 py-1.5 rounded-lg border font-semibold transition cursor-pointer text-rose-700 dark:text-rose-400 bg-rose-500/10 hover:bg-rose-500/20 border-rose-500/25 flex items-center gap-1.5 active:scale-95">
                        <i data-lucide="code" class="w-3.5 h-3.5 text-rose-500"></i>
                        <span>Missing in Git (21)</span>
                    </button>

                    <!-- Pill 6: Extra in Repo (+46) -->
                    <button type="button" onclick="setFilterQuick('extra_repo')" onmouseenter="showFilterHelp('extra_repo')" onmouseleave="resetFilterHelp()" id="pill-filter-extra_repo" class="quick-pill px-3 py-1.5 rounded-lg border font-semibold transition cursor-pointer text-purple-700 dark:text-purple-400 bg-purple-500/10 hover:bg-purple-500/20 border-purple-500/25 flex items-center gap-1.5 active:scale-95">
                        <i data-lucide="box" class="w-3.5 h-3.5 text-purple-500"></i>
                        <span>Extra in Repo (+{extra_repo_count})</span>
                    </button>
                </div>

                <!-- Row 3: Simple Explanation Line (Dynamically explains hovered or active filter) -->
                <div id="filterHelpLine" class="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 text-xs transition-all duration-150">
                    <i data-lucide="info" id="filterHelpIcon" class="w-3.5 h-3.5 text-blue-500 shrink-0 transition-colors"></i>
                    <span id="filterHelpText" class="text-slate-600 dark:text-slate-300 font-medium leading-relaxed">All Scope (294): Shows all 294 curriculum widgets tracked across QA, Git, and Excel.</span>
                </div>

                <!-- Hidden inputs for programmatic compatibility -->
                <select id="statusFilter" class="hidden">
                    <option value="all">All</option>
                    <option value="needs_attention">Needs Attention</option>
                    <option value="matched_all">Matched in All 3</option>
                    <option value="missing_qa">Missing in QA</option>
                    <option value="requires_dev">Missing in Git</option>
                    <option value="missing_git">Missing in Git</option>
                    <option value="pending_dev">Pending Dev</option>
                    <option value="developed">Developed</option>
                    <option value="source_present">Developed</option>
                    <option value="in_qa">In QA</option>
                    <option value="qa_ready">In QA</option>
                    <option value="whiteboard">Canvas Tools</option>
                    <option value="canvas">Canvas Tools</option>
                    <option value="naming_issues">Naming Issues</option>
                    <option value="name_diff">Naming Issues</option>
                    <option value="present_in_git">Present in Git</option>
                    <option value="extra_qa">Extra in QA</option>
                    <option value="all_including_extra">All 340 Assets</option>
                    <option value="all_codebase">All Codebase</option>
                    <option value="qa_verified">QA Verified</option>
                    <option value="extra_repo">Extra in Repo</option>
                </select>
                <button id="btn-toggle-attention" class="hidden"></button>
                <button id="btn-toggle-all" class="hidden"></button>
            </div>

            <!-- Table & Mobile Card View Container -->
            <div class="app-card border rounded-lg overflow-hidden shadow-sm">
                
                <!-- Mobile Widget Cards List (Visible on phones < 768px) -->
                <div id="widgetMobileCardsList" class="md:hidden divide-y divide-slate-200 dark:divide-slate-800">
                    <!-- Injected dynamically via renderTable() -->
                </div>

                <!-- Desktop Data Table (Visible on md+ screens) -->
                <div class="hidden md:block overflow-x-auto">
                    <table class="w-full text-left text-xs">
                        <thead>
                            <tr class="app-subtle border-b text-slate-600 dark:text-slate-400 font-medium">
                                <th class="py-3 px-3 w-12 text-center cursor-pointer select-none" onclick="sortData('sr')">#</th>
                                <th class="py-3 px-4 cursor-pointer select-none" onclick="sortData('name')">
                                    <div class="font-bold text-xs uppercase tracking-wider text-slate-700 dark:text-slate-200">IWN (Widget Name)</div>
                                    <div class="text-[10px] text-slate-400 font-normal">Widget Name & Details</div>
                                </th>
                                <th class="py-3 px-3 w-32 cursor-pointer select-none" onclick="sortData('owner')">
                                    <div class="font-bold text-xs uppercase tracking-wider text-slate-700 dark:text-slate-200">Owner</div>
                                    <div class="text-[10px] text-slate-400 font-normal">Assigned Dev</div>
                                </th>
                                <th class="py-3 px-3 w-28 text-center cursor-pointer select-none" onclick="sortData('in_qa')">
                                    <div class="font-bold text-xs uppercase tracking-wider text-slate-700 dark:text-slate-200">QA</div>
                                    <div class="text-[10px] text-slate-400 font-normal">In QA</div>
                                </th>
                                <th class="py-3 px-3 w-28 text-center cursor-pointer select-none" onclick="sortData('has_file')">
                                    <div class="font-bold text-xs uppercase tracking-wider text-slate-700 dark:text-slate-200">Git</div>
                                    <div class="text-[10px] text-slate-400 font-normal">In Git</div>
                                </th>
                                <th class="py-3 px-3 w-28 text-center cursor-pointer select-none" onclick="sortData('in_xl')">
                                    <div class="font-bold text-xs uppercase tracking-wider text-slate-700 dark:text-slate-200">XL</div>
                                    <div class="text-[10px] text-slate-400 font-normal">In Excel</div>
                                </th>
                                <th class="py-3 px-3 w-24 text-center select-none">
                                    <div class="font-bold text-xs uppercase tracking-wider text-slate-700 dark:text-slate-200">Rep Folder</div>
                                    <div class="text-[10px] text-slate-400 font-normal">Folder</div>
                                </th>
                                <th class="py-3 px-3 w-24 text-center select-none">
                                    <div class="font-bold text-xs uppercase tracking-wider text-slate-700 dark:text-slate-200">Live</div>
                                    <div class="text-[10px] text-slate-400 font-normal">Launch</div>
                                </th>
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
<!-- SECTION 3: USER MANAGEMENT (Admin Only)                   -->
<!-- ======================================================== -->
<div id="view-users" class="view-content space-y-4 hidden">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
            <h2 class="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <i data-lucide="users" class="w-4 h-4 text-blue-500"></i>
                <span>Team User Management</span>
                <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold border border-emerald-500/20" id="cloudStatusBadge">v2.8 Cloud & Local Sync</span>
            </h2>
            <p class="text-xs text-slate-500 dark:text-slate-400">Manage authorized team members, roles, and dashboard permissions.</p>
        </div>
        <div class="flex items-center gap-2 self-start sm:self-auto">
            <button onclick="openCloudSyncModal()" id="cloudDbBtn"
                title="Configure Supabase PostgreSQL multi-system cloud sync"
                class="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-slate-800/60 hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium text-xs shadow-sm transition flex items-center gap-1.5 cursor-pointer">
                <span class="w-2 h-2 rounded-full bg-slate-400" id="cloudStatusDot"></span>
                <i data-lucide="database" class="w-3.5 h-3.5 text-blue-500"></i>
                <span id="cloudStatusBtnText">Cloud Database</span>
            </button>
            <button onclick="openAddUserModal()"
                class="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-sm transition flex items-center gap-1.5">
                <i data-lucide="user-plus" class="w-3.5 h-3.5"></i>
                <span>Add / Invite User</span>
            </button>
        </div>
    </div>

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

    <div class="app-card border rounded-lg overflow-hidden shadow-sm">
        <div class="overflow-x-auto">
            <table class="w-full text-left text-xs min-w-[700px]">
                <thead>
                    <tr class="app-subtle border-b text-slate-600 dark:text-slate-400 font-medium">
                        <th class="py-2.5 px-4">Name & Email</th>
                        <th class="py-2.5 px-4 w-32">Role</th>
                        <th class="py-2.5 px-4 w-28">Status</th>
                        <th class="py-2.5 px-4 w-36">Last Login</th>
                        <th class="py-2.5 px-4 text-right w-64">Management Actions</th>
                    </tr>
                </thead>
                <tbody id="userTableBody" class="divide-y divide-slate-200 dark:divide-slate-800">
                    <!-- Populated dynamically via renderUsersTable() -->
                </tbody>
            </table>
        </div>
        <!-- Mobile User Cards -->
        <div id="userMobileCardsList" class="md:hidden divide-y divide-slate-200 dark:divide-slate-800 p-3 space-y-3">
            <!-- Populated dynamically on mobile -->
        </div>
    </div>
</div>

<!-- ======================================================== -->
<!-- SECTION 5: ACTIVITY HISTORY (Admin Only)                  -->
<!-- ======================================================== -->
<div id="view-activity" class="view-content space-y-4 hidden">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
            <h2 class="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <i data-lucide="activity" class="w-4 h-4 text-emerald-500"></i>
                <span>Activity & Access Audit History</span>
            </h2>
            <p class="text-xs text-slate-500 dark:text-slate-400">Complete immutable record of team logins, section
                access, widget inspections, and data actions.</p>
        </div>
        <div class="flex items-center gap-2">
            <button onclick="exportActivityCSV()"
                class="app-subtle hover:bg-slate-200 dark:hover:bg-slate-800 border rounded-lg px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 transition flex items-center gap-1.5">
                <i data-lucide="download" class="w-3.5 h-3.5"></i>
                <span>Export Activity CSV</span>
            </button>
        </div>
    </div>

    <div class="app-card border rounded-lg overflow-hidden shadow-sm">
        <div class="overflow-x-auto">
            <table class="w-full text-left text-xs">
                <thead>
                    <tr class="app-subtle border-b text-slate-600 dark:text-slate-400 font-medium">
                        <th class="py-2.5 px-4 w-40">Timestamp</th>
                        <th class="py-2.5 px-4 w-36">User</th>
                        <th class="py-2.5 px-4 w-32">Action Type</th>
                        <th class="py-2.5 px-4 w-32">Target Area</th>
                        <th class="py-2.5 px-4">Details</th>
                    </tr>
                </thead>
                <tbody id="activityTableBody" class="divide-y divide-slate-200 dark:divide-slate-800">
                    <!-- Populated dynamically via renderActivityTable() -->
                </tbody>
            </table>
        </div>
    </div>
</div>

</main>

<!-- ======================================================== -->
<!-- MODAL DIALOGS                                            -->
<!-- ======================================================== -->

<!-- Widget Detail Modal -->
<div id="widgetModal"
    class="fixed inset-0 z-[100] bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 hidden">
    <div
        class="app-card border rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl text-left max-h-[90vh] overflow-y-auto custom-scroll">
        <div class="flex items-center justify-between pb-2 border-b">
            <div class="flex items-center gap-2">
                <span id="modalSr" class="font-mono text-xs font-bold text-slate-400">#0</span>
                <span id="modalSubject"
                    class="text-xs font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">General</span>
            </div>
            <button onclick="closeModal()" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1">
                <i data-lucide="x" class="w-4 h-4"></i>
            </button>
        </div>

        <div>
            <h3 id="modalName" class="text-base font-bold text-slate-900 dark:text-white">Widget Title</h3>
            <div id="modalOwner" class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Owner: Developer</div>
        </div>

        <div>
            <div class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                Widget Status</div>
            <div id="modalBadge"></div>
        </div>

        <!-- Strategic Action Note -->
        <div id="modalActionSection" class="p-3 rounded-lg border bg-blue-500/10 border-blue-500/20 space-y-1 text-xs">
            <div class="flex items-center justify-between font-semibold text-blue-700 dark:text-blue-400">
                <span class="flex items-center gap-1.5"><i data-lucide="compass" class="w-3.5 h-3.5"></i> Management
                    Action Plan</span>
                <span id="modalActionPriority" class="font-mono text-[10px] bg-blue-600/15 px-2 py-0.5 rounded">HIGH
                    PRIORITY</span>
            </div>
            <p id="modalActionJustification" class="text-slate-700 dark:text-slate-300 leading-relaxed"></p>
        </div>

        <!-- QA Information Section -->
        <div id="modalQaSection" class="hidden"></div>

        <div class="space-y-3 text-xs">
            <div class="p-3 rounded-lg app-subtle border space-y-1">
                <div class="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                    <i data-lucide="info" class="w-3.5 h-3.5 text-blue-500"></i>
                    <span>Plain-English Status Summary</span>
                </div>
                <p id="modalExplanation" class="text-slate-600 dark:text-slate-400 leading-relaxed"></p>
            </div>

            <div class="p-3 rounded-lg app-subtle border space-y-1">
                <div class="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                    <i data-lucide="check-circle" class="w-3.5 h-3.5 text-emerald-500"></i>
                    <span>What Was Checked</span>
                </div>
                <p id="modalChecked" class="text-slate-600 dark:text-slate-400 leading-relaxed"></p>
            </div>

            <div class="p-3 rounded-lg app-subtle border space-y-1">
                <div class="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                    <i data-lucide="list-todo" class="w-3.5 h-3.5 text-amber-500"></i>
                    <span>Required Next Steps</span>
                </div>
                <p id="modalAction" class="text-slate-600 dark:text-slate-400 leading-relaxed"></p>
            </div>
        </div>

        <div class="pt-3 border-t flex items-center justify-between text-xs">
            <div id="modalPathContainer" class="truncate max-w-[280px]">
                <span class="text-slate-400">Path: </span>
                <span id="modalPath" class="font-mono text-slate-600 dark:text-slate-300"></span>
            </div>
            <div class="flex items-center gap-2">
                <button type="button" onclick="closeModal()"
                    class="px-3 py-1.5 rounded-lg border app-subtle hover:bg-slate-200 dark:hover:bg-slate-800 font-medium">Close</button>
                <div id="modalRunBtnContainer"></div>
            </div>
        </div>
    </div>
</div>

<!-- Status Briefing Report Modal -->
<div id="statusReportModal"
    class="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 hidden">
    <div
        class="app-card border rounded-2xl max-w-3xl w-full p-6 sm:p-8 space-y-5 shadow-2xl text-left max-h-[90vh] overflow-y-auto custom-scroll">
        <div class="flex items-center justify-between pb-3 border-b">
            <div class="flex items-center gap-2.5">
                <div
                    class="w-8 h-8 rounded-lg bg-blue-500/15 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
                    <i data-lucide="file-text" class="w-4 h-4"></i>
                </div>
                <div>
                    <h3 class="font-bold text-base text-slate-900 dark:text-white">Widget Status Briefing Report</h3>
                    <p class="text-xs text-slate-500 dark:text-slate-400">Printable summary of widget status and
                        production readiness</p>
                </div>
            </div>
            <button onclick="closeStatusReportModal()"
                class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1">
                <i data-lucide="x" class="w-4 h-4"></i>
            </button>
        </div>

        <div id="statusReportTextContent"
            class="space-y-4 text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-sans bg-slate-50 dark:bg-slate-900/60 p-5 rounded-xl border border-slate-200 dark:border-slate-800">
            <!-- Injected dynamically via openStatusReportModal() -->
        </div>

        <div class="pt-3 border-t flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
            <div class="text-[11px] text-slate-500">
                Generated: <span class="font-mono">{build_time}</span> • Source: {excel_filename}
            </div>
            <div class="flex items-center gap-2">
                <button onclick="copyStatusReport()"
                    class="px-3.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 font-medium text-xs transition flex items-center gap-1.5 shadow-sm">
                    <i data-lucide="copy" class="w-3.5 h-3.5"></i>
                    <span>Copy Report</span>
                </button>
                <button onclick="window.print()"
                    class="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition flex items-center gap-1.5 shadow-sm">
                    <i data-lucide="printer" class="w-3.5 h-3.5"></i>
                    <span>Print / Save PDF</span>
                </button>
            </div>
        </div>
    </div>
</div>

<!-- Supabase Cloud Sync Modal -->
<div id="cloudSyncModal" class="fixed inset-0 z-[100] bg-slate-900/60 backdrop-blur-sm hidden flex items-center justify-center p-4">
    <div class="app-card border rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4 bg-white dark:bg-[#111622] border-slate-200 dark:border-slate-800 text-left">
        <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80 pb-3">
            <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
                    <i data-lucide="database" class="w-4 h-4"></i>
                </div>
                <div>
                    <h3 class="text-sm font-bold text-slate-900 dark:text-white">Supabase Cloud Database Sync</h3>
                    <p class="text-[11px] text-slate-500 dark:text-slate-400">Industry-standard PostgreSQL multi-system persistence</p>
                </div>
            </div>
            <button onclick="closeCloudSyncModal()" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1">
                <i data-lucide="x" class="w-4 h-4"></i>
            </button>
        </div>

        <div class="p-3 rounded-xl border text-xs space-y-2 bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800" id="cloudStatusBanner">
            <div class="flex items-center justify-between font-semibold">
                <span class="flex items-center gap-1.5">
                    <span class="w-2.5 h-2.5 rounded-full bg-slate-400" id="cloudModalStatusDot"></span>
                    <span id="cloudModalStatusTitle">Local Offline Mode</span>
                </span>
                <span class="font-mono text-[10px] px-2 py-0.5 rounded-full bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-500/20" id="cloudModeBadge">Browser Storage</span>
            </div>
            <p class="text-[11px] text-slate-600 dark:text-slate-400" id="cloudModalStatusDesc">
                Currently storing accounts locally in your browser. Connect Supabase to sync team accounts across all computers, tablets, and phones in real-time.
            </p>
        </div>

        <div class="space-y-3">
            <div>
                <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Supabase Project URL</label>
                <input type="text" id="supabaseUrlInput" placeholder="https://your-project-id.supabase.co" class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 font-mono">
            </div>

            <div>
                <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Supabase Anon Public API Key</label>
                <input type="password" id="supabaseKeyInput" placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 font-mono">
                <p class="text-[10px] text-slate-400 mt-1">Found in your Supabase Project Settings → API.</p>
            </div>
        </div>

        <div class="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800/80">
            <button onclick="copySupabaseSchema()" type="button" class="text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 font-medium">
                <i data-lucide="copy" class="w-3.5 h-3.5"></i>
                <span>Copy 1-Click SQL Schema</span>
            </button>
            <div class="flex items-center gap-2">
                <button onclick="closeCloudSyncModal()" type="button" class="px-3 py-1.5 text-xs text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition font-medium">
                    Cancel
                </button>
                <button onclick="saveAndConnectSupabase()" type="button" id="saveSupabaseBtn" class="px-4 py-1.5 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition font-semibold flex items-center gap-1.5 shadow-sm">
                    <i data-lucide="plug" class="w-3.5 h-3.5"></i>
                    <span>Connect & Sync</span>
                </button>
            </div>
        </div>
    </div>
</div>

<!-- User Management Modals (Add, Edit, Delete) -->
<div id="addUserModal"
    class="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 hidden">
    <div class="app-card border rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl text-left">
        <div class="flex items-center justify-between pb-2 border-b">
            <div class="flex items-center gap-2">
                <i data-lucide="user-plus" class="w-4 h-4 text-blue-500"></i>
                <h3 class="font-bold text-sm text-slate-900 dark:text-white">Add Team Member</h3>
            </div>
            <button onclick="closeAddUserModal()" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                <i data-lucide="x" class="w-4 h-4"></i>
            </button>
        </div>

        <form onsubmit="handleSaveNewUser(event)" class="space-y-3 text-xs">
            <div>
                <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Full Name</label>
                <input type="text" id="addUserName" required placeholder="e.g. Jane Doe"
                    class="w-full app-subtle border rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-500" />
            </div>
            <div>
                <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Email Address</label>
                <input type="email" id="addUserEmail" required placeholder="jane@company.com"
                    class="w-full app-subtle border rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-500" />
            </div>
            <div>
                <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Role & Permissions</label>
                <select id="addUserRole"
                    class="w-full app-subtle border rounded-lg px-3 py-2 text-xs focus:outline-none cursor-pointer">
                    <option value="developer">Developer (Codebase & Technical views)</option>
                    <option value="content">Content (Curriculum & Inventory)</option>
                    <option value="qa">QA (Verification & Testing)</option>
                    <option value="viewer" selected>Viewer (Read-Only)</option>
                    <option value="admin">Admin (Full Control)</option>
                </select>
            </div>
            <div>
                <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Initial Password</label>
                <input type="text" id="addUserPass" required placeholder="Generate or enter password"
                    value="Widget2026!"
                    class="w-full app-subtle border rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:border-blue-500" />
            </div>
            <div class="pt-3 border-t flex justify-end gap-2">
                <button type="button" onclick="closeAddUserModal()"
                    class="px-3 py-1.5 rounded-lg border app-subtle hover:bg-slate-200 dark:hover:bg-slate-800 font-medium">Cancel</button>
                <button type="submit"
                    class="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium">Create
                    User</button>
            </div>
        </form>
    </div>
</div>

<!-- Edit User Modal -->
<div id="editUserModal"
    class="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 hidden">
    <div class="app-card border rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl text-left">
        <div class="flex items-center justify-between pb-2 border-b">
            <div class="flex items-center gap-2">
                <i data-lucide="user-cog" class="w-4 h-4 text-blue-500"></i>
                <h3 class="font-bold text-sm text-slate-900 dark:text-white">Edit Team Member</h3>
            </div>
            <button onclick="closeEditUserModal()"
                class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                <i data-lucide="x" class="w-4 h-4"></i>
            </button>
        </div>

        <form onsubmit="handleSaveEditUser(event)" class="space-y-3 text-xs">
            <input type="hidden" id="editUserId" />
            <div>
                <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Full Name</label>
                <input type="text" id="editUserName" required
                    class="w-full app-subtle border rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-500" />
            </div>
            <div>
                <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Email Address</label>
                <input type="email" id="editUserEmail" required
                    class="w-full app-subtle border rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-500" />
            </div>
            <div>
                <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Assigned Role</label>
                <select id="editUserRole"
                    class="w-full app-subtle border rounded-lg px-3 py-2 text-xs focus:outline-none cursor-pointer">
                    <option value="developer">Developer (Codebase & Technical views)</option>
                    <option value="content">Content (Curriculum & Inventory)</option>
                    <option value="qa">QA (Verification & Testing)</option>
                    <option value="viewer">Viewer (Read-Only)</option>
                    <option value="admin">Admin (Full Control)</option>
                </select>
            </div>
            <div>
                <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Change Password <span
                        class="text-[10px] text-slate-400 font-normal">(Leave blank to keep unchanged)</span></label>
                <input type="text" id="editUserPass" placeholder="Enter new password or leave blank"
                    class="w-full app-subtle border rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:border-blue-500" />
            </div>
            <div class="pt-3 border-t flex justify-end gap-2">
                <button type="button" onclick="closeEditUserModal()"
                    class="px-3 py-1.5 rounded-lg border app-subtle hover:bg-slate-200 dark:hover:bg-slate-800 font-medium">Cancel</button>
                <button type="submit"
                    class="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium">Save
                    Changes</button>
            </div>
        </form>
    </div>
</div>

<!-- Delete User Modal -->
<div id="deleteUserModal"
    class="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 hidden">
    <div class="app-card border border-rose-500/30 rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl text-left">
        <div class="flex items-center gap-3">
            <div
                class="w-10 h-10 rounded-xl bg-rose-500/15 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0">
                <i data-lucide="alert-triangle" class="w-5 h-5"></i>
            </div>
            <div>
                <h3 class="font-bold text-sm text-slate-900 dark:text-white">Delete Team Member</h3>
                <p class="text-[11px] text-slate-500 dark:text-slate-400">This action is permanent and cannot be undone.
                </p>
            </div>
        </div>

        <div class="p-3 rounded-lg app-subtle border text-xs space-y-1">
            <div class="font-semibold text-slate-900 dark:text-white" id="deleteTargetName">User Name</div>
            <div class="text-[11px] text-slate-500 font-mono" id="deleteTargetEmail">email@company.com</div>
            <div class="text-[10px] text-slate-400 pt-1" id="deleteTargetRole">Role: -</div>
        </div>

        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            Removing this user will permanently revoke their login. All dashboard metrics and user records will update
            immediately.
        </p>

        <div class="pt-2 flex items-center justify-end gap-2">
            <button type="button" onclick="closeDeleteUserModal()"
                class="px-3 py-1.5 rounded-lg border app-subtle hover:bg-slate-200 dark:hover:bg-slate-800 text-xs font-medium">Cancel</button>
            <button type="button" onclick="confirmDeleteUser()" id="confirmDeleteBtn"
                class="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs shadow-sm flex items-center gap-1.5">
                <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                <span>Delete User</span>
            </button>
        </div>
    </div>
</div>

<!-- Drag & Drop Full Window Overlay -->
<div id="dropOverlay"
    class="fixed inset-0 z-[100] bg-slate-950/80 backdrop-blur-md flex flex-col items-center justify-center text-white hidden pointer-events-none transition-all">
    <div
        class="p-8 sm:p-10 rounded-3xl bg-slate-900 border-2 border-dashed border-emerald-500 text-center shadow-2xl space-y-4 pointer-events-auto max-w-lg mx-4">
        <div
            class="w-20 h-20 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto border border-emerald-500/30">
            <i data-lucide="file-spreadsheet" class="w-10 h-10 animate-bounce"></i>
        </div>
        <div class="text-xl font-bold text-white">Release Excel File to Update Dashboard</div>
        <p class="text-xs text-slate-300 leading-relaxed">
            Drop your updated <code>.xlsx</code> spreadsheet here. All 294 widgets, repo status links, and verification
            numbers will recalculate in real time.
        </p>
        <div class="text-[11px] text-emerald-400 font-medium">
            Supports "Widgets in CE Platinum cum Crystal.xlsx" (Widget-RepoList sheet)
        </div>
    </div>
</div>

<!-- Toast Notification -->
<div id="toastNotification"
    class="fixed top-6 left-1/2 -translate-x-1/2 z-[110] max-w-md w-[calc(100%-2rem)] p-3.5 sm:p-4 rounded-2xl shadow-2xl app-card border flex items-center justify-between gap-3 text-xs transition-all duration-300 transform -translate-y-20 opacity-0 pointer-events-none">
    <div class="flex items-center gap-3 min-w-0">
        <div id="toastIcon" class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0"></div>
        <div class="min-w-0">
            <div id="toastTitle" class="font-semibold text-slate-900 dark:text-white"></div>
            <div id="toastMsg" class="text-slate-500 dark:text-slate-400 mt-0.5 truncate"></div>
        </div>
    </div>
    <button type="button" onclick="hideToast()"
        class="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition shrink-0">
        <i data-lucide="x" class="w-4 h-4"></i>
    </button>
</div>
    <!-- Scripts -->
    <script>
        const currentUser = (typeof authManager !== 'undefined') ? authManager.requireAuth() : null;

        let rawData = __DATA_JSON__;
        let rawQaData = __QA_DATA_JSON__;
        let filteredData = [...rawData];
        let currentPage = 1;
        const pageSize = 25;
        let sortCol = 'sr';
        let sortAsc = true;
        let currentModalPath = '';

        function initUserProfile() {
            const pill = document.getElementById('userProfilePill');
        if (!currentUser) {
                if (pill) pill.classList.add('hidden');
        return;
            }
        if (pill) {
            pill.classList.remove('hidden');
        pill.classList.add('flex');
            }
        const nameEl = document.getElementById('userNameDisplay');
        const roleEl = document.getElementById('userRoleBadge');
        const avatarEl = document.getElementById('userAvatar');

        if (nameEl) nameEl.innerText = currentUser.fullName;
        if (roleEl) roleEl.innerText = (currentUser.role || 'viewer').toUpperCase();
        if (avatarEl) avatarEl.innerText = (currentUser.fullName || 'U').charAt(0).toUpperCase();

        // Role-based visibility:
        // Admin sees all hidden components (Docs, Users, Activity, Project Status Overview, Management Insights, Action Plan).
        // All non-admin users (developer, qa, content, viewer) have these hidden.
        const role = (currentUser.role || '').toLowerCase();
        const adminElements = [
        'tab-users',
        'tab-activity',
        'section-project-status-overview',
        'section-management-insights',
        'section-management-action-plan'
        ];

            adminElements.forEach(id => {
                const el = document.getElementById(id);
        if (!el) return;
        if (role === 'admin') {
            el.classList.remove('hidden');
                } else {
            el.classList.add('hidden');
                }
            });
        }

        function handleLogout() {
            authManager.logout();
        }

        function initTheme() {
            const saved = localStorage.getItem('theme-preference') || 'system';
        applyTheme(saved);
        }

        function changeTheme(theme) {
            localStorage.setItem('theme-preference', theme);
        applyTheme(theme);
        }

        function toggleThemeQuick() {
            const isDark = document.documentElement.classList.contains('dark');
        const target = isDark ? 'light' : 'dark';
        changeTheme(target);
        }

        function applyTheme(theme) {
            const root = document.documentElement;
        let isDark = false;
        if (theme === 'dark') {
            root.classList.add('dark');
        isDark = true;
            } else if (theme === 'light') {
            root.classList.remove('dark');
        isDark = false;
            } else {
                if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            root.classList.add('dark');
        isDark = true;
                } else {
            root.classList.remove('dark');
        isDark = false;
                }
            }
        updateQuickThemeIcon(isDark);
        if (typeof updateChartsTheme === 'function') {
            updateChartsTheme();
            }
        }

        function updateQuickThemeIcon(isDark) {
            const btn = document.getElementById('quickThemeBtn');
        if (!btn) return;
        if (isDark) {
            btn.innerHTML = '<i data-lucide="sun" class="w-4 h-4 text-amber-400"></i>';
        btn.title = "Switch to Light Mode";
            } else {
            btn.innerHTML = '<i data-lucide="moon" class="w-4 h-4 text-slate-600"></i>';
        btn.title = "Switch to Dark Mode";
            }
        if (window.lucide) lucide.createIcons();
        }

        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (localStorage.getItem('theme-preference') === 'system' || !localStorage.getItem('theme-preference')) {
            applyTheme('system');
            }
        });

        function switchTab(tabId) {
            if ((tabId === 'users' || tabId === 'activity') && (!currentUser || currentUser.role !== 'admin')) {
            showToast('Administrator privilege required', 'error');
        return;
            }

            document.querySelectorAll('.view-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.nav-tab').forEach(el => {
            el.classList.remove('border-blue-500', 'text-blue-500', 'dark:text-blue-400');
        el.classList.add('border-transparent', 'text-slate-500', 'dark:text-slate-400');
            });

        if (tabId === 'all') tabId = 'inventory';

        const targetView = document.getElementById('view-' + tabId);
        if (targetView) targetView.classList.remove('hidden');
        const activeTab = document.getElementById('tab-' + tabId);
        if (activeTab) {
            activeTab.classList.remove('border-transparent', 'text-slate-500', 'dark:text-slate-400');
        activeTab.classList.add('border-blue-500', 'text-blue-500', 'dark:text-blue-400');
            }

        if (tabId === 'inventory') filterWidgets();
        else if (tabId === 'users') renderUsersTable();
        else if (tabId === 'activity') renderActivityTable();

        try {
            sessionStorage.setItem('active_dashboard_tab', tabId);
        if (window.history && window.history.replaceState) {
            window.history.replaceState(null, '', '#' + tabId);
                }
            } catch { }

        if (typeof authManager !== 'undefined') {
            authManager.logActivity('NAVIGATION', tabId.toUpperCase(), '', `Switched to ${tabId} tab`);
            }
        lucide.createIcons();
        window.scrollTo({top: 0, behavior: 'smooth' });
        }

        let pendingDeleteUserId = null;

        function renderUsersTable() {
            if (typeof authManager === 'undefined') return;
        const users = authManager.getUsers();
        const tbody = document.getElementById('userTableBody');
        const mobileContainer = document.getElementById('userMobileCardsList');
        if (!tbody) return;
        if (typeof updateCloudSyncUI === 'function') updateCloudSyncUI();

        const totalEl = document.getElementById('statTotalUsers');
        const activeEl = document.getElementById('statActiveUsers');
        const adminEl = document.getElementById('statAdminUsers');
        const staffEl = document.getElementById('statStaffUsers');

        if (totalEl) totalEl.innerText = users.length;
            if (activeEl) activeEl.innerText = users.filter(u => u.status === 'active').length;
            if (adminEl) adminEl.innerText = users.filter(u => u.role === 'admin').length;
            if (staffEl) staffEl.innerText = users.filter(u => u.role !== 'admin' && u.role !== 'viewer').length;

        const currUser = authManager.getCurrentUser() || { };

            tbody.innerHTML = users.map(u => {
                const isSelf = String(u.id) === String(currUser.id) ||
        (u.email && currUser.email && u.email.toLowerCase() === currUser.email.toLowerCase()) ||
        (u.username && currUser.username && u.username.toLowerCase() === currUser.username.toLowerCase());

        const roleColors = {
            admin: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 border-blue-200 dark:border-blue-800',
        developer: 'text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/60 border-teal-200 dark:border-teal-800',
        qa: 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/60 border-amber-200 dark:border-amber-800',
        content: 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-950/60 border-purple-200 dark:border-purple-800',
        viewer: 'text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-800'
                };
        const roleClass = roleColors[u.role] || roleColors.viewer;

        return `
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
            <td class="py-3 px-4">
                <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center font-bold text-xs shrink-0">
                        ${(u.fullName || 'U').charAt(0).toUpperCase()}
                    </div>
                    <div class="min-w-0">
                        <div class="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                            <span class="truncate">${u.fullName || 'User'}</span>
                            ${isSelf ? '<span class="text-[9px] px-1.5 py-0.2 rounded bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300 font-semibold uppercase">You</span>' : ''}
                        </div>
                        <div class="text-[11px] text-slate-400 font-mono truncate">${u.email}</div>
                    </div>
                </div>
            </td>
            <td class="py-3 px-4">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold uppercase border ${roleClass}">
                    ${u.role}
                </span>
            </td>
            <td class="py-3 px-4">
                <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${u.status === 'active' ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20' : 'bg-slate-500/10 text-slate-500 border-slate-500/20'}">
                    <span class="w-1.5 h-1.5 rounded-full ${u.status === 'active' ? 'bg-emerald-500' : 'bg-slate-400'}"></span>
                    ${u.status}
                </span>
            </td>
            <td class="py-3 px-4 font-mono text-[11px] text-slate-500">
                ${u.lastLogin ? new Date(u.lastLogin).toLocaleDateString() : 'Never'}
            </td>
            <td class="py-3 px-4 text-right">
                <div class="inline-flex items-center gap-1.5 justify-end">
                    <button onclick="openEditUserModal('${u.id}')" title="Edit user details" class="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/60 dark:hover:bg-blue-900 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800 transition flex items-center gap-1 cursor-pointer">
                        <i data-lucide="edit-3" class="w-3 h-3"></i>
                        <span>Edit</span>
                    </button>
                    <button onclick="toggleUserStatus('${u.id}')" title="${u.status === 'active' ? 'Disable account' : 'Activate account'}" class="px-2.5 py-1 rounded-md text-[11px] font-semibold ${u.status === 'active' ? 'bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/60 dark:hover:bg-amber-900 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800' : 'bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-950/60 dark:hover:bg-emerald-900 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800'} transition flex items-center gap-1 cursor-pointer" ${isSelf ? 'disabled style="opacity: 0.3; cursor: not-allowed;"' : ''}>
                        <i data-lucide="${u.status === 'active' ? 'user-x' : 'user-check'}" class="w-3 h-3"></i>
                        <span>${u.status === 'active' ? 'Disable' : 'Enable'}</span>
                    </button>
                    <button onclick="openDeleteUserModal('${u.id}')" title="Delete user" class="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/60 dark:hover:bg-rose-900 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800 transition flex items-center gap-1 cursor-pointer" ${isSelf ? 'disabled style="opacity: 0.3; cursor: not-allowed;"' : ''}>
                        <i data-lucide="trash-2" class="w-3 h-3"></i>
                        <span>Delete</span>
                    </button>
                </div>
            </td>
        </tr>
        `;
            }).join('');

        if (mobileContainer) {
            mobileContainer.innerHTML = users.map(u => {
                const isSelf = String(u.id) === String(currUser.id) ||
                    (u.email && currUser.email && u.email.toLowerCase() === currUser.email.toLowerCase()) ||
                    (u.username && currUser.username && u.username.toLowerCase() === currUser.username.toLowerCase());
                return `
                    <div class="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
                        <div class="flex items-start justify-between gap-2">
                            <div class="flex items-center gap-2.5">
                                <div class="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center font-bold text-xs shrink-0">
                                    ${(u.fullName || 'U').charAt(0).toUpperCase()}
                                </div>
                                <div>
                                    <div class="font-semibold text-xs text-slate-900 dark:text-white flex items-center gap-1.5">
                                        <span>${u.fullName || 'User'}</span>
                                        ${isSelf ? '<span class="text-[9px] px-1.5 py-0.2 rounded bg-blue-100 dark:bg-blue-900 text-blue-600 font-semibold uppercase">You</span>' : ''}
                                    </div>
                                    <div class="text-[11px] text-slate-400 font-mono">${u.email}</div>
                                </div>
                            </div>
                            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold uppercase border border-blue-500/20 bg-blue-500/10 text-blue-600 dark:text-blue-400">
                                ${u.role}
                            </span>
                        </div>
                        <div class="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-100 dark:border-slate-800">
                            <span>Status: <strong class="${u.status === 'active' ? 'text-emerald-600' : 'text-slate-400'}">${u.status}</strong></span>
                            <span>Login: <strong>${u.lastLogin ? new Date(u.lastLogin).toLocaleDateString() : 'Never'}</strong></span>
                        </div>
                        <div class="grid grid-cols-3 gap-2 pt-1">
                            <button onclick="openEditUserModal('${u.id}')" class="py-1.5 rounded-lg text-center text-xs font-semibold bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800 flex items-center justify-center gap-1">
                                <i data-lucide="edit-3" class="w-3 h-3"></i>
                                <span>Edit</span>
                            </button>
                            <button onclick="toggleUserStatus('${u.id}')" class="py-1.5 rounded-lg text-center text-xs font-semibold ${u.status === 'active' ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-emerald-50 text-emerald-700 border-emerald-200'} border flex items-center justify-center gap-1" ${isSelf ? 'disabled style="opacity: 0.3;"' : ''}>
                                <i data-lucide="${u.status === 'active' ? 'user-x' : 'user-check'}" class="w-3 h-3"></i>
                                <span>${u.status === 'active' ? 'Disable' : 'Enable'}</span>
                            </button>
                            <button onclick="openDeleteUserModal('${u.id}')" class="py-1.5 rounded-lg text-center text-xs font-semibold bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800 flex items-center justify-center gap-1" ${isSelf ? 'disabled style="opacity: 0.3;"' : ''}>
                                <i data-lucide="trash-2" class="w-3 h-3"></i>
                                <span>Delete</span>
                            </button>
                        </div>
                    </div>
                    `;
            }).join('');
            }

        if (window.lucide) lucide.createIcons();
        }

        // ==========================================
        // SUPABASE CLOUD DATABASE SYNC CONTROLS
        // ==========================================
        const SUPABASE_SCHEMA_SQL = `-- Supabase PostgreSQL Schema for Widget Dashboard
        create table if not exists public.app_users (
        id text primary key,
        full_name text not null,
        username text not null,
        email text unique not null,
        password_hash text not null,
        role text not null default 'viewer',
        status text not null default 'active',
        created_at timestamp with time zone default timezone('utc'::text, now()) not null,
        last_login timestamp with time zone
        );

        create table if not exists public.app_activity_logs (
        id text primary key,
        user_id text,
        user_name text,
        user_email text,
        role text,
        activity_type text not null,
        section text,
        target_ref text,
        details text,
        timestamp timestamp with time zone default timezone('utc'::text, now()) not null
        );

        alter table public.app_users enable row level security;
        alter table public.app_activity_logs enable row level security;

        grant usage on schema public to anon, authenticated, service_role;
        grant all on table public.app_users to anon, authenticated, service_role;
        grant all on table public.app_activity_logs to anon, authenticated, service_role;

        create policy "Allow anon read and write on app_users" on public.app_users for all to anon, authenticated using (true) with check (true);
        create policy "Allow anon read and write on app_activity_logs" on public.app_activity_logs for all to anon, authenticated using (true) with check (true);

        alter publication supabase_realtime add table public.app_users;
        alter publication supabase_realtime add table public.app_activity_logs;`;

        function openCloudSyncModal() {
            const modal = document.getElementById('cloudSyncModal');
        if (!modal) return;
        if (typeof authManager !== 'undefined') {
                const config = authManager.getSupabaseConfig();
        const urlEl = document.getElementById('supabaseUrlInput');
        const keyEl = document.getElementById('supabaseKeyInput');
        if (urlEl) urlEl.value = config.url || '';
        if (keyEl) keyEl.value = config.anonKey || '';
            }
        updateCloudSyncUI();
        modal.classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
        }

        function closeCloudSyncModal() {
            const modal = document.getElementById('cloudSyncModal');
        if (modal) modal.classList.add('hidden');
        }

        async function saveAndConnectSupabase() {
            if (typeof authManager === 'undefined') return;
        const urlInput = document.getElementById('supabaseUrlInput');
        const keyInput = document.getElementById('supabaseKeyInput');
        const url = urlInput ? urlInput.value.trim() : '';
        const key = keyInput ? keyInput.value.trim() : '';

        const btn = document.getElementById('saveSupabaseBtn');
        const originalBtn = btn ? btn.innerHTML : '';
        if (btn) btn.innerHTML = '<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i><span>Connecting...</span>';

        authManager.saveSupabaseConfig(url, key, true);

        if (url && key) {
                try {
                    const res = await authManager.syncWithCloud();
        if (res && res.error) {
            showToast(`Supabase Error: ${res.error}`, 'error');
                    } else if (res && res.seeded) {
            showToast(`Connected & uploaded ${res.count || 7} team accounts to cloud!`, 'success');
                    } else if (res && res.count) {
            showToast(`Connected! Synced ${res.count} team accounts from cloud.`, 'success');
                    } else {
            showToast('Connected to Supabase PostgreSQL successfully!', 'success');
                    }
                } catch (e) {
            showToast('Connection error: ' + (e.message || e), 'error');
                }
            } else {
            showToast('Switched to local offline browser storage.', 'info');
            }

        if (btn) btn.innerHTML = originalBtn;
        updateCloudSyncUI();
        renderUsersTable();
        closeCloudSyncModal();
        if (window.lucide) lucide.createIcons();
        }

        function copySupabaseSchema() {
            if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(SUPABASE_SCHEMA_SQL).then(() => {
                showToast('Supabase SQL Schema copied to clipboard!', 'success');
            }).catch(() => {
                showToast('Please copy schema from scripts/supabase_schema.sql', 'info');
            });
            } else {
            showToast('Please copy schema from scripts/supabase_schema.sql', 'info');
            }
        }

        function updateCloudSyncUI() {
            if (typeof authManager === 'undefined') return;
        const isConnected = authManager.isSupabaseConnected();
        const isConfigured = authManager.isSupabaseConfigured();

        const dot = document.getElementById('cloudStatusDot');
        const text = document.getElementById('cloudStatusBtnText');
        const modalDot = document.getElementById('cloudModalStatusDot');
        const modalTitle = document.getElementById('cloudModalStatusTitle');
        const modalBadge = document.getElementById('cloudModeBadge');
        const modalDesc = document.getElementById('cloudModalStatusDesc');
        const cloudBadge = document.getElementById('cloudStatusBadge');

        if (isConnected) {
                if (dot) dot.className = 'w-2 h-2 rounded-full bg-emerald-500 animate-pulse';
        if (text) text.textContent = 'Cloud Connected';
        if (modalDot) modalDot.className = 'w-2.5 h-2.5 rounded-full bg-emerald-500';
        if (modalTitle) modalTitle.textContent = 'Supabase Cloud Connected';
        if (modalBadge) {
            modalBadge.className = 'font-mono text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20';
        modalBadge.textContent = 'Live PostgreSQL Sync';
                }
        if (modalDesc) modalDesc.textContent = 'Real-time multi-device sync is active. Any user created, updated, or removed will sync instantly across all machines.';
        if (cloudBadge) {
            cloudBadge.className = 'text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold border border-emerald-500/20';
        cloudBadge.textContent = 'v2.8 Live Cloud DB';
                }
            } else if (isConfigured) {
                if (dot) dot.className = 'w-2 h-2 rounded-full bg-amber-500';
        if (text) text.textContent = 'Connecting...';
        if (modalDot) modalDot.className = 'w-2.5 h-2.5 rounded-full bg-amber-500';
        if (modalTitle) modalTitle.textContent = 'Connecting to Supabase...';
        if (modalBadge) {
            modalBadge.className = 'font-mono text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20';
        modalBadge.textContent = 'Connecting';
                }
        if (modalDesc) modalDesc.textContent = 'Attempting connection to your Supabase instance. Ensure tables exist by running scripts/supabase_schema.sql.';
            } else {
                if (dot) dot.className = 'w-2 h-2 rounded-full bg-slate-400';
        if (text) text.textContent = 'Cloud Database';
        if (modalDot) modalDot.className = 'w-2.5 h-2.5 rounded-full bg-slate-400';
        if (modalTitle) modalTitle.textContent = 'Local Offline Mode';
        if (modalBadge) {
            modalBadge.className = 'font-mono text-[10px] px-2 py-0.5 rounded-full bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-500/20';
        modalBadge.textContent = 'Browser Storage';
                }
        if (modalDesc) modalDesc.textContent = 'Currently storing accounts locally in your browser. Connect Supabase to sync team accounts across all computers, tablets, and phones in real-time.';
            }
        if (window.lucide) lucide.createIcons();
        }

        // Auto-refresh user table when users change via cloud or other tabs
        window.addEventListener('dashboard_users_changed', () => {
            if (typeof renderUsersTable === 'function') renderUsersTable();
        if (typeof updateCloudSyncUI === 'function') updateCloudSyncUI();
        });

        function openAddUserModal() {
            const modal = document.getElementById('addUserModal');
        if (!modal) return;
        document.getElementById('addUserName').value = '';
        document.getElementById('addUserEmail').value = '';
        document.getElementById('addUserRole').value = 'viewer';
        document.getElementById('addUserPass').value = 'Widget2026!';
        modal.classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
        }

        function closeAddUserModal() {
            const modal = document.getElementById('addUserModal');
        if (modal) modal.classList.add('hidden');
        }

        function handleSaveNewUser(e) {
            e.preventDefault();
        if (typeof authManager === 'undefined') return;
        const name = document.getElementById('addUserName').value.trim();
        const email = document.getElementById('addUserEmail').value.trim();
        const role = document.getElementById('addUserRole').value;
        const pass = document.getElementById('addUserPass').value.trim();

        const res = authManager.addUser(name, email, pass, role);
        if (res.success) {
            closeAddUserModal();
        renderUsersTable();
        showToast(`User ${name} added successfully!`, 'success');
            } else {
            alert(res.error || 'Failed to create user');
            }
        }

        function openEditUserModal(userId) {
            if (typeof authManager === 'undefined') return;
        const users = authManager.getUsers();
            const user = users.find(u => String(u.id) === String(userId));
        if (!user) return;

        document.getElementById('editUserId').value = user.id;
        document.getElementById('editUserName').value = user.fullName || '';
        document.getElementById('editUserEmail').value = user.email || '';
        document.getElementById('editUserRole').value = user.role || 'viewer';
        document.getElementById('editUserPass').value = '';

        const modal = document.getElementById('editUserModal');
        if (modal) modal.classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
        }

        function closeEditUserModal() {
            const modal = document.getElementById('editUserModal');
        if (modal) modal.classList.add('hidden');
        }

        function handleSaveEditUser(e) {
            e.preventDefault();
        if (typeof authManager === 'undefined') return;
        const id = document.getElementById('editUserId').value;
        const name = document.getElementById('editUserName').value.trim();
        const email = document.getElementById('editUserEmail').value.trim();
        const role = document.getElementById('editUserRole').value;
        const pass = document.getElementById('editUserPass').value.trim();

        const res = authManager.editUser(id, {fullName: name, email, role, password: pass });
        if (res.success) {
            closeEditUserModal();
        renderUsersTable();
        initUserProfile();
        showToast(`User details updated successfully!`, 'success');
            } else {
            alert(res.error || 'Failed to update user');
            }
        }

        function toggleUserStatus(userId) {
            if (typeof authManager === 'undefined') return;
        const res = authManager.toggleUserStatus(userId);
        if (res.success) {
            renderUsersTable();
        showToast(`User status updated to ${res.status.toUpperCase()}`, 'info');
            } else {
            alert(res.error || 'Failed to change status');
            }
        }

        function openDeleteUserModal(userId) {
            if (typeof authManager === 'undefined') return;
        const users = authManager.getUsers();
            const user = users.find(u => String(u.id) === String(userId));
        if (!user) return;

        pendingDeleteUserId = userId;
        const nameEl = document.getElementById('deleteTargetName');
        const emailEl = document.getElementById('deleteTargetEmail');
        const roleEl = document.getElementById('deleteTargetRole');

        if (nameEl) nameEl.innerText = user.fullName || 'User';
        if (emailEl) emailEl.innerText = user.email || '';
        if (roleEl) roleEl.innerText = `Role: ${(user.role || '').toUpperCase()}`;

        const modal = document.getElementById('deleteUserModal');
        if (modal) modal.classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
        }

        function closeDeleteUserModal() {
            pendingDeleteUserId = null;
        const modal = document.getElementById('deleteUserModal');
        if (modal) modal.classList.add('hidden');
        }

        function confirmDeleteUser() {
            if (!pendingDeleteUserId || typeof authManager === 'undefined') return;
        const res = authManager.deleteUser(pendingDeleteUserId);
        if (res.success) {
            closeDeleteUserModal();
        renderUsersTable();
        showToast('User permanently removed', 'success');
            } else {
            alert(res.error || 'Failed to delete user');
            }
        }

        function renderActivityTable() {
            if (typeof authManager === 'undefined') return;
        const logs = authManager.getLogs ? authManager.getLogs() : [];
        const tbody = document.getElementById('activityTableBody');
        if (!tbody) return;
        if (typeof updateCloudSyncUI === 'function') updateCloudSyncUI();

        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="p-6 text-center text-slate-400">No activity logged yet.</td></tr>';
        return;
            }

            tbody.innerHTML = logs.map(l => `
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
            <td class="py-2.5 px-4 font-mono text-[11px] text-slate-500">${l.timestamp ? new Date(l.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''}</td>
            <td class="py-2.5 px-4">
                <div class="font-medium text-slate-900 dark:text-white">${l.userName || l.userEmail || ''}</div>
                <div class="text-[10px] text-slate-400 font-mono uppercase">${l.role || ''}</div>
            </td>
            <td class="py-2.5 px-4 font-mono text-[11px] font-semibold text-teal-600 dark:text-teal-400">${l.activityType || ''}</td>
            <td class="py-2.5 px-4 text-slate-600 dark:text-slate-400">${l.section || ''}</td>
            <td class="py-2.5 px-4 text-slate-500">${l.details || ''}</td>
        </tr>
        `).join('');
        if (window.lucide) lucide.createIcons();
        }

        function setSourceToggle(mode) {
            const btnAtt = document.getElementById('btn-toggle-attention');
        const btnAll = document.getElementById('btn-toggle-all');
        if (mode === 'attention') {
                if (btnAtt) {
            btnAtt.className = 'px-3.5 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer flex items-center gap-1.5 bg-rose-600 text-white shadow-xs active:scale-95';
                }
        if (btnAll) {
            btnAll.className = 'px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition cursor-pointer flex items-center gap-1.5 active:scale-95';
                }
        setFilterQuick('needs_attention');
            } else {
                if (btnAll) {
            btnAll.className = 'px-3.5 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer flex items-center gap-1.5 bg-blue-600 text-white shadow-xs active:scale-95';
                }
        if (btnAtt) {
            btnAtt.className = 'px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition cursor-pointer flex items-center gap-1.5 active:scale-95';
                }
        setFilterQuick('all');
            }
        }

        const filterHelpDescriptions = {
            'all': 'All Scope (294): Shows all 294 curriculum widgets tracked across QA, Git, and Excel.',
            'needs_attention': 'Needs Attention (36): Widgets requiring action — 15 pending QA deployment + 21 missing in Git.',
            'matched_all': 'Matched in All 3 (258): Production-ready widgets verified present and working in QA, Git, and Excel.',
            'missing_qa': 'Missing in QA (15): Widgets present in Git and Excel, but not yet deployed to the QA server.',
            'requires_dev': 'Missing in Git (21): Widgets in curriculum scope missing in Git codebase (12 dev backlog + 9 whiteboard tools).',
            'missing_git': 'Missing in Git (21): Widgets in curriculum scope missing in Git codebase (12 dev backlog + 9 whiteboard tools).',
            'pending_dev': 'Pending Dev Backlog (12): In-scope widgets that have not yet been developed in the repository.',
            'developed': 'Developed in Scope (273): Curriculum scope widgets with code committed in the repository.',
            'source_present': 'Developed in Scope (273): Curriculum scope widgets with code committed in the repository.',
            'in_qa': 'In QA (258): Curriculum scope widgets deployed and verified in the QA environment.',
            'whiteboard': 'Canvas Scope Tools (9): Canvas and whiteboard widgets in curriculum scope.',
            'canvas': 'Canvas Scope Tools (9): Canvas and whiteboard widgets in curriculum scope.',
            'naming_issues': 'Name Differences (7): Widgets with minor name differences between Excel and codebase.',
            'name_diff': 'Name Differences (7): Widgets with minor name differences between Excel and codebase.',
            'present_in_git': 'Present in Git (273): All curriculum scope widgets with verified runnable code committed in repository.',
            'extra_qa': 'Extra in QA (13): Additional standalone repository widgets cataloged in QA environment.',
            'all_including_extra': 'Total Tracked Assets (340): All 294 Curriculum Scope widgets plus 46 Extra Standalone repository tools.',
            'all_codebase': 'All Git Codebase (319): All assets present in Git repository (273 Scope + 46 Extra).',
            'qa_verified': 'All QA Verified (271): All assets cataloged in QA (258 Scope + 13 Extra).',
            'extra_repo': 'Extra in Repo (+46): Standalone widgets found in Git repository that are not in the 294 curriculum scope.',
            'search': 'Search: Filter instantly by widget name, WG code (e.g. WG-042), UID (tool-xxxx), subject, or developer.',
            'subject': 'Subject Filter: Narrow down widgets by curriculum subject (e.g., Mathematics, Physics, Chemistry).',
            'owner': 'Owner Filter: Filter widgets by assigned developer (Prasanna, Nitin, or Extra).',
            'reset': 'Reset: Clears all search keywords, subject filters, owner selections, and status back to default.'
        };

        function getOwnerDetails(name) {
            const raw = (name || '').trim();
            if (!raw || raw === '-' || raw === 'None') {
                return {
                    initials: '—',
                    name: 'Unassigned',
                    bg: 'bg-slate-400',
                    badge: 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400 border-slate-200 dark:border-slate-700'
                };
            }
            if (raw === 'Repository Extra' || raw.toLowerCase().includes('extra') || raw.toLowerCase().includes('repo')) {
                return {
                    initials: 'E',
                    name: 'Extra',
                    bg: 'bg-purple-600',
                    badge: 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800/60'
                };
            }
            if (raw.toLowerCase().includes('prasanna')) {
                return {
                    initials: 'P',
                    name: 'Prasanna',
                    bg: 'bg-indigo-600',
                    badge: 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800/60'
                };
            }
            if (raw.toLowerCase().includes('nitin')) {
                return {
                    initials: 'N',
                    name: 'Nitin',
                    bg: 'bg-teal-600',
                    badge: 'bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-300 border-teal-200 dark:border-teal-800/60'
                };
            }
            const firstName = raw.split(' ')[0];
            return {
                initials: firstName.charAt(0).toUpperCase(),
                name: firstName,
                bg: 'bg-blue-600',
                badge: 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800/60'
            };
        }

        function showFilterHelp(key) {
            const el = document.getElementById('filterHelpText');
            const icon = document.getElementById('filterHelpIcon');
            if (!el || !filterHelpDescriptions[key]) return;
            el.innerText = filterHelpDescriptions[key];
            el.classList.add('text-blue-600', 'dark:text-blue-400');
            if (icon) icon.className = 'w-3.5 h-3.5 text-blue-600 dark:text-blue-400 shrink-0 transition-all scale-110';
        }

        function resetFilterHelp() {
            const el = document.getElementById('filterHelpText');
            const icon = document.getElementById('filterHelpIcon');
            if (!el) return;
            el.classList.remove('text-blue-600', 'dark:text-blue-400');
            if (icon) icon.className = 'w-3.5 h-3.5 text-blue-500 shrink-0 transition-all';

            const activeKey = document.getElementById('statusFilter')?.value || 'all';
            const subj = document.getElementById('subjectFilter')?.value || 'all';
            const count = typeof filteredData !== 'undefined' ? filteredData.length : '';

            if (subj !== 'all' && activeKey !== 'all') {
                const statDesc = filterHelpDescriptions[activeKey] ? filterHelpDescriptions[activeKey].split(':')[0] : activeKey;
                el.innerText = `${subj} • ${statDesc} (${count} widget${count === 1 ? '' : 's'} matching)`;
            } else if (subj !== 'all') {
                el.innerText = `Subject: ${subj} (${count} widget${count === 1 ? '' : 's'} in curriculum scope)`;
            } else if (filterHelpDescriptions[activeKey]) {
                el.innerText = filterHelpDescriptions[activeKey];
            } else {
                el.innerText = filterHelpDescriptions['all'];
            }
        }

        function setFilterQuick(statusKey) {
            const statusSelect = document.getElementById('statusFilter');
            if (statusSelect) statusSelect.value = statusKey;
            syncQuickFilterPills(statusKey);
            resetFilterHelp();
            currentPage = 1;
            filterWidgets();
        }

        function clearSearchInput() {
            const input = document.getElementById('widgetSearch');
            if (input) input.value = '';
            const btn = document.getElementById('searchClearBtn');
            if (btn) btn.classList.add('hidden');
            const hint = document.getElementById('searchKbdHint');
            if (hint) hint.classList.remove('hidden');
            filterWidgets();
        }

        function syncQuickFilterPills(statusKey) {
            let activeTarget = statusKey;
            if (activeTarget === 'missing_git') activeTarget = 'requires_dev';
            const pillConfigs = {
                'all': { active: 'bg-blue-600 text-white border-blue-600 shadow-xs font-bold', inactive: 'text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:border-blue-500 font-semibold' },
                'needs_attention': { active: 'bg-rose-600 text-white border-rose-600 shadow-xs font-bold', inactive: 'text-rose-700 dark:text-rose-400 bg-rose-500/10 hover:bg-rose-500/20 border-rose-500/25 font-semibold' },
                'matched_all': { active: 'bg-emerald-600 text-white border-emerald-600 shadow-xs font-bold', inactive: 'text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 border-emerald-500/25 font-semibold' },
                'missing_qa': { active: 'bg-amber-600 text-white border-amber-600 shadow-xs font-bold', inactive: 'text-amber-700 dark:text-amber-400 bg-amber-500/10 hover:bg-amber-500/20 border-amber-500/25 font-semibold' },
                'requires_dev': { active: 'bg-rose-600 text-white border-rose-600 shadow-xs font-bold', inactive: 'text-rose-700 dark:text-rose-400 bg-rose-500/10 hover:bg-rose-500/20 border-rose-500/25 font-semibold' },
                'extra_repo': { active: 'bg-purple-600 text-white border-purple-600 shadow-xs font-bold', inactive: 'text-purple-700 dark:text-purple-400 bg-purple-500/10 hover:bg-purple-500/20 border-purple-500/25 font-semibold' }
            };

            const baseClass = 'quick-pill px-3 py-1.5 rounded-lg border transition cursor-pointer flex items-center gap-1.5 text-xs';

            Object.keys(pillConfigs).forEach(key => {
                const el = document.getElementById('pill-filter-' + key);
                if (!el) return;
                const conf = pillConfigs[key];
                if (key === activeTarget) {
                    el.className = `${baseClass} ${conf.active}`;
                } else {
                    el.className = `${baseClass} ${conf.inactive}`;
                }
            });
        }

        function drillDownSubject(subj) {
            switchTab('all');
        const subjSelect = document.getElementById('subjectFilter');
        if (subjSelect) subjSelect.value = subj;
        const statSelect = document.getElementById('statusFilter');
        if (statSelect) statSelect.value = 'all';
        syncQuickFilterPills('all');
        currentPage = 1;
        filterWidgets();
        window.scrollTo({top: 0, behavior: 'smooth' });
        }

        function drillDownSubjectAndStatus(subj, statusKey) {
            switchTab('all');
        const subjSelect = document.getElementById('subjectFilter');
        if (subjSelect) subjSelect.value = subj || 'all';
        const statSelect = document.getElementById('statusFilter');
        if (statSelect) statSelect.value = statusKey || 'all';
        const searchInput = document.getElementById('widgetSearch');
        if (searchInput) searchInput.value = '';
        syncQuickFilterPills(statusKey || 'all');
        currentPage = 1;
        filterWidgets();
        window.scrollTo({top: 0, behavior: 'smooth' });
        }

        function drillDown(statusKey) {
            document.querySelectorAll('.view-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.nav-tab').forEach(el => {
            el.classList.remove('border-blue-500', 'text-blue-500', 'dark:text-blue-400');
        el.classList.add('border-transparent', 'text-slate-500', 'dark:text-slate-400');
            });

        const invView = document.getElementById('view-inventory');
        if (invView) invView.classList.remove('hidden');

        const activeTab = document.getElementById('tab-inventory');
        if (activeTab) {
            activeTab.classList.remove('border-transparent', 'text-slate-500', 'dark:text-slate-400');
        activeTab.classList.add('border-blue-500', 'text-blue-500', 'dark:text-blue-400');
            }

        const statusSelect = document.getElementById('statusFilter');
        if (statusSelect) statusSelect.value = statusKey;
        const subjSelect = document.getElementById('subjectFilter');
        if (subjSelect) subjSelect.value = 'all';
        const searchInput = document.getElementById('widgetSearch');
        if (searchInput) searchInput.value = '';

        syncQuickFilterPills(statusKey);
        resetFilterHelp();
        currentPage = 1;
        filterWidgets();
        window.scrollTo({top: 0, behavior: 'smooth' });
        }

        function clearFilter() {
            const statusSelect = document.getElementById('statusFilter');
            if (statusSelect) statusSelect.value = 'all';
            const subjSelect = document.getElementById('subjectFilter');
            if (subjSelect) subjSelect.value = 'all';
            const ownerSelect = document.getElementById('ownerFilter');
            if (ownerSelect) ownerSelect.value = 'all';
            const searchInput = document.getElementById('widgetSearch');
            if (searchInput) searchInput.value = '';
            const searchClear = document.getElementById('searchClearBtn');
            if (searchClear) searchClear.classList.add('hidden');
            syncQuickFilterPills('all');
            resetFilterHelp();
            currentPage = 1;
            filterWidgets();
        }

        function updateFilterBanner(statusKey) {
            const banner = document.getElementById('activeFilterBanner');
            const label = document.getElementById('filterBannerLabel');
            if (!banner || !label) return;

            const counts = getCategoryCounts();
            const labels = {
                'needs_attention': `Widgets Needing Attention (${counts.needs_attention} Widgets - 21 Missing in Git + 15 Missing in QA)`,
                'matched_all': `Matched in All 3 Sources (${counts.matched_all} Widgets - Production Ready)`,
                'missing_qa': `Missing in QA Catalog (${counts.missing_qa} Widgets)`,
                'requires_dev': `Missing in Git Repository (21 Widgets)`,
                'missing_git': `Missing in Git Repository (21 Widgets)`,
                'pending_dev': `Pending Dev Backlog (${counts.pending_dev || 12} Widgets)`,
                'developed': `Developed Widgets in Scope (${counts.source_present || 273} Widgets)`,
                'source_present': `Developed Widgets in Scope (${counts.source_present || 273} Widgets)`,
                'in_qa': `QA Verified Widgets in Scope (${counts.matched_all || 258} Widgets)`,
                'qa_ready': `QA Verified Widgets in Scope (${counts.matched_all || 258} Widgets)`,
                'whiteboard': `Canvas / Whiteboard Scope Tools (${counts.whiteboard || 9} Widgets)`,
                'canvas': `Canvas / Whiteboard Scope Tools (${counts.whiteboard || 9} Widgets)`,
                'naming_issues': `Widgets with Minor Naming Differences (${counts.naming_issues || 7} Widgets)`,
                'name_diff': `Widgets with Minor Naming Differences (${counts.naming_issues || 7} Widgets)`,
                'extra_repo': `Extra in Repository (+${counts.extra_repo} Standalone Assets)`,
                'extra_qa': `Extra in Repository & QA Catalog (13 Widgets)`,
                'present_in_git': `In Scope & Present in Git (273 Widgets)`,
                'all_codebase': `All Git Codebase Assets (319 Assets)`,
                'qa_verified': `All QA Verified Assets (271 Assets)`,
                'all_including_extra': `All Tracked Assets (${rawData.length} Total Universe)`
            };

            const subj = document.getElementById('subjectFilter')?.value || 'all';
            let labelText = '';
            if (subj !== 'all' && statusKey && statusKey !== 'all') {
                const statName = labels[statusKey] ? labels[statusKey].split('(')[0].trim() : statusKey;
                labelText = `${subj} • ${statName} (${filteredData.length} widgets)`;
            } else if (subj !== 'all') {
                labelText = `Subject: ${subj} (${filteredData.length} widgets)`;
            } else if (statusKey && statusKey !== 'all' && labels[statusKey]) {
                labelText = labels[statusKey];
            }

            if (labelText) {
                label.innerText = labelText;
                banner.classList.remove('hidden');
            } else {
                banner.classList.add('hidden');
            }
            if (window.lucide) lucide.createIcons();
        }

        function getCategoryCounts() {
            let total = 0, needs_attention = 0;
        let matched_all = 0, missing_qa = 0, pending_dev = 0, whiteboard = 0;
        let extra_repo = 0, naming_issues = 0, investigation = 0, duplicates = 0;
        let source_present = 0, in_qa = 0;

            rawData.forEach(w => {
                if (w.in_qa) in_qa++;
        if (w.is_extra) {
            extra_repo++;
        return;
                }
        total++;
        if (w.needs_attention) needs_attention++;
        if (w.has_file && w.in_qa) matched_all++;
        if (w.has_file && !w.in_qa) missing_qa++;
        if (w.status_category === 'requires_dev') pending_dev++;
        if (w.status_category === 'whiteboard') whiteboard++;
        if (w.status_category === 'corrected' || w.status_category === 'minor_changes') naming_issues++;
        if (w.excel_status === 'repeated') duplicates++;
        if (w.excel_status === 'repeated' || w.excel_status === 'not_found' || w.status_category === 'minor_changes') investigation++;
        if (w.has_file) source_present++;
            });

        return {
            total, needs_attention, matched_all, missing_qa, pending_dev, whiteboard,
            extra_repo, naming_issues, investigation, duplicates, source_present, in_qa
        };
        }

        function getStatusBadge(category, label, u) {
            if (u && u.reconcile_cat === 'matched_all') {
                return '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold border bg-emerald-500/10 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-500/25"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 shrink-0"></span>Matched in All 3</span>';
            }
        if (u && u.reconcile_cat === 'missing_qa') {
                return '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold border bg-amber-500/10 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border-amber-500/25"><span class="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1.5 shrink-0"></span>Missing in QA</span>';
            }

        const config = {
            available: {cls: 'bg-emerald-500/10 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-500/25', dot: 'bg-emerald-500' },
        corrected: {cls: 'bg-sky-500/10 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300 border-sky-500/25', dot: 'bg-sky-500' },
        requires_dev: {cls: 'bg-rose-500/10 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border-rose-500/25', dot: 'bg-rose-500' },
        whiteboard: {cls: 'bg-indigo-500/10 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border-indigo-500/25', dot: 'bg-indigo-500' },
        minor_changes: {cls: 'bg-purple-500/10 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300 border-purple-500/25', dot: 'bg-purple-500' },
        extra_repo: {cls: 'bg-purple-500/10 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300 border-purple-500/25', dot: 'bg-purple-500' }
            };
        const c = config[category] || {cls: 'bg-slate-500/10 text-slate-700 border-slate-300', dot: 'bg-slate-400' };
        return `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold border ${c.cls}"><span class="w-1.5 h-1.5 rounded-full ${c.dot} mr-1.5 shrink-0"></span>${label || category}</span>`;
        }

        function filterWidgets() {
            const searchInput = document.getElementById('widgetSearch');
            const q = searchInput ? searchInput.value.toLowerCase().trim() : '';
            const status = document.getElementById('statusFilter').value;
            const subject = document.getElementById('subjectFilter').value;
            const owner = document.getElementById('ownerFilter')?.value || 'all';

            const searchClearBtn = document.getElementById('searchClearBtn');
            const searchKbdHint = document.getElementById('searchKbdHint');
            if (searchClearBtn) {
                if (q) {
                    searchClearBtn.classList.remove('hidden');
                    if (searchKbdHint) searchKbdHint.classList.add('hidden');
                } else {
                    searchClearBtn.classList.add('hidden');
                    if (searchKbdHint) searchKbdHint.classList.remove('hidden');
                }
            }

            filteredData = rawData.filter(w => {
                if (status === 'needs_attention') {
                    if (w.is_extra || !w.needs_attention) return false;
                } else if (status === 'all') {
                    if (w.is_extra) return false;
                } else if (status === 'matched_all') {
                    if (w.is_extra || !w.has_file || !w.in_qa) return false;
                } else if (status === 'missing_qa') {
                    if (w.is_extra || !w.has_file || w.in_qa) return false;
                } else if (status === 'requires_dev' || status === 'missing_git') {
                    if (w.is_extra || w.has_file) return false;
                } else if (status === 'pending_dev') {
                    if (w.is_extra || w.status_category !== 'requires_dev') return false;
                } else if (status === 'present_in_git' || status === 'developed' || status === 'source_present') {
                    if (w.is_extra || !w.has_file) return false;
                } else if (status === 'in_qa' || status === 'qa_ready') {
                    if (w.is_extra || !w.in_qa) return false;
                } else if (status === 'extra_qa') {
                    if (!w.is_extra || !w.in_qa) return false;
                } else if (status === 'all_including_extra' || status === 'total_assets') {
                    // All 340 assets included
                    return true;
                } else if (status === 'extra_repo') {
                    if (!w.is_extra) return false;
                } else if (status === 'naming_issues' || status === 'name_diff') {
                    if (w.is_extra || (w.status_category !== 'corrected' && w.status_category !== 'minor_changes')) return false;
                } else if (status === 'investigation') {
                    if (w.is_extra) return false;
        const isInv = (w.excel_status === 'repeated' || w.excel_status === 'not_found' || w.status_category === 'minor_changes');
        if (!isInv) return false;
                } else if (status === 'duplicates') {
                    if (w.is_extra || w.excel_status !== 'repeated') return false;
                } else if (status === 'whiteboard' || status === 'canvas') {
                    if (w.is_extra || w.status_category !== 'whiteboard') return false;
                } else if (status === 'source_missing') {
                    if (w.is_extra || w.has_file || w.status_category === 'whiteboard') return false;
                } else if (status === 'qa_verified') {
                    if (!w.in_qa) return false;
                } else if (status === 'all_codebase') {
                    if (!w.has_file) return false;
                } else if (status === 'has_live') {
                    if (!w.live_html) return false;
                } else if (status.startsWith('excel:')) {
                    if (w.is_extra) return false;
        const exCat = status.replace('excel:', '');
        if (w.excel_status !== exCat) return false;
                }

        if (subject !== 'all' && w.subject !== subject) return false;
        if (owner !== 'all') {
            const wOwnerFirst = getOwnerDetails(w.owner).name.toLowerCase();
            if (wOwnerFirst !== owner.toLowerCase() && (w.owner || '').toLowerCase() !== owner.toLowerCase()) return false;
        }
        if (q) {
                    const combined = (w.name + ' ' + w.subject + ' ' + (w.owner || '') + ' ' + (w.batch || '') + ' ' + (w.wg_code || '') + ' ' + (w.excel_repo || '') + ' ' + (w.repo_path || '') + ' ' + (w.qa_tool_uid || '') + ' ' + (w.action_justification || '')).toLowerCase();
        if (!combined.includes(q)) return false;
                }
        return true;
            });

        if (status === 'needs_attention' && sortCol === 'sr' && sortAsc) {
            filteredData.sort((a, b) => (b.gaps_count - a.gaps_count) || (a.sr - b.sr));
            } else {
            filteredData.sort((a, b) => {
                let vA = a[sortCol];
                let vB = b[sortCol];
                if (typeof vA === 'boolean') { vA = vA ? 1 : 0; vB = vB ? 1 : 0; }
                if (typeof vA === 'string') return sortAsc ? vA.localeCompare(vB) : vB.localeCompare(vA);
                return sortAsc ? vA - vB : vB - vA;
            });
            }

        currentPage = 1;
        renderTable();
        updateFilterBanner(status);
        syncQuickFilterPills(status);
        resetFilterHelp();
        }

        function sortData(col) {
            if (sortCol === col) sortAsc = !sortAsc;
        else {sortCol = col; sortAsc = true; }
        filterWidgets();
        }

        function resetAllFilters() {
            const searchInput = document.getElementById('widgetSearch');
            if (searchInput) searchInput.value = '';
            const searchClearBtn = document.getElementById('searchClearBtn');
            if (searchClearBtn) searchClearBtn.classList.add('hidden');
            const searchKbdHint = document.getElementById('searchKbdHint');
            if (searchKbdHint) searchKbdHint.classList.remove('hidden');

            const statusFilter = document.getElementById('statusFilter');
            if (statusFilter) statusFilter.value = 'all';

            const subjectFilter = document.getElementById('subjectFilter');
            if (subjectFilter) subjectFilter.value = 'all';

            const ownerFilter = document.getElementById('ownerFilter');
            if (ownerFilter) ownerFilter.value = 'all';

            // Reset active filter pill buttons UI
            document.querySelectorAll('#filterPillsContainer button').forEach(b => {
                b.classList.remove('bg-blue-600', 'text-white', 'shadow-sm');
                b.classList.add('bg-white', 'dark:bg-slate-900', 'text-slate-600', 'dark:text-slate-300');
            });
            const allPill = document.querySelector('#filterPillsContainer button[data-filter="all"]');
            if (allPill) {
                allPill.classList.remove('bg-white', 'dark:bg-slate-900', 'text-slate-600', 'dark:text-slate-300');
                allPill.classList.add('bg-blue-600', 'text-white', 'shadow-sm');
            }

            if (typeof updateFilterHelp === 'function') {
                updateFilterHelp('all');
            }

            currentPage = 1;
            filterWidgets();
            if (window.lucide) lucide.createIcons();
        }

        // Resolves live simulation URLs reliably for Localhost and GitHub Pages
        function resolveLiveSimulationUrl(path) {
            if (!path) return '';
            if (path.startsWith('http://') || path.startsWith('https://')) return path;
            let cleanPath = path;
            while (cleanPath.charAt(0) === '/' || cleanPath.charCodeAt(0) === 92) {
                cleanPath = cleanPath.substring(1);
            }
            cleanPath = cleanPath.split('/').map(segment => encodeURIComponent(decodeURIComponent(segment))).join('/');
            try {
                let loc = window.location.href.split('?')[0].split('#')[0];
                if (loc.endsWith('.html') || loc.endsWith('.htm')) {
                    loc = loc.substring(0, loc.lastIndexOf('/') + 1);
                } else if (!loc.endsWith('/')) {
                    loc = loc + '/';
                }
                return new URL(cleanPath, loc).href;
            } catch (e) {
                return './' + cleanPath;
            }
        }

        // Returns the launchable live simulation URL or GitHub repository code link
        function getLiveSimulationUrl(w) {
            if (!w) return '';
            if (w.live_html) {
                return resolveLiveSimulationUrl(w.live_html);
            }
            if (w.excel_repo && w.excel_repo.startsWith('http')) {
                return w.excel_repo;
            }
            if (w.has_file && w.repo_path) {
                if (w.repo_path.startsWith('http')) return w.repo_path;
                let cleanRepo = w.repo_path;
                while (cleanRepo.charAt(0) === '/' || cleanRepo.charCodeAt(0) === 92) {
                    cleanRepo = cleanRepo.substring(1);
                }
                return 'https://github.com/tce-widgets/all-widgets-v1/blob/main/' + cleanRepo;
            }
            return '';
        }

        function renderTable() {
            const tbody = document.getElementById('widgetTableBody');
        const mobileContainer = document.getElementById('widgetMobileCardsList');
        const total = filteredData.length;
        const totalPages = Math.ceil(total / pageSize) || 1;
            if (currentPage > totalPages) currentPage = totalPages;

        const startIdx = (currentPage - 1) * pageSize;
        const items = filteredData.slice(startIdx, startIdx + pageSize);

        document.getElementById('totalFiltered').innerText = total;
        document.getElementById('pageCount').innerText = total === 0 ? '0' : `${startIdx + 1}-${Math.min(startIdx + pageSize, total)}`;
        document.getElementById('pageIndicator').innerText = `Page ${currentPage} of ${totalPages}`;
        document.getElementById('prevBtn').disabled = currentPage === 1;
            document.getElementById('nextBtn').disabled = currentPage >= totalPages;

        if (items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="p-10 text-center text-slate-500">
                <div class="flex flex-col items-center justify-center gap-2">
                    <p class="text-sm font-medium text-slate-700 dark:text-slate-300">No widgets match the selected filters.</p>
                    <p class="text-xs text-slate-400 dark:text-slate-500">Try adjusting your search query, status pill, or owner filter.</p>
                    <button type="button" onclick="resetAllFilters()" class="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-50 dark:bg-blue-950/60 border border-blue-200/80 dark:border-blue-800/80 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/60 font-semibold text-xs transition cursor-pointer shadow-sm">
                        <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i>
                        <span>Reset All Filters</span>
                    </button>
                </div>
            </td></tr>`;
            if (mobileContainer) {
                mobileContainer.innerHTML = `<div class="p-8 text-center text-slate-500 text-xs">
                    <p class="font-medium text-slate-700 dark:text-slate-300">No widgets match the selected filters.</p>
                    <p class="text-[11px] text-slate-400 mt-0.5">Try adjusting your search or filters.</p>
                    <button type="button" onclick="resetAllFilters()" class="mt-2.5 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-50 dark:bg-blue-950/60 border border-blue-200/80 dark:border-blue-800/80 text-blue-600 dark:text-blue-400 hover:bg-blue-100 font-semibold text-xs transition cursor-pointer shadow-sm">
                        <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i>
                        <span>Reset All Filters</span>
                    </button>
                </div>`;
            }
            if (window.lucide) lucide.createIcons();
            return;
        }

            // Render Mobile Cards View (Phones < 768px)
        if (mobileContainer) {
            mobileContainer.innerHTML = items.map(w => {
                const liveUrl = getLiveSimulationUrl(w);
                const isStandaloneSim = Boolean(w.live_html);
                const safeName = (w.name || '').replace(/"/g, '&quot;');
                const isQa = !!w.in_qa;
                const isGit = !!w.has_file;
                const isXl = !w.is_extra;
                const ownerInfo = getOwnerDetails(w.owner);

                return `
                    <div onclick="openModal(${w.sr})" class="p-3.5 space-y-2.5 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/40 active:bg-slate-100 dark:active:bg-slate-800 transition">
                        <div class="flex items-center justify-between gap-2">
                            <div class="flex items-center gap-1.5 font-mono text-[11px] truncate">
                                <span class="text-slate-400 font-bold shrink-0">#${w.sr}</span>
                                ${w.is_extra ? `
                                    <span class="px-1.5 py-0.2 rounded text-[10px] font-semibold bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">EXTRA</span>
                                ` : (w.wg_code && w.wg_code !== '-' ? `
                                    <span class="px-1.5 py-0.2 rounded text-[10px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">${w.wg_code}</span>
                                ` : '')}
                                <span class="text-[10px] text-slate-500 font-sans truncate">• ${w.is_extra ? 'Extra' : w.subject}</span>
                            </div>
                            <div class="text-[10px] font-mono font-medium ${w.needs_attention ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'}">
                                ${w.needs_attention ? '⚠️ Needs Attention' : '✓ All 3 Sources'}
                            </div>
                        </div>

                        <div class="font-medium text-xs text-slate-900 dark:text-white leading-snug">
                            ${w.name}
                        </div>

                        <!-- Owner with Initials Badge -->
                        <div class="flex items-center gap-1.5 text-[11px]">
                            <span class="text-slate-400 text-[10px]">Owner:</span>
                            <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md border ${ownerInfo.badge} text-[10px] font-semibold">
                                <span class="w-4 h-4 rounded-sm flex items-center justify-center text-[9px] font-bold text-white ${ownerInfo.bg}">${ownerInfo.initials}</span>
                                <span>${ownerInfo.name}</span>
                            </span>
                        </div>

                        <!-- 3 Sources Presence Pills -->
                        <div class="grid grid-cols-3 gap-1.5 text-center text-[10px] font-semibold pt-1">
                            <div class="py-1 px-1.5 rounded-lg border ${isQa ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20' : 'bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400 border-rose-200 dark:border-rose-900'}">
                                QA: ${isQa ? '✓ Present' : '✗ Missing'}
                            </div>
                            <div class="py-1 px-1.5 rounded-lg border ${isGit ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20' : 'bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400 border-rose-200 dark:border-rose-900'}">
                                Git: ${isGit ? '✓ Present' : '✗ Missing'}
                            </div>
                            <div class="py-1 px-1.5 rounded-lg border ${isXl ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20' : 'bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400 border-rose-200 dark:border-rose-900'}">
                                XL: ${isXl ? '✓ Present' : '✗ Missing'}
                            </div>
                        </div>

                        <div class="flex items-center justify-between pt-1 border-t border-slate-100 dark:border-slate-800/60 text-[11px]" onclick="event.stopPropagation()">
                            <span class="text-[10px] text-slate-400">Actions:</span>
                            <div class="flex items-center gap-2">
                                <button type="button" onclick="openModal(${w.sr})" aria-label="Open report folder for ${safeName}" class="w-11 h-11 inline-flex items-center justify-center rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 transition active:scale-95 cursor-pointer" title="Report details">
                                    <i data-lucide="folder" class="w-4 h-4 text-blue-600 dark:text-blue-400"></i>
                                </button>
                                ${liveUrl ? `
                                    <a href="${liveUrl}" target="_blank" rel="noopener noreferrer" aria-label="Launch web simulation for ${safeName}" class="w-11 h-11 inline-flex items-center justify-center rounded-xl ${isStandaloneSim ? 'bg-emerald-600 hover:bg-emerald-500 text-white' : 'bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700'} shadow-2xs transition active:scale-95 cursor-pointer" title="${isStandaloneSim ? `Run live simulation for ${safeName}` : `View code on GitHub for ${safeName}`}">
                                        <i data-lucide="${isStandaloneSim ? 'external-link' : 'github'}" class="w-4 h-4"></i>
                                    </a>
                                ` : `
                                    <button disabled aria-label="No web link" class="w-11 h-11 inline-flex items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-800/40 text-slate-300 dark:text-slate-600 border border-slate-200/60 dark:border-slate-800 cursor-not-allowed">
                                        <i data-lucide="external-link" class="w-4 h-4 opacity-40"></i>
                                    </button>
                                `}
                            </div>
                        </div>
                    </div>
                    `;
            }).join('');
            }

            tbody.innerHTML = items.map(w => {
                const liveUrl = getLiveSimulationUrl(w);
                const isStandaloneSim = Boolean(w.live_html);
        const safeName = (w.name || '').replace(/"/g, '&quot;');
        const isQa = !!w.in_qa;
        const isGit = !!w.has_file;
        const isXl = !w.is_extra;
        const ownerInfo = getOwnerDetails(w.owner);

        const qaBadge = isQa
        ? `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"><i data-lucide="check" class="w-3.5 h-3.5 stroke-[2.5]"></i> Present</span>`
        : `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-600 text-white shadow-2xs"><i data-lucide="x" class="w-3.5 h-3.5 stroke-[2.5]"></i> Missing</span>`;

        const gitBadge = isGit
        ? `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"><i data-lucide="check" class="w-3.5 h-3.5 stroke-[2.5]"></i> Present</span>`
        : `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-600 text-white shadow-2xs"><i data-lucide="x" class="w-3.5 h-3.5 stroke-[2.5]"></i> Missing</span>`;

        const xlBadge = isXl
        ? `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"><i data-lucide="check" class="w-3.5 h-3.5 stroke-[2.5]"></i> Present</span>`
        : `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-600 text-white shadow-2xs"><i data-lucide="x" class="w-3.5 h-3.5 stroke-[2.5]"></i> Missing</span>`;

        return `
        <tr onclick="openModal(${w.sr})" class="hover:bg-slate-100/70 dark:hover:bg-slate-800/50 cursor-pointer transition">
            <td class="py-3 px-3 text-center font-mono text-slate-400 font-semibold">${w.sr}</td>
            <td class="py-3 px-4">
                <div class="font-semibold text-xs text-slate-900 dark:text-white leading-snug">${w.name}</div>
                <div class="flex items-center gap-1.5 mt-1 text-[10px] text-slate-500">
                    ${w.is_extra ? `
                                <span class="px-1.5 py-0.2 rounded font-mono text-[9px] font-semibold bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20 uppercase">EXTRA</span>
                            ` : (w.wg_code && w.wg_code !== '-' ? `
                                <span class="px-1.5 py-0.2 rounded font-mono text-[10px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700">${w.wg_code}</span>
                            ` : '')}
                    <span>${w.is_extra ? 'Uncataloged Asset' : w.subject}</span>
                    ${w.in_qa ? `<span class="text-slate-400 font-mono text-[9px]">(${w.qa_tool_uid})</span>` : ''}
                </div>
            </td>
            <td class="py-3 px-3">
                <div class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg border ${ownerInfo.badge} text-[11px] font-semibold" title="Assigned Owner: ${w.owner || 'Unassigned'}">
                    <span class="w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold text-white ${ownerInfo.bg} shrink-0 shadow-2xs">${ownerInfo.initials}</span>
                    <span class="truncate max-w-[95px]">${ownerInfo.name}</span>
                </div>
            </td>
            <td class="py-3 px-3 text-center ${!isQa ? 'bg-rose-50/80 dark:bg-rose-950/25' : ''}">
                ${qaBadge}
            </td>
            <td class="py-3 px-3 text-center ${!isGit ? 'bg-rose-50/80 dark:bg-rose-950/25' : ''}">
                ${gitBadge}
            </td>
            <td class="py-3 px-3 text-center ${!isXl ? 'bg-rose-50/80 dark:bg-rose-950/25' : ''}">
                ${xlBadge}
            </td>
            <td class="py-3 px-3 text-center">
                <button type="button" onclick="event.stopPropagation(); openModal(${w.sr})" aria-label="Open report folder for ${safeName}" class="w-11 h-11 inline-flex items-center justify-center rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 transition active:scale-95 cursor-pointer shadow-2xs" title="Open report details for ${safeName}">
                    <i data-lucide="folder" class="w-4 h-4 text-blue-600 dark:text-blue-400"></i>
                </button>
            </td>
            <td class="py-3 px-3 text-center">
                ${liveUrl ? `
                            <a href="${liveUrl}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()" aria-label="Launch web link for ${safeName}" class="w-11 h-11 inline-flex items-center justify-center rounded-xl ${isStandaloneSim ? 'bg-emerald-600 hover:bg-emerald-500 text-white' : 'bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700'} shadow-2xs transition active:scale-95 cursor-pointer" title="${isStandaloneSim ? `Launch web simulation for ${safeName}` : `View source on GitHub for ${safeName}`}">
                                <i data-lucide="${isStandaloneSim ? 'external-link' : 'github'}" class="w-4 h-4"></i>
                            </a>
                        ` : `
                            <button disabled aria-label="No web link available for ${safeName}" class="w-11 h-11 inline-flex items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-800/40 text-slate-300 dark:text-slate-600 border border-slate-200/60 dark:border-slate-800 cursor-not-allowed" title="No web link">
                                <i data-lucide="external-link" class="w-4 h-4 opacity-40"></i>
                            </button>
                        `}
            </td>
        </tr>
        `;
            }).join('');

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
        const modalOwnerEl = document.getElementById('modalOwner');
        if (modalOwnerEl) {
            const ownerInfo = getOwnerDetails(w.owner);
            modalOwnerEl.innerHTML = `<span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md border ${ownerInfo.badge} text-[11px] font-semibold mt-1">
                <span class="w-4 h-4 rounded-sm flex items-center justify-center text-[9px] font-bold text-white ${ownerInfo.bg}">${ownerInfo.initials}</span>
                <span>Owner: ${ownerInfo.name}</span>
            </span>`;
        }
        document.getElementById('modalBadge').innerHTML = getStatusBadge(w.status_category, w.status_label, w);
        document.getElementById('modalExplanation').innerText = w.plain_explanation;
        document.getElementById('modalChecked').innerText = w.what_was_checked;
        document.getElementById('modalAction').innerText = w.what_needs_to_be_done;

        // Action Plan
        const actPriorityEl = document.getElementById('modalActionPriority');
        const actJustEl = document.getElementById('modalActionJustification');
        if (actPriorityEl && actJustEl) {
            actPriorityEl.innerText = (w.action_priority || 'LOW') + ' PRIORITY';
        actJustEl.innerText = w.action_justification || 'No immediate action required.';
            }

        // QA Information in modal
        const qaSection = document.getElementById('modalQaSection');
        if (qaSection) {
                if (w.in_qa) {
            qaSection.className = 'p-3 rounded-lg border bg-emerald-500/10 border-emerald-500/20 space-y-1.5 text-xs';
        qaSection.innerHTML = `
        <div class="flex items-center justify-between font-semibold text-emerald-700 dark:text-emerald-400">
            <span class="flex items-center gap-1.5"><i data-lucide="check-check" class="w-3.5 h-3.5"></i> QA Registered Tool Profile</span>
            <span class="font-mono text-[10px] bg-emerald-600/15 px-2 py-0.5 rounded">GOLD QA</span>
        </div>
        <div class="font-mono text-[11px] text-slate-700 dark:text-slate-300 break-all select-all flex items-center justify-between">
            <span>${w.qa_tool_uid}</span>
            <button onclick="navigator.clipboard.writeText('${w.qa_tool_uid}'); showToast('Tool UID copied', 'success')" class="text-blue-600 dark:text-blue-400 hover:underline shrink-0 text-[10px]">Copy</button>
        </div>
        <div class="text-[10px] text-slate-500 dark:text-slate-400 flex items-center gap-3">
            <span>Strand: <strong>${w.qa_strand || w.subject}</strong></span>
            <span>Target: <strong>${w.qa_launch_page || 'index.html'}</strong></span>
            <span>Dimensions: <strong>${w.qa_dimensions || '800x600'}</strong></span>
        </div>
        `;
                } else if (w.has_file && !w.is_extra) {
            qaSection.className = 'p-3 rounded-lg border bg-amber-500/10 border-amber-500/20 space-y-1 text-xs';
        qaSection.innerHTML = `
        <div class="font-semibold text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
            <i data-lucide="alert-circle" class="w-3.5 h-3.5"></i>
            <span>Pending QA Tool Registration</span>
        </div>
        <p class="text-slate-600 dark:text-slate-400">Simulation exists on disk but is not yet ingested into Gold QA Catalog. Test metadata profile required.</p>
        `;
                } else {
            qaSection.className = 'hidden';
                }
            }

        document.getElementById('modalPath').innerText = w.repo_path || 'No local repository file';

        const liveUrl = getLiveSimulationUrl(w);
        const isStandaloneSim = Boolean(w.live_html);
        const btnContainer = document.getElementById('modalRunBtnContainer');
        if (liveUrl) {
            btnContainer.innerHTML = `
                    ${isStandaloneSim ? `
                        <a href="${liveUrl}" target="_blank" rel="noopener noreferrer" class="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs shadow-sm flex items-center gap-1.5 transition" title="Launch live simulation">
                            <i data-lucide="play" class="w-3.5 h-3.5 fill-current"></i>
                            <span>Run Simulation</span>
                            <i data-lucide="external-link" class="w-3 h-3"></i>
                        </a>
                    ` : ''}
                    ${w.repo_path ? `
                        <a href="https://github.com/tce-widgets/all-widgets-v1/blob/main/${(w.repo_path || '').startsWith('/') ? (w.repo_path || '').slice(1) : (w.repo_path || '')}" target="_blank" rel="noopener noreferrer" class="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium text-xs shadow-xs flex items-center gap-1.5 transition" title="View repository source on GitHub">
                            <i data-lucide="github" class="w-3.5 h-3.5"></i>
                            <span>View on GitHub</span>
                        </a>
                    ` : ''}
                `;
            } else {
            btnContainer.innerHTML = '';
            }

        document.getElementById('widgetModal').classList.remove('hidden');
        lucide.createIcons();
        }

        function closeModal() {
            document.getElementById('widgetModal').classList.add('hidden');
        }

        // Status Briefing Modal
        function openStatusReportModal() {
            const counts = getCategoryCounts();
        const modal = document.getElementById('statusReportModal');
        const content = document.getElementById('statusReportTextContent');
        if (!modal || !content) return;

        content.innerHTML = `
        <div class="space-y-4">
            <div class="border-b pb-3">
                <h4 class="text-base font-bold text-slate-900 dark:text-white">Widget Ecosystem Status Briefing</h4>
                <div class="text-xs text-slate-500">Audit Date: ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })} • Status: Cross-Source Audit Complete</div>
            </div>

            <div class="space-y-1.5">
                <div class="font-bold text-xs uppercase text-blue-600 dark:text-blue-400 tracking-wider">1. Core Project Status Answers</div>
                <ul class="list-disc pl-5 space-y-1 text-xs">
                    <li><strong>Total Required Scope:</strong> 294 curriculum widgets required across 15 subject strands.</li>
                    <li><strong>Development Progress:</strong> 273 / 294 (92.9%) curriculum widgets developed on disk (+46 uncataloged simulations = 319 runnable assets).</li>
                    <li><strong>QA Readiness:</strong> 258 / 294 (87.8%) curriculum widgets matched and verified in Gold QA Catalog (273 total QA tools).</li>
                    <li><strong>Major Gaps:</strong> 12 simulations in active dev backlog (Biology 3, Math 3, Geography 2, Chemistry 1, Science 1, English 1, Geometry 1).</li>
                    <li><strong>QA Gap:</strong> 15 finished widgets on disk need ingestion into the QA catalog to reach 92.9% production readiness.</li>
                </ul>
            </div>

            <div class="space-y-1.5">
                <div class="font-bold text-xs uppercase text-teal-600 dark:text-teal-400 tracking-wider">2. Widget Status Breakdown</div>
                <div class="grid grid-cols-2 gap-2 text-xs font-mono">
                    <div class="p-2 bg-slate-100 dark:bg-slate-800 rounded">Matched in All 3: <strong>${counts.matched_all} (87.8%)</strong></div>
                    <div class="p-2 bg-slate-100 dark:bg-slate-800 rounded">Missing from QA: <strong>${counts.missing_qa} (5.1%)</strong></div>
                    <div class="p-2 bg-slate-100 dark:bg-slate-800 rounded">Needs Development: <strong>${counts.pending_dev} (4.1%)</strong></div>
                    <div class="p-2 bg-slate-100 dark:bg-slate-800 rounded">Extra in Repo: <strong>+${counts.extra_repo} Assets</strong></div>
                    <div class="p-2 bg-slate-100 dark:bg-slate-800 rounded">Whiteboard Tools: <strong>${counts.whiteboard} Canvas</strong></div>
                    <div class="p-2 bg-slate-100 dark:bg-slate-800 rounded">Naming Issues: <strong>${counts.naming_issues} Mappings</strong></div>
                </div>
            </div>

            <div class="space-y-1.5">
                <div class="font-bold text-xs uppercase text-rose-600 dark:text-rose-400 tracking-wider">3. Critical Business Risks & Recommendations</div>
                <p class="text-xs"><strong>Engineering Staffing (High):</strong> Dedicate 2 senior frontend engineers to a 3-week sprint on the 12 backlog simulations to unlock full syllabus completion.</p>
                <p class="text-xs"><strong>QA Pipeline Throughput (Medium):</strong> Ingest the 15 finished widgets into QA within 5 business days to immediately elevate production readiness to 92.9%.</p>
                <p class="text-xs"><strong>Content Monetization (Medium):</strong> Academic curriculum committee to evaluate and adopt the 46 uncataloged simulations into the syllabus.</p>
            </div>
        </div>
        `;

        modal.classList.remove('hidden');
        lucide.createIcons();
        }

        function closeStatusReportModal() {
            const modal = document.getElementById('statusReportModal');
        if (modal) modal.classList.add('hidden');
        }

        function copyStatusReport() {
            const counts = getCategoryCounts();
        const text = `WIDGET COMPARISON & STATUS BRIEFING REPORT
==============================================================
Date: ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
Status: All Sources Verified & Checked

1. FIVE CORE QUESTIONS ANSWERED:
- Total Expected Widgets: 294
- Codebase Development Complete: 273 (92.9%) [+46 Extra = 319 Runnable Assets]
- QA Validated Widgets: 258 (87.8%) [273 Registered QA Profiles]
- Net-New Development Backlog: 12 Widgets (Biology 3, Math 3, Geography 2, Chem 1, Sci 1, Eng 1, Geom 1)
- QA Ingestion Gap: 15 Developed Widgets Missing from QA

2. 3-WAY SOURCE COMPARISON SUMMARY:
- Matched in All 3 Sources (Excel ∩ Repo ∩ QA): 258
- Extra Standalone Simulations in Repo: +46
- Present in Excel but Missing from Repo: 21 (12 Dev + 9 Canvas Tools)
- Present in Excel & Repo but Missing in QA: 15
- Naming Differences Resolved: 7
- Duplicate Rows in Master Excel: 2 (#25, #257)
- Records Needing Review: 6

3. RECOMMENDED MANAGEMENT ACTIONS:
- High Priority: Staff 3-week sprint with 2 frontend devs for 12 backlog simulations.
- Medium Priority: QA Lead to ingest 15 finished widgets within 5 business days.
- Medium Priority: Curriculum Head to adopt 46 bonus simulations into syllabus.
- Medium Priority: Clean 2 duplicate rows and 4 flag issues in master sheet.
- Low Priority: Reclassify 9 whiteboard tools to Platform Infrastructure.
`;
            navigator.clipboard.writeText(text);
            showToast('Status briefing copied to clipboard!', 'success');
        }

        function exportCSV() {
            if (!filteredData || filteredData.length === 0) {
                showToast('No data to export', 'error');
                return;
            }
            const headers = ['Sr', 'Batch/WG Code', 'Widget Name', 'Subject', 'Excel Status', 'Codebase Status', 'QA Verified', 'Action Required', 'Action Priority', 'Repo Path'];
            const rows = filteredData.map(w => [
                w.sr,
                `"${w.wg_code || ''}"`,
                `"${(w.name || '').replace(/"/g, '""')}"`,
                `"${w.subject || ''}"`,
                `"${w.excel_status_label || ''}"`,
                `"${w.status_label || ''}"`,
                w.in_qa ? 'Yes' : 'No',
                `"${(w.action_type || '').replace(/"/g, '""')}"`,
                `"${w.action_priority || ''}"`,
                `"${w.repo_path || ''}"`
            ]);

            const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\\n');
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement('a');
            link.setAttribute('href', encodedUri);
            link.setAttribute('download', `Widget_Comparison_Status_${new Date().toISOString().slice(0, 10)}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            showToast('CSV exported successfully!', 'success');
        }

        // ==========================================
        // SINGLE OVERVIEW DIAGRAM: WIDGET STATUS BREAKDOWN
        // ==========================================
        let reconciliationChartInstance = null;

        function updateChartsTheme() {
            if (typeof Chart === 'undefined') return;
            const isDark = document.documentElement.classList.contains('dark');

            if (reconciliationChartInstance) {
                if (reconciliationChartInstance.data.datasets[0]) {
                    reconciliationChartInstance.data.datasets[0].borderColor = isDark ? '#1e293b' : '#ffffff';
                }
                reconciliationChartInstance.update();
            }
        }

        function initOverviewCharts() {
            const donutCanvas = document.getElementById('reconciliationDonutChart');
            if (!donutCanvas || typeof Chart === 'undefined') return;

            const isDark = document.documentElement.classList.contains('dark');
            if (reconciliationChartInstance) reconciliationChartInstance.destroy();

            // Single Diagram: Widget Status Breakdown (4 clean, exact categories)
            const counts = getCategoryCounts();
            const matchedAll = counts.matched_all || 258;
            const missingQa = counts.missing_qa || 15;
            const missingGit = (counts.pending_dev || 12) + (counts.whiteboard || 9); // 21 total missing in git
            const extraRepo = counts.extra_repo || 46;

            const donutLabels = [
                'Matched in All 3 (258)',
                'Missing in QA (15)',
                'Missing in Git (21)',
                'Extra in Repo (+46)'
            ];
            const donutData = [
                matchedAll,
                missingQa,
                missingGit,
                extraRepo
            ];
            const donutColors = [
                '#10b981', // Emerald
                '#f59e0b', // Amber
                '#f43f5e', // Rose
                '#a855f7'  // Purple
            ];
            const donutFilterKeys = [
                'matched_all',
                'missing_qa',
                'needs_attention',
                'extra_repo'
            ];

            reconciliationChartInstance = new Chart(donutCanvas, {
                type: 'doughnut',
                data: {
                    labels: donutLabels,
                    datasets: [{
                        data: donutData,
                        backgroundColor: donutColors,
                        borderWidth: 2,
                        borderColor: isDark ? '#1e293b' : '#ffffff',
                        hoverOffset: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '68%',
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.95)',
                            titleColor: isDark ? '#ffffff' : '#0f172a',
                            bodyColor: isDark ? '#cbd5e1' : '#334155',
                            borderColor: isDark ? '#334155' : '#cbd5e1',
                            borderWidth: 1,
                            padding: 10,
                            callbacks: {
                                label: function(context) {
                                    const val = context.raw;
                                    const total = donutData.reduce((a, b) => a + b, 0);
                                    const pct = ((val / total) * 100).toFixed(1);
                                    return ` ${context.label}: ${val} (${pct}%)`;
                                },
                                afterLabel: function() {
                                    return 'Click slice to filter in All Widgets';
                                }
                            }
                        }
                    },
                    onClick: (evt, elements) => {
                        if (elements && elements.length > 0) {
                            const idx = elements[0].index;
                            const statusKey = donutFilterKeys[idx];
                            drillDown(statusKey);
                        }
                    },
                    onHover: (evt, elements) => {
                        evt.native.target.style.cursor = (elements && elements.length > 0) ? 'pointer' : 'default';
                    }
                }
            });
        }

        // Window Drag & Drop Listeners
        window.addEventListener('dragover', (e) => {
            e.preventDefault();
            const overlay = document.getElementById('dropOverlay');
            if (overlay) overlay.classList.remove('hidden');
        });

        window.addEventListener('dragleave', (e) => {
            if (e.relatedTarget === null) {
                const overlay = document.getElementById('dropOverlay');
                if (overlay) overlay.classList.add('hidden');
            }
        });

        window.addEventListener('drop', (e) => {
            e.preventDefault();
            const overlay = document.getElementById('dropOverlay');
            if (overlay) overlay.classList.add('hidden');
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                processExcelFile(e.dataTransfer.files[0]);
            }
        });

        let toastTimeout = null;

        function showToast(msg, type = 'info') {
            const toast = document.getElementById('toastNotification');
            const icon = document.getElementById('toastIcon');
            const title = document.getElementById('toastTitle');
            const body = document.getElementById('toastMsg');

            if (!toast || !icon || !title || !body) return;

            if (type === 'success') {
                icon.className = 'w-8 h-8 rounded-xl bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0';
                icon.innerHTML = '<i data-lucide="check" class="w-4 h-4"></i>';
                title.innerText = 'Success';
            } else if (type === 'error') {
                icon.className = 'w-8 h-8 rounded-xl bg-rose-500/15 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0';
                icon.innerHTML = '<i data-lucide="alert-triangle" class="w-4 h-4"></i>';
                title.innerText = 'Error';
            } else {
                icon.className = 'w-8 h-8 rounded-xl bg-blue-500/15 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0';
                icon.innerHTML = '<i data-lucide="info" class="w-4 h-4"></i>';
                title.innerText = 'Notice';
            }

            body.innerText = msg;
            toast.classList.remove('-translate-y-20', 'opacity-0', 'pointer-events-none');
            toast.classList.add('translate-y-0', 'opacity-100', 'pointer-events-auto');
            lucide.createIcons();

            if (toastTimeout) clearTimeout(toastTimeout);
            toastTimeout = setTimeout(() => {
                hideToast();
            }, 4500);
        }

        function hideToast() {
            const toast = document.getElementById('toastNotification');
            if (toast) {
                toast.classList.remove('translate-y-0', 'opacity-100', 'pointer-events-auto');
                toast.classList.add('-translate-y-20', 'opacity-0', 'pointer-events-none');
            }
        }

        // Initialize UI, Theme, Profile, Filter & Charts
        initTheme();
        initUserProfile();
        filterWidgets();
        initOverviewCharts();

        // Warm up users table & stats for admin on load so data is instantly ready
        if (currentUser && currentUser.role === 'admin') {
            renderUsersTable();
        }

        // Restore active tab across page refresh / reload
        try {
            const hashTab = (window.location.hash || '').replace('#', '').trim();
            const savedTab = sessionStorage.getItem('active_dashboard_tab');
            const candidateTab = hashTab || savedTab;
            if (candidateTab && ['overview', 'inventory', 'users', 'activity'].includes(candidateTab)) {
                if (candidateTab !== 'overview') {
                    switchTab(candidateTab);
                }
            }
        } catch {}

        lucide.createIcons();

        if (window.location.protocol === 'file:') {
            const b = document.getElementById('localFileBanner');
            if (b) b.classList.remove('hidden');
        }

        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeModal();
                closeStatusReportModal();
                hideToast();
            } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                switchTab('inventory');
                const search = document.getElementById('widgetSearch');
                if (search) {
                    search.focus();
                    search.select();
                }
            } else if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
                e.preventDefault();
                switchTab('inventory');
                const search = document.getElementById('widgetSearch');
                if (search) {
                    search.focus();
                    search.select();
                }
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
        .replace('{total_git_assets}', str(present_both_count + extra_repo_count))
        .replace('{total_repo_assets}', str(total_repo_assets))
        .replace('{total_repo_physical_count}', str(total_repo_physical_count))
        .replace('{angular_comp_count}', str(angular_comp_count))
        .replace('{extra_repo_count}', str(extra_repo_count))
        .replace('{need_attention_count}', str(need_attention_count))
        .replace('{need_attention_pct}', need_attention_pct)
        .replace('{qa_present_count}', str(qa_present_count))
        .replace('{git_present_count}', str(git_present_count))
        .replace('{xl_present_count}', str(xl_present_count))
        .replace('{present_both_count}', str(present_both_count))
        .replace('{missing_repo_count}', str(missing_repo_count))
        .replace('{missing_repo_pct}', missing_repo_pct)
        .replace('{dev_coverage_pct}', dev_coverage_pct)
        .replace('{qa_coverage_pct}', qa_coverage_pct)
        .replace('{matched_all_count}', str(matched_all_count))
        .replace('{matched_all_pct}', matched_all_pct)
        .replace('{missing_qa_count}', str(missing_qa_count))
        .replace('{missing_qa_pct}', missing_qa_pct)
        .replace('{pending_dev_count}', str(pending_dev_count))
        .replace('{pending_dev_pct}', pending_dev_pct)
        .replace('{whiteboard_count}', str(whiteboard_count))
        .replace('{whiteboard_pct}', whiteboard_pct)
        .replace('{naming_issue_count}', str(naming_issue_count))
        .replace('{duplicate_count}', str(duplicate_count))
        .replace('{investigation_count}', str(investigation_count))
        .replace('{total_runnable_assets}', str(total_runnable_assets))
        .replace('{subject_count}', str(len(subj_stats)))
        .replace('{subject_performance_table_html}', subject_performance_table_html)
        .replace('{subject_cards_html}', subject_cards_html)
        .replace('{extra_in_repo_json}', extra_in_repo_json)
        .replace('{commit_badge}', commit_badge)
        .replace('{repo_found_count}', str(repo_found_count))
        .replace('{repo_not_found_count}', str(repo_not_found_count))
        .replace('{repeated_count}', str(repeated_count))
        .replace('{not_found_count}', str(not_found_count))
        .replace('{total_count}', str(total_count))
        .replace('{total_assets_count}', str(total_assets_count))
        .replace('{qa_tool_count}', str(qa_tool_count))
        .replace('{qa_verified_count}', str(qa_verified_count))
        .replace('{qa_html_count}', str(qa_html_count))
        .replace('{qa_angular_count}', str(qa_angular_count))
        .replace('__SUBJECT_OPTIONS__', subject_options)
        .replace('__OWNER_OPTIONS__', owner_options)
        .replace('__DATA_JSON__', json.dumps(unified_list, indent=2))
        .replace('__QA_DATA_JSON__', qa_tools_json)
        .replace('__QA_STRAND_OPTIONS__', qa_strand_options)
        .replace('__REPO_CATALOG_JSON__', json.dumps(repo_catalog, indent=2))
    )

    index_path = 'index.html'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(rendered_html)

    print(f"Successfully generated CEO Executive Dashboard in {index_path}!")
    print(f"Saved standalone repository catalog in {catalog_path}!")

if __name__ == '__main__':
    generate()
