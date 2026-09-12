# MuleGuard — Agent Instructions

## Project Overview
Fraud investigation platform for detecting mule-account behavior using ML, graph analysis, and investigation workflows. Student project with startup-grade engineering.

## Commands
- **Build CSS**: `npm run build:css` (compiles `frontend/input.css` → `frontend/style.css` via Tailwind)
- **Run verification tests**: `node scratch/verify_realtime_ingestion.js` (loads browser JS in Node, runs 17 integration tests)

## Architecture
```
frontend/
├── scripts/          # Core logic (data-store, ML inference, simulator, synthetic DB)
├── bank/             # HTML pages (investigator/, compliance/)
├── internal/         # Internal dashboard
├── input.css         # Tailwind source
└── style.css         # Compiled output (gitignored)
data/                 # Model JSON, synthetic DB, experiment results
scratch/              # Verification runner + Python migration scripts
```

## Key Files
- `frontend/scripts/data-store.js` — Central state, ingestion, alerts, rules, audit logs
- `frontend/scripts/xgboost-infer.js` — XGBoost model inference wrapper
- `frontend/scripts/best_muleguard_model.js` — Embedded model weights
- `frontend/scripts/transaction-simulator.js` — Real-time transaction generator
- `frontend/scripts/synthetic_db_expanded.js` — Seed data
- `tailwind.config.js` — Design system tokens (colors, spacing, typography)

## Conventions
- All monetary values in INR (₹ prefix), never USD/$
- Transaction ingestion is atomic: downstream failures roll back ledger & balances
- ML threshold crossing (below→above) creates exactly one alert; staying above creates no duplicates
- Rules engine evaluates on every ingestion; `R-CIRC-1` and `R-DORM-1` are additive named rules
- Authentication guard (`scripts/auth-guard.js`) must be included in all HTML pages

## Verification
Run `node scratch/verify_realtime_ingestion.js` before committing. Tests cover:
- Transaction ingestion, feature recalculation, network features
- ML probability recalculation, threshold crossing semantics
- Rule re-evaluation (ML-only, Rule-only, Combined)
- Audit trail, INR formatting, simulator lifecycle
- Atomic rollback, balance protection, deterministic reset
- Temporal windowing (24h, 30m holding), R-CIRC-1, R-DORM-1

## No linting/typecheck/test configs present — verification runner is the CI gate.