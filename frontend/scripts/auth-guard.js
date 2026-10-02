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
    const isCompliance = path.includes('/bank/compliance/');
    const isBank = path.includes('/bank/');
    let depth = '';
    let logoPath = '';
    
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

    let session = null;
    const sessionStr = sessionStorage.getItem('muleguard_session');
    if (sessionStr) {
        try {
            session = JSON.parse(sessionStr);
        } catch (_) {
            session = null;
        }
    }

    const defaultRole = isInternal ? 'internal_team' : (isCompliance ? 'bank_compliance' : 'bank_investigator');
    const role = (session && session.role) ? session.role : defaultRole;
    const subRole = session ? session.subRole : null;

    if (!session || !session.authenticated) {
        if (typeof document !== 'undefined') {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initSidebar);
            } else {
                initSidebar();
            }
        }
        window.location.href = depth + 'login.html';
        return;
    }

    // Backend Session Integrity Handshake (if running over HTTP/HTTPS)
    if (typeof window !== 'undefined' && window.location && window.location.protocol.startsWith('http') && typeof fetch === 'function') {
        fetch('/api/v1/auth/me')
            .then(res => {
                if (res.status === 401) {
                    sessionStorage.removeItem('muleguard_session');
                    window.location.href = depth + 'login.html';
                } else if (res.ok) {
                    return res.json();
                }
            })
            .then(data => {
                if (data && data.user) {
                    const curSession = JSON.parse(sessionStorage.getItem('muleguard_session') || '{}');
                    curSession.user = Object.assign({}, curSession.user || {}, data.user);
                    curSession.role = data.user.role || curSession.role;
                    curSession.authenticated = true;
                    sessionStorage.setItem('muleguard_session', JSON.stringify(curSession));
                }
            })
            .catch(() => {
                // If network transiently drops, retain active session locally
            });
    }

    // Auto-load Shared Profile & Settings Right Drawer
    if (typeof document !== 'undefined') {
        const drawerScriptId = 'muleguard-profile-drawer-script';
        if (!document.getElementById(drawerScriptId)) {
            const script = document.createElement('script');
            script.id = drawerScriptId;
            script.src = depth + 'scripts/profile-drawer.js';
            document.head.appendChild(script);
        }
    }

    // 4. Access Control / Role-based Routing Protection
    if (isInternal && role !== 'internal_team') {
        if (typeof document !== 'undefined') {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initSidebar);
            } else {
                initSidebar();
            }
        }
        window.location.href = depth + 'access-denied.html';
        return;
    }

    if (path.includes('/bank/investigator/') && role !== 'bank_investigator') {
        if (typeof document !== 'undefined') {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initSidebar);
            } else {
                initSidebar();
            }
        }
        window.location.href = depth + 'access-denied.html';
        return;
    }

    if (path.includes('/bank/compliance/') && role !== 'bank_compliance') {
        if (typeof document !== 'undefined') {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initSidebar);
            } else {
                initSidebar();
            }
        }
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
                { id: "risk-analytics", label: "Risk Analytics", href: "risk-analytics.html", icon: "monitoring" },
                { id: "network-intelligence", label: "Network Intelligence", href: "network-intelligence.html", icon: "hub" },
                { id: "watchlists", label: "Watchlists", href: "watchlists.html", icon: "rule_folder" }
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
                { id: "network-intelligence", label: "Network Intelligence", href: "network-intelligence.html", icon: "hub" },
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
    // Inject global collapsible sidebar stylesheet
    if (typeof document !== 'undefined' && typeof document.createElement === 'function') {
        const styleId = 'muleguard-collapsible-sidebar-css';
        if (!document.getElementById(styleId)) {
            const style = document.createElement('style');
            style.id = styleId;
            style.textContent = `
                #sidebar-container {
                    transition: width 0.22s cubic-bezier(0.4, 0, 0.2, 1), transform 0.3s ease-in-out !important;
                }
                @media (min-width: 768px) {
                    div.md\\:pl-\\[280px\\],
                    main.md\\:pl-\\[280px\\],
                    div[class*="md:pl-[280px]"],
                    div[class*="md:pl-[260px]"],
                    #main-content-layout {
                        transition: padding-left 0.22s cubic-bezier(0.4, 0, 0.2, 1) !important;
                    }
                    body.sidebar-collapsed div.md\\:pl-\\[280px\\],
                    body.sidebar-collapsed main.md\\:pl-\\[280px\\],
                    body.sidebar-collapsed div[class*="md:pl-[280px]"],
                    body.sidebar-collapsed div[class*="md:pl-[260px]"],
                    body.sidebar-collapsed #main-content-layout,
                    html.sidebar-collapsed div.md\\:pl-\\[280px\\],
                    html.sidebar-collapsed main.md\\:pl-\\[280px\\],
                    html.sidebar-collapsed div[class*="md:pl-[280px]"],
                    html.sidebar-collapsed div[class*="md:pl-[260px]"],
                    html.sidebar-collapsed #main-content-layout {
                        padding-left: 72px !important;
                    }
                    body.sidebar-collapsed #sidebar-container,
                    html.sidebar-collapsed #sidebar-container {
                        width: 72px !important;
                    }
                }
                body.sidebar-collapsed .sidebar-text,
                body.sidebar-collapsed .sidebar-group-header,
                body.sidebar-collapsed .sidebar-footer-text,
                body.sidebar-collapsed .sidebar-logo-full,
                body.sidebar-collapsed .sidebar-footer-status,
                html.sidebar-collapsed .sidebar-text,
                html.sidebar-collapsed .sidebar-group-header,
                html.sidebar-collapsed .sidebar-footer-text,
                html.sidebar-collapsed .sidebar-logo-full,
                html.sidebar-collapsed .sidebar-footer-status {
                    display: none !important;
                }
                body.sidebar-collapsed .sidebar-logo-compact,
                html.sidebar-collapsed .sidebar-logo-compact,
                body.sidebar-collapsed a[title="MuleGuard Home"],
                html.sidebar-collapsed a[title="MuleGuard Home"] {
                    display: none !important;
                }
                body.sidebar-collapsed #sidebar-container nav,
                html.sidebar-collapsed #sidebar-container nav {
                    padding-left: 0.5rem !important;
                    padding-right: 0.5rem !important;
                }
                body.sidebar-collapsed #sidebar-container nav a,
                html.sidebar-collapsed #sidebar-container nav a {
                    justify-content: center !important;
                    padding-left: 0 !important;
                    padding-right: 0 !important;
                    gap: 0 !important;
                }
                body.sidebar-collapsed #sidebar-container .h-\\[70px\\],
                html.sidebar-collapsed #sidebar-container .h-\\[70px\\] {
                    padding-left: 0 !important;
                    padding-right: 0 !important;
                    justify-content: center !important;
                }
                body.sidebar-collapsed #sidebar-toggle-btn,
                html.sidebar-collapsed #sidebar-toggle-btn {
                    margin: 0 auto !important;
                }
                body.sidebar-collapsed #sidebar-container .p-2.rounded-lg.bg-primary\\/20,
                html.sidebar-collapsed #sidebar-container .p-2.rounded-lg.bg-primary\\/20 {
                    justify-content: center !important;
                    padding: 0.35rem !important;
                }
                body.sidebar-collapsed #sidebar-container .p-2.rounded-lg.bg-primary\\/20 > div,
                html.sidebar-collapsed #sidebar-container .p-2.rounded-lg.bg-primary\\/20 > div {
                    gap: 0 !important;
                    justify-content: center !important;
                    margin: 0 auto !important;
                }
                body.sidebar-collapsed #sidebar-container .p-2.rounded-lg.bg-primary\\/20 button,
                html.sidebar-collapsed #sidebar-container .p-2.rounded-lg.bg-primary\\/20 button {
                    display: none !important;
                }
            `;
            (document.head || document.documentElement).appendChild(style);
        }

        // Apply collapsed state before render to avoid flash (safe check for head execution)
        if (typeof localStorage !== 'undefined' && localStorage.getItem('muleguard_sidebar_collapsed') === 'true') {
            if (document.documentElement) {
                document.documentElement.classList.add('sidebar-collapsed');
            }
            if (document.body) {
                document.body.classList.add('sidebar-collapsed');
            }
        }
    }

    window.toggleMuleGuardSidebar = function() {
        const isCollapsed = document.body ? document.body.classList.toggle('sidebar-collapsed') : false;
        if (document.documentElement) {
            document.documentElement.classList.toggle('sidebar-collapsed', isCollapsed);
        }
        localStorage.setItem('muleguard_sidebar_collapsed', isCollapsed ? 'true' : 'false');
        const icon = document.getElementById('sidebar-toggle-icon');
        if (icon) {
            icon.textContent = isCollapsed ? 'menu' : 'menu_open';
        }
        const btn = document.getElementById('sidebar-toggle-btn');
        if (btn) {
            btn.title = isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar';
            btn.setAttribute('aria-expanded', isCollapsed ? 'false' : 'true');
        }
        setTimeout(() => {
            window.dispatchEvent(new Event('resize'));
        }, 240);
    };

    // Global fallback for mobile sidebar drawer toggle
    if (typeof window !== 'undefined' && typeof window.toggleMobileSidebar !== 'function') {
        window.toggleMobileSidebar = function() {
            const sidebar = document.getElementById('sidebar-container');
            const overlay = document.getElementById('sidebar-overlay');
            if (!sidebar) return;
            if (sidebar.classList.contains('-translate-x-full')) {
                sidebar.classList.remove('-translate-x-full');
                if (overlay) overlay.classList.remove('hidden');
            } else {
                sidebar.classList.add('-translate-x-full');
                if (overlay) overlay.classList.add('hidden');
            }
        };
    }

    // Global fallback for showToast if not present on page
    if (typeof window !== 'undefined' && typeof window.showToast !== 'function') {
        window.showToast = function(msg) {
            const existingToast = document.getElementById('toast');
            if (existingToast) {
                const toastText = document.getElementById('toast-text');
                if (toastText) toastText.textContent = msg;
                existingToast.classList.remove('translate-y-20', 'opacity-0', 'pointer-events-none');
                existingToast.classList.add('translate-y-0', 'opacity-100');
                setTimeout(() => {
                    existingToast.classList.remove('translate-y-0', 'opacity-100');
                    existingToast.classList.add('translate-y-20', 'opacity-0', 'pointer-events-none');
                }, 2800);
            } else {
                console.log('[MuleGuard]', msg);
            }
        };
    }

    function initSidebar() {
        const sidebarContainer = document.getElementById('sidebar-container');
        if (!sidebarContainer) return;

        const effectiveRole = (session && session.role) ? session.role : (isInternal ? 'internal_team' : (isCompliance ? 'bank_compliance' : 'bank_investigator'));
        const homePath = isInternal ? 'dashboard.html#health' : 'dashboard.html';

        // Safe User Metadata with Institutional Fallbacks
        const userName = (session && session.user && typeof session.user.name === 'string' && session.user.name.trim())
            ? session.user.name.trim()
            : (effectiveRole === 'bank_compliance' ? 'A. Kumar' : (effectiveRole === 'internal_team' ? 'T. Miller' : 'J. Doe'));

        const userTitle = (session && session.user && typeof session.user.title === 'string' && session.user.title.trim())
            ? session.user.title.trim()
            : (effectiveRole === 'bank_compliance' ? 'Senior Compliance Officer' : (effectiveRole === 'internal_team' ? 'Platform Operations Lead' : 'Senior Fraud Investigator'));

        const userInitials = userName.split(/\s+/).filter(Boolean).map(n => n[0]).join('').substring(0, 2).toUpperCase() || 'MG';

        const isInitiallyCollapsed = (typeof localStorage !== 'undefined' && localStorage.getItem('muleguard_sidebar_collapsed') === 'true');
        if (isInitiallyCollapsed) {
            if (document.body) document.body.classList.add('sidebar-collapsed');
            if (document.documentElement) document.documentElement.classList.add('sidebar-collapsed');
        } else {
            if (document.body) document.body.classList.remove('sidebar-collapsed');
            if (document.documentElement) document.documentElement.classList.remove('sidebar-collapsed');
        }

        const initialIcon = isInitiallyCollapsed ? 'menu' : 'menu_open';
        const initialTitle = isInitiallyCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar';

        // Always hydrate with full dynamic markup matching the effective institutional role
        const renderedRole = sidebarContainer.getAttribute('data-rendered-role');
        if (renderedRole !== effectiveRole) {
            let navConfig = INVESTIGATOR_NAV;
            if (effectiveRole === 'bank_compliance') {
                navConfig = COMPLIANCE_NAV;
            } else if (effectiveRole === 'internal_team') {
                navConfig = INTERNAL_NAV;
            }

            let navHTML = `
                <div class="flex flex-col flex-1 overflow-y-auto">
                        <!-- Sidebar Header & Logo with Collapsible Toggle -->
                        <div class="h-[70px] flex items-center justify-between px-5 border-b border-[#1e293b] select-none">
                                <a href="${homePath}" class="flex items-center gap-2 overflow-hidden" title="MuleGuard Home">
                                        <img alt="MuleGuard Logo" class="sidebar-logo-full w-[110px] h-auto object-contain transition-all" src="${logoPath}" />
                                        <span class="sidebar-logo-compact hidden font-mono-technical font-extrabold text-[16px] text-secondary-container tracking-wider">MG</span>
                                </a>
                                <button id="sidebar-toggle-btn" onclick="toggleMuleGuardSidebar()" title="${initialTitle}" aria-label="Toggle Sidebar" aria-expanded="${!isInitiallyCollapsed}" class="text-on-primary-container/70 hover:text-on-primary p-1.5 rounded-lg hover:bg-secondary-container/20 transition-all focus:outline-none focus:ring-1 focus:ring-secondary/40 shrink-0">
                                        <span class="material-symbols-outlined text-[20px] transition-transform duration-200" id="sidebar-toggle-icon">${initialIcon}</span>
                                </button>
                        </div>

                        <!-- Sidebar Menu Groups -->
                        <nav class="flex-1 px-4 py-6 space-y-7">
            `;

            navConfig.forEach(groupConfig => {
                navHTML += `
                            <div class="space-y-1">
                                    <div class="px-3 mb-2 sidebar-group-header">
                                            <span class="font-mono-technical text-[10px] text-on-primary-container tracking-wider uppercase opacity-55">${groupConfig.group}</span>
                                    </div>
                `;

                groupConfig.items.forEach(item => {
                    const clickAttr = item.onClick ? `onclick="${item.onClick}"` : '';
                    navHTML += `
                                    <a href="${item.href}" id="nav-link-${item.id}" ${clickAttr} title="${item.label}" class="nav-item-link flex items-center gap-3 px-3 py-2.5 rounded-lg text-on-primary-container/70 font-body-md text-[14px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150">
                                            <span class="material-symbols-outlined text-[20px] shrink-0">${item.icon}</span>
                                            <span class="sidebar-text truncate">${item.label}</span>
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
                    <div class="p-3 border-t border-[#1e293b] space-y-3">
                            <div class="sidebar-footer-status flex items-center justify-between px-1">
                                    <div class="flex items-center gap-2">
                                            <span class="inline-block w-2 h-2 rounded-full bg-risk-low animate-pulse"></span>
                                            <span class="font-mono-technical text-[10px] text-[#38BDF8] tracking-wider uppercase">Systems OK</span>
                                    </div>
                                    <span class="font-mono-technical text-[10px] text-on-primary-container/40">v1.2.4</span>
                            </div>
                            <div class="flex items-center justify-between p-2 rounded-lg bg-primary/20 border border-[#1e293b] cursor-pointer hover:bg-primary/30 transition-colors" onclick="if(window.openProfileDrawer)window.openProfileDrawer('profile')" title="View Institutional Profile">
                                    <div class="flex items-center gap-3 overflow-hidden">
                                            <div class="w-8 h-8 rounded-full bg-secondary-container/30 border border-[#316bf3]/30 flex items-center justify-center font-headline-md text-[12px] text-on-primary font-bold shrink-0">
                                                    ${userInitials}
                                            </div>
                                            <div class="sidebar-footer-text flex flex-col overflow-hidden">
                                                    <span class="font-headline-md text-[13px] text-on-primary font-semibold leading-tight truncate">${userName}</span>
                                                    <span class="font-body-md text-[11px] text-on-primary-container/50 truncate">${userTitle}</span>
                                            </div>
                                    </div>
                                    <button class="sidebar-footer-text text-on-primary-container/50 hover:text-on-primary transition-colors focus:outline-none ml-1 p-1 rounded hover:bg-secondary-container/20" onclick="event.stopPropagation(); if(window.openProfileDrawer)window.openProfileDrawer('settings'); else showToast('Settings opened.');" title="Settings">
                                            <span class="material-symbols-outlined text-[18px]">settings</span>
                                    </button>
                            </div>
                    </div>
            `;

            sidebarContainer.innerHTML = navHTML;
            sidebarContainer.setAttribute('data-rendered-role', effectiveRole);
        }

        // Set active link highlight based on current pageName and hash
        let activeLinkId = 'nav-link-' + pageName.replace('.html', '');
        if (effectiveRole === 'internal_team') {
            const hash = (window.location.hash ? window.location.hash.substring(1) : '') || 'health';
            activeLinkId = 'nav-link-' + hash;
        }

        // Synchronize active and inactive link classes
        const allNavLinks = (typeof sidebarContainer.querySelectorAll === 'function')
            ? sidebarContainer.querySelectorAll('a.nav-item-link')
            : [];
        allNavLinks.forEach(link => {
            if (link.id === activeLinkId) {
                link.className = 'nav-item-link flex items-center gap-3 px-3 py-2.5 rounded-lg text-on-primary font-body-md text-[14px] bg-secondary-container/25 border-l-2 border-secondary-container hover:bg-secondary-container/30 transition-all duration-150';
                const icon = link.querySelector ? link.querySelector('.material-symbols-outlined') : null;
                if (icon) icon.className = 'material-symbols-outlined text-[20px] text-secondary-container shrink-0';
                const textSpan = link.querySelector ? link.querySelector('span:not(.material-symbols-outlined)') : null;
                if (textSpan) textSpan.classList.add('font-medium');
            } else {
                link.className = 'nav-item-link flex items-center gap-3 px-3 py-2.5 rounded-lg text-on-primary-container/70 font-body-md text-[14px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150';
                const icon = link.querySelector ? link.querySelector('.material-symbols-outlined') : null;
                if (icon) icon.className = 'material-symbols-outlined text-[20px] shrink-0';
                const textSpan = link.querySelector ? link.querySelector('span:not(.material-symbols-outlined)') : null;
                if (textSpan) textSpan.classList.remove('font-medium');
            }
        });

        // Set global header and sidebar user profile texts elsewhere on the page
        try {
            const headerNameEl = document.querySelector('header div.flex.items-center.gap-5 div.relative.cursor-pointer.group div.flex.items-center.gap-2 span.hidden.sm\\:inline') || document.getElementById('header-username');
            const headerAvatarEl = document.querySelector('header div.relative.cursor-pointer.group div.flex.items-center.gap-2 div.rounded-full') || document.getElementById('header-avatar');

            if (headerNameEl) headerNameEl.textContent = userName;
            if (headerAvatarEl) headerAvatarEl.textContent = userInitials;
        } catch (_) {}
    }

    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initSidebar);
        } else {
            initSidebar();
        }
    }
    if (typeof window !== 'undefined') {
        window.addEventListener('DOMContentLoaded', initSidebar);
        window.addEventListener('hashchange', initSidebar);
    }

    // Expose logoutUser globally
    window.logoutUser = function() {
        if (typeof fetch === 'function') {
            try {
                fetch('/api/v1/auth/logout', { method: 'POST' }).catch(() => {});
            } catch (_) {}
        }
        sessionStorage.removeItem('muleguard_session');
        const path = window.location.pathname;
        const depth = path.includes('/bank/') ? '../../' : (path.includes('/internal/') ? '../' : '');
        window.location.href = depth + 'login.html';
    };
})();

