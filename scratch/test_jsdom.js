const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const virtualConsole = new VirtualConsole();
virtualConsole.on('error', (err) => console.error('BROWSER ERROR:', err));
virtualConsole.on('warn', (msg) => console.warn('BROWSER WARN:', msg));
virtualConsole.on('log', (msg) => console.log('BROWSER LOG:', msg));

// Read dashboard.html
const htmlPath = path.join(__dirname, '../frontend/bank/investigator/dashboard.html');
const htmlContent = fs.readFileSync(htmlPath, 'utf8');

// Mock sessionStorage with investigator user
const dom = new JSDOM(htmlContent, {
    url: 'http://localhost:8000/frontend/bank/investigator/dashboard.html',
    runScripts: 'dangerously',
    resources: 'usable',
    virtualConsole
});

const { window } = dom;

window.sessionStorage.setItem('muleguard_session', JSON.stringify({
    authenticated: true,
    role: 'bank_investigator',
    subRole: 'detection',
    user: { name: 'A. Kumar', title: 'Senior Analyst' }
}));

// Load auth-guard.js manually inside the JSDOM context
const authGuardScript = fs.readFileSync(path.join(__dirname, '../frontend/scripts/auth-guard.js'), 'utf8');
window.eval(authGuardScript);

// Trigger DOMContentLoaded
window.document.dispatchEvent(new window.Event('DOMContentLoaded'));

console.log('\n--- GENERATED SIDEBAR LINKS ---');
const sidebar = window.document.getElementById('sidebar-container');
if (sidebar) {
    const links = sidebar.querySelectorAll('a');
    links.forEach(a => {
        console.log(`Label: "${a.textContent.trim()}" | ID: "${a.id}" | Href: "${a.getAttribute('href')}" | Onclick: "${a.getAttribute('onclick') || 'NONE'}"`);
    });
} else {
    console.error('sidebar-container NOT FOUND!');
}
