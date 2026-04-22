# Self-Hosting Migration Plan — Miracle MD Dashboard

**Purpose**: When/if you decide to move off Supabase Cloud, this document is your roadmap. It captures what you've built, why it exists, and exactly how to migrate.

**Author**: Claude + Isaac, session ending April 21, 2026
**Current state**: Supabase Cloud (https://rqitgmydcbyiygqjssrb.supabase.co)
**Intended destination**: Self-hosted on your office hardware

---

## Table Of Contents
1. [When To Actually Do This](#when-to-actually-do-this)
2. [What You Need To Acquire First](#what-you-need)
3. [Architecture Options (Ranked)](#architecture-options)
4. [Step-By-Step Migration](#step-by-step)
5. [Schema Reference](#schema-reference)
6. [Files That Need Changes](#files-to-change)
7. [Rollback Plan](#rollback)
8. [Ongoing Maintenance Tasks](#maintenance)
9. [Cost Analysis](#costs)

---

## 1. When To Actually Do This <a name="when-to-actually-do-this"></a>

Migrate when ONE or MORE of these become true:

- [ ] Regulatory requirement forces local data residency (e.g., PDPA audit, client contract clause)
- [ ] Supabase announces pricing that makes it unfeasible
- [ ] You hit Supabase free tier limits (500MB / 50K MAU / 2GB bandwidth)
- [ ] You hire a dedicated IT person who can maintain it
- [ ] You want to integrate with on-premise systems that can't reach cloud
- [ ] Operations grow to a size where self-hosting saves significant money

**Don't migrate just because "self-hosting feels better."** Until one of the above triggers, cloud is objectively better for your scale.

---

## 2. What You Need To Acquire First <a name="what-you-need"></a>

### Hardware
- **Dedicated machine** (not your primary laptop):
  - Mini PC: Intel NUC / Beelink / Minisforum (~RM 1,500–2,500 new, RM 800 used)
  - OR: Old laptop repurposed as server (free if you have one)
  - Minimum specs: 4 cores, 16 GB RAM, 256 GB SSD
  - Must run 24/7 with UPS battery backup for power outages
- **Network**:
  - Static IP from your ISP (~RM 50/mo extra for business fibre)
  - OR: Dynamic DNS service (free — DuckDNS, No-IP)
- **Backup media**:
  - External HDD 2TB minimum for rotating backups

### Skills / Support
- Basic Linux command-line (can be learned in 2-3 weekends)
- Docker Desktop on Windows (simpler) OR Linux server with Docker
- Understanding of TCP/IP, ports, DNS
- **Or**: Hired IT person (~RM 1,500–3,000/mo part-time)

### Software (all free)
- Docker Desktop (Windows) or Docker Engine (Linux)
- Supabase self-host kit from GitHub
- pgAdmin (PostgreSQL GUI) or Supabase Studio
- Caddy (automatic HTTPS) or nginx (manual HTTPS)
- Optional: Tailscale (free for 3 users, solves remote access without port forwarding)

---

## 3. Architecture Options (Ranked Safest → Most Complex) <a name="architecture-options"></a>

### Option A: Tailscale + Self-Hosted Supabase (RECOMMENDED)

Your office PC runs Supabase. Agents connect via Tailscale VPN. No port forwarding, no public IP needed.

```
Agent Phone                    Office PC
┌────────────┐                 ┌──────────────────────┐
│ Tailscale  │◀──encrypted────▶│ Tailscale            │
│ client app │     tunnel      │   └─▶ Supabase       │
│            │                 │         ├─ PostgreSQL│
│ Browser    │                 │         ├─ REST API  │
│ opens      │                 │         └─ Studio    │
│ http://    │                 │                      │
│ miracle.ts/│                 │ Docker Desktop       │
└────────────┘                 └──────────────────────┘
```

**Pros**:
- Zero port forwarding (router config untouched)
- Zero firewall drama
- Works from any agent location (WiFi, 4G, anywhere)
- Encrypted end-to-end
- Tailscale free tier = 3 users; paid = USD 5/user/mo
- Dead simple: install Tailscale on PC + each phone, done

**Cons**:
- Each agent phone needs Tailscale app installed (2 min each, one-time)
- Tailscale company could theoretically see connection metadata (not data itself)

**Time to set up**: 1 evening

### Option B: Caddy + Port Forwarding + Dynamic DNS

Office PC is publicly reachable. Agent phones connect directly.

```
Agent Phone                    Office PC
┌────────────┐                 ┌──────────────────────┐
│ Browser    │◀── HTTPS ──────▶│ Caddy (auto-TLS)     │
│ opens      │  internet       │   └─▶ Supabase       │
│ https://   │                 │                      │
│ miracle.my │                 │ + DuckDNS updater    │
└────────────┘                 └──────────────────────┘
                               Router: port 443 → PC
```

**Pros**:
- Standard web access (no client app needed)
- Free

**Cons**:
- Must configure router port forwarding
- Exposes PC to internet (attack surface)
- Need fail2ban, rate limiting, basic WAF
- Dynamic DNS can glitch during IP changes
- HTTPS certificate renewal (automated with Caddy — less concern)

**Time to set up**: 2-3 evenings. More if router gives you trouble.

### Option C: Office Network Only

Agents come to office to mark claims. Data never leaves office network.

**Pros**: Ultimate data sovereignty.
**Cons**: Kills the mobile workflow that's the whole point of this dashboard.

**Don't recommend** unless business model changes.

### Option D: Rent Malaysia-Located Cloud VPS

Use cloud but within Malaysia — TM Cloud, AirTrunk, Exabytes.

**Pros**: Data in Malaysia, professional hosting, no hardware to maintain.
**Cons**: Still cloud (though regional). Costs RM 100-300/mo.

**Good middle ground** if you want sovereignty without self-hosting burden.

---

## 4. Step-By-Step Migration <a name="step-by-step"></a>

### Phase 1: Preparation (do when you decide to migrate)

**Step 1.1**: Backup current Supabase data
```bash
# Using Supabase CLI or the backup script already built
supabase db dump -f supabase_backup.sql
```

**Step 1.2**: Set up the hardware
- Install Ubuntu Server 22.04 LTS (or Windows + Docker Desktop)
- Enable automatic security updates
- Configure UPS, test power-fail recovery
- Test SSH access from your workstation

**Step 1.3**: Install Docker
```bash
# Ubuntu
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### Phase 2: Deploy Self-Hosted Supabase

**Step 2.1**: Clone Supabase repo
```bash
git clone --depth 1 https://github.com/supabase/supabase
cd supabase/docker
cp .env.example .env
```

**Step 2.2**: Configure `.env`
- Generate strong passwords for DB + JWT secrets
- Set domain name (or Tailscale hostname)
- Configure SMTP for auth emails (can skip since you use PIN auth)

**Step 2.3**: Start it
```bash
docker compose up -d
# Wait 2 min, check status
docker compose ps
```

**Step 2.4**: Verify
- Open `http://localhost:3000` (Supabase Studio)
- Create a test table, insert a row, query it
- If it works, you have a functional Supabase

### Phase 3: Restore Data

**Step 3.1**: Import schema
```bash
psql -h localhost -U postgres < supabase_backup.sql
```

**Step 3.2**: Verify counts match
```sql
SELECT COUNT(*) FROM claims;  -- Should match what was in cloud
SELECT COUNT(*) FROM kpi_scores;
-- etc.
```

### Phase 4: Switch Your HTML Files

**Step 4.1**: Update Supabase URL + key in 4 files
```
FILES: admin.html, sales_dashboard.html, management.html, campaign_audit.html

REPLACE:
  const SUPABASE_URL = 'https://rqitgmydcbyiygqjssrb.supabase.co';
  const SUPABASE_KEY = 'sb_publishable_8xb7ZaHyr3OF3WNEqufuDg_67spOIFw';

WITH:
  const SUPABASE_URL = 'https://miracle-supa.your-domain.com'; // or tailscale URL
  const SUPABASE_KEY = 'YOUR_NEW_SELFHOSTED_ANON_KEY';
```

**Step 4.2**: Deploy updated HTML to GitHub Pages

**Step 4.3**: Test agent login on one phone before rolling out

### Phase 5: Rollout (sunrise deployment)

- Day 1: Keep BOTH systems running (old Supabase Cloud + new self-hosted)
- Day 2-7: Monitor for issues, users can always fall back
- Day 8: Disable cloud Supabase (pause project, don't delete)
- Day 30: Cancel cloud Supabase if no issues

---

## 5. Schema Reference <a name="schema-reference"></a>

Current Supabase tables to recreate:

```sql
-- Claims (agent deliveries for campaigns)
CREATE TABLE claims (
  id bigserial PRIMARY KEY,
  month text NOT NULL,
  agent text NOT NULL,
  camp_id text NOT NULL,
  debtor_code text NOT NULL,
  status text DEFAULT 'delivered',  -- delivered | verified | rejected
  remark text,
  bulk boolean DEFAULT false,
  actor text,
  ts timestamptz DEFAULT now(),
  UNIQUE (month, agent, camp_id, debtor_code)
);

-- Flags (agent annotations on debtors)
CREATE TABLE flags (
  id bigserial PRIMARY KEY,
  month text NOT NULL,
  agent text NOT NULL,
  debtor_code text NOT NULL,
  reason text,
  ts timestamptz DEFAULT now(),
  UNIQUE (month, agent, debtor_code)
);

-- KPI scores per agent per month
CREATE TABLE kpi_scores (
  month text NOT NULL,
  agent text NOT NULL,
  scores jsonb,
  updated_at timestamptz DEFAULT now(),
  PRIMARY KEY (month, agent)
);

-- Manual KPI entries (VIP count, new accounts)
CREATE TABLE kpi_manual (
  month text NOT NULL,
  agent text NOT NULL,
  new_accounts integer,
  vip_count integer,
  updated_at timestamptz DEFAULT now(),
  updated_by text,
  PRIMARY KEY (month, agent)
);

-- Agent PINs for login
CREATE TABLE agent_pins (
  agent text PRIMARY KEY,
  pin text NOT NULL
);

-- Audit log (optional, currently minimal use)
CREATE TABLE audit_log (
  id bigserial PRIMARY KEY,
  ts timestamptz DEFAULT now(),
  actor text,
  action text,
  month text,
  details jsonb
);

-- Indices for performance
CREATE INDEX idx_claims_month_agent ON claims(month, agent);
CREATE INDEX idx_claims_month_camp ON claims(month, camp_id);
CREATE INDEX idx_flags_month_agent ON flags(month, agent);
CREATE INDEX idx_kpi_scores_month ON kpi_scores(month);
```

---

## 6. Files That Need Changes <a name="files-to-change"></a>

When migrating, these files reference Supabase URL/key:

| File | Lines with URL/key | Action |
|------|-------------------|--------|
| `admin.html` | `SUPABASE_URL` constants in 3-4 places | Replace URL + key |
| `sales_dashboard.html` | `_SUPA_URL`, `_SUPA_KEY` at top of script | Replace URL + key |
| `management.html` | Inside GistSync module | Replace URL + key |
| `campaign_audit.html` | Inside Supabase module | Replace URL + key |
| `process_data.py` | If you migrate targets later | Replace URL + key |
| `backup.py` (when built) | Backup target | Replace URL + key |

**Tip**: Use a single `config.js` included by all HTML files so there's only one place to update. Future refactor worth doing.

---

## 7. Rollback Plan <a name="rollback"></a>

If self-hosted deployment fails:

### Immediate Rollback (<1 hour)
1. Reactivate Supabase Cloud project (just log into supabase.com)
2. `git revert` the HTML commits that changed the URL
3. `git push` — GitHub Pages rebuilds in 60 seconds
4. Everything back to cloud

### Data-Level Rollback (if data diverged)
1. Export from self-hosted: `supabase db dump -f selfhost_state.sql`
2. Import to cloud: use Supabase Studio SQL editor
3. Agents see up-to-date data

**Key insight**: As long as you keep BOTH running for the first week, rollback is painless. Don't delete the cloud project for at least 30 days.

---

## 8. Ongoing Maintenance Tasks <a name="maintenance"></a>

Self-hosting adds these responsibilities:

| Task | Frequency | Time |
|------|-----------|------|
| Docker image updates | Monthly | 15 min |
| OS security patches | Weekly (auto) | 0 min if auto-update |
| Database backups verification | Weekly | 5 min |
| Disk space check | Monthly | 2 min |
| SSL cert renewal | Every 90 days | 0 min if Caddy |
| PostgreSQL vacuum/analyze | Quarterly | 30 min |
| Disaster recovery drill | Annually | 2 hours |
| Dependency upgrades (breaking changes) | Annually | 4-8 hours |

**Estimated ongoing burden**: ~5 hours/month average, with spikes when upgrading major versions.

---

## 9. Cost Analysis <a name="costs"></a>

### Supabase Cloud (Current)
| Item | Cost |
|------|------|
| Database | Free (< 500 MB) |
| Bandwidth | Free (< 2 GB/mo) |
| Your time | ~0 hours/mo |
| **Total** | **RM 0/mo** |

### Self-Hosted (Option A: Tailscale)
| Item | Cost |
|------|------|
| Mini PC (one-time) | RM 1,500 (amortized RM 40/mo over 3 years) |
| Electricity (15W × 24h × 30d) | RM 5/mo |
| UPS + battery | RM 300 (amortized RM 8/mo) |
| Tailscale (3+ users) | USD 5/user/mo = RM 23/user |
| Your time (5 hr/mo × RM 50/hr opportunity cost) | RM 250/mo |
| **Total (4 users)** | **~RM 400/mo** |

### Self-Hosted (Option D: Malaysia Cloud VPS)
| Item | Cost |
|------|------|
| VPS (Exabytes 4GB) | RM 70/mo |
| Backup storage | RM 15/mo |
| Your time (2 hr/mo) | RM 100/mo |
| **Total** | **~RM 185/mo** |

**Takeaway**: Self-hosting costs you RM 200-400/mo in real money + time, vs RM 0 on cloud. Only worth it if data sovereignty has RM 400+/mo of business value to you.

---

## 10. Pre-Migration Checklist

Before pulling the trigger:

- [ ] Read this entire document
- [ ] Made backup of all HTML files
- [ ] Made backup of Supabase data (`supabase_backup.sql`)
- [ ] Tested self-hosted stack in isolation (on a spare machine first)
- [ ] Have rollback plan understood
- [ ] Have 3-day window where you can be on-call for issues
- [ ] Agents are notified of potential downtime
- [ ] Verified at least 2 weeks of Supabase Cloud backups exist
- [ ] Have Tailscale accounts created for all users
- [ ] Documented new URL + login procedure for agents

---

## 11. Questions To Revisit Annually

- Has Supabase Cloud caused any actual problems?
- Has data grown to where free tier limits are imminent?
- Has business scale changed (more agents, more campaigns, more tables)?
- Have regulatory requirements changed?
- Do you have new IT capabilities in team?

If all answers are "no change" → stay on cloud another year.

---

## Appendix: Why This Plan Even Exists

Isaac (the business owner) indicated an interest in data sovereignty but admitted limited Linux comfort. The honest recommendation is to stay on Supabase Cloud until there's a concrete trigger for migration. This document exists so that when that trigger arrives, execution is systematic rather than improvised.

**The migration path is real. It's documented. You can execute it when it matters. Don't rush into it without a reason.**
