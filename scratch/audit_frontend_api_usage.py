import os
import re

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

api_js_path = os.path.join(PROJECT_DIR, "frontend", "scripts", "api.js")
with open(api_js_path, "r", encoding="utf-8") as f:
    api_text = f.read()

# Extract method names from MuleGuardAPI
# pattern: methodName(...) { return this.request(...) }
methods = re.findall(r"(\w+)\s*\([^)]*\)\s*\{[\s\S]*?this\.request\((['\"][^'\"]+['\"])", api_text)

print(f"Total API methods in MuleGuardAPI: {len(methods)}")

frontend_files = []
for root, dirs, files in os.walk(os.path.join(PROJECT_DIR, "frontend")):
    for f in files:
        if f.endswith(".html") or f.endswith(".js"):
            frontend_files.append(os.path.join(root, f))

results = []
for m_name, path in methods:
    call_pattern = re.compile(rf"MuleGuardAPI\.{m_name}\b")
    callers = []
    for fp in frontend_files:
        rel = os.path.relpath(fp, PROJECT_DIR).replace("\\", "/")
        if rel == "frontend/scripts/api.js":
            continue
        try:
            with open(fp, "r", encoding="utf-8") as file:
                content = file.read()
                if call_pattern.search(content):
                    callers.append(rel)
        except Exception:
            pass
    results.append((m_name, path.strip("'\""), callers))

print(f"{'API METHOD':28} | {'BACKEND PATH':40} | {'CALLERS IN FRONTEND'}")
print("-" * 110)
for m_name, ep, callers in results:
    caller_str = ", ".join(callers) if callers else "UNUSED IN FRONTEND"
    print(f"{m_name:28} | {ep:40} | {caller_str}")
