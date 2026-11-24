import json
import re
from collections import Counter, defaultdict

with open('index.html', 'r', encoding='utf-8') as f:
    c = f.read()

m = re.search(r'let rawData = (\[.*?\]);', c, re.DOTALL)
raw_data = json.loads(m.group(1))

m_qa = re.search(r'let rawQaData = (\[.*?\]);', c, re.DOTALL)
raw_qa = json.loads(m_qa.group(1))

excel_items = [x for x in raw_data if not x.get('is_extra')]
extra_items = [x for x in raw_data if x.get('is_extra')]

print(f"Total Expected Widgets (Excel): {len(excel_items)}")
print(f"Total Extra in Repo: {len(extra_items)}")
print(f"Total QA Registered Tools: {len(raw_qa)}")

# 1. Available in all 3 sources
in_all_three = [x for x in excel_items if x.get('has_file') and x.get('in_qa')]
print(f"\n1. In All 3 Sources (Excel ∩ Repo ∩ QA): {len(in_all_three)}")

# 2. Present in Repo but Missing in Excel
print(f"2. Present in Repo but Missing in Excel (Extra): {len(extra_items)}")

# 3. Present in Excel but Missing in Repo
missing_in_repo = [x for x in excel_items if not x.get('has_file')]
dev_backlog = [x for x in excel_items if x.get('status_category') == 'requires_dev']
whiteboard_canvas = [x for x in excel_items if x.get('status_category') == 'whiteboard']
print(f"3. Present in Excel but Missing in Repo: {len(missing_in_repo)} (Dev: {len(dev_backlog)}, Whiteboard: {len(whiteboard_canvas)})")

# 4. Present in Excel & Repo but Missing in QA
excel_repo_missing_qa = [x for x in excel_items if x.get('has_file') and not x.get('in_qa')]
print(f"4. Present in Excel & Repo but Missing in QA: {len(excel_repo_missing_qa)}")
for x in excel_repo_missing_qa:
    print(f"   - #{x['sr']}: {x['name']} ({x['subject']}) -> {x.get('repo_path')}")

# 5. Naming Inconsistencies / Alias Mapping
naming_issues = [x for x in excel_items if x.get('status_category') in ['corrected', 'minor_changes']]
print(f"\n5. Naming Inconsistencies across Sources: {len(naming_issues)}")
for x in naming_issues:
    print(f"   - #{x['sr']}: Excel Name='{x['name']}' | Repo Path='{x.get('repo_path')}' | Status={x['status_category']}")

# 6. Duplicates in Excel
repeated_items = [x for x in excel_items if x.get('excel_status') == 'repeated']
print(f"\n6. Duplicate / Repeated in Excel: {len(repeated_items)}")
for x in repeated_items:
    print(f"   - #{x['sr']}: '{x['name']}' ({x['subject']})")

# 7. Unmatched / Investigation Required
investigation_items = [x for x in excel_items if x.get('excel_status') in ['repeated', 'not_found'] or x.get('status_category') == 'minor_changes']
print(f"\n7. Investigation Required: {len(investigation_items)}")
for x in investigation_items:
    print(f"   - #{x['sr']}: '{x['name']}' ({x['subject']}) -> Reason: {x['excel_status']} / {x['status_category']}")

# Subject-Wise Analysis
print("\n--- SUBJECT-WISE BREAKDOWN ---")
subj_stats = defaultdict(lambda: {'expected': 0, 'developed': 0, 'qa_ready': 0, 'pending_dev': 0, 'whiteboard': 0, 'naming_diff': 0})
for x in excel_items:
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

print(f"{'Subject':<22} | {'Expected':<8} | {'Developed':<9} | {'QA Ready':<8} | {'Dev Gap':<7} | {'Canvas':<6} | {'Naming':<6} | {'Dev %':<6} | {'QA %':<6}")
print("-" * 95)
for s, d in sorted(subj_stats.items(), key=lambda i: -i[1]['expected']):
    dev_pct = (d['developed'] / d['expected']) * 100 if d['expected'] > 0 else 0
    qa_pct = (d['qa_ready'] / d['expected']) * 100 if d['expected'] > 0 else 0
    print(f"{s:<22} | {d['expected']:<8} | {d['developed']:<9} | {d['qa_ready']:<8} | {d['pending_dev']:<7} | {d['whiteboard']:<6} | {d['naming_diff']:<6} | {dev_pct:>5.1f}% | {qa_pct:>5.1f}%")
