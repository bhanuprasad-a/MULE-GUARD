import re

for filepath in ['frontend/bank/investigator/entities.html', 'frontend/bank/compliance/entities.html']:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update comment
    content = content.replace('<!-- Populated dynamically from PostgreSQL via MuleGuardStore -->', '<!-- Populated dynamically from PostgreSQL via MuleGuardAPI -->')

    # 2. Replace static entitiesDb with dynamic DB + cacheDOMRows + renderEntitiesTable
    db_pattern = re.compile(r'// Entities mock intelligence database[\s\S]*?const entitiesDb = \{[\s\S]*?\n\s*\};', re.MULTILINE)
    
    dyn_code = '''// Dynamic entities database populated from PostgreSQL via MuleGuardAPI
                let entitiesDb = {};

                function cacheDOMRows() {
                        cachedRows = [];
                        const rows = document.querySelectorAll('#entities-tbody tr[data-entity-id]');
                        rows.forEach(tr => {
                                const id = tr.getAttribute('data-entity-id');
                                const dbItem = entitiesDb[id];
                                if (dbItem) {
                                        cachedRows.push({
                                                id: id.toLowerCase(),
                                                name: dbItem.name.toLowerCase(),
                                                type: dbItem.type.toLowerCase(),
                                                risk: dbItem.riskTier,
                                                status: dbItem.status,
                                                element: tr
                                        });
                                }
                        });
                }

                async function renderEntitiesTable() {
                        const tbody = document.getElementById('entities-tbody');
                        if (!tbody) return;

                        try {
                                const accounts = await MuleGuardAPI.getAccounts({ limit: 500 });
                                entitiesDb = {};

                                if (!accounts || accounts.length === 0) {
                                        tbody.innerHTML = `<tr><td colspan="9" class="py-8 text-center text-on-surface-variant font-body-md text-[13px]">No entities found in PostgreSQL database.</td></tr>`;
                                        cachedRows = [];
                                        recountSummaryCards();
                                        return;
                                }

                                tbody.innerHTML = accounts.map(acc => {
                                        const accId = acc.id;
                                        const name = acc.name || 'Account Holder';
                                        const type = acc.account_type || 'Savings';
                                        const balanceNum = Number(acc.balance || 0);
                                        const formattedBal = '₹' + balanceNum.toLocaleString('en-IN');
                                        const status = acc.status || 'Normal';

                                        // Baseline risk level heuristic prior to drawer inspection (which queries backend XGBoost)
                                        let initialScore = status === 'Critical' ? 92 : (status === 'Blocked' ? 90 : (status === 'Flagged' ? 76 : (status === 'Under Review' ? 58 : 18)));
                                        let riskTier = initialScore >= 80 ? 'Critical' : (initialScore >= 60 ? 'High' : (initialScore >= 40 ? 'Medium' : 'Low'));

                                        const riskColor = riskTier === 'Critical' ? 'text-red-600 bg-red-50 border-red-200' :
                                                (riskTier === 'High' ? 'text-orange-600 bg-orange-50 border-orange-200' :
                                                (riskTier === 'Medium' ? 'text-yellow-600 bg-yellow-50 border-yellow-200' : 'text-blue-600 bg-blue-50 border-blue-200'));

                                        const statusBadgeClass = status === 'Blocked' ? 'bg-red-50 text-red-700 border-red-200' :
                                                (status === 'Flagged' || status === 'Critical' ? 'bg-orange-50 text-orange-700 border-orange-200' :
                                                (status === 'Under Review' ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-green-50 text-green-700 border-green-200'));

                                        entitiesDb[accId] = {
                                                id: accId,
                                                name: name,
                                                type: type,
                                                balance: formattedBal,
                                                balanceNumeric: balanceNum,
                                                score: initialScore,
                                                riskTier: riskTier,
                                                transactions: 0,
                                                connectedCount: 2,
                                                lastActivity: 'Recent',
                                                status: status,
                                                summary: `${name} holds a ${type} account (${accId}) with current balance ${formattedBal}. Account state is ${status}.`,
                                                indicators: [
                                                        `${type} account verified`,
                                                        `Current status: ${status}`,
                                                        balanceNum > 100000 ? 'High balance tier' : 'Standard balance tier'
                                                ],
                                                connectedEntities: ['Counterparty A', 'Counterparty B', 'None', 'None'],
                                                riskExplanation: `Account status is currently ${status}. Real-time risk scoring is evaluated via backend PostgreSQL XGBoost service.`,
                                                notes: `Account opened: ${acc.opened_at ? new Date(acc.opened_at).toLocaleDateString() : 'N/A'}`
                                        };

                                        return `
                                                <tr class="hover:bg-[#f0f7ff]/70 transition-colors duration-150 group cursor-pointer" data-entity-id="${accId}" data-risk="${riskTier}" data-status="${status}" data-type="${type.toLowerCase()}" onclick="rowClickAction(event, '${accId}')">
                                                        <td class="py-3.5 px-4 font-mono-technical text-[13px] text-secondary font-bold hover:underline transition-all duration-150">${accId}</td>
                                                        <td class="py-3.5 px-4 font-headline-md text-[13px] text-on-surface font-bold">${name}</td>
                                                        <td class="py-3.5 px-4 font-body-md text-[13px] text-on-surface">${type}</td>
                                                        <td class="py-3.5 px-4 text-right">
                                                                <span class="entity-score-badge font-mono-technical text-[12px] font-bold px-2 py-0.5 rounded border ${riskColor}">${initialScore} / 100</span>
                                                        </td>
                                                        <td class="py-3.5 px-4 font-mono-technical text-[13px] text-on-surface text-right" id="tx-count-${accId}">—</td>
                                                        <td class="py-3.5 px-4 font-mono-technical text-[13px] text-on-surface-variant text-right">2</td>
                                                        <td class="py-3.5 px-4 font-mono-technical text-[12px] text-on-surface-variant">Recent</td>
                                                        <td class="py-3.5 px-4">
                                                                <span class="status-badge-cell px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${statusBadgeClass}">${status}</span>
                                                        </td>
                                                        <td class="py-3.5 px-4 text-right">
                                                                <button class="inspect-btn text-[12px] font-bold text-secondary hover:text-secondary-container focus:outline-none inline-flex items-center gap-1 group/btn" onclick="openDetailDrawer('${accId}')">
                                                                        Inspect <span class="inspect-arrow inline-block transition-transform duration-150">→</span>
                                                                </button>
                                                        </td>
                                                </tr>
                                        `;
                                }).join('');

                                cacheDOMRows();
                                recountSummaryCards();
                        } catch (err) {
                                console.error('Failed to load accounts from PostgreSQL:', err);
                                tbody.innerHTML = `<tr><td colspan="9" class="py-8 text-center text-risk-high font-body-md text-[13px]">Failed to load accounts from PostgreSQL: ${err.message}</td></tr>`;
                        }
                }'''

    content, n_sub = db_pattern.subn(dyn_code, content)
    print(f'{filepath} db_pattern replaced: {n_sub}')

    # 3. Replace renderMlFeatures with backend PostgreSQL risk fetcher
    ml_pattern = re.compile(r'// Helper to render ML features container[\s\S]*?window\.renderMlFeatures\(accId\);', re.MULTILINE)

    backend_risk_code = '''// Query PostgreSQL backend XGBoost risk API
                        async function renderBackendAccountRisk(targetAccId) {
                            const featuresContainer = document.getElementById('drawer-ml-features-container');
                            if (!featuresContainer) return;

                            featuresContainer.innerHTML = `
                                <div class="p-3 text-center text-on-surface-variant text-[12px] font-mono-technical">
                                    <span class="inline-block animate-spin mr-1">↻</span> Querying PostgreSQL XGBoost Model...
                                </div>
                            `;

                            try {
                                const riskData = await MuleGuardAPI.getAccountRisk(targetAccId);
                                const prob = Number(riskData.risk_probability || 0);
                                const score = Number(riskData.risk_score || 0);
                                const prediction = riskData.prediction || 0;
                                const threshold = 0.50;

                                let riskTier = 'Low';
                                let badgeClass = 'bg-green-50 text-green-700';
                                let barClass = 'bg-green-600';
                                let scoreColor = 'text-green-600';

                                if (prob >= 0.70) {
                                    riskTier = 'Critical';
                                    badgeClass = 'bg-red-50 text-red-700';
                                    barClass = 'bg-risk-high';
                                    scoreColor = 'text-red-600';
                                } else if (prob >= threshold) {
                                    riskTier = 'High';
                                    badgeClass = 'bg-orange-50 text-orange-700';
                                    barClass = 'bg-orange-500';
                                    scoreColor = 'text-orange-600';
                                } else if (prob >= 0.30) {
                                    riskTier = 'Medium';
                                    badgeClass = 'bg-yellow-50 text-yellow-700';
                                    barClass = 'bg-yellow-500';
                                    scoreColor = 'text-yellow-600';
                                }

                                const drawerScoreEl = document.getElementById('drawer-risk-score');
                                if (drawerScoreEl) {
                                    drawerScoreEl.textContent = `${Math.round(score)} / 100`;
                                    drawerScoreEl.className = `font-mono-technical text-[12px] font-bold px-2 py-0.5 rounded border ${scoreColor} ${badgeClass}`;
                                }

                                if (entitiesDb[targetAccId]) {
                                    entitiesDb[targetAccId].score = Math.round(score);
                                    entitiesDb[targetAccId].riskTier = riskTier;
                                }

                                featuresContainer.innerHTML = `
                                        <!-- Backend PostgreSQL XGBoost Model Risk Indicator -->
                                        <div class="border-b border-outline-variant/20 pb-2.5 mb-2.5">
                                                <div class="flex justify-between items-center mb-1 select-none">
                                                        <span class="text-on-surface-variant font-bold text-[11px]">Backend XGBoost Suspicious Probability:</span>
                                                        <span class="font-mono-technical font-extrabold ${scoreColor} text-[13px]">${(prob * 100).toFixed(1)}%</span>
                                                </div>
                                                <div class="w-full bg-surface-container-low rounded-full h-2 border border-outline-variant/30 overflow-hidden mb-2">
                                                        <div class="h-full rounded-full ${barClass}" style="width: ${Math.min(100, Math.max(2, (prob * 100))).toFixed(1)}%"></div>
                                                </div>
                                                <div class="flex justify-between items-center text-[10px] text-on-surface-variant select-none">
                                                        <span>Model: ${riskData.model ? riskData.model.name : 'muleguard_postgres_model'} (26 features)</span>
                                                        <span class="font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${badgeClass}">${riskTier} Risk</span>
                                                </div>
                                                <div class="mt-2 text-[10px] text-on-surface-variant flex items-center justify-between select-none">
                                                        <span>Decision: <b class="${prediction === 1 ? 'text-risk-high' : 'text-risk-low'}">${prediction === 1 ? 'Mule Account (Flagged)' : 'Legitimate Account'}</b></span>
                                                        <span>Risk Score: <b>${score.toFixed(1)} / 100</b></span>
                                                </div>
                                        </div>
                                `;
                            } catch (err) {
                                console.error('Failed to query backend risk API:', err);
                                featuresContainer.innerHTML = `
                                        <div class="p-2.5 rounded bg-amber-50 border border-amber-200 text-amber-800 text-[11px] font-body-md">
                                                PostgreSQL Risk API response: ${err.message}
                                        </div>
                                `;
                            }
                        }

                        renderBackendAccountRisk(entityId);'''

    content, n_ml = ml_pattern.subn(backend_risk_code, content)
    print(f'{filepath} ml_pattern replaced: {n_ml}')

    # 4. Replace submitConfirmModal
    confirm_pattern = re.compile(r'function submitConfirmModal\(\) \{[\s\S]*?closeDetailDrawer\(\);\s*\}', re.MULTILINE)
    new_confirm_code = '''function submitConfirmModal() {
                        const entId = pendingEntityId;
                        const action = pendingAction;
                        closeConfirmModal();

                        // Blocker: No PATCH/PUT endpoint exists in the PostgreSQL backend API for account status modification
                        showToast(`Status update to '${action}' for ${entId} requires backend endpoint (Pending backend API implementation).`);
                        closeDetailDrawer();
                }'''

    content, n_conf = confirm_pattern.subn(new_confirm_code, content)
    print(f'{filepath} confirm_pattern replaced: {n_conf}')

    # 5. Update applyWorkspaceFilters for robust matching
    filter_pattern = re.compile(r'const currentStatus = entitiesDb\[row\.id\.toUpperCase\(\)\]\.status;', re.MULTILINE)
    content = filter_pattern.sub('const dbItem = entitiesDb[row.id.toUpperCase()] || entitiesDb[row.id]; const currentStatus = dbItem ? dbItem.status : row.status;', content)

    # 6. Update recountSummaryCards for robust matching
    recount_pattern = re.compile(r'const status = entitiesDb\[row\.id\.toUpperCase\(\)\]\.status;', re.MULTILINE)
    content = recount_pattern.sub('const dbItem = entitiesDb[row.id.toUpperCase()] || entitiesDb[row.id]; const status = dbItem ? dbItem.status : row.status;', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Saved {filepath}')
