const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const pages = [
    'frontend/bank/investigator/dashboard.html',
    'frontend/bank/investigator/alerts.html',
    'frontend/bank/investigator/risk-analytics.html',
    'frontend/bank/investigator/network-intelligence.html',
    'frontend/bank/investigator/watchlists.html'
];

pages.forEach(p => {
    console.log('='*40);
    console.log('Testing execution for:', p);
    const html = fs.readFileSync(path.join(ROOT, p), 'utf-8');
    
    // Check if there are any unhandled errors when running scripts in order
    // Let's extract scripts
    const headScripts = [];
    const srcMatches = html.matchAll(/<script[^>]*src=["']([^"']+)["'][^>]*>/gi);
    for (const m of srcMatches) {
        headScripts.push({ type: 'src', path: m[1] });
    }
    
    const inlineMatches = html.matchAll(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/gi);
    const inlineScripts = [];
    for (const m of inlineMatches) {
        inlineScripts.push({ type: 'inline', content: m[1] });
    }
    
    console.log('  External scripts:', headScripts.map(s => s.path));
    console.log('  Inline script count:', inlineScripts.length);
});
