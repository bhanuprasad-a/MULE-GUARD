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
    getAccounts() {
        return this.request("/accounts");
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
    getAlerts() {
        return this.request("/alerts");
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
    getCases() {
        return this.request("/cases");
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

    // Audit
    getAuditLogs() {
        return this.request("/audit-logs");
    },

    // Application
    getWatchlists() {
        return this.request("/watchlists");
    },

    getDecisions() {
        return this.request("/decisions");
    },

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
    getTransactions() {
        return this.request("/transactions");
    },

    ingestTransaction(data) {
        return this.request("/transactions/ingest", {
            method: "POST",
            body: JSON.stringify(data)
        });
    }
};

window.MuleGuardAPI = MuleGuardAPI;