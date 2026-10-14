import re
import os

pages = [
    'frontend/bank/compliance/dashboard.html',
    'frontend/bank/investigator/dashboard.html',
    'frontend/bank/compliance/reports.html',
    'frontend/internal/dashboard.html',
]

patterns = [
    r'MuleGuardStore\.getAccounts\(.*?\)',
    r'MuleGuardStore\.getTransactions\(.*?\)',
    r'MuleGuardStore\.getAlerts\(.*?\)',
    r'MuleGuardStore\.getCases\(.*?\)',
    r'MuleGuardStore\.getDecisions\(.*?\)',
    r'MuleGuardStore\.getWatchlist\(.*?\)',
    r'MuleGuardStore\.[a-zA-Z0-9_]+',
    r'getDb\(.*?\)',
    r'muleguard_db',
    r'MuleGuardExpandedDB',
    r'MuleGuardAPI\.[a-zA-Z0-9_]+',
]

print("=== MULEGUARD STEP 9I DASHBOARD & REPORT AUDIT ===")
for p in pages:
    print(f"\n=======================================================")
    print(f"AUDITING: {p}")
    print(f"=======================================================")
    if not os.path.exists(p):
        print("  FILE NOT FOUND!")
        continue
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()

    # Search patterns
    for pat in patterns:
        matches = list(re.finditer(pat, content))
        if matches:
            unique_matches = set(m.group(0) for m in matches)
            print(f"  [MATCH] Pattern: {pat} ({len(matches)} occurrences)")
            for u in sorted(unique_matches):
                count = sum(1 for m in matches if m.group(0) == u)
                print(f"     - {u} (count: {count})")

    # Search for <script> blocks
    scripts = re.findall(r'<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>', content)
    print(f"  Inline Script Blocks: {len(scripts)}")
