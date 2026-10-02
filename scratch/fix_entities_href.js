const fs = require('fs');
const path = require('path');

const file = path.join(__dirname, '../frontend/bank/investigator/entities.html');
let content = fs.readFileSync(file, 'utf8');

// Use regex to replace Risk Analytics, Network Intelligence, and Watchlists href="#" in entities.html
let count = 0;

content = content.replace(/(<a\s+href=")#[^"]*("\s+class="[^"]*">\s*<span[^>]*>[^<]*<\/span>\s*<span>Risk Analytics<\/span>)/gi, (m, p1, p2) => {
    count++;
    return `${p1}risk-analytics.html${p2}`;
});

content = content.replace(/(<a\s+href=")#[^"]*("\s+class="[^"]*">\s*<span[^>]*>[^<]*<\/span>\s*<span>Network Intelligence<\/span>)/gi, (m, p1, p2) => {
    count++;
    return `${p1}fraud_networks.html${p2}`;
});

content = content.replace(/(<a\s+href=")#[^"]*("\s+class="[^"]*">\s*<span[^>]*>[^<]*<\/span>\s*<span>Watchlists<\/span>)/gi, (m, p1, p2) => {
    count++;
    return `${p1}watchlists.html${p2}`;
});

fs.writeFileSync(file, content, 'utf8');
console.log(`Updated ${count} links in entities.html`);
