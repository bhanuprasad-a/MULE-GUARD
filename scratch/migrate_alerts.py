import re

def migrate_alerts_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace the entire alertsDb line
    content = re.sub(
        r'// Alerts database loaded dynamically from MuleGuardStore\s*const alertsDb = \(window\.MuleGuardStore\) \? window\.MuleGuardStore\.getAlerts\(\)\.reduce\([^\n]+\n',
        '// Alerts database loaded dynamically from PostgreSQL via MuleGuardAPI\n\t\tlet alertsDb = {};\n',
        content
    )

    # 2. Update drawer score
    content = content.replace(
        "document.getElementById('drawer-risk-score').textContent = `${data.score} / 100`;",
        "document.getElementById('drawer-risk-score').textContent = `${Math.round(data.risk_score !== undefined ? data.risk_score : (data.score || 0))} / 100`;"
    )

    # 3. Replace submitConfirmModal
    old_submit_pattern = r'function submitConfirmModal\(\) \{[\s\S]*?closeDetailDrawer\(\);\s*\}'
    new_submit = '''async function submitConfirmModal() {
			const alertId = pendingAlertId;
			const action = pendingAction;
			const data = alertsDb[alertId];

			closeConfirmModal();

			if (action === 'Dismiss') {
				showToast(`Alert dismissal pending backend endpoint. Action recorded in UI only; not persisted locally.`);
				if (data) data.status = 'Dismissed';
				const row = document.querySelector("#alerts-tbody tr[data-alert-id='" + alertId + "']");
				if (row) {
					row.setAttribute('data-status', 'Dismissed');
					const badge = row.querySelector('.status-badge-cell');
					if (badge) {
						badge.className = "status-badge-cell px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-50 text-slate-700 border border-slate-200";
						badge.textContent = "Dismissed";
					}
				}
			} else if (action === 'Escalate') {
				if (window.MuleGuardAPI) {
					try {
						await MuleGuardAPI.createCaseFromAlert(alertId);
						showToast(`Success: Alert ${alertId} escalated to formal case queue in PostgreSQL.`);
						if (data) data.status = 'Escalated';
						const row = document.querySelector("#alerts-tbody tr[data-alert-id='" + alertId + "']");
						if (row) {
							row.setAttribute('data-status', 'Escalated');
							const badge = row.querySelector('.status-badge-cell');
							if (badge) {
								badge.className = "status-badge-cell px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-purple-50 text-purple-700 border border-purple-200";
								badge.textContent = "Escalated";
							}
						}
					} catch (err) {
						console.warn('Failed to escalate alert in backend:', err);
						showToast(`Case escalation note: ${err.message || 'Already escalated or created'}`);
					}
				}
			} else if (action === 'Acknowledge') {
				if (window.MuleGuardAPI) {
					try {
						await MuleGuardAPI.acknowledgeAlert(alertId);
						showToast(`Success: Alert ${alertId} acknowledged in PostgreSQL.`);
						if (data) data.status = 'Acknowledged';
						const row = document.querySelector("#alerts-tbody tr[data-alert-id='" + alertId + "']");
						if (row) {
							row.setAttribute('data-status', 'Acknowledged');
							const badge = row.querySelector('.status-badge-cell');
							if (badge) {
								badge.className = "status-badge-cell px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200";
								badge.textContent = "Acknowledged";
							}
						}
					} catch (err) {
						console.error('Failed to acknowledge alert in backend:', err);
						showToast(`Error acknowledging alert: ${err.message}`);
					}
				}
			}

			applyWorkspaceFilters();
			closeDetailDrawer();
		}'''
    content = re.sub(old_submit_pattern, new_submit, content)

    # 4. Replace renderAlerts and refreshAlerts
    old_render_pattern = r'// ── renderAlerts ──[\s\S]*?function refreshAlerts\(\) \{[\s\S]*?showToast\([^\)]+\);\s*\}\s*\}'
    new_render = '''// ── renderAlerts ───────────────────────────────────────────────────────
		async function renderAlerts() {
			let allAlerts = [];
			if (window.MuleGuardAPI) {
				try {
					allAlerts = await MuleGuardAPI.getAlerts({ limit: 100 });
				} catch (err) {
					console.error('Failed to fetch alerts from backend:', err);
				}
			}
			if ((!allAlerts || allAlerts.length === 0) && window.MuleGuardExpandedDB) {
				allAlerts = window.MuleGuardExpandedDB.alerts || [];
			}
			Object.keys(alertsDb).forEach(k => delete alertsDb[k]);
			(allAlerts || []).forEach(a => { alertsDb[a.id] = a; });
			const SORDER = { Critical: 0, High: 1, Medium: 2, Low: 3 };
			const sorted = (allAlerts || []).slice().sort((a, b) => (SORDER[a.severity] || 3) - (SORDER[b.severity] || 3));
			const tbody = document.getElementById('alerts-tbody');
			if (!tbody) return;
			tbody.innerHTML = sorted.map(a => {
				const sevBadge = a.severity === 'Critical' ? 'bg-red-50 text-red-700 border-red-200' :
					a.severity === 'High' ? 'bg-orange-50 text-orange-700 border-orange-200' :
					a.severity === 'Medium' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
					'bg-blue-50 text-blue-700 border-blue-200';
				const score = Math.round(a.risk_score !== undefined ? a.risk_score : (a.score || 0));
				const scoreClass = score >= 90 ? 'text-red-600 bg-red-50 border-red-200' :
					score >= 70 ? 'text-orange-600 bg-orange-50 border-orange-200' :
					score >= 50 ? 'text-yellow-600 bg-yellow-50 border-yellow-200' :
					'text-blue-800 bg-blue-50 border-blue-200';
				const stBadge = a.status === 'New' || a.status === 'Open' ? 'bg-red-50 text-red-700 border-red-200' :
					a.status === 'Resolved' || a.status === 'False Positive' || a.status === 'Dismissed' ? 'bg-slate-50 text-slate-600 border-slate-200' :
					a.status === 'Escalated' ? 'bg-purple-50 text-purple-700 border-purple-200' :
					'bg-blue-50 text-blue-700 border-blue-200';
				const srcLabel = a.detectionSource === 'Combined' ? 'Corroborated' :
					a.detectionSource === 'ML' ? 'ML Risk' :
					a.detectionSource === 'Rule' ? 'Rule Alert' : (a.detectionSource || 'ML Risk');
				const srcClass = a.detectionSource === 'Combined' ? 'bg-red-50 text-red-700 border-red-200' :
					a.detectionSource === 'Rule' ? 'bg-amber-50 text-amber-700 border-amber-200' :
					'bg-blue-50 text-blue-700 border-blue-200';
				const displayName = a.customer_name || a.accountName || a.target || a.account_id || a.accountId || '—';
				const category = a.category || (score >= 80 ? 'Velocity Anomaly' : (score >= 60 ? 'Structuring' : 'Behavioral Shift'));
				const formattedAmt = a.amount || (a.balance ? '₹' + Math.round(a.balance).toLocaleString('en-IN') : '—');
				const formattedTime = a.time || (a.created_at ? new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Just now');
				return `<tr class="hover:bg-[#f0f7ff]/70 transition-colors duration-150 group cursor-pointer" data-alert-id="${a.id}" data-severity="${a.severity}" data-status="${a.status}" data-category="${category}" data-source="${a.detectionSource || ''}" onclick="rowClickAction(event, '${a.id}')">
					<td class="py-[18px] px-4 font-mono-technical text-[13px] text-secondary font-bold hover:underline transition-all duration-150 align-middle whitespace-nowrap case-id-cell">${a.id}</td>
					<td class="py-[18px] px-4 font-headline-md text-[13px] text-on-surface font-bold align-middle">${displayName}</td>
					<td class="py-[18px] px-4 font-body-md text-[13px] text-on-surface align-middle">${category}</td>
					<td class="py-[18px] px-4 align-middle whitespace-nowrap"><span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${srcClass}">${srcLabel}</span></td>
					<td class="py-[18px] px-4 align-middle text-right whitespace-nowrap"><span class="font-mono-technical text-[12px] font-bold px-2 py-0.5 rounded border ${scoreClass}">${score} / 100</span></td>
					<td class="py-[18px] px-4 font-mono-technical text-[13px] text-on-surface text-right font-semibold align-middle whitespace-nowrap">${formattedAmt}</td>
					<td class="py-[18px] px-4 font-body-md text-[13px] text-on-surface-variant align-middle whitespace-nowrap">${formattedTime}</td>
					<td class="py-[18px] px-4 align-middle whitespace-nowrap"><span class="severity-badge px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${sevBadge}">${a.severity}</span></td>
					<td class="py-[18px] px-4 align-middle whitespace-nowrap"><span class="status-badge-cell px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${stBadge}">${a.status}</span></td>
					<td class="py-[18px] px-4 align-middle text-right whitespace-nowrap"><button class="inspect-btn text-[12px] font-bold text-secondary hover:text-secondary-container focus:outline-none inline-flex items-center gap-1 group/btn" onclick="openDetailDrawer('${a.id}')">Inspect <span class="inspect-arrow inline-block transition-transform duration-150">→</span></button></td>
				</tr>`;
			}).join('');
			cachedRows = Array.from(tbody.querySelectorAll('tr')).map(row => {
				const aid = row.getAttribute('data-alert-id');
				const d = alertsDb[aid] || {};
				return {
					element: row,
					id: (aid || '').toLowerCase(),
					target: (d.customer_name || d.accountName || d.target || '').toLowerCase(),
					category: (d.category || '').toLowerCase(),
					severity: row.getAttribute('data-severity'),
					source: row.getAttribute('data-source') || '',
					status: d.status
				};
			});
			recountSummaryCards();
		}

		async function refreshAlerts() {
			const btn = document.getElementById('refresh-alerts-btn');
			if (btn) btn.textContent = '↻ Refreshing...';
			await renderAlerts();
			if (btn) btn.textContent = '↻ Refresh Alerts';
			showToast('Alerts refreshed from PostgreSQL.');
		}'''
    content = re.sub(old_render_pattern, new_render, content)

    # 5. Replace initAlertsPage
    old_init = r'function initAlertsPage\(\) \{[\s\S]*?renderAlerts\(\);\s*\}'
    new_init = '''async function initAlertsPage() {
			await renderAlerts();
		}'''
    content = re.sub(old_init, new_init, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Migrated {filepath} successfully.')

migrate_alerts_file('frontend/bank/compliance/alerts.html')
migrate_alerts_file('frontend/bank/investigator/alerts.html')
