import os, re, json
from pathlib import Path

root = Path('.')
terms = [
    'MuleGuardStore.getAccounts',
    'MuleGuardStore.getTransactions',
    'MuleGuardStore.getAlerts',
    'MuleGuardStore.getCases',
    'MuleGuardStore.getDecisions',
    'MuleGuardStore.getWatchlist',
    'MuleGuardStore.getAuditLogs',
    'getDb()',
    "localStorage['muleguard_db']"
]

ignore = {'.git', '.venv', 'node_modules', '__pycache__', '.idea', '.vscode'}
results = {t: [] for t in terms}

for p in root.rglob('*'):
    if p.is_file() and not any(part in ignore for part in p.parts):
        try:
            txt = p.read_text(encoding='utf-8', errors='ignore')
            for i, line in enumerate(txt.splitlines(), 1):
                for t in terms:
                    if t in line:
                        results[t].append({
                            'file': str(p),
                            'line': i,
                            'snippet': line.strip()
                        })
        except:
            pass

print(json.dumps(results, indent=2))
