import re

with open('frontend/bank/investigator/watchlists.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Update oninput/onchange in filter controls if needed
content = content.replace('oninput="renderWatchlist()"', 'oninput="applyWatchlistFiltersAndRender()"')
content = content.replace('onchange="renderWatchlist()"', 'onchange="applyWatchlistFiltersAndRender()"')

new_script = """		<script>
		let pendingRemoveId = null;
		let currentWatchlists = [];

		function toggleMobileSidebar() {
			const sidebar = document.getElementById('sidebar-container');
			const overlay = document.getElementById('sidebar-overlay');
			if (sidebar.classList.contains('-translate-x-full')) {
				sidebar.classList.remove('-translate-x-full');
				overlay.classList.remove('hidden');
			} else {
				sidebar.classList.add('-translate-x-full');
				overlay.classList.add('hidden');
			}
		}

		let toastTimeout;
		function showToast(message) {
			const toast = document.getElementById('toast');
			const toastText = document.getElementById('toast-text');
			toastText.textContent = message;
			clearTimeout(toastTimeout);
			toast.classList.remove('translate-y-20', 'opacity-0', 'pointer-events-none');
			toast.classList.add('translate-y-0', 'opacity-100');
			toastTimeout = setTimeout(() => {
				toast.classList.remove('translate-y-0', 'opacity-100');
				toast.classList.add('translate-y-20', 'opacity-0', 'pointer-events-none');
			}, 3200);
		}

		function formatINR(val) {
			return '₹' + Number(val || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 });
		}

		async function openAddModal() {
			let accounts = {};
			if (window.MuleGuardAPI && MuleGuardAPI.getAccounts) {
				try {
					const accList = await MuleGuardAPI.getAccounts({ limit: 500 });
					(Array.isArray(accList) ? accList : []).forEach(a => {
						const id = a.id || a.account_id;
						if (id) accounts[id] = a;
					});
				} catch (e) {
					console.warn('Failed to fetch accounts via MuleGuardAPI:', e);
				}
			}

			const select = document.getElementById('modal-account-select');
			select.innerHTML = '';

			const watchedIds = new Set(currentWatchlists.map(w => w.accountId || w.account_id));
			const accKeys = Object.keys(accounts);

			if (accKeys.length === 0) {
				select.innerHTML = '<option value="" disabled>No accounts available from backend</option>';
			} else {
				accKeys.forEach(accId => {
					const isAdded = watchedIds.has(accId);
					const acc = accounts[accId];
					const name = acc.name || acc.customer_name || accId;
					select.innerHTML += `<option value="${accId}" ${isAdded ? 'disabled' : ''}>${accId} — ${name} ${isAdded ? '(Already Monitored)' : ''}</option>`;
				});
			}

			document.getElementById('modal-reason-input').value = '';
			document.getElementById('modal-priority-select').value = 'Medium';
			document.getElementById('add-watchlist-modal').classList.remove('hidden');
			document.getElementById('modal-backdrop').classList.remove('hidden');
		}

		function closeAddModal() {
			document.getElementById('add-watchlist-modal').classList.add('hidden');
			document.getElementById('modal-backdrop').classList.add('hidden');
		}

		async function handleAddWatchlistSubmit(e) {
			e.preventDefault();
			const accId = document.getElementById('modal-account-select').value;
			const reason = document.getElementById('modal-reason-input').value;

			if (!accId) {
				showToast('Please select a valid account.');
				return;
			}

			if (window.MuleGuardAPI && MuleGuardAPI.addToWatchlist) {
				try {
					await MuleGuardAPI.addToWatchlist(accId, reason);
					showToast(`Success: ${accId} added to active PostgreSQL watchlist.`);
					closeAddModal();
					await renderWatchlist();
					return;
				} catch (err) {
					console.error('Error adding to watchlist:', err);
					showToast(`Error adding to watchlist: ${err.message || err}`);
					return;
				}
			}

			showToast('Error: MuleGuardAPI client unavailable.');
		}

		function confirmRemoveWatchlist(accId, accName) {
			pendingRemoveId = accId;
			document.getElementById('remove-modal-text').textContent = `Are you sure you want to remove ${accId} (${accName}) from active monitoring?`;
			document.getElementById('remove-confirm-btn').onclick = () => {
				if (pendingRemoveId) {
					// Phase 3 Blocker Notice: DELETE /watchlists/{account_id} is missing in backend API.
					// Deletion is recorded in UI memory only, NOT persisted to localStorage.
					showToast('Watchlist deletion pending backend DELETE endpoint. Action recorded in UI only; not persisted locally.');
					currentWatchlists = currentWatchlists.filter(w => (w.accountId || w.account_id) !== pendingRemoveId);
					closeRemoveModal();
					applyWatchlistFiltersAndRender();
				}
			};
			document.getElementById('remove-modal').classList.remove('hidden');
			document.getElementById('modal-backdrop').classList.remove('hidden');
		}

		function closeRemoveModal() {
			pendingRemoveId = null;
			document.getElementById('remove-modal').classList.add('hidden');
			document.getElementById('modal-backdrop').classList.add('hidden');
		}

		async function renderWatchlist() {
			let watchlists = [];
			if (window.MuleGuardAPI && MuleGuardAPI.getWatchlists) {
				try {
					const res = await MuleGuardAPI.getWatchlists({ limit: 100 });
					watchlists = Array.isArray(res) ? res : (res.data || []);
				} catch (err) {
					console.error('Failed to fetch watchlists from PostgreSQL:', err);
					showToast('Failed to load watchlists from PostgreSQL backend.');
				}
			}
			currentWatchlists = watchlists;
			applyWatchlistFiltersAndRender();
		}

		function applyWatchlistFiltersAndRender() {
			const tbody = document.getElementById('watchlist-tbody');
			if (!tbody) return;

			const searchVal = (document.getElementById('filter-search')?.value || '').toLowerCase().trim();
			const priorityVal = document.getElementById('filter-priority')?.value || 'All';

			// KPI Calculations
			const totalEl = document.getElementById('kpi-total-watchlisted');
			if (totalEl) totalEl.textContent = currentWatchlists.length;

			const highCount = currentWatchlists.filter(w => (w.priority || '').toLowerCase() === 'high').length;
			const highEl = document.getElementById('kpi-high-priority');
			if (highEl) highEl.textContent = highCount;

			let totalVol = currentWatchlists.reduce((sum, w) => sum + (Number(w.balance) || 0), 0);
			const volEl = document.getElementById('kpi-24h-volume');
			if (volEl) volEl.textContent = formatINR(totalVol);

			// Filter entries
			let filtered = currentWatchlists.filter(w => {
				const accId = (w.accountId || w.account_id || '').toLowerCase();
				const accName = (w.accountName || w.customer_name || w.entity || '').toLowerCase();
				const reason = (w.reason || '').toLowerCase();
				const prio = w.priority || 'Medium';

				const matchesSearch = !searchVal || accId.includes(searchVal) || accName.includes(searchVal) || reason.includes(searchVal);
				const matchesPriority = (priorityVal === 'All') || (prio === priorityVal);
				return matchesSearch && matchesPriority;
			});

			tbody.innerHTML = '';

			if (filtered.length === 0) {
				tbody.innerHTML = `
					<tr>
						<td colspan="9" class="py-12 text-center text-on-surface-variant opacity-75">
							<div class="flex flex-col items-center justify-center gap-2">
								<span class="material-symbols-outlined text-[36px] text-slate-400">rule_folder</span>
								<p class="font-headline-md text-[14px] font-bold">No Entities Currently Monitored</p>
								<p class="font-body-md text-[12px]">No accounts are currently matching the active filter criteria.</p>
								<button class="mt-2 bg-secondary text-white rounded-lg px-3 py-1.5 font-label-md text-[11px] font-bold" onclick="openAddModal()">+ Add Watchlist Entity</button>
							</div>
						</td>
					</tr>
				`;
				return;
			}

			filtered.forEach(w => {
				const accId = w.accountId || w.account_id || 'UNKNOWN';
				const accName = w.accountName || w.customer_name || w.entity || accId;
				const priority = w.priority || 'Medium';
				const reason = w.reason || 'Monitored account';
				const addedBy = w.addedBy || 'System / Investigator';
				const addedAt = w.addedAt || w.created_at;
				const dateStr = addedAt ? new Date(addedAt).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : 'Recently';

				let prioBadgeClass = 'bg-blue-50 text-blue-700 border-blue-200';
				if (priority === 'High') prioBadgeClass = 'bg-red-50 text-red-700 border-red-200';
				else if (priority === 'Medium') prioBadgeClass = 'bg-amber-50 text-amber-700 border-amber-200';

				let riskBadgeClass = 'bg-emerald-50 text-emerald-700 border-emerald-200';
				let riskScoreText = 'Low Risk';
				if (priority === 'High' || (w.balance && w.balance > 100000)) {
					riskBadgeClass = 'bg-red-50 text-red-700 border-red-200';
					riskScoreText = 'High Risk';
				} else if (priority === 'Medium') {
					riskBadgeClass = 'bg-amber-50 text-amber-700 border-amber-200';
					riskScoreText = 'Medium Risk';
				}

				const balDisplay = w.balance != null ? formatINR(w.balance) : '₹0';

				tbody.innerHTML += `
					<tr class="hover:bg-slate-50 transition-colors">
						<td class="py-3.5 px-4 font-headline-md text-[12px] font-bold text-on-surface">${accName}</td>
						<td class="py-3.5 px-4 font-mono-technical text-[12px] font-bold text-secondary">${accId}</td>
						<td class="py-3.5 px-4">
							<span class="px-2 py-0.5 rounded text-[10px] font-bold border ${riskBadgeClass}">${riskScoreText}</span>
						</td>
						<td class="py-3.5 px-4">
							<span class="px-2 py-0.5 rounded text-[10px] font-bold border ${prioBadgeClass}">${priority}</span>
						</td>
						<td class="py-3.5 px-4 font-body-md text-[12px] text-on-surface-variant max-w-[240px] truncate" title="${reason.replace(/"/g, '&quot;')}">${reason}</td>
						<td class="py-3.5 px-4 font-body-md text-[12px] text-on-surface-variant">${addedBy}</td>
						<td class="py-3.5 px-4 font-body-md text-[12px] text-on-surface-variant">${dateStr}</td>
						<td class="py-3.5 px-4 font-mono-technical text-[11px] text-on-surface-variant">Bal: ${balDisplay}</td>
						<td class="py-3.5 px-4 text-right">
							<div class="flex items-center justify-end gap-1.5">
								<a href="investigations.html?account=${accId}" class="text-secondary hover:bg-blue-50 p-1 rounded font-label-md text-[11px] font-bold" title="Investigate Entity">Investigate</a>
								<a href="fraud_networks.html" class="text-slate-600 hover:bg-slate-100 p-1 rounded font-label-md text-[11px] font-bold" title="View Graph Network">Network</a>
								<button class="text-red-600 hover:bg-red-50 p-1 rounded font-label-md text-[11px] font-bold" onclick="confirmRemoveWatchlist('${accId}', '${accName.replace(/'/g, "\\'")}')" title="Remove from Watchlist">Remove</button>
							</div>
						</td>
					</tr>
				`;
			});
		}

		// Keyboard modal accessibility (Escape key)
		window.addEventListener('keydown', (e) => {
			if (e.key === 'Escape') {
				closeAddModal();
				closeRemoveModal();
			}
		});

		window.addEventListener('DOMContentLoaded', renderWatchlist);
		window.addEventListener('muleguard:transaction-ingested', renderWatchlist);
	</script>"""

# Replace the script block
script_pattern = re.compile(r'<script>\s*let pendingRemoveId = null;.*?</script>', re.DOTALL)
if script_pattern.search(content):
    content = script_pattern.sub(new_script, content)
    with open('frontend/bank/investigator/watchlists.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("watchlists.html successfully updated!")
else:
    print("Could not find script block to replace!")
