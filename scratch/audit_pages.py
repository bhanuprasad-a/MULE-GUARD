import re
import os

pages = [
    'frontend/bank/compliance/alerts.html',
    'frontend/bank/compliance/high-risk-alerts.html',
    'frontend/bank/compliance/cases.html',
    'frontend/bank/compliance/escalated-cases.html',
    'frontend/bank/investigator/alerts.html',
    'frontend/bank/investigator/cases.html',
    'frontend/bank/investigator/watchlists.html',
]

patterns = [
    'MuleGuardStore.getAlerts',
    'MuleGuardStore.getCases',
    'MuleGuardStore.getWatchlist',
    'getDb()',
    'muleguard_db',
    'MuleGuardStore',
]

print("=== MULEGUARD STEP 9G STORE DEPENDENCY AUDIT ===")
total_matches = 0
for p in pages:
    print(f"\nPage: {p}")
    if not os.path.exists(p):
        print("  FILE NOT FOUND!")
        continue
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()

    # check script tags
    script_srcs = re.findall(r'<script\s+src=["\']([^"\']+)["\']', content)
    print(f"  External Scripts: {script_srcs}")

    for pat in patterns:
        matches = list(re.finditer(re.escape(pat), content))
        if matches:
            total_matches += len(matches)
            print(f"  [FOUND] {pat}: {len(matches)} occurrences")
            for m in matches[:3]:
                line_no = content[:m.start()].count('\n') + 1
                line_snippet = content.splitlines()[line_no - 1].strip()
                print(f"     Line {line_no}: {line_snippet}")

if total_matches == 0:
    print("\nAUDIT SUMMARY: 0 legacy store occurrences found across all 7 production pages! 100% clean PostgreSQL migration.")
else:
    print(f"\nAUDIT SUMMARY: {total_matches} occurrences remaining.")
