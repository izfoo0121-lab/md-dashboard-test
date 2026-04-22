# Surgical Patch — Archived Agent CTN Fix for process_data.py

Apply these 6 edits to your LOCAL `process_data.py`. Don't replace the whole file.

## Edit 1 — Agent list logic (around line 2340-2350)

### FIND this block:
```python
    # ── Agent list ─────────────────────────────────────────────────
    # Use agents defined in targets.json; fall back to agents found in data
    agents_from_targets = list(targets.get("agents", {}).keys())
    agents_from_data    = sorted(df["agent"].unique().tolist())
    agents = agents_from_targets if agents_from_targets else agents_from_data
    agents = [a for a in agents if a]  # remove blanks
    # Filter out inactive agents (active=False in targets.json)
    # Archived agents (archived=True) are also excluded from current view
    agents = [a for a in agents if targets.get("agents", {}).get(a, {}).get("active", True) != False]
    agents = [a for a in agents if not targets.get("agents", {}).get(a, {}).get("archived", False)]
    log(f"Agents: {agents}")
```

### REPLACE with:
```python
    # ── Agent list ─────────────────────────────────────────────────
    # Use agents defined in targets.json; fall back to agents found in data
    agents_from_targets = list(targets.get("agents", {}).keys())
    agents_from_data    = sorted(df["agent"].unique().tolist())
    raw_agents = agents_from_targets if agents_from_targets else agents_from_data
    raw_agents = [a for a in raw_agents if a]  # remove blanks
    # Archived agents are excluded from EVERYWHERE (they've left the company)
    raw_agents = [a for a in raw_agents if not targets.get("agents", {}).get(a, {}).get("archived", False)]

    # Two agent lists:
    #   all_agents  = includes active=false (e.g. JW) for company-wide totals
    #   agents      = active only — used for dropdowns, per-agent rankings, individual cards
    # Business rule: "JW (active=False) is hidden from agent dashboard
    #   but his CTN still counts in team totals."
    all_agents = list(raw_agents)
    agents     = [a for a in raw_agents
                  if targets.get("agents", {}).get(a, {}).get("active", True) != False]
    inactive_agents = [a for a in all_agents if a not in agents]
    log(f"Active agents:   {agents}")
    if inactive_agents:
        log(f"Inactive agents (team-totals only): {inactive_agents}")
```

## Edit 2 — calc_sales_progression & calc_brand_commission (around line 2409)

### FIND:
```python
    sales_prog  = calc_sales_progression(df, targets, agents, cur_month)
    brand_comm  = calc_brand_commission(df, targets, agents, cur_month, prev_months, brand_config)
```

### REPLACE with:
```python
    # Sales + brand commission calculated for ALL agents (incl. inactive like JW)
    # so team totals are accurate. Per-agent UI filters to active agents separately.
    sales_prog  = calc_sales_progression(df, targets, all_agents, cur_month)
    brand_comm  = calc_brand_commission(df, targets, all_agents, cur_month, prev_months, brand_config)
```

## Edit 3 — calc_aging (around line 2415)

### FIND:
```python
    aging       = calc_aging(df, agents, cur_month)
```

### REPLACE with:
```python
    aging       = calc_aging(df, all_agents, cur_month)  # include inactive for company-wide overdue
```

## Edit 4 — calc_team_summary (around line 2423)

### FIND:
```python
    team         = calc_team_summary(sales_prog, brand_comm, agents, targets, cur_month, df_raw, prev_months)
```

### REPLACE with:
```python
    team         = calc_team_summary(sales_prog, brand_comm, all_agents, targets, cur_month, df_raw, prev_months)
```

## Edit 5 — Expose agent lists in config output (around line 2468-2474)

### FIND:
```python
        "config": {
            "brand_config":       brand_config,
            "group_brand_config": group_brand_config,
            "inhouse_codes":      targets.get("inhouse_codes", DEFAULT_INHOUSE_CODES),
            "scope":              SCOPE_AREA,
            "group_incentive":    targets.get("team", {}).get("incentive", None),
        }
```

### REPLACE with:
```python
        "config": {
            "brand_config":       brand_config,
            "group_brand_config": group_brand_config,
            "inhouse_codes":      targets.get("inhouse_codes", DEFAULT_INHOUSE_CODES),
            "scope":              SCOPE_AREA,
            "group_incentive":    targets.get("team", {}).get("incentive", None),
            "active_agents":      agents,
            "all_agents":         all_agents,
            "inactive_agents":    inactive_agents,
        }
```

## That's it — 5 small edits total.

After applying, run:
```batch
update_dashboard.bat "Apr 26"
```

Watch the console output. You should see something like:
```
Active agents:   ['BEN', 'CJ', 'JACKY', 'JAMES', 'KEAN', 'KEE', 'KF', 'KI-MI', 'KW', 'LEON', 'NMK', 'SAM', 'YI']
Inactive agents (team-totals only): ['JW']
```

That confirms JW is properly separated: hidden from dropdown, included in team totals.

## Verification after deploy

On the dashboard, team-level totals (management.html, group tab) should now show HIGHER numbers than before — because JW's April CTN is finally included.

Rough sanity check: if JW had T1 target of 778 CTN and did, say, 60% of target, you should see ~470 extra CTN added to team totals.

