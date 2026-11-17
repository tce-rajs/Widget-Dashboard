#!/usr/bin/env python3
"""
Excel Auto-Watcher for Widget Dashboard
=======================================
Continuously watches for modifications in Excel spreadsheets (.xlsx).
Whenever an Excel file is edited or saved, it automatically triggers
the complete update pipeline and keeps both local workspaces synchronized.
"""

import time
import os
import sys

# Ensure scripts directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from update_dashboard import run_pipeline

PRIMARY_DIR = r"D:\Projects\all-widgets-v1"

def watch():
    print("=" * 70)
    print("      EXCEL CONTINUOUS AUTO-WATCHER FOR WIDGET DASHBOARD")
    print("=" * 70)
    print(f"Monitoring directory: {PRIMARY_DIR}")
    print("Whenever you save or update an Excel file (.xlsx), this script will:")
    print("  1. Re-read the Excel file and map all widget rows")
    print("  2. Verify all 294+ widgets and source files on disk")
    print("  3. Rebuild index.html and widget-comparison.html")
    print("  4. Synchronize standalone repository (D:\\Projects\\widget-dashboard)")
    print("\nPress Ctrl+C to stop.")
    print("=" * 70 + "\n")

    last_mtimes = {}

    # Initialize mtimes
    for fname in os.listdir(PRIMARY_DIR):
        if fname.endswith('.xlsx') and not fname.startswith('~$'):
            fp = os.path.join(PRIMARY_DIR, fname)
            try:
                last_mtimes[fname] = os.path.getmtime(fp)
            except OSError:
                pass

    while True:
        try:
            changed_file = None
            for fname in os.listdir(PRIMARY_DIR):
                if fname.endswith('.xlsx') and not fname.startswith('~$'):
                    fp = os.path.join(PRIMARY_DIR, fname)
                    try:
                        mtime = os.path.getmtime(fp)
                        if fname not in last_mtimes:
                            last_mtimes[fname] = mtime
                            changed_file = fp
                        elif mtime > last_mtimes[fname]:
                            last_mtimes[fname] = mtime
                            changed_file = fp
                    except OSError:
                        continue

            if changed_file:
                now = time.strftime('%H:%M:%S')
                print(f"\n[{now}] Detected change in '{os.path.basename(changed_file)}'!")
                # Brief sleep to allow Excel file write lock to release
                time.sleep(0.7)
                run_pipeline(changed_file, auto_push=False)
                print(f"[{now}] Dashboard regenerated & synchronized successfully.\n")

            time.sleep(1)
        except KeyboardInterrupt:
            print("\nAuto-watcher stopped.")
            break
        except Exception as e:
            print(f"[Watcher Error]: {e}")
            time.sleep(2)

if __name__ == '__main__':
    watch()
