const fs = require('fs');
const path = require('path');
const http = require('http');

function fetchJson(url) {
    return new Promise((resolve, reject) => {
        http.get(url, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    reject(e);
                }
            });
        }).on('error', reject);
    });
}

// Lightweight Mock DOM Element
class MockElement {
    constructor(tagName, id = '') {
        this.tagName = tagName;
        this.id = id;
        this.className = '';
        this.classList = {
            classes: new Set(),
            add: (c) => this.classList.classes.add(c),
            remove: (c) => this.classList.classes.delete(c),
            toggle: (c) => {
                if (this.classList.classes.has(c)) {
                    this.classList.classes.delete(c);
                    return false;
                } else {
                    this.classList.classes.add(c);
                    return true;
                }
            },
            contains: (c) => this.classList.classes.has(c)
        };
        this.attributes = {};
        this.children = [];
        this.innerHTML = '';
        this.textContent = '';
        this.style = {};
        this.value = '';
        this.clientWidth = 1000;
        this.clientHeight = 500;
        this.parentNode = null;
    }

    setAttribute(k, v) { this.attributes[k] = String(v); }
    getAttribute(k) { return this.attributes[k] || null; }
    appendChild(child) {
        child.parentNode = this;
        this.children.push(child);
        return child;
    }
    removeChild(child) {
        const idx = this.children.indexOf(child);
        if (idx !== -1) this.children.splice(idx, 1);
        child.parentNode = null;
        return child;
    }
    querySelector(selector) {
        if (selector.includes('data-node-id')) {
            const match = selector.match(/data-node-id="([^"]+)"/);
            if (match) {
                const targetId = match[1];
                return this.findChild(el => el.attributes['data-node-id'] === targetId);
            }
        }
        return this.children[0] || null;
    }
    querySelectorAll(selector) {
        const res = [];
        this.collectChildren(el => {
            if (selector === '.group/node' && el.attributes['data-node-id']) return true;
            if (selector === 'circle' && el.tagName === 'circle') return true;
            if (selector === '.hop-btn' && (el.className || '').includes('hop-btn')) return true;
            if (selector === '.node-label-group' && (el.attributes['class'] || '').includes('node-label-group')) return true;
            if (selector === '#networks-table-body tr' && el.tagName === 'tr') return true;
            return false;
        }, res);
        return res;
    }
    findChild(pred) {
        for (const c of this.children) {
            if (pred(c)) return c;
            if (c.findChild) {
                const f = c.findChild(pred);
                if (f) return f;
            }
        }
        return null;
    }
    collectChildren(pred, arr) {
        for (const c of this.children) {
            if (pred(c)) arr.push(c);
            if (c.collectChildren) c.collectChildren(pred, arr);
        }
    }
    getBoundingClientRect() {
        return { left: 0, top: 0, width: this.clientWidth, height: this.clientHeight };
    }
    scrollIntoView() {}
}

async function runTests() {
    console.log("====================================================");
    console.log("MULEGUARD REFINED NETWORK INTELLIGENCE TEST SUITE");
    console.log("====================================================\n");

    const networks = await fetchJson('http://127.0.0.1:8000/api/v1/networks');
    console.log(`✔ Fetched ${networks.length} real networks from PostgreSQL API.\n`);

    const filesToTest = [
        'frontend/bank/compliance/network-intelligence.html',
        'frontend/bank/investigator/network-intelligence.html'
    ];

    for (const filePath of filesToTest) {
        console.log(`Checking file: ${filePath}`);
        const html = fs.readFileSync(filePath, 'utf8');

        // 1. Verify HTML Structure Requirements
        const requiredSnippets = [
            'id="sidebar-collapse-btn"',
            'id="account-graph-search"',
            'id="selected-account-dossier"',
            'id="active-network-chip"',
            'body.sidebar-collapsed',
            'id="graph-viewport-wrapper"',
            'loadNetworkIntoWorkspace'
        ];
        requiredSnippets.forEach(snip => {
            if (!html.includes(snip)) {
                throw new Error(`Missing expected element/pattern: ${snip} in ${filePath}`);
            }
        });
        console.log("  ✔ PASS: HTML markup contains all required elements (collapse button, search input, dossier, active network chip, rail CSS).");

        // 2. Setup mock browser environment to test execution of the script
        const scripts = html.match(/<script>([\s\S]*?)<\/script>/gi);
        if (!scripts || scripts.length === 0) throw new Error(`Could not find script in ${filePath}`);
        const scriptCode = scripts[scripts.length - 1].replace(/<script>/i, '').replace(/<\/script>/i, '');

        // Global DOM Elements Map
        const elementsMap = {};
        const getEl = (id, tag = 'div') => {
            if (!elementsMap[id]) elementsMap[id] = new MockElement(tag, id);
            return elementsMap[id];
        };

        // Create standard elements
        getEl('sidebar-container', 'aside');
        getEl('sidebar-collapse-btn', 'button');
        getEl('sidebar-collapse-icon', 'span');
        getEl('account-graph-search', 'input');
        getEl('search-clear-btn', 'button');
        getEl('account-search-suggestions', 'div');
        getEl('active-network-chip', 'div');
        getEl('active-network-name-badge', 'span');
        getEl('network-graph-svg', 'svg');
        getEl('graph-viewport-wrapper', 'div');
        getEl('selected-account-dossier', 'div');
        getEl('networks-table-body', 'tbody');
        getEl('count-total', 'h3');
        getEl('count-high-risk', 'h3');
        getEl('count-review', 'h3');
        getEl('count-newly-detected', 'h3');
        getEl('filter-search', 'input');
        getEl('filter-risk', 'select');
        getEl('filter-type', 'select');
        getEl('filter-status', 'select');
        getEl('toggle-suspicious', 'input');
        getEl('toast', 'div');
        getEl('toast-text', 'span');

        const mockBody = new MockElement('body', '');
        const mockDocument = {
            body: mockBody,
            getElementById: (id) => getEl(id),
            querySelectorAll: (sel) => {
                if (sel === '.hop-btn') {
                    return [0, 1, 2, 3].map(h => {
                        const el = new MockElement('button');
                        el.setAttribute('data-hop', h.toString());
                        el.className = 'hop-btn';
                        return el;
                    });
                }
                if (sel === '.node-label-group') {
                    return [new MockElement('g'), new MockElement('g')];
                }
                return [];
            },
            createElementNS: (ns, tag) => {
                const el = new MockElement(tag);
                if (tag === 'svg') {
                    el.createSVGPoint = () => ({ x: 0, y: 0, matrixTransform: () => ({ x: 100, y: 100 }) });
                }
                return el;
            },
            createElement: (tag) => new MockElement(tag),
            addEventListener: () => {}
        };

        const mockWindow = {
            document: mockDocument,
            addEventListener: () => {},
            localStorage: {
                store: {},
                getItem(k) { return this.store[k] || null; },
                setItem(k, v) { this.store[k] = String(v); }
            },
            setTimeout: (fn) => fn(),
            clearTimeout: () => {},
            console: console
        };

        // Contextual eval
        const runContext = new Function(
            'window', 'document', 'localStorage', 'setTimeout', 'clearTimeout',
            `
            ${scriptCode}
            return {
                networksDb,
                graphState,
                toggleSidebarCollapse,
                loadNetworkIntoWorkspace,
                renderNetworkGraph,
                selectAccountNode,
                selectAndFocusAccount,
                centerGraphOnAccountNode,
                handleAccountSearchInput,
                renderNetworksTable,
                zoomInGraph,
                zoomOutGraph,
                resetActiveVisualizerGraph,
                setHopDepthFilter,
                toggleGraphLabels,
                toggleGraphAmounts,
                toggleGraphDirections,
                toggleSuspiciousOnly,
                handleGraphResize
            };
            `
        );

        const scope = runContext(
            mockWindow,
            mockDocument,
            mockWindow.localStorage,
            mockWindow.setTimeout,
            mockWindow.clearTimeout
        );

        // Populate scope.networksDb with real PostgreSQL data
        networks.forEach(net => { scope.networksDb[net.id] = net; });

        // Test 1: Collapse / Expand Sidebar
        const initialCollapsed = mockBody.classList.contains('sidebar-collapsed');
        scope.toggleSidebarCollapse();
        const afterToggle = mockBody.classList.contains('sidebar-collapsed');
        if (afterToggle === initialCollapsed) {
            throw new Error("Sidebar collapse toggle failed");
        }
        scope.toggleSidebarCollapse();
        console.log("  ✔ PASS: Sidebar collapse/expand toggles correctly and updates rail state.");

        // Test 2: Table Rendering & Network Workspace Loading
        scope.renderNetworksTable(Object.values(scope.networksDb));
        const testNetId = networks[0].id;
        scope.loadNetworkIntoWorkspace(testNetId);
        const activeName = getEl('active-network-name-badge').textContent;
        if (!activeName.includes(testNetId)) {
            throw new Error(`Active network badge was not updated with ${testNetId}`);
        }
        console.log(`  ✔ PASS: Network ${testNetId} loaded into workspace; active badge updated.`);

        // Test 3: Account Search & Auto-Focusing
        const sampleAccount = networks[0].graphNodes[1].id;
        const sampleCustName = networks[0].graphNodes[1].customer_name;
        scope.selectAndFocusAccount(sampleAccount);
        if (scope.graphState.selectedNodeId !== sampleAccount) {
            throw new Error(`Failed to focus account ${sampleAccount}`);
        }
        console.log(`  ✔ PASS: Account search focused ${sampleAccount} (${sampleCustName}).`);

        // Test 4: Selected Account Dossier Fields
        const dossierHtml = getEl('selected-account-dossier').innerHTML;
        const requiredTerms = [
            sampleAccount,
            sampleCustName,
            'Balance',
            'Total Inflow',
            'Total Outflow',
            'Total Transactions',
            'Unique Counterparties',
            'Mule Risk Score'
        ];
        requiredTerms.forEach(t => {
            if (!dossierHtml.includes(t)) {
                throw new Error(`Dossier missing term: ${t}`);
            }
        });
        console.log("  ✔ PASS: Selected Account Dossier renders complete PostgreSQL profile & KPI cards.");

        // Test 5: Graph Controls
        const initialZoom = scope.graphState.zoom;
        scope.zoomInGraph();
        if (scope.graphState.zoom <= initialZoom) throw new Error("Zoom in failed");
        scope.zoomOutGraph();
        scope.resetActiveVisualizerGraph();
        if (scope.graphState.zoom !== 1.0) throw new Error("Reset view failed");

        scope.setHopDepthFilter(2);
        if (scope.graphState.hopDepth !== 2) throw new Error("Hop filter failed");
        scope.setHopDepthFilter(0);

        scope.toggleGraphLabels(false);
        scope.toggleGraphLabels(true);
        scope.toggleGraphAmounts(false);
        scope.toggleGraphAmounts(true);
        scope.toggleGraphDirections(false);
        scope.toggleGraphDirections(true);
        scope.toggleSuspiciousOnly(true);
        scope.toggleSuspiciousOnly(false);
        console.log("  ✔ PASS: Graph controls (zoom in/out, reset, 1/2/3-hop, labels, amounts, directions, high-risk only) executed without errors.");

        // Test 6: Auto Resize
        scope.handleGraphResize();
        console.log("  ✔ PASS: Auto-resize handler executed.\n");
    }

    console.log("====================================================");
    console.log("ALL TESTS COMPLETED SUCCESSFULLY: ALL CHECKS PASS");
    console.log("====================================================");
}

runTests().catch(err => {
    console.error("Test execution failed:", err);
    process.exit(1);
});
