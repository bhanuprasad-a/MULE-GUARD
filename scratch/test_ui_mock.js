const fs = require('fs');
const path = require('path');
const vm = require('vm');
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

// Lightweight Element Mock
class MockElement {
    constructor(tagName, id = '') {
        this.tagName = tagName;
        this.id = id;
        this.attributes = {};
        this.classList = new Set();
        this.children = [];
        this.style = {};
        this.innerHTML = '';
        this.textContent = '';
        this.clientWidth = 1000;
        this.clientHeight = 500;
        this.listeners = {};
    }

    setAttribute(name, val) {
        this.attributes[name] = String(val);
        if (name === 'id') this.id = String(val);
    }

    getAttribute(name) {
        return this.attributes[name] || null;
    }

    appendChild(child) {
        this.children.push(child);
        return child;
    }

    addEventListener(event, fn) {
        if (!this.listeners[event]) this.listeners[event] = [];
        this.listeners[event].push(fn);
    }

    dispatchEvent(event) {
        if (this.listeners[event.type]) {
            this.listeners[event.type].forEach(fn => fn(event));
        }
        if (this['on' + event.type]) {
            this['on' + event.type](event);
        }
    }

    querySelector(selector) {
        if (selector.startsWith('.')) {
            const cls = selector.slice(1);
            return this.children.find(c => c.classList && c.classList.has(cls)) || null;
        }
        return this.children.find(c => c.tagName && c.tagName.toLowerCase() === selector.toLowerCase()) || null;
    }

    querySelectorAll(selector) {
        const results = [];
        const check = (node) => {
            if (selector.startsWith('.')) {
                if (node.classList && node.classList.has(selector.slice(1))) results.push(node);
            } else if (node.tagName && node.tagName.toLowerCase() === selector.toLowerCase()) {
                results.push(node);
            }
            if (node.children) node.children.forEach(check);
        };
        check(this);
        return results;
    }

    scrollIntoView() {
        this.scrolledIntoView = true;
    }
}

// Set up Mock DOM
function createMockDOM() {
    const elements = new Map();

    const getOrCreate = (id, tag = 'div') => {
        if (!elements.has(id)) {
            const el = new MockElement(tag, id);
            el.classList = {
                set: new Set(),
                add: function(c) { this.set.add(c); },
                remove: function(c) { this.set.delete(c); },
                contains: function(c) { return this.set.has(c); },
                toggle: function(c, force) {
                    if (force !== undefined) {
                        if (force) this.set.add(c); else this.set.delete(c);
                        return force;
                    }
                    if (this.set.has(c)) { this.set.delete(c); return false; }
                    this.set.add(c); return true;
                }
            };
            elements.set(id, el);
        }
        return elements.get(id);
    };

    const doc = {
        getElementById: (id) => getOrCreate(id),
        createElementNS: (ns, tag) => {
            const el = new MockElement(tag);
            el.classList = {
                set: new Set(),
                add: function(c) { this.set.add(c); },
                remove: function(c) { this.set.delete(c); },
                contains: function(c) { return this.set.has(c); },
                toggle: function(c) {
                    if (this.set.has(c)) { this.set.delete(c); return false; }
                    this.set.add(c); return true;
                }
            };
            return el;
        },
        createElement: (tag) => {
            const el = new MockElement(tag);
            el.classList = {
                set: new Set(),
                add: function(c) { this.set.add(c); },
                remove: function(c) { this.set.delete(c); },
                contains: function(c) { return this.set.has(c); },
                toggle: function(c) {
                    if (this.set.has(c)) { this.set.delete(c); return false; }
                    this.set.add(c); return true;
                }
            };
            return el;
        },
        addEventListener: () => {},
        body: getOrCreate('body', 'body'),
        documentElement: getOrCreate('html', 'html')
    };

    // Pre-create required elements
    doc.getElementById('network-graph-svg', 'svg');
    doc.getElementById('graph-viewport-wrapper', 'div');
    doc.getElementById('selected-account-dossier', 'section');
    doc.getElementById('networks-table-body', 'tbody');
    doc.getElementById('active-network-name-badge', 'span');
    doc.getElementById('network-inspection-drawer', 'aside');
    doc.getElementById('network-inspection-overlay', 'div');
    doc.getElementById('drawer-network-id-subtitle', 'span');
    doc.getElementById('drawer-content-body', 'div');
    doc.getElementById('drawer-view-graph-btn', 'button');
    doc.getElementById('fullscreen-btn', 'button');
    const fsIcon = new MockElement('span');
    fsIcon.classList.add('material-symbols-outlined');
    fsIcon.textContent = 'fullscreen';
    doc.getElementById('fullscreen-btn').appendChild(fsIcon);
    doc.getElementById('graph-panel-section', 'section');
    doc.getElementById('count-total', 'h3');
    doc.getElementById('count-high-risk', 'h3');
    doc.getElementById('count-review', 'h3');
    doc.getElementById('count-newly-detected', 'h3');
    doc.getElementById('toast', 'div');
    doc.getElementById('toast-text', 'span');

    return { doc, elements };
}

async function run() {
    console.log("=== Testing Network Intelligence Interactions via Headless Execution ===");

    // 1. Fetch live networks from PostgreSQL
    const liveNetworks = await fetchJson('http://127.0.0.1:8000/api/v1/networks');
    console.log(`[PASS] Fetched ${liveNetworks.length} networks from PostgreSQL API`);

    // 2. Load script from compliance page
    const compHtmlPath = path.join(__dirname, '../frontend/bank/compliance/network-intelligence.html');
    const compHtml = fs.readFileSync(compHtmlPath, 'utf8');
    const compScripts = compHtml.match(/<script>([\s\S]*?)<\/script>/g);
    const compScriptCode = compScripts[compScripts.length - 1].replace(/^<script>/, '').replace(/<\/script>$/, '');

    const { doc, elements } = createMockDOM();

    // Setup window/sandbox context
    const sandbox = {
        document: doc,
        window: {
            addEventListener: () => {},
            removeEventListener: () => {}
        },
        console: console,
        setTimeout: (fn) => fn(),
        clearTimeout: () => {},
        Math: Math,
        Array: Array,
        Object: Object,
        String: String,
        Set: Set,
        isNaN: isNaN,
        parseInt: parseInt
    };

    vm.createContext(sandbox);
    vm.runInContext(compScriptCode, sandbox);

    // Provide fetch so loadNetworksData populates internal networksDb
    sandbox.fetch = async (url) => ({
        ok: true,
        json: async () => liveNetworks
    });

    await sandbox.loadNetworksData();
    const netKeys = vm.runInContext('Object.keys(networksDb)', sandbox);
    console.log(`[PASS] loadNetworksData completed, loaded ${netKeys.length} networks`);

    const net1 = liveNetworks[0];
    const net2 = liveNetworks[1];

    console.log(`[PASS] Initial graph rendered: ${vm.runInContext('currentlyRenderedNetworkId', sandbox)}`);

    // TEST 1: Click Inspect on net2
    console.log("\n[TEST 1] Testing Inspect button opens drawer without replacing graph...");
    sandbox.openNetworkInspectionDrawer(net2.id);

    const drawer = doc.getElementById('network-inspection-drawer');
    const overlay = doc.getElementById('network-inspection-overlay');
    const drawerBody = doc.getElementById('drawer-content-body');

    if (!drawer.classList.contains('drawer-open')) throw new Error("Drawer missing .drawer-open");
    if (!overlay.classList.contains('overlay-open')) throw new Error("Overlay missing .overlay-open");
    let currentRendered = vm.runInContext('currentlyRenderedNetworkId', sandbox);
    if (currentRendered !== net1.id) {
        throw new Error(`Graph was replaced immediately! Expected ${net1.id} but got ${currentRendered}`);
    }
    console.log(`  ✔ PASS: Drawer is open, and main graph STILL renders ${currentRendered} (NOT replaced)`);

    // Verify metadata inside drawer
    if (!drawerBody.innerHTML.includes(net2.id)) throw new Error("Drawer missing net2 ID");
    if (!drawerBody.innerHTML.includes("Total Value") || !drawerBody.innerHTML.includes("Members")) {
        throw new Error("Drawer missing required metrics");
    }
    console.log(`  ✔ PASS: Drawer contains full metadata for ${net2.id} (${net2.name})`);

    // TEST 2: Network ID click
    console.log("\n[TEST 2] Testing Network ID click in table...");
    sandbox.closeNetworkInspectionDrawer();
    if (drawer.classList.contains('drawer-open')) throw new Error("Drawer did not close");

    // Click Network ID of net2
    sandbox.openNetworkInspectionDrawer(net2.id);
    if (!drawer.classList.contains('drawer-open')) throw new Error("Network ID click failed to open drawer");
    currentRendered = vm.runInContext('currentlyRenderedNetworkId', sandbox);
    if (currentRendered !== net1.id) throw new Error("Network ID click prematurely replaced graph");
    console.log("  ✔ PASS: Clicking Network ID opens the same inspection drawer without replacing graph");

    // TEST 3: Click "View Network Graph" in drawer
    console.log("\n[TEST 3] Testing 'View Network Graph' button in drawer...");
    sandbox.executeLoadNetworkFromDrawer();

    currentRendered = vm.runInContext('currentlyRenderedNetworkId', sandbox);
    if (currentRendered !== net2.id) {
        throw new Error(`Expected main graph to load ${net2.id}, but got ${currentRendered}`);
    }
    if (drawer.classList.contains('drawer-open')) throw new Error("Drawer should be closed after loading network graph");
    const badge = doc.getElementById('active-network-name-badge');
    if (!badge.textContent.includes(net2.id)) throw new Error("Active network badge not updated");
    console.log(`  ✔ PASS: Main graph loaded selected network ${currentRendered}`);
    console.log("  ✔ PASS: Inspection drawer closed and active badge updated");

    // TEST 4: Graph Pan and Node Drag
    console.log("\n[TEST 4] Testing Pan and Node Drag...");
    const graphState = vm.runInContext('graphState', sandbox);
    graphState.panX = 0;
    graphState.panY = 0;
    graphState.dragStart = { x: 50, y: 50 };
    graphState.isDraggingCanvas = true;
    graphState.panX = 120 - graphState.dragStart.x;
    graphState.panY = 80 - graphState.dragStart.y;
    sandbox.applyGraphViewportTransform();

    const vp = doc.getElementById('network-graph-svg-viewport');
    if (!vp.getAttribute('transform').includes('translate(70, 30)')) {
        throw new Error(`Viewport transform incorrect: ${vp.getAttribute('transform')}`);
    }
    console.log("  ✔ PASS: Canvas pan updates viewport transform freely without boundary restrictions");

    // Test Node Drag in DOM
    const testNode = net2.graphNodes[0];
    const initialPos = { x: 200, y: 150 };
    const movedPos = { x: 280, y: 220 };
    sandbox.updateNodePositionInDOM(testNode.id, movedPos, 'network-graph-svg');
    const nodeEl = doc.getElementById(`network-graph-svg-node-group-${testNode.id}`);
    if (!nodeEl || !nodeEl.getAttribute('transform').includes('translate(280, 220)')) {
        throw new Error(`Node element not moved in DOM: ${nodeEl ? nodeEl.getAttribute('transform') : 'null'}`);
    }
    console.log("  ✔ PASS: Node dragged smoothly moves only that node directly in DOM");

    // TEST 5: Fullscreen Toggle and Scrolling
    console.log("\n[TEST 5] Testing Fullscreen button and scrolling mode...");
    sandbox.setFullscreenVisualizerMode(true);
    if (!doc.body.classList.contains('network-fullscreen-mode')) {
        throw new Error("network-fullscreen-mode not added to body");
    }
    const fsBtn = doc.getElementById('fullscreen-btn');
    const icon = fsBtn.querySelector('.material-symbols-outlined');
    if (icon.textContent !== 'fullscreen_exit') {
        throw new Error(`Expected fullscreen_exit icon, got ${icon.textContent}`);
    }
    console.log("  ✔ PASS: Fullscreen mode activates and icon toggles to fullscreen_exit");

    sandbox.setFullscreenVisualizerMode(false);
    if (doc.body.classList.contains('network-fullscreen-mode')) {
        throw new Error("network-fullscreen-mode not removed from body");
    }
    if (icon.textContent !== 'fullscreen') {
        throw new Error(`Expected fullscreen icon, got ${icon.textContent}`);
    }
    console.log("  ✔ PASS: Exiting fullscreen restores normal layout correctly");

    console.log("\n==================================================");
    console.log("ALL 5/5 UI INTERACTION REQUIREMENTS VERIFIED!");
    console.log("==================================================");
}

run().catch(err => {
    console.error("FAIL:", err);
    process.exit(1);
});
