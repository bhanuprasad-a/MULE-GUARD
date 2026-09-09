(function() {
    let simIntervalId = null;
    let currentScenario = "Legitimate";
    let scenarioStep = 0;
    
    // Deterministic scenario definitions using clean and target accounts from synthetic_db_expanded
    const Scenarios = {
        "Legitimate": [
            { senderId: 'ACC-982134', receiverId: 'ACC-982135', amountNumeric: 12000, type: 'Payment', summary: 'Supplier invoice payment' },
            { senderId: 'ACC-982135', receiverId: 'ACC-982136', amountNumeric: 8500, type: 'Payment', summary: 'Logistics delivery clearing' },
            { senderId: 'ACC-982136', receiverId: 'ACC-982137', amountNumeric: 5200, type: 'Transfer', summary: 'Inter-office reimbursement' },
            { senderId: 'ACC-982137', receiverId: 'ACC-982134', amountNumeric: 9000, type: 'Payment', summary: 'Corporate subscription renewal' }
        ],
        "Suspicious Rapid Forwarding": [
            // Target recipient is ACC-982006 (balance ₹31,665.24)
            { senderId: 'ACC-982134', receiverId: 'ACC-982006', amountNumeric: 220000, type: 'Transfer', summary: 'High value deposit layering' },
            { senderId: 'ACC-982006', receiverId: 'ACC-982135', amountNumeric: 219500, type: 'Transfer', summary: 'Rapid outbound forwarding' }
        ],
        "Network Expansion": [
            // Target recipient is ACC-982008
            { senderId: 'ACC-982134', receiverId: 'ACC-982008', amountNumeric: 15000, type: 'Payment', summary: 'Network wire 1' },
            { senderId: 'ACC-982135', receiverId: 'ACC-982008', amountNumeric: 18000, type: 'Payment', summary: 'Network wire 2' },
            { senderId: 'ACC-982136', receiverId: 'ACC-982008', amountNumeric: 12000, type: 'Transfer', summary: 'Network wire 3' },
            { senderId: 'ACC-982137', receiverId: 'ACC-982008', amountNumeric: 25000, type: 'Transfer', summary: 'Network wire 4' },
            { senderId: 'ACC-982008', receiverId: 'ACC-982138', amountNumeric: 30000, type: 'Payment', summary: 'Outbound fan-out route' }
        ],
        "Circular Transaction": [
            { senderId: 'ACC-982134', receiverId: 'ACC-982135', amountNumeric: 45000, type: 'Transfer', summary: 'Circular flow leg 1' },
            { senderId: 'ACC-982135', receiverId: 'ACC-982136', amountNumeric: 45000, type: 'Transfer', summary: 'Circular flow leg 2' },
            { senderId: 'ACC-982136', receiverId: 'ACC-982134', amountNumeric: 45000, type: 'Transfer', summary: 'Circular flow leg 3' }
        ]
    };

    function getSimState() {
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

    function saveSimState(state) {
        localStorage.setItem('muleguard_sim_state', JSON.stringify(state));
    }

    function tick() {
        const state = getSimState();
        const scName = state.scenario || "Legitimate";
        const list = Scenarios[scName] || [];
        if (list.length === 0) return;

        // Fetch transaction template deterministically
        const template = list[scenarioStep % list.length];
        scenarioStep++;

        // Call ingestTransaction on the store
        if (window.MuleGuardStore && window.MuleGuardStore.ingestTransaction) {
            const res = window.MuleGuardStore.ingestTransaction(template);
            if (res.success) {
                const tx = res.transaction;
                // Get updated ML probability of receiver
                let updatedProb = null;
                let updatedSource = null;
                const risk = window.MuleGuardStore.predictAccountRisk(tx.receiverId);
                if (risk) {
                    updatedProb = (risk.probability * 100).toFixed(1) + "%";
                }
                // Check if any alert is active for the receiver
                const alerts = window.MuleGuardStore.getAlerts();
                const activeAlert = alerts.find(a => a.accountId === tx.receiverId && a.status === 'New');
                if (activeAlert) {
                    updatedSource = activeAlert.detectionSource;
                }

                // Update state statistics
                state.txCount = (state.txCount || 0) + 1;
                state.lastTxAmount = tx.amountNumeric;
                state.lastTxSender = tx.senderId;
                state.lastTxReceiver = tx.receiverId;
                state.lastTxProb = updatedProb;
                state.lastTxSource = updatedSource || "None";
                state.lastTxTime = new Date().toLocaleTimeString();
                state.error = null;
                saveSimState(state);

                // Dispatch global event for the control panel to update itself
                const event = new CustomEvent('muleguard:simulator-tick', { detail: state });
                window.dispatchEvent(event);
            } else {
                console.error("Simulation ingestion failed:", res.error);
                // Pause simulation to prevent runaways
                window.MuleGuardSimulator.pause();
                state.error = res.error;
                saveSimState(state);
                window.dispatchEvent(new CustomEvent('muleguard:simulator-tick', { detail: state }));
            }
        }
    }

    window.MuleGuardSimulator = {
        start: function(scenarioName, intervalMs) {
            // Safety limits
            const safeInterval = Math.max(500, intervalMs || 3000);
            
            // Check double-start
            if (simIntervalId !== null) {
                console.warn("Simulator is already running.");
                return;
            }

            const state = getSimState();
            state.status = "Running";
            state.scenario = scenarioName || "Legitimate";
            state.intervalMs = safeInterval;
            state.error = null;
            saveSimState(state);

            currentScenario = state.scenario;
            scenarioStep = 0; // Reset deterministic steps on start

            simIntervalId = setInterval(tick, safeInterval);
            window.dispatchEvent(new CustomEvent('muleguard:simulator-tick', { detail: state }));
        },

        stop: function() {
            if (simIntervalId !== null) {
                clearInterval(simIntervalId);
                simIntervalId = null;
            }
            const state = getSimState();
            state.status = "Stopped";
            state.error = null;
            saveSimState(state);
            scenarioStep = 0;

            window.dispatchEvent(new CustomEvent('muleguard:simulator-tick', { detail: state }));
        },

        pause: function() {
            if (simIntervalId !== null) {
                clearInterval(simIntervalId);
                simIntervalId = null;
            }
            const state = getSimState();
            state.status = "Paused";
            saveSimState(state);

            window.dispatchEvent(new CustomEvent('muleguard:simulator-tick', { detail: state }));
        },

        resume: function() {
            const state = getSimState();
            if (state.status !== "Paused") return;

            // Check double-start
            if (simIntervalId !== null) return;

            state.status = "Running";
            state.error = null;
            saveSimState(state);

            simIntervalId = setInterval(tick, state.intervalMs || 3000);
            window.dispatchEvent(new CustomEvent('muleguard:simulator-tick', { detail: state }));
        },

        getState: function() {
            return getSimState();
        }
    };

    // Auto-resume if status says running (e.g. after a page navigation or refresh)
    const state = getSimState();
    if (state.status === "Running") {
        if (simIntervalId !== null) {
            clearInterval(simIntervalId);
        }
        simIntervalId = setInterval(tick, state.intervalMs || 3000);
    }
})();
