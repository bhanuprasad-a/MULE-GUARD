/**
 * MuleGuard Shared Profile & Settings Right-Side Drawer
 * Unified across Investigator, Compliance Officer, and Platform Administrator roles.
 */
(function() {
    // Prevent duplicate initialization
    if (window.__MuleGuardProfileDrawerInitialized) return;
    window.__MuleGuardProfileDrawerInitialized = true;

    // Role display mappings
    const ROLE_LABELS = {
        'bank_investigator': 'Bank Fraud Investigator',
        'bank_compliance': 'AML Compliance Officer',
        'internal_team': 'Platform Administrator'
    };

    const ROLE_BADGE_CLASSES = {
        'bank_investigator': 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30',
        'bank_compliance': 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30',
        'internal_team': 'bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/30'
    };

    const ROLE_PERMISSIONS = {
        'bank_investigator': 'Level 2 Authorization • Ledger Read/Write • Case Triage',
        'bank_compliance': 'Level 3 Authorization • Regulatory Filing • Escalation Decision',
        'internal_team': 'Root System Access • Model Tuning • Security & Health'
    };

    // Global drawer state
    let activeTab = 'profile'; // 'profile' | 'settings'
    let cachedUser = null;

    // Inject drawer styles
    function injectDrawerStyles() {
        if (document.getElementById('muleguard-profile-drawer-styles')) return;
        const style = document.createElement('style');
        style.id = 'muleguard-profile-drawer-styles';
        style.textContent = `
            #muleguard-profile-drawer-overlay {
                transition: opacity 0.28s cubic-bezier(0.4, 0, 0.2, 1);
            }
            #muleguard-profile-drawer {
                transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1);
            }
            .drawer-tab-active {
                border-bottom: 2px solid #316bf3 !important;
                color: #316bf3 !important;
                font-weight: 600 !important;
            }
            .drawer-tab-inactive {
                border-bottom: 2px solid transparent !important;
                color: #64748b !important;
                font-weight: 500 !important;
            }
            .drawer-tab-inactive:hover {
                color: #0f172a !important;
            }
            .switch-checkbox:checked + .switch-label {
                background-color: #316bf3 !important;
            }
            .switch-checkbox:checked + .switch-label .switch-knob {
                transform: translateX(18px) !important;
            }
        `;
        document.head.appendChild(style);
    }

    // Build the drawer HTML structure
    function createDrawerDOM() {
        if (document.getElementById('muleguard-profile-drawer')) return;

        // Overlay backdrop
        const overlay = document.createElement('div');
        overlay.id = 'muleguard-profile-drawer-overlay';
        overlay.className = 'fixed inset-0 bg-primary/40 backdrop-blur-sm z-[90] transition-opacity duration-300 opacity-0 pointer-events-none';
        overlay.setAttribute('aria-hidden', 'true');
        overlay.onclick = () => window.closeProfileDrawer();

        // Right-side Drawer
        const drawer = document.createElement('aside');
        drawer.id = 'muleguard-profile-drawer';
        drawer.className = 'fixed inset-y-0 right-0 z-[100] w-full sm:w-[460px] md:w-[480px] bg-interface-base border-l border-outline-variant/40 shadow-2xl transform translate-x-full transition-transform duration-300 ease-in-out select-none flex flex-col';
        drawer.setAttribute('role', 'dialog');
        drawer.setAttribute('aria-modal', 'true');
        drawer.setAttribute('aria-label', 'User Profile and Settings');

        drawer.innerHTML = `
            <!-- Drawer Header -->
            <div class="h-[70px] border-b border-outline-variant/30 flex items-center justify-between px-6 bg-surface-container-low shrink-0">
                <div class="flex items-center gap-3">
                    <div class="w-9 h-9 rounded-lg bg-secondary-container/20 border border-secondary-container/30 flex items-center justify-center text-secondary-container">
                        <span class="material-symbols-outlined text-[20px]" id="drawer-header-icon">badge</span>
                    </div>
                    <div>
                        <h2 class="font-headline-md text-[16px] text-on-surface font-bold tracking-tight" id="drawer-header-title">Institutional Profile</h2>
                        <p class="font-body-md text-[11px] text-on-surface-variant leading-none" id="drawer-header-sub">MuleGuard Core Security Protocol</p>
                    </div>
                </div>
                <button type="button" onclick="closeProfileDrawer()" class="w-8 h-8 rounded-lg flex items-center justify-center text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors focus:outline-none focus:ring-1 focus:ring-secondary/40" title="Close Drawer (ESC)" aria-label="Close">
                    <span class="material-symbols-outlined text-[20px]">close</span>
                </button>
            </div>

            <!-- Tab Switcher Navigation -->
            <div class="flex border-b border-outline-variant/30 bg-interface-base px-6 shrink-0">
                <button type="button" id="tab-btn-profile" onclick="switchDrawerTab('profile')" class="flex items-center gap-2 py-3 px-4 font-body-md text-[13px] drawer-tab-active transition-all focus:outline-none">
                    <span class="material-symbols-outlined text-[18px]">person</span>
                    <span>My Profile</span>
                </button>
                <button type="button" id="tab-btn-settings" onclick="switchDrawerTab('settings')" class="flex items-center gap-2 py-3 px-4 font-body-md text-[13px] drawer-tab-inactive transition-all focus:outline-none">
                    <span class="material-symbols-outlined text-[18px]">settings</span>
                    <span>Preferences & Settings</span>
                </button>
            </div>

            <!-- Drawer Body Scrollable Content -->
            <div class="flex-1 overflow-y-auto p-6 space-y-6">
                <!-- TAB 1: PROFILE VIEW -->
                <div id="drawer-tab-profile-content" class="space-y-6">
                    <!-- Profile Card -->
                    <div class="p-5 rounded-2xl bg-surface-container-low border border-outline-variant/40 flex items-center gap-4">
                        <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-primary to-secondary-container flex items-center justify-center text-white font-headline-md font-bold text-[22px] shadow-md border-2 border-white/20 shrink-0" id="drawer-profile-avatar">
                            --
                        </div>
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-2 mb-1">
                                <h3 class="font-headline-md text-[17px] text-on-surface font-bold truncate" id="drawer-profile-name">Loading...</h3>
                                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono-technical font-bold border shrink-0" id="drawer-profile-role-badge">STAFF</span>
                            </div>
                            <p class="font-body-md text-[12px] text-on-surface-variant truncate" id="drawer-profile-title">Institutional Officer</p>
                            <p class="font-mono-technical text-[11px] text-secondary-container font-semibold mt-0.5 truncate" id="drawer-profile-empid">ID: ---</p>
                        </div>
                    </div>

                    <!-- Institutional Credential Details -->
                    <div class="space-y-3">
                        <div class="flex items-center justify-between">
                            <span class="font-mono-technical text-[11px] uppercase tracking-wider text-on-surface-variant font-bold">Institutional Credentials</span>
                            <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-600 text-[11px] font-mono-technical font-semibold border border-emerald-500/20">
                                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                                ACTIVE
                            </span>
                        </div>

                        <div class="rounded-xl border border-outline-variant/40 divide-y divide-outline-variant/20 bg-interface-base text-[13px]">
                            <div class="flex justify-between items-center py-2.5 px-3.5">
                                <span class="text-on-surface-variant font-medium">Department</span>
                                <span class="text-on-surface font-semibold" id="drawer-detail-dept">--</span>
                            </div>
                            <div class="flex justify-between items-center py-2.5 px-3.5">
                                <span class="text-on-surface-variant font-medium">Official Email</span>
                                <span class="text-on-surface font-mono-technical text-[12px]" id="drawer-detail-email">--</span>
                            </div>
                            <div class="flex justify-between items-center py-2.5 px-3.5">
                                <span class="text-on-surface-variant font-medium">Access Tier</span>
                                <span class="text-on-surface text-[12px] text-right font-medium" id="drawer-detail-access">--</span>
                            </div>
                            <div class="flex justify-between items-center py-2.5 px-3.5">
                                <span class="text-on-surface-variant font-medium">Account Status</span>
                                <span class="text-emerald-600 font-semibold text-[12px] flex items-center gap-1">
                                    <span class="material-symbols-outlined text-[15px]">verified</span>
                                    <span>Verified Personnel</span>
                                </span>
                            </div>
                        </div>
                    </div>

                    <!-- Security & Biometrics Card -->
                    <div class="space-y-3">
                        <span class="font-mono-technical text-[11px] uppercase tracking-wider text-on-surface-variant font-bold">Biometric & Authentication Proof</span>
                        <div class="p-4 rounded-xl border border-outline-variant/40 bg-surface-container-low space-y-3">
                            <div class="flex items-start gap-3">
                                <div class="w-8 h-8 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-600 shrink-0">
                                    <span class="material-symbols-outlined text-[18px]">face</span>
                                </div>
                                <div>
                                    <div class="font-headline-md text-[13px] font-bold text-on-surface">Face Biometrics Active</div>
                                    <p class="font-body-md text-[11px] text-on-surface-variant mt-0.5 leading-snug" id="drawer-detail-face">Enrolled & Biometrically Verified (OpenCV SFace 128-D)</p>
                                </div>
                            </div>
                            <div class="pt-2 border-t border-outline-variant/20 flex justify-between items-center text-[11px]">
                                <span class="text-on-surface-variant font-medium">Last Login Handshake</span>
                                <span class="font-mono-technical text-on-surface font-semibold" id="drawer-detail-lastlogin">--</span>
                            </div>
                            <div class="flex justify-between items-center text-[11px]">
                                <span class="text-on-surface-variant font-medium">Session Token Security</span>
                                <span class="font-mono-technical text-emerald-600 font-semibold flex items-center gap-1">
                                    <span class="material-symbols-outlined text-[13px]">lock</span>
                                    <span>Encrypted & Verified</span>
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- TAB 2: SETTINGS VIEW -->
                <div id="drawer-tab-settings-content" class="space-y-6 hidden">
                    <!-- General Workspace Preferences -->
                    <div class="space-y-3">
                        <span class="font-mono-technical text-[11px] uppercase tracking-wider text-on-surface-variant font-bold">Workspace Appearance</span>
                        <div class="p-4 rounded-xl border border-outline-variant/40 bg-surface-container-low space-y-4">
                            <!-- Theme Toggle -->
                            <div class="flex items-center justify-between">
                                <div>
                                    <div class="font-headline-md text-[13px] font-semibold text-on-surface">Interface Theme</div>
                                    <div class="font-body-md text-[11px] text-on-surface-variant">Switch light or dark display mode</div>
                                </div>
                                <div class="flex bg-surface-container-highest p-1 rounded-lg border border-outline-variant/40 gap-1 text-[12px]">
                                    <button type="button" id="theme-btn-light" onclick="setMuleGuardTheme('light')" class="px-2.5 py-1 rounded font-medium transition-colors bg-white text-on-surface shadow-xs">Light</button>
                                    <button type="button" id="theme-btn-dark" onclick="setMuleGuardTheme('dark')" class="px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface">Dark</button>
                                </div>
                            </div>

                            <!-- Density Selector -->
                            <div class="flex items-center justify-between pt-3 border-t border-outline-variant/20">
                                <div>
                                    <div class="font-headline-md text-[13px] font-semibold text-on-surface">Layout Density</div>
                                    <div class="font-body-md text-[11px] text-on-surface-variant">Adjust table padding and grid compactness</div>
                                </div>
                                <div class="flex bg-surface-container-highest p-1 rounded-lg border border-outline-variant/40 gap-1 text-[12px]">
                                    <button type="button" id="density-btn-comfortable" onclick="setMuleGuardDensity('comfortable')" class="px-2.5 py-1 rounded font-medium transition-colors bg-white text-on-surface shadow-xs">Default</button>
                                    <button type="button" id="density-btn-compact" onclick="setMuleGuardDensity('compact')" class="px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface">Compact</button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Real-Time Ingestion & Streaming Data -->
                    <div class="space-y-3">
                        <span class="font-mono-technical text-[11px] uppercase tracking-wider text-on-surface-variant font-bold">Data & Notifications</span>
                        <div class="p-4 rounded-xl border border-outline-variant/40 bg-surface-container-low space-y-4">
                            <!-- Live Auto-Refresh -->
                            <div class="flex items-center justify-between">
                                <div>
                                    <div class="font-headline-md text-[13px] font-semibold text-on-surface">Live Ingestion Polling</div>
                                    <div class="font-body-md text-[11px] text-on-surface-variant">Real-time simulator and ledger streaming</div>
                                </div>
                                <label class="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" id="setting-autorefresh" onchange="toggleSettingPreference('autorefresh', this.checked)" class="sr-only switch-checkbox" checked />
                                    <div class="switch-label w-10 h-5 bg-slate-300 rounded-full transition-colors relative">
                                        <div class="switch-knob absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow-xs"></div>
                                    </div>
                                </label>
                            </div>

                            <!-- Audio Alerts -->
                            <div class="flex items-center justify-between pt-3 border-t border-outline-variant/20">
                                <div>
                                    <div class="font-headline-md text-[13px] font-semibold text-on-surface">Audible Alert Chime</div>
                                    <div class="font-body-md text-[11px] text-on-surface-variant">Play sound cue on critical risk detection</div>
                                </div>
                                <label class="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" id="setting-sound" onchange="toggleSettingPreference('sound', this.checked)" class="sr-only switch-checkbox" checked />
                                    <div class="switch-label w-10 h-5 bg-slate-300 rounded-full transition-colors relative">
                                        <div class="switch-knob absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow-xs"></div>
                                    </div>
                                </label>
                            </div>
                        </div>
                    </div>

                    <!-- Role-Specific Preferences -->
                    <div class="space-y-3">
                        <div class="flex items-center justify-between">
                            <span class="font-mono-technical text-[11px] uppercase tracking-wider text-on-surface-variant font-bold">Role-Specific Toggles</span>
                            <span class="font-mono-technical text-[10px] text-secondary-container font-semibold uppercase" id="role-settings-label">INVESTIGATOR</span>
                        </div>
                        <div class="p-4 rounded-xl border border-outline-variant/40 bg-surface-container-low space-y-4" id="role-settings-container">
                            <!-- Populated dynamically based on user role -->
                        </div>
                    </div>
                </div>
            </div>

            <!-- Drawer Footer with Logout -->
            <div class="p-4 border-t border-outline-variant/30 bg-surface-container-low shrink-0 flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                    <span class="font-mono-technical text-[11px] text-on-surface-variant font-medium">Session Active</span>
                </div>
                <button type="button" onclick="logoutUser()" class="flex items-center gap-2 px-3.5 py-1.5 rounded-lg border border-risk-high/30 text-risk-high hover:bg-risk-high/10 font-body-md text-[12px] font-semibold transition-colors focus:outline-none">
                    <span class="material-symbols-outlined text-[16px]">logout</span>
                    <span>Secure Sign Out</span>
                </button>
            </div>
        `;

        document.body.appendChild(overlay);
        document.body.appendChild(drawer);

        // Escape key closes drawer
        window.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' || e.key === 'Esc') {
                const d = document.getElementById('muleguard-profile-drawer');
                if (d && !d.classList.contains('translate-x-full')) {
                    window.closeProfileDrawer();
                }
            }
        });
    }

    // Populate user profile data in the drawer
    function populateDrawerData(user) {
        if (!user) return;
        cachedUser = user;

        const role = user.role || 'bank_investigator';
        const roleLabel = ROLE_LABELS[role] || 'Institutional Officer';
        const roleBadgeClass = ROLE_BADGE_CLASSES[role] || 'bg-blue-500/15 text-blue-600 border-blue-500/30';
        const accessDesc = ROLE_PERMISSIONS[role] || 'Standard Access';

        const name = user.name || 'Institutional Officer';
        const initials = name.split(/\s+/).filter(Boolean).map(n => n[0]).join('').substring(0, 2).toUpperCase() || 'MG';

        // Header info
        const avatarEl = document.getElementById('drawer-profile-avatar');
        if (avatarEl) avatarEl.textContent = initials;

        const nameEl = document.getElementById('drawer-profile-name');
        if (nameEl) nameEl.textContent = name;

        const titleEl = document.getElementById('drawer-profile-title');
        if (titleEl) titleEl.textContent = user.title || roleLabel;

        const empidEl = document.getElementById('drawer-profile-empid');
        if (empidEl) empidEl.textContent = `Employee ID: ${user.employee_id || 'MG-000'}`;

        const badgeEl = document.getElementById('drawer-profile-role-badge');
        if (badgeEl) {
            badgeEl.className = `inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono-technical font-bold border shrink-0 ${roleBadgeClass}`;
            badgeEl.textContent = (role === 'bank_compliance' ? 'COMPLIANCE' : (role === 'internal_team' ? 'ADMIN' : 'INVESTIGATOR'));
        }

        // Details
        const deptEl = document.getElementById('drawer-detail-dept');
        if (deptEl) deptEl.textContent = user.department || (role === 'bank_compliance' ? 'AML Compliance' : (role === 'internal_team' ? 'Core Platform Engineering' : 'Fraud Investigations'));

        const emailEl = document.getElementById('drawer-detail-email');
        if (emailEl) emailEl.textContent = user.email || `${(user.employee_id || 'user').toLowerCase()}@muleguard.bank`;

        const accessEl = document.getElementById('drawer-detail-access');
        if (accessEl) accessEl.textContent = accessDesc;

        const faceEl = document.getElementById('drawer-detail-face');
        if (faceEl) faceEl.textContent = user.face_auth_status || 'Enrolled & Biometrically Verified (OpenCV SFace 128-D)';

        const lastLoginEl = document.getElementById('drawer-detail-lastlogin');
        if (lastLoginEl) lastLoginEl.textContent = user.last_login_at || 'Active Session (Verified)';

        // Role settings label
        const roleLabelEl = document.getElementById('role-settings-label');
        if (roleLabelEl) roleLabelEl.textContent = (role === 'bank_compliance' ? 'COMPLIANCE OFFICER' : (role === 'internal_team' ? 'PLATFORM ADMIN' : 'FRAUD INVESTIGATOR'));

        // Render role-specific settings toggles
        renderRoleSettings(role);
    }

    // Role-specific settings renderer
    function renderRoleSettings(role) {
        const container = document.getElementById('role-settings-container');
        if (!container) return;

        let items = [];
        if (role === 'bank_investigator') {
            items = [
                {
                    key: 'inv_case_alert',
                    title: 'Case Assignment Notifications',
                    desc: 'Alert when a high-priority fraud case is assigned to you',
                    default: true
                },
                {
                    key: 'inv_stream_refresh',
                    title: 'Live Streaming Alert Queue',
                    desc: 'Refresh alerts instantaneously without manual page reload',
                    default: true
                },
                {
                    key: 'inv_risk_threshold_alert',
                    title: 'Critical Risk Threshold Warnings',
                    desc: 'Highlight mule probability crossings above 80%',
                    default: true
                }
            ];
        } else if (role === 'bank_compliance') {
            items = [
                {
                    key: 'cmp_filing_deadlines',
                    title: 'Regulatory Filing Reminders',
                    desc: 'Notifications for pending SAR/STR regulatory deadlines',
                    default: true
                },
                {
                    key: 'cmp_escalations',
                    title: 'Investigator Escalation Alerts',
                    desc: 'Prompt notification when an investigator escalates a case',
                    default: true
                },
                {
                    key: 'cmp_audit_verification',
                    title: 'Compliance Audit Integrity Digest',
                    desc: 'Daily verification of immutable audit trail signatures',
                    default: true
                }
            ];
        } else {
            // internal_team / platform admin
            items = [
                {
                    key: 'adm_node_health',
                    title: 'System Node & Service Health',
                    desc: 'Notify on container restart or degraded ingestion pipeline',
                    default: true
                },
                {
                    key: 'adm_rule_failures',
                    title: 'Detection Rule Execution Health',
                    desc: 'Alert on rule execution timeouts or graph query latency spikes',
                    default: true
                },
                {
                    key: 'adm_pool_capacity',
                    title: 'Database & ML Pool Capacity',
                    desc: 'Warn when PostgreSQL connection pool exceeds 75% capacity',
                    default: true
                }
            ];
        }

        container.innerHTML = items.map((item, idx) => {
            const isChecked = localStorage.getItem(`muleguard_${item.key}`) !== 'false';
            const borderClass = idx > 0 ? 'pt-3 border-t border-outline-variant/20' : '';
            return `
                <div class="flex items-center justify-between ${borderClass}">
                    <div>
                        <div class="font-headline-md text-[13px] font-semibold text-on-surface">${item.title}</div>
                        <div class="font-body-md text-[11px] text-on-surface-variant">${item.desc}</div>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" onchange="toggleSettingPreference('${item.key}', this.checked)" class="sr-only switch-checkbox" ${isChecked ? 'checked' : ''} />
                        <div class="switch-label w-10 h-5 bg-slate-300 rounded-full transition-colors relative">
                            <div class="switch-knob absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow-xs"></div>
                        </div>
                    </label>
                </div>
            `;
        }).join('');
    }

    // Tab switcher
    window.switchDrawerTab = function(tabName) {
        activeTab = tabName;
        const profileBtn = document.getElementById('tab-btn-profile');
        const settingsBtn = document.getElementById('tab-btn-settings');
        const profileContent = document.getElementById('drawer-tab-profile-content');
        const settingsContent = document.getElementById('drawer-tab-settings-content');
        const headerTitle = document.getElementById('drawer-header-title');
        const headerIcon = document.getElementById('drawer-header-icon');

        if (tabName === 'profile') {
            if (profileBtn) {
                profileBtn.className = 'flex items-center gap-2 py-3 px-4 font-body-md text-[13px] drawer-tab-active transition-all focus:outline-none';
            }
            if (settingsBtn) {
                settingsBtn.className = 'flex items-center gap-2 py-3 px-4 font-body-md text-[13px] drawer-tab-inactive transition-all focus:outline-none';
            }
            if (profileContent) profileContent.classList.remove('hidden');
            if (settingsContent) settingsContent.classList.add('hidden');
            if (headerTitle) headerTitle.textContent = 'Institutional Profile';
            if (headerIcon) headerIcon.textContent = 'badge';
        } else {
            if (profileBtn) {
                profileBtn.className = 'flex items-center gap-2 py-3 px-4 font-body-md text-[13px] drawer-tab-inactive transition-all focus:outline-none';
            }
            if (settingsBtn) {
                settingsBtn.className = 'flex items-center gap-2 py-3 px-4 font-body-md text-[13px] drawer-tab-active transition-all focus:outline-none';
            }
            if (profileContent) profileContent.classList.add('hidden');
            if (settingsContent) settingsContent.classList.remove('hidden');
            if (headerTitle) headerTitle.textContent = 'Preferences & Settings';
            if (headerIcon) headerIcon.textContent = 'settings';
        }
    };

    // Public Open Drawer API
    window.openProfileDrawer = function(tab = 'profile') {
        createDrawerDOM();
        window.switchDrawerTab(tab);

        // Fetch latest session / backend user
        let session = null;
        try {
            session = JSON.parse(sessionStorage.getItem('muleguard_session') || '{}');
        } catch (_) {}

        if (session && session.user) {
            populateDrawerData(session.user);
        }

        // Also fetch /api/v1/auth/me to ensure fresh DB ground truth
        if (typeof fetch === 'function' && window.location.protocol.startsWith('http')) {
            fetch('/api/v1/auth/me')
                .then(r => r.ok ? r.json() : null)
                .then(data => {
                    if (data && data.user) {
                        populateDrawerData(data.user);
                    }
                })
                .catch(() => {});
        }

        // Animate drawer in
        const overlay = document.getElementById('muleguard-profile-drawer-overlay');
        const drawer = document.getElementById('muleguard-profile-drawer');
        if (overlay) {
            overlay.classList.remove('pointer-events-none', 'opacity-0');
            overlay.classList.add('opacity-100');
        }
        if (drawer) {
            drawer.classList.remove('translate-x-full');
            drawer.classList.add('translate-x-0');
        }
    };

    // Public Close Drawer API
    window.closeProfileDrawer = function() {
        const overlay = document.getElementById('muleguard-profile-drawer-overlay');
        const drawer = document.getElementById('muleguard-profile-drawer');
        if (overlay) {
            overlay.classList.remove('opacity-100');
            overlay.classList.add('opacity-0', 'pointer-events-none');
        }
        if (drawer) {
            drawer.classList.remove('translate-x-0');
            drawer.classList.add('translate-x-full');
        }
    };

    window.toggleProfileDrawer = function(tab = 'profile') {
        const drawer = document.getElementById('muleguard-profile-drawer');
        if (drawer && !drawer.classList.contains('translate-x-full') && activeTab === tab) {
            window.closeProfileDrawer();
        } else {
            window.openProfileDrawer(tab);
        }
    };

    // Setting handlers
    window.setMuleGuardTheme = function(theme) {
        localStorage.setItem('muleguard_theme', theme);
        const lightBtn = document.getElementById('theme-btn-light');
        const darkBtn = document.getElementById('theme-btn-dark');

        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
            document.documentElement.classList.remove('light');
            if (darkBtn) darkBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors bg-white text-on-surface shadow-xs';
            if (lightBtn) lightBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface';
        } else {
            document.documentElement.classList.remove('dark');
            document.documentElement.classList.add('light');
            if (lightBtn) lightBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors bg-white text-on-surface shadow-xs';
            if (darkBtn) darkBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface';
        }

        if (typeof window.showToast === 'function') {
            window.showToast(`Theme set to ${theme.toUpperCase()} mode`);
        }
    };

    window.setMuleGuardDensity = function(density) {
        localStorage.setItem('muleguard_density', density);
        const comfBtn = document.getElementById('density-btn-comfortable');
        const compBtn = document.getElementById('density-btn-compact');

        if (density === 'compact') {
            document.documentElement.classList.add('density-compact');
            if (compBtn) compBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors bg-white text-on-surface shadow-xs';
            if (comfBtn) comfBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface';
        } else {
            document.documentElement.classList.remove('density-compact');
            if (comfBtn) comfBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors bg-white text-on-surface shadow-xs';
            if (compBtn) compBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface';
        }

        if (typeof window.showToast === 'function') {
            window.showToast(`Density set to ${density}`);
        }
    };

    window.toggleSettingPreference = function(key, isChecked) {
        localStorage.setItem(`muleguard_${key}`, isChecked ? 'true' : 'false');
        if (typeof window.showToast === 'function') {
            window.showToast(`Preference updated: ${isChecked ? 'Enabled' : 'Disabled'}`);
        }
    };

    // Wire existing header dropdowns and profile buttons
    function attachTriggerListeners() {
        // Wire top header profile avatar & username clicks
        const profileTriggers = document.querySelectorAll('header div.relative.cursor-pointer.group, #header-profile-trigger');
        profileTriggers.forEach(el => {
            // Find dropdown menu inside
            const dropdown = el.querySelector('div.absolute');
            if (dropdown) {
                // Ensure dropdown has Settings option
                let myProfileLink = null;
                let settingsLink = null;
                const links = dropdown.querySelectorAll('a');
                links.forEach(link => {
                    const text = (link.textContent || '').trim().toLowerCase();
                    if (text.includes('my profile') || text.includes('profile')) {
                        myProfileLink = link;
                    }
                    if (text.includes('settings') || text.includes('configuration')) {
                        settingsLink = link;
                    }
                });

                if (myProfileLink) {
                    myProfileLink.removeAttribute('onclick');
                    myProfileLink.href = 'javascript:void(0)';
                    myProfileLink.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        window.openProfileDrawer('profile');
                    });
                }

                if (settingsLink) {
                    settingsLink.textContent = 'Settings';
                    settingsLink.removeAttribute('onclick');
                    settingsLink.href = 'javascript:void(0)';
                    settingsLink.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        window.openProfileDrawer('settings');
                    });
                } else if (myProfileLink) {
                    // Inject Settings item if missing
                    const newSettings = document.createElement('a');
                    newSettings.href = 'javascript:void(0)';
                    newSettings.className = 'block px-4 py-2 font-body-md text-[13px] text-on-surface hover:bg-surface-container-low transition-colors';
                    newSettings.textContent = 'Settings';
                    newSettings.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        window.openProfileDrawer('settings');
                    });
                    myProfileLink.insertAdjacentElement('afterend', newSettings);
                }
            }
        });

        // Wire sidebar footer profile card & settings button
        const sidebarSettingsBtn = document.querySelector('#sidebar-container button[title="Settings"], #sidebar-container button[onclick*="settings"]');
        if (sidebarSettingsBtn) {
            sidebarSettingsBtn.removeAttribute('onclick');
            sidebarSettingsBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                window.openProfileDrawer('settings');
            });
        }
    }

    // Initialize on DOM load
    injectDrawerStyles();
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            createDrawerDOM();
            attachTriggerListeners();
        });
    } else {
        createDrawerDOM();
        attachTriggerListeners();
    }
})();
