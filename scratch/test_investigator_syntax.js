const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = 'e:\\PROJECTS\\MULE GUARD\\frontend\\bank\\investigator';
const pages = [
  'dashboard.html',
  'investigations.html',
  'transactions.html',
  'entities.html',
  'fraud_networks.html',
  'alerts.html',
  'cases.html',
  'risk-analytics.html',
  'network-intelligence.html',
  'watchlists.html'
];

pages.forEach(p => {
  const file = path.join(ROOT, p);
  const content = fs.readFileSync(file, 'utf-8');
  
  const regex = /<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/gi;
  let match;
  let count = 0;
  let err = null;
  while ((match = regex.exec(content)) !== null) {
    count++;
    try {
      new vm.Script(match[1]);
    } catch(e) {
      err = 'Script ' + count + ': ' + e.message;
    }
  }
  console.log(p + ': ' + count + ' inline scripts, Syntax Valid: ' + (err === null ? 'YES' : 'NO (' + err + ')'));
});
