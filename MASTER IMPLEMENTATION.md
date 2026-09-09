# MULEGUARD — MASTER IMPLEMENTATION SPECIFICATION
## Phases 2–9

> PHASE 1 IS COMPLETE.
> The current UI/page structure is approved and FROZEN.
> From this point onward, focus on functionality, data, intelligence,
> integration, workflow, ML, and testing.

---

# 1. PROJECT GOAL

MuleGuard is an AI-assisted financial fraud intelligence and investigation platform designed to detect suspicious money movement and connected mule-account networks.

The system must help investigators answer:

- Which accounts or transactions are suspicious?
- Why are they suspicious?
- What behavioural patterns caused the risk?
- Which accounts/entities are connected?
- How did money move through the network?
- What evidence supports the risk score?
- What should an investigator investigate next?
- Which cases require compliance review?

MuleGuard is NOT a generic banking dashboard.

Its core value is:

TRANSACTION INTELLIGENCE
+
BEHAVIOURAL ANALYSIS
+
SUSPICIOUS ACTIVITY DETECTION
+
RISK SCORING
+
NETWORK/GRAPH ANALYSIS
+
EXPLAINABILITY
+
INVESTIGATION WORKFLOW

---

# 2. PHASE 1 STATUS — UI FREEZE

Phase 1 is DONE.

The current approved UI must NOT be unnecessarily redesigned.

Do not:

- redesign the login page
- redesign approved dashboards
- create additional dashboards just for appearance
- create duplicate pages
- replace working UI without a functional reason

From this point onward, prioritize:

- backend
- data
- APIs
- authentication/authorization
- detection
- risk scoring
- graph intelligence
- investigation workflow
- compliance workflow
- ML
- testing

---

# 3. ACCESS ARCHITECTURE

There are EXACTLY THREE access categories:

1. Bank Investigator
2. Bank Compliance Officer
3. Internal Team

There must be:

- ONE login page
- role selection on the login page
- role-aware authentication
- role-based authorization
- role-based routing
- one shared application/data layer

There must NOT be:

- Developer Auth Terminal
- developer bypass UI
- DevOps role
- DevOps dashboard
- separate login pages
- separate AI/ML dashboard
- separate Detection dashboard
- separate System dashboard
- multiple Internal Team dashboards

The Internal Team gets:

# ONE INTERNAL CONTROL CENTER

The Internal Control Center may contain modules/sections for:

- System Health
- Detection / Rules
- ML / Models
- Network / Graph Engine
- Synthetic Data
- Audit / System Information

These are modules inside ONE control center.

They are NOT separate dashboards.

---

# 4. PHASE 2 — SYNTHETIC DATA FOUNDATION

## Objective

Build a realistic and coherent synthetic financial dataset that powers the entire MuleGuard system.

Do NOT create unrelated random numbers for individual dashboard cards.

All important parts of the application must use the same underlying data.

The same account shown in:

- dashboard
- investigation
- transactions
- risk analysis
- network graph
- alerts
- cases
- compliance

must refer to the same underlying entity.

---

## 4.1 ACCOUNT DATA

Create realistic synthetic account records containing appropriate fields such as:

- account_id
- customer_id
- bank/institution
- account_type
- account_open_date
- account_age
- KYC status
- location
- occupation/business category
- baseline risk
- current risk

---

## 4.2 CUSTOMER/PERSON DATA

Create synthetic customer/person records.

Include appropriate fields such as:

- customer_id
- synthetic name
- location
- occupation/category
- KYC status
- linked accounts

Do NOT use real people's personal information.

---

## 4.3 TRANSACTION DATA

Create realistic transaction records containing:

- transaction_id
- timestamp
- sender_account
- receiver_account
- amount
- transaction_type
- channel
- location
- status
- category/reference

Transactions must contain realistic temporal behaviour.

---

## 4.4 ENTITY DATA

Model entities such as:

- Person
- Business
- Merchant
- Phone
- Email
- Device
- IP Address
- Address
- Bank Account

---

## 4.5 RELATIONSHIP DATA

Represent relationships such as:

Person → Account

Account → Account

Account → Phone

Account → Device

Account → IP

Person → Business

Account → Business

Person → Person where appropriate

---

## 4.6 REQUIRED SYNTHETIC SCENARIOS

The dataset must contain both legitimate and suspicious behaviour.

Include examples of:

- normal accounts
- legitimate high-volume accounts
- dormant accounts becoming active
- rapid incoming/outgoing transactions
- many-to-one aggregation
- one-to-many distribution
- pass-through accounts
- circular money movement
- suspicious account clusters
- shared device patterns
- shared IP patterns
- shared phone patterns
- suspicious transaction bursts
- unusual transaction amounts
- connected mule-account networks

The dataset should be reproducible/deterministic where practical so testing can consistently reproduce results.

---

# 5. PHASE 3 — DETECTION ENGINE

## Objective

Build a transparent rule-based suspicious-activity detection engine.

Do NOT start by hiding all intelligence inside ML.

The rule engine provides the baseline evidence that investigators can understand.

---

## REQUIRED INITIAL RULES

### Rule 1 — Rapid Fund Movement

Detect funds being received and transferred out unusually quickly.

### Rule 2 — Many-to-One Aggregation

Detect many different accounts sending money into one account within a suspicious time window.

### Rule 3 — One-to-Many Distribution

Detect one account rapidly distributing funds to many other accounts.

### Rule 4 — Circular Money Flow

Detect money moving through a cycle of connected accounts.

### Rule 5 — Dormant Account Activation

Detect previously inactive accounts suddenly becoming highly active.

### Rule 6 — Unusual Transaction Amount

Detect transactions that significantly differ from the account's historical behaviour.

### Rule 7 — Shared Identifiers

Detect suspicious accounts sharing:

- device
- IP
- phone
- email
- address
- other relevant synthetic identifiers

### Rule 8 — Pass-Through Behaviour

Detect accounts receiving funds and forwarding a significant proportion shortly afterward.

---

# 6. DETECTION OUTPUT

Every detection must produce structured evidence.

Example:

Account: AC-10482

Risk Level: HIGH

Evidence:

- 17 incoming accounts in 24 hours
- 14 outgoing transfers within 30 minutes
- 3 connected high-risk accounts
- shared device with suspicious accounts
- rapid pass-through behaviour

Do NOT display arbitrary risk labels without evidence.

Every alert should have:

- affected account/entity
- detection rule
- timestamp/time window
- relevant transactions
- evidence
- severity
- risk contribution

---

# 7. PHASE 4 — RISK SCORING

## Objective

Create a coherent risk-scoring system.

The exact implementation should be determined after inspecting the current architecture.

The risk score must be:

- consistent
- explainable
- bounded
- evidence-based
- reproducible where appropriate

The conceptual risk components can include:

- transaction/velocity risk
- behavioural anomaly risk
- rule-based risk
- network risk
- later ML risk

Do NOT invent arbitrary numbers just to populate cards.

---

## EVERY RISK SCORE MUST ANSWER:

1. What is the score?
2. What risk level does it represent?
3. Which factors contributed?
4. What evidence supports each factor?
5. Which transactions/accounts/entities are involved?

Example:

RISK SCORE: 91 / 100

RISK LEVEL: CRITICAL

Reasons:

1. unusually high transaction velocity
2. rapid pass-through behaviour
3. multiple connected high-risk accounts
4. shared device identifier
5. significant deviation from historical behaviour

---

# 8. PHASE 5 — NETWORK / GRAPH INTELLIGENCE

## Objective

Build the connected-account intelligence layer.

MuleGuard must be able to represent relationships between:

- accounts
- customers
- businesses
- transactions
- devices
- IP addresses
- phones
- other relevant entities

---

## REQUIRED GRAPH CAPABILITIES

The investigator should be able to:

- select an account/entity
- see direct connections
- inspect second-degree connections
- identify suspicious clusters
- inspect money-flow direction
- inspect transaction amounts
- inspect timestamps
- inspect relationship types
- identify shared identifiers
- trace relevant transaction paths

Example:

Account A
↓
Account B
↓
Account C
↓
Account D

The system should explain why the network is suspicious.

The graph MUST be generated from the same underlying dataset used by:

- transactions
- detection
- risk scoring
- investigations

Do NOT create a decorative graph disconnected from the actual data.

---

# 9. PHASE 6 — END-TO-END INVESTIGATION WORKFLOW

This is the most important user-facing workflow.

---

## INVESTIGATOR FLOW

Dashboard

↓

Investigations

↓

Select suspicious account/case

↓

Account Details

↓

Transaction History

↓

Behaviour Analysis

↓

Risk Score

↓

Risk Explanation

↓

Network Graph

↓

Evidence

↓

Create / Update Case

↓

Investigator Action

---

## COMPLIANCE FLOW

Compliance Dashboard

↓

Escalated Cases

↓

Case Details

↓

Evidence

↓

Risk Information

↓

Network Information

↓

Review

↓

Decision

↓

Audit / History

---

# 10. SHARED STATE REQUIREMENT

This is mandatory.

The Investigator and Compliance Officer MUST work with the same underlying data and case state.

Example:

Investigator:

Creates case for AC-10482

↓

Case appears in shared case system

↓

Compliance Officer logs in

↓

Compliance sees AC-10482

↓

Compliance reviews evidence

↓

Compliance changes case status

↓

Investigator can see the appropriate updated state

Do NOT create isolated mock data for each dashboard.

---

# 11. PHASE 7 — MACHINE LEARNING

ML must be implemented AFTER the synthetic data pipeline and rule-based detection system are working.

## Objective

Use ML to identify suspicious behavioural patterns that complement explicit detection rules.

First inspect the existing data and architecture.

Choose a model appropriate for the actual data.

Possible approaches may include:

- anomaly detection
- classification
- clustering
- behavioural scoring

Do NOT add ML merely because the project needs an "AI" label.

---

## REQUIRED ML PIPELINE

Synthetic Data

↓

Feature Engineering

↓

ML Model

↓

Prediction / Risk Contribution

↓

Explanation

↓

Investigation Interface

---

## IMPORTANT

ML must integrate into the actual MuleGuard risk/investigation pipeline.

Do NOT create a fake ML dashboard that has no effect on investigations.

The ONE Internal Control Center may expose:

- model status
- model metrics
- feature information
- model performance
- feature importance
- model configuration where appropriate

But the ML output must connect to the actual risk/investigation system.

---

# 12. PHASE 8 — EXPLAINABILITY

Explainability is a CORE requirement.

Do NOT simply show:

"Fraud probability = 0.94"

Instead show understandable evidence.

Example:

## WHY WAS THIS ACCOUNT FLAGGED?

- unusually high transaction velocity
- abnormal transaction amount
- rapid movement of received funds
- connection to multiple flagged accounts
- shared device with another suspicious account
- unusual deviation from historical behaviour

Where ML is used, provide meaningful model explanations/features appropriate to the selected model.

Every explanation shown to an investigator must correspond to actual computed data.

NO fabricated explanations.

---

# 13. PHASE 9 — COMPLETE TESTING

Before declaring MuleGuard complete, test it as a real user would.

---

## AUTHENTICATION

Verify:

- Investigator login
- Compliance Officer login
- Internal Team login
- invalid credentials
- role restrictions
- correct routing
- logout
- session handling

---

## INVESTIGATOR

Verify:

- dashboard loads
- investigations load
- suspicious accounts are actual dataset records
- transaction details work
- behavioural analysis works
- risk score is computed
- risk explanation is displayed
- network graph uses real relationships
- evidence is visible
- case creation works
- case update works

---

## COMPLIANCE

Verify:

- dashboard loads
- escalated cases appear
- case details work
- evidence is visible
- risk/network information is available
- decisions work
- case status persists
- audit/history works where implemented

---

## INTERNAL TEAM

Verify ONE Internal Control Center.

It must contain working modules for:

- system health
- detection/rules
- ML/model information
- network/graph
- synthetic data
- audit/system information

---

# 14. TECHNICAL VERIFICATION

Find and fix ALL:

- 404 errors
- broken routes
- dead buttons
- dead links
- JavaScript errors
- API failures
- authentication problems
- authorization problems
- incorrect redirects
- disconnected data
- duplicate mock data
- stale hardcoded values
- missing assets
- broken navigation
- inconsistent role handling

Do NOT claim a feature works merely because its page renders.

Actually exercise the workflow.

---

# 15. ONE SHARED DATA FOUNDATION

This is a HARD REQUIREMENT.

The following must come from one coherent data layer:

- dashboard metrics
- accounts
- customers
- transactions
- alerts
- risk scores
- graph relationships
- investigations
- cases
- compliance reviews
- ML outputs
- audit/history

If the same account appears in multiple places, its important attributes must remain consistent.

---

# 16. IMPLEMENTATION PRINCIPLES

## INSPECT BEFORE MODIFYING

First inspect:

- repository structure
- frontend
- backend
- APIs
- data files
- authentication
- authorization
- routes
- dependencies
- existing components
- existing working functionality

Reuse working code where appropriate.

Do not blindly replace the existing application.

---

# 17. PLAN BEFORE IMPLEMENTATION

Before making major implementation changes:

Create:

IMPLEMENTATION_PLAN.md

The implementation plan must include:

- current architecture
- current implementation status
- completed functionality
- missing functionality
- architecture gaps
- proposed architecture
- data model
- API architecture
- authentication architecture
- detection architecture
- risk architecture
- graph architecture
- ML architecture
- investigation workflow
- compliance workflow
- testing strategy
- implementation order
- acceptance criteria

The plan must be based on the ACTUAL repository.

Do not create a generic theoretical plan.

---

# 18. EXECUTION METHOD

After creating IMPLEMENTATION_PLAN.md:

Execute it step by step.

For every major milestone:

1. implement the milestone
2. run the application
3. test the relevant workflow
4. inspect browser errors
5. inspect API/backend errors
6. fix discovered problems
7. verify again
8. move to the next milestone

Do not leave known errors for the end if they can be fixed immediately.

---

# 19. DO NOT OVER-ENGINEER

This is an academic/project demonstration system.

Prioritize:

- correctness
- reliability
- understandable architecture
- meaningful functionality
- realistic data
- explainability
- strong demonstration workflow

Do NOT introduce unnecessary production-scale infrastructure simply to make the project look complicated.

---

# 20. DO NOT FABRICATE FUNCTIONALITY

A button must perform a real action.

A chart must represent real data.

A risk score must have real evidence.

A graph must represent real relationships.

A case must persist.

A role must actually control access.

An alert must correspond to a real detection.

An ML result must come from the implemented model.

Do not use fake UI behaviour to make the application appear functional.

---

# 21. ABSOLUTE EXCLUSIONS

Never reintroduce the previous architectural mistakes.

DO NOT create:

- Developer Auth Terminal
- DevOps role
- DevOps dashboard
- Internal AI/ML dashboard
- Internal Detection dashboard
- Internal System dashboard
- multiple Internal Team dashboards
- duplicate login pages
- duplicate dashboards
- disconnected mock dashboards
- decorative pages with no functionality
- fake navigation

There are exactly:

3 ROLES

1 LOGIN

1 INTERNAL CONTROL CENTER

1 SHARED DATA FOUNDATION

1 COHERENT INVESTIGATION WORKFLOW

---

# 22. FINAL DEMONSTRATION

The final system must allow an evaluator to perform this complete demonstration:

1. Open MuleGuard.
2. Sign in as Bank Investigator.
3. View suspicious activity.
4. Open a suspicious account.
5. Inspect its transactions.
6. Inspect behavioural analysis.
7. See the risk score.
8. Understand why the account was flagged.
9. Open the connected-account network.
10. Inspect suspicious relationships.
11. Create/update an investigation case.
12. Sign out.
13. Sign in as Bank Compliance Officer.
14. Find the relevant case.
15. Review the evidence.
16. Review risk/network information.
17. Make a compliance decision.
18. Verify that the case state persists.
19. Sign out.
20. Sign in as Internal Team.
21. Open the ONE Internal Control Center.
22. Inspect detection information.
23. Inspect ML/model information.
24. Inspect network information.
25. Inspect synthetic data/system information.
26. Verify that everything is based on the same coherent dataset.

The entire demonstration must work without manually editing files or database records.

---

# 23. FINAL MULEGUARD ARCHITECTURE

The final system should conceptually operate as:

Transactions
        ↓
Account Behaviour
        ↓
Suspicious Pattern Detection
        ↓
Risk Scoring
        ↓
Network Analysis
        ↓
Explainability
        ↓
Alert / Investigation
        ↓
Investigator Action
        ↓
Compliance Review
        ↓
Decision / Audit

ML should be integrated into the intelligence/risk pipeline after the baseline detection system is working.

---

# 24. ANTIGRAVITY MASTER INSTRUCTION

When you receive this document:

DO NOT immediately modify random files.

FIRST:

## STEP 1 — EXPLORE

Inspect the complete repository.

Understand:

- what exists
- what works
- what is broken
- what can be reused
- what is missing

## STEP 2 — CREATE THE PLAN

Create:

IMPLEMENTATION_PLAN.md

The plan must specifically map Phases 2–9 to the current repository.

## STEP 3 — EXECUTE

Execute the implementation plan completely and sequentially.

## STEP 4 — VERIFY

Run the application and test actual browser workflows.

## STEP 5 — FIX

Fix all discovered errors.

## STEP 6 — CONTINUE

Do not stop after one successful page.

Continue until all applicable phases are implemented.

## STEP 7 — FINAL AUDIT

Compare the finished project against this specification.

Verify:

- authentication
- authorization
- data
- detection
- risk scoring
- graph
- investigation
- compliance
- ML
- explainability
- shared state
- Internal Control Center
- routing
- APIs
- browser workflows
- technical errors

Finally report:

- what was implemented
- what was reused
- what was changed
- what was tested
- which routes were verified
- which workflows were verified
- remaining limitations, if any

DO NOT stop after writing IMPLEMENTATION_PLAN.md.

Create the plan FIRST, then execute it COMPLETELY, test the result, fix the problems, and perform the final audit.

---

# FINAL OBJECTIVE

Do not measure the success of MuleGuard by the number of pages created.

Measure it by whether an evaluator can follow a convincing, working fraud-investigation story:

Suspicious Transactions
        ↓
Suspicious Behaviour
        ↓
Detection
        ↓
Risk Score
        ↓
Why Flagged?
        ↓
Connected Mule Network
        ↓
Investigation
        ↓
Case
        ↓
Compliance Review
        ↓
Decision

Build that system completely and coherently using the approved Phase 1 UI.