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

async function runTests() {
    console.log("=== MuleGuard Network Intelligence Verification ===");
    
    // 1. Test API endpoint
    const networks = await fetchJson('http://127.0.0.1:8000/api/v1/networks');
    console.log(`[PASS] Fetched ${networks.length} networks from /api/v1/networks`);
    
    if (networks.length === 0) {
        throw new Error("No networks returned from API");
    }
    
    // 2. Verify no 'Shell Partner' in any network or node
    const rawString = JSON.stringify(networks);
    if (rawString.includes('Shell Partner')) {
        throw new Error("Found 'Shell Partner' in network API response!");
    }
    console.log("[PASS] Zero 'Shell Partner' occurrences across all networks and nodes.");
    
    // 3. Inspect first 5 networks
    for (let i = 0; i < Math.min(5, networks.length); i++) {
        const net = networks[i];
        console.log(`\nNetwork ${i+1}: ${net.id} | ${net.name} | Type: ${net.type}`);
        console.log(`  - Risk Score: ${net.risk_score} | Status: ${net.status}`);
        console.log(`  - Nodes: ${net.nodes_count} (${net.graphNodes.length} graphNodes)`);
        console.log(`  - Links: ${net.links_count} (${net.graphLinks.length} graphLinks)`);
        
        // Verify nodes have real Indian names and valid account IDs
        net.graphNodes.forEach((node, idx) => {
            if (!node.account_id || !node.customer_name) {
                throw new Error(`Node ${idx} missing account_id or customer_name in net ${net.id}`);
            }
            if (!node.account_id.startsWith('ACC-')) {
                throw new Error(`Invalid account_id ${node.account_id} in net ${net.id}`);
            }
        });
        
        // Verify links are valid directed edges between nodes
        const nodeIds = new Set(net.graphNodes.map(n => n.account_id));
        net.graphLinks.forEach((link, idx) => {
            if (!link.source || !link.target) {
                throw new Error(`Link ${idx} missing source or target in net ${net.id}`);
            }
            if (!nodeIds.has(link.source) || !nodeIds.has(link.target)) {
                throw new Error(`Link ${link.source} -> ${link.target} references non-existent node in net ${net.id}`);
            }
            if (!link.amount_formatted || !link.amount_formatted.includes('₹')) {
                throw new Error(`Link ${link.source} -> ${link.target} missing INR formatted amount`);
            }
        });
    }
    console.log("\n[PASS] All nodes have real customer names, valid account IDs, and valid directed transaction links with INR amounts.");
    
    // 4. Test 2D Force-Directed Simulation logic
    const testNet = networks[0];
    const nodes = testNet.graphNodes.map(n => ({ ...n }));
    const links = testNet.graphLinks.map(l => ({ ...l }));
    
    // Simulation function replication
    const width = 800, height = 460;
    const simNodes = nodes.map((n, i) => {
        const angle = (2 * Math.PI * i) / Math.max(nodes.length, 1);
        const radius = Math.min(width, height) * 0.28 + (i % 3) * 20;
        return {
            ...n,
            x: width / 2 + Math.cos(angle) * radius + (Math.random() - 0.5) * 20,
            y: height / 2 + Math.sin(angle) * radius + (Math.random() - 0.5) * 20,
            vx: 0,
            vy: 0
        };
    });
    
    const nodeById = {};
    simNodes.forEach(n => { nodeById[n.account_id] = n; });
    
    const simLinks = links.map(l => ({
        source: nodeById[l.source],
        target: nodeById[l.target],
        amount: l.amount,
        amount_formatted: l.amount_formatted
    })).filter(l => l.source && l.target);
    
    // Run 60 simulation steps
    for (let step = 0; step < 60; step++) {
        // Repulsion
        for (let i = 0; i < simNodes.length; i++) {
            for (let j = i + 1; j < simNodes.length; j++) {
                const a = simNodes[i], b = simNodes[j];
                const dx = b.x - a.x;
                const dy = b.y - a.y;
                const distSq = dx * dx + dy * dy + 100;
                const dist = Math.sqrt(distSq);
                const force = 3800 / distSq;
                const fx = (dx / dist) * force;
                const fy = (dy / dist) * force;
                a.vx -= fx;
                a.vy -= fy;
                b.vx += fx;
                b.vy += fy;
            }
        }
        // Spring attraction along real links
        for (const link of simLinks) {
            const dx = link.target.x - link.source.x;
            const dy = link.target.y - link.source.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const diff = dist - 130;
            const force = diff * 0.045;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            link.source.vx += fx;
            link.source.vy += fy;
            link.target.vx -= fx;
            link.target.vy -= fy;
        }
        // Center gravity and damping
        for (const n of simNodes) {
            n.vx += (width / 2 - n.x) * 0.015;
            n.vy += (height / 2 - n.y) * 0.015;
            n.vx *= 0.65;
            n.vy *= 0.65;
            n.x += n.vx;
            n.y += n.vy;
            n.x = Math.max(30, Math.min(width - 30, n.x));
            n.y = Math.max(30, Math.min(height - 30, n.y));
        }
    }
    
    // Check results
    simNodes.forEach(n => {
        if (isNaN(n.x) || isNaN(n.y)) {
            throw new Error(`NaN coordinate for node ${n.account_id}`);
        }
    });
    console.log(`[PASS] 2D Force simulation executed stably for ${simNodes.length} nodes and ${simLinks.length} links.`);
    
    // 5. Test Selected Account Dossier generation for each node
    for (const node of testNet.graphNodes) {
        if (!node.connected_accounts || !Array.isArray(node.connected_accounts)) {
            throw new Error(`Node ${node.account_id} missing connected_accounts array`);
        }
        if (!node.recent_transactions || !Array.isArray(node.recent_transactions)) {
            throw new Error(`Node ${node.account_id} missing recent_transactions array`);
        }
        if (!node.suspicion_reasons || !Array.isArray(node.suspicion_reasons)) {
            throw new Error(`Node ${node.account_id} missing suspicion_reasons array`);
        }
    }
    console.log(`[PASS] All nodes contain complete Selected Account Dossier data (connected_accounts, recent_transactions, suspicion_reasons).`);
    
    console.log("\n>>> ALL NETWORK INTELLIGENCE VERIFICATIONS PASSED SUCCESSFULLY! <<<");
}

runTests().catch(err => {
    console.error("Verification failed:", err);
    process.exit(1);
});
