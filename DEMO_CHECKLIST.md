# MuleGuard End-to-End Demo Checklist

This document details the exact live demo execution sequence, target data assets, API endpoints, and protected system components for the MuleGuard Fraud & Mule Account Detection Platform.

---

## Target Demo Case Profile

- **Target Account**: `ACC-982161`
- **XGBoost Risk Prediction**: `1` (Mule/Suspicious)
- **Risk Score**: `98.33` (Probability: 0.9833)
- **Severity**: `Critical`
- **Active Alert ID**: `ALT-FC7E53009A85`
- **Active Case ID**: `CASE-2398913C8184`

---

## Step-by-Step Navigation & Demo Sequence

1. **Sign In**:
   - URL: `http://localhost:8000/frontend/login.html`
   - Action: Select **Compliance Officer** or click **Demo Login**.

2. **Compliance Control Dashboard**:
   - URL: `http://localhost:8000/frontend/bank/compliance/dashboard.html`
   - Focus: Highlight live backend metrics.
   - API Endpoint: `GET /api/v1/kpis`

3. **Verify Live KPI Metrics**:
   - **Total Accounts**: `291`
   - **Suspicious Accounts**: `86`
   - **Total Transactions**: `1958`
   - **Open Alerts**: `1`
   - **Active Cases**: `1`

4. **Navigate to Accounts & Entities Intelligence**:
   - URL: `http://localhost:8000/frontend/bank/compliance/entities.html`
   - Action: Inspect the 291 PostgreSQL-backed accounts list.
   - API Endpoint: `GET /api/v1/accounts`

5. **Open High-Risk Account Details (`ACC-982161`)**:
   - Action: Click account `ACC-982161`.
   - API Endpoints:
     - `GET /api/v1/accounts/ACC-982161`
     - `GET /api/v1/accounts/ACC-982161/transactions`

6. **Demonstrate XGBoost Risk Model Score & Features**:
   - Action: Inspect the risk analysis breakdown.
   - Expected Output: Risk Score `98.33`, Prediction `1` (High-Risk Mule).
   - API Endpoint: `GET /api/v1/accounts/ACC-982161/risk`

7. **Navigate to Alerts Management**:
   - URL: `http://localhost:8000/frontend/bank/compliance/alerts.html`
   - Action: View system-generated alerts queue.
   - API Endpoint: `GET /api/v1/alerts`

8. **Inspect Critical Alert (`ALT-FC7E53009A85`)**:
   - Action: Click alert `ALT-FC7E53009A85` targeting `ACC-982161`.
   - Details: Severity `Critical`, Risk Score `98.33`, Status `Open`.
   - API Endpoints:
     - `GET /api/v1/alerts/ALT-FC7E53009A85`
     - `PATCH /api/v1/alerts/ALT-FC7E53009A85/acknowledge`

9. **Escalate to Case Investigation**:
   - Action: Click **Create / View Case** for alert `ALT-FC7E53009A85`.
   - API Endpoint: `POST /api/v1/cases/from-alert/ALT-FC7E53009A85`

10. **Inspect Investigation Case (`CASE-2398913C8184`)**:
    - URL: `http://localhost:8000/frontend/bank/compliance/cases.html`
    - Action: Review priority `Critical`, status `Open`, and workflow action buttons (**Investigate**, **Escalate**, **Resolve**).
    - API Endpoints:
      - `GET /api/v1/cases/CASE-2398913C8184`
      - `PATCH /api/v1/cases/CASE-2398913C8184/investigate`

11. **Review Central Audit Trail**:
    - Action: Inspect audit log events.
    - Expected Logs: `ALERT_CREATED`, `CASE_CREATED`, `TRANSACTION_INGESTED`.
    - API Endpoint: `GET /api/v1/audit-logs`

12. **Review Account Transaction History**:
    - URL: `http://localhost:8000/frontend/bank/compliance/transactions.html`
    - Action: View inbound and outbound transaction ledger for `ACC-982161`.
    - API Endpoint: `GET /api/v1/accounts/ACC-982161/transactions`

13. **Demonstrate Real-Time Transaction Ingestion**:
    - Action: Trigger simulator play/pause button or execute `POST /api/v1/transactions/ingest`.
    - Expected Output: Immediate balance update, transaction record insertion, and audit trail update.
    - API Endpoint: `POST /api/v1/transactions/ingest`

---

## Key Backend API Architecture Summary

| UI Screen / Feature | Primary API Endpoint | Response Data |
| :--- | :--- | :--- |
| Dashboard KPIs | `GET /api/v1/kpis` | `total_accounts`, `suspicious_accounts`, `open_alerts`, `active_cases` |
| Accounts List | `GET /api/v1/accounts` | Array of 291 PostgreSQL account objects |
| Account Risk | `GET /api/v1/accounts/{id}/risk` | `risk_score`, `risk_probability`, `prediction`, XGBoost metadata |
| Alerts Queue | `GET /api/v1/alerts` | Array of alert records (`ALT-...`) |
| Cases Queue | `GET /api/v1/cases` | Array of case records (`CASE-...`) |
| Audit Trail | `GET /api/v1/audit-logs` | Chronological audit events (`ALERT_CREATED`, `CASE_CREATED`) |
| Transaction Ingest | `POST /api/v1/transactions/ingest` | Atomic balance update & transaction receipt |

---

## DO NOT TOUCH BEFORE DEMO

The following core files contain protected model weights, 26-feature pipeline calculations, seed data, and CI verification tests. **Do not modify or delete these files**:

1. `app/ml_baseline.py`
2. `data/muleguard_postgres_model.json`
3. `data/best_muleguard_model.json`
4. `frontend/scripts/data-store.js`
5. `frontend/scripts/synthetic_db_expanded.js`
6. `frontend/scripts/best_muleguard_model.js`
7. `frontend/scripts/xgboost-infer.js`
8. `scratch/verify_realtime_ingestion.js`
