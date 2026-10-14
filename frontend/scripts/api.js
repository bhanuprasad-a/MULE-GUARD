const MuleGuardAPI = {
    baseURL: (typeof window !== 'undefined' && window.location && window.location.origin && window.location.origin.startsWith('http'))
        ? `${window.location.origin}/api/v1`
        : "http://127.0.0.1:8000/api/v1",

    async request(path, options = {}) {
        const response = await fetch(`${this.baseURL}${path}`, {
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            },
            ...options
        });

        if (!response.ok) {
            let detail = `API request failed: ${response.status}`;

            try {
                const error = await response.json();
                detail = error.detail || detail;
            } catch (_) { }

            throw new Error(detail);
        }

        return response.json();
    },

    // Accounts
    getAccounts(params = {}) {
        const query = new URLSearchParams();
        if (params.limit) query.set("limit", params.limit);
        if (params.offset !== undefined && params.offset !== null) query.set("offset", params.offset);
        const qs = query.toString();
        return this.request(`/accounts${qs ? '?' + qs : ''}`);
    },

    getAccount(accountId) {
        return this.request(`/accounts/${encodeURIComponent(accountId)}`);
    },

    getAccountTransactions(accountId) {
        return this.request(
            `/accounts/${encodeURIComponent(accountId)}/transactions`
        );
    },

    // Risk
    getAccountRisk(accountId) {
        return this.request(
            `/accounts/${encodeURIComponent(accountId)}/risk`
        );
    },

    getRiskSummary() {
        return this.request("/risk/summary");
    },

    getRiskDistribution() {
        return this.request("/risk/distribution");
    },

    // Alerts
    getAlerts(params = {}) {
        const query = new URLSearchParams();
        if (params.limit) query.set("limit", params.limit);
        if (params.offset !== undefined && params.offset !== null) query.set("offset", params.offset);
        const qs = query.toString();
        return this.request(`/alerts${qs ? '?' + qs : ''}`);
    },

    getAlert(alertId) {
        return this.request(`/alerts/${encodeURIComponent(alertId)}`);
    },

    analyzeAccount(accountId) {
        return this.request(
            `/alerts/analyze/${encodeURIComponent(accountId)}`,
            {
                method: "POST"
            }
        );
    },

    acknowledgeAlert(alertId) {
        return this.request(
            `/alerts/${encodeURIComponent(alertId)}/acknowledge`,
            {
                method: "PATCH"
            }
        );
    },

    // Cases
    getCases(params = {}) {
        const query = new URLSearchParams();
        if (params.limit) query.set("limit", params.limit);
        if (params.offset !== undefined && params.offset !== null) query.set("offset", params.offset);
        const qs = query.toString();
        return this.request(`/cases${qs ? '?' + qs : ''}`);
    },

    getCase(caseId) {
        return this.request(`/cases/${encodeURIComponent(caseId)}`);
    },

    createCaseFromAlert(alertId) {
        return this.request(
            `/cases/from-alert/${encodeURIComponent(alertId)}`,
            {
                method: "POST"
            }
        );
    },

    investigateCase(caseId) {
        return this.request(
            `/cases/${encodeURIComponent(caseId)}/investigate`,
            {
                method: "PATCH"
            }
        );
    },

    escalateCase(caseId) {
        return this.request(
            `/cases/${encodeURIComponent(caseId)}/escalate`,
            {
                method: "PATCH"
            }
        );
    },

    resolveCase(caseId) {
        return this.request(
            `/cases/${encodeURIComponent(caseId)}/resolve`,
            {
                method: "PATCH"
            }
        );
    },

    // Audit Trail
    getAuditLogs(params = {}) {
        const query = new URLSearchParams();
        if (params.limit) query.set("limit", params.limit);
        if (params.offset !== undefined && params.offset !== null) query.set("offset", params.offset);
        if (params.category && params.category !== "ALL") query.set("category", params.category);
        if (params.action) query.set("action", params.action);
        if (params.entity_type) query.set("entity_type", params.entity_type);
        if (params.entity_id) query.set("entity_id", params.entity_id);
        if (params.account_id) query.set("account_id", params.account_id);
        if (params.search) query.set("search", params.search);
        if (params.date_from) query.set("date_from", params.date_from);
        if (params.date_to) query.set("date_to", params.date_to);
        if (params.format) query.set("format", params.format);
        const qs = query.toString();
        return this.request(`/audit-logs${qs ? '?' + qs : ''}`);
    },

    getAuditSummary() {
        return this.request("/audit-logs/summary");
    },

    // Application
    getWatchlists(params = {}) {
        const query = new URLSearchParams();
        if (params.limit) query.set("limit", params.limit);
        if (params.offset !== undefined && params.offset !== null) query.set("offset", params.offset);
        if (params.search) query.set("search", params.search);
        if (params.status && params.status !== "ALL") query.set("status", params.status);
        const qs = query.toString();
        return this.request(`/watchlists${qs ? '?' + qs : ''}`);
    },


    addToWatchlist(accountId, reason = "Suspicious activity") {
        const query = new URLSearchParams();
        if (reason) query.set("reason", reason);
        const qs = query.toString();
        return this.request(`/watchlists/${encodeURIComponent(accountId)}${qs ? '?' + qs : ''}`, {
            method: "POST"
        });
    },

    getDecisions(params = {}) {
        const q = new URLSearchParams();
        if (params.limit !== undefined) q.append("limit", params.limit);
        if (params.offset !== undefined) q.append("offset", params.offset);
        const qs = q.toString();
        return this.request(qs ? `/decisions?${qs}` : "/decisions");
    },

    createDecision(accountId, decision, reason = "", alertId = null) {
        const q = new URLSearchParams({ decision, reason });
        if (alertId) q.append("alert_id", alertId);
        return this.request(`/decisions/${encodeURIComponent(accountId)}?${q.toString()}`, {
            method: "POST"
        });
    },

    // Regulatory Filings
    getFilings(params = {}) {
        const query = new URLSearchParams();
        if (params.limit) query.set("limit", params.limit);
        if (params.offset !== undefined && params.offset !== null) query.set("offset", params.offset);
        if (params.status && params.status !== "ALL") query.set("status", params.status);
        if (params.filing_type && params.filing_type !== "ALL") query.set("filing_type", params.filing_type);
        if (params.search) query.set("search", params.search);
        const qs = query.toString();
        return this.request(`/filings${qs ? '?' + qs : ''}`);
    },

    getFilingsSummary() {
        return this.request("/filings/summary");
    },

    getFiling(filingId) {
        return this.request(`/filings/${encodeURIComponent(filingId)}`);
    },

    createFiling(data) {
        return this.request("/filings", {
            method: "POST",
            body: JSON.stringify(data)
        });
    },

    submitFiling(filingId) {
        return this.request(`/filings/${encodeURIComponent(filingId)}/submit`, {
            method: "POST"
        });
    },

    acceptFiling(filingId) {
        return this.request(`/filings/${encodeURIComponent(filingId)}/accept`, {
            method: "POST"
        });
    },

    /**
     * @deprecated Legacy database rules endpoint. Use getInternalDetectionRules() for operational rules report.
     */
    getRules() {
        return this.request("/rules");
    },

    getNetworks() {
        return this.request("/networks");
    },

    getKPIs() {
        return this.request("/kpis");
    },

    // Transactions
    getTransactions(params = {}) {
        const query = new URLSearchParams();
        if (params.limit) query.set("limit", params.limit);
        if (params.offset !== undefined && params.offset !== null) query.set("offset", params.offset);
        const qs = query.toString();
        return this.request(`/transactions${qs ? '?' + qs : ''}`);
    },

    ingestTransaction(data) {
        return this.request("/transactions/ingest", {
            method: "POST",
            body: JSON.stringify(data)
        });
    },

    // Internal Operations
    getSystemHealth() {
        return this.request("/internal/system-health");
    },

    getMLHealth() {
        return this.request("/internal/ml-health");
    },

    getDetectionRules() {
        return this.request("/internal/detection-rules");
    },

    getGraphHealth(refresh = false) {
        return this.request(`/internal/graph-health${refresh ? '?refresh=true' : ''}`);
    },

    runGraphAnalysis() {
        return this.request("/internal/graph-health/analyze", {
            method: "POST"
        });
    },

    getSyntheticData(refresh = false) {
        return this.request(`/internal/synthetic-data${refresh ? '?refresh=true' : ''}`);
    },

    validateDataset() {
        return this.request("/internal/synthetic-data/validate", {
            method: "POST"
        });
    },

    getInternalAuditLogs(params = {}) {
        const query = new URLSearchParams();
        if (params.limit) query.set("limit", params.limit);
        if (params.offset !== undefined && params.offset !== null) query.set("offset", params.offset);
        if (params.action) query.set("action", params.action);
        if (params.entity_type) query.set("entity_type", params.entity_type);
        if (params.entity_id) query.set("entity_id", params.entity_id);
        if (params.account_id) query.set("account_id", params.account_id);
        if (params.category && params.category !== "ALL") query.set("category", params.category);
        if (params.search) query.set("search", params.search);
        if (params.date_from) query.set("date_from", params.date_from);
        if (params.date_to) query.set("date_to", params.date_to);
        const qs = query.toString();
        return this.request(`/internal/audit-logs${qs ? '?' + qs : ''}`);
    }
};

window.MuleGuardAPI = MuleGuardAPI;