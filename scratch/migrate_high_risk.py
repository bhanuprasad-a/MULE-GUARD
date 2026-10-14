import re

filepath = 'frontend/bank/compliance/high-risk-alerts.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = r'function renderHighRiskAlerts\(\) \{[\s\S]*?function blockAccountForAlert\([^\)]+\) \{[\s\S]*?renderHighRiskAlerts\(\);\s*\}'

new_block = '''async function renderHighRiskAlerts() {
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
			const alerts = (allAlerts || []).filter(a => a.severity === 'Critical' || a.severity === 'High');
			const tbody = document.querySelector('tbody');
			const kpiCount = document.getElementById('kpi-alert-count');
			const kpiAmount = document.getElementById('kpi-at-risk-amount');
			if (!tbody) return;

			if (kpiCount) kpiCount.textContent = alerts.length;

			// Calculate total at risk amount
			let totalVal = 0;
			alerts.forEach(a => {
				if (typeof a.balance === 'number') {
					totalVal += a.balance;
				} else if (typeof a.amount === 'number') {
					totalVal += a.amount;
				} else if (typeof a.amount === 'string') {
					const clean = parseFloat(a.amount.replace(/[^0-9.]/g, ''));
					if (!isNaN(clean)) totalVal += clean;
				}
			});
			if (kpiAmount) {
				kpiAmount.textContent = `₹${Math.round(totalVal).toLocaleString('en-IN')}`;
			}

			tbody.innerHTML = '';
			if (alerts.length === 0) {
				tbody.innerHTML = `
					<tr>
						<td colspan="6" class="py-12 text-center text-on-surface-variant opacity-70">
							<div class="flex flex-col items-center justify-center gap-2">
								<span class="material-symbols-outlined text-[36px] text-emerald-500">check_circle</span>
								<p class="font-headline-md text-[14px] font-bold">No Pending High-Risk Alerts</p>
								<p class="font-body-md text-[12px]">All incoming transactions are currently below critical compliance risk thresholds.</p>
							</div>
						</td>
					</tr>
				`;
				return;
			}

			alerts.forEach(a => {
				let badgeColor = a.severity === 'Critical' ? 'bg-red-50 text-red-700 border-red-200' : 'bg-orange-50 text-orange-700 border-orange-200';
				const formattedAmt = a.amount ? (a.amount.startsWith('₹') ? a.amount : `₹${a.amount}`) : (a.balance ? `₹${Math.round(a.balance).toLocaleString('en-IN')}` : '₹50,000');
				const targetName = a.customer_name || a.target || a.accountName || a.account_id || 'Unknown';
				const safeTarget = targetName.replace(/'/g, "\\\\'");

				tbody.innerHTML += `
					<tr class="hover:bg-slate-50 transition-colors">
						<td class="py-3.5 px-4 font-mono-technical text-[12px] font-bold text-secondary">${a.id}</td>
						<td class="py-3.5 px-4 font-headline-md text-[12px] text-on-surface font-semibold">${a.category || a.rule || 'Suspicious Mule Activity'}</td>
						<td class="py-3.5 px-4 font-body-md text-[12px] text-on-surface-variant">${targetName}</td>
						<td class="py-3.5 px-4">
							<span class="px-2 py-0.5 rounded text-[10px] font-bold border ${badgeColor}">${a.severity}</span>
						</td>
						<td class="py-3.5 px-4 font-mono-technical text-[12px] font-bold text-right text-on-surface">${formattedAmt}</td>
						<td class="py-3.5 px-4 text-right">
							<button class="bg-red-600 hover:bg-red-700 text-white rounded px-2.5 py-1 font-label-md text-[10px] font-bold active:scale-95 transition-all shadow-sm focus:outline-none focus:ring-2 focus:ring-red-500/50" onclick="blockAccountForAlert('${a.id}', '${safeTarget}')">Block Account</button>
						</td>
					</tr>
				`;
			});
		}

		function blockAccountForAlert(alertId, accountName) {
			showToast(`Account blocking pending backend endpoint. Action recorded in UI only; not persisted locally.`);
		}'''

content = re.sub(old_block, new_block, content)
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('high-risk-alerts.html updated successfully!')
