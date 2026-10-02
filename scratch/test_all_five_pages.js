const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const pages = [
    'frontend/bank/investigator/dashboard.html',
    'frontend/bank/investigator/alerts.html',
    'frontend/bank/investigator/risk-analytics.html',
    'frontend/bank/investigator/network-intelligence.html',
    'frontend/bank/investigator/watchlists.html'
];

pages.forEach(p => {
    console.log('\n========================================');
    console.log('Testing page:', p);
    console.log('========================================');

    const virtualConsole = new VirtualConsole();
    virtualConsole.on('error', (err) => console.error('  BROWSER ERROR:', err));
    virtualConsole.on('warn', (msg) => console.warn('  BROWSER WARN:', msg));
    virtualConsole.on('log', (msg) => {});

    const htmlPath = path.join(__dirname, '..', p);
    const htmlContent = fs.readFileSync(htmlPath, 'utf8');

    const dom = new JSDOM(htmlContent, {
        url: 'http://localhost:8000/' + p,
        runScripts: 'dangerously',
        resources: 'usable',
        virtualConsole
    });

    const { window } = dom;

    window.sessionStorage.setItem('muleguard_session', JSON.stringify({
        authenticated: true,
        role: 'bank_investigator',
        user: { name: 'J. Doe', title: 'Senior Fraud Investigator' }
    }));

    // In JSDOM with 'usable' resources, local scripts may need to be loaded if fetch/external fails,
    // but let's check what auth-guard.js does
    const authGuardScript = fs.readFileSync(path.join(__dirname, '../frontend/scripts/auth-guard.js'), 'utf8');
    window.eval(authGuardScript);

    // Dispatch DOMContentLoaded
    window.document.dispatchEvent(new window.Event('DOMContentLoaded'));

    const sidebar = window.document.getElementById('sidebar-container');
    if (!sidebar) {
        console.error('  FAIL: #sidebar-container NOT FOUND!');
        return;
    }

    const toggleBtn = window.document.getElementById('sidebar-toggle-btn');
    console.log('  #sidebar-toggle-btn exists:', !!toggleBtn);
    if (toggleBtn) {
        console.log('    Toggle onclick:', toggleBtn.getAttribute('onclick'));
    }

    const toggleIcon = window.document.getElementById('sidebar-toggle-icon');
    console.log('  Initial toggle icon:', toggleIcon ? toggleIcon.textContent : 'NONE');

    // Test toggle function
    console.log('  window.toggleMuleGuardSidebar is function:', typeof window.toggleMuleGuardSidebar === 'function');

    if (typeof window.toggleMuleGuardSidebar === 'function') {
        // Test collapse
        window.toggleMuleGuardSidebar();
        const isCollapsed = window.document.body.classList.contains('sidebar-collapsed');
        console.log('  After toggle 1 -> body.sidebar-collapsed:', isCollapsed, '| icon:', toggleIcon ? toggleIcon.textContent : 'NONE');

        // Test expand
        window.toggleMuleGuardSidebar();
        const isExpanded = !window.document.body.classList.contains('sidebar-collapsed');
        console.log('  After toggle 2 -> body expanded:', isExpanded, '| icon:', toggleIcon ? toggleIcon.textContent : 'NONE');
    }

    // Check active navigation link
    const activeLink = sidebar.querySelector('a.nav-item-link.bg-secondary-container\\/25') || sidebar.querySelector('a[class*="bg-secondary-container"]');
    console.log('  Active link highlighted:', activeLink ? activeLink.textContent.trim() : 'NONE');
});
