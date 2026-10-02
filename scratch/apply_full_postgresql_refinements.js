const fs = require('fs');
const path = require('path');

// Load authoritative PostgreSQL expanded synthetic DB
global.window = global;
require('../frontend/scripts/synthetic_db_expanded.js');
const pgDb = global.MuleGuardExpandedDB;

// ============================================================================
// 1. UPDATE ALERTS PAGES (Investigator & Compliance)
// ============================================================================
['frontend/bank/investigator/alerts.html', 'frontend/bank/compliance/alerts.html'].forEach(relPath => {
    const fullPath = path.resolve(__dirname, '..', relPath);
    if (!fs.existsSync(fullPath)) return;
    let content = fs.readFileSync(fullPath, 'utf8');

    // Remove any static rows inside or outside tbody
    content = content.replace(
        /(<tbody class="divide-y divide-\[#f1f5f9\]" id="alerts-tbody">)[\s\S]*?(<\/table>)/,
        '$1\n                                                        <!-- Rows rendered dynamically by renderAlerts() -->\n                                                </tbody>\n                                        $2'
    );

    // Replace static drawer placeholder text
    content = content.replace(/Apex Trading Ltd/g, 'Target Account');
    content = content.replace(/Apex Trading/g, 'Target Account');
    content = content.replace(/Alert triggered on account.*30-minute window\./g, 'Alert details will populate dynamically upon selecting an account.');

    // Replace entire staticAlertsFallback block with dynamic database mapping
    content = content.replace(
        /const staticAlertsFallback = \{[\s\S]*?\};\n\s*const alertsDb =[^;]*;/m,
        `const staticAlertsFallback = {};\n                const alertsDb = (window.MuleGuardStore) ? window.MuleGuardStore.getAlerts().reduce((acc, a) => {\n                        acc[a.id] = a;\n                        return acc;\n                }, {}) : (window.MuleGuardExpandedDB ? window.MuleGuardExpandedDB.alerts.reduce((acc, a) => { acc[a.id] = a; return acc; }, {}) : {});`
    );

    fs.writeFileSync(fullPath, content, 'utf8');
    console.log(`✔ Fully aligned ${relPath} to PostgreSQL alerts`);
});

// ============================================================================
// 2. UPDATE CASES PAGES (Investigator & Compliance)
// ============================================================================
['frontend/bank/investigator/cases.html', 'frontend/bank/compliance/cases.html'].forEach(relPath => {
    const fullPath = path.resolve(__dirname, '..', relPath);
    if (!fs.existsSync(fullPath)) return;
    let content = fs.readFileSync(fullPath, 'utf8');

    // Replace entire static casesDb / staticCasesFallback block with dynamic mapping
    content = content.replace(
        /\/\/ Cases database[\s\S]*?const casesDb = window\.MuleGuardStore[^;]*;/m,
        `// Dynamic cases database from PostgreSQL\n                const staticCasesFallback = {};\n                const casesDb = (window.MuleGuardStore) ? window.MuleGuardStore.getCases().reduce((acc, c) => {\n                        acc[c.id] = c;\n                        return acc;\n                }, {}) : (window.MuleGuardExpandedDB ? window.MuleGuardExpandedDB.cases.reduce((acc, c) => { acc[c.id] = c; return acc; }, {}) : {});`
    );

    fs.writeFileSync(fullPath, content, 'utf8');
    console.log(`✔ Fully aligned ${relPath} to PostgreSQL cases`);
});

// ============================================================================
// 3. UPDATE TRANSACTIONS PAGES (Investigator & Compliance)
// ============================================================================
['frontend/bank/investigator/transactions.html', 'frontend/bank/compliance/transactions.html'].forEach(relPath => {
    const fullPath = path.resolve(__dirname, '..', relPath);
    if (!fs.existsSync(fullPath)) return;
    let content = fs.readFileSync(fullPath, 'utf8');

    // Replace any remaining static placeholder in drawer
    content = content.replace(/Apex Trading Ltd/g, 'Target Account');
    content = content.replace(/Apex Trading/g, 'Target Account');
    content = content.replace(/Apex Trading Ltd initiated.*velocity ratios\./g, 'Transaction ledger details loaded dynamically from PostgreSQL.');

    fs.writeFileSync(fullPath, content, 'utf8');
    console.log(`✔ Cleaned transaction placeholders in ${relPath}`);
});

// ============================================================================
// 4. UPDATE ENTITIES PAGES (Investigator & Compliance)
// ============================================================================
['frontend/bank/investigator/entities.html', 'frontend/bank/compliance/entities.html'].forEach(relPath => {
    const fullPath = path.resolve(__dirname, '..', relPath);
    if (!fs.existsSync(fullPath)) return;
    let content = fs.readFileSync(fullPath, 'utf8');

    content = content.replace(/Apex Trading Ltd/g, 'Target Account');
    content = content.replace(/Apex Trading/g, 'Target Account');
    content = content.replace(/Orion Financial/g, 'Deepak Verma');
    content = content.replace(/Vertex Imports/g, 'Kishore Varma');
    content = content.replace(/Northstar Holdings/g, 'Prakash Chatterjee');
    content = content.replace(/Meridian Capital/g, 'Sri Venkateswara Kirana');
    content = content.replace(/Blackwood Assets/g, 'Naveen Goud');
    content = content.replace(/Atlas Global/g, 'Annapurna Provisions');
    content = content.replace(/Swift Logistics/g, 'Sai Krupa Medical');
    content = content.replace(/Phoenix Ventures/g, 'Subhash Nair');
    content = content.replace(/Vanguard Logistics/g, 'Santosh Hegde');

    fs.writeFileSync(fullPath, content, 'utf8');
    console.log(`✔ Cleaned entity placeholders in ${relPath}`);
});

// ============================================================================
// 5. UPDATE INVESTIGATIONS PAGES (Investigator & Compliance)
// ============================================================================
['frontend/bank/investigator/investigations.html', 'frontend/bank/compliance/investigations.html'].forEach(relPath => {
    const fullPath = path.resolve(__dirname, '..', relPath);
    if (!fs.existsSync(fullPath)) return;
    let content = fs.readFileSync(fullPath, 'utf8');

    content = content.replace(/Orion Fin/g, 'Deepak V');
    content = content.replace(/Meridian Cap/g, 'Priya S');
    content = content.replace(/edge-orion/g, 'edge-deepak');
    content = content.replace(/edge-meridian/g, 'edge-priya');
    content = content.replace(/edgeOrion/g, 'edgeDeepak');
    content = content.replace(/edgeMeridian/g, 'edgePriya');

    fs.writeFileSync(fullPath, content, 'utf8');
    console.log(`✔ Cleaned investigation nodes in ${relPath}`);
});

// ============================================================================
// 6. UPDATE FRAUD NETWORKS PAGES (Investigator & Compliance)
// ============================================================================
['frontend/bank/investigator/fraud_networks.html', 'frontend/bank/compliance/fraud_networks.html'].forEach(relPath => {
    const fullPath = path.resolve(__dirname, '..', relPath);
    if (!fs.existsSync(fullPath)) return;
    let content = fs.readFileSync(fullPath, 'utf8');

    // Replace static rows in networks-tbody with dynamic rendering
    const dynamicRenderNetworksScript = `
        function renderNetworks() {
                const tbody = document.getElementById('networks-tbody');
                if (!tbody) return;
                const networks = window.MuleGuardStore ? window.MuleGuardStore.getNetworks() : {};
                const list = Object.values(networks);
                if (list.length === 0) return;
                tbody.innerHTML = list.map(net => {
                        const statusBadgeClass = net.status === 'Critical' ? 'bg-red-50 text-red-700 border-red-200' :
                                (net.status === 'Flagged' ? 'bg-orange-50 text-orange-700 border-orange-200' : 'bg-blue-50 text-blue-700 border-blue-200');
                        return \`
                                <tr class="hover:bg-[#f0f7ff]/70 transition-colors duration-150 group cursor-pointer" data-net-id="\${net.id}" data-risk="\${net.score >= 90 ? 'Critical' : (net.score >= 70 ? 'High' : 'Medium')}" data-status="\${net.status}" data-type="\${net.type}" onclick="rowClickAction(event, '\${net.id}')">
                                        <td class="py-[18px] px-4 font-mono-technical text-[13px] text-secondary font-bold hover:underline transition-all duration-150 align-middle whitespace-nowrap case-id-cell">\${net.id}</td>
                                        <td class="py-[18px] px-4 font-headline-md text-[13px] text-on-surface font-bold align-middle">\${net.name}</td>
                                        <td class="py-[18px] px-4 font-body-md text-[13px] text-on-surface align-middle">\${net.type}</td>
                                        <td class="py-[18px] px-4 align-middle text-right whitespace-nowrap">
                                                <span class="font-mono-technical text-[12px] font-bold text-red-600 px-2 py-0.5 rounded bg-red-50 border border-red-200">\${net.score} / 100</span>
                                        </td>
                                        <td class="py-[18px] px-4 font-mono-technical text-[13px] text-on-surface text-right font-semibold align-middle whitespace-nowrap">\${net.totalValue}</td>
                                        <td class="py-[18px] px-4 font-mono-technical text-[13px] text-on-surface-variant text-right font-semibold align-middle whitespace-nowrap">\${net.members}</td>
                                        <td class="py-[18px] px-4 font-mono-technical text-[13px] text-on-surface-variant text-right font-semibold align-middle whitespace-nowrap">\${net.connectedCount}</td>
                                        <td class="py-[18px] px-4 font-body-md text-[13px] text-on-surface-variant align-middle whitespace-nowrap">\${net.lastActivity}</td>
                                        <td class="py-[18px] px-4 align-middle whitespace-nowrap">
                                                <span class="status-badge-cell px-2.5 py-0.5 rounded-full text-[11px] font-semibold border \${statusBadgeClass}">\${net.status}</span>
                                        </td>
                                        <td class="py-[18px] px-4 align-middle text-right whitespace-nowrap">
                                                <button class="inspect-btn text-[12px] font-bold text-secondary hover:text-secondary-container focus:outline-none inline-flex items-center gap-1 group/btn" onclick="openDetailDrawer('\${net.id}')">
                                                        Inspect <span class="inspect-arrow inline-block transition-transform duration-150">→</span>
                                                </button>
                                        </td>
                                </tr>
                        \`;
                }).join('');
                cacheDOMRows();
        }
    `;

    // Replace static rows
    content = content.replace(
        /(<tbody class="divide-y divide-\[#f1f5f9\]" id="networks-tbody">)[\s\S]*?(<\/tbody>)/,
        '$1\n                                                        <!-- Dynamically populated from PostgreSQL -->\n                                                $2'
    );

    // Insert renderNetworks logic
    if (!content.includes('function renderNetworks(')) {
        content = content.replace(
            /(let networksDb = window\.MuleGuardStore\.getNetworks\(\);)/,
            `$1\n${dynamicRenderNetworksScript}`
        );
        content = content.replace(
            /(window\.addEventListener\('DOMContentLoaded', \(\) => \{)/,
            '$1\n                        renderNetworks();'
        );
    }

    fs.writeFileSync(fullPath, content, 'utf8');
    console.log(`✔ Cleaned and dynamicized networks in ${relPath}`);
});

// ============================================================================
// 7. UPDATE DASHBOARD (Investigator)
// ============================================================================
{
    const fullPath = path.resolve(__dirname, '../frontend/bank/investigator/dashboard.html');
    if (fs.existsSync(fullPath)) {
        let content = fs.readFileSync(fullPath, 'utf8');

        // Replace lingering static rows in recent-cases-tbody
        content = content.replace(
            /(<tbody class="divide-y divide-\[#f1f5f9\]" id="recent-cases-tbody"[^>]*>)[\s\S]*?(<\/tbody>)/,
            '$1\n                                                        <!-- Rendered dynamically from PostgreSQL -->\n                                                $2'
        );

        content = content.replace(/Proxy Shell Agent \(Northstar\)/g, 'Priya Sharma (Mule Layering Node)');
        content = content.replace(/Orion Structuring Review/g, 'Deepak Verma Inflow Review');
        content = content.replace(/Phoenix Velocity Review/g, 'Prakash Chatterjee Sink Review');
        content = content.replace(/Phoenix Logistics/g, 'Prakash Chatterjee');

        fs.writeFileSync(fullPath, content, 'utf8');
        console.log(`✔ Cleaned and updated dashboard.html`);
    }
}

console.log("\nFull frontend PostgreSQL alignment finished!");
