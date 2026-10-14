with open("frontend/bank/investigator/transactions.html", "r", encoding="utf-8") as f:
    text = f.read()

import re
scripts = re.findall(r"<script[^>]*>(.*?)</script>", text, re.DOTALL)
print(f"Found {len(scripts)} script blocks.")
for idx, s in enumerate(scripts):
    print(f"\n--- Script {idx+1} (length {len(s)}) ---")
    lines = s.strip().split("\n")
    print(f"Starts: {lines[0][:80]}")
    for l in lines:
        if "tbody" in l or "render" in l or "transactionsDb" in l:
            print("  MATCH:", l.strip()[:100])
