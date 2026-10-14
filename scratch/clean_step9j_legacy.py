"""
MuleGuard Step 9J: Clean legacy store references from fraud_networks and risk-analytics.
"""

# 1. Update frontend/bank/compliance/fraud_networks.html
with open('frontend/bank/compliance/fraud_networks.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix head script typo
c = c.replace(
    '<script src="../../scripts/api.js"></script>`n        <script src="../../scripts/data-store.js"></script>',
    '<script src="../../scripts/api.js"></script>\n        <script src="../../scripts/data-store.js"></script>'
)

# Initialize networksDb dynamically
c = c.replace(
    '// Fraud Networks mock database\n        const networksDb = window.MuleGuardStore.getNetworks();',
    '// Fraud Networks database\n        let networksDb = {};'
)

# Update showNodeDetails to use nodeObj from currentlyRenderedNetworkId
old_node_details = """                function showNodeDetails(nodeId, label, role, risk) {
                        const infoBox = document.getElementById('graph-node-info');
                        if (!infoBox) return;

                        const db = window.MuleGuardStore ? window.MuleGuardStore.getAccounts() : null;
                        const acc = db ? db[nodeId] : null;
                        const statusText = acc ? acc.status : 'Normal';
                        const score = acc ? acc.riskScore : (risk === 'Critical' ? 95 : (risk === 'High' ? 82 : (risk === 'Medium' ? 62 : 20)));

                        let badgeColor = "bg-blue-50 text-blue-800 border-blue-200";
                        if (statusText === 'Blocked') badgeColor = "bg-slate-900 text-slate-300 border-slate-700";
                        else if (statusText === 'Flagged') badgeColor = "bg-red-50 text-red-700 border-red-200";
                        else if (statusText === 'Under Review') badgeColor = "bg-orange-50 text-orange-700 border-orange-200";

                        let triggersHtml = '';
                        if (acc && acc.triggers && acc.triggers.length > 0) {
                                triggersHtml = `
                                        <div class="mt-2 pt-2 border-t border-slate-800 text-[10px] space-y-1">
                                                <div class="font-bold text-slate-300 uppercase tracking-wider">Triggers:</div>
                                                ${acc.triggers.map(t => `<div class="text-red-400">• ${t}</div>`).join('')}
                                        </div>
                                `;
                        }"""

new_node_details = """                function showNodeDetails(nodeId, label, role, risk) {
                        const infoBox = document.getElementById('graph-node-info');
                        if (!infoBox) return;

                        const currNet = networksDb[currentlyRenderedNetworkId];
                        const nodeObj = (currNet && currNet.graphNodes) ? currNet.graphNodes.find(n => n.id === nodeId) : null;
                        const statusText = nodeObj ? (nodeObj.status || 'Normal') : 'Normal';
                        const score = nodeObj ? (nodeObj.score !== undefined ? nodeObj.score : (risk === 'Critical' ? 95 : (risk === 'High' ? 82 : (risk === 'Medium' ? 62 : 20)))) : (risk === 'Critical' ? 95 : (risk === 'High' ? 82 : (risk === 'Medium' ? 62 : 20)));

                        let badgeColor = "bg-blue-50 text-blue-800 border-blue-200";
                        if (statusText === 'Blocked') badgeColor = "bg-slate-900 text-slate-300 border-slate-700";
                        else if (statusText === 'Flagged') badgeColor = "bg-red-50 text-red-700 border-red-200";
                        else if (statusText === 'Under Review') badgeColor = "bg-orange-50 text-orange-700 border-orange-200";

                        let triggersHtml = '';
                        const triggersList = (nodeObj && Array.isArray(nodeObj.triggers)) ? nodeObj.triggers : [];
                        if (triggersList.length > 0) {
                                triggersHtml = `
                                        <div class="mt-2 pt-2 border-t border-slate-800 text-[10px] space-y-1">
                                                <div class="font-bold text-slate-300 uppercase tracking-wider">Triggers:</div>
                                                ${triggersList.map(t => `<div class="text-red-400">• ${t}</div>`).join('')}
                                        </div>
                                `;
                        }"""

c = c.replace(old_node_details, new_node_details)

# Remove MuleGuardStore fallback in loadNetworksData
c = c.replace(
    """                        } else if (rawNetworks && typeof rawNetworks === 'object' && Object.keys(rawNetworks).length > 0) {
                                networksDb = rawNetworks;
                        } else if (window.MuleGuardStore && window.MuleGuardStore.getNetworks) {
                                networksDb = window.MuleGuardStore.getNetworks() || {};
                        }""",
    """                        } else if (rawNetworks && typeof rawNetworks === 'object' && Object.keys(rawNetworks).length > 0) {
                                networksDb = rawNetworks;
                        }"""
)

with open('frontend/bank/compliance/fraud_networks.html', 'w', encoding='utf-8') as f:
    f.write(c)
print("Updated frontend/bank/compliance/fraud_networks.html")

# 2. Update frontend/bank/investigator/fraud_networks.html
with open('frontend/bank/investigator/fraud_networks.html', 'r', encoding='utf-8') as f:
    ci = f.read()

ci = ci.replace(
    '// Fraud Networks database\n                let networksDb = window.MuleGuardStore.getNetworks();',
    '// Fraud Networks database\n                let networksDb = {};'
)

# Remove unused renderNetworks() function that called MuleGuardStore.getNetworks()
old_render_networks = """        function renderNetworks() {
                const tbody = document.getElementById('networks-tbody');
                if (!tbody) return;
                const networks = window.MuleGuardStore ? window.MuleGuardStore.getNetworks() : {};
                const list = Object.values(networks);
                if (list.length === 0) return;
                tbody.innerHTML = list.map(net => {
                        const statusBadgeClass = net.status === 'Critical' ? 'bg-red-50 text-red-700 border-red-200' :
                                (net.status === 'Flagged' ? 'bg-orange-50 text-orange-700 border-orange-200' : 'bg-blue-50 text-blue-700 border-blue-200');
                        return `
                                <tr class="hover:bg-[#f0f7ff]/70 transition-colors duration-150 group cursor-pointer" data-net-id="${net.id}" data-risk="${net.score >= 90 ? 'Critical' : (net.score >= 70 ? 'High' : 'Medium')}" data-status="${net.status}" data-type="${net.type}" onclick="rowClickAction(event, '${net.id}')">
                                        <td class="py-[18px] px-4 font-mono-technical text-[13px] text-secondary font-bold hover:underline transition-all duration-150 align-middle whitespace-nowrap case-id-cell">${net.id}</td>
                                        <td class="py-[18px] px-4 font-headline-md text-[13px] text-on-surface font-bold align-middle">${net.name}</td>
                                        <td class="py-[18px] px-4 font-body-md text-[13px] text-on-surface align-middle">${net.type}</td>
                                        <td class="py-[18px] px-4 align-middle text-right whitespace-nowrap">
                                                <span class="font-mono-technical text-[12px] font-bold text-red-600 px-2 py-0.5 rounded bg-red-50 border border-red-200">${net.score} / 100</span>
                                        </td>
                                        <td class="py-[18px] px-4 font-mono-technical text-[13px] text-on-surface text-right font-semibold align-middle whitespace-nowrap">${net.totalValue}</td>
                                        <td class="py-[18px] px-4 font-mono-technical text-[13px] text-on-surface-variant text-right font-semibold align-middle whitespace-nowrap">${net.members}</td>
                                        <td class="py-[18px] px-4 font-mono-technical text-[13px] text-on-surface-variant text-right font-semibold align-middle whitespace-nowrap">${net.connectedCount}</td>
                                        <td class="py-[18px] px-4 align-middle text-center whitespace-nowrap">
                                                <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold border ${statusBadgeClass}">${net.status}</span>
                                        </td>
                                        <td class="py-[18px] px-4 align-middle text-right whitespace-nowrap" onclick="event.stopPropagation()">
                                                <button onclick="openDetailDrawer('${net.id}')" class="p-1 rounded text-on-surface-variant hover:text-primary hover:bg-slate-100 transition-colors" title="Investigate">
                                                        <span class="material-symbols-outlined text-[18px]">open_in_new</span>
                                                </button>
                                        </td>
                                </tr>
                        `;
                }).join('');
        }"""

ci = ci.replace(old_render_networks, "")

# Update showNodeDetails in investigator
ci = ci.replace(old_node_details, new_node_details)

# Remove MuleGuardStore fallback in loadNetworksData in investigator
ci = ci.replace(
    """                        } else if (rawNetworks && typeof rawNetworks === 'object' && Object.keys(rawNetworks).length > 0) {
                                networksDb = rawNetworks;
                        } else if (window.MuleGuardStore && window.MuleGuardStore.getNetworks) {
                                networksDb = window.MuleGuardStore.getNetworks() || {};
                        }""",
    """                        } else if (rawNetworks && typeof rawNetworks === 'object' && Object.keys(rawNetworks).length > 0) {
                                networksDb = rawNetworks;
                        }"""
)

with open('frontend/bank/investigator/fraud_networks.html', 'w', encoding='utf-8') as f:
    f.write(ci)
print("Updated frontend/bank/investigator/fraud_networks.html")

# 3. Update frontend/bank/investigator/risk-analytics.html
with open('frontend/bank/investigator/risk-analytics.html', 'r', encoding='utf-8') as f:
    cr = f.read()

# Replace if (!summary) fallback block with clean PostgreSQL-only handling
old_risk_fallback = """                        if (!summary) {
                                let accounts = (window.MuleGuardStore && window.MuleGuardStore.getAccounts) ? window.MuleGuardStore.getAccounts() : null;
                                if (!accounts || Object.keys(accounts).length === 0) {
                                        if (typeof window !== 'undefined' && window.MuleGuardExpandedDB && window.MuleGuardExpandedDB.accounts) {
                                                accounts = window.MuleGuardExpandedDB.accounts;
                                        }
                                }
                                const alerts = (window.MuleGuardStore && window.MuleGuardStore.getAlerts) ? window.MuleGuardStore.getAlerts() : (window.MuleGuardExpandedDB && window.MuleGuardExpandedDB.alerts ? window.MuleGuardExpandedDB.alerts : []);
                                if (accounts && Object.keys(accounts).length > 0) {
                                        const accountIds = Object.keys(accounts);
                                        let criticalCnt = 0, highCnt = 0, modCnt = 0, lowCnt = 0;
                                        let totalProb = 0;
                                        const leaderboard = accountIds.map(id => {
                                                const acc = accounts[id];
                                                const risk = (window.MuleGuardStore && window.MuleGuardStore.predictAccountRisk) ? window.MuleGuardStore.predictAccountRisk(id) : null;
                                        const prob = risk && typeof risk.probability === 'number' ? risk.probability : ((acc.riskScore || 0) / 100);
                                        const score = Math.round(prob * 100);
                                        totalProb += prob;
                                        let tier = 'Low';
                                        if (score >= 80) { tier = 'Critical'; criticalCnt++; }
                                        else if (score >= 60) { tier = 'High'; highCnt++; }
                                        else if (score >= 40) { tier = 'Moderate'; modCnt++; }
                                        else { lowCnt++; }
                                        return {
                                                id: id,
                                                name: acc.name,
                                                account_type: acc.type || 'Savings',
                                                balance: acc.balance || 0,
                                                status: acc.status || 'Normal',
                                                risk_score: score,
                                                risk_probability: prob,
                                                tier: tier,
                                                triggers: acc.triggers || []
                                        };
                                }).sort((a, b) => b.risk_score - a.risk_score);

                                const totalAccs = accountIds.length || 1;
                                summary = {
                                        total_accounts: totalAccs,
                                        high_risk_accounts: criticalCnt + highCnt,
                                        critical_accounts: criticalCnt,
                                        high_accounts: highCnt,
                                        moderate_accounts: modCnt,
                                        low_risk_accounts: lowCnt,
                                        active_alerts: alerts.length,
                                        active_cases: 8,
                                        avg_risk_probability: Math.round((totalProb / totalAccs) * 100),
                                        tier_distribution: [
                                                { tier: 'Critical', range: '80-100%', count: criticalCnt, percentage: Math.round((criticalCnt / totalAccs) * 100) },
                                                { tier: 'High', range: '60-79%', count: highCnt, percentage: Math.round((highCnt / totalAccs) * 100) },
                                                { tier: 'Moderate', range: '40-59%', count: modCnt, percentage: Math.round((modCnt / totalAccs) * 100) },
                                                { tier: 'Low', range: '0-39%', count: lowCnt, percentage: Math.round((lowCnt / totalAccs) * 100) }
                                        ],
                                        tier_counts: {
                                                Critical: criticalCnt,
                                                High: highCnt,
                                                Moderate: modCnt,
                                                Low: lowCnt
                                        },
                                        rule_triggers: [
                                                { id: 'R-VEL-1', name: 'Velocity Spike (Inbound Degree)', count: 14 },
                                                { id: 'R-HOLD-1', name: 'Short Holding Time Ratio', count: 12 },
                                                { id: 'R-NET-1', name: 'Suspicious Component Connection', count: 9 },
                                                { id: 'R-VAL-1', name: 'High-Value Shell Transfer', count: 8 },
                                                { id: 'R-CIRC-1', name: 'Circular Money Flow', count: 6 },
                                                { id: 'R-DORM-1', name: 'Dormant Account Activation', count: 5 }
                                        ],
                                        detection_sources: {
                                                combined: 14,
                                                ml_only: 6,
                                                rule_only: 3
                                        },
                                        leaderboard: leaderboard
                                };
                        }
                }"""

new_risk_fallback = """                        if (!summary) {
                                console.error('Failed to load risk summary from PostgreSQL backend.');
                                const tbody = document.getElementById('risk-leaderboard-tbody');
                                if (tbody) {
                                        tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-on-surface-variant font-body-md">Unable to load risk summary from server. Please refresh or verify API connection.</td></tr>`;
                                }
                                return;
                        }"""

cr = cr.replace(old_risk_fallback, new_risk_fallback)

# Format INR without MuleGuardStore
cr = cr.replace(
    """                                const formattedBal = window.MuleGuardStore && window.MuleGuardStore.formatINR 
                                        ? window.MuleGuardStore.formatINR(item.balance) 
                                        : `₹${(item.balance || 0).toLocaleString('en-IN')}`;""",
    """                                const formattedBal = `₹${Number(item.balance || 0).toLocaleString('en-IN')}`;"""
)

with open('frontend/bank/investigator/risk-analytics.html', 'w', encoding='utf-8') as f:
    f.write(cr)
print("Updated frontend/bank/investigator/risk-analytics.html")
