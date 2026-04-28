import json

with open('dashboard_data.json', encoding='utf-8') as f:
    dash = json.load(f)

with open('campaigns.json', encoding='utf-8') as f:
    camps = json.load(f)

# Build code -> agent lookup from dashboard_data
code_to_agent = {}
for ag, ag_data in dash.get('agents', {}).items():
    for d in ag_data.get('debtor_cards', {}).get('debtors', []):
        code = (d.get('debtor_code') or '').strip().upper()
        if code:
            code_to_agent[code] = ag  # last-write wins for shared codes

patched = 0
skipped = 0

for camp in camps.get('campaigns', []):
    for d in camp.get('debtors', []):
        code = (d.get('code') or '').strip().upper()
        if not d.get('agent'):
            agent = code_to_agent.get(code, '')
            d['agent'] = agent
            if agent:
                patched += 1
            else:
                skipped += 1

with open('campaigns.json', 'w', encoding='utf-8') as f:
    json.dump(camps, f, ensure_ascii=False, separators=(',', ':'))

print(f'Patched: {patched}, Skipped (unmapped): {skipped}')
