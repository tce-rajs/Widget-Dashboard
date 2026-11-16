/**
 * Simple Authentication, Role-Based Access Control, and Activity Tracking Engine
 * Self-contained, zero-external dependency, secure client-side implementation.
 */

const AUTH_STORAGE_KEY = 'widget_dashboard_auth_state_v1';
const USERS_STORAGE_KEY = 'widget_dashboard_users_v2';
const DELETED_USERS_STORAGE_KEY = 'widget_dashboard_deleted_users_v2';
const ACTIVITY_STORAGE_KEY = 'widget_dashboard_activity_logs_v1';

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
        this.initUsers();
        this.initLogs();
    }

    getDeletedUserEmails() {
        try {
            return JSON.parse(localStorage.getItem(DELETED_USERS_STORAGE_KEY)) || [];
        } catch {
            return [];
        }
    }

    saveDeletedUserEmail(email) {
        const list = this.getDeletedUserEmails();
        const clean = (email || '').trim().toLowerCase();
        if (clean && !list.includes(clean)) {
            list.push(clean);
            localStorage.setItem(DELETED_USERS_STORAGE_KEY, JSON.stringify(list));
        }
    }

    initUsers() {
        const deletedList = this.getDeletedUserEmails();
        const stored = localStorage.getItem(USERS_STORAGE_KEY);
        if (!stored) {
            const filtered = INITIAL_USERS.filter(u => !deletedList.includes(u.email.toLowerCase()));
            localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(filtered));
            return;
        }
        try {
            let currentUsers = JSON.parse(stored) || [];
            currentUsers = currentUsers.filter(u => !deletedList.includes(u.email.toLowerCase()));

            INITIAL_USERS.forEach(seed => {
                if (deletedList.includes(seed.email.toLowerCase())) return;
                const found = currentUsers.find(u => u.email.toLowerCase() === seed.email.toLowerCase());
                if (!found) {
                    currentUsers.push(seed);
                } else {
                    if (seed.username && found.username !== seed.username) {
                        found.username = seed.username;
                    }
                    if (seed.passwordHash && found.passwordHash !== seed.passwordHash) {
                        found.passwordHash = seed.passwordHash;
                    }
                }
            });
            localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(currentUsers));
        } catch {
            const filtered = INITIAL_USERS.filter(u => !deletedList.includes(u.email.toLowerCase()));
            localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(filtered));
        }
    }

    initLogs() {
        if (!localStorage.getItem(ACTIVITY_STORAGE_KEY)) {
            localStorage.setItem(ACTIVITY_STORAGE_KEY, JSON.stringify(INITIAL_LOGS));
        }
    }

    getUsers() {
        try {
            return JSON.parse(localStorage.getItem(USERS_STORAGE_KEY)) || INITIAL_USERS;
        } catch {
            return INITIAL_USERS;
        }
    }

    saveUsers(users) {
        localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(users));
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
        // Keep last 1,000 logs
        if (logs.length > 1000) logs.pop();
        this.saveLogs(logs);
        return newLog;
    }

    login(email, password, remember = true) {
        const cleanEmail = (email || '').trim().toLowerCase();
        const cleanPass = (password || '').trim();

        if (!cleanEmail || !cleanPass) {
            return { success: false, error: 'Email and password are required.' };
        }

        const users = this.getUsers();
        const user = users.find(u => 
            u.email.toLowerCase() === cleanEmail || 
            (u.username && u.username.toLowerCase() === cleanEmail)
        );

        if (!user) {
            this.logActivity('LOGIN_FAILED', 'Authentication', cleanEmail, 'Invalid email or username entered');
            return { success: false, error: 'No account found with this email address or username.' };
        }

        if (user.status === 'disabled') {
            this.logActivity('LOGIN_FAILED', 'Authentication', cleanEmail, 'Attempted login to disabled account');
            return { success: false, error: 'This account has been disabled by an administrator. Please contact your admin.' };
        }

        if (user.passwordHash !== cleanPass) {
            this.logActivity('LOGIN_FAILED', 'Authentication', cleanEmail, 'Incorrect password entered');
            return { success: false, error: 'Incorrect password. Please verify your credentials and try again.' };
        }

        // Update last login
        user.lastLogin = new Date().toISOString();
        this.saveUsers(users);

        const sessionData = {
            user: {
                id: user.id,
                fullName: user.fullName,
                email: user.email,
                role: user.role,
                status: user.status
            },
            token: 'tok_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
            expiresAt: Date.now() + (remember ? (7 * 24 * 60 * 60 * 1000) : (12 * 60 * 60 * 1000)) // 7 days or 12 hours
        };

        if (remember) {
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
        window.location.href = 'login.html';
    }

    getCurrentSession() {
        try {
            const raw = localStorage.getItem(AUTH_STORAGE_KEY) || sessionStorage.getItem(AUTH_STORAGE_KEY);
            if (!raw) return null;
            const session = JSON.parse(raw);
            if (Date.now() > session.expiresAt) {
                this.logout();
                return null;
            }
            return session;
        } catch {
            return null;
        }
    }

    getCurrentUser() {
        const session = this.getCurrentSession();
        return session ? session.user : null;
    }

    requireAuth() {
        const session = this.getCurrentSession();
        if (!session || !session.user) {
            const currentPath = window.location.pathname.split('/').pop() || 'index.html';
            window.location.href = `login.html?redirect=${encodeURIComponent(currentPath)}`;
            return null;
        }

        // Check if user status was disabled while logged in
        const users = this.getUsers();
        const freshUser = users.find(u => u.id === session.user.id);
        if (!freshUser || freshUser.status === 'disabled') {
            alert('Your account has been disabled by an administrator.');
            this.logout();
            return null;
        }

        return freshUser;
    }

    isAdmin() {
        const user = this.getCurrentUser();
        return user && user.role === 'admin';
    }

    // Admin User Management functions
    addUser(fullName, email, password, role) {
        if (!this.isAdmin()) return { success: false, error: 'Unauthorized: Admin privilege required' };
        
        const cleanEmail = (email || '').trim().toLowerCase();
        const users = this.getUsers();

        if (users.some(u => u.email.toLowerCase() === cleanEmail)) {
            return { success: false, error: 'A team member with this email address already exists.' };
        }

        const newUser = {
            id: 'usr_' + Date.now().toString(36),
            fullName: fullName.trim(),
            email: cleanEmail,
            passwordHash: password.trim() || 'Welcome@123',
            role: role || 'viewer',
            status: 'active',
            createdAt: new Date().toISOString(),
            lastLogin: null
        };

        users.push(newUser);
        this.saveUsers(users);
        this.logActivity('USER_MGMT', 'User Management', cleanEmail, `Created user ${newUser.fullName} with role ${newUser.role}`);
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
        return { success: true };
    }

    editUser(userId, { fullName, email, role, password }) {
        if (!this.isAdmin()) return { success: false, error: 'Unauthorized: Admin privilege required' };
        const users = this.getUsers();
        const user = users.find(u => u.id === userId);
        if (!user) return { success: false, error: 'User not found' };

        const cleanEmail = (email || '').trim().toLowerCase();
        if (!cleanEmail) return { success: false, error: 'Email cannot be empty' };

        if (cleanEmail !== user.email.toLowerCase()) {
            if (users.some(u => u.id !== userId && u.email.toLowerCase() === cleanEmail)) {
                return { success: false, error: 'A team member with this email already exists.' };
            }
        }

        const cleanName = (fullName || '').trim();
        if (!cleanName) return { success: false, error: 'Full name cannot be empty' };

        const currentUser = this.getCurrentUser();
        if (currentUser && currentUser.id === userId && role !== 'admin') {
            const activeAdmins = users.filter(u => u.role === 'admin' && u.status === 'active' && u.id !== userId);
            if (activeAdmins.length === 0) {
                return { success: false, error: 'Cannot remove admin role: At least one active admin must exist.' };
            }
        }

        user.fullName = cleanName;
        user.email = cleanEmail;
        if (role) user.role = role;
        if (password && password.trim()) {
            user.passwordHash = password.trim();
        }

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
        return { success: true, user };
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
        return { success: true, users: INITIAL_USERS };
    }
}

// Global singleton instance
window.authManager = new AuthManager();
