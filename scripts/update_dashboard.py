#!/usr/bin/env python3
r"""
Update Dashboard Pipeline
=========================
One-step automated update script for the Widget Comparison Dashboard.

Features:
- Auto-detects new/updated Excel spreadsheets (in project root or Downloads folder)
- Reconciles 294+ widgets against repository source code and components
- Updates index.html, widget-comparison.html, and scripts/repo_catalog.json
- Automatically synchronizes files to D:\Projects\widget-dashboard
- Displays a clean visual report of counts, subjects, and verified source files
- Supports optional --push flag to commit and push changes directly to GitHub
"""

import os
import sys
import shutil
import subprocess
import time
from collections import Counter

# Base paths
PRIMARY_DIR = r"D:\Projects\all-widgets-v1"
STANDALONE_DIR = r"D:\Projects\widget-dashboard"
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

def find_latest_excel(specified_path=None):
    if specified_path:
        if os.path.exists(specified_path):
            return os.path.abspath(specified_path)
        print(f"[ERROR] Specified file not found: {specified_path}")
        sys.exit(1)

    candidates = []

    # Check primary directory
    if os.path.exists(PRIMARY_DIR):
        for f in os.listdir(PRIMARY_DIR):
            if f.endswith('.xlsx') and not f.startswith('~$'):
                fp = os.path.join(PRIMARY_DIR, f)
                candidates.append((os.path.getmtime(fp), fp, "Project Directory"))

    # Check standalone directory
    if os.path.exists(STANDALONE_DIR):
        for f in os.listdir(STANDALONE_DIR):
            if f.endswith('.xlsx') and not f.startswith('~$'):
                fp = os.path.join(STANDALONE_DIR, f)
                candidates.append((os.path.getmtime(fp), fp, "Standalone Repo"))

    # Check Downloads folder for recently modified Widgets spreadsheets
    if os.path.exists(DOWNLOADS_DIR):
        for f in os.listdir(DOWNLOADS_DIR):
            if f.endswith('.xlsx') and 'widget' in f.lower() and not f.startswith('~$'):
                fp = os.path.join(DOWNLOADS_DIR, f)
                candidates.append((os.path.getmtime(fp), fp, "Downloads Folder"))

    if not candidates:
        print("[ERROR] No .xlsx spreadsheets found!")
        sys.exit(1)

    candidates.sort(key=lambda x: x[0], reverse=True)
    latest_mtime, latest_path, location = candidates[0]
    return latest_path

def run_pipeline(excel_file=None, auto_push=False):
    print("=" * 70)
    print("      WIDGET DASHBOARD AUTOMATED UPDATE PIPELINE")
    print("=" * 70)

    # 1. Identify Target Excel
    target_excel = find_latest_excel(excel_file)
    excel_name = os.path.basename(target_excel)
    print(f"\n[1/5] Using reference spreadsheet:")
    print(f"      Path: {target_excel}")
    print(f"      Modified: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(target_excel)))}")

    # Ensure target_excel is in PRIMARY_DIR with standard name
    dest_excel_primary = os.path.join(PRIMARY_DIR, "Widgets in CE Platinum cum Crystal.xlsx")
    if os.path.abspath(target_excel) != os.path.abspath(dest_excel_primary):
        print(f"      Syncing reference copy to: {dest_excel_primary}")
        shutil.copy2(target_excel, dest_excel_primary)

    # 2. Run Comparison Generator
    print(f"\n[2/5] Regenerating dashboard and repository catalog...")
    scripts_dir = os.path.join(PRIMARY_DIR, "scripts")
    sys.path.insert(0, scripts_dir)
    from generate_comparison_page import generate

    os.chdir(PRIMARY_DIR)
    generate()

    # 3. Synchronize widget-comparison.html
    print(f"\n[3/5] Synchronizing primary workspace...")
    index_html = os.path.join(PRIMARY_DIR, "index.html")
    comp_html = os.path.join(PRIMARY_DIR, "widget-comparison.html")
    shutil.copy2(index_html, comp_html)
    print(f"      Updated index.html & widget-comparison.html")

    # 4. Synchronize with Standalone Repository
    if os.path.exists(STANDALONE_DIR):
        print(f"\n[4/5] Synchronizing standalone repository ({STANDALONE_DIR})...")
        sync_files = [
            ("index.html", "index.html"),
            ("widget-comparison.html", "widget-comparison.html"),
            ("Widgets in CE Platinum cum Crystal.xlsx", "Widgets in CE Platinum cum Crystal.xlsx"),
            ("run_local_dashboard.bat", "run_local_dashboard.bat"),
            ("run_local_dashboard.ps1", "run_local_dashboard.ps1"),
            ("update_dashboard.bat", "update_dashboard.bat"),
            ("update_dashboard.ps1", "update_dashboard.ps1"),
            ("UPDATE_GUIDE.md", "UPDATE_GUIDE.md"),
            (os.path.join("scripts", "repo_catalog.json"), os.path.join("scripts", "repo_catalog.json")),
            (os.path.join("scripts", "generate_comparison_page.py"), os.path.join("scripts", "generate_comparison_page.py")),
            (os.path.join("scripts", "update_dashboard.py"), os.path.join("scripts", "update_dashboard.py")),
            (os.path.join("scripts", "watch_excel.py"), os.path.join("scripts", "watch_excel.py")),
        ]
        for src_rel, dst_rel in sync_files:
            src_full = os.path.join(PRIMARY_DIR, src_rel)
            dst_full = os.path.join(STANDALONE_DIR, dst_rel)
            if os.path.exists(src_full):
                os.makedirs(os.path.dirname(dst_full), exist_ok=True)
                shutil.copy2(src_full, dst_full)
        print("      Synchronized HTML, scripts, Excel, and catalog to standalone repo.")

    # 5. Read and Print Report
    print(f"\n[5/5] Verification & Summary Report:")
    import json
    import re
    with open(index_html, "r", encoding="utf-8") as f:
        html_content = f.read()

    m = re.search(r'let rawData = (\[.*?\]);\s*\n', html_content, re.DOTALL)
    if m:
        unique_widgets = json.loads(m.group(1))
    else:
        unique_widgets = []

    total_w = len(unique_widgets)
    statuses = Counter(w.get("status_category") for w in unique_widgets)
    excel_st = Counter(w.get("excel_status") for w in unique_widgets)
    present_on_disk = sum(1 for w in unique_widgets if w.get("has_file"))
    live_sims = sum(1 for w in unique_widgets if w.get("live_html"))

    print("-" * 65)
    print("  1. EXCEL REFERENCE ANALYSIS (Spreadsheet Ground Truth):")
    print(f"     Total Widgets in Sheet: {total_w}")
    print(f"     Repo Found in Excel   : {excel_st.get('repo_found', 0)} ({(excel_st.get('repo_found', 0)/total_w)*100:.1f}%)")
    print(f"     Repo Not Found ('No') : {excel_st.get('repo_not_found', 0)} ({(excel_st.get('repo_not_found', 0)/total_w)*100:.1f}%)")
    print(f"     Repeated in Sheet     : {excel_st.get('repeated', 0)}")
    print(f"     Widget Not Found      : {excel_st.get('not_found', 0)}")
    print("-" * 65)
    print("  2. CODEBASE AUDIT ANALYSIS (Repository Ground Truth):")
    print(f"     Verified Files on Disk: {present_on_disk} ({(present_on_disk/total_w)*100:.1f}%)")
    print(f"     Already Available     : {statuses.get('available', 0)}")
    print(f"     Found via Mapping     : {statuses.get('corrected', 0)}")
    print(f"     Small Changes Needed  : {statuses.get('minor_changes', 0)}")
    print(f"     Classroom Tools       : {statuses.get('whiteboard', 0)}")
    print(f"     Needs Development     : {statuses.get('requires_dev', 0)}")
    print(f"     Live HTML Simulations : {live_sims}")
    print("-" * 65)

    # Optional Git Push
    if auto_push:
        push_to_github()
    else:
        print("\nAll files successfully updated and verified locally!")
        print("To push to GitHub:")
        print("  - Run with --push flag:  python scripts/update_dashboard.py --push")
        print("  - Or commit and push in D:\\Projects\\widget-dashboard")

def push_to_github():
    print("\n[GIT] Preparing to commit and push to GitHub...")
    if not os.path.exists(STANDALONE_DIR):
        print("[GIT ERROR] Standalone directory does not exist.")
        return

    os.chdir(STANDALONE_DIR)
    try:
        subprocess.run(["git", "add", "."], check=True)
        status = subprocess.check_output(["git", "status", "--porcelain"]).decode().strip()
        if not status:
            print("[GIT] No changes to commit. Everything is up to date.")
            return

        commit_msg = f"Update dashboard with latest Excel reference data ({time.strftime('%Y-%m-%d')})"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print(f"[GIT] Created commit: {commit_msg}")
        print("[GIT] Pushing to origin main...")
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("[GIT SUCCESS] Pushed updates to GitHub!")
    except Exception as e:
        print(f"[GIT ERROR] Failed to push: {e}")

if __name__ == "__main__":
    specified = None
    push_flag = False

    for arg in sys.argv[1:]:
        if arg in ("--push", "-p"):
            push_flag = True
        elif arg.endswith((".xlsx", ".xls")):
            specified = arg

    run_pipeline(specified, push_flag)
