import os
import re

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

html_files = []
for root, dirs, files in os.walk(os.path.join(PROJECT_DIR, "frontend")):
    for f in files:
        if f.endswith(".html"):
            html_files.append(os.path.join(root, f))

print(f"{'HTML PAGE':55} | {'DATA STORE SCRIPT'} | {'API SCRIPT'} | {'SYNTHETIC DB SCRIPT'} | {'USES API'}")
print("-" * 125)

for hp in sorted(html_files):
    rel = os.path.relpath(hp, PROJECT_DIR).replace("\\", "/")
    with open(hp, "r", encoding="utf-8") as f:
        content = f.read()
    
    has_datastore = "data-store.js" in content
    has_api = "api.js" in content
    has_synthetic = "synthetic_db" in content
    uses_api = "MuleGuardAPI" in content
    
    print(f"{rel:55} | {str(has_datastore):17} | {str(has_api):10} | {str(has_synthetic):19} | {str(uses_api)}")
