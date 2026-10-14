/**
 * verify_audit_trail_dom.js
 * Comprehensive DOM, UI logic, and client simulation test for audit-trail.html
 */
const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '..');
const HTML_PATH = path.join(ROOT_DIR, 'frontend', 'bank', 'compliance', 'audit-trail.html');
const htmlSource = fs.readFileSync(HTML_PATH, 'utf-8');

console.log("====================================================");
console.log("MULEGUARD AUDIT TRAIL DOM & INTERACTION VERIFICATION");
console.log("====================================================\n");

let passed = 0;
function check(condition, message) {
    if (!condition) {
        console.error(`  ✖ FAIL: ${message}`);
        process.exit(1);
    }
    console.log(`  ✔ PASS: ${message}`);
    passed++;
}

// 1. Static HTML Checks
console.log("[Section 1] Static HTML & Component IDs...");
check(htmlSource.includes('<h1 class="font-headline-md text-[18px] text-on-surface font-bold tracking-tight">Audit Trail</h1>'), "Header title is 'Audit Trail'");
check(htmlSource.includes('id="sidebar-container"'), "Sidebar container present");
check(htmlSource.includes('id="kpi-total-events"'), "KPI total events element present");
check(htmlSource.includes('id="kpi-auth-events"'), "KPI auth events element present");
check(htmlSource.includes('id="kpi-sec-events"'), "KPI sec events element present");
check(htmlSource.includes('id="kpi-tx-events"'), "KPI tx events element present");
check(htmlSource.includes('id="filter-search"'), "Search filter input present");
check(htmlSource.includes('id="filter-category"'), "Category select element present");
check(htmlSource.includes('id="filter-limit"'), "Limit select element present");
check(htmlSource.includes('id="btn-refresh"'), "Refresh button present");
check(htmlSource.includes('id="audit-table-body"'), "Audit table tbody present");
check(htmlSource.includes('id="audit-pagination-info"'), "Pagination info element present");
check(htmlSource.includes('id="audit-page-number"'), "Pagination page number element present");
check(htmlSource.includes('id="btn-prev"'), "Prev page button present");
check(htmlSource.includes('id="btn-next"'), "Next page button present");
check(htmlSource.includes('id="audit-detail-modal"'), "Audit detail modal element present");
check(htmlSource.includes('id="modal-details-payload"'), "Modal details payload pre element present");

// 2. Extract and Validate JavaScript
console.log("\n[Section 2] Client Script Syntax & Functions...");
const scriptMatch = htmlSource.match(/<script>([\s\S]*?)<\/script>\s*<\/body>/i);
check(scriptMatch !== null, "Inline script block successfully located");

const clientScript = scriptMatch[1];
check(!clientScript.includes('MuleGuardStore'), "Strict zero MuleGuardStore banking calls");
check(clientScript.includes('MuleGuardAPI.getAuditLogs'), "Uses MuleGuardAPI.getAuditLogs");
check(clientScript.includes('MuleGuardAPI.getAuditSummary'), "Uses MuleGuardAPI.getAuditSummary");
check(clientScript.includes('openAuditDetailModal'), "Implements openAuditDetailModal");
check(clientScript.includes('closeAuditDetailModal'), "Implements closeAuditDetailModal");
check(clientScript.includes('debounceSearch'), "Implements debounceSearch");
check(clientScript.includes('applyFilters'), "Implements applyFilters");
check(clientScript.includes('goToPrevPage'), "Implements goToPrevPage");
check(clientScript.includes('goToNextPage'), "Implements goToNextPage");

// 3. Execution Simulation in Mock DOM
console.log("\n[Section 3] Client Logic Simulation in Mock Environment...");
const elements = {};
function createMockElement(id, tag = 'div') {
    return {
        id: id,
        tagName: tag.toUpperCase(),
        textContent: '',
        innerHTML: '',
        value: '',
        disabled: false,
        classList: {
            classes: new Set(),
            add(c) { this.classes.add(c); },
            remove(c) { this.classes.delete(c); },
            contains(c) { return this.classes.has(c); },
            toggle(c) { if (this.classes.has(c)) { this.classes.delete(c); return false; } else { this.classes.add(c); return true; } }
        }
    };
}

[
    'kpi-total-events', 'kpi-auth-events', 'kpi-sec-events', 'kpi-tx-events',
    'audit-badge-total', 'filter-search', 'filter-category', 'filter-limit',
    'btn-refresh', 'audit-table-body', 'audit-pagination-info', 'audit-page-number',
    'btn-prev', 'btn-next', 'audit-detail-modal', 'modal-event-id',
    'modal-event-subtitle', 'modal-category-badge', 'modal-action-text',
    'modal-actor-text', 'modal-result-badge', 'modal-timestamp-text',
    'modal-resource-text', 'modal-ip-text', 'modal-details-payload'
].forEach(id => {
    elements[id] = createMockElement(id);
});

elements['filter-category'].value = 'ALL';
elements['filter-limit'].value = '50';

const mockDocument = {
    getElementById(id) {
        return elements[id] || null;
    },
    addEventListener(event, fn) {}
};

const mockWindow = {
    location: { href: 'http://localhost:8000/frontend/bank/compliance/audit-trail.html' },
    document: mockDocument,
    MuleGuardAPI: {
        getAuditSummary: async () => ({
            total_events: 2681,
            authentication_events: 2520,
            security_events: 140,
            transaction_events: 21,
        }),
        getAuditLogs: async (params) => ({
            status: "Healthy",
            summary: {
                total_events: 2681,
                authentication_events: 2520,
                security_events: 140,
                transaction_events: 21,
            },
            pagination: {
                limit: params.limit || 50,
                offset: params.offset || 0,
                total: 2681,
                has_more: true,
            },
            items: [
                {
                    id: "auth_101",
                    timestamp: "2026-10-11T12:00:00Z",
                    action: "LOGIN_SUCCESS",
                    entity_type: "auth",
                    entity_id: "MG-CMP-001",
                    account_id: null,
                    actor: "MG-CMP-001",
                    category: "AUTHENTICATION",
                    details: {
                        outcome: "SUCCESS",
                        ip_address: "10.99.1.1",
                        password: "[REDACTED]"
                    }
                },
                {
                    id: "app_202",
                    timestamp: "2026-10-11T11:45:00Z",
                    action: "ALERT_CREATED",
                    entity_type: "alert",
                    entity_id: "ALT-9081",
                    account_id: "ACC-1001",
                    actor: "SYSTEM",
                    category: "ALERT",
                    details: {
                        severity: "CRITICAL",
                        rule: "R-VEL-1"
                    }
                }
            ]
        })
    }
};

// Evaluate script inside mock context
const runScript = new Function(
    'window', 'document', 'setTimeout', 'clearTimeout',
    clientScript + `
    return {
        loadAuditSummary,
        loadAuditTrail,
        openAuditDetailModal,
        closeAuditDetailModal,
        formatTimestamp,
        getCategoryBadgeHTML,
        getStatusBadgeHTML
    };
`
);

const vm = runScript(mockWindow, mockDocument, setTimeout, clearTimeout);

// Run loadAuditSummary
vm.loadAuditSummary().then(() => {
    check(elements['kpi-total-events'].textContent === '2,681', "kpi-total-events correctly formatted as 2,681");
    check(elements['kpi-auth-events'].textContent === '2,520', "kpi-auth-events correctly formatted as 2,520");
    check(elements['kpi-sec-events'].textContent === '140', "kpi-sec-events correctly formatted as 140");
    check(elements['kpi-tx-events'].textContent === '21', "kpi-tx-events correctly formatted as 21");

    // Run loadAuditTrail
    return vm.loadAuditTrail(true);
}).then(() => {
    check(elements['audit-badge-total'].textContent === '2,681 Events', "Badge total updated");
    check(elements['audit-table-body'].innerHTML.includes('auth_101'), "Table body contains auth_101");
    check(elements['audit-table-body'].innerHTML.includes('app_202'), "Table body contains app_202");
    check(elements['audit-table-body'].innerHTML.includes('LOGIN_SUCCESS'), "Table body contains LOGIN_SUCCESS");
    check(elements['audit-table-body'].innerHTML.includes('ALERT_CREATED'), "Table body contains ALERT_CREATED");
    check(elements['btn-prev'].disabled === true, "Prev button disabled on page 1");
    check(elements['btn-next'].disabled === false, "Next button enabled when has_more is true");

    // Test Inspect modal
    elements['audit-detail-modal'].classList.add('hidden');
    vm.openAuditDetailModal(0);
    check(!elements['audit-detail-modal'].classList.contains('hidden'), "Modal opened (hidden class removed)");
    check(elements['modal-event-id'].textContent === 'Event auth_101', "Modal event id set to Event auth_101");
    check(elements['modal-action-text'].textContent === 'LOGIN_SUCCESS', "Modal action text set to LOGIN_SUCCESS");
    check(elements['modal-actor-text'].textContent === 'MG-CMP-001', "Modal actor text set to MG-CMP-001");
    check(elements['modal-ip-text'].textContent === '10.99.1.1', "Modal ip text set to 10.99.1.1");
    check(elements['modal-details-payload'].textContent.includes('[REDACTED]'), "Modal details payload preserves [REDACTED]");

    // Close Modal
    vm.closeAuditDetailModal();
    check(elements['audit-detail-modal'].classList.contains('hidden'), "Modal closed (hidden class restored)");

    console.log("\n====================================================");
    console.log(`ALL AUDIT TRAIL DOM TESTS PASSED: ${passed}/${passed}`);
    console.log("====================================================");
}).catch(err => {
    console.error("Simulation error:", err);
    process.exit(1);
});
