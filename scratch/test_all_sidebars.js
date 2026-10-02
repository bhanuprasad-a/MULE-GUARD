const fs = require('fs');
const path = require('path');

const pages = [
    'frontend/bank/investigator/dashboard.html',
    'frontend/bank/investigator/investigations.html',
    'frontend/bank/investigator/transactions.html',
    'frontend/bank/investigator/entities.html',
    'frontend/bank/investigator/fraud_networks.html',
    'frontend/bank/investigator/alerts.html',
    'frontend/bank/investigator/cases.html',
    'frontend/bank/investigator/risk-analytics.html',
    'frontend/bank/investigator/watchlists.html'
];

console.log('=== INSPECTING ALL SIDEBAR LINKS IN ALL INVESTIGATOR PAGES ===\n');

pages.forEach(relPath => {
    const fullPath = path.join(__dirname, '..', relPath);
    if (!fs.existsSync(fullPath)) {
        console.error(`[FAIL] File missing: ${relPath}`);
        return;
    }
    
    const content = fs.readFileSync(fullPath, 'utf8');
    
    // Extract <aside id="sidebar-container"> ... </aside>
    const asideMatch = /<aside\s+id="sidebar-container"[^>]*>([\s\S]*?)<\/aside>/i.exec(content);
    console.log(`Page: ${relPath}`);
    if (!asideMatch) {
        console.log('  <aside id="sidebar-container"> NOT FOUND!');
        return;
    }
    
    const asideContent = asideMatch[1];
    // Find all <a ...> ... </a>
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
        console.log(`  - Text: "${inner}" | Href: "${href}" | Onclick: "${onclick}"`);
    }
    if (!foundLinks) {
        console.log('  (No static links - empty aside container, hydrated dynamically by auth-guard.js)');
    }
});
