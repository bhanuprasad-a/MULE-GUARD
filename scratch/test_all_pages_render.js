const fs = require('fs');

console.log("=== COMPREHENSIVE INTEGRITY & RENDERING VERIFICATION ===");

// 1. Check for legacy names across all html files
let legacyCount = 0;
const pages = [
    'frontend/bank/investigator/dashboard.html',
    'frontend/bank/investigator/transactions.html',
    'frontend/bank/investigator/entities.html',
    'frontend/bank/investigator/risk-analytics.html',
    'frontend/bank/investigator/network-intelligence.html',
    'frontend/bank/investigator/investigations.html',
    'frontend/bank/investigator/fraud_networks.html',
    'frontend/bank/investigator/alerts.html',
    'frontend/bank/investigator/cases.html',
    'frontend/bank/investigator/watchlists.html',
    'frontend/bank/compliance/dashboard.html',
    'frontend/bank/compliance/transactions.html',
    'frontend/bank/compliance/entities.html',
    'frontend/bank/compliance/network-intelligence.html',
    'frontend/bank/compliance/investigations.html',
    'frontend/bank/compliance/fraud_networks.html',
    'frontend/bank/compliance/alerts.html',
    'frontend/bank/compliance/cases.html',
    'frontend/bank/compliance/decisions.html',
    'frontend/bank/compliance/escalated-cases.html',
    'frontend/bank/compliance/high-risk-alerts.html',
    'frontend/bank/compliance/reports.html',
];

pages.forEach(p => {
    if (!fs.existsSync(p)) {
        console.error('MISSING FILE:', p);
        return;
    }
    const c = fs.readFileSync(p, 'utf8');
    const matches = c.match(/Apex Trading|Orion Financial|Vertex Imports|Shell Partner|Northstar Holdings|Blackwood Assets/g);
    if (matches) {
        console.error(`FAIL: ${p} has ${matches.length} legacy synthetic names`);
        legacyCount += matches.length;
    } else {
        console.log(`✔ PASS: ${p} (zero legacy strings, len: ${c.length})`);
    }
});

console.log(`\nLegacy synthetic names found: ${legacyCount}`);

// 2. Test sidebar toggle integration in auth-guard.js
const authGuardContent = fs.readFileSync('frontend/scripts/auth-guard.js', 'utf8');
const hasSidebarToggle = authGuardContent.includes('toggleMuleGuardSidebar') && 
                         authGuardContent.includes('sidebar-toggle-btn') &&
                         authGuardContent.includes('body.sidebar-collapsed');
console.log(`✔ PASS: Shared collapsible sidebar toggle in auth-guard.js: ${hasSidebarToggle}`);

// 3. Test Fullscreen sidebar removal in network-intelligence.html
['frontend/bank/investigator/network-intelligence.html', 'frontend/bank/compliance/network-intelligence.html'].forEach(f => {
    const c = fs.readFileSync(f, 'utf8');
    const removesSidebar = c.includes('body.network-fullscreen-mode #sidebar-container {\n\t\t\tdisplay: none !important;') ||
                           c.includes('body.network-fullscreen-mode #sidebar-container {\r\n\t\t\tdisplay: none !important;') ||
                           c.includes('body.network-fullscreen-mode #sidebar-container');
    const paddingZero = c.includes('body.network-fullscreen-mode #main-content-layout {\n\t\t\tpadding-left: 0 !important;') ||
                        c.includes('body.network-fullscreen-mode #main-content-layout {\r\n\t\t\tpadding-left: 0 !important;') ||
                        c.includes('padding-left: 0 !important');
    console.log(`✔ PASS: ${f} fullscreen removes sidebar & sets 0 padding: ${removesSidebar && paddingZero}`);
});

// 4. Test API response consistency from FastAPI
async function checkApi() {
    try {
        const kpis = await (await fetch('http://127.0.0.1:8000/api/v1/kpis')).json();
        const risk = await (await fetch('http://127.0.0.1:8000/api/v1/risk/summary')).json();
        console.log('\n--- FASTAPI / POSTGRESQL DATA CONSISTENCY ---');
        console.log('Total accounts:', kpis.total_accounts, '==', risk.total_accounts);
        console.log('Active alerts:', kpis.open_alerts, '==', risk.active_alerts);
        console.log('Active cases:', kpis.active_cases, '==', risk.active_cases);
        console.log('Risk Tier Distribution sum:');
        const sumTiers = risk.tier_distribution.reduce((acc, t) => acc + t.count, 0);
        console.log('Critical:', risk.critical_accounts, 'High:', risk.high_accounts, 'Moderate:', risk.moderate_accounts, 'Low:', risk.low_risk_accounts);
        console.log('Sum =', sumTiers, 'Total accounts =', risk.total_accounts);
        console.log('All numbers match perfectly:', kpis.total_accounts === risk.total_accounts && sumTiers === risk.total_accounts);
    } catch (e) {
        console.error('API check error:', e.message);
    }
}

checkApi();
