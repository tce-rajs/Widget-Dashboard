/**
 * Supabase Cloud Database Configuration
 * Industry-Standard PostgreSQL & Real-Time Sync Engine
 *
 * How to get your credentials:
 * 1. Go to https://supabase.com and create a project (free tier).
 * 2. In Project Settings -> API, copy:
 *    - Project URL (e.g. "https://xxxxxx.supabase.co")
 *    - Project API Keys -> "anon public"
 * 3. Paste them below, OR configure them directly in the dashboard UI under "User Management" -> "Cloud Database".
 */

window.SUPABASE_CONFIG = {
    // Project URL (Leave empty for automatic fallback to offline local mode)
    url: '',

    // Public Anon Key (Safe to expose in browser for RLS-enabled tables)
    anonKey: '',

    // Real-time synchronization across all team computers and phones
    realtime: true
};
