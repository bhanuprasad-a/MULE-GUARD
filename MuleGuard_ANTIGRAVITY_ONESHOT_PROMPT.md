You are the lead engineer responsible for rebuilding the MuleGuard academic prototype in the current workspace.

I am giving you a project-context document named `MuleGuard_PROJECT_CONTEXT.md`. Read it completely before making changes. Also inspect the entire existing repository yourself. The current implementation is the result of several failed iterations, so do NOT assume the current routes, login system, dashboards, or navigation are correct.

PROJECT PURPOSE:
MuleGuard is an academic AI-assisted fraud detection and investigation system for UPI-like synthetic transactions. Its purpose is to detect suspicious money-movement behaviour and connected mule-account networks early, then explain the evidence so investigators can take appropriate action. It should combine transaction behaviour, time/history, account relationships, ML-style risk scoring, graph/network analysis, and explainability. It is NOT simply a single-transaction fraud classifier.

IMPORTANT PRODUCT MODEL:
There is exactly ONE application and ONE login page.

There are exactly THREE access categories:
1. Bank Investigator
2. Bank Compliance Officer
3. Internal Team

After login:
- Bank Investigator -> Investigator Command Center
- Bank Compliance Officer -> Compliance Control Dashboard
- Internal Team -> ONE Internal Control Center

There must NOT be:
- a Developer Auth Terminal
- developer-only role bypass UI
- separate login pages per role
- separate Internal Ops AI/ML dashboard
- separate Internal Ops Detection dashboard
- separate Internal Ops System dashboard
- separate DevOps dashboard
- three internal dashboards

Internal ML, detection, graph, data and system functions are modules inside ONE Internal Control Center.

ROLE RESPONSIBILITIES:
Bank Investigator:
investigations, suspicious accounts, transactions, cases, alerts, fraud networks, risk analytics, network intelligence, watchlists and evidence/explanations.

Bank Compliance Officer:
escalated cases, high-risk alerts, compliance decisions/review, reports and regulatory/audit oversight.

Internal Team:
model status/metrics, detection configuration, graph engine status, synthetic data environment, system health, audit logs and operational controls — all inside ONE dashboard.

AUTHENTICATION:
Create/fix ONE clean login page containing:
- Email / Employee ID
- Password
- Institutional Role
- Remember me
- Forgot password
- Sign In

Role options must be exactly:
- Bank Investigator
- Bank Compliance Officer
- Internal Team

The role flow must actually authenticate/navigate correctly in the academic prototype. If there is no backend auth, deterministic local/mock credentials are acceptable, but the entire demo must work consistently.

CURRENT FAILURES TO FIX:
- broken/404 bank dashboards
- inconsistent login
- Developer Auth Terminal
- role flow not reliably connected
- duplicate/identical left-side navigation between Investigator and Compliance
- three unnecessary internal dashboards
- pages that look polished but are disconnected/static
- dead navigation links
- routes that only work by manually typing URLs

CORE INTELLIGENCE:
Use deterministic synthetic virtual-bank data. Include normal behaviour and mule-like behaviour such as:
- sudden many inbound counterparties
- rapid onward transfers
- high transaction velocity
- short holding times
- fan-in/fan-out
- repeated pass-through behaviour
- connected suspicious accounts
- behavioural change over time

Risk should be explainable. A risk result should show evidence such as unique counterparties, rapid onward movement, network connections, behavioural change, etc. Do not simply display "AI says fraud."

Graph/network functionality is a core differentiator:
account = node
transaction = directed edge
amount/time/risk = edge metadata
network relationships should be inspectable.

Use the supplied MuleGuard assets appropriately and keep the professional financial-security visual identity. Do not let decorative graphics replace functionality.

WORKFLOW — FOLLOW THIS EXACTLY:

PHASE 1: EXPLORE
Audit the repository first. Inspect:
- directory tree
- entry points
- routing
- frontend
- backend/API if present
- authentication
- data/model code
- assets
- dependencies
- scripts
- every existing dashboard and login file
- all routes referenced by navigation

Identify which files are reusable, which are broken, and which should be removed/replaced.

Do NOT start randomly editing files.

PHASE 2: PLAN
Create `IMPLEMENTATION_PLAN.md` containing:
- current architecture findings
- problems discovered
- target architecture
- route map
- authentication flow
- role model
- shared components
- dashboard responsibilities
- data model
- synthetic-data strategy
- risk-scoring/explainability strategy
- graph/network strategy
- files to create/change/delete
- testing/verification plan
- definition of done

Do not hide architectural problems. Be explicit.

PHASE 3: IMPLEMENT
After creating the plan, execute the plan yourself. Do not stop after merely describing the plan.

Build the application as one coherent system.

Priorities:
1. correct architecture
2. working authentication/routing
3. working role-specific pages
4. coherent synthetic data and intelligence
5. explainability/network investigation
6. visual polish

PHASE 4: VERIFY
Actually run the available build/test commands.

Then launch/use the application and verify the complete flow:
1. open login
2. Investigator login
3. investigator dashboard
4. investigator primary navigation
5. suspicious case
6. account/transaction evidence
7. network graph
8. risk explanation
9. logout
10. Compliance login using the SAME login page
11. compliance dashboard
12. escalated case/review flow
13. decision/review page
14. logout
15. Internal Team login using the SAME login page
16. ONE Internal Control Center
17. model/detection/network/data/system modules
18. logout
19. refresh/direct-route checks
20. verify no intended route produces 404
21. check browser/runtime errors

If tests do not exist, create appropriate tests or a practical verification script before claiming completion.

Do not claim a route works unless you have verified it.

PHASE 5: CLEANUP
Remove obsolete/conflicting implementation artifacts, especially:
- Developer Auth Terminal
- duplicate internal dashboards
- unused broken dashboard routes
- dead navigation
- obsolete role-selection code
- conflicting login implementations

Do not delete useful project assets or working functionality without checking dependencies first.

IMPORTANT:
Do not create a new page merely because it sounds impressive. Every page must serve one of the three user roles and the actual MuleGuard goal.

Do not make Investigator and Compliance dashboards visually identical with only different titles. Their navigation and content must reflect their different responsibilities.

Do not create three internal personas just to make the UI look bigger. One Internal Team dashboard is required.

Do not use real banking data or imply production banking integration. This is a controlled academic prototype with synthetic data.

At the end, provide:
1. a concise summary of what was changed
2. the final route map
3. login/demo credentials if mock credentials are used
4. files created/changed/deleted
5. tests/verification performed
6. any remaining limitations
7. confirmation that the definition of done in `MuleGuard_PROJECT_CONTEXT.md` was checked item-by-item

If you encounter a conflict between the existing code and the project-context document, treat the project-context document and the requirements above as authoritative.

Do not optimize for preserving previous work. Optimize for producing a clean, working, coherent MuleGuard prototype.
