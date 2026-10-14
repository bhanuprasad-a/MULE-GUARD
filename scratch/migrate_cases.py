import re

def migrate_cases_file(filepath, is_compliance=False):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update renderLinkedAlertsHTML to not fail on missing MuleGuardStore
    old_linked = r'function renderLinkedAlertsHTML\(caseData\) \{[\s\S]*?return caseData\.linkedAlerts\.map\(aid => \{[\s\S]*?const a = window\.MuleGuardStore\.getAlertById\(aid\);'
    new_linked = '''function renderLinkedAlertsHTML(caseData) {
			const alertsList = caseData.linkedAlerts || (caseData.alert_id ? [caseData.alert_id] : []);
			if (alertsList.length === 0) {
				return '<span class="text-[12px] text-on-surface-variant italic">No linked alerts for this case.</span>';
			}
			return alertsList.map(aid => {
				const a = (window.MuleGuardStore && window.MuleGuardStore.getAlertById) ? window.MuleGuardStore.getAlertById(aid) : null;'''
    content = re.sub(old_linked, lambda m: new_linked, content)

    # 2. Update saveCaseNote
    old_note = r'function saveCaseNote\(\) \{[\s\S]*?showToast\([^\)]+\);\s*\}\s*\}'
    new_note = '''function saveCaseNote() {
			const caseId = document.getElementById('drawer-title-id').textContent;
			const input = document.getElementById('drawer-note-input');
			const text = input.value.trim();
			if (!text) return;
			input.value = '';
			const c = casesDb[caseId];
			if (c) {
				c.notes = (c.notes ? c.notes + '\\n' : '') + `[${new Date().toLocaleDateString('en-GB', {day:'2-digit', month:'short'})}]: ${text}`;
				renderAnalystNotes(c);
			}
			showToast('Case notes pending backend endpoint. Note recorded in UI only; not persisted locally.');
		}'''
    content = re.sub(old_note, lambda m: new_note, content)

    # 3. Update submitConfirmModal
    old_submit = r'function submitConfirmModal\(\) \{[\s\S]*?renderCases\(\);\s*closeDetailDrawer\(\);\s*\}'
    new_submit = '''async function submitConfirmModal() {
			const caseId = pendingCaseId;
			const action = pendingAction || 'Acknowledge';
			closeConfirmModal();

			if (action === 'Close' || action === 'Resolve') {
				if (window.MuleGuardAPI) {
					try {
						await MuleGuardAPI.resolveCase(caseId);
						showToast(`Success: Case ${caseId} resolved in PostgreSQL.`);
					} catch (err) {
						console.error('Failed to resolve case:', err);
						showToast(`Resolution error: ${err.message}`);
					}
				}
			} else if (action === 'Escalate') {
				if (window.MuleGuardAPI) {
					try {
						await MuleGuardAPI.escalateCase(caseId);
						showToast(`Success: Case ${caseId} escalated in PostgreSQL.`);
					} catch (err) {
						console.error('Failed to escalate case:', err);
						showToast(`Escalation error: ${err.message}`);
					}
				}
			} else if (action === 'Acknowledge') {
				if (window.MuleGuardAPI) {
					try {
						await MuleGuardAPI.investigateCase(caseId);
						showToast(`Success: Case ${caseId} marked as Investigating in PostgreSQL.`);
					} catch (err) {
						console.error('Failed to investigate case:', err);
						showToast(`Acknowledge error: ${err.message}`);
					}
				}
			} else if (action === 'False Positive') {
				showToast(`False-positive status pending backend endpoint. Action recorded in UI only; not persisted locally.`);
			}

			await renderCases();
			closeDetailDrawer();
		}'''
    content = re.sub(old_submit, lambda m: new_submit, content)

    # 4. Update renderCases
    old_render = r'// ── renderCases ──[\s\S]*?function renderCases\(\) \{[\s\S]*?recountSummaryCards\(\);\s*\}'
    new_render = '''// ── renderCases ─────────────────────────────────────────────────────────
		async function renderCases() {
			let allCases = [];
			if (window.MuleGuardAPI) {
				try {
					allCases = await MuleGuardAPI.getCases({ limit: 100 });
				} catch (err) {
					console.error('Failed to fetch cases from backend:', err);
				}
			}
			if ((!allCases || allCases.length === 0) && window.MuleGuardExpandedDB) {
				allCases = window.MuleGuardExpandedDB.cases || [];
			}
			Object.keys(casesDb).forEach(k => delete casesDb[k]);
			(allCases || []).forEach(c => { casesDb[c.id] = c; });
			const tbody = document.getElementById('cases-tbody');
			if (!tbody) return;
			tbody.innerHTML = (allCases || []).map(c => {
				const priBadge = c.priority === 'Critical' ? 'bg-red-50 text-red-700 border-red-200' :
					c.priority === 'High' ? 'bg-orange-50 text-orange-700 border-orange-200' :
					c.priority === 'Medium' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
					'bg-blue-50 text-blue-700 border-blue-200';
				const score = Number(c.score || (c.priority === 'Critical' ? 92 : (c.priority === 'High' ? 78 : (c.priority === 'Medium' ? 55 : 30))));
				const scoreClass = score >= 90 ? 'text-red-600 bg-red-50 border-red-200' :
					score >= 70 ? 'text-orange-600 bg-orange-50 border-orange-200' :
					score >= 50 ? 'text-yellow-600 bg-yellow-50 border-yellow-200' :
					'text-blue-800 bg-blue-50 border-blue-200';
				const stBadge = c.status === 'Open' ? 'bg-blue-50 text-blue-700 border-blue-200' :
					c.status === 'Under Review' || c.status === 'Investigating' ? 'bg-amber-50 text-amber-700 border-amber-200' :
					c.status === 'Escalated' ? 'bg-purple-50 text-purple-700 border-purple-200' :
					'bg-slate-50 text-slate-600 border-slate-200';
				const displayName = c.customer_name || c.entity || c.account_id || '—';
				const formattedAmt = c.amount || (c.balance ? '₹' + Math.round(c.balance).toLocaleString('en-IN') : '₹1,00,000');
				const formattedTime = c.createdTime || (c.created_at ? new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Just now');
				return `<tr class="hover:bg-[#f0f7ff]/70 transition-colors duration-150 group cursor-pointer" data-case-id="${c.id}" data-priority="${c.priority}" data-status="${c.status}" onclick="rowClickAction(event, '${c.id}')">
					<td class="py-[18px] px-4 font-mono-technical text-[13px] text-secondary font-bold hover:underline transition-all duration-150 align-middle whitespace-nowrap case-id-cell">${c.id}</td>
					<td class="py-[18px] px-4 font-headline-md text-[13px] text-on-surface font-bold align-middle">${c.title}</td>
					<td class="py-[18px] px-4 font-body-md text-[13px] text-on-surface align-middle">${displayName}</td>
					<td class="py-[18px] px-4 align-middle whitespace-nowrap"><span class="priority-badge px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${priBadge}">${c.priority}</span></td>
					<td class="py-[18px] px-4 align-middle text-right whitespace-nowrap"><span class="font-mono-technical text-[12px] font-bold px-2 py-0.5 rounded border ${scoreClass}">${score}</span></td>
					<td class="py-[18px] px-4 font-mono-technical text-[13px] text-on-surface text-right font-semibold align-middle whitespace-nowrap">${formattedAmt}</td>
					<td class="py-[18px] px-4 font-body-md text-[13px] text-on-surface align-middle whitespace-nowrap">${c.assignee || 'A. Kumar'}</td>
					<td class="py-[18px] px-4 font-body-md text-[13px] text-on-surface-variant align-middle whitespace-nowrap">${formattedTime}</td>
					<td class="py-[18px] px-4 align-middle whitespace-nowrap"><span class="status-badge-cell px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${stBadge}">${c.status}</span></td>
					<td class="py-[18px] px-4 align-middle text-right whitespace-nowrap"><button class="inspect-btn text-[12px] font-bold text-secondary hover:text-secondary-container focus:outline-none inline-flex items-center gap-1 group/btn" onclick="openDetailDrawer('${c.id}')">Inspect <span class="inspect-arrow inline-block transition-transform duration-150">→</span></button></td>
				</tr>`;
			}).join('');
			cachedRows = Array.from(tbody.querySelectorAll('tr')).map(row => {
				const cid = row.getAttribute('data-case-id');
				const d = casesDb[cid] || {};
				return {
					element: row,
					id: (cid || '').toLowerCase(),
					title: (d.title || '').toLowerCase(),
					entity: (d.customer_name || d.entity || '').toLowerCase(),
					priority: row.getAttribute('data-priority'),
					status: d.status
				};
			});
			recountSummaryCards();
		}'''
    content = re.sub(old_render, lambda m: new_render, content)

    # 5. Update initCasesPage
    old_init = r'function initCasesPage\(\) \{[\s\S]*?renderCases\(\);\s*\}'
    new_init = '''async function initCasesPage() {
			await renderCases();
		}'''
    content = re.sub(old_init, lambda m: new_init, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Migrated {filepath} successfully.')

def migrate_escalated_cases():
    filepath = 'frontend/bank/compliance/escalated-cases.html'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    old_block = r'function renderEscalations\(\) \{[\s\S]*?function resolveComplianceCase\([^\)]+\) \{[\s\S]*?renderEscalations\(\);\s*\}'
    new_block = '''async function renderEscalations() {
			let allCases = [];
			if (window.MuleGuardAPI) {
				try {
					allCases = await MuleGuardAPI.getCases({ limit: 100 });
				} catch (err) {
					console.error('Failed to fetch cases from backend:', err);
				}
			}
			if ((!allCases || allCases.length === 0) && window.MuleGuardExpandedDB) {
				allCases = window.MuleGuardExpandedDB.cases || [];
			}
			const cases = (allCases || []).filter(c => c.status === 'Escalated');
			const tbody = document.getElementById('escalations-tbody');
			if (!tbody) return;

			renderKPIs(cases);

			if (cases.length === 0) {
				tbody.innerHTML = `
					<tr>
						<td colspan="6" class="py-14 text-center">
							<div class="flex flex-col items-center gap-3">
								<span class="material-symbols-outlined text-[44px] text-on-surface-variant/25">shield_with_heart</span>
								<p class="font-body-md text-[13px] text-on-surface-variant/60 font-medium">No pending escalated cases in the review queue.</p>
								<p class="font-mono-technical text-[10px] text-on-surface-variant/40 uppercase tracking-wider">Start the transaction simulator to generate activity</p>
							</div>
						</td>
					</tr>
				`;
				return;
			}

			const rows = cases.map(c => {
				const score = Number(c.score || (c.priority === 'Critical' ? 92 : (c.priority === 'High' ? 78 : (c.priority === 'Medium' ? 55 : 30))));
				let scoreBadge;
				if (score >= 75)      scoreBadge = 'bg-red-50 text-red-700 border-red-200';
				else if (score >= 50) scoreBadge = 'bg-orange-50 text-orange-700 border-orange-200';
				else                  scoreBadge = 'bg-green-50 text-green-700 border-green-200';

				const displayName = c.customer_name || c.entity || c.account_id || '—';
				return `
					<tr class="hover:bg-slate-50 transition-colors">
						<td class="py-3.5 px-3 font-mono-technical text-[12px] font-bold text-secondary whitespace-nowrap">${c.id}</td>
						<td class="py-3.5 px-3 font-headline-md text-[12px] text-on-surface font-semibold max-w-[220px] truncate">${c.title}</td>
						<td class="py-3.5 px-3 font-body-md text-[12px] text-on-surface-variant whitespace-nowrap">${displayName}</td>
						<td class="py-3.5 px-3 text-right">
							<span class="font-mono-technical text-[11px] font-bold px-2 py-0.5 rounded border ${scoreBadge}">${score}</span>
						</td>
						<td class="py-3.5 px-3 font-body-md text-[12px] text-on-surface-variant whitespace-nowrap">${c.assignee || 'Investigator'}</td>
						<td class="py-3.5 px-3 text-right">
							<div class="flex justify-end gap-2">
								<button
									class="bg-secondary hover:bg-secondary/90 text-white rounded px-3 py-1 font-mono-technical text-[10px] font-bold active:scale-95 transition-all"
									onclick="resolveComplianceCase('${c.id}', 'File SAR')">
									File SAR
								</button>
								<button
									class="bg-transparent border border-outline-variant hover:border-secondary text-on-surface rounded px-3 py-1 font-mono-technical text-[10px] active:scale-95 transition-all"
									onclick="resolveComplianceCase('${c.id}', 'Approve / Clear')">
									Clear Case
								</button>
							</div>
						</td>
					</tr>
				`;
			});
			tbody.innerHTML = rows.join('');
		}

		async function resolveComplianceCase(caseId, action) {
			if (window.MuleGuardAPI) {
				try {
					await MuleGuardAPI.resolveCase(caseId);
					showToast(`Success: Case ${caseId} resolved in PostgreSQL. Formal SAR filing pending backend endpoint.`);
				} catch (err) {
					console.error('Failed to resolve compliance case:', err);
					showToast(`Resolution error: ${err.message}`);
				}
			}
			await renderEscalations();
		}'''

    content = re.sub(old_block, lambda m: new_block, content)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Migrated {filepath} successfully.')

migrate_cases_file('frontend/bank/compliance/cases.html', is_compliance=True)
migrate_cases_file('frontend/bank/investigator/cases.html', is_compliance=False)
migrate_escalated_cases()
