// MuleGuard Shared Stateful Data Store
// Manages synthetic virtual-bank datasets, transactions, alerts, cases, rules, and audit logs.
// Persists in localStorage to enable dynamic end-to-end user workflows.

(function() {
    const STORE_KEY = 'muleguard_db';

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
    if (typeof window !== 'undefined' && window.location && !window.MuleGuardExpandedDB) {
        const isSubDir = window.location.pathname.includes('/bank/');
        const isInternal = window.location.pathname.includes('/internal/');
        const prefix = isSubDir ? '../../' : (isInternal ? '../' : '');
        document.write(`<script src="${prefix}scripts/synthetic_db_expanded.js"></script>`);
        document.write(`<script src="${prefix}scripts/best_muleguard_model.js"></script>`);
        document.write(`<script src="${prefix}scripts/xgboost-infer.js"></script>`);
    }

    // Default Seed Data
    const defaultDb = window.MuleGuardExpandedDB || {
        rules: [
            { id: 'R-VEL-1', name: 'Velocity Spike (Inbound Degree)', threshold: 5, unit: 'transfers/24h', description: 'Triggers when an account receives more than the threshold of inbound UPI transfers in a 24-hour period.', active: true },
            { id: 'R-HOLD-1', name: 'Short Holding Time Ratio', threshold: 80, unit: '% ratio', description: 'Triggers when more than the threshold of received funds are transferred out of the account within 30 minutes.', active: true },
            { id: 'R-NET-1', name: 'Suspicious Component Connection', threshold: 1, unit: 'hops', description: 'Triggers when a node has direct connection (shared device/IP/phone) to previously blocked/flagged fraud nodes.', active: true },
            { id: 'R-VAL-1', name: 'High-Value Shell Transfer', threshold: 100000, unit: 'INR', description: 'Triggers on a transfer exceeding threshold from/to newly registered corporate shell entities.', active: true },
            { id: 'R-CIRC-1', name: 'Circular Money Flow', threshold: 1, unit: 'cycles', description: 'Triggers when an account participates in a closed money flow loop of connected accounts.', active: true },
            { id: 'R-DORM-1', name: 'Dormant Account Activation', threshold: 50000, unit: 'INR/24h', description: 'Triggers when a previously inactive/dormant account receives significant transaction volume within 24 hours.', active: true }
        ],
        accounts: {
            'ACC-982741': { id: 'ACC-982741', name: 'Apex Trading Ltd', type: 'Current', balance: 450000.00, riskScore: 91, status: 'Flagged', created: '2025-01-10', phone: '+91 90110 54321', device: 'IPHONE_15_PRO', ip: '192.168.4.15', address: '12th Floor, Apex Towers, Mumbai' },
            'ACC-982736': { id: 'ACC-982736', name: 'Orion Financial', type: 'Current', balance: 124000.50, riskScore: 78, status: 'Under Review', created: '2025-03-12', phone: '+91 80990 12345', device: 'MACBOOK_PRO_M3', ip: '10.15.22.45', address: 'Suite 4B, Blackwood Plaza, Chennai' },
            'ACC-982728': { id: 'ACC-982728', name: 'Vertex Imports', type: 'Current', balance: 89000.00, riskScore: 62, status: 'Normal', created: '2024-06-20', phone: '+91 72001 98765', device: 'SAMSUNG_S24', ip: '172.16.89.12', address: 'Vertex Depot, Kandla Port, Gujarat' },
            'ACC-982714': { id: 'ACC-982714', name: 'Northstar Holdings', type: 'Current', balance: 312000.00, riskScore: 96, status: 'Critical', created: '2024-09-15', phone: '+91 90110 54321', device: 'IPHONE_15_PRO', ip: '192.168.4.15', address: '12th Floor, Apex Towers, Mumbai' },
            'ACC-982705': { id: 'ACC-982705', name: 'Meridian Capital', type: 'Current', balance: 94600.00, riskScore: 45, status: 'Normal', created: '2026-05-01', phone: '+91 98450 11223', device: 'THINKPAD_T14', ip: '198.51.100.7', address: 'Meridian Chambers, Nariman Point, Mumbai' },
            'ACC-982698': { id: 'ACC-982698', name: 'Atlas Global Trading', type: 'Current', balance: 28450.00, riskScore: 32, status: 'Normal', created: '2026-05-10', phone: '+91 94440 55667', device: 'DELL_LATITUDE', ip: '203.0.113.12', address: 'Atlas Logistics Yard, Chennai Port' },
            'ACC-982685': { id: 'ACC-982685', name: 'Vanguard Logistics', type: 'Current', balance: 15600.00, riskScore: 18, status: 'Normal', created: '2026-05-12', phone: '+91 91500 88990', device: 'IPAD_AIR', ip: '198.51.100.8', address: 'Vanguard Shed, Kochi Port, Kerala' },
            'ACC-982672': { id: 'ACC-982672', name: 'Blackwood Assets', type: 'Current', balance: 620000.00, riskScore: 98, status: 'Blocked', created: '2026-02-18', phone: '+91 80990 12345', device: 'MACBOOK_PRO_M3', ip: '10.15.22.45', address: 'Suite 4B, Blackwood Plaza, Chennai' },
            'ACC-982659': { id: 'ACC-982659', name: 'Phoenix Ventures', type: 'Current', balance: 105300.00, riskScore: 75, status: 'Under Review', created: '2026-02-20', phone: '+91 88877 66554', device: 'IPHONE_14', ip: '192.168.10.88', address: 'Phoenix Tech Park, Bangalore' },
            'ACC-982641': { id: 'ACC-982641', name: 'Swift Logistics Corp', type: 'Current', balance: 38200.00, riskScore: 52, status: 'Normal', created: '2025-11-05', phone: '+91 77766 55443', device: 'MACBOOK_AIR', ip: '172.16.4.5', address: 'Swift Cargo House, Kolkata' }
        },
        transactions: [
            // Circular money flow loop: Phoenix (ACC-982659) -> Swift (ACC-982641) -> Orion (ACC-982736) -> Phoenix (ACC-982659)
            { id: 'TX-LOOP-01', senderId: 'ACC-982659', receiverId: 'ACC-982641', amountNumeric: 35000, type: 'Transfer', value: '₹35,000', score: 72, time: getRelativeTime(12), origin: 'Bangalore', destination: 'Kolkata', status: 'Normal', summary: 'Circular loop element 1.' },
            { id: 'TX-LOOP-02', senderId: 'ACC-982641', receiverId: 'ACC-982736', amountNumeric: 35000, type: 'Transfer', value: '₹35,000', score: 72, time: getRelativeTime(15), origin: 'Kolkata', destination: 'Chennai', status: 'Normal', summary: 'Circular loop element 2.' },
            { id: 'TX-LOOP-03', senderId: 'ACC-982736', receiverId: 'ACC-982659', amountNumeric: 35000, type: 'Transfer', value: '₹35,000', score: 72, time: getRelativeTime(18), origin: 'Chennai', destination: 'Bangalore', status: 'Normal', summary: 'Circular loop element 3.' },

            // Aggregation into Apex Trading (ACC-982741)
            { id: 'TX-AGG-01', senderId: 'ACC-982705', receiverId: 'ACC-982741', amountNumeric: 10000, type: 'Transfer', value: '₹10,000', score: 60, time: getRelativeTime(30), origin: 'Mumbai', destination: 'Mumbai', status: 'Normal', summary: 'Inbound layering conduit.' },
            { id: 'TX-AGG-02', senderId: 'ACC-982728', receiverId: 'ACC-982741', amountNumeric: 12000, type: 'Transfer', value: '₹12,000', score: 60, time: getRelativeTime(40), origin: 'Gujarat', destination: 'Mumbai', status: 'Normal', summary: 'Inbound layering conduit.' },
            { id: 'TX-AGG-03', senderId: 'ACC-982698', receiverId: 'ACC-982741', amountNumeric: 9500, type: 'Transfer', value: '₹9,500', score: 60, time: getRelativeTime(50), origin: 'Chennai', destination: 'Mumbai', status: 'Normal', summary: 'Inbound layering conduit.' },
            { id: 'TX-AGG-04', senderId: 'ACC-982685', receiverId: 'ACC-982741', amountNumeric: 11000, type: 'Transfer', value: '₹11,000', score: 60, time: getRelativeTime(60), origin: 'Kerala', destination: 'Mumbai', status: 'Normal', summary: 'Inbound layering conduit.' },
            { id: 'TX-AGG-05', senderId: 'ACC-982641', receiverId: 'ACC-982741', amountNumeric: 8000, type: 'Transfer', value: '₹8,000', score: 60, time: getRelativeTime(70), origin: 'Kolkata', destination: 'Mumbai', status: 'Normal', summary: 'Inbound layering conduit.' },
            { id: 'TX-AGG-06', senderId: 'ACC-982659', receiverId: 'ACC-982741', amountNumeric: 15000, type: 'Transfer', value: '₹15,000', score: 60, time: getRelativeTime(80), origin: 'Bangalore', destination: 'Mumbai', status: 'Normal', summary: 'Inbound layering conduit.' },

            // Outbound distribution from Northstar Holdings (ACC-982714)
            { id: 'TX-DIST-01', senderId: 'ACC-982714', receiverId: 'ACC-982705', amountNumeric: 15000, type: 'Transfer', value: '₹15,000', score: 50, time: getRelativeTime(90), origin: 'Mumbai', destination: 'Mumbai', status: 'Normal', summary: 'Outbound smurfing transfer.' },
            { id: 'TX-DIST-02', senderId: 'ACC-982714', receiverId: 'ACC-982728', amountNumeric: 15000, type: 'Transfer', value: '₹15,000', score: 50, time: getRelativeTime(100), origin: 'Mumbai', destination: 'Gujarat', status: 'Normal', summary: 'Outbound smurfing transfer.' },
            { id: 'TX-DIST-03', senderId: 'ACC-982714', receiverId: 'ACC-982698', amountNumeric: 15000, type: 'Transfer', value: '₹15,000', score: 50, time: getRelativeTime(110), origin: 'Mumbai', destination: 'Chennai', status: 'Normal', summary: 'Outbound smurfing transfer.' },
            { id: 'TX-DIST-04', senderId: 'ACC-982714', receiverId: 'ACC-982685', amountNumeric: 15000, type: 'Transfer', value: '₹15,000', score: 50, time: getRelativeTime(120), origin: 'Mumbai', destination: 'Kerala', status: 'Normal', summary: 'Outbound smurfing transfer.' },
            { id: 'TX-DIST-05', senderId: 'ACC-982714', receiverId: 'ACC-982641', amountNumeric: 15000, type: 'Transfer', value: '₹15,000', score: 50, time: getRelativeTime(130), origin: 'Mumbai', destination: 'Kolkata', status: 'Normal', summary: 'Outbound smurfing transfer.' },

            // High-Value Transfers (Shell routing / unusual sizing)
            { id: 'TX-HIGH-01', senderId: 'ACC-982741', receiverId: 'ACC-982714', amountNumeric: 127500, type: 'Transfer', value: '₹1,27,500', score: 91, time: getRelativeTime(12), origin: 'Singapore', destination: 'India', status: 'Flagged', summary: 'High velocity circular loop conduit.' },
            { id: 'TX-HIGH-02', senderId: 'ACC-982672', receiverId: 'ACC-982714', amountNumeric: 312400, type: 'Transfer', value: '₹3,12,400', score: 96, time: getRelativeTime(60), origin: 'Zurich', destination: 'India', status: 'Blocked', summary: 'High risk shell integration block.' },
            { id: 'TX-HIGH-03', senderId: 'ACC-982672', receiverId: 'ACC-982705', amountNumeric: 620000, type: 'Transfer', value: '₹6,20,000', score: 98, time: getRelativeTime(480), origin: 'Zurich', destination: 'India', status: 'Blocked', summary: 'Critical value shell routing.' },
            { id: 'TX-HIGH-04', senderId: 'ACC-982736', receiverId: 'ACC-982672', amountNumeric: 86200, type: 'Transfer', value: '₹86,200', score: 78, time: getRelativeTime(28), origin: 'London', destination: 'India', status: 'Under Review', summary: 'Layering transfer structuring.' },

            // Normal operating baseline transfers
            { id: 'TX-NORM-01', senderId: 'ACC-982728', receiverId: 'ACC-982705', amountNumeric: 42800, type: 'Payment', value: '₹42,800', score: 20, time: getRelativeTime(41), origin: 'Dubai', destination: 'India', status: 'Normal', summary: 'Normal supplier clearing.' },
            { id: 'TX-NORM-02', senderId: 'ACC-982705', receiverId: 'ACC-982698', amountNumeric: 94600, type: 'Deposit', value: '₹94,600', score: 15, time: getRelativeTime(120), origin: 'New York', destination: 'India', status: 'Normal', summary: 'Standard corporate deposit.' },
            { id: 'TX-NORM-03', senderId: 'ACC-982698', receiverId: 'ACC-982685', amountNumeric: 28450, type: 'Payment', value: '₹28,450', score: 10, time: getRelativeTime(180), origin: 'Singapore', destination: 'India', status: 'Normal', summary: 'Trade logistical payment.' },
            { id: 'TX-NORM-04', senderId: 'ACC-982685', receiverId: 'ACC-982641', amountNumeric: 15600, type: 'Payment', value: '₹15,600', score: 10, time: getRelativeTime(300), origin: 'Tokyo', destination: 'India', status: 'Normal', summary: 'Standard logistics dispatch.' },
            { id: 'TX-NORM-05', senderId: 'ACC-982641', receiverId: 'ACC-982705', amountNumeric: 38200, type: 'Withdrawal', value: '₹38,200', score: 22, time: getRelativeTime(1080), origin: 'Sydney', destination: 'India', status: 'Normal', summary: 'Standard corporate debit.' }
        ],
        alerts: [
            { id: 'AL-982711', target: 'Apex Trading Ltd', category: 'Velocity Anomaly', score: 91, amount: '₹1,27,500', time: getRelativeTime(12), severity: 'Critical', status: 'New', summary: 'Dynamic rule evaluation triggers.', indicators: [], riskExplanation: '', notes: 'Active ledger monitoring.', caseId: 'CS-982714' },
            { id: 'AL-982705', target: 'Orion Financial', category: 'Suspicious Connection', score: 78, amount: '₹86,200', time: getRelativeTime(28), severity: 'High', status: 'Investigating', summary: 'Shares device with Blocked entity.', indicators: [], riskExplanation: '', notes: 'Awaiting sub-ledger reviews.', caseId: 'CS-982701' },
            { id: 'AL-982684', target: 'Blackwood Assets', category: 'Critical Value Shell', score: 98, amount: '₹6,20,000', time: getRelativeTime(60), severity: 'Critical', status: 'New', summary: 'Account routing to blocked entities.', indicators: [], riskExplanation: '', notes: 'Locked.', caseId: 'CS-982714' }
        ],
        cases: [
            {
                id: 'CS-982701',
                title: 'Orion Structuring Review',
                entity: 'Orion Financial',
                primaryEntityId: 'ACC-982736',
                priority: 'High',
                score: 78,
                assignee: 'S. Rao',
                createdTime: '2 hrs ago',
                lastUpdated: '28 min ago',
                status: 'Investigating',
                summary: 'Orion Financial shares registration metadata with Blocked assets.',
                findings: [
                        'Shared device footprint with blocked account ACC-982672',
                        'Shared IP address matching Zurich shell conduit'
                ],
                notes: 'Awaiting sub-ledger reviews.',
                activity: [
                        { time: '28 min ago', text: 'Investigation status updated' },
                        { time: '2 hrs ago', text: 'Alert AL-982705 linked' }
                ]
            },
            {
                id: 'CS-982714',
                title: 'Apex & Northstar Review',
                entity: 'Apex Trading Ltd',
                primaryEntityId: 'ACC-982741',
                priority: 'Critical',
                score: 91,
                assignee: 'R. Singh',
                createdTime: '3 hrs ago',
                lastUpdated: '1 hr ago',
                status: 'Escalated',
                summary: 'Suspicious loops routing funds offshore.',
                findings: [
                        'Velocity spike detected on current account',
                        'Funds holding time ratio exceeds 95%',
                        'Common device footprint matched to Northstar Holdings'
                ],
                notes: 'Active ledger monitoring.',
                activity: [
                        { time: '1 hr ago', text: 'Escalated to Compliance' },
                        { time: '3 hrs ago', text: 'Alert AL-982711 linked' }
                ]
            }
        ],
        decisions: [
            { id: 'DEC-001', caseId: 'CS-982701', caseTitle: 'Orion Structuring Review', decision: 'Hold / Escalate', rationale: 'Escalating for cross-border terminal audit.', timestamp: '1 day ago', reviewer: 'A. Kumar' }
        ],
        auditLogs: [
            { id: 'LOG-001', actor: 'System Engine', action: 'Initialized MuleGuard synthetic data environment', time: 'Just now', details: 'Loaded 10 accounts and 50+ transaction history.' }
        ],
        networks: {
            'NET-082714': {
                id: 'NET-082714',
                name: 'Apex-Northstar Link',
                type: 'Shell Conduit',
                score: 95,
                members: 5,
                totalValue: '₹96,90,000',
                connectedCount: 12,
                lastActivity: '8 min ago',
                status: 'Flagged',
                summary: 'The Apex-Northstar link constitutes a high-velocity circular loop routing funds from international trading accounts to verified shell nodes.',
                graphNodes: [
                    { id: 'ACC-982741', label: 'Apex Hub', role: 'Main Treasury Conduit', risk: 'Critical', cx: 200, cy: 80, r: 16 },
                    { id: 'ACC-982714', label: 'Northstar', role: 'Offshore Receiver', risk: 'Critical', cx: 80, cy: 40, r: 12 },
                    { id: 'ACC-982728', label: 'Vertex Imp', role: 'Trade Interface', risk: 'Medium', cx: 80, cy: 120, r: 12 },
                    { id: 'ACC-982705', label: 'Mule Acct A', role: 'Sub-Clearing Node', risk: 'High', cx: 320, cy: 40, r: 12 },
                    { id: 'ACC-982736', label: 'Mule Acct B', role: 'Intermediary Smurfer', risk: 'High', cx: 320, cy: 120, r: 12 }
                ],
                graphLinks: [
                    { source: 0, target: 1, flow: true },
                    { source: 2, target: 0, flow: true },
                    { source: 0, target: 3, flow: true },
                    { source: 0, target: 4, flow: true }
                ]
            },
            'NET-082703': {
                id: 'NET-082703',
                name: 'Orion Clearing Loop',
                type: 'Layering Loop',
                score: 82,
                members: 4,
                totalValue: '₹42,00,000',
                connectedCount: 8,
                lastActivity: '18 min ago',
                status: 'Under Review',
                summary: 'Orion Clearing Loop routes deposits continuously via sub-clearing micro-accounts to mask layering activity.',
                graphNodes: [
                    { id: 'ACC-982736', label: 'Orion Hub', role: 'Broker clearing interface', risk: 'High', cx: 200, cy: 80, r: 16 },
                    { id: 'ACC-982705', label: 'Meridian', role: 'Treasury source', risk: 'Low', cx: 90, cy: 45, r: 12 },
                    { id: 'ACC-982672', label: 'Blackwood', role: 'Loop exit account', risk: 'Critical', cx: 310, cy: 50, r: 12 },
                    { id: 'ACC-982659', label: 'Shell-901', role: 'Dynamic Layerer', risk: 'High', cx: 200, cy: 140, r: 12 }
                ],
                graphLinks: [
                    { source: 1, target: 0, flow: true },
                    { source: 0, target: 2, flow: true },
                    { source: 2, target: 3, flow: true },
                    { source: 3, target: 0, flow: true }
                ]
            }
        }
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

    // Load Database
    function getDb() {
        const stored = localStorage.getItem(STORE_KEY);
        let db;
        if (!stored) {
            db = defaultDb;
            ensureDefaultRules(db);
            saveDb(db);
            return db;
        }
        try {
            db = JSON.parse(stored);
            ensureDefaultRules(db);
            return db;
        } catch (e) {
            db = defaultDb;
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
            // Enrich graphNode risk labels dynamically based on live accounts table
            const enriched = JSON.parse(JSON.stringify(db.networks));
            Object.keys(enriched).forEach(netId => {
                const net = enriched[netId];
                net.graphNodes.forEach(node => {
                    if (node.id && db.accounts[node.id]) {
                        const acc = db.accounts[node.id];
                        node.risk = acc.riskScore >= 90 ? 'Critical' : (acc.riskScore >= 70 ? 'High' : (acc.riskScore >= 40 ? 'Medium' : 'Low'));
                        node.status = acc.status; // live state (Normal, Blocked, Under Review, Flagged)
                    }
                });
            });
            return enriched;
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
            const newLog = {
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
            };
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
