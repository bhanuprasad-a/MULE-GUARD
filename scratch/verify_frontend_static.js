const http = require('http');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://127.0.0.1:8000';

const PAGES = [
    { url: '/frontend/login.html', depth: 0 },
    { url: '/frontend/access-denied.html', depth: 0 },
    { url: '/frontend/three-demo.html', depth: 0 },
    { url: '/frontend/internal/dashboard.html', depth: 1 },
    { url: '/frontend/bank/compliance/dashboard.html', depth: 2 },
    { url: '/frontend/bank/compliance/entities.html', depth: 2 },
    { url: '/frontend/bank/compliance/alerts.html', depth: 2 },
    { url: '/frontend/bank/compliance/cases.html', depth: 2 },
    { url: '/frontend/bank/compliance/decisions.html', depth: 2 },
    { url: '/frontend/bank/compliance/high-risk-alerts.html', depth: 2 },
    { url: '/frontend/bank/compliance/escalated-cases.html', depth: 2 },
    { url: '/frontend/bank/compliance/fraud_networks.html', depth: 2 },
    { url: '/frontend/bank/compliance/investigations.html', depth: 2 },
    { url: '/frontend/bank/compliance/reports.html', depth: 2 },
    { url: '/frontend/bank/compliance/transactions.html', depth: 2 },
    { url: '/frontend/bank/investigator/dashboard.html', depth: 2 },
    { url: '/frontend/bank/investigator/entities.html', depth: 2 },
    { url: '/frontend/bank/investigator/alerts.html', depth: 2 },
    { url: '/frontend/bank/investigator/cases.html', depth: 2 },
    { url: '/frontend/bank/investigator/fraud_networks.html', depth: 2 },
    { url: '/frontend/bank/investigator/investigations.html', depth: 2 },
    { url: '/frontend/bank/investigator/risk-analytics.html', depth: 2 },
    { url: '/frontend/bank/investigator/transactions.html', depth: 2 },
    { url: '/frontend/bank/investigator/watchlists.html', depth: 2 }
];

function fetchUrl(urlPath) {
    return new Promise((resolve, reject) => {
        http.get(BASE_URL + urlPath, (res) => {
            let data = '';
            res.on('data', (chunk) => { data += chunk; });
            res.on('end', () => {
                resolve({ statusCode: res.statusCode, body: data });
            });
        }).on('error', (err) => reject(err));
    });
}

async function runStaticVerification() {
    console.log("====================================================");
    console.log("MULEGUARD FRONTEND STATIC & DOM VERIFICATION");
    console.log("====================================================\n");

    let allPassed = true;
    let pageErrors = [];

    // 1. Verify HTTP 200 & Script import paths for all HTML pages
    for (const page of PAGES) {
        try {
            const res = await fetchUrl(page.url);
            if (res.statusCode !== 200) {
                allPassed = false;
                pageErrors.push(`[${page.url}] HTTP status ${res.statusCode} (expected 200)`);
                continue;
            }

            const prefix = page.depth === 0 ? 'scripts/' : (page.depth === 1 ? '../scripts/' : '../../scripts/');
            const expectedApiScript = `${prefix}api.js`;
            const expectedDataStoreScript = `${prefix}data-store.js`;

            // Check if page references api.js or data-store.js with broken depth
            const scriptMatches = res.body.match(/src=["']([^"']*scripts\/[^"']*)["']/g) || [];
            for (const m of scriptMatches) {
                const src = m.replace(/src=["']/, '').replace(/["']$/, '');
                if (src.includes('api.js') && !src.includes(expectedApiScript)) {
                    allPassed = false;
                    pageErrors.push(`[${page.url}] Incorrect relative path for api.js: found "${src}", expected "${expectedApiScript}"`);
                }
                if (src.includes('data-store.js') && !src.includes(expectedDataStoreScript)) {
                    allPassed = false;
                    pageErrors.push(`[${page.url}] Incorrect relative path for data-store.js: found "${src}", expected "${expectedDataStoreScript}"`);
                }
            }

            // Verify api.js comes before data-store.js if both are present
            const apiIdx = res.body.indexOf('api.js');
            const dataStoreIdx = res.body.indexOf('data-store.js');
            if (apiIdx !== -1 && dataStoreIdx !== -1 && apiIdx > dataStoreIdx) {
                allPassed = false;
                pageErrors.push(`[${page.url}] api.js is loaded AFTER data-store.js`);
            }

            console.log(`✔ OK [200]: ${page.url}`);
        } catch (e) {
            allPassed = false;
            pageErrors.push(`[${page.url}] Fetch failed: ${e.message}`);
        }
    }

    // 2. Verify frontend/scripts/api.js methods
    const apiJsPath = path.join(__dirname, '..', 'frontend', 'scripts', 'api.js');
    const apiJsContent = fs.readFileSync(apiJsPath, 'utf8');

    const requiredMethods = [
        'getKPIs',
        'getAccounts',
        'getAccount',
        'getAccountTransactions',
        'getAccountRisk',
        'getAlerts',
        'getCase',
        'getCases',
        'getAuditLogs',
        'getTransactions',
        'ingestTransaction'
    ];

    console.log("\n--- Checking frontend/scripts/api.js ---");
    for (const method of requiredMethods) {
        if (!apiJsContent.includes(method)) {
            allPassed = false;
            pageErrors.push(`[api.js] Missing method: ${method}`);
            console.log(` ❌ MISSING: ${method}`);
        } else {
            console.log(` ✔ FOUND: ${method}`);
        }
    }

    // 3. Verify compliance dashboard KPI integration
    console.log("\n--- Checking Compliance Dashboard KPI Integration ---");
    const compDashPath = path.join(__dirname, '..', 'frontend', 'bank', 'compliance', 'dashboard.html');
    const compDashContent = fs.readFileSync(compDashPath, 'utf8');
    if (compDashContent.includes('MuleGuardAPI.getKPIs()')) {
        console.log(" ✔ Compliance dashboard calls MuleGuardAPI.getKPIs()");
    } else {
        allPassed = false;
        pageErrors.push("Compliance dashboard missing MuleGuardAPI.getKPIs() integration");
        console.log(" ❌ MISSING: MuleGuardAPI.getKPIs() in compliance dashboard");
    }

    // 4. Verify transaction simulator calls ingestTransaction
    console.log("\n--- Checking Transaction Simulator ---");
    const simPath = path.join(__dirname, '..', 'frontend', 'scripts', 'transaction-simulator.js');
    const simContent = fs.readFileSync(simPath, 'utf8');
    if (simContent.includes('window.MuleGuardStore.ingestTransaction')) {
        console.log(" ✔ Transaction simulator calls window.MuleGuardStore.ingestTransaction()");
    } else {
        allPassed = false;
        pageErrors.push("Transaction simulator missing window.MuleGuardStore.ingestTransaction() call");
        console.log(" ❌ MISSING: window.MuleGuardStore.ingestTransaction() in transaction-simulator.js");
    }

    // 5. Verify data-store.js contains ingestTransaction implementation
    console.log("\n--- Checking data-store.js ingestTransaction ---");
    const storePath = path.join(__dirname, '..', 'frontend', 'scripts', 'data-store.js');
    const storeContent = fs.readFileSync(storePath, 'utf8');
    if (storeContent.includes('ingestTransaction: function')) {
        console.log(" ✔ data-store.js contains ingestTransaction: function implementation");
    } else {
        allPassed = false;
        pageErrors.push("data-store.js missing ingestTransaction implementation");
        console.log(" ❌ MISSING: ingestTransaction in data-store.js");
    }

    console.log("\n====================================================");
    if (allPassed) {
        console.log("FRONTEND STATIC VERIFICATION: PASS");
    } else {
        console.log("FRONTEND STATIC VERIFICATION: FAIL");
        console.log("Failures:");
        pageErrors.forEach(err => console.log(` - ${err}`));
    }
    console.log("====================================================\n");

    process.exit(allPassed ? 0 : 1);
}

runStaticVerification();
