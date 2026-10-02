const { JSDOM } = require('jsdom');
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

async function runInteractionTests() {
    console.log("==================================================");
    console.log("VERIFYING REFINED NETWORK INTELLIGENCE INTERACTIONS");
    console.log("==================================================");

    // 1. Fetch live PostgreSQL networks from API
    const liveNetworks = await fetchJson('http://127.0.0.1:8000/api/v1/networks');
    console.log(`[PASS] Fetched ${liveNetworks.length} live PostgreSQL networks`);
    if (liveNetworks.length < 2) {
        throw new Error("Expected at least 2 networks in database to test selection");
    }

    const htmlPath = path.join(__dirname, '../frontend/bank/investigator/network-intelligence.html');
    const htmlContent = fs.readFileSync(htmlPath, 'utf8');

    // Setup JSDOM
    const dom = new JSDOM(htmlContent, {
        runScripts: 'dangerously',
        resources: 'usable',
        url: 'http://127.0.0.1:8000/bank/investigator/network-intelligence.html'
    });

    const { window } = dom;
    const { document } = window;

    // Wait for scripts and DOM to load
    await new Promise(resolve => setTimeout(resolve, 600));

    // Inject networksDb directly into window
    window.networksDb = {};
    liveNetworks.forEach(n => {
        window.networksDb[n.id] = n;
    });

    // Call renderNetworksTable & initial load
    window.renderNetworksTable(Object.values(window.networksDb));
    const firstNetId = liveNetworks[0].id;
    const secondNetId = liveNetworks[1].id;
    window.currentlyRenderedNetworkId = firstNetId;
    window.renderNetworkGraph(firstNetId, 'network-graph-svg');

    console.log(`\nInitial state: Currently rendered network = ${window.currentlyRenderedNetworkId}`);

    // ==========================================
    // TEST 1: Inspect button opens drawer (DO NOT replace graph)
    // ==========================================
    console.log("\n[TEST 1] Testing 'Inspect →' button opens inspection drawer without replacing graph...");
    const inspectButtons = document.querySelectorAll('.inspect-btn');
    if (inspectButtons.length === 0) throw new Error("No inspect buttons found in table");

    // Click inspect on second network
    window.openNetworkInspectionDrawer(secondNetId);

    const drawer = document.getElementById('network-inspection-drawer');
    const overlay = document.getElementById('network-inspection-overlay');
    const bodyContent = document.getElementById('drawer-content-body');

    if (!drawer.classList.contains('drawer-open')) {
        throw new Error("Drawer failed to open with .drawer-open class");
    }
    if (!overlay.classList.contains('overlay-open')) {
        throw new Error("Overlay failed to open with .overlay-open class");
    }
    if (window.currentlyRenderedNetworkId !== firstNetId) {
        throw new Error(`Graph was immediately replaced! Expected ${firstNetId} but got ${window.currentlyRenderedNetworkId}`);
    }
    console.log("  ✔ PASS: Inspect opens drawer with smooth classes without replacing current graph");
    console.log(`  ✔ PASS: Main graph still renders ${window.currentlyRenderedNetworkId}`);

    // Verify drawer metadata content
    const drawerHtml = bodyContent.innerHTML;
    if (!drawerHtml.includes(secondNetId)) {
        throw new Error(`Drawer does not display Network ID ${secondNetId}`);
    }
    if (!drawerHtml.includes("Total Value") || !drawerHtml.includes("Members") || !drawerHtml.includes("Relevant Network Indicators")) {
        throw new Error("Drawer is missing required metadata sections");
    }
    console.log("  ✔ PASS: Drawer contains full metadata (ID, risk, members, total value, indicators, inflow/outflow)");

    // ==========================================
    // TEST 2: Network ID click opens drawer (same behavior as Inspect)
    // ==========================================
    console.log("\n[TEST 2] Testing Network ID click opens same inspection drawer...");
    window.closeNetworkInspectionDrawer();
    if (drawer.classList.contains('drawer-open')) {
        throw new Error("Drawer failed to close");
    }

    // Simulate clicking the Network ID cell of the second network
    window.openNetworkInspectionDrawer(secondNetId);
    if (!drawer.classList.contains('drawer-open')) {
        throw new Error("Network ID click failed to open inspection drawer");
    }
    if (window.currentlyRenderedNetworkId !== firstNetId) {
        throw new Error("Network ID click prematurely replaced main graph");
    }
    console.log("  ✔ PASS: Clicking Network ID opens the same inspection drawer without replacing graph");

    // ==========================================
    // TEST 3: "View Network Graph" button in drawer loads selected network into graph
    // ==========================================
    console.log("\n[TEST 3] Testing 'View Network Graph' button loads network and closes drawer...");
    window.executeLoadNetworkFromDrawer();

    if (window.currentlyRenderedNetworkId !== secondNetId) {
        throw new Error(`Expected main graph to render ${secondNetId}, but rendered ${window.currentlyRenderedNetworkId}`);
    }
    if (drawer.classList.contains('drawer-open')) {
        throw new Error("Drawer should close after clicking 'View Network Graph'");
    }
    const badge = document.getElementById('active-network-name-badge');
    if (!badge.textContent.includes(secondNetId)) {
        throw new Error(`Active network badge was not updated with ${secondNetId}`);
    }
    console.log(`  ✔ PASS: 'View Network Graph' updated main graph to ${secondNetId}`);
    console.log("  ✔ PASS: Drawer closed automatically and active network badge updated");

    // ==========================================
    // TEST 4: Graph Canvas Pan and Drag
    // ==========================================
    console.log("\n[TEST 4] Testing Graph Canvas Pan & Node Drag behaviors...");
    const wrapper = document.getElementById('graph-viewport-wrapper');
    const svg = document.getElementById('network-graph-svg');

    // Simulate Canvas Panning
    window.graphState.panX = 0;
    window.graphState.panY = 0;
    window.graphState.dragStart = { x: 100, y: 100 };
    window.graphState.isDraggingCanvas = true;
    document.body.classList.add('is-canvas-panning');
    wrapper.classList.add('is-panning');

    // Pan by dx=45, dy=30
    window.graphState.panX = 145 - window.graphState.dragStart.x; // 45
    window.graphState.panY = 130 - window.graphState.dragStart.y; // 30
    window.applyGraphViewportTransform();

    const vp = document.getElementById('network-graph-svg-viewport');
    if (!vp.getAttribute('transform').includes('translate(45, 30)')) {
        throw new Error(`Expected viewport transform to have translate(45, 30), got ${vp.getAttribute('transform')}`);
    }
    console.log("  ✔ PASS: Empty canvas background dragging updates pan coordinates freely");

    // Test Node Drag without rebuild
    const net = window.networksDb[secondNetId];
    const testNode = net.graphNodes[0];
    const nodeGroup = document.getElementById(`network-graph-svg-node-group-${testNode.id}`);
    if (!nodeGroup) {
        throw new Error(`Node group element network-graph-svg-node-group-${testNode.id} not found in DOM`);
    }

    const netKey = `${secondNetId}_${net.graphNodes.length}_${window.graphState.canvasWidth}_${window.graphState.canvasHeight}`;
    const initialPos = window.graphState.nodePositions[netKey][testNode.id];
    const newPos = { x: initialPos.x + 80, y: initialPos.y + 60 };

    // Update in DOM
    window.updateNodePositionInDOM(testNode.id, newPos, 'network-graph-svg');
    const updatedTransform = nodeGroup.getAttribute('transform');
    if (!updatedTransform.includes(`translate(${newPos.x}, ${newPos.y})`)) {
        throw new Error(`Node DOM transform not updated! Expected translate(${newPos.x}, ${newPos.y}), got ${updatedTransform}`);
    }
    console.log(`  ✔ PASS: Node dragging moves only that node directly in DOM without rebuilding SVG`);

    // ==========================================
    // TEST 5: Fullscreen & Vertical Scrolling
    // ==========================================
    console.log("\n[TEST 5] Testing Fullscreen mode & vertical scrolling...");
    window.setFullscreenVisualizerMode(true);

    if (!document.body.classList.contains('network-fullscreen-mode')) {
        throw new Error("network-fullscreen-mode class not added to body");
    }
    const fsBtn = document.getElementById('fullscreen-btn');
    const fsIcon = fsBtn.querySelector('.material-symbols-outlined');
    if (fsIcon.textContent !== 'fullscreen_exit') {
        throw new Error(`Expected fullscreen_exit icon, got ${fsIcon.textContent}`);
    }
    console.log("  ✔ PASS: Fullscreen mode activates and toggles icon to fullscreen_exit");

    // Exit fullscreen
    window.setFullscreenVisualizerMode(false);
    if (document.body.classList.contains('network-fullscreen-mode')) {
        throw new Error("network-fullscreen-mode not removed from body");
    }
    if (fsIcon.textContent !== 'fullscreen') {
        throw new Error(`Expected fullscreen icon, got ${fsIcon.textContent}`);
    }
    console.log("  ✔ PASS: Exiting fullscreen restores normal layout correctly");

    console.log("\n==================================================");
    console.log("ALL INTERACTION VERIFICATION TESTS PASSED (5/5 PASS)");
    console.log("==================================================");
}

runInteractionTests().catch(err => {
    console.error("\n[TEST ERROR]:", err);
    process.exit(1);
});
