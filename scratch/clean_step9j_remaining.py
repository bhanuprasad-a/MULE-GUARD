# Update frontend/bank/investigator/risk-analytics.html
with open('frontend/bank/investigator/risk-analytics.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if 'if (!summary) {' in line and 370 < i < 400:
        start_idx = i
    if 'if (!summary) return;' in line and 440 < i < 460:
        end_idx = i + 1

print('risk-analytics: start_idx =', start_idx, 'end_idx =', end_idx)
if start_idx is not None and end_idx is not None:
    replacement = [
        '                        if (!summary) {\n',
        '                                console.error("Failed to load risk summary from PostgreSQL backend.");\n',
        '                                const tbody = document.getElementById("risk-leaderboard-tbody");\n',
        '                                if (tbody) {\n',
        '                                        tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-on-surface-variant font-body-md">Unable to load risk summary from server. Please refresh or verify API connection.</td></tr>`;\n',
        '                                }\n',
        '                                return;\n',
        '                        }\n'
    ]
    new_lines = lines[:start_idx] + replacement + lines[end_idx:]
    with open('frontend/bank/investigator/risk-analytics.html', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print('Successfully updated risk-analytics.html')

# Update compliance fraud_networks.html (line 688)
with open('frontend/bank/compliance/fraud_networks.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'const networksDb = window.MuleGuardStore.getNetworks();' in line:
        lines[i] = '                let networksDb = {};\n'
        print('Updated compliance fraud_networks line', i)

with open('frontend/bank/compliance/fraud_networks.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

# Update investigator fraud_networks.html (renderNetworks dead function removal)
with open('frontend/bank/investigator/fraud_networks.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'const networks = window.MuleGuardStore ? window.MuleGuardStore.getNetworks() : {};' in line:
        print('Found legacy renderNetworks at line', i)
        # remove renderNetworks function
        start_fn = None
        end_fn = None
        for j in range(max(0, i-5), i):
            if 'function renderNetworks()' in lines[j]:
                start_fn = j
                break
        for k in range(i, min(len(lines), i+30)):
            if lines[k].strip() == '}' or lines[k].strip() == '});':
                end_fn = k + 1
                break
        if start_fn is not None and end_fn is not None:
            print('Removing lines', start_fn, 'to', end_fn)
            lines = lines[:start_fn] + lines[end_fn:]
            break

with open('frontend/bank/investigator/fraud_networks.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)
