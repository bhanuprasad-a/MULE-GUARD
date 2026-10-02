import re, glob

files = glob.glob('frontend/bank/investigator/*.html')
for f in sorted(files):
    with open(f, 'r', encoding='utf-8') as fp:
        content = fp.read()
    aside_m = re.search(r'<aside[^>]*id=["\']sidebar-container["\'][^>]*>(.*?)</aside>', content, re.DOTALL)
    if aside_m:
        inside = aside_m.group(1).strip()
        has_toggle = 'sidebar-toggle' in inside
        has_nav = '<nav' in inside
        print(f'{f:50} | len={len(inside):5} | has_toggle={has_toggle} | has_nav={has_nav}')
    else:
        print(f'{f:50} | NO ASIDE')
