import os

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

categories = {
    "backend_routers": [],
    "backend_services": [],
    "backend_core_db": [],
    "frontend_html_pages": [],
    "frontend_scripts": [],
    "frontend_styles": [],
    "ml_models_and_scripts": [],
    "scratch_verification_scripts": [],
    "scratch_migration_and_debug": [],
    "documentation": [],
    "config_and_build": [],
}

for root, dirs, files in os.walk(PROJECT_DIR):
    # skip .git, .venv, node_modules, __pycache__
    if any(p in root for p in [".git", ".venv", "node_modules", "__pycache__"]):
        continue
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), PROJECT_DIR).replace("\\", "/")
        if rel.startswith("app/api/"):
            categories["backend_routers"].append(rel)
        elif rel.startswith("app/services/"):
            categories["backend_services"].append(rel)
        elif rel.startswith("app/db/") or rel.startswith("app/core/"):
            categories["backend_core_db"].append(rel)
        elif rel.startswith("frontend/") and rel.endswith(".html"):
            categories["frontend_html_pages"].append(rel)
        elif rel.startswith("frontend/scripts/"):
            categories["frontend_scripts"].append(rel)
        elif rel.endswith(".css"):
            categories["frontend_styles"].append(rel)
        elif "model" in rel or "ml_" in rel or rel.startswith("data/"):
            categories["ml_models_and_scripts"].append(rel)
        elif rel.startswith("scratch/verify_"):
            categories["scratch_verification_scripts"].append(rel)
        elif rel.startswith("scratch/"):
            categories["scratch_migration_and_debug"].append(rel)
        elif rel.endswith(".md"):
            categories["documentation"].append(rel)
        else:
            categories["config_and_build"].append(rel)

print(f"Total categories summary:")
for cat, file_list in categories.items():
    print(f"  {cat}: {len(file_list)} files")
