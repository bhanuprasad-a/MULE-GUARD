const fs = require('fs');
const path = require('path');

const compPages = [
    'frontend/bank/compliance/dashboard.html',
    'frontend/bank/compliance/escalated-cases.html',
    'frontend/bank/compliance/high-risk-alerts.html',
    'frontend/bank/compliance/decisions.html',
    'frontend/bank/compliance/reports.html',
    'frontend/bank/compliance/investigations.html',
    'frontend/bank/compliance/transactions.html',
    'frontend/bank/compliance/entities.html',
    'frontend/bank/compliance/fraud_networks.html',
    'frontend/bank/compliance/alerts.html',
    'frontend/bank/compliance/cases.html'
];

console.log('=== INSPECTING COMPLIANCE PAGES SIDEBAR LINKS ===\n');

compPages.forEach(relPath => {
    const fullPath = path.join(__dirname, '..', relPath);
    if (!fs.existsSync(fullPath)) return;
    
    const content = fs.readFileSync(fullPath, 'utf8');
    const asideMatch = /<aside\s+id="sidebar-container"[^>]*>([\s\S]*?)<\/aside>/i.exec(content);
    console.log(`Page: ${relPath}`);
    if (!asideMatch) {
        console.log('  <aside id="sidebar-container"> NOT FOUND!');
        return;
    }
    
    const asideContent = asideMatch[1];
    const linkRegex = /<a\s+([^>]*)>([\s\S]*?)<\/a>/gi;
    let match;
    let foundLinks = false;
    while ((match = linkRegex.exec(asideContent)) !== null) {
        foundLinks = true;
        const attrs = match[1];
        const inner = match[2].replace(/<[^>]*>/g, '').trim();
        const hrefMatch = /href=["']([^"']*)["']/i.exec(attrs);
        const onclickMatch = /onclick=["']([^"']*)["']/i.exec(attrs);
        const href = hrefMatch ? hrefMatch[1] : 'NONE';
        const onclick = onclickMatch ? onclickMatch[1] : 'NONE';
        if (href === '#' || inner.includes('Risk Analytics') || inner.includes('Network Intelligence') || inner.includes('Watchlists')) {
            console.log(`  - Text: "${inner}" | Href: "${href}" | Onclick: "${onclick}"`);
        }
    }
    if (!foundLinks) {
        console.log('  (No static links)');
    }
});
