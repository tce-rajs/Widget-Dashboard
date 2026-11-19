import os
import sys

scripts_dir = os.path.dirname(os.path.abspath(__file__))
tpl_dir = os.path.join(scripts_dir, 'templates_ceo')

with open(os.path.join(tpl_dir, '00_python_logic.py'), 'r', encoding='utf-8') as f:
    py_logic = f.read()

with open(os.path.join(tpl_dir, '01_head_header.html'), 'r', encoding='utf-8') as f:
    p1 = f.read()

with open(os.path.join(tpl_dir, '02_overview.html'), 'r', encoding='utf-8') as f:
    p2 = f.read()

with open(os.path.join(tpl_dir, '03_inventory_all_widgets.html'), 'r', encoding='utf-8') as f:
    p3 = f.read()

with open(os.path.join(tpl_dir, '04_docs_admin_modals.html'), 'r', encoding='utf-8') as f:
    p4 = f.read()

with open(os.path.join(tpl_dir, '05_scripts.js'), 'r', encoding='utf-8') as f:
    p5 = f.read()

full_html_template = p1 + "\n" + p2 + "\n" + p3 + "\n" + p4 + "\n" + p5

py_footer = '''
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
'''

final_generator_code = py_logic + '\n\n    html_template = """' + full_html_template + '"""\n\n' + py_footer

target_path = os.path.join(scripts_dir, 'generate_comparison_page.py')
with open(target_path, 'w', encoding='utf-8') as f:
    f.write(final_generator_code)

print(f"Compiled CEO Executive Dashboard generator into {target_path} successfully ({len(final_generator_code)} bytes).")
