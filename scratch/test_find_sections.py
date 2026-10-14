from pathlib import Path
import re

file_path = Path(r"e:\PROJECTS\MULE GUARD\frontend\bank\investigator\investigations.html")
content = file_path.read_text(encoding="utf-8")

tbody_match = re.search(r'(<tbody[^>]*id="investigations-tbody"[^>]*>)([\s\S]*?)(</tbody>)', content)
if tbody_match:
    print(f"Found tbody! Length of inner: {len(tbody_match.group(2))}")
    print(f"Start tag: {tbody_match.group(1)}")
else:
    print("tbody NOT found")

script_match = re.search(r'<script>\s*// Investigations Queue mock database records[\s\S]*?</script>', content)
if script_match:
    print(f"Found mock script! Length: {len(script_match.group(0))}")
else:
    print("mock script NOT found")
