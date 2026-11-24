/**
 * Authentication, Role-Based Access Control, Activity Tracking & Cloud Sync Engine
 * Hybrid Architecture: Client-Side Resilience + Industry-Standard Supabase PostgreSQL Cloud Sync
 */

const AUTH_STORAGE_KEY = 'widget_dashboard_auth_state_v1';
const USERS_STORAGE_KEY = 'widget_dashboard_users_v2';
const DELETED_USERS_STORAGE_KEY = 'widget_dashboard_deleted_users_v2';
const ACTIVITY_STORAGE_KEY = 'widget_dashboard_activity_logs_v1';
const SUPABASE_STORAGE_CONFIG_KEY = 'widget_dashboard_supabase_config_v1';

// Default initial team members (linked with GitHub repository)
const INITIAL_USERS = [
    {
        id: 'usr_raj_00',
        fullName: 'Raj Shinde',
        username: 'tce-rajs',
        email: 'raj.shinde@optimizeq.com',
        passwordHash: 'Raj@123',
        role: 'admin',
        status: 'active',
        createdAt: '2026-11-10T08:00:00.000Z',
        lastLogin: '2026-11-16T11:00:00.000Z'
    },
    {
        id: 'usr_admin_01',
        fullName: 'Administrator',
        username: 'admin',
        email: 'admin@company.com',
        passwordHash: 'Admin@123',
        role: 'admin',
        status: 'active',
        createdAt: '2026-11-10T09:00:00.000Z',
        lastLogin: '2026-11-16T10:00:00.000Z'
    },
    {
        id: 'usr_prasanna_02',
        fullName: 'Prasanna Sir',
        username: 'prasanna',
        email: 'prasanna@company.com',
        passwordHash: 'Prasanna@123',
        role: 'admin',
        status: 'active',
        createdAt: '2026-11-10T09:00:00.000Z',
        lastLogin: '2026-11-15T14:30:00.000Z'
    },
    {
        id: 'usr_nitin_03',
        fullName: 'Nitin',
        username: 'nitin',
        email: 'nitin@company.com',
        passwordHash: 'Nitin@123',
        role: 'developer',
        status: 'active',
        createdAt: '2026-11-10T09:30:00.000Z',
        lastLogin: '2026-11-16T08:15:00.000Z'
    },
    {
        id: 'usr_content_04',
        fullName: 'Content Team Lead',
        username: 'content',
        email: 'content@company.com',
        passwordHash: 'Content@123',
        role: 'content',
        status: 'active',
        createdAt: '2026-11-11T11:00:00.000Z',
        lastLogin: '2026-11-14T16:20:00.000Z'
    },
    {
        id: 'usr_qa_05',
        fullName: 'QA Verification Engineer',
        username: 'qa',
        email: 'qa@company.com',
        passwordHash: 'Qa@123',
        role: 'qa',
        status: 'active',
        createdAt: '2026-11-11T11:30:00.000Z',
        lastLogin: '2026-11-16T09:45:00.000Z'
    },
    {
        id: 'usr_mgmt_06',
        fullName: 'Academic Management',
        username: 'viewer',
        email: 'viewer@company.com',
        passwordHash: 'Viewer@123',
        role: 'viewer',
        status: 'active',
        createdAt: '2026-11-12T10:00:00.000Z',
        lastLogin: '2026-11-13T12:00:00.000Z'
    }
];

// Initial mock activity log for realistic history
const INITIAL_LOGS = [
    {
        id: 'act_init_01',
        userId: 'usr_admin_01',
        userName: 'Administrator',
        userEmail: 'admin@company.com',
        role: 'admin',
        activityType: 'LOGIN',
        section: 'Authentication',
        targetRef: '',
        details: 'Initial system login & session verified',
        timestamp: '2026-11-16T09:30:00.000Z'
    },
    {
        id: 'act_init_02',
        userId: 'usr_nitin_03',
        userName: 'Nitin',
        userEmail: 'nitin@company.com',
        role: 'developer',
        activityType: 'WIDGET_VIEW',
        section: 'All Widgets',
        targetRef: 'B3-WG96 (Operation Domino)',
        details: 'Verified physical entry point in widgets-b3/wg96-operation-domino',
        timestamp: '2026-11-16T09:35:10.000Z'
    },
    {
        id: 'act_init_03',
        userId: 'usr_qa_05',
        userName: 'QA Verification Engineer',
        userEmail: 'qa@company.com',
        role: 'qa',
        activityType: 'NAVIGATION',
        section: 'What Needs to Be Done',
        targetRef: '',
        details: 'Inspected 12 missing curriculum widgets backlog',
        timestamp: '2026-11-16T09:40:22.000Z'
    }
];

class AuthManager {
    constructor() {
        this.supabase = null;
        this.realtimeChannel = null;
        this.cloudSyncing = false;
        this.initUsers();
        this.initLogs();
        this.initSupabase();
    }

    // ==========================================
    // SUPABASE CLOUD DATABASE INTEGRATION
    // ==========================================
    getSupabaseConfig() {
        try {
            const stored = localStorage.getItem(SUPABASE_STORAGE_CONFIG_KEY);
            if (stored) {
                const parsed = JSON.parse(stored);
                if (parsed && parsed.url && parsed.anonKey) {
                    return parsed;
                }
            }
        } catch (e) {
            console.warn('Error reading Supabase stored config:', e);
        }

        if (typeof window !== 'undefined' && window.SUPABASE_CONFIG && window.SUPABASE_CONFIG.url) {
            return window.SUPABASE_CONFIG;
        }

        return { url: '', anonKey: '', realtime: true };
    }

    saveSupabaseConfig(url, anonKey, realtime = true) {
        const config = {
            url: (url || '').trim(),
            anonKey: (anonKey || '').trim(),
            realtime: !!realtime
        };
        try {
            localStorage.setItem(SUPABASE_STORAGE_CONFIG_KEY, JSON.stringify(config));
        } catch (e) {
            console.warn('Error saving Supabase config:', e);
        }
        return this.initSupabase(false);
    }

    isSupabaseConfigured() {
        const cfg = this.getSupabaseConfig();
        return !!(cfg && cfg.url && cfg.anonKey);
    }

    isSupabaseConnected() {
        return !!(this.supabase && this.isSupabaseConfigured());
    }

    initSupabase(autoSync = true) {
        const config = this.getSupabaseConfig();
        if (config.url && config.anonKey && typeof window !== 'undefined' && window.supabase && typeof window.supabase.createClient === 'function') {
            try {
                this.supabase = window.supabase.createClient(config.url, config.anonKey, {
                    auth: { persistSession: false }
                });
                console.log('[AuthManager] Supabase client initialized for:', config.url);
                if (autoSync) {
                    this.syncWithCloud();
                }
                if (config.realtime) {
                    this.subscribeRealtime();
                }
                return true;
            } catch (err) {
                console.error('[AuthManager] Failed to init Supabase client:', err);
                this.supabase = null;
                return false;
            }
        } else {
            this.supabase = null;
            return false;
        }
    }

    async syncWithCloud() {
        if (!this.supabase) return { success: false, error: 'Database not initialized' };
        if (this.cloudSyncing) return { success: false, error: 'Sync already in progress' };
        this.cloudSyncing = true;
        try {
            const { data, error } = await this.supabase
                .from('app_users')
                .select('*')
                .order('created_at', { ascending: true });

            if (error) {
                console.warn('[AuthManager] Supabase select error:', error.message);
                return { success: false, error: error.message };
            }

            if (Array.isArray(data)) {
                if (data.length === 0) {
                    // Cloud table is empty: Auto-seed initial local users to Supabase
                    console.log('[AuthManager] Cloud table empty. Seeding local users to Supabase...');
                    const pushRes = await this.pushLocalUsersToCloud();
                    return { success: pushRes.success, count: pushRes.count, seeded: true, error: pushRes.error };
                } else {
                    // Map cloud DB records to local user format
                    const cloudUsers = data.map(r => ({
                        id: r.id,
                        fullName: r.full_name,
                        username: r.username || (r.email ? r.email.split('@')[0] : 'user'),
                        email: (r.email || '').toLowerCase(),
                        passwordHash: r.password_hash,
                        role: r.role || 'viewer',
                        status: r.status || 'active',
                        createdAt: r.created_at || new Date().toISOString(),
                        lastLogin: r.last_login || null
                    }));

                    this.saveUsers(cloudUsers);
                    console.log(`[AuthManager] Synced ${cloudUsers.length} users from Supabase Cloud Database!`);

                    if (typeof window !== 'undefined' && window.dispatchEvent) {
                        window.dispatchEvent(new CustomEvent('dashboard_users_changed', { detail: { source: 'cloud' } }));
                    }
                    return { success: true, count: cloudUsers.length, seeded: false };
                }
            }
            return { success: true, count: 0 };
        } catch (e) {
            console.warn('[AuthManager] Cloud sync exception:', e);
            return { success: false, error: e.message };
        } finally {
            this.cloudSyncing = false;
        }
    }

    async pushLocalUsersToCloud() {
        if (!this.supabase) return { success: false, error: 'Supabase client not connected' };
        try {
            const users = this.getUsers();
            if (!users || users.length === 0) {
                return { success: false, error: 'No local users available to push' };
            }
            const rows = users.map(u => ({
                id: u.id,
                full_name: u.fullName,
                username: u.username || (u.email ? u.email.split('@')[0] : 'user'),
                email: u.email.toLowerCase(),
                password_hash: u.passwordHash,
                role: u.role,
                status: u.status,
                created_at: u.createdAt || new Date().toISOString(),
                last_login: u.lastLogin || null
            }));

            let { data, error } = await this.supabase
                .from('app_users')
                .upsert(rows);

            if (error) {
                console.warn('[AuthManager] Primary key upsert failed, retrying on email conflict:', error.message);
                const retry = await this.supabase
                    .from('app_users')
                    .upsert(rows, { onConflict: 'email' });
                error = retry.error;
            }

            if (error) {
                console.error('[AuthManager] pushLocalUsersToCloud failed:', error.message);
                return { success: false, error: error.message };
            }
            console.log(`[AuthManager] Successfully seeded ${rows.length} users to Supabase cloud!`);
            return { success: true, count: rows.length };
        } catch (e) {
            console.error('[AuthManager] pushLocalUsersToCloud exception:', e);
            return { success: false, error: e.message };
        }
    }

    subscribeRealtime() {
        if (!this.supabase) return;
        try {
            if (this.realtimeChannel) {
                this.supabase.removeChannel(this.realtimeChannel);
            }
            this.realtimeChannel = this.supabase
                .channel('public:app_users')
                .on('postgres_changes', { event: '*', schema: 'public', table: 'app_users' }, payload => {
                    console.log('[AuthManager] Realtime Postgres change detected:', payload.eventType);
                    this.syncWithCloud();
                })
                .subscribe();
        } catch (e) {
            console.warn('[AuthManager] Realtime subscription error:', e);
        }
    }

    // ==========================================
    // LOCAL STORAGE USER PERSISTENCE & BLACKLIST
    // ==========================================
    getDeletedUserEmails() {
        try {
            const raw = localStorage.getItem(DELETED_USERS_STORAGE_KEY) || sessionStorage.getItem(DELETED_USERS_STORAGE_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch {
            return [];
        }
    }

    saveDeletedUserEmail(email) {
        const list = this.getDeletedUserEmails();
        const clean = (email || '').trim().toLowerCase();
        if (clean && !list.includes(clean)) {
            list.push(clean);
            const json = JSON.stringify(list);
            try { localStorage.setItem(DELETED_USERS_STORAGE_KEY, json); } catch {}
            try { sessionStorage.setItem(DELETED_USERS_STORAGE_KEY, json); } catch {}
        }
    }

    unmarkDeletedUserEmail(email) {
        const list = this.getDeletedUserEmails();
        const clean = (email || '').trim().toLowerCase();
        if (clean) {
            const filtered = list.filter(e => e !== clean);
            const json = JSON.stringify(filtered);
            try { localStorage.setItem(DELETED_USERS_STORAGE_KEY, json); } catch {}
            try { sessionStorage.setItem(DELETED_USERS_STORAGE_KEY, json); } catch {}
        }
    }

    initUsers() {
        const deletedList = this.getDeletedUserEmails();
        let currentUsers = null;

        try {
            const stored = localStorage.getItem(USERS_STORAGE_KEY) || sessionStorage.getItem(USERS_STORAGE_KEY);
            if (stored) {
                const parsed = JSON.parse(stored);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    currentUsers = parsed;
                }
            }
        } catch (e) {
            console.warn('Error reading stored users, will initialize:', e);
        }

        if (!currentUsers) {
            currentUsers = INITIAL_USERS.filter(u => u && u.email && !deletedList.includes(u.email.toLowerCase()));
            this.saveUsers(currentUsers);
            return;
        }

        // If users already exist in storage, PRESERVE EVERY ONE OF THEM!
        // Only inject any non-deleted initial seed users if they aren't already present in currentUsers
        let modified = false;
        INITIAL_USERS.forEach(seed => {
            if (!seed || !seed.email) return;
            const seedEmail = seed.email.toLowerCase();
            if (deletedList.includes(seedEmail)) return; // explicitly deleted by admin
            const exists = currentUsers.some(u => u && u.email && u.email.toLowerCase() === seedEmail);
            if (!exists) {
                currentUsers.push(seed);
                modified = true;
            }
        });

        // Ensure every user object has consistent fields (id, username, email, status)
        currentUsers.forEach(u => {
            if (u && u.email) {
                if (!u.username) u.username = u.email.includes('@') ? u.email.split('@')[0] : u.email;
                if (!u.status) u.status = 'active';
            }
        });

        this.saveUsers(currentUsers);
    }

    initLogs() {
        if (!localStorage.getItem(ACTIVITY_STORAGE_KEY) && !sessionStorage.getItem(ACTIVITY_STORAGE_KEY)) {
            const json = JSON.stringify(INITIAL_LOGS);
            try { localStorage.setItem(ACTIVITY_STORAGE_KEY, json); } catch {}
            try { sessionStorage.setItem(ACTIVITY_STORAGE_KEY, json); } catch {}
        }
    }

    getUsers() {
        try {
            const raw = localStorage.getItem(USERS_STORAGE_KEY) || sessionStorage.getItem(USERS_STORAGE_KEY);
            if (raw) {
                const parsed = JSON.parse(raw);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    return parsed;
                }
            }
            return INITIAL_USERS;
        } catch {
            return INITIAL_USERS;
        }
    }

    saveUsers(users) {
        if (!Array.isArray(users)) return;
        const json = JSON.stringify(users);
        try { localStorage.setItem(USERS_STORAGE_KEY, json); } catch (e) { console.warn('localStorage save failed', e); }
        try { sessionStorage.setItem(USERS_STORAGE_KEY, json); } catch (e) { console.warn('sessionStorage save failed', e); }
    }

    getLogs() {
        try {
            return JSON.parse(localStorage.getItem(ACTIVITY_STORAGE_KEY)) || INITIAL_LOGS;
        } catch {
            return INITIAL_LOGS;
        }
    }

    saveLogs(logs) {
        localStorage.setItem(ACTIVITY_STORAGE_KEY, JSON.stringify(logs));
    }

    logActivity(type, section, targetRef = '', details = '') {
        const currentUser = this.getCurrentUser();
        const logs = this.getLogs();
        const newLog = {
            id: 'act_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
            userId: currentUser ? currentUser.id : 'anonymous',
            userName: currentUser ? currentUser.fullName : 'Guest',
            userEmail: currentUser ? currentUser.email : 'guest@company.com',
            role: currentUser ? currentUser.role : 'viewer',
            activityType: type,
            section: section,
            targetRef: targetRef,
            details: details,
            timestamp: new Date().toISOString()
        };

        logs.unshift(newLog);
        if (logs.length > 500) logs.pop();
        this.saveLogs(logs);

        // Supabase Cloud Activity Log Insertion
        if (this.supabase) {
            this.supabase.from('app_activity_logs').insert({
                id: newLog.id,
                user_id: newLog.userId,
                user_name: newLog.userName,
                user_email: newLog.userEmail,
                role: newLog.role,
                activity_type: newLog.activityType,
                section: newLog.section,
                target_ref: newLog.targetRef,
                details: newLog.details,
                timestamp: newLog.timestamp
            }).then(({ error }) => {
                if (error) console.warn('[AuthManager] Supabase logActivity error:', error.message);
            });
        }

        return newLog;
    }

    // ==========================================
    // AUTHENTICATION & SESSIONS
    // ==========================================
    login(identifier, password, rememberMe = false) {
        const cleanId = (identifier || '').trim().toLowerCase();
        const cleanPass = (password || '').trim();

        if (!cleanId || !cleanPass) {
            return { success: false, error: 'Please enter both username/email and password.' };
        }

        const users = this.getUsers();
        const user = users.find(u =>
            (u.email && u.email.toLowerCase() === cleanId) ||
            (u.username && u.username.toLowerCase() === cleanId)
        );

        if (!user) {
            this.logActivity('LOGIN_FAILED', 'Authentication', cleanId, 'User not found');
            return { success: false, error: 'Invalid username/email or password.' };
        }

        if (user.status === 'disabled') {
            this.logActivity('LOGIN_REJECTED', 'Authentication', user.email, 'Account disabled');
            return { success: false, error: 'This account has been disabled by the system administrator. Please contact admin.' };
        }

        if (user.passwordHash !== cleanPass) {
            this.logActivity('LOGIN_FAILED', 'Authentication', user.email, 'Password mismatch');
            return { success: false, error: 'Invalid username/email or password.' };
        }

        user.lastLogin = new Date().toISOString();
        this.saveUsers(users);

        // Push last login timestamp to Supabase if connected
        if (this.supabase) {
            this.supabase.from('app_users').update({ last_login: user.lastLogin }).eq('id', user.id).then(() => {});
        }

        const sessionData = {
            user: {
                id: user.id,
                fullName: user.fullName,
                username: user.username,
                email: user.email,
                role: user.role
            },
            token: 'auth_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
            rememberMe: rememberMe,
            loginTime: Date.now(),
            expiresAt: Date.now() + (rememberMe ? 30 * 86400000 : 86400000)
        };

        if (rememberMe) {
            localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(sessionData));
        } else {
            sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(sessionData));
            localStorage.removeItem(AUTH_STORAGE_KEY);
        }

        this.logActivity('LOGIN', 'Authentication', user.email, `Successful login as ${user.role.toUpperCase()}`);
        return { success: true, user: user };
    }

    logout() {
        const currentUser = this.getCurrentUser();
        if (currentUser) {
            this.logActivity('LOGOUT', 'Authentication', currentUser.email, 'User logged out');
        }
        localStorage.removeItem(AUTH_STORAGE_KEY);
        sessionStorage.removeItem(AUTH_STORAGE_KEY);
        window.location.href = 'index.html';
    }

    getCurrentSession() {
        try {
            const raw = localStorage.getItem(AUTH_STORAGE_KEY) || sessionStorage.getItem(AUTH_STORAGE_KEY);
            if (!raw) return null;
            const session = JSON.parse(raw);
            if (Date.now() > session.expiresAt) {
                return null;
            }
            return session;
        } catch {
            return null;
        }
    }

    getCurrentUser() {
        const session = this.getCurrentSession();
        return (session && session.user) ? session.user : { fullName: 'Team Member', role: 'admin' };
    }

    requireAuth() {
        return this.getCurrentUser();
    }

    hasRole(requiredRoles) {
        const user = this.getCurrentUser();
        if (!user) return false;
        if (!Array.isArray(requiredRoles)) {
            requiredRoles = [requiredRoles];
        }
        return requiredRoles.includes(user.role);
    }

    isAdmin() {
        const user = this.getCurrentUser();
        return user && user.role === 'admin';
    }

    // ==========================================
    // ADMIN USER MANAGEMENT FUNCTIONS
    // ==========================================
    addUser(fullName, email, password, role) {
        if (!this.isAdmin()) return { success: false, error: 'Unauthorized: Admin privilege required' };

        const cleanEmail = (email || '').trim().toLowerCase();
        if (!cleanEmail) return { success: false, error: 'Email address is required.' };
        const cleanName = (fullName || '').trim();
        if (!cleanName) return { success: false, error: 'Full name is required.' };

        const users = this.getUsers();

        if (users.some(u => u && u.email && u.email.toLowerCase() === cleanEmail)) {
            return { success: false, error: 'A team member with this email address already exists.' };
        }

        const username = cleanEmail.includes('@') ? cleanEmail.split('@')[0] : cleanEmail;
        const newUser = {
            id: 'usr_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5),
            fullName: cleanName,
            username: username,
            email: cleanEmail,
            passwordHash: (password || '').trim() || 'Welcome@123',
            role: role || 'viewer',
            status: 'active',
            createdAt: new Date().toISOString(),
            lastLogin: null
        };

        // Guarantee this email is unblacklisted so reload NEVER filters it out!
        this.unmarkDeletedUserEmail(cleanEmail);

        users.push(newUser);
        this.saveUsers(users);
        this.logActivity('USER_MGMT', 'User Management', cleanEmail, `Created user ${newUser.fullName} with role ${newUser.role}`);

        // Push new user to Supabase Cloud Database
        if (this.supabase) {
            this.supabase.from('app_users').insert({
                id: newUser.id,
                full_name: newUser.fullName,
                username: newUser.username,
                email: newUser.email,
                password_hash: newUser.passwordHash,
                role: newUser.role,
                status: newUser.status,
                created_at: newUser.createdAt,
                last_login: null
            }).then(({ error }) => {
                if (error) console.error('[AuthManager] Supabase addUser error:', error);
            });
        }

        if (typeof window !== 'undefined' && window.dispatchEvent) {
            window.dispatchEvent(new CustomEvent('dashboard_users_changed', { detail: { action: 'add', user: newUser } }));
        }

        return { success: true, user: newUser };
    }

    updateUserRole(userId, newRole) {
        if (!this.isAdmin()) return { success: false, error: 'Unauthorized' };
        const users = this.getUsers();
        const user = users.find(u => u.id === userId);
        if (!user) return { success: false, error: 'User not found' };

        const oldRole = user.role;
        user.role = newRole;
        this.saveUsers(users);
        this.logActivity('USER_MGMT', 'User Management', user.email, `Changed role from ${oldRole} to ${newRole}`);

        if (this.supabase) {
            this.supabase.from('app_users').update({ role: newRole }).eq('id', userId).then(() => {});
        }

        return { success: true };
    }

    toggleUserStatus(userId) {
        if (!this.isAdmin()) return { success: false, error: 'Unauthorized' };
        const users = this.getUsers();
        const user = users.find(u => u.id === userId);
        if (!user) return { success: false, error: 'User not found' };

        // Prevent disabling yourself if you are the only active admin
        const currentUser = this.getCurrentUser();
        if (currentUser && currentUser.id === user.id) {
            return { success: false, error: 'You cannot disable your own administrator account while logged in.' };
        }

        user.status = user.status === 'active' ? 'disabled' : 'active';
        this.saveUsers(users);
        this.logActivity('USER_MGMT', 'User Management', user.email, `Set status to ${user.status.toUpperCase()}`);

        if (this.supabase) {
            this.supabase.from('app_users').update({ status: user.status }).eq('id', userId).then(({ error }) => {
                if (error) console.error('[AuthManager] Supabase toggleStatus error:', error);
            });
        }

        if (typeof window !== 'undefined' && window.dispatchEvent) {
            window.dispatchEvent(new CustomEvent('dashboard_users_changed', { detail: { action: 'toggle', user: user } }));
        }

        return { success: true, status: user.status };
    }

    resetPassword(userId, newPassword) {
        if (!this.isAdmin()) return { success: false, error: 'Unauthorized' };
        const users = this.getUsers();
        const user = users.find(u => u.id === userId);
        if (!user) return { success: false, error: 'User not found' };

        user.passwordHash = newPassword.trim();
        this.saveUsers(users);
        this.logActivity('USER_MGMT', 'User Management', user.email, 'Admin reset user password');

        if (this.supabase) {
            this.supabase.from('app_users').update({ password_hash: user.passwordHash }).eq('id', userId).then(() => {});
        }

        return { success: true };
    }

    updateUser(userId, fullName, email, role, password) {
        if (!this.isAdmin()) return { success: false, error: 'Unauthorized: Admin privilege required' };

        // Support both object syntax and positional arguments
        if (fullName && typeof fullName === 'object') {
            const data = fullName;
            fullName = data.fullName;
            email = data.email;
            role = data.role;
            password = data.password;
        }

        const users = this.getUsers();
        const user = users.find(u => String(u.id) === String(userId));
        if (!user) return { success: false, error: 'User not found' };

        const cleanEmail = (email || user.email || '').trim().toLowerCase();
        if (!cleanEmail) return { success: false, error: 'Email is required' };
        const cleanName = (fullName || user.fullName || '').trim();
        if (!cleanName) return { success: false, error: 'Full name is required' };
        role = role || user.role || 'viewer';

        const emailExists = users.some(u => String(u.id) !== String(userId) && u.email && u.email.toLowerCase() === cleanEmail);
        if (emailExists) {
            return { success: false, error: 'Another user already exists with this email address.' };
        }

        const currentUser = this.getCurrentUser();
        if (currentUser && currentUser.id === userId && role !== 'admin') {
            const activeAdmins = users.filter(u => u.role === 'admin' && u.status === 'active' && u.id !== userId);
            if (activeAdmins.length === 0) {
                return { success: false, error: 'Cannot remove admin role: At least one active admin must exist.' };
            }
        }

        user.fullName = cleanName;
        user.email = cleanEmail;
        user.username = cleanEmail.includes('@') ? cleanEmail.split('@')[0] : cleanEmail;
        if (role) user.role = role;
        if (password && password.trim()) {
            user.passwordHash = password.trim();
        }

        this.unmarkDeletedUserEmail(cleanEmail);
        this.saveUsers(users);

        if (currentUser && currentUser.id === userId) {
            const session = this.getCurrentSession();
            if (session && session.user) {
                session.user.fullName = user.fullName;
                session.user.email = user.email;
                session.user.role = user.role;
                if (localStorage.getItem(AUTH_STORAGE_KEY)) {
                    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
                } else {
                    sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
                }
            }
        }

        this.logActivity('USER_MGMT', 'User Management', user.email, `Admin updated user details for ${user.fullName} (${user.role.toUpperCase()})`);

        if (this.supabase) {
            const updatePayload = {
                full_name: user.fullName,
                username: user.username,
                email: user.email,
                role: user.role
            };
            if (password && password.trim()) updatePayload.password_hash = user.passwordHash;

            this.supabase.from('app_users').update(updatePayload).eq('id', userId).then(({ error }) => {
                if (error) console.error('[AuthManager] Supabase updateUser error:', error);
            });
        }

        if (typeof window !== 'undefined' && window.dispatchEvent) {
            window.dispatchEvent(new CustomEvent('dashboard_users_changed', { detail: { action: 'update', user: user } }));
        }

        return { success: true, user };
    }

    editUser(userId, fullNameOrData, email, role, password) {
        return this.updateUser(userId, fullNameOrData, email, role, password);
    }

    deleteUser(userId) {
        if (!this.isAdmin()) return { success: false, error: 'Unauthorized: Admin privilege required' };
        const users = this.getUsers();
        const user = users.find(u => String(u.id) === String(userId));
        if (!user) return { success: false, error: 'User not found in system.' };

        const currentUser = this.getCurrentUser();
        if (currentUser && String(currentUser.id) === String(userId)) {
            return { success: false, error: 'You cannot delete your own logged-in administrator account.' };
        }

        if ((user.role || '').toLowerCase() === 'admin') {
            const otherAdmins = users.filter(u => (u.role || '').toLowerCase() === 'admin' && String(u.id) !== String(userId));
            if (otherAdmins.length === 0) {
                return { success: false, error: 'Cannot delete the only administrator account.' };
            }
        }

        // Permanently record on deleted blacklist so it NEVER gets resurrected on reload
        this.saveDeletedUserEmail(user.email);

        const remainingUsers = users.filter(u => String(u.id) !== String(userId));
        this.saveUsers(remainingUsers);
        this.logActivity('USER_MGMT', 'User Management', user.email, `Admin deleted user ${user.fullName} (${user.email})`);

        if (this.supabase) {
            this.supabase.from('app_users').delete().eq('id', userId).then(({ error }) => {
                if (error) console.error('[AuthManager] Supabase deleteUser error:', error);
            });
        }

        if (typeof window !== 'undefined' && window.dispatchEvent) {
            window.dispatchEvent(new CustomEvent('dashboard_users_changed', { detail: { action: 'delete', userId: userId } }));
        }

        return { success: true, user: user, remainingCount: remainingUsers.length };
    }

    restoreDefaultUsers() {
        if (!this.isAdmin()) return { success: false, error: 'Unauthorized: Admin privilege required' };
        localStorage.removeItem(DELETED_USERS_STORAGE_KEY);
        this.saveUsers(INITIAL_USERS);
        this.logActivity('USER_MGMT', 'User Management', '', 'Admin restored default team accounts');

        if (this.supabase) {
            this.pushLocalUsersToCloud();
        }

        return { success: true, users: INITIAL_USERS };
    }
}

// Global singleton instance
window.authManager = new AuthManager();
