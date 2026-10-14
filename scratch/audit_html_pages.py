import os
import re

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

html_files = []
for root, dirs, files in os.walk(os.path.join(PROJECT_DIR, "frontend")):
    for f in files:
        if f.endswith(".html"):
            html_files.append(os.path.join(root, f))

print(f"Total HTML pages: {len(html_files)}")

for hp in sorted(html_files):
    rel = os.path.relpath(hp, PROJECT_DIR).replace("\\", "/")
    with open(hp, "r", encoding="utf-8") as f:
        content = f.read()

    title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else "No Title"

    scripts = re.findall(r'<script\s+src="([^"]+)"', content, re.IGNORECASE)
    scripts_str = ", ".join([os.path.basename(s) for s in scripts])

    # Check navigation links
    nav_links = re.findall(r'href="([^"]+\.html[^"]*)"', content, re.IGNORECASE)
    unique_links = len(set(nav_links))

    print(f"\nPage: {rel}")
    print(f"  Title: {title}")
    print(f"  Scripts: {scripts_str if scripts_str else 'None'}")
    print(f"  Nav targets ({unique_links}): {', '.join(sorted(list(set(nav_links)))[:5])}")
