const fs = require('fs');
const path = require('path');

const compPages = [
    'frontend/bank/compliance/investigations.html',
    'frontend/bank/compliance/transactions.html',
    'frontend/bank/compliance/entities.html',
    'frontend/bank/compliance/fraud_networks.html',
    'frontend/bank/compliance/alerts.html',
    'frontend/bank/compliance/cases.html'
];

compPages.forEach(relPath => {
    const file = path.join(__dirname, '..', relPath);
    if (!fs.existsSync(file)) return;
    let content = fs.readFileSync(file, 'utf8');

    content = content.replace(/(<a\s+href=")#[^"]*("\s+class="[^"]*">\s*<span[^>]*>[^<]*<\/span>\s*<span>Risk Analytics<\/span>)/gi, (m, p1, p2) => `${p1}risk-analytics.html${p2}`);
    content = content.replace(/(<a\s+href=")#[^"]*("\s+class="[^"]*">\s*<span[^>]*>[^<]*<\/span>\s*<span>Network Intelligence<\/span>)/gi, (m, p1, p2) => `${p1}fraud_networks.html${p2}`);
    content = content.replace(/(<a\s+href=")#[^"]*("\s+class="[^"]*">\s*<span[^>]*>[^<]*<\/span>\s*<span>Watchlists<\/span>)/gi, (m, p1, p2) => `${p1}watchlists.html${p2}`);

    fs.writeFileSync(file, content, 'utf8');
});

console.log('Fixed compliance sidebar static links.');
