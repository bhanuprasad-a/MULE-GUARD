from pathlib import Path
import re

file_path = Path(r"e:\PROJECTS\MULE GUARD\frontend\bank\investigator\investigations.html")
content = file_path.read_text(encoding="utf-8")

script_match = re.search(r'(<script>\s*// Investigations Queue mock database records[\s\S]*?</script>)', content)
if script_match:
    lines = script_match.group(1).splitlines()
    for i, line in enumerate(lines):
        if "function triggerDrawerAction" in line:
            print("\n".join(lines[i:i+70]))
            break
