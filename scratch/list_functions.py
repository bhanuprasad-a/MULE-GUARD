from pathlib import Path
import re

file_path = Path(r"e:\PROJECTS\MULE GUARD\frontend\bank\investigator\investigations.html")
content = file_path.read_text(encoding="utf-8")

script_match = re.search(r'(<script>\s*// Investigations Queue mock database records[\s\S]*?</script>)', content)
if script_match:
    script_text = script_match.group(1)
    functions = re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', script_text)
    print("Functions in script:", functions)
