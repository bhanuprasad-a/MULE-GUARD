import re

def migrate_cases_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update renderLinkedAlertsHTML
    content = content.replace(
        "const a = window.MuleGuardStore.getAlertById(aid);",
        "const a = (window.MuleGuardStore && window.MuleGuardStore.getAlertById) ? window.MuleGuardStore.getAlertById(aid) : null;"
    )

    # 2. Update saveCaseNote
    old_note_pattern = r'function saveCaseNote\(\) \{[\s\S]*?showToast\(\'Compliance note saved successfully\.\'\);\s*\}\s*\}|function saveCaseNote\(\) \{[\s\S]*?showToast\(\'Analyst note saved successfully\.\'\);\s*\}\s*\}'
    new_note = '''function saveCaseNote() {
			const caseId = document.getElementById('drawer-title-id').textContent;
			const input = document.getElementById('drawer-note-input');
			const text = input.value.trim();
			if (!text) return;
			input.value = '';
			const c = casesDb[caseId];
			if (c) {
				c.notes = (c.notes ? c.notes + '\\n' : '') + `[Today]: ${text}`;
				renderAnalystNotes(c);
			}
			showToast('Case notes pending backend endpoint. Note recorded in UI only; not persisted locally.');
		}'''
    content = re.sub(old_note_pattern, lambda m: new_note, content)

    # 3. Update submitConfirmModal
    old_submit_pattern = r'function submitConfirmModal\(\) \{[\s\S]*?renderCases\(\);\s*closeDetailDrawer\(\);\s*\}'
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
						console.error('Failed to resolve case in backend:', err);
						showToast(`Resolution error: ${err.message}`);
					}
				}
			} else if (action === 'Escalate') {
				if (window.MuleGuardAPI) {
					try {
						await MuleGuardAPI.escalateCase(caseId);
						showToast(`Success: Case ${caseId} escalated in PostgreSQL.`);
					} catch (err) {
						console.error('Failed to escalate case in backend:', err);
						showToast(`Escalation error: ${err.message}`);
					}
				}
			} else if (action === 'Acknowledge') {
				if (window.MuleGuardAPI) {
					try {
						await MuleGuardAPI.investigateCase(caseId);
						showToast(`Success: Case ${caseId} marked as Investigating in PostgreSQL.`);
					} catch (err) {
						console.error('Failed to investigate case in backend:', err);
						showToast(`Acknowledge error: ${err.message}`);
					}
				}
			} else if (action === 'False Positive') {
				showToast(`False-positive status pending backend endpoint. Action recorded in UI only; not persisted locally.`);
			}

			await renderCases();
			closeDetailDrawer();
		}'''
    content = re.sub(old_submit_pattern, lambda m: new_submit, content)

    # 4. Update renderCases
    old_render_pattern = r'// Dynamic renderCases — fully rebuilds table from store state\s*function renderCases\(\) \{[\s\S]*?recountSummaryCards\(\);\s*\}'
    new_render = '''// Dynamic renderCases — fully rebuilds table from PostgreSQL via MuleGuardAPI
		async function renderCases() {
			const tbody = document.getElementById('cases-tbody');
			if (!tbody) return;
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
			const cases = Object.values(casesDb);
			if (cases.length === 0) {
				tbody.innerHTML = `<tr><td colspan="9" class="py-16 text-center text-on-surface-variant font-body-md text-[13px] italic">No cases found. Cases are auto-generated when High or Critical alerts are raised.</td></tr>`;
				cachedRows = [];
				recountSummaryCards();
				return;
			}
			cases.sort((a, b) => (b.score || 0) - (a.score || 0));
			tbody.innerHTML = cases.map(c => {
				const sLabel = statusLabel(c.status);
				const sBadge = statusBadgeClass(c.status);
				const pBadge = priorityBadgeClass(c.priority);
				const score = Number(c.score || (c.priority === 'Critical' ? 92 : (c.priority === 'High' ? 78 : (c.priority === 'Medium' ? 55 : 30))));
				const sBadgeScore = scoreBadgeClass(score);
				const caseType = c.caseType || c.type || 'Investigation';
				const lastUpdated = c.createdTime || c.lastUpdated || c.updatedAt || 'Just now';
				const displayName = c.customer_name || c.entity || c.account_id || '—';
				return `<tr class="hover:bg-[#f0f7ff]/70 transition-colors duration-150 group cursor-pointer" data-case-id="${c.id}" data-priority="${c.priority || 'Low'}" data-status="${c.status}" data-type="${caseType}" onclick="rowClickAction(event, '${c.id}')"><td class="py-[18px] px-4 font-mono-technical text-[13px] text-secondary font-bold hover:underline transition-all duration-150 align-middle whitespace-nowrap case-id-cell">${c.id}</td><td class="py-[18px] px-4 font-headline-md text-[13px] text-on-surface font-bold align-middle">${c.title || '—'}</td><td class="py-[18px] px-4 font-body-md text-[13px] text-on-surface align-middle">${displayName}</td><td class="py-[18px] px-4 align-middle whitespace-nowrap"><span class="severity-badge px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${pBadge}">${c.priority || 'Low'}</span></td><td class="py-[18px] px-4 align-middle text-right whitespace-nowrap"><span class="font-mono-technical text-[12px] font-bold px-2 py-0.5 rounded border ${sBadgeScore}">${score} / 100</span></td><td class="py-[18px] px-4 font-body-md text-[13px] text-on-surface-variant align-middle whitespace-nowrap">${c.assignee || 'Unassigned'}</td><td class="py-[18px] px-4 font-body-md text-[13px] text-on-surface-variant align-middle whitespace-nowrap">${lastUpdated}</td><td class="py-[18px] px-4 align-middle whitespace-nowrap"><span class="status-badge-cell px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${sBadge}">${sLabel}</span></td><td class="py-[18px] px-4 align-middle text-right whitespace-nowrap"><button class="inspect-btn text-[12px] font-bold text-secondary hover:text-secondary-container focus:outline-none inline-flex items-center gap-1 group/btn" onclick="openDetailDrawer('${c.id}')">Inspect <span class="inspect-arrow inline-block transition-transform duration-150">→</span></button></td></tr>`;
			}).join('');
			const rows = tbody.querySelectorAll('tr[data-case-id]');
			cachedRows = Array.from(rows).map(row => {
				const caseId = row.getAttribute('data-case-id');
				const data = casesDb[caseId] || {};
				return { element: row, id: caseId.toLowerCase(), title: (data.title || '').toLowerCase(), entity: (data.entity || '').toLowerCase(), assignee: (data.assignee || '').toLowerCase(), type: (row.getAttribute('data-type') || '').toLowerCase(), status: data.status || '' };
			});
			recountSummaryCards();
		}'''
    content = re.sub(old_render_pattern, lambda m: new_render, content)

    # 5. Update init function
    old_init_pattern = r'function init[A-Za-z]+Cases\(\) \{[\s\S]*?renderCases\(\);\s*\}'
    init_fn_name = 'initComplianceCases' if 'Compliance' in content else 'initInvestigatorCases'
    new_init = f'''async function {init_fn_name}() {{
			await renderCases();
		}}'''
    content = re.sub(old_init_pattern, lambda m: new_init, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Migrated {filepath} successfully.')

migrate_cases_file('frontend/bank/compliance/cases.html')
migrate_cases_file('frontend/bank/investigator/cases.html')
