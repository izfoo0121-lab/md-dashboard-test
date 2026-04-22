-- ═══════════════════════════════════════════════════════════════════════
-- kpi_manual table — admin-entered KPI values per agent per month
-- Replaces the "auto calc" for new_accounts, vip_count
-- Data flow: admin.html writes → sales_dashboard.html reads on render
-- ═══════════════════════════════════════════════════════════════════════

create table if not exists public.kpi_manual (
  month        text not null,       -- e.g. "Apr 26"
  agent        text not null,       -- e.g. "BEN"
  new_accounts numeric default 0,   -- 开户口 (新户口) actual count
  vip_count    numeric default 0,   -- VIP 招聘 actual count
  updated_at   timestamptz default now(),
  updated_by   text default 'admin',
  primary key (month, agent)
);

create index if not exists idx_kpi_manual_month on public.kpi_manual (month);

-- RLS — permissive (consistent with other tables)
alter table public.kpi_manual enable row level security;

do $$
begin
  if not exists (select 1 from pg_policies where tablename='kpi_manual' and policyname='allow_all_kpi_manual') then
    create policy allow_all_kpi_manual on public.kpi_manual for all to anon using (true) with check (true);
  end if;
end $$;

-- Realtime (changes propagate instantly to agent dashboards)
do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname='supabase_realtime' and schemaname='public' and tablename='kpi_manual'
  ) then
    alter publication supabase_realtime add table public.kpi_manual;
  end if;
end $$;

-- Sanity check
select count(*) as row_count from public.kpi_manual;
