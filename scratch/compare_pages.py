import re

files = [
    'frontend/bank/investigator/dashboard.html',
    'frontend/bank/investigator/alerts.html',
    'frontend/bank/investigator/risk-analytics.html',
    'frontend/bank/investigator/network-intelligence.html',
    'frontend/bank/investigator/watchlists.html'
]

for p in files:
    print('='*50)
    print(p)
    with open(p, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # CSS links
    css = re.findall(r'<link[^>]*href=["\']([^"\']+\.css)["\']', html)
    print('CSS:', css)
    
    # Scripts in head
    head_match = re.search(r'<head>(.*?)</head>', html, re.DOTALL)
    if head_match:
        scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', head_match.group(1))
        print('Head Scripts:', scripts)
    
    # Aside tag
    aside_full = re.search(r'(<aside[^>]*id=["\']sidebar-container["\'][^>]*>)(.*?)(</aside>)', html, re.DOTALL)
    if aside_full:
        content = aside_full.group(2).strip()
        print('Aside content length:', len(content), '| Has toggle btn:', 'sidebar-toggle-btn' in content, '| Has data-rendered-role:', 'data-rendered-role' in aside_full.group(1))
    else:
        print('Aside NOT FOUND!')
    
    # Main container after aside
    if aside_full:
        after_aside = html[aside_full.end():aside_full.end()+300]
        first_tag = re.search(r'<([a-zA-Z0-9]+)[^>]*class=["\']([^"\']+)["\'][^>]*>', after_aside)
        if first_tag:
            print('Post-aside element:', first_tag.group(1), '| class:', first_tag.group(2))
            
    # Bottom scripts
    bottom_scripts = re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', html, re.DOTALL)
    print('Inline script count:', len(bottom_scripts))
