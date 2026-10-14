import os
import re
import json
from pathlib import Path

root = Path('.')
html_pages = list(Path('frontend').rglob('*.html'))
js_files = list(Path('frontend').rglob('*.js'))

print("=== AUDIT STEP 9J: ISOLATION & DEPENDENCY AUDIT ===")

# 1. Check sidebar links in all HTML files
print("\n[1] Network & Fraud Navigation Links in HTML files:")
for html in html_pages:
    content = html.read_text(encoding='utf-8', errors='ignore')
    links = re.findall(r'href="([^"]*(?:network|fraud|risk)[^"]*)"', content)
    if links:
        print(f"  {html}: {set(links)}")

# 2. Check all MuleGuardStore references in frontend
print("\n[2] MuleGuardStore occurrences in frontend:")
for f in html_pages + js_files:
    content = f.read_text(encoding='utf-8', errors='ignore')
    matches = re.findall(r'MuleGuardStore(?:\.[a-zA-Z0-9_]+)?', content)
    if matches:
        print(f"  {f} (count: {len(matches)}): {set(matches)}")

# 3. Check getDb() in frontend
print("\n[3] getDb() occurrences in frontend:")
for f in html_pages + js_files:
    content = f.read_text(encoding='utf-8', errors='ignore')
    matches = re.findall(r'\bgetDb\(\)', content)
    if matches:
        print(f"  {f} (count: {len(matches)})")

# 4. Check localStorage occurrences in frontend
print("\n[4] localStorage occurrences in frontend:")
for f in html_pages + js_files:
    content = f.read_text(encoding='utf-8', errors='ignore')
    matches = re.findall(r'localStorage(?:\[[^\]]+\]|\.[a-zA-Z0-9_]+|\.getItem\([^)]+\)|\.setItem\([^)]+\))', content)
    if matches:
        keys = set(matches)
        print(f"  {f}: {keys}")
