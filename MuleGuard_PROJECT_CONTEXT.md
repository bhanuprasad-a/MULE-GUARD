# MuleGuard — Project Context & Implementation Brief

## 1. Purpose of this document

This document is the authoritative project context for the implementation agent.

The current codebase/UI has gone through several incorrect iterations. Do **not** assume the current pages, routes, dashboards, authentication flow, or navigation structure are correct. Treat the existing implementation as a prototype that must be audited and corrected.

The goal is to build a coherent academic prototype of **MuleGuard**, not a collection of unrelated mock dashboards.

---

# 2. Actual project goal

## Project title

**MuleGuard: Explainable Real-Time UPI Mule-Account and Fraud Network Detection System**

## One-sentence goal

MuleGuard detects suspicious money-movement behaviour and connected mule-account networks early, then explains the evidence so investigators can take appropriate action.

## Core problem

UPI/payment fraud is not necessarily visible in one transaction. Fraudsters can move money through multiple accounts so that each individual transaction looks normal.

The real problem is identifying when normal-looking transaction behaviour becomes a suspicious pattern over time and across connected accounts.

MuleGuard therefore combines:

- transaction behaviour
- time-based behaviour
- account history
- counterparties
- account-to-account relationships
- graph/network analysis
- machine-learning risk scoring
- explainability

The system should support investigation rather than simply declaring a person "fraudulent."

---

# 3. Source-of-truth project definition

The supplied project abstract states that MuleGuard is an AI-assisted fraud detection and investigation system for suspicious money movement and connected mule-account networks in UPI-like transactions.

It describes continuous analysis of:

- transaction frequency
- transaction velocity
- account history
- counterparties
- relationships between accounts

It also specifies:

- ML-based transaction-level risk analysis
- graph-based identification of suspicious money-flow patterns
- connected account networks
- an explainable layer that gives understandable reasons for risk assessments
- investigation alerts

The intended first version is a controlled virtual-bank environment using synthetic transaction data so known normal and mule-like behaviours can be tested and evaluated.

The academic objective is to determine whether combining behavioural and network information improves early identification of suspicious account activity while reducing false positives.

---

# 4. Important conceptual distinction

MuleGuard is **not** simply:

> "Enter a transaction -> output fraud/not fraud."

It is:

> transactions -> account behaviour over time -> suspicious behavioural patterns -> connected-account network -> risk assessment -> explanation -> investigation alert/action

A single unusual transaction must not automatically label an account as a mule.

A legitimate user can have:

- high-value transactions
- frequent transactions
- many counterparties

The system should look for repeated and connected patterns.

Example:

If an account suddenly receives money from 20–30 different accounts every day and quickly sends most of that money onward, the behaviour becomes materially different from ordinary use.

The system should show the investigator:

- what happened
- why it looks suspicious
- which accounts are connected
- how the behaviour changed over time
- what evidence contributed to the risk

---

# 5. Intended users and access model

There are exactly **three user access categories** in the prototype.

## A. Bank Investigator

Primary purpose:
- investigate suspicious accounts
- inspect cases
- inspect transactions
- inspect connected account networks
- inspect alerts
- view risk explanations
- trace money movement

This user needs an **Investigation Command Center**.

## B. Bank Compliance Officer

Primary purpose:
- review escalated/high-risk cases
- review compliance decisions
- review alerts
- record decisions
- review/report filing status
- perform senior oversight

This user needs a **Compliance Control Dashboard**.

## C. Internal Team

There is **ONE internal team login and ONE internal control dashboard**.

Do NOT create separate login pages or separate dashboards for:

- Internal Ops - AI / ML
- Internal Ops - Detection
- Internal Ops - System
- DevOps
- separate internal departments

Those were artifacts of previous incorrect iterations.

If internal responsibilities need to be represented, they can be represented as sections, permissions, status cards, tabs, or administrative controls inside the **single Internal Control Center**.

The internal team dashboard may contain:

- model/ML status
- detection-engine status
- data pipeline status
- graph/network engine status
- system health
- model evaluation
- detection configuration
- synthetic-data controls
- audit/system logs

But these are modules of ONE dashboard, not separate user dashboards.

---

# 6. Authentication requirements

There must be **one clean login page**.

The login page should provide:

- MuleGuard branding
- Email / Employee ID
- Password
- Institutional Role selector
- Remember me
- Forgot password
- Sign In button

The role selector should contain exactly:

1. Bank Investigator
2. Bank Compliance Officer
3. Internal Team

The login flow must actually work.

After successful login:

- Bank Investigator -> Investigator dashboard
- Bank Compliance Officer -> Compliance dashboard
- Internal Team -> Internal Control Center

Do NOT create a hidden developer authentication mechanism.

Do NOT create a "Developer Auth Terminal".

Do NOT expose development-only role bypasses in the normal user interface.

Do NOT make users choose from five development accounts through a modal.

Do NOT create a separate authentication UI for each role.

Role selection belongs to the single normal login experience.

For this academic prototype, credentials may be deterministic/mock credentials stored locally if there is no backend authentication system. The important requirement is that the complete demo flow works consistently.

---

# 7. Required application architecture

The implementation should be treated as one application with:

## Shared authentication

One login page.

## Three role destinations

### Investigator
`/frontend/bank/investigator/...`

### Compliance
`/frontend/bank/compliance/...`

### Internal
`/frontend/internal/...`

The exact route names may be changed if the existing project architecture uses a better structure. Do not preserve broken routes merely because they already exist.

Every navigation link must resolve to a real page.

There must be no dead links and no 404 pages during the intended demo flow.

---

# 8. Investigator experience

The investigator dashboard should be meaningfully different from the compliance dashboard.

Suggested primary navigation:

### Command Center
Overview of:

- transactions monitored
- high-risk transactions
- active investigations
- fraud loss prevented
- risk activity over time
- risk distribution

### Investigations
- active cases
- priority
- case status
- assigned investigator
- risk score
- investigation timeline

### Transactions
- transaction table
- filters
- amount
- timestamp
- sender
- receiver
- risk indicators
- suspicious-pattern indicators

### Entities / Accounts
- account profile
- risk score
- behaviour summary
- transaction history
- counterparties

### Fraud Networks
- graph visualization
- connected accounts
- money-flow direction
- suspicious clusters
- network risk

### Alerts
- alert queue
- severity
- reason
- affected account
- linked case

### Cases
- investigation case management
- evidence
- notes
- timeline
- status

### Risk Analytics
- behavioural risk
- transaction risk
- network risk
- trends

### Network Intelligence
- graph/network analysis

### Watchlists
- monitored accounts/entities

These are investigator-oriented capabilities.

---

# 9. Compliance Officer experience

The compliance officer must NOT simply receive a copy of the investigator dashboard.

The compliance dashboard should focus on oversight and decision-making.

Suggested navigation:

### Compliance Control Dashboard
- escalated cases
- high-risk alerts
- decisions logged
- reports filed

### Escalated Cases
- cases requiring compliance review
- risk score
- escalation reason
- investigator
- review action

### High-Risk Alerts
- unresolved alerts
- severity
- alert source
- account/entity
- review status

### Decisions / Review
- approve/escalate/reject/hold-style workflow appropriate for the prototype
- decision history
- reviewer
- timestamp
- rationale

### Reports
- reporting status
- generated/submitted reports
- filing status
- audit information

The compliance navigation should reflect compliance oversight, not investigation operations.

---

# 10. Internal Control Center

There must be ONE internal dashboard.

Suggested navigation:

### Internal Control Center
- overall system health
- detection engine status
- ML model status
- graph engine status
- data pipeline status
- active alerts/jobs
- model version
- last model evaluation

### Detection / Rules
- detection rules
- thresholds
- pattern definitions
- alert configuration

### ML / Models
- model version
- model metrics
- precision
- recall
- F1
- false-positive rate
- evaluation status
- feature information

### Network / Graph Engine
- graph processing status
- connected-component/network statistics
- processing jobs

### Data / Synthetic Environment
- synthetic transaction dataset status
- generation controls
- dataset statistics
- normal vs mule-like scenario counts

### System / Audit
- system events
- audit logs
- service health
- errors/warnings

Again: these are modules in ONE internal control center.

---

# 11. Required MuleGuard intelligence

The UI is only useful if it represents the actual project concept.

The prototype should have synthetic data that can demonstrate patterns such as:

## Normal behaviour

Examples:
- ordinary transfers
- salary-like credits
- routine payments
- normal recurring counterparties

## Mule-like behaviour

Examples:
- sudden increase in inbound counterparties
- many incoming accounts
- rapid onward transfers
- high incoming/outgoing velocity
- repeated pass-through behaviour
- short holding times
- fan-in / fan-out structures
- circular or layered money movement
- multiple accounts connected through suspicious transfers

The data should be deterministic enough that the demo is reproducible.

---

# 12. Risk scoring concept

The prototype should not pretend that an ML model is magically accurate.

Use a transparent risk architecture.

Conceptually:

`Behavioural Risk + Transaction Risk + Network Risk + History/Context -> Overall Risk`

Possible behavioural features:

- transaction frequency
- transaction velocity
- incoming transaction count
- outgoing transaction count
- unique counterparties
- inbound/outbound amount ratios
- rapid pass-through behaviour
- average holding time
- sudden behavioural change

Possible network features:

- degree
- inbound degree
- outbound degree
- fan-in
- fan-out
- connected component size
- suspicious neighbour count
- network concentration
- repeated paths

The UI must explain which factors contributed to a score.

Example:

> HIGH RISK — 82/100  
> Main contributing evidence:
> - 31 unique inbound counterparties in 24h
> - 89% of received funds transferred onward within 30 minutes
> - connected to 7 previously flagged accounts
> - behaviour increased sharply compared with previous 30 days

These numbers are synthetic demo values unless generated by the implemented model.

---

# 13. Explainability is a core feature

Every meaningful risk alert should answer:

### What happened?

Describe the transaction/behaviour.

### Why is it suspicious?

Show the behavioural/network evidence.

### Which accounts are connected?

Show the relevant graph relationships.

### How did behaviour change?

Compare recent activity with historical activity.

### What should the investigator inspect?

Point to transactions, accounts, networks, or cases.

Never present an unexplained "AI says fraud" result.

---

# 14. Graph/network component

A core differentiator of MuleGuard is network intelligence.

Represent:

- account as node
- transaction as directed edge
- amount as edge information
- timestamp as temporal information
- risk as node/edge metadata

The UI should allow an investigator to inspect a suspicious network.

Example:

`Victim -> Mule A -> Mule B -> Mule C -> Beneficiary/Fraudster`

The system is intended to make multi-account money movement easier to investigate.

---

# 15. Synthetic virtual-bank environment

The academic prototype should operate on synthetic data.

Do not claim that the prototype is connected to real UPI banking systems.

The environment should clearly communicate that the data is simulated/mock.

Recommended demo entities:

- accounts
- transactions
- counterparties
- alerts
- cases
- networks

Seed enough deterministic data to make the dashboards look realistic and make the investigation flow demonstrable.

---

# 16. End-to-end demo flow

The final application must support this complete flow:

1. Open MuleGuard.
2. See the single login page.
3. Select Bank Investigator.
4. Sign in.
5. Land on the Investigator Command Center.
6. Open a suspicious case.
7. Inspect account behaviour.
8. Inspect transaction evidence.
9. Open the connected fraud network.
10. View risk score and explanation.
11. Return/logout.
12. Select Bank Compliance Officer.
13. Sign in through the SAME login page.
14. Land on Compliance Control Dashboard.
15. Review an escalated case.
16. Record/view a compliance decision.
17. Return/logout.
18. Select Internal Team.
19. Sign in through the SAME login page.
20. Land on the ONE Internal Control Center.
21. Inspect model, detection, graph, data and system health.

Every step must work without manually changing URLs.

---

# 17. UI/UX direction

The existing visual direction can be retained where it is good:

- professional financial-security product
- MuleGuard branding
- dark navy/white/light-gray foundation
- lime/green brand accent
- restrained blue/red/green status indicators
- clean enterprise dashboard
- clear typography
- information-dense but readable

Use the supplied MuleGuard logo/symbol assets where appropriate.

Do not sacrifice functionality for visual effects.

Avoid:

- giant decorative logos occupying most of the screen
- unnecessary 3D animation
- decorative screens that hide the actual application
- fake developer terminals
- redundant dashboards
- excessive role duplication
- inaccessible buttons
- broken links

---

# 18. Current known problems that must be corrected

The previous implementation has demonstrated these failures:

1. Login page changed multiple times and became inconsistent.
2. A "Developer Auth Terminal" appeared. This is unwanted and must be removed.
3. The login page initially did not provide a clear working role-based sign-in flow.
4. Bank Investigator and Bank Compliance Officer pages were initially broken/404.
5. Some routes pointed to missing dashboard files.
6. Investigator and Compliance navigation became almost identical.
7. Three separate internal roles/dashboards were created even though only one internal control dashboard is required.
8. Some dashboard pages looked polished but did not represent distinct responsibilities.
9. Some pages were static visual mockups rather than a coherent working application.
10. Navigation links and routes were not consistently wired.
11. The project accumulated changes without first establishing a stable architecture.

Treat these as symptoms of architectural drift.

---

# 19. Non-negotiable implementation rules

## Rule 1 — Audit before editing

First inspect:

- complete directory structure
- frontend files
- backend files if present
- routing
- authentication
- existing data/model code
- assets
- scripts
- dependencies
- all current dashboard files

Do not blindly overwrite files.

## Rule 2 — Establish architecture before UI polishing

Determine:

- actual application entry point
- routing strategy
- authentication strategy
- shared components
- role model
- data model
- API/data flow
- static vs dynamic responsibilities

## Rule 3 — One login

Never create multiple role login pages.

## Rule 4 — Three access categories

Exactly:

- Bank Investigator
- Bank Compliance Officer
- Internal Team

## Rule 5 — One internal dashboard

Never create separate internal dashboards for AI/ML, Detection, System or DevOps.

## Rule 6 — Role-specific dashboards must be genuinely different

Investigator = investigation.

Compliance = oversight/review.

Internal = system/model/detection operations.

## Rule 7 — No developer bypass UI

No "Developer Auth Terminal" or similar feature in the normal product.

## Rule 8 — No broken routes

Every visible navigation item must point to a working page.

## Rule 9 — No fake completion

Do not say a feature works unless you actually test it.

## Rule 10 — Verify end-to-end

Run the application and test:

- login
- each role
- every primary navigation item
- logout
- direct route loading
- refresh behaviour
- missing-page/404 conditions
- console errors
- build/test commands

---

# 20. Implementation strategy for Antigravity

Use this sequence:

### Phase 1 — Exploration

Audit the existing repository and determine what is reusable and what must be removed/rebuilt.

### Phase 2 — Plan

Create a concrete implementation plan with:

- architecture
- routes
- files to modify/create/delete
- authentication flow
- role model
- dashboard structure
- data model
- testing strategy

### Phase 3 — Stabilize foundation

Fix routing, application entry points and authentication before polishing dashboards.

### Phase 4 — Build role experiences

Implement:

1. Investigator
2. Compliance
3. Internal Control Center

### Phase 5 — Build intelligence/data

Implement deterministic synthetic transaction data, risk scoring, network representation and explainability.

### Phase 6 — Connect UI

Make dashboards consume the same coherent data model.

### Phase 7 — Verification

Run build/tests and manually exercise the entire user flow.

### Phase 8 — Cleanup

Remove obsolete files/routes/components that conflict with the final architecture.

---

# 21. Definition of done

The project is complete only when:

- one login page exists
- role selection works
- Bank Investigator login works
- Bank Compliance Officer login works
- Internal Team login works
- investigator dashboard works
- compliance dashboard works
- internal control center works
- internal team has only ONE dashboard
- no developer-auth terminal exists
- no broken 404 dashboard routes remain
- investigator navigation is investigation-focused
- compliance navigation is compliance-focused
- internal navigation is operations/model/system-focused
- synthetic data is coherent
- risk scores have explainable evidence
- connected-account graph/network analysis is demonstrable
- cases/alerts/transactions/accounts are connected logically
- refresh/direct navigation does not break the application
- build/tests pass
- browser console has no material application errors
- the final application can be demonstrated from login to investigation to compliance review to internal monitoring

---

# 22. Important instruction to the implementation agent

Do not try to preserve every previous implementation decision.

The previous implementation is explicitly considered unreliable.

Preserve only useful assets/components/data that fit the architecture.

If the existing structure is fundamentally broken, simplify it and rebuild the affected parts cleanly.

Prioritize:

**correct architecture > working flow > meaningful functionality > visual polish**

The finished application should feel like one coherent MuleGuard product, not several unrelated HTML pages.

