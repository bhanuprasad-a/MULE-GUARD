const fs = require('fs');
const path = require('path');

console.log("====================================================");
console.log("MULEGUARD REAL-TIME INGESTION VERIFICATION RUNNER");
console.log("====================================================\n");

// 1. Setup global browser mocks for Node.js
global.window = global;
global.localStorage = {
    store: {},
    getItem(key) { return this.store[key] || null; },
    setItem(key, value) { this.store[key] = String(value); },
    removeItem(key) { delete this.store[key]; },
    clear() { this.store = {}; }
};
global.document = {
    write(html) { /* Mock script inclusion write */ }
};

// Mock CustomEvent
global.CustomEvent = class CustomEvent {
    constructor(name, opts) {
        this.type = name;
        this.detail = opts ? opts.detail : null;
    }
};
global.dispatchEvent = function(event) {
    global.dispatchedEvents.push(event);
};
global.dispatchedEvents = [];

// 2. Load the actual browser scripts in sequence
const dbPath = path.resolve(__dirname, '../frontend/scripts/synthetic_db_expanded.js');
const modelPath = path.resolve(__dirname, '../frontend/scripts/best_muleguard_model.js');
const inferPath = path.resolve(__dirname, '../frontend/scripts/xgboost-infer.js');
const storePath = path.resolve(__dirname, '../frontend/scripts/data-store.js');
const simPath   = path.resolve(__dirname, '../frontend/scripts/transaction-simulator.js');

try {
    eval(fs.readFileSync(dbPath, 'utf8'));
    eval(fs.readFileSync(modelPath, 'utf8'));
    eval(fs.readFileSync(inferPath, 'utf8'));
    eval(fs.readFileSync(storePath, 'utf8'));
    eval(fs.readFileSync(simPath, 'utf8'));
    console.log("✔ Environment loaded successfully.");
} catch (e) {
    console.error("✘ Failed to load environment:", e);
    process.exit(1);
}

// Helper to assert
function assert(condition, message) {
    if (!condition) {
        console.error("  ✘ FAIL:", message);
        throw new Error(message);
    }
    console.log("  ✔ PASS:", message);
}

const Store = window.MuleGuardStore;
const Sim = window.MuleGuardSimulator;

// Keep verification fast and deterministic without changing the protected seed file.
// data-store.js retains a reference to this object as its reset seed, so mutate only
// this in-memory test fixture before any test reset occurs.
const verificationSeed = window.MuleGuardExpandedDB;
verificationSeed.accounts = {
    'ACC-982134': { id: 'ACC-982134', name: 'Verification Sender', type: 'Current', balance: 1000000, riskScore: 10, status: 'Normal', phone: 'V-134', device: 'V-134', ip: '10.0.0.134' },
    'ACC-982135': { id: 'ACC-982135', name: 'Verification Counterparty', type: 'Current', balance: 500000, riskScore: 10, status: 'Normal', phone: 'V-135', device: 'V-135', ip: '10.0.0.135' },
    'ACC-982006': { id: 'ACC-982006', name: 'Verification Target', type: 'Savings', balance: 50000, riskScore: 10, status: 'Normal', phone: 'V-006', device: 'V-006', ip: '10.0.0.6' },
    'ACC-982008': { id: 'ACC-982008', name: 'Verification Network Target', type: 'Savings', balance: 50000, riskScore: 10, status: 'Normal', phone: 'V-008', device: 'V-008', ip: '10.0.0.8' }
};
verificationSeed.transactions = [];
verificationSeed.alerts = [];
verificationSeed.cases = [{ id: 'CS-VERIFY', title: 'Verification case', primaryEntityId: 'ACC-982006', priority: 'Low', status: 'New', activity: [], notes: '' }];
verificationSeed.auditLogs = [];
verificationSeed.networks = {};
localStorage.clear();

function activeAlertsFor(accountId) {
    return Store.getAlerts().filter(alert =>
        alert.accountId === accountId &&
        !['Resolved', 'False Positive', 'Dismissed'].includes(alert.status)
    );
}

function preparePersistentMlState(accountId, probability, threshold, setProbability) {
    Store.resetTransactionSimulation();
    setProbability(probability);
    const db = JSON.parse(localStorage.getItem('muleguard_db'));
    db.rules.forEach(rule => { rule.active = false; });
    db.alerts.forEach(alert => {
        if (alert.accountId === accountId && !['Resolved', 'False Positive', 'Dismissed'].includes(alert.status)) {
            alert.status = 'Resolved';
        }
    });
    localStorage.setItem('muleguard_db', JSON.stringify(db));
    const thresholdResult = Store.setRiskThreshold(threshold);
    assert(thresholdResult.success === true, 'Threshold update should succeed through the persistent store path');
    Store.generateAlertsFromAllAccounts();
    const state = Store.getAccountInferenceState(accountId);
    assert(state && state.currentProbability === probability, 'ML inference state should persist the current probability');
    assert(state.thresholdUsed === threshold, 'ML inference state should persist the threshold used');
}

// Reset dataset to baseline state
Store.resetTransactionSimulation();

// -----------------------------------------------------------------------------
// Test 1: Transaction Ingestion
// -----------------------------------------------------------------------------
console.log("\n[Test 1] Ingest Transaction Ledger Verification...");
const testTx1 = {
    id: "TX-TEST-001",
    senderId: "ACC-982134",
    receiverId: "ACC-982006",
    amountNumeric: 5000,
    type: "Transfer",
    summary: "Verification Test Transfer 1"
};

const initialTxLength = Store.getTransactions().length;
const res1 = Store.ingestTransaction(testTx1);
assert(res1.success === true, "Ingestion should succeed with valid parameters");
assert(Store.getTransactions().length === initialTxLength + 1, "Ledger size should increase by 1");
assert(Store.getTransactions()[0].id === "TX-TEST-001", "Newest transaction should be on top of ledger");

// -----------------------------------------------------------------------------
// Test 2: Feature Recalculation
// -----------------------------------------------------------------------------
console.log("\n[Test 2] Feature Recalculation Verification...");
const featsBefore = Store.getAccountFeatures("ACC-982006");
// Ingest a second transaction affecting ACC-982006
Store.ingestTransaction({
    id: "TX-TEST-002",
    senderId: "ACC-982134",
    receiverId: "ACC-982006",
    amountNumeric: 10000,
    type: "Transfer"
});
const featsAfter = Store.getAccountFeatures("ACC-982006");
assert(featsAfter.txCount === featsBefore.txCount + 1, "Transaction count feature should increment");
assert(featsAfter.totalInAmount === featsBefore.totalInAmount + 10000, "Total Inbound Amount feature should increase by 10,000");

// -----------------------------------------------------------------------------
// Test 3: Network Feature Recalculation
// -----------------------------------------------------------------------------
console.log("\n[Test 3] Network Feature Recalculation Verification...");
// Ingest transaction from new sender ACC-982135 to receiver ACC-982008
const netBefore = Store.getAccountFeatures("ACC-982008");
Store.ingestTransaction({
    id: "TX-TEST-003",
    senderId: "ACC-982135",
    receiverId: "ACC-982008",
    amountNumeric: 20000,
    type: "Transfer"
});
const netAfter = Store.getAccountFeatures("ACC-982008");
assert(netAfter.totalDegree > netBefore.totalDegree, "Total Network Degree should increase");
assert(netAfter.fanIn > netBefore.fanIn, "Inbound counterparty fan-in should increase");

// -----------------------------------------------------------------------------
// Test 4: ML Recalculation
// -----------------------------------------------------------------------------
console.log("\n[Test 4] ML Probability Recalculation...");
const riskStatus = Store.predictAccountRisk("ACC-982006");
assert(riskStatus !== null && typeof riskStatus.probability === "number", "ML probability should be a valid calculated number");
assert(riskStatus.probability >= 0 && riskStatus.probability <= 1, "ML probability should be bounded between 0 and 1");

// -----------------------------------------------------------------------------
// Test 5: Rule Re-evaluation
// -----------------------------------------------------------------------------
console.log("\n[Test 5] Rule Re-evaluation Verification...");
const rules = Store.getRules();
assert(rules && rules.length > 0, "Rules metadata should be present and non-empty");

// -----------------------------------------------------------------------------
// Stub ML Model predictions to test threshold crossing logic deterministically
// -----------------------------------------------------------------------------
const originalPredictRisk = window.MuleGuardXGBoost.predictRisk;
const originalPredictRiskWithFeatures = window.MuleGuardXGBoost.predictRiskWithFeatures;

let stubbedProb = 0.10;
window.MuleGuardXGBoost.predictRisk = function() {
    return stubbedProb;
};
window.MuleGuardXGBoost.predictRiskWithFeatures = function() {
    return {
        probability: stubbedProb,
        topFeatures: [
            { name: "rapidHoldingRatio", label: "Short Holding Ratio", value: 95 },
            { name: "networkConcentration", label: "Network Concentration", value: 0.8 },
            { name: "cycleParticipation", label: "Cycle Participation", value: 1 }
        ]
    };
};

// -----------------------------------------------------------------------------
// Test 6: ML Threshold Crossing Semantics
// -----------------------------------------------------------------------------
console.log("\n[Test 6] ML Threshold Crossing Semantics (Below -> Above)...");
const targetAccId = "ACC-982006";
preparePersistentMlState(targetAccId, 0.10, 0.40, value => { stubbedProb = value; });
assert(Store.predictAccountRisk(targetAccId).probability < 0.40, "Baseline ML probability must be below threshold");

// Step B: Set stub probability above threshold (0.55) to trigger threshold crossing
stubbedProb = 0.55;
const prevAlertCount = activeAlertsFor(targetAccId).length;

const resCrossing = Store.ingestTransaction({
    id: "TX-CROSSING",
    senderId: "ACC-982134",
    receiverId: targetAccId,
    amountNumeric: 250000,
    type: "Transfer"
});

const alertsAfter = activeAlertsFor(targetAccId);
assert(alertsAfter.length === prevAlertCount + 1, "Exactly one new alert should be created on threshold crossing");
assert(alertsAfter[0].accountId === targetAccId, "Alert target should match the crossing account");
assert(alertsAfter[0].mlProbability === 0.55, "ML probability in the alert should match the crossed probability");
assert(alertsAfter[0].previousMLProbability === 0.10 && alertsAfter[0].currentMLProbability === 0.55,
    "Alert should preserve the persisted previous and current ML probabilities");
assert(alertsAfter[0].detectionSource === "ML", "Crossing should be ML-only while rules are inactive");

// -----------------------------------------------------------------------------
// Test 7: No Duplicate ML Alert
// -----------------------------------------------------------------------------
console.log("\n[Test 7] No Duplicate ML Alert when staying above threshold...");
const alertCountAfterFirst = activeAlertsFor(targetAccId).length;

// Ingest another transaction while probability remains above threshold (0.60)
stubbedProb = 0.60;
Store.ingestTransaction({
    id: "TX-ABOVE-2",
    senderId: "ACC-982134",
    receiverId: targetAccId,
    amountNumeric: 100000,
    type: "Transfer"
});

const alertCountAfterSecond = activeAlertsFor(targetAccId).length;
assert(alertCountAfterSecond === alertCountAfterFirst, "Alert count should NOT increase when staying above threshold");

// -----------------------------------------------------------------------------
// Test 8: Combined Detection Source
// -----------------------------------------------------------------------------
console.log("\n[Test 8] Combined ML + Rule Alert Verification...");
Store.updateRule('R-VEL-1', 0, true);
const crossAlert = activeAlertsFor(targetAccId)[0];
assert(crossAlert.detectionSource === "Combined", "Detection source should be Combined when both ML and Rules trigger");
assert(crossAlert.triggeredRules.length > 0, "Triggered rules array should not be empty");
assert(crossAlert.mlProbability === 0.60, "Combined alert should retain the latest ML probability evidence");

// -----------------------------------------------------------------------------
// Test 8B: Rule-only and threshold-policy re-evaluation
// -----------------------------------------------------------------------------
console.log("\n[Test 8B] Rule-only and threshold-change re-evaluation...");
activeAlertsFor(targetAccId).forEach(alert => Store.resolveAlert(alert.id));
stubbedProb = 0.10;
Store.generateAlertsFromAllAccounts();
const ruleOnlyAlert = activeAlertsFor(targetAccId)[0];
assert(ruleOnlyAlert && ruleOnlyAlert.detectionSource === "Rule", "Below-threshold ML with active rule should produce a Rule-only alert");

activeAlertsFor(targetAccId).forEach(alert => Store.resolveAlert(alert.id));
const thresholdSetupDb = JSON.parse(localStorage.getItem('muleguard_db'));
thresholdSetupDb.rules.forEach(rule => { rule.active = false; });
localStorage.setItem('muleguard_db', JSON.stringify(thresholdSetupDb));
stubbedProb = 0.35;
Store.generateAlertsFromAllAccounts();
const logsBeforeThresholdChange = Store.getLogs().length;
const thresholdChange = Store.setRiskThreshold(0.30);
assert(thresholdChange.success === true && thresholdChange.previousThreshold === 0.40,
    "Threshold change should report the previous persisted threshold");
const policyAlert = activeAlertsFor(targetAccId)[0];
assert(policyAlert && policyAlert.detectionSource === "ML",
    "A lower threshold should activate a newly eligible ML alert through deterministic re-evaluation");
assert(Store.getLogs().length > logsBeforeThresholdChange && Store.getLogs().some(l => l.eventType === 'RISK_THRESHOLD_UPDATED'),
    "Threshold change should be recorded in the audit trail");

// Restore original prediction function wrappers before non-ML regression checks.
window.MuleGuardXGBoost.predictRisk = originalPredictRisk;
window.MuleGuardXGBoost.predictRiskWithFeatures = originalPredictRiskWithFeatures;

// -----------------------------------------------------------------------------
// Test 9: Audit Trail Tracing
// -----------------------------------------------------------------------------
console.log("\n[Test 9] Audit Trail Ingestion Tracing...");
const logs = Store.getLogs();
const ingestionLogs = logs.filter(l => l.eventType === 'TRANSACTION_INGESTED');
assert(ingestionLogs.length > 0, "Ingestion events must be recorded in the central audit logs");
assert(ingestionLogs.some(l => l.action.includes("TX-CROSSING") || l.details.includes("TX-CROSSING")), "Audit trail must log the ingested transaction ID");

// -----------------------------------------------------------------------------
// Test 10: INR Requirement
// -----------------------------------------------------------------------------
console.log("\n[Test 10] INR Formatting Checks...");
const ledger = Store.getTransactions();
assert(ledger[0].value.startsWith("₹"), "Ingested transaction value must start with ₹ prefix");
assert(!ledger[0].value.includes("$") && !ledger[0].value.includes("USD"), "Monetary value must not contain USD or $");

// -----------------------------------------------------------------------------
// Test 11: Simulator Lifecycle States
// -----------------------------------------------------------------------------
console.log("\n[Test 11] Simulator Lifecycle Play/Pause/Stop...");
// Verify idempotent starts
Sim.stop();
Sim.start("Legitimate", 3000);
const state1 = Sim.getState();
assert(state1.status === "Running", "Simulator state should be Running after start()");

// Attempt double-start
Sim.start("Legitimate", 1000);
const state2 = Sim.getState();
assert(state2.intervalMs === 3000, "Double-start must not modify interval or spawn duplicate loops");

// Pause
Sim.pause();
assert(Sim.getState().status === "Paused", "Simulator status should be Paused");

// Resume
Sim.resume();
assert(Sim.getState().status === "Running", "Simulator status should return to Running after resume()");

// Stop
Sim.stop();
assert(Sim.getState().status === "Stopped", "Simulator status should be Stopped after stop()");

// -----------------------------------------------------------------------------
// Test 12: Existing Workflows Protected
// -----------------------------------------------------------------------------
console.log("\n[Test 12] Workflow Regression Checks...");
const cases = Store.getCases();
assert(cases && cases.length > 0, "Seeded cases list should remain functional");
const rulesMeta = Store.getRules();
assert(rulesMeta.length === 6, "Rule definitions array must contain 6 active rules including R-CIRC-1 and R-DORM-1");

// -----------------------------------------------------------------------------
// Additional Assertions
// -----------------------------------------------------------------------------
console.log("\n[Test 13] Atomic Rollback on Ingestion Downstream Failure...");
const originalTxCount = Store.getTransactions().length;
const originalBalance = Store.getAccounts()["ACC-982134"].balance;

// Mock evaluateRules to throw an intentional downstream error
const originalEvaluateRules = Store.evaluateRules;
Store.evaluateRules = function() {
    throw new Error("Downstream crash simulation");
};

// Attempt to ingest valid transaction
const failedRes = Store.ingestTransaction({
    id: "TX-CRASH-TEST",
    senderId: "ACC-982134",
    receiverId: "ACC-982006",
    amountNumeric: 1000,
    type: "Transfer"
});

// Verify rollback succeeded
assert(failedRes.success === false, "Ingestion must report failure if downstream rules engine fails");
assert(Store.getTransactions().length === originalTxCount, "Ledger size must remain unchanged after failed ingestion");
assert(Store.getAccounts()["ACC-982134"].balance === originalBalance, "Account balances must remain unchanged after failed ingestion");

// Restore rules engine function
Store.evaluateRules = originalEvaluateRules;

console.log("\n[Test 14] Balance and Negative-Balance Protection...");
const richSender = "ACC-982134";
const currentBal = Store.getAccounts()[richSender].balance;

// Attempt to ingest transaction with amount exceeding balance
const overdrawRes = Store.ingestTransaction({
    id: "TX-OVERDRAW",
    senderId: richSender,
    receiverId: "ACC-982006",
    amountNumeric: currentBal + 1000, // overdraw
    type: "Transfer"
});
assert(overdrawRes.success === false, "Overdrawing transactions must be rejected");
assert(Store.getAccounts()[richSender].balance === currentBal, "Sender balance must not change on overdraw rejection");

// Attempt to ingest unknown account
const unknownRes = Store.ingestTransaction({
    id: "TX-UNKNOWN",
    senderId: "ACC-UNKNOWN",
    receiverId: "ACC-982006",
    amountNumeric: 1000,
    type: "Transfer"
});
assert(unknownRes.success === false, "Transactions with unknown accounts must be rejected");

console.log("\n[Test 15] Deterministic Scenarios & Reset Verification...");
Store.resetTransactionSimulation();
const resetDb = Store.getTransactions();
assert(resetDb.length === verificationSeed.transactions.length, `Reset restores database transactions list to the expected seed length of ${verificationSeed.transactions.length}`);

// -----------------------------------------------------------------------------
// Test 16: Temporal Correctness & Windowing (Phase B)
// -----------------------------------------------------------------------------
console.log("\n[Test 16] Temporal Correctness & Windowing Checks...");
Store.resetTransactionSimulation();
const accTemp = "ACC-982006";

const now = Date.now();
const txWithin24h = new Date(now - (23 * 3600 * 1000)).toISOString();
const txOutside24h = new Date(now - (25 * 3600 * 1000)).toISOString();

// Ingest transaction outside 24h window (25h ago)
Store.ingestTransaction({
    id: "TX-OLD-25H",
    senderId: "ACC-982134",
    receiverId: accTemp,
    amountNumeric: 5000,
    timestamp: txOutside24h,
    time: "1 day ago"
});

// Ingest transaction inside 24h window (23h ago)
Store.ingestTransaction({
    id: "TX-RECENT-23H",
    senderId: "ACC-982134",
    receiverId: accTemp,
    amountNumeric: 10000,
    timestamp: txWithin24h,
    time: "23 hrs ago"
});

Store.evaluateRules();
const accAfterTemp = Store.getAccounts()[accTemp];
assert(accAfterTemp !== undefined, "Target account must exist for temporal checks");

// 30-minute matched holding time (Inbound followed by outbound within 30m)
const inTimeMs = now - (10 * 60 * 1000); // 10 min ago
const outWithin30mMs = now - (5 * 60 * 1000); // 5 min ago (5 min after inbound)

const tInIso = new Date(inTimeMs).toISOString();
const tOut30mIso = new Date(outWithin30mMs).toISOString();

Store.ingestTransaction({
    id: "TX-IN-SEQ",
    senderId: "ACC-982134",
    receiverId: accTemp,
    amountNumeric: 50000,
    timestamp: tInIso,
    time: "10 min ago"
});

Store.ingestTransaction({
    id: "TX-OUT-30M",
    senderId: accTemp,
    receiverId: "ACC-982135",
    amountNumeric: 50000,
    timestamp: tOut30mIso,
    time: "5 min ago"
});

Store.evaluateRules();
const triggersHold = Store.getAccounts()[accTemp].triggers || [];
assert(triggersHold.some(t => t.includes("Short Holding Ratio")), "Short Holding Ratio rule must trigger for outbound within 30m of inbound");

// Legacy transactions without canonical timestamp
Store.ingestTransaction({
    id: "TX-LEGACY",
    senderId: "ACC-982134",
    receiverId: "ACC-982135",
    amountNumeric: 1500,
    time: "12 min ago"
});
const legacyTx = Store.getTransactions().find(t => t.id === "TX-LEGACY");
assert(legacyTx !== undefined && legacyTx.timestamp !== undefined, "Ingest should backfill canonical timestamp for legacy/relative inputs");

// -----------------------------------------------------------------------------
// Test 17: Additive Named Rules R-CIRC-1 & R-DORM-1 (Phase C)
// -----------------------------------------------------------------------------
console.log("\n[Test 17] Missing Rules (R-CIRC-1 & R-DORM-1) Verification...");
const activeRules = Store.getRules();
assert(activeRules.some(r => r.id === 'R-CIRC-1'), "R-CIRC-1 (Circular Money Flow) must be present in rules");
assert(activeRules.some(r => r.id === 'R-DORM-1'), "R-DORM-1 (Dormant Account Activation) must be present in rules");

// Stub getAccountFeatures to test R-CIRC-1 trigger
const origGetFeats = Store.getAccountFeatures;
Store.getAccountFeatures = function(accId) {
    const feats = origGetFeats.call(Store, accId) || {};
    feats.cycleParticipation = 1;
    return feats;
};
Store.evaluateRules();
const circTriggers = Store.getAccounts()["ACC-982006"].triggers || [];
assert(circTriggers.some(t => t.includes("Circular Money Flow")), "R-CIRC-1 must trigger when cycleParticipation > 0");
Store.getAccountFeatures = origGetFeats;

// Test R-DORM-1 trigger on old account (>90 days) receiving large 24h transfer
const dormAccId = "ACC-982008";
const dormAcc = Store.getAccounts()[dormAccId];
dormAcc.created = "2024-01-01"; // Old account registered >90 days ago
Store.ingestTransaction({
    id: "TX-DORM-IN",
    senderId: "ACC-982134",
    receiverId: dormAccId,
    amountNumeric: 60000,
    time: "Just now"
});
Store.evaluateRules();
const dormTriggers = Store.getAccounts()[dormAccId].triggers || [];
assert(dormTriggers.some(t => t.includes("Dormant Account Activation")), "R-DORM-1 must trigger for account created >90 days ago receiving >₹50,000 in 24h");

console.log("\n====================================================");
console.log("ALL TESTS COMPLETED SUCCESSFULLY: 17/17 PASS");
console.log("====================================================");
