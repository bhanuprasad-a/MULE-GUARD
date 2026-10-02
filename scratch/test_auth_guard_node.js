const fs = require('fs');
const path = require('path');

// Mock browser globals
global.window = {
    location: {
        pathname: '/frontend/bank/investigator/dashboard.html',
        protocol: 'http:'
    },
    addEventListener: function(event, callback) {
        if (event === 'DOMContentLoaded') {
            this.onDOMContentLoaded = callback;
        }
    }
};

global.sessionStorage = {
    getItem: function(key) {
        if (key === 'muleguard_session') {
            return JSON.stringify({
                authenticated: true,
                role: 'bank_investigator',
                subRole: 'detection',
                user: { name: 'A. Kumar', title: 'Senior Analyst' }
            });
        }
        return null;
    }
};

let innerHTMLVal = '';
const mockSidebar = {
    id: 'sidebar-container',
    set innerHTML(val) {
        innerHTMLVal = val;
    },
    get innerHTML() {
        return innerHTMLVal;
    }
};

global.document = {
    getElementById: function(id) {
        if (id === 'sidebar-container') return mockSidebar;
        return null;
    },
    querySelector: function() { return null; }
};

// Load auth-guard.js
const authGuardCode = fs.readFileSync(path.join(__dirname, '../frontend/scripts/auth-guard.js'), 'utf8');
eval(authGuardCode);

// Trigger DOMContentLoaded
if (global.window.onDOMContentLoaded) {
    global.window.onDOMContentLoaded();
}

console.log('=== RENDERED SIDEBAR HTML IN AUTH-GUARD ===');
console.log(innerHTMLVal);
