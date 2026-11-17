# Widget Reconciliation & Management Dashboard

Live tracking, reconciliation, team authentication, and activity tracking for 293 client-specified curriculum widgets vs. repository codebase.

---

## 🚀 Key Features

- **🔐 Built-in Authentication & Access Control**:
  - Secure login page (`login.html`) supporting **Email or Username** login, session management, and Light/Dark theme switcher.
  - Role-based permissions across 5 roles: **Admin**, **Developer**, **Content**, **QA**, and **Viewer**.
- **👥 Team User Management (Admin Only)**:
  - Add / invite new team members with specific roles and passwords.
  - Edit user names, emails, roles, and passwords.
  - Disable / enable user accounts with 1-click toggling.
  - Delete team members with safety protections (cannot delete active session admin).
- **📋 Centralized Activity Auditing (Admin Only)**:
  - Real-time audit log tracking logins, logouts, section visits, widget views, user edits, and exports.
  - Search by user or action, filter by event type, and export audit logs to CSV.
- **📊 293 Curated Reconciliation Records**:
  - 265 Available, 5 Corrected, 12 Requires Dev, 9 Whiteboard Tools, 2 Minor Changes.
  - Physical source file verification (272 verified files on disk).
  - Live standalone HTML simulation and Angular component links.
- **🔄 Dynamic Real-Time Excel Sync**:
  - In-browser drag-and-drop spreadsheet upload for instant recalculation.
  - Automated CI/CD deployment via GitHub Actions.

---

## 📂 Repository Contents

```
widget-dashboard/
├── index.html                                  # Protected main dashboard
├── login.html                                  # Authentication portal
├── auth.js                                     # Auth, RBAC & activity engine
├── widget-comparison.html                      # Mirror dashboard file
├── Widgets in CE Platinum cum Crystal.xlsx     # Reference spreadsheet
├── scripts/
│   ├── repo_catalog.json                       # 293 verified codebase mappings
│   └── generate_comparison_page.py            # Automated page generator
└── .github/
    └── workflows/
        └── deploy.yml                          # GitHub Actions Pages deployment
```

---

## 🔐 Access & Role Permissions

Access to the dashboard is protected by Role-Based Access Control (RBAC). Authorized team members can sign in with their assigned accounts via the login portal (`login.html`). For account provisioning or credential assistance, please connect directly with the System Administrator.

| Role | Permissions & Access Scope |
|---|---|
| **Admin** | Full system control: curriculum tracking, live Excel update/sync, team user management, activity history, and cloud database configuration. |
| **Developer** | Repository codebase audit, simulation code review, documentation, and Excel export. |
| **Content** | Curriculum reconciliation, widget content evaluation, documentation, and Excel export. |
| **QA** | Delivery readiness verification, QA tracking, documentation, and Excel export. |
| **Viewer** | Read-only access to overview metrics, curriculum catalog, and comparison tracking. |

---

## 🔄 Automated CI/CD (GitHub Pages)

Whenever `Widgets in CE Platinum cum Crystal.xlsx` or generator scripts are updated and pushed to `main`, GitHub Actions automatically:
1. Re-runs reconciliation against `scripts/repo_catalog.json`.
2. Generates updated `index.html` with latest figures and timestamps.
3. Deploys the site to GitHub Pages in ~35 seconds.
