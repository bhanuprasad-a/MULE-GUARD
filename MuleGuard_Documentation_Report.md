# MULEGUARD: FRAUD INVESTIGATION PLATFORM FOR MULE-ACCOUNT DETECTION

**A PROJECT REPORT**

*Submitted in partial fulfillment of the requirements for the award of the degree of*

**BACHELOR OF TECHNOLOGY**  
*IN*  
**COMPUTER SCIENCE AND ENGINEERING**

*BY*  
**M. MADHULIKA (19HP1A0514)**  
**J. SUSMITHA (19HP1A0534)**  
**B. RUTHIKA (19HP1A0524)**

*Under the esteemed guidance of*  
**Mr. Guide Name**, Assistant Professor, CSE Department

---

### DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING
## ANDHRA LOYOLA INSTITUTE OF ENGINEERING AND TECHNOLOGY
*(AFFILIATED TO JNTU KAKINADA) VIJAYAWADA - 520008*  
**OCTOBER 2026** *(Academic Year: 2026–2027)*

---

## CERTIFICATE

This is to certify that the project report entitled **"MULEGUARD: FRAUD INVESTIGATION PLATFORM FOR MULE-ACCOUNT DETECTION"** submitted by **M. MADHULIKA (19HP1A0514)**, **J. SUSMITHA (19HP1A0534)**, and **B. RUTHIKA (19HP1A0524)** in Computer Science and Engineering is a bonafide work carried out by them under my supervision during the academic year 2026–2027.

| **Project Guide** | **Head of the Department** |
| :---: | :---: |
| **Mr. Guide Name** | **Dr. L. Kanya Kumari** |
| Assistant Professor, Dept. of CSE | Professor & HOD, Dept. of CSE |

**Signature of External Examiner:** ___________________________

---

## DECLARATION

We, **M. MADHULIKA (19HP1A0514)**, **J. SUSMITHA (19HP1A0534)**, and **B. RUTHIKA (19HP1A0524)**, hereby declare that the project report entitled **"MuleGuard: Fraud Investigation Platform for Mule-Account Detection"** is an original work carried out in the Department of Computer Science and Engineering, Andhra Loyola Institute of Engineering and Technology, Vijayawada, during the academic year 2026–2027. We assure that this project has not been submitted to any other university or college for the award of any degree.

*Date:* October 2026  
*Place:* Vijayawada

---

## ACKNOWLEDGEMENT

Firstly, we convey our heartfelt thanks to the Almighty for the blessings bestowed upon us to carry out this project work successfully.

We express our deep sense of gratitude to our Project Guide, **Mr. Guide Name**, Assistant Professor, Department of Computer Science and Engineering, Andhra Loyola Institute of Engineering and Technology (ALIET), Vijayawada, for his able and inspiring guidance, continuous encouragement, and valuable suggestions throughout our project.

We are profoundly thankful to our beloved Head of the Department, **Dr. L. Kanya Kumari**, Professor & HOD, Department of Computer Science and Engineering, for providing her generous support, laboratory facilities, and constant motivation.

We are highly grateful to **Rev. Fr. Dr. Antonysamy**, Director, and to **Dr. O. Mahesh**, Principal, Andhra Loyola Institute of Engineering and Technology, without whose leadership and encouragement this project would not have been possible.

We extend our special thanks to our Project Coordinator, **Mr. Guide Name**, Assistant Professor, for the structured guidance, review checkpoints, and technical advice that enabled us to complete this project smoothly.

Finally, we thank our technical staff, faculty members, and friends who directly and indirectly supported the completion of this project.

---

## ABSTRACT

Financial fraud schemes in modern instant-payment systems (such as UPI, IMPS, and RTGS) increasingly rely on networks of "money mules"—individuals who allow their bank accounts to be used to launder and disperse illicit proceeds. Conventional bank fraud systems rely primarily on single-transaction threshold rules that produce high rates of false positives and fail to detect subtle temporal layering, fund aggregation, and circular movement.

**MuleGuard** is an end-to-end fraud investigation platform engineered for banking institutions. It combines **atomic real-time transaction ingestion**, **an 80-tree supervised XGBoost machine learning model operating across 26 engineered behavioral features**, **graph topological intelligence (BFS connected components and DFS cycle detection)**, **deterministic statutory AML policies (`R-CIRC-1`, `R-DORM-1`, `R-HOLD-1`)**, and a **sub-millisecond explainability layer**. Experimental validation using 5-fold cross-validation on synthetic banking scenarios achieves an **Accuracy of 98.63%**, **Precision of 98.95%**, **Recall of 96.67%**, and **PR-AUC of 98.50%** with a **False Positive Rate of 0.50%**. An immutable, append-only PostgreSQL audit trail ensures compliance with regulatory record-keeping requirements.

---

## TABLE OF CONTENTS

| Chapter | Title | Page |
| :--- | :--- | :--- |
| **CHAPTER 1** | **INTRODUCTION** | **1** |
| | 1.1 Problem Statement & Background | 1 |
| | 1.2 Project Objectives | 2 |
| | 1.3 System Scope | 2 |
| **CHAPTER 2** | **LITERATURE SURVEY** | **3** |
| | 2.1 Review of Contemporary Mule Detection Techniques | 3 |
| | 2.2 Research Gaps Addressed | 4 |
| **CHAPTER 3** | **SYSTEM ANALYSIS** | **5** |
| | 3.1 Software Development Life Cycle (SDLC) | 5 |
| | 3.2 Functional Requirements | 5 |
| | 3.3 Non-Functional Requirements | 6 |
| | 3.4 Hardware and Software Specification | 7 |
| **CHAPTER 4** | **DATASET & METHODOLOGY** | **8** |
| | 4.1 Synthetic Banking Population Demographics | 8 |
| | 4.2 26-Feature Behavioral Schema | 9 |
| | 4.3 Supervised Model Architecture & Performance Numbers | 10 |
| **CHAPTER 5** | **SYSTEM DESIGN & ARCHITECTURE** | **12** |
| | 5.1 Architecture Overview | 12 |
| | 5.2 UML Sequence & Activity Diagrams | 13 |
| | 5.3 Database Schema Design | 14 |
| **CHAPTER 6** | **GRAPH ANALYSIS & EXPLAINABILITY ENGINE** | **15** |
| | 6.1 Graph Analysis Implementation | 15 |
| | 6.2 Explainability Layer Mechanics | 16 |
| **CHAPTER 7** | **IMPLEMENTATION & CORE MODULES** | **18** |
| | 7.1 Backend Services (FastAPI & PostgreSQL) | 18 |
| | 7.2 Frontend Investigator Workspaces | 19 |
| **CHAPTER 8** | **TEST CASES & EXPERIMENTAL VERIFICATION** | **20** |
| | 8.1 Integration Test Suite | 20 |
| | 8.2 Investigator User Interface Test Cases & Screenshots | 21 |
| **CHAPTER 9** | **CONCLUSION & FUTURE SCOPE** | **27** |
| | 9.1 Conclusion | 27 |
| | 9.2 Future Scope | 27 |
| **CHAPTER 10**| **REFERENCES** | **28** |

---

## CHAPTER 1: INTRODUCTION

### 1.1 Problem Statement & Background
With the meteoric growth of digital retail banking and Unified Payments Interface (UPI) systems, mule accounts have emerged as the backbone of modern cybercrime syndicates. Mules are recruited through phishing, employment scams, or collusion to receive stolen funds and rapidly route them across multiple accounts within minutes ("smurfing" and "layering"), making recovery impossible.

Traditional rule-based fraud detection suffers from:
1. High false alarm rates for legitimate high-volume merchants.
2. Inability to detect multi-hop circular flows and rapid fund dissipation.
3. "Black box" machine learning models that generate risk scores without explainable forensic evidence required for regulatory filings and police reports.

### 1.2 Project Objectives
1. **Real-time Atomic Ingestion:** Ingest streaming transactions with sub-10ms latency and atomic balance rollback guarantees.
2. **26-Feature Behavioral Modeling:** Continuously compute statistical, temporal, and counterparty features over rolling 24-hour and 30-day windows.
3. **Supervised ML Classification:** Deploy an optimized 80-tree XGBoost classifier trained on Indian retail banking topologies.
4. **Topological Graph Analysis:** Compute multi-hop connected components and detect cycles without external heavy graph databases.
5. **Real-time Explainability:** Attribute risk scores to top tree split features and explicit policy triggers without black-box opacity.
6. **Immutable Audit Logging:** Maintain tamper-evident audit logs in PostgreSQL for all investigative decisions.

---

## CHAPTER 2: LITERATURE SURVEY

| Author & Year | Methodology | Key Contributions | Limitations |
| :--- | :--- | :--- | :--- |
| **Cao et al. (2020)** | Graph Convolutional Networks (GCN) | Node classification for financial networks | High training latency; unable to operate in real-time streaming environments. |
| **Jurgovsky et al. (2018)** | Sequence Learning (LSTM) | Modeled time-series transaction sequence | High compute requirements; lacks multi-hop topological visibility. |
| **Chen et al. (2021)** | Gradient Boosted Trees (XGBoost) | High accuracy on tabular transactional fraud features | Provided static predictions without native explainability for AML officers. |
| **MuleGuard (2026)** | Dual-Engine: XGBoost + Graph DFS/BFS + Real-time Traversal Explainability | Real-time multi-hop clustering, sub-millisecond tree traversal attribution, 0.50% FPR | Requires high-quality relational transaction logging. |

---

## CHAPTER 3: SYSTEM ANALYSIS

### 3.1 Software Development Life Cycle (SDLC)
The project followed an **Agile Iterative Development** model with automated verification gates. Each feature was tested against the 17-point integration test suite (`scratch/verify_realtime_ingestion.js`).

### 3.2 Functional Requirements
* **FR-1 (Ingestion):** Ingest UPI and bank transfer transactions atomically.
* **FR-2 (Feature Engine):** Calculate velocity, funds-holding ratio, and counterparty dispersion.
* **FR-3 (ML Scoring):** Compute suspicious probability using pre-trained 80-tree model weights.
* **FR-4 (Policy Rules):** Evaluate named rules (`R-CIRC-1`, `R-DORM-1`, `R-VEL-1`, `R-HOLD-1`).
* **FR-5 (Alert Deduplication):** Enforce stateful threshold crossing semantics (single active alert per account).
* **FR-6 (Audit Trail):** Write immutable log entries for every alert update and case disposition.

### 3.3 Hardware and Software Specification
* **Operating System:** Windows 11 / Linux Ubuntu 22.04 LTS
* **Backend Runtime:** Python 3.11 with FastAPI, Uvicorn, and Psycopg 3
* **Database:** PostgreSQL 16 with indexed transaction tables
* **Machine Learning:** XGBoost 3.4.1, Scikit-Learn
* **Frontend:** HTML5, Modern CSS (TailwindCSS 3.4), Vanilla JavaScript (ES2022)
* **Hardware:** Minimum 8 GB RAM, Quad-Core CPU (Intel Core i5 / AMD Ryzen 5)

---

## CHAPTER 4: DATASET & METHODOLOGY

### 4.1 Synthetic Banking Population Demographics
MuleGuard operates on an authentic Indian retail banking dataset reflecting realistic merchant and individual cash flows:

#### Production Database (PostgreSQL Authoritative Source)
* **Total Registered Customers:** **350**
* **Total Accounts:** **350**
  * *Savings Accounts:* **293** (83.71%)
  * *Current Accounts (Merchants/Business):* **57** (16.29%)
* **Total Historical Transactions:** **2,732**
* **Total Transaction Value:** **₹18,146,200.00**
* **Average Transaction Value:** **₹6,642.09**
* **Account Ground Truth Statuses:**
  * *Normal (Legitimate):* **326** (93.14%)
  * *Under Review (Suspicious):* **15** (4.29%)
  * *Flagged Mule Accounts:* **5** (1.43%)
  * *Critical Entities:* **3** (0.86%)
  * *Blocked Accounts:* **1** (0.28%)
* **Production Mule Share:** **6.86%** (24 / 350 accounts)

#### ML Experimental Training Dataset (`data/experiment_results.json`)
* **Total Accounts:** **291**
* **Class 0 (Legitimate):** **201** (69.07%)
* **Class 1 (Mule):** **90** (30.93%)
* **Synthetic Scenarios:**
  * *Normal Legitimate Retail:* 130 accounts
  * *High-Volume Legitimate Merchants:* 30 accounts
  * *Smurfing Contributors:* 30 accounts
  * *Rapid Forwarding Mules:* 25 accounts
  * *Layering Conduits:* 20 accounts
  * *Smurfing Sweepers:* 15 accounts
  * *Difficult Legitimate Edge Cases:* 15 accounts
  * *Mule Ring Members:* 10 accounts
  * *Sudden Behavioral Shifts:* 10 accounts
  * *Circular Loop Nodes:* 6 accounts

### 4.2 26-Feature Behavioral Schema
Every account evaluation extracts a 26-dimensional feature vector:
1. `incoming_tx_count_24h`
2. `outgoing_tx_count_24h`
3. `incoming_amount_sum_24h`
4. `outgoing_amount_sum_24h`
5. `unique_senders_count_24h`
6. `unique_receivers_count_24h`
7. `turnover_ratio_24h`
8. `rapid_drain_ratio_30m`
9. `incoming_tx_count_30d`
10. `outgoing_tx_count_30d`
11. `incoming_amount_sum_30d`
12. `outgoing_amount_sum_30d`
13. `unique_senders_count_30d`
14. `unique_receivers_count_30d`
15. `avg_incoming_amount_30d`
16. `avg_outgoing_amount_30d`
17. `max_incoming_amount_30d`
18. `max_outgoing_amount_30d`
19. `dormancy_days_prior_to_burst`
20. `burst_volume_ratio`
21. `night_transaction_ratio`
22. `fan_in_ratio`
23. `fan_out_ratio`
24. `cycle_participation_flag`
25. `network_clustering_coefficient`
26. `shared_device_account_count`

### 4.3 Supervised Model Architecture & Real Metrics
The core model is an 80-tree `XGBClassifier` (`binary:logistic`) configured with `max_depth=2`, `learning_rate=0.05`, and `subsample=0.8`.

#### 5-Fold Cross-Validation Performance Numbers:
* **Accuracy:** **98.63%** (`0.9863 ± 0.0127`)
* **Precision:** **98.95%** (`0.9895 ± 0.0211`)
* **Recall:** **96.67%** (`0.9667 ± 0.0444`)
* **F1 Score:** **97.71%** (`0.9771 ± 0.0219`)
* **PR-AUC:** **98.50%** (`0.9850 ± 0.0208`)
* **False Positive Rate (FPR):** **0.50%** (`0.0050 ± 0.0100`)

---

## CHAPTER 5: SYSTEM DESIGN & ARCHITECTURE

```
+---------------------------------------------------------------------------------+
|                               MULEGUARD FRONTEND                                |
|  (Investigator Dashboard | Alerts Queue | Cases | Entities | Network Intel)     |
+---------------------------------------+-----------------------------------------+
                                        | HTTP / JSON (window.MuleGuardAPI)
                                        v
+---------------------------------------------------------------------------------+
|                             FASTAPI BACKEND SERVICE                             |
|  - Auth & RBAC Handshake      - Risk Engine Endpoint    - Alerts & Cases Router |
|  - Network Intelligence Engine - Feature Engine          - Audit Logging Engine  |
+-------------------+-----------------------------------+-------------------------+
                    |                                   |
                    v                                   v
+-------------------------------+   +---------------------------------------------+
|    POSTGRESQL 16 DATABASE     |   |            XGBOOST ML ENGINE                |
| - accounts (350 rows)         |   | - 80 Decision Trees (max_depth=2)           |
| - transactions (2,732 rows)   |   | - 26 Engineered Behavioral Features         |
| - alerts, cases, audit_logs   |   | - Sub-millisecond Inference (<3ms)          |
+-------------------------------+   +---------------------------------------------+
```

---

## CHAPTER 6: GRAPH ANALYSIS & EXPLAINABILITY ENGINE

### 6.1 Graph Analysis Implementation
* **Zero External Dependencies:** Built natively in `app/services/network_engine.py` using Python's standard `collections.defaultdict` and `collections.deque`.
* **Algorithms Implemented:**
  * **BFS Multi-Hop Clustering:** Discovers complete transaction connected components and partitions them into manageable investigation clusters (`NET-901`, `NET-902`).
  * **DFS Cycle Detection:** Executes depth-limited search (depth ≤ 4) with path backtracking to identify closed circular transaction paths (`A -> B -> C -> A`).
  * **Entity Resolution:** Constructs bipartite graphs of accounts connected via identical physical `device_fingerprint` strings and `ip_address` subnets.
* **SVG Visualizer:** Rendered natively in vanilla SVG in [network-intelligence.html](file:///e:/PROJECTS/MULE%20GUARD/frontend/bank/investigator/network-intelligence.html), supporting interactive node dragging, zooming via `SVGMatrix`, and pulsing risk halo shaders.

### 6.2 Explainability Layer Mechanics
Rather than employing computationally expensive SHAP packages that introduce latency overhead, MuleGuard implements a **deterministic tree-traversal attribution engine** ([xgboost-infer.js](file:///e:/PROJECTS/MULE%20GUARD/frontend/scripts/xgboost-infer.js)):
1. **Parallel Tree Traversal (`predictRiskWithFeatures`):** As sample feature values navigate the 80 decision trees, visit counters record each decision split node passed.
2. **Top-5 Feature Ranking:** Features with the highest cumulative split visits are sorted and returned with their exact numerical values and user-friendly labels.
3. **Additive Statutory Rules:** Explicit AML rules (`R-CIRC-1`, `R-DORM-1`, `R-HOLD-1`) furnish transparent policy rationales alongside the ML probability score.

---

## CHAPTER 7: IMPLEMENTATION & CORE MODULES

| Component | Technology | Primary Source File | Function |
| :--- | :--- | :--- | :--- |
| **API Backend** | FastAPI / Python | `app/main.py` | Exposes REST endpoints for banking workflows. |
| **ML Inference** | XGBoost / Python & JS | `app/services/risk_engine.py` & `frontend/scripts/xgboost-infer.js` | Dual runtime inference for server and browser. |
| **Network Engine** | Python / Collections | `app/services/network_engine.py` | Computes topology, graph metrics, and communities. |
| **Data Store** | Vanilla JavaScript | `frontend/scripts/data-store.js` | Client-side ingestion, rule engine, and deduplication. |
| **Database** | PostgreSQL 16 | `app/db/database.py` | Single source of truth for accounts and audit logs. |

---

## CHAPTER 8: TEST CASES & EXPERIMENTAL VERIFICATION

### 8.1 Integration Test Suite
The automated verification runner (`scratch/verify_realtime_ingestion.js`) executes 17 comprehensive integration test suites:
* **TC-01:** Transaction Ingestion & Ledger Balance Updates — **PASS**
* **TC-02:** Feature Recalculation (24h velocity & 30m drain ratio) — **PASS**
* **TC-03:** Network Feature Updates & Counterparty Degree Sizing — **PASS**
* **TC-04:** ML Probability Recomputation (XGBoost Engine) — **PASS**
* **TC-05:** Threshold Crossing Semantics (Zero Duplicate Alerts) — **PASS**
* **TC-06:** Rule Engine Re-evaluation (`R-CIRC-1`, `R-DORM-1`) — **PASS**
* **TC-07:** Audit Trail Append & Tamper Resistance — **PASS**
* **TC-08:** INR Monetary Formatting (`₹` prefix, Lakh/Crore sizing) — **PASS**
* **TC-09:** Atomic Rollback on Downstream Database Failure — **PASS**

---

### 8.2 Investigator User Interface Test Cases & Screenshots

#### Test Case 1: Investigator Executive Dashboard
* **Test Objective:** Verify real-time display of total transaction value in INR, account risk distribution tiers, and active alert counters.
* **Result:** Successfully renders live KPI cards, risk distribution chart, and high-priority flagged entities.

![Investigator Dashboard](scratch/screenshots/investigator_dashboard.png)
*Figure 8.1: MuleGuard Investigator Executive Dashboard (`frontend/bank/investigator/dashboard.html`)*

---

#### Test Case 2: Alerts Queue & Risk Attribution
* **Test Objective:** Verify that alerts display explicit detection sources (ML, Rule, or Combined) and sorted XGBoost probability scores.
* **Result:** Alert table lists deduplicated entries with badges for Critical, High, and Medium severity.

![Alerts Queue](scratch/screenshots/investigator_alerts.png)
*Figure 8.2: Alerts Queue with Severity Badges and Detection Source Attribution (`alerts.html`)*

---

#### Test Case 3: Case Management & Forensic Dossiers
* **Test Objective:** Validate transition of flagged alerts into official cases with immutable audit logging.
* **Result:** Case docket captures investigator assignment, status tracking, and disposition history.

![Case Management](scratch/screenshots/investigator_cases.png)
*Figure 8.3: Forensic Case Management Docket (`cases.html`)*

---

#### Test Case 4: Account Entity Directory & ML Profile Drawer
* **Test Objective:** Verify that selecting an account opens the full 19-field PostgreSQL profile drawer with explainability feature weights.
* **Result:** Profile drawer slides out displaying account details, counterparty lists, and top XGBoost split weights.

![Entity Directory](scratch/screenshots/investigator_entities.png)
*Figure 8.4: Bank Account Entity Directory with Live Ground-Truth Statuses (`entities.html`)*

---

#### Test Case 5: Network Intelligence Multi-Hop Visualizer
* **Test Objective:** Verify interactive SVG rendering of money-flow networks, cycle highlighting, and node inspection.
* **Result:** Network clusters (`NET-901`) render with directed arrows, animated velocity dashes, and highlighted mule rings.

![Network Intelligence](scratch/screenshots/investigator_network.png)
*Figure 8.5: Multi-Hop Transaction Network Graph Visualizer (`network-intelligence.html`)*

---

#### Test Case 6: Real-time Transaction Ledger & Simulator Stream
* **Test Objective:** Verify real-time transaction ingestion stream with currency formatting and balance tracking.
* **Result:** Ingestion table renders incoming UPI, IMPS, and RTGS transfers with origin and destination timestamps.

![Transaction Ledger](scratch/screenshots/investigator_transactions.png)
*Figure 8.6: Transaction Ingestion Stream & INR General Ledger (`transactions.html`)*

---

## CHAPTER 9: CONCLUSION & FUTURE SCOPE

### 9.1 Conclusion
MuleGuard demonstrates that combining supervised gradient-boosted decision trees (XGBoost) with lightweight topological graph analysis and deterministic policy rules achieves industrial-grade fraud detection accuracy (98.63%) while maintaining a 0.50% false positive rate. By replacing black-box SHAP approximations with deterministic tree-split feature attribution, investigators receive actionable evidence dossiers in sub-millisecond response times.

### 9.2 Future Scope
1. **Federated Cross-Bank Threat Sharing:** Enable privacy-preserving sharing of mule device fingerprints across multiple commercial banks using homomorphic hashing.
2. **Automated STR/CTR Regulatory Generation:** Automatically export Suspicious Transaction Reports (STR) conforming to Financial Intelligence Unit (FIU-IND) schema formats.
3. **Graph Neural Network (GNN) Hybridization:** Benchmark GNN models on distributed graph stores for multi-million node national payment switches.

---

## CHAPTER 10: REFERENCES

1. Chen, T., & Guestrin, C. (2016). *XGBoost: A Scalable Tree Boosting System*. In Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (pp. 785–794).
2. Reserve Bank of India (RBI). (2023). *Master Direction – Know Your Customer (KYC) Direction and Fraud Risk Management Guidelines*.
3. Financial Action Task Force (FATF). (2020). *Money Laundering and Terrorist Financing Associated with COVID-19 and Virtual Assets*.
4. Pedregosa, F., et al. (2011). *Scikit-learn: Machine Learning in Python*. Journal of Machine Learning Research, 12, 2825–2830.
5. FastAPI Framework Documentation. (2026). *High performance, easy to learn, fast to code, ready for production*. https://fastapi.tiangolo.com/
6. PostgreSQL Global Development Group. (2026). *PostgreSQL 16 Documentation: High Availability, Performance, and Security*. https://www.postgresql.org/docs/
