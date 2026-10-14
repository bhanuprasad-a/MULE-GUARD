/**
 * MuleGuard Shared Institutional Profile & Preferences/Security Drawer
 * Unified across Investigator, Compliance Officer, and Platform Administrator roles.
 * Conforms strictly to MuleGuard institutional banking & security design system.
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
        'bank_investigator': 'bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20',
        'bank_compliance': 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20',
        'internal_team': 'bg-indigo-500/10 text-indigo-700 dark:text-indigo-400 border-indigo-500/20'
    };

    const ROLE_PERMISSIONS = {
        'bank_investigator': 'Level 2 Authorization • Incident Triage & Network Graph Analysis',
        'bank_compliance': 'Level 3 Authorization • Regulatory SAR/STR Decisioning & Audit Governance',
        'internal_team': 'System Administration • Model & Service Oversight • Infrastructure Telemetry'
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
                transition: opacity 0.24s cubic-bezier(0.4, 0, 0.2, 1);
            }
            #muleguard-profile-drawer {
                transition: transform 0.24s cubic-bezier(0.4, 0, 0.2, 1);
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
                transform: translateX(16px) !important;
            }
            html.dark #muleguard-profile-drawer {
                background-color: #0b1f3a !important;
                border-color: #1e293b !important;
                color: #f8fafc !important;
            }
            html.dark #muleguard-profile-drawer .bg-interface-base {
                background-color: #0f2747 !important;
                border-color: #1e3a5f !important;
            }
            html.dark #muleguard-profile-drawer .bg-surface-container-low {
                background-color: #08162b !important;
                border-color: #1e293b !important;
            }
            html.dark #muleguard-profile-drawer .text-on-surface {
                color: #f8fafc !important;
            }
            html.dark #muleguard-profile-drawer .text-on-surface-variant {
                color: #94a3b8 !important;
            }
            html.dark #muleguard-profile-drawer .border-outline-variant\\/30,
            html.dark #muleguard-profile-drawer .border-outline-variant\\/20 {
                border-color: #1e3a5f !important;
            }
            html.dark #muleguard-profile-drawer .divide-outline-variant\\/20 > :not([hidden]) ~ :not([hidden]) {
                border-color: #1e3a5f !important;
            }
            html.density-compact #muleguard-profile-drawer .p-5 {
                padding: 0.875rem !important;
            }
            html.density-compact #muleguard-profile-drawer .p-4 {
                padding: 0.75rem !important;
            }
            html.density-compact #muleguard-profile-drawer .p-3\\.5 {
                padding: 0.625rem !important;
            }
            html.density-compact #muleguard-profile-drawer .py-2\\.5 {
                padding-top: 0.375rem !important;
                padding-bottom: 0.375rem !important;
            }
            html.density-compact #muleguard-profile-drawer .space-y-5 > :not([hidden]) ~ :not([hidden]) {
                margin-top: 0.875rem !important;
            }
        `;
        document.head.appendChild(style);
    }

    // Apply stored appearance preferences on boot
    function applyStoredPreferences() {
        const storedTheme = localStorage.getItem('muleguard_theme');
        if (storedTheme === 'dark') {
            document.documentElement.classList.add('dark');
            document.documentElement.classList.remove('light');
        } else if (storedTheme === 'light') {
            document.documentElement.classList.remove('dark');
            document.documentElement.classList.add('light');
        }

        const storedDensity = localStorage.getItem('muleguard_density');
        if (storedDensity === 'compact') {
            document.documentElement.classList.add('density-compact');
        } else {
            document.documentElement.classList.remove('density-compact');
        }
    }

    // Build the drawer HTML structure
    function createDrawerDOM() {
        if (document.getElementById('muleguard-profile-drawer')) return;

        // Overlay backdrop
        const overlay = document.createElement('div');
        overlay.id = 'muleguard-profile-drawer-overlay';
        overlay.className = 'fixed inset-0 bg-[#000615]/50 backdrop-blur-xs z-[90] transition-opacity duration-200 opacity-0 pointer-events-none';
        overlay.setAttribute('aria-hidden', 'true');
        overlay.onclick = () => window.closeProfileDrawer();

        // Right-side Drawer
        const drawer = document.createElement('aside');
        drawer.id = 'muleguard-profile-drawer';
        drawer.className = 'fixed inset-y-0 right-0 z-[100] w-full sm:w-[450px] md:w-[470px] max-w-full bg-interface-base border-l border-outline-variant/30 shadow-2xl transform translate-x-full transition-transform duration-250 ease-in-out select-none flex flex-col';
        drawer.setAttribute('role', 'dialog');
        drawer.setAttribute('aria-modal', 'true');
        drawer.setAttribute('aria-label', 'Institutional Profile and Settings');

        drawer.innerHTML = `
            <!-- Drawer Header -->
            <div class="h-[64px] border-b border-outline-variant/30 flex items-center justify-between px-5 bg-surface-container-low shrink-0">
                <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-lg bg-secondary-container/10 border border-secondary-container/20 flex items-center justify-center text-secondary-container">
                        <span class="material-symbols-outlined text-[18px]" id="drawer-header-icon">badge</span>
                    </div>
                    <div>
                        <h2 class="font-headline-md text-[15px] text-on-surface font-bold tracking-tight" id="drawer-header-title">Institutional Profile</h2>
                        <p class="font-body-md text-[11px] text-on-surface-variant leading-none" id="drawer-header-sub">MuleGuard Banking Security Console</p>
                    </div>
                </div>
                <button type="button" onclick="closeProfileDrawer()" class="w-8 h-8 rounded-lg flex items-center justify-center text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors focus:outline-none focus:ring-1 focus:ring-secondary/40" title="Close Drawer (ESC)" aria-label="Close">
                    <span class="material-symbols-outlined text-[18px]">close</span>
                </button>
            </div>

            <!-- Tab Switcher Navigation -->
            <div class="flex border-b border-outline-variant/30 bg-interface-base px-5 shrink-0">
                <button type="button" id="tab-btn-profile" onclick="switchDrawerTab('profile')" class="flex items-center gap-2 py-3 px-3 font-body-md text-[13px] drawer-tab-active transition-all focus:outline-none">
                    <span class="material-symbols-outlined text-[17px]">person</span>
                    <span>My Profile</span>
                </button>
                <button type="button" id="tab-btn-settings" onclick="switchDrawerTab('settings')" class="flex items-center gap-2 py-3 px-3 font-body-md text-[13px] drawer-tab-inactive transition-all focus:outline-none">
                    <span class="material-symbols-outlined text-[17px]">tune</span>
                    <span>Preferences & Security</span>
                </button>
            </div>

            <!-- Drawer Body Scrollable Content -->
            <div class="flex-1 overflow-y-auto p-5 space-y-5">
                <!-- TAB 1: PROFILE VIEW -->
                <div id="drawer-tab-profile-content" class="space-y-5">
                    <!-- Prominent Identity Header Card -->
                    <div class="p-4 rounded-xl bg-interface-base border border-outline-variant/30 shadow-xs flex items-center gap-3.5">
                        <div class="w-13 h-13 sm:w-14 sm:h-14 rounded-xl bg-primary text-white font-headline-md font-bold text-[18px] flex items-center justify-center border border-[#1e293b] shadow-xs shrink-0" id="drawer-profile-avatar">
                            --
                        </div>
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-2 mb-0.5">
                                <h3 class="font-headline-md text-[16px] text-on-surface font-bold truncate leading-tight" id="drawer-profile-name">Loading...</h3>
                                <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono-technical font-bold border shrink-0" id="drawer-profile-role-badge">STAFF</span>
                            </div>
                            <p class="font-body-md text-[12px] text-on-surface-variant truncate" id="drawer-profile-title">Institutional Officer</p>
                            <p class="font-mono-technical text-[11px] text-secondary-container font-semibold tracking-wider mt-0.5 truncate" id="drawer-profile-empid">ID: ---</p>
                        </div>
                    </div>

                    <!-- Institutional Credentials Details -->
                    <div class="space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="font-mono-technical text-[11px] uppercase tracking-wider text-on-surface-variant font-bold">Institutional Credentials</span>
                            <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-emerald-700 bg-emerald-500/10 text-[10px] font-mono-technical font-semibold border border-emerald-500/20">
                                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                                ACTIVE
                            </span>
                        </div>

                        <div class="rounded-xl border border-outline-variant/30 divide-y divide-outline-variant/20 bg-interface-base text-[12px] shadow-xs overflow-hidden">
                            <div class="flex justify-between items-center py-2.5 px-3.5">
                                <span class="text-on-surface-variant font-medium">Department</span>
                                <span class="text-on-surface font-semibold text-right" id="drawer-detail-dept">--</span>
                            </div>
                            <div class="flex justify-between items-center py-2.5 px-3.5">
                                <span class="text-on-surface-variant font-medium">Official Email</span>
                                <span class="text-on-surface font-mono-technical text-[12px] text-right" id="drawer-detail-email">--</span>
                            </div>
                            <div class="flex justify-between items-center py-2.5 px-3.5">
                                <span class="text-on-surface-variant font-medium">Institutional Role</span>
                                <span class="text-on-surface font-semibold text-right" id="drawer-detail-role">--</span>
                            </div>
                            <div class="flex justify-between items-start py-2.5 px-3.5 gap-2">
                                <span class="text-on-surface-variant font-medium shrink-0">Authorization Tier</span>
                                <span class="text-on-surface text-[11px] text-right font-medium leading-snug" id="drawer-detail-access">--</span>
                            </div>
                            <div class="flex justify-between items-center py-2.5 px-3.5">
                                <span class="text-on-surface-variant font-medium">Account Status</span>
                                <span class="text-emerald-700 font-semibold text-[11px] flex items-center gap-1">
                                    <span class="material-symbols-outlined text-[15px] text-emerald-600">check_circle</span>
                                    <span>Institutional Account Active</span>
                                </span>
                            </div>
                        </div>
                    </div>

                    <!-- Authentication & Session Status -->
                    <div class="space-y-2">
                        <span class="font-mono-technical text-[11px] uppercase tracking-wider text-on-surface-variant font-bold">Authentication & Security</span>
                        <div class="rounded-xl border border-outline-variant/30 divide-y divide-outline-variant/20 bg-interface-base text-[12px] shadow-xs overflow-hidden">
                            <div class="flex justify-between items-center py-2.5 px-3.5">
                                <span class="text-on-surface-variant font-medium">Face Authentication</span>
                                <span class="text-emerald-700 font-semibold text-[11px] flex items-center gap-1" id="drawer-face-status-badge">
                                    <span class="material-symbols-outlined text-[15px] text-emerald-600">check_circle</span>
                                    <span id="drawer-detail-face">Enrolled (OpenCV SFace 128-D)</span>
                                </span>
                            </div>
                            <div class="flex justify-between items-center py-2.5 px-3.5">
                                <span class="text-on-surface-variant font-medium">Current Session Status</span>
                                <span class="text-emerald-700 font-semibold text-[11px] flex items-center gap-1">
                                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                                    <span>Session Active</span>
                                </span>
                            </div>
                            <div class="flex justify-between items-center py-2.5 px-3.5">
                                <span class="text-on-surface-variant font-medium">Last Successful Auth</span>
                                <span class="font-mono-technical text-on-surface font-semibold text-[11px] text-right" id="drawer-detail-lastlogin">--</span>
                            </div>
                            <div class="flex justify-between items-center py-2.5 px-3.5">
                                <span class="text-on-surface-variant font-medium">Session Protection</span>
                                <span class="font-mono-technical text-on-surface-variant text-[11px] flex items-center gap-1">
                                    <span class="material-symbols-outlined text-[14px] text-slate-500">lock</span>
                                    <span>HttpOnly Cookie • TLS 1.3</span>
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- TAB 2: PREFERENCES & SECURITY VIEW -->
                <div id="drawer-tab-settings-content" class="space-y-5 hidden">
                    <!-- SECTION A: WORKSPACE -->
                    <div class="space-y-2">
                        <span class="font-mono-technical text-[11px] uppercase tracking-wider text-on-surface-variant font-bold">Workspace</span>
                        <div class="p-3.5 rounded-xl border border-outline-variant/30 bg-interface-base shadow-xs space-y-3">
                            <!-- Theme Toggle -->
                            <div class="flex items-center justify-between">
                                <div>
                                    <div class="font-headline-md text-[13px] font-semibold text-on-surface">Interface Theme</div>
                                    <div class="font-body-md text-[11px] text-on-surface-variant">Switch light or dark display mode</div>
                                </div>
                                <div class="flex bg-surface-container-high p-0.5 rounded-lg border border-outline-variant/30 gap-1 text-[11px]">
                                    <button type="button" id="theme-btn-light" onclick="setMuleGuardTheme('light')" class="px-2.5 py-1 rounded font-semibold transition-colors bg-white text-on-surface shadow-xs">Light</button>
                                    <button type="button" id="theme-btn-dark" onclick="setMuleGuardTheme('dark')" class="px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface">Dark</button>
                                </div>
                            </div>

                            <!-- Density Selector -->
                            <div class="flex items-center justify-between pt-2.5 border-t border-outline-variant/20">
                                <div>
                                    <div class="font-headline-md text-[13px] font-semibold text-on-surface">Layout Density</div>
                                    <div class="font-body-md text-[11px] text-on-surface-variant">Adjust table padding and grid compactness</div>
                                </div>
                                <div class="flex bg-surface-container-high p-0.5 rounded-lg border border-outline-variant/30 gap-1 text-[11px]">
                                    <button type="button" id="density-btn-comfortable" onclick="setMuleGuardDensity('comfortable')" class="px-2.5 py-1 rounded font-semibold transition-colors bg-white text-on-surface shadow-xs">Default</button>
                                    <button type="button" id="density-btn-compact" onclick="setMuleGuardDensity('compact')" class="px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface">Compact</button>
                                </div>
                            </div>

                            <!-- Live Auto-Refresh -->
                            <div class="flex items-center justify-between pt-2.5 border-t border-outline-variant/20">
                                <div>
                                    <div class="font-headline-md text-[13px] font-semibold text-on-surface">Auto Refresh / Live Data</div>
                                    <div class="font-body-md text-[11px] text-on-surface-variant">Real-time simulator and ledger streaming</div>
                                </div>
                                <label class="relative inline-flex items-center cursor-pointer shrink-0">
                                    <input type="checkbox" id="setting-autorefresh" onchange="toggleSettingPreference('autorefresh', this.checked)" class="sr-only switch-checkbox" checked />
                                    <div class="switch-label w-9 h-5 bg-slate-300 rounded-full transition-colors relative">
                                        <div class="switch-knob absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow-xs"></div>
                                    </div>
                                </label>
                            </div>

                            <!-- Timestamp Format -->
                            <div class="flex items-center justify-between pt-2.5 border-t border-outline-variant/20">
                                <div>
                                    <div class="font-headline-md text-[13px] font-semibold text-on-surface">Time / Date Display</div>
                                    <div class="font-body-md text-[11px] text-on-surface-variant">Standardized banking timestamp format</div>
                                </div>
                                <div class="flex bg-surface-container-high p-0.5 rounded-lg border border-outline-variant/30 gap-1 text-[11px]">
                                    <button type="button" id="time-btn-local" onclick="setMuleGuardTimeFormat('local')" class="px-2.5 py-1 rounded font-semibold transition-colors bg-white text-on-surface shadow-xs">Local (IST)</button>
                                    <button type="button" id="time-btn-utc" onclick="setMuleGuardTimeFormat('utc')" class="px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface">UTC</button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- SECTION B: NOTIFICATIONS -->
                    <div class="space-y-2">
                        <span class="font-mono-technical text-[11px] uppercase tracking-wider text-on-surface-variant font-bold">Notifications</span>
                        <div class="p-3.5 rounded-xl border border-outline-variant/30 bg-interface-base shadow-xs space-y-3">
                            <!-- Critical Risk Alerts -->
                            <div class="flex items-center justify-between">
                                <div>
                                    <div class="font-headline-md text-[13px] font-semibold text-on-surface">Critical Risk Alerts</div>
                                    <div class="font-body-md text-[11px] text-on-surface-variant">Immediate notifications on high-severity risk crossings</div>
                                </div>
                                <label class="relative inline-flex items-center cursor-pointer shrink-0">
                                    <input type="checkbox" id="setting-notif-critical-risk" onchange="toggleSettingPreference('notif_critical_risk', this.checked)" class="sr-only switch-checkbox" checked />
                                    <div class="switch-label w-9 h-5 bg-slate-300 rounded-full transition-colors relative">
                                        <div class="switch-knob absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow-xs"></div>
                                    </div>
                                </label>
                            </div>

                            <!-- Investigation / Case Updates -->
                            <div class="flex items-center justify-between pt-2.5 border-t border-outline-variant/20">
                                <div>
                                    <div class="font-headline-md text-[13px] font-semibold text-on-surface">Investigation / Case Updates</div>
                                    <div class="font-body-md text-[11px] text-on-surface-variant">Status updates on active cases and triage escalations</div>
                                </div>
                                <label class="relative inline-flex items-center cursor-pointer shrink-0">
                                    <input type="checkbox" id="setting-notif-case-updates" onchange="toggleSettingPreference('notif_case_updates', this.checked)" class="sr-only switch-checkbox" checked />
                                    <div class="switch-label w-9 h-5 bg-slate-300 rounded-full transition-colors relative">
                                        <div class="switch-knob absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow-xs"></div>
                                    </div>
                                </label>
                            </div>

                            <!-- System Notifications -->
                            <div class="flex items-center justify-between pt-2.5 border-t border-outline-variant/20">
                                <div>
                                    <div class="font-headline-md text-[13px] font-semibold text-on-surface">System Notifications</div>
                                    <div class="font-body-md text-[11px] text-on-surface-variant">Maintenance, engine status, and operational advisories</div>
                                </div>
                                <label class="relative inline-flex items-center cursor-pointer shrink-0">
                                    <input type="checkbox" id="setting-notif-system" onchange="toggleSettingPreference('notif_system', this.checked)" class="sr-only switch-checkbox" checked />
                                    <div class="switch-label w-9 h-5 bg-slate-300 rounded-full transition-colors relative">
                                        <div class="switch-knob absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow-xs"></div>
                                    </div>
                                </label>
                            </div>

                            <!-- Alert Sound -->
                            <div class="flex items-center justify-between pt-2.5 border-t border-outline-variant/20">
                                <div>
                                    <div class="font-headline-md text-[13px] font-semibold text-on-surface">Alert Sound</div>
                                    <div class="font-body-md text-[11px] text-on-surface-variant">Audible chime on high-priority fraud detection</div>
                                </div>
                                <label class="relative inline-flex items-center cursor-pointer shrink-0">
                                    <input type="checkbox" id="setting-sound" onchange="toggleSettingPreference('sound', this.checked)" class="sr-only switch-checkbox" checked />
                                    <div class="switch-label w-9 h-5 bg-slate-300 rounded-full transition-colors relative">
                                        <div class="switch-knob absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow-xs"></div>
                                    </div>
                                </label>
                            </div>
                        </div>
                    </div>

                    <!-- SECTION C: SECURITY & SESSION -->
                    <div class="space-y-2">
                        <span class="font-mono-technical text-[11px] uppercase tracking-wider text-on-surface-variant font-bold">Security & Session</span>
                        <div class="rounded-xl border border-outline-variant/30 divide-y divide-outline-variant/20 bg-interface-base text-[12px] shadow-xs overflow-hidden">
                            <div class="flex justify-between items-center py-2.5 px-3.5">
                                <div>
                                    <div class="font-medium text-on-surface">Face Authentication</div>
                                    <div class="text-[11px] text-on-surface-variant">Biometric probe verification</div>
                                </div>
                                <span class="inline-flex items-center gap-1 text-emerald-700 bg-emerald-500/10 px-2 py-0.5 rounded text-[11px] font-mono-technical font-semibold border border-emerald-500/20" id="drawer-sec-face">
                                    <span class="material-symbols-outlined text-[13px] text-emerald-600">check_circle</span>
                                    <span>Enrolled</span>
                                </span>
                            </div>
                            <div class="flex justify-between items-center py-2.5 px-3.5">
                                <div>
                                    <div class="font-medium text-on-surface">Current Session Status</div>
                                    <div class="text-[11px] text-on-surface-variant">Cryptographic token validation</div>
                                </div>
                                <span class="inline-flex items-center gap-1 text-emerald-700 bg-emerald-500/10 px-2 py-0.5 rounded text-[11px] font-mono-technical font-semibold border border-emerald-500/20">
                                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                                    <span>Session Active</span>
                                </span>
                            </div>
                            <div class="flex justify-between items-center py-2.5 px-3.5">
                                <div>
                                    <div class="font-medium text-on-surface">Last Authentication</div>
                                    <div class="text-[11px] text-on-surface-variant">Timestamp of verified login</div>
                                </div>
                                <span class="font-mono-technical text-on-surface font-semibold text-[11px] text-right" id="drawer-sec-lastlogin">--</span>
                            </div>
                            <div class="flex justify-between items-center py-2.5 px-3.5">
                                <div>
                                    <div class="font-medium text-on-surface">Session Timeout Policy</div>
                                    <div class="text-[11px] text-on-surface-variant">Automatic revocation threshold</div>
                                </div>
                                <span class="font-mono-technical text-on-surface-variant text-[11px]">30m idle / 24h max</span>
                            </div>
                            <div class="flex justify-between items-center py-2.5 px-3.5 bg-surface-container-low/40">
                                <div>
                                    <div class="font-medium text-on-surface">Active Session Management</div>
                                    <div class="text-[11px] text-on-surface-variant">Revoke token and terminate session</div>
                                </div>
                                <button type="button" onclick="logoutUser()" class="flex items-center gap-1.5 px-3 py-1 rounded-lg border border-risk-high/30 text-risk-high hover:bg-risk-high/10 font-body-md text-[11px] font-semibold transition-colors focus:outline-none">
                                    <span class="material-symbols-outlined text-[14px]">logout</span>
                                    <span>Sign Out</span>
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- SECTION D: ROLE-SPECIFIC PREFERENCES -->
                    <div class="space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="font-mono-technical text-[11px] uppercase tracking-wider text-on-surface-variant font-bold">Role-Specific Preferences</span>
                            <span class="font-mono-technical text-[10px] text-secondary-container font-semibold uppercase tracking-wider" id="role-settings-label">INVESTIGATOR</span>
                        </div>
                        <div class="p-3.5 rounded-xl border border-outline-variant/30 bg-interface-base shadow-xs space-y-3" id="role-settings-container">
                            <!-- Populated dynamically based on user role -->
                        </div>
                    </div>
                </div>
            </div>

            <!-- Drawer Footer with Session Indicator & Logout -->
            <div class="h-[60px] px-5 border-t border-outline-variant/30 bg-surface-container-low shrink-0 flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                    <span class="font-mono-technical text-[11px] text-on-surface-variant font-medium">Session Active</span>
                </div>
                <button type="button" onclick="logoutUser()" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-risk-high/30 text-risk-high hover:bg-risk-high/10 font-body-md text-[12px] font-semibold transition-colors focus:outline-none">
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
        const roleBadgeClass = ROLE_BADGE_CLASSES[role] || 'bg-blue-500/10 text-blue-700 border-blue-500/20';
        const accessDesc = ROLE_PERMISSIONS[role] || 'Standard Institutional Authorization';

        const name = user.name || user.full_name || 'Institutional Officer';
        const initials = name.split(/\s+/).filter(Boolean).map(n => n[0]).join('').substring(0, 2).toUpperCase() || 'MG';

        // Prominent Header Identity Info
        const avatarEl = document.getElementById('drawer-profile-avatar');
        if (avatarEl) avatarEl.textContent = initials;

        const nameEl = document.getElementById('drawer-profile-name');
        if (nameEl) nameEl.textContent = name;

        const titleEl = document.getElementById('drawer-profile-title');
        if (titleEl) titleEl.textContent = user.title || roleLabel;

        const empidEl = document.getElementById('drawer-profile-empid');
        if (empidEl) empidEl.textContent = user.employee_id || 'MG-000';

        const badgeEl = document.getElementById('drawer-profile-role-badge');
        if (badgeEl) {
            badgeEl.className = `inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono-technical font-bold border shrink-0 ${roleBadgeClass}`;
            badgeEl.textContent = (role === 'bank_compliance' ? 'COMPLIANCE' : (role === 'internal_team' ? 'ADMIN' : 'INVESTIGATOR'));
        }

        // Institutional Credentials Section
        const deptEl = document.getElementById('drawer-detail-dept');
        if (deptEl) deptEl.textContent = user.department || (role === 'bank_compliance' ? 'AML Compliance' : (role === 'internal_team' ? 'Core Platform Engineering' : 'Fraud Investigations'));

        const emailEl = document.getElementById('drawer-detail-email');
        if (emailEl) emailEl.textContent = user.email || `${(user.employee_id || 'officer').toLowerCase()}@muleguard.bank`;

        const roleDetailEl = document.getElementById('drawer-detail-role');
        if (roleDetailEl) roleDetailEl.textContent = roleLabel;

        const accessEl = document.getElementById('drawer-detail-access');
        if (accessEl) accessEl.textContent = accessDesc;

        // Face & Authentication Section
        const faceStatusText = user.face_auth_status || 'Enrolled (OpenCV SFace 128-D)';
        const faceEl = document.getElementById('drawer-detail-face');
        if (faceEl) faceEl.textContent = faceStatusText;

        const faceBadgeEl = document.getElementById('drawer-face-status-badge');
        if (faceBadgeEl) {
            const isEnrolled = !faceStatusText.toLowerCase().includes('pending');
            faceBadgeEl.className = isEnrolled
                ? 'text-emerald-700 font-semibold text-[11px] flex items-center gap-1'
                : 'text-amber-700 font-semibold text-[11px] flex items-center gap-1';
        }

        const lastLoginFmt = user.last_login_at || 'Active Session (Verified)';
        const lastLoginEl = document.getElementById('drawer-detail-lastlogin');
        if (lastLoginEl) lastLoginEl.textContent = lastLoginFmt;

        // Security tab items
        const secFaceEl = document.getElementById('drawer-sec-face');
        if (secFaceEl) {
            const isEnrolled = !faceStatusText.toLowerCase().includes('pending');
            secFaceEl.innerHTML = `
                <span class="material-symbols-outlined text-[13px] ${isEnrolled ? 'text-emerald-600' : 'text-amber-600'}">${isEnrolled ? 'check_circle' : 'pending'}</span>
                <span>${isEnrolled ? 'Enrolled' : 'Pending Enrollment'}</span>
            `;
            secFaceEl.className = isEnrolled
                ? 'inline-flex items-center gap-1 text-emerald-700 bg-emerald-500/10 px-2 py-0.5 rounded text-[11px] font-mono-technical font-semibold border border-emerald-500/20'
                : 'inline-flex items-center gap-1 text-amber-700 bg-amber-500/10 px-2 py-0.5 rounded text-[11px] font-mono-technical font-semibold border border-amber-500/20';
        }

        const secLastLoginEl = document.getElementById('drawer-sec-lastlogin');
        if (secLastLoginEl) secLastLoginEl.textContent = lastLoginFmt;

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
                    key: 'inv_high_risk_alerts',
                    title: 'High-Risk Account Alerts',
                    desc: 'Real-time alerts when account risk score exceeds high threshold',
                    default: true
                },
                {
                    key: 'inv_case_updates',
                    title: 'Investigation / Case Updates',
                    desc: 'Notifications on case assignments, status changes, and evidence',
                    default: true
                },
                {
                    key: 'inv_network_intel',
                    title: 'Network Intelligence Notifications',
                    desc: 'Alerts on multi-hop mule ring and graph cluster discoveries',
                    default: true
                }
            ];
        } else if (role === 'bank_compliance') {
            items = [
                {
                    key: 'cmp_high_risk_alerts',
                    title: 'High-Risk Alerts',
                    desc: 'Priority notifications for high-risk accounts and threshold breaches',
                    default: true
                },
                {
                    key: 'cmp_escalations',
                    title: 'Escalation Notifications',
                    desc: 'Immediate alerts on investigator escalations requiring compliance review',
                    default: true
                },
                {
                    key: 'cmp_case_reviews',
                    title: 'Compliance / Case Review Notifications',
                    desc: 'Alerts on pending case reviews and regulatory milestone tracking',
                    default: true
                },
                {
                    key: 'cmp_audit_reviews',
                    title: 'Audit / Review Notifications',
                    desc: 'Digests for audit trail integrity checks and supervisory reporting',
                    default: true
                }
            ];
        } else {
            // internal_team / platform admin
            items = [
                {
                    key: 'adm_platform_health',
                    title: 'Platform / System Health Alerts',
                    desc: 'Alerts on node, API service, or container status transitions',
                    default: true
                },
                {
                    key: 'adm_rule_execution',
                    title: 'Detection Rule Execution Alerts',
                    desc: 'Notifications for rule evaluation timeouts or latency spikes',
                    default: true
                },
                {
                    key: 'adm_db_ml_health',
                    title: 'Database / ML Service Health',
                    desc: 'Telemetry alerts for PostgreSQL pool and XGBoost inference engine',
                    default: true
                },
                {
                    key: 'adm_infra_notifs',
                    title: 'Infrastructure Notifications',
                    desc: 'Alerts for background simulator workers and ingestion queues',
                    default: true
                }
            ];
        }

        container.innerHTML = items.map((item, idx) => {
            const isChecked = localStorage.getItem(`muleguard_${item.key}`) !== 'false';
            const borderClass = idx > 0 ? 'pt-2.5 border-t border-outline-variant/20' : '';
            return `
                <div class="flex items-center justify-between ${borderClass}">
                    <div>
                        <div class="font-headline-md text-[13px] font-semibold text-on-surface">${item.title}</div>
                        <div class="font-body-md text-[11px] text-on-surface-variant">${item.desc}</div>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer shrink-0">
                        <input type="checkbox" onchange="toggleSettingPreference('${item.key}', this.checked)" class="sr-only switch-checkbox" ${isChecked ? 'checked' : ''} />
                        <div class="switch-label w-9 h-5 bg-slate-300 rounded-full transition-colors relative">
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
        const headerSub = document.getElementById('drawer-header-sub');

        if (tabName === 'profile') {
            if (profileBtn) {
                profileBtn.className = 'flex items-center gap-2 py-3 px-3 font-body-md text-[13px] drawer-tab-active transition-all focus:outline-none';
            }
            if (settingsBtn) {
                settingsBtn.className = 'flex items-center gap-2 py-3 px-3 font-body-md text-[13px] drawer-tab-inactive transition-all focus:outline-none';
            }
            if (profileContent) profileContent.classList.remove('hidden');
            if (settingsContent) settingsContent.classList.add('hidden');
            if (headerTitle) headerTitle.textContent = 'Institutional Profile';
            if (headerIcon) headerIcon.textContent = 'person';
            if (headerSub) headerSub.textContent = 'MuleGuard Banking Security Console';
        } else {
            if (profileBtn) {
                profileBtn.className = 'flex items-center gap-2 py-3 px-3 font-body-md text-[13px] drawer-tab-inactive transition-all focus:outline-none';
            }
            if (settingsBtn) {
                settingsBtn.className = 'flex items-center gap-2 py-3 px-3 font-body-md text-[13px] drawer-tab-active transition-all focus:outline-none';
            }
            if (profileContent) profileContent.classList.add('hidden');
            if (settingsContent) settingsContent.classList.remove('hidden');
            if (headerTitle) headerTitle.textContent = 'Preferences & Security';
            if (headerIcon) headerIcon.textContent = 'tune';
            if (headerSub) headerSub.textContent = 'Institutional Workspace & Security Controls';
        }
    };

    // Synchronize UI preference control states
    function syncPreferencesUI() {
        // Theme
        const theme = localStorage.getItem('muleguard_theme') || 'light';
        const lightBtn = document.getElementById('theme-btn-light');
        const darkBtn = document.getElementById('theme-btn-dark');
        if (lightBtn && darkBtn) {
            if (theme === 'dark') {
                darkBtn.className = 'px-2.5 py-1 rounded font-semibold transition-colors bg-white text-on-surface shadow-xs';
                lightBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface';
            } else {
                lightBtn.className = 'px-2.5 py-1 rounded font-semibold transition-colors bg-white text-on-surface shadow-xs';
                darkBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface';
            }
        }

        // Density
        const density = localStorage.getItem('muleguard_density') || 'comfortable';
        const comfBtn = document.getElementById('density-btn-comfortable');
        const compBtn = document.getElementById('density-btn-compact');
        if (comfBtn && compBtn) {
            if (density === 'compact') {
                compBtn.className = 'px-2.5 py-1 rounded font-semibold transition-colors bg-white text-on-surface shadow-xs';
                comfBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface';
            } else {
                comfBtn.className = 'px-2.5 py-1 rounded font-semibold transition-colors bg-white text-on-surface shadow-xs';
                compBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface';
            }
        }

        // Time format
        const timeFormat = localStorage.getItem('muleguard_time_format') || 'local';
        const localBtn = document.getElementById('time-btn-local');
        const utcBtn = document.getElementById('time-btn-utc');
        if (localBtn && utcBtn) {
            if (timeFormat === 'utc') {
                utcBtn.className = 'px-2.5 py-1 rounded font-semibold transition-colors bg-white text-on-surface shadow-xs';
                localBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface';
            } else {
                localBtn.className = 'px-2.5 py-1 rounded font-semibold transition-colors bg-white text-on-surface shadow-xs';
                utcBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface';
            }
        }

        // Toggles
        const autorefreshInput = document.getElementById('setting-autorefresh');
        if (autorefreshInput) {
            autorefreshInput.checked = localStorage.getItem('muleguard_autorefresh') !== 'false';
        }

        const soundInput = document.getElementById('setting-sound');
        if (soundInput) {
            soundInput.checked = localStorage.getItem('muleguard_sound') !== 'false';
        }

        const criticalRiskInput = document.getElementById('setting-notif-critical-risk');
        if (criticalRiskInput) {
            criticalRiskInput.checked = localStorage.getItem('muleguard_notif_critical_risk') !== 'false';
        }

        const caseUpdatesInput = document.getElementById('setting-notif-case-updates');
        if (caseUpdatesInput) {
            caseUpdatesInput.checked = localStorage.getItem('muleguard_notif_case_updates') !== 'false';
        }

        const systemNotifInput = document.getElementById('setting-notif-system');
        if (systemNotifInput) {
            systemNotifInput.checked = localStorage.getItem('muleguard_notif_system') !== 'false';
        }
    }

    // Public Open Drawer API
    window.openProfileDrawer = function(tab = 'profile') {
        createDrawerDOM();
        window.switchDrawerTab(tab);
        syncPreferencesUI();

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

    // Setting handlers (UI-only preferences saved to localStorage)
    window.setMuleGuardTheme = function(theme) {
        localStorage.setItem('muleguard_theme', theme);
        const lightBtn = document.getElementById('theme-btn-light');
        const darkBtn = document.getElementById('theme-btn-dark');

        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
            document.documentElement.classList.remove('light');
            if (darkBtn) darkBtn.className = 'px-2.5 py-1 rounded font-semibold transition-colors bg-white text-on-surface shadow-xs';
            if (lightBtn) lightBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface';
        } else {
            document.documentElement.classList.remove('dark');
            document.documentElement.classList.add('light');
            if (lightBtn) lightBtn.className = 'px-2.5 py-1 rounded font-semibold transition-colors bg-white text-on-surface shadow-xs';
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
            if (compBtn) compBtn.className = 'px-2.5 py-1 rounded font-semibold transition-colors bg-white text-on-surface shadow-xs';
            if (comfBtn) comfBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface';
        } else {
            document.documentElement.classList.remove('density-compact');
            if (comfBtn) comfBtn.className = 'px-2.5 py-1 rounded font-semibold transition-colors bg-white text-on-surface shadow-xs';
            if (compBtn) compBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface';
        }

        if (typeof window.showToast === 'function') {
            window.showToast(`Layout density set to ${density === 'compact' ? 'Compact' : 'Default'}`);
        }
    };

    window.setMuleGuardTimeFormat = function(format) {
        localStorage.setItem('muleguard_time_format', format);
        const localBtn = document.getElementById('time-btn-local');
        const utcBtn = document.getElementById('time-btn-utc');

        if (format === 'utc') {
            if (utcBtn) utcBtn.className = 'px-2.5 py-1 rounded font-semibold transition-colors bg-white text-on-surface shadow-xs';
            if (localBtn) localBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface';
        } else {
            if (localBtn) localBtn.className = 'px-2.5 py-1 rounded font-semibold transition-colors bg-white text-on-surface shadow-xs';
            if (utcBtn) utcBtn.className = 'px-2.5 py-1 rounded font-medium transition-colors text-on-surface-variant hover:text-on-surface';
        }

        if (typeof window.showToast === 'function') {
            window.showToast(`Display time set to ${format.toUpperCase()}`);
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
                    if (text.includes('settings') || text.includes('configuration') || text.includes('preferences')) {
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
                    settingsLink.textContent = 'Preferences & Security';
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
                    newSettings.textContent = 'Preferences & Security';
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
    applyStoredPreferences();
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
