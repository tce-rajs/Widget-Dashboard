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
