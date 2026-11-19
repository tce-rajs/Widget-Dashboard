-- ======================================================================
-- WIDGET COMPARISON & STATUS DASHBOARD
-- SUPABASE POSTGRESQL CLOUD DATABASE SCHEMA
-- ======================================================================
-- Run this script in your Supabase SQL Editor (https://supabase.com/dashboard/project/_/sql)
-- It creates the tables, indexes, and initial team accounts for multi-system persistence.

-- 1. Create the App Users Table
create table if not exists public.app_users (
    id text primary key,
    full_name text not null,
    username text not null,
    email text unique not null,
    password_hash text not null,
    role text not null default 'viewer', -- 'admin', 'developer', 'content', 'qa', 'viewer'
    status text not null default 'active', -- 'active', 'disabled'
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    last_login timestamp with time zone
);

-- 2. Create the Activity Logs Table
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

-- 3. Create Indexes for High Performance
create index if not exists idx_app_users_email on public.app_users (email);
create index if not exists idx_app_users_status on public.app_users (status);
create index if not exists idx_app_activity_logs_timestamp on public.app_activity_logs (timestamp desc);

-- 4. Enable Row Level Security (RLS) & Grant Permissions
alter table public.app_users enable row level security;
alter table public.app_activity_logs enable row level security;

-- Grant table access to anon and authenticated roles
grant usage on schema public to anon, authenticated, service_role;
grant all on table public.app_users to anon, authenticated, service_role;
grant all on table public.app_activity_logs to anon, authenticated, service_role;

-- 5. Policies for Public Anon API Access (Permits direct browser dashboard access)
drop policy if exists "Allow anon read and write on app_users" on public.app_users;
create policy "Allow anon read and write on app_users"
    on public.app_users
    for all
    to anon, authenticated
    using (true)
    with check (true);

drop policy if exists "Allow anon read and write on app_activity_logs" on public.app_activity_logs;
create policy "Allow anon read and write on app_activity_logs"
    on public.app_activity_logs
    for all
    to anon, authenticated
    using (true)
    with check (true);

-- 6. Enable Real-Time Publication for instant multi-tab & multi-system sync
alter publication supabase_realtime add table public.app_users;
alter publication supabase_realtime add table public.app_activity_logs;

-- 7. Seed Initial Team Members (Linked with GitHub Repository)
insert into public.app_users (id, full_name, username, email, password_hash, role, status, created_at, last_login)
values
    ('usr_raj_00', 'Raj Shinde', 'tce-rajs', 'raj.shinde@optimizeq.com', 'Raj@123', 'admin', 'active', now(), now()),
    ('usr_admin_01', 'Administrator', 'admin', 'admin@company.com', 'Admin@123', 'admin', 'active', now(), now()),
    ('usr_prasanna_02', 'Prasanna Sir', 'prasanna', 'prasanna@company.com', 'Prasanna@123', 'admin', 'active', now(), null),
    ('usr_nitin_03', 'Nitin', 'nitin', 'nitin@company.com', 'Nitin@123', 'developer', 'active', now(), null),
    ('usr_content_04', 'Content Team Lead', 'content', 'content@company.com', 'Content@123', 'content', 'active', now(), null),
    ('usr_qa_05', 'QA Verification Engineer', 'qa', 'qa@company.com', 'Qa@123', 'qa', 'active', now(), null),
    ('usr_mgmt_06', 'Academic Management', 'viewer', 'viewer@company.com', 'Viewer@123', 'viewer', 'active', now(), null)
on conflict (email) do nothing;
