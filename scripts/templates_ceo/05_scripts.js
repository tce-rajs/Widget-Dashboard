    <!-- Scripts -->
    <script>
        // Direct Access Mode (Authentication removed for immediate presentation & viewing)
        const currentUser = (typeof authManager !== 'undefined') ? (authManager.getCurrentUser() || { fullName: 'Team Member', role: 'admin' }) : { fullName: 'Team Member', role: 'admin' };

        let rawData = __DATA_JSON__;
        let rawQaData = __QA_DATA_JSON__;
        let filteredData = [...rawData];
        let currentPage = 1;
        const pageSize = 25;
        let sortCol = 'sr';
        let sortAsc = true;
        let currentModalPath = '';

        function initUserProfile() {
            // Direct access mode: user pill is not needed
            const pill = document.getElementById('userProfilePill');
            if (pill) pill.classList.add('hidden');
        }

        function handleLogout() {
            // Direct access mode: no logout
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
                <h4 class="text-base font-bold text-slate-900 dark:text-white">Widget Ecosystem Status Report</h4>
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
        const text = `WIDGET COMPARISON & STATUS REPORT
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
            showToast('Status report copied to clipboard!', 'success');
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
