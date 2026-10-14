import re
from pathlib import Path

file_path = Path(r"e:\PROJECTS\MULE GUARD\frontend\bank\investigator\investigations.html")
content = file_path.read_text(encoding="utf-8")

print(f"Original content length: {len(content)}")
print(f"Contains investigationsDb: {'investigationsDb' in content}")
print(f"Contains MG-20479: {'MG-20479' in content}")
