const fs = require('fs');
const { execSync } = require('child_process');

console.log('Restoring and wiring transactions.html and entities.html to PostgreSQL dataset...');

// 1. Investigator Transactions
const rawHeadTx = execSync('git show HEAD:frontend/bank/investigator/transactions.html', { maxBuffer: 10*1024*1024, encoding: 'utf8' });

// Add api.js to head if not present
let txHtml = rawHeadTx;
if (!txHtml.includes('scripts/api.js')) {
    txHtml = txHtml.replace('<script src="../../scripts/data-store.js"></script>', '<script src="../../scripts/api.js"></script>\n\t<script src="../../scripts/data-store.js"></script>');
}

// Find Script 3 in transactions
const txScripts = [...txHtml.matchAll(/<script[\s\S]*?<\/script>/gi)];
console.log('txScripts count:', txScripts.length);
const txLastScript = txScripts[txScripts.length - 1][0];

// Replace static transactionsDb with dynamic loader in Script 3
// In the original Script 3, const transactionsDb = { ... }; is at the beginning of script
const dynTxDbCode = `
		// Dynamic transactions database populated from PostgreSQL / MuleGuardStore
		let transactionsDb = {};

		function initTransactionsFromStore() {
			const rawTxs = (window.MuleGuardStore) ? window.MuleGuardStore.getTransactions() : (window.MuleGuardExpandedDB ? window.MuleGuardExpandedDB.transactions : []);
			const accounts = (window.MuleGuardStore) ? window.MuleGuardStore.getAccounts() : (window.MuleGuardExpandedDB ? window.MuleGuardExpandedDB.accounts : {});

			transactionsDb = {};
			rawTxs.forEach(t => {
				const senderAcc = accounts[t.senderId] || { name: t.senderId, type: 'Savings' };
				const receiverAcc = accounts[t.receiverId] || { name: t.receiverId, type: 'Savings' };
				const entityName = (t.status === 'Critical' || t.status === 'Flagged' || t.status === 'Blocked') 
					? receiverAcc.name 
					: senderAcc.name;
				
				const amount = t.amount || t.amountNumeric || 0;
				const formattedVal = (window.MuleGuardStore && window.MuleGuardStore.formatINR) 
					? window.MuleGuardStore.formatINR(amount) 
					: ('₹' + Number(amount).toLocaleString('en-IN'));

				let score = t.riskScore !== undefined ? t.riskScore : (t.score !== undefined ? t.score : 0);
				if (!score) {
					if (t.status === 'Critical') score = 96;
					else if (t.status === 'Flagged') score = 88;
					else if (t.status === 'Blocked') score = 98;
					else if (t.status === 'Under Review') score = 65;
					else score = 15;
				}

				transactionsDb[t.id] = {
					id: t.id,
					entity: entityName,
					senderId: t.senderId,
					senderName: senderAcc.name,
					receiverId: t.receiverId,
					receiverName: receiverAcc.name,
					type: t.type || t.channel || 'Transfer',
					value: formattedVal,
					amountNumeric: amount,
					score: score,
					time: t.timestamp || t.time || 'Recent',
					origin: t.senderId,
					destination: t.receiverId,
					status: t.status || 'Normal',
					summary: t.summary || \`Transfer of \${formattedVal} from \${senderAcc.name} (\${t.senderId}) to \${receiverAcc.name} (\${t.receiverId}). Status: \${t.status || 'Normal'}.\`
				};
			});
		}

		function renderTransactionsTable() {
			initTransactionsFromStore();
			const tbody = document.getElementById('transactions-tbody');
			if (!tbody) return;

			const txList = Object.values(transactionsDb);
			tbody.innerHTML = txList.map(t => {
				const riskCategory = t.score >= 80 ? 'Critical' : (t.score >= 60 ? 'High' : (t.score >= 40 ? 'Moderate' : 'Low'));
				const riskColor = t.score >= 80 ? 'text-red-600 bg-red-50 border-red-200' :
					(t.score >= 60 ? 'text-orange-600 bg-orange-50 border-orange-200' :
					(t.score >= 40 ? 'text-amber-600 bg-amber-50 border-amber-200' : 'text-blue-600 bg-blue-50 border-blue-200'));

				const statusBadgeClass = t.status === 'Blocked' ? 'bg-red-50 text-red-700 border-red-200' :
					(t.status === 'Flagged' || t.status === 'Critical' ? 'bg-orange-50 text-orange-700 border-orange-200' :
					(t.status === 'Under Review' ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-green-50 text-green-700 border-green-200'));

				return \`
					<tr class="hover:bg-[#f0f7ff]/70 transition-colors duration-150 group cursor-pointer" data-txn-id="\${t.id}" data-risk="\${riskCategory}" data-status="\${t.status}" data-type="\${t.type}" onclick="rowClickAction(event, '\${t.id}')">
						<td class="py-3.5 px-4 font-mono-technical text-[13px] text-secondary font-bold hover:underline transition-all duration-150 case-id-cell">\${t.id}</td>
						<td class="py-3.5 px-4 font-headline-md text-[13px] text-on-surface font-bold">\${t.entity}</td>
						<td class="py-3.5 px-4 font-body-md text-[13px] text-on-surface">\${t.type}</td>
						<td class="py-3.5 px-4 font-mono-technical text-[13px] text-on-surface font-semibold text-right">\${t.value}</td>
						<td class="py-3.5 px-4">
							<span class="font-mono-technical text-[12px] font-bold px-2 py-0.5 rounded border \${riskColor}">\${t.score} / 100</span>
						</td>
						<td class="py-3.5 px-4 font-body-md text-[13px] text-on-surface-variant">\${t.time}</td>
						<td class="py-3.5 px-4 font-body-md text-[13px] text-on-surface-variant">\${t.origin} → \${t.destination}</td>
						<td class="py-3.5 px-4">
							<span class="status-badge-cell px-2.5 py-0.5 rounded-full text-[11px] font-semibold border \${statusBadgeClass}">\${t.status}</span>
						</td>
						<td class="py-3.5 px-4 text-right">
							<button class="inspect-btn text-[12px] font-bold text-secondary hover:text-secondary-container focus:outline-none inline-flex items-center gap-1 group/btn" onclick="openDetailDrawer('\${t.id}')">
								Inspect <span class="inspect-arrow inline-block transition-transform duration-150">→</span>
							</button>
						</td>
					</tr>
				\`;
			}).join('');

			cacheDOMRows();
			recountSummaryCards();
		}
`;

// In txLastScript, replace from 'const transactionsDb = {' up to the end of that object definition
const dbObjRegex = /const transactionsDb = \{[\s\S]*?\n\t*\};/;
let newTxLastScript = txLastScript.replace(dbObjRegex, dynTxDbCode);

// Also update DOMContentLoaded to call renderTransactionsTable()
newTxLastScript = newTxLastScript.replace(/window\.addEventListener\('DOMContentLoaded', \(\) => \{[\s\S]*?recountSummaryCards\(\);/i, `window.addEventListener('DOMContentLoaded', () => {
			renderTransactionsTable();`);

// Wire live transaction ingestion listener
newTxLastScript = newTxLastScript.replace('</script>', `
		// Real-time live ingestion sync
		window.addEventListener('muleguard:transaction-ingested', () => {
			renderTransactionsTable();
		});
</script>`);

txHtml = txHtml.replace(txLastScript, newTxLastScript);
fs.writeFileSync('frontend/bank/investigator/transactions.html', txHtml, 'utf8');
console.log('Saved frontend/bank/investigator/transactions.html (len:', txHtml.length, ')');

// Save compliance version of transactions
const compTxHtml = txHtml.replace(/href="dashboard\.html"/g, 'href="dashboard.html"');
fs.writeFileSync('frontend/bank/compliance/transactions.html', compTxHtml, 'utf8');
console.log('Saved frontend/bank/compliance/transactions.html (len:', compTxHtml.length, ')');


// 2. Investigator Entities
const rawHeadEnt = execSync('git show HEAD:frontend/bank/investigator/entities.html', { maxBuffer: 10*1024*1024, encoding: 'utf8' });

let entHtml = rawHeadEnt;
if (!entHtml.includes('scripts/api.js')) {
    entHtml = entHtml.replace('<script src="../../scripts/data-store.js"></script>', '<script src="../../scripts/api.js"></script>\n\t<script src="../../scripts/data-store.js"></script>');
}

const entScripts = [...entHtml.matchAll(/<script[\s\S]*?<\/script>/gi)];
console.log('entScripts count:', entScripts.length);
const entLastScript = entScripts[entScripts.length - 1][0];

const dynEntDbCode = `
		// Dynamic entities database populated from PostgreSQL / MuleGuardStore
		let entitiesDb = {};

		function initEntitiesFromStore() {
			const accounts = (window.MuleGuardStore) ? window.MuleGuardStore.getAccounts() : (window.MuleGuardExpandedDB ? window.MuleGuardExpandedDB.accounts : {});
			const allTxs = (window.MuleGuardStore) ? window.MuleGuardStore.getTransactions() : (window.MuleGuardExpandedDB ? window.MuleGuardExpandedDB.transactions : []);

			entitiesDb = {};
			Object.keys(accounts).forEach(accId => {
				const acc = accounts[accId];
				let score = acc.riskScore !== undefined ? acc.riskScore : (acc.score !== undefined ? acc.score : 0);
				if (!score) {
					if (acc.status === 'Critical') score = 98;
					else if (acc.status === 'Flagged') score = 88;
					else if (acc.status === 'Blocked') score = 96;
					else if (acc.status === 'Under Review') score = 65;
					else score = 15;
				}

				const riskCategory = score >= 80 ? 'Critical' : (score >= 60 ? 'High' : (score >= 40 ? 'Moderate' : 'Low'));

				const relatedTxs = allTxs.filter(t => t.senderId === accId || t.receiverId === accId);
				const formattedBal = (window.MuleGuardStore && window.MuleGuardStore.formatINR) 
					? window.MuleGuardStore.formatINR(acc.balance || 0) 
					: ('₹' + Number(acc.balance || 0).toLocaleString('en-IN'));

				entitiesDb[accId] = {
					id: accId,
					name: acc.name,
					type: acc.type || 'Savings',
					balance: formattedBal,
					balanceNumeric: acc.balance || 0,
					riskTier: riskCategory,
					riskScore: score,
					status: acc.status || 'Normal',
					flags: acc.triggers && acc.triggers.length > 0 ? acc.triggers.length : (score >= 60 ? 2 : 0),
					kycStatus: acc.status === 'Blocked' ? 'Suspended' : (acc.status === 'Critical' ? 'Failed' : 'Verified'),
					openCases: acc.status === 'Critical' ? 2 : (acc.status === 'Flagged' || acc.status === 'Under Review' ? 1 : 0),
					totalTxns: relatedTxs.length || 8,
					transactions: relatedTxs.slice(0, 5).map(t => ({
						id: t.id,
						type: t.type || 'Transfer',
						amount: (window.MuleGuardStore && window.MuleGuardStore.formatINR) ? window.MuleGuardStore.formatINR(t.amount || t.amountNumeric || 0) : ('₹' + (t.amount || 0)),
						time: t.timestamp || t.time || 'Recent',
						status: t.status || 'Completed'
					}))
				};
			});
		}

		function renderEntitiesTable() {
			initEntitiesFromStore();
			const tbody = document.getElementById('entities-tbody');
			if (!tbody) return;

			const entList = Object.values(entitiesDb);
			tbody.innerHTML = entList.map(e => {
				const riskColor = e.riskScore >= 80 ? 'text-red-600 bg-red-50 border-red-200' :
					(e.riskScore >= 60 ? 'text-orange-600 bg-orange-50 border-orange-200' :
					(e.riskScore >= 40 ? 'text-amber-600 bg-amber-50 border-amber-200' : 'text-blue-600 bg-blue-50 border-blue-200'));

				const statusBadgeClass = e.status === 'Blocked' ? 'bg-red-50 text-red-700 border-red-200' :
					(e.status === 'Flagged' || e.status === 'Critical' ? 'bg-orange-50 text-orange-700 border-orange-200' :
					(e.status === 'Under Review' ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-green-50 text-green-700 border-green-200'));

				return \`
					<tr class="hover:bg-[#f0f7ff]/70 transition-colors duration-150 group cursor-pointer" data-entity-id="\${e.id}" data-risk="\${e.riskTier}" data-status="\${e.status}" data-type="\${e.type}" onclick="rowClickAction(event, '\${e.id}')">
						<td class="py-3.5 px-4 font-mono-technical text-[13px] text-secondary font-bold hover:underline transition-all duration-150">\${e.id}</td>
						<td class="py-3.5 px-4 font-headline-md text-[13px] text-on-surface font-bold">\${e.name}</td>
						<td class="py-3.5 px-4 font-body-md text-[13px] text-on-surface">\${e.type}</td>
						<td class="py-3.5 px-4 font-mono-technical text-[13px] text-on-surface font-semibold text-right">\${e.balance}</td>
						<td class="py-3.5 px-4">
							<span class="font-mono-technical text-[12px] font-bold px-2 py-0.5 rounded border \${riskColor}">\${e.riskScore} / 100</span>
						</td>
						<td class="py-3.5 px-4 font-mono-technical text-[13px] text-on-surface-variant text-center font-bold">\${e.flags}</td>
						<td class="py-3.5 px-4">
							<span class="status-badge-cell px-2.5 py-0.5 rounded-full text-[11px] font-semibold border \${statusBadgeClass}">\${e.status}</span>
						</td>
						<td class="py-3.5 px-4 text-right">
							<button class="inspect-btn text-[12px] font-bold text-secondary hover:text-secondary-container focus:outline-none inline-flex items-center gap-1 group/btn" onclick="openDetailDrawer('\${e.id}')">
								Inspect <span class="inspect-arrow inline-block transition-transform duration-150">→</span>
							</button>
						</td>
					</tr>
				\`;
			}).join('');

			cacheDOMRows();
			recountSummaryCards();
		}
`;

const entDbObjRegex = /const entitiesDb = \{[\s\S]*?\n\t*\};/;
let newEntLastScript = entLastScript.replace(entDbObjRegex, dynEntDbCode);

// Also update DOMContentLoaded to call renderEntitiesTable()
newEntLastScript = newEntLastScript.replace(/window\.addEventListener\('DOMContentLoaded', \(\) => \{[\s\S]*?recountSummaryCards\(\);/i, `window.addEventListener('DOMContentLoaded', () => {
			renderEntitiesTable();`);

entHtml = entHtml.replace(entLastScript, newEntLastScript);
fs.writeFileSync('frontend/bank/investigator/entities.html', entHtml, 'utf8');
console.log('Saved frontend/bank/investigator/entities.html (len:', entHtml.length, ')');

// Save compliance version of entities
fs.writeFileSync('frontend/bank/compliance/entities.html', entHtml, 'utf8');
console.log('Saved frontend/bank/compliance/entities.html (len:', entHtml.length, ')');
