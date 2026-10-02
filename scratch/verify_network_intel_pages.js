const http = require('http');

function checkPage(url, name) {
    http.get(url, (res) => {
        let html = '';
        res.on('data', chunk => html += chunk);
        res.on('end', () => {
            console.log('=== ' + name + ' ===');
            console.log('Status:', res.statusCode);
            console.log('Title match:', html.includes('<title>MuleGuard - Network Intelligence</title>'));
            console.log('Fraud Networks link:', html.includes('href="fraud_networks.html" id="nav-link-fraud_networks"'));
            console.log('Network Intelligence link:', html.includes('href="network-intelligence.html" id="nav-link-network-intelligence"'));
            console.log('API call:', html.includes('MuleGuardAPI.getNetworks'));
            console.log('Visualizer SVG:', html.includes('id="network-graph-svg"'));
            console.log('Tbody table:', html.includes('id="networks-tbody"'));
        });
    });
}

checkPage('http://127.0.0.1:8000/frontend/bank/investigator/network-intelligence.html', 'INVESTIGATOR');
checkPage('http://127.0.0.1:8000/frontend/bank/compliance/network-intelligence.html', 'COMPLIANCE');
