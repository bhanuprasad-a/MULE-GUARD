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

console.log('=== CHECKING INVESTIGATOR PAGES FOR SCRIPT & STATIC HREF ERRORS ===');

pages.forEach(relPath => {
    const fullPath = path.join(__dirname, '..', relPath);
    if (!fs.existsSync(fullPath)) {
        console.error(`[FAIL] File does not exist: ${relPath}`);
        return;
    }
    
    const content = fs.readFileSync(fullPath, 'utf8');
    
    // Check Intelligence section hrefs in static HTML
    const hrefMatches = [];
    const intelligenceSectionRegex = /<!--\s*Intelligence Group\s*-->[\s\S]*?<\/div>/gi;
    const match = intelligenceSectionRegex.exec(content);
    if (match) {
        const linksRegex = /<a\s+[^>]*href=["']([^"']*)["'][^>]*>/gi;
        let lMatch;
        while ((lMatch = linksRegex.exec(match[0])) !== null) {
            hrefMatches.push(lMatch[1]);
        }
    }
    
    console.log(`\nPage: ${relPath}`);
    console.log(`Static Intelligence Hrefs:`, hrefMatches.length ? hrefMatches : '(Dynamic/Hydrated by auth-guard)');
});
