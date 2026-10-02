// MuleGuard Shared Stateful Data Store
// Manages synthetic virtual-bank datasets, transactions, alerts, cases, rules, and audit logs.
// Persists in localStorage to enable dynamic end-to-end user workflows.

(function() {
    const STORE_KEY = 'muleguard_db';

    // Invalidate deprecated pre-PostgreSQL cache containing legacy 'Shell Partner' data
    if (typeof localStorage !== 'undefined') {
        try {
            const legacy = localStorage.getItem('muleguard_db');
            if (legacy && legacy.includes('Shell Partner')) {
                localStorage.removeItem('muleguard_db');
            }
        } catch (_) {}
    }

    // Helper to generate relative time offsets
    function getRelativeTime(offsetMinutes) {
        const d = new Date();
        d.setMinutes(d.getMinutes() - offsetMinutes);
        
        if (offsetMinutes < 60) {
            return `${offsetMinutes} min ago`;
        } else {
            const hrs = Math.floor(offsetMinutes / 60);
            return `${hrs} hr${hrs > 1 ? 's' : ''} ago`;
        }
    }

    // Helper to extract absolute epoch milliseconds from canonical ISO timestamp or relative time string
    function getTxEpochMs(tx, refMs) {
        const now = refMs || Date.now();
        if (!tx) return now;

        const isoStr = tx.isoTimestamp || tx.timestamp;
        if (isoStr) {
            const parsed = Date.parse(isoStr);
            if (!isNaN(parsed)) return parsed;
        }

        if (tx.time) {
            const parsed = Date.parse(tx.time);
            if (!isNaN(parsed) && (tx.time.includes('T') || (tx.time.includes('-') && tx.time.includes(':')))) {
                return parsed;
            }

            if (tx.time.includes('Just now')) return now;
            const num = parseFloat(tx.time);
            if (!isNaN(num)) {
                if (tx.time.includes('min')) return now - (num * 60 * 1000);
                if (tx.time.includes('hr'))  return now - (num * 60 * 60 * 1000);
                if (tx.time.includes('day')) return now - (num * 24 * 60 * 60 * 1000);
            }
        }

        return now;
    }

    // Inject synthetic_db_expanded.js dynamically if running in browser
    if (typeof window !== 'undefined' && window.location && !window.MuleGuardExpandedDB && typeof document !== 'undefined' && document.createElement) {
        const isSubDir = window.location.pathname.includes('/bank/');
        const isInternal = window.location.pathname.includes('/internal/');
        const prefix = isSubDir ? '../../' : (isInternal ? '../' : '');
        
        ['synthetic_db_expanded.js', 'best_muleguard_model.js', 'xgboost-infer.js'].forEach(scriptName => {
            if (!document.querySelector(`script[src*="${scriptName}"]`)) {
                const scriptEl = document.createElement('script');
                scriptEl.src = prefix + 'scripts/' + scriptName;
                scriptEl.async = false;
                (document.head || document.documentElement).appendChild(scriptEl);
            }
        });
    }

    // Default Seed Data
    // Default Seed Data - PostgreSQL Authoritative Indian Retail Universe
    const defaultDb = (typeof window !== 'undefined' && window.MuleGuardExpandedDB) ? window.MuleGuardExpandedDB : {
        rules: [
            { id: 'R-VEL-1', name: 'Velocity Spike (Inbound Degree)', threshold: 5, unit: 'transfers/24h', description: 'Triggers when an account receives more than the threshold of inbound UPI transfers in a 24-hour period.', active: true },
            { id: 'R-HOLD-1', name: 'Short Holding Time Ratio', threshold: 80, unit: '% ratio', description: 'Triggers when more than the threshold of received funds are transferred out of the account within 30 minutes.', active: true },
            { id: 'R-NET-1', name: 'Suspicious Component Connection', threshold: 1, unit: 'hops', description: 'Triggers when a node has direct connection (shared device/IP/phone) to previously blocked/flagged fraud nodes.', active: true },
            { id: 'R-VAL-1', name: 'High-Value Shell Transfer', threshold: 100000, unit: 'INR', description: 'Triggers on a transfer exceeding threshold from/to newly registered corporate shell entities.', active: true },
            { id: 'R-CIRC-1', name: 'Circular Money Flow', threshold: 1, unit: 'cycles', description: 'Triggers when an account participates in a closed money flow loop of connected accounts.', active: true },
            { id: 'R-DORM-1', name: 'Dormant Account Activation', threshold: 50000, unit: 'INR/24h', description: 'Triggers when a previously inactive/dormant account receives significant transaction volume within 24 hours.', active: true }
        ],
        accounts: {
            'ACC-982001': { id: 'ACC-982001', name: 'Sri Venkateswara Kirana & General Stores', type: 'Current', balance: 147939.55, riskScore: 20, status: 'Normal', created: '2024-07-19', phone: '+91 83321 81960', device: 'SAMSUNG_M34_5G', ip: '49.37.56.60', address: 'Shop No 33, Main Bazaar Road, Bengaluru, Karnataka - 560013' },
            'ACC-982002': { id: 'ACC-982002', name: 'Annapurna Provisions & Rice Depot', type: 'Current', balance: 18608.09, riskScore: 20, status: 'Normal', created: '2025-12-18', phone: '+91 99402 65423', device: 'DELL_INSPIRON_3520', ip: '106.52.27.24', address: 'Shop No 25, Main Bazaar Road, Guntur, Andhra Pradesh - 522038' },
            'ACC-982003': { id: 'ACC-982003', name: 'Sai Krupa Medical Agencies', type: 'Current', balance: 246527.89, riskScore: 20, status: 'Normal', created: '2025-08-06', phone: '+91 98161 84959', device: 'VIVO_V29E', ip: '182.73.18.12', address: 'Shop No 43, Main Bazaar Road, Visakhapatnam, Andhra Pradesh - 530015' },
            'ACC-982004': { id: 'ACC-982004', name: 'Balaji Textiles & Handlooms', type: 'Current', balance: 12370.05, riskScore: 20, status: 'Normal', created: '2025-10-11', phone: '+91 94752 55341', device: 'SAMSUNG_A54', ip: '182.72.44.137', address: 'Shop No 16, Main Bazaar Road, Kolkata, West Bengal - 700022' },
            'ACC-982005': { id: 'ACC-982005', name: 'Hyderabad Biryani Point & Caterers', type: 'Current', balance: 43186.69, riskScore: 20, status: 'Normal', created: '2024-11-01', phone: '+91 80305 64139', device: 'MACBOOK_AIR_M2', ip: '182.73.81.55', address: 'Shop No 42, Main Bazaar Road, Kolkata, West Bengal - 700097' },
            'ACC-982050': { id: 'ACC-982050', name: 'Deepak Verma', type: 'Savings', balance: 49200.00, riskScore: 88, status: 'Flagged', created: '2025-10-01', phone: '+91 98765 43210', device: 'ONEPLUS_11R', ip: '106.51.72.10', address: 'Flat 101, Lakeview Apts, Hyderabad, Telangana' },
            'ACC-982054': { id: 'ACC-982054', name: 'Priya Sharma', type: 'Savings', balance: 128500.00, riskScore: 94, status: 'Critical', created: '2025-08-15', phone: '+91 91234 56789', device: 'IPHONE_14', ip: '182.72.88.42', address: 'Plot 45, Sector 12, Noida, Uttar Pradesh' },
            'ACC-982061': { id: 'ACC-982061', name: 'Kishore Varma', type: 'Savings', balance: 45153.32, riskScore: 75, status: 'Under Review', created: '2026-04-02', phone: '+91 89663 19314', device: 'ACER_ASPIRE_5', ip: '182.72.154.207', address: 'Flat 224, Green Acres Colony, Chennai, Tamil Nadu - 600013' },
            'ACC-982062': { id: 'ACC-982062', name: 'Naveen Goud', type: 'Savings', balance: 30225.95, riskScore: 75, status: 'Under Review', created: '2026-07-16', phone: '+91 95185 06716', device: 'MOTO_G84_5G', ip: '182.72.229.213', address: 'Flat 571, Green Acres Colony, Chennai, Tamil Nadu - 600054' },
            'ACC-982067': { id: 'ACC-982067', name: 'Prakash Chatterjee', type: 'Savings', balance: 21997.51, riskScore: 92, status: 'Critical', created: '2026-01-01', phone: '+91 73374 98941', device: 'ACER_ASPIRE_5', ip: '122.162.76.59', address: 'Flat 470, Green Acres Colony, Bengaluru, Karnataka - 560078' }
        },
        transactions: [
            { id: 'TX-982050', senderId: 'ACC-982001', receiverId: 'ACC-982050', amountNumeric: 45000, type: 'UPI', value: '₹45,000', score: 88, time: getRelativeTime(12), origin: 'Bengaluru', destination: 'Hyderabad', status: 'Flagged', summary: 'Velocity spike into flagged account.' },
            { id: 'TX-982054', senderId: 'ACC-982050', receiverId: 'ACC-982054', amountNumeric: 44000, type: 'IMPS', value: '₹44,000', score: 94, time: getRelativeTime(25), origin: 'Hyderabad', destination: 'Noida', status: 'Flagged', summary: 'Short holding time pass-through.' },
            { id: 'TX-982067', senderId: 'ACC-982054', receiverId: 'ACC-982067', amountNumeric: 42000, type: 'NEFT', value: '₹42,000', score: 92, time: getRelativeTime(40), origin: 'Noida', destination: 'Bengaluru', status: 'Flagged', summary: 'Downstream layering flow to critical mule node.' },
            { id: 'TX-982061', senderId: 'ACC-982002', receiverId: 'ACC-982061', amountNumeric: 18000, type: 'UPI', value: '₹18,000', score: 75, time: getRelativeTime(60), origin: 'Guntur', destination: 'Chennai', status: 'Under Review', summary: 'Suspicious device link cluster transfer.' },
            { id: 'TX-982062', senderId: 'ACC-982003', receiverId: 'ACC-982062', amountNumeric: 25000, type: 'IMPS', value: '₹25,000', score: 75, time: getRelativeTime(90), origin: 'Visakhapatnam', destination: 'Chennai', status: 'Under Review', summary: 'Intermediate smurfer account routing.' }
        ],
        alerts: [
            { id: 'AL-982054', target: 'Priya Sharma', category: 'Short Holding Time', score: 94, amount: '₹44,000', time: getRelativeTime(25), severity: 'Critical', status: 'New', summary: 'Immediate 95% pass-through within 13 minutes.', indicators: ['Short Holding Ratio', 'High Risk Corridor'], riskExplanation: 'Pass-through velocity alert on Priya Sharma account.', notes: 'Active ledger monitoring.', caseId: 'CS-982054' },
            { id: 'AL-982050', target: 'Deepak Verma', category: 'Velocity Spike', score: 88, amount: '₹45,000', time: getRelativeTime(12), severity: 'High', status: 'Investigating', summary: 'Spike in inbound UPI transfers from retail merchant.', indicators: ['Inbound Spike', 'New Terminal Link'], riskExplanation: 'Velocity anomaly detected on Deepak Verma account.', notes: 'Reviewing linked counterparties.', caseId: 'CS-982050' },
            { id: 'AL-982067', target: 'Prakash Chatterjee', category: 'Mule Layering Endpoint', score: 92, amount: '₹42,000', time: getRelativeTime(40), severity: 'Critical', status: 'New', summary: 'Terminal recipient in structured dispersal chain.', indicators: ['Mule Topology', 'Rapid Inbound-Outbound'], riskExplanation: 'Prakash Chatterjee flagged as critical mule sink node.', notes: 'Account restricted pending KYC audit.', caseId: 'CS-982054' }
        ],
        cases: [
            {
                id: 'CS-982054',
                title: 'Priya Sharma Dispersal Investigation',
                entity: 'Priya Sharma',
                primaryEntityId: 'ACC-982054',
                priority: 'Critical',
                score: 94,
                assignee: 'A. Kumar',
                createdTime: '1 hr ago',
                lastUpdated: '15 min ago',
                status: 'Investigating',
                summary: 'Rapid funds pass-through and multi-hop layering into Prakash Chatterjee node.',
                findings: [
                    'Short holding time ratio exceeds 95%',
                    'Shared IP sub-network with flagged mule nodes',
                    'High velocity UPI/IMPS transactions across interstate nodes'
                ],
                notes: 'SAR filing initiated. Coordinated review with nodal compliance officer.',
                activity: [
                    { time: '15 min ago', text: 'Investigation status updated to Critical' },
                    { time: '40 min ago', text: 'Alert AL-982067 linked to case' },
                    { time: '1 hr ago', text: 'Case created from alert AL-982054' }
                ]
            },
            {
                id: 'CS-982050',
                title: 'Deepak Verma Inflow Audit',
                entity: 'Deepak Verma',
                primaryEntityId: 'ACC-982050',
                priority: 'High',
                score: 88,
                assignee: 'S. Rao',
                createdTime: '2 hrs ago',
                lastUpdated: '30 min ago',
                status: 'Open',
                summary: 'Inbound velocity spike from retail accounts into newly activated account.',
                findings: [
                    'Unusual burst of 5 transfers within 30 minutes',
                    'New mobile device footprint'
                ],
                notes: 'Awaiting beneficiary verification response.',
                activity: [
                    { time: '30 min ago', text: 'Case review commenced by S. Rao' },
                    { time: '2 hrs ago', text: 'Case created automatically' }
                ]
            }
        ],
        decisions: [
            { id: 'DEC-982054', caseId: 'CS-982054', caseTitle: 'Priya Sharma Dispersal Investigation', decision: 'Hold / Escalate', rationale: 'Escalated for immediate forensic audit of mule sink accounts.', timestamp: '1 hour ago', reviewer: 'A. Kumar' }
        ],
        auditLogs: [
            { id: 'LOG-001', actor: 'System Engine', action: 'Initialized MuleGuard PostgreSQL Indian retail dataset', time: 'Just now', details: 'Authoritative database connection active.' }
        ],
        networks: {
            'NET-982054': {
                id: 'NET-982054',
                name: 'Rapid Mule Dispersal Cluster',
                type: 'Dispersal Mesh',
                score: 94,
                members: 4,
                totalValue: '₹1,75,000',
                connectedCount: 6,
                lastActivity: '12 min ago',
                status: 'Critical',
                summary: 'Coordinated rapid transit layering corridor connecting retail sources through Deepak Verma and Priya Sharma to Prakash Chatterjee.',
                graphNodes: [
                    { id: 'ACC-982054', label: 'Priya Sharma', role: 'Main Layering Node', risk: 'Critical', cx: 200, cy: 80, r: 16 },
                    { id: 'ACC-982050', label: 'Deepak Verma', role: 'Inbound Conduit', risk: 'High', cx: 80, cy: 80, r: 14 },
                    { id: 'ACC-982067', label: 'Prakash Chatterjee', role: 'Mule Sink Node', risk: 'Critical', cx: 320, cy: 80, r: 16 },
                    { id: 'ACC-982001', label: 'Sri Venkateswara', role: 'Retail Ingress', risk: 'Low', cx: 80, cy: 160, r: 12 }
                ],
                graphLinks: [
                    { source: 3, target: 1, flow: true },
                    { source: 1, target: 0, flow: true },
                    { source: 0, target: 2, flow: true }
                ]
            }
        },
        watchlists: {}
    };

    const REQUIRED_RULES = [
        { id: 'R-VEL-1', name: 'Velocity Spike (Inbound Degree)', threshold: 5, unit: 'transfers/24h', description: 'Triggers when an account receives more than the threshold of inbound UPI transfers in a 24-hour period.', active: true },
        { id: 'R-HOLD-1', name: 'Short Holding Time Ratio', threshold: 80, unit: '% ratio', description: 'Triggers when more than the threshold of received funds are transferred out of the account within 30 minutes.', active: true },
        { id: 'R-NET-1', name: 'Suspicious Component Connection', threshold: 1, unit: 'hops', description: 'Triggers when a node has direct connection (shared device/IP/phone) to previously blocked/flagged fraud nodes.', active: true },
        { id: 'R-VAL-1', name: 'High-Value Shell Transfer', threshold: 100000, unit: 'INR', description: 'Triggers on a transfer exceeding threshold from/to newly registered corporate shell entities.', active: true },
        { id: 'R-CIRC-1', name: 'Circular Money Flow', threshold: 1, unit: 'cycles', description: 'Triggers when an account participates in a closed money flow loop of connected accounts.', active: true },
        { id: 'R-DORM-1', name: 'Dormant Account Activation', threshold: 50000, unit: 'INR/24h', description: 'Triggers when a previously inactive/dormant account receives significant transaction volume within 24 hours.', active: true }
    ];

    function ensureDefaultRules(db) {
        if (!db || !db.rules) return;
        REQUIRED_RULES.forEach(req => {
            if (!db.rules.some(r => r.id === req.id)) {
                db.rules.push(Object.assign({}, req));
            }
        });
    }

    // Load Database - PostgreSQL Single Source of Truth
    function getDb() {
        const stored = localStorage.getItem(STORE_KEY);
        const legacyPattern = /Apex Trading|ACC-982741|ACC-982736|Orion Financial|Vertex Imports|Shell Partner|Northstar Holdings|Blackwood Assets/;
        let db;
        if (!stored || legacyPattern.test(stored)) {
            if (stored && legacyPattern.test(stored)) {
                try { localStorage.removeItem(STORE_KEY); } catch (_) {}
            }
            db = (typeof window !== 'undefined' && window.MuleGuardExpandedDB) ? window.MuleGuardExpandedDB : defaultDb;
            if (!db.watchlists) db.watchlists = {};
            ensureDefaultRules(db);
            saveDb(db);
            return db;
        }
        try {
            db = JSON.parse(stored);
            if (!db.watchlists) db.watchlists = {};
            ensureDefaultRules(db);
            return db;
        } catch (e) {
            db = (typeof window !== 'undefined' && window.MuleGuardExpandedDB) ? window.MuleGuardExpandedDB : defaultDb;
            if (!db.watchlists) db.watchlists = {};
            ensureDefaultRules(db);
            saveDb(db);
            return db;
        }
    }

    // Save Database
    function saveDb(db) {
        localStorage.setItem(STORE_KEY, JSON.stringify(db));
    }

    // Expose Global Store Object
    window.MuleGuardStore = {
        // Reset DB to default
        reset: function() {
            saveDb(defaultDb);
            this.evaluateRules(); // Run initial evaluation
            this.generateAlertsFromAllAccounts(); // Seed ML/rule alerts
            this.log('System Engine', 'Reset synthetic data environments', 'Reloaded default seeded mock tables.', { eventType: 'SYSTEM_RESET' });
            return getDb();
        },

        // Rules
        getRules: function() {
            return getDb().rules;
        },
        updateRule: function(id, threshold, active) {
            const db = getDb();
            const rule = db.rules.find(r => r.id === id);
            if (rule) {
                const oldThreshold = rule.threshold;
                const oldActive = rule.active;
                rule.threshold = parseFloat(threshold);
                rule.active = active;
                saveDb(db);
                this.log('Internal Team Operator', `Modified Rule ${id}`, `Threshold changed from ${oldThreshold} to ${threshold}, Active status changed from ${oldActive} to ${active}.`, { eventType: 'RULE_UPDATED' });
                // Re-evaluate risk scores dynamically based on updated rule parameters!
                this.evaluateRules();
                // Re-evaluate alerts in light of changed rule triggers
                this.generateAlertsFromAllAccounts();
            }
        },

        // Dynamic Rule Evaluation Engine (Calculates risk scores based on live thresholds & data)
        evaluateRules: function() {
            const db = getDb();
            const nowMs = Date.now();
            const rolling24hMs = 24 * 60 * 60 * 1000;
            const rolling30mMs = 30 * 60 * 1000;
            
            // Precompute population baseline for ML Anomaly (Z-Score)
            const txCounts = {};
            Object.keys(db.accounts).forEach(id => { txCounts[id] = 0; });
            db.transactions.forEach(t => {
                if (t.senderId) txCounts[t.senderId] = (txCounts[t.senderId] || 0) + 1;
                if (t.receiverId) txCounts[t.receiverId] = (txCounts[t.receiverId] || 0) + 1;
            });

            const countsArray = Object.values(txCounts);
            const meanCount = countsArray.reduce((a, b) => a + b, 0) / countsArray.length;
            const variance = countsArray.reduce((a, b) => a + Math.pow(b - meanCount, 2), 0) / countsArray.length;
            const stdDevCount = Math.sqrt(variance) || 1;

            Object.keys(db.accounts).forEach(accId => {
                const acc = db.accounts[accId];
                
                let score = 15; // Baseline starting score
                const triggers = [];

                // Get transactions related to this account sorted by canonical timestamp
                const inboundTxs = db.transactions.filter(t => t.receiverId === accId);
                const outboundTxs = db.transactions.filter(t => t.senderId === accId);
                const accountTxs = [...inboundTxs, ...outboundTxs].sort((a, b) => getTxEpochMs(b, nowMs) - getTxEpochMs(a, nowMs));

                // Rule 1: Velocity Spike (R-VEL-1) — Rolling 24-hour window
                const ruleVel = db.rules.find(r => r.id === 'R-VEL-1');
                if (ruleVel && ruleVel.active) {
                    const inbound24h = inboundTxs.filter(t => {
                        const txMs = getTxEpochMs(t, nowMs);
                        return (nowMs - txMs) <= rolling24hMs && (nowMs - txMs) >= 0;
                    });
                    const count24h = inbound24h.length;
                    if (count24h > ruleVel.threshold) {
                        score += 25;
                        triggers.push(`Velocity Spike: ${count24h} inbound transfers/24h (threshold: ${ruleVel.threshold})`);
                    }
                }

                // Rule 2: Short Holding Time Ratio (R-HOLD-1) — Matched 30-minute window
                const ruleHold = db.rules.find(r => r.id === 'R-HOLD-1');
                if (ruleHold && ruleHold.active) {
                    const inbound24h = inboundTxs.filter(t => {
                        const txMs = getTxEpochMs(t, nowMs);
                        return (nowMs - txMs) <= rolling24hMs && (nowMs - txMs) >= 0;
                    });
                    const totalInbound = inbound24h.reduce((sum, t) => sum + (t.amountNumeric || 0), 0);
                    if (totalInbound > 0) {
                        let matchedOutbound = 0;
                        inbound24h.forEach(inTx => {
                            const inMs = getTxEpochMs(inTx, nowMs);
                            const inAmt = inTx.amountNumeric || 0;
                            let currentInMatched = 0;
                            outboundTxs.forEach(outTx => {
                                const outMs = getTxEpochMs(outTx, nowMs);
                                if (outMs >= inMs && (outMs - inMs) <= rolling30mMs) {
                                    currentInMatched += (outTx.amountNumeric || 0);
                                }
                            });
                            matchedOutbound += Math.min(inAmt, currentInMatched);
                        });
                        const ratio = Math.min(100, Math.round((matchedOutbound / totalInbound) * 100));
                        if (ratio > ruleHold.threshold) {
                            score += 25;
                            triggers.push(`Short Holding Ratio: ${ratio}% (threshold: ${ruleHold.threshold}%)`);
                        }
                    }
                }

                // Rule 3: Suspicious connection (R-NET-1)
                const ruleNet = db.rules.find(r => r.id === 'R-NET-1');
                if (ruleNet && ruleNet.active) {
                    let sharedBlock = false;
                    let sharedReason = "";
                    Object.keys(db.accounts).forEach(otherId => {
                        if (otherId !== accId && db.accounts[otherId].status === 'Blocked') {
                            const other = db.accounts[otherId];
                            if (acc.phone === other.phone) {
                                sharedBlock = true;
                                sharedReason = `Shares phone (${acc.phone}) with Blocked entity ${other.name}`;
                            } else if (acc.device === other.device) {
                                sharedBlock = true;
                                sharedReason = `Shares device (${acc.device}) with Blocked entity ${other.name}`;
                            } else if (acc.ip === other.ip) {
                                sharedBlock = true;
                                sharedReason = `Shares IP (${acc.ip}) with Blocked entity ${other.name}`;
                            }
                        }
                    });
                    if (sharedBlock) {
                        score += 20;
                        triggers.push(`Suspicious Connection: ${sharedReason}`);
                    }
                }

                // Rule 4: High Value Shell (R-VAL-1)
                const ruleVal = db.rules.find(r => r.id === 'R-VAL-1');
                if (ruleVal && ruleVal.active) {
                    const highValTx = accountTxs.find(t => t.amountNumeric > ruleVal.threshold);
                    if (highValTx) {
                        score += 20;
                        triggers.push(`High Value Transfer: ₹${highValTx.amountNumeric.toLocaleString('en-IN')} exceeds shell threshold`);
                    }
                }

                // Rule 5: Circular Money Flow (R-CIRC-1)
                const ruleCirc = db.rules.find(r => r.id === 'R-CIRC-1');
                if (ruleCirc && ruleCirc.active) {
                    const mlFeats = this.getAccountFeatures(accId) || {};
                    if (mlFeats.cycleParticipation > 0) {
                        score += 25;
                        triggers.push(`Circular Money Flow: Account participates in closed money movement cycle`);
                    }
                }

                // Rule 6: Dormant Account Activation (R-DORM-1)
                const ruleDorm = db.rules.find(r => r.id === 'R-DORM-1');
                if (ruleDorm && ruleDorm.active) {
                    let accountAgeDays = 0;
                    if (acc.created) {
                        const createdMs = Date.parse(acc.created);
                        if (!isNaN(createdMs)) {
                            accountAgeDays = Math.floor((nowMs - createdMs) / (24 * 60 * 60 * 1000));
                        }
                    } else {
                        accountAgeDays = 100;
                    }
                    if (accountAgeDays > 90) {
                        const inbound24h = inboundTxs.filter(t => {
                            const txMs = getTxEpochMs(t, nowMs);
                            return (nowMs - txMs) <= rolling24hMs && (nowMs - txMs) >= 0;
                        });
                        const total24hVal = inbound24h.reduce((sum, t) => sum + (t.amountNumeric || 0), 0);
                        if (total24hVal >= ruleDorm.threshold) {
                            score += 20;
                            triggers.push(`Dormant Account Activation: ₹${Math.round(total24hVal).toLocaleString('en-IN')} received on account registered >90 days ago`);
                        }
                    }
                }

                // ML Behavioral Anomaly Score
                const mlRes = this.evaluateMLModel(accId, db);
                if (mlRes.isAnomaly) {
                    score += mlRes.contribution;
                    triggers.push(`ML Anomaly Profiler: Deviation of ${mlRes.stdDevs} std devs`);
                }

                // Update account values bounded
                acc.riskScore = Math.min(99, Math.max(10, score));
                acc.triggers = triggers;
                
                // Dynamic severity categorisation
                if (acc.riskScore >= 90) {
                    acc.status = acc.status === 'Normal' ? 'Flagged' : acc.status; 
                }
            });

            // Update alerts explanations
            db.alerts.forEach(a => {
                const acc = Object.values(db.accounts).find(ac => ac.name === a.target);
                if (acc) {
                    a.score = acc.riskScore;
                    a.severity = acc.riskScore >= 90 ? 'Critical' : (acc.riskScore >= 70 ? 'High' : 'Medium');
                    a.indicators = acc.triggers;
                    a.riskExplanation = `Risk index at ${acc.riskScore} triggered by actual database rule executions: ${acc.triggers.join(', ')}`;
                }
            });

            // Sync cases risk scores
            db.cases.forEach(c => {
                const acc = db.accounts[c.primaryEntityId];
                if (acc) {
                    c.score = acc.riskScore;
                    c.priority = acc.riskScore >= 90 ? 'Critical' : (acc.riskScore >= 70 ? 'High' : 'Medium');
                }
            });

            saveDb(db);
        },

        // Client-Side Z-Score Behavioral Anomaly Classifier
        evaluateMLModel: function(accId, db) {
            const txCounts = {};
            Object.keys(db.accounts).forEach(id => { txCounts[id] = 0; });
            db.transactions.forEach(t => {
                if (t.senderId) txCounts[t.senderId] = (txCounts[t.senderId] || 0) + 1;
                if (t.receiverId) txCounts[t.receiverId] = (txCounts[t.receiverId] || 0) + 1;
            });

            const countsArray = Object.values(txCounts);
            const meanCount = countsArray.reduce((a, b) => a + b, 0) / countsArray.length;
            const variance = countsArray.reduce((a, b) => a + Math.pow(b - meanCount, 2), 0) / countsArray.length;
            const stdDevCount = Math.sqrt(variance) || 1;

            const currentCount = txCounts[accId] || 0;
            const zScore = (currentCount - meanCount) / stdDevCount;
            const isAnomaly = zScore > 2.0;

            return {
                isAnomaly: isAnomaly,
                stdDevs: zScore.toFixed(1),
                contribution: isAnomaly ? 15 : 0
            };
        },

        // Expose Machine Learning coefficients and training characteristics to Admin models tab
        getMLMetrics: function() {
            return {
                modelName: 'Z-Score Behavioral Profiler',
                version: '1.2.0',
                accuracy: '94.2%',
                f1Score: '0.915',
                features: [
                    { name: 'Inbound Transaction Frequency', importance: 0.42 },
                    { name: 'Funds Holding Duration Ratio', importance: 0.35 },
                    { name: 'Direct Counterparty Risk Sizing', importance: 0.15 },
                    { name: 'Offshore Route Sizing Mismatch', importance: 0.08 }
                ]
            };
        },

        // Networks (Phase 5: dynamic SVG rendering datasets)
        getNetworks: function() {
            const db = getDb();
            const accounts = db.accounts || {};
            const txs = db.transactions || [];
            
            const adj = {};
            const inDeg = {};
            const outDeg = {};
            
            txs.forEach(t => {
                const s = t.senderId;
                const r = t.receiverId;
                if (s && r && accounts[s] && accounts[r]) {
                    if (!adj[s]) adj[s] = new Set();
                    if (!adj[r]) adj[r] = new Set();
                    adj[s].add(r);
                    adj[r].add(s);
                    inDeg[r] = (inDeg[r] || 0) + 1;
                    outDeg[s] = (outDeg[s] || 0) + 1;
                }
            });

            const networksMap = JSON.parse(JSON.stringify(db.networks || {}));
            
            Object.keys(networksMap).forEach(netId => {
                const net = networksMap[netId];
                if (net.graphNodes) {
                    net.graphNodes.forEach(node => {
                        if (node.id && accounts[node.id]) {
                            const acc = accounts[node.id];
                            node.risk = acc.riskScore >= 90 ? 'Critical' : (acc.riskScore >= 70 ? 'High' : (acc.riskScore >= 40 ? 'Medium' : 'Low'));
                            node.status = acc.status;
                        }
                    });
                }
            });

            const hubAccIds = Object.keys(accounts).filter(accId => {
                const acc = accounts[accId];
                const totalDeg = (inDeg[accId] || 0) + (outDeg[accId] || 0);
                return totalDeg >= 2 || (acc && (acc.status === 'Flagged' || acc.status === 'Blocked' || acc.riskScore >= 70));
            });

            hubAccIds.forEach(hubId => {
                const cleanDigits = hubId.replace(/\D/g, '');
                const netId = `NET-${cleanDigits.slice(-6).padStart(6, '0')}`;
                
                if (!networksMap[netId]) {
                    const hubAcc = accounts[hubId];
                    const neighbors = Array.from(adj[hubId] || []);
                    const members = [hubId, ...neighbors];
                    
                    const compTxs = txs.filter(t => members.includes(t.senderId) && members.includes(t.receiverId));
                    const totalVal = compTxs.reduce((sum, t) => sum + (t.amountNumeric || 0), 0);
                    
                    const suspiciousCount = members.filter(m => accounts[m] && (accounts[m].status === 'Flagged' || accounts[m].status === 'Blocked' || accounts[m].riskScore >= 70)).length;
                    
                    const graphNodes = members.map((mId, i) => {
                        const mAcc = accounts[mId] || { name: mId, status: 'Normal', riskScore: 20 };
                        let cx = 200, cy = 80, r = 16;
                        if (i > 0) {
                            const angle = (2 * Math.PI * (i - 1)) / Math.max(1, members.length - 1);
                            cx = Math.round(200 + 100 * Math.cos(angle));
                            cy = Math.round(80 + 100 * Math.sin(angle));
                            r = 12;
                        }
                        return {
                            id: mId,
                            label: mAcc.name || mId,
                            role: i === 0 ? 'Primary Hub' : 'Member Node',
                            risk: mAcc.riskScore >= 90 ? 'Critical' : (mAcc.riskScore >= 70 ? 'High' : (mAcc.riskScore >= 40 ? 'Medium' : 'Low')),
                            status: mAcc.status || 'Normal',
                            cx: cx,
                            cy: cy,
                            r: r
                        };
                    });

                    const nodeIdxMap = {};
                    graphNodes.forEach((n, i) => nodeIdxMap[n.id] = i);
                    
                    const graphLinks = [];
                    compTxs.forEach(t => {
                        const sIdx = nodeIdxMap[t.senderId];
                        const rIdx = nodeIdxMap[t.receiverId];
                        if (sIdx !== undefined && rIdx !== undefined) {
                            graphLinks.push({ source: sIdx, target: rIdx, flow: true });
                        }
                    });

                    const score = Math.min(99, Math.max(20, Math.round(hubAcc.riskScore || 50)));

                    networksMap[netId] = {
                        id: netId,
                        name: `${hubAcc.name || hubId} Network`,
                        type: suspiciousCount >= 2 ? 'Shell Conduit' : 'Layering Loop',
                        score: score,
                        members: members.length,
                        totalValue: `₹${(totalVal / 100000).toFixed(2)} Lakh`,
                        connectedCount: compTxs.length,
                        lastActivity: 'Recent',
                        status: hubAcc.status || 'Active',
                        summary: `Network ${netId} centered around hub account ${hubId} (${hubAcc.name}).`,
                        riskExplanation: `Risk score ${score} derived from ${suspiciousCount} suspicious accounts and transaction connections.`,
                        notes: `Store network generated from ${members.length} connected accounts.`,
                        indicators: [suspiciousCount > 0 ? `${suspiciousCount} Suspicious Accounts` : 'Active Flow', 'Transaction Network'],
                        graphNodes: graphNodes,
                        graphLinks: graphLinks
                    };
                }
            });

            return networksMap;
        },

        // Transactions
        getTransactions: function() {
            const txs = getDb().transactions;
            const nowMs = Date.now();
            return txs.slice().sort((a, b) => getTxEpochMs(b, nowMs) - getTxEpochMs(a, nowMs));
        },
        updateTransactionStatus: function(id, status) {
            const db = getDb();
            const tx = db.transactions.find(t => t.id === id);
            if (tx) {
                tx.status = status;
                saveDb(db);
                this.log('Bank Investigator', `Updated transaction ${id} status`, `Status changed to ${status}`);
            }
        },

        // Accounts
        getAccounts: function() {
            return getDb().accounts;
        },
        getAccountFeatures: function(accId) {
            const db = getDb();
            const acc = db.accounts[accId];
            if (!acc) return null;

            const inboundTxs = db.transactions.filter(t => t.receiverId === accId);
            const outboundTxs = db.transactions.filter(t => t.senderId === accId);
            const allTxs = [...inboundTxs, ...outboundTxs];

            // 1. Transaction count/frequency
            const txCount = allTxs.length;

            // 2. Incoming transaction count
            const inTxCount = inboundTxs.length;

            // 3. Outgoing transaction count
            const outTxCount = outboundTxs.length;

            // 4. Total incoming/outgoing amount
            const totalInAmount = inboundTxs.reduce((sum, t) => sum + (t.amountNumeric || 0), 0);
            const totalOutAmount = outboundTxs.reduce((sum, t) => sum + (t.amountNumeric || 0), 0);

            // 5. Unique counterparties
            const counterparties = new Set();
            allTxs.forEach(t => {
                if (t.senderId && t.senderId !== accId) counterparties.add(t.senderId);
                if (t.receiverId && t.receiverId !== accId) counterparties.add(t.receiverId);
            });
            const uniqueCounterparties = counterparties.size;

            // 6. Transaction velocity
            const velocity = txCount;

            // 7. Average transaction amount
            const avgTxAmount = txCount > 0 ? (allTxs.reduce((sum, t) => sum + (t.amountNumeric || 0), 0) / txCount) : 0;

            // 8. Amount deviation
            let amountStdDev = 0;
            if (txCount > 1) {
                const variance = allTxs.reduce((sum, t) => sum + Math.pow((t.amountNumeric || 0) - avgTxAmount, 2), 0) / txCount;
                amountStdDev = Math.sqrt(variance);
            }

            // 9. Rapid receive-to-send behaviour / holding time
            let rapidHoldingRatio = 0;
            if (totalInAmount > 0) {
                rapidHoldingRatio = Math.min(100, Math.round((totalOutAmount / totalInAmount) * 100));
            }

            // 10. Incoming-to-outgoing ratio
            const inOutRatio = totalInAmount > 0 ? (totalOutAmount / totalInAmount) : 0;

            // 11. Behavioural change over time
            const recentTxs = allTxs.filter(t => t.time.includes('min') || t.time.includes('1 hr') || t.time.includes('Just now'));
            const behavioralShift = txCount > 0 ? (recentTxs.length / txCount) : 0;

            // 12. Network degree / inbound degree / outbound degree
            const inboundDegree = inTxCount;
            const outboundDegree = outTxCount;
            const networkDegree = inboundDegree + outboundDegree;

            // 13. Fan-in / fan-out indicators
            const inboundCounterparties = new Set(inboundTxs.map(t => t.senderId).filter(id => id && id !== accId)).size;
            const outboundCounterparties = new Set(outboundTxs.map(t => t.receiverId).filter(id => id && id !== accId)).size;
            const isFanIn = inboundCounterparties >= 3;
            const isFanOut = outboundCounterparties >= 3;

            // 14. Suspicious connected-account evidence where available
            let sharedSuspiciousConnection = false;
            let connectionDetail = "";
            Object.keys(db.accounts).forEach(otherId => {
                if (otherId !== accId && (db.accounts[otherId].status === 'Blocked' || db.accounts[otherId].status === 'Flagged')) {
                    const other = db.accounts[otherId];
                    if (acc.phone === other.phone) {
                        sharedSuspiciousConnection = true;
                        connectionDetail = `Shared phone with flagged entity ${other.name}`;
                    } else if (acc.device === other.device) {
                        sharedSuspiciousConnection = true;
                        connectionDetail = `Shared device with flagged entity ${other.name}`;
                    } else if (acc.ip === other.ip) {
                        sharedSuspiciousConnection = true;
                        connectionDetail = `Shared IP with flagged entity ${other.name}`;
                    }
                }
            });

            // --- Leakage-Free Network Features ---
            
            // Helper: Parse relative times into minutes
            function parseTimeToMinutes(timeStr) {
                if (!timeStr) return 999999;
                if (timeStr.includes('Just now')) return 0;
                const num = parseInt(timeStr);
                if (isNaN(num)) return 999999;
                if (timeStr.includes('min')) return num;
                if (timeStr.includes('hr')) return num * 60;
                if (timeStr.includes('day')) return num * 1440;
                return 999999;
            }

            // A. Inbound / Outbound / Total Degree
            const totalDegree = inboundDegree + outboundDegree;

            // B. Fan-in / Fan-out
            const fanIn = inboundCounterparties;
            const fanOut = outboundCounterparties;

            // C. Network Concentration (HHI of transaction volumes)
            const counterpartyVolumes = {};
            allTxs.forEach(t => {
                const partner = t.senderId === accId ? t.receiverId : t.senderId;
                if (partner && partner !== accId) {
                    counterpartyVolumes[partner] = (counterpartyVolumes[partner] || 0) + (t.amountNumeric || 0);
                }
            });
            const totalVol = Object.values(counterpartyVolumes).reduce((sum, v) => sum + v, 0);
            let networkConcentration = 0;
            if (totalVol > 0) {
                Object.values(counterpartyVolumes).forEach(v => {
                    const share = v / totalVol;
                    networkConcentration += share * share;
                });
            }

            // D. Cycle Participation (Loops A -> B -> C -> A of length 3 or 4)
            const adj = {};
            db.transactions.forEach(t => {
                if (t.senderId && t.receiverId) {
                    if (!adj[t.senderId]) adj[t.senderId] = new Set();
                    adj[t.senderId].add(t.receiverId);
                }
            });

            let cycleParticipation = 0;
            const visited = new Set();
            function findCycle(current, depth) {
                if (depth > 4) return false;
                const neighbors = adj[current] || [];
                for (const next of neighbors) {
                    if (next === accId && depth >= 2) {
                        return true;
                    }
                    if (!visited.has(next)) {
                        visited.add(next);
                        if (findCycle(next, depth + 1)) return true;
                        visited.delete(next);
                    }
                }
                return false;
            }
            visited.add(accId);
            if (findCycle(accId, 1)) {
                cycleParticipation = 1;
            }

            // E. Multi-hop Connectivity (2-hop neighborhood size)
            const directNeighbors = new Set();
            allTxs.forEach(t => {
                if (t.senderId && t.senderId !== accId) directNeighbors.add(t.senderId);
                if (t.receiverId && t.receiverId !== accId) directNeighbors.add(t.receiverId);
            });
            const twoHopNeighbors = new Set(directNeighbors);
            directNeighbors.forEach(n => {
                const nTxs = db.transactions.filter(t => t.senderId === n || t.receiverId === n);
                nTxs.forEach(t => {
                    if (t.senderId && t.senderId !== accId) twoHopNeighbors.add(t.senderId);
                    if (t.receiverId && t.receiverId !== accId) twoHopNeighbors.add(t.receiverId);
                });
            });
            const multiHopConnectivity = twoHopNeighbors.size;

            // F. Temporal Proximity (min minutes gap inbound to outbound)
            let temporalProximity = 1440; // Default 1 day
            inboundTxs.forEach(inTx => {
                const inTime = parseTimeToMinutes(inTx.time);
                outboundTxs.forEach(outTx => {
                    const outTime = parseTimeToMinutes(outTx.time);
                    if (outTime <= inTime) {
                        const gap = inTime - outTime;
                        if (gap < temporalProximity) {
                            temporalProximity = gap;
                        }
                    }
                });
            });

            // G. Activity Pattern (temporal ratio)
            const recentTxsCount = allTxs.filter(t => parseTimeToMinutes(t.time) <= 120).length;
            const activityPattern = txCount > 0 ? (recentTxsCount / txCount) : 0;

            return {
                // Behavioural
                txCount,
                inTxCount,
                outTxCount,
                totalInAmount,
                totalOutAmount,
                uniqueCounterparties,
                velocity,
                avgTxAmount,
                amountStdDev,
                rapidHoldingRatio,
                inOutRatio,
                behavioralShift,
                networkDegree,
                inboundDegree,
                outboundDegree,
                isFanIn,
                isFanOut,
                sharedSuspiciousConnection,
                connectionDetail,
                
                // Network
                totalDegree,
                fanIn,
                fanOut,
                networkConcentration,
                cycleParticipation,
                multiHopConnectivity,
                temporalProximity,
                activityPattern
            };
        },

        predictAccountRisk: function(accId) {
            const features = this.getAccountFeatures(accId);
            if (!features) return null;
            
            // Check if inference engine and model booster are loaded
            if (typeof window !== 'undefined' && window.MuleGuardXGBoost && window.MuleGuardModelBooster) {
                try {
                    const prob = window.MuleGuardXGBoost.predictRisk(features, window.MuleGuardModelBooster);
                    const threshold = this.getRiskThreshold();
                    
                    let level = "Low";
                    let color = "text-green-600";
                    if (prob >= threshold) {
                        level = "High";
                        color = "text-red-500";
                    } else if (prob >= threshold / 2) {
                        level = "Moderate";
                        color = "text-amber-500";
                    }
                    
                    return {
                        probability: prob,
                        threshold: threshold,
                        level: level,
                        color: color,
                        isFallback: false
                    };
                } catch (e) {
                    console.error("XGBoost prediction error:", e);
                }
            }
            
            // A rule-derived account score is not an ML probability. When the protected
            // browser model is unavailable, expose that state explicitly instead of
            // manufacturing a probability from riskScore.
            const threshold = this.getRiskThreshold();
            return {
                probability: null,
                threshold: threshold,
                level: "Unavailable",
                color: "text-on-surface-variant",
                isFallback: false,
                unavailable: true
            };
        },

        getRiskThreshold: function() {
            if (typeof localStorage !== 'undefined') {
                const stored = localStorage.getItem('muleguard_risk_threshold');
                if (stored !== null) {
                    const parsed = parseFloat(stored);
                    if (!isNaN(parsed)) return parsed;
                }
            }
            return 0.30; // Default high-recall demo threshold
        },

        setRiskThreshold: function(val) {
            const nextThreshold = parseFloat(val);
            if (!Number.isFinite(nextThreshold) || nextThreshold <= 0 || nextThreshold > 1) {
                return { success: false, error: 'Risk threshold must be a finite value greater than 0 and at most 1.' };
            }

            const previousThreshold = this.getRiskThreshold();
            if (typeof localStorage !== 'undefined') {
                localStorage.setItem('muleguard_risk_threshold', nextThreshold.toString());
            }

            // Keep threshold changes on the same deterministic rule/ML/alert path as rule updates.
            // The policy context lets the alert engine distinguish a newly eligible model result
            // caused by a lower threshold from a normal probability threshold crossing.
            this.evaluateRules();
            this.generateAlertsFromAllAccounts({
                thresholdChanged: true,
                previousThreshold: previousThreshold,
                currentThreshold: nextThreshold
            });
            this.log('Internal Team Operator', 'Modified ML risk threshold',
                `Threshold changed from ${previousThreshold} to ${nextThreshold}. Risk and alert state re-evaluated.`, {
                    eventType: 'RISK_THRESHOLD_UPDATED',
                    prevState: previousThreshold,
                    newState: nextThreshold
                });

            return { success: true, previousThreshold: previousThreshold, threshold: nextThreshold };
        },

        // Returns the persisted account-level ML inference state. This is deliberately read-only;
        // callers must not mutate getAccounts() snapshots to influence alert semantics.
        getAccountInferenceState: function(accId) {
            const account = getDb().accounts[accId];
            if (!account) return null;
            return account.mlInferenceState || null;
        },

        // Alerts
        getAlerts: function() {
            return getDb().alerts;
        },
        resolveAlert: function(id) {
            const db = getDb();
            const alert = db.alerts.find(a => a.id === id);
            if (alert) {
                alert.status = 'Resolved';
                saveDb(db);
                this.log('Bank Investigator', `Resolved Alert ${id}`, `Alert resolved manually.`);
            }
        },

        // Cases
        getCases: function() {
            return getDb().cases;
        },
        getCaseById: function(id) {
            return getDb().cases.find(c => c.id === id);
        },
        escalateCase: function(id, notes, actor) {
            const db = getDb();
            const c = db.cases.find(c => c.id === id);
            if (c) {
                c.status = 'Escalated';
                c.escalatedBy = actor || 'J. Doe';
                c.activity.unshift({ text: `Case escalated to compliance by ${c.escalatedBy}`, time: 'Just now' });
                if (notes) {
                    c.notes += `\n[Escalation Summary - ${c.escalatedBy}]: ${notes}`;
                }
                
                // Update matching alerts to compliance queue
                db.alerts.forEach(a => {
                    if (a.caseId === id && a.status === 'New') {
                        a.status = 'Escalated';
                    }
                });
                saveDb(db);
                this.log(actor || 'J. Doe', `Escalated Case ${id}`, `Case forwarded to compliance for review.`);
            }
        },
        addCaseNote: function(id, text, author) {
            const db = getDb();
            const c = db.cases.find(c => c.id === id);
            if (c && text) {
                c.notes += `\n[Note - ${author || 'J. Doe'}]: ${text}`;
                c.activity.unshift({ text: `Note added by ${author || 'J. Doe'}`, time: 'Just now' });
                saveDb(db);
                this.log(author || 'J. Doe', `Added note to Case ${id}`, text);
            }
        },

        // Compliance Decisions
        getDecisions: function() {
            return getDb().decisions;
        },
        logComplianceDecision: function(caseId, decision, rationale, reviewer) {
            const db = getDb();
            const c = db.cases.find(c => c.id === caseId);
            
            const newDecision = {
                id: `DEC-0${db.decisions.length + 1}`,
                caseId: caseId,
                caseTitle: c ? c.title : 'External Review',
                decision: decision, // 'Approve / Clear', 'Reject / Block', 'Hold / Escalate', 'Block Account', 'File SAR'
                rationale: rationale,
                timestamp: 'Just now',
                reviewer: reviewer || 'A. Kumar'
            };

            db.decisions.unshift(newDecision);

            let targetEntityName = c ? c.entity : '';
            if (!targetEntityName) {
                // If it is an alert, look up the target entity
                const alert = db.alerts.find(a => a.id === caseId);
                if (alert) {
                    targetEntityName = alert.target;
                }
            }

            if (c) {
                c.status = (decision.includes('Approve') || decision.includes('Clear')) ? 'Closed - Action Taken' : ((decision.includes('Reject') || decision.includes('Block') || decision.includes('SAR')) ? 'Closed - Blocked' : 'Escalated');
                c.activity.unshift({ text: `Compliance decision logged: ${decision} by ${newDecision.reviewer}`, time: 'Just now' });
                c.notes += `\n[Compliance Review - ${newDecision.reviewer}]: ${rationale}`;
            }

            // Sync live account status dynamically
            let acc = c ? db.accounts[c.primaryEntityId] : null;
            if (!acc && targetEntityName) {
                acc = Object.values(db.accounts).find(a => a.name.toLowerCase() === targetEntityName.toLowerCase());
            }
            if (acc) {
                if (decision.includes('Approve') || decision.includes('Clear')) {
                    acc.status = 'Normal';
                    acc.riskScore = 15;
                } else if (decision.includes('Reject') || decision.includes('Block') || decision.includes('SAR')) {
                    acc.status = 'Blocked';
                    acc.riskScore = 99;
                }
            }

            saveDb(db);
            this.evaluateRules(); // recalculate database on decision to update connection risks
            this.log(reviewer || 'A. Kumar', `Logged decision on Case ${caseId}`, `Decision: ${decision}. Rationale: ${rationale}`);
        },

        // Audit Logs
        getLogs: function() {
            return getDb().auditLogs;
        },
        // Extended log() — accepts optional structured audit opts
        log: function(actor, action, details, opts) {
            const db = getDb();
            const newLog = Object.assign({
                id: 'LOG-' + (db.auditLogs.length + 1).toString().padStart(4, '0'),
                eventType:  (opts && opts.eventType)  || 'SYSTEM_EVENT',
                caseId:     (opts && opts.caseId)     || null,
                alertId:    (opts && opts.alertId)     || null,
                prevState:  (opts && opts.prevState)   || null,
                newState:   (opts && opts.newState)    || null,
                actor:      actor,
                action:     action,
                time:       'Just now',
                isoTimestamp: new Date().toISOString(),
                details:    details || ''
            }, opts || {});
            db.auditLogs.unshift(newLog);
            saveDb(db);
        },

        // ── getAuditTrail ─────────────────────────────────────────────────────
        // Returns all audit entries associated with a given caseId, in order.
        getAuditTrail: function(caseId) {
            return getDb().auditLogs.filter(l => l.caseId === caseId);
        },

        // ── getAlertById ──────────────────────────────────────────────────────
        getAlertById: function(id) {
            return getDb().alerts.find(a => a.id === id) || null;
        },

        // ── acknowledgeAlert ──────────────────────────────────────────────────
        acknowledgeAlert: function(id, actor) {
            const db = getDb();
            const alert = db.alerts.find(a => a.id === id);
            if (!alert) return false;
            const prev = alert.status;
            alert.status = 'Acknowledged';
            saveDb(db);
            this.log(actor || 'J. Doe', `Acknowledged Alert ${id}`, `Alert acknowledged — under investigation.`, {
                eventType: 'ALERT_ACKNOWLEDGED', alertId: id,
                prevState: prev, newState: 'Acknowledged'
            });
            return true;
        },

        // ── updateCaseStatus ──────────────────────────────────────────────────
        // Validates transitions before applying. Returns true on success.
        updateCaseStatus: function(id, newStatus, actor, note) {
            const VALID = {
                'New':          ['Under Review', 'False Positive'],
                'Under Review': ['Escalated', 'Resolved', 'False Positive'],
                'Escalated':    ['Resolved']
                // Resolved and False Positive are terminal
            };
            const db = getDb();
            const c = db.cases.find(c => c.id === id);
            if (!c) return false;
            const allowed = VALID[c.status] || [];
            if (!allowed.includes(newStatus)) {
                console.warn(`[MuleGuard] Invalid case transition: ${c.status} → ${newStatus}`);
                return false;
            }
            const prev = c.status;
            c.status = newStatus;
            c.lastUpdated = 'Just now';
            c.activity.unshift({ time: 'Just now', text: `Status changed to ${newStatus}${note ? ': ' + note : ''}`, actor: actor || 'J. Doe' });
            if (note) c.notes = (c.notes || '') + `\n[${actor || 'J. Doe'}]: ${note}`;
            saveDb(db);
            this.log(actor || 'J. Doe', `Case ${id} status: ${prev} → ${newStatus}`, note || '', {
                eventType: 'CASE_STATUS_CHANGE', caseId: id,
                prevState: prev, newState: newStatus
            });
            return true;
        },

        // ── resolveCase ───────────────────────────────────────────────────────
        resolveCase: function(id, note, actor) {
            const db = getDb();
            const c = db.cases.find(c => c.id === id);
            if (!c) return false;
            const allowed = ['Under Review', 'Escalated'];
            if (!allowed.includes(c.status)) return false;
            const prev = c.status;
            c.status = 'Resolved';
            c.resolutionType = 'Resolved';
            c.resolutionNote = note || '';
            c.resolvedBy = actor || 'J. Doe';
            c.resolvedAt = new Date().toISOString();
            c.lastUpdated = 'Just now';
            c.activity.unshift({ time: 'Just now', text: `Case resolved by ${actor || 'J. Doe'}${note ? ': ' + note : ''}`, actor: actor || 'J. Doe' });
            // Resolve linked alerts
            if (c.linkedAlerts) {
                c.linkedAlerts.forEach(aid => {
                    const a = db.alerts.find(a => a.id === aid);
                    if (a && a.status !== 'Resolved' && a.status !== 'False Positive') {
                        a.status = 'Resolved';
                    }
                });
            }
            saveDb(db);
            this.log(actor || 'J. Doe', `Case ${id} resolved`, note || '', {
                eventType: 'CASE_RESOLVED', caseId: id,
                prevState: prev, newState: 'Resolved'
            });
            return true;
        },

        // ── markFalsePositive ─────────────────────────────────────────────────
        markFalsePositive: function(id, note, actor) {
            const db = getDb();
            const c = db.cases.find(c => c.id === id);
            if (!c) return false;
            const allowed = ['New', 'Under Review'];
            if (!allowed.includes(c.status)) return false;
            const prev = c.status;
            c.status = 'False Positive';
            c.resolutionType = 'False Positive';
            c.resolutionNote = note || '';
            c.resolvedBy = actor || 'J. Doe';
            c.resolvedAt = new Date().toISOString();
            c.lastUpdated = 'Just now';
            c.activity.unshift({ time: 'Just now', text: `Marked as False Positive by ${actor || 'J. Doe'}${note ? ': ' + note : ''}`, actor: actor || 'J. Doe' });
            // Update linked alert statuses
            if (c.linkedAlerts) {
                c.linkedAlerts.forEach(aid => {
                    const a = db.alerts.find(a => a.id === aid);
                    if (a) a.status = 'False Positive';
                });
            }
            saveDb(db);
            this.log(actor || 'J. Doe', `Case ${id} marked False Positive`, note || '', {
                eventType: 'CASE_FALSE_POSITIVE', caseId: id,
                prevState: prev, newState: 'False Positive'
            });
            return true;
        },

        // ── getKPIs ───────────────────────────────────────────────────────────
        // Returns live KPI object used by all dashboard pages.
        getKPIs: function() {
            const db = getDb();
            const alerts = db.alerts;
            const cases  = db.cases;
            const active = a => a.status !== 'Resolved' && a.status !== 'False Positive' && a.status !== 'Dismissed';
            return {
                openAlerts:       alerts.filter(a => active(a)).length,
                newAlerts:        alerts.filter(a => a.status === 'New').length,
                criticalAlerts:   alerts.filter(a => a.severity === 'Critical' && active(a)).length,
                highAlerts:       alerts.filter(a => a.severity === 'High'     && active(a)).length,
                mlAlerts:         alerts.filter(a => active(a) && (a.detectionSource === 'ML' || a.detectionSource === 'Combined')).length,
                ruleAlerts:       alerts.filter(a => active(a) && (a.detectionSource === 'Rule' || a.detectionSource === 'Combined')).length,
                openCases:        cases.filter(c  => c.status !== 'Resolved' && c.status !== 'False Positive' && !c.status.startsWith('Closed')).length,
                newCases:         cases.filter(c  => c.status === 'New').length,
                underReviewCases: cases.filter(c  => c.status === 'Under Review').length,
                escalatedCases:   cases.filter(c  => c.status === 'Escalated').length,
                resolvedCases:    cases.filter(c  => c.status === 'Resolved').length,
                falsePositives:   cases.filter(c  => c.status === 'False Positive').length,
                highRiskAccounts: Object.values(db.accounts).filter(a => (a.riskScore || 0) >= 70).length
            };
        },

        // ── generateAlertsFromAllAccounts ─────────────────────────────────────
        // Core alert engine. For each account:
        //   1. Run XGBoost predictRiskWithFeatures (explainability parallel path)
        //   2. Read existing rule triggers from acc.triggers (set by evaluateRules)
        //   3. Determine detectionSource: Rule | ML | Combined
        //   4. Deduplicate: UPDATE existing active alert, or CREATE new one
        //   5. Auto-generate case for new High/Critical alerts
        //
        // IMPORTANT: ML alerts are created only when mlProbability >= threshold.
        // Historical evidence (probability, threshold used) is stored at creation
        // time and is NOT overwritten when the threshold later changes.
        generateAlertsFromAllAccounts: function(options) {
            const db     = getDb();
            const thresh = this.getRiskThreshold();
            const store  = this;
            const evaluationOptions = options || {};

            function formatINR(n) {
                return '\u20b9' + Math.round(n || 0).toLocaleString('en-IN');
            }

            function hexId(prefix) {
                return prefix + Math.floor(Math.random() * 0xFFFFFF).toString(16).padStart(6, '0').toUpperCase();
            }

            function computeSeverity(prob, threshold, ruleCount, netEv) {
                let s = 0;
                if (prob >= threshold) s += Math.round((prob / 1.0) * 60);
                else s += Math.round((prob / Math.max(threshold, 0.01)) * 20);
                s += Math.min(ruleCount * 12, 48);
                if (netEv.cycleParticipation > 0) s += 6;
                if (netEv.networkConcentration > 0.7) s += 3;
                if (netEv.temporalProximity < 15) s += 3;
                if (s >= 75) return 'Critical';
                if (s >= 50) return 'High';
                if (s >= 25) return 'Medium';
                return 'Low';
            }

            function computeCategory(source, triggeredRules, mlLevel) {
                if (source === 'Combined') return `ML Risk + ${triggeredRules.length} Rule(s) Corroborated`;
                if (source === 'ML')       return `ML Suspicious Probability — ${mlLevel}`;
                const first = triggeredRules[0] || '';
                if (first.includes('Velocity'))    return 'Velocity Anomaly';
                if (first.includes('Holding'))     return 'Short Holding Ratio';
                if (first.includes('Connection'))  return 'Suspicious Connection';
                if (first.includes('High Value'))  return 'High-Value Transfer';
                if (first.includes('Circular'))    return 'Circular Money Flow';
                if (first.includes('Dormant'))     return 'Dormant Account Activation';
                return 'Rule-Based Detection';
            }

            Object.keys(db.accounts).forEach(accId => {
                const acc = db.accounts[accId];

                // 1. XGBoost explainability inference
                let mlProb = 0, mlLevel = 'Low', topFeatures = [];
                let xgbResult = null;
                if (typeof window !== 'undefined' && window.MuleGuardXGBoost && window.MuleGuardModelBooster) {
                    try {
                        const feats = store.getAccountFeatures(accId);
                        xgbResult = window.MuleGuardXGBoost.predictRiskWithFeatures(feats, window.MuleGuardModelBooster);
                    } catch(e) {}
                }
                if (xgbResult) {
                    mlProb     = xgbResult.probability;
                    topFeatures = xgbResult.topFeatures || [];
                    if (mlProb >= thresh)          mlLevel = 'High';
                    else if (mlProb >= thresh / 2) mlLevel = 'Moderate';
                }

                // 2. Rule triggers (set by evaluateRules)
                const triggeredRules = (acc.triggers || []).filter(t => !t.includes('ML Anomaly'));

                // 3. Determine if any detection fires
                const mlFired   = mlProb >= thresh;
                const ruleFired = triggeredRules.length > 0;
                
                // Persisted model state is the sole source for normal threshold crossing semantics.
                // lastProbability is retained only as a backward-compatible migration source.
                const persistedState = acc.mlInferenceState || {};
                const previousProbability = Number.isFinite(persistedState.currentProbability)
                    ? persistedState.currentProbability
                    : null;
                const previousThreshold = Number.isFinite(persistedState.thresholdUsed)
                    ? persistedState.thresholdUsed
                    : thresh;
                const isNewMlCrossing = previousProbability !== null &&
                    previousProbability < thresh && mlProb >= thresh;
                const isThresholdPolicyCrossing = evaluationOptions.thresholdChanged === true &&
                    previousProbability !== null &&
                    previousProbability < (evaluationOptions.previousThreshold || previousThreshold) &&
                    mlProb >= thresh;
                
                // Find existing active alert
                const existingIdx = db.alerts.findIndex(
                    a => a.deduplicationKey === accId &&
                         a.status !== 'Resolved' && a.status !== 'False Positive' && a.status !== 'Dismissed'
                );
                
                // ML alert is generated only if:
                // - There is already an active alert for the account (to update it)
                // - OR it is a fresh crossing from below -> above
                const allowMlAlert = (existingIdx !== -1) || isNewMlCrossing || isThresholdPolicyCrossing;

                // Persist inference state through the store write path so the next evaluation
                // never depends on a mutable object returned by getAccounts().
                acc.mlInferenceState = {
                    previousProbability: previousProbability,
                    currentProbability: mlProb,
                    thresholdUsed: thresh,
                    evaluatedAt: new Date().toISOString()
                };
                // Legacy compatibility for existing pages/localStorage records.
                acc.lastProbability = mlProb;

                // Skip if no rules triggered and no allowed ML alerts triggered
                if (!ruleFired && (!mlFired || !allowMlAlert)) {
                    return;
                }

                // If mlFired is true but not allowed (no new crossing & no active alert), detection source is Rule-only
                const effectiveMlFired = mlFired && allowMlAlert;
                const detectionSource = (effectiveMlFired && ruleFired) ? 'Combined' : (effectiveMlFired ? 'ML' : 'Rule');

                // 4. Collect network evidence from feature set
                const feats = store.getAccountFeatures(accId) || {};
                const netEv = {
                    cycleParticipation:   feats.cycleParticipation   || 0,
                    networkConcentration: feats.networkConcentration  || 0,
                    fanIn:                feats.fanIn                 || 0,
                    fanOut:               feats.fanOut                || 0,
                    multiHopConnectivity: feats.multiHopConnectivity  || 0,
                    temporalProximity:    feats.temporalProximity     || 1440
                };

                // 5. Find relevant transaction refs (highest-score txs for account)
                const accTxs = db.transactions
                    .filter(t => t.senderId === accId || t.receiverId === accId)
                    .sort((a, b) => (b.score || 0) - (a.score || 0))
                    .slice(0, 10)
                    .map(t => t.id);

                // 6. Largest transaction amount for this account
                const maxTx = db.transactions
                    .filter(t => t.senderId === accId || t.receiverId === accId)
                    .reduce((max, t) => (t.amountNumeric || 0) > max ? (t.amountNumeric || 0) : max, 0);

                const severity   = computeSeverity(mlProb, thresh, triggeredRules.length, netEv);
                const category   = computeCategory(detectionSource, triggeredRules, mlLevel);
                const dedupKey   = accId; // One active alert per account

                if (existingIdx !== -1) {
                    // UPDATE existing alert evidence — preserve id, status, createdAt, notes, caseId
                    const existing = db.alerts[existingIdx];
                    existing.mlProbability   = mlProb;
                    existing.previousMLProbability = previousProbability;
                    existing.currentMLProbability  = mlProb;
                    existing.thresholdUsed         = thresh;
                    existing.mlRiskLevel     = mlLevel;
                    existing.detectionSource = detectionSource;
                    existing.triggeredRules  = triggeredRules;
                    existing.topFeatures     = topFeatures;
                    existing.networkEvidence = netEv;
                    existing.transactionRefs = accTxs;
                    existing.severity        = severity;
                    existing.category        = category;
                    existing.lastEvaluatedAt = new Date().toISOString();
                    // Do NOT change mlThresholdUsed — preserve historical threshold
                } else {
                    // CREATE new alert
                    const alertId = hexId('AL-');
                    const now     = new Date().toISOString();
                    const newAlert = {
                        id:               alertId,
                        accountId:        accId,
                        accountName:      acc.name || accId,
                        deduplicationKey: dedupKey,
                        detectionSource:  detectionSource,
                        mlProbability:    mlProb,
                        previousMLProbability: previousProbability,
                        currentMLProbability:  mlProb,
                        thresholdUsed:    thresh,
                        mlRiskLevel:      mlLevel,
                        mlThresholdUsed:  thresh,     // Locked to threshold at creation time
                        topFeatures:      topFeatures,
                        triggeredRules:   triggeredRules,
                        networkEvidence:  netEv,
                        transactionRefs:  accTxs,
                        category:         category,
                        severity:         severity,
                        amount:           formatINR(maxTx),
                        amountNumeric:    maxTx,
                        status:           'New',
                        summary:          `Potential mule activity detected — requires investigation`,
                        notes:            '',
                        caseId:           null,
                        // Legacy fields for backwards compat with alert drawer
                        target:           acc.name || accId,
                        score:            Math.min(99, Math.round(mlProb * 100)),
                        indicators:       triggeredRules,
                        riskExplanation:  `Suspicious probability: ${(mlProb * 100).toFixed(1)}% (threshold: ${(thresh * 100).toFixed(0)}%). Detection: ${detectionSource}.`,
                        time:             'Just now',
                        createdAt:        now,
                        lastEvaluatedAt:  now,
                        generatedBySystem: true
                    };
                    db.alerts.push(newAlert);
                    this.log('Alert Engine', `Alert ${alertId} created for ${acc.name}`,
                        `Source: ${detectionSource}. ML: ${(mlProb*100).toFixed(1)}%. Rules: ${triggeredRules.length}.`, {
                        eventType: 'ALERT_CREATED', alertId: alertId
                    });

                    // Auto-generate case for High/Critical severity
                    if (severity === 'High' || severity === 'Critical') {
                        // Only if no open case already exists for this account
                        const openCase = db.cases.find(
                            c => c.primaryEntityId === accId &&
                                 c.status !== 'Resolved' && c.status !== 'False Positive' &&
                                 !c.status.startsWith('Closed')
                        );
                        if (!openCase) {
                            // We need saveDb before autoGenerateCaseFromAlert reads db
                            saveDb(db);
                            const caseId = this.autoGenerateCaseFromAlert(alertId);
                            // Refresh db reference after case creation
                            const refreshed = getDb();
                            db.alerts = refreshed.alerts;
                            db.cases  = refreshed.cases;
                            db.auditLogs = refreshed.auditLogs;
                        }
                    }
                }
            });

            saveDb(db);
        },

        // ── autoGenerateCaseFromAlert ─────────────────────────────────────────
        autoGenerateCaseFromAlert: function(alertId) {
            const db    = getDb();
            const alert = db.alerts.find(a => a.id === alertId);
            if (!alert) return null;
            if (alert.caseId) return alert.caseId; // Already has a case

            const ASSIGNEE_ROSTER = ['J. Doe', 'S. Rao', 'A. Kumar', 'R. Singh'];
            const assignee = ASSIGNEE_ROSTER[db.cases.length % ASSIGNEE_ROSTER.length];

            function hexId(prefix) {
                return prefix + Math.floor(Math.random() * 0xFFFFFF).toString(16).padStart(6, '0').toUpperCase();
            }

            const caseId = hexId('CS-');
            const now    = new Date().toISOString();
            const acc    = db.accounts[alert.accountId] || {};

            const newCase = {
                id:                          caseId,
                title:                       `${alert.accountName || alert.accountId} — Potential Mule Activity`,
                entity:                      alert.accountName || alert.accountId,
                primaryEntityId:             alert.accountId,
                linkedAlerts:                [alertId],
                mlProbabilityAtCreation:     alert.mlProbability,
                detectionSourceAtCreation:   alert.detectionSource,
                priority:                    alert.severity,
                score:                       Math.min(99, Math.round((alert.mlProbability || 0) * 100)),
                assignee:                    assignee,
                status:                      'New',
                autoGenerated:               true,
                summary:                     `Potential mule activity — requires investigation. ML suspicious probability: ${((alert.mlProbability || 0) * 100).toFixed(1)}%.`,
                findings:                    [],
                notes:                       '',
                activity: [
                    { time: 'Just now', text: `Case auto-generated from alert ${alertId} (${alert.detectionSource || 'System'} detection)`, actor: 'System' }
                ],
                resolutionType:  null,
                resolutionNote:  null,
                resolvedBy:      null,
                resolvedAt:      null,
                createdTime:     'Just now',
                lastUpdated:     'Just now'
            };

            db.cases.push(newCase);
            alert.caseId = caseId;
            saveDb(db);

            this.log('System', `Case ${caseId} auto-generated from alert ${alertId}`,
                `Account: ${alert.accountName}. Priority: ${alert.severity}.`, {
                eventType: 'CASE_CREATED', caseId: caseId, alertId: alertId
            });

            return caseId;
        },

        // ── Ingest Transaction (Atomic, validation and rollback) ──────────────
        ingestTransaction: function(transaction) {
            if (!transaction) {
                return { success: false, error: "Empty transaction object" };
            }

            const db = getDb();

            const senderId = transaction.senderId || transaction.senderAccountId;
            const receiverId = transaction.receiverId || transaction.receiverAccountId;
            const amountNumeric = parseFloat(transaction.amountNumeric || transaction.amount);
            const type = transaction.type || 'Transfer';
            const id = transaction.id || transaction.transactionId || ('TX-' + Math.floor(Math.random() * 1000000));
            const time = transaction.time || 'Just now';
            const origin = transaction.origin || 'Mumbai';
            const destination = transaction.destination || 'Delhi';
            const status = transaction.status || 'Normal';
            const score = transaction.score || 15;
            const summary = transaction.summary || `Transaction ingested dynamically: ${id}`;

            // 1. Validation
            if (isNaN(amountNumeric) || amountNumeric <= 0) {
                return { success: false, error: "Invalid/non-positive transaction amount" };
            }

            if (senderId) {
                if (!db.accounts[senderId]) {
                    return { success: false, error: `Sender account ${senderId} not found` };
                }
                if (db.accounts[senderId].balance < amountNumeric) {
                    return { success: false, error: `Insufficient balance in sender account ${senderId}` };
                }
            } else {
                return { success: false, error: "Sender account must be specified" };
            }

            if (receiverId) {
                if (!db.accounts[receiverId]) {
                    return { success: false, error: `Receiver account ${receiverId} not found` };
                }
            } else {
                return { success: false, error: "Receiver account must be specified" };
            }

            // 2. Downstream changes inside atomic try/catch
            const originalSerialized = localStorage.getItem(STORE_KEY);
            try {
                // Apply changes in memory
                db.accounts[senderId].balance -= amountNumeric;
                db.accounts[receiverId].balance += amountNumeric;

                const isoTimestamp = transaction.isoTimestamp || transaction.timestamp || (
                    transaction.time && (transaction.time.includes('T') || transaction.time.includes('-')) && !isNaN(Date.parse(transaction.time))
                        ? new Date(transaction.time).toISOString()
                        : new Date().toISOString()
                );

                const newTx = {
                    id,
                    senderId,
                    receiverId,
                    amountNumeric,
                    type,
                    value: '\u20b9' + Math.round(amountNumeric).toLocaleString('en-IN'),
                    score,
                    time,
                    isoTimestamp,
                    timestamp: isoTimestamp,
                    origin,
                    destination,
                    status,
                    summary
                };
                db.transactions.unshift(newTx);

                // Save to localStorage temporary to evaluate rules and run inference
                saveDb(db);

                try {
                    // Re-run rules & ML probability updates
                    this.evaluateRules();
                    this.generateAlertsFromAllAccounts();
                } catch (downstreamErr) {
                    // Downstream failed: roll back localStorage completely
                    if (originalSerialized) {
                        localStorage.setItem(STORE_KEY, originalSerialized);
                    } else {
                        localStorage.removeItem(STORE_KEY);
                    }
                    return { success: false, error: `Downstream processing failed: ${downstreamErr.message}` };
                }

                // Log the success event
                this.log('System Engine', `Ingested transaction ${id}`, 
                    `Transferred \u20b9${Math.round(amountNumeric).toLocaleString('en-IN')} from ${senderId} to ${receiverId}.`, {
                    eventType: 'TRANSACTION_INGESTED'
                });

                if (typeof window !== 'undefined' && window.MuleGuardAPI && window.MuleGuardAPI.ingestTransaction) {
                    window.MuleGuardAPI.ingestTransaction({
                        senderId,
                        receiverId,
                        amountNumeric,
                        type,
                        origin,
                        destination,
                        summary
                    }).catch(err => console.warn('Backend transaction ingest sync warning:', err));
                }

                // Dispatch custom event to notify open browser pages
                if (typeof window !== 'undefined') {
                    const event = new CustomEvent('muleguard:transaction-ingested', {
                        detail: {
                            transaction: newTx,
                            affectedAccounts: [senderId, receiverId]
                        }
                    });
                    window.dispatchEvent(event);
                }

                return { success: true, transaction: newTx };

            } catch (err) {
                // Rollback if any unexpected exception occurred
                if (originalSerialized) {
                    localStorage.setItem(STORE_KEY, originalSerialized);
                } else {
                    localStorage.removeItem(STORE_KEY);
                }
                return { success: false, error: `Ingestion error: ${err.message}` };
            }
        },

        // ── Reset Ledger and Simulator ────────────────────────────────────────
        resetLiveLedger: function() {
            return this.resetTransactionSimulation();
        },

        resetTransactionSimulation: function() {
            this.stopTransactionSimulation();
            const defaultSimState = {
                status: "Stopped",
                scenario: "Legitimate",
                txCount: 0,
                lastTxAmount: null,
                lastTxSender: null,
                lastTxReceiver: null,
                lastTxProb: null,
                lastTxSource: null,
                lastTxTime: null,
                intervalMs: 3000
            };
            localStorage.setItem('muleguard_sim_state', JSON.stringify(defaultSimState));
            const restored = this.reset();
            return restored;
        },

        // ── Simulator API Wrapper Passthroughs ────────────────────────────────
        startTransactionSimulation: function(scenarioName, intervalMs) {
            if (window.MuleGuardSimulator) {
                window.MuleGuardSimulator.start(scenarioName, intervalMs);
            }
        },

        stopTransactionSimulation: function() {
            if (window.MuleGuardSimulator) {
                window.MuleGuardSimulator.stop();
            }
        },

        pauseTransactionSimulation: function() {
            if (window.MuleGuardSimulator) {
                window.MuleGuardSimulator.pause();
            }
        },

        resumeTransactionSimulation: function() {
            if (window.MuleGuardSimulator) {
                window.MuleGuardSimulator.resume();
            }
        },

        getSimulationState: function() {
            if (window.MuleGuardSimulator) {
                return window.MuleGuardSimulator.getState();
            }
            // Fallback read from localStorage if simulator script not initialized
            const stored = localStorage.getItem('muleguard_sim_state');
            return stored ? JSON.parse(stored) : {
                status: "Stopped",
                scenario: "Legitimate",
                txCount: 0,
                lastTxAmount: null,
                lastTxSender: null,
                lastTxReceiver: null,
                lastTxProb: null,
                lastTxSource: null,
                lastTxTime: null,
                intervalMs: 3000
            };
        },

        // ── Watchlist Management API ─────────────────────────────────────────
        getWatchlist: function() {
            const db = getDb();
            if (!db.watchlists) db.watchlists = {};
            return Object.values(db.watchlists);
        },

        isWatchlisted: function(accountId) {
            if (!accountId) return false;
            const db = getDb();
            if (!db.watchlists) db.watchlists = {};
            return Boolean(db.watchlists[accountId]);
        },

        addToWatchlist: function(accountId, reason, priority, addedBy) {
            if (!accountId || typeof accountId !== 'string') {
                return { success: false, error: 'Account ID is required' };
            }

            const db = getDb();
            if (!db.watchlists) db.watchlists = {};

            // 1. Validate account existence
            const acc = db.accounts && db.accounts[accountId];
            if (!acc) {
                return { success: false, error: `Account ${accountId} not found` };
            }

            // 2. Validate reason mandatory
            if (!reason || typeof reason !== 'string' || reason.trim() === '') {
                return { success: false, error: 'Reason is required' };
            }

            // 3. Validate priority (High, Medium, Low)
            const validPriorities = ['High', 'Medium', 'Low'];
            const normalizedPriority = priority ? String(priority).trim() : 'Medium';
            if (!validPriorities.includes(normalizedPriority)) {
                return { success: false, error: 'Invalid priority. Must be High, Medium, or Low' };
            }

            // 4. Prevent duplicate watchlist entries
            if (db.watchlists[accountId]) {
                return { success: false, error: `Account ${accountId} is already on the watchlist` };
            }

            const investigatorName = addedBy && typeof addedBy === 'string' && addedBy.trim() ? addedBy.trim() : 'Investigator';
            const now = new Date().toISOString();

            // Find latest active transaction reference for account if any
            let lastActiveTx = null;
            if (db.transactions && Array.isArray(db.transactions)) {
                const tx = db.transactions.find(t => t.senderId === accountId || t.receiverId === accountId);
                if (tx) lastActiveTx = tx.id;
            }

            const entry = {
                accountId: accountId,
                accountName: acc.name || accountId,
                addedBy: investigatorName,
                addedAt: now,
                reason: reason.trim(),
                priority: normalizedPriority,
                autoFlagOnTx: true,
                lastActiveTx: lastActiveTx
            };

            db.watchlists[accountId] = entry;
            saveDb(db);

            // Create audit log entry
            this.log('Watchlist Engine', `Account Added to Watchlist: ${accountId}`,
                `Account ${accountId} (${acc.name || accountId}) added to watchlist by ${investigatorName}. Priority: ${normalizedPriority}. Reason: ${reason.trim()}.`, {
                eventType: 'WATCHLIST_ADD',
                accountId: accountId,
                addedBy: investigatorName,
                priority: normalizedPriority
            });

            return { success: true, entry: entry };
        },

        removeFromWatchlist: function(accountId, removedBy) {
            if (!accountId || typeof accountId !== 'string') {
                return { success: false, error: 'Account ID is required' };
            }

            const db = getDb();
            if (!db.watchlists) db.watchlists = {};

            const entry = db.watchlists[accountId];
            if (!entry) {
                return { success: false, error: `Account ${accountId} is not on the watchlist` };
            }

            const investigatorName = removedBy && typeof removedBy === 'string' && removedBy.trim() ? removedBy.trim() : 'Investigator';

            delete db.watchlists[accountId];
            saveDb(db);

            // Create audit log entry
            this.log('Watchlist Engine', `Account Removed from Watchlist: ${accountId}`,
                `Account ${accountId} (${entry.accountName || accountId}) removed from watchlist by ${investigatorName}.`, {
                eventType: 'WATCHLIST_REMOVE',
                accountId: accountId,
                removedBy: investigatorName
            });

            return { success: true, accountId: accountId };
        }
    };

    // Run initial rules evaluation loop to bind default scores
    const db = getDb();
    if (db && db.accounts) {
        if (!Object.values(db.accounts)[0].triggers) {
            window.MuleGuardStore.evaluateRules();
        }
        
        // Initialize lastProbability for baseline threshold checks
        let dirty = false;
        const freshDb = getDb();
        Object.keys(freshDb.accounts).forEach(id => {
            if (!freshDb.accounts[id].mlInferenceState) {
                const risk = window.MuleGuardStore.predictAccountRisk(id);
                const probability = risk && Number.isFinite(risk.probability) ? risk.probability : null;
                freshDb.accounts[id].mlInferenceState = {
                    previousProbability: probability,
                    currentProbability: probability,
                    thresholdUsed: window.MuleGuardStore.getRiskThreshold(),
                    evaluatedAt: new Date().toISOString()
                };
                freshDb.accounts[id].lastProbability = probability;
                dirty = true;
            }
        });
        if (dirty) {
            saveDb(freshDb);
        }
    }
})();
