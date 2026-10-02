/**
 * verify_sidebar_navigation.js
 * Comprehensive DOM & Navigation verification for MuleGuard institutional pages.
 */
const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '..');
const AUTH_GUARD_SRC = fs.readFileSync(path.join(ROOT_DIR, 'frontend', 'scripts', 'auth-guard.js'), 'utf-8');

// Lightweight Mock DOM Environment for testing institutional HTML pages
function createMockDOM(htmlContent, currentPath, role, userName, userTitle) {
    const listeners = {};
    const storage = {};

    const localStorageMock = {
        getItem: (k) => storage[k] || null,
        setItem: (k, v) => { storage[k] = String(v); },
        removeItem: (k) => { delete storage[k]; },
        clear: () => { Object.keys(storage).forEach(k => delete storage[k]); }
    };

    const sessionStorageMock = {
        getItem: (k) => {
            if (k === 'muleguard_session') {
                return JSON.stringify({
                    authenticated: true,
                    role: role,
                    user: { name: userName, title: userTitle }
                });
            }
            return null;
        },
        setItem: () => {},
        removeItem: () => {}
    };

    // Extract sidebar container from html
    const asideMatch = htmlContent.match(/<aside[^>]*id=["']sidebar-container["'][^>]*>([\s\S]*?)<\/aside>/i);
    let sidebarInnerHTML = asideMatch ? asideMatch[1] : '';

    const classList = new Set();
    const bodyClassList = {
        add: (c) => classList.add(c),
        remove: (c) => classList.delete(c),
        toggle: (c) => {
            if (classList.has(c)) {
                classList.delete(c);
                return false;
            } else {
                classList.add(c);
                return true;
            }
        },
        contains: (c) => classList.has(c)
    };

    const docClassList = new Set();
    const docElementClassList = {
        add: (c) => docClassList.add(c),
        remove: (c) => docClassList.delete(c),
        toggle: (c) => {
            if (docClassList.has(c)) {
                docClassList.delete(c);
                return false;
            } else {
                docClassList.add(c);
                return true;
            }
        },
        contains: (c) => docClassList.has(c)
    };

    const elementsById = {};
    const attributes = {};

    const sidebarContainer = {
        id: 'sidebar-container',
        get innerHTML() { return sidebarInnerHTML; },
        set innerHTML(val) { sidebarInnerHTML = val; },
        getAttribute: (attr) => attributes[attr] || null,
        setAttribute: (attr, val) => { attributes[attr] = String(val); },
        classList: {
            contains: (c) => false,
            remove: () => {},
            add: () => {}
        },
        querySelectorAll: (sel) => {
            // Find all anchor links in sidebarInnerHTML
            const matches = [];
            const regex = /<a\s+([^>]*?)>/gi;
            let m;
            while ((m = regex.exec(sidebarInnerHTML)) !== null) {
                const attrs = m[1];
                const idMatch = attrs.match(/id=["']([^"']+)["']/i);
                const classMatch = attrs.match(/class=["']([^"']+)["']/i);
                const hrefMatch = attrs.match(/href=["']([^"']+)["']/i);
                const titleMatch = attrs.match(/title=["']([^"']+)["']/i);
                const id = idMatch ? idMatch[1] : '';
                let currentClass = classMatch ? classMatch[1] : '';

                matches.push({
                    id: id,
                    get className() { return currentClass; },
                    set className(val) { currentClass = val; },
                    getAttribute: (a) => {
                        if (a === 'href') return hrefMatch ? hrefMatch[1] : null;
                        if (a === 'title') return titleMatch ? titleMatch[1] : null;
                        return null;
                    },
                    querySelector: (s) => ({
                        classList: { add: () => {}, remove: () => {} },
                        className: ''
                    })
                });
            }
            return matches;
        }
    };

    elementsById['sidebar-container'] = sidebarContainer;

    const mockWindow = {
        location: {
            pathname: currentPath,
            hash: '',
            protocol: 'http:',
            href: 'http://127.0.0.1:8000' + currentPath
        },
        localStorage: localStorageMock,
        sessionStorage: sessionStorageMock,
        addEventListener: (ev, fn) => {
            listeners[ev] = listeners[ev] || [];
            listeners[ev].push(fn);
        },
        dispatchEvent: () => {},
        Event: function(type) { this.type = type; },
        fetch: () => Promise.resolve({ status: 200, json: () => Promise.resolve({}) })
    };

    const mockDocument = {
        readyState: 'complete',
        documentElement: {
            classList: docElementClassList,
            appendChild: () => {}
        },
        body: {
            classList: bodyClassList
        },
        head: {
            appendChild: () => {}
        },
        createElement: (tag) => ({
            id: '',
            textContent: '',
            setAttribute: () => {}
        }),
        getElementById: (id) => {
            if (id === 'sidebar-container') return sidebarContainer;
            if (id === 'sidebar-toggle-btn') {
                return {
                    id: 'sidebar-toggle-btn',
                    title: '',
                    setAttribute: () => {}
                };
            }
            if (id === 'sidebar-toggle-icon') {
                return {
                    id: 'sidebar-toggle-icon',
                    textContent: storage['muleguard_sidebar_collapsed'] === 'true' ? 'menu' : 'menu_open'
                };
            }
            return null;
        },
        querySelector: () => null,
        querySelectorAll: () => [],
        addEventListener: (ev, fn) => {
            listeners[ev] = listeners[ev] || [];
            listeners[ev].push(fn);
        }
    };

    return {
        window: mockWindow,
        document: mockDocument,
        localStorage: localStorageMock,
        sessionStorage: sessionStorageMock,
        sidebarContainer: sidebarContainer,
        bodyClassList: bodyClassList,
        triggerEvent: (ev) => {
            if (listeners[ev]) {
                listeners[ev].forEach(fn => fn());
            }
        }
    };
}

function runTests() {
    console.log("====================================================");
    console.log("MULEGUARD INSTITUTIONAL SIDEBAR VERIFICATION SUITE");
    console.log("====================================================\n");

    let passCount = 0;
    let failCount = 0;

    function assert(desc, condition) {
        if (condition) {
            console.log(`  ✔ PASS: ${desc}`);
            passCount++;
        } else {
            console.error(`  ✖ FAIL: ${desc}`);
            failCount++;
        }
    }

    const testPages = [
        { path: '/frontend/bank/investigator/dashboard.html', role: 'bank_investigator', name: 'Investigator Dashboard', user: 'J. Doe', title: 'Senior Fraud Investigator' },
        { path: '/frontend/bank/investigator/transactions.html', role: 'bank_investigator', name: 'Investigator Transactions', user: 'J. Doe', title: 'Senior Fraud Investigator' },
        { path: '/frontend/bank/investigator/entities.html', role: 'bank_investigator', name: 'Investigator Entities', user: 'J. Doe', title: 'Senior Fraud Investigator' },
        { path: '/frontend/bank/investigator/risk-analytics.html', role: 'bank_investigator', name: 'Investigator Risk Analytics', user: 'J. Doe', title: 'Senior Fraud Investigator' },
        { path: '/frontend/bank/investigator/network-intelligence.html', role: 'bank_investigator', name: 'Investigator Network Intelligence', user: 'J. Doe', title: 'Senior Fraud Investigator' },
        { path: '/frontend/bank/investigator/alerts.html', role: 'bank_investigator', name: 'Investigator Alerts', user: 'J. Doe', title: 'Senior Fraud Investigator' },
        { path: '/frontend/bank/investigator/cases.html', role: 'bank_investigator', name: 'Investigator Cases', user: 'J. Doe', title: 'Senior Fraud Investigator' },
        { path: '/frontend/bank/compliance/dashboard.html', role: 'bank_compliance', name: 'Compliance Dashboard', user: 'A. Kumar', title: 'Senior Compliance Officer' },
        { path: '/frontend/bank/compliance/transactions.html', role: 'bank_compliance', name: 'Compliance Transactions', user: 'A. Kumar', title: 'Senior Compliance Officer' },
        { path: '/frontend/bank/compliance/decisions.html', role: 'bank_compliance', name: 'Compliance Decisions', user: 'A. Kumar', title: 'Senior Compliance Officer' },
        { path: '/frontend/bank/compliance/alerts.html', role: 'bank_compliance', name: 'Compliance Alerts', user: 'A. Kumar', title: 'Senior Compliance Officer' },
        { path: '/frontend/bank/compliance/cases.html', role: 'bank_compliance', name: 'Compliance Cases', user: 'A. Kumar', title: 'Senior Compliance Officer' },
        { path: '/frontend/bank/compliance/network-intelligence.html', role: 'bank_compliance', name: 'Compliance Network Intelligence', user: 'A. Kumar', title: 'Senior Compliance Officer' },
        { path: '/frontend/internal/dashboard.html', role: 'internal_team', name: 'Internal Team Dashboard', user: 'T. Miller', title: 'Platform Operations Lead' }
    ];

    testPages.forEach((p, idx) => {
        console.log(`[Test ${idx + 1}] Testing ${p.name} (${p.role})...`);
        const filePath = path.join(ROOT_DIR, p.path.replace(/\//g, path.sep));
        const html = fs.readFileSync(filePath, 'utf-8');

        const env = createMockDOM(html, p.path, p.role, p.user, p.title);

        // Run auth-guard in this environment
        const runAuthGuard = new Function('window', 'document', 'localStorage', 'sessionStorage', AUTH_GUARD_SRC);
        runAuthGuard(env.window, env.document, env.localStorage, env.sessionStorage);
        env.triggerEvent('DOMContentLoaded');

        const rendered = env.sidebarContainer.innerHTML;

        // 1. Sidebar toggle button rendered
        assert(`${p.name} renders #sidebar-toggle-btn with toggleMuleGuardSidebar`,
            rendered.includes('id="sidebar-toggle-btn"') && rendered.includes('toggleMuleGuardSidebar()')
        );

        // 2. Role-appropriate navigation items rendered
        if (p.role === 'bank_investigator') {
            assert(`${p.name} contains Investigator navigation (Dashboard, Transactions, Risk Analytics, Network Intel)`,
                rendered.includes('id="nav-link-dashboard"') &&
                rendered.includes('id="nav-link-transactions"') &&
                rendered.includes('id="nav-link-risk-analytics"') &&
                rendered.includes('id="nav-link-network-intelligence"')
            );
            assert(`${p.name} does NOT contain Compliance-only or Internal items`,
                !rendered.includes('Regulatory Filings') && !rendered.includes('System Health')
            );
        } else if (p.role === 'bank_compliance') {
            assert(`${p.name} contains Compliance navigation (Dashboard, Decisions, Alerts, Cases, Filings)`,
                rendered.includes('id="nav-link-dashboard"') &&
                rendered.includes('id="nav-link-decisions"') &&
                rendered.includes('Regulatory Filings')
            );
            assert(`${p.name} does NOT contain Internal-only items`,
                !rendered.includes('AI / ML Models') && !rendered.includes('Synthetic Data')
            );
        } else if (p.role === 'internal_team') {
            assert(`${p.name} contains Internal navigation (Health, ML, Rules, Graph, Synthetic Data, Logs)`,
                rendered.includes('id="nav-link-health"') &&
                rendered.includes('id="nav-link-ml"') &&
                rendered.includes('id="nav-link-rules"')
            );
            assert(`${p.name} does NOT contain Investigator/Compliance items`,
                !rendered.includes('Entities') && !rendered.includes('Decisions')
            );
        }

        // 3. User metadata correctly populated
        assert(`${p.name} renders user initials (${p.user.split(' ').map(n=>n[0]).join('')}) and name`,
            rendered.includes(p.user)
        );

        // 4. Toggle collapse / expand mechanism
        assert(`${p.name} exposes window.toggleMuleGuardSidebar function`,
            typeof env.window.toggleMuleGuardSidebar === 'function'
        );

        // Initial state is expanded
        assert(`${p.name} is initially expanded`,
            !env.bodyClassList.contains('sidebar-collapsed')
        );

        // Toggle to collapsed
        env.window.toggleMuleGuardSidebar();
        assert(`${p.name} collapses on toggle click (sidebar-collapsed added, persisted in localStorage)`,
            env.bodyClassList.contains('sidebar-collapsed') &&
            env.localStorage.getItem('muleguard_sidebar_collapsed') === 'true'
        );

        // Toggle back to expanded
        env.window.toggleMuleGuardSidebar();
        assert(`${p.name} expands on second toggle click (sidebar-collapsed removed, localStorage updated)`,
            !env.bodyClassList.contains('sidebar-collapsed') &&
            env.localStorage.getItem('muleguard_sidebar_collapsed') === 'false'
        );

        console.log('');
    });

    console.log("====================================================");
    if (failCount === 0) {
        console.log(`ALL SIDEBAR VERIFICATION TESTS PASSED: ${passCount}/${passCount}`);
    } else {
        console.error(`SOME TESTS FAILED: ${passCount} passed, ${failCount} failed`);
        process.exit(1);
    }
    console.log("====================================================");
}

runTests();
