(function() {
    // 1. Get path and page info
    const path = window.location.pathname;
    const pageName = path.substring(path.lastIndexOf('/') + 1) || 'dashboard.html';

    // 2. Exclude login.html and access-denied.html from auth checks
    if (pageName === 'login.html' || pageName === 'access-denied.html') {
        return;
    }

    // 3. Determine depth and session
    const isInternal = path.includes('/internal/');
    const isBank = path.includes('/bank/');
    let depth = '';
    let logoPath = '';
    
    const isLocalFile = window.location.protocol === 'file:';
    if (isLocalFile) {
        if (isBank) {
            depth = '../../';
            logoPath = '../../../assets/MULEGUARD_LOGO_W&G.png';
        } else if (isInternal) {
            depth = '../';
            logoPath = '../../assets/MULEGUARD_LOGO_W&G.png';
        } else {
            depth = '';
            logoPath = '../assets/MULEGUARD_LOGO_W&G.png';
        }
    } else {
        if (isBank) {
            depth = '../../';
        } else if (isInternal) {
            depth = '../';
        } else {
            depth = '';
        }
        logoPath = '/assets/MULEGUARD_LOGO_W&G.png';
    }

    const sessionStr = sessionStorage.getItem('muleguard_session');
    if (!sessionStr) {
        window.location.href = depth + 'login.html';
        return;
    }

    const session = JSON.parse(sessionStr);
    if (!session || !session.authenticated) {
        window.location.href = depth + 'login.html';
        return;
    }

    // 4. Access Control / Role-based Routing Protection
    const role = session.role; // 'bank_investigator', 'bank_compliance', 'internal_team'
    const subRole = session.subRole; // 'ai_ml', 'detection', 'system'

    if (isInternal && role !== 'internal_team') {
        window.location.href = depth + 'access-denied.html';
        return;
    }

    if (path.includes('/bank/investigator/') && role !== 'bank_investigator') {
        window.location.href = depth + 'access-denied.html';
        return;
    }

    if (path.includes('/bank/compliance/') && role !== 'bank_compliance') {
        window.location.href = depth + 'access-denied.html';
        return;
    }

    // Define navigation configurations
    const INVESTIGATOR_NAV = [
        {
            group: "COMMAND CENTER",
            items: [
                { id: "dashboard", label: "Dashboard", href: "dashboard.html", icon: "dashboard" },
                { id: "investigations", label: "Investigations", href: "investigations.html", icon: "search_insights" },
                { id: "transactions", label: "Transactions", href: "transactions.html", icon: "receipt_long" },
                { id: "entities", label: "Entities", href: "entities.html", icon: "group" },
                { id: "fraud_networks", label: "Fraud Networks", href: "fraud_networks.html", icon: "share" },
                { id: "alerts", label: "Alerts", href: "alerts.html", icon: "notifications_active" },
                { id: "cases", label: "Cases", href: "cases.html", icon: "work" }
            ]
        },
        {
            group: "INTELLIGENCE",
            items: [
                { id: "risk-analytics", label: "Risk Analytics", href: "#", icon: "monitoring", onClick: "showToast('Risk Analytics dashboard opened')" },
                { id: "network-intelligence", label: "Network Intelligence", href: "#", icon: "hub", onClick: "showToast('Network Intelligence graph database opened')" },
                { id: "watchlists", label: "Watchlists", href: "#", icon: "rule_folder", onClick: "showToast('Watchlist controls opened')" }
            ]
        }
    ];

    const COMPLIANCE_NAV = [
        {
            group: "COMPLIANCE CONTROL",
            items: [
                { id: "dashboard", label: "Dashboard", href: "dashboard.html", icon: "dashboard" },
                { id: "escalated-cases", label: "Escalated Cases", href: "escalated-cases.html", icon: "warning" },
                { id: "high-risk-alerts", label: "High-Risk Alerts", href: "high-risk-alerts.html", icon: "error" },
                { id: "decisions", label: "Decisions / Review", href: "decisions.html", icon: "gavel" },
                { id: "reports", label: "Reports", href: "reports.html", icon: "assessment" }
            ]
        },
        {
            group: "INVESTIGATION TOOLS",
            items: [
                { id: "investigations", label: "Investigations", href: "investigations.html", icon: "search_insights" },
                { id: "transactions", label: "Transactions", href: "transactions.html", icon: "receipt_long" },
                { id: "entities", label: "Entities", href: "entities.html", icon: "group" },
                { id: "fraud_networks", label: "Fraud Networks", href: "fraud_networks.html", icon: "share" },
                { id: "alerts", label: "Alerts", href: "alerts.html", icon: "notifications_active" },
                { id: "cases", label: "Cases", href: "cases.html", icon: "work" }
            ]
        },
        {
            group: "OVERSIGHT",
            items: [
                { id: "regulatory-filings", label: "Regulatory Filings", href: "#", icon: "description", onClick: "showToast('Regulatory filings queue opened')" },
                { id: "audit-trail", label: "Audit Trail", href: "#", icon: "history", onClick: "showToast('Compliance audit trails opened')" },
                { id: "compliance-watchlist", label: "Compliance Watchlist", href: "#", icon: "rule_folder", onClick: "showToast('Compliance watchlists opened')" }
            ]
        }
    ];

    const INTERNAL_NAV = [
        {
            group: "CONTROL CENTER",
            items: [
                { id: "health", label: "System Health", href: "dashboard.html#health", icon: "health_and_safety" },
                { id: "ml", label: "AI / ML Models", href: "dashboard.html#ml", icon: "psychology" },
                { id: "rules", label: "Detection Rules", href: "dashboard.html#rules", icon: "settings_applications" },
                { id: "graph", label: "Graph Engine", href: "dashboard.html#graph", icon: "hub" },
                { id: "data", label: "Synthetic Data", href: "dashboard.html#data", icon: "database" },
                { id: "logs", label: "Audit Logs", href: "dashboard.html#logs", icon: "receipt_long" }
            ]
        }
    ];

    // 5. Dynamic Sidebar Rendering and Navigation Highlights
    window.addEventListener('DOMContentLoaded', () => {
        const sidebarContainer = document.getElementById('sidebar-container');
        if (!sidebarContainer) return;

        const homePath = 'dashboard.html';
        let navHTML = '';

        // Select navigation config based on role
        let navConfig = INVESTIGATOR_NAV;
        if (role === 'bank_compliance') {
            navConfig = COMPLIANCE_NAV;
        } else if (role === 'internal_team') {
            navConfig = INTERNAL_NAV;
        }

        navHTML = `
            <div class="flex flex-col flex-1 overflow-y-auto">
                    <!-- Sidebar Header & Logo -->
                    <div class="h-[70px] flex items-center px-6 border-b border-[#1e293b] gap-3">
                            <a href="${homePath}">
                                    <img alt="MuleGuard Logo" class="w-[110px] h-auto object-contain" src="${logoPath}" />
                            </a>
                    </div>

                    <!-- Sidebar Menu Groups -->
                    <nav class="flex-1 px-4 py-6 space-y-7">
        `;

        navConfig.forEach(groupConfig => {
            navHTML += `
                        <div class="space-y-1">
                                <div class="px-3 mb-2">
                                        <span class="font-mono-technical text-[10px] text-on-primary-container tracking-wider uppercase opacity-55">${groupConfig.group}</span>
                                </div>
            `;

            groupConfig.items.forEach(item => {
                const clickAttr = item.onClick ? `onclick="${item.onClick}"` : '';
                navHTML += `
                                <a href="${item.href}" id="nav-link-${item.id}" ${clickAttr} class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-on-primary-container/70 font-body-md text-[14px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150">
                                        <span class="material-symbols-outlined text-[20px]">${item.icon}</span>
                                        <span>${item.label}</span>
                                </a>
                `;
            });

            navHTML += `
                        </div>
            `;
        });

        navHTML += `
                    </nav>
            </div>
        `;

        // Add common sidebar footer
        navHTML += `
                <!-- Sidebar Footer Status -->
                <div class="p-4 border-t border-[#1e293b] space-y-4">
                        <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                        <span class="inline-block w-2 h-2 rounded-full bg-risk-low animate-pulse"></span>
                                        <span class="font-mono-technical text-[10px] text-[#38BDF8] tracking-wider uppercase">Systems OK</span>
                                </div>
                                <span class="font-mono-technical text-[10px] text-on-primary-container/40">v1.2.4</span>
                        </div>
                        <div class="flex items-center justify-between p-2 rounded-lg bg-primary/20 border border-[#1e293b]">
                                <div class="flex items-center gap-3 w-[180px] overflow-hidden">
                                        <div class="w-9 h-9 rounded-full bg-secondary-container/30 border border-[#316bf3]/30 flex items-center justify-center font-headline-md text-[13px] text-on-primary font-bold shrink-0">
                                                ${session.user.name.split(' ').map(n => n[0]).join('')}
                                        </div>
                                        <div class="flex flex-col overflow-hidden">
                                                <span class="font-headline-md text-[13px] text-on-primary font-semibold leading-tight truncate">${session.user.name}</span>
                                                <span class="font-body-md text-[11px] text-on-primary-container/50 truncate">${session.user.title}</span>
                                        </div>
                                </div>
                                <button class="text-on-primary-container/50 hover:text-on-primary transition-colors focus:outline-none" onclick="showToast('Settings opened.')">
                                        <span class="material-symbols-outlined text-[20px]">settings</span>
                                </button>
                        </div>
                </div>
        `;

        sidebarContainer.innerHTML = navHTML;

        // Set active link highlight based on current pageName and hash
        let activeLinkId = 'nav-link-' + pageName.replace('.html', '');
        if (role === 'internal_team') {
            const hash = window.location.hash ? window.location.hash.substring(1) : 'health';
            activeLinkId = 'nav-link-' + hash;
        }

        const activeLink = document.getElementById(activeLinkId);
        if (activeLink) {
            // Convert it to active styling
            activeLink.className = 'flex items-center gap-3 px-3 py-2.5 rounded-lg text-on-primary font-body-md text-[14px] bg-secondary-container/25 border-l-2 border-secondary-container hover:bg-secondary-container/30 transition-all duration-150';
            const icon = activeLink.querySelector('.material-symbols-outlined');
            if (icon) icon.className = 'material-symbols-outlined text-[20px] text-secondary-container';
            const textSpan = activeLink.querySelector('span:not(.material-symbols-outlined)');
            if (textSpan) textSpan.classList.add('font-medium');
        }

        // Set global header and sidebar user profile texts elsewhere on the page
        const headerNameEl = document.querySelector('header div.flex.items-center.gap-5 div.relative.cursor-pointer.group div.flex.items-center.gap-2 span.hidden.sm\\:inline');
        const headerAvatarEl = document.querySelector('header div.relative.cursor-pointer.group div.flex.items-center.gap-2 div.rounded-full');

        if (headerNameEl) headerNameEl.textContent = session.user.name;
        if (headerAvatarEl) {
            headerAvatarEl.textContent = session.user.name.split(' ').map(n => n[0]).join('');
        }
    });

    // Expose logoutUser globally
    window.logoutUser = function() {
        sessionStorage.removeItem('muleguard_session');
        const path = window.location.pathname;
        const depth = path.includes('/bank/') ? '../../' : (path.includes('/internal/') ? '../' : '');
        window.location.href = depth + 'login.html';
    };
})();

