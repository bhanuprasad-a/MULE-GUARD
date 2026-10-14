import re
from pathlib import Path

target = Path(r'e:/PROJECTS/MULE GUARD/frontend/bank/investigator/investigations.html')
content = target.read_text(encoding='utf-8')
print('Read original, length:', len(content))
