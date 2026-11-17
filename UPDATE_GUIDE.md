# Widget Dashboard Update Guide

This guide explains how to easily update the **Widget Comparison Dashboard** whenever a new or updated Excel spreadsheet is provided.

---

## 4 Easy Ways to Update

### Method 1: Double-Click `update_dashboard.bat` (Easiest)
* **What to do**:
  1. Simply double-click **`update_dashboard.bat`** in the project folder.
  2. The script will automatically locate the latest Excel spreadsheet, reconcile all 294+ widgets against repository source files, and update both workspaces.
  3. At the end, it will display a clean summary report and ask if you want to push the updates to GitHub (`y/N`).
* **Drag-and-Drop bonus**: You can also drag and drop any `.xlsx` file directly on top of `update_dashboard.bat` in Windows Explorer!

---

### Method 2: In-Browser Live Drag-and-Drop (Instant Preview)
* **What to do**:
  1. Open the dashboard in your browser (`http://localhost:8000/` or `index.html`).
  2. Drag and drop your `.xlsx` spreadsheet anywhere onto the dashboard page (or click the **"Update Excel"** / **"Sync Excel"** button in the header).
  3. The dashboard reconciles all rows client-side in less than 1 second, updating all stat cards, progress bars, and table rows dynamically.

---

### Method 3: Command Line / PowerShell
* **PowerShell**:
  ```powershell
  # Automatic detection of latest spreadsheet
  .\update_dashboard.ps1

  # With specific spreadsheet path
  .\update_dashboard.ps1 -File "C:\path\to\Widgets_Updated.xlsx"

  # Automatic push to GitHub
  .\update_dashboard.ps1 -Push
  ```
* **Python**:
  ```bash
  # Standard update
  python scripts/update_dashboard.py

  # With specific spreadsheet path
  python scripts/update_dashboard.py "C:\path\to\Widgets_Updated.xlsx"

  # With direct GitHub push
  python scripts/update_dashboard.py --push
  ```

---

### Method 4: Continuous Auto-Watcher (For Live Excel Editing)
If you or your team are actively making edits inside Microsoft Excel and want the dashboard to update immediately upon saving:
```bash
python scripts/watch_excel.py
```
* Monitors the folder for changes to `.xlsx` files.
* Every time you press **Save** in Excel, the script detects the change, rebuilds the dashboard, and refreshes the repository catalog.

---

## What the Pipeline Does Automatically

Whenever the update script runs, it performs the following steps:
1. **Spreadsheet Discovery**: Finds the newest `.xlsx` file (in project root or your `Downloads` folder) and copies it to `Widgets in CE Platinum cum Crystal.xlsx`.
2. **Reconciliation & Code Mapping**:
   - Parses all 294 widget rows and preserves exact Excel order and subjects.
   - Maps naming typos (e.g. *Operation Domino*, *India's Constitution*, *Commutative Property*).
   - Maps Angular components (e.g. *Biology Microscope* vs *Physics Virtual Microscope*).
   - Checks the disk for executable entry points (`index.html` or `.component.html`).
3. **HTML & Catalog Generation**:
   - Generates [index.html](file:///d:/Projects/all-widgets-v1/index.html) and [widget-comparison.html](file:///d:/Projects/all-widgets-v1/widget-comparison.html).
   - Updates `scripts/repo_catalog.json` for client-side search and filtering.
4. **Repository Sync**:
   - Automatically synchronizes all updated files to the standalone Git repository at `D:\Projects\widget-dashboard\`.
5. **Report & Verification**:
   - Prints a formatted report in your terminal showing total widgets, breakdown by status category, and percentage of verified files on disk.
